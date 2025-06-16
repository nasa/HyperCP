''' GUI for the selection of L1B calibration and characterization configuration. '''
import os
import glob
import shutil
from pathlib import Path
from PyQt5 import QtWidgets

from ocdb.api.OCDBApi import new_api, OCDBApi

from Source.ConfigFile import ConfigFile
from Source import PATH_TO_CONFIG


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
        self.ClassRadio1 = QtWidgets.QRadioButton("Local", self)
        self.addClassFilesButton = QtWidgets.QPushButton("Add calibration files:")
        self.classFilesLineEdit = QtWidgets.QLineEdit(self)
        self.classFilesLineEdit.setDisabled(True)
        self.ClassRadio2 = QtWidgets.QRadioButton("FidRadDB", self)
        ClassFidRadDBLabel = QtWidgets.QLabel(f"Calibration files will be downloaded into /Data/FidRadDB/{ConfigFile.settings['SensorType']}", self)
        self.ClassCalRadioButton.clicked.connect(self.ClassCalRadioButtonClicked)
        self.ClassRadio1.clicked.connect(self.RadioUpdate1)
        self.ClassRadio2.clicked.connect(self.RadioUpdate2)

        # Full
        self.FullCalRadioButton = QtWidgets.QRadioButton("FRM Sensor-Specific characterisation coefficients will be used (highest quality)"
                                                         "\n NB: Sensor-specific calibrations with uncertainties and characterizations in the FidRadDB format required")
        self.FullCalRadioButton.setAutoExclusive(False)
        self.FRMRadio1 = QtWidgets.QRadioButton("Local", self)
        self.addFullFilesButton = QtWidgets.QPushButton("Add Cal/Char files:")
        # self.addFullFilesButton.clicked.connect(self.ChooseCalFiles('cal_char'))
        self.fullFilesLineEdit = QtWidgets.QLineEdit(self)
        self.fullFilesLineEdit.setDisabled(True)
        self.FRMRadio2 = QtWidgets.QRadioButton("FidRadDB", self)
        FidRadDBLabel = QtWidgets.QLabel(f"Cal/Char files will be downloaded into /Data/FidRadDB/{ConfigFile.settings['SensorType']}", self)
        self.FullCalRadioButton.clicked.connect(self.FullCalRadioButtonClicked)
        self.FullCalDir = ConfigFile.settings['FullCalDir']
        self.FRMRadio1.clicked.connect(self.RadioUpdate1)
        self.FRMRadio2.clicked.connect(self.RadioUpdate2)

        if ConfigFile.settings["fL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
        elif ConfigFile.settings["fL1bCal"] == 2:
            self.ClassCalRadioButton.setChecked(True)
        elif ConfigFile.settings["fL1bCal"] == 3:
            self.FullCalRadioButton.setChecked(True)

        if ConfigFile.settings['FidRadDB']:
            self.FRMRadio1.setChecked(False)
            self.ClassRadio1.setChecked(False)
            self.FRMRadio2.setChecked(True)
            self.ClassRadio2.setChecked(True)
        else:
            self.FRMRadio1.setChecked(True)
            self.ClassRadio1.setChecked(True)
            self.FRMRadio2.setChecked(False)
            self.ClassRadio2.setChecked(False)

        CalLabel2 = QtWidgets.QLabel("Multiple calibrations for each sensor (FRM regimes only)? Select option:", self)

        CalLabel2_font = CalLabel2.font()
        CalLabel2_font.setPointSize(12)
        CalLabel2_font.setBold(True)
        CalLabel2.setFont(CalLabel2_font)

        self.calFileMostRecent = QtWidgets.QRadioButton("Use most recent calibration prior to acquisition time (default)")
        self.calFileMostRecent.setAutoExclusive(False)
        self.calFileMostRecent.clicked.connect(lambda: self.MultiCalOptions('most_recent'))

        self.calFilePrePost = QtWidgets.QRadioButton("Use mean of pre- and post- calibrations (1 each for DALEC, 3 for TriOS, 6 for SeaBird)")
        self.calFilePrePost.setAutoExclusive(False)
        self.calFilePrePost.clicked.connect(lambda: self.MultiCalOptions('pre_post'))

        self.addPreCalButton = QtWidgets.QPushButton("Choose pre-cal files:")
        self.addPreCalButton.clicked.connect(lambda: self.ChooseCalFiles('pre_cal'))
        self.PreCalLineEdit = QtWidgets.QLineEdit(self)
        self.PreCalLineEdit.setDisabled(True)

        self.addPostCalButton = QtWidgets.QPushButton("Choose post-cal files:")
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

        self.CalStatusUpdate()
        self.MultiCalOptions('most_recent')

        #####################################################################################

        VBox = QtWidgets.QVBoxLayout()

        # Thermal Source
        VBox.addWidget(ThermalLabel)
        ThermalHBox = QtWidgets.QHBoxLayout()
        ThermalHBox.addStretch()
        ThermalHBox.addWidget(self.ThermistorRadioButton)
        ThermalHBox.addWidget(self.AirTempRadioButton)
        ThermalHBox.addWidget(self.CapsOnFileRadioButton)
        VBox.addLayout(ThermalHBox)

        # Instrument/Cal Files
        VBox.addWidget(CalLabel)

        #   Factory
        VBox.addWidget(self.DefaultCalRadioButton)

        #   Class
        VBox.addWidget(self.ClassCalRadioButton)
        CalHBox1 = QtWidgets.QHBoxLayout()
        CalHBox1.addStretch()
        CalHBox1.addWidget(self.ClassRadio1)
        CalHBox1.addWidget(self.addClassFilesButton)
        CalHBox1.addWidget(self.classFilesLineEdit)
        CalHBox1.addStretch()
        VBox.addLayout(CalHBox1)

        CalHBox2 = QtWidgets.QHBoxLayout()
        CalHBox2.addStretch()
        CalHBox2.addWidget(self.ClassRadio2)
        CalHBox2.addWidget(ClassFidRadDBLabel)
        CalHBox2.addStretch()
        VBox.addLayout(CalHBox2)

        #   Full
        VBox.addWidget(self.FullCalRadioButton)
        CalHBox3 = QtWidgets.QHBoxLayout()
        CalHBox3.addStretch()
        CalHBox3.addWidget(self.FRMRadio1)
        CalHBox3.addWidget(self.addFullFilesButton)
        CalHBox3.addWidget(self.fullFilesLineEdit)
        CalHBox3.addStretch()
        VBox.addLayout(CalHBox3)

        CalHBox4 = QtWidgets.QHBoxLayout()
        CalHBox4.addStretch()
        CalHBox4.addWidget(self.FRMRadio2)
        CalHBox4.addWidget(FidRadDBLabel)
        CalHBox4.addStretch()
        VBox.addLayout(CalHBox4)

        # Multiple calibration files
        VBox.addWidget(CalLabel2)

        #   Most recent
        VBox.addWidget(self.calFileMostRecent)

        #   Pre- Post-
        VBox.addWidget(self.calFilePrePost)
        CalHBox5 = QtWidgets.QHBoxLayout()
        CalHBox5.addStretch()
        CalHBox5.addWidget(self.addPreCalButton)
        CalHBox5.addWidget(self.PreCalLineEdit)
        CalHBox5.addWidget(self.addPostCalButton)
        CalHBox5.addWidget(self.PostCalLineEdit)
        CalHBox5.addStretch()
        VBox.addLayout(CalHBox5)

        #   Choose other
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

    #####################################################################################

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
        elif option_cal_char_file in ['only_cal', 'choose_cal']:
            calFileStr = "3 calibration"
        elif option_cal_char_file == 'cal_char':
            calFileStr = "3 calibration and 9 characterisation"

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
                # Then filter for files containing "ABC" in their name
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

            self.addClassFilesButton.setDisabled(True)
            self.FRMRadio1.setDisabled(True)
            self.ClassRadio1.setDisabled(True)
            self.FRMRadio2.setDisabled(True)
            self.ClassRadio2.setDisabled(True)
            self.addFullFilesButton.setDisabled(True)

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

            self.addClassFilesButton.setDisabled(False)
            self.FRMRadio1.setDisabled(True)
            self.ClassRadio1.setDisabled(False)
            self.FRMRadio2.setDisabled(True)
            self.ClassRadio2.setDisabled(False)
            self.addFullFilesButton.setDisabled(True)

            self.calFileMostRecent.setDisabled(False)
            self.calFilePrePost.setDisabled(False)
            self.calFileChoose.setDisabled(False)

            self.addPreCalButton.setDisabled(False)
            self.addPostCalButton.setDisabled(False)
            self.addChooseCalButton.setDisabled(False)

        elif ConfigFile.settings["fL1bCal"] == 3:
            self.DefaultCalRadioButton.setChecked(False)
            self.ClassCalRadioButton.setChecked(False)
            self.FullCalRadioButton.setChecked(True)

            self.addClassFilesButton.setDisabled(True)
            self.FRMRadio1.setDisabled(False)
            self.ClassRadio1.setDisabled(True)
            self.FRMRadio2.setDisabled(False)
            self.ClassRadio2.setDisabled(True)
            self.addFullFilesButton.setDisabled(False)

            self.calFileMostRecent.setDisabled(False)
            self.calFilePrePost.setDisabled(False)
            self.calFileChoose.setDisabled(False)

            self.addPreCalButton.setDisabled(False)
            self.addPostCalButton.setDisabled(False)
            self.addChooseCalButton.setDisabled(False)

        # Check for RadCal and Full-char files:
        failCode = 0
        # Confirm 3 RADCAL files found in destination
        files = glob.glob(os.path.join(self.calibrationPath, '*RADCAL*.[tT][xX][tT]'))
        if len(files) != 3:
            failCode += 1
            self.classFilesLineEdit.setText("Files not found")
        else:
            self.classFilesLineEdit.setText("Files found")
            ConfigFile.settings['RadCalDir'] = self.calibrationPath
        # Confirm 2 POLAR files found in destination
        files = glob.glob(os.path.join(self.calibrationPath, '*POLAR*.[tT][xX][tT]'))
        if len(files) != 2:
            failCode += 1
        # Confirm 3 STRAY files found in destination
        files = glob.glob(os.path.join(self.calibrationPath, '*STRAY*.[tT][xX][tT]'))
        if len(files) != 3:
            failCode += 1
        # Confirm 3 THERMAL files found in destination
        files = glob.glob(os.path.join(self.calibrationPath, '*THERMAL*.[tT][xX][tT]'))
        if len(files) != 3:
            failCode += 1
        if failCode > 0:
            self.fullFilesLineEdit.setText("Files not found")
        else:
            self.fullFilesLineEdit.setText("Files found")
            ConfigFile.settings['FullCalDir'] = self.calibrationPath

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

    def RadioUpdate1(self):
        print("ConfigWindow - FRMRadioUpdate local files")
        if self.FRMRadio1.isChecked():
            self.FRMRadio2.setChecked(False)
            ConfigFile.settings['FidRadDB'] = 0

    def addFullFilesButtonClicked(self):
        print("ConfigWindow - Add/update full characterization files")
        targetDir = QtWidgets.QFileDialog.getExistingDirectory(self, \
                                                               'Choose Characterization File Directory.',
                                                               ConfigFile.settings['FullCalDir'])

        # Copy full characterization files into calibration folder and test it
        failCode = 0
        # POLAR
        files = glob.iglob(os.path.join(Path(targetDir), '*POLAR*.[tT][xX][tT]'))
        for file in files:
            dest = Path(self.calibrationPath) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {self.calibrationPath}')
                shutil.copy(file, dest)
        # Confirm 2 POLAR files found in destination
        files = glob.glob(os.path.join(self.calibrationPath, '*POLAR*.[tT][xX][tT]'))
        if len(files) != 2:
            failCode += 1
            print(f'Copying of POLAR files failed. {len(files)}/2 POLAR files found in Config folder')

        # RADCAL
        files = glob.iglob(os.path.join(Path(targetDir), '*RADCAL*.[tT][xX][tT]'))
        for file in files:
            dest = Path(self.calibrationPath) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {self.calibrationPath}')
                shutil.copy(file, dest)
        # Confirm 3 RADCAL files found in destination
        files = glob.glob(os.path.join(self.calibrationPath, '*RADCAL*.[tT][xX][tT]'))
        if len(files) != 3:
            failCode += 1
            print(f'Copying of RADCAL files failed. {len(files)}/3 RADCAL files found in Config folder')

        # STRAYLIGHT
        files = glob.iglob(os.path.join(Path(targetDir), '*STRAY*.[tT][xX][tT]'))
        for file in files:
            dest = Path(self.calibrationPath) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {self.calibrationPath}')
                shutil.copy(file, dest)
        # Confirm 3 STRAY files found in destination
        files = glob.glob(os.path.join(self.calibrationPath, '*STRAY*.[tT][xX][tT]'))
        if len(files) != 3:
            failCode += 1
            print(f'Copying of STRAY files failed. {len(files)}/3 STRAY files found in Config folder')

        # THERMAL
        files = glob.iglob(os.path.join(Path(targetDir), '*THERMAL*.[tT][xX][tT]'))
        for file in files:
            dest = Path(self.calibrationPath) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {self.calibrationPath}')
                shutil.copy(file, dest)
        # Confirm 3 THERMAL files found in destination
        files = glob.glob(os.path.join(self.calibrationPath, '*THERMAL*.[tT][xX][tT]'))
        if len(files) != 3:
            failCode += 1
            print(f'Copying of THERMAL files failed. {len(files)}/3 THERMAL files found in Config folder')

        # ANGULAR
        files = glob.iglob(os.path.join(Path(targetDir), '*ANGULAR*.[tT][xX][tT]'))
        for file in files:
            dest = Path(self.calibrationPath) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {self.calibrationPath}')
                shutil.copy(file, dest)
        # Confirm 1 ANGULAR files found in destination
        files = glob.glob(os.path.join(self.calibrationPath, '*ANGULAR*.[tT][xX][tT]'))
        if len(files) != 1:
            failCode += 1
            print(f'Copying of ANGULAR files failed. {len(files)}/1 ANGULAR files found in Config folder')

        if failCode > 0:
            self.fullFilesLineEdit.setText("Files not found")
        else:
            self.fullFilesLineEdit.setText("Files found")

        self.FullCalDir = self.calibrationPath
        print('Full characterization directory changed: ', self.FullCalDir)
        ConfigFile.settings['FullCalDir'] = self.FullCalDir

    def RadioUpdate2(self):
        print("ConfigWindow - FRMRadioUpdate FidRadDB")
        if self.FRMRadio2.isChecked():
            self.FRMRadio1.setChecked(False)
            ConfigFile.settings['FidRadDB'] = 1
            api = new_api(server_url='https://ocdb.eumetsat.int')

            ##### SERIAL NUMBERS...
            if ConfigFile.settings['SensorType'] ==  'TriOS':
                serialNumbers = [sn.split('.ini')[0] for sn in ConfigFile.settings['CalibrationFiles'].keys()]
            elif ConfigFile.settings['SensorType'] == 'SeaBird':
                serialNumbers = ['SAT' + sn[3:7] for sn in ConfigFile.settings['CalibrationFiles'].keys() if sn.endswith('.cal')]
            else:
                print('Only implemented for TriOS... and SeaBird')

            for sn in serialNumbers:
                cal_char_files = OCDBApi.fidrad_list_files(api, sn)
                for cal_char_file in cal_char_files:
                    try:
                        OCDBApi.fidrad_download_file(api, cal_char_file, '/tcenas/home/gossn')
                    except Exception as exc:
                        raise ConnectionError('Unable to download file from FidRadDB. Check your internet connection. '
                                              'If problem persists, provide cal/char file manually.') from exc

    def FullCalDirButtonPressed(self):
        if not ConfigFile.settings['FullCalDir'].startswith('Choose'):
            srcDir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Choose Directory',
                                                                ConfigFile.settings['FullCalDir'])
        else:
            srcDir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Choose Directory')
        print('Full characterization folders selected for copy: ', srcDir)

        calDir = Path(srcDir)
        files = glob.iglob(os.path.join(Path(calDir), '*.[tT][xX][tT]'))
        for file in files:
            dest = Path(self.calibrationPath) / os.path.basename(file)
            if not dest.exists():
                shutil.copy(file, dest)

        ConfigFile.settings['FullCalDir'] = self.calibrationPath
        self.CalStatusUpdate()

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
