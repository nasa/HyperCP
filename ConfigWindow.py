
import os
import shutil
from PyQt5 import QtCore, QtGui, QtWidgets


from ConfigFile import ConfigFile


#class myListWidget(QtWidgets.QListWidget):
#   def Clicked(self,item):
#      QMessageBox.information(self, "ListWidget", "You clicked: "+item.text())


class ConfigWindow(QtWidgets.QDialog):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.name = name
        self.initUI()

    def initUI(self):
        # print("ConfigWindow - initUI")
        #self.label = QtWidgets.QLabel("Popup", self)

        nameLabel = QtWidgets.QLabel("Editing: " + self.name, self)

        # Calibration Config Settings
        self.addCalibrationFileButton = QtWidgets.QPushButton("Add Calibration Files")
        self.addCalibrationFileButton.clicked.connect(self.addCalibrationFileButtonPressed)

        calFiles = ConfigFile.settings["CalibrationFiles"]
        print("Calibration Files:")
        self.calibrationFileComboBox = QtWidgets.QComboBox(self)
        for file in calFiles:
            print(file)
        self.calibrationFileComboBox.addItems(sorted(calFiles.keys()))
        fsm = QtWidgets.QFileSystemModel()
        fsm.setNameFilters(["*.cal", "*.tdf"])
        fsm.setNameFilterDisables(False)
        fsm.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)
        calibrationDir = os.path.splitext(self.name)[0] + "_Calibration"
        configPath = os.path.join("Config", calibrationDir)
        index = fsm.setRootPath(configPath)
        self.calibrationFileComboBox.setModel(fsm)
        self.calibrationFileComboBox.setRootModelIndex(index)
        self.calibrationFileComboBox.currentIndexChanged.connect(self.calibrationFileChanged)
        
        self.calibrationEnabledCheckBox = QtWidgets.QCheckBox("Enabled", self)
        self.calibrationEnabledCheckBox.stateChanged.connect(self.calibrationEnabledStateChanged)
        self.calibrationEnabledCheckBox.setEnabled(False)

        calibrationFrameTypeLabel = QtWidgets.QLabel("Frame Type:", self)
        self.calibrationFrameTypeComboBox = QtWidgets.QComboBox(self)
        self.calibrationFrameTypeComboBox.addItem("ShutterLight")
        self.calibrationFrameTypeComboBox.addItem("ShutterDark")
        self.calibrationFrameTypeComboBox.addItem("Not Required")
        self.calibrationFrameTypeComboBox.addItem("LightAncCombined")
        self.calibrationFrameTypeComboBox.currentIndexChanged.connect(self.calibrationFrameTypeChanged)
        self.calibrationFrameTypeComboBox.setEnabled(False)

        # Config File Settings
        intValidator = QtGui.QIntValidator()
        doubleValidator = QtGui.QDoubleValidator()

        # L1A
        l1aLabel = QtWidgets.QLabel("Level 1A Processing", self)
        l1aLabel_font = l1aLabel.font()
        l1aLabel_font.setPointSize(14)
        l1aLabel_font.setBold(True)
        l1aLabel.setFont(l1aLabel_font)
        l1aSublabel = QtWidgets.QLabel(" Raw binary to HDF5", self)
        # l1aSublabel = QtWidgets.QLabel(" Raw counts to dark-corrected radiometric quanitities", self)
        
        l1aCleanSZALabel = QtWidgets.QLabel("     Solar Zenith Angle Filter", self)        
        self.l1aCleanSZACheckBox = QtWidgets.QCheckBox("", self)            
        if int(ConfigFile.settings["bL1aCleanSZA"]) == 1:
            self.l1aCleanSZACheckBox.setChecked(True)
        l1aCleanSZAMaxLabel = QtWidgets.QLabel("     SZA Max", self)
        self.l1aCleanSZAMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l1aCleanSZAMaxLineEdit.setText(str(ConfigFile.settings["fL1aCleanSZAMax"]))
        self.l1aCleanSZAMaxLineEdit.setValidator(doubleValidator)

        l1aSaveSeaBASSLabel = QtWidgets.QLabel("     Save SeaBASS text file", self)        
        self.l1aSaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)            
        if int(ConfigFile.settings["bL1aSaveSeaBASS"]) == 1:
            self.l1aSaveSeaBASSCheckBox.setChecked(True)     

        self.l1aCleanSZACheckBoxUpdate()   
        self.l1aCleanSZACheckBox.clicked.connect(self.l1aCleanSZACheckBoxUpdate) 
        # self.l1aSaveSeaBASSCheckBox.clicked.connect(self.l1aSaveSeaBASSCheckBoxUpdate)

        # L1b
        l1bLabel = QtWidgets.QLabel("Level 1B Processing", self)
        l1bLabel_font = l1bLabel.font()
        l1bLabel_font.setPointSize(14)
        l1bLabel_font.setBold(True)
        l1bLabel.setFont(l1bLabel_font)
        l1bSublabel = QtWidgets.QLabel(" Raw counts to calibrated radiometric quanitities", self)
        # l1bSublabel = QtWidgets.QLabel(" Interpolation of time stamps and wavebands", self)
        
        
        l1bSaveSeaBASSLabel = QtWidgets.QLabel("     Save SeaBASS text file", self)        
        self.l1bSaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)                    
        if int(ConfigFile.settings["bL1bSaveSeaBASS"]) == 1:
            self.l1bSaveSeaBASSCheckBox.setChecked(True)

        # self.l1bSaveSeaBASSCheckBox.clicked.connect(self.l1bSaveSeaBASSCheckBoxUpdate)        

        # L2
        l2Label = QtWidgets.QLabel("Level 2 Processing", self)
        l2Label_font = l2Label.font()
        l2Label_font.setPointSize(14)
        l2Label_font.setBold(True)
        l2Label.setFont(l2Label_font)
        l2Sublabel = QtWidgets.QLabel(" Shutter dark corrections and data deglitching", self)  

        # Deglitcher
        self.l2DeglitchLabel = QtWidgets.QLabel("     Deglitch data", self)                
        self.l2DeglitchCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2Deglitch"]) == 1:
            self.l2DeglitchCheckBox.setChecked(True)

        self.l2Deglitch1Label = QtWidgets.QLabel("     Noise Threshold Es", self)
        self.l2Deglitch1LineEdit = QtWidgets.QLineEdit(self)
        self.l2Deglitch1LineEdit.setText(str(ConfigFile.settings["fL2Deglitch1"]))
        self.l2Deglitch1LineEdit.setValidator(doubleValidator)

        self.l2Deglitch2Label = QtWidgets.QLabel("     Noise Threshold Li,Lt", self)
        self.l2Deglitch2LineEdit = QtWidgets.QLineEdit(self)
        self.l2Deglitch2LineEdit.setText(str(ConfigFile.settings["fL2Deglitch2"]))
        self.l2Deglitch2LineEdit.setValidator(doubleValidator)
        
        self.l2DeglitchCheckBoxUpdate()      

        l2SaveSeaBASSLabel = QtWidgets.QLabel("     Save SeaBASS text file", self)        
        self.l2SaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)                    
        if int(ConfigFile.settings["bL2SaveSeaBASS"]) == 1:
            self.l2SaveSeaBASSCheckBox.setChecked(True)

        # self.l2SaveSeaBASSCheckBox.clicked.connect(self.l2SaveSeaBASSCheckBoxUpdate)    
        self.l2DeglitchCheckBox.clicked.connect(self.l2DeglitchCheckBoxUpdate)   

        # L2s
        l2sLabel = QtWidgets.QLabel("Level 2s Processing", self)
        l2sLabel_font = l2sLabel.font()
        l2sLabel_font.setPointSize(14)
        l2sLabel_font.setBold(True)
        l2sLabel.setFont(l2sLabel_font)
        l2sSublabel = QtWidgets.QLabel(" Interpolate to common time coordinates. Filter", self)
        l2sSublabel2 = QtWidgets.QLabel(" for rotator and relative solar azimuth.", self)

        # Rotator
        l2sCleanRotatorAngleLabel = QtWidgets.QLabel("     Absolute Rotator Angle Filter", self)        
        self.l2sRotatorHomeAngleLineEdit = QtWidgets.QLineEdit(self)
        self.l2sRotatorHomeAngleLineEdit.setText(str(ConfigFile.settings["fL2sRotatorHomeAngle"]))
        self.l2sRotatorHomeAngleLineEdit.setValidator(doubleValidator)
        
        self.l2sCleanRotatorAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2sCleanRotatorAngle"]) == 1:
            self.l2sCleanRotatorAngleCheckBox.setChecked(True)

        self.l2sRotatorAngleMinLabel = QtWidgets.QLabel("     Rotator Angle Min", self)
        self.l2sRotatorAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l2sRotatorAngleMinLineEdit.setText(str(ConfigFile.settings["fL2sRotatorAngleMin"]))
        self.l2sRotatorAngleMinLineEdit.setValidator(doubleValidator)

        self.l2sRotatorAngleMaxLabel = QtWidgets.QLabel("     Rotator Angle Max", self)
        self.l2sRotatorAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l2sRotatorAngleMaxLineEdit.setText(str(ConfigFile.settings["fL2sRotatorAngleMax"]))
        self.l2sRotatorAngleMaxLineEdit.setValidator(doubleValidator)

        self.l2sRotatorDelayLabel = QtWidgets.QLabel("     Rotator Delay (Seconds)", self)
        self.l2sRotatorDelayLineEdit = QtWidgets.QLineEdit(self)
        self.l2sRotatorDelayLineEdit.setText(str(ConfigFile.settings["fL2sRotatorDelay"]))
        self.l2sRotatorDelayLineEdit.setValidator(doubleValidator)        
        self.l2sCleanRotatorAngleCheckBoxUpdate()        

        # Relative SZA
        l2sCleanSunAngleLabel = QtWidgets.QLabel("Relative Solar Azimuth Filter", self)
        self.l2sCleanSunAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2sCleanSunAngle"]) == 1:
            self.l2sCleanSunAngleCheckBox.setChecked(True)
        self.l2sRotatorHomeAngleLabel = QtWidgets.QLabel("Rotator Home Angle (already set underway?)", self)                

        self.l2sSunAngleMinLabel = QtWidgets.QLabel("Sun Angle Min", self)
        self.l2sSunAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l2sSunAngleMinLineEdit.setText(str(ConfigFile.settings["fL2sSunAngleMin"]))
        self.l2sSunAngleMinLineEdit.setValidator(doubleValidator)

        self.l2sSunAngleMaxLabel = QtWidgets.QLabel("Sun Angle Max", self)
        self.l2sSunAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l2sSunAngleMaxLineEdit.setText(str(ConfigFile.settings["fL2sSunAngleMax"]))
        self.l2sSunAngleMaxLineEdit.setValidator(doubleValidator)

        self.l2sCleanSunAngleCheckBoxUpdate()  

        l2sSaveSeaBASSLabel = QtWidgets.QLabel("     Save SeaBASS text file", self)        
        self.l2sSaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)                    
        if int(ConfigFile.settings["bL2sSaveSeaBASS"]) == 1:
            self.l2sSaveSeaBASSCheckBox.setChecked(True)   

        self.l2sCleanRotatorAngleCheckBox.clicked.connect(self.l2sCleanRotatorAngleCheckBoxUpdate)
        self.l2sCleanSunAngleCheckBox.clicked.connect(self.l2sCleanSunAngleCheckBoxUpdate)
        # self.l2sSaveSeaBASSCheckBox.clicked.connect(self.l2sSaveSeaBASSCheckBoxUpdate)           
       
        # L3a
        l3aLabel = QtWidgets.QLabel("Level 3a Processing", self)
        l3aLabel_font = l3aLabel.font()
        l3aLabel_font.setPointSize(14)
        l3aLabel_font.setBold(True)
        l3aLabel.setFont(l3aLabel_font)
        l3aSublabel = QtWidgets.QLabel(" Interpolation to common wavelengths.", self)
        l3aInterpIntervalLabel = QtWidgets.QLabel("     Interpolation Interval (nm)", self)
        self.l3aInterpIntervalLineEdit = QtWidgets.QLineEdit(self)
        self.l3aInterpIntervalLineEdit.setText(str(ConfigFile.settings["fL3aInterpInterval"]))
        self.l3aInterpIntervalLineEdit.setValidator(doubleValidator)
    
        # l2sLabel2 = QtWidgets.QLabel("Level 2a Processing - Continued", self)
        # l2sLabel2_font = l2sLabel2.font()
        # l2sLabel2_font.setPointSize(14)
        # l2sLabel2.setFont(l2sLabel2_font)
        
        l3aSaveSeaBASSLabel = QtWidgets.QLabel("     Save SeaBASS text file", self)        
        self.l3aSaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)                    
        if int(ConfigFile.settings["bL3aSaveSeaBASS"]) == 1:
            self.l3aSaveSeaBASSCheckBox.setChecked(True)   

        # self.l3aSaveSeaBASSCheckBox.clicked.connect(self.l3aSaveSeaBASSCheckBoxUpdate)   

        # L4     
        l4Label = QtWidgets.QLabel("Level 4 Processing", self)
        l4Label_font = l4Label.font()
        l4Label_font.setPointSize(14)
        l4Label_font.setBold(True)
        l4Label.setFont(l4Label_font)
        l4Sublabel = QtWidgets.QLabel(" Atmos Corr, QA, Reflectances.", self)                   
        
        # Rho Sky & Wind
        l4RhoSkyLabel = QtWidgets.QLabel("Rho Sky", self)
        self.l4RhoSkyLineEdit = QtWidgets.QLineEdit(self)
        self.l4RhoSkyLineEdit.setText(str(ConfigFile.settings["fL4RhoSky"]))
        self.l4RhoSkyLineEdit.setValidator(doubleValidator)

        l4EnableWindSpeedCalculationLabel = QtWidgets.QLabel("Enable Wind Speed Calculation", self)
        self.l4EnableWindSpeedCalculationCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL4EnableWindSpeedCalculation"]) == 1:
            self.l4EnableWindSpeedCalculationCheckBox.setChecked(True)

        self.l4DefaultWindSpeedLabel = QtWidgets.QLabel("Default Wind Speed (m/s)", self)
        self.l4DefaultWindSpeedLineEdit = QtWidgets.QLineEdit(self)
        self.l4DefaultWindSpeedLineEdit.setText(str(ConfigFile.settings["fL4DefaultWindSpeed"]))
        self.l4DefaultWindSpeedLineEdit.setValidator(doubleValidator)
        
        self.l4EnableWindSpeedCalculationCheckBoxUpdate()

        # Meteorology Flags
        l4QualityFlagLabel = QtWidgets.QLabel("Enable Meteorological Flags", self)
        self.l4QualityFlagCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL4EnableQualityFlags"]) == 1:
            self.l4QualityFlagCheckBox.setChecked(True)

        self.l4EsFlagLabel = QtWidgets.QLabel("Es Flag", self)
        self.l4EsFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l4EsFlagLineEdit.setText(str(ConfigFile.settings["fL4SignificantEsFlag"]))
        self.l4EsFlagLineEdit.setValidator(doubleValidator)

        self.l4DawnDuskFlagLabel = QtWidgets.QLabel("Dawn/Dusk Flag", self)
        self.l4DawnDuskFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l4DawnDuskFlagLineEdit.setText(str(ConfigFile.settings["fL4DawnDuskFlag"]))
        self.l4DawnDuskFlagLineEdit.setValidator(doubleValidator)

        self.l4RainfallHumidityFlagLabel = QtWidgets.QLabel("Rainfall/Humidity Flag", self)
        self.l4RainfallHumidityFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l4RainfallHumidityFlagLineEdit.setText(str(ConfigFile.settings["fL4RainfallHumidityFlag"]))
        self.l4RainfallHumidityFlagLineEdit.setValidator(doubleValidator)

        self.l4QualityFlagCheckBoxUpdate()

        # Time Average Rrs
        l4TimeIntervalLabel = QtWidgets.QLabel("Rrs Time Interval (seconds)", self)
        self.l4TimeIntervalLineEdit = QtWidgets.QLineEdit(self)
        self.l4TimeIntervalLineEdit.setText(str(ConfigFile.settings["fL4TimeInterval"]))
        self.l4TimeIntervalLineEdit.setValidator(intValidator)        

        # NIR AtmoCorr
        l4NIRCorrectionLabel = QtWidgets.QLabel("Enable Near-infrared Correction", self)
        self.l4NIRCorrectionCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL4PerformNIRCorrection"]) == 1:
            self.l4NIRCorrectionCheckBox.setChecked(True)

        self.l4EnablePercentLtLabel = QtWidgets.QLabel("Enable Percent Lt Calculation", self)
        self.l4EnablePercentLtCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL4EnablePercentLt"]) == 1:
           self.l4EnablePercentLtCheckBox.setChecked(True)

        # Set percentage for Rrs calculation
        l4PercentLtLabel = QtWidgets.QLabel("Percent Lt", self)
        self.l4PercentLtLineEdit = QtWidgets.QLineEdit(self)
        self.l4PercentLtLineEdit.setText(str(ConfigFile.settings["fL4PercentLt"]))
        self.l4PercentLtLineEdit.setValidator(doubleValidator)
        l4SaveSeaBASSLabel = QtWidgets.QLabel("Save SeaBASS text file", self)     

        self.l4SaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)    
        self.l4SaveSeaBASSCheckBox.clicked.connect(self.l4SaveSeaBASSCheckBoxUpdate)        
        if int(ConfigFile.settings["bL4SaveSeaBASS"]) == 1:
            self.l4SaveSeaBASSCheckBox.setChecked(True)

        self.l4QualityFlagCheckBox.clicked.connect(self.l4QualityFlagCheckBoxUpdate)
        self.l4EnableWindSpeedCalculationCheckBox.clicked.connect(self.l4EnableWindSpeedCalculationCheckBoxUpdate)
        self.l4NIRCorrectionCheckBox.clicked.connect(self.l4NIRCorrectionCheckBoxUpdate)
        self.l4EnablePercentLtCheckBox.clicked.connect(self.l4EnablePercentLtCheckBoxUpdate)

        self.saveButton = QtWidgets.QPushButton("Save")
        self.cancelButton = QtWidgets.QPushButton("Cancel")                      
            
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        # print("ConfigWindow - Create Layout")

        # Overall box?
        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(nameLabel)
        # VBox.addSpacing(5)

        # Vertical Box (left)
        VBox1 = QtWidgets.QVBoxLayout()

        # Calibration Setup
        VBox1.addWidget(self.addCalibrationFileButton)
        # Horizontal Box 
        calHBox = QtWidgets.QHBoxLayout()
        calHBox.addWidget(self.calibrationFileComboBox)
        calHBox.addWidget(self.calibrationEnabledCheckBox)
        VBox1.addLayout(calHBox)   

        VBox1.addWidget(calibrationFrameTypeLabel)
        VBox1.addWidget(self.calibrationFrameTypeComboBox)

        VBox1.addSpacing(12)

        # L1a
        VBox1.addWidget(l1aLabel)
        VBox1.addWidget(l1aSublabel)
               
        VBox1.addWidget(l1aCleanSZALabel)
        # Horizontal Box; SZA Filter
        szaHBox = QtWidgets.QHBoxLayout()
        szaHBox.addWidget(l1aCleanSZAMaxLabel)
        szaHBox.addWidget(self.l1aCleanSZACheckBox)
        szaHBox.addWidget(self.l1aCleanSZAMaxLineEdit)        
        VBox1.addLayout(szaHBox)

        # Horizontal Box; Save SeaBASS
        l1aSeaBASSHBox = QtWidgets.QHBoxLayout()
        l1aSeaBASSHBox.addWidget(l1aSaveSeaBASSLabel)
        l1aSeaBASSHBox.addWidget(self.l1aSaveSeaBASSCheckBox)    
        VBox1.addLayout(l1aSeaBASSHBox)        
        
        VBox1.addSpacing(20)

        # L1b
        VBox1.addWidget(l1bLabel)
        VBox1.addWidget(l1bSublabel)
        
        # Horizontal Box 
        l1bSeaBASSHBox = QtWidgets.QHBoxLayout()
        l1bSeaBASSHBox.addWidget(l1bSaveSeaBASSLabel)
        l1bSeaBASSHBox.addWidget(self.l1bSaveSeaBASSCheckBox)    
        VBox1.addLayout(l1bSeaBASSHBox)

        VBox1.addSpacing(20)

        # L2
        VBox1.addWidget(l2Label)
        VBox1.addWidget(l2Sublabel)
        
        # Deglitcher
        deglitchHBox = QtWidgets.QHBoxLayout()
        deglitchHBox.addWidget(self.l2DeglitchLabel)
        deglitchHBox.addWidget(self.l2DeglitchCheckBox)
        VBox1.addLayout(deglitchHBox)

        deglitch1HBox = QtWidgets.QHBoxLayout()
        deglitch1HBox.addWidget(self.l2Deglitch1Label)
        deglitch1HBox.addWidget(self.l2Deglitch1LineEdit)
        VBox1.addLayout(deglitch1HBox)
        
        deglitch2HBox = QtWidgets.QHBoxLayout()
        deglitch2HBox.addWidget(self.l2Deglitch2Label)
        deglitch2HBox.addWidget(self.l2Deglitch2LineEdit)
        VBox1.addLayout(deglitch2HBox)

        # Horizontal Box 
        l2SeaBASSHBox = QtWidgets.QHBoxLayout()
        l2SeaBASSHBox.addWidget(l2SaveSeaBASSLabel)
        l2SeaBASSHBox.addWidget(self.l2SaveSeaBASSCheckBox)    
        VBox1.addLayout(l2SeaBASSHBox)

        # Middle box
        VBox2 = QtWidgets.QVBoxLayout()
        VBox2.setAlignment(QtCore.Qt.AlignBottom)

        # L2s
        VBox2.addWidget(l2sLabel)
        VBox2.addWidget(l2sSublabel)
        VBox2.addWidget(l2sSublabel2)

        # Rotator
        rotateHBox = QtWidgets.QHBoxLayout()
        rotateHBox.addWidget(l2sCleanRotatorAngleLabel)
        rotateHBox.addWidget(self.l2sCleanRotatorAngleCheckBox)
        VBox2.addLayout(rotateHBox)
        RotMinHBox = QtWidgets.QHBoxLayout()
        RotMinHBox.addWidget(self.l2sRotatorAngleMinLabel)
        RotMinHBox.addWidget(self.l2sRotatorAngleMinLineEdit)
        VBox2.addLayout(RotMinHBox)
        RotMaxHBox = QtWidgets.QHBoxLayout()
        RotMaxHBox.addWidget(self.l2sRotatorAngleMaxLabel)
        RotMaxHBox.addWidget(self.l2sRotatorAngleMaxLineEdit)
        VBox2.addLayout(RotMaxHBox)        
        RotatorDelayHBox = QtWidgets.QHBoxLayout()
        RotatorDelayHBox.addWidget(self.l2sRotatorDelayLabel)
        RotatorDelayHBox.addWidget(self.l2sRotatorDelayLineEdit)
        VBox2.addLayout(RotatorDelayHBox)

        
        # Relative SZA
        CleanSunAngleHBox = QtWidgets.QHBoxLayout()
        CleanSunAngleHBox.addWidget(l2sCleanSunAngleLabel)
        CleanSunAngleHBox.addWidget(self.l2sCleanSunAngleCheckBox)
        VBox2.addLayout(CleanSunAngleHBox)                
        VBox2.addWidget(self.l2sRotatorHomeAngleLabel)
        VBox2.addWidget(self.l2sRotatorHomeAngleLineEdit)        
        VBox2.addWidget(self.l2sSunAngleMinLabel)
        VBox2.addWidget(self.l2sSunAngleMinLineEdit)
        VBox2.addWidget(self.l2sSunAngleMaxLabel)
        VBox2.addWidget(self.l2sSunAngleMaxLineEdit)

        # Horizontal Box 
        l2sSeaBASSHBox = QtWidgets.QHBoxLayout()
        l2sSeaBASSHBox.addWidget(l2sSaveSeaBASSLabel)
        l2sSeaBASSHBox.addWidget(self.l2sSaveSeaBASSCheckBox)    
        VBox2.addLayout(l2sSeaBASSHBox)     

        VBox2.addSpacing(20)   

        #L3a        
        VBox2.addWidget(l3aLabel)
        VBox2.addWidget(l3aSublabel)

        interpHBox = QtWidgets.QHBoxLayout()
        interpHBox.addWidget(l3aInterpIntervalLabel)
        interpHBox.addWidget(self.l3aInterpIntervalLineEdit)
        VBox2.addLayout(interpHBox)

        # Horizontal Box 
        l3aSeaBASSHBox = QtWidgets.QHBoxLayout()
        l3aSeaBASSHBox.addWidget(l3aSaveSeaBASSLabel)
        l3aSeaBASSHBox.addWidget(self.l3aSaveSeaBASSCheckBox)    
        VBox2.addLayout(l3aSeaBASSHBox)

        # VBox2.addSpacing(5)
        
        # Right box
        VBox3 = QtWidgets.QVBoxLayout()
        VBox3.setAlignment(QtCore.Qt.AlignBottom)

        # L4
        VBox3.addWidget(l4Label)
        VBox3.addWidget(l4Sublabel)
        
        # Rho Sky & Wind
        VBox3.addWidget(l4RhoSkyLabel)
        VBox3.addWidget(self.l4RhoSkyLineEdit)
        WindSpeedHBox = QtWidgets.QHBoxLayout()
        WindSpeedHBox.addWidget(l4EnableWindSpeedCalculationLabel)
        WindSpeedHBox.addWidget(self.l4EnableWindSpeedCalculationCheckBox)
        VBox3.addLayout(WindSpeedHBox)             
        VBox3.addWidget(self.l4DefaultWindSpeedLabel)
        VBox3.addWidget(self.l4DefaultWindSpeedLineEdit)

        VBox3.addSpacing(5)

        # Meteorology Flags
        QualityFlagHBox = QtWidgets.QHBoxLayout()
        QualityFlagHBox.addWidget(l4QualityFlagLabel)
        QualityFlagHBox.addWidget(self.l4QualityFlagCheckBox)
        VBox3.addLayout(QualityFlagHBox)         
        VBox3.addWidget(self.l4EsFlagLabel)
        VBox3.addWidget(self.l4EsFlagLineEdit)
        VBox3.addWidget(self.l4DawnDuskFlagLabel)
        VBox3.addWidget(self.l4DawnDuskFlagLineEdit)
        VBox3.addWidget(self.l4RainfallHumidityFlagLabel)
        VBox3.addWidget(self.l4RainfallHumidityFlagLineEdit)

        VBox3.addSpacing(5)

        # Time Average Rrs
        VBox3.addWidget(l4TimeIntervalLabel)
        VBox3.addWidget(self.l4TimeIntervalLineEdit)

        VBox3.addSpacing(5)

        # NIR AtmoCorr
        NIRCorrectionHBox = QtWidgets.QHBoxLayout()
        NIRCorrectionHBox.addWidget(l4NIRCorrectionLabel)
        NIRCorrectionHBox.addWidget(self.l4NIRCorrectionCheckBox)
        VBox3.addLayout(NIRCorrectionHBox)         

        VBox3.addSpacing(5)
        
        # Percent Light; Hooker & Morel 2003
        PercentLtHBox = QtWidgets.QHBoxLayout()
        PercentLtHBox.addWidget(self.l4EnablePercentLtLabel)
        PercentLtHBox.addWidget(self.l4EnablePercentLtCheckBox)
        VBox3.addLayout(PercentLtHBox)  
        VBox3.addWidget(l4PercentLtLabel)
        VBox3.addWidget(self.l4PercentLtLineEdit)

        VBox3.addSpacing(5)
        
        # Horizontal Box; Save SeaBASS
        l4SeaBASSHBox = QtWidgets.QHBoxLayout()
        l4SeaBASSHBox.addWidget(l4SaveSeaBASSLabel)
        l4SeaBASSHBox.addWidget(self.l4SaveSeaBASSCheckBox)    
        VBox3.addLayout(l4SeaBASSHBox)
        
        # VBox3.addSpacing(30)

        # ?
        hBox = QtWidgets.QHBoxLayout()
        hBox.addLayout(VBox1)
        # hBox.addSpacing(30)
        hBox.addLayout(VBox2)        
        # hBox.addSpacing(30)
        hBox.addLayout(VBox3)    

        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.cancelButton)

        # Adds hBox and saveHBox, but what about VBox1 and VBox2?
        VBox.addLayout(hBox)
        VBox.addLayout(saveHBox)

        self.setLayout(VBox)
        self.setGeometry(300, 100, 0, 0)
        self.setWindowTitle('Edit Configuration')
        #self.show()

        # print("ConfigWindow - initUI Done")


    def addCalibrationFileButtonPressed(self):
        print("CalibrationEditWindow - Add Calibration File Pressed")
        fnames = QtWidgets.QFileDialog.getOpenFileNames(self, "Add Calibration Files")
        print(fnames)

        configName = self.name
        calibrationDir = os.path.splitext(configName)[0] + "_Calibration"
        configPath = os.path.join("Config", calibrationDir)
        for src in fnames[0]:
            (dirpath, filename) = os.path.split(src)
            dest = os.path.join(configPath, filename)
            print(src)
            print(dest)
            shutil.copy(src, dest)
        #print(fp)


    def getCalibrationSettings(self):
        print("CalibrationEditWindow - getCalibrationSettings")
        ConfigFile.refreshCalibrationFiles()
        calFileName = self.calibrationFileComboBox.currentText()
        calConfig = ConfigFile.getCalibrationConfig(calFileName)
        #print(calConfig["enabled"])
        #print(calConfig["frameType"])
        self.calibrationEnabledCheckBox.blockSignals(True)
        self.calibrationFrameTypeComboBox.blockSignals(True)

        self.calibrationEnabledCheckBox.setChecked(bool(calConfig["enabled"]))
        index = self.calibrationFrameTypeComboBox.findText(str(calConfig["frameType"]))
        self.calibrationFrameTypeComboBox.setCurrentIndex(index)

        self.calibrationEnabledCheckBox.blockSignals(False)
        self.calibrationFrameTypeComboBox.blockSignals(False)


    def setCalibrationSettings(self):
        print("CalibrationEditWindow - setCalibrationSettings")
        calFileName = self.calibrationFileComboBox.currentText()
        enabled = self.calibrationEnabledCheckBox.isChecked()
        frameType = self.calibrationFrameTypeComboBox.currentText()
        ConfigFile.setCalibrationConfig(calFileName, enabled, frameType)


    def calibrationFileChanged(self, i):
        print("CalibrationEditWindow - Calibration File Changed")
        print("Current index",i,"selection changed ", self.calibrationFileComboBox.currentText())
        calFileName = self.calibrationFileComboBox.currentText()
        calDir = ConfigFile.getCalibrationDirectory()
        calPath = os.path.join(calDir, calFileName)
        #print("calPath: " + calPath)
        if os.path.isfile(calPath):
            self.getCalibrationSettings()
            self.calibrationEnabledCheckBox.setEnabled(True)
            self.calibrationFrameTypeComboBox.setEnabled(True)
        else:
            self.calibrationEnabledCheckBox.setEnabled(False)
            self.calibrationFrameTypeComboBox.setEnabled(False)


    def calibrationEnabledStateChanged(self):
        print("CalibrationEditWindow - Calibration Enabled State Changed")
        print(self.calibrationEnabledCheckBox.isChecked())
        self.setCalibrationSettings()

    def calibrationFrameTypeChanged(self, i):
        print("CalibrationEditWindow - Calibration Frame Type Changed")
        print("Current index",i,"selection changed ", self.calibrationFrameTypeComboBox.currentText())
        self.setCalibrationSettings()


    def l1aCleanSZACheckBoxUpdate(self):
        print("ConfigWindow - l1aCleanSZAAngleCheckBoxUpdate")

        disabled = (not self.l1aCleanSZACheckBox.isChecked())
        self.l1aCleanSZAMaxLineEdit.setDisabled(disabled)

    
    def l1aSaveSeaBASSCheckBoxUpdate(self):
        print("ConfigWindow - l1aSaveSeaBASSCheckBoxUpdate")

        # disabled = (not self.l1aSaveSeaBASSCheckBox.isChecked())
        # self.l1aSaveSeaBASSLabel.setDisabled(disabled)

    def l1bSaveSeaBASSCheckBoxUpdate(self):
        print("ConfigWindow - l1bSaveSeaBASSCheckBoxUpdate")

    def l2DeglitchCheckBoxUpdate(self):
        print("ConfigWindow - l2DeglitchCheckBoxUpdate")
        
        disabled = (not self.l2DeglitchCheckBox.isChecked())
        self.l2Deglitch1Label.setDisabled(disabled)
        self.l2Deglitch1LineEdit.setDisabled(disabled)
        self.l2Deglitch2Label.setDisabled(disabled)
        self.l2Deglitch2LineEdit.setDisabled(disabled)        

    def l2sCleanRotatorAngleCheckBoxUpdate(self):
        print("ConfigWindow - l2sCleanRotatorAngleCheckBoxUpdate")
        
        disabled = (not self.l2sCleanRotatorAngleCheckBox.isChecked())
        self.l2sRotatorAngleMinLabel.setDisabled(disabled)
        self.l2sRotatorAngleMinLineEdit.setDisabled(disabled)
        self.l2sRotatorAngleMaxLabel.setDisabled(disabled)
        self.l2sRotatorAngleMaxLineEdit.setDisabled(disabled)
        self.l2sRotatorDelayLabel.setDisabled(disabled)
        self.l2sRotatorDelayLineEdit.setDisabled(disabled)

    def l2sCleanSunAngleCheckBoxUpdate(self):
        print("ConfigWindow - l2sCleanSunAngleCheckBoxUpdate")
        
        disabled = (not self.l2sCleanSunAngleCheckBox.isChecked())
        self.l2sSunAngleMinLabel.setDisabled(disabled)
        self.l2sSunAngleMinLineEdit.setDisabled(disabled)
        self.l2sSunAngleMaxLabel.setDisabled(disabled)
        self.l2sSunAngleMaxLineEdit.setDisabled(disabled)
        self.l2sRotatorHomeAngleLabel.setDisabled(disabled)
        self.l2sRotatorHomeAngleLineEdit.setDisabled(disabled)

    def l4EnableWindSpeedCalculationCheckBoxUpdate(self):
        print("ConfigWindow - l4EnableWindSpeedCalculationCheckBoxUpdate")
        # print("This should do something....?")
        
        disabled = (not self.l4EnableWindSpeedCalculationCheckBox.isChecked())
        self.l4DefaultWindSpeedLabel.setDisabled(disabled)
        self.l4DefaultWindSpeedLineEdit.setDisabled(disabled)

    def l4QualityFlagCheckBoxUpdate(self):
        print("ConfigWindow - l4QualityFlagCheckBoxUpdate")
        # print("This should do something....?")

        disabled = (not self.l4QualityFlagCheckBox.isChecked())
        self.l4EsFlagLabel.setDisabled(disabled)
        self.l4EsFlagLineEdit.setDisabled(disabled)
        self.l4DawnDuskFlagLabel.setDisabled(disabled)
        self.l4DawnDuskFlagLineEdit.setDisabled(disabled)
        self.l4RainfallHumidityFlagLabel.setDisabled(disabled)
        self.l4RainfallHumidityFlagLineEdit.setDisabled(disabled)
    
    def l4NIRCorrectionCheckBoxUpdate(self):
        print("ConfigWindow - l4NIRCorrectionCheckBoxUpdate")
        # print("This should do something....?")

    def l4EnablePercentLtCheckBoxUpdate(self):
        print("ConfigWindow - l4EnablePercentLtCheckBoxUpdate")
        # print("This should do something....?")        
        
        disabled = (not self.l4EnablePercentLtCheckBox.isChecked())
        self.l4PercentLtLabel.setDisabled(disabled)
        self.l4PercentLtLineEdit.setDisabled(disabled)        

    def l4SaveSeaBASSCheckBoxUpdate(self):
        print("ConfigWindow - l4SaveSeaBASSCheckBoxUpdate")


    def saveButtonPressed(self):
        print("ConfigWindow - Save Pressed")

        ConfigFile.settings["bL1aCleanSZA"] = int(self.l1aCleanSZACheckBox.isChecked())
        ConfigFile.settings["fL1aCleanSZAMax"] = float(self.l1aCleanSZAMaxLineEdit.text())
        ConfigFile.settings["bL1aSaveSeaBASS"] = int(self.l1aSaveSeaBASSCheckBox.isChecked())
                
        ConfigFile.settings["bL1bSaveSeaBASS"] = int(self.l1bSaveSeaBASSCheckBox.isChecked())

        ConfigFile.settings["bL2Deglitch"] = int(self.l2DeglitchCheckBox.isChecked()) 
        ConfigFile.settings["bL2SaveSeaBASS"] = int(self.l2SaveSeaBASSCheckBox.isChecked())
        
        ConfigFile.settings["bl2sCleanRotatorAngle"] = int(self.l2sCleanRotatorAngleCheckBox.isChecked())        
        ConfigFile.settings["fl2sRotatorAngleMin"] = float(self.l2sRotatorAngleMinLineEdit.text())
        ConfigFile.settings["fl2sRotatorAngleMax"] = float(self.l2sRotatorAngleMaxLineEdit.text())        
        ConfigFile.settings["fl2sRotatorDelay"] = float(self.l2sRotatorDelayLineEdit.text())     
        ConfigFile.settings["bl2sCleanSunAngle"] = int(self.l2sCleanSunAngleCheckBox.isChecked())
        ConfigFile.settings["fl2sRotatorHomeAngle"] = float(self.l2sRotatorHomeAngleLineEdit.text())
        ConfigFile.settings["fl2sSunAngleMin"] = float(self.l2sSunAngleMinLineEdit.text())
        ConfigFile.settings["fl2sSunAngleMax"] = float(self.l2sSunAngleMaxLineEdit.text())
        ConfigFile.settings["b2sSaveSeaBASS"] = int(self.l2sSaveSeaBASSCheckBox.isChecked())

        ConfigFile.settings["fL3aInterpInterval"] = float(self.l3aInterpIntervalLineEdit.text())
        ConfigFile.settings["fL3aInterpInterval"] = float(self.l3aInterpIntervalLineEdit.text())
        ConfigFile.settings["bL2sSaveSeaBASS"] = int(self.l2sSaveSeaBASSCheckBox.isChecked())

        ConfigFile.settings["fl4RhoSky"] = float(self.l4RhoSkyLineEdit.text())
        ConfigFile.settings["bl4EnableWindSpeedCalculation"] = int(self.l4EnableWindSpeedCalculationCheckBox.isChecked())
        ConfigFile.settings["fl4DefaultWindSpeed"] = float(self.l4DefaultWindSpeedLineEdit.text())
        ConfigFile.settings["bl4EnableQualityFlags"] = int(self.l4QualityFlagCheckBox.isChecked())
        ConfigFile.settings["fl4SignificantEsFlag"] = float(self.l4EsFlagLineEdit.text())
        ConfigFile.settings["fl4DawnDuskFlag"] = float(self.l4DawnDuskFlagLineEdit.text())
        ConfigFile.settings["fl4RainfallHumidityFlag"] = float(self.l4RainfallHumidityFlagLineEdit.text())
        ConfigFile.settings["fl4TimeInterval"] = int(self.l4TimeIntervalLineEdit.text())                
        ConfigFile.settings["bl4PerformNIRCorrection"] = int(self.l4NIRCorrectionCheckBox.isChecked())
        ConfigFile.settings["bl4EnablePercentLtCorrection"] = int(self.l4EnablePercentLtCheckBox.isChecked())
        ConfigFile.settings["fl4PercentLt"] = float(self.l4PercentLtLineEdit.text())
        ConfigFile.settings["bl4SaveSeaBASS"] = int(self.l4SaveSeaBASSCheckBox.isChecked())

        ConfigFile.saveConfig(self.name)

        QtWidgets.QMessageBox.about(self, "Edit Config File", "Config File Saved")
        self.close()


    def cancelButtonPressed(self):
        print("ConfigWindow - Cancel Pressed")
        self.close()

