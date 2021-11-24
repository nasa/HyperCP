
import os
import sys
import math
import datetime
import time
import pytz
from collections import Counter
import csv

# from PyQt5.QtWidgets import QApplication, QDesktopWidget, QWidget, QPushButton, QMessageBox
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
import scipy.interpolate
from scipy.interpolate import splev, splrep
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from tqdm import tqdm

from ConfigFile import ConfigFile
from MainConfig import MainConfig

# This gets reset later in Controller.processSingleLevel to reflect the file being processed.
if "LOGFILE" not in os.environ:
    os.environ["LOGFILE"] = "temp.log"

class Utilities:


    @staticmethod
    def mostFrequent(List):
        occurence_count = Counter(List)
        return occurence_count.most_common(1)[0][0]

    @staticmethod
    def find_nearest(array,value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx

        # ''' ONLY FOR SORTED ARRAYS'''
        # idx = np.searchsorted(array, value, side="left")
        # if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
        #     return array[idx-1]
        # else:
        #     return array[idx]

    @staticmethod
    def errorWindow(winText,errorText):
        msgBox = QMessageBox()
        # msgBox.setIcon(QMessageBox.Information)
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText(errorText)
        msgBox.setWindowTitle(winText)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    @staticmethod
    def waitWindow(winText,waitText):
        msgBox = QMessageBox()
        # msgBox.setIcon(QMessageBox.Information)
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText(waitText)
        msgBox.setWindowTitle(winText)
        # msgBox.setStandardButtons(QMessageBox.Ok)
        # msgBox.exec_()
        return msgBox

    @staticmethod
    def YNWindow(winText,infoText):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(infoText)
        msgBox.setWindowTitle(winText)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = msgBox.exec_()
        return returnValue

    @staticmethod
    def writeLogFile(logText, mode='a'):
        with open('Logs/' + os.environ["LOGFILE"], mode) as logFile:
            logFile.write(logText + "\n")

    # Converts degrees minutes to decimal degrees format
    @staticmethod # for some reason, these were not set to static method, but didn't refer to self
    def dmToDd(dm, direction):
        d = int(dm/100)
        m = dm-d*100
        dd = d + m/60
        if direction == b'W' or direction == b'S':
            dd *= -1
        return dd

    # Converts decimal degrees to degrees minutes format
    @staticmethod
    def ddToDm(dd):
        d = int(dd)
        m = abs(dd - d)*60
        dm = (d*100) + m
        return dm


    # Converts GPS UTC time (HHMMSS.ds; i.e. 99 ds after midnight is 000000.99)to seconds
    # Note: Does not support multiple days
    @staticmethod
    def utcToSec(utc):
        # Use zfill to ensure correct width, fixes bug when hour is 0 (12 am)
        t = str(int(utc)).zfill(6)
        # print(t)
        #print(t[:2], t[2:4], t[4:])
        h = int(t[:2])
        m = int(t[2:4])
        s = float(t[4:])
        return ((h*60)+m)*60+s

    # Converts datetime date and UTC (HHMMSS.ds) to datetime (uses microseconds)
    @staticmethod
    def utcToDateTime(dt, utc):
        # Use zfill to ensure correct width, fixes bug when hour is 0 (12 am)
        num, dec = str(float(utc)).split('.')
        t = num.zfill(6)
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:6])
        us = 10000*int(dec) # i.e. 0.55 s = 550,000 us
        return datetime.datetime(dt.year,dt.month,dt.day,h,m,s,us,tzinfo=datetime.timezone.utc)

    # Converts datetag (YYYYDDD) to date string
    @staticmethod
    def dateTagToDate(dateTag):
        dt = datetime.datetime.strptime(str(int(dateTag)), '%Y%j')
        timezone = pytz.utc
        dt = timezone.localize(dt)
        return dt.strftime('%Y%m%d')

    # Converts datetag (YYYYDDD) to datetime
    @staticmethod
    def dateTagToDateTime(dateTag):
        dt = datetime.datetime.strptime(str(int(dateTag)), '%Y%j')
        timezone = pytz.utc
        dt = timezone.localize(dt)
        return dt

    # Converts seconds of the day (NOT GPS UTCPOS) to GPS UTC (HHMMSS.SS)
    @staticmethod
    def secToUtc(sec):
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return float("%d%02d%02d" % (h, m, s))

    # Converts seconds of the day to TimeTag2 (HHMMSSmmm; i.e. 0.999 sec after midnight = 000000999)
    @staticmethod
    def secToTimeTag2(sec):
        #return float(time.strftime("%H%M%S", time.gmtime(sec)))
        t = sec * 1000
        s, ms = divmod(t, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return int("%d%02d%02d%03d" % (h, m, s, ms))

    # Converts TimeTag2 (HHMMSSmmm) to seconds
    @staticmethod
    def timeTag2ToSec(tt2):
        t = str(int(tt2)).zfill(9)
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:6])
        ms = int(t[6:])
        # print(h, m, s, ms)
        return ((h*60)+m)*60+s+(float(ms)/1000.0)

    # Converts datetime.date and TimeTag2 (HHMMSSmmm) to datetime
    @staticmethod
    def timeTag2ToDateTime(dt,tt2):
        t = str(int(tt2)).zfill(9)
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:6])
        us = 1000*int(t[6:])
        # print(h, m, s, us)
        # print(tt2)
        return datetime.datetime(dt.year,dt.month,dt.day,h,m,s,us,tzinfo=datetime.timezone.utc)

    # Converts datetime to Timetag2 (HHMMSSmmm)
    @staticmethod
    def datetime2TimeTag2(dt):
        h = dt.hour
        m = dt.minute
        s = dt.second
        ms = dt.microsecond/1000
        return int("%d%02d%02d%03d" % (h, m, s, ms))

    # Converts datetime to Datetag
    @staticmethod
    def datetime2DateTag(dt):
        y = dt.year
        # mon = dt.month
        day = dt.timetuple().tm_yday

        return int("%d%03d" % (y, day))

    # Converts HDFRoot timestamp attribute to seconds
    @staticmethod
    def timestampToSec(timestamp):
        timei = timestamp.split(" ")[3]
        t = timei.split(":")
        h = int(t[0])
        m = int(t[1])
        s = int(t[2])
        return ((h*60)+m)*60+s

    # Convert GPRMC Date to Datetag
    @staticmethod
    def gpsDateToDatetime(year, gpsDate):
        date = str(gpsDate).zfill(6)
        day = int(date[:2])
        mon = int(date[2:4])
        return datetime.datetime(year,mon,day,0,0,0,0,tzinfo=datetime.timezone.utc)


    # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
    # Also screens for nonsense timetags like 0.0 or NaN, and datetags that are not
    # in the 20th or 21st centuries
    @staticmethod
    def rootAddDateTime(node):
        for gp in node.groups:
            # print(gp.id)
            if gp.id != "SOLARTRACKER_STATUS": # No valid timestamps in STATUS
                timeData = gp.getDataset("TIMETAG2").data["NONE"].tolist()
                dateTag = gp.getDataset("DATETAG").data["NONE"].tolist()
                timeStamp = []
                for i, timei in enumerate(timeData):
                    # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
                    # Filter for aberrant Datetags
                    t = str(int(timei)).zfill(9)
                    h = int(t[:2])
                    m = int(t[2:4])
                    s = int(t[4:6])
                    if (str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20")) \
                        and timei != 0.0 and not np.isnan(timei) \
                            and h < 60 and m < 60 and s < 60:

                        dt = Utilities.dateTagToDateTime(dateTag[i])
                        timeStamp.append(Utilities.timeTag2ToDateTime(dt, timei))
                    else:
                        msg = f"Bad Datetag or Timetag2 found. Eliminating record. {i} : {dateTag[i]} : {timei}"
                        print(msg)
                        Utilities.writeLogFile(msg)
                        gp.datasetDeleteRow(i)
                dateTime = gp.addDataset("DATETIME")
                dateTime.data = timeStamp
        return node

    # Add a data column to each group dataset for DATETIME, as defined by TIMETAG2 and DATETAG
    # Also screens for nonsense timetags like 0.0 or NaN, and datetags that are not
    # in the 20th or 21st centuries
    @staticmethod
    def rootAddDateTimeL2(node):
        for gp in node.groups:
            if gp.id != "SOLARTRACKER_STATUS": # No valid timestamps in STATUS
                for ds in gp.datasets:
                    # Make sure all datasets have been transcribed to columns
                    gp.datasets[ds].datasetToColumns()

                    if not 'Datetime' in gp.datasets[ds].columns:
                        timeData = gp.datasets[ds].columns["Timetag2"]
                        dateTag = gp.datasets[ds].columns["Datetag"]

                        timeStamp = []
                        for i, timei in enumerate(timeData):
                            # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
                            # Filter for aberrant Datetags
                            if (str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20")) \
                                and timei != 0.0 and not np.isnan(timei):

                                dt = Utilities.dateTagToDateTime(dateTag[i])
                                timeStamp.append(Utilities.timeTag2ToDateTime(dt, timei))
                            else:
                                gp.datasetDeleteRow(i)
                                msg = f"Bad Datetag or Timetag2 found. Eliminating record. {dateTag[i]} : {timei}"
                                print(msg)
                                Utilities.writeLogFile(msg)
                        gp.datasets[ds].columns["Datetime"] = timeStamp
                        gp.datasets[ds].columns.move_to_end('Datetime', last=False)
                        gp.datasets[ds].columnsToDataset()

        return node

    # Remove records if values of DATETIME are not strictly increasing
    # (strictly increasing values required for interpolation)
    @staticmethod
    def fixDateTime(gp):
        dateTime = gp.getDataset("DATETIME").data

        # Test for strictly ascending values
        # Not sensitive to UTC midnight (i.e. in datetime format)
        total = len(dateTime)
        globalTotal = total
        if total >= 2:
            # Check the first element prior to looping over rest
            i = 0
            if dateTime[i+1] <= dateTime[i]:
                    gp.datasetDeleteRow(i)
                    del dateTime[i] # I'm fuzzy on why this is necessary; not a pointer?
                    total = total - 1
                    msg = f'Out of order timestamp deleted at {i}'
                    print(msg)
                    Utilities.writeLogFile(msg)

                    #In case we went from 2 to 1 element on the first element,
                    if total == 1:
                        msg = f'************Too few records ({total}) to test for ascending timestamps. Exiting.'
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return False

            i = 1
            while i < total:

                if dateTime[i] <= dateTime[i-1]:

                    ''' BUG?:Same values of consecutive TT2s are shockingly common. Confirmed
                    that 1) they exist from L1A, and 2) sensor data changes while TT2 stays the same '''

                    gp.datasetDeleteRow(i)
                    del dateTime[i] # I'm fuzzy on why this is necessary; not a pointer?
                    total = total - 1
                    msg = f'Out of order TIMETAG2 row deleted at {i}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    continue # goto while test skipping i incrementation. dateTime[i] is now the next value.
                i += 1
        else:
            msg = f'************Too few records ({total}) to test for ascending timestamps. Exiting.'
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        if (globalTotal - total) > 0:
            msg = f'Data eliminated for non-increasing timestamps: {100*(globalTotal - total)/globalTotal:3.1f}%'
            print(msg)
            Utilities.writeLogFile(msg)

        return True

    # @staticmethod
    # def epochSecToDateTagTimeTag2(eSec):
    #     dateTime = datetime.datetime.utcfromtimestamp(eSec)
    #     year = dateTime.timetuple()[0]
    #     return

    # Checks if a string is a floating point number
    @staticmethod
    def isFloat(text):
        try:
            float(text)
            return True
        except ValueError:
            return False

    # Check if dataset contains NANs
    @staticmethod
    def hasNan(ds):
        for k in ds.data.dtype.fields.keys():
            for x in range(ds.data.shape[0]):
                if k != 'Datetime':
                    if np.isnan(ds.data[k][x]):
                        return True
                # else:
                #     if np.isnan(ds.data[k][x]):
                #         return True
        return False

    # Check if the list contains strictly increasing values
    @staticmethod
    def isIncreasing(l):
        return all(x<y for x, y in zip(l, l[1:]))

    @staticmethod
    def windowAverage(data,window_size):
        min_periods = round(window_size/2)
        df=pd.DataFrame(data)
        out=df.rolling(window_size,min_periods,center=True,win_type='boxcar')
        # out = [item for items in out for item in items] #flattening doesn't work
        return out

    @staticmethod
    def movingAverage(data, window_size):
        # Window size will be determined experimentally by examining the dark and light data from each instrument.
        """ Noise detection using a low-pass filter.
        https://www.datascience.com/blog/python-anomaly-detection
        Computes moving average using discrete linear convolution of two one dimensional sequences.
        Args:
        -----
                data (pandas.Series): independent variable
                window_size (int): rolling window size
        Returns:
        --------
                ndarray of linear convolution
        References:
        ------------
        [1] Wikipedia, "Convolution", http://en.wikipedia.org/wiki/Convolution.
        [2] API Reference: https://docs.scipy.org/doc/numpy/reference/generated/numpy.convolve.html
        [3] ABE, N., Zadrozny, B., and Langford, J. 2006. Outlier detection by active learning.
            In Proceedings of the 12th ACM SIGKDD International Conference on Knowledge Discovery and
            Data Mining. ACM Press, New York, 504–509
        [4] V Chandola, A Banerjee and V Kumar 2009. Anomaly Detection: A Survey Article No. 15 in ACM
            Computing Surveys"""

        # window = np.ones(int(window_size))/float(window_size)
        # Convolve is not nan-tolerant, so use a mask
        data = np.array(data)
        mask = np.isnan(data)
        K = np.ones(window_size, dtype=int)
        denom = np.convolve(~mask,K)
        denom = np.where(denom != 0, denom, 1) # replace the 0s with 1s to block div0 error; the numerator will be zero anyway

        out = np.convolve(np.where(mask,0,data), K)/denom
        # return np.convolve(data, window, 'same')

        # Slice out one half window on either side; this requires an odd-sized window
        return out[int(np.floor(window_size/2)):-int(np.floor(window_size/2))]


    @staticmethod
    def darkConvolution(data,avg,std,sigma):
        badIndex = []
        for i in range(len(data)):
            if i < 1 or i > len(data)-2:
                # First and last avg values from convolution are not to be trusted
                badIndex.append(True)
            elif np.isnan(data[i]):
                badIndex.append(False)
            else:
                # Use stationary standard deviation anomaly (from rolling average) detection for dark data
                if (data[i] > avg[i] + (sigma*std)) or (data[i] < avg[i] - (sigma*std)):
                    badIndex.append(True)
                else:
                    badIndex.append(False)
        return badIndex

    @staticmethod
    def lightConvolution(data,avg,rolling_std,sigma):
        badIndex = []
        for i in range(len(data)):
            if i < 1 or i > len(data)-2:
                # First and last avg values from convolution are not to be trusted
                badIndex.append(True)
            elif np.isnan(data[i]):
                badIndex.append(False)
            else:
                # Use rolling standard deviation anomaly (from rolling average) detection for dark data
                if (data[i] > avg[i] + (sigma*rolling_std[i])) or (data[i] < avg[i] - (sigma*rolling_std[i])):
                    badIndex.append(True)
                else:
                    badIndex.append(False)
        return badIndex

    @staticmethod
    def l1dThresholds(band,data,minRad,maxRad,minMaxBand):

        badIndex = []
        for i in range(len(data)):
            badIndex.append(False)
            # ConfigFile setting updated directly from the checkbox in AnomDetection.
            # This insures values of badIndex are false if unthresholded or Min or Max are None
            if ConfigFile.settings["bL1dThreshold"]:
                # Only run on the pre-selected waveband
                if band == minMaxBand:
                    if minRad or minRad==0: # beware falsy zeros...
                        if data[i] < minRad:
                            badIndex[-1] = True

                    if maxRad or maxRad==0:
                        if data[i] > maxRad:
                            badIndex[-1] = True
        return badIndex

    # @staticmethod
    # def rejectOutliers(data, m):
    #     d = np.abs(data - np.nanmedian(data))
    #     mdev = np.nanmedian(d)
    #     s = d/mdev if mdev else 0.
    #     badIndex = np.zeros((len(s),1),dtype=bool)
    #     badIndex = [s>=m]
    #     return badIndex


    @staticmethod
    def interp(x, y, new_x, kind='linear', fill_value=0.0):
        ''' Wrapper for scipy interp1d that works even if
            values in new_x are outside the range of values in x'''

        ''' NOTE: This will fill missing values at the beginning and end of data record with
            the nearest actual record. This is fine for integrated datasets, but may be dramatic
            for some gappy ancillary records of lower temporal resolution.'''
        # If the last value to interp to is larger than the last value interp'ed from,
        # then append that higher value onto the values to interp from
        n0 = len(x)-1
        n1 = len(new_x)-1
        if new_x[n1] > x[n0]:
            #print(new_x[n], x[n])
            # msg = '********** Warning: extrapolating to beyond end of data record ********'
            # print(msg)
            # Utilities.writeLogFile(msg)

            x.append(new_x[n1])
            y.append(y[n0])
        # If the first value to interp to is less than the first value interp'd from,
        # then add that lesser value to the beginning of values to interp from
        if new_x[0] < x[0]:
            #print(new_x[0], x[0])
            # msg = '********** Warning: extrapolating to before beginning of data record ******'
            # print(msg)
            # Utilities.writeLogFile(msg)

            x.insert(0, new_x[0])
            y.insert(0, y[0])

        new_y = scipy.interpolate.interp1d(x, y, kind=kind, bounds_error=False, fill_value=fill_value)(new_x)

        return new_y

    @staticmethod
    def interpAngular(x, y, new_x, fill_value="extrapolate"):
        ''' Wrapper for scipy interp1d that works even if
            values in new_x are outside the range of values in x'''

        ''' NOTE: Except for SOLAR_AZ and SZA, which are extrapolated, this will fill missing values at the
            beginning and end of data record with the nearest actual record. This is fine for integrated
            datasets, but may be dramatic for some gappy ancillary records of lower temporal resolution.'''

        if fill_value != "extrapolate": # Only extrapolate SOLAR_AZ and SZA, otherwise keep fill values constant
            # Some angular measurements (like SAS pointing) are + and -. Convert to all +
            # eliminate NaNs
            for i, value in enumerate(y):
                if value < 0:
                    y[i] = 360 + value
                if np.isnan(value):
                    x.pop(i)
                    y.pop(i)

            # If the last value to interp to is larger than the last value interp'ed from,
            # then append that higher value onto the values to interp from
            n0 = len(x)-1
            n1 = len(new_x)-1
            if new_x[n1] > x[n0]:
                #print(new_x[n], x[n])
                # msg = '********** Warning: extrapolating to beyond end of data record ********'
                # print(msg)
                # Utilities.writeLogFile(msg)

                x.append(new_x[n1])
                y.append(y[n0])
            # If the first value to interp to is less than the first value interp'd from,
            # then add that lesser value to the beginning of values to interp from
            if new_x[0] < x[0]:
                #print(new_x[0], x[0])
                # msg = '********** Warning: extrapolating to before beginning of data record ******'
                # print(msg)
                # Utilities.writeLogFile(msg)

                x.insert(0, new_x[0])
                y.insert(0, y[0])

        y_rad = np.deg2rad(y)
        # f = scipy.interpolate.interp1d(x,y_rad,kind='linear', bounds_error=False, fill_value=None)
        f = scipy.interpolate.interp1d(x,y_rad,kind='linear', bounds_error=False, fill_value=fill_value)
        new_y_rad = f(new_x)%(2*np.pi)
        new_y = np.rad2deg(new_y_rad)

        return new_y

    # Cubic spline interpolation intended to get around the all NaN output from InterpolateUnivariateSpline
    # x is original time to be splined, y is the data to be interpolated, new_x is the time to interpolate/spline to
    # interpolate.splrep is intolerant of duplicate or non-ascending inputs, and inputs with fewer than 3 points
    @staticmethod
    def interpSpline(x, y, new_x):
        spl = splrep(x, y)
        new_y = splev(new_x, spl)

        for i in range(len(new_y)):
            if np.isnan(new_y[i]):
                print("NaN")

        return new_y

    @staticmethod
    def plotRadiometry(root, filename, rType, plotDelta = False):

        dirPath = os.getcwd()
        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L2')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        dataDelta = None
        ''' Note: If only one spectrum is left in a given ensemble, deltas will
        be zero for Es, Li, and Lt.'''

        if rType=='Rrs':
            print('Plotting Rrs')
            group = root.getGroup("REFLECTANCE")
            Data = group.getDataset(f'{rType}_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_unc')
            plotRange = [340, 800]
            if ConfigFile.settings['bL2WeightMODISA']:
                Data_MODISA = group.getDataset(f'{rType}_MODISA')
                if plotDelta:
                    dataDelta_MODISA = group.getDataset(f'{rType}_MODISA_unc')
            if ConfigFile.settings['bL2WeightMODIST']:
                Data_MODIST = group.getDataset(f'{rType}_MODIST')
                if plotDelta:
                    dataDelta_MODIST = group.getDataset(f'{rType}_MODIST_unc')
            if ConfigFile.settings['bL2WeightVIIRSN']:
                Data_VIIRSN = group.getDataset(f'{rType}_VIIRSN')
                if plotDelta:
                    dataDelta_VIIRSN = group.getDataset(f'{rType}_VIIRSN_unc')
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                Data_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ')
                if plotDelta:
                    dataDelta_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ_unc')
            if ConfigFile.settings['bL2WeightSentinel3A']:
                Data_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A')
                if plotDelta:
                    dataDelta_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A_unc')
            if ConfigFile.settings['bL2WeightSentinel3B']:
                Data_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B')
                if plotDelta:
                    dataDelta_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B_unc')

        if rType=='nLw':
            print('Plotting nLw')
            group = root.getGroup("REFLECTANCE")
            Data = group.getDataset(f'{rType}_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_unc')
            plotRange = [340, 800]
            if ConfigFile.settings['bL2WeightMODISA']:
                Data_MODISA = group.getDataset(f'{rType}_MODISA')
                if plotDelta:
                    dataDelta_MODISA = group.getDataset(f'{rType}_MODISA_unc')
            if ConfigFile.settings['bL2WeightMODIST']:
                Data_MODIST = group.getDataset(f'{rType}_MODIST')
                if plotDelta:
                    dataDelta_MODIST = group.getDataset(f'{rType}_MODIST_unc')
            if ConfigFile.settings['bL2WeightVIIRSN']:
                Data_VIIRSN = group.getDataset(f'{rType}_VIIRSN')
                if plotDelta:
                    dataDelta_VIIRSN = group.getDataset(f'{rType}_VIIRSN_unc')
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                Data_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ')
                if plotDelta:
                    dataDelta_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ_unc')
            if ConfigFile.settings['bL2WeightSentinel3A']:
                Data_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A')
                if plotDelta:
                    dataDelta_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A_unc')
            if ConfigFile.settings['bL2WeightSentinel3B']:
                Data_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B')
                if plotDelta:
                    dataDelta_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B_unc')

        ''' Could include satellite convolved (ir)radiances in the future '''
        if rType=='ES':
            print('Plotting Es')
            group = root.getGroup("IRRADIANCE")
            Data = group.getDataset(f'{rType}_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_sd')
            plotRange = [305, 1140]

        if rType=='LI':
            print('Plotting Li')
            group = root.getGroup("RADIANCE")
            Data = group.getDataset(f'{rType}_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_sd')
            plotRange = [305, 1140]

        if rType=='LT':
            print('Plotting Lt')
            group = root.getGroup("RADIANCE")
            Data = group.getDataset(f'{rType}_HYPER')
            lwData = group.getDataset(f'LW_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_sd')
                # lwDataDelta = group.getDataset(f'LW_HYPER_sd')
            plotRange = [305, 1140]

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }

        # Hyperspectral
        x = []
        xLw = []
        wave = []
        subwave = [] # accomodates Zhang, which deletes out-of-bounds wavebands
        # For each waveband
        for k in Data.data.dtype.names:
            if Utilities.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    x.append(k)
                    wave.append(float(k))
        # Add Lw to Lt plots
        if rType=='LT':
            for k in lwData.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        xLw.append(k)
                        subwave.append(float(k))

        # Satellite Bands
        x_MODISA = []
        wave_MODISA = []
        if ConfigFile.settings['bL2WeightMODISA'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_MODISA.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_MODISA.append(k)
                        wave_MODISA.append(float(k))
        x_MODIST = []
        wave_MODIST = []
        if ConfigFile.settings['bL2WeightMODIST'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_MODIST.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_MODIST.append(k)
                        wave_MODIST.append(float(k))
        x_VIIRSN = []
        wave_VIIRSN = []
        if ConfigFile.settings['bL2WeightVIIRSN'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_VIIRSN.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_VIIRSN.append(k)
                        wave_VIIRSN.append(float(k))
        x_VIIRSJ = []
        wave_VIIRSJ = []
        if ConfigFile.settings['bL2WeightVIIRSJ'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_VIIRSJ.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_VIIRSJ.append(k)
                        wave_VIIRSJ.append(float(k))
        x_Sentinel3A = []
        wave_Sentinel3A = []
        if ConfigFile.settings['bL2WeightSentinel3A'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_Sentinel3A.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_Sentinel3A.append(k)
                        wave_Sentinel3A.append(float(k))
        x_Sentinel3B = []
        wave_Sentinel3B = []
        if ConfigFile.settings['bL2WeightSentinel3B'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_Sentinel3B.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_Sentinel3B.append(k)
                        wave_Sentinel3B.append(float(k))


        total = Data.data.shape[0]
        maxRad = 0
        minRad = 0
        cmap = cm.get_cmap("jet")
        color=iter(cmap(np.linspace(0,1,total)))

        plt.figure(1, figsize=(8,6))
        for i in range(total):
            # Hyperspectral
            y = []
            dy = []
            for k in x:
                y.append(Data.data[k][i])
                if plotDelta:
                    dy.append(dataDelta.data[k][i])
            # Add Lw to Lt plots
            if rType=='LT':
                yLw = []
                # dyLw = []
                for k in xLw:
                    yLw.append(lwData.data[k][i])
                    # if plotDelta:
                    #     dy.append(dataDelta.data[k][i])


            # Satellite Bands
            y_MODISA = []
            dy_MODISA = []
            if ConfigFile.settings['bL2WeightMODISA']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_MODISA:
                    y_MODISA.append(Data_MODISA.data[k][i])
                    if plotDelta:
                        dy_MODISA.append(dataDelta_MODISA.data[k][i])
            y_MODIST = []
            dy_MODIST = []
            if ConfigFile.settings['bL2WeightMODIST']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_MODIST:
                    y_MODIST.append(Data_MODIST.data[k][i])
                    if plotDelta:
                        dy_MODIST.append(dataDelta_MODIST.data[k][i])
            y_VIIRSN = []
            dy_VIIRSN = []
            if ConfigFile.settings['bL2WeightVIIRSN']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_VIIRSN:
                    y_VIIRSN.append(Data_VIIRSN.data[k][i])
                    if plotDelta:
                        dy_VIIRSN.append(dataDelta_VIIRSN.data[k][i])
            y_VIIRSJ = []
            dy_VIIRSJ = []
            if ConfigFile.settings['bL2WeightVIIRSJ']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_VIIRSJ:
                    y_VIIRSJ.append(Data_VIIRSJ.data[k][i])
                    if plotDelta:
                        dy_VIIRSJ.append(dataDelta_VIIRSJ.data[k][i])
            y_Sentinel3A = []
            dy_Sentinel3A = []
            if ConfigFile.settings['bL2WeightSentinel3A']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_Sentinel3A:
                    y_Sentinel3A.append(Data_Sentinel3A.data[k][i])
                    if plotDelta:
                        dy_Sentinel3A.append(dataDelta_Sentinel3A.data[k][i])
            y_Sentinel3B = []
            dy_Sentinel3B = []
            if ConfigFile.settings['bL2WeightSentinel3B']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_Sentinel3B:
                    y_Sentinel3B.append(Data_Sentinel3B.data[k][i])
                    if plotDelta:
                        dy_Sentinel3B.append(dataDelta_Sentinel3B.data[k][i])

            c=next(color)
            if max(y) > maxRad:
                maxRad = max(y)+0.1*max(y)
            if rType == 'LI' and maxRad > 20:
                maxRad = 20
            if rType == 'LT' and maxRad > 2:
                maxRad = 2
            if min(y) < minRad:
                minRad = min(y)-0.1*min(y)
            if rType == 'LI':
                minRad = 0
            if rType == 'LT':
                minRad = 0
            if rType == 'ES':
                minRad = 0

            # Plot the Hyperspectral spectrum
            plt.plot(wave, y, c=c, zorder=-1)

            # Add the Wei QA score to the Rrs plot, if calculated
            if rType == 'Rrs':
                if ConfigFile.products['bL2ProdweiQA']:
                    groupProd = root.getGroup("DERIVED_PRODUCTS")
                    score = groupProd.getDataset('wei_QA')
                    QA_note = f"Score: {score.columns['QA_score'][i]}"
                    axes = plt.gca()
                    axes.text(1.0,1.1 - (i+1)/len(score.columns['QA_score']), QA_note,
                        verticalalignment='top', horizontalalignment='right',
                        transform=axes.transAxes,
                        color=c, fontdict=font)

            # Add Lw to Lt plots
            if rType=='LT':
                plt.plot(subwave, yLw, c=c, zorder=-1, linestyle='dashed')

            if plotDelta:
                # Generate the polygon for uncertainty bounds
                deltaPolyx = wave + list(reversed(wave))
                dPolyyPlus = [(y[i]+dy[i]) for i in range(len(y))]
                dPolyyMinus = [(y[i]-dy[i]) for i in range(len(y))]
                deltaPolyyPlus = y + list(reversed(dPolyyPlus))
                deltaPolyyMinus = y + list(reversed(dPolyyMinus))

                plt.fill(deltaPolyx, deltaPolyyPlus, alpha=0.2, c=c, zorder=-1)
                plt.fill(deltaPolyx, deltaPolyyMinus, alpha=0.2, c=c, zorder=-1)

            # Satellite Bands
            if ConfigFile.settings['bL2WeightMODISA']:
                # Plot the MODISA spectrum
                if plotDelta:
                    plt.errorbar(wave_MODISA, y_MODISA, yerr=dy_MODISA, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black', zorder=3) # ecolor is broken
                else:
                    plt.plot(wave_MODISA, y_MODISA, 'o', c=c)
            if ConfigFile.settings['bL2WeightMODIST']:
                # Plot the MODIST spectrum
                if plotDelta:
                    plt.errorbar(wave_MODIST, y_MODIST, yerr=dy_MODIST, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_MODIST, y_MODIST, 'o', c=c)
            if ConfigFile.settings['bL2WeightVIIRSN']:
                # Plot the VIIRSN spectrum
                if plotDelta:
                    plt.errorbar(wave_VIIRSN, y_VIIRSN, yerr=dy_VIIRSN, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_VIIRSN, y_VIIRSN, 'o', c=c)
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                # Plot the VIIRSJ spectrum
                if plotDelta:
                    plt.errorbar(wave_VIIRSJ, y_VIIRSJ, yerr=dy_VIIRSJ, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_VIIRSJ, y_VIIRSJ, 'o', c=c)
            if ConfigFile.settings['bL2WeightSentinel3A']:
                # Plot the Sentinel3A spectrum
                if plotDelta:
                    plt.errorbar(wave_Sentinel3A, y_Sentinel3A, yerr=dy_Sentinel3A, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_Sentinel3A, y_Sentinel3A, 'o', c=c)
            if ConfigFile.settings['bL2WeightSentinel3B']:
                # Plot the Sentinel3B spectrum
                if plotDelta:
                    plt.errorbar(wave_Sentinel3B, y_Sentinel3B, yerr=dy_Sentinel3B, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_Sentinel3B, y_Sentinel3B, 'o', c=c)

        axes = plt.gca()
        axes.set_title(filename, fontdict=font)
        # axes.set_xlim([390, 800])
        axes.set_ylim([minRad, maxRad])

        plt.xlabel('wavelength (nm)', fontdict=font)
        if rType=='LT':
            plt.ylabel('LT (LW dashed)', fontdict=font)
        else:
            plt.ylabel(rType, fontdict=font)

        # Tweak spacing to prevent clipping of labels
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)

        note = f'Interval: {ConfigFile.settings["fL2TimeInterval"]} s'
        axes.text(0.95, 0.95, note,
        verticalalignment='top', horizontalalignment='right',
        transform=axes.transAxes,
        color='black', fontdict=font)
        axes.grid()

        # plt.show() # --> QCoreApplication::exec: The event loop is already running

        # Save the plot
        filebasename = filename.split('_')
        fp = os.path.join(plotDir, '_'.join(filebasename[0:-1]) + '_' + rType + '.png')
        plt.savefig(fp)
        plt.close() # This prevents displaying the plot on screen with certain IDEs

    @staticmethod
    def plotRadiometryL1D(root, filename, rType):

        dirPath = os.getcwd()
        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L1D')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        plotRange = [305, 1140]

        if rType=='ES':
            print('Plotting Es')
            group = root.getGroup(rType)
            Data = group.getDataset(rType)

        if rType=='LI':
            print('Plotting Li')
            group = root.getGroup(rType)
            Data = group.getDataset(rType)

        if rType=='LT':
            print('Plotting Lt')
            group = root.getGroup(rType)
            Data = group.getDataset(rType)

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }

        # Hyperspectral
        x = []
        wave = []

        # For each waveband
        for k in Data.data.dtype.names:
            if Utilities.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    x.append(k)
                    wave.append(float(k))

        total = Data.data.shape[0]
        maxRad = 0
        minRad = 0
        cmap = cm.get_cmap("jet")
        color=iter(cmap(np.linspace(0,1,total)))

        plt.figure(1, figsize=(8,6))
        for i in range(total):
            # Hyperspectral
            y = []
            for k in x:
                y.append(Data.data[k][i])

            c=next(color)
            if max(y) > maxRad:
                maxRad = max(y)+0.1*max(y)
            if rType == 'LI' and maxRad > 20:
                maxRad = 20
            if rType == 'LT' and maxRad > 10:
                maxRad = 10
            if min(y) < minRad:
                minRad = min(y)-0.1*min(y)
            if rType == 'LI':
                minRad = 0
            if rType == 'LT':
                minRad = 0
            if rType == 'ES':
                minRad = 0

            # Plot the Hyperspectral spectrum
            plt.plot(wave, y, c=c, zorder=-1)

        axes = plt.gca()
        axes.set_title(filename, fontdict=font)
        # axes.set_xlim([390, 800])
        axes.set_ylim([minRad, maxRad])

        plt.xlabel('wavelength (nm)', fontdict=font)
        plt.ylabel(rType, fontdict=font)

        # Tweak spacing to prevent clipping of labels
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)

        axes.grid()

        # plt.show() # --> QCoreApplication::exec: The event loop is already running

        # Save the plot
        filebasename = filename.split('_')
        fp = os.path.join(plotDir, '_'.join(filebasename[0:-1]) + '_' + rType + '.png')
        plt.savefig(fp)
        plt.close() # This prevents displaying the plot on screen with certain IDEs


    @staticmethod
    def plotTimeInterp(xData, xTimer, newXData, yTimer, instr, fileName):
        ''' Plot results of L1E time interpolation '''

        dirPath = os.getcwd()
        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L1E')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        # For the sake of MacOS, need to hack the datetimes into panda dataframes for plotting
        dfx = pd.DataFrame(data=xTimer, index=list(range(0,len(xTimer))), columns=['x'])
        # *** HACK: CONVERT datetime column to string and back again - who knows why this works? ***
        dfx['x'] = pd.to_datetime(dfx['x'].astype(str))
        dfy = pd.DataFrame(data=yTimer, index=list(range(0,len(yTimer))), columns=['x'])
        dfy['x'] = pd.to_datetime(dfy['x'].astype(str))

        fileBaseName,_ = fileName.split('.')
        register_matplotlib_converters()

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }

        # Steps in wavebands used for plots
        # step = float(ConfigFile.settings["fL3InterpInterval"]) # this is in nm
        # This happens prior to waveband interpolation, so each interval is ~3.3 nm
        ''' To Do: THIS COULD BE SET IN THE CONFIG WINDOW '''
        step = 20 # this is in band intervals

        if instr == 'ES' or instr == 'LI' or instr == 'LT':
            l = round((len(xData.data.dtype.names)-3)/step) # skip date and time and datetime
            index = l
        else:
            l = len(xData.data.dtype.names)-3 # skip date and time and datetime
            index = None

        if index:
            progressBar = tqdm(total=l, unit_scale=True, unit_divisor=step)

        ticker = 0
        if index is not None:
            for k in xData.data.dtype.names:
                if index % step == 0:
                    if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                        continue
                    ticker += 1
                    progressBar.update(1)

                    x = np.copy(xData.data[k]).tolist()
                    new_x = np.copy(newXData.columns[k]).tolist()

                    fig = plt.figure(figsize=(12, 4))
                    ax = fig.add_subplot(1, 1, 1)
                    # ax.plot(xTimer, x, 'bo', label='Raw')
                    ax.plot(dfx['x'], x, 'bo', label='Raw')
                    # ax.plot(yTimer, new_x, 'k.', label='Interpolated')
                    ax.plot(dfy['x'], new_x, 'k.', label='Interpolated')
                    ax.legend()

                    plt.xlabel('Date/Time (UTC)', fontdict=font)
                    plt.ylabel(f'{instr}_{k}', fontdict=font)
                    plt.subplots_adjust(left=0.15)
                    plt.subplots_adjust(bottom=0.15)

                    # plt.savefig(os.path.join('Plots','L1E',f'{fileBaseName}_{instr}_{k}.png'))
                    plt.savefig(os.path.join(plotDir,f'{fileBaseName}_{instr}_{k}.png'))
                    plt.close()
                index +=1
        else:
            for k in xData.data.dtype.names:
                if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                    continue

                x = np.copy(xData.data[k]).tolist()
                new_x = np.copy(newXData.columns[k]).tolist()

                fig = plt.figure(figsize=(12, 4))
                ax = fig.add_subplot(1, 1, 1)
                # ax.plot(xTimer, x, 'bo', label='Raw')
                ax.plot(dfx['x'], x, 'bo', label='Raw')
                # ax.plot(yTimer, new_x, 'k.', label='Interpolated')
                ax.plot(dfy['x'], new_x, 'k.', label='Interpolated')
                ax.legend()

                plt.xlabel('Date/Time (UTC)', fontdict=font)
                plt.ylabel(f'{instr}', fontdict=font)
                plt.subplots_adjust(left=0.15)
                plt.subplots_adjust(bottom=0.15)

                plt.savefig(os.path.join(plotDir,f'{fileBaseName}_{instr}_{k}.png'))
                plt.close()

        print('\n')

    @staticmethod
    def specFilter(inFilePath, Dataset, timeStamp, station=None, filterRange=[400, 700],\
                filterFactor=3, rType='None'):

        dirPath = os.getcwd()
        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L2_Spectral_Filter')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        font = {'family': 'serif',
                'color':  'darkred',
                'weight': 'normal',
                'size': 16,
                }

        # Collect each column name ignoring Datetag and Timetag2 (i.e. each wavelength) in the desired range
        x = []
        wave = []
        for k in Dataset.data.dtype.names:
            if Utilities.isFloat(k):
                if float(k)>=filterRange[0] and float(k)<=filterRange[1]:
                    x.append(k)
                    wave.append(float(k))

        # Read in each spectrum
        total = Dataset.data.shape[0]
        specArray = []
        normSpec = []
        # cmap = cm.get_cmap("jet")
        # color=iter(cmap(np.linspace(0,1,total)))
        print('Creating plots...')
        plt.figure(1, figsize=(10,8))
        for timei in range(total):
            y = []
            for waveband in x:
                y.append(Dataset.data[waveband][timei])

            specArray.append(y)
            peakIndx = y.index(max(y))
            normSpec.append(y / y[peakIndx])
            # plt.plot(wave, y / y[peakIndx], color='grey')

        normSpec = np.array(normSpec)

        aveSpec = np.median(normSpec, axis = 0)
        stdSpec = np.std(normSpec, axis = 0)

        badTimes  = []
        badIndx = []
        # For each spectral band...
        for i in range(0, len(normSpec[0])-1):
            # For each timeseries radiometric measurement...
            for j, rad in enumerate(normSpec[:,i]):
                # Identify outliers and negative values for elimination
                if rad > (aveSpec[i] + filterFactor*stdSpec[i]) or \
                    rad < (aveSpec[i] - filterFactor*stdSpec[i]) or \
                    rad < 0:
                    badIndx.append(j)
                    badTimes.append(timeStamp[j])

        badIndx = np.unique(badIndx)
        badTimes = np.unique(badTimes)
        # Duplicates each element to a list of two elements in a list:
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3)

        # t0 = time.time()
        for timei in range(total):
        # for i in badIndx:
            if timei in badIndx:
                # plt.plot( wave, normSpec[i,:], color='red', linewidth=0.5, linestyle=(0, (1, 10)) ) # long-dot
                plt.plot( wave, normSpec[timei,:], color='red', linewidth=0.5, linestyle=(0, (5, 5)) ) # dashed
            else:
                plt.plot(wave, normSpec[timei,:], color='grey')

        # t1 = time.time()
        # print(f'Time elapsed: {str(round((t1-t0)))} Seconds')

        plt.plot(wave, aveSpec, color='black', linewidth=0.5)
        plt.plot(wave, aveSpec + filterFactor*stdSpec, color='black', linewidth=2, linestyle='dashed')
        plt.plot(wave, aveSpec - filterFactor*stdSpec, color='black', linewidth=2, linestyle='dashed')

        plt.title(f'Sigma = {filterFactor}', fontdict=font)
        plt.xlabel('Wavelength [nm]', fontdict=font)
        plt.ylabel(f'{rType} [Normalized to peak value]', fontdict=font)
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)
        axes = plt.gca()
        axes.grid()

        # Save the plot
        _,filename = os.path.split(inFilePath)
        filebasename,_ = filename.rsplit('_',1)
        if station:
            fp = os.path.join(plotDir, f'STATION_{station}_{filebasename}_{rType}.png')
        else:
            fp = os.path.join(plotDir, f'{filebasename}_{rType}.png')
        plt.savefig(fp)
        plt.close()

        return badTimes

    @staticmethod
    def plotIOPs(root, filename, algorithm, iopType, plotDelta = False):

        dirPath = os.getcwd()
        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L2_Products')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }

        cmap = cm.get_cmap("jet")

        # dataDelta = None

        group = root.getGroup("DERIVED_PRODUCTS")
        # if iopType=='a':
        #     print('Plotting absorption')

        if algorithm == "qaa" or algorithm == "giop":
            plotRange = [340, 700]
            qaaName = f'bL2Prod{iopType}Qaa'
            giopName = f'bL2Prod{iopType}Giop'
            if ConfigFile.products["bL2Prodqaa"] and ConfigFile.products[qaaName]:
                label = f'qaa_{iopType}'
                DataQAA = group.getDataset(label)
                # if plotDelta:
                #     dataDelta = group.getDataset(f'{iopType}_HYPER_delta')

                xQAA = []
                waveQAA = []
                # For each waveband
                for k in DataQAA.data.dtype.names:
                    if Utilities.isFloat(k):
                        if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                            xQAA.append(k)
                            waveQAA.append(float(k))
                totalQAA = DataQAA.data.shape[0]
                colorQAA = iter(cmap(np.linspace(0,1,totalQAA)))

            if ConfigFile.products["bL2Prodgiop"] and ConfigFile.products[giopName]:
                label = f'giop_{iopType}'
                DataGIOP = group.getDataset(label)
                # if plotDelta:
                #     dataDelta = group.getDataset(f'{iopType}_HYPER_delta')

                xGIOP = []
                waveGIOP = []
                # For each waveband
                for k in DataGIOP.data.dtype.names:
                    if Utilities.isFloat(k):
                        if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                            xGIOP.append(k)
                            waveGIOP.append(float(k))
                totalGIOP = DataQAA.data.shape[0]
                colorGIOP = iter(cmap(np.linspace(0,1,totalGIOP)))


        if algorithm == "gocad":
            plotRange = [270, 700]
            gocadName = f'bL2Prod{iopType}'
            if ConfigFile.products["bL2Prodgocad"] and ConfigFile.products[gocadName]:

                # ag
                label = f'gocad_{iopType}'
                agDataGOCAD = group.getDataset(label)
                # if plotDelta:
                #     dataDelta = group.getDataset(f'{iopType}_HYPER_delta')

                agGOCAD = []
                waveGOCAD = []
                # For each waveband
                for k in agDataGOCAD.data.dtype.names:
                    if Utilities.isFloat(k):
                        if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                            agGOCAD.append(k)
                            waveGOCAD.append(float(k))
                totalGOCAD = agDataGOCAD.data.shape[0]
                colorGOCAD = iter(cmap(np.linspace(0,1,totalGOCAD)))

                # Sg
                sgDataGOCAD = group.getDataset(f'gocad_Sg')

                sgGOCAD = []
                waveSgGOCAD = []
                # For each waveband
                for k in sgDataGOCAD.data.dtype.names:
                    if Utilities.isFloat(k):
                        if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                            sgGOCAD.append(k)
                            waveSgGOCAD.append(float(k))

                # DOC
                docDataGOCAD = group.getDataset(f'gocad_doc')

        maxIOP = 0
        minIOP = 0

        # Plot
        plt.figure(1, figsize=(8,6))

        if algorithm == "qaa" or algorithm == "giop":
            if ConfigFile.products["bL2Prodqaa"] and ConfigFile.products[qaaName]:
                for i in range(totalQAA):
                    y = []
                    # dy = []
                    for k in xQAA:
                        y.append(DataQAA.data[k][i])
                        # if plotDelta:
                        #     dy.append(dataDelta.data[k][i])

                    c=next(colorQAA)
                    if max(y) > maxIOP:
                        maxIOP = max(y)+0.1*max(y)
                    # if iopType == 'LI' and maxIOP > 20:
                    #     maxIOP = 20

                    # Plot the Hyperspectral spectrum
                    plt.plot(waveQAA, y, c=c, zorder=-1)

                    # if plotDelta:
                    #     # Generate the polygon for uncertainty bounds
                    #     deltaPolyx = wave + list(reversed(wave))
                    #     dPolyyPlus = [(y[i]+dy[i]) for i in range(len(y))]
                    #     dPolyyMinus = [(y[i]-dy[i]) for i in range(len(y))]
                    #     deltaPolyyPlus = y + list(reversed(dPolyyPlus))
                    #     deltaPolyyMinus = y + list(reversed(dPolyyMinus))
                    #     plt.fill(deltaPolyx, deltaPolyyPlus, alpha=0.2, c=c, zorder=-1)
                    #     plt.fill(deltaPolyx, deltaPolyyMinus, alpha=0.2, c=c, zorder=-1)
            if ConfigFile.products["bL2Prodgiop"] and ConfigFile.products[giopName]:
                for i in range(totalGIOP):
                    y = []
                    for k in xGIOP:
                        y.append(DataGIOP.data[k][i])

                    c=next(colorGIOP)
                    if max(y) > maxIOP:
                        maxIOP = max(y)+0.1*max(y)

                    # Plot the Hyperspectral spectrum
                    plt.plot(waveGIOP, y,  c=c, ls='--', zorder=-1)

        if algorithm == "gocad":
            if ConfigFile.products["bL2Prodgocad"] and ConfigFile.products[gocadName]:
                for i in range(totalGOCAD):
                    y = []
                    for k in agGOCAD:
                        y.append(agDataGOCAD.data[k][i])

                    c=next(colorGOCAD)
                    if max(y) > maxIOP:
                        maxIOP = max(y)+0.1*max(y)

                    # Plot the point spectrum
                    # plt.scatter(waveGOCAD, y, s=100, c=c, marker='*', zorder=-1)
                    plt.plot(waveGOCAD, y, c=c, marker='*', markersize=13, linestyle = '', zorder=-1)

                    # Now extrapolate using the slopes
                    Sg = []
                    for k in sgGOCAD:
                        Sg.append(sgDataGOCAD.data[k][i])
                        yScaler = maxIOP*i/totalGOCAD
                        if k == '275':
                            wave = np.array(list(range(275, 300)))
                            ag_extrap = agDataGOCAD.data['275'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 275))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(285, 0.9*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S275 = ', sgDataGOCAD.data[k][i]), color=c)

                        if k == '300':
                            wave = np.array(list(range(300, 355)))
                            # uses the trailing end of the last extrapolation.
                            ag_extrap = ag_extrap[-1] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 300))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(300, 0.7*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S300 = ', sgDataGOCAD.data[k][i]), color=c)

                        if k == '350':
                            # Use the 350 slope starting at 355 (where we have ag)
                            wave = np.array(list(range(355, 380)))
                            ag_extrap = agDataGOCAD.data['355'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 355))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(350, 0.5*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S350 = ', sgDataGOCAD.data[k][i]), color=c)

                        if k == '380':
                            wave = np.array(list(range(380, 412)))
                            ag_extrap = agDataGOCAD.data['380'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 380))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(380, 0.3*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S380 = ', sgDataGOCAD.data[k][i]), color=c)

                        if k == '412':
                            wave = np.array(list(range(412, 700)))
                            ag_extrap = agDataGOCAD.data['412'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 412))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(440, 0.15*maxIOP- 0.12*yScaler, '{} {:.4f}'.format('S412 = ', sgDataGOCAD.data[k][i]), color=c)

                    # Now tack on DOC
                    plt.text(600, 0.5 - 0.12*yScaler, '{} {:3.2f}'.format('DOC = ', docDataGOCAD.data['doc'][i]) , color=c)

        axes = plt.gca()
        axes.set_title(filename, fontdict=font)
        axes.set_ylim([minIOP, maxIOP])

        plt.xlabel('wavelength (nm)', fontdict=font)
        plt.ylabel(f'{label} [1/m]', fontdict=font)

        # Tweak spacing to prevent clipping of labels
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)

        note = f'Interval: {ConfigFile.settings["fL2TimeInterval"]} s'
        axes.text(0.95, 0.95, note,
        verticalalignment='top', horizontalalignment='right',
        transform=axes.transAxes,
        color='black', fontdict=font)
        axes.grid()

        # plt.show() # --> QCoreApplication::exec: The event loop is already running

        # Save the plot
        filebasename = filename.split('_')
        fp = os.path.join(plotDir, '_'.join(filebasename[0:-1]) + '_' + label + '.png')
        plt.savefig(fp)
        plt.close() # This prevents displaying the plot on screen with certain IDEs

    @staticmethod
    def readAnomAnalFile(filePath):
        paramDict = {}
        with open(filePath, newline='') as csvfile:
            paramreader = csv.DictReader(csvfile)
            for row in paramreader:

                paramDict[row['filename']] = [int(row['ESWindowDark']), int(row['ESWindowLight']), \
                                    float(row['ESSigmaDark']), float(row['ESSigmaLight']),
                                    float(row['ESMinDark']), float(row['ESMaxDark']),
                                    float(row['ESMinMaxBandDark']),float(row['ESMinLight']),
                                    float(row['ESMaxLight']),float(row['ESMinMaxBandLight']),
                                    int(row['LIWindowDark']), int(row['LIWindowLight']),
                                    float(row['LISigmaDark']), float(row['LISigmaLight']),
                                    float(row['LIMinDark']), float(row['LIMaxDark']),\
                                    float(row['LIMinMaxBandDark']),float(row['LIMinLight']),\
                                    float(row['LIMaxLight']),float(row['LIMinMaxBandLight']),\
                                    int(row['LTWindowDark']), int(row['LTWindowLight']),
                                    float(row['LTSigmaDark']), float(row['LTSigmaLight']),
                                    float(row['LTMinDark']), float(row['LTMaxDark']),\
                                    float(row['LTMinMaxBandDark']),float(row['LTMinLight']),\
                                    float(row['LTMaxLight']),float(row['LTMinMaxBandLight']),int(row['Threshold']) ]
                paramDict[row['filename']] = [None if v==-999 else v for v in paramDict[row['filename']]]

        return paramDict

    @staticmethod
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
            avg = Utilities.movingAverage(radiometry1D, windowSize).tolist()
            residual = np.array(radiometry1D) - np.array(avg)
            stdData = np.std(residual)

            badIndex = Utilities.darkConvolution(radiometry1D,avg,stdData,sigma)

            # Second pass
            radiometry1D2 = np.array(radiometry1D[:])
            radiometry1D2[badIndex] = np.nan
            radiometry1D2 = radiometry1D2.tolist()
            avg2 = Utilities.movingAverage(radiometry1D2, windowSize).tolist()
            residual = np.array(radiometry1D2) - np.array(avg2)
            stdData = np.nanstd(residual)

            badIndex2 = Utilities.darkConvolution(radiometry1D2,avg2,stdData,sigma)

            # Threshold pass
            # Tolerates "None" for min or max Rad. ConfigFile.setting updated directly from checkbox
            badIndex3 = Utilities.l1dThresholds(band,radiometry1D,minRad,maxRad, minMaxBand)

        else:
            # For Lights, calculate the moving average and residual vectors
            #   and the ROLLING standard deviation of the residual

            # First pass
            avg = Utilities.movingAverage(radiometry1D, windowSize).tolist()
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

            badIndex = Utilities.lightConvolution(radiometry1D,avg,rolling_std,sigma)

            # Second pass
            radiometry1D2 = np.array(radiometry1D[:])
            radiometry1D2[badIndex] = np.nan
            radiometry1D2 = radiometry1D2.tolist()
            avg2 = Utilities.movingAverage(radiometry1D2, windowSize).tolist()
            residual2 = np.array(radiometry1D2) - np.array(avg2)
            residualDf2 = pd.DataFrame(residual2)
            testing_std_as_df2 = residualDf2.rolling(windowSize).std()
            rolling_std2 = testing_std_as_df2.replace(np.nan,
                testing_std_as_df2.iloc[windowSize - 1]).round(3).iloc[:,0].tolist()
            y = np.array(rolling_std2)
            y[np.isnan(y)] = np.nanmedian(y)
            y[y > np.nanmedian(y)+3*np.nanstd(y)] = np.nanmedian(y)
            rolling_std2 = y.tolist()

            badIndex2 = Utilities.lightConvolution(radiometry1D2,avg2,rolling_std2,sigma)

            # Threshold pass
            # Tolerates "None" for min or max Rad
            badIndex3 = Utilities.l1dThresholds(band, radiometry1D,minRad,maxRad, minMaxBand)

        return badIndex, badIndex2, badIndex3


    @staticmethod
    def saveDeglitchPlots(fileName,timeSeries,dateTime,sensorType,lightDark,windowSize,sigma,badIndex,badIndex2,badIndex3):#,\
        import matplotlib.dates as mdates
        #Plot results

        # # Set up datetime axis objects
        # #   https://stackoverflow.com/questions/49046931/how-can-i-use-dateaxisitem-of-pyqtgraph
        # class TimeAxisItem(pg.AxisItem):
        #     def tickStrings(self, values, scale, spacing):
        #         return [datetime.datetime.fromtimestamp(value, pytz.timezone("UTC")) for value in values]

        # date_axis_Dark = TimeAxisItem(orientation='bottom')
        # date_axis_Light = TimeAxisItem(orientation='bottom')
        dirPath = os.getcwd()
        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L1C_Anoms')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16}

        waveBand = timeSeries[0]

        radiometry1D = timeSeries[1]
        # x = np.arange(0,len(radiometry1D),1)
        x = np.array(dateTime)
        avg = Utilities.movingAverage(radiometry1D, windowSize).tolist()

        # try:
        text_xlabel="Time Series"
        text_ylabel=f'{sensorType}({waveBand}) {lightDark}'
        # plt.figure(figsize=(15, 8))
        fig, ax = plt.subplots(1)
        fig.autofmt_xdate()

        # First Pass
        y_anomaly = np.array(radiometry1D)[badIndex]
        x_anomaly = x[badIndex]
        # Second Pass
        y_anomaly2 = np.array(radiometry1D)[badIndex2]
        x_anomaly2 = x[badIndex2]
        # Thresholds
        y_anomaly3 = np.array(radiometry1D)[badIndex3]
        x_anomaly3 = x[badIndex3]

        plt.plot(x, radiometry1D, marker='o', color='k', linestyle='', fillstyle='none')
        plt.plot(x_anomaly, y_anomaly, marker='x', color='red', markersize=12, linestyle='')
        plt.plot(x_anomaly2, y_anomaly2, marker='+', color='red', markersize=12, linestyle='')
        plt.plot(x_anomaly3, y_anomaly3, marker='o', color='red', markersize=12, linestyle='', fillstyle='full', markerfacecolor='blue')
        # y_av = moving_average(radiometry1D, window_size)
        plt.plot(x[3:-3], avg[3:-3], color='green')

        xfmt = mdates.DateFormatter('%y-%m-%d %H:%M')
        ax.xaxis.set_major_formatter(xfmt)

        plt.text(0,0.95,'Marked for exclusions in ALL bands', transform=plt.gcf().transFigure)
        # plt.xlabel(text_xlabel, fontdict=font)
        plt.ylabel(text_ylabel, fontdict=font)
        plt.title('WindowSize = ' + str(windowSize) + ' Sigma Factor = ' + str(sigma), fontdict=font)

        fp = os.path.join(plotDir,fileName)
        # plotName = f'{fp}_W{windowSize}S{sigma}_{sensorType}{lightDark}_{waveBand}.png'
        plotName = f'{fp}_{sensorType}{lightDark}_{waveBand}.png'

        print(plotName)
        plt.savefig(plotName)
        plt.close()
        # except:
        #     e = sys.exc_info()[0]
        #     print("Error: %s" % e)

    @staticmethod
    def getDateTime(gp):
        dateTagDS = gp.getDataset('DATETAG')
        dateTags = dateTagDS.data["NONE"].tolist()
        timeTagDS = gp.getDataset('TIMETAG2')
        timeTags = timeTagDS.data["NONE"].tolist()
        # Conversion not set up for vectors, loop it
        dateTime=[]
        for i, dateTag in enumerate(dateTags):
            dt = Utilities.dateTagToDateTime(dateTag)
            dateTime.append(Utilities.timeTag2ToDateTime(dt,timeTags[i]))

        return dateTime
