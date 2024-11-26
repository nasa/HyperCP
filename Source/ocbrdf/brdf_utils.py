import numpy as np
import xarray as xr
import os

# Define default auxiliary data file (OLCI OCP ADF)
ref_path = os.path.dirname(os.path.realpath(__file__))
# ADF_OCP = os.path.join(ref_path, '..', 'AuxiliaryData/OCP/S3A_OL_2_OCP_AX_20160216T000000_20991231T235959_20240327T100000___________________EUM_O_AL_008.SEN3/OL_2_OCP_AX.nc')
ADF_OCP = os.path.join(ref_path, 'BRDF_LUTs','BRDF_%s.nc')

def solve_2nd_order_poly(A, B, C):
    """ Solve 2nd order polynomial inversion 
    where coefficients are xr dataArray
    Take only positive solution, otherwise provide 0.
    """

    # Compute solution according to sign of delta
    delta = B*B - 4*A*C
    mask = delta > 0
    
    # By default (and when delta < 0), take value at extremum
    x = - B / (2*A)
    
    # When delta > 0, take biggest solutions
    x_1 = (-B.where(mask) - np.sqrt(delta.where(mask))) / (2*A.where(mask))
    x_2 = (-B.where(mask) + np.sqrt(delta.where(mask))) / (2*A.where(mask))
    x_sol = xr.where(x_1 > x_2, x_1, x_2)
    x = xr.where(delta > 0, x_sol, x)
    
    # Take only positive value
    x = xr.where(x > 0, x, 0.)

    return x

def drop_unused_coords(var):
    for coord in var.coords:
        if coord not in var.dims:
            var = var.drop(coord)
    return var

def squeeze_trivial_dims(ds,dimOrderAccordingTo='Rw'):
    squeezedDims = {}
    for d0,dim in enumerate(ds[dimOrderAccordingTo].dims):
        if ds.sizes[dim] == 1:
            squeezedDims[dim] = d0

    return ds.squeeze(), squeezedDims
