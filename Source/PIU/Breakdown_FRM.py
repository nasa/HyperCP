from os import path, makedirs, umask
import numpy as np
import matplotlib.pyplot as plt

import comet_maths as cm
from typing import Optional, Union

# Source
from Source.MainConfig import MainConfig

# PIU
from Source.PIU.MeasurementFunctions import MeasurementFunctions as mf
from Source.PIU.PIUDataStore import PIUDataStore


class plottingToolsFRM:
    def __init__(self, sza, station):
        self.sza = sza
        self.station = station
        self.plot_folder = path.join(MainConfig.settings['outDir'],'Plots','L2_Uncertainty_Breakdown')

    def plotL1B(self, wvls, BD_UNCS, signal):
        for s_type in ['ES', 'LI', 'LT']:
            ## DO PLOTS ##
            self.plot(s_type, wvls, BD_UNCS[s_type]['noise'],  "noise",                   rel_to=signal[s_type])
            self.plot(s_type, wvls, BD_UNCS[s_type]['pert'],   "env perturbations",       rel_to=signal[s_type])
            self.plot(s_type, wvls, BD_UNCS[s_type]['clin'],   "non-linearity",           rel_to=signal[s_type])
            self.plot(s_type, wvls, BD_UNCS[s_type]['cSl'],    "straylight",              rel_to=signal[s_type])
            self.plot(s_type, wvls, BD_UNCS[s_type]['radcal'], "radiometric calibration", rel_to=signal[s_type])

            # post normalisation
            self.plot(s_type, wvls, BD_UNCS[s_type]['stab'], "stability", rel_to=signal[s_type])
            self.plot(s_type, wvls, BD_UNCS[s_type]['ct'],   "ct",        rel_to=signal[s_type])
            
            # plot contributions that vary between sensors
            if s_type.upper() == 'ES':
                self.plot(s_type, wvls, BD_UNCS[s_type]['cos_dir'],  "cosine (direct)",  rel_to=signal[s_type])
                self.plot(s_type, wvls, BD_UNCS[s_type]['cos_diff'], "cosine (diffuse)", rel_to=signal[s_type])
            else:
                self.plot(s_type, wvls, BD_UNCS[s_type]['pol'], "polarisation", rel_to=signal[s_type])
            
            self.save_figure(s_type)  # save the figure once all of the contributions have been added to the plot (will close the figure)
        
            self.plot_pie_FRM(s_type, wvls, BD_UNCS[s_type], signal[s_type])

    def plotL2(self, waveSubset, BD_UNCS, signal):
        ylim = [0, 5]
        for meas in ['nLw', 'Rrs']:
            UNC = BD_UNCS[meas]

            ## DO PLOTS ##
            wvls = np.array(waveSubset)
            self.plot(meas, wvls, UNC['noise'],  "noise",                   rel_to=signal[meas], ylim=ylim)
            self.plot(meas, wvls, UNC['pert'],   "env perturbations",       rel_to=signal[meas], ylim=ylim)
            self.plot(meas, wvls, UNC['clin'],   "non-linearity",           rel_to=signal[meas], ylim=ylim)
            self.plot(meas, wvls, UNC['cSl'],    "straylight",              rel_to=signal[meas], ylim=ylim)
            self.plot(meas, wvls, UNC['radcal'], "radiometric calibration", rel_to=signal[meas], ylim=ylim)

            # post normalisation
            self.plot(meas, wvls, UNC['stab'], "stability", rel_to=signal[meas], ylim=ylim)
            self.plot(meas, wvls, UNC['ct'],   "ct",        rel_to=signal[meas], ylim=ylim)
            self.plot(meas, wvls, UNC['rho'],  "rho",       rel_to=signal[meas], ylim=ylim)
            
            # plot contributions that vary between sensors
            if meas.upper() != 'LW':
                self.plot(meas, wvls, UNC['cos_dir'],  "cosine (direct)",  rel_to=signal[meas], ylim=ylim)
                self.plot(meas, wvls, UNC['cos_diff'], "cosine (diffuse)", rel_to=signal[meas], ylim=ylim)
                if meas.upper() == 'NLW':
                    self.plot(meas, wvls, UNC['f0'],  "coddington f0",  rel_to=signal[meas], ylim=ylim)
                if 'BRDF' in UNC:
                    self.plot(meas, wvls, UNC['BRDF'],  "brdf correction",  rel_to=signal[meas], ylim=ylim)

            self.plot(meas, wvls, UNC['pol'], "polarisation", rel_to=signal[meas], ylim=ylim)
            
            self.save_figure(meas, level='L2')  # save the figure once all of the contributions have been added to the plot (will close the figure)
        
            self.plot_pie_FRM(meas, wvls, BD_UNCS[meas], signal[meas], 'L2')


    def plot(self, s, x: np.array, y: np.array, name: str, rel_to: Optional[np.array]=None, unit: Optional[str]="", ylim: Optional[list]=None) -> None:
        """
        simple method for plotting uncertainties both in absolute and relative (if rel_to is given)

        :param x: x axis values
        :param y: y axis values
        :param name: name of plot for title and save name
        :param rel_to: array of values for the signal that uncertainties (param y) are to be calculated relative to, i.e. Rrs values
        :param unit: unit to be displayed on y axis of plot
        :param ylim: y limits if required
        """

        self.get_figure(s)  # create plt.figure with name based on sensor/station/cast
        if rel_to is not None:
            if len(rel_to.shape) > 1:
                y_mean = np.mean(rel_to, axis=0)  # if rel_to is a sample/PDF make sure to get the mean 
            else:  # if we have a signal to put uncs in relative units
                y_mean = rel_to  # otherwise we just use rel_to directly
            
            u_rel = (y/y_mean)*100  # calculate relative uncertainty
            plt.plot(x, u_rel, label=f"{name}")
            plt.ylabel("relative uncertainty (%)")  # unit is always % if relative uncertainties used
            if ylim is None:
                plt.ylim(0,5)  # if not ylim then default to 5% max (if relative)
            else:
                plt.ylim(*ylim)
        else:
            plt.plot(x, y, label=f"{name}")
            plt.ylabel(f"uncertainty ({unit})")

        plt.title(f"FRM Breakdown: {s}, Solar Zenith: {round(self.sza, 2)}")  # provide title with sza which is relevant for uncerstanding cosine uncs
        plt.xlabel("Wavelength (nm)")  # x lable always wavelength in uncertainty plotting in HyperCP
        
        plt.xlim(400,800)  # standard xlim, could be changed when cal/char is updated to better cover UV range

    def plot_pie_FRM(self, s: str, wavelengths: np.array, BD_UNCS: dict[str: np.array], signal: np.array, level: str='L1B') -> None:
        """
        plots a pie chart for the sensor-specific regime

        :param s: sensor name
        :param wavelengths: wavelengths for signal/uncertainties
        :param BD_UNCS: dictionary of breakdown uncertainties to be plotted
        :param signal: the signal for caluclating relative uncertainties
        :param level: string to delinate between L1B: ES, LI, LT and L2: Lw, NLw, Rrs plotting

        """

        # select appropriate keys and lable names for given level (based on how BD_UNCS is filled in BaseInstrument, HyperOCR and TriOS classes. 
        if level.upper() == 'L1B':
            keys = dict(
                ES=["noise", "pert", "radcal", "stab", "clin", "ct", "cSl", "cos_diff", "cos_dir"],
                LI=["noise", "pert", "radcal", "stab", "clin", "ct", "cSl", "pol"],
                LT=["noise", "pert", "radcal", "stab", "clin", "ct", "cSl", "pol"]
            )
            labels = dict(
                ES=["noise", "env perturbations", "calibration", "stability", "non-linearity", "temperature", "strayLight", "cosine (diffuse)", "cosine (direct)"],
                LI=["noise", "env perturbations", "calibration", "stability", "non-linearity", "temperature", "strayLight", "polarisation"],
                LT=["noise", "env perturbations", "calibration", "stability", "non-linearity", "temperature", "strayLight", "polarisation"]
            )
        else:
            keys = dict(
                Lw =["noise", "pert", "radcal", "stab", "clin", "ct", "cSl", "pol", "rho"],
                nLw=["noise", "pert", "radcal", "stab", "clin", "ct", "cSl", "pol", "rho", "f0"],
                Rrs=["noise", "pert", "radcal", "stab", "clin", "ct", "cSl", "pol", "cos_diff", "cos_dir", "rho"],
            )
            labels = dict(
                Lw =["noise", "env perturbations", "calibration", "stability", "non-linearity", "temperature", "strayLight", "polarisation", "rho"],
                nLw=["noise", "env perturbations", "calibration", "stability", "non-linearity", "temperature", "strayLight", "polarisation", "rho", "f0"],
                Rrs=["noise", "env perturbations", "calibration", "stability", "non-linearity", "temperature", "strayLight", "polarisation", "cosine (diffuse)", "cosine (direct)", "rho"],
            )
            if "BRDF" in BD_UNCS:
                keys['nLw'].append("BRDF")
                labels['nLw'].append("brdf correction")
                keys['Rrs'].append("BRDF")
                labels['Rrs'].append("brdf correction")

        indexes = [  # specific wavelengths requested by consortium partners
            np.argmin(np.abs(wavelengths - 670)),
            np.argmin(np.abs(wavelengths - 620)),
            np.argmin(np.abs(wavelengths - 560)),
            np.argmin(np.abs(wavelengths - 490)),
            np.argmin(np.abs(wavelengths - 442)),
            np.argmin(np.abs(wavelengths - 400)),
        ]  # get closest wavelength available to the specific wavelengths which are to be outputted
        for indx in indexes:  # loop through indexes
            wvl_at_indx = wavelengths[indx]  # why is numpy like this?
            fig = self.get_figure(s)
            ax = plt.gca()

            vals = [self.getpct(BD_UNCS[key], signal)[indx] for key in keys[s]]
            combined = np.sqrt(np.sum([v**2 for v in vals]))  # combined uncertainty (for estimate at wvl)

            l = ax.pie(
                vals,
                # labels=labels[s],
                autopct='%1.1f%%',
                pctdistance=1.1,
                labeldistance=1.2,
            )

            plt.title(f"{s} FRM Sensor-Specific Uncertainty: {wvl_at_indx} nm, Total: {round(combined, 2)}%", pad=40)  # y=-0.01

            # set up the lables so they aren't occluded in small slices - TODO: improve this for better clarity
            import math
            for label, t in zip(labels[s], l[1]):
                x, y = t.get_position()
                angle = int(math.degrees(math.atan2(y, x)))
                ha = "left"

                if x<0:
                    angle -= 180
                    ha = "right"

                plt.annotate(label, xy=(x,y), rotation=angle, ha=ha, va="center", rotation_mode="anchor", size=8)

            plt.tight_layout()  # for improved clarity and less overlapping of labels
            fp = path.join(self.plot_folder, f"Sensor_pie_{s}_{self.station}_{wvl_at_indx}.png")
            self.save_figure(s=s, fp=fp, legend=False, grid=False, level=level)
            # plt.close(fig)

    def get_figure(self, s: str) -> plt.figure:
        """
        Helper method to return a figure with a specific naming convention

        :param s: sensor type string
        """
        try:
            fig = plt.figure(f"{s}_{self.station}")
        except AttributeError:
            try:
                fig = plt.figure(f"{s}")
            except AttributeError:
                fig = plt.figure(s)
        
        return fig
    
    def save_figure(self, s: Optional[str]=None, fp: Optional[str]=None, legend: bool=True, grid: bool=True, level='L1B') -> None:
        """
        Helper function to save figures based on cast/station information
        
        :param fp: optional, save path for figure
        :param legend: bool to add legend to plot - default = True
        :param grid: bool to add grid to both axes of plot - default = True
        :param level: to determine which level is being saved so it can be included in savefilepath 
        """

        if (not s) and (not fp):
            print("either sensor or filepath must be defined to save a figure")
            return False

        if legend:
            plt.legend()
        if grid:
            plt.grid('both')

        if fp is None:
            try:
                fp = path.join(self.plot_folder, f"BD_plot_{level}_{s}_{self.station}.png")
            except (AttributeError, ValueError):
                fp = path.join(self.plot_folder, f"plot_sample_{s}.png")
        
        if not path.exists(self.plot_folder):
            try:
                orig_umask = umask(0)
                makedirs(self.plot_folder, 0o777)
            finally:
                umask(orig_umask)
        
        plt.savefig(fp)
        plt.close()
    
    @staticmethod
    def getpct(v1: Union[float, np.array], v2: Union[float, np.array]) -> np.array:
        """
        gets the percentage of v1 out of v2: (v1/v2) * 100%
        
        :param v1: value to be made relative
        :param v2: value that v1 is relative to
        
        """
        pct = []
        for i in range(len(v1)):
            if v2[i] != 0:  # ignore wavelengths where we do not have an output
                pct.append(v1[i]/v2[i])
            else:
                pct.append(0)  # put zero there instead of np.nan, it will be easy to avoid in plotting
        return np.array(pct) * 100  # convert to np array so we can use numpy broadcasting


class SolveLPU:
    """
    class to calculate the LPU
    :param prop: MC propagation object, required only for L1B outputs
    """

    def __init__(self, prop=None):
        if prop is not None:
            self.prop = prop
    
    @staticmethod
    def S12_alpha(PDS: PIUDataStore, s: str) -> dict[str: np.array]:
        """
        calculates breakdown uncertainties for S12 and alpha

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

    def updatedGains(self, LPU_UNCS: dict[str: np.array], PDS: PIUDataStore, s: str, sample_S12_sl_corr) -> dict[str: np.array]:
        """
        calculate breakdown uncertaintiesd for the updated radiometric gains

        :param LPU_UNCS: BreakDown Uncertainties calculated in FRM method, should contain breakdown uncertainties for above methods in class
        :param PDS: PIUDataStore object containing information on the coefficients and uncertainty inputs for calulating sensor-specific uncertainties
        :param s: sensor name
        :param sample_S12_sl_corr: straylight and non-linearity corrected signal for calculating updated gains
        """

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
        # f = signal - signal*alpha
        # sen coef 1 = 1 - 2*alpha*signal
        # sen coef 2 = signal^2

        LPU_UNCS['noise'] = np.sqrt(
            (1 - 2*alpha*signal)**2 * LPU_UNCS['noise']**2  # signal unc at this point is just dark correction uncertainty
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
        sample_lpu_nlin      = cm.generate_sample(mDraws, nlin_signal, LPU_UNCS['clin'],  'syst')
        sample_signal_no_unc = cm.generate_sample(mDraws, nlin_signal, None, None)
        c_zong_no_unc        = cm.generate_sample(mDraws, np.mean(sample_C_zong, axis=0), None, None)

        LPU_UNCS['noise'] = self._slMC(sample_lpu_dark, c_zong_no_unc)
        LPU_UNCS['clin']  = self._slMC(sample_lpu_nlin, c_zong_no_unc)
        LPU_UNCS['cSl']   = self._slMC(sample_signal_no_unc, sample_C_zong)
        
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
        uses LPU to calculate temperature uncertainty as well as propagate uncertainties through the temperature correction
        
        :param LPU_UNCS: BreakDown Uncertainties calculated in FRM method, should contain breakdown uncertainties for above methods in class
        :param PDS: PIUDataStore object containing information on the coefficients and uncertainty inputs for calulating sensor-specific uncertainties
        :param s: sensor name
        :param radcal_signal: signal with radiometric calibration applied
        """

        DATA = PDS.coeff[s]  # retrieve dictionaries for speed
        UNC = PDS.uncs[s]

        LPU_UNCS['noise']  = np.sqrt(DATA['Ct']**2 * LPU_UNCS['noise']**2)
        LPU_UNCS['clin']   = np.sqrt(DATA['Ct']**2 * LPU_UNCS['clin']**2)
        LPU_UNCS['cSl']    = np.sqrt(DATA['Ct']**2 * LPU_UNCS['cSl']**2)
        LPU_UNCS['radcal'] = np.sqrt(DATA['Ct']**2 * LPU_UNCS['radcal']**2)
        LPU_UNCS['stab']   = np.sqrt(DATA['Ct']**2 * LPU_UNCS['stab']**2)
        LPU_UNCS['ct']     = np.sqrt(radcal_signal**2 * UNC['Ct']**2)

        return LPU_UNCS

    def cosine(self, LPU_UNCS: dict[str: np.array], sample_ct_corr, dir_ratio, sample_cos_corr, sample_fhemi)-> dict[str: np.array]:
        """
        uses LPU to calculate cosine uncertainty as well as propagate uncertainties through the cosine correction. This method uses Monte Carlo instead 
        of the LPU due to complicated sensitivity coefficents
        
        :param LPU_UNCS: BreakDown Uncertainties calculated in FRM method, should contain breakdown uncertainties for above methods in class
        :param sample_ct_corr: PDF of the ct corrected signal
        :param dir_ratio: direct ratio calculated by 6S
        :param sample_cor_corr: PDF of the cosine correction
        :param sample_fhemi: PDF of the full hemispherical correction
        """

        mDraws = sample_ct_corr.shape[0]

        sample_sig_no_unc = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), None, None)
        sample_sig_dark   = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['noise'],  "rand")
        sample_sig_clin   = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['clin'],   "syst")
        sample_sig_sl     = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['cSl'],    "syst")
        sample_sig_cal    = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['radcal'], "syst")
        sample_sig_stab   = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['stab'],   "syst")
        sample_sig_ct     = cm.generate_sample(mDraws, np.mean(sample_ct_corr, axis=0), LPU_UNCS['ct'],     "syst")
        
        dir_rat_no_unc  = cm.generate_sample(mDraws, np.mean(dir_ratio), None, None)
        cos_corr_no_unc = cm.generate_sample(mDraws, np.mean(sample_cos_corr, axis=0), None, None)
        fhemi_no_unc    = cm.generate_sample(mDraws, np.mean(sample_fhemi, axis=0), None, None)
        
        LPU_UNCS['noise']    = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr, [sample_sig_dark,   dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['clin']     = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr, [sample_sig_clin,   dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['cSl']      = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr, [sample_sig_sl,     dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['radcal']   = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr, [sample_sig_cal,    dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['stab']     = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr, [sample_sig_stab,   dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['ct']       = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr, [sample_sig_ct,     dir_rat_no_unc, cos_corr_no_unc, fhemi_no_unc]))
        LPU_UNCS['cos_dir']  = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr, [sample_sig_no_unc, dir_ratio,      sample_cos_corr, fhemi_no_unc]))
        LPU_UNCS['cos_diff'] = self.prop.process_samples(None, self.prop.run_samples(mf.cos_corr, [sample_sig_no_unc, dir_ratio,      cos_corr_no_unc, sample_fhemi]))
        LPU_UNCS['cosine']   = np.sqrt(LPU_UNCS['cos_dir']**2 +  LPU_UNCS['cos_diff']**2)

        return LPU_UNCS

    def environmental_perturbations(self, LPU_UNCS: dict[str: np.array], signal: np.ndarray, pert: np.array) -> dict[str: np.array]:
        """
        get estimate of perterbations caused by environmental effects. Measured as instability (stdev) in the corrected signal 

        :param LPU_UNCS: Breakdown Uncertainties calculated in FRM method, should contain breakdown uncertainties for above methods in class
        :param signal: either signal or PDF of signal to take the standard deviation to calculate env perturbations
        :param pert: perturbation from lightDarkStats
        """

        if len(signal.shape) > 1:
            signal = np.mean(signal, axis=0)

        # environmental perturbations is caluclated relative to DN, multiply by corrected signal to recover abs units
        LPU_UNCS['pert'] = pert * signal  # signal standard deviation.

    ## L2 ##
    def waterLeaving(self, LPU_common_wb: dict[str: np.array], LPU_UNCS: dict[str: np.array], Li: np.array, rho: np.array) -> dict[str: np.array]:
        """
        Method to propagate L1B uncertainties to water leaving radiance

        :param LPU_common_wb: Breakdown uncertainties interpolated to L2 'common' wavebands
        :param LPU_UNCS: Breakdown Uncertainties calculated in FRM method, should contain breakdown uncertainties for above methods in class
        :param Li: Li signal for caluclating sensitivity coefficients
        :param rho: rho values for caluclating sensitivity coefficients
        """
        
        # f = Lt - rho*Li
        sc_1 = 1  # df/dLt
        sc_2 = Li**2  # df/drho
        sc_3 = rho**2  # df/dLi
        # signals have been interpolated to common wavebands, however LPU uncs exist at radcal wavelengths

        for k in LPU_common_wb['LI'].keys():  # pass all uncs through sen coeffs for LW
            LPU_UNCS['Lw'][k] = np.sqrt(
                (sc_1 * LPU_common_wb['LT'][k]**2) +
                (sc_3 * LPU_common_wb['LI'][k]**2) 
            )
            
        LPU_UNCS['Lw']['rho'] = np.sqrt(sc_2 * LPU_UNCS['rho']['rho_unc']**2)

    def reflectance(self, LPU_common_wb: dict[str: np.array], LPU_UNCS: dict[str: np.array], Es: np.array, Li: np.array, Lt: np.array, rho: np.array) -> dict[str: np.array]:
        """
        Method to propagate L1B uncertainties to remote sensing reflectance

        :param LPU_common_wb: Breakdown uncertainties interpolated to L2 'common' wavebands
        :param LPU_UNCS: Breakdown Uncertainties calculated in FRM method, should contain breakdown uncertainties for above methods in class
        :param Es: Es signal for caluclating sensitivity coefficients
        :param Li: Li signal for caluclating sensitivity coefficients
        :param Lt: Lt signal for caluclating sensitivity coefficients
        :param rho: rho values for caluclating sensitivity coefficients
        """
        
        # Y = f(x) ==> Rrs =  LT - rho*LI / ES
        sc_1 = 1 / Es   # df/dLT
        sc_2 = rho / Es # df/dLI
        sc_3 = Li / Es  # df/drho
        sc_4 = (Lt - rho*Li) / Es**2  # df/dES

        for k in LPU_UNCS['Lw'].keys():
            if k != 'pol' and k != 'rho':
                LPU_UNCS['Rrs'][k] = np.sqrt(
                    sc_1**2 * LPU_common_wb['LT'][k]**2 +
                    sc_2**2 * LPU_common_wb['LI'][k]**2 + 
                    sc_4**2 * LPU_common_wb['ES'][k]**2
                )
            
        LPU_UNCS['Rrs']['pol'] = np.sqrt(
            # es does not have pol
            sc_1**2 * LPU_common_wb['LT']['pol']**2 + 
            sc_2**2 * LPU_common_wb['LI']['pol']**2
        )

        LPU_UNCS['Rrs']['cos_dir'] = np.sqrt(
            sc_4**2 * LPU_common_wb['ES']['cos_dir']**2
        )
        LPU_UNCS['Rrs']['cos_diff'] = np.sqrt(
            sc_4**2 * LPU_common_wb['ES']['cos_diff']**2
        )  # no contribution from LW here

        LPU_UNCS['Rrs']['rho'] = np.sqrt(sc_3**2 * LPU_UNCS['rho']['rho_unc']**2)

    def normalised_waterLeaving(self, LPU_UNCS: dict[str: np.array], rrs, f0, f0_unc: np.array) -> dict[str: np.array]:
        """
        Method to propagate L1B uncertainties to normalised water leaving radiance

        :param LPU_UNCS: Breakdown Uncertainties calculated in FRM method, should contain breakdown uncertainties for above methods in class
        :param Li: Li signal for caluclating sensitivity coefficients
        :param rho: rho values for caluclating sensitivity coefficients
        """
        
        for k in LPU_UNCS['Rrs'].keys():
            LPU_UNCS['nLw'][k] = np.sqrt(
               f0**2 * LPU_UNCS['Rrs'][k]**2
            )  # add in quadrature for NLw

        LPU_UNCS['nLw']["f0"] = np.sqrt(rrs**2 * f0_unc**2)
