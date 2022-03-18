
import os
import datetime as dt
import calendar
import numpy as np

from HDFRoot import HDFRoot
from ProcessL1b_DefaultCal import ProcessL1b_DefaultCal
from ConfigFile import ConfigFile
from CalibrationFileReader import CalibrationFileReader
from Source.ProcessL1b_Interp import ProcessL1b_Interp
from Utilities import Utilities

class ProcessL1b:

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
            msg = "**************Found NAN 0"
            print(msg)
            Utilities.writeLogFile(msg)
            exit

        if Utilities.hasNan(darkData):
            msg = "**************Found NAN 1"
            print(msg)
            Utilities.writeLogFile(msg)
            exit

        # Interpolate Dark Dataset to match number of elements as Light Dataset
        newDarkData = np.copy(lightData.data)
        for k in darkData.data.dtype.fields.keys(): # For each wavelength
            # x = np.copy(darkTimer.data["NONE"]).tolist() # darktimer
            x = np.copy(darkTimer.data).tolist() # darktimer
            y = np.copy(darkData.data[k]).tolist()  # data at that band over time
            # new_x = lightTimer.data["NONE"].tolist()  # lighttimer
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
                        print('nan')
                        exit
            else:
                msg = '**************Record too small for splining. Exiting.'
                print(msg)
                Utilities.writeLogFile(msg)
                return False

        darkData.data = newDarkData

        if Utilities.hasNan(darkData):
            msg = "**************Found NAN 2"
            print(msg)
            Utilities.writeLogFile(msg)
            exit

        # Correct light data by subtracting interpolated dark data from light data
        for k in lightData.data.dtype.fields.keys():
            for x in range(lightData.data.shape[0]):
                lightData.data[k][x] -= newDarkData[k][x]

        if Utilities.hasNan(lightData):
            msg = "**************Found NAN 3"
            print(msg)
            Utilities.writeLogFile(msg)
            exit

        return True

    # Copies TIMETAG2 values to Timer and converts to seconds
    @staticmethod
    def copyTimetag2(timerDS, tt2DS):
        if (timerDS.data is None) or (tt2DS.data is None):
            msg = "copyTimetag2: Timer/TT2 is None"
            print(msg)
            Utilities.writeLogFile(msg)
            return

        #print("Time:", time)
        #print(ds.data)
        for i in range(0, len(timerDS.data)):
            tt2 = float(tt2DS.data["NONE"][i])
            t = Utilities.timeTag2ToSec(tt2)
            timerDS.data["NONE"][i] = t

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
        Apply dark shutter correction to light data. Then apply either default factory cals or full instrument characterization.
        Then match timestamps and interpolate wavebands.
        '''
        root = HDFRoot()
        root.copy(node)
        root.attributes["PROCESSING_LEVEL"] = "1b"
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        root.attributes["FILE_CREATION_TIME"] = timestr

        msg = f"ProcessL1b.processL1b: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        root  = Utilities.rootAddDateTime(root)

        if not ProcessL1b.processDarkCorrection(root, "ES"):
            msg = 'Error dark correcting ES'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1b.processDarkCorrection(root, "LI"):
            msg = 'Error dark correcting LI'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1b.processDarkCorrection(root, "LT"):
            msg = 'Error dark correcting LT'
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Depending on the Configuration, process either the factory
        # calibration or the complete instrument characterizations
        if ConfigFile.settings['bL1bDefaultCal']:
            calFolder = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
            calPath = os.path.join("Config", calFolder)
            print("Read CalibrationFile ", calPath)
            calibrationMap = CalibrationFileReader.read(calPath)
            ProcessL1b_DefaultCal.processL1b(node, calibrationMap)

        elif ConfigFile.settings['bL1bFullFiles']:
            # This is a placeholder
            print('Processing full instrument characterizations')
            # ProcessL1b_FullFiles.processL1b(node, calibrationMap)

        # Match instruments to a common timestamp and interpolate to the chosen
        #   spectral resolution. HyperSAS instruments operate on different timestamps
        #   and wavebands, so interpolation is required.
        ProcessL1b_Interp.processL1b_Interp(node, outFilePath)





        # Datetime format is not supported in HDF5; remove
        # DATETIME is not supported in HDF5; remove
        for gp in root.groups:
            if (gp.id == "SOLARTRACKER_STATUS") is False:
                del gp.datasets["DATETIME"]

        return root
