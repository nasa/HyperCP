# Packages
from os import path, makedirs, umask

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

# PIU
from Source.PIU import PIUDataStore as pds


class plottingToolsCB:

    def __init__(self, PDS: pds, sensor: str, prop: Optional[MCPropagation]=None):
        self.Data = PDS  # TODO: get vals and uncs from self.Data and not inputs to the class_plotting funcs
        self.s = sensor
        # self.adjusted = None  # not implemented yet
        self.engine = prop if prop is not None else MCPropagation(100, parallel_cores=1)
        self.plot_folder = path.join(MainConfig.settings['outDir'],'Plots','L2_Uncertainty_Breakdown')


    def plot_CB_spectral(self, BD_UNCS, BD_VALS, wavelengths, level='L1B'):
        if level == 'L1B':
            keys = dict(
                ES=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "cosine"],
                LI=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
                LT=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"]
            )
            sensors = ['ES', 'LI', 'LT']
        else:
            keys = dict(
                Lw =["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "rho"],
                Rrs=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "cosine", "rho"],
            )
            sensors = ['Lw', 'Rrs']

        # now we plot the result
        sensors = ['ES'] if ConfigFile.settings["SensorType"].lower() == "trios es only" else ['ES', 'LI', 'LT']
        for sensor in sensors:
            plt.figure(f"{sensor}_{self.Data.cast}")
            for key in keys[sensor]:
                plt.plot(wavelengths[sensor], 
                PlotMaths.getpct(BD_UNCS[sensor][key], BD_VALS[sensor]), 
                label=key
                )
            
            plt.xlabel("Wavelengths")
            plt.xlim(350, 900)
            plt.ylabel("Relative Uncertainty (%)")
            plt.ylim(0, 15)
            plt.title(f"Class-Based branch Breakdown of {sensor} Uncertainties")
            plt.legend()
            plt.grid()
            
            fp = path.join(self.plot_folder,f"spectral_{sensor}_{self.Data.cast}.png")
            if not path.exists(self.plot_folder):
                makedirs(self.plot_folder)
            plt.savefig(fp)
            plt.close(f"{sensor}_{self.Data.cast}")

    def pie_plot_class(self, BD_UNCS, BD_VALS, wavelengths, ancGrp) -> dict[str: np.array]:
        if ConfigFile.settings["fL1bCal"] == 1:
            regime = 'Factory'
        else:
            regime = 'Class'
        
        if np.any(BD_VALS['ES'] < 0):
            print('WARNING: Negative uncertainty potential')
        if np.any(BD_VALS['LI'] < 0):
            print('WARNING: Negative uncertainty potential')
        if np.any(BD_VALS['LT'] < 0):
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

        for sensor in BD_UNCS.keys():
            indexes = [  # todo: add extra wavelengths
                np.argmin(np.abs(wavelengths[sensor] - 670)),
                np.argmin(np.abs(wavelengths[sensor] - 620)),
                np.argmin(np.abs(wavelengths[sensor] - 560)),
                np.argmin(np.abs(wavelengths[sensor] - 490)),
                np.argmin(np.abs(wavelengths[sensor] - 442)),
                np.argmin(np.abs(wavelengths[sensor] - 400)),
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
                    [PlotMaths.getpct(BD_UNCS[sensor][key], BD_VALS[sensor])[indx] for key in labels[sensor]],
                    labels=labels[sensor],
                    autopct='%1.1f%%'
                )
                plt.title(f"{sensor} {regime} Based Uncertainty Components at {wvl_at_indx}nm")
                fp = path.join(self.plot_folder, f"pie_{sensor}_{self.Data.cast}_{wvl_at_indx}.png")
                self.save_figure(fp, legend=False, grid=False)
                plt.close(fig)
                
        return BD_UNCS

    def pie_plot_class_l2(self, BD_UNCS, BD_VALS, wavelengths, cast, ancGrp) -> dict[str: np.array]:
        if ConfigFile.settings["fL1bCal"] == 1:
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

        labels = dict(
            Lw=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "rho"],
            Rrs=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "cosine", "rho"]
        )
        for product in BD_UNCS.keys():
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
                fig, ax = plt.subplots()

                # the_table = plt.table(cellText=table_vals,
                #                       colWidths=[0.1],
                #                       rowLabels=row_labels,
                #                       colLabels=col_labels,
                #                       loc='best')
                # plt.text(12, 3.4, 'Ancillary Data', size=8)

                # try:
                ax.pie([PlotMaths.getpct(BD_UNCS[product][key], BD_VALS[product])[indx] for key in labels[product]],
                        labels=labels[product], autopct='%1.1f%%')
                # except ValueError:
                #     # todo discuss a better solution to issue #262 with programming team
                #     print("all zeros encountered, cannot plot pie chart")

                plt.title(f"{product} {regime} Based Uncertainty Components at {wvl_at_indx}nm")
                fp = path.join(self.plot_folder,f"pie_{product}_{cast}_{wvl_at_indx}.png")
                self.save_figure(fp, legend=False, grid=False)
                plt.close(fig)

        return BD_UNCS

    def plot_sample(self, x: np.array, sample: np.ndarray, name: str, rel_to: Optional[np.array]=None, cal: Optional[np.array]=None):
        if rel_to is None:
            y_mean = np.mean(sample, axis=0)
        elif len(rel_to.shape) > 1:
            y_mean = np.mean(rel_to, axis=0)
        else:
            y_mean = rel_to

        y = self.engine.process_samples(None, sample)

        if cal is not None:
            y_mean = y_mean/cal  # multiply uncertainties by cal to convert into irradiance/radiance

        u_rel = (y/np.abs(y_mean))*100 
        try:
            plt.figure(f"{self.s}_{self.Data.cast}_{self.Data.station}")
        except AttributeError:
            try:
                plt.figure(f"{self.s}_{self.Data.cast}")
            except AttributeError:
                plt.figure(self.s)

        plt.title(f"FRM Breakdown: {self.s}")
        plt.plot(x, u_rel, label=f"{name}")
        
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("relative uncertainty (%)")
        plt.xlim(400,800)
        plt.ylim(0,5)
    
    def save_figure(self, fp: Optional[str]=None, legend: bool=True, grid:bool=True):
        if legend:
            plt.legend()
        if grid:
            plt.grid('both')

        if fp is None:
            try:
                fp = path.join(self.plot_folder, f"BD_plot_{self.s}_{self.Data.cast}_{self.Data.station}.png")
            except (AttributeError, ValueError):
                fp = path.join(self.plot_folder, f"plot_sample_{self.s}.png")
        
        if not path.exists(self.plot_folder):
            try:
                orig_umask = umask(0)
                makedirs(self.plot_folder, 0o777)
            finally:
                umask(orig_umask)
        
        plt.savefig(fp)
    

class PlotMaths:
    
    def __init__(self):
        pass

    @staticmethod
    def classBased(prop: MCPropagation, vals: list, uncs: list, cul: bool=False):
        """
        
        """
        keys = dict(
            ES=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "cosine"],
            LI=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"],
            LT=["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol"]
        )
        UNCS = {"ES": {}, "LI": {}, "LT": {}}
        VALS = {}
        p_uncs = np.zeros_like(np.asarray(uncs))
        VALS['ES'], VALS['LI'], VALS['LT'] = prop.instruments(*vals) # get values to make uncs relative
        
        for indx, i in enumerate([0, 6, 9, 12, 18, 15, 21]):
            if indx == 0:
                p_uncs[0:6] = uncs[0:6]
            else:
                p_uncs[i:i+3] = uncs[i:i+3]
            (
                UNCS['ES'][keys['ES'][indx]],
                UNCS['LI'][keys['LI'][indx]],
                UNCS['LT'][keys['LT'][indx]]
            ) = prop.propagate_Instrument_Uncertainty(vals, p_uncs)
            if not cul:
                p_uncs = np.zeros_like(np.asarray(uncs))  # reset uncertaitnies

        return UNCS, VALS

    @staticmethod
    def classBasedL2(prop: MCPropagation, lw_vals: list, rrs_vals: list, lw_uncs: list, rrs_uncs: list, cul: bool=False):
        # generate class based uncertaitnies from 0 and adding each contribution in turn
        UNCS = {"Lw": {}, "Rrs": {}}
        VALS = {}
        
        # Get RRS uncertainty contributions
        keys_lw  = ["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "rho"]
        VALS['Lw'] = prop.Lw(*lw_vals)
        uLw = np.zeros_like(np.asarray(lw_uncs))
        for indx, i in enumerate([0, 3, 5, 7, 11, 9, 13, 1]):
            if indx == 0:
                uLw[0] = lw_uncs[0]
                uLw[2] = lw_uncs[2]
            elif indx == 7:
                uLw[1] = lw_uncs[1]  # add rho
            else:
                uLw[i:i + 2] = lw_uncs[i:i + 2]

            UNCS['Lw'][keys_lw[indx]] = prop.Propagate_Lw_HYPER(lw_vals, uLw)

            if not cul:
                uLw = np.zeros_like(np.asarray(lw_uncs))  # reset uncertaitnies

        # Get RRS uncertainty contributions
        keys_rrs = ["noise", "Cal", "Stab", "Lin", "cT", "Stray", "pol", "cosine", "rho"]
        uRrs = np.zeros_like(np.asarray(rrs_uncs))
        VALS['Rrs'] = prop.RRS(*rrs_vals) # get values to make uncs relative
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

            UNCS['Rrs'][keys_rrs[indx]] = prop.Propagate_RRS_HYPER(rrs_vals, uRrs)

            if not cul:
                uRrs = np.zeros_like(np.asarray(rrs_uncs))  # reset uncertaitnies

        # screen negative values (they can result in negative relative uncertainties)
        for meas in ['Lw', 'Rrs']:
            for i, val in enumerate(VALS[meas]):
                if val < 0:
                    VALS[meas][i] = 0

        return UNCS, VALS

    @staticmethod
    def getpct(v1, v2):
        pct = []
        for i in range(len(v1)):
            if v2[i] != 0:  # ignore wavelengths where we do not have an output
                pct.append(v1[i]/v2[i])
            else:
                pct.append(0)  # put zero there instead of np.nan, it will be easy to avoid in plotting
        return np.array(pct) * 100  # convert to np array so we can use numpy broadcasting
