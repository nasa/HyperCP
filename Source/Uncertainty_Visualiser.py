# docs and typing
import os
from abc import ABC
from typing import Optional, Union

# packages
import matplotlib.pyplot as plt
import numpy as np
from punpy import MCPropagation

from Source.Uncertainty_Analysis import Propagate
from Source.MainConfig import MainConfig
from Source.ConfigFile import ConfigFile


# I think it may be best to put something in controller.py which then calls plotting from utilities or another file.
class UncertaintyGUI(ABC):
    def __init__(self, _mcp: Union[Propagate, MCPropagation] =None):
        super().__init__()
        if _mcp is None:
            mcp = Propagate(M=100, cores=1)
        elif isinstance(_mcp, MCPropagation):
            mcp = Propagate()
            mcp.MCP = _mcp
        else:
            mcp = _mcp
        self._engine = UncertaintyEngine(mcp)
        del mcp, _mcp  # free up memory

        self.plot_folder = os.path.join(MainConfig.settings['outDir'],'Plots','L2_Uncertainty_Breakdown')
        if not os.path.exists(self.plot_folder):
            os.makedirs(self.plot_folder)

    def pie_plot_class(self, mean_vals, uncs, wavelengths, cast, ancGrp):
        is_negative = np.any([ x < 0 for x in mean_vals])
        if is_negative:
            print('WARNING: Negative uncertainty potential')

        if ConfigFile.settings['fL1bCal'] == 1:
            regime = 'Factory'
        else:
            regime = 'Class'
        results, values = self._engine.breakdown_Class(mean_vals, uncs, False)
        if np.any(values['ES'] < 0):
            print('WARNING: Negative uncertainty potential')
        if np.any(values['LI'] < 0):
            print('WARNING: Negative uncertainty potential')
        if np.any(values['LT'] < 0):
            print('WARNING: Negative uncertainty potential')
        labels = dict(
            ES=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "cosine"],
            LI=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
            LT=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"]
        )

        # build table of anc data
        aod = ancGrp.datasets['AOD'].columns['AOD'][0]
        rel_az = ancGrp.datasets['REL_AZ'].columns['REL_AZ'][0]
        saa = ancGrp.datasets['SOLAR_AZ'].columns['SOLAR_AZ'][0]
        sza = ancGrp.datasets['SZA'].columns['SZA'][0]
        ws = ancGrp.datasets['WINDSPEED'].columns['WINDSPEED'][0]
        sst = ancGrp.datasets['SST'].columns['SST'][0]

        col_labels = ['value']
        row_labels = [
            'Aerosol Optical Depth',
            'Relative Azimuth',
            'Solar Azimuth',
            'Solar Zenith',
            'Wind Speed',
            'Water Temperature'
        ]
        table_vals = [
            [aod],
            [rel_az],
            [saa],
            [sza],
            [ws],
            [sst]
        ]

        for sensor in results.keys():
            indexes = [
                np.argmin(np.abs(wavelengths[sensor] - 675)),
                np.argmin(np.abs(wavelengths[sensor] - 560)),
                np.argmin(np.abs(wavelengths[sensor] - 442))
            ]
            for indx in indexes:
                wvl_at_indx = wavelengths[sensor][indx]  # why is numpy like this?
                fig, ax = plt.subplots()

                # the_table = plt.table(cellText=table_vals,
                #                       colWidths=[0.1],
                #                       rowLabels=row_labels,
                #                       colLabels=col_labels,
                #                       loc="best",
                #                       )
                # plt.text(0.1, 0.5, 'Ancillary Data', size=12)

                ax.pie(
                    [self._engine.getpct(results[sensor][key], values[sensor])[indx] for key in labels[sensor]],
                    labels=labels[sensor],
                    autopct='%1.1f%%'
                )
                plt.title(f"{sensor} {regime} Based Uncertainty Components at {wvl_at_indx}nm")
                fp = os.path.join(self.plot_folder,f"pie_{sensor}_{cast}_{wvl_at_indx}.png")
                plt.savefig(fp)
                plt.close(fig)

    def pie_plot_class_l2(self, rrs_vals, lw_vals, rrs_uncs, lw_uncs, wavelengths, cast, ancGrp):
        if ConfigFile.settings['fL1bCal'] == 1:
            regime = 'Factory'
        else:
            regime = 'Class'
        # build table of anc data
        aod = ancGrp.datasets['AOD'].columns['AOD'][0]
        rel_az = ancGrp.datasets['REL_AZ'].columns['REL_AZ'][0]
        saa = ancGrp.datasets['SOLAR_AZ'].columns['SOLAR_AZ'][0]
        sza = ancGrp.datasets['SZA'].columns['SZA'][0]
        ws = ancGrp.datasets['WINDSPEED'].columns['WINDSPEED'][0]
        sst = ancGrp.datasets['SST'].columns['SST'][0]

        col_labels = ['value']
        row_labels = [
            'Aerosol Optical Depth',
            'Relative Azimuth',
            'Solar Azimuth',
            'Solar Zenith',
            'Wind Speed',
            'Water Temperature'
        ]
        table_vals = [
            [aod],
            [rel_az],
            [saa],
            [sza],
            [ws],
            [sst]
        ]

        results, values = self._engine.breakdown_Class_L2(rrs_vals, lw_vals, rrs_uncs, lw_uncs, False)
        labels = dict(
            Lw=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "rho"],
            Rrs=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "cosine", "rho"]
        )
        for product in results.keys():
            indexes = [
                np.argmin(np.abs(wavelengths - 675)),
                np.argmin(np.abs(wavelengths - 560)),
                np.argmin(np.abs(wavelengths - 442))
            ]
            for indx in indexes:
                wvl_at_indx = wavelengths[indx]  # why is numpy like this?
                fig, ax = plt.subplots()

                # the_table = plt.table(cellText=table_vals,
                #                       colWidths=[0.1],
                #                       rowLabels=row_labels,
                #                       colLabels=col_labels,
                #                       loc='best')
                # plt.text(12, 3.4, 'Ancillary Data', size=8)

                try:
                    ax.pie([self._engine.getpct(results[product][key], values[product])[indx] for key in labels[product]],
                           labels=labels[product], autopct='%1.1f%%')
                except ValueError:
                    # todo discuss a better solution to issue #262 with programming team
                    print("all zeros encountered, cannot plot pie chart")

                plt.title(f"{product} {regime} Based Uncertainty Components at {wvl_at_indx}nm")
                fp = os.path.join(self.plot_folder,f"pie_{product}_{cast}_{wvl_at_indx}.png")
                plt.savefig(fp)
                # todo: put different wavelengths in a subplot instead of making separate plots
                # todo: make table of ancillary data to include with plots
                plt.close(fig)

    def plot_class(self, mean_vals, uncs, wavelengths, cast=""):
        results, values = self._engine.breakdown_Class(mean_vals, uncs, True)
        keys = dict(
            ES=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "cosine"],
            LI=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
            LT=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"]
        )

        # now we plot the result
        for sensor in ['ES', 'LI', 'LT']:
            plt.figure(f"{sensor}_{cast}")
            for key in keys[sensor]:
                plt.plot(wavelengths[sensor], self._engine.getpct(results[sensor][key], values[sensor]), label=key)
            plt.xlabel("Wavelengths")
            plt.xlim(400, 890)
            plt.ylabel("Relative Uncertainty (%)")
            plt.ylim(0, 15)
            plt.title(f"Class-Based branch Breakdown of {sensor} Uncertainties")
            plt.legend()
            plt.grid()
            if isinstance(cast, list):
                cast = cast[0]
            fp = os.path.join(self.plot_folder,f"spectral_{sensor}_{cast}.png")
            plt.savefig(fp)
            plt.close(f"{sensor}_{cast}")

    def plot_class_L2(self, rrs_vals, lw_vals, rrs_uncs, lw_uncs, wavelengths, cast=""):
        results, values = self._engine.breakdown_Class_L2(rrs_vals, lw_vals, rrs_uncs, lw_uncs, True)
        keys = dict(
            Lw=["noise", "rho", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
            Rrs=["noise", "rho", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "cosine"]
        )
        # now we plot the result
        for product in ['Lw', 'Rrs']:
            plt.figure(f"{product}_{cast}")
            for key in keys[product]:
                plt.plot(wavelengths, self._engine.getpct(results[product][key], values[product]), label=key)
            plt.xlabel("Wavelengths")
            plt.xlim(400,700)
            plt.ylabel("Relative Uncertainty (%)")
            plt.ylim(0,15)
            plt.title(f"Class-Based branch Breakdown of {product} Uncertainties")
            plt.legend()
            plt.grid()
            if isinstance(cast, list):
                cast = cast[0]
            fp = os.path.join(self.plot_folder,f"spectral_{product}_{cast}.png")
            plt.savefig(fp)
            plt.close(f"{product}_{cast}")

    def plot_unc_from_sample_1D(
        self, sample: np.array, x: np.array, fig_name: Optional[str] = "breakdown", name: Optional[str] = None,
            xlim: Optional[tuple] = None, save: Union[bool, dict] = False
    ):
        """
        Plots the relative uncertainty for a provided PDF

        :param sample: PDF
        :param x: wavelengths to go on x-axis
        :param fig_name: name for the figure, "breakdown by default"
        :param name: name for the plot/saved figure
        :param xlim: xlimit in the format (x_min, x_max)
        """
        means = np.mean(sample, axis=0)
        abs_unc_k1 = self._engine.punpy_MCP.MCP.process_samples(None, sample)
        rel_unc = ((abs_unc_k1*1e10) / (means*1e10)) * 100

        fig = plt.figure(fig_name)

        plt.plot(x, rel_unc, label=f"{name}")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Relative Uncertainty (%)")

        # apply x-limit if provided
        if xlim is not None and (xlim[1] > xlim[0]):
            xmin = xlim[0]
            xmax = xlim[1]
        else:
            xmin = 400
            xmax = 800

        # get ylimit from data
        plt.xlim(xmin, xmax)
        # rel_unc_in_lim = np.max(rel_unc[np.argmin(np.abs(x - xmin)):np.argmin(np.abs(x - xmax))])
        # ymax = np.max(rel_unc_in_lim)
        plt.ylim(0, 4)  # TODO: create flexible solution for ylim
        if save:
            plt.grid()
            plt.legend()
            if isinstance(save, dict):
                t = save['time'].split(' ')
                try:
                    plt.title(f"{fig_name.replace('_', ' ')} {save['instrument']} {' '.join([t[2], t[1], t[-1], t[-2]])}")
                except IndexError:
                    plt.title(f"{fig_name.replace('_', ' ')} {save['instrument']}")
                sp = f"{fig_name}_{save['cal_type']}_{save['time']}_{save['instrument']}_unc_in_pct.png"
                sp.replace(':', '-').replace(' ', '_')
                fp = os.path.join(self.plot_folder,sp)
                plt.savefig(fp)
                plt.close(fig)
            else:
                plt.title(f"{fig_name}")
                fp = os.path.join(self.plot_folder,f"{fig_name}_unc_in_pct.png")
                plt.savefig(fp)
                plt.close(fig)

    def plot_val_from_sample_1D(
            self, sample: np.array, x: np.array, name: Optional[str] = None, xlim: Optional[tuple] = None
    ):
        """
        Plots the value with shaded uncertainties for a given PDF

        :param sample: PDF
        :param x: wavelengths to go on x-axis
        :param name: name for the plot/saved figure
        :param xlim: xlimit in the format (x_min, x_max)
        """
        means = np.mean(sample, axis=0)
        abs_unc_k1 = self._engine.punpy_MCP.MCP.process_samples(None, sample)
        # rel_unc = (abs_unc_k1 / means) * 100

        if name is not None:
            fig = plt.figure(name)
        else:
            fig = plt.figure()

        plt.plot(x, means, 'k-')
        plt.fill_between(
            x,
            means - abs_unc_k1,
            means + abs_unc_k1
        )
        plt.xlabel("Wavelength (nm)")
        plt.ylabel(f"{name} with Uncertainty")
        plt.title(f"Plot of {name}")

        # apply x-limit if provided
        if xlim is not None and (xlim[1] > xlim[0]):
            xmin = xlim[0]
            xmax = xlim[1]
        else:
            xmin = 400
            xmax = 800

        # get ylimit from data
        plt.xlim(xmin, xmax)
        means_in_lim = np.max(means[np.argmin(np.abs(x - xmin)):np.argmin(np.abs(x - xmax))])
        ymax = np.max(means_in_lim)
        plt.ylim(0, ymax + (2*abs_unc_k1))
        fp = os.path.join(self.plot_folder,f"{name}_mean_with_abs_unc.png")
        plt.savefig(fp)
        plt.close(fig)

        # for 2D samples
        # means = xr.DataArray(data=means, dims=("x", "y"), coords={"x": x})
        # u_rel = xr.DataArray(data=rel_unc, dims=("x", "y"), coords={"x": x})

    def plot_FRM(
            self, 
            node, 
            uncGrp, 
            raw_grps, 
            raw_slices, 
            stats,  
            rhoScalar, 
            rhoVec, 
            rhoUNC, 
            waveSubset
        ):

        L1B, L2 = self._engine.breakdown_FRM_HyperOCR( 
            node, 
            uncGrp, 
            raw_grps, 
            raw_slices, 
            stats, 
            rhoScalar, 
            rhoVec, 
            rhoUNC, 
            waveSubset
        )


class UncertaintyEngine(ABC):
    def __init__(self, punpy_prop_obj):
        """
        :param MCPropagation: Monte Carlo Propagation object from Uncertainty_Analysis.py
        """
        super().__init__()
        self.punpy_MCP = punpy_prop_obj
    # add absolute to LW/Rrs to make sure we propagate uncertainty for cases where we have negative values 
    def breakdown_Class(self, mean_values: list, uncertainty: list, cumulative: bool = True):
        """

        """
        keys = dict(
            ES=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "cosine"],
            LI=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
            LT=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"]
        )
        output = {"ES": {}, "LI": {}, "LT": {}}
        vals = {}
        # nul = np.zeroes(len(uncertainty[0]))
        uncs = np.zeros(np.asarray(uncertainty).shape)
        # generate class based uncertaitnies from 0 and adding each contribution in turn
        is_negative = np.any([ x < 0 for x in uncertainty])
        if is_negative:
            print('WARNING: Negative uncertainty potential')
        is_negative = np.any([ x < 0 for x in mean_values])
        if is_negative:
            print('WARNING: Negative uncertainty potential')
        vals['ES'], vals['LI'], vals['LT'] = self.punpy_MCP.instruments(*mean_values) # get values to make uncs relative
        if np.any(vals['ES'] < 0):
            print('WARNING: Negative uncertainty potential')
        if np.any(vals['LI'] < 0):
            # NOTE: This is where negatives are found in my data. Is this LI, or LI_unc?
            # If LI, is this only used in convertion to relative LI_unc?
            # If LI, is it measurement data or MC distributions around measurements? 
            #   If LI and MC distributions, set to zero. If not, set to absolute value IFF outside of critical bands,
            #       else dump the ensemble. Could check for this earlier in the process.   
            # 
            # NOTE: Update: These are (ir)radiances but they are model outputs from MC runs.
            #  i.e., taking an abs value (in sensible bands) is harmless         
            print('WARNING: Negative uncertainty potential')
        if np.any(vals['LT'] < 0):
            print('WARNING: Negative uncertainty potential')
        for indx, i in enumerate([0, 6, 9, 12, 18, 15, 21]):
            if indx == 0:
                uncs[0:6] = uncertainty[0:6]
            else:
                uncs[i:i+3] = uncertainty[i:i+3]
            (
                output['ES'][keys['ES'][indx]],
                output['LI'][keys['LI'][indx]],
                output['LT'][keys['LT'][indx]]
            ) = self.punpy_MCP.propagate_Instrument_Uncertainty(mean_values, uncs)
            if not cumulative:
                uncs = np.zeros(np.asarray(uncertainty).shape)  # reset uncertaitnies

        return output, vals

    def breakdown_Class_L2(self, rrs_vals: list, lw_vals: list, rrs_uncs: list, lw_uncs: list, cumulative: bool = True):
        """
        Breakdown uncertainties for L2 products when running in class based mode
        """

        keys = ["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "cosine", "rho"]
        keys_lw = ["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "rho"]
        output = {"Lw": {}, "Rrs": {}}
        vals = {}
        uRrs = np.zeros(np.asarray(rrs_uncs).shape)

        # generate class based uncertaitnies from 0 and adding each contribution in turn
        vals['Rrs'] = self.punpy_MCP.RRS(*rrs_vals) # get values to make uncs relative
        for indx, i in enumerate([0, 4, 7, 10, 16, 13, 19, 21, 1]):
            if indx == 0:
                uRrs[0:4] = rrs_uncs[0:4]
                uRrs[1] = np.zeros(len(rrs_uncs[1]))
            elif indx == 8:
                uRrs[1] = rrs_uncs[1]  # add rho
            elif indx == 6:
                uRrs[i:i + 2] = rrs_uncs[i:i + 2]
            elif indx == 7:
                uRrs[i] = rrs_uncs[i]
            else:
                uRrs[i:i+3] = rrs_uncs[i:i+3]

            output['Rrs'][keys[indx]] = self.punpy_MCP.Propagate_RRS_HYPER(rrs_vals, uRrs)

            if not cumulative:
                uRrs = np.zeros(np.asarray(rrs_uncs).shape)  # reset uncertaitnies

        vals['Lw'] = self.punpy_MCP.Lw(*lw_vals)
        uLw = np.zeros(np.asarray(lw_uncs).shape)
        for indx, i in enumerate([0, 3, 5, 7, 11, 9, 13, 1]):
            if indx == 0:
                uLw[0] = lw_uncs[0]
                uLw[2] = lw_uncs[2]
            elif indx == 7:
                uLw[1] = lw_uncs[1]  # add rho
            else:
                uLw[i:i + 2] = lw_uncs[i:i + 2]

            output['Lw'][keys_lw[indx]] = self.punpy_MCP.Propagate_Lw_HYPER(lw_vals, uLw)

            if not cumulative:
                uLw = np.zeros(np.asarray(lw_uncs).shape)  # reset uncertaitnies

        # screen negative values (they can result in negative relative uncertainties)
        for s in ['Lw', 'Rrs']:
            for i, val in enumerate(vals[s]):
                if val < 0:
                    vals[s][i] = 0
        return output, vals

    @staticmethod
    def getpct(val1, val2):
        pct = []
        for i in range(len(val1)):
            if val2[i] != 0:  # ignore wavelengths where we do not have an output
                pct.append(val1[i]/val2[i])
            else:
                pct.append(0)  # put zero there instead of np.nan, it will be easy to avoid in plotting
        return np.array(pct) * 100  # convert to np array so we can use numpy broadcasting


    def breakdown_FRM_HyperOCR(
            self, 
            node, 
            uncGrp, 
            raw_grps, 
            raw_slices, 
            stats,  
            rhoScalar, 
            rhoVec, 
            rhoUNC, 
            waveSubset
        ):
        """
        
        """
        from Source.ProcessInstrumentUncertainties import HyperOCR, Trios
        from Source.HDFGroup import HDFGroup
        
        if ConfigFile.settings['SensorType'].lower() == "trios":
            instrument = Trios()
        elif ConfigFile.settings['SensorType'].lower() == "seabird":
            instrument = HyperOCR()

        L1B = {}; L2 = {}
        for i, comp in enumerate([
                ('Noise', 0), 
                ('RADCAL_CAL', ''),  
                ('RADCAL_LAMP', ''),  # data[3] updated radcal gain
                ('RADCAL_PANEL', ''),  # data[3] updated radcal gain
                ('Nlin', ['6', '8']), # RADCAL_CAL data 7 & 9 S1, S2
                ('STRAYDATA_UNCERTAINTY', 0), 
                ('Stability', 0), 
                ('TEMPDATA', ['ES_TEMPERATURE_UNCERTAINTIES',
                              'LI_TEMPERATURE_UNCERTAINTIES',
                              'LT_TEMPERATURE_UNCERTAINTIES'
                              ]), # TEMPDATA_CAL needs to not include class based
                ('POLDATA_CAL', 0), 
                ('ANGDATA_UNCERTAINTY', 0),
                ('Glint', 0),
            ]):  # breakdown of corrections also
            # adjust uncertainties
            uncGrp_adjusted = HDFGroup()
            uncGrp_adjusted.copy(uncGrp)  # make a copy of the uncertainty group

            if comp == 'no_unc':  # 'Noise':
                adj_stats = stats
            elif comp == 'Glint':
                rhoUNC_adj = rhoUNC
            else:
                adj_stats = {k: {sk: np.zeros(len(v)) for sk, v in stats[k].items()} for k in stats.keys()}
                rhoUNC_adj = np.zeros(len(rhoUNC))
        
            for k, ds in uncGrp.datasets.items():
                # if 'CLASS' not in k.upper():
                if comp in k.upper():
                    uncGrp_adjusted.datasets[k].copy(ds)
                else:
                    for wvl, col in uncGrp_adjusted.datasets[k].columns.items():
                        uncGrp_adjusted.datasets[k].columns[wvl] = np.zeros(len(col))
                    uncGrp_adjusted.datasets[k].columnsToDataset()

            L1B[comp] = instrument.FRM(node, uncGrp_adjusted, raw_grps, raw_slices, adj_stats, np.array(waveSubset, float))
            # for cumulative add in quadrature at the end
            
            L2[comp] = instrument.FRM_L2(rhoScalar, rhoVec, rhoUNC_adj, waveSubset, L1B[comp])
        
        return L1B, L2

    def breakdown_FRM_TriOS(self, uncGrp, raw_grps, raw_slices, stats, newWaveBands):
        """
        """
        from Source.ProcessInstrumentUncertainties import Trios
        instrument = Trios()

    def breakdown_FRM_DALEC(self, uncGrp, raw_grps, raw_slices, stats, newWaveBands):
        """
        """
        from Source.ProcessInstrumentUncertainties import Dalec
        instrument = Dalec()

# this is my Pie-Chart widget that I made for another project. It would introduce a pyqtchart dependency.
# pyqtchart must have the same version as pyqt5

# import PyQt5
# from PyQt5.QtWidgets import (
#     QPushButton, QAbstractScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem
# )
# from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
# from PyQt5.QtGui import QIcon, QColor, QFont
#
# class piChart(QWidget):
#     def __init__(self, vals, tot, sensor, *args, **kwargs):
#         super(piChart, self).__init__(*args, **kwargs)
#         self._isopen = False
#
#         # create pi chart
#         self.series = QPieSeries()
#         self.series.append("Noise", self.getpct(tot, vals["stdev"]))
#         self.series.append("Calibration", self.getpct(tot, vals["Cal"]))
#         self.series.append("Stability", self.getpct(tot, vals["Stab"]))
#         self.series.append("Non-Linearity", self.getpct(tot, vals["Lin"]))
#         self.series.append("Temperature", self.getpct(tot, vals["cT"]))
#         self.series.append("Straylight", self.getpct(tot, vals["Stray"]))
#
#         if sensor == 'ES':
#             self.series.append("Cosine", self.getpct(tot, vals["Cos"]))
#         else:
#             self.series.append("Polarisation", self.getpct(tot, vals["Pol"]))
#
#         # set slice properties
#         l_font = QFont()
#         l_font.setPixelSize(10)
#         l_font.setPointSize(10)
#         self.series.setHoleSize(0.35)
#         for i, slce in enumerate(self.series.slices()):
#             colours = np.linspace(0, 359, len(self.series.slices()))
#             slce.setBrush(QColor.fromHsv(*[int(colours[i]), 180, 210]))
#             slce.setLabelFont(l_font)
#
#         chart = QChart()
#         chart.addSeries(self.series)
#         chart.setAnimationOptions(QChart.SeriesAnimations)
#         title_font = QFont()
#         title_font.setPixelSize(18)
#         title_font.setPointSize(18)
#         chart.setTitleFont(title_font)
#         chart.setTitle(f"Uncertainty Breakdown {sensor}")
#         # self.legend = chart.legend()
#         # self.legend.font.pointsize = 20
#         chartview = QChartView(chart)
#
#         vbox = QVBoxLayout()
#         vbox.addWidget(chartview)
#
#         self.setLayout(vbox)
#
#     def setExploded(self):
#         # slice = QPieSlice()
#         if not self._isopen:
#             for slce in self.series.slices():
#                 slce.setLabelVisible(True)
#                 slce.setExploded(True)
#                 self._isopen = True
#         else:
#             for slce in self.series.slices():
#                 slce.setLabelVisible(False)
#                 slce.setExploded(False)
#                 self._isopen = False
#
#     @staticmethod
#     def getpct(val1, val2):
#         pct = []
#         for i in range(len(val1)):
#             pct.append(val2[i]/val1[i])
#         return np.mean(pct) * 100
#
#     def init(self):
#         pass
#
#     def setBehaviour(self):
#         pass