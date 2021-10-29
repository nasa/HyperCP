
import math
import datetime
import numpy as np
from pysolar.solar import get_azimuth, get_altitude
from operator import add
import bisect

from HDFDataset import HDFDataset
from Utilities import Utilities
from ConfigFile import ConfigFile

class ProcessL1c:

    @staticmethod
    def filterData(group, badTimes):
        ''' Delete flagged records '''

        msg = f'Remove {group.id} Data'
        print(msg)
        Utilities.writeLogFile(msg)

        timeStamp = group.getDataset("DATETIME").data

        startLength = len(timeStamp)
        msg = f'   Length of dataset prior to removal {startLength} long'
        print(msg)
        Utilities.writeLogFile(msg)

        # Delete the records in badTime ranges from each dataset in the group
        finalCount = 0
        originalLength = len(timeStamp)
        for dateTime in badTimes:
            # Need to reinitialize for each loop
            startLength = len(timeStamp)
            newTimeStamp = []

            start = dateTime[0]
            stop = dateTime[1]

            # msg = f'Eliminate data between: {dateTime}'
            # print(msg)
            # Utilities.writeLogFile(msg)

            if startLength > 0:
                counter = 0
                for i in range(startLength):
                    if start <= timeStamp[i] and stop >= timeStamp[i]:
                        group.datasetDeleteRow(i - counter)  # Adjusts the index for the shrinking arrays
                        counter += 1
                        finalCount += 1
                    else:
                        newTimeStamp.append(timeStamp[i])
            else:
                msg = 'Data group is empty. Continuing.'
                print(msg)
                Utilities.writeLogFile(msg)
            timeStamp = newTimeStamp.copy()

        msg = f'   Length of records removed from dataset: {finalCount}'
        print(msg)
        Utilities.writeLogFile(msg)

        return finalCount/originalLength

    @staticmethod
    def processL1c(node, ancillaryData=None):
        '''
        Filters data for pitch, roll, yaw, and rotator.
        '''

        node.attributes["PROCESSING_LEVEL"] = "1c"
        now = datetime.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr

        # Add configuration parameters (L1C) to root/node attributes
        if ConfigFile.settings['bL1cSolarTracker']:
            node.attributes['SOLARTRACKER'] = 'YES'

        if ConfigFile.settings['bL1cCleanPitchRoll']:
            node.attributes['PITCH_ROLL_FILTER'] = ConfigFile.settings['fL1cPitchRollPitch']
        node.attributes['HOME_ANGLE'] = ConfigFile.settings['fL1cRotatorHomeAngle']
        node.attributes['ROTATOR_DELAY_FILTER'] = ConfigFile.settings['fL1cRotatorDelay']
        if ConfigFile.settings['bL1cRotatorAngle']:
            node.attributes['ROT_ANGLE_MIN'] = ConfigFile.settings['fL1cRotatorAngleMin']
            node.attributes['ROT_ANGLE_MAX'] = ConfigFile.settings['fL1cRotatorAngleMax']
        if ConfigFile.settings['bL1cCleanSunAngle']:
            node.attributes['RELATIVE_AZIMUTH_MIN'] = ConfigFile.settings['fL1cSunAngleMin']
            node.attributes['RELATIVE_AZIMUTH_MAX'] = ConfigFile.settings['fL1cSunAngleMax']

        msg = f"ProcessL1c.processL1c: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        node  = Utilities.rootAddDateTime(node)

        # 2021-04-09: Include ANCILLARY_METADATA in all datasets, regardless of whether they are SOLARTRACKER or not

        for gp in node.groups:
            if gp.id.startswith("GP"):
                gpsDateTime = gp.getDataset("DATETIME").data
                gpsLat = gp.getDataset('LATPOS')
                latHemiData = gp.getDataset("LATHEMI")
                gpsLon = gp.getDataset('LONPOS')
                lonHemiData = gp.getDataset("LONHEMI")

        # If ancillary file is provided, use it. Otherwise fill in what you can using the datetime, lat, lon from GPS
        if ancillaryData is not None:
            ancDateTime = ancillaryData.columns["DATETIME"][0].copy()

            # Remove all ancillary data that does not intersect GPS data
            print('Removing non-pertinent ancillary data.')
            lower = bisect.bisect_left(ancDateTime, min(gpsDateTime))
            lower = list(range(0,lower))
            upper = bisect.bisect_right(ancDateTime, max(gpsDateTime))
            upper = list(range(upper,len(ancDateTime)))
            ancillaryData.colDeleteRow(upper)
            ancillaryData.colDeleteRow(lower)

            # Test if any data is left
            if not ancillaryData.columns["DATETIME"][0]:
                msg = "No coincident ancillary data found. Check ancillary file. Aborting"
                print(msg)
                Utilities.writeLogFile(msg)
                return None

            # Reinitialize with new, smaller dataset
            ''' Essential ancillary data for non-SolarTracker file includes
                lat, lon, datetime, ship heading and offset between bow and
                SAS instrument from which SAS azimuth is calculated '''
            timeStamp = ancillaryData.columns["DATETIME"][0]
            ancTimeTag2 = [Utilities.datetime2TimeTag2(dt) for dt in timeStamp]
            ancDateTag = [Utilities.datetime2DateTag(dt) for dt in timeStamp]
            lat = ancillaryData.columns["LATITUDE"][0]
            lon = ancillaryData.columns["LONGITUDE"][0]

            # if "SHIPAZIMUTH" in ancillaryData.columns:
            if "HEADING" in ancillaryData.columns:
                # HEADING/shipAzimuth comes from ancillary data file here (not GPS or SATNAV)
                shipAzimuth = ancillaryData.columns["HEADING"][0]
                if "HOMEANGLE" in ancillaryData.columns:
                    homeAngle = ancillaryData.columns["HOMEANGLE"][0]
                    for i, offset in enumerate(homeAngle):
                        if offset > 180:
                            homeAngle[i] = offset-360
                    sasAzimuth = list(map(add, shipAzimuth, homeAngle))
                else:
                    if ConfigFile.settings['bL1cSolarTracker'] == 0:
                        msg = 'Required ancillary metadata for sensor offset missing. Abort.'
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return None
            else:
                if ConfigFile.settings['bL1cSolarTracker'] == 0:
                    msg = 'Required ancillary metadata for ship heading missing. Abort.'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return None
            if "STATION" in ancillaryData.columns:
                station = ancillaryData.columns["STATION"][0]
            if "SALINITY" in ancillaryData.columns:
                salt = ancillaryData.columns["SALINITY"][0]
            if "SST" in ancillaryData.columns:
                sst = ancillaryData.columns["SST"][0]
            if "WINDSPEED" in ancillaryData.columns:
                wind = ancillaryData.columns["WINDSPEED"][0]
            if "AOD" in ancillaryData.columns:
                aod = ancillaryData.columns["AOD"][0]
            if "CLOUD" in ancillaryData.columns:
                cloud = ancillaryData.columns["CLOUD"][0]
            if "WAVE_HT" in ancillaryData.columns:
                wave = ancillaryData.columns["WAVE_HT"][0]
            if "SPEED_F_W" in ancillaryData.columns:
                speed_f_w = ancillaryData.columns["SPEED_F_W"][0]
            if "PITCH" in ancillaryData.columns:
                pitch = ancillaryData.columns["PITCH"][0]
            if "ROLL" in ancillaryData.columns:
                roll = ancillaryData.columns["ROLL"][0]

        else:
            # 2021-08-20: Create an ancillary group from GPS regardless of whether an external file is provided
            # Generate HDFDataset
            ancillaryData = HDFDataset()
            ancillaryData.id = "AncillaryData"

            timeStamp = gpsDateTime
            ancillaryData.appendColumn("DATETIME", timeStamp)

            ancTimeTag2 = [Utilities.datetime2TimeTag2(dt) for dt in timeStamp]
            ancDateTag = [Utilities.datetime2DateTag(dt) for dt in timeStamp]

            lat = []
            lon = []
            for i in range(gpsLat.data.shape[0]):
                latDM = gpsLat.data["NONE"][i]
                latDirection = latHemiData.data["NONE"][i]
                latDD = Utilities.dmToDd(latDM, latDirection)
                lonDM = gpsLon.data["NONE"][i]
                lonDirection = lonHemiData.data["NONE"][i]
                lonDD = Utilities.dmToDd(lonDM, lonDirection)
                lat.append(latDD)
                lon.append(lonDD)

            ancillaryData.appendColumn("LATITUDE", lat)
            ancillaryData.attributes["LATITUDE_Units"]='degrees'
            ancillaryData.appendColumn("LONGITUDE", lon)
            ancillaryData.attributes["LONGITUDE_Units"]='degrees'

        # Run Pysolar to obtain solar geometry. These may be redundant with SolarTracker values
        sunAzimuthAnc = []
        sunZenith = []
        for i, dt_utc in enumerate(timeStamp):
            sunAzimuthAnc.append(get_azimuth(lat[i],lon[i],dt_utc,0))
            sunZenith.append(90 - get_altitude(lat[i],lon[i],dt_utc,0))

        #############################################################################################
        ''' Begin Filtering '''
        #############################################################################################

        badTimes = None
        # Apply Pitch & Roll Filter
        # This has to record the time interval (in datetime) for the bad angles in order to remove these time intervals
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.

        if node is not None and int(ConfigFile.settings["bL1cCleanPitchRoll"]) == 1:
            msg = "Filtering file for high pitch and roll"
            print(msg)
            Utilities.writeLogFile(msg)

            # Preferentially read PITCH and ROLL from SolarTracker/pySAS THS sensor...
            pitch = None
            roll = None
            gp  = None
            for group in node.groups:
                if group.id == "SOLARTRACKER":
                    gp = group
                    timeStamp = gp.getDataset("DATETIME").data
                    if "PITCH" in gp.datasets:
                        pitch = gp.getDataset("PITCH").data["SAS"]
                    if "ROLL" in gp.datasets:
                        roll = gp.getDataset("ROLL").data["SAS"]
                if group.id.startswith('SATTHS'): # For SATTHS without SolarTracker (i.e. with pySAS)
                    gp = group
                    timeStamp = gp.getDataset("DATETIME").data
                    if "PITCH" in gp.datasets:
                        pitch = gp.getDataset("PITCH").data["NONE"]
                    if "ROLL" in gp.datasets:
                        roll = gp.getDataset("ROLL").data["NONE"]
            # ...and failing that, try to pull from ancillary data
            if pitch is None or roll is None:
                if "PITCH" in ancillaryData.columns:
                    msg = "Pitch data from ancillary file used."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    pitch = ancillaryData.columns["PITCH"][0]
                    if "ROLL" in ancillaryData.columns:
                        msg = "Roll data from ancillary file used."
                        print(msg)
                        Utilities.writeLogFile(msg)
                        roll = ancillaryData.columns["ROLL"][0]
                    timeStamp = ancillaryData.columns["DATETIME"][0]
                else:
                    msg = "Pitch and roll data not found for tilt filter. Aborting."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return None

            pitchMax = float(ConfigFile.settings["fL1cPitchRollPitch"])
            rollMax = float(ConfigFile.settings["fL1cPitchRollRoll"])

            if badTimes is None:
                badTimes = []

            # timeStamp may now align with ancillary file or radiometry platform, but this should not matter
            # since it will align with pitch/roll, and will be applied by value not index to all data (i.e. startstop are
            # python datetimes).
            i = 0
            start = -1
            stop =[]
            for index in range(len(pitch)):
                if abs(pitch[index]) > pitchMax or abs(roll[index]) > rollMax:
                    i += 1
                    if start == -1:
                        # print('Pitch or roll angle outside bounds. Pitch: ' + str(round(pitch[index])) + ' Roll: ' +str(round(pitch[index])))
                        start = index
                    stop = index
                else:
                    if start != -1:
                        # print('Pitch or roll angle passed. Pitch: ' + str(round(pitch[index])) + ' Roll: ' +str(round(pitch[index])))
                        startstop = [timeStamp[start],timeStamp[stop]]
                        msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
                        # print(msg)
                        Utilities.writeLogFile(msg)
                        badTimes.append(startstop)
                        start = -1
            msg = f'Percentage of data out of Pitch/Roll bounds: {round(100*i/len(timeStamp))} %'
            print(msg)
            Utilities.writeLogFile(msg)

            if start != -1 and stop == index: # Records from a mid-point to the end are bad
                startstop = [timeStamp[start],timeStamp[stop]]
                msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]} (HHMMSSMSS)'
                # print(msg)
                Utilities.writeLogFile(msg)
                if badTimes is None: # only one set of records
                    badTimes = [startstop]
                else:
                    badTimes.append(startstop)

            if start==0 and stop==index: # All records are bad
                return None


        # Apply Rotator Delay Filter (delete records within so many seconds of a rotation)
        # This has to record the time interval (TT2) for the bad angles in order to remove these time intervals
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.
        if node is not None and ConfigFile.settings["bL1cRotatorDelay"] and ConfigFile.settings["bL1cSolarTracker"]:
            gp = None
            for group in node.groups:
                if group.id == "SOLARTRACKER" or group.id == "SOLARTRACKER_UM":
                    gp = group

            if 'gp' in locals():
                if gp.getDataset("POINTING"):
                    timeStamp = gp.getDataset("DATETIME").data
                    rotator = gp.getDataset("POINTING").data["ROTATOR"]
                    # Rotator Home Angle Offset is generally set in the .sat file when setting up the SolarTracker
                    # It may also be set for when no SolarTracker is present and it's not included in the
                    # ancillary data, but that's not relevant here...
                    home = float(ConfigFile.settings["fL1cRotatorHomeAngle"])
                    delay = float(ConfigFile.settings["fL1cRotatorDelay"])

                    # if node is not None and int(ConfigFile.settings["bL1cRotatorDelay"]) == 1:
                    msg = "Filtering file for Rotator Delay"
                    print(msg)
                    Utilities.writeLogFile(msg)

                    if badTimes is None:
                        badTimes = []

                    kickout = 0
                    i = 0
                    for index in range(len(rotator)):
                        if index == 0:
                            lastAngle = rotator[index]
                        else:
                            if rotator[index] > (lastAngle + 0.05) or rotator[index] < (lastAngle - 0.05):
                                i += 1
                                # Detect angle changed
                                start = timeStamp[index]
                                # print('Rotator delay kick-out. ' + str(timeInt) )
                                startIndex = index
                                lastAngle = rotator[index]
                                kickout = 1

                            else:
                                # Test if this is fL1cRotatorDelay seconds past a kick-out start
                                time = timeStamp[index]
                                if kickout==1 and time > (start + datetime.timedelta(0,delay)):
                                    # startstop = [timeStampTuple[startIndex],timeStampTuple[index-1]]
                                    startstop = [timeStamp[startIndex],timeStamp[index-1]]
                                    msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
                                    # print(msg)
                                    Utilities.writeLogFile(msg)
                                    badTimes.append(startstop)
                                    kickout = 0
                                elif kickout ==1:
                                    i += 1

                    msg = f'Percentage of SolarTracker data out of Rotator Delay bounds: {round(100*i/len(timeStamp))} %'
                    print(msg)
                    Utilities.writeLogFile(msg)

                else:
                    msg = f'No POINTING data found. Filtering on rotator delay failed.'
                    print(msg)
                    Utilities.writeLogFile(msg)


        # Apply Absolute Rotator Angle Filter
        # This has to record the time interval (TT2) for the bad angles in order to remove these time intervals
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.
        if node is not None and ConfigFile.settings["bL1cSolarTracker"] and ConfigFile.settings["bL1cRotatorAngle"]:
            msg = "Filtering file for bad Absolute Rotator Angle"
            print(msg)
            Utilities.writeLogFile(msg)

            i = 0
            # try:
            gp = None
            for group in node.groups:
                if group.id == "SOLARTRACKER" or group.id == "SOLARTRACKER_UM":
                    gp = group

            if gp.getDataset("POINTING"):
                timeStamp = gp.getDataset("DATETIME").data
                rotator = gp.getDataset("POINTING").data["ROTATOR"]
                # Rotator Home Angle Offset is generally set in the .sat file when setting up the SolarTracker
                # It may also be set for when no SolarTracker is present and it's not included in the
                # ancillary data, but that's not relevant here
                home = float(ConfigFile.settings["fL1cRotatorHomeAngle"])

                absRotatorMin = float(ConfigFile.settings["fL1cRotatorAngleMin"])
                absRotatorMax = float(ConfigFile.settings["fL1cRotatorAngleMax"])

                if badTimes is None:
                    badTimes = []

                start = -1
                stop = []
                for index in range(len(rotator)):
                    if rotator[index] + home > absRotatorMax or rotator[index] + home < absRotatorMin or math.isnan(rotator[index]):
                        i += 1
                        if start == -1:
                            # print('Absolute rotator angle outside bounds. ' + str(round(rotator[index] + home)))
                            start = index
                        stop = index
                    else:
                        if start != -1:
                            # print('Absolute rotator angle passed: ' + str(round(rotator[index] + home)))
                            startstop = [timeStamp[start],timeStamp[stop]]
                            msg = ('   Flag data from TT2: ' + str(startstop[0]) + ' to ' + str(startstop[1]) + '(HHMMSSMSS)')
                            # print(msg)
                            Utilities.writeLogFile(msg)

                            badTimes.append(startstop)
                            start = -1
                msg = f'Percentage of SolarTracker data out of Absolute Rotator bounds: {round(100*i/len(timeStamp))} %'
                print(msg)
                Utilities.writeLogFile(msg)

                if start != -1 and stop == index: # Records from a mid-point to the end are bad
                    startstop = [timeStamp[start],timeStamp[stop]]
                    msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
                    # print(msg)
                    Utilities.writeLogFile(msg)
                    if badTimes is None: # only one set of records
                        badTimes = [startstop]
                    else:
                        badTimes.append(startstop)

                if start==0 and stop==index: # All records are bad
                    return None
            else:
                msg = f'No rotator data found. Filtering on absolute rotator angle failed.'
                print(msg)
                Utilities.writeLogFile(msg)

        # General setup for ancillary or SolarTracker data prior to Relative Solar Azimuth option
        if ConfigFile.settings["bL1cSolarTracker"]:
            gp = None
            for group in node.groups:
                    if group.id == "SOLARTRACKER" or group.id == "SOLARTRACKER_UM":
                        gp = group
            if gp.getDataset("AZIMUTH") and gp.getDataset("HEADING") and gp.getDataset("POINTING"):
                timeStamp = gp.getDataset("DATETIME").data
                # Rotator Home Angle Offset is generally set in the .sat file when setting up the SolarTracker
                # It may also be set here for when no SolarTracker is present and it's not included in the
                # ancillary data. See below.
                home = float(ConfigFile.settings["fL1cRotatorHomeAngle"])
                sunAzimuth = gp.getDataset("AZIMUTH").data["SUN"]
                if gp.id == "SOLARTRACKER":
                    sasAzimuth = gp.getDataset("HEADING").data["SAS_TRUE"]
                elif gp.id == "SOLARTRACKER_UM":
                    sasAzimuth = gp.getDataset("HEADING").data["SAS"]
                newRelAzData = gp.addDataset("REL_AZ")
            else:
                    msg = f"No rotator, solar azimuth, and/or ship'''s heading data found. Filtering on relative azimuth not added."
                    print(msg)
                    Utilities.writeLogFile(msg)
        else:
            if ancillaryData is not None:
                sunAzimuth = sunAzimuthAnc
            else:
                print('ERROR: No ancillary file provided. Ancillary data is required if SolarTracker or pySAS is not in use. Abort.')
                return None

        relAz=[]
        for index in range(len(sunAzimuth)):
            if ConfigFile.settings["bL1cSolarTracker"]:
                # Changes in the angle between the bow and the sensor changes are tracked by SolarTracker
                # This home offset is generally set in .sat file in the field, but can be updated here with
                # the value from the Configuration Window (L1C)
                offset = home
            else:
                # Changes in the angle between the bow and the sensor changes are tracked in ancillary data
                offset = homeAngle[index]

            # Check for angles spanning north
            if sunAzimuth[index] > sasAzimuth[index]: # sasAzimuth is now accurate regardless of SolarTracker or NoTracker
                hiAng = sunAzimuth[index]
                loAng = sasAzimuth[index] + offset
            else:
                hiAng = sasAzimuth[index] + offset
                loAng = sunAzimuth[index]
            # Choose the smallest angle between them
            if hiAng-loAng > 180:
                relAzimuthAngle = 360 - (hiAng-loAng)
            else:
                relAzimuthAngle = hiAng-loAng

            relAz.append(relAzimuthAngle)

        # In case there is no SolarTracker to provide sun/sensor geometries, Pysolar will be used
        # to estimate sun zenith and azimuth using GPS position and time, and sensor azimuth will
        # come from ancillary data input. For SolarTracker and pySAS, SZA and solar azimuth go in the
        # SOLARTRACKER or SOLARTRACKER_UM group, otherwise in the ANCILLARY group.

        # Initialize a new group to host the unconventional ancillary data
        ancGroup = node.addGroup("ANCILLARY_METADATA")
        # If using a SolarTracker or pySAS, add RelAz to the SATNAV/SOLARTRACKER group...
        if ConfigFile.settings["bL1cSolarTracker"]:
            newRelAzData.columns["REL_AZ"] = relAz
            newRelAzData.columnsToDataset()
        else:
        #... otherwise populate the ancGroup
            ancGroup.addDataset("REL_AZ")
            ancGroup.datasets["REL_AZ"].data = np.array(relAz, dtype=[('NONE', '<f8')])
            ancGroup.attributes["REL_AZ_Units"]='degrees'

        # Now including the remaining ancillary data in ancGroup with or w/out SolarTracker
        ancGroup.addDataset("LATITUDE")
        ancGroup.datasets["LATITUDE"].data = np.array(lat, dtype=[('NONE', '<f8')])
        ancGroup.addDataset("LONGITUDE")
        ancGroup.datasets["LONGITUDE"].data = np.array(lon, dtype=[('NONE', '<f8')])
        ancGroup.addDataset("TIMETAG2")
        ancGroup.datasets["TIMETAG2"].data = np.array(ancTimeTag2, dtype=[('NONE', '<f8')])
        ancGroup.addDataset("DATETAG")
        ancGroup.datasets["DATETAG"].data = np.array(ancDateTag, dtype=[('NONE', '<f8')])
        ancGroup.addDataset("SOLAR_AZ")
        ancGroup.attributes["SOLAR_AZ_Units"]='degrees'
        ancGroup.datasets["SOLAR_AZ"].data = np.array(sunAzimuthAnc, dtype=[('NONE', '<f8')])
        ancGroup.addDataset("SZA")
        ancGroup.datasets["SZA"].data = np.array(sunZenith, dtype=[('NONE', '<f8')])
        ancGroup.attributes["SZA_Units"]='degrees'

        dateTime = ancGroup.addDataset("DATETIME")
        timeData = ancGroup.getDataset("TIMETAG2").data["NONE"].tolist()
        dateTag = ancGroup.getDataset("DATETAG").data["NONE"].tolist()
        timeStampAnc = []
        for i, time in enumerate(timeData):
            # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
            # Filter for aberrant Datetags
            if str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20"):
                dt = Utilities.dateTagToDateTime(dateTag[i])
                timeStampAnc.append(Utilities.timeTag2ToDateTime(dt, time))
            else:
                ancGroup.datasetDeleteRow(i)
                msg = "Bad Datetag found in ancillary. Eliminating record"
                print(msg)
                Utilities.writeLogFile(msg)
        dateTime.data = timeStampAnc

        # For non-SolarTracker datasets, define the timeStamp around the ancillary data
        # Otherwise, it was already defined above
        if ConfigFile.settings['bL1cSolarTracker']==0:
            # Convert datetimes
            timeStamp = timeStampAnc

        # Look for additional datasets in provided ancillaryData and populate the new ancillary group
        if ancillaryData is not None:
            ancGroup.attributes = ancillaryData.attributes.copy()
            ancGroup.attributes["FrameType"] = "Not Required"
            if "HEADING" in ancillaryData.columns:
                ancGroup.addDataset("HEADING")
                ancGroup.datasets["HEADING"].data = np.array(shipAzimuth, dtype=[('NONE', '<f8')])
            if "STATION" in ancillaryData.columns:
                ancGroup.addDataset("STATION")
                ancGroup.datasets["STATION"].data = np.array(station, dtype=[('NONE', '<f8')])
            if "SALINITY" in ancillaryData.columns:
                ancGroup.addDataset("SALINITY")
                ancGroup.datasets["SALINITY"].data = np.array(salt, dtype=[('NONE', '<f8')])
            if "SST" in ancillaryData.columns:
                ancGroup.addDataset("SST")
                ancGroup.datasets["SST"].data = np.array(sst, dtype=[('NONE', '<f8')])
            if "WINDSPEED" in ancillaryData.columns:
                ancGroup.addDataset("WINDSPEED")
                ancGroup.datasets["WINDSPEED"].data = np.array(wind, dtype=[('NONE', '<f8')])
            if "AOD" in ancillaryData.columns:
                ancGroup.addDataset("AOD")
                ancGroup.datasets["AOD"].data = np.array(aod, dtype=[('NONE', '<f8')])
            if "CLOUD" in ancillaryData.columns:
                ancGroup.addDataset("CLOUD")
                ancGroup.datasets["CLOUD"].data = np.array(cloud, dtype=[('NONE', '<f8')])
            if "WAVE_HT" in ancillaryData.columns:
                ancGroup.addDataset("WAVE_HT")
                ancGroup.datasets["WAVE_HT"].data = np.array(wave, dtype=[('NONE', '<f8')])
            if "SPEED_F_W" in ancillaryData.columns:
                ancGroup.addDataset("SPEED_F_W")
                ancGroup.datasets["SPEED_F_W"].data = np.array(speed_f_w, dtype=[('NONE', '<f8')])
            if "PITCH" in ancillaryData.columns:
                ancGroup.addDataset("PITCH")
                ancGroup.datasets["PITCH"].data = np.array(ancillaryData.columns["PITCH"][0], dtype=[('NONE', '<f8')])
            if "ROLL" in ancillaryData.columns:
                ancGroup.addDataset("ROLL")
                ancGroup.datasets["ROLL"].data = np.array(ancillaryData.columns["ROLL"][0], dtype=[('NONE', '<f8')])

        ######################################################################################################

        # Apply Relative Azimuth filter
        # This has to record the time interval (TT2) for the bad angles in order to remove these time intervals
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.
        if node is not None and int(ConfigFile.settings["bL1cCleanSunAngle"]) == 1:
            msg = "Filtering file for bad Relative Solar Azimuth"
            print(msg)
            Utilities.writeLogFile(msg)

            i = 0
            relAzimuthMin = float(ConfigFile.settings["fL1cSunAngleMin"])
            relAzimuthMax = float(ConfigFile.settings["fL1cSunAngleMax"])

            if badTimes is None:
                badTimes = []

            start = -1
            stop = []
            # The length of relAz (and therefore the value of i) depends on whether ancillary
            #  data are used or SolarTracker data
            for index in range(len(relAz)):
                relAzimuthAngle = relAz[index]

                if relAzimuthAngle > relAzimuthMax or relAzimuthAngle < relAzimuthMin or math.isnan(relAzimuthAngle):
                    i += 1
                    if start == -1:
                        # print('Relative solar azimuth angle outside bounds. ' + str(round(relAzimuthAngle,2)))
                        start = index
                    stop = index
                else:
                    if start != -1:
                        # print('Relative solar azimuth angle passed: ' + str(round(relAzimuthAngle,2)))
                        startstop = [timeStamp[start],timeStamp[stop]]
                        msg = f'   Flag data from: {startstop[0]}  to {startstop[1]}'
                        # print(msg)
                        Utilities.writeLogFile(msg)

                        badTimes.append(startstop)
                        start = -1

            for group in node.groups:
                if group.id.startswith("GP"):
                    gp = group

            msg = f'Percentage of data out of Relative Solar Azimuth bounds: {round(100*i/len(relAz))} %'
            print(msg)
            Utilities.writeLogFile(msg)

            if start != -1 and stop == index: # Records from a mid-point to the end are bad
                startstop = [timeStamp[start],timeStamp[stop]]
                msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]} (HHMMSSMSS)'
                # print(msg)
                Utilities.writeLogFile(msg)
                if badTimes is None: # only one set of records
                    badTimes = [startstop]
                else:
                    badTimes.append(startstop)

            if start==0 and stop==index: # All records are bad
                msg = ("All records out of bounds. Aborting.")
                print(msg)
                Utilities.writeLogFile(msg)
                return None

        # For each dataset in each group, find the badTimes to remove and delete those rows
        if badTimes is not None:
            msg = "Eliminate combined filtered data from datasets.*****************************"
            print(msg)
            Utilities.writeLogFile(msg)

            for gp in node.groups:

                # SATMSG has an ambiguous timer POSFRAME.COUNT, cannot filter
                if (gp.id == "SOLARTRACKER_STATUS") is False:
                    fractionRemoved = ProcessL1c.filterData(gp, badTimes)

                    # Now test whether the overlap has eliminated all radiometric data
                    if fractionRemoved > 0.98 and (gp.id.startswith("ES") or gp.id.startswith("LI") or gp.id.startswith("LT")):
                        msg = "Radiometric data >98'%' eliminated. Aborting."
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return None

                    # Confirm that data were removed from Root
                    # group = node.getGroup(gp.id)
                    # if gp.id.startswith("GP"):
                    #     gpTimeset  = group.getDataset("UTCPOS")
                    # else:
                    gpTimeset  = gp.getDataset("TIMETAG2")

                    gpTime = gpTimeset.data["NONE"]
                    lenGpTime = len(gpTime)
                    msg = f'   Data end {lenGpTime} long, a loss of {round(100*(fractionRemoved))} %'
                    print(msg)
                    Utilities.writeLogFile(msg)

        # DATETIME is not supported in HDF5; remove
        for gp in node.groups:
            if (gp.id == "SOLARTRACKER_STATUS") is False:
                del gp.datasets["DATETIME"]

        return node
