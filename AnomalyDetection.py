
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
# matplotlib.use('Qt4Agg')
# matplotlib.use("TkAgg")
import sys

import easygui
from itertools import count

from HDFRoot import HDFRoot
from Utilities import Utilities

def plotDeglitch(k,avg,residual,std,sensorType,lightDark,windowSize,sigma,\
    text_xlabel="Series",\
    text_ylabel="Radiometry"):      

    data = k[1]
    x = np.arange(0,len(data),1) 
    # Calculate the variation in the distribution of the residual
    residualDf = pd.DataFrame(residual)
    testing_std_as_df = residualDf.rolling(windowSize).std()
    rolling_std = testing_std_as_df.replace(np.nan,
                        testing_std_as_df.iloc[windowSize - 1]).round(3).iloc[:,0].tolist()

    badIndex = []

    if lightDark=='Dark':
        for i in range(len(data)):
            if i < 2 or i > len(data)-2:
                # First and last avg values from convolution are not to be trusted
                badIndex.append(True)
            else:
                # Use stationary standard deviation anomaly (from rolling average) detection for dark data
                if (data[i] > avg[i] + (sigma*std)) or (data[i] < avg[i] - (sigma*std)):
                    badIndex.append(True)
                else:
                    badIndex.append(False)
    else:
        for i in range(len(data)):
            if i < 2 or i > len(data)-2:
                # First and last avg values from convolution are not to be trusted
                badIndex.append(True)
            else:

                # Use rolling standard deviation anomaly (from rolling average) detection for dark data
                if (data[i] > avg[i] + (sigma*rolling_std[i])) or (data[i] < avg[i] - (sigma*rolling_std[i])):
                    badIndex.append(True)
                else:
                    badIndex.append(False)

    #Plot results  
    font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16}   
    # try:     
    plt.figure(figsize=(15, 8))
    
    # y_av = moving_average(data, window_size)
    plt.plot(x[3:-3], avg[3:-3], color='green')
    y_anomaly = np.array(data)[badIndex]
    x_anomaly = x[badIndex]
    plt.plot(x_anomaly, y_anomaly, "r*", markersize=12)
    plt.plot(x, data, "k.")

    plt.xlabel(text_xlabel, fontdict=font)
    plt.ylabel(text_ylabel, fontdict=font)   
    plt.title('WindowSize = ' + str(windowSize) + ' Sigma Factor = ' + str(sigma), fontdict=font) 

    plotName = ('Plots/Anomalies/W' + str(windowSize) + 'S' + str(sigma) + '_' \
        + sensorType + lightDark + '_' + k[0] + '.png')
    print(plotName)
    plt.savefig(plotName)
    plt.close()    
    # except:
    #     e = sys.exc_info()[0]
    #     print("Error: %s" % e)

def launchAnomalyDetection(selfy):
    if not os.path.exists("Plots/Anomalies"):
            os.makedirs("Plots/Anomalies")

    # print(outputDirectory)
    # default_L1B_dir = outputDirectory


    # Open L1B HDF5 file for Deglitching
    # inFilePath = easygui.fileopenbox(msg=None, title=None, default='*', filetypes=None)
    # , multiple=False)
    inFilePath = easygui.fileopenbox(msg="Open L1B HDF5 file for Deglitching", \
        title="Open HDF5 L1B", filetypes=None, multiple=False)

    print(inFilePath)
    windowSizeDark = int(input("Enter window size for Darks: "))
    sigmaDark = int(input("Enter sigma multiplier for Darks: "))
    windowSizeLight = int(input("Enter window size for Lights: "))
    sigmaLight = int(input("Enter sigma multiplier for Lights: "))
    sensorTypes = ["ES","LT","LI"]

    root = HDFRoot.readHDF5(inFilePath)


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

            step = 20
            index = 0
            for k in columns.items():
                if index % step == 0:
                    timeSeries = k[1]            
                    avg = Utilities.movingAverage(timeSeries, windowSizeDark).tolist()        
                    residual = np.array(timeSeries) - np.array(avg)
                    std = np.std(residual)

                    plotDeglitch(k,avg,residual,std,sensorType,lightDark,windowSizeDark,sigmaDark,\
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
                    timeSeries = k[1]            
                    avg = Utilities.movingAverage(timeSeries, windowSizeLight).tolist()        
                    residual = np.array(timeSeries) - np.array(avg)
                    std = np.std(residual)

                    # print('Window: ' + str(windowSizeLight) + ' Sigma: ' + str(sigmaLight))
                    plotDeglitch(k,avg,residual,std,sensorType,lightDark,windowSizeLight,sigmaLight,\
                        text_ylabel=sensorType + " Lights " + k[0])
                index += 1

# # Uncomment to run as an independant function
# x=2
# launchAnomalyDetection(x)