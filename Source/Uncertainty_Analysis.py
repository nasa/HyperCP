import os
import numpy as np

# for analysis NPL developed packages
import punpy
from Source.Weight_RSR import Weight_RSR

# zhangWrapper
import collections
from Source import ZhangRho, PATH_TO_DATA

# M99 Rho
from Source.HDFRoot import HDFRoot
from Source.Utilities import Utilities

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

    corr_matrix_Default_Instruments = np.array([
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
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
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

    corr_matrix_Default_Lw: np.array = np.array([
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0]
    ])

    corr_matrix_Default_RRS: np.array = np.array([
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
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    ], dtype=np.float64)

    def __init__(self, M: int = 100, cores: int = 1):
        self._platform: str = ''  # internally used variable to store platform string to use in L2 conv products
        self._wavebands: np.array = None  # stores wavebands for convolution
        if isinstance(cores, int):
            self.MCP = punpy.MCPropagation(M, parallel_cores=cores)
        else:
            self.MCP = punpy.MCPropagation(M)

    # Main functions
    def propagate_Instrument_Uncertainty(self, mean_vals: list[np.array], uncertainties: list[np.array]) -> np.array:
        """
        :param mean_vals:  list (normally numpy array) of input means matching the arguments of
        Source.Uncertainty_Analysis.Propagate.instruments() - [ESLIGHT, ESDARK, 
                                                               LILIGHT, LIDARK, 
                                                               LTLIGHT, LTDARK,
                                                               ESCal, LICal, LTCal,
                                                               ESStab, LIStab, LTStab,
                                                               ESLin, LILin, LTLin,
                                                               ESStray, LIStray, LTStray,
                                                               EST, LIT, LTT,
                                                               LIPol, LTPol, ESCos]
        :param uncertainties: list (normally numpy array) of input uncertainties matching the order of mean_vals

        :Return: absolute uncertainty [es, li, lt]
        """

        corr_list = ['rand', 'rand', 'rand', 'rand', 'rand', 'rand', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst',
                     'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst']

        # NOTE: ISSUE #95
        unc = self.MCP.propagate_random(self.instruments,
                                        mean_vals,
                                        uncertainties,
                                        corr_between=self.corr_matrix_Default_Instruments,
                                        corr_x=corr_list,
                                        output_vars=3)

        # separate uncertainties and sensor values from their lists - for clarity
        Es_unc, Li_unc, Lt_unc = [unc[i] for i in range(len(unc))]

        return Es_unc, Li_unc, Lt_unc

    def Propagate_Lw_HYPER(self, mean_vals: list[np.array], uncertainties: list[np.array]) -> np.array:
        """
        :param mean_vals: list (normally numpy array) of input means matching the arguments of
        Source.Uncertainty_Analysis.Propagate.Lw() - [lt, rhoVec, li,
                                                      c_lt, c_li,
                                                      cstab_lt, cstab_li,
                                                      clin_lt, clin_li,
                                                      cstray_lt, cstray_li,
                                                      cT_lt, cT_li,
                                                      cpol_lt, cpol_li]
        :param uncertainties: list (normally numpy array) of input uncertainties matching the order of mean_vals

        :return: Lw uncertainty
        """

        corr_list = ['rand', 'syst', 'rand', 'syst', 'syst', 'syst', 'syst', 'syst',
                     'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst']

        return self.MCP.propagate_standard(self.Lw,
                                         mean_vals,
                                         uncertainties,
                                         corr_between=self.corr_matrix_Default_Lw,
                                         corr_x=corr_list)

    def Propagate_Lw_Convolved(self, mean_vals: list[np.array], uncertainties: list[np.array],
                          platform: str, wavebands: np.array) -> np.array:
        """
        :param mean_vals: list (normally numpy array) of input means matching the arguments of
        Source.Uncertainty_Analysis.Propagate.Lw() - [lt, rhoVec, li,
                                                      c_lt, c_li,
                                                      cstab_lt, cstab_li,
                                                      clin_lt, clin_li,
                                                      cstray_lt, cstray_li,
                                                      cT_lt, cT_li,
                                                      cpol_lt, cpol_li]
        :param uncertainties: list (normally numpy array) of input uncertainties matching the order of mean_vals
        :param platform:
        :param wavebands:
        :return: Lw uncertainty
        """

        corr_list = ['rand', 'syst', 'rand', 'syst', 'syst', 'syst', 'syst', 'syst',
                     'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst']

        self._platform = platform  # set platform which is used in self.RRS_Conv
        self._wavebands = wavebands  # set wavebands to be used in self.RRS_Conv

        rnd_unc = np.array(uncertainties)
        rnd_unc[np.where(np.array(corr_list, dtype=str) == 'syst')] = 0.0
        sys_unc = np.array(uncertainties)
        sys_unc[np.where(np.array(corr_list, dtype=str) == 'rand')] = 0.0

        # propagate random and systematic uncertainties separately
        random = self.MCP.propagate_random(
            self.Lw_Conv,
            mean_vals,
            rnd_unc,
            corr_between=self.corr_matrix_Default_Lw,
        )

        systematic = self.MCP.propagate_systematic(
            self.Lw_Conv,
            mean_vals,
            sys_unc,
            corr_between=self.corr_matrix_Default_Lw,
        )

        return np.sqrt(random ** 2 + systematic ** 2)

    def Propagate_RRS_HYPER(self, mean_vals: list[np.array], uncertainties: list[np.array]) -> np.array:
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

        corr_list = ['rand', 'syst', 'rand', 'rand', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst',
                     'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst']

        return self.MCP.propagate_standard(self.RRS,
                                           mean_vals,
                                           uncertainties,
                                           corr_between=self.corr_matrix_Default_RRS,
                                           corr_x=corr_list)

    def Propagate_RRS_Convolved(self, mean_vals: list[np.array], uncertainties: list[np.array], platform: str,
                                wavebands: np.array) -> np.array:
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
        :param platform:
        :param wavebands:

        :return: Rrs uncertainty


            will be replaced in the near future - for pixel by pixel method """

        corr_list = ['rand', 'syst', 'rand', 'rand', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst',
                     'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst', 'syst']

        self._platform = platform  # set platform which is used in self.RRS_Conv
        self._wavebands = wavebands  # set wavebands to be used in self.RRS_Conv

        rnd_unc = np.array(uncertainties)
        rnd_unc[np.where(np.array(corr_list, dtype=str) == 'syst')] = 0.0
        sys_unc = np.array(uncertainties)
        sys_unc[np.where(np.array(corr_list, dtype=str) == 'rand')] = 0.0

        # propagate random and systematic uncertainties separately
        random = self.MCP.propagate_random(
            self.RRS_Conv,
            mean_vals,
            rnd_unc,
            corr_between=self.corr_matrix_Default_RRS,
        )

        systematic = self.MCP.propagate_systematic(
            self.RRS_Conv,
            mean_vals,
            sys_unc,
            corr_between=self.corr_matrix_Default_RRS,
        )

        return np.sqrt(random ** 2 + systematic ** 2)

    def def_sensor_mfunc(self, platform):
        """

        """
        if platform.upper() == "S3A" or platform.lower().rstrip().replace('-','') == "sentinel3a":
            func = self.band_Conv_Sensor_S3A
        elif platform.upper() == "S3B" or platform.lower().rstrip().replace('-','') == "sentinel3b":
            func = self.band_Conv_Sensor_S3B
        elif platform.upper() == "MOD-A" or platform.lower().rstrip().replace('-','') == "eos-aqua":
            func = self.band_Conv_Sensor_AQUA
        elif platform.upper() == "MOD-T" or platform.lower().rstrip().replace('-', '') == "eos-terra":
            func = self.band_Conv_Sensor_TERRA
        elif platform.upper() == "VIIRS-J" or platform.lower().rstrip().replace('-', '') == "noaa-J":
            func = self.band_Conv_Sensor_NOAA_J
        elif platform.upper() == "VIIRS-N" or platform.lower().rstrip().replace('-', '') == "noaa-N":
            func = self.band_Conv_Sensor_NOAA_N
        elif platform.upper() == "HYPER":
            func = self.no_Conv
        else:
            msg = "sensor not supported"
            print(msg)
            raise SensorNotSupportedError("sensor not suppored, perhaps there is a typo in the sensor string")

        return func

    def band_Conv_Uncertainty(self, mean_vals: list[np.array], uncertainties: list[np.array], platform: str) -> np.array:
        """
        :param mean_vals: list (normally numpy array) of input values matching matheo.band_Conv_Sensor_[SENSOR]
        function - [Hyper_Rrs, wvl, Band cetral wavelengths, Band width]
        :param uncertainties: list (normally numpy array) of input uncertainties matching mean_vals
        :param platform: name of the sensor to be convolved

        :return: relative Rrs uncertainty per spectral band
        """
        func = self.def_sensor_mfunc(platform)

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
    def band_Conv_Sensor_S3A(Hyperspec, Wavelengths) -> np.array:
        """ band convolution of Rrs for S3A using Source.Weight_RSR"""

        hyperspec_as_dict = {str(k): [val] for k, val in zip(Wavelengths, Hyperspec)}
        rad_band = Weight_RSR.processSentinel3Bands(
            hyperspec_as_dict, sensor='A'
        )
        return np.array([value[0] for value in rad_band.values()])  # convert back to np.array for correct punpy return

    @staticmethod
    def band_Conv_Sensor_S3B(Hyperspec, Wavelengths) -> np.array:
        """ band convolution of Rrs for S3B using Source.Weight_RSR"""

        hyperspec_as_dict = {str(k): [val] for k, val in zip(Wavelengths, Hyperspec)}
        rad_band = Weight_RSR.processSentinel3Bands(
            hyperspec_as_dict, sensor='B'
        )
        return np.array([value[0] for value in rad_band.values()])  # return np.array for punpy

    @staticmethod
    def band_Conv_Sensor_AQUA(Hyperspec, Wavelengths) -> np.array:
        """ band convolution of Rrs for EOS-AQUA Modis using Source.Weight_RSR"""

        hyperspec_as_dict = {str(k): [val] for k, val in zip(Wavelengths, Hyperspec)}
        rad_band = Weight_RSR.processMODISBands(
            hyperspec_as_dict, sensor='A'
        )
        return np.array([value[0] for value in rad_band.values()])  # return as np.array for punpy

    @staticmethod
    def band_Conv_Sensor_TERRA(Hyperspec, Wavelengths) -> np.array:
        """ band convolution of Rrs for EOS-Terra Modis using Source.Weight_RSR"""

        hyperspec_as_dict = {str(k): [val] for k, val in zip(Wavelengths, Hyperspec)}
        rad_band = Weight_RSR.processMODISBands(
            hyperspec_as_dict, sensor='T'
        )
        return np.array([value[0] for value in rad_band.values()])

    @staticmethod
    def band_Conv_Sensor_NOAA_J(Hyperspec, Wavelengths) -> np.array:
        """ band convolution of Rrs for NOAA Virrs using Source.Weight_RSR"""

        hyperspec_as_dict = {str(k): [val] for k, val in zip(Wavelengths, Hyperspec)}
        rad_band = Weight_RSR.processVIIRSBands(
            hyperspec_as_dict, sensor='J'  # uses else to identify, string does not matter
        )
        return np.array([value[0] for value in rad_band.values()])

    @staticmethod
    def band_Conv_Sensor_NOAA_N(Hyperspec, Wavelengths) -> np.array:
        """ band convolution of Rrs for NOAA Virrs using Source.Weight_RSR"""

        hyperspec_as_dict = {str(k): [val] for k, val in zip(Wavelengths, Hyperspec)}
        rad_band = Weight_RSR.processVIIRSBands(
            hyperspec_as_dict, sensor='N'
        )
        return np.array([value[0] for value in rad_band.values()])

    @staticmethod
    def no_Conv(Hyperspec, *args, **kwargs) -> np.array:
        return Hyperspec

    @staticmethod
    def Lw(lt, rhoVec, li, c_li, c_lt, cstab_li, cstab_lt, clin_li, clin_lt, cstray_li, cstray_lt, cT_li, cT_lt, cpol_li, cpol_lt):
        """ Lw Class based branch measurment function """
        li_signal = li * c_li * cstab_li * clin_li * cstray_li * cT_li * cpol_li
        lt_signal = lt * c_lt * cstab_lt * clin_lt * cstray_lt * cT_lt * cpol_lt

        return lt_signal - (li_signal * rhoVec)

    def Lw_Conv(self, lt, rhoVec, li, c_li, c_lt, cstab_li, cstab_lt, clin_li, clin_lt, cstray_li, cstray_lt, cT_li, cT_lt, cpol_li, cpol_lt):
        """ Lw Class based branch measurment function """
        li_signal = li * c_li * cstab_li * clin_li * cstray_li * cT_li * cpol_li
        lt_signal = lt * c_lt * cstab_lt * clin_lt * cstray_lt * cT_lt * cpol_lt

        func = self.def_sensor_mfunc(self._platform)  # get mfunc per platform, saves us from making 8 mfuncs

        liConv = func(li_signal, self._wavebands)  # wavebands not included in uncertainty estimation
        ltConv = func(lt_signal, self._wavebands)  # we can pull data from class variables
        rhoConv = func(rhoVec, self._wavebands)

        return ltConv - (liConv * rhoConv)

    @staticmethod
    def RRS(lt, rhoVec, li, es, c_es, c_li, c_lt, cstab_es, cstab_li, cstab_lt, clin_es, clin_li, clin_lt, cstray_es, cstray_li, cstray_lt,
            cT_es, cT_li, cT_lt, cpol_li, cpol_lt, ccos):
        """ Rrs Class based branch measurment function """
        es_signal = es * c_es * cstab_es * clin_es * cstray_es * cT_es * ccos
        li_signal = li * c_li * cstab_li * clin_li * cstray_li * cT_li * cpol_li
        lt_signal = lt * c_lt * cstab_lt * clin_lt * cstray_lt * cT_lt * cpol_lt

        lw = lt_signal - (rhoVec*li_signal)
        lw[np.where(lw < 0)] = 0
        return lw/es_signal

    def RRS_Conv(self, lt, rhoVec, li, es, c_es, c_li, c_lt, cstab_es, cstab_li, cstab_lt, clin_es, clin_li, clin_lt, cstray_es, cstray_li, cstray_lt,
            cT_es, cT_li, cT_lt, cpol_li, cpol_lt, ccos):
        """ Rrs Class based branch measurment function """
        es_signal = es * c_es * cstab_es * clin_es * cstray_es * cT_es * ccos
        li_signal = li * c_li * cstab_li * clin_li * cstray_li * cT_li * cpol_li
        lt_signal = lt * c_lt * cstab_lt * clin_lt * cstray_lt * cT_lt * cpol_lt

        func = self.def_sensor_mfunc(self._platform)  # get mfunc per platform, saves us from making 8 mfuncs

        esConv = func(es_signal, self._wavebands)  # get band convoloved (ir)radiance
        liConv = func(li_signal, self._wavebands)  # wavebands not included in uncertainty estimation
        ltConv = func(lt_signal, self._wavebands)  # we can pull data from class variables
        rhoConv = func(rhoVec, self._wavebands)

        lw = ltConv - (rhoConv*liConv)
        lw[np.where(lw < 0)] = 0
        return lw/esConv  # calculate Rrs

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
        # Build in guardrails limiting to database bounds (DAA 2023-11-24)
        env['wind'] = windSpeedMean if windSpeedMean <= 15 else 15
        env['wind'] = env['wind'] if env['wind'] >= 0 else 0
        # clip AOD to 0.2 to ensure no error in Z17, potential underestimation of uncertainty however
        env['od'] = AOD if AOD <= 0.2 else 0.2
        env['od'] = env['od'] if env['od'] >= 0 else 0
        env['C'] = cloud  # Not used
        env['zen_sun'] = sza if sza <= 60 else 60
        env['zen_sun'] = env['zen_sun'] if env['zen_sun'] >= 0 else 0
        # Appears these are only use for Fresnel and are analytical and not inherently limited
        env['wtem'] = wTemp
        env['sal'] = sal

        # === The sensor ===
        sensor = collections.OrderedDict()
        # Current database is not limited near these values
        sensor['ang'] = [40, 180 - abs(relAz)]  # relAz should vary from about 90-135
        sensor['wv'] = waveBands

        # msg = (f"Uncertainty_Analysis.zhangWrapper. Wind: {env['wind']:.1f} AOT: {env['od']:.2f} Cloud: {env['C']:.1f} SZA: {env['zen_sun']:.1f} "
        #      f"SST: {env['wtem']:.1f} SSS: {env['sal']:.1f} VZA: {sensor['ang'][0]:.1f} RelAz: {relAz:.1f}")
        # Utilities.writeLogFile(msg)
        # print(msg)

        # tic = time.process_time()
        rho = ZhangRho.get_sky_sun_rho(env, sensor)['rho']
        # msg = f'zhangWrapper Z17 Elapsed Time: {time.process_time() - tic:.1f} s'
        # print(msg)
        # Utilities.writeLogFile(msg)
        return rho


class SensorNotSupportedError:
    """
    sensor not suppored, perhaps there is a typo in the sensor string
    """
    def __init__(self, message):
        print(message)
