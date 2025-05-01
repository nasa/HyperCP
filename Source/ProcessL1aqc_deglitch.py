
import datetime as dt
import numpy as np
import pandas as pd

from Source.HDFRoot import HDFRoot
from Source.ConfigFile import ConfigFile
from Source.Utilities import Utilities

class ProcessL1aqc_deglitch:
    '''
    # The Deglitching process departs signicantly from ProSoft and PySciDON
    # Reference: ProSoft 7.7 Rev. K May 8, 2017, SAT-DN-00228
    # More information can be found in AnomalyDetection.py
    '''

    @staticmethod
    def darkDataDeglitching(darkData, windowSize, sigma):
        ''' Dark deglitching is now based on double-pass discrete linear convolution of the residual
        with a stationary std over a rolling average.

        TBD: This is very aggressive in that it eliminates data in all bands if a record in any band fails
            the test. This is why the percentages in the logs appear much higher than the knockouts in any
            given band (as seen in the plots). Could be revisited. '''

        minBand = ConfigFile.minDeglitchBand
        maxBand = ConfigFile.maxDeglitchBand

        darkData.datasetToColumns()
        columns = darkData.columns

        badIndex = [False] * len(darkData.data)
        for key,timeSeries in columns.items():   # Loop over all wavebands
            if float(key) > minBand and float(key) < maxBand:
                # Note: the moving average is not tolerant to 2 or fewer records
                avg = Utilities.movingAverage(timeSeries, windowSize).tolist()
                residual = np.array(timeSeries) - np.array(avg)
                stdData = np.std(residual)

                # First pass
                badIndex1 = Utilities.darkConvolution(timeSeries,avg,stdData,sigma)

                # Second pass
                timeSeries2 = np.array(timeSeries[:])
                timeSeries2[badIndex1] = np.nan # BEWARE: NaNs introduced
                timeSeries2 = timeSeries2.tolist()
                avg2 = Utilities.movingAverage(timeSeries2, windowSize).tolist()
                residual = np.array(timeSeries2) - np.array(avg2)
                stdData = np.nanstd(residual)

                badIndex2 = Utilities.darkConvolution(timeSeries2,avg2,stdData,sigma)

                for i in range(len(badIndex)):
                    if badIndex1[i] is True or badIndex2[i] is True or badIndex[i] is True:
                        badIndex[i] = True
                    else:
                        badIndex[i] = False # this is redundant
        return badIndex

    @staticmethod
    def lightDataDeglitching(lightData, windowSize, sigma):
        ''' Light deglitching is now based on double-pass discrete linear convolution of the residual
        with a ROLLING std over a rolling average'''

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

                for i in range(len(badIndex)):
                    if badIndex1[i] is True or badIndex2[i] is True or badIndex[i] is True:
                        badIndex[i] = True
                    else:
                        badIndex[i] = False # this is redundant

        return badIndex

    @staticmethod
    def processDataDeglitching(node, sensorType):
        msg = sensorType
        print(msg)
        Utilities.writeLogFile(msg)

        step = float(ConfigFile.settings["fL1aqcAnomalyStep"])

        rawFileName = node.attributes['RAW_FILE_NAME']
        L1AfileName = f"{rawFileName.split('.')[0]}_L1A"

        darkData = None
        lightData = None

        for gp in node.groups:
            if 'FrameType' not in gp.attributes:
                continue
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                darkData = gp.getDataset(sensorType)
                darkDateTime = Utilities.getDateTime(gp)
                windowDark = int(ConfigFile.settings[f'fL1aqc{sensorType}WindowDark'])
                sigmaDark = float(ConfigFile.settings[f'fL1aqc{sensorType}SigmaDark'])
                minDark = None if ConfigFile.settings[f'fL1aqc{sensorType}MinDark']=='None' else ConfigFile.settings[f'fL1aqc{sensorType}MinDark']
                maxDark = None if ConfigFile.settings[f'fL1aqc{sensorType}MaxDark']=='None' else ConfigFile.settings[f'fL1aqc{sensorType}MaxDark']
                minMaxBandDark = ConfigFile.settings[f'fL1aqc{sensorType}MinMaxBandDark']
            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
                lightDateTime = Utilities.getDateTime(gp)
                windowLight = int(ConfigFile.settings[f'fL1aqc{sensorType}WindowLight'])
                sigmaLight = float(ConfigFile.settings[f'fL1aqc{sensorType}SigmaLight'])
                minLight = None if ConfigFile.settings[f'fL1aqc{sensorType}MinLight']=='None' else ConfigFile.settings[f'fL1aqc{sensorType}MinLight']
                maxLight = None if ConfigFile.settings[f'fL1aqc{sensorType}MaxLight']=='None' else ConfigFile.settings[f'fL1aqc{sensorType}MaxLight']
                minMaxBandLight = ConfigFile.settings[f'fL1aqc{sensorType}MinMaxBandLight']

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
            # badIndexDark = ProcessL1aqc.darkDataDeglitching(darkData, sensorType, windowDark, sigmaDark)
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
                        Utilities.saveDeglitchPlots(L1AfileName,timeSeries,dateTime,sensorType,lightDark,windowDark,sigmaDark,globBad,globBad2,globBad3)
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
            # NOTE: if you similarly collapse globBads 1-3, you should get the same result as gIndex
            # NOTE: Confirmed that plotted AnomAnal deletions correspond to gIndex

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
                        Utilities.saveDeglitchPlots(L1AfileName,timeSeries,dateTime,sensorType,lightDark,windowLight,sigmaLight,globBad,globBad2,globBad3)
                index +=1

        # Delete the glitchy rows of the datasets
        for gp in node.groups:
            if 'FrameType' not in gp.attributes:
                continue
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                try:
                    gp.datasetDeleteRow(np.where(badIndexDark))
                except Exception:
                    print('Error deleting group datasets. Check that Light/Dark cals are correctly identified in Configuration Window.')

            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
                try:
                    gp.datasetDeleteRow(np.where(badIndexLight))
                except Exception:
                    print('Error deleting group datasets. Check that Light/Dark cals are correctly identified in Configuration Window.')

        return False

    @staticmethod
    def processL1aqc_deglitch(node):
        '''
        Apply data deglitching to light and shutter-dark data, then apply dark shutter correction to light data.
        '''
        root = HDFRoot()
        root.copy(node)
        root.attributes["PROCESSING_LEVEL"] = "1aqc"
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        root.attributes["FILE_CREATION_TIME"] = timestr
        # root.attributes['Deglitcher_Comments'] = ConfigFile.settings['AnomAnalComments']
        if ConfigFile.settings['bL1aqcDeglitch']:
            root.attributes['L1AQC_DEGLITCH'] = 'ON'
            for sensor in ["ES","LI","LT"]:
                # If parameters were picked up from an anoms.csv file, ConfigFile.settings were updated in Controller to reflect
                #    these saved parameters. Now push them into root attributes for posterity.
                root.attributes[f'{sensor}_WINDOW_DARK'] = str(ConfigFile.settings[f'fL1aqc{sensor}WindowDark'])
                root.attributes[f'{sensor}_WINDOW_LIGHT'] = str(ConfigFile.settings[f'fL1aqc{sensor}WindowLight'])
                root.attributes[f'{sensor}_SIGMA_DARK'] = str(ConfigFile.settings[f'fL1aqc{sensor}SigmaDark'])
                root.attributes[f'{sensor}_SIGMA_LIGHT'] = str(ConfigFile.settings[f'fL1aqc{sensor}SigmaLight'])
                if ConfigFile.settings["bL1aqcThreshold"]:
                    root.attributes[f'{sensor}_THRESHOLDS'] = 'TRUE'
                    root.attributes[f'{sensor}_MIN_DARK'] = ConfigFile.settings[f'fL1aqc{sensor}MinDark']
                    root.attributes[f'{sensor}_MAX_DARK'] = ConfigFile.settings[f'fL1aqc{sensor}MaxDark']
                    root.attributes[f'{sensor}_MINMAX_BAND_DARK'] = ConfigFile.settings[f'fL1aqc{sensor}MinMaxBandDark']
                    root.attributes[f'{sensor}_MIN_LIGHT'] = ConfigFile.settings[f'fL1aqc{sensor}MinLight']
                    root.attributes[f'{sensor}_MAX_LIGHT'] = ConfigFile.settings[f'fL1aqc{sensor}MaxLight']
                    root.attributes[f'{sensor}_MINMAX_BAND_LIGHT'] = ConfigFile.settings[f'fL1aqc{sensor}MinMaxBandLight']
                else:
                    root.attributes[f'{sensor}_MIN_DARK'] = 'None'
                    root.attributes[f'{sensor}_MAX_DARK'] = 'None'
                    root.attributes[f'{sensor}_MINMAX_BAND_DARK'] = 'None'
                    root.attributes[f'{sensor}_MIN_LIGHT'] = 'None'
                    root.attributes[f'{sensor}_MAX_LIGHT'] = 'None'
                    root.attributes[f'{sensor}_MINMAX_BAND_LIGHT'] = 'None'
        else:
            root.attributes['L1AQC_DEGLITCH'] = 'OFF'

        msg = f"ProcessL1aqc.processL1aqc: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        # root  = Utilities.rootAddDateTime(root)

        # # Fix in case time doesn't increase from one sample to the next
        # # or there are fewer than 2 two stamps remaining.
        # for gp in root.groups:
        #     if gp.id != "SOLARTRACKER_STATUS":
        #         msg = f'Screening {gp.id} for clean timestamps.'
        #         print(msg)
        #         Utilities.writeLogFile(msg)
        #         if not Utilities.fixDateTime(gp):
        #             msg = f'***********Too few records in {gp.id} to continue after timestamp correction. Exiting.'
        #             print(msg)
        #             Utilities.writeLogFile(msg)
        #             return None

        if int(ConfigFile.settings["bL1aqcDeglitch"]) == 1:
            flagES = ProcessL1aqc_deglitch.processDataDeglitching(root, "ES")
            flagLI = ProcessL1aqc_deglitch.processDataDeglitching(root, "LI")
            flagLT = ProcessL1aqc_deglitch.processDataDeglitching(root, "LT")

            if flagES or flagLI or flagLT:
                msg = '***********Too few records in the file after deglitching to continue. Exiting.'
                print(msg)
                Utilities.writeLogFile(msg)
                return None

        return root
