''' GUI for the selection of L1B calibration and characterization configuration. '''
import os
import glob
import shutil
import re
import numpy as np
from pathlib import Path
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal

import multiprocessing

from ocdb.api.OCDBApi import new_api, OCDBApi
from Source.ConfigFile import ConfigFile
# from Source import PATH_TO_CONFIG
from Source.Controller import Controller
from Source.CalibrationFileReader import CalibrationFileReader
from Source import PACKAGE_DIR as CODE_HOME

class CalCharWindow(QtWidgets.QDialog):
    ''' Object for calibration/characterization configuration GUI '''

    window_closed = pyqtSignal()
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        # Define path to local repository of FidRadDB sensor-specific files.
        sensor_type = 'TriOS' if ConfigFile.settings['SensorType'].lower() == "trios es only" \
            else ConfigFile.settings['SensorType']
        self.path_FidRadDB = os.path.join(CODE_HOME, 'Data', 'FidRadDB', sensor_type)
        self.setModal(True)
        self.FidRadDB_timeout = 3  # Seconds it will attempt to connect to FidRadDB (tigggererd everytime the cal/char window is opened)
        # NB: Once an attempt fails, time_out is set to 0.1 until Download button is clicked or window re-initialized, to avoid unnecessary waiting
        self.FidRadDB_connect_flag = True
        self.initUI()

    def initUI(self):
        ''' Initialize the GUI '''


        self.serialNumber_neededCalChars_FullFRM()

        self.FidRadDB_api = new_api(server_url='https://ocdb.eumetsat.int')

        self.available_files_FidRadDB = {}
        for sensorType, serialNumber_calCharTypes in ConfigFile.settings['neededCalCharsFRM'].items():
            for serialNumber_calCharType in serialNumber_calCharTypes:
                self.available_files_FidRadDB[serialNumber_calCharType] = self.FidRadDB_call_queue(self.FidRadDB_api, call_type='list_files', serialNumber_calCharType=serialNumber_calCharType)

        # Thermal source selection
        ThermalLabel = QtWidgets.QLabel(" Select source of internal sensor working temperature:", self)
        ThermalLabel_font = ThermalLabel.font()
        ThermalLabel_font.setPointSize(12)
        ThermalLabel_font.setBold(True)
        ThermalLabel.setFont(ThermalLabel_font)

        self.ThermistorRadioButton = QtWidgets.QRadioButton("Internal Thermistor (SeaBird, DALEC, TriOS-G2)")
        # self.ThermistorRadioButton.setAutoExclusive(False)
        self.ThermistorRadioButton.clicked.connect(self.ThermistorRadioButtonClicked)
        self.AirTempRadioButton = QtWidgets.QRadioButton("Air Temperature + 2.5 deg. C")
        self.AirTempRadioButton.clicked.connect(self.AirTempRadioButtonClicked)
        self.CapsOnFileRadioButton = QtWidgets.QRadioButton("Caps-on Dark File (T > 30 deg. C)")
        self.CapsOnFileRadioButton.clicked.connect(self.CapsOnFileRadioButtonClicked)

        self.ThermalStatusUpdate()

        # Cal/Char selection
        CalLabel = QtWidgets.QLabel(" Select Calibration-Characterization Regime:", self)
        CalLabel_font = CalLabel.font()
        CalLabel_font.setPointSize(12)
        CalLabel_font.setBold(True)
        CalLabel.setFont(CalLabel_font)

        # Factory
        self.DefaultCalRadioButton = QtWidgets.QRadioButton("Non-FRM, factory calibration only (no uncertainties except with SeaBird)")
        self.DefaultCalRadioButton.setAutoExclusive(False)
        self.DefaultCalRadioButton.clicked.connect(self.DefaultCalRadioButtonClicked)

        # Class
        self.ClassCalRadioButton = QtWidgets.QRadioButton(
            f"FRM Class-Specific characterisations\n"# (in /Data/Class_Based_Characterizations/{ConfigFile.settings['SensorType']})\n"
                "    Sensor-specific calibrations with uncertainties in FidRadDB format required" )
        self.ClassCalRadioButton.setAutoExclusive(False)
        self.ClassCalRadioButton.clicked.connect(self.ClassCalRadioButtonClicked)

         # Full
        self.FullCalRadioButton = QtWidgets.QRadioButton(
            "FRM Sensor-Specific characterisations (highest quality)\n"
                "    Sensor-specific calibrations and characterisations with uncertainties in FidRadDB format required")
        self.FullCalRadioButton.setAutoExclusive(False)
        self.FullCalRadioButton.clicked.connect(self.FullCalRadioButtonClicked)

        # Disable FRM regimes for DALEC for the moment.
        if ConfigFile.settings['SensorType'].lower() == 'dalec':
            self.ClassCalRadioButton.setDisabled(True)
            self.FullCalRadioButton.setDisabled(False)

        # Define which radio button is checked at initialisation
        if ConfigFile.settings["fL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
        elif ConfigFile.settings["fL1bCal"] == 2:
            self.ClassCalRadioButton.setChecked(True)
        elif ConfigFile.settings["fL1bCal"] == 3:
            self.FullCalRadioButton.setChecked(True)

        # Check completeness of calibration directory according to selected cal/char regime
        FidRadDB_link = '<a href="https://ocdb.eumetsat.int/docs/fidrad-database.html">FidRadDB-formatted</a>'
        CalLabel2 = QtWidgets.QLabel(f"Checking for required {FidRadDB_link} cal/char files:", self)
        CalLabel2_font = CalLabel2.font()
        CalLabel2_font.setPointSize(12)
        CalLabel2_font.setBold(True)
        CalLabel2.setFont(CalLabel2_font)

        # CalLabel2a = QtWidgets.QLabel(f'Checking for required {FidRadDB_link} cal/char files in: <br> {self.path_FidRadDB}', self)
        # CalLabel2a_font = CalLabel2a.font()
        # CalLabel2a_font.setPointSize(9)
        # CalLabel2a_font.setBold(False)
        # CalLabel2a.setFont(CalLabel2a_font)

        # CalLabel2b = QtWidgets.QLabel("Missing cal/char files?", self)
        # CalLabel2b_font = CalLabel2b.font()
        # CalLabel2b_font.setPointSize(9)
        # CalLabel2b_font.setBold(False)
        # CalLabel2b.setFont(CalLabel2b_font)

        CalLabel2cES = QtWidgets.QLabel('Es (SN: %s)' % ConfigFile.settings['serialNumber'].get('ES'), self)
        # CalLabel2cES_font = CalLabel2cES.font()
        # CalLabel2cES_font.setPointSize(9)
        # CalLabel2cES_font.setBold(False)
        # CalLabel2cES.setFont(CalLabel2cES_font)

        CalLabel2cLT = QtWidgets.QLabel('Lt (SN: %s)' % ConfigFile.settings['serialNumber'].get('LT'), self)
        # CalLabel2cLT_font = CalLabel2cLT.font()
        # CalLabel2cLT_font.setPointSize(9)
        # CalLabel2cLT_font.setBold(False)
        # CalLabel2cLT.setFont(CalLabel2cLT_font)

        CalLabel2cLI = QtWidgets.QLabel('Li (SN: %s)' % ConfigFile.settings['serialNumber'].get('LI'), self)
        # CalLabel2cLI_font = CalLabel2cLI.font()
        # CalLabel2cLI_font.setPointSize(9)
        # CalLabel2cLI_font.setBold(False)
        # CalLabel2cLI.setFont(CalLabel2cLI_font)

        # Line edits for each sensor type reporting what's missing...
        self.FidRadDBcalCharDirCheckES = QtWidgets.QLineEdit(self)
        self.FidRadDBcalCharDirCheckES.setDisabled(True)

        self.FidRadDBcalCharDirCheckLT = QtWidgets.QLineEdit(self)
        self.FidRadDBcalCharDirCheckLT.setDisabled(True)

        self.FidRadDBcalCharDirCheckLI = QtWidgets.QLineEdit(self)
        self.FidRadDBcalCharDirCheckLI.setDisabled(True)

        # Options to provide missing cal/char files
        self.addCalCharFilesButton = QtWidgets.QPushButton("Copy from local source")
        self.addCalCharFilesButton.clicked.connect(self.addCalCharFilesButtonClicked)


        self.FidRadDBdownload = QtWidgets.QPushButton("Download from FidRadDB", self)
        self.FidRadDBdownload.clicked.connect(self.FidRadDBdownloadClicked)

        # Multi-cal options
        # NB: pre-post average is disabled for the moment...
        CalLabel3 = QtWidgets.QLabel("Multiple calibrations available? Select option (only supported for FRM regimes):", self)

        CalLabel3_font = CalLabel3.font()
        CalLabel3_font.setPointSize(12)
        CalLabel3_font.setBold(True)
        CalLabel3.setFont(CalLabel3_font)

        # Option 1: Most recent cal prior to acquisition
        self.calFileMostRecent = QtWidgets.QRadioButton("Use most recent calibrations prior to acquisition time (default)")
        self.calFileMostRecent.setAutoExclusive(False)
        self.calFileMostRecent.clicked.connect(lambda: self.MultiCalOptions('most_recent'))

        # Option 2: Pre and post average
        self.calFilePrePost = QtWidgets.QRadioButton("Use mean of pre- and post- calibrations") 
        self.calFilePrePost.setAutoExclusive(False)
        self.calFilePrePost.clicked.connect(lambda: self.MultiCalOptions('pre_post'))

        self.addPreCalButton = QtWidgets.QPushButton("Choose (3) pre-cal files:")
        self.addPreCalButton.clicked.connect(lambda: self.ChooseCalFiles('preCal'))

        self.PreCalLineEdit = QtWidgets.QLineEdit(self)
        self.PreCalLineEdit.setDisabled(True)
        PreCal_defined = (ConfigFile.settings['preCal_ES'] is not None) and (ConfigFile.settings['preCal_LT'] is not None) and (ConfigFile.settings['preCal_LI'] is not None)
        if PreCal_defined:
            self.PreCalLineEdit.setText('Already selected')
        else:
            self.PreCalLineEdit.setText('Not selected')

        self.addPostCalButton = QtWidgets.QPushButton("Choose (3) post-cal files:")
        self.addPostCalButton.clicked.connect(lambda: self.ChooseCalFiles('postCal'))

        self.PostCalLineEdit = QtWidgets.QLineEdit(self)
        self.PostCalLineEdit.setDisabled(True)
        PostCal_defined = (ConfigFile.settings['postCal_ES'] is not None) and (ConfigFile.settings['postCal_LT'] is not None) and (ConfigFile.settings['postCal_LI'] is not None)
        if PostCal_defined:
            self.PostCalLineEdit.setText('Already selected')
        else:
            self.PostCalLineEdit.setText('Not selected')

        # Option 3: Choose a given cal
        self.calFileChoose = QtWidgets.QRadioButton("Use specific calibration files")
        self.calFileChoose.setAutoExclusive(False)
        self.calFileChoose.clicked.connect(lambda: self.MultiCalOptions('choose'))

        self.addChooseCalButton = QtWidgets.QPushButton("Choose (3) cal files:")
        self.addChooseCalButton.clicked.connect(lambda: self.ChooseCalFiles('chooseCal'))
        self.ChooseCalLineEdit = QtWidgets.QLineEdit(self)
        self.ChooseCalLineEdit.setDisabled(True)
        ChooseCal_defined = (ConfigFile.settings['chooseCal_ES'] is not None) and (ConfigFile.settings['chooseCal_LT'] is not None) and (ConfigFile.settings['chooseCal_LI'] is not None)
        if ChooseCal_defined:
            self.ChooseCalLineEdit.setText('Already selected')
        else:
            self.ChooseCalLineEdit.setText('Not selected')

        # TODO Average of pre and post disabled as still not implemented
        self.calFilePrePost.setDisabled(True)
        self.addPreCalButton.setDisabled(True)
        self.addPostCalButton.setDisabled(True)

        # Save and close
        self.saveButton = QtWidgets.QPushButton("Save/Close")
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        # determine cal status and multi cal options according to settings at initialisation
        self.CalStatusUpdate()

        if ConfigFile.settings['MultiCal'] == 0:
            self.MultiCalOptions('most_recent')
        elif ConfigFile.settings['MultiCal'] == 1:
            self.MultiCalOptions('pre_post')
        elif ConfigFile.settings['MultiCal'] == 2:
            self.MultiCalOptions('choose')

        ########################################## Build window ###########################################

        VBox = QtWidgets.QVBoxLayout()

        # Thermal Source
        VBox.addWidget(ThermalLabel)
        ThermalHBox = QtWidgets.QHBoxLayout()
        ThermalHBox.addWidget(self.ThermistorRadioButton)
        ThermalHBox.addWidget(self.AirTempRadioButton)
        ThermalHBox.addWidget(self.CapsOnFileRadioButton)
        ThermalHBox.addStretch()
        VBox.addLayout(ThermalHBox)

        # Instrument/Cal Files
        VBox.addWidget(CalLabel)

        #  Cal/char regimes
        VBox.addWidget(self.DefaultCalRadioButton) # Factory
        VBox.addWidget(self.ClassCalRadioButton) # Class
        VBox.addWidget(self.FullCalRadioButton) # Full

        # UT/FidRadDB files location
        VBox.addWidget(CalLabel2)
        # VBox.addWidget(CalLabel2a)
        # VBox.addWidget(CalLabel2b)

        # Check cal/char files: Es
        CalHBox1 = QtWidgets.QHBoxLayout()
        CalHBox1.addWidget(CalLabel2cES)
        CalHBox1.addWidget(self.FidRadDBcalCharDirCheckES)
        VBox.addLayout(CalHBox1)

        # Check cal/char files: Lt
        CalHBox2 = QtWidgets.QHBoxLayout()
        CalHBox2.addWidget(CalLabel2cLT)
        CalHBox2.addWidget(self.FidRadDBcalCharDirCheckLT)
        VBox.addLayout(CalHBox2)

        # Check cal/char files: Li
        CalHBox3 = QtWidgets.QHBoxLayout()
        CalHBox3.addWidget(CalLabel2cLI)
        CalHBox3.addWidget(self.FidRadDBcalCharDirCheckLI)
        VBox.addLayout(CalHBox3)

        # Copy/download missing files
        CalHBox4 = QtWidgets.QHBoxLayout()
        CalHBox4.addWidget(self.addCalCharFilesButton)
        CalHBox4.addWidget(self.FidRadDBdownload)
        VBox.addLayout(CalHBox4)

        # Multiple calibration files options
        VBox.addWidget(CalLabel3)

        # Most recent
        VBox.addWidget(self.calFileMostRecent)

        # Pre - Post average
        VBox.addWidget(self.calFilePrePost)
        CalHBox5 = QtWidgets.QHBoxLayout()
        CalHBox5.addWidget(self.addPreCalButton)
        CalHBox5.addWidget(self.PreCalLineEdit)
        CalHBox5.addWidget(self.addPostCalButton)
        CalHBox5.addWidget(self.PostCalLineEdit)
        VBox.addLayout(CalHBox5)

        # Choose other
        VBox.addWidget(self.calFileChoose)
        CalHBox6 = QtWidgets.QHBoxLayout()
        CalHBox6.addWidget(self.addChooseCalButton)
        CalHBox6.addWidget(self.ChooseCalLineEdit)
        VBox.addLayout(CalHBox6)

        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.cancelButton)

        # Adds hBox and saveHBox to primary VBox
        VBox.addLayout(saveHBox)

        self.setLayout(VBox)
        self.setGeometry(100, 100, 0, 0)
        self.setWindowTitle('Calibration/Characterization options')

    ###################################### GUI-controlled functions ###############################################

    def serialNumber_neededCalChars_FullFRM(self):
            # Sensor information (not implemented for DALEC
            # SERIAL NUMBERS and cl/char files needed for full FRM case
            # NB: This is needed only for FRM regimes (class and full)
            ConfigFile.settings['neededCalCharsFRM'] = {}
            ConfigFile.settings['serialNumber'] = {}

            if ConfigFile.settings['SensorType'].lower() in ["trios", "trios es only"]:
                for k,v in ConfigFile.settings['CalibrationFiles'].items():

                    # Keep only ini files for the identification of serial numbers
                    if not k.endswith('.ini'):
                        continue

                    # sensorType is frameType only for TriOS
                    sensorType = v['frameType']
                    serialNumber = k.split('.ini')[0]

                    # infer serial number from cal file name
                    ConfigFile.settings['serialNumber'][sensorType] = serialNumber

                    # cal/char tags are created based on serial number and char. type (e.g. STRAY) for each sensor type (e.g. ES)
                    if sensorType in  ['LI', 'LT']:
                        ConfigFile.settings['neededCalCharsFRM'][sensorType] = ['%s_%s' % (serialNumber, c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'POLAR']]
                    elif sensorType == 'ES':
                        ConfigFile.settings['neededCalCharsFRM'][sensorType] = ['%s_%s' % (serialNumber, c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'ANGULAR']]

            elif ConfigFile.settings['SensorType'].lower() == 'seabird':

                # Force use of thermistor
                ConfigFile.settings["fL1bThermal"] = 1

                # SeaBird: sensor type inferred from calibration map
                calibrationMap = CalibrationFileReader.read(ConfigFile.getCalibrationDirectory())
                Controller.generateContext(calibrationMap)

                for k,v in ConfigFile.settings['CalibrationFiles'].items():
                    # Serial numbers will be inferred from these specific cal files
                    if not ((k.startswith('HSL') or k.startswith('HED')) and k.endswith('.cal')):
                        continue

                    # SeaBird: sensor type inferred from calibration map
                    sensorType = calibrationMap[k].sensorType

                    # extract digits to compose serial number
                    serialNumber0 = '%04d' % int(''.join([k0 for k0 in k[len('HSE'):-len('.cal')] if k0.isdigit()]))
                    serialNumber = 'SAT' + serialNumber0

                    ConfigFile.settings['serialNumber'][sensorType] = serialNumber

                    # cal/char tags are created based on serial number and char. type (e.g. STRAY) for each sensor type (e.g. ES)
                    if sensorType in  ['LI', 'LT']:
                        ConfigFile.settings['neededCalCharsFRM'][sensorType] = ['%s_%s' % (serialNumber, c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'POLAR']]
                    elif sensorType == 'ES':
                        ConfigFile.settings['neededCalCharsFRM'][sensorType] = ['%s_%s' % (serialNumber, c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'ANGULAR']]

            elif ConfigFile.settings['SensorType'] == 'Dalec':
                # TODO
                # Not yet implemented, and not needed for now, as FRM regimes are not available still for DALEC.
                pass

            if ConfigFile.settings['SensorType'] == 'Dalec':
                # FRM regimes not yet implemented, forcing factory mode.
                ConfigFile.settings["fL1bCal"] = 1

    def ThermalStatusUpdate(self):
        if ConfigFile.settings['SensorType'].lower() in ["trios"]: # Assume: TriOS is G1 and TriOS ES Only is G2
            self.ThermistorRadioButton.setDisabled(True)
            if ConfigFile.settings["fL1bThermal"] == 1:
                # NOTE: This will need to be changed for G2
                ConfigFile.settings["fL1bThermal"] = 2 # Fallback in case of corrupted config
                self.AirTempRadioButton.setChecked(True)
                self.ThermistorRadioButton.setChecked(False)
            self.AirTempRadioButton.setDisabled(False)
            self.CapsOnFileRadioButton.setDisabled(False)
        else:
            if ConfigFile.settings['SensorType'].lower() in ["trios es only"]: # Assume: TriOS ES Only is G2
                ConfigFile.settings["fL1bThermal"] = 1 # In case config has no fL1bThermal. Assume: TriOS ES Only is G2
            self.ThermistorRadioButton.setDisabled(False)
            self.AirTempRadioButton.setDisabled(True)
            self.CapsOnFileRadioButton.setDisabled(True)

        if ConfigFile.settings["fL1bThermal"] == 1:
            self.ThermistorRadioButton.setChecked(True)
            self.AirTempRadioButton.setChecked(False)
            self.CapsOnFileRadioButton.setChecked(False)

        elif ConfigFile.settings["fL1bThermal"] == 2:
            self.ThermistorRadioButton.setChecked(False)
            self.AirTempRadioButton.setChecked(True)
            self.CapsOnFileRadioButton.setChecked(False)

        elif ConfigFile.settings["fL1bThermal"] == 3:
            self.ThermistorRadioButton.setChecked(False)
            self.AirTempRadioButton.setChecked(False)
            self.CapsOnFileRadioButton.setChecked(True)

    def ThermistorRadioButtonClicked(self):
        # NOTE: Once we can dynamically recognize TriOS G1 compared to G2, this radio should be deactivated for G1
        print("ConfigWindow - L1b Thermal source set to internal thermistor")
        ConfigFile.settings["fL1bThermal"] = 1
        self.ThermalStatusUpdate()

    def AirTempRadioButtonClicked(self):
        print("ConfigWindow - L1b Thermal source set to air-temperature-based")
        ConfigFile.settings["fL1bThermal"] = 2
        self.ThermalStatusUpdate()

    def CapsOnFileRadioButtonClicked(self):
        print("ConfigWindow - L1b Thermal source set to caps-on dark file")
        ConfigFile.settings["fL1bThermal"] = 3
        self.ThermalStatusUpdate()

    def CalStatusUpdate(self):
        # Enable/disable and check/uncheck features based on cal/char regime selected
        if ConfigFile.settings["fL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
            self.ClassCalRadioButton.setChecked(False)
            self.FullCalRadioButton.setChecked(False)

            self.addCalCharFilesButton.setDisabled(True)
            self.FidRadDBdownload.setDisabled(True)

            self.calFileMostRecent.setDisabled(True)
            self.calFilePrePost.setDisabled(True)
            self.calFileChoose.setDisabled(True)

        elif ConfigFile.settings["fL1bCal"] == 2:
            self.DefaultCalRadioButton.setChecked(False)
            self.ClassCalRadioButton.setChecked(True)
            self.FullCalRadioButton.setChecked(False)

            self.addCalCharFilesButton.setDisabled(False)
            self.FidRadDBdownload.setDisabled(False)

            self.calFileMostRecent.setDisabled(False)
            # self.calFilePrePost.setDisabled(False) TODO: commented as not yet implemented
            self.calFileChoose.setDisabled(False)

        elif ConfigFile.settings["fL1bCal"] == 3:
            self.DefaultCalRadioButton.setChecked(False)
            self.ClassCalRadioButton.setChecked(False)
            self.FullCalRadioButton.setChecked(True)

            self.addCalCharFilesButton.setDisabled(False)
            self.FidRadDBdownload.setDisabled(False)

            self.calFileMostRecent.setDisabled(False)
            # self.calFilePrePost.setDisabled(False) TODO: commented as not yet implemented
            self.calFileChoose.setDisabled(False)

        self.missing_FidRadDB_cal_char_files(ConfigFile.settings['fL1bCal'])

    def DefaultCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Factory")
        ConfigFile.settings["fL1bCal"] = 1
        self.CalStatusUpdate()
        # Force multical to most recent as other options are not supported for non-FRM regime
        self.MultiCalOptions('most_recent')

    def FidRadDB_list_files_queue(self, queue, api, serialNumber_calCharType):
        '''
        Put the OCDB list files command into a parallel queue...
        :param queue: a multithread parameter...
        :param api: the OCDB API
        :param serialNumber_calCharType: a string, e.g. 'SAM_8329_POLAR' or 'SAM_8329_RADCAL'
        :return:
        '''
        try:
            list_files = OCDBApi.fidrad_list_files(api, serialNumber_calCharType)
            queue.put(list_files)
        except Exception as e:
            print('Unable to list files of type %s in FidRadDB: %s' % (serialNumber_calCharType,e))

    def FidRadDB_download_files_queue(self, queue, api, files, path_out):
        '''
        Put the OCDB download files command into a parallel queue...
        :param queue: a multithread parameter...
        :param api: the OCDB API
        :param serialNumber_calCharType: a string, e.g. 'SAM_8329_POLAR' or 'SAM_8329_RADCAL'
        :return:
        '''
        try:
            if len(files) == 0:
                queue.put(print('Nothing to download'))
            for file in files:
                queue.put(OCDBApi.fidrad_download_file(api, file, path_out))
        except Exception as e:
            print('Unable to download files from FidRadDB: %s' % (e))

    def FidRadDB_call_queue(self, api, call_type='list_files', **kwargs):
        '''
        Call FidRadDB within a thread (to avoid FidRadDB time outs to block the opening of the Cal/Char window
        :param api: the OCDB API
        :param call_type: a string, either 'list_files' or 'download_files
        :param kwargs: a dictionary, containing the options needed to execute the OCDB API functions
        :return:
        '''
        # List all files available in FidRadDB and locally
        queue = multiprocessing.Queue()

        if call_type == 'list_files':
            call_function = self.FidRadDB_list_files_queue
            call_args = (queue, api, kwargs['serialNumber_calCharType'])
        elif call_type == 'download_files':
            call_function = self.FidRadDB_download_files_queue
            call_args = (queue, api, kwargs['files'], kwargs['path_out'])
        else:
            raise NotImplementedError

        # Start the thread
        p = multiprocessing.Process(
            target=call_function,
            args=call_args
        )
        p.start()
        # Define time out!
        p.join(self.FidRadDB_timeout)

        # If thread is alive after timeout, then kill and raise time out status (FidRadDB_connect_flag=False)
        # Also reduce timeout to minimum (0.1) unless download is re-atempted by user.
        if p.is_alive(): # timeout case
            p.terminate()
            p.join()
            self.FidRadDB_timeout = 0.1 # Timeout reduced to avoid excessive waiting... Re-set to 3 when Download button is clicked
            if call_type == 'list_files':
                print("Issue connecting to FidRadDB: %s. Skipping search ..." % kwargs['serialNumber_calCharType'])
                filesInFidRadDB = []
            elif call_type == 'download_files':
                print("Issue connecting to FidRadDB: %s. Skipping download ..." % kwargs['files'])
            self.FidRadDB_connect_flag = False
        else: # successful connection case
            if call_type == 'list_files':
                filesInFidRadDB = queue.get()
                if filesInFidRadDB == 0:
                    print('No files of type %s available in FidRadDB' % kwargs['serialNumber_calCharType'])
                else:
                    print('Files of type %s found in FidRadDB' % kwargs['serialNumber_calCharType'])

            elif call_type == 'download_files':
                queue.get()
                print('File %s successfully downloaded from FidRadDB' % kwargs['files'])

            self.FidRadDB_connect_flag = True

        if call_type == 'list_files':
            return filesInFidRadDB
        elif call_type == 'download_files':
            return

    def ClassCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Class-based")
        ConfigFile.settings["fL1bCal"] = 2
        self.CalStatusUpdate()

    def FullCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Instrument-specific FRM")
        ConfigFile.settings["fL1bCal"] = 3
        self.CalStatusUpdate()

    def missing_FidRadDB_cal_char_files(self, fL1bCal):
        '''
        Check which FidRadDB-like cal/char files are missing from ConfigFile.getCalibrationDirectory() according to the selected cal/char regime, fL1bCal
        if fL1bCal = 0
            non-FRM regime: No FidRadDB-like cal/char files are needed...
        if fL1bCal = 1
            FRM class based regime: only RADCALS in FidRadDB format are needed for each sensor ES, LI, and LT
        if fL1bCal = 2
            FRM full regime: RADCALS in FidRadDB format are needed for each sensor ES, LI, and LT and additionally
                LI and LT: STRAY, THERMAL, POLAR
                ES: STRAY, THERMAL, ANGULAR

        Output:
        missingFilesStrings
        missingFilesList:
        '''


        # Define strings to be
        if ConfigFile.settings['SensorType'].lower() == 'trios es only':
            missingFilesStrings = {'ES':'All needed files found', 'LT':'No LT sensor', 'LI':'No LI sensor'}
        else:
            missingFilesStrings = {'ES':'All needed files found', 'LT':'All needed files found', 'LI':'All needed files found'}
        # missingFilesStrings = {'ES':'', 'LT':'', 'LI':''}
        missingFilesList = []
        # Define path to local repository of FidRadDB sensor-specific files.
        # path_FidRadDB = os.path.join(CODE_HOME, 'Data', 'FidRadDB',ConfigFile.settings['SensorType'])

        # Perform checks according to cal/char regime
        if fL1bCal == 1:
            missingFilesStrings = {k:'No FidRadDB cal./char. files needed' for k in missingFilesStrings.keys()}
            missingFilesList = []
        else:

            # Loop over sensorType
            for sensorType, serialNumber_calCharTypes in ConfigFile.settings['neededCalCharsFRM'].items():

                # If ES only: Skip if sensor is not ES
                if 'es only' in ConfigFile.settings['SensorType'].lower():
                    if sensorType != 'ES':
                        continue

                # missingFiles: 0 of the needed files found locally... cannot be processed
                missingFiles = []

                # outdatedFiles: Updated file list in FidRadDB exists wrt local DB.
                outdatedFiles = []

                # missingInFidRadDBFiles: File also missing in FidRadDB!
                missingInFidRadDBFiles = []

                # Loop over serialNumber-cal./char. type combinations
                for serialNumber_calCharType in serialNumber_calCharTypes:

                    # RADCAL follows different rules: All RADCAL files in FidRadDB should be available locally
                    is_RADCAL = serialNumber_calCharType.split('_')[-1] == 'RADCAL'

                    # Skip if class-based and file is not RADCAL
                    if fL1bCal == 2 and not is_RADCAL:
                        continue

                    filesInFidRadDB = self.available_files_FidRadDB[serialNumber_calCharType]

                    filesInLocalDB = sorted([f for f in os.listdir(Path(self.path_FidRadDB)) if (re.match('[C][P][_]%s[_][0-9]{14}[\.][tT][xX][tT]' % serialNumber_calCharType, f) is not None)])

                    # Dates of files in FidRadDB and locally
                    filesDatesFidRadDB = np.array([int(f.split('_')[-1].split('.')[0]) for f in filesInFidRadDB])
                    filesDatesLocalDB = np.array([int(f.split('_')[-1].split('.')[0]) for f in filesInLocalDB])

                    # Files can be available or:
                    # - missing both locally and in FidRadDB (cannot process)  (missingInFidRadDBFiles)
                    # - missing locally (cannot process unless download from FidRadDB) (missingFiles)
                    # - outdated ("new" or other files available in FidRadDB) (outdatedFiles)
                    if len(filesDatesLocalDB) == 0:
                        if len(filesInFidRadDB) > 0:
                            missingFiles = missingFiles + filesInFidRadDB
                        else:
                            missingInFidRadDBFiles = missingInFidRadDBFiles + [serialNumber_calCharType]
                    else:
                        if is_RADCAL:
                            outdatedFiles = outdatedFiles + [f for f in filesInFidRadDB if f not in filesInLocalDB]
                        else:
                            if (len(filesDatesFidRadDB) > 0) and (np.nanmax(filesDatesFidRadDB) > np.max(filesDatesLocalDB)):
                                outdatedFiles = outdatedFiles + [f for f in filesInFidRadDB if f not in filesInLocalDB]

                # Output string
                if len(missingFiles)>0 or len(outdatedFiles)>0 or len(missingInFidRadDBFiles) > 0:
                    missingFilesStrings[sensorType] = ''
                else:
                    if not self.FidRadDB_connect_flag:
                        missingFilesStrings[sensorType] = 'All needed files available, but update status unconfirmed (FidRadDB unreachable!) '

                if len(missingInFidRadDBFiles)>0:
                    if self.FidRadDB_connect_flag:
                        missingFilesStrings[sensorType] = 'Needed files not available, neither locally nor in FidRadDB!: %s ' % ' '.join(missingInFidRadDBFiles)
                    else:
                        missingFilesStrings[sensorType] = 'Needed files not available, and cannot get them from FidRadDB (unreachable!): %s ' % ' '.join(missingInFidRadDBFiles)
                if len(missingFiles)>0:
                    if self.FidRadDB_connect_flag:
                        missingFilesStrings[sensorType] = missingFilesStrings[sensorType] + 'Must download files from FidRadDB: %s ' % ' '.join(missingFiles)
                    else:
                        missingFilesStrings[sensorType] = missingFilesStrings[sensorType] + 'Needed files not available, and cannot get them from FidRadDB (unreachable!): %s ' % ' '.join(missingFiles)

                if len(outdatedFiles)>0:
                    missingFilesStrings[sensorType] = missingFilesStrings[sensorType] + 'Suggest download updated files from FidRadDB: %s ' % ' '.join(outdatedFiles)


                # Missing file list
                missingFilesList = missingFilesList + missingFiles + outdatedFiles + missingInFidRadDBFiles

        # Update line edits
        self.FidRadDBcalCharDirCheckES.setText(missingFilesStrings['ES'])
        self.FidRadDBcalCharDirCheckES.setCursorPosition(0) # Avoid text getting trimmed from the left
        self.FidRadDBcalCharDirCheckLT.setText(missingFilesStrings['LT'])
        self.FidRadDBcalCharDirCheckLT.setCursorPosition(0)
        self.FidRadDBcalCharDirCheckLI.setText(missingFilesStrings['LI'])
        self.FidRadDBcalCharDirCheckLI.setCursorPosition(0)

        return missingFilesStrings, missingFilesList

    def addCalCharFilesButtonClicked(self):
        print("ConfigWindow - Add/update full characterization files")

        # List selected files...
        selected_files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,  # parent window
            "Select cal/char files",
            CODE_HOME,
            "Text files (*.txt);;All Files (*)",  # file filter
            options=QtWidgets.QFileDialog.Options())

        # Copy them to self.path_FidRadDB if not yet existing there
        for file in selected_files:
            dest = Path(self.path_FidRadDB) / os.path.basename(file)
            if not dest.exists():
                try:
                    shutil.copy(file, dest)
                except:
                    print(f'Issue copying {os.path.basename(file)} to {self.path_FidRadDB}, check directory permissions.')
                else:
                    print(f'{os.path.basename(file)} copied to {self.path_FidRadDB}')

        # Check completeness of self.path_FidRadDB after file copying
        self.missing_FidRadDB_cal_char_files(ConfigFile.settings['fL1bCal'])

    def FidRadDBdownloadClicked(self):
        '''
        For the list of missing files (listed according to serial number and cal/char type):
        - attempts download from OCDB/FidRadDB if file not found in local FidRadDB sensor-specific repository, "self.path_FidRadDB".
        '''

        ConfigFile.settings['FidRadDB'] = 1 # TODO deprecated... remove

        # First list missing files
        _, missingFilesList = self.missing_FidRadDB_cal_char_files(ConfigFile.settings['fL1bCal'])

        # Nothing to download, return
        if len(missingFilesList) == 0:
            print('All cal./char. files were found under %s, nothing to download' % ConfigFile.getCalibrationDirectory())
            return

        # Define path to local repository of FidRadDB sensor-specific files.
        # path_FidRadDB = os.path.join(CODE_HOME, 'Data', 'FidRadDB',ConfigFile.settings['SensorType'])

        # Check if files are already in local FidRadDB repository
        # If not download them first to local FidRadDB repository
        # Then, copy them to calPath
        # Loop over missing files according to cal_char type and serial number...

        self.FidRadDB_timeout = 3  # Reset timeout to 3 seconds when attempting Download!

        files_to_be_downloaded = []

        for serialNumber_calCharType in missingFilesList:

            # Attempt listing of files available in OCDB/FidRadDB
            cal_char_files_remote = self.available_files_FidRadDB[serialNumber_calCharType]
            cal_char_files_remote = [os.path.basename(file) for file in cal_char_files_remote]

            # See what's already available in the local repository of FidRadDB sensor-specific cal/char files
            cal_char_files_local = [os.path.basename(file) for file in glob.glob(os.path.join(self.path_FidRadDB,'*%s*' % serialNumber_calCharType))]

            # The files of interest will be the concatenation of both lists...
            # NB: We may have different time tags, however in principle we care for all time tags...
            #     and then we choose at L1B based on selected multical option)
            cal_char_files = list(set(cal_char_files_remote + cal_char_files_local))

            # Loop on targeted cal/char files...
            for file in cal_char_files:

                # /full/path destination files...
                dest_FidRadDB_local = os.path.join(self.path_FidRadDB, file)
                # dest_CalPath = os.path.join(ConfigFile.getCalibrationDirectory(), file)

                # If not in local FidRadDB repo, then attempt download
                if not os.path.exists(dest_FidRadDB_local):
                    files_to_be_downloaded = files_to_be_downloaded + [file]

                # # If existing in local FidRadDB repo and not in sel.calibrationPath, then attempt copying file...
                # if os.path.exists(dest_FidRadDB_local) and not os.path.exists(dest_CalPath):
                #     try:
                #         shutil.copy(dest_FidRadDB_local, dest_CalPath)
                #     except:
                #         print(f'Could not copy {os.path.basename(file)} to {ConfigFile.getCalibrationDirectory()}. Check permissions, and try manually ...')
                #     else:
                #         print(f'{os.path.basename(file)} copied to {ConfigFile.getCalibrationDirectory()} from {self.path_FidRadDB}')

        self.FidRadDB_call_queue(self.FidRadDB_api, call_type='download_files', files=files_to_be_downloaded, path_out=self.path_FidRadDB)

        # Check completeness of ConfigFile.getCalibrationDirectory() after file download and copying
        self.missing_FidRadDB_cal_char_files(ConfigFile.settings['fL1bCal'])

    def MultiCalOptions(self,option_multical):
        # Enable/disable and check/uncheck features based on selected multi cal options.
        if option_multical == 'most_recent':
            ConfigFile.settings['MultiCal'] = 0

            self.calFileMostRecent.setChecked(True)
            self.calFilePrePost.setChecked(False)
            self.calFileChoose.setChecked(False)

            self.addPreCalButton.setDisabled(True)
            self.addPostCalButton.setDisabled(True)
            self.addChooseCalButton.setDisabled(True)
        elif option_multical == 'pre_post':
            # NB: unreachable (disabled)
            ConfigFile.settings['MultiCal'] = 1

            self.calFileMostRecent.setChecked(False)
            self.calFilePrePost.setChecked(True)
            self.calFileChoose.setChecked(False)

            self.addPreCalButton.setDisabled(False)
            self.addPostCalButton.setDisabled(False)
            self.addChooseCalButton.setDisabled(True)
        elif option_multical == 'choose':
            ConfigFile.settings['MultiCal'] = 2

            self.calFileMostRecent.setChecked(False)
            self.calFilePrePost.setChecked(False)
            self.calFileChoose.setChecked(True)

            self.addPreCalButton.setDisabled(True)
            self.addPostCalButton.setDisabled(True)
            self.addChooseCalButton.setDisabled(False)

    def ChooseCalFiles(self,option_cal_char_file):
        '''
        Multi-cal options: Choose calibration files for multical options 1 (pre-cal and post-cal) and 2 (choose-cal) ...
        and check whether the choice is correct.
        '''

        print("ConfigWindow - Add/update cal/char files")

        #
        calFileStr = None
        if option_cal_char_file == 'preCal':
            calFileStr = "pre-calibration"
        elif option_cal_char_file == 'postCal':
            calFileStr = "post-calibration"
        elif option_cal_char_file in 'chooseCal':
            calFileStr = "calibration"

        file_paths = []
        # For each requeted
        for sensorType, serialNumber in ConfigFile.settings['serialNumber'].items():

            # Collect file paths from selected files...
            file_path_sensorType, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,  # parent window
                f"Select one {sensorType} {calFileStr} file, SN: {serialNumber}",  # dialog title
                self.path_FidRadDB,  # starting directory (empty string means current dir)
                "%s RADCAL file (CP_%s_RADCAL*.txt);;All Files (*)" % (sensorType, serialNumber),
                options=QtWidgets.QFileDialog.Options())
            if file_path_sensorType != []:
                file_paths.append(file_path_sensorType)


        # Initialise status flag and string
        selectCorrect = True
        selectCorrectStr = ''

        # Iterate over sensor type and expected RADCALS....
        for sensorType, calcharFiles in ConfigFile.settings['neededCalCharsFRM'].items():

            serialNumber = ConfigFile.settings['serialNumber'][sensorType]

            # Select only rad cals
            radcalStr = [f for f in calcharFiles if 'RADCAL' in f][0]

            # Check if selected files match the RADCAL tag (format CP_serialNumber_RADCAL_date.txt)
            calChar0 = [f for f in file_paths if '_'.join(os.path.basename(f).split('_')[1:-1]) == radcalStr]

            # Check correctness of selection
            if len(calChar0) == 0: # files missing
                selectCorrectStr = selectCorrectStr + '%s (Serial nr. %s): RADCAL not selected! <br><br>' % (sensorType, serialNumber)
                selectCorrect = False
                ConfigFile.settings['%s_%s' % (option_cal_char_file, sensorType)] = None
            elif len(calChar0) > 1: # multiple RADCALS for same sensor were selected
                selectCorrectStr = selectCorrectStr + '%s (SN: %s): Select only one RADCAL. ' % (sensorType, serialNumber)
                selectCorrect = False
                ConfigFile.settings['%s_%s' % (option_cal_char_file, sensorType)] = None
            else:
                ConfigFile.settings['%s_%s' % (option_cal_char_file, sensorType)] = calChar0[0]

        # If incorrectly selected, raise warning...
        if selectCorrect:
            selectCorrectStr = 'Correctly selected'
        else:
            QtWidgets.QMessageBox.warning(None, "No match", "Missing RADCAL files! <br><br> %s" % selectCorrectStr)

        selectCorrectStr = selectCorrectStr.replace('<br><br>','')

        # Update message in line edits
        if option_cal_char_file == 'preCal':
            self.PreCalLineEdit.setText(selectCorrectStr)
            self.PreCalLineEdit.setCursorPosition(0)
        elif option_cal_char_file == 'postCal':
            self.PostCalLineEdit.setText(selectCorrectStr)
            self.PostCalLineEdit.setCursorPosition(0)
        elif option_cal_char_file in 'chooseCal':
            self.ChooseCalLineEdit.setText(selectCorrectStr)
            self.ChooseCalLineEdit.setCursorPosition(0)

        # Copy it to calPath if not selected from there.
        for file in file_paths:
            dest = Path(ConfigFile.getCalibrationDirectory()) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {ConfigFile.getCalibrationDirectory()}')
                shutil.copy(file, dest)

    def saveButtonPressed(self):
        '''
        Save settings, but check before saving...
        '''

        # Checks before saving!!
        closeFlag = True

        # Checks if missing cal/char files, if yes raise a Warning!!
        missingFilesStrings, missingFilesList = self.missing_FidRadDB_cal_char_files(ConfigFile.settings['fL1bCal'])
        if len(missingFilesList) != 0:

            cannot_process_flag = np.any([True if ('Must' in string or 'neither' in string) else False for string in missingFilesStrings.values()])

            if cannot_process_flag:
                # WARNING
                QtWidgets.QMessageBox.warning(None, "No match", "Missing FidRadDB cal/char files:<br>%s<br>"
                                                                "<br>Please copy them to %s from local source or FidRadDB (https://ocdb.eumetsat.int)." % ('<br>'.join(missingFilesList), ConfigFile.getCalibrationDirectory()))

                closeFlag = False

        sensorTypes = ConfigFile.settings['neededCalCharsFRM'].keys()
        sensorTypes_str = ', '.join([sensorType for sensorType in ConfigFile.settings['neededCalCharsFRM'].keys()])

        # Checks if missing multi. cal selections, if yes, raise a warning
        if ConfigFile.settings['MultiCal'] == 1:
            pre_postCal_complete = True
            for multiCalOpt in ['preCal', 'postCal']:
                for sensorType in sensorTypes:
                    # RADCAL filename instead if selected in Source/CalCharWindow.py options.
                    if not ConfigFile.settings['%s_%s' % (multiCalOpt, sensorType)]:
                        pre_postCal_complete = False
                        break

            if not pre_postCal_complete:
                QtWidgets.QMessageBox.warning(None, "Missing files", "If mean of pre- and post-calibration selected, please select all pre-cal and post-cal files for %s!" % sensorTypes_str)
                closeFlag = False
        elif ConfigFile.settings['MultiCal'] == 2:
            chooseCal_complete = True
            for multiCalOpt in ['chooseCal']:
                for sensorType in sensorTypes:
                    # RADCAL filename instead if selected in Source/CalCharWindow.py options.
                    if not ConfigFile.settings['%s_%s' % (multiCalOpt, sensorType)]:
                        chooseCal_complete = False
                        break

            if not chooseCal_complete:
                QtWidgets.QMessageBox.warning(None, "Missing files", "If 'specific calibration' selected, please select calibration file(s) for %s" % sensorTypes_str)
                closeFlag = False

        # If no warnings raised, then close window...
        if closeFlag:
            print("Cal/char - Save/Close Pressed")
            self.window_closed.emit()
            # event.accept()
            self.close()

    def cancelButtonPressed(self):
        print("Cal/char - Cancel Pressed")
        self.window_closed.emit()
        # event.accept()
        self.close()
