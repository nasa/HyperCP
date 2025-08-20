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
        saveTimetag2 = None
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

        for i in range(newWaveBands.shape[0]):
            newColumns[str(round(10*newWaveBands[i])/10)] = []  # limit to one decimal place

        new_y = np.interp(newWaveBands, x, y)  #InterpolatedUnivariateSpline(x, y, k=3)(newWavebands)

        for waveIndex in range(newWaveBands.shape[0]):
            newColumns[str(round(10*newWaveBands[waveIndex])/10)].append(new_y[waveIndex])

        if return_as_dict:
            return newColumns
        else:
            return new_y

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
