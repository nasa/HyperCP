'''################################# F0 ORIENTED #################################'''

import collections

import numpy as np
import scipy as sp

from Source.HDFRoot import HDFRoot
from Source.SB_support import readSB
import Source.utils.loggingHCP as logging

def TSIS_1(dateTag, wavelength, F0_raw=None, F0_unc_raw=None, wv_raw=None):
    def dop(year):
        # day of perihelion
        years = list(range(2001,2031))
        key = [str(x) for x in years]
        day = [4, 2, 4, 4, 2, 4, 3, 2, 4, 3, 3, 5, 2, 4, 4, 2, 4, 3, 3, 5, 2, 4, 4, 3, 4, 3, 3, 5, 2, 3]
        dop = {key[i]: day[i] for i in range(0, len(key))}
        result = dop[str(year)]
        return result

    if F0_raw is None:
        # Only read this if we haven't already read it in
        fp = 'Data/hybrid_reference_spectrum_p1nm_resolution_c2020-09-21_with_unc.nc'
        # fp = 'Data/Thuillier_F0.sb'
        # print("SB_support.readSB: " + fp)
        # print("Reading : " + fp)
        if not HDFRoot.readHDF5(fp):
            logging.writeLogFileAndPrint("Unable to read TSIS-1 netcdf file.")
            return None
        else:
            F0_hybrid = HDFRoot.readHDF5(fp)
            # F0_raw = np.array(thuillier.data['esun']) # uW cm^-2 nm^-1
            # wv_raw = np.array(thuillier.data['wavelength'])
            for ds in F0_hybrid.datasets:
                if ds.id == 'SSI':
                    F0_raw = ds.data        #  W  m^-2 nm^-1
                    F0_raw = F0_raw * 100 # uW cm^-2 nm^-1
                if ds.id == 'SSI_UNC':
                    F0_unc_raw = ds.data        #  W  m^-2 nm^-1
                    F0_unc_raw = F0_unc_raw * 100 # uW cm^-2 nm^-1
                if ds.id == 'Vacuum Wavelength':
                    wv_raw =ds.data

    # Earth-Sun distance
    day = int(str(dateTag)[4:7])
    year = int(str(dateTag)[0:4])
    eccentricity = 0.01672
    dayFactor = 360/365.256363
    dayOfPerihelion = dop(year)
    dES = 1-eccentricity*np.cos(dayFactor*(day-dayOfPerihelion)) # in AU
    F0_fs = F0_raw*dES

    # Smooth F0 to 10 nm windows centered on data wavelengths
    avg_f0 = np.empty(len(wavelength))
    avg_f0[:] = np.nan
    avg_f0_unc = avg_f0.copy()
    for i, wv in enumerate(wavelength):
        idx = np.where((wv_raw >= wv-5.) & ( wv_raw <= wv+5.))
        if idx:
            avg_f0[i] = np.mean(F0_fs[idx])
            avg_f0_unc[i] = np.mean(F0_unc_raw[idx])
    # F0 = sp.interpolate.interp1d(wv_raw, F0_fs)(wavelength)

    # Use the strings for the F0 dict
    wavelengthStr = [str(wave) for wave in wavelength]
    F0 = collections.OrderedDict(zip(wavelengthStr, avg_f0))
    F0_unc = collections.OrderedDict(zip(wavelengthStr, avg_f0_unc))

    return F0, F0_unc, F0_raw, F0_unc_raw, wv_raw


def Thuillier(dateTag, wavelength):
    def dop(year):
        # day of perihelion
        years = list(range(2001,2031))
        key = [str(x) for x in years]
        day = [4, 2, 4, 4, 2, 4, 3, 2, 4, 3, 3, 5, 2, 4, 4, 2, 4, 3, 3, 5, 2, 4, 4, 3, 4, 3, 3, 5, 2, 3]
        dop = {key[i]: day[i] for i in range(0, len(key))}
        result = dop[str(year)]
        return result

    fp = 'Data/Thuillier_F0.sb'
    print("SB_support.readSB: " + fp)
    if not readSB(fp, no_warn=True):
        logging.writeLogFileAndPrint("Unable to read Thuillier file. Make sure it is in SeaBASS format.")
        return None
    else:
        thuillier = readSB(fp, no_warn=True)
        F0_raw = np.array(thuillier.data['esun']) # uW cm^-2 nm^-1
        wv_raw = np.array(thuillier.data['wavelength'])
        # Earth-Sun distance
        day = int(str(dateTag)[4:7])
        year = int(str(dateTag)[0:4])
        eccentricity = 0.01672
        dayFactor = 360/365.256363
        dayOfPerihelion = dop(year)
        dES = 1-eccentricity*np.cos(dayFactor*(day-dayOfPerihelion)) # in AU
        F0_fs = F0_raw*dES

        F0 = sp.interpolate.interp1d(wv_raw, F0_fs)(wavelength)
        # Use the strings for the F0 dict
        wavelengthStr = [str(wave) for wave in wavelength]
        F0 = collections.OrderedDict(zip(wavelengthStr, F0))

    return F0
