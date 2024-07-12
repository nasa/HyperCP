import netCDF4
import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull
import os
from matplotlib import pyplot as plt
import sys
import xarray as xr

from .brdf_utils import ADF_OCP, solve_2nd_order_poly

''' Morel et al. (2002) BRDF correction
    R gothic included
    f/Q LUT as in OLCI operational processor (See OLCI "OCP" ADF)
    With OC4ME Chl inversion, 2 iterations, no convergence criterion on delta_Chl applied (1%)
'''

""" Class for M02 coefficients """


class Coeffs():
    def __init__(self, Rgoth, foq):
        self.Rgoth = Rgoth
        self.foq = foq


""" Class for M02 BRDF model """
class M02:
    """ Initialise M02 model: BRDF LUT, coeffs, OC4ME parameters, water IOPs LUT
        Note: bands are fixed and defined at class initilization, but could be initialized in init_pixels if needed
    """

    def __init__(self, bands, aot, wind, adf=None):
        if adf is None:
            adf = ADF_OCP

        # Check required bands are existing, within a 25 nm threshold
        self.bands = bands
        threshold = 25.
        bands_required = [442.5, 490, 510, 560]
        bands_ref = bands.sel(bands=bands_required, method='nearest')
        for band_ref, band_required in zip(bands_ref, bands_required):
            assert abs(band_ref - band_required) < threshold, 'Band %d nm missing or too far' % band_ref
        self.b442, self.b490, self.b510, self.b560 = bands_ref

        # Read BRDF LUT and compute default coeffs
        LUT_OCP = xr.open_dataset(adf % 'M02',engine='netcdf4')
        self.LUT = xr.Dataset()

        # Homogeneise naming convention with other methods... (PZA --> OZA transformation comes below...)
        self.LUT['Rgoth'] = LUT_OCP.r_goth_LUT.rename({'PZA_r_goth':'theta_v_Rgoth',
                                                       'wind_speeds_r_goth':'wind_Rgoth'})
        self.LUT['foq'] = LUT_OCP.f_over_q_LUT.rename({'SZA_FOQ':'theta_s',
                                                       'PZA_FOQ':'theta_v',
                                                       'RAA_FOQ':'delta_phi',
                                                       'wind_speeds_FOQ':'wind_foq',
                                                       'tau_a_FOQ':'aot_foq',
                                                       'log_chl_FOQ':'log_chl_foq'})

        # Index of refraction
        self.n_w = float(LUT_OCP.water_refraction_index.data)

        # Remove trivial aot indexation
        self.LUT['foq'] = self.LUT['foq'].squeeze()

        # Interpolate for wind speed.
        self.LUT['Rgoth'] = self.LUT['Rgoth'].interp(wind_Rgoth=np.clip(wind,0,16))
        self.LUT['foq'  ] = self.LUT['foq'  ].interp(wind_foq  =np.clip(wind,0,10))

        #
        self.coeffs0 = self.interp_geometries(0., 0., 0.)
        self.coeffs = Coeffs(np.nan, np.nan)

        # Parameters for the OC4ME chl retrieval
        self.OC4MEcoeff = LUT_OCP.log10_coeff_LUT.values
        self.OC4MEepsilon = LUT_OCP.oc4me_epsilon
        self.OC4MEchl0 = float(LUT_OCP.oc4me_chl0.values)
        self.niter = LUT_OCP.oc4me_niter

    """ Initialize pixel: coefficient at current geometry and water IOP at current bands """

    def init_pixels(self, theta_s, theta_v, delta_phi):
        self.coeffs = self.interp_geometries(theta_s, theta_v, delta_phi)

    """ Interpolate coefficients """
    def interp_geometries(self, theta_s, theta_v, delta_phi):
        # Transform PZA to VZA (Snell's refraction Law)
        theta_v = np.rad2deg(np.arcsin(np.sin(np.deg2rad(theta_v)) / self.n_w))
        theta_v_Rgoth_0 = np.clip(theta_v,
                                   float(np.min(self.LUT.theta_v_Rgoth)),
                                   float(np.max(self.LUT.theta_v_Rgoth)))

        theta_v_0 = np.clip(theta_v,
                                   float(np.min(self.LUT.theta_v)),
                                   float(np.max(self.LUT.theta_v)))

        Rgoth = self.LUT.Rgoth.interp(theta_v_Rgoth=theta_v_Rgoth_0)
        foq = self.LUT.foq.interp(theta_s=theta_s, theta_v=theta_v_0, delta_phi=delta_phi)

        return Coeffs(Rgoth, foq)

    """ Compute remote-sensing reflectance"""

    def forward(self, ds, normalized=False):

        if normalized:
            coeffs = self.coeffs0
        else:
            coeffs = self.coeffs

        wave_foq = np.clip(ds['bands'],
                           float(np.min(coeffs.foq.wavelengths_FOQ)),
                           float(np.max(coeffs.foq.wavelengths_FOQ)))

        log10_chl_foq = np.clip(ds['log10_chl'],
                           float(np.min(coeffs.foq.log_chl_foq)/np.log(10)),
                           float(np.max(coeffs.foq.log_chl_foq)/np.log(10)))

        # f/Q LUT indexed with ln(CHL), i.e. log_e(CHL)
        log_chl_foq = log10_chl_foq * np.log(10)

        forward_mod = coeffs.Rgoth * coeffs.foq.interp(wavelengths_FOQ=wave_foq).interp(log_chl_foq=log_chl_foq)

        return forward_mod

    """ Apply QAA to retrieve IOP (omega_b, eta_b) from Rrs """

    def backward(self, ds, iter_brdf):

        Rrs = ds['nrrs']

        # Local renaming of bands
        b442, b490, b510, b560 = self.b442, self.b490, self.b510, self.b560

        # Apply upper and lower limits to Rrs(665) #TODO check if not finite or missing?
        Rrs442 = Rrs.sel(bands=b442)
        Rrs490 = Rrs.sel(bands=b490)
        Rrs510 = Rrs.sel(bands=b510)
        Rrs560 = Rrs.sel(bands=b560)

        # Compute the OC4ME "R"
        # NB: Could be the case that Rrs[442-560]<0,
        #   then ds['log10_chl_OC4ME_Ratio'] will be NaN.
        #   then ds['log10_chl'] will be NaN.
        #   then forward_mod0/forward_mod (in brdf_prototype, ocbrdf/main.py) will be NaN.
        #   then ds['C_BRDF'] = NaN.
        #   In this case, C_BRDF will be set to 1 and C_BRDF_flag will be raised (see brdf_prototype, ocbrdf/main.py).
        ds['log10_chl_OC4ME_Ratio'] = np.log10(np.max([Rrs442, Rrs490, Rrs510], axis=0) / Rrs560)

        ds['log10_chl'] = 0 * ds['log10_chl_OC4ME_Ratio']
        # Apply OC4ME 5-degree polynomial
        for k, Ak in enumerate(self.OC4MEcoeff):
            ds['log10_chl'] += Ak * (ds['log10_chl_OC4ME_Ratio'] ** k)

        ds['theta_s'] = ds['sza']
        ds['theta_v'] = ds['vza']
        ds['delta_phi'] = ds['raa']

        return ds