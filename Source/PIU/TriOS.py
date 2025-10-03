# python packages
import pandas as pd
from copy import deepcopy
from collections import OrderedDict

# maths
import numpy as np
import comet_maths as cm

# typing
from typing import Optional, Union, Any

# Source files
from Source.HDFGroup import HDFGroup
from Source.ConfigFile import ConfigFile

# PIU files
from Source.PIU.BaseInstrument import BaseInstrument
from Source.PIU.MeasurementFunctions import MeasurementFunctions as mf
from Source.PIU.PIUDataStore import PIUDataStore as pds

# UTILITIES
from Source.utils.loggingHCP import writeLogFileAndPrint


class TriOS(BaseInstrument):

    def __init__(self):
        super().__init__()
        self.name = "TriOS"

    def lightDarkStats(self, grp: HDFGroup, XSlice: OrderedDict, sensortype: str) -> dict[str: Union[np.array, dict]]:
        """
        TriOS specific method to get statistics from ensemble

        :param grp: HDFGroup of data for the entire RAW file
        :param XSlice: OrderedDict of data for the ensemble
        :param sensortype: name of sensortype, i.e. ES, LI or LT
        """

        (
            raw_cal, 
            raw_back,
            raw_data,
            raw_wvl,
            int_time,
            int_time_t0,
            DarkPixelStart,
            DarkPixelStop,
        ) = TriOSUtils.readParams(grp, XSlice, sensortype)

        del grp, XSlice  # delete unused data to save memory

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
            writeLogFileAndPrint("too few scans to make meaningful statistics")
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

        std_signal = {}
        for i, wvl in enumerate(raw_wvl):
            std_signal[wvl] = pow(
                (pow(light_std[i], 2) + pow(dark_std[i], 2)), 0.5) / np.average(calibrated_mesure, axis=0)[i]

        return dict(
            ave_Light=np.array(light_avg),
            ave_Dark=np.array(dark_avg),
            std_Light=np.array(light_std),
            std_Dark=np.array(dark_std),
            std_Signal=std_signal,
        )

    def FRM(self, PDS: pds, stats: dict, newWaveBands: np.array) -> dict[str, np.array]:
        
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

            from Source.PIU.Breakdown_FRM import plottingToolsFRM, SolveLPU
            PT = plottingToolsFRM(s_type, PDS)
            LPU = SolveLPU(prop)
            DATA = PDS.coeff[s_type]  # retrieve dictionaries for speed
            UNC = PDS.uncs[s_type]
            BD_UNCS = output_BD_UNCS[s_type]  # breakdown uncertainties
            BD_CORR = output_BD_CORR[s_type]  # breakdown correction magnitudes

            # generate samples
            sample_cal_int = cm.generate_sample(mDraws, DATA['cal_int'], None, None)
            sample_int_time = cm.generate_sample(mDraws, DATA['int_time'], None, None)
            sample_n_iter =   cm.generate_sample(mDraws, DATA['n_iter'], None, None, dtype=int)
            
            sample_Ct =   cm.generate_sample(mDraws, DATA['Ct'], UNC['Ct'], "syst")
            sample_LAMP = cm.generate_sample(mDraws, DATA['LAMP'], UNC['LAMP'], "syst")
            sample_PANEL = None
            sample_mZ =   cm.generate_sample(mDraws, DATA['mZ'], UNC['mZ'], "rand")

            k = DATA['t1']/(DATA['t2'] - DATA['t1'])
            sample_k = cm.generate_sample(mDraws, k, None, None)
            sample_t1 = cm.generate_sample(mDraws, DATA['t1'], None, None)
            sample_S1 = cm.generate_sample(mDraws, np.asarray(DATA['S1']), UNC['S1'], "rand")
            sample_S2 = cm.generate_sample(mDraws, np.asarray(DATA['S2']), UNC['S2'], "rand")
            sample_S12 = prop.run_samples(mf.S12func, [sample_k, sample_S1, sample_S2])

            BD_CORR['S1'] = np.mean(sample_S1, axis=0)
            BD_CORR['S2'] = np.mean(sample_S2, axis=0)
            BD_CORR['S12'] = np.mean(sample_S12, axis=0)  # output sample means for Sample_S12 mean per pixel (dont worry about 320 nm)
            BD_UNCS.update(LPU.S12_alpha(PDS, s_type))

            if self.sl_method.upper() == 'ZONG':  # for internal coding use only, set by default in HCP
                sample_n_IB = self.gen_n_IB_sample(mDraws)  # n_IB sample must be integer and in the range 3-6
                from Source.ProcessL1b_FRMCal import ProcessL1b_FRMCal
                sample_C_zong = prop.run_samples(ProcessL1b_FRMCal.Zong_SL_correction_matrix,
                                                 [sample_mZ, sample_n_IB])
                sample_sl_corr = prop.run_samples(mf.Zong_SL_correction, [sample_S12, sample_C_zong])
            else:  # slaper
                sample_sl_corr = self.get_Slaper_Sl_unc(
                    DATA['S12'], sample_S12, DATA['mZ'], sample_mZ, DATA['n_iter'], sample_n_iter, prop, mDraws
                )

            # sample for Non-Linearity
            sample_alpha = prop.run_samples(mf.alphafunc, [sample_S1, sample_S12])
            BD_CORR['alpha_mag'] = np.mean(sample_alpha, axis=0)

            if s_type.upper() == "ES":
                sample_updated_radcal_gain = prop.run_samples(mf.update_cal_ES, 
                                                              [sample_sl_corr, sample_LAMP, sample_cal_int, sample_t1]
                                                              )
                
                # compute cosine error based on lab characterisation and cosine response asymmetry
                sample_zen_ang = cm.generate_sample(mDraws, DATA['zenith_ang'], None, None)
                sample_zen_avg_coserror = cm.generate_sample(mDraws, DATA['zen_avg_coserr'], UNC['zenith_ang'], "syst")
                sample_fhemi_coserr = cm.generate_sample(mDraws, DATA['fhemi'], UNC['fhemi'], "syst")
            else:
                sample_PANEL = cm.generate_sample(mDraws, DATA['PANEL'], UNC['PANEL'], "syst")
                sample_updated_radcal_gain = prop.run_samples(mf.update_cal_rad,
                                                              [sample_sl_corr, sample_LAMP, sample_PANEL,
                                                               sample_cal_int,
                                                               sample_t1])
            
            BD_UNCS.update(LPU.updatedGains(BD_UNCS, PDS, s_type, sample_sl_corr))

            ind_nocal = DATA['ind_nocal']
            sample_updated_radcal_gain[:, ind_nocal == True] = 1

            BD_UNCS['radcal'][ind_nocal == True] = 0  # set radcal uncertainty to 0 where calibration is not applied 
            BD_CORR['updated_gain'] = np.mean(sample_updated_radcal_gain, axis=0)

            std_light = stats[s_type]['std_Light'] / 65535.0 # standard deviations are taken from generateSensorStats
            std_dark = stats[s_type]['std_Dark']

            sample_back_corr = cm.generate_sample(mDraws, np.mean(DATA['light'], axis=0), std_light, "rand")
            sample_offset = cm.generate_sample(mDraws, np.mean(DATA['dark']), np.mean(std_dark), "rand")  # mean of std_dark?
            sample_dark_corr = prop.run_samples(mf.dark_Substitution, [sample_back_corr, sample_offset])

            # Non-Linearity Correction
            sample_nlin_corr = prop.run_samples(mf.non_linearity_corr, [sample_dark_corr, sample_alpha])
            BD_UNCS.update(LPU.nonLinearity(BD_UNCS, BD_CORR['alpha_mag'], sample_dark_corr))
            BD_CORR['nlin'] = np.mean(sample_nlin_corr, axis=0)
            BD_CORR['clin'] = np.mean(sample_dark_corr, axis=0) - BD_CORR['nlin']
            
            # apply cal to absolute uncs at the end of the process to put them all in the same units. then put them relative to final signal
            # Straylight Correction
            if self.sl_method.upper() == 'ZONG':  # for internal use only, Zong set as default in HCP
                sample_sl_corr = prop.run_samples(
                    mf.Zong_SL_correction, [sample_nlin_corr, sample_C_zong]
                )
            else:
                dark_corr_data = mf.dark_Substitution(
                    np.mean(sample_back_corr, axis=0), np.mean(sample_offset, axis=0)
                )
                nl_corr_signal = mf.non_linearity_corr(dark_corr_data, BD_CORR['alpha_mag'])
                sample_sl_corr = self.get_Slaper_Sl_unc(
                    nl_corr_signal, sample_nlin_corr, DATA['mZ'], sample_mZ, DATA['n_iter'], sample_n_iter, prop, mDraws
                )  # simplified code by adding Slaper correction to one fucntion

            BD_UNCS.update(LPU.strayLight(BD_UNCS, BD_CORR['nlin'], sample_C_zong))
            BD_CORR['sl'] = np.mean(sample_sl_corr, axis=0)
            BD_CORR['cSl'] = BD_CORR['nlin'] - BD_CORR['sl']

            # Normalise based on integration time
            sample_normalised = prop.run_samples(mf.normalise, [sample_sl_corr, sample_cal_int, sample_int_time])
            
            # Apply Updated Calibration
            sample_cal_corr = prop.run_samples(mf.absolute_calibration, [sample_normalised, sample_updated_radcal_gain])
            cal_corr_signal = np.mean(sample_cal_corr, axis=0)  # calibrated signal for sensitivity coeffs
            BD_UNCS.update(LPU.calibration(BD_UNCS, BD_CORR['updated_gain'], sample_normalised))
            BD_CORR['radcal'] = LPU.get_original_gains(s_type, DATA['S1'], sample_LAMP, sample_PANEL)           

            # Stability correction
            sample_stab = cm.generate_sample(mDraws, np.ones(len(UNC['stab'])), UNC['stab'], "syst")
            sample_stab_corr = prop.run_samples(mf.apply_CB_corr, [sample_cal_corr, sample_stab])
            BD_UNCS['stab'] = np.sqrt(cal_corr_signal**2 * UNC['stab']**2)

            # Thermal correction
            sample_ct_corr = prop.run_samples(mf.thermal_corr, [sample_stab_corr, sample_Ct])
            BD_UNCS.update(LPU.temperature(BD_UNCS, PDS, s_type, cal_corr_signal))

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

                BD_UNCS.update(LPU.cosine(BD_UNCS, sample_ct_corr, dir_rat, sample_cos_corr_comp, sample_fhemi_coserr))
                signal = np.mean(sample_cos_corr, axis=0)

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
            
            if ConfigFile.settings['bL2UncertaintyBreakdownPlot']:  # check if unc plots enabled
                ## DO PLOTS ##
                PT.plot(DATA['radcal_wvl'], BD_UNCS['noise'],  "dark corrected",          rel_to=signal)
                PT.plot(DATA['radcal_wvl'], BD_UNCS['clin'],   "non-linearity",           rel_to=signal)
                PT.plot(DATA['radcal_wvl'], BD_UNCS['cSl'],    "straylight",              rel_to=signal)
                PT.plot(DATA['radcal_wvl'], BD_UNCS['radcal'], "radiometric calibration", rel_to=signal)

                # post normalisation
                PT.plot(DATA['radcal_wvl'], BD_UNCS['stab'], "stability", rel_to=signal)
                PT.plot(DATA['radcal_wvl'], BD_UNCS['ct'],   "ct",        rel_to=signal)
                
                # plot contributions that vary between sensors
                if s_type.upper() == 'ES':
                    # PT.plot(DATA['radcal_wvl'], BD_UNCS['cosine'], "cosine", rel_to=signal)
                    PT.plot(DATA['radcal_wvl'], BD_UNCS['cos_dir'],  "cosine (direct)",  rel_to=signal)
                    PT.plot(DATA['radcal_wvl'], BD_UNCS['cos_diff'], "cosine (diffuse)", rel_to=signal)
                else:
                    PT.plot(DATA['radcal_wvl'], BD_UNCS['pol'], "polarisation", rel_to=signal)
                
                PT.save_figure()  # save the figure once all of the contributions have been added to the plot (will close the figure)
            
                PT.plot_pie_FRM(s_type, DATA['wvls'], BD_UNCS, signal)

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


class TriOSUtils:
    def __init__(self):
        pass

    @staticmethod
    def readParams(grp, data, s):
        raw_cal = grp.getDataset(f"CAL_{s}").data
        raw_back = np.asarray(grp.getDataset(f"BACK_{s}").data.tolist())
        raw_data = np.asarray(list(data['data'].values())).transpose()  # data is transpose of old version

        raw_wvl = np.array(pd.DataFrame(grp.getDataset(s).data).columns)
        int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
        DarkPixelStart = int(grp.attributes["DarkPixelStart"])
        DarkPixelStop = int(grp.attributes["DarkPixelStop"])
        int_time_t0 = int(grp.getDataset(f"BACK_{s}").attributes["IntegrationTime"])

        # sensitivity factor : if raw_cal==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = np.array([rc[0] == 0 for rc in raw_cal])  # changed due to raw_cal now being a np array
        ind_nan = np.array([np.isnan(rc[0]) for rc in raw_cal])
        ind_nocal = ind_nan | ind_zero
        raw_cal = np.array([rc[0] for rc in raw_cal])
        raw_cal[ind_nocal==True] = 1

        return (
            raw_cal, 
            raw_back,
            raw_data,
            raw_wvl,
            int_time,
            int_time_t0,
            DarkPixelStart,
            DarkPixelStop,
            )