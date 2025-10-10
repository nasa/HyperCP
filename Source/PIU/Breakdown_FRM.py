from os import path, makedirs, umask
import numpy as np
import matplotlib.pyplot as plt

import comet_maths as cm
from typing import Optional

# Source
from Source.MainConfig import MainConfig

# PIU
from Source.PIU.MeasurementFunctions import MeasurementFunctions as mf
from Source.PIU.PIUDataStore import PIUDataStore
from Source.PIU.HyperOCR import HyperOCR
from Source.PIU.TriOS import TriOS
from Source.PIU.DALEC import Dalec


class plottingToolsFRM:
    def __init__(self, s, PDS):
        self.s = s
        self.sza = PDS.sza
        self.cast = PDS.cast
        self.station = PDS.station

        self.plot_folder = path.join(MainConfig.settings['outDir'],'Plots','L2_Uncertainty_Breakdown')

    def plot(self, x: np.array, y: np.array, name: str, rel_to: Optional[np.array]=None, unit: Optional[str]=""):
        """

        """

        self.get_figure()  # create plt.figure with name based on sensor/station/cast
        if rel_to is not None:
            if len(rel_to.shape) > 1:
                y_mean = np.mean(rel_to, axis=0)
            else:  # if we have a signal to put uncs in relative units
                y_mean = rel_to  
            
            u_rel = (y/y_mean)*100
            plt.plot(x, u_rel, label=f"{name}")
            plt.ylabel("relative uncertainty (%)")
            plt.ylim(0,5)
        else:
            plt.plot(x, y, label=f"{name}")
            plt.ylabel(f"uncertainty ({unit})")

        plt.title(f"FRM Breakdown: {self.s}, Solar Zenith: {self.sza}")
        plt.xlabel("Wavelength (nm)")
        
        plt.xlim(400,800)

    def plot_pie_FRM(self, s, wavelengths, BD_UNCS, signal):
        """

        """

        self.get_figure()
        keys = dict(
            ES=["noise", "radcal", "stab", "clin", "ct", "cSl", "cos_diff", "cos_dir"],
            LI=["noise", "radcal", "stab", "clin", "ct", "cSl", "pol"],
            LT=["noise", "radcal", "stab", "clin", "ct", "cSl", "pol"]
        )
        labels = dict(
            ES=["noise", "calibration", "stability", "non-linearity", "temperature", "strayLight", "cosine (diffuse)", "cosine (direct)"],
            LI=["noise", "calibration", "stability", "non-linearity", "temperature", "strayLight", "polarisation"],
            LT=["noise", "calibration", "stability", "non-linearity", "temperature", "strayLight", "polarisation"]
        )

        indexes = [  # specific wavelengths requested by consortium partners
            np.argmin(np.abs(wavelengths - 670)),
            np.argmin(np.abs(wavelengths - 620)),
            np.argmin(np.abs(wavelengths - 560)),
            np.argmin(np.abs(wavelengths - 490)),
            np.argmin(np.abs(wavelengths - 442)),
            np.argmin(np.abs(wavelengths - 400)),
        ]
        for indx in indexes:
            wvl_at_indx = wavelengths[indx]  # why is numpy like this?
            fig, ax = plt.subplots()

            ax.pie(
                [self.getpct(BD_UNCS[key], signal)[indx] for key in keys[s]],
                labels=labels[s],
                autopct='%1.1f%%'
            )
            plt.title(f"{s} FRM Sensor-Specific Uncertainty Components at {wvl_at_indx}nm")
            fp = path.join(self.plot_folder, f"Sensor_pie_{s}_{self.cast}_{self.station}_{wvl_at_indx}.png")
            self.save_figure(fp, legend=False, grid=False)
            plt.close(fig)

    def get_figure(self):
        try:
            plt.figure(f"{self.s}_{self.cast}_{self.station}")
        except AttributeError:
            try:
                plt.figure(f"{self.s}_{self.cast}")
            except AttributeError:
                plt.figure(self.s)

    def save_figure(self, fp: Optional[str]=None, legend: bool=True, grid: bool=True):

        if legend:
            plt.legend()
        if grid:
            plt.grid('both')

        if fp is None:
            try:
                fp = path.join(self.plot_folder, f"BD_plot_{self.s}_{self.cast}_{self.station}.png")
            except (AttributeError, ValueError):
                fp = path.join(self.plot_folder, f"plot_sample_{self.s}.png")
        
        if not path.exists(self.plot_folder):
            try:
                orig_umask = umask(0)
                makedirs(self.plot_folder, 0o777)
            finally:
                umask(orig_umask)
        
        plt.savefig(fp)
        plt.close()
    
    @staticmethod
    def getpct(v1, v2):
        pct = []
        for i in range(len(v1)):
            if v2[i] != 0:  # ignore wavelengths where we do not have an output
                pct.append(v1[i]/v2[i])
            else:
                pct.append(0)  # put zero there instead of np.nan, it will be easy to avoid in plotting
        return np.array(pct) * 100  # convert to np array so we can use numpy broadcasting


class SolveLPU:
    def __init__(self, prop=None):
        if prop is not None:
            self.prop = prop
    
    @staticmethod
    def S12_alpha(PDS: PIUDataStore, s: str) -> dict[str: np.array]:
        """

        :param PDS: uncertainties and coefficients used in FRM-Sensor-Specific L1B signal caluclation
        :param s: sensor name - ES, LI or LT
        """

        LPU_UNCS = {}
        DATA = PDS.coeff[s]  # retrieve dictionaries for speed
        UNC = PDS.uncs[s]

        k = DATA['t1']/(DATA['t2'] - DATA['t1'])
        S12 = mf.S12func(k, DATA['S1'], DATA['S2'])
        
        # TODO: comment equations and sensitivity coeffs
        LPU_UNCS['S12'] = np.sqrt(
            ((1 + k)**2)*(UNC['S1']**2) + 
            (k**2)*(UNC['S2']**2)
        )
        LPU_UNCS['alpha'] = np.sqrt(
            (1/S12**2)**2 * UNC['S1']**2 + 
            ((S12 - 2*DATA['S1']) / S12**3)**2 * LPU_UNCS['S12']
        )

        return LPU_UNCS

    def updatedGains(self, LPU_UNCS: dict[str: np.array], PDS: PIUDataStore, s: str, sample_S12_sl_corr):
        DATA = PDS.coeff[s]  # retrieve dictionaries for speed
        UNC = PDS.uncs[s]

        S12_sl_corr = np.mean(sample_S12_sl_corr, axis=0)
        S12_sl_unc  = self.prop.process_samples(None, sample_S12_sl_corr)

        if s.upper() == 'ES':
            sensitivity_coefficient_1 = (1/DATA['LAMP'])*(10*DATA['cal_int']/DATA['t1'])
            sensitivity_coefficient_2 = (S12_sl_corr/DATA['LAMP']**2)*(10*DATA['cal_int']/DATA['t1'])
            LPU_UNCS['radcal'] = np.sqrt(
                sensitivity_coefficient_1**2 * S12_sl_unc**2 +
                sensitivity_coefficient_2**2 * UNC['LAMP']**2
            )
        else:
            lamp_2 = DATA['LAMP']**2
            panel_2 = DATA['PANEL']**2
            sensitivity_coefficient_1 = (np.pi/(DATA['LAMP']*DATA['PANEL']))*(10*DATA['cal_int']/DATA['t1'])
            sensitivity_coefficient_2 = (np.pi*S12_sl_corr/(DATA['PANEL'] * lamp_2))*(10*DATA['cal_int']/DATA['t1'])
            sensitivity_coefficient_3 = (np.pi*S12_sl_corr/(panel_2 * DATA['LAMP']))*(10*DATA['cal_int']/DATA['t1'])
            LPU_UNCS['radcal'] = np.sqrt(
                sensitivity_coefficient_1**2 * S12_sl_unc**2 + 
                sensitivity_coefficient_2**2 * UNC['LAMP']**2 + 
                sensitivity_coefficient_3**2 * UNC['PANEL']**2
            )

        return LPU_UNCS

    def nonLinearity(self, LPU_UNCS: dict[str: np.array], alpha: np.array, sample_signal: np.ndarray) -> dict[str: np.array]:
        """
        returns a dictionary with uncertainties in S12, alpha, instrument noise, non-linearity correction

        :param alpha: alpha for generating sensitivity coefficients
        :param signal: raw signal
        :param signal_unc: raw signal uncertainty
        """
        
        signal = np.mean(sample_signal, axis=0)
        signal_unc = self.prop.process_samples(None, sample_signal)  # uncertainty in dark correction due to noise
        # f = signal - signal*alpha
        # sen coef 1 = 1 - 2*alpha*signal
        # sen coef 2 = signal^2

        LPU_UNCS['noise'] = np.sqrt(
            (1 - 2*alpha*signal)**2 * signal_unc**2  # signal unc at this point is just dark correction uncertainty
        )
        LPU_UNCS['clin'] = np.sqrt(
            signal**4 * LPU_UNCS['alpha']**2
        )

        return LPU_UNCS

    def strayLight(self, LPU_UNCS: dict[str: np.array], nlin_signal: np.array, sample_C_zong: np.ndarray) -> dict[str: np.array]:
        """
        uses Monte Carlo to isolate uncertainty in signal which is due to straylight. 
        In addition passed other uncertainty contributions through measurement function in lieu of sensitivity coefficents

        :param LPU_UNCS: breakdown uncertainties generated from LPU
        :param nlin_signal: magnitude of non-linearity corrected signal
        :param sample_C_zong: PDF for C_zong matrix used in straylight correction
        """

        mDraws = sample_C_zong.shape[0]
        sample_lpu_dark      = cm.generate_sample(mDraws, nlin_signal, LPU_UNCS['noise'], 'rand')
        sample_lpu_nlin      = cm.generate_sample(mDraws, nlin_signal, LPU_UNCS['clin'], 'syst')
        sample_signal_no_unc = cm.generate_sample(mDraws, nlin_signal, None, None)
        c_zong_no_unc        = cm.generate_sample(mDraws, np.mean(sample_C_zong, axis=0), None, None)

        LPU_UNCS['noise'] = self._slMC(sample_lpu_dark, c_zong_no_unc)
        LPU_UNCS['clin'] = self._slMC(sample_lpu_nlin, c_zong_no_unc)
        LPU_UNCS['cSl']  = self._slMC(sample_signal_no_unc, sample_C_zong)
        
        return LPU_UNCS

    def _slMC(self, sample_signal, sample_zong):
        """
        propagates uncertainty through straylight using Monte Carlo
        """
        sample_out = self.prop.run_samples(mf.Zong_SL_correction, [sample_signal, sample_zong])
        return self.prop.process_samples(None, sample_out)
    
    def calibration(self, LPU_UNCS: dict[str: np.array], updated_gain: np.array, signal: np.ndarray) -> dict[str: np.array]:
        """
        :param LPU_UNCS: breakdown uncertainties generated from LPU
        :param updated_gain: magnitude of recalculated gains - for generating sensitivity coefficients
        :param signal: PDF of the normalised signal - for generating sensitivity coefficients
        """

        sen_coef1 = 1/updated_gain
        sen_coef2 = (np.mean(signal, axis=0) / updated_gain**2)
        
        LPU_UNCS['noise']  = np.sqrt(sen_coef1**2 * LPU_UNCS['noise']**2)
        LPU_UNCS['clin']   = np.sqrt(sen_coef1**2 * LPU_UNCS['clin']**2)
        LPU_UNCS['cSl']    = np.sqrt(sen_coef1**2 * LPU_UNCS['cSl']**2)
        LPU_UNCS['radcal'] = np.sqrt(sen_coef2**2 * LPU_UNCS['radcal']**2)

        return LPU_UNCS
    
    @staticmethod
    def get_original_gains(s, S1, sample_LAMP, sample_PANEL=None):
        """
        recovers original (not corrected for non-lin) radcal values

        :param s:
        :param S1: S1 signal from RadCalFile (S2 can be used)
        :param sample_LAMP: PDF for LAMP from radcal file
        :param sample_PANEL: PDF for PANEL from radcal file
        """

        LAMP_mag = np.mean(sample_LAMP, axis=0)
        if s.upper() == "ES":  # irradiance does not use a Panel
            return LAMP_mag / (S1*10)
        else:  # Radiance
            return (LAMP_mag * np.mean(sample_PANEL, axis=0)) / (np.pi*S1*10)
        
    def temperature(self, LPU_UNCS: dict[str: np.array], PDS: PIUDataStore, s: str, radcal_signal) -> dict[str: np.array]:
        """
        
        """

        DATA = PDS.coeff[s]  # retrieve dictionaries for speed
        UNC = PDS.uncs[s]

        LPU_UNCS['noise']   = np.sqrt(DATA['Ct']**2 * LPU_UNCS['noise']**2)
        LPU_UNCS['clin']   = np.sqrt(DATA['Ct']**2 * LPU_UNCS['clin']**2)
        LPU_UNCS['cSl']     = np.sqrt(DATA['Ct']**2 * LPU_UNCS['cSl']**2)
        LPU_UNCS['radcal'] = np.sqrt(DATA['Ct']**2 * LPU_UNCS['radcal']**2)
        LPU_UNCS['stab']   = np.sqrt(DATA['Ct']**2 * LPU_UNCS['stab']**2)
        LPU_UNCS['ct']     = np.sqrt(radcal_signal**2 * UNC['Ct']**2)

        return LPU_UNCS

    def cosine(self, LPU_UNCS: dict[str: np.array], sample_ct_corr, dir_ratio, sample_cos_corr, sample_fhemi)-> dict[str: np.array]:
        """

        """

        mDraws = sample_ct_corr.shape[0]

        sample_sig_no_unc = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), None, None)
        sample_sig_dark   = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['noise'], "rand")
        sample_sig_clin   = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['clin'], "syst")
        sample_sig_sl     = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['cSl'], "syst")
        sample_sig_cal    = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['radcal'], "syst")
        sample_sig_stab   = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['stab'], "syst")
        sample_sig_ct     = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['ct'], "syst")
        
        dir_rat_no_unc  = cm.generate_sample(mDraws, np.mean(dir_ratio), None, None)
        cos_corr_no_unc = cm.generate_sample(mDraws, np.mean(sample_cos_corr, axis=0), None, None)
        fhemi_no_unc    = cm.generate_sample(mDraws, np.mean(sample_fhemi, axis=0), None, None)
        
        LPU_UNCS['noise']    = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr,  [sample_sig_dark,   dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['clin']     = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr,  [sample_sig_clin,   dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['cSl']       = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr, [sample_sig_sl  ,   dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['radcal']   = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr,  [sample_sig_cal ,   dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['stab']     = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr,  [sample_sig_stab,   dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['ct']       = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr,  [sample_sig_ct  ,   dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['cos_dir']  = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr,  [sample_sig_no_unc, dir_ratio,      sample_cos_corr, fhemi_no_unc]))
        LPU_UNCS['cos_diff'] = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr,  [sample_sig_no_unc, dir_ratio,      cos_corr_no_unc, sample_fhemi]))
        LPU_UNCS['cosine']   = np.sqrt(LPU_UNCS['cos_dir']**2 +  LPU_UNCS['cos_diff']**2)

        return LPU_UNCS

    ## L2 ##
    def waterLeaving(self, LPU_UNCS, li, rho):
        sc_1 = 1 # sensitivity coefficient, 1 for LT
        sc_1 = Li**2
        sc_2 = rho**2 

        for k in LPU_UNCS['LI'].keys():  # pass all uncs through sen coeffs for LW
            LPU_UNCS['Lw'][k] = np.sqrt(
                (sc_1 * LPU_UNCS['LT'][k]**2) +
                (sc_2 * LPU_UNCS['LI'][k]**2) 
            )
            
        LPU_UNCS['rho']['Lw_units'] = np.sqrt(sc_1 * LPU_UNCS['rho']['rho_unc']**2)

    def reflectance(self, LPU_UNCS, Es, Lw):
        sc_1 = 1 / Es
        sc_2  = Lw / Es**2
        sc_3 = LI / ES  # calculated sensitivity coeff for Rho only

        for k in LPU_UNCS['Lw'].keys():
            LPU_UNCS['Rrs'][k] = np.sqrt(
                sc_1**2 * LPU['ES'][k] +
                sc_2**2 * LPU['Lw'][k]
            )
       
        LPU_UNCS['Rrs']['cos_dir'] = np.sqrt(
            sc_1**2 * LPU['ES']['cos_dir'] +
        )
        LPU_UNCS['Rrs']['cos_diff'] = np.sqrt(
            sc_1**2 * LPU['ES']['cos_diff'] +
        )  # no contribution from LW here

        LPU_UNCS['rho']['Rrs_units'] = np.sqrt(sc_3**2 * LPU_UNCS['rho']['rho_unc']**2)

    def normalised_waterLeaving(self, LPU_UNCS, f0_unc):
        for k in LPU_UNCS['Lw'].keys():
            LPU_UNCS['NLw'][k] = np.sqrt(
                LPU_UNCS['Lw'][k]**2 + 
                f0_unc**2
            )  # add in quadrature for NLw

        LPU_UNCS['rho']['NLw_units'] = np.sqrt(f0_unc**2 + LPU_UNCS['rho']['Lw_units']**2)
