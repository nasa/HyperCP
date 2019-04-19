
import numpy as np

import HDFRoot
#import HDFGroup
#import HDFDataset

from Utilities import Utilities


class ProcessL2:

    '''
    # ToDo: improve later
    # Reference: "ProSoft-7.7- Manual.pdf", Appendix D
    '''    
    @staticmethod
    def dataDeglitching(ds):
        noiseThresh = 20        

        # Copy dataset to dictionary
        ds.datasetToColumns()
        columns = ds.columns

        for k,v in columns.items():
            #print(k,v)
            dS = []
            for i in range(len(v)-1):
                #print(v[i])
                if v[i] != 0:
                    dS.append(v[i+1]/v[i])
            dS_sorted = sorted(dS)
            n1 = 0.2 * len(dS)
            n2 = 0.75 * len(dS)
            #print(dS_sorted)
            stdS = dS_sorted[round(n2)] - dS_sorted[round(n1)]
            medN = np.median(np.array(dS))
            print(n1,n2,stdS,medN)
            for i in range(len(v)):
                if abs(v[i] - medN) > noiseThresh*stdS:
                    v[i] = np.nan

        #ds.columns = columns
        ds.columnsToDataset()

    @staticmethod
    def processDataDeglitching(node, sensorType):
        darkData = None
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and gp.hasDataset(sensorType):
                darkData = gp.getDataset(sensorType)
      
        ProcessL2.dataDeglitching(darkData)



    @staticmethod
    # This does not change the HDF object
    def darkCorrection(darkData, darkTimer, lightData, lightTimer):
        if (darkData == None) or (lightData == None):
            print("Dark Correction, dataset not found:", darkData, lightData)
            return False

        '''        
        # Prosoft - Replace Light Timer with closest value in Dark Timer, interpolate Light Data
        print("Test interpolate light data", lightData.id)
        oldLightTimer = np.copy(lightTimer.data["NONE"]).tolist()
        j = 0
        for i in range(len(darkTimer.data["NONE"])):
            v = darkTimer.data["NONE"][i]
            closest = [0, abs(lightTimer.data["NONE"][0] - v)]
            for j in range(1, len(lightTimer.data["NONE"])):
                if abs(lightTimer.data["NONE"][j] - v) < closest[1]:
                    closest[0] = j
                    closest[1] = abs(lightTimer.data["NONE"][j] - v)
            if closest[0] != len(lightTimer.data["NONE"])-1:
                #print(closest)
                lightTimer.data["NONE"][closest[0]] = v

        newLightData = np.copy(lightData.data)
        for k in darkData.data.dtype.fields.keys():
            x = np.copy(oldLightTimer).tolist()
            y = np.copy(lightData.data[k]).tolist()
            #print("t1", len(x), len(y))
            #print(len(x),len(y))
            new_x = lightTimer.data["NONE"]
            #newLightData[k] = Utilities.interp(x,y,new_x,'linear')
            newLightData[k] = Utilities.interp(x,y,new_x,'cubic')
        lightData.data = newLightData
        '''

        if Utilities.hasNan(darkData):
           print("Found NAN 1")
           exit

        # Interpolate Dark Dataset to match number of elements as Light Dataset
        newDarkData = np.copy(lightData.data)
        # print(darkTimer.data["NONE"])
        for k in darkData.data.dtype.fields.keys(): # For each wavelength
            x = np.copy(darkTimer.data["NONE"]).tolist() # darktimer
            y = np.copy(darkData.data[k]).tolist()  # data at that band over time
            new_x = lightTimer.data["NONE"]         # lighttimer

            if len(x) < 3 or len(y) < 3 or len(new_x) < 3:
                print("Cannot do cubic spline interpolation, length of datasets < 3")
                return False

            if not Utilities.isIncreasing(x):
                print("darkTimer does not contain strictly increasing values")
                #return False
            if not Utilities.isIncreasing(new_x):
                print("lightTimer does not contain strictly increasing values")
                #return False

            #print(x[0], new_x[0])
            #newDarkData[k] = Utilities.interp(x,y,new_x,'cubic')
            newDarkData[k] = Utilities.interpSpline(x,y,new_x)

        darkData.data = newDarkData

        #if Utilities.hasNan(darkData):
        #    print("Found NAN 2")
        #    exit

        #print(lightData.data.shape)
        #print(newDarkData.shape)

        # Correct light data by subtracting interpolated dark data from light data
        for k in lightData.data.dtype.fields.keys():
            for x in range(lightData.data.shape[0]):
                lightData.data[k][x] -= newDarkData[k][x]

        # NOW THAT THE LIGHTDATA HAS BEEN CORRECTED, WHAT HAPPENS TO IT? WHERE IS IT 
        # PLACED WITHIN THE HDF OBJECT???

        #print(lightData.data)
        return True


    # Copies TIMETAG2 values to Timer and converts to seconds
    @staticmethod
    def copyTimetag2(timerDS, tt2DS):
        if (timerDS.data is None) or (tt2DS.data is None):
            print("copyTimetag2: Timer/TT2 is None")
            return

        #print("Time:", time)
        #print(ds.data)
        for i in range(0, len(timerDS.data)):
            tt2 = float(tt2DS.data["NONE"][i])
            t = Utilities.timeTag2ToSec(tt2)
            timerDS.data["NONE"][i] = t
        

    # Finds minimum timer stamp between dark and light, and starts there
    # Resets this time to zero, and increments dark and light by the minimum
    # increment in the light timer. 
    # 
    # THIS DOESN'T MAKE SENSE. DARK TIME AND LIGHT TIME WILL BE ON DIFFERING
    # INTERVALS THANKS TO INTEGRATION TIME, RIGHT?
    # DARK DATA NEEDS TO BE ALIGNED SOMEHOW SO EACH LIGHT CAN HAVE THE NEAREST
    # DARK SAMPLE SUBTRACTED.
    @staticmethod
    def processTimer(darkTimer, lightTimer):

        if (darkTimer.data is None) or (lightTimer.data is None):
            return

        t0 = lightTimer.data["NONE"][0]
        t1 = lightTimer.data["NONE"][1]
        #offset = t1 - t0

        # Finds the minimum cycle time of the instrument to use as offset
        min0 = t1 - t0
        total = len(lightTimer.data["NONE"])
        #print("test avg")
        for i in range(1, total):
            num = lightTimer.data["NONE"][i] - lightTimer.data["NONE"][i-1]
            if num < min0 and num > 0:
                min0 = num
        offset = min0
        #print("min:",min0)

        # Set start time to minimum of light/dark timer values
        if darkTimer.data["NONE"][0] < t0:
            t0 = darkTimer.data["NONE"][0]

        # Recalculate timers by subtracting start time and adding offset
        #print("Time:", time)
        #print(darkTimer.data)
        for i in range(0, len(darkTimer.data)):
            darkTimer.data["NONE"][i] += -t0 + offset
        for i in range(0, len(lightTimer.data)):
            lightTimer.data["NONE"][i] += -t0 + offset
        #print(darkTimer.data)


    # Used to correct TIMETAG2 values if they are not strictly increasing
    # (strictly increasing values required for interpolation)
    @staticmethod
    def fixTimeTag2(gp):
        tt2 = gp.getDataset("TIMETAG2")
        total = len(tt2.data["NONE"])
        # Check the first element prior to looping over rest
        i = 0
        num = tt2.data["NONE"][i+1] - tt2.data["NONE"][i]
        if num <= 0:
                gp.datasetDeleteRow(i)
                total = total - 1
                print('Out of order TIMETAG2 row deleted at ' + str(i))
        i = 1
        while i < total:
            num = tt2.data["NONE"][i] - tt2.data["NONE"][i-1]
            if num <= 0:
                gp.datasetDeleteRow(i)
                total = total - 1
                print('Out of order TIMETAG2 row deleted at ' + str(i))
                continue
            i = i + 1


    @staticmethod
    def processDarkCorrection(node, sensorType):
        print("Dark Correction:", sensorType)
        darkGroup = None
        darkData = None
        darkTimer = None
        lightGroup = None
        lightData = None
        lightTimer = None

        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensorType):
                darkGroup = gp
                darkData = gp.getDataset(sensorType)
                darkTimer = gp.getDataset("TIMER")
                darkTT2 = gp.getDataset("TIMETAG2")

            if gp.attributes["FrameType"] == "ShutterLight" and gp.getDataset(sensorType):
                lightGroup = gp
                lightData = gp.getDataset(sensorType)
                lightTimer = gp.getDataset("TIMER")
                lightTT2 = gp.getDataset("TIMETAG2")

        if darkGroup is None or lightGroup is None:
            print("No radiometry found for " + sensorType)
            return False

        # Fix in case time doesn't increase from one sample to the next
        ProcessL2.fixTimeTag2(darkGroup)
        ProcessL2.fixTimeTag2(lightGroup)        

        ProcessL2.copyTimetag2(darkTimer, darkTT2)
        ProcessL2.copyTimetag2(lightTimer, lightTT2)
        # ProcessL2.processTimer(darkTimer, lightTimer)
        if not ProcessL2.darkCorrection(darkData, darkTimer, lightData, lightTimer):
            print("ProcessL2.darkCorrection failed  for " + sensorType)
            return False
            
        # Now that the dark correction is done, we can strip the dark shutter data from the        
        # HDF object.            
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensorType):                
                node.removeGroup(gp)

        return True


    # Applies dark data correction / data deglitching
    @staticmethod
    def processL2(node):
        root = HDFRoot.HDFRoot()
        root.copy(node) #  Copy everything from the L1b file into the new HDF object

        root.attributes["PROCESSING_LEVEL"] = "2"
        root.attributes["DEGLITCH_PRODAT"] = "OFF"
        root.attributes["DEGLITCH_REFDAT"] = "OFF"
        #root.attributes["STRAY_LIGHT_CORRECT"] = "OFF"
        #root.attributes["THERMAL_RESPONSIVITY_CORRECT"] = "OFF"

        #ProcessL2.processDataDeglitching(root, "ES")
        #ProcessL2.processDataDeglitching(root, "LI")
        #ProcessL2.processDataDeglitching(root, "LT")

        if not ProcessL2.processDarkCorrection(root, "ES"):
            print('Error dark correcting ES')
            return None
        if not ProcessL2.processDarkCorrection(root, "LI"):
            print('Error dark correcting LI')
            return None
        if not ProcessL2.processDarkCorrection(root, "LT"):
            print('Error dark correcting LT')
            return None

        return root
