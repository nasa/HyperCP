# import python packages
import os
import numpy as np
import scipy as sp
import pandas as pd
import collections
from decimal import Decimal

# NPL packages
import punpy
import comet_maths as cm

# HCP files
import Utilities
from Source.ConfigFile import ConfigFile
from ProcessL1b import ProcessL1b
from ProcessL1b_Interp import ProcessL1b_Interp
from Uncertainty_Analysis import Propagate


class Instrument:
    """Base class for instrument uncertainty analysis"""

    def __init__(self):
        pass

    @staticmethod
    def lightDarkStats(grp, sensortype):
        pass

    def generateSensorStats(self, rawGroups, newWaveBands):
        output = {}
        # Start = {}
        # End = {}
        types = ['ES', 'LI', 'LT']
        for sensortype in types:
            output[sensortype] = self.lightDarkStats(rawGroups[sensortype], sensortype)

        #     # generate common wavebands for interpolation
        #     wvls = np.asarray(output[sensortype]['wvl'], dtype=float)
        #     Start[sensortype] = np.ceil(wvls[0])
        #     End[sensortype] = np.floor(wvls[-1])
        #
        # start = max([Start[stype] for stype in types])
        # end = min([End[stype] for stype in types])
        # newWavebands = np.arange(start, end, float(ConfigFile.settings["fL1bInterpInterval"]))

        # interpolate to common wavebands
        for stype in types:
            wvls = np.asarray(output[stype].pop('wvl'), dtype=float)  # get sensor specific wavebands and remove from output
            output[stype]['ave_Light'], _ = self.interp_common_wvls(output[stype]['ave_Light'], wvls,
                                                                    newWaveBands)
            output[stype]['std_Light'], _ = self.interp_common_wvls(output[stype]['std_Light'], wvls,
                                                                    newWaveBands)
            _, output[stype]['std_Signal'] = self.interp_common_wvls(
                                             np.asarray(list(output[stype]['std_Signal'].values())),
                                             np.asarray(list(output[stype]['std_Signal'].keys()), dtype=float),
                                             newWaveBands)
        return output

    ## Branch Processing
    @staticmethod
    def factory():
        pass

    @staticmethod
    def Default(uncGrp, stats):
        # read in uncertainties from HDFRoot and define propagate object
        PropagateL1B = Propagate(M=100, cores=0)

        # define dictionaries for uncertainty components
        Cal = {}
        Coeff = {}
        cPol = {}
        cStray = {}
        Ct = {}
        cLin = {}
        cStab = {}

        # loop through instruments
        for sensor in ["ES", "LI", "LT"]:
            # TODO: Implement Slaper and propagate as error
            straylight = uncGrp.getDataset(f"{sensor}_STRAYDATA_CAL")
            straylight.datasetToColumns()
            cStray[sensor] = np.asarray(list(straylight.data[1]))

            linear = uncGrp.getDataset(sensor + "_NLDATA_CAL")
            linear.datasetToColumns()
            cLin[sensor] = np.asarray(list(linear.data[1]))

            stab = uncGrp.getDataset(sensor + "_STABDATA_CAL")
            stab.datasetToColumns()
            cStab[sensor] = np.asarray(list(stab.data[1]))

            radcal = uncGrp.getDataset(f"{sensor}_RADCAL_CAL")
            radcal.datasetToColumns()
            Coeff[sensor] = np.asarray(list(radcal.data[2]))
            Cal[sensor] = np.asarray(list(radcal.data[3]))

            if sensor == 'ES':
                pol = uncGrp.getDataset("ES_ANGDATA_UNCERTAINTY")
            else:
                pol = uncGrp.getDataset(sensor + "_POLDATA_CAL")
            pol.datasetToColumns()
            cPol[sensor] = np.asarray(list(pol.data[1]))

            # temp uncertainties calculated at L1AQC
            Temp = uncGrp.getDataset(sensor + "_TEMPDATA_CAL")
            Temp.datasetToColumns()
            Ct[sensor] = np.array(
                [Temp.columns[k][-1] for k in Temp.columns])  # last row of temp group has uncertainties

        ones = np.ones(len(Cal['ES']))  # to provide array of 1s with the correct shape

        # create lists containing mean values and their associated uncertainties (list order matters)
        mean_values = [stats['ES']['ave_Light'], ones*stats['ES']['ave_Dark'],
                       stats['LI']['ave_Light'], ones*stats['LI']['ave_Dark'],
                       stats['LT']['ave_Light'], ones*stats['LT']['ave_Dark'],
                       Coeff['ES'], Coeff['LI'], Coeff['LT'],
                       ones, ones, ones,
                       ones, ones, ones,
                       ones, ones, ones,
                       ones, ones, ones,
                       ones, ones, ones]

        uncertainty = [stats['ES']['std_Light'], ones*stats['ES']['std_Dark'],
                       stats['LI']['std_Light'], ones*stats['LI']['std_Dark'],
                       stats['LT']['std_Light'], ones*stats['LT']['std_Dark'],
                       Cal['ES']*Coeff['ES']/100, Cal['LI']*Coeff['LI']/100, Cal['LT']*Coeff['LT']/100,
                       cStab['ES'], cStab['LI'], cStab['LT'],
                       cLin['ES'], cLin['LI'], cLin['LT'],
                       np.array(cStray['ES'])/100, np.array(cStray['LI'])/100, np.array(cStray['LT'])/100,
                       np.array(Ct['ES']), np.array(Ct['LI']), np.array(Ct['LT']),
                       np.array(cPol['LI']), np.array(cPol['LT']), np.array(cPol['ES'])]

        # generate uncertainties using Monte Carlo Propagation (M=100, def line 27)
        ES_unc, LI_unc, LT_unc, ES_rel, LI_rel, LT_rel = PropagateL1B.propagate_Instrument_Uncertainty(mean_values,
                                                                                                       uncertainty)

        # return uncertainties as dictionary to be appended to xSlice
        data_wvl = np.asarray(list(stats['ES']['std_Signal'].keys()))  # get wvls
        return dict(
            esUnc=dict(zip(data_wvl, [[i] for i in ES_rel])),
            # Li_rel will be changed to unc but still be relative uncertainty
            liUnc=dict(zip(data_wvl, [[j] for j in LI_rel])),
            ltUnc=dict(zip(data_wvl, [[k] for k in LT_rel]))
        )

    def FRM(self, node, uncGrp, grps, newWaveBands):
        pass

    ## L2 uncertainty Processing
    @staticmethod
    def rrsHyperDeltaFRM(rhoScalar, rhoVec, rhoDelta, waveSubset, xSlice):
        # organise data
        es = np.asarray([val[0] for val in list(xSlice["es"].values())],
                        dtype=np.float64)  # list comprehension needed as is list of lists
        li = np.asarray([val[0] for val in list(xSlice["li"].values())], dtype=np.float64)
        lt = np.asarray([val[0] for val in list(xSlice["lt"].values())], dtype=np.float64)

        esSampleXSlice = xSlice['esSample']
        liSampleXSlice = xSlice['liSample']
        ltSampleXSlice = xSlice['ltSample']

        if rhoScalar is not None:  # make rho a constant array if scalar
            rho = np.ones(len(waveSubset))*rhoScalar
            # rhoDelta = np.ones(len(waveSubset))*rhoDelta  # make rhoDelta the same shape as other values/Uncertainties
        else:
            rho = rhoVec

        # initialise punpy propagation object
        mdraws = esSampleXSlice.shape[0]  # keep no. of monte carlo draws consistent
        Propagate_L2_FRM = punpy.MCPropagation(mdraws, parallel_cores=1)

        # get sample for rho
        rhoSample = cm.generate_sample(mdraws, rho, rhoDelta*rho, "syst")

        # get AOPs for band convolution and relative uncertainties
        lw = lt - (rho*li)
        rrs = lw/es

        # initialise lists to store uncertainties per replicate

        esSample = np.asarray([[i[0] for i in k.values()] for k in esSampleXSlice])  # recover original shape of samples
        liSample = np.asarray([[i[0] for i in k.values()] for k in liSampleXSlice])
        ltSample = np.asarray([[i[0] for i in k.values()] for k in ltSampleXSlice])

        sample_wavelengths = cm.generate_sample(mdraws, np.array(waveSubset), None,
                                                None)  # no uncertainty in wavelength
        sample_Lw = Propagate_L2_FRM.run_samples(Propagate.Lw_FRM, [ltSample, rhoSample, liSample])
        sample_Rrs = Propagate_L2_FRM.run_samples(Propagate.Rrs_FRM, [ltSample, rhoSample, liSample, esSample])

        output = {}

        if ConfigFile.settings["bL2WeightSentinel3A"]:
            lwBand = Propagate.band_Conv_Sensor_S3A(lw, np.array(waveSubset))
            rrsBand = Propagate.band_Conv_Sensor_S3A(rrs, np.array(waveSubset))

            sample_lw_S3A = Propagate_L2_FRM.run_samples(Propagate.band_Conv_Sensor_S3A, [sample_Lw, sample_wavelengths])
            sample_rrs_S3A = Propagate_L2_FRM.run_samples(Propagate.band_Conv_Sensor_S3A, [sample_Rrs, sample_wavelengths])

            lwDeltaBand = Propagate_L2_FRM.process_samples(None, sample_lw_S3A)
            rrsDeltaBand = Propagate_L2_FRM.process_samples(None, sample_rrs_S3A)

            output["lwDelta_Sentinel3A"] = np.abs((lwDeltaBand*1e10)/(lwBand*1e10))
            output["rrsDelta_Sentinel3A"] = np.abs((rrsDeltaBand*1e10)/(rrsBand*1e10))

        if ConfigFile.settings["bL2WeightSentinel3B"]:
            lwBand = Propagate.band_Conv_Sensor_S3B(lw, np.array(waveSubset))
            rrsBand = Propagate.band_Conv_Sensor_S3B(rrs, np.array(waveSubset))

            sample_lw_S3B = Propagate_L2_FRM.run_samples(Propagate.band_Conv_Sensor_S3B, [sample_Lw, sample_wavelengths])
            sample_rrs_S3B = Propagate_L2_FRM.run_samples(Propagate.band_Conv_Sensor_S3B, [sample_Rrs, sample_wavelengths])

            lwDeltaBand = Propagate_L2_FRM.process_samples(None, sample_lw_S3B)
            rrsDeltaBand = Propagate_L2_FRM.process_samples(None, sample_rrs_S3B)

            output["lwDelta_Sentinel3B"] = np.abs((lwDeltaBand*1e10)/(lwBand*1e10))
            output["rrsDelta_Sentinel3B"] = np.abs((rrsDeltaBand*1e10)/(rrsBand*1e10))

        lwDelta = Propagate_L2_FRM.process_samples(None, sample_Lw)
        rrsDelta = Propagate_L2_FRM.process_samples(None, sample_Rrs)

        output["lwDelta"] = np.abs((lwDelta*1e10)/(lw*1e10))  # multiply by large number to reduce round off error
        output["rrsDelta"] = np.abs((rrsDelta*1e10)/(rrs*1e10))

        return output

    @staticmethod
    def rrsHyperDelta(uncGrp, rhoScalar, rhoVec, rhoDelta, waveSubset, xSlice):
        esXSlice = xSlice['es']
        esXstd = xSlice['esStd']
        liXSlice = xSlice['li']
        liXstd = xSlice['liStd']
        ltXSlice = xSlice['lt']
        ltXstd = xSlice['ltStd']

        if rhoScalar is not None:  # make rho a constant array if scalar
            rho = np.ones(len(waveSubset))*rhoScalar
            rhoDelta = np.ones(len(waveSubset))*rhoDelta
        else:
            rho = rhoVec

        if ConfigFile.settings["bL1bDefaultCal"] == 2:
            esPol = uncGrp.getDataset("ES_POLDATA_CAL").columns
            liPol = uncGrp.getDataset("LI_POLDATA_CAL").columns
            ltPol = uncGrp.getDataset("LT_POLDATA_CAL").columns
            esStray = uncGrp.getDataset("ES_STRAYDATA_CAL").columns
            liStray = uncGrp.getDataset("LI_STRAYDATA_CAL").columns
            ltStray = uncGrp.getDataset("LT_STRAYDATA_CAL").columns
            esNL = uncGrp.getDataset("ES_NLDATA_CAL").columns
            liNL = uncGrp.getDataset("LI_NLDATA_CAL").columns
            ltNL = uncGrp.getDataset("LT_NLDATA_CAL").columns
            esStab = uncGrp.getDataset("ES_STABDATA_CAL").columns
            liStab = uncGrp.getDataset("LI_STABDATA_CAL").columns
            ltStab = uncGrp.getDataset("LT_STABDATA_CAL").columns
            esCtemp = uncGrp.getDataset("ES_TEMPDATA_CAL").columns
            liCtemp = uncGrp.getDataset("LI_TEMPDATA_CAL").columns
            ltCtemp = uncGrp.getDataset("LT_TEMPDATA_CAL").columns
            esCal = uncGrp.getDataset("ES_RADCAL_CAL").columns
            liCal = uncGrp.getDataset("LI_RADCAL_CAL").columns
            ltCal = uncGrp.getDataset("LT_RADCAL_CAL").columns

        elif ConfigFile.settings['bL1bDefaultCal'] == 3:
            esPol = uncGrp.getDataset("ES_ANGDATA_UNCERTAINTY").columns
            liPol = uncGrp.getDataset("LI_POLDATA_CAL").columns
            ltPol = uncGrp.getDataset("LT_POLDATA_CAL").columns
            esStray = uncGrp.getDataset("ES_STRAYDATA_UNCERTAINTY").columns
            liStray = uncGrp.getDataset("LI_STRAYDATA_UNCERTAINTY").columns
            ltStray = uncGrp.getDataset("LT_STRAYDATA_UNCERTAINTY").columns
            esNL = uncGrp.getDataset("ES_NLDATA_CAL").columns
            liNL = uncGrp.getDataset("LI_NLDATA_CAL").columns
            ltNL = uncGrp.getDataset("LT_NLDATA_CAL").columns
            esStab = uncGrp.getDataset("ES_STABDATA_CAL").columns
            liStab = uncGrp.getDataset("LI_STABDATA_CAL").columns
            ltStab = uncGrp.getDataset("LT_STABDATA_CAL").columns
            esCtemp = uncGrp.getDataset("ES_TEMPDATA_CAL").columns
            liCtemp = uncGrp.getDataset("LI_TEMPDATA_CAL").columns
            ltCtemp = uncGrp.getDataset("LT_TEMPDATA_CAL").columns
            esCal = uncGrp.getDataset("ES_RADCAL_CAL").columns
            liCal = uncGrp.getDataset("LI_RADCAL_CAL").columns
            ltCal = uncGrp.getDataset("LT_RADCAL_CAL").columns

        Propagate_L2 = Propagate(M=1000, cores=0)
        slice_size = len(list(esXSlice.keys()))
        ones = np.ones(slice_size)

        # TODO: do with list comprehension for speed
        Lt = np.zeros(slice_size)
        Li = np.zeros(slice_size)
        Es = np.zeros(slice_size)
        EsCal = np.zeros(slice_size)
        LiCal = np.zeros(slice_size)
        LtCal = np.zeros(slice_size)
        EsStab = np.zeros(slice_size)
        LiStab = np.zeros(slice_size)
        LtStab = np.zeros(slice_size)
        EsNL = np.zeros(slice_size)
        LiNL = np.zeros(slice_size)
        LtNL = np.zeros(slice_size)
        EsStray = np.zeros(slice_size)
        LiStray = np.zeros(slice_size)
        LtStray = np.zeros(slice_size)
        EsTemp = np.zeros(slice_size)
        LiTemp = np.zeros(slice_size)
        LtTemp = np.zeros(slice_size)  # convert from dictionaries into numpy arrays
        EsCos = np.zeros(slice_size)
        LiPol = np.zeros(slice_size)
        LtPol = np.zeros(slice_size)

        for i, wvl in enumerate(esCal):
            Lt[i] = ltXSlice[wvl][0]
            Li[i] = liXSlice[wvl][0]
            Es[i] = esXSlice[wvl][0]
            EsCal[i] = esCal[wvl][3]
            LiCal[i] = liCal[wvl][3]
            LtCal[i] = ltCal[wvl][3]
            EsStab[i] = esStab[wvl][1]
            LiStab[i] = liStab[wvl][1]
            LtStab[i] = ltStab[wvl][1]
            EsNL[i] = esNL[wvl][1]
            LiNL[i] = liNL[wvl][1]
            LtNL[i] = ltNL[wvl][1]
            EsStray[i] = esStray[wvl][1]
            LiStray[i] = liStray[wvl][1]
            LtStray[i] = ltStray[wvl][1]
            EsTemp[i] = esCtemp[wvl][4]
            LiTemp[i] = liCtemp[wvl][4]
            LtTemp[i] = ltCtemp[wvl][4]
            EsCos[i] = esPol[wvl][1]
            LiPol[i] = liPol[wvl][1]
            LtPol[i] = ltPol[wvl][1]

        lw_means = [Lt, rho, Li,
                    ones, ones, ones, ones, ones, ones,
                    ones, ones, ones, ones, ones, ones]

        lw_uncertainties = [np.array(list(ltXstd.values())).flatten()*Lt,
                            rhoDelta,
                            np.array(list(liXstd.values())).flatten()*Li,
                            LiCal/100, LtCal/100, LiStab, LtStab, LiNL, LtNL,
                            LiStray/100, LtStray/100, LiTemp, LtTemp, LiPol, LtPol]

        lwDelta, lwAbsUnc, lw_vals = Propagate_L2.Propagate_Lw(lw_means, lw_uncertainties)

        means = [Lt, rho, Li, Es,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones,
                 ones, ones, ones]

        uncertainties = [np.array(list(ltXstd.values())).flatten()*Lt,
                         rhoDelta,
                         np.array(list(liXstd.values())).flatten()*Li,
                         np.array(list(esXstd.values())).flatten()*Es,
                         EsCal/100, LiCal/100, LtCal/100,
                         EsStab, LiStab, LtStab,
                         EsNL, LiNL, LtNL,
                         EsStray/100, LiStray/100, LtStray/100,
                         EsTemp, LiTemp, LtTemp,
                         LiPol, LtPol, EsCos]
        rrsDelta, rrsAbsUnc, rrs_vals = Propagate_L2.Propagate_RRS(means, uncertainties)

        ## BAND CONVOLUTION
        # band convolution of uncertainties is done here to include uncertainty contribution of band convolution process
        Convolve = Propagate(M=100, cores=1)
        # these are absolute values! Dont get confused
        if ConfigFile.settings["bL2WeightSentinel3A"]:
            output["lwDelta_Sentinel3A"] = Convolve.band_Conv_Uncertainty([lw_vals, np.array(waveSubset)], [lwAbsUnc, None], "S3A")
            output["rrsDelta_Sentinel3A"] = Convolve.band_Conv_Uncertainty([rrs_vals, np.array(waveSubset)], [rrsAbsUnc, None], "S3A")
        elif ConfigFile.settings["bL2WeightSentinel3B"]:
            output["lwDelta_Sentinel3B"] = Convolve.band_Conv_Uncertainty([lw_vals, np.array(waveSubset)], [lwAbsUnc, None], "S3B")
            output["rrsDelta_Sentinel3B"] = Convolve.band_Conv_Uncertainty([rrs_vals, np.array(waveSubset)], [rrsAbsUnc, None], "S3B")

        output.update({"lwDelta": lwDelta, "rrsDelta": rrsDelta})

        return output

    ## Utilties
    @staticmethod
    def interp_common_wvls(columns, waves, newWavebands):
        saveTimetag2 = None
        if "Datetag" in columns:
            saveDatetag = columns.pop("Datetag")
            saveTimetag2 = columns.pop("Timetag2")
            columns.pop("Datetime")

        # Get wavelength values

        x = np.asarray(waves)

        newColumns = collections.OrderedDict()
        if saveTimetag2 is not None:
            newColumns["Datetag"] = saveDatetag
            newColumns["Timetag2"] = saveTimetag2
        # Can leave Datetime off at this point

        for i in range(newWavebands.shape[0]):
            newColumns[str(round(10*newWavebands[i])/10)] = []  # limit to one decimal place

        new_y = sp.interpolate.InterpolatedUnivariateSpline(x, columns, k=3)(newWavebands)

        for waveIndex in range(newWavebands.shape[0]):
            newColumns[str(round(10*newWavebands[waveIndex])/10)].append(new_y[waveIndex])

        return new_y, newColumns

    @staticmethod
    def interpolateSamples(Columns, waves, newWavebands):
        ''' Wavelength Interpolation for differently sized arrays containing samples
                    Use a common waveband set determined by the maximum lowest wavelength
                    of all sensors, the minimum highest wavelength, and the interval
                    set in the Configuration Window.
                    '''

        # Copy dataset to dictionary
        columns = {k: Columns[:, i] for i, k in enumerate(waves)}
        cols = []
        for m in range(Columns.shape[0]):  # across all the monte carlo draws
            newColumns = {}

            for i in range(newWavebands.shape[0]):
                # limit to one decimal place
                newColumns[str(round(10*newWavebands[i])/10)] = []

            # for m in range(Columns.shape[0]):
            # Perform interpolation for each timestamp
            y = np.asarray([columns[k][m] for k in columns])

            for waveIndex in range(newWavebands.shape[0]):
                newColumns[str(round(10*newWavebands[waveIndex])/10)].append(y[waveIndex])

            cols.append(newColumns)

        return np.asarray(cols)

    # Measurement Functions
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
    def prepare_cos(uncGrp, sensortype, level=None):
        """
        read from hdf and prepare inputs for cos_err measurement function
        """
        ## Angular cosine correction (for Irradiance)
        if level != 'L2':
            radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
            coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:, 2:]
            cos_unc = (np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:, 2:]
                       /100)*coserror

            coserror_90 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
            cos90_unc = (np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:,
                         2:]/100)*coserror_90
        else:
            # reading in data changes if at L2 (because hdf files have different layout)
            radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())
            coserror = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").data))[1:, 2:]
            cos_unc = (np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY").data))[1:, 2:]/100)*coserror

            coserror_90 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR_AZ90").data))[1:, 2:]
            cos90_unc = (np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_ANGDATA_UNCERTAINTY_AZ90").data))[1:, 2:]/100)*coserror_90

        radcal_unc = None  # no uncertainty in the wavelengths as they are only used to index

        zenith_ang = uncGrp.getDataset(sensortype + "_ANGDATA_COSERROR").attributes["COLUMN_NAMES"].split('\t')[2:]
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
        AZI_delta = np.power(np.power(coserror_unc, 2) + np.power(coserror_90_unc, 2), 0.5)

        # comparing cos_error for symetric zenith
        ZEN_delta_err = np.abs(AZI_avg_coserror - AZI_avg_coserror[:, ::-1])
        ZEN_delta = np.power(np.power(AZI_delta, 2) + np.power(AZI_delta[:, ::-1], 2), 0.5)

        # if delta < 2% : averaging symetric zenith
        ZEN_avg_coserror = (AZI_avg_coserror + AZI_avg_coserror[:, ::-1])/2.

        # set coserror to 1 outside range [450,700]
        ZEN_avg_coserror[0:i1, :] = 0
        ZEN_avg_coserror[i2:, :] = 0

        return ZEN_avg_coserror, AZI_avg_coserror, zenith_ang, ZEN_delta_err, ZEN_delta, AZI_delta_err, AZI_delta


class HyperOCR(Instrument):
    def __init__(self):
        super().__init__()
        self.instrument = "HyperOCR"

    @staticmethod
    def _check_data(dark, light):
        msg = None
        if (dark is None) or (light is None):
            msg = f'Dark Correction, dataset not found: {dark} , {light}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        if Utilities.hasNan(light):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'

        if Utilities.hasNan(dark):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'
        if msg:
            print(msg)
            Utilities.writeLogFile(msg)
        return True

    @staticmethod
    def _interp(lightData, lightTimer, darkData, darkTimer):
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

        if Utilities.hasNan(darkData):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'
            print(msg)
            Utilities.writeLogFile(msg)
            exit()

        return darkData.data

    @staticmethod
    def lightDarkStats(node, sensortype):
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensortype):
                darkGroup = gp
                darkData = gp.getDataset(sensortype)
                darkDateTime = gp.getDataset("DATETIME")

            if gp.attributes["FrameType"] == "ShutterLight" and gp.getDataset(sensortype):
                lightGroup = gp
                lightData = gp.getDataset(sensortype)
                lightDateTime = gp.getDataset("DATETIME")

        if darkGroup is None or lightGroup is None:
            msg = f'No radiometry found for {sensortype}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        elif not self._check_data(darkData, lightData):
            return False
        if not(newDarkData := self._interp(lightData, lightDateTime, darkData, darkDateTime)):
            return False

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
            std_Light.append(np.std(lightData.data[k])/pow(N, 0.5))  # = (sigma / sqrt(N))**2 or sigma**2
            std_Dark.append(np.std(newDarkData[k])/pow(Nd, 0.5))  # sigma here is essentially sigma**2 so N must be rooted
            ave_Light.append(np.average(lightData.data[k]))
            ave_Dark.append(np.average(darkData.data[k]))

            for x in range(lightData.data.shape[0]):
                lightData.data[k][x] -= newDarkData[k][x]

            # Normalised signal standard deviation =
            signalAve = np.average(lightData.data[k])
            stdevSignal[k1] = pow((pow(std_Light[-1], 2) + pow(std_Dark[-1], 2))/pow(signalAve, 2), 0.5)

            # sensitivity factor : if raw_cal==0 (or NaN), no calibration is performed and data is affected to 0
            ind_zero = np.array([rc[0] == 0 for rc in raw_cal])  # changed due to raw_cal now being a np array
            ind_nan = np.array([np.isnan(rc[0]) for rc in raw_cal])
            ind_nocal = ind_nan | ind_zero

        return dict(
            ave_Light=np.array(ave_Light),
            ave_Dark=np.array(ave_Dark),
            std_Light=np.array(std_Light),
            std_Dark=np.array(std_Dark),
            std_Signal=stdevSignal,
            wvl=wvl[ind_nocal==False]
            )

    def FRM(self, node, uncGrp, grps, newWaveBands):
        # calibration of HyperOCR following the FRM processing of FRM4SOC2
        output = {}
        # Start = {}
        # End = {}
        for sensortype in ['ES', 'LI', 'LT']:
            print('FRM Processing:', sensortype)
            # Read data
            grp = node.getGroup(sensortype)

            # read in data for FRM processing
            raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())
            int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())

            # Read FRM characterisation
            radcal_wvl = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data).transpose()[1][1:].tolist())
            radcal_cal = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data).transpose()[2]
            dark = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data).transpose()[4][
                1:].tolist())  # dark signal
            S1 = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data).transpose()[6]
            S1_unc = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data).transpose()[7]/100
            S2 = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data).transpose()[8]
            S2_unc = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data).transpose()[9]/100
            mZ = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_STRAYDATA_LSF").data))
            mZ_unc = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_STRAYDATA_UNCERTAINTY").data))

            # remove 1st line and column, we work on 255 pixel not 256.
            mZ = mZ[1:, 1:]
            mZ_unc = mZ_unc[1:, 1:]

            Ct = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_TEMPDATA_CAL").data).transpose()[4][1:].tolist())
            Ct_unc = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_TEMPDATA_CAL").data).transpose()[5][1:].tolist())
            LAMP = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_LAMP").data).transpose()[2])
            LAMP_unc = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_LAMP").data).transpose()[3])/100*LAMP

            # Defined constants
            nband = len(radcal_wvl)
            nmes = len(raw_data)
            n_iter = 5

            # set up uncertainty propagation
            mDraws = 100  # number of monte carlo draws
            prop = punpy.MCPropagation(mDraws, parallel_cores=1)

            # uncertainties from data:
            sample_mZ = cm.generate_sample(mDraws, mZ, mZ_unc, "rand")
            sample_n_iter = cm.generate_sample(mDraws, n_iter, None, None, dtype=int)
            sample_Ct = cm.generate_sample(mDraws, Ct, Ct_unc, "syst")

            LAMP = np.pad(LAMP, (0, nband - len(LAMP)), mode='constant')  # PAD with zero if not 255 long
            LAMP_unc = np.pad(LAMP_unc, (0, nband - len(LAMP_unc)), mode='constant')
            sample_LAMP = cm.generate_sample(mDraws, LAMP, LAMP_unc, "syst")

            # Non-linearity alpha computation
            cal_int = radcal_cal.pop(0)
            sample_cal_int = cm.generate_sample(100, cal_int, None, None)
            t1 = S1.pop(0)
            t2 = S2.pop(0)

            sample_t1 = cm.generate_sample(mDraws, t1, None, None)
            sample_S1 = cm.generate_sample(mDraws, np.asarray(S1), S1_unc[1:], "rand")
            sample_S2 = cm.generate_sample(mDraws, np.asarray(S2), S2_unc[1:], "rand")

            k = t1/(t2 - t1)
            sample_k = cm.generate_sample(mDraws, k, None, None)
            S12 = self.S12func(k, S1, S2)
            sample_S12 = prop.run_samples(self.S12func, [sample_k, sample_S1, sample_S2])

            S12_sl_corr = self.Slaper_SL_correction(S12, mZ, n_iter=5)
            S12_sl_corr_unc = []
            sl4 = self.Slaper_SL_correction(S12, mZ, n_iter=4)
            for i in range(len(S12_sl_corr)):  # get the difference between n=4 and n=5
                if S12_sl_corr[i] > sl4[i]:
                    S12_sl_corr_unc.append(S12_sl_corr[i] - sl4[i])
                else:
                    S12_sl_corr_unc.append(sl4[i] - S12_sl_corr[i])

            sample_S12_sl_syst = cm.generate_sample(mDraws, S12_sl_corr, np.array(S12_sl_corr_unc), "syst")
            sample_S12_sl_rand = prop.run_samples(self.Slaper_SL_correction, [sample_S12, sample_mZ, sample_n_iter])
            sample_S12_sl_corr = prop.combine_samples([sample_S12_sl_syst, sample_S12_sl_rand])

            # alpha = ((S1-S12)/(S12**2)).tolist()
            alpha = self.alphafunc(S1, S12)
            sample_alpha = prop.run_samples(self.alphafunc, [sample_S1, sample_S12])

            # Updated calibration gain
            if sensortype == "ES":
                ## Compute avg cosine error
                avg_coserror, avg_azi_coserror, zenith_ang, zen_delta, azi_delta, zen_unc, azi_unc = \
                    self.cosine_error_correction(node, sensortype)

                # error due to lack of symmetry in cosine response
                sample_azi_delta_err1 = cm.generate_sample(mDraws, avg_azi_coserror, azi_unc, "syst")
                sample_azi_delta_err2 = cm.generate_sample(mDraws, avg_azi_coserror, azi_delta, "syst")
                sample_azi_delta_err = prop.combine_samples([sample_azi_delta_err1, sample_azi_delta_err2])
                sample_azi_err = prop.run_samples(self.AZAvg_Coserr, [sample_coserr, sample_coserr90])
                sample_azi_avg_coserror = prop.combine_samples([sample_azi_err, sample_azi_delta_err])

                sample_zen_delta_err1 = cm.generate_sample(mDraws, avg_coserror, zen_unc, "syst")
                sample_zen_delta_err2 = cm.generate_sample(mDraws, avg_coserror, zen_delta, "syst")
                sample_zen_delta_err = prop.combine_samples([sample_zen_delta_err1, sample_zen_delta_err2])
                sample_zen_err = prop.run_samples(self.ZENAvg_Coserr, [sample_radcal_wvl, sample_azi_avg_coserror])
                sample_zen_avg_coserror = prop.combine_samples([sample_zen_err, sample_zen_delta_err])

                sample_fhemi_coserr = prop.run_samples(self.FHemi_Coserr, [sample_zen_avg_coserror, sample_zen_ang])

                ## Irradiance direct and diffuse ratio
                # res_py6s = ProcessL1b.get_direct_irradiance_ratio(node, sensortype, trios=0)

                updated_radcal_gain = Hyper_update_cal_data_ES(S12_sl_corr, LAMP, cal_int, t1)
                sample_updated_radcal_gain = prop.run_samples(Hyper_update_cal_data_ES,
                                                              [sample_S12_sl_corr, sample_LAMP, sample_cal_int,
                                                               sample_t1])
            else:
                PANEL = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_PANEL").data).transpose()[2])
                PANEL_unc = (np.asarray(
                    pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_PANEL").data).transpose()[3])/100)*PANEL
                PANEL = np.pad(PANEL, (0, nband - len(PANEL)), mode='constant')
                PANEL_unc = np.pad(PANEL_unc, (0, nband - len(PANEL_unc)), mode='constant')
                sample_PANEL = cm.generate_sample(100, PANEL, PANEL_unc, "syst")
                updated_radcal_gain = Hyper_update_cal_data_rad(S12_sl_corr, LAMP, PANEL, cal_int, t1)
                sample_updated_radcal_gain = prop.run_samples(Hyper_update_cal_data_rad,
                                                              [sample_S12_sl_corr, sample_LAMP, sample_PANEL,
                                                               sample_cal_int,
                                                               sample_t1])

            ## sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
            ind_zero = radcal_cal <= 0
            ind_nan = np.isnan(radcal_cal)
            ind_nocal = ind_nan | ind_zero
            # set 1 instead of 0 to perform calibration (otherwise division per 0)
            updated_radcal_gain[ind_nocal == True] = 1

            # keep only defined wavelength
            updated_radcal_gain = updated_radcal_gain[ind_nocal == False]
            wvl = radcal_wvl[ind_nocal == False]
            dark = dark[ind_nocal == False]
            alpha = np.asarray(alpha)[ind_nocal == False]
            mZ = mZ[:, ind_nocal == False]
            mZ = mZ[ind_nocal == False, :]
            Ct = np.asarray(Ct)[ind_nocal == False]

            FRM_mesure = np.zeros((nmes, len(updated_radcal_gain)))

            ind_raw_data = (radcal_cal[radcal_wvl > 0]) > 0
            for n in range(nmes):
                # dark substraction
                data = raw_data[n][ind_raw_data] - dark

                # signal uncertainties
                std_light = np.std(raw_data[n][ind_raw_data], axis=0)
                std_dark = np.std(dark, axis=0)
                sample_light = cm.generate_sample(100, raw_data[n][ind_raw_data], std_light, "rand")
                sample_dark = cm.generate_sample(100, dark, std_dark, "rand")
                sample_dark_corr_data = prop.run_samples(self.dark_Substitution, [sample_light, sample_dark])

                # Non-linearity
                data1 = data*(1 - alpha*data)
                sample_data1 = prop.run_samples(DATA1, [sample_dark_corr_data, sample_alpha])

                # Straylight
                data2 = self.Slaper_SL_correction(data1, mZ, n_iter)

                S12_sl_corr_unc = []
                sl4 = self.Slaper_SL_correction(linear_corr_mesure, mZ, n_iter=4)
                for i in range(len(straylight_corr_mesure)):  # get the difference between n=4 and n=5
                    if linear_corr_mesure[i] > sl4[i]:
                        S12_sl_corr_unc.append(straylight_corr_mesure[i] - sl4[i])
                    else:
                        S12_sl_corr_unc.append(sl4[i] - straylight_corr_mesure[i])

                sample_straylight_1 = cm.generate_sample(mDraws, sample_data1, np.array(S12_sl_corr_unc), "syst")
                sample_straylight_2 = prop.run_samples(self.Slaper_SL_correction,
                                                       [sample_linear_corr_mesure, sample_mZ, sample_n_iter])
                sample_data2 = prop.combine_samples([sample_straylight_1, sample_straylight_2])

                # Calibration
                data3 = data2*(cal_int/int_time[n])/updated_radcal_gain
                sample_data3 = prop.combine_samples(DATA3, [sample_data2, sample_cal_int, sample_int_time,
                                                            sample_updated_radcal_gain])

                # thermal
                data4 = DATA4(data3, Ct)
                sample_data4 = prop.combine_samples(DATA4, [sample_data3, sample_Ct])

                # Cosine correction
                if sensortype == "ES":
                    solar_zenith = np.array([46.87415726])
                    direct_ratio = np.array([0.222, 0.245, 0.256, 0.268, 0.279, 0.302, 0.313, 0.335, 0.345, 0.356,
                                             0.376, 0.386, 0.396, 0.415, 0.424, 0.433, 0.45, 0.459, 0.467, 0.482,
                                             0.489, 0.496, 0.51, 0.516, 0.522, 0.534, 0.539, 0.545, 0.555, 0.56,
                                             0.565, 0.576, 0.581, 0.586, 0.596, 0.6, 0.605, 0.613, 0.617, 0.621,
                                             0.629, 0.632, 0.636, 0.644, 0.647, 0.651, 0.657, 0.66, 0.663, 0.669,
                                             0.672, 0.675, 0.68, 0.683, 0.686, 0.691, 0.693, 0.696, 0.7, 0.702,
                                             0.705, 0.709, 0.711, 0.714, 0.717, 0.719, 0.721, 0.725, 0.726, 0.728,
                                             0.731, 0.733, 0.736, 0.738, 0.739, 0.742, 0.744, 0.745, 0.748, 0.749,
                                             0.75, 0.753, 0.754, 0.755, 0.757, 0.758, 0.759, 0.761, 0.763, 0.764,
                                             0.766, 0.767, 0.768, 0.769, 0.77, 0.771, 0.773, 0.774, 0.775, 0.776,
                                             0.777, 0.778, 0.779, 0.78, 0.781, 0.782, 0.783, 0.784, 0.785, 0.7855,
                                             0.786, 0.788, 0.788, 0.789, 0.79, 0.79, 0.791, 0.792, 0.793, 0.793,
                                             0.795, 0.795, 0.796, 0.797, 0.797, 0.798, 0.799, 0.799, 0.8, 0.801,
                                             0.801, 0.802, 0.802, 0.803, 0.803, 0.804, 0.805, 0.805, 0.806, 0.806,
                                             0.807, 0.807, 0.808, 0.808, 0.809, 0.809, 0.81, 0.81, 0.811, 0.811,
                                             0.811, 0.812, 0.812, 0.813, 0.813, 0.814, 0.814, 0.814, 0.815, 0.815,
                                             0.816, 0.816, 0.816, 0.817, 0.817, 0.817, 0.818, 0.818, 0.818, 0.819,
                                             0.819, 0.819, 0.819, 0.82, 0.82, 0.821, 0.821, 0.821, 0.822, 0.822,
                                             0.822, 0.822, 0.823, 0.823, 0.823, 0.824, 0.824, 0.824, 0.824, 0.825,
                                             0.825, 0.825, 0.826, 0.826, 0.826, 0.826, 0.827, 0.827, 0.827, 0.827,
                                             0.828, 0.828, 0.828, 0.828, 0.828, 0.829, 0.829, 0.829, 0.829, 0.83,
                                             0.83, 0.83, 0.83, 0.83, 0.83, 0.831, 0.831, 0.831, 0.831, 0.831,
                                             0.832, 0.832, 0.832, 0.832, 0.832, 0.832, 0.833, 0.833, 0.833, 0.833,
                                             0.833, 0.833, 0.834, 0.834, 0.834, 0.834, 0.834, 0.834, 0.834, 0.835,
                                             0.835, 0.835, 0.835, 0.835, 0.835, 0.835, 0.836, 0.836, 0.836, 0.836,
                                             0.836, 0.836, 0.836, 0.836, 0.837])
                    data5 = DATA5(data4, solar_zenith, direct_ratio, zenith_ang, avg_coserror, full_hemi_coserror)
                    # data5 = DATA5(data4, res_py6s['solar_zenith'], res_py6s['direct_ratio'][ind_raw_data], zenith_ang,
                    #               avg_coserror, full_hemi_coserror)
                    sample_data5 = prop.run_samples(DATA5, [data4, solar_zenith, direct_ratio, zenith_ang, avg_coserror,
                                                            full_hemi_coserror])
                    unc = prop.process_samples(None, sample_data5)
                    sample = sample_data5
                    FRM_mesure[n, :] = data5
                else:
                    unc = prop.process_samples(None, sample_data4)
                    sample = sample_data4
                    FRM_mesure[n, :] = data4

                # mask for arrays
                ind_zero = np.array([rc[0] == 0 for rc in raw_cal])  # changed due to raw_cal now being a np array
                ind_nan = np.array([np.isnan(rc[0]) for rc in raw_cal])
                ind_nocal = ind_nan | ind_zero

                # Remove wvl without calibration from the dataset and make uncertainties relative
                filtered_mesure = FRM_mesure[ind_nocal == False]
                filtered_unc = np.power(np.power(unc[ind_nocal == False]*1e10, 2)/np.power(filtered_mesure*1e10, 2),
                                        0.5)

                output[f"{sensortype.lower()}Wvls"] = radcal_wvl[ind_nocal == False]
                output[f"{sensortype.lower()}Unc"] = filtered_unc  # relative uncertainty
                output[f"{sensortype.lower()}Sample"] = sample[:, ind_nocal == False]  # samples keep raw

            #     # generate common wavebands for interpolation
            #     wvls = radcal_wvl[ind_nocal == False]
            #     Start[sensortype] = np.ceil(wvls[0])
            #     End[sensortype] = np.floor(wvls[-1])
            #
            # types = ['ES', 'LI', 'LT']
            # # interpolate to common wavebands
            # start = max([Start[stype] for stype in types])
            # end = min([End[stype] for stype in types])
            # newWavebands = np.arange(start, end, float(ConfigFile.settings["fL1bInterpInterval"]))

            for sensortype in types:
                # get sensor specific wavebands - # output[f"{sensortype.lower()}Wvls"]
                wvls = np.asarray(output[f"{sensortype.lower()}Wvls"].pop('Wvls'), dtype=float)
                _, output[f"{sensortype.lower()}Unc"] = self.interp_common_wvls(
                    output[f"{sensortype.lower()}Unc"], wvls, newWaveBands)
                output[f"{sensortype.lower()}Sample"] = self.interpolateSamples(
                    output[f"{sensortype.lower()}Sample"], wvls, newWaveBands)

        return output

    # Measurement Functions
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
    def update_cal_data_ES(S12_sl_corr, LAMP, cal_int, t1):
        return (S12_sl_corr/LAMP)*(10*cal_int/t1)

    @staticmethod
    def update_cal_data_rad(S12_sl_corr, LAMP, PANEL, cal_int, t1):
        return (np.pi*S12_sl_corr)/(LAMP*PANEL)*(10*cal_int/t1)


class Trios(Instrument):
    def __init__(self):
        super().__init__()

    @staticmethod
    def lightDarkStats(grp, sensortype):
        raw_cal = grp.getDataset(f"CAL_{sensortype}").data
        raw_back = grp.getDataset(f"BACK_{sensortype}").data
        raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())

        raw_wvl = np.array(pd.DataFrame(grp.getDataset(sensortype).data).columns)
        int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
        DarkPixelStart = int(grp.attributes["DarkPixelStart"])
        DarkPixelStop = int(grp.attributes["DarkPixelStop"])
        int_time_t0 = int(grp.getDataset(f"BACK_{sensortype}").attributes["IntegrationTime"])

        # sensitivity factor : if raw_cal==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = np.array([rc[0] == 0 for rc in raw_cal])  # changed due to raw_cal now being a np array
        ind_nan = np.array([np.isnan(rc[0]) for rc in raw_cal])
        ind_nocal = ind_nan | ind_zero
        raw_cal = np.array([rc[0] for rc in raw_cal])
        raw_cal[ind_nocal==True] = 1

        # if ConfigFile.settings["bL1bCal"] > 2:  # for some reason FRM branch keeps everything in a tuple
        #     raw_back = np.array([[rb[0][0] for rb in raw_back], [rb[1][0] for rb in raw_back]]).transpose()
        # else:

        # slice raw_back to remove indexes where raw_cal is 0 or "NaN"
        raw_back = np.array([[rb[0] for rb in raw_back], [rb[1] for rb in raw_back]]).transpose()

        # check size of data
        nband = len(raw_back)  # indexes changed for raw_back as is brought to L2
        nmes = len(raw_data)
        if nband != len(raw_data[0]):
            print("ERROR: different number of pixels between dat and back")
            exit()

        # Data conversion
        mesure = raw_data/65365.0
        calibrated_mesure = np.zeros((nmes, nband))
        back_mesure = np.zeros((nmes, nband))

        for n in range(nmes):
            # Background correction : B0 and B1 read from "back data"
            back_mesure[n, :] = raw_back[:, 0] + raw_back[:, 1]*(int_time[n]/int_time_t0)
            back_corrected_mesure = mesure[n] - back_mesure[n, :]

            # Offset substraction : dark index read from attribute
            offset = np.mean(back_corrected_mesure[DarkPixelStart:DarkPixelStop])
            offset_corrected_mesure = back_corrected_mesure - offset

            # Normalization for integration time
            normalized_mesure = offset_corrected_mesure*int_time_t0/int_time[n]

            # Sensitivity calibration
            calibrated_mesure[n, :] = normalized_mesure/raw_cal

        # get light and dark data before correction
        light_avg = np.mean(mesure, axis=0)[ind_nocal == False]
        light_std = np.std(mesure, axis=0)[ind_nocal == False]
        dark_avg = offset
        dark_std = np.std(back_corrected_mesure[DarkPixelStart:DarkPixelStop], axis=0)

        filtered_mesure = calibrated_mesure[:, ind_nocal == False]

        # back_avg = np.mean(back_mesure, axis=0)
        # back_std = np.std(back_mesure, axis=0)

        stdevSignal = {}
        for i, wvl in enumerate(raw_wvl[ind_nocal == False]):
            stdevSignal[wvl] = pow(
                (pow(light_std[i], 2) + pow(dark_std, 2))/pow(np.average(filtered_mesure, axis=0)[i], 2), 0.5)

        return dict(
            ave_Light=np.array(light_avg),
            ave_Dark=np.array(dark_avg),
            std_Light=np.array(light_std),
            std_Dark=np.array(dark_std),
            std_Signal=stdevSignal,
            wvl=raw_wvl[ind_nocal == False]
        )

    def FRM(self, node, uncGrp, grps, newWaveBands):
        output = {}
        # Start = {}
        # End = {}
        for sensortype in ['ES', 'LI', 'LT']:

            ### Read HDF file inputs
            grp = grps[sensortype]

            # read data for L1B FRM processing
            raw_data = np.asarray(grp.getDataset(sensortype).data.tolist())
            DarkPixelStart = int(grp.attributes["DarkPixelStart"])
            DarkPixelStop = int(grp.attributes["DarkPixelStop"])
            int_time = np.asarray(grp.getDataset("INTTIME").data.tolist())
            int_time_t0 = int(grp.getDataset("BACK_" + sensortype).attributes["IntegrationTime"])

            ### Read full characterisation files
            radcal_wvl = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['1'][1:].tolist())

            ### for masking arrays only
            raw_cal = grp.getDataset(f"CAL_{sensortype}").data

            B0 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['4'][1:].tolist())
            B1 = np.asarray(
                pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['5'][1:].tolist())
            S1 = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['6']
            S2 = pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['8']
            mZ = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_STRAYDATA_LSF").data))
            mZ_unc = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_STRAYDATA_UNCERTAINTY").data))
            mZ = mZ[1:, 1:]  # remove 1st line and column, we work on 255 pixel not 256.
            mZ_unc = mZ_unc[1:, 1:]  # remove 1st line and column, we work on 255 pixel not 256.
            Ct = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_TEMPDATA_CAL").data[1:].transpose().tolist())[4])
            Ct_unc = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_TEMPDATA_CAL").data[1:].transpose().tolist())[5])
            LAMP = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_LAMP").data)['2'])
            LAMP_unc = (np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_LAMP").data)['3'])/100)*LAMP

            # Defined constants
            nband = len(B0)
            nmes = len(raw_data)
            grp.attributes["nmes"] = nmes
            n_iter = 5

            # set up uncertainty propagation
            mDraws = 100  # number of monte carlo draws
            prop = punpy.MCPropagation(mDraws, parallel_cores=1)

            # uncertainties from data:
            sample_mZ = cm.generate_sample(mDraws, mZ, mZ_unc, "rand")
            sample_n_iter = cm.generate_sample(mDraws, n_iter, None, None, dtype=int)
            sample_int_time_t0 = cm.generate_sample(mDraws, int_time_t0, None, None)
            sample_LAMP = cm.generate_sample(mDraws, LAMP, LAMP_unc, "syst")
            sample_Ct = cm.generate_sample(mDraws, Ct, Ct_unc, "syst")

            # Non-linearity alpha computation

            t1 = S1.iloc[0]
            S1 = S1.drop(S1.index[0])
            t2 = S2.iloc[0]
            S2 = S2.drop(S2.index[0])
            sample_t1 = cm.generate_sample(mDraws, t1, None, None)

            S1 = np.asarray(S1/65535.0, dtype=float)
            S2 = np.asarray(S2/65535.0, dtype=float)
            k = t1/(t2 - t1)
            sample_k = cm.generate_sample(mDraws, k, None, None)

            S1_unc = (pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['7']/100)[1:]*np.abs(S1)
            S2_unc = (pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_CAL").data)['9']/100)[1:]*np.abs(S2)

            sample_S1 = cm.generate_sample(mDraws, np.asarray(S1), S1_unc, "rand")
            sample_S2 = cm.generate_sample(mDraws, np.asarray(S2), S2_unc, "rand")

            S12 = self.S12func(k, S1, S2)
            sample_S12 = prop.run_samples(self.S12func, [sample_k, sample_S1, sample_S2])

            S12_sl_corr = self.Slaper_SL_correction(S12, mZ, n_iter=5)
            S12_sl_corr_unc = []
            sl4 = self.Slaper_SL_correction(S12, mZ, n_iter=4)
            for i in range(len(S12_sl_corr)):  # get the difference between n=4 and n=5
                if S12_sl_corr[i] > sl4[i]:
                    S12_sl_corr_unc.append(S12_sl_corr[i] - sl4[i])
                else:
                    S12_sl_corr_unc.append(sl4[i] - S12_sl_corr[i])

            sample_S12_sl_syst = cm.generate_sample(mDraws, S12_sl_corr, np.array(S12_sl_corr_unc), "syst")
            sample_S12_sl_rand = prop.run_samples(self.Slaper_SL_correction, [sample_S12, sample_mZ, sample_n_iter])
            sample_S12_sl_corr = prop.combine_samples([sample_S12_sl_syst, sample_S12_sl_rand])

            alpha = self.alphafunc(S1, S12)
            alpha_unc = np.power(np.power(S1_unc, 2) + np.power(S2_unc, 2) + np.power(S2_unc, 2), 0.5)
            sample_alpha = cm.generate_sample(mDraws, alpha, alpha_unc, "syst")

            # Updated calibration gain
            if sensortype == "ES":
                # Compute avg cosine error (not done for the moment)
                cos_mean_vals, cos_uncertainties = self.prepare_cos(uncGrp, sensortype, 'L2')
                corr = [None, "syst", "syst", "rand"]
                sample_radcal_wvl, sample_coserr, sample_coserr90, sample_zen_ang = [
                    cm.generate_sample(mDraws, samp, cos_uncertainties[i], corr[i]) for i, samp in
                    enumerate(cos_mean_vals)]
                # ZEN_avg_coserror, AZI_avg_coserror, zenith_ang, ZEN_delta_err, ZEN_delta, AZI_delta_err, AZI_delta
                avg_coserror, avg_azi_coserror, zenith_ang, zen_delta, azi_delta, zen_unc, azi_unc = \
                    self.cosine_error_correction(uncGrp, sensortype)
                # two components for cos unc, one from the file (rand), one is the difference between two symmetries

                # error due to lack of symmetry in cosine response
                sample_azi_delta_err1 = cm.generate_sample(mDraws, avg_azi_coserror, azi_unc, "syst")
                sample_azi_delta_err2 = cm.generate_sample(mDraws, avg_azi_coserror, azi_delta, "syst")
                sample_azi_delta_err = prop.combine_samples([sample_azi_delta_err1, sample_azi_delta_err2])
                sample_azi_err = prop.run_samples(self.AZAvg_Coserr, [sample_coserr, sample_coserr90])
                sample_azi_avg_coserror = prop.combine_samples([sample_azi_err, sample_azi_delta_err])

                sample_zen_delta_err1 = cm.generate_sample(mDraws, avg_coserror, zen_unc, "syst")
                sample_zen_delta_err2 = cm.generate_sample(mDraws, avg_coserror, zen_delta, "syst")
                sample_zen_delta_err = prop.combine_samples([sample_zen_delta_err1, sample_zen_delta_err2])
                sample_zen_err = prop.run_samples(self.ZENAvg_Coserr, [sample_radcal_wvl, sample_azi_avg_coserror])
                sample_zen_avg_coserror = prop.combine_samples([sample_zen_err, sample_zen_delta_err])

                full_hemi_coserr = self.FHemi_Coserr(avg_coserror, zenith_ang)
                sample_fhemi_coserr = prop.run_samples(self.FHemi_Coserr, [sample_zen_avg_coserror, sample_zen_ang])

                # Irradiance direct and diffuse ratio
                # res_py6s = ProcessL1b.get_direct_irradiance_ratio(node, sensortype, trios=0,
                #                                                   L2_irr_grp=grp)  # , trios=instrument_number)
                updated_radcal_gain = self.update_cal_data_ES(S12_sl_corr, LAMP, int_time_t0, t1)
                sample_updated_radcal_gain = prop.run_samples(self.update_cal_data_ES,
                                                              [sample_S12_sl_corr, sample_LAMP, sample_int_time_t0,
                                                               sample_t1])
            else:
                PANEL = np.asarray(pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_PANEL").data)['2'])
                unc_PANEL = (np.asarray(
                    pd.DataFrame(uncGrp.getDataset(sensortype + "_RADCAL_PANEL").data)['3'])/100)*PANEL
                sample_PANEL = cm.generate_sample(mDraws, PANEL, unc_PANEL, "syst")
                updated_radcal_gain = self.update_cal_data_rad(PANEL, S12_sl_corr, LAMP, int_time_t0, t1)
                sample_updated_radcal_gain = prop.run_samples(self.update_cal_data_rad,
                                                              [sample_PANEL, sample_S12_sl_corr, sample_LAMP,
                                                               sample_int_time_t0, sample_t1])

            # Data conversion
            mesure = raw_data/65365.0

            back_mesure = np.array([B0 + B1*(int_time[n]/int_time_t0) for n in range(nmes)])
            back_corrected_mesure = mesure - back_mesure
            std_light = np.std(back_corrected_mesure, axis=0)/nmes
            sample_back_corrected_mesure = cm.generate_sample(mDraws, np.mean(back_corrected_mesure, axis=0), std_light,
                                                              "rand")

            # Offset substraction : dark index read from attribute
            offset = np.mean(back_corrected_mesure[:, DarkPixelStart:DarkPixelStop], axis=1)
            offset_corrected_mesure = np.asarray(
                [back_corrected_mesure[:, i] - offset for i in range(nband)]).transpose()
            offset_std = np.std(back_corrected_mesure[:, DarkPixelStart:DarkPixelStop], axis=1)  # std in dark pixels
            std_dark = np.power((np.power(np.std(offset), 2) + np.power(offset_std, 2))/np.power(nmes, 2), 0.5)

            # add in quadrature with std in offset across scans
            sample_offset = cm.generate_sample(mDraws, np.mean(offset), np.mean(std_dark), "rand")
            sample_offset_corrected_mesure = prop.run_samples(self.dark_Substitution,
                                                              [sample_back_corrected_mesure, sample_offset])

            # average the signal and int_time for the station
            offset_corr_mesure = np.mean(offset_corrected_mesure, axis=0)
            int_time = np.average(int_time)

            prop = punpy.MCPropagation(mDraws, parallel_cores=1)

            # set standard variables
            n_iter = 5
            sample_n_iter = cm.generate_sample(mDraws, n_iter, None, None, dtype=int)

            # Non-Linearity Correction
            linear_corr_mesure = self.non_linearity_corr(offset_corr_mesure, alpha)
            sample_linear_corr_mesure = prop.run_samples(self.non_linearity_corr,
                                                         [sample_offset_corrected_mesure, sample_alpha])

            # Straylight Correction
            straylight_corr_mesure = self.Slaper_SL_correction(linear_corr_mesure, mZ, n_iter)

            S12_sl_corr_unc = []
            sl4 = self.Slaper_SL_correction(linear_corr_mesure, mZ, n_iter=4)
            for i in range(len(straylight_corr_mesure)):  # get the difference between n=4 and n=5
                if linear_corr_mesure[i] > sl4[i]:
                    S12_sl_corr_unc.append(straylight_corr_mesure[i] - sl4[i])
                else:
                    S12_sl_corr_unc.append(sl4[i] - straylight_corr_mesure[i])

            sample_straylight_1 = cm.generate_sample(mDraws, straylight_corr_mesure, np.array(S12_sl_corr_unc), "syst")
            sample_straylight_2 = prop.run_samples(self.Slaper_SL_correction,
                                                   [sample_linear_corr_mesure, sample_mZ, sample_n_iter])
            sample_straylight_corr_mesure = prop.combine_samples([sample_straylight_1, sample_straylight_2])

            # Normalization Correction, based on integration time
            normalized_mesure = straylight_corr_mesure*int_time_t0/int_time
            sample_normalized_mesure = sample_straylight_corr_mesure*int_time_t0/int_time

            # Calculate New Calibration Coeffs
            calibrated_mesure = self.absolute_calibration(normalized_mesure, updated_radcal_gain)
            sample_calibrated_mesure = prop.run_samples(self.absolute_calibration,
                                                        [sample_normalized_mesure, sample_updated_radcal_gain])

            # Thermal correction
            thermal_corr_mesure = self.thermal_corr(Ct, calibrated_mesure)
            sample_thermal_corr_mesure = prop.run_samples(self.thermal_corr, [sample_Ct, sample_calibrated_mesure])

            if sensortype.lower() == "es":
                # get cosine correction attributes and samples from dictionary
                # solar_zenith = res_py6s['solar_zenith']
                # direct_ratio = res_py6s['direct_ratio']
                solar_zenith = np.array([46.87415726])
                direct_ratio = np.array([0.222, 0.245, 0.256, 0.268, 0.279, 0.302, 0.313, 0.335, 0.345, 0.356,
                                         0.376, 0.386, 0.396, 0.415, 0.424, 0.433, 0.45, 0.459, 0.467, 0.482,
                                         0.489, 0.496, 0.51, 0.516, 0.522, 0.534, 0.539, 0.545, 0.555, 0.56,
                                         0.565, 0.576, 0.581, 0.586, 0.596, 0.6, 0.605, 0.613, 0.617, 0.621,
                                         0.629, 0.632, 0.636, 0.644, 0.647, 0.651, 0.657, 0.66, 0.663, 0.669,
                                         0.672, 0.675, 0.68, 0.683, 0.686, 0.691, 0.693, 0.696, 0.7, 0.702,
                                         0.705, 0.709, 0.711, 0.714, 0.717, 0.719, 0.721, 0.725, 0.726, 0.728,
                                         0.731, 0.733, 0.736, 0.738, 0.739, 0.742, 0.744, 0.745, 0.748, 0.749,
                                         0.75, 0.753, 0.754, 0.755, 0.757, 0.758, 0.759, 0.761, 0.763, 0.764,
                                         0.766, 0.767, 0.768, 0.769, 0.77, 0.771, 0.773, 0.774, 0.775, 0.776,
                                         0.777, 0.778, 0.779, 0.78, 0.781, 0.782, 0.783, 0.784, 0.785, 0.7855,
                                         0.786, 0.788, 0.788, 0.789, 0.79, 0.79, 0.791, 0.792, 0.793, 0.793,
                                         0.795, 0.795, 0.796, 0.797, 0.797, 0.798, 0.799, 0.799, 0.8, 0.801,
                                         0.801, 0.802, 0.802, 0.803, 0.803, 0.804, 0.805, 0.805, 0.806, 0.806,
                                         0.807, 0.807, 0.808, 0.808, 0.809, 0.809, 0.81, 0.81, 0.811, 0.811,
                                         0.811, 0.812, 0.812, 0.813, 0.813, 0.814, 0.814, 0.814, 0.815, 0.815,
                                         0.816, 0.816, 0.816, 0.817, 0.817, 0.817, 0.818, 0.818, 0.818, 0.819,
                                         0.819, 0.819, 0.819, 0.82, 0.82, 0.821, 0.821, 0.821, 0.822, 0.822,
                                         0.822, 0.822, 0.823, 0.823, 0.823, 0.824, 0.824, 0.824, 0.824, 0.825,
                                         0.825, 0.825, 0.826, 0.826, 0.826, 0.826, 0.827, 0.827, 0.827, 0.827,
                                         0.828, 0.828, 0.828, 0.828, 0.828, 0.829, 0.829, 0.829, 0.829, 0.83,
                                         0.83, 0.83, 0.83, 0.83, 0.83, 0.831, 0.831, 0.831, 0.831, 0.831,
                                         0.832, 0.832, 0.832, 0.832, 0.832, 0.832, 0.833, 0.833, 0.833, 0.833,
                                         0.833, 0.833, 0.834, 0.834, 0.834, 0.834, 0.834, 0.834, 0.834, 0.835,
                                         0.835, 0.835, 0.835, 0.835, 0.835, 0.835, 0.836, 0.836, 0.836, 0.836,
                                         0.836, 0.836, 0.836, 0.836, 0.837])

                sample_sol_zen = cm.generate_sample(mDraws, solar_zenith,
                                                    np.asarray([0.05 for i in range(len(solar_zenith))]),
                                                    "rand")  # TODO: get second opinion on zen unc in 6S
                sample_dir_rat = cm.generate_sample(mDraws, direct_ratio, 0.08*direct_ratio, "syst")

                ind_closest_zen = np.argmin(np.abs(zenith_ang - solar_zenith))
                cos_corr = 1 - avg_coserror[:, ind_closest_zen]/100
                Fhcorr = 1 - np.array(full_hemi_coserr)/100
                cos_corr_mesure = (direct_ratio*thermal_corr_mesure*cos_corr) + (
                        (1 - direct_ratio)*thermal_corr_mesure*Fhcorr)

                FRM_mesure = cos_corr_mesure
                sample_cos_corr_mesure = prop.run_samples(self.cosine_corr,
                                                          [sample_zen_avg_coserror, sample_fhemi_coserr, sample_zen_ang,
                                                           sample_thermal_corr_mesure, sample_sol_zen, sample_dir_rat])
                cos_unc = prop.process_samples(None, sample_cos_corr_mesure)

                unc = cos_unc
                sample = sample_cos_corr_mesure
            else:
                FRM_mesure = thermal_corr_mesure
                sample = sample_thermal_corr_mesure
                unc = prop.process_samples(None, sample_thermal_corr_mesure)

            # mask for arrays
            ind_zero = np.array([rc[0] == 0 for rc in raw_cal])  # changed due to raw_cal now being a np array
            ind_nan = np.array([np.isnan(rc[0]) for rc in raw_cal])
            ind_nocal = ind_nan | ind_zero

            # Remove wvl without calibration from the dataset and make uncertainties relative
            filtered_mesure = FRM_mesure[ind_nocal == False]
            filtered_unc = np.power(np.power(unc[ind_nocal == False]*1e10, 2)/np.power(filtered_mesure*1e10, 2), 0.5)

            output[f"{sensortype.lower()}Wvls"] = radcal_wvl[ind_nocal == False]
            output[
                f"{sensortype.lower()}Unc"] = filtered_unc  # dict(zip(str_wvl[ind_nocal==False], filtered_unc))  # unc in dict with wavelengths
            output[f"{sensortype.lower()}Sample"] = sample[:, ind_nocal == False]  # samples keep raw

        for sensortype in ['ES', 'LI', 'LT']:
            # get sensor specific wavebands - output[f"{sensortype.lower()}Wvls"].pop
            wvls = np.asarray(output.pop(f"{sensortype.lower()}Wvls"), dtype=float)
            _, output[f"{sensortype.lower()}Unc"] = self.interp_common_wvls(
                output[f"{sensortype.lower()}Unc"], wvls, newWaveBands)
            output[f"{sensortype.lower()}Sample"] = self.interpolateSamples(
                output[f"{sensortype.lower()}Sample"], wvls, newWaveBands)

        return output  # return products as dictionary to be appended to xSlice

    # Measurement functions
    @staticmethod
    def back_Mesure(B0, B1, int_time, t0):
        return B0 + B1*(int_time/t0)

    @staticmethod
    def update_cal_data_ES(S12_sl_corr, LAMP, int_time_t0, t1):
        updated_radcal_gain = (S12_sl_corr/LAMP)*(int_time_t0/t1)
        # sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = (updated_radcal_gain <= 1e-2)
        ind_nan = np.isnan(updated_radcal_gain)
        ind_nocal = ind_nan | ind_zero
        updated_radcal_gain[ind_nocal == True] = 1  # set 1 instead of 0 to perform calibration (otherwise division per 0)
        return updated_radcal_gain

    @staticmethod
    def update_cal_data_rad(PANEL, S12_sl_corr, LAMP, int_time_t0, t1):
        updated_radcal_gain = (np.pi*S12_sl_corr)/(LAMP*PANEL)*(int_time_t0/t1)

        # sensitivity factor : if gain==0 (or NaN), no calibration is performed and data is affected to 0
        ind_zero = (updated_radcal_gain <= 1e-2)
        ind_nan = np.isnan(updated_radcal_gain)
        ind_nocal = ind_nan | ind_zero
        updated_radcal_gain[
            ind_nocal == True] = 1  # set 1 instead of 0 to perform calibration (otherwise division per 0)
        return updated_radcal_gain
