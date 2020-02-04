
import os
import shutil
from PyQt5 import QtCore, QtGui, QtWidgets


from ConfigFile import ConfigFile
from AnomalyDetection import AnomalyDetection
from SeaBASSHeader import SeaBASSHeader
from SeaBASSHeaderWindow import SeaBASSHeaderWindow
from GetAnc import GetAnc



class ConfigWindow(QtWidgets.QDialog):
    def __init__(self, name, inputDir, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.name = name
        self.inputDirectory = inputDir
        self.initUI()

    def initUI(self):
        # print("ConfigWindow - initUI")
        # nameLabel = QtWidgets.QLabel("Editing: " + self.name, self)

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


        # L1B
        l1bLabel = QtWidgets.QLabel("Level 1B Processing", self)        
        l1bLabel_font = l1bLabel.font()
        l1bLabel_font.setPointSize(12)
        l1bLabel_font.setBold(True)
        l1bLabel.setFont(l1bLabel_font)
        l1bSublabel = QtWidgets.QLabel(" Apply factory calibrations", self)    


        # L1C (Main)
        l1cLabel = QtWidgets.QLabel("Level 1C Processing", self)
        l1cLabel_font = l1cLabel.font()
        l1cLabel_font.setPointSize(12)
        l1cLabel_font.setBold(True)
        l1cLabel.setFont(l1cLabel_font)
        l1cSublabel = QtWidgets.QLabel(" Filter on pitch, roll, yaw, and azimuth", self)        
        # l1cSublabel2 = QtWidgets.QLabel("   relative solar azimuth.", self)
        # l1cSublabel3 = QtWidgets.QLabel("   factory calibrations.", self)        

        # L1C Rotator 
        self.l1cRotatorHomeAngleLabel = QtWidgets.QLabel(" Rotator Home Angle Offset", self)
        self.l1cRotatorHomeAngleLineEdit = QtWidgets.QLineEdit(self)
        self.l1cRotatorHomeAngleLineEdit.setText(str(ConfigFile.settings["fL1cRotatorHomeAngle"]))
        self.l1cRotatorHomeAngleLineEdit.setValidator(doubleValidator)   

        self.l1cRotatorDelayLabel = QtWidgets.QLabel(" Rotator Delay (Seconds)", self)
        self.l1cRotatorDelayLineEdit = QtWidgets.QLineEdit(self)
        self.l1cRotatorDelayLineEdit.setText(str(ConfigFile.settings["fL1cRotatorDelay"]))
        self.l1cRotatorDelayLineEdit.setValidator(doubleValidator)     

        # L1C Pitch and Roll
        l1cCleanPitchRollLabel = QtWidgets.QLabel(" Pitch & Roll Filter", self)                        
        self.l1cCleanPitchRollCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1cCleanPitchRoll"]) == 1:
            self.l1cCleanPitchRollCheckBox.setChecked(True)
        self.l1cPitchRollPitchLabel = QtWidgets.QLabel("       Max Pitch Angle", self)
        self.l1cPitchRollPitchLineEdit = QtWidgets.QLineEdit(self)
        self.l1cPitchRollPitchLineEdit.setText(str(ConfigFile.settings["fL1cPitchRollPitch"]))
        self.l1cPitchRollPitchLineEdit.setValidator(doubleValidator)
        self.l1cPitchRollRollLabel = QtWidgets.QLabel("       Max Roll Angle", self)
        self.l1cPitchRollRollLineEdit = QtWidgets.QLineEdit(self)
        self.l1cPitchRollRollLineEdit.setText(str(ConfigFile.settings["fL1cPitchRollRoll"]))
        self.l1cPitchRollRollLineEdit.setValidator(doubleValidator)        
        self.l1cCleanPitchRollCheckBoxUpdate()        

         # L1C Rotator                
        l1cCleanRotatorAngleLabel = QtWidgets.QLabel(" Absolute Rotator Angle Filter", self)                        
        self.l1cCleanRotatorAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1cCleanRotatorAngle"]) == 1:
            self.l1cCleanRotatorAngleCheckBox.setChecked(True)
        self.l1cRotatorAngleMinLabel = QtWidgets.QLabel("       Rotator Angle Min", self)
        self.l1cRotatorAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l1cRotatorAngleMinLineEdit.setText(str(ConfigFile.settings["fL1cRotatorAngleMin"]))
        self.l1cRotatorAngleMinLineEdit.setValidator(doubleValidator)
        self.l1cRotatorAngleMaxLabel = QtWidgets.QLabel("       Rotator Angle Max", self)
        self.l1cRotatorAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l1cRotatorAngleMaxLineEdit.setText(str(ConfigFile.settings["fL1cRotatorAngleMax"]))
        self.l1cRotatorAngleMaxLineEdit.setValidator(doubleValidator)        
        self.l1cCleanRotatorAngleCheckBoxUpdate()        

        # L1C Relative SZA
        l1cCleanSunAngleLabel = QtWidgets.QLabel(" Relative Solar Azimuth Filter", self)
        self.l1cCleanSunAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1cCleanSunAngle"]) == 1:
            self.l1cCleanSunAngleCheckBox.setChecked(True)        
        self.l1cSunAngleMinLabel = QtWidgets.QLabel("       Rel Angle Min", self)
        self.l1cSunAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l1cSunAngleMinLineEdit.setText(str(ConfigFile.settings["fL1cSunAngleMin"]))
        self.l1cSunAngleMinLineEdit.setValidator(doubleValidator)
        self.l1cSunAngleMaxLabel = QtWidgets.QLabel("       Rel Angle Max", self)
        self.l1cSunAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l1cSunAngleMaxLineEdit.setText(str(ConfigFile.settings["fL1cSunAngleMax"]))
        self.l1cSunAngleMaxLineEdit.setValidator(doubleValidator)
        self.l1cCleanSunAngleCheckBoxUpdate() 
        
        self.l1cCleanPitchRollCheckBox.clicked.connect(self.l1cCleanPitchRollCheckBoxUpdate)
        self.l1cCleanRotatorAngleCheckBox.clicked.connect(self.l1cCleanRotatorAngleCheckBoxUpdate)
        self.l1cCleanSunAngleCheckBox.clicked.connect(self.l1cCleanSunAngleCheckBoxUpdate)


        # L1D (Main)
        l1dLabel = QtWidgets.QLabel("Level 1D Processing", self)
        l1dLabel_font = l1dLabel.font()
        l1dLabel_font.setPointSize(12)
        l1dLabel_font.setBold(True)
        l1dLabel.setFont(l1dLabel_font)
        l1dSublabel = QtWidgets.QLabel("Data deglitching and shutter dark corrections", self)  
        
        # L1D Deglitcher
        self.l1dDeglitchLabel = QtWidgets.QLabel("  Deglitch data", self)                
        self.l1dDeglitchCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1dDeglitch"]) == 1:
            self.l1dDeglitchCheckBox.setChecked(True)

        self.l1dDeglitch0Label = QtWidgets.QLabel("     Window for Darks (odd)", self)
        self.l1dDeglitch0LineEdit = QtWidgets.QLineEdit(self)
        self.l1dDeglitch0LineEdit.setText(str(ConfigFile.settings["fL1dDeglitch0"]))
        self.l1dDeglitch0LineEdit.setValidator(intValidator)
        # self.l1dDeglitch0LineEdit.setValidator(oddValidator)

        self.l1dDeglitch1Label = QtWidgets.QLabel("     Window for Lights (odd)", self)
        self.l1dDeglitch1LineEdit = QtWidgets.QLineEdit(self)
        self.l1dDeglitch1LineEdit.setText(str(ConfigFile.settings["fL1dDeglitch1"]))
        self.l1dDeglitch1LineEdit.setValidator(intValidator)
        # self.l1dDeglitch1LineEdit.setValidator(oddValidator)

        self.l1dDeglitch2Label = QtWidgets.QLabel("     Sigma Factor Darks", self)
        self.l1dDeglitch2LineEdit = QtWidgets.QLineEdit(self)
        self.l1dDeglitch2LineEdit.setText(str(ConfigFile.settings["fL1dDeglitch2"]))
        self.l1dDeglitch2LineEdit.setValidator(doubleValidator)
        
        self.l1dDeglitch3Label = QtWidgets.QLabel("     Sigma Factor Lights", self)
        self.l1dDeglitch3LineEdit = QtWidgets.QLineEdit(self)
        self.l1dDeglitch3LineEdit.setText(str(ConfigFile.settings["fL1dDeglitch3"]))
        self.l1dDeglitch3LineEdit.setValidator(doubleValidator)

        self.l1dDeglitchCheckBoxUpdate()      

        self.l1dDeglitchCheckBox.clicked.connect(self.l1dDeglitchCheckBoxUpdate)   

        # L1D Launch Deglitcher Analysis 
        l1dAnomalySublabel1 = QtWidgets.QLabel("  Launch Anom. Anal. to test params on L1C. Save config",self)
        l1dAnomalySublabel2 = QtWidgets.QLabel("   after updating params. Results saved to /Plot/L1C_Anoms.",self)
        # l1dAnomalySublabel3 = QtWidgets.QLabel("   ", self)  
        l1dAnomalyStepLabel = QtWidgets.QLabel("   Waveband interval to plot (integer): ", self)  
        self.l1dAnomalyStepLineEdit = QtWidgets.QLineEdit(self)
        self.l1dAnomalyStepLineEdit.setText(str(ConfigFile.settings["bL1dAnomalyStep"]))
        self.l1dAnomalyStepLineEdit.setValidator(intValidator)
        self.l1dAnomalyButton = QtWidgets.QPushButton("Anomaly Analysis")
        self.l1dAnomalyButton.clicked.connect(self.l1dAnomalyButtonPressed)


        # L1E
        l1eLabel = QtWidgets.QLabel("Level 1E Processing", self)
        l1eLabel_font = l1eLabel.font()
        l1eLabel_font.setPointSize(12)
        l1eLabel_font.setBold(True)
        l1eLabel.setFont(l1eLabel_font)
        l1eSublabel = QtWidgets.QLabel(" Interpolation to common wavelengths.", self)
        l1eSublabel2 = QtWidgets.QLabel(" Interpolate to common time coordinates.", self)
        l1eInterpIntervalLabel = QtWidgets.QLabel("     Interpolation Interval (nm)", self)
        self.l1eInterpIntervalLineEdit = QtWidgets.QLineEdit(self)
        self.l1eInterpIntervalLineEdit.setText(str(ConfigFile.settings["fL1eInterpInterval"]))
        self.l1eInterpIntervalLineEdit.setValidator(doubleValidator)

        l1ePlotTimeInterpLabel = QtWidgets.QLabel("Generate Plots (slow; saved in ./Plots/L1E/)", self)        
        self.l1ePlotTimeInterpCheckBox = QtWidgets.QCheckBox("", self)                    
        if int(ConfigFile.settings["bL1ePlotTimeInterp"]) == 1:
            self.l1ePlotTimeInterpCheckBox.setChecked(True)   
        self.l1ePlotTimeInterpCheckBox.clicked.connect(self.l1ePlotTimeInterpCheckBoxUpdate)   

        l1eSaveSeaBASSLabel = QtWidgets.QLabel("Save SeaBASS text file", self)        
        self.l1eSaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)                    
        if int(ConfigFile.settings["bL1eSaveSeaBASS"]) == 1:
            self.l1eSaveSeaBASSCheckBox.setChecked(True)   
        self.l1eSaveSeaBASSCheckBox.clicked.connect(self.l1eSaveSeaBASSCheckBoxUpdate)         

        # L1E SeaBASSHeader File
        '''# Can't figure out how to change the index when the window is drawn, so creating
         a lineedit instead. It should be a pull-down, then drop the "Open" box.'''
        # l1eSeaBASSfsm = QtWidgets.QFileSystemModel()
        # index = l1eSeaBASSfsm.setRootPath("Config")        
        self.l1eSeaBASSHeaderLabel = QtWidgets.QLabel('       SeaBASS Header File', self)
        # #self.l1eSeaBASSHeaderLabel.move(30, 20)
        # self.l1eSeaBASSHeaderComboBox = QtWidgets.QComboBox(self)
        # self.l1eSeaBASSHeaderComboBox.setModel(l1eSeaBASSfsm)
        # l1eSeaBASSfsm.setNameFilters(["*.hdr"]) 
        # l1eSeaBASSfsm.setNameFilterDisables(False) 
        # l1eSeaBASSfsm.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)
        # self.l1eSeaBASSHeaderComboBox.setRootModelIndex(index) # Sets directory to Config        
        # headFileIndex=self.l1eSeaBASSHeaderComboBox.findText(ConfigFile.settings["seaBASSHeaderFileName"])
        # print(ConfigFile.settings["seaBASSHeaderFileName"])
        # print(headFileIndex)
        # self.l1eSeaBASSHeaderComboBox.setCurrentIndex(headFileIndex)
        #self.l1eSeaBASSHeaderComboBox.move(30, 50)        
        self.l1eSeaBASSHeaderLineEdit = QtWidgets.QLineEdit(ConfigFile.settings["seaBASSHeaderFileName"])        
        self.l1eSeaBASSHeaderNewButton = QtWidgets.QPushButton("New", self)
        self.l1eSeaBASSHeaderOpenButton = QtWidgets.QPushButton("Open", self)
        self.l1eSeaBASSHeaderEditButton = QtWidgets.QPushButton("Edit", self)
        #self.l1eSeaBASSHeaderEditButton.move(130, 80)
        self.l1eSeaBASSHeaderDeleteButton = QtWidgets.QPushButton("Delete", self)
        self.l1eSeaBASSHeaderNewButton.clicked.connect(self.l1eSeaBASSHeaderNewButtonPressed)
        self.l1eSeaBASSHeaderOpenButton.clicked.connect(self.l1eSeaBASSHeaderOpenButtonPressed)
        self.l1eSeaBASSHeaderEditButton.clicked.connect(self.l1eSeaBASSHeaderEditButtonPressed)
        self.l1eSeaBASSHeaderDeleteButton.clicked.connect(self.l1eSeaBASSHeaderDeleteButtonPressed)  

        self.l1eSaveSeaBASSCheckBoxUpdate()

        # L2 (Preliminary)
        l2pLabel = QtWidgets.QLabel("Level 2 Preliminary", self)
        l2pLabel_font = l1eLabel.font()
        l2pLabel_font.setPointSize(12)
        l2pLabel_font.setBold(True)
        l2pLabel.setFont(l1eLabel_font)
        l2pSublabel = QtWidgets.QLabel(" Select here to download GMAO MERRA2 ancillary met data", self)
        l2pSublabel2 = QtWidgets.QLabel(" Required for Zhang correction and fills in gaps in wind data.", self)
        l2pSublabel3 = QtWidgets.QLabel(" WILL PROMPT FOR EARTHDATA USERNAME/PASSWORD", self)
        l2pSublabel4 = QtWidgets.QLabel(
            "<a href=\"https://oceancolor.gsfc.nasa.gov/registration/\">       Register here.</a>", self)
        l2pSublabel4.setOpenExternalLinks(True)

        l2pGetAncLabel = QtWidgets.QLabel("       Download ancillary models", self)        
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

        # L2 Meteorology Flags
        l2QualityFlagLabel = QtWidgets.QLabel("     Enable Meteorological Filters", self)
        # l2QualityFlagLabel2 = QtWidgets.QLabel("    (Wernand 2012, OO XVI)", self)
        self.l2QualityFlagCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2EnableQualityFlags"]) == 1:
            self.l2QualityFlagCheckBox.setChecked(True)

        self.l2CloudFlagLabel = QtWidgets.QLabel("      Cloud Li(750)Es(750)>", self)
        self.l2CloudFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l2CloudFlagLineEdit.setText(str(ConfigFile.settings["fL2CloudFlag"]))
        self.l2CloudFlagLineEdit.setValidator(doubleValidator)

        self.l2EsFlagLabel = QtWidgets.QLabel("      Significant Es(480) (uW cm^-2 nm^-1)", self)
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

        # L2 Rho Sky Correction
        l2RhoSkyLabel = QtWidgets.QLabel("  Skyglint/Sunglint Correction (Rho)", self)
        l2DefaultRhoSkyLabel = QtWidgets.QLabel("     Default Rho", self)
        self.l2RhoSkyLineEdit = QtWidgets.QLineEdit(self)
        self.l2RhoSkyLineEdit.setText(str(ConfigFile.settings["fL2RhoSky"]))
        self.l2RhoSkyLineEdit.setValidator(doubleValidator)
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

        self.RhoRadioButtonRuddick = QtWidgets.QRadioButton("Ruddick et al 2006 Rho")
        if ConfigFile.settings["bL2RuddickRho"]==1:
            self.RhoRadioButtonRuddick.setChecked(True)
        self.RhoRadioButtonRuddick.clicked.connect(self.l2RhoCorrectionRadioButtonClicked)        
        self.RhoRadioButtonZhang = QtWidgets.QRadioButton("Zhang et al 2017 Rho")
        if ConfigFile.settings["bL2ZhangRho"]==1:
            self.RhoRadioButtonZhang.setChecked(True)
        self.RhoRadioButtonZhang.clicked.connect(self.l2RhoCorrectionRadioButtonClicked)
        self.RhoRadioButtonDefault = QtWidgets.QRadioButton("Default Rho")
        if ConfigFile.settings["bL2DefaultRho"]==1:
            self.RhoRadioButtonDefault.setChecked(True)
        self.RhoRadioButtonDefault.clicked.connect(self.l2RhoCorrectionRadioButtonClicked)        

        # self.l2pGetAncCheckBoxUpdate()        

        # L2 NIR AtmoCorr
        l2NIRCorrectionLabel = QtWidgets.QLabel("  Enable NIR Correction (blue water only)", self)
        self.l2NIRCorrectionCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2PerformNIRCorrection"]) == 1:
            self.l2NIRCorrectionCheckBox.setChecked(True)

        # Spectral Weighting
        l2WeightsLabel = QtWidgets.QLabel("  Add weighted satellite spectra:", self)

        l2WeightMODISALabel = QtWidgets.QLabel("AQUA", self)             
        self.l2WeightMODISACheckBox = QtWidgets.QCheckBox("", self)      
        if int(ConfigFile.settings["bL2WeightMODISA"]) == 1:
            self.l2WeightMODISACheckBox.setChecked(True)

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
        l2PlotsLabel = QtWidgets.QLabel("  Generate Spectral Plots", self)
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

        self.l2QualityFlagCheckBox.clicked.connect(self.l2QualityFlagCheckBoxUpdate)
        self.l2SpecQualityCheckBox.clicked.connect(self.l2SpecQualityCheckBoxUpdate)
        # self.l2RuddickRhoCheckBox.clicked.connect(self.l2RuddickRhoCheckBoxUpdate)
        self.l2NIRCorrectionCheckBox.clicked.connect(self.l2NIRCorrectionCheckBoxUpdate)
        self.l2EnablePercentLtCheckBox.clicked.connect(self.l2EnablePercentLtCheckBoxUpdate)

        l2SaveSeaBASSLabel = QtWidgets.QLabel("Save SeaBASS text file", self)     
        self.l2SaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)    
        self.l2SaveSeaBASSCheckBox.clicked.connect(self.l2SaveSeaBASSCheckBoxUpdate)        
        if int(ConfigFile.settings["bL2SaveSeaBASS"]) == 1:
            self.l2SaveSeaBASSCheckBox.setChecked(True)


        self.saveButton = QtWidgets.QPushButton("Save")        
        self.saveAsButton = QtWidgets.QPushButton("Save As")
        self.cancelButton = QtWidgets.QPushButton("Cancel")                      
            
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.saveAsButton.clicked.connect(self.saveAsButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        # Whole Window Box
        VBox = QtWidgets.QVBoxLayout()
        # VBox.addWidget(nameLabel)

        # Vertical Box (left)
        VBox1 = QtWidgets.QVBoxLayout()

        # Calibration Setup
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

        # VBox1.addSpacing(10)

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

        # VBox1.addSpacing(10)

        # L1B
        VBox1.addWidget(l1bLabel)
        VBox1.addWidget(l1bSublabel)

        # L1C
        VBox1.addWidget(l1cLabel)
        VBox1.addWidget(l1cSublabel)
        # VBox1.addWidget(l1cSublabel2)
        # VBox1.addWidget(l1cSublabel3)

        # L1C Rotator
        RotHomeAngleHBox = QtWidgets.QHBoxLayout()       
        RotHomeAngleHBox.addWidget(self.l1cRotatorHomeAngleLabel)
        RotHomeAngleHBox.addWidget(self.l1cRotatorHomeAngleLineEdit)        
        VBox1.addLayout(RotHomeAngleHBox)    
        RotatorDelayHBox = QtWidgets.QHBoxLayout()
        RotatorDelayHBox.addWidget(self.l1cRotatorDelayLabel)
        RotatorDelayHBox.addWidget(self.l1cRotatorDelayLineEdit)
        VBox1.addLayout(RotatorDelayHBox)

        # L1C Pitch & Roll
        PitchRollHBox = QtWidgets.QHBoxLayout()
        PitchRollHBox.addWidget(l1cCleanPitchRollLabel)
        PitchRollHBox.addWidget(self.l1cCleanPitchRollCheckBox)
        VBox1.addLayout(PitchRollHBox)
        RotMinHBox = QtWidgets.QHBoxLayout()
        RotMinHBox.addWidget(self.l1cPitchRollPitchLabel)
        RotMinHBox.addWidget(self.l1cPitchRollPitchLineEdit)
        VBox1.addLayout(RotMinHBox)
        RotMaxHBox = QtWidgets.QHBoxLayout()
        RotMaxHBox.addWidget(self.l1cPitchRollRollLabel)
        RotMaxHBox.addWidget(self.l1cPitchRollRollLineEdit)
        VBox1.addLayout(RotMaxHBox)                        
        
        # L1C Rotator
        rotateHBox = QtWidgets.QHBoxLayout()
        rotateHBox.addWidget(l1cCleanRotatorAngleLabel)
        rotateHBox.addWidget(self.l1cCleanRotatorAngleCheckBox)
        VBox1.addLayout(rotateHBox)
        RotMinHBox = QtWidgets.QHBoxLayout()
        RotMinHBox.addWidget(self.l1cRotatorAngleMinLabel)
        RotMinHBox.addWidget(self.l1cRotatorAngleMinLineEdit)
        VBox1.addLayout(RotMinHBox)
        RotMaxHBox = QtWidgets.QHBoxLayout()
        RotMaxHBox.addWidget(self.l1cRotatorAngleMaxLabel)
        RotMaxHBox.addWidget(self.l1cRotatorAngleMaxLineEdit)
        VBox1.addLayout(RotMaxHBox) 
                        
        # L1C Relative SZA
        CleanSunAngleHBox = QtWidgets.QHBoxLayout()
        CleanSunAngleHBox.addWidget(l1cCleanSunAngleLabel)
        CleanSunAngleHBox.addWidget(self.l1cCleanSunAngleCheckBox)
        VBox1.addLayout(CleanSunAngleHBox)                      
        SunAngleMinHBox = QtWidgets.QHBoxLayout()       
        SunAngleMinHBox.addWidget(self.l1cSunAngleMinLabel)
        SunAngleMinHBox.addWidget(self.l1cSunAngleMinLineEdit)
        VBox1.addLayout(SunAngleMinHBox)         
        SunAngleMaxHBox = QtWidgets.QHBoxLayout()       
        SunAngleMaxHBox.addWidget(self.l1cSunAngleMaxLabel)
        SunAngleMaxHBox.addWidget(self.l1cSunAngleMaxLineEdit)
        VBox1.addLayout(SunAngleMaxHBox)         

        # L1D 
        VBox1.addWidget(l1dLabel)
        VBox1.addWidget(l1dSublabel)

        # L1D Deglitcher
        deglitchHBox = QtWidgets.QHBoxLayout()
        deglitchHBox.addWidget(self.l1dDeglitchLabel)
        deglitchHBox.addWidget(self.l1dDeglitchCheckBox)
        VBox1.addLayout(deglitchHBox)

        # Middle Vertical Box
        VBox2 = QtWidgets.QVBoxLayout()
        VBox2.setAlignment(QtCore.Qt.AlignBottom)                                                    

        deglitch0HBox = QtWidgets.QHBoxLayout()
        deglitch0HBox.addWidget(self.l1dDeglitch0Label)
        deglitch0HBox.addWidget(self.l1dDeglitch0LineEdit)
        VBox2.addLayout(deglitch0HBox)

        deglitch1HBox = QtWidgets.QHBoxLayout()
        deglitch1HBox.addWidget(self.l1dDeglitch1Label)
        deglitch1HBox.addWidget(self.l1dDeglitch1LineEdit)
        VBox2.addLayout(deglitch1HBox)
        
        deglitch2HBox = QtWidgets.QHBoxLayout()
        deglitch2HBox.addWidget(self.l1dDeglitch2Label)
        deglitch2HBox.addWidget(self.l1dDeglitch2LineEdit)
        VBox2.addLayout(deglitch2HBox)

        deglitch3HBox = QtWidgets.QHBoxLayout()
        deglitch3HBox.addWidget(self.l1dDeglitch3Label)
        deglitch3HBox.addWidget(self.l1dDeglitch3LineEdit)
        VBox2.addLayout(deglitch3HBox)

        # VBox2.addSpacing(10)

        # L1D Anomaly Launcher
        # VBox2.addWidget(l1dAnomalyLabel)
        VBox2.addWidget(l1dAnomalySublabel1)
        VBox2.addWidget(l1dAnomalySublabel2)
        # VBox2.addWidget(l1dAnomalySublabel3)
        stepHBox = QtWidgets.QHBoxLayout()
        stepHBox.addWidget(l1dAnomalyStepLabel)
        stepHBox.addWidget(self.l1dAnomalyStepLineEdit)
        VBox2.addLayout(stepHBox)
        VBox2.addWidget(self.l1dAnomalyButton)

        # VBox2.addSpacing(20)   

        #L1E 
        VBox2.addWidget(l1eLabel)
        VBox2.addWidget(l1eSublabel2)
        VBox2.addWidget(l1eSublabel)

        interpHBox = QtWidgets.QHBoxLayout()
        interpHBox.addWidget(l1eInterpIntervalLabel)
        interpHBox.addWidget(self.l1eInterpIntervalLineEdit)
        VBox2.addLayout(interpHBox)

        # VBox2.addSpacing(10)

        l1ePlotTimeInterpHBox = QtWidgets.QHBoxLayout()
        l1ePlotTimeInterpHBox.addWidget(l1ePlotTimeInterpLabel)
        l1ePlotTimeInterpHBox.addWidget(self.l1ePlotTimeInterpCheckBox)    
        VBox2.addLayout(l1ePlotTimeInterpHBox)

        # VBox2.addSpacing(10)
        
        l1eSeaBASSHBox = QtWidgets.QHBoxLayout()
        l1eSeaBASSHBox.addWidget(l1eSaveSeaBASSLabel)
        l1eSeaBASSHBox.addWidget(self.l1eSaveSeaBASSCheckBox)    
        VBox2.addLayout(l1eSeaBASSHBox)

        l1eSeaBASSHeaderHBox = QtWidgets.QHBoxLayout()
        l1eSeaBASSHeaderHBox.addWidget(self.l1eSeaBASSHeaderLabel)
        # l1eSeaBASSHeaderHBox.addWidget(self.l1eSeaBASSHeaderComboBox)
        l1eSeaBASSHeaderHBox.addWidget(self.l1eSeaBASSHeaderLineEdit)
        VBox2.addLayout(l1eSeaBASSHeaderHBox)

        l1eSeaBASSHeaderHBox2 = QtWidgets.QHBoxLayout()
        l1eSeaBASSHeaderHBox2.addWidget(self.l1eSeaBASSHeaderNewButton)
        l1eSeaBASSHeaderHBox2.addWidget(self.l1eSeaBASSHeaderOpenButton)
        l1eSeaBASSHeaderHBox2.addWidget(self.l1eSeaBASSHeaderEditButton)
        l1eSeaBASSHeaderHBox2.addWidget(self.l1eSeaBASSHeaderDeleteButton)
        VBox2.addLayout(l1eSeaBASSHeaderHBox2)    

        # VBox2.addSpacing(20)       

        # L2 (Preliminary)
        VBox2.addWidget(l2pLabel)
        VBox2.addWidget(l2pSublabel)
        VBox2.addWidget(l2pSublabel2)
        VBox2.addWidget(l2pSublabel3)
        VBox2.addWidget(l2pSublabel4)

        l2pGetAncHBox = QtWidgets.QHBoxLayout()
        l2pGetAncHBox.addWidget(l2pGetAncLabel)
        l2pGetAncHBox.addWidget(self.l2pGetAncCheckBox)    
        VBox2.addLayout(l2pGetAncHBox)

        # L2 
        VBox2.addWidget(l2Label)
        VBox2.addWidget(l2Sublabel)
        VBox2.addWidget(l2Sublabel2)

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

        # Right box
        VBox3 = QtWidgets.QVBoxLayout()
        VBox3.setAlignment(QtCore.Qt.AlignBottom)
        

        # L2 Spectral Outlier Filter
        SpecFilterHBox = QtWidgets.QHBoxLayout()
        SpecFilterHBox.addWidget(l2SpecQualityCheckLabel)
        SpecFilterHBox.addWidget(self.l2SpecQualityCheckBox)
        VBox3.addLayout(SpecFilterHBox)
        SpecFilterEsHBox = QtWidgets.QHBoxLayout()
        SpecFilterEsHBox.addWidget(self.l2SpecFilterEsLabel)
        SpecFilterEsHBox.addWidget(self.l2SpecFilterEsLineEdit)
        VBox3.addLayout(SpecFilterEsHBox)
        SpecFilterLiHBox = QtWidgets.QHBoxLayout()
        SpecFilterLiHBox.addWidget(self.l2SpecFilterLiLabel)
        SpecFilterLiHBox.addWidget(self.l2SpecFilterLiLineEdit)
        VBox3.addLayout(SpecFilterLiHBox)
        SpecFilterLtHBox = QtWidgets.QHBoxLayout()
        SpecFilterLtHBox.addWidget(self.l2SpecFilterLtLabel)
        SpecFilterLtHBox.addWidget(self.l2SpecFilterLtLineEdit)
        VBox3.addLayout(SpecFilterLtHBox)

        # VBox3.addSpacing(5)

        # L2 Meteorology Flags
        QualityFlagHBox = QtWidgets.QHBoxLayout()
        QualityFlagHBox.addWidget(l2QualityFlagLabel)
        # QualityFlagHBox.addWidget(l2QualityFlagLabel2)
        QualityFlagHBox.addWidget(self.l2QualityFlagCheckBox)
        VBox3.addLayout(QualityFlagHBox) 
        CloudFlagHBox = QtWidgets.QHBoxLayout()        
        CloudFlagHBox.addWidget(self.l2CloudFlagLabel)
        CloudFlagHBox.addWidget(self.l2CloudFlagLineEdit)
        VBox3.addLayout(CloudFlagHBox) 
        EsFlagHBox = QtWidgets.QHBoxLayout()        
        EsFlagHBox.addWidget(self.l2EsFlagLabel)
        EsFlagHBox.addWidget(self.l2EsFlagLineEdit)
        VBox3.addLayout(EsFlagHBox) 
        DawnFlagHBox =QtWidgets.QHBoxLayout()
        DawnFlagHBox.addWidget(self.l2DawnDuskFlagLabel)
        DawnFlagHBox.addWidget(self.l2DawnDuskFlagLineEdit)
        VBox3.addLayout(DawnFlagHBox) 
        RainFlagHBox = QtWidgets.QHBoxLayout()
        RainFlagHBox.addWidget(self.l2RainfallHumidityFlagLabel)
        RainFlagHBox.addWidget(self.l2RainfallHumidityFlagLineEdit)
        VBox3.addLayout(RainFlagHBox) 

        # VBox3.addSpacing(5)

        # L2 Time Average Rrs
        TimeAveHBox = QtWidgets.QHBoxLayout()
        TimeAveHBox.addWidget(l2TimeIntervalLabel)
        TimeAveHBox.addWidget(self.l2TimeIntervalLineEdit)
        VBox3.addLayout(TimeAveHBox)  

        # L2 Percent Light; Hooker & Morel 2003
        PercentLtHBox = QtWidgets.QHBoxLayout()
        PercentLtHBox.addWidget(self.l2EnablePercentLtLabel)
        PercentLtHBox.addWidget(self.l2EnablePercentLtCheckBox)
        VBox3.addLayout(PercentLtHBox)  
        PercentLtHBox2 = QtWidgets.QHBoxLayout()
        PercentLtHBox2.addWidget(self.l2PercentLtLabel)
        PercentLtHBox2.addWidget(self.l2PercentLtLineEdit)
        VBox3.addLayout(PercentLtHBox2)              

        # L2 Rho Skyglint/Sunglint Correction
        VBox3.addWidget(l2RhoSkyLabel)
        # Default Rho
        RhoHBox = QtWidgets.QHBoxLayout()
        RhoHBox.addWidget(l2DefaultRhoSkyLabel)
        RhoHBox.addWidget(self.l2RhoSkyLineEdit)
        VBox3.addLayout(RhoHBox)
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
        # WindSpeedHBox = QtWidgets.QHBoxLayout()
        RhoHBox2.addWidget(self.RhoRadioButtonRuddick)
        RhoHBox2.addWidget(self.RhoRadioButtonZhang)
        VBox3.addLayout(RhoHBox2)         
        RhoHBox3 = QtWidgets.QHBoxLayout()
        RhoHBox3.addWidget(self.RhoRadioButtonDefault)
        VBox3.addLayout(RhoHBox3)

        # VBox3.addSpacing(5)

        # L2 NIR AtmoCorr
        NIRCorrectionHBox = QtWidgets.QHBoxLayout()
        NIRCorrectionHBox.addWidget(l2NIRCorrectionLabel)
        NIRCorrectionHBox.addWidget(self.l2NIRCorrectionCheckBox)
        VBox3.addLayout(NIRCorrectionHBox)         

        # VBox3.addSpacing(5)

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

        # VBox3.addSpacing(5)

        # Horizontal Box; Save SeaBASS
        l2SeaBASSHBox = QtWidgets.QHBoxLayout()
        l2SeaBASSHBox.addWidget(l2SaveSeaBASSLabel)
        l2SeaBASSHBox.addWidget(self.l2SaveSeaBASSCheckBox)    
        VBox3.addLayout(l2SeaBASSHBox)    

        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.saveAsButton)
        saveHBox.addWidget(self.cancelButton)
        VBox3.addLayout(saveHBox)

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
        # os.remove(os.path.join(configPath,self.calibrationFileComboBox.currentText()))
        os.remove(configPath)


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
            ConfigFile.settings["bL1ACleanSZA"] = 0      

    def l1cCleanPitchRollCheckBoxUpdate(self):
        print("ConfigWindow - l1cCleanPitchRollCheckBoxUpdate")
        
        disabled = (not self.l1cCleanPitchRollCheckBox.isChecked())
        self.l1cPitchRollPitchLabel.setDisabled(disabled)
        self.l1cPitchRollPitchLineEdit.setDisabled(disabled)
        self.l1cPitchRollRollLabel.setDisabled(disabled)
        self.l1cPitchRollRollLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL1cCleanPitchRoll"] = 0
        #     ConfigFile.settings["fL1cPitchRollPitch"] = "NA"
        #     ConfigFile.settings["fL1cPitchRollRoll"] = "NA"

    def l1cCleanRotatorAngleCheckBoxUpdate(self):
        print("ConfigWindow - l1cCleanRotatorAngleCheckBoxUpdate")
        
        disabled = (not self.l1cCleanRotatorAngleCheckBox.isChecked())
        self.l1cRotatorAngleMinLabel.setDisabled(disabled)
        self.l1cRotatorAngleMinLineEdit.setDisabled(disabled)
        self.l1cRotatorAngleMaxLabel.setDisabled(disabled)
        self.l1cRotatorAngleMaxLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL1cCleanRotatorAngle"] = 0
        #     ConfigFile.settings["fL1cRotatorAngleMin"] = "NA"
        #     ConfigFile.settings["fL1cRotatorAngleMax"] = "NA"

    def l1cCleanSunAngleCheckBoxUpdate(self):
        print("ConfigWindow - l1cCleanSunAngleCheckBoxUpdate")
        
        disabled = (not self.l1cCleanSunAngleCheckBox.isChecked())
        self.l1cSunAngleMinLabel.setDisabled(disabled)
        self.l1cSunAngleMinLineEdit.setDisabled(disabled)
        self.l1cSunAngleMaxLabel.setDisabled(disabled)
        self.l1cSunAngleMaxLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL1cCleanSunAngle"] = 0
        #     ConfigFile.settings["fL1cSunAngleMin"] = "NA"
        #     ConfigFile.settings["fL1cSunAngleMax"] = "NA"

    def l1dAnomalyButtonPressed(self):
        print("CalibrationEditWindow - Launching anomaly analysis module")        
        AnomalyDetection(self,self.inputDirectory)

    def l1dDeglitchCheckBoxUpdate(self):
        print("ConfigWindow - l1dDeglitchCheckBoxUpdate")
        
        disabled = (not self.l1dDeglitchCheckBox.isChecked())
        self.l1dDeglitch0Label.setDisabled(disabled)
        self.l1dDeglitch0LineEdit.setDisabled(disabled)
        self.l1dDeglitch1Label.setDisabled(disabled)
        self.l1dDeglitch1LineEdit.setDisabled(disabled)
        self.l1dDeglitch2Label.setDisabled(disabled)
        self.l1dDeglitch2LineEdit.setDisabled(disabled)   
        self.l1dDeglitch3Label.setDisabled(disabled)
        self.l1dDeglitch3LineEdit.setDisabled(disabled)   
        if disabled:
            ConfigFile.settings["bL1dDeglitch"]   = 0
        #     ConfigFile.settings["fL1dDeglitch0"]   = "NA"
        #     ConfigFile.settings["fL1dDeglitch1"]   = "NA"
        #     ConfigFile.settings["fL1dDeglitch2"]   = "NA"
        #     ConfigFile.settings["fL1dDeglitch3"]   = "NA"

    def l1ePlotTimeInterpCheckBoxUpdate(self):
        print("ConfigWindow - l1ePlotTimeInterpCheckBoxUpdate")

    def l1eSaveSeaBASSCheckBoxUpdate(self):
        print("ConfigWindow - l1eSaveSeaBASSCheckBoxUpdate")
        disabled = (not self.l1eSaveSeaBASSCheckBox.isChecked())
        self.l1eSeaBASSHeaderNewButton.setDisabled(disabled)
        self.l1eSeaBASSHeaderOpenButton.setDisabled(disabled)
        self.l1eSeaBASSHeaderEditButton.setDisabled(disabled)
        self.l1eSeaBASSHeaderDeleteButton.setDisabled(disabled)

    def l1eSeaBASSHeaderNewButtonPressed(self):
        print("New SeaBASSHeader Dialogue")
        text, ok = QtWidgets.QInputDialog.getText(self, 'New SeaBASSHeader File', 'Enter File Name')
        seaBASSHeaderFileName = f'{text}.hdr'
        if ok:
            print("Create SeaBASSHeader File: ", seaBASSHeaderFileName)
            
            inputDir = self.inputDirectory
            seaBASSHeaderPath = os.path.join("Config", seaBASSHeaderFileName)
            # Now open the new file
            
            if os.path.isfile(seaBASSHeaderPath):
                seaBASSHeaderDeleteMessage = "Overwrite " + seaBASSHeaderFileName + "?"

                reply = QtWidgets.QMessageBox.question(self, 'Message', seaBASSHeaderDeleteMessage, \
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

                if reply == QtWidgets.QMessageBox.Yes:
                    SeaBASSHeader.createDefaultSeaBASSHeader(seaBASSHeaderFileName)
                    SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)
                    seaBASSHeaderDialog = SeaBASSHeaderWindow(seaBASSHeaderFileName, inputDir, self)
                    #seaBASSHeaderDialog = CalibrationEditWindow(seaBASSHeaderFileName, self)
                    seaBASSHeaderDialog.show()                
            else:
                SeaBASSHeader.createDefaultSeaBASSHeader(seaBASSHeaderFileName)
                SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)
                seaBASSHeaderDialog = SeaBASSHeaderWindow(seaBASSHeaderFileName, inputDir, self)
                seaBASSHeaderDialog.show()  
            
            self.l1eSeaBASSHeaderLineEdit.setText(seaBASSHeaderFileName)  

    def l1eSeaBASSHeaderOpenButtonPressed(self):
        print("SeaBASSHeader Open Dialogue")
        text, ok = QtWidgets.QFileDialog.getOpenFileNames(self, "Select SeaBASS Header File","Config","hdr(*.hdr)")
        if ok:
            (_, fname) = os.path.split(text[0])
            print(fname)
            if len(fname[0]) == 1:
                self.l1eSeaBASSHeaderLineEdit.setText(fname)            

    def l1eSeaBASSHeaderEditButtonPressed(self):
        print("Edit seaBASSHeader Dialogue")
        
        # seaBASSHeaderFileName = self.l1eSeaBASSHeaderComboBox.currentText()
        seaBASSHeaderFileName = self.l1eSeaBASSHeaderLineEdit.text()
        inputDir = self.inputDirectory
        seaBASSHeaderPath = os.path.join("Config", seaBASSHeaderFileName)
        if os.path.isfile(seaBASSHeaderPath):
            SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)
            seaBASSHeaderDialog = SeaBASSHeaderWindow(seaBASSHeaderFileName, inputDir, self)
            #seaBASSHeaderDialog = CalibrationEditWindow(seaBASSHeaderFileName, self)
            seaBASSHeaderDialog.show()
        else:
            #print("Not a SeaBASSHeader File: " + seaBASSHeaderFileName)
            message = "Not a seaBASSHeader File: " + seaBASSHeaderFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)

    def l1eSeaBASSHeaderDeleteButtonPressed(self):
        print("Delete seaBASSHeader Dialogue")
        # print("index: ", self.seaBASSHeaderComboBox.currentIndex())
        # print("text: ", self.seaBASSHeaderComboBox.currentText())
        # seaBASSHeaderFileName = self.l1eSeaBASSHeaderComboBox.currentText()
        seaBASSHeaderFileName = self.l1eSeaBASSHeaderLineEdit.text()
        seaBASSHeaderPath = os.path.join("Config", seaBASSHeaderFileName)
        if os.path.isfile(seaBASSHeaderPath):
            seaBASSHeaderDeleteMessage = "Delete " + seaBASSHeaderFileName + "?"

            reply = QtWidgets.QMessageBox.question(self, 'Message', seaBASSHeaderDeleteMessage, \
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                SeaBASSHeader.deleteSeaBASSHeader(seaBASSHeaderFileName)
                self.l1eSeaBASSHeaderLineEdit.setText('')              
        else:
            #print("Not a seaBASSHeader File: " + seaBASSHeaderFileName)
            message = "Not a seaBASSHeader File: " + seaBASSHeaderFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)

    def l2pGetAncCheckBoxUpdate(self):
        print("ConfigWindow - l2pGetAncCheckBoxUpdate")        
            
        if self.l2pGetAncCheckBox.isChecked():
            if not ConfigFile.settings["bL2pObpgCreds"]:
                usr = QtWidgets.QInputDialog.getText(None, 
                                                "Earthdata Username",
                                                "username:", 
                                                QtWidgets.QLineEdit.Normal, 
                                                "") 
                pwd = QtWidgets.QInputDialog.getText(None, 
                                                "Earthdata Password",
                                                "password:", 
                                                QtWidgets.QLineEdit.Normal, 
                                                "") 
                GetAnc.userCreds(usr[0],pwd[0])
                
            ConfigFile.settings["bL2pGetAnc"] = 1
            self.RhoRadioButtonRuddick.setDisabled(0)
            self.RhoRadioButtonZhang.setDisabled(0)
        else:            
            ConfigFile.settings["bL2pGetAnc"] = 0
            ConfigFile.settings["bL2pObpgCreds"] = False
            self.RhoRadioButtonZhang.setChecked(0)
            self.RhoRadioButtonZhang.setDisabled(1)
            self.RhoRadioButtonRuddick.setChecked(1)
            # self.RhoRadioButtonRuddick.setDisabled(1)
            
            print("ConfigWindow - l2RhoCorrection set to Ruddick")
            ConfigFile.settings["bL2RuddickRho"] = 1
            ConfigFile.settings["bL2ZhangRho"] = 0
            ConfigFile.settings["bL2DefaultRho"] = 0

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
        #     ConfigFile.settings["fL2CloudFlag"] = "NA"
        #     ConfigFile.settings["fL2SignificantEsFlag"] = "NA"
        #     ConfigFile.settings["fL2DawnDuskFlag"] = "NA"
        #     ConfigFile.settings["fL2RainfallHumidityFlag"] = "NA"

    def l2EnablePercentLtCheckBoxUpdate(self):
        print("ConfigWindow - l2EnablePercentLtCheckBoxUpdate")
        
        disabled = (not self.l2EnablePercentLtCheckBox.isChecked())
        self.l2PercentLtLabel.setDisabled(disabled)
        self.l2PercentLtLineEdit.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL2EnablePercentLt"] = 0
        #     ConfigFile.settings["fL2PercentLt"] = "NA"

    def l2RhoCorrectionRadioButtonClicked(self):
        # radioButton = self.sender()
        if self.RhoRadioButtonRuddick.isChecked():
            print("ConfigWindow - l2RhoCorrection set to Ruddick")
            ConfigFile.settings["bL2RuddickRho"] = 1
            ConfigFile.settings["bL2ZhangRho"] = 0
            ConfigFile.settings["bL2DefaultRho"] = 0
        elif self.RhoRadioButtonZhang.isChecked():
            print("ConfigWindow - l2RhoCorrection set to Zhang")
            ConfigFile.settings["bL2RuddickRho"] = 0
            ConfigFile.settings["bL2ZhangRho"] = 1
            ConfigFile.settings["bL2DefaultRho"] = 0
        elif self.RhoRadioButtonDefault.isChecked():
            print("ConfigWindow - l2RhoCorrection set to Default")
            ConfigFile.settings["bL2RuddickRho"] = 0
            ConfigFile.settings["bL2ZhangRho"] = 0
            ConfigFile.settings["bL2DefaultRho"] = 1
    
    def l2NIRCorrectionCheckBoxUpdate(self):
        print("ConfigWindow - l2NIRCorrectionCheckBoxUpdate")
        
        disabled = (not self.l2NIRCorrectionCheckBox.isChecked())     
        if disabled:
            ConfigFile.settings["bL2PerformNIRCorrection"] = 0

    def l2SaveSeaBASSCheckBoxUpdate(self):
        print("ConfigWindow - l2SaveSeaBASSCheckBoxUpdate")

    def saveButtonPressed(self):
        print("ConfigWindow - Save Pressed")
        # print(self.l1dDeglitch0LineEdit.text())
        # print(int(self.l1dDeglitch0LineEdit.text())%2)
        if int(self.l1dDeglitch0LineEdit.text())%2 == 0 or int(self.l1dDeglitch1LineEdit.text())%2 ==0:
            alert = QtWidgets.QMessageBox()
            alert.setText('Deglitching windows must be odd integers.')
            alert.exec_()
            return

        ConfigFile.settings["bL1aCleanSZA"] = int(self.l1aCleanSZACheckBox.isChecked())
        ConfigFile.settings["fL1aCleanSZAMax"] = float(self.l1aCleanSZAMaxLineEdit.text())
        
        ConfigFile.settings["fL1cRotatorHomeAngle"] = float(self.l1cRotatorHomeAngleLineEdit.text())
        ConfigFile.settings["fL1cRotatorDelay"] = float(self.l1cRotatorDelayLineEdit.text())     
        ConfigFile.settings["bL1cCleanPitchRoll"] = int(self.l1cCleanPitchRollCheckBox.isChecked())        
        ConfigFile.settings["fL1cPitchRollPitch"] = float(self.l1cPitchRollPitchLineEdit.text())
        ConfigFile.settings["fL1cPitchRollRoll"] = float(self.l1cPitchRollRollLineEdit.text())         
        ConfigFile.settings["bL1cCleanRotatorAngle"] = int(self.l1cCleanRotatorAngleCheckBox.isChecked())        
        ConfigFile.settings["fL1cRotatorAngleMin"] = float(self.l1cRotatorAngleMinLineEdit.text())
        ConfigFile.settings["fL1cRotatorAngleMax"] = float(self.l1cRotatorAngleMaxLineEdit.text())                
        ConfigFile.settings["bL1cCleanSunAngle"] = int(self.l1cCleanSunAngleCheckBox.isChecked())        
        ConfigFile.settings["fL1cSunAngleMin"] = float(self.l1cSunAngleMinLineEdit.text())
        ConfigFile.settings["fL1cSunAngleMax"] = float(self.l1cSunAngleMaxLineEdit.text())

        ConfigFile.settings["bL1dDeglitch"] = int(self.l1dDeglitchCheckBox.isChecked()) 
        ConfigFile.settings["fL1dDeglitch0"] = int(self.l1dDeglitch0LineEdit.text())
        ConfigFile.settings["fL1dDeglitch1"] = int(self.l1dDeglitch1LineEdit.text())
        ConfigFile.settings["fL1dDeglitch2"] = float(self.l1dDeglitch2LineEdit.text())
        ConfigFile.settings["fL1dDeglitch3"] = float(self.l1dDeglitch3LineEdit.text())
        ConfigFile.settings["bL1dAnomalyStep"] = int(self.l1dAnomalyStepLineEdit.text())

        ConfigFile.settings["fL1eInterpInterval"] = float(self.l1eInterpIntervalLineEdit.text())
        ConfigFile.settings["bL1ePlotTimeInterp"] = int(self.l1ePlotTimeInterpCheckBox.isChecked())
        ConfigFile.settings["bL1eSaveSeaBASS"] = int(self.l1eSaveSeaBASSCheckBox.isChecked())
        # ConfigFile.settings["seaBASSHeaderFileName"] = self.l1eSeaBASSHeaderComboBox.currentText()
        ConfigFile.settings["seaBASSHeaderFileName"] = self.l1eSeaBASSHeaderLineEdit.text()

        ConfigFile.settings["bL2pGetAnc"] = int(self.l2pGetAncCheckBox.isChecked())
        
        ConfigFile.settings["fL2MaxWind"] = float(self.l2MaxWindLineEdit.text())
        ConfigFile.settings["fL2SZAMin"] = float(self.l2SZAMinLineEdit.text())
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

        ConfigFile.settings["fL2TimeInterval"] = int(self.l2TimeIntervalLineEdit.text())                        
        ConfigFile.settings["bL2EnablePercentLt"] = int(self.l2EnablePercentLtCheckBox.isChecked())
        ConfigFile.settings["fL2PercentLt"] = float(self.l2PercentLtLineEdit.text())

        ConfigFile.settings["bL2ZhangRho"] = int(self.RhoRadioButtonZhang.isChecked())
        ConfigFile.settings["fL2DefaultWindSpeed"] = float(self.l2DefaultWindSpeedLineEdit.text())
        ConfigFile.settings["fL2DefaultAOD"] = float(self.l2DefaultAODLineEdit.text())
        ConfigFile.settings["fL2DefaultSalt"] = float(self.l2DefaultSaltLineEdit.text())
        ConfigFile.settings["fL2DefaultSST"] = float(self.l2DefaultSSTLineEdit.text())
        ConfigFile.settings["fL2RhoSky"] = float(self.l2RhoSkyLineEdit.text())
        ConfigFile.settings["bL2RuddickRho"] = int(self.RhoRadioButtonRuddick.isChecked())

        ConfigFile.settings["bL2PerformNIRCorrection"] = int(self.l2NIRCorrectionCheckBox.isChecked())
        
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

        ConfigFile.saveConfig(self.name)

        # QtWidgets.QMessageBox.about(self, "Edit Config File", "Config File Saved")  

        # Confirm that SeaBASS Headers need to be/are updated
        if ConfigFile.settings["bL1eSaveSeaBASS"] or ConfigFile.settings["bL1eSaveSeaBASS"]: 
            reply = QtWidgets.QMessageBox.question(self, "Message", "Did you remember to update SeaBASS Headers?", \
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No) 

            if reply == QtWidgets.QMessageBox.Yes:
                self.close()
            else:
                note = QtWidgets.QMessageBox()
                note.setText('Update SeaBASS Headers in Level 1E Processing')
                note.exec_()
        else:
            self.close()

    def saveAsButtonPressed(self):
        print("ConfigWindow - Save As Pressed")
        self.newName, ok = QtWidgets.QInputDialog.getText(self, 'Save As Config File', 'Enter File Name')
        if ok:
            print("Create Config File: ", self.newName)

            if not self.newName.endswith(".cfg"):
                self.newName = self.newName + ".cfg"
                # oldConfigName = ConfigFile.filename
                ConfigFile.filename = self.newName                

            # self.calibrationFileComboBox.currentIndexChanged.connect(self.calibrationFileChanged)
            
            if int(self.l1dDeglitch0LineEdit.text())%2 == 0 or int(self.l1dDeglitch1LineEdit.text())%2 ==0:
                alert = QtWidgets.QMessageBox()
                alert.setText('Deglitching windows must be odd integers.')
                alert.exec_()
                return

            ConfigFile.settings["bL1aCleanSZA"] = int(self.l1aCleanSZACheckBox.isChecked())
            ConfigFile.settings["fL1aCleanSZAMax"] = float(self.l1aCleanSZAMaxLineEdit.text())
            
            ConfigFile.settings["fL1cRotatorHomeAngle"] = float(self.l1cRotatorHomeAngleLineEdit.text())
            ConfigFile.settings["fL1cRotatorDelay"] = float(self.l1cRotatorDelayLineEdit.text())     
            ConfigFile.settings["bL1cCleanPitchRoll"] = int(self.l1cCleanPitchRollCheckBox.isChecked())        
            ConfigFile.settings["fL1cPitchRollPitch"] = float(self.l1cPitchRollPitchLineEdit.text())
            ConfigFile.settings["fL1cPitchRollRoll"] = float(self.l1cPitchRollRollLineEdit.text())         
            ConfigFile.settings["bL1cCleanRotatorAngle"] = int(self.l1cCleanRotatorAngleCheckBox.isChecked())        
            ConfigFile.settings["fL1cRotatorAngleMin"] = float(self.l1cRotatorAngleMinLineEdit.text())
            ConfigFile.settings["fL1cRotatorAngleMax"] = float(self.l1cRotatorAngleMaxLineEdit.text())                
            ConfigFile.settings["bL1cCleanSunAngle"] = int(self.l1cCleanSunAngleCheckBox.isChecked())        
            ConfigFile.settings["fL1cSunAngleMin"] = float(self.l1cSunAngleMinLineEdit.text())
            ConfigFile.settings["fL1cSunAngleMax"] = float(self.l1cSunAngleMaxLineEdit.text())

            ConfigFile.settings["bL1dDeglitch"] = int(self.l1dDeglitchCheckBox.isChecked()) 
            ConfigFile.settings["fL1dDeglitch0"] = int(self.l1dDeglitch0LineEdit.text())
            ConfigFile.settings["fL1dDeglitch1"] = int(self.l1dDeglitch1LineEdit.text())
            ConfigFile.settings["fL1dDeglitch2"] = float(self.l1dDeglitch2LineEdit.text())
            ConfigFile.settings["fL1dDeglitch3"] = float(self.l1dDeglitch3LineEdit.text())

            ConfigFile.settings["fL1eInterpInterval"] = float(self.l1eInterpIntervalLineEdit.text())
            ConfigFile.settings["bL1ePlotTimeInterp"] = int(self.l1ePlotTimeInterpCheckBox.isChecked())
            ConfigFile.settings["bL1eSaveSeaBASS"] = int(self.l1eSaveSeaBASSCheckBox.isChecked())
            # ConfigFile.settings["seaBASSHeaderFileName"] = self.l1eSeaBASSHeaderComboBox.currentText()
            ConfigFile.settings["seaBASSHeaderFileName"] = self.l1eSeaBASSHeaderLineEdit.text()

            ConfigFile.settings["bL2pGetAnc"] = int(self.l2pGetAncCheckBox.isChecked())
            
            ConfigFile.settings["fL2MaxWind"] = float(self.l2MaxWindLineEdit.text())
            ConfigFile.settings["fL2SZAMin"] = float(self.l2SZAMinLineEdit.text())
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
            ConfigFile.settings["fL2TimeInterval"] = int(self.l2TimeIntervalLineEdit.text())                            
            ConfigFile.settings["bL2EnablePercentLt"] = int(self.l2EnablePercentLtCheckBox.isChecked())
            ConfigFile.settings["fL2PercentLt"] = float(self.l2PercentLtLineEdit.text())
            ConfigFile.settings["fL2RhoSky"] = float(self.l2RhoSkyLineEdit.text())            
            ConfigFile.settings["fL2DefaultWindSpeed"] = float(self.l2DefaultWindSpeedLineEdit.text())
            ConfigFile.settings["fL2DefaultAOD"] = float(self.l2DefaultAODLineEdit.text())
            ConfigFile.settings["fL2DefaultSalt"] = float(self.l2DefaultSaltLineEdit.text())
            ConfigFile.settings["fL2DefaultSST"] = float(self.l2DefaultSSTLineEdit.text())  
            ConfigFile.settings["bL2RuddickRho"] = int(self.RhoRadioButtonRuddick.isChecked())
            ConfigFile.settings["bL2ZhangRho"] = int(self.RhoRadioButtonZhang.isChecked())
            ConfigFile.settings["bL2DefaultRho"] = int(self.RhoRadioButtonDefault.isChecked())
            ConfigFile.settings["bL2PerformNIRCorrection"] = int(self.l2NIRCorrectionCheckBox.isChecked())          
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

            # QtWidgets.QMessageBox.about(self, "Save As Config File", "Config File Saved")
            ConfigFile.saveConfig(ConfigFile.filename)

            # Copy Calibration files into new Config folder
            # fnames = QtWidgets.QFileDialog.getOpenFileNames(self, "Add Calibration Files")
            fnames = ConfigFile.settings['CalibrationFiles']

            # oldCalibrationDir = os.path.splitext(oldConfigName)[0] + "_Calibration"
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
            if ConfigFile.settings["bL1eSaveSeaBASS"] or ConfigFile.settings["bL1eSaveSeaBASS"]: 
                reply = QtWidgets.QMessageBox.question(self, "Message", "Did you remember to update SeaBASS Headers?", \
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No) 

                if reply == QtWidgets.QMessageBox.Yes:
                    self.close()
                else:
                    note = QtWidgets.QMessageBox()
                    note.setText('Update SeaBASS Headers in Level 1E Processing')
                    note.exec_()
            else:
                self.close()
        

    def cancelButtonPressed(self):
        print("ConfigWindow - Cancel Pressed")
        self.close()

