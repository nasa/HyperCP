import numpy as np
import pandas as pd

# for common measurement functions that should be made available to all methods
# the purpose of this class is to contain methods that need to be accessed by all of the child instrument classes


class MeasurementFunctions:

    def __init__(self):
        """
        Static class to contain measurement functions
        """
        pass

    @staticmethod
    def dark_Substitution(light, dark):
        return light - dark
    
    @staticmethod
    def S12func(k, S1, S2):
        "compares DN at two separate times, part of non linearity correction derrivation"
        return ((1 + k)*S1) - (k*S2)

    @staticmethod
    def alphafunc(S1, S12):
        from decimal import Decimal

        t1 = [Decimal(S1[i]) - Decimal(S12[i]) for i in range(len(S1))]
        t2 = [pow(Decimal(S12[i]), 2) for i in range(len(S12))]
        # I added a conditional to check if any values in S12 are zero. One value of S12 was 0 which caused issue #253
        return np.asarray([float(t1[i]/t2[i]) if t2[i] != 0 else 0 for i in range(len(t1))])

    @staticmethod
    def update_cal_ES(S12_sl_corr, LAMP, cal_int, t1):
        return (S12_sl_corr/LAMP)*(10*cal_int/t1)
    
    @staticmethod
    def update_cal_rad(S12_sl_corr, LAMP, PANEL, cal_int, t1):
        return (np.pi*S12_sl_corr)/(LAMP*PANEL)*(10*cal_int/t1)
    
    @staticmethod
    def non_linearity_corr(signal, alpha):
        corrected = signal*(1 - alpha*signal)
        return corrected

    @staticmethod
    def Zong_SL_correction(input_data, C_matrix):
        return np.matmul(C_matrix, input_data)

    @staticmethod
    def Slaper_SL_correction(input_data, SL_matrix, n_iter=5):
        nband = len(input_data)
        m_norm = np.zeros(nband)

        mC = np.zeros((n_iter + 1, nband))
        mX = np.zeros((n_iter + 1, nband))
        mZ = SL_matrix
        mX[0, :] = input_data

        for i in range(nband):
            jstart = np.max([0, i - 10])
            jstop = np.min([nband, i + 10])
            m_norm[i] = np.sum(mZ[i, jstart:jstop])  # eq 4

        for i in range(nband):
            if m_norm[i] == 0:
                mZ[i, :] = np.zeros(nband)
            else:
                mZ[i, :] = mZ[i, :]/m_norm[i]  # eq 5

        for k in range(1, n_iter + 1):
            for i in range(nband):
                mC[k - 1, i] = mC[k - 1, i] + np.sum(mX[k - 1, :]*mZ[i, :])  # eq 6
                if mC[k - 1, i] == 0:
                    mX[k, i] = 0
                else:
                    mX[k, i] = (mX[k - 1, i]*mX[0, i])/mC[k - 1, i]  # eq 7

        return mX[n_iter - 1, :]

    @staticmethod
    def normalise(signal, cal_int, int_time):
        return signal*cal_int/int_time

    @staticmethod
    def absolute_calibration(signal, updated_radcal_gain):
        return signal/updated_radcal_gain

    @staticmethod
    def thermal_corr(Ct, calibrated_mesure):
        return Ct*calibrated_mesure

    @staticmethod
    def apply_CB_corr(signal, corr):
        return signal*corr

    @staticmethod
    def prepare_cos(uncGrp, sensortype, level=None, ind_raw_wvl=None):
        """
        read from hdf and prepare inputs for cos_err measurement function
        """
        ## Angular cosine correction (for Irradiance)
        if level != 'L2':
            radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
            coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:, 2:]
            cos_unc = (np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:, 2:]
                       /100)*np.abs(coserror)

            coserror_90 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
            cos90_unc = (np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:,
                         2:]/100)*np.abs(coserror_90)
        else:
            # reading in data changes if at L2 (because hdf files have different layout)
            radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
            coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:, 2:]
            cos_unc = (np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:, 2:]/100)*np.abs(coserror)
            coserror_90 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
            cos90_unc = (np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:, 2:]/100)*np.abs(coserror_90)

        radcal_unc = None  # no uncertainty in the wavelengths as they are only used to index

        zenith_ang = uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
        zenith_ang = np.asarray([float(x) for x in zenith_ang])
        zen_unc = np.asarray([0.05 for x in zenith_ang])  # default of 0.5 for solar zenith unc

        if ind_raw_wvl is not None:
            radcal_wvl = radcal_wvl[ind_raw_wvl]
            coserror = coserror[ind_raw_wvl]
            coserror_90 = coserror_90[ind_raw_wvl]
            cos_unc = cos_unc[ind_raw_wvl]
            cos90_unc = cos90_unc[ind_raw_wvl]

        return [radcal_wvl, coserror, coserror_90, zenith_ang], [radcal_unc, cos_unc, cos90_unc, zen_unc]

    @staticmethod
    def AZAvg_Coserr(coserror, coserror_90):
        # if delta < 2% : averaging the 2 azimuth plan
        return (coserror + coserror_90)/2.  # average azi coserr

    @staticmethod
    def ZENAvg_Coserr(radcal_wvl, AZI_avg_coserror):
        i1 = np.argmin(np.abs(radcal_wvl - 300))
        i2 = np.argmin(np.abs(radcal_wvl - 1000))

        # if delta < 2% : averaging symetric zenith
        ZEN_avg_coserror = (AZI_avg_coserror + AZI_avg_coserror[:, ::-1])/2.

        # set coserror to 1 outside range [450,700]
        ZEN_avg_coserror[0:i1, :] = 0
        ZEN_avg_coserror[i2:, :] = 0
        return ZEN_avg_coserror

    @staticmethod
    def FHemi_Coserr(ZEN_avg_coserror, zenith_ang):
        # Compute full hemisperical coserror
        zen0 = np.argmin(np.abs(zenith_ang))
        zen90 = np.argmin(np.abs(zenith_ang - 90))
        deltaZen = (zenith_ang[1::] - zenith_ang[:-1])

        full_hemi_coserror = np.zeros(ZEN_avg_coserror.shape[0])

        for i in range(ZEN_avg_coserror.shape[0]):
            full_hemi_coserror[i] = np.sum(
                ZEN_avg_coserror[i, zen0:zen90]*np.sin(2*np.pi*zenith_ang[zen0:zen90]/180)*deltaZen[
                                                                                           zen0:zen90]*np.pi/180)

        return full_hemi_coserror

    @staticmethod
    def cosine_corr(avg_coserror, full_hemi_coserror, zenith_ang, thermal_corr_mesure, sol_zen, dir_rat):
        ind_closest_zen = np.argmin(np.abs(zenith_ang - sol_zen))
        cos_corr = 1 - avg_coserror[:, ind_closest_zen]/100
        Fhcorr = 1 - np.array(full_hemi_coserror)/100
        cos_corr_mesure = (dir_rat*thermal_corr_mesure*cos_corr) + ((1 - dir_rat)*thermal_corr_mesure*Fhcorr)

        return cos_corr_mesure

    @staticmethod
    def get_cos_corr(zenith_angle, solar_zenith, cosine_error):
        ind_closest_zen = np.argmin(np.abs(zenith_angle - solar_zenith))
        return 1 - cosine_error[:, ind_closest_zen]/100

    @staticmethod
    def cos_corr(signal, direct_ratio, cos_correction, full_hemi_cos_error):
        Fhcorr = (1 - full_hemi_cos_error / 100)
        return (direct_ratio * signal * cos_correction) + ((1 - direct_ratio) * signal * Fhcorr)

    @staticmethod
    def cos_corr_fun(avg_coserror, zenith_ang, sol_zen):
        ind_closest_zen = np.argmin(np.abs(zenith_ang - sol_zen))
        return 1 - avg_coserror[:, ind_closest_zen]/100

    @staticmethod
    def cosine_error_correction(uncGrp, sensortype):

        ## Angular cosine correction (for Irradiance)
        radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
        coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:,2:]
        coserror_90 = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
        coserror_unc = (np.asarray(
            pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:,2:]/100)*coserror
        coserror_90_unc = (np.asarray(
            pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:, 2:]/100)*coserror_90
        zenith_ang = uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
        i1 = np.argmin(np.abs(radcal_wvl - 300))
        i2 = np.argmin(np.abs(radcal_wvl - 1000))
        zenith_ang = np.asarray([float(x) for x in zenith_ang])

        # comparing cos_error for 2 azimuth
        AZI_delta_err = np.abs(coserror - coserror_90)

        # if delta < 2% : averaging the 2 azimuth plan
        AZI_avg_coserror = (coserror + coserror_90)/2.
        AZI_delta = np.power(np.power(coserror_unc, 2) + np.power(coserror_90_unc, 2), 0.5)  # TODO: check this!

        # comparing cos_error for symetric zenith
        ZEN_delta_err = np.abs(AZI_avg_coserror - AZI_avg_coserror[:, ::-1])
        ZEN_delta = np.power(np.power(AZI_delta, 2) + np.power(AZI_delta[:, ::-1], 2), 0.5)

        # if delta < 2% : averaging symetric zenith
        ZEN_avg_coserror = (AZI_avg_coserror + AZI_avg_coserror[:, ::-1])/2.

        # set coserror to 1 outside range [450,700]
        ZEN_avg_coserror[0:i1, :] = 0
        ZEN_avg_coserror[i2:, :] = 0

        return ZEN_avg_coserror, AZI_avg_coserror, zenith_ang, ZEN_delta_err, ZEN_delta, AZI_delta_err, AZI_delta
