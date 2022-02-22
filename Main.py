"""
HyperInSPACE is designed to provide Hyperspectral In situ Support for the PACE mission by processing
above-water, hyperspectral radiometry from Satlantic HyperSAS instruments.
See README.md or README.pdf for installation instructions and guide.
Version 1.0.9: Under development September 2021 (See Changelog.md)
Dirk Aurin, NASA GSFC dirk.a.aurin@nasa.gov
"""
# from Source.Utilities import Utilities
import argparse
import os
import shutil
import sys
import collections
import json
from PyQt5 import QtCore, QtGui, QtWidgets
import time
import requests
from tqdm import tqdm

# Why does pylint have a problem with this path formulation?
sys.path.append(os.path.join(os.path.dirname(__file__),'Source'))
from MainConfig import MainConfig
from Controller import Controller
from ConfigFile import ConfigFile
from ConfigWindow import ConfigWindow
from GetAnc import GetAnc
from SeaBASSHeader import SeaBASSHeader
from Utilities import Utilities

""" Window is the main GUI container """
class Window(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        if not os.path.exists('Plots'):
            os.makedirs('Plots')
        if not os.path.exists('Config'):
            os.makedirs('Config')
        if not os.path.exists('Logs'):
            os.makedirs('Logs')

        # Confirm that core data files are in place. Download if necessary.
        if not os.path.exists(os.path.join('Data','Zhang_rho_db.mat')):
            infoText = '  NEW INSTALLATION\nGlint database required.\nClick OK to download.\n\nWARNING: THIS IS A 2.5 GB DOWNLOAD.\n\n\
            If canceled, Zhang et al. (2017) glint correction will fail. If download fails, a link and instructions will be provided in the terminal.'
            YNReply = Utilities.YNWindow('Database Download',infoText)
            if YNReply == QtWidgets.QMessageBox.Ok:

                url = 'https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Zhang_rho_db.mat'
                download_session=requests.Session()
                local_filename = os.path.join('Data','Zhang_rho_db.mat')
                try:
                        file_size=int(download_session.head(url).headers["Content-length"])
                        file_size_read=round(int(file_size)/(1024**3),2)
                        print(f"##### Downloading {file_size_read}GB data file. This could take several minutes. ##### ")
                        download_file=download_session.get(url, stream=True)
                        download_file.raise_for_status()
                except requests.exceptions.HTTPError as err:
                                    print('Error in download_file:',err)
                if download_file.ok:
                        progress_bar = tqdm(total=file_size, unit='iB', unit_scale=True, unit_divisor=1024)
                        with open(local_filename, 'wb') as f:
                            for chunk in download_file.iter_content(chunk_size=1024):
                                progress_bar.update(len(chunk))
                                f.write(chunk)
                        progress_bar.close()
                else:
                    print('Failed to download core databases.')
                    print('Download from: \
                                             https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Zhang_rho_db.mat \
                                                      and place in HyperInSPACE/Data directory.')

        self.initUI()

    def initUI(self):
        """Initialize the user interface"""

        # Main window configuration restore
        MainConfig.loadConfig(MainConfig.fileName)
        MainConfig.settings['version'] = '1.0.9'

        banner = QtWidgets.QLabel(self)
        # pixmap = QtGui.QPixmap('./Data/banner.jpg')
        pixmap = QtGui.QPixmap('./Data/banner2.png')
        banner.setPixmap(pixmap)
        banner.setAlignment(QtCore.Qt.AlignCenter)

        # Configuration File
        configLabel = QtWidgets.QLabel('Select/Create Configuration File', self)
        configLabel_font = configLabel.font()
        configLabel_font.setPointSize(10)
        configLabel_font.setBold(True)
        configLabel.setFont(configLabel_font)
        self.fsm = QtWidgets.QFileSystemModel()
        self.fsm.setNameFilters(['*.cfg'])
        self.fsm.setNameFilterDisables(False) # This activates the Filter (on Win10)
        self.fsm.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)
        self.configComboBox = QtWidgets.QComboBox(self)
        self.configComboBox.setModel(self.fsm)
        self.configComboBox.setRootModelIndex(self.fsm.setRootPath('Config'))
        self.fsm.directoryLoaded.connect(self.on_directoryLoaded)
        self.configComboBox.currentTextChanged.connect(self.comboBox1Changed)
        #self.configComboBox.move(30, 50)

        self.configNewButton = QtWidgets.QPushButton('New', self)
        #self.configNewButton.move(30, 80)
        self.configEditButton = QtWidgets.QPushButton('Edit', self)
        #self.configEditButton.move(130, 80)
        self.configDeleteButton = QtWidgets.QPushButton('Delete', self)

        self.configNewButton.clicked.connect(self.configNewButtonPressed)
        self.configEditButton.clicked.connect(self.configEditButtonPressed)
        self.configDeleteButton.clicked.connect(self.configDeleteButtonPressed)

        self.inDirLabel = QtWidgets.QLabel('Input Data Parent Directory', self)
        self.inputDirectory = MainConfig.settings['inDir']
        self.inDirButton = QtWidgets.QPushButton(self.inputDirectory,self)
        self.inDirButton.clicked.connect(self.inDirButtonPressed)

        self.outDirLabel = QtWidgets.QLabel('Output Data/Plots Parent Directory', self)
        self.outputDirectory = MainConfig.settings['outDir']
        self.outDirButton = QtWidgets.QPushButton(self.outputDirectory,self)
        self.outDirButton.clicked.connect(self.outDirButtonPressed)

        self.outInDirButton = QtWidgets.QPushButton('^^^ Mimic Input Dir. vvv',self)
        self.outInDirButton.clicked.connect(self.outInDirButtonPressed)

        self.ancFileLabel = QtWidgets.QLabel('Ancillary Data File for L2 (SeaBASS format)')
        self.ancFileLineEdit = QtWidgets.QLineEdit()
        self.ancFileLineEdit.setText(str(MainConfig.settings['metFile']))
        self.ancAddButton = QtWidgets.QPushButton('Add', self)
        self.ancRemoveButton = QtWidgets.QPushButton('Remove', self)

        self.ancAddButton.clicked.connect(self.ancAddButtonPressed)
        self.ancRemoveButton.clicked.connect(self.ancRemoveButtonPressed)


        singleLevelLabel = QtWidgets.QLabel('Single-Level Processing', self)
        singleLevelLabel_font = singleLevelLabel.font()
        singleLevelLabel_font.setPointSize(10)
        singleLevelLabel_font.setBold(True)
        singleLevelLabel.setFont(singleLevelLabel_font)
        #self.singleLevelLabel.move(30, 270)

        self.singleL1aButton = QtWidgets.QPushButton('Raw (BIN) --> Level 1A (HDF5)', self)
        #self.singleL0Button.move(30, 300)
        self.singleL1bButton = QtWidgets.QPushButton('L1A --> L1B', self)
        #self.singleL1aButton.move(30, 350)
        self.singleL1cButton = QtWidgets.QPushButton('L1B --> L1C', self)
        #self.singleL1cButton.move(30, 450)
        self.singleL1dButton = QtWidgets.QPushButton('L1C --> L1D', self)
        #self.singleL1bButton.move(30, 400)
        self.singleL1eButton = QtWidgets.QPushButton('L1D --> L1E', self)
        #self.singleL1bButton.move(30, 400)
        self.singleL2Button = QtWidgets.QPushButton('L1E --> L2', self)
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

        self.multi2Button = QtWidgets.QPushButton('Raw (BIN) ----->> L2 (HDF5)', self)
        #self.multi1Button.move(30, 170)

        self.multi2Button.clicked.connect(self.multi2Clicked)

        popQueryLabel = QtWidgets.QLabel('Suppress pop-up window on processing fail?', self)
        self.popQueryCheckBox = QtWidgets.QCheckBox('', self)
        if int(MainConfig.settings['popQuery']) == 1:
            self.popQueryCheckBox.setChecked(True)
        self.popQueryCheckBoxUpdate()
        self.popQueryCheckBox.clicked.connect(self.popQueryCheckBoxUpdate)

        saveLabel = QtWidgets.QLabel('(Automatic on Window Close -->)')
        self.saveButton = QtWidgets.QPushButton('Save Settings', self)
        self.saveButton.clicked.connect(self.saveButtonClicked)

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

        outHBox = QtWidgets.QHBoxLayout()
        outHBox.addWidget(self.outDirLabel)
        outHBox.addWidget(self.outInDirButton)
        vBox.addLayout(outHBox)
        vBox.addWidget(self.outDirButton)

        vBox.addSpacing(10)

        vBox.addWidget(self.ancFileLabel)
        vBox.addWidget(self.ancFileLineEdit)

        ancHBox = QtWidgets.QHBoxLayout()
        ancHBox.addWidget(self.ancAddButton)
        ancHBox.addWidget(self.ancRemoveButton)

        vBox.addLayout(ancHBox)
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

        saveQueryBox = QtWidgets.QHBoxLayout()
        saveQueryBox.addWidget(saveLabel)
        saveQueryBox.addWidget(self.saveButton)
        vBox.addLayout(saveQueryBox)

        vBox.addStretch(1)

        self.setLayout(vBox)

        self.setGeometry(300, 300, 290, 600)
        # self.setGeometry(300, 300, 250, 600) This does nothing.
        self.setWindowTitle(f"Main v{MainConfig.settings['version']}")
        self.show()

    ########################################################################################
    # Build functionality modules
    def on_directoryLoaded(self, path):
        index = self.configComboBox.findText(MainConfig.settings['cfgFile'])
        self.configComboBox.setCurrentIndex(index)

    def comboBox1Changed(self,value):
        MainConfig.settings['cfgFile'] = value
        index = self.configComboBox.findText(MainConfig.settings['cfgFile'])
        self.configComboBox.setCurrentIndex(index)
        print('MainConfig: Configuration file changed to: ', value)

    def configNewButtonPressed(self):
        print('New Config Dialogue')
        text, ok = QtWidgets.QInputDialog.getText(self, 'New Config File', 'Enter File Name')
        if ok:
            print('Create Config File: ', text)
            ConfigFile.createDefaultConfig(text, 1)
            MainConfig.settings['cfgFile'] = ConfigFile.filename
            seaBASSHeaderFileName = ConfigFile.settings['seaBASSHeaderFileName']
            print('Creating New SeaBASSHeader File: ', seaBASSHeaderFileName)
            SeaBASSHeader.createDefaultSeaBASSHeader(seaBASSHeaderFileName)
            # SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)

    def configEditButtonPressed(self):
        print('Edit Config Dialogue')
        configFileName = self.configComboBox.currentText()
        inputDir = self.inputDirectory
        configPath = os.path.join('Config', configFileName)
        if os.path.isfile(configPath):
            ConfigFile.loadConfig(configFileName)
            configDialog = ConfigWindow(configFileName, inputDir, self)
            configDialog.show()
        else:
            message = 'Not a Config File: ' + configFileName
            QtWidgets.QMessageBox.critical(self, 'Error', message)

    def configDeleteButtonPressed(self):
        print('Delete Config Dialogue')
        configFileName = self.configComboBox.currentText()
        configPath = os.path.join('Config', configFileName)
        if os.path.isfile(configPath):
            configDeleteMessage = 'Delete ' + configFileName + '?'

            reply = QtWidgets.QMessageBox.question(self, 'Message', configDeleteMessage, \
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                ConfigFile.deleteConfig(configFileName)
        else:
            message = 'Not a Config File: ' + configFileName
            QtWidgets.QMessageBox.critical(self, 'Error', message)

    def inDirButtonPressed(self):
        temp = self.inputDirectory
        self.inputDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Choose Directory.',
            self.inputDirectory)
        if self.inputDirectory == '':
            self.inputDirectory = temp
        if self.inputDirectory == '':
            self.inputDirectory = './Data'
        print('Data input directory changed: ', self.inputDirectory)
        self.inDirButton.setText(self.inputDirectory)
        MainConfig.settings['inDir'] = self.inputDirectory
        return self.inputDirectory

    def outDirButtonPressed(self):
        temp = self.outputDirectory
        self.outputDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'SUBDIRECTORIES FOR DATA LEVELS WILL BE CREATED HERE AUTOMATICALLY.',
            self.outputDirectory)
        if self.outputDirectory == '':
            self.outputDirectory = temp
        if self.outputDirectory == '':
            self.outputDirectory = './Data'
        print('Data output directory changed: ', self.outputDirectory)
        print('NOTE: Subdirectories for data levels will be created here')
        print('      automatically, unless they already exist.')
        self.outDirButton.setText(self.outputDirectory)
        MainConfig.settings['outDir'] = self.outputDirectory
        return self.outputDirectory

    def outInDirButtonPressed(self):
        self.outputDirectory = self.inputDirectory
        print('Data output directory changed: ', self.outputDirectory)
        print('NOTE: Subdirectories for data levels will be created here')
        print('      automatically, unless they already exist.')
        self.outDirButton.setText(self.outputDirectory)
        MainConfig.settings['outDir'] = self.outputDirectory
        return self.outputDirectory

    def ancAddButtonPressed(self):
        print('Met File Add Dialogue')
        fnames = QtWidgets.QFileDialog.getOpenFileNames(self, 'Select Meteorologic Data File',self.inputDirectory)
        if any(fnames):
            print(fnames)
            if len(fnames[0]) == 1:
                self.ancFileLineEdit.setText(fnames[0][0])
            MainConfig.settings['metFile'] = fnames[0][0]

    def ancRemoveButtonPressed(self):
        print('Wind File Remove Dialogue')
        self.ancFileLineEdit.setText('')
        MainConfig.settings['metFile'] = ''

    def processSingle(self, level):
        print('Process Single-Level')
        t0Single=time.time()
        # Load Config file
        configFileName = self.configComboBox.currentText()
        configPath = os.path.join('Config', configFileName)
        if not os.path.isfile(configPath):
            message = 'Not valid Config File: ' + configFileName
            QtWidgets.QMessageBox.critical(self, 'Error', message)
            return
        ConfigFile.loadConfig(configFileName)
        seaBASSHeaderFileName = ConfigFile.settings['seaBASSHeaderFileName']
        SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)

        # Select data files
        if not self.inputDirectory[0]:
            print('Bad input parent directory.')
            return

        if level == 'L1A':
            inLevel = 'unknown'
        if level == 'L1B':
            inLevel = 'L1A'
        if level == 'L1C':
            inLevel = 'L1B'
        if level == 'L1D':
            inLevel = 'L1C'
        if level == 'L1E':
            inLevel = 'L1D'
        if level == 'L2':
            inLevel = 'L1E'
        # Check for subdirectory associated with level chosen
        subInputDir = os.path.join(self.inputDirectory + '/' + inLevel + '/')
        if os.path.exists(subInputDir):
            openFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open File',subInputDir)
            fileNames = openFileNames[0] # The first element is the whole list

        else:
            openFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open File',self.inputDirectory)
            fileNames = openFileNames[0] # The first element is the whole list

        print('Files:', openFileNames)
        if not fileNames:
            return

        ancFile = self.ancFileLineEdit.text()
        if ancFile == '':
            ancFile = None

        print('Process Calibration Files')
        filename = ConfigFile.filename
        calFiles = ConfigFile.settings['CalibrationFiles']
        print('JMR', filename, calFiles) # JMR?
        calibrationMap = Controller.processCalibrationConfig(filename, calFiles)
        if not calibrationMap.keys():
            print('No calibration files found. '
            'Check Config directory for your instrument files.')
            return

        print('Output Directory:', os.path.abspath(self.outputDirectory))
        if not self.outputDirectory[0]:
            print('Bad output directory.')
            return

        Controller.processFilesSingleLevel(self.outputDirectory,fileNames, calibrationMap, level, ancFile)
        t1Single = time.time()
        print(f'Time elapsed: {str(round((t1Single-t0Single)/60))} minutes')

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            MainConfig.saveConfig(MainConfig.fileName)
            event.accept()
        else:
            event.ignore()

    def singleL1aClicked(self):
        self.processSingle('L1A')

    def singleL1bClicked(self):
        self.processSingle('L1B')

    def singleL1cClicked(self):
        self.processSingle('L1C')

    def singleL1dClicked(self):
        self.processSingle('L1D')

    def singleL1eClicked(self):
        self.processSingle('L1E')

    def singleL2Clicked(self):
        self.processSingle('L2')

    def processMulti(self, level):
        print('Process Multi-Level')
        t0Multi = time.time()
        # Load Config file
        configFileName = self.configComboBox.currentText()
        configPath = os.path.join('Config', configFileName)
        if not os.path.isfile(configPath):
            message = 'Not valid Config File: ' + configFileName
            QtWidgets.QMessageBox.critical(self, 'Error', message)
            return
        ConfigFile.loadConfig(configFileName)

        # Select data files
        if not self.inputDirectory[0]:
            print('Bad input directory.')
            return

        openFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open File',self.inputDirectory)

        print('Files:', openFileNames)

        if not openFileNames[0]:
            return
        fileNames = openFileNames[0]

        print('Output Directory:', self.outputDirectory)
        if not self.outputDirectory:
            return

        ancFile = self.ancFileLineEdit.text()

        print('Process Calibration Files')
        filename = ConfigFile.filename
        calFiles = ConfigFile.settings['CalibrationFiles']
        calibrationMap = Controller.processCalibrationConfig(filename, calFiles)

        Controller.processFilesMultiLevel(self.outputDirectory,fileNames, calibrationMap, ancFile)
        t1Multi = time.time()
        print(f'Time elapsed: {str(round((t1Multi-t0Multi)/60))} Minutes')

    def multi2Clicked(self):
        ''' Sneaky work around until I can pass signals btw. windows'''
        self.processMulti(2)

    def popQueryCheckBoxUpdate(self):
        print('Main - popQueryCheckBoxUpdate')
        MainConfig.settings['popQuery'] = int(self.popQueryCheckBox.isChecked())
        pass

    def saveButtonClicked(self):
        print('Main - saveButtonClicked')
        MainConfig.saveConfig(MainConfig.fileName)


""" Class without using the GUI """
class Command():

    def __init__(self, configFilePath, inputFile, outputDirectory, level, ancFile):

        # Configuration File
        self.configFilename = configFilePath
        # Input File
        self.inputFile = inputFile
        # Output Directory
        self.outputDirectory = outputDirectory
        # Processing Level
        self.level = level
        # Ancillary File
        self.ancFile = ancFile

        super().__init__()

        # Confirm that core data files are in place. Download if necessary.
        if not os.path.exists(os.path.join('Data','Zhang_rho_db.mat')):
            print('##### Downloading 2.5 GB data file. This could take several minutes. #####')
            print('#####        Program will open when download is complete.            #####')
            url = 'https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Zhang_rho_db.mat'
            local_filename = os.path.join('Data','Zhang_rho_db.mat')
            try:
                r = requests.get(url, stream=True)
                r.raise_for_status()

            except requests.exceptions.HTTPError as err:
                print('Error in download_file:',err)

            if r.ok:
                with open(local_filename, 'wb') as f:
                    n = 0
                    for chunk in r.iter_content(chunk_size=1024):
                        n += 1
                        if (n % 1000) == 0:
                            print('.', end='')
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                    print(' done.')
            else:
                print('Failed to download core databases.')
                print('Download from: \
                                https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Zhang_rho_db.mat \
                                    and place in HyperInSPACE/Data directory.')
        # Main configuration restore
        MainConfig.loadConfig(MainConfig.fileName)
        MainConfig.settings['version'] = '1.0.9'

        # For our need, we only use a single processing
        self.processSingle(self.level)


    ########################################################################################

    def processSingle(self, level):
        print('Process Single-Level')
        t0Single=time.time()
        # Load Config file
        configFileName = self.configFilename
        configPath = os.path.join('Config', configFileName)
        if not os.path.isfile(configPath):
            message = 'Not valid Config File: ' + configFileName
            return
        ConfigFile.loadConfig(configFileName)
        seaBASSHeaderFileName = ConfigFile.settings['seaBASSHeaderFileName']
        SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)

        if level == 'L1A':
            inLevel = 'unknown'
        if level == 'L1B':
            inLevel = 'L1A'
        if level == 'L1C':
            inLevel = 'L1B'
        if level == 'L1D':
            inLevel = 'L1C'
        if level == 'L1E':
            inLevel = 'L1D'
        if level == 'L2':
            inLevel = 'L1E'

        # Only one file is given in argument (inputFile) but to keep the same use of the Controller function,
        # we keep variable fileNames which is an array
        fileNames = [inputFile]
        print('Files:', fileNames)
        if not fileNames:
            return

        print('Process Calibration Files')
        filename = ConfigFile.filename
        calFiles = ConfigFile.settings['CalibrationFiles']
        calibrationMap = Controller.processCalibrationConfig(filename, calFiles)
        if not calibrationMap.keys():
            print('No calibration files found. '
            'Check Config directory for your instrument files.')
            return

        print('Output Directory:', os.path.abspath(self.outputDirectory))
        if not self.outputDirectory[0]:
            print('Bad output directory.')
            return

        Controller.processFilesSingleLevel(self.outputDirectory, fileNames, calibrationMap, level, self.ancFile)
        t1Single = time.time()
        print(f'Time elapsed: {str(round((t1Single-t0Single)/60))} minutes')


# Arguments declaration
parser = argparse.ArgumentParser(description='Arguments description')
# Mandatory arguments
required = parser.add_argument_group('Required arguments')
required.add_argument('-cmd',
                    action="store_true",
                    dest="cmd",
                    help='To use for commandline mode. If not given, the GUI mode is run',
                    default=None
                    )
required.add_argument('-c',
                    action="store",
                    dest="configFilePath",
                    help='Path of the configuration file',
                    default=None,
                    type=str)
required.add_argument('-i',
                    action="store",
                    dest="inputFile",
                    help='Path of the input file',
                    default=None,
                    type=str)
required.add_argument('-o',
                    action="store",
                    dest="outputDirectory",
                    help='Path of the output folder',
                    default=None,
                    type=str)
required.add_argument('-l',
                    action="store",
                    dest="level",
                    help='Level of the generated file. e.g.: Computing RAW to L1A means -l L1A',
                    choices=['L1A', 'L1B', 'L1C', 'L1D', 'L1E', 'L2'],
                    default=None,
                    type=str)
required.add_argument('-a',
                    action="store",
                    dest="ancFile",
                    help='Path of the ancillary file',
                    default=None,
                    type=str)
required.add_argument('-u',
                    action="store",
                    dest="username",
                    help='Username of the account on https://oceancolor.gsfc.nasa.gov/',
                    default=None,
                    type=str)
required.add_argument('-p',
                    action="store",
                    dest="password",
                    help='Password of the account on https://oceancolor.gsfc.nasa.gov/',
                    default=None,
                    type=str)

args = parser.parse_args()

# If the commandline option is given, check if all needed information are given
if args.cmd and (args.configFilePath is None or args.inputFile is None or args.outputDirectory is None or args.level is None):
    parser.error("-cmd requires -c config -i inputFile -o outputDirectory -l processingLevel")
# If the commandline option is given, check if all needed information are given
if args.cmd and args.level=='L2' and (args.username is None or args.password is None):
    parser.error("L2 processing requires username and password for https://oceancolor.gsfc.nasa.gov/")

# We store all arguments in variables
cmd = args.cmd
configFilePath = args.configFilePath
inputFile = args.inputFile
outputDirectory = args.outputDirectory
level = args.level
ancFile = args.ancFile
username = args.username
password = args.password

if __name__ == '__main__':

    # If the cmd argument is given, run the Command class without the GUI
    if cmd:
        if not (args.username is None or args.password is None):
            # Only for L2 processing set credentials
            GetAnc.userCreds(username, password)
        Command(configFilePath, inputFile, outputDirectory, level, ancFile)
    else:
        app = QtWidgets.QApplication(sys.argv)
        win = Window()
        sys.exit(app.exec_())
