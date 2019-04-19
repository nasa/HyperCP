
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
        print("ConfigWindow - initUI")
        #self.label = QtWidgets.QLabel("Popup", self)

        self.nameLabel = QtWidgets.QLabel("Editing: " + self.name, self)

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

        # L0
        l0Label = QtWidgets.QLabel("Level 0 - Preprocessing", self)
        l0Sublabel = QtWidgets.QLabel(" Raw binary to HDF; no parameters to set", self)

        # L1A
        l1aLabel = QtWidgets.QLabel("Level 1A Processing", self)
        l1aSublabel = QtWidgets.QLabel("     Raw counts to dark-corrected radiometric quanitities", self)
        
        l1aCleanSZALabel = QtWidgets.QLabel("     Solar Zenith Angle Filter", self)        
        self.l1aCleanSZACheckBox = QtWidgets.QCheckBox("", self)            
        if int(ConfigFile.settings["bL1aCleanSZA"]) == 1:
            self.l1aCleanSZACheckBox.setChecked(True)
        self.l1aCleanSZAMaxLabel = QtWidgets.QLabel("     SZA Max", self)
        self.l1aCleanSZAMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l1aCleanSZAMaxLineEdit.setText(str(ConfigFile.settings["fL1aCleanSZAMax"]))
        self.l1aCleanSZAMaxLineEdit.setValidator(doubleValidator)

        # L1b
        l1bLabel = QtWidgets.QLabel("Level 1B Processing", self)
        l1bSublabel = QtWidgets.QLabel("     Interpolation of time stamps and wavebands", self)
        self.l1bInterpIntervalLabel = QtWidgets.QLabel("     Interpolation Interval (nm)", self)
        self.l1bInterpIntervalLineEdit = QtWidgets.QLineEdit(self)
        self.l1bInterpIntervalLineEdit.setText(str(ConfigFile.settings["fL1bInterpInterval"]))
        self.l1bInterpIntervalLineEdit.setValidator(doubleValidator)

        # L2
        l2Label = QtWidgets.QLabel("Level 2 Processing", self)
        l2Sublabel = QtWidgets.QLabel("     Quality control and reflectance calculation", self)

        # Rotator
        l2CleanRotatorAngleLabel = QtWidgets.QLabel("     Absolute Rotator Angle Filter", self)
        self.l2RotatorHomeAngleLabel = QtWidgets.QLabel("     Rotator Home Angle", self)
        self.l2RotatorHomeAngleLineEdit = QtWidgets.QLineEdit(self)
        self.l2RotatorHomeAngleLineEdit.setText(str(ConfigFile.settings["fL2RotatorHomeAngle"]))
        self.l2RotatorHomeAngleLineEdit.setValidator(doubleValidator)
        
        self.l2CleanRotatorAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2CleanRotatorAngle"]) == 1:
            self.l2CleanRotatorAngleCheckBox.setChecked(True)

        self.l2RotatorAngleMinLabel = QtWidgets.QLabel("     Rotator Angle Min", self)
        self.l2RotatorAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l2RotatorAngleMinLineEdit.setText(str(ConfigFile.settings["fL2RotatorAngleMin"]))
        self.l2RotatorAngleMinLineEdit.setValidator(doubleValidator)

        self.l2RotatorAngleMaxLabel = QtWidgets.QLabel("     Rotator Angle Max", self)
        self.l2RotatorAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l2RotatorAngleMaxLineEdit.setText(str(ConfigFile.settings["fL2RotatorAngleMax"]))
        self.l2RotatorAngleMaxLineEdit.setValidator(doubleValidator)

        self.l2RotatorDelayLabel = QtWidgets.QLabel("     Rotator Delay (Seconds)", self)
        self.l2RotatorDelayLineEdit = QtWidgets.QLineEdit(self)
        self.l2RotatorDelayLineEdit.setText(str(ConfigFile.settings["fL2RotatorDelay"]))
        self.l2RotatorDelayLineEdit.setValidator(doubleValidator)

        self.l2CleanRotatorAngleCheckBoxUpdate()

        # Relative SZA 
        l2CleanSunAngleLabel = QtWidgets.QLabel("Relative Solar Azimuth Filter", self)
        self.l2CleanSunAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2CleanSunAngle"]) == 1:
            self.l2CleanSunAngleCheckBox.setChecked(True)

        self.l2SunAngleMinLabel = QtWidgets.QLabel("Sun Angle Min", self)
        self.l2SunAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l2SunAngleMinLineEdit.setText(str(ConfigFile.settings["fL2SunAngleMin"]))
        self.l2SunAngleMinLineEdit.setValidator(doubleValidator)

        self.l2SunAngleMaxLabel = QtWidgets.QLabel("Sun Angle Max", self)
        self.l2SunAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l2SunAngleMaxLineEdit.setText(str(ConfigFile.settings["fL2SunAngleMax"]))
        self.l2SunAngleMaxLineEdit.setValidator(doubleValidator)

        self.l2CleanSunAngleCheckBoxUpdate()       

        # Rho Sky & Wind
        l2RhoSkyLabel = QtWidgets.QLabel("Rho Sky", self)
        self.l2RhoSkyLineEdit = QtWidgets.QLineEdit(self)
        self.l2RhoSkyLineEdit.setText(str(ConfigFile.settings["fL2RhoSky"]))
        self.l2RhoSkyLineEdit.setValidator(doubleValidator)

        l2EnableWindSpeedCalculationLabel = QtWidgets.QLabel("Enable Wind Speed Calculation", self)
        self.l2EnableWindSpeedCalculationCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2EnableWindSpeedCalculation"]) == 1:
            self.l2EnableWindSpeedCalculationCheckBox.setChecked(True)

        self.l2DefaultWindSpeedLabel = QtWidgets.QLabel("Default Wind Speed (m/s)", self)
        self.l2DefaultWindSpeedLineEdit = QtWidgets.QLineEdit(self)
        self.l2DefaultWindSpeedLineEdit.setText(str(ConfigFile.settings["fL2DefaultWindSpeed"]))
        self.l2DefaultWindSpeedLineEdit.setValidator(doubleValidator)
        
        self.l2EnableWindSpeedCalculationCheckBoxUpdate()

        # Meteorology Flags
        l2QualityFlagLabel = QtWidgets.QLabel("Enable Meteorological Flags", self)
        self.l2QualityFlagCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2EnableQualityFlags"]) == 1:
            self.l2QualityFlagCheckBox.setChecked(True)

        self.l2EsFlagLabel = QtWidgets.QLabel("Es Flag", self)
        self.l2EsFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l2EsFlagLineEdit.setText(str(ConfigFile.settings["fL2SignificantEsFlag"]))
        self.l2EsFlagLineEdit.setValidator(doubleValidator)

        self.l2DawnDuskFlagLabel = QtWidgets.QLabel("Dawn/Dusk Flag", self)
        self.l2DawnDuskFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l2DawnDuskFlagLineEdit.setText(str(ConfigFile.settings["fL2DawnDuskFlag"]))
        self.l2DawnDuskFlagLineEdit.setValidator(doubleValidator)

        self.l2RainfallHumidityFlagLabel = QtWidgets.QLabel("Rainfall/Humidity Flag", self)
        self.l2RainfallHumidityFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l2RainfallHumidityFlagLineEdit.setText(str(ConfigFile.settings["fL2RainfallHumidityFlag"]))
        self.l2RainfallHumidityFlagLineEdit.setValidator(doubleValidator)

        self.l2QualityFlagCheckBoxUpdate()

        # Time Average Rrs
        l2TimeIntervalLabel = QtWidgets.QLabel("Rrs Time Interval (seconds)", self)
        self.l2TimeIntervalLineEdit = QtWidgets.QLineEdit(self)
        self.l2TimeIntervalLineEdit.setText(str(ConfigFile.settings["fL2TimeInterval"]))
        self.l2TimeIntervalLineEdit.setValidator(intValidator)        

        # NIR AtmoCorr
        l2NIRCorrectionLabel = QtWidgets.QLabel("Enable Near-infrared Correction", self)
        self.l2NIRCorrectionCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2PerformNIRCorrection"]) == 1:
            self.l2NIRCorrectionCheckBox.setChecked(True)

        l2EnablePercentLtLabel = QtWidgets.QLabel("Level 4 - Enable Percent Lt Calculation", self)
        self.l2EnablePercentLtCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2EnablePercentLt"]) == 1:
           self.l2EnablePercentLtCheckBox.setChecked(True)

        # Set percentage for Rrs calculation
        l2PercentLtLabel = QtWidgets.QLabel("Percent Lt", self)
        self.l2PercentLtLineEdit = QtWidgets.QLineEdit(self)
        self.l2PercentLtLineEdit.setText(str(ConfigFile.settings["fL2PercentLt"]))
        self.l2PercentLtLineEdit.setValidator(doubleValidator)


        self.saveButton = QtWidgets.QPushButton("Save")
        self.cancelButton = QtWidgets.QPushButton("Cancel")
      
        self.l2CleanRotatorAngleCheckBox.clicked.connect(self.l2CleanRotatorAngleCheckBoxUpdate)
        self.l2CleanSunAngleCheckBox.clicked.connect(self.l2CleanSunAngleCheckBoxUpdate)
        self.l2QualityFlagCheckBox.clicked.connect(self.l2QualityFlagCheckBoxUpdate)
        self.l2EnableWindSpeedCalculationCheckBox.clicked.connect(self.l2EnableWindSpeedCalculationCheckBoxUpdate)
            
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        print("ConfigWindow - Create Layout")

        # Overall box??
        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(self.nameLabel)
        VBox.addSpacing(10)

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

        VBox1.addSpacing(25)

        # L0
        VBox1.addWidget(l0Label)
        VBox1.addWidget(l0Sublabel)
        
        VBox1.addSpacing(10)

        # L1a
        VBox1.addWidget(l1aLabel)
        VBox1.addWidget(l1aSublabel)

        # SZA Filter
        VBox1.addWidget(l1aCleanSZALabel)
        # Horizontal Box 
        szaHBox = QtWidgets.QHBoxLayout()
        szaHBox.addWidget(self.l1aCleanSZAMaxLabel)
        szaHBox.addWidget(self.l1aCleanSZACheckBox)
        szaHBox.addWidget(self.l1aCleanSZAMaxLineEdit)        
        VBox1.addLayout(szaHBox)
        
        VBox1.addSpacing(10)

        # L1b
        VBox1.addWidget(l1bLabel)
        VBox1.addWidget(l1bSublabel)
        interpHBox = QtWidgets.QHBoxLayout()
        interpHBox.addWidget(self.l1bInterpIntervalLabel)
        interpHBox.addWidget(self.l1bInterpIntervalLineEdit)
        VBox1.addLayout(interpHBox)

        # L2
        VBox1.addWidget(l2Label)
        VBox1.addWidget(l2Sublabel)

        # Rotator
        rotateHBox = QtWidgets.QHBoxLayout()
        rotateHBox.addWidget(self.l2CleanRotatorAngleLabel)
        rotateHBox.addWidget(self.l2CleanRotatorAngleCheckBox)
        VBox1.addLayout(rotateHBox)
        VBox1.addWidget(self.l2RotatorAngleMinLabel)
        VBox1.addWidget(self.l2RotatorAngleMinLineEdit)
        VBox1.addWidget(self.l2RotatorAngleMaxLabel)
        VBox1.addWidget(self.l2RotatorAngleMaxLineEdit)
        VBox1.addWidget(self.l2RotatorDelayLabel)
        VBox1.addWidget(self.l2RotatorDelayLineEdit)

        # Right box
        VBox2 = QtWidgets.QVBoxLayout()
        VBox2.setAlignment(QtCore.Qt.AlignBottom)

        VBox2.addSpacing(15)            
        VBox2.addWidget(self.l2Label)
        VBox2.addWidget(self.l2Sublabel)

        # Relative SZA
        VBox2.addWidget(self.l2RotatorHomeAngleLabel)
        VBox2.addWidget(self.l2RotatorHomeAngleLineEdit)
        VBox2.addWidget(self.l2CleanSunAngleLabel)
        VBox2.addWidget(self.l2CleanSunAngleCheckBox)
        VBox2.addWidget(self.l2SunAngleMinLabel)
        VBox2.addWidget(self.l2SunAngleMinLineEdit)
        VBox2.addWidget(self.l2SunAngleMaxLabel)
        VBox2.addWidget(self.l2SunAngleMaxLineEdit)

        # Rho Sky & Wind
        VBox2.addWidget(l2RhoSkyLabel)
        VBox2.addWidget(self.l2RhoSkyLineEdit)
        VBox2.addWidget(l2EnableWindSpeedCalculationLabel)
        VBox2.addWidget(self.l2EnableWindSpeedCalculationCheckBox)        
        VBox2.addWidget(self.l2DefaultWindSpeedLabel)
        VBox2.addWidget(self.l2DefaultWindSpeedLineEdit)

        # Meteorology Flags
        VBox2.addWidget(l2QualityFlagLabel)
        VBox2.addWidget(self.l2QualityFlagCheckBox)
        VBox2.addWidget(self.l2EsFlagLabel)
        VBox2.addWidget(self.l2EsFlagLineEdit)
        VBox2.addWidget(self.l2DawnDuskFlagLabel)
        VBox2.addWidget(self.l2DawnDuskFlagLineEdit)
        VBox2.addWidget(self.l2RainfallHumidityFlagLabel)
        VBox2.addWidget(self.l2RainfallHumidityFlagLineEdit)

        VBox2.addSpacing(10)

        # Time Average Rrs
        VBox2.addWidget(l2TimeIntervalLabel)
        VBox2.addWidget(self.l2TimeIntervalLineEdit)

        # NIR AtmoCorr
        VBox2.addWidget(l2NIRCorrectionLabel)
        VBox2.addWidget(self.l2NIRCorrectionCheckBox)
        
        # Percent Light; Hooker & Morel 2003
        VBox2.addWidget(l2EnablePercentLtLabel)
        VBox2.addWidget(self.l2EnablePercentLtCheckBox)
        VBox2.addWidget(l2PercentLtLabel)
        VBox2.addWidget(self.l2PercentLtLineEdit)
        VBox2.addSpacing(25)
        
        # ??
        hBox = QtWidgets.QHBoxLayout()
        hBox.addLayout(VBox1)
        hBox.addSpacing(50)
        hBox.addLayout(VBox2)        

        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.cancelButton)

        # Adds hBox and saveHBox, but what about VBox1 and VBox2?
        VBox.addLayout(hBox)
        VBox.addLayout(saveHBox)

        self.setLayout(VBox)
        self.setGeometry(300, 200, 400, 750)
        self.setWindowTitle('Edit Config')
        #self.show()

        print("ConfigWindow - initUI Done")


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


    def l2CheckCoordsCheckBoxUpdate(self):
        print("ConfigWindow - l2CheckCoordsCheckBoxUpdate")

        disabled = (not self.l2CheckCoordsCheckBox.isChecked())
        self.lonMinLabel.setDisabled(disabled)
        self.lonMinLineEdit.setDisabled(disabled)
        self.lonMaxLabel.setDisabled(disabled)
        self.lonMaxLineEdit.setDisabled(disabled)
        self.directionLabel.setDisabled(disabled)
        self.directionComboBox.setDisabled(disabled)

    def l2CleanRotatorAngleCheckBoxUpdate(self):
        print("ConfigWindow - l2CleanRotatorAngleCheckBoxUpdate")
        
        disabled = (not self.l2CleanRotatorAngleCheckBox.isChecked())
        self.l2RotatorAngleMinLabel.setDisabled(disabled)
        self.l2RotatorAngleMinLineEdit.setDisabled(disabled)
        self.l2RotatorAngleMaxLabel.setDisabled(disabled)
        self.l2RotatorAngleMaxLineEdit.setDisabled(disabled)
        self.l2RotatorDelayLabel.setDisabled(disabled)
        self.l2RotatorDelayLineEdit.setDisabled(disabled)

    def l2CleanSunAngleCheckBoxUpdate(self):
        print("ConfigWindow - l2CleanSunAngleCheckBoxUpdate")
        
        disabled = (not self.l2CleanSunAngleCheckBox.isChecked())
        self.l2SunAngleMinLabel.setDisabled(disabled)
        self.l2SunAngleMinLineEdit.setDisabled(disabled)
        self.l2SunAngleMaxLabel.setDisabled(disabled)
        self.l2SunAngleMaxLineEdit.setDisabled(disabled)
        self.l2RotatorHomeAngleLabel.setDisabled(disabled)
        self.l2RotatorHomeAngleLineEdit.setDisabled(disabled)

    def l2QualityFlagCheckBoxUpdate(self):
        print("ConfigWindow - l2QualityFlagCheckBoxUpdate")
        
        disabled = (not self.l2QualityFlagCheckBox.isChecked())
        self.l2EsFlagLabel.setDisabled(disabled)
        self.l2EsFlagLineEdit.setDisabled(disabled)
        self.l2DawnDuskFlagLabel.setDisabled(disabled)
        self.l2DawnDuskFlagLineEdit.setDisabled(disabled)
        self.l2RainfallHumidityFlagLabel.setDisabled(disabled)
        self.l2RainfallHumidityFlagLineEdit.setDisabled(disabled)

    def l2EnableWindSpeedCalculationCheckBoxUpdate(self):
        print("ConfigWindow - l2EnableWindSpeedCalculationCheckBoxUpdate")
        
        disabled = (not self.l2EnableWindSpeedCalculationCheckBox.isChecked())
        self.l2DefaultWindSpeedLabel.setDisabled(disabled)
        self.l2DefaultWindSpeedLineEdit.setDisabled(disabled)


    def saveButtonPressed(self):
        print("ConfigWindow - Save Pressed")

        ConfigFile.settings["bL1aCleanSZA"] = int(self.l1aCleanSZACheckBox.isChecked())
        ConfigFile.settings["fL1aCleanSZAMax"] = float(self.l1aCleanSZAMaxLineEdit.text())
        
        ConfigFile.settings["fL1bInterpInterval"] = float(self.l1bInterpIntervalLineEdit.text())

        ConfigFile.settings["bL2CleanSunAngle"] = int(self.l2CleanSunAngleCheckBox.isChecked())
        ConfigFile.settings["bL2CleanRotatorAngle"] = int(self.l2CleanRotatorAngleCheckBox.isChecked())
        ConfigFile.settings["fL2SunAngleMin"] = float(self.l2SunAngleMinLineEdit.text())
        ConfigFile.settings["fL2SunAngleMax"] = float(self.l2SunAngleMaxLineEdit.text())
        ConfigFile.settings["fL2RotatorAngleMin"] = float(self.l2RotatorAngleMinLineEdit.text())
        ConfigFile.settings["fL2RotatorAngleMax"] = float(self.l2RotatorAngleMaxLineEdit.text())
        ConfigFile.settings["fL2RotatorHomeAngle"] = float(self.l2RotatorHomeAngleLineEdit.text())
        ConfigFile.settings["fL2RotatorDelay"] = float(self.l2RotatorDelayLineEdit.text())

        ConfigFile.settings["bL2EnableQualityFlags"] = int(self.l2QualityFlagCheckBox.isChecked())
        ConfigFile.settings["fL2SignificantEsFlag"] = float(self.l2EsFlagLineEdit.text())
        ConfigFile.settings["fL2DawnDuskFlag"] = float(self.l2DawnDuskFlagLineEdit.text())
        ConfigFile.settings["fL2RainfallHumidityFlag"] = float(self.l2RainfallHumidityFlagLineEdit.text())
        ConfigFile.settings["fL2TimeInterval"] = int(self.l2TimeIntervalLineEdit.text())
        ConfigFile.settings["fL2RhoSky"] = float(self.l2RhoSkyLineEdit.text())
        ConfigFile.settings["bL2EnableWindSpeedCalculation"] = int(self.l2EnableWindSpeedCalculationCheckBox.isChecked())
        ConfigFile.settings["fL2DefaultWindSpeed"] = float(self.l2DefaultWindSpeedLineEdit.text())
        ConfigFile.settings["bL2PerformNIRCorrection"] = int(self.l2NIRCorrectionCheckBox.isChecked())
        ConfigFile.settings["bL2EnablePercentLtCorrection"] = int(self.l2EnablePercentLtCheckBox.isChecked())
        ConfigFile.settings["fL2PercentLt"] = float(self.l2PercentLtLineEdit.text())

        ConfigFile.saveConfig(self.name)

        QtWidgets.QMessageBox.about(self, "Edit Config File", "Config File Saved")
        self.close()


    def cancelButtonPressed(self):
        print("ConfigWindow - Cancel Pressed")
        self.close()

