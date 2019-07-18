
import math
import HDFRoot
#import HDFGroup
#import HDFDataset
from Utilities import Utilities
from ConfigFile import ConfigFile

class ProcessL1b:

    # Delete records within the out-of-bounds times found by filtering on relative solar angle
    # Or records within the out-of-bounds for absolute rotator angle.
    @staticmethod
    def filterData(group, badTimes):                    
        
        # Now delete the record from each dataset in the group
        ticker = 0
        finalCount = 0
        for timeTag in badTimes:               
            msg = ("Eliminate data between: " + str(timeTag) + " (HHMMSSMSS)")
            # print(msg)
            Utilities.writeLogFile(msg)
            # print(timeTag)
            # print(" ")         
            start = Utilities.timeTag2ToSec(list(timeTag[0])[0])
            stop = Utilities.timeTag2ToSec(list(timeTag[1])[0])                
            # badIndex = ([i for i in range(lenDataSec) if start <= dataSec[i] and stop >= dataSec[i]])      
            
            # Convert all time stamps to milliseconds UTC
            if group.id.startswith("GPR"):
                # This is handled seperately in order to deal with the UTC fields in GPS            
                if ticker ==0:
                    msg = "   Remove GPS Data"
                    # print(msg)
                    Utilities.writeLogFile(msg)

                gpsTimeData = group.getDataset("UTCPOS")        
                dataSec = []
                for i in range(gpsTimeData.data.shape[0]):
                    # UTC format (hhmmss.) similar to TT2 (hhmmssmss.) with the miliseconds truncated
                    dataSec.append(Utilities.utcToSec(gpsTimeData.data["NONE"][i]))    
                    # print(dataSec[i])        
            else:
                msg = ("   Remove " + group.id + " Data")
                # print(msg)
                Utilities.writeLogFile(msg)
                timeData = group.getDataset("TIMETAG2")        
                dataSec = []
                for i in range(timeData.data.shape[0]):
                    # Converts from TT2 (hhmmssmss. UTC) to milliseconds UTC
                    dataSec.append(Utilities.timeTag2ToSec(timeData.data["NONE"][i])) 

            lenDataSec = len(dataSec)
            if ticker == 0:
                startLength = lenDataSec
                ticker +=1

            # msg = ('   Length of dataset prior to removal ' + str(lenDataSec) + ' long')
            # print(msg)
            # Utilities.writeLogFile(msg)

            if lenDataSec > 0:
                counter = 0
                for i in range(lenDataSec):
                    if start <= dataSec[i] and stop >= dataSec[i]:
                        if group.id.startswith("GPR"):
                            test = group.getDataset("UTCPOS").data["NONE"][i - counter]
                        else:
                            test = group.getDataset("TIMETAG2").data["NONE"][i - counter]                    
                        # print("     Removing " + str(test) + " " + str(Utilities.secToTimeTag2(dataSec[i])) + " index: " + str(i))                                        
                        # print(i-counter)
                        group.datasetDeleteRow(i - counter)  # Adjusts the index for the shrinking arrays
                        counter += 1
                # print(str(counter) + " records eliminated.")
                if group.id.startswith("GPR"):
                    test = len(group.getDataset("UTCPOS").data["NONE"])
                else:
                    test = len(group.getDataset("TIMETAG2").data["NONE"])
                # msg = ("     Length of dataset after removal " + str(test))
                # print(msg)
                # Utilities.writeLogFile(msg)
                finalCount += counter
            else:
                msg = ('Data group is empty')
                print(msg)
                Utilities.writeLogFile(msg)

        return finalCount/startLength

    # Used to calibrate raw data (convert from L1a to L1b)
    # Reference: "SAT-DN-00134_Instrument File Format.pdf"
    @staticmethod
    def processDataset(ds, cd, inttime=None, immersed=False):
        #print("FitType:", cd.fitType)
        if cd.fitType == "OPTIC1":
            ProcessL1b.processOPTIC1(ds, cd, immersed)
        elif cd.fitType == "OPTIC2":
            ProcessL1b.processOPTIC2(ds, cd, immersed)
        elif cd.fitType == "OPTIC3":
            ProcessL1b.processOPTIC3(ds, cd, immersed, inttime)
        elif cd.fitType == "OPTIC4":
            ProcessL1b.processOPTIC4(ds, cd, immersed)
        elif cd.fitType == "THERM1":
            ProcessL1b.processTHERM1(ds, cd)
        elif cd.fitType == "POW10":
            ProcessL1b.processPOW10(ds, cd, immersed)
        elif cd.fitType == "POLYU":
            ProcessL1b.processPOLYU(ds, cd)
        elif cd.fitType == "POLYF":
            ProcessL1b.processPOLYF(ds, cd)
        elif cd.fitType == "DDMM":
            ProcessL1b.processDDMM(ds, cd)
        elif cd.fitType == "HHMMSS":
            ProcessL1b.processHHMMSS(ds, cd)
        elif cd.fitType == "DDMMYY":
            ProcessL1b.processDDMMYY(ds, cd)
        elif cd.fitType == "TIME2":
            ProcessL1b.processTIME2(ds, cd)
        elif cd.fitType == "COUNT":
            pass
        elif cd.fitType == "NONE":
            pass
        else:
            msg = ("Unknown Fit Type:", cd.fitType)
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

    # Used to calibrate raw data (from L0 to L1b)
    @staticmethod
    def processGroup(gp, cf): # group, calibration file
        inttime = None
        for cd in cf.data: # cd is the name of the cal file data
            # Process slightly differently for INTTIME
            if cd.type == "INTTIME":
                #print("Process INTTIME")
                ds = gp.getDataset("INTTIME")
                ProcessL1b.processDataset(ds, cd)
                inttime = ds

        for cd in cf.data:
            # process each dataset in the cal file list of data, except INTTIME
            if gp.getDataset(cd.type) and cd.type != "INTTIME":
                #print("Dataset:", cd.type)
                ds = gp.getDataset(cd.type)
                ProcessL1b.processDataset(ds, cd, inttime)

    # Filters data for pitch, roll, yaw, and rotator.
    # Calibrates raw data from L1a using information from calibration file
    @staticmethod
    def processL1b(node, calibrationMap): 
        

        badTimes = None   
        # Apply Pitch & Roll Filter
        # This has to record the time interval (TT2) for the bad angles in order to remove these time intervals 
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.
        if node is not None and int(ConfigFile.settings["bL1bCleanPitchRoll"]) == 1:
            msg = "Filtering file for high pitch and roll"
            print(msg)
            Utilities.writeLogFile(msg)
            
            i = 0
            # try:
            for group in node.groups:
                if group.id.startswith("SATNAV"):
                    gp = group

            if gp.getDataset("POINTING"):   
                # TIMETAG2 format: hhmmssmss.0
                timeStamp = gp.getDataset("TIMETAG2").data
                pitch = gp.getDataset("PITCH").data["SAS"]
                roll = gp.getDataset("ROLL").data["SAS"]
                               
                pitchMax = float(ConfigFile.settings["fL1bPitchRollPitch"])
                rollMax = float(ConfigFile.settings["fL1bPitchRollRoll"])

                if badTimes is None:
                    badTimes = []

                start = -1
                for index in range(len(pitch)):
                    # Check for angles spanning north
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
                            msg = ('   Flag data from TT2: ' + str(startstop[0]) + ' to ' + str(startstop[1]) + '(HHMMSSMSS)')
                            print(msg)
                            Utilities.writeLogFile(msg)
                            # startSec = Utilities.timeTag2ToSec(list(startstop[0])[0])
                            # stopSec = Utilities.timeTag2ToSec(list(startstop[1])[0])                            
                            badTimes.append(startstop)
                            start = -1
                msg = ("Percentage of SATNAV data out of Pitch/Roll bounds: " + str(round(100*i/len(timeStamp))) + "%")
                print(msg)
                Utilities.writeLogFile(msg)

        # Apply Rotator Delay Filter (delete records within so many seconds of a rotation)
        # This has to record the time interval (TT2) for the bad angles in order to remove these time intervals 
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.

        msg = "Filtering file for Rotator Delay"
        print(msg)
        Utilities.writeLogFile(msg)
            
        for group in node.groups:
            if group.id.startswith("SATNAV"):
                gp = group

        if gp.getDataset("POINTING"):   
            # TIMETAG2 format: hhmmssmss.0 is unbuffered (i.e. 1234.0 is 1.234 minutes after midnight)
            timeStamp = gp.getDataset('TIMETAG2').data['NONE']
            timeStampTuple = gp.getDataset("TIMETAG2").data
            rotator = gp.getDataset("POINTING").data["ROTATOR"]                        
            home = float(ConfigFile.settings["fL1bRotatorHomeAngle"])     
            delay = float(ConfigFile.settings["fL1bRotatorDelay"])

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
                            msg = ('   Flag data from TT2: ' + str(startstop[0]) + ' to ' + str(startstop[1]) + '(HHMMSSMSS)')
                            print(msg)
                            Utilities.writeLogFile(msg)
                            badTimes.append(startstop)
                            kickout = 0
                        elif kickout ==1:
                            i += 1

            msg = ("Percentage of SATNAV data out of Rotator Delay bounds: " + str(round(100*i/len(timeStamp))) + "%")
            print(msg)
            Utilities.writeLogFile(msg)

        # Apply Absolute Rotator Angle Filter
        # This has to record the time interval (TT2) for the bad angles in order to remove these time intervals 
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.
        if node is not None and int(ConfigFile.settings["bL1bCleanRotatorAngle"]) == 1:
            msg = "Filtering file for bad Absolute Rotator Angle"
            print(msg)
            Utilities.writeLogFile(msg)
            
            i = 0
            # try:
            for group in node.groups:
                if group.id.startswith("SATNAV"):
                    gp = group

            if gp.getDataset("POINTING"):   
                # TIMETAG2 format: hhmmssmss.0
                timeStamp = gp.getDataset("TIMETAG2").data
                rotator = gp.getDataset("POINTING").data["ROTATOR"]                        
                home = float(ConfigFile.settings["fL1bRotatorHomeAngle"])
               
                absRotatorMin = float(ConfigFile.settings["fL1bRotatorAngleMin"])
                absRotatorMax = float(ConfigFile.settings["fL1bRotatorAngleMax"])

                if badTimes is None:
                    badTimes = []

                start = -1
                for index in range(len(rotator)):
                    # Check for angles spanning north
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
                            print(msg)
                            Utilities.writeLogFile(msg)
                            # startSec = Utilities.timeTag2ToSec(list(startstop[0])[0])
                            # stopSec = Utilities.timeTag2ToSec(list(startstop[1])[0])                            
                            badTimes.append(startstop)
                            start = -1
                msg = ("Percentage of SATNAV data out of Absolute Rotator bounds: " + str(round(100*i/len(timeStamp))) + "%")
                print(msg)
                Utilities.writeLogFile(msg)

        # Apply Relative Azimuth filter 
        # This has to record the time interval (TT2) for the bad angles in order to remove these time intervals 
        # rather than indexed values gleaned from SATNAV, since they have not yet been interpolated in time.
        # Interpolating them first would introduce error.
        if node is not None and int(ConfigFile.settings["bL1bCleanSunAngle"]) == 1:
            msg = "Filtering file for bad Relative Solar Azimuth"
            print(msg)
            Utilities.writeLogFile(msg)
            # Utilities.hyperLogger(inFilePath,'a')
            
            i = 0
            # try:
            for group in node.groups:
                if group.id.startswith("SATNAV"):
                    gp = group

            if gp.getDataset("AZIMUTH") and gp.getDataset("HEADING") and gp.getDataset("POINTING"):   
                # TIMETAG2 format: hhmmssmss.0
                timeStamp = gp.getDataset("TIMETAG2").data
                # rotator = gp.getDataset("POINTING").data["ROTATOR"]                        
                home = float(ConfigFile.settings["fL1bRotatorHomeAngle"])
                sunAzimuth = gp.getDataset("AZIMUTH").data["SUN"]
                sasAzimuth = gp.getDataset("HEADING").data["SAS_TRUE"]
                # shipAzimuth = gp.getDataset("HEADING").data["SHIP_TRUE"]
                relAzimuthMin = float(ConfigFile.settings["fL1bSunAngleMin"])
                relAzimuthMax = float(ConfigFile.settings["fL1bSunAngleMax"])

                if badTimes is None:
                    badTimes = []

                # Need to add relAzimuthAngle to a dataset in node
                newRelAzData = gp.addDataset("REL_AZ")
                relAz=[]
                start = -1
                for index in range(len(sunAzimuth)):
                    # Check for angles spanning north
                    if sunAzimuth[index] > sasAzimuth[index]:
                        hiAng = sunAzimuth[index] + home
                        loAng = sasAzimuth[index] + home
                    else:
                        hiAng = sasAzimuth[index] + home
                        loAng = sunAzimuth[index] + home
                    # Choose the smallest angle between them
                    if hiAng-loAng > 180:
                        relAzimuthAngle = 360 - (hiAng-loAng)
                    else:
                        relAzimuthAngle = hiAng-loAng

                    relAz.append(relAzimuthAngle)

                    if relAzimuthAngle > relAzimuthMax or relAzimuthAngle < relAzimuthMin or math.isnan(relAzimuthAngle):   
                        i += 1                              
                        if start == -1:
                            # print('Relative solar azimuth angle outside bounds. ' + str(round(relAzimuthAngle)))
                            start = index
                        stop = index                                
                    else:                                
                        if start != -1:
                            # print('Relative solar azimuth angle passed: ' + str(round(relAzimuthAngle)))
                            startstop = [timeStamp[start],timeStamp[stop]]
                            msg = ('   Flag data from TT2: ' + str(startstop[0]) + ' to ' + str(startstop[1]) + '(HHMMSSMSS)')
                            print(msg)
                            Utilities.writeLogFile(msg)
                            # startSec = Utilities.timeTag2ToSec(list(startstop[0])[0])
                            # stopSec = Utilities.timeTag2ToSec(list(startstop[1])[0])                            
                            badTimes.append(startstop)
                            start = -1
                newRelAzData.columns["REL_AZ"] = relAz
                newRelAzData.columnsToDataset()
                msg = ("Percentage of SATNAV data out of Solar Azimuth bounds: " + str(round(100*i/len(timeStamp))) + "%")
                print(msg)
                Utilities.writeLogFile(msg)
                        
        msg = "Eliminate combined filtered data from datasets.__________________________________"
        print(msg)
        Utilities.writeLogFile(msg)
        # For each dataset in each group, find the badTimes to remove and delete those rows                
        for gp in node.groups:                                        
            
            # if gp.id.startswith("GPR"):
            #     #  pass
            #     fractionRemoved = ProcessL1b.filterTimeData(gp, badTimes)
            #     # Confirm that data were removed from group
            #     # gpTimeset  = gp.getDataset("UTCPOS") 
            #     # gpTime = gpTimeset.data["NONE"]
            #     # print('Group data end up ' + str(len(gpTime)) + ' long')                    
            #     # Confirm that data were removed from Root    
            #     group = node.getGroup("GPR")
            #     gpTimeset  = group.getDataset("UTCPOS") 
            #     gpTime = gpTimeset.data["NONE"]
            #     lenGpTime = len(gpTime)
            #     print('Data end   ' + str(lenGpTime) + ' long, a loss of ' + str(round(100*(fractionRemoved))) + '%')
            
            # SATMSG has an ambiguous timer POSFRAME.COUNT, cannot filter
            if gp.id.startswith("SATMSG") is False:                
                fractionRemoved = ProcessL1b.filterData(gp, badTimes)
                
                # Confirm that data were removed from Root    
                group = node.getGroup(gp.id)
                if gp.id.startswith("GPRMC"):
                    gpTimeset  = group.getDataset("UTCPOS") 
                else:
                    gpTimeset  = group.getDataset("TIMETAG2") 

                gpTime = gpTimeset.data["NONE"]
                lenGpTime = len(gpTime)
                msg = ('Data end   ' + str(lenGpTime) + ' long, a loss of ' + str(round(100*(fractionRemoved))) + '%') 
                print(msg)
                Utilities.writeLogFile(msg)                                               

        esUnits = None
        liUnits = None
        ltUnits = None

        for gp in node.groups:
            # Apply calibration factors to each dataset in HDF 
            print("Group: ", gp.id)
            if "CalFileName" in gp.attributes:
                #cf = calibrationMap[gp.attributes["FrameTag"]]
                cf = calibrationMap[gp.attributes["CalFileName"]]
                #print(gp.id, gp.attributes)
                print("File:", cf.id)
                ProcessL1b.processGroup(gp, cf)
    
                if esUnits == None:
                    esUnits = cf.getUnits("ES")
                if liUnits == None:
                    liUnits = cf.getUnits("LI")
                if ltUnits == None:
                    ltUnits = cf.getUnits("LT")

        #print(esUnits, luUnits)
        node.attributes["LI_UNITS"] = liUnits
        node.attributes["LT_UNITS"] = ltUnits
        node.attributes["ES_UNITS"] = esUnits

        return node
