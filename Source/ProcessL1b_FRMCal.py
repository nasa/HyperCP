''' L1AQC to L1B for Full-FRM or Class-based '''
import logging
import os
from datetime import datetime as dt
import numpy as np
import pandas as pd
import pytz
from scipy import interpolate
import concurrent.futures

from j6s import SixS

# internal files
from Source.ConfigFile import ConfigFile
from Source.Utilities import Utilities

class ProcessL1b_FRMCal:
    ''' L1AQC to L1B for Full-FRM or Class-based '''

    @staticmethod
    def get_direct_irradiance_ratio(node: object, sensortype: object, called_L2: bool = False) -> object:
        ''' Used for both SeaBird and TriOS L1b

            SunTracker geometries, when available, have already been
            flipped into Ancillary and interpolated.
        '''

        ## Reading ancilliary data and SunTracker, if necessary
        if called_L2:
            # keys change depending on if the process is called at L1B or L2, store correct keys in dictionary
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                irad_key = f'{sensortype}_LIGHT_L1AQC'
            elif ConfigFile.settings['SensorType'].lower() == 'trios' or \
                ConfigFile.settings['SensorType'].lower() == 'dalec' or  \
                    ConfigFile.settings['SensorType'].lower() == 'sorad':
                irad_key = f'{sensortype}_L1AQC'
            else:
                return False

            keys = {
                        'anc' : 'ANCILLARY',
                        'rel' : 'REL_AZ',
                        'sza' : 'SZA',
                        'saa' : 'SOLAR_AZ',
                        'irad' : irad_key
            }
        else:
            # keys as before
            keys = {
                        'anc' : 'ANCILLARY_METADATA',
                        'rel' : 'NONE',
                        'sza' : 'NONE',
                        'saa' : 'NONE',
                        'irad' : f'{sensortype}'
            }

        anc_grp = node.getGroup(keys['anc'])

        if ConfigFile.settings['bL1aqcSunTracker'] == 1:
            rel_az = np.asarray(anc_grp.datasets['REL_AZ'].columns["REL_AZ"])
        else:
            rel_az = np.asarray(anc_grp.datasets['REL_AZ'].columns[keys['rel']])
        sun_zenith = np.asarray(anc_grp.datasets['SZA'].columns[keys['sza']])
        sun_azimuth = np.asarray(anc_grp.datasets['SOLAR_AZ'].columns[keys['saa']])

        aod = np.asarray(anc_grp.datasets['AOD'].columns["AOD"])
        anc_datetime = anc_grp.datasets['LATITUDE'].columns['Datetime']

        irr_grp = node.getGroup(keys['irad'])
        str_wvl = np.asarray(pd.DataFrame(irr_grp.getDataset(sensortype).data).columns)
        wvl = np.asarray([float(x) for x in str_wvl])
        if not called_L2:
            irr_datetime = irr_grp.datasets['DATETIME'].data
        else:
            datetag = np.asarray(pd.DataFrame(irr_grp.getDataset("DATETAG").data))
            timetag = np.asarray(pd.DataFrame(irr_grp.getDataset("TIMETAG2").data))
            dtime = [dt.strptime(str(int(x[0])) + str(int(y[0])).rjust(9, '0'), "%Y%j%H%M%S%f") for x, y in
                        zip(datetag, timetag)]
            irr_datetime = [pytz.utc.localize(dt) for dt in dtime]  # set to utc localisation

        ## SIXS configuration
        n_mesure = len(irr_datetime)
        nband = len(wvl)

        # SIXS called over 3min bin
        ## SIXS configuration
        n_mesure = len(irr_datetime)
        nband = len(wvl)
        
        # SIXS called over 3min bin
        deltat = (irr_datetime[-1]-irr_datetime[0])/len(irr_datetime)
        n_min = int(3*60/deltat.total_seconds())  # nb of mesures over a bin
        if n_min == 0:  
            n_min = n_min + 1
        n_bin = len(irr_datetime)//(n_min)  # nb of bin in a cast
        if len(irr_datetime) % n_min != 0:
            # +1 to account for last points that fall in the last bin (smaller than 3 min)
            n_bin += 1
        
        percent_direct_solar_irradiance = np.zeros((n_bin, nband))
        percent_diffuse_solar_irradiance = np.zeros((n_bin, nband))
        direct_solar_irradiance = np.zeros((n_bin, nband))
        diffuse_solar_irradiance = np.zeros((n_bin, nband))
        environmental_irradiance = np.zeros((n_bin, nband))
        solar_zenith = np.zeros(n_bin)

        # Instanciate the class only once outside the loop
        s = SixS()

        for n in range(n_bin):
            # find ancillary point that match the 1st mesure of the 3min ensemble
            ind_anc = np.argmin(np.abs(np.array(anc_datetime)-irr_datetime[n*n_min]))

            solar_zenith[n] = sun_zenith[ind_anc]

            s.geometry(
                sun_zen=sun_zenith[ind_anc],
                sun_azi=sun_azimuth[ind_anc],
                view_zen=180,
                view_azi=rel_az[ind_anc],
                month=irr_datetime[ind_anc].month,
                day=irr_datetime[ind_anc].day
            )
            s.gas()
            s.aerosol(aot_550=aod[ind_anc])
            s.target_altitude()
            s.sensor_altitude()

            s.to_be_implemented()

            # Create placeholder to contain the values
            # percent_direct_solar_irradiance = [0] * len(wvl)
            # percent_diffuse_solar_irradiance = [0] * len(wvl)
            # direct_solar_irradiance = [0] * len(wvl)
            # diffuse_solar_irradiance = [0] * len(wvl)
            # environmental_irradiance = [0] * len(wvl)

            # Determine the number of workers to use
            num_workers = os.cpu_count()
            logging.info(f"Running on {num_workers} threads")
            iterations_per_worker = len(wvl) // num_workers
            logging.info(f"{iterations_per_worker} iteration per threads")

            # Create the function for 6s that will be run by each worker
            def run_model_and_accumulate(
                    n,
                    start,
                    end,
                    s,
                    wvl,
                    percent_direct_solar_irradiance,
                    percent_diffuse_solar_irradiance,
                    direct_solar_irradiance,
                    diffuse_solar_irradiance,
                    environmental_irradiance
            ):
                for i in range(start, end):
                    wavelength = wvl[i]
                    s.wavelength(wavelength)

                    temp = s.run()

                    # if math.isnan(float(temp["atmospheric_reflectance_at_sensor"])):
                    #     print("atmospheric_path_radiance is NaN ...")

                    # TODO: provide warning (with wavelength) if any of the values are NaN

                    percent_direct_solar_irradiance[n,i] = float(
                        temp["percent_of_direct_solar_irradiance_at_target"]
                    )
                    percent_diffuse_solar_irradiance[n,i] = float(
                        temp["percent_of_diffuse_atmospheric_irradiance_at_target"]
                    )
                    direct_solar_irradiance[n,i] = float(
                        temp["direct_solar_irradiance_at_target_[W m-2 um-1]"]
                    )
                    diffuse_solar_irradiance[n,i] = float(
                        temp["diffuse_atmospheric_irradiance_at_target_[W m-2 um-1]"]
                    )
                    environmental_irradiance[n,i] = float(
                        temp["environement_irradiance_at_target_[W m-2 um-1]"]
                    )

                return

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = []
                for i in range(num_workers):
                    # Calculate the start and end indices for this worker
                    start = i * iterations_per_worker
                    end = (
                        start + iterations_per_worker
                        if i != num_workers - 1
                        else len(wvl)
                    )

                    # Start the worker
                    futures.append(
                        executor.submit(
                            run_model_and_accumulate,
                            n,
                            start,
                            end,
                            s,
                            wvl,
                            percent_direct_solar_irradiance,
                            percent_diffuse_solar_irradiance,
                            direct_solar_irradiance,
                            diffuse_solar_irradiance,
                            environmental_irradiance
                        )
                    )

            # Wait for all workers to finish
            concurrent.futures.wait(futures)

            if np.isnan(percent_direct_solar_irradiance).any():
                logging.debug("direct contains NaN values at: %s", wvl[np.isnan(percent_direct_solar_irradiance)[n]])

            if np.isnan(percent_diffuse_solar_irradiance).any():
                logging.debug("diffuse contains NaN values at: %s", wvl[np.isnan(percent_diffuse_solar_irradiance)[n]])

            if np.isnan(direct_solar_irradiance).any():
                logging.debug("irr_direct contains NaN values at: %s", wvl[np.isnan(direct_solar_irradiance)[n]])

            if np.isnan(diffuse_solar_irradiance).any():
                logging.debug("irr_diffuse contains NaN values at: %s", wvl[np.isnan(diffuse_solar_irradiance)[n]])

            if np.isnan(environmental_irradiance).any():
                logging.debug("irr_env contains NaN values at: %s", wvl[np.isnan(environmental_irradiance)[n]])

            if np.isnan(solar_zenith).any():
                logging.debug("solar_zenith contains NaN values at: %s", wvl[np.isnan(solar_zenith)[n]])

            # Check for potential NaN values and interpolate them with neighbour
            # direct
            ind0 = np.where(np.isnan(percent_direct_solar_irradiance[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        percent_direct_solar_irradiance[n,i0] = percent_direct_solar_irradiance[n,i0-1]
                    else:
                        percent_direct_solar_irradiance[n,i0] = (percent_direct_solar_irradiance[n,i0-1]+percent_direct_solar_irradiance[n,i0+1])/2
            # diffuse
            ind0 = np.where(np.isnan(percent_diffuse_solar_irradiance[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        percent_diffuse_solar_irradiance[n,i0] = percent_diffuse_solar_irradiance[n,i0-1]
                    else:
                        percent_diffuse_solar_irradiance[n,i0] = (percent_diffuse_solar_irradiance[n,i0-1]+percent_diffuse_solar_irradiance[n,i0+1])/2

            # irr_direct
            ind0 = np.where(np.isnan(direct_solar_irradiance[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        direct_solar_irradiance[n,i0] = direct_solar_irradiance[n,i0-1]
                    else:
                        direct_solar_irradiance[n,i0] = (direct_solar_irradiance[n,i0-1]+direct_solar_irradiance[n,i0+1])/2

            # irr_diffuse
            ind0 = np.where(np.isnan(diffuse_solar_irradiance[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        diffuse_solar_irradiance[n,i0] = diffuse_solar_irradiance[n,i0-1]
                    else:
                        diffuse_solar_irradiance[n,i0] = (diffuse_solar_irradiance[n,i0-1]+diffuse_solar_irradiance[n,i0+1])/2

            # irr_env
            ind0 = np.where(np.isnan(environmental_irradiance[n, :]))[0]
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        environmental_irradiance[n,i0] = environmental_irradiance[n,i0-1]
                    else:
                        environmental_irradiance[n,i0] = (environmental_irradiance[n,i0-1]+environmental_irradiance[n,i0+1])/2

            # Check for potential zero values and interpolate them with neighbour
            _, ind0 = np.where([percent_direct_solar_irradiance[n,:]==0])
            if len(ind0)>0:
                for i0 in ind0:
                    if i0==ind0[-1]:
                        # End of array. Take left neighbor.
                        percent_direct_solar_irradiance[n,i0] = percent_direct_solar_irradiance[n,i0-1]
                    else:
                        percent_direct_solar_irradiance[n,i0] = (percent_direct_solar_irradiance[n,i0-1]+percent_direct_solar_irradiance[n,i0+1])/2

        # if only 1 bin, repeat value for each timestamp over cast duration (<3min)
        res_sixS = {}
        if n_bin == 1:
            logging.warning("n_bin == 1, cast is probably too short")
            res_sixS['solar_zenith'] = np.repeat(solar_zenith, n_mesure)
            res_sixS['direct_ratio'] = np.repeat(percent_direct_solar_irradiance, n_mesure, axis=0)
            res_sixS['diffuse_ratio'] = np.repeat(percent_diffuse_solar_irradiance, n_mesure, axis=0)
            res_sixS['direct_irr'] = np.repeat(direct_solar_irradiance, n_mesure, axis=0)
            res_sixS['diffuse_irr'] = np.repeat(diffuse_solar_irradiance, n_mesure, axis=0)
            res_sixS['env_irr'] = np.repeat(environmental_irradiance, n_mesure, axis=0)
        # if more than 1 bin, interpolate fo each timestamp
        else:
            x_bin  = [n*n_min for n in range(n_bin)]
            x_full = np.linspace(0, n_mesure, n_mesure)
            f =  interpolate.interp1d(x_bin, solar_zenith, fill_value='extrapolate')
            res_sixS['solar_zenith'] = f(x_full)
            f =  interpolate.interp1d(x_bin, percent_direct_solar_irradiance, fill_value='extrapolate', axis=0)
            res_sixS['direct_ratio'] = f(x_full)
            f =  interpolate.interp1d(x_bin, percent_diffuse_solar_irradiance, fill_value='extrapolate', axis=0)
            res_sixS['diffuse_ratio'] = f(x_full)
            f =  interpolate.interp1d(x_bin, direct_solar_irradiance, fill_value='extrapolate', axis=0)
            res_sixS['direct_irr'] = f(x_full)
            f =  interpolate.interp1d(x_bin, diffuse_solar_irradiance, fill_value='extrapolate', axis=0)
            res_sixS['diffuse_irr'] = f(x_full)
            f =  interpolate.interp1d(x_bin, environmental_irradiance, fill_value='extrapolate', axis=0)
            res_sixS['env_irr'] = f(x_full)

        return res_sixS

    @staticmethod
    def cosine_error_correction(node, sensorstring):
        ''' Used for both SeaBird and TriOS L1b'''

        ## Angular cosine correction (for Irradiance)
        unc_grp = node.getGroup('RAW_UNCERTAINTIES')
        radcal_wvl = np.asarray(pd.DataFrame(unc_grp.getDataset(sensorstring+"_RADCAL_CAL").data)['1'][1:].tolist())
        coserror = np.asarray(pd.DataFrame(unc_grp.getDataset(sensorstring+"_ANGDATA_COSERROR").data))[1:,2:]
        coserror_90 = np.asarray(pd.DataFrame(unc_grp.getDataset(sensorstring+"_ANGDATA_COSERROR_AZ90").data))[1:,2:]
        zenith_ang = unc_grp.getDataset(sensorstring+"_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
        # zenith_ang_90 = unc_grp.getDataset(sensortype+"_ANGDATA_COSERROR_AZ90").attributes["COLUMN_NAMES"].split('\t')[2:]
        i1 = np.argmin(np.abs(radcal_wvl-300))
        i2 = np.argmin(np.abs(radcal_wvl-1000))
        zenith_ang = np.asarray([float(x) for x in zenith_ang])

        # comparing cos_error for 2 azimuth
        # AZI_delta_cos = coserror-coserror_90

        # if delta < 2% : averaging the 2 azimuth plan
        AZI_avg_coserror = (coserror+coserror_90)/2.

        # comparing cos_error for symetric zenith
        # ZEN_delta_cos = AZI_avg_coserror - AZI_avg_coserror[:,::-1]

        # if delta < 2% : averaging symetric zenith
        ZEN_avg_coserror = (AZI_avg_coserror+AZI_avg_coserror[:,::-1])/2.

        # set coserror to 1 outside range [450,700]
        ZEN_avg_coserror[0:i1,:] = 0
        ZEN_avg_coserror[i2:,:] = 0

        # Compute full hemisperical coserror
        zen0 = np.argmin(np.abs(zenith_ang))
        zen90 = np.argmin(np.abs(zenith_ang-90))
        deltaZen = (zenith_ang[1::]-zenith_ang[:-1])
        full_hemi_coserror = np.zeros(255)

        for i in range(255):
            full_hemi_coserror[i] = np.sum(ZEN_avg_coserror[i,zen0:zen90]*np.sin(2*np.pi*zenith_ang[zen0:zen90]/180)*deltaZen[zen0:zen90]*np.pi/180 )

        return ZEN_avg_coserror, full_hemi_coserror, zenith_ang

    @staticmethod
    def Zong_SL_correction_matrix(LSF, n_IB: int = 3):
        LSF[LSF<=0] = 0
        SDF = np.copy(LSF)
        for i in range(len(LSF)):
        # for j in range(len(LSF)):
            # define IB indexes
            j1 = i-n_IB
            j2 = i+n_IB
            if j1 <= 0:
                j1 = 0
            IB = LSF[i,j1:j2+1]
            IBsum = np.sum(IB)
            if np.sum(IB) == 0:
                IBsum = 1.0
            # Zong eq. 1
            SDF[i,:] = SDF[i,:]/float(IBsum)
            SDF[i,j1:j2+1] = 0

        A = np.identity(len(LSF)) + SDF   # Matrix A from eq. 8
        C = np.linalg.inv(A)              # Matrix C from eq. 9

        return C

    @staticmethod
    def Slaper_SL_correction(input_data, SL_matrix, n_iter=5):
        nband = len(input_data)
        m_norm = np.zeros(nband)
        mC = np.zeros((n_iter+1, nband))
        mX = np.zeros((n_iter+1, nband))
        mZ = SL_matrix
        mX[0, :] = input_data

        for i in range(nband):
            jstart = np.max([0,i-10])
            jstop  = np.min([nband,i+10])
            m_norm[i] = np.sum(mZ[i,jstart:jstop])  # eq 4

        for i in range(nband):
            if m_norm[i] == 0:
                mZ[i,:] = np.zeros(nband)
            else:
                mZ[i,:] = mZ[i,:]/m_norm[i]   # eq 5

        for k in range(1,n_iter+1):
            for i in range(nband):
                mC[k-1,i] = mC[k-1,i] + np.sum(mX[k-1,:]*mZ[i,:])  # eq 6
                if mC[k-1,i] == 0:
                    mX[k,i] = 0
                else:
                    mX[k,i] = (mX[k-1,i] * mX[0,i]) / mC[k-1,i]   # eq 7

        return mX[n_iter-1,:]

    @staticmethod
    def processL1b_SeaBird(node, calibrationMap):
        # calibration of HyperOCR following the FRM processing of FRM4SOC2
        esUnits = None
        liUnits = None
        ltUnits = None
        pyrUnits = None

        now = dt.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr
        msg = f"ProcessL1b_FactoryCal.processL1b: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        msg = "Applying factory calibrations."
        print(msg)
        Utilities.writeLogFile(msg)

        for gp in node.groups:
            if 'L1AQC' not in gp.id:
                msg = f'  Group: {gp.id}'
                print(msg)
                Utilities.writeLogFile(msg)
                if "CalFileName" in gp.attributes:
                    if gp.attributes["CalFileName"] != 'ANCILLARY':  # GPS constructed from Ancillary data will cause bug here
                        cf = calibrationMap[gp.attributes["CalFileName"]]
                        #print(gp.id, gp.attributes)
                        msg = f'    File: {cf.id}'
                        print(msg)
                        Utilities.writeLogFile(msg)

                        if esUnits == None:
                            esUnits = cf.getUnits("ES")
                        if liUnits == None:
                            liUnits = cf.getUnits("LI")
                        if ltUnits == None:
                            ltUnits = cf.getUnits("LT")
                        if pyrUnits == None:
                            pyrUnits = cf.getUnits("T") #Pyrometer

        node.attributes["LI_UNITS"] = liUnits
        node.attributes["LT_UNITS"] = ltUnits
        node.attributes["ES_UNITS"] = esUnits
        node.attributes["L1AQC_UNITS"] = 'count'
        node.attributes["SATPYR_UNITS"] = pyrUnits

        # setup node attrs

        unc_grp = node.getGroup('RAW_UNCERTAINTIES')

        for sensortype in ['ES', 'LI', 'LT']:
            print('FRM Processing:', sensortype)
            # Read data
            grp = node.getGroup(sensortype)
            raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())
            int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())

            # Read FRM characterisation
            radcal_wvl = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['1'][1:].tolist())
            radcal_cal = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['2']
            dark = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['4'][1:].tolist())
            S1 = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['6']
            S2 = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['8']
            Ct = pd.DataFrame(unc_grp.getDataset(sensortype+"_TEMPDATA_CAL").data)[sensortype+"_TEMPERATURE_COEFFICIENTS"][1:].tolist()
            mZ = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_STRAYDATA_LSF").data))
            mZ = mZ[1:,1:] # remove 1st line and column, we work on 255 pixel not 256.
            LAMP = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_LAMP").data)['2'])

            # create Zong SDF straylight correction matrix
            C_zong = ProcessL1b_FRMCal.Zong_SL_correction_matrix(mZ)

            # Defined constants
            nband = len(radcal_wvl)
            nmes  = len(raw_data)
            # n_iter = 5

            # Non-linearity alpha computation
            cal_int = radcal_cal.pop(0)
            t1 = S1.pop(0)
            t2 = S2.pop(0)
            k = t1/(t2-t1)
            S12 = (1+k)*S1 - k*S2

            # S12_sl_corr = ProcessL1b_FRMCal.Slaper_SL_correction(S12, mZ, n_iter)  # Slapper
            S12_sl_corr = np.matmul(C_zong, S12) # Zong SL corr
            alpha = ((S1-S12)/(S12**2)).tolist()
            LAMP = np.pad(LAMP, (0, nband-len(LAMP)), mode='constant') # PAD with zero if not 255 long

            ## sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
            ind_zero = radcal_cal<=0
            ind_nan  = np.isnan(radcal_cal)
            ind_nocal = ind_nan | ind_zero

            # keep only defined wavelength
            wvl = radcal_wvl[ind_nocal==False]
            str_wvl = np.asarray([str(x) for x in wvl])
            dark = dark[ind_nocal==False]
            alpha = np.asarray(alpha)[ind_nocal==False]
            Ct = np.asarray(Ct)[ind_nocal==False]
            mZ = mZ[:, ind_nocal==False]
            mZ = mZ[ind_nocal==False, :]
            C_zong = C_zong[:, ind_nocal==False]
            C_zong = C_zong[ind_nocal==False, :]
            ind_raw_data = (radcal_cal[radcal_wvl>0])>0

            # Updated calibration gain
            if sensortype == "ES":
                updated_radcal_gain = (S12_sl_corr/LAMP) * (10*cal_int/t1)
                # Compute avg cosine error
                avg_coserror, full_hemi_coserror, zenith_ang = ProcessL1b_FRMCal.cosine_error_correction(node, sensortype)
                # Irradiance direct and diffuse ratio
                res_sixS = ProcessL1b_FRMCal.get_direct_irradiance_ratio(node, sensortype)
            else:
                PANEL = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_PANEL").data)['2'])
                PANEL = np.pad(PANEL, (0, nband-len(PANEL)), mode='constant')
                updated_radcal_gain = (np.pi*S12_sl_corr)/(LAMP*PANEL) * (10*cal_int/t1)

            # set 1 instead of 0 to perform calibration (otherwise division per 0)
            updated_radcal_gain[ind_nocal==True] = 1
            updated_radcal_gain = updated_radcal_gain[ind_nocal==False]

            FRM_mesure = np.zeros((nmes, len(updated_radcal_gain)))
            for n in range(nmes):
                # raw data
                data = raw_data[n][ind_raw_data]
                # Non-linearity
                data = data*(1-alpha*data)
                # Straylight
                # data = ProcessL1b_FRMCal.Slaper_SL_correction(data, mZ, n_iter)
                data = np.matmul(C_zong, data)
                # Calibration
                data = data * (cal_int/int_time[n]) / updated_radcal_gain
                # thermal
                data = data * Ct
                # Cosine correction
                if sensortype == "ES":
                    # retrive sixS variables for given wvl
                    solar_zenith = res_sixS['solar_zenith'][n]
                    direct_ratio = res_sixS['direct_ratio'][n,ind_raw_data]
                    diffuse_ratio = res_sixS['diffuse_ratio'][n,ind_raw_data]
                    ind_closest_zen = np.argmin(np.abs(zenith_ang-solar_zenith))
                    cos_corr = (1-avg_coserror[:,ind_closest_zen]/100)[ind_nocal==False]
                    Fhcorr = (1-full_hemi_coserror/100)[ind_nocal==False]
                    data = (direct_ratio*data*cos_corr) + ((1-direct_ratio)*data*Fhcorr)
                    FRM_mesure[n,:] = data
                else:
                    FRM_mesure[n,:] = data

            # Remove wvl without calibration from the dataset
            filtered_mesure = FRM_mesure
            filtered_wvl = str_wvl

            # Replace raw data with calibrated data in hdf root
            ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
            rec_arr = np.rec.fromarrays(np.array(filtered_mesure).transpose(), dtype=ds_dt)
            grp.getDataset(sensortype).data = rec_arr

            # Store SIXS results in new group
            if sensortype == "ES":
                solar_zenith = res_sixS['solar_zenith']
                direct_ratio = res_sixS['direct_ratio'][:,ind_raw_data]
                diffuse_ratio = res_sixS['diffuse_ratio'][:,ind_raw_data]
                # SIXS model irradiance is in W/m^2/um, scale by 10 to match HCP units
                model_irr = (res_sixS['direct_irr']+res_sixS['diffuse_irr']+res_sixS['env_irr'])[:,ind_raw_data]/10

                sixS_grp = node.addGroup("SIXS_MODEL")
                for dsname in ["DATETAG", "TIMETAG2", "DATETIME"]:
                    # copy datetime dataset for interp process
                    ds = sixS_grp.addDataset(dsname)
                    ds.data = grp.getDataset(dsname).data

                ds = sixS_grp.addDataset("sixS_irradiance")
                ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
                rec_arr = np.rec.fromarrays(np.array(model_irr).transpose(), dtype=ds_dt)
                ds.data = rec_arr

                ds = sixS_grp.addDataset("direct_ratio")
                ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
                rec_arr = np.rec.fromarrays(np.array(direct_ratio).transpose(), dtype=ds_dt)
                ds.data = rec_arr

                ds = sixS_grp.addDataset("diffuse_ratio")
                ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
                rec_arr = np.rec.fromarrays(np.array(diffuse_ratio).transpose(), dtype=ds_dt)
                ds.data = rec_arr

                ds = sixS_grp.addDataset("solar_zenith")
                ds.columns["solar_zenith"] = solar_zenith
                ds.columnsToDataset()

        return True
    