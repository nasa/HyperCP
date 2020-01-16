
import collections

from ConfigFile import ConfigFile
from Utilities import Utilities
import get_sky_sun_rho

class RhoCorrections:

    @staticmethod 
    def RuddickCorr(sky750,rhoSky,windSpeedMean):
        ''' Ruddick 2006 L&O'''
        if sky750 >= 0.05:
            # Cloudy conditions: no further correction
            if sky750 >= 0.05:
                msg = f'Sky 750 threshold triggered for cloudy sky. Rho set to {rhoSky}.'
                print(msg)
                Utilities.writeLogFile(msg)
            rhoSky = rhoSky
            rhoDelta = 0.003 # Unknown, presumably higher...

        else:
            # Clear sky conditions: correct for wind
            # Set wind speed here
            w = windSpeedMean
            rhoSky = 0.0256 + 0.00039 * w + 0.000034 * w * w
            rhoDelta = 0.003 # Ruddick 2006 Appendix 2; intended for clear skies as defined here

            msg = f'Rho_sky: {rhoSky:.4f} Wind: {w:.1f} m/s'
            print(msg)
            Utilities.writeLogFile(msg)
            
        return rhoSky, rhoDelta

    @staticmethod
    def ZhangCorr(windSpeedMean,AOD,cloud,solZen,wTemp,sal,relAz,waveBands):
        ''' Requires xarray: http://xarray.pydata.org/en/stable/installing.html
        Recommended installation using Anaconda:
        
        $ conda install xarray dask netCDF4 bottleneck'''

        # === environmental conditions during experiment ===
        env = collections.OrderedDict()
        env['wind'] = windSpeedMean
        env['od'] = AOD
        env['C'] = cloud 
        env['zen_sun'] = solZen
        env['wtem'] = wTemp
        env['sal'] = sal

        # === The sensor ===
        # the zenith and azimuth angles of light that the sensor will see
        # 0 azimuth angle is where the sun located
        # positive z is upward
        sensor = collections.OrderedDict()
        sensor['ang'] = [40,180-relAz]
        sensor['wv'] = waveBands

        rhoSky = get_sky_sun_rho.Main(env,sensor)

        # rhoSky=3.14159
        rhoDelta = 0.003 # Unknown
        
        return rhoSky, rhoDelta
