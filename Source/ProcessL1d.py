
import os
import numpy as np
import datetime as dt
import pandas as pd
import calendar
# import matplotlib.pyplot as plt

from HDFRoot import HDFRoot
from MainConfig import MainConfig
from ConfigFile import ConfigFile
# from AnomalyDetection import AnomAnalWindow
from Utilities import Utilities

class ProcessL1d:
    '''
    # The Deglitching process departs signicantly from ProSoft and PySciDON
    # Reference: ProSoft 7.7 Rev. K May 8, 2017, SAT-DN-00228
    # More information can be found in AnomalyDetection.py
    '''

    @staticmethod
    def darkDataDeglitching(darkData, sensorType, windowSize, sigma):
        ''' Dark deglitching is now based on double-pass discrete linear convolution of the residual
        with a stationary std over a rolling average.

        TBD: This is very aggressive in that it eliminates data in all bands if a record in any band fails
            the test. This is why the percentages in the logs appear much higher than the knockouts in any
            given band (as seen in the plots). Could be revisited. '''

        # windowSize = int(ConfigFile.settings["fL1dDeglitch0"])
        # sigma = float(ConfigFile.settings["fL1dDeglitch2"])
        # This is a hardcoding of the min/max bands in which to perform deglitching
        minBand = ConfigFile.minDeglitchBand
        maxBand = ConfigFile.maxDeglitchBand

        darkData.datasetToColumns()
        columns = darkData.columns

        # waveindex = 0
        badIndex = [False] * len(darkData.data)
        for key,timeSeries in columns.items():   # Loop over all wavebands
            if float(key) > minBand and float(key) < maxBand:
                # Note: the moving average is not tolerant to 2 or fewer records
                avg = Utilities.movingAverage(timeSeries, windowSize).tolist()
                # avg = Utilities.windowAverage(timeSeries, windowSize).mean().values.tolist()
                residual = np.array(timeSeries) - np.array(avg)
                stdData = np.std(residual)

                # First pass
                badIndex1 = Utilities.darkConvolution(timeSeries,avg,stdData,sigma)

                # Second pass
                timeSeries2 = np.array(timeSeries[:])
                timeSeries2[badIndex1] = np.nan # BEWARE: NaNs introduced
                timeSeries2 = timeSeries2.tolist()
                avg2 = Utilities.movingAverage(timeSeries2, windowSize).tolist()
                # avg2 = Utilities.windowAverage(timeSeries2, windowSize).mean().values.tolist()
                residual = np.array(timeSeries2) - np.array(avg2)
                stdData = np.nanstd(residual)

                badIndex2 = Utilities.darkConvolution(timeSeries2,avg2,stdData,sigma)

                # This setup will later eliminate data from all wavebands for glitches found in any one waveband
                # if waveindex==0:
                #     # badIndex = badIndex1[:]
                #     for i in range(len(badIndex1)):
                #         if badIndex1[i] is True or badIndex2[i] is True:
                #             badIndex.append(True)
                #         else:
                #             badIndex.append(False)
                # else:
                for i in range(len(badIndex)):
                    if badIndex1[i] is True or badIndex2[i] is True or badIndex[i] is True:
                        badIndex[i] = True
                    else:
                        badIndex[i] = False # this is redundant
                # print(badIndex[i])
                # waveindex += 1
        return badIndex

    @staticmethod
    def lightDataDeglitching(lightData, sensorType, windowSize, sigma):
        ''' Light deglitching is now based on double-pass discrete linear convolution of the residual
        with a ROLLING std over a rolling average'''

        # print(str(sensorType))
        # windowSize = int(ConfigFile.settings["fL1dDeglitch1"])
        # sigma = float(ConfigFile.settings["fL1dDeglitch3"])
        minBand = ConfigFile.minDeglitchBand
        maxBand = ConfigFile.maxDeglitchBand

        lightData.datasetToColumns()
        columns = lightData.columns

        badIndex = [False] * len(lightData.data)
        for key,timeSeries in columns.items():   # Loop over all wavebands
            if float(key) > minBand and float(key) < maxBand:
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
                # if waveindex==0:
                #     # badIndex = badIndex1[:]
                #     for i in range(len(badIndex1)):
                #         if badIndex1[i] is True or badIndex2[i] is True:
                #             badIndex.append(True)
                #         else:
                #             badIndex.append(False)
                # else:
                for i in range(len(badIndex)):
                    if badIndex1[i] is True or badIndex2[i] is True or badIndex[i] is True:
                        badIndex[i] = True
                    else:
                        badIndex[i] = False # this is redundant
                # print(badIndex[i])
                # waveindex += 1
        return badIndex

    @staticmethod
    def processDataDeglitching(node, sensorType):
        msg = sensorType
        print(msg)
        Utilities.writeLogFile(msg)

        step = float(ConfigFile.settings["fL1dAnomalyStep"])

        # outDir = MainConfig.settings["outDir"]
        # # If default output path is used, choose the root HyperInSPACE path, and build on that
        # if os.path.abspath(outDir) == os.path.join('./','Data'):
        #     outDir = './'

        # if not os.path.exists(os.path.join(outDir,'Plots','L1C_Anoms')):
        #     os.makedirs(os.path.join(outDir,'Plots','L1C_Anoms'))
        # plotdir = os.path.join(outDir,'Plots','L1C_Anoms')
        # fileName is the pathless basename (no extention) of the L1C file
        rawFileName = node.attributes['RAW_FILE_NAME']
        L1CfileName = f"{rawFileName.split('.')[0]}_L1C"

        darkData = None
        lightData = None

        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                darkData = gp.getDataset(sensorType)
                darkDateTime = Utilities.getDateTime(gp)
                windowDark = int(ConfigFile.settings[f'fL1d{sensorType}WindowDark'])
                sigmaDark = float(ConfigFile.settings[f'fL1d{sensorType}SigmaDark'])
                minDark = None if ConfigFile.settings[f'fL1d{sensorType}MinDark']=='None' else ConfigFile.settings[f'fL1d{sensorType}MinDark']
                maxDark = None if ConfigFile.settings[f'fL1d{sensorType}MaxDark']=='None' else ConfigFile.settings[f'fL1d{sensorType}MaxDark']
                minMaxBandDark = ConfigFile.settings[f'fL1d{sensorType}MinMaxBandDark']
            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
                lightDateTime = Utilities.getDateTime(gp)
                windowLight = int(ConfigFile.settings[f'fL1d{sensorType}WindowLight'])
                sigmaLight = float(ConfigFile.settings[f'fL1d{sensorType}SigmaLight'])
                minLight = None if ConfigFile.settings[f'fL1d{sensorType}MinLight']=='None' else ConfigFile.settings[f'fL1d{sensorType}MinLight']
                maxLight = None if ConfigFile.settings[f'fL1d{sensorType}MaxLight']=='None' else ConfigFile.settings[f'fL1d{sensorType}MaxLight']
                minMaxBandLight = ConfigFile.settings[f'fL1d{sensorType}MinMaxBandLight']

            # Rolling averages required for deglitching of data are intolerant to 2 or fewer data points
            # Furthermore, 5 or fewer datapoints is a suspiciously short sampling time. Finally,
            # Having fewer data points than the size of the rolling window won't work. Exit processing if
            # these conditions are met.

        # Problems with the sizes of the datasets:
        if darkData is not None and lightData is not None:
            if len(darkData.data) <= 2 or \
                len(lightData.data) <= 5 or \
                len(darkData.data) < windowDark or \
                len(lightData.data) < windowLight:
                    msg = f'Error: Too few records to deglitch. Darks: {len(darkData.data)} Lights: {len(lightData.data)}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return True # Sets the flag to true

        if darkData is None:
            msg = "Error: No dark data to deglitch"
            print(msg)
            Utilities.writeLogFile(msg)
        else:
            msg = "Deglitching dark"
            print(msg)
            Utilities.writeLogFile(msg)
            lightDark = 'Dark'

            darkData.datasetToColumns()
            columns = darkData.columns
            dateTime = darkDateTime

            globalBadIndex = []

            index = 0
            # Loop over bands to populate globBads
            for timeSeries in columns.items():
                if index==0:
                    # Initialize boolean lists for capturing global badIndex conditions across all wavebands
                    globBad = [False]*len(timeSeries[1])
                    globBad2 = [False]*len(timeSeries[1])
                    globBad3 = [False]*len(timeSeries[1])
                band = float(timeSeries[0])
                if band > ConfigFile.minDeglitchBand and band < ConfigFile.maxDeglitchBand:
                    # if index % step == 0:
                    radiometry1D = timeSeries[1]
                    badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(band,radiometry1D, windowDark, sigmaDark, lightDark, minDark, maxDark,minMaxBandDark)

                    # for the plotting routine:
                    globBad[:] = (True if val2 else val1 for (val1,val2) in zip(globBad,badIndex))
                    globBad2[:] = (True if val2 else val1 for (val1,val2) in zip(globBad2,badIndex2))
                    globBad3[:] = (True if val2 else val1 for (val1,val2) in zip(globBad3,badIndex3))

                    # For the deletion routine:
                    globalBadIndex.append(badIndex) # First pass
                    globalBadIndex.append(badIndex2) # Second pass
                    globalBadIndex.append(badIndex3) # Thresholds

                index +=1

             # Collapse the badIndexes from all wavebands into one timeseries
            # Convert to an array and test along the columns (i.e. each timestamp)
            gIndex = np.any(np.array(globalBadIndex), 0)
            percentLoss = 100*(sum(gIndex)/len(gIndex))
            # badIndexDark = ProcessL1d.darkDataDeglitching(darkData, sensorType, windowDark, sigmaDark)
            msg = f'Data reduced by {sum(gIndex)} ({round(percentLoss)}%)'
            print(msg)
            Utilities.writeLogFile(msg)
            badIndexDark = gIndex

            # Now plot a selection of these USING UNIVERSALLY EXCLUDED INDEXES
            index =0
            for timeSeries in columns.items():
                band = float(timeSeries[0])
                if band > ConfigFile.minDeglitchBand and band < ConfigFile.maxDeglitchBand:
                    if index % step == 0:
                        Utilities.saveDeglitchPlots(L1CfileName,timeSeries,dateTime,sensorType,lightDark,windowDark,sigmaDark,globBad,globBad2,globBad3)
                index +=1


        if lightData is None:
            msg = "Error: No light data to deglitch"
            print(msg)
            Utilities.writeLogFile(msg)
        else:
            msg = "Deglitching light"
            print(msg)
            Utilities.writeLogFile(msg)

            lightData.datasetToColumns()
            columns = lightData.columns
            lightDark = 'Light'
            dateTime = lightDateTime

            globalBadIndex = []

            index = 0
            # Loop over bands to populate globBads
            for timeSeries in columns.items():
                if index==0:
                    # Initialize boolean lists for capturing global badIndex conditions across all wavebands
                    globBad = [False]*len(timeSeries[1])
                    globBad2 = [False]*len(timeSeries[1])
                    globBad3 = [False]*len(timeSeries[1])
                band = float(timeSeries[0])
                if band > ConfigFile.minDeglitchBand and band < ConfigFile.maxDeglitchBand:
                    # if index % step == 0:
                    radiometry1D = timeSeries[1]
                    badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(band,radiometry1D, windowLight, sigmaLight, lightDark, minLight, maxLight,minMaxBandLight)

                    # For plotting:
                    globBad[:] = (True if val2 else val1 for (val1,val2) in zip(globBad,badIndex))
                    globBad2[:] = (True if val2 else val1 for (val1,val2) in zip(globBad2,badIndex2))
                    globBad3[:] = (True if val2 else val1 for (val1,val2) in zip(globBad3,badIndex3))

                    # For deletion:
                    globalBadIndex.append(badIndex)
                    globalBadIndex.append(badIndex2)
                    globalBadIndex.append(badIndex3)
                index +=1

            # Collapse the badIndexes from all wavebands into one timeseries
            # Convert to an array and test along the columns (i.e. each timestamp)
            gIndex = np.any(np.array(globalBadIndex), 0)
            percentLoss = 100*(sum(gIndex)/len(gIndex))
            # badIndexLight = ProcessL1d.lightDataDeglitching(lightData, sensorType, windowLight, sigmaLight)
            msg = f'Data reduced by {sum(gIndex)} ({round(percentLoss)}%)'
            print(msg)
            Utilities.writeLogFile(msg)
            badIndexLight = gIndex

            # Now plot a selection of these USING UNIVERSALLY EXCLUDED INDEXES
            index =0
            for timeSeries in columns.items():
                band = float(timeSeries[0])
                if band > ConfigFile.minDeglitchBand and band < ConfigFile.maxDeglitchBand:
                    if index % step == 0:
                        Utilities.saveDeglitchPlots(L1CfileName,timeSeries,dateTime,sensorType,lightDark,windowLight,sigmaLight,globBad,globBad2,globBad3)
                index +=1

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
            msg  = f'Dark Correction, dataset not found: {darkData} , {lightData}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        '''
        # HyperInSPACE - Interpolate Dark values to match light measurements (e.g. Brewin 2016, Prosoft
        # 7.7 User Manual SAT-DN-00228-K)
        '''

        if Utilities.hasNan(lightData):
            msg = "**************Found NAN 0"
            print(msg)
            Utilities.writeLogFile(msg)
            exit

        if Utilities.hasNan(darkData):
            msg = "**************Found NAN 1"
            print(msg)
            Utilities.writeLogFile(msg)
            exit

        # Interpolate Dark Dataset to match number of elements as Light Dataset
        newDarkData = np.copy(lightData.data)
        for k in darkData.data.dtype.fields.keys(): # For each wavelength
            # x = np.copy(darkTimer.data["NONE"]).tolist() # darktimer
            x = np.copy(darkTimer.data).tolist() # darktimer
            y = np.copy(darkData.data[k]).tolist()  # data at that band over time
            # new_x = lightTimer.data["NONE"].tolist()  # lighttimer
            new_x = lightTimer.data  # lighttimer

            if len(x) < 3 or len(y) < 3 or len(new_x) < 3:
                msg = "**************Cannot do cubic spline interpolation, length of datasets < 3"
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            if not Utilities.isIncreasing(x):
                msg = "**************darkTimer does not contain strictly increasing values"
                print(msg)
                Utilities.writeLogFile(msg)
                return False
            if not Utilities.isIncreasing(new_x):
                msg = "**************lightTimer does not contain strictly increasing values"
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            # print(x[0], new_x[0])
            #newDarkData[k] = Utilities.interp(x,y,new_x,'cubic')
            if len(x) >= 3:
                # newDarkData[k] = Utilities.interpSpline(x,y,new_x)

                # Because x is now a list of datetime tuples, they'll need to be
                # converted to Unix timestamp values
                xTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in x]
                newXTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in new_x]

                # newDarkData[k] = Utilities.interp(x,y,new_x, fill_value=np.nan)
                newDarkData[k] = Utilities.interp(xTS,y,newXTS, fill_value=np.nan)


                for val in newDarkData[k]:
                    if np.isnan(val):
                        print('nan')
                        exit
                # newDarkData[k] = Utilities.interp(x,y,new_x)
            else:
                msg = '**************Record too small for splining. Exiting.'
                print(msg)
                Utilities.writeLogFile(msg)
                return False

        darkData.data = newDarkData

        if Utilities.hasNan(darkData):
            msg = "**************Found NAN 2"
            print(msg)
            Utilities.writeLogFile(msg)
            exit

        # Correct light data by subtracting interpolated dark data from light data
        for k in lightData.data.dtype.fields.keys():
            for x in range(lightData.data.shape[0]):
                lightData.data[k][x] -= newDarkData[k][x]

        if Utilities.hasNan(lightData):
            msg = "**************Found NAN 3"
            print(msg)
            Utilities.writeLogFile(msg)
            exit

        return True


    # Copies TIMETAG2 values to Timer and converts to seconds
    @staticmethod
    def copyTimetag2(timerDS, tt2DS):
        if (timerDS.data is None) or (tt2DS.data is None):
            msg = "copyTimetag2: Timer/TT2 is None"
            print(msg)
            Utilities.writeLogFile(msg)
            return

        #print("Time:", time)
        #print(ds.data)
        for i in range(0, len(timerDS.data)):
            tt2 = float(tt2DS.data["NONE"][i])
            t = Utilities.timeTag2ToSec(tt2)
            timerDS.data["NONE"][i] = t

    @staticmethod
    def processDarkCorrection(node, sensorType):
        msg = f'Dark Correction: {sensorType}'
        print(msg)
        Utilities.writeLogFile(msg)
        darkGroup = None
        darkData = None
        darkDateTime = None
        lightGroup = None
        lightData = None
        lightDateTime = None

        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensorType):
                darkGroup = gp
                darkData = gp.getDataset(sensorType)
                darkDateTime = gp.getDataset("DATETIME")

            if gp.attributes["FrameType"] == "ShutterLight" and gp.getDataset(sensorType):
                lightGroup = gp
                lightData = gp.getDataset(sensorType)
                lightDateTime = gp.getDataset("DATETIME")

        if darkGroup is None or lightGroup is None:
            msg = f'No radiometry found for {sensorType}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        # Instead of using TT2 or seconds, use python datetimes to avoid problems crossing
        # UTC midnight.
        if not ProcessL1d.darkCorrection(darkData, darkDateTime, lightData, lightDateTime):
            msg = f'ProcessL1d.darkCorrection failed  for {sensorType}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        # Now that the dark correction is done, we can strip the dark shutter data from the
        # HDF object.
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensorType):
                node.removeGroup(gp)
        # And rename the corrected light frame
        for gp in node.groups:
            if gp.attributes["FrameType"] == "ShutterLight" and gp.getDataset(sensorType):
                gp.id = gp.id[0:2] # Strip off "_LIGHT" from the name
        return True

    @staticmethod
    def processL1d(node):
        '''
        Apply data deglitching to light and shutter-dark data, then apply dark shutter correction to light data.
        '''
        root = HDFRoot()
        root.copy(node)
        root.attributes["PROCESSING_LEVEL"] = "1d"
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        root.attributes["FILE_CREATION_TIME"] = timestr
        if ConfigFile.settings['bL1dDeglitch']:
            root.attributes['L1D_DEGLITCH'] = 'ON'
            for sensor in ["ES","LI","LT"]:
                ''' If parameters were picked up from an anoms.csv file, ConfigFile.settings were updated in Controller to reflect
                    these saved parameters. Now push them into root attributes for posterity.'''
                root.attributes[f'{sensor}_WINDOW_DARK'] = str(ConfigFile.settings[f'fL1d{sensor}WindowDark'])
                root.attributes[f'{sensor}_WINDOW_LIGHT'] = str(ConfigFile.settings[f'fL1d{sensor}WindowLight'])
                root.attributes[f'{sensor}_SIGMA_DARK'] = str(ConfigFile.settings[f'fL1d{sensor}SigmaDark'])
                root.attributes[f'{sensor}_SIGMA_LIGHT'] = str(ConfigFile.settings[f'fL1d{sensor}SigmaLight'])
                # if ConfigFile.settings['bL1dThreshold']:
                root.attributes[f'{sensor}_MIN_DARK'] = ConfigFile.settings[f'fL1d{sensor}MinDark']
                root.attributes[f'{sensor}_MAX_DARK'] = ConfigFile.settings[f'fL1d{sensor}MaxDark']
                root.attributes[f'{sensor}_MINMAX_BAND_DARK'] = ConfigFile.settings[f'fL1d{sensor}MinMaxBandDark']
                root.attributes[f'{sensor}_MIN_LIGHT'] = ConfigFile.settings[f'fL1d{sensor}MinLight']
                root.attributes[f'{sensor}_MAX_LIGHT'] = ConfigFile.settings[f'fL1d{sensor}MaxLight']
                root.attributes[f'{sensor}_MINMAX_BAND_LIGHT'] = ConfigFile.settings[f'fL1d{sensor}MinMaxBandLight']

        msg = f"ProcessL1d.processL1d: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        root  = Utilities.rootAddDateTime(root)

        # Fix in case time doesn't increase from one sample to the next
        # or there are fewer than 2 two stamps remaining.
        for gp in root.groups:
            if gp.id != "SOLARTRACKER_STATUS":
                msg = f'Screening {gp.id} for clean timestamps.'
                print(msg)
                Utilities.writeLogFile(msg)
                if not Utilities.fixDateTime(gp):
                    msg = f'***********Too few records in {gp.id} to continue after timestamp correction. Exiting.'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return None

        if int(ConfigFile.settings["bL1dDeglitch"]) == 1:
            flagES = ProcessL1d.processDataDeglitching(root, "ES")
            flagLI = ProcessL1d.processDataDeglitching(root, "LI")
            flagLT = ProcessL1d.processDataDeglitching(root, "LT")

            if flagES or flagLI or flagLT:
                msg = '***********Too few records in the file after deglitching to continue. Exiting.'
                print(msg)
                Utilities.writeLogFile(msg)
                return None
        # else:
            #root.attributes["STRAY_LIGHT_CORRECT"] = "OFF"
            #root.attributes["THERMAL_RESPONSIVITY_CORRECT"] = "OFF"

        if not ProcessL1d.processDarkCorrection(root, "ES"):
            msg = 'Error dark correcting ES'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1d.processDarkCorrection(root, "LI"):
            msg = 'Error dark correcting LI'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1d.processDarkCorrection(root, "LT"):
            msg = 'Error dark correcting LT'
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Datetime format is not supported in HDF5; remove
        # DATETIME is not supported in HDF5; remove
        for gp in root.groups:
            if (gp.id == "SOLARTRACKER_STATUS") is False:
                del gp.datasets["DATETIME"]

        return root
