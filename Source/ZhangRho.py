import os
import logging
from typing import Optional
from functools import lru_cache

import numpy as np
import xarray as xr  # Only needed to read original data
from scipy.interpolate import interpn

from Source import PATH_TO_DATA


logger = logging.getLogger('zhang17')

db: Optional[dict] = None
quads: Optional[dict] = None
skyrad0: Optional[np.ndarray] = None
sunrad0: Optional[np.ndarray] = None
sdb: Optional[dict] = None
vdb: Optional[dict] = None
rad_boa_sca: Optional[np.ndarray] = None
rad_boa_vec: Optional[np.ndarray] = None


def load():
    """
    Load look up tables from Zhang et al. 2017
    """
    logger.debug('Load constants')
    global db, quads, skyrad0, sunrad0, sdb, vdb, rad_boa_sca, rad_boa_vec

    db_path = os.path.join(PATH_TO_DATA, 'Zhang_rho_db_expanded.mat')
    with xr.open_dataset(db_path, engine='netcdf4') as ds:
        skyrad0 = ds['skyrad0'].to_numpy().T
        sunrad0 = ds['sunrad0'].to_numpy().T
        rad_boa_sca = ds['Radiance_BOA_sca'].to_numpy().T
        rad_boa_vec = ds['Radiance_BOA_vec'].to_numpy().T

    db = xr.open_dataset(db_path, group='db', engine='netcdf4')
    quads = xr.open_dataset(db_path, group='quads', engine='netcdf4')
    sdb = xr.open_dataset(db_path, group='sdb', engine='netcdf4')
    vdb = xr.open_dataset(db_path, group='vdb', engine='netcdf4')

    quads = {k: quads[k].to_numpy().T for k in ['zen', 'azm', 'du', 'dphi', 'sun05',
                                                'zen_num', 'azm_num', 'zen0', 'azm0']}
    db = {k: db[k].to_numpy().T.squeeze() for k in ['wind', 'od', 'C', 'zen_sun', 'wv']}
    sdb = {k: sdb[k].to_numpy().T.squeeze()
           for k in ['wind', 'od', 'zen_sun', 'zen_view', 'azm_view', 'wv']}
    vdb = {k: vdb[k].to_numpy().T.squeeze()
           for k in ['wind', 'od', 'zen_sun', 'zen_view', 'azm_view', 'wv']}


def assign(DB):
    global db, quads, skyrad0, sunrad0, sdb, vdb, rad_boa_sca, rad_boa_vec

    db = DB["db"]
    quads = DB["quads"]
    sdb = DB["sdb"]
    vdb = DB["vdb"]
    skyrad0 = DB["skyrad0"]
    sunrad0 = DB["sunrad0"]
    rad_boa_sca = DB["rad_boa_sca"]
    rad_boa_vec = DB["rad_boa_vec"]


def clear_memory():
    """
    Remove look up tables from memory (~2.5Gb).
    """
    global db, quads, skyrad0, sunrad0, sdb, vdb, rad_boa_sca, rad_boa_vec
    db, quads, skyrad0, sunrad0, sdb, vdb, rad_boa_sca, rad_boa_vec = \
        None, None, None, None, None, None, None, None


def my_sph2cart(azm, zen, r=1):
    """
    Converts spherical coordinates to cartesian

    Inputs
    -------
    azm [Numpy array] : -azimuth angle
    zen [Numpy array] : zenith angle
    r  [float] : radius = 1

    Outputs
    -------
    x :
    y :
    z :
    """
    elev = np.pi / 2 - zen
    cos_elev = np.cos(elev)
    xyz = np.empty((*np.broadcast_shapes(azm.shape, zen.shape), 3), dtype=float)
    xyz[..., 0] = r * cos_elev * np.cos(azm)
    xyz[..., 1] = r * cos_elev * np.sin(azm)
    xyz[..., 2] = r * np.sin(elev)
    return xyz


def find_quads(zen, azm):
    """
    Finds location in quads (why is it called find_quads?)

    Inputs
    ------
    zen :
    azm :

    Outputs
    -------
    locs :
    """
    return np.argmin(np.sqrt((quads['zen'][:] - zen) ** 2 + (quads['azm'][:] - azm) ** 2))


@lru_cache(maxsize=32)
def get_prob(wind, vec):
    """
    Computes probability of sky light being reflected into the sensor

    Inputs
    ------
    wind : Wind speed (m/s)
    vec : sensor vector

    Outputs
    -------
    prob [np.array] :  probability of sky light reflected into the sensor
    angr_sky[np.array] : reflection angle
    """
    # prob = np.empty((len(quads['zen']), len(wind) * vec.shape[0]))
    # angr_sky = np.empty(prob.shape)
    # k = 0
    # for w in wind:
    #     for v in vec:
    #         prob[:, k], angr_sky[:, k] = sky_light_reflection2(w, v)
    #         k += 1
    # return prob, angr_sky
    return sky_light_reflection2(wind, np.array(vec))


def gen_vec(zens, azms):
    # generate vectors from permutation of zenith and azimuth angles
    zens, azms = np.meshgrid(zens, azms, sparse=True, copy=False)
    return my_sph2cart(azms, zens, 1).reshape(-1, 3)


def gen_vec_quad(zen, du, azm, dphi, num):
    half_azm = np.linspace(-dphi / 2, dphi / 2, num)
    half_zen = np.linspace(-du / 2 / np.sin(zen), du / 2 / np.sin(zen), num)
    return gen_vec(zen + half_zen, azm + half_azm)


def sky_light_reflection2(wind, sensor):
    """
    Computes probability of light reflection at angle.

    Inputs
    ------
    wind : Wind speed (m/s)
    sensor : Numpy array
             The vector of reflected light measured by the sensor
    quads :
            Sky light quads
    """
    zen, du, azm, dphi = quads['zen'], quads['du'], quads['azm'], quads['dphi']
    prob = np.empty_like(zen[:, 0])
    ang = np.empty_like(prob)

    zen0 = zen[0, 0]
    p_vec = gen_vec_polar(zen0, num=100)
    prob[0], ang[0] = prob_reflection(-p_vec, sensor, wind)

    # sky = gen_vec_quad(zen, du, azm, dphi, num=10)
    for i in np.arange(1, prob.size):
        sky = gen_vec_quad(zen[i], du, azm[i], dphi, num=10)
        prob[i], ang[i] = prob_reflection(-sky, sensor, wind)

    return prob, ang


def cart2sph(x, y, z):
    azimuth = np.arctan2(y, x)
    elevation = np.arctan2(z, np.sqrt(x ** 2 + y ** 2))
    r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    return azimuth, elevation, r


def my_cart2sph(n):
    azm = np.arctan2(n[..., 1], n[..., 0])
    zen = np.pi / 2 - np.arctan2(n[..., 2], np.sqrt(n[..., 0] ** 2 + n[..., 1] ** 2))
    # r = np.sqrt(n[..., 0] ** 2 + n[..., 1] ** 2 + n[..., 2] ** 2)
    return azm, zen  # , r


def gen_vec_polar(zen, num=10):
    """
    Generates vectors for the polar cap, quad, and sun disk.
    By convention, the sun disk is at XZ plane, i.e., azimuth = 0.

    Inputs
    ------
    zen : Sun zenith angle
    sun05 :
    num : Number of angles to consider

    Outputs
    -------
    vec : Polar cap vector
    """
    sun05 = quads['sun05']
    phi = np.linspace(0, 2 * np.pi, num)
    sin_sun05 = np.sin(sun05)
    x = np.insert((sin_sun05 * np.cos(phi)), 0, 0)
    y = np.insert((sin_sun05 * np.sin(phi)), 0, 0)
    z = np.insert((np.ones_like(phi) * np.cos(sun05)), 0, 1)
    tmp = np.array([x, y, z])
    Ry = [[np.cos(zen), 0, np.sin(zen)],
          [0, 1, 0],
          [-np.sin(zen), 0, np.cos(zen)]]
    return np.matmul(Ry, tmp).T  # vec


def prob_reflection(inc, refl, wind):
    """
    Estimates probability of facets reflecting incident light into given direction and wind.

    Inputs
    ------
    inc : incident light vector (either -sun or -sky)
    refl : reflected light vector (sensor)
    wind : Wind speed (m/s)

    Outputs
    -------
    prob : Probability
    ang : Reflection angle
    """

    def vec_length(a):
        # The length of vector a
        al = np.sqrt(np.sum(abs(a) ** 2, 1))
        return al

    def cox_munk(wind):
        # Cox and Munk slope distribution of capillary wave facets
        sigma = np.sqrt(0.003 + 0.00512 * wind)
        return sigma

    def rayleighcdf(x, s):
        # Cumulative distribution function for Rayleigh distribution
        t = (x / s) ** 2
        y = 1 - np.exp(-t / 2)
        return y

    # Elementwise broadcasting 1x3(refl) onto 101x3(inc)
    n = refl - inc
    vl = vec_length(n)
    n /= vl.reshape(len(vl), 1)

    # the zenith and azimuth angles of the facets
    azm_n, zen_n = my_cart2sph(n)

    # convert facet zenith angle to slopes
    slope = np.tan(zen_n)

    # estimate wind-roughened probability of facets
    # sigma2 = 0.003 + 0.00512*wind;
    # sigma = sigma2^0.5;
    sigma = cox_munk(wind)
    sigma = sigma / np.sqrt(2)
    p1 = rayleighcdf(max(slope), sigma) - rayleighcdf(min(slope), sigma)
    # } !!!
    # azimuth angle ranges from -180 to 180. Need to treat the cases when the
    # azimuth angles cover both positive ang negative ranges.
    # case 1: -2 -1 1 2
    # case 2: -179, -178, 178, 179
    # case 3: -179 -120 2 5 130 178
    # cases 1 and 2: the range should be 4
    # case 3: the range should be 357
    azm_nx = max(azm_n)
    azm_nn = min(azm_n)

    if azm_nx * azm_nn > 0:  # not an issue
        p2 = (azm_nx - azm_nn) / 2 / np.pi
    elif any(abs(azm_n) < np.pi / 2):  # cases 1 and 3
        p2 = (azm_nx - azm_nn) / 2 / np.pi
    else:  # case 2
        ind = azm_n < 0
        azm_n[ind] = azm_n[ind] + 2 * np.pi
        azm_nx = max(azm_n)
        azm_nn = min(azm_n)
        p2 = (azm_nx - azm_nn) / 2 / np.pi

    prob = 2 * p1 * p2  # factor 2 accounts for 180 degree ambiguity

    # incident angle
    cosw = np.sum(n * refl, 1)
    ang = np.arccos(cosw)
    ind = ang > np.pi / 2
    ang[ind] = np.pi - ang[ind]
    ang = np.mean(ang)
    return prob, ang


def sw_fresnel(wv, ang, t, s):
    """
    Calculates Fresnel reflectance for seawater.

    Inputs
    ------
    wv : Wavelength (nm)
    ang : Reflectance angle
    T : Temperature (degC)
    S : Salinity (PSU)

    Outputs
    -------
    m : Refractive index
    ref : Fresnel reflectance of seawater
    """
    return fresnel(index_w(wv, t, s), ang)


def index_w(wv, t, s):
    """
    Calculates water refractive index
     mw(wv,T,S)=n0+(n1+n2T+n3T^2)S+n4T2+(n5+n6S+n7T)/wv+n8/wv^2+n9/wv^3;

    Inputs
    -------
    wv : Wavelength (nm)
    T : Temperature (degC)
    S : Salinity (PPT)
    """
    n0 = 1.31405
    n1 = 1.779e-4
    n2 = -1.05e-6
    n3 = 1.6e-8
    n4 = -2.02e-6
    n5 = 15.868
    n6 = 0.01155
    n7 = -0.00423
    n8 = -4382
    n9 = 1.1455e6

    n0_4 = n0 + (n1 + n2 * t + n3 * t ** 2) * s + n4 * t ** 2
    n5_7 = n5 + n6 * s + n7 * t
    wv = np.array(wv, dtype=float)
    mw = n0_4 + n5_7 * (wv ** -1) + n8 * (wv ** -2) + n9 * (wv ** -3)
    return mw


def fresnel(m, ang):
    """
    This function calculates the Fresnel reflectances for electric vector
    parallel (Rp), perpendicular (Rr) and unpolarized incident light.
     The reflection matrix =
     [R11, R12, 0; R12, R11, 0; 0, 0, R33]
     Only accounts for I, Q, U and ignore the V component.
     Revision History
     2016-07-10:   1st version, just compute R11, i.e, R
     2016-12-14:   add other reflection matrix elements R12 and R33
                   Also found an error in the previous equation for Rp1

    Inputs
    ------
    m : Relative refractive index
    ang : Reflectance (incident) angle

    Outputs
    -------
    R : Fresnel reflectance matrix element (1, 1)
    R12 : Fresnel reflectance matrix element (1, 2)
    R33 : Fresnel reflectance matrix element (3, 3)
    """
    ang = np.reshape(ang, (-1, 1))
    m = np.reshape(m, (1, -1))

    cosang = abs(np.cos(ang))  # cosine of incident angle
    sinangr = np.sin(ang) * (1 / m)  # sine of refraction angle
    cosangr = (1 - sinangr ** 2) ** 0.5  # cosine of refraction angle

    # reflection coefficient for perpendicular incident light
    tmp = cosangr * m
    Rr1 = (cosang - tmp) / (cosang + tmp)

    # reflection coefficient for parallel incident light
    tmp = cosang * m
    Rp1 = (tmp - cosangr) / (cosangr + tmp)

    Rr = np.abs(Rr1) ** 2  # reflectance for perpendicular incident light

    Rp = np.abs(Rp1) ** 2  # reflectance for parallel incident light

    R = (Rr + Rp) / 2
    # R12 = (Rp - Rr) / 2
    # R33 = np.real(Rr1 * np.conj(Rp1))

    return R  # , R12, R33


def interpn_chunked(x, y, xi, chunked_axis=2, cache_size=(16 * 10 ** 6) / 4):
    # x: array(arrays(0:3)) ranges of zen_sun(7), od(4), index(92476), waveband(131); x[chunked_axis=2]=index, so array(0:92475)
    # y: skyrad0 (7x4x92746x131)
    # xi: array(arrays(0:3)) env['zen_sun'](1), env['od'](1), db_idx(92476), sensor['wv'](depends on sensor))

    ndim = len(x)
    chunk = (y.size * y.dtype.itemsize) / cache_size  # TODO Optimize chunk size automatically based on cache size
    if chunk > 1:
        # Chunked
        indices = np.append(np.arange(len(x[chunked_axis]), step=len(x[chunked_axis]) / chunk, dtype=int),
                            len(x[chunked_axis]))
        ys = np.split(y, indices[1:-1], axis=chunked_axis)
        cyi = np.empty([len(v) if hasattr(v, '__iter__') else 1 for v in xi])
        for cy, s, e in zip(ys, indices[:-1], indices[1:]):
            cx = [v[s:e] if i == chunked_axis else v for i, v in enumerate(x)]
            cxi = np.array(np.meshgrid(*[v[s:e] if i == chunked_axis else v for i, v in enumerate(xi)], copy=False)).T
            try:
                cyi[:, :, s:e, :] = interpn(cx, cy, cxi.reshape(-1, ndim)).reshape(cxi.shape[:-1]).T
            except ValueError as err:
                print(err)

        return cyi
    else:
        # One shot
        vxi = np.array(np.meshgrid(*xi, copy=False)).T
        return interpn(x, y, vxi.reshape(-1, ndim)).reshape(vxi.shape[:-1]).T


def get_sky_sun_rho(env, sensor, round4cache=False, DB=None):
    """
    Computes sea surface reflectance of skylight.
    Based on: Zhang, X., S. He, A. Shabani, P.-W. Zhai, and K. Du. 2017. Spectral sea
    surface reflectance of skylight. Opt. Express 25: A1-A13, doi:10.1364/OE.25.0000A1.
    Translated from Matlab by D. Aurin 1/2020

    Inputs
    ------
    env: Environmental variables (scalars)
            C(cloud; not used), od(aerosol optical depth), sal(salinity),
            wind, wtem(water temp), zen_sun(solar zenith angle)
    sensor: Sensor configurations
            ang([zenith angle (scalar), 180-relative solar azimuth angle (scalar)]),
            wv(list of waveband centers) (vector)
    round4cache: Round input wind and sensor['ang'] to one and zero decimals to allow to leverage cache.

    Outputs
    -------
    rho:  Spectral sea surface reflectance of sun/sky glint including
            sun(solar rho), sky(sky rho), sca2vec(), rho(total rho)
    """
    # Load constants
    # global db, quads, skyrad0, sunrad0, sdb, vdb, radiance_boa_sca, radiance_boa_vec
    if DB is None:
        if db is None:
            load()
    else:
        assign(DB)

        # with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data/zhang_rho_db.pickle'), 'rb') as f:
        #     db, quads, skyrad0, sunrad0, sdb, vdb, radiance_boa_sca, radiance_boa_vec = pickle.load(f)

    # Round input to speed up processing
    if round4cache:
        env['wind'] = round(env['wind'], 1)
        sensor['ang'] = np.round(sensor['ang'], 0)

    # Change units
    sensor['ang2'] = sensor['ang'] + np.array([0, 180])
    sensor['pol'] = np.deg2rad(sensor['ang'])  # sensor polar coordinate
    sensor['vec'] = my_sph2cart(sensor['pol'][1], sensor['pol'][0])  # sensor vector
    sensor['pol2'] = np.deg2rad(sensor['ang2'])  # skylight polar coordinate
    sensor['loc2'] = find_quads(sensor['pol2'][0], sensor['pol2'][1])
    # Set output
    rho = {}

    # Probability and reflection angle of reflecting skylight into the sensor
    logger.debug(f"Get prob & ang ({env['wind']}, {sensor['ang']})")
    prob, angr_sky = get_prob(env['wind'], tuple(sensor['vec']))
    tprob = np.sum(prob, 0)
    ref = sw_fresnel(sensor['wv'], angr_sky, env['wtem'], env['sal'])

    # Sky radiance
    # TODO Check dtype of skyrad0 to lower memory footprint
    # TODO Look into numexpr, numba, dask library
    logger.debug(f"Interpolate skyrad ({env['zen_sun']}', '{env['od']}', '{sensor['wv'][0:5]}...)")
    db_idx = np.arange(skyrad0.shape[2])
    # xi = np.array(np.meshgrid(env['zen_sun'], env['od'], db_idx, sensor['wv'], copy=False)).T
    # skyrad = interpn((db['zen_sun'], db['od'], db_idx, db['wv']),
    #                  skyrad0, xi.reshape(-1, 4)).reshape(xi.shape[:-1]).T.squeeze()

    #if(env['zen_sun'] > 60.0):
    #    env['zen_sun']=59.9
    skyrad = interpn_chunked((db['zen_sun'], db['od'], db_idx, db['wv']), skyrad0,
                             (env['zen_sun'], env['od'], db_idx, sensor['wv']), chunked_axis=2).squeeze()

    n0 = skyrad[sensor['loc2']]
    n = skyrad / n0
    rho['sky'] = np.sum((ref * n) * (prob / tprob).reshape((len(prob), 1)), 0)

    # Sun radiance
    logger.debug('Interpolating sunrad')
    xi = np.array(np.meshgrid(env['zen_sun'], env['od'], sensor['wv'], copy=False)).T.reshape(-1, 3)
    sunrad = interpn((db['zen_sun'], db['od'], db['wv']), sunrad0, xi.reshape(-1, 3)).reshape(xi.shape[:-1]).T.squeeze()

    sun_vec = gen_vec_polar(np.deg2rad(env['zen_sun']))
    prob_sun, angr_sun = prob_reflection(-sun_vec, sensor['vec'], env['wind'])
    ref_sun = sw_fresnel(sensor['wv'], angr_sun, env['wtem'], env['sal'])
    rho['sun'] = ((sunrad / n0) * (ref_sun * prob_sun / tprob)).squeeze()

    # Radiance Inc
    logger.debug('Interpolating radiance')
    x = (sdb['wind'], sdb['od'][:, 9], sdb['zen_sun'], sdb['wv'], sdb['zen_view'], sdb['azm_view'])
    xi = np.array(np.meshgrid(env['wind'], env['od'], env['zen_sun'],
                              sensor['wv'], 180 - sensor['ang'][0], 180 - sensor['ang'][1], copy=False)).T
    rad_inc_sca = interpn(x, rad_boa_sca, xi.reshape(-1, 6)).reshape(xi.shape[:-1]).T.squeeze()
    xi = np.array(np.meshgrid(env['wind'], env['od'], env['zen_sun'],
                              sensor['wv'], sensor['ang'][0], 180 - sensor['ang'][1]), copy=False).T
    rad_mea_sca = interpn(x, rad_boa_sca, xi.reshape(-1, 6)).reshape(xi.shape[:-1]).T.squeeze()
    rho_sca = rad_mea_sca / rad_inc_sca

    # Radiance Inc
    logger.debug('Interpolating radiance again')
    x = (vdb['wind'], vdb['od'][:, 9], vdb['zen_sun'], vdb['wv'], vdb['zen_view'], vdb['azm_view'])
    xi = np.array(np.meshgrid(env['wind'], env['od'], env['zen_sun'],
                              sensor['wv'], 180 - sensor['ang'][0], 180 - sensor['ang'][1], copy=False)).T
    rad_inc_vec = interpn(x, rad_boa_vec, xi.reshape(-1, 6)).reshape(xi.shape[:-1]).T.squeeze()
    xi = np.array(np.meshgrid(env['wind'], env['od'], env['zen_sun'],
                              sensor['wv'], sensor['ang'][0], 180 - sensor['ang'][1], copy=False)).T
    rad_mea_vec = interpn(x, rad_boa_vec, xi.reshape(-1, 6)).reshape(xi.shape[:-1]).T.squeeze()
    rho_vec = rad_mea_vec / rad_inc_vec

    rho['sca2vec'] = rho_vec / rho_sca
    rho['rho'] = rho['sky'] * rho['sca2vec'] + rho['sun']
    return rho
