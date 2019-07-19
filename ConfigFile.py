
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

        print("fL1bRotatorHomeAngle", ConfigFile.settings["fL1bRotatorHomeAngle"])
        print("fL1bRotatorDelay", ConfigFile.settings["fL1bRotatorDelay"]) 
        print("fL1bPitchRollPitch", ConfigFile.settings["fL1bPitchRollPitch"]) 
        print("fL1bPitchRollRoll", ConfigFile.settings["fL1bPitchRollRoll"]) 
        print("bL1bCleanRotatorAngle", ConfigFile.settings["bL1bCleanRotatorAngle"])
        print("fL1bRotatorAngleMin", ConfigFile.settings["fL1bRotatorAngleMin"])
        print("fL1bRotatorAngleMax", ConfigFile.settings["fL1bRotatorAngleMax"])
        print("bL1bCleanSunAngle", ConfigFile.settings["bL1bCleanSunAngle"])
        print("fL1bSunAngleMin", ConfigFile.settings["fL1bSunAngleMin"])
        print("fL1bSunAngleMax", ConfigFile.settings["fL1bSunAngleMax"])

        print("bL2Deglitch", ConfigFile.settings["bL2Deglitch"])
        print("fL2Deglitch0", ConfigFile.settings["fL2Deglitch0"])
        print("fL2Deglitch1", ConfigFile.settings["fL2Deglitch1"])
        print("fL2Deglitch2", ConfigFile.settings["fL2Deglitch2"])
        print("fL2Deglitch3", ConfigFile.settings["fL2Deglitch3"])   

        print("fL3InterpInterval", ConfigFile.settings["fL3InterpInterval"])
        print("bL3PlotTimeInterp", ConfigFile.settings["bL3PlotTimeInterp"])
        print("bL3SaveSeaBASS", ConfigFile.settings["bL3SaveSeaBASS"])
        print("seaBASSHeaderFileName", ConfigFile.settings["seaBASSHeaderFileName"])

        print("fL4RhoSky", ConfigFile.settings["fL4RhoSky"])
        print("bL4EnableWindSpeedCalculation", ConfigFile.settings["bL4EnableWindSpeedCalculation"])
        print("fL4DefaultWindSpeed", ConfigFile.settings["fL4DefaultWindSpeed"])        
        print("bL4EnableQualityFlags", ConfigFile.settings["bL4EnableQualityFlags"])
        print("fL4SignificantEsFlag", ConfigFile.settings["fL4SignificantEsFlag"])
        print("fL4DawnDuskFlag", ConfigFile.settings["fL4DawnDuskFlag"])
        print("fL4RainfallHumidityFlag", ConfigFile.settings["fL4RainfallHumidityFlag"])                        
        print("fL4TimeInterval", ConfigFile.settings["fL4TimeInterval"])
        print("bL4PerformNIRCorrection", ConfigFile.settings["bL4PerformNIRCorrection"])        
        print("bL4EnablePercentLt", ConfigFile.settings["bL4EnablePercentLt"])
        print("fL4PercentLt", ConfigFile.settings["fL4PercentLt"])


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

        ConfigFile.settings["CalibrationFiles"] = {}

        ConfigFile.settings["bL1aCleanSZA"] = 0
        ConfigFile.settings["fL1aCleanSZAMax"] = 60.0 # e.g. Brewin 2016

        ConfigFile.settings["bL1bCleanPitchRoll"] = 0
        ConfigFile.settings["fL1bPitchRollPitch"] = 5
        ConfigFile.settings["fL1bPitchRollRoll"] = 5
        ConfigFile.settings["fL1bRotatorHomeAngle"] = 0.0
        ConfigFile.settings["fL1bRotatorDelay"] = 60.0
        ConfigFile.settings["bL1bCleanRotatorAngle"] = 0
        ConfigFile.settings["fL1bRotatorAngleMin"] = -40.0
        ConfigFile.settings["fL1bRotatorAngleMax"] = 40.0
        ConfigFile.settings["bL1bCleanSunAngle"] = 0
        ConfigFile.settings["fL1bSunAngleMin"] = 90.0
        ConfigFile.settings["fL1bSunAngleMax"] = 135.0                
        ConfigFile.settings["bL1bSaveSeaBASS"] = 0


        ConfigFile.settings["bL2Deglitch"] = 0
        ConfigFile.settings["fL2Deglitch0"] = 15    # These should all have citable defaults
        ConfigFile.settings["fL2Deglitch1"] = 15     # An "info" button would be nice for the citation
        ConfigFile.settings["fL2Deglitch2"] = 3
        ConfigFile.settings["fL2Deglitch3"] = 3

        ConfigFile.settings["fL3InterpInterval"] = 3
        ConfigFile.settings["bL3PlotTimeInterp"] = 0
        ConfigFile.settings["bL3SaveSeaBASS"] = 0
        ConfigFile.settings["seaBASSHeaderFileName"] = None
                
        ConfigFile.settings["fL4TimeInterval"] = 60
        ConfigFile.settings["bL4EnableQualityFlags"] = 1
        ConfigFile.settings["fL4SignificantEsFlag"] = 2.0
        ConfigFile.settings["fL4DawnDuskFlag"] = 1.0
        ConfigFile.settings["fL4RainfallHumidityFlag"] = 1.095
        ConfigFile.settings["fL4RhoSky"] = 0.0256
        ConfigFile.settings["bL4EnableWindSpeedCalculation"] = 1
        ConfigFile.settings["fL4DefaultWindSpeed"] = 0.0
        ConfigFile.settings["bL4PerformNIRCorrection"] = 0
        ConfigFile.settings["bL4EnablePercentLt"] = 0
        ConfigFile.settings["fL4PercentLt"] = 5

        if not name.endswith(".cfg"):
            name = name + ".cfg"
        ConfigFile.filename = name
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
    # ToDo: Apply default values to any settings that are missing (in case settings are updated)
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

