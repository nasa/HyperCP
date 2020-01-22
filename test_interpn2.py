from scipy.interpolate import interpn
import numpy as np
import xarray as xr

# Data space in the 6D rad_boa array
azimuth = np.arange(0, 185, 5) # 37
senzen = np.arange(0, 185, 5) # 37
# wave = np.arange(350,1050,5)    # 140
wave = np.array([350, 360, 370, 380, 390, 410, 440, 470, 510, 550, 610, 670, 750, 865, 1040, 1240, 1640, 2250]) # 18
solzen = np.arange(0,65,5)     # 13
aod = np.arange(0,0.55,0.05)    # 11
wind = np.arange(0, 20, 5)      # 4
coords = [azimuth, senzen, wave, solzen, aod, wind]


# Simulated rad_boa
rad_boa = np.random.rand(
    azimuth.size,senzen.size,wave.size,solzen.size,aod.size,wind.size,) # 37, 37, 140/18, 13, 11, 4

azimuth0 = 135              # 1
senzen0 = 140               # 1
wave0 = np.arange(350,1010,10) # 66
solzen0 = 30                # 1
aod0 = 0.1                  # 1
wind0 = 10                  # 1
interp_coords = [azimuth0, senzen0, wave0, solzen0, aod0, wind0]

da = xr.DataArray(name='Radiance_BOA',
                data=rad_boa,
                dims=['azimuth','senzen','wave','solzen','aod','wind'],
                coords=coords)

interp_dict = dict(zip(da.dims, interp_coords))
rad_inc_scaXR = da.interp(**interp_dict).squeeze()

print('hi')