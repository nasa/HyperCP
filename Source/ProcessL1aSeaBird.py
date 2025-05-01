'''Process Raw (L0) data to L1A HDF5'''
import collections
import datetime as dt
import os
import numpy as np

from Source.HDFRoot import HDFRoot
from Source.HDFGroup import HDFGroup
from Source.MainConfig import MainConfig
from Source.Utilities import Utilities
from Source.RawFileReader import RawFileReader
from Source.ConfigFile import ConfigFile


class ProcessL1aSeaBird:
    '''Process L1A for SeaBird'''
    @staticmethod
    def processL1a(fp, calibrationMap):
        (_, fileName) = os.path.split(fp)

        # Generate root attributes
        root = HDFRoot()
        root.id = "/"
        if os.environ['HYPERINSPACE_CMD'].lower() == 'true': # os.environ must be string
            MainConfig.loadConfig('cmdline_main.config','version')
        else:
            MainConfig.loadConfig('main.config','version')
        root.attributes["HYPERINSPACE"] = MainConfig.settings["version"]
        root.attributes["CAL_FILE_NAMES"] = ','.join(calibrationMap.keys())
        root.attributes["WAVELENGTH_UNITS"] = "nm"
        root.attributes["LI_UNITS"] = "count"
        root.attributes["LT_UNITS"] = "count"
        root.attributes["ES_UNITS"] = "count"
        root.attributes["SATPYR_UNITS"] = "count"
        root.attributes["RAW_FILE_NAME"] = fileName
        root.attributes["PROCESSING_LEVEL"] = "1a"

        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        root.attributes["FILE_CREATION_TIME"] = timestr
        # SZA Filter configuration parameter added to attributes below

        msg = f"ProcessL1a.processL1a: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        contextMap = collections.OrderedDict()

        for key in calibrationMap:
            cf = calibrationMap[key]
            gp = HDFGroup()
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
            # Don't add contexts that did not match any data in RawFileReader
            if 'CalFileName' not in gp.attributes:
                continue
            gp.attributes["InstrumentType"] = cf.instrumentType
            gp.attributes["Media"] = cf.media
            gp.attributes["MeasMode"] = cf.measMode
            gp.attributes["FrameType"] = cf.frameType
            gp.getTableHeader(cf.sensorType)
            gp.attributes["DISTANCE_1"] = "Pressure " + cf.sensorType + " 1 1 0"
            gp.attributes["DISTANCE_2"] = "Surface " + cf.sensorType + " 1 1 0"
            gp.attributes["SensorDataList"] = ", ".join(list(gp.datasets.keys()))
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
        # if hld != 2 or hsl != 2 or hse != 1 or hed != 1 or gps != 1:
        if hld != 2 or hsl != 2 or hse != 1 or hed != 1:
            msg = "ProcessL1a.processL1a: Essential dataset missing. Check your configuration calibration files match cruise setup. Aborting."
            msg = f'{msg}\ngps: {gps} :0'
            msg = f'{msg}\nhed: {hed} :1'
            msg = f'{msg}\nhld: {hld} :2'
            msg = f'{msg}\nhse: {hse} :1'
            msg = f'{msg}\nhsl: {hsl} :2'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        # No GPS workaround
        if gps != 1:
            msg = "ProcessL1a.processL1a: GPS data missing from raw file. Will attempt to use ancillary data"
            print(msg)
            Utilities.writeLogFile(msg)

        # Update the GPS group to include a datasets for DATETAG and TIMETAG2
        gpsGroup = None
        esDateTag = None
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

        if gps == 1:
            gpsGroup.addDataset("DATETAG")
            gpsGroup.addDataset("TIMETAG2")
            if "UTCPOS" in gpsGroup.datasets:
                gpsTime = gpsGroup.datasets["UTCPOS"].columns["NONE"]
            elif "TIME" in gpsGroup.datasets:
                # prepSAS output
                gpsTime = gpsGroup.datasets["TIME"].columns["UTC"]
            else:
                msg ='Failed to import GPS data.'
                print(msg)
                Utilities.writeLogFile(msg)
                return None

            # Another case for GPGGA input...
            if gpsGroup.id.startswith("GPGGA"):
                # No date is provided in GPGGA, need to find nearest time in Es and take the Datetag from Es
                # NOTE: Catch-22. To covert the gps time, we need the year and day, which GPGGA does not have.
                # To get these, could compare to find the nearest DATETAG in Es. In order to compare the gps time
                # to the Es time to find the nearest, need to convert them to datetimes ... which would
                # require the year and day. Instead, I use either the first or last Datetag from Es, depending
                # on whether UTC 00:00 was crossed.
                # If the date does not change in Es, then no problem, use the Datetag of Es first element.
                # Otherwise, change the datetag at midnight by one day
                gpsDateTag = []
                gpsTimeTag2 = []

                if esDateTag[0] != esDateTag[-1]:
                    msg = "ProcessL1a.processL1a: Warning: File crosses UTC 00:00. Adjusting timestamps for matchup of Datetag."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    newDay = False
                    for time in gpsTime:
                        gpsSec = Utilities.utcToSec(time)
                        if 'gpsSecPrior' not in locals():
                            gpsSecPrior = gpsSec
                        # Test for a change of ~24 hrs between this sample and the last sample
                        # To cross 0, gpsSecPrior would need to be approaching 86400 seconds
                        # In that case, take the final Es Datetag
                        if (gpsSecPrior - gpsSec) > 86000:
                            # Once triggered the first time, this will remain true for remainder of file
                            newDay = True
                        if newDay is True:
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
            if not gp.id.startswith("SATMSG"): # Don't convert these strings to datasets.
                for ds in gp.datasets.values():
                    if not ds.columnsToDataset():
                        msg = "ProcessL1a.processL1a: Essential column cannot be converted to Dataset. Aborting."
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return None

        try:
            root  = Utilities.rootAddDateTime(root)
        except AttributeError as err:
            msg = f"ProcessL1a.processL1a: Cannot add datetime to a group dataset: {err}. Aborting."
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Adjust to UTC if necessary
        if ConfigFile.settings["fL1aUTCOffset"] != 0:
            # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
            root = Utilities.SASUTCOffset(root)

        # Apply SZA filter; Currently only works with SunTracker data at L1A (again possible in L2 for all types)
        if ConfigFile.settings["bL1aCleanSZA"]:
            root.attributes['SZA_FILTER_L1A'] = ConfigFile.settings["fL1aCleanSZAMax"]
            for gp in root.groups:
                # try:
                if 'FrameTag' in gp.attributes:
                    if gp.attributes["FrameTag"].startswith("SATNAV") or gp.attributes["FrameTag"].startswith("UMTWR"):
                        elevData = gp.getDataset("ELEVATION")
                        elevation = elevData.data.tolist()
                        szaLimit = float(ConfigFile.settings["fL1aCleanSZAMax"])

                        # NOTE: It would be good to add local time as a printed output with SZA
                        if (90-np.nanmax(elevation)) > szaLimit:
                            msg = f'SZA too low. Discarding entire file. {round(90-np.nanmax(elevation))}'
                            print(msg)
                            Utilities.writeLogFile(msg)
                            return None
                        else:
                            if np.isnan(elevation).all():
                                msg = 'SZA: elevation all NaNs.'
                            else:
                                msg = f'SZA passed filter: {round(90-np.nanmax(elevation))}'
                            print(msg)
                            Utilities.writeLogFile(msg)

                else:
                    print(f'No FrameTag in {gp.id} group')

        # DATETIME is not supported in HDF5; remove
        if root is not None:
            for gp in root.groups:
                if gp.id != "SOLARTRACKER_STATUS" and gp.id != "SATMSG.tdf":
                    del gp.datasets["DATETIME"]

        return root
