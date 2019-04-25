
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
        print("fL1bInterpInterval", ConfigFile.settings["fL1bInterpInterval"])
        print("bL2CleanSunAngle", ConfigFile.settings["bL2CleanSunAngle"])
        print("bL2CleanRotatorAngle", ConfigFile.settings["bL2CleanRotatorAngle"])
        print("fL2SunAngleMin", ConfigFile.settings["fL2SunAngleMin"])
        print("fL2SunAngleMax", ConfigFile.settings["fL2SunAngleMax"])
        print("fL2RotatorAngleMin", ConfigFile.settings["fL2RotatorAngleMin"])
        print("fL2RotatorAngleMax", ConfigFile.settings["fL2RotatorAngleMax"])
        print("fL2RotatorHomeAngle", ConfigFile.settings["fL2RotatorHomeAngle"])
        print("fL2RotatorDelay", ConfigFile.settings["fL2RotatorDelay"])    
        print("fL2TimeInterval", ConfigFile.settings["fL2TimeInterval"])
        print("bL2EnableQualityFlags", ConfigFile.settings["bL2EnableQualityFlags"])
        print("fL2SignificantEsFlag", ConfigFile.settings["fL2SignificantEsFlag"])
        print("fL2DawnDuskFlag", ConfigFile.settings["fL2DawnDuskFlag"])
        print("fL2RainfallHumidityFlag", ConfigFile.settings["fL2RainfallHumidityFlag"])
        print("fL2RhoSky", ConfigFile.settings["fL2RhoSky"])
        print("bL2EnableWindSpeedCalculation", ConfigFile.settings["bL2EnableWindSpeedCalculation"])
        print("fL2DefaultWindSpeed", ConfigFile.settings["fL2DefaultWindSpeed"])
        print("bL2PerformNIRCorrection", ConfigFile.settings["bL2PerformNIRCorrection"])        
        print("bL2EnablePercentLt", ConfigFile.settings["bL2EnablePercentLt"])
        print("fL2PercentLt", ConfigFile.settings["fL2PercentLt"])


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

        #ConfigFile.settings["CalibrationFiles"] = {'GPRMC_WithMode.tdf': 1, \
        #        'HED527A.cal': 1, 'HLD419A.cal': 1, 'HLD420A.cal': 1, 'HSE527A.cal': 1, \
        #        'HSL419A.cal': 1, 'HSL420A.cal': 1, 'SATMSG.tdf': 1, 'SATNAV0004A.tdf': 1}
        ConfigFile.settings["CalibrationFiles"] = {}

        ConfigFile.settings["bL1aCleanSZA"] = 0
        ConfigFile.settings["fL1aCleanSZAMax"] = 60.0 # e.g. Brewin 2016
        ConfigFile.settings["bL1aSaveSeaBASS"] = 0

        ConfigFile.settings["fL1bInterpInterval"] = 1.0

        ConfigFile.settings["bL2CleanSunAngle"] = 0
        ConfigFile.settings["bL2CleanRotatorAngle"] = 0
        ConfigFile.settings["fL2SunAngleMin"] = 90.0
        ConfigFile.settings["fL2SunAngleMax"] = 135.0
        ConfigFile.settings["fL2RotatorAngleMin"] = -40.0
        ConfigFile.settings["fL2RotatorAngleMax"] = 40.0
        ConfigFile.settings["fL2RotatorHomeAngle"] = 0.0
        ConfigFile.settings["fL2RotatorDelay"] = 60.0
        ConfigFile.settings["fL2TimeInterval"] = 60
        ConfigFile.settings["bL2EnableQualityFlags"] = 1
        ConfigFile.settings["fL2SignificantEsFlag"] = 2.0
        ConfigFile.settings["fL2DawnDuskFlag"] = 1.0
        ConfigFile.settings["fL2RainfallHumidityFlag"] = 1.095
        ConfigFile.settings["fL2RhoSky"] = 0.0256
        ConfigFile.settings["bL2EnableWindSpeedCalculation"] = 1
        ConfigFile.settings["fL2DefaultWindSpeed"] = 0.0
        ConfigFile.settings["bL2PerformNIRCorrection"] = 0
        ConfigFile.settings["bL2EnablePercentLt"] = 0
        ConfigFile.settings["fL2PercentLt"] = 5

        if not name.endswith(".cfg"):
            name = name + ".cfg"
        ConfigFile.filename = name
        ConfigFile.saveConfig(name)


    # Saves the cfg file
    @staticmethod
    def saveConfig(filename):
        print("ConfigFile - Save Config")

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

