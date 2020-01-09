
from ConfigFile import ConfigFile
from Utilities import Utilities

class RhoCorrections:

    @staticmethod 
    def RuddickCorr(sky750,rhoSky,windSpeedMean):
        if sky750 >= 0.05:
            # Cloudy conditions: no further correction
            if sky750 >= 0.05:
                msg = f'Sky 750 threshold triggered for cloudy sky. Rho set to {rhoSky}.'
                print(msg)
                Utilities.writeLogFile(msg)
            p_sky = rhoSky
        else:
            # Clear sky conditions: correct for wind
            # Set wind speed here
            w = windSpeedMean
            p_sky = 0.0256 + 0.00039 * w + 0.000034 * w * w
            msg = f'Rho_sky: {p_sky:.4f} Wind: {w:.1f} m/s'
            print(msg)
            Utilities.writeLogFile(msg)
        return p_sky

    @staticmethod
    def ZhangCorr(windSpeedMean,AOD,Cloud,solZen,wTemp,Sal):

        p_sky=3.14159
        
        return p_sky
