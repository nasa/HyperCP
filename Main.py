"""
HyperInSPACE is designed to provide Hyperspectral In situ Support for the PACE mission by processing
above-water, hyperspectral radiometry from Satlantic HyperSAS instruments.

See README.md or README.pdf for installation instructions and guide.

Version 1.0.b: Under development November 2019
Dirk Aurin, NASA GSFC dirk.a.aurin@nasa.gov
"""
import os
import shutil
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

from Controller import Controller
from ConfigFile import ConfigFile
from ConfigWindow import ConfigWindow
from SeaBASSHeader import SeaBASSHeader

""" Window is the main GUI container """
class Window(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create folders if they don't exist
        # if not os.path.exists("RawData"):
        #    os.makedirs("RawData")
        if not os.path.exists("Data"):  
           os.makedirs("Data") 
        if not os.path.exists("Plots"):
           os.makedirs("Plots")
        if not os.path.exists("Config"):
            os.makedirs("Config")
        if not os.path.exists("Logs"):
            os.makedirs("Logs")

        self.initUI()

    def initUI(self):

        banner = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap('banner.jpg')
        # banner.setPixmap(pixmap.scaled(banner.size(),QtCore.Qt.IgnoreAspectRatio))
        banner.setPixmap(pixmap)
        # banner.resize(self.width(),100)        

        """Initialize the user interface"""        

        # Configuration File
        fsm = QtWidgets.QFileSystemModel()
        index = fsm.setRootPath("Config")
        
        configLabel = QtWidgets.QLabel('Select/Create Configuration File', self)
        configLabel_font = configLabel.font()
        configLabel_font.setPointSize(10)
        configLabel_font.setBold(True)
        configLabel.setFont(configLabel_font)
        #configLabel.move(30, 20)

        self.configComboBox = QtWidgets.QComboBox(self)
        self.configComboBox.setModel(fsm)
        fsm.setNameFilters(["*.cfg"]) 
        fsm.setNameFilterDisables(False) # This activates the Filter (on Win10)
        fsm.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)
        self.configComboBox.setRootModelIndex(index)
        self.configComboBox.setCurrentIndex(0) # How to default to last used, or first on the list?
        # self.configComboBox.addItem("1")        
        #self.configComboBox.move(30, 50)                

        self.configNewButton = QtWidgets.QPushButton("New", self)
        #self.configNewButton.move(30, 80)
        self.configEditButton = QtWidgets.QPushButton("Edit", self)
        #self.configEditButton.move(130, 80)
        self.configDeleteButton = QtWidgets.QPushButton("Delete", self)

        self.configNewButton.clicked.connect(self.configNewButtonPressed)
        self.configEditButton.clicked.connect(self.configEditButtonPressed)
        self.configDeleteButton.clicked.connect(self.configDeleteButtonPressed)

        ''' Should create a .config file to store defaults for the Main window'''
        self.inDirLabel = QtWidgets.QLabel("Input Data Directory", self)        
        self.inputDirectory = "./Data"
        # self.inputDirectory = "../Field_Data/NOAA-ECOA_2015/hyperSAS" # for processed data on Candiru
        # self.inputDirectory = "D:/Dirk/NASA/HyperSAS/Field_Data" # for processed data on SMITHERS
        # self.inputDirectory = "../../Projects_Supplemental/HyperPACE/Field_Data" # for raw data on Mac        
        self.inDirButton = QtWidgets.QPushButton(self.inputDirectory,self) 
        self.inDirButton.clicked.connect(self.inDirButtonPressed)   

        self.outDirLabel = QtWidgets.QLabel("Output Data Directory", self)        
        self.outputDirectory = "./Data"
        # self.outputDirectory = "../Field_Data/Processed/NOAA-ECOA_2015" # for processed data on Candiru
        # self.outputDirectory = "D:/Dirk/NASA/HyperSAS/Field_Data/Processed" # for processed data on SMITHERS
        # self.outputDirectory = "../../Projects_Supplemental/HyperPACE/Field_Data" # for raw data on Mac
        self.outDirButton = QtWidgets.QPushButton(self.outputDirectory,self) 
        self.outDirButton.clicked.connect(self.outDirButtonPressed)                
        

        self.windFileLabel = QtWidgets.QLabel("Meteorologic File for L2 (SeaBASS format)")
        self.windFileLineEdit = QtWidgets.QLineEdit()
        self.windAddButton = QtWidgets.QPushButton("Add", self)
        self.windRemoveButton = QtWidgets.QPushButton("Remove", self)                

        self.windAddButton.clicked.connect(self.windAddButtonPressed)
        self.windRemoveButton.clicked.connect(self.windRemoveButtonPressed)


        singleLevelLabel = QtWidgets.QLabel('Single-Level Processing', self)
        singleLevelLabel_font = singleLevelLabel.font()
        singleLevelLabel_font.setPointSize(10)
        singleLevelLabel_font.setBold(True)
        singleLevelLabel.setFont(singleLevelLabel_font)
        #self.singleLevelLabel.move(30, 270)

        self.singleL1aButton = QtWidgets.QPushButton("Raw (BIN) --> Level 1A (HDF5)", self)
        #self.singleL0Button.move(30, 300)

        self.singleL1bButton = QtWidgets.QPushButton("L1A --> L1B", self)
        #self.singleL1aButton.move(30, 350)

        self.singleL1cButton = QtWidgets.QPushButton("L1B --> L1C", self)
        #self.singleL1cButton.move(30, 450)

        self.singleL1dButton = QtWidgets.QPushButton("L1C --> L1D", self)
        #self.singleL1bButton.move(30, 400)

        self.singleL1eButton = QtWidgets.QPushButton("L1D --> L1E", self)
        #self.singleL1bButton.move(30, 400)

        self.singleL2Button = QtWidgets.QPushButton("L1E --> L2", self)
        #self.singleL1bButton.move(30, 400)
        
        self.singleL1aButton.clicked.connect(self.singleL1aClicked)
        self.singleL1bButton.clicked.connect(self.singleL1bClicked)            
        self.singleL1cButton.clicked.connect(self.singleL1cClicked)
        self.singleL1dButton.clicked.connect(self.singleL1dClicked)
        self.singleL1eButton.clicked.connect(self.singleL1eClicked)
        self.singleL2Button.clicked.connect(self.singleL2Clicked)

        multiLevelLabel = QtWidgets.QLabel('Multi-Level Processing', self)
        multiLevelLabel_font = multiLevelLabel.font()
        multiLevelLabel_font.setPointSize(10)
        multiLevelLabel_font.setBold(True)
        multiLevelLabel.setFont(multiLevelLabel_font)
        #self.multiLevelLabel.move(30, 140)

        self.multi4Button = QtWidgets.QPushButton("Raw (BIN) ----->> L2 (HDF5)", self)
        #self.multi1Button.move(30, 170)

        self.multi4Button.clicked.connect(self.multi4Clicked)

        ########################################################################################
        # Add QtWidgets to the Window
        vBox = QtWidgets.QVBoxLayout()
        # vBox.addStretch(1)

        vBox.addWidget(banner)

        # vBox1 = QtWidgets.QVBoxLayout()
        vBox.addWidget(configLabel)
        vBox.addWidget(self.configComboBox)
        # print("index: ", self.configComboBox.currentIndex())
        # print("text: ", self.configComboBox.currentText())        
        # index = self.configComboBox.findText("*.cfg",QtCore.Qt.MatchFixedString)

        # Horizontal Box; New Edit Delete Buttons
        configHBox = QtWidgets.QHBoxLayout()
        configHBox.addWidget(self.configNewButton)
        configHBox.addWidget(self.configEditButton)
        configHBox.addWidget(self.configDeleteButton)
        vBox.addLayout(configHBox) 
        vBox.addStretch(1) # allows vBox to stretch open here when resized

        vBox.addWidget(self.inDirLabel)
        vBox.addWidget(self.inDirButton)

        vBox.addWidget(self.outDirLabel)
        vBox.addWidget(self.outDirButton)

        vBox.addSpacing(10)

        vBox.addWidget(self.windFileLabel)        
        vBox.addWidget(self.windFileLineEdit)

        windHBox = QtWidgets.QHBoxLayout()        
        windHBox.addWidget(self.windAddButton)
        windHBox.addWidget(self.windRemoveButton)

        vBox.addLayout(windHBox)
        vBox.addStretch(1)

        vBox.addStretch(1)

        vBox.addWidget(singleLevelLabel)
        # vBox.addWidget(self.singleL0Button)
        vBox.addWidget(self.singleL1aButton)
        vBox.addWidget(self.singleL1bButton)
        vBox.addWidget(self.singleL1cButton)
        vBox.addWidget(self.singleL1dButton)
        vBox.addWidget(self.singleL1eButton)
        vBox.addWidget(self.singleL2Button)

        vBox.addStretch(1)

        vBox.addWidget(multiLevelLabel)
        vBox.addWidget(self.multi4Button)

        vBox.addStretch(1)

        # vBox.addLayout(vBox1)
        self.setLayout(vBox)

        self.setGeometry(300, 300, 290, 600)
        self.setWindowTitle('HyperInSPACE')
        self.show()


    def configNewButtonPressed(self):
        print("New Config Dialogue")
        text, ok = QtWidgets.QInputDialog.getText(self, 'New Config File', 'Enter File Name')
        if ok:
            print("Create Config File: ", text)
            ConfigFile.createDefaultConfig(text)
            # ToDo: Add code to change text for the combobox once file is created            


    def configEditButtonPressed(self):
        print("Edit Config Dialogue")
        # print("index: ", self.configComboBox.currentIndex())
        # print("text: ", self.configComboBox.currentText())
        configFileName = self.configComboBox.currentText()
        inputDir = self.inputDirectory
        configPath = os.path.join("Config", configFileName)
        if os.path.isfile(configPath):
            ConfigFile.loadConfig(configFileName)
            configDialog = ConfigWindow(configFileName, inputDir, self)
            #configDialog = CalibrationEditWindow(configFileName, self)
            configDialog.show()
        else:
            #print("Not a Config File: " + configFileName)
            message = "Not a Config File: " + configFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)


    def configDeleteButtonPressed(self):
        print("Delete Config Dialogue")
        # print("index: ", self.configComboBox.currentIndex())
        # print("text: ", self.configComboBox.currentText())
        configFileName = self.configComboBox.currentText()
        configPath = os.path.join("Config", configFileName)
        if os.path.isfile(configPath):
            configDeleteMessage = "Delete " + configFileName + "?"

            reply = QtWidgets.QMessageBox.question(self, 'Message', configDeleteMessage, \
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                ConfigFile.deleteConfig(configFileName)
        else:
            #print("Not a Config File: " + configFileName)
            message = "Not a Config File: " + configFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)

    def inDirButtonPressed(self):        
        self.inputDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose Directory.", 
            self.inputDirectory)
        print('Data input directory changed: ', self.inputDirectory)
        (_, inDirName) = os.path.split(self.inputDirectory)        
        self.inDirButton.setText(inDirName)
        # self.inputDirectory = inDir
        return self.inputDirectory

    def outDirButtonPressed(self):        
        self.outputDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "SUBDIRECTORIES FOR DATA LEVELS WILL BE CREATED HERE AUTOMATICALLY.",
            self.outputDirectory)
        print('Data output directory changed: ', self.outputDirectory)
        print("NOTE: Subdirectories for data levels will be created here")
        print("      automatically, unless they already exist.")        
        (_, dirName) = os.path.split(self.outputDirectory)        
        self.outDirButton.setText(dirName)
        return self.outputDirectory

    def windAddButtonPressed(self):
        print("Wind File Add Dialogue")
        fnames = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Wind File",self.inputDirectory)
        print(fnames)
        if len(fnames[0]) == 1:
            self.windFileLineEdit.setText(fnames[0][0])

    def windRemoveButtonPressed(self):
        print("Wind File Remove Dialogue")
        self.windFileLineEdit.setText("")

    def processSingle(self, level):
        print("Process Single-Level")

        # Load Config file
        configFileName = self.configComboBox.currentText()
        configPath = os.path.join("Config", configFileName)
        if not os.path.isfile(configPath):
            message = "Not valid Config File: " + configFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)
            return
        ConfigFile.loadConfig(configFileName)
        seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
        SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)

        # Select data files    
        if not self.inputDirectory[0]:
            print("Bad input directory.")
            return                
        openFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, "Open File",self.inputDirectory)
        
        print("Files:", openFileNames)
        if not openFileNames[0]:
            return
        fileNames = openFileNames[0] # The first element is the whole list

        windFile = self.windFileLineEdit.text()
        if windFile == '':
            windFile = None

        print("Process Calibration Files")
        filename = ConfigFile.filename
        calFiles = ConfigFile.settings["CalibrationFiles"]
        calibrationMap = Controller.processCalibrationConfig(filename, calFiles)
        if not calibrationMap.keys():
            print("No calibration files found. "
            "Check Config directory for your instrument files.")
            return            
            
        # outputDirectory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory")
        print("Output Directory:", os.path.abspath(self.outputDirectory))
        if not self.outputDirectory[0]:
            print("Bad output directory.")
            return            

        Controller.processFilesSingleLevel(self.outputDirectory,fileNames, calibrationMap, level, windFile) 

    def singleL1aClicked(self):
        self.processSingle("1a")

    def singleL1bClicked(self):
        self.processSingle("1b")

    def singleL1cClicked(self):
        self.processSingle("1c")

    def singleL1dClicked(self):
        self.processSingle("1d")

    def singleL1eClicked(self):
        self.processSingle("1e")      

    def singleL2Clicked(self):
        self.processSingle("4")   

    def processMulti(self, level):
        print("Process Multi-Level")

        # Load Config file
        configFileName = self.configComboBox.currentText()
        configPath = os.path.join("Config", configFileName)
        if not os.path.isfile(configPath):
            message = "Not valid Config File: " + configFileName
            QtWidgets.QMessageBox.critical(self, "Error", message)
            return
        ConfigFile.loadConfig(configFileName)

        # Select data files    
        if not self.inputDirectory[0]:
            print("Bad input directory.")
            return                
        openFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, "Open File",self.inputDirectory)

        print("Files:", openFileNames)
        
        if not openFileNames[0]:
            return
        fileNames = openFileNames[0]

        ## Select Output Directory
        # outputDirectory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory")
        print("Output Directory:", self.outputDirectory)
        if not self.outputDirectory:
            return

        windFile = self.windFileLineEdit.text()

        print("Process Calibration Files")
        filename = ConfigFile.filename
        calFiles = ConfigFile.settings["CalibrationFiles"]
        calibrationMap = Controller.processCalibrationConfig(filename, calFiles)
    
        Controller.processFilesMultiLevel(self.outputDirectory,fileNames, calibrationMap, windFile)


    def multi4Clicked(self):
        self.processMulti(4)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    sys.exit(app.exec_())
