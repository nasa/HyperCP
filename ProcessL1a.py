
import collections
import datetime as dt
import os

import HDFRoot
import HDFGroup
from MainConfig import MainConfig
from Utilities import Utilities
from RawFileReader import RawFileReader


class ProcessL1a:

    # Reads a raw file and generates a L1a HDF file
    @staticmethod
    def processL1a(fp, outFilePath, calibrationMap):
        (_, fileName) = os.path.split(fp)

        # Generate root header attributes
        root = HDFRoot.HDFRoot()
        root.id = "/"
        root.attributes["HYPERINSPACE"] = MainConfig.settings["version"]
        root.attributes["CAL_FILE_NAMES"] = ','.join(calibrationMap.keys())
        root.attributes["WAVELENGTH_UNITS"] = "nm"
        root.attributes["LU_UNITS"] = "count"
        root.attributes["ED_UNITS"] = "count"
        root.attributes["ES_UNITS"] = "count"
        root.attributes["SATPYR_UNITS"] = "count"
        root.attributes["RAW_FILE_NAME"] = fileName

        contextMap = collections.OrderedDict()

        for key in calibrationMap:
            cf = calibrationMap[key]
            gp = HDFGroup.HDFGroup()
            gp.id = cf.instrumentType
            contextMap[cf.id] = gp

        # print("contextMap:", list(contextMap.keys()))
        # print("calibrationMap:", list(calibrationMap.keys()))
        print('Reading in raw binary data may take a moment.')
        RawFileReader.readRawFile(fp, calibrationMap, contextMap, root)

        # Populate HDF group attributes
        for key in calibrationMap:
            cf = calibrationMap[key]
            gp = contextMap[cf.id]
            gp.attributes["InstrumentType"] = cf.instrumentType
            gp.attributes["Media"] = cf.media
            gp.attributes["MeasMode"] = cf.measMode
            gp.attributes["FrameType"] = cf.frameType            
            gp.getTableHeader(cf.sensorType)
            gp.attributes["DISTANCE_1"] = "Pressure " + cf.sensorType + " 1 1 0"
            gp.attributes["DISTANCE_2"] = "Surface " + cf.sensorType + " 1 1 0"
            gp.attributes["SensorDataList"] = ", ".join([x for x in gp.datasets.keys()])
            if gp.id != 'SAS' and gp.id != 'Reference':
                root.groups.append(gp)

        # Insure essential data groups are present before proceeding
        hld = 0
        hsl = 0
        hse = 0
        hed = 0
        gps = 0
        for gp in root.groups:
            if gp.id.startswith("HLD"):
                hld += 1
            if gp.id.startswith("HSL"):
                hsl += 1
            if gp.id.startswith("HSE"):
                hse += 1
            if gp.id.startswith("HED"):
                hed += 1
            if gp.id.startswith("GPRMC"):
                gps += 1
        if hld != 2 or hsl != 2 or hse != 1 or hed != 1 or gps != 1:
            msg = "ProcessL1a.processL1a: Essential dataset missing. Aborting."
            print(msg)
            Utilities.writeLogFile(msg)
            return None
                
                                
        # Generates root footer attributes
        root.attributes["PROCESSING_LEVEL"] = "1a"
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        root.attributes["FILE_CREATION_TIME"] = timestr
        msg = "ProcessL1a.processL1a: " + timestr
        print(msg)
        Utilities.writeLogFile(msg)

        # Converts gp.columns to numpy array
        for gp in root.groups:
            if gp.id.startswith("SATMSG"): # Don't convert these strings to datasets.
                for ds in gp.datasets.values():
                    ds.columnsToDataset()
                # break
            else:
                for ds in gp.datasets.values():
                    if not ds.columnsToDataset():                                                
                        msg = "ProcessL1a.processL1a: Essential column cannot be converted to Dataset. Aborting."
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return None

        return root
