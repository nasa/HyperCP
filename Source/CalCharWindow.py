''' GUI for the selection of L1B calibration and characterization configuration. '''
import os
import glob
import shutil
from pathlib import Path
from PyQt5 import QtWidgets

from ocdb.api.OCDBApi import new_api, OCDBApi
from Source.ConfigFile import ConfigFile
from Source import PATH_TO_CONFIG
from Source.Controller import Controller
from Source.CalibrationFileReader import CalibrationFileReader
from Source import PACKAGE_DIR as CODE_HOME

class CalCharWindow(QtWidgets.QDialog):
    ''' Object for calibration/characterization configuration GUI '''
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.setModal(True)
        self.initUI()

    def initUI(self):
        ''' Initialize the GUI '''
        calibrationDir = os.path.splitext(self.name)[0] + "_Calibration"
        self.calibrationPath = os.path.join(PATH_TO_CONFIG, calibrationDir)

        # Sensor information
        # SERIAL NUMBERS...
        self.neededCalCharsFRM = {}
        if ConfigFile.settings['SensorType'] == 'TriOS':
            for k,v in ConfigFile.settings['CalibrationFiles'].items():

                sensorType = v['frameType']

                v['serialNumber'] = k.split('.ini')[0]
                if sensorType in  ['LI', 'LT']:
                    self.neededCalCharsFRM[v['frameType']] = ['%s_%s' % (v['serialNumber'], c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'POLAR']]
                elif sensorType == 'ES':
                    self.neededCalCharsFRM[v['frameType']] = ['%s_%s' % (v['serialNumber'], c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'ANGULAR']]
        elif ConfigFile.settings['SensorType'] == 'SeaBird':

            calibrationMap = CalibrationFileReader.read(self.calibrationPath)
            Controller.generateContext(calibrationMap)

            for k,v in ConfigFile.settings['CalibrationFiles'].items():
                print(k,v)
                if not ((k.startswith('HSL') or k.startswith('HED')) and k.endswith('.cal')):
                    continue

                # extract digits...
                serialNumber0 = '%04d' % int(''.join([k0 for k0 in k[len('HSE'):-len('.cal')] if k0.isdigit()]))
                v['serialNumber'] = 'SAT' + serialNumber0

                sensorType = calibrationMap[k].sensorType

                if sensorType in  ['LI', 'LT']:
                    self.neededCalCharsFRM[sensorType] = ['%s_%s' % (v['serialNumber'], c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'POLAR']]
                elif sensorType == 'ES':
                    self.neededCalCharsFRM[sensorType] = ['%s_%s' % (v['serialNumber'], c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'ANGULAR']]

        elif ConfigFile.settings['SensorType'] == 'Dalec':
            # TODO
            pass # Not yet implemented, and not needed, as FRM regimes are not available still for DALEC.

        if ConfigFile.settings['SensorType'] == 'Dalec':
            # FRM regimes not yet implemented, forcing factory mode.
            ConfigFile.settings["fL1bCal"] == 1

        # Files needed


        # Thermal source selection
        ThermalLabel = QtWidgets.QLabel(" Select source of internal sensor working temperature:", self)
        ThermalLabel_font = ThermalLabel.font()
        ThermalLabel_font.setPointSize(12)
        ThermalLabel_font.setBold(True)
        ThermalLabel.setFont(ThermalLabel_font)

        self.ThermistorRadioButton = QtWidgets.QRadioButton("Internal Thermistor (SeaBird, DALEC, TriOS-G2)")
        # self.ThermistorRadioButton.setAutoExclusive(False)
        self.ThermistorRadioButton.clicked.connect(self.ThermistorRadioButtonClicked)
        self.AirTempRadioButton = QtWidgets.QRadioButton("Air Temperature + 5 deg. C")
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
        self.ClassCalRadioButton = QtWidgets.QRadioButton(f"FRM Class-Specific characterisation coefficients will be used (available in /Data/Class_Based_Characterizations/{ConfigFile.settings['SensorType']})"
                                                          "\n NB: Sensor-specific calibrations with uncertainties in the FidRadDB format required" )
        self.ClassCalRadioButton.setAutoExclusive(False)
        self.ClassCalRadioButton.clicked.connect(self.ClassCalRadioButtonClicked)

         # Full
        self.FullCalRadioButton = QtWidgets.QRadioButton("FRM Sensor-Specific characterisation coefficients will be used (highest quality)"
                                                         "\n NB: Sensor-specific calibrations with uncertainties and characterizations in the FidRadDB format required")
        self.FullCalRadioButton.setAutoExclusive(False)
        self.FullCalRadioButton.clicked.connect(self.FullCalRadioButtonClicked)

        # Disable FRM regimes for DALEC for the moment.
        if ConfigFile.settings['SensorType'] == 'Dalec':
            self.ClassCalRadioButton.setDisabled(True)
            self.FullCalRadioButton.setDisabled(True)

        if ConfigFile.settings["fL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
        elif ConfigFile.settings["fL1bCal"] == 2:
            self.ClassCalRadioButton.setChecked(True)
        elif ConfigFile.settings["fL1bCal"] == 3:
            self.FullCalRadioButton.setChecked(True)

        CalLabel2 = QtWidgets.QLabel("If FRM cal-char regime selected, then ...", self)

        CalLabel2_font = CalLabel2.font()
        CalLabel2_font.setPointSize(12)
        CalLabel2_font.setBold(True)
        CalLabel2.setFont(CalLabel2_font)


        FidRadDB_link = '<a href="https://ocdb.eumetsat.int/docs/fidrad-database.html">FidRadDB-formatted</a>'
        CalLabel2a = QtWidgets.QLabel(f'... check that all the needed {FidRadDB_link} cal/char files are available under: <br> {self.calibrationPath}', self)

        CalLabel2a_font = CalLabel2a.font()
        CalLabel2a_font.setPointSize(9)
        CalLabel2a_font.setBold(False)
        CalLabel2a.setFont(CalLabel2a_font)

        CalLabel2b = QtWidgets.QLabel("Missing cal/char files?", self)

        CalLabel2b_font = CalLabel2b.font()
        CalLabel2b_font.setPointSize(9)
        CalLabel2b_font.setBold(False)
        CalLabel2b.setFont(CalLabel2b_font)

        CalLabel2cES = QtWidgets.QLabel("Downwelling irradiance, ES", self)

        CalLabel2cES_font = CalLabel2cES.font()
        CalLabel2cES_font.setPointSize(9)
        CalLabel2cES_font.setBold(False)
        CalLabel2cES.setFont(CalLabel2cES_font)

        CalLabel2cLT = QtWidgets.QLabel("Total water radiance, LT (water)", self)

        CalLabel2cLT_font = CalLabel2cLT.font()
        CalLabel2cLT_font.setPointSize(9)
        CalLabel2cLT_font.setBold(False)
        CalLabel2cLT.setFont(CalLabel2cLT_font)

        CalLabel2cLI = QtWidgets.QLabel("Sky radiance, LI (sky)", self)

        CalLabel2cLI_font = CalLabel2cLI.font()
        CalLabel2cLI_font.setPointSize(9)
        CalLabel2cLI_font.setBold(False)
        CalLabel2cLI.setFont(CalLabel2cLI_font)

        self.FidRadDBcalCharDirCheckES = QtWidgets.QLineEdit(self)
        self.FidRadDBcalCharDirCheckES.setDisabled(True)

        self.FidRadDBcalCharDirCheckLT = QtWidgets.QLineEdit(self)
        self.FidRadDBcalCharDirCheckLT.setDisabled(True)

        self.FidRadDBcalCharDirCheckLI = QtWidgets.QLineEdit(self)
        self.FidRadDBcalCharDirCheckLI.setDisabled(True)

        self.addCalCharFilesButton = QtWidgets.QPushButton("Copy from local source")
        self.addCalCharFilesButton.clicked.connect(self.addCalCharFilesButtonClicked)


        self.FidRadDBdownload = QtWidgets.QPushButton("Download from FidRadDB", self)
        self.FidRadDBdownload.clicked.connect(self.FidRadDBdownloadClicked)


        CalLabel3 = QtWidgets.QLabel("Multiple calibrations available? Select option (only supported for FRM regimes):", self)

        CalLabel3_font = CalLabel3.font()
        CalLabel3_font.setPointSize(12)
        CalLabel3_font.setBold(True)
        CalLabel3.setFont(CalLabel3_font)

        self.calFileMostRecent = QtWidgets.QRadioButton("Use most recent calibrations prior to acquisition time (default)")
        self.calFileMostRecent.setAutoExclusive(False)
        self.calFileMostRecent.clicked.connect(lambda: self.MultiCalOptions('most_recent'))

        self.calFilePrePost = QtWidgets.QRadioButton("Use mean of pre- and post- calibrations") 
        self.calFilePrePost.setAutoExclusive(False)
        self.calFilePrePost.clicked.connect(lambda: self.MultiCalOptions('pre_post'))

        self.addPreCalButton = QtWidgets.QPushButton("Choose (3) pre-cal files:")
        self.addPreCalButton.clicked.connect(lambda: self.ChooseCalFiles('pre_cal'))
        self.PreCalLineEdit = QtWidgets.QLineEdit(self)
        self.PreCalLineEdit.setDisabled(True)

        self.addPostCalButton = QtWidgets.QPushButton("Choose (3) post-cal files:")
        self.addPostCalButton.clicked.connect(lambda: self.ChooseCalFiles('post_cal'))
        self.PostCalLineEdit = QtWidgets.QLineEdit(self)
        self.PostCalLineEdit.setDisabled(True)

        self.calFileChoose = QtWidgets.QRadioButton("Use specific calibration files")
        self.calFileChoose.setAutoExclusive(False)
        self.calFileChoose.clicked.connect(lambda: self.MultiCalOptions('choose'))

        self.addChooseCalButton = QtWidgets.QPushButton("Choose (3) cal files:")
        self.addChooseCalButton.clicked.connect(lambda: self.ChooseCalFiles('choose_cal'))
        self.ChooseCalLineEdit = QtWidgets.QLineEdit(self)
        self.ChooseCalLineEdit.setDisabled(True)

        self.saveButton = QtWidgets.QPushButton("Save/Close")
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        # TODO Average of pre and post still not implemented (disabled)
        self.calFilePrePost.setDisabled(True)
        self.addPreCalButton.setDisabled(True)
        self.addPostCalButton.setDisabled(True)


        self.CalStatusUpdate()
        self.MultiCalOptions('most_recent')

        #####################################################################################

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
        VBox.addWidget(CalLabel2a)
        VBox.addWidget(CalLabel2b)

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
        CalHBox5.addStretch()
        CalHBox5.addWidget(self.addPreCalButton)
        CalHBox5.addWidget(self.PreCalLineEdit)
        CalHBox5.addWidget(self.addPostCalButton)
        CalHBox5.addWidget(self.PostCalLineEdit)
        CalHBox5.addStretch()
        VBox.addLayout(CalHBox5)

        # Choose other
        VBox.addWidget(self.calFileChoose)
        CalHBox6 = QtWidgets.QHBoxLayout()
        CalHBox6.addStretch()
        CalHBox6.addWidget(self.addChooseCalButton)
        CalHBox6.addWidget(self.ChooseCalLineEdit)
        CalHBox6.addStretch()
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

    def ThermalStatusUpdate(self):
        if ConfigFile.settings['SensorType'].lower() == 'trios': # G1
            self.ThermistorRadioButton.setDisabled(True)
            self.AirTempRadioButton.setDisabled(False)
            self.CapsOnFileRadioButton.setDisabled(False)
        else:
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

    def ChooseCalFiles(self,option_cal_char_file):
        print("ConfigWindow - Add/update cal/char files")

        self.RadCalDir = self.calibrationPath
        print('Radiometric characterization directory changed: ', self.RadCalDir)

        ConfigFile.settings['RadCalDir'] = self.RadCalDir
        # self.CalStatusUpdate()

        calFileStr = None
        if option_cal_char_file == 'pre_cal':
            calFileStr = "3 pre-calibration"
        elif option_cal_char_file == 'post_cal':
            calFileStr = "3 post-calibration"
        elif option_cal_char_file in 'choose_cal':
            calFileStr = "3 calibration"

        correctSelection = False
        while not correctSelection:
            file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
                self,  # parent window
                f"Select {calFileStr} files",  # dialog title
                ConfigFile.settings['FullCalDir'],  # starting directory (empty string means current dir)
                "RADCAL text files (*RADCAL*.txt);;All Files (*)",  # file filter
                options=QtWidgets.QFileDialog.Options())

            # If cancel or X selected
            if not file_paths:
                correctSelection = True
            else:
                # Then filter for files containing "RADCAL" in their name
                file_paths = [f for f in file_paths if "RADCAL" in os.path.basename(f)]

                if len(file_paths) != 3:
                    QtWidgets.QMessageBox.warning(None, "No match", "Please select 3 RADCAL files one for each sensor (Es, Li and Lt)")
                else:
                    correctSelection = True

        for file in file_paths:
            dest = Path(self.calibrationPath) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {self.calibrationPath}')
                shutil.copy(file, dest)

    def CalStatusUpdate(self):
        # Enable/disable features based on regime selected
        if ConfigFile.settings["fL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
            self.ClassCalRadioButton.setChecked(False)
            self.FullCalRadioButton.setChecked(False)

            self.addCalCharFilesButton.setDisabled(True)
            self.FidRadDBdownload.setDisabled(True)
            # self.addClassFilesButton.setDisabled(True)
            # self.addFullFilesButton.setDisabled(True)

            self.calFileMostRecent.setDisabled(True)
            self.calFilePrePost.setDisabled(True)
            self.calFileChoose.setDisabled(True)

            self.addPreCalButton.setDisabled(True)
            self.addPostCalButton.setDisabled(True)
            self.addChooseCalButton.setDisabled(True)

        elif ConfigFile.settings["fL1bCal"] == 2:
            self.DefaultCalRadioButton.setChecked(False)
            self.ClassCalRadioButton.setChecked(True)
            self.FullCalRadioButton.setChecked(False)

            self.addCalCharFilesButton.setDisabled(False)
            self.FidRadDBdownload.setDisabled(False)

            self.calFileMostRecent.setDisabled(False)
            # self.calFilePrePost.setDisabled(False) TODO not yet implemented
            self.calFileChoose.setDisabled(False)

            # self.addPreCalButton.setDisabled(False) TODO not yet implemented
            # self.addPostCalButton.setDisabled(False) TODO not yet implemented
            self.addChooseCalButton.setDisabled(False)

        elif ConfigFile.settings["fL1bCal"] == 3:
            self.DefaultCalRadioButton.setChecked(False)
            self.ClassCalRadioButton.setChecked(False)
            self.FullCalRadioButton.setChecked(True)

            self.addCalCharFilesButton.setDisabled(False)
            self.FidRadDBdownload.setDisabled(False)

            self.calFileMostRecent.setDisabled(False)
            # self.calFilePrePost.setDisabled(False) TODO not yet implemented
            self.calFileChoose.setDisabled(False)

            # self.addPreCalButton.setDisabled(False) TODO not yet implemented
            # self.addPostCalButton.setDisabled(False) TODO not yet implemented
            self.addChooseCalButton.setDisabled(False)

        self.missing_files(ConfigFile.settings['fL1bCal'])


    def DefaultCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Factory")
        ConfigFile.settings["fL1bCal"] = 1
        self.CalStatusUpdate()

    def ClassCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Class-based")
        ConfigFile.settings["fL1bCal"] = 2
        self.CalStatusUpdate()

    def FullCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Instrument-specific FRM")
        ConfigFile.settings["fL1bCal"] = 3
        self.CalStatusUpdate()

    def missing_files(self, fL1bCal):

        missingFilesStrings = {'ES':'All needed files found', 'LT':'All needed files found', 'LI':'All needed files found'}
        missingFilesList = []

        if fL1bCal == 1:
            missingFilesStrings = {k:'No FidRadDB cal./char. files needed' for k in missingFilesStrings.keys()}
            missingFilesList = []
        else:
            for frameType, files in self.neededCalCharsFRM.items():
                missingFullFRM0 = [f for f in files if len(glob.glob(os.path.join(Path(self.calibrationPath), '*%s*.[tT][xX][tT]' % f))) == 0]
                if fL1bCal == 2:
                    missingFullFRM = [f for f in missingFullFRM0 if f.split('_')[-1] == 'RADCAL']
                elif fL1bCal == 3:
                    missingFullFRM = missingFullFRM0

                if len(missingFullFRM)>0:
                    missingFilesStrings[frameType] = 'Missing files: %s' % ' '.join(missingFullFRM)
                    missingFilesList = missingFilesList + missingFullFRM

        self.FidRadDBcalCharDirCheckES.setText(missingFilesStrings['ES'])
        self.FidRadDBcalCharDirCheckLT.setText(missingFilesStrings['LT'])
        self.FidRadDBcalCharDirCheckLI.setText(missingFilesStrings['LI'])

        return missingFilesStrings, missingFilesList

    def addCalCharFilesButtonClicked(self):
        print("ConfigWindow - Add/update full characterization files")

        selected_files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,  # parent window
            f"Select cal/char files",
            self.calibrationPath,
            "Text files (*.txt);;All Files (*)",  # file filter
            options=QtWidgets.QFileDialog.Options())

        for file in selected_files:
            dest = Path(self.calibrationPath) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {self.calibrationPath}')
                shutil.copy(file, dest)

        self.missing_files(ConfigFile.settings['fL1bCal'])


    def FidRadDBdownloadClicked(self):

        ConfigFile.settings['FidRadDB'] = 1 # TODO deprecated... remove

        # First list missing files
        _, missingFilesList = self.missing_files(ConfigFile.settings['fL1bCal'])

        if len(missingFilesList) == 0:
            print('All cal./char. files were found under %s, nothing to download' % self.calibrationPath)
            return

        path_FidRadDB = os.path.join(CODE_HOME, 'Data', 'FidRadDB',ConfigFile.settings['SensorType'])

        try:
            api = new_api(server_url='https://ocdb.eumetsat.int')
        except:
            print('Unable to connect to FidRadDB.')

        # Check if files are already in local FidRadDB repository
        # If not download them first to local FidRadDB repository
        # Then, copy them to calPath
        for serialNumber_calCharType in missingFilesList:

            try:
                cal_char_files_remote = OCDBApi.fidrad_list_files(api, serialNumber_calCharType)
                cal_char_files_remote = [os.path.basename(file) for file in cal_char_files_remote]
            except:
                print('File %s not available at FidRadDB (https://ocdb.eumetsat.int) or not reachable.')
                cal_char_files_remote = []
            else:
                print('File(s) found at FidRadDB (https://ocdb.eumetsat.int) for tag %s.' % serialNumber_calCharType)

            cal_char_files_local = [os.path.basename(file) for file in glob.glob(os.path.join(path_FidRadDB,'*%s*' % serialNumber_calCharType))]

            cal_char_files = list(set(cal_char_files_remote + cal_char_files_local))

            print(serialNumber_calCharType, cal_char_files)


            for file in cal_char_files:

                dest_FidRadDB_local = os.path.join(path_FidRadDB, file)
                dest_CalPath = os.path.join(self.calibrationPath, file)

                if not os.path.exists(dest_FidRadDB_local):
                    try:
                        OCDBApi.fidrad_download_file(api, file, path_FidRadDB)
                    except:
                        print('Unable to download file %s from FidRadDB. Maybe file does not exist. '
                              'Also check your internet connection, if problem persists, provide cal/char file manually.')
                    else:
                        print('File %s successfully downloaded from FidRadDB' % file)

                if os.path.exists(dest_FidRadDB_local) and not os.path.exists(dest_CalPath):
                    try:
                        print(f'Copying {os.path.basename(file)} to {self.calibrationPath}')
                        shutil.copy(dest_FidRadDB_local, dest_CalPath)
                    except:
                        print(f'Could not copy {os.path.basename(file)} to {self.calibrationPath}. Check permissions, and try manually ...')

        self.missing_files(ConfigFile.settings['fL1bCal'])


    def MultiCalOptions(self,option_multical):

        if option_multical == 'most_recent':
            self.calFileMostRecent.setChecked(True)
            self.calFilePrePost.setChecked(False)
            self.calFileChoose.setChecked(False)

            self.addPreCalButton.setDisabled(True)
            self.addPostCalButton.setDisabled(True)
            self.addChooseCalButton.setDisabled(True)
        elif option_multical == 'pre_post':
            self.calFileMostRecent.setChecked(False)
            self.calFilePrePost.setChecked(True)
            self.calFileChoose.setChecked(False)

            self.addPreCalButton.setDisabled(False)
            self.addPostCalButton.setDisabled(False)
            self.addChooseCalButton.setDisabled(True)
        elif option_multical == 'choose':
            self.calFileMostRecent.setChecked(False)
            self.calFilePrePost.setChecked(False)
            self.calFileChoose.setChecked(True)

            self.addPreCalButton.setDisabled(True)
            self.addPostCalButton.setDisabled(True)
            self.addChooseCalButton.setDisabled(False)

    def saveButtonPressed(self):
        print("Cal/char - Save/Close Pressed")

        # ConfigFile.products["bL2Prodoc3m"] = int(self.oc3mCheckBox.isChecked())
        # ConfigFile.settings["bL2WeightMODISA"] = 1

        self.close()

    def cancelButtonPressed(self):
        print("Cal/char - Cancel Pressed")
        self.close()
