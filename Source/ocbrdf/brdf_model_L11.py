import numpy as np
import xarray as xr

from .brdf_utils import ADF_OCP, solve_2nd_order_poly, drop_unused_coords
from .Raman import Raman


''' Lee et al. (2011) BRDF correction
    With QAA v6 inversion

'''

# Init Raman class
Raman = Raman()

""" Class for L11 coefficients """
class Coeffs():
    def __init__(self,Gw0,Gw1,Gp0,Gp1):
        self.Gw0 = Gw0
        self.Gw1 = Gw1
        self.Gp0 = Gp0
        self.Gp1 = Gp1

""" Class for L11 BRDF model """
class L11:

    """ Initialise L11 model: BRDF LUT, coeffs, QAA parameters, water IOPs LUT
        Note: bands are fixed and defined at class initilization, but could be initialized in init_pixels if needed
    """
    def __init__(self, bands, adf=None):
        if adf is None:
            adf = ADF_OCP

        # Check required bands are existing, within a 10 nm threshold
        self.bands = bands
        threshold = 10.
        bands_required = [442, 490, 560, 665]
        bands_ref = bands.sel(bands=bands_required, method='nearest')
        for band_ref, band_required in zip(bands_ref, bands_required):
            assert abs(band_ref - band_required) < threshold, 'Band %d nm missing or too far'% band_ref
        self.b442, self.b490, self.b560, self.b665 = bands_ref

        # Read BRDF LUT and compute default coeffs
        LUT_OCP = xr.open_dataset(adf % 'L11',engine='netcdf4')
        self.LUT = xr.Dataset()
        self.LUT['Gw0'] = LUT_OCP.Gw0
        self.LUT['Gw1'] = LUT_OCP.Gw1
        self.LUT['Gp0'] = LUT_OCP.Gp0
        self.LUT['Gp1'] = LUT_OCP.Gp1

        self.coeffs0 = self.interp(0.,0.,0.)
        self.coeffs = Coeffs(np.nan,np.nan,np.nan,np.nan)

        # Read IOPs of pure water (store in LUT for further spectral interpolation)
        self.awLUT = LUT_OCP.aw.rename({'IOP_wl':'bands'})
        self.bbwLUT = LUT_OCP.bbw.rename({'IOP_wl':'bands'})

        # Read QAA parameters
        self.a0G = LUT_OCP.a0G.values
        self.a0R = LUT_OCP.a0R.values
        self.gamma = LUT_OCP.gamma.values
        self.niter = LUT_OCP.niter.values
              
    """ Initialize pixel: coefficient at current geometry and water IOP at current bands """
    def init_pixels(self, theta_s, theta_v, delta_phi):
        self.coeffs = self.interp(theta_s, theta_v, delta_phi)

        # Compute IOPs at current bands
        self.aw = self.awLUT.interp(bands = self.bands, kwargs={'fill_value':'extrapolate'})
        self.bbw = self.bbwLUT.interp(bands = self.bands, kwargs={'fill_value':'extrapolate'})

    """ Interpolate coefficients """
    def interp(self, theta_s, theta_v, delta_phi):
        Gw0 = self.LUT.Gw0.interp(theta_s=theta_s,theta_v=theta_v,delta_phi=delta_phi)
        Gw1 = self.LUT.Gw1.interp(theta_s=theta_s,theta_v=theta_v,delta_phi=delta_phi)
        Gp0 = self.LUT.Gp0.interp(theta_s=theta_s,theta_v=theta_v,delta_phi=delta_phi)
        Gp1 = self.LUT.Gp1.interp(theta_s=theta_s,theta_v=theta_v,delta_phi=delta_phi)
        return Coeffs(Gw0,Gw1,Gp0,Gp1)

    """ Compute remote-sensing reflectance, without Raman effect (vanish in the normalization factor) """
    def forward(self, ds, normalized=False):
        omega_b = ds['omega_b']
        eta_b = ds['eta_b']

        if normalized:
            coeffs = self.coeffs0
        else:
            coeffs = self.coeffs
        mod_Rrs = (coeffs.Gw0+coeffs.Gw1*omega_b*eta_b)*omega_b*eta_b + (coeffs.Gp0+coeffs.Gp1*omega_b*(1-eta_b))*omega_b*(1-eta_b)

        return mod_Rrs

    """ Apply QAA to retrieve IOP (omega_b, eta_b) from Rrs """
    def backward(self, ds, iter_brdf):

        Rrs = ds['nrrs']

        # Select G coeff according to iteration
        if iter_brdf == 0:
            coeffs = self.coeffs
        else:
            coeffs = self.coeffs0

        # Apply Raman correction
        Rrs = Raman.correct(Rrs)
       
        # Local renaming of bands 
        b442, b490, b560, b665 = self.b442, self.b490, self.b560, self.b665

        # Apply upper and lower limits to Rrs(665) #TODO check if not finite or missing?
        Rrs442 = Rrs.sel(bands=b442)
        Rrs490 = Rrs.sel(bands=b490)
        Rrs560 = Rrs.sel(bands=b560)
        Rrs665 = Rrs.sel(bands=b665)
        mask= ((Rrs665 > 20*np.power(Rrs560,1.5)) | (Rrs665 < 0.9*np.power(Rrs560, 1.7)))
        if np.any(mask):
            Rrs665_ = 1.27*np.power(Rrs560, 1.47) + 0.00018*np.power(Rrs490/Rrs560,-3.19)
            # Redefine Rrs665 and Rrs[bands=b665] (both important for computations below)
            Rrs665 = xr.where(mask, Rrs665_, Rrs665)
            Rrs.loc[dict(bands=b665)] = Rrs665

        # Calculate rrs below water for absorption computation
        rrs = Rrs / (0.52 + 1.7*Rrs)

        # Define reference band band0 according to Rrs at 665 nm
        # and compute total absorption
        mask = Rrs.sel(bands=b665) < 0.0015
        band0 = xr.where(mask, b560, b665)
        aw0 = xr.where(mask, self.aw.sel(bands=b560), self.aw.sel(bands=b665))
        bbw0 = xr.where(mask, self.bbw.sel(bands=b560), self.bbw.sel(bands=b665))
        Rrs0 = xr.where(mask, Rrs.sel(bands=b560), Rrs.sel(bands=b665))
        # Compute a0 when band0 = b560
        rrs442 = rrs.sel(bands=b442)
        rrs490 = rrs.sel(bands=b490)
        rrs560 = rrs.sel(bands=b560)
        rrs665 = rrs.sel(bands=b665)
        chi = np.log10((rrs442 + rrs490) / (rrs560 + 5.0 * rrs665*rrs665 / rrs490))
        poly = np.polynomial.polynomial.polyval(chi, self.a0G)
        a0_560 = aw0 + np.power(10., poly)
        # Compute a0 when band0 = b665
        a0_665 = aw0 + self.a0R[0] * np.power(Rrs665 / (Rrs442 + Rrs490), self.a0R[1])
        # Compute a0 for all pixels
        a0 = xr.where(mask, a0_560, a0_665)

        # Compute bbp at band0 by 2nd order polynomial inversion
        k0 = a0 + bbw0
        cA = coeffs.Gp0 + coeffs.Gp1 - Rrs0
        cB = coeffs.Gw0 * bbw0 + (coeffs.Gp0 -2*Rrs0) *k0
        cC = (coeffs.Gw0 * bbw0 - Rrs0 * k0) * k0 + coeffs.Gw1 * bbw0 * bbw0
        bbp0 = solve_2nd_order_poly(cA, cB, cC)

        # Assume bbp0 = 0 if solve_2nd_order_poly fails to retrieve non-negative numbers
        # In this case activate bbp0_fail flag (which in turn activates QAA_fail)
        bbp0_fail = (bbp0 < 0) | (np.isinf(bbp0)) | (np.isnan(bbp0))
        bbp0 = xr.where(bbp0_fail, 0, bbp0)

        # Compute bbp slope and extrapolate at all bands
        gamma = self.gamma[0] * (1.0 - self.gamma[1] * np.exp(-self.gamma[2] * (rrs442 / rrs560)))
        bbp = bbp0 * np.power(band0 / self.bands, gamma)

        # Compute total bb
        bb = self.bbw + bbp

        # Compute quasi-diffuse attenuation coefficient k at each band
        # by 2nd order polynomial inversion
        cA = Rrs
        cB = - (coeffs.Gw0 * self.bbw + coeffs.Gp0 * bbp)
        cC = - (coeffs.Gw1 * self.bbw *self.bbw + coeffs.Gp1 * bbp * bbp)
        k = solve_2nd_order_poly(cA, cB, cC)

        # If k is not a positive value, then
        #   i) k --> bbw + aw
        #   ii) k_fail flag is activated
        k_fail = (k <= 0) | (np.isinf(k)) | (np.isnan(k))
        k = xr.where(k_fail, self.aw + self.bbw, k)

        # Drop unused coords to avoid issues
        bb        = drop_unused_coords(bb)
        k         = drop_unused_coords(k)
        k_fail    = drop_unused_coords(k_fail)
        bbp0_fail = drop_unused_coords(bbp0_fail)

        # Set QAA_fail is either bbp0_fail or k_fail are activated
        ds['QAA_fail'] = (bbp0_fail) | (k_fail)

        # Compute final IOPs
        ds['omega_b'] = bb / k
        ds['eta_b'] = self.bbw / bb

        return ds

