import netCDF4
import numpy as np
import sys
import xarray as xr
from .brdf_model_L11 import L11
from .brdf_model_O23 import O23
from .brdf_utils import ADF_OCP

"""
Main BRDF correction module
    Works with xarray dataset as input
    Required spectral dimension is "bands", others dimensions are free
    Required fields in input dataset:
        Rw: directional marine reflectance
        sza: sun zenith angle
        vza: view zenith angle
        raa: relative azimuth angle (raa=0 for sun and view on same side)
    Optional fields in inout dataset:
        Rw_unc: uncertainty of Rw (if missing, set to zero)
    Output fields in dataset: 
        nrrs: fully normalized remote-sensing reflectance
        rho_ex_w: nrrs * PI
        omega_b: bb/(a+bb)
        eta_b: bbw/bb
        C_brdf: BRDF correction factor
        brdf_unc: uncertainty of C_brdf
        nrrs_unc : uncertainty of nrrs
"""
def brdf_prototype(ds, adf=None, brdf_model='L11'):

    # Initialise model
    if brdf_model == 'L11':
        BRDF_model = L11(bands=ds.bands, adf=None) # Don't use brdf_py.ADF context
    elif brdf_model == 'O23':
        BRDF_model = O23(bands=ds.bands, adf=None) # Don't use brdf_py.ADF context
    else:
        print("BRDF model %s not existing"%brdf_model)
        sys.exit(1)

    # Init pixel
    BRDF_model.init_pixels(ds['sza'], ds['vza'], ds['raa'])

    # Compute IOP and normalize by iterating
    ds['nrrs'] = ds['Rw'] / np.pi
    for iter_brdf in range(BRDF_model.niter):
        ds['omega_b'], ds['eta_b'] = BRDF_model.backward(ds['nrrs'], iter_brdf)

        # Apply forward model in both geometries
        rrs_mod = BRDF_model.forward(ds.omega_b, ds.eta_b)
        rrs_mod0 = BRDF_model.forward(ds.omega_b, ds.eta_b, normalized=True)

        # Normalize reflectance
        ds['C_brdf'] = rrs_mod0 / rrs_mod
        ds['nrrs'] = ds['Rw']/np.pi * ds['C_brdf']


    # Compute uncertainty
    brdf_uncertainty(ds)
    
    # Compute flag
    ds['flags_level2'] = ds['Rw']*0 #TODO

    # Convert to reflectance unit
    ds['rho_ex_w'] = ds['nrrs'] * np.pi

    return ds

''' Compute uncertainty of BRDF factor and propagate to nrrs '''
def brdf_uncertainty(ds, adf=None):
    
    # Read LUT
    if adf is None:
        adf = ADF_OCP
    # LUT = xr.open_dataset(adf,group='BRDF').unc
    LUT = xr.open_dataset(adf,group='BRDF')['unc']
    
    # Interpolate relative uncertainty
    unc = LUT.interp(lambda_unc=ds.bands, theta_s_unc=ds.theta_s, theta_v_unc=ds.theta_v, delta_phi_unc=ds.delta_phi)

    
    # Compute absolute uncertainty of factor
    ds['brdf_unc'] = unc * ds['C_brdf']

    # Propagate to nrrs
    nrrs_unc2 = ds['brdf_unc']*ds['brdf_unc']*ds['Rw']*ds['Rw']
    if 'Rw_unc' in ds:
        nrrs_unc2 += ds['C_brdf']*ds['C_brdf']*ds['Rw_unc']*ds['Rw_unc']
    ds['nrrs_unc'] = np.sqrt(nrrs_unc2)



