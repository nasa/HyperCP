# docs and typing
from abc import ABC
from typing import Optional, Union

# packages
import matplotlib.pyplot as plt
import numpy as np

class Show_Uncertainties(ABC):
    def __init__(self, punpy_prop_obj):
        """
        :param punpy_prop_obj: Monte Carlo Propagation object from punpy package
        """
        super().__init__()
        self.punpy_MCP = punpy_prop_obj
        # mpl.use('qtagg')

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
        abs_unc_k1 = self.punpy_MCP.process_samples(None, sample)
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
                plt.savefig(sp.replace(':', '-').replace(' ', '_'))
                fig.close()
            else:
                plt.title(f"{fig_name}")
                plt.savefig(f"{fig_name}_unc_in_pct.png")
                fig.close()

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
        abs_unc_k1 = self.punpy_MCP.process_samples(None, sample)
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
        plt.savefig(f"{name}_mean_with_abs_unc.png")

        # for 2D samples
        # means = xr.DataArray(data=means, dims=("x", "y"), coords={"x": x})
        # u_rel = xr.DataArray(data=rel_unc, dims=("x", "y"), coords={"x": x})

    def plot_all_FRM(self):
        """
        To plot every sample from FRM processing - To be implemented -
        """
        pass

    def plot_breakdown_Class(self, mean_values: list, uncertainty: list, wavelengths: dict, cumulative: bool = True,
                             cast: str = ''):
        """

        """
        keys = ["stdev", "Cal", "Stab", "Lin", "cT", "Stray", "pol"]
        output = {"ES": {}, "LI": {}, "LT": {}}
        vals = {}
        # nul = np.zeroes(len(uncertainty[0]))
        uncs = np.zeros(np.asarray(uncertainty).shape)
        # generate class based uncertaitnies from 0 and adding each contribution in turn
        vals['ES'], vals['LI'], vals['LT'] = self.punpy_MCP.instruments(*mean_values) # get values to make uncs relative
        for indx, i in enumerate([0, 6, 9, 12, 18, 15, 21]):
            if indx == 0:
                uncs[0:6] = uncertainty[0:6]
            else:
                uncs[i:i+3] = uncertainty[i:i+3]
            (
                output['ES'][keys[indx]],
                output['LI'][keys[indx]],
                output['LT'][keys[indx]]
            ) = self.punpy_MCP.propagate_Instrument_Uncertainty(mean_values, uncs)
            if not cumulative:
                uncs = np.zeros(np.asarray(uncertainty).shape)  # reset uncertaitnies

        # now we plot the result

        for sensor in ['ES', 'LI', 'LT']:

            plt.figure(f"{sensor}_{cast}")
            for key in keys:
                plt.plot(wavelengths[sensor], (output[sensor][key] / vals[sensor]) * 100, label=key)
            plt.xlabel("Wavelengths")
            plt.ylabel("Relative Uncertainties (%)")
            plt.title(f"Class-Based branch Breakdown of {sensor} Uncertainties")
            plt.legend()
            plt.grid()
            if isinstance(cast, list):
                cast = cast[0]
            plt.savefig(f"{sensor}_{cast}_class_breakdown.png")
