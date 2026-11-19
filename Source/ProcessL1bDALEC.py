''' Process L1AQC to L1B '''
import os
import datetime as dt
import numpy as np
import pandas as pd
from scipy import interpolate

from Source import PATH_TO_DATA, PACKAGE_DIR as CODE_HOME
from Source.ProcessL1b import ProcessL1b
# from Source.ProcessL1b_FactoryCal import ProcessL1b_FactoryCal
from Source.ProcessL1b_FRMCal import ProcessL1b_FRMCal
from Source.ConfigFile import ConfigFile
from Source.CalibrationFileReader import CalibrationFileReader
from Source.ProcessL1b_Interp import ProcessL1b_Interp
from Source.GetAnc import GetAnc
from Source.GetAnc_ecmwf import GetAnc_ecmwf
import Source.utils.loggingHCP as logging
import Source.utils.dating as dating
from Source.utils.uncertainties import unc_management as um
from Source.utils.loggingHCP import writeLogFileAndPrint

class ProcessL1bDALEC:
    '''L1B for DALEC'''

    @staticmethod
    def read_unc_coefficient_factory(root):
        ''' SeaBird or TriOS'''
        # Read Uncertainties_new_char from provided files
        gp = root.addGroup("RAW_UNCERTAINTIES")
        gp.attributes['FrameType'] = 'NONE'  # add FrameType = None so grp passes a quality check later

        # Unc dataset renaming
        um.RenameUncertainties_Class(root)

        for sensor in ['LI','LT','ES']:
            dsname = sensor+'_RADCAL_UNC'
            gp.addDataset(dsname)
            ds = gp.getDataset(dsname)
            ds.columns["wvl"] = [400]
            ds.columns["unc"] = [0.0]
            ds.columnsToDataset()

        # interpolate unc to full wavelength range, depending on class based or full char
        um.interpUncertainties_Factory(root)

        # # generate temperature coefficient
       #Utilities.UncTempCorrection(root)

        return root

    # NOTE: These three methods could be combined into one.
    @staticmethod
    def processSensor(node,s):
        specialNames = {
            'ES':['Delta_T_Ed','Tempco_Ed','d0','d1','a0'],
            'LT':['Delta_T_Lu','Tempco_Lu','e0','e1','b0'],
            'LI':['Delta_T_Lsky','Tempco_Lsky','f0','f1','c0']}

        gp=node.getGroup(s)
        gpc=node.getGroup('CAL_COEF')
        delta_t=float(gpc.attributes[specialNames[s][0]])
        tref=float(gpc.attributes['Tref'])
        def0=float(gpc.attributes[specialNames[s][2]])
        def1=float(gpc.attributes[specialNames[s][3]])
        ds=gp.datasets[s]
        dc=gp.datasets['DARK_CNT'].data[s].tolist()
        inttime=gp.datasets['INTTIME'].data[s].tolist()
        temp=gp.datasets['SPECTEMP'].data['NONE'].tolist()
        cd=gpc.datasets[f'Cal_{s}']
        abc0 = cd.data[specialNames[s][4]].tolist()
        tempco=cd.data[specialNames[s][1]].tolist()

        # K1=d0*(V-DC)+d1
        # Ed=a0*((V-DC)/(Inttime+DeltaT_Ed)/K1)/(Tempco_Ed*(Temp-Tref)+1)

        for i in range(ds.data.shape[0]):
            c1=inttime[i]+delta_t
            for j in range(cd.data.shape[0]):
                ds.data[i][j] = 100.0*abc0[j]*((ds.data[i][j]-dc[i])/c1
                /(def1*(ds.data[i][j]-dc[i])+def0))/(tempco[j]*(temp[i]-tref)+1)

        # As in the calibration step above, this presumes UV bands (initial pixels) are always calibrated and
        #   any truncation in calibration is on the NIR end
        gp.attributes['CAL_START'] = str(0)
        gp.attributes['CAL_STOP'] = str(j)

        gp_l1aqc = node.getGroup(f'{s}_L1AQC')
        calDS = gp_l1aqc.addDataset('CAL_COEF')
        gp_l1aqc.datasets.move_to_end('CAL_COEF',last=False)
        calDS.data = cd.data
        calDS.datasetToColumns()
        gp_l1aqc.attributes['Tref'] = tref
        for key, attr in gp.attributes.items():
            if key in ['CAL_START','CAL_STOP']:
                gp_l1aqc.attributes[key] = attr
        for key in specialNames[s]:
            if key.lower().startswith('d') or key.lower().startswith('e') or key.lower().startswith('f'):
                gp_l1aqc.attributes[key] = gpc.attributes[key]
            elif key.startswith('Tempco'):
                gp_l1aqc.attributes[key] = tempco
            else:
                gp_l1aqc.attributes[key] = abc0

    @staticmethod
    def _to_pixel_grid(v, valid):
        ''' Put a vector on the 255-pixel RADCAL grid. LAMP/PANEL may come back from
            um.interpUncertainties_FullChar as reported bands only (190) or as the full grid (255). '''
        v = np.asarray(v, dtype=float)
        out = np.zeros(len(valid))
        if len(v) == len(valid):
            return v
        if len(v) == valid.sum():
            out[valid] = v
            return out
        writeLogFileAndPrint(f'ProcessL1bDALEC: WARNING unexpected LAMP/PANEL length {len(v)}; padding with zeros like SeaBird.')
        out[:len(v)] = v
        return out

    @staticmethod
    def _thermal_temps(unc_grp, s):
        ''' (T_ref, T_cal) for the Tartu thermal characterisation, or None if they are not in RAW_UNCERTAINTIES.
            T_ref = REFERENCE_TEMP of the THERMAL file (cT is defined relative to it).
            T_cal = AMBIENT_TEMP of the RADCAL file (temperature at which the lamp calibration was made),
                    falling back to AMBIENT_TEMP of the THERMAL file.
            Looks in the dataset attributes, then the group attributes (case-insensitive). '''
        def find(holders, key):
            for h in holders:
                if h is None:
                    continue
                for k, v in h.attributes.items():
                    if str(k).strip().upper() == key:
                        try:
                            return float(str(v).strip())
                        except ValueError:
                            pass
            return None
        th = unc_grp.datasets.get(s + '_TEMPDATA_CAL')
        rc = unc_grp.datasets.get(s + '_RADCAL_CAL')
        t_ref = find([th, unc_grp], 'REFERENCE_TEMP')
        t_cal = find([rc], 'AMBIENT_TEMP')
        if t_cal is None:
            t_cal = find([th, unc_grp], 'AMBIENT_TEMP')
        return None if (t_ref is None or t_cal is None) else (t_ref, t_cal)

    @staticmethod
    def processL1b_FRM(node, sensortype, delta_t_correction=True, thermal_temps=None):
        ''' Full-FRM calibration of one DALEC sensor (ES, LI or LT), L1AQC -> L1B.
            Same pattern as ProcessL1bTriOS.processDarkCorrection_FRM: one call per sensor, with the shared
            maths (Zong straylight, cosine error) taken from ProcessL1b_FRMCal.

            Expects in the node: RAW_UNCERTAINTIES (ProcessL1b.read_unc_coefficient_frm), CAL_COEF,
            ES_L1AQC, and, for ES, SIXS_MODEL. The ES/LI/LT data are dark-UNcorrected counts with
            DARK_CNT (dark-pixel mean, per spectrum), INTTIME and SPECTEMP datasets.

            Order: dark -> non-linearity -> straylight* -> calibration -> thermal -> cosine* (ES)
            (*) only when the characterisation datasets are in RAW_UNCERTAINTIES; otherwise skipped with a log line.

            Thermal: if the Tartu thermal file (cT per pixel, relative to REFERENCE_TEMP) is loaded and its temperatures
            can be found (or are passed as thermal_temps=(T_ref, T_cal)), each spectrum is corrected to the calibration
            temperature with its own SPECTEMP: divide by (1+cT*(T-T_ref))/(1+cT*(T_cal-T_ref)).
            Otherwise the manufacturer coefficients of the factory branch are used (with a log line).

            NOTE: 
                delta_t_correction == True uses the integration time offsets from the factory calibration in the full-FRM path.
                delta_t_correction == False sets this offset to zero
                --> According to latest email from Riho this should always be used!
        '''
        s = sensortype
        names = {'ES': ('Delta_T_Ed', 'Tempco_Ed'),
                 'LT': ('Delta_T_Lu', 'Tempco_Lu'),
                 'LI': ('Delta_T_Lsky', 'Tempco_Lsky')}
        writeLogFileAndPrint(f'FRM Processing: {s}')

        unc_grp = node.getGroup('RAW_UNCERTAINTIES')
        gpc = node.getGroup('CAL_COEF')
        sixS_grp = node.getGroup('SIXS_MODEL')
        grp = node.getGroup(s)
        if unc_grp is None or gpc is None or grp is None or (s == 'ES' and sixS_grp is None):
            writeLogFileAndPrint(f'ProcessL1bDALEC.processL1b_FRM: missing RAW_UNCERTAINTIES, CAL_COEF, {s} (or SIXS_MODEL for ES).')
            return False
        tref = float(gpc.attributes['Tref'])

        # ---------- L1AQC data: counts, NOT dark corrected ----------
        raw = np.asarray(grp.getDataset(s).data.tolist(), dtype=float)          # (nmes, npix)
        dark = np.asarray(grp.getDataset('DARK_CNT').data[s], dtype=float)      # (nmes,)
        int_time = np.asarray(grp.getDataset('INTTIME').data[s], dtype=float)
        temp = np.asarray(grp.getDataset('SPECTEMP').data['NONE'], dtype=float)
        nmes, npix = raw.shape

        # ---------- FRM characterisation (RADCAL columns as in SeaBird/TriOS code) ----------
        cal = pd.DataFrame(unc_grp.getDataset(s + '_RADCAL_CAL').data)
        t1 = float(cal['6'].iloc[0])           # row 0 holds integration times, not pixel data
        t2 = float(cal['8'].iloc[0])
        radcal_wvl = cal['1'].to_numpy(dtype=float)[1:]                         # 255 pixels
        gain0 = cal['2'].to_numpy(dtype=float)[1:]
        S1 = cal['6'].to_numpy(dtype=float)[1:]
        S2 = cal['8'].to_numpy(dtype=float)[1:]

        valid = (gain0 > 0) & np.isfinite(gain0) & (radcal_wvl > 0)             # calibrated pixels (DALEC: 11..200)
        if valid.sum() != npix:
            writeLogFileAndPrint(f'ProcessL1bDALEC.processL1b_FRM: {s} has {npix} L1AQC bands but RADCAL has {valid.sum()} calibrated pixels.')
            return False

        LAMP = ProcessL1bDALEC._to_pixel_grid(pd.DataFrame(unc_grp.getDataset(s + '_RADCAL_LAMP').data)['2'], valid)
        if s != 'ES':
            PANEL = ProcessL1bDALEC._to_pixel_grid(pd.DataFrame(unc_grp.getDataset(s + '_RADCAL_PANEL').data)['2'], valid)

        dT = float(gpc.attributes[names[s][0]]) if delta_t_correction else 0.0

        # ---------- non-linearity (FRM; there is no class-based fallback for DALEC) ----------
        k = t1 / (t2 - t1)
        S12 = (1 + k) * S1 - k * S2
        alpha = np.zeros_like(S12)
        ok = valid & (S12 > 0)                                                 # avoid divide-by-zero, as in TriOS
        alpha[ok] = (S1[ok] - S12[ok]) / S12[ok] ** 2
        if ok.sum() != valid.sum():
            writeLogFileAndPrint(f'ProcessL1bDALEC.processL1b_FRM: {s} non-linearity undefined for {valid.sum() - ok.sum()} pixels; set to 0.')

        # ---------- straylight (Zong) if the LSF file was loaded ----------
        C_zong = None
        S12_sl = S12
        if s + '_STRAYDATA_LSF' in unc_grp.datasets:
            mZ = np.asarray(pd.DataFrame(unc_grp.getDataset(s + '_STRAYDATA_LSF').data))[1:, 1:]
            if mZ.shape[0] != len(valid):
                writeLogFileAndPrint(f'ProcessL1bDALEC.processL1b_FRM: {s} LSF is {mZ.shape}, expected {len(valid)} pixels.')
                return False
            C_full = ProcessL1b_FRMCal.Zong_SL_correction_matrix(mZ)
            S12_sl = C_full @ S12
            C_zong = C_full[np.ix_(valid, valid)]          # same sub-selection as the SeaBird code
        else:
            writeLogFileAndPrint(f'ProcessL1bDALEC.processL1b_FRM: no {s}_STRAYDATA_LSF found, straylight correction skipped.')

        # ---------- calibration factor per pixel (lamp-referenced) ----------
        # SeaBird/TriOS: gain = (S12_sl/LAMP)*(t0/t1) and data*(t0/int)/gain, where t0 (cal_int or back. int.) cancels:
        #   E = (counts/int) / (S12_sl/t1) * LAMP/10            L = ... * PANEL/pi          (/10: mW/m2 -> uW/cm2)
        with np.errstate(divide='ignore', invalid='ignore'):
            ref = (LAMP / 10.0) * ((t1 + dT) / S12_sl)
        if s != 'ES':
            ref = ref * PANEL / np.pi
        ref = ref[valid]

        # ---------- apply, vectorised over all spectra ----------
        data = raw - dark[:, None]                                       # dark pixels, per spectrum
        data = data * (1 - alpha[valid][None, :] * data)                 # non-linearity
        if C_zong is not None:
            data = data @ C_zong.T                                       # straylight
        data = data / (int_time + dT)[:, None] * ref[None, :]            # calibration

        # thermal
        temps = thermal_temps or ProcessL1bDALEC._thermal_temps(unc_grp, s)
        cT = None
        if (s + '_TEMPDATA_CAL') in unc_grp.datasets:
            th = pd.DataFrame(unc_grp.getDataset(s + '_TEMPDATA_CAL').data)
            if '2' in th.columns and len(th) == len(valid) + 1:
                cT = th['2'].to_numpy(dtype=float)[1:][valid]              # px, wl, cT, ucT -> column '2'
                if not np.isfinite(cT).all() or np.abs(cT).max() > 0.1:
                    writeLogFileAndPrint(f'ProcessL1bDALEC.processL1b_FRM: {s} thermal coefficients look wrong (max |cT| {np.nanmax(np.abs(cT))}).')
                    cT = None
        if cT is not None and temps is not None:
            t_ref, t_cal = temps
            factor = (1 + cT[None, :] * (temp[:, None] - t_ref)) / (1 + cT[None, :] * (t_cal - t_ref))
            data = data / factor
        else:
            writeLogFileAndPrint(f'ProcessL1bDALEC.processL1b_FRM: {s} Tartu thermal correction not applicable '
                                 f'(dataset found: {cT is not None}, temperatures found: {temps is not None}); using manufacturer Tempco.')
            tempco = np.asarray(gpc.datasets['Cal_' + s].data[names[s][1]], dtype=float)
            data = data / (tempco[None, :] * (temp[:, None] - tref) + 1)

        wvl = radcal_wvl[valid]
        str_wvl = np.asarray([str(x) for x in wvl])
        ds_dt = np.dtype({'names': str_wvl, 'formats': [np.float64] * len(str_wvl)})

        # ---------- ES: 6S -> FRM wavelengths, then cosine correction ----------
        if s == 'ES':
            wvl_l1aqc = np.asarray([float(x) for x in node.getGroup('ES_L1AQC').getDataset('ES').data.dtype.names])

            def on_frm_grid(name):
                old = np.asarray(sixS_grp.getDataset(name).data.tolist(), dtype=float)
                return interpolate.interp1d(wvl_l1aqc, old, axis=1, fill_value='extrapolate')(wvl)

            direct_ratio = on_frm_grid('direct_ratio')
            diffuse_ratio = on_frm_grid('diffuse_ratio')
            model_irr = on_frm_grid('sixS_irradiance')
            solar_zenith = np.asarray(sixS_grp.getDataset('solar_zenith').data['solar_zenith'], dtype=float)

            if 'ES_ANGDATA_COSERROR' in unc_grp.datasets and 'ES_ANGDATA_COSERROR_AZ90' in unc_grp.datasets:
                avg_coserror, full_hemi_coserror, zenith_ang = ProcessL1b_FRMCal.cosine_error_correction(node, 'ES')
                idx = np.argmin(np.abs(zenith_ang[None, :] - solar_zenith[:, None]), axis=1)   # per-spectrum SZA, as SeaBird
                cos_corr = (1 - avg_coserror[:, idx] / 100)[valid, :].T                       # (nmes, npix)
                Fhcorr = (1 - full_hemi_coserror / 100)[valid][None, :]
                data = direct_ratio * data * cos_corr + (1 - direct_ratio) * data * Fhcorr
            else:
                writeLogFileAndPrint('ProcessL1bDALEC.processL1b_FRM: no ES cosine-error characterisation found, cosine correction skipped.')

            # relabel SIXS_MODEL on the FRM wavelengths (values already interpolated)
            for name, arr in [('sixS_irradiance', model_irr), ('direct_ratio', direct_ratio),
                              ('diffuse_ratio', diffuse_ratio)]:
                sixS_grp.getDataset(name).data = np.rec.fromarrays(np.array(arr).transpose(), dtype=ds_dt)

        # ---------- write back ----------
        grp.getDataset(s).data = np.rec.fromarrays(np.array(data).transpose(), dtype=ds_dt)
        for g in (grp, node.getGroup(s + '_L1AQC')):
            g.attributes['CAL_START'] = str(0)
            g.attributes['CAL_STOP'] = str(npix - 1)

        return True

    @staticmethod
    def processL1b(node, outFilePath):
        '''
        Non-TriOS path. ProcessL1b_Interp.processL1b_Interp will be common to both platforms
        Apply dark shutter correction to light data. Then apply either default factory cals
        or full instrument characterization. Introduce uncertainty group.
        Match timestamps and interpolate wavebands.
        '''
        node.attributes["PROCESSING_LEVEL"] = "1B"
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr
        if ConfigFile.settings["fL1bCal"] == 1:
            node.attributes['CAL_TYPE'] = 'Factory'
        elif ConfigFile.settings["fL1bCal"] == 2:
            node.attributes['CAL_TYPE'] = 'FRM-Class'
        elif ConfigFile.settings["fL1bCal"] == 3:
            node.attributes['CAL_TYPE'] = 'FRM-Full'
        node.attributes['WAVE_INTERP'] = str(ConfigFile.settings['fL1bInterpInterval']) + ' nm'

        logging.writeLogFileAndPrint(f"ProcessL1bDALEC.processL1b: {timestr}")

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        node  = dating.rootAddDateTime(node)

        # Introduce a new group for carrying L1AQC data forward.
        esGroup = node.addGroup('ES_L1AQC')
        liGroup = node.addGroup('LI_L1AQC')
        ltGroup = node.addGroup('LT_L1AQC')

        for gp in node.groups:
            if gp.id == 'ES':
                esGroup.copy(gp)
            elif gp.id == 'LI':
                liGroup.copy(gp)
            elif gp.id == 'LT':
                ltGroup.copy(gp)

        # Interpolate only the Ancillary group, and then fold in model data.
        # As in the SeaBird and TriOS pathways, this runs BEFORE the cal/char files are read: the thermal
        # coefficients generated in read_unc_coefficient_* need the filled-in ancillary data.
        if not ProcessL1b_Interp.interp_Anc(node, outFilePath):
            logging.writeLogFileAndPrint('Error interpolating ancillary data')
            return None

        # Need to fill in with model data here. This had previously been run on the GPS group, but now shifted to Ancillary group
        ancGroup = node.getGroup("ANCILLARY_METADATA")
        # Retrieve MERRA2 model ancillary data
        if ConfigFile.settings["bL1bGetAnc"] ==1:
            logging.writeLogFileAndPrint('MERRA2 data for Wind and AOD may be used to replace blank values. Reading in model data...')
            modRoot = GetAnc.getAnc(ancGroup)
        # Retrieve ECMWF model ancillary data
        elif ConfigFile.settings["bL1bGetAnc"] == 2:
            logging.writeLogFileAndPrint('ECMWF data for Wind and AOD may be used to replace blank values. Reading in model data...')
            modRoot = GetAnc_ecmwf.getAnc_ecmwf(ancGroup)
        else:
            modRoot = None

        # if modRoot is not None:
        # Regardless of whether SolarTracker/pySAS is used, Ancillary data will have been already been
        # interpolated in L1B as long as the ancillary file was read in at L1AQC. Regardless, these need
        # to have model data and/or default values incorporated.

        # If GMAO modeled data is selected in ConfigWindow, and an ancillary field data file
        # is provided in Main Window, then use the model data to fill in gaps in the field
        # record. Otherwise, use the selected default values from ConfigWindow

        # This step is only necessary for the ancillary datasets that REQUIRE
        # either field or GMAO or GUI default values. The remaining ancillary data
        # are culled from datasets in groups in L1B
        ProcessL1b.includeModelDefaults(ancGroup, modRoot)

        ######### PLACEHOOLDER: when DALEC class-based and full-FRM become available #########
        # classbased_dir needed for FRM whilst pol is handled in class-based way
        classbased_dir = os.path.join(PATH_TO_DATA, 'Class_Based_Characterizations', ConfigFile.settings['SensorType'] + "_initial")

        # The radCalDir is now the same for all cal/char regimes and regardless of whether files were downloaded from FidRadDB or not
        # radcal_dir = ConfigFile.settings['calibrationPath']
        sensor_type = ConfigFile.settings['SensorType']
        radcal_dir = os.path.join(CODE_HOME, 'Data', 'FidRadDB', sensor_type)

        # Add Class-based characterization files if needed (RAW_UNCERTAINTIES)
        if ConfigFile.settings['fL1bCal'] == 1:
            print("Factory DALEC - no uncertainty computation")

        # Add Class-based characterization files + RADCAL files
        elif ConfigFile.settings['fL1bCal'] == 2:

            print("Class-Based - uncertainty computed from class-based and RADCAL")
            print('Class-Based:', classbased_dir)
            print('RADCAL:', radcal_dir)
            node = ProcessL1b.read_unc_coefficient_class(node, classbased_dir)
            if node is None:
                logging.writeLogFileAndPrint('Error running class based uncertainties.')
                return None

        # Or add Full characterization files (RAW_UNCERTAINTIES)
        elif ConfigFile.settings['fL1bCal'] == 3:
            needed = ConfigFile.settings.get('neededCalCharsFRM', {})
            if not all(needed.get(s) for s in ['ES', 'LI', 'LT']):
                writeLogFileAndPrint('DALEC module IDs missing from config. Open Edit > Cal/Char options.')
                return None
            print("Sensor-Specific - uncertainty and corrections computed from complete FidRadDB files")
            node = ProcessL1b.read_unc_coefficient_frm(node, classbased_dir)
            if node is None:
                logging.writeLogFileAndPrint('Error loading FRM characterization files. Check directory.')
                return None
        ############################################################################################################

        # Calculate 6S model
        print('Running sixS')

        sensortype = "ES"
        # Irradiance direct and diffuse ratio
        res_sixS = ProcessL1b_FRMCal.get_direct_irradiance_ratio(node, sensortype)

        # Store sixS results in new group
        grp = node.getGroup(sensortype)
        solar_zenith = res_sixS['solar_zenith']
        # ProcessL1b_FRMCal.get_direct_irradiance_ratio uses Es bands to run 6S and then works around bands that
        #  don't have values from Tartu for full FRM. Here, use all the Es bands.
        direct_ratio = res_sixS['direct_ratio']
        diffuse_ratio = res_sixS['diffuse_ratio']
        # sixS model irradiance is in W/m^2/um, scale by 10 to match HCP units
        # model_irr = (res_sixS['direct_irr']+res_sixS['diffuse_irr']+res_sixS['env_irr'])[:,ind_raw_data]/10
        model_irr = (res_sixS['direct_irr']+res_sixS['diffuse_irr']+res_sixS['env_irr'])/10
        # model_irr = (res_sixS['direct_irr']+res_sixS['diffuse_irr']+res_sixS['env_irr'])[:,ind_nocal==False]/10

        sixS_grp = node.addGroup("SIXS_MODEL")
        for dsname in ["DATETAG", "TIMETAG2", "DATETIME"]:
            # copy datetime dataset for interp process
            ds = sixS_grp.addDataset(dsname)
            ds.data = grp.getDataset(dsname).data

        ds = sixS_grp.addDataset("sixS_irradiance")

        irr_grp = node.getGroup('ES_L1AQC')
        str_wvl = np.asarray(pd.DataFrame(irr_grp.getDataset(sensortype).data).columns)
        ds_dt = np.dtype({'names': str_wvl,'formats': [np.float64]*len(str_wvl)})
        rec_arr = np.rec.fromarrays(np.array(model_irr).transpose(), dtype=ds_dt)
        ds.data = rec_arr

        ds = sixS_grp.addDataset("direct_ratio")
        ds_dt = np.dtype({'names': str_wvl,'formats': [np.float64]*len(str_wvl)})
        rec_arr = np.rec.fromarrays(np.array(direct_ratio).transpose(), dtype=ds_dt)
        ds.data = rec_arr

        ds = sixS_grp.addDataset("diffuse_ratio")
        ds_dt = np.dtype({'names': str_wvl,'formats': [np.float64]*len(str_wvl)})
        rec_arr = np.rec.fromarrays(np.array(diffuse_ratio).transpose(), dtype=ds_dt)
        ds.data = rec_arr

        ds = sixS_grp.addDataset("solar_zenith")
        ds.columns["solar_zenith"] = solar_zenith
        ds.columnsToDataset()

        # Calibration
        #   Depending on the Configuration, process either the factory calibration, class-based characterization,
        #   or the complete instrument characterizations.
        if ConfigFile.settings['fL1bCal'] == 1:
            # TODO: Combine these three methods into one and pass the sensor type
            for sensor in ['ES','LI','LT']:
                ProcessL1bDALEC.processSensor(node,sensor)
                # ProcessL1bDALEC.processES(node)
                # ProcessL1bDALEC.processLT(node)
                # ProcessL1bDALEC.processLI(node)

        elif ConfigFile.settings['fL1bCal'] == 2:
            # NOTE: Class-based processing is not available for DALEC. Previously this branch fell through with
            #   uncalibrated counts labelled as 'FRM-Class'.
            writeLogFileAndPrint('FRM-Class processing for DALEC is not available. Use Factory or FRM-Full. Halting. *****')
            return None
        elif ConfigFile.settings['fL1bCal'] == 3:
            # FRM sensor-specific calibration, one sensor at a time as in ProcessL1bTriOS.
            # SIXS_MODEL (above) provides the direct/diffuse ratio for the ES cosine correction.
            for sensor in ['ES','LI','LT']:
                if not ProcessL1bDALEC.processL1b_FRM(node, sensor):
                    writeLogFileAndPrint(f'Error in ProcessL1bDALEC.processL1b_FRM: {sensor}')
                    return None

        # Interpolation
        # Match instruments to a common timestamp (slowest shutter, should be Lt) and
        # interpolate to the chosen spectral resolution.
        node = ProcessL1b_Interp.processL1b_Interp(node, outFilePath)

        # Datetime format is not supported in HDF5; already removed in ProcessL1b_Interp.py
        node.attributes["LI_UNITS"] = 'uW/cm^2/nm/sr'
        node.attributes["LT_UNITS"] = 'uW/cm^2/nm/sr'
        node.attributes["ES_UNITS"] = 'uW/cm^2/nm'

        return node