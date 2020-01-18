from scipy.interpolate import interpn
import numpy as np
import xarray as xr

db_path = './Data/db.mat'
skyrad0 = xr.open_dataset(db_path)['skyrad0']
db = xr.open_dataset(db_path, group='db')


# # Define the data space in the 4D skyrad0 array
# solzen = np.arange(0,70,10)     # 7
# aod = np.arange(0,0.25,0.05)    # 5
# index = np.arange(1,92477,1)    # 92476
# wave = np.arange(350,1050,5)    # 140

solzen = db.zen_sun.data.flatten()
aod = db.od.data.flatten()
index = np.arange(1,skyrad0.data.shape[1]+1)
wave = db.wv.data.flatten()

# # Simulated skyrad for the values above
# skyrad0 = np.random.rand(
#     solzen.size,aod.size,index.size,wave.size) # 7, 5, 92476, 140

# Data space for desired output values of skyrad 
# with interpolation between input data space
solzen0 = 30                    # 1
aod0 = 0.1                      # 1
index0 = index                  # 92476
wave0 = np.arange(350,1010,10)  # 70

# Matlab
# result = squeeze(interpn(solzen, aod, index, wave,
#                   skyrad0,
#                   solzen0, aod0, index0, wave0))

# # Scipy
# points = (solzen, aod, index, wave)             # 7, 5, 92476, 140
# interp_mesh = np.array(
#     np.meshgrid(solzen0, aod0, index0, wave0))  # 4, 1, 1, 92476, 70
# interp_points = np.moveaxis(interp_mesh, 0, -1) # 1, 1, 92476, 70, 4
# # interp_points = interp_points.reshape(
# #     (interp_mesh.size // interp_mesh.shape[3], 
# #     interp_mesh.shape[3]))                      # 280, 92476
# interp_points = interp_points.reshape(
#     (np.prod(interp_mesh.shape[1:]), 
#     interp_points.shape[-1])) # 6473320, 4

# result = interpn(points, skyrad0, interp_points) # 6473320
# result = result.reshape(interp_mesh.shape[3],interp_mesh.shape[-1])

# def slow():
#     points = (solzen, aod, index, wave)                 # 7, 5, 92476, 140
#     mg = np.meshgrid(solzen0, aod0, index0, wave0)      # 4, 1, 1, 92476, 70
#     interp_points = np.moveaxis(mg, 0, -1)              # 1, 1, 92476, 70, 4
#     result_presqueeze = interpn(points, 
#                                 skyrad0, interp_points) # 1, 1, 92476, 70
#     result = np.squeeze(result_presqueeze,
#                         axis=(0,1))                     # 92476, 70
#     return result

# def fast():
da = xr.DataArray(name='skyrad0',
                data=skyrad0.data,
                dims=['wave','index','aod','solzen'],
                coords=[wave, index, aod, solzen])

result = da.loc[wave0, index0, aod0, solzen0].squeeze()

    # return result

print('hi')