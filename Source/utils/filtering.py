'''################################# FILTERING & DEGLITCHING ORIENTED #################################'''

import numpy as np
import pandas as pd

from Source.ConfigFile import ConfigFile
import Source.utils.averaging as averaging
import Source.utils.loggingHCP as logging

def darkConvolution(data,avg,std,sigma):
    ''' Used in anomaly analysis in L1AQC for discrete linear convolution of the residual
    with a stationary std over a rolling average.'''
    badIndex = []
    for i, dat in enumerate(data):
        if i < 1 or i > len(data)-2:
            # First and last avg values from convolution are not to be trusted
            badIndex.append(True)
        elif np.isnan(dat):
            badIndex.append(False)
        else:
            # Use stationary standard deviation anomaly (from rolling average) detection for dark data
            if (dat > avg[i] + (sigma*std)) or (dat < avg[i] - (sigma*std)):
                badIndex.append(True)
            else:
                badIndex.append(False)
    return badIndex


def lightConvolution(data,avg,rolling_std,sigma):
    '''Used in anomaly analysis in L1AQC for discrete linear convolution of the residual
    with a ROLLING std over a rolling average'''
    badIndex = []
    for i, dat in enumerate(data):
        if i < 1 or i > len(data)-2:
            # First and last avg values from convolution are not to be trusted
            badIndex.append(True)
        elif np.isnan(dat):
            badIndex.append(False)
        else:
            # Use rolling standard deviation anomaly (from rolling average) detection for dark data
            if (dat > avg[i] + (sigma*rolling_std[i])) or (dat < avg[i] - (sigma*rolling_std[i])):
                badIndex.append(True)
            else:
                badIndex.append(False)
    return badIndex


def deglitchThresholds(band,data,minRad,maxRad,minMaxBand):

    badIndex = []
    for dat in data:
        badIndex.append(False)
        # ConfigFile setting updated directly from the checkbox in AnomDetection.
        # This insures values of badIndex are false if unthresholded or Min or Max are None
        if ConfigFile.settings["bL1aqcThreshold"]:
            # Only run on the pre-selected waveband
            if band == minMaxBand:
                if minRad or minRad==0: # beware falsy zeros...
                    if dat < minRad:
                        badIndex[-1] = True

                if maxRad or maxRad==0:
                    if dat > maxRad:
                        badIndex[-1] = True
    return badIndex


def deglitchBand(band, radiometry1D, windowSize, sigma, lightDark, minRad, maxRad, minMaxBand):
    ''' For a given sensor in a given band (1D), calculate the first and second outliers on the
            light and dark based on moving average filters. Then apply thresholds.

            This may benefit in the future from eliminating the thresholded values from the moving
            average filter analysis.
    '''
    if lightDark == 'Dark':
        # For Darks, calculate the moving average and residual vectors
        #   and the OVERALL standard deviation of the residual over the entire file

        # First pass
        avg = averaging.movingAverage(radiometry1D, windowSize).tolist()
        residual = np.array(radiometry1D) - np.array(avg)
        stdData = np.std(residual)

        badIndex = darkConvolution(radiometry1D,avg,stdData,sigma)

        # Second pass
        radiometry1D2 = np.array(radiometry1D[:])
        radiometry1D2[badIndex] = np.nan
        radiometry1D2 = radiometry1D2.tolist()
        avg2 = averaging.movingAverage(radiometry1D2, windowSize).tolist()
        residual = np.array(radiometry1D2) - np.array(avg2)
        stdData = np.nanstd(residual)

        badIndex2 = darkConvolution(radiometry1D2,avg2,stdData,sigma)

        # Threshold pass
        # Tolerates "None" for min or max Rad. ConfigFile.setting updated directly from checkbox
        badIndex3 = deglitchThresholds(band,radiometry1D,minRad,maxRad, minMaxBand)

    else:
        # For Lights, calculate the moving average and residual vectors
        #   and the ROLLING standard deviation of the residual

        # First pass
        avg = averaging.movingAverage(radiometry1D, windowSize).tolist()
        residual = np.array(radiometry1D) - np.array(avg)

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

        badIndex = lightConvolution(radiometry1D,avg,rolling_std,sigma)

        # Second pass
        radiometry1D2 = np.array(radiometry1D[:])
        radiometry1D2[badIndex] = np.nan
        radiometry1D2 = radiometry1D2.tolist()
        avg2 = averaging.movingAverage(radiometry1D2, windowSize).tolist()
        residual2 = np.array(radiometry1D2) - np.array(avg2)
        residualDf2 = pd.DataFrame(residual2)
        testing_std_as_df2 = residualDf2.rolling(windowSize).std()
        rolling_std2 = testing_std_as_df2.replace(np.nan,
            testing_std_as_df2.iloc[windowSize - 1]).round(3).iloc[:,0].tolist()
        y = np.array(rolling_std2)
        y[np.isnan(y)] = np.nanmedian(y)
        y[y > np.nanmedian(y)+3*np.nanstd(y)] = np.nanmedian(y)
        rolling_std2 = y.tolist()

        badIndex2 = lightConvolution(radiometry1D2,avg2,rolling_std2,sigma)

        # Threshold pass
        # Tolerates "None" for min or max Rad
        badIndex3 = deglitchThresholds(band, radiometry1D,minRad,maxRad, minMaxBand)

    return badIndex, badIndex2, badIndex3


def filterData(group, badTimes, level = None):
    ''' Called only by ProcessL1bqc. filterData for L1AQC is contained within ProcessL1aqc.py
        and for L2 within ProcessL2.py.
        Delete L1BQC flagged records. 
        Level is only used to flag L1AQC carry-over groups to work around timestamps and
        embedded CALs and BACKs with TriOS.
        All data in the group (including satellite sensors) will be deleted.
        '''
    # NOTE: This is still very slow on long files with many badTimes, despite badTimes being filtered for
    #   unique pairs.

    logging.writeLogFileAndPrint(f'Remove {group.id} Data')

    # Trigger for reset of CAL & BACK
    do_reset = False

    timeStamp = None
    raw_cal, raw_back, raw_back_att, raw_cal_att = None,None,None,None,
    if level != 'L1AQC':
        if group.id == "ANCILLARY":
            timeStamp = group.getDataset("LATITUDE").data["Datetime"]
        if group.id == "IRRADIANCE":
            timeStamp = group.getDataset("ES").data["Datetime"]
        if group.id == "RADIANCE":
            timeStamp = group.getDataset("LI").data["Datetime"]
        if group.id == "SIXS_MODEL":
            timeStamp = group.getDataset("solar_zenith").data["Datetime"]
    else:
        timeStamp = group.getDataset("Timestamp").data["Datetime"]
        # TRIOS: copy CAL & BACK before filetering, and delete them
        # to avoid conflict when filtering more row than 255
        if ConfigFile.settings['SensorType'].lower() in ["sorad", "trios", "trios es only"]:
            do_reset = True
            raw_cal  = group.getDataset("CAL_"+group.id[0:2]).data
            raw_back = group.getDataset("BACK_"+group.id[0:2]).data
            raw_cal_att  = group.getDataset("CAL_"+group.id[0:2]).attributes
            raw_back_att = group.getDataset("BACK_"+group.id[0:2]).attributes
            del group.datasets['CAL_'+group.id[0:2]]
            del group.datasets['BACK_'+group.id[0:2]]

    startLength = len(timeStamp)
    logging.writeLogFileAndPrint(f'   Length of dataset prior to removal {startLength} long')

    # Delete the records in badTime ranges from each dataset in the group
    finalCount = 0
    originalLength = len(timeStamp)
    for dateTime in badTimes:
        # logging.writeLogFileAndPrint(f'Eliminate data between: {dateTime}'
        # Need to reinitialize for each loop
        startLength = len(timeStamp)
        newTimeStamp = []
        start = dateTime[0]
        stop = dateTime[1]

        if startLength > 0:
            rowsToDelete = []
            for i in range(startLength):
                if start <= timeStamp[i] and stop >= timeStamp[i]:
                    try:
                        rowsToDelete.append(i)
                        finalCount += 1
                    except Exception:
                        print('error')
                else:
                    newTimeStamp.append(timeStamp[i])
            group.datasetDeleteRow(rowsToDelete)
        else:
            logging.writeLogFileAndPrint('Data group is empty. Continuing.')
            break
        timeStamp = newTimeStamp.copy()

    if ConfigFile.settings['SensorType'].lower()  in ["sorad", "trios", "trios es only"]:
        # TRIOS: reset CAL and BACK as before filtering
        if do_reset:
            group.addDataset("CAL_"+group.id[0:2])
            group.datasets["CAL_"+group.id[0:2]].data = raw_cal
            group.datasets["CAL_"+group.id[0:2]].attributes = raw_cal_att
            group.addDataset("BACK_"+group.id[0:2])
            group.datasets["BACK_"+group.id[0:2]].data = raw_back
            group.datasets["BACK_"+group.id[0:2]].attributes = raw_back_att

        for ds in group.datasets:
            group.datasets[ds].datasetToColumns()
    else:
        for ds in group.datasets:
            group.datasets[ds].datasetToColumns()

    logging.writeLogFileAndPrint(\
        f'   Length of dataset after removal {originalLength-finalCount} long: {(100*finalCount/originalLength):.1f}% removed')
    return finalCount/originalLength
