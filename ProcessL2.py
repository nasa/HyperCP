
import numpy as np
# import matplotlib.pyplot as plt

import HDFRoot
#import HDFGroup
#import HDFDataset

from ConfigFile import ConfigFile
from Utilities import Utilities



class ProcessL2:

    '''
    # ToDo: Confirm that interpolation of timestamps is okay. Fix deglitching.
    # Reference: ProSoft 7.7 Rev. K May 8, 2017, SAT-DN-00228
    '''    
    @staticmethod
    def darkDataDeglitching(darkData, sensorType):        
        ''' Dark deglitching is very poorly described by SeaBird (pg 41).
        For now, set to NaN anything outside X STDS from the mean of the 
        dark dataset'''        
        # print(str(sensorType))
        noiseThresh = float(ConfigFile.settings["fL2Deglitch0"])

        # Copy dataset to dictionary
        darkData.datasetToColumns()
        columns = darkData.columns
        
        for k,v in columns.items(): # k is the waveband, v is the series data in the OrdDict
            stdDark = np.std(v)
            medDark = np.median(v)

            # print(str(k) + " nm Median = " + str(medDark) + " +/- " + str(stdDark) + " (1 STD)")

            counter = 0
            for i in range(len(v)):
                if abs(v[i] - medDark) > noiseThresh*stdDark:
                    v[i] = np.nan
                    # print("Dark data nan'ed at " + str(i))
                    darkData.datasetDeleteRow(i-counter)
                    print("Dark data deleted at " + str(i) + " , new index " + str(i-counter))
                    counter += 1
                                        
        darkData.columnsToDataset()

    @staticmethod
    def lightDataDeglitching(lightData, sensorType):        
        ''' The code below seems to be modeled off the ProSoft manual
        for shutter-open data (Appendix D).
        Still problems with the format and the length of dS below
        '''
        # print(str(sensorType))
        # noiseThresh = 5 default for Irradiance ("reference"), fL2Deglitch1
        # noiseThresh = 20 default for Radiance, fL2Deglitch2               
        if sensorType=="Es":
            noiseThresh = float(ConfigFile.settings["fL2Deglitch1"])
        else:
            noiseThresh = float(ConfigFile.settings["fL2Deglitch2"])        

        # Copy dataset to dictionary
        lightData.datasetToColumns()
        columns = lightData.columns

        for k,S in columns.items(): # k is the waveband, S is the series data in the OrdDict
            #print(k,v)
            dS = []

            for i in range(len(S)-1):
                #print(S[i])
                if S[i] != 0:
                    dS.append(S[i+1]/S[i])
            dS_sorted = sorted(dS)
            n1 = 0.2 * len(dS)
            n2 = 0.75 * len(dS)
            #print(dS_sorted)
            stdS = dS_sorted[round(n2)] - dS_sorted[round(n1)] # Has to be n2 - n1, or it's negative
            medN = np.median(np.array(dS))
            # print(str(k) + " nm Median = " + str(medN) + " +/- " + str(stdS) + " (1 STD)")
            
            # print(n1,n2,stdS,medN)
            # print(len(S))
            # print(len(dS))
            counter = 0
            # badIndex = []
            for i in range(len(dS)): # Had to stop at len(dS instead of len(S), or it bombs)
                if abs(dS[i] - medN) > noiseThresh*stdS:
                    S[i] = np.nan
                    # print("Light data nan'ed at " + str(i))
                    # lightData.datasetDeleteRow(i - counter)
                    # badIndex.append(i - counter)
                    print("Light data " + str(i) + " , new index " + str(i-counter) + " marked for deletion")
                    counter += 1

        lightData.columnsToDataset()
        # return badIndex # To be used for deleting the NaN'ed row of the dataset later
        # for i in range(len(badIndex)):
        #     lightData.datasetDeleteRow(badIndex[i])            

    @staticmethod
    def processDataDeglitching(node, sensorType):   
        print("Deglitching " + sensorType)     
        darkData = None
        lightData = None
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                darkData = gp.getDataset(sensorType)
            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)

        if darkData is None:
            print("Error: No dark data to deglitch")
        else:
            print("Deglitching dark")
            ProcessL2.darkDataDeglitching(darkData, sensorType)
        if lightData is None:
            print("Error: No light data to deglitch")
        else:    
            print("Deglitching light")
            ProcessL2.lightDataDeglitching(lightData, sensorType)

        # Now we need to delete the rows of the datasets that have any NaNs in them
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                darkData = gp.getDataset(sensorType)
                
            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
            

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

        if Utilities.hasNan(lightData):
            print("Found NAN 0")
            exit
        if Utilities.hasNan(darkData):
           print("Found NAN 1")
           exit

        # Interpolate Dark Dataset to match number of elements as Light Dataset
        newDarkData = np.copy(lightData.data)        
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

            # print(x[0], new_x[0])
            #newDarkData[k] = Utilities.interp(x,y,new_x,'cubic')
            newDarkData[k] = Utilities.interpSpline(x,y,new_x)
            # plt.plot(x,y,'ro')
            # # plt.plot(new_x,newDarkData[k],'bo')
            # plt.show()
            # print('asdf')

        darkData.data = newDarkData

        if Utilities.hasNan(darkData):
            print("Found NAN 2")
            exit

        #print(lightData.data.shape)
        #print(newDarkData.shape)

        # Correct light data by subtracting interpolated dark data from light data
        for k in lightData.data.dtype.fields.keys():
            for x in range(lightData.data.shape[0]):
                # THIS CHANGES NOT ONLY lightData, BUT THE ROOT OBJECT gp FROM processDarkCorrection
                lightData.data[k][x] -= newDarkData[k][x]

        if Utilities.hasNan(lightData):
            print("Found NAN 3")
            exit

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
        

    # # Finds minimum timer stamp between dark and light, and starts there
    # # Resets this time to zero, and increments dark and light by the minimum
    # # increment in the light timer. 
    # # 
    # # THIS DOESN'T MAKE SENSE. DARK TIME AND LIGHT TIME WILL BE ON DIFFERING
    # # INTERVALS THANKS TO INTEGRATION TIME, RIGHT?
    # # DARK DATA NEEDS TO BE ALIGNED SOMEHOW SO EACH LIGHT CAN HAVE THE NEAREST
    # # DARK SAMPLE SUBTRACTED.
    # @staticmethod
    # def processTimer(darkTimer, lightTimer):

    #     if (darkTimer.data is None) or (lightTimer.data is None):
    #         return

    #     t0 = lightTimer.data["NONE"][0]
    #     t1 = lightTimer.data["NONE"][1]
    #     #offset = t1 - t0

    #     # Finds the minimum cycle time of the instrument to use as offset
    #     min0 = t1 - t0
    #     total = len(lightTimer.data["NONE"])
    #     #print("test avg")
    #     for i in range(1, total):
    #         num = lightTimer.data["NONE"][i] - lightTimer.data["NONE"][i-1]
    #         if num < min0 and num > 0:
    #             min0 = num
    #     offset = min0
    #     #print("min:",min0)

    #     # Set start time to minimum of light/dark timer values
    #     if darkTimer.data["NONE"][0] < t0:
    #         t0 = darkTimer.data["NONE"][0]

    #     # Recalculate timers by subtracting start time and adding offset
    #     #print("Time:", time)
    #     #print(darkTimer.data)
    #     for i in range(0, len(darkTimer.data)):
    #         darkTimer.data["NONE"][i] += -t0 + offset
    #     for i in range(0, len(lightTimer.data)):
    #         lightTimer.data["NONE"][i] += -t0 + offset
    #     #print(darkTimer.data)


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
                lightData = gp.getDataset(sensorType) # This is a two-way equivalence. Change lightData, and it changes the ShutterLight group dataset
                lightTimer = gp.getDataset("TIMER")
                lightTT2 = gp.getDataset("TIMETAG2")

        if darkGroup is None or lightGroup is None:
            print("No radiometry found for " + sensorType)
            return False

        # Fix in case time doesn't increase from one sample to the next
        ProcessL2.fixTimeTag2(darkGroup)
        ProcessL2.fixTimeTag2(lightGroup)        

        # Replace Timer with TT2
        ProcessL2.copyTimetag2(darkTimer, darkTT2)
        ProcessL2.copyTimetag2(lightTimer, lightTT2)

        # ProcessL2.processTimer(darkTimer, lightTimer) # makes no sense

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
        if int(ConfigFile.settings["bL2Deglitch"]) == 1:
            root.attributes["DEGLITCH_PRODAT"] = "ON"
            root.attributes["DEGLITCH_REFDAT"] = "ON"
            ProcessL2.processDataDeglitching(root, "ES")
            ProcessL2.processDataDeglitching(root, "LI")
            ProcessL2.processDataDeglitching(root, "LT")

        else:
            root.attributes["DEGLITCH_PRODAT"] = "OFF"
            root.attributes["DEGLITCH_REFDAT"] = "OFF"
        #root.attributes["STRAY_LIGHT_CORRECT"] = "OFF"
        #root.attributes["THERMAL_RESPONSIVITY_CORRECT"] = "OFF"

        
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
