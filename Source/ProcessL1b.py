
import os
import datetime as dt
import calendar
import numpy as np
from inspect import currentframe, getframeinfo

from Source.ProcessL1b_FactoryCal import ProcessL1b_FactoryCal
from Source.ProcessL1b_ClassCal import ProcessL1b_ClassCal
from Source.ProcessL1b_FRMCal import ProcessL1b_FRMCal
from Source.ConfigFile import ConfigFile
from Source.CalibrationFileReader import CalibrationFileReader
from Source.ProcessL1b_Interp import ProcessL1b_Interp
from Source.Utilities import Utilities

class ProcessL1b:
    '''SeaBird L1b'''

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
    def darkCorrection(darkData, darkTimer, lightData, lightTimer):
        '''
        HyperInSPACE - Interpolate Dark values to match light measurements (e.g. Brewin 2016, Prosoft
        7.7 User Manual SAT-DN-00228-K)
        '''
        if (darkData is None) or (lightData is None):
            msg  = f'Dark Correction, dataset not found: {darkData} , {lightData}'
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
        for k in lightData.data.dtype.fields.keys():
            for x in range(lightData.data.shape[0]):
                lightData.data[k][x] -= newDarkData[k][x]

        if Utilities.hasNan(lightData):
            frameinfo = getframeinfo(currentframe())
            msg = f'found NaN {frameinfo.lineno}'
            print(msg)
            Utilities.writeLogFile(msg)
            exit()

        return True

    # # Copies TIMETAG2 values to Timer and converts to seconds
    # @staticmethod
    # def copyTimetag2(timerDS, tt2DS):
    #     if (timerDS.data is None) or (tt2DS.data is None):
    #         msg = "copyTimetag2: Timer/TT2 is None"
    #         print(msg)
    #         Utilities.writeLogFile(msg)
    #         return

    #     for i in range(0, len(timerDS.data)):
    #         tt2 = float(tt2DS.data["NONE"][i])
    #         t = Utilities.timeTag2ToSec(tt2)
    #         timerDS.data["NONE"][i] = t

    @staticmethod
    def processDarkCorrection(node, sensorType):
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
            if not gp.id.endswith('_L1AQC'):
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

        # Instead of using TT2 or seconds, use python datetimes to avoid problems crossing
        # UTC midnight.
        if not ProcessL1b.darkCorrection(darkData, darkDateTime, lightData, lightDateTime):
            msg = f'ProcessL1d.darkCorrection failed  for {sensorType}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        # Now that the dark correction is done, we can strip the dark shutter data from the
        # HDF object.
        for gp in node.groups:
            if not gp.id.endswith('_L1AQC'):
                if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensorType):
                    node.removeGroup(gp)
        # And rename the corrected light frame
        for gp in node.groups:
            if not gp.id.endswith('_L1AQC'):
                if gp.attributes["FrameType"] == "ShutterLight" and gp.getDataset(sensorType):
                    gp.id = gp.id[0:2] # Strip off "_LIGHT" from the name
        return True

    @staticmethod
    def processL1b(node, outFilePath):
        '''
        Non-TriOS path. ProcessL1b_Interp.processL1b_Interp will be common to both platforms
        Apply dark shutter correction to light data. Then apply either default factory cals
        or full instrument characterization. Introduce uncertainty group.
        Match timestamps and interpolate wavebands.
        '''
        node.attributes["PROCESSING_LEVEL"] = "1B"
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr
        if ConfigFile.settings["bL1bCal"] == 1:
            node.attributes['CAL_TYPE'] = 'Default/Factory'
        elif ConfigFile.settings["bL1bCal"] == 2:
            node.attributes['CAL_TYPE'] = 'Class-based'
        elif ConfigFile.settings["bL1bCal"] == 3:
            node.attributes['CAL_TYPE'] = 'Full-FRM'
        node.attributes['WAVE_INTERP'] = str(ConfigFile.settings['fL1bInterpInterval']) + ' nm'


        msg = f"ProcessL1b.processL1b: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        node  = Utilities.rootAddDateTime(node)

        ''' Introduce a new group for carrying L1AQC data forward. Groups keep consistent timestamps across all datasets,
            so it has to be a new group to avoid conflict with interpolated timestamps. '''

        # Due to the way light/dark sampling works with OCRs, each will need its own group
        esDarkGroup = node.addGroup('ES_DARK_L1AQC')
        esLightGroup = node.addGroup('ES_LIGHT_L1AQC')
        liDarkGroup = node.addGroup('LI_DARK_L1AQC')
        liLightGroup = node.addGroup('LI_LIGHT_L1AQC')
        ltDarkGroup = node.addGroup('LT_DARK_L1AQC')
        ltLightGroup = node.addGroup('LT_LIGHT_L1AQC')
        for gp in node.groups:
            if gp.id == 'ES_DARK':
                esDarkGroup.copy(gp)
            elif gp.id == 'ES_LIGHT':
                esLightGroup.copy(gp)
            elif gp.id == 'LI_DARK':
                liDarkGroup.copy(gp)
            elif gp.id == 'LI_LIGHT':
                liLightGroup.copy(gp)
            elif gp.id == 'LT_DARK':
                ltDarkGroup.copy(gp)
            elif gp.id == 'LT_LIGHT':
                ltLightGroup.copy(gp)

        # Dark Correction
        if not ProcessL1b.processDarkCorrection(node, "ES"):
            msg = 'Error dark correcting ES'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1b.processDarkCorrection(node, "LI"):
            msg = 'Error dark correcting LI'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1b.processDarkCorrection(node, "LT"):
            msg = 'Error dark correcting LT'
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Interpolate only the Ancillary group, and then fold in model data
        if not ProcessL1b_Interp.interp_Anc(node, outFilePath):
            msg = 'Error interpolating ancillary data'
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Calibration
        # Depending on the Configuration, process either the factory
        # calibration or the complete instrument characterizations
        if ConfigFile.settings['bL1bCal'] == 1:
            calFolder = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
            calPath = os.path.join("Config", calFolder)
            print("Read CalibrationFile ", calPath)
            calibrationMap = CalibrationFileReader.read(calPath)
            ProcessL1b_FactoryCal.processL1b_SeaBird(node, calibrationMap)

        elif ConfigFile.settings['bL1bCal'] == 2:
            print('Placeholder for Class-based')
            if not ProcessL1b_ClassCal.processL1b_SeaBird(node):
                msg = 'Error in ProcessL1b.process_FRM_calibration'
                print(msg)
                Utilities.writeLogFile(msg)
                return None

        elif ConfigFile.settings['bL1bCal'] == 3:
            if not ProcessL1b_FRMCal.process_FRM_SeaBird(node):
                msg = 'Error in ProcessL1b.process_FRM_calibration'
                print(msg)
                Utilities.writeLogFile(msg)
                return None

        # Interpolation
        ''' Used with both TriOS and SeaBird '''
        # Match instruments to a common timestamp (slowest shutter, should be Lt) and
        # interpolate to the chosen spectral resolution. HyperSAS instruments operate on
        # different timestamps and wavebands, so interpolation is required.
        node = ProcessL1b_Interp.processL1b_Interp(node, outFilePath)

        # Datetime format is not supported in HDF5; already removed in ProcessL1b_Interp.py

        return node
