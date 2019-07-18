import os
import shutil
from PyQt5 import QtCore, QtGui, QtWidgets


from SeaBASSHeader import SeaBASSHeader


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

        nameLabel = QtWidgets.QLabel("Editing: " + self.name, self)
        linkSeaBASSLabel = QtWidgets.QLabel("For input assistance, go to \
            <a href=\"https://seabass.gsfc.nasa.gov/wiki/metadataheaders\"> SeaBASS Metadata Headers</a>")
        linkSeaBASSLabel.setOpenExternalLinks(True)                

        instructionLabel = QtWidgets.QLabel("  Separate multiple entries with commas, and replace spaces with underscores.\
            ")
        instructionLabel_font = instructionLabel.font()
        instructionLabel_font.setPointSize(10)
        instructionLabel_font.setBold(True)
        instructionLabel.setFont(instructionLabel_font)

       
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

        stationLabel = QtWidgets.QLabel("station", self)
        self.stationLineEdit = QtWidgets.QLineEdit(self)
        self.stationLineEdit.setText(str(SeaBASSHeader.settings["station"]))

        documentsLabel = QtWidgets.QLabel("documents", self)
        self.documentsLineEdit = QtWidgets.QLineEdit(self)
        self.documentsLineEdit.setText(str(SeaBASSHeader.settings["documents"]))

        # These should be retrieved from the ConfigFile
        calibration_filesLabel = QtWidgets.QLabel("calibration_files", self)
        self.calibration_filesLineEdit = QtWidgets.QLineEdit(self)
        self.calibration_filesLineEdit.setText(str(SeaBASSHeader.settings["calibration_files"]))

        data_typeLabel = QtWidgets.QLabel("data_type", self)
        self.data_typeLineEdit = QtWidgets.QLineEdit(self)
        self.data_typeLineEdit.setText(str(SeaBASSHeader.settings["data_type"]))

        data_statusLabel = QtWidgets.QLabel("data_status", self)
        self.data_statusLineEdit = QtWidgets.QLineEdit(self)
        self.data_statusLineEdit.setText(str(SeaBASSHeader.settings["data_status"]))
        
        water_depthLabel = QtWidgets.QLabel("water_depth", self)
        self.water_depthLineEdit = QtWidgets.QLineEdit(self)
        self.water_depthLineEdit.setText(str(SeaBASSHeader.settings["water_depth"]))

        measurement_depthLabel = QtWidgets.QLabel("measurement_depth", self)
        self.measurement_depthLineEdit = QtWidgets.QLineEdit(self)
        self.measurement_depthLineEdit.setText(str(SeaBASSHeader.settings["measurement_depth"]))

        cloud_percentLabel = QtWidgets.QLabel("cloud_percent", self)
        self.cloud_percentLineEdit = QtWidgets.QLineEdit(self)
        self.cloud_percentLineEdit.setText(str(SeaBASSHeader.settings["cloud_percent"]))
        

        wave_heightLabel = QtWidgets.QLabel("wave_height", self)
        self.wave_heightLineEdit = QtWidgets.QLineEdit(self)
        self.wave_heightLineEdit.setText(str(SeaBASSHeader.settings["wave_height"]))

        instructionLabel2 = QtWidgets.QLabel("  If left blank, the entries below will be extracted from processed files")
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

        start_dateLabel = QtWidgets.QLabel("start_date", self)
        self.start_dateLineEdit = QtWidgets.QLineEdit(self)
        self.start_dateLineEdit.setText(str(SeaBASSHeader.settings["start_date"]))

        end_dateLabel = QtWidgets.QLabel("end_date", self)
        self.end_dateLineEdit = QtWidgets.QLineEdit(self)
        self.end_dateLineEdit.setText(str(SeaBASSHeader.settings["end_date"]))

        start_timeLabel = QtWidgets.QLabel("start_time", self)
        self.start_timeLineEdit = QtWidgets.QLineEdit(self)
        self.start_timeLineEdit.setText(str(SeaBASSHeader.settings["start_time"]))

        end_timeLabel = QtWidgets.QLabel("end_time", self)
        self.end_timeLineEdit = QtWidgets.QLineEdit(self)
        self.end_timeLineEdit.setText(str(SeaBASSHeader.settings["end_time"]))

        north_latitudeLabel = QtWidgets.QLabel("north_latitude", self)
        self.north_latitudeLineEdit = QtWidgets.QLineEdit(self)
        self.north_latitudeLineEdit.setText(str(SeaBASSHeader.settings["north_latitude"]))

        south_latitudeLabel = QtWidgets.QLabel("south_latitude", self)
        self.south_latitudeLineEdit = QtWidgets.QLineEdit(self)
        self.south_latitudeLineEdit.setText(str(SeaBASSHeader.settings["south_latitude"]))

        east_longitudeLabel = QtWidgets.QLabel("east_longitude", self)
        self.east_longitudeLineEdit = QtWidgets.QLineEdit(self)
        self.east_longitudeLineEdit.setText(str(SeaBASSHeader.settings["east_longitude"]))

        west_longitudeLabel = QtWidgets.QLabel("west_longitude", self)
        self.west_longitudeLineEdit = QtWidgets.QLineEdit(self)
        self.west_longitudeLineEdit.setText(str(SeaBASSHeader.settings["west_longitude"]))

        wind_speedLabel = QtWidgets.QLabel("wind_speed", self)
        self.wind_speedLineEdit = QtWidgets.QLineEdit(self)
        self.wind_speedLineEdit.setText(str(SeaBASSHeader.settings["wind_speed"]))

        commentsLabel = QtWidgets.QLabel("comments", self)
        self.commentsLineEdit = QtWidgets.QTextEdit(self)
        self.commentsLineEdit.setPlainText(SeaBASSHeader.settings["comments"])

        ##

        self.saveButton = QtWidgets.QPushButton("Save")
        self.cancelButton = QtWidgets.QPushButton("Cancel")                      
            
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)

        # Whole Window Box
        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(nameLabel)
        VBox.addWidget(linkSeaBASSLabel)
        VBox.addWidget(instructionLabel)

        
        # Horizontal Box 
        HBox1 = QtWidgets.QHBoxLayout()
        HBox1.addWidget(investigatorsLabel)
        HBox1.addWidget(self.investigatorsLineEdit)
        VBox.addLayout(HBox1)   

        HBox2 = QtWidgets.QHBoxLayout()
        HBox2.addWidget(affiliationsLabel)
        HBox2.addWidget(self.affiliationsLineEdit)
        VBox.addLayout(HBox2)

        HBox3 = QtWidgets.QHBoxLayout()
        HBox3.addWidget(contactLabel)
        HBox3.addWidget(self.contactLineEdit)
        VBox.addLayout(HBox3)

        HBox4 = QtWidgets.QHBoxLayout()
        HBox4.addWidget(experimentLabel)
        HBox4.addWidget(self.experimentLineEdit)
        VBox.addLayout(HBox4)

        HBox5 = QtWidgets.QHBoxLayout()
        HBox5.addWidget(cruiseLabel)
        HBox5.addWidget(self.cruiseLineEdit)
        VBox.addLayout(HBox5)

        HBox6 = QtWidgets.QHBoxLayout()
        HBox6.addWidget(stationLabel)
        HBox6.addWidget(self.stationLineEdit)
        VBox.addLayout(HBox6)        

        HBox9 = QtWidgets.QHBoxLayout()
        HBox9.addWidget(documentsLabel)
        HBox9.addWidget(self.documentsLineEdit)
        VBox.addLayout(HBox9)

        HBox10 = QtWidgets.QHBoxLayout()
        HBox10.addWidget(calibration_filesLabel)
        HBox10.addWidget(self.calibration_filesLineEdit)
        VBox.addLayout(HBox10)

        HBox11 = QtWidgets.QHBoxLayout()
        HBox11.addWidget(data_typeLabel)
        HBox11.addWidget(self.data_typeLineEdit)
        VBox.addLayout(HBox11)

        HBox12 = QtWidgets.QHBoxLayout()
        HBox12.addWidget(data_statusLabel)
        HBox12.addWidget(self.data_statusLineEdit)
        VBox.addLayout(HBox12)        

        HBox21 = QtWidgets.QHBoxLayout()
        HBox21.addWidget(water_depthLabel)
        HBox21.addWidget(self.water_depthLineEdit)
        VBox.addLayout(HBox21)

        HBox22 = QtWidgets.QHBoxLayout()
        HBox22.addWidget(measurement_depthLabel)
        HBox22.addWidget(self.measurement_depthLineEdit)
        VBox.addLayout(HBox22)

        HBox23 = QtWidgets.QHBoxLayout()
        HBox23.addWidget(cloud_percentLabel)
        HBox23.addWidget(self.cloud_percentLineEdit)
        VBox.addLayout(HBox23)        

        HBox25 = QtWidgets.QHBoxLayout()
        HBox25.addWidget(wave_heightLabel)
        HBox25.addWidget(self.wave_heightLineEdit)
        VBox.addLayout(HBox25)


        VBox.addSpacing(20) 
        VBox.addWidget(instructionLabel2)

        HBox7 = QtWidgets.QHBoxLayout()
        HBox7.addWidget(data_file_nameLabel)
        HBox7.addWidget(self.data_file_nameLineEdit)
        VBox.addLayout(HBox7)

        HBox8 = QtWidgets.QHBoxLayout()
        HBox8.addWidget(original_file_nameLabel)
        HBox8.addWidget(self.original_file_nameLineEdit)
        VBox.addLayout(HBox8)

        HBox13 = QtWidgets.QHBoxLayout()
        HBox13.addWidget(start_dateLabel)
        HBox13.addWidget(self.start_dateLineEdit)
        VBox.addLayout(HBox13)

        HBox14 = QtWidgets.QHBoxLayout()
        HBox14.addWidget(end_dateLabel)
        HBox14.addWidget(self.end_dateLineEdit)
        VBox.addLayout(HBox14)

        HBox15 = QtWidgets.QHBoxLayout()
        HBox15.addWidget(start_timeLabel)
        HBox15.addWidget(self.start_timeLineEdit)
        VBox.addLayout(HBox15)

        HBox16 = QtWidgets.QHBoxLayout()
        HBox16.addWidget(end_timeLabel)
        HBox16.addWidget(self.end_timeLineEdit)
        VBox.addLayout(HBox16)

        HBox17 = QtWidgets.QHBoxLayout()
        HBox17.addWidget(north_latitudeLabel)
        HBox17.addWidget(self.north_latitudeLineEdit)
        VBox.addLayout(HBox17)

        HBox18 = QtWidgets.QHBoxLayout()
        HBox18.addWidget(south_latitudeLabel)
        HBox18.addWidget(self.south_latitudeLineEdit)
        VBox.addLayout(HBox18)

        HBox19 = QtWidgets.QHBoxLayout()
        HBox19.addWidget(east_longitudeLabel)
        HBox19.addWidget(self.east_longitudeLineEdit)
        VBox.addLayout(HBox19)

        HBox20 = QtWidgets.QHBoxLayout()
        HBox20.addWidget(west_longitudeLabel)
        HBox20.addWidget(self.west_longitudeLineEdit)
        VBox.addLayout(HBox20)

        HBox24 = QtWidgets.QHBoxLayout()
        HBox24.addWidget(wind_speedLabel)
        HBox24.addWidget(self.wind_speedLineEdit)
        VBox.addLayout(HBox24)

        HBox26 = QtWidgets.QHBoxLayout()
        HBox26.addWidget(commentsLabel)
        HBox26.addWidget(self.commentsLineEdit)
        VBox.addLayout(HBox26)


        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.cancelButton)
        VBox.addLayout(saveHBox)


        self.setLayout(VBox)
        self.setGeometry(300, 100, 0, 0)
        self.setWindowTitle('Edit SeaBASS Header')

       
    def saveButtonPressed(self):
        print("SeaBASSHeaderWindow - Save Pressed")        
        
        SeaBASSHeader.settings["investigators"] = self.investigatorsLineEdit.text()
        SeaBASSHeader.settings["affiliations"] = self.affiliationsLineEdit.text()  
        SeaBASSHeader.settings["contact"] = self.contactLineEdit.text()
        SeaBASSHeader.settings["experiment"] = self.experimentLineEdit.text()
        SeaBASSHeader.settings["cruise"] = self.cruiseLineEdit.text()        
        SeaBASSHeader.settings["station"] = self.stationLineEdit.text()        
        SeaBASSHeader.settings["documents"] = self.documentsLineEdit.text() 
        SeaBASSHeader.settings["calibration_files"] = self.calibration_filesLineEdit.text()
        SeaBASSHeader.settings["data_type"] = self.data_typeLineEdit.text()
        SeaBASSHeader.settings["data_status"] = self.data_statusLineEdit.text()                
        SeaBASSHeader.settings["water_depth"] = self.water_depthLineEdit.text()   
        SeaBASSHeader.settings["measurement_depth"] = self.measurement_depthLineEdit.text()      
        SeaBASSHeader.settings["cloud_percent"] = self.cloud_percentLineEdit.text()     
        SeaBASSHeader.settings["wave_height"] = self.wave_heightLineEdit.text()

        SeaBASSHeader.settings["data_file_name"] = self.data_file_nameLineEdit.text()
        SeaBASSHeader.settings["original_file_name"] = self.original_file_nameLineEdit.text()                                       
        SeaBASSHeader.settings["start_date"] = self.start_dateLineEdit.text()
        SeaBASSHeader.settings["end_date"] = self.end_dateLineEdit.text()
        SeaBASSHeader.settings["start_time"] = self.start_timeLineEdit.text()
        SeaBASSHeader.settings["end_date"] = self.end_dateLineEdit.text()

        SeaBASSHeader.settings["north_latitude"] = self.north_latitudeLineEdit.text()
        SeaBASSHeader.settings["south_latitude"] = self.south_latitudeLineEdit.text()
        SeaBASSHeader.settings["east_longitude"] = self.east_longitudeLineEdit.text()
        SeaBASSHeader.settings["west_longitude"] = self.west_longitudeLineEdit.text()                
        SeaBASSHeader.settings["wind_speed"] = self.wind_speedLineEdit.text()        
        SeaBASSHeader.settings["comments"] = self.commentsLineEdit.toPlainText()

        SeaBASSHeader.saveSeaBASSHeader(self.name)

        QtWidgets.QMessageBox.about(self, "Edit SeaBASSHeader File", "SeaBASSHeader File Saved")
        self.close()


    def cancelButtonPressed(self):
        print("SeaBASSWindow - Cancel Pressed")
        self.close()