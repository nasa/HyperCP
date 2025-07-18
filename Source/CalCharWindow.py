''' GUI for the selection of L1B calibration and characterization configuration. '''
import os
import glob
import shutil
from pathlib import Path
from PyQt5 import QtWidgets

from ocdb.api.OCDBApi import new_api, OCDBApi
from Source.ConfigFile import ConfigFile
# from Source import PATH_TO_CONFIG
from Source.Controller import Controller
from Source.CalibrationFileReader import CalibrationFileReader
from Source import PACKAGE_DIR as CODE_HOME

class CalCharWindow(QtWidgets.QDialog):
    ''' Object for calibration/characterization configuration GUI '''
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        # Define path to local repository of FidRadDB sensor-specific files.
        self.path_FidRadDB = os.path.join(CODE_HOME, 'Data', 'FidRadDB',ConfigFile.settings['SensorType'])
        self.setModal(True)
        self.initUI()

    def initUI(self):
        ''' Initialize the GUI '''

        # Sensor information (not implemented for DALEC
        # SERIAL NUMBERS and cl/char files needed for full FRM case
        # NB: This is needed only for FRM regimes (class and full)
        ConfigFile.settings['neededCalCharsFRM'] = {}
        if ConfigFile.settings['SensorType'].lower() == 'trios':
            for k,v in ConfigFile.settings['CalibrationFiles'].items():
                # sensorType is frameType only for TriOS
                sensorType = v['frameType']
                # infer serial number from cal file name
                v['serialNumber'] = k.split('.ini')[0]

                # cal/char tags are created based on serial number and char. type (e.g. STRAY) for each sensor type (e.g. ES)
                if sensorType in  ['LI', 'LT']:
                    ConfigFile.settings['neededCalCharsFRM'][v['frameType']] = ['%s_%s' % (v['serialNumber'], c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'POLAR']]
                elif sensorType == 'ES':
                    ConfigFile.settings['neededCalCharsFRM'][v['frameType']] = ['%s_%s' % (v['serialNumber'], c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'ANGULAR']]

        elif ConfigFile.settings['SensorType'].lower() == 'seabird':

            # Force use of thermistor
            ConfigFile.settings["fL1bThermal"] == 1

            # SeaBird: sensor type inferred from calibration map
            calibrationMap = CalibrationFileReader.read(ConfigFile.getCalibrationDirectory())
            Controller.generateContext(calibrationMap)

            for k,v in ConfigFile.settings['CalibrationFiles'].items():
                # Serial numbers will be inferred from these specific cal files
                if not ((k.startswith('HSL') or k.startswith('HED')) and k.endswith('.cal')):
                    continue

                # extract digits to compose serial number
                serialNumber0 = '%04d' % int(''.join([k0 for k0 in k[len('HSE'):-len('.cal')] if k0.isdigit()]))
                v['serialNumber'] = 'SAT' + serialNumber0

                # SeaBird: sensor type inferred from calibration map
                sensorType = calibrationMap[k].sensorType

                # cal/char tags are created based on serial number and char. type (e.g. STRAY) for each sensor type (e.g. ES)
                if sensorType in  ['LI', 'LT']:
                    ConfigFile.settings['neededCalCharsFRM'][sensorType] = ['%s_%s' % (v['serialNumber'], c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'POLAR']]
                elif sensorType == 'ES':
                    ConfigFile.settings['neededCalCharsFRM'][sensorType] = ['%s_%s' % (v['serialNumber'], c) for c in ['RADCAL', 'STRAY', 'THERMAL', 'ANGULAR']]

        elif ConfigFile.settings['SensorType'] == 'Dalec':
            # TODO
            # Not yet implemented, and not needed for now, as FRM regimes are not available still for DALEC.
            pass

        if ConfigFile.settings['SensorType'] == 'Dalec':
            # FRM regimes not yet implemented, forcing factory mode.
            ConfigFile.settings["fL1bCal"] == 1


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
                "    Sensor-Specific cal/char files with uncertainties in FidRadDB format required" )
        self.ClassCalRadioButton.setAutoExclusive(False)
        self.ClassCalRadioButton.clicked.connect(self.ClassCalRadioButtonClicked)

         # Full
        self.FullCalRadioButton = QtWidgets.QRadioButton(
            "FRM Sensor-Specific characterisations (highest quality)\n"
                "    Sensor-Specific calibrations with uncertainties in FidRadDB format required")
        self.FullCalRadioButton.setAutoExclusive(False)
        self.FullCalRadioButton.clicked.connect(self.FullCalRadioButtonClicked)

        # Disable FRM regimes for DALEC for the moment.
        if ConfigFile.settings['SensorType'].lower() == 'dalec':
            self.ClassCalRadioButton.setDisabled(True)
            self.FullCalRadioButton.setDisabled(True)

        # Define which radio button is checked at initialisation
        if ConfigFile.settings["fL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
        elif ConfigFile.settings["fL1bCal"] == 2:
            self.ClassCalRadioButton.setChecked(True)
        elif ConfigFile.settings["fL1bCal"] == 3:
            self.FullCalRadioButton.setChecked(True)

        # Check completeness of calibration directory according to selected cal/char regime
        FidRadDB_link = '<a href="https://ocdb.eumetsat.int/docs/fidrad-database.html">FidRadDB-formatted</a>'
        CalLabel2 = QtWidgets.QLabel("Checking for required {FidRadDB_link} cal/char files:", self)
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

        CalLabel2cES = QtWidgets.QLabel("       Es:", self)
        # CalLabel2cES_font = CalLabel2cES.font()
        # CalLabel2cES_font.setPointSize(9)
        # CalLabel2cES_font.setBold(False)
        # CalLabel2cES.setFont(CalLabel2cES_font)

        CalLabel2cLT = QtWidgets.QLabel("       Lt:", self)
        # CalLabel2cLT_font = CalLabel2cLT.font()
        # CalLabel2cLT_font.setPointSize(9)
        # CalLabel2cLT_font.setBold(False)
        # CalLabel2cLT.setFont(CalLabel2cLT_font)

        CalLabel2cLI = QtWidgets.QLabel("       Li:", self)
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

    def ThermalStatusUpdate(self):
        if ConfigFile.settings['SensorType'].lower() == 'trios': # G1
            self.ThermistorRadioButton.setDisabled(True)
            if ConfigFile.settings["fL1bThermal"] == 1:
                # NOTE: This will need to be changed for G2
                ConfigFile.settings["fL1bThermal"] == 2 # Fallback in case of corrupted config
                self.AirTempRadioButton.setChecked(True)
                self.ThermistorRadioButton.setChecked(False)
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
            for sensorType, files in ConfigFile.settings['neededCalCharsFRM'].items():
                # Check for all files required for the given sensor in full FRM regime
                # missingFullFRM0 = [f for f in files if len(glob.glob(os.path.join(Path(ConfigFile.getCalibrationDirectory()), '*%s*.[tT][xX][tT]' % f))) == 0]
                missingFullFRM0 = [f for f in files if len(glob.glob(os.path.join(Path(self.path_FidRadDB), '*%s*.[tT][xX][tT]' % f))) == 0]
                missingFullFRM = None
                if fL1bCal == 2:
                    # Keep only the RADCALs
                    missingFullFRM = [f for f in missingFullFRM0 if f.split('_')[-1] == 'RADCAL']
                elif fL1bCal == 3:
                    missingFullFRM = missingFullFRM0

                # Output missing files
                if len(missingFullFRM)>0:
                    missingFilesStrings[sensorType] = 'Missing files: %s' % ' '.join(missingFullFRM)
                    missingFilesList = missingFilesList + missingFullFRM

        # Update line edits
        self.FidRadDBcalCharDirCheckES.setText(missingFilesStrings['ES'])
        self.FidRadDBcalCharDirCheckLT.setText(missingFilesStrings['LT'])
        self.FidRadDBcalCharDirCheckLI.setText(missingFilesStrings['LI'])

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

        # Attempt connection to OCDB/FidRadDB
        try:
            api = new_api(server_url='https://ocdb.eumetsat.int')
        except:
            print('Unable to connect to FidRadDB.')

        # Check if files are already in local FidRadDB repository
        # If not download them first to local FidRadDB repository
        # Then, copy them to calPath
        # Loop over missing files according to cal_char type and serial number...
        for serialNumber_calCharType in missingFilesList:

            # Attempt listing of files available in OCDB/FidRadDB
            try:
                cal_char_files_remote = OCDBApi.fidrad_list_files(api, serialNumber_calCharType)
                cal_char_files_remote = [os.path.basename(file) for file in cal_char_files_remote]
            except:
                print('File %s not available at FidRadDB (https://ocdb.eumetsat.int) or not reachable.')
                cal_char_files_remote = []
            else:
                print('File(s) found at FidRadDB (https://ocdb.eumetsat.int) for tag %s.' % serialNumber_calCharType)

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
                    try:
                        OCDBApi.fidrad_download_file(api, file, self.path_FidRadDB)
                    except:
                        print('Unable to download file %s from FidRadDB. Maybe file does not exist. '
                              'Also check your internet connection, if problem persists, provide cal/char file manually.')
                    else:
                        print('File %s successfully downloaded from FidRadDB' % file)

                # # If existing in local FidRadDB repo and not in sel.calibrationPath, then attempt copying file...
                # if os.path.exists(dest_FidRadDB_local) and not os.path.exists(dest_CalPath):
                #     try:
                #         shutil.copy(dest_FidRadDB_local, dest_CalPath)
                #     except:
                #         print(f'Could not copy {os.path.basename(file)} to {ConfigFile.getCalibrationDirectory()}. Check permissions, and try manually ...')
                #     else:
                #         print(f'{os.path.basename(file)} copied to {ConfigFile.getCalibrationDirectory()} from {self.path_FidRadDB}')

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
            calFileStr = "3 pre-calibration"
        elif option_cal_char_file == 'postCal':
            calFileStr = "3 post-calibration"
        elif option_cal_char_file in 'chooseCal':
            calFileStr = "3 calibration"

        # Collect file paths from selected files...
        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,  # parent window
            f"Select {calFileStr} files",  # dialog title
            self.path_FidRadDB,  # starting directory (empty string means current dir)
            "RADCAL text files (*RADCAL*.txt);;All Files (*)",  # file filter
            options=QtWidgets.QFileDialog.Options())

        # Then filter for files containing "RADCAL" in their name
        file_paths = [os.path.basename(f) for f in file_paths if "RADCAL" in os.path.basename(f)]

        # Initialise status flag and string
        selectCorrect = True
        selectCorrectStr = ''

        # Iterate over sensor type and expected RADCALS....
        for sensorType, calcharFiles in ConfigFile.settings['neededCalCharsFRM'].items():

            # Select only rad cals
            radcalStr = [f for f in calcharFiles if 'RADCAL' in f][0]

            # Check if selected files match the RADCAL tag (format CP_serialNumber_RADCAL_date.txt)
            calChar0 = [f for f in file_paths if '_'.join(f.split('_')[1:-1]) == radcalStr]

            # Check correctness of selection
            if len(calChar0) == 0: # files missing
                selectCorrectStr = selectCorrectStr + '%s: Missing RADCAL. ' % sensorType
                selectCorrect = False
                ConfigFile.settings['%s_%s' % (option_cal_char_file, sensorType)] = None
            elif len(calChar0) > 1: # multiple RADCALS for same sensor were selected
                selectCorrectStr = selectCorrectStr + '%s: select only one RADCAL. ' % sensorType
                selectCorrect = False
                ConfigFile.settings['%s_%s' % (option_cal_char_file, sensorType)] = None
            else:
                ConfigFile.settings['%s_%s' % (option_cal_char_file, sensorType)] = calChar0[0]

        # If incorrectly selected, raise warning...
        if selectCorrect:
            selectCorrectStr = 'Correctly selected'
        else:
            QtWidgets.QMessageBox.warning(None, "No match", "Please select 3 RADCAL files one for each sensor (Es, Li and Lt): <br><br> %s" % selectCorrectStr)

        # Update message in line edits
        if option_cal_char_file == 'preCal':
            self.PreCalLineEdit.setText(selectCorrectStr)
        elif option_cal_char_file == 'postCal':
            self.PostCalLineEdit.setText(selectCorrectStr)
        elif option_cal_char_file in 'chooseCal':
            self.ChooseCalLineEdit.setText(selectCorrectStr)

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
        _, missingFilesList = self.missing_FidRadDB_cal_char_files(ConfigFile.settings['fL1bCal'])
        if len(missingFilesList) != 0:
            # WARNING
            QtWidgets.QMessageBox.warning(None, "No match", "Missing FidRadDB cal/char files:<br>%s<br>"
                                                            "<br>Please copy them to %s from local source or FidRadDB (https://ocdb.eumetsat.int)." % ('<br>'.join(missingFilesList), ConfigFile.getCalibrationDirectory()))

            closeFlag = False

        # Checks if missing multi. cal selections, if yes, raise a warning
        if ConfigFile.settings['MultiCal'] == 1:
            pre_postCal_complete = True
            for multiCalOpt in ['preCal', 'postCal']:
                for sensorType in ['ES', 'LT', 'LI']:
                    # RADCAL filename instead if selected in Source/CalCharWindow.py options.
                    if not ConfigFile.settings['%s_%s' % (multiCalOpt, sensorType)]:
                        pre_postCal_complete = False

            if not pre_postCal_complete:
                QtWidgets.QMessageBox.warning(None, "Missing files", "If mean of pre- and post-calibration selected, please select all 3 pre-cal and 3 post-cal files!")
                closeFlag = False
        elif ConfigFile.settings['MultiCal'] == 2:
            chooseCal_complete = True
            for multiCalOpt in ['chooseCal']:
                for sensorType in ['ES', 'LT', 'LI']:
                    # RADCAL filename instead if selected in Source/CalCharWindow.py options.
                    if not ConfigFile.settings['%s_%s' % (multiCalOpt, sensorType)]:
                        chooseCal_complete = False

            if not chooseCal_complete:
                QtWidgets.QMessageBox.warning(None, "Missing files", "If 'specific calibration' selected, please select all 3 targeted calibration files!")
                closeFlag = False

        # If no warnings raised, then close window...
        if closeFlag:
            print("Cal/char - Save/Close Pressed")
            self.close()

    def cancelButtonPressed(self):
        print("Cal/char - Cancel Pressed")
        self.close()
