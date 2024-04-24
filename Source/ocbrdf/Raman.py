import numpy as np
import xarray as xr

''' Raman correction from Lee et al?. (2013):
      Penetration of UV-visible solar radiation in the global oceans:
      Insights from ocean color remote sensing. J Geophys Res Oceans 2013;118:4241–55

    Spectral interpolation done at the nearest bands

'''

""" Class for Raman correction LUT """ # TODO store and read in the ADF
class Raman():
    def __init__(self):
        bands = [412,443,488,531,551,667]
        coords = {'bands': bands}
        self.alpha = xr.DataArray([0.003,0.004,0.011,0.015,0.017,0.018], dims='bands', coords=coords)
        self.beta1 = xr.DataArray([0.014,0.015,0.010,0.010,0.010,0.010], dims='bands', coords=coords)
        self.beta2 = xr.DataArray([-0.022,-0.023,-0.051,-0.070,-0.080,-0.081], dims='bands', coords=coords)

    def correct(self, Rrs):
        # Interpolate coefficients at nearest bands
        interp_opt = {'method':'nearest', 'kwargs':{'fill_value':'extrapolate'}}
        alpha = self.alpha.interp(bands=Rrs.bands, **interp_opt)
        beta1 = self.beta1.interp(bands=Rrs.bands, **interp_opt)
        beta2 = self.beta2.interp(bands=Rrs.bands, **interp_opt)

        # Select reference bands closest to 440 and 550
        Rrs440 = Rrs.sel(bands=440, method='nearest')
        Rrs550 = Rrs.sel(bands=550, method='nearest')

        # Compute Raman factor
        RF = alpha*Rrs440/Rrs550 + beta1*np.power(Rrs550,beta2)

        # Correct
        return Rrs/(1+RF)

