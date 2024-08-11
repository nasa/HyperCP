"""
Functions to band integrate spectra for given spectral response function.
"""

from Source.matheo.srf_utils import (
    return_iter_srf,
    return_band_centres,
    return_band_names,
)
from Source.matheo.punpy_util import func_with_unc
# from Source.matheo.utils.function_def import iter_f, f_tophat, f_triangle, f_gaussian
import numpy as np
from typing import Optional, Union, Tuple, List, Iterable, Callable
from comet_maths import interpolate_1d

__author__ = "Sam Hunt"
__created__ = "30/7/2021"


def cutout_nonzero(y, x, buffer=0.2):
    """
    Returns continuous non-zero part of function y(x)

    :type y: numpy.ndarray
    :param y: function data values

    :type x: numpy.ndarray
    :param x: function coordinate data values

    :type buffer: float
    :param buffer: fraction of non-zero section of y to include as buffer on either side (default: 0.2)
    """

    # Find extent of non-zero region
    idx = np.nonzero(y)
    imin = min(idx[0])
    imax = max(idx[0]) + 1

    # Determine buffer
    width = imax - imin

    imin -= int(width * buffer)
    imax += int(width * buffer)

    imin = imin if imin >= 0 else 0
    imax = imax if imax <= len(y) else len(y)

    return y[imin:imax], x[imin:imax], [imin, imax]


def get_x_offset(y, x, x_centre):
    """
    Returns coordinate offset required to centre function on given position.

    :param y: function values
    :param x: function coordinates
    :param x_centre: function centre defined my location of maximum value.
    :return: coordinate offset to centre function on x_centre
    """

    return x_centre - x[np.argmax(y)]


def _band_int(d: np.ndarray, x: np.ndarray, r: np.ndarray, x_r: np.ndarray, rint_norm: bool = True) -> float:
    """
    Returns integral of data array over a response band (i.e., d(x) * r(x_r))

    N.B.: This function is intended to be wrapped, so it can be applied to an array and run within punpy

    :param d: data to be band integrated
    :param x: data coordinates
    :param r: band response function
    :param x_r: band response function coordinates
    :param rint_norm: (default: True) option to normalise result by integral of r
    :return: band integrated data
    """

    # Cut out non-zero part of SRF to minimise risk of interpolation errors and optimise performance
    r, x_r, idx = cutout_nonzero(r, x_r)

    res_d = (max(x) - min(x)) / len(x)
    res_r = (max(x_r) - min(x_r)) / len(x_r)

    norm_val = 1.0

    # If spectrum lower res than the SRF - interpolate spectrum onto SRF wavelength coordinates before integration
    if res_r < res_d:
        d_interp = interpolate_1d(x, d, x_r)

        if rint_norm:
            norm_val = np.trapz(r, x_r)

        return np.trapz(r * d_interp, x_r) / norm_val

    # If spectrum lower res than the SRF - interpolate spectrum onto SRF wavelength coordinates before integration
    else:
        # First cut out spectrum to SRF wavelength range to avoid extrapolation errors in interpolation
        idx = np.where(np.logical_and(x < max(x_r), x > min(x_r)))
        d = d[idx]
        x = x[idx]

        r_interp = interpolate_1d(x_r, r, x)

        if rint_norm:
            norm_val = np.trapz(r_interp, x)

        return np.trapz(d * r_interp, x) / norm_val


def _band_int_regular_grid(
    d: np.ndarray, x: np.ndarray, r: np.ndarray, d_axis_x: int = 0, rint_norm: bool = True
) -> np.ndarray:
    """
    Returns integral of data array over a response band(s) defined along common, even-spaced coordinates (i.e., d(x) * r(x))

    Accelerated with respect to _band_int using dot product for integral

    N.B.: This function is intended to be wrapped, so it can be run within punpy

    :param d: data to be band integrated
    :param x: data and band response function coordinates along band integration axis, must be evenly spaced
    :param r: band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``x``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param d_axis_x: (default 0) x axis in data array
    :param rint_norm: (default: True) option to normalise result by integral of r
    :return: band integrated data
    """

    norm_val = 1.0
    if rint_norm:
        if r.ndim == 1:
            r_sum = np.sum(r)
        else:
            r_sum = np.sum(r, axis=1)

    if d.ndim == 1:
        if rint_norm:
            norm_val = r_sum
        return np.dot(r, d) / norm_val

    dot_dim = 1
    if (r.ndim == 2) and (d.ndim == 2):
        dot_dim = 0

    r_dot_d = np.moveaxis(np.dot(r, np.moveaxis(d, d_axis_x, dot_dim)), 0, d_axis_x)

    if rint_norm:
        sli = [np.newaxis] * d.ndim
        sli[d_axis_x] = slice(None)
        norm_val = r_sum[tuple(sli)]

    return r_dot_d / norm_val


def _band_int_arr(
    d: np.ndarray, x: np.ndarray, r: np.ndarray, x_r: np.ndarray, d_axis_x: int = 0, rint_norm: bool = False
) -> np.ndarray:
    """
    Band integrates multi-dimensional data array along x axis.

    In case where ``x == x_r`` and ``x`` is evenly sampled, an accelerated function is used.

    N.B.: This function is intended to be wrapped, so it can be run within punpy

    :param d: data to be band integrated
    :param x: data coordinates along band integration axis
    :param r: band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``x``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param x_r: band response function coordinates
    :param d_axis_x: (default 0) x axis in data array
    :param rint_norm: (default: True) option to normalise result by integral of r
    :return: band integrated data
    """

    # If r and d defined on common regular grid, use accelerated _band_int_regular_grid
    x_sampling = np.diff(x)
    if np.array_equal(x, x_r) and all(x_sampling == x_sampling[0]):
        return _band_int_regular_grid(d, x, r, d_axis_x=d_axis_x)

    # Else run _band_int
    # If single band response function defined, run once
    if r.ndim == 1:

        # If d has multiple dims, ensure integration done along correct axis
        if d.ndim == 1:
            return np.array([_band_int(d, x=x, r=r, x_r=x_r, rint_norm=rint_norm)])
        return np.apply_along_axis(_band_int, d_axis_x, arr=d, x=x, r=r, x_r=x_r, rint_norm=rint_norm)

    # If multiple band response functions defined, run multiple times
    elif r.ndim == 2:

        # If d has multiple dims, ensure integration done along correct axis
        if d.ndim == 1:
            d_int = np.zeros(len(r))
            for i in range(len(d_int)):
                d_int[i] = _band_int(d, x=x, r=r[i], x_r=x_r, rint_norm=rint_norm)

        else:
            # (this bit could probably be accelerated)
            d_int_shape = list(d.shape)
            d_int_shape[d_axis_x] = r.shape[0]
            d_int = np.zeros(d_int_shape)
            for i in range(r.shape[0]):
                # define slice ith band integrated data needs to populate in d_int
                sli = [slice(None)] * d_int.ndim
                sli[d_axis_x] = i
                d_int[tuple(sli)] = np.apply_along_axis(
                    _band_int, d_axis_x, arr=d, x=x, r=r[i], x_r=x_r, rint_norm=rint_norm
                )

        return d_int


def _band_int2ax_arr(
    d: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    rx: np.ndarray,
    x_rx: np.ndarray,
    ry: np.ndarray,
    y_ry: np.ndarray,
    d_axis_x: int = 0,
    d_axis_y: int = 1,
    rint_norm: bool = True
) -> np.ndarray:
    """
    Sequentially band integrates multi-dimensional data array along x axis and y axis

    In case where ``x == x_rx`` and ``x`` is evenly sampled or ``y == y_ry`` and ``y`` is evenly spaced, an accelerated function is used.

    N.B.: This function is intended to be wrapped, so it can be run within punpy

    :param d: data to be band integrated
    :param x: data coordinates along first band integration axis
    :param y: data coordinates along second band integration axis
    :param rx: first axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``x_rx``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param x_rx: first band response function coordinates
    :param ry: second axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``y_ry``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param y_ry: second band response function coordinates
    :param d_axis_x: (default 0) x axis in data array
    :param d_axis_y: (default 1) y axis in data array
    :param rint_norm: (default: True) option to normalise result by integral of r
    :return: band integrated data
    """

    d_intx = _band_int_arr(d, x=x, r=rx, x_r=x_rx, d_axis_x=d_axis_x, rint_norm=rint_norm)
    d_intx_inty = _band_int_arr(d_intx, x=y, r=ry, x_r=y_ry, d_axis_x=d_axis_y, rint_norm=rint_norm)

    return d_intx_inty


def _band_int3ax_arr(
    d: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    rx: np.ndarray,
    x_rx: np.ndarray,
    ry: np.ndarray,
    y_ry: np.ndarray,
    rz: np.ndarray,
    z_rz: np.ndarray,
    d_axis_x: int = 0,
    d_axis_y: int = 1,
    d_axis_z: int = 2,
    rint_norm: bool = True
) -> np.ndarray:
    """
    Sequentially band integrates multi-dimensional data array along x, y and z axes

    N.B. In case where ``x == x_rx`` and ``x`` is evenly sampled, ``y == y_ry`` and ``y`` is evenly spaced, or ``z == z_rz`` and ``z`` is evenly spaced, an accelerated function is used.

    N.B.: This function is intended to be wrapped, so it can be run within punpy

    :param d: data to be band integrated
    :param x: data coordinates along first band integration axis
    :param y: data coordinates along second band integration axis
    :param z: data coordinates along third band integration axis
    :param rx: first axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``x_rx``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param x_rx: first band response function coordinates
    :param ry: second axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``y_ry``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param y_ry: second band response function coordinates
    :param rz: third axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``z_rz``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param z_rz: third band response function coordinates
    :param d_axis_x: (default 0) x axis in data array
    :param d_axis_y: (default 1) y axis in data array
    :param d_axis_z: (default 2) z axis in data array
    :param rint_norm: (default: True) option to normalise result by integral of r
    :return: band integrated data
    """

    d_intx = _band_int_arr(d, x=x, r=rx, x_r=x_rx, d_axis_x=d_axis_x, rint_norm=rint_norm)
    d_intx_inty = _band_int_arr(d_intx, x=y, r=ry, x_r=y_ry, d_axis_x=d_axis_y, rint_norm=rint_norm)
    d_intx_inty_intz = _band_int_arr(
        d_intx_inty, x=z, r=rz, x_r=z_rz, d_axis_x=d_axis_z, rint_norm=rint_norm
    )

    return d_intx_inty_intz


def band_int(
    d: np.ndarray,
    x: np.ndarray,
    r: np.ndarray,
    x_r: np.ndarray,
    d_axis_x: int = 0,
    x_r_centre: Union[None, float] = None,
    u_d: Union[None, float, np.ndarray] = None,
    u_x: Union[None, float, np.ndarray] = None,
    u_r: Union[None, float, np.ndarray] = None,
    u_x_r: Union[None, float, np.ndarray] = None,
    rint_norm: bool = True
) -> Union[
    float, np.ndarray, Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]
]:
    """
    Returns integral of data array over a response band (i.e., d(x) * r(x_r))

    N.B. In case where ``x == x_r`` and ``x`` is evenly sampled, an accelerated function is used.

    :param d: data to be band integrated
    :param x: data coordinates
    :param r: band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``x_r``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param x_r: band response function coordinates
    :param d_axis_x: (default 0) if d greater than 1D, specify axis to band integrate along
    :param x_r_centre: (optional) centre of band response function in data coordinates, if there is an offset.
     Defined by location of band response function peak in data coordinates.
     Useful to define where sensor is looking along an extended input, e.g. spatially.
    :param u_d: (optional) uncertainty in data
    :param u_x: (optional) uncertainty in data coordinates
    :param u_r: (optional) uncertainty in band response function
    :param u_x_r: (optional) uncertainty in band response function coordinates
    :param rint_norm: (default: True) option to normalise result by integral of r

    :return: band integrated data
    :return: uncertainty of band integrated data (skipped if no input uncertainties provided)
    """

    x_r_off = get_x_offset(r, x_r, x_r_centre) if x_r_centre is not None else 0

    d_band, u_d_band = func_with_unc(
        _band_int_arr,
        params=dict(d=d, x=x, r=r, x_r=x_r + x_r_off, d_axis_x=d_axis_x, rint_norm=rint_norm),
        u_params=dict(d=u_d, x=u_x, r=u_r, x_r=u_x_r),
    )

    if u_d_band is None:
        return d_band

    return d_band, u_d_band


def band_int2ax(
    d: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    rx: np.ndarray,
    x_rx: np.ndarray,
    ry: np.ndarray,
    y_ry: np.ndarray,
    d_axis_x: int = 0,
    d_axis_y: int = 0,
    x_rx_centre: Union[None, float] = None,
    y_ry_centre: Union[None, float] = None,
    u_d: Union[None, float, np.ndarray] = None,
    u_x: Union[None, float, np.ndarray] = None,
    u_y: Union[None, float, np.ndarray] = None,
    u_rx: Union[None, float, np.ndarray] = None,
    u_x_rx: Union[None, float, np.ndarray] = None,
    u_ry: Union[None, float, np.ndarray] = None,
    u_y_ry: Union[None, float, np.ndarray] = None,
    rint_norm: bool = True
) -> Union[
    float, np.ndarray, Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]
]:
    """
    Sequentially band integrates multi-dimensional data array along x axis and y axis

    N.B. In case where ``x == x_rx`` and ``x`` is evenly sampled or ``y == y_ry`` and ``y`` is evenly spaced, an accelerated function is used.

    :param d: data to be band integrated
    :param x: data coordinates along first band integration axis
    :param y: data coordinates along second band integration axis
    :param rx: first axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``x_rx``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param x_rx: first band response function coordinates
    :param ry: second axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``y_ry``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param y_ry: second band response function coordinates
    :param d_axis_x: (default 0) x axis in data array
    :param d_axis_y: (default 1) y axis in data array
    :param x_rx_centre: (optional) centre of rx function in data coordinates, if there is an offset.
     Defined by location of band response function peak in data coordinates.
     Useful to define where sensor is looking along an extended input, e.g. spatially.
    :param y_ry_centre: (optional) centre of ry function in data coordinates, if there is an offset (as for x_rx_centre)
    :param u_d: (optional) uncertainty in data
    :param u_x: (optional) uncertainty in data coordinates along first band integration axis
    :param u_y: (optional) uncertainty in data coordinates along second band integration axis
    :param u_rx: (optional) uncertainty in first band response function
    :param u_x_rx: (optional) uncertainty in first band response function coordinates
    :param u_ry: (optional) uncertainty in second band response function
    :param u_y_ry: (optional) uncertainty in second band response function coordinates
    :param rint_norm: (default: True) option to normalise result by integral of r

    :return: band integrated data
    :return: uncertainty of band integrated data (skipped if no input uncertainties provided)
    """

    x_rx_off = get_x_offset(rx, x_rx, x_rx_centre) if x_rx_centre is not None else 0
    y_ry_off = get_x_offset(ry, y_ry, y_ry_centre) if y_ry_centre is not None else 0

    d_band, u_d_band = func_with_unc(
        _band_int2ax_arr,
        params=dict(
            d=d,
            x=x,
            y=y,
            rx=rx,
            x_rx=x_rx + x_rx_off,
            ry=ry,
            y_ry=y_ry + y_ry_off,
            d_axis_x=d_axis_x,
            d_axis_y=d_axis_y,
            rint_norm=rint_norm
        ),
        u_params=dict(d=u_d, x=u_x, y=u_y, rx=u_rx, x_rx=u_x_rx, ry=u_ry, y_ry=u_y_ry),
    )

    if u_d_band is None:
        return d_band

    return d_band, u_d_band


def band_int3ax(
    d: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    rx: np.ndarray,
    x_rx: np.ndarray,
    ry: np.ndarray,
    y_ry: np.ndarray,
    rz: np.ndarray,
    z_rz: np.ndarray,
    d_axis_x: int = 0,
    d_axis_y: int = 1,
    d_axis_z: int = 2,
    x_rx_centre: Union[None, float] = None,
    y_ry_centre: Union[None, float] = None,
    z_rz_centre: Union[None, float] = None,
    u_d: Union[None, float, np.ndarray] = None,
    u_x: Union[None, float, np.ndarray] = None,
    u_y: Union[None, float, np.ndarray] = None,
    u_z: Union[None, float, np.ndarray] = None,
    u_rx: Union[None, float, np.ndarray] = None,
    u_x_rx: Union[None, float, np.ndarray] = None,
    u_ry: Union[None, float, np.ndarray] = None,
    u_y_ry: Union[None, float, np.ndarray] = None,
    u_rz: Union[None, float, np.ndarray] = None,
    u_z_rz: Union[None, float, np.ndarray] = None,
    rint_norm: bool = True
) -> Union[
    float, np.ndarray, Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]
]:
    """
    Sequentially band integrates multi-dimensional data array along x, y and z axes

    N.B. In case where ``x == x_rx`` and ``x`` is evenly sampled, ``y == y_ry`` and ``y`` is evenly spaced, or ``z == z_rz`` and ``z`` is evenly spaced, an accelerated function is used.

    :param d: data to be band integrated
    :param x: data coordinates along first band integration axis
    :param y: data coordinates along second band integration axis
    :param z: data coordinates along third band integration axis
    :param rx: first axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``x_rx``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param x_rx: first band response function coordinates
    :param ry: second axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``y_ry``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param y_ry: second band response function coordinates
    :param rz: third axis band response function(s). For a single band, a 1D length-M array is required, where M is the length of ``z_rz``. Multiple bands may be defined in an N x M array, where N is number of response bands.
    :param z_rz: third band response function coordinates
    :param d_axis_x: (default 0) x axis in data array
    :param d_axis_y: (default 1) y axis in data array
    :param d_axis_z: (default 2) z axis in data array
    :param x_rx_centre: (optional) centre of rx function in data coordinates, if there is an offset.
     Defined by location of band response function peak in data coordinates.
     Useful to define where sensor is looking along an extended input, e.g. spatially.
    :param y_ry_centre: (optional) centre of ry function in data coordinates, if there is an offset (as for x_rx_centre)
    :param z_rz_centre: (optional) centre of rz function in data coordinates, if there is an offset (as for x_rx_centre)
    :param u_d: (optional) uncertainty in data
    :param u_x: (optional) uncertainty in data coordinates along first band integration axis
    :param u_y: (optional) uncertainty in data coordinates along second band integration axis
    :param u_z: (optional) uncertainty in data coordinates along third band integration axis
    :param u_rx: (optional) uncertainty in first band response function
    :param u_x_rx: (optional) uncertainty in first band response function coordinates
    :param u_ry: (optional) uncertainty in second band response function
    :param u_y_ry: (optional) uncertainty in second band response function coordinates
    :param u_rz: (optional) uncertainty in second band response function
    :param u_z_rz: (optional) uncertainty in third band response function coordinates
    :param rint_norm: (default: True) option to normalise result by integral of r

    :return: band integrated data
    :return: uncertainty of band integrated data (skipped if no input uncertainties provided)
    """

    x_rx_off = get_x_offset(rx, x_rx, x_rx_centre) if x_rx_centre is not None else 0
    y_ry_off = get_x_offset(ry, y_ry, y_ry_centre) if y_ry_centre is not None else 0
    z_rz_off = get_x_offset(rz, z_rz, z_rz_centre) if z_rz_centre is not None else 0

    params = dict(
        d=d,
        x=x,
        y=y,
        z=z,
        rx=rx,
        x_rx=x_rx + x_rx_off,
        ry=ry,
        y_ry=y_ry + y_ry_off,
        rz=rz,
        z_ry=z_rz + z_rz_off,
        d_axis_x=d_axis_x,
        d_axis_y=d_axis_y,
        d_axis_z=d_axis_z,
        rint_norm=rint_norm
    )

    u_params = dict(
        d=u_d,
        x=u_x,
        y=u_y,
        z=u_z,
        rx=u_rx,
        x_rx=u_x_rx,
        ry=u_ry,
        y_ry=u_y_ry,
        rz=u_rz,
        z_rz=u_z_rz,
    )

    d_band, u_d_band = func_with_unc(_band_int3ax_arr, params=params, u_params=u_params)

    if u_d_band is None:
        return d_band

    return d_band, u_d_band


def iter_band_int(
    d: np.ndarray,
    x: np.ndarray,
    iter_r: Iterable,
    d_axis_x: int = 0,
    u_d: Optional[Union[float, np.ndarray]] = None,
    u_x: Optional[Union[float, np.ndarray]] = None,
    u_r: Optional[Union[float, np.ndarray]] = None,
    u_x_r: Optional[Union[float, np.ndarray]] = None,
    rint_norm: Optional[bool] = True
) -> Union[
    float, np.ndarray, Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]
]:
    """
    Returns integral of data array over a set of response bands defined by iterator

    :param d: data to be band integrated
    :param x: data coordinates
    :param iter_r: iterable that returns band response function and band response function coordinates at each iteration
    :param d_axis_x: (default 0) if d greater than 1D, specify axis to band integrate along
    :param u_d: uncertainty in data
    :param u_x: uncertainty in data coordinates
    :param u_r: uncertainty in band response function
    :param u_x_r: uncertainty in band response function coordinates
    :param rint_norm: (default: True) option to normalise result by integral of r

    :return: band integrated data
    :return: uncertainty of band integrated data (skipped if no input uncertainties provided)
    """

    # Initialise output data matrix
    d_band_shape = list(d.shape)
    d_band_shape[d_axis_x] = sum(1 for x in iter_r)

    d_band = np.zeros(d_band_shape)
    u_d_band = np.zeros(d_band_shape)

    # Evaluate band integrate
    for i, (r_i, x_r_i) in enumerate(iter_r):

        # define slice ith band integrated data needs to populate in d_band
        sli = [slice(None)] * d_band.ndim
        sli[d_axis_x] = i
        sli = tuple(sli)

        # evaluate band integral
        if (u_d is None) and (u_x is None) and (u_r is None) and (u_x_r is None):
            d_band[sli] = band_int(d, x, r_i, x_r_i, d_axis_x, rint_norm=rint_norm)
        else:
            d_band[sli], u_d_band[sli] = band_int(
                d, x, r_i, x_r_i, d_axis_x, u_d, u_x, u_r, u_x_r, rint_norm=rint_norm
            )

    if not u_d_band.any():
        return d_band
    else:
        return d_band, u_d_band


def spectral_band_int_sensor(
    d: np.ndarray,
    wl: np.ndarray,
    platform_name: str,
    sensor_name: str,
    detector_name: str = None,
    band_names: Union[None, List[str]] = None,
    d_axis_wl: int = 0,
    u_d: np.ndarray = None,
    u_wl: np.ndarray = None,
) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    Returns spectral band integrated data array for named sensor spectral bands

    :param d: data to be band integrated
    :param wl: data wavelength coordinates
    :param platform_name: satellite name (must be valid value for
    :param sensor_name: name of instrument on satellite
    :param detector_name: (optional) name of sensor detector. Can be used in sensor has SRF data for for different
    detectors separately - if not specified in this case different
    :param band_names: (optional) sensor bands to evaluate band integral for, if omitted band integral evaluated for
    all bands within spectral range of data
    :param d_axis_wl: (default 0) spectral axis in data array
    :param u_d: (optional) uncertainty in data
    :param u_wl: (optional) uncertainty in data coordinates along first band integration axis

    :return: band integrated data
    :return: band integrated data centre wavelengths
    :return: uncertainties in band integrated data (skipped if no input uncertainties provided)
    """

    # Find bands within data spectral range
    band_names = return_band_names(platform_name, sensor_name, band_names)
    band_centres = return_band_centres(platform_name, sensor_name, band_names)
    valid_idx = np.where(
        np.logical_and(band_centres < max(wl), band_centres > min(wl))
    )[0]
    band_centres = band_centres[valid_idx]
    band_names = [band_names[i] for i in valid_idx]

    # Evaluate band integral
    iter_srf = return_iter_srf(
        platform_name, sensor_name, band_names, detector_name=detector_name
    )

    if (u_d is None) and (u_wl is None):
        return iter_band_int(d, wl, iter_srf, d_axis_wl), band_centres

    d_band, u_d_band = iter_band_int(d, wl, iter_srf, d_axis_wl)
    return d_band, band_centres, u_d_band


def return_r_pixel(
    x_pixel: np.ndarray,
    width_pixel: np.ndarray,
    x: np.ndarray,
    f: Callable,
    x_pixel_off: Optional[float] = None,
) -> np.ndarray:
    """
    Returns per pixel response function, expressed as an n_x X n_pixel matrix, where n_x is the length of wavelength coordinates of the response function defintion and n_pixel matrix is the number of pixels.

    :param x_pixel: centre of band response per pixel
    :param width_pixel: width of band response per pixel
    :param x: coordinates to define band response functions
    :param f: functional shape of response band - a python function with the interface ``f(x, centre, width)``, where ``x`` is a numpy array of the x coordinates to define the function along, ``centre`` is the response band centre, and ``width`` is the response band width.
    :param x_pixel_off: offset to pixel centre locations

    :return: pixel response function matrix
    """

    x_pixel_off = 0.0 if x_pixel_off is None else x_pixel_off

    r_pixel = np.zeros((len(x_pixel), len(x)))
    for i_pixel, (x_pixel_i, width_pixel_i) in enumerate(zip(x_pixel, width_pixel)):
        r_pixel[i_pixel, :] = f(x, x_pixel_i + x_pixel_off, width_pixel_i)

    return r_pixel


def pixel_int(
    d: np.ndarray,
    x: np.ndarray,
    x_pixel: Optional[np.ndarray] = None,
    width_pixel: Optional[np.ndarray] = None,
    u_d: Optional[Union[float, np.ndarray]] = None,
    u_x: Optional[Union[float, np.ndarray]] = None,
    u_x_pixel: Optional[Union[float, np.ndarray]] = None,
    u_width_pixel: Optional[Union[float, np.ndarray]] = None,
    band_shape: Union[Callable, str] = "triangle",
    r_sampling: Optional[float] = None,
    d_axis_x: int = 0,
    x_pixel_centre: Optional[float] = None,
    eval_iter: bool = False,
) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """
    Returns integral of data array over a set of response bands (i.e., d(x) * r_i(x_r) for i pixels)

    :param d: data to be band integrated
    :param x: data coordinates
    :param x_pixel: centre of band response per pixel
    :param width_pixel: width of band response per pixel
    :param u_d: uncertainty in data
    :param u_x: uncertainty in data coordinates
    :param u_x_pixel: uncertainty in centre of band response per pixel
    :param u_width_pixel: uncertainty in width of band response per pixel
    :param band_shape: (default: ``triangle``) functional shape of response band - must be either a defined name, one of 'triangle', 'tophat', or 'gaussian', or a python function with the interface ``f(x, centre, width)``, where ``x`` is a numpy array of the x coordinates to define the function along, ``centre`` is the response band centre, and ``width`` is the response band width.
    :param r_sampling: x sampling interval for derived pixel band response functions (if omitted pixel band response functions defined along x, this results in an accelerated computation)
    :param d_axis_x: (default: ``0``) if d greater than 1D, specify axis pixels are along
    :param x_pixel_centre: centre of pixels in data coordinates, if there is an offset.
     Defined as half way between max and min pixel values.
     Useful to define where sensor is looking along an extended input, e.g. spatially.
    :param eval_iter: (default: False) option to evaluate each pixel iteratively, saving memory

    :return: band integrated data
    :return: uncertainty in band integrated data
    """

    # If x_pixel_centre defined compute offset for x_pixel array
    x_pixel_off = (
        x_pixel_centre - ((x_pixel.max() - x_pixel.min()) / 2.0)
        if x_pixel_centre is not None
        else 0
    )

    # Get function
    if band_shape == "triangle":
        f = f_triangle
        xlim_width = 1
    elif band_shape == "tophat":
        f = f_tophat
        xlim_width = 1
    elif band_shape == "gaussian":
        f = f_gaussian
        xlim_width = 3
    else:
        f = band_shape
        xlim_width = 3

    if eval_iter:
        return iter_band_int(
            d,
            x,
            iter_f(f, x_pixel + x_pixel_off, width_pixel, xlim_width=xlim_width),
            d_axis_x,
            u_d,
            u_x,
        )

    else:

        # Define r x coordinates
        x_r_pixel = x

        if r_sampling is not None:
            i_x_p_min = np.argmin(x_pixel)
            i_x_p_max = np.argmax(x_pixel)

            x_r_pixel = np.arange(
                x_pixel[i_x_p_min] - xlim_width * width_pixel[i_x_p_min],
                x_pixel[i_x_p_max] + xlim_width * width_pixel[i_x_p_max] + 1,
                r_sampling,
            )

        # Build spectral response function matrix
        r_pixel = return_r_pixel(
            x_pixel,
            width_pixel,
            x_r_pixel,
            f,
            x_pixel_off=x_pixel_off,
        )

        return band_int(d=d, x=x, r=r_pixel, x_r=x_r_pixel, d_axis_x=d_axis_x)


def _band_int2d(
    d: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    psf: np.ndarray,
    x_psf: np.ndarray,
    y_psf: np.ndarray,
) -> float:
    """
    Returns integral of a 2D data array over a response band defined by a 2D point spread function
    (i.e., d(x, y) * psf(x_psf, y_psf))

    N.B.: This function is intended to be wrapped, so it can be applied to an array and run within punpy

    :param d: two dimensional data to be band integrated
    :param x: data x coordinates
    :param y: data y coordinates
    :param psf: two dimensional point spread function of band response
    :param x_psf: psf x coordinates
    :param y_psf: psf y coordinates
    :return: band integrated data
    """

    # todo - implement _band_int2d
    raise NotImplementedError


def _band_int2d_arr(
    d: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    psf: np.ndarray,
    x_psf: np.ndarray,
    y_psf: np.ndarray,
    d_axis_x: int = 0,
    d_axis_y: int = 1,
) -> np.ndarray:
    """
    Integrates two dimensional slice of multi-dimensional data array over a response band defined by a 2D point spread
    function

    N.B.: This function is intended to be wrapped, so it can be run within punpy

    :param d: two dimensional data to be band integrated
    :param x: data x coordinates
    :param y: data y coordinates
    :param psf: two dimensional point spread function of band response
    :param x_psf: psf x coordinates
    :param y_psf: psf y coordinates
    :param d_axis_x: (default 0) x axis in data array
    :param d_axis_y: (default 1) y axis in data array
    :return: band integrated data
    """

    # todo - implement _band_int2d_arr
    raise NotImplementedError


def band_int2d(
    d: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    psf: np.ndarray,
    x_psf: np.ndarray,
    y_psf: np.ndarray,
    d_axis_x: int = 0,
    d_axis_y: int = 1,
    u_d: Union[None, float, np.ndarray] = None,
    u_x: Union[None, float, np.ndarray] = None,
    u_y: Union[None, float, np.ndarray] = None,
    u_psf: Union[None, float, np.ndarray] = None,
    u_x_psf: Union[None, float, np.ndarray] = None,
    u_y_psf: Union[None, float, np.ndarray] = None,
) -> Union[
    float, np.ndarray, Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]
]:
    """
    Returns integral of a 2D data array over a response band defined by a 2D point spread function
    (i.e., d(x, y) * psf(x_psf, y_psf))

    :param d: two dimensional data to be band integrated
    :param x: data x coordinates
    :param y: data y coordinates
    :param psf: two dimensional point spread function of band response
    :param x_psf: psf x coordinates
    :param y_psf: psf y coordinates
    :param d_axis_x: (default 0) x axis in data array, if d more than 2D
    :param d_axis_y: (default 1) y axis in data array, if d more than 2D
    :param u_d: (optional) uncertainty in data
    :param u_x: (optional) uncertainty in data x coordinates
    :param u_y: (optional) uncertainty in data y coordinates
    :param u_psf: (optional) uncertainty in point spread function of band response
    :param u_x_psf: (optional) uncertainty in psf x coordinates
    :param u_y_psf: (optional) uncertainty in psf x coordinates

    :return: band integrated data
    :return: uncertainty of band integrated data (skipped if no input uncertainties provided)
    """

    d_band, u_d_band = func_with_unc(
        _band_int2d_arr,
        params=dict(
            d=d,
            x=x,
            y=y,
            psf=psf,
            x_psf=x_psf,
            y_psf=y_psf,
            d_axis_x=d_axis_x,
            d_axis_y=d_axis_y,
        ),
        u_params=dict(d=u_d, x=u_x, y=u_y, psf=u_psf, x_psf=u_x_psf, y_psf=u_y_psf),
    )

    if u_d_band is None:
        return d_band

    return d_band, u_d_band


def pixel_int2d(
    d: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    x_pixel: np.ndarray,
    y_pixel: np.ndarray,
    width_pixel: np.ndarray,
    psf_shape: str = "triangle",
    d_axis_x: int = 0,
    d_axis_y: int = 0,
    u_d: Union[None, float, np.ndarray] = None,
    u_x: Union[None, float, np.ndarray] = None,
    u_y: Union[None, float, np.ndarray] = None,
    u_x_pixel: Union[None, float, np.ndarray] = None,
    u_y_pixel: Union[None, float, np.ndarray] = None,
    u_width_pixel: Union[None, float, np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns integral of data array over a response band (i.e., d(x) * r(x_r))

    :param d: data to be band integrated
    :param x: data x coordinates
    :param y: data y coordinates
    :param x_pixel: x positions of centre of psf per pixel
    :param y_pixel: y positions of centre of psf per pixel
    :param width_pixel: width of psf per pixel
    :param psf_shape: (default X) psf shape - must be one of...
    :param d_axis_x: (default 0) x axis in data array, if d more than 2D
    :param d_axis_y: (default 1) y axis in data array, if d more than 2D
    :param u_d: uncertainty in data
    :param u_x: uncertainty in data x coordinates
    :param u_y: uncertainty in data y coordinates
    :param u_x_pixel: uncertainty in x positions of centre of psf per pixel
    :param u_y_pixel: uncertainty in y positions of centre of psf per pixel
    :param u_width_pixel: uncertainty in width of psf per pixel

    :return: band integrated data
    :return: uncertainty in band integrated data
    """

    # todo - implement _band_int2d_arr
    raise NotImplementedError


if __name__ == "__main__":
    pass
