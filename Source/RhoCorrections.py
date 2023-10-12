import os
import time

import numpy as np

import ZhangRho
from Source.ConfigFile import ConfigFile
from Source.Utilities import Utilities
from Source.HDFRoot import HDFRoot

class RhoCorrections:

    @staticmethod
    def M99Corr(windSpeedMean, SZAMean, relAzMean, Propagate = None,
                AOD=None, cloud=None, wTemp=None, sal=None, waveBands=None):
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

        Delta = Propagate.M99_Rho_Uncertainty(mean_vals=[windSpeedMean, SZAMean, relAzMean],
                                              uncertainties=[1, 0.5, 3])

        # TODO: Model error estimation, requires ancillary data to be switched on. This could create a conflict.
        if not any([AOD is None, wTemp is None, sal is None, waveBands is None]) and \
                ((ConfigFile.settings["bL1bCal"] > 1) or (ConfigFile.settings['SensorType'].lower() == "seabird")):
            # Fix: Truncate input parameters to stay within Zhang ranges:
            # AOD
            AOD = np.min([AOD,0.2])
            # SZA
            if 60<SZAMean<70:
                SZAMean = SZAMean
            elif SZAMean>=70:
                raise ValueError('SZAMean is to high (%s), Zhang correction cannot be performed above SZA=70.')
            # wavelengths in range [350-1000] nm
            newWaveBands = [w for w in waveBands if w>=350 and w<=1000]
            # Wavebands clips the ends off of the spectra reducing the amount of values from 200 to 189 for
            # TriOS_NOTRACKER. We need to add these specra back into rhoDelta to prevent broadcasting errors later

            zhang, _ = RhoCorrections.ZhangCorr(windSpeedMean, AOD, cloud, SZAMean, wTemp, sal,
                                                relAzMean, newWaveBands)

            # get the relative difference between mobley and zhang and add in quadrature as uncertainty component
            # pct_diff = np.abs((zhang['ρ'] / rhoScalar) - 1)
            pct_diff = np.abs((zhang / rhoScalar) - 1)
            tot_diff = np.power(np.power(Delta, 2) + np.power(pct_diff, 2), 0.5)
            tot_diff[np.isnan(tot_diff)==True] = 0  # ensure no NaNs are present in the uncertainties.

            # add back in filtered wavelengths
            rhoDelta = []
            i = 0
            for w in waveBands:
                if w>=350 and w<=1000:
                    rhoDelta.append(tot_diff[i])
                    i += 1
                else:
                    # in cases where we are outside the range in which Zhang is calculated a placeholder is used
                    rhoDelta.append(np.power(np.power(Delta, 2) + np.power(0.003, 2), 0.5))
                    # TODO: define how uncertainties outside of zhang range should be addressed (next TC meeting?)
            # if uncertainty is NaN then we cannot estimate what the uncertainty should be. We could argue that 0 could
            # be replaced by np.power(np.power(Delta, 2) + np.power(0.003, 2), 0.5). I personally think it's best to
            # say that we have no uncertainty for that pixel should Zhang be invalid.
            #   Why would Zhang have NaNs?
            #   Is this a case where we are outside the AOD range of the Zhang matrix?
            #   If so, we could set it to the top limit as we do in ProcessL2 for Zhang rho.
            #   If so, and this is a common problem, we may consider whether we can build rho bigger
            #   to accommodate a wider range of AOD(?) DAA
        else:
            # this is temporary. It is possible for users to not select any ancillary data in the config, meaning Zhang
            # Rho will fail. It is far too easy for a user to do this, so I added the following line to make sure the
            # processor doesn't break.
            # 0.003 was chosen because it is the only number with any scientific justification
            # (estimated from Ruddick 2006).
            rhoDelta = np.power(np.power(Delta, 2) + np.power(0.003, 2), 0.5)

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
    def ZhangCorr(windSpeedMean, AOD, cloud, sza, wTemp, sal, relAz, waveBands, Propagate = None):
        ''' Requires xarray: http://xarray.pydata.org/en/stable/installing.html
        Recommended installation using Anaconda:
        $ conda install xarray dask netCDF4 bottleneck'''

        msg = 'Calculating Zhang glint correction.'
        print(msg)
        Utilities.writeLogFile(msg)

        # === environmental conditions during experiment ===
        env = {'wind': windSpeedMean, 'od': AOD, 'C': cloud, 'zen_sun': sza, 'wtem': wTemp, 'sal': sal}

        # === The sensor ===
        # the zenith and azimuth angles of light that the sensor will see
        # 0 azimuth angle is where the sun located
        # positive z is upward
        sensor = {'ang': np.array([40, 180 - relAz]), 'wv': np.array(waveBands)}

        # define uncertainties and create variable list for punpy. Inputs cannot be ordered dictionaries
        varlist = [windSpeedMean, AOD, 0.0, sza, wTemp, sal, relAz, np.array(waveBands)]
        ulist = [1.0, 0.01, 0.0, 0.5, 2, 0.5, 3, None]

        tic = time.process_time()
        rhoVector = ZhangRho.get_sky_sun_rho(env, sensor, round4cache=True)['rho']
        print(f'Zhang17 Elapsed Time: {time.process_time() - tic:.1f} s')

        if Propagate is None:
            rhoDelta = 0.003  # Unknown; estimated from Ruddick 2006
        else:
            rhoDelta = Propagate.zhangWrapper(mean_vals=varlist, uncertainties=ulist,
                                                       waveSubset=np.array(waveBands))

        return rhoVector, rhoDelta
