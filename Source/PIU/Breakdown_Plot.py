from os import path, makedirs, umask
from datetime import datetime as dt
from itertools import cycle
import numpy as np
from punpy import MCPropagation
import matplotlib.pyplot as plt

# linting
from typing import Optional, Union

# Source
from Source.MainConfig import MainConfig
from Source.ConfigFile import ConfigFile
from Source.utils.loggingHCP import writeLogFileAndPrint


class plottingTools:
    """ for plotting uncertainty breakdowns """
    _ALL_LABELS = [
        "noise", 
        "env perturbations", 
        "calibration", 
        "stability", 
        "non-linearity", 
        "temperature", 
        "strayLight", 
        "polarisation", 
        "rho", 
        "f0",
        "brdf correction",    
        "cosine (direct)",
        "cosine (diffuse)",
    ]

    cb_translation = {
        "noise": "noise",
        "pert": "env perturbations",
        "Cal": "calibration",
        "Stab": "stability",
        "Lin": "non-linearity",
        "cT": "temperature",
        "Stray": "strayLight",
        "cosine (direct)": "cosine",
        "cosine (diffuse)": None,
        "pol": "polarisation",
        "rho": "rho",
        "f0": "f0",
        "BRDF": "brdf correction",
    }

    def __init__(self, sza, station, engine: Optional[MCPropagation] = None):
        self.sza = sza
        self.station = station
        self.engine = engine if engine is not None else MCPropagation(100, parallel_cores=0)
        self.plot_folder = path.join(
            MainConfig.settings["outDir"], "Plots", "L2_Uncertainty_Breakdown"
        )

        palette = plt.cm.tab20(np.linspace(0, 1, 20))
        color_cycle = cycle(palette)
        self.LABEL_COLORS = {
            k: v for k,v in zip(self._ALL_LABLES, color_cycle)
        }

    def plot(self, wavelengths, BD_UNCS, signal) -> None:
        for meas in ['ES', 'LI', 'LT', 'nLw', 'Rrs']:
            
            # TODO: plot spectral
            
            self.plot_bar(
                s=meas, 
                x=wavelengths,
                BD_UNCS=BD_UNCS[meas],
                signal=signal[meas],
            )

    def plot_bar(
            self, 
            s: str, 
            wavelengths: np.array, 
            BD_UNCS: dict[str, np.array], 
            signal: np.array, 
        ) -> None:
        """
        plots a bar chart for the sensor-specific regime

        :param s: sensor name
        :param wavelengths: wavelengths for signal/uncertainties
        :param BD_UNCS: dictionary of breakdown uncertainties to be plotted
        :param signal: the signal for caluclating relative uncertainties

        """
        # select appropriate keys and lable names for given level (based on how BD_UNCS is filled in BaseInstrument, HyperOCR and TriOS classes.
        if s.upper() in ["ES", "LI", "LT"]:
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
        elif s.upper() in ["NLW", "RRS"]:
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

            # --- Build figure and axis ---
            fig = self.get_figure(s)
            fig.set_size_inches(12, 8)
            ax = plt.gca()

            # --- Data ---
            vals = [self.getpct(BD_UNCS[key], signal)[indx] for key in keys[s]]

            labels_list = labels[s]

            # Safety: handle empty or all-zero data
            if not vals or sum(vals) == 0:
                ax.text(0.5, 0.5, "No data to display", ha='center', va='center', transform=ax.transAxes)
                plt.title(f"{s} FRM Sensor-Specific Uncertainty: {wvl_at_indx} nm, Total: 0%", pad=20)
                plt.axis('off')
                plt.tight_layout()
                return

            # Combined uncertainty
            combined = (sum(v**2 for v in vals)) ** 0.5

            # --- Sort by value descending for readability --- #
            sorted_data = sorted(zip(vals, labels_list), key=lambda t: t[0], reverse=True)
            vals_sorted, labels_sorted = zip(*sorted_data)
            colors_sorted = [self.LABEL_COLORS[lab] for lab in labels_sorted]

            # --- Plot horizontal bars --- #
            ax.barh(labels_sorted, vals_sorted, color=colors_sorted)

            # --- Add percentage labels to the right of each bar --- #
            ref_at_indx = []
            x_offset = max(vals_sorted) * 0.01  # small offset so text doesn’t touch the bar
            for i, v in enumerate(vals_sorted):
                # pct = (v / combined) * 100
                pct = (v**2 / combined**2) * 100
                ax.text(v + x_offset, i, f'{pct:.1f}%', va='center', fontsize=11)
                ref_at_indx.append(round(pct,1))

            # --- Styling --- #
            ax.invert_yaxis()  # largest at top
            ax.set_xlabel(f"Uncertainty relative to {s} (%)")
            ax.set_ylabel("Contributors")
            plt.title(f"{s} FRM Sensor-Specific Uncertainty: {wvl_at_indx} nm, Total: {round(combined, 2)}%", pad=20)

            # --- Add text explaining calculation of combined uncertainty --- #
            textstr = f"Bars represent relative uncertainty in {s} signal (abscissa) at {wvl_at_indx} nm. " \
                    f"Percentages displayed by each bar represent the contribution of the component to the variance of {s}, " \
                    r"where uncertainty is a positive square root of variance $u_{c}^{2} =$ " + "\u03A3" + r"$_{i=0}^{N} u_{i}^{2}$"
            plt.gcf().text(0.02, 0.04,
                            textstr,
                            fontsize=12,
                            color='black',
                            wrap=True,
                            bbox={'facecolor': 'white', 'alpha': 1, 'pad': 5}
            )

            plt.tight_layout()
            plt.subplots_adjust(bottom=0.16)  # create space for text

            fp = path.join(self.plot_folder, f"{s}_SB_bar_{self.station}_{wvl_at_indx}.png")
            self.save_figure(s=s, fp=fp, legend=False, grid=False)

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

    def save_figure(
        self,
        s: Optional[str],
        fp: Optional[str] = None,
        legend: bool = True,
        grid: bool = True,
    ):
        if (not s) and (not fp):
            print("either sensor or filepath must be defined to save a figure")
            return False

        if legend:
            plt.legend()
        if grid:
            plt.grid("both")

        if fp is None:
            try:
                # fp = path.join(self.plot_folder, f"BD_plot_CB_{s}_{self.station}.png")
                fp = path.join(self.plot_folder, f"{s}_CB_pie_{self.station}.png")
            except (AttributeError, ValueError):
                fp = path.join(self.plot_folder, f"plot_sample_{s}.png")

        if not path.exists(self.plot_folder):
            orig_umask = None
            try:
                orig_umask = umask(0)
                makedirs(self.plot_folder, 0o777)
            finally:
                umask(orig_umask)

        plt.savefig(fp)
        plt.close()

    @staticmethod
    def getpct(v1: Union[list, np.array], v2: Union[list, np.array]) -> np.array:
        """
        gets the percentage of v1 out of v2: (v1/v2) * 100%
        
        :param v1: value to be made relative
        :param v2: value that v1 is relative to
        
        """
        pct = []
        for i, v1i in enumerate(v1):
            if v2[i] != 0:  # ignore wavelengths where we do not have an output
                pct.append(v1i/v2[i])
            else:
                pct.append(0)  # put zero there instead of np.nan, it will be easy to avoid in plotting
        return np.array(pct) * 100  # convert to np array so we can use numpy broadcasting

