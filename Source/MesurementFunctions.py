class L1BMesurementFunctions:

    def __init__(self):
        pass

    ## General
    @staticmethod
    def S12func(k, S1, S2):
        return ((1 + k)*S1) - (k*S2)

    @staticmethod
    def alphafunc(S1, S12):
        t1 = [Decimal(S1[i]) - Decimal(S12[i]) for i in range(len(S1))]
        t2 = [pow(Decimal(S12[i]), 2) for i in range(len(S12))]
        return np.asarray([float(t1[i]/t2[i]) for i in range(len(t1))])

    @staticmethod
    def dark_Substitution(light, dark):
        return light - dark

    @staticmethod
    def non_linearity_corr(offset_corrected_mesure, alpha):
        linear_corr_mesure = offset_corrected_mesure*(1 - alpha*offset_corrected_mesure)
        return linear_corr_mesure

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
    def absolute_calibration(normalized_mesure, updated_radcal_gain):
        return normalized_mesure/updated_radcal_gain

    @staticmethod
    def thermal_corr(Ct, calibrated_mesure):
        return Ct*calibrated_mesure

    @staticmethod
    def prepare_cos(node, sensortype, level=None):
        """
        read from hdf and prepare inputs for cos_err measurement function
        """
        ## Angular cosine correction (for Irradiance)
        if level != 'L2':
            unc_grp = node.getGroup('RAW_UNCERTAINTIES')
            radcal_wvl = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
            coserror = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:, 2:]
            cos_unc = (np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:, 2:]
                       /100)*coserror

            coserror_90 = np.asarray(
                pd.DataFrame(unc_grp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
            cos90_unc = (np.asarray(
                pd.DataFrame(unc_grp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:,
                         2:]/100)*coserror_90
        else:
            # reading in data changes if at L2 (because hdf files have different layout)
            unc_grp = node.getGroup('UNCERTAINTY_BUDGET')
            radcal_wvl = np.asarray(
                pd.DataFrame(unc_grp.getDataset(sensortype + "_RADCAL_CAL").data).transpose()[1][1:].tolist())

            coserror = np.asarray(pd.DataFrame(unc_grp.getDataset(sensortype + "_ANGDATA_COSERROR").data)).transpose()[
                       1:, 2:]
            cos_unc = (np.asarray(
                pd.DataFrame(unc_grp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data)).transpose()[1:, 2:]
                       /100)*coserror

            coserror_90 = np.asarray(
                pd.DataFrame(unc_grp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data)).transpose()[1:, 2:]
            cos90_unc = (np.asarray(
                pd.DataFrame(unc_grp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data)).transpose()[1:, 2:]
                         /100)*coserror_90

        radcal_unc = None  # no uncertainty in the wavelengths as they are only used to index

        zenith_ang = unc_grp.getDataset(sensortype + "_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
        zenith_ang = np.asarray([float(x) for x in zenith_ang])
        zen_unc = np.asarray([0.05 for x in zenith_ang])  # default of 0.5 for solar zenith unc

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

        full_hemi_coserror = np.zeros(255)

        for i in range(255):
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
    def cos_corr_fun(avg_coserror, zenith_ang, sol_zen):
        ind_closest_zen = np.argmin(np.abs(zenith_ang - sol_zen))
        return 1 - avg_coserror[:, ind_closest_zen]/100

    ## HyperOCR Specific
    @staticmethod
    def DATA1(data, alpha):
        return data*(1 - alpha*data)

    @staticmethod
    def DATA3(data2, cal_int, int_time, updated_radcal_gain):
        return data2*(cal_int/int_time[n])/updated_radcal_gain

    @staticmethod
    def DATA4(data3, Ct):
        data4 = data3*Ct
        data4[data4 <= 0] = 0
        return data4

    @staticmethod
    def DATA5(data4, solar_zenith, direct_ratio, zenith_ang, avg_coserror, full_hemi_coserror):
        ind_closest_zen = np.argmin(np.abs(zenith_ang - solar_zenith))
        cos_corr = (1 - avg_coserror[:, ind_closest_zen]/100)[ind_nocal == False]
        Fhcorr = (1 - full_hemi_coserror/100)[ind_nocal == False]
        return (direct_ratio*data4*cos_corr) + ((1 - direct_ratio)*data4*Fhcorr)

    @staticmethod
    def Hyper_update_cal_data_ES(S12_sl_corr, LAMP, cal_int, t1):
        return (S12_sl_corr/LAMP)*(10*cal_int/t1)

    @staticmethod
    def Hyper_update_cal_data_rad(S12_sl_corr, LAMP, PANEL, cal_int, t1):
        return (np.pi*S12_sl_corr)/(LAMP*PANEL)*(10*cal_int/t1)

    @staticmethod
    def Hyper_Therm_Correction(therm_coeff, InternalTemp, refTemp):
        ThermCorr = []
        for i in range(len(therm_coeff)):
            try:
                ThermCorr.append(1 + (therm_coeff[i]*(InternalTemp - refTemp)))

            except IndexError:
                ThermCorr.append(1.0)

        return ThermCorr

    ## TriOS Specific
    @staticmethod
    def back_Mesure(B0, B1, int_time, t0):
        return B0 + B1*(int_time/t0)

    @staticmethod
    def TriOS_update_cal_data_ES(S12_sl_corr, LAMP, int_time_t0, t1):
        updated_radcal_gain = (S12_sl_corr/LAMP)*(int_time_t0/t1)
        # sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = (updated_radcal_gain <= 1e-2)
        ind_nan = np.isnan(updated_radcal_gain)
        ind_nocal = ind_nan | ind_zero
        updated_radcal_gain[ind_nocal == True] = 1  # set 1 instead of 0 to perform calibration (otherwise division per 0)
        return updated_radcal_gain

    @staticmethod
    def TriOS_update_cal_data_rad(PANEL, S12_sl_corr, LAMP, int_time_t0, t1):
        updated_radcal_gain = (np.pi*S12_sl_corr)/(LAMP*PANEL)*(int_time_t0/t1)

        # sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = (updated_radcal_gain <= 1e-2)
        ind_nan = np.isnan(updated_radcal_gain)
        ind_nocal = ind_nan | ind_zero
        updated_radcal_gain[
            ind_nocal == True] = 1  # set 1 instead of 0 to perform calibration (otherwise division per 0)
        return updated_radcal_gain

    @staticmethod
    def Trios_Therm_Correction(therm_coeff, InternalTemp, ambTemp, refTemp):
        ThermCorr = []
        for i in range(len(therm_coeff)):
            try:
                ThermCorr.append(1 + (therm_coeff[i]*(InternalTemp + ambTemp + 5 - refTemp)))

            except IndexError:
                ThermCorr.append(1.0)

        return ThermCorr
