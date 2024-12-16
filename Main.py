"""
HyperInSPACE Community Processor (HyperCP) is the successor to the
Hyperspectral In situ Support for PACE (HyperInSPACE) project. It is
designed to process above-water, hyperspectral radiometry from
Satlantic/Sea-Bird HyperSAS instruments and TriOS RAMSES instruments.
See README.md for installation instructions and processor guide.
See Changelog.md for software updates.
See HyperCP_Project_guidelines.md and HyperCP_Project_guidelines_APPENDIX.md
for collaboration guidelines and contact information.
See the Discussions tab on GitHub for software support and development
forum.
"""

import argparse
import os
import sys
import time
from PyQt5 import QtCore, QtGui, QtWidgets

from Source import PACKAGE_DIR as CODE_HOME
from Source.MainConfig import MainConfig
from Source.Controller import Controller
from Source.ConfigFile import ConfigFile
from Source.ConfigWindow import ConfigWindow
import Source.GetAnc_credentials as credentials
from Source.SeaBASSHeader import SeaBASSHeader
from Source.SeaBASSHeaderWindow import SeaBASSHeaderWindow
from Source.Utilities import Utilities

VERSION = "1.2.10"


class Window(QtWidgets.QWidget):
    """Window is the main GUI container"""

    def __init__(self, parent=None):
        self.inputDirectory = ""
        self.outputDirectory = ""
        self.ancFileDirectory = ""

        super().__init__(parent)
        # self.setStyleSheet("background-color: #e3e6e1;")

        icon_path = os.path.join(os.path.dirname(__file__), 'Data', 'Img', 'logo.ico')
        # load_icon = Image.open(icon_path)
        # render = ImageTk.PhotoImage(load_icon)  # Loads the given icon
        # app.iconphoto(False, render)

        self.setWindowIcon(QtGui.QIcon(icon_path))

        # Create - if inexistent - directories Plots, Config and Logs
        hypercpDirs = ["Plots", "Config", "Logs"]
        for directory in hypercpDirs:
            dirPath = os.path.join(CODE_HOME, directory)
            if not os.path.exists(dirPath):
                os.makedirs(dirPath)

        # Confirm that core data files are in place. Download if necessary.
        fpfZhang = os.path.join(CODE_HOME, "Data", "Zhang_rho_db.mat")
        if not os.path.exists(fpfZhang):
            Utilities.downloadZhangDB(fpfZhang)

        self.initUI()

    def initUI(self):
        """Initialize the user interface"""
        # Main window configuration restore
        MainConfig.loadConfig(
            MainConfig.fileName, VERSION
        )  # VERSION in case it has to make new
        MainConfig.settings["version"] = VERSION  # VERSION to update if necessary

        # Banner
        banner = QtWidgets.QLabel(self)
        # pixmap = QtGui.QPixmap('./Data/banner.jpg')
        # pixmap = QtGui.QPixmap('./Data/Img/with_background_530x223.png')
        pixmap = QtGui.QPixmap(
            os.path.join(CODE_HOME, "Data", "Img", "banner_530x151.png")
        )
        banner.setPixmap(pixmap)
        banner.setAlignment(QtCore.Qt.AlignCenter)

        # Configuration File section
        configLabel = QtWidgets.QLabel("Select/Create Configuration File", self)
        configLabel_font = configLabel.font()
        configLabel_font.setPointSize(10)
        configLabel_font.setBold(True)
        configLabel.setFont(configLabel_font)

        self.fsm = QtWidgets.QFileSystemModel()
        self.fsm.setNameFilters(["*.cfg"])
        self.fsm.setNameFilterDisables(False)  # This activates the Filter (on Win10)
        self.fsm.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)

        self.configComboBox = QtWidgets.QComboBox(self)
        self.configComboBox.setModel(self.fsm)
        self.configComboBox.setRootModelIndex(
            self.fsm.setRootPath(os.path.join(CODE_HOME, "Config"))
        )
        self.fsm.directoryLoaded.connect(self.on_directoryLoaded)
        self.configComboBox.currentTextChanged.connect(self.comboBox1Changed)

        self.configNewButton = QtWidgets.QPushButton("New", self)
        self.configEditButton = QtWidgets.QPushButton("Edit", self)
        self.configDeleteButton = QtWidgets.QPushButton("Delete", self)

        self.configNewButton.clicked.connect(self.configNewButtonPressed)
        self.configEditButton.clicked.connect(self.configEditButtonPressed)
        self.configDeleteButton.clicked.connect(self.configDeleteButtonPressed)

        self.inDirLabel = QtWidgets.QLabel("Input Data Parent Directory", self)
        self.inputDirectory = MainConfig.settings["inDir"]
        self.inDirButton = QtWidgets.QPushButton(self.inputDirectory, self)
        self.inDirButton.clicked.connect(self.inDirButtonPressed)

        self.outDirLabel = QtWidgets.QLabel("Output Directory", self)
        self.outputDirectory = MainConfig.settings["outDir"]
        self.outDirButton = QtWidgets.QPushButton(self.outputDirectory, self)
        self.outDirButton.clicked.connect(self.outDirButtonPressed)
        # self.outDirButton.setGeometry(200, 150, 100, 40)
        self.outDirButton.resize(50, 100)

        self.outInDirButton = QtWidgets.QPushButton("^^^ Mimic Input Dir. vvv", self)
        self.outInDirButton.clicked.connect(self.outInDirButtonPressed)

        self.ancFileLabel = QtWidgets.QLabel(
            "Ancillary Data File (SeaBASS format; MUST USE UTC)"
        )
        self.ancFileLineEdit = QtWidgets.QLineEdit()
        self.ancFileLineEdit.setText(str(MainConfig.settings["ancFile"]))
        self.ancFileDirectory = MainConfig.settings["ancFileDir"]
        self.ancAddButton = QtWidgets.QPushButton("Add", self)
        self.ancRemoveButton = QtWidgets.QPushButton("Remove", self)

        self.ancAddButton.clicked.connect(self.ancAddButtonPressed)
        self.ancRemoveButton.clicked.connect(self.ancRemoveButtonPressed)

        singleLevelLabel = QtWidgets.QLabel("Single-Level Processing", self)
        singleLevelLabel_font = singleLevelLabel.font()
        singleLevelLabel_font.setPointSize(14)
        singleLevelLabel_font.setBold(True)
        singleLevelLabel.setFont(singleLevelLabel_font)

        self.singleL1aButton = QtWidgets.QPushButton(
            "Level 0 (Raw) --> Level 1A (HDF5)", self
        )
        self.singleL1aqcButton = QtWidgets.QPushButton("L1A --> L1AQC", self)
        self.singleL1bButton = QtWidgets.QPushButton("L1AQC --> L1B", self)
        self.singleL1bqcButton = QtWidgets.QPushButton("L1B --> L1BQC", self)
        self.singleL2Button = QtWidgets.QPushButton("L1BQC --> L2", self)

        self.singleL1aButton.clicked.connect(self.singleL1aClicked)
        self.singleL1aqcButton.clicked.connect(self.singleL1aqcClicked)
        self.singleL1bButton.clicked.connect(self.singleL1bClicked)
        self.singleL1bqcButton.clicked.connect(self.singleL1bqcClicked)
        self.singleL2Button.clicked.connect(self.singleL2Clicked)

        multiLevelLabel = QtWidgets.QLabel("Multi-Level Processing", self)
        multiLevelLabel_font = multiLevelLabel.font()
        multiLevelLabel_font.setPointSize(14)
        multiLevelLabel_font.setBold(True)
        multiLevelLabel.setFont(multiLevelLabel_font)

        self.multi2Button = QtWidgets.QPushButton("Raw (BIN) ----->> L2 (HDF5)", self)

        self.multi2Button.clicked.connect(self.multi2Clicked)

        popQueryLabel = QtWidgets.QLabel(
            "Suppress pop-up window on processing fail?", self
        )
        self.popQueryCheckBox = QtWidgets.QCheckBox("", self)
        if int(MainConfig.settings["popQuery"]) == 1:
            self.popQueryCheckBox.setChecked(True)
        self.popQueryCheckBoxUpdate()
        self.popQueryCheckBox.clicked.connect(self.popQueryCheckBoxUpdate)

        ########################################################################################
        # Add QtWidgets to the Window
        ########################################################################################

        # vBox = vertical box layout
        vBox = QtWidgets.QVBoxLayout()

        vBox.addWidget(banner)
        vBox.addWidget(configLabel)
        vBox.addWidget(self.configComboBox)

        # Horizontal Box; New Edit Delete Buttons
        configHBox = QtWidgets.QHBoxLayout()
        configHBox.addWidget(self.configNewButton)
        configHBox.addWidget(self.configEditButton)
        configHBox.addWidget(self.configDeleteButton)
        vBox.addLayout(configHBox)
        # vBox.addStretch(1) # allows vBox to stretch open here when resized

        inDataHBox = QtWidgets.QHBoxLayout()
        inDataHBox.addWidget(self.inDirLabel)
        inDataHBox.addWidget(self.inDirButton)
        vBox.addLayout(inDataHBox)

        vBox.addWidget(self.outInDirButton)

        outHBox = QtWidgets.QHBoxLayout()
        outHBox.addWidget(self.outDirLabel)
        outHBox.addWidget(self.outDirButton)
        vBox.addLayout(outHBox)

        vBox.addWidget(self.ancFileLabel)
        vBox.addWidget(self.ancFileLineEdit)

        # vBox.addStretch(1)

        ancHBox = QtWidgets.QHBoxLayout()
        ancHBox.addWidget(self.ancAddButton)
        ancHBox.addWidget(self.ancRemoveButton)

        vBox.addLayout(ancHBox)

        singleHBox = QtWidgets.QHBoxLayout()
        singleHBox.addWidget(singleLevelLabel)

        singleVBox = QtWidgets.QVBoxLayout()
        singleVBox.addWidget(self.singleL1aButton)
        singleVBox.addWidget(self.singleL1aqcButton)
        singleVBox.addWidget(self.singleL1bButton)
        singleVBox.addWidget(self.singleL1bqcButton)
        singleVBox.addWidget(self.singleL2Button)

        singleHBox.addLayout(singleVBox)
        vBox.addLayout(singleHBox)

        multiHBox = QtWidgets.QHBoxLayout()
        multiHBox.addWidget(multiLevelLabel)
        multiHBox.addWidget(self.multi2Button)
        vBox.addLayout(multiHBox)

        popQueryBox = QtWidgets.QHBoxLayout()
        popQueryBox.addWidget(popQueryLabel)
        popQueryBox.addWidget(self.popQueryCheckBox)
        vBox.addLayout(popQueryBox)

        # vBox.setContentsMargins(0, 0, 0, 0)
        # vBox.addStretch(1)
        self.setLayout(vBox)

        # self.setGeometry(300, 300, 290, 600)
        self.setWindowTitle(f"HyperCP Main v{MainConfig.settings['version']}")
        # self.setFixedSize(self.sizeHint())
        self.show()

    ########################################################################################
    # Build functionality methods
    def on_directoryLoaded(self):
        index = self.configComboBox.findText(MainConfig.settings["cfgFile"])
        self.configComboBox.setCurrentIndex(index)
        # MainConfig.saveConfig(MainConfig.fileName)

    def comboBox1Changed(self, value):
        MainConfig.settings["cfgFile"] = value
        index = self.configComboBox.findText(MainConfig.settings["cfgFile"])
        self.configComboBox.setCurrentIndex(index)
        print("MainConfig: Configuration file changed to: ", value)
        # MainConfig.saveConfig(MainConfig.fileName)

    def configNewButtonPressed(self):
        print("New Config Dialogue")
        fileName, ok = QtWidgets.QInputDialog.getText(
            self, "New Config File", "Enter File Name"
        )
        if ok:
            if not fileName.endswith(".cfg"):
                fileName = fileName + ".cfg"
            fp = os.path.join(CODE_HOME, "Config", fileName)
            if os.path.exists(fp):
                ret = QtWidgets.QMessageBox.question(
                    self,
                    "File Exists",
                    "Overwrite Config File?",
                    QtWidgets.QMessageBox.Yes
                    | QtWidgets.QMessageBox.No
                    | QtWidgets.QMessageBox.Cancel,
                    QtWidgets.QMessageBox.Cancel,
                )

                if ret == QtWidgets.QMessageBox.Yes:
                    print("Overwriting Config File:", fileName)
                    ConfigFile.createDefaultConfig(fileName, 1)
                    MainConfig.settings["cfgFile"] = ConfigFile.filename
                    seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
                    print("Overwriting SeaBASSHeader File: ", seaBASSHeaderFileName)
                    SeaBASSHeader.createDefaultSeaBASSHeader(seaBASSHeaderFileName)
            else:
                print("Create New Config File: ", fileName)
                ConfigFile.createDefaultConfig(fileName, 1)
                MainConfig.settings["cfgFile"] = ConfigFile.filename
                seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
                print("Creating New SeaBASSHeader File: ", seaBASSHeaderFileName)
                SeaBASSHeader.createDefaultSeaBASSHeader(seaBASSHeaderFileName)
            MainConfig.saveConfig(MainConfig.fileName)

    def configEditButtonPressed(self):
        print("Edit Config Dialogue")

        MainConfig.saveConfig(MainConfig.fileName)

        configFileName = self.configComboBox.currentText()

        inputDir = self.inputDirectory
        configPath = os.path.join(CODE_HOME, "Config", configFileName)
        if os.path.isfile(configPath):
            ConfigFile.loadConfig(configFileName)
            configDialog = ConfigWindow(configFileName, inputDir, self)
            configDialog.show()
        else:
            message = "Not a Config File: " + configFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)

    def configDeleteButtonPressed(self):
        print("Delete Config Dialogue")
        configFileName = self.configComboBox.currentText()
        configPath = os.path.join(CODE_HOME, "Config", configFileName)
        if os.path.isfile(configPath):
            configDeleteMessage = "Delete " + configFileName + "?"

            reply = QtWidgets.QMessageBox.question(
                self,
                "Message",
                configDeleteMessage,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )

            if reply == QtWidgets.QMessageBox.Yes:
                ConfigFile.deleteConfig(configFileName)
        else:
            message = "Not a Config File: " + configFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)
        MainConfig.saveConfig(MainConfig.fileName)

    def inDirButtonPressed(self):
        temp = self.inputDirectory
        self.inputDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose Directory.", self.inputDirectory
        )
        if self.inputDirectory == "":
            self.inputDirectory = temp
        if self.inputDirectory == "":
            self.inputDirectory = os.path.join(CODE_HOME, "/Data")
        print("Data input directory changed: ", self.inputDirectory)
        self.inDirButton.setText(self.inputDirectory)
        MainConfig.settings["inDir"] = self.inputDirectory
        MainConfig.saveConfig(MainConfig.fileName)
        return self.inputDirectory

    def outDirButtonPressed(self):
        temp = self.outputDirectory
        self.outputDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "SUBDIRECTORIES FOR DATA LEVELS WILL BE CREATED HERE AUTOMATICALLY.",
            self.outputDirectory,
        )
        if self.outputDirectory == "":
            self.outputDirectory = temp
        if self.outputDirectory == "":
            self.outputDirectory = os.path.join(CODE_HOME, "Data", "Sample_Data")
        print("Data output directory changed: ", self.outputDirectory)
        print("NOTE: Subdirectories for data levels will be created here")
        print("      automatically, unless they already exist.")
        self.outDirButton.setText(self.outputDirectory)
        MainConfig.settings["outDir"] = self.outputDirectory
        MainConfig.saveConfig(MainConfig.fileName)
        return self.outputDirectory

    def outInDirButtonPressed(self):
        self.outputDirectory = self.inputDirectory
        print("Data output directory changed: ", self.outputDirectory)
        print("NOTE: Subdirectories for data levels will be created here")
        print("      automatically, unless they already exist.")
        self.outDirButton.setText(self.outputDirectory)
        MainConfig.settings["outDir"] = self.outputDirectory
        MainConfig.saveConfig(MainConfig.fileName)
        return self.outputDirectory

    def ancAddButtonPressed(self):
        print("Ancillary File Add Dialogue")
        if self.ancFileDirectory == "":
            self.ancFileDirectory = (
                self.inputDirectory
            )  # Reverts to Input directory first
            if self.ancFileDirectory == "":
                self.ancFileDirectory = os.path.join(
                    CODE_HOME, "Data", "Sample_Data"
                )  # Falls back to ./Data/Sample_Data
        fnames = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Select Ancillary Data File", self.ancFileDirectory
        )
        if any(fnames):
            print(fnames)
            if len(fnames[0]) == 1:
                self.ancFileLineEdit.setText(fnames[0][0])
            MainConfig.settings["ancFile"] = fnames[0][0]  # unclear why this sometimes does not "take" the first time
        MainConfig.saveConfig(MainConfig.fileName)

    def ancRemoveButtonPressed(self):
        print("Wind File Remove Dialogue")
        self.ancFileLineEdit.setText("")
        MainConfig.settings["ancFile"] = ""
        self.ancFileDirectory = ""
        MainConfig.saveConfig(MainConfig.fileName)

    def processSingle(self, lvl):
        print("Process Single-Level")

        t0Single = time.time()
        # Load Config file
        configFileName = self.configComboBox.currentText()
        MainConfig.settings["cfgPath"] = os.path.join(
            CODE_HOME, "Config", configFileName)
        if not os.path.isfile(MainConfig.settings["cfgPath"]):
            message = "Not valid Config File: " + configFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)
            return
        MainConfig.saveConfig(MainConfig.fileName)
        ConfigFile.loadConfig(configFileName)
        seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
        SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)

        if lvl == "L1A":
            inLevel = "raw"
        elif lvl == "L1AQC":
            inLevel = "L1A"
        elif lvl == "L1B":
            inLevel = "L1AQC"
        elif lvl == "L1BQC":
            inLevel = "L1B"
        elif lvl == "L2":
            inLevel = "L1BQC"
        else:
            inLevel = None

        # Check for subdirectory associated with level chosen
        subInputDir = os.path.join(self.inputDirectory, inLevel)
        if os.path.exists(subInputDir):
            openFileNames = QtWidgets.QFileDialog.getOpenFileNames(
                self, "Open File", subInputDir
            )
            fileNames = openFileNames[0]  # The first element is the whole list

        else:
            openFileNames = QtWidgets.QFileDialog.getOpenFileNames(
                self, "Open File", self.inputDirectory
            )
            fileNames = openFileNames[0]  # The first element is the whole list

        print("Files:", openFileNames)
        if not fileNames:
            return

        print("Process Calibration Files")
        calFiles = ConfigFile.settings["CalibrationFiles"]

        # if flag_Trios == 0:
        calibrationMap = None
        if ConfigFile.settings["SensorType"].lower() == "seabird":
            calibrationMap = Controller.processCalibrationConfig(
                configFileName, calFiles
            )
        # else:
        elif ConfigFile.settings["SensorType"].lower() == "trios":
            calibrationMap = Controller.processCalibrationConfigTrios(calFiles)

        if not calibrationMap:
            print(
                "No calibration files found. "
                "Check Config directory for your instrument files."
            )
            return

        print("Output Directory:", os.path.abspath(self.outputDirectory))
        if not self.outputDirectory[0]:
            print("Bad output directory.")
            return

        # Controller.processFilesSingleLevel(
        #     self.outputDirectory, fileNames, calibrationMap, lvl, flag_Trios
        # )
        Controller.processFilesSingleLevel(
            self.outputDirectory, fileNames, calibrationMap, lvl)
        t1Single = time.time()
        print(f"Time elapsed: {str(round((t1Single-t0Single)/60))} minutes")

    def closeEvent(self, event):
        # reply = QtWidgets.QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
        #         QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        # if reply == QtWidgets.QMessageBox.Yes:
        configFileName = self.configComboBox.currentText()
        MainConfig.settings["cfgPath"] = os.path.join(
            CODE_HOME, "Config", configFileName)
        MainConfig.saveConfig(MainConfig.fileName)
        event.accept()
        # else:
        #     event.ignore()

    def singleL1aClicked(self):
        self.processSingle("L1A")

    def singleL1aqcClicked(self):
        self.processSingle("L1AQC")

    def singleL1bClicked(self):
        self.processSingle("L1B")

    def singleL1bqcClicked(self):
        self.processSingle("L1BQC")

    def singleL2Clicked(self):
        self.processSingle("L2")

    def processMulti(self):
        print("Process Multi-Level")
        MainConfig.saveConfig(MainConfig.fileName)
        t0Multi = time.time()
        # Load Config file
        configFileName = self.configComboBox.currentText()
        configPath = os.path.join(CODE_HOME, "Config", configFileName)
        MainConfig.settings["cfgPath"] = configPath
        if not os.path.isfile(configPath):
            message = "Not valid Config File: " + configFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)
            return
        ConfigFile.loadConfig(configFileName)

        # Select data files
        if not self.inputDirectory[0]:
            print("Bad input directory.")
            return

        openFileNames = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open File", self.inputDirectory)

        print("Files:", openFileNames)

        if not openFileNames[0]:
            return
        fileNames = openFileNames[0]

        print("Output Directory:", self.outputDirectory)
        if not self.outputDirectory:
            return

        calFiles = ConfigFile.settings["CalibrationFiles"]
        # To check instrument type
        if ConfigFile.settings["SensorType"].lower() == "trios":
            calibrationMap = Controller.processCalibrationConfigTrios(calFiles)
        elif ConfigFile.settings["SensorType"].lower() == "seabird":
            print("Process Calibration Files")
            filename = ConfigFile.filename
            calibrationMap = Controller.processCalibrationConfig(filename, calFiles)
        else:
            print("Error in configuration file: Sensor type not specified")
            sys.exit()

        Controller.processFilesMultiLevel(
            self.outputDirectory, fileNames, calibrationMap)
        t1Multi = time.time()
        print(f"Time elapsed: {str(round((t1Multi-t0Multi)/60))} Minutes")

    def multi2Clicked(self):
        """Sneaky work around until I can pass signals btw. windows"""
        self.processMulti()

    def popQueryCheckBoxUpdate(self):
        print("Main - popQueryCheckBoxUpdate")
        MainConfig.settings["popQuery"] = int(self.popQueryCheckBox.isChecked())
        MainConfig.saveConfig(MainConfig.fileName)

    # def saveButtonClicked(self):
    #     print("Main - saveButtonClicked")
    #     MainConfig.saveConfig(MainConfig.fileName)


###################################################################################


class Command:
    """Class for batching without using the GUI. Scripted calls preferred, but
    direct call possible."""

    def __init__(
        self,
        configFP,
        from_level,
        iFile,
        dataDirectory,
        to_level,
        anc='',
        processMultiLevel=False,
    ):

        self.configFilename = configFP
        self.inputFile = iFile
        self.inputDirectory = os.path.join(dataDirectory, from_level)
        self.outputDirectory = dataDirectory
        self.level = to_level
        self.ancFile = anc

        super().__init__()

        # Confirm that core data files are in place. Download if necessary.
        fpfZhang = os.path.join(CODE_HOME, "Data", "Zhang_rho_db.mat")
        if not os.path.exists(fpfZhang):
            Utilities.downloadZhangDB(fpfZhang, force=True)

        # Create a default main config to be filled with cmd argument
        # to avoid reading the one generated with the GUI
        MainConfig.createDefaultConfig("cmdline_main.config", VERSION)
        MainConfig.fileName = "cmdline_main.config"

        # Update main configuration path with cmd line input
        MainConfig.settings["cfgFile"] = os.path.split(configFP)[-1]
        MainConfig.settings["cfgPath"] = configFP
        MainConfig.settings["version"] = VERSION
        MainConfig.settings["ancFile"] = self.ancFile
        MainConfig.settings["outDir"] = self.outputDirectory

        if isinstance(iFile,list):
            # Process the entire directory of the first file in the list
            MainConfig.settings["inDir"] = os.path.dirname(iFile[0])
        else:
            # Single file
            MainConfig.settings["inDir"] = os.path.dirname(iFile)
        # Now make it a list as it is expected to be
        # inputFile = [inputFile]

        # No GUI used: error message are display in prompt and not in graphical window
        MainConfig.settings["popQuery"] = 1 # 1 suppresses popup
        MainConfig.saveConfig(MainConfig.fileName)
        print("MainConfig - Config updated with cmd line arguments")

        ConfigFile.loadConfig(self.configFilename)

        calFiles = ConfigFile.settings["CalibrationFiles"]

        if ConfigFile.settings["SensorType"].lower() == "trios":
            calibrationMap = Controller.processCalibrationConfigTrios(calFiles)
        elif ConfigFile.settings["SensorType"].lower() == "seabird":
            print("Process Calibration Files")
            filename = ConfigFile.filename
            calibrationMap = Controller.processCalibrationConfig(filename, calFiles)
        else:
            print(f'CalibrationConfig is not yet ready for {ConfigFile.settings["SensorType"]}')
            sys.exit()

        # Update the SeaBASS .hdr file in case changes were made to the configuration without using the GUI
        SeaBASSHeader.loadSeaBASSHeader(ConfigFile.settings['seaBASSHeaderFileName'])
        SeaBASSHeaderWindow.configUpdateButtonPressed(self, 'config1')
        SeaBASSHeader.saveSeaBASSHeader(ConfigFile.settings['seaBASSHeaderFileName'])

        if processMultiLevel:
            if ConfigFile.settings["SensorType"].lower() == "trios" and to_level == "L1A":
                Controller.processFilesMultiLevel(
                    self.outputDirectory, iFile, calibrationMap)
            else:
                Controller.processFilesMultiLevel(
                    self.outputDirectory, [iFile], calibrationMap)
        else:
            # processSingleLevel is only prepared for a singleton file at a time
            Controller.processSingleLevel(
                self.outputDirectory, iFile, calibrationMap, to_level)


if __name__ == "__main__":
    # Arguments declaration
    ######## This section is not up to date. Scripted calls to Command are preferred. ##########
    parser = argparse.ArgumentParser(description="Arguments description")
    # Mandatory arguments
    required = parser.add_argument_group("Required arguments")
    required.add_argument(
        "-cmd",
        action="store_true",
        dest="cmd",
        help="To use for commandline mode. If not given, the GUI mode is run",
        default=None,
    )
    required.add_argument(
        "-c",
        action="store",
        dest="configFilePath",
        help="Path of the configuration file",
        default=None,
        type=str,
    )
    required.add_argument(
        "-i",
        action="store",
        dest="inputFile",
        help="Path of the input file",
        default=None,
        type=str,
    )
    required.add_argument(
        "-o",
        action="store",
        dest="outputDirectory",
        help="Path of the output folder",
        default=None,
        type=str,
    )
    required.add_argument(
        "-l",
        action="store",
        dest="level",
        help="Level of the generated file. e.g.: Computing RAW to L1A means -l L1A",
        choices=["L1A", "L1AQC", "L1B", "L1BQC", "L2"],
        default=None,
        type=str,
    )
    required.add_argument(
        "-m",
        action="store",
        dest="multiLevel",
        help="Single or multilevel processing (L0-L2): -m False",
        choices=["True", "False"],
        default="False",
        type=str,
    )
    required.add_argument(
        "-a",
        action="store",
        dest="ancFile",
        help="Path of the ancillary file",
        default=None,
        type=str,
    )

    args = parser.parse_args()

    # If the commandline option is given, check if all needed information are given
    if args.cmd and (
        args.configFilePath is None
        or args.inputFile is None
        or args.multiLevel is None
        or args.outputDirectory is None
        or args.level is None
    ):
        parser.error(
            "-cmd requires -c config -i inputFile -m multiLevel -o outputDirectory -l processingLevel"
        )
    # If the commandline option is given, check if all needed information are given
    if (
        args.cmd
        and args.level == "L1BQC"
        and (args.username is None or args.password is None)
    ):
        parser.error(
            "L1BQC processing requires username and password for https://oceancolor.gsfc.nasa.gov/"
        )

    # We store all arguments in variables
    cmd = args.cmd
    configFilePath = args.configFilePath
    inputFile = args.inputFile
    outputDirectory = args.outputDirectory
    level = args.level
    ancFile = args.ancFile
    multiLevel = args.multiLevel


    # Close splashscreen
    try:
        import platform

        if platform.system() in ["Windows", "Linux"]:
            import pyi_splash

            pyi_splash.close()
    except ImportError:
        pass

    # If the cmd argument is given, run the Command class without the GUI
    if cmd:
        os.environ["HYPERINSPACE_CMD"] = "TRUE" # Must be a string

        # Pop up credential windows if credentials not stored...
        credentials.credentialsWindow('NASA_Earth_Data')
        credentials.credentialsWindow('ECMWF_ADS')

        Command(configFilePath, inputFile, multiLevel, outputDirectory, level, ancFile)
    else:
        os.environ["HYPERINSPACE_CMD"] = "FALSE" # Must be a string

        app = QtWidgets.QApplication(sys.argv)
        win = Window()
        sys.exit(app.exec_())
