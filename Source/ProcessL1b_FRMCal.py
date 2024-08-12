# python packages
import logging
import numpy as np
import os
import pandas as pd
import Py6S
import pytz
from datetime import datetime as dt
from scipy import interpolate

# internal files
from Source.ConfigFile import ConfigFile
from Source.Utilities import Utilities

class ProcessL1b_FRMCal:

    @staticmethod
    def get_direct_irradiance_ratio(node: object, sensortype: object, called_L2: bool = False) -> object:
        ''' Used for both SeaBird and TriOS L1b

            SolarTracker geometries, when available, have already been
            flipped into Ancillary and interpolated.
        '''

        ## Reading ancilliary data and SolarTracker, if necessary
        if called_L2:
            # keys change depending on if the process is called at L1B or L2, store correct keys in dictionary
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                irad_key = f'{sensortype}_LIGHT_L1AQC'
            elif ConfigFile.settings['SensorType'].lower() == 'trios':
                irad_key = f'{sensortype}_L1AQC'
            else:
                return False

            keys = dict(
                        anc = 'ANCILLARY',
                        rel = 'REL_AZ',
                        sza = 'SZA',
                        saa = 'SOLAR_AZ',
                        irad = irad_key
                        )
        else:
            # keys as before
            keys = dict(
                        anc = 'ANCILLARY_METADATA',
                        rel = 'NONE',
                        sza = 'NONE',
                        saa = 'NONE',
                        irad = f'{sensortype}'
                        )

        anc_grp = node.getGroup(keys['anc'])

        if ConfigFile.settings['bL1aqcSolarTracker'] == 1:
            rel_az = np.asarray(anc_grp.datasets['REL_AZ'].columns["REL_AZ"])
        else:
            rel_az = np.asarray(anc_grp.datasets['REL_AZ'].columns[keys['rel']])
        sun_zenith = np.asarray(anc_grp.datasets['SZA'].columns[keys['sza']])
        sun_azimuth = np.asarray(anc_grp.datasets['SOLAR_AZ'].columns[keys['saa']])

        aod = np.asarray(anc_grp.datasets['AOD'].columns["AOD"])
        anc_datetime = anc_grp.datasets['LATITUDE'].columns['Datetime']

        irr_grp = node.getGroup(keys['irad'])
        str_wvl = np.asarray(pd.DataFrame(irr_grp.getDataset(sensortype).data).columns)
        wvl = np.asarray([float(x) for x in str_wvl])
        if not called_L2:
            datetime = irr_grp.datasets['DATETIME'].data
        else:  # TODO: tested for Trios case answer is the same either method, test for seabird case
            datetag = np.asarray(pd.DataFrame(irr_grp.getDataset("DATETAG").data))
            timetag = np.asarray(pd.DataFrame(irr_grp.getDataset("TIMETAG2").data))
            dtime = [dt.strptime(str(int(x[0])) + str(int(y[0])).rjust(9, '0'), "%Y%j%H%M%S%f") for x, y in
                        zip(datetag, timetag)]
            datetime = [pytz.utc.localize(dt) for dt in dtime]  # set to utc localisation

        ## Py6S configuration
        n_mesure = len(datetime)
        nband = len(wvl)

        # Py6S called over 3min bin
        deltat = (datetime[-1]-datetime[0])/len(datetime)
        n_min = int(3*60//deltat.total_seconds())  # nb of mesures over a bin
        n_bin = len(datetime)//n_min  # nb of bin in a cast
        if len(datetime) % n_min != 0:
            # +1 to account for last points that fall in the last bin (smaller than 3 min)
            n_bin += 1

        direct = np.zeros((n_bin, nband))
        diffuse = np.zeros((n_bin, nband))
        irr_direct = np.zeros((n_bin, nband))
        irr_diffuse = np.zeros((n_bin, nband))
        irr_env = np.zeros((n_bin, nband))
        solar_zenith = np.zeros(n_bin)

        for n in range(n_bin):
            # find ancillary point that match the 1st mesure of the 3min ensemble
            ind_anc = np.argmin(np.abs(np.array(anc_datetime)-datetime[n*n_min]))
            s = Py6S.SixS()
            s.atmos_profile = Py6S.AtmosProfile.PredefinedType(Py6S.AtmosProfile.MidlatitudeSummer)
            s.aero_profile  = Py6S.AeroProfile.PredefinedType(Py6S.AeroProfile.Maritime)
            s.month = datetime[ind_anc].month
            s.day = datetime[ind_anc].day
            s.geometry.solar_z = sun_zenith[ind_anc]
            s.geometry.solar_a = sun_azimuth[ind_anc]
            s.geometry.view_a = rel_az[ind_anc]
            s.geometry.view_z = 180
            s.altitudes = Py6S.Altitudes()
            s.altitudes.set_target_sea_level()
            s.altitudes.set_sensor_sea_level()
            s.aot550 = aod[ind_anc]
            n_cores = None
            if os.name == 'nt':  # if system is windows do not do parallel processing to avoid potential error
                n_cores = 1
            wavelengths, res = Py6S.SixSHelpers.Wavelengths.run_wavelengths(s, 1e-3*wvl, n=n_cores)

            # extract value from Py6s
            # total_gaseous_transmittance[n,:] = np.array([res[x].values['total_gaseous_transmittance'] for x in range(nband)])
            # env[n,:]  = np.array([res[x].values['percent_environmental_irradiance'] for x in range(nband)])
            direct[n,:]  = np.array([res[x].values['percent_direct_solar_irradiance'] for x in range(nband)])
            diffuse[n,:]  = np.array([res[x].values['percent_diffuse_solar_irradiance'] for x in range(nband)])
            irr_direct[n,:]  = np.array([res[x].values['direct_solar_irradiance'] for x in range(nband)])
            irr_diffuse[n,:]  = np.array([res[x].values['diffuse_solar_irradiance'] for x in range(nband)])
            irr_env[n,:]  = np.array([res[x].values['environmental_irradiance'] for x in range(nband)])
            solar_zenith[n] = sun_zenith[ind_anc]


            if np.isnan(direct).any():
                logging.debug("direct contains NaN values at: %s" % wvl[np.isnan(direct)[n]])

            if np.isnan(diffuse).any():
                logging.debug("diffuse contains NaN values at: %s" % wvl[np.isnan(diffuse)[n]])

            if np.isnan(irr_direct).any():
                logging.debug("irr_direct contains NaN values at: %s" % wvl[np.isnan(irr_direct)[n]])

            if np.isnan(irr_diffuse).any():
                logging.debug("irr_diffuse contains NaN values at: %s" % wvl[np.isnan(irr_diffuse)[n]])

            if np.isnan(irr_env).any():
                logging.debug("irr_env contains NaN values at: %s" % wvl[np.isnan(irr_env)[n]])

            if np.isnan(solar_zenith).any():
                logging.debug("solar_zenith contains NaN values at: %s" % wvl[np.isnan(solar_zenith)[n]])

            # Check for potential NaN values and interpolate them with neighbour
            # direct
            ind0 = np.where(np.isnan(direct[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        direct[n,i0] = direct[n,i0-1]
                    else:
                        direct[n,i0] = (direct[n,i0-1]+direct[n,i0+1])/2
            # diffuse
            ind0 = np.where(np.isnan(diffuse[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        diffuse[n,i0] = diffuse[n,i0-1]
                    else:
                        diffuse[n,i0] = (diffuse[n,i0-1]+diffuse[n,i0+1])/2

            # irr_direct
            ind0 = np.where(np.isnan(irr_direct[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        irr_direct[n,i0] = irr_direct[n,i0-1]
                    else:
                        irr_direct[n,i0] = (irr_direct[n,i0-1]+irr_direct[n,i0+1])/2

            # irr_diffuse
            ind0 = np.where(np.isnan(irr_diffuse[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        irr_diffuse[n,i0] = irr_diffuse[n,i0-1]
                    else:
                        irr_diffuse[n,i0] = (irr_diffuse[n,i0-1]+irr_diffuse[n,i0+1])/2

            # irr_env
            ind0 = np.where(np.isnan(irr_env[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        irr_env[n,i0] = irr_env[n,i0-1]
                    else:
                        irr_env[n,i0] = (irr_env[n,i0-1]+irr_env[n,i0+1])/2

            # Check for potential zero values and interpolate them with neighbour
            val, ind0 = np.where([direct[n,:]==0])
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        direct[n,i0] = direct[n,i0-1]
                    else:
                        direct[n,i0] = (direct[n,i0-1]+direct[n,i0+1])/2

        # if only 1 bin, repeat value for each timestamp over cast duration (<3min)
        res_py6s = {}
        if n_bin == 1:
            logging.warning("n_bin == 1, cast is probably too short")
            res_py6s['solar_zenith'] = np.repeat(solar_zenith, n_mesure)
            res_py6s['direct_ratio'] = np.repeat(direct, n_mesure, axis=0)
            res_py6s['diffuse_ratio'] = np.repeat(diffuse, n_mesure, axis=0)
            res_py6s['direct_irr'] = np.repeat(irr_direct, n_mesure, axis=0)
            res_py6s['diffuse_irr'] = np.repeat(irr_diffuse, n_mesure, axis=0)
            res_py6s['env_irr'] = np.repeat(irr_env, n_mesure, axis=0)
        # if more than 1 bin, interpolate fo each timestamp
        else:
            x_bin  = [n*n_min for n in range(n_bin)]
            x_full = np.linspace(0, n_mesure, n_mesure)
            f =  interpolate.interp1d(x_bin, solar_zenith, fill_value='extrapolate')
            res_py6s['solar_zenith'] = f(x_full)
            f =  interpolate.interp1d(x_bin, direct, fill_value='extrapolate', axis=0)
            res_py6s['direct_ratio'] = f(x_full)
            f =  interpolate.interp1d(x_bin, diffuse, fill_value='extrapolate', axis=0)
            res_py6s['diffuse_ratio'] = f(x_full)
            f =  interpolate.interp1d(x_bin, irr_direct, fill_value='extrapolate', axis=0)
            res_py6s['direct_irr'] = f(x_full)
            f =  interpolate.interp1d(x_bin, irr_diffuse, fill_value='extrapolate', axis=0)
            res_py6s['diffuse_irr'] = f(x_full)
            f =  interpolate.interp1d(x_bin, irr_env, fill_value='extrapolate', axis=0)
            res_py6s['env_irr'] = f(x_full)

        return res_py6s

    @staticmethod
    def cosine_error_correction(node, sensorstring):
        ''' Used for both SeaBird and TriOS L1b'''

        ## Angular cosine correction (for Irradiance)
        unc_grp = node.getGroup('RAW_UNCERTAINTIES')
        radcal_wvl = np.asarray(pd.DataFrame(unc_grp.getDataset(sensorstring+"_RADCAL_CAL").data)['1'][1:].tolist())
        coserror = np.asarray(pd.DataFrame(unc_grp.getDataset(sensorstring+"_ANGDATA_COSERROR").data))[1:,2:]
        coserror_90 = np.asarray(pd.DataFrame(unc_grp.getDataset(sensorstring+"_ANGDATA_COSERROR_AZ90").data))[1:,2:]
        zenith_ang = unc_grp.getDataset(sensorstring+"_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
        # zenith_ang_90 = unc_grp.getDataset(sensortype+"_ANGDATA_COSERROR_AZ90").attributes["COLUMN_NAMES"].split('\t')[2:]
        i1 = np.argmin(np.abs(radcal_wvl-300))
        i2 = np.argmin(np.abs(radcal_wvl-1000))
        zenith_ang = np.asarray([float(x) for x in zenith_ang])

        # comparing cos_error for 2 azimuth
        AZI_delta_cos = coserror-coserror_90

        # if delta < 2% : averaging the 2 azimuth plan
        AZI_avg_coserror = (coserror+coserror_90)/2.

        # comparing cos_error for symetric zenith
        ZEN_delta_cos = AZI_avg_coserror - AZI_avg_coserror[:,::-1]

        # if delta < 2% : averaging symetric zenith
        ZEN_avg_coserror = (AZI_avg_coserror+AZI_avg_coserror[:,::-1])/2.

        # set coserror to 1 outside range [450,700]
        ZEN_avg_coserror[0:i1,:] = 0
        ZEN_avg_coserror[i2:,:] = 0

        # Compute full hemisperical coserror
        zen0 = np.argmin(np.abs(zenith_ang))
        zen90 = np.argmin(np.abs(zenith_ang-90))
        deltaZen = (zenith_ang[1::]-zenith_ang[:-1])
        full_hemi_coserror = np.zeros(255)

        for i in range(255):
            full_hemi_coserror[i] = np.sum(ZEN_avg_coserror[i,zen0:zen90]*np.sin(2*np.pi*zenith_ang[zen0:zen90]/180)*deltaZen[zen0:zen90]*np.pi/180 )

        return ZEN_avg_coserror, full_hemi_coserror, zenith_ang

    @staticmethod
    def Zong_SL_correction_matrix(LSF, n_IB: int = 3):
        LSF[LSF<=0] = 0
        SDF = np.copy(LSF)
        for i in range(len(LSF)):
        # for j in range(len(LSF)):
            # define IB indexes
            j1 = i-n_IB
            j2 = i+n_IB
            if j1 <= 0:
                j1 = 0
            IB = LSF[i,j1:j2+1]
            IBsum = np.sum(IB)
            if np.sum(IB) == 0:
                IBsum = 1.0
            # Zong eq. 1
            SDF[i,:] = SDF[i,:]/float(IBsum)
            SDF[i,j1:j2+1] = 0

        A = np.identity(len(LSF)) + SDF   # Matrix A from eq. 8
        C = np.linalg.inv(A)              # Matrix C from eq. 9

        return C

    @staticmethod
    def Slaper_SL_correction(input_data, SL_matrix, n_iter=5):
        nband = len(input_data)
        m_norm = np.zeros(nband)
        mC = np.zeros((n_iter+1, nband))
        mX = np.zeros((n_iter+1, nband))
        mZ = SL_matrix
        mX[0, :] = input_data

        for i in range(nband):
            jstart = np.max([0,i-10])
            jstop  = np.min([nband,i+10])
            m_norm[i] = np.sum(mZ[i,jstart:jstop])  # eq 4

        for i in range(nband):
            if m_norm[i] == 0:
                mZ[i,:] = np.zeros(nband)
            else:
                mZ[i,:] = mZ[i,:]/m_norm[i]   # eq 5

        for k in range(1,n_iter+1):
            for i in range(nband):
                mC[k-1,i] = mC[k-1,i] + np.sum(mX[k-1,:]*mZ[i,:])  # eq 6
                if mC[k-1,i] == 0:
                    mX[k,i] = 0
                else:
                    mX[k,i] = (mX[k-1,i] * mX[0,i]) / mC[k-1,i]   # eq 7

        return mX[n_iter-1,:]

    @staticmethod
    def processL1b_SeaBird(node, calibrationMap):
        # calibration of HyperOCR following the FRM processing of FRM4SOC2
        esUnits = None
        liUnits = None
        ltUnits = None
        pyrUnits = None

        now = dt.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr
        msg = f"ProcessL1b_FactoryCal.processL1b: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        msg = "Applying factory calibrations."
        print(msg)
        Utilities.writeLogFile(msg)

        for gp in node.groups:
            if 'L1AQC' not in gp.id:
                msg = f'  Group: {gp.id}'
                print(msg)
                Utilities.writeLogFile(msg)
                if "CalFileName" in gp.attributes:
                    if gp.attributes["CalFileName"] != 'ANCILLARY':  # GPS constructed from Ancillary data will cause bug here
                        cf = calibrationMap[gp.attributes["CalFileName"]]
                        #print(gp.id, gp.attributes)
                        msg = f'    File: {cf.id}'
                        print(msg)
                        Utilities.writeLogFile(msg)

                        if esUnits == None:
                            esUnits = cf.getUnits("ES")
                        if liUnits == None:
                            liUnits = cf.getUnits("LI")
                        if ltUnits == None:
                            ltUnits = cf.getUnits("LT")
                        if pyrUnits == None:
                            pyrUnits = cf.getUnits("T") #Pyrometer

        node.attributes["LI_UNITS"] = liUnits
        node.attributes["LT_UNITS"] = ltUnits
        node.attributes["ES_UNITS"] = esUnits
        node.attributes["L1AQC_UNITS"] = 'count'
        node.attributes["SATPYR_UNITS"] = pyrUnits

        # setup node attrs

        unc_grp = node.getGroup('RAW_UNCERTAINTIES')

        for sensortype in ['ES', 'LI', 'LT']:
            print('FRM Processing:', sensortype)
            # Read data
            grp = node.getGroup(sensortype)
            raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())
            int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())

            # Read FRM characterisation
            radcal_wvl = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['1'][1:].tolist())
            radcal_cal = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['2']
            dark = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['4'][1:].tolist())
            S1 = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['6']
            S2 = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['8']
            Ct = pd.DataFrame(unc_grp.getDataset(sensortype+"_TEMPDATA_CAL").data)[sensortype+"_TEMPERATURE_COEFFICIENTS"][1:].tolist()
            mZ = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_STRAYDATA_LSF").data))
            mZ = mZ[1:,1:] # remove 1st line and column, we work on 255 pixel not 256.
            LAMP = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_LAMP").data)['2'])

            # create Zong SDF straylight correction matrix
            C_zong = ProcessL1b_FRMCal.Zong_SL_correction_matrix(mZ)

            # Defined constants
            nband = len(radcal_wvl)
            nmes  = len(raw_data)
            # n_iter = 5

            # Non-linearity alpha computation
            cal_int = radcal_cal.pop(0)
            t1 = S1.pop(0)
            t2 = S2.pop(0)
            k = t1/(t2-t1)
            S12 = (1+k)*S1 - k*S2

            # S12_sl_corr = ProcessL1b_FRMCal.Slaper_SL_correction(S12, mZ, n_iter)  # Slapper
            S12_sl_corr = np.matmul(C_zong, S12) # Zong SL corr
            alpha = ((S1-S12)/(S12**2)).tolist()
            LAMP = np.pad(LAMP, (0, nband-len(LAMP)), mode='constant') # PAD with zero if not 255 long

            ## sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
            ind_zero = radcal_cal<=0
            ind_nan  = np.isnan(radcal_cal)
            ind_nocal = ind_nan | ind_zero

            # keep only defined wavelength
            wvl = radcal_wvl[ind_nocal==False]
            str_wvl = np.asarray([str(x) for x in wvl])
            dark = dark[ind_nocal==False]
            alpha = np.asarray(alpha)[ind_nocal==False]
            Ct = np.asarray(Ct)[ind_nocal==False]
            mZ = mZ[:, ind_nocal==False]
            mZ = mZ[ind_nocal==False, :]
            C_zong = C_zong[:, ind_nocal==False]
            C_zong = C_zong[ind_nocal==False, :]
            ind_raw_data = (radcal_cal[radcal_wvl>0])>0

            # Updated calibration gain
            if sensortype == "ES":
                updated_radcal_gain = (S12_sl_corr/LAMP) * (10*cal_int/t1)
                # Compute avg cosine error
                avg_coserror, full_hemi_coserror, zenith_ang = ProcessL1b_FRMCal.cosine_error_correction(node, sensortype)
                # Irradiance direct and diffuse ratio
                res_py6s = ProcessL1b_FRMCal.get_direct_irradiance_ratio(node, sensortype)
            else:
                PANEL = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_PANEL").data)['2'])
                PANEL = np.pad(PANEL, (0, nband-len(PANEL)), mode='constant')
                updated_radcal_gain = (np.pi*S12_sl_corr)/(LAMP*PANEL) * (10*cal_int/t1)

            # set 1 instead of 0 to perform calibration (otherwise division per 0)
            updated_radcal_gain[ind_nocal==True] = 1
            updated_radcal_gain = updated_radcal_gain[ind_nocal==False]

            FRM_mesure = np.zeros((nmes, len(updated_radcal_gain)))
            for n in range(nmes):
                # raw data
                data = raw_data[n][ind_raw_data]
                # Non-linearity
                data = data*(1-alpha*data)
                # Straylight
                # data = ProcessL1b_FRMCal.Slaper_SL_correction(data, mZ, n_iter)
                data = np.matmul(C_zong, data)
                # Calibration
                data = data * (cal_int/int_time[n]) / updated_radcal_gain
                # thermal
                data = data * Ct
                # Cosine correction
                if sensortype == "ES":
                    # retrive py6s variables for given wvl
                    solar_zenith = res_py6s['solar_zenith'][n]
                    direct_ratio = res_py6s['direct_ratio'][n,ind_raw_data]
                    diffuse_ratio = res_py6s['diffuse_ratio'][n,ind_raw_data]
                    ind_closest_zen = np.argmin(np.abs(zenith_ang-solar_zenith))
                    cos_corr = (1-avg_coserror[:,ind_closest_zen]/100)[ind_nocal==False]
                    Fhcorr = (1-full_hemi_coserror/100)[ind_nocal==False]
                    data = (direct_ratio*data*cos_corr) + ((1-direct_ratio)*data*Fhcorr)
                    FRM_mesure[n,:] = data
                else:
                    FRM_mesure[n,:] = data

            # Remove wvl without calibration from the dataset
            filtered_mesure = FRM_mesure
            filtered_wvl = str_wvl

            # Replace raw data with calibrated data in hdf root
            ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
            rec_arr = np.rec.fromarrays(np.array(filtered_mesure).transpose(), dtype=ds_dt)
            grp.getDataset(sensortype).data = rec_arr

            # Store Py6S results in new group
            if sensortype == "ES":
                solar_zenith = res_py6s['solar_zenith']
                direct_ratio = res_py6s['direct_ratio'][:,ind_raw_data]
                diffuse_ratio = res_py6s['diffuse_ratio'][:,ind_raw_data]
                # Py6S model irradiance is in W/m^2/um, scale by 10 to match HCP units
                model_irr = (res_py6s['direct_irr']+res_py6s['diffuse_irr']+res_py6s['env_irr'])[:,ind_raw_data]/10

                py6s_grp = node.addGroup("PY6S_MODEL")
                for dsname in ["DATETAG", "TIMETAG2", "DATETIME"]:
                    # copy datetime dataset for interp process
                    ds = py6s_grp.addDataset(dsname)
                    ds.data = grp.getDataset(dsname).data

                ds = py6s_grp.addDataset("py6s_irradiance")
                ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
                rec_arr = np.rec.fromarrays(np.array(model_irr).transpose(), dtype=ds_dt)
                ds.data = rec_arr

                ds = py6s_grp.addDataset("direct_ratio")
                ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
                rec_arr = np.rec.fromarrays(np.array(direct_ratio).transpose(), dtype=ds_dt)
                ds.data = rec_arr

                ds = py6s_grp.addDataset("diffuse_ratio")
                ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
                rec_arr = np.rec.fromarrays(np.array(diffuse_ratio).transpose(), dtype=ds_dt)
                ds.data = rec_arr

                ds = py6s_grp.addDataset("solar_zenith")
                ds.columns["solar_zenith"] = solar_zenith
                ds.columnsToDataset()

        return True