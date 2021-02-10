
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
        for sensor in ["ES","LI","LT"]:                
            setattr(self,f'{sensor}WindowDark', ConfigFile.settings[f'fL1d{sensor}WindowDark'])            
            setattr(self,f'{sensor}WindowLight', ConfigFile.settings[f'fL1d{sensor}WindowLight'] )
            setattr(self,f'{sensor}SigmaDark', ConfigFile.settings[f'fL1d{sensor}SigmaDark'] )
            setattr(self,f'{sensor}SigmaLight', ConfigFile.settings[f'fL1d{sensor}SigmaLight'] )
            setattr(self,f'{sensor}MinDark', ConfigFile.settings[f'fL1d{sensor}MinDark'] )
            setattr(self,f'{sensor}MaxDark', ConfigFile.settings[f'fL1d{sensor}MaxDark'] )
            setattr(self,f'{sensor}MinMaxBandDark', ConfigFile.settings[f'fL1d{sensor}MinMaxBandDark'] )
            setattr(self,f'{sensor}MinLight', ConfigFile.settings[f'fL1d{sensor}MinLight'] )
            setattr(self,f'{sensor}MaxLight', ConfigFile.settings[f'fL1d{sensor}MaxLight'] )  
            setattr(self,f'{sensor}MinMaxBandLight', ConfigFile.settings[f'fL1d{sensor}MinMaxBandLight'] )        
        
        setattr(self,'Threshold', ConfigFile.settings['bL1dThreshold'] )

        # Set up the User Interface    
        self.initUI()

    def initUI(self):

        intValidator = QtGui.QIntValidator()
        doubleValidator = QtGui.QDoubleValidator() 

        # These will be adjusted on the slider once a file is loaded
        interval = 10
        self.waveBands = list(range(380, 780 +1, interval))
        # self.sLabel = QtWidgets.QLabel(f'{self.waveBands[0]}')
        self.sLabel = QtWidgets.QLabel(\
            'Use autoscaled slider to select the waveband keeping in mind deglitching is only performed from 350 - 850 nm:')
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
        self.updateButton.setToolTip('Updates all but the Min/Max Bands')
        self.updateButton.setDefault(True)

        self.saveButton = QtWidgets.QPushButton('Save Sensor Params', self, clicked=self.saveButtonPressed)
        self.saveButton.setToolTip('Save these params to Configuration and file')

        self.plotButton = QtWidgets.QPushButton('Save Anomaly Plots', self, clicked=self.plotButtonPressed)

        self.processButton = QtWidgets.QPushButton('Process to L1D', self, clicked=self.processButtonPressed)

        self.closeButton = QtWidgets.QPushButton('Close', self, clicked=self.closeButtonPressed)

        self.WindowDarkLabel = QtWidgets.QLabel("Window(odd)", self)
        self.WindowDarkLineEdit = QtWidgets.QLineEdit(self)
        self.WindowDarkLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}WindowDark']))
        self.WindowDarkLineEdit.setValidator(intValidator)
        # self.WindowDarkLineEdit.setValidator(oddValidator)
        self.WindowDarkLineEdit.returnPressed.connect(self.updateButton.click)        

        self.SigmaDarkLabel = QtWidgets.QLabel("Sigma", self)
        self.SigmaDarkLineEdit = QtWidgets.QLineEdit(self)
        self.SigmaDarkLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}SigmaDark']))
        self.SigmaDarkLineEdit.setValidator(doubleValidator)
        self.SigmaDarkLineEdit.returnPressed.connect(self.updateButton.click) 

        self.MinDarkLabel = QtWidgets.QLabel("Min", self)
        self.MinDarkLineEdit = QtWidgets.QLineEdit(self)
        self.MinDarkLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}MinDark']))    
        self.MinDarkLineEdit.returnPressed.connect(self.updateButton.click)

        self.MinMaxDarkButton = QtWidgets.QPushButton('Set Band:', self, clicked=self.MinMaxDarkButtonPressed)
        self.MinMaxDarkButton.setToolTip('Select this band for Min/Max thresholding')
        self.MinMaxDarkLabel = QtWidgets.QLabel("", self)

        self.MaxDarkLabel = QtWidgets.QLabel("Max", self)
        self.MaxDarkLineEdit = QtWidgets.QLineEdit(self)
        self.MaxDarkLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}MaxDark']))        
        self.MaxDarkLineEdit.returnPressed.connect(self.updateButton.click) 

        self.pLossDarkLabel = QtWidgets.QLabel('% Loss (all bands)', self)
        self.pLossDarkLineEdit = QtWidgets.QLineEdit(self)
        self.pLossDarkLineEdit.setText('0')

        self.WindowLightLabel = QtWidgets.QLabel("Window(odd)", self)
        self.WindowLightLineEdit = QtWidgets.QLineEdit(self)
        self.WindowLightLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}WindowLight']))
        self.WindowLightLineEdit.setValidator(intValidator)
        # self.WindowLightLineEdit.setValidator(oddValidator)
        self.WindowLightLineEdit.returnPressed.connect(self.updateButton.click) 

        self.SigmaLightLabel = QtWidgets.QLabel("Sigma Factor", self)
        self.SigmaLightLineEdit = QtWidgets.QLineEdit(self)
        self.SigmaLightLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}SigmaLight']))        
        self.SigmaLightLineEdit.setValidator(doubleValidator)
        self.SigmaLightLineEdit.returnPressed.connect(self.updateButton.click) 

        self.MinLightLabel = QtWidgets.QLabel("Min", self)
        self.MinLightLineEdit = QtWidgets.QLineEdit(self)
        self.MinLightLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}MinLight']))
        self.MinLightLineEdit.returnPressed.connect(self.updateButton.click) 

        self.MinMaxLightButton = QtWidgets.QPushButton('Set Band:', self, clicked=self.MinMaxLightButtonPressed)
        self.MinMaxLightButton.setToolTip('Select this band for Min/Max thresholding')
        self.MinMaxLightLabel = QtWidgets.QLabel("", self)

        self.MaxLightLabel = QtWidgets.QLabel("Max", self)
        self.MaxLightLineEdit = QtWidgets.QLineEdit(self)
        self.MaxLightLineEdit.setText(str(ConfigFile.settings[f'fL1d{self.sensor}MaxLight']))        
        self.MaxLightLineEdit.returnPressed.connect(self.updateButton.click) 

        self.pLossLightLabel = QtWidgets.QLabel('% Loss (all bands)', self)
        self.pLossLightLineEdit = QtWidgets.QLineEdit(self)
        self.pLossLightLineEdit.setText('0')

        # self.ThresholdLabel = QtWidgets.QLabel("Threshold", self)
        self.ThresholdCheckBox = QtWidgets.QCheckBox("Threshold", self)
        if int(ConfigFile.settings["bL1dThreshold"]) == 1:
            self.ThresholdCheckBox.setChecked(True)
        else:
            self.ThresholdCheckBox.setChecked(False)
        self.ThresholdCheckBoxUpdate()

        self.plotWidgetDark = pg.PlotWidget(self)            
        self.plotWidgetLight = pg.PlotWidget(self)     

        guideLabel = QtWidgets.QLabel(\
            'Left-click to pan. Right click to zoom. Hit "A" button on bottom left of plot to restore.')

        self.ThresholdCheckBox.clicked.connect(self.ThresholdCheckBoxUpdate) 

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
        self.ph3rdDark = self.plotWidgetDark.plot(x,y, symbolPen='r',\
                 symbol='o', name='2nd pass', pen=None)

        self.phLight = self.plotWidgetLight.plot(x,y, symbolPen='b',\
                 symbol='o', name='time series', pen=None)
        self.phTimeAveLight = self.plotWidgetLight.plot(x,y, pen='g', name='running')
        self.ph1stLight = self.plotWidgetLight.plot(x,y, symbolPen='r',\
                 symbol='x', name='1st pass', pen=None)
        self.ph2ndLight = self.plotWidgetLight.plot(x,y, symbolPen='r',\
                 symbol='+', name='2nd pass', pen=None)   
        self.ph3rdLight = self.plotWidgetLight.plot(x,y, symbolPen='r',\
                 symbol='o', name='2nd pass', pen=None)   
                            
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
        
        HBox2.addSpacing(55)
        HBox2.addWidget(self.updateButton)    
        HBox2.addSpacing(55)
        HBox2.addStretch()        
                
        HBox2.addWidget(AnomalyStepLabel)        
        HBox2.addWidget(self.AnomalyStepLineEdit)
        HBox2.addWidget(self.saveButton)
        HBox2.addWidget(self.plotButton)
        HBox2.addWidget(self.processButton)
        HBox2.addWidget(self.closeButton)
        self.VBox.addLayout(HBox2)

        HBox3 = QtWidgets.QHBoxLayout()  
        HBox3.addWidget(self.WindowDarkLabel)
        HBox3.addWidget(self.WindowDarkLineEdit)
        HBox3.addWidget(self.SigmaDarkLabel)
        HBox3.addWidget(self.SigmaDarkLineEdit)                
        
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
        # HBox4.addWidget(self.ThresholdLabel)
        HBox4.addWidget(self.ThresholdCheckBox)
        HBox4.addWidget(self.MinDarkLabel)
        HBox4.addWidget(self.MinDarkLineEdit)        
        HBox4.addWidget(self.MaxDarkLabel)
        HBox4.addWidget(self.MaxDarkLineEdit)
        HBox4.addWidget(self.MinMaxDarkButton)
        HBox4.addWidget(self.MinMaxDarkLabel)
        HBox4.addSpacing(35)
        HBox4.addStretch() 
        HBox4.addWidget(self.MinLightLabel)
        HBox4.addWidget(self.MinLightLineEdit)        
        HBox4.addWidget(self.MaxLightLabel)
        HBox4.addWidget(self.MaxLightLineEdit)
        HBox4.addWidget(self.MinMaxLightButton)
        HBox4.addWidget(self.MinMaxLightLabel)
        self.VBox.addLayout(HBox4)

        HBox5 = QtWidgets.QHBoxLayout()  
        HBox5.addWidget(self.plotWidgetDark)
        HBox5.addWidget(self.plotWidgetLight)
        self.VBox.addLayout(HBox5)

        self.VBox.addWidget(guideLabel)
        
        self.setLayout(self.VBox)
        self.setGeometry(100, 70, 1400, 700)  

        self.sliderWave = float(self.slider.value())

        # Run this on first opening the GUI
        self.loadL1Cfile()
        # self.updateButtonPressed()

    def sliderMove(self):
        self.sliderWave = float(self.slider.value())
        ''' This fails to update the label '''
        self.sLabel.setText(f'Deglitching only performed from 350-850 nm: {self.sliderWave}')            
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
                setattr(self,f'{sensor}MinDark', self.params[self.fileName][ref+4] )
                setattr(self,f'{sensor}MaxDark', self.params[self.fileName][ref+5] )
                setattr(self,f'{sensor}MinMaxBandDark', self.params[self.fileName][ref+6] )
                setattr(self,f'{sensor}MinLight', self.params[self.fileName][ref+7] )
                setattr(self,f'{sensor}MaxLight', self.params[self.fileName][ref+8] )  
                setattr(self,f'{sensor}MinMaxBandLight', self.params[self.fileName][ref+9] )
                ref += 10
            setattr(self,'Threshold', self.params[self.fileName][30])
            if getattr(self,'Threshold') == 1:
                self.ThresholdCheckBox.setChecked(True)
            else:
                self.ThresholdCheckBox.setChecked(False)
            self.ThresholdCheckBoxUpdate()
        
        # Set the GUI parameters for the current sensor from the local object
        self.WindowDarkLineEdit.setText(str(getattr(self,f'{self.sensor}WindowDark')))
        self.WindowLightLineEdit.setText(str(getattr(self,f'{self.sensor}WindowLight')))
        self.SigmaDarkLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaDark')))
        self.SigmaLightLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaLight')))
        self.MinDarkLineEdit.setText(str(getattr(self,f'{self.sensor}MinDark')))
        self.MinLightLineEdit.setText(str(getattr(self,f'{self.sensor}MinLight')))
        self.MaxDarkLineEdit.setText(str(getattr(self,f'{self.sensor}MaxDark')))
        self.MaxLightLineEdit.setText(str(getattr(self,f'{self.sensor}MaxLight')))            

        self.updateButtonPressed() 

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
        x = None if self.MinDarkLineEdit.text()=='None' else float(self.MinDarkLineEdit.text())
        setattr(self,f'{self.sensor}MinDark', x )
        x = None if self.MinLightLineEdit.text()=='None' else float(self.MinLightLineEdit.text())
        setattr(self,f'{self.sensor}MinLight', x )
        x = None if self.MaxDarkLineEdit.text()=='None' else float(self.MaxDarkLineEdit.text())
        setattr(self,f'{self.sensor}MaxDark', x )
        x = None if self.MaxLightLineEdit.text()=='None' else float(self.MaxLightLineEdit.text())
        setattr(self,f'{self.sensor}MaxLight', x )             

        radioButton = self.sender()
        if radioButton.isChecked():
            self.sensor = radioButton.text()
            print("Sensor is %s" % (self.sensor))        
            # Now update the LineEdits with saved values in the local object
            self.WindowDarkLineEdit.setText(str(getattr(self,f'{self.sensor}WindowDark')))
            self.WindowLightLineEdit.setText(str(getattr(self,f'{self.sensor}WindowLight')))
            self.SigmaDarkLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaDark')))
            self.SigmaLightLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaLight')))
            self.MinDarkLineEdit.setText(str(getattr(self,f'{self.sensor}MinDark')))
            self.MinLightLineEdit.setText(str(getattr(self,f'{self.sensor}MinLight')))
            self.MaxDarkLineEdit.setText(str(getattr(self,f'{self.sensor}MaxDark')))
            self.MaxLightLineEdit.setText(str(getattr(self,f'{self.sensor}MaxLight')))

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
        x = None if self.MinDarkLineEdit.text()=='None' else float(self.MinDarkLineEdit.text())
        setattr(self,f'{self.sensor}MinDark', x )
        x = None if self.MinLightLineEdit.text()=='None' else float(self.MinLightLineEdit.text())
        setattr(self,f'{self.sensor}MinLight', x )
        x = None if self.MaxDarkLineEdit.text()=='None' else float(self.MaxDarkLineEdit.text())
        setattr(self,f'{self.sensor}MaxDark', x )
        x = None if self.MaxLightLineEdit.text()=='None' else float(self.MaxLightLineEdit.text())
        setattr(self,f'{self.sensor}MaxLight', x )     
                
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
        self.sLabel.setText(f'Deglitching only performed from 350-850 nm: {self.waveBand}')            
        self.slider.setMinimum(min(waveBands))
        self.slider.setMaximum(max(waveBands))
        # self.slider.setTickInterval(10)
        self.slider.setValue(self.sliderWave)

        # Update minmax text
        self.MinMaxDarkLabel.setText(str(getattr(self,f'{self.sensor}MinMaxBandDark')) +'nm' )
        self.MinMaxLightLabel.setText(str(getattr(self,f'{self.sensor}MinMaxBandLight')) +'nm')

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
                window = int(self.WindowDarkLineEdit.text())
                sigma = float(self.SigmaDarkLineEdit.text())
                minDark = None if self.MinDarkLineEdit.text()=='None' else float(self.MinDarkLineEdit.text())
                maxDark = None if self.MaxDarkLineEdit.text()=='None' else float(self.MaxDarkLineEdit.text())
                MinMaxDarkBand = getattr(self,f'{self.sensor}MinMaxBandDark')
                lightDark = 'Dark'
                badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(band,radiometry1D, window, sigma, lightDark, minDark, maxDark,MinMaxDarkBand) 
                globalBadIndex.append(badIndex)
                globalBadIndex.append(badIndex2)
                globalBadIndex.append(badIndex3)

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
                window = int(self.WindowLightLineEdit.text())
                sigma = float(self.SigmaLightLineEdit.text())
                minLight = None if self.MinLightLineEdit.text()=='None' else float(self.MinLightLineEdit.text())
                maxLight = None if self.MaxLightLineEdit.text()=='None' else float(self.MaxLightLineEdit.text())
                MinMaxLightBand = getattr(self,f'{self.sensor}MinMaxBandLight')
                lightDark = 'Light'
                badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(band,radiometry1D, window, sigma, lightDark, minLight, maxLight,MinMaxLightBand) 
                globalBadIndex.append(badIndex)
                globalBadIndex.append(badIndex2)
                globalBadIndex.append(badIndex3)

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
            ConfigFile.settings[f'fL1d{sensor}MinDark'] = getattr(self,f'{sensor}MinDark')
            ConfigFile.settings[f'fL1d{sensor}MinLight'] = getattr(self,f'{sensor}MinLight')
            ConfigFile.settings[f'fL1d{sensor}MaxDark'] = getattr(self,f'{sensor}MaxDark')
            ConfigFile.settings[f'fL1d{sensor}MaxLight'] = getattr(self,f'{sensor}MaxLight')
            ConfigFile.settings[f'fL1d{sensor}MinMaxBandDark'] = getattr(self,f'{sensor}MinMaxBandDark')
            ConfigFile.settings[f'fL1d{sensor}MinMaxBandLight'] = getattr(self,f'{sensor}MinMaxBandLight')

            params.append(getattr(self,f'{sensor}WindowDark'))
            params.append(getattr(self,f'{sensor}WindowLight'))
            params.append(getattr(self,f'{sensor}SigmaDark'))
            params.append(getattr(self,f'{sensor}SigmaLight'))
            params.append(getattr(self,f'{sensor}MinDark'))
            params.append(getattr(self,f'{sensor}MaxDark'))
            params.append(getattr(self,f'{sensor}MinMaxBandDark'))
            params.append(getattr(self,f'{sensor}MinLight'))            
            params.append(getattr(self,f'{sensor}MaxLight'))
            params.append(getattr(self,f'{sensor}MinMaxBandLight'))
        
        ConfigFile.settings[f'bL1dThreshold'] = getattr(self,f'Threshold')
        params.append(getattr(self,f'Threshold'))

        self.params[self.fileName] = params

        # Steps in wavebands used for plots
        ConfigFile.settings["fL1dAnomalyStep"] = int(self.AnomalyStepLineEdit.text())

        # Save file-specific parameters to CSV file
        fp = os.path.join('Config',self.anomAnalFileName)
        self.writeAnomAnalFile(fp)

    def writeAnomAnalFile(self, filePath):
        header = ['filename','ESWindowDark','ESWindowLight','ESSigmaDark','ESSigmaLight','ESMinDark','ESMaxDark',\
            'ESMinMaxBandDark','ESMinLight','ESMaxLight','ESMinMaxBandLight',
            'LIWindowDark','LIWindowLight','LISigmaDark','LISigmaLight','LIMinDark','LIMaxDark',
            'LIMinMaxBandDark','LIMinLight','LIMaxLight','LIMinMaxBandLight',
            'LTWindowDark','LTWindowLight','LTSigmaDark','LTSigmaLight','LTMinDark','LTMaxDark',
            'LTMinMaxBandDark','LTMinLight','LTMaxLight','LTMinMaxBandLight','Threshold']
        # fieldnames = params.keys()

        with open(filePath, 'w', newline='') as csvfile:
            paramwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            paramwriter.writerow(header)
            for key, values in self.params.items():
                values = [-999 if v==None else v for v in values]
                paramwriter.writerow([key]+values)

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
                window = getattr(self,f'{sensorType}WindowDark')
                sigma = getattr(self,f'{sensorType}SigmaDark')
                minDark = getattr(self,f'{sensorType}MinDark')
                maxDark = getattr(self,f'{sensorType}MaxDark')
                minMaxDarkBand = getattr(self,f'{sensorType}MinMaxBandDark')

                index = 0
                for timeSeries in columns.items():
                    band = float(timeSeries[0])
                    if band > self.minBand and band < self.maxBand:
                        if index % step == 0:    
                            radiometry1D = timeSeries[1]
                            badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(band,radiometry1D, window, sigma, lightDark, minDark, maxDark,minMaxDarkBand)                
                            self.savePlots(self.fileName,plotdir,timeSeries,sensorType,lightDark,window,sigma,badIndex,badIndex2,badIndex3)
                        index +=1

            if lightData is None:
                print("Error: No light data to deglitch")
            else:    
                print("Light data anomaly analysis") 
                lightDark = 'Light'       
                lightData.datasetToColumns()
                columns = lightData.columns
                window = getattr(self,f'{sensorType}WindowLight')
                sigma = getattr(self,f'{sensorType}SigmaLight')
                minLight = getattr(self,f'{sensorType}MinLight')
                maxLight = getattr(self,f'{sensorType}MaxLight')
                minMaxLightBand = getattr(self,f'{sensorType}MinMaxBandLight')

                index = 0        
                for timeSeries in columns.items():
                    band = float(timeSeries[0])
                    if band > self.minBand and band < self.maxBand:
                        if index % step == 0:           
                            radiometry1D = timeSeries[1]
                            badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(band,radiometry1D, window, sigma, lightDark, minLight, maxLight,minMaxLightBand)              
                            self.savePlots(self.fileName,plotdir,timeSeries,sensorType,lightDark,window,sigma,badIndex,badIndex2,badIndex3)
                        index += 1
                print('Complete')

    def processButtonPressed(self):
        # Run L1D processing for this file        

        inFilePath = os.path.join(self.inputDirectory, 'L1C', self.fileName+'.hdf')
        fileBaseName = self.fileName.split('_L1C')
        outFilePath = os.path.join(self.inputDirectory, 'L1D', fileBaseName[0]+'_L1D.hdf')

        # self.processL1d(inFilePath, outFilePath)
        # Jumpstart the logger:
        msg = "Process Single Level from Anomaly Analysis"
        os.environ["LOGFILE"] = (fileBaseName[0] + '_L1C_L1D.log') 
        Utilities.writeLogFile(msg,mode='w') # <<---- Logging initiated here
        root = Controller.processL1d(inFilePath, outFilePath)

        # In case of processing failure, write the report at this Process level, unless running stations
        #   Use numeric level for writeReport
        pathOut = outFilePath.split('L1D')[0]
        # outFilePath = os.path.join(self.inputDirectory, 'L1D', fileBaseName[0])
        if root is not None:
            timeStamp = root.attributes['TIME-STAMP']
            title = f'File: {fileBaseName[0]} Collected: {timeStamp}'
        else:
            timeStamp = 'Null'
            title = f'File: {fileBaseName} Collected: {timeStamp}'
        if root is None and ConfigFile.settings["bL2WriteReport"] == 1:
            Controller.writeReport(title, fileBaseName, pathOut, outFilePath, 'L1D')
        print('Process L1D complete')

    def closeButtonPressed(self):
        print('Done')        
        self.close()      

    def ThresholdCheckBoxUpdate(self):
        print("ThresholdCheckBoxUpdate")
        
        disabled = (not self.ThresholdCheckBox.isChecked())
        self.MinDarkLineEdit.setDisabled(disabled)
        self.MaxDarkLineEdit.setDisabled(disabled)
        self.MinLightLineEdit.setDisabled(disabled)
        self.MaxLightLineEdit.setDisabled(disabled)
        self.MinMaxDarkButton.setDisabled(disabled)
        self.MinMaxLightButton.setDisabled(disabled)

        if disabled:
            ConfigFile.settings["bL1dThreshold"] = 0  
            setattr(self,"Threshold", 0)
        else:
            ConfigFile.settings["bL1dThreshold"] = 1
            setattr(self,"Threshold", 1)

    def MinMaxDarkButtonPressed(self):
        print('Updating waveband for Dark thresholds')
        # Test for root
        if not hasattr(self, 'root'):
            note = QtWidgets.QMessageBox()
            note.setText('You must load L1C file before continuing')
            note.exec_()
            return   
        sensorType = self.sensor
        print(sensorType)

         # Set parameters in the local object from the GUI
        setattr(self,f'{self.sensor}MinMaxBandDark', self.waveBand)
        self.MinMaxDarkLabel.setText(str(self.waveBand) +'nm' )

    def MinMaxLightButtonPressed(self):
        print('Updating waveband for Light thresholds')
        # Test for root
        if not hasattr(self, 'root'):
            note = QtWidgets.QMessageBox()
            note.setText('You must load L1C file before continuing')
            note.exec_()
            return   
        sensorType = self.sensor
        print(sensorType)

         # Set parameters in the local object from the GUI
        setattr(self,f'{self.sensor}MinMaxBandLight', self.waveBand)        
        self.MinMaxLightLabel.setText(str(self.waveBand) +'nm' )        


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
            ph3rd = self.ph3rdDark
            window = getattr(self,f'{sensorType}WindowDark')
            sigma = getattr(self,f'{sensorType}SigmaDark')
            minRad = getattr(self,f'{sensorType}MinDark')
            maxRad = getattr(self,f'{sensorType}MaxDark')
            minMaxBand = getattr(self,f'{sensorType}MinMaxBandDark')
            text_ylabel=f'{sensorType} Darks {self.waveBand}'
            figTitle = f'Band: {self.waveBand} Window: {window} Sigma: {sigma}'
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
            ph3rd = self.ph3rdLight
            window = getattr(self,f'{sensorType}WindowLight')
            sigma = getattr(self,f'{sensorType}SigmaLight')
            minRad = getattr(self,f'{sensorType}MinLight')
            maxRad = getattr(self,f'{sensorType}MaxLight')
            minMaxBand = getattr(self,f'{sensorType}MinMaxBandLight')
            text_ylabel=f'{sensorType} Lights {self.waveBand}'
            figTitle = f'Band: {self.waveBand} Window: {window} Sigma: {sigma}'
            print(f'{figTitle} Dark')
            # self.plotWidgetLight.setWindowTitle(figTitle, **styles)
            self.plotWidgetLight.setLabel('left', text_ylabel, **styles)
            self.plotWidgetLight.setLabel('bottom', text_xlabel, **styles)
            self.plotWidgetLight.showGrid(x=True, y=True)
            self.plotWidgetLight.addLegend()    
             
        badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(self.waveBand,radiometry1D, window, sigma, lightDark, minRad, maxRad,minMaxBand)        
        avg = Utilities.movingAverage(radiometry1D, window).tolist() 

        ''' Use numeric series (x) for now in place of datetime '''
        x = np.arange(0,len(radiometry1D),1)    

        y_anomaly = np.array(radiometry1D)[badIndex]
        x_anomaly = x[badIndex]
        # x_anomaly = dfx['x'][badIndex]
        y_anomaly2 = np.array(radiometry1D)[badIndex2]
        x_anomaly2 = x[badIndex2]
        # x_anomaly2 = dfx['x'][badIndex2]
        y_anomaly3 = np.array(radiometry1D)[badIndex3]
        x_anomaly3 = x[badIndex3]

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
            ph3rd.setData(x_anomaly3, y_anomaly3, symbolPen='r',\
                symbol='o', name='thresholds')
            
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)

    @staticmethod
    def savePlots(fileName,plotdir,timeSeries,sensorType,lightDark,windowSize,sigma,badIndex,badIndex2,badIndex3):#,\
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
            y_anomaly3 = np.array(radiometry1D)[badIndex3]
            x_anomaly3 = x[badIndex3]
            plt.plot(x_anomaly, y_anomaly, "rs", markersize=12)
            plt.plot(x_anomaly2, y_anomaly2, "b*", markersize=12)
            plt.plot(x_anomaly3, y_anomaly3, "ro", markersize=12)
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
