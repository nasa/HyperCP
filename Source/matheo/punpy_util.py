"""
Functions to band integrate spectra for given spectral response function.
"""

from punpy import MCPropagation
import numpy as np
from typing import Union, Callable, Tuple, Iterable, Dict
import multiprocessing


__author__ = "Sam Hunt"
__created__ = "24/7/2020"


def _max_dim(arrays: Iterable[np.ndarray]) -> int:
    """
    Return max dimension of input numpy arrays

    :param arrays: n input numpy arrays
    :return: maximum dimension
    """

    dims = []
    for array in arrays:
        dims.append(np.ndim(array))

    return max(dims)


def _unc_to_dim(unc: Union[float, np.ndarray], dim: int, x: np.ndarray = None, x_len: int = None) -> np.ndarray:
    """
    Scales up uncertainty to given dimension (e.g. float to full vector, vector to diagonal maxtrix)

    :param unc: uncertainty value (in percent) or vector
    :param dim: target dimension to raise to
    :param x:
    :param x_len:
    :return:
    """

    original_dim = np.ndim(unc)

    if (original_dim > 2) or (dim > 2):
        raise ValueError(
            "Can only raise uncertainty to a max dimension of 2 (e.g. covariance matrix)"
        )

    if original_dim == dim:
        return unc
    elif unc is None:
        return None
    else:
        if original_dim == 0:
            if (x is None) and (x_len is None):
                raise AttributeError(
                    "Please define either x or x_len to raise dimension of shape 0 uncertainty"
                )
            elif x is not None:
                unc *= x
            else:
                unc = np.full(x_len, unc)

        if dim == 1:
            return unc

        return np.diag(unc)


def func_with_unc(
        f: Callable,
        params: Dict[str, Union[float, np.ndarray]],
        u_params: Dict[str, Union[None, float, np.ndarray]],
        parallel: bool = True,
) -> Tuple[Union[float, np.ndarray], Union[None, float, np.ndarray]]:
    """
    Evaluate function and uncertainties using Monte Carlo method

    Provides simple interface to run a simple Monte Carlo experiment with punpy.

    :param f: function
    :param params: function parameters
    :param u_params: function parameter uncertainties (entries keys same as parameters, one uncertainty per parameter).
    Entries may be of following type:

    * ``None`` - value assumed a constant, no uncertainty (assumed if not provided)
    * ``float`` - assumed to be a relative random uncertainty
    * 1 dimensional ``numpy.ndarray`` - assumed to be an array of absolute random uncertainties (must be same length as
    variable parameter)
    * 2 dimensional ``numpy.ndarray`` - assumed to be a covariance matrix (must be the length of the variable parameter
    square)

    :return: evaluated function and uncertainty
    """

    # evaluate function
    y = f(**params)

    # if no uncertainties return only in band spectrum
    if all(v == None for v in u_params.values()):
        return y, None

    # Add None's for any undefined uncertainties
    u_params_missing = {k: None for k in params.keys() if k not in u_params}
    u_params = {**u_params, **u_params_missing}

    # Find max dimension of uncertainty data and match other variables
    unc_dim = _max_dim(u_params.values())
    if unc_dim != 2:
        unc_dim = 1

    u_params = dict((k, _unc_to_dim(u, unc_dim, x=v)) if (u is not None) else (k, u) for (k, u), v in zip(u_params.items(), params.values()))

    # Propagate uncertainties
    if parallel:
        prop = MCPropagation(10000, parallel_cores=multiprocessing.cpu_count())
    else:
        prop = MCPropagation(10000)

    x = [v for v in params.values()]
    u_x = [u_params[k] for k in params.keys()]

    if unc_dim == 1:
        u_y = prop.propagate_random(func=f, x=x, u_x=u_x)
    elif unc_dim == 2:
        u_y = prop.propagate_cov(func=f, x=x, cov_x=u_x, return_corr=False)
    else:
        u_y = None

    del prop

    return y, u_y


if __name__ == "__main__":
    pass
