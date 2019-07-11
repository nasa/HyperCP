
import os
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from PyQt5 import QtCore, QtGui, QtWidgets


from ConfigFile import ConfigFile
from HDFRoot import HDFRoot
from Utilities import Utilities        


def AnomalyDetection(self,inputDirectory):
    print("AnomalyDetection - Launching anomaly analysis")

    if not os.path.exists("Plots/Anomalies"):
            os.makedirs("Plots/Anomalies")

    # Open L1B HDF5 file for Deglitching        
    inFilePath,_ = QtWidgets.QFileDialog.getOpenFileNames(self, "Open L1B HDF5 file for Deglitching", \
        inputDirectory)
    print(inFilePath[0])

    windowSizeDark = int(self.l2Deglitch0LineEdit.text())
    windowSizeLight= int(self.l2Deglitch1LineEdit.text())
    sigmaDark = float(self.l2Deglitch2LineEdit.text())
    sigmaLight = float(self.l2Deglitch3LineEdit.text())
    sensorTypes = ["ES","LT","LI"]

    root = HDFRoot.readHDF5(inFilePath[0])
    fileName = os.path.basename(os.path.splitext(inFilePath[0])[0])


    for sensorType in sensorTypes:
        print(sensorType)
        darkData = None
        lightData = None

        for gp in root.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                darkData = gp.getDataset(sensorType)
                # print(type(darkData))
                # print(type(darkData.data))
            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
            
        if darkData is None:
            print("Error: No dark data to deglitch")
        else:
            print("Dark data anomaly analysis") 
            lightDark = 'Dark'       
            darkData.datasetToColumns()
            columns = darkData.columns

            step = 20 # Steps in wavebands used for plots
            index = 0
            for k in columns.items():
                if index % step == 0:                    
                    deglitchAndPlot(fileName,k,sensorType,lightDark,windowSizeDark,sigmaDark,\
                        text_ylabel=sensorType + " Darks " + k[0])
                index +=1

        if lightData is None:
            print("Error: No light data to deglitch")
        else:    
            print("Light data anomaly analysis") 
            lightDark = 'Light'       
            lightData.datasetToColumns()
            columns = lightData.columns

            step = 20
            index = 0        
            for k in columns.items():
                if index % step == 0:                    
                    # print('Window: ' + str(windowSizeLight) + ' Sigma: ' + str(sigmaLight))
                    deglitchAndPlot(fileName,k,sensorType,lightDark,windowSizeLight,sigmaLight,\
                        text_ylabel=sensorType + " Lights " + k[0])
                index += 1

def deglitchAndPlot(fileName,k,sensorType,lightDark,windowSize,sigma,\
    text_xlabel="Series",\
    text_ylabel="Radiometry"):      

    timeSeries = k[1]     
    avg = Utilities.movingAverage(timeSeries, windowSize).tolist()        
    # avg = Utilities.windowAverage(timeSeries, windowSize).mean().values.tolist()  
    residual = np.array(timeSeries) - np.array(avg)
    stdData = np.std(residual)
    x = np.arange(0,len(timeSeries),1)     

    if lightDark=='Dark':        
        # First pass
        badIndex = Utilities.darkConvolution(timeSeries,avg,stdData,sigma)  

        # Second pass
        timeSeries2 = np.array(timeSeries[:])
        timeSeries2[badIndex] = np.nan
        timeSeries2 = timeSeries2.tolist()
        avg2 = Utilities.movingAverage(timeSeries2, windowSize).tolist()        
        # avg2 = Utilities.windowAverage(timeSeries2, windowSize).mean().values.tolist()        
        residual = np.array(timeSeries2) - np.array(avg2)
        stdData = np.nanstd(residual)        

        badIndex2 = Utilities.darkConvolution(timeSeries2,avg2,stdData,sigma)        
    else:   
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
        badIndex = Utilities.lightConvolution(timeSeries,avg,rolling_std,sigma)

        # Second pass
        timeSeries2 = np.array(timeSeries[:])
        timeSeries2[badIndex] = np.nan
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
        # print(badIndex2)       
    #Plot results  
    font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16}   
    # try:     
    plt.figure(figsize=(15, 8))
    
    # y_av = moving_average(timeSeries, window_size)
    plt.plot(x[3:-3], avg[3:-3], color='green')
    y_anomaly = np.array(timeSeries)[badIndex]
    x_anomaly = x[badIndex]
    y_anomaly2 = np.array(timeSeries)[badIndex2]
    x_anomaly2 = x[badIndex2]
    plt.plot(x_anomaly, y_anomaly, "rs", markersize=12)
    plt.plot(x_anomaly2, y_anomaly2, "b*", markersize=12)
    plt.plot(x, timeSeries, "k.")

    plt.xlabel(text_xlabel, fontdict=font)
    plt.ylabel(text_ylabel, fontdict=font)   
    plt.title('WindowSize = ' + str(windowSize) + ' Sigma Factor = ' + str(sigma), fontdict=font) 

    plotName = ('Plots/Anomalies/' + fileName + '_W' + str(windowSize) + 'S' + str(sigma) + '_' \
        + sensorType + lightDark + '_' + k[0] + '.png')
    print(plotName)
    plt.savefig(plotName)
    plt.close()    
    # except:
    #     e = sys.exc_info()[0]
    #     print("Error: %s" % e)

