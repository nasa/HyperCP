# linting
from typing import Optional, Union
from collections import OrderedDict

# math
import os.path
import numpy as np
import pandas as pd
from datetime import datetime as dt

# Source
from Source import PATH_TO_CONFIG
from Source.ConfigFile import ConfigFile
from Source.CalibrationFileReader import CalibrationFileReader
from Source.ProcessL1b_FactoryCal import ProcessL1b_FactoryCal
from Source.HDFRoot import HDFRoot
from Source.HDFGroup import HDFGroup
from Source.HDFDataset import HDFDataset

# PIU
from Source.PIU.utils import utils

# Utilities
from Source.utils.loggingHCP import writeLogFileAndPrint


class PIUDataStore:
    """contains class to read and store input uncertainties for PIU"""
    sensors: list = ['ES', 'LI', 'LT']

    def __init__(self, root: HDFRoot, inpt: HDFGroup, raw_grps: Optional[dict[str: dict]]=None, raw_slices: Optional[dict[str:dict]]=None, create_empty: Optional[bool]=False):
        """ class which contains methods that provide digestable uncertainties to classes in PIU 
            converts datafile inputs into a dictionary of coefficients and uncertainties for all regimes
        """
        if ConfigFile.settings["SensorType"].lower() == "trios es only":
            PIUDataStore.sensors = ['ES']

        self.uncs:      dict = {s: {} for s in self.sensors}
        self.coeff:     dict = {s: {} for s in self.sensors}
        self.cal_level: int = ConfigFile.settings["fL1bCal"]

        self.cal_start: int = None
        self.cal_stop:  int = None

        # Masks length of all reported bands to all calibrated bands
        self.ind_rad_wvl: dict = {s: {} for s in self.sensors}
        self.wvl:         dict = {s: {} for s in self.sensors}
        self.l1ACommonCalPix: bool
        self.l1ACommonCalPix255: bool
        self.nan_mask:    np.array = None

        ancGroup = root.getGroup("ANCILLARY")
        self.sza = round(ancGroup.getDataset("SZA").columns["SZA"][0], 2) # take to 2.d.p for outputting

        try:
            ancGroup = root.getGroup("ANCILLARY")
            self.station = ancGroup.getDataset("STATION").columns["STATION"][0]
        except (AttributeError, KeyError):
            self.station = None

        try:
            acqTime = dt.strptime(root.attributes['TIME-STAMP'], '%a %b %d %H:%M:%S %Y')
            self.cast = f"{self.get_regime_Name()}_{acqTime.strftime('%Y%m%d%H%M%S')}"
        except (AttributeError, KeyError):
            self.cast = None

        if not create_empty:  # do not read uncs and coeffs if we are creating an empty PDS
            if self.cal_level == 3:
                [self.readCalFRM(root, inpt, raw_grps, raw_slices, sensor) for sensor in self.sensors]
            else:
                self.get_inttime(root)
                if self.cal_level == 2:
                    [self.readCalClassBased(inpt, sensor) for sensor in self.sensors]
                elif ConfigFile.settings['SensorType'].lower() == 'seabird':
                    [self.readCalFactory(root, inpt, sensor) for sensor in self.sensors]
                    # NOTE: If any sensors have a different number of calibrated bands (e.g., pySAS sample), we need to interp to set of pixels in order to math them together
                    #   Take the pixels of the sensor with the fewest pixels. This does NOT change the sensor-specific wavebands themselves.
                    l1APixels = [sum(self.ind_rad_wvl['ES']), sum(self.ind_rad_wvl['LI']), sum(self.ind_rad_wvl['LT'])]
                    fewestBands = l1APixels.index(min(l1APixels))
                    # Length is L1A reported pixels masked for L1B calibration bands (not necessarily L1B interpolated bands)                    
                    if fewestBands==0:
                        l1ACommonCalPix = self.ind_rad_wvl['ES']
                    elif fewestBands==1:
                        l1ACommonCalPix = self.ind_rad_wvl['LI']
                    else:
                        l1ACommonCalPix = self.ind_rad_wvl['LT']
                    # Make sure they are not only pixels in common, but commonly TRUE in those bands...
                    if any(l1ACommonCalPix[l1ACommonCalPix] !=  self.ind_rad_wvl['ES'][l1ACommonCalPix]) or\
                        any(l1ACommonCalPix[l1ACommonCalPix] !=  self.ind_rad_wvl['LI'][l1ACommonCalPix]) or\
                        any(l1ACommonCalPix[l1ACommonCalPix] !=  self.ind_rad_wvl['LT'][l1ACommonCalPix]):
                        writeLogFileAndPrint("WARNING: Pixel calibration mismatch across sensors")
                    self.l1ACommonCalPix = l1ACommonCalPix.tolist()
                    # Length is 255 pixels (redundant for sensors reporting 255 bands)
                    self.l1ACommonCalPix255 = [bool(0) for _ in range(255)]
                    self.l1ACommonCalPix255[0:len(self.l1ACommonCalPix)] = [test for test in self.l1ACommonCalPix]
                else:
                    writeLogFileAndPrint("TriOS/Dalec factory uncertainties not implemented")
                    raise NotImplementedError  # TODO: test behaviour of this - implemented because _init__ classes cannot have return or yeilds - Ashley

                # finally
                [self.read_uncertainties(root, inpt, sensor) for sensor in self.sensors]

    def get_inttime(self, root: HDFRoot):
        for s in ["ES", "LI", "LT"]:
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                gp = root.getGroup(f"{s}_LIGHT_L1AQC")

                calPath = os.path.join(
                    PATH_TO_CONFIG,
                    f"{os.path.splitext(ConfigFile.filename)[0]}_Calibration"
                )

                cf = CalibrationFileReader.read(calPath)[gp.attributes['CalFileName']]
                int_time = np.array(
                    [float(cd.coefficients[3]) if len(cd.coefficients) >= 4 else np.nan for cd in cf.data]
                )
                int_time = int(np.mean(int_time[~np.isnan(int_time)][1:]) * 1000) # convert to int (*1000 for 4sf of information)
                # cut all 0s and first pixel
            else:
                gp = root.getGroup(f"{s}_L1AQC")
                int_time = int(gp.getDataset(f"BACK_{s}").attributes['IntegrationTime'])
            
            self.coeff[s]['cal_int']  = int_time
            self.coeff[s]['int_time'] = np.mean(np.asarray(gp.datasets['INTTIME'].data.tolist()))

    #### FRM ####
    def readCalFRM(self, root, uncGrp, raw_grps, raw_slices, s_type):
        # read data
        grp = raw_grps[s_type]
        
        radcal_wvl = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '1')[1:]  # keep local var because it is used for reading the FRM cal
        self.coeff[s_type]['radcal_wvl'] = radcal_wvl
        ind_raw_wvl = (radcal_wvl > 0)  # remove any index for which we do not have radcal wvls available
        
        instrument = ConfigFile.settings['SensorType'].lower()
        if instrument == "seabird":
            radcal_raw = self.readHyperCal(grp, uncGrp, raw_slices, s_type)
            Nlin_CB_string = "CLASS_HYPEROCR_RADIANCE"
            calDate_string = f"{s_type}_LIGHT_L1AQC"
        elif instrument in ["trios", "trios es only"]:
            radcal_raw = self.readTriOSCal(grp, uncGrp, raw_slices, s_type)
            Nlin_CB_string = "CLASS_RAMSES_RADIANCE"
            calDate_string = f"{s_type}_L1AQC"
        else:
            writeLogFileAndPrint(f"{self.instsrument} not yet implemented")
            raise NotImplementedError

        # define input data
        self.coeff[s_type]['n_iter'] = 5
        self.coeff[s_type]['radcal_cal'] = radcal_raw[ind_raw_wvl]
        
        S1 = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '6', return_df=True)  # needs to be pandas dataframes
        S2 = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '8', return_df=True)

        self.coeff[s_type]['t1'] = S1.iloc[0]
        S1 = S1.drop(S1.index[0])
        self.coeff[s_type]['t2'] = S2.iloc[0]
        S2 = S2.drop(S2.index[0])
        
        S1_unc = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '7')[1:]
        S2_unc = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '9')[1:]

        if instrument in ["trios", "trios es only"]:  # if trios then convert to same units as signal
            S1 = S1/65535.0
            S2 = S2/65535.0
            S1_unc = np.asarray(S1_unc/65535.0, dtype=float)  # TODO: does this need to cast to np.array?
            S2_unc = np.asarray(S2_unc/65535.0, dtype=float)

        self.coeff[s_type]['S1'] = np.asarray(S1, dtype=float)[ind_raw_wvl]
        self.coeff[s_type]['S2'] = np.asarray(S2, dtype=float)[ind_raw_wvl]
        self.uncs[s_type]['S1'] = S1_unc[ind_raw_wvl]
        self.uncs[s_type]['S2'] = S2_unc[ind_raw_wvl]

        mZ = self.read_cal(uncGrp, s_type, "_STRAYDATA_LSF")[1:, 1:]
        mZ_unc = self.read_cal(uncGrp, s_type, "_STRAYDATA_UNCERTAINTY")[1:, 1:]

        mZ = mZ[:, ind_raw_wvl]
        self.coeff[s_type]['mZ'] = mZ[ind_raw_wvl, :]
        mZ_unc = mZ_unc[:, ind_raw_wvl]
        self.uncs[s_type]['mZ'] = mZ_unc[ind_raw_wvl, :]

        Ct = self.read_cal(uncGrp, s_type, "_TEMPDATA_CAL", f'{s_type}_TEMPERATURE_COEFFICIENTS')[1:]
        Ct_unc = self.read_cal(uncGrp, s_type, "_TEMPDATA_CAL", f'{s_type}_TEMPERATURE_UNCERTAINTIES')[1:]
        self.coeff[s_type]['Ct'] = Ct[ind_raw_wvl]
        self.uncs[s_type]['Ct'] = Ct_unc[ind_raw_wvl]

        self.coeff[s_type]['LAMP'] = self.read_cal(uncGrp, s_type, "_RADCAL_LAMP", '2')
        self.uncs[s_type]['LAMP'] = (self.read_cal(uncGrp, s_type, "_RADCAL_LAMP", '3') / 100) * self.coeff[s_type]['LAMP']

        ind_zero = radcal_raw[ind_raw_wvl] <= 0
        ind_nan = np.isnan(radcal_raw[ind_raw_wvl])
        self.coeff[s_type]['ind_nocal'] = ind_nan | ind_zero
        
        self.coeff[s_type]['wvls'] = np.asarray(radcal_wvl[ind_raw_wvl == True][self.coeff[s_type]['ind_nocal'] == False], dtype=float)
        
        # non-lin CB correction currently implemented the same for all sensor
        self.coeff[s_type]['cb_alpha'] = self.read_cal(uncGrp, Nlin_CB_string, "_LINDATA_CAL", '2')[1:]
        self.uncs[s_type]['cb_alpha']  = self.read_cal(uncGrp, Nlin_CB_string, "_LINDATA_CAL", '3')[1:]

        # Stability is handled with Class Based processing
        cal_date  = dt.strptime(root.getGroup(calDate_string).attributes['CalibrationDate'], "%Y%m%d%H%M%S")
        meas_date = dt.strptime(self.cast.split('_')[-1], "%Y%m%d%H%M%S")
        deltaTCal = meas_date - cal_date

        stab_unc = np.abs(int(deltaTCal.days)/365) * 0.01  # ignoring leap years
        self.uncs[s_type]['stab'] = np.ones_like(self.coeff[s_type]['ind_nocal']) * stab_unc # 1% stability uncertainty estimate for class based
        
        if s_type.upper() == "ES":
            raw_zen = uncGrp.getDataset(s_type + "_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
            zenith_ang = np.asarray([float(x) for x in raw_zen])

            self.coeff[s_type]['cos'] = np.asarray(pd.DataFrame(uncGrp.getDataset(s_type+"_ANGDATA_COSERROR").data))[1:, 2:]
            self.uncs[s_type]['cos'] = (np.asarray(pd.DataFrame(uncGrp.getDataset(s_type + "_ANGDATA_UNCERTAINTY").data))[1:, 2:] / 100) * np.abs(self.coeff[s_type]['cos'])
            self.coeff[s_type]['cos_90'] = np.asarray(pd.DataFrame(uncGrp.getDataset(s_type+"_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
            self.uncs[s_type]['cos_90'] = (np.asarray(pd.DataFrame(uncGrp.getDataset(s_type + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:, 2:] / 100) * np.abs(self.coeff[s_type]['cos_90'])    

            # get indexes for first and last radiometric calibration wavelengths in range [300-1000]
            i1 = np.argmin(np.abs(radcal_wvl - 300))
            i2 = np.argmin(np.abs(radcal_wvl - 1000))

            # comparing cos_error for 2 azimuth to check for asymmetry (ideally would be 0)
            azi_avg_coserr = (self.coeff[s_type]['cos'] + self.coeff[s_type]['cos_90']) / 2.
            # each value has 4 numbers azi = 0, azi = 90, -zen, +zen which need their TU uncertainties combining
            total_coserror_err = np.sqrt(
                self.uncs[s_type]['cos']**2 + 
                self.uncs[s_type]['cos_90']**2 + 
                self.uncs[s_type]['cos'][:, ::-1]**2 + 
                self.uncs[s_type]['cos_90'][:, ::-1]**2
                )

            # comparing cos_error for symetric zenith (ideally would be 0)
            zen_avg_coserr = (azi_avg_coserr + azi_avg_coserr[:, ::-1]) / 2.

            # get total error due to asymmetry  todo: find a smart way to do this without for loops
            tot_asymmetry_err = np.zeros(self.coeff[s_type]['cos'].shape, float)
            for i in range(255):
                for j in range(45):
                    tot_asymmetry_err[i, j] = np.std(
                        [self.coeff[s_type]['cos'][i, j], self.coeff[s_type]['cos_90'][i, j],
                            self.coeff[s_type]['cos'][i, -j], self.coeff[s_type]['cos_90'][i, -j]]
                    )  # get std across the 4 measurements azi_0, azi_90, zen, -zen

            zen_unc = np.sqrt(total_coserror_err**2 + tot_asymmetry_err**2)
            
            # cut indexes that are out of range
            zen_avg_coserr[0:i1, :] = 0
            zen_avg_coserr[i2:, :] = 0
            zen_unc[0:i1, :] = 0
            zen_unc[i2:, :] = 0

            # Compute full hemisperical coserror
            zen0 = np.argmin(np.abs(zenith_ang))
            zen90 = np.argmin(np.abs(zenith_ang - 90))
            deltaZen = (zenith_ang[1::] - zenith_ang[:-1])
            full_hemi_coserror = np.zeros(zen_avg_coserr.shape[0])
            sensitivity_coeff = np.zeros(zen_avg_coserr.shape[0])
            zen_unc_sum = np.zeros(zen_avg_coserr.shape[0])
            for i in range(zen_avg_coserr.shape[0]):
                full_hemi_coserror[i] = np.sum(
                    zen_avg_coserr[i, zen0:zen90] *
                    np.sin(2 * np.pi * zenith_ang[zen0:zen90] / 180) * deltaZen[zen0:zen90] * np.pi / 180
                )
                # calculate the sensitivity coefficient from the LPU
                sensitivity_coeff[i] = np.sum(
                    np.cos(2 * np.pi * zenith_ang[zen0:zen90] / 180) * deltaZen[zen0:zen90] * np.pi / 180
                )  # sin(x) differentiates to cos(x)

                zen_unc_sum[i] = np.sum(zen_unc[i, zen0:zen90])

            # get full hemispherical uncertainty using the LPU
            self.coeff[s_type]['fhemi'] = full_hemi_coserror
            self.uncs[s_type]['fhemi']  = np.sqrt(sensitivity_coeff**2 * zen_unc_sum**2)

            # save coeffs to self for access by FRM processing
            self.coeff[s_type]['zenith_ang'] =     zenith_ang
            self.uncs[s_type]['zenith_ang'] =      zen_unc
            self.coeff[s_type]['zen_avg_coserr'] = zen_avg_coserr

            res_sixS = self.read_sixS_model(root)
            self.coeff[s_type]['solar_zenith'] =  np.mean(res_sixS['solar_zenith'], axis=0)
            direct_rat = np.mean(res_sixS['direct_ratio'][:, 2:], axis=0)
            self.coeff[s_type]['direct_ratio'] = utils.interp_common_wvls(np.array(direct_rat, float), res_sixS['wavelengths'], radcal_wvl)[ind_raw_wvl]

        else:
            self.coeff[s_type]['PANEL'] = np.asarray(pd.DataFrame(uncGrp.getDataset(s_type + "_RADCAL_PANEL").data)['2'])
            self.uncs[s_type]['PANEL'] = (np.asarray(pd.DataFrame(uncGrp.getDataset(s_type + "_RADCAL_PANEL").data)['3'])/100)*self.coeff[s_type]['PANEL']
            
            # Polarisation unc from class based processing
            pol = uncGrp.getDataset(f"CLASS_{self.instrument_calfile_name(instrument)}_{s_type}_POLDATA_CAL") 
            pol.datasetToColumns()
            x = pol.columns['0']
            y = pol.columns['1']
            y_new = np.interp(radcal_wvl, x, y)
            pol.columns['0'] = radcal_wvl
            pol.columns['1'] = y_new

            self.uncs[s_type]['pol'] = np.asarray(list(pol.columns['1']))[ind_raw_wvl]
            # When using the class based uncs for FRM, should they be multiplied by some coeff?
            # thoughts - Ashley
            # to convert the polarisation and stability uncertainty from a percentage to absolute values we must multiply by the magnitude of the correction.
            # Since we are using CB regime, we do not apply the correction. Therefore the correction = 1 since it is applied by multiplying.
            # Then: U_abs = U_rel * corr_coeff = U_rel * 1 = U_rel. No conversion necessary. 
        
    def readHyperCal(self, grp, uncGrp, raw_slices, s_type):
        radcal_raw = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '2', return_df=True)
        self.coeff[s_type]['light'] = np.asarray(list(raw_slices[s_type]['LIGHT']['data'].values())).transpose()
        self.coeff[s_type]['dark']  = np.asarray(list(raw_slices[s_type]['DARK']['data'].values())).transpose()
        self.coeff[s_type]['int_time'] = np.mean(np.asarray(grp.getDataset("INTTIME").data.tolist()))
        self.coeff[s_type]['cal_int'] = radcal_raw.pop(0)
    
        return radcal_raw
    
    def readTriOSCal(self, grp, uncGrp, raw_slices, s_type):
        radcal_raw = np.array([rc[0] for rc in grp.getDataset(f"CAL_{s_type}").data])
        raw_data = np.asarray(list(raw_slices[s_type]['data'].values())).transpose() / 65535.0
        DarkPixelStart = int(grp.attributes["DarkPixelStart"])
        DarkPixelStop = int(grp.attributes["DarkPixelStop"])
        int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
        self.coeff[s_type]['cal_int'] = int(grp.getDataset("BACK_" + s_type).attributes["IntegrationTime"])

        B0 = self.read_cal(uncGrp, s_type, "_RADCAL_CAL", '4')[1:]
        B1 = self.read_cal(uncGrp, s_type, "_RADCAL_CAL", '5')[1:]
        self.coeff[s_type]['nband'] = len(B0)
        grp.attributes["nmes"] = len(raw_data)  # TODO: why is this necessary?
        
        back = np.array([B0 + B1*(int_time[n]/self.coeff[s_type]['cal_int']) for n in range(len(raw_data))])
        back_corr = raw_data - back

        self.coeff[s_type]['light'] = back_corr
        self.coeff[s_type]['dark']  = np.mean(back_corr[:, DarkPixelStart:DarkPixelStop], axis=1)
        self.coeff[s_type]['int_time'] = np.mean(int_time)  # average before passing to FRM processing
        self.coeff[s_type]['dark_std_old'] = np.std(back_corr[:, DarkPixelStart:DarkPixelStop], axis=1)
        return radcal_raw

    #### Class-Based ####
    def readCalClassBased(self, inpt: HDFGroup, s: str) -> None:
        radcal = self.extract_unc_from_grp(inpt, f"{s}_RADCAL_CAL")
        ind_rad_wvl = np.array(radcal.columns['1']) # > 0 Beware inconsistent use by Tartu of zeroed wavelengths

        corr_factor = 10 if ConfigFile.settings['SensorType'].lower() in ["sorad", "trios", "trios es only"] else 1  # Convert TriOS mW/m2/nm to uW/cm^2/nm

        self.coeff[s]['cal'] = np.asarray(list(radcal.columns['2']))[ind_rad_wvl] / corr_factor
        self.uncs[s]['cal'] = np.asarray(list(radcal.columns['3']))[ind_rad_wvl]

        self.ind_rad_wvl[s] = ind_rad_wvl

    def readCalFactory(self, node: HDFRoot, inpt: HDFGroup, s: str) -> None:
        radcal = self.extract_unc_from_grp(inpt, f"{s}_RADCAL_UNC")
        ind_rad_wvl = np.array(radcal.columns['wvl']) > 0
        # read cal start and cal stop for shaping stray-light class based uncertainties
        # self.cal_start = int(node.attributes['CAL_START'])
        # self.cal_stop = int(node.attributes['CAL_STOP'])
        # What we need here are the L1A pixel numbers rather than L1b interpolated pixels
        self.cal_start = int(node.attributes[f'{s}_LIGHT_L1AQC_START_PIXEL'])
        self.cal_stop = int(node.attributes[f'{s}_LIGHT_L1AQC_STOP_PIXEL'])

        ind_rad_wvl[0:self.cal_start] = False
        ind_rad_wvl[self.cal_stop+1:] = False

        self.uncs[s]['cal'], self.coeff[s]['cal'] = self.extract_factory_cal(node, radcal, s)  # populates dicts with calibration
        self.ind_rad_wvl[s] = ind_rad_wvl
        self.wvl[s] = np.array(radcal.columns['wvl'])

    def read_uncertainties(self, root, inpt: HDFGroup, s: str) -> None:
        instrument = ConfigFile.settings['SensorType'].lower()
        if instrument == "seabird":
            calDate_string = f"{s}_LIGHT_L1AQC"
        elif instrument in ["trios", "trios es only"]:
            calDate_string = f"{s}_L1AQC"
        else:
            writeLogFileAndPrint(f"{instrument} not yet implemented")
            raise NotImplementedError

        cal_date  = dt.strptime(root.getGroup(calDate_string).attributes['CalibrationDate'], "%Y%m%d%H%M%S")
        meas_date = dt.strptime(self.cast.split('_')[-1], "%Y%m%d%H%M%S")
        deltaTCal = meas_date - cal_date

        stab_unc = np.abs(int(deltaTCal.days)/365) * 0.01  # ignoring leap years
        self.uncs[s]['stab'] = np.ones(255, dtype=float) * stab_unc # 1% stability uncertainty estimate for class based

        self.uncs[s]['stray'] = self.extract_unc_from_grp(inpt, f"{s}_STRAYDATA_CAL", '1')
        # BUG: clipSL breaks the PIU mean_val to uncertainty comparison in MCP
        # self.clipSL(s)

        self.uncs[s]['nlin'] = self.extract_unc_from_grp(grp=inpt, name=f"{s}_NLDATA_CAL", col_name='1')
        self.uncs[s]['ct'] = self.extract_unc_from_grp(grp=inpt, name=f"{s}_TEMPDATA_CAL", col_name=f'{s}_TEMPERATURE_UNCERTAINTIES')

        if "ES" in s.upper():
            lw = None 
            up = None
            sza_range = None
            for k in inpt.datasets.keys():
                if "ES_ANGDATA_COSERROR_RANGE" in k:
                    _, sza_range = k.split('RANGE')
                    lw, up = sza_range.split('-')
                    break

            if sza_range is not None:
                if float(lw) > self.sza:
                    self.uncs[s]['cos'] = self.extract_unc_from_grp(grp=inpt, name=f"{s}_ANGDATA_COSERROR", col_name='1')
                elif float(lw) < self.sza < float(up):
                    self.uncs[s]['cos'] = self.extract_unc_from_grp(grp=inpt, name=f"{s}_ANGDATA_COSERROR_RANGE{sza_range}", col_name='1')
                else:
                    writeLogFileAndPrint(f"SZA out of bound with sza={self.sza} with range={lw}:{up}")
            else:
                writeLogFileAndPrint(f"SZA Range information not found, default to SZA < 60 calculation for SZA={self.sza}")
                self.uncs[s]['cos'] = self.extract_unc_from_grp(grp=inpt, name=f"{s}_ANGDATA_CAL", col_name='1')
        else:
            self.uncs[s]['pol'] = self.extract_unc_from_grp(grp=inpt, name=f"{s}_POLDATA_CAL", col_name='1')

        # self.nan_mask = np.where(any([(u[s] <= 0) for u in self.uncs]))  # not implemented

    #### General Read Methods ####
    @staticmethod
    def read_sixS_model(node):
        res_sixS = {}
        
        # Create a temporary group to pop date time columns
        newGrp = node.addGroup('temp')
        newGrp.copy(node.getGroup('SIXS_MODEL'))
        for ds in newGrp.datasets:
            newGrp.datasets[ds].datasetToColumns()
        sixS_gp = node.getGroup('temp')
        
        sixS_gp.getDataset("direct_ratio").columns.pop('Datetime')
        sixS_gp.getDataset("direct_ratio").columns.pop('Timetag2')
        sixS_gp.getDataset("direct_ratio").columns.pop('Datetag')
        sixS_gp.getDataset("direct_ratio").columnsToDataset()
        sixS_gp.getDataset("diffuse_ratio").columns.pop('Datetime')
        sixS_gp.getDataset("diffuse_ratio").columns.pop('Timetag2')
        sixS_gp.getDataset("diffuse_ratio").columns.pop('Datetag')
        sixS_gp.getDataset("diffuse_ratio").columnsToDataset()

        # sixS_gp.getDataset("direct_ratio").datasetToColumns()
        res_sixS['solar_zenith'] = np.asarray(sixS_gp.getDataset('solar_zenith').columns['solar_zenith'])
        res_sixS['wavelengths'] = np.asarray(list(sixS_gp.getDataset('direct_ratio').columns.keys())[2:], dtype=float)
        if 'timetag' in res_sixS['wavelengths']:
            # because timetag2 was included for some data and caused a bug
            res_sixS['wavelengths'] = res_sixS['wavelengths'][1:]
        res_sixS['direct_ratio'] = np.asarray(pd.DataFrame(sixS_gp.getDataset("direct_ratio").data))
        res_sixS['diffuse_ratio'] = np.asarray(pd.DataFrame(sixS_gp.getDataset("diffuse_ratio").data))
        node.removeGroup(sixS_gp)
        return res_sixS


    ## UTILITIES ##
    def get_regime_Name(self):
        if self.cal_level == int(3):
            return "FRM_Sensor_Specific"
        elif self.cal_level == int(2):
            return "FRM_Class_Based"
        else:
            return "Factory"

    @staticmethod
    def instrument_calfile_name(i:str) -> str:
        if i == "seabird":
            return "HYPEROCR"
        elif (i == "trios") | (i == "sorad"):
            return "RAMSES"
        else:
            return "DALEC"
    
    @staticmethod
    def read_cal(grp: HDFGroup, s: str, cal_name: str, idx: Optional[str]=None, return_df: bool = False) -> Union[np.ndarray, pd.DataFrame]:
        try:
            if grp.getDataset(s + cal_name) is None:
                print("here")
            data = pd.DataFrame(grp.getDataset(s + cal_name).data)[idx]
        except (IndexError, KeyError) as err:
            data = pd.DataFrame(grp.getDataset(s + cal_name).data)
        try:  # ask forgiveness not permission
            data = data if return_df else np.asarray(data.tolist())
        except AttributeError:
            data = np.asarray(data)
        return data

    def clipSL(self, s: str) -> None:
        start = self.cal_start
        stop = self.cal_stop
        ind_wvl = self.ind_rad_wvl[s]

        if (ind_wvl is not None) and (len(ind_wvl) == len(self.uncs[s]['stray'])):
            self.uncs[s]['stray'] = self.uncs[s]['stray'][ind_wvl]
        elif (start is not None) and (stop is not None):
            self.uncs[s]['stray'] = self.uncs[s]['stray'][start:stop + 1]
        else:
            msg = "cannot mask straylight"
            print(msg)  # to cover for potential coding errors, should not be hit in normal use

    @staticmethod
    def extract_factory_cal(node: HDFGroup, radcal: np.array, s: str) -> tuple[np.array, np.array]:
        """

        :param node: HDF root - full HDF file
        :param radcal: HDF group containing radiometric calibration
        :param s: dict key to append data to cCal and cCoef
        :param cCal: dict for storing calibration
        :param cCoef: dict for storing calibration coeficients 
        """

        cal = np.asarray(list(radcal.columns['unc']))
        calFolder = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
        calPath = os.path.join(PATH_TO_CONFIG, calFolder)
        calibrationMap = CalibrationFileReader.read(calPath)

        if ConfigFile.settings['SensorType'].lower() == "dalec":
            _, coef = ProcessL1b_FactoryCal.extract_calibration_coeff_dalec(calibrationMap, s)
        else:
            _, coef = ProcessL1b_FactoryCal.extract_calibration_coeff(node, calibrationMap, s)

        return cal, coef

    @staticmethod
    def extract_unc_from_grp(grp: HDFGroup, name: str, col_name: Optional[str] = None) -> Union[np.array, HDFDataset]:
        """

        :param grp: HDF group to take dataset from
        :param name: name of dataset
        :param col_name: name of column to extract unc from
        """
        ds = grp.getDataset(name)
        ds.datasetToColumns()
        if col_name is not None:
            return np.asarray(list(ds.columns[col_name]))
        else:
            return ds

    # saves importing Utils to Instrument classes for interpolating outputs
    @staticmethod
    def interp_common_wvls(columns, waves, newWaveBands, return_as_dict: bool=False) -> Union[np.array, OrderedDict]:
        return utils.interp_common_wvls(columns, waves, newWaveBands, return_as_dict)

    @staticmethod
    def interpolateSamples(Columns, waves, newWavebands):
        return utils.interpolateSamples(Columns, waves, newWavebands)
