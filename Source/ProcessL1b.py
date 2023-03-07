
import os
import datetime as dt
import calendar
import numpy as np
from inspect import currentframe, getframeinfo

from HDFRoot import HDFRoot
from ProcessL1b_DefaultCal import ProcessL1b_DefaultCal
from ConfigFile import ConfigFile
from CalibrationFileReader import CalibrationFileReader
from ProcessL1b_Interp import ProcessL1b_Interp
from Utilities import Utilities
from Uncertainty_Analysis import Propagate
import pandas as pd
import matplotlib.pyplot as plt
import Py6S 

class ProcessL1b:

    @staticmethod
    def get_direct_irradiance_ratio(node, sensortype, trios=0):
        
        ## Reading ancilliary data
        anc_grp = node.getGroup('ANCILLARY_METADATA')
        # lat = np.asarray(pd.DataFrame(anc_grp.getDataset("LATITUDE").data))
        # lon = np.asarray(pd.DataFrame(anc_grp.getDataset("LONGITUDE").data))
        rel_az = np.asarray(pd.DataFrame(anc_grp.getDataset("REL_AZ").data))
        sun_zenith = np.asarray(pd.DataFrame(anc_grp.getDataset("SZA").data))
        sun_azimuth = np.asarray(pd.DataFrame(anc_grp.getDataset("SOLAR_AZ").data))
        anc_datetag = np.asarray(pd.DataFrame(anc_grp.getDataset("DATETAG").data))
        anc_timetag = np.asarray(pd.DataFrame(anc_grp.getDataset("TIMETAG2").data))
        anc_datetime = [dt.datetime.strptime(str(int(x[0]))+str(int(y[0])).rjust(9,'0'), "%Y%j%H%M%S%f") for x,y in zip(anc_datetag,anc_timetag)]

        ## Reading irradiance data
        if trios == 0:
            irr_grp = node.getGroup(sensortype)
        else:
            irr_grp = node.getGroup(trios+'.dat')
        str_wvl = np.asarray(pd.DataFrame(irr_grp.getDataset(sensortype).data).columns)
        wvl = np.asarray([float(x) for x in str_wvl])        
        datetag = np.asarray(pd.DataFrame(irr_grp.getDataset("DATETAG").data))
        timetag = np.asarray(pd.DataFrame(irr_grp.getDataset("TIMETAG2").data))
        datetime = [dt.datetime.strptime(str(int(x[0]))+str(int(y[0])).rjust(9,'0'), "%Y%j%H%M%S%f") for x,y in zip(datetag,timetag)]
        # datetime_str = [x.strftime("%Y-%m-%d %H:%M:%S") for x in datetime]     
        
        ## Py6S configuration
        n_mesure = len(datetag)
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
        s.aot550 = 0.153
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


    @staticmethod
    def convertDataset(group, datasetName, newGroup, newDatasetName):
        ''' Converts a sensor group into the L1B format; option to change dataset name.
            Moves dataset to new group.
            The separate DATETAG, TIMETAG2, and DATETIME datasets are combined into
            the sensor dataset. This also adds a temporary column in the sensor data
            array for datetime to be used in interpolation. This is later removed, as
            HDF5 does not support datetime. '''

        dataset = group.getDataset(datasetName)
        dateData = group.getDataset("DATETAG")
        timeData = group.getDataset("TIMETAG2")
        dateTimeData = group.getDataset("DATETIME")

        # Convert degrees minutes to decimal degrees format; only for GPS, not ANCILLARY_METADATA
        if group.id.startswith("GP"):
            if newDatasetName == "LATITUDE":
                latPosData = group.getDataset("LATPOS")
                latHemiData = group.getDataset("LATHEMI")
                for i in range(dataset.data.shape[0]):
                    latDM = latPosData.data["NONE"][i]
                    latDirection = latHemiData.data["NONE"][i]
                    latDD = Utilities.dmToDd(latDM, latDirection)
                    latPosData.data["NONE"][i] = latDD
            if newDatasetName == "LONGITUDE":
                lonPosData = group.getDataset("LONPOS")
                lonHemiData = group.getDataset("LONHEMI")
                for i in range(dataset.data.shape[0]):
                    lonDM = lonPosData.data["NONE"][i]
                    lonDirection = lonHemiData.data["NONE"][i]
                    lonDD = Utilities.dmToDd(lonDM, lonDirection)
                    lonPosData.data["NONE"][i] = lonDD

        newSensorData = newGroup.addDataset(newDatasetName)

        # Datetag, Timetag2, and Datetime columns added to sensor data array
        newSensorData.columns["Datetag"] = dateData.data["NONE"].tolist()
        newSensorData.columns["Timetag2"] = timeData.data["NONE"].tolist()
        newSensorData.columns["Datetime"] = dateTimeData.data

        # Copies over the sensor dataset from original group to newGroup
        for k in dataset.data.dtype.names: # For each waveband (or vector data for other groups)
            #print("type",type(esData.data[k]))
            newSensorData.columns[k] = dataset.data[k].tolist()
        newSensorData.columnsToDataset()

    @staticmethod
    def darkCorrection(darkData, darkTimer, lightData, lightTimer, sensor, stats: dict):
        '''
        HyperInSPACE - Interpolate Dark values to match light measurements (e.g. Brewin 2016, Prosoft
        7.7 User Manual SAT-DN-00228-K)
        '''
        if (darkData is None) or (lightData is None):
            msg = f'Dark Correction, dataset not found: {darkData} , {lightData}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        if Utilities.hasNan(lightData):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'

        if Utilities.hasNan(darkData):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'

        # Interpolate Dark Dataset to match number of elements as Light Dataset
        newDarkData = np.copy(lightData.data)
        for k in darkData.data.dtype.fields.keys(): # For each wavelength
            x = np.copy(darkTimer.data).tolist() # darktimer
            y = np.copy(darkData.data[k]).tolist()  # data at that band over time
            new_x = lightTimer.data  # lighttimer

            if len(x) < 3 or len(y) < 3 or len(new_x) < 3:
                msg = "**************Cannot do cubic spline interpolation, length of datasets < 3"
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            if not Utilities.isIncreasing(x):
                msg = "**************darkTimer does not contain strictly increasing values"
                print(msg)
                Utilities.writeLogFile(msg)
                return False
            if not Utilities.isIncreasing(new_x):
                msg = "**************lightTimer does not contain strictly increasing values"
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            if len(x) >= 3:
                # Because x is now a list of datetime tuples, they'll need to be
                # converted to Unix timestamp values
                xTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in x]
                newXTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in new_x]

                newDarkData[k] = Utilities.interp(xTS,y,newXTS, fill_value=np.nan)

                for val in newDarkData[k]:
                    if np.isnan(val):
                        frameinfo = getframeinfo(currentframe())
                        msg = f'found NaN {frameinfo.lineno}'
            else:
                msg = '**************Record too small for splining. Exiting.'
                print(msg)
                Utilities.writeLogFile(msg)
                return False

        darkData.data = newDarkData

        if Utilities.hasNan(darkData):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'
            print(msg)
            Utilities.writeLogFile(msg)
            exit()

        # Correct light data by subtracting interpolated dark data from light data
        wvl = []
        std_Light = []
        std_Dark = []
        ave_Light = []
        ave_Dark = []
        stdevSignal = {}
        for i, k in enumerate(lightData.data.dtype.fields.keys()):
            k1 = str(float(k))
            # number of replicates for light and dark readings
            N = lightData.data.shape[0]
            Nd = newDarkData.data.shape[0]
            wvl.append(k1)

            # apply normalisation to the standard deviations used in uncertainty calculations
            std_Light.append(np.std(lightData.data[k]) / pow(N, 0.5))  # = (sigma / sqrt(N))**2 or sigma**2
            std_Dark.append(np.std(newDarkData[k]) / pow(Nd, 0.5))  # sigma here is essentially sigma**2 so N must be rooted
            ave_Light.append(np.average(lightData.data[k]))
            ave_Dark.append(np.average(darkData.data[k]))

            for x in range(lightData.data.shape[0]):
                lightData.data[k][x] -= newDarkData[k][x]

            # Normalised signal standard deviation =
            # U^2 = (std_light^2 / replicates_light) + (std_dark^2 / replicates Dark) / (light - dark)^2
            signalAve = np.average(lightData.data[k])
            stdevSignal[k1] = pow((pow(std_Light[-1], 2) + pow(std_Dark[-1], 2))/pow(signalAve, 2), 0.5)
                
        # return all the necessary statistics from the substitution by adding to this dictionary
        stats[sensor] = {'ave_Light': np.array(ave_Light), 'ave_Dark': np.array(ave_Dark),
                         'std_Light': np.array(std_Light), 'std_Dark': np.array(std_Dark),
                         'std_Signal': stdevSignal, 'wvl':wvl}  # std_Signal stored as dict to help when interpolating wavebands

        if Utilities.hasNan(lightData):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'
            print(msg)
            Utilities.writeLogFile(msg)
            exit()

        return True


    def process_FRM_calibration(node):
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
            S12_sl_corr = ProcessL1b.Slaper_SL_correction(S12, mZ, n_iter)
            alpha = ((S1-S12)/(S12**2)).tolist()    
            LAMP = np.pad(LAMP, (0, nband-len(LAMP)), mode='constant') # PAD with zero if not 255 long               

            # Updated calibration gain
            if sensortype == "ES":
                updated_radcal_gain = (S12_sl_corr/LAMP) * (10*cal_int/t1)
                ## Compute avg cosine error
                avg_coserror, full_hemi_coserror, zenith_ang = ProcessL1b.cosine_error_correction(node, sensortype)            
                ## Irradiance direct and diffuse ratio
                res_py6s = ProcessL1b.get_direct_irradiance_ratio(node, sensortype, trios=0)
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
                data = ProcessL1b.Slaper_SL_correction(data, mZ, n_iter)
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



    @staticmethod
    def process_FRM_Uncertainties(node, stats):
        
        # Generate Uncertainties
        uncertGrp = node.getGroup("RAW_UNCERTAINTIES")
        
        # set up for Uncertainty Calculation
        Propagate_L1b = Propagate(M=10000, cores=0)
        Cal = {}; Coeff = {}; cPol = {}; cAng = {}; cStray = {}; cTemp = {}; cLin = {}; cStab = {}
        for sensor in ['ES', 'LI', 'LT']:

            # populate the columns dictionary to make data groups more readable
            SL_unc = np.asarray(pd.DataFrame(uncertGrp.getDataset(sensor+"_STRAYDATA_UNCERTAINTY").data))[1:,1:]
            cStray[sensor] = np.sum(SL_unc, axis=0) # for test : wrong equation
            # TODO : how to use SL_unc matrix ???
               
            linear = uncertGrp.getDataset(sensor+"_NLDATA_CAL")
            linear.datasetToColumns()
            cLin[sensor] = linear.data[list(linear.columns.keys())[1]]
                                                     
            stab = uncertGrp.getDataset(sensor+"_STABDATA_CAL")
            stab.datasetToColumns()
            cStab[sensor] = stab.data[list(stab.columns.keys())[1]]
               
            radcal = uncertGrp.getDataset(f"{sensor}_RADCAL_CAL")
            radcal.datasetToColumns()
            Coeff[sensor] = radcal.data[list(radcal.columns.keys())[2]][1:]
            Cal[sensor] = radcal.data[list(radcal.columns.keys())[3]][1:]
            
            if sensor == "ES":
                ang_unc = np.asarray(pd.DataFrame(uncertGrp.getDataset(sensor+"_ANGDATA_UNCERTAINTY").data))[1:,2:]
                cAng[sensor] = np.sum(ang_unc, axis=1) # for test : wrong equation
                # TODO : How to use Ang_unc ???
            else:
                pol = uncertGrp.getDataset(sensor+"_POLDATA_CAL")
                pol.datasetToColumns()
                cPol[sensor] = pol.data[list(pol.columns.keys())[5]][1:]
                
            Temp = uncertGrp.getDataset(sensor+"_TEMPDATA_CAL")
            Temp.datasetToColumns()        
            cTemp[sensor] = Temp.columns[f"{sensor}_TEMPERATURE_UNCERTAINTIES"][1:] 

        # n_wvl = np.shape(stats['ES']['std_Light'])
        n_wvl = len(Cal['ES'])
        ones = np.ones(n_wvl)
        
        means = [stats['ES']['ave_Light'], stats['ES']['ave_Dark'],
                 stats['LI']['ave_Light'], stats['LI']['ave_Dark'],
                 stats['LT']['ave_Light'], stats['LT']['ave_Dark'],
                 Coeff['ES'], Coeff['LI'], Coeff['LT'], ones, ones, ones, ones, ones, ones,
                 ones, ones, ones, ones, ones, ones, ones, ones, ones]
            
        uncertainties = [stats['ES']['std_Light'], stats['ES']['std_Dark'],
                         stats['LI']['std_Light'], stats['LI']['std_Dark'],
                         stats['LT']['std_Light'], stats['LT']['std_Dark'],
                         Cal['ES']*Coeff['ES']/100, Cal['LI']*Coeff['LI']/100, Cal['LT']*Coeff['LT']/100,
                         cStab['ES'], cStab['LI'], cStab['LT'],
                         cLin['ES'], cLin['LI'], cLin['LT'],
                         np.array(cStray['ES'])/100, np.array(cStray['LI'])/100, np.array(cStray['LT'])/100,
                         np.array(cTemp['ES']), np.array(cTemp['LI']), np.array(cTemp['LT']),
                         np.array(cPol['LI']), np.array(cPol['LT']), np.array(cAng['ES'])]
        
        # pad with zeros if wome wvl are not defined in the calibration
        for i, m in enumerate(means):
            if len(m) < n_wvl:
                means[i] = np.pad(m, (0,n_wvl-len(m)), mode='constant')
        for i, u in enumerate(uncertainties):
            if len(u) < n_wvl:
                uncertainties[i] = np.pad(u, (0,n_wvl-len(u)), mode='constant')

        """c1, c2, c3, clin1, clin2, clin3, cstab1, cstab2, cstab3, cstray1, cstray2, cstray3, cT1, cT2, cT3, cpol1, cpol2, ccos"""
        ES_unc, LI_unc, LT_unc, ES_rel, LI_rel, LT_rel = Propagate_L1b.propagate_Instrument_Uncertainty(means, uncertainties)
        
        # Output standard deviations for each sensor
        esGrp = node.getGroup("ES")
        liGrp = node.getGroup("LI")
        ltGrp = node.getGroup("LT")
        esStd = esGrp.addDataset("ES_std"); liStd = liGrp.addDataset("LI_std"); ltStd = ltGrp.addDataset("LT_std")
        esDS = esGrp.addDataset("ES_unc"); esDSrel = esGrp.addDataset("ES_unc_relative")
        liDS = liGrp.addDataset("LI_unc"); liDSrel = liGrp.addDataset("LI_unc_relative")
        ltDS = ltGrp.addDataset("LT_unc"); ltDSrel = ltGrp.addDataset("LT_unc_relative")
        
        # output uncertainties (relative, absolute and standard deviation)        
        data_wvl = np.array(pd.DataFrame(esGrp.getDataset('ES').data).columns)
        for i, k in enumerate(data_wvl):           
            esStd.columns[k] = [stats["ES"]["std_Signal"][k]]
            esDS.columns[k] = [ES_unc[i]]
            esDSrel.columns[k] = [ES_rel[i]]
            
        data_wvl = np.array(pd.DataFrame(liGrp.getDataset('LI').data).columns)
        for i, k in enumerate(data_wvl):
            liStd.columns[k] = [stats["LI"]["std_Signal"][k]]
            liDS.columns[k] = [LI_unc[i]]
            liDSrel.columns[k] = [LI_rel[i]]
            
        data_wvl = np.array(pd.DataFrame(ltGrp.getDataset('LT').data).columns)
        for i, k in enumerate(data_wvl):
            ltStd.columns[k] = [stats["LT"]["std_Signal"][k]]
            ltDS.columns[k] = [LT_unc[i]]
            ltDSrel.columns[k] = [LT_rel[i]]          

        # convert columns to datasets so that they will be correctly outputted to the hdf file
        esDS.columnsToDataset(); esDSrel.columnsToDataset(); esStd.columnsToDataset()
        liDS.columnsToDataset(); liDSrel.columnsToDataset(); liStd.columnsToDataset()
        ltDS.columnsToDataset(); ltDSrel.columnsToDataset(); ltStd.columnsToDataset()
        
        return True


    @staticmethod
    def process_Class_Uncertainties(node, stats):
        
        # Generate Uncertainties
        uncertGrp = node.getGroup("RAW_UNCERTAINTIES")
        
        # set up for Uncertainty Calculation
        Propagate_L1b = Propagate(M=10000, cores=0)
        Cal = {}; Coeff = {}; cPol = {}; cStray = {}; cTemp = {}; cLin = {}; cStab = {}
        for sensor in ['ES', 'LI', 'LT']:

            # populate the columns dictionary to make data groups more readable
            straylight = uncertGrp.getDataset(f"{sensor}_STRAYDATA_CAL")
            straylight.datasetToColumns()
            cStray[sensor] = straylight.data[list(straylight.columns.keys())[1]]
               
            linear = uncertGrp.getDataset(sensor+"_NLDATA_CAL")
            linear.datasetToColumns()
            cLin[sensor] = linear.data[list(linear.columns.keys())[1]]
                                         
            stab = uncertGrp.getDataset(sensor+"_STABDATA_CAL")
            stab.datasetToColumns()
            cStab[sensor] = stab.data[list(stab.columns.keys())[1]]
               
            radcal = uncertGrp.getDataset(f"{sensor}_RADCAL_CAL")
            radcal.datasetToColumns()
            Coeff[sensor] = radcal.data[list(radcal.columns.keys())[2]]
            Cal[sensor] = radcal.data[list(radcal.columns.keys())[3]]
               
            pol = uncertGrp.getDataset(sensor+"_POLDATA_CAL")
            pol.datasetToColumns()
            cPol[sensor] = pol.data[list(pol.columns.keys())[1]]
                
            Temp = uncertGrp.getDataset(sensor+"_TEMPDATA_CAL")
            Temp.datasetToColumns()        
            cTemp[sensor] = Temp.columns[f"{sensor}_TEMPERATURE_UNCERTAINTIES"]  
        
        ones = np.ones(len(Cal['ES']))
        
        means = [stats['ES']['ave_Light'], stats['ES']['ave_Dark'],
                 stats['LI']['ave_Light'], stats['LI']['ave_Dark'],
                 stats['LT']['ave_Light'], stats['LT']['ave_Dark'],
                 Coeff['ES'], Coeff['LI'], Coeff['LT'], ones, ones, ones, ones, ones, ones,
                 ones, ones, ones, ones, ones, ones, ones, ones, ones]
            
        uncertainties = [stats['ES']['std_Light'], stats['ES']['std_Dark'],
                         stats['LI']['std_Light'], stats['LI']['std_Dark'],
                         stats['LT']['std_Light'], stats['LT']['std_Dark'],
                         Cal['ES']*Coeff['ES']/100, Cal['LI']*Coeff['LI']/100, Cal['LT']*Coeff['LT']/100,
                         cStab['ES'], cStab['LI'], cStab['LT'],
                         cLin['ES'], cLin['LI'], cLin['LT'],
                         np.array(cStray['ES'])/100, np.array(cStray['LI'])/100, np.array(cStray['LT'])/100,
                         np.array(cTemp['ES']), np.array(cTemp['LI']), np.array(cTemp['LT']),
                         np.array(cPol['LI']), np.array(cPol['LT']), np.array(cPol['ES'])]
        
        """c1, c2, c3, clin1, clin2, clin3, cstab1, cstab2, cstab3, cstray1, cstray2, cstray3, cT1, cT2, cT3, cpol1, cpol2, ccos"""
        ES_unc, LI_unc, LT_unc, ES_rel, LI_rel, LT_rel = Propagate_L1b.propagate_Instrument_Uncertainty(means, uncertainties)
        
        # Output standard deviations for each sensor
        esGrp = node.getGroup("ES")
        liGrp = node.getGroup("LI")
        ltGrp = node.getGroup("LT")
        esStd = esGrp.addDataset("ES_std"); liStd = liGrp.addDataset("LI_std"); ltStd = ltGrp.addDataset("LT_std")
        esDS = esGrp.addDataset("ES_unc"); esDSrel = esGrp.addDataset("ES_unc_relative")
        liDS = liGrp.addDataset("LI_unc"); liDSrel = liGrp.addDataset("LI_unc_relative")
        ltDS = ltGrp.addDataset("LT_unc"); ltDSrel = ltGrp.addDataset("LT_unc_relative")
        
        # output uncertainties (relative, absolute and standard deviation)        
        data_wvl = np.array(pd.DataFrame(esGrp.getDataset('ES').data).columns)
        data_wvl = [str(float(x)) for x in data_wvl]
        for i, k in enumerate(data_wvl):           
            esStd.columns[k] = [stats["ES"]["std_Signal"][k]]
            esDS.columns[k] = [ES_unc[i]]
            esDSrel.columns[k] = [ES_rel[i]]
            
        data_wvl = np.array(pd.DataFrame(liGrp.getDataset('LI').data).columns)
        data_wvl = [str(float(x)) for x in data_wvl]
        for i, k in enumerate(data_wvl):
            liStd.columns[k] = [stats["LI"]["std_Signal"][k]]
            liDS.columns[k] = [LI_unc[i]]
            liDSrel.columns[k] = [LI_rel[i]]
            
        data_wvl = np.array(pd.DataFrame(ltGrp.getDataset('LT').data).columns)
        data_wvl = [str(float(x)) for x in data_wvl]
        for i, k in enumerate(data_wvl):
            ltStd.columns[k] = [stats["LT"]["std_Signal"][k]]
            ltDS.columns[k] = [LT_unc[i]]
            ltDSrel.columns[k] = [LT_rel[i]]
            
        # convert columns to datasets so that they will be correctly outputted to the hdf file
        esDS.columnsToDataset(); esDSrel.columnsToDataset(); esStd.columnsToDataset()
        liDS.columnsToDataset(); liDSrel.columnsToDataset(); liStd.columnsToDataset()
        ltDS.columnsToDataset(); ltDSrel.columnsToDataset(); ltStd.columnsToDataset()
        
        return True


    @staticmethod
    def process_Default_Uncertainties(node, stats):
        
        # Output standard deviations for each sensor
        esGrp = node.getGroup("ES")
        liGrp = node.getGroup("LI")
        ltGrp = node.getGroup("LT")
        esStd = esGrp.addDataset("ES_std")
        liStd = liGrp.addDataset("LI_std")
        ltStd = ltGrp.addDataset("LT_std")
        
        # output uncertainties (relative, absolute and standard deviation)        
        data_wvl = np.array(pd.DataFrame(esGrp.getDataset('ES').data).columns)
        for i, k in enumerate(data_wvl):           
            esStd.columns[k] = [stats["ES"]["std_Signal"][k]]
            
        data_wvl = np.array(pd.DataFrame(liGrp.getDataset('LI').data).columns)
        for i, k in enumerate(data_wvl):
            liStd.columns[k] = [stats["LI"]["std_Signal"][k]]
            
        data_wvl = np.array(pd.DataFrame(ltGrp.getDataset('LT').data).columns)
        for i, k in enumerate(data_wvl):
            ltStd.columns[k] = [stats["LT"]["std_Signal"][k]]
            
        # convert columns to datasets so that they will be correctly outputted to the hdf file
        esStd.columnsToDataset()
        liStd.columnsToDataset()
        ltStd.columnsToDataset()
        
        return True




    # Copies TIMETAG2 values to Timer and converts to seconds
    @staticmethod
    def copyTimetag2(timerDS, tt2DS):
        if (timerDS.data is None) or (tt2DS.data is None):
            msg = "copyTimetag2: Timer/TT2 is None"
            print(msg)
            Utilities.writeLogFile(msg)
            return

        for i in range(0, len(timerDS.data)):
            tt2 = float(tt2DS.data["NONE"][i])
            t = Utilities.timeTag2ToSec(tt2)
            timerDS.data["NONE"][i] = t

    @staticmethod
    def processDarkCorrection(node, sensorType, stats: dict):
        msg = f'Dark Correction: {sensorType}'
        print(msg)
        Utilities.writeLogFile(msg)
        darkGroup = None
        darkData = None
        darkDateTime = None
        lightGroup = None
        lightData = None
        lightDateTime = None

        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensorType):
                darkGroup = gp
                darkData = gp.getDataset(sensorType)
                darkDateTime = gp.getDataset("DATETIME")

            if gp.attributes["FrameType"] == "ShutterLight" and gp.getDataset(sensorType):
                lightGroup = gp
                lightData = gp.getDataset(sensorType)
                lightDateTime = gp.getDataset("DATETIME")

        if darkGroup is None or lightGroup is None:
            msg = f'No radiometry found for {sensorType}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        # Instead of using TT2 or seconds, use python datetimes to avoid problems crossing UTC midnight.

        if not ProcessL1b.darkCorrection(darkData, darkDateTime, lightData, lightDateTime, sensorType, stats):
            msg = f'ProcessL1d.darkCorrection failed for {sensorType}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False
            
        # Now that the dark correction is done, we can strip the dark shutter data from the
        # HDF object.
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensorType):
                node.removeGroup(gp)
        # And rename the corrected light frame
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterLight" and gp.getDataset(sensorType):
                gp.id = gp.id[0:2] # Strip off "_LIGHT" from the name
                
        return True

    @staticmethod
    def processL1b(node, outFilePath):
        '''
        Apply dark shutter correction to light data. Then apply either default factory cals
        or full instrument characterization. Introduce uncertainty group.
        Match timestamps and interpolate wavebands.
        '''
        node.attributes["PROCESSING_LEVEL"] = "1B"
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr
        if ConfigFile.settings["bL1bDefaultCal"] == 1:
            node.attributes['CAL_TYPE'] = 'Factory'
        elif ConfigFile.settings["bL1bDefaultCal"] == 2:
            node.attributes['CAL_TYPE'] = 'Class-based'
        elif ConfigFile.settings["bL1bDefaultCal"] == 3:
            node.attributes['CAL_TYPE'] = 'Full Character'    
        node.attributes['WAVE_INTERP'] = str(ConfigFile.settings['fL1bInterpInterval']) + ' nm'



        msg = f"ProcessL1b.processL1b: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        node = Utilities.rootAddDateTime(node)
        stats = {}

        ''' It is unclear whether we need to introduce new datasets within radiometry groups for
            uncertainties prior to dark correction (e.g. what about variability/stability in dark counts?)
            Otherwise, uncertainty datasets could be added during calibration below to the ES, LI, LT
            groups. A third option is to add a new group for uncertainties, but this would have to
            happen after interpolation below so all datasets within the group shared timestamps, as
            in all other groups. '''


        # Dark Correction
        if not ProcessL1b.processDarkCorrection(node, "ES", stats):
            msg = 'Error dark correcting ES'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1b.processDarkCorrection(node, "LI", stats):
            msg = 'Error dark correcting LI'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1b.processDarkCorrection(node, "LT", stats):
            msg = 'Error dark correcting LT'
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Calibration
        # Depending on the Configuration, process either the factory
        # calibration (for both factory and class based) or the complete 
        # instrument characterizations for FRM.
        if ConfigFile.settings['bL1bDefaultCal'] <= 2:
            calFolder = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
            calPath = os.path.join("Config", calFolder)
            print("Read CalibrationFile ", calPath)
            calibrationMap = CalibrationFileReader.read(calPath)
            ProcessL1b_DefaultCal.processL1b(node, calibrationMap)

        elif ConfigFile.settings['bL1bDefaultCal'] == 3:
            if not ProcessL1b.process_FRM_calibration(node):
                msg = 'Error in ProcessL1b.process_FRM_calibration'
                print(msg)
                Utilities.writeLogFile(msg)
                return None   
      

        ## Uncertainty initialisation
        if ConfigFile.settings["bL1bDefaultCal"] == 1:
            if not ProcessL1b.process_Default_Uncertainties(node, stats):
                msg = 'Error in process_Default_Uncertainties'
                print(msg)
                Utilities.writeLogFile(msg)
                return None
        elif ConfigFile.settings["bL1bDefaultCal"] == 2:
            if not ProcessL1b.process_Class_Uncertainties(node, stats):
                msg = 'Error in process_Class_Uncertainties'
                print(msg)
                Utilities.writeLogFile(msg)
                return None
        elif ConfigFile.settings['bL1bDefaultCal'] == 3:
            if not ProcessL1b.process_FRM_Uncertainties(node, stats):
                msg = 'Error in process_FRM_Uncertainties'
                print(msg)
                Utilities.writeLogFile(msg)
                return None    
            
            
        # Interpolation
        # Match instruments to a common timestamp (slowest shutter, should be Lt) and
        # interpolate to the chosen spectral resolution. HyperSAS instruments operate on
        # different timestamps and wavebands, so interpolation is required.
        node = ProcessL1b_Interp.processL1b_Interp(node, outFilePath)
        
        # Datetime format is not supported in HDF5; already removed in ProcessL1b_Interp.py

        return node
