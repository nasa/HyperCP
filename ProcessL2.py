
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt

import HDFRoot
#import HDFGroup
#import HDFDataset

from ConfigFile import ConfigFile
from Utilities import Utilities



class ProcessL2:
    '''
    # The Deglitching process departs signicantly from ProSoft and PySciDON
    # Reference: ProSoft 7.7 Rev. K May 8, 2017, SAT-DN-00228
    # More information can be found in AnomalyDetection.py
    '''    
    @staticmethod
    def darkDataDeglitching(darkData, sensorType):        
        ''' Dark deglitching is now based on double-pass discrete linear convolution of the residual 
        with a stationary std over a rolling average'''        
        # print(str(sensorType))
        windowSize = int(ConfigFile.settings["fL2Deglitch0"])
        sigma = float(ConfigFile.settings["fL2Deglitch2"])

        darkData.datasetToColumns()
        columns = darkData.columns

        waveindex = 0
        for k in columns.items():   # Loop over all wavebands     
            timeSeries = k[1]            
            # Note: the moving average is not tolerant to 2 or fewer records
            avg = Utilities.movingAverage(timeSeries, windowSize).tolist()        
            # avg = Utilities.windowAverage(timeSeries, windowSize).mean().values.tolist()  
            residual = np.array(timeSeries) - np.array(avg)
            stdData = np.std(residual)                                  

            # First pass
            badIndex1 = Utilities.darkConvolution(timeSeries,avg,stdData,sigma)  

            # Second pass
            timeSeries2 = np.array(timeSeries[:])
            timeSeries2[badIndex1] = np.nan
            timeSeries2 = timeSeries2.tolist()
            avg2 = Utilities.movingAverage(timeSeries2, windowSize).tolist()        
            # avg2 = Utilities.windowAverage(timeSeries2, windowSize).mean().values.tolist()        
            residual = np.array(timeSeries2) - np.array(avg2)
            stdData = np.nanstd(residual)        

            badIndex2 = Utilities.darkConvolution(timeSeries2,avg2,stdData,sigma)  
            
            # This will eliminate data from all wavebands for glitches found in any one waveband        
            if waveindex==0:
                badIndex = badIndex1[:]
                
            for i in range(len(badIndex)):
                if badIndex1[i] is True or badIndex2[i] is True:
                    badIndex[i] = True
            # print(badIndex[i])                
            waveindex += 1
        return badIndex
           
    @staticmethod
    def lightDataDeglitching(lightData, sensorType):        
        ''' Light deglitching is now based on double-pass discrete linear convolution of the residual
        with a ROLLING std over a rolling average'''        
        # print(str(sensorType))
        windowSize = int(ConfigFile.settings["fL2Deglitch1"])
        sigma = float(ConfigFile.settings["fL2Deglitch3"])

        lightData.datasetToColumns()
        columns = lightData.columns

        waveindex = 0
        for k in columns.items():        
            timeSeries = k[1]       
            # Note: the moving average is not tolerant to 2 or fewer records     
            avg = Utilities.movingAverage(timeSeries, windowSize).tolist()        
            residual = np.array(timeSeries) - np.array(avg)
                           
             # Calculate the variation in the distribution of the residual
            residualDf = pd.DataFrame(residual)
            testing_std_as_df = residualDf.rolling(windowSize).std()
            rolling_std = testing_std_as_df.replace(np.nan,
                testing_std_as_df.iloc[windowSize - 1]).round(3).iloc[:,0].tolist() 
            # This rolling std on the residual has a tendancy to blow up for extreme outliers,
            # replace it with the median residual std when that happens
            y = np.array(rolling_std)
            y[y > np.median(y)+3*np.std(y)] = np.median(y)
            rolling_std = y.tolist()

            
            # First pass
            badIndex1 = Utilities.lightConvolution(timeSeries,avg,rolling_std,sigma)

            # Second pass
            timeSeries2 = np.array(timeSeries[:])
            timeSeries2[badIndex1] = np.nan
            timeSeries2 = timeSeries2.tolist()
            avg2 = Utilities.movingAverage(timeSeries2, windowSize).tolist()        
            # avg2 = Utilities.windowAverage(timeSeries2, windowSize).mean.values.tolist()        
            residual2 = np.array(timeSeries2) - np.array(avg2)        
            # Calculate the variation in the distribution of the residual
            residualDf2 = pd.DataFrame(residual2)
            testing_std_as_df2 = residualDf2.rolling(windowSize).std()
            rolling_std2 = testing_std_as_df2.replace(np.nan,
                testing_std_as_df2.iloc[windowSize - 1]).round(3).iloc[:,0].tolist()
            # This rolling std on the residual has a tendancy to blow up for extreme outliers,
            # replace it with the median residual std when that happens
            y = np.array(rolling_std2)
            y[np.isnan(y)] = np.nanmedian(y)
            y[y > np.nanmedian(y)+3*np.nanstd(y)] = np.nanmedian(y)
            rolling_std2 = y.tolist()

            badIndex2 = Utilities.lightConvolution(timeSeries2,avg2,rolling_std2,sigma)
            
            # This will eliminate data from all wavebands for glitches found in any one waveband        
            if waveindex==0:
                badIndex = badIndex1[:]
                
            for i in range(len(badIndex)):
                if badIndex1[i] is True or badIndex2[i] is True:
                    badIndex[i] = True
            # print(badIndex[i])                
            waveindex += 1
        return badIndex

    @staticmethod
    def processDataDeglitching(node, sensorType):   
        print(sensorType)     
        darkData = None
        lightData = None
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                darkData = gp.getDataset(sensorType)
            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
            
            # Rolling averages required for deglitching of data are intolerant to 2 or fewer data points
            # Furthermore, 5 or fewer datapoints is a suspiciously short sampling time. Finally,
            # Having fewer data points than the size of the rolling window won't work. Exit processing if 
            # these conditions are met.
            windowSizeDark = int(ConfigFile.settings["fL2Deglitch0"])
            windowSizeLight = int(ConfigFile.settings["fL2Deglitch1"])
            if darkData is not None and lightData is not None:
                if len(darkData.data) <= 2 or \
                    len(lightData.data) <= 5 or \
                    len(darkData.data) < windowSizeDark or \
                    len(lightData.data) < windowSizeLight:
                        return True

        if darkData is None:
            print("Error: No dark data to deglitch")
        else:
            print("Deglitching dark")
            badIndexDark = ProcessL2.darkDataDeglitching(darkData, sensorType)
            print('Data reduced by ' + str(sum(badIndexDark)) + ' (' + \
                str(round(100*sum(badIndexDark)/len(darkData.data))) + '%)')
            

        if lightData is None:
            print("Error: No light data to deglitch")
        else:    
            print("Deglitching light")
            badIndexLight = ProcessL2.lightDataDeglitching(lightData, sensorType)      
            print('Data reduced by ' + str(sum(badIndexLight)) + ' (' + \
                str(round(100*sum(badIndexLight)/len(lightData.data))) + '%)')      

        # Delete the glitchy rows of the datasets
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
               gp.datasetDeleteRow(np.where(badIndexDark))

            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
                gp.datasetDeleteRow(np.where(badIndexLight))
                
        return False
            

    @staticmethod
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
            print("**************Found NAN 0")
            exit
        if Utilities.hasNan(darkData):
           print("**************Found NAN 1")
           exit

        # Interpolate Dark Dataset to match number of elements as Light Dataset
        newDarkData = np.copy(lightData.data)        
        for k in darkData.data.dtype.fields.keys(): # For each wavelength
            x = np.copy(darkTimer.data["NONE"]).tolist() # darktimer
            y = np.copy(darkData.data[k]).tolist()  # data at that band over time
            new_x = lightTimer.data["NONE"].tolist()  # lighttimer

            if len(x) < 3 or len(y) < 3 or len(new_x) < 3:
                print("**************Cannot do cubic spline interpolation, length of datasets < 3")
                return False

            if not Utilities.isIncreasing(x):
                print("**************darkTimer does not contain strictly increasing values")
                return False
            if not Utilities.isIncreasing(new_x):
                print("**************lightTimer does not contain strictly increasing values")
                return False

            # print(x[0], new_x[0])
            #newDarkData[k] = Utilities.interp(x,y,new_x,'cubic')
            if len(x) > 3:
                newDarkData[k] = Utilities.interpSpline(x,y,new_x)
            else:
                print('**************Record too small for splining. Exiting.')
                return False
            # plt.plot(x,y,'ro')
            # # plt.plot(new_x,newDarkData[k],'bo')
            # plt.show()
            # print('asdf')

        darkData.data = newDarkData

        if Utilities.hasNan(darkData):
            print("**************Found NAN 2")
            exit

        #print(lightData.data.shape)
        #print(newDarkData.shape)

        # Correct light data by subtracting interpolated dark data from light data
        for k in lightData.data.dtype.fields.keys():
            for x in range(lightData.data.shape[0]):
                # THIS CHANGES NOT ONLY lightData, BUT THE ROOT OBJECT gp FROM processDarkCorrection
                lightData.data[k][x] -= newDarkData[k][x]

        if Utilities.hasNan(lightData):
            print("**************Found NAN 3")
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
        if total >= 2:
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
        else:
            print('************Too few records to test for ascending timestamps. Exiting.')
            return False


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
        # or there are fewer than 2 two stamps remaining.
        fixTimeFlagDark = ProcessL2.fixTimeTag2(darkGroup)
        fixTimeFlagLight = ProcessL2.fixTimeTag2(lightGroup)        

        if fixTimeFlagLight is False or fixTimeFlagDark is False:
            return False

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
            flagES = ProcessL2.processDataDeglitching(root, "ES")
            flagLI = ProcessL2.processDataDeglitching(root, "LI")
            flagLT = ProcessL2.processDataDeglitching(root, "LT")

            if flagES or flagLI or flagLT:
                print('***********Too few records in the file to continue. Exiting.')
                return None

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
