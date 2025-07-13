import os
from PyQt5 import QtWidgets

from Source.SeaBASSHeader import SeaBASSHeader
from Source.AncillaryReader import AncillaryReader
from Source.ConfigFile import ConfigFile
from Source.MainConfig import MainConfig


class SeaBASSHeaderWindow(QtWidgets.QDialog):
    def __init__(self, name, inputDir, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.name = name
        self.inputDirectory = inputDir
        # print(self.inputDirectory)
        self.initUI()
        # self.outputDirectory = outputDirectory

    def initUI(self):
        # print("ConfigWindow - initUI")
        #self.label = QtWidgets.QLabel("Popup", self)

        # intValidator = QtGui.QIntValidator()
        # doubleValidator = QtGui.QDoubleValidator()

        self.nameLabel = QtWidgets.QLabel(f'Editing: {self.name}', self)
        linkSeaBASSLabel = QtWidgets.QLabel(
            "Separate multiple entries with commas, and replace spaces with underscores. For input assistance, go to \
            <a href=\"https://seabass.gsfc.nasa.gov/wiki/metadataheaders\"> SeaBASS Metadata Headers</a>")
        linkSeaBASSLabel.setOpenExternalLinks(True)

        instructionLabel = QtWidgets.QLabel("Separate multiple entries with commas, and replace spaces with underscores.")
        instructionLabel_font = instructionLabel.font()
        instructionLabel_font.setPointSize(10)
        instructionLabel_font.setBold(True)
        instructionLabel.setFont(instructionLabel_font)

        versionLabel = QtWidgets.QLabel("SeaBASS submission verion (e.g. 'R1', 'R2')", self)
        self.versionLineEdit = QtWidgets.QLineEdit(self)
        self.versionLineEdit.setText(str(SeaBASSHeader.settings["version"]))

        instructionLabel1 = QtWidgets.QLabel(" ENTRIES NOT IN BOLD BELOW CAN BE CAPTURED FROM")
        instructionLabel1a = QtWidgets.QLabel(" THE ANCILLARY SEABASS FILE AND CONFIGURATION")
        instructionLabel1_font = instructionLabel1.font()
        instructionLabel1_font.setPointSize(10)
        instructionLabel1_font.setBold(True)
        instructionLabel1.setFont(instructionLabel1_font)
        instructionLabel1a_font = instructionLabel1a.font()
        instructionLabel1a_font.setPointSize(10)
        instructionLabel1a_font.setBold(True)
        instructionLabel1a.setFont(instructionLabel1a_font)

        instructionLabelSub = QtWidgets.QLabel("To match fields to existing SeaBASS entries,")
        instructionLabelSub1 = QtWidgets.QLabel(
            "check the 'Lists' pull-down menu<a href=\"https://seabass.gsfc.nasa.gov\"> here</a>.")
        instructionLabelSub1.setOpenExternalLinks(True)


        investigatorsLabel = QtWidgets.QLabel("Investigators", self)
        self.investigatorsLineEdit = QtWidgets.QLineEdit(self)
        self.investigatorsLineEdit.setText(str(SeaBASSHeader.settings["investigators"]))

        affiliationsLabel = QtWidgets.QLabel("affiliations", self)
        self.affiliationsLineEdit = QtWidgets.QLineEdit(self)
        self.affiliationsLineEdit.setText(str(SeaBASSHeader.settings["affiliations"]))

        contactLabel = QtWidgets.QLabel("contact", self)
        self.contactLineEdit = QtWidgets.QLineEdit(self)
        self.contactLineEdit.setText(str(SeaBASSHeader.settings["contact"]))

        experimentLabel = QtWidgets.QLabel("experiment", self)
        self.experimentLineEdit = QtWidgets.QLineEdit(self)
        self.experimentLineEdit.setText(str(SeaBASSHeader.settings["experiment"]))

        cruiseLabel = QtWidgets.QLabel("cruise", self)
        self.cruiseLineEdit = QtWidgets.QLineEdit(self)
        self.cruiseLineEdit.setText(str(SeaBASSHeader.settings["cruise"]))

        stationLabel = QtWidgets.QLabel("station (RAW filename if blank)", self)
        self.stationLineEdit = QtWidgets.QLineEdit(self)
        self.stationLineEdit.setText(str(SeaBASSHeader.settings["station"]))

        platformLabel = QtWidgets.QLabel("platform/ship", self)
        platformLabel_font = platformLabel.font()
        platformLabel_font.setBold(True)
        platformLabel.setFont(platformLabel_font)
        self.platformLineEdit = QtWidgets.QLineEdit(self)
        try:
            self.platformLineEdit.setText(str(SeaBASSHeader.settings["platform"]))
        except Exception:
            SeaBASSHeader.settings["platform"] = ''
            self.platformLineEdit.setText(str(SeaBASSHeader.settings["platform"]))


        documentsLabel = QtWidgets.QLabel("documents", self)
        documentsLabel_font = documentsLabel.font()
        documentsLabel_font.setBold(True)
        documentsLabel.setFont(documentsLabel_font)
        self.documentsLineEdit = QtWidgets.QLineEdit(self)
        self.documentsLineEdit.setText(str(SeaBASSHeader.settings["documents"]))

        instrument_manufacturerLabel = QtWidgets.QLabel("instrument_manufacturer", self)
        instrument_manufacturerLabel_font = instrument_manufacturerLabel.font()
        instrument_manufacturerLabel_font.setBold(True)
        instrument_manufacturerLabel.setFont(instrument_manufacturerLabel_font)
        self.instrument_manufacturerLineEdit = QtWidgets.QLineEdit(self)
        self.instrument_manufacturerLineEdit.setText(str(SeaBASSHeader.settings["instrument_manufacturer"]))

        instrument_modelLabel = QtWidgets.QLabel("instrument_model", self)
        instrument_modelLabel_font = instrument_modelLabel.font()
        instrument_modelLabel_font.setBold(True)
        instrument_modelLabel.setFont(documentsLabel_font)
        self.instrument_modelLineEdit = QtWidgets.QLineEdit(self)
        self.instrument_modelLineEdit.setText(str(SeaBASSHeader.settings["instrument_model"]))

        calibration_dateLabel = QtWidgets.QLabel("calibration_date (YYYYMMDD)", self)
        self.calibration_dateLineEdit = QtWidgets.QLineEdit(self)
        self.calibration_dateLineEdit.setText(str(SeaBASSHeader.settings["calibration_date"]))

        # These will always be refreshed from the ConfigFile
        SeaBASSHeader.refreshCalibrationFiles()
        calibration_filesLabel = QtWidgets.QLabel("calibration_files", self)
        self.calibration_filesLineEdit = QtWidgets.QLineEdit(self)
        self.calibration_filesLineEdit.setText(str(SeaBASSHeader.settings["calibration_files"]))

        data_typeLabel = QtWidgets.QLabel("data_type", self)
        self.data_typeLineEdit = QtWidgets.QLineEdit(self)
        self.data_typeLineEdit.setText(str(SeaBASSHeader.settings["data_type"]))

        data_statusLabel = QtWidgets.QLabel("data_status (e.g. preliminary)", self)
        data_statusLabel_font = data_statusLabel.font()
        data_statusLabel_font.setBold(True)
        data_statusLabel.setFont(data_statusLabel_font)
        self.data_statusLineEdit = QtWidgets.QLineEdit(self)
        self.data_statusLineEdit.setText(str(SeaBASSHeader.settings["data_status"]))

        water_depthLabel = QtWidgets.QLabel("water_depth (use -9999 for missing)", self)
        water_depthLabel_font = water_depthLabel.font()
        water_depthLabel_font.setBold(True)
        water_depthLabel.setFont(water_depthLabel_font)
        self.water_depthLineEdit = QtWidgets.QLineEdit(self)
        self.water_depthLineEdit.setText(str(SeaBASSHeader.settings["water_depth"]))

        measurement_depthLabel = QtWidgets.QLabel("measurement_depth", self)
        measurement_depthLabel_font = measurement_depthLabel.font()
        measurement_depthLabel_font.setBold(True)
        measurement_depthLabel.setFont(measurement_depthLabel_font)
        self.measurement_depthLineEdit = QtWidgets.QLineEdit(self)
        self.measurement_depthLineEdit.setText(str(SeaBASSHeader.settings["measurement_depth"]))

        cloud_percentLabel = QtWidgets.QLabel("cloud_percent", self)
        cloud_percentLabel_font = cloud_percentLabel.font()
        cloud_percentLabel_font.setBold(True)
        cloud_percentLabel.setFont(cloud_percentLabel_font)
        self.cloud_percentLineEdit = QtWidgets.QLineEdit(self)
        self.cloud_percentLineEdit.setText(str(SeaBASSHeader.settings["cloud_percent"]))

        wave_heightLabel = QtWidgets.QLabel("wave_height", self)
        wave_heightLabel_font = wave_heightLabel.font()
        wave_heightLabel_font.setBold(True)
        wave_heightLabel.setFont(wave_heightLabel_font)
        self.wave_heightLineEdit = QtWidgets.QLineEdit(self)
        self.wave_heightLineEdit.setText(str(SeaBASSHeader.settings["wave_height"]))

        secchi_depthLabel = QtWidgets.QLabel("secchi_depth", self)
        secchi_depthLabel_font = secchi_depthLabel.font()
        secchi_depthLabel_font.setBold(True)
        secchi_depthLabel.setFont(secchi_depthLabel_font)
        self.secchi_depthLineEdit = QtWidgets.QLineEdit(self)
        self.secchi_depthLineEdit.setText(str(SeaBASSHeader.settings["secchi_depth"]))
        # self.secchi_depthLineEdit.setValidator(doubleValidator)

        #############################
        commentsLabel = QtWidgets.QLabel("Config Comments (lead with !)", self)
        self.commentsLineEdit = QtWidgets.QTextEdit(self)
        self.commentsLineEdit.setPlainText(SeaBASSHeader.settings["comments"])

        self.configUpdateButton = QtWidgets.QPushButton("Update from Config Window")
        self.configUpdateButton.clicked.connect(lambda: self.configUpdateButtonPressed( 'local'))

        other_commentsLabel = QtWidgets.QLabel("Other Comments", self)
        other_commentsLabel2 = QtWidgets.QLabel("(lead with !)", self)
        self.other_commentsLineEdit = QtWidgets.QTextEdit(self)
        self.other_commentsLineEdit.setPlainText(SeaBASSHeader.settings["other_comments"])

        #############################
        instructionLabel2 = QtWidgets.QLabel(" ENTRIES BELOW ARE EXTRACTED FROM CONFIGURATION AND DATA")
        instructionLabel2_font = instructionLabel2.font()
        instructionLabel2_font.setPointSize(10)
        instructionLabel2_font.setBold(True)
        instructionLabel2.setFont(instructionLabel2_font)

        data_file_nameLabel = QtWidgets.QLabel("data_file_name", self)
        self.data_file_nameLineEdit = QtWidgets.QLineEdit(self)
        self.data_file_nameLineEdit.setText(str(SeaBASSHeader.settings["data_file_name"]))

        original_file_nameLabel = QtWidgets.QLabel("original_file_name", self)
        self.original_file_nameLineEdit = QtWidgets.QLineEdit(self)
        self.original_file_nameLineEdit.setText(str(SeaBASSHeader.settings["original_file_name"]))

        start_dateLabel = QtWidgets.QLabel("start_date (RAW data should be in GMT)", self)
        self.start_dateLineEdit = QtWidgets.QLineEdit(self)
        self.start_dateLineEdit.setText(str(SeaBASSHeader.settings["start_date"]))

        end_dateLabel = QtWidgets.QLabel("end_date [GMT]", self)
        self.end_dateLineEdit = QtWidgets.QLineEdit(self)
        self.end_dateLineEdit.setText(str(SeaBASSHeader.settings["end_date"]))

        start_timeLabel = QtWidgets.QLabel("start_time [GMT]", self)
        self.start_timeLineEdit = QtWidgets.QLineEdit(self)
        self.start_timeLineEdit.setText(str(SeaBASSHeader.settings["start_time"]))

        end_timeLabel = QtWidgets.QLabel("end_time [GMT]", self)
        self.end_timeLineEdit = QtWidgets.QLineEdit(self)
        self.end_timeLineEdit.setText(str(SeaBASSHeader.settings["end_time"]))

        north_latitudeLabel = QtWidgets.QLabel("north_latitude [dec deg]", self)
        self.north_latitudeLineEdit = QtWidgets.QLineEdit(self)
        self.north_latitudeLineEdit.setText(str(SeaBASSHeader.settings["north_latitude"]))
        # self.north_latitudeLineEdit.setValidator(doubleValidator)

        south_latitudeLabel = QtWidgets.QLabel("south_latitude", self)
        self.south_latitudeLineEdit = QtWidgets.QLineEdit(self)
        self.south_latitudeLineEdit.setText(str(SeaBASSHeader.settings["south_latitude"]))
        # self.south_latitudeLineEdit.setValidator(doubleValidator)

        east_longitudeLabel = QtWidgets.QLabel("east_longitude", self)
        self.east_longitudeLineEdit = QtWidgets.QLineEdit(self)
        self.east_longitudeLineEdit.setText(str(SeaBASSHeader.settings["east_longitude"]))
        # self.east_longitudeLineEdit.setValidator(doubleValidator)

        west_longitudeLabel = QtWidgets.QLabel("west_longitude", self)
        self.west_longitudeLineEdit = QtWidgets.QLineEdit(self)
        self.west_longitudeLineEdit.setText(str(SeaBASSHeader.settings["west_longitude"]))
        # self.west_longitudeLineEdit.setValidator(doubleValidator)

        wind_speedLabel = QtWidgets.QLabel("wind_speed", self)
        self.wind_speedLineEdit = QtWidgets.QLineEdit(self)
        self.wind_speedLineEdit.setText(str(SeaBASSHeader.settings["wind_speed"]))
        # self.wind_speedLineEdit.setValidator(doubleValidator)

        # No need to include rho, NIR, BRDF fields to override values extracted from data
        ##

        self.openButton = QtWidgets.QPushButton("Open/Copy")
        self.saveButton = QtWidgets.QPushButton("Save")
        self.saveAsButton = QtWidgets.QPushButton("Save As")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

        self.openButton.clicked.connect(self.openButtonPressed)
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.saveAsButton.clicked.connect(self.saveAsButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        # ####################################################################################
        # Whole Window Box
        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(self.nameLabel)
        VBox.addWidget(linkSeaBASSLabel)

        VBox1 = QtWidgets.QVBoxLayout()
        # VBox1.addSpacing(10)

        VBox1.addWidget(instructionLabel1)
        VBox1.addWidget(instructionLabel1a)

        HBoxVersion = QtWidgets.QHBoxLayout()
        HBoxVersion.addWidget(versionLabel)
        HBoxVersion.addWidget(self.versionLineEdit)
        VBox1.addLayout(HBoxVersion)

        VBox1.addWidget(instructionLabelSub)
        VBox1.addWidget(instructionLabelSub1)

        # Horizontal Box
        HBox1 = QtWidgets.QHBoxLayout()
        HBox1.addWidget(investigatorsLabel)
        HBox1.addWidget(self.investigatorsLineEdit)
        VBox1.addLayout(HBox1)

        HBox2 = QtWidgets.QHBoxLayout()
        HBox2.addWidget(affiliationsLabel)
        HBox2.addWidget(self.affiliationsLineEdit)
        VBox1.addLayout(HBox2)

        HBox3 = QtWidgets.QHBoxLayout()
        HBox3.addWidget(contactLabel)
        HBox3.addWidget(self.contactLineEdit)
        VBox1.addLayout(HBox3)

        HBox4 = QtWidgets.QHBoxLayout()
        HBox4.addWidget(experimentLabel)
        HBox4.addWidget(self.experimentLineEdit)
        VBox1.addLayout(HBox4)

        HBox5 = QtWidgets.QHBoxLayout()
        HBox5.addWidget(cruiseLabel)
        HBox5.addWidget(self.cruiseLineEdit)
        VBox1.addLayout(HBox5)

        platformHBox = QtWidgets.QHBoxLayout()
        platformHBox.addWidget(platformLabel)
        platformHBox.addWidget(self.platformLineEdit)
        VBox1.addLayout(platformHBox)

        HBox9 = QtWidgets.QHBoxLayout()
        HBox9.addWidget(documentsLabel)
        HBox9.addWidget(self.documentsLineEdit)
        VBox1.addLayout(HBox9)

        HBox27 = QtWidgets.QHBoxLayout()
        HBox27.addWidget(instrument_manufacturerLabel)
        HBox27.addWidget(self.instrument_manufacturerLineEdit)
        VBox1.addLayout(HBox27)

        HBox28 = QtWidgets.QHBoxLayout()
        HBox28.addWidget(instrument_modelLabel)
        HBox28.addWidget(self.instrument_modelLineEdit)
        VBox1.addLayout(HBox28)

        HBox29 = QtWidgets.QHBoxLayout()
        HBox29.addWidget(calibration_dateLabel)
        HBox29.addWidget(self.calibration_dateLineEdit)
        VBox1.addLayout(HBox29)

        HBox10 = QtWidgets.QHBoxLayout()
        HBox10.addWidget(calibration_filesLabel)
        HBox10.addWidget(self.calibration_filesLineEdit)
        VBox1.addLayout(HBox10)

        HBox11 = QtWidgets.QHBoxLayout()
        HBox11.addWidget(data_typeLabel)
        HBox11.addWidget(self.data_typeLineEdit)
        VBox1.addLayout(HBox11)

        HBox12 = QtWidgets.QHBoxLayout()
        HBox12.addWidget(data_statusLabel)
        HBox12.addWidget(self.data_statusLineEdit)
        VBox1.addLayout(HBox12)

        HBox21 = QtWidgets.QHBoxLayout()
        HBox21.addWidget(water_depthLabel)
        HBox21.addWidget(self.water_depthLineEdit)
        VBox1.addLayout(HBox21)

        HBox22 = QtWidgets.QHBoxLayout()
        HBox22.addWidget(measurement_depthLabel)
        HBox22.addWidget(self.measurement_depthLineEdit)
        VBox1.addLayout(HBox22)

        HBox23 = QtWidgets.QHBoxLayout()
        HBox23.addWidget(cloud_percentLabel)
        HBox23.addWidget(self.cloud_percentLineEdit)
        VBox1.addLayout(HBox23)

        HBox25 = QtWidgets.QHBoxLayout()
        HBox25.addWidget(wave_heightLabel)
        HBox25.addWidget(self.wave_heightLineEdit)
        VBox1.addLayout(HBox25)

        HBox31 = QtWidgets.QHBoxLayout()
        HBox31.addWidget(secchi_depthLabel)
        HBox31.addWidget(self.secchi_depthLineEdit)
        VBox1.addLayout(HBox31)
        ##############
        VBox2 = QtWidgets.QVBoxLayout()
        #############

        VBox2.addWidget(instructionLabel2)

        HBoxSub = QtWidgets.QHBoxLayout()
        VBoxSub = QtWidgets.QVBoxLayout()

        VBoxSub.addWidget(commentsLabel)
        # VBoxSub.addWidget(self.configUpdateButton)
        HBoxSub.addLayout(VBoxSub)

        HBoxSub.addWidget(self.commentsLineEdit)

        # HBoxSub.addLayout(VBoxSub)

        VBox2.addLayout(HBoxSub)

        ############
        HBox30 = QtWidgets.QHBoxLayout()
        HBox30.addWidget(other_commentsLabel)
        HBox30.addWidget(other_commentsLabel2)
        HBox30.addWidget(self.other_commentsLineEdit)
        VBox2.addLayout(HBox30)

        # VBox1.addSpacing(20)


        HBox6 = QtWidgets.QHBoxLayout()
        HBox6.addWidget(stationLabel)
        HBox6.addWidget(self.stationLineEdit)
        VBox2.addLayout(HBox6)

        HBox7 = QtWidgets.QHBoxLayout()
        HBox7.addWidget(data_file_nameLabel)
        HBox7.addWidget(self.data_file_nameLineEdit)
        VBox2.addLayout(HBox7)

        HBox8 = QtWidgets.QHBoxLayout()
        HBox8.addWidget(original_file_nameLabel)
        HBox8.addWidget(self.original_file_nameLineEdit)
        VBox2.addLayout(HBox8)

        HBox13 = QtWidgets.QHBoxLayout()
        HBox13.addWidget(start_dateLabel)
        HBox13.addWidget(self.start_dateLineEdit)
        VBox2.addLayout(HBox13)

        HBox14 = QtWidgets.QHBoxLayout()
        HBox14.addWidget(end_dateLabel)
        HBox14.addWidget(self.end_dateLineEdit)
        VBox2.addLayout(HBox14)

        HBox15 = QtWidgets.QHBoxLayout()
        HBox15.addWidget(start_timeLabel)
        HBox15.addWidget(self.start_timeLineEdit)
        VBox2.addLayout(HBox15)

        HBox16 = QtWidgets.QHBoxLayout()
        HBox16.addWidget(end_timeLabel)
        HBox16.addWidget(self.end_timeLineEdit)
        VBox2.addLayout(HBox16)

        HBox17 = QtWidgets.QHBoxLayout()
        HBox17.addWidget(north_latitudeLabel)
        HBox17.addWidget(self.north_latitudeLineEdit)
        VBox2.addLayout(HBox17)

        HBox18 = QtWidgets.QHBoxLayout()
        HBox18.addWidget(south_latitudeLabel)
        HBox18.addWidget(self.south_latitudeLineEdit)
        VBox2.addLayout(HBox18)

        HBox19 = QtWidgets.QHBoxLayout()
        HBox19.addWidget(east_longitudeLabel)
        HBox19.addWidget(self.east_longitudeLineEdit)
        VBox2.addLayout(HBox19)

        HBox20 = QtWidgets.QHBoxLayout()
        HBox20.addWidget(west_longitudeLabel)
        HBox20.addWidget(self.west_longitudeLineEdit)
        VBox2.addLayout(HBox20)

        HBox24 = QtWidgets.QHBoxLayout()
        HBox24.addWidget(wind_speedLabel)
        HBox24.addWidget(self.wind_speedLineEdit)
        VBox2.addLayout(HBox24)


        # Add 3 Vertical Boxes to Horizontal Box hBox
        hBox = QtWidgets.QHBoxLayout()
        hBox.addLayout(VBox1)
        hBox.addLayout(VBox2)

        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.openButton)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.saveAsButton)
        saveHBox.addWidget(self.cancelButton)

        # Adds hBox and saveHBox to primary VBox
        VBox.addLayout(hBox)
        VBox.addLayout(saveHBox)

        self.setLayout(VBox)
        self.setGeometry(300, 100, 0, 0)
        self.setWindowTitle('Edit SeaBASS Header')


    def configUpdateButtonPressed(self, caller):
        print("Updating SeaBASS Header comments from values in ConfigFile")
        # This will update subsequently from the ConfigFile on demand

        # First try to fill left column metadata headers using the Ancillary fill if provided.
        #   Only when opening, not when saving 
        if caller == 'config1' and not os.environ["HYPERINSPACE_CMD"].lower() == 'true': # os.environ must be string
            fp = MainConfig.settings["ancFile"]
            if not os.path.isfile(fp):
                print("Specified ancillary file not found: " + fp)
            else:
                metaHeaders = AncillaryReader.readAncillaryHeader(fp)
                for key,value in metaHeaders.items():
                    # The ancillary file may cover a whole cruise, so only use the general metadata, not the specific
                    omitList = ['data_file_name','calibration_files','data_status','station','documents','start_date','end_date',\
                                'north_latitude','south_latitude','east_longitude','west_longitude','start_time','end_time',\
                                    'measurement_depth','water_depth','fields','units']
                    if key in SeaBASSHeader.settings and \
                        (SeaBASSHeader.settings[key] == '' or SeaBASSHeader.settings[key] == 'temp') \
                            and key not in omitList:
                        SeaBASSHeader.settings[key] = value

        SeaBASSHeader.settings['instrument_manufacturer'] = ConfigFile.settings['SensorType']
        if ConfigFile.settings['SensorType'].lower() == 'trios':
            SeaBASSHeader.settings['instrument_model'] = 'RAMSES'
        if ConfigFile.settings['SensorType'].lower() == 'seabird':
            SeaBASSHeader.settings['instrument_model'] = 'HyperOCR'
        if ConfigFile.settings['SensorType'].lower() == 'dalec':
            SeaBASSHeader.settings['instrument_model'] = 'DALEC'

        # NOTE: Need to capture the calibration date for the SeaBASS file header
        
        if ConfigFile.settings["bL1aqcCleanPitchRoll"]:
            pitchRollFilt = "On"
        else:
            pitchRollFilt = "Off"
        if ConfigFile.settings["bL1aqcRotatorAngle"]:
            cleanRotFilt = "On"
        else:
            cleanRotFilt = "Off"
        if ConfigFile.settings["bL1aqcCleanSunAngle"]:
            cleanRelAzFilt = "On"
        else:
            cleanRelAzFilt = "Off"
        if ConfigFile.settings["bL1aqcDeglitch"]:
            deglitchFilt = "On"
        else:
            deglitchFilt = "Off"

        if ConfigFile.settings['fL1bCal'] == 1:
            if ConfigFile.settings['SensorType'].lower() == 'seabird':
                FRMRegime = 'Non-FRM_Class-based'
            else:
                FRMRegime = 'Factory_Calibration'
        elif ConfigFile.settings['fL1bCal'] == 2:
            FRMRegime = 'FRM_Class-based'
        elif ConfigFile.settings['fL1bCal'] == 3:
            FRMRegime = 'FRM-Full-Characterization'
        else:
            FRMRegime = None

        if ConfigFile.settings['fL1bThermal'] == 1:
            ThermalSource = 'Internal_Thermistor'
        elif ConfigFile.settings['fL1bThermal'] == 2:
            ThermalSource = 'Air_Termperature'
        elif ConfigFile.settings['fL1bThermal'] == 3:
            ThermalSource = 'Caps_On_Dark_File'
        else:
            ThermalSource = None

        if ConfigFile.settings["bL1bqcEnableSpecQualityCheck"]:
            specFilt = "On"
        else:
            specFilt = "Off"
        if ConfigFile.settings["bL1bqcEnableQualityFlags"]:
            metFilt = "On"
        else:
            metFilt = "Off"
        if ConfigFile.settings["bL2EnablePercentLt"]:
            ltFilt = "On"
        else:
            ltFilt = "Off"
        if ConfigFile.settings["bL23CRho"]:
            SeaBASSHeader.settings["rho_correction"] = '3C'
        elif ConfigFile.settings["bL2ZhangRho"]:
            SeaBASSHeader.settings["rho_correction"] = 'Z17'
        else:
            SeaBASSHeader.settings["rho_correction"] = 'M99'
        if ConfigFile.settings["bL2PerformNIRCorrection"]:
            if ConfigFile.settings["bL2SimpleNIRCorrection"]:
                SeaBASSHeader.settings["NIR_residual_correction"] = 'MA95'
            else:
                SeaBASSHeader.settings["NIR_residual_correction"] = 'R06'
        else:
            SeaBASSHeader.settings["NIR_residual_correction"] = 'NA'

        if ConfigFile.settings["bL2BRDF"]:
            if ConfigFile.settings["bL2BRDF_fQ"]:
                # Morel 2002
                SeaBASSHeader.settings["BRDF_correction"] = 'M02'
            elif ConfigFile.settings["bL2BRDF_IOP"]:
                # Lee 2011
                SeaBASSHeader.settings["BRDF_correction"] = 'L11'
            elif ConfigFile.settings["bL2BRDF_O23"]:
                # Pitarch 2025
                SeaBASSHeader.settings["BRDF_correction"] = 'O23'
            # elif ConfigFile.settings["bL2BRDF_OXX"]:
            #     # Lee 2011 adapted by D'Allimonte et al.
            #     SeaBASSHeader.settings["BRDF_correction"] = 'Rrs:OXX,Lwnex:OXX'
        else:
            SeaBASSHeader.settings["BRDF_correction"] = 'noBRDF'

        if ConfigFile.settings["bL2NegativeSpec"]:
            NegativeFilt = "On"
        else:
            NegativeFilt = "Off"

        if os.environ["HYPERINSPACE_CMD"].lower() == 'true': #os.environs must be strings
            MainConfig.loadConfig('cmdline_main.config','version')
        else:
            MainConfig.loadConfig('main.config','version')
        SeaBASSHeader.settings["comments"] =\
            f'! HyperInSPACE vers = {MainConfig.settings["version"]}\n'+\
            f'! HyperInSPACE Config = {ConfigFile.filename}\n'+\
            f'! Rotator Home Angle = {ConfigFile.settings["fL1aqcRotatorHomeAngle"]}\n'+\
            f'! Rotator Delay = {ConfigFile.settings["fL1aqcRotatorDelay"]}\n'+\
            f'! Pitch/Roll Filter = {pitchRollFilt}\n'+\
            f'! Max Pitch/Roll = {ConfigFile.settings["fL1aqcPitchRollPitch"]}\n'+\
            f'! Rotator Min/Max Filter = {cleanRotFilt}\n'+\
            f'! Rotator Min = {ConfigFile.settings["fL1aqcRotatorAngleMin"]}\n'+\
            f'! Rotator Max = {ConfigFile.settings["fL1aqcRotatorAngleMax"]}\n'+\
            f'! Rel Azimuth Filter = {cleanRelAzFilt}\n'+\
            f'! Rel Azimuth Min = {ConfigFile.settings["fL1aqcSunAngleMin"]}\n'+\
            f'! Rel Azimuth Max = {ConfigFile.settings["fL1aqcSunAngleMax"]}\n'+\
            f'! Deglitch Filter = {deglitchFilt}\n'+\
            f'! ES Dark Window = {ConfigFile.settings["fL1aqcESWindowDark"]}\n'+\
            f'! ES Light Window = {ConfigFile.settings["fL1aqcESWindowLight"]}\n'+\
            f'! ES Dark Sigma = {ConfigFile.settings["fL1aqcESSigmaDark"]}\n'+\
            f'! ES Light Sigma = {ConfigFile.settings["fL1aqcESSigmaLight"]}\n'+\
            f'! LI Dark Window = {ConfigFile.settings["fL1aqcLIWindowDark"]}\n'+\
            f'! LI Light Window = {ConfigFile.settings["fL1aqcLIWindowLight"]}\n'+\
            f'! LI Dark Sigma = {ConfigFile.settings["fL1aqcLISigmaDark"]}\n'+\
            f'! LI Light Sigma = {ConfigFile.settings["fL1aqcLISigmaLight"]}\n'+\
            f'! LT Dark Window = {ConfigFile.settings["fL1aqcLTWindowDark"]}\n'+\
            f'! LT Light Window = {ConfigFile.settings["fL1aqcLTWindowLight"]}\n'+\
            f'! LT Dark Sigma = {ConfigFile.settings["fL1aqcLTSigmaDark"]}\n'+\
            f'! LT Light Sigma = {ConfigFile.settings["fL1aqcLTSigmaLight"]}\n'+\
            f'! FRM Pathway = {FRMRegime}\n'+\
            f'! Thermal Source = {ThermalSource}\n'+\
            f'! Default Salt = {ConfigFile.settings["fL1bDefaultSalt"]}\n'+\
            f'! Default SST = {ConfigFile.settings["fL1bDefaultSST"]}\n'+\
            f'! Default AOD = {ConfigFile.settings["fL1bDefaultAOD"]}\n'+\
            f'! Default Wind = {ConfigFile.settings["fL1bDefaultWindSpeed"]}\n'+\
            f'! Default AirTemp = {ConfigFile.settings["fL1bDefaultAirT"]}\n'+\
            f'! Wavelength Interp Int = {ConfigFile.settings["fL1bInterpInterval"]}\n'+\
            f'! Max Wind = {ConfigFile.settings["fL1bqcMaxWind"]}\n'+\
            f'! Min SZA = {ConfigFile.settings["fL1bqcSZAMin"]}\n'+\
            f'! Max SZA = {ConfigFile.settings["fL1bqcSZAMax"]}\n'+\
            f'! Spectral Filter = {specFilt}\n'+\
            f'! Filter Sigma Es = {ConfigFile.settings["fL1bqcSpecFilterEs"]}\n'+\
            f'! Filter Sigma Li = {ConfigFile.settings["fL1bqcSpecFilterLi"]}\n'+\
            f'! Filter Sigma Lt = {ConfigFile.settings["fL1bqcSpecFilterLt"]}\n'+\
            f'! Meteorological Filter = {metFilt}\n'+\
            f'! Cloud Flag = {ConfigFile.settings["fL1bqcCloudFlag"]}\n'+\
            f'! Es Flag = {ConfigFile.settings["fL1bqcSignificantEsFlag"]}\n'+\
            f'! Dawn/Dusk Flag = {ConfigFile.settings["fL1bqcDawnDuskFlag"]}\n'+\
            f'! Rain/Humidity Flag = {ConfigFile.settings["fL1bqcRainfallHumidityFlag"]}\n'+\
            f'! Ensemble Interval = {ConfigFile.settings["fL2TimeInterval"]}\n'+\
            f'! Percent Lt Filter = {ltFilt}\n'+\
            f'! Percent Light = {ConfigFile.settings["fL2PercentLt"]}\n'+\
            f'! Remove Negatives = {NegativeFilt}'
            # f'! Processing DateTime = {time.asctime()}'

        if caller == 'local':
            self.commentsLineEdit.setPlainText(SeaBASSHeader.settings["comments"])
            self.commentsLineEdit.update()

        # print(SeaBASSHeader.settings["comments"])

    def openButtonPressed(self):
        print('SeaBASSHeaderWindow - Open/Copy Pressed')

        # fileToCopy, ok = QtWidgets.QInputDialog.getText(self, 'Save As SeaBASS Header File', 'Enter File Name')
        caption =  "Select .hdr File to Copy"
        directory = "Config"
        fpfToCopy, ok = QtWidgets.QFileDialog.getOpenFileNames(self,caption,directory,filter="*.hdr")
        (_, fileToCopy) = os.path.split(fpfToCopy[0])
        if ok:
            print("Copying SeaBASS Header: ", fileToCopy)
            SeaBASSHeader.loadSeaBASSHeader(fileToCopy)

            # How to refresh...
            self.name = fileToCopy
            SeaBASSHeaderWindow.refreshWindow(self)


    def saveButtonPressed(self):
        print("SeaBASSHeaderWindow - Save Pressed")

        SeaBASSHeader.settings["version"] = self.versionLineEdit.text()
        SeaBASSHeader.settings["investigators"] = self.investigatorsLineEdit.text()
        SeaBASSHeader.settings["affiliations"] = self.affiliationsLineEdit.text()
        SeaBASSHeader.settings["contact"] = self.contactLineEdit.text()
        SeaBASSHeader.settings["experiment"] = self.experimentLineEdit.text()
        SeaBASSHeader.settings["cruise"] = self.cruiseLineEdit.text()
        SeaBASSHeader.settings["station"] = self.stationLineEdit.text()
        SeaBASSHeader.settings["platform"] = self.platformLineEdit.text()

        SeaBASSHeader.settings["documents"] = self.documentsLineEdit.text()
        SeaBASSHeader.settings["calibration_files"] = self.calibration_filesLineEdit.text()
        SeaBASSHeader.settings["data_type"] = self.data_typeLineEdit.text()
        SeaBASSHeader.settings["data_status"] = self.data_statusLineEdit.text()
        SeaBASSHeader.settings["water_depth"] = self.water_depthLineEdit.text()
        SeaBASSHeader.settings["measurement_depth"] = self.measurement_depthLineEdit.text()
        SeaBASSHeader.settings["cloud_percent"] = self.cloud_percentLineEdit.text()
        SeaBASSHeader.settings["wave_height"] = self.wave_heightLineEdit.text()
        SeaBASSHeader.settings["secchi_depth"] = self.secchi_depthLineEdit.text()

        SeaBASSHeader.settings["instrument_manufacturer"] = self.instrument_manufacturerLineEdit.text()
        SeaBASSHeader.settings["instrument_model"] = self.instrument_modelLineEdit.text()
        SeaBASSHeader.settings["calibration_date"] = self.calibration_dateLineEdit.text()

        SeaBASSHeader.settings["data_file_name"] = self.data_file_nameLineEdit.text()
        SeaBASSHeader.settings["original_file_name"] = self.original_file_nameLineEdit.text()
        SeaBASSHeader.settings["start_date"] = self.start_dateLineEdit.text()
        SeaBASSHeader.settings["end_date"] = self.end_dateLineEdit.text()
        SeaBASSHeader.settings["start_time"] = self.start_timeLineEdit.text()
        SeaBASSHeader.settings["end_time"] = self.end_timeLineEdit.text()

        SeaBASSHeader.settings["north_latitude"] = self.north_latitudeLineEdit.text()
        SeaBASSHeader.settings["south_latitude"] = self.south_latitudeLineEdit.text()
        SeaBASSHeader.settings["east_longitude"] = self.east_longitudeLineEdit.text()
        SeaBASSHeader.settings["west_longitude"] = self.west_longitudeLineEdit.text()
        SeaBASSHeader.settings["wind_speed"] = self.wind_speedLineEdit.text()

        SeaBASSHeader.settings["comments"] = self.commentsLineEdit.toPlainText()
        SeaBASSHeader.settings["other_comments"] = self.other_commentsLineEdit.toPlainText()

        SeaBASSHeader.saveSeaBASSHeader(self.name)
        # print(SeaBASSHeader.settings["comments"])
        ConfigFile.settings["seaBASSHeaderFileName"] = self.name

        # QtWidgets.QMessageBox.about(self, "Edit SeaBASSHeader File", "SeaBASSHeader File Saved")
        ConfigFile.saveConfig(ConfigFile.filename)
        self.close()

    def refreshWindow(self):
        print("SeaBASSHeaderWindow - refreshWindow")
        self.nameLabel.setText(f'Editing: {self.name}')
        self.versionLineEdit.setText(str(SeaBASSHeader.settings["version"]))
        self.investigatorsLineEdit.setText(str(SeaBASSHeader.settings["investigators"]))
        self.affiliationsLineEdit.setText(str(SeaBASSHeader.settings["affiliations"]))
        self.contactLineEdit.setText(str(SeaBASSHeader.settings["contact"]))
        self.experimentLineEdit.setText(str(SeaBASSHeader.settings["experiment"]))
        self.cruiseLineEdit.setText(str(SeaBASSHeader.settings["cruise"]))
        self.stationLineEdit.setText(str(SeaBASSHeader.settings["station"]))
        self.platformLineEdit.setText(str(SeaBASSHeader.settings["platform"]))
        self.documentsLineEdit.setText(str(SeaBASSHeader.settings["documents"]))
        self.instrument_manufacturerLineEdit.setText(str(SeaBASSHeader.settings["instrument_manufacturer"]))
        self.instrument_modelLineEdit.setText(str(SeaBASSHeader.settings["instrument_model"]))
        self.calibration_dateLineEdit.setText(str(SeaBASSHeader.settings["calibration_date"]))
        self.commentsLineEdit.setPlainText(SeaBASSHeader.settings["comments"])
        self.other_commentsLineEdit.setText(SeaBASSHeader.settings["other_comments"])

    def saveAsButtonPressed(self):
        print("ConfigWindow - Save As Pressed")
        self.name, ok = QtWidgets.QInputDialog.getText(self, 'Save As SeaBASS Header File', 'Enter File Name')
        if ok:

            if not self.name.endswith(".hdr"):
                self.name = self.name + ".hdr"
            print("Create SeaBASS Header: ", self.name)

            self.nameLabel.update()
            SeaBASSHeaderWindow.saveButtonPressed(self)
            ConfigFile.settings["seaBASSHeaderFileName"] = self.name

    def cancelButtonPressed(self):
        print("SeaBASSWindow - Cancel Pressed")
        self.close()