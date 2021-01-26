
import os
import sys
import shutil
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib
from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5.QtCore import Qt
# from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

from MainConfig import MainConfig
from ConfigFile import ConfigFile
from HDFRoot import HDFRoot
from Utilities import Utilities        

class AnomAnalWindow(QtWidgets.QDialog):
# class AnomAnalWindow(QtWidgets.QWidget):
    def __init__(self, inputDirectory, parent=None):
    # def __init__(self, inputDirectory):
        super().__init__(parent)
        self.inputDirectory = inputDirectory
        self.setModal(True)   

        print(inputDirectory)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k') 

        self.windowDark = ConfigFile.settings['fL1dWindowDark'] # int
        self.windowLight = ConfigFile.settings['fL1dWindowLight'] # int
        self.sigmaDark = ConfigFile.settings['fL1dSigmaDark'] # float
        self.sigmaLight = ConfigFile.settings['fL1dSigmaLight']# float

        # Set up the User Interface    
        self.initUI()

    def initUI(self):

        # These will be adjusted on the slider once a file is loaded
        interval = 10
        self.waveBands = list(range(380, 780 +1, interval))
        self.sLabel = QtWidgets.QLabel(f'{self.waveBands[0]}')
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.valueChanged.connect(self.sliderMove)
        self.slider.setMinimum(min(self.waveBands))
        self.slider.setMaximum(max(self.waveBands))
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(interval)
        self.slider.setValue(self.waveBands[0])
        # self.slider.setSingleStep(1)

        self.radioButton1 = QtWidgets.QRadioButton('ES')
        self.radioButton1.setChecked(True)
        self.sensor = 'ES'
        self.radioButton1.toggled.connect(self.radioClick)

        self.radioButton2 = QtWidgets.QRadioButton('LI')
        self.radioButton2.toggled.connect(self.radioClick)

        self.radioButton3 = QtWidgets.QRadioButton('LT')
        self.radioButton3.toggled.connect(self.radioClick)        

        self.loadButton = QtWidgets.QPushButton('Load L1C', self, clicked=self.loadL1Cfile)

        self.plotButton = QtWidgets.QPushButton('Update', self, clicked=self.plotButtonPressed)

        self.saveButton = QtWidgets.QPushButton('Save', self, clicked=self.saveButtonPressed)

        self.closeButton = QtWidgets.QPushButton('Close', self, clicked=self.closeButtonPressed)

        self.plotWidgetDark = pg.PlotWidget(self)            
        self.plotWidgetLight = pg.PlotWidget(self)     

        # Opening plot
        x=[0,0]
        y=[0,0]
        self.phDark = self.plotWidgetDark.plot(x,y, symbolPen='b',\
                 symbol='o', name='time series', pen=None)
        self.phTimeAveDark = self.plotWidgetDark.plot(x,y, pen='g', name='running')
        self.ph1stDark = self.plotWidgetDark.plot(x,y, symbolPen='r',\
                 symbol='x', name='1st pass', pen=None)
        self.ph2ndDark = self.plotWidgetDark.plot(x,y, symbolPen='r',\
                 symbol='+', name='2nd pass', pen=None)  

        self.phLight = self.plotWidgetLight.plot(x,y, symbolPen='b',\
                 symbol='o', name='time series', pen=None)
        self.phTimeAveLight = self.plotWidgetLight.plot(x,y, pen='g', name='running')
        self.ph1stLight = self.plotWidgetLight.plot(x,y, symbolPen='r',\
                 symbol='x', name='1st pass', pen=None)
        self.ph2ndLight = self.plotWidgetLight.plot(x,y, symbolPen='r',\
                 symbol='+', name='2nd pass', pen=None)   
                            
        # Layout
        self.VBox = QtWidgets.QVBoxLayout()   
        self.VBox.addWidget(self.sLabel)     
        self.VBox.addWidget(self.slider)
        
        HBox1 = QtWidgets.QHBoxLayout()  
        # RBox = QtWidgets.QGridLayout()
        self.buttonGroup = QtWidgets.QButtonGroup()
        self.buttonGroup.addButton(self.radioButton1)
        self.buttonGroup.addButton(self.radioButton2)
        self.buttonGroup.addButton(self.radioButton3)
        HBox1.addWidget(self.radioButton1)
        HBox1.addWidget(self.radioButton2)
        HBox1.addWidget(self.radioButton3)
        # self.VBox.addLayout(RBox)
        HBox1.addWidget(self.loadButton) 
        HBox1.addWidget(self.plotButton)            
        HBox1.addWidget(self.saveButton)
        HBox1.addWidget(self.closeButton)
        self.VBox.addLayout(HBox1)

        HBox2 = QtWidgets.QHBoxLayout()  
        HBox2.addWidget(self.plotWidgetDark)
        HBox2.addWidget(self.plotWidgetLight)
        self.VBox.addLayout(HBox2)
        
        self.setLayout(self.VBox)
        self.setGeometry(100, 70, 1400, 700)  

        self.sliderWave = float(self.slider.value())

    def sliderMove(self):
        self.sliderWave = float(self.slider.value())
        self.sLabel.setText(f'{self.sliderWave}')            
        # print(self.sliderWave)          

    def radioClick(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.sensor = radioButton.text()
            print("Sensor is %s" % (self.sensor))        

    def plotButtonPressed(self):
        print("Plot pressed")  
        # print(self.sliderWave)  
        
        if not hasattr(self, 'root'):
            note = QtWidgets.QMessageBox()
            note.setText('You must load L1C file before plotting')
            note.exec_()
            return            

        ''' This needs to be a radio selection button, not a for loop '''
        # sensorTypes = ['ES','LT','LI']
        # for sensorType in sensorTypes:
        sensorType = self.sensor
        print(sensorType)
        darkData = None
        lightData = None

        # Extract Light & Dark datasets from the sensor group
        for gp in self.root.groups:
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
            radiometry2D = darkData.columns            

            # Conversion not set up for vectors, loop it                              
            dateTagDS = gp.getDataset('DATETAG')
            dateTags = dateTagDS.data["NONE"].tolist()
            timeTagDS = gp.getDataset('TIMETAG2')
            timeTags = timeTagDS.data["NONE"].tolist()
            dateTime=[]
            for i, dateTag in enumerate(dateTags):
                dt = Utilities.dateTagToDateTime(dateTag)     
                dateTime.append(Utilities.timeTag2ToDateTime(dt,timeTags[i]))

            # Same for Dark and Light... here taking from Dark
            waveBands = []
            waveBandStrings = []
            for key in radiometry2D.keys():
                waveBands.append(float(key))
                waveBandStrings.append(key)                
            self.waveBands = waveBands
            whr = Utilities.find_nearest(self.waveBands, self.sliderWave)
            self.waveBand = self.waveBands[whr]
            print(self.waveBand)

            radiometry1D = radiometry2D[f'{self.waveBand:03.2f}']
            
            # Update the slider
            self.sLabel = QtWidgets.QLabel(f'{self.waveBand}')
            self.slider.setMinimum(min(waveBands))
            self.slider.setMaximum(max(waveBands))
            # self.slider.setTickInterval(10)
            self.slider.setValue(self.sliderWave)

            self.deglitchAndPlot(self, radiometry1D, dateTime, sensorType,lightDark)

        if lightData is None:
            print("Error: No light data to deglitch")
        else:    
            print("Light data anomaly analysis") 
            lightDark = 'Light'       
            lightData.datasetToColumns()
            radiometry2D = lightData.columns
            radiometry1D = radiometry2D[str(self.waveBand)]
            print(self.waveBand)

            # Conversion not set up for vectors, loop it                              
            dateTagDS = gp.getDataset('DATETAG')
            dateTags = dateTagDS.data["NONE"].tolist()
            timeTagDS = gp.getDataset('TIMETAG2')
            timeTags = timeTagDS.data["NONE"].tolist()
            dateTime=[]
            for i, dateTag in enumerate(dateTags):
                dt = Utilities.dateTagToDateTime(dateTag)     
                dateTime.append(Utilities.timeTag2ToDateTime(dt,timeTags[i]))
            
            self.deglitchAndPlot(self, radiometry1D, dateTime, sensorType, lightDark)
        
        
    def saveButtonPressed(self):
        print("Save pressed")    
        # Steps in wavebands used for plots
        step = float(ConfigFile.settings["bL1dAnomalyStep"])

        outDir = MainConfig.settings["outDir"]
        # If default output path is used, choose the root HyperInSPACE path, and build on that
        if os.path.abspath(outDir) == os.path.join('./','Data'):
            outDir = './'
        
        if not os.path.exists(os.path.join(outDir,'Plots','L1C_Anoms')):
            os.makedirs(os.path.join(outDir,'Plots','L1C_Anoms'))    
        plotdir = os.path.join(outDir,'Plots','L1C_Anoms')
        fp = os.path.join(plotdir,self.fileName)

    def closeButtonPressed(self):
        print('Done')        
        self.close()      


    def loadL1Cfile(self):        
        inputDirectory = self.inputDirectory
        # Open L1C HDF5 file for Deglitching   
        inLevel = "L1C"   
        subInputDir = os.path.join(inputDirectory + '/' + inLevel + '/')
        if os.path.exists(subInputDir):
            inFilePath,_ = QtWidgets.QFileDialog.getOpenFileNames(self, "Open L1C HDF5 file for Deglitching", \
                subInputDir)
        else:
            inFilePath,_ = QtWidgets.QFileDialog.getOpenFileNames(self, "Open L1C HDF5 file for Deglitching", \
                inputDirectory)
        try:
            print(inFilePath[0])
            if not "hdf" in inFilePath[0] and not "HDF" in inFilePath[0]:
                msg = "This does not appear to be an HDF file."
                Utilities.errorWindow("File Error", msg)
                print(msg)            
                return
        except:
            print('No file returned')
            return    

        root = HDFRoot.readHDF5(inFilePath[0])
        if root.attributes["PROCESSING_LEVEL"] != "1c":
            msg = "This is not a Level 1C file."
            Utilities.errorWindow("File Error", msg)
            print(msg)            
            return

        self.fileName = os.path.basename(os.path.splitext(inFilePath[0])[0])  
        self.setWindowTitle(self.fileName)
        self.root = root

    @staticmethod
    def deglitchAndPlot(self, timeSeries, dateTime, sensorType,lightDark):
        # Radiometry at this point is 1D 'column' from the appropriate group/dataset/waveband
        #   in time (timeSeries)

        styles = {'font-size': '18px'}
        text_xlabel="Time Series"   
        if lightDark == 'Dark':
            
            ph =  self.phDark
            
            phAve = self.phTimeAveDark
            ph1st = self.ph1stDark
            ph2nd = self.ph2ndDark
            windowSize = self.windowDark
            sigma = self.sigmaDark
            text_ylabel=f'{sensorType} Darks {self.waveBand}'
            figTitle = f'Band: {self.waveBand} Window: {windowSize} Sigma: {sigma}'
            # self.plotWidgetDark.setWindowTitle(figTitle)            
            print(f'{figTitle} Dark')
            # self.plotWidgetDark.setWindowTitle(figTitle, **styles)
            self.plotWidgetDark.setLabel('left', text_ylabel,**styles)
            self.plotWidgetDark.setLabel('bottom', text_xlabel,**styles)
            self.plotWidgetDark.showGrid(x=True, y=True)
            self.plotWidgetDark.addLegend()    
        else:
            ph = self.phLight
            phAve = self.phTimeAveLight
            ph1st = self.ph1stLight
            ph2nd = self.ph2ndLight
            windowSize = self.windowLight
            windowSize = self.windowLight
            sigma = self.sigmaLight
            text_ylabel=f'{sensorType} Lights {self.waveBand}'
            figTitle = f'Band: {self.waveBand} Window: {windowSize} Sigma: {sigma}'
            print(f'{figTitle} Dark')
            # self.plotWidgetLight.setWindowTitle(figTitle, **styles)
            self.plotWidgetLight.setLabel('left', text_ylabel, **styles)
            self.plotWidgetLight.setLabel('bottom', text_xlabel, **styles)
            self.plotWidgetLight.showGrid(x=True, y=True)
            self.plotWidgetLight.addLegend()    
             

        avg = Utilities.movingAverage(timeSeries, windowSize).tolist()        
        # avg = Utilities.windowAverage(timeSeries, windowSize).mean().values.tolist()  
        residual = np.array(timeSeries) - np.array(avg)
        stdData = np.std(residual)

        ''' struggling with datetime x-axis plots. Use timeseries for now'''
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

        y_anomaly = np.array(timeSeries)[badIndex]
        x_anomaly = x[badIndex]
        y_anomaly2 = np.array(timeSeries)[badIndex2]
        x_anomaly2 = x[badIndex2]

        #Plot results                  
        try:     
            ph.setData(x, timeSeries, symbolPen='k', symbolBrush='w', \
                 symbol='o', name=sensorType, pen=None)
            phAve.setData(x[3:-3], avg[3:-3], name='rMean', \
                pen=pg.mkPen('g', width=3))
            ph1st.setData(x_anomaly, y_anomaly, symbolPen=pg.mkPen('r', width=3),\
                 symbol='x', name='1st pass')
            ph2nd.setData(x_anomaly2, y_anomaly2, symbolPen='r',\
                 symbol='+', name='2nd pass')
            
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)

