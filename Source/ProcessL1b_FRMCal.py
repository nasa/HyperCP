
import numpy as np
import pandas as pd
import datetime as dt
import Py6S

class ProcessL1b_FRMCal:

    @staticmethod
    def get_direct_irradiance_ratio(node, sensortype):
        ''' Used for both SeaBird and TriOS L1b

        Need to flip relAz, sza, solarAz into Ancillary before the interpolation of Ancillary for SolarTracker data.

        '''

        ## Reading ancilliary data
        anc_grp = node.getGroup('ANCILLARY_METADATA')
        # lat = np.asarray(pd.DataFrame(anc_grp.getDataset("LATITUDE").data))
        # lon = np.asarray(pd.DataFrame(anc_grp.getDataset("LONGITUDE").data))
        rel_az = np.asarray(pd.DataFrame(anc_grp.getDataset("REL_AZ").data))
        sun_zenith = np.asarray(pd.DataFrame(anc_grp.getDataset("SZA").data))
        sun_azimuth = np.asarray(pd.DataFrame(anc_grp.getDataset("SOLAR_AZ").data))
        anc_datetime = anc_grp.datasets['LATITUDE'].columns['Datetime']
        # anc_datetag = np.asarray(pd.DataFrame(anc_grp.getDataset("DATETAG").data))
        # anc_timetag = np.asarray(pd.DataFrame(anc_grp.getDataset("TIMETAG2").data))
        # anc_datetime = [dt.datetime.strptime(str(int(x[0]))+str(int(y[0])).rjust(9,'0'), "%Y%j%H%M%S%f") for x,y in zip(anc_datetag,anc_timetag)]

        ## Reading irradiance data
        # if trios == 0:
        irr_grp = node.getGroup(sensortype)
        # else:
        #     irr_grp = node.getGroup(trios+'.dat')
        str_wvl = np.asarray(pd.DataFrame(irr_grp.getDataset(sensortype).data).columns)
        wvl = np.asarray([float(x) for x in str_wvl])
        datetime = irr_grp.datasets['DATETIME'].data
        # datetag = np.asarray(pd.DataFrame(irr_grp.getDataset("DATETAG").data))
        # timetag = np.asarray(pd.DataFrame(irr_grp.getDataset("TIMETAG2").data))
        # datetime = [dt.datetime.strptime(str(int(x[0]))+str(int(y[0])).rjust(9,'0'), "%Y%j%H%M%S%f") for x,y in zip(datetag,timetag)]
        # datetime_str = [x.strftime("%Y-%m-%d %H:%M:%S") for x in datetime]

        ## Py6S configuration
        n_mesure = len(datetime)
        nband = len(wvl)
        res_py6s = {}

        # Py6S called only once per cast, for starttime
        ind_anc = np.argmin(np.abs(np.array(anc_datetime)-datetime[0]))
        s = Py6S.SixS()
        s.atmos_profile = Py6S.AtmosProfile.PredefinedType(Py6S.AtmosProfile.MidlatitudeSummer)
        s.aero_profile  = Py6S.AeroProfile.PredefinedType(Py6S.AeroProfile.Maritime)
        s.month = datetime[0].month
        s.day = datetime[0].day
        s.geometry.solar_z = sun_zenith[ind_anc]
        s.geometry.solar_a = sun_azimuth[ind_anc]
        s.geometry.view_a = rel_az[ind_anc]
        s.geometry.view_z = 180
        s.altitudes = Py6S.Altitudes()
        s.altitudes.set_target_sea_level()
        s.altitudes.set_sensor_sea_level()
        '''
        Presumably this is where the model data are needed
        '''
        s.aot550 = 0.153

        '''
        This throws the error: TypeError: only size-1 arrays can be converted to Python scalars
        '''
        wavelengths, res = Py6S.SixSHelpers.Wavelengths.run_wavelengths(s, 1e-3*wvl)

        # extract value from Py6s
        total_gaseous_transmittance = np.array([res[x].values['total_gaseous_transmittance'] for x in range(nband)])
        direct = np.array([res[x].values['percent_direct_solar_irradiance'] for x in range(nband)])
        diffuse = np.array([res[x].values['percent_diffuse_solar_irradiance'] for x in range(nband)])
        env = np.array([res[x].values['percent_environmental_irradiance'] for x in range(nband)])
        irr_direct = np.array([res[x].values['direct_solar_irradiance'] for x in range(nband)])
        irr_diffuse = np.array([res[x].values['diffuse_solar_irradiance'] for x in range(nband)])
        irr_env = np.array([res[x].values['environmental_irradiance'] for x in range(nband)])

        # Check for potential zero values and interpolate them with neighbour
        val, ind0 = np.where([direct==0])
        if len(ind0)>0:
            for i0 in ind0:
                direct[i0] = (direct[i0-1]+direct[i0+1])/2

        res_py6s = {'direct_ratio': direct, 'diffuse_ratio': diffuse, 'env_ratio': env,
                    'direct_irr': irr_direct, 'diffuse_irr': irr_diffuse, 'env_irr': irr_env,
                    'solar_zenith':sun_zenith[ind_anc], 'total_gaseous_transmittance':total_gaseous_transmittance}

        ### if Py6S values need to be computed for each replicates
        # for n in range(n_mesure):
        #     ind_anc = np.argmin(np.abs(np.array(anc_datetime)-datetime[n]))
        #     s = Py6S.SixS()
        #     s.atmos_profile = Py6S.AtmosProfile.PredefinedType(Py6S.AtmosProfile.MidlatitudeSummer)
        #     s.aero_profile  = Py6S.AeroProfile.PredefinedType(Py6S.AeroProfile.Maritime)
        #     s.month = datetime[n].month
        #     s.day = datetime[n].day
        #     s.geometry.solar_z = sun_zenith[ind_anc]
        #     s.geometry.solar_a = sun_azimuth[ind_anc]
        #     s.geometry.view_a = rel_az[ind_anc]
        #     s.geometry.view_z = 180
        #     s.altitudes = Py6S.Altitudes()
        #     s.altitudes.set_target_sea_level()
        #     s.altitudes.set_sensor_sea_level()
        #     s.aot550 = 0.153
        #     # s.run()
        #     # print(s.outputs.fulltext)
        #     # print(s.outputs.values)
        #     # exit()
        #     wavelengths, res = Py6S.SixSHelpers.Wavelengths.run_wavelengths(s, 1e-3*wvl)

        #     # extract value from Py6s
        #     total_gaseous_transmittance = np.array([res[x].values['total_gaseous_transmittance'] for x in range(nband)])
        #     direct = np.array([res[x].values['percent_direct_solar_irradiance'] for x in range(nband)])
        #     diffuse = np.array([res[x].values['percent_diffuse_solar_irradiance'] for x in range(nband)])
        #     env = np.array([res[x].values['percent_environmental_irradiance'] for x in range(nband)])
        #     irr_direct = np.array([res[x].values['direct_solar_irradiance'] for x in range(nband)])
        #     irr_diffuse = np.array([res[x].values['diffuse_solar_irradiance'] for x in range(nband)])
        #     irr_env = np.array([res[x].values['environmental_irradiance'] for x in range(nband)])

        #     # Check for potential zero values and interpolate them with neighbour
        #     val, ind0 = np.where([direct==0])
        #     if len(ind0)>0:
        #         for i0 in ind0:
        #             direct[i0] = (direct[i0-1]+direct[i0+1])/2

        #     res_py6s[n] = {'direct_ratio': direct, 'diffuse_ratio': diffuse, 'env_ratio': env,
        #                 'direct_irr': irr_direct, 'diffuse_irr': irr_diffuse, 'env_irr': irr_env,
        #                 'solar_zenith':sun_zenith[ind_anc], 'total_gaseous_transmittance':total_gaseous_transmittance}

        return res_py6s

    @staticmethod
    def cosine_error_correction(node, sensortype):
        ''' Used for both SeaBird and TriOS L1b'''

        ## Angular cosine correction (for Irradiance)
        unc_grp = node.getGroup('RAW_UNCERTAINTIES')
        radcal_wvl = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['1'][1:].tolist())
        coserror = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_ANGDATA_COSERROR").data))[1:,2:]
        coserror_90 = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_ANGDATA_COSERROR_AZ90").data))[1:,2:]
        zenith_ang = unc_grp.getDataset(sensortype+"_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
        # zenith_ang_90 = unc_grp.getDataset(sensortype+"_ANGDATA_COSERROR_AZ90").attributes["COLUMN_NAMES"].split('\t')[2:]
        i1 = np.argmin(np.abs(radcal_wvl-300))
        i2 = np.argmin(np.abs(radcal_wvl-1000))
        zenith_ang = np.asarray([float(x) for x in zenith_ang])

        # comparing cos_error for 2 azimuth
        AZI_delta_cos = coserror-coserror_90

        # if delta < 2% : averaging the 2 azimuth plan
        AZI_avg_coserror = (coserror+coserror_90)/2.

        # comparing cos_error for symetric zenith
        ZEN_delta_cos = AZI_avg_coserror - AZI_avg_coserror[:,::-1]

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

    def processL1b_SeaBird(node):
        # calibration of HyperOCR following the FRM processing of FRM4SOC2

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
            mZ = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_STRAYDATA_LSF").data))
            mZ = mZ[1:,1:] # remove 1st line and column, we work on 255 pixel not 256.
            Ct = pd.DataFrame(unc_grp.getDataset(sensortype+"_TEMPDATA_CAL").data)[sensortype+"_TEMPERATURE_COEFFICIENTS"][1:].tolist()
            LAMP = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_LAMP").data)['2'])

            # Defined constants
            nband = len(radcal_wvl)
            nmes  = len(raw_data)
            n_iter = 5

            # Non-linearity alpha computation
            cal_int = radcal_cal.pop(0)
            t1 = S1.pop(0)
            t2 = S2.pop(0)
            k = t1/(t2-t1)
            S12 = (1+k)*S1 - k*S2
            S12_sl_corr = ProcessL1b_FRMCal.Slaper_SL_correction(S12, mZ, n_iter)
            alpha = ((S1-S12)/(S12**2)).tolist()
            LAMP = np.pad(LAMP, (0, nband-len(LAMP)), mode='constant') # PAD with zero if not 255 long

            # Updated calibration gain
            if sensortype == "ES":
                updated_radcal_gain = (S12_sl_corr/LAMP) * (10*cal_int/t1)
                ## Compute avg cosine error
                avg_coserror, full_hemi_coserror, zenith_ang = ProcessL1b_FRMCal.cosine_error_correction(node, sensortype)
                ## Irradiance direct and diffuse ratio
                res_py6s = ProcessL1b_FRMCal.get_direct_irradiance_ratio(node, sensortype)
            else:
                PANEL = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_PANEL").data)['2'])
                PANEL = np.pad(PANEL, (0, nband-len(PANEL)), mode='constant')
                updated_radcal_gain = (np.pi*S12_sl_corr)/(LAMP*PANEL) * (10*cal_int/t1)


            ## sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
            ind_zero = radcal_cal<=0
            ind_nan  = np.isnan(radcal_cal)
            ind_nocal = ind_nan | ind_zero
            # set 1 instead of 0 to perform calibration (otherwise division per 0)
            updated_radcal_gain[ind_nocal==True] = 1

            # keep only defined wavelength
            updated_radcal_gain = updated_radcal_gain[ind_nocal==False]
            wvl = radcal_wvl[ind_nocal==False]
            str_wvl = np.asarray([str(x) for x in wvl])
            dark = dark[ind_nocal==False]
            alpha = np.asarray(alpha)[ind_nocal==False]
            mZ = mZ[:, ind_nocal==False]
            mZ = mZ[ind_nocal==False, :]
            Ct = np.asarray(Ct)[ind_nocal==False]

            FRM_mesure = np.zeros((nmes, len(updated_radcal_gain)))
            ind_raw_data = (radcal_cal[radcal_wvl>0])>0
            for n in range(nmes):
                # raw data
                data = raw_data[n][ind_raw_data]
                # Non-linearity
                data = data*(1-alpha*data)
                # Straylight
                data = ProcessL1b_FRMCal.Slaper_SL_correction(data, mZ, n_iter)
                # Calibration
                data = data * (cal_int/int_time[n]) / updated_radcal_gain
                # thermal
                data = data * Ct
                # Cosine correction
                if sensortype == "ES":
                    solar_zenith = res_py6s['solar_zenith']
                    direct_ratio = res_py6s['direct_ratio'][ind_raw_data]
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

        return True