"""
HyperInSPACE is designed to provide Hyperspectral In situ Support for the PACE mission by processing
above-water, hyperspectral radiometry from Satlantic HyperSAS instruments.

Author: Dirk Aurin, USRA @ NASA Goddard Space Flight Center
Acknowledgements: Nathan Vanderberg (PySciDON; https://ieeexplore.ieee.org/abstract/document/8121926)

Version 1.0: Under development April 2019

"""
import os
import shutil
import sys
#from PyQt4 import QtCore, QtGui
from PyQt5 import QtCore, QtGui, QtWidgets

from Controller import Controller

from ConfigFile import ConfigFile
from ConfigWindow import ConfigWindow

""" Window is the main GUI container """
class Window(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create folders if they don't exist
        # if not os.path.exists("RawData"):
        #    os.makedirs("RawData")
        if not os.path.exists("Data"):  
           os.makedirs("Data") # These should ultimately be placed within a designated cruise directory
        if not os.path.exists("Plots"):
           os.makedirs("Plots")
        if not os.path.exists("Ascii"):
           os.makedirs("Ascii")
        if not os.path.exists("Config"):
            os.makedirs("Config")

        self.initUI()

    def initUI(self):

        """Initialize the user interface"""        

        # Configuration File
        fsm = QtWidgets.QFileSystemModel()
        index = fsm.setRootPath("Config")
        
        self.configLabel = QtWidgets.QLabel('Configuration File', self)
        #self.configLabel.move(30, 20)

        self.configComboBox = QtWidgets.QComboBox(self)
        self.configComboBox.setModel(fsm)
        fsm.setNameFilters(["*.cfg"]) # How to default to last used, or first on the list?
        # fsm.setNameFilterDisables(False) #??
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

        self.inDirLabel = QtWidgets.QLabel("Input Data Directory", self)        
        # inputDirectory = "./"
        # self.inputDirectory = "../Field_Data" # for raw data on Candiru
        self.inputDirectory = "../../Projects_Supplemental/HyperPACE/Field_Data" # for raw data on Mac
        # self.inputDirectory = "./Data"
        self.inDirButton = QtWidgets.QPushButton(self.inputDirectory,self) 
        self.inDirButton.clicked.connect(self.inDirButtonPressed)   

        self.outDirLabel = QtWidgets.QLabel("Output Data Directory", self)        
        # self.outputDirectory = "./Data"
        self.outputDirectory = "../../Projects_Supplemental/HyperPACE/Field_Data" # for raw data on Mac
        self.outDirButton = QtWidgets.QPushButton(self.outputDirectory,self) 
        self.outDirButton.clicked.connect(self.outDirButtonPressed)                
        

        self.windFileLabel = QtWidgets.QLabel("Wind Speed File (SeaBASS format)")
        self.windFileLineEdit = QtWidgets.QLineEdit()
        self.windAddButton = QtWidgets.QPushButton("Add", self)
        self.windRemoveButton = QtWidgets.QPushButton("Remove", self)                

        self.windAddButton.clicked.connect(self.windAddButtonPressed)
        self.windRemoveButton.clicked.connect(self.windRemoveButtonPressed)

        self.skyFileLabel = QtWidgets.QLabel("Sky File (SeaBASS format)")
        self.skyFileLineEdit = QtWidgets.QLineEdit()
        self.skyAddButton = QtWidgets.QPushButton("Add", self)
        self.skyRemoveButton = QtWidgets.QPushButton("Remove", self)                

        self.skyAddButton.clicked.connect(self.skyAddButtonPressed)
        self.skyRemoveButton.clicked.connect(self.skyRemoveButtonPressed)


        self.singleLevelLabel = QtWidgets.QLabel('Single-Level Processing', self)
        #self.singleLevelLabel.move(30, 270)

        self.singleL1aButton = QtWidgets.QPushButton("Raw (BIN) --> Level 1a (HDF)", self)
        #self.singleL0Button.move(30, 300)

        self.singleL1bButton = QtWidgets.QPushButton("L1A --> L1B", self)
        #self.singleL1aButton.move(30, 350)

        self.singleL2Button = QtWidgets.QPushButton("L1B --> L2", self)
        #self.singleL2Button.move(30, 450)

        self.singleL2sButton = QtWidgets.QPushButton("L2 --> L2s", self)
        #self.singleL1bButton.move(30, 400)

        self.singleL3aButton = QtWidgets.QPushButton("L2s --> L3a", self)
        #self.singleL1bButton.move(30, 400)

        self.singleL4Button = QtWidgets.QPushButton("L2s --> L4", self)
        #self.singleL1bButton.move(30, 400)
        
        self.singleL1aButton.clicked.connect(self.singleL1aClicked)
        self.singleL1bButton.clicked.connect(self.singleL1bClicked)            
        self.singleL2Button.clicked.connect(self.singleL2Clicked)
        self.singleL2sButton.clicked.connect(self.singleL2sClicked)
        self.singleL3aButton.clicked.connect(self.singleL3aClicked)
        self.singleL4Button.clicked.connect(self.singleL4Clicked)

        self.multiLevelLabel = QtWidgets.QLabel('Multi-Level Processing', self)
        #self.multiLevelLabel.move(30, 140)

        self.multi2Button = QtWidgets.QPushButton("Level 1 --> 4", self)
        #self.multi1Button.move(30, 170)

        self.multi2Button.clicked.connect(self.multi2Clicked)

        # Add QtWodgets to the Window
        vBox = QtWidgets.QVBoxLayout()
        vBox.addStretch(1)

        vBox.addWidget(self.configLabel)
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
        vBox.addStretch(1) # allows vbox to stretch open here when resized

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

        vBox.addWidget(self.skyFileLabel)        
        vBox.addWidget(self.skyFileLineEdit)

        skyHBox = QtWidgets.QHBoxLayout()        
        skyHBox.addWidget(self.skyAddButton)
        skyHBox.addWidget(self.skyRemoveButton)

        vBox.addLayout(skyHBox)
        vBox.addStretch(1)

        vBox.addWidget(self.singleLevelLabel)
        # vBox.addWidget(self.singleL0Button)
        vBox.addWidget(self.singleL1aButton)
        vBox.addWidget(self.singleL1bButton)
        vBox.addWidget(self.singleL2Button)
        vBox.addWidget(self.singleL2sButton)
        vBox.addWidget(self.singleL3aButton)
        vBox.addWidget(self.singleL4Button)

        vBox.addStretch(1)

        vBox.addWidget(self.multiLevelLabel)
        vBox.addWidget(self.multi2Button)

        vBox.addStretch(1)

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
        configPath = os.path.join("Config", configFileName)
        if os.path.isfile(configPath):
            ConfigFile.loadConfig(configFileName)
            configDialog = ConfigWindow(configFileName, self)
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
            self, "Choose Directory", 
            self.inputDirectory)
        print('Data input directory changed: ', self.inputDirectory)
        (inDirPath, inDirName) = os.path.split(self.inputDirectory)        
        self.inDirButton.setText(inDirName)
        # self.inputDirectory = inDir
        return self.inputDirectory

    def outDirButtonPressed(self):        
        self.outputDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose Directory",
            self.outputDirectory)
        print('Data output directory changed: ', self.outputDirectory)
        (dirPath, dirName) = os.path.split(self.outputDirectory)        
        self.outDirButton.setText(dirName)
        return self.outputDirectory

    def windAddButtonPressed(self):
        print("Wind File Add Dialogue")
        fnames = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Wind File")
        print(fnames)
        if len(fnames[0]) == 1:
            self.windFileLineEdit.setText(fnames[0][0])

    def windRemoveButtonPressed(self):
        print("Wind File Remove Dialogue")
        self.windFileLineEdit.setText("")

    def skyAddButtonPressed(self):
        print("Sky File Add Dialogue")
        fnames = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Sky File")
        print(fnames)
        if len(fnames[0]) == 1:
            self.skyFileLineEdit.setText(fnames[0][0])

    def skyRemoveButtonPressed(self):
        print("Sky File Remove Dialogue")
        self.skyFileLineEdit.setText("")


    # Backup files before preprocessing if source files same as output directory
    def createBackupFiles(self, fileNames):
        if len(fileNames) > 0:
            path = fileNames[0]
            (dirPath, fileName) = os.path.split(path)
            if dirPath == self.outputDirectory:
                newFileNames = []
                backupDir = os.path.join(self.outputDirectory, "Backup")
                if not os.path.exists(backupDir):
                    os.makedirs(backupDir)
                for path in fileNames:
                    (dirPath, fileName) = os.path.split(path)
                    backupPath = os.path.join(backupDir, fileName)
                    if not os.path.exists(backupPath):
                        shutil.move(path, backupPath)
                    newFileNames.append(backupPath)
                fileNames = newFileNames
        return fileNames

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

        # Select data files        
        openFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, "Open File",self.inputDirectory)
        
        print("Files:", openFileNames)
        if not openFileNames[0]:
            return
        fileNames = openFileNames[0] # The first element is the whole list

        windFile = self.windFileLineEdit.text()
        skyFile = self.skyFileLineEdit.text()

        print("Process Calibration Files")
        #calibrationMap = Controller.processCalibration(calibrationDirectory)
        filename = ConfigFile.filename
        calFiles = ConfigFile.settings["CalibrationFiles"]
        calibrationMap = Controller.processCalibrationConfig(filename, calFiles)
            
        # outputDirectory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory")
        print("Output Directory:", os.path.abspath(self.outputDirectory))

        if not self.outputDirectory[0]:
            print("Bad output directory.")
            return

        # Copy to backup folder if same directory
        # fileNames = self.createBackupFiles(fileNames)    
                
        # print("Process Raw Files")
        Controller.processFilesSingleLevel(self.outputDirectory,fileNames, calibrationMap, level, windFile, skyFile) # add sky file...........
        # Controller.processFilesSingleLevel(fileNames, calibrationMap, level, skyFile)

    # def singleL0Clicked(self):
    #     self.processSingle("0")

    def singleL1aClicked(self):
        self.processSingle("1a")

    def singleL1bClicked(self):
        self.processSingle("1b")

    def singleL2Clicked(self):
        self.processSingle("2")

    def singleL2sClicked(self):
        self.processSingle("2s")        

    def singleL3aClicked(self):
        self.processSingle("3a")   

    def singleL4Clicked(self):
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
        openFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, "Open File")
        print("Files:", openFileNames)
        if not openFileNames[0]:
            return
        fileNames = openFileNames[0]
        #calibrationDirectory = settings["sCalibrationFolder"].strip('"')
        #preprocessDirectory = settings["sPreprocessFolder"].strip('"')


        ## Select Output Directory
        # outputDirectory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory")
        print("Output Directory:", self.outputDirectory)
        if not self.outputDirectory:
            return


        # Copy to backup folder if same directory
        fileNames = self.createBackupFiles(fileNames)


        windFile = self.windFileLineEdit.text()
        skyFile = self.skyFileLineEdit.text()

        print("Process Calibration Files")
        filename = ConfigFile.filename
        calFiles = ConfigFile.settings["CalibrationFiles"]
        calibrationMap = Controller.processCalibrationConfig(filename, calFiles)
    
        Controller.processFilesMultiLevel(self.outputDirectory,fileNames, calibrationMap, level, windFile, skyFile)

    # def multi1Clicked(self):
    #     self.processMulti(1)

    def multi2Clicked(self):
        self.processMulti(2)

    # def multi3Clicked(self):
    #     self.processMulti(3)

    # def multi4Clicked(self):
    #     self.processMulti(4)


if __name__ == '__main__':
    #app = QtGui.QApplication(sys.argv)
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    sys.exit(app.exec_())
