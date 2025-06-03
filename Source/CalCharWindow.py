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
        if ConfigFile.settings["bL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
        self.DefaultCalRadioButton.clicked.connect(self.l1bDefaultCalRadioButtonClicked)
        # self.DefaultCalRadioButtonTriOS = QtWidgets.QRadioButton("TriOS")
        # self.DefaultCalRadioButtonSeaBird = QtWidgets.QRadioButton("SeaBird (Non-FRM Class-based)")
        # if CurrentSensor.lower() == 'trios':
        #     self.DefaultCalRadioButtonTriOS.setChecked(True)
        #     self.DefaultCalRadioButtonSeaBird.setChecked(False)
        #     self.DefaultCalRadioButtonSeaBird.setDisabled(True)
        # else:
        #     self.DefaultCalRadioButtonSeaBird.setChecked(True)
        #     self.DefaultCalRadioButtonTriOS.setChecked(False)
        #     self.DefaultCalRadioButtonTriOS.setDisabled(True)

        self.ClassCalRadioButton = QtWidgets.QRadioButton("FRM standard: Class-specific characterisations (calibrations with uncertainties required)")
        self.ClassCalRadioButton.setAutoExclusive(False)
        if ConfigFile.settings["bL1bCal"] == 2:
            self.ClassCalRadioButton.setChecked(True)
        self.ClassCalRadioButton.clicked.connect(self.l1bClassCalRadioButtonClicked)
        self.addClassFilesButton = QtWidgets.QPushButton("Add cal. files:")
        self.addClassFilesButton.clicked.connect(self.addClassFilesButtonClicked)
        self.classFilesLineEdit = QtWidgets.QLineEdit(self)
        self.classFilesLineEdit.setDisabled(True)

        self.FullCalRadioButton = QtWidgets.QRadioButton("FRM highest quality: Sensor-specific characterisation (cal./char. with uncertainties required)")
        self.FullCalRadioButton.setAutoExclusive(False)
        self.l1bFRMRadio1 = QtWidgets.QRadioButton("Local", self)
        self.addFullFilesButton = QtWidgets.QPushButton("Add cal./char. files:")
        self.addFullFilesButton.clicked.connect(self.addFullFilesButtonClicked)
        self.fullFilesLineEdit = QtWidgets.QLineEdit(self)
        self.fullFilesLineEdit.setDisabled(True)

        self.l1bFRMRadio2 = QtWidgets.QRadioButton("FidRadDB", self)
        l1bFidRadDBLabel = QtWidgets.QLabel("Cal./char. files will be downloaded", self)
        if ConfigFile.settings['FidRadDB']:
            self.l1bFRMRadio1.setChecked(False)
            self.l1bFRMRadio2.setChecked(True)
        else:
            self.l1bFRMRadio1.setChecked(True)
            self.l1bFRMRadio2.setChecked(False)

        if ConfigFile.settings["bL1bCal"] == 3:
            self.FullCalRadioButton.setChecked(True)
            if int(ConfigFile.settings["FidRadDB"]) == 0:
                self.l1bFRMRadio1.setChecked(True)
                self.l1bFRMRadio2.setChecked(False)
            elif int(ConfigFile.settings["FidRadDB"]) == 1:
                self.l1bFRMRadio1.setChecked(False)
                self.l1bFRMRadio2.setChecked(True)
        self.FullCalRadioButton.clicked.connect(self.l1bFullCalRadioButtonClicked)

        self.FullCalDir = ConfigFile.settings['FullCalDir']
        self.l1bFRMRadio1.clicked.connect(self.l1bFRMRadioUpdate1)
        self.l1bFRMRadio2.clicked.connect(self.l1bFRMRadioUpdate2)


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
        CalHBox3.addWidget(self.addClassFilesButton)
        CalHBox3.addWidget(self.classFilesLineEdit)
        CalHBox3.addStretch()
        VBox2.addLayout(CalHBox3)
        # VBox2.addLayout(CalHBox2)

        VBox2.addWidget(self.FullCalRadioButton)
        CalHBox4 = QtWidgets.QHBoxLayout()
        CalHBox4.addStretch()
        CalHBox4.addWidget(self.l1bFRMRadio1)
        CalHBox4.addWidget(self.addFullFilesButton)
        CalHBox4.addWidget(self.fullFilesLineEdit)
        CalHBox4.addStretch()
        # CalHBox4.addStretch(1)
        VBox2.addLayout(CalHBox4)
        CalHBox5 = QtWidgets.QHBoxLayout()
        CalHBox5.addStretch()
        CalHBox5.addWidget(self.l1bFRMRadio2)
        CalHBox5.addWidget(l1bFidRadDBLabel)
        CalHBox5.addStretch()
        VBox2.addLayout(CalHBox5)

        VBox2.addWidget(l1bCalLabel2)

        VBox2.addWidget(self.calFileMostRecent)

        VBox2.addWidget(self.calFilePrePost)
        CalHBox6 = QtWidgets.QHBoxLayout()
        CalHBox6.addStretch()
        CalHBox6.addWidget(self.addPreCalButton)
        CalHBox6.addWidget(self.PreCalLineEdit)
        CalHBox6.addWidget(self.addPostCalButton)
        CalHBox6.addWidget(self.PostCalLineEdit)
        CalHBox6.addStretch()
        VBox2.addLayout(CalHBox6)

        VBox2.addWidget(self.calFileChoose)
        CalHBox7 = QtWidgets.QHBoxLayout()
        CalHBox7.addStretch()
        CalHBox7.addWidget(self.addChooseCalButton)
        CalHBox7.addWidget(self.ChooseCalLineEdit)
        CalHBox7.addStretch()
        VBox2.addLayout(CalHBox7)

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

    def l1bCalStatusUpdate(self):
        # Enable/disable features based on regime selected
        if ConfigFile.settings["bL1bCal"] == 1:
            self.DefaultCalRadioButton.setChecked(True)
            self.ClassCalRadioButton.setChecked(False)
            self.FullCalRadioButton.setChecked(False)

            self.addClassFilesButton.setDisabled(True)
            self.l1bFRMRadio1.setDisabled(True)
            self.l1bFRMRadio2.setDisabled(True)
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
            self.l1bFRMRadio2.setDisabled(True)
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
            self.l1bFRMRadio2.setDisabled(False)
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

    def addClassFilesButtonClicked(self):
        print("ConfigWindow - Add/update class-based files")
        targetDir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Choose RADCAL Directory.',
                                                               ConfigFile.settings['RadCalDir'])

        # copy radcal file into configuration folder
        files = glob.iglob(os.path.join(Path(targetDir), '*RADCAL*.[tT][xX][tT]'))
        for file in files:
            dest = Path(self.calibrationPath) / os.path.basename(file)
            if not dest.exists():
                print(f'Copying {os.path.basename(file)} to {self.calibrationPath}')
                shutil.copy(file, dest)

        self.RadCalDir = self.calibrationPath
        print('Radiometric characterization directory changed: ', self.RadCalDir)
        ConfigFile.settings['RadCalDir'] = self.RadCalDir

        self.l1bCalStatusUpdate()

    def l1bFullCalRadioButtonClicked(self):
        print("ConfigWindow - L1b Calibration set to Instrument-specific FRM")
        ConfigFile.settings["bL1bCal"] = 3
        self.l1bCalStatusUpdate()

    def l1bFRMRadioUpdate1(self):
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

    def l1bFRMRadioUpdate2(self):
        print("ConfigWindow - l1bFRMRadioUpdate FidRadDB")
        if self.l1bFRMRadio2.isChecked():
            self.l1bFRMRadio1.setChecked(False)
            ConfigFile.settings['FidRadDB'] = 1


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
    def l1bChooseCalFiles(self,option_multical_file):

        if option_multical_file == 'pre_cal':
            calFileStr = "pre-"
        elif option_multical_file == 'post_cal':
            calFileStr = "post-"
        elif option_multical_file == 'choose_cal':
            calFileStr = ""

        correctSelection = False
        while not correctSelection:
            file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
                self,  # parent window
                "Select 3 %scalibration files" % calFileStr,  # dialog title
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



    def saveButtonPressed(self):
        print("Cal/char - Save/Close Pressed")

        # ConfigFile.products["bL2Prodoc3m"] = int(self.oc3mCheckBox.isChecked())
        # ConfigFile.settings["bL2WeightMODISA"] = 1

        self.close()

    def cancelButtonPressed(self):
        print("Cal/char - Cancel Pressed")
        self.close()