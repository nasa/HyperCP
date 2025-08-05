# linting
from typing import Optional, Union
from collections import OrderedDict

# math
import numpy as np
import pandas as pd

# Source
from Source.ConfigFile import ConfigFile
from Source.Utilities import Utilities
from Source.HDFRoot import HDFRoot
from Source.HDFGroup import HDFGroup
from Source.HDFDataset import HDFDataset

# PIU
from Source.PIU.utils import utils

# contains class to read and store input uncertainties for PIU

class PIUDataStore:
    sensors: list = ['ES', 'LI', 'LT']

    def __init__(self, root: HDFRoot, input: HDFGroup, raw_grps: Optional[dict[str: dict]]=None, raw_slices: Optional[dict[str:dict]]=None):
        """ class which contains methods that provide digestable uncertainties to classes in PIU 
            converts datafile inputs into a dictionary of coefficients and uncertainties for all regimes
        """
        self.uncs:      dict = {s: {} for s in self.sensors}
        self.coeff:     dict = {s: {} for s in self.sensors}
        self.cal_level: int = ConfigFile.settings["fL1bCal"]

        self.cal_start: int = None
        self.cal_stop:  int = None

        self.ind_rad_wvl: dict = {s: {} for s in self.sensors}
        self.nan_mask:    np.array = None

        instrument = ConfigFile.settings['SensorType'].lower()  # get instrument type
        if self.cal_level == 3:
            [self.readCalFRM(root, input, raw_grps, raw_slices, sensor) for sensor in self.sensors]
        else:
            if self.cal_level == 2:
                [self.readCalClassBased(input, sensor, instrument) for sensor in self.sensors]
            elif instrument == 'seabird':
                [self.readCalFactory(root, input, sensor) for sensor in self.sensors]
            else:
                msg = "TriOS/Dalec factory uncertainties not implemented"
                Utilities.writeLogFile(msg)
                print(msg)
                raise NotImplementedError  # TODO: test behaviour of this - implemented because _init__ classes cannot have return or yeilds - Ashley
            
            # finally
            [self.read_uncertainties(input, sensor) for sensor in self.sensors]
    
    #### FRM ####
    def readCalFRM(self, root, uncGrp, raw_grps, raw_slices, s_type):
        # read data
        grp = raw_grps[s_type]
        
        radcal_wvl = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '1')[1:]  # keep local var because it is used for reading the FRM cal
        self.coeff[s_type]['radcal_wvl'] = radcal_wvl
        ind_raw_wvl = (radcal_wvl > 0)  # remove any index for which we do not have radcal wvls available

        if self.instrument == "seabird":
            radcal_cal_raw = self.readHyperCal(grp, uncGrp, raw_slices, s_type)
        elif self.instrument == "trios":
            radcal_cal_raw = self.readTriOSCal(grp, uncGrp, raw_slices, s_type)
        else:
            msg = f"{self.instsrument} not yet implemented"
            print(msg)
            Utilities.writeLogFile(msg)
            raise NotImplementedError

        # define input data
        self.coeff[s_type]['n_iter'] = 5
        self.coeff[s_type]['radcal_cal'] = radcal_cal_raw[ind_raw_wvl]
        
        S1 = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '6', return_df=True)  # needs to be pandas dataframes
        S2 = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '8', return_df=True)

        self.coeff[s_type]['t1'] = S1.iloc[0]
        S1 = S1.drop(S1.index[0])
        self.coeff[s_type]['t2'] = S2.iloc[0]
        S2 = S2.drop(S2.index[0])
        
        S1_unc = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '7')[1:]
        S2_unc = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '9')[1:]

        if self.instrument == "trios":  # if trios then convert to same units as signal
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

        ind_zero = radcal_cal_raw[ind_raw_wvl] <= 0
        ind_nan = np.isnan(radcal_cal_raw[ind_raw_wvl])
        self.coeff[s_type]['ind_nocal'] = ind_nan | ind_zero
        
        self.coeff[s_type]['wvls'] = np.asarray(radcal_wvl[ind_raw_wvl == True][self.coeff[s_type]['ind_cal'] == True], dtype=float)  # optimise by removing ind_cal, replace with ind_nocal==False
        
        # Stability is handled with Class Based processing
        self.uncs[s_type]['stab'] = np.ones_like(self.coeff[s_type]['ind_cal']) * 0.01 # 1% stability uncertainty estimate for class based

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
            pol = uncGrp.getDataset(f"CLASS_HYPEROCR_{s_type}_POLDATA_CAL")
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
        radcal_cal_raw = self.read_cal(uncGrp, s_type, '_RADCAL_CAL', '2', return_df=True)
        self.coeff[s_type]['light'] = np.asarray(list(raw_slices[s_type]['LIGHT']['data'].values())).transpose()
        self.coeff[s_type]['dark']  = np.asarray(list(raw_slices[s_type]['DARK']['data'].values())).transpose()
        self.coeff[s_type]['int_time'] = np.mean(np.asarray(grp.getDataset("INTTIME").data.tolist()))
        self.coeff[s_type]['cal_int'] = radcal_cal_raw.pop(0)
    
        return radcal_cal_raw
    
    def readTriOSCal(self, grp, uncGrp, raw_slices, s_type):
        radcal_cal_raw = grp.getDataset(f"CAL_{s_type}").data
        raw_data = np.asarray(list(raw_slices[s_type]['data'].values())).transpose() / 65535.0
        DarkPixelStart = int(grp.attributes["DarkPixelStart"])
        DarkPixelStop = int(grp.attributes["DarkPixelStop"])
        self.coeff[s_type]['int_time'] = np.asarray(grp.getDataset("INTTIME").data.tolist())  # no mean for TriOS
        self.coeff[s_type]['cal_int'] = int(grp.getDataset("BACK_" + s_type).attributes["IntegrationTime"])
        B0 = self.read_cal(uncGrp, s_type, "_RADCAL_CAL", '4')[1:]
        B1 = self.read_cal(uncGrp, s_type, "_RADCAL_CAL", '5')[1:]
        self.coeff[s_type]['nband'] = len(B0)
        grp.attributes["nmes"] = len(raw_data)  # TODO: why is this necessary?
        
        back = np.array([B0 + B1*(self.coeff[s_type]['int_time'][n]/self.coeff[s_type]['cal_int']) for n in range(nmes)])
        back_corr = raw_data - back

        self.coeff[s_type]['light'] = back_corr
        self.coeff[s_type]['dark']  = np.mean(back_corr[:, DarkPixelStart:DarkPixelStop], axis=1)

        return radcal_cal_raw

    #### Class-Based ####
    def readCalClassBased(self, inpt: HDFGroup, s: str, i_type: str) -> None:
        radcal = self.extract_unc_from_grp(inpt, f"{s}_RADCAL_CAL")
        ind_rad_wvl = (np.array(radcal.columns['1']) > 0)  # where radcal wvls are available
        
        corr_factor = 10 if (i_type == "trios" or i_type == "sorad") else 1 # Convert TriOS mW/m2/nm to uW/cm^2/nm
        self.coeff[s]['cal'] = np.asarray(list(radcal.columns['2']))[ind_rad_wvl] / corr_factor
        self.uncs[s]['cal'] = np.asarray(list(radcal.columns['3']))[ind_rad_wvl]

        self.ind_rad_wvl[s] = ind_rad_wvl

    def readCalFactory(self, node: HDFRoot, inpt: HDFGroup, s: str) -> None:
        radcal = self.extract_unc_from_grp(inpt, f"{s}_RADCAL_UNC")
        ind_rad_wvl = (np.array(radcal.columns['wvl']) > 0)  # all radcal wvls should be available from sirrex
        # read cal start and cal stop for shaping stray-light class based uncertainties
        self.cal_start = int(node.attributes['CAL_START'])
        self.cal_stop = int(node.attributes['CAL_STOP'])

        self.uncs['cal'], self.coeff['cal'] = self.extract_factory_cal(node, radcal, s)  # populates dicts with calibration
        self.ind_rad_wvl[s] = ind_rad_wvl

    def read_uncertainties(self, inpt: HDFGroup, s: str) -> None:
        self.uncs[s]['stab'] = self.extract_unc_from_grp(inpt, f"{s}_STABDATA_CAL", '1')
        self.uncs[s]['stray'] = self.extract_unc_from_grp(inpt, f"{s}_STRAYDATA_CAL", '1')
        self.clipSL(s)

        self.uncs[s]['nlin'] = self.extract_unc_from_grp(grp=inpt, name=f"{s}_NLDATA_CAL", col_name='1')
        self.uncs[s]['ct'] = self.extract_unc_from_grp(grp=inpt, name=f"{s}_TEMPDATA_CAL", col_name=f'{s}_TEMPERATURE_UNCERTAINTIES')

        if "ES" in s.upper():
            self.uncs[s]['cos'] = self.extract_unc_from_grp(grp=inpt, name=f"{s}_POLDATA_CAL", col_name='1')
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
    @staticmethod
    def read_cal(grp: HDFGroup, s: str, cal_name: str, idx: Optional[str]=None, return_df: bool = False) -> Union[np.ndarray, pd.DataFrame]:
        try:
            data = pd.DataFrame(grp.getDataset(s + cal_name).data)[idx]
        except (IndexError, KeyError):
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
    def extract_factory_cal(node: HDFGroup, radcal: np,array, s: str) -> tuple[np.array, np.array]:
        """

        :param node: HDF root - full HDF file
        :param radcal: HDF group containing radiometric calibration
        :param s: dict key to append data to cCal and cCoef
        :param cCal: dict for storing calibration
        :param cCoef: dict for storing calibration coeficients 
        """
        from os import path
        from Source import PATH_TO_CONFIG
        from Source.CalibrationFileReader import CalibrationFileReader
        from Source.ProcessL1b_FactoryCal import ProcessL1b_FactoryCal

        cal = np.asarray(list(radcal.columns['unc']))
        calFolder = path.splitext(ConfigFile.filename)[0] + "_Calibration"
        calPath = path.join(PATH_TO_CONFIG, calFolder)
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
