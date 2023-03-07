# System imports
import os
import sys
import time

# maths imports
import numpy as np
from scipy.interpolate import interpn

# storage imports
import collections
import xarray as xr

# Groups in db.mat
DB, QUADS, SDB, VDB = None, None, None, None
# Vars. in db.mat
SKYRAD0, SUNRAD0, RAD_BOA_SCA, RAD_BOA_VEC = None, None, None, None


def load_db():
    # global appropriate here as values are constants
    global DB, QUADS, SDB, VDB, SKYRAD0, SUNRAD0, RAD_BOA_SCA, RAD_BOA_VEC

    db_path = './Data/Zhang_rho_db.mat'
    DB = xr.open_dataset(db_path, group='db', engine='netcdf4')
    QUADS = xr.open_dataset(db_path, group='quads', engine='netcdf4')
    SDB = xr.open_dataset(db_path, group='sdb', engine='netcdf4')
    VDB = xr.open_dataset(db_path, group='vdb', engine='netcdf4')
    SKYRAD0 = xr.open_dataset(db_path, engine='netcdf4')['skyrad0']
    SUNRAD0 = xr.open_dataset(db_path, engine='netcdf4')['sunrad0']
    RAD_BOA_SCA = xr.open_dataset(db_path, engine='netcdf4')['Radiance_BOA_sca']
    RAD_BOA_VEC = xr.open_dataset(db_path, engine='netcdf4')['Radiance_BOA_vec']


def Main(env, sensor):
    ρ = collections.OrderedDict()
    load_db()

    sensor['ang2'] = []
    for i in range(len(sensor['ang'])):
        sensor['ang2'].append(sensor['ang'][i] + np.array[0, 180])

    sensor['pol'] = np.deg2rad(sensor['ang'])
    sensor['vec'] = mp_soh2cart(sensor['pol'][1], sensor['pol'][0])
    sensor['pol2'] = np.deg2rad(sensor['ang2'])
    sensor['loc2'] = find_quads(*sensor['pol2'])
