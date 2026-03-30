''' Generate and plot spectral and pie breakdowns for class-based FRM uncertainties'''
# Packages
from os import path, makedirs, umask
from datetime import datetime
from itertools import cycle

# linting
from typing import Optional

# Maths
import numpy as np
from punpy import MCPropagation

# Plotting
import matplotlib.pyplot as plt

# Source
from Source.MainConfig import MainConfig
from Source.ConfigFile import ConfigFile
from Source.utils.loggingHCP import writeLogFileAndPrint

# PIU
# from Source.PIU import PIUDataStore as pds


class plottingToolsCB:
    '''Class for class-based uncertainty plotting tools'''
    _ALL_LABLES = [
        "noise", 
        "pert", 
        "Cal", 
        "Stab", 
        "Lin", 
        "cT", 
        "Stray", 
        "pol", 
        "cosine", 
        "rho", 
        "f0",
        "BRDF",
    ]

    def __init__(self, sza, station, prop: Optional[MCPropagation] = None):
        self.sza = sza
        self.station = station
        self.engine = prop if prop is not None else MCPropagation(100, parallel_cores=1)
        self.plot_folder = path.join(
            MainConfig.settings["outDir"], "Plots", "L2_Uncertainty_Breakdown"
        )

        palette = plt.cm.tab20(np.linspace(0, 1, 20))
        color_cycle = cycle(palette)
        self.LABEL_COLORS = {
            k: v for k,v in zip(self._ALL_LABLES, color_cycle)
        }

    def PlotL1B(self, node, wavelengths, BD_UNCS, es, li, lt):
        try:
            BD_VALS = {"ES": es, "LI": li, "LT": lt}
            # print('Plotting L1B product uncertainty breakdown')
            self.plot_CB_spectral(BD_UNCS, BD_VALS, wavelengths)
            self.plot_bar_classBased(
                BD_UNCS, BD_VALS, wavelengths, node.getGroup("ANCILLARY")
            )
        except ValueError as err:
            writeLogFileAndPrint(
                f"unable to run uncertainty breakdown plots, error: {err}"
            )

    def PlotL2(self, node, wavelengths, BD_UNCS, nlw, rrs):
        acqTime = datetime.strptime(
            node.attributes["TIME-STAMP"], "%a %b %d %H:%M:%S %Y"
        )

        cast = acqTime.strftime("%Y%m%d_%H%M%S") #

        try:
            BD_VALS = {
                "nLw": nlw,
                "Rrs": rrs,
            }
            # print(f'Plotting L2 product uncertainty breakdown for {cast}')
            self.plot_CB_spectral(BD_UNCS, BD_VALS, wavelengths, level="L2")
            self.plot_bar_class_l2(
                BD_UNCS,
                BD_VALS,
                wavelengths,  # pass radcal wavelengths
                cast,
                node.getGroup("ANCILLARY"),
            )
        except ValueError as err:
            writeLogFileAndPrint(
                f"unable to run uncertainty breakdown plots for {cast}, with error: {err}"
            )

    def plot_CB_spectral(self, BD_UNCS, BD_VALS, wavelengths, level="L1B"):
        if "L1B" in level:
            keys = dict(
                ES=["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "cosine"],
                LI=["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
                LT=["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
            )
            sensors = (
                ["ES"]
                if ConfigFile.settings["SensorType"].lower() == "trios es only"
                else ["ES", "LI", "LT"]
            )
        else:
            keys = dict(
                # Lw =["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "rho"],
                Rrs=["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "cosine", "rho"],
                nLw=["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "cosine", "rho", "f0"],
            )
            sensors = ["nLw", "Rrs"]
            if "BRDF" in BD_UNCS["Rrs"]:
                keys["nLw"].append("BRDF")
                keys["Rrs"].append("BRDF")

        # now we plot the result
        for sensor in sensors:
            plt.figure(f"{sensor}_{self.station}")
            for key in keys[sensor]:
                plt.plot(
                    wavelengths,
                    PlotMaths.getpct(BD_UNCS[sensor][key], BD_VALS[sensor]),
                    label=key,
                )

            plt.xlabel("Wavelengths")
            plt.xlim(350, 900)
            plt.ylabel("Relative Uncertainty (%)")
            plt.ylim(0, 5)
            plt.title(f"Class-Based branch Breakdown of {sensor} Uncertainties")
            plt.legend()
            plt.grid()

            # fp = path.join(self.plot_folder, f"spectral_CB_{sensor}_{self.station}.png")
            fp = path.join(self.plot_folder, f"{sensor}_CB_spectral_{self.station}.png")
            if not path.exists(self.plot_folder):
                makedirs(self.plot_folder)
            plt.savefig(fp)
            plt.close(f"{sensor}_{self.station}")

    def plot_bar_classBased(self, BD_UNCS, BD_VALS, wavelengths, ancGrp) -> dict[str, np.array]:
        # if ConfigFile.settings["fL1bCal"] == 1:
        #     regime = "Factory"
        # else:
        #     regime = "Class"

        labels = dict(
            ES=["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "cosine"],
            LI=["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
            LT=["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
        )

        for s, keys in labels.items():
            # TODO: add extra wavelengths
            indexes = [
                np.argmin(np.abs(wavelengths - 670)),
                np.argmin(np.abs(wavelengths - 620)),
                np.argmin(np.abs(wavelengths - 560)),
                np.argmin(np.abs(wavelengths - 490)),
                np.argmin(np.abs(wavelengths - 442)),
                np.argmin(np.abs(wavelengths - 400)),
            ]
            for indx in indexes:
                wvl_at_indx = wavelengths[indx]  # why is numpy like this?
                # fig, ax = plt.subplots()

                # --- Build figure and axis ---
                fig = plt.figure(s)
                fig.set_size_inches(12, 8)
                ax = plt.gca()

                # --- Data ---
                vals = [PlotMaths.getpct(BD_UNCS[s][key], BD_VALS[s])[indx] for key in keys]

                labels_list = labels[s]

                # Safety: handle empty or all-zero data
                if not vals or sum(vals) == 0:
                    ax.text(0.5, 0.5, "No data to display", ha='center', va='center', transform=ax.transAxes)
                    plt.title(f"{s} FRM Class-Based Uncertainty: {wvl_at_indx} nm, Total: 0%", pad=20)
                    plt.axis('off')
                    plt.tight_layout()
                    return

                # --- Sort by value descending for readability ---
                sorted_data = sorted(zip(vals, labels_list), key=lambda t: t[0], reverse=True)
                vals_sorted, labels_sorted = zip(*sorted_data)
                colors_sorted = [self.LABEL_COLORS[lab] for lab in labels_sorted]

                # --- Plot horizontal bars ---
                ax.barh(labels_sorted, vals_sorted, color=colors_sorted)

                # --- Add percentage labels to the right of each bar ---

                # Combined uncertainty
                combined = (np.sum(v**2 for v in vals)) ** 0.5

                # relative uncertainties
                # unc component / total signal
                # unc components add in quad / signal
                x_offset = max(vals_sorted) * 0.01  # small offset so text doesn’t touch the bar
                ref_at_indx = []
                for i, v in enumerate(vals_sorted):
                    # pct = (v / combined) * 100
                    pct = (v**2 / combined**2) * 100
                    ax.text(v + x_offset, i, f'{pct:.1f}%', va='center', fontsize=11)
                    ref_at_indx.append(round(pct,1) + 1)

                # --- Styling --- #
                ax.invert_yaxis()  # largest at top
                ax.set_xlabel(f"Uncertainty relative to {s} (%)")
                ax.set_ylabel("Contributors")
                plt.title(f"{s} FRM Class-Based Uncertainty: {wvl_at_indx} nm, Total: {round(combined, 2)}%", pad=40)

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

                fp = path.join(
                    self.plot_folder,
                    f"{s}_CB_bar_{self.station}_{wvl_at_indx}.png",
                )
                self.save_figure(s=s, fp=fp, legend=False, grid=False)
                plt.close(fig)

        return BD_UNCS

    def plot_bar_class_l2(
        self, BD_UNCS, BD_VALS, wavelengths, cast, ancGrp
    ) -> Optional[bool]:
        # if ConfigFile.settings["fL1bCal"] == 1:
        #     regime = "Factory"
        # else:
        #     regime = "Class"

        labels = dict(
            # Lw =["noise", "pert", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "rho"],
            Rrs=["noise","pert","Cal","Stab","Lin","cT","Stray","pol","cosine","rho",],
            nLw=["noise","pert","Cal","Stab","Lin","cT","Stray","pol","cosine","rho","f0",],
        )
        if "BRDF" in BD_UNCS["Rrs"]:
            labels["nLw"].append("BRDF")
            labels["Rrs"].append("BRDF")

        for s, keys in labels.items():
            indexes = [
                np.argmin(np.abs(wavelengths - 670)),
                np.argmin(np.abs(wavelengths - 620)),
                np.argmin(np.abs(wavelengths - 560)),
                np.argmin(np.abs(wavelengths - 490)),
                np.argmin(np.abs(wavelengths - 442)),
                np.argmin(np.abs(wavelengths - 400)),
            ]
            for indx in indexes:
                wvl_at_indx = wavelengths[indx]  # why is numpy like this?

                # --- Build figure and axis ---
                fig = plt.figure(s)
                ax = plt.gca()
                fig.set_size_inches(12, 8)

                # --- Data ---
                vals = [PlotMaths.getpct(BD_UNCS[s][key], BD_VALS[s])[indx] for key in keys]

                labels_list = labels[s]
                # colors = [LABEL_COLORS[lab] for lab in labels_list]

                # Safety: handle empty or all-zero data
                if not vals or sum(vals) == 0:
                    ax.text(0.5, 0.5, "No data to display", ha='center', va='center', transform=ax.transAxes)
                    plt.title(f"{s} FRM Class-Based Uncertainty: {wvl_at_indx} nm, Total: 0%", pad=20)
                    plt.axis('off')
                    plt.tight_layout()
                    return False

                # --- Sort by value descending for readability ---
                sorted_data = sorted(zip(vals, labels_list), key=lambda t: t[0], reverse=True)
                vals_sorted, labels_sorted = zip(*sorted_data)
                colors_sorted = [self.LABEL_COLORS[lab] for lab in labels_sorted]

                # --- Plot horizontal bars --- #
                ax.barh(labels_sorted, vals_sorted, color=colors_sorted)

                # --- Combined uncertainty --- #
                combined = (sum(v**2 for v in vals)) ** 0.5

                # --- Add percentage labels to the right of each bar --- #
                ref_at_indx = []
                x_offset = max(vals_sorted) * 0.01  # small offset so text doesn’t touch the bar
                for i, v in enumerate(vals_sorted):
                    # pct = (v / combined) * 100
                    pct = (v**2 / combined**2) * 100
                    ax.text(v + x_offset, i, f'{pct:.1f}%', va='center', fontsize=11)
                    ref_at_indx.append(pct)

                # --- Styling --- #
                ax.invert_yaxis()  # largest at top
                ax.set_xlabel(f"Uncertainty relative to {s} (%)")
                ax.set_ylabel("Contributors")
                plt.title(f"{s} FRM Class-Based Uncertainty: {wvl_at_indx} nm, Total: {round(combined, 2)}%", pad=20)

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

                fp = path.join(
                    self.plot_folder, f"{s}_CB_bar_{cast}_{wvl_at_indx}.png"
                )
                self.save_figure(s=s, fp=fp, legend=False, grid=False)
                plt.close(fig)

    def plot_sample(
        self,
        s: str,
        x: np.array,
        sample: np.ndarray,
        name: str,
        rel_to: Optional[np.array] = None,
        cal: Optional[np.array] = None,
    ):
        if rel_to is None:
            y_mean = np.mean(sample, axis=0)
        elif len(rel_to.shape) > 1:
            y_mean = np.mean(rel_to, axis=0)
        else:
            y_mean = rel_to

        y = self.engine.process_samples(None, sample)

        if cal is not None:
            y_mean = (
                y_mean / cal
            )  # multiply uncertainties by cal to convert into irradiance/radiance

        u_rel = PlotMaths.getpct(y, y_mean)
        try:
            plt.figure(f"{s}_{self.station}")
        except AttributeError:
            try:
                plt.figure(f"{s}")
            except AttributeError:
                plt.figure(s)

        plt.title(f"FRM Breakdown: {s}")
        plt.plot(x, u_rel, label=f"{name}")

        plt.xlabel("Wavelength (nm)")
        plt.ylabel("relative uncertainty (%)")
        plt.xlim(400, 800)
        plt.ylim(0, 5)

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


class PlotMaths:

    def __init__(self):
        pass

    @staticmethod
    def classBased(prop: MCPropagation, vals: list, uncs: list, cul: bool = False):
        """ """
        keys = dict(
            ES=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "cosine"],
            LI=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
            LT=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
        )
        UNCS = {"ES": {}, "LI": {}, "LT": {}}
        VALS = {}
        p_uncs = np.zeros_like(np.asarray(uncs))
        VALS["ES"], VALS["LI"], VALS["LT"] = prop.instruments(
            *vals
        )  # get values to make uncs relative

        # Add uncertainty elements incrementally. Indexes refer to elements listed in keys above, as they appear in vals and uncs
        for indx, i in enumerate([0, 6, 9, 12, 18, 15, 21]):
            if indx == 0:
                p_uncs[0:6] = uncs[0:6]
            else:
                p_uncs[i : i + 3] = uncs[i : i + 3]
            try:
                (
                    UNCS["ES"][keys["ES"][indx]],
                    UNCS["LI"][keys["LI"][indx]],
                    UNCS["LT"][keys["LT"][indx]],
                ) = prop.propagate_Instrument_Uncertainty(vals, p_uncs)
            except ValueError as err:
                # from Source.utils.loggingHCP import writeLogFileAndPrint
                writeLogFileAndPrint(
                    f"Error in Class Based Breakdown - {keys['ES'][indx]}: {err}"
                )
                (
                    UNCS["ES"][keys["ES"][indx]],
                    UNCS["LI"][keys["LI"][indx]],
                    UNCS["LT"][keys["LT"][indx]],
                ) = prop.propagate_Instrument_Uncertainty(
                    vals, p_uncs, corr_between=False
                )

            if not cul:
                p_uncs = np.zeros_like(np.asarray(uncs))  # reset uncertaitnies

        return UNCS, VALS

    @staticmethod
    def classBasedL2(
        prop: MCPropagation,
        lw_vals: list,
        rrs_vals: list,
        lw_uncs: list,
        rrs_uncs: list,
        cul: bool = False,
    ):
        # generate class based uncertaitnies from 0 and adding each contribution in turn
        UNCS = {"Lw": {}, "Rrs": {}}
        VALS = {}

        # Get RRS uncertainty contributions
        keys_lw = ["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "rho"]
        VALS["Lw"] = prop.Lw(*lw_vals)
        uLw = np.zeros_like(np.asarray(lw_uncs))
        for indx, i in enumerate([0, 3, 5, 7, 11, 9, 13, 1]):
            if indx == 0:
                uLw[0] = lw_uncs[0]
                uLw[2] = lw_uncs[2]
            elif indx == 7:
                uLw[1] = lw_uncs[1]  # add rho
            else:
                uLw[i : i + 2] = lw_uncs[i : i + 2]

            try:
                UNCS["Lw"][keys_lw[indx]] = prop.Propagate_Lw_HYPER(lw_vals, uLw)
            except ValueError as err:
                writeLogFileAndPrint(
                    f"Error in Class Based Breakdown - {keys_lw[indx]}: {err}"
                )
                UNCS["Lw"][keys_lw[indx]] = prop.Propagate_Lw_HYPER(
                    lw_vals, uLw, corr_between=False
                )
            if not cul:
                uLw = np.zeros_like(np.asarray(lw_uncs))  # reset uncertaitnies

        # Get RRS uncertainty contributions
        keys_rrs = [
            "noise",
            "Cal",
            "Stab",
            "Lin",
            "cT",
            "Stray",
            "pol",
            "cosine",
            "rho",
        ]
        uRrs = np.zeros_like(np.asarray(rrs_uncs))
        VALS["Rrs"] = prop.RRS(*rrs_vals)  # get values to make uncs relative
        for indx, i in enumerate([0, 4, 7, 10, 16, 13, 19, 21, 1]):
            if indx == 0:
                uRrs[0:4] = rrs_uncs[0:4]
                uRrs[1] = np.zeros(len(rrs_uncs[1]))
            elif indx == 8:
                uRrs[1] = rrs_uncs[1]  # add rho
            elif indx == 6:
                uRrs[i : i + 2] = rrs_uncs[i : i + 2]
            elif indx == 7:
                uRrs[i] = rrs_uncs[i]
            else:
                uRrs[i : i + 3] = rrs_uncs[i : i + 3]

            try:
                UNCS["Rrs"][keys_rrs[indx]] = prop.Propagate_RRS_HYPER(rrs_vals, uRrs)
            except ValueError as err:
                writeLogFileAndPrint(f"Error in Class Based Breakdown - {keys_rrs[indx]}: {err}")
                UNCS["Rrs"][keys_rrs[indx]] = prop.Propagate_RRS_HYPER(
                    rrs_vals, uRrs, corr_between=False
                )
            if not cul:
                uRrs = np.zeros_like(np.asarray(rrs_uncs))  # reset uncertaitnies

        # screen negative values (they can result in negative relative uncertainties)
        for meas in ["Lw", "Rrs"]:
            for i, val in enumerate(VALS[meas]):
                if val < 0:
                    VALS[meas][i] = 0

        return UNCS, VALS

    @staticmethod
    def getpct(v1, v2):
        pct = []
        for i,v1i in enumerate(v1):
            if v2[i] != 0:  # ignore wavelengths where we do not have an output
                pct.append(v1i / v2[i])
            else:
                pct.append(
                    0
                )  # put zero there instead of np.nan, it will be easy to avoid in plotting
        return (
            np.array(pct) * 100
        )  # convert to np array so we can use numpy broadcasting
