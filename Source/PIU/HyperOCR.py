
# python packages
from copy import deepcopy
import calendar
from inspect import currentframe, getframeinfo

# typing
from typing import Union, Any, Optional
from collections import OrderedDict

# maths
import numpy as np

# Source files
from Source.HDFRoot import HDFRoot
from Source.HDFGroup import HDFGroup
from Source.ConfigFile import ConfigFile

# PIU files
from Source.PIU.BaseInstrument import BaseInstrument
from Source.PIU.PIUDataStore import PIUDataStore as pds

# Utilities
from Source.utils.comparing import isIncreasing, hasNan
from Source.utils.interpolating import interp
from Source.utils.loggingHCP import writeLogFileAndPrint


class HyperOCR(BaseInstrument):

    def __init__(self):
        super().__init__()
        self.name = "HyperOCR"

    def lightDarkStats(self, grp: dict[str: HDFGroup], XSlice: dict[str: OrderedDict], sensortype: str) -> dict[str: Union[np.array, dict]]:
        """
        Seabird HyperOCR method for retrieving ensemble statistics

        :param grp: dictionary with keys 'LIGHT' for light data and 'DARK' for dark data. 
        The dictionary value should be the HDFGroup of the associated data type for the entire RAW file
        :param XSlice: dictionary with keys 'LIGHT' and 'DARK' for respective data types. 
        The dictionary value should be the associated data for the ensemble
        :param sensortype: name of sensortype, i.e. ES, LI or LT
        """
        lightGrp = grp['LIGHT']
        lightSlice = deepcopy(XSlice['LIGHT'])
        darkGrp = grp['DARK']
        darkSlice = deepcopy(XSlice['DARK'])

        if darkGrp.attributes["FrameType"] == "ShutterDark" and darkGrp.getDataset(sensortype):
            darkData = darkSlice['data'] 
        if lightGrp.attributes["FrameType"] == "ShutterLight" and lightGrp.getDataset(sensortype):
            lightData = lightSlice['data']
        
        # check valid data for retireving stats
        if darkGrp is None or lightGrp is None:
            msg = f'No radiometry found for {sensortype}'
            print(msg)
            writeLogFileAndPrint(msg)
            return False
        elif not HyperOCRUtils.check_data(darkData, lightData):
            return False

        # store results locally for speed
        std_light=[]
        std_dark=[]
        ave_light=[]
        ave_dark = []
        env_pert = []
        std_signal = []
        signal_noise = {}

        # number of replicates for light and dark readings
        N = np.asarray(list(lightData.values())).shape[1]
        Nd = np.asarray(list(darkData.values())).shape[1]
        for i, k in enumerate(lightData.keys()):
            wvl = str(float(k))

            # apply normalisation to the standard deviations used in uncertainty calculations
            if N > 25:  # normal case
                std_light.append(np.std(lightData[k])/np.sqrt(N))
                std_dark.append(np.std(darkData[k])/np.sqrt(Nd) )  # sigma here is essentially sigma**2 so N must sqrt
            elif N > 3:  # few scans, use different statistics
                std_light.append(np.sqrt(((N-1)/(N-3))*(np.std(lightData[k]) / np.sqrt(N))**2))
                std_dark.append(np.sqrt(((Nd-1)/(Nd-3))*(np.std(darkData[k]) / np.sqrt(Nd))**2))
            else:
                writeLogFileAndPrint("too few scans to make meaningful statistics")
                return False

            ave_light.append(np.average(lightData[k]))
            ave_dark.append(np.average(darkData[k]))
            env_pert.append(np.abs(np.std(lightData[k])/np.average(lightData[k])))

            for x in range(N):
                try:
                    lightData[k][x] -= darkData[k][x]
                except IndexError as err:
                    writeLogFileAndPrint(f"Light/Dark indexing error PIU.HypperOCR: {err}")
                    return False
            

            signalAve = np.average(lightData[k])  # at this point in the code lightdata is light-dark see line 95

            if signalAve:
                signal_noise[wvl] = pow((pow(std_light[i], 2) + pow(std_dark[i], 2))/pow(signalAve, 2), 0.5)
                # this should be divided by 
            else:
                signal_noise[wvl] = 0.0
            
            std_signal.append(np.std(lightData[k])/signalAve)  # as % of Dark corrected signal

        return dict(
            ave_Light=np.array(ave_light),
            ave_Dark=np.array(ave_dark),
            std_Light=np.array(std_light),
            std_Dark=np.array(std_dark),
            Signal_std=np.array(std_signal),
            Signal_noise=signal_noise,
            )  # output as dictionary for use in ProcessL2/PIU

    def FRM(self, PDS: pds, stats, newWaveBands) -> dict[str, np.array]:
        """
        FRM regime propagation instrument uncertainties for HyperOCR, see D10 section 5.3.2 for more information.

        :param PDS: PIUDataStore object containing all necessary FRM uncertanties/coefficients
        :param stats: nested dictionaries containing the output of LightDarkStats
        :param newWaveBands: common wavebands for interpolation of output
        """

        output_UNC = {}
        output_BD_UNCS = {k: {} for k in self.sensors}  # breakdown uncertainties
        output_BD_CORR = {k: {} for k in self.sensors}  # breakdown correction magnitudes

        for s_type in self.sensors:
            print(f"FRM Processing, {s_type}")

            # set up uncertainty propagation
            import punpy
            import comet_maths as cm
            from Source.PIU.MeasurementFunctions import MeasurementFunctions as mf
            mDraws = 100  # number of monte carlo draws
            prop = punpy.MCPropagation(mDraws, parallel_cores=1)

            from Source.PIU.Breakdown_FRM import SolveLPU
            LPU = SolveLPU(prop)
            DATA = PDS.coeff[s_type]  # retrieve dictionaries for speed
            UNC = PDS.uncs[s_type]
            BD_UNCS = output_BD_UNCS[s_type]  # breakdown uncertainties
            BD_CORR = output_BD_CORR[s_type]  # breakdown correction magnitudes
            
            # generate initial samples with comet maths
            sample_cal_int  = cm.generate_sample(mDraws, DATA['cal_int'], None, None)
            sample_int_time = cm.generate_sample(mDraws, DATA['int_time'], None, None)
            sample_n_iter   = cm.generate_sample(mDraws, DATA['n_iter'], None, None, dtype=int)
            
            sample_Ct    = cm.generate_sample(mDraws, DATA['Ct'], UNC['Ct'], "syst")
            sample_LAMP  = cm.generate_sample(mDraws, DATA['LAMP'], UNC['LAMP'], "syst")
            sample_PANEL = None
            sample_mZ    = cm.generate_sample(mDraws, DATA['mZ'], UNC['mZ'], "rand")

            sample_t1 = cm.generate_sample(mDraws, DATA['t1'], None, None)
            sample_S1 = cm.generate_sample(mDraws, np.asarray(DATA['S1']), UNC['S1'], "rand")
            sample_S2 = cm.generate_sample(mDraws, np.asarray(DATA['S2']), UNC['S2'], "rand")
            # normalise to the longer time

            k = DATA['t1']/(DATA['t2'] - DATA['t1'])
            sample_k   = cm.generate_sample(mDraws, k, None, None)
            sample_S12 = prop.run_samples(mf.S12func, [sample_k, sample_S1, sample_S2])
            
            BD_CORR['S1']  = np.mean(sample_S1, axis=0)
            BD_CORR['S2']  = np.mean(sample_S2, axis=0)
            BD_CORR['S12'] = np.mean(sample_S12, axis=0)  # output sample means for Sample_S12 mean per pixel (dont worry about 320 nm)
            BD_UNCS.update(LPU.S12_alpha(PDS, s_type))

            # samples for Straylight correction
            if self.sl_method.upper() == 'ZONG':  # zong is the default straylight correction
                sample_n_IB = self.gen_n_IB_sample(mDraws)
                from Source.ProcessL1b_FRMCal import ProcessL1b_FRMCal
                sample_C_zong = prop.run_samples(ProcessL1b_FRMCal.Zong_SL_correction_matrix,
                                                 [sample_mZ, sample_n_IB])
                sample_S12_sl_corr = prop.run_samples(mf.Zong_SL_correction, [sample_S12, sample_C_zong])  # TODO: REPLACED sample_S12 WITH sample_S1
            else:  # use slaper correction if selected - only available as a developer option currently
                sample_S12_sl_corr = self.get_Slaper_Sl_unc(
                    DATA['S12'], sample_S12, DATA['mZ'], sample_mZ, DATA['n_iter'], sample_n_iter, prop, mDraws
                )

            # sample for Non-Linearity
            sample_alpha = prop.run_samples(mf.alphafunc, [sample_S1, sample_S12])
            sample_alpha_CB  = cm.generate_sample(mDraws, DATA['cb_alpha'], UNC['cb_alpha'], "syst")
            no_lin_corr_indx = DATA['cb_alpha'] == 0
            sample_alpha[:, no_lin_corr_indx] = sample_alpha_CB[:, no_lin_corr_indx] 
            # validated by processing the sample and verifying that uncertainty in no_lin_corr_indx(s) are 1.077e-7
            
            BD_CORR['alpha_mag'] = np.mean(sample_alpha, axis=0)

            # direct comparison between Sample_S12 and alpha is useful but only if we're on the same integration time
            # Sample_S12 is integration time of lab, alpha is integration time of measurement

            if s_type.upper() == "ES":
                sample_updated_radcal_gain = prop.run_samples(mf.update_cal_ES, 
                                                              [sample_S12_sl_corr, sample_LAMP, sample_cal_int, sample_t1]
                                                              )

                sample_zen_ang = cm.generate_sample(mDraws, DATA['zenith_ang'], None, None)
                sample_zen_avg_coserror = cm.generate_sample(mDraws, DATA['zen_avg_coserr'], UNC['zenith_ang'], "syst")
                sample_fhemi_coserr = cm.generate_sample(mDraws, DATA['fhemi'], UNC['fhemi'], "syst")
            else:
                sample_PANEL = cm.generate_sample(mDraws, DATA['PANEL'], UNC['PANEL'], "syst")
                sample_updated_radcal_gain = prop.run_samples(mf.update_cal_rad,
                                                              [sample_S12_sl_corr, sample_LAMP, sample_PANEL,
                                                               sample_cal_int,
                                                               sample_t1])
            
            BD_UNCS.update(LPU.updatedGains(BD_UNCS, PDS, s_type, sample_S12_sl_corr))
            
            ind_nocal = DATA['ind_nocal']
            sample_updated_radcal_gain[:, ind_nocal == True] = 1

            BD_UNCS['radcal'][ind_nocal == True] = 0  # set radcal uncertainty to 0 where calibration is not applied 
            BD_CORR['updated_gain'] = np.mean(sample_updated_radcal_gain, axis=0)

            data = np.mean(DATA['light'], axis=0)
            data[ind_nocal is True] = 0  # 0 out data outside of cal so it doesn't affect statistics
            dark = np.mean(DATA['dark'], axis=0)
            dark[ind_nocal is True] = 0

            # signal uncertainties
            std_light = stats[s_type]['std_Light']  # standard deviations are taken from generateSensorStats
            std_dark = stats[s_type]['std_Dark']
            sample_light = cm.generate_sample(100, data, std_light, "rand")
            sample_dark  = cm.generate_sample(100, dark, std_dark,  "rand")

            # Dark correction
            sample_dark_corr = prop.run_samples(mf.dark_Substitution, [sample_light, sample_dark])
            BD_UNCS['noise'] = prop.process_samples(None, sample_dark_corr)

            # Non-Linearity
            sample_nlin_corr = prop.run_samples(mf.non_linearity_corr, [sample_dark_corr, sample_alpha])
            BD_UNCS.update(LPU.nonLinearity(BD_UNCS, BD_CORR['alpha_mag'], sample_dark_corr))
            BD_CORR['nlin'] = np.mean(sample_nlin_corr, axis=0)
            BD_CORR['clin'] = np.mean(sample_dark_corr, axis=0) - BD_CORR['nlin']

            # Straylight
            if self.sl_method.upper() == 'ZONG':
                sample_sl_corr = prop.run_samples(mf.Zong_SL_correction, [sample_nlin_corr, sample_C_zong])
            else:  # slaper
                dark_corr_data = mf.dark_Substitution(data, dark)
                nl_corr_signal = mf.non_linearity_corr(dark_corr_data, BD_CORR['alpha_mag'])
                sample_sl_corr = self.get_Slaper_Sl_unc(
                    nl_corr_signal, sample_nlin_corr, DATA['mZ'], sample_mZ, DATA['n_iter'], sample_n_iter, prop, mDraws
                )
            
            BD_UNCS.update(LPU.strayLight(BD_UNCS, BD_CORR['nlin'], sample_C_zong))
            BD_CORR['sl'] = np.mean(sample_sl_corr, axis=0)
            BD_CORR['cSl'] = BD_CORR['nlin'] - BD_CORR['sl']
            
            # Normalise based on integration time
            sample_normalised = prop.run_samples(mf.normalise, [sample_sl_corr, sample_cal_int, sample_int_time])  # no correction here but must be added to sensitivity coeffs

            # Apply Updated Calibration
            sample_cal_corr = prop.run_samples(mf.absolute_calibration, [sample_normalised, sample_updated_radcal_gain])
            BD_UNCS.update(LPU.calibration(BD_UNCS, BD_CORR['updated_gain'], sample_normalised))
            BD_CORR['radcal_coefs'] = LPU.get_original_gains(s_type, DATA['S1'], sample_LAMP, sample_PANEL)           

            # Stability correction
            cal_corr_signal = np.mean(sample_cal_corr, axis=0)
            sample_stab = cm.generate_sample(mDraws, np.ones(len(UNC['stab'])), UNC['stab'], "syst")
            sample_stab_corr = prop.run_samples(mf.apply_CB_corr, [sample_cal_corr, sample_stab])
            BD_UNCS['stab'] = np.sqrt(cal_corr_signal**2 * UNC['stab']**2)

            # Thermal correction
            sample_ct_corr = prop.run_samples(mf.thermal_corr, [sample_stab_corr, sample_Ct])
            BD_UNCS.update(LPU.temperature(BD_UNCS, PDS, s_type, cal_corr_signal))
            BD_CORR['ct'] = np.mean(sample_ct_corr, axis=0) - cal_corr_signal

            if s_type == "ES":
                # Cosine correction
                sol_zen = DATA['solar_zenith']
                dir_rat = DATA['direct_ratio']
                sample_sol_zen = cm.generate_sample(mDraws, sol_zen, np.asarray([0.05 for i in range(np.size(sol_zen))]), "rand")
                sample_dir_rat = cm.generate_sample(mDraws, dir_rat, 0.08*dir_rat, "syst")

                sample_cos_corr_comp = prop.run_samples(
                    mf.get_cos_corr, [
                        sample_zen_ang,
                        sample_sol_zen,
                        sample_zen_avg_coserror
                        ]
                )
                sample_cos_corr = prop.run_samples(
                    mf.cos_corr, [sample_ct_corr, sample_dir_rat, sample_cos_corr_comp, sample_fhemi_coserr]  # sample_cos_corr[:,ind_raw_wvl], sample_fhemi_coserr[:,ind_raw_wvl]
                )

                signal = np.mean(sample_cos_corr, axis=0)
                BD_UNCS.update(LPU.cosine(BD_UNCS, sample_ct_corr, dir_rat, sample_cos_corr_comp, sample_fhemi_coserr))
                BD_CORR['cosine'] = signal - np.mean(sample_ct_corr, axis=0)

                # Save Uncertainties
                unc = prop.process_samples(None, sample_cos_corr)
                sample = sample_cos_corr

            else:
                sample_pol = cm.generate_sample(mDraws, np.ones(len(UNC['pol'])), UNC['pol'], "syst")
                sample_pol_corr = prop.run_samples(mf.apply_CB_corr, [sample_ct_corr, sample_pol])
                ct_corr_signal = np.mean(sample_ct_corr, axis=0)
                
                BD_UNCS['pol'] = np.sqrt(ct_corr_signal**2 * UNC['pol']**2)
                signal = np.mean(sample_pol_corr, axis=0)

                # Save Uncertainties
                unc = prop.process_samples(None, sample_pol_corr)
                sample = sample_pol_corr

            LPU.environmental_perturbations(BD_UNCS, sample, stats[s_type]["Signal_std"])

            ind_nocal = DATA['ind_nocal']
            output_UNC[f"{s_type.lower()}Unc"] = unc[ind_nocal == False]  # relative uncertainty
            output_UNC[f"{s_type.lower()}Sample"] = sample[:, ind_nocal == False]  # keep samples raw

            # sort the outputs ready for processing
            # get sensor specific wavebands to be keys for uncs, then remove from output
            wvls = DATA['wvls']
            output_UNC[f"{s_type.lower()}Unc"] = PDS.interp_common_wvls(
                output_UNC[f"{s_type.lower()}Unc"], 
                wvls, 
                newWaveBands, 
                return_as_dict=True
                )
            output_UNC[f"{s_type.lower()}Sample"] = PDS.interpolateSamples(
                output_UNC[f"{s_type.lower()}Sample"], 
                wvls,
                newWaveBands
                )
            
        return output_UNC, output_BD_CORR, output_BD_UNCS


class HyperOCRUtils:
    def __init__(self):
        pass

    @staticmethod
    def darkToLightTimer(rawGrp, sensortype):
        darkGrp = rawGrp['DARK']
        lightGrp = rawGrp['LIGHT']

        lightData,darkData,lightDateTime,darkDateTime  = None,None,None,None,

        if darkGrp.attributes["FrameType"] == "ShutterDark" and darkGrp.getDataset(sensortype):
            darkData = darkGrp.getDataset(sensortype)
            darkDateTime = darkGrp.getDataset("DATETIME")
        if lightGrp.attributes["FrameType"] == "ShutterLight" and lightGrp.getDataset(sensortype):
            lightData = lightGrp.getDataset(sensortype)
            lightDateTime = lightGrp.getDataset("DATETIME")

        if darkGrp is None or lightGrp is None:
            writeLogFileAndPrint(f'No radiometry found for {sensortype}')
            return False
        elif not HyperOCRUtils.check_data(darkData, lightData):
            return False

        newDarkData = HyperOCRUtils.LightDarkInterp(lightData, lightDateTime, darkData, darkDateTime)
        if isinstance(newDarkData, bool):
            return False
        else:
            rawGrp['DARK'].datasets[sensortype].data = newDarkData
            rawGrp['DARK'].datasets[sensortype].datasetToColumns()
            return True
        
    @staticmethod
    def LightDarkInterp(lightData, lightTimer, darkData, darkTimer):
        # Interpolate Dark Dataset to match number of elements as Light Dataset
        newDarkData = np.copy(lightData.data)
        for k in darkData.data.dtype.fields.keys():  # For each wavelength
            x = np.copy(darkTimer.data).tolist()     # darktimer
            y = np.copy(darkData.data[k]).tolist()   # data at that band over time
            new_x = lightTimer.data                  # lighttimer

            if len(x) < 3 or len(y) < 3 or len(new_x) < 3:
                writeLogFileAndPrint("**************Cannot do cubic spline interpolation, length of datasets < 3")
                return False
            if not isIncreasing(x):
                writeLogFileAndPrint("**************darkTimer does not contain strictly increasing values")
                return False
            if not isIncreasing(new_x):
                writeLogFileAndPrint("**************lightTimer does not contain strictly increasing values")
                return False

            if len(x) >= 3:
                # Because x is now a list of datetime tuples, they'll need to be converted to Unix timestamp values
                xTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in x]
                newXTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in new_x]

                newDarkData[k] = interp(xTS,y,newXTS, fill_value=np.nan)

                for val in newDarkData[k]:
                    if np.isnan(val):
                        frameinfo = getframeinfo(currentframe())
                        msg = f'found NaN {frameinfo.lineno}'
            else:
                writeLogFileAndPrint('**************Record too small for splining. Exiting.')
                return False

        if hasNan(darkData):
            frameinfo = getframeinfo(currentframe())
            writeLogFileAndPrint(f'found NaN {frameinfo.lineno}')
            return False

        return newDarkData
    
    @staticmethod
    def check_data(dark, light):
        msg = None
        if (dark is None) or (light is None):
            writeLogFileAndPrint(f'Dark Correction, dataset not found: {dark} , {light}')
            return False

        if hasNan(light):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'

        if hasNan(dark):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'

        if msg:
            writeLogFileAndPrint(msg)

        return True
