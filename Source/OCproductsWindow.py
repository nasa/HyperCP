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

        biochemLabel = QtWidgets.QLabel("Biogeochemical Products")
        biochemLabel_font = biochemLabel.font()
        biochemLabel_font.setPointSize(12)
        biochemLabel_font.setBold(True)
        biochemLabel.setFont(biochemLabel_font)
        biochemLabel1 = QtWidgets.QLabel("    & Empirical IOPs")
        biochemLabel_font = biochemLabel1.font()
        biochemLabel_font.setPointSize(12)
        biochemLabel_font.setBold(True)
        biochemLabel1.setFont(biochemLabel_font)

        oc3mLabel = QtWidgets.QLabel("chlor_a", self)     
        self.oc3mCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodoc3m"]) == 1:
            self.oc3mCheckBox.setChecked(True) 

        picLabel = QtWidgets.QLabel("pic", self)     
        self.picCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodpic"]) == 1:
            self.picCheckBox.setChecked(True)

        pocLabel = QtWidgets.QLabel("poc", self)     
        self.pocCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodpoc"]) == 1:
            self.pocCheckBox.setChecked(True)
        
        gocadLabel = QtWidgets.QLabel("GOCAD (Aurin et al. 2018)", self)     
        self.gocadCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodgocad"]) == 1:
            self.gocadCheckBox.setChecked(True)

        self.agLabel = QtWidgets.QLabel("   ag(275, 355, 380, 412, 443, 488)", self)     
        self.agCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodag"]) == 1:
            self.agCheckBox.setChecked(True)

        self.SgLabel = QtWidgets.QLabel("   Sg(275, 300, 350, 380, 412)", self)     
        self.SgCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdSg"]) == 1:
            self.SgCheckBox.setChecked(True)

        # self.Sg275Label = QtWidgets.QLabel("     Sg275", self)     
        # self.Sg275CheckBox = QtWidgets.QCheckBox("", self)              
        # if int(ConfigFile.products["bL2ProdSg275"]) == 1:
        #     self.Sg275CheckBox.setChecked(True)
        # self.Sg300Label = QtWidgets.QLabel("     Sg300", self)     
        # self.Sg300CheckBox = QtWidgets.QCheckBox("", self)              
        # if int(ConfigFile.products["bL2ProdSg300"]) == 1:
        #     self.Sg300CheckBox.setChecked(True)
        # self.Sg412Label = QtWidgets.QLabel("     Sg412", self)     
        # self.Sg412CheckBox = QtWidgets.QCheckBox("", self)              
        # if int(ConfigFile.products["bL2ProdSg412"]) == 1:
        #     self.Sg412CheckBox.setChecked(True)
        self.DOCLabel = QtWidgets.QLabel("   doc", self)     
        self.DOCCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdDOC"]) == 1:
            self.DOCCheckBox.setChecked(True)

        # self.gocadCheckBoxUpdate()
        self.gocadCheckBox.clicked.connect(self.gocadCheckBoxUpdate)
        
        geoPhysLabel = QtWidgets.QLabel("Geophysical Products")
        geoPhysLabel_font = geoPhysLabel.font()
        geoPhysLabel_font.setPointSize(12)
        geoPhysLabel_font.setBold(True)
        geoPhysLabel.setFont(geoPhysLabel_font)                  

        kd490Label = QtWidgets.QLabel("kd490", self)     
        self.kd490CheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodkd490"]) == 1:
            self.kd490CheckBox.setChecked(True)        

        iparLabel = QtWidgets.QLabel("ipar", self)     
        self.iparCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodipar"]) == 1:
            self.iparCheckBox.setChecked(True)

        avwLabel = QtWidgets.QLabel("avw (Vandermuellen et al. 2020)", self)     
        self.avwCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2Prodavw"]) == 1:
            self.avwCheckBox.setChecked(True)

        aotLabel = QtWidgets.QLabel("aot (see Ancillary Data)", self)     
        # self.aotCheckBox = QtWidgets.QCheckBox("", self)              
        # if int(ConfigFile.products["bL2Prodaot"]) == 1:
        #     self.aotCheckBox.setChecked(True)

        weiLabel = QtWidgets.QLabel("weiQA (Wei et al. 2016)", self)     
        self.weiCheckBox = QtWidgets.QCheckBox("", self)              
        if int(ConfigFile.products["bL2ProdweiQA"]) == 1:
            self.weiCheckBox.setChecked(True) 

        iopLabel = QtWidgets.QLabel("Semi-analytical Algorithms")
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
        
        # self.giopCheckBoxUpdate()
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
        # Geophysical
        VBox1 = QtWidgets.QVBoxLayout()
       

        # Biogeochem
        VBox1.addWidget(biochemLabel)
        VBox1.addWidget(biochemLabel1)
        # VBox1.addSpacing(10)           

        # oc3m
        oc3mHBox = QtWidgets.QHBoxLayout()
        oc3mHBox.addWidget(oc3mLabel)
        oc3mHBox.addWidget(self.oc3mCheckBox)
        VBox1.addLayout(oc3mHBox)

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

        # VBox1.addSpacing(10)

        # CDOM, Sg, DOC
        gocadVBox = QtWidgets.QVBoxLayout()
        
        gocadHBox = QtWidgets.QHBoxLayout()
        gocadHBox.addWidget(gocadLabel)
        gocadHBox.addWidget(self.gocadCheckBox)
        gocadVBox.addLayout(gocadHBox)

        agHBox = QtWidgets.QHBoxLayout()
        agHBox.addWidget(self.agLabel)
        agHBox.addWidget(self.agCheckBox)
        gocadVBox.addLayout(agHBox)

        # ag275HBox = QtWidgets.QHBoxLayout()
        # ag275HBox.addWidget(self.ag275Label)
        # ag275HBox.addWidget(self.ag275CheckBox)
        # gocadVBox.addLayout(ag275HBox)

        # ag355HBox = QtWidgets.QHBoxLayout()
        # ag355HBox.addWidget(self.ag355Label)
        # ag355HBox.addWidget(self.ag355CheckBox)
        # gocadVBox.addLayout(ag355HBox)

        # ag380HBox = QtWidgets.QHBoxLayout()
        # ag380HBox.addWidget(self.ag380Label)
        # ag380HBox.addWidget(self.ag380CheckBox)
        # gocadVBox.addLayout(ag380HBox)

        # ag412HBox = QtWidgets.QHBoxLayout()
        # ag412HBox.addWidget(self.ag412Label)
        # ag412HBox.addWidget(self.ag412CheckBox)
        # gocadVBox.addLayout(ag412HBox)

        # ag443HBox = QtWidgets.QHBoxLayout()
        # ag443HBox.addWidget(self.ag443Label)
        # ag443HBox.addWidget(self.ag443CheckBox)
        # gocadVBox.addLayout(ag443HBox)

        # ag488HBox = QtWidgets.QHBoxLayout()
        # ag488HBox.addWidget(self.ag488Label)
        # ag488HBox.addWidget(self.ag488CheckBox)
        # gocadVBox.addLayout(ag488HBox)

        SgHBox = QtWidgets.QHBoxLayout()
        SgHBox.addWidget(self.SgLabel)
        SgHBox.addWidget(self.SgCheckBox)
        gocadVBox.addLayout(SgHBox)

        # Sg275HBox = QtWidgets.QHBoxLayout()
        # Sg275HBox.addWidget(self.Sg275Label)
        # Sg275HBox.addWidget(self.Sg275CheckBox)
        # gocadVBox.addLayout(Sg275HBox)

        # Sg300HBox = QtWidgets.QHBoxLayout()
        # Sg300HBox.addWidget(self.Sg300Label)
        # Sg300HBox.addWidget(self.Sg300CheckBox)
        # gocadVBox.addLayout(Sg300HBox)

        # Sg412HBox = QtWidgets.QHBoxLayout()
        # Sg412HBox.addWidget(self.Sg412Label)
        # Sg412HBox.addWidget(self.Sg412CheckBox)
        # gocadVBox.addLayout(Sg412HBox)

        DOCHBox = QtWidgets.QHBoxLayout()
        DOCHBox.addWidget(self.DOCLabel)
        DOCHBox.addWidget(self.DOCCheckBox)
        gocadVBox.addLayout(DOCHBox)

        VBox1.addLayout(gocadVBox)

        VBox1.addStretch()

        # Right Box
        VBox2 = QtWidgets.QVBoxLayout()
        VBox2.addWidget(geoPhysLabel)
        # VBox2.addSpacing(10)       

        # AOT
        aotHBox = QtWidgets.QHBoxLayout()
        aotHBox.addWidget(aotLabel)
        # aotHBox.addWidget(self.aotCheckBox)
        VBox2.addLayout(aotHBox)

        # AVW
        avwHBox = QtWidgets.QHBoxLayout()
        avwHBox.addWidget(avwLabel)
        avwHBox.addWidget(self.avwCheckBox)
        VBox2.addLayout(avwHBox)

        # Kd490
        kd490HBox = QtWidgets.QHBoxLayout()
        kd490HBox.addWidget(kd490Label)
        kd490HBox.addWidget(self.kd490CheckBox)
        VBox2.addLayout(kd490HBox)

        # PAR
        iparHBox = QtWidgets.QHBoxLayout()
        iparHBox.addWidget(iparLabel)
        iparHBox.addWidget(self.iparCheckBox)
        VBox2.addLayout(iparHBox)                

         # WeiQA
        weiHBox = QtWidgets.QHBoxLayout()
        weiHBox.addWidget(weiLabel)
        weiHBox.addWidget(self.weiCheckBox)
        VBox2.addLayout(weiHBox)

        # VBox2.addSpacing(10)

        # Semianalyticals
        VBox2.addWidget(iopLabel)

        # VBox2.addSpacing(10)

        # GIOP
        giopVBox = QtWidgets.QVBoxLayout()
        
        giopHBox = QtWidgets.QHBoxLayout()
        giopHBox.addWidget(giopLabel)
        giopHBox.addWidget(self.giopCheckBox)
        giopVBox.addLayout(giopHBox)
        self.giopCheckBox.setDisabled(1)

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

        # VBox2.addSpacing(10)

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
        VBox2.addStretch()
       
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
        ''' TO DO: I still have no control over the window size or line spacing'''
        self.setGeometry(100, 100, 0, 0)
        self.setWindowTitle('Derived L2 Geophysical and Inherent Optical Properties')

    def gocadCheckBoxUpdate(self):
        print("OCproductsWindow - gocadCheckBoxUpdate")
        
        disabled = self.gocadCheckBox.isChecked()
        self.agLabel.setDisabled(not disabled)
        self.agCheckBox.setDisabled(not disabled)
        self.agCheckBox.setChecked(disabled)
        # self.ag275Label.setDisabled(not disabled)
        # self.ag275CheckBox.setDisabled(not disabled)
        # self.ag275CheckBox.setChecked(disabled)
        # self.ag355Label.setDisabled(not disabled)
        # self.ag355CheckBox.setDisabled(not disabled)
        # self.ag355CheckBox.setChecked(disabled)
        # self.ag380Label.setDisabled(not disabled)
        # self.ag380CheckBox.setDisabled(not disabled)
        # self.ag380CheckBox.setChecked(disabled)
        # self.ag412Label.setDisabled(not disabled)
        # self.ag412CheckBox.setDisabled(not disabled)
        # self.ag412CheckBox.setChecked(disabled)
        # self.ag443Label.setDisabled(not disabled)
        # self.ag443CheckBox.setDisabled(not disabled)
        # self.ag443CheckBox.setChecked(disabled)
        # self.ag488Label.setDisabled(not disabled)
        # self.ag488CheckBox.setDisabled(not disabled)
        # self.ag488CheckBox.setChecked(disabled)
        self.SgLabel.setDisabled(not disabled)
        self.SgCheckBox.setDisabled(not disabled)
        self.SgCheckBox.setChecked(disabled)
        # self.Sg275Label.setDisabled(not disabled)
        # self.Sg275CheckBox.setDisabled(not disabled)
        # self.Sg275CheckBox.setChecked(disabled)
        # self.Sg300Label.setDisabled(not disabled)
        # self.Sg300CheckBox.setDisabled(not disabled)
        # self.Sg300CheckBox.setChecked(disabled)
        # self.Sg412Label.setDisabled(not disabled)
        # self.Sg412CheckBox.setDisabled(not disabled)
        # self.Sg412CheckBox.setChecked(disabled)
        self.DOCLabel.setDisabled(not disabled)
        self.DOCCheckBox.setDisabled(not disabled)
        self.DOCCheckBox.setChecked(disabled)

        if disabled:
            ConfigFile.products["bL2Prodgocad"] = 0
        else:
            ConfigFile.products["bL2Prodgocad"] = 1

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
        ConfigFile.products["bL2Prodavw"] = int(self.avwCheckBox.isChecked())
        ConfigFile.products["bL2ProdweiQA"] = int(self.weiCheckBox.isChecked())
        ConfigFile.products["bL2Prodgocad"] = int(self.gocadCheckBox.isChecked())
        ConfigFile.products["bL2Prodag"] = int(self.agCheckBox.isChecked())
        # ConfigFile.products["bL2Prodag275"] = int(self.ag275CheckBox.isChecked())
        # ConfigFile.products["bL2Prodag355"] = int(self.ag355CheckBox.isChecked())
        # ConfigFile.products["bL2Prodag380"] = int(self.ag380CheckBox.isChecked())
        # ConfigFile.products["bL2Prodag412"] = int(self.ag412CheckBox.isChecked())
        # ConfigFile.products["bL2Prodag443"] = int(self.ag443CheckBox.isChecked())
        # ConfigFile.products["bL2Prodag488"] = int(self.ag488CheckBox.isChecked())
        ConfigFile.products["bL2ProdSg"] = int(self.SgCheckBox.isChecked())
        # ConfigFile.products["bL2ProdSg275"] = int(self.Sg275CheckBox.isChecked())
        # ConfigFile.products["bL2ProdSg300"] = int(self.Sg300CheckBox.isChecked())
        # ConfigFile.products["bL2ProdSg412"] = int(self.Sg412CheckBox.isChecked())
        ConfigFile.products["bL2ProdDOC"] = int(self.DOCCheckBox.isChecked())
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
            ConfigFile.products["bL2Prodpic"] or ConfigFile.products["bL2Prodpoc"] or \
            ConfigFile.products["bL2Prodgocad"] or ConfigFile.products["bL2Prodgiop"] or \
            ConfigFile.products["bL2Prodqaa"] or ConfigFile.products["bL2ProdweiQA"]:

            ConfigFile.settings["bL2WeightMODISA"] = 1
        
        self.close()

    def cancelButtonPressed(self):
        print("L2 Products - Cancel Pressed")
        self.close()  
        
    

