# import python packages
import os
import numpy as np
import scipy as sp
import pandas as pd
import copy
import calendar
import warnings
from datetime import datetime
from collections import OrderedDict
from decimal import Decimal
from abc import ABC, abstractmethod
from typing import Union, Optional, Any
from inspect import currentframe, getframeinfo

# NPL packages
import punpy
import comet_maths as cm

# HCP files
from Source import PATH_TO_CONFIG
from Source.Utilities import Utilities
from Source.ConfigFile import ConfigFile
from Source.HDFRoot import HDFRoot  # for typing and docstrings
from Source.HDFGroup import HDFGroup  # for typing and docstrings
from Source.HDFDataset import HDFDataset
from Source.ProcessL1b_FRMCal import ProcessL1b_FRMCal
from Source.Uncertainty_Analysis import Propagate
from Source.Weight_RSR import Weight_RSR
from Source.CalibrationFileReader import CalibrationFileReader
from Source.ProcessL1b_FactoryCal import ProcessL1b_FactoryCal
from Source.Uncertainty_Visualiser import UncertaintyGUI # class for uncertainty visualisation plots


class BaseInstrument(ABC):  # Inheriting ABC allows for more function decorators which exist to give warnings to coders.
    """Base class for instrument uncertainty analysis. Abstract methods are utilised where appropriate. The core idea is
    to reuse as much code as possible whilst making it simpler to add functionality through the addition of child
    classes"""

    # variable placed here will be made available to all instances of Instrument class. Varname preceded by '_'
    # to indicate privacy, this should NOT be changed at runtime
    _SATELLITES: dict = {
        "S3A": {"name": "Sentinel3A", "config": "bL2WeightSentinel3A", "Weight_RSR": Weight_RSR.Sentinel3Bands()},
        "S3B": {"name": "Sentinel3B", "config": "bL2WeightSentinel3B", "Weight_RSR": Weight_RSR.Sentinel3Bands()},
        "MOD-A": {"name": "MODISA", "config": "bL2WeightMODISA", "Weight_RSR": Weight_RSR.MODISBands()},
        "MOD-T": {"name": "MODIST", "config": "bL2WeightMODIST", "Weight_RSR": Weight_RSR.MODISBands()},
        "VIIRS-N": {"name": "VIIRSN", "config": "bL2WeightVIIRSN", "Weight_RSR": Weight_RSR.VIIRSBands()},
        "VIIRS-J": {"name": "VIIRSJ", "config": "bL2WeightVIIRSJ", "Weight_RSR": Weight_RSR.VIIRSBands()},
    }  # list of avaialble sensors with their config file names a name for the xUNC key and associated Weight_RSR bands

    def __init__(self):
        # use this to switch the straylight correction method -> FOR UNCERTAINTY PROPAGATION ONLY <- between SLAPER and
        # ZONG. Not added to config file settings because this isn't intended for the end user.
        self.sl_method: str = 'ZONG'

    @abstractmethod
    def lightDarkStats(self, grp: Union[HDFGroup, list], slice: list, sensortype: str) -> dict[np.array]:
        """
        method to return the noise (std before and after light-dark substitution) and averages for light and dark data. 
        Refer to D-10 figure-8, Eq-10 for Radiance and figure-9, Eq-11 for Irradiance. Both figures and equations indicate 
        signal as "S" with std Dark/Light being DN_dark/DN_light respectively. 

        :param grp: HDFGroup representing the sensor specific data
        :param slice: Ensembled sensor data
        :param sensortype: sensor name

        :return:
        """
        # abstract method indicates the requirement for all child/derived classes to have a lightDarkStats method, this will be
        # sensor specific and is required for generateSensorStats. For Dalec (or other sensors) it must be a function
        # that outputs a dictionary containing:
        # {
        # "ave_Light": averaged light data,
        # "ave_Dark": averaged dark data,
        # "std_Light": standard deviation from the mean of light data,
        # "std_Dark": standard deviation from the mean of dark data,
        # "std_Signal" standard deviation from the mean of the instrument signal,
        # }
        # all standard deviations are divided by root N (number of scans) to become standard deviation from the mean.
        pass

    def generateSensorStats(self, InstrumentType: str, rawData: dict, rawSlice: dict, newWaveBands: np.array
                            ) -> dict[str: np.array]:
        """
        Generate Sensor Stats calls lightDarkStats for a given instrument. Once sensor statistics are known, they are 
        interpolated to common wavebands to match the other L1B sensor inputs Es, Li, & Lt.

        :return: dictionary of statistics used later in the processing pipeline. Keys are:
        [ave_Light, ave_Dark, std_Light, std_Dark, std_Signal]
        """
        output = {}  # used tp store standard deviations and averages as a function return for generateSensorStats
        types = ['ES', 'LI', 'LT']
        for sensortype in types:
           if InstrumentType.lower() == "trios" or InstrumentType.lower() == "sorad":
                # filter nans
                self.apply_NaN_Mask(rawSlice[sensortype]['data'])
                # RawData is the full group - this is used to get a few attributes only
                # rawSlice is the ensemble 'slice' of raw data currently to be evaluated
                #  todo: check the shape and that there are no nans or infs
                output[sensortype] = self.lightDarkStats(
                    copy.deepcopy(rawData[sensortype]), copy.deepcopy(rawSlice[sensortype]), sensortype
                )
                # copy.deepcopy ensures RAW data is unchanged for FRM uncertainty generation.
           elif InstrumentType.lower() == "dalec":
                # RawData is the full group - this is used to get a few attributes only
                # rawSlice is the ensemble 'slice' of raw data currently to be evaluated
                #  todo: check the shape and that there are no nans or infs
                output[sensortype] = self.lightDarkStats(
                    copy.deepcopy(rawData[sensortype]), copy.deepcopy(rawSlice[sensortype]), sensortype
                )
                # copy.deepcopy ensures RAW data is unchanged for FRM uncertainty generation.
           elif InstrumentType.lower() == "seabird":
                # rawData here is the group, passed along only for the purpose of
                # confirming "FrameTypes", i.e., ShutterLight or ShutterDark. Calculations
                # are performed on the Slice.
                # output contains:
                # ave_Light: (array 1 x number of wavebands)
                # ave_Dark: (array 1 x number of wavebands)
                # std_Light: (array 1 x number of wavebands)
                # std_Dark: (array 1 x number of wavebands)
                # std_Signal: OrdDict by wavebands: sqrt( (std(Light)^2 + std(Dark)^2)/ave(Light)^2 )

                # filter nans
                # this should work because of the interpolation, however I cannot test this as I do not have seabird
                # data with NaNs
                # self.apply_NaN_Mask(rawSlice[sensortype]['LIGHT'])
                # self.apply_NaN_Mask(rawSlice[sensortype]['DARK'])
                output[sensortype] = self.lightDarkStats(
                    [rawData[sensortype]['LIGHT'],
                    rawData[sensortype]['DARK']],
                    [rawSlice[sensortype]['LIGHT'],
                    rawSlice[sensortype]['DARK']],
                    sensortype
                )
           if not output[sensortype]:
                msg = "Could not generate statistics for the ensemble"
                print(msg)
                return False

        # interpolate std Signal to common wavebands - taken from L2 ES group: ProcessL2.py L1352
        for stype in types:
            try:
                output[stype]['std_Signal_Interpolated'] = self.interp_common_wvls(
                    output[stype]['std_Signal'],
                    np.asarray(list(output[stype]['std_Signal'].keys()), dtype=float),
                    newWaveBands,
                    return_as_dict=True)
                    # this interpolation is giving an array back of a slightly different size in the new wave bands
            except IndexError as err:
                msg = "Unable to parse statistics for the ensemble, possibly too few scans."
                print(msg)
                Utilities.writeLogFile(msg)
                return False
        #print("generateSensorStats: output(stats)")
        #print(output)
        return output

    def read_uncertainties(self, node, uncGrp, cCal, cCoef, cStab, cLin, cStray, cT, cPol, cCos) -> Optional[np.array]:
        """
        reads the uncertainties from the HDF file, must return indicated raw bands, i.e. which bands we have uncertainty 
        values saved in the cal/char files.
        
        :param node: HDFRoot of input HDF is required to retrieve calibration file start and stop for slicing straylight
        :param uncGrp: HDFGroup Uncertainties from HDF is required to retrieve uncertainties
        :param cCal: dict to contain calibration
        :param cCoef: dict to contain calibration coefficient uncertainty
        :param cStab: dict to contain stability information
        :param cLin: dict to contain non-linearity information
        :param cStray: dict to contain straylight information
        :param cT: dict to contain temperature correction information
        :param cPol: dict to contain polarisation information
        :param cCos: dict to contain cosine response information
        """

        for s in ["ES", "LI", "LT"]:  # s for sensor type
            cal_start = None
            cal_stop = None
            if ConfigFile.settings["fL1bCal"] == 1 and ConfigFile.settings['SensorType'].lower() == "seabird":
                radcal = self.extract_unc_from_grp(uncGrp, f"{s}_RADCAL_UNC")
                ind_rad_wvl = (np.array(radcal.columns['wvl']) > 0)  # all radcal wvls should be available from sirrex
                # read cal start and cal stop for shaping stray-light class based uncertainties
                cal_start = int(node.attributes['CAL_START'])
                cal_stop = int(node.attributes['CAL_STOP'])

                self.extract_factory_cal(node, radcal, s, cCal, cCoef)  # populates dicts with calibration

                        
            #elif ConfigFile.settings["fL1bCal"] == 1 and ConfigFile.settings['SensorType'].lower() == "dalec":
            #    radcal = self.extract_unc_from_grp(uncGrp, f"{s}_RADCAL_UNC")
            #    ind_rad_wvl = (np.array(radcal.columns['wvl']) > 0)  # all radcal wvls should be available from sirrex
            #    self.extract_factory_cal(node, radcal, s, cCal, cCoef)  # populates dicts with calibration
            
            elif ConfigFile.settings["fL1bCal"] == 2:  # class-Based
                radcal = self.extract_unc_from_grp(uncGrp, f"{s}_RADCAL_CAL")
                ind_rad_wvl = (np.array(radcal.columns['1']) > 0)  # where radcal wvls are available

                # ensure correct units are used for uncertainty calculation
                if ConfigFile.settings['SensorType'].lower() == "trios" or ConfigFile.settings['SensorType'].lower() == "sorad":
                    # Convert TriOS mW/m2/nm to uW/cm^2/nm
                    cCoef[s] = np.asarray(list(radcal.columns['2']))[ind_rad_wvl] / 10
                elif ConfigFile.settings['SensorType'].lower() == "seabird":
                    cCoef[s] = np.asarray(list(radcal.columns['2']))[ind_rad_wvl]
                cCal[s] = np.asarray(list(radcal.columns['3']))[ind_rad_wvl]

            else:
                msg = "TriOS/Dalec factory uncertainties not implemented"
                Utilities.writeLogFile(msg)
                print(msg)
                return False,False

            cStab[s] = self.extract_unc_from_grp(uncGrp, f"{s}_STABDATA_CAL", '1')

            cStray[s] = self.extract_unc_from_grp(uncGrp, f"{s}_STRAYDATA_CAL", '1')
            if (ind_rad_wvl is not None) and (len(ind_rad_wvl) == len(cStray[s])):
                cStray[s] = cStray[s][ind_rad_wvl]
            elif (cal_start is not None) and (cal_stop is not None):
                cStray[s] = cStray[s][cal_start:cal_stop + 1]
            else:
                # to cover for potential coding errors, should not be hit in normal use
                msg = "cannot mask straylight"
                print(msg)
                return False,False

            cLin[s] = self.extract_unc_from_grp(grp=uncGrp, name=f"{s}_NLDATA_CAL", col_name='1')

            # temp uncertainties calculated at L1AQC
            cT[s] = self.extract_unc_from_grp(grp=uncGrp,
                                              name=f"{s}_TEMPDATA_CAL",
                                              col_name=f'{s}_TEMPERATURE_UNCERTAINTIES')

            # temporary fix angular for ES is written as ES_POL
            if "ES" in s:
                cCos[s] = self.extract_unc_from_grp(grp=uncGrp, name=f"{s}_POLDATA_CAL", col_name='1')
            else:
                cPol[s] = self.extract_unc_from_grp(grp=uncGrp, name=f"{s}_POLDATA_CAL", col_name='1')

            nan_mask = np.where((cStab[s] <= 0) | (cStray[s] <= 0) | (cLin[s] <= 0) | (cT[s] <= 0) |
                                (self.extract_unc_from_grp(grp=uncGrp, name=f"{s}_POLDATA_CAL", col_name='1') <= 0))

        return ind_rad_wvl, nan_mask

    def ClassBased(self, node: HDFRoot, uncGrp: HDFGroup, stats: dict[str, np.array]) -> Union[dict[str, dict], bool]:
        """
        Propagates class based uncertainties for all instruments. If no calibration uncertainties are available will use Sirrex-7 
        to propagate uncertainties in the SeaBird Case. See D-10 secion 5.3.1.

        :param node: HDFRoot containing all L1BQC data
        :param uncGrp: HDFGroup containing raw uncertainties
        :param stats: output of PIU.py BaseInstrument.generateSensorStats

        :return: dictionary of instrument uncertainties [Es uncertainty, Li uncertainty, Lt uncertainty]
        alternatively errors in processing will return False for context management purposes.
        """

        # create object for running uncertainty propagation, M means number of monte carlo draws
        Prop_Instrument_CB = Propagate(M=100, cores=0)  # Propagate_Instrument_Uncertainty_ClassBased

        # initialise dicts for error sources
        cCal = {}
        cCoef = {}
        cStab = {}
        cLin = {}
        cStray = {}
        cT = {}
        cPol = {}
        cCos = {}

        ind_rad_wvl, nan_mask = self.read_uncertainties(
            node,
            uncGrp,
            cCal=cCal,
            cCoef=cCoef,
            cStab=cStab,
            cLin=cLin,
            cStray=cStray,
            cT=cT,
            cPol=cPol,
            cCos=cCos
        )
        if isinstance(ind_rad_wvl, bool):
            return False

        ones = np.ones_like(cCal['ES'])  # array of ones with correct shape.

        means = [stats['ES']['ave_Light'], stats['ES']['ave_Dark'],
                 stats['LI']['ave_Light'], stats['LI']['ave_Dark'],
                 stats['LT']['ave_Light'], stats['LT']['ave_Dark'],
                 cCoef['ES'], cCoef['LI'], cCoef['LT'],
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones
                 ]

        uncertainties = [stats['ES']['std_Light'], stats['ES']['std_Dark'],
                         stats['LI']['std_Light'], stats['LI']['std_Dark'],
                         stats['LT']['std_Light'], stats['LT']['std_Dark'],
                         cCal['ES'] * cCoef['ES'] / 200,
                         cCal['LI'] * cCoef['LI'] / 200,
                         cCal['LT'] * cCoef['LT'] / 200,
                         cStab['ES'], cStab['LI'], cStab['LT'],
                         cLin['ES'], cLin['LI'], cLin['LT'],
                         np.array(cStray['ES']) / 100,
                         np.array(cStray['LI']) / 100,
                         np.array(cStray['LT']) / 100,
                         np.array(cT['ES']), np.array(cT['LI']), np.array(cT['LT']),
                         np.array(cPol['LI']), np.array(cPol['LT']), np.array(cCos['ES'])
                         ]

        # generate uncertainties using Monte Carlo Propagation object
        es_unc, li_unc, lt_unc = Prop_Instrument_CB.propagate_Instrument_Uncertainty(means, uncertainties)

        # NOTE: Debugging check
        is_negative = np.any([ x < 0 for x in means])
        if is_negative:
            print('WARNING: Negative uncertainty potential')
        is_negative = np.any([ x < 0 for x in uncertainties])
        if is_negative:
            print('WARNING: Negative uncertainty potential')
        if any(es_unc < 0) or any(li_unc < 0) or any(lt_unc < 0):
            print('WARNING: Negative uncertainty potential')

        es, li, lt = Prop_Instrument_CB.instruments(*means)

        # plot class based L1B uncertainties
        rad_cal_str = "ES_RADCAL_CAL" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "ES_RADCAL_UNC"
        cal_col_str = "1" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"
        if ConfigFile.settings['bL2UncertaintyBreakdownPlot']:
            #       NOTE: For continuous, autonomous acquisition (e.g. SolarTracker, pySAS, SoRad, DALEC), stations are
            #       only associated with specific spectra during times that intersect with station designation in the
            #       Ancillary file. If station extraction is performed in L2, then the resulting HDF will have only one
            #       unique station designation, though that may include multiple ensembles, depending on how long the ship
            #       was on station. - DA
            acqTime = datetime.strptime(node.attributes['TIME-STAMP'], '%a %b %d %H:%M:%S %Y')
            cast = f"{type(self).__name__}_{acqTime.strftime('%Y%m%d%H%M%S')}"

            # the breakdown plots must calculate uncertainties separately from the main processor, will incur additional
            # computational overheads
            p_unc = UncertaintyGUI(Prop_Instrument_CB)
            p_unc.pie_plot_class(
                means,
                uncertainties,
                dict(
                    ES=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str]),
                    LI=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str]),
                    LT=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str])
                ),
                cast,
                node.getGroup("ANCILLARY")
            )
            p_unc.plot_class(
                means,
                uncertainties,
                dict(
                    ES=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str]),
                    LI=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str]),
                    LT=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str])
                ),
                cast
            )

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="invalid value encountered in divide")
            # convert to relative in order to avoid a complex unit conversion process in ProcessL2.

            ES_unc = es_unc / np.abs(es)
            LI_unc = li_unc / np.abs(li)
            LT_unc = lt_unc / np.abs(lt)


        # interpolation step - bringing uncertainties to common wavebands from radiometric calibration wavebands.
        data_wvl = np.asarray(list(stats['ES']['std_Signal_Interpolated'].keys()),
                              dtype=float)
    
        es_Unc = self.interp_common_wvls(ES_unc,
                                         np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                                     dtype=float)[ind_rad_wvl],
                                         data_wvl,
                                         return_as_dict=True
                                         )
        li_Unc = self.interp_common_wvls(LI_unc,
                                         np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                                  dtype=float)[ind_rad_wvl],
                                         data_wvl,
                                         return_as_dict=True
                                         )
        lt_Unc = self.interp_common_wvls(LT_unc,
                                         np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                                  dtype=float)[ind_rad_wvl],
                                         data_wvl,
                                         return_as_dict=True
                                         )
        
        # return uncertainties to ProcessL2 as dictionary - will update xUnc dict with new uncs propagated to L1B
        return dict(
            esUnc=es_Unc,
            liUnc=li_Unc,
            ltUnc=lt_Unc,
            valid_pixels=nan_mask,
        )

    @abstractmethod
    def FRM(self, node: HDFRoot, uncGrp: HDFGroup, raw_grps: dict[str, HDFGroup], raw_slices: dict[str, np.array],
            stats: dict, newWaveBands: np.array) -> dict[str, np.array]:
        """
        Propagates instrument uncertainties with corrections (except polarisation) if full characterisation available - see D-10 section 5.3.1
        
        :param node: HDFRoot of L1BQC data for processing
        :param uncGrp: HDFGroup of uncertainty budget
        :param raw_grps: dictionary of raw data groups
        :param raw_slices: dictionary of sliced data for specific sensors
        :param stats: standard deviation and averages for Light, Dark and Light-Dark signal
        :param newWaveBands: wavelength subset for interpolation

        :return: output FRM uncertainties
        """
        pass

    ## L2 uncertainty Processing
    def FRM_L2(self, rhoScalar: float, rhoVec: np.array, rhoDelta: np.array, waveSubset: np.array,
               xSlice: dict[str, np.array]) -> dict[str, np.array]:
        """
        Propagates Lw and Rrs uncertainties if full characterisation available - see D-10 5.3.1

        :param rhoScalar: rho input if Mobley99 or threeC rho is used
        :param rhoVec: rho input if Zhang17 rho is used
        :param rhoDelta: uncertainties associated with rho
        :param waveSubset: wavelength subset for any band convolution (and sizing rhoScalar if used)
        :param xSlice: Dictionary of input radiance, raw_counts, standard deviations etc.

        :return: dictionary of output uncertainties that are generated

        """
        # organise data
        # cut data down to wavelengths where rho values exist -- should be no change for M99
        esSampleXSlice = np.asarray([{key: sample for key, sample in
                                      xSlice['esSample'][i].items() if float(key) in waveSubset}
                                     for i in range(len(xSlice['esSample']))])
        liSampleXSlice = np.asarray([{key: sample for key, sample in
                                      xSlice['liSample'][i].items() if float(key) in waveSubset}
                                     for i in range(len(xSlice['liSample']))])
        ltSampleXSlice = np.asarray([{key: sample for key, sample in
                                      xSlice['ltSample'][i].items() if float(key) in waveSubset}
                                     for i in range(len(xSlice['ltSample']))])

        # Get rho from scalar or vector
        if rhoScalar is not None:  # make rho a constant array if scalar
            rho = np.ones(len(waveSubset))*rhoScalar  # convert rhoScalar to the same dims as other values/Uncertainties
        else:
            rho = np.asarray(list(rhoVec.values()), dtype=float)

        # Get rhoDelta from scalar or vector
        if not hasattr(rhoDelta, '__len__'):  # Not an array (e.g. list or np.array)
            rhoDelta = np.ones(len(waveSubset)) * rhoDelta  # convert rhoDelta to the same dims as other values/Uncertainties

        # initialise punpy propagation object
        mdraws = esSampleXSlice.shape[0]  # keep no. of monte carlo draws consistent
        Propagate_L2_FRM = Propagate(mdraws, cores=1)  # punpy.MCPropagation(mdraws, parallel_cores=1)

        # get sample for rho
        rhoSample = cm.generate_sample(mdraws, rho, rhoDelta, "syst")

        # initialise lists to store uncertainties per replicate

        esSample = np.asarray([[i[0] for i in k.values()] for k in esSampleXSlice])  # recover original shape of samples
        liSample = np.asarray([[i[0] for i in k.values()] for k in liSampleXSlice])
        ltSample = np.asarray([[i[0] for i in k.values()] for k in ltSampleXSlice])

        # no uncertainty in wavelengths
        sample_wavelengths = cm.generate_sample(mdraws, np.array(waveSubset), None, None)
        # Propagate_L2_FRM is a Propagate object defined in Uncertainty_Analysis, this stores a punpy MonteCarlo
        # Propagation object (punpy.MCP) as a class member variable Propagate.MCP. We can therefore use this to get to
        # the punpy.MCP namespace to access punpy specific methods such as 'run_samples'. This has a memory saving over
        # making a separate object for running these methods.
        sample_Lw = Propagate_L2_FRM.MCP.run_samples(Propagate.Lw_FRM, [ltSample, rhoSample, liSample])
        sample_Rrs = Propagate_L2_FRM.MCP.run_samples(Propagate.Rrs_FRM, [ltSample, rhoSample, liSample, esSample])

        output = {}

        for s_key in self._SATELLITES.keys():
            output.update(
                self.get_band_outputs_FRM(
                s_key, Propagate_L2_FRM, esSample, liSample, ltSample, rhoSample, sample_wavelengths
                )
            )

        lwDelta = Propagate_L2_FRM.MCP.process_samples(None, sample_Lw)
        rrsDelta = Propagate_L2_FRM.MCP.process_samples(None, sample_Rrs)

        output["rhoUNC_HYPER"] = {str(wvl): val for wvl, val in zip(waveSubset, rhoDelta)}
        output["lwUNC"] = lwDelta  # Multiply by large number to reduce round off error
        output["rrsUNC"] = rrsDelta

        return output

    def ClassBasedL2(self, node, uncGrp, rhoScalar, rhoVec, rhoDelta, waveSubset, xSlice) -> dict:
        """
        Propagates class based uncertainties for all Lw and Rrs. See D-10 secion 5.3.1.

        :param node: HDFRoot which stores L1BQC data
        :param uncGrp: HDFGroup storing the uncertainty budget
        :param rhoScalar: rho input if Mobley99 or threeC rho is used
        :param rhoVec: rho input if Zhang17 rho is used
        :param rhoDelta: uncertainties associated with rho
        :param waveSubset: wavelength subset for any band convolution (and sizing rhoScalar if used)
        :param xSlice: Dictionary of input radiance, raw_counts, standard deviations etc.

        :return: dictionary of output uncertainties that are generated
        """

        Prop_L2_CB = Propagate(M=100, cores=0)
        waveSubset = np.array(waveSubset, dtype=float)  # convert waveSubset to numpy array
        esXstd = xSlice['esSTD_RAW']  # stdevs taken at instrument wavebands (not common wavebands)
        liXstd = xSlice['liSTD_RAW']
        ltXstd = xSlice['ltSTD_RAW']

        if rhoScalar is not None:  # make rho a constant array if scalar
            rho = np.ones(len(list(esXstd.keys()))) * rhoScalar
            rhoUNC = self.interp_common_wvls(np.array(rhoDelta, dtype=float),
                                             waveSubset,
                                             np.asarray(list(esXstd.keys()), dtype=float),
                                             return_as_dict=False)
        else:  # zhang rho needs to be interpolated to radcal wavebands (len must be 255)
            rho = self.interp_common_wvls(np.array(list(rhoVec.values()), dtype=float),
                                          waveSubset,
                                          np.asarray(list(esXstd.keys()), dtype=float),
                                          return_as_dict=False)
            rhoUNC = self.interp_common_wvls(rhoDelta,
                                             waveSubset,
                                             np.asarray(list(esXstd.keys()), dtype=float),
                                             return_as_dict=False)

        # initialise dicts for error sources
        cCal = {}
        cCoef = {}
        cStab = {}
        cLin = {}
        cStray = {}
        cT = {}
        cPol = {}
        cCos = {}

        ind_rad_wvl, nan_mask = self.read_uncertainties(
            node,
            uncGrp,
            cCal=cCal,
            cCoef=cCoef,
            cStab=cStab,
            cLin=cLin,
            cStray=cStray,
            cT=cT,
            cPol=cPol,
            cCos=cCos
        )

        # interpolate to radcal wavebands - check string for radcal group based on factory or class-based processing
        rad_cal_str = "ES_RADCAL_CAL" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "ES_RADCAL_UNC"
        cal_col_str = "1" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"
        es = self.interp_common_wvls(np.asarray(list(xSlice['es'].values()), dtype=float).flatten(),
                                     np.asarray(list(xSlice['es'].keys()), dtype=float).flatten(),
                                     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                              dtype=float)[ind_rad_wvl],
                                     return_as_dict=False)
        li = self.interp_common_wvls(np.asarray(list(xSlice['li'].values()), dtype=float).flatten(),
                                     np.asarray(list(xSlice['li'].keys()), dtype=float).flatten(),
                                     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                              dtype=float)[ind_rad_wvl],
                                     return_as_dict=False)
        lt = self.interp_common_wvls(np.asarray(list(xSlice['lt'].values()), dtype=float).flatten(),
                                     np.asarray(list(xSlice['lt'].keys()), dtype=float).flatten(),
                                     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                              dtype=float)[ind_rad_wvl],
                                     return_as_dict=False)

        ones = np.ones_like(es)

        lw_means = [lt, rho, li,
                    ones, ones,
                    ones, ones,
                    ones, ones,
                    ones, ones,
                    ones, ones,
                    ones, ones]

        lw_uncertainties = [np.abs(np.array(list(ltXstd.values())).flatten() * lt),
                            rhoUNC,
                            np.abs(np.array(list(liXstd.values())).flatten() * li),
                            cCal['LI'] / 200, cCal['LT'] / 200,
                            cStab['LI'], cStab['LT'],
                            cLin['LI'], cLin['LT'],
                            cStray['LI'] / 100, cStray['LI'] / 100,
                            cT['LI'], cT['LI'],
                            cPol['LI'], cPol['LI']]

        lwAbsUnc = Prop_L2_CB.Propagate_Lw_HYPER(lw_means, lw_uncertainties)

        rrs_means = [lt, rho, li, es,
                     ones, ones, ones,
                     ones, ones, ones,
                     ones, ones, ones,
                     ones, ones, ones,
                     ones, ones, ones,
                     ones, ones, ones
                     ]

        rrs_uncertainties = [np.abs(np.array(list(ltXstd.values())).flatten() * lt),
                             rhoUNC,
                             np.abs(np.array(list(liXstd.values())).flatten() * li),
                             np.abs(np.array(list(esXstd.values())).flatten() * es),
                             cCal['ES'] / 200, cCal['LI'] / 200, cCal['LT'] / 200,
                             cStab['ES'], cStab['LI'], cStab['LT'],
                             cLin['ES'], cLin['LI'], cLin['LT'],
                             cStray['ES'] / 100, cStray['LI'] / 100, cStray['LT'] / 100,
                             cT['ES'], cT['LI'], cT['LT'],
                             cPol['LI'], cPol['LT'], cCos['ES']
                             ]

        rrsAbsUnc = Prop_L2_CB.Propagate_RRS_HYPER(rrs_means, rrs_uncertainties)
        #print("rrsAbsUnc")
        #print(rrsAbsUnc)

        # Plot Class based L2 uncertainties
        if ConfigFile.settings['bL2UncertaintyBreakdownPlot']:
            acqTime = datetime.strptime(node.attributes['TIME-STAMP'], '%a %b %d %H:%M:%S %Y')
            cast = f"{type(self).__name__}_{acqTime.strftime('%Y%m%d%H%M%S')}"

            p_unc = UncertaintyGUI()
            try:
                p_unc.pie_plot_class_l2(
                    rrs_means,
                    lw_means,
                    rrs_uncertainties,
                    lw_uncertainties,
                    np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float),  # pass radcal wavelengths
                    cast,
                    node.getGroup("ANCILLARY")
                )
                p_unc.plot_class_L2(
                    rrs_means,
                    lw_means,
                    rrs_uncertainties,
                    lw_uncertainties,
                    np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float),
                    cast
                )
            except ValueError as err:
                msg = f"unable to run uncertainty breakdown plots for {cast}, with error: {err}"
                print(msg)
                Utilities.writeLogFile(msg)

        # these are absolute values!
        output = {}
        rhoUNC_CWB = self.interp_common_wvls(
            rhoUNC,
            np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[ind_rad_wvl],
            waveSubset,
            return_as_dict=False
        )
        lwAbsUnc[nan_mask] = np.nan
        lwAbsUnc = self.interp_common_wvls(
            lwAbsUnc,
            np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[ind_rad_wvl],
            waveSubset,
            return_as_dict=False
        )
        rrsAbsUnc[nan_mask] = np.nan
        rrsAbsUnc = self.interp_common_wvls(
            rrsAbsUnc,
            np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[ind_rad_wvl],
            waveSubset,
            return_as_dict=False
        )
        #print("rrsAbsUnc")
        #print(rrsAbsUnc)

        ## Band Convolution of Uncertainties
        # get unc values at common wavebands (from ProcessL2) and convert any NaNs to 0 to not create issues with punpy
        esUNC_band = np.array([i[0] for i in xSlice['esUnc'].values()])
        liUNC_band = np.array([i[0] for i in xSlice['liUnc'].values()])
        ltUNC_band = np.array([i[0] for i in xSlice['ltUnc'].values()])

        # Prune the uncertainties to remove NaNs and negative values (uncertainties which make no physical sense)
        esUNC_band[np.isnan(esUNC_band)] = 0.0
        liUNC_band[np.isnan(liUNC_band)] = 0.0
        ltUNC_band[np.isnan(ltUNC_band)] = 0.0
        esUNC_band = np.abs(esUNC_band)  # uncertainties may have negative values after conversion to relative units
        liUNC_band = np.abs(liUNC_band)
        ltUNC_band = np.abs(ltUNC_band)

        ## Update the output dictionary with band L2 hyperspectral and satellite band uncertainties
        for s_key in self._SATELLITES.keys():
            output.update(
                self.get_band_outputs(
                    s_key, rho, lw_means, lw_uncertainties, rrs_means, rrs_uncertainties,
                    esUNC_band, liUNC_band, ltUNC_band, rhoUNC, waveSubset, xSlice
                )
            )
        output.update(
            {"rhoUNC_HYPER": {str(k): val for k, val in zip(waveSubset, rhoUNC_CWB)},
            "lwUNC": lwAbsUnc,
             "rrsUNC": rrsAbsUnc}
        )

        return output

    ## Utilities ##

    @staticmethod
    def extract_unc_from_grp(grp: HDFGroup, name: str, col_name: Optional[str] = None) -> Union[np.array, HDFDataset]:
        """
        small function to avoid repetition of code

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

    @staticmethod
    def extract_factory_cal(node, radcal, s, cCal, cCoef):
        """
        small function to get the calibration and calibration uncertainty, mutates cCal and cCoef in lieu of return value
        :param node: HDF root - full HDF file
        :param radcal: HDF group containing radiometric calibration
        :param s: dict key to append data to cCal and cCoef
        :param cCal: dict for storing calibration
        :param cCoef: dict for storing calibration coeficients 
        """
         
        # ADERU : Read radiometric coeff value from configuration files
        cCal[s] = np.asarray(list(radcal.columns['unc']))
        calFolder = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
        calPath = os.path.join(PATH_TO_CONFIG, calFolder)
        calibrationMap = CalibrationFileReader.read(calPath)

        if ConfigFile.settings['SensorType'].lower() == "dalec":
            waves, cCoef[s] = ProcessL1b_FactoryCal.extract_calibration_coeff_dalec(calibrationMap, s)
        else:    
            waves, cCoef[s] = ProcessL1b_FactoryCal.extract_calibration_coeff(node, calibrationMap, s)

    def get_band_outputs(self, sensor_key: str, rho, lw_means, lw_uncertainties, rrs_means, rrs_uncertainties,
                         esUNC, liUNC, ltUNC, rhoUNC, waveSubset, xSlice) -> dict:

        """
        runs band convolution for class-based regime

        :param sensor_key: sensor key for self._SATELLITES depending on target for band conv
        :param rho: rho values provided by M99 or Z17 (depending on user settings)
        :param lw_means: class based regime mean values for Lw inputs
        :param lw_uncertainties: class based regime uncertainty values for Lw inputs
        :param rrs_means: class based regime mean values for Rrs inputs
        :param rrs_uncertainties: class based regime uncertainty values for Rrs inputs
        :param esUNC: Es uncertainty values
        :param liUNC: Li uncertainty values
        :param ltUNC: Lt uncertainty values
        :param rhoUNC: rho uncertainty values
        :param waveSubset: subset of wavelengths for L2 products to be interpolated to
        :param xSlice: dictionary for storing outputs
        """

        if ConfigFile.settings[self._SATELLITES[sensor_key]['config']]:
            sensor_name = self._SATELLITES[sensor_key]['name']
            RSR_Bands = self._SATELLITES[sensor_key]['Weight_RSR']
            prop_Band_CB = Propagate(M=100, cores=1)  # propagate band convolved uncertainties class based
            Band_Convolved_UNC = {}
            esDeltaBand = prop_Band_CB.band_Conv_Uncertainty(
                [np.asarray(list(xSlice['es'].values()), dtype=float).flatten(), waveSubset],
                [esUNC, None],
                sensor_key  # used to choose correct band convolution measurement function in uncertainty_analysis.py
            )
            # band_Conv_Uncertainty uses def_sensor_mfunc(sensor_key) to select the correct measurement function
            # per satellite. sensor_key refers to the keys of the _SATELLITE dict which were chosen to match the keys
            # in def_sensor_mfunc.

            Band_Convolved_UNC[f"esUNC_{sensor_name}"] = {
                str(k): [val] for k, val in zip(RSR_Bands, esDeltaBand)
            }

            liDeltaBand = prop_Band_CB.band_Conv_Uncertainty(
                [np.asarray(list(xSlice['li'].values()), dtype=float).flatten(), waveSubset],
                [liUNC, None],
                sensor_key
            )
            Band_Convolved_UNC[f"liUNC_{sensor_name}"] = {
                str(k): [val] for k, val in zip(RSR_Bands, liDeltaBand)
            }

            ltDeltaBand = prop_Band_CB.band_Conv_Uncertainty(
                [np.asarray(list(xSlice['lt'].values()), dtype=float).flatten(), waveSubset],
                [ltUNC, None],
                sensor_key
            )
            Band_Convolved_UNC[f"ltUNC_{sensor_name}"] = {
                str(k): [val] for k, val in zip(RSR_Bands, ltDeltaBand)
            }

            rhoDeltaBand = prop_Band_CB.band_Conv_Uncertainty(
                [rho, waveSubset],
                [rhoUNC, None],
                sensor_key
            )
            Band_Convolved_UNC[f"rhoUNC_{sensor_name}"] = {
                str(k): [val] for k, val in zip(RSR_Bands, rhoDeltaBand)
            }

            Band_Convolved_UNC[f"lwUNC_{sensor_name}"] = prop_Band_CB.Propagate_Lw_Convolved(
                lw_means,
                lw_uncertainties,
                sensor_key,
                waveSubset
            )
            Band_Convolved_UNC[f"rrsUNC_{sensor_name}"] = prop_Band_CB.Propagate_RRS_Convolved(
                rrs_means,
                rrs_uncertainties,
                sensor_key,
                waveSubset
            )

            return Band_Convolved_UNC
        else:
            return {}

    def get_band_outputs_FRM(self, sensor_key, MCP_obj, esSample, liSample, ltSample, rhoSample, sample_wavelengths
                             ) -> dict:
        """
        runs band convolution for FRM regime
        
        :param sensor_key: sensor key for self._SATELLITES depending on target for band conv
        :param MCP_obj: Monte Carlo propagation object for accessing measurment functions and punpy/comet_maths methods
        :param esSample: Monte Carlo sample (wavelengths x Mdraws) generated for Es 
        :param liSample: Monte Carlo sample (wavelengths x Mdraws) generated for Li 
        :param ltSample: Monte Carlo sample (wavelengths x Mdraws) generated for Lt 
        :param rhoSample: Monte Carlo sample (wavelengths x Mdraws) generated for rho
         """
        
        # now requires MCP_obj to be a Propagate object as def_sensor_mfunc is not a static method
        if ConfigFile.settings[self._SATELLITES[sensor_key]['config']]:
            sensor_name = self._SATELLITES[sensor_key]['name']
            RSR_Bands = self._SATELLITES[sensor_key]['Weight_RSR']
            Band_Convolved_UNC = {}

            sample_es_conv = MCP_obj.MCP.run_samples(MCP_obj.def_sensor_mfunc(sensor_key), [esSample, sample_wavelengths])
            sample_li_conv = MCP_obj.MCP.run_samples(MCP_obj.def_sensor_mfunc(sensor_key), [liSample, sample_wavelengths])
            sample_lt_conv = MCP_obj.MCP.run_samples(MCP_obj.def_sensor_mfunc(sensor_key), [ltSample, sample_wavelengths])

            sample_rho_conv = MCP_obj.MCP.run_samples(MCP_obj.def_sensor_mfunc(sensor_key), [rhoSample, sample_wavelengths])

            esDeltaBand = MCP_obj.MCP.process_samples(None, sample_es_conv)
            liDeltaBand = MCP_obj.MCP.process_samples(None, sample_li_conv)
            ltDeltaBand = MCP_obj.MCP.process_samples(None, sample_lt_conv)

            rhoDeltaBand = MCP_obj.MCP.process_samples(None, sample_rho_conv)

            sample_lw_conv = MCP_obj.MCP.run_samples(MCP_obj.Lw_FRM, [sample_lt_conv, sample_rho_conv, sample_li_conv])
            sample_rrs_conv = MCP_obj.MCP.run_samples(MCP_obj.Rrs_FRM, [sample_lt_conv, sample_rho_conv, sample_li_conv, sample_es_conv])

            # put in expected format (converted from punpy conpatible outputs) and put in output dictionary which will
            # be returned to ProcessingL2 and used to update xSlice/xUNC
            Band_Convolved_UNC[f"esUNC_{sensor_name}"] = {str(k): [val] for k, val in zip(RSR_Bands, esDeltaBand)}
            Band_Convolved_UNC[f"liUNC_{sensor_name}"] = {str(k): [val] for k, val in zip(RSR_Bands, liDeltaBand)}
            Band_Convolved_UNC[f"ltUNC_{sensor_name}"] = {str(k): [val] for k, val in zip(RSR_Bands, ltDeltaBand)}
            Band_Convolved_UNC[f"rhoUNC_{sensor_name}"] = {str(k): [val] for k, val in zip(RSR_Bands, rhoDeltaBand)}
            # L2 uncertainty products can be reported as np arrays
            Band_Convolved_UNC[f"lwUNC_{sensor_name}"] = MCP_obj.MCP.process_samples(None, sample_lw_conv)
            Band_Convolved_UNC[f"rrsUNC_{sensor_name}"] = MCP_obj.MCP.process_samples(None, sample_rrs_conv)

            return Band_Convolved_UNC
        else:
            return {}

    @staticmethod
    def apply_NaN_Mask(rawSlice):
        for wvl in rawSlice:  # iterate over wavelengths
            if any(np.isnan(rawSlice[wvl])):  # if we encounter any NaN's
                for msk in np.where(np.isnan(rawSlice[wvl]))[0]:  # mask may be multiple indexes
                    for wl in rawSlice:  # strip the scan
                        rawSlice[wl].pop(msk)  # remove the scan if nans are found anywhere

    @staticmethod
    def interp_common_wvls(columns, waves, newWaveBands, return_as_dict: bool =False) -> Union[np.array, OrderedDict]:
        """
        interpolate array to common wavebands

        :param columns: values to be interpolated (y)
        :param waves: current wavelengths (x)
        :param newWaveBands: wavelenghts to interpolate (new_x)
        :param return_as_dict: boolean which if true will return an ordered dictionary (wavelengths are keys)

        :return: returns the interpolated output as either a numpy array or Ordered-Dictionary
        """
        saveTimetag2 = None
        if isinstance(columns, dict):
            if "Datetag" in columns:
                saveDatetag = columns.pop("Datetag")
                saveTimetag2 = columns.pop("Timetag2")
                columns.pop("Datetime")
            y = np.asarray(list(columns.values()))
        elif isinstance(columns, np.ndarray):  # is numpy array
            y = columns
        else:
            msg = "columns are unexpected type: ProcessInstrumentUncertainties.py - interp_common_wvls"
            print(msg)
        # Get wavelength values
        x = np.asarray(waves)

        newColumns = OrderedDict()
        if saveTimetag2 is not None:
            newColumns["Datetag"] = saveDatetag
            newColumns["Timetag2"] = saveTimetag2
        # Can leave Datetime off at this point

        for i in range(newWaveBands.shape[0]):
            newColumns[str(round(10*newWaveBands[i])/10)] = []  # limit to one decimal place

        new_y = np.interp(newWaveBands, x, y)  #InterpolatedUnivariateSpline(x, y, k=3)(newWavebands)

        for waveIndex in range(newWaveBands.shape[0]):
            newColumns[str(round(10*newWaveBands[waveIndex])/10)].append(new_y[waveIndex])

        if return_as_dict:
            return newColumns
        else:
            return new_y

    @staticmethod
    def interpolateSamples(Columns, waves, newWavebands):
        '''
        Wavelength Interpolation for differently sized arrays containing samples
        Use a common waveband set determined by the maximum lowest wavelength
        of all sensors, the minimum highest wavelength, and the interval
        set in the Configuration Window.
        '''

        # Copy dataset to dictionary
        columns = {k: Columns[:, i] for i, k in enumerate(waves)}
        cols = []
        for m in range(Columns.shape[0]):  # across all the monte carlo draws
            newColumns = {}

            for i in range(newWavebands.shape[0]):
                # limit to one decimal place
                newColumns[str(round(10*newWavebands[i])/10)] = []

            # for m in range(Columns.shape[0]):
            # Perform interpolation for each timestamp
            y = np.asarray([columns[k][m] for k in columns])

            new_y = sp.interpolate.InterpolatedUnivariateSpline(waves, y, k=3)(newWavebands)

            for waveIndex in range(newWavebands.shape[0]):
                newColumns[str(round(10*newWavebands[waveIndex])/10)].append(new_y[waveIndex])

            cols.append(newColumns)

        return np.asarray(cols)

    def gen_n_IB_sample(self, mDraws):
        # make your own sample here min is 3, max is 6 - all values must be integer
        import random as rand
        # seed random number generator with current systime (default behaviour of rand.seed)
        rand.seed(a=None, version=2)
        sample_n_IB = []
        for i in range(mDraws):
            sample_n_IB.append(rand.randrange(3, 7, 1))  # sample_n_IB max should be 6
        return np.asarray(sample_n_IB)  # make numpy array to be compatible with comet maths

    def get_Slaper_Sl_unc(self, data, sample_data, mZ, sample_mZ, n_iter, sample_n_iter, MC_prop, mDraws):
        """
        finds the uncertainty in the slaper correction. Error estimated from the difference between slaper correction
        using n_iter and n_iter - 1

        :param data: signal to be corrected (either S12 or signal)
        :param sample_data: MC sample [PDF] of data attribute
        :param mZ: LSF read from tartu files
        :param sample mZ: PDF of mZ
        :param n_iter: number of iterations
        :param sample_n_iter: simple PDF of n_iter, no uncertainty should be passed here.
        :param MC_prop: punpy.MCP object as namespace for calling punpy functions/settings
        :param mDraws: number of monte carlo draws, M
        """
        # calculates difference between n=4 and n=5, then propagates as an error
        sl_corr = self.Slaper_SL_correction(data, mZ, n_iter)
        sl_corr_unc = []
        sl4 = self.Slaper_SL_correction(data, mZ, n_iter=n_iter - 1)
        for i in range(len(sl_corr)):  # get the difference between n=4 and n=5
            if sl_corr[i] > sl4[i]:
                sl_corr_unc.append(sl_corr[i] - sl4[i])
            else:
                sl_corr_unc.append(sl4[i] - sl_corr[i])

        sample_sl_syst = cm.generate_sample(mDraws, sl_corr, np.array(sl_corr_unc), "syst")
        sample_sl_rand = MC_prop.run_samples(self.Slaper_SL_correction, [sample_data, sample_mZ, sample_n_iter])
        sample_sl_corr = MC_prop.combine_samples([sample_sl_syst, sample_sl_rand])

        return sample_sl_corr

    # Measurement Functions
    @staticmethod
    def S12func(k, S1, S2):
        "compares DN at two separate times, part of non linearity correction derrivation"
        return ((1 + k)*S1) - (k*S2)

    @staticmethod
    def alphafunc(S1, S12):
        t1 = [Decimal(S1[i]) - Decimal(S12[i]) for i in range(len(S1))]
        t2 = [pow(Decimal(S12[i]), 2) for i in range(len(S12))]
        # I added a conditional to check if any values in S12 are zero. One value of S12 was 0 which caused issue #253
        return np.asarray([float(t1[i]/t2[i]) if t2[i] != 0 else 0 for i in range(len(t1))])

    @staticmethod
    def dark_Substitution(light, dark):
        return light - dark

    @staticmethod
    def non_linearity_corr(offset_corrected_mesure, alpha):
        linear_corr_mesure = offset_corrected_mesure*(1 - alpha*offset_corrected_mesure)
        return linear_corr_mesure

    @staticmethod
    def Zong_SL_correction(input_data, C_matrix):
        return np.matmul(C_matrix, input_data)

    @staticmethod
    def Slaper_SL_correction(input_data, SL_matrix, n_iter=5):
        nband = len(input_data)
        m_norm = np.zeros(nband)

        mC = np.zeros((n_iter + 1, nband))
        mX = np.zeros((n_iter + 1, nband))
        mZ = SL_matrix
        mX[0, :] = input_data

        for i in range(nband):
            jstart = np.max([0, i - 10])
            jstop = np.min([nband, i + 10])
            m_norm[i] = np.sum(mZ[i, jstart:jstop])  # eq 4

        for i in range(nband):
            if m_norm[i] == 0:
                mZ[i, :] = np.zeros(nband)
            else:
                mZ[i, :] = mZ[i, :]/m_norm[i]  # eq 5

        for k in range(1, n_iter + 1):
            for i in range(nband):
                mC[k - 1, i] = mC[k - 1, i] + np.sum(mX[k - 1, :]*mZ[i, :])  # eq 6
                if mC[k - 1, i] == 0:
                    mX[k, i] = 0
                else:
                    mX[k, i] = (mX[k - 1, i]*mX[0, i])/mC[k - 1, i]  # eq 7

        return mX[n_iter - 1, :]

    @staticmethod
    def absolute_calibration(normalized_mesure, updated_radcal_gain):
        return normalized_mesure/updated_radcal_gain

    @staticmethod
    def thermal_corr(Ct, calibrated_mesure):
        return Ct*calibrated_mesure

    @staticmethod
    def prepare_cos(uncGrp, sensortype, level=None, ind_raw_wvl=None):
        """
        read from hdf and prepare inputs for cos_err measurement function
        """
        ## Angular cosine correction (for Irradiance)
        if level != 'L2':
            radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
            coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:, 2:]
            cos_unc = (np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:, 2:]
                       /100)*np.abs(coserror)

            coserror_90 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
            cos90_unc = (np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:,
                         2:]/100)*np.abs(coserror_90)
        else:
            # reading in data changes if at L2 (because hdf files have different layout)
            radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
            coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:, 2:]
            cos_unc = (np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:, 2:]/100)*np.abs(coserror)
            coserror_90 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
            cos90_unc = (np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:, 2:]/100)*np.abs(coserror_90)

        radcal_unc = None  # no uncertainty in the wavelengths as they are only used to index

        zenith_ang = uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
        zenith_ang = np.asarray([float(x) for x in zenith_ang])
        zen_unc = np.asarray([0.05 for x in zenith_ang])  # default of 0.5 for solar zenith unc

        if ind_raw_wvl is not None:
            radcal_wvl = radcal_wvl[ind_raw_wvl]
            coserror = coserror[ind_raw_wvl]
            coserror_90 = coserror_90[ind_raw_wvl]
            cos_unc = cos_unc[ind_raw_wvl]
            cos90_unc = cos90_unc[ind_raw_wvl]

        return [radcal_wvl, coserror, coserror_90, zenith_ang], [radcal_unc, cos_unc, cos90_unc, zen_unc]

    @staticmethod
    def AZAvg_Coserr(coserror, coserror_90):
        # if delta < 2% : averaging the 2 azimuth plan
        return (coserror + coserror_90)/2.  # average azi coserr

    @staticmethod
    def ZENAvg_Coserr(radcal_wvl, AZI_avg_coserror):
        i1 = np.argmin(np.abs(radcal_wvl - 300))
        i2 = np.argmin(np.abs(radcal_wvl - 1000))

        # if delta < 2% : averaging symetric zenith
        ZEN_avg_coserror = (AZI_avg_coserror + AZI_avg_coserror[:, ::-1])/2.

        # set coserror to 1 outside range [450,700]
        ZEN_avg_coserror[0:i1, :] = 0
        ZEN_avg_coserror[i2:, :] = 0
        return ZEN_avg_coserror

    @staticmethod
    def FHemi_Coserr(ZEN_avg_coserror, zenith_ang):
        # Compute full hemisperical coserror
        zen0 = np.argmin(np.abs(zenith_ang))
        zen90 = np.argmin(np.abs(zenith_ang - 90))
        deltaZen = (zenith_ang[1::] - zenith_ang[:-1])

        full_hemi_coserror = np.zeros(ZEN_avg_coserror.shape[0])

        for i in range(ZEN_avg_coserror.shape[0]):
            full_hemi_coserror[i] = np.sum(
                ZEN_avg_coserror[i, zen0:zen90]*np.sin(2*np.pi*zenith_ang[zen0:zen90]/180)*deltaZen[
                                                                                           zen0:zen90]*np.pi/180)

        return full_hemi_coserror

    @staticmethod
    def cosine_corr(avg_coserror, full_hemi_coserror, zenith_ang, thermal_corr_mesure, sol_zen, dir_rat):
        ind_closest_zen = np.argmin(np.abs(zenith_ang - sol_zen))
        cos_corr = 1 - avg_coserror[:, ind_closest_zen]/100
        Fhcorr = 1 - np.array(full_hemi_coserror)/100
        cos_corr_mesure = (dir_rat*thermal_corr_mesure*cos_corr) + ((1 - dir_rat)*thermal_corr_mesure*Fhcorr)

        return cos_corr_mesure

    @staticmethod
    def get_cos_corr(zenith_angle, solar_zenith, cosine_error):
        ind_closest_zen = np.argmin(np.abs(zenith_angle - solar_zenith))
        return 1 - cosine_error[:, ind_closest_zen]/100

    @staticmethod
    def cos_corr(signal, direct_ratio, cos_correction, full_hemi_cos_error):
        Fhcorr = (1 - full_hemi_cos_error / 100)
        return (direct_ratio * signal * cos_correction) + ((1 - direct_ratio) * signal * Fhcorr)

    @staticmethod
    def cos_corr_fun(avg_coserror, zenith_ang, sol_zen):
        ind_closest_zen = np.argmin(np.abs(zenith_ang - sol_zen))
        return 1 - avg_coserror[:, ind_closest_zen]/100

    @staticmethod
    def cosine_error_correction(uncGrp, sensortype):

        ## Angular cosine correction (for Irradiance)
        radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
        coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:,2:]
        coserror_90 = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
        coserror_unc = (np.asarray(
            pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:,2:]/100)*coserror
        coserror_90_unc = (np.asarray(
            pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:, 2:]/100)*coserror_90
        zenith_ang = uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
        i1 = np.argmin(np.abs(radcal_wvl - 300))
        i2 = np.argmin(np.abs(radcal_wvl - 1000))
        zenith_ang = np.asarray([float(x) for x in zenith_ang])

        # comparing cos_error for 2 azimuth
        AZI_delta_err = np.abs(coserror - coserror_90)

        # if delta < 2% : averaging the 2 azimuth plan
        AZI_avg_coserror = (coserror + coserror_90)/2.
        AZI_delta = np.power(np.power(coserror_unc, 2) + np.power(coserror_90_unc, 2), 0.5)  # TODO: check this!

        # comparing cos_error for symetric zenith
        ZEN_delta_err = np.abs(AZI_avg_coserror - AZI_avg_coserror[:, ::-1])
        ZEN_delta = np.power(np.power(AZI_delta, 2) + np.power(AZI_delta[:, ::-1], 2), 0.5)

        # if delta < 2% : averaging symetric zenith
        ZEN_avg_coserror = (AZI_avg_coserror + AZI_avg_coserror[:, ::-1])/2.

        # set coserror to 1 outside range [450,700]
        ZEN_avg_coserror[0:i1, :] = 0
        ZEN_avg_coserror[i2:, :] = 0

        return ZEN_avg_coserror, AZI_avg_coserror, zenith_ang, ZEN_delta_err, ZEN_delta, AZI_delta_err, AZI_delta


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


class HyperOCR(BaseInstrument):

    warnings.filterwarnings("ignore", message="One of the provided covariance matrix is not positivedefinite. It has been slightly changed")

    def __init__(self):
        super().__init__()  # call to instrument __init__
        self.instrument = "HyperOCR"

    @staticmethod
    def _check_data(dark, light):
        msg = None
        if (dark is None) or (light is None):
            msg = f'Dark Correction, dataset not found: {dark} , {light}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        if Utilities.hasNan(light):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'

        if Utilities.hasNan(dark):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'
        if msg:
            print(msg)
            Utilities.writeLogFile(msg)
        return True

    def darkToLightTimer(self, rawGrp, sensortype):
        darkGrp = rawGrp['DARK']
        lightGrp = rawGrp['LIGHT']

        if darkGrp.attributes["FrameType"] == "ShutterDark" and darkGrp.getDataset(sensortype):
            darkData = darkGrp.getDataset(sensortype)
            darkDateTime = darkGrp.getDataset("DATETIME")
        if lightGrp.attributes["FrameType"] == "ShutterLight" and lightGrp.getDataset(sensortype):
            lightData = lightGrp.getDataset(sensortype)
            lightDateTime = lightGrp.getDataset("DATETIME")

        if darkGrp is None or lightGrp is None:
            msg = f'No radiometry found for {sensortype}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        elif not self._check_data(darkData, lightData):
            return False

        newDarkData = self._interp(lightData, lightDateTime, darkData, darkDateTime)
        if isinstance(newDarkData, bool):
            return False
        else:
            rawGrp['DARK'].datasets[sensortype].data = newDarkData
            rawGrp['DARK'].datasets[sensortype].datasetToColumns()
            return True

    @staticmethod
    def _interp(lightData, lightTimer, darkData, darkTimer):
        # Interpolate Dark Dataset to match number of elements as Light Dataset
        newDarkData = np.copy(lightData.data)
        for k in darkData.data.dtype.fields.keys():  # darkData.data.dtype.fields.keys():  # For each wavelength
            x = np.copy(darkTimer.data).tolist()  # darktimer
            y = np.copy(darkData.data[k]).tolist()  # data at that band over time
            new_x = lightTimer.data  # lighttimer

            if len(x) < 3 or len(y) < 3 or len(new_x) < 3:
                msg = "**************Cannot do cubic spline interpolation, length of datasets < 3"
                print(msg)
                Utilities.writeLogFile(msg)
                return False
            if not Utilities.isIncreasing(x):
                msg = "**************darkTimer does not contain strictly increasing values"
                print(msg)
                Utilities.writeLogFile(msg)
                return False
            if not Utilities.isIncreasing(new_x):
                msg = "**************lightTimer does not contain strictly increasing values"
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            if len(x) >= 3:
                # Because x is now a list of datetime tuples, they'll need to be
                # converted to Unix timestamp values
                xTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in x]
                newXTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in new_x]

                newDarkData[k] = Utilities.interp(xTS,y,newXTS, fill_value=np.nan)

                for val in newDarkData[k]:
                    if np.isnan(val):
                        frameinfo = getframeinfo(currentframe())
                        msg = f'found NaN {frameinfo.lineno}'
            else:
                msg = '**************Record too small for splining. Exiting.'
                print(msg)
                Utilities.writeLogFile(msg)
                return False

        if Utilities.hasNan(darkData):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        return newDarkData

    def lightDarkStats(self, grp, slice, sensortype):
        # SeaBird HyperOCR
        lightGrp = grp[0]
        lightSlice = copy.deepcopy(slice[0])  # copy to prevent changing of Raw data
        darkGrp = grp[1]
        darkSlice = copy.deepcopy(slice[1])

        if darkGrp.attributes["FrameType"] == "ShutterDark" and darkGrp.getDataset(sensortype):
            darkData = darkSlice['data']  # darkGrp.getDataset(sensortype)
            # darkDateTime = darkSlice['datetime']  # darkGrp.getDataset("DATETIME")

        if lightGrp.attributes["FrameType"] == "ShutterLight" and lightGrp.getDataset(sensortype):
            lightData = lightSlice['data']  # lightGrp.getDataset(sensortype)
            # lightDateTime = lightSlice['datetime']  # lightGrp.getDataset("DATETIME")

        if darkGrp is None or lightGrp is None:
            msg = f'No radiometry found for {sensortype}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        elif not self._check_data(darkData, lightData):
            return False
        # Do interpolation at the start of the stations ensemble process, then slice like light data
        # newDarkData = self._interp(lightData, lightDateTime, darkData, darkDateTime)
        # if not newDarkData:
        #     return False

        # Correct light data by subtracting interpolated dark data from light data
        std_Light = []
        std_Dark = []
        ave_Light = []
        ave_Dark = []
        stdevSignal = {}

        # number of replicates for light and dark readings
        N = np.asarray(list(lightData.values())).shape[1]
        Nd = np.asarray(list(darkData.values())).shape[1]
        for i, k in enumerate(lightData.keys()):
            wvl = str(float(k))

            # apply normalisation to the standard deviations used in uncertainty calculations
            if N > 25:  # normal case
                std_Light.append(np.std(lightData[k])/np.sqrt(N))
                std_Dark.append(np.std(darkData[k])/np.sqrt(Nd) )  # sigma here is essentially sigma**2 so N must sqrt
            elif N > 3:  # few scans, use different statistics
                std_Light.append(np.sqrt(((N-1)/(N-3))*(np.std(lightData[k]) / np.sqrt(N))**2))
                std_Dark.append(np.sqrt(((Nd-1)/(Nd-3))*(np.std(darkData[k]) / np.sqrt(Nd))**2))
            else:
                msg = "too few scans to make meaningful statistics"
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            ave_Light.append(np.average(lightData[k]))
            ave_Dark.append(np.average(darkData[k]))

            for x in range(N):
                try:
                    lightData[k][x] -= darkData[k][x]
                except IndexError as err:
                    msg = f"Light/Dark indexing error PIU.HypperOCR: {err}"
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
            

            signalAve = np.average(lightData[k])

            # Normalised signal standard deviation =
            if signalAve:
                stdevSignal[wvl] = pow((pow(std_Light[i], 2) + pow(std_Dark[i], 2))/pow(signalAve, 2), 0.5)
            else:
                stdevSignal[wvl] = 0.0

        #print("std_Light/Dark")
        #print(std_Light)
        #print(stdevSignal)

        return dict(
            ave_Light=np.array(ave_Light),
            ave_Dark=np.array(ave_Dark),
            std_Light=np.array(std_Light),
            std_Dark=np.array(std_Dark),
            std_Signal=stdevSignal,
            )

    def FRM(self, node, uncGrp, raw_grps, raw_slices, stats, newWaveBands):
        """
        FRM regime propagation instrument uncertainties for HyperOCR, see D10 section 5.3.2 for more information.
        :param node: HDFRoot containing entire HDF file
        :param uncGrp: HDFGroup containing uncertainties from HDF file
        :param raw_grps: raw data dictionary containing Es, Li, & Lt as HDFGroups
        :param raw_slices: sliced raw data dictionary containing Es, Li, & Lt as np.arrays
        :param stats: nested dictionaries containing the output of LightDarkStats
        :param newWaveBands: common wavebands for interpolation of output
        """
         
        # calibration of HyperOCR following the FRM processing of FRM4SOC2
        output = {}
        for sensortype in ['ES', 'LI', 'LT']:
            print('FRM Processing:', sensortype)
            # Read data
            grp = raw_grps[sensortype]
            raw_data = np.asarray(list(raw_slices[sensortype]["LIGHT"]['data'].values())).transpose()
            raw_dark = np.asarray(list(raw_slices[sensortype]["DARK"]['data'].values())).transpose()

            # read in data for FRM processing
            # raw_data = np.asarray(list(slice.values())).transpose()  # raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())  # dark subtracted signal
            # raw_data = np.asarray(list(slice['data'].values())).transpose()
            # raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())  # dark subtracted signal
            int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
            int_time = np.mean(int_time)

            # Read FRM characterisation
            radcal_wvl = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
            radcal_cal_raw = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['2']
            S1 = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['6']
            S2 = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['8']
            S1_unc = np.array((pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['7'])[1:].to_list())  # removed /100 as not relative in tartu file
            S2_unc = np.array((pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['9'])[1:].to_list())
            mZ = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_STRAYDATA_LSF").data))
            mZ_unc = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_STRAYDATA_UNCERTAINTY").data))

            # remove 1st line and column, we work on 255 pixel not 256.
            mZ = mZ[1:, 1:]
            mZ_unc = mZ_unc[1:, 1:]

            # set up uncertainty propagation
            mDraws = 100  # number of monte carlo draws
            prop = punpy.MCPropagation(mDraws, parallel_cores=1)
            ind_raw_wvl = (radcal_wvl > 0)  # remove any index for which we do not have radcal wvls available

            mZ = mZ[:, ind_raw_wvl]
            mZ = mZ[ind_raw_wvl, :]
            mZ_unc = mZ_unc[:, ind_raw_wvl]
            mZ_unc = mZ_unc[ind_raw_wvl, :]

            sample_mZ = cm.generate_sample(mDraws, mZ, mZ_unc, "rand")
            # pythonic error here, code does not think np.array and array.pyi are the same things

            Ct = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_TEMPDATA_CAL").data
                                         )[f'{sensortype}_TEMPERATURE_COEFFICIENTS'][1:].tolist())
            Ct_unc = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_TEMPDATA_CAL").data
                                             )[f'{sensortype}_TEMPERATURE_UNCERTAINTIES'][1:].tolist())
            LAMP = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_LAMP").data)['2'])
            LAMP_unc = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_LAMP").data)['3'])/100*LAMP

            # Defined constants
            # nband = len(radcal_wvl)
            n_iter = 5

            Ct = Ct[ind_raw_wvl]
            Ct_unc = Ct_unc[ind_raw_wvl]

            # uncertainties from data:
            sample_int_time = cm.generate_sample(mDraws, int_time, None, None)
            sample_n_iter = cm.generate_sample(mDraws, n_iter, None, None, dtype=int)
            # sample_mZ = cm.generate_sample(mDraws, mZ, mZ_unc, "rand")
            sample_Ct = cm.generate_sample(mDraws, Ct, Ct_unc, "syst")

            # pad Lamp data and generate sample
            # LAMP = np.pad(LAMP, (0, nband - len(LAMP)), mode='constant')  # PAD with zero if not 255 long
            # LAMP_unc = np.pad(LAMP_unc, (0, nband - len(LAMP_unc)), mode='constant')
            sample_LAMP = cm.generate_sample(mDraws, LAMP, LAMP_unc, "syst")

            # Non-linearity alpha computation
            cal_int = radcal_cal_raw.pop(0)
            radcal_cal = radcal_cal_raw[ind_raw_wvl]
            sample_cal_int = cm.generate_sample(100, cal_int, None, None)

            t1 = S1.iloc[0]
            S1 = S1.drop(S1.index[0])
            t2 = S2.iloc[0]
            S2 = S2.drop(S2.index[0])

            S1 = np.asarray(S1, dtype=float)[ind_raw_wvl]
            S2 = np.asarray(S2, dtype=float)[ind_raw_wvl]
            S1_unc = S1_unc[ind_raw_wvl]
            S2_unc = S2_unc[ind_raw_wvl]

            sample_t1 = cm.generate_sample(mDraws, t1, None, None)
            sample_S1 = cm.generate_sample(mDraws, np.asarray(S1), S1_unc, "rand")
            sample_S2 = cm.generate_sample(mDraws, np.asarray(S2), S2_unc, "rand")

            k = t1/(t2 - t1)
            sample_k = cm.generate_sample(mDraws, k, None, None)
            S12 = self.S12func(k, S1, S2)
            sample_S12 = prop.run_samples(self.S12func, [sample_k, sample_S1, sample_S2])

            if self.sl_method.upper() == 'ZONG':  # zong is the default straylight correction
                sample_n_IB = self.gen_n_IB_sample(mDraws)
                sample_C_zong = prop.run_samples(ProcessL1b_FRMCal.Zong_SL_correction_matrix,
                                                 [sample_mZ, sample_n_IB])
                sample_S12_sl_corr = prop.run_samples(self.Zong_SL_correction, [sample_S12, sample_C_zong])
            else:  # slaper correction is used
                sample_S12_sl_corr = self.get_Slaper_Sl_unc(
                    S12, sample_S12, mZ, sample_mZ, n_iter, sample_n_iter, prop, mDraws
                )
            # S12_unc = (prop.process_samples(None, sample_S12_sl_corr)/S12_sl_corr)*100

            # alpha = ((S1-S12)/(S12**2)).tolist()
            alpha = self.alphafunc(S1, S12)
            sample_alpha = prop.run_samples(self.alphafunc, [sample_S1, sample_S12])

            # Updated calibration gain
            if sensortype == "ES":
                ## Irradiance direct and diffuse ratio
                res_sixS = BaseInstrument.read_sixS_model(node)

                ## compute updated radiometric calibration (required step after applying straylight correction)
                sample_updated_radcal_gain = prop.run_samples(self.update_cal_ES,
                                                              [sample_S12_sl_corr, sample_LAMP, sample_cal_int,
                                                               sample_t1])

                ## Compute avg cosine error

                # make zenith angle sample for cosine correction -- read from TU file column header, represents
                # available zenith angles and incurs no uncertainty (hence None, None in generate_sample).
                raw_zen = uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
                zenith_ang = np.asarray([float(x) for x in raw_zen])
                sample_zen_ang = cm.generate_sample(mDraws, zenith_ang, None, None)

                # Note: uncGrp already in scope
                coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype+"_ANGDATA_COSERROR").data))[1:, 2:]
                cos_unc = (np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:, 2:] / 100) * np.abs(coserror)
                coserror_90 = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype+"_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
                cos90_unc = (np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:, 2:] / 100) * np.abs(coserror_90)

                # get indexes for first and last radiometric calibration wavelengths in range [300-1000]
                i1 = np.argmin(np.abs(radcal_wvl - 300))
                i2 = np.argmin(np.abs(radcal_wvl - 1000))

                # comparing cos_error for 2 azimuth to check for asymmetry (ideally would be 0)
                azi_avg_coserr = (coserror + coserror_90) / 2.
                # each value has 4 numbers azi = 0, azi = 90, -zen, +zen which need their TU uncertainties combining
                total_coserror_err = np.sqrt(cos_unc**2 + cos90_unc**2 + cos_unc[:, ::-1]**2 + cos90_unc[:, ::-1]**2)

                # comparing cos_error for symetric zenith (ideally would be 0)
                zen_avg_coserr = (azi_avg_coserr + azi_avg_coserr[:, ::-1]) / 2.

                # get total error due to asymmetry  todo: find a smart way to do this without for loops
                tot_asymmetry_err = np.zeros(coserror.shape, float)
                for i in range(255):
                    for j in range(45):
                        tot_asymmetry_err[i, j] = np.std(
                            [coserror[i, j], coserror_90[i, j],
                             coserror[i, -j], coserror_90[i, -j]]
                        )  # get std across the 4 measurements azi_0, azi_90, zen, -zen

                # PDF of total error in cosine, combines TU uncertainties from lab characterisation and asymmetry in
                # cosine response
                zen_unc = np.sqrt(total_coserror_err**2 + tot_asymmetry_err**2)

                # 0 out data that is OOB (out of bounds)
                zen_avg_coserr[0:i1, :] = 0
                zen_avg_coserr[i2:, :] = 0
                zen_unc[0:i1, :] = 0
                zen_unc[i2:, :] = 0

                # use mean and error to build PDF, converting error to uncertainty using Monte Carlo
                sample_zen_avg_coserror = cm.generate_sample(mDraws, zen_avg_coserr, zen_unc, "syst")

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
                fhemi_unc = np.sqrt(sensitivity_coeff**2 * zen_unc_sum**2)

                # PDF of full hemispherical cosine error uncertainty
                sample_fhemi_coserr = cm.generate_sample(mDraws, full_hemi_coserror, fhemi_unc, "syst")
            else:
                PANEL = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_PANEL").data)['2'])
                PANEL_unc = (np.asarray(
                    pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_PANEL").data)['3'])/100)*PANEL
                # PANEL = np.pad(PANEL, (0, nband - len(PANEL)), mode='constant')
                # PANEL_unc = np.pad(PANEL_unc, (0, nband - len(PANEL_unc)), mode='constant')
                sample_PANEL = cm.generate_sample(100, PANEL, PANEL_unc, "syst")
                # updated_radcal_gain = self.update_cal_rad(S12_sl_corr, LAMP, PANEL, cal_int, t1)
                sample_updated_radcal_gain = prop.run_samples(self.update_cal_rad,
                                                              [sample_S12_sl_corr, sample_LAMP, sample_PANEL,
                                                               sample_cal_int,
                                                               sample_t1])

            # Filter Raw Data
            # ind_raw_data = (radcal_cal[radcal_wvl > 0]) > 0
            # raw_filtered = np.asarray([raw_data[n][ind_raw_data] for n in range(nmes)])
            # dark_filtered = np.asarray([raw_dark[n][ind_raw_data] for n in range(nmes)])

            ind_zero = radcal_cal <= 0
            ind_nan = np.isnan(radcal_cal)
            ind_nocal = ind_nan | ind_zero
            # set 1 instead of 0 to perform calibration (otherwise division per 0)
            sample_updated_radcal_gain[:, ind_nocal == True] = 1

            data = np.mean(raw_data, axis=0)  # raw data already dark subtracted, use mean for statistical analysis
            data[ind_nocal is True] = 0  # 0 out data outside of cal so it doesn't affect statistics
            dark = np.mean(raw_dark, axis=0)
            dark[ind_nocal is True] = 0
            # data is already 180 len for PML HyperOCR
            # signal uncertainties
            std_light = stats[sensortype]['std_Light']  # standard deviations are taken from generateSensorStats
            std_dark = stats[sensortype]['std_Dark']
            sample_light = cm.generate_sample(100, data, std_light, "rand")
            sample_dark = cm.generate_sample(100, dark, std_dark, "rand")
            sample_dark_corr_data = prop.run_samples(self.dark_Substitution, [sample_light, sample_dark])

            # plt.figure()
            # plt.plot(radcal_wvl, np.mean(sample_light, axis=0))
            # plt.plot(radcal_wvl, np.mean(sample_dark, axis=0), color='k')
            # plt.legend()
            # plt.grid()
            # plt.savefig(f"check_signal_FRM_{sensortype}.png")

            # Non-linearity
            data1 = self.DATA1(data, alpha)  # data*(1 - alpha*data)
            sample_data1 = prop.run_samples(self.DATA1, [sample_dark_corr_data, sample_alpha])

            # data1 unc
            # data1_unc = (prop.process_samples(None, sample_data1)/data1)*100

            # Straylight
            if self.sl_method.upper() == 'ZONG':
                sample_data2 = prop.run_samples(self.Zong_SL_correction, [sample_data1, sample_C_zong])
            else:  # slaper
                sample_data2 = self.get_Slaper_Sl_unc(
                    data1, sample_data1, mZ, sample_mZ, n_iter, sample_n_iter, prop, mDraws
                )


            # data2 unc
            # data2_unc = (prop.process_samples(None, sample_data2)/data2)*100

            # Calibration
            # data3 = self.DATA3(data2, cal_int, int_time, updated_radcal_gain)
            sample_data3 = prop.run_samples(
                self.DATA3, [sample_data2, sample_cal_int, sample_int_time, sample_updated_radcal_gain]
            )

            # thermal
            # data4 = self.DATA4(data3, Ct)
            sample_data4 = prop.run_samples(self.DATA4, [sample_data3, sample_Ct])

            # Cosine correction
            if sensortype == "ES":

                ## ADERU: SIXS results now match the length of input data
                ## I arbitrary select the first value here (index 0). If I understand correctly
                ## this will need to read the stored value in the sixS group instead of recomputing it.
                solar_zenith = np.mean(res_sixS['solar_zenith'], axis=0)
                direct_ratio = np.mean(res_sixS['direct_ratio'][:, 2:], axis=0)
                direct_ratio = self.interp_common_wvls(np.array(direct_ratio, float), res_sixS['wavelengths'], radcal_wvl)

                sample_sol_zen = cm.generate_sample(mDraws, solar_zenith,
                                                    np.asarray([0.05 for i in range(np.size(solar_zenith))]),
                                                    "rand")  # TODO: get second opinion on zen unc in 6S

                # sample_dir_rat = cm.generate_sample(mDraws, direct_ratio[ind_raw_wvl], 0.08*direct_ratio, "syst")
                sample_dir_rat = cm.generate_sample(mDraws, direct_ratio[ind_raw_wvl], 0.08*direct_ratio[ind_raw_wvl], "syst")

                # data5 = self.DATA5(data4, solar_zenith, direct_ratio, zenith_ang, avg_coserror, full_hemi_coserr)
                sample_cos_corr = prop.run_samples(
                    self.get_cos_corr, [sample_zen_ang,
                                        sample_sol_zen,
                                        sample_zen_avg_coserror]
                )
                sample_data5 = prop.run_samples(
                    self.cos_corr, [sample_data4, sample_dir_rat, sample_cos_corr[:,ind_raw_wvl], sample_fhemi_coserr[:,ind_raw_wvl]]
                )
                # sample_data5 = prop.run_samples(self.DATA5, [sample_data4,
                #                                              sample_sol_zen,
                #                                              sample_dir_rat,
                #                                              sample_zen_ang,
                #                                              sample_zen_avg_coserror, # check that zen_avg_coserror is correct
                #                                              sample_fhemi_coserr])

                unc = prop.process_samples(None, sample_data5)
                sample = sample_data5
            else:
                pol = uncGrp.getDataset(f"CLASS_HYPEROCR_{sensortype}_POLDATA_CAL")
                pol.datasetToColumns()
                x = pol.columns['0']
                y = pol.columns['1']
                y_new = np.interp(radcal_wvl, x, y)
                pol.columns['0'] = radcal_wvl
                pol.columns['1'] = y_new

                pol_unc = np.asarray(list(pol.columns['1']))[ind_raw_wvl]  # [1:]
                sample_pol = cm.generate_sample(mDraws, np.ones(len(pol_unc)), pol_unc, "syst")

                sample_pol_mesure = prop.run_samples(self.DATA6, [sample_data4, sample_pol])

                unc = prop.process_samples(None, sample_pol_mesure)
                sample = sample_pol_mesure

            ind_cal = (radcal_cal_raw[ind_raw_wvl]) > 0

            output[f"{sensortype.lower()}Wvls"] = radcal_wvl[ind_raw_wvl == True][ind_cal == True]
            output[f"{sensortype.lower()}Unc"] = unc[ind_cal == True]  # relative uncertainty
            output[f"{sensortype.lower()}Sample"] = sample[:, ind_cal == True]  # samples keep raw

            # sort the outputs ready for following process
            # get sensor specific wavebands to be keys for uncs, then remove from output
            wvls = np.asarray(output.pop(f"{sensortype.lower()}Wvls"), dtype=float)
            output[f"{sensortype.lower()}Unc"] = self.interp_common_wvls(
                output[f"{sensortype.lower()}Unc"], wvls, newWaveBands, return_as_dict=True)
            output[f"{sensortype.lower()}Sample"] = self.interpolateSamples(
                output[f"{sensortype.lower()}Sample"], wvls, newWaveBands)

            # if ConfigFile.settings['bL2UncertaintyBreakdownPlot']:
            #     p_unc = UncertaintyGUI(prop)  # initialise plotting obj - punpy MCP as arg
            #     time = node.attributes['TIME-STAMP'].split(' ')[-2]  # for labelling
            #     if sensortype.upper() == 'ES':
            #         p_unc.plot_unc_from_sample_1D(
            #             sample_data5, radcal_wvl, fig_name=f"breakdown_{sensortype}_{time}", name=f"Cosine", xlim=(400, 800)
            #         )
            #     else:
            #         p_unc.plot_unc_from_sample_1D(
            #             sample_pol_mesure, radcal_wvl, fig_name=f"breakdown_{sensortype}_{time}", name="Polarisation", xlim=(400, 800)
            #         )
            #     p_unc.plot_unc_from_sample_1D(
            #         sample_data4, radcal_wvl, fig_name=f"breakdown_{sensortype}_{time}", name=f"Thermal", xlim=(400, 800)
            #     )
            #     p_unc.plot_unc_from_sample_1D(
            #         sample_data3, radcal_wvl, fig_name=f"breakdown_{sensortype}_{time}", name=f"Calibration", xlim=(400, 800)
            #     )
            #     p_unc.plot_unc_from_sample_1D(
            #         sample_data2, radcal_wvl, fig_name=f"breakdown_{sensortype}_{time}", name=f"Straylight", xlim=(400, 800)
            #     )
            #     p_unc.plot_unc_from_sample_1D(
            #         sample_data1, radcal_wvl, fig_name=f"breakdown_{sensortype}_{time}", name=f"Nlin", xlim=(400, 800)
            #     )
            #     p_unc.plot_unc_from_sample_1D(
            #         sample_dark_corr_data, radcal_wvl, fig_name=f"breakdown_{sensortype}_{time}", name=f"Dark_Corrected", xlim=(400, 800),
            #         save={
            #             "cal_type": node.attributes["CAL_TYPE"],
            #             "time": node.attributes['TIME-STAMP'],
            #             "instrument": "SeaBird"
            #         }
            #     )

        return output

    # Measurement Functions
    @staticmethod
    def DATA1(data, alpha):
        return data*(1 - alpha*data)

    @staticmethod
    def DATA3(data2, cal_int, int_time, updated_radcal_gain):
        return data2*(cal_int/int_time)/updated_radcal_gain

    @staticmethod
    def DATA4(data3, Ct):
        data4 = data3*Ct
        data4[data4 <= 0] = 0
        return data4

    @staticmethod
    def DATA5(data4, solar_zenith, direct_ratio, zenith_ang, avg_coserror, full_hemi_coserror):
        ind_closest_zen = np.argmin(np.abs(zenith_ang - solar_zenith))
        cos_corr = (1 - avg_coserror[:, ind_closest_zen]/100)
        Fhcorr = (1 - full_hemi_coserror/100)
        return (direct_ratio*data4*cos_corr) + ((1 - direct_ratio)*data4*Fhcorr)

    @staticmethod
    def DATA6(signal, Cpol):
        return signal*Cpol

    @staticmethod
    def update_cal_ES(S12_sl_corr, LAMP, cal_int, t1):
        return (S12_sl_corr/LAMP)*(10*cal_int/t1)

    @staticmethod
    def update_cal_rad(S12_sl_corr, LAMP, PANEL, cal_int, t1):
        return (np.pi*S12_sl_corr)/(LAMP*PANEL)*(10*cal_int/t1)


class Trios(BaseInstrument):

    warnings.filterwarnings("ignore", message="One of the provided covariance matrix is not positivedefinite. It has been slightly changed")

    def __init__(self):
        super().__init__()   # call to instrument __init__
        self.instrument = 'TriOS-RAMSES'

    def lightDarkStats(self, grp, slice, sensortype):
        raw_cal = grp.getDataset(f"CAL_{sensortype}").data
        raw_back = np.asarray(grp.getDataset("BACK_"+sensortype).data.tolist())
        raw_data = np.asarray(list(slice['data'].values())).transpose()  # data is transpose of old version

        raw_wvl = np.array(pd.DataFrame(grp.getDataset(sensortype).data).columns)
        int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
        DarkPixelStart = int(grp.attributes["DarkPixelStart"])
        DarkPixelStop = int(grp.attributes["DarkPixelStop"])
        int_time_t0 = int(grp.getDataset(f"BACK_{sensortype}").attributes["IntegrationTime"])

        # sensitivity factor : if raw_cal==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = np.array([rc[0] == 0 for rc in raw_cal])  # changed due to raw_cal now being a np array
        ind_nan = np.array([np.isnan(rc[0]) for rc in raw_cal])
        ind_nocal = ind_nan | ind_zero
        raw_cal = np.array([rc[0] for rc in raw_cal])
        raw_cal[ind_nocal==True] = 1

        # check size of data
        nband = len(raw_back)  # indexes changed for raw_back as is brought to L2
        nmes = len(raw_data)
        if nband != len(raw_data[0]):
            print("ERROR: different number of pixels between dat and back")
            return None

        # Data conversion
        mesure = raw_data/65535.0
        calibrated_mesure = np.zeros((nmes, nband))
        calibrated_light_measure = np.zeros((nmes, nband))
        back_mesure = np.zeros((nmes, nband))

        for n in range(nmes):
            # Background correction : B0 and B1 read from "back data"
            back_mesure[n, :] = raw_back[:, 0] + raw_back[:, 1]*(int_time[n]/int_time_t0)
            back_corrected_mesure = mesure[n] - back_mesure[n, :]

            # Offset substraction : dark index read from attribute
            offset = np.mean(back_corrected_mesure[DarkPixelStart:DarkPixelStop])
            offset_corrected_mesure = back_corrected_mesure - offset

            # Normalization for integration time
            normalized_mesure = offset_corrected_mesure*int_time_t0/int_time[n]
            normalised_light_measure = back_corrected_mesure*int_time_t0/int_time[n]  # do not do the dark substitution as we need light data

            # Sensitivity calibration
            calibrated_mesure[n, :] = normalized_mesure/raw_cal  # uncommented /raw_cal L1985-6
            calibrated_light_measure[n, :] = normalised_light_measure/raw_cal

        # get light and dark data before correction
        light_avg = np.mean(calibrated_light_measure, axis=0)  # [ind_nocal == False]
        if nmes > 25:
            light_std = np.std(calibrated_light_measure, axis=0) / pow(nmes, 0.5)  # [ind_nocal == False]
        elif nmes > 3:
            light_std = np.sqrt(((nmes-1)/(nmes-3))*(np.std(calibrated_light_measure, axis=0) / np.sqrt(nmes))**2)
        else:
            msg = "too few scans to make meaningful statistics"
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        # ensure all TriOS outputs are length 255 to match SeaBird HyperOCR stats output
        ones = np.ones(nband)  # to provide array of 1s with the correct shape
        dark_avg = ones * offset
        if nmes > 25:
            dark_std = ones * np.std(back_corrected_mesure[DarkPixelStart:DarkPixelStop], axis=0) / pow(nmes, 0.5)
        else:  # already checked for light data so we know nmes > 3
            dark_std = np.sqrt(((nmes-1)/(nmes-3))*(
                    ones * np.std(back_corrected_mesure[DarkPixelStart:DarkPixelStop], axis=0)/np.sqrt(nmes))**2)
        # adjusting the dark_ave and dark_std shapes will remove sensor specific behaviour in Default and Factory

        stdevSignal = {}
        for i, wvl in enumerate(raw_wvl):
            stdevSignal[wvl] = pow(
                (pow(light_std[i], 2) + pow(dark_std[i], 2)), 0.5) / np.average(calibrated_mesure, axis=0)[i]

        return dict(
            ave_Light=np.array(light_avg),
            ave_Dark=np.array(dark_avg),
            std_Light=np.array(light_std),
            std_Dark=np.array(dark_std),
            std_Signal=stdevSignal,
        )

    def FRM(self, node, uncGrp, raw_grps, raw_slices, stats, newWaveBands):
        """
        """
        unc_dict = {}
        for sensortype in ['ES', 'LI', 'LT']:

            # straylight
            unc_dict[f"mZ_unc_{sensortype}"] = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_STRAYDATA_UNCERTAINTY").data))
            # temperature
            unc_dict[f"Ct_unc_{sensortype}"] = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_TEMPDATA_CAL").data[1:].transpose().tolist())[5])
            # Radcal Cal S1/S2
            unc_dict[f'S1_unc_{sensortype}'] = (pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['7'])[1:]
            unc_dict[f'S2_unc_{sensortype}'] = (pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['9'])[1:]
            # Stability
            # unc_dict[f'stab_{sensortype}'] = self.extract_unc_from_grp(uncGrp, f"{sensortype}_STABDATA_CAL", '1')  # class based method
            # Nlin
            # if I remove uncertainties in S1/S2 then I necessarily remove the Nlin unc!

            # Lamp_cal - part of radcal corr
            LAMP = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_LAMP").data)['2']) / 10  # div by 10
            unc_dict[f'lamp_{sensortype}'] = (np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_LAMP").data)['3'])/100)*LAMP
            
            if sensortype == 'ES':
                # Cosine
                coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:, 2:]
                coserror_90 = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
                unc_dict['cos_unc'] = (np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:, 2:] / 100) * np.abs(coserror)
                unc_dict['cos90_unc'] = (np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:, 2:] / 100) * np.abs(coserror_90)
            else:
                # Polarisation
                # read pol uncertainties and interpolate to radcal wavebands
                radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
                pol = uncGrp.getDataset(f"CLASS_RAMSES_{sensortype}_POLDATA_CAL")
                pol.datasetToColumns()
                x = pol.columns['0']
                y = pol.columns['1']
                y_new = np.interp(radcal_wvl, x, y)
                pol.columns['0'] = radcal_wvl
                pol.columns['1'] = y_new
                unc_dict[f'pol_unc_{sensortype}'] = np.asarray(list(pol.columns['1']))
                
                # Panel - part of radcal corr
                PANEL = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_PANEL").data)['2'])
                unc_dict[f'unc_PANEL_{sensortype}'] = (np.asarray(
                    pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_PANEL").data)['3'])/100)*PANEL

        return self._FRM(node, uncGrp, unc_dict, raw_grps, raw_slices, stats, newWaveBands)

    def _FRM(self, node, uncGrp, uncDict, raw_grps, raw_slices, stats, newWaveBands) -> dict[str, Any]:
        """
        FRM regime propagation instrument uncertainties, see D10 section 5.3.2 for more information.
        :param node: HDFRoot containing entire HDF file
        :param uncGrp: HDFGroup containing uncertainties from HDF file
        :param raw_grps: raw data dictionary containing Es, Li, & Lt as HDFGroups
        :param raw_slices: sliced raw data dictionary containing Es, Li, & Lt as np.arrays
        :param stats: not required for TriOS specific processing, set to None at start of method
        :param newWaveBands: common wavebands for interpolation of output
        """
        
        # TriOS specific
        output = {}
        # stats = None  # stats is unused in this method, but required as an input because of Seabird
        for sensortype in ['ES', 'LI', 'LT']:

            ### Read HDF file inputs
            grp = raw_grps[sensortype]
            # slice = rawSlices[sensortype]
            slice = raw_slices[sensortype]

            # read data for L1B FRM processing
            raw_data = np.asarray(list(slice['data'].values())).transpose()  # raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())
            DarkPixelStart = int(grp.attributes["DarkPixelStart"])
            DarkPixelStop = int(grp.attributes["DarkPixelStop"])
            int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
            int_time_t0 = int(grp.getDataset("BACK_" + sensortype).attributes["IntegrationTime"])

            ### Read full characterisation files
            radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())

            ### for masking arrays only
            raw_cal = grp.getDataset(f"CAL_{sensortype}").data

            B0 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['4'][1:].tolist())
            B1 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['5'][1:].tolist())
            S1 = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['6']
            S2 = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['8']
            mZ = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_STRAYDATA_LSF").data))
            mZ_unc = uncDict[f"mZ_unc_{sensortype}"]
            mZ = mZ[1:, 1:]  # remove 1st line and column, we work on 255 pixel not 256.
            mZ_unc = mZ_unc[1:, 1:]  # remove 1st line and column, we work on 255 pixel not 256.
            Ct = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_TEMPDATA_CAL").data[1:].transpose().tolist())[4])
            Ct_unc = uncDict[f"Ct_unc_{sensortype}"]

            # Convert TriOS mW/m2/nm to uW/cm^2/nm
            LAMP = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_LAMP").data)['2']) / 10  # div by 10
            # corrects LAMP and LAMP_unc
            LAMP_unc = uncDict[f'lamp_{sensortype}']

            # Defined constants
            nband = len(B0)
            nmes = len(raw_data)
            grp.attributes["nmes"] = nmes
            n_iter = 5

            # set up uncertainty propagation
            mDraws = 100  # number of monte carlo draws
            prop = punpy.MCPropagation(mDraws, parallel_cores=1)

            # uncertainties from data:
            sample_mZ = cm.generate_sample(mDraws, mZ, mZ_unc, "rand")

            sample_n_iter = cm.generate_sample(mDraws, n_iter, None, None, dtype=int)
            sample_int_time_t0 = cm.generate_sample(mDraws, int_time_t0, None, None)
            sample_LAMP = cm.generate_sample(mDraws, LAMP, LAMP_unc, "syst")
            sample_Ct = cm.generate_sample(mDraws, Ct, Ct_unc, "syst")

            # Non-linearity alpha computation

            t1 = S1.iloc[0]
            S1 = S1.drop(S1.index[0])
            t2 = S2.iloc[0]
            S2 = S2.drop(S2.index[0])
            sample_t1 = cm.generate_sample(mDraws, t1, None, None)

            S1 = np.asarray(S1/65535.0, dtype=float)
            S2 = np.asarray(S2/65535.0, dtype=float)
            k = t1/(t2 - t1)
            sample_k = cm.generate_sample(mDraws, k, None, None)

            S1_unc = uncDict[f'S1_unc_{sensortype}']
            S2_unc = uncDict[f'S2_unc_{sensortype}']
            S1_unc = np.asarray(S1_unc/65535.0, dtype=float)
            S2_unc = np.asarray(S2_unc/65535.0, dtype=float)  # put in the same units as S1/S2

            sample_S1 = cm.generate_sample(mDraws, np.asarray(S1), S1_unc, "rand")
            sample_S2 = cm.generate_sample(mDraws, np.asarray(S2), S2_unc, "rand")

            S12 = self.S12func(k, S1, S2)
            sample_S12 = prop.run_samples(self.S12func, [sample_k, sample_S1, sample_S2])

            if self.sl_method.upper() == 'ZONG':  # for internal coding use only, set by default in HCP
                sample_n_IB = self.gen_n_IB_sample(mDraws)  # n_IB sample must be integer and in the range 3-6
                sample_C_zong = prop.run_samples(ProcessL1b_FRMCal.Zong_SL_correction_matrix,
                                                 [sample_mZ, sample_n_IB])
                sample_S12_sl_corr = prop.run_samples(self.Zong_SL_correction, [sample_S12, sample_C_zong])
            else:  # slaper
                sample_S12_sl_corr = self.get_Slaper_Sl_unc(
                    S12, sample_S12, mZ, sample_mZ, n_iter, sample_n_iter, prop, mDraws
                )

            alpha = self.alphafunc(S1, S12)
            sample_alpha = prop.run_samples(self.alphafunc, [sample_S1, sample_S12])

            # Updated calibration gain
            if sensortype == "ES":
                # Irradiance direct and diffuse ratio
                # res_sixS = ProcessL1b_FRMCal.get_direct_irradiance_ratio(node, sensortype, called_L2=True)
                res_sixS = BaseInstrument.read_sixS_model(node)

                # updated_radcal_gain = self.update_cal_ES(S12_sl_corr, LAMP, int_time_t0, t1)
                sample_updated_radcal_gain = prop.run_samples(self.update_cal_ES,
                                                              [sample_S12_sl_corr, sample_LAMP, sample_int_time_t0,
                                                               sample_t1])
                ## Compute avg cosine error

                # make zenith angle sample for cosine correction -- read from TU file column header, represents
                # available zenith angles and incurs no uncertainty (hence None, None in generate_sample).
                raw_zen = uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
                zenith_ang = np.asarray([float(x) for x in raw_zen])
                sample_zen_ang = cm.generate_sample(mDraws, zenith_ang, None, None)

                # Note: uncGrp already in scope
                coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:, 2:]
                cos_unc = uncDict['cos_unc']
                coserror_90 = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[
                              1:, 2:]
                cos90_unc = uncDict['cos90_unc']

                # get indexes for first and last radiometric calibration wavelengths in range [300-1000]
                i1 = np.argmin(np.abs(radcal_wvl - 300))
                i2 = np.argmin(np.abs(radcal_wvl - 1000))

                # comparing cos_error for 2 azimuth to check for asymmetry (ideally would be 0)
                azi_avg_coserr = (coserror + coserror_90) / 2.
                # each value has 4 numbers azi = 0, azi = 90, -zen, +zen which need their TU uncertainties combining
                total_coserror_err = np.sqrt(
                    cos_unc ** 2 + cos90_unc ** 2 + cos_unc[:, ::-1] ** 2 + cos90_unc[:, ::-1] ** 2)

                # comparing cos_error for symetric zenith (ideally would be 0)
                zen_avg_coserr = (azi_avg_coserr + azi_avg_coserr[:, ::-1]) / 2.

                # get total error due to asymmetry  todo: find a smart way to do this without for loops
                tot_asymmetry_err = np.zeros(coserror.shape, float)
                for i in range(255):
                    for j in range(45):
                        tot_asymmetry_err[i, j] = np.std(
                            [coserror[i, j], coserror_90[i, j],
                             coserror[i, -j], coserror_90[i, -j]]
                        )  # get std across the 4 measurements azi_0, azi_90, zen, -zen

                # PDF of total error in cosine, combines TU uncertainties from lab characterisation and asymmetry in
                # cosine response
                zen_unc = np.sqrt(total_coserror_err ** 2 + tot_asymmetry_err ** 2)

                # 0 out data that is OOB (out of bounds)
                zen_avg_coserr[0:i1, :] = 0
                zen_avg_coserr[i2:, :] = 0
                zen_unc[0:i1, :] = 0
                zen_unc[i2:, :] = 0

                # use mean and error to build PDF, converting error to uncertainty using Monte Carlo
                sample_zen_avg_coserror = cm.generate_sample(mDraws, zen_avg_coserr, zen_unc, "syst")

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
                fhemi_unc = np.sqrt(sensitivity_coeff ** 2 * zen_unc_sum ** 2)

                # PDF of full hemispherical cosine error uncertainty
                sample_fhemi_coserr = cm.generate_sample(mDraws, full_hemi_coserror, fhemi_unc, "syst")

                # I was doing some debugging here, sorry that this ended up in the PR.
                # p_unc = UncertaintyGUI(prop)
                # p_unc.plot_unc_from_sample_1D(sample_zen_avg_coserror, radcal_wvl, "zen")
                # p_unc.plot_unc_from_sample_1D(sample_fhemi_coserr, radcal_wvl, "fhemi")
            else:
                PANEL = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_PANEL").data)['2'])
                unc_PANEL = uncDict[f'unc_PANEL_{sensortype}']
                sample_PANEL = cm.generate_sample(mDraws, PANEL, unc_PANEL, "syst")
                # updated_radcal_gain = self.update_cal_rad(PANEL, S12_sl_corr, LAMP, int_time_t0, t1)
                sample_updated_radcal_gain = prop.run_samples(self.update_cal_rad,
                                                              [sample_PANEL, sample_S12_sl_corr, sample_LAMP,
                                                               sample_int_time_t0, sample_t1])

            # Data conversion
            mesure = raw_data/65535.0
            # todo: issue #253 there is a nan in the raw data for the 4th ensemble! implement in L1AQC.
            back_mesure = np.array([B0 + B1*(int_time[n]/int_time_t0) for n in range(nmes)])
            back_corrected_mesure = mesure - back_mesure
            std_light = np.std(back_corrected_mesure, axis=0)/nmes
            sample_back_corrected_mesure = cm.generate_sample(mDraws, np.mean(back_corrected_mesure, axis=0), std_light, "rand")

            # Offset substraction : dark index read from attribute
            offset = np.mean(back_corrected_mesure[:, DarkPixelStart:DarkPixelStop], axis=1)
            offset_corrected_mesure = np.asarray(
                [back_corrected_mesure[:, i] - offset for i in range(nband)]).transpose()
            offset_std = np.std(back_corrected_mesure[:, DarkPixelStart:DarkPixelStop], axis=1)  # std in dark pixels
            std_dark = np.power((np.power(np.std(offset), 2) + np.power(offset_std, 2))/np.power(nmes, 2), 0.5)

            # add in quadrature with std in offset across scans
            sample_offset = cm.generate_sample(mDraws, np.mean(offset), np.mean(std_dark), "rand")
            sample_offset_corrected_mesure = prop.run_samples(self.dark_Substitution,
                                                              [sample_back_corrected_mesure, sample_offset])

            # average the signal and int_time for the station
            offset_corr_mesure = np.mean(offset_corrected_mesure, axis=0)
            int_time = np.average(int_time)

            prop = punpy.MCPropagation(mDraws, parallel_cores=1)

            # set standard variables
            # n_iter = 5
            # sample_n_iter = cm.generate_sample(mDraws, n_iter, None, None, dtype=int)

            # Non-Linearity Correction
            linear_corr_mesure = self.non_linearity_corr(offset_corr_mesure, alpha)
            sample_linear_corr_mesure = prop.run_samples(self.non_linearity_corr,
                                                         [sample_offset_corrected_mesure, sample_alpha])

            # Straylight Correction
            if self.sl_method.upper() == 'ZONG':  # for internal use only, Zong set as default in HCP
                sample_straylight_corr_mesure = prop.run_samples(
                    self.Zong_SL_correction, [sample_linear_corr_mesure, sample_C_zong]
                )
            else:
                sample_straylight_corr_mesure = self.get_Slaper_Sl_unc(
                    linear_corr_mesure, sample_linear_corr_mesure, mZ, sample_mZ, n_iter, sample_n_iter, prop, mDraws
                )   # simplified code by adding Slaper correction to one fucntion

            # Normalization Correction, based on integration time
            sample_normalized_mesure = sample_straylight_corr_mesure*int_time_t0/int_time

            # Calculate New Calibration Coeffs
            sample_calibrated_mesure = prop.run_samples(self.absolute_calibration,
                                                        [sample_normalized_mesure, sample_updated_radcal_gain])

            # Thermal correction
            sample_thermal_corr_mesure = prop.run_samples(self.thermal_corr, [sample_Ct, sample_calibrated_mesure])

            if sensortype.lower() == "es":
                # get cosine correction attributes and samples from dictionary

                ## ADERU: SIXS results now match the length of input data
                ## I arbitrary select the first value here (index 0). If I understand correctly
                ## this will need to read the stored value in the sixS group instead of recomputing it.
                solar_zenith = np.mean(res_sixS['solar_zenith'], axis=0)
                direct_ratio = np.mean(res_sixS['direct_ratio'][:, 2:], axis=0)
                direct_ratio = self.interp_common_wvls(direct_ratio, res_sixS['wavelengths'], radcal_wvl)
                sample_sol_zen = cm.generate_sample(mDraws, solar_zenith, 0.05, "rand")
                sample_dir_rat = cm.generate_sample(mDraws, direct_ratio, 0.08*direct_ratio, "syst")
                sample_cos_corr = prop.run_samples(
                    self.get_cos_corr, [sample_zen_ang,
                                        sample_sol_zen,
                                        sample_zen_avg_coserror]
                )
                sample_cos_corr_mesure = prop.run_samples(
                    self.cos_corr, [sample_thermal_corr_mesure, sample_dir_rat, sample_cos_corr, sample_fhemi_coserr]
                )
                # sample_cos_corr_mesure = prop.run_samples(self.cosine_corr,
                #                                           [sample_zen_avg_coserror, sample_fhemi_coserr, sample_zen_ang,
                #                                            sample_thermal_corr_mesure, sample_sol_zen, sample_dir_rat])

                sample = sample_cos_corr_mesure
                unc = prop.process_samples(None, sample_cos_corr_mesure)
            else:
                pol_unc = uncDict[f'pol_unc_{sensortype}']
                sample_pol = cm.generate_sample(mDraws, np.ones(len(pol_unc)), pol_unc, "syst")
                sample_pol_mesure = prop.run_samples(self.CPOL_MF, [sample_thermal_corr_mesure, sample_pol])

                sample = sample_pol_mesure
                unc = prop.process_samples(None, sample_pol_mesure)

            # mask for arrays
            ind_zero = np.array([rc[0] == 0 for rc in raw_cal])  # changed due to raw_cal now being a np array
            ind_nan = np.array([np.isnan(rc[0]) for rc in raw_cal])
            ind_nocal = ind_nan | ind_zero

            # Remove wvl without calibration from the dataset and make uncertainties relative
            output[f"{sensortype.lower()}Wvls"] = radcal_wvl[ind_nocal == False]
            output[f"{sensortype.lower()}Unc"] = unc[ind_nocal == False]
            output[f"{sensortype.lower()}Sample"] = sample[:, ind_nocal == False]  # samples keep raw

        for sensortype in ['ES', 'LI', 'LT']:
            # get sensor specific wavebands - output[f"{sensortype.lower()}Wvls"].pop
            wvls = np.asarray(output.pop(f"{sensortype.lower()}Wvls"), dtype=float)
            output[f"{sensortype.lower()}Unc"] = self.interp_common_wvls(
                output[f"{sensortype.lower()}Unc"], wvls, newWaveBands, return_as_dict=True)
            output[f"{sensortype.lower()}Sample"] = self.interpolateSamples(
                output[f"{sensortype.lower()}Sample"], wvls, newWaveBands)

        return output  # return products as dictionary to be appended to xSlice

    # Measurement functions
    @staticmethod
    def back_Mesure(B0, B1, int_time, t0):
        return B0 + B1*(int_time/t0)

    @staticmethod
    def CPOL_MF(signal, Cpol):
        return signal*Cpol

    @staticmethod
    def update_cal_ES(S12_sl_corr, LAMP, int_time_t0, t1):
        updated_radcal_gain = (S12_sl_corr/LAMP)*(int_time_t0/t1)
        # sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = (updated_radcal_gain <= 1e-2)
        ind_nan = np.isnan(updated_radcal_gain)
        ind_nocal = ind_nan | ind_zero
        updated_radcal_gain[ind_nocal == True] = 1  # set 1 instead of 0 to perform calibration (otherwise division per 0)
        return updated_radcal_gain

    @staticmethod
    def update_cal_rad(PANEL, S12_sl_corr, LAMP, int_time_t0, t1):
        updated_radcal_gain = (np.pi*S12_sl_corr)/(LAMP*PANEL)*(int_time_t0/t1)

        # sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = (updated_radcal_gain <= 1e-2)
        ind_nan = np.isnan(updated_radcal_gain)
        ind_nocal = ind_nan | ind_zero
        updated_radcal_gain[
            ind_nocal == True] = 1  # set 1 instead of 0 to perform calibration (otherwise division per 0)
        return updated_radcal_gain

class Dalec(BaseInstrument):

    warnings.filterwarnings("ignore", message="One of the provided covariance matrix is not positivedefinite. It has been slightly changed")

    def __init__(self):
        super().__init__()  # call to instrument __init__
        self.instrument = "Dalec"

    def lightDarkStats(self, grp, slice, sensortype):
        # Dalec
        lightSlice = copy.deepcopy(slice)  # copy to prevent changing of Raw data
    
        lightData = lightSlice['data']  # lightGrp.getDataset(sensortype)
        darkData = lightSlice['dc']
        if  grp is None:
            msg = f'No radiometry found for {sensortype}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        
        # Correct light data by subtracting interpolated dark data from light data
        std_Light = []
        std_Dark = []
        ave_Light = []
        ave_Dark = []
        stdevSignal = {}

        # number of replicates for light and dark readings
        N = np.asarray(list(lightData.values())).shape[1]

        if N > 25:  # normal case
            std_Dark0=np.std(darkData[sensortype])/np.sqrt(N)
        elif N > 3:
            std_Dark0=np.sqrt(((N-1)/(N-3))*(np.std(darkData[sensortype]) / np.sqrt(N))**2)

        ave_Dark0=np.average(darkData[sensortype])
        #print("std_Dark0")
        #print(std_Dark0)
        for i, k in enumerate(lightData.keys()):
            wvl = str(float(k))

            # apply normalisation to the standard deviations used in uncertainty calculations
            if N > 25:  # normal case
                std_Light.append(np.std(lightData[k])/np.sqrt(N))
                std_Dark.append(std_Dark0)  # sigma here is essentially sigma**2 so N must sqrt
            elif N > 3:  # few scans, use different statistics
                std_Light.append(np.sqrt(((N-1)/(N-3))*(np.std(lightData[k]) / np.sqrt(N))**2))
                std_Dark.append(std_Dark0)
            else:
                msg = "too few scans to make meaningful statistics"
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            ave_Light.append(np.average(lightData[k]))
            ave_Dark.append(ave_Dark0)

            for x in range(N):
                lightData[k][x] -= darkData[sensortype][x]

            signalAve = np.average(lightData[k])

            # Normalised signal standard deviation =
            if signalAve:
                stdevSignal[wvl] = pow((pow(std_Light[i], 2) + pow(std_Dark[i], 2))/pow(signalAve, 2), 0.5)
            else:
                stdevSignal[wvl] = 0.0

        #print("std_Light/Dark")
        #print(std_Light)
        #print(stdevSignal)
        return dict(
            ave_Light=np.array(ave_Light),
            ave_Dark=np.array(ave_Dark),
            std_Light=np.array(std_Light),
            std_Dark=np.array(std_Dark),
            std_Signal=stdevSignal,
            )

    def FRM(self, node, uncGrp, raw_grps, raw_slices, stats, newWaveBands):
        # calibration of HyperOCR following the FRM processing of FRM4SOC2
        output = {}
        return output
