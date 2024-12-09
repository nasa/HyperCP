'''Deglitching of L1AQC radiometry time series'''
import os
import sys
import csv
import warnings
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from Source import PATH_TO_CONFIG
from Source.Controller import Controller
from Source.MainConfig import MainConfig
from Source.ConfigFile import ConfigFile
from Source.HDFRoot import HDFRoot
from Source.Utilities import Utilities
from Source.FieldPhotos import FieldPhotos
from Source.CalibrationFileReader import CalibrationFileReader

class AnomAnalWindow(QtWidgets.QDialog):
    '''Anomaly Analysis supervised screening and deglitching GUI'''

    def __init__(self, inputDirectory, parent=None):
        super().__init__(parent)
        self.inputDirectory = inputDirectory
        self.waveBand = []
        self.waveBands = []
        self.setModal(True)
        self.sensor='ES'
        self.sliderWave=525
        self.fileName = None
        self.root = None
        self.start = None
        self.end = None
        self.photoList = None
        self.photoDT = None

        #   This is going to truncate the ancillary data, so for the purposes of re-use, copy it
        self.ancillaryData = Controller.processAncData(MainConfig.settings["ancFile"])

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.minBand = ConfigFile.minDeglitchBand
        self.maxBand = ConfigFile.maxDeglitchBand

        # If there is an AnomAnal file, open it for later access
        # to file-specific parameters
        anomAnalFileName = os.path.splitext(ConfigFile.filename)[0]
        self.anomAnalFileName = anomAnalFileName + '_anoms.csv'
        fp = os.path.join(PATH_TO_CONFIG, self.anomAnalFileName)
        if os.path.exists(fp):
            print(f'{self.anomAnalFileName} found. Loading params.')
            self.params = Utilities.readAnomAnalFile(fp)
        else:
            self.params = {}

        # Initially, set these to generic values in ConfigFile
        for sensor in ["ES","LI","LT"]:
            setattr(self,f'{sensor}WindowDark', ConfigFile.settings[f'fL1aqc{sensor}WindowDark'])
            setattr(self,f'{sensor}WindowLight', ConfigFile.settings[f'fL1aqc{sensor}WindowLight'] )
            setattr(self,f'{sensor}SigmaDark', ConfigFile.settings[f'fL1aqc{sensor}SigmaDark'] )
            setattr(self,f'{sensor}SigmaLight', ConfigFile.settings[f'fL1aqc{sensor}SigmaLight'] )
            setattr(self,f'{sensor}MinDark', ConfigFile.settings[f'fL1aqc{sensor}MinDark'] )
            setattr(self,f'{sensor}MaxDark', ConfigFile.settings[f'fL1aqc{sensor}MaxDark'] )
            setattr(self,f'{sensor}MinMaxBandDark', ConfigFile.settings[f'fL1aqc{sensor}MinMaxBandDark'] )
            setattr(self,f'{sensor}MinLight', ConfigFile.settings[f'fL1aqc{sensor}MinLight'] )
            setattr(self,f'{sensor}MaxLight', ConfigFile.settings[f'fL1aqc{sensor}MaxLight'] )
            setattr(self,f'{sensor}MinMaxBandLight', ConfigFile.settings[f'fL1aqc{sensor}MinMaxBandLight'] )

        setattr(self,'Threshold', ConfigFile.settings['bL1aqcThreshold'] )

        # Set up the User Interface
        self.initUI()

    def paint(self, p, *args):
        p.setPen(pg.mkPen(0, 0, 0, 100))
        p.setBrush(pg.mkBrush(255, 255, 255, 50))
        p.viewRect()

    def initUI(self):

        intValidator = QtGui.QIntValidator()
        doubleValidator = QtGui.QDoubleValidator()

        # Set up the window
        self.commentLabel =  QtWidgets.QLabel('Comments',self)
        self.commentLineEdit = QtWidgets.QLineEdit(self)

        # Put up the metadata at the top of the window
        self.fileDateLabel = QtWidgets.QLabel(self)
        self.windSpeedLabel = QtWidgets.QLabel(self)
        self.cloudsLabel = QtWidgets.QLabel(self)
        self.relAzLabel = QtWidgets.QLabel(self)
        self.szaLabel = QtWidgets.QLabel(self)
        self.wavesLabel = QtWidgets.QLabel(self)
        self.speedLabel = QtWidgets.QLabel(self)

        # Add a button to launch photo method
        # photoLabel = QtWidgets.QLabel("Photo",self)
        self.photoButton = QtWidgets.QPushButton("Photo")
        self.photoButton.clicked.connect(self.photoButtonPressed)
        photoFormatLabel = QtWidgets.QLabel(\
            "InputDir/Photos naming (+timezone), e.g. IMG_%Y%m%d_%H%M%S.jpg-0400:", self)
        self.photoFormat = QtWidgets.QLineEdit(self)
        if 'sL1aqcphotoFormat' in ConfigFile.settings:
            self.photoFormat.setText(ConfigFile.settings["sL1aqcphotoFormat"])
        else:
            self.photoFormat.setText('IMG_%Y%m%d_%H%M%S.jpg-0400')
            # Adds to Config, and saves
            ConfigFile.settings['sL1aqcphotoFormat'] = 'IMG_%Y%m%d_%H%M%S.jpg-0400'
            ConfigFile.saveConfig(ConfigFile.filename)

        # These will be adjusted on the slider once a file is loaded
        interval = 10
        self.waveBands = list(range(380, 780 +1, interval))
        # self.sLabel = QtWidgets.QLabel(f'{self.waveBands[0]}')
        self.sLabel = QtWidgets.QLabel(\
            'Use autoscaled slider to select the waveband keeping in mind deglitching is only performed from 350 - 850 nm:')
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.valueChanged.connect(self.sliderMove)
        # self.slider.setMinimum(min(self.waveBands))
        # self.slider.setMaximum(max(self.waveBands))
        self.slider.setMinimum(self.minBand)
        self.slider.setMaximum(self.maxBand)
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

        AnomalyStepLabel = QtWidgets.QLabel("Waveband interval to for plots: ", self)
        self.AnomalyStepLineEdit = QtWidgets.QLineEdit(self)
        self.AnomalyStepLineEdit.setText(str(ConfigFile.settings["fL1aqcAnomalyStep"]))
        self.AnomalyStepLineEdit.setValidator(intValidator)

        self.loadButton = QtWidgets.QPushButton('Load L1A', self, clicked=self.loadL1Afile)

        self.updateButton = QtWidgets.QPushButton('***  Update  ***', self, clicked=self.updateButtonPressed)
        self.updateButton.setToolTip('Updates all but the Min/Max Bands')
        self.updateButton.setDefault(True)

        self.photoFormat.returnPressed.connect(self.updateButton.click)

        self.saveButton = QtWidgets.QPushButton('Save Sensor Params', self, clicked=self.saveButtonPressed)
        self.saveButton.setToolTip('Save these params to Configuration and file')

        self.plotButton = QtWidgets.QPushButton('Save Anomaly Plots', self, clicked=self.plotButtonPressed)

        self.processButton = QtWidgets.QPushButton('Process to L1AQC', self, clicked=self.processButtonPressed)

        self.closeButton = QtWidgets.QPushButton('Close', self, clicked=self.closeButtonPressed)

        self.WindowDarkLabel = QtWidgets.QLabel("Window(odd)", self)
        self.WindowDarkLineEdit = QtWidgets.QLineEdit(self)
        self.WindowDarkLineEdit.setText(str(ConfigFile.settings[f'fL1aqc{self.sensor}WindowDark']))
        self.WindowDarkLineEdit.setValidator(intValidator)
        # self.WindowDarkLineEdit.setValidator(oddValidator)
        self.WindowDarkLineEdit.returnPressed.connect(self.updateButton.click)

        self.SigmaDarkLabel = QtWidgets.QLabel("Sigma", self)
        self.SigmaDarkLineEdit = QtWidgets.QLineEdit(self)
        self.SigmaDarkLineEdit.setText(str(ConfigFile.settings[f'fL1aqc{self.sensor}SigmaDark']))
        self.SigmaDarkLineEdit.setValidator(doubleValidator)
        self.SigmaDarkLineEdit.returnPressed.connect(self.updateButton.click)

        self.MinDarkLabel = QtWidgets.QLabel("Dark Min", self)
        self.MinDarkLineEdit = QtWidgets.QLineEdit(self)
        self.MinDarkLineEdit.setText(str(ConfigFile.settings[f'fL1aqc{self.sensor}MinDark']))
        self.MinDarkLineEdit.returnPressed.connect(self.updateButton.click)

        self.MinMaxDarkButton = QtWidgets.QPushButton('Set Band:', self, clicked=self.MinMaxDarkButtonPressed)
        self.MinMaxDarkButton.setToolTip('Select this band for Min/Max thresholding')
        self.MinMaxDarkLabel = QtWidgets.QLabel("", self)

        self.MaxDarkLabel = QtWidgets.QLabel("Max", self)
        self.MaxDarkLineEdit = QtWidgets.QLineEdit(self)
        self.MaxDarkLineEdit.setText(str(ConfigFile.settings[f'fL1aqc{self.sensor}MaxDark']))
        self.MaxDarkLineEdit.returnPressed.connect(self.updateButton.click)

        self.pLossDarkLabel = QtWidgets.QLabel('% Loss (all bands)', self)
        self.pLossDarkLineEdit = QtWidgets.QLineEdit(self)
        self.pLossDarkLineEdit.setText('0')

        self.WindowLightLabel = QtWidgets.QLabel("Window(odd)", self)
        self.WindowLightLineEdit = QtWidgets.QLineEdit(self)
        self.WindowLightLineEdit.setText(str(ConfigFile.settings[f'fL1aqc{self.sensor}WindowLight']))
        self.WindowLightLineEdit.setValidator(intValidator)
        # self.WindowLightLineEdit.setValidator(oddValidator)
        self.WindowLightLineEdit.returnPressed.connect(self.updateButton.click)

        self.SigmaLightLabel = QtWidgets.QLabel("Sigma Factor", self)
        self.SigmaLightLineEdit = QtWidgets.QLineEdit(self)
        self.SigmaLightLineEdit.setText(str(ConfigFile.settings[f'fL1aqc{self.sensor}SigmaLight']))
        self.SigmaLightLineEdit.setValidator(doubleValidator)
        self.SigmaLightLineEdit.returnPressed.connect(self.updateButton.click)

        self.MinLightLabel = QtWidgets.QLabel("Light Min", self)
        self.MinLightLineEdit = QtWidgets.QLineEdit(self)
        self.MinLightLineEdit.setText(str(ConfigFile.settings[f'fL1aqc{self.sensor}MinLight']))
        self.MinLightLineEdit.returnPressed.connect(self.updateButton.click)

        self.GoToButton = QtWidgets.QPushButton('Go To Set Band', self, clicked=self.GoToButtonPressed)
        self.GoToButton.setToolTip('Go to threshold waveband')

        self.MaxLightLabel = QtWidgets.QLabel("Max", self)
        self.MaxLightLineEdit = QtWidgets.QLineEdit(self)
        self.MaxLightLineEdit.setText(str(ConfigFile.settings[f'fL1aqc{self.sensor}MaxLight']))
        self.MaxLightLineEdit.returnPressed.connect(self.updateButton.click)

        self.pLossLightLabel = QtWidgets.QLabel('% Loss (all bands)', self)
        self.pLossLightLineEdit = QtWidgets.QLineEdit(self)
        self.pLossLightLineEdit.setText('0')

        self.ThresholdCheckBox = QtWidgets.QCheckBox("Threshold", self)
        if int(ConfigFile.settings["bL1aqcThreshold"]) == 1:
            self.ThresholdCheckBox.setChecked(True)
        else:
            self.ThresholdCheckBox.setChecked(False)
        self.ThresholdCheckBoxUpdate()

        # Set up realtime plot widgets
        self.plotWidgetDark = pg.PlotWidget(self)
        self.plotWidgetDark.addLegend()
        self.plotWidgetDark.setAxisItems({'bottom': pg.DateAxisItem(utcOffset=0)})
        self.plotWidgetLight = pg.PlotWidget(self)
        self.plotWidgetLight.setAxisItems({'bottom': pg.DateAxisItem(utcOffset=0)})

        guideLabel = QtWidgets.QLabel(\
            'Left-click-hold to pan, right-click-hold to zoom, or right-click-release for more options.\
                IF PLOT IS BLANK, CLICK THE "A" IN THE BOTTOM LEFT CORNER TO RESET ZOOM.')

        self.ThresholdCheckBox.clicked.connect(self.ThresholdCheckBoxUpdate)

        # Opening plot
        x=[0,0]
        y=[0,0]
        self.phDark = self.plotWidgetDark.plot(x,y, name='Time series', pen='k')
        self.phTimeAveDark = self.plotWidgetDark.plot(x,y, name='Moving-window mean', pen='g')
        self.ph1stDark = self.plotWidgetDark.plot(x,y, symbolPen='r',symbol='x', name='Low-pass filter (1)', pen=None)
        self.ph2ndDark = self.plotWidgetDark.plot(x,y, symbolPen='m',symbol='+', name='Low-pass filter (2)', pen=None)
        self.ph3rdDark = self.plotWidgetDark.plot(x,y, symbolPen='c',symbol='o', symbolBrush=None, name='Threshold exceeded', pen=None)
        # Add datetime object to x axis
        # self.plotWidgetDark.setAxisItems({'bottom': date_axis_Dark})

        self.phLight = self.plotWidgetLight.plot(x,y, name='Time series', pen='k')
        self.phTimeAveLight = self.plotWidgetLight.plot(x,y, name='Moving-window mean', pen='g')
        self.ph1stLight = self.plotWidgetLight.plot(x,y, symbolPen='r',symbol='x', name='Low-pass filter (1)', pen=None)
        self.ph2ndLight = self.plotWidgetLight.plot(x,y, symbolPen='m',symbol='+', name='Low-pass filter (2)', pen=None)
        self.ph3rdLight = self.plotWidgetLight.plot(x,y, symbolPen='c',symbol='o', symbolBrush=None, name='Threshold exceeded', pen=None)
        # Add datetime object to x axis
        # self.plotWidgetLight.setAxisItems({'bottom': date_axis_Light})

        # Show defaults
        if self.sensor == "ES":
            WD = 11
            WL = 5
            SD = 3.2
            SL = 2.3
        elif self.sensor == 'LI':
            WD = 11
            WL = 5
            SD = 3.3
            SL = 3.0
        elif self.sensor == 'LT':
            WD = 11
            WL = 13
            SD = 3.2
            SL = 2.7

        self.WindowDarkLabel.setText(f'Window (odd;{WD})')
        self.WindowLightLabel.setText(f'Window (odd;{WL})')
        self.SigmaDarkLabel.setText(f'Sigma ({SD})')
        self.SigmaLightLabel.setText(f'Sigma ({SL})')


        # Layout ######################################################
        self.VBox = QtWidgets.QVBoxLayout()

        self.HBoxComment = QtWidgets.QHBoxLayout()
        self.HBoxComment.addWidget(self.commentLabel)
        self.HBoxComment.addWidget(self.commentLineEdit)
        self.VBox.addLayout(self.HBoxComment)

        self.HBoxMeta1 = QtWidgets.QHBoxLayout()
        self.HBoxMeta2 = QtWidgets.QHBoxLayout()
        self.HBoxMeta1.addWidget(self.fileDateLabel)
        self.HBoxMeta1.addSpacing(45)
        self.HBoxMeta1.addWidget(photoFormatLabel)
        self.HBoxMeta1.addWidget(self.photoFormat)
        self.HBoxMeta1.addWidget(self.photoButton)

        self.HBoxMeta2.addWidget(self.windSpeedLabel)
        self.HBoxMeta2.addWidget(self.cloudsLabel)
        self.HBoxMeta2.addWidget(self.relAzLabel)
        self.HBoxMeta2.addWidget(self.szaLabel)
        self.HBoxMeta2.addWidget(self.wavesLabel)
        self.HBoxMeta2.addWidget(self.speedLabel)
        self.VBox.addLayout(self.HBoxMeta1)
        self.VBox.addLayout(self.HBoxMeta2)

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
        HBox4.addWidget(self.ThresholdCheckBox)
        HBox4.addWidget(self.MinMaxDarkButton)
        HBox4.addWidget(self.MinMaxDarkLabel)
        HBox4.addWidget(self.GoToButton)

        HBox4.addSpacing(15)
        HBox4.addWidget(self.MinDarkLabel)
        HBox4.addWidget(self.MinDarkLineEdit)
        HBox4.addWidget(self.MaxDarkLabel)
        HBox4.addWidget(self.MaxDarkLineEdit)

        # HBox4.addSpacing(35)
        HBox4.addStretch()
        HBox4.addWidget(self.MinLightLabel)
        HBox4.addWidget(self.MinLightLineEdit)
        HBox4.addWidget(self.MaxLightLabel)
        HBox4.addWidget(self.MaxLightLineEdit)
        # HBox4.addWidget(self.MinMaxLightButton)
        # HBox4.addWidget(self.MinMaxLightLabel)
        self.VBox.addLayout(HBox4)

        HBox5 = QtWidgets.QHBoxLayout()
        HBox5.addWidget(self.plotWidgetDark)
        HBox5.addWidget(self.plotWidgetLight)
        self.VBox.addLayout(HBox5)

        self.VBox.addWidget(guideLabel)

        self.setLayout(self.VBox)
        self.setGeometry(100, 70, 1400, 700)

        # self.sliderWave = int(self.slider.value())
        self.sliderWave = float(self.slider.value())

        # Set up the photo path
        # pFormat = self.photoFormat.text()
        # tz = pFormat[-5:] # clumsy hardcoding of TZ pFormat: Must be the last 5 characters
        # pFormat = pFormat[0:-5]
        self.photoFP = os.path.join(self.inputDirectory, 'Photos')
        # print(self.photoFP)
        if os.path.isdir(self.photoFP) is False:
            os.mkdir(self.photoFP)
        # photoList, self.photoDT = FieldPhotos.photoSetup(self.photoFP, self.start, self.end, pFormat, tz)

        # Run this on first opening the GUI
        self.loadL1Afile()

        ##############################################

    def photoButtonPressed(self):
        print("Photo button pressed")

        photoWidget = FieldPhotos(self.photoList, self.photoDT, self)
        photoWidget.show()

    def sliderMove(self):
        # self.sliderWave = int(self.slider.value())
        self.sliderWave = float(self.slider.value())
        self.sLabel.setText(f'Deglitching only performed from 350-850 nm: {self.sliderWave}')

        # This creates problem prior to window opening. Use the update button after sliding.
        # self.updateButtonPressed()

    # def loadL1Afile(self, next=False):
    def loadL1Afile(self):
        inputDirectory = self.inputDirectory
        # Open L1A HDF5 file for Deglitching

        # self.sensor == "ES"

        inLevel = "L1A"
        subInputDir = os.path.join(inputDirectory + '/' + inLevel + '/')
        if os.path.exists(subInputDir):
            inFilePath,_ = QtWidgets.QFileDialog.getOpenFileNames(self, "Open L1A HDF5 file for Deglitching", \
                subInputDir,\
                   "Images (*.hdf *.HDF)",\
                    options=QtWidgets.QFileDialog.DontUseNativeDialog)
        else:
            inFilePath,_ = QtWidgets.QFileDialog.getOpenFileNames(self, "Open L1A HDF5 file for Deglitching", \
                inputDirectory,\
                   "Images (*.hdf *.HDF)",\
                    options=QtWidgets.QFileDialog.DontUseNativeDialog)
        try:
            print(inFilePath[0])
            if "hdf" not in inFilePath[0] and "HDF" not in inFilePath[0]:
                msg = "This does not appear to be an HDF file."
                Utilities.errorWindow("File Error", msg)
                print(msg)
                return
        except Exception:
            print('No file returned')
            return

        root = HDFRoot.readHDF5(inFilePath[0])
        if root.attributes["PROCESSING_LEVEL"] != "1a":
            msg = "This is not a Level 1A file."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            return

        # Process L1A to L1AQC with no deglitching        
        fileName = os.path.basename(os.path.splitext(inFilePath[0])[0]).replace("_L1A","_L1AQC")+".hdf"
        calibrationMap = Controller.processCalibrationConfig(ConfigFile.filename, ConfigFile.settings['CalibrationFiles'])
        outputDirectory = MainConfig.settings['outDir']
        pathOutLevel = os.path.join(outputDirectory, "L1AQC")
        outFilePath = os.path.join(pathOutLevel,fileName)
        # Add output level directory if necessary
        if os.path.isdir(pathOutLevel) is False:
            os.mkdir(pathOutLevel)
        temp = ConfigFile.settings['bL1aqcDeglitch']
        ConfigFile.settings['bL1aqcDeglitch'] = 0
        root = Controller.processL1aqc(inFilePath[0], outFilePath, calibrationMap, self.ancillaryData)

        if root is None:
            msg = "L1A file fails basic L1AQC."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            return
        # Restore full ancillary data
        # self.ancillaryData = self.ancillaryDataComplete
        ConfigFile.settings['bL1aqcDeglitch'] = temp


        Utilities.rootAddDateTime(root)

        # self.fileName = os.path.basename(os.path.splitext(inFilePath[0])[0])
        self.fileName = fileName.replace(".hdf",'')
        self.setWindowTitle(self.fileName)
        self.root = root # Undeglitched L1AQC

        # If a parameterization has been saved in the AnomAnalFile, set the properties in the local object
        # for all sensors
        if self.fileName in self.params.keys():
            print(f'{self.fileName} found in {self.anomAnalFileName}')

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
            self.commentLineEdit.setText(self.params[self.fileName][31])
            if getattr(self,'Threshold') == 1:
                self.ThresholdCheckBox.setChecked(True)
                # if getattr(self,f'{self.sensor}MinMaxBandDark'):
                #     self.waveBand = getattr(self,f'{self.sensor}MinMaxBandDark')
                #     self.slider.setValue(self.waveBand)
                # if getattr(self,f'{self.sensor}MinMaxBandLight'):
                #     self.waveBand = getattr(self,f'{self.sensor}MinMaxBandLight')
                #     self.slider.setValue(self.waveBand)
            else:
                self.ThresholdCheckBox.setChecked(False)
            self.ThresholdCheckBoxUpdate()
        else:
            print(f'{self.fileName} not found in {self.anomAnalFileName}. Falling back to Config settings')

        # Set the GUI parameters for the current sensor from the local object
        self.WindowDarkLineEdit.setText(str(getattr(self,f'{self.sensor}WindowDark')))
        self.WindowLightLineEdit.setText(str(getattr(self,f'{self.sensor}WindowLight')))
        self.SigmaDarkLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaDark')))
        self.SigmaLightLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaLight')))
        self.MinDarkLineEdit.setText(str(getattr(self,f'{self.sensor}MinDark')))
        self.MinLightLineEdit.setText(str(getattr(self,f'{self.sensor}MinLight')))
        self.MaxDarkLineEdit.setText(str(getattr(self,f'{self.sensor}MaxDark')))
        self.MaxLightLineEdit.setText(str(getattr(self,f'{self.sensor}MaxLight')))

        # Add an information bar based on metadata
        self.start = None
        self.end = None
        for group in root.groups:
            if group.id == 'ANCILLARY_METADATA':
                ancGroup = group
            if group.id == 'GPS':
                gpsGroup = group
                self.start = gpsGroup.datasets['DATETIME'].data[0]
                self.end = gpsGroup.datasets['DATETIME'].data[-1]
            if group.id == "SOLARTRACKER" or group.id == "SOLARTRACKER_pySAS":
                trackerGroup = group

        # For case of no GPS
        if self.start is None:
            self.start = ancGroup.datasets['DATETIME'].data[0]
            self.end = ancGroup.datasets['DATETIME'].data[-1]

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
            if 'WINDSPEED' in ancGroup.datasets:
                windSpeed = np.nanmedian(ancGroup.datasets['WINDSPEED'].data.tolist())
            else:
                windSpeed = np.nan
            if 'CLOUD' in ancGroup.datasets:
                cloud = np.nanmedian(ancGroup.datasets['CLOUD'].data.tolist())
            else:
                cloud = np.nan
            if 'REL_AZ' in ancGroup.datasets:
                relAz = np.nanmedian(ancGroup.datasets['REL_AZ'].data.tolist())
            else:
                relAz = np.nanmedian(trackerGroup.datasets['REL_AZ'].data.tolist())
            if 'SZA' in ancGroup.datasets:
                sza = np.nanmedian(ancGroup.datasets['SZA'].data.tolist())
            else:
                sza = np.nanmedian(trackerGroup.datasets['SZA'].data.tolist())
            if 'WAVE_HT' in ancGroup.datasets:
                waves = np.nanmedian(ancGroup.datasets['WAVE_HT'].data.tolist())
            else:
                waves = np.nan
            if 'SPEED_F_W' in ancGroup.datasets:
                speed = np.nanmedian(ancGroup.datasets['SPEED_F_W'].data.tolist())
            else:
                # Could resort to GPS SOG here, but that makes less sense than NaN
                speed = np.nan

        # self.fileDateLabel.setText(f"Begin: {root.attributes['TIME-STAMP']}")
        self.fileDateLabel.setText(f"FROM: {self.start:%Y-%m-%d %H:%M} TO: {self.end:%Y-%m-%d %H:%M} UTC")
        self.windSpeedLabel.setText(f' (Median->) WIND: {windSpeed:.1f} m/s')
        self.cloudsLabel.setText(f' CLOUD: {cloud:.0f} %')
        self.relAzLabel.setText(f' REL.AZ: {relAz:.0f} deg.')
        self.szaLabel.setText(f' SZA: {sza:.0f} deg.')
        self.wavesLabel.setText(f' WAVES: {waves:.1f} m')
        self.speedLabel.setText(f' SPEED: {speed:.1f} m/s')

        self.photoUpdate()
        self.updateButtonPressed()


    def photoUpdate(self): # Match data to photo, if possible
        pFormat = self.photoFormat.text()
        if '-' in pFormat[-5] or '+' in pFormat[-5]:
            tz = pFormat[-5:] # clumsy hardcoding of TZ pFormat: Must be the last 5 characters
            pFormat = pFormat[0:-5]
        else:
            tz = '-0000'

        self.photoList, self.photoDT = FieldPhotos.photoSetup(self.photoFP, self.start, self.end, pFormat, tz)
        if self.photoList is not None:
            print('Matching photo found')
            self.photoButton.setText(os.path.split(self.photoList[0])[-1])
            self.photoButton.setDisabled(0)
        else:
            self.photoButton.setText('No Photo Found')
            self.photoButton.setDisabled(1)

        # self.updateButtonPressed()

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
            print(f"Sensor is {self.sensor}")
            # Now update the LineEdits with saved values in the local object
            self.WindowDarkLineEdit.setText(str(getattr(self,f'{self.sensor}WindowDark')))
            self.WindowLightLineEdit.setText(str(getattr(self,f'{self.sensor}WindowLight')))
            self.SigmaDarkLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaDark')))
            self.SigmaLightLineEdit.setText(str(getattr(self,f'{self.sensor}SigmaLight')))
            self.MinDarkLineEdit.setText(str(getattr(self,f'{self.sensor}MinDark')))
            self.MinLightLineEdit.setText(str(getattr(self,f'{self.sensor}MinLight')))
            self.MaxDarkLineEdit.setText(str(getattr(self,f'{self.sensor}MaxDark')))
            self.MaxLightLineEdit.setText(str(getattr(self,f'{self.sensor}MaxLight')))


            # Show defaults
            if self.sensor == "ES":
                WD = 11
                WL = 5
                SD = 3.2
                SL = 2.3
            elif self.sensor == 'LI':
                WD = 11
                WL = 5
                SD = 3.3
                SL = 3.0
            elif self.sensor == 'LT':
                WD = 11
                WL = 13
                SD = 3.2
                SL = 2.7

            self.WindowDarkLabel.setText(f'Window (odd;{WD})')
            self.WindowLightLabel.setText(f'Window (odd;{WL})')
            self.SigmaDarkLabel.setText(f'Sigma ({SD})')
            self.SigmaLightLabel.setText(f'Sigma ({SL})')

        self.updateButtonPressed()

    def updateButtonPressed(self):
        print("Update pressed")
        # print(self.sliderWave)

        sensorType = self.sensor
        print(sensorType)

        # Update photo pFormat
        ConfigFile.settings['sL1aqcphotoFormat'] = self.photoFormat.text()
        ConfigFile.saveConfig(ConfigFile.filename)

        # Test for root
        if not hasattr(self, 'root'):
            note = QtWidgets.QMessageBox()
            note.setText('You must load L1A file before plotting')
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
            if "FrameType" not in gp.attributes:
                continue
            if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                darkData = gp.getDataset(sensorType)
                darkDateTime = Utilities.getDateTime(gp)
            if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                lightData = gp.getDataset(sensorType)
                lightDateTime = Utilities.getDateTime(gp)

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
            if not self.sliderWave:
                self.sliderWave = float(self.slider.value())
            whr = Utilities.find_nearest(self.waveBands, self.sliderWave)
            self.waveBand = self.waveBands[whr]
            # print(self.waveBand)

            radiometry1D = dark2D[f'{self.waveBand:03.2f}']

            # self.realTimePlot(self, radiometry1D, darkDateTime, sensorType,lightDark)
            AnomAnalWindow.realTimePlot(self, radiometry1D, darkDateTime, sensorType,lightDark)

        # Update the slider
        self.sLabel.setText(f'Deglitching only performed from 350-850 nm: {self.waveBand}')
        # self.slider.setMinimum(min(waveBands))
        # self.slider.setMaximum(max(waveBands))
        # self.slider.setTickInterval(10)
        self.slider.setValue(int(self.sliderWave))

        # Update minmax text
        self.MinMaxDarkLabel.setText(str(getattr(self,f'{self.sensor}MinMaxBandDark')) +' nm' )
        # self.MinMaxLightLabel.setText(str(getattr(self,f'{self.sensor}MinMaxBandLight')) +'nm')

        # # Try to use the Threshold bands to reset the slider and display
        # self.ThresholdCheckBoxUpdate()

        # Deglitch and plot Light from selected band
        if lightData is None:
            print("Error: No light data to deglitch")
        else:
            print("Light data anomaly analysis")
            lightDark = 'Light'
            lightData.datasetToColumns()
            light2D = lightData.columns
            radiometry1D = light2D[f'{self.waveBand:03.2f}']
            # print(self.waveBand)

            # self.realTimePlot(self, radiometry1D, lightDateTime, sensorType, lightDark)
            AnomAnalWindow.realTimePlot(self, radiometry1D, lightDateTime, sensorType, lightDark)

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

        self.photoUpdate()

    def saveButtonPressed(self):
        # Saves local parameterizations to the ConfigFile.settings
        # Triggered only when button pressed
        print("Save params pressed")

        params = []
        for sensor in ["ES","LI","LT"]:
            ConfigFile.settings[f'fL1aqc{sensor}WindowDark'] = getattr(self,f'{sensor}WindowDark')
            ConfigFile.settings[f'fL1aqc{sensor}WindowLight'] = getattr(self,f'{sensor}WindowLight')
            ConfigFile.settings[f'fL1aqc{sensor}SigmaDark'] = getattr(self,f'{sensor}SigmaDark')
            ConfigFile.settings[f'fL1aqc{sensor}SigmaLight'] = getattr(self,f'{sensor}SigmaLight')
            ConfigFile.settings[f'fL1aqc{sensor}MinDark'] = getattr(self,f'{sensor}MinDark')
            ConfigFile.settings[f'fL1aqc{sensor}MinLight'] = getattr(self,f'{sensor}MinLight')
            ConfigFile.settings[f'fL1aqc{sensor}MaxDark'] = getattr(self,f'{sensor}MaxDark')
            ConfigFile.settings[f'fL1aqc{sensor}MaxLight'] = getattr(self,f'{sensor}MaxLight')
            ConfigFile.settings[f'fL1aqc{sensor}MinMaxBandDark'] = getattr(self,f'{sensor}MinMaxBandDark')
            ConfigFile.settings[f'fL1aqc{sensor}MinMaxBandLight'] = getattr(self,f'{sensor}MinMaxBandLight')

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

        ConfigFile.settings['bL1aqcThreshold'] = getattr(self,'Threshold')
        params.append(getattr(self,'Threshold'))
        params.append(self.commentLineEdit.text())

        self.params[self.fileName] = params

        # Steps in wavebands used for plots
        ConfigFile.settings["fL1aqcAnomalyStep"] = int(self.AnomalyStepLineEdit.text())

        # Save file-specific parameters to CSV file
        fp = os.path.join(PATH_TO_CONFIG,self.anomAnalFileName)
        self.writeAnomAnalFile(fp)

    def writeAnomAnalFile(self, filePath):
        header = ['filename','ESWindowDark','ESWindowLight','ESSigmaDark','ESSigmaLight','ESMinDark','ESMaxDark',\
            'ESMinMaxBandDark','ESMinLight','ESMaxLight','ESMinMaxBandLight',
            'LIWindowDark','LIWindowLight','LISigmaDark','LISigmaLight','LIMinDark','LIMaxDark',
            'LIMinMaxBandDark','LIMinLight','LIMaxLight','LIMinMaxBandLight',
            'LTWindowDark','LTWindowLight','LTSigmaDark','LTSigmaLight','LTMinDark','LTMaxDark',
            'LTMinMaxBandDark','LTMinLight','LTMaxLight','LTMinMaxBandLight','Threshold','Comments']
        # fieldnames = params.keys()

        print(f'Saving {filePath}')
        with open(filePath, 'w', newline='', encoding="utf-8") as csvfile:
            paramwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            paramwriter.writerow(header)
            for key, values in self.params.items():
                values = [-999 if v is None else v for v in values]
                paramwriter.writerow([key]+values)

    def plotButtonPressed(self):
        print("Save plots pressed")
        # Steps in wavebands used for plots
        step = float(ConfigFile.settings["fL1aqcAnomalyStep"])

        sensorTypes = ["ES","LT","LI"]

        for sensorType in sensorTypes:
            print(sensorType)
            darkData = None
            lightData = None

            for gp in self.root.groups:
                if "FrameType" not in gp.attributes:
                    continue
                if gp.attributes["FrameType"] == "ShutterDark" and sensorType in gp.datasets:
                    darkData = gp.getDataset(sensorType)
                    darkDateTime = Utilities.getDateTime(gp)
                    # print(type(darkData))
                    # print(type(darkData.data))
                if gp.attributes["FrameType"] == "ShutterLight" and sensorType in gp.datasets:
                    lightData = gp.getDataset(sensorType)
                    lightDateTime = Utilities.getDateTime(gp)

            if darkData is None:
                print("Error: No dark data to deglitch")
            else:
                print("Dark data anomaly analysis")
                lightDark = 'Dark'
                darkData.datasetToColumns()
                columns = darkData.columns
                dateTime = darkDateTime
                window = getattr(self,f'{sensorType}WindowDark')
                sigma = getattr(self,f'{sensorType}SigmaDark')
                minDark = getattr(self,f'{sensorType}MinDark')
                maxDark = getattr(self,f'{sensorType}MaxDark')
                minMaxDarkBand = getattr(self,f'{sensorType}MinMaxBandDark')

                index = 0
                # Loop over bands to populate globBads
                for timeSeries in columns.items():
                    if index==0:
                        # Initialize boolean lists for capturing global badIndex conditions across all wavebands
                        globBad = [False]*len(timeSeries[1])
                        globBad2 = [False]*len(timeSeries[1])
                        globBad3 = [False]*len(timeSeries[1])
                    band = float(timeSeries[0])
                    if band > self.minBand and band < self.maxBand:
                        # if index % step == 0:
                        radiometry1D = timeSeries[1]
                        badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(band,radiometry1D, window, sigma, lightDark, minDark, maxDark,minMaxDarkBand)
                        globBad[:] = (True if val2 else val1 for (val1,val2) in zip(globBad,badIndex))
                        globBad2[:] = (True if val2 else val1 for (val1,val2) in zip(globBad2,badIndex2))
                        globBad3[:] = (True if val2 else val1 for (val1,val2) in zip(globBad3,badIndex3))
                            ##It would be good to use an aggregated badIndex on these plots for all bands combined...
                            # self.savePlots(self.fileName,plotdir,timeSeries,sensorType,lightDark,window,sigma,badIndex,badIndex2,badIndex3)
                    index +=1
                # Now plot a selection of these USING UNIVERSALLY EXCLUDED INDEXES
                index =0
                for timeSeries in columns.items():
                    band = float(timeSeries[0])
                    if band > self.minBand and band < self.maxBand:
                        if index % step == 0:
                            Utilities.saveDeglitchPlots(self.fileName,timeSeries,dateTime,sensorType,lightDark,window,sigma,globBad,globBad2,globBad3)
                    index +=1

            if lightData is None:
                print("Error: No light data to deglitch")
            else:
                print("Light data anomaly analysis")
                lightDark = 'Light'
                lightData.datasetToColumns()
                columns = lightData.columns
                dateTime = lightDateTime
                window = getattr(self,f'{sensorType}WindowLight')
                sigma = getattr(self,f'{sensorType}SigmaLight')
                minLight = getattr(self,f'{sensorType}MinLight')
                maxLight = getattr(self,f'{sensorType}MaxLight')
                minMaxLightBand = getattr(self,f'{sensorType}MinMaxBandLight')

                globalBadIndex = []

                index = 0
                for timeSeries in columns.items():
                    if index==0:
                        # Initialize boolean lists for capturing global badIndex conditions across all wavebands
                        globBad = [False]*len(timeSeries[1])
                        globBad2 = [False]*len(timeSeries[1])
                        globBad3 = [False]*len(timeSeries[1])
                    band = float(timeSeries[0])
                    if band > self.minBand and band < self.maxBand:
                        radiometry1D = timeSeries[1]
                        badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(band,radiometry1D, window, sigma, lightDark, minLight, maxLight,minMaxLightBand)

                        # For plotting:
                        globBad[:] = (True if val2 else val1 for (val1,val2) in zip(globBad,badIndex))
                        globBad2[:] = (True if val2 else val1 for (val1,val2) in zip(globBad2,badIndex2))
                        globBad3[:] = (True if val2 else val1 for (val1,val2) in zip(globBad3,badIndex3))

                        # For deletion:
                        globalBadIndex.append(badIndex)
                        globalBadIndex.append(badIndex2)
                        globalBadIndex.append(badIndex3)
                    index += 1

                # Collapse the badIndexes from all wavebands into one timeseries
                # Convert to an array and test along the columns (i.e. each timestamp)
                # gIndex = np.any(np.array(globalBadIndex), 0)
                # NOTE: if you similarly collapse globBads 1-3, you should get the same result as gIndex

                # Now plot a selection of these USING UNIVERSALLY EXCLUDED INDEXES
                index =0
                for timeSeries in columns.items():
                    band = float(timeSeries[0])
                    if band > self.minBand and band < self.maxBand:
                        if index % step == 0:
                            # self.savePlots(self.fileName,plotdir,timeSeries,sensorType,lightDark,window,sigma,globBad,globBad2,globBad3)
                            Utilities.saveDeglitchPlots(self.fileName,timeSeries,dateTime,sensorType,lightDark,window,sigma,globBad,globBad2,globBad3)
                    index +=1

                print('Complete')

    def processButtonPressed(self):
        # Run L1AQC processing for this file

        fileBaseName = self.fileName.split('_L1A')[0]
        # inFilePath = os.path.join(self.inputDirectory, 'L1A', fileBaseName+'_L1A.hdf')
        inFilePath = os.path.join(self.inputDirectory, 'L1A', self.fileName.replace('L1AQC','L1A')+'.hdf')
        outFilePath = os.path.join(self.inputDirectory, 'L1AQC', fileBaseName+'_L1AQC.hdf')

        # Jumpstart the logger:
        msg = "Process Single Level from Anomaly Analysis"
        os.environ["LOGFILE"] = (fileBaseName + '_L1A_L1AQC.log')
        Utilities.writeLogFile(msg,mode='w') # <<---- Logging initiated here

        calFolder = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
        calPath = os.path.join(PATH_TO_CONFIG, calFolder)
        print("Read CalibrationFile ", calPath)
        calibrationMap = CalibrationFileReader.read(calPath)
        root = Controller.processL1aqc(inFilePath, outFilePath, calibrationMap, self.ancillaryData)
        # Restore full ancillary data
        self.ancillaryData = self.ancillaryDataComplete

        # In case of processing failure, write the report at this Process level, unless running stations
        #   Use numeric level for writeReport
        pathOut = outFilePath.split('L1AQC')[0]

        if root is None and ConfigFile.settings["bL2WriteReport"] == 1:
            Controller.writeReport(fileBaseName, pathOut, outFilePath, 'L1AQC', inFilePath)
        print('Process L1AQC complete')

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
        # self.MinMaxLightButton.setDisabled(disabled)

        if disabled:
            ConfigFile.settings["bL1aqcThreshold"] = 0
            setattr(self,"Threshold", 0)
        else:
            ConfigFile.settings["bL1aqcThreshold"] = 1
            setattr(self,"Threshold", 1)

            # # Problem: can either set to the threshold waveband or to the slider position, not both
            # if getattr(self,f'{self.sensor}MinMaxBandDark'):
            #     self.waveBand = getattr(self,f'{self.sensor}MinMaxBandDark')
            #     self.slider.setValue(self.waveBand)
            # if getattr(self,f'{self.sensor}MinMaxBandLight'):
            #     self.waveBand = getattr(self,f'{self.sensor}MinMaxBandLight')
            #     self.slider.setValue(self.waveBand)

    def MinMaxDarkButtonPressed(self):
        print('Updating waveband for Dark thresholds')
        # Test for root
        if not hasattr(self, 'root'):
            note = QtWidgets.QMessageBox()
            note.setText('You must load L1A file before continuing')
            note.exec_()
            return
        sensorType = self.sensor
        print(sensorType)

         # Set parameters in the local object from the GUI
        whr = Utilities.find_nearest(self.waveBands, float(self.slider.value()))
        self.waveBand = self.waveBands[whr]
        setattr(self,f'{self.sensor}MinMaxBandDark', self.waveBand)
        self.MinMaxDarkLabel.setText(str(self.waveBand) +' nm' )
         # Set parameters in the local object from the GUI
        setattr(self,f'{self.sensor}MinMaxBandLight', self.waveBand)
        # self.MinMaxLightLabel.setText(str(self.waveBand) +'nm' )

    def GoToButtonPressed(self):
        print('Updating wavebands')

        # self.sliderWave = float(self.slider.value())
        self.sliderWave = getattr(self,f'{self.sensor}MinMaxBandLight')
        self.slider.setValue(int(self.sliderWave))
        self.sLabel.setText(f'Deglitching only performed from 350-850 nm: {self.sliderWave}')

        self.updateButtonPressed()

        #  # Set parameters in the local object from the GUI
        # setattr(self,f'{self.sensor}MinMaxBandLight', self.waveBand)
        # self.MinMaxLightLabel.setText(str(self.waveBand) +'nm' )


    # @staticmethod
    def realTimePlot(self, radiometry1D, dateTime, sensorType,lightDark):
        # Radiometry at this point is 1D 'column' from the appropriate group/dataset/waveband
        #   in time (radiometry1D)

        styles = {'font-size': '18px'}
        # text_xlabel="Time Series"

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
            # Round/truncate waveband and add units
            if sensorType == 'ES':
                radUnits = self.root.attributes['ES_UNITS']
            else:
                radUnits = self.root.attributes['LI_UNITS']

            text_ylabel=f'[DARKS]  {sensorType}({self.waveBand:.0f}) [{radUnits}]'
            text_xlabel='Time series'
            figTitle = f'Band: {self.waveBand} Window: {window} Sigma: {sigma}'
            # self.plotWidgetDark.setWindowTitle(figTitle)
            print(f'{figTitle} Dark')
            # self.plotWidgetDark.setWindowTitle(figTitle, **styles)
            self.plotWidgetDark.setLabel('left', text_ylabel,**styles)
            self.plotWidgetDark.setLabel('bottom', text_xlabel,**styles)
            # self.plotWidgetDark.setLabel('bottom', text_xlabel,**styles)
            self.plotWidgetDark.showGrid(x=True, y=True)

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
            # Round/truncate waveband and add units
            if sensorType == 'ES':
                radUnits = self.root.attributes['ES_UNITS']
            else:
                radUnits = self.root.attributes['LI_UNITS']

            text_ylabel=f'[LIGHTS]  {sensorType}({self.waveBand:.0f}) [{radUnits}]'
            text_xlabel='Time series'
            figTitle = f'Band: {self.waveBand} Window: {window} Sigma: {sigma}'
            print(f'{figTitle} Dark')
            # self.plotWidgetLight.setWindowTitle(figTitle, **styles)
            self.plotWidgetLight.setLabel('left', text_ylabel, **styles)
            self.plotWidgetLight.setLabel('bottom', text_xlabel,**styles)
            self.plotWidgetLight.showGrid(x=True, y=True)
            # self.plotWidgetLight.addLegend()

        badIndex, badIndex2, badIndex3 = Utilities.deglitchBand(self.waveBand,radiometry1D, window, sigma, lightDark, minRad, maxRad,minMaxBand)
        avg = Utilities.movingAverage(radiometry1D, window).tolist()

        # Convert to timestamp
        x = np.array([x.timestamp() for x in dateTime])

        # First Pass
        y_anomaly = np.array(radiometry1D)[badIndex]
        x_anomaly = x[badIndex]

        # Second Pass
        y_anomaly2 = np.array(radiometry1D)[badIndex2]
        x_anomaly2 = x[badIndex2]

        # Thresholds
        y_anomaly3 = np.array(radiometry1D)[badIndex3]
        x_anomaly3 = x[badIndex3]

        #Plot results
        try:
            ph.setData(x, radiometry1D, name=sensorType, pen=pg.mkPen('k', width=1))
            phAve.setData(x[3:-3], avg[3:-3], name='Moving-window mean', pen=pg.mkPen('g', width=3))
            ph1st.setData(x_anomaly , y_anomaly , symbolPen='r',symbol='x', name='Low-pass filter (1)')
            ph2nd.setData(x_anomaly2, y_anomaly2, symbolPen='m',symbol='+', name='Low-pass filter (2)')
            ph3rd.setData(x_anomaly3, y_anomaly3, symbolPen='c',symbol='o', symbolBrush=None, name='Threshold exceeded')


        except Exception:
            e = sys.exc_info()[0]
            print(f"Error: {e}")

