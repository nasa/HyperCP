
import collections
import os
import numpy as np

from ConfigFile import ConfigFile
from Utilities import Utilities
from HDFRoot import HDFRoot
import ZhangRho

class RhoCorrections:

    @staticmethod
    def M99Corr(windSpeedMean,SZAMean,relAzMean):
        ''' Mobley 1999 AO'''

        msg = 'Calculating M99 glint correction with complete LUT'
        print(msg)
        Utilities.writeLogFile(msg)

        theta = 40 # viewing zenith angle
        winds = np.arange(0, 14+1, 2)       # 0:2:14
        szas = np.arange(0, 80+1, 10)       # 0:10:80
        phiViews = np.arange(0, 180+1, 15)  # 0:15:180 # phiView is relAz

        # Find the nearest values in the LUT
        wind_idx = Utilities.find_nearest(winds, windSpeedMean)
        wind = winds[wind_idx]
        sza_idx = Utilities.find_nearest(szas, SZAMean)
        sza = szas[sza_idx]
        relAz_idx = Utilities.find_nearest(phiViews, relAzMean)
        relAz = phiViews[relAz_idx]

        # load in the LUT HDF file
        inFilePath = os.path.join(ConfigFile.fpHySP, 'Data','rhoTable_AO1999.hdf')
        try:
            lut = HDFRoot.readHDF5(inFilePath)
        except:
            msg = "Unable to open M99 LUT."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)

        lutData = lut.groups[0].datasets['LUT'].data
        # convert to a 2D array
        lut = np.array(lutData.tolist())
        # match to the row
        row = lut[(lut[:,0] == wind) & (lut[:,1] == sza) & \
            (lut[:,2] == theta) & (lut[:,4] == relAz)]

        rhoScalar = row[0][5]
        rhoDelta = 0.003 # Unknown; estimated from Ruddick 2006

        return rhoScalar, rhoDelta

    @staticmethod
    def threeCCorr(sky750,rhoDefault,windSpeedMean):
        ''' Groetsch et al. 2017 PLACEHOLDER'''
        msg = 'Calculating 3C glint correction'
        print(msg)
        Utilities.writeLogFile(msg)

        if sky750 >= 0.05:
            # Cloudy conditions: no further correction
            if sky750 >= 0.05:
                msg = f'Sky 750 threshold triggered for cloudy sky. Rho set to {rhoDefault}.'
                print(msg)
                Utilities.writeLogFile(msg)
            rhoScalar = rhoDefault
            rhoDelta = 0.003 # Unknown, presumably higher...

        else:
            # Clear sky conditions: correct for wind
            # Set wind speed here
            w = windSpeedMean
            rhoScalar = 0.0256 + 0.00039 * w + 0.000034 * w * w
            rhoDelta = 0.003 # Ruddick 2006 Appendix 2; intended for clear skies as defined here

            msg = f'Rho_sky: {rhoScalar:.6f} Wind: {w:.1f} m/s'
            print(msg)
            Utilities.writeLogFile(msg)

        return rhoScalar, rhoDelta

    @staticmethod
    def ZhangCorr(windSpeedMean,AOD,cloud,sza,wTemp,sal,relAz,waveBands):
        ''' Requires xarray: http://xarray.pydata.org/en/stable/installing.html
        Recommended installation using Anaconda:
        $ conda install xarray dask netCDF4 bottleneck'''

        msg = 'Calculating Zhang glint correction. This can take several minutes.'
        print(msg)
        Utilities.writeLogFile(msg)

        # === environmental conditions during experiment ===
        env = collections.OrderedDict()
        env['wind'] = windSpeedMean
        env['od'] = AOD
        env['C'] = cloud # Not used
        env['zen_sun'] = sza
        env['wtem'] = wTemp
        env['sal'] = sal

        # === The sensor ===
        # the zenith and azimuth angles of light that the sensor will see
        # 0 azimuth angle is where the sun located
        # positive z is upward
        sensor = collections.OrderedDict()
        sensor['ang'] = [40,180-relAz] # relAz should vary from about 90-135
        sensor['wv'] = waveBands

        rhoStructure = ZhangRho.Main(env,sensor)

        rhoDelta = 0.003 # Unknown; estimated from Ruddick 2006

        return rhoStructure, rhoDelta
