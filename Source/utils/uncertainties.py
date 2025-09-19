import re
import numpy as np
import pandas as pd
from Source.ConfigFile import ConfigFile


class unc_management:
    def __init__(self):
        pass

    @staticmethod
    def RenameUncertainties_Class(node):
        """
        Rename unc dataset from generic class-based id to sensor type
        TODO: adapted to old version of ckass-based file, will be switch to next version
        when ready. Next version is commented below.
        """
        unc_group = node.getGroup("RAW_UNCERTAINTIES")
        sensorID = unc_management.get_sensor_dict(node) # should result in OD{[Instr#:ES, Instr#:LI, Instr#:LT]}
        print("sensors type", sensorID)
        names = [i for i in unc_group.datasets]  # get names in advance, mutation of iteration object breaks for loop
        for name in names:
            ds = unc_group.getDataset(name)

            if "_RADIANCE_" in name:
                # Class-based radiance coefficient are the same for both Li and Lt
                new_LI_name = ''.join(["LI", name.split("RADIANCE")[-1]])
                new_LI_ds = unc_group.addDataset(new_LI_name)
                new_LI_ds.copy(ds)
                new_LI_ds.datasetToColumns()

                new_LT_name = ''.join(["LT", name.split("RADIANCE")[-1]])
                new_LT_ds = unc_group.addDataset(new_LT_name)
                new_LT_ds.copy(ds)
                new_LT_ds.datasetToColumns()
                unc_group.removeDataset(ds.id) # remove dataset

            if "_IRRADIANCE_" in name:
                # Class-based irradiance coefficient are unique for Es
                new_ES_name = ''.join(["ES", name.split("IRRADIANCE")[-1]])
                new_ES_ds = unc_group.addDataset(new_ES_name)
                new_ES_ds.copy(ds)
                new_ES_ds.datasetToColumns()
                unc_group.removeDataset(ds.id) # remove dataset

            if "_LI_" in name:
                # Class-based irradiance coefficient are unique for Es
                new_name = ''.join(["LI", name.split("LI")[-1]])
                new_ds = unc_group.addDataset(new_name)
                new_ds.copy(ds)
                new_ds.datasetToColumns()
                unc_group.removeDataset(ds.id) # remove dataset

            if "_LT_" in name:
                # Class-based irradiance coefficient are unique for Es
                new_name = ''.join(["LT", name.split("LT")[-1]])
                new_ds = unc_group.addDataset(new_name)
                new_ds.copy(ds)
                new_ds.datasetToColumns()
                unc_group.removeDataset(ds.id) # remove dataset

            if "_RADCAL_" in name:
                # RADCAL are always sensor specific
                for sensor in sensorID:
                    if sensor in ds.id:
                        new_ds_name = ''.join([sensorID[sensor], ds.id.split(sensor)[-1]])
                        new_ds = unc_group.addDataset(new_ds_name)
                        new_ds.copy(ds)
                        new_ds.datasetToColumns()
                        unc_group.removeDataset(ds.id)  # remove dataset

        return True
    
    @staticmethod
    def interpUncertainties_Factory(node):

        grp = node.getGroup("RAW_UNCERTAINTIES")
        sensorList = ['ES', 'LI', 'LT']
        for sensor in sensorList:

            ## retrieve dataset from corresponding instrument
            data = None
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                data = node.getGroup(sensor+'_LIGHT').getDataset(sensor)
            elif ConfigFile.settings['SensorType'].lower() == "trios" or \
                ConfigFile.settings['SensorType'].lower() == "dalec" or \
                ConfigFile.settings['SensorType'].lower() == "sorad":
                data = node.getGroup(sensor).getDataset(sensor)

            # Retrieve hyper-spectral wavelengths from dataset
            x_new = np.array(pd.DataFrame(data.data).columns, dtype=float)

            for data_type in ["_RADCAL_UNC"]:
                ds = grp.getDataset(sensor+data_type)
                ds.datasetToColumns()
                x = ds.columns['wvl']
                y = ds.columns['unc']
                y_new = np.interp(x_new, x, y)
                ds.columns['unc'] = y_new
                ds.columns['wvl'] = x_new
                ds.columnsToDataset()


            ## Interpolate for initial class-based file, in use at the moment
            for data_type in ["_TEMPDATA_CAL"]:
                ds = grp.getDataset(sensor + data_type)
                ds.datasetToColumns()
                x = ds.columns['1']
                for indx in range(2, len(ds.columns)):
                    y = ds.columns[str(indx)]
                    y_new = np.interp(x_new, x, y)
                    ds.columns[str(indx)] = y_new
                # column ['0'] longer than the rest due to interpolation - this is a quick work around
                ds.columns['0'] = np.array(
                    range(len(x_new)))  # np.array(ds.columns['0'])[1:] # drop 1st line from TARTU file
                ds.columns['1'] = x_new
                ds.columnsToDataset()

            ## Interpolate for initial class-based file, in use at the moment
            for data_type in ["_POLDATA_CAL", "_STABDATA_CAL", "_NLDATA_CAL"]:
                ds = grp.getDataset(sensor + data_type)
                ds.datasetToColumns()
                x = ds.columns['0']
                y = ds.columns['1']
                y_new = np.interp(x_new, x, y)
                ds.columns['0'] = x_new
                ds.columns['1'] = y_new
                ds.columnsToDataset()

        return True

    @staticmethod
    def interpUncertainties_Class(node):

        grp = node.getGroup("RAW_UNCERTAINTIES")
        sensorList = ['ES', 'LI', 'LT']

        for sensor in sensorList:

            ## retrieve dataset from corresponding instrument
            data = None
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                data = node.getGroup(sensor+'_LIGHT').getDataset(sensor)
            elif ConfigFile.settings['SensorType'].lower() == "trios" or ConfigFile.settings['SensorType'].lower() == "sorad":
                data = node.getGroup(sensor).getDataset(sensor)

            # Retrieve hyper-spectral wavelengths from dataset
            x_new = np.array(pd.DataFrame(data.data).columns, dtype=float)


            # RADCAL data do not need interpolation, just removing the first line
            for data_type in ["_RADCAL_CAL"]:

                ds = grp.getDataset(sensor+data_type)
                try:
                    ds.datasetToColumns()
                except:
                    print('erk')
                for indx in range(len(ds.columns)):
                    indx_name = str(indx)
                    if indx_name != '':
                        y = np.array(ds.columns[indx_name])
                        if len(y)==255:
                            ds.columns[indx_name] = y
                        elif len(y)==256:
                            # drop 1st line from TARTU file
                            ds.columns[indx_name] = y[1:]
                ds.columnsToDataset()

            ## Interpolate for initial class-based file, in use at the moment
            for data_type in ["_TEMPDATA_CAL"]:
                ds = grp.getDataset(sensor + data_type)
                ds.datasetToColumns()
                x = ds.columns['1']
                for indx in range(2, len(ds.columns)):
                    y = ds.columns[str(indx)]
                    y_new = np.interp(x_new, x, y)
                    ds.columns[str(indx)] = y_new
                # column ['0'] longer than the rest due to interpolation - this is a quick work around
                ds.columns['0'] = np.array(
                    range(len(x_new)))  # np.array(ds.columns['0'])[1:] # drop 1st line from TARTU file
                ds.columns['1'] = x_new
                ds.columnsToDataset()

            ## Interpolate for initial class-based file, in use at the moment
            for data_type in ["_POLDATA_CAL", "_STABDATA_CAL", "_NLDATA_CAL"]:
                ds = grp.getDataset(sensor + data_type)
                ds.datasetToColumns()
                x = ds.columns['0']
                y = ds.columns['1']
                y_new = np.interp(x_new, x, y)
                ds.columns['0'] = x_new
                ds.columns['1'] = y_new
                ds.columnsToDataset()

            ## RADCAL_LAMP/: Interpolate data to hyper-spectral pixels
            for data_type in ["_RADCAL_LAMP"]:
                ds = grp.getDataset(sensor+data_type)
                ds.datasetToColumns()
                x = ds.columns['0']
                for indx in range(1,len(ds.columns)):
                    y = ds.columns[str(indx)]
                    y_new = np.interp(x_new, x, y)
                    ds.columns[str(indx)] = y_new
                ds.columns['0'] = x_new
                ds.columnsToDataset()

            ## RADCAL_PANEL: only for Li & Lt
            if sensor != "ES":
                for data_type in ["_RADCAL_PANEL"]:
                    ds = grp.getDataset(sensor+data_type)
                    ds.datasetToColumns()
                    x = ds.columns['0']
                    for indx in range(1,len(ds.columns)):
                        y = ds.columns[str(indx)]
                        y_new = np.interp(x_new, x, y)
                        ds.columns[str(indx)] = y_new
                    ds.columns['0'] = x_new
                    ds.columnsToDataset()
            else:
                for data_type in ["_ANGDATA_COSERROR", "_ANGDATA_COSERROR_RANGE60-90"]:
                    ds = grp.getDataset(sensor + data_type)
                    ds.datasetToColumns()
                    x = ds.columns['0']
                    y = ds.columns['1']
                    y_new = np.interp(x_new, x, y)
                    ds.columns['0'] = x_new
                    ds.columns['1'] = y_new
                    ds.columnsToDataset()

        return True

    @staticmethod
    def interpUncertainties_FullChar(node):
        """
        For full char, all input comes already with a wavelength columns,
        except RADCAL LAMP ad PANEL, that need to be interpolated on wvl.
        """

        grp = node.getGroup("RAW_UNCERTAINTIES")
        # sensorId = unc_management.get_sensor_dict(node)
        sensorList = ['ES', 'LI', 'LT']
        for sensor in sensorList:
            ds = grp.getDataset(sensor+"_RADCAL_CAL")
            ds.datasetToColumns()
            # indx = ds.attributes["INDEX"]
            # pixel = np.array(ds.columns['0'[1:])
            bands = np.array(ds.columns['1'][1:])
            coeff = np.array(ds.columns['2'][1:])
            valid = bands>0
            # x_new2 = bands[valid]

            ## retrieve hyper-spectral wavelengths from corresponding instrument
            data = None
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                data = node.getGroup(sensor+'_LIGHT').getDataset(sensor)
            elif ConfigFile.settings['SensorType'].lower() == "trios" or ConfigFile.settings['SensorType'].lower() == "sorad":
                # inv_dict = {v: k for k, v in sensorId.items()}
                # data = node.getGroup('SAM_'+inv_dict[sensor]+'.dat').getDataset(sensor)
                data = node.getGroup(sensor).getDataset(sensor)

            x_new = np.array(pd.DataFrame(data.data).columns, dtype=float)

            # intersect, ind1, valid = np.intersect1d(x_new, bands, return_indices=True)
            if len(bands[valid]) != len(x_new):
                print("ERROR: band wavelength not found in calibration file")
                print(len(bands[valid]))
                print(len(x_new))
                # exit()
                return False

            ## RADCAL_LAMP: Interpolate data to hyper-spectral pixels
            for data_type in ["_RADCAL_LAMP"]:
                ds = grp.getDataset(sensor+data_type)
                ds.datasetToColumns()
                x = ds.columns['0']
                for indx in range(1,len(ds.columns)):
                    y = ds.columns[str(indx)]
                    y_new = np.interp(x_new, x, y)
                    ds.columns[str(indx)] = y_new
                ds.columns['0'] = x_new
                ds.columnsToDataset()

            ## RADCAL_PANEL: interplation only for Li & Lt
            if sensor != "ES":
                for data_type in ["_RADCAL_PANEL"]:
                    ds = grp.getDataset(sensor+data_type)
                    ds.datasetToColumns()
                    x = ds.columns['0']
                    for indx in range(1,len(ds.columns)):
                        y = ds.columns[str(indx)]
                        y_new = np.interp(x_new, x, y)
                        ds.columns[str(indx)] = y_new
                    ds.columns['0'] = x_new
                    ds.columnsToDataset()
        
        return True
    
    @staticmethod
    def get_sensor_dict(node):
        sensorID = {}
        for grp in node.groups:
            # if "CalFileName" in grp.attributes:
            if ConfigFile.settings['SensorType'].lower() == 'seabird':
                # Provision for sensor calibration names without leading zeros
                if "ES_" in grp.id or "LI_" in grp.id or "LT_" in grp.id:
                    sensorCode = grp.attributes["CalFileName"][3:7]
                    if not sensorCode.isnumeric():
                        sensorCode = re.findall(r'\d+', sensorCode)
                    if len(sensorCode) < 4:
                        sensorCode = '0' + sensorCode[0]

                if "ES_" in grp.id:
                    sensorID[sensorCode] = "ES"
                    # sensorID[grp.attributes["CalFileName"][3:7]] = "ES"
                if "LI_" in grp.id:
                    sensorID[sensorCode] = "LI"
                if "LT_" in grp.id:
                    sensorID[sensorCode] = "LT"

            # elif "IDDevice" in grp.attributes:
            elif ConfigFile.settings['SensorType'].lower() == 'trios' or  ConfigFile.settings['SensorType'].lower() == 'sorad':
                if "ES" in grp.datasets:
                    sensorID[grp.attributes["IDDevice"][4:8]] = "ES"
                if "LI" in grp.datasets:
                    sensorID[grp.attributes["IDDevice"][4:8]] = "LI"
                if "LT" in grp.datasets:
                    sensorID[grp.attributes["IDDevice"][4:8]] = "LT"

        return sensorID

    @staticmethod
    def RenameUncertainties_FullChar(node):
        """
        Rename unc dataset from specific sensor id to sensor type
        """
        unc_group = node.getGroup("RAW_UNCERTAINTIES")
        sensorID = unc_management.get_sensor_dict(node) # should result in OD{[Instr#:ES, Instr#:LI, Instr#:LT]}
        print("sensors type", sensorID)
        names = [i for i in unc_group.datasets]  # get names in advance, mutation of iteration object breaks for loop
        for name in names:
            ds = unc_group.getDataset(name)
            for sensor in sensorID:
                if sensor in ds.id:
                    new_ds_name = ''.join([sensorID[sensor], ds.id.split(sensor)[-1]])
                    new_ds = unc_group.addDataset(new_ds_name)
                    new_ds.copy(ds)
                    new_ds.datasetToColumns()
                    unc_group.removeDataset(ds.id)  # remove  dataset
        return True
