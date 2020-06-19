import os
from PyQt5 import QtCore, QtGui, QtWidgets

from ConfigFile import ConfigFile
import ConfigWindow
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
        satNoteLabel = QtWidgets.QLabel(
            "Algorithms requiring satellite bands will activate MODIS Aqua waveband convolution" \
                " processing in L2")

        geoPhysLabel = QtWidgets.QLabel("Geophysical Parameters")
        geoPhysLabel_font = geoPhysLabel.font()
        geoPhysLabel_font.setPointSize(12)
        geoPhysLabel_font.setBold(True)
        geoPhysLabel.setFont(geoPhysLabel_font)

        oc3mLabel = QtWidgets.QLabel("chlor_a", self)     
        self.oc3mCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodoc3m"]) == 1:
            self.oc3mCheckBox.setChecked(True)       

        # aotLabel = QtWidgets.QLabel("aot", self)     
        # self.aotCheckBox = QtWidgets.QCheckBox("", self)              
        # if int(ConfigFile.products["bL2Prodaot"]) == 1:
        #     self.aotCheckBox.setChecked(True)      

        kd490Label = QtWidgets.QLabel("kd490", self)     
        self.kd490CheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodkd490"]) == 1:
            self.kd490CheckBox.setChecked(True)

        picLabel = QtWidgets.QLabel("pic", self)     
        self.picCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodpic"]) == 1:
            self.picCheckBox.setChecked(True)

        pocLabel = QtWidgets.QLabel("poc", self)     
        self.pocCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodpoc"]) == 1:
            self.pocCheckBox.setChecked(True)

        iparLabel = QtWidgets.QLabel("ipar", self)     
        self.iparCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodipar"]) == 1:
            self.iparCheckBox.setChecked(True)

        otherLabel = QtWidgets.QLabel("Other Parameters")
        otherLabel_font = otherLabel.font()
        otherLabel_font.setPointSize(12)
        otherLabel_font.setBold(True)
        otherLabel.setFont(otherLabel_font)

        avrLabel = QtWidgets.QLabel("avr (Vandermuellen et al. 2020)", self)     
        self.avrCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodavr"]) == 1:
            self.avrCheckBox.setChecked(True)

        iopLabel = QtWidgets.QLabel("Inherent Optical Properties")
        iopLabel_font = iopLabel.font()
        iopLabel_font.setPointSize(12)
        iopLabel_font.setBold(True)
        iopLabel.setFont(iopLabel_font)

        giopLabel = QtWidgets.QLabel("GIOP", self)     
        self.giopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodgiop"]) == 1:
            self.giopCheckBox.setChecked(True)
        self.aGiopLabel = QtWidgets.QLabel("     a", self)     
        self.aGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdaGiop"]) == 1:
            self.aGiopCheckBox.setChecked(True)
        self.adgGiopLabel = QtWidgets.QLabel("     adg", self)     
        self.adgGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdadgGiop"]) == 1:
            self.adgGiopCheckBox.setChecked(True)
        self.adgSGiopLabel = QtWidgets.QLabel("     adg_S", self)     
        self.adgSGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdadgSGiop"]) == 1:
            self.adgSGiopCheckBox.setChecked(True)
        self.aphGiopLabel = QtWidgets.QLabel("     aph", self)     
        self.aphGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdaphGiop"]) == 1:
            self.aphGiopCheckBox.setChecked(True)
        self.aphSGiopLabel = QtWidgets.QLabel("     aph_S", self)     
        self.aphSGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdaphSGiop"]) == 1:
            self.aphSGiopCheckBox.setChecked(True)
        self.bbGiopLabel = QtWidgets.QLabel("     bb", self)     
        self.bbGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdbbGiop"]) == 1:
            self.bbGiopCheckBox.setChecked(True)
        self.bbpGiopLabel = QtWidgets.QLabel("     bbp", self)     
        self.bbpGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdbbpGiop"]) == 1:
            self.bbpGiopCheckBox.setChecked(True)
        self.bbpSGiopLabel = QtWidgets.QLabel("     bbp_S", self)     
        self.bbpSGiopCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdbbpSGiop"]) == 1:
            self.bbpSGiopCheckBox.setChecked(True)
        
        self.giopCheckBoxUpdate()
        self.giopCheckBox.clicked.connect(self.giopCheckBoxUpdate)
        
        
        qaaLabel = QtWidgets.QLabel("QAA", self)     
        self.qaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodqaa"]) == 1:
            self.qaaCheckBox.setChecked(True)
        self.aQaaLabel = QtWidgets.QLabel("     a", self)     
        self.aQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdaQaa"]) == 1:
            self.aQaaCheckBox.setChecked(True)
        self.adgQaaLabel = QtWidgets.QLabel("     adg", self)     
        self.adgQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdadgQaa"]) == 1:
            self.adgQaaCheckBox.setChecked(True)
        self.aphQaaLabel = QtWidgets.QLabel("     aph", self)     
        self.aphQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdaphQaa"]) == 1:
            self.aphQaaCheckBox.setChecked(True)
        self.bQaaLabel = QtWidgets.QLabel("     b", self)     
        self.bQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdbQaa"]) == 1:
            self.bQaaCheckBox.setChecked(True)
        self.bbQaaLabel = QtWidgets.QLabel("     bb", self)     
        self.bbQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdbbQaa"]) == 1:
            self.bbQaaCheckBox.setChecked(True)
        self.bbpQaaLabel = QtWidgets.QLabel("     bbp", self)     
        self.bbpQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdbbpQaa"]) == 1:
            self.bbpQaaCheckBox.setChecked(True)
        self.cQaaLabel = QtWidgets.QLabel("     c", self)     
        self.cQaaCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdcQaa"]) == 1:
            self.cQaaCheckBox.setChecked(True)

        self.qaaCheckBoxUpdate()
        self.qaaCheckBox.clicked.connect(self.qaaCheckBoxUpdate)

        self.saveButton = QtWidgets.QPushButton("Save/Close")        
        self.cancelButton = QtWidgets.QPushButton("Cancel")    
        self.saveButton.clicked.connect(self.saveButtonPressed)
        self.cancelButton.clicked.connect(self.cancelButtonPressed)
  

        # ####################################################################################    
        # Whole Window Box
        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(linkOCWebLabel)
        VBox.addWidget(satNoteLabel)

        # Left Box
        VBox1 = QtWidgets.QVBoxLayout()
        VBox1.addWidget(geoPhysLabel)
        VBox1.addSpacing(10)

        # oc3m
        oc3mHBox = QtWidgets.QHBoxLayout()
        oc3mHBox.addWidget(oc3mLabel)
        oc3mHBox.addWidget(self.oc3mCheckBox)
        VBox1.addLayout(oc3mHBox)

        # # AOT
        # aotHBox = QtWidgets.QHBoxLayout()
        # aotHBox.addWidget(aotLabel)
        # aotHBox.addWidget(self.aotCheckBox)
        # VBox1.addLayout(aotHBox)

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


        self.picCheckBox.setDisabled(1)



        # POC
        pocHBox = QtWidgets.QHBoxLayout()
        pocHBox.addWidget(pocLabel)
        pocHBox.addWidget(self.pocCheckBox)
        VBox1.addLayout(pocHBox)

        # PAR
        iparHBox = QtWidgets.QHBoxLayout()
        iparHBox.addWidget(iparLabel)
        iparHBox.addWidget(self.iparCheckBox)
        VBox1.addLayout(iparHBox)


        VBox1.addWidget(otherLabel)  
        VBox1.addSpacing(10)      
        # AVR
        avrHBox = QtWidgets.QHBoxLayout()
        avrHBox.addWidget(avrLabel)
        avrHBox.addWidget(self.avrCheckBox)
        VBox1.addLayout(avrHBox)

        VBox1.addStretch()

        # Right Box
        VBox2 = QtWidgets.QVBoxLayout()
        VBox2.addWidget(iopLabel)

        # GIOP
        giopVBox = QtWidgets.QVBoxLayout()
        
        giopHBox = QtWidgets.QHBoxLayout()
        giopHBox.addWidget(giopLabel)
        giopHBox.addWidget(self.giopCheckBox)
        giopVBox.addLayout(giopHBox)

        aGiopHBox = QtWidgets.QHBoxLayout()
        aGiopHBox.addWidget(self.aGiopLabel)
        aGiopHBox.addWidget(self.aGiopCheckBox)
        giopVBox.addLayout(aGiopHBox)

        adgGiopHBox = QtWidgets.QHBoxLayout()
        adgGiopHBox.addWidget(self.adgGiopLabel)
        adgGiopHBox.addWidget(self.adgGiopCheckBox)
        giopVBox.addLayout(adgGiopHBox)

        adgSGiopHBox = QtWidgets.QHBoxLayout()
        adgSGiopHBox.addWidget(self.adgSGiopLabel)
        adgSGiopHBox.addWidget(self.adgSGiopCheckBox)
        giopVBox.addLayout(adgSGiopHBox)

        aphGiopHBox = QtWidgets.QHBoxLayout()
        aphGiopHBox.addWidget(self.aphGiopLabel)
        aphGiopHBox.addWidget(self.aphGiopCheckBox)
        giopVBox.addLayout(aphGiopHBox)

        aphSGiopHBox = QtWidgets.QHBoxLayout()
        aphSGiopHBox.addWidget(self.aphSGiopLabel)
        aphSGiopHBox.addWidget(self.aphSGiopCheckBox)
        giopVBox.addLayout(aphSGiopHBox)

        bbGiopHBox = QtWidgets.QHBoxLayout()
        bbGiopHBox.addWidget(self.bbGiopLabel)
        bbGiopHBox.addWidget(self.bbGiopCheckBox)
        giopVBox.addLayout(bbGiopHBox)

        bbpGiopHBox = QtWidgets.QHBoxLayout()
        bbpGiopHBox.addWidget(self.bbpGiopLabel)
        bbpGiopHBox.addWidget(self.bbpGiopCheckBox)
        giopVBox.addLayout(bbpGiopHBox)

        bbpSGiopHBox = QtWidgets.QHBoxLayout()
        bbpSGiopHBox.addWidget(self.bbpSGiopLabel)
        bbpSGiopHBox.addWidget(self.bbpSGiopCheckBox)
        giopVBox.addLayout(bbpSGiopHBox)

        VBox2.addLayout(giopVBox)

        # QAA
        qaaVBox = QtWidgets.QVBoxLayout()

        qaaHBox = QtWidgets.QHBoxLayout()
        qaaHBox.addWidget(qaaLabel)
        qaaHBox.addWidget(self.qaaCheckBox)
        VBox2.addLayout(qaaHBox)

        aQaaHBox = QtWidgets.QHBoxLayout()
        aQaaHBox.addWidget(self.aQaaLabel)
        aQaaHBox.addWidget(self.aQaaCheckBox)
        VBox2.addLayout(aQaaHBox)

        adgQaaHBox = QtWidgets.QHBoxLayout()
        adgQaaHBox.addWidget(self.adgQaaLabel)
        adgQaaHBox.addWidget(self.adgQaaCheckBox)
        VBox2.addLayout(adgQaaHBox)

        aphQaaHBox = QtWidgets.QHBoxLayout()
        aphQaaHBox.addWidget(self.aphQaaLabel)
        aphQaaHBox.addWidget(self.aphQaaCheckBox)
        VBox2.addLayout(aphQaaHBox)

        bQaaHBox = QtWidgets.QHBoxLayout()
        bQaaHBox.addWidget(self.bQaaLabel)
        bQaaHBox.addWidget(self.bQaaCheckBox)
        VBox2.addLayout(bQaaHBox)

        bbQaaHBox = QtWidgets.QHBoxLayout()
        bbQaaHBox.addWidget(self.bbQaaLabel)
        bbQaaHBox.addWidget(self.bbQaaCheckBox)
        VBox2.addLayout(bbQaaHBox)

        bbpQaaHBox = QtWidgets.QHBoxLayout()
        bbpQaaHBox.addWidget(self.bbpQaaLabel)
        bbpQaaHBox.addWidget(self.bbpQaaCheckBox)
        VBox2.addLayout(bbpQaaHBox)

        cQaaHBox = QtWidgets.QHBoxLayout()
        cQaaHBox.addWidget(self.cQaaLabel)
        cQaaHBox.addWidget(self.cQaaCheckBox)
        VBox2.addLayout(cQaaHBox)

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
        self.adgGiopLabel.setDisabled(disabled)
        self.adgGiopCheckBox.setDisabled(disabled)
        self.adgSGiopLabel.setDisabled(disabled)
        self.adgSGiopCheckBox.setDisabled(disabled)
        self.aphGiopLabel.setDisabled(disabled)
        self.aphGiopCheckBox.setDisabled(disabled)
        self.aphSGiopLabel.setDisabled(disabled)
        self.aphSGiopCheckBox.setDisabled(disabled)
        self.bbGiopLabel.setDisabled(disabled)
        self.bbGiopCheckBox.setDisabled(disabled)
        self.bbpGiopLabel.setDisabled(disabled)
        self.bbpGiopCheckBox.setDisabled(disabled)
        self.bbpSGiopLabel.setDisabled(disabled)
        self.bbpSGiopCheckBox.setDisabled(disabled)

        if disabled:
            ConfigFile.products["bL2Prodgiop"] = 0
        else:
            ConfigFile.products["bL2Prodgiop"] = 1

    def qaaCheckBoxUpdate(self):
        print("OCproductsWindow - qaaCheckBoxUpdate")
        
        disabled = (not self.qaaCheckBox.isChecked())
        self.aQaaLabel.setDisabled(disabled)
        self.aQaaCheckBox.setDisabled(disabled)
        self.adgQaaLabel.setDisabled(disabled)
        self.adgQaaCheckBox.setDisabled(disabled)
        self.aphQaaLabel.setDisabled(disabled)
        self.aphQaaCheckBox.setDisabled(disabled)
        self.bQaaLabel.setDisabled(disabled)
        self.bQaaCheckBox.setDisabled(disabled)
        self.bbQaaLabel.setDisabled(disabled)
        self.bbQaaCheckBox.setDisabled(disabled)
        self.bbpQaaLabel.setDisabled(disabled)
        self.bbpQaaCheckBox.setDisabled(disabled)
        self.cQaaLabel.setDisabled(disabled)
        self.cQaaCheckBox.setDisabled(disabled)

        if disabled:
            ConfigFile.products["bL2Prodqaa"] = 0
        else:
            ConfigFile.products["bL2Prodqaa"] = 1
       
    def saveButtonPressed(self):
        print("L2 Products - Save/Close Pressed")        
        
        ConfigFile.products["bL2Prodoc3m"] = int(self.oc3mCheckBox.isChecked())
        # ConfigFile.products["bL2Prodaot"] = int(self.aotCheckBox.isChecked())
        ConfigFile.products["bL2Prodkd490"] = int(self.kd490CheckBox.isChecked())
        ConfigFile.products["bL2Prodpic"] = int(self.picCheckBox.isChecked())
        ConfigFile.products["bL2Prodpoc"] = int(self.pocCheckBox.isChecked())
        ConfigFile.products["bL2Prodipar"] = int(self.iparCheckBox.isChecked())
        ConfigFile.products["bL2Prodavr"] = int(self.avrCheckBox.isChecked())
        ConfigFile.products["bL2Prodgiop"] = int(self.giopCheckBox.isChecked())
        ConfigFile.products["bL2ProdaGiop"] = int(self.aGiopCheckBox.isChecked())
        ConfigFile.products["bL2ProdadgGiop"] = int(self.adgGiopCheckBox.isChecked())
        ConfigFile.products["bL2ProdadgSGiop"] = int(self.adgSGiopCheckBox.isChecked())
        ConfigFile.products["bL2ProdaphGiop"] = int(self.aphGiopCheckBox.isChecked())
        ConfigFile.products["bL2ProdaphSGiop"] = int(self.aphSGiopCheckBox.isChecked())
        ConfigFile.products["bL2ProdbbGiop"] = int(self.bbGiopCheckBox.isChecked())
        ConfigFile.products["bL2ProdbbpGiop"] = int(self.bbpGiopCheckBox.isChecked())
        ConfigFile.products["bL2ProdbbpSGiop"] = int(self.bbpSGiopCheckBox.isChecked())
        ConfigFile.products["bL2Prodqaa"] = int(self.qaaCheckBox.isChecked())
        ConfigFile.products["bL2ProdaQaa"] = int(self.aQaaCheckBox.isChecked())
        ConfigFile.products["bL2ProdadgQaa"] = int(self.adgQaaCheckBox.isChecked())
        ConfigFile.products["bL2ProdaphQaa"] = int(self.aphQaaCheckBox.isChecked())
        ConfigFile.products["bL2ProdbQaa"] = int(self.bQaaCheckBox.isChecked())
        ConfigFile.products["bL2ProdbbQaa"] = int(self.bbQaaCheckBox.isChecked())
        ConfigFile.products["bL2ProdbbpQaa"] = int(self.bbpQaaCheckBox.isChecked())
        ConfigFile.products["bL2ProdcQaa"] = int(self.cQaaCheckBox.isChecked())

        # Confirm necessary satellite bands are processed
        if ConfigFile.products["bL2Prodoc3m"] or ConfigFile.products["bL2Prodkd490"] or \
            ConfigFile.products["bL2Prodpic"] or ConfigFile.products["bL2Prodpoc"]:

            ConfigFile.settings["bL2WeightMODISA"] = 1
        
        self.close()

    def cancelButtonPressed(self):
        print("L2 Products - Cancel Pressed")
        self.close()  
        
    

