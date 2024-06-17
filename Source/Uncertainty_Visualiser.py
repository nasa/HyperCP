# docs and typing
from abc import ABC, abstractmethod
from typing import Optional

# packages
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr


class show_Uncertainties(ABC):
    def __init__(self, punpy_prop_obj):
        """
        :param punpy_prop_obj: Monte Carlo Propagation object from punpy package
        """
        super().__init__()
        self.punpy_MCP = punpy_prop_obj
        mpl.use('qtagg')

    def plot_unc_from_sample_1D(
            self, sample: np.array, waveSubset: np.array, name: Optional[str] = None, xlim: Optional[tuple] = None
    ):
        means = np.mean(sample, axis=0)
        abs_unc_k1 = self.punpy_MCP.process_samples(None, sample)
        rel_unc = (abs_unc_k1 / means) * 100

        if waveSubset is not None:
            x = waveSubset
        else:
            x = np.arange(len(means))
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
        if xlim is not None and (xlim[1] > xlim[0]):
            xmin = xlim[0]
            xmax = xlim[1]
        else:
            xmin = 400
            xmax = 800

        plt.xlim(xmin,xmax)
        means_in_lim = np.max(means[np.argmin(np.abs(waveSubset - xmin)):np.argmin(np.abs(waveSubset - xmax))])
        ymax = np.max(means_in_lim)
        plt.ylim(0, ymax + (2*abs_unc_k1))
        plt.savefig(f"{name}.png")

        # for 2D samples
        # means = xr.DataArray(data=means, dims=("x", "y"), coords={"x": x})
        # u_rel = xr.DataArray(data=rel_unc, dims=("x", "y"), coords={"x": x})
