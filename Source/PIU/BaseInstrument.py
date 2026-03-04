# linting
from abc import ABC, abstractmethod
from typing import Union, Optional, Any
import warnings

# maths
import numpy as np
import copy
from datetime import datetime
import comet_maths as cm

# Source
from Source.ConfigFile import ConfigFile
from Source.HDFGroup import HDFGroup
from Source.HDFRoot import HDFRoot
from Source.Weight_RSR import Weight_RSR

# PIU
from Source.PIU.Uncertainty_Analysis import Propagate
from Source.PIU.utils import utils
from Source.PIU.PIUDataStore import PIUDataStore as pds
from Source.PIU.Breakdown_CB import PlotMaths

# UTILITIES
from Source.utils.loggingHCP import writeLogFileAndPrint


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

    sensors = ['ES', 'LI', 'LT']

    def __init__(self):
        if ConfigFile.settings["SensorType"].lower() == "trios es only":
            BaseInstrument.sensors = ['ES']
        # use this to switch the straylight correction method -> FOR UNCERTAINTY PROPAGATION ONLY <- between SLAPER and
        # ZONG. Not added to config file settings because this isn't intended for the end user.
        self.sl_method: str = 'ZONG'        
        warnings.filterwarnings("ignore", message="One of the correlation matrices is not positive definite.",category=UserWarning)
    ## Regime Agnostic Methods ##

    @abstractmethod
    def lightDarkStats(self, grp: Union[HDFGroup, dict[str: HDFGroup]], XSlice: dict, sensortype: str) -> dict[str: np.array]:
        pass

    def generateSensorStats(self, i_type: str, rawData: dict, rawSlice: dict, newWaveBands: np.array) -> dict[str: np.array]:
        """
        Generate Sensor Stats calls lightDarkStats for a given instrument. Once sensor statistics are known, they are 
        interpolated to common wavebands to match the other L1B sensor inputs Es, Li, & Lt.

        "Raw" refers to uncalibrated L1AQC data.

        :return: dictionary of statistics used later in the processing pipeline. Keys are:
        [ave_Light, ave_Dark, std_Light, std_Dark, std_Signal]
        """
        stats = {}  # used tp store standard deviations and averages as a function return for generateSensorStats
        for s_type in self.sensors:
            # filter nans
            from Source.PIU.utils import utils

            if i_type.lower() in ["sorad", "trios", "trios es only"]:
                # L1AQC unsliced data group is passed and used for calibration data contained therein.
                utils.apply_NaN_Mask(rawSlice[s_type]['data'])  # apply Nan mask
                args = [copy.deepcopy(rawData[s_type]),
                        copy.deepcopy(rawSlice[s_type]),
                        s_type]
                    # copy.deepcopy ensures RAW data is unchanged for FRM uncertainty generation.
            elif i_type.lower() == "dalec":
                # NOTE: Under development
                # L1AQC unsliced data group is passed, but not used.
                utils.apply_NaN_Mask(rawSlice[s_type]['light'])
                utils.apply_NaN_Mask(rawSlice[s_type]['dark'])
                args = [
                    {'L1AQC': copy.deepcopy(rawData[s_type].datasets[s_type]), 'DARK': copy.deepcopy(rawData[s_type].datasets['DARK_CNT'])},
                    {'LIGHT': copy.deepcopy(rawSlice[s_type]['light']), 'DARK': copy.deepcopy(rawSlice[s_type]['dark'])},
                    s_type
                ]
            elif i_type.lower() == "seabird":
                # L1AQC unsliced data group is passed, but only used for reference.
                utils.apply_NaN_Mask(rawSlice[s_type]['LIGHT']['data'])  # how closely should light follow dark, i.e. do we mask light with dark and vice versa - Ashley
                utils.apply_NaN_Mask(rawSlice[s_type]['DARK']['data'])
                args =[
                    {'LIGHT': rawData[s_type]['LIGHT'], 'DARK': rawData[s_type]['DARK']},
                    {'LIGHT': rawSlice[s_type]['LIGHT'], 'DARK': rawSlice[s_type]['DARK']},
                    s_type
                    ]
            else:
                writeLogFileAndPrint("WARNING sensor not recognised")
                args = None

            try:
                stats[s_type] = self.lightDarkStats(*args)
            except (ValueError, IndexError, KeyError):
                writeLogFileAndPrint("Could not generate statistics for the ensemble")
                return False

        # interpolate std Signal to common wavebands - taken from L2 ES group: ProcessL2.py L1352
        
        try:
            for s_type in self.sensors:  # we want the std at common wavebands for outputting in hdf file
                stats[s_type]['Signal_std_Interpolated'] = utils.interp_common_wvls(
                    stats[s_type]['Signal_std'],
                    np.asarray(list(stats[s_type]['Signal_noise'].keys()), dtype=float),  # wavelengths available in Signal noise keys
                    newWaveBands,
                    return_as_dict=True)
            
            return stats
            
        except (IndexError, TypeError) as err:
            writeLogFileAndPrint(f"Unable to parse statistics with for the ensemble: {err}. (possibly too few scans).")
            return False

    def ClassBasedL1A(self, node: HDFRoot, uncGrp: HDFGroup, stats: dict[str, np.array]) -> Union[dict[str, dict], bool]:
        """
        Propagates class based uncertainties for all instruments. If no calibration uncertainties are available will use Sirrex-7 
        to propagate uncertainties in the SeaBird Case. See D-10 secion 5.3.1.

        :param node: HDFRoot containing all L1BQC data
        :param uncGrp: HDFGroup containing raw uncertainties
        :param stats: output of PIU.py BaseInstrument.generateSensorStats

        :return: dictionary of instrument uncertainties [Es uncertainty, Li uncertainty, Lt uncertainty]
        alternatively errors in processing will return False for context management purposes.
        """

        try:
            # create object for running uncertainty propagation, M means number of monte carlo draws
            mDraws = 100
            UNC_obj_CB = Propagate(M=mDraws, cores=0)
            PDS = pds(node, uncGrp)
        except NotImplementedError:
            print("Uncertainties not implemented for TriOS/DALEC/So-rad in Factory Regime")
            return False, None

        # put cal_int and int_time into propagate object to save having to pass arguments through punpy
        UNC_obj_CB.cal_int  = {sensor: PDS.coeff[sensor]['cal_int'] for sensor in stats.keys()}
        UNC_obj_CB.int_time = {sensor: PDS.coeff[sensor]['int_time'] for sensor in stats.keys()}

        # Unlike LB+ data that are interpolated (see ClassBaseL2 below), L1AQC results can be directly subset for calibrated wavebands
        #   based on a common set of pixels across all instruments for mathing with stats and PDS.
        PDS.l1ACommonCalPix = PDS.l1ACommonCalPix
        PDS.l1ACommonCalPix255 = PDS.l1ACommonCalPix255
        ones   = np.ones_like(PDS.uncs['ES']['cal'])[PDS.l1ACommonCalPix]
        zeroes = np.zeros_like(PDS.uncs['ES']['cal'])[PDS.l1ACommonCalPix]

        means = [stats['ES']['ave_Light'][PDS.l1ACommonCalPix],
                 stats['ES']['ave_Dark'][PDS.l1ACommonCalPix],
                 stats['LI']['ave_Light'][PDS.l1ACommonCalPix] if 'LI' in stats else ones,
                 stats['LI']['ave_Dark'][PDS.l1ACommonCalPix] if 'LI' in stats else ones,
                 stats['LT']['ave_Light'][PDS.l1ACommonCalPix] if 'LT' in stats else ones,
                 stats['LT']['ave_Dark'][PDS.l1ACommonCalPix] if 'LT' in stats else ones,
                 PDS.coeff['ES']['cal'][PDS.l1ACommonCalPix],
                 PDS.coeff['LI']['cal'][PDS.l1ACommonCalPix] if 'LI' in PDS.coeff else ones,
                 PDS.coeff['LT']['cal'][PDS.l1ACommonCalPix] if 'LT' in PDS.coeff else ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
        ]

        uncertainties = [stats['ES']['std_Light'][PDS.l1ACommonCalPix],
                         stats['ES']['std_Dark'][PDS.l1ACommonCalPix],
                         stats['LI']['std_Light'][PDS.l1ACommonCalPix] if 'LI' in stats else zeroes,
                         stats['LI']['std_Dark'][PDS.l1ACommonCalPix] if 'LI' in stats else zeroes,
                         stats['LT']['std_Light'][PDS.l1ACommonCalPix] if 'LT' in stats else zeroes,
                         stats['LT']['std_Dark'][PDS.l1ACommonCalPix] if 'LT' in stats else zeroes,
                         (PDS.uncs['ES']['cal'][PDS.l1ACommonCalPix] / 200 * PDS.coeff['ES']['cal'][PDS.l1ACommonCalPix]),
                         (PDS.uncs['LI']['cal'][PDS.l1ACommonCalPix] / 200 * PDS.coeff['LI']['cal'][PDS.l1ACommonCalPix]) if 'LI' in PDS.uncs else zeroes,
                         (PDS.uncs['LT']['cal'][PDS.l1ACommonCalPix] / 200 * PDS.coeff['LT']['cal'][PDS.l1ACommonCalPix]) if 'LT' in PDS.uncs else zeroes,
                         PDS.uncs['ES']['stab'][PDS.l1ACommonCalPix255],
                         PDS.uncs['LI']['stab'][PDS.l1ACommonCalPix255] if 'LI' in PDS.uncs else zeroes,
                         PDS.uncs['LT']['stab'][PDS.l1ACommonCalPix255] if 'LT' in PDS.uncs else zeroes,
                         PDS.uncs['ES']['nlin'][PDS.l1ACommonCalPix],
                         PDS.uncs['LI']['nlin'][PDS.l1ACommonCalPix] if 'LI' in PDS.uncs else zeroes,
                         PDS.uncs['LT']['nlin'][PDS.l1ACommonCalPix] if 'LT' in PDS.uncs else zeroes,
                         np.array(PDS.uncs['ES']['stray'][PDS.l1ACommonCalPix255]) / 100,  # change straylight and set nl uncs with file
                         np.array(PDS.uncs['LI']['stray'][PDS.l1ACommonCalPix255]) / 100 if 'LI' in PDS.uncs else zeroes,
                         np.array(PDS.uncs['LT']['stray'][PDS.l1ACommonCalPix255]) / 100 if 'LT' in PDS.uncs else zeroes,
                         np.array(PDS.uncs['ES']['ct'][PDS.l1ACommonCalPix]),
                         np.array( PDS.uncs['LI']['ct'][PDS.l1ACommonCalPix]) if 'LI' in PDS.uncs else zeroes,
                         np.array( PDS.uncs['LT']['ct'][PDS.l1ACommonCalPix]) if 'LT' in PDS.uncs else zeroes,
                         np.array(PDS.uncs['LI']['pol'][PDS.l1ACommonCalPix]) if 'LI' in PDS.uncs else zeroes,
                         np.array( PDS.uncs['LT']['pol'][PDS.l1ACommonCalPix]) if 'LT' in PDS.uncs else zeroes,
                         np.array( PDS.uncs['ES']['cos'][PDS.l1ACommonCalPix]),
        ]

        # generate uncertainties using Monte Carlo Propagation object
        es_unc, li_unc, lt_unc = UNC_obj_CB.propagate_Instrument_Uncertainty(means, uncertainties)

        # NOTE: Debugging check
        # is_negative = np.any([ x < 0 for x in means])
        # if is_negative:
        #     print('WARNING: Negative uncertainty potential')
        is_negative = np.any([ x < 0 for x in uncertainties])
        if is_negative:
            print('WARNING: Potential negative input uncertainties encountered.')
        if any(es_unc < 0) or any(li_unc < 0) or any(lt_unc < 0):
            print('WARNING: Negative output uncertainties encountered in es, li, and/or lt.')

        es, li, lt = UNC_obj_CB.instruments(*means)

        # BD_UNCS, BD_VALS = PlotMaths.classBased(UNC_obj_CB, means, uncertainties, cul=False)  # can set to be cumulative spectral plots
        BD_UNCS, _ = PlotMaths.classBased(UNC_obj_CB, means, uncertainties, cul=False)  # can set to be cumulative spectral plots

        # # check if negative signal for any pixels
        # is_negative = np.any([ x < 0 for x in means])
        # if is_negative:
        #     print('WARNING: Negative uncertainty potential')

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="invalid value encountered in divide")
            warnings.filterwarnings("ignore", message="divide by zero encountered in divide")

            # convert to relative in order to avoid a complex unit conversion process in ProcessL2.
            ES_unc = es_unc / np.abs(es)
            LI_unc = li_unc / np.abs(li)
            LT_unc = lt_unc / np.abs(lt)

            # quad_es = np.sqrt(np.sum([BD_UNCS['ES'][k]**2 for k in BD_UNCS['ES']], axis=0))
            # quad_li = np.sqrt(np.sum([BD_UNCS['LI'][k]**2 for k in BD_UNCS['LI']], axis=0))
            # quad_lt = np.sqrt(np.sum([BD_UNCS['LT'][k]**2 for k in BD_UNCS['LT']], axis=0))

            # pct_diff_es = ((quad_es - es_unc)/es)*100
            # pct_diff_li = ((quad_li - li_unc)/li)*100
            # pct_diff_lt = ((quad_lt - lt_unc)/lt)*100

            # then propagate perturbation uncertainty
            pert_uncs = np.zeros_like(np.asarray(uncertainties))
            pert_uncs[0:6] = [
                np.abs(stats['ES']["Signal_std"][PDS.l1ACommonCalPix]) * stats['ES']['ave_Light'][PDS.l1ACommonCalPix],
                zeroes,
                np.abs(stats['LI']["Signal_std"][PDS.l1ACommonCalPix]) * stats['LI']['ave_Light'][PDS.l1ACommonCalPix] if 'LI' in PDS.uncs else zeroes,
                zeroes,
                np.abs(stats['LT']["Signal_std"][PDS.l1ACommonCalPix]) * stats['LT']['ave_Light'][PDS.l1ACommonCalPix] if 'LT' in PDS.uncs else zeroes,
                zeroes
            ]
            (
                BD_UNCS['ES']['pert'],
                BD_UNCS['LI']['pert'],
                BD_UNCS['LT']['pert'],
            ) = UNC_obj_CB.propagate_Instrument_Uncertainty(means, pert_uncs)

            BD_UNCS['ES'] = {k: BD_UNCS['ES'][k] / np.abs(es) for k in BD_UNCS['ES']}  # convert all to relative units
            BD_UNCS['LI'] = {k: BD_UNCS['LI'][k] / np.abs(li) for k in BD_UNCS['LI']}
            BD_UNCS['LT'] = {k: BD_UNCS['LT'][k] / np.abs(lt) for k in BD_UNCS['LT']}

        # interpolation step - bringing uncertainties to common L2 wavebands from radiometric calibration wavebands.
        l2_wvl = np.asarray(list(stats['ES']['Signal_std_Interpolated'].keys()),
                              dtype=float)

        # NOTE: Uncertainties should all be masked to calibrated, **non-interpolated** L1B wavebands
        rad_cal_str_es = "ES_RADCAL_CAL" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "ES_RADCAL_UNC"
        # The difference between factory approach and class-based:
        cal_col_str_es = "1" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"
        pds_cal_set = PDS.l1ACommonCalPix255 if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else PDS.l1ACommonCalPix255
        out = dict(
            esUnc=utils.interp_common_wvls(ES_unc,
                                           np.array(uncGrp.getDataset(rad_cal_str_es).columns[cal_col_str_es],
                                                       dtype=float)[pds_cal_set],
                                           l2_wvl,
                                           return_as_dict=True
            )
        )
        if 'LI' in stats:
            rad_cal_str_li = "LI_RADCAL_CAL" if "LI_RADCAL_CAL" in uncGrp.datasets.keys() else "LI_RADCAL_UNC"
            cal_col_str_li = "1" if "LI_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"
            out['liUnc']=utils.interp_common_wvls(LI_unc,
                                                  np.array(uncGrp.getDataset(rad_cal_str_li).columns[cal_col_str_li],
                                                           dtype=float)[pds_cal_set],
                                                  l2_wvl,
                                                  return_as_dict=True
            )
        if 'LT' in stats:
            rad_cal_str_lt = "LT_RADCAL_CAL" if "LT_RADCAL_CAL" in uncGrp.datasets.keys() else "LT_RADCAL_UNC"
            cal_col_str_lt = "1" if "LT_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"
            out['ltUnc']=utils.interp_common_wvls(LT_unc,
                                                  np.array(uncGrp.getDataset(rad_cal_str_lt).columns[cal_col_str_lt],
                                                           dtype=float)[pds_cal_set],
                                                  l2_wvl,
                                                  return_as_dict=True
            )


        out['valid_pixels']=PDS.nan_mask # <- PDS.nan_mask not implemented?

        # -- interpolate Breakdowns to common wavebands --
        BD_UNCS['ES'] = {
            k: utils.interp_common_wvls(
                v,
                np.array(uncGrp.getDataset(rad_cal_str_es).columns[cal_col_str_es],
                dtype=float)[pds_cal_set],
                l2_wvl,
                return_as_dict=False
            ) for k,v in BD_UNCS['ES'].items()
        }
        BD_UNCS['LI'] = {
            k: utils.interp_common_wvls(
                v,
                np.array(uncGrp.getDataset(rad_cal_str_li).columns[cal_col_str_li],
                dtype=float)[pds_cal_set],
                l2_wvl,
                return_as_dict=False
            ) for k,v in BD_UNCS['LI'].items()
        }
        BD_UNCS['LT'] = {
            k: utils.interp_common_wvls(
                v,
                np.array(uncGrp.getDataset(rad_cal_str_lt).columns[cal_col_str_lt],
                dtype=float)[pds_cal_set],
                l2_wvl,
                return_as_dict=False
            ) for k,v in BD_UNCS['LT'].items()
        }

        return out, BD_UNCS

    def ClassBasedL2(self, node, uncGrp, PDS, stats, rhoScalar, rhoVec, rhoDelta, f0, f0_unc, waveSubset, xSlice) -> dict:
        """
        Propagates class based uncertainties for all Lw and Rrs. See D-10 section 5.3.1.

        :param node: HDFRoot which stores L1BQC data
        :param uncGrp: HDFGroup storing the uncertainty budget
        :param PDS: PIUDataStore object containing all reported sensor bands for coef and unc, except stray and stab which are 255
        :param stats: dict containing all reported bands except Signal_std_Interpolated
        :param rhoScalar: rho input if Mobley99 or threeC rho is used
        :param rhoVec: rho input if Zhang17 rho is used
        :param rhoDelta: uncertainties associated with rho
        :param waveSubset: wavelength subset for any band convolution (and sizing rhoScalar if used)
        :param xSlice: Dictionary of input radiance, raw_counts, standard deviations etc.
            wavebands in xSlice are all L2 except those keyed "xxSTD_RAW"

        :return: dictionary of output uncertainties that are generated
        """
        try:
            # create object for running uncertainty propagation, M means number of monte carlo draws
            mDraws = 100
            UNC_obj_CB = Propagate(M=mDraws, cores=0)
        except NotImplementedError:
            print("Uncertainties not implemented for TriOS/DALEC/So-rad in Factory Regime")
            return False

        # TODO: shift to using common pixels for all
        l2Wavelength = np.array(waveSubset, dtype=float)  # convert waveSubset to numpy array

        # Try again to use L2 wavelengths and interp stats and pds rather than masking them
        if rhoScalar is not None:  # make rho a constant array if scalar
            rho = np.ones(len(l2Wavelength)) * rhoScalar
        else:
            # rho = rhoVec
            rho = np.asarray(list(rhoVec.values()), dtype=float)
        rhoUNC = np.array(rhoDelta, dtype=float)

        es = np.asarray(list(xSlice['es'].values()), dtype=float).flatten()
        li = np.asarray(list(xSlice['li'].values()), dtype=float).flatten()
        lt = np.asarray(list(xSlice['lt'].values()), dtype=float).flatten()
        f0 = np.asarray(list(f0.values()), dtype=float).flatten()
        f0_unc = np.asarray(list(f0_unc.values()), dtype=float).flatten()
        if ConfigFile.settings['bL2Z17Rho']:
            # May need to truncate to Z17 rho wavebands, depending on how comprehensive the calibration was spectrally
            # L2 data are already at common, interpolated bands, so use Es keys
            fullL2bands = np.array(list(xSlice['es'].keys()),dtype=float)
            es = es[int(np.where(fullL2bands==min(l2Wavelength))[0]):int(np.where(fullL2bands==max(l2Wavelength))[0])+1]
            li = li[int(np.where(fullL2bands==min(l2Wavelength))[0]):int(np.where(fullL2bands==max(l2Wavelength))[0])+1]
            lt = lt[int(np.where(fullL2bands==min(l2Wavelength))[0]):int(np.where(fullL2bands==max(l2Wavelength))[0])+1]
            # f0 = f0[int(np.where(fullL2bands==min(l2Wavelength))[0]):int(np.where(fullL2bands==max(l2Wavelength))[0])+1]
            # f0_unc = f0_unc[int(np.where(fullL2bands==min(l2Wavelength))[0]):int(np.where(fullL2bands==max(l2Wavelength))[0])+1]



        # waveSubset = np.array(waveSubset, dtype=float)  # convert waveSubset to numpy array
        # radcalwvls = list(xSlice['esSTD_RAW'].keys())

        # # stdevs taken at instrument wavebands (not common wavebands) so we can use them to get the radcal keys
        # # interpolate L1B interpolated bands in xSlice to the common set of calibrated pixels - check string for radcal group based on factory or class-based processing
        # rad_cal_str = "ES_RADCAL_CAL" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "ES_RADCAL_UNC"
        # cal_col_str = "1" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"
        # common_pixels_es_wavebands = np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
        #                                       dtype=float)[PDS.l1ACommonCalPix]
        # rad_cal_str = "LI_RADCAL_CAL" if "LI_RADCAL_CAL" in uncGrp.datasets.keys() else "LI_RADCAL_UNC"
        # cal_col_str = "1" if "LI_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"
        # common_pixels_li_wavebands = np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
        #                                       dtype=float)[PDS.l1ACommonCalPix]
        # rad_cal_str = "LT_RADCAL_CAL" if "LT_RADCAL_CAL" in uncGrp.datasets.keys() else "LT_RADCAL_UNC"
        # cal_col_str = "1" if "LT_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"
        # common_pixels_lt_wavebands = np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
        #                                       dtype=float)[PDS.l1ACommonCalPix]
        # # Unlike interpolation of L2 es, li, and lt, interpolation of rho is arbitrarily to es common bands
        # if rhoScalar is not None:  # make rho a vector constant array if scalar
        #     rho = np.ones(len(common_pixels_es_wavebands)) * rhoScalar
        #     rhoUNC = utils.interp_common_wvls(np.array(rhoDelta, dtype=float),
        #                                      l2Wavelength,
        #                                      common_pixels_es_wavebands,
        #                                      return_as_dict=False)
        # else:  # zhang rho needs to be interpolated to common bands
        #     rho = utils.interp_common_wvls(np.array(list(rhoVec.values()), dtype=float),
        #                                   l2Wavelength,
        #                                   common_pixels_es_wavebands,
        #                                   return_as_dict=False)
        #     rhoUNC = utils.interp_common_wvls(rhoDelta,
        #                                      l2Wavelength,
        #                                      common_pixels_es_wavebands,
        #                                      return_as_dict=False)

        # # Data from xSlice cannot be subset using the masks in PDS since they were interpolated in L1BInterp. Therefore,
        # #   must be interpolated back to their original pixels based on a common set of pixels across all instruments.
        # #   Wavelengths from these pixels for Es are used here, but irrelevant as long as they are in common and match pixels
        # #   in PDS and stats.
        # es = utils.interp_common_wvls(np.asarray(list(xSlice['es'].values()), dtype=float).flatten(),
        #                              np.asarray(list(xSlice['es'].keys()), dtype=float).flatten(),
        #                              common_pixels_es_wavebands,
        #                              return_as_dict=False)
        # li = utils.interp_common_wvls(np.asarray(list(xSlice['li'].values()), dtype=float).flatten(),
        #                              np.asarray(list(xSlice['li'].keys()), dtype=float).flatten(),
        #                              common_pixels_es_wavebands,
        #                              return_as_dict=False)
        # lt = utils.interp_common_wvls(np.asarray(list(xSlice['lt'].values()), dtype=float).flatten(),
        #                              np.asarray(list(xSlice['lt'].keys()), dtype=float).flatten(),
        #                              common_pixels_es_wavebands,
        #                              return_as_dict=False)
        # f0 = utils.interp_common_wvls(np.asarray(list(f0.values()), dtype=float).flatten(),
        #                              np.asarray(list(f0.keys()), dtype=float).flatten(),
        #                              common_pixels_es_wavebands,
        #                              return_as_dict=False)
        # f0_unc = utils.interp_common_wvls(np.asarray(list(f0_unc.values()), dtype=float).flatten(),
        #                              np.asarray(list(f0_unc.keys()), dtype=float).flatten(),
        #                              common_pixels_es_wavebands,
        #                              return_as_dict=False)
        # if rhoScalar is not None:  # make rho a vector constant array if scalar
        #     rho = np.ones(len(radcalwvls)) * rhoScalar
        #     rhoUNC = utils.interp_common_wvls(np.array(rhoDelta, dtype=float),
        #                                      waveSubset,
        #                                      np.asarray(radcalwvls, dtype=float),
        #                                      return_as_dict=False)
        # else:  # zhang rho needs to be interpolated to common bands
        #     rho = utils.interp_common_wvls(np.array(list(rhoVec.values()), dtype=float),
        #                                   waveSubset,
        #                                   np.asarray(radcalwvls, dtype=float),
        #                                   return_as_dict=False)
        #     rhoUNC = utils.interp_common_wvls(rhoDelta,
        #                                      waveSubset,
        #                                      np.asarray(radcalwvls, dtype=float),
        #                                      return_as_dict=False)


        # es = utils.interp_common_wvls(np.asarray(list(xSlice['es'].values()), dtype=float).flatten(),
        #                              np.asarray(list(xSlice['es'].keys()), dtype=float).flatten(),
        #                              np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
        #                                       dtype=float)[PDS.l1ACommonCalPix],
        #                              return_as_dict=False)
        # li = utils.interp_common_wvls(np.asarray(list(xSlice['li'].values()), dtype=float).flatten(),
        #                              np.asarray(list(xSlice['li'].keys()), dtype=float).flatten(),
        #                              np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
        #                                       dtype=float)[PDS.l1ACommonCalPix],
        #                              return_as_dict=False)
        # lt = utils.interp_common_wvls(np.asarray(list(xSlice['lt'].values()), dtype=float).flatten(),
        #                              np.asarray(list(xSlice['lt'].keys()), dtype=float).flatten(),
        #                              np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
        #                                       dtype=float)[PDS.l1ACommonCalPix],
        #                              return_as_dict=False)
        # f0 = utils.interp_common_wvls(np.asarray(list(f0.values()), dtype=float).flatten(),
        #                              np.asarray(list(f0.keys()), dtype=float).flatten(),
        #                              np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
        #                                       dtype=float)[PDS.l1ACommonCalPix],
        #                              return_as_dict=False)
        # f0_unc = utils.interp_common_wvls(np.asarray(list(f0_unc.values()), dtype=float).flatten(),
        #                              np.asarray(list(f0_unc.keys()), dtype=float).flatten(),
        #                              np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
        #                                       dtype=float)[PDS.l1ACommonCalPix],
        #                              return_as_dict=False)

        ones = np.ones_like(es)

        # These are all at a common set of bands from raw ES at the common set of calibrated pixels
        lw_means = [lt, rho, li,
                    ones, ones,
                    ones, ones,
                    ones, ones,
                    ones, ones,
                    ones, ones,
                    ones, ones
                    ]

        # # Some PDS elements are at the reported/output bands, some at the full 255 pixels. Use masks accordingly.
        # #   These are all at common pixels, regardless of the wavelength.
        # lw_uncertainties = [ np.abs(np.array(list(stats['LT']['Signal_noise'].values())).flatten()[PDS.l1ACommonCalPix] * lt),
        #                     rhoUNC,
        #                     np.abs(np.array(list(stats['LI']['Signal_noise'].values())).flatten()[PDS.l1ACommonCalPix] * li),
        #                     PDS.uncs['LI']['cal'][PDS.l1ACommonCalPix] / 200,
        #                     PDS.uncs['LT']['cal'][PDS.l1ACommonCalPix] / 200,
        #                     PDS.uncs['LI']['stab'][PDS.l1ACommonCalPix255],
        #                     PDS.uncs['LT']['stab'][PDS.l1ACommonCalPix255],
        #                     PDS.uncs['LI']['nlin'][PDS.l1ACommonCalPix],
        #                     PDS.uncs['LT']['nlin'][PDS.l1ACommonCalPix],
        #                     PDS.uncs['LI']['stray'][PDS.l1ACommonCalPix255] / 100,
        #                     PDS.uncs['LI']['stray'][PDS.l1ACommonCalPix255] / 100,
        #                     PDS.uncs['LI']['ct'][PDS.l1ACommonCalPix],
        #                     PDS.uncs['LI']['ct'][PDS.l1ACommonCalPix],
        #                     PDS.uncs['LI']['pol'][PDS.l1ACommonCalPix],
        #                     PDS.uncs['LI']['pol'][PDS.l1ACommonCalPix]
        #                     ]

        # TODO: try interpolating the necesary PDS and stats elements to L2 bands rather than changing PDS

        statsL2 = {}
        sensors = ['ES','LI','LT']
        for sensor in sensors:
            params = ['Signal_noise','Signal_std']
            for param in params:
                key = f'{sensor}{param}'
                if param == 'Signal_noise':
                # Signal_noise is the only dict with wave keys
                    statsL2[key] = utils.interp_common_wvls( np.array(list(stats[sensor][param].values())).flatten(),
                                        np.asarray(list(stats[sensor]['Signal_noise'].keys()), dtype=float).flatten(),
                                        l2Wavelength,
                                        return_as_dict=False)
                else:
                    statsL2[key] = utils.interp_common_wvls(stats[sensor][param],
                                        np.asarray(list(stats[sensor]['Signal_noise'].keys()), dtype=float).flatten(),
                                        l2Wavelength,
                                        return_as_dict=False)

        # esNoise = utils.interp_common_wvls( np.array(list(stats['ES']['Signal_noise'].values())).flatten(),
        #                              np.asarray(list(stats['ES']['Signal_noise'].keys()), dtype=float).flatten(),
        #                              l2Wavelength,
        #                              return_as_dict=False)
        # ltNoise = utils.interp_common_wvls( np.array(list(stats['LT']['Signal_noise'].values())).flatten(),
        #                              np.asarray(list(stats['LT']['Signal_noise'].keys()), dtype=float).flatten(),
        #                              l2Wavelength,
        #                              return_as_dict=False)
        # liNoise = utils.interp_common_wvls( np.array(list(stats['LI']['Signal_noise'].values())).flatten(),
        #                              np.asarray(list(stats['LI']['Signal_noise'].keys()), dtype=float).flatten(),
        #                              l2Wavelength,
        #                              return_as_dict=False)
        PDSL2 = {}
        for sensor in sensors:
            params = ['cal','nlin','ct']
            if sensor in ['LI','LT']:
                params.append('pol')
            if sensor == 'ES':
                params.append('cos')
            for param in params:
                key = f'{sensor}{param}'
                PDSL2[key] = utils.interp_common_wvls( PDS.uncs[sensor][param],
                                        PDS.wvl[sensor],
                                        l2Wavelength,
                                        return_as_dict=False)
            params = ['stray','stab'] # Contain 255 pixels. PDS.wvl only has recorded bands, but the mask is otherwise the same.
            for param in params:
                key = f'{sensor}{param}'
                PDSL2[key] = utils.interp_common_wvls( PDS.uncs[sensor][param][PDS.l1ACommonCalPix255],
                                         PDS.wvl[sensor][PDS.l1ACommonCalPix],
                                         l2Wavelength,
                                         return_as_dict=False)

        # Some PDS elements are at the reported/output bands, some at the full 255 pixels. Use masks accordingly.
        #   These are all at common pixels, regardless of the wavelength.
        lw_uncertainties = [ np.abs(statsL2['LTSignal_noise'] * lt),
                            rhoUNC,
                            np.abs(statsL2['LISignal_noise'] * li),
                            PDSL2['LIcal'] / 200,
                            PDSL2['LTcal'] / 200,
                            PDSL2['LIstab'],
                            PDSL2['LTstab'],
                            PDSL2['LInlin'],
                            PDSL2['LTnlin'],
                            PDSL2['LIstray'] / 100,
                            PDSL2['LIstray'] / 100,
                            PDSL2['LIct'],
                            PDSL2['LIct'],
                            PDSL2['LIpol'],
                            PDSL2['LIpol']
                            ]

        lwAbsUnc = UNC_obj_CB.Propagate_Lw_HYPER(lw_means, lw_uncertainties)

        rrs_means = [lt, rho, li, es,
                     ones, ones, ones,
                     ones, ones, ones,
                     ones, ones, ones,
                     ones, ones, ones,
                     ones, ones, ones,
                     ones, ones, ones
                     ]

        # rrs_uncertainties = [np.abs(np.array(list(stats['LT']['Signal_noise'].values())).flatten()[PDS.l1ACommonCalPix] * lt),
        #                      rhoUNC,
        #                      np.abs(np.array(list(stats['LI']['Signal_noise'].values())).flatten()[PDS.l1ACommonCalPix] * li),
        #                      np.abs(np.array(list(stats['ES']['Signal_noise'].values())).flatten()[PDS.l1ACommonCalPix] * es),
        #                      PDS.uncs['ES']['cal'][PDS.l1ACommonCalPix] / 200,
        #                      PDS.uncs['LI']['cal'][PDS.l1ACommonCalPix] / 200,
        #                      PDS.uncs['LT']['cal'][PDS.l1ACommonCalPix] / 200,
        #                      PDS.uncs['ES']['stab'][PDS.l1ACommonCalPix255],
        #                      PDS.uncs['LI']['stab'][PDS.l1ACommonCalPix255],
        #                      PDS.uncs['LT']['stab'][PDS.l1ACommonCalPix255],
        #                      PDS.uncs['ES']['nlin'][PDS.l1ACommonCalPix],
        #                      PDS.uncs['LI']['nlin'][PDS.l1ACommonCalPix],
        #                      PDS.uncs['LT']['nlin'][PDS.l1ACommonCalPix],
        #                      PDS.uncs['ES']['stray'][PDS.l1ACommonCalPix255] / 100,
        #                      PDS.uncs['LI']['stray'][PDS.l1ACommonCalPix255] / 100,
        #                      PDS.uncs['LT']['stray'][PDS.l1ACommonCalPix255] / 100,
        #                      PDS.uncs['ES']['ct'][PDS.l1ACommonCalPix],
        #                      PDS.uncs['LI']['ct'][PDS.l1ACommonCalPix],
        #                      PDS.uncs['LT']['ct'][PDS.l1ACommonCalPix],
        #                      PDS.uncs['LI']['pol'][PDS.l1ACommonCalPix],
        #                      PDS.uncs['LT']['pol'][PDS.l1ACommonCalPix],
        #                      PDS.uncs['ES']['cos'][PDS.l1ACommonCalPix]
        #                      ]
        rrs_uncertainties = [np.abs(statsL2['LTSignal_noise'] * lt),
                             rhoUNC,
                             np.abs(statsL2['LISignal_noise'] * li),
                             np.abs(statsL2['ESSignal_noise'] * es),
                             PDSL2['EScal'] / 200,
                             PDSL2['LIcal'] / 200,
                             PDSL2['LTcal'] / 200,
                             PDSL2['ESstab'],
                             PDSL2['LIstab'],
                             PDSL2['LTstab'],
                             PDSL2['ESnlin'],
                             PDSL2['LInlin'],
                             PDSL2['LTnlin'],
                             PDSL2['ESstray'] / 100,
                             PDSL2['LIstray'] / 100,
                             PDSL2['LTstray'] / 100,
                             PDSL2['ESct'],
                             PDSL2['LIct'],
                             PDSL2['LTct'],
                             PDSL2['LIpol'],
                             PDSL2['LTpol'],
                             PDSL2['EScos']
                             ]

        rrsAbsUnc = UNC_obj_CB.Propagate_RRS_HYPER(rrs_means, rrs_uncertainties)

        BD_UNCS, BD_VALS = PlotMaths.classBasedL2(UNC_obj_CB, lw_means, rrs_means, lw_uncertainties, rrs_uncertainties, cul=False)

        # then propagate perturbation uncertainty
        zeroes = np.zeros_like(ones)
        pert_uncs = np.zeros_like(np.asarray(lw_uncertainties))
        # pert_uncs[0:3] = [
        #     np.abs(stats['LT']["Signal_std"][PDS.l1ACommonCalPix]) * np.abs(lt) if 'LT' in PDS.uncs else zeroes,
        #     zeroes,
        #     np.abs(stats['LI']["Signal_std"][PDS.l1ACommonCalPix]) * np.abs(li) if 'LI' in PDS.uncs else zeroes,
        # ]
        pert_uncs[0:3] = [
            np.abs(statsL2['LTSignal_std']) * np.abs(lt) if 'LT' in PDS.uncs else zeroes,
            zeroes,
            np.abs(statsL2['LISignal_std']) * np.abs(li) if 'LI' in PDS.uncs else zeroes,
        ]

        BD_UNCS['Lw']['pert'] = UNC_obj_CB.Propagate_Lw_HYPER(lw_means, pert_uncs)
        lw = UNC_obj_CB.Lw(*lw_means)

        pert_uncs = np.zeros_like(np.asarray(rrs_uncertainties))
        # pert_uncs[0:4] = [
        #     np.abs(stats['LT']["Signal_std"][PDS.l1ACommonCalPix]) * np.abs(lt) if 'LT' in PDS.uncs else zeroes,
        #     np.zeros_like(ones),
        #     np.abs(stats['LI']["Signal_std"][PDS.l1ACommonCalPix]) * np.abs(li) if 'LI' in PDS.uncs else zeroes,
        #     np.abs(stats['ES']["Signal_std"][PDS.l1ACommonCalPix]) * np.abs(es),
        # ]
        pert_uncs[0:4] = [
            np.abs(statsL2['LTSignal_std']) * np.abs(lt) if 'LT' in PDS.uncs else zeroes,
            np.zeros_like(ones),
            np.abs(statsL2['LISignal_std']) * np.abs(li) if 'LI' in PDS.uncs else zeroes,
            np.abs(statsL2['ESSignal_std']) * np.abs(es),
        ]

        BD_UNCS['Rrs']['pert'] = UNC_obj_CB.Propagate_RRS_HYPER(rrs_means, pert_uncs)
        rrs = UNC_obj_CB.RRS(*rrs_means)

        sample_f0 = cm.generate_sample(mDraws, f0,  f0_unc, "syst")
        no_unc_f0  = cm.generate_sample(mDraws, f0,  None,   None)
        no_unc_rrs = cm.generate_sample(mDraws, BD_VALS['Rrs'], None,   None)

        BD_UNCS['nLw'] = {}
        for k in BD_UNCS['Rrs'].keys():
            if k.lower() == 'pert' or k.lower() == 'noise':
                sample_bd_rrs = cm.generate_sample(mDraws, BD_VALS['Rrs'], np.abs(BD_UNCS['Rrs'][k]), "rand")  # noise is a random uncertainy
            else:
                sample_bd_rrs = cm.generate_sample(mDraws, BD_VALS['Rrs'], np.abs(BD_UNCS['Rrs'][k]), "syst")  # all others considered systematic
            BD_UNCS['nLw'][k] = UNC_obj_CB.MCP.process_samples(
                None,
                UNC_obj_CB.MCP.run_samples(UNC_obj_CB.nLw_FRM, [sample_bd_rrs, no_unc_f0])
                )
        BD_UNCS['nLw']['f0']  = UNC_obj_CB.MCP.process_samples(
                None,
                UNC_obj_CB.MCP.run_samples(UNC_obj_CB.nLw_FRM, [no_unc_rrs, sample_f0])
                )

        # NOTE: uncertainty outputs are already at common L2 bands
        # # these are absolute values!
        # rhoUNC_CWB = utils.interp_common_wvls(
        #     rhoUNC,
        #     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[PDS.ind_rad_wvl['ES']],
        #     waveSubset,
        #     return_as_dict=False
        # )
        # # lwAbsUnc[PDS.nan_mask] = np.nan
        # lwAbsUnc = utils.interp_common_wvls(
        #     lwAbsUnc,
        #     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[PDS.ind_rad_wvl['ES']],
        #     waveSubset,
        #     return_as_dict=False
        # )
        # nlwAbsUnc = utils.interp_common_wvls(
        #     np.sqrt((rrsAbsUnc**2 * f0**2) +
        #     (BD_VALS['Rrs']**2 * f0_unc**2)),
        #     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[PDS.ind_rad_wvl['ES']],
        #     waveSubset,
        #     return_as_dict=False
        # )
        # # rrsAbsUnc[PDS.nan_mask] = np.nan
        # rrsAbsUnc = utils.interp_common_wvls(
        #     rrsAbsUnc,
        #     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[PDS.ind_rad_wvl['ES']],
        #     waveSubset,
        #     return_as_dict=False
        # )

        nlwAbsUnc = np.sqrt((rrsAbsUnc**2 * f0**2) + (BD_VALS['Rrs']**2 * f0_unc**2))        

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

        UNC = {}  # output uncertainties to ProcessL2

        ## Update the output dictionary with band L2 hyperspectral and satellite band uncertainties
        for s_key in self._SATELLITES.keys():
            UNC.update(
                self.get_band_outputs(
                    s_key, rho, lw_means, lw_uncertainties, rrs_means, rrs_uncertainties,
                    esUNC_band, liUNC_band, ltUNC_band, rhoUNC, l2Wavelength, xSlice
                )
            )
        UNC.update(
            {"rhoUNC_HYPER": {str(k): val for k, val in zip(l2Wavelength, rhoUNC)},
            "lwUNC": lwAbsUnc,
             "rrsUNC": rrsAbsUnc,
             "nlwUNC": nlwAbsUnc}
        )

        return UNC, BD_UNCS


    def ClassBasedL2ESOnly(self, waveSubset: np.array, xSlice) -> dict:
        """
        Sames as ClassBasedL2 except only process Es signal, which results in band convolution of Es uncertainties only.

        :param waveSubset: wavelength subset for any band convolution (and sizing rhoScalar if used)
        :param xSlice: Dictionary of input radiance, raw_counts, standard deviations etc.
        :return: dictionary of output uncertainties that are generated
        """

        ## Band Convolution of Uncertainties
        # get unc values at common wavebands (from ProcessL2) and convert any NaNs to 0 to not create issues with punpy
        esUNC_band = np.array([i[0] for i in xSlice['esUnc'].values()])

        # Prune the uncertainties to remove NaNs and negative values (uncertainties which make no physical sense)
        esUNC_band[np.isnan(esUNC_band)] = 0.0
        esUNC_band = np.abs(esUNC_band)  # uncertainties may have negative values after conversion to relative units

        ## Update the output dictionary with band L2 hyperspectral and satellite band uncertainties
        UNC = {}
        for sensor_key in self._SATELLITES.keys():
            # Given that only one parameter simplified function self.get_band_outputs below
            if ConfigFile.settings[self._SATELLITES[sensor_key]['config']]:
                sensor_name = self._SATELLITES[sensor_key]['name']
                RSR_Bands = self._SATELLITES[sensor_key]['Weight_RSR']
                prop_Band_CB = Propagate(M=100, cores=1)  # propagate band convolved uncertainties class based
                esDeltaBand = prop_Band_CB.band_Conv_Uncertainty(
                    [np.asarray(list(xSlice['es'].values()), dtype=float).flatten(), waveSubset],
                    [esUNC_band, None],
                    sensor_key
                    # used to choose correct band convolution measurement function in uncertainty_analysis.py
                )
                UNC[f"esUNC_{sensor_name}"] = {
                    str(k): [val] for k, val in zip(RSR_Bands, esDeltaBand)
                }

        return UNC


    @abstractmethod
    def FRM(self, PDS: pds, stats: dict, newWaveBands: np.array) -> dict[str, np.array]:
        """
        Propagates instrument uncertainties with corrections (except polarisation/stability) if full characterisation available - see D-10 section 5.3.1
        
        :param node: HDFRoot of L1BQC data for processing
        :param uncGrp: HDFGroup of uncertainty budget
        :param raw_grps: dictionary of raw data groups
        :param raw_slices: dictionary of sliced data for specific sensors
        :param stats: standard deviation and averages for Light, Dark and Light-Dark signal
        :param newWaveBands: wavelength subset for interpolation

        :return: output FRM uncertainties
        """
        pass

    def FRML2(self, PDS: pds, rhoScalar: float, rhoVec: np.array, rhoDelta: np.array, waveSubset: np.array,
               xSlice: dict[str, np.array], BD_UNCS: dict[str: np.array]) -> dict[str, np.array]:
        """
        Propagates Lw and Rrs uncertainties if full characterisation available - see D-10 5.3.1

        :param rhoScalar: rho input if Mobley99 or threeC rho is used
        :param rhoVec: rho input if Zhang17 rho is used
        :param rhoDelta: uncertainties associated with rho
        :param waveSubset: wavelength subset for any band convolution (and sizing rhoScalar if used)
        :param xSlice: Dictionary of input radiance, raw_counts, standard deviations etc.

        :return: dictionary of output uncertainties that are generated

        """

        from Source.PIU.Breakdown_FRM import SolveLPU
        LPU = SolveLPU()

        BD_UNCS_common_wb = {'ES': {}, 'LI': {}, 'LT': {}}
        for s in BD_UNCS.keys():  # Breakdown uncs must be interpolated to common wavebands to apply to Lw and Rrs
            for k in BD_UNCS[s].keys():  # use interp method from PIUDataStore - method is static so no instance required
                BD_UNCS_common_wb[s][k] = pds.interp_common_wvls(
                    BD_UNCS[s][k],
                    PDS.coeff[s]["radcal_wvl"],
                    np.array(waveSubset),
                    return_as_dict=False  # return as numpy array
                )

        BD_UNCS.update({k: {} for k in ['nLw', 'Lw', 'Rrs', 'rho']})

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

        BD_UNCS['rho']['rho_unc'] = np.array(rhoDelta)

        # initialise punpy propagation object
        mdraws = esSampleXSlice.shape[0]  # keep no. of monte carlo draws consistent
        UNC_Obj_FRM = Propagate(mdraws, cores=1)  # punpy.MCPropagation(mdraws, parallel_cores=1)

        # get sample for rho
        sample_rho = cm.generate_sample(mdraws, rho, rhoDelta, "syst")

        # initialise lists to store uncertainties per replicate
        sample_ES = np.asarray([[i[0] for i in k.values()] for k in esSampleXSlice])  # recover original shape of samples
        sample_LI = np.asarray([[i[0] for i in k.values()] for k in liSampleXSlice])
        sample_LT = np.asarray([[i[0] for i in k.values()] for k in ltSampleXSlice])
        f0 = np.array(list(xSlice['f0'].values()))
        f0_unc = np.array(list(xSlice['f0_unc'].values()))
        sample_f0 = cm.generate_sample(mdraws, np.array(f0), np.array(f0_unc), "syst")

        # no uncertainty in wavelengths
        sample_wavelengths = cm.generate_sample(mdraws, np.array(waveSubset), None, None)
        sample_Lw  = UNC_Obj_FRM.MCP.run_samples(Propagate.Lw_FRM,  [sample_LT, sample_rho, sample_LI])
        sample_Rrs = UNC_Obj_FRM.MCP.run_samples(Propagate.Rrs_FRM, [sample_LT, sample_rho, sample_LI, sample_ES])
        sample_nLw = UNC_Obj_FRM.MCP.run_samples(Propagate.nLw_FRM, [sample_Rrs, sample_f0])

        LPU.waterLeaving(BD_UNCS_common_wb, BD_UNCS, np.mean(sample_LI, axis=0), rho)
        LPU.reflectance(
            BD_UNCS_common_wb, 
            BD_UNCS, 
            np.mean(sample_ES, axis=0), 
            np.mean(sample_LI, axis=0), 
            np.mean(sample_LT, axis=0),
            rho
        )
        LPU.normalised_waterLeaving(BD_UNCS, np.mean(sample_Rrs, axis=0), f0, f0_unc)

        del BD_UNCS_common_wb  # no longer needed

        UNCS = {}  # output uncertainties

        # do band convolution if selected
        for s_key in self._SATELLITES.keys():
            UNCS.update(
                self.get_band_outputs_FRM(
                s_key, UNC_Obj_FRM, sample_ES, sample_LI, sample_LT, sample_rho, sample_f0, sample_wavelengths
                )
            )

        lwDelta  = UNC_Obj_FRM.MCP.process_samples(None, sample_Lw)
        rrsDelta = UNC_Obj_FRM.MCP.process_samples(None, sample_Rrs)
        nlwDelta = UNC_Obj_FRM.MCP.process_samples(None, sample_nLw)

        UNCS["rhoUNC_HYPER"] = {str(wvl): val for wvl, val in zip(waveSubset, rhoDelta)}
        UNCS["lwUNC"]  = lwDelta  # Multiply by large number to reduce round off error
        UNCS["rrsUNC"] = rrsDelta
        UNCS["nlwUNC"] = nlwDelta

        return UNCS

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

    def get_band_outputs_FRM(self, sensor_key, MCP_obj, esSample, liSample, ltSample, rhoSample, f0_sample, sample_wavelengths
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
            sample_f0_conv  = MCP_obj.MCP.run_samples(MCP_obj.def_sensor_mfunc(sensor_key), [f0_sample, sample_wavelengths])

            esDeltaBand = MCP_obj.MCP.process_samples(None, sample_es_conv)
            liDeltaBand = MCP_obj.MCP.process_samples(None, sample_li_conv)
            ltDeltaBand = MCP_obj.MCP.process_samples(None, sample_lt_conv)

            rhoDeltaBand = MCP_obj.MCP.process_samples(None, sample_rho_conv)

            sample_lw_conv  = MCP_obj.MCP.run_samples(MCP_obj.Lw_FRM, [sample_lt_conv, sample_rho_conv, sample_li_conv])
            sample_rrs_conv = MCP_obj.MCP.run_samples(MCP_obj.Rrs_FRM, [sample_lt_conv, sample_rho_conv, sample_li_conv, sample_es_conv])
            sample_nlw_conv = MCP_obj.MCP.run_samples(MCP_obj.nLw_FRM, [sample_rrs_conv, sample_f0_conv])

            # put in expected format (converted from punpy conpatible outputs) and put in output dictionary which will
            # be returned to ProcessingL2 and used to update xSlice/xUNC
            Band_Convolved_UNC[f"esUNC_{sensor_name}"]  = {str(k): [val] for k, val in zip(RSR_Bands, esDeltaBand)}
            Band_Convolved_UNC[f"liUNC_{sensor_name}"]  = {str(k): [val] for k, val in zip(RSR_Bands, liDeltaBand)}
            Band_Convolved_UNC[f"ltUNC_{sensor_name}"]  = {str(k): [val] for k, val in zip(RSR_Bands, ltDeltaBand)}
            Band_Convolved_UNC[f"rhoUNC_{sensor_name}"] = {str(k): [val] for k, val in zip(RSR_Bands, rhoDeltaBand)}
            # L2 uncertainty products can be reported as np arrays
            Band_Convolved_UNC[f"lwUNC_{sensor_name}"]  = MCP_obj.MCP.process_samples(None, sample_lw_conv)
            Band_Convolved_UNC[f"rrsUNC_{sensor_name}"] = MCP_obj.MCP.process_samples(None, sample_rrs_conv)
            Band_Convolved_UNC[f"nlwUNC_{sensor_name}"] = MCP_obj.MCP.process_samples(None, sample_nlw_conv)

            return Band_Convolved_UNC
        else:
            return {}

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
        from Source.PIU.MeasurementFunctions import MeasurementFunctions as mf
        sl_corr = mf.Slaper_SL_correction(data, mZ, n_iter)
        sl_corr_unc = []
        sl4 = mf.Slaper_SL_correction(data, mZ, n_iter=n_iter - 1)
        for i in range(len(sl_corr)):  # get the difference between n=4 and n=5
            if sl_corr[i] > sl4[i]:
                sl_corr_unc.append(sl_corr[i] - sl4[i])
            else:
                sl_corr_unc.append(sl4[i] - sl_corr[i])

        sample_sl_syst = cm.generate_sample(mDraws, sl_corr, np.array(sl_corr_unc), "syst")
        sample_sl_rand = MC_prop.run_samples(self.Slaper_SL_correction, [sample_data, sample_mZ, sample_n_iter])
        sample_sl_corr = MC_prop.combine_samples([sample_sl_syst, sample_sl_rand])

        return sample_sl_corr

    def gen_n_IB_sample(self, mDraws):
        # make your own sample here min is 3, max is 6 - all values must be integer
        import random as rand
        # seed random number generator with current systime (default behaviour of rand.seed)
        rand.seed(a=None, version=2)
        sample_n_IB = []
        for i in range(mDraws):
            sample_n_IB.append(rand.randrange(3, 7, 1))  # sample_n_IB max should be 6
        return np.asarray(sample_n_IB)  # make numpy array to be compatible with comet maths
