import os
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from Source.ConfigFile import ConfigFile
from Source.ProcessL1b import ProcessL1b
from Source.ProcessL1b_Interp import ProcessL1b_Interp
from Source.Utilities import Utilities
from Source.Uncertainty_Analysis import Propagate

class TriosL1B:


    @staticmethod
    def processDarkCorrection_FRM(node, instrument_number, sensortype, stats: dict):
        # Dark & Calibration process for FRM branch using Full Characterisation from TO,
        # and with additional correction for (non-linearity, straylight, ...)

        ### Read HDF file inputs
        grp = node.getGroup(instrument_number+'.dat')
        raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())
        DarkPixelStart = int(grp.attributes["DarkPixelStart"])
        DarkPixelStop  = int(grp.attributes["DarkPixelStop"])
        int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
        int_time_t0 = int(grp.getDataset("BACK_"+sensortype).attributes["IntegrationTime"])

        ### Read full characterisation files
        unc_grp = node.getGroup('RAW_UNCERTAINTIES')
        radcal_wvl = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['1'][1:].tolist())
        str_wvl = np.asarray([str(x) for x in radcal_wvl])
        # radcal_cal = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['2'][1:].tolist())
        B0 = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['4'][1:].tolist())
        B1 = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['5'][1:].tolist())
        S1 = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['6']
        S2 = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['8']
        mZ = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_STRAYDATA_LSF").data))
        mZ = mZ[1:,1:] # remove 1st line and column, we work on 255 pixel not 256.
        Ct = pd.DataFrame(unc_grp.getDataset(sensortype+"_TEMPDATA_CAL").data)[sensortype+"_TEMPERATURE_COEFFICIENTS"][1:].tolist()
        LAMP = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_LAMP").data)['2'])

        # Defined constants
        nband = len(B0)
        nmes  = len(raw_data)
        n_iter = 5

        # Non-linearity alpha computation
        t1 = S1.pop(0)
        t2 = S2.pop(0)
        S1 = S1/65535.0
        S2 = S2/65535.0
        k = t1/(t2-t1)
        S12 = (1+k)*S1 - k*S2
        S12_sl_corr = ProcessL1b.Slaper_SL_correction(S12, mZ, n_iter)
        alpha = ((S1-S12)/(S12**2)).tolist()

        # Updated calibration gain
        if sensortype == "ES":
            updated_radcal_gain = (S12_sl_corr/LAMP) * (int_time_t0/t1)
            # Compute avg cosine error (not done for the moment)
            avg_coserror, full_hemi_coserror, zenith_ang = ProcessL1b.cosine_error_correction(node, sensortype)
            # Irradiance direct and diffuse ratio
            res_py6s = ProcessL1b.get_direct_irradiance_ratio(node, sensortype, trios=instrument_number)
        else:
            PANEL = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_PANEL").data)['2'])
            updated_radcal_gain = (np.pi*S12_sl_corr)/(LAMP*PANEL) * (int_time_t0/t1)

        # sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = (updated_radcal_gain<=1e-2)
        ind_nan  = np.isnan(updated_radcal_gain)
        ind_nocal = ind_nan | ind_zero
        updated_radcal_gain[ind_nocal==True] = 1 # set 1 instead of 0 to perform calibration (otherwise division per 0)

        # Data conversion
        mesure = raw_data/65365.0
        FRM_mesure = np.zeros((nmes, nband))
        back_mesure = np.zeros((nmes, nband))

        for n in range(nmes):
            # Background correction : B0 and B1 read from full charaterisation
            back_mesure[n,:] = B0 + B1*(int_time[n]/int_time_t0)
            back_corrected_mesure = mesure[n] - back_mesure[n,:]
            # Offset substraction : dark index read from attribute
            offset = np.mean(back_corrected_mesure[DarkPixelStart:DarkPixelStop])
            offset_corrected_mesure = back_corrected_mesure - offset
            # Non-linearity correction
            linear_corr_mesure = offset_corrected_mesure*(1-alpha*offset_corrected_mesure)
            # Straylight correction over measurement
            straylight_corr_mesure = ProcessL1b.Slaper_SL_correction(linear_corr_mesure, mZ, n_iter)
            # Normalization for integration time
            normalized_mesure = straylight_corr_mesure * int_time_t0/int_time[n]
            # Absolute calibration
            # calibrated_mesure_origin = (offset_corrected_mesure*int_time_t0/int_time[n])/radcal_cal
            calibrated_mesure = normalized_mesure/updated_radcal_gain
            # Thermal correction
            thermal_corr_mesure = Ct*calibrated_mesure
            # Cosine correction : commented for the moment
            if sensortype == "ES":
                solar_zenith = res_py6s['solar_zenith']
                direct_ratio = res_py6s['direct_ratio']
                ind_closest_zen = np.argmin(np.abs(zenith_ang-solar_zenith))
                cos_corr = 1-avg_coserror[:,ind_closest_zen]/100
                Fhcorr = 1-full_hemi_coserror/100
                cos_corr_mesure = (direct_ratio*thermal_corr_mesure*cos_corr) + ((1-direct_ratio)*thermal_corr_mesure*Fhcorr)
                FRM_mesure[n,:] = cos_corr_mesure

            else:
                FRM_mesure[n,:] = thermal_corr_mesure

        # Remove wvl without calibration from the dataset
        # unit conversion from mW/m2 to uW/cm2 : divide per 10
        filtered_mesure = FRM_mesure[:,ind_nocal==False]
        filtered_wvl = str_wvl[ind_nocal==False]

        # Replace raw data with calibrated data in hdf root
        ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
        rec_arr = np.rec.fromarrays(np.array(filtered_mesure).transpose(), dtype=ds_dt)
        grp.getDataset(sensortype).data = rec_arr

        # Rename the group from serial_numer to frame type
        grp.id = sensortype

        # Get light and dark data before correction
        light_avg = np.mean(mesure, axis=0)
        back_avg  = np.mean(back_mesure, axis=0)
        light_std = np.std(mesure, axis=0)
        back_std  = np.std(back_mesure, axis=0)
        stdevSignal = {}
        for i, wvl in enumerate(str_wvl):
            stdevSignal[wvl] = pow((pow(light_std[i],2) + pow(back_std[i], 2)) / pow(light_avg[i], 2), 0.5)

        stats[sensortype] = {'ave_Light': np.array(light_avg), 'ave_Dark': np.array(back_avg),
                          'std_Light': np.array(light_std), 'std_Dark': np.array(back_std),
                          'std_Signal': stdevSignal, 'wvl':str_wvl}  # std_Signal stored as dict to help when interpolating wavebands

        return True

    @staticmethod
    def processDarkCorrection(node, instrument_number, sensortype, stats: dict):
        # Dark correction performed for each trios radiometers
        # Instrument serial number and associated frame type are read in configuration
        # return the wvl of dark pixel for which no calibration factor is defined

        # Read HDF file inputs
        # grp = node.getGroup(instrument_number+'.dat')
        grp = node.getGroup(sensortype)
        raw_cal  = grp.getDataset("CAL_"+sensortype).data
        raw_back = grp.getDataset("BACK_"+sensortype).data
        raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())
        raw_wvl = np.array(pd.DataFrame(grp.getDataset(sensortype).data).columns)
        int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
        DarkPixelStart = int(grp.attributes["DarkPixelStart"])
        DarkPixelStop  = int(grp.attributes["DarkPixelStop"])
        # int_time_t0 = int(grp.getDataset("BACK_"+sensortype).attributes["IntegrationTime"])
        int_time_t0 = int(grp.attributes["IntegrationTime"])

        # Retain raw data for L2 instrument uncertainty analysis
        grp.addDataset(sensortype+'_RAW')
        grp.datasets[sensortype+'_RAW'].data = grp.getDataset(sensortype).data

        '''
        Temporary patch for bad int_time_t0 in .ini files

        WARNING: THIS WILL NOT BE ACCURATE AND MUST BE REMOVED LATER
        '''

        if int_time_t0 == 0:
            int_time_t0 = 1

        # check size of data
        nband = len(raw_back[:,0])
        nmes = len(raw_data)
        if nband != len(raw_data[0]):
            print("ERROR: different number of pixel between dat and back")
            exit()

        # sensitivity factor : if raw_cal==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = (raw_cal==0)
        ind_nan  = np.isnan(raw_cal)
        ind_nocal = ind_nan | ind_zero
        raw_cal[ind_nocal==True] = 1 # set 1 instead of 0 to perform calibration (otherwise division per 0)

        # Data conversion
        mesure = raw_data/65365.0
        calibrated_mesure = np.zeros((nmes, nband))
        back_mesure = np.zeros((nmes, nband))
        for n in range(nmes):
            # Background correction : B0 and B1 read from "back data"
            back_mesure[n,:] = raw_back[:,0] +  raw_back[:,1]*(int_time[n]/int_time_t0)
            back_corrected_mesure = mesure[n] - back_mesure[n,:]

            # Offset substraction : dark index read from attribute
            offset = np.mean(back_corrected_mesure[DarkPixelStart:DarkPixelStop])
            offset_corrected_mesure = back_corrected_mesure - offset

            # Normalization for integration time
            normalized_mesure = offset_corrected_mesure * int_time_t0/int_time[n]

            # Sensitivity calibration
            calibrated_mesure[n,:] = normalized_mesure/raw_cal

            # # When no calibration available, set data to 0.
            # calibrated_mesure[n, ind_nocal==True] = 0.  # not used at the moment

        # Remove wvl without calibration from the dataset
        filtered_mesure = calibrated_mesure[:,ind_nocal==False]
        filtered_wvl = raw_wvl[ind_nocal==False]

        # replace raw data with calibrated data in hdf root
        ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
        rec_arr = np.rec.fromarrays(np.array(filtered_mesure).transpose(), dtype=ds_dt)
        grp.getDataset(sensortype).data = rec_arr
        # And rename the group from serial_numer to frame type
        # grp.id = sensortype

        # get light and dark data before correction
        light_avg = np.mean(mesure, axis=0)
        back_avg = np.mean(back_mesure, axis=0)
        light_std = np.std(mesure, axis=0)
        back_std = np.std(back_mesure, axis=0)
        stdevSignal = {}
        for i, wvl in enumerate(raw_wvl):
            stdevSignal[wvl] = pow((pow(light_std[i],2) + pow(back_std[i], 2)) / pow(light_avg[i], 2), 0.5)

        stats[sensortype] = {'ave_Light': np.array(light_avg), 'ave_Dark': np.array(back_avg),
                          'std_Light': np.array(light_std), 'std_Dark': np.array(back_std),
                          'std_Signal': stdevSignal, 'wvl':raw_wvl}  # std_Signal stored as dict to help when interpolating wavebands
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
        node.attributes['WAVE_INTERP'] = str(ConfigFile.settings['fL1bInterpInterval']) + ' nm'
        if ConfigFile.settings["bL1bCal"] == 1:
            node.attributes['CAL_TYPE'] = 'Factory'
        elif ConfigFile.settings["bL1bCal"] == 2:
            node.attributes['CAL_TYPE'] = 'Class-based'
        elif ConfigFile.settings["bL1bCal"] == 3:
            node.attributes['CAL_TYPE'] = 'Instrument-based'

        msg = f"TriosL1B.processL1b: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        node  = Utilities.rootAddDateTime(node)
        stats = {}

        '''
        It is unclear whether we need to introduce new datasets within radiometry groups for
        uncertainties prior to dark correction (e.g. what about variability/stability in dark counts?)
        Otherwise, uncertainty datasets could be added during calibration below to the ES, LI, LT
        groups. A third option is to add a new group for uncertainties, but this would have to
        happen after interpolation below so all datasets within the group shared timestamps, as
        in all other groups.
        '''

        ## Dark Correction & Absolute Calibration
        for instrument in ConfigFile.settings['CalibrationFiles'].keys():
            # get instrument serial number and sensor type
            instrument_number = os.path.splitext(instrument)[0]
            sensortype = ConfigFile.settings['CalibrationFiles'][instrument]['frameType']
            enabled = ConfigFile.settings['CalibrationFiles'][instrument]['enabled']
            if enabled:
                msg = f'Dark Correction: {instrument_number} - {sensortype}'
                print(msg)
                Utilities.writeLogFile(msg)

                if ConfigFile.settings["bL1bCal"] <= 2:
                    if not TriosL1B.processDarkCorrection(node, instrument_number, sensortype, stats):
                        msg = f'Error in TriosL1B.processDarkCorrection: {instrument_number} - {sensortype}'
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return None
                elif ConfigFile.settings['bL1bCal'] == 3:
                    if not TriosL1B.processDarkCorrection_FRM(node, instrument_number, sensortype, stats):
                        msg = f'Error in TriosL1B.processDarkCorrection_FRM: {instrument_number} - {sensortype}'
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return None


        # ## Uncertainty computation/initialisation
        # if ConfigFile.settings["bL1bCal"] == 1:
        #     if not ProcessL1b.process_Default_Uncertainties(node, stats):
        #         msg = 'Error in process_Default_Uncertainties'
        #         print(msg)
        #         Utilities.writeLogFile(msg)
        #         return None
        # elif ConfigFile.settings["bL1bCal"] == 2:
        #     if not ProcessL1b.process_Class_Uncertainties(node, stats):
        #         msg = 'Error in process_Class_Uncertainties'
        #         print(msg)
        #         Utilities.writeLogFile(msg)
        #         return None
        # elif ConfigFile.settings['bL1bCal'] == 3:
        #     if not ProcessL1b.process_FRM_Uncertainties(node, stats):
        #         msg = 'Error in process_FRM_Uncertainties'
        #         print(msg)
        #         Utilities.writeLogFile(msg)
        #         return None


        ## Interpolation
        # Match instruments to a common timestamp (slowest shutter, should be Lt) and
        # interpolate to the chosen spectral resolution. HyperSAS instruments operate on
        # different timestamps and wavebands, so interpolation is required.
        node = ProcessL1b_Interp.processL1b_Interp(node, outFilePath)


        return node
