
import datetime
import os
import sys

import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
import scipy.interpolate
from scipy.interpolate import splev, splrep
import pandas as pd

from ConfigFile import ConfigFile

# This gets reset later in Controller.processSingleLevel to reflect the file being processed.
if "LOGFILE" not in os.environ:
    os.environ["LOGFILE"] = "temp.log"

class Utilities:

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


    # Converts seconds to UTC
    @staticmethod
    def secToUtc(sec):
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return float("%d%02d%02d" % (h, m, s))

    # Converts GPS UTC time to seconds
    # Note: Does not support multiple days
    @staticmethod
    def utcToSec(utc):
        # Use zfill to ensure correct width, fixes bug when hour is 0 (12 am)
        t = str(int(utc)).zfill(6)
        # print(t)
        #print(t[:2], t[2:4], t[4:])
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:])
        return ((h*60)+m)*60+s

    # Converts datetag to date string
    @staticmethod
    def dateTagToDate(dateTag):
        dt = datetime.datetime.strptime(str(int(dateTag)), '%Y%j')
        return dt.strftime('%Y%m%d')

    # Converts datetag to datetime
    @staticmethod
    def dateTagToDateTime(dateTag):
        dt = datetime.datetime.strptime(str(int(dateTag)), '%Y%j')
        return dt

    # Converts seconds to TimeTag2
    @staticmethod
    def secToTimeTag2(sec):
        #return float(time.strftime("%H%M%S", time.gmtime(sec)))
        t = sec * 1000
        s, ms = divmod(t, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return float("%d%02d%02d%03d" % (h, m, s, ms))

    # Converts TimeTag2 to seconds
    @staticmethod
    def timeTag2ToSec(tt2):
        t = str(int(tt2)).zfill(9)
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:6])
        ms = int(t[6:])
        # print(h, m, s, ms)
        return ((h*60)+m)*60+s+(float(ms)/1000.0)

    # Converts datetime.date and TimeTag2 to datetime
    @staticmethod
    def timeTag2ToDateTime(dt,tt2):
        t = str(int(tt2)).zfill(9)
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:6])
        us = 1000*int(t[6:])
        # print(h, m, s, us)
        
        return datetime.datetime(dt.year,dt.month,dt.day,h,m,s,us)

    # Converts HDFRoot timestamp attribute to seconds
    @staticmethod
    def timestampToSec(timestamp):
        time = timestamp.split(" ")[3]
        t = time.split(":")
        h = int(t[0])
        m = int(t[1])
        s = int(t[2])
        return ((h*60)+m)*60+s
    
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
                if np.isnan(ds.data[k][x]):
                    return True
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


    # Wrapper for scipy interp1d that works even if
    # values in new_x are outside the range of values in x
    @staticmethod
    def interp(x, y, new_x, kind='linear', fill_value=0.0):

        # If the last value to interp to is larger than the last value interp'ed from,
        # then append that higher value onto the values to interp from
        n0 = len(x)-1
        n1 = len(new_x)-1
        if new_x[n1] > x[n0]:
            #print(new_x[n], x[n])
            x.append(new_x[n1])
            y.append(y[n0])
        # If the first value to interp to is less than the first value interp'd from,
        # then add that lesser value to the beginning of values to interp from
        if new_x[0] < x[0]:
            #print(new_x[0], x[0])
            x.insert(0, new_x[0])
            y.insert(0, y[0])

        new_y = scipy.interpolate.interp1d(x, y, kind=kind, bounds_error=False, fill_value=fill_value)(new_x)

        '''
        test = False
        for i in range(len(new_y)):
            if np.isnan(new_y[i]):
                #print("NaN")
                if test:
                    new_y[i] = darkData.data[k][darkData.data.shape[0]-1]
                else:
                    new_y[i] = darkData.data[k][0]
            else:
                test = True
        '''

        return new_y

    # Wrapper for scipy interp1d that works even if
    # values in new_x are outside the range of values in x
    @staticmethod
    def interpAngular(x, y, new_x):
        complement360 = np.rad2deg(np.unwrap(np.deg2rad(y)))
        f = scipy.interpolate.interp1d(x,complement360,kind='linear', bounds_error=False, fill_value=None)
        new_y = f(new_x)%360
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
    def plotRadiometry(root, dirpath, filename, rType):

        if rType=='Rrs':
            print('Plotting Rrs')
            group = root.getGroup("Reflectance")
            Data = group.getDataset(rType)            
            if not os.path.exists("Plots/L4_Rrs/"):
                os.makedirs("Plots/L4_Rrs/")
            plotdir = os.path.join(dirpath, 'Plots/L4_Rrs/')
            plotRange = [380, 800]
        else:
            if not os.path.exists("Plots/L4_EsLiLt"):
                os.makedirs("Plots/L4_EsLiLt")
            plotdir = os.path.join(dirpath, 'Plots/L4_EsLiLt/')
            plotRange = [305, 1140]

        if rType=='ES':
            print('Plotting Es')
            group = root.getGroup("Irradiance")
            Data = group.getDataset(rType)
            
        if rType=='LI':
            print('Plotting Li')
            group = root.getGroup("Radiance")
            Data = group.getDataset(rType)
            
        if rType=='LT':
            print('Plotting Lt')
            group = root.getGroup("Radiance")
            Data = group.getDataset(rType)            

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }

        x = []
        wave = []
        
        for k in Data.data.dtype.names:
            if Utilities.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]:
                    x.append(k)
                    wave.append(float(k))

        total = Data.data.shape[0]
        maxRad = 0
        cmap = cm.get_cmap("jet")
        color=iter(cmap(np.linspace(0,1,total)))

        plt.figure(1, figsize=(6,4))
        for i in range(total):
            y = []
            for k in x:
                y.append(Data.data[k][i])

            c=next(color)
            if max(y) > maxRad:
                maxRad = max(y)
            if rType == 'LI' and maxRad > 20:
                maxRad = 20
            if rType == 'LT' and maxRad > 2:
                maxRad = 2

            plt.plot(wave, y, 'k', c=c)
            #if (i % 25) == 0:
            #    plt.plot(x, y, 'k', color=(i/total, 0, 1-i/total, 1))
        # x1,x2,y1,y2 = plt.axis()
        # print(f'{x1} {x2} {y1} {y2}')        
        axes = plt.gca()
        axes.set_title(filename, fontdict=font)
        # axes.set_xlim([390, 800])
        axes.set_ylim([0, maxRad])
        
        plt.xlabel('wavelength (nm)', fontdict=font)
        plt.ylabel(rType, fontdict=font)

        # Tweak spacing to prevent clipping of labels
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)

        note = f'Interval: {ConfigFile.settings["fL4TimeInterval"]} s'
        axes.text(0.95, 0.95, note,
        verticalalignment='top', horizontalalignment='right',
        transform=axes.transAxes,
        color='black', fontdict=font)
        #plt.show()        


        # Create output directory        
        os.makedirs(plotdir, exist_ok=True)

        # Save the plot
        filebasename,_ = filename.split('_')
        fp = os.path.join(plotdir, filebasename + '_' + rType + '.png')
        plt.savefig(fp)
        plt.close() # This prevents displaying the polt on screen with certain IDEs
        # except:
        #     e = sys.exc_info()[0]
        #     print("Error: %s" % e)        
   

    @staticmethod
    def plotTimeInterp(xData, xTimer, newXData, yTimer, instr, fileName):     
        fileBaseName,_ = fileName.split('.')
        if not os.path.exists("Plots/L3"):
            os.makedirs("Plots/L3")   
        try:           
            font = {'family': 'serif',
                'color':  'darkred',
                'weight': 'normal',
                'size': 16,
                }

            if instr == 'ES' or instr == 'LI' or instr == 'LT':
                l = len(xData.data.dtype.names)-2 # skip date and time
                index = 0
            # elif instr == 'Heading':
            #     l = 2
            else:
                l = len(xData.data.dtype.names)
                index = None

            Utilities.printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
            
            # Steps in wavebands used for plots
            # step = float(ConfigFile.settings["fL3InterpInterval"]) # this is in nm
            # This happens prior to waveband interpolation, so each interval is ~3.5 nm
            step = 2 # this is in band intervals
            
            if index == 0:
                for i, k in enumerate(xData.data.dtype.names):
                    if index % step == 0: 
                        Utilities.printProgressBar(i+1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                        
                        if k == "Datetag" or k == "Timetag2":
                            continue                            
                        x = np.copy(xData.data[k]).tolist()
                        new_x = np.copy(newXData.columns[k]).tolist()

                        fig = plt.figure(figsize=(12, 4))
                        ax = fig.add_subplot(1, 1, 1)
                        ax.plot(xTimer, x, 'bo', label='Raw')
                        ax.plot(yTimer, new_x, 'k.', label='Interpolated')
                        ax.legend()

                        plt.xlabel('Seconds', fontdict=font)
                        plt.ylabel(f'{instr}_{k}', fontdict=font)
                        plt.subplots_adjust(left=0.15)
                        plt.subplots_adjust(bottom=0.15)
                        
                        plt.savefig(os.path.join('Plots','L3',f'{fileBaseName}_{instr}_{k}.png'))
                        plt.close()
                        # plt.show() # This doesn't work (at least on Ubuntu, haven't tried other platforms yet)                
                        # # Tweak spacing to prevent clipping of ylabel
                        # plt.subplots_adjust(left=0.15)     

                    index +=1     
            else:
                for i, k in enumerate(xData.data.dtype.names):
                    Utilities.printProgressBar(i+1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                    
                    if k == "Datetag" or k == "Timetag2":
                        continue                            
                    x = np.copy(xData.data[k]).tolist()
                    new_x = np.copy(newXData.columns[k]).tolist()

                    fig = plt.figure(figsize=(12, 4))
                    ax = fig.add_subplot(1, 1, 1)
                    ax.plot(xTimer, x, 'bo', label='Raw')
                    ax.plot(yTimer, new_x, 'k.', label='Interpolated')
                    ax.legend()

                    plt.xlabel('Seconds', fontdict=font)
                    plt.ylabel('Data', fontdict=font)
                    plt.subplots_adjust(left=0.15)
                    plt.subplots_adjust(bottom=0.15)
                    
                    plt.savefig(os.path.join('Plots','L3',f'{fileBaseName}_{instr}_{k}.png'))
                    plt.close()
                    
            print('\n')      
                
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)

    @staticmethod
    def specFilter(inFilePath, Dataset, timeStamp, filterRange, filterFactor, rType):
        dirpath = './'
        if not os.path.exists("Plots/L4_Spectral_Filter/"):
            os.makedirs("Plots/L4_Spectral_Filter/")
        plotdir = os.path.join(dirpath, 'Plots/L4_Spectral_Filter/')

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
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3)
        
        for i in badIndx:
            plt.plot(wave, normSpec[i,:], color='red', linewidth=0.5, linestyle='dashed')

        plt.xlabel('Seconds', fontdict=font)
        plt.ylabel('Data', fontdict=font)
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)
            
        # Create output directory        
        os.makedirs(plotdir, exist_ok=True)

        # Save the plot
        _,filename = os.path.split(inFilePath)
        filebasename,_ = filename.split('_')
        fp = os.path.join(plotdir, filebasename + '_' + rType + '.png')
        plt.savefig(fp)
        plt.close()

        return badTimes

    

    
