
'''
Placeholder for SeaBird Class-based Cal
'''
import numpy as np
import pandas as pd

class ProcessL1b_ClassCal:

    def processL1b_SeaBird(node):
        # calibration of HyperOCR following the class-based processing of FRM4SOC2
        
        unc_grp = node.getGroup('RAW_UNCERTAINTIES')
        for sensortype in ['ES', 'LI', 'LT']:
            print('Class-based Processing:', sensortype)
            # Read data
            grp = node.getGroup(sensortype)
            raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())
            int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
        
            # Read FRM characterisation
            # radcal_wvl = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['1'][1:].tolist())
            radcal_wvl = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['1']
            radcal_cal = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['2']
            # dark = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['4'][1:].tolist())
            S1 = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['6']
            S2 = pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_CAL").data)['8']
            LAMP = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_LAMP").data)['2'])

            # Defined constants
            nband = len(radcal_wvl)
            nmes  = len(raw_data)
        
            # Non-linearity alpha computation
            cal_int = radcal_cal
            k = S1/(S2-S1)
            S12 = (1+k)*S1 - k*S2
            alpha = ((S1-S12)/(S12**2)).tolist()
            LAMP = np.pad(LAMP, (0, nband-len(LAMP)), mode='constant') # PAD with zero if not 255 long
        
            # Updated calibration gain
            if sensortype == "ES":
                updated_radcal_gain = (S12/LAMP) * (10*cal_int/S1)
            else:
                PANEL = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype+"_RADCAL_PANEL").data)['2'])
                PANEL = np.pad(PANEL, (0, nband-len(PANEL)), mode='constant')
                updated_radcal_gain = (np.pi*S12)/(LAMP*PANEL) * (10*cal_int/S1)
        
        
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
            alpha = np.asarray(alpha)[ind_nocal==False]
            cal_int = np.asarray(cal_int)[ind_nocal==False]
        
            ClassBased_mesure = np.zeros((nmes, len(updated_radcal_gain)))
            ind_raw_data = (radcal_cal[radcal_wvl>0])>0
            for n in range(nmes):
                # raw data
                data = raw_data[n][ind_raw_data]
                # Non-linearity
                data = data*(1-alpha*data)
                # Calibration
                ClassBased_mesure[n,:] = data * (cal_int/int_time[n]) / updated_radcal_gain
                        
            # Remove wvl without calibration from the dataset
            filtered_mesure = ClassBased_mesure
            filtered_wvl = str_wvl
        
            # Replace raw data with calibrated data in hdf root
            ds_dt = np.dtype({'names': filtered_wvl,'formats': [np.float64]*len(filtered_wvl)})
            rec_arr = np.rec.fromarrays(np.array(filtered_mesure).transpose(), dtype=ds_dt)
            grp.getDataset(sensortype).data = rec_arr
        
        return True
