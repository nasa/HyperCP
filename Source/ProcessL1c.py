
import math
import datetime
import numpy as np
from pysolar.solar import get_azimuth, get_altitude
# import pytz
from operator import add

import HDFRoot

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


        if badTimes == []:
            startLength = 1 # avoids div by zero below when finalCount is 0
        
        return finalCount/originalLength

    # # Used to calibrate raw data (convert from L1a to L1b)
    # # Reference: "SAT-DN-00134_Instrument File Format.pdf"
    # @staticmethod
    # def processDataset(ds, cd, inttime=None, immersed=False):
    #     #print("FitType:", cd.fitType)
    #     if cd.fitType == "OPTIC1":
    #         ProcessL1c.processOPTIC1(ds, cd, immersed)
    #     elif cd.fitType == "OPTIC2":
    #         ProcessL1c.processOPTIC2(ds, cd, immersed)
    #     elif cd.fitType == "OPTIC3":
    #         ProcessL1c.processOPTIC3(ds, cd, immersed, inttime)
    #     elif cd.fitType == "OPTIC4":
    #         ProcessL1c.processOPTIC4(ds, cd, immersed)
    #     elif cd.fitType == "THERM1":
    #         ProcessL1c.processTHERM1(ds, cd)
    #     elif cd.fitType == "POW10":
    #         ProcessL1c.processPOW10(ds, cd, immersed)
    #     elif cd.fitType == "POLYU":
    #         ProcessL1c.processPOLYU(ds, cd)
    #     elif cd.fitType == "POLYF":
    #         ProcessL1c.processPOLYF(ds, cd)
    #     elif cd.fitType == "DDMM":
    #         ProcessL1c.processDDMM(ds, cd)
    #     elif cd.fitType == "HHMMSS":
    #         ProcessL1c.processHHMMSS(ds, cd)
    #     elif cd.fitType == "DDMMYY":
    #         ProcessL1c.processDDMMYY(ds, cd)
    #     elif cd.fitType == "TIME2":
    #         ProcessL1c.processTIME2(ds, cd)
    #     elif cd.fitType == "COUNT":
    #         pass
    #     elif cd.fitType == "NONE":
    #         pass
    #     else:
    #         msg = f'Unknown Fit Type: {cd.fitType}'
    #         print(msg)
    #         Utilities.writeLogFile(msg)

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
    
    @staticmethod
    def processL1c(node, calibrationMap, ancillaryData=None):    
        '''
        Filters data for pitch, roll, yaw, and rotator.
        '''

        node.attributes["PROCESSING_LEVEL"] = "1c"
        now = datetime.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr
        msg = f"ProcessL1c.processL1c: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)   

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG        
        node  = Utilities.rootAddDateTime(node)

        badTimes = None   
        # Apply Pitch & Roll Filter   
        # This has to record the time interval (in datetime) for the bad angles in order to remove these time intervals 
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.

        ''' To Do: This is currently unavailable without SolarTracker. Once I come across accelerometer data
        from other sources or can incorporate it into the ancillary data stream, I can make it available again.'''
        
        if node is not None and int(ConfigFile.settings["bL1cCleanPitchRoll"]) == 1:
            msg = "Filtering file for high pitch and roll"
            print(msg)
            Utilities.writeLogFile(msg)
            
            i = 0
            for group in node.groups:
                if group.id == "SOLARTRACKER":
                    gp = group

            timeStamp = gp.getDataset("DATETIME").data
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
                        msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
                        # print(msg)
                        Utilities.writeLogFile(msg)
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
        for group in node.groups:
            if group.id == "SOLARTRACKER":
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

                if node is not None and int(ConfigFile.settings["bL1cRotatorDelay"]) == 1:
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

                        msg = f'Percentage of SATNAV data out of Rotator Delay bounds: {round(100*i/len(timeStamp))} %'
                        print(msg)
                        Utilities.writeLogFile(msg)    
                    # else:
                    #     msg = f'No rotator data found. Filtering on rotator delay failed.'
                    #     print(msg)
                    #     Utilities.writeLogFile(msg)    
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
                timeStamp = gp.getDataset("DATETIME").data
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
            for group in node.groups:
                    if group.id == "SOLARTRACKER":
                        gp = group 
            if gp.getDataset("AZIMUTH") and gp.getDataset("HEADING") and gp.getDataset("POINTING"):   
                timeStamp = gp.getDataset("DATETIME").data
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
            # Remove all ancillary data that does not intersect GPS data            
            for gp in node.groups:
                if gp.id.startswith("GP"):
                    gpsDateTime = gp.getDataset("DATETIME").data
            
            # Eliminate all ancillary data outside file times
            # This is very slow, but necessary to build a new group at L1C rather than just matching
            # to the existing ancillary group when run from L2.
            ticker = 0
            l = len(ancDateTime)
            Utilities.printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
            print('Removing non-pertinent ancillary data... May take a moment with large SeaBASS file')
            for i, dt in enumerate(ancDateTime):
                if dt < min(gpsDateTime) or dt > max(gpsDateTime):                    
                    index = i-ticker # adjusts for deleted rows
                    ticker += 1
                    Utilities.printProgressBar(ticker, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                    ancillaryData.colDeleteRow(index) # this removes row from data structure as well                
            # Test if any data is left
            if not ancillaryData.columns["DATETIME"][0]:
                msg = "No coincident ancillary data found. Aborting"
                print(msg)
                Utilities.writeLogFile(msg)                   
                return None 

            # Reinitialize with new, smaller dataset
            ''' Essential ancillary data for non-SolarTracker file includes
                lat, lon, datetime, ship heading and offset between bow and 
                SAS instrument from which SAS azimuth is calculated '''
            timeStamp = ancillaryData.columns["DATETIME"][0]
            shipAzimuth = ancillaryData.columns["HEADING"][0] # HEADING/shipAzimuth comes from ancillary data file here (not GPS or SATNAV)
            # ancDateTime = ancillaryData.columns["DATETIME"][0].copy()
            ancTimeTag2 = [Utilities.datetime2TimeTag2(dt) for dt in timeStamp]
            ancDateTag = [Utilities.datetime2DateTag(dt) for dt in timeStamp]
            home = ancillaryData.columns["HOMEANGLE"][0]
            for i, offset in enumerate(home):
                if offset > 180:
                    home[i] = offset-360
            sasAzimuth = list(map(add, shipAzimuth, home))

            lat = ancillaryData.columns["LATITUDE"][0]
            lon = ancillaryData.columns["LONGITUDE"][0]
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

            sunAzimuth = []
            sunZenith = []
            for i, dt_utc in enumerate(timeStamp):
                # Run Pysolar to obtain solar geometry
                # sunAzimuth.append(get_azimuth(lat[i],lon[i],pytz.utc.localize(dt_utc),0))
                # sunZenith.append(90 - get_altitude(lat[i],lon[i],pytz.utc.localize(dt_utc),0))
                sunAzimuth.append(get_azimuth(lat[i],lon[i],dt_utc,0))
                sunZenith.append(90 - get_altitude(lat[i],lon[i],dt_utc,0))
            
        relAz=[]
        for index in range(len(sunAzimuth)):
            if ConfigFile.settings["bL1cSolarTracker"]:
                # Changes in the angle between the bow and the sensor changes are tracked by SolarTracker
                # This home offset is generally set in .sat file in the field, but can be updated here with
                # the value from the Configuration Window (L1C)
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
            ancGroup.attributes = ancillaryData.attributes.copy()
            ancGroup.attributes["FrameType"] = "Not Required"
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
            ancGroup.datasets["SOLAR_AZ"].data = np.array(sunAzimuth, dtype=[('NONE', '<f8')])
            ancGroup.addDataset("SZA")
            ancGroup.datasets["SZA"].data = np.array(sunZenith, dtype=[('NONE', '<f8')])
            ancGroup.attributes["SZA_Units"]='degrees'
            ancGroup.addDataset("HEADING")
            ancGroup.datasets["HEADING"].data = np.array(shipAzimuth, dtype=[('NONE', '<f8')])
            ancGroup.addDataset("REL_AZ")
            ancGroup.datasets["REL_AZ"].data = np.array(relAz, dtype=[('NONE', '<f8')])
            ancGroup.attributes["REL_AZ_Units"]='degrees'
            if "STATION" in ancillaryData.columns:
                ancGroup.addDataset("STATION")
                ancGroup.datasets["STATION"].data = np.array(station, dtype=[('NONE', '<f8')])
            ancGroup.attributes["REL_AZ_Units"]='degrees'
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
            
            # Convert datetimes
            dateTime = ancGroup.addDataset("DATETIME")
            timeData = ancGroup.getDataset("TIMETAG2").data["NONE"].tolist()
            dateTag = ancGroup.getDataset("DATETAG").data["NONE"].tolist()
            timeStamp = []        
            for i, time in enumerate(timeData):
                # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
                # Filter for aberrant Datetags
                if str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20"):
                    dt = Utilities.dateTagToDateTime(dateTag[i])
                    timeStamp.append(Utilities.timeTag2ToDateTime(dt, time))
                else:                    
                    ancGroup.datasetDeleteRow(i)
                    msg = "Bad Datetag found. Eliminating record"
                    print(msg)
                    Utilities.writeLogFile(msg)
            dateTime.data = timeStamp


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
                    if fractionRemoved > 0.98 and gp.id.startswith("H"):
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
