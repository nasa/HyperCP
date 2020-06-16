
import collections
import json
import os
import shutil

class ConfigFile:
    filename = ""
    settings = collections.OrderedDict()

    @staticmethod
    def printd():
        print("ConfigFile - Printd")
        print("bL1aCleanSZA", ConfigFile.settings["bL1aCleanSZA"])
        print("fL1aCleanSZAMax", ConfigFile.settings["fL1aCleanSZAMax"])

        print("bL1cSolarTracker", ConfigFile.settings["bL1cSolarTracker"]) 
        print("fL1cRotatorHomeAngle", ConfigFile.settings["fL1cRotatorHomeAngle"])
        print("bL1cRotatorDelay", ConfigFile.settings["bL1cRotatorDelay"]) 
        print("fL1cRotatorDelay", ConfigFile.settings["fL1cRotatorDelay"]) 
        print("bL1cCleanPitchRoll", ConfigFile.settings["bL1cCleanPitchRoll"])
        print("fL1cPitchRollPitch", ConfigFile.settings["fL1cPitchRollPitch"]) 
        print("fL1cPitchRollRoll", ConfigFile.settings["fL1cPitchRollRoll"]) 
        print("bL1cRotatorAngle", ConfigFile.settings["bL1cRotatorAngle"])
        print("fL1cRotatorAngleMin", ConfigFile.settings["fL1cRotatorAngleMin"])
        print("fL1cRotatorAngleMax", ConfigFile.settings["fL1cRotatorAngleMax"])
        print("bL1cCleanSunAngle", ConfigFile.settings["bL1cCleanSunAngle"])
        print("fL1cSunAngleMin", ConfigFile.settings["fL1cSunAngleMin"])
        print("fL1cSunAngleMax", ConfigFile.settings["fL1cSunAngleMax"])

        print("bL1dDeglitch", ConfigFile.settings["bL1dDeglitch"])
        print("fL1dDeglitch0", ConfigFile.settings["fL1dDeglitch0"])
        print("fL1dDeglitch1", ConfigFile.settings["fL1dDeglitch1"])
        print("fL1dDeglitch2", ConfigFile.settings["fL1dDeglitch2"])
        print("fL1dDeglitch3", ConfigFile.settings["fL1dDeglitch3"])
        print("bL1dAnomalyStep", ConfigFile.settings["bL1dAnomalyStep"])   

        print("fL1eInterpInterval", ConfigFile.settings["fL1eInterpInterval"])
        print("bL1ePlotTimeInterp", ConfigFile.settings["bL1ePlotTimeInterp"])
        print("bL1eSaveSeaBASS", ConfigFile.settings["bL1eSaveSeaBASS"])
        print("seaBASSHeaderFileName", ConfigFile.settings["seaBASSHeaderFileName"])

        print("bL2pGetAnc", ConfigFile.settings["bL2pGetAnc"])
        print("bL2pObpgCreds", ConfigFile.settings["bL2pObpgCreds"])

        print("bL2LtUVNIR", ConfigFile.settings["bL2LtUVNIR"])
        print("fL2MaxWind", ConfigFile.settings["fL2MaxWind"])
        print("fL2SZAMin", ConfigFile.settings["fL2SZAMin"])
        print("fL2SZAMax", ConfigFile.settings["fL2SZAMax"])
        
        print("bL2EnableSpecQualityCheck", ConfigFile.settings["bL2EnableSpecQualityCheck"])
        print("fL2SpecFilterEs", ConfigFile.settings["fL2SpecFilterEs"])
        print("fL2SpecFilterLi", ConfigFile.settings["fL2SpecFilterLi"])
        print("fL2SpecFilterLt", ConfigFile.settings["fL2SpecFilterLt"])
        
        print("bL2EnableQualityFlags", ConfigFile.settings["bL2EnableQualityFlags"])
        print("fL2CloudFlag", ConfigFile.settings["fL2CloudFlag"])
        print("fL2SignificantEsFlag", ConfigFile.settings["fL2SignificantEsFlag"])
        print("fL2DawnDuskFlag", ConfigFile.settings["fL2DawnDuskFlag"])
        print("fL2RainfallHumidityFlag", ConfigFile.settings["fL2RainfallHumidityFlag"]) 

        print("fL2TimeInterval", ConfigFile.settings["fL2TimeInterval"])
        print("bL2EnablePercentLt", ConfigFile.settings["bL2EnablePercentLt"])
        print("fL2PercentLt", ConfigFile.settings["fL2PercentLt"])

        print("fL2RhoSky", ConfigFile.settings["fL2RhoSky"])
        print("fL2DefaultWindSpeed", ConfigFile.settings["fL2DefaultWindSpeed"])   
        print("fL2DefaultAOD", ConfigFile.settings["fL2DefaultAOD"])
        print("fL2DefaultSalt", ConfigFile.settings["fL2DefaultSalt"])
        print("fL2DefaultSST", ConfigFile.settings["fL2DefaultSST"])
        print("bL2RuddickRho", ConfigFile.settings["bL2RuddickRho"])
        print("bL2ZhangRho", ConfigFile.settings["bL2ZhangRho"])                                            
        print("bL2DefaultRho", ConfigFile.settings["bL2DefaultRho"])
        
        print("bL2PerformNIRCorrection", ConfigFile.settings["bL2PerformNIRCorrection"])        
        print("bL2SimpleNIRCorrection", ConfigFile.settings["bL2SimpleNIRCorrection"])    
        print("bL2SimSpecNIRCorrection", ConfigFile.settings["bL2SimSpecNIRCorrection"])

        print("bL2NegativeSpec", ConfigFile.settings["bL2NegativeSpec"])
        
        print("bL2WeightMODISA", ConfigFile.settings["bL2WeightMODISA"])
        print("bL2WeightSentinel3A", ConfigFile.settings["bL2WeightSentinel3A"])
        print("bL2WeightVIIRSN", ConfigFile.settings["bL2WeightVIIRSN"])
        print("bL2WeightMODISA", ConfigFile.settings["bL2WeightMODIST"])
        print("bL2WeightSentinel3A", ConfigFile.settings["bL2WeightSentinel3B"])
        print("bL2WeightVIIRSN", ConfigFile.settings["bL2WeightVIIRSJ"])

        print("bL2PlotRrs", ConfigFile.settings["bL2PlotRrs"])
        print("bL2PlotnLw", ConfigFile.settings["bL2PlotnLw"])
        print("bL2PlotEs", ConfigFile.settings["bL2PlotEs"])
        print("bL2PlotLi", ConfigFile.settings["bL2PlotLi"])
        print("bL2PlotLt", ConfigFile.settings["bL2PlotLt"])

        print("bL2oc4", ConfigFile.settings["bL2oc4"])
        print("bL2aot", ConfigFile.settings["bL2aot"])
        print("bL2kd490", ConfigFile.settings["bL2kd490"])
        print("bL2pic", ConfigFile.settings["bL2pic"])
        print("bL2poc", ConfigFile.settings["bL2poc"])
        print("bL2par", ConfigFile.settings["bL2par"])
        print("bL2avr", ConfigFile.settings["bL2avr"])
        print("bL2giop", ConfigFile.settings["bL2giop"])
        print("bL2aGiop", ConfigFile.settings["bL2aGiop"])
        print("bL2adgGiop", ConfigFile.settings["bL2adgGiop"])
        print("bL2adgSGiop", ConfigFile.settings["bL2adgSGiop"])
        print("bL2aphGiop", ConfigFile.settings["bL2aphGiop"])
        print("bL2aphSGiop", ConfigFile.settings["bL2aphSGiop"])
        print("bL2bbGiop", ConfigFile.settings["bL2bbGiop"])
        print("bL2bbpGiop", ConfigFile.settings["bL2bbpGiop"])
        print("bL2bbpSGiop", ConfigFile.settings["bL2bbpSGiop"])
        print("bL2qaa", ConfigFile.settings["bL2qaa"])
        print("bL2aQaa", ConfigFile.settings["bL2aQaa"])
        print("bL2adgQaa", ConfigFile.settings["bL2adgQaa"])
        print("bL2aphQaa", ConfigFile.settings["bL2aphQaa"])
        print("bL2bQaa", ConfigFile.settings["bL2bQaa"])
        print("bL2bbQaa", ConfigFile.settings["bL2bbQaa"])
        print("bL2bbpQaa", ConfigFile.settings["bL2bbpQaa"])
        print("bL2cQaa", ConfigFile.settings["bL2cQaa"])
        


        print("bL2SaveSeaBASS", ConfigFile.settings["bL2SaveSeaBASS"])


    # Creates the calibration file folder if not exist
    @staticmethod
    def createCalibrationFolder():
        #print("ConfigFile - createCalibrationFolder")
        fp = ConfigFile.getCalibrationDirectory()
        os.makedirs(fp, exist_ok=True)


    # Generates the default configuration
    @staticmethod
    def createDefaultConfig(name):
        print("ConfigFile - Create Default Config")

        if not name.endswith(".cfg"):
            name = name + ".cfg"
        ConfigFile.filename = name

        ConfigFile.settings["CalibrationFiles"] = {}

        ConfigFile.settings["bL1aCleanSZA"] = 0
        ConfigFile.settings["fL1aCleanSZAMax"] = 60.0 # e.g. 60:Brewin 2016, 

        ConfigFile.settings["bL1cSolarTracker"] = 1 
        ConfigFile.settings["bL1cCleanPitchRoll"] = 0
        ConfigFile.settings["fL1cPitchRollPitch"] = 5 # 2-5 deg. IOCCG Draft Protocols
        ConfigFile.settings["fL1cPitchRollRoll"] = 5 # 2-5 deg. IOCCG Draft Protocols
        ConfigFile.settings["fL1cRotatorHomeAngle"] = 0.0 # Require knowledge of deployment set-up
        ConfigFile.settings["bL1cRotatorDelay"] = 0 
        ConfigFile.settings["fL1cRotatorDelay"] = 60.0 # Vandenberg 2016
        ConfigFile.settings["bL1cRotatorAngle"] = 0
        ConfigFile.settings["fL1cRotatorAngleMin"] = -40.0 # Require knowledge of deployment set-up
        ConfigFile.settings["fL1cRotatorAngleMax"] = 40.0 # Require knowledge of deployment set-up
        ConfigFile.settings["bL1cCleanSunAngle"] = 0
        ConfigFile.settings["fL1cSunAngleMin"] = 90.0 # Zhang 2017: 45*, Mobley 1999: 90, Zibordi 2009 (and IOCCG Protocols): 90
        ConfigFile.settings["fL1cSunAngleMax"] = 135.0 # Zhang 2017: 90*, Mobley 1999: 135, Zibordi 2009 (and IOCCG Protocols): 90        

        ConfigFile.settings["bL1dDeglitch"] = 0
        ConfigFile.settings["fL1dDeglitch0"] = 9   # These can be experimentally derived with the AnomalyDetection tool
        ConfigFile.settings["fL1dDeglitch1"] = 11     
        ConfigFile.settings["fL1dDeglitch2"] = 2.7
        ConfigFile.settings["fL1dDeglitch3"] = 3.7
        ConfigFile.settings["bL1dAnomalyStep"] = 3

        ConfigFile.settings["fL1eInterpInterval"] = 3.5 # Brewin 2016 uses 3.5 nm
        ConfigFile.settings["bL1ePlotTimeInterp"] = 0
        ConfigFile.settings["bL1eSaveSeaBASS"] = 0
        ConfigFile.settings["seaBASSHeaderFileName"] = os.path.splitext(name)[0] + ".hdr" # 

        ConfigFile.settings["bL2pGetAnc"] = 0
        ConfigFile.settings["bL2pObpgCreds"] = 0
                
        ConfigFile.settings["bL2LtUVNIR"] = 1
        ConfigFile.settings["fL2MaxWind"] = 7.0 # 6-7 m/s: IOCCG Draft Protocols, D'Alimonte pers. comm. 2019; 10 m/s: NASA SeaWiFS Protocols; 15 m/s: Zibordi 2009, 
        ConfigFile.settings["fL2SZAMin"] = 20 # e.g. 20: Zhang 2017, depends on wind
        ConfigFile.settings["fL2SZAMax"] = 60 # e.g. 60:Brewin 2016,
        
        ConfigFile.settings["bL2EnableSpecQualityCheck"] = 1
        ConfigFile.settings["fL2SpecFilterEs"] = 5
        ConfigFile.settings["fL2SpecFilterLi"] = 8
        ConfigFile.settings["fL2SpecFilterLt"] = 3

        ConfigFile.settings["bL2EnableQualityFlags"] = 1
        ConfigFile.settings["fL2CloudFlag"] = 0.05 # Ruddick 2006, IOCCG Protocols
        ConfigFile.settings["fL2SignificantEsFlag"] = 2.0 # Wernand 2002
        ConfigFile.settings["fL2DawnDuskFlag"] = 1.0 # Wernand 2002
        ConfigFile.settings["fL2RainfallHumidityFlag"] = 1.095  # ?? Wang? # Wernand 2002 uses Es(940/370), with >0.25 dry, 0.2-0.25 humid, <=0.25 rain      

        ConfigFile.settings["bL2Stations"] = 0
        ConfigFile.settings["fL2TimeInterval"] = 300
        ConfigFile.settings["bL2EnablePercentLt"] = 0
        ConfigFile.settings["fL2PercentLt"] = 5 # 5% Hooker et al. 2002, Hooker and Morel 2003; <10% IOCCG Protocols

        ConfigFile.settings["fL2RhoSky"] = 0.0256 # Mobley 1999
        ConfigFile.settings["fL2DefaultWindSpeed"] = 5.0        
        ConfigFile.settings["fL2DefaultAOD"] = 0.5
        ConfigFile.settings["fL2DefaultSalt"] = 35.0
        ConfigFile.settings["fL2DefaultSST"] = 26.0
        ConfigFile.settings["bL2RuddickRho"] = 1
        ConfigFile.settings["bL2ZhangRho"] = 0        
        ConfigFile.settings["bL2DefaultRho"] = 0   
                
        ConfigFile.settings["bL2PerformNIRCorrection"] = 1
        ConfigFile.settings["bL2SimpleNIRCorrection"] = 0 # Mobley 1999 adapted to minimum 700-800, not 750 nm
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = 1 # Ruddick 2005, Ruddick 2006 similarity spectrum

        ConfigFile.settings["bL2NegativeSpec"] = 1
       
        ConfigFile.settings["bL2WeightMODISA"] = 0
        ConfigFile.settings["bL2WeightSentinel3A"] = 0
        ConfigFile.settings["bL2WeightVIIRSN"] = 0        
        ConfigFile.settings["bL2WeightMODIST"] = 0
        ConfigFile.settings["bL2WeightSentinel3B"] = 0
        ConfigFile.settings["bL2WeightVIIRSJ"] = 0        
        ConfigFile.settings["bL2PlotRrs"] = 0
        ConfigFile.settings["bL2PlotnLw"] = 0
        ConfigFile.settings["bL2PlotEs"] = 0
        ConfigFile.settings["bL2PlotLi"] = 0
        ConfigFile.settings["bL2PlotLt"] = 0

        ConfigFile.settings["bL2oc4"] = 0
        ConfigFile.settings["bL2aot"] = 0
        ConfigFile.settings["bL2kd490"] = 0
        ConfigFile.settings["bL2pic"] = 0
        ConfigFile.settings["bL2poc"] = 0
        ConfigFile.settings["bL2par"] = 0
        ConfigFile.settings["bL2avr"] = 0
        ConfigFile.settings["bL2giop"] = 0
        ConfigFile.settings["bL2aGiop"] = 0
        ConfigFile.settings["bL2adgGiop"] = 0
        ConfigFile.settings["bL2adgSGiop"] = 0
        ConfigFile.settings["bL2aphGiop"] = 0
        ConfigFile.settings["bL2aphSGiop"] = 0
        ConfigFile.settings["bL2bbGiop"] = 0
        ConfigFile.settings["bL2bbpGiop"] = 0
        ConfigFile.settings["bL2bbpSGiop"] = 0
        ConfigFile.settings["bL2qaa"] = 0
        ConfigFile.settings["bL2aQaa"] = 0
        ConfigFile.settings["bL2adgQaa"] = 0
        ConfigFile.settings["bL2aphQaa"] = 0
        ConfigFile.settings["bL2bQaa"] = 0
        ConfigFile.settings["bL2bbQaa"] = 0
        ConfigFile.settings["bL2bbpQaa"] = 0
        ConfigFile.settings["bL2cQaa"] = 0

        ConfigFile.settings["bL2SaveSeaBASS"] = 0
        
        ConfigFile.saveConfig(name)


    # Saves the cfg file
    @staticmethod
    def saveConfig(filename):
        print("ConfigFile - Save Config")
        ConfigFile.filename = filename
        jsn = json.dumps(ConfigFile.settings)
        fp = os.path.join("Config", filename)

        #print(os.path.abspath(os.curdir))
        with open(fp, 'w') as f:
            f.write(jsn)
        ConfigFile.createCalibrationFolder()

    # Loads the cfg file
    @staticmethod
    def loadConfig(filename):
        # print("ConfigFile - Load Config")
        configPath = os.path.join("Config", filename)
        if os.path.isfile(configPath):
            ConfigFile.filename = filename
            text = ""
            with open(configPath, 'r') as f:
                text = f.read()
                ConfigFile.settings = json.loads(text, object_pairs_hook=collections.OrderedDict)
                ConfigFile.createCalibrationFolder()


    # Deletes a config
    @staticmethod
    def deleteConfig(filename):
        print("ConfigFile - Delete Config")
        configPath = os.path.join("Config", filename)
        if "seaBASSHeaderFileName" in ConfigFile.settings:
            seaBassConfig = os.path.join("Config", ConfigFile.settings["seaBASSHeaderFileName"])
            if os.path.isfile(seaBassConfig):
                os.remove(seaBassConfig)
        if os.path.isfile(configPath):
            ConfigFile.filename = filename
            calibrationPath = ConfigFile.getCalibrationDirectory()
            os.remove(configPath)
            shutil.rmtree(calibrationPath)
        
        

    @staticmethod
    def getCalibrationDirectory():
        # print("ConfigFile - getCalibrationDirectory")
        calibrationDir = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
        calibrationPath = os.path.join("Config", calibrationDir)
        return calibrationPath

    @staticmethod
    def refreshCalibrationFiles():
        print("ConfigFile - refreshCalibrationFiles")
        calibrationPath = ConfigFile.getCalibrationDirectory()
        files = os.listdir(calibrationPath)

        newCalibrationFiles = {}
        calibrationFiles = ConfigFile.settings["CalibrationFiles"]
        
        for file in files:
            if file in calibrationFiles:
                newCalibrationFiles[file] = calibrationFiles[file]
            else:
                newCalibrationFiles[file] = {"enabled": 0, "frameType": "Not Required"}

        ConfigFile.settings["CalibrationFiles"] = newCalibrationFiles

    @staticmethod
    def setCalibrationConfig(calFileName, enabled, frameType):
        print("ConfigFile - setCalibrationConfig")
        calibrationFiles = ConfigFile.settings["CalibrationFiles"]
        calibrationFiles[calFileName] = {"enabled": enabled, "frameType": frameType}

    @staticmethod
    def getCalibrationConfig(calFileName):
        print("ConfigFile - getCalibrationConfig")
        calibrationFiles = ConfigFile.settings["CalibrationFiles"]
        return calibrationFiles[calFileName]

