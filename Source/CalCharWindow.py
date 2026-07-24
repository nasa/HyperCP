''' GUI for the selection of L1B calibration and characterization configuration. '''
import os
import glob
import shutil
import re
from pathlib import Path
from datetime import datetime
import urllib.request

import numpy as np
import pandas as pd

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

import threading
import urllib.request


# Wrap the original urlopen with a fixed timeout argument (must be before ocdb import)
# TODO: Ask OCDB team to implement a timeout option
time_out = 5
original_urlopen = urllib.request.urlopen
def urlopen_default_timeout(*args, **kwargs):
    print('Modified urlopen called to enforce timeout of %s seconds' % time_out)
    if 'timeout' in kwargs:
        return urllib.request.urlopen(*args, **kwargs)  # If timeout is already specified, use it
    return original_urlopen(*args, **kwargs, timeout=time_out)
urllib.request.urlopen = urlopen_default_timeout

from ocdb.api.OCDBApi import new_api, OCDBApi

from Source.ConfigFile import ConfigFile
from Source.Controller import Controller
from Source.CalibrationFileReader import CalibrationFileReader
from Source import PACKAGE_DIR as CODE_HOME


# Wrap the original urlopen with a fixed timeout argument (must be before ocdb import)
# TODO: Ask OCDB team to implement a timeout option
time_out = 5
original_urlopen = urllib.request.urlopen
def urlopen_default_timeout(*args, **kwargs):
    print('Modified urlopen called to enforce timeout of %s seconds' % time_out)
    if 'timeout' in kwargs:
        return urllib.request.urlopen(*args, **kwargs)  # If timeout is already specified, use it
    return original_urlopen(*args, **kwargs, timeout=time_out)
urllib.request.urlopen = urlopen_default_timeout

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class mplWindow(QtWidgets.QDialog):
    ''' Object for matplotlib figures in pop-up winodows'''
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set window properties
        self.setWindowTitle("Pre/Post Calibration Drift Check")
        self.setModal(False)
        self.resize(800, 600)

        # Create layout
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Create matplotlib canvas
        self.sc = MplCanvas(self, width=8, height=6, dpi=100)
        layout.addWidget(self.sc)

        # Add close button
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

class CalCharWindow(QtWidgets.QDialog):
    ''' Object for calibration/characterization configuration GUI '''

    window_closed = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name

        # Define cal/char serial numbers
        self.serialNumber_neededCalChars_FullFRM()

        # FidRadDB thread...
        self._thread = None
        self.FidRadDB_api = new_api(server_url='https://ocdb.eumetsat.int')
        self.FidRadDB_connect_flag = False
        self.available_files_FidRadDB = {}

        # FidRadDB thread...Will execute worker_done once thread emits signal to "finished"
        self.finished.connect(self.worker_done)

        # Define path to local repository of FidRadDB sensor-specific files.
        sensor_type = 'TriOS' if ConfigFile.settings['SensorType'].lower() == "trios es only" else ConfigFile.settings['SensorType']
        self.path_FidRadDB = os.path.join(CODE_HOME, 'Data', 'FidRadDB', sensor_type)

        # Blocks input to other windows in the application
        self.setModal(True)

        # Initialize UI
        self.initUI()

    def initUI(self):
        ''' Initialize the GUI '''

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
            "FRM Class-Specific characterisations\n"# (in /Data/Class_Based_Characterizations/{ConfigFile.settings['SensorType']})\n"
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

        # Option 2: Pre and post check
        self.calFilePrePost = QtWidgets.QRadioButton("Use pre- and post- calibrations: Check consistency, and use closest to acquisition time")
        self.calFilePrePost.setAutoExclusive(False)
        self.calFilePrePost.clicked.connect(lambda: self.MultiCalOptions('pre_post'))
        self.CheckPrePostButton = QtWidgets.QPushButton("Check pre-/post-cal consistency")
        self.CheckPrePostButton.setAutoExclusive(False)
        self.CheckPrePostButton.clicked.connect(lambda: self.check_pre_post_CalDrift())

        self.CheckPrePostLineEdit = QtWidgets.QLineEdit(self)
        self.CheckPrePostLineEdit.setDisabled(True)

        self.addPreCalButton = QtWidgets.QPushButton("Choose (%s) pre-cal file(s):" % ConfigFile.settings['num_of_sensors'])
        self.addPreCalButton.clicked.connect(lambda: self.ChooseCalFiles('preCal'))

        self.PreCalLineEdit = QtWidgets.QLineEdit(self)
        self.PreCalLineEdit.setDisabled(True)

        self.addPostCalButton = QtWidgets.QPushButton("Choose (%s) post-cal file(s):" % ConfigFile.settings['num_of_sensors'])
        self.addPostCalButton.clicked.connect(lambda: self.ChooseCalFiles('postCal'))

        self.PostCalLineEdit = QtWidgets.QLineEdit(self)
        self.PostCalLineEdit.setDisabled(True)

        self.pre_post_cal_status()

        ###
        for cal_time in ['pre','post']:
            if ConfigFile.settings['%sCal_defined' % cal_time]:
                if cal_time == 'pre':
                    self.PreCalLineEdit.setText('Correctly selected')
                elif cal_time == 'post':
                    self.PostCalLineEdit.setText('Correctly selected')
            else:
                if cal_time == 'pre':
                    self.PreCalLineEdit.setText('Not selected')
                elif cal_time == 'post':
                    self.PostCalLineEdit.setText('Not selected')

        self.update_postCal()

        # Option 3: Choose a given cal
        self.calFileChoose = QtWidgets.QRadioButton("Use specific calibration files (regardless of calibration and acquisition times)")
        self.calFileChoose.setAutoExclusive(False)
        self.calFileChoose.clicked.connect(lambda: self.MultiCalOptions('choose'))

        self.addChooseCalButton = QtWidgets.QPushButton("Choose (%s) cal file(s):" % ConfigFile.settings['num_of_sensors'])
        self.addChooseCalButton.clicked.connect(lambda: self.ChooseCalFiles('chooseCal'))
        self.ChooseCalLineEdit = QtWidgets.QLineEdit(self)
        self.ChooseCalLineEdit.setDisabled(True)
        ChooseCal_defined = (ConfigFile.settings['chooseCal_ES'] is not None) and (ConfigFile.settings['chooseCal_LT'] is not None) and (ConfigFile.settings['chooseCal_LI'] is not None)
        if ChooseCal_defined:
            self.ChooseCalLineEdit.setText('Correctly selected')
        else:
            self.ChooseCalLineEdit.setText('Not selected')

        #
        self.calFilePrePost.setDisabled(True)
        self.addPreCalButton.setDisabled(True)
        self.addPostCalButton.setDisabled(True)
        self.CheckPrePostButton.setDisabled(True)

        # Save and close
        self.saveButton = QtWidgets.QPushButton("Save/Close")
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        self.populate_available_files_FidRadDB() # Required by worker and CalStatusUpdate
        self.CalStatusUpdate()

        if ConfigFile.settings["fL1bCal"] == 1:
            self.FidRadDB_initial_check = False
        else:
            self.start_worker('list_files')
            self.FidRadDB_initial_check = True

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

        # Pre - Post check
        VBox.addWidget(self.calFilePrePost)
        CalHBox5 = QtWidgets.QHBoxLayout()
        CalHBox5.addWidget(self.addPreCalButton)
        CalHBox5.addWidget(self.PreCalLineEdit)
        CalHBox5.addWidget(self.addPostCalButton)
        CalHBox5.addWidget(self.PostCalLineEdit)
        VBox.addLayout(CalHBox5)

        CalHBox5_2 = QtWidgets.QHBoxLayout()
        CalHBox5_2.addWidget(self.CheckPrePostButton)
        CalHBox5_2.addWidget(self.CheckPrePostLineEdit)
        VBox.addLayout(CalHBox5_2)

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
        '''
        define keys in ConfigFile.settings:
            - 'neededCalCharsFRM' --> For each sensor type (LI, LT, ES), list which cal/char files are needed for the full FRM case
            - 'serialNumber' --> For each sensor type (LI, LT, ES), identify serial number
        :return:
        '''
        # Sensor information (not implemented for DALEC
        # SERIAL NUMBERS and cl/char files needed for full FRM case
        # NB: This is needed only for FRM regimes (class and full)
        ConfigFile.settings['neededCalCharsFRM'] = {}
        ConfigFile.settings['serialNumber'] = {}

        # Identify serial number for TriOS case
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

        # SeaBird case
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

        # DALEC
        elif ConfigFile.settings['SensorType'] == 'Dalec':
            # TODO
            # Not yet implemented, and not needed for now, as FRM regimes are not available still for DALEC.
            pass

        if ConfigFile.settings['SensorType'] == 'Dalec':
            # FRM regimes not yet implemented, forcing factory mode.
            ConfigFile.settings["fL1bCal"] = 1

        #num_of_sensors
        n = 0
        for sensor_type in ['ES', 'LI', 'LT']:
            if ConfigFile.settings['serialNumber'].get(sensor_type) is not None:
                n += 1
        ConfigFile.settings['num_of_sensors'] = n

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
            self.calFilePrePost.setDisabled(False)
            self.calFileChoose.setDisabled(False)

        elif ConfigFile.settings["fL1bCal"] == 3:
            self.DefaultCalRadioButton.setChecked(False)
            self.ClassCalRadioButton.setChecked(False)
            self.FullCalRadioButton.setChecked(True)

            self.addCalCharFilesButton.setDisabled(False)
            self.FidRadDBdownload.setDisabled(False)

            self.calFileMostRecent.setDisabled(False)
            self.calFilePrePost.setDisabled(False)
            self.calFileChoose.setDisabled(False)

        # COMMENT TO TEST
        # self.calFilePrePost.setDisabled(True)

        self.missing_FidRadDB_cal_char_files()


    def FidRadDB_list_files(self):
        '''
        Put the OCDB list files command into a parallel queue...
        :return:
        available_files: dictionary, for each sensor type (LT, LI, ES) (and resp. serial number) listed corresponding files from FidRadDB
        success, Boolean, True unless exception in FidRadDB connection raised
        '''
        available_files = {}
        try:
            for sensorType, serialNumber_calCharTypes in ConfigFile.settings['neededCalCharsFRM'].items():
                for serialNumber_calCharType in serialNumber_calCharTypes:
                    available_files[serialNumber_calCharType] = OCDBApi.fidrad_list_files(self.FidRadDB_api, serialNumber_calCharType)
        except Exception as e:
            print('Unable to list files of type in FidRadDB: %s' % e)
            success = False
            for sensorType, serialNumber_calCharTypes in ConfigFile.settings['neededCalCharsFRM'].items():
                for serialNumber_calCharType in serialNumber_calCharTypes:
                    available_files[serialNumber_calCharType] = []
        else:
            print('Files successfully listed from FidRadDB.')
            success = True

        self.available_files_FidRadDB = available_files

        return success

    def FidRadDB_download_files(self):
        '''
        Download FidRadDB files according to self.files_to_be_downloaded, to be stored at self.path_FidRadDB
        :return:
        success: Boolean, True unless exception raised while downloading
        '''

        # First attempt listing files from FidRadDB
        success = self.FidRadDB_list_files()

        # List the files that are missing according to the selected cal/char regime
        _, missingFilesList = self.missing_FidRadDB_cal_char_files(out_of_thread=False)

        # Extract serial number and cal/char types from list of missing files.
        serialNumber_calCharTypes = list(set(list(['_'.join(mf.split('_')[1:-1]) for mf in missingFilesList])))

        # Nothing to download, return
        if len(missingFilesList) == 0:
            print('All cal./char. files were found under %s for the selected regime, nothing to download' % ConfigFile.getCalibrationDirectory())
            return

        # Initialise list to be inputted to the FidRadDB download function
        self.files_to_be_downloaded = []

        for serialNumber_calCharType in serialNumber_calCharTypes:

            # List files available in OCDB/FidRadDB
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
                    self.files_to_be_downloaded = self.files_to_be_downloaded + [file]


        # Needed inputs to perform download
        files = self.files_to_be_downloaded
        path_out = self.path_FidRadDB

        # Attempt download
        try:
            if len(files) == 0:
                print('Nothing found in FidRadDB (unreachable?)')
            for file in files:
                _ = OCDBApi.fidrad_list_files(self.FidRadDB_api, file)
                msg = OCDBApi.fidrad_download_file(self.FidRadDB_api, file, path_out)
                if not msg.startswith('File successfully'):
                    success = False
        except Exception as e:
            print('Unable to download files from FidRadDB: %s' % e)
            success = False

        if success:
            print('Files successfully listed and downloaded from FidRadDB.')
        else:
            print('FidRadDB connection timed out')

        return success

    def populate_available_files_FidRadDB(self):
        '''
        Fill up self.available_files_FidRadDB with empty lists
        :return:
        '''

        for sensorType, serialNumber_calCharTypes in ConfigFile.settings['neededCalCharsFRM'].items():
            for serialNumber_calCharType in serialNumber_calCharTypes:
                if serialNumber_calCharType not in self.available_files_FidRadDB:
                    self.available_files_FidRadDB[serialNumber_calCharType] = []

        return

    def start_worker(self, call_type):
        '''
        Start FidRadDB parallel thread

        :param call_type: a string ether 'list_files' or 'download_files'
        :return:
        '''

        # Disable all UI buttons that could trigger two FidRadDB threads...
        self.FullCalRadioButton.setDisabled(True)
        self.ClassCalRadioButton.setDisabled(True)
        self.DefaultCalRadioButton.setDisabled(True)
        self.FidRadDBdownload.setDisabled(True)
        self.addCalCharFilesButton.setDisabled(True)

        # Just before thread starts line edits show checking status (cannot be done inside thread otherwise UI can crash)
        self.FidRadDBcalCharDirCheckES.setText('Checking FidRadDB, (%i sec)...' % time_out)
        self.FidRadDBcalCharDirCheckES.setCursorPosition(0)  # Avoid text getting trimmed from the left
        self.FidRadDBcalCharDirCheckLT.setText('Checking FidRadDB, (%i sec)...' % time_out)
        self.FidRadDBcalCharDirCheckLT.setCursorPosition(0)
        self.FidRadDBcalCharDirCheckLI.setText('Checking FidRadDB, (%i sec)...' % time_out)
        self.FidRadDBcalCharDirCheckLI.setCursorPosition(0)

        # Start thread
        # self._thread_alive = True
        self._thread = threading.Thread(target=self.worker, args=(call_type,))
        self._thread.daemon = True
        self._thread.start()

    def worker(self, call_type):
        '''
        Connection to FidRadDB...
        :param call_type: string ... either for 'list_files' ro for 'download_files'
        :return:
        '''

        print('Attempting connection to FidRadDB ...')

        if call_type == 'list_files':
            success = self.FidRadDB_list_files()
        else: # 'download_files':
            success = self.FidRadDB_download_files()

        # This will modify the status text for each sensor
        if not success:
            self.FidRadDB_connect_flag = False
        else:
            self.FidRadDB_connect_flag = True

        # Emit signal to "finished" so that worker_done will be triggered
        self.finished.emit()

    def worker_done(self):
        '''
        Once 'finished' receives the signal from worker, this function is activated out of the thread to re-enable a few
        functionalities in CalCharWindow (this should not be done inside the thread).
        Also re-check the missing cal/char files...
        :return:
        '''

        # Re-enable UI functionalities
        self.FullCalRadioButton.setDisabled(False)
        self.ClassCalRadioButton.setDisabled(False)
        self.DefaultCalRadioButton.setDisabled(False)
        self.FidRadDBdownload.setDisabled(False)
        self.addCalCharFilesButton.setDisabled(False)

        # check the missing cal/char files...
        self.missing_FidRadDB_cal_char_files()

    def DefaultCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Factory")
        ConfigFile.settings["fL1bCal"] = 1
        self.CalStatusUpdate()
        # Force multical to most recent as other options are not supported for non-FRM regime
        self.MultiCalOptions('most_recent')

    def ClassCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Class-based")
        ConfigFile.settings["fL1bCal"] = 2
        self.CalStatusUpdate()
        if not self.FidRadDB_initial_check:
            self.start_worker('list_files')
            self.FidRadDB_initial_check = True

    def FullCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Instrument-specific FRM")
        ConfigFile.settings["fL1bCal"] = 3
        self.CalStatusUpdate()
        if not self.FidRadDB_initial_check:
            self.start_worker('list_files')
            self.FidRadDB_initial_check = True

    def missing_FidRadDB_cal_char_files(self, out_of_thread=True):
        '''
        out_of_thread: a Boolean, True if executed out of the FidRadDB thread

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
        missingFilesStrings: String to be printed in the line edit
        missingFilesList: List with missing cal/char files
        '''


        # Define strings to be
        if ConfigFile.settings['SensorType'].lower() == 'trios es only':
            missingFilesStrings = {'ES':'All needed files found', 'LT':'No LT sensor', 'LI':'No LI sensor'}
        else:
            missingFilesStrings = {'ES':'All needed files found', 'LT':'All needed files found', 'LI':'All needed files found'}

        missingFilesList = []
        # Define path to local repository of FidRadDB sensor-specific files.
        # path_FidRadDB = os.path.join(CODE_HOME, 'Data', 'FidRadDB',ConfigFile.settings['SensorType'])

        # Perform checks according to cal/char regime
        if ConfigFile.settings['fL1bCal'] == 1:
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
                    if ConfigFile.settings['fL1bCal'] == 2 and not is_RADCAL:
                        continue

                    filesInFidRadDB = self.available_files_FidRadDB[serialNumber_calCharType]

                    filesInLocalDB = sorted([f for f in os.listdir(Path(self.path_FidRadDB)) if (re.match(r'[C][P][_]%s[_][0-9]{14}[\.][tT][xX][tT]' % serialNumber_calCharType, f) is not None)])

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

        # # Update line edits (not to be executed if inside thread)
        if out_of_thread:
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
        self.missing_FidRadDB_cal_char_files()

    def FidRadDBdownloadClicked(self):
        '''
        Attempt listing and downloading from FidRadDB
        '''

        self.start_worker('download_files')

    def MultiCalOptions(self,option_multical):
        # Enable/disable and check/uncheck features based on selected multi cal options.
        if option_multical == 'most_recent':
            ConfigFile.settings['MultiCal'] = 0

            self.calFileMostRecent.setChecked(True)
            self.calFilePrePost.setChecked(False)
            self.calFileChoose.setChecked(False)

            self.addPreCalButton.setDisabled(True)
            self.addPostCalButton.setDisabled(True)
            self.CheckPrePostButton.setDisabled(True)
            self.addChooseCalButton.setDisabled(True)
        elif option_multical == 'pre_post':
            ConfigFile.settings['MultiCal'] = 1

            self.calFileMostRecent.setChecked(False)
            self.calFilePrePost.setChecked(True)
            self.calFileChoose.setChecked(False)

            self.addPreCalButton.setDisabled(False)

            self.update_postCal()

            # Check button disabled unless pre- and post-cal files are defined
            if ConfigFile.settings['pre_postCal_defined']:
                self.CheckPrePostButton.setDisabled(False)
            else:
                self.CheckPrePostButton.setDisabled(True)

            self.addChooseCalButton.setDisabled(True)
        elif option_multical == 'choose':
            ConfigFile.settings['MultiCal'] = 2

            self.calFileMostRecent.setChecked(False)
            self.calFilePrePost.setChecked(False)
            self.calFileChoose.setChecked(True)

            self.addPreCalButton.setDisabled(True)
            self.addPostCalButton.setDisabled(True)
            self.CheckPrePostButton.setDisabled(True)
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
        # For each requested
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
                selectCorrectStr = selectCorrectStr + '%s (%s): RADCAL not selected! <br><br>' % (sensorType, serialNumber)
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
            self.pre_post_cal_status()
        elif option_cal_char_file == 'postCal':
            self.PostCalLineEdit.setText(selectCorrectStr)
            self.PostCalLineEdit.setCursorPosition(0)
            self.pre_post_cal_status()
        elif option_cal_char_file in 'chooseCal':
            self.ChooseCalLineEdit.setText(selectCorrectStr)
            self.ChooseCalLineEdit.setCursorPosition(0)

        # Check button disabled unless pre- and post-cal files are defined
        if ConfigFile.settings['pre_postCal_defined']:
            self.CheckPrePostButton.setDisabled(False)
        else:
            self.CheckPrePostButton.setDisabled(True)

        self.update_postCal()

        # Copy it to calPath if not selected from there.
        for file in file_paths:
            dest = Path(ConfigFile.getCalibrationDirectory()) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {ConfigFile.getCalibrationDirectory()}')
                shutil.copy(file, dest)

    def pre_post_cal_status(self):
        '''
        Check if pre- and post-cals were properly selected and enable the corresponding buttons...
        :return:
        '''


        # Check if pre and post cals are defined for each sensor
        for cal_time in ['pre', 'post']:
            ConfigFile.settings['%sCal_defined' % cal_time] = True
            for sensor_type in ['ES', 'LI', 'LT']:
                if ConfigFile.settings['serialNumber'].get(sensor_type) is not None:
                    if ConfigFile.settings['%sCal_%s' % (cal_time,sensor_type)] is None:
                        ConfigFile.settings['%sCal_defined' % cal_time] = False

        # pre_postCal_defined?
        ConfigFile.settings['pre_postCal_defined'] = ConfigFile.settings['preCal_defined'] and ConfigFile.settings['postCal_defined']

        # Update pre-post check button
        if ConfigFile.settings['pre_postCal_defined']:
            self.CheckPrePostLineEdit.setText('Click button to check.')
        elif (not ConfigFile.settings['preCal_defined']) and (not ConfigFile.settings['postCal_defined']):
            self.CheckPrePostLineEdit.setText('Select pre- and post- cals first.')
        elif not ConfigFile.settings['preCal_defined']:
            self.CheckPrePostLineEdit.setText('Select pre- cals first.')
        elif not ConfigFile.settings['postCal_defined']:
            self.CheckPrePostLineEdit.setText('Select post- cals first.')

    def update_postCal(self):
        '''
        Check:
        if:
            pre-cals are defined
            pre-cals are previous to post-cals
        then:
            post-cal button enabled
        ... and update corresponding line edits..
        :return:
        '''

        # Default post cal line edit
        pre_cal_first_str = 'Select Pre-Cal first'

        # Check if pre-cal defined and update select button and line edit ...
        if ConfigFile.settings['preCal_defined']:
            self.addPostCalButton.setDisabled(False)
            if self.PostCalLineEdit.text() == pre_cal_first_str:
                self.PostCalLineEdit.setText('Not selected')
        else:
            self.addPostCalButton.setDisabled(True)
            self.PostCalLineEdit.setText(pre_cal_first_str)
            for sensorType in ConfigFile.settings['neededCalCharsFRM'].keys():
                ConfigFile.settings['postCal_%s' % sensorType] = None

        # Check if t(post-cal) > t(pre-cal) for each sensor and update line edits and butons respectively
        post_wrong = []
        post_later_str = ''
        for sensorType in ConfigFile.settings['neededCalCharsFRM'].keys():
            preCalFile = ConfigFile.settings.get('preCal_%s' % sensorType)
            postCalFile = ConfigFile.settings.get('postCal_%s' % sensorType)
            # Skip check if no pre-/post-cal files
            if (preCalFile is None) or (postCalFile is None):
                continue
            else:
                # Extract date from RADCAL filenames
                date0 = os.path.basename(preCalFile).split('_RADCAL_')[1][:-4]
                date1 = os.path.basename(postCalFile).split('_RADCAL_')[1][:-4]

                # Transform to date objects
                date0_ts = datetime.strptime(date0, '%Y%m%d%H%M%S')
                date1_ts = datetime.strptime(date1, '%Y%m%d%H%M%S')

                # Time check....
                if date0_ts >= date1_ts:
                    if post_later_str == '':
                        post_later_str += ' %s: Post-cal should be posterior to pre-cal. Select again!'

                    post_wrong = post_wrong + [sensorType]

                    ConfigFile.settings['postCal_%s' % sensorType] = None

        # post_later_str != '' here means an issue was spotted... then disable the check button.
        if post_later_str != '':
            post_later_str = post_later_str % ', '.join(post_wrong)
            self.PostCalLineEdit.setText(post_later_str)
            self.CheckPrePostButton.setDisabled(True)

    def check_pre_post_CalDrift(self):
        '''
        Take pre- and post- cals to determine whether they fall within expected
        Let:
         - R1 and R2 be responsivities associated to a given sensor,
         - u(R1), u(R2) the respective (k=2) uncertainties,
         - dt the time difference between the two calibrations,
        we estimate an acceptable "drift uncertainty" (k=1) as  1%<R1,R2>dT, where
            <R1,R2> is the mean responsivity

        then compute a En-score (k=2) (ISO 13528:2022) accounting for drift as:
        En = (R1-R2)/sqrt(u(R1)^2 + u(R2)^2 + (2*1%<R1,R2>dT)^2)
            - NB: for simplicity we do not consider covariances between R1 and R2

        To test consistency:
            if |En|[400 nm - 700 nm] <= 1 ---> R1 and R2 are considered consistent within uncertainties and expected drift.
            if |En|[400 nm - 700 nm] > 1 ---> R1 and R2 are considered inconsistent

        For each pair of responsivities and for sensor (Li, Lt, Es) a plot pops up showing the results of the test
            - If the test passes for all sensors in the full [400-700] nm range, then "check passed" should show
            - If it fails for any of these cases, then a WARNING is issued to the user, but processing can continue

        :return:
        '''

        # Summarise check status for each sensor
        check_passed = {}

        # Wavelength range
        vis = [400, 700]

        # Cal file columns
        cols = ['Nr.', 'wavelength[nm]', 'responsivity', 'uncertainty', 'dark1', 'dark2', 'raw1', 'stdev1', 'raw2', 'stdev2']

        # Perform test and plots for each sensor
        for sensorType in ConfigFile.settings['neededCalCharsFRM'].keys():

            # Get serial number, and get cal files from the chosen pre and post cals
            serialNumber = ConfigFile.settings['serialNumber'][sensorType]
            calFiles = {}
            cals = {}
            calFiles[0]  = ConfigFile.settings['preCal_%s'  % sensorType]
            calFiles[1]  = ConfigFile.settings['postCal_%s' % sensorType]

            # Get cal dates from cal file names
            date0 = os.path.basename(calFiles[0]).split('_RADCAL_')[1][:-4]
            date1 = os.path.basename(calFiles[1]).split('_RADCAL_')[1][:-4]

            # Convert dates to time
            date0_ts = datetime.strptime(date0, '%Y%m%d%H%M%S')
            date1_ts = datetime.strptime(date1, '%Y%m%d%H%M%S')

            # Convert to "readable" time to show in the plots
            date0_str= date0_ts.strftime('%Y-%m-%dT%H:%M:%S')
            date1_str= date1_ts.strftime('%Y-%m-%dT%H:%M:%S')

            # Time difference in years
            delta_t = (date1_ts - date0_ts).days / 365.2425

            # Read cal coefficients from cal files into "cals" dictionary
            for calnum in [0,1]:

                # Open Cal file
                with open(calFiles[calnum], 'r') as file:
                    lines = file.readlines()

                # Range of lines of interest
                startline = [ln for ln,l in enumerate(lines) if l=='[CALDATA]\n'][0] +1
                endline = len(lines)-[ln for ln,l in enumerate(lines) if l=='[END_OF_CALDATA]\n'][0]

                # Read into pandas dataframe
                cals[calnum]  = pd.read_csv(calFiles[calnum], names=cols, skiprows=startline, skipfooter=endline, engine='python', sep='\t')

                # Extract the wavelengths of interest
                cals[calnum] = cals[calnum].loc[(cals[calnum]['wavelength[nm]']>=vis[0]) & (cals[calnum]['wavelength[nm]']<=vis[1]),['wavelength[nm]', 'responsivity', 'uncertainty']]

                # Get absolute uncertainty
                cals[calnum]['uncertainty_abs'] = cals[calnum]['uncertainty']*cals[calnum]['responsivity']/100

            # Compute the "tolerable drift" term
            # Factor 0.01 ---> 1% tolerable drift per year at k=1
            # Factor 2 --->  to transform to k=2
            drift_r1r2 = 2* (0.01 * (cals[0]['responsivity'] + cals[1]['responsivity'])/2) * delta_t
            corrected_En_score =  (cals[0]['responsivity'] - cals[1]['responsivity']) / np.sqrt(cals[0]['uncertainty_abs']**2 + cals[1]['uncertainty_abs']**2 + drift_r1r2**2)

            # Perform En test
            excessiveDrift = np.abs(corrected_En_score) >= 1

            # Fill output dictionary with result of the test
            check_passed[sensorType] = bool(~ np.any(excessiveDrift))

            # Printout statement
            check_status = ('%s: Check PASSED!' % sensorType) if check_passed[sensorType] else ('%s: Check FAILED. INSPECT BEFORE RUNNING HYPERCP' % sensorType)

            ### Plotting ###

            # Initialise plot
            plot_window = mplWindow(self)  # Pass parent
            plot_window.sc.axes.clear()  # Clear any existing plots
            fig = plot_window.sc.figure
            fig.clear()

            # ax1: Plot R1 and R2 responsivities with respective k=2 uncertainties
            ax1 = fig.add_subplot(2, 1, 1)
            ax1.set_title(check_status)
            ax1.fill_between(cals[0]['wavelength[nm]'], cals[0]['responsivity'] - cals[0]['uncertainty_abs'], cals[0]['responsivity'] + cals[0]['uncertainty_abs'], alpha=0.5, color='m')
            ax1.plot(cals[0]['wavelength[nm]'],cals[0]['responsivity'], color='m', label='Pre-cal responsivity, sensor %s, date %s' % (serialNumber, date0_str))
            ax1.fill_between(cals[0]['wavelength[nm]'], cals[1]['responsivity'] - cals[1]['uncertainty_abs'], cals[1]['responsivity'] + cals[1]['uncertainty_abs'], alpha=0.5, color='c')
            ax1.plot(cals[0]['wavelength[nm]'],cals[1]['responsivity'], color='c', label='Post-cal responsivity, sensor %s, date %s' % (serialNumber, date1_str))
            ax1.legend()
            ax1.set_ylabel('Responsivities,r[a. u.]')

            # ax2: Plot En scores
            ax2 = fig.add_subplot(2, 1, 2)
            ax2.plot(cals[0]['wavelength[nm]'], corrected_En_score, label='Temporal-drift-corrected ' + r'$E_{n}$' + '-score = ' + r'$\frac{r_1-r_2}{\sqrt{(\Delta r_1)^2+(\Delta r_2)^2 + (2 \times 1\%\overline{r} \times \Delta t )^2}}$')
            ax2.axhline(y=-1, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label=r'$E_{n}$' + '-score acceptable range')
            ax2.axhline(y= 1, color='red', linestyle='--', linewidth=1.5, alpha=0.7)

            # Change to RED wherever |En| > 1
            if np.any(excessiveDrift):
                ax2.plot(cals[0]['wavelength[nm]'][excessiveDrift], corrected_En_score[excessiveDrift], label='Out of consistency range!', color='r', markersize=5)

            ax2.legend()
            ax2.set_ylabel(r'$E_{n}$' + '-score [unitless]')
            ax2.set_xlabel('Wavelength [nm]')
            ax2.set_ylim(-3, 3)

            # Draw and show
            plot_window.sc.draw()
            plot_window.show()  # Keep the window open
            plot_window.raise_()  # Bring to front

        # Summary of check status passed to ConfigFile.settings
        ConfigFile.settings['pre_post_check'] = check_passed

        # Compose printout string to show in cal-char window (in CheckPrePostLineEdit)
        check_out_str = ''; failed_for = []
        for sensorType, check_status in check_passed.items():
            if not check_status:
                if check_out_str == '':
                    check_out_str = 'Check FAILED for: %s. INSPECT pre-/post-cals BEFORE running HyperCP'
                failed_for = failed_for + [sensorType.capitalize()]
        if check_out_str == '':
            check_out_str = 'Check PASSED!'
        else:
            check_out_str = check_out_str % ', '.join(failed_for)

        # Send prinout string to cal char window
        self.CheckPrePostLineEdit.setText(check_out_str)

    def saveButtonPressed(self):
        '''
        Save settings, but check before saving...
        '''

        # Checks before saving!!
        closeFlag = True

        # Checks if missing cal/char files, if yes raise a Warning!!
        missingFilesStrings, missingFilesList = self.missing_FidRadDB_cal_char_files()
        if len(missingFilesList) != 0:

            cannot_process_flag = np.any([True if ('Must' in string or 'neither' in string or 'not available' in string) else False for string in missingFilesStrings.values()])

            if cannot_process_flag:
                # WARNING
                QtWidgets.QMessageBox.warning(None, "No match", "Missing FidRadDB cal/char files:<br>%s<br>"
                                                                "<br>Please copy them to %s from local source or attempt downloading them from FidRadDB." % ('<br>'.join(missingFilesList), ConfigFile.getCalibrationDirectory()))

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
                QtWidgets.QMessageBox.warning(None, "Missing files", "If pre- and post-calibration selected, please select all pre-cal and post-cal files for %s!" % sensorTypes_str)
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
            # Return to original URL open time out
            # urllib.request.urlopen = original_urlopen
            self.close()

    def cancelButtonPressed(self):
        print("Cal/char - Cancel Pressed")
        self.window_closed.emit()
        # event.accept()
        # Return to original URL open time out
        # urllib.request.urlopen = original_urlopen
        self.close()
