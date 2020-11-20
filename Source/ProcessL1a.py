
import collections
import datetime as dt
import os

import HDFRoot
import HDFGroup
from MainConfig import MainConfig
from Utilities import Utilities
from RawFileReader import RawFileReader


class ProcessL1a:
    
    @staticmethod
    def processL1a(fp, calibrationMap):
        '''
        Reads a raw binary file and generates a L1a HDF5 file
        '''
        (_, fileName) = os.path.split(fp)

        # Generate root header attributes
        root = HDFRoot.HDFRoot()
        root.id = "/"
        root.attributes["HYPERINSPACE"] = MainConfig.settings["version"]
        root.attributes["CAL_FILE_NAMES"] = ','.join(calibrationMap.keys())
        root.attributes["WAVELENGTH_UNITS"] = "nm"
        root.attributes["LI_UNITS"] = "count"
        root.attributes["LT_UNITS"] = "count"
        root.attributes["ES_UNITS"] = "count"
        root.attributes["SATPYR_UNITS"] = "count"
        root.attributes["RAW_FILE_NAME"] = fileName

        # Generates root footer attributes
        root.attributes["PROCESSING_LEVEL"] = "1a"
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        root.attributes["FILE_CREATION_TIME"] = timestr
        msg = f"ProcessL1a.processL1a: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

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
            if gp.id.startswith("GP"):
                gps += 1
        if hld != 2 or hsl != 2 or hse != 1 or hed != 1 or gps != 1:
            msg = "ProcessL1a.processL1a: Essential dataset missing. Aborting."
            msg = f'{msg}\ngps: {gps}'
            msg = f'{msg}\nhed: {hed}'
            msg = f'{msg}\nhld: {hld}'
            msg = f'{msg}\nhse: {hse}'
            msg = f'{msg}\nhsl: {hsl}'
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Update the GPS group to include a datasets for DATETAG and TIMETAG2
        for gp in root.groups:
            if gp.id.startswith("GP"):
                gpsGroup = gp
            # Need year-gang and sometimes Datetag from one of the sensors
            if gp.id.startswith("HSE"):
                esDateTag = gp.datasets["DATETAG"].columns["NONE"]                
                esTimeTag2 = gp.datasets["TIMETAG2"].columns["NONE"]
                esSec = []
                for time in esTimeTag2:
                    esSec.append(Utilities.timeTag2ToSec(time))

        gpsGroup.addDataset("DATETAG")
        gpsGroup.addDataset("TIMETAG2")
        gpsTime = gpsGroup.datasets["UTCPOS"].columns["NONE"]
        # One case for GPRMC input...
        if gpsGroup.id.startswith("GPRMC"):
            gpsDate = gpsGroup.datasets["DATE"].columns["NONE"]
            # Obtain year-gang from Es data
            year = int(str(esDateTag[0])[0:4])
            gpsDateTag = []
            gpsTimeTag2 = []
            for date in gpsDate:
                gpsDateTag.append(Utilities.datetime2DateTag(Utilities.gpsDateToDatetime(year,date)))
            for i, time in enumerate(gpsTime):
                dtDate = Utilities.dateTagToDateTime(gpsDateTag[i])
                gpsTimeTag2.append(Utilities.datetime2TimeTag2(Utilities.utcToDateTime(dtDate,time)))
            gpsGroup.datasets["DATETAG"].columns["NONE"] = gpsDateTag
            gpsGroup.datasets["TIMETAG2"].columns["NONE"] = gpsTimeTag2
        
        # Another case for GPGGA input...
        if gpsGroup.id.startswith("GPGGA"):
            # No date is provided in GPGGA, need to find nearest time in Es and take the Datetag from Es
            ''' Catch-22. In order to covert the gps time, we need the year and day, which GPGGA does not have. 
                To get these, could compare to find the nearest DATETAG in Es. In order to compare the gps time
                to the Es time to find the nearest, I would need to convert them to datetimes ... which would 
                require the year and day. Instead, I use either the first or last Datetag from Es, depending
                on whether UTC 00:00 was crossed.'''
            # If the date does not change in Es, then no problem, use the Datetag of Es first element.
            # Otherwise, change the datetag at noon by one day 
            gpsDateTag = []
            gpsTimeTag2 = []
            
            if esDateTag[0] != esDateTag[-1]:
                msg = "ProcessL1a.processL1a: Warning: File crosses UTC 00:00. Adjusting timestamps for matchup of Datetag."
                print(msg)
                Utilities.writeLogFile(msg)
                newDay = False
                for time in gpsTime:                    
                    gpsSec = Utilities.utcToSec(time)
                    if not 'gpsSecPrior' in locals():
                        gpsSecPrior = gpsSec
                    # Test for a change of ~24 hrs between this sample and the last sample
                    # To cross 0, gpsSecPrior would need to be approaching 86400 seconds
                    # In that case, take the final Es Datetag
                    if (gpsSecPrior - gpsSec) > 86000:
                        # Once triggered the first time, this will remain true for remainder of file
                        newDay = True
                    if newDay == True:
                        gpsDateTag.append(esDateTag[-1])
                        dtDate = Utilities.dateTagToDateTime(esDateTag[-1])
                        gpsTimeTag2.append(Utilities.datetime2TimeTag2(Utilities.utcToDateTime(dtDate,time)))
                    else:
                        gpsDateTag.append(esDateTag[0])
                        dtDate = Utilities.dateTagToDateTime(esDateTag[0])
                        gpsTimeTag2.append(Utilities.datetime2TimeTag2(Utilities.utcToDateTime(dtDate,time)))
                    gpsSecPrior = gpsSec
            else:
                for time in gpsTime:
                    gpsDateTag.append(esDateTag[0])
                    dtDate = Utilities.dateTagToDateTime(esDateTag[0])
                    gpsTimeTag2.append(Utilities.datetime2TimeTag2(Utilities.utcToDateTime(dtDate,time)))

            gpsGroup.datasets["DATETAG"].columns["NONE"] = gpsDateTag
            gpsGroup.datasets["TIMETAG2"].columns["NONE"] = gpsTimeTag2        

        # Converts gp.columns to numpy array
        for gp in root.groups:
            if gp.id.startswith("SATMSG"): # Don't convert these strings to datasets.
                for ds in gp.datasets.values():
                    ds.columnsToDataset()
            else:
                for ds in gp.datasets.values():
                    if not ds.columnsToDataset():                                                
                        msg = "ProcessL1a.processL1a: Essential column cannot be converted to Dataset. Aborting."
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return None

        return root
