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
import collections
import json
from PyQt5 import QtCore, QtGui, QtWidgets

from MainConfig import MainConfig
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
        """Initialize the user interface"""   

        # Main window configuration restore
        MainConfig.loadConfig(MainConfig.fileName)  
        MainConfig.settings["version"] = "1.0.b"
        # print(MainConfig.settings)   

        banner = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap('banner.jpg')
        # banner.setPixmap(pixmap.scaled(banner.size(),QtCore.Qt.IgnoreAspectRatio))
        banner.setPixmap(pixmap)
        # banner.resize(self.width(),100)        


        # Configuration File        
        configLabel = QtWidgets.QLabel('Select/Create Configuration File', self)
        configLabel_font = configLabel.font()
        configLabel_font.setPointSize(10)
        configLabel_font.setBold(True)
        configLabel.setFont(configLabel_font)
        self.fsm = QtWidgets.QFileSystemModel()        
        self.fsm.setNameFilters(["*.cfg"]) 
        self.fsm.setNameFilterDisables(False) # This activates the Filter (on Win10)
        self.fsm.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)
        self.configComboBox = QtWidgets.QComboBox(self)
        self.configComboBox.setModel(self.fsm)
        self.configComboBox.setRootModelIndex(self.fsm.setRootPath("Config"))
        self.fsm.directoryLoaded.connect(self.on_directoryLoaded)         
        self.configComboBox.currentTextChanged.connect(self.comboBox1Changed)             
        #self.configComboBox.move(30, 50)                

        self.configNewButton = QtWidgets.QPushButton("New", self)
        #self.configNewButton.move(30, 80)
        self.configEditButton = QtWidgets.QPushButton("Edit", self)
        #self.configEditButton.move(130, 80)
        self.configDeleteButton = QtWidgets.QPushButton("Delete", self)

        self.configNewButton.clicked.connect(self.configNewButtonPressed)
        self.configEditButton.clicked.connect(self.configEditButtonPressed)
        self.configDeleteButton.clicked.connect(self.configDeleteButtonPressed)

        self.inDirLabel = QtWidgets.QLabel("Input Data Parent Directory", self)        
        self.inputDirectory = MainConfig.settings["inDir"]
        self.inDirButton = QtWidgets.QPushButton(self.inputDirectory,self) 
        self.inDirButton.clicked.connect(self.inDirButtonPressed)   

        self.outDirLabel = QtWidgets.QLabel("Output Data Parent Directory", self)        
        self.outputDirectory = MainConfig.settings["outDir"]
        self.outDirButton = QtWidgets.QPushButton(self.outputDirectory,self) 
        self.outDirButton.clicked.connect(self.outDirButtonPressed)                
        

        self.windFileLabel = QtWidgets.QLabel("Ancillary Data File for L2 (SeaBASS format)")
        self.windFileLineEdit = QtWidgets.QLineEdit()
        self.windFileLineEdit.setText(str(MainConfig.settings["metFile"]))
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

        self.multi2Button = QtWidgets.QPushButton("Raw (BIN) ----->> L2 (HDF5)", self)
        #self.multi1Button.move(30, 170)

        self.multi2Button.clicked.connect(self.multi2Clicked)

        popQueryLabel = QtWidgets.QLabel('Suppress pop-up window on processing fail?', self)
        self.popQueryCheckBox = QtWidgets.QCheckBox("", self)
        if int(MainConfig.settings["popQuery"]) == 1:
            self.popQueryCheckBox.setChecked(True)

        self.popQueryCheckBoxUpdate()      

        self.popQueryCheckBox.clicked.connect(self.popQueryCheckBoxUpdate)  

        ########################################################################################
        # Add QtWidgets to the Window
        vBox = QtWidgets.QVBoxLayout()
        # vBox.addStretch(1)

        vBox.addWidget(banner)
        
        vBox.addWidget(configLabel)
        vBox.addWidget(self.configComboBox)

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
        vBox.addWidget(self.singleL1aButton)
        vBox.addWidget(self.singleL1bButton)
        vBox.addWidget(self.singleL1cButton)
        vBox.addWidget(self.singleL1dButton)
        vBox.addWidget(self.singleL1eButton)
        vBox.addWidget(self.singleL2Button)

        vBox.addStretch(1)

        vBox.addWidget(multiLevelLabel)
        vBox.addWidget(self.multi2Button)

        popQueryBox = QtWidgets.QHBoxLayout()  
        popQueryBox.addWidget(popQueryLabel)
        popQueryBox.addWidget(self.popQueryCheckBox)
        vBox.addLayout(popQueryBox)

        vBox.addStretch(1)

        self.setLayout(vBox)

        self.setGeometry(300, 300, 290, 600)
        self.setWindowTitle('HyperInSPACE')
        self.show()

    def on_directoryLoaded(self, path):
        index = self.configComboBox.findText(MainConfig.settings["cfgFile"])
        self.configComboBox.setCurrentIndex(index)

    def comboBox1Changed(self,value):
        MainConfig.settings["cfgFile"] = value
        print("MainConfig: Configuration file changed to: ", value)    

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
        # (_, inDirName) = os.path.split(self.inputDirectory)        
        self.inDirButton.setText(self.inputDirectory)
        MainConfig.settings["inDir"] = self.inputDirectory
        return self.inputDirectory

    def outDirButtonPressed(self):        
        self.outputDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "SUBDIRECTORIES FOR DATA LEVELS WILL BE CREATED HERE AUTOMATICALLY.",
            self.outputDirectory)
        print('Data output directory changed: ', self.outputDirectory)
        print("NOTE: Subdirectories for data levels will be created here")
        print("      automatically, unless they already exist.")        
        # (_, outDirName) = os.path.split(self.outputDirectory)        
        self.outDirButton.setText(self.outputDirectory)
        MainConfig.settings["outDir"] = self.outputDirectory
        return self.outputDirectory

    def windAddButtonPressed(self):
        print("Met File Add Dialogue")
        fnames = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Meteorologic Data File",self.inputDirectory)
        print(fnames)
        if len(fnames[0]) == 1:
            self.windFileLineEdit.setText(fnames[0][0])
        MainConfig.settings["metFile"] = fnames[0][0]

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
            print("Bad input parent directory.")
            return       
        
        if level == "L1A":
            inLevel = "unknown"
        if level == "L1B":
            inLevel = "L1A"
        if level == "L1C":
            inLevel = "L1B"
        if level == "L1D":
            inLevel = "L1C"
        if level == "L1E":
            inLevel = "L1D"
        if level == "L2":
            inLevel = "L1E"
        # Check for subdirectory associated with level chosen
        subInputDir = os.path.join(self.inputDirectory + '/' + inLevel + '/')
        if os.path.exists(subInputDir):
            openFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, "Open File",subInputDir)
            fileNames = openFileNames[0] # The first element is the whole list
        else:    
            openFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, "Open File",self.inputDirectory)
            fileNames = openFileNames[0] # The first element is the whole list
        
        print("Files:", openFileNames)
        if not fileNames:
            return
        

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

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            MainConfig.saveConfig(MainConfig.fileName)
        else:
            event.ignore()

    def singleL1aClicked(self):
        self.processSingle("L1A")

    def singleL1bClicked(self):
        self.processSingle("L1B")

    def singleL1cClicked(self):
        self.processSingle("L1C")

    def singleL1dClicked(self):
        self.processSingle("L1D")

    def singleL1eClicked(self):
        self.processSingle("L1E")      

    def singleL2Clicked(self):
        self.processSingle("L2")   

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


    def multi2Clicked(self):
        self.processMulti(2)

    def popQueryCheckBoxUpdate(self):
        print("Main - popQueryCheckBoxUpdate")
        MainConfig.settings["popQuery"] = int(self.popQueryCheckBox.isChecked())
        pass
        

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    sys.exit(app.exec_())
