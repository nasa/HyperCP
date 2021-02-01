
import os
import sys
import shutil
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
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

        self.ESwindowDark = ConfigFile.settings['fL1dESWindowDark'] # int
        self.ESwindowLight = ConfigFile.settings['fL1dESWindowLight'] # int
        self.ESsigmaDark = ConfigFile.settings['fL1dESSigmaDark'] # float
        self.ESsigmaLight = ConfigFile.settings['fL1dESSigmaLight']# float
        self.LIwindowDark = ConfigFile.settings['fL1dLIWindowDark'] # int
        self.LIwindowLight = ConfigFile.settings['fL1dLIWindowLight'] # int
        self.LIsigmaDark = ConfigFile.settings['fL1dLISigmaDark'] # float
        self.LIsigmaLight = ConfigFile.settings['fL1dLISigmaLight']# float
        self.LTwindowDark = ConfigFile.settings['fL1dLTWindowDark'] # int
        self.LTwindowLight = ConfigFile.settings['fL1dLTWindowLight'] # int
        self.LTsigmaDark = ConfigFile.settings['fL1dLTSigmaDark'] # float
        self.LTsigmaLight = ConfigFile.settings['fL1dLTSigmaLight']# float
        

        # Set up the User Interface    
        self.initUI()

    def initUI(self):

        intValidator = QtGui.QIntValidator()
        doubleValidator = QtGui.QDoubleValidator() 

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

        l1dAnomalyStepLabel = QtWidgets.QLabel("   Waveband interval to plot (integer): ", self)  
        self.l1dAnomalyStepLineEdit = QtWidgets.QLineEdit(self)
        self.l1dAnomalyStepLineEdit.setText(str(ConfigFile.settings["fL1dAnomalyStep"]))
        self.l1dAnomalyStepLineEdit.setValidator(intValidator)     

        self.loadButton = QtWidgets.QPushButton('Load L1C', self, clicked=self.loadL1Cfile)

        self.plotButton = QtWidgets.QPushButton('*** Update ***', self, clicked=self.plotButtonPressed)

        self.saveButton = QtWidgets.QPushButton('Save', self, clicked=self.saveButtonPressed)

        self.closeButton = QtWidgets.QPushButton('Close', self, clicked=self.closeButtonPressed)

        self.l1dWindowDarkLabel = QtWidgets.QLabel("Window Size (odd)", self)
        self.l1dWindowDarkLineEdit = QtWidgets.QLineEdit(self)
        self.l1dWindowDarkLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}WindowDark']))
        self.l1dWindowDarkLineEdit.setValidator(intValidator)
        # self.l1dWindowDarkLineEdit.setValidator(oddValidator)

        self.l1dSigmaDarkLabel = QtWidgets.QLabel("Sigma Factor", self)
        self.l1dSigmaDarkLineEdit = QtWidgets.QLineEdit(self)
        self.l1dSigmaDarkLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}SigmaDark']))
        self.l1dSigmaDarkLineEdit.setValidator(doubleValidator)

        self.l1dWindowLightLabel = QtWidgets.QLabel("Window Size (odd)", self)
        self.l1dWindowLightLineEdit = QtWidgets.QLineEdit(self)
        self.l1dWindowLightLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}WindowLight']))
        self.l1dWindowLightLineEdit.setValidator(intValidator)
        # self.l1dWindowLightLineEdit.setValidator(oddValidator)

        self.l1dSigmaLightLabel = QtWidgets.QLabel("Sigma Factor", self)
        self.l1dSigmaLightLineEdit = QtWidgets.QLineEdit(self)
        self.l1dSigmaLightLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}SigmaLight']))
        self.l1dSigmaLightLineEdit.setValidator(doubleValidator)

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
        HBox1 = QtWidgets.QHBoxLayout()     
        HBox1.addWidget(self.slider)
        self.VBox.addLayout(HBox1)
        
        HBox2 = QtWidgets.QHBoxLayout()  
        HBox2.addWidget(self.loadButton) 
        # RBox = QtWidgets.QGridLayout()
        self.buttonGroup = QtWidgets.QButtonGroup()
        self.buttonGroup.addButton(self.radioButton1)
        self.buttonGroup.addButton(self.radioButton2)
        self.buttonGroup.addButton(self.radioButton3)
        HBox2.addWidget(self.radioButton1)
        HBox2.addWidget(self.radioButton2)
        HBox2.addWidget(self.radioButton3)
        # self.VBox.addLayout(RBox)

        # stepHBox = QtWidgets.QHBoxLayout()
        HBox2.addWidget(l1dAnomalyStepLabel)
        HBox2.addWidget(self.l1dAnomalyStepLineEdit)
        # VBox2.addLayout(stepHBox)
        
        HBox2.addWidget(self.plotButton)    
        HBox2.addStretch()        
        HBox2.addWidget(self.saveButton)
        HBox2.addWidget(self.closeButton)
        self.VBox.addLayout(HBox2)

        HBox3 = QtWidgets.QHBoxLayout()  
        HBox3.addWidget(self.l1dWindowDarkLabel)
        HBox3.addWidget(self.l1dWindowDarkLineEdit)
        HBox3.addWidget(self.l1dSigmaDarkLabel)
        HBox3.addWidget(self.l1dSigmaDarkLineEdit)
        HBox3.addSpacing(20)
        HBox3.addWidget(self.l1dWindowLightLabel)
        HBox3.addWidget(self.l1dWindowLightLineEdit)
        HBox3.addWidget(self.l1dSigmaLightLabel)
        HBox3.addWidget(self.l1dSigmaLightLineEdit)
        self.VBox.addLayout(HBox3)

        HBox4 = QtWidgets.QHBoxLayout()  
        HBox4.addWidget(self.plotWidgetDark)
        HBox4.addWidget(self.plotWidgetLight)
        self.VBox.addLayout(HBox4)
        
        self.setLayout(self.VBox)
        self.setGeometry(100, 70, 1400, 700)  

        self.sliderWave = float(self.slider.value())

    def sliderMove(self):
        self.sliderWave = float(self.slider.value())
        ''' This fails to update the label '''
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

        if int(self.l1dWindowDarkLineEdit.text())%2 == 0 or int(self.l1dWindowLightLineEdit.text())%2 ==0:
            alert = QtWidgets.QMessageBox()
            alert.setText('Deglitching windows must be odd integers.')
            alert.exec_()
            return
        
        # ConfigFile.settings[f'fL1d{self.sensor}WindowDark'] = int(self.l1dWindowDarkLineEdit.text())
        # ConfigFile.settings[f'fL1d{self.sensor}WindowLight'] = int(self.l1dWindowLightLineEdit.text())
        # ConfigFile.settings[f'fL1d{self.sensor}SigmaDark'] = float(self.l1dSigmaDarkLineEdit.text())
        # ConfigFile.settings[f'fL1d{self.sensor}SigmaLight'] = float(self.l1dSigmaLightLineEdit.text())        

        ConfigFile.settings["fL1dAnomalyStep"] = int(self.l1dAnomalyStepLineEdit.text())
        
        if not hasattr(self, 'root'):
            note = QtWidgets.QMessageBox()
            note.setText('You must load L1C file before plotting')
            note.exec_()
            return            

        
        sensorType = self.sensor
        print(sensorType)
        darkData = None
        lightData = None

        # Extract Light & Dark datasets from the sensor group
        for gp in self.root.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                darkData = gp.getDataset(sensorType)
                dateTagDS = gp.getDataset('DATETAG')
                dateTags = dateTagDS.data["NONE"].tolist()
                timeTagDS = gp.getDataset('TIMETAG2')
                timeTags = timeTagDS.data["NONE"].tolist()
                # Conversion not set up for vectors, loop it                                          
                darkDateTime=[]
                for i, dateTag in enumerate(dateTags):
                    dt = Utilities.dateTagToDateTime(dateTag)     
                    darkDateTime.append(Utilities.timeTag2ToDateTime(dt,timeTags[i]))
            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
                dateTagDS = gp.getDataset('DATETAG')
                dateTags = dateTagDS.data["NONE"].tolist()
                timeTagDS = gp.getDataset('TIMETAG2')
                timeTags = timeTagDS.data["NONE"].tolist()
                # Conversion not set up for vectors, loop it                                          
                lightDateTime=[]
                for i, dateTag in enumerate(dateTags):
                    dt = Utilities.dateTagToDateTime(dateTag)     
                    lightDateTime.append(Utilities.timeTag2ToDateTime(dt,timeTags[i]))
            
        if darkData is None:
            print("Error: No dark data to deglitch")
        else:
            print("Dark data anomaly analysis") 
            lightDark = 'Dark'       
            darkData.datasetToColumns()
            radiometry2D = darkData.columns            

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

            self.realTimePlot(self, radiometry1D, darkDateTime, sensorType,lightDark)

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
            # dateTagDS = gp.getDataset('DATETAG')
            # dateTags = dateTagDS.data["NONE"].tolist()
            # timeTagDS = gp.getDataset('TIMETAG2')
            # timeTags = timeTagDS.data["NONE"].tolist()
            # dateTime=[]
            # for i, dateTag in enumerate(dateTags):
            #     dt = Utilities.dateTagToDateTime(dateTag)     
            #     dateTime.append(Utilities.timeTag2ToDateTime(dt,timeTags[i]))
            
            self.realTimePlot(self, radiometry1D, lightDateTime, sensorType, lightDark)
        
        
    def saveButtonPressed(self):
        print("Save pressed")    
        # Steps in wavebands used for plots
        step = float(ConfigFile.settings["bL1dAnomalyStep"])

        if int(self.l1dWindowDarkLineEdit.text())%2 == 0 or int(self.l1dWindowLightLineEdit.text())%2 ==0:
            alert = QtWidgets.QMessageBox()
            alert.setText('Deglitching windows must be odd integers.')
            alert.exec_()
            return
        
        ConfigFile.settings[f'fL1d{self.sensor}WindowDark'] = int(self.l1dWindowDarkLineEdit.text())
        ConfigFile.settings[f'fL1d{self.sensor}WindowLight'] = int(self.l1dWindowLightLineEdit.text())
        ConfigFile.settings[f'fL1d{self.sensor}SigmaDark'] = float(self.l1dSigmaDarkLineEdit.text())
        ConfigFile.settings[f'fL1d{self.sensor}SigmaLight'] = float(self.l1dSigmaLightLineEdit.text())

        outDir = MainConfig.settings["outDir"]
        # If default output path is used, choose the root HyperInSPACE path, and build on that
        if os.path.abspath(outDir) == os.path.join('./','Data'):
            outDir = './'
        
        if not os.path.exists(os.path.join(outDir,'Plots','L1C_Anoms')):
            os.makedirs(os.path.join(outDir,'Plots','L1C_Anoms'))    
        plotdir = os.path.join(outDir,'Plots','L1C_Anoms')
        fp = os.path.join(plotdir,self.fileName)

        sensorTypes = ["ES","LT","LI"]

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

                ''' This should include the time stamp instead of just an index to
                plot against below.'''

                
                index = 0
                for k in columns.items():
                    if index % step == 0:                    
                        deglitchAndPlot(fileName,plotdir,k,sensorType,lightDark,windowSizeDark,sigmaDark,\
                            text_ylabel=sensorType + " Darks " + k[0])
                    index +=1

            if lightData is None:
                print("Error: No light data to deglitch")
            else:    
                print("Light data anomaly analysis") 
                lightDark = 'Light'       
                lightData.datasetToColumns()
                columns = lightData.columns

                # step = 20
                index = 0        
                for k in columns.items():
                    if index % step == 0:                    
                        # print('Window: ' + str(windowSizeLight) + ' Sigma: ' + str(sigmaLight))
                        deglitchAndPlot(fileName,plotdir,k,sensorType,lightDark,windowSizeLight,sigmaLight,\
                            text_ylabel=sensorType + " Lights " + k[0])
                    index += 1
                print('Complete')


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

    def deglitchAndPlot(fileName,plotdir,k,sensorType,lightDark,windowSize,sigma,\
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
        try:     
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

            # plotName = (plotdir + fileName + '_W' + str(windowSize) + 'S' + str(sigma) + '_' \
            #     + sensorType + lightDark + '_' + k[0] + '.png')
            fp = os.path.join(plotdir,fileName)
            plotName = f'{fp}_W{windowSize}S{sigma}_{sensorType}{lightDark}_{k[0]}.png'

            print(plotName)
            plt.savefig(plotName)
            plt.close()    
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)


    @staticmethod
    def realTimePlot(self, timeSeries, dateTime, sensorType,lightDark):
        # Radiometry at this point is 1D 'column' from the appropriate group/dataset/waveband
        #   in time (timeSeries)

        # For the sake of MacOS, need to hack the datetimes into panda dataframes for plotting
        dfx = pd.DataFrame(data=dateTime, index=list(range(0,len(dateTime))), columns=['x'])
        # *** HACK: CONVERT datetime column to string and back again - who knows why this works? ***
        dfx['x'] = pd.to_datetime(dfx['x'].astype(str))
        register_matplotlib_converters()

        styles = {'font-size': '18px'}
        text_xlabel="Time Series"   
        if lightDark == 'Dark':
            
            ph =  self.phDark
            
            phAve = self.phTimeAveDark
            ph1st = self.ph1stDark
            ph2nd = self.ph2ndDark
            windowSize = getattr(self,f'{sensorType}windowDark')
            sigma = getattr(self,f'{sensorType}sigmaDark')
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
            windowSize = getattr(self,f'{sensorType}windowLight')
            sigma = getattr(self,f'{sensorType}sigmaLight')
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

        # Pyqtgraph also not working with Timestamp...
        y_anomaly = np.array(timeSeries)[badIndex]
        x_anomaly = x[badIndex]
        # x_anomaly = dfx['x'][badIndex]
        y_anomaly2 = np.array(timeSeries)[badIndex2]
        x_anomaly2 = x[badIndex2]
        # x_anomaly2 = dfx['x'][badIndex2]

        #Plot results                  
        try:
            # ph.setData(dfx['x'], timeSeries, symbolPen='k', symbolBrush='w', \
            ph.setData(x, timeSeries, symbolPen='k', symbolBrush='w', \
                symbol='o', name=sensorType, pen=None)            
            # phAve.setData(dfx['x'][3:-3], avg[3:-3], name='rMean', \
            phAve.setData(x[3:-3], avg[3:-3], name='rMean', \
                pen=pg.mkPen('g', width=3))
            ph1st.setData(x_anomaly, y_anomaly, symbolPen=pg.mkPen('r', width=3),\
                symbol='x', name='1st pass')
            ph2nd.setData(x_anomaly2, y_anomaly2, symbolPen='r',\
                symbol='+', name='2nd pass')
            
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)

