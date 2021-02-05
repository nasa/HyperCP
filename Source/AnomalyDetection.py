
import os
import sys
import shutil
import csv
import numpy as np
import pandas as pd
# from pandas.plotting import register_matplotlib_converters
import matplotlib.pyplot as plt
import matplotlib
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from Controller import Controller
# import Controller as CT
# from Controller import processL1d
# from ProcessL1d import ProcessL1d

from MainConfig import MainConfig
from ConfigFile import ConfigFile
# from AnomAnalFile import AnomAnalFile
from HDFRoot import HDFRoot
from Utilities import Utilities        

class AnomAnalWindow(QtWidgets.QDialog):
# class AnomAnalWindow(QtWidgets.QWidget):
    def __init__(self, inputDirectory, parent=None):
    # def __init__(self, inputDirectory):
        super().__init__(parent)
        self.inputDirectory = inputDirectory
        self.setModal(True)   

        # print(inputDirectory)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k') 

        self.minBand = ConfigFile.minDeglitchBand
        self.maxBand = ConfigFile.maxDeglitchBand        

        # If there is an AnomAnal file, open it for later access
        # to file-specific parameters
        anomAnalFileName,_ = ConfigFile.filename.split('.')
        self.anomAnalFileName = anomAnalFileName + '_anoms.csv'
        fp = os.path.join('Config',self.anomAnalFileName)
        if os.path.exists(fp):
            self.params = Utilities.readAnomAnalFile(fp)
        else:
            self.params = {}

        # Initially, set these to generic values in ConfigFile
        self.ESWindowDark = ConfigFile.settings['fL1dESWindowDark'] # int
        self.ESWindowLight = ConfigFile.settings['fL1dESWindowLight'] # int
        self.ESSigmaDark = ConfigFile.settings['fL1dESSigmaDark'] # float
        self.ESSigmaLight = ConfigFile.settings['fL1dESSigmaLight']# float
        self.LIWindowDark = ConfigFile.settings['fL1dLIWindowDark'] # int
        self.LIWindowLight = ConfigFile.settings['fL1dLIWindowLight'] # int
        self.LISigmaDark = ConfigFile.settings['fL1dLISigmaDark'] # float
        self.LISigmaLight = ConfigFile.settings['fL1dLISigmaLight']# float
        self.LTWindowDark = ConfigFile.settings['fL1dLTWindowDark'] # int
        self.LTWindowLight = ConfigFile.settings['fL1dLTWindowLight'] # int
        self.LTSigmaDark = ConfigFile.settings['fL1dLTSigmaDark'] # float
        self.LTSigmaLight = ConfigFile.settings['fL1dLTSigmaLight']# float
        

        # Set up the User Interface    
        self.initUI()

    def initUI(self):

        intValidator = QtGui.QIntValidator()
        doubleValidator = QtGui.QDoubleValidator() 

        # These will be adjusted on the slider once a file is loaded
        interval = 10
        self.waveBands = list(range(380, 780 +1, interval))
        # self.sLabel = QtWidgets.QLabel(f'{self.waveBands[0]}')
        self.sLabel = QtWidgets.QLabel('Use autoscaled slider to select the waveband:')
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

        AnomalyStepLabel = QtWidgets.QLabel("Waveband interval to save plots to disk: ", self)  
        self.AnomalyStepLineEdit = QtWidgets.QLineEdit(self)
        self.AnomalyStepLineEdit.setText(str(ConfigFile.settings["fL1dAnomalyStep"]))
        self.AnomalyStepLineEdit.setValidator(intValidator)     

        self.loadButton = QtWidgets.QPushButton('Load L1C', self, clicked=self.loadL1Cfile)

        self.updateButton = QtWidgets.QPushButton('***  Update  ***', self, clicked=self.updateButtonPressed)
        self.updateButton.setDefault(True)

        self.saveButton = QtWidgets.QPushButton('Save Sensor Params', self, clicked=self.saveButtonPressed)

        self.plotButton = QtWidgets.QPushButton('Save Anomaly Plots', self, clicked=self.plotButtonPressed)

        self.processButton = QtWidgets.QPushButton('Process to L1D', self, clicked=self.processButtonPressed)

        self.closeButton = QtWidgets.QPushButton('Close', self, clicked=self.closeButtonPressed)

        self.WindowDarkLabel = QtWidgets.QLabel("Window Size (odd)", self)
        self.WindowDarkLineEdit = QtWidgets.QLineEdit(self)
        self.WindowDarkLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}WindowDark']))
        self.WindowDarkLineEdit.setValidator(intValidator)
        self.WindowDarkLineEdit.returnPressed.connect(self.updateButton.click)
        # self.WindowDarkLineEdit.setValidator(oddValidator)

        self.SigmaDarkLabel = QtWidgets.QLabel("Sigma Factor", self)
        self.SigmaDarkLineEdit = QtWidgets.QLineEdit(self)
        self.SigmaDarkLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}SigmaDark']))
        self.SigmaDarkLineEdit.setValidator(doubleValidator)

        self.pLossDarkLabel = QtWidgets.QLabel('% Loss (all bands)', self)
        self.pLossDarkLineEdit = QtWidgets.QLineEdit(self)
        self.pLossDarkLineEdit.setText('0')

        self.WindowLightLabel = QtWidgets.QLabel("Window Size (odd)", self)
        self.WindowLightLineEdit = QtWidgets.QLineEdit(self)
        self.WindowLightLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}WindowLight']))
        self.WindowLightLineEdit.setValidator(intValidator)
        # self.WindowLightLineEdit.setValidator(oddValidator)

        self.SigmaLightLabel = QtWidgets.QLabel("Sigma Factor", self)
        self.SigmaLightLineEdit = QtWidgets.QLineEdit(self)
        self.SigmaLightLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}SigmaLight']))
        self.SigmaLightLineEdit.setValidator(doubleValidator)

        self.pLossLightLabel = QtWidgets.QLabel('% Loss (all bands)', self)
        self.pLossLightLineEdit = QtWidgets.QLineEdit(self)
        self.pLossLightLineEdit.setText('0')

        self.plotWidgetDark = pg.PlotWidget(self)            
        self.plotWidgetLight = pg.PlotWidget(self)     

        guideLabel = QtWidgets.QLabel(\
            'Left-click to pan. Right click to zoom. Hit "A" button on bottom left of plot to restore.')

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
        
        HBox2.addSpacing(135)
        HBox2.addWidget(self.updateButton)    
        HBox2.addStretch()        
        
        HBox2.addWidget(self.saveButton)
        HBox2.addWidget(AnomalyStepLabel)        
        HBox2.addWidget(self.AnomalyStepLineEdit)
        HBox2.addWidget(self.plotButton)
        HBox2.addWidget(self.processButton)
        HBox2.addWidget(self.closeButton)
        self.VBox.addLayout(HBox2)

        HBox3 = QtWidgets.QHBoxLayout()  
        HBox3.addWidget(self.WindowDarkLabel)
        HBox3.addWidget(self.WindowDarkLineEdit)
        HBox3.addWidget(self.SigmaDarkLabel)
        HBox3.addWidget(self.SigmaDarkLineEdit)
        # HBox3.addSpacing(20)
        HBox3.addWidget(self.pLossDarkLabel)
        HBox3.addWidget(self.pLossDarkLineEdit)

        HBox3.addWidget(self.WindowLightLabel)
        HBox3.addWidget(self.WindowLightLineEdit)
        HBox3.addWidget(self.SigmaLightLabel)
        HBox3.addWidget(self.SigmaLightLineEdit)
        HBox3.addWidget(self.pLossLightLabel)
        HBox3.addWidget(self.pLossLightLineEdit)

        self.VBox.addLayout(HBox3)

        HBox4 = QtWidgets.QHBoxLayout()  
        HBox4.addWidget(self.plotWidgetDark)
        HBox4.addWidget(self.plotWidgetLight)
        self.VBox.addLayout(HBox4)

        self.VBox.addWidget(guideLabel)
        
        self.setLayout(self.VBox)
        self.setGeometry(100, 70, 1400, 700)  

        self.sliderWave = float(self.slider.value())

        # Run this on first opening the GUI
        self.loadL1Cfile()
        self.updateButtonPressed()

    # def readAnomAnalFile(self, filePath):
    #     paramDict = {}
    #     with open(filePath, newline='') as csvfile:
    #         paramreader = csv.DictReader(csvfile)
    #         for row in paramreader:
                
    #             paramDict[row['filename']] = [int(row['ESWindowDark']), int(row['ESWindowLight']), \
    #                                 float(row['ESSigmaDark']), float(row['ESSigmaLight']),\
    #                                     int(row['LIWindowDark']), int(row['LIWindowLight']),
    #                                     float(row['LISigmaDark']), float(row['LISigmaLight']),
    #                                     int(row['LTWindowDark']), int(row['LTWindowLight']),
    #                                     float(row['LTSigmaDark']), float(row['LTSigmaLight']),]
    #     return paramDict

    def writeAnomAnalFile(self, filePath):
        header = ['filename','ESWindowDark','ESWindowLight','ESSigmaDark','ESSigmaLight',\
            'LIWindowDark','LIWindowLight','LISigmaDark','LISigmaLight',
            'LTWindowDark','LTWindowLight','LTSigmaDark','LTSigmaLight',]
        # fieldnames = params.keys()

        with open(filePath, 'w', newline='') as csvfile:
            paramwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            paramwriter.writerow(header)
            for key, values in self.params.items():
                paramwriter.writerow([key]+values)

    def sliderMove(self):
        self.sliderWave = float(self.slider.value())
        # ''' This fails to update the label '''
        # self.sLabel.setText(f'{self.sliderWave}')            
        # print(self.sliderWave)          

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

        # If a parameterization has been saved in the AnomAnalFile, set the properties in the local object
        # for all sensors
        if self.fileName in self.params.keys():
            ref = 0
            for sensor in ['ES','LI','LT']:
                setattr(self,f'{sensor}WindowDark', self.params[self.fileName][ref+0] )
                setattr(self,f'{sensor}WindowLight', self.params[self.fileName][ref+1] )
                setattr(self,f'{sensor}SigmaDark', self.params[self.fileName][ref+2] )
                setattr(self,f'{sensor}SigmaLight', self.params[self.fileName][ref+3] )  
                ref += 4
        
        # Set the GUI parameters for the current sensor from the local object
        self.WindowDarkLineEdit.setText(str(getattr(self,f'{self.sensor}WindowDark')))
        self.WindowLightLineEdit.setText(str(getattr(self,f'{self.sensor}WindowLight')))
        self.SigmaDarkLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaDark')))
        self.SigmaLightLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaLight')))        

    def radioClick(self):
        # Before changing to the new sensor, locally save the parameters 
        # from the last sensor in case it was changed.

        # Test the window sizes
        if int(self.WindowDarkLineEdit.text())%2 == 0 or int(self.WindowLightLineEdit.text())%2 ==0:
            alert = QtWidgets.QMessageBox()
            alert.setText('Deglitching windows must be odd integers.')
            alert.exec_()
            return
                
        # Set parameters in the local object
        setattr(self,f'{self.sensor}WindowDark', int(self.WindowDarkLineEdit.text()) )
        setattr(self,f'{self.sensor}WindowLight', int(self.WindowLightLineEdit.text()) )
        setattr(self,f'{self.sensor}SigmaDark', float(self.SigmaDarkLineEdit.text()) )
        setattr(self,f'{self.sensor}SigmaLight', float(self.SigmaLightLineEdit.text()) )  

        radioButton = self.sender()
        if radioButton.isChecked():
            self.sensor = radioButton.text()
            print("Sensor is %s" % (self.sensor))        
            # Now update the LineEdits with saved values in the local object
            self.WindowDarkLineEdit.setText(str(getattr(self,f'{self.sensor}WindowDark')))
            self.WindowLightLineEdit.setText(str(getattr(self,f'{self.sensor}WindowLight')))
            self.SigmaDarkLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaDark')))
            self.SigmaLightLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaLight')))

        self.updateButtonPressed()
            

    def updateButtonPressed(self):
        print("Update pressed")  
        # print(self.sliderWave) 

        sensorType = self.sensor
        print(sensorType)
        
        # Test for root
        if not hasattr(self, 'root'):
            note = QtWidgets.QMessageBox()
            note.setText('You must load L1C file before plotting')
            note.exec_()
            return   

        # Test the window sizes
        if int(self.WindowDarkLineEdit.text())%2 == 0 or int(self.WindowLightLineEdit.text())%2 ==0:
            alert = QtWidgets.QMessageBox()
            alert.setText('Deglitching windows must be odd integers.')
            alert.exec_()
            return
                
        # Set parameters in the local object from the GUI
        setattr(self,f'{self.sensor}WindowDark', int(self.WindowDarkLineEdit.text()) )
        setattr(self,f'{self.sensor}WindowLight', int(self.WindowLightLineEdit.text()) )
        setattr(self,f'{self.sensor}SigmaDark', float(self.SigmaDarkLineEdit.text()) )
        setattr(self,f'{self.sensor}SigmaLight', float(self.SigmaLightLineEdit.text()) )        
                
        darkData = None
        lightData = None
        # Extract Light & Dark datasets from the sensor group
        for gp in self.root.groups:
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                darkData = gp.getDataset(sensorType)
                darkDateTime = self.getDateTime(gp)
            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
                lightDateTime = self.getDateTime(gp)            

        # Deglitch and plot Dark from selected band
        if darkData is None:
            print("Error: No dark data to deglitch")
        else:
            print("Dark data anomaly analysis") 
            lightDark = 'Dark'       
            darkData.datasetToColumns()
            dark2D = darkData.columns            

            # Same for Dark and Light... here taking from Dark
            waveBands = []
            waveBandStrings = []
            for key in dark2D.keys():
                waveBands.append(float(key))
                waveBandStrings.append(key)                
            self.waveBands = waveBands
            whr = Utilities.find_nearest(self.waveBands, self.sliderWave)
            self.waveBand = self.waveBands[whr]
            # print(self.waveBand)

            radiometry1D = dark2D[f'{self.waveBand:03.2f}']                        

            self.realTimePlot(self, radiometry1D, darkDateTime, sensorType,lightDark)

        # Update the slider
        # ''' NOT WORKING '''
        # self.sLabel = QtWidgets.QLabel(f'{self.waveBand}')
        self.slider.setMinimum(min(waveBands))
        self.slider.setMaximum(max(waveBands))
        # self.slider.setTickInterval(10)
        self.slider.setValue(self.sliderWave)

        # Deglitch and plot Light from selected band
        if lightData is None:
            print("Error: No light data to deglitch")
        else:    
            print("Light data anomaly analysis") 
            lightDark = 'Light'       
            lightData.datasetToColumns()
            light2D = lightData.columns
            radiometry1D = light2D[str(self.waveBand)]
            # print(self.waveBand)      
            
            self.realTimePlot(self, radiometry1D, lightDateTime, sensorType, lightDark)

        # Now run the deglitcher for all wavebands light and dark to calculate the % loss to the data from this sensor
        # Darks
        columns = darkData.columns
        globalBadIndex = []
        for dark1D in columns.items():
            band = float(dark1D[0])
            if band > self.minBand and band < self.maxBand:
                radiometry1D = dark1D[1]
                windowSize = int(self.WindowDarkLineEdit.text())
                sigma = float(self.SigmaDarkLineEdit.text())
                lightDark = 'Dark'
                badIndex, badIndex2 = self.deglitchBand(radiometry1D, windowSize, sigma, lightDark) 
                globalBadIndex.append(badIndex)
                globalBadIndex.append(badIndex2)

        # Collapse the badIndexes from all wavebands into one timeseries 
        # Must be done seperately for dark and light as they are different length time series
        # Convert to an array and test along the columns (i.e. each timestamp)
        gIndex = np.any(np.array(globalBadIndex), 0)
        percentLoss = 100*(sum(gIndex)/len(gIndex))                    
        pLabel = f'Data reduced by {sum(gIndex)} ({percentLoss:.1f}%)'
        print(pLabel)
        # self.plotWidgetLight.TextItem(pLabel,anchor=(0.2,0.2))
        self.pLossDarkLineEdit.setText(f'{percentLoss:.1f}')
        
        # Lights
        columns = lightData.columns    
        globalBadIndex = []
        for light1D in columns.items():
            band = float(light1D[0])
            if band > self.minBand and band < self.maxBand:
                radiometry1D = light1D[1]
                windowSize = int(self.WindowLightLineEdit.text())
                sigma = float(self.SigmaLightLineEdit.text())
                lightDark = 'Light'
                badIndex, badIndex2 = self.deglitchBand(radiometry1D, windowSize, sigma, lightDark) 
                globalBadIndex.append(badIndex)
                globalBadIndex.append(badIndex2)

        # Collapse the badIndexes from all wavebands into one timeseries
        # Convert to an array and test along the columns (i.e. each timestamp)
        gIndex = np.any(np.array(globalBadIndex), 0)
        percentLoss = 100*(sum(gIndex)/len(gIndex))                    
        pLabel = f'Data reduced by {sum(gIndex)} ({percentLoss:.1f}%)'
        print(pLabel)
        self.pLossLightLineEdit.setText(f'{percentLoss:.1f}')

        
    def saveButtonPressed(self):
        # Saves local parameterizations to the ConfigFile.settings
        # Triggered only when button pressed
        print("Save params pressed")         

        params = []
        for sensor in ["ES","LI","LT"]:                
            ConfigFile.settings[f'fL1d{sensor}WindowDark'] = getattr(self,f'{sensor}WindowDark')
            ConfigFile.settings[f'fL1d{sensor}WindowLight'] = getattr(self,f'{sensor}WindowLight')
            ConfigFile.settings[f'fL1d{sensor}SigmaDark'] = getattr(self,f'{sensor}SigmaDark')
            ConfigFile.settings[f'fL1d{sensor}SigmaLight'] = getattr(self,f'{sensor}SigmaLight')

            params.append(getattr(self,f'{sensor}WindowDark'))
            params.append(getattr(self,f'{sensor}WindowLight'))
            params.append(getattr(self,f'{sensor}SigmaDark'))
            params.append(getattr(self,f'{sensor}SigmaLight'))

        self.params[self.fileName] = params

        # Steps in wavebands used for plots
        ConfigFile.settings["fL1dAnomalyStep"] = int(self.AnomalyStepLineEdit.text())

        # Save file-specific parameters to CSV file
        fp = os.path.join('Config',self.anomAnalFileName)
        self.writeAnomAnalFile(fp)

    def plotButtonPressed(self):
        print("Save plots pressed")    
        # Steps in wavebands used for plots
        step = float(ConfigFile.settings["fL1dAnomalyStep"])     

        outDir = MainConfig.settings["outDir"]
        # If default output path is used, choose the root HyperInSPACE path, and build on that
        if os.path.abspath(outDir) == os.path.join('./','Data'):
            outDir = './'
        
        if not os.path.exists(os.path.join(outDir,'Plots','L1C_Anoms')):
            os.makedirs(os.path.join(outDir,'Plots','L1C_Anoms'))    
        plotdir = os.path.join(outDir,'Plots','L1C_Anoms')
        # fp = os.path.join(plotdir,self.fileName)

        sensorTypes = ["ES","LT","LI"]

        for sensorType in sensorTypes:
            print(sensorType)
            darkData = None
            lightData = None

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
                columns = darkData.columns
                windowSize = getattr(self,f'{sensorType}WindowDark')
                sigma = getattr(self,f'{sensorType}SigmaDark')

                index = 0
                for timeSeries in columns.items():
                    if index % step == 0:    
                        radiometry1D = timeSeries[1]
                        badIndex, badIndex2 = self.deglitchBand(radiometry1D, windowSize, sigma, lightDark)                
                        self.savePlots(self.fileName,plotdir,timeSeries,sensorType,lightDark,windowSize,sigma,badIndex,badIndex2)
                    index +=1

            if lightData is None:
                print("Error: No light data to deglitch")
            else:    
                print("Light data anomaly analysis") 
                lightDark = 'Light'       
                lightData.datasetToColumns()
                columns = lightData.columns
                windowSize = getattr(self,f'{sensorType}WindowLight')
                sigma = getattr(self,f'{sensorType}SigmaLight')

                index = 0        
                for timeSeries in columns.items():
                    if index % step == 0:           
                        radiometry1D = timeSeries[1]
                        badIndex, badIndex2 = self.deglitchBand(radiometry1D, windowSize, sigma, lightDark)              
                        self.savePlots(self.fileName,plotdir,timeSeries,sensorType,lightDark,windowSize,sigma,badIndex,badIndex2)
                    index += 1
                print('Complete')

    def processButtonPressed(self):
        # Run L1D processing for this file

        inFilePath = os.path.join(self.inputDirectory, 'L1C', self.fileName+'.hdf')
        fileBaseName = self.fileName.split('L1C')
        outFilePath = os.path.join(self.inputDirectory, 'L1D', fileBaseName[0]+'L1D.hdf')

        # self.processL1d(inFilePath, outFilePath)
        Controller.processL1d(inFilePath, outFilePath)
        print('Process L1D complete')


    def closeButtonPressed(self):
        print('Done')        
        self.close()      


    @staticmethod
    def realTimePlot(self, radiometry1D, dateTime, sensorType,lightDark):        
        # Radiometry at this point is 1D 'column' from the appropriate group/dataset/waveband
        #   in time (radiometry1D)

        ''' Still unable to plot against a datetime '''
        # # For the sake of MacOS, need to hack the datetimes into panda dataframes for plotting
        # dfx = pd.DataFrame(data=dateTime, index=list(range(0,len(dateTime))), columns=['x'])
        # # *** HACK: CONVERT datetime column to string and back again - who knows why this works? ***
        # dfx['x'] = pd.to_datetime(dfx['x'].astype(str))
        # register_matplotlib_converters()

        styles = {'font-size': '18px'}
        text_xlabel="Time Series"   

        # Initialize the plot
        if lightDark == 'Dark':            
            ph =  self.phDark            
            phAve = self.phTimeAveDark
            ph1st = self.ph1stDark
            ph2nd = self.ph2ndDark
            windowSize = getattr(self,f'{sensorType}WindowDark')
            sigma = getattr(self,f'{sensorType}SigmaDark')
            text_ylabel=f'{sensorType} Darks {self.waveBand}'
            figTitle = f'Band: {self.waveBand} Window: {windowSize} Sigma: {sigma}'
            # self.plotWidgetDark.setWindowTitle(figTitle)            
            print(f'{figTitle} Dark')
            # self.plotWidgetDark.setWindowTitle(figTitle, **styles)
            self.plotWidgetDark.setLabel('left', text_ylabel,**styles)
            self.plotWidgetDark.setLabel('bottom', text_xlabel,**styles)
            self.plotWidgetDark.showGrid(x=True, y=True)
            ''' legend not working '''
            self.plotWidgetDark.addLegend()    
        else:
            ph = self.phLight
            phAve = self.phTimeAveLight
            ph1st = self.ph1stLight
            ph2nd = self.ph2ndLight
            windowSize = getattr(self,f'{sensorType}WindowLight')
            sigma = getattr(self,f'{sensorType}SigmaLight')
            text_ylabel=f'{sensorType} Lights {self.waveBand}'
            figTitle = f'Band: {self.waveBand} Window: {windowSize} Sigma: {sigma}'
            print(f'{figTitle} Dark')
            # self.plotWidgetLight.setWindowTitle(figTitle, **styles)
            self.plotWidgetLight.setLabel('left', text_ylabel, **styles)
            self.plotWidgetLight.setLabel('bottom', text_xlabel, **styles)
            self.plotWidgetLight.showGrid(x=True, y=True)
            self.plotWidgetLight.addLegend()    
             
        badIndex, badIndex2 = self.deglitchBand(radiometry1D, windowSize, sigma, lightDark)        
        avg = Utilities.movingAverage(radiometry1D, windowSize).tolist() 

        ''' Use numeric series (x) for now in place of datetime '''
        x = np.arange(0,len(radiometry1D),1)    

        y_anomaly = np.array(radiometry1D)[badIndex]
        x_anomaly = x[badIndex]
        # x_anomaly = dfx['x'][badIndex]
        y_anomaly2 = np.array(radiometry1D)[badIndex2]
        x_anomaly2 = x[badIndex2]
        # x_anomaly2 = dfx['x'][badIndex2]

        #Plot results                  
        try:
            # ph.setData(dfx['x'], radiometry1D, symbolPen='k', symbolBrush='w', \
            ph.setData(x, radiometry1D, symbolPen='k', symbolBrush='w', \
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

    @staticmethod
    def deglitchBand(radiometry1D, windowSize, sigma, lightDark):    
        # For a given sensor in a given band (1D), calculate the first and second outliers on the light and dark          
        if lightDark == 'Dark':
            avg = Utilities.movingAverage(radiometry1D, windowSize).tolist()        
            # avg = Utilities.windowAverage(radiometry1D, windowSize).mean().values.tolist()  
            residual = np.array(radiometry1D) - np.array(avg)
            stdData = np.std(residual)
            # x = np.arange(0,len(radiometry1D),1)  

            # First pass
            badIndex = Utilities.darkConvolution(radiometry1D,avg,stdData,sigma)  

            # Second pass
            radiometry1D2 = np.array(radiometry1D[:])
            radiometry1D2[badIndex] = np.nan
            radiometry1D2 = radiometry1D2.tolist()
            avg2 = Utilities.movingAverage(radiometry1D2, windowSize).tolist()               
            residual = np.array(radiometry1D2) - np.array(avg2)
            stdData = np.nanstd(residual)        

            badIndex2 = Utilities.darkConvolution(radiometry1D2,avg2,stdData,sigma) 

        else:
            avg = Utilities.movingAverage(radiometry1D, windowSize).tolist()        
            # avg = Utilities.windowAverage(radiometry1D, windowSize).mean().values.tolist()  
            residual = np.array(radiometry1D) - np.array(avg)
            stdData = np.std(residual)
            # x = np.arange(0,len(radiometry1D),1)     

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
            badIndex = Utilities.lightConvolution(radiometry1D,avg,rolling_std,sigma)

            # Second pass
            radiometry1D2 = np.array(radiometry1D[:])
            radiometry1D2[badIndex] = np.nan
            radiometry1D2 = radiometry1D2.tolist()
            avg2 = Utilities.movingAverage(radiometry1D2, windowSize).tolist()        
            # avg2 = Utilities.windowAverage(radiometry1D2, windowSize).mean.values.tolist()        
            residual2 = np.array(radiometry1D2) - np.array(avg2)        
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

            badIndex2 = Utilities.lightConvolution(radiometry1D2,avg2,rolling_std2,sigma)
            # print(badIndex2)       

        return badIndex, badIndex2

    @staticmethod
    def savePlots(fileName,plotdir,timeSeries,sensorType,lightDark,windowSize,sigma,badIndex,badIndex2):#,\
        text_xlabel="Series"
        text_ylabel="Radiometry"
        

        #Plot results  
        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16}   
        
        waveBand = timeSeries[0]
        radiometry1D = timeSeries[1]
        x = np.arange(0,len(radiometry1D),1)  
        avg = Utilities.movingAverage(radiometry1D, windowSize).tolist() 

        try:     
            plt.figure(figsize=(15, 8))
            
            # y_av = moving_average(radiometry1D, window_size)
            plt.plot(x[3:-3], avg[3:-3], color='green')
            y_anomaly = np.array(radiometry1D)[badIndex]
            x_anomaly = x[badIndex]
            y_anomaly2 = np.array(radiometry1D)[badIndex2]
            x_anomaly2 = x[badIndex2]
            plt.plot(x_anomaly, y_anomaly, "rs", markersize=12)
            plt.plot(x_anomaly2, y_anomaly2, "b*", markersize=12)
            plt.plot(x, radiometry1D, "k.")

            plt.xlabel(text_xlabel, fontdict=font)
            plt.ylabel(text_ylabel, fontdict=font)   
            plt.title('WindowSize = ' + str(windowSize) + ' Sigma Factor = ' + str(sigma), fontdict=font) 

            # plotName = (plotdir + fileName + '_W' + str(windowSize) + 'S' + str(sigma) + '_' \
            #     + sensorType + lightDark + '_' + k[0] + '.png')
            fp = os.path.join(plotdir,fileName)
            plotName = f'{fp}_W{windowSize}S{sigma}_{sensorType}{lightDark}_{waveBand}.png'

            print(plotName)
            plt.savefig(plotName)
            plt.close()    
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)


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
