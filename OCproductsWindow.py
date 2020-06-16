import os
from PyQt5 import QtCore, QtGui, QtWidgets

from ConfigFile import ConfigFile
from MainConfig import MainConfig


class OCproductsWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)        
        self.initUI()

    def initUI(self):
        
        linkOCWebLabel = QtWidgets.QLabel(
            "Descriptions of the algorithms used to derive these products can be found at  \
            <a href=\"https://oceancolor.gsfc.nasa.gov/atbd/\"> NASA's Ocean Color Web</a>")
        linkOCWebLabel.setOpenExternalLinks(True)

        oc4Label = QtWidgets.QLabel("chlor_a", self)     
        self.oc4CheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2oc4"]) == 1:
            self.oc4CheckBox.setChecked(True)       

        aotLabel = QtWidgets.QLabel("aot", self)     
        self.aotCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2aot"]) == 1:
            self.aotCheckBox.setChecked(True)      

        kd490Label = QtWidgets.QLabel("kd490", self)     
        self.kd490CheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2kd490"]) == 1:
            self.kd490CheckBox.setChecked(True)

        picLabel = QtWidgets.QLabel("pic", self)     
        self.picCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2pic"]) == 1:
            self.picCheckBox.setChecked(True)

        pocLabel = QtWidgets.QLabel("poc", self)     
        self.pocCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2poc"]) == 1:
            self.pocCheckBox.setChecked(True)

        parLabel = QtWidgets.QLabel("par", self)     
        self.parCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2par"]) == 1:
            self.parCheckBox.setChecked(True)

        giopLabel = QtWidgets.QLabel("giop", self)     
        self.giopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2giop"]) == 1:
            self.giopCheckBox.setChecked(True)
        self.aGiopLabel = QtWidgets.QLabel("a", self)     
        self.aGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2aGiop"]) == 1:
            self.aGiopCheckBox.setChecked(True)
        self.adgGiopLabel = QtWidgets.QLabel("adg", self)     
        self.adgGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2adgGiop"]) == 1:
            self.adgGiopCheckBox.setChecked(True)
        self.adgSGiopLabel = QtWidgets.QLabel("adg_S", self)     
        self.adgSGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2adgSGiop"]) == 1:
            self.adgSGiopCheckBox.setChecked(True)
        self.aphGiopLabel = QtWidgets.QLabel("aph", self)     
        self.aphGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2aphGiop"]) == 1:
            self.aphGiopCheckBox.setChecked(True)
        self.aphSGiopLabel = QtWidgets.QLabel("aph_S", self)     
        self.aphSGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2aphSGiop"]) == 1:
            self.aphSGiopCheckBox.setChecked(True)
        self.bbGiopLabel = QtWidgets.QLabel("bb", self)     
        self.bbGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2bbGiop"]) == 1:
            self.bbGiopCheckBox.setChecked(True)
        self.bbpGiopLabel = QtWidgets.QLabel("bbp", self)     
        self.bbpGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2bbpGiop"]) == 1:
            self.bbpGiopCheckBox.setChecked(True)
        self.bbpSGiopLabel = QtWidgets.QLabel("bbp_S", self)     
        self.bbpSGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2bbpSGiop"]) == 1:
            self.bbpSGiopCheckBox.setChecked(True)
        
        self.giopCheckBoxUpdate()
        self.giopCheckBox.clicked.connect(self.giopCheckBoxUpdate)
        
        
        qaaLabel = QtWidgets.QLabel("qaa", self)     
        self.qaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2qaa"]) == 1:
            self.qaaCheckBox.setChecked(True)
        self.aQaaLabel = QtWidgets.QLabel("a", self)     
        self.aQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2aQaa"]) == 1:
            self.aQaaCheckBox.setChecked(True)
        self.adgQaaLabel = QtWidgets.QLabel("adg", self)     
        self.adgQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2adgQaa"]) == 1:
            self.adgQaaCheckBox.setChecked(True)
        self.aphQaaLabel = QtWidgets.QLabel("aph", self)     
        self.aphQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2aphQaa"]) == 1:
            self.aphQaaCheckBox.setChecked(True)
        self.bQaaLabel = QtWidgets.QLabel("b", self)     
        self.bQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2bQaa"]) == 1:
            self.bQaaCheckBox.setChecked(True)
        self.bbQaaLabel = QtWidgets.QLabel("bb", self)     
        self.bbQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2bbQaa"]) == 1:
            self.bbQaaCheckBox.setChecked(True)
        self.bbpQaaLabel = QtWidgets.QLabel("bbp", self)     
        self.bbpQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2bbpQaa"]) == 1:
            self.bbpQaaCheckBox.setChecked(True)
        self.cQaaLabel = QtWidgets.QLabel("c", self)     
        self.cQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.settings["bL2cQaa"]) == 1:
            self.cQaaCheckBox.setChecked(True)

        self.qaaCheckBoxUpdate()
        self.qaaCheckBox.clicked.connect(self.qaaCheckBoxUpdate)
        



        self.saveButton = QtWidgets.QPushButton("Save/Close")        
        self.cancelButton = QtWidgets.QPushButton("Cancel")    
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.saveButton.clicked.connect(self.cancelButtonPressed)
  

        # ####################################################################################    
        # Whole Window Box
        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(linkOCWebLabel)

        # Left Box
        VBox1 = QtWidgets.QVBoxLayout()
        VBox1.addSpacing(10)

        # OC4
        oc4HBox = QtWidgets.QHBoxLayout()
        oc4HBox.addWidget(oc4Label)
        oc4HBox.addWidget(self.oc4CheckBox)
        VBox1.addLayout(oc4HBox)

        # AOT
        aotHBox = QtWidgets.QHBoxLayout()
        aotHBox.addWidget(aotLabel)
        aotHBox.addWidget(self.aotCheckBox)
        VBox1.addLayout(aotHBox)

        # Kd490
        kd490HBox = QtWidgets.QHBoxLayout()
        kd490HBox.addWidget(kd490Label)
        kd490HBox.addWidget(self.kd490CheckBox)
        VBox1.addLayout(kd490HBox)

        # PIC
        picHBox = QtWidgets.QHBoxLayout()
        picHBox.addWidget(picLabel)
        picHBox.addWidget(self.picCheckBox)
        VBox1.addLayout(picHBox)

        # POC
        pocHBox = QtWidgets.QHBoxLayout()
        pocHBox.addWidget(pocLabel)
        pocHBox.addWidget(self.pocCheckBox)
        VBox1.addLayout(pocHBox)

        # PAR
        parHBox = QtWidgets.QHBoxLayout()
        parHBox.addWidget(parLabel)
        parHBox.addWidget(self.parCheckBox)
        VBox1.addLayout(parHBox)

        # Right Box
        VBox2 = QtWidgets.QVBoxLayout()

        # GIOP
        giopVBox = QtWidgets.QVBoxLayout()
        
        giopHBox = QtWidgets.QHBoxLayout()
        giopHBox.addWidget(giopLabel)
        giopHBox.addWidget(self.giopCheckBox)
        giopVBox.addLayout(giopHBox)

        aGiopHBox = QtWidgets.QHBoxLayout()
        aGiopHBox.addWidget(aGiopLabel)
        aGiopHBox.addWidget(self.aGiopCheckBox)
        giopVBox.addLayout(aGiopHBox)

        adgGiopHBox = QtWidgets.QHBoxLayout()
        adgGiopHBox.addWidget(adgGiopLabel)
        adgGiopHBox.addWidget(self.adgGiopCheckBox)
        giopVBox.addLayout(adgGiopHBox)

        VBox2.addLayout(giopVBox)



        # QAA
        qaaVBox = QtWidgets.QVBoxLayout()

        qaaHBox = QtWidgets.QHBoxLayout()
        qaaHBox.addWidget(qaaLabel)
        qaaHBox.addWidget(self.qaaCheckBox)
        VBox2.addLayout(qaaHBox)

        aQaaHBox = QtWidgets.QHBoxLayout()
        aQaaHBox.addWidget(aQaaLabel)
        aQaaHBox.addWidget(self.aQaaCheckBox)
        VBox2.addLayout(aQaaHBox)

        adgQaaHBox = QtWidgets.QHBoxLayout()
        adgQaaHBox.addWidget(adgQaaLabel)
        adgQaaHBox.addWidget(self.adgQaaCheckBox)
        VBox2.addLayout(adgQaaHBox)

        VBox2.addLayout(qaaVBox)


       
        # Add 2 Vertical Boxes to Horizontal Box hBox
        hBox = QtWidgets.QHBoxLayout()
        hBox.addLayout(VBox1)
        hBox.addLayout(VBox2)                

        # Save/Cancel
        saveHBox = QtWidgets.QHBoxLayout()
        saveHBox.addStretch(1)
        saveHBox.addWidget(self.saveButton)
        saveHBox.addWidget(self.cancelButton)

        # Adds hBox and saveHBox to primary VBox 
        VBox.addLayout(hBox)
        VBox.addLayout(saveHBox)

        self.setLayout(VBox)
        self.setGeometry(300, 100, 0, 0)
        self.setWindowTitle('Derived L2 Geophysical and Inherent Optical Properties')


    def giopCheckBoxUpdate(self):
        print("OCproductsWindow - giopCheckBoxUpdate")
        
        disabled = (not self.giopCheckBox.isChecked())
        self.aGiopLabel.setDisabled(disabled)
        self.aGiopCheckBox.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL2giop"] = 0
        else:
            ConfigFile.settings["bL2giop"] = 1

    def qaaCheckBoxUpdate(self):
        print("OCproductsWindow - qaaCheckBoxUpdate")
        
        disabled = (not self.qaaCheckBox.isChecked())
        self.aQaaLabel.setDisabled(disabled)
        self.aQaaCheckBox.setDisabled(disabled)
        if disabled:
            ConfigFile.settings["bL2qaa"] = 0
        else:
            ConfigFile.settings["bL2qaa"] = 1
       
    def saveButtonPressed(self):
        print("L2 Products - Save/Close Pressed")        
        
        ConfigFile.settings["bL2oc4"] = int(self.oc4CheckBox.isChecked())
        ConfigFile.settings["bL2aot"] = int(self.aotCheckBox.isChecked())
        ConfigFile.settings["bL2kd490"] = int(self.kd490CheckBox.isChecked())
        ConfigFile.settings["bL2pic"] = int(self.picCheckBox.isChecked())
        ConfigFile.settings["bL2poc"] = int(self.pocCheckBox.isChecked())
        ConfigFile.settings["bL2par"] = int(self.parCheckBox.isChecked())
        ConfigFile.settings["bL2giop"] = int(self.giopCheckBox.isChecked())
        ConfigFile.settings["bL2qaa"] = int(self.qaaCheckBox.isChecked())
        
        #QtWidgets.QMessageBox.about(self, "Edit SeaBASSHeader File", "SeaBASSHeader File Saved")
        self.close()

    def cancelButtonPressed(self):
        print("L2 Products - Cancel Pressed")
        self.close()

    # def refreshWindow(self):
    #     print("SeaBASSHeaderWindow - refreshWindow")        
    #     self.nameLabel.setText(f'Editing: {self.name}')
    #     self.investigatorsLineEdit.setText(str(SeaBASSHeader.settings["investigators"]))
    #     self.affiliationsLineEdit.setText(str(SeaBASSHeader.settings["affiliations"]))
    #     self.contactLineEdit.setText(str(SeaBASSHeader.settings["contact"]))
    #     self.experimentLineEdit.setText(str(SeaBASSHeader.settings["experiment"]))
    #     self.cruiseLineEdit.setText(str(SeaBASSHeader.settings["cruise"]))
    #     self.stationLineEdit.setText(str(SeaBASSHeader.settings["station"]))
    #     self.documentsLineEdit.setText(str(SeaBASSHeader.settings["documents"]))
    #     self.instrument_manufacturerLineEdit.setText(str(SeaBASSHeader.settings["instrument_manufacturer"]))
    #     self.instrument_modelLineEdit.setText(str(SeaBASSHeader.settings["instrument_model"]))
    #     self.calibration_dateLineEdit.setText(str(SeaBASSHeader.settings["calibration_date"]))
    #     self.commentsLineEdit.setPlainText(SeaBASSHeader.settings["comments"])
    #     self.other_commentsLineEdit.setText(SeaBASSHeader.settings["other_comments"])        
        
    

