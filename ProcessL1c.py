
import math
import numpy as np
from pysolar.solar import get_azimuth, get_altitude
import pytz
from operator import add

import HDFRoot

from Utilities import Utilities
from ConfigFile import ConfigFile

class ProcessL1c:

    # Delete records within the out-of-bounds times found by filtering on relative solar angle
    # Or records within the out-of-bounds for absolute rotator angle.
    @staticmethod
    def filterData(group, badTimes):                    
        
        ''' BUG: This could cause problems if the data to be filtered spam UTC noon. Needs to be updated
        to use datetimes rather than seconds of the day. '''

        # Convert all time stamps to milliseconds UTC
        if group.id.startswith("GP"):
            # This is handled seperately in order to deal with the UTC fields in GPS            
            msg = "   Remove GPS Data"
            print(msg)
            Utilities.writeLogFile(msg)

            gpsTimeData = group.getDataset("UTCPOS")        
            dataSec = []
            for i in range(gpsTimeData.data.shape[0]):
                # Screen raw GPS UTCPOS data for NaN (ECOA-1)
                if not np.isnan(gpsTimeData.data["NONE"][i]):

                    ''' To get datetime from GPS UTC, will need date of each record,
                    which is not included in the GPS datastream '''
                    
                    # UTC format (hhmmss.) similar to TT2 (hhmmssmss.) with the miliseconds truncated
                    dataSec.append(Utilities.utcToSec(gpsTimeData.data["NONE"][i]))               
        else:
            msg = f'   Remove {group.id} Data'
            print(msg)
            Utilities.writeLogFile(msg)
            timeData = group.getDataset("TIMETAG2")        
            dataSec = []
            for i in range(timeData.data.shape[0]):
                # Converts from TT2 (hhmmssmss. UTC) to milliseconds UTC
                dataSec.append(Utilities.timeTag2ToSec(timeData.data["NONE"][i])) 

        startLength = len(dataSec) # Length of either GPS UTCPOS or TimeTag2
        msg = ('   Length of dataset prior to removal ' + str(startLength) + ' long')
        print(msg)
        Utilities.writeLogFile(msg)
            
        # Now delete the record from each dataset in the group
        finalCount = 0
        originalLength = len(dataSec)
        
        for timeTag in badTimes:     
            # Need to reinitialize for each loop
            startLength = len(dataSec) # Length of either GPS UTCPOS or TimeTag2
            newDataSec = []

            if ConfigFile.settings['bL1cSolarTracker']:
                start = Utilities.timeTag2ToSec(list(timeTag[0])[0])
                stop = Utilities.timeTag2ToSec(list(timeTag[1])[0]) 
            else:
                start = Utilities.timeTag2ToSec(timeTag[0])
                stop = Utilities.timeTag2ToSec(timeTag[1])                      

            # msg = f'Eliminate data between: {timeTag}  (HHMMSSMSS)'
            # print(msg)
            # Utilities.writeLogFile(msg)            

            if startLength > 0:  
                counter = 0              
                for i in range(startLength):
                    if start <= dataSec[i] and stop >= dataSec[i]:                      
                        group.datasetDeleteRow(i - counter)  # Adjusts the index for the shrinking arrays
                        counter += 1
                        finalCount += 1
                    else:
                        newDataSec.append(dataSec[i])
                # if group.id.startswith("GP"):
                #     test = len(group.getDataset("UTCPOS").data["NONE"])
                # else:
                    # test = len(group.getDataset("TIMETAG2").data["NONE"])
                # msg = ("     Length of dataset after removal " + str(test))
                # print(msg)
                # Utilities.writeLogFile(msg)
                # finalCount += counter
            else:
                msg = 'Data group is empty. Continuing.'
                print(msg)
                Utilities.writeLogFile(msg)
            dataSec = newDataSec.copy()


        if badTimes == []:
            startLength = 1 # avoids div by zero below when finalCount is 0
        
        return finalCount/originalLength

    # Used to calibrate raw data (convert from L1a to L1b)
    # Reference: "SAT-DN-00134_Instrument File Format.pdf"
    @staticmethod
    def processDataset(ds, cd, inttime=None, immersed=False):
        #print("FitType:", cd.fitType)
        if cd.fitType == "OPTIC1":
            ProcessL1c.processOPTIC1(ds, cd, immersed)
        elif cd.fitType == "OPTIC2":
            ProcessL1c.processOPTIC2(ds, cd, immersed)
        elif cd.fitType == "OPTIC3":
            ProcessL1c.processOPTIC3(ds, cd, immersed, inttime)
        elif cd.fitType == "OPTIC4":
            ProcessL1c.processOPTIC4(ds, cd, immersed)
        elif cd.fitType == "THERM1":
            ProcessL1c.processTHERM1(ds, cd)
        elif cd.fitType == "POW10":
            ProcessL1c.processPOW10(ds, cd, immersed)
        elif cd.fitType == "POLYU":
            ProcessL1c.processPOLYU(ds, cd)
        elif cd.fitType == "POLYF":
            ProcessL1c.processPOLYF(ds, cd)
        elif cd.fitType == "DDMM":
            ProcessL1c.processDDMM(ds, cd)
        elif cd.fitType == "HHMMSS":
            ProcessL1c.processHHMMSS(ds, cd)
        elif cd.fitType == "DDMMYY":
            ProcessL1c.processDDMMYY(ds, cd)
        elif cd.fitType == "TIME2":
            ProcessL1c.processTIME2(ds, cd)
        elif cd.fitType == "COUNT":
            pass
        elif cd.fitType == "NONE":
            pass
        else:
            msg = f'Unknown Fit Type: {cd.fitType}'
            print(msg)
            Utilities.writeLogFile(msg)

    # Process OPTIC1 - not implemented
    @staticmethod
    def processOPTIC1(ds, cd, immersed):
        return

    @staticmethod
    def processOPTIC2(ds, cd, immersed):
        a0 = float(cd.coefficients[0])
        a1 = float(cd.coefficients[1])
        im = float(cd.coefficients[2]) if immersed else 1.0
        k = cd.id
        for x in range(ds.data.shape[0]):
            ds.data[k][x] = im * a1 * (ds.data[k][x] - a0)

    @staticmethod
    def processOPTIC3(ds, cd, immersed, inttime):
        a0 = float(cd.coefficients[0])
        a1 = float(cd.coefficients[1])
        im = float(cd.coefficients[2]) if immersed else 1.0
        cint = float(cd.coefficients[3])
        #print(inttime.data.shape[0], self.data.shape[0])
        k = cd.id
        #print(cint, aint)
        #print(cd.id)
        for x in range(ds.data.shape[0]):
            aint = inttime.data[cd.type][x]
            #v = self.data[k][x]
            ds.data[k][x] = im * a1 * (ds.data[k][x] - a0) * (cint/aint)

    @staticmethod
    def processOPTIC4(ds, cd, immersed):
        a0 = float(cd.coefficients[0])
        a1 = float(cd.coefficients[1])
        im = float(cd.coefficients[2]) if immersed else 1.0
        cint = float(cd.coefficients[3])
        k = cd.id
        aint = 1
        for x in range(ds.data.shape[0]):
            ds.data[k][x] = im * a1 * (ds.data[k][x] - a0) * (cint/aint)

    # Process THERM1 - not implemented
    @staticmethod
    def processTHERM1(ds, cd):
        return

    @staticmethod
    def processPOW10(ds, cd, immersed):
        a0 = float(cd.coefficients[0])
        a1 = float(cd.coefficients[1])
        im = float(cd.coefficients[2]) if immersed else 1.0
        k = cd.id
        for x in range(ds.data.shape[0]):
            ds.data[k][x] = im * pow(10, ((ds.data[k][x]-a0)/a1))

    @staticmethod
    def processPOLYU(ds, cd):
        k = cd.id
        for x in range(ds.data.shape[0]):
            num = 0
            for i in range(0, len(cd.coefficients)):
                a = float(cd.coefficients[i])
                num += a * pow(ds.data[k][x],i)
            ds.data[k][x] = num

    @staticmethod
    def processPOLYF(ds, cd):
        a0 = float(cd.coefficients[0])
        k = cd.id
        for x in range(ds.data.shape[0]):
            num = a0
            for a in cd.coefficients[1:]:
                num *= (ds.data[k][x] - float(a))
            ds.data[k][x] = num

    # Process DDMM - not implemented
    @staticmethod
    def processDDMM(ds, cd):
        return
        #s = "{:.2f}".format(x)
        #x = s[:1] + " " + s[1:3] + "\' " + s[3:5] + "\""

    # Process HHMMSS - not implemented
    @staticmethod
    def processHHMMSS(ds, cd):
        return
        #s = "{:.2f}".format(x)
        #x = s[:2] + ":" + s[2:4] + ":" + s[4:6] + "." + s[6:8]

    # Process DDMMYY - not implemented
    @staticmethod
    def processDDMMYY(ds, cd):
        return
        #s = str(x)
        #x = s[:2] + "/" + s[2:4] + "/" + s[4:]

    # Process TIME2 - not implemented
    @staticmethod
    def processTIME2(ds, cd):
        return
        #x = datetime.fromtimestamp(x).strftime("%y-%m-%d %H:%M:%S")
    
    @staticmethod
    def processL1c(node, calibrationMap, ancillaryData=None):    
        '''
        Filters data for pitch, roll, yaw, and rotator.
        Calibrates raw data from L1a using information from calibration file
        '''

        node.attributes["PROCESSING_LEVEL"] = "1c"     

        badTimes = None   
        # Apply Pitch & Roll Filter   
        # This has to record the time interval (TT2) for the bad angles in order to remove these time intervals 
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.

        ''' To Do:This is currently unavailable without SolarTracker. Once I come across accelerometer data
        from other sources or can incorporate it into the ancillary data stream, I can make it available again.'''
        
        if node is not None and int(ConfigFile.settings["bL1cCleanPitchRoll"]) == 1:
            msg = "Filtering file for high pitch and roll"
            print(msg)
            Utilities.writeLogFile(msg)
            
            i = 0
            # try:
            for group in node.groups:
                if group.id == "SOLARTRACKER":
                    gp = group

            # if gp.getDataset("POINTING"):   
            # TIMETAG2 format: hhmmssmss.0
            timeStamp = gp.getDataset("TIMETAG2").data
            pitch = gp.getDataset("PITCH").data["SAS"]
            roll = gp.getDataset("ROLL").data["SAS"]
                            
            pitchMax = float(ConfigFile.settings["fL1cPitchRollPitch"])
            rollMax = float(ConfigFile.settings["fL1cPitchRollRoll"])

            if badTimes is None:
                badTimes = []

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
                        msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]} (HHMMSSMSS)'
                        # print(msg)
                        Utilities.writeLogFile(msg)
                        # startSec = Utilities.timeTag2ToSec(list(startstop[0])[0])
                        # stopSec = Utilities.timeTag2ToSec(list(startstop[1])[0])                            
                        badTimes.append(startstop)
                        start = -1
            msg = f'Percentage of SATNAV data out of Pitch/Roll bounds: {round(100*i/len(timeStamp))} %'
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
        if node is not None and int(ConfigFile.settings["bL1cRotatorDelay"]) == 1:
            msg = "Filtering file for Rotator Delay"
            print(msg)
            Utilities.writeLogFile(msg)
                
            for group in node.groups:
                if group.id == "SOLARTRACKER":
                    gp = group
            
            if 'gp' in locals():
                if gp.getDataset("POINTING"):   
                    # TIMETAG2 format: hhmmssmss.0 is unbuffered (i.e. 1234.0 is 1.234 minutes after midnight)
                    timeStamp = gp.getDataset('TIMETAG2').data['NONE']
                    timeStampTuple = gp.getDataset("TIMETAG2").data
                    rotator = gp.getDataset("POINTING").data["ROTATOR"] 
                    # Rotator Home Angle Offset is generally set in the .sat file when setting up the SolarTracker
                    # It may also be set for when no SolarTracker is present and it's not included in the
                    # ancillary data, but that's not relevant here                       
                    home = float(ConfigFile.settings["fL1cRotatorHomeAngle"])     
                    delay = float(ConfigFile.settings["fL1cRotatorDelay"])

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
                                timeInt = int(timeStamp[index])                    
                                # print('Rotator delay kick-out. ' + str(timeInt) )
                                startIndex = index
                                start = Utilities.timeTag2ToSec(timeInt)
                                lastAngle = rotator[index]
                                kickout = 1

                            else:                        
                                # Is this X seconds past a kick-out start?
                                timeInt = int(timeStamp[index])
                                time = Utilities.timeTag2ToSec(timeInt)
                                if kickout==1 and time > (start+delay):
                                    startstop = [timeStampTuple[startIndex],timeStampTuple[index-1]]
                                    msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]} (HHMMSSMSS)'
                                    # print(msg)
                                    Utilities.writeLogFile(msg)
                                    badTimes.append(startstop)
                                    kickout = 0
                                elif kickout ==1:
                                    i += 1

                    msg = f'Percentage of SATNAV data out of Rotator Delay bounds: {round(100*i/len(timeStamp))} %'
                    print(msg)
                    Utilities.writeLogFile(msg)    
                else:
                    msg = f'No rotator data found. Filtering on rotator delay failed.'
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
        if node is not None and int(ConfigFile.settings["bL1cRotatorAngle"]) == 1:
            msg = "Filtering file for bad Absolute Rotator Angle"
            print(msg)
            Utilities.writeLogFile(msg)
            
            i = 0
            # try:
            for group in node.groups:
                if group.id == "SOLARTRACKER":
                    gp = group

            if gp.getDataset("POINTING"):   
                # TIMETAG2 format: hhmmssmss.0
                timeStamp = gp.getDataset("TIMETAG2").data
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
                msg = f'Percentage of SATNAV data out of Absolute Rotator bounds: {round(100*i/len(timeStamp))} %'
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
            else:
                msg = f'No rotator data found. Filtering on absolute rotator angle failed.'
                print(msg)
                Utilities.writeLogFile(msg)                       

        if ConfigFile.settings["bL1cSolarTracker"]:    
            for group in node.groups:
                    if group.id == "SOLARTRACKER":
                        gp = group 
            if gp.getDataset("AZIMUTH") and gp.getDataset("HEADING") and gp.getDataset("POINTING"):   
                # TIMETAG2 format: hhmmssmss.0
                timeStamp = gp.getDataset("TIMETAG2").data
                # Rotator Home Angle Offset is generally set in the .sat file when setting up the SolarTracker
                # It may also be set here for when no SolarTracker is present and it's not included in the
                # ancillary data. See below.                 
                home = float(ConfigFile.settings["fL1cRotatorHomeAngle"])
                sunAzimuth = gp.getDataset("AZIMUTH").data["SUN"]
                sasAzimuth = gp.getDataset("HEADING").data["SAS_TRUE"]    
                newRelAzData = gp.addDataset("REL_AZ")                            
            else:
                    msg = f"No rotator, solar azimuth, and/or ship'''s heading data found. Filtering on relative azimuth not added."
                    print(msg)
                    Utilities.writeLogFile(msg)
        else:
            # In case there is no SolarTracker to provide sun/sensor geometries, Pysolar will be used
            # to estimate sun zenith and azimuth using GPS position and time, and sensor azimuth will
            # come from ancillary data input.
            
            # Initialize a new group to host the unconventioal ancillary data
            ancGroup = node.addGroup("ANCILLARY_NOTRACKER")
            ancGroup.attributes["FrameType"] = "Not Required"

            ancDateTime = ancillaryData.columns["DATETIME"][0].copy()
            timeStamp = [Utilities.datetime2TimeTag2(dt) for dt in ancDateTime]
            # ancSec =  [Utilities.timeTag2ToSec(tt2) for tt2 in timeStamp]
            # Remove all ancillary data that does not intersect GPS data            
            for gp in node.groups:
                if gp.id == "ES_LIGHT":
                    esTimeTag2 = gp.getDataset("TIMETAG2").data
                    esDateTag = gp.getDataset("DATETAG").data
                    esSec = [Utilities.timeTag2ToSec(tt2[0]) for tt2 in esTimeTag2]

                if gp.id.startswith("GP"):
                    gpsTime = gp.getDataset("UTCPOS").data["NONE"]
                    gpsDateTime = []
                    # Need to combine time and date
                    for n, utc in enumerate(gpsTime):
                        gpsSec = Utilities.utcToSec(utc)
                        gpsTimeTag2 = Utilities.secToTimeTag2(gpsSec)
                        # There is no date data in GPGGA
                        if gp.id.startswith("GPGGA"):
                            nearestIndex = Utilities.find_nearest(esSec,gpsSec)
                            gpsDateTag = esDateTag[nearestIndex]
                            gpsDate = Utilities.dateTagToDateTime(gpsDateTag[0])
                            gpsDateTime.append(Utilities.timeTag2ToDateTime(gpsDate,gpsTimeTag2))
                        else:
                            gpsDateTag = ancillaryData.columns["DATETAG"][n]
                            gpsDate = Utilities.dateTagToDateTime(gpsDateTag[0])
                            gpsDateTime.append(Utilities.timeTag2ToDateTime(gpsDateTag,gpsTimeTag2))
            
            # Eliminate all ancillary data outside file times
            ticker = 0
            print('Removing non-pertinent ancillary data... May take a moment with large SeaBASS file')
            for i, dt in enumerate(ancDateTime):
                if dt < min(gpsDateTime) or dt > max(gpsDateTime):                    
                    index = i-ticker # adjusts for deleted rows
                    ticker += 1
                    ancillaryData.colDeleteRow(index) # this removes row from data structure as well                
            # Test if any data is left
            if not ancillaryData.columns["DATETIME"][0]:
                msg = "No coincident ancillary data found. Aborting"
                print(msg)
                Utilities.writeLogFile(msg)                   
                return None 

            # Reinitialize with new, smaller dataset
            ancDateTime = ancillaryData.columns["DATETIME"][0]
            shipAzimuth = ancillaryData.columns["HEADING"][0]
            # ancDateTime = ancillaryData.columns["DATETIME"][0].copy()
            timeStamp = [Utilities.datetime2TimeTag2(dt) for dt in ancDateTime]
            ancDateTag = [Utilities.datetime2DateTag(dt) for dt in ancDateTime]
            home = ancillaryData.columns["HOMEANGLE"][0]
            for i, offset in enumerate(home):
                if offset > 180:
                    home[i] = offset-360
            sasAzimuth = list(map(add, shipAzimuth, home))

            lat = ancillaryData.columns["LATITUDE"][0]
            lon = ancillaryData.columns["LATITUDE"][0]
            sunAzimuth = []
            sunZenith = []
            for i, dt_utc in enumerate(ancDateTime):
                # Run Pysolar to obtain solar geometry
                sunAzimuth.append(get_azimuth(lat[i],lon[i],pytz.utc.localize(dt_utc),0))
                sunZenith.append(90 - get_altitude(lat[i],lon[i],pytz.utc.localize(dt_utc),0))
            
        relAz=[]
        for index in range(len(sunAzimuth)):
            if ConfigFile.settings["bL1cSolarTracker"]:
                # Changes in the angle between the bow and the sensor changes are tracked by SolarTracker
                # This home offset is generally set in .sat file in the field, but can be updated here with
                # the value from the configuration window (L1C)
                offset = home
            else:
                # Changes in the angle between the bow and the sensor changes are tracked in ancillary data
                offset = home[index]

            # Check for angles spanning north
            if sunAzimuth[index] > sasAzimuth[index]:
                hiAng = sunAzimuth[index] + offset
                loAng = sasAzimuth[index] + offset
            else:
                hiAng = sasAzimuth[index] + offset
                loAng = sunAzimuth[index] + offset
            # Choose the smallest angle between them
            if hiAng-loAng > 180:
                relAzimuthAngle = 360 - (hiAng-loAng)
            else:
                relAzimuthAngle = hiAng-loAng

            relAz.append(relAzimuthAngle)        

        # If using a SolarTracker, add RelAz to the SATNAV/SOLARTRACKER group...
        if ConfigFile.settings["bL1cSolarTracker"]:               
            newRelAzData.columns["REL_AZ"] = relAz
            newRelAzData.columnsToDataset()        
        else:
            # ... otherwise populate the ancGroup
            ancGroup.addDataset("TIMETAG2")
            ancGroup.addDataset("DATETAG")
            ancGroup.addDataset("SOLAR_AZ")
            ancGroup.addDataset("SZA")
            ancGroup.addDataset("HEADING")
            ancGroup.addDataset("REL_AZ")

            ancGroup.datasets["TIMETAG2"].data = np.array(timeStamp, dtype=[('NONE', '<f8')])
            ancGroup.datasets["DATETAG"].data = np.array(ancDateTag, dtype=[('NONE', '<f8')])
            ancGroup.datasets["SOLAR_AZ"].data = np.array(sunAzimuth, dtype=[('NONE', '<f8')])
            ancGroup.datasets["SZA"].data = np.array(sunZenith, dtype=[('NONE', '<f8')])
            ancGroup.datasets["HEADING"].data = np.array(shipAzimuth, dtype=[('NONE', '<f8')])
            ancGroup.datasets["REL_AZ"].data = np.array(relAz, dtype=[('NONE', '<f8')])


        # Apply Relative Azimuth filter 
        # This has to record the time interval (TT2) for the bad angles in order to remove these time intervals 
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.
        if node is not None and int(ConfigFile.settings["bL1cCleanSunAngle"]) == 1:
            msg = "Filtering file for bad Relative Solar Azimuth"
            print(msg)
            Utilities.writeLogFile(msg)
            
            i = 0
            # try:
            # for group in node.groups:
            #     if group.id == "SOLARTRACKER":
            #         gp = group

            # if gp.getDataset("AZIMUTH") and gp.getDataset("HEADING") and gp.getDataset("POINTING"):                           
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
                        msg = f'   Flag data from TT2: {startstop[0]}  to {startstop[1]} (HHMMSSMSS)'
                        # print(msg)
                        Utilities.writeLogFile(msg)
                    
                        badTimes.append(startstop)
                        start = -1
            
            for group in node.groups:
                if group.id.startswith("GP"):
                    gp = group
                        
            msg = f'Percentage of ancillary data out of Relative Solar Azimuth bounds: {round(100*i/len(relAz))} %'
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
            # else:
            #     msg = f'No rotator, solar azimuth, and/or relative azimuth data found. Filtering on relative azimuth failed.'
            #     print(msg)
            #     Utilities.writeLogFile(msg)        
                        
        msg = "Eliminate combined filtered data from datasets.*****************************"
        print(msg)
        Utilities.writeLogFile(msg)

        # For each dataset in each group, find the badTimes to remove and delete those rows                
        for gp in node.groups:                                                    
            
            # SATMSG has an ambiguous timer POSFRAME.COUNT, cannot filter
            if (gp.id == "SOLARTRACKER_STATUS") is False:                
                fractionRemoved = ProcessL1c.filterData(gp, badTimes)

                # Now test whether the overlap has eliminated all radiometric data
                if fractionRemoved > 0.98 and gp.id.startswith("H"):
                    msg = "Radiometric data >98'%' eliminated. Aborting."
                    print(msg)
                    Utilities.writeLogFile(msg)                   
                    return None                            
                
                # Confirm that data were removed from Root    
                group = node.getGroup(gp.id)
                if gp.id.startswith("GP"):
                    gpTimeset  = group.getDataset("UTCPOS") 
                else:
                    gpTimeset  = group.getDataset("TIMETAG2") 

                gpTime = gpTimeset.data["NONE"]
                lenGpTime = len(gpTime)
                msg = f'{gp.id}  Data end {lenGpTime} long, a loss of {round(100*(fractionRemoved))} %'
                print(msg)
                Utilities.writeLogFile(msg)                                               

        return node
