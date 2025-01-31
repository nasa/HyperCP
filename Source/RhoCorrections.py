import os
import time

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from Source.ZhangRho import get_sky_sun_rho, PATH_TO_DATA
from Source.ConfigFile import ConfigFile
from Source.Utilities import Utilities
from Source.HDFRoot import HDFRoot
from Source.Water_IOPs import water_iops


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
        inFilePath = os.path.join(PATH_TO_DATA, 'rhoTable_AO1999.hdf')
        try:
            lut = HDFRoot.readHDF5(inFilePath)
        except Exception:
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
                                              uncertainties=[2, 0.5, 3])/rhoScalar

        # TODO: find the source of the windspeed uncertainty to reference this. EMWCF should have this info
        # TODO: Model error estimation, requires ancillary data to be switched on. This could create a conflict.
        if not any([AOD is None, wTemp is None, sal is None, waveBands is None]) and \
                ((ConfigFile.settings["bL1bCal"] > 1) or (ConfigFile.settings['SensorType'].lower() == "seabird")):
            # Fix: Truncate input parameters to stay within Zhang ranges:
            # AOD
            AOD = np.min([AOD,0.2])
            # SZA
            if SZAMean >= 70:
                raise ValueError('SZAMean is too high (%s), Zhang correction cannot be performed above SZA=70.')
            # wavelengths in range [350-1000] nm
            newWaveBands = [w for w in waveBands if w >= 350 and w <= 1000]
            # Wavebands clips the ends off of the spectra reducing the amount of values from 200 to 189 for
            # TriOS_NOTRACKER. We need to add these specra back into rhoDelta to prevent broadcasting errors later
            from datetime import datetime as dt
            start = dt.now()
            zhang, _ = RhoCorrections.ZhangCorr(windSpeedMean, AOD, cloud, SZAMean, wTemp, sal, relAzMean, newWaveBands)
            end = dt.now() - start
            print(end)

            start_lut = dt.now()
            zhang = RhoCorrections.read_Z17_LUT(windSpeedMean, AOD, SZAMean, wTemp, sal, relAzMean, newWaveBands, zhang, indx=f"ws={windSpeedMean}")
            end_lut = dt.now() - start_lut
            print(end_lut)

            # zhang = RhoCorrections.read_Z17_LUT(windSpeedMean, AOD, SZAMean, wTemp, sal, relAzMean, newWaveBands, zhang, indx=f"ws={windSpeedMean}")
            # this is the method to read zhang from the LUT. It is commented out pending the sensitivity study and
            # correction to the interpolation errors that have been noted.
            # zhang = RhoCorrections.read_Z17_LUT(windSpeedMean, AOD, SZAMean, wTemp, sal, relAzMean, newWaveBands, zhang, indx=1)
            # zhang = RhoCorrections.read_Z17_LUT(windSpeedMean, AOD, SZAMean, wTemp, sal, relAzMean, newWaveBands, zhang, indx=1)

            # wind speed was set to 1 for the aot test
            # 1, 0.1, None, 40, wTemp, sal, 105, newWaveBands

            # windspeed = np.array([1])  # , 2, 3, 4])  # 7
            # AOT = np.array([0, 0.05, 0.1, 0.2, 0.5])  # 5
            # SZA = np.arange(10, 55, 5)  # 12  # expanded database would go to 65
            # RELAZ = np.arange(80, 145, 5)  # 13
            # SAL = np.arange(0, 45, 5)  # 10
            # SST = np.arange(0, 35, 5)  # 8

            # for wtemp in [10, 12, 15, 17.5, 20.2, 25.6, 28, 32.1, 35]:
            #     z, _ = RhoCorrections.ZhangCorr(1, 0.1, cloud, 40, wtemp, 35, 105, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(1, 0.1, 40, wtemp, 35, 105, newWaveBands, z, indx=f"water_temp={wtemp}")
            # wind speed was set to 1 for the aot test
            # 1, 0.1, None, 40, wTemp, sal, 105, newWaveBands

            # windspeed = np.array([1])  # , 2, 3, 4])  # 7
            # AOT = np.array([0, 0.05, 0.1, 0.2, 0.5])  # 5
            # SZA = np.arange(10, 55, 5)  # 12  # expanded database would go to 65
            # RELAZ = np.arange(80, 145, 5)  # 13
            # SAL = np.arange(0, 45, 5)  # 10
            # SST = np.arange(0, 35, 5)  # 8

            # for wtemp in [10, 12, 15, 17.5, 20.2, 25.6, 28, 32.1, 35]:
            #     z, _ = RhoCorrections.ZhangCorr(1, 0.1, cloud, 40, wtemp, 35, 105, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(1, 0.1, 40, wtemp, 35, 105, newWaveBands, z, indx=f"water_temp={wtemp}")

            # for salt in [0, 5, 12.5, 17, 26, 30, 32.5, 38.7, 40, 42.25, 45]:
            #     z, _ = RhoCorrections.ZhangCorr(1, 0.1, cloud, 40, 26, salt, 105, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(1, 0.1, 40, 26, salt, 105, newWaveBands, z, indx=f"salinity={salt}")
            # for salt in [0, 5, 12.5, 17, 26, 30, 32.5, 38.7, 40, 42.25, 45]:
            #     z, _ = RhoCorrections.ZhangCorr(1, 0.1, cloud, 40, 26, salt, 105, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(1, 0.1, 40, 26, salt, 105, newWaveBands, z, indx=f"salinity={salt}")

            # for wind in [1, 2, 3, 4, 5, 6, 7, 8 ,9, 10]:
            #     z, _ = RhoCorrections.ZhangCorr(wind, 0.1, cloud, 40, 26, 35, 105, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(wind, 0.1, 40, 26, 35, 105, newWaveBands, z, indx=f"wind={wind}")
            # for wind in [1, 2, 3, 4, 5, 6, 7, 8 ,9, 10]:
            #     z, _ = RhoCorrections.ZhangCorr(wind, 0.1, cloud, 40, 26, 35, 105, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(wind, 0.1, 40, 26, 35, 105, newWaveBands, z, indx=f"wind={wind}")

            # for a in [0, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]:
            #     z, _ = RhoCorrections.ZhangCorr(1, a, cloud, 40, 26, 35, 105, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(1, a, 40, 26, 35, 105, newWaveBands, z, indx=f"aot={a}")
            # for a in [0, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]:
            #     z, _ = RhoCorrections.ZhangCorr(1, a, cloud, 40, 26, 35, 105, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(1, a, 40, 26, 35, 105, newWaveBands, z, indx=f"aot={a}")

            # for rel in [90, 107, 112, 117, 121, 126, 133, 137, 140]:
            #     z, _ = RhoCorrections.ZhangCorr(1, 0.1, cloud, 40, 26, 35, rel, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(1, 0.1, 40, 26, 35, rel, newWaveBands, z, indx=f"relaz={rel}")

            # for s in [41, 45, 47, 50, 52, 55]:
            #     z, _ = RhoCorrections.ZhangCorr(1, 0.1, cloud, s, 26, 35, 105, newWaveBands)
            #     RhoCorrections.read_Z17_LUT(1, 0.1, s, 26, 35, 105, newWaveBands, z, indx=f"sza={s}")

            # |M99 - Z17| is an estimation of model error, added to MC M99 uncertainty in quadrature to give combined
            # uncertainty
            pct_diff = (np.abs(rhoScalar - zhang) / rhoScalar)  # relative units
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
            ## NOTES ##
            # this is temporary. It is possible for users to not select any ancillary data in the config, meaning Zhang
            # Rho will fail. It is far too easy for a user to do this, so I added the following line to make sure the
            # processor doesn't break.
            # Not sure I follow. Ancillary data should be populated regardless of whether an ancillary file is
            # added (i.e., using the model data) - DAA
            # yes but if none of the ancillary datasets i.e. ECMWF are selected then surely info like AOD could be
            # missing? -AJR.

            # 0.003 was chosen because it is the only number with any scientific justification
            # (estimated from Ruddick 2006).
            rhoDelta = np.sqrt(Delta**2 + (0.003 / rhoScalar)**2) * rhoScalar

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
    # def ZhangCorr(windSpeedMean, AOD, cloud, sza, wTemp, sal, relAz, waveBands):
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

        # # define uncertainties and create variable list for punpy. Inputs cannot be ordered dictionaries
        varlist = [windSpeedMean, AOD, 0.0, sza, wTemp, sal, relAz, np.array(waveBands)]
        ulist = [2.0, 0.01, 0.0, 0.5, 2, 0.5, 3, None]
        # todo: find the source of the windspeed uncertainty to reference this. EMWCF should have this info

        tic = time.process_time()
        rhoVector = get_sky_sun_rho(env, sensor, round4cache=True)['rho']
        msg = f'Zhang17 Elapsed Time: {time.process_time() - tic:.1f} s'
        print(msg)
        Utilities.writeLogFile(msg)

        # Presumably obsolete (Ashley)? -DAA
        # It will be once the LUT  is finished, right now the Z17 without a propagate object is important for the
        # Monte Carlo runs
        if Propagate is None:
            rhoDelta = 0.003  # Unknown; estimated from Ruddick 2006
        else:
            tic = time.process_time()
            rhoDelta = Propagate.Zhang_Rho_Uncertainty(mean_vals=varlist,
                                                       uncertainties=ulist,
                                                       )
            msg = f'Zhang_Rho_Uncertainty Elapsed Time: {time.process_time() - tic:.1f} s'
            print(msg)
            Utilities.writeLogFile(msg)

        return rhoVector, rhoDelta

    @staticmethod
    def read_Z17_LUT(ws, aod, sza, wt, sal, rel_az, nwb, zhang=None, indx="") -> np.array:
        """
        windSpeedMean, AOD, SZAMean, wTemp, sal, relAzMean, newWaveBands, zhang

        """
        db_path = os.path.join(PATH_TO_DATA, 'z17_RHO_LUT_no_nan_pchip.nc')
        # db_path = os.path.join(PATH_TO_DATA, 'Zhang_rho_LUT.nc')

        db_path = os.path.join(PATH_TO_DATA, 'z17_RHO_LUT_no_nan_pchip.nc')
        # db_path = os.path.join(PATH_TO_DATA, 'Zhang_rho_LUT.nc')

        z17_lut = xr.open_dataset(db_path, engine='netcdf4')

        import scipy.interpolate as spin

        # used to test: z17_lut.Glint.values[np.isnan(z17_lut.Glint.values)]

        # interp missing vals out of LUT.
        # Glint = z17_lut.Glint.interpolate_na(dim="wind", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="aot", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="sza", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="relAz", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="sal", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="SST", method='cubic', fill_value='extrapolate')
        # z17_lut.Glint.values = Glint.values
        # z17_lut.to_netcdf(os.path.join("z17_lut_no_nan_cubic.nc"))

        # work out the speeds!
        import time

        t0 = time.time()
        methods = ['cubic', 'linear', 'slinear', 'pchip']
        # used to test: z17_lut.Glint.values[np.isnan(z17_lut.Glint.values)]

        # interp missing vals out of LUT.
        # Glint = z17_lut.Glint.interpolate_na(dim="wind", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="aot", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="sza", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="relAz", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="sal", method='cubic', fill_value='extrapolate')
        # Glint = Glint.interpolate_na(dim="SST", method='cubic', fill_value='extrapolate')
        # z17_lut.Glint.values = Glint.values
        # z17_lut.to_netcdf(os.path.join("z17_lut_no_nan_cubic.nc"))

        # work out the speeds!
        import time

        t0 = time.time()
        methods = ['cubic', 'linear', 'slinear', 'pchip']
        for i, method in enumerate(methods):
            zhang_L = spin.interpn(
                points=(
                    z17_lut.wind.values,
                    z17_lut.aot.values,
                    z17_lut.aot.values,
                    z17_lut.sza.values,
                    z17_lut.relAz.values,
                    z17_lut.sal.values,
                    z17_lut.SST.values,
                    z17_lut.wavelength.values
                ),
                values=z17_lut.Glint.values,
                xi=(
                    ws,
                    aod,
                    aod,
                    sza,
                    rel_az,
                    sal,
                    wt,
                    nwb
                ),
                method=method,
            )

            print(time.time()-t0)

            print(time.time()-t0)

            plt.figure("LUT-Interp")
            plt.plot(nwb, zhang_L, label=f'scipy interpn {method}', linestyle='--')  # color='r'
            if i == 0 and (zhang is not None):
            plt.plot(nwb, zhang_L, label=f'scipy interpn {method}', linestyle='--')  # color='r'
            if i == 0 and (zhang is not None):
                plt.plot(nwb, zhang, label='Calculated', linestyle='--', color='k')

            plt.legend()
            plt.xlabel("Wavelength (nm)")
            plt.ylabel(r"$\rho$")
            plt.ylabel(r"$\rho$")
            plt.grid()
            plt.title(f"Interpolation methods compared with Calculated Zhang Rho: {indx}")
            plt.title(f"Interpolation methods compared with Calculated Zhang Rho: {indx}")
            plt.show()

        plt.savefig(f"Z17_LUT_interp_compare_{indx}.png")

        plt.close("LUT-Interp")  # close the figure so it cannot interact with others (good encapsulation)

        # using numpy interp in the end for wavelength as per Tom's suggestion. Not important since wavebands
        # match LUT in test case (I used Pysas wavebands to generate LUT).
        return zhang_L
