
import os
import shutil
from PyQt5 import QtCore, QtGui, QtWidgets


from ConfigFile import ConfigFile
from AnomalyDetection import AnomalyDetection
from SeaBASSHeader import SeaBASSHeader
from SeaBASSHeaderWindow import SeaBASSHeaderWindow



class ConfigWindow(QtWidgets.QDialog):
    def __init__(self, name, inputDir, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.name = name
        self.inputDirectory = inputDir
        # print(self.inputDirectory)
        self.initUI()
        # self.outputDirectory = outputDirectory

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
        # rx = QtCore.QRegExp.isValid("")
        # oddValidator = QtGui.QRegExpValidator(rx,self)

        # L1A
        l1aLabel = QtWidgets.QLabel("Level 1A Processing", self)
        l1aLabel_font = l1aLabel.font()
        l1aLabel_font.setPointSize(12)
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

        # l1aSaveSeaBASSLabel = QtWidgets.QLabel("     Save SeaBASS text file", self)        
        # self.l1aSaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)            
        # if int(ConfigFile.settings["bL1aSaveSeaBASS"]) == 1:
        #     self.l1aSaveSeaBASSCheckBox.setChecked(True)     

        self.l1aCleanSZACheckBoxUpdate()   
        self.l1aCleanSZACheckBox.clicked.connect(self.l1aCleanSZACheckBoxUpdate) 
        # self.l1aSaveSeaBASSCheckBox.clicked.connect(self.l1aSaveSeaBASSCheckBoxUpdate)

        # L1b
        l1bLabel = QtWidgets.QLabel("Level 1B Processing", self)        
        l1bLabel_font = l1bLabel.font()
        l1bLabel_font.setPointSize(12)
        l1bLabel_font.setBold(True)
        l1bLabel.setFont(l1bLabel_font)
        # l1bLabel2 = QtWidgets.QLabel("Level 1B Processing (cntd)", self)
        # l1bLabel2_font = l1bLabel2.font()
        # l1bLabel2_font.setPointSize(12)
        # l1bLabel2_font.setBold(True)
        
        # l1bLabel2.setFont(l1bLabel_font)
        l1bSublabel = QtWidgets.QLabel(" Filter on pitch, roll, rotator, yaw,", self)        
        l1bSublabel2 = QtWidgets.QLabel("   and relative solar azimuth. Apply", self)
        l1bSublabel3 = QtWidgets.QLabel("   factory calibrations.", self)        

        # Rotator 
        self.l1bRotatorHomeAngleLabel = QtWidgets.QLabel(" Rotator Home Angle", self)
        self.l1bRotatorHomeAngleLineEdit = QtWidgets.QLineEdit(self)
        self.l1bRotatorHomeAngleLineEdit.setText(str(ConfigFile.settings["fL1bRotatorHomeAngle"]))
        self.l1bRotatorHomeAngleLineEdit.setValidator(doubleValidator)   

        self.l1bRotatorDelayLabel = QtWidgets.QLabel(" Rotator Delay (Seconds)", self)
        self.l1bRotatorDelayLineEdit = QtWidgets.QLineEdit(self)
        self.l1bRotatorDelayLineEdit.setText(str(ConfigFile.settings["fL1bRotatorDelay"]))
        self.l1bRotatorDelayLineEdit.setValidator(doubleValidator)     

        # Pitch and Roll
        l1bCleanPitchRollLabel = QtWidgets.QLabel(" Pitch & Roll Filter", self)                        
        self.l1bCleanPitchRollCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1bCleanPitchRoll"]) == 1:
            self.l1bCleanPitchRollCheckBox.setChecked(True)
        self.l1bPitchRollPitchLabel = QtWidgets.QLabel("       Max Pitch Angle", self)
        self.l1bPitchRollPitchLineEdit = QtWidgets.QLineEdit(self)
        self.l1bPitchRollPitchLineEdit.setText(str(ConfigFile.settings["fL1bPitchRollPitch"]))
        self.l1bPitchRollPitchLineEdit.setValidator(doubleValidator)
        self.l1bPitchRollRollLabel = QtWidgets.QLabel("       Max Roll Angle", self)
        self.l1bPitchRollRollLineEdit = QtWidgets.QLineEdit(self)
        self.l1bPitchRollRollLineEdit.setText(str(ConfigFile.settings["fL1bPitchRollRoll"]))
        self.l1bPitchRollRollLineEdit.setValidator(doubleValidator)        
        self.l1bCleanPitchRollCheckBoxUpdate()        

         # Rotator                
        l1bCleanRotatorAngleLabel = QtWidgets.QLabel(" Absolute Rotator Angle Filter", self)                        
        self.l1bCleanRotatorAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1bCleanRotatorAngle"]) == 1:
            self.l1bCleanRotatorAngleCheckBox.setChecked(True)
        self.l1bRotatorAngleMinLabel = QtWidgets.QLabel("       Rotator Angle Min", self)
        self.l1bRotatorAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l1bRotatorAngleMinLineEdit.setText(str(ConfigFile.settings["fL1bRotatorAngleMin"]))
        self.l1bRotatorAngleMinLineEdit.setValidator(doubleValidator)
        self.l1bRotatorAngleMaxLabel = QtWidgets.QLabel("       Rotator Angle Max", self)
        self.l1bRotatorAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l1bRotatorAngleMaxLineEdit.setText(str(ConfigFile.settings["fL1bRotatorAngleMax"]))
        self.l1bRotatorAngleMaxLineEdit.setValidator(doubleValidator)        
        self.l1bCleanRotatorAngleCheckBoxUpdate()        

        # Relative SZA
        l1bCleanSunAngleLabel = QtWidgets.QLabel(" Relative Solar Azimuth Filter", self)
        self.l1bCleanSunAngleCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL1bCleanSunAngle"]) == 1:
            self.l1bCleanSunAngleCheckBox.setChecked(True)        
        self.l1bSunAngleMinLabel = QtWidgets.QLabel("       Rel Angle Min", self)
        self.l1bSunAngleMinLineEdit = QtWidgets.QLineEdit(self)
        self.l1bSunAngleMinLineEdit.setText(str(ConfigFile.settings["fL1bSunAngleMin"]))
        self.l1bSunAngleMinLineEdit.setValidator(doubleValidator)
        self.l1bSunAngleMaxLabel = QtWidgets.QLabel("       Rel Angle Max", self)
        self.l1bSunAngleMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l1bSunAngleMaxLineEdit.setText(str(ConfigFile.settings["fL1bSunAngleMax"]))
        self.l1bSunAngleMaxLineEdit.setValidator(doubleValidator)
        self.l1bCleanSunAngleCheckBoxUpdate() 
        
        self.l1bCleanPitchRollCheckBox.clicked.connect(self.l1bCleanPitchRollCheckBoxUpdate)
        self.l1bCleanRotatorAngleCheckBox.clicked.connect(self.l1bCleanRotatorAngleCheckBoxUpdate)
        self.l1bCleanSunAngleCheckBox.clicked.connect(self.l1bCleanSunAngleCheckBoxUpdate)


        # L2 (Main)
        l2Label = QtWidgets.QLabel("Level 2 Processing", self)
        l2Label_font = l2Label.font()
        l2Label_font.setPointSize(12)
        l2Label_font.setBold(True)
        l2Label.setFont(l2Label_font)
        l2Sublabel = QtWidgets.QLabel(" Shutter dark corrections and data deglitching", self)  
        
        # Deglitcher
        self.l2DeglitchLabel = QtWidgets.QLabel("  Deglitch data", self)                
        self.l2DeglitchCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL2Deglitch"]) == 1:
            self.l2DeglitchCheckBox.setChecked(True)

        self.l2Deglitch0Label = QtWidgets.QLabel("     Window for Darks (odd)", self)
        self.l2Deglitch0LineEdit = QtWidgets.QLineEdit(self)
        self.l2Deglitch0LineEdit.setText(str(ConfigFile.settings["fL2Deglitch0"]))
        self.l2Deglitch0LineEdit.setValidator(intValidator)
        # self.l2Deglitch0LineEdit.setValidator(oddValidator)

        self.l2Deglitch1Label = QtWidgets.QLabel("     Window for Lights (odd)", self)
        self.l2Deglitch1LineEdit = QtWidgets.QLineEdit(self)
        self.l2Deglitch1LineEdit.setText(str(ConfigFile.settings["fL2Deglitch1"]))
        self.l2Deglitch1LineEdit.setValidator(intValidator)
        # self.l2Deglitch1LineEdit.setValidator(oddValidator)

        self.l2Deglitch2Label = QtWidgets.QLabel("     Sigma Factor Darks", self)
        self.l2Deglitch2LineEdit = QtWidgets.QLineEdit(self)
        self.l2Deglitch2LineEdit.setText(str(ConfigFile.settings["fL2Deglitch2"]))
        self.l2Deglitch2LineEdit.setValidator(doubleValidator)
        
        self.l2Deglitch3Label = QtWidgets.QLabel("     Sigma Factor Lights", self)
        self.l2Deglitch3LineEdit = QtWidgets.QLineEdit(self)
        self.l2Deglitch3LineEdit.setText(str(ConfigFile.settings["fL2Deglitch3"]))
        self.l2Deglitch3LineEdit.setValidator(doubleValidator)

        self.l2DeglitchCheckBoxUpdate()      

        self.l2DeglitchCheckBox.clicked.connect(self.l2DeglitchCheckBoxUpdate)   

        # Launch Deglitcher Analysis 
        # l2AnomalyLabel = QtWidgets.QLabel("Level 2 Anomaly Detection", self)
        # l2AnomalyLabel_font = l2AnomalyLabel.font()
        # l2AnomalyLabel_font.setPointSize(12)
        # l2AnomalyLabel_font.setBold(True)
        # l2AnomalyLabel.setFont(l2AnomalyLabel_font)
        l2AnomalySublabel1 = QtWidgets.QLabel("  Launch Anom. Anal. below to test above",self)
        l2AnomalySublabel2 = QtWidgets.QLabel("   params on L1B. Save config when updating",self)
        l2AnomalySublabel3 = QtWidgets.QLabel("   params. Results will be saved to Plot/Anoms.", self)  
        self.anomalyButton = QtWidgets.QPushButton("Anomaly Analysis")
        self.anomalyButton.clicked.connect(self.anomalyButtonPressed)
                        
        # l3
        l3Label = QtWidgets.QLabel("Level 3 Processing", self)
        l3Label_font = l3Label.font()
        l3Label_font.setPointSize(12)
        l3Label_font.setBold(True)
        l3Label.setFont(l3Label_font)
        l3Sublabel = QtWidgets.QLabel(" Interpolation to common wavelengths.", self)
        l3Sublabel2 = QtWidgets.QLabel(" Interpolate to common time coordinates.", self)
        l3InterpIntervalLabel = QtWidgets.QLabel("     Interpolation Interval (nm)", self)
        self.l3InterpIntervalLineEdit = QtWidgets.QLineEdit(self)
        self.l3InterpIntervalLineEdit.setText(str(ConfigFile.settings["fL3InterpInterval"]))
        self.l3InterpIntervalLineEdit.setValidator(doubleValidator)

        l3PlotTimeInterpLabel = QtWidgets.QLabel("Generate Plots (slow; saved in ./Plots/L3/)", self)        
        self.l3PlotTimeInterpCheckBox = QtWidgets.QCheckBox("", self)                    
        if int(ConfigFile.settings["bL3PlotTimeInterp"]) == 1:
            self.l3PlotTimeInterpCheckBox.setChecked(True)   
        self.l3PlotTimeInterpCheckBox.clicked.connect(self.l3PlotTimeInterpCheckBoxUpdate)   

        l3SaveSeaBASSLabel = QtWidgets.QLabel("Save SeaBASS text file", self)        
        self.l3SaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)                    
        if int(ConfigFile.settings["bL3SaveSeaBASS"]) == 1:
            self.l3SaveSeaBASSCheckBox.setChecked(True)   
        self.l3SaveSeaBASSCheckBox.clicked.connect(self.l3SaveSeaBASSCheckBoxUpdate)         

        # # SeaBASSHeader File
        '''# Can't figure out how to change the index when the window is drawn, so creating
         a lineedit instead. It should be a pull-down, then drop the "Open" box.'''
        # l3SeaBASSfsm = QtWidgets.QFileSystemModel()
        # index = l3SeaBASSfsm.setRootPath("Config")        
        self.l3SeaBASSHeaderLabel = QtWidgets.QLabel('       SeaBASS Header File', self)
        # #self.l3SeaBASSHeaderLabel.move(30, 20)
        # self.l3SeaBASSHeaderComboBox = QtWidgets.QComboBox(self)
        # self.l3SeaBASSHeaderComboBox.setModel(l3SeaBASSfsm)
        # l3SeaBASSfsm.setNameFilters(["*.hdr"]) 
        # l3SeaBASSfsm.setNameFilterDisables(False) 
        # l3SeaBASSfsm.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)
        # self.l3SeaBASSHeaderComboBox.setRootModelIndex(index) # Sets directory to Config        
        # headFileIndex=self.l3SeaBASSHeaderComboBox.findText(ConfigFile.settings["seaBASSHeaderFileName"])
        # print(ConfigFile.settings["seaBASSHeaderFileName"])
        # print(headFileIndex)
        # self.l3SeaBASSHeaderComboBox.setCurrentIndex(headFileIndex)
        #self.l3SeaBASSHeaderComboBox.move(30, 50)        
        self.l3SeaBASSHeaderLineEdit = QtWidgets.QLineEdit(ConfigFile.settings["seaBASSHeaderFileName"])        
        self.l3SeaBASSHeaderNewButton = QtWidgets.QPushButton("New", self)
        self.l3SeaBASSHeaderOpenButton = QtWidgets.QPushButton("Open", self)
        self.l3SeaBASSHeaderEditButton = QtWidgets.QPushButton("Edit", self)
        #self.l3SeaBASSHeaderEditButton.move(130, 80)
        self.l3SeaBASSHeaderDeleteButton = QtWidgets.QPushButton("Delete", self)
        self.l3SeaBASSHeaderNewButton.clicked.connect(self.l3seaBASSHeaderNewButtonPressed)
        self.l3SeaBASSHeaderOpenButton.clicked.connect(self.l3seaBASSHeaderOpenButtonPressed)
        self.l3SeaBASSHeaderEditButton.clicked.connect(self.l3seaBASSHeaderEditButtonPressed)
        self.l3SeaBASSHeaderDeleteButton.clicked.connect(self.l3seaBASSHeaderDeleteButtonPressed)  

        self.l3SaveSeaBASSCheckBoxUpdate()

        # L4     
        l4Label = QtWidgets.QLabel("Level 4 Processing", self)
        l4Label_font = l4Label.font()
        l4Label_font.setPointSize(12)
        l4Label_font.setBold(True)
        l4Label.setFont(l4Label_font)
        l4Sublabel = QtWidgets.QLabel(" Quality control filters, glint correction, temporal", self)   
        l4Sublabel2 = QtWidgets.QLabel(" binning, reflectance calculation.", self)   
        # Min/Max SZA
        l4MaxWindLabel = QtWidgets.QLabel("     Max. Wind Speed (m/s)", self)
        self.l4MaxWindLineEdit = QtWidgets.QLineEdit(self)
        self.l4MaxWindLineEdit.setText(str(ConfigFile.settings["fL4MaxWind"]))
        self.l4MaxWindLineEdit.setValidator(doubleValidator)        

        # Min/Max SZA
        l4SZAMinLabel = QtWidgets.QLabel("     SZA Minimum (deg)", self)
        self.l4SZAMinLineEdit = QtWidgets.QLineEdit(self)
        self.l4SZAMinLineEdit.setText(str(ConfigFile.settings["fL4SZAMin"]))
        self.l4SZAMinLineEdit.setValidator(doubleValidator)        
        l4SZAMaxLabel = QtWidgets.QLabel("     SZA Maximum (deg)", self)
        self.l4SZAMaxLineEdit = QtWidgets.QLineEdit(self)
        self.l4SZAMaxLineEdit.setText(str(ConfigFile.settings["fL4SZAMax"]))
        self.l4SZAMaxLineEdit.setValidator(doubleValidator)         

        l4EnableSpecQualityCheckLabel = QtWidgets.QLabel("    Enable Spectral Outlier Filter", self)
        self.l4EnableSpecQualityCheckCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL4EnableSpecQualityCheck"]) == 1:
            self.l4EnableSpecQualityCheckCheckBox.setChecked(True)       
        

        # Time Average Rrs
        l4TimeIntervalLabel = QtWidgets.QLabel("  Time Ave. Interval (seconds; 0=None)", self)
        self.l4TimeIntervalLineEdit = QtWidgets.QLineEdit(self)
        self.l4TimeIntervalLineEdit.setText(str(ConfigFile.settings["fL4TimeInterval"]))
        self.l4TimeIntervalLineEdit.setValidator(intValidator)        

        self.l4EnablePercentLtLabel = QtWidgets.QLabel("    Enable Percent Lt Calculation", self)
        self.l4EnablePercentLtCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL4EnablePercentLt"]) == 1:
           self.l4EnablePercentLtCheckBox.setChecked(True)

        # Set percentage Lt filter
        self.l4PercentLtLabel = QtWidgets.QLabel("      Percent Lt (%)", self)
        self.l4PercentLtLineEdit = QtWidgets.QLineEdit(self)
        self.l4PercentLtLineEdit.setText(str(ConfigFile.settings["fL4PercentLt"]))
        self.l4PercentLtLineEdit.setValidator(doubleValidator)

        self.l4EnablePercentLtCheckBoxUpdate()

        # Rho Sky & Wind
        l4RhoSkyLabel = QtWidgets.QLabel("    Default Rho Sky", self)
        self.l4RhoSkyLineEdit = QtWidgets.QLineEdit(self)
        self.l4RhoSkyLineEdit.setText(str(ConfigFile.settings["fL4RhoSky"]))
        self.l4RhoSkyLineEdit.setValidator(doubleValidator)

        l4EnableWindSpeedCalculationLabel = QtWidgets.QLabel("    Enable Wind Speed Rho Calculation", self)
        self.l4EnableWindSpeedCalculationCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL4EnableWindSpeedCalculation"]) == 1:
            self.l4EnableWindSpeedCalculationCheckBox.setChecked(True)

        self.l4DefaultWindSpeedLabel = QtWidgets.QLabel("      Default Wind Speed (m/s)", self)
        self.l4DefaultWindSpeedLineEdit = QtWidgets.QLineEdit(self)
        self.l4DefaultWindSpeedLineEdit.setText(str(ConfigFile.settings["fL4DefaultWindSpeed"]))
        self.l4DefaultWindSpeedLineEdit.setValidator(doubleValidator)
        
        self.l4EnableWindSpeedCalculationCheckBoxUpdate()

        # Meteorology Flags
        l4QualityFlagLabel = QtWidgets.QLabel("    Enable Meteorological Flags", self)
        # l4QualityFlagLabel2 = QtWidgets.QLabel("    (Wernand 2012, OO XVI)", self)
        self.l4QualityFlagCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL4EnableQualityFlags"]) == 1:
            self.l4QualityFlagCheckBox.setChecked(True)

        self.l4EsFlagLabel = QtWidgets.QLabel("      Significant Es(480) (uW cm^-2 nm^-1)", self)
        self.l4EsFlagLineEdit = QtWidgets.QLineEdit(self)
        self.l4EsFlagLineEdit.setText(str(ConfigFile.settings["fL4SignificantEsFlag"]))
        self.l4EsFlagLineEdit.setValidator(doubleValidator)

        self.l4DawnDuskFlagLabel = QtWidgets.QLabel("      Dawn/Dusk Es(470/680)<", self)
        self.l4DawnDuskFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l4DawnDuskFlagLineEdit.setText(str(ConfigFile.settings["fL4DawnDuskFlag"]))
        self.l4DawnDuskFlagLineEdit.setValidator(doubleValidator)

        self.l4RainfallHumidityFlagLabel = QtWidgets.QLabel("      Rain/Humid. Es(720/370)<", self)
        self.l4RainfallHumidityFlagLineEdit = QtWidgets.QLineEdit("", self)
        self.l4RainfallHumidityFlagLineEdit.setText(str(ConfigFile.settings["fL4RainfallHumidityFlag"]))
        self.l4RainfallHumidityFlagLineEdit.setValidator(doubleValidator)

        self.l4QualityFlagCheckBoxUpdate()

        # NIR AtmoCorr
        l4NIRCorrectionLabel = QtWidgets.QLabel("  Enable Near-infrared Correction", self)
        self.l4NIRCorrectionCheckBox = QtWidgets.QCheckBox("", self)
        if int(ConfigFile.settings["bL4PerformNIRCorrection"]) == 1:
            self.l4NIRCorrectionCheckBox.setChecked(True)

        l4PlotsLabel = QtWidgets.QLabel("  Generate Spectral Plots", self)
        l4PlotRrsLabel = QtWidgets.QLabel("Rrs", self)     
        self.l4PlotRrsCheckBox = QtWidgets.QCheckBox("", self)      
        if int(ConfigFile.settings["bL4PlotRrs"]) == 1:
            self.l4PlotRrsCheckBox.setChecked(True)

        l4PlotEsLabel = QtWidgets.QLabel("Es", self)     
        self.l4PlotEsCheckBox = QtWidgets.QCheckBox("", self)      
        if int(ConfigFile.settings["bL4PlotEs"]) == 1:
            self.l4PlotEsCheckBox.setChecked(True)

        l4PlotLiLabel = QtWidgets.QLabel("Li", self)     
        self.l4PlotLiCheckBox = QtWidgets.QCheckBox("", self)      
        if int(ConfigFile.settings["bL4PlotLi"]) == 1:
            self.l4PlotLiCheckBox.setChecked(True)

        l4PlotLtLabel = QtWidgets.QLabel("Lt", self)     
        self.l4PlotLtCheckBox = QtWidgets.QCheckBox("", self)      
        if int(ConfigFile.settings["bL4PlotLt"]) == 1:
            self.l4PlotLtCheckBox.setChecked(True)

        self.l4QualityFlagCheckBox.clicked.connect(self.l4QualityFlagCheckBoxUpdate)
        self.l4EnableWindSpeedCalculationCheckBox.clicked.connect(self.l4EnableWindSpeedCalculationCheckBoxUpdate)
        self.l4NIRCorrectionCheckBox.clicked.connect(self.l4NIRCorrectionCheckBoxUpdate)
        self.l4EnablePercentLtCheckBox.clicked.connect(self.l4EnablePercentLtCheckBoxUpdate)

        l4SaveSeaBASSLabel = QtWidgets.QLabel("Save SeaBASS text file", self)     
        self.l4SaveSeaBASSCheckBox = QtWidgets.QCheckBox("", self)    
        self.l4SaveSeaBASSCheckBox.clicked.connect(self.l4SaveSeaBASSCheckBoxUpdate)        
        if int(ConfigFile.settings["bL4SaveSeaBASS"]) == 1:
            self.l4SaveSeaBASSCheckBox.setChecked(True)


        self.saveButton = QtWidgets.QPushButton("Save")
        self.saveAsButton = QtWidgets.QPushButton("Save As")
        self.cancelButton = QtWidgets.QPushButton("Cancel")                      
            
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.saveAsButton.clicked.connect(self.saveAsButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        # Whole Window Box
        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(nameLabel)

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

        VBox1.addSpacing(10)

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
        
        VBox1.addSpacing(10)

        # L1b
        VBox1.addWidget(l1bLabel)
        VBox1.addWidget(l1bSublabel)
        VBox1.addWidget(l1bSublabel2)
        VBox1.addWidget(l1bSublabel3)

        # Rotator
        RotHomeAngleHBox = QtWidgets.QHBoxLayout()       
        RotHomeAngleHBox.addWidget(self.l1bRotatorHomeAngleLabel)
        RotHomeAngleHBox.addWidget(self.l1bRotatorHomeAngleLineEdit)        
        VBox1.addLayout(RotHomeAngleHBox)    
        RotatorDelayHBox = QtWidgets.QHBoxLayout()
        RotatorDelayHBox.addWidget(self.l1bRotatorDelayLabel)
        RotatorDelayHBox.addWidget(self.l1bRotatorDelayLineEdit)
        VBox1.addLayout(RotatorDelayHBox)

        # Pitch & Roll
        PitchRollHBox = QtWidgets.QHBoxLayout()
        PitchRollHBox.addWidget(l1bCleanPitchRollLabel)
        PitchRollHBox.addWidget(self.l1bCleanPitchRollCheckBox)
        VBox1.addLayout(PitchRollHBox)
        RotMinHBox = QtWidgets.QHBoxLayout()
        RotMinHBox.addWidget(self.l1bPitchRollPitchLabel)
        RotMinHBox.addWidget(self.l1bPitchRollPitchLineEdit)
        VBox1.addLayout(RotMinHBox)
        RotMaxHBox = QtWidgets.QHBoxLayout()
        RotMaxHBox.addWidget(self.l1bPitchRollRollLabel)
        RotMaxHBox.addWidget(self.l1bPitchRollRollLineEdit)
        VBox1.addLayout(RotMaxHBox)                        
        
        # Rotator
        rotateHBox = QtWidgets.QHBoxLayout()
        rotateHBox.addWidget(l1bCleanRotatorAngleLabel)
        rotateHBox.addWidget(self.l1bCleanRotatorAngleCheckBox)
        VBox1.addLayout(rotateHBox)
        RotMinHBox = QtWidgets.QHBoxLayout()
        RotMinHBox.addWidget(self.l1bRotatorAngleMinLabel)
        RotMinHBox.addWidget(self.l1bRotatorAngleMinLineEdit)
        VBox1.addLayout(RotMinHBox)
        RotMaxHBox = QtWidgets.QHBoxLayout()
        RotMaxHBox.addWidget(self.l1bRotatorAngleMaxLabel)
        RotMaxHBox.addWidget(self.l1bRotatorAngleMaxLineEdit)
        VBox1.addLayout(RotMaxHBox) 
                
        
        # Relative SZA
        CleanSunAngleHBox = QtWidgets.QHBoxLayout()
        CleanSunAngleHBox.addWidget(l1bCleanSunAngleLabel)
        CleanSunAngleHBox.addWidget(self.l1bCleanSunAngleCheckBox)
        VBox1.addLayout(CleanSunAngleHBox)                      
        SunAngleMinHBox = QtWidgets.QHBoxLayout()       
        SunAngleMinHBox.addWidget(self.l1bSunAngleMinLabel)
        SunAngleMinHBox.addWidget(self.l1bSunAngleMinLineEdit)
        VBox1.addLayout(SunAngleMinHBox)         
        SunAngleMaxHBox = QtWidgets.QHBoxLayout()       
        SunAngleMaxHBox.addWidget(self.l1bSunAngleMaxLabel)
        SunAngleMaxHBox.addWidget(self.l1bSunAngleMaxLineEdit)
        VBox1.addLayout(SunAngleMaxHBox)         

        # Middle Vertical Box
        VBox2 = QtWidgets.QVBoxLayout()
        VBox2.setAlignment(QtCore.Qt.AlignBottom)               
        
        # VBox2.addSpacing(20) 
        # # Middle Vertical Box
        # VBox2 = QtWidgets.QVBoxLayout()
        # VBox2.setAlignment(QtCore.Qt.AlignBottom)               
        
        # VBox2.addWidget(l1bLabel2)
        # # Relative SZA
        # CleanSunAngleHBox = QtWidgets.QHBoxLayout()
        # CleanSunAngleHBox.addWidget(l1bCleanSunAngleLabel)
        # CleanSunAngleHBox.addWidget(self.l1bCleanSunAngleCheckBox)
        # VBox2.addLayout(CleanSunAngleHBox)                      
        # SunAngleMinHBox = QtWidgets.QHBoxLayout()       
        # SunAngleMinHBox.addWidget(self.l1bSunAngleMinLabel)
        # SunAngleMinHBox.addWidget(self.l1bSunAngleMinLineEdit)
        # VBox2.addLayout(SunAngleMinHBox)         
        # SunAngleMaxHBox = QtWidgets.QHBoxLayout()       
        # SunAngleMaxHBox.addWidget(self.l1bSunAngleMaxLabel)
        # SunAngleMaxHBox.addWidget(self.l1bSunAngleMaxLineEdit)
        # VBox2.addLayout(SunAngleMaxHBox)         
        
        # VBox2.addSpacing(20) 

        
        # VBox2.addSpacing(20)           

        # L2
        VBox2.addWidget(l2Label)
        VBox2.addWidget(l2Sublabel)
        
        # Deglitcher
        deglitchHBox = QtWidgets.QHBoxLayout()
        deglitchHBox.addWidget(self.l2DeglitchLabel)
        deglitchHBox.addWidget(self.l2DeglitchCheckBox)
        VBox2.addLayout(deglitchHBox)

        deglitch0HBox = QtWidgets.QHBoxLayout()
        deglitch0HBox.addWidget(self.l2Deglitch0Label)
        deglitch0HBox.addWidget(self.l2Deglitch0LineEdit)
        VBox2.addLayout(deglitch0HBox)

        deglitch1HBox = QtWidgets.QHBoxLayout()
        deglitch1HBox.addWidget(self.l2Deglitch1Label)
        deglitch1HBox.addWidget(self.l2Deglitch1LineEdit)
        VBox2.addLayout(deglitch1HBox)
        
        deglitch2HBox = QtWidgets.QHBoxLayout()
        deglitch2HBox.addWidget(self.l2Deglitch2Label)
        deglitch2HBox.addWidget(self.l2Deglitch2LineEdit)
        VBox2.addLayout(deglitch2HBox)

        deglitch3HBox = QtWidgets.QHBoxLayout()
        deglitch3HBox.addWidget(self.l2Deglitch3Label)
        deglitch3HBox.addWidget(self.l2Deglitch3LineEdit)
        VBox2.addLayout(deglitch3HBox)

        VBox2.addSpacing(10)

        # L2 Anomaly Launcher
        # VBox2.addWidget(l2AnomalyLabel)
        VBox2.addWidget(l2AnomalySublabel1)
        VBox2.addWidget(l2AnomalySublabel2)
        VBox2.addWidget(l2AnomalySublabel3)
        VBox2.addWidget(self.anomalyButton)


        VBox2.addSpacing(20)   

        #L3        
        VBox2.addWidget(l3Label)
        VBox2.addWidget(l3Sublabel)
        VBox2.addWidget(l3Sublabel2)

        interpHBox = QtWidgets.QHBoxLayout()
        interpHBox.addWidget(l3InterpIntervalLabel)
        interpHBox.addWidget(self.l3InterpIntervalLineEdit)
        VBox2.addLayout(interpHBox)

        VBox2.addSpacing(10)

        l3PlotTimeInterpHBox = QtWidgets.QHBoxLayout()
        l3PlotTimeInterpHBox.addWidget(l3PlotTimeInterpLabel)
        l3PlotTimeInterpHBox.addWidget(self.l3PlotTimeInterpCheckBox)    
        VBox2.addLayout(l3PlotTimeInterpHBox)

        VBox2.addSpacing(10)
        
        l3SeaBASSHBox = QtWidgets.QHBoxLayout()
        l3SeaBASSHBox.addWidget(l3SaveSeaBASSLabel)
        l3SeaBASSHBox.addWidget(self.l3SaveSeaBASSCheckBox)    
        VBox2.addLayout(l3SeaBASSHBox)

        l3SeaBASSHeaderHBox = QtWidgets.QHBoxLayout()
        l3SeaBASSHeaderHBox.addWidget(self.l3SeaBASSHeaderLabel)
        # l3SeaBASSHeaderHBox.addWidget(self.l3SeaBASSHeaderComboBox)
        l3SeaBASSHeaderHBox.addWidget(self.l3SeaBASSHeaderLineEdit)
        VBox2.addLayout(l3SeaBASSHeaderHBox)

        l3SeaBASSHeaderHBox2 = QtWidgets.QHBoxLayout()
        l3SeaBASSHeaderHBox2.addWidget(self.l3SeaBASSHeaderNewButton)
        l3SeaBASSHeaderHBox2.addWidget(self.l3SeaBASSHeaderOpenButton)
        l3SeaBASSHeaderHBox2.addWidget(self.l3SeaBASSHeaderEditButton)
        l3SeaBASSHeaderHBox2.addWidget(self.l3SeaBASSHeaderDeleteButton)
        VBox2.addLayout(l3SeaBASSHeaderHBox2)
        
        
        # Right box
        VBox3 = QtWidgets.QVBoxLayout()
        VBox3.setAlignment(QtCore.Qt.AlignBottom)

        # L4
        VBox3.addWidget(l4Label)
        VBox3.addWidget(l4Sublabel)
        VBox3.addWidget(l4Sublabel2)
        
        # SZA Min
        maxWindBox = QtWidgets.QHBoxLayout()
        maxWindBox.addWidget(l4MaxWindLabel)
        maxWindBox.addWidget(self.l4MaxWindLineEdit)
        VBox3.addLayout(maxWindBox)

        # SZA Min
        SZAHBox1 = QtWidgets.QHBoxLayout()
        SZAHBox1.addWidget(l4SZAMinLabel)
        SZAHBox1.addWidget(self.l4SZAMinLineEdit)
        VBox3.addLayout(SZAHBox1)

        # SZA Max
        SZAHBox2 = QtWidgets.QHBoxLayout()
        SZAHBox2.addWidget(l4SZAMaxLabel)
        SZAHBox2.addWidget(self.l4SZAMaxLineEdit)
        VBox3.addLayout(SZAHBox2)

        # Spectral Outlier Filter
        SpecFilterHBox = QtWidgets.QHBoxLayout()
        SpecFilterHBox.addWidget(l4EnableSpecQualityCheckLabel)
        SpecFilterHBox.addWidget(self.l4EnableSpecQualityCheckCheckBox)
        VBox3.addLayout(SpecFilterHBox)

        VBox3.addSpacing(5)

        # Time Average Rrs
        TimeAveHBox = QtWidgets.QHBoxLayout()
        TimeAveHBox.addWidget(l4TimeIntervalLabel)
        TimeAveHBox.addWidget(self.l4TimeIntervalLineEdit)
        VBox3.addLayout(TimeAveHBox)     

        # Percent Light; Hooker & Morel 2003
        PercentLtHBox = QtWidgets.QHBoxLayout()
        PercentLtHBox.addWidget(self.l4EnablePercentLtLabel)
        PercentLtHBox.addWidget(self.l4EnablePercentLtCheckBox)
        VBox3.addLayout(PercentLtHBox)  
        PercentLtHBox2 = QtWidgets.QHBoxLayout()
        PercentLtHBox2.addWidget(self.l4PercentLtLabel)
        PercentLtHBox2.addWidget(self.l4PercentLtLineEdit)
        VBox3.addLayout(PercentLtHBox2)              

        # Rho Sky & Wind
        RhoHBox = QtWidgets.QHBoxLayout()
        RhoHBox.addWidget(l4RhoSkyLabel)
        RhoHBox.addWidget(self.l4RhoSkyLineEdit)
        VBox3.addLayout(RhoHBox)
        WindSpeedHBox = QtWidgets.QHBoxLayout()
        WindSpeedHBox.addWidget(l4EnableWindSpeedCalculationLabel)
        WindSpeedHBox.addWidget(self.l4EnableWindSpeedCalculationCheckBox)
        VBox3.addLayout(WindSpeedHBox)         
        WindSpeedHBox2 = QtWidgets.QHBoxLayout()    
        WindSpeedHBox2.addWidget(self.l4DefaultWindSpeedLabel)
        WindSpeedHBox2.addWidget(self.l4DefaultWindSpeedLineEdit)
        VBox3.addLayout(WindSpeedHBox2)         

        VBox3.addSpacing(5)

        # Meteorology Flags
        QualityFlagHBox = QtWidgets.QHBoxLayout()
        QualityFlagHBox.addWidget(l4QualityFlagLabel)
        # QualityFlagHBox.addWidget(l4QualityFlagLabel2)
        QualityFlagHBox.addWidget(self.l4QualityFlagCheckBox)
        VBox3.addLayout(QualityFlagHBox) 
        EsFlagHBox = QtWidgets.QHBoxLayout()        
        EsFlagHBox.addWidget(self.l4EsFlagLabel)
        EsFlagHBox.addWidget(self.l4EsFlagLineEdit)
        VBox3.addLayout(EsFlagHBox) 
        DawnFlagHBox =QtWidgets.QHBoxLayout()
        DawnFlagHBox.addWidget(self.l4DawnDuskFlagLabel)
        DawnFlagHBox.addWidget(self.l4DawnDuskFlagLineEdit)
        VBox3.addLayout(DawnFlagHBox) 
        RainFlagHBox = QtWidgets.QHBoxLayout()
        RainFlagHBox.addWidget(self.l4RainfallHumidityFlagLabel)
        RainFlagHBox.addWidget(self.l4RainfallHumidityFlagLineEdit)
        VBox3.addLayout(RainFlagHBox) 

        VBox3.addSpacing(5)

        # NIR AtmoCorr
        NIRCorrectionHBox = QtWidgets.QHBoxLayout()
        NIRCorrectionHBox.addWidget(l4NIRCorrectionLabel)
        NIRCorrectionHBox.addWidget(self.l4NIRCorrectionCheckBox)
        VBox3.addLayout(NIRCorrectionHBox)         

        VBox3.addSpacing(5)

        # Plotting
        VBox3.addWidget(l4PlotsLabel)
        l4PlotHBox = QtWidgets.QHBoxLayout()
        l4PlotHBox.addSpacing(45)
        l4PlotHBox.addWidget(l4PlotRrsLabel)
        l4PlotHBox.addWidget(self.l4PlotRrsCheckBox)    
        l4PlotHBox.addWidget(l4PlotEsLabel)
        l4PlotHBox.addWidget(self.l4PlotEsCheckBox)
        l4PlotHBox.addWidget(l4PlotLiLabel)
        l4PlotHBox.addWidget(self.l4PlotLiCheckBox)
        l4PlotHBox.addWidget(l4PlotLtLabel)
        l4PlotHBox.addWidget(self.l4PlotLtCheckBox)
        VBox3.addLayout(l4PlotHBox)    

        VBox3.addSpacing(5)

        # Horizontal Box; Save SeaBASS
        l4SeaBASSHBox = QtWidgets.QHBoxLayout()
        l4SeaBASSHBox.addWidget(l4SaveSeaBASSLabel)
        l4SeaBASSHBox.addWidget(self.l4SaveSeaBASSCheckBox)    
        VBox3.addLayout(l4SeaBASSHBox)    

        # Add 3 Vertical Boxes to Horizontal Box hBox
        hBox = QtWidgets.QHBoxLayout()
        hBox.addLayout(VBox1)
        hBox.addLayout(VBox2)        
        hBox.addLayout(VBox3)    

        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.saveAsButton)
        saveHBox.addWidget(self.cancelButton)

        # Adds hBox and saveHBox to primary VBox 
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
            (_, filename) = os.path.split(src)
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

    def l1bCleanPitchRollCheckBoxUpdate(self):
        print("ConfigWindow - l1bCleanPitchRollCheckBoxUpdate")
        
        disabled = (not self.l1bCleanPitchRollCheckBox.isChecked())
        self.l1bPitchRollPitchLabel.setDisabled(disabled)
        self.l1bPitchRollPitchLineEdit.setDisabled(disabled)
        self.l1bPitchRollRollLabel.setDisabled(disabled)
        self.l1bPitchRollRollLineEdit.setDisabled(disabled)

    def l1bCleanRotatorAngleCheckBoxUpdate(self):
        print("ConfigWindow - l1bCleanRotatorAngleCheckBoxUpdate")
        
        disabled = (not self.l1bCleanRotatorAngleCheckBox.isChecked())
        self.l1bRotatorAngleMinLabel.setDisabled(disabled)
        self.l1bRotatorAngleMinLineEdit.setDisabled(disabled)
        self.l1bRotatorAngleMaxLabel.setDisabled(disabled)
        self.l1bRotatorAngleMaxLineEdit.setDisabled(disabled)

    def l1bCleanSunAngleCheckBoxUpdate(self):
        print("ConfigWindow - l1bCleanSunAngleCheckBoxUpdate")
        
        disabled = (not self.l1bCleanSunAngleCheckBox.isChecked())
        self.l1bSunAngleMinLabel.setDisabled(disabled)
        self.l1bSunAngleMinLineEdit.setDisabled(disabled)
        self.l1bSunAngleMaxLabel.setDisabled(disabled)
        self.l1bSunAngleMaxLineEdit.setDisabled(disabled)

    def anomalyButtonPressed(self):
        print("CalibrationEditWindow - Launching anomaly analysis module")

        AnomalyDetection(self,self.inputDirectory)

    def l2DeglitchCheckBoxUpdate(self):
        print("ConfigWindow - l2DeglitchCheckBoxUpdate")
        
        disabled = (not self.l2DeglitchCheckBox.isChecked())
        self.l2Deglitch0Label.setDisabled(disabled)
        self.l2Deglitch0LineEdit.setDisabled(disabled)
        self.l2Deglitch1Label.setDisabled(disabled)
        self.l2Deglitch1LineEdit.setDisabled(disabled)
        self.l2Deglitch2Label.setDisabled(disabled)
        self.l2Deglitch2LineEdit.setDisabled(disabled)   
        self.l2Deglitch3Label.setDisabled(disabled)
        self.l2Deglitch3LineEdit.setDisabled(disabled)     

    def l3PlotTimeInterpCheckBoxUpdate(self):
        print("ConfigWindow - l3PlotTimeInterpCheckBoxUpdate")

    def l3SaveSeaBASSCheckBoxUpdate(self):
        print("ConfigWindow - l3SaveSeaBASSCheckBoxUpdate")
        disabled = (not self.l3SaveSeaBASSCheckBox.isChecked())
        self.l3SeaBASSHeaderNewButton.setDisabled(disabled)
        self.l3SeaBASSHeaderOpenButton.setDisabled(disabled)
        self.l3SeaBASSHeaderEditButton.setDisabled(disabled)
        self.l3SeaBASSHeaderDeleteButton.setDisabled(disabled)

    def l3seaBASSHeaderNewButtonPressed(self):
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
            
            self.l3SeaBASSHeaderLineEdit.setText(seaBASSHeaderFileName)  

    def l3seaBASSHeaderOpenButtonPressed(self):
        print("SeaBASSHeader Open Dialogue")
        text, ok = QtWidgets.QFileDialog.getOpenFileNames(self, "Select SeaBASS Header File","Config","hdr(*.hdr)")
        if ok:
            (_, fname) = os.path.split(text[0])
            print(fname)
            if len(fname[0]) == 1:
                self.l3SeaBASSHeaderLineEdit.setText(fname)            

    def l3seaBASSHeaderEditButtonPressed(self):
        print("Edit seaBASSHeader Dialogue")
        
        # seaBASSHeaderFileName = self.l3SeaBASSHeaderComboBox.currentText()
        seaBASSHeaderFileName = self.l3SeaBASSHeaderLineEdit.text()
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

    def l3seaBASSHeaderDeleteButtonPressed(self):
        print("Delete seaBASSHeader Dialogue")
        # print("index: ", self.seaBASSHeaderComboBox.currentIndex())
        # print("text: ", self.seaBASSHeaderComboBox.currentText())
        # seaBASSHeaderFileName = self.l3SeaBASSHeaderComboBox.currentText()
        seaBASSHeaderFileName = self.l3SeaBASSHeaderLineEdit.text()
        seaBASSHeaderPath = os.path.join("Config", seaBASSHeaderFileName)
        if os.path.isfile(seaBASSHeaderPath):
            seaBASSHeaderDeleteMessage = "Delete " + seaBASSHeaderFileName + "?"

            reply = QtWidgets.QMessageBox.question(self, 'Message', seaBASSHeaderDeleteMessage, \
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                SeaBASSHeader.deleteSeaBASSHeader(seaBASSHeaderFileName)
                self.l3SeaBASSHeaderLineEdit.setText('')              
        else:
            #print("Not a seaBASSHeader File: " + seaBASSHeaderFileName)
            message = "Not a seaBASSHeader File: " + seaBASSHeaderFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)

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
        
        disabled = (not self.l4EnablePercentLtCheckBox.isChecked())
        self.l4PercentLtLabel.setDisabled(disabled)
        self.l4PercentLtLineEdit.setDisabled(disabled)        

    def l4SaveSeaBASSCheckBoxUpdate(self):
        print("ConfigWindow - l4SaveSeaBASSCheckBoxUpdate")

    def saveButtonPressed(self):
        print("ConfigWindow - Save Pressed")
        # print(self.l2Deglitch0LineEdit.text())
        # print(int(self.l2Deglitch0LineEdit.text())%2)
        if int(self.l2Deglitch0LineEdit.text())%2 == 0 or int(self.l2Deglitch1LineEdit.text())%2 ==0:
            alert = QtWidgets.QMessageBox()
            alert.setText('Deglitching windows must be odd integers.')
            alert.exec_()
            return

        ConfigFile.settings["bL1aCleanSZA"] = int(self.l1aCleanSZACheckBox.isChecked())
        ConfigFile.settings["fL1aCleanSZAMax"] = float(self.l1aCleanSZAMaxLineEdit.text())
        
        ConfigFile.settings["fL1bRotatorHomeAngle"] = float(self.l1bRotatorHomeAngleLineEdit.text())
        ConfigFile.settings["fL1bRotatorDelay"] = float(self.l1bRotatorDelayLineEdit.text())     
        ConfigFile.settings["bL1bCleanPitchRoll"] = int(self.l1bCleanPitchRollCheckBox.isChecked())        
        ConfigFile.settings["fL1bPitchRollPitch"] = float(self.l1bPitchRollPitchLineEdit.text())
        ConfigFile.settings["fL1bPitchRollRoll"] = float(self.l1bPitchRollRollLineEdit.text())         
        ConfigFile.settings["bL1bCleanRotatorAngle"] = int(self.l1bCleanRotatorAngleCheckBox.isChecked())        
        ConfigFile.settings["fL1bRotatorAngleMin"] = float(self.l1bRotatorAngleMinLineEdit.text())
        ConfigFile.settings["fL1bRotatorAngleMax"] = float(self.l1bRotatorAngleMaxLineEdit.text())                
        ConfigFile.settings["bL1bCleanSunAngle"] = int(self.l1bCleanSunAngleCheckBox.isChecked())        
        ConfigFile.settings["fL1bSunAngleMin"] = float(self.l1bSunAngleMinLineEdit.text())
        ConfigFile.settings["fL1bSunAngleMax"] = float(self.l1bSunAngleMaxLineEdit.text())

        ConfigFile.settings["bL2Deglitch"] = int(self.l2DeglitchCheckBox.isChecked()) 
        ConfigFile.settings["fL2Deglitch0"] = int(self.l2Deglitch0LineEdit.text())
        ConfigFile.settings["fL2Deglitch1"] = int(self.l2Deglitch1LineEdit.text())
        ConfigFile.settings["fL2Deglitch2"] = float(self.l2Deglitch2LineEdit.text())
        ConfigFile.settings["fL2Deglitch3"] = float(self.l2Deglitch3LineEdit.text())

        ConfigFile.settings["fL3InterpInterval"] = float(self.l3InterpIntervalLineEdit.text())
        ConfigFile.settings["bL3PlotTimeInterp"] = int(self.l3PlotTimeInterpCheckBox.isChecked())
        ConfigFile.settings["bL3SaveSeaBASS"] = int(self.l3SaveSeaBASSCheckBox.isChecked())
        # ConfigFile.settings["seaBASSHeaderFileName"] = self.l3SeaBASSHeaderComboBox.currentText()
        ConfigFile.settings["seaBASSHeaderFileName"] = self.l3SeaBASSHeaderLineEdit.text()
        
        ConfigFile.settings["fL4MaxWind"] = float(self.l4MaxWindLineEdit.text())
        ConfigFile.settings["fL4SZAMin"] = float(self.l4SZAMinLineEdit.text())
        ConfigFile.settings["fL4SZAMax"] = float(self.l4SZAMaxLineEdit.text())
        ConfigFile.settings["bL4EnableSpecQualityCheck"] = int(self.l4EnableSpecQualityCheckCheckBox.isChecked())
        ConfigFile.settings["fL4RhoSky"] = float(self.l4RhoSkyLineEdit.text())
        ConfigFile.settings["bL4EnableWindSpeedCalculation"] = int(self.l4EnableWindSpeedCalculationCheckBox.isChecked())
        ConfigFile.settings["fL4DefaultWindSpeed"] = float(self.l4DefaultWindSpeedLineEdit.text())
        ConfigFile.settings["bL4EnableQualityFlags"] = int(self.l4QualityFlagCheckBox.isChecked())
        ConfigFile.settings["fL4SignificantEsFlag"] = float(self.l4EsFlagLineEdit.text())
        ConfigFile.settings["fL4DawnDuskFlag"] = float(self.l4DawnDuskFlagLineEdit.text())
        ConfigFile.settings["fL4RainfallHumidityFlag"] = float(self.l4RainfallHumidityFlagLineEdit.text())
        ConfigFile.settings["fL4TimeInterval"] = int(self.l4TimeIntervalLineEdit.text())                
        ConfigFile.settings["bL4PerformNIRCorrection"] = int(self.l4NIRCorrectionCheckBox.isChecked())
        ConfigFile.settings["bL4EnablePercentLt"] = int(self.l4EnablePercentLtCheckBox.isChecked())
        ConfigFile.settings["fL4PercentLt"] = float(self.l4PercentLtLineEdit.text())
        ConfigFile.settings["bL4PlotRrs"] = int(self.l4PlotRrsCheckBox.isChecked())
        ConfigFile.settings["bL4PlotEs"] = int(self.l4PlotEsCheckBox.isChecked())
        ConfigFile.settings["bL4PlotLi"] = int(self.l4PlotLiCheckBox.isChecked())
        ConfigFile.settings["bL4PlotLt"] = int(self.l4PlotLtCheckBox.isChecked())
        ConfigFile.settings["bL4SaveSeaBASS"] = int(self.l4SaveSeaBASSCheckBox.isChecked())

        ConfigFile.saveConfig(self.name)

        QtWidgets.QMessageBox.about(self, "Edit Config File", "Config File Saved")
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
            
            if int(self.l2Deglitch0LineEdit.text())%2 == 0 or int(self.l2Deglitch1LineEdit.text())%2 ==0:
                alert = QtWidgets.QMessageBox()
                alert.setText('Deglitching windows must be odd integers.')
                alert.exec_()
                return

            ConfigFile.settings["bL1aCleanSZA"] = int(self.l1aCleanSZACheckBox.isChecked())
            ConfigFile.settings["fL1aCleanSZAMax"] = float(self.l1aCleanSZAMaxLineEdit.text())
            
            ConfigFile.settings["fL1bRotatorHomeAngle"] = float(self.l1bRotatorHomeAngleLineEdit.text())
            ConfigFile.settings["fL1bRotatorDelay"] = float(self.l1bRotatorDelayLineEdit.text())     
            ConfigFile.settings["bL1bCleanPitchRoll"] = int(self.l1bCleanPitchRollCheckBox.isChecked())        
            ConfigFile.settings["fL1bPitchRollPitch"] = float(self.l1bPitchRollPitchLineEdit.text())
            ConfigFile.settings["fL1bPitchRollRoll"] = float(self.l1bPitchRollRollLineEdit.text())         
            ConfigFile.settings["bL1bCleanRotatorAngle"] = int(self.l1bCleanRotatorAngleCheckBox.isChecked())        
            ConfigFile.settings["fL1bRotatorAngleMin"] = float(self.l1bRotatorAngleMinLineEdit.text())
            ConfigFile.settings["fL1bRotatorAngleMax"] = float(self.l1bRotatorAngleMaxLineEdit.text())                
            ConfigFile.settings["bL1bCleanSunAngle"] = int(self.l1bCleanSunAngleCheckBox.isChecked())        
            ConfigFile.settings["fL1bSunAngleMin"] = float(self.l1bSunAngleMinLineEdit.text())
            ConfigFile.settings["fL1bSunAngleMax"] = float(self.l1bSunAngleMaxLineEdit.text())

            ConfigFile.settings["bL2Deglitch"] = int(self.l2DeglitchCheckBox.isChecked()) 
            ConfigFile.settings["fL2Deglitch0"] = int(self.l2Deglitch0LineEdit.text())
            ConfigFile.settings["fL2Deglitch1"] = int(self.l2Deglitch1LineEdit.text())
            ConfigFile.settings["fL2Deglitch2"] = float(self.l2Deglitch2LineEdit.text())
            ConfigFile.settings["fL2Deglitch3"] = float(self.l2Deglitch3LineEdit.text())

            ConfigFile.settings["fL3InterpInterval"] = float(self.l3InterpIntervalLineEdit.text())
            ConfigFile.settings["bL3PlotTimeInterp"] = int(self.l3PlotTimeInterpCheckBox.isChecked())
            ConfigFile.settings["bL3SaveSeaBASS"] = int(self.l3SaveSeaBASSCheckBox.isChecked())
            # ConfigFile.settings["seaBASSHeaderFileName"] = self.l3SeaBASSHeaderComboBox.currentText()
            ConfigFile.settings["seaBASSHeaderFileName"] = self.l3SeaBASSHeaderLineEdit.text()
            
            ConfigFile.settings["fL4MaxWind"] = float(self.l4MaxWindLineEdit.text())
            ConfigFile.settings["fL4SZAMin"] = float(self.l4SZAMinLineEdit.text())
            ConfigFile.settings["fL4SZAMax"] = float(self.l4SZAMaxLineEdit.text())
            ConfigFile.settings["bL4EnableSpecQualityCheck"] = int(self.l4EnableSpecQualityCheckCheckBox.isChecked())
            ConfigFile.settings["fL4RhoSky"] = float(self.l4RhoSkyLineEdit.text())
            ConfigFile.settings["bL4EnableWindSpeedCalculation"] = int(self.l4EnableWindSpeedCalculationCheckBox.isChecked())
            ConfigFile.settings["fL4DefaultWindSpeed"] = float(self.l4DefaultWindSpeedLineEdit.text())
            ConfigFile.settings["bL4EnableQualityFlags"] = int(self.l4QualityFlagCheckBox.isChecked())
            ConfigFile.settings["fL4SignificantEsFlag"] = float(self.l4EsFlagLineEdit.text())
            ConfigFile.settings["fL4DawnDuskFlag"] = float(self.l4DawnDuskFlagLineEdit.text())
            ConfigFile.settings["fL4RainfallHumidityFlag"] = float(self.l4RainfallHumidityFlagLineEdit.text())
            ConfigFile.settings["fL4TimeInterval"] = int(self.l4TimeIntervalLineEdit.text())                
            ConfigFile.settings["bL4PerformNIRCorrection"] = int(self.l4NIRCorrectionCheckBox.isChecked())
            ConfigFile.settings["bL4EnablePercentLt"] = int(self.l4EnablePercentLtCheckBox.isChecked())
            ConfigFile.settings["fL4PercentLt"] = float(self.l4PercentLtLineEdit.text())
            ConfigFile.settings["bL4PlotRrs"] = int(self.l4PlotRrsCheckBox.isChecked())  
            ConfigFile.settings["bL4PlotEs"] = int(self.l4PlotEsCheckBox.isChecked())  
            ConfigFile.settings["bL4PlotLi"] = int(self.l4PlotLiCheckBox.isChecked())  
            ConfigFile.settings["bL4PlotLt"] = int(self.l4PlotLtCheckBox.isChecked())  
            ConfigFile.settings["bL4SaveSeaBASS"] = int(self.l4SaveSeaBASSCheckBox.isChecked())            

            QtWidgets.QMessageBox.about(self, "Save As Config File", "Config File Saved")
            ConfigFile.saveConfig(ConfigFile.filename)

            # Copy Calibration files into new Config folder
            # fnames = QtWidgets.QFileDialog.getOpenFileNames(self, "Add Calibration Files")
            fnames = ConfigFile.settings['CalibrationFiles']
            # print(fnames)

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
            # self.configComboBox.update()
            self.close()
        

    def cancelButtonPressed(self):
        print("ConfigWindow - Cancel Pressed")
        self.close()

