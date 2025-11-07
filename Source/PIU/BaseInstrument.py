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
        warnings.filterwarnings("ignore", message="One of the provided covariance matrix is not positivedefinite. It has been slightly changed")

    ## Regime Agnostic Methods ##

    @abstractmethod
    def lightDarkStats(self, grp: Union[HDFGroup, dict[str: HDFGroup]], XSlice: dict, sensortype: str) -> dict[str: np.array]:
        pass

    def generateSensorStats(self, i_type: str, rawData: dict, rawSlice: dict, newWaveBands: np.array) -> dict[str: np.array]:
        """
        Generate Sensor Stats calls lightDarkStats for a given instrument. Once sensor statistics are known, they are 
        interpolated to common wavebands to match the other L1B sensor inputs Es, Li, & Lt.

        :return: dictionary of statistics used later in the processing pipeline. Keys are:
        [ave_Light, ave_Dark, std_Light, std_Dark, std_Signal]
        """
        stats = {}  # used tp store standard deviations and averages as a function return for generateSensorStats
        for s_type in self.sensors:
            # filter nans
            from Source.PIU.utils import utils

            if i_type.lower() in ["sorad", "trios", "trios es only"]:
                    utils.apply_NaN_Mask(rawSlice[s_type]['data'])  # apply Nan mask
                    args = [copy.deepcopy(rawData[s_type]), copy.deepcopy(rawSlice[s_type]), s_type]  
                    # copy.deepcopy ensures RAW data is unchanged for FRM uncertainty generation.
            elif i_type.lower() == "dalec":
                    # NOTE: Needs updating
                    utils.apply_NaN_Mask(rawSlice[s_type]['data'])  # apply Nan mask
                    args = [copy.deepcopy(rawData[s_type]), copy.deepcopy(rawSlice[s_type]), s_type]    
            elif i_type.lower() == "seabird":
                    utils.apply_NaN_Mask(rawSlice[s_type]['LIGHT']['data'])  # how closely should light follow dark, i.e. do we mask light with dark and vice versa - Ashley
                    utils.apply_NaN_Mask(rawSlice[s_type]['DARK']['data'])
                    args =[
                        {'LIGHT': rawData[s_type]['LIGHT'], 'DARK': rawData[s_type]['DARK']},
                        {'LIGHT': rawSlice[s_type]['LIGHT'], 'DARK': rawSlice[s_type]['DARK']},
                        s_type
                        ]
            else:
                writeLogFileAndPrint("WARNING sensor not recognised")
            try:
                stats[s_type] = self.lightDarkStats(*args)
            except (ValueError, IndexError, KeyError):
                writeLogFileAndPrint("Could not generate statistics for the ensemble")
                return False

        # interpolate std Signal to common wavebands - taken from L2 ES group: ProcessL2.py L1352
        
        try:
            for s_type in self.sensors:
                stats[s_type]['std_Signal_Interpolated'] = utils.interp_common_wvls(
                    stats[s_type]['std_Signal'],
                    np.asarray(list(stats[s_type]['std_Signal'].keys()), dtype=float),
                    newWaveBands,
                    return_as_dict=True)
            
            return stats
            
        except (IndexError, TypeError) as err:
            writeLogFileAndPrint(f"Unable to parse statistics with for the ensemble: {err}. (possibly too few scans).")
            return False

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

        try:
            # create object for running uncertainty propagation, M means number of monte carlo draws
            UNC_obj_CB = Propagate(M=100, cores=0)
            PDS = pds(node, uncGrp)
        except NotImplementedError:
             print("Uncertainties not implemented for TriOS/DALEC/So-rad in Factory Regime")
             return False, None

        ones = np.ones_like(PDS.uncs['ES']['cal'])  # array of ones with correct shape.
        zeroes = np.zeros_like(PDS.uncs['ES']['cal']) 

        means = [stats['ES']['ave_Light'], stats['ES']['ave_Dark'],
                 stats['LI']['ave_Light'] if 'LI' in stats else ones, stats['LI']['ave_Dark'] if 'LI' in stats else ones,
                 stats['LT']['ave_Light'] if 'LT' in stats else ones, stats['LT']['ave_Dark'] if 'LT' in stats else ones,
                 PDS.coeff['ES']['cal'], PDS.coeff['LI']['cal'] if 'LI' in PDS.coeff else ones, PDS.coeff['LT']['cal'] if 'LT' in PDS.coeff else ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones
                 ]

        uncertainties = [stats['ES']['std_Light'], stats['ES']['std_Dark'],
                         stats['LI']['std_Light'] if 'LI' in stats else zeroes, stats['LI']['std_Dark'] if 'LI' in stats else zeroes,
                         stats['LT']['std_Light'] if 'LT' in stats else zeroes, stats['LT']['std_Dark'] if 'LT' in stats else zeroes,
                         PDS.uncs['ES']['cal'] * PDS.coeff['ES']['cal'] / 200,
                         PDS.uncs['LI']['cal'] * PDS.coeff['LI']['cal'] / 200 if 'LI' in PDS.uncs else zeroes,
                         PDS.uncs['LT']['cal'] * PDS.coeff['LT']['cal'] / 200 if 'LT' in PDS.uncs else zeroes,
                         PDS.uncs['ES']['stab'], PDS.uncs['LI']['stab'] if 'LI' in PDS.uncs else zeroes, PDS.uncs['LT']['stab'] if 'LT' in PDS.uncs else zeroes,
                         PDS.uncs['ES']['nlin'], PDS.uncs['LI']['nlin'] if 'LI' in PDS.uncs else zeroes, PDS.uncs['LT']['nlin'] if 'LT' in PDS.uncs else zeroes,
                         np.array(PDS.uncs['ES']['stray']) / 100,  # change straylight and set nl uncs with file
                         np.array(PDS.uncs['LI']['stray']) / 100 if 'LI' in PDS.uncs else zeroes,
                         np.array(PDS.uncs['LT']['stray']) / 100 if 'LT' in PDS.uncs else zeroes,
                         np.array(PDS.uncs['ES']['ct']), np.array( PDS.uncs['LI']['ct']) if 'LI' in PDS.uncs else zeroes, np.array( PDS.uncs['LT']['ct']) if 'LT' in PDS.uncs else zeroes,
                         np.array(PDS.uncs['LI']['pol']) if 'LI' in PDS.uncs else zeroes, np.array( PDS.uncs['LT']['pol']) if 'LT' in PDS.uncs else zeroes, np.array( PDS.uncs['ES']['cos'])
                         ]

        # generate uncertainties using Monte Carlo Propagation object
        es_unc, li_unc, lt_unc = UNC_obj_CB.propagate_Instrument_Uncertainty(means, uncertainties)

        # NOTE: Debugging check
        is_negative = np.any([ x < 0 for x in means])
        if is_negative:
            print('WARNING: Negative uncertainty potential')
        is_negative = np.any([ x < 0 for x in uncertainties])
        if is_negative:
            print('WARNING: Negative uncertainty potential')
        if any(es_unc < 0) or any(li_unc < 0) or any(lt_unc < 0):
            print('WARNING: Negative uncertainty potential')

        es, li, lt = UNC_obj_CB.instruments(*means)

        # plot class based L1B uncertainties
        rad_cal_str = "ES_RADCAL_CAL" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "ES_RADCAL_UNC"
        cal_col_str = "1" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"

        from Source.PIU.Breakdown_CB import plottingToolsCB, PlotMaths
        BD_UNCS, BD_VALS = PlotMaths.classBased(UNC_obj_CB, means, uncertainties, cul=False)  # can set to be cumulative spectral plots
        
        BD_UNCS['ES']['pert'] = stats['ES']["perturbations"] * es
        BD_UNCS['LI']['pert'] = stats['LI']["perturbations"] * li if 'LI' in PDS.uncs else zeroes
        BD_UNCS['LT']['pert'] = stats['LT']["perturbations"] * lt if 'LT' in PDS.uncs else zeroes

        es_unc = np.sqrt(es_unc**2 + BD_UNCS['ES']['pert']**2)
        li_unc = np.sqrt(li_unc**2 + BD_UNCS['LI']['pert']**2)
        lt_unc = np.sqrt(lt_unc**2 + BD_UNCS['LT']['pert']**2)

        # check if negative signal for any pixels
        is_negative = np.any([ x < 0 for x in means])
        if is_negative:
            print('WARNING: Negative uncertainty potential')

        # TODO: when plotting include the UV. start at 350-360 nm
        if ConfigFile.settings['bL2UncertaintyBreakdownPlot']:
            PT = plottingToolsCB(PDS, "", UNC_obj_CB)
            try:
                wavelengths = dict(
                        ES=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str]),
                        LI=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str]),
                        LT=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str])
                    )
                PT.plot_CB_spectral(BD_UNCS, BD_VALS, wavelengths)
                PT.pie_plot_class(BD_UNCS, BD_VALS, wavelengths, node.getGroup("ANCILLARY"))
            except ValueError as err:
                writeLogFileAndPrint(f"unable to run uncertainty breakdown plots, error: {err}")

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="invalid value encountered in divide")
            warnings.filterwarnings("ignore", message="divide by zero encountered in divide")

            # convert to relative in order to avoid a complex unit conversion process in ProcessL2.
            ES_unc = es_unc / np.abs(es)
            LI_unc = li_unc / np.abs(li)
            LT_unc = lt_unc / np.abs(lt)

        # interpolation step - bringing uncertainties to common wavebands from radiometric calibration wavebands.
        data_wvl = np.asarray(list(stats['ES']['std_Signal_Interpolated'].keys()),
                              dtype=float)
        out = dict(
            esUnc=utils.interp_common_wvls(ES_unc,
                                           np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                                       dtype=float)[PDS.ind_rad_wvl['ES']],
                                           data_wvl,
                                           return_as_dict=True
            )
        )
        if 'LI' in stats:
            out['liUnc']=utils.interp_common_wvls(LI_unc,
                                                  np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                                           dtype=float)[PDS.ind_rad_wvl['LI']],
                                                  data_wvl,
                                                  return_as_dict=True
            )
        if 'LT' in stats:
            out['ltUnc']=utils.interp_common_wvls(LT_unc,
                                                  np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                                           dtype=float)[PDS.ind_rad_wvl['LT']],
                                                  data_wvl,
                                                  return_as_dict=True
            )
        out['valid_pixels']=PDS.nan_mask
        return out, BD_UNCS

    def ClassBasedL2(self, node, uncGrp, PDS, stats, rhoScalar, rhoVec, rhoDelta, waveSubset, xSlice) -> dict:
        """
        Propagates class based uncertainties for all Lw and Rrs. See D-10 section 5.3.1.

        :param node: HDFRoot which stores L1BQC data
        :param uncGrp: HDFGroup storing the uncertainty budget
        :param rhoScalar: rho input if Mobley99 or threeC rho is used
        :param rhoVec: rho input if Zhang17 rho is used
        :param rhoDelta: uncertainties associated with rho
        :param waveSubset: wavelength subset for any band convolution (and sizing rhoScalar if used)
        :param xSlice: Dictionary of input radiance, raw_counts, standard deviations etc.

        :return: dictionary of output uncertainties that are generated
        """
        try:
            # create object for running uncertainty propagation, M means number of monte carlo draws
            UNC_obj_CB = Propagate(M=100, cores=0)
        except NotImplementedError:
             print("Uncertainties not implemented for TriOS/DALEC/So-rad in Factory Regime")
             return False

        waveSubset = np.array(waveSubset, dtype=float)  # convert waveSubset to numpy array
        esXstd = xSlice['esSTD_RAW']  # stdevs taken at instrument wavebands (not common wavebands)
        liXstd = xSlice['liSTD_RAW']
        ltXstd = xSlice['ltSTD_RAW']

        if rhoScalar is not None:  # make rho a constant array if scalar
            rho = np.ones(len(list(esXstd.keys()))) * rhoScalar
            rhoUNC = utils.interp_common_wvls(np.array(rhoDelta, dtype=float),
                                             waveSubset,
                                             np.asarray(list(esXstd.keys()), dtype=float),
                                             return_as_dict=False)
        else:  # zhang rho needs to be interpolated to radcal wavebands (len must be 255)
            rho = utils.interp_common_wvls(np.array(list(rhoVec.values()), dtype=float),
                                          waveSubset,
                                          np.asarray(list(esXstd.keys()), dtype=float),
                                          return_as_dict=False)
            rhoUNC = utils.interp_common_wvls(rhoDelta,
                                             waveSubset,
                                             np.asarray(list(esXstd.keys()), dtype=float),
                                             return_as_dict=False)

        # interpolate to radcal wavebands - check string for radcal group based on factory or class-based processing
        rad_cal_str = "ES_RADCAL_CAL" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "ES_RADCAL_UNC"
        cal_col_str = "1" if "ES_RADCAL_CAL" in uncGrp.datasets.keys() else "wvl"
        es = utils.interp_common_wvls(np.asarray(list(xSlice['es'].values()), dtype=float).flatten(),
                                     np.asarray(list(xSlice['es'].keys()), dtype=float).flatten(),
                                     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                              dtype=float)[PDS.ind_rad_wvl['ES']],
                                     return_as_dict=False)
        li = utils.interp_common_wvls(np.asarray(list(xSlice['li'].values()), dtype=float).flatten(),
                                     np.asarray(list(xSlice['li'].keys()), dtype=float).flatten(),
                                     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                              dtype=float)[PDS.ind_rad_wvl['LI']],
                                     return_as_dict=False)
        lt = utils.interp_common_wvls(np.asarray(list(xSlice['lt'].values()), dtype=float).flatten(),
                                     np.asarray(list(xSlice['lt'].keys()), dtype=float).flatten(),
                                     np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str],
                                              dtype=float)[PDS.ind_rad_wvl['LT']],
                                     return_as_dict=False)

        ones = np.ones_like(es)

        lw_means = [lt, rho, li,
                    ones, ones,
                    ones, ones,
                    ones, ones,
                    ones, ones,
                    ones, ones,
                    ones, ones
                    ]

        lw_uncertainties = [np.abs(np.array(list(ltXstd.values())).flatten() * lt),
                            rhoUNC,
                            np.abs(np.array(list(liXstd.values())).flatten() * li),
                            PDS.uncs['LI']['cal'] / 200, PDS.uncs['LT']['cal'] / 200,
                            PDS.uncs['LI']['stab'], PDS.uncs['LT']['stab'],
                            PDS.uncs['LI']['nlin'], PDS.uncs['LT']['nlin'],
                            PDS.uncs['LI']['stray'] / 100, PDS.uncs['LI']['stray'] / 100,
                            PDS.uncs['LI']['ct'], PDS.uncs['LI']['ct'],
                            PDS.uncs['LI']['pol'], PDS.uncs['LI']['pol']
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

        rrs_uncertainties = [np.abs(np.array(list(ltXstd.values())).flatten() * lt),
                             rhoUNC,
                             np.abs(np.array(list(liXstd.values())).flatten() * li),
                             np.abs(np.array(list(esXstd.values())).flatten() * es),
                             PDS.uncs['ES']['cal'] / 200, PDS.uncs['LI']['cal'] / 200, PDS.uncs['LT']['cal'] / 200,
                             PDS.uncs['ES']['stab'], PDS.uncs['LI']['stab'], PDS.uncs['LT']['stab'],
                             PDS.uncs['ES']['nlin'], PDS.uncs['LI']['nlin'], PDS.uncs['LT']['nlin'],
                             PDS.uncs['ES']['stray'] / 100, PDS.uncs['LI']['stray'] / 100, PDS.uncs['LT']['stray'] / 100,
                             PDS.uncs['ES']['ct'], PDS.uncs['LI']['ct'], PDS.uncs['LT']['ct'],
                             PDS.uncs['LI']['pol'], PDS.uncs['LT']['pol'], PDS.uncs['ES']['cos']
                             ]

        rrsAbsUnc = UNC_obj_CB.Propagate_RRS_HYPER(rrs_means, rrs_uncertainties)

        from Source.PIU.Breakdown_CB import plottingToolsCB, PlotMaths
        BD_UNCS, BD_VALS = PlotMaths.classBasedL2(UNC_obj_CB, lw_means, rrs_means, lw_uncertainties, rrs_uncertainties, cul=False)
        
        # Use Law of propagation of uncertainty to add perturbation uncertainty to Rrs/Lw
        es_pert = stats['ES']["perturbations"] * es
        li_pert = stats['LI']["perturbations"] * li
        lt_pert = stats['LT']["perturbations"] * lt

        sc_1 = 1  # df/dLt
        # rho not included as it has no unc contribution to perturbations
        sc_3 = rho**2  # df/dLi
        
        BD_UNCS['Lw']['pert'] = np.sqrt(
            (sc_1 * lt_pert**2) +
            (sc_3 * li_pert**2) 
        )

        sc_1 = 1 / es   # df/dLT
        sc_2 = rho / es # df/dLI
        sc_4 = (lt - rho*li) / es**2  # df/dES

        BD_UNCS['Rrs']['pert'] = np.sqrt(
            sc_1**2 * lt_pert**2 +
            sc_2**2 * li_pert**2 + 
            sc_4**2 * es_pert**2
        )

        if ConfigFile.settings['bL2UncertaintyBreakdownPlot']:
            acqTime = datetime.strptime(node.attributes['TIME-STAMP'], '%a %b %d %H:%M:%S %Y')
            cast = f"{type(self).__name__}_{acqTime.strftime('%Y%m%d%H%M%S')}"
            PT = plottingToolsCB(PDS, "", UNC_obj_CB)
            try:
                PT.plot_CB_spectral(
                    BD_UNCS, 
                    BD_VALS,                     
                    dict(
                        Lw =np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[PDS.ind_rad_wvl['ES']],
                        Rrs=np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[PDS.ind_rad_wvl['ES']],
                    ),
                    level='L2'
                )
                PT.pie_plot_class_l2(
                    BD_UNCS,
                    BD_VALS,
                    np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float),  # pass radcal wavelengths
                    cast,
                    node.getGroup("ANCILLARY")
                )
            except ValueError as err:
                writeLogFileAndPrint(f"unable to run uncertainty breakdown plots for {cast}, with error: {err}")

        # these are absolute values!
        rhoUNC_CWB = utils.interp_common_wvls(
            rhoUNC,
            np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[PDS.ind_rad_wvl['ES']],
            waveSubset,
            return_as_dict=False
        )
        # lwAbsUnc[PDS.nan_mask] = np.nan
        lwAbsUnc = utils.interp_common_wvls(
            lwAbsUnc,
            np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[PDS.ind_rad_wvl['ES']],
            waveSubset,
            return_as_dict=False
        )
        # rrsAbsUnc[PDS.nan_mask] = np.nan
        rrsAbsUnc = utils.interp_common_wvls(
            rrsAbsUnc,
            np.array(uncGrp.getDataset(rad_cal_str).columns[cal_col_str], dtype=float)[PDS.ind_rad_wvl['ES']],
            waveSubset,
            return_as_dict=False
        )

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
                    esUNC_band, liUNC_band, ltUNC_band, rhoUNC, waveSubset, xSlice
                )
            )
        UNC.update(
            {"rhoUNC_HYPER": {str(k): val for k, val in zip(waveSubset, rhoUNC_CWB)},
            "lwUNC": lwAbsUnc,
             "rrsUNC": rrsAbsUnc}
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

        from Source.PIU.Breakdown_FRM import SolveLPU, plottingToolsFRM
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

        BD_UNCS.update({k: {} for k in ['NLw', 'Lw', 'Rrs', 'rho']})

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
        f0_unc = np.array(list(xSlice['f0_unc'].values()))

        # no uncertainty in wavelengths
        sample_wavelengths = cm.generate_sample(mdraws, np.array(waveSubset), None, None)
        sample_Lw = UNC_Obj_FRM.MCP.run_samples(Propagate.Lw_FRM, [sample_LT, sample_rho, sample_LI])
        sample_Rrs = UNC_Obj_FRM.MCP.run_samples(Propagate.Rrs_FRM, [sample_LT, sample_rho, sample_LI, sample_ES])
        LPU.waterLeaving(BD_UNCS_common_wb, BD_UNCS, np.mean(sample_LI, axis=0), rho)
        LPU.reflectance(
            BD_UNCS_common_wb, 
            BD_UNCS, 
            np.mean(sample_ES, axis=0), 
            np.mean(sample_LI, axis=0), 
            np.mean(sample_LT, axis=0),
            rho
        )
        LPU.normalised_waterLeaving(BD_UNCS, f0_unc)

        del BD_UNCS_common_wb  # no longer needed

        UNCS = {}  # output uncertainties

        # do band convolution if selected
        for s_key in self._SATELLITES.keys():
            UNCS.update(
                self.get_band_outputs_FRM(
                s_key, UNC_Obj_FRM, sample_ES, sample_LI, sample_LT, sample_rho, sample_wavelengths
                )
            )

        lwDelta = UNC_Obj_FRM.MCP.process_samples(None, sample_Lw)
        rrsDelta = UNC_Obj_FRM.MCP.process_samples(None, sample_Rrs)

        if ConfigFile.settings['bL2UncertaintyBreakdownPlot']:  # check if unc plots enabled
            for meas in ['Lw', 'Rrs']:
                UNC = BD_UNCS[meas]
                PT = plottingToolsFRM(meas, PDS)

                if meas.upper() == 'LW':
                    signal = np.mean(sample_Lw,  axis=0)
                    ylim = [0, 5]
                else:
                    signal = np.mean(sample_Rrs, axis=0)
                    ylim = [0, 5]

                ## DO PLOTS ##
                wvls = np.array(waveSubset)
                PT.plot(wvls, UNC['noise'],  "noise",                   rel_to=signal, ylim=ylim)
                PT.plot(wvls, UNC['pert'],   "env perturbations",       rel_to=signal, ylim=ylim)
                PT.plot(wvls, UNC['clin'],   "non-linearity",           rel_to=signal, ylim=ylim)
                PT.plot(wvls, UNC['cSl'],    "straylight",              rel_to=signal, ylim=ylim)
                PT.plot(wvls, UNC['radcal'], "radiometric calibration", rel_to=signal, ylim=ylim)

                # post normalisation
                PT.plot(wvls, UNC['stab'], "stability", rel_to=signal, ylim=ylim)
                PT.plot(wvls, UNC['ct'],   "ct",        rel_to=signal, ylim=ylim)
                PT.plot(wvls, UNC['rho'],  "rho",       rel_to=signal, ylim=ylim)
                
                # plot contributions that vary between sensors
                if meas.upper() == 'RRS':
                    PT.plot(wvls, UNC['cos_dir'],  "cosine (direct)",  rel_to=signal, ylim=ylim)
                    PT.plot(wvls, UNC['cos_diff'], "cosine (diffuse)", rel_to=signal, ylim=ylim)
                
                PT.plot(wvls, UNC['pol'], "polarisation", rel_to=signal, ylim=ylim)
                
                PT.save_figure(level=meas)  # save the figure once all of the contributions have been added to the plot (will close the figure)
            
                PT.plot_pie_FRM(meas, wvls, BD_UNCS[meas], signal, 'L2')

        UNCS["rhoUNC_HYPER"] = {str(wvl): val for wvl, val in zip(waveSubset, rhoDelta)}
        UNCS["lwUNC"] = lwDelta  # Multiply by large number to reduce round off error
        UNCS["rrsUNC"] = rrsDelta

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
