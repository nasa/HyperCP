''' Establish and process configuration settings. '''
import collections
import json
import os
import shutil

from Source import PATH_TO_CONFIG, PACKAGE_DIR


class ConfigFile:
    ''' An object to establish and process the configuration settings and file. '''
    filename = ''
    settings = collections.OrderedDict()
    products = collections.OrderedDict()
    minDeglitchBand = 350
    maxDeglitchBand = 850


    # Creates the calibration file folder if not exist
    @staticmethod
    def createCalibrationFolder():
        #print("ConfigFile - createCalibrationFolder")
        fp = ConfigFile.getCalibrationDirectory()
        os.makedirs(fp, exist_ok=True)


    # Generates the default configuration
    @staticmethod
    def createDefaultConfig(fileName, new=1):
        # fileName: the filename of the configuration file without path
        # if new==1:
        print("ConfigFile - Create Default Config, or fill in newly added parameters with default values.")

        if not fileName.endswith(".cfg"):
            fileName = fileName + ".cfg"
        ConfigFile.filename = fileName
        ConfigFile.settings["inDir"] = './Data'
        ConfigFile.settings["outDir"] = './Data'
        ConfigFile.settings["ancFileDir"] = './Data/Sample_Data'
        ConfigFile.settings["ancFile"] = ""
        ConfigFile.settings["CalibrationFiles"] = {}
        # ConfigFile.settings["AncFile"] = ''
        ConfigFile.settings["SensorType"] = "SeaBird" # SeaBird TriOS SoRad DALEC EsOnly (not case sensitive)
        ConfigFile.settings["fL1aUTCOffset"] = 0
        ConfigFile.settings["bL1aCleanSZA"] = 1
        ConfigFile.settings["fL1aCleanSZAMax"] = 70.0 # e.g. 60:Brewin 2016,
        ConfigFile.settings["bL1aCOD"] = 0 # Caps-on darks; TriOS only

        ConfigFile.settings["bL1aqcSunTracker"] = 1
        ConfigFile.settings["bL1aqcCleanPitchRoll"] = 1
        ConfigFile.settings["fL1aqcPitchRollPitch"] = 5 # 2-5 deg. IOCCG Draft Protocols
        ConfigFile.settings["fL1aqcPitchRollRoll"] = 5 # 2-5 deg. IOCCG Draft Protocols
        ConfigFile.settings["fL1aqcRotatorHomeAngle"] = 0.0 # Require knowledge of deployment set-up
        ConfigFile.settings["bL1aqcRotatorDelay"] = 1
        ConfigFile.settings["fL1aqcRotatorDelay"] = 2.0 # 60.0s Vandenberg 2016, but for SolarTracker, not pySAS
        ConfigFile.settings["bL1aqcRotatorAngle"] = 0
        ConfigFile.settings["fL1aqcRotatorAngleMin"] = -40.0 # Require knowledge of deployment set-up
        ConfigFile.settings["fL1aqcRotatorAngleMax"] = 40.0 # Require knowledge of deployment set-up
        ConfigFile.settings["bL1aqcCleanSunAngle"] = 1
        ConfigFile.settings["fL1aqcSunAngleMin"] = 90.0 # Zhang 2017: 45*, Mobley 1999: 90, Zibordi 2009 (and IOCCG Protocols): 90
        ConfigFile.settings["fL1aqcSunAngleMax"] = 135.0 # Zhang 2017: 90*, Mobley 1999: 135, Zibordi 2009 (and IOCCG Protocols): 90

        ConfigFile.settings["bL1aqcDeglitch"] = 1
        # These can be experimentally derived with the AnomalyDetection tool
        ConfigFile.settings["fL1aqcESWindowDark"] = 11
        ConfigFile.settings["fL1aqcESWindowLight"] = 5
        ConfigFile.settings["fL1aqcESSigmaDark"] = 3.2
        ConfigFile.settings["fL1aqcESSigmaLight"] = 2.3

        ConfigFile.settings["fL1aqcLIWindowDark"] = 11
        ConfigFile.settings["fL1aqcLIWindowLight"] = 5
        ConfigFile.settings["fL1aqcLISigmaDark"] = 3.3
        ConfigFile.settings["fL1aqcLISigmaLight"] = 3.0

        ConfigFile.settings["fL1aqcLTWindowDark"] = 11
        ConfigFile.settings["fL1aqcLTWindowLight"] = 13
        ConfigFile.settings["fL1aqcLTSigmaDark"] = 3.2
        ConfigFile.settings["fL1aqcLTSigmaLight"] = 2.7

        # Optional threshold values for L1AQC processing of light & dark data (see AnomalyDetection tool)
        ConfigFile.settings["bL1aqcThreshold"] = 0
        ConfigFile.settings["fL1aqcESMinDark"] = None
        ConfigFile.settings["fL1aqcESMinLight"] = None
        ConfigFile.settings["fL1aqcESMaxDark"] = None
        ConfigFile.settings["fL1aqcESMaxLight"] = None
        ConfigFile.settings["fL1aqcESMinMaxBandDark"] = None
        ConfigFile.settings["fL1aqcESMinMaxBandLight"] = None
        ConfigFile.settings["fL1aqcLIMinDark"] = None
        ConfigFile.settings["fL1aqcLIMinLight"] = None
        ConfigFile.settings["fL1aqcLIMaxDark"] = None
        ConfigFile.settings["fL1aqcLIMaxLight"] = None
        ConfigFile.settings["fL1aqcLIMinMaxBandDark"] = None
        ConfigFile.settings["fL1aqcLIMinMaxBandLight"] = None
        ConfigFile.settings["fL1aqcLTMinDark"] = None
        ConfigFile.settings["fL1aqcLTMinLight"] = None
        ConfigFile.settings["fL1aqcLTMaxDark"] = None
        ConfigFile.settings["fL1aqcLTMaxLight"] = None
        ConfigFile.settings["fL1aqcLTMinMaxBandDark"] = None
        ConfigFile.settings["fL1aqcLTMinMaxBandLight"] = None

        ConfigFile.settings["fL1aqcAnomalyStep"] = 20

        ConfigFile.settings["bL1bGetAnc"] = 0
        ConfigFile.settings["fL1bDefaultWindSpeed"] = 5.0
        ConfigFile.settings["fL1bDefaultAOD"] = 0.2
        ConfigFile.settings["fL1bDefaultSalt"] = 35.0
        ConfigFile.settings["fL1bDefaultSST"] = 26.0
        ConfigFile.settings["bL1bCal"] = 1  # 1 for Factory, 2 for Class, 3 for Instrument Full
        ConfigFile.settings["FullCalDir"] = PACKAGE_DIR
        ConfigFile.settings['RadCalDir'] = PACKAGE_DIR
        ConfigFile.settings['FidRadDB'] = 0

        ConfigFile.settings["fL1bInterpInterval"] = 3.3 #3.3 is nominal HyperOCR; Brewin 2016 uses 3.5 nm
        ConfigFile.settings["bL1bPlotTimeInterp"] = 0
        ConfigFile.settings["fL1bPlotInterval"] = 20 # nm

        ConfigFile.settings["bL1bqcLtUVNIR"] = 1
        ConfigFile.settings["fL1bqcMaxWind"] = 10.0 # 6-7 m/s: IOCCG Draft Protocols, D'Alimonte pers. comm. 2019; 10 m/s: NASA SeaWiFS Protocols; 15 m/s: Zibordi 2009,
        ConfigFile.settings["fL1bqcSZAMin"] = 20 # e.g. 20: Zhang 2017, depends on wind
        ConfigFile.settings["fL1bqcSZAMax"] = 60 # e.g. 60:Brewin 2016,

        ConfigFile.settings["bL1bqcEnableSpecQualityCheck"] = 1
        ConfigFile.settings["bL1bqcEnableSpecQualityCheckPlot"] = 1
        ConfigFile.settings["fL1bqcSpecFilterEs"] = 5
        ConfigFile.settings["fL1bqcSpecFilterLi"] = 8
        ConfigFile.settings["fL1bqcSpecFilterLt"] = 3

        ConfigFile.settings["bL1bqcEnableQualityFlags"] = 0
        ConfigFile.settings["fL1bqcCloudFlag"] = 0.05 # 0.05 Ruddick 2006, IOCCG Protocols
        ConfigFile.settings["fL1bqcSignificantEsFlag"] = 2.0 # Wernand 2002
        ConfigFile.settings["fL1bqcDawnDuskFlag"] = 1.0 # Wernand 2002
        ConfigFile.settings["fL1bqcRainfallHumidityFlag"] = 1.095  # ?? Wang? # Wernand 2002 uses Es(940/370), with >0.25 dry, 0.2-0.25 humid, <=0.25 rain

        ConfigFile.settings["fL2SVA"] = 40 # Sensor viewing angle. 30 or 40 deg.
        ConfigFile.settings["bL2Stations"] = 0
        ConfigFile.settings["fL2TimeInterval"] = 300
        ConfigFile.settings["bL2EnablePercentLt"] = 1
        ConfigFile.settings["fL2PercentLt"] = 10 # 5% Hooker et al. 2002, Hooker and Morel 2003; <10% IOCCG Protocols

        ConfigFile.settings["fL2RhoSky"] = 0.0256 # Mobley 1999
        ConfigFile.settings["bL23CRho"] = 0
        ConfigFile.settings["bL2ZhangRho"] = 0
        ConfigFile.settings["bL2DefaultRho"] = 1

        ConfigFile.settings["bL2PerformNIRCorrection"] = 1
        ConfigFile.settings["bL2SimpleNIRCorrection"] = 0 # Mobley 1999 adapted to minimum 700-800, not 750 nm
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = 1 # Ruddick 2005, Ruddick 2006 similarity spectrum

        ConfigFile.settings["bL2NegativeSpec"] = 1

        ConfigFile.settings["bL2BRDF"] = 0
        ConfigFile.settings["bL2BRDF_fQ"] = 0
        ConfigFile.settings["bL2BRDF_IOP"] = 0

        ConfigFile.settings["bL2WeightMODISA"] = 0
        ConfigFile.settings["bL2WeightSentinel3A"] = 0
        ConfigFile.settings["bL2WeightVIIRSN"] = 0
        ConfigFile.settings["bL2WeightMODIST"] = 0
        ConfigFile.settings["bL2WeightSentinel3B"] = 0
        ConfigFile.settings["bL2WeightVIIRSJ"] = 0

        ConfigFile.settings["bL2PlotRrs"] = 1
        ConfigFile.settings["bL2PlotnLw"] = 1
        ConfigFile.settings["bL2PlotEs"] = 1
        ConfigFile.settings["bL2PlotLi"] = 1
        ConfigFile.settings["bL2PlotLt"] = 1

        ConfigFile.settings["bL2UncertaintyBreakdownPlot"] = 0

        ConfigFile.products["bL2PlotProd"] = 0
        ConfigFile.products["bL2Prodoc3m"] = 0
        ConfigFile.products["bL2Prodkd490"] = 0
        ConfigFile.products["bL2Prodpic"] = 0
        ConfigFile.products["bL2Prodpoc"] = 0
        ConfigFile.products["bL2Prodipar"] = 0
        ConfigFile.products["bL2Prodavw"] = 0
        ConfigFile.products["bL2Prodqwip"] = 0
        ConfigFile.products["bL2ProdweiQA"] = 0

        ConfigFile.products["bL2Prodgocad"] = 0
        ConfigFile.products["bL2Prodag"] = 0
        ConfigFile.products["bL2ProdSg"] = 0
        ConfigFile.products["bL2ProdDOC"] = 0

        ConfigFile.products["bL2Prodgiop"] = 0
        ConfigFile.products["bL2ProdaGiop"] = 0
        ConfigFile.products["bL2ProdadgGiop"] = 0
        ConfigFile.products["bL2ProdadgSGiop"] = 0
        ConfigFile.products["bL2ProdaphGiop"] = 0
        ConfigFile.products["bL2ProdaphSGiop"] = 0
        ConfigFile.products["bL2ProdbbGiop"] = 0
        ConfigFile.products["bL2ProdbbpGiop"] = 0
        ConfigFile.products["bL2ProdbbpSGiop"] = 0
        ConfigFile.products["bL2Prodqaa"] = 0
        ConfigFile.products["bL2ProdaQaa"] = 0
        ConfigFile.products["bL2ProdadgQaa"] = 0
        ConfigFile.products["bL2ProdaphQaa"] = 0
        ConfigFile.products["bL2ProdbQaa"] = 0
        ConfigFile.products["bL2ProdbbQaa"] = 0
        ConfigFile.products["bL2ProdbbpQaa"] = 0
        ConfigFile.products["bL2ProdcQaa"] = 0

        ConfigFile.settings["seaBASSHeaderFileName"] = os.path.splitext(fileName)[0] + ".hdr" #
        ConfigFile.settings["bL2SaveSeaBASS"] = 1
        ConfigFile.settings["bL2WriteReport"] = 1

        # If this is a new config file, save it
        if new==1:
            ConfigFile.saveConfig(fileName)


    # Saves the cfg file
    @staticmethod
    def saveConfig(filename):
        # if filename =='':
        #     # This is insane. Why is it not getting filename, even with this catch??
        #     import time
        #     print(f'{ConfigFile.filename}')
        #     print('sleep')
        #     time.sleep(8)
        #     print(f'{ConfigFile.filename}')
        #     filename = ConfigFile.filename

        print(f"ConfigFile - Save Config: {filename}")
        ConfigFile.filename = filename
        params = dict(ConfigFile.settings, **ConfigFile.products)
        params['FullCalDir'] = os.path.relpath(params['FullCalDir'])
        params['RadCalDir'] = os.path.relpath(params['RadCalDir'])
        fp = os.path.join(PATH_TO_CONFIG, filename)

        with open(fp, 'w', encoding="utf-8") as f:
            json.dump(params,f,indent=4)
        ConfigFile.createCalibrationFolder()

    # Loads the cfg file
    @staticmethod
    def loadConfig(filename):
        # print("ConfigFile - Load Config")
        calFormats = ['.cal', '.tdf', '.ini']

        # Load the default values first to insure all settings are present, then populate with saved values where possible
        ConfigFile.createDefaultConfig(filename, 0)
        goodSettingsKeys = ConfigFile.settings.keys()
        goodProdKeys = ConfigFile.products.keys()

        configPath = os.path.join(PATH_TO_CONFIG, filename)
        if os.path.isfile(configPath):
            # print(f'Populating ConfigFile with saved parameters: {filename}')
            ConfigFile.filename = filename
            text = ""
            with open(configPath, 'r', encoding="utf-8") as f:
                text = f.read()
                # ConfigFile.settings = json.loads(text, object_pairs_hook=collections.OrderedDict)
                fullCollection = json.loads(text, object_pairs_hook=collections.OrderedDict)

                for key, value in fullCollection.items():
                    if key.startswith("bL2Prod"):
                        if key in goodProdKeys:
                            ConfigFile.products[key] = value
                    else:
                        if key in goodSettingsKeys:
                            # Clean out extraneous files (e.g., Full FRM Characterizations) from CalibrationFiles
                            if key.startswith('CalibrationFiles'):
                                for k in list(value.keys()):
                                    if not any(ele.lower() in k.lower() for ele in calFormats):
                                        del value[k]
                            ConfigFile.settings[key] = value

                ConfigFile.createCalibrationFolder()
        else:
            print(f'####### Configuration {filename} not found. Using defaults. No cals.############')


    # Deletes a config
    @staticmethod
    def deleteConfig(filename):
        print("ConfigFile - Delete Config")
        configPath = os.path.join(PATH_TO_CONFIG, filename)
        seabassPath = os.path.join(PATH_TO_CONFIG, filename.split('.')[0], "hdr")
        if "seaBASSHeaderFileName" in ConfigFile.settings:
            seabassPath = os.path.join(PATH_TO_CONFIG, ConfigFile.settings["seaBASSHeaderFileName"])
            if os.path.isfile(seabassPath):
                os.remove(seabassPath)
        if os.path.isfile(configPath):
            ConfigFile.filename = filename
            calibrationPath = ConfigFile.getCalibrationDirectory()
            os.remove(configPath)
            shutil.rmtree(calibrationPath)
        if os.path.isfile(seabassPath):
            os.remove()


    @staticmethod
    def getCalibrationDirectory():
        # print("ConfigFile - getCalibrationDirectory")
        calibrationDir = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
        calibrationPath = os.path.join(PATH_TO_CONFIG, calibrationDir)
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
    