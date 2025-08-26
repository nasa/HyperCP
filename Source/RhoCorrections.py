'''Calculate skylight reflectance factor'''
import os
import time

import numpy as np
import xarray as xr
# import matplotlib.pyplot as plt
import scipy.interpolate as spin

from Source.ZhangRho import get_sky_sun_rho, PATH_TO_DATA
from Source.ConfigFile import ConfigFile
from Source.HDFRoot import HDFRoot
import Source.utils.loggingHCP as logging
import Source.utils.comparing as comparing

class RhoCorrections:
    ''' Object for processing glint corrections '''
    @staticmethod
    def M99Corr(windSpeedMean, SZAMean, relAzMean, Propagate = None,
                AOD=None, cloud=None, wTemp=None, sal=None, waveBands=None):
        ''' Mobley 1999 AO'''

        logging.writeLogFileAndPrint('Calculating M99 glint correction with complete LUT')
        
        theta = 40 # viewing nadir angle of Lt or VZA of Li (TODO: tweak to allow theta=30)
        winds = np.arange(0, 14+1, 2)       # 0:2:14
        szas = np.arange(0, 80+1, 10)       # 0:10:80
        phiViews = np.arange(0, 180+1, 15)  # 0:15:180 # phiView is relAz

        # Find the nearest values in the LUT
        wind_idx = comparing.find_nearest(winds, windSpeedMean)
        wind = winds[wind_idx]
        sza_idx = comparing.find_nearest(szas, SZAMean)
        sza = szas[sza_idx]
        relAz_idx = comparing.find_nearest(phiViews, relAzMean)
        relAz = phiViews[relAz_idx]

        # load in the LUT HDF file
        inFilePath = os.path.join(PATH_TO_DATA, 'rhoTable_AO1999.hdf')
        try:
            lut = HDFRoot.readHDF5(inFilePath)
        except Exception as err:
            msg = f"Unable to open M99 LUT. {err}"
            logging.writeLogFileAndPrint(msg)
            logging.errorWindow("File Error", msg)

        lutData = lut.groups[0].datasets['LUT'].data
        # convert to a 2D array
        lut = np.array(lutData.tolist())
        # match to the row
        row = lut[(lut[:,0] == wind) & (lut[:,1] == sza) & \
            (lut[:,2] == theta) & (lut[:,4] == relAz)]

        rhoScalar = row[0][5]

        Delta = Propagate.M99_Rho_Uncertainty(mean_vals=[windSpeedMean, SZAMean, relAzMean],
                                              uncertainties=[2, 0.5, 3])/rhoScalar

        # TODO: find the source of the windspeed uncertainty to reference this. EMWCF should have this info
        # TODO: Model error estimation, requires ancillary data to be switched on. This could create a conflict.
        if not any([AOD is None, wTemp is None, sal is None, waveBands is None]) and \
                ((ConfigFile.settings["fL1bCal"] > 1) or (ConfigFile.settings['SensorType'].lower() == "seabird") \
                 or (ConfigFile.settings['SensorType'].lower() == "dalec")):
            # Fix: Truncate input parameters to stay within Zhang ranges:
            # AOD
            if AOD > 0.5:
                logging.writeLogFileAndPrint("Warning: AOD > 0.5. Adjusting to 0.5.")
                AOD = 0.5
            # SZA
            if SZAMean > 60:
                logging.writeLogFileAndPrint("Warning: SZA > 60. Adjusting to 60.")
                # raise ValueError('SZAMean is too high (%s), Zhang correction cannot be performed above SZA=70.')
                SZAMean = 60
            # wavelengths in range [350-1000] nm
            newWaveBands = [w for w in waveBands if w >= 350 and w <= 1000]
            # Wavebands clips the ends off of the spectra reducing the amount of values from 200 to 189 for
            # TriOS_NOTRACKER. We need to add these specra back into rhoDelta to prevent broadcasting errors later

            SVA = ConfigFile.settings['fL2SVA']

            try:
                # raise InterpolationError("Forcing full model")
                # Z17 LUT interpolation
                logging.writeLogFileAndPrint('Using LUT interpolations.')
                zhang = RhoCorrections.read_Z17_LUT(windSpeedMean, AOD, SZAMean, wTemp, sal, relAzMean, SVA, newWaveBands)
            except (InterpolationError, NotImplementedError) as err:
                # Full Z17 model
                logging.writeLogFileAndPrint(f'{err}: Unable to use LUT interpolations. Reverting to analytical solution.')
                zhang, _ = RhoCorrections.ZhangCorr(windSpeedMean, AOD, cloud, SZAMean, wTemp, sal, relAzMean, SVA, newWaveBands)

            if isinstance(zhang, float):
                raise ValueError("Interpolation of zhang lookup table failed")

            # |M99 - Z17| is an estimation of model error added to MC M99 uncertainty 
            # in quadrature to give combined uncertainty
            pct_diff = np.abs(rhoScalar - zhang) / rhoScalar  # relative units
            tot_diff = np.sqrt(Delta ** 2 + pct_diff ** 2)
            tot_diff[np.isnan(tot_diff) is True] = 0  # ensure no NaNs are present in the uncertainties.
            tot_diff = tot_diff * rhoScalar  # ensure difference is in proper units
            # add back in filtered wavelengths
            rhoDelta = []
            i = 0
            for w in waveBands:
                if w >= 350 and w <= 1000:
                    rhoDelta.append(tot_diff[i])
                    i += 1
                else:
                    # in cases where we are outside the range in which Zhang is calculated 0.003 from Ruddick is used
                    rhoDelta.append(np.sqrt(Delta**2 + (0.003 / rhoScalar)**2) * rhoScalar)
                    # necessary to convert to relative before propagating, then converted back to absolute
        else:
            # NOTE: It is possible for users to not select any ancillary data in the config, meaning Zhang Rho 
            # will fail. It is far too easy for a user to do this, so I added the following line to make sure the
            # processor doesn't break.
            logging.writeLogFileAndPrint("Z17 innaccessible likely from lack of ancillary data. Fall back on rho_unc est. by Ruddick 2006")

            # 0.003 was chosen because it is the only number with any scientific justification
            # (estimated from Ruddick 2006).
            rhoDelta = np.sqrt(Delta**2 + (0.003 / rhoScalar)**2) * rhoScalar

        return rhoScalar, rhoDelta

    @staticmethod
    def threeCCorr(sky750,rhoDefault,windSpeedMean):
        ''' Groetsch et al. 2017 PLACEHOLDER'''
        logging.writeLogFileAndPrint('Calculating 3C glint correction')

        if sky750 >= 0.05:
            # Cloudy conditions: no further correction
            if sky750 >= 0.05:
                logging.writeLogFileAndPrint(f'Sky 750 threshold triggered for cloudy sky. Rho set to {rhoDefault}.')
            rhoScalar = rhoDefault
            rhoDelta = 0.003 # Unknown, presumably higher...

        else:
            # Clear sky conditions: correct for wind
            # Set wind speed here
            w = windSpeedMean
            rhoScalar = 0.0256 + 0.00039 * w + 0.000034 * w * w
            rhoDelta = 0.003 # Ruddick 2006 Appendix 2; intended for clear skies as defined here

            logging.writeLogFileAndPrint(f'Rho_sky: {rhoScalar:.6f} Wind: {w:.1f} m/s')

        return rhoScalar, rhoDelta

    @staticmethod
    # def ZhangCorr(windSpeedMean, AOD, cloud, sza, wTemp, sal, relAz, waveBands):
    def ZhangCorr(windSpeedMean, AOD, cloud, sza, wTemp, sal, relAz, sva, waveBands, Propagate = None, db = None):
        logging.writeLogFileAndPrint('Calculating Zhang glint correction (FULL MODEL).')

        # === environmental conditions during experiment ===
        env = {'wind': windSpeedMean, 'od': AOD, 'C': cloud, 'zen_sun': sza, 'wtem': wTemp, 'sal': sal}

        # === The sensor ===
        # the zenith and azimuth angles of light that the sensor will see
        # 0 azimuth angle is where the sun located
        # positive z is upward
        sensor = {'ang': np.array([sva, 180 - relAz]), 'wv': np.array(waveBands)}

        # # define uncertainties and create variable list for punpy. Inputs cannot be ordered dictionaries
        varlist = [windSpeedMean, AOD, sza, wTemp + 273.15, sal, relAz, sva, np.array(waveBands)]  # convert wtemp to kelvin
        ulist = [2.0, 0.01, 0.5, 2, 0.5, 3, 0.0, None]
        # TODO: find the source of the windspeed uncertainty to reference this. EMWCF should have this info

        # tic = time.process_time() # CPU time
        tic = time.time()
        rhoVector = get_sky_sun_rho(env, sensor, round4cache=True, DB=db)['rho']
        # logging.writeLogFileAndPrint(f'Zhang17 Elapsed Time: {time.process_time() - tic:.1f} s')
        logging.writeLogFileAndPrint(f'Zhang17 Elapsed Time: {time.time() - tic:.1f} s')

        # Presumably obsolete (Ashley)? -DAA
        # No I'm only changing how the zhang uncertainties work - this all happes in uncertianty_analysis.py - Ashley
        # It will be once the LUT  is finished, right now the Z17 without a propagate object is important for the
        # Monte Carlo runs
        if Propagate is None:
            rhoDelta = 0.003  # Unknown; estimated from Ruddick 2006
        else:
            tic = time.time()
            rhoDelta = Propagate.Zhang_Rho_Uncertainty(mean_vals=varlist,
                                                       uncertainties=ulist,
                                                       )
            logging.writeLogFileAndPrint(f'Zhang_Rho_Uncertainty Elapsed Time: {time.time() - tic:.1f} s')

        return rhoVector, rhoDelta

    @staticmethod
    def read_Z17_LUT(ws, aod, sza, wt, sal, rel_az, sva, nwb) -> np.array:
        """
        windSpeedMean, AOD, SZAMean, wTemp, sal, relAzMean, newWaveBands, zhang

        """        
        logging.writeLogFileAndPrint('Calculating Zhang glint correction (LUT).')
        tic = time.time()
        if sva == 30:
            db_path = "Z17_LUT_30.nc"
            logging.writeLogFileAndPrint("running Z17 interpolation for instrument viewing zenith of 30",False)
        else:
            db_path = "Z17_LUT_40.nc"
            logging.writeLogFileAndPrint("running Z17 interpolation for instrument viewing zenith of 40",False)

        try:
            LUT = xr.open_dataset(os.path.join(PATH_TO_DATA, db_path), engine='netcdf4')
        except FileNotFoundError as err:
            raise InterpolationError(f"cannot find LUT netcdf file {db_path} at {PATH_TO_DATA}") from err

        try:
            if ConfigFile.settings['SensorType'].lower() == "sorad":
                zhang_interp = spin.interpn(
                    points=(
                        LUT.wind.values,
                        LUT.aot.values,
                        LUT.sza.values,
                        LUT.relAz.values,
                        LUT.sal.values,
                        LUT.SST.values,
                        LUT.wavelength.values
                    ),
                    values=LUT.Glint.values,
                    xi=(
                        ws,
                        aod,
                        sza,
                        rel_az,
                        sal,
                        wt,
                        nwb
                    ),
                    method="pchip", # should be cubic - temporary fix due to memory issues
                )
                print('Interpolating Z17 LUT using pchip (3rd order Hermitian Polynomial) method')
            else:
                zhang_interp = spin.interpn(
                    points=(
                        LUT.wind.values,
                        LUT.aot.values,
                        LUT.sza.values,
                        LUT.relAz.values,
                        LUT.sal.values,
                        LUT.SST.values,
                        LUT.wavelength.values
                    ),
                    values=LUT.Glint.values,
                    xi=(
                        ws,
                        aod,
                        sza,
                        rel_az,
                        sal,
                        wt,
                        nwb
                    ),
                    method="cubic",
                )
                print('Interpolating Z17 LUT using cubic method')

            logging.writeLogFileAndPrint(f'Zhang17 LUT Elapsed Time: {time.time() - tic:.1f} s')

        except ValueError as err:
            raise InterpolationError(f"Interpolation of Z17 LUT failed with {err}") from err
        else:
            return zhang_interp


class InterpolationError(Exception):
    def __init__(self, msg):
        super().__init__(msg)
