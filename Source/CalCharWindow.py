from PyQt5 import QtWidgets

from Source.ConfigFile import ConfigFile
import os
import glob
import shutil
from pathlib import Path
from Source import PATH_TO_CONFIG
from ocdb.api.OCDBApi import new_api, OCDBApi

class CalCharWindow(QtWidgets.QDialog):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.setModal(True)
        self.initUI()

    def initUI(self):

        calibrationDir = os.path.splitext(self.name)[0] + "_Calibration"
        self.calibrationPath = os.path.join(PATH_TO_CONFIG, calibrationDir)

        ''' Initialize the GUIs '''

        l1bCalLabel = QtWidgets.QLabel(" Select Calibration-Characterization Regime:", self)

        l1bCalLabel_font = l1bCalLabel.font()
        l1bCalLabel_font.setPointSize(12)
        l1bCalLabel_font.setBold(True)
        l1bCalLabel.setFont(l1bCalLabel_font)


        self.DefaultCalRadioButton = QtWidgets.QRadioButton("non-FRM: Factory calibration only (no uncertainties)")
        self.DefaultCalRadioButton.setAutoExclusive(False)

        self.DefaultCalRadioButton.clicked.connect(self.l1bDefaultCalRadioButtonClicked)


        self.ClassCalRadioButton = QtWidgets.QRadioButton("FRM standard: Class-specific characterisation coefficients will be used (available in /Data/Class_Based_Characterizations/%s)"
                                                          "\n NB: Sensor-specific calibrations with uncertainties in the FidRadDB format required" % ConfigFile.settings['SensorType'])
        self.ClassCalRadioButton.setAutoExclusive(False)

        self.l1bClassRadio1 = QtWidgets.QRadioButton("Local", self)
        self.addClassFilesButton = QtWidgets.QPushButton("Add calibration files:")
        # self.addClassFilesButton.clicked.connect(self.l1bChooseCalFiles('only_cal'))
        self.classFilesLineEdit = QtWidgets.QLineEdit(self)
        self.classFilesLineEdit.setDisabled(True)
        self.l1bClassRadio2 = QtWidgets.QRadioButton("FidRadDB", self)
        l1bClassFidRadDBLabel = QtWidgets.QLabel("Calibration files will be downloaded into /Data/FidRadDB/%s" % ConfigFile.settings['SensorType'], self)

        self.ClassCalRadioButton.clicked.connect(self.l1bClassCalRadioButtonClicked)

        self.l1bClassRadio1.clicked.connect(self.l1bRadioUpdate1)
        self.l1bClassRadio2.clicked.connect(self.l1bRadioUpdate2)


        self.FullCalRadioButton = QtWidgets.QRadioButton("FRM highest quality: Sensor-specific characterisation coefficients will be used "
                                                         "\n NB: Sensor-specific calibrations with uncertainties and characterizations in the FidRadDB format required")
        self.FullCalRadioButton.setAutoExclusive(False)
        self.l1bFRMRadio1 = QtWidgets.QRadioButton("Local", self)
        self.addFullFilesButton = QtWidgets.QPushButton("Add cal./char. files:")
        # self.addFullFilesButton.clicked.connect(self.l1bChooseCalFiles('cal_char'))
        self.fullFilesLineEdit = QtWidgets.QLineEdit(self)
        self.fullFilesLineEdit.setDisabled(True)

        self.l1bFRMRadio2 = QtWidgets.QRadioButton("FidRadDB", self)
        l1bFidRadDBLabel = QtWidgets.QLabel("Cal./char. files will be downloaded into /Data/FidRadDB/%s" % ConfigFile.settings['SensorType'], self)

        self.FullCalRadioButton.clicked.connect(self.l1bFullCalRadioButtonClicked)

        self.FullCalDir = ConfigFile.settings['FullCalDir']
        self.l1bFRMRadio1.clicked.connect(self.l1bRadioUpdate1)
        self.l1bFRMRadio2.clicked.connect(self.l1bRadioUpdate2)


        if ConfigFile.settings["bL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
        elif ConfigFile.settings["bL1bCal"] == 2:
            self.ClassCalRadioButton.setChecked(True)
        elif ConfigFile.settings["bL1bCal"] == 3:
            self.FullCalRadioButton.setChecked(True)

        if ConfigFile.settings['FidRadDB']:
            self.l1bFRMRadio1.setChecked(False)
            self.l1bClassRadio1.setChecked(False)
            self.l1bFRMRadio2.setChecked(True)
            self.l1bClassRadio2.setChecked(True)
        else:
            self.l1bFRMRadio1.setChecked(True)
            self.l1bClassRadio1.setChecked(True)
            self.l1bFRMRadio2.setChecked(False)
            self.l1bClassRadio2.setChecked(False)


        l1bCalLabel2 = QtWidgets.QLabel("Multiple calibrations for each sensor? Select option:", self)

        l1bCalLabel2_font = l1bCalLabel2.font()
        l1bCalLabel2_font.setPointSize(12)
        l1bCalLabel2_font.setBold(True)
        l1bCalLabel2.setFont(l1bCalLabel2_font)

        self.calFileMostRecent = QtWidgets.QRadioButton("Use most recent calibration prior to acquisition time (default)")
        self.calFileMostRecent.setAutoExclusive(False)
        self.calFileMostRecent.clicked.connect(lambda: self.l1bMultiCalOptions('most_recent'))

        self.calFilePrePost = QtWidgets.QRadioButton("Use mean of pre- and post- calibrations")
        self.calFilePrePost.setAutoExclusive(False)
        self.calFilePrePost.clicked.connect(lambda: self.l1bMultiCalOptions('pre_post'))

        self.addPreCalButton = QtWidgets.QPushButton("Choose (3) pre-cal files:")
        self.addPreCalButton.clicked.connect(lambda: self.l1bChooseCalFiles('pre_cal'))
        self.PreCalLineEdit = QtWidgets.QLineEdit(self)
        self.PreCalLineEdit.setDisabled(True)

        self.addPostCalButton = QtWidgets.QPushButton("Choose (3) post-cal files:")
        self.addPostCalButton.clicked.connect(lambda: self.l1bChooseCalFiles('post_cal'))
        self.PostCalLineEdit = QtWidgets.QLineEdit(self)
        self.PostCalLineEdit.setDisabled(True)

        self.calFileChoose = QtWidgets.QRadioButton("Use specific calibration files")
        self.calFileChoose.setAutoExclusive(False)
        self.calFileChoose.clicked.connect(lambda: self.l1bMultiCalOptions('choose'))

        self.addChooseCalButton = QtWidgets.QPushButton("Choose (3) cal files:")
        self.addChooseCalButton.clicked.connect(lambda: self.l1bChooseCalFiles('choose_cal'))
        self.ChooseCalLineEdit = QtWidgets.QLineEdit(self)
        self.ChooseCalLineEdit.setDisabled(True)

        self.saveButton = QtWidgets.QPushButton("Save/Close")
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        self.l1bCalStatusUpdate()
        self.l1bMultiCalOptions('most_recent')


        #####################################################################################

        VBox = QtWidgets.QVBoxLayout()

        VBox2 = QtWidgets.QVBoxLayout()

        #   Instrument/Cal Files
        VBox2.addWidget(l1bCalLabel)
        # CalHBox2 = QtWidgets.QHBoxLayout()
        # CalHBox2.addWidget(self.DefaultCalRadioButton)
        VBox2.addWidget(self.DefaultCalRadioButton)
        # CalHBox2 = QtWidgets.QHBoxLayout()
        # CalHBox2.addStretch()
        # CalHBox2.addWidget(self.DefaultCalRadioButtonTriOS)
        # CalHBox2.addWidget(self.DefaultCalRadioButtonSeaBird)
        # VBox2.addLayout(CalHBox2)

        VBox2.addWidget(self.ClassCalRadioButton)
        CalHBox3 = QtWidgets.QHBoxLayout()
        CalHBox3.addStretch()
        CalHBox3.addWidget(self.l1bClassRadio1)
        CalHBox3.addWidget(self.addClassFilesButton)
        CalHBox3.addWidget(self.classFilesLineEdit)
        CalHBox3.addStretch()
        # CalHBox5.addStretch(1)
        VBox2.addLayout(CalHBox3)

        CalHBox4 = QtWidgets.QHBoxLayout()
        CalHBox4.addStretch()
        CalHBox4.addWidget(self.l1bClassRadio2)
        CalHBox4.addWidget(l1bClassFidRadDBLabel)
        CalHBox4.addStretch()
        VBox2.addLayout(CalHBox4)

        VBox2.addWidget(self.FullCalRadioButton)
        CalHBox5 = QtWidgets.QHBoxLayout()
        CalHBox5.addStretch()
        CalHBox5.addWidget(self.l1bFRMRadio1)
        CalHBox5.addWidget(self.addFullFilesButton)
        CalHBox5.addWidget(self.fullFilesLineEdit)
        CalHBox5.addStretch()
        # CalHBox5.addStretch(1)
        VBox2.addLayout(CalHBox5)


        CalHBox6 = QtWidgets.QHBoxLayout()
        CalHBox6.addStretch()
        CalHBox6.addWidget(self.l1bFRMRadio2)
        CalHBox6.addWidget(l1bFidRadDBLabel)
        CalHBox6.addStretch()
        VBox2.addLayout(CalHBox6)

        VBox2.addWidget(l1bCalLabel2)

        VBox2.addWidget(self.calFileMostRecent)

        VBox2.addWidget(self.calFilePrePost)
        CalHBox7 = QtWidgets.QHBoxLayout()
        CalHBox7.addStretch()
        CalHBox7.addWidget(self.addPreCalButton)
        CalHBox7.addWidget(self.PreCalLineEdit)
        CalHBox7.addWidget(self.addPostCalButton)
        CalHBox7.addWidget(self.PostCalLineEdit)
        CalHBox7.addStretch()
        VBox2.addLayout(CalHBox7)

        VBox2.addWidget(self.calFileChoose)
        CalHBox8 = QtWidgets.QHBoxLayout()
        CalHBox8.addStretch()
        CalHBox8.addWidget(self.addChooseCalButton)
        CalHBox8.addWidget(self.ChooseCalLineEdit)
        CalHBox8.addStretch()
        VBox2.addLayout(CalHBox8)

        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.cancelButton)

        # Adds hBox and saveHBox to primary VBox
        VBox2.addLayout(saveHBox)

        # Add 3 Vertical Boxes to Horizontal Box hBox
        hBox = QtWidgets.QHBoxLayout()
        hBox.addLayout(VBox2)

        VBox.addLayout(hBox)
        self.setLayout(VBox)

        self.setGeometry(100, 100, 0, 0)

        self.setWindowTitle('Cal./char. options')

    #####################################################################################

    def l1bChooseCalFiles(self,option_cal_char_file):

        print("ConfigWindow - Add/update cal/char files")

        self.RadCalDir = self.calibrationPath
        print('Radiometric characterization directory changed: ', self.RadCalDir)

        ConfigFile.settings['RadCalDir'] = self.RadCalDir
        # self.l1bCalStatusUpdate()

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
                "Select %s files" % calFileStr,  # dialog title
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

    def l1bCalStatusUpdate(self):
        # Enable/disable features based on regime selected
        if ConfigFile.settings["bL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
            self.ClassCalRadioButton.setChecked(False)
            self.FullCalRadioButton.setChecked(False)

            self.addClassFilesButton.setDisabled(True)
            self.l1bFRMRadio1.setDisabled(True)
            self.l1bClassRadio1.setDisabled(True)
            self.l1bFRMRadio2.setDisabled(True)
            self.l1bClassRadio2.setDisabled(True)
            self.addFullFilesButton.setDisabled(True)

            self.calFileMostRecent.setDisabled(True)
            self.calFilePrePost.setDisabled(True)
            self.calFileChoose.setDisabled(True)

            self.addPreCalButton.setDisabled(True)
            self.addPostCalButton.setDisabled(True)
            self.addChooseCalButton.setDisabled(True)

        elif ConfigFile.settings["bL1bCal"] == 2:
            self.DefaultCalRadioButton.setChecked(False)
            self.ClassCalRadioButton.setChecked(True)
            self.FullCalRadioButton.setChecked(False)

            self.addClassFilesButton.setDisabled(False)
            self.l1bFRMRadio1.setDisabled(True)
            self.l1bClassRadio1.setDisabled(False)
            self.l1bFRMRadio2.setDisabled(True)
            self.l1bClassRadio2.setDisabled(False)
            self.addFullFilesButton.setDisabled(True)

            self.calFileMostRecent.setDisabled(False)
            self.calFilePrePost.setDisabled(False)
            self.calFileChoose.setDisabled(False)

            self.addPreCalButton.setDisabled(False)
            self.addPostCalButton.setDisabled(False)
            self.addChooseCalButton.setDisabled(False)

        elif ConfigFile.settings["bL1bCal"] == 3:
            self.DefaultCalRadioButton.setChecked(False)
            self.ClassCalRadioButton.setChecked(False)
            self.FullCalRadioButton.setChecked(True)

            self.addClassFilesButton.setDisabled(True)
            self.l1bFRMRadio1.setDisabled(False)
            self.l1bClassRadio1.setDisabled(True)
            self.l1bFRMRadio2.setDisabled(False)
            self.l1bClassRadio2.setDisabled(True)
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

    def l1bDefaultCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Factory")
        ConfigFile.settings["bL1bCal"] = 1
        self.l1bCalStatusUpdate()

    def l1bClassCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Class-based")
        ConfigFile.settings["bL1bCal"] = 2
        self.l1bCalStatusUpdate()

    def l1bFullCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Instrument-specific FRM")
        ConfigFile.settings["bL1bCal"] = 3
        self.l1bCalStatusUpdate()

    def l1bRadioUpdate1(self):
        print("ConfigWindow - l1bFRMRadioUpdate local files")
        if self.l1bFRMRadio1.isChecked():
            self.l1bFRMRadio2.setChecked(False)
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

    def l1bRadioUpdate2(self):
        print("ConfigWindow - l1bFRMRadioUpdate FidRadDB")
        if self.l1bFRMRadio2.isChecked():
            self.l1bFRMRadio1.setChecked(False)
            ConfigFile.settings['FidRadDB'] = 1
            api = new_api(server_url='https://ocdb.eumetsat.int')

            ##### SERIAL NUMBERS...
            if ConfigFile.settings['SensorType'] ==  'TriOS':
                serialNumbers = [sn.split('.ini')[0] for sn in ConfigFile.settings['CalibrationFiles'].keys()]
            elif ConfigFile.settings['SensorType'] == 'SeaBird':
                serialNumbers = ['SAT' + sn[3:7] for sn in ConfigFile.settings['CalibrationFiles'].keys() if sn.endswith('.cal')]
            else:
                ValueError('Only implemented for TriOS... and SeaBird')

            for sn in serialNumbers:
                cal_char_files = OCDBApi.fidrad_list_files(api, sn)
                for cal_char_file in cal_char_files:
                    try:
                        OCDBApi.fidrad_download_file(api, cal_char_file, '/tcenas/home/gossn')
                    except:
                        raise ConnectionError('Unable to download file from FidRadDB. Check your internet connection. '
                                              'If problem persists, provide cal/char file manually.')

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
        self.l1bCalStatusUpdate()

    def l1bMultiCalOptions(self,option_multical):

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