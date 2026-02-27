# linting
from typing import Union

# maths
import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline
from collections import OrderedDict


# contains utility methods to be accessed by all classes within the PIU


class utils:

    def __init__(self):
        """
        static class to contain utility methods for PIU
        """
        pass

    @staticmethod
    def apply_NaN_Mask(rawSlice):
        for wvl in rawSlice:  # iterate over wavelengths
            if any(np.isnan(rawSlice[wvl])):  # if we encounter any NaN's
                for msk in np.where(np.isnan(rawSlice[wvl]))[0]:  # mask may be multiple indexes
                    for wl in rawSlice:  # strip the scan
                        rawSlice[wl].pop(msk)  # remove the scan if nans are found anywhere

    @staticmethod
    def interp_common_wvls(columns, waves, newWaveBands, return_as_dict: bool=False) -> Union[np.array, OrderedDict]:
        """
        interpolate array to common wavebands

        :param columns: values to be interpolated (y)
        :param waves: current wavelengths (x)
        :param newWaveBands: wavelenghts to interpolate (new_x)
        :param return_as_dict: boolean which if true will return an ordered dictionary (wavelengths are keys)

        :return: returns the interpolated output as either a numpy array or Ordered-Dictionary
        """
        saveDatetag,saveTimetag2,y = None,None,None
        if isinstance(columns, dict):
            if "Datetag" in columns:
                saveDatetag = columns.pop("Datetag")
                saveTimetag2 = columns.pop("Timetag2")
                columns.pop("Datetime")
            y = np.asarray(list(columns.values()))
        elif isinstance(columns, np.ndarray):  # is numpy array
            y = columns
        else:
            msg = "columns are unexpected type: ProcessInstrumentUncertainties.py - interp_common_wvls"
            print(msg)
        # Get wavelength values
        x = np.asarray(waves)

        newColumns = OrderedDict()
        if saveTimetag2 is not None:
            newColumns["Datetag"] = saveDatetag
            newColumns["Timetag2"] = saveTimetag2
        # Can leave Datetime off at this point

        new_y = np.interp(newWaveBands, x, y)  # InterpolatedUnivariateSpline(x, y, k=3)(newWavebands)

        if return_as_dict:
            for idx, wb in enumerate(newWaveBands):
                # wb_str = str(round(10 * wb) / 10) # limit to one decimal place (inconsitent with other parts of the code)
                wb_str = str(wb)  # preferred for consistency
                newColumns[wb_str] = [new_y[idx]]
            return newColumns
        else:
            return new_y

    @staticmethod
    def interp_L1A_L2sub(l1Data,oldWavebands,newWavebands,uncType):
        '''
        :param l1Data: Level 1AQC sized class of raw uncertainties
        :param oldWavebands: Level 1AQC wavebands
        :param newWavebands: Level 2 wavebands, common bands truncated for rho limitation
        :param uncType: 'pds' or 'stats' to designate class to be interpolated
        '''
        l2Data = {}
        if uncType.lower() == 'pds':

            l2Data['EsCalUnc'] = utils.interp_common_wvls(
                l1Data.uncs['ES']['cal'],
                oldWavebands['ES'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LiCalUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LI']['cal'],
                oldWavebands['LI'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LtCalUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LT']['cal'],
                oldWavebands['LT'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['EsStabUnc'] = utils.interp_common_wvls(
                l1Data.uncs['ES']['stab'],
                oldWavebands['ES'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LiStabUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LI']['stab'],
                oldWavebands['LI'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LtStabUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LT']['stab'],
                oldWavebands['LT'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['EsNLinUnc'] = utils.interp_common_wvls(
                l1Data.uncs['ES']['nlin'],
                oldWavebands['ES'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LiNLinUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LI']['nlin'],
                oldWavebands['LI'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LtNLinUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LT']['nlin'],
                oldWavebands['LT'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['EsStrayUnc'] = utils.interp_common_wvls(
                l1Data.uncs['ES']['stray'],
                oldWavebands['ES'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LiStrayUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LI']['stray'],
                oldWavebands['LI'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LtStrayUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LT']['stray'],
                oldWavebands['LT'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['EsCtUnc'] = utils.interp_common_wvls(
                l1Data.uncs['ES']['ct'],
                oldWavebands['ES'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LiCtUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LI']['ct'],
                oldWavebands['LI'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LtCtUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LT']['ct'],
                oldWavebands['LT'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LiPolUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LI']['pol'],
                oldWavebands['LI'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['LtPolUnc'] = utils.interp_common_wvls(
                l1Data.uncs['LT']['pol'],
                oldWavebands['LT'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['EsCosUnc'] = utils.interp_common_wvls(
                l1Data.uncs['ES']['cos'],
                oldWavebands['ES'],
                newWavebands,
                return_as_dict=False
            )
        else: # stats
            l2Data['LiStd'] = utils.interp_common_wvls(
            l1Data['LI']['Signal_std'],
            oldWavebands['LI'],
            newWavebands,
            return_as_dict=False
            )
            l2Data['LtStd'] = utils.interp_common_wvls(
                l1Data['LT']['Signal_std'],
                oldWavebands['LT'],
                newWavebands,
                return_as_dict=False
            )
            l2Data['EsStd'] = utils.interp_common_wvls(
                l1Data['ES']['Signal_std'],
                oldWavebands['ES'],
                newWavebands,
                return_as_dict=False
            )

        return l2Data

    @staticmethod
    def pad_wavebands_L1A(stats, fidradBands):
        '''Retain uninterpolated L1A wavebands, but pad them to 255 pixels based of ES RADCAL_CAL bands
            Do not edit the Signal_std_Interpolated dataset.'''
        sensors = ['ES','LI','LT']
        datasets = ['ave_Light','ave_Dark','std_Light','std_Dark','Signal_std']
        dicts = ['Signal_noise']

        # Reported L1A bands are in Signal_noise dict
        for sType in sensors:
            l1Abands = np.array(list(stats[sType][dicts[0]].keys()), dtype=float)
            if sType != 'ES':
                        fidradBands[0:len(l1Abands)] = l1Abands
            if len(l1Abands) < 255:
                for ds in datasets:
                    stats[sType][ds] = utils.interp_common_wvls(
                        stats[sType][ds],
                        l1Abands,
                        fidradBands,
                        return_as_dict=False
                        )

    @staticmethod
    def interpolateSamples(Columns, waves, newWavebands):
        '''
        Wavelength Interpolation for differently sized arrays containing samples
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

            new_y = InterpolatedUnivariateSpline(waves, y, k=3)(newWavebands)

            for waveIndex in range(newWavebands.shape[0]):
                newColumns[str(round(10*newWavebands[waveIndex])/10)].append(new_y[waveIndex])

            cols.append(newColumns)

        return np.asarray(cols)
    
    @staticmethod
    def read_sixS_model(node):
        import pandas as pd

        res_sixS = {}
        
        # Create a temporary group to pop date time columns
        newGrp = node.addGroup('temp')
        newGrp.copy(node.getGroup('SIXS_MODEL'))
        for ds in newGrp.datasets:
            newGrp.datasets[ds].datasetToColumns()
        sixS_gp = node.getGroup('temp')
        
        sixS_gp.getDataset("direct_ratio").columns.pop('Datetime')
        sixS_gp.getDataset("direct_ratio").columns.pop('Timetag2')
        sixS_gp.getDataset("direct_ratio").columns.pop('Datetag')
        sixS_gp.getDataset("direct_ratio").columnsToDataset()
        sixS_gp.getDataset("diffuse_ratio").columns.pop('Datetime')
        sixS_gp.getDataset("diffuse_ratio").columns.pop('Timetag2')
        sixS_gp.getDataset("diffuse_ratio").columns.pop('Datetag')
        sixS_gp.getDataset("diffuse_ratio").columnsToDataset()

        # sixS_gp.getDataset("direct_ratio").datasetToColumns()
        res_sixS['solar_zenith'] = np.asarray(sixS_gp.getDataset('solar_zenith').columns['solar_zenith'])
        res_sixS['wavelengths'] = np.asarray(list(sixS_gp.getDataset('direct_ratio').columns.keys())[2:], dtype=float)
        if 'timetag' in res_sixS['wavelengths']:
            # because timetag2 was included for some data and caused a bug
            res_sixS['wavelengths'] = res_sixS['wavelengths'][1:]
        res_sixS['direct_ratio'] = np.asarray(pd.DataFrame(sixS_gp.getDataset("direct_ratio").data))
        res_sixS['diffuse_ratio'] = np.asarray(pd.DataFrame(sixS_gp.getDataset("diffuse_ratio").data))
        node.removeGroup(sixS_gp)

        return res_sixS
