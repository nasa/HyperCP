import os
import numpy as np

# for analysis NPL developed packages
import punpy
import Source.matheo.band_integration as band_integration
from Source.matheo.srf_utils import (
    return_iter_srf,
    return_band_centres,
    return_band_names,
)
from Source.matheo.punpy_util import func_with_unc
from typing import Optional, Union, Tuple, List, Iterable, Callable, Iterator

# zhangWrapper
import collections
from Source import ZhangRho, PATH_TO_DATA

# M99 Rho
from Source.HDFRoot import HDFRoot
from Source.Utilities import Utilities
from Source.ConfigFile import ConfigFile
from Source.RhoCorrections import RhoCorrections

# TODO remove this part and properly address the warning
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class Propagate:
    """
    Class to contain all uncertainty analysis to be used in HyperInSPACE

    used to contain mesurement functions as well as functions to appy uncertainty analsys to HyperInSPACE products:
    inputs, processes and derrivatives.

    path: Str - output path for results to be written too
    M: Int - number of monte carlo draws
    cores: Int - punpy parallel_cores option (see documentation) Set None to ignore, 1 is default.
    """
    MCP: punpy.MCPropagation
    corr_fp: str = os.path.join(PATH_TO_DATA, 'correlation_mats.csv')
    corr_matrices: dict = {}

    def __init__(self, M: int = 10000, cores: int = 1):
        if isinstance(cores, int):
            self.MCP = punpy.MCPropagation(M, parallel_cores=cores)
        else:
            self.MCP = punpy.MCPropagation(M)

    # Main functions
    def propagate_Instrument_Uncertainty(self, mean_vals: list[np.array], uncertainties: list[np.array]) -> np.array:
        """
        :param mean_vals:  list (normally numpy array) of input means matching the arguments of
        Source.Uncertainty_Analysis.Propagate.instruments() - [ESLIGHT, ESDARK, LILIGHT, LIDARK, LTLIGHT, LTDARK,
                                                               ESCal, LICal, LTCal,
                                                               ESStab, LIStab, LTStab,
                                                               ESLin, LILin, LTLin,
                                                               ESStray, LIStray, LTStray,
                                                               EST, LIT, LTT,
                                                               LIPol, LTPol, ESCos]
        :param uncertainties: list (normally numpy array) of input uncertainties matching the order of mean_vals

        :Return: absolute uncertainty [es, li, lt]
        """

        corr_matrix = np.array([
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        ])

        corr_list = ['rand', 'rand', 'rand', 'rand', 'rand', 'rand', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst',
                     'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst']

        unc = self.MCP.propagate_random(self.instruments,
                                        mean_vals,
                                        uncertainties,
                                        corr_between=corr_matrix,
                                        corr_x=corr_list,
                                        output_vars=3)

        # separate uncertainties and sensor values from their lists - for clarity
        Es_unc, Li_unc, Lt_unc = [unc[i] for i in range(len(unc))]

        return Es_unc, Li_unc, Lt_unc

    def Propagate_Lw(self, mean_vals: list[np.array], uncertainties: list[np.array]) -> np.array:
        """
        :param mean_vals: list (normally numpy array) of input means matching the arguments of
        Source.Uncertainty_Analysis.Propagate.Lw() - [lt, rhoVec, li,
                                                      c2, c3,
                                                      clin2, clin3,
                                                      cstab2, cstab3,
                                                      cstray2, cstray3,
                                                      cT2, cT3,
                                                      cpol1, cpol2]
        :param uncertainties: list (normally numpy array) of input uncertainties matching the order of mean_vals

        :return: Lw uncertainty
        """
        corr_matrix = np.array([
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0]
            ])

        return self.MCP.propagate_random(self.Lw,
                                         mean_vals,
                                         uncertainties,
                                         corr_between=corr_matrix)

    def Propagate_RRS(self, mean_vals: list[np.array], uncertainties: list[np.array]) -> np.array:
        """
        :param mean_vals: list (normally numpy array) of input means matching the arguments of
        Source.Uncertainty_Analysis.Propagate.Rrs() - [lt, rhoVec, li, es,
                                                       c1, c2, c3,
                                                       clin1, clin2, clin3,
                                                       cstab1, cstab2, cstab3,
                                                       cstray1, cstray2, cstray3,
                                                       cT1, cT2, cT3,
                                                       cpol1, cpol2, ccos]
        :param uncertainties: list (normally numpy array) of input uncertainties matching the order of mean_vals

        :return: Rrs uncertainty


            will be replaced in the near future - for pixel by pixel method """
        corr_matrix = np.array([
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
            ],dtype=np.float64)
        corr_list = ['rand', 'syst', 'rand', 'rand', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst',
                     'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst']

        return self.MCP.propagate_standard(self.RRS,
                                           mean_vals,
                                           uncertainties,
                                           corr_between=corr_matrix,
                                           corr_x=corr_list)

    def band_Conv_Uncertainty(self, mean_vals: list[np.array], uncertainties: list[np.array], platform: str) -> np.array:
        """
        :param mean_vals: list (normally numpy array) of input values matching matheo.band_Conv_Sensor_[SENSOR]
        function - [Hyper_Rrs, wvl, Band cetral wavelengths, Band width]
        :param uncertainties: list (normally numpy array) of input uncertainties matching mean_vals
        :param platform: name of the sensor to be convolved

        :return: relative Rrs uncertainty per spectral band
        """
        if platform.upper() == "S3A" or platform.lower().rstrip().replace('-','') == "sentinel3a":
            func = self.band_Conv_Sensor_S3A
        elif platform.upper() == "S3B" or platform.lower().rstrip().replace('-','') == "sentinel3b":
            func = self.band_Conv_Sensor_S3B
        elif platform.upper() == "MOD-A" or platform.lower().rstrip().replace('-','') == "eos-aqua":
            func = self.band_Conv_Sensor_AQUA
        elif platform.upper() == "MOD-T" or platform.lower().rstrip().replace('-', '') == "eos-terra":
            func = self.band_Conv_Sensor_TERRA
        elif platform.upper() == "VIIRS" or platform.lower().rstrip().replace('-', '') == "noaa-20":
            func = self.band_Conv_Sensor_NOAA
        else:
            msg = "sensor not supported"
            print(msg)
            return False
        return self.MCP.propagate_standard(func,
                                           mean_vals,
                                           uncertainties,
                                           corr_x=['syst', None])

    # Rho propagation methods
    def M99_Rho_Uncertainty(self, mean_vals: list[np.array], uncertainties: list[np.array]) -> np.array:
        """
        :param mean_vals: list (normally numpy array) of input means matching the arguments of
        Source.Uncertainty_Analysis.Propagate.rhoM99()
        - [windSpeedMean, SZAMean, relAzMean]
        :param uncertainties: list (normally numpy array) of input uncertainties matching the order of mean_vals

        :return: Mobley99 method rho uncertainty
        """
        return self.MCP.propagate_random(self.rhoM99,
                                         mean_vals,
                                         uncertainties,
                                         corr_x=["rand", "rand", "rand"]
                                         )

    def Zhang_Rho_Uncertainty(self, mean_vals: list[np.array], uncertainties: list[np.array]) -> np.array:
        """
        :param mean_vals: list (normally numpy array) of input means matching the arguments of
        Source.Propagate.Uncertainty_Analysis.zhangWrapper() - [windSpeedMean, AOD, cloud,
                                                                sza, wTemp, sal,
                                                                relAz, waveBands]
        :param uncertainties: list (normally numpy array) of input uncertainties matching the order of mean_vals

        :return: Zhang17 method rho uncertainty
        """
        return self.MCP.propagate_random(self.zhangWrapper,
                                         mean_vals,
                                         uncertainties
                                         )

    # Measurement Functions
    @staticmethod
    def instruments(ESLIGHT, ESDARK, LILIGHT, LIDARK, LTLIGHT, LTDARK, ESCal, LICal, LTCal, ESStab, LIStab, LTStab,
                    ESLin, LILin, LTLin, ESStray, LIStray, LTStray, EST, LIT, LTT, LIPol, LTPol, ESCos):
        """ Instrument specific uncertainties measurement function """
        return np.array((ESLIGHT - ESDARK)*ESCal*ESStab*ESLin*ESStray*EST*ESCos), \
               np.array((LILIGHT - LIDARK)*LICal*LIStab*LILin*LIStray*LIT*LIPol), \
               np.array((LTLIGHT - LTDARK)*LTCal*LTStab*LTLin*LTStray*LTT*LTPol)

    @staticmethod
    def band_Conv_Sensor_S3A(Hyperspec, Wavelengths):
        """ band convolution of Rrs for S3A"""
        rad_band, band_centres = band_integration.spectral_band_int_sensor(d=Hyperspec,
                                                                           wl=Wavelengths,
                                                                           platform_name="Sentinel-3A",
                                                                           sensor_name="olci", u_d=None)
        return rad_band

    @staticmethod
    def band_Conv_Sensor_S3B(Hyperspec, Wavelengths):
        """ band convolution of Rrs for S3B"""
        rad_band, band_centres = band_integration.spectral_band_int_sensor(d=Hyperspec,
                                                                           wl=Wavelengths,
                                                                           platform_name="Sentinel-3B",
                                                                           sensor_name="olci", u_d=None)
        return rad_band

    @staticmethod
    def band_Conv_Sensor_AQUA(Hyperspec, Wavelengths):
        """ band convolution of Rrs for EOS-AQUA Modis"""
        rad_band, band_centres = band_integration.spectral_band_int_sensor(d=Hyperspec,
                                                                           wl=Wavelengths,
                                                                           platform_name="EOS-Aqua",
                                                                           sensor_name="modis", u_d=None)
        return rad_band

    @staticmethod
    def band_Conv_Sensor_TERRA(Hyperspec, Wavelengths):
        """ band convolution of Rrs for EOS-Terra Modis"""
        rad_band, band_centres = band_integration.spectral_band_int_sensor(d=Hyperspec,
                                                                           wl=Wavelengths,
                                                                           platform_name="EOS-Terra",
                                                                           sensor_name="modis", u_d=None)
        return rad_band

    @staticmethod
    def band_Conv_Sensor_NOAA(Hyperspec, Wavelengths):
        """ band convolution of Rrs for NOAA Virrs"""
        rad_band, band_centres = band_integration.spectral_band_int_sensor(d=Hyperspec,
                                                                           wl=Wavelengths,
                                                                           platform_name="NOAA-20",
                                                                           sensor_name="viirs", u_d=None)
        return rad_band

    @staticmethod
    def Lw(lt, rhoVec, li, c2, c3, clin2, clin3, cstab2, cstab3, cstray2, cstray3, cT2, cT3, cpol1, cpol2):
        """ Lw Class based branch measurment function """
        li_signal = li * c2 * clin2 * cstab2 * cstray2 * cT2 * cpol1
        lt_signal = lt * c3 * clin3 * cstab3 * cstray3 * cT3 * cpol2

        return lt_signal - (li_signal * rhoVec)

    @staticmethod
    def RRS(lt, rhoVec, li, es, c1, c2, c3, clin1, clin2, clin3, cstab1, cstab2, cstab3, cstray1, cstray2, cstray3,
            cT1, cT2, cT3, cpol1, cpol2, ccos):
        """ Rrs Class based branch measurment function """
        es_signal = es*c1*cstab1*clin1*cstray1*cT1*ccos
        li_signal = li*c2*cstab2*clin2*cstray2*cT2*cpol1
        lt_signal = lt*c3*clin3*cstab3*cstray3*cT3*cpol2

        lw = lt_signal - (rhoVec*li_signal)
        lw[np.where(lw < 0)] = 0
        return lw/es_signal

    @staticmethod
    def Lw_FRM(lt, rho, li):
        """ Lw FRM branch measurment function """
        return lt - (rho * li)

    @staticmethod
    def Rrs_FRM(lt, rho, li, es):
        """ Rrs FRM branch measurment function """
        return (lt - (rho * li)) / es

    @staticmethod
    def rhoM99(windSpeedMean, SZAMean, relAzMean):
        """ Wrapper for Mobley 99 rho calculation to be called by punpy """

        theta = 40  # viewing zenith angle
        winds = np.arange(0, 14 + 1, 2)  # 0:2:14
        szas = np.arange(0, 80 + 1, 10)  # 0:10:80
        phiViews = np.arange(0, 180 + 1, 15)  # 0:15:180 # phiView is relAz

        # Find the nearest values in the LUT
        wind_idx = Utilities.find_nearest(winds, windSpeedMean)
        wind = winds[wind_idx]
        sza_idx = Utilities.find_nearest(szas, SZAMean)
        sza = szas[sza_idx]
        relAz_idx = Utilities.find_nearest(phiViews, relAzMean)
        relAz = phiViews[relAz_idx]

        # load in the LUT HDF file
        inFilePath = os.path.join(PATH_TO_DATA, 'rhoTable_AO1999.hdf')
        lut = HDFRoot.readHDF5(inFilePath)
        lutData = lut.groups[0].datasets['LUT'].data

        # convert to a 2D array
        lut = np.array(lutData.tolist())

        # match to the row
        row = lut[(lut[:, 0] == wind) & (lut[:, 1] == sza) & \
                  (lut[:, 2] == theta) & (lut[:, 4] == relAz)]

        rhoScalar = row[0][5]

        return rhoScalar

    @staticmethod
    def zhangWrapper(windSpeedMean, AOD, cloud, sza, wTemp, sal, relAz, waveBands):
        """ Wrapper for Zhang17 rho calculation to be called by punpy """
        # === environmental conditions during experiment ===
        env = collections.OrderedDict()
        env['wind'] = windSpeedMean
        env['od'] = AOD
        env['C'] = cloud  # Not used
        env['zen_sun'] = sza
        env['wtem'] = wTemp
        env['sal'] = sal

        # === The sensor ===
        sensor = collections.OrderedDict()
        sensor['ang'] = [40, 180 - relAz]  # relAz should vary from about 90-135
        sensor['wv'] = waveBands

        return ZhangRho.get_sky_sun_rho(env, sensor)['rho']
