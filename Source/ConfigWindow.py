
import os
import shutil
# import threading
from PyQt5 import QtCore, QtGui, QtWidgets

# from MainConfig import MainConfig
# from Main import Window
from ConfigFile import ConfigFile
# from AnomalyDetection import AnomalyDetection
from AnomalyDetection import AnomAnalWindow
from SeaBASSHeader import SeaBASSHeader
from SeaBASSHeaderWindow import SeaBASSHeaderWindow
from GetAnc import GetAnc
from OCproductsWindow import OCproductsWindow
# import pyqtgraph as pg


class ConfigWindow(QtWidgets.QDialog):
    ''' Configuration window object '''
    def __init__(self, name, inputDir, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.name = name
        self.inputDirectory = inputDir
        self.initUI()


    def initUI(self):
        ''' Initialize the GUI '''
        # Calibration Config Settings
        self.addCalibrationFileButton = QtWidgets.QPushButton("Add Cals")
        self.addCalibrationFileButton.clicked.connect(self.addCalibrationFileButtonPressed)
        self.deleteCalibrationFileButton = QtWidgets.QPushButton("Remove Cals")
        self.deleteCalibrationFileButton.clicked.connect(self.deleteCalibrationFileButtonPressed)

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
        # self.calibrationFrameTypeComboBox.addItem("LightAncCombined")
        self.calibrationFrameTypeComboBox.currentIndexChanged.connect(self.calibrationFrameTypeChanged)
        self.calibrationFrameTypeComboBox.setEnabled(False)

        # Config File Settings
        intValidator = QtGui.QIntValidator()
        doubleValidator = QtGui.QDoubleValidator()
        # oddValidator = QtGui.QRegExpValidator(rx,self)

        # L1A
        l1aLabel = QtWidgets.QLabel("Level 1A Processing", self)
        l1aLabel_font = l1aLabel.font()
        l1aLabel_font.setPointSize(12)
        l1aLabel_font.setBold(True)
        l1aLabel.setFont(l1aLabel_font)
        l1aSublabel = QtWidgets.QLabel(" Raw binary to HDF5", self)

        l1aCleanSZALabel = QtWidgets.QLabel("     Solar Zenith Angle Filter", self)
        self.l1aCleanSZACheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1aCleanSZA"]) == 1:
            self.l1aCleanSZACheckBox.setChecked(True)
        l1aCleanSZAMaxLabel = QtWidgets.QLabel("     SZA Max", self)
        self.l1aCleanSZAMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l1aCleanSZAMaxLineEdit.setText(str(ConfigFile.settings["fL1aCleanSZAMax"]))
        self.l1aCleanSZAMaxLineEdit.setValidator(doubleValidator)

        self.l1aCleanSZACheckBoxUpdate()
        self.l1aCleanSZACheckBox.clicked.connect(self.l1aCleanSZACheckBoxUpdate)


        # # L1B
        # l1bLabel = QtWidgets.QLabel("Level 1B Processing", self)
        # l1bLabel_font = l1bLabel.font()
        # l1bLabel_font.setPointSize(12)
        # l1bLabel_font.setBold(True)
        # l1bLabel.setFont(l1bLabel_font)
        # l1bSublabel = QtWidgets.QLabel(" Apply factory calibrations", self)


        # L1AQC (Main)
        l1aqcLabel = QtWidgets.QLabel("Level 1AQC Processing", self)
        l1aqcLabel_font = l1aqcLabel.font()
        l1aqcLabel_font.setPointSize(12)
        l1aqcLabel_font.setBold(True)
        l1aqcLabel.setFont(l1aqcLabel_font)
        l1aqcSublabel = QtWidgets.QLabel(" Filter on pitch, roll, yaw, and azimuth", self)
        # l1aqcSublabel2 = QtWidgets.QLabel("   relative solar azimuth.", self)
        # l1aqcSublabel3 = QtWidgets.QLabel("   factory calibrations.", self)

        # SolarTracker
        self.l1aqcSolarTrackerLabel = QtWidgets.QLabel(" SolarTracker or pySAS", self)
        self.l1aqcSolarTrackerCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1aqcSolarTracker"]) == 1:
            self.l1aqcSolarTrackerCheckBox.setChecked(True)


        # L1AQC Rotator
        self.l1aqcRotatorHomeAngleLabel = QtWidgets.QLabel(" Rotator Home Angle Offset", self)
        self.l1aqcRotatorHomeAngleLineEdit = QtWidgets.QLineEdit(self)
        self.l1aqcRotatorHomeAngleLineEdit.setText(str(ConfigFile.settings["fL1aqcRotatorHomeAngle"]))
        self.l1aqcRotatorHomeAngleLineEdit.setValidator(doubleValidator)

        self.l1aqcRotatorDelayLabel = QtWidgets.QLabel(" Rotator Delay (Seconds)", self)
        self.l1aqcRotatorDelayCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1aqcRotatorDelay"]) == 1:
            self.l1aqcRotatorDelayCheckBox.setChecked(True)
        self.l1aqcRotatorDelayLineEdit = QtWidgets.QLineEdit(self)
        self.l1aqcRotatorDelayLineEdit.setText(str(ConfigFile.settings["fL1aqcRotatorDelay"]))
        self.l1aqcRotatorDelayLineEdit.setValidator(doubleValidator)
        self.l1aqcRotatorDelayCheckBoxUpdate()

        # L1AQC Pitch and Roll
        self.l1aqcCleanPitchRollLabel = QtWidgets.QLabel(" Pitch & Roll Filter", self)
        self.l1aqcCleanPitchRollCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1aqcCleanPitchRoll"]) == 1:
            self.l1aqcCleanPitchRollCheckBox.setChecked(True)
        self.l1aqcPitchRollPitchLabel = QtWidgets.QLabel("       Max Pitch/Roll Angle", self)
        self.l1aqcPitchRollPitchLineEdit = QtWidgets.QLineEdit(self)
        self.l1aqcPitchRollPitchLineEdit.setText(str(ConfigFile.settings["fL1aqcPitchRollPitch"]))
        self.l1aqcPitchRollPitchLineEdit.setValidator(doubleValidator)

         # L1AQC Rotator
        self.l1aqcRotatorAngleLabel = QtWidgets.QLabel(" Absolute Rotator Angle Filter", self)
        self.l1aqcRotatorAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1aqcRotatorAngle"]) == 1:
            self.l1aqcRotatorAngleCheckBox.setChecked(True)
        self.l1aqcRotatorAngleMinLabel = QtWidgets.QLabel("       Rotator Angle Min", self)
        self.l1aqcRotatorAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l1aqcRotatorAngleMinLineEdit.setText(str(ConfigFile.settings["fL1aqcRotatorAngleMin"]))
        self.l1aqcRotatorAngleMinLineEdit.setValidator(doubleValidator)
        self.l1aqcRotatorAngleMaxLabel = QtWidgets.QLabel("       Rotator Angle Max", self)
        self.l1aqcRotatorAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l1aqcRotatorAngleMaxLineEdit.setText(str(ConfigFile.settings["fL1aqcRotatorAngleMax"]))
        self.l1aqcRotatorAngleMaxLineEdit.setValidator(doubleValidator)
        self.l1aqcSolarTrackerCheckBoxUpdate()
        self.l1aqcRotatorAngleCheckBoxUpdate()

        # L1AQC Relative SZA
        l1aqcCleanSunAngleLabel = QtWidgets.QLabel(" Relative Solar Azimuth Filter", self)
        self.l1aqcCleanSunAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1aqcCleanSunAngle"]) == 1:
            self.l1aqcCleanSunAngleCheckBox.setChecked(True)
        self.l1aqcSunAngleMinLabel = QtWidgets.QLabel("       Rel Angle Min", self)
        self.l1aqcSunAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l1aqcSunAngleMinLineEdit.setText(str(ConfigFile.settings["fL1aqcSunAngleMin"]))
        self.l1aqcSunAngleMinLineEdit.setValidator(doubleValidator)
        self.l1aqcSunAngleMaxLabel = QtWidgets.QLabel("       Rel Angle Max", self)
        self.l1aqcSunAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l1aqcSunAngleMaxLineEdit.setText(str(ConfigFile.settings["fL1aqcSunAngleMax"]))
        self.l1aqcSunAngleMaxLineEdit.setValidator(doubleValidator)
        self.l1aqcCleanSunAngleCheckBoxUpdate()

        self.l1aqcSolarTrackerCheckBox.clicked.connect(self.l1aqcSolarTrackerCheckBoxUpdate)
        self.l1aqcRotatorDelayCheckBox.clicked.connect(self.l1aqcRotatorDelayCheckBoxUpdate)
        self.l1aqcCleanPitchRollCheckBox.clicked.connect(self.l1aqcCleanPitchRollCheckBoxUpdate)
        self.l1aqcRotatorAngleCheckBox.clicked.connect(self.l1aqcRotatorAngleCheckBoxUpdate)
        self.l1aqcCleanSunAngleCheckBox.clicked.connect(self.l1aqcCleanSunAngleCheckBoxUpdate)

        # L1AQC Deglitcher
        self.l1aqcDeglitchLabel = QtWidgets.QLabel("  Deglitch Data", self)
        self.l1aqcDeglitchCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1aqcDeglitch"]) == 1:
            self.l1aqcDeglitchCheckBox.setChecked(True)

        self.l1aqcDeglitchCheckBoxUpdate()
        self.l1aqcDeglitchCheckBox.clicked.connect(self.l1aqcDeglitchCheckBoxUpdate)

        # L1AQC Launch Deglitcher Analysis
        l1aqcAnomalySublabel1 = QtWidgets.QLabel("  Launch Anom. Anal. to test parameters",self)
        l1aqcAnomalySublabel2 = QtWidgets.QLabel("  on L1AQC files. Saved to Plots/L1AQC_Anoms.",self)
        self.l1aqcAnomalyButton = QtWidgets.QPushButton("Anomaly Analysis")
        self.l1aqcAnomalyButton.clicked.connect(self.l1aqcAnomalyButtonPressed)

        # L1ADARK
        l1adarkLabel = QtWidgets.QLabel("Level 1D Processing", self)
        l1adarkLabel_font = l1adarkLabel.font()
        l1adarkLabel_font.setPointSize(12)
        l1adarkLabel_font.setBold(True)
        l1adarkLabel.setFont(l1adarkLabel_font)
        l1adarkSublabel = QtWidgets.QLabel("Shutter dark corrections", self)

        # L1B
        l1bLabel = QtWidgets.QLabel("Level 1B Processing", self)
        l1bLabel_font = l1bLabel.font()
        l1bLabel_font.setPointSize(12)
        l1bLabel_font.setBold(True)
        l1bLabel.setFont(l1bLabel_font)
        l1bSublabel = QtWidgets.QLabel(" Apply factory calibrations and corrections.", self)
        l1bSublabel2 = QtWidgets.QLabel(" Interpolate to common time coordinates.", self)

        self.CalRadioButtonDefault = QtWidgets.QRadioButton("Default Factory")
        self.CalRadioButtonDefault.setAutoExclusive(False)
        if ConfigFile.settings["bL1bDefaultCal"]==1:
            self.CalRadioButtonDefault.setChecked(True)
        self.CalRadioButtonDefault.clicked.connect(self.l1bCalRadioButtonDefaultClicked)

        self.CalRadioButtonFull = QtWidgets.QRadioButton("Full Characterization")
        self.CalRadioButtonFull.setAutoExclusive(False)
        if ConfigFile.settings["bL1bFullCal"]==1:
            self.CalRadioButtonFull.setChecked(True)
        if ConfigFile.settings["bL1bFullFiles"]==0:  # <---- Needs to be a test for full cal files
            self.CalRadioButtonFull.setChecked(False)
            self.CalRadioButtonFull.setDisabled(1)
        self.CalRadioButtonFull.clicked.connect(self.l1bCalRadioButtonFullClicked)

        l1bInterpIntervalLabel = QtWidgets.QLabel("     Interpolation Interval (nm)", self)
        self.l1bInterpIntervalLineEdit = QtWidgets.QLineEdit(self)
        self.l1bInterpIntervalLineEdit.setText(str(ConfigFile.settings["fL1bInterpInterval"]))
        self.l1bInterpIntervalLineEdit.setValidator(doubleValidator)

        l1bPlotTimeInterpLabel = QtWidgets.QLabel("     Generate Plots (OUTPUTPATH/Plots/L1B_Interp/)", self)
        self.l1bPlotTimeInterpCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1bPlotTimeInterp"]) == 1:
            self.l1bPlotTimeInterpCheckBox.setChecked(True)
        self.l1bPlotTimeInterpCheckBox.clicked.connect(self.l1bPlotTimeInterpCheckBoxUpdate)

        l1bSaveSeaBASSLabel = QtWidgets.QLabel('     Save SeaBASS Text Files', self)
        self.l1bSaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1bSaveSeaBASS"]) == 1:
            self.l1bSaveSeaBASSCheckBox.setChecked(True)
        self.l1bSaveSeaBASSCheckBox.clicked.connect(self.l1bSaveSeaBASSCheckBoxUpdate)

        self.l1bSeaBASSHeaderEditButton = QtWidgets.QPushButton("Edit SeaBASS Header", self)
        self.l1bSeaBASSHeaderEditButton.clicked.connect(self.l1bSeaBASSHeaderEditButtonPressed)

        l2pGetAncLabel = QtWidgets.QLabel("       Download Ancillary Models", self)
        self.l2pGetAncCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2pGetAnc"]) == 1:
            self.l2pGetAncCheckBox.setChecked(True)
        self.l2pGetAncCheckBox.clicked.connect(self.l2pGetAncCheckBoxUpdate)

        # L2
        l2Label = QtWidgets.QLabel("Level 2 Processing", self)
        l2Label_font = l2Label.font()
        l2Label_font.setPointSize(12)
        l2Label_font.setBold(True)
        l2Label.setFont(l2Label_font)
        l2Sublabel = QtWidgets.QLabel(" Quality control filters, glint correction, temporal", self)
        l2Sublabel2 = QtWidgets.QLabel(" binning, reflectance calculation.", self)

        # Lt UV<NIR
        l2LtUVNIRLabel= QtWidgets.QLabel("     Eliminate where Lt(NIR)>Lt(UV)", self)
        self.l2LtUVNIRCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2LtUVNIR"]) == 1:
            self.l2LtUVNIRCheckBox.setChecked(True)
        self.l2LtUVNIRCheckBox.clicked.connect(self.l2LtUVNIRCheckBoxUpdate)

        # L2 Max Wind
        l2MaxWindLabel = QtWidgets.QLabel("     Max. Wind Speed (m/s)", self)
        self.l2MaxWindLineEdit = QtWidgets.QLineEdit(self)
        self.l2MaxWindLineEdit.setText(str(ConfigFile.settings["fL2MaxWind"]))
        self.l2MaxWindLineEdit.setValidator(doubleValidator)

        # L2 Min/Max SZA
        l2SZAMinLabel = QtWidgets.QLabel("     SZA Minimum (deg)", self)
        self.l2SZAMinLineEdit = QtWidgets.QLineEdit(self)
        self.l2SZAMinLineEdit.setText(str(ConfigFile.settings["fL2SZAMin"]))
        self.l2SZAMinLineEdit.setValidator(doubleValidator)
        l2SZAMaxLabel = QtWidgets.QLabel("     SZA Maximum (deg)", self)
        self.l2SZAMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l2SZAMaxLineEdit.setText(str(ConfigFile.settings["fL2SZAMax"]))
        self.l2SZAMaxLineEdit.setValidator(doubleValidator)

        # L2 Spectral Outlier Filter
        l2SpecQualityCheckLabel = QtWidgets.QLabel("     Enable Spectral Outlier Filter", self)
        self.l2SpecQualityCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2EnableSpecQualityCheck"]) == 1:
            self.l2SpecQualityCheckBox.setChecked(True)

        self.l2SpecFilterEsLabel = QtWidgets.QLabel("      Filter Sigma Es", self)
        self.l2SpecFilterEsLineEdit = QtWidgets.QLineEdit(self)
        self.l2SpecFilterEsLineEdit.setText(str(ConfigFile.settings["fL2SpecFilterEs"]))
        self.l2SpecFilterEsLineEdit.setValidator(doubleValidator)
        self.l2SpecFilterLiLabel = QtWidgets.QLabel("      Filter Sigma Li", self)
        self.l2SpecFilterLiLineEdit = QtWidgets.QLineEdit(self)
        self.l2SpecFilterLiLineEdit.setText(str(ConfigFile.settings["fL2SpecFilterLi"]))
        self.l2SpecFilterLiLineEdit.setValidator(doubleValidator)
        self.l2SpecFilterLtLabel = QtWidgets.QLabel("      Filter Sigma Lt", self)
        self.l2SpecFilterLtLineEdit = QtWidgets.QLineEdit(self)
        self.l2SpecFilterLtLineEdit.setText(str(ConfigFile.settings["fL2SpecFilterLt"]))
        self.l2SpecFilterLtLineEdit.setValidator(doubleValidator)

        self.l2SpecQualityCheckBoxUpdate()

        # L2 Meteorology Flags
        l2QualityFlagLabel = QtWidgets.QLabel("     Enable Meteorological Filters", self)
        self.l2QualityFlagCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2EnableQualityFlags"]) == 1:
            self.l2QualityFlagCheckBox.setChecked(True)

        self.l2CloudFlagLabel = QtWidgets.QLabel("      Cloud Li(750)/Es(750)>", self)
        self.l2CloudFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l2CloudFlagLineEdit.setText(str(ConfigFile.settings["fL2CloudFlag"]))
        self.l2CloudFlagLineEdit.setValidator(doubleValidator)

        self.l2EsFlagLabel = QtWidgets.QLabel("      Sig. Es(480) (uW cm^-2 nm^-1)", self)
        self.l2EsFlagLineEdit = QtWidgets.QLineEdit(self)
        self.l2EsFlagLineEdit.setText(str(ConfigFile.settings["fL2SignificantEsFlag"]))
        self.l2EsFlagLineEdit.setValidator(doubleValidator)

        self.l2DawnDuskFlagLabel = QtWidgets.QLabel("      Dawn/Dusk Es(470/680)<", self)
        self.l2DawnDuskFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l2DawnDuskFlagLineEdit.setText(str(ConfigFile.settings["fL2DawnDuskFlag"]))
        self.l2DawnDuskFlagLineEdit.setValidator(doubleValidator)

        self.l2RainfallHumidityFlagLabel = QtWidgets.QLabel("      Rain/Humid. Es(720/370)<", self)
        self.l2RainfallHumidityFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l2RainfallHumidityFlagLineEdit.setText(str(ConfigFile.settings["fL2RainfallHumidityFlag"]))
        self.l2RainfallHumidityFlagLineEdit.setValidator(doubleValidator)

        self.l2QualityFlagCheckBoxUpdate()

        # L2 Ensembles
        l2ensLabel = QtWidgets.QLabel("L2 Ensembles", self)
        l2ensLabel_font = l2ensLabel.font()
        l2ensLabel_font.setPointSize(12)
        l2ensLabel_font.setBold(True)
        l2ensLabel.setFont(l2ensLabel_font)

        # L2 Station breakout
        l2StationsLabel = QtWidgets.QLabel("Extract Cruise Stations", self)
        self.l2StationsCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2Stations"]) == 1:
            self.l2StationsCheckBox.setChecked(True)

        # L2 Time Average Rrs
        l2TimeIntervalLabel = QtWidgets.QLabel("  Ensemble Interval (secs; 0=None)", self)
        self.l2TimeIntervalLineEdit = QtWidgets.QLineEdit(self)
        self.l2TimeIntervalLineEdit.setText(str(ConfigFile.settings["fL2TimeInterval"]))
        self.l2TimeIntervalLineEdit.setValidator(intValidator)

        # L2 Set percentage Lt filter
        self.l2EnablePercentLtLabel = QtWidgets.QLabel("    Enable Percent Lt Calculation", self)
        self.l2EnablePercentLtCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2EnablePercentLt"]) == 1:
            self.l2EnablePercentLtCheckBox.setChecked(True)
        self.l2PercentLtLabel = QtWidgets.QLabel("     Percent Lt (%)", self)
        self.l2PercentLtLineEdit = QtWidgets.QLineEdit(self)
        self.l2PercentLtLineEdit.setText(str(ConfigFile.settings["fL2PercentLt"]))
        self.l2PercentLtLineEdit.setValidator(doubleValidator)

        self.l2EnablePercentLtCheckBoxUpdate()

        l2pSublabel = QtWidgets.QLabel(" GMAO MERRA2 ancillary data are required for Zhang glint", self)
        l2pSublabel2 = QtWidgets.QLabel(" correction and can fill in wind for Ruddick glint.", self)
        l2pSublabel3 = QtWidgets.QLabel(" WILL PROMPT FOR EARTHDATA USERNAME/PASSWORD", self)
        l2pSublabel4 = QtWidgets.QLabel(
            "<a href=\"https://oceancolor.gsfc.nasa.gov/registration/\">         Register here</a>", self)
        l2pSublabel4.setOpenExternalLinks(True)

        # L2 Rho Sky Correction
        l2RhoSkyLabel = QtWidgets.QLabel("L2 Sky/Sunglint Correction (ρ)", self)
        l2RhoSkyLabel_font = l1bLabel.font()
        # l2RhoSkyLabel_font.setPointSize(12)
        l2RhoSkyLabel_font.setBold(True)
        l2RhoSkyLabel.setFont(l1bLabel_font)

        self.l2DefaultWindSpeedLabel = QtWidgets.QLabel("     Default Wind Speed (m/s)", self)
        self.l2DefaultWindSpeedLineEdit = QtWidgets.QLineEdit(self)
        self.l2DefaultWindSpeedLineEdit.setText(str(ConfigFile.settings["fL2DefaultWindSpeed"]))
        self.l2DefaultWindSpeedLineEdit.setValidator(doubleValidator)
        self.l2DefaultAODLabel = QtWidgets.QLabel("     Default AOD(550)", self)
        self.l2DefaultAODLineEdit = QtWidgets.QLineEdit(self)
        self.l2DefaultAODLineEdit.setText(str(ConfigFile.settings["fL2DefaultAOD"]))
        self.l2DefaultAODLineEdit.setValidator(doubleValidator)
        self.l2DefaultSaltLabel = QtWidgets.QLabel("     Default Salinity (psu)", self)
        self.l2DefaultSaltLineEdit = QtWidgets.QLineEdit(self)
        self.l2DefaultSaltLineEdit.setText(str(ConfigFile.settings["fL2DefaultSalt"]))
        self.l2DefaultSaltLineEdit.setValidator(doubleValidator)
        self.l2DefaultSSTLabel = QtWidgets.QLabel("     Default SST (C)", self)
        self.l2DefaultSSTLineEdit = QtWidgets.QLineEdit(self)
        self.l2DefaultSSTLineEdit.setText(str(ConfigFile.settings["fL2DefaultSST"]))
        self.l2DefaultSSTLineEdit.setValidator(doubleValidator)


        self.RhoRadioButtonDefault = QtWidgets.QRadioButton("Mobley (1999) ρ")
        self.RhoRadioButtonDefault.setAutoExclusive(False)
        if ConfigFile.settings["bL2DefaultRho"]==1:
            self.RhoRadioButtonDefault.setChecked(True)
        self.RhoRadioButtonDefault.clicked.connect(self.l2RhoRadioButtonDefaultClicked)

        self.RhoRadioButtonZhang = QtWidgets.QRadioButton("Zhang et al. (2017) ρ")
        self.RhoRadioButtonZhang.setAutoExclusive(False)
        if ConfigFile.settings["bL2ZhangRho"]==1:
            self.RhoRadioButtonZhang.setChecked(True)
        if ConfigFile.settings["bL2pGetAnc"]==0:
            self.RhoRadioButtonZhang.setChecked(False)
            self.RhoRadioButtonZhang.setDisabled(1)
        self.RhoRadioButtonZhang.clicked.connect(self.l2RhoRadioButtonZhangClicked)

        self.RhoRadoButton3C = QtWidgets.QRadioButton("Groetsch et al. (2017)")
        self.RhoRadoButton3C.setAutoExclusive(False)
        self.RhoRadoButton3C.setDisabled(True)

        self.RhoRadioButtonYour = QtWidgets.QRadioButton("Your Glint (2021) ρ")
        self.RhoRadioButtonYour.setAutoExclusive(False)
        self.RhoRadioButtonYour.setDisabled(True)
        # if ConfigFile.settings["bL2YourRho"]==1:
        #     self.RhoRadioButtonYour.setChecked(True)
        # self.RhoRadioButtonYour.clicked.connect(self.l2RhoRadioButtonYourClicked)


        # L2 NIR AtmoCorr
        l2NIRCorrectionLabel = QtWidgets.QLabel("NIR Residual Correction", self)
        self.l2NIRCorrectionCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2PerformNIRCorrection"]) == 1:
            self.l2NIRCorrectionCheckBox.setChecked(True)

        self.SimpleNIRRadioButton = QtWidgets.QRadioButton("   Mueller and Austin (1995) (blue water)")
        self.SimpleNIRRadioButton.setAutoExclusive(False)
        if ConfigFile.settings["bL2SimpleNIRCorrection"] == 1:
            self.SimpleNIRRadioButton.setChecked(True)
        self.SimpleNIRRadioButton.clicked.connect(self.l2SimpleNIRRadioButtonClicked)
        self.SimSpecNIRRadioButton = QtWidgets.QRadioButton("   SimSpec. Ruddick et al. (2006) (turbid)")
        self.SimSpecNIRRadioButton.setAutoExclusive(False)
        if ConfigFile.settings["bL2SimSpecNIRCorrection"] == 1:
            self.SimSpecNIRRadioButton.setChecked(True)
        self.SimSpecNIRRadioButton.clicked.connect(self.l2SimSpecNIRRadioButtonClicked)
        self.YourNIRRadioButton = QtWidgets.QRadioButton("   Your NIR Residual (2021) (universal)")
        self.YourNIRRadioButton.setAutoExclusive(False)
        # if ConfigFile.settings["bL2YourNIRCorrection"] == 1:
        #     self.YourNIRRadioButton.setChecked(True)
        # self.YourNIRRadioButton.clicked.connect(self.l2YourNIRRadioButtonClicked)
        self.YourNIRRadioButton.setDisabled(True)

        self.l2NIRCorrectionCheckBoxUpdate()

        # L2 Remove negative spectra
        #   Could add spectral range here
        self.l2NegativeSpecLabel = QtWidgets.QLabel("Remove Negative Spectra", self)
        self.l2NegativeSpecCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2NegativeSpec"]) == 1:
            self.l2NegativeSpecCheckBox.setChecked(True)

        self.l2NegativeSpecCheckBoxUpdate()

        # Spectral Weighting
        l2WeightsLabel = QtWidgets.QLabel("Convolve to Satellite Bands:", self)

        l2WeightMODISALabel = QtWidgets.QLabel("AQUA *", self)
        self.l2WeightMODISACheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2WeightMODISA"]) == 1:
            self.l2WeightMODISACheckBox.setChecked(True)
        l2WeightMODISALabel2 = QtWidgets.QLabel("* Will be turned on automatically for Derived Products", self)

        l2WeightMODISTLabel = QtWidgets.QLabel("TERRA", self)
        self.l2WeightMODISTCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2WeightMODIST"]) == 1:
            self.l2WeightMODISTCheckBox.setChecked(True)

        l2WeightVIIRSNLabel = QtWidgets.QLabel("V-NPP", self)
        self.l2WeightVIIRSNCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2WeightVIIRSN"]) == 1:
            self.l2WeightVIIRSNCheckBox.setChecked(True)

        l2WeightVIIRSJLabel = QtWidgets.QLabel("V-JPSS", self)
        self.l2WeightVIIRSJCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2WeightVIIRSJ"]) == 1:
            self.l2WeightVIIRSJCheckBox.setChecked(True)

        l2WeightSentinel3ALabel = QtWidgets.QLabel("Sen-3A", self)
        self.l2WeightSentinel3ACheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2WeightSentinel3A"]) == 1:
            self.l2WeightSentinel3ACheckBox.setChecked(True)

        l2WeightSentinel3BLabel = QtWidgets.QLabel("Sen-3B", self)
        self.l2WeightSentinel3BCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2WeightSentinel3B"]) == 1:
            self.l2WeightSentinel3BCheckBox.setChecked(True)

        # Plots
        l2PlotsLabel = QtWidgets.QLabel("Generate Spectral Plots", self)
        l2PlotRrsLabel = QtWidgets.QLabel("Rrs", self)
        self.l2PlotRrsCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2PlotRrs"]) == 1:
            self.l2PlotRrsCheckBox.setChecked(True)

        l2PlotnLwLabel = QtWidgets.QLabel("nLw", self)
        self.l2PlotnLwCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2PlotnLw"]) == 1:
            self.l2PlotnLwCheckBox.setChecked(True)

        l2PlotEsLabel = QtWidgets.QLabel("Es", self)
        self.l2PlotEsCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2PlotEs"]) == 1:
            self.l2PlotEsCheckBox.setChecked(True)

        l2PlotLiLabel = QtWidgets.QLabel("Li", self)
        self.l2PlotLiCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2PlotLi"]) == 1:
            self.l2PlotLiCheckBox.setChecked(True)

        l2PlotLtLabel = QtWidgets.QLabel("Lt", self)
        self.l2PlotLtCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2PlotLt"]) == 1:
            self.l2PlotLtCheckBox.setChecked(True)

        self.l2SpecQualityCheckBox.clicked.connect(self.l2SpecQualityCheckBoxUpdate)
        self.l2QualityFlagCheckBox.clicked.connect(self.l2QualityFlagCheckBoxUpdate)
        self.l2StationsCheckBox.clicked.connect(self.l2StationsCheckBoxUpdate)
        self.l2EnablePercentLtCheckBox.clicked.connect(self.l2EnablePercentLtCheckBoxUpdate)
        self.l2NIRCorrectionCheckBox.clicked.connect(self.l2NIRCorrectionCheckBoxUpdate)
        self.l2NegativeSpecCheckBox.clicked.connect(self.l2NegativeSpecCheckBoxUpdate)


        self.l2OCproducts = QtWidgets.QPushButton("Derived L2 Ocean Color Products", self)
        self.l2OCproducts.clicked.connect(self.l2OCproductsButtonPressed)


        l2SaveSeaBASSLabel = QtWidgets.QLabel("Save SeaBASS Files (Edit Header in L1E)", self)
        self.l2SaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)
        self.l2SaveSeaBASSCheckBox.clicked.connect(self.l2SaveSeaBASSCheckBoxUpdate)
        if int(ConfigFile.settings["bL2SaveSeaBASS"]) == 1:
            self.l2SaveSeaBASSCheckBox.setChecked(True)
        # self.l2SaveSeaBASSCheckBox.clicked.connect(self.l2SaveSeaBASSCheckBoxUpdate)
        self.l1bSaveSeaBASSCheckBoxUpdate()
        self.l2SaveSeaBASSCheckBoxUpdate()


        l2WriteReportLabel = QtWidgets.QLabel("Write PDF Report", self)
        self.l2WriteReportCheckBox = QtWidgets.QCheckBox("", self)
        self.l2WriteReportCheckBox.clicked.connect(self.l2WriteReportCheckBoxUpdate)
        if int(ConfigFile.settings["bL2WriteReport"]) == 1:
            self.l2WriteReportCheckBox.setChecked(True)
        # self.l2WriteReportCheckBox.clicked.connect(self.l2SWriteReportCheckBoxUpdate)
        self.l2WriteReportCheckBoxUpdate()

        self.saveButton = QtWidgets.QPushButton("Save/Close")
        self.saveAsButton = QtWidgets.QPushButton("Save As")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.saveAsButton.clicked.connect(self.saveAsButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        #################################################################################

        # Whole Window Box
        VBox = QtWidgets.QVBoxLayout()
        # VBox.addWidget(nameLabel)

        # Vertical Box (left)
        VBox1 = QtWidgets.QVBoxLayout()

        # Instrument Files Setup
        # Horizontal Box
        calHBox1 = QtWidgets.QHBoxLayout()
        calHBox1.addWidget(self.addCalibrationFileButton)
        calHBox1.addWidget(self.deleteCalibrationFileButton)
        VBox1.addLayout(calHBox1)
        # Horizontal Box
        calHBox = QtWidgets.QHBoxLayout()
        calHBox.addWidget(self.calibrationFileComboBox)
        calHBox.addWidget(self.calibrationEnabledCheckBox)
        VBox1.addLayout(calHBox)

        VBox1.addWidget(calibrationFrameTypeLabel)
        VBox1.addWidget(self.calibrationFrameTypeComboBox)

        # L1A
        VBox1.addWidget(l1aLabel)
        VBox1.addWidget(l1aSublabel)
        VBox1.addWidget(l1aCleanSZALabel)
        # Horizontal Box; SZA Filter
        szaHBox = QtWidgets.QHBoxLayout()
        szaHBox.addWidget(l1aCleanSZAMaxLabel)
        szaHBox.addWidget(self.l1aCleanSZACheckBox)
        szaHBox.addWidget(self.l1aCleanSZAMaxLineEdit)
        VBox1.addLayout(szaHBox)

        # L1AQC
        VBox1.addWidget(l1aqcLabel)
        VBox1.addWidget(l1aqcSublabel)

        # SolarTracker
        SolarTrackerHBox = QtWidgets.QHBoxLayout()
        SolarTrackerHBox.addWidget(self.l1aqcSolarTrackerLabel)
        SolarTrackerHBox.addWidget(self.l1aqcSolarTrackerCheckBox)
        VBox1.addLayout(SolarTrackerHBox)

        # L1AQC Rotator
        RotHomeAngleHBox = QtWidgets.QHBoxLayout()
        RotHomeAngleHBox.addWidget(self.l1aqcRotatorHomeAngleLabel)
        RotHomeAngleHBox.addWidget(self.l1aqcRotatorHomeAngleLineEdit)
        VBox1.addLayout(RotHomeAngleHBox)
        RotatorDelayHBox = QtWidgets.QHBoxLayout()
        RotatorDelayHBox.addWidget(self.l1aqcRotatorDelayLabel)
        RotatorDelayHBox.addWidget(self.l1aqcRotatorDelayCheckBox)
        RotatorDelayHBox.addWidget(self.l1aqcRotatorDelayLineEdit)
        VBox1.addLayout(RotatorDelayHBox)

        # L1AQC Pitch & Roll
        PitchRollHBox = QtWidgets.QHBoxLayout()
        PitchRollHBox.addWidget(self.l1aqcCleanPitchRollLabel)
        PitchRollHBox.addWidget(self.l1aqcCleanPitchRollCheckBox)
        VBox1.addLayout(PitchRollHBox)
        PitchRollHBox2 = QtWidgets.QHBoxLayout()
        PitchRollHBox2.addWidget(self.l1aqcPitchRollPitchLabel)
        PitchRollHBox2.addWidget(self.l1aqcPitchRollPitchLineEdit)
        VBox1.addLayout(PitchRollHBox2)

        # L1AQC Rotator
        rotateHBox = QtWidgets.QHBoxLayout()
        rotateHBox.addWidget(self.l1aqcRotatorAngleLabel)
        rotateHBox.addWidget(self.l1aqcRotatorAngleCheckBox)
        VBox1.addLayout(rotateHBox)
        RotMinHBox = QtWidgets.QHBoxLayout()
        RotMinHBox.addWidget(self.l1aqcRotatorAngleMinLabel)
        RotMinHBox.addWidget(self.l1aqcRotatorAngleMinLineEdit)
        VBox1.addLayout(RotMinHBox)
        RotMaxHBox = QtWidgets.QHBoxLayout()
        RotMaxHBox.addWidget(self.l1aqcRotatorAngleMaxLabel)
        RotMaxHBox.addWidget(self.l1aqcRotatorAngleMaxLineEdit)
        VBox1.addLayout(RotMaxHBox)

        # L1AQC Relative SZA
        CleanSunAngleHBox = QtWidgets.QHBoxLayout()
        CleanSunAngleHBox.addWidget(l1aqcCleanSunAngleLabel)
        CleanSunAngleHBox.addWidget(self.l1aqcCleanSunAngleCheckBox)
        VBox1.addLayout(CleanSunAngleHBox)
        SunAngleMinHBox = QtWidgets.QHBoxLayout()
        SunAngleMinHBox.addWidget(self.l1aqcSunAngleMinLabel)
        SunAngleMinHBox.addWidget(self.l1aqcSunAngleMinLineEdit)
        VBox1.addLayout(SunAngleMinHBox)
        SunAngleMaxHBox = QtWidgets.QHBoxLayout()
        SunAngleMaxHBox.addWidget(self.l1aqcSunAngleMaxLabel)
        SunAngleMaxHBox.addWidget(self.l1aqcSunAngleMaxLineEdit)
        VBox1.addLayout(SunAngleMaxHBox)

        # L1AQC Deglitcher
        deglitchHBox = QtWidgets.QHBoxLayout()
        deglitchHBox.addWidget(self.l1aqcDeglitchLabel)
        deglitchHBox.addWidget(self.l1aqcDeglitchCheckBox)
        VBox1.addLayout(deglitchHBox)
        # L1AQC Anomaly Launcher
        VBox1.addWidget(l1aqcAnomalySublabel1)
        VBox1.addWidget(l1aqcAnomalySublabel2)
        VBox1.addWidget(self.l1aqcAnomalyButton)

        VBox1.addStretch()

        # Middle Vertical Box
        VBox2 = QtWidgets.QVBoxLayout()
        VBox2.setAlignment(QtCore.Qt.AlignBottom)

        # L1ADARK
        VBox2.addWidget(l1adarkLabel)
        VBox2.addWidget(l1adarkSublabel)

        #L1B
        VBox2.addWidget(l1bLabel)
        VBox2.addWidget(l1bSublabel)
        VBox2.addWidget(l1bSublabel2)

        # Instrument Files
        CalHBox2 = QtWidgets.QHBoxLayout()
        CalHBox2.addWidget(self.CalRadioButtonDefault)
        CalHBox2.addWidget(self.CalRadioButtonFull)

        interpHBox = QtWidgets.QHBoxLayout()
        interpHBox.addWidget(l1bInterpIntervalLabel)
        interpHBox.addWidget(self.l1bInterpIntervalLineEdit)
        VBox2.addLayout(interpHBox)

        # VBox2.addSpacing(10)

        l1bPlotTimeInterpHBox = QtWidgets.QHBoxLayout()
        l1bPlotTimeInterpHBox.addWidget(l1bPlotTimeInterpLabel)
        l1bPlotTimeInterpHBox.addWidget(self.l1bPlotTimeInterpCheckBox)
        VBox2.addLayout(l1bPlotTimeInterpHBox)

        # VBox2.addSpacing(10)

        l1bSeaBASSHBox = QtWidgets.QHBoxLayout()
        l1bSeaBASSHBox.addWidget(l1bSaveSeaBASSLabel)
        l1bSeaBASSHBox.addWidget(self.l1bSaveSeaBASSCheckBox)
        VBox2.addLayout(l1bSeaBASSHBox)

        l1bSeaBASSHeaderHBox2 = QtWidgets.QHBoxLayout()
        l1bSeaBASSHeaderHBox2.addWidget(self.l1bSeaBASSHeaderEditButton)
        VBox2.addLayout(l1bSeaBASSHeaderHBox2)

        # VBox2.addSpacing(20)

        # L2
        VBox2.addWidget(l2Label)
        VBox2.addWidget(l2Sublabel)
        VBox2.addWidget(l2Sublabel2)

        # Lt UV<NIR
        LtUVNIRHBox = QtWidgets.QHBoxLayout()
        LtUVNIRHBox.addWidget(l2LtUVNIRLabel)
        LtUVNIRHBox.addWidget(self.l2LtUVNIRCheckBox)
        VBox2.addLayout(LtUVNIRHBox)

        # L2 Max wind
        maxWindBox = QtWidgets.QHBoxLayout()
        maxWindBox.addWidget(l2MaxWindLabel)
        maxWindBox.addWidget(self.l2MaxWindLineEdit)
        VBox2.addLayout(maxWindBox)

        # L2 SZA Min/Max
        SZAHBox1 = QtWidgets.QHBoxLayout()
        SZAHBox1.addWidget(l2SZAMinLabel)
        SZAHBox1.addWidget(self.l2SZAMinLineEdit)
        VBox2.addLayout(SZAHBox1)

        SZAHBox2 = QtWidgets.QHBoxLayout()
        SZAHBox2.addWidget(l2SZAMaxLabel)
        SZAHBox2.addWidget(self.l2SZAMaxLineEdit)
        VBox2.addLayout(SZAHBox2)

         # L2 Spectral Outlier Filter
        SpecFilterHBox = QtWidgets.QHBoxLayout()
        SpecFilterHBox.addWidget(l2SpecQualityCheckLabel)
        SpecFilterHBox.addWidget(self.l2SpecQualityCheckBox)
        VBox2.addLayout(SpecFilterHBox)
        SpecFilterEsHBox = QtWidgets.QHBoxLayout()
        SpecFilterEsHBox.addWidget(self.l2SpecFilterEsLabel)
        SpecFilterEsHBox.addWidget(self.l2SpecFilterEsLineEdit)
        VBox2.addLayout(SpecFilterEsHBox)

        # L2 Spectral Outlier Filter
        SpecFilterLiHBox = QtWidgets.QHBoxLayout()
        SpecFilterLiHBox.addWidget(self.l2SpecFilterLiLabel)
        SpecFilterLiHBox.addWidget(self.l2SpecFilterLiLineEdit)
        VBox2.addLayout(SpecFilterLiHBox)
        SpecFilterLtHBox = QtWidgets.QHBoxLayout()
        SpecFilterLtHBox.addWidget(self.l2SpecFilterLtLabel)
        SpecFilterLtHBox.addWidget(self.l2SpecFilterLtLineEdit)
        VBox2.addLayout(SpecFilterLtHBox)

        # VBox3.addSpacing(5)

        # L2 Meteorology Flags
        QualityFlagHBox = QtWidgets.QHBoxLayout()
        QualityFlagHBox.addWidget(l2QualityFlagLabel)
        # QualityFlagHBox.addWidget(l2QualityFlagLabel2)
        QualityFlagHBox.addWidget(self.l2QualityFlagCheckBox)
        VBox2.addLayout(QualityFlagHBox)
        CloudFlagHBox = QtWidgets.QHBoxLayout()
        CloudFlagHBox.addWidget(self.l2CloudFlagLabel)
        CloudFlagHBox.addWidget(self.l2CloudFlagLineEdit)
        VBox2.addLayout(CloudFlagHBox)
        EsFlagHBox = QtWidgets.QHBoxLayout()
        EsFlagHBox.addWidget(self.l2EsFlagLabel)
        EsFlagHBox.addWidget(self.l2EsFlagLineEdit)
        VBox2.addLayout(EsFlagHBox)
        DawnFlagHBox =QtWidgets.QHBoxLayout()
        DawnFlagHBox.addWidget(self.l2DawnDuskFlagLabel)
        DawnFlagHBox.addWidget(self.l2DawnDuskFlagLineEdit)
        VBox2.addLayout(DawnFlagHBox)
        RainFlagHBox = QtWidgets.QHBoxLayout()
        RainFlagHBox.addWidget(self.l2RainfallHumidityFlagLabel)
        RainFlagHBox.addWidget(self.l2RainfallHumidityFlagLineEdit)
        VBox2.addLayout(RainFlagHBox)

        # L2 Ensembles
        VBox2.addWidget(l2ensLabel)

        # L2 Stations
        StationsHBox = QtWidgets.QHBoxLayout()
        StationsHBox.addWidget(l2StationsLabel)
        StationsHBox.addWidget(self.l2StationsCheckBox)
        VBox2.addLayout(StationsHBox)

        # L2 Time Average Rrs
        TimeAveHBox = QtWidgets.QHBoxLayout()
        TimeAveHBox.addWidget(l2TimeIntervalLabel)
        TimeAveHBox.addWidget(self.l2TimeIntervalLineEdit)
        VBox2.addLayout(TimeAveHBox)

        # L2 Percent Light; Hooker & Morel 2003
        PercentLtHBox = QtWidgets.QHBoxLayout()
        PercentLtHBox.addWidget(self.l2EnablePercentLtLabel)
        PercentLtHBox.addWidget(self.l2EnablePercentLtCheckBox)
        VBox2.addLayout(PercentLtHBox)
        PercentLtHBox2 = QtWidgets.QHBoxLayout()
        PercentLtHBox2.addWidget(self.l2PercentLtLabel)
        PercentLtHBox2.addWidget(self.l2PercentLtLineEdit)
        VBox2.addLayout(PercentLtHBox2)

        VBox2.addStretch()

        # Right box
        VBox3 = QtWidgets.QVBoxLayout()
        VBox3.setAlignment(QtCore.Qt.AlignBottom)
        # L2 Rho Skyglint/Sunglint Correction
        VBox3.addWidget(l2RhoSkyLabel)

        # L2 (Preliminary)
        # VBox2.addWidget(l2pLabel)
        VBox3.addWidget(l2pSublabel)
        VBox3.addWidget(l2pSublabel2)
        VBox3.addWidget(l2pSublabel3)
        # VBox2.addWidget(l2pSublabel4)
        l2pGetAncHBox = QtWidgets.QHBoxLayout()
        l2pGetAncHBox.addWidget(l2pSublabel4)
        l2pGetAncHBox.addWidget(l2pGetAncLabel)
        l2pGetAncHBox.addWidget(self.l2pGetAncCheckBox)
        VBox3.addLayout(l2pGetAncHBox)

        # Default Wind
        WindSpeedHBox2 = QtWidgets.QHBoxLayout()
        WindSpeedHBox2.addWidget(self.l2DefaultWindSpeedLabel)
        WindSpeedHBox2.addWidget(self.l2DefaultWindSpeedLineEdit)
        VBox3.addLayout(WindSpeedHBox2)
        # Default AOD
        AODHBox2 = QtWidgets.QHBoxLayout()
        AODHBox2.addWidget(self.l2DefaultAODLabel)
        AODHBox2.addWidget(self.l2DefaultAODLineEdit)
        VBox3.addLayout(AODHBox2)
        # Default Salt
        SaltHBox2 = QtWidgets.QHBoxLayout()
        SaltHBox2.addWidget(self.l2DefaultSaltLabel)
        SaltHBox2.addWidget(self.l2DefaultSaltLineEdit)
        VBox3.addLayout(SaltHBox2)
        # Default SST
        SSTHBox2 = QtWidgets.QHBoxLayout()
        SSTHBox2.addWidget(self.l2DefaultSSTLabel)
        SSTHBox2.addWidget(self.l2DefaultSSTLineEdit)
        VBox3.addLayout(SSTHBox2)

        # Rho model
        RhoHBox2 = QtWidgets.QHBoxLayout()
        RhoHBox2.addWidget(self.RhoRadioButtonDefault)
        RhoHBox2.addWidget(self.RhoRadioButtonZhang)
        VBox3.addLayout(RhoHBox2)
        RhoHBox3 = QtWidgets.QHBoxLayout()
        # RhoHBox3.addSpacing(60)
        RhoHBox3.addWidget(self.RhoRadoButton3C)
        RhoHBox3.addWidget(self.RhoRadioButtonYour)
        VBox3.addLayout(RhoHBox3)

        VBox3.addSpacing(5)

        # L2 NIR AtmoCorr
        # NIRCorrectionVBox = QtWidgets.QVBoxLayout()
        NIRCorrectionHBox = QtWidgets.QHBoxLayout()
        NIRCorrectionHBox.addWidget(l2NIRCorrectionLabel)
        NIRCorrectionHBox.addWidget(self.l2NIRCorrectionCheckBox)
        VBox3.addLayout(NIRCorrectionHBox)
        VBox3.addWidget(self.SimpleNIRRadioButton)
        VBox3.addWidget(self.SimSpecNIRRadioButton)
        VBox3.addWidget(self.YourNIRRadioButton)

        VBox3.addSpacing(5)

        # L2 Remove negative spectra
        NegativeSpecHBox = QtWidgets.QHBoxLayout()
        NegativeSpecHBox.addWidget(self.l2NegativeSpecLabel)
        NegativeSpecHBox.addWidget(self.l2NegativeSpecCheckBox)
        VBox3.addLayout(NegativeSpecHBox)

        VBox3.addSpacing(5)

        # L2 Spectral weighting to satellites
        VBox3.addWidget(l2WeightsLabel)
        l2WeightHBox = QtWidgets.QHBoxLayout()
        l2WeightHBox.addSpacing(45)
        l2WeightHBox.addWidget(l2WeightMODISALabel)
        l2WeightHBox.addWidget(self.l2WeightMODISACheckBox)
        l2WeightHBox.addWidget(l2WeightSentinel3ALabel)
        l2WeightHBox.addWidget(self.l2WeightSentinel3ACheckBox)
        l2WeightHBox.addWidget(l2WeightVIIRSNLabel)
        l2WeightHBox.addWidget(self.l2WeightVIIRSNCheckBox)
        VBox3.addLayout(l2WeightHBox)
        l2WeightHBox2 = QtWidgets.QHBoxLayout()
        l2WeightHBox2.addSpacing(45)
        l2WeightHBox2.addWidget(l2WeightMODISTLabel)
        l2WeightHBox2.addWidget(self.l2WeightMODISTCheckBox)
        l2WeightHBox2.addWidget(l2WeightSentinel3BLabel)
        l2WeightHBox2.addWidget(self.l2WeightSentinel3BCheckBox)
        l2WeightHBox2.addWidget(l2WeightVIIRSJLabel)
        l2WeightHBox2.addWidget(self.l2WeightVIIRSJCheckBox)
        VBox3.addLayout(l2WeightHBox2)
        VBox3.addWidget(l2WeightMODISALabel2)

        VBox3.addSpacing(5)

        # L2 Plotting
        VBox3.addWidget(l2PlotsLabel)
        l2PlotHBox = QtWidgets.QHBoxLayout()
        l2PlotHBox.addSpacing(45)
        l2PlotHBox.addWidget(l2PlotRrsLabel)
        l2PlotHBox.addWidget(self.l2PlotRrsCheckBox)
        l2PlotHBox.addWidget(l2PlotnLwLabel)
        l2PlotHBox.addWidget(self.l2PlotnLwCheckBox)
        l2PlotHBox.addWidget(l2PlotEsLabel)
        l2PlotHBox.addWidget(self.l2PlotEsCheckBox)
        l2PlotHBox.addWidget(l2PlotLiLabel)
        l2PlotHBox.addWidget(self.l2PlotLiCheckBox)
        l2PlotHBox.addWidget(l2PlotLtLabel)
        l2PlotHBox.addWidget(self.l2PlotLtCheckBox)
        VBox3.addLayout(l2PlotHBox)

        VBox3.addSpacing(5)

        l2OCproductsHBox = QtWidgets.QHBoxLayout()
        l2OCproductsHBox.addWidget(self.l2OCproducts)
        VBox3.addLayout(l2OCproductsHBox)

        # Horizontal Box; Save SeaBASS
        l2SeaBASSHBox = QtWidgets.QHBoxLayout()
        l2SeaBASSHBox.addWidget(l2SaveSeaBASSLabel)
        l2SeaBASSHBox.addWidget(self.l2SaveSeaBASSCheckBox)
        VBox3.addLayout(l2SeaBASSHBox)

        # Horizontal Box; Write Report
        l2ReportHBox = QtWidgets.QHBoxLayout()
        l2ReportHBox.addWidget(l2WriteReportLabel)
        l2ReportHBox.addWidget(self.l2WriteReportCheckBox)
        VBox3.addLayout(l2ReportHBox)

        VBox3.addSpacing(20)

        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.saveAsButton)
        saveHBox.addWidget(self.cancelButton)
        VBox3.addLayout(saveHBox)

        VBox3.addStretch()

        # Add 3 Vertical Boxes to Horizontal Box hBox
        hBox = QtWidgets.QHBoxLayout()
        hBox.addLayout(VBox1)
        hBox.addLayout(VBox2)
        hBox.addLayout(VBox3)

        # Adds hBox and saveHBox to primary VBox
        VBox.addLayout(hBox)

        self.setLayout(VBox)
        self.setGeometry(300, 100, 0, 0)
        self.setWindowTitle(f'Configuration: {self.name}')
        #self.show()

        # print("ConfigWindow - initUI Done")
    ###############################################################
    def addCalibrationFileButtonPressed(self):
        print("CalibrationEditWindow - Add Calibration File Pressed")
        fnames = QtWidgets.QFileDialog.getOpenFileNames(self, "Add Calibration Files")
        print(fnames)

        configName = self.name
        calibrationDir = os.path.splitext(configName)[0] + "_Calibration"
        configPath = os.path.join("Config", calibrationDir)
        for src in fnames[0]:
            (_, filename) = os.path.split(src)
            dest = os.path.join(configPath, filename)
            print(src)
            print(dest)
            shutil.copy(src, dest)

    def deleteCalibrationFileButtonPressed(self):
        print("CalibrationEditWindow - Remove Calibration File Pressed")
        configName = self.name
        calibrationDir = os.path.splitext(configName)[0] + "_Calibration"
        configPath = os.path.join("Config", calibrationDir)
        os.remove(os.path.join(configPath,self.calibrationFileComboBox.currentText()))
        # os.remove(configPath)


    def getCalibrationSettings(self):
        print("CalibrationEditWindow - getCalibrationSettings")
        ConfigFile.refreshCalibrationFiles()
        calFileName = self.calibrationFileComboBox.currentText()
        calConfig = ConfigFile.getCalibrationConfig(calFileName)
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
        if disabled:
            ConfigFile.settings["bL1aCleanSZA"] = 0
        else:
            ConfigFile.settings["bL1aCleanSZA"] = 1

    def l1aqcSolarTrackerCheckBoxUpdate(self):
        print("ConfigWindow - l1aqcSolarTrackerCheckBoxUpdate")

        disabled = (not self.l1aqcSolarTrackerCheckBox.isChecked())
        self.l1aqcRotatorDelayLabel.setDisabled(disabled)
        self.l1aqcRotatorDelayLineEdit.setDisabled(disabled)
        self.l1aqcRotatorDelayCheckBox.setDisabled(disabled)
        self.l1aqcCleanPitchRollCheckBox.setDisabled(disabled)
        self.l1aqcCleanPitchRollLabel.setDisabled(disabled)
        self.l1aqcPitchRollPitchLabel.setDisabled(disabled)
        self.l1aqcPitchRollPitchLineEdit.setDisabled(disabled)
        self.l1aqcRotatorAngleLabel.setDisabled(disabled)
        self.l1aqcRotatorAngleCheckBox.setDisabled(disabled)
        self.l1aqcRotatorAngleMinLabel.setDisabled(disabled)
        self.l1aqcRotatorAngleMinLineEdit.setDisabled(disabled)
        self.l1aqcRotatorAngleMaxLabel.setDisabled(disabled)
        self.l1aqcRotatorAngleMaxLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL1aqcSolarTracker"] = 0
            ConfigFile.settings["bL1aqcCleanPitchRoll"] = 0
            ConfigFile.settings["bL1aqcRotatorDelay"] = 0
            self.l1aqcRotatorDelayCheckBox.setChecked(False)
            self.l1aqcCleanPitchRollCheckBox.setChecked(False)
            self.l1aqcRotatorAngleCheckBox.setChecked(False)
        else:
            ConfigFile.settings["bL1aqcSolarTracker"] = 1


    def l1aqcRotatorDelayCheckBoxUpdate(self):
        print("ConfigWindow - l1aqcRotatorDelayCheckBoxUpdate")

        disabled = (not self.l1aqcRotatorDelayCheckBox.isChecked())
        # self.l1aqcRotatorDelayLabel.setDisabled(disabled)
        self.l1aqcRotatorDelayLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL1aqcRotatorDelay"] = 0
        else:
            ConfigFile.settings["bL1aqcRotatorDelay"] = 1

    def l1aqcCleanPitchRollCheckBoxUpdate(self):
        print("ConfigWindow - l1aqcCleanPitchRollCheckBoxUpdate")

        disabled = (not self.l1aqcCleanPitchRollCheckBox.isChecked())
        self.l1aqcPitchRollPitchLabel.setDisabled(disabled)
        self.l1aqcPitchRollPitchLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL1aqcCleanPitchRoll"] = 0
        else:
            ConfigFile.settings["bL1aqcCleanPitchRoll"] = 1

    def l1aqcRotatorAngleCheckBoxUpdate(self):
        print("ConfigWindow - l1aqcRotatorAngleCheckBoxUpdate")

        disabled = (not self.l1aqcRotatorAngleCheckBox.isChecked())
        self.l1aqcRotatorAngleMinLabel.setDisabled(disabled)
        self.l1aqcRotatorAngleMinLineEdit.setDisabled(disabled)
        self.l1aqcRotatorAngleMaxLabel.setDisabled(disabled)
        self.l1aqcRotatorAngleMaxLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL1aqcRotatorAngle"] = 0
        else:
            ConfigFile.settings["bL1aqcRotatorAngle"] = 1

    def l1aqcCleanSunAngleCheckBoxUpdate(self):
        print("ConfigWindow - l1aqcCleanSunAngleCheckBoxUpdate")

        disabled = (not self.l1aqcCleanSunAngleCheckBox.isChecked())
        self.l1aqcSunAngleMinLabel.setDisabled(disabled)
        self.l1aqcSunAngleMinLineEdit.setDisabled(disabled)
        self.l1aqcSunAngleMaxLabel.setDisabled(disabled)
        self.l1aqcSunAngleMaxLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL1aqcCleanSunAngle"] = 0
        else:
            ConfigFile.settings["bL1aqcCleanSunAngle"] = 1

    def l1aqcAnomalyButtonPressed(self):
        print("CalibrationEditWindow - Launching anomaly analysis module")
        ConfigWindow.refreshConfig(self)
        # AnomalyDetection(self,self.inputDirectory)
        anomAnalDialog = AnomAnalWindow(self.inputDirectory, self)
        anomAnalDialog.show()

    def l1aqcDeglitchCheckBoxUpdate(self):
        print("ConfigWindow - l1aqcDeglitchCheckBoxUpdate")

        disabled = (not self.l1aqcDeglitchCheckBox.isChecked())
        if disabled:
            ConfigFile.settings["bL1dDeglitch"]   = 0
        else:
            ConfigFile.settings["bL1dDeglitch"]   = 1

    def l1bPlotTimeInterpCheckBoxUpdate(self):
        print("ConfigWindow - l1bPlotTimeInterpCheckBoxUpdate")

    def l1bSaveSeaBASSCheckBoxUpdate(self):
        print("ConfigWindow - l1bSaveSeaBASSCheckBoxUpdate")
        disabled = (not self.l1bSaveSeaBASSCheckBox.isChecked()) \
                and (not self.l2SaveSeaBASSCheckBox.isChecked())
        self.l1bSeaBASSHeaderEditButton.setDisabled(disabled)

    def l1bSeaBASSHeaderEditButtonPressed(self):
        print("Edit seaBASSHeader Dialogue")

        ConfigWindow.refreshConfig(self)
        seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
        inputDir = self.inputDirectory
        seaBASSHeaderPath = os.path.join("Config", seaBASSHeaderFileName)
        if os.path.isfile(seaBASSHeaderPath):
            SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)
            # Update comments to reflect any changes in ConfigWindow
            SeaBASSHeaderWindow.configUpdateButtonPressed(self, 'config')
            seaBASSHeaderDialog = SeaBASSHeaderWindow(seaBASSHeaderFileName, inputDir, self)
            seaBASSHeaderDialog.show()
        else:
            # print("Creating New SeaBASSHeader File: ", seaBASSHeaderFileName)
            # SeaBASSHeader.createDefaultSeaBASSHeader(seaBASSHeaderFileName)
            # SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)
            # seaBASSHeaderDialog = SeaBASSHeaderWindow(seaBASSHeaderFileName, inputDir, self)
            # seaBASSHeaderDialog.show()
            print("SeaBass Header file lost.")

    def l2pGetAncCheckBoxUpdate(self):
        print("ConfigWindow - l2pGetAncCheckBoxUpdate")

        if self.l2pGetAncCheckBox.isChecked():
            if not ConfigFile.settings["bL2pObpgCreds"]:
                usr = QtWidgets.QInputDialog.getText(None,
                                                "Earthdata Username",
                                                "Username (Cancel to use current credentials):",
                                                QtWidgets.QLineEdit.Normal,
                                                "")
                if usr[1]:
                    pwd = QtWidgets.QInputDialog.getText(None,
                                                    "Earthdata Password",
                                                    "Password:",
                                                    QtWidgets.QLineEdit.Normal,
                                                    "")
                    GetAnc.userCreds(usr[0],pwd[0])
                else:
                    # If the user cancels out of these, presume their account is
                    # already set up properly and skip netrc file creation.
                    print('Credentials skipped. Will try to use current credentials.')
                    ConfigFile.settings["bL2pObpgCreds"] = 1

            ConfigFile.settings["bL2pGetAnc"] = 1
            # self.RhoRadoButton3C.setDisabled(0)
            self.RhoRadioButtonZhang.setDisabled(0)
        else:
            ConfigFile.settings["bL2pGetAnc"] = 0
            ConfigFile.settings["bL2pObpgCreds"] = 0
            self.RhoRadioButtonZhang.setChecked(0)
            self.RhoRadioButtonZhang.setDisabled(1)
            # self.RhoRadoButton3C.setChecked(1)
            self.RhoRadioButtonDefault.setChecked(1)

            print("ConfigWindow - l2RhoCorrection set to M99")
            ConfigFile.settings["bL23CRho"] = 0
            ConfigFile.settings["bL2ZhangRho"] = 0
            ConfigFile.settings["bL2DefaultRho"] = 1

    def l2LtUVNIRCheckBoxUpdate(self):
        print("ConfigWindow - l2UVNIRCheckBoxUpdate")

        if self.l2LtUVNIRCheckBox.isChecked():
            ConfigFile.settings["bL2LtUVNIR"] = 1
        else:
            ConfigFile.settings["bL2LtUVNIR"] = 0

    def l2SpecQualityCheckBoxUpdate(self):
        print("ConfigWindow - l2SpecQualityCheckBoxUpdate")

        disabled = (not self.l2SpecQualityCheckBox.isChecked())
        self.l2SpecFilterLiLabel.setDisabled(disabled)
        self.l2SpecFilterLiLineEdit.setDisabled(disabled)
        self.l2SpecFilterLtLabel.setDisabled(disabled)
        self.l2SpecFilterLtLineEdit.setDisabled(disabled)
        self.l2SpecFilterEsLabel.setDisabled(disabled)
        self.l2SpecFilterEsLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL2EnableSpecQualityCheck"] = 0
        else:
            ConfigFile.settings["bL2EnableSpecQualityCheck"] = 1
        #     ConfigFile.settings["fL2SpecFilterEs"] = "NA"
        #     ConfigFile.settings["fL2SpecFilterLi"] = "NA"
        #     ConfigFile.settings["fL2SpecFilterLt"] = "NA"

    def l2QualityFlagCheckBoxUpdate(self):
        print("ConfigWindow - l2QualityFlagCheckBoxUpdate")

        disabled = (not self.l2QualityFlagCheckBox.isChecked())
        self.l2CloudFlagLabel.setDisabled(disabled)
        self.l2CloudFlagLineEdit.setDisabled(disabled)
        self.l2EsFlagLabel.setDisabled(disabled)
        self.l2EsFlagLineEdit.setDisabled(disabled)
        self.l2DawnDuskFlagLabel.setDisabled(disabled)
        self.l2DawnDuskFlagLineEdit.setDisabled(disabled)
        self.l2RainfallHumidityFlagLabel.setDisabled(disabled)
        self.l2RainfallHumidityFlagLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL2EnableQualityFlags"] = 0
        else:
            ConfigFile.settings["bL2EnableQualityFlags"] = 1
        #     ConfigFile.settings["fL2CloudFlag"] = "NA"
        #     ConfigFile.settings["fL2SignificantEsFlag"] = "NA"
        #     ConfigFile.settings["fL2DawnDuskFlag"] = "NA"
        #     ConfigFile.settings["fL2RainfallHumidityFlag"] = "NA"

    def l2StationsCheckBoxUpdate(self):
        print("ConfigWindow - l2StationsCheckBoxUpdate")

        disabled = (not self.l2StationsCheckBox.isChecked())
        if disabled:
            ConfigFile.settings["bL2Stations"] = 0
        else:
            ConfigFile.settings["bL2Stations"] = 1

    def l2EnablePercentLtCheckBoxUpdate(self):
        print("ConfigWindow - l2EnablePercentLtCheckBoxUpdate")

        disabled = (not self.l2EnablePercentLtCheckBox.isChecked())
        self.l2PercentLtLabel.setDisabled(disabled)
        self.l2PercentLtLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL2EnablePercentLt"] = 0
        else:
            ConfigFile.settings["bL2EnablePercentLt"] = 1
        #     ConfigFile.settings["fL2PercentLt"] = "NA"

    def l2RhoRadoButton3CClicked(self):
        print("ConfigWindow - l2RhoCorrection set to Ruddick")
        self.RhoRadoButton3C.setChecked(True)
        self.RhoRadioButtonZhang.setChecked(False)
        self.RhoRadioButtonDefault.setChecked(False)
        ConfigFile.settings["bL23CRho"] = 1
        ConfigFile.settings["bL2ZhangRho"] = 0
        ConfigFile.settings["bL2DefaultRho"] = 0

    def l2RhoRadioButtonZhangClicked(self):
        print("ConfigWindow - l2RhoCorrection set to Zhang")
        self.RhoRadoButton3C.setChecked(False)
        self.RhoRadioButtonZhang.setChecked(True)
        self.RhoRadioButtonDefault.setChecked(False)
        ConfigFile.settings["bL23CRho"] = 0
        ConfigFile.settings["bL2ZhangRho"] = 1
        ConfigFile.settings["bL2DefaultRho"] = 0
        if float(self.l2SZAMaxLineEdit.text()) > 60:
            print("SZA outside model limits; adjusting to 60")
            ConfigFile.settings["fL2SZAMax"] = 60
            self.l2SZAMaxLineEdit.setText(str(ConfigFile.settings["fL2SZAMax"]))

    def l2RhoRadioButtonDefaultClicked(self):
        print("ConfigWindow - l2RhoCorrection set to Default")
        self.RhoRadoButton3C.setChecked(False)
        self.RhoRadioButtonZhang.setChecked(False)
        self.RhoRadioButtonDefault.setChecked(True)
        ConfigFile.settings["bL23CRho"] = 0
        ConfigFile.settings["bL2ZhangRho"] = 0
        ConfigFile.settings["bL2DefaultRho"] = 1

    def l2RhoRadioButtonYourClicked(self):
        print("ConfigWindow - l2RhoCorrection set to Default. You have not submitted your method.")
        self.RhoRadoButton3C.setChecked(False)
        self.RhoRadioButtonZhang.setChecked(False)
        self.RhoRadioButtonYour.setChecked(True)
        ConfigFile.settings["bL23CRho"] = 0
        ConfigFile.settings["bL2ZhangRho"] = 0
        ConfigFile.settings["bL2DefaultRho"] = 1 # This is a mock up. Use Default

    def l2SimpleNIRRadioButtonClicked(self):
        print("ConfigWindow - l2NIRCorrection set to Simple")
        self.SimpleNIRRadioButton.setChecked(True)
        self.SimSpecNIRRadioButton.setChecked(False)
        self.YourNIRRadioButton.setChecked(False)
        ConfigFile.settings["bL2SimpleNIRCorrection"] = 1
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = 0
    def l2SimSpecNIRRadioButtonClicked(self):
        self.SimpleNIRRadioButton.setChecked(False)
        self.SimSpecNIRRadioButton.setChecked(True)
        self.YourNIRRadioButton.setChecked(False)
        print("ConfigWindow - l2NIRCorrection set to SimSpec")
        ConfigFile.settings["bL2SimpleNIRCorrection"] = 0
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = 1
    def l2YourNIRRadioButtonClicked(self):
        self.SimpleNIRRadioButton.setChecked(True)
        self.SimSpecNIRRadioButton.setChecked(False)
        self.YourNIRRadioButton.setChecked(True)
        print("ConfigWindow - l2NIRCorrection set to Simple. You have not submitted Your method.")
        ConfigFile.settings["bL2SimpleNIRCorrection"] = 1 # Mock up. Use Simple
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = 0

    def l2NIRCorrectionCheckBoxUpdate(self):
        print("ConfigWindow - l2NIRCorrectionCheckBoxUpdate")

        disabled = (not self.l2NIRCorrectionCheckBox.isChecked())
        self.SimpleNIRRadioButton.setDisabled(disabled)
        self.SimSpecNIRRadioButton.setDisabled(disabled)
        self.YourNIRRadioButton.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL2PerformNIRCorrection"] = 0
        else:
            ConfigFile.settings["bL2PerformNIRCorrection"] = 1

    def l2NegativeSpecCheckBoxUpdate(self):
        print("ConfigWindow - l2NegativeSpecCheckBoxUpdate")

        disabled = (not self.l2NegativeSpecCheckBox.isChecked())
        if disabled:
            ConfigFile.settings["bL2NegativeSpec"] = 0
        else:
            ConfigFile.settings["bL2NegativeSpec"] = 1


    def l2OCproductsButtonPressed(self):
        print("OC Products Dialogue")

        ConfigWindow.refreshConfig(self)
        OCproductsDialog = OCproductsWindow(self)
        OCproductsDialog.exec()

        if int(ConfigFile.settings["bL2WeightMODISA"]) == 1:
            self.l2WeightMODISACheckBox.setChecked(True)


    def l2SaveSeaBASSCheckBoxUpdate(self):
        print("ConfigWindow - l2SaveSeaBASSCheckBoxUpdate")
        disabled = (not self.l1bSaveSeaBASSCheckBox.isChecked()) \
                and (not self.l2SaveSeaBASSCheckBox.isChecked())
        self.l1bSeaBASSHeaderEditButton.setDisabled(disabled)

    def l2WriteReportCheckBoxUpdate(self):
        print("ConfigWindow - l2WriteReportCheckBoxUpdate")
        # disabled = not self.l2WriteReportCheckBox.isChecked()

    def saveButtonPressed(self):
        print("ConfigWindow - Save Pressed")

        ConfigWindow.refreshConfig(self)

        ConfigFile.saveConfig(self.name)

        # Confirm that SeaBASS Headers need to be/are updated
        SeaBASSHeader.loadSeaBASSHeader(ConfigFile.settings["seaBASSHeaderFileName"])
        # This now updates the SeaBASS Header comments to reflect the ConfigWindow parameters automatically.
        SeaBASSHeaderWindow.configUpdateButtonPressed(self, 'config')
        SeaBASSHeader.saveSeaBASSHeader(ConfigFile.settings["seaBASSHeaderFileName"])

        self.close()

    def refreshConfig(self):
        print("ConfigWindow - refreshConfig")

        ConfigFile.settings["bL1aCleanSZA"] = int(self.l1aCleanSZACheckBox.isChecked())
        ConfigFile.settings["fL1aCleanSZAMax"] = float(self.l1aCleanSZAMaxLineEdit.text())

        ConfigFile.settings["bL1aqcSolarTracker"] = int(self.l1aqcSolarTrackerCheckBox.isChecked())
        ConfigFile.settings["fL1aqcRotatorHomeAngle"] = float(self.l1aqcRotatorHomeAngleLineEdit.text())
        ConfigFile.settings["bL1aqcRotatorDelay"] = int(self.l1aqcRotatorDelayCheckBox.isChecked())
        ConfigFile.settings["fL1aqcRotatorDelay"] = float(self.l1aqcRotatorDelayLineEdit.text())
        ConfigFile.settings["bL1aqcCleanPitchRoll"] = int(self.l1aqcCleanPitchRollCheckBox.isChecked())
        ConfigFile.settings["fL1aqcPitchRollPitch"] = float(self.l1aqcPitchRollPitchLineEdit.text())
        ConfigFile.settings["fL1aqcPitchRollRoll"] = float(self.l1aqcPitchRollPitchLineEdit.text())
        ConfigFile.settings["bL1aqcRotatorAngle"] = int(self.l1aqcRotatorAngleCheckBox.isChecked())
        ConfigFile.settings["fL1aqcRotatorAngleMin"] = float(self.l1aqcRotatorAngleMinLineEdit.text())
        ConfigFile.settings["fL1aqcRotatorAngleMax"] = float(self.l1aqcRotatorAngleMaxLineEdit.text())
        ConfigFile.settings["bL1aqcCleanSunAngle"] = int(self.l1aqcCleanSunAngleCheckBox.isChecked())
        ConfigFile.settings["fL1aqcSunAngleMin"] = float(self.l1aqcSunAngleMinLineEdit.text())
        ConfigFile.settings["fL1aqcSunAngleMax"] = float(self.l1aqcSunAngleMaxLineEdit.text())

        ConfigFile.settings["bL1dDeglitch"] = int(self.l1aqcDeglitchCheckBox.isChecked())

        ConfigFile.settings["fL1bInterpInterval"] = float(self.l1bInterpIntervalLineEdit.text())
        ConfigFile.settings["bL1bPlotTimeInterp"] = int(self.l1bPlotTimeInterpCheckBox.isChecked())
        ConfigFile.settings["bL1bSaveSeaBASS"] = int(self.l1bSaveSeaBASSCheckBox.isChecked())

        ConfigFile.settings["bL2pGetAnc"] = int(self.l2pGetAncCheckBox.isChecked())

        ConfigFile.settings["bL2LtUVNIR"] = int(self.l2LtUVNIRCheckBox.isChecked())
        ConfigFile.settings["fL2MaxWind"] = float(self.l2MaxWindLineEdit.text())
        ConfigFile.settings["fL2SZAMin"] = float(self.l2SZAMinLineEdit.text())
        if int(self.RhoRadioButtonZhang.isChecked()) and float(self.l2SZAMaxLineEdit.text()) > 60:
            print("SZA outside Zhang model limits; adjusting.")
            self.l2SZAMaxLineEdit.setText(str(60.0))
        ConfigFile.settings["fL2SZAMax"] = float(self.l2SZAMaxLineEdit.text())
        ConfigFile.settings["bL2EnableSpecQualityCheck"] = int(self.l2SpecQualityCheckBox.isChecked())
        ConfigFile.settings["fL2SpecFilterEs"] = float(self.l2SpecFilterEsLineEdit.text())
        ConfigFile.settings["fL2SpecFilterLi"] = float(self.l2SpecFilterLiLineEdit.text())
        ConfigFile.settings["fL2SpecFilterLt"] = float(self.l2SpecFilterLtLineEdit.text())

        ConfigFile.settings["bL2EnableQualityFlags"] = int(self.l2QualityFlagCheckBox.isChecked())
        ConfigFile.settings["fL2CloudFlag"] = float(self.l2CloudFlagLineEdit.text())
        ConfigFile.settings["fL2SignificantEsFlag"] = float(self.l2EsFlagLineEdit.text())
        ConfigFile.settings["fL2DawnDuskFlag"] = float(self.l2DawnDuskFlagLineEdit.text())
        ConfigFile.settings["fL2RainfallHumidityFlag"] = float(self.l2RainfallHumidityFlagLineEdit.text())

        ConfigFile.settings["bL2Stations"] = int(self.l2StationsCheckBox.isChecked())
        ConfigFile.settings["fL2TimeInterval"] = int(self.l2TimeIntervalLineEdit.text())
        ConfigFile.settings["bL2EnablePercentLt"] = int(self.l2EnablePercentLtCheckBox.isChecked())
        ConfigFile.settings["fL2PercentLt"] = float(self.l2PercentLtLineEdit.text())

        ConfigFile.settings["fL2DefaultWindSpeed"] = float(self.l2DefaultWindSpeedLineEdit.text())
        ConfigFile.settings["fL2DefaultAOD"] = float(self.l2DefaultAODLineEdit.text())
        ConfigFile.settings["fL2DefaultSalt"] = float(self.l2DefaultSaltLineEdit.text())
        ConfigFile.settings["fL2DefaultSST"] = float(self.l2DefaultSSTLineEdit.text())
        # ConfigFile.settings["fL2RhoSky"] = float(self.l2RhoSkyLineEdit.text())
        ConfigFile.settings["bL23CRho"] = int(self.RhoRadoButton3C.isChecked())
        ConfigFile.settings["bL2ZhangRho"] = int(self.RhoRadioButtonZhang.isChecked())
        ConfigFile.settings["bL2DefaultRho"] = int(self.RhoRadioButtonDefault.isChecked())

        ConfigFile.settings["bL2PerformNIRCorrection"] = int(self.l2NIRCorrectionCheckBox.isChecked())
        ConfigFile.settings["bL2SimpleNIRCorrection"] = int(self.SimpleNIRRadioButton.isChecked())
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = int(self.SimSpecNIRRadioButton.isChecked())

        ConfigFile.settings["bL2NegativeSpec"] = int(self.l2NegativeSpecCheckBox.isChecked())

        ConfigFile.settings["bL2WeightMODISA"] = int(self.l2WeightMODISACheckBox.isChecked())
        ConfigFile.settings["bL2WeightSentinel3A"] = int(self.l2WeightSentinel3ACheckBox.isChecked())
        ConfigFile.settings["bL2WeightVIIRSN"] = int(self.l2WeightVIIRSNCheckBox.isChecked())
        ConfigFile.settings["bL2WeightMODIST"] = int(self.l2WeightMODISTCheckBox.isChecked())
        ConfigFile.settings["bL2WeightSentinel3B"] = int(self.l2WeightSentinel3BCheckBox.isChecked())
        ConfigFile.settings["bL2WeightVIIRSJ"] = int(self.l2WeightVIIRSJCheckBox.isChecked())
        ConfigFile.settings["bL2PlotRrs"] = int(self.l2PlotRrsCheckBox.isChecked())
        ConfigFile.settings["bL2PlotnLw"] = int(self.l2PlotnLwCheckBox.isChecked())
        ConfigFile.settings["bL2PlotEs"] = int(self.l2PlotEsCheckBox.isChecked())
        ConfigFile.settings["bL2PlotLi"] = int(self.l2PlotLiCheckBox.isChecked())
        ConfigFile.settings["bL2PlotLt"] = int(self.l2PlotLtCheckBox.isChecked())
        ConfigFile.settings["bL2SaveSeaBASS"] = int(self.l2SaveSeaBASSCheckBox.isChecked())
        ConfigFile.settings["bL2WriteReport"] = int(self.l2WriteReportCheckBox.isChecked())

        # ConfigFile.saveConfig(self.name) # overkill?

        # Confirm necessary satellite bands are processed
        if ConfigFile.products["bL2Prodoc3m"] or ConfigFile.products["bL2Prodkd490"] or \
            ConfigFile.products["bL2Prodpic"] or ConfigFile.products["bL2Prodpoc"] or \
                ConfigFile.products["bL2Prodgocad"] or ConfigFile.products["bL2Prodgiop"] or \
                ConfigFile.products["bL2Prodqaa"]:

            ConfigFile.settings["bL2WeightMODISA"] = 1
            self.l2WeightMODISACheckBox.setChecked(True)


    def saveAsButtonPressed(self):
        print("ConfigWindow - Save As Pressed")
        self.newName, ok = QtWidgets.QInputDialog.getText(self, 'Save As Config File', 'Enter File Name')
        if ok:
            print("Create Config File: ", self.newName)

            if not self.newName.endswith(".cfg"):
                self.newName = self.newName + ".cfg"
                # oldConfigName = ConfigFile.filename
            ConfigFile.filename = self.newName
            # self.name = self.newName

            ConfigWindow.refreshConfig(self)
            ConfigFile.saveConfig(ConfigFile.filename)

            # Copy Calibration files into new Config folder
            fnames = ConfigFile.settings['CalibrationFiles']
            oldConfigName = self.name
            newConfigName = ConfigFile.filename
            oldCalibrationDir = os.path.splitext(oldConfigName)[0] + "_Calibration"
            newCalibrationDir = os.path.splitext(newConfigName)[0] + "_Calibration"
            oldConfigPath = os.path.join("Config", oldCalibrationDir)
            newConfigPath = os.path.join("Config", newCalibrationDir)
            for src in fnames:
                srcPath = os.path.join(oldConfigPath, src)
                destPath = os.path.join(newConfigPath, src)
                print(srcPath)
                print(destPath)
                shutil.copy(srcPath, destPath)

            # Confirm that SeaBASS Headers need to be/are updated
            if ConfigFile.settings["bL1bSaveSeaBASS"] or ConfigFile.settings["bL2SaveSeaBASS"]:
                SeaBASSHeaderWindow.configUpdateButtonPressed(self, 'config')
            else:
                self.close()


    def cancelButtonPressed(self):
        print("ConfigWindow - Cancel Pressed")
        self.close()

