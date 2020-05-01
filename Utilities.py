
import os
import sys
import math
import datetime
import pytz
from collections import Counter

from PyQt5.QtWidgets import QApplication, QDesktopWidget, QWidget, QPushButton, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
import scipy.interpolate
from scipy.interpolate import splev, splrep
import pandas as pd
from pandas.plotting import register_matplotlib_converters

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
        # desktopsize = QDesktopWidget().screenGeometry()
        # size = msgBox.size()
        # top = (desktopsize.height()/2) - (size.height()/2)
        # left = (desktopsize.width() / 2) - (size.width() / 2)
        # msgBox.move(left,top)
        # msgBox.raise_()
        # msgBox.buttonClicked.connect(msgButtonClick)
        msgBox.exec_()

    # Print iterations progress
    @staticmethod
    def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
        # Print New Line on Complete
        if iteration == total: 
            print()

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
        time = timestamp.split(" ")[3]
        t = time.split(":")
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
            if gp.id != "SOLARTRACKER_STATUS": # No valid timestamps in STATUS
                dateTime = gp.addDataset("DATETIME")
                timeData = gp.getDataset("TIMETAG2").data["NONE"].tolist()
                dateTag = gp.getDataset("DATETAG").data["NONE"].tolist()
                timeStamp = [] 
                for i, time in enumerate(timeData):
                    # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
                    # Filter for aberrant Datetags
                    if (str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20")) \
                        and time != 0.0 and not np.isnan(time):

                        dt = Utilities.dateTagToDateTime(dateTag[i])
                        timeStamp.append(Utilities.timeTag2ToDateTime(dt, time))
                    else:                    
                        gp.datasetDeleteRow(i)
                        msg = f"Bad Datetag or Timetag2 found. Eliminating record. {dateTag[i]} : {time}"
                        print(msg)
                        Utilities.writeLogFile(msg)
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
                        for i, time in enumerate(timeData):
                            # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
                            # Filter for aberrant Datetags
                            if (str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20")) \
                                and time != 0.0 and not np.isnan(time):

                                dt = Utilities.dateTagToDateTime(dateTag[i])
                                timeStamp.append(Utilities.timeTag2ToDateTime(dt, time))
                            else:                    
                                gp.datasetDeleteRow(i)
                                msg = f"Bad Datetag or Timetag2 found. Eliminating record. {dateTag[i]} : {time}"
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
                    total = total - 1
                    msg = f'Out of order timestamp deleted at {i}'
                    print(msg)
                    Utilities.writeLogFile(msg)
            i = 1
            while i < total:

                if dateTime[i] <= dateTime[i-1]:

                    ''' BUG?:Same values of consecutive TT2s are shockingly common. Confirmed
                    that 1) they exist from L1A, and 2) sensor data changes while TT2 stays the same '''

                    gp.datasetDeleteRow(i)
                    del dateTime[i] # I'm fuzzy on why this is necessary; not a pointer?
                    total = total - 1
                    msg = f'Out of order TIMETAG2 row deleted at {i}'
                    # print(msg)
                    Utilities.writeLogFile(msg)
                    continue
                i += 1
        else:
            msg = '************Too few records to test for ascending timestamps. Exiting.'
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        if (globalTotal - total) > 0:
            msg = f'Data eliminated for non-increasing timestamps: {100*round((globalTotal - total)/globalTotal)}%'
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

        ''' BUG: I should probably rewrite this to be more cautious of extrapolation '''
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
    def interpAngular(x, y, new_x):
        ''' Wrapper for scipy interp1d that works even if
            values in new_x are outside the range of values in x'''

        # Some angular measurements (like SAS pointing) are + and -. Convert to all +
        # eliminate NaNs
        for i, value in enumerate(y):
            if value < 0:
                y[i] = 360 + value
            if np.isnan(value):
                x.pop(i)
                y.pop(i)

        y_rad = np.deg2rad(y)
        f = scipy.interpolate.interp1d(x,y_rad,kind='linear', bounds_error=False, fill_value=None)
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

    '''Below is the problematic interpolation scheme in PySciDON
    # # Wrapper for scipy UnivariateSpline interpolation
    # # This method does not seem stable unless points are uniform distance apart - results in all Nan output
    # @staticmethod
    # def interpSpline(x, y, new_x):

    #     #print("t0", len(x), len(y))
    #     n0 = len(x)-1
    #     n1 = len(new_x)-1
    #     if new_x[n1] > x[n0]:
    #         #print(new_x[n], x[n])
    #         x.append(new_x[n1])
    #         y.append(y[n0])
    #     if new_x[0] < x[0]:
    #         #print(new_x[0], x[0])
    #         x.insert(0, new_x[0])
    #         y.insert(0, y[0])

    #     new_y = scipy.interpolate.InterpolatedUnivariateSpline(x, y, k=3)(new_x)
    #     # print('len(new_y) = ' + str(len(new_y)))

    #     return new_y'''


    @staticmethod
    def plotRadiometry(root, dirpath, filename, rType, plotDelta = False):

        outDir = MainConfig.settings["outDir"]
        # If default output path is used, choose the root HyperInSPACE path, and build on that
        if os.path.abspath(outDir) == os.path.join(dirpath,'Data'):
            outDir = dirpath

        if not os.path.exists(os.path.join(outDir,'Plots','L2')):
            os.makedirs(os.path.join(outDir,'Plots','L2'))        
        plotdir = os.path.join(outDir,'Plots','L2')

        dataDelta = None
        ''' Note: If only one spectrum is left in a given ensemble, deltas will
        be zero for Es, Li, and Lt.'''
        
        if rType=='Rrs':
            print('Plotting Rrs')
            group = root.getGroup("REFLECTANCE")
            Data = group.getDataset(f'{rType}_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_delta')
            plotRange = [380, 800]
            if ConfigFile.settings['bL2WeightMODISA']:
                Data_MODISA = group.getDataset(f'{rType}_MODISA')
                if plotDelta:
                    dataDelta_MODISA = group.getDataset(f'{rType}_MODISA_delta')
            if ConfigFile.settings['bL2WeightMODIST']:
                Data_MODIST = group.getDataset(f'{rType}_MODIST')
                if plotDelta:
                    dataDelta_MODIST = group.getDataset(f'{rType}_MODIST_delta')
            if ConfigFile.settings['bL2WeightVIIRSN']:
                Data_VIIRSN = group.getDataset(f'{rType}_VIIRSN')
                if plotDelta:
                    dataDelta_VIIRSN = group.getDataset(f'{rType}_VIIRSN_delta')
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                Data_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ')
                if plotDelta:
                    dataDelta_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ_delta')
            if ConfigFile.settings['bL2WeightSentinel3A']:
                Data_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A')
                if plotDelta:
                    dataDelta_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A_delta')
            if ConfigFile.settings['bL2WeightSentinel3B']:
                Data_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B')
                if plotDelta:
                    dataDelta_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B_delta')

        if rType=='nLw':
            print('Plotting nLw')
            group = root.getGroup("REFLECTANCE")
            Data = group.getDataset(f'{rType}_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_delta')
            plotRange = [380, 800]   
            if ConfigFile.settings['bL2WeightMODISA']:        
                Data_MODISA = group.getDataset(f'{rType}_MODISA')
                if plotDelta:
                    dataDelta_MODISA = group.getDataset(f'{rType}_MODISA_delta')
            if ConfigFile.settings['bL2WeightMODIST']:        
                Data_MODIST = group.getDataset(f'{rType}_MODIST')
                if plotDelta:
                    dataDelta_MODIST = group.getDataset(f'{rType}_MODIST_delta')
            if ConfigFile.settings['bL2WeightVIIRSN']:        
                Data_VIIRSN = group.getDataset(f'{rType}_VIIRSN')
                if plotDelta:
                    dataDelta_VIIRSN = group.getDataset(f'{rType}_VIIRSN_delta')
            if ConfigFile.settings['bL2WeightVIIRSJ']:        
                Data_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ')
                if plotDelta:
                    dataDelta_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ_delta')
            if ConfigFile.settings['bL2WeightSentinel3A']:        
                Data_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A')
                if plotDelta:
                    dataDelta_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A_delta')
            if ConfigFile.settings['bL2WeightSentinel3B']:        
                Data_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B')
                if plotDelta:
                    dataDelta_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B_delta')

        ''' Could include satellite convolved (ir)radiances in the future '''
        if rType=='ES':
            print('Plotting Es')
            group = root.getGroup("IRRADIANCE")
            Data = group.getDataset(f'{rType}_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_delta')
            plotRange = [305, 1140]
            
        if rType=='LI':
            print('Plotting Li')
            group = root.getGroup("RADIANCE")
            Data = group.getDataset(f'{rType}_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_delta')
            plotRange = [305, 1140]
            
        if rType=='LT':
            print('Plotting Lt')
            group = root.getGroup("RADIANCE")
            Data = group.getDataset(f'{rType}_HYPER')  
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_delta')          
            plotRange = [305, 1140]

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
            plt.plot(wave, y, 'k', c=c, zorder=-1)
            
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
        fp = os.path.join(plotdir, '_'.join(filebasename[0:-1]) + '_' + rType + '.png')
        plt.savefig(fp)
        plt.close() # This prevents displaying the plot on screen with certain IDEs          
   

    @staticmethod
    def plotTimeInterp(xData, xTimer, newXData, yTimer, instr, fileName):    
        ''' Plot results of L1E time interpolation '''

        fileBaseName,_ = fileName.split('.')
        register_matplotlib_converters()
        
        outDir = MainConfig.settings["outDir"]
        # If default output path is used, choose the root HyperInSPACE path, and build on that
        if os.path.abspath(outDir) == os.path.join('./','Data'):
            outDir = './'

        if not os.path.exists(os.path.join(outDir,'Plots','L1E')):
            os.makedirs(os.path.join(outDir,'Plots','L1E'))        
        plotdir = os.path.join(outDir,'Plots','L1E')

        # if not os.path.exists(os.path.join('Plots','L1E')):
        #     os.makedirs(os.path.join('Plots','L1E'))
        try:           
            font = {'family': 'serif',
                'color':  'darkred',
                'weight': 'normal',
                'size': 16,
                }

            # Steps in wavebands used for plots
            # step = float(ConfigFile.settings["fL3InterpInterval"]) # this is in nm
            # This happens prior to waveband interpolation, so each interval is ~3.3 nm
            step = 5 # this is in band intervals
            
            if instr == 'ES' or instr == 'LI' or instr == 'LT':                
                l = round((len(xData.data.dtype.names)-3)/step) # skip date and time and datetime
                index = l
            else:
                l = len(xData.data.dtype.names)-3 # skip date and time and datetime
                index = None

            Utilities.printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)            
            
            ticker = 0
            if index is not None:
                for k in xData.data.dtype.names:
                    if index % step == 0:                                                 
                        if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                            continue  
                        ticker += 1    
                        Utilities.printProgressBar(ticker, l, prefix = 'Progress:', suffix = 'Complete', length = 50)                      
                        x = np.copy(xData.data[k]).tolist()
                        new_x = np.copy(newXData.columns[k]).tolist()

                        fig = plt.figure(figsize=(12, 4))
                        ax = fig.add_subplot(1, 1, 1)
                        ax.plot(xTimer, x, 'bo', label='Raw')
                        ax.plot(yTimer, new_x, 'k.', label='Interpolated')
                        ax.legend()

                        plt.xlabel('Date/Time (UTC)', fontdict=font)
                        plt.ylabel(f'{instr}_{k}', fontdict=font)
                        plt.subplots_adjust(left=0.15)
                        plt.subplots_adjust(bottom=0.15)
                        
                        plt.savefig(os.path.join('Plots','L1E',f'{fileBaseName}_{instr}_{k}.png'))
                        # plt.show() # This doesn't work (at least on Ubuntu, haven't tried other platforms yet)  
                        plt.close()                                      
                        # # Tweak spacing to prevent clipping of ylabel
                        # plt.subplots_adjust(left=0.15)     

                    index +=1     
            else:
                for k in xData.data.dtype.names:                                        
                    if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                        continue     
                    ticker += 1                  
                    Utilities.printProgressBar(ticker, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                    x = np.copy(xData.data[k]).tolist()
                    new_x = np.copy(newXData.columns[k]).tolist()

                    fig = plt.figure(figsize=(12, 4))
                    ax = fig.add_subplot(1, 1, 1)
                    ax.plot(xTimer, x, 'bo', label='Raw')
                    ax.plot(yTimer, new_x, 'k.', label='Interpolated')
                    ax.legend()

                    plt.xlabel('Date/Time (UTC)', fontdict=font)
                    plt.ylabel(f'{instr}', fontdict=font)
                    plt.subplots_adjust(left=0.15)
                    plt.subplots_adjust(bottom=0.15)
                    
                    plt.savefig(os.path.join(plotdir,f'{fileBaseName}_{instr}_{k}.png'))
                    plt.close()
                    
            print('\n')      
                
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)

    @staticmethod
    def specFilter(inFilePath, Dataset, timeStamp, station=None, filterRange=[400, 700],\
                filterFactor=3, rType='None'):
        dirpath = './'

        outDir = MainConfig.settings["outDir"]
        # If default output path is used, choose the root HyperInSPACE path, and build on that
        if os.path.abspath(outDir) == os.path.join(dirpath,'Data'):
            outDir = dirpath

        if not os.path.exists(os.path.join(outDir,'Plots','L2_Spectral_Filter')):
            os.makedirs(os.path.join(outDir,'Plots','L2_Spectral_Filter'))        
        plotdir = os.path.join(outDir,'Plots','L2_Spectral_Filter')
                

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
        plt.figure(1, figsize=(10,8))
        for time in range(total):
            y = []
            for waveband in x:
                y.append(Dataset.data[waveband][time])
            
            specArray.append(y)
            peakIndx = y.index(max(y))
            normSpec.append(y / y[peakIndx])
            # c=next(color)
            # plt.plot(wave, y / y[peakIndx], 'k', c=c)
            plt.plot(wave, y / y[peakIndx], color='grey')

        normSpec = np.array(normSpec)
        
        aveSpec = np.median(normSpec, axis = 0)
        stdSpec = np.std(normSpec, axis = 0)

        plt.plot(wave, aveSpec, color='black', linewidth=0.5)
        plt.plot(wave, aveSpec + filterFactor*stdSpec, color='black', linewidth=2, linestyle='dashed')
        plt.plot(wave, aveSpec - filterFactor*stdSpec, color='black', linewidth=2, linestyle='dashed')

        badTimes  = []
        badIndx = []
        # For each spectral band...
        for i in range(0, len(normSpec[0])-1):
            # For each timeserioes radiometric measurement...
            for j, rad in enumerate(normSpec[:,i]):
                # Identify outliers and negative values for elimination
                if rad > (aveSpec[i] + filterFactor*stdSpec[i]) or \
                    rad < (aveSpec[i] - filterFactor*stdSpec[i]) or \
                    rad < 0:
                    badIndx.append(j)
                    badTimes.append(timeStamp[j])

        badTimes = np.unique(badTimes)
        # Duplicates each element to a list of two elements in a list:
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) 
        
        for i in badIndx:
            plt.plot(wave, normSpec[i,:], color='red', linewidth=0.5, linestyle='dashed')

        plt.xlabel('Wavelength [nm]', fontdict=font)
        plt.ylabel(f'{rType}', fontdict=font)
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)
            
        # Create output directory        
        os.makedirs(plotdir, exist_ok=True)

        # Save the plot
        _,filename = os.path.split(inFilePath)
        filebasename,_ = filename.split('_')
        if station:
            fp = os.path.join(plotdir, f'{station}_{filebasename}_{rType}.png')
        else:            
            fp = os.path.join(plotdir, f'{filebasename}_{rType}.png')
        plt.savefig(fp)
        plt.close()

        return badTimes

    

    
