
import collections
import json
import os
import shutil

class ConfigFile:
    filename = ''
    settings = collections.OrderedDict()
    products = collections.OrderedDict()
    minDeglitchBand = 350
    maxDeglitchBand = 850

    fpHySP = os.path.dirname(__file__).split(os.path.sep)
    fpHySP[0] = os.path.sep
    fpHySP[-1] = ''
    fpHySP = os.path.join(*fpHySP)

    @staticmethod
    def printd():
        print("ConfigFile - Printd")
        print("AncFile", ConfigFile.settings["AncFile"])
        print("SensorType", ConfigFile.settings["SensorType"])

        print("fL1aUTCOffset", ConfigFile.settings["fL1aUTCOffset"])
        print("bL1aCleanSZA", ConfigFile.settings["bL1aCleanSZA"])
        print("fL1aCleanSZAMax", ConfigFile.settings["fL1aCleanSZAMax"])

        print("bL1aqcSolarTracker", ConfigFile.settings["bL1aqcSolarTracker"])
        print("fL1aqcRotatorHomeAngle", ConfigFile.settings["fL1aqcRotatorHomeAngle"])
        print("bL1aqcRotatorDelay", ConfigFile.settings["bL1aqcRotatorDelay"])
        print("fL1aqcRotatorDelay", ConfigFile.settings["fL1aqcRotatorDelay"])
        print("bL1aqcCleanPitchRoll", ConfigFile.settings["bL1aqcCleanPitchRoll"])
        print("fL1aqcPitchRollPitch", ConfigFile.settings["fL1aqcPitchRollPitch"])
        print("fL1aqcPitchRollRoll", ConfigFile.settings["fL1aqcPitchRollRoll"])
        print("bL1aqcRotatorAngle", ConfigFile.settings["bL1aqcRotatorAngle"])
        print("fL1aqcRotatorAngleMin", ConfigFile.settings["fL1aqcRotatorAngleMin"])
        print("fL1aqcRotatorAngleMax", ConfigFile.settings["fL1aqcRotatorAngleMax"])
        print("bL1aqcCleanSunAngle", ConfigFile.settings["bL1aqcCleanSunAngle"])
        print("fL1aqcSunAngleMin", ConfigFile.settings["fL1aqcSunAngleMin"])
        print("fL1aqcSunAngleMax", ConfigFile.settings["fL1aqcSunAngleMax"])

        print("bL1aqcDeglitch", ConfigFile.settings["bL1aqcDeglitch"])
        print("fL1aqcESWindowDark", ConfigFile.settings["fL1aqcESWindowDark"])
        print("fL1aqcESWindowLight", ConfigFile.settings["fL1aqcESWindowLight"])
        print("fL1aqcESSigmaDark", ConfigFile.settings["fL1aqcESSigmaDark"])
        print("fL1aqcESSigmaLight", ConfigFile.settings["fL1aqcESSigmaLight"])
        print("fL1aqcLIWindowDark", ConfigFile.settings["fL1aqcLIWindowDark"])
        print("fL1aqcLIWindowLight", ConfigFile.settings["fL1aqcLIWindowLight"])
        print("fL1aqcLISigmaDark", ConfigFile.settings["fL1aqcLISigmaDark"])
        print("fL1aqcLISigmaLight", ConfigFile.settings["fL1aqcLISigmaLight"])
        print("fL1aqcLTWindowDark", ConfigFile.settings["fL1aqcLTWindowDark"])
        print("fL1aqcLTWindowLight", ConfigFile.settings["fL1aqcLTWindowLight"])
        print("fL1aqcLTSigmaDark", ConfigFile.settings["fL1aqcLTSigmaDark"])
        print("fL1aqcLTSigmaLight", ConfigFile.settings["fL1aqcLTSigmaLight"])

        print("bL1aqcThreshold", ConfigFile.settings["bL1aqcThreshold"])
        print("fL1aqcESMinDark", ConfigFile.settings["fL1aqcESMinDark"])
        print("fL1aqcESMinLight", ConfigFile.settings["fL1aqcESMinLight"])
        print("fL1aqcESMaxDark", ConfigFile.settings["fL1aqcESMaxDark"])
        print("fL1aqcESMaxLight", ConfigFile.settings["fL1aqcESMaxLight"])
        print("fL1aqcESMinMaxBand", ConfigFile.settings["fL1aqcESMinMaxBand"])
        print("fL1aqcESMinMaxBand", ConfigFile.settings["fL1aqcESMinMaxBand"])
        print("fL1aqcLIMinDark", ConfigFile.settings["fL1aqcLIMinDark"])
        print("fL1aqcLIMinLight", ConfigFile.settings["fL1aqcLIMinLight"])
        print("fL1aqcLIMaxDark", ConfigFile.settings["fL1aqcLIMaxDark"])
        print("fL1aqcLIMaxLight", ConfigFile.settings["fL1aqcLIMaxLight"])
        print("fL1aqcLIMinMaxBand", ConfigFile.settings["fL1aqcLIMinMaxBand"])
        print("fL1aqcLIMinMaxBand", ConfigFile.settings["fL1aqcLIMinMaxBand"])
        print("fL1aqcLTMinDark", ConfigFile.settings["fL1aqcLTMinDark"])
        print("fL1aqcLTMinLight", ConfigFile.settings["fL1aqcLTMinLight"])
        print("fL1aqcLTMaxDark", ConfigFile.settings["fL1aqcLTMaxDark"])
        print("fL1aqcLTMaxLight", ConfigFile.settings["fL1aqcLTMaxLight"])
        print("fL1aqcLTMinMaxBand", ConfigFile.settings["fL1aqcLTMinMaxBand"])
        print("fL1aqcLTMinMaxBand", ConfigFile.settings["fL1aqcLTMinMaxBand"])

        print("fL1aqcAnomalyStep", ConfigFile.settings["fL1aqcAnomalyStep"])

        print("bL1bCal", ConfigFile.settings["bL1bCal"])
        print("RadCalDir", ConfigFile.settings["RadCalDir"])
        print("FullCalDir", ConfigFile.settings['FullCalDir'])
        print("FidRadDB", ConfigFile.settings["FidRadDB"])
        print("fL1bInterpInterval", ConfigFile.settings["fL1bInterpInterval"])
        print("bL1bPlotTimeInterp", ConfigFile.settings["bL1bPlotTimeInterp"])
        print("fL1bPlotInterval", ConfigFile.settings["fL1bPlotInterval"])

        print("bL1bGetAnc", ConfigFile.settings["bL1bGetAnc"])
        print("bL1bObpgCreds", ConfigFile.settings["bL1bObpgCreds"])

        print("bL1bqcLtUVNIR", ConfigFile.settings["bL1bqcLtUVNIR"])
        print("fL1bqcMaxWind", ConfigFile.settings["fL1bqcMaxWind"])
        print("fL1bqcSZAMin", ConfigFile.settings["fL1bqcSZAMin"])
        print("fL1bqcSZAMax", ConfigFile.settings["fL1bqcSZAMax"])

        print("bL1bqcEnableSpecQualityCheck", ConfigFile.settings["bL1bqcEnableSpecQualityCheck"])
        print("bL1bqcEnableSpecQualityCheckPlot", ConfigFile.settings["bL1bqcEnableSpecQualityCheckPlot"])
        print("fL1bqcSpecFilterEs", ConfigFile.settings["fL1bqcSpecFilterEs"])
        print("fL1bqcSpecFilterLi", ConfigFile.settings["fL1bqcSpecFilterLi"])
        print("fL1bqcSpecFilterLt", ConfigFile.settings["fL1bqcSpecFilterLt"])

        print("bL1bqcEnableQualityFlags", ConfigFile.settings["bL1bqcEnableQualityFlags"])
        print("fL1bqcCloudFlag", ConfigFile.settings["fL1bqcCloudFlag"])
        print("fL1bqcSignificantEsFlag", ConfigFile.settings["fL1bqcSignificantEsFlag"])
        print("fL1bqcDawnDuskFlag", ConfigFile.settings["fL1bqcDawnDuskFlag"])
        print("fL1bqcRainfallHumidityFlag", ConfigFile.settings["fL1bqcRainfallHumidityFlag"])

        print("bL2Stations", ConfigFile.settings["bL2Stations"])
        print("fL2TimeInterval", ConfigFile.settings["fL2TimeInterval"])
        print("bL2EnablePercentLt", ConfigFile.settings["bL2EnablePercentLt"])
        print("fL2PercentLt", ConfigFile.settings["fL2PercentLt"])

        print("fL2RhoSky", ConfigFile.settings["fL2RhoSky"])
        print("fL2DefaultWindSpeed", ConfigFile.settings["fL2DefaultWindSpeed"])
        print("fL2DefaultAOD", ConfigFile.settings["fL2DefaultAOD"])
        print("fL2DefaultSalt", ConfigFile.settings["fL2DefaultSalt"])
        print("fL2DefaultSST", ConfigFile.settings["fL2DefaultSST"])
        print("bL23CRho", ConfigFile.settings["bL23CRho"])
        print("bL2ZhangRho", ConfigFile.settings["bL2ZhangRho"])
        print("bL2DefaultRho", ConfigFile.settings["bL2DefaultRho"])

        print("bL2PerformNIRCorrection", ConfigFile.settings["bL2PerformNIRCorrection"])
        print("bL2SimpleNIRCorrection", ConfigFile.settings["bL2SimpleNIRCorrection"])
        print("bL2SimSpecNIRCorrection", ConfigFile.settings["bL2SimSpecNIRCorrection"])

        print("bL2NegativeSpec", ConfigFile.settings["bL2NegativeSpec"])

        print("bL2BRDF", ConfigFile.settings["bL2BRDF"])
        print("bL2BRDF_fQ", ConfigFile.settings["bL2BRDF_fQ"])
        print("bL2BRDF_IOP", ConfigFile.settings["bL2BRDF_IOP"])

        print("bL2WeightMODISA", ConfigFile.settings["bL2WeightMODISA"])
        print("bL2WeightSentinel3A", ConfigFile.settings["bL2WeightSentinel3A"])
        print("bL2WeightVIIRSN", ConfigFile.settings["bL2WeightVIIRSN"])
        print("bL2WeightMODIST", ConfigFile.settings["bL2WeightMODIST"])
        print("bL2WeightSentinel3A", ConfigFile.settings["bL2WeightSentinel3B"])
        print("bL2WeightVIIRSN", ConfigFile.settings["bL2WeightVIIRSJ"])

        print("bL2PlotRrs", ConfigFile.settings["bL2PlotRrs"])
        print("bL2PlotnLw", ConfigFile.settings["bL2PlotnLw"])
        print("bL2PlotEs", ConfigFile.settings["bL2PlotEs"])
        print("bL2PlotLi", ConfigFile.settings["bL2PlotLi"])
        print("bL2PlotLt", ConfigFile.settings["bL2PlotLt"])

        print("bL2Prodoc3m", ConfigFile.products["bL2Prodoc3m"])
        # print("bL2Prodaot", ConfigFile.products["bL2Prodaot"])
        print("bL2Prodkd490", ConfigFile.products["bL2Prodkd490"])
        print("bL2Prodpic", ConfigFile.products["bL2Prodpic"])
        print("bL2Prodpoc", ConfigFile.products["bL2Prodpoc"])
        print("bL2Prodipar", ConfigFile.products["bL2Prodipar"])
        print("bL2Prodavw", ConfigFile.products["bL2Prodavw"])
        print("bL2Prodqwip", ConfigFile.products["bL2Prodqwip"])
        print("bL2ProdweiQA", ConfigFile.products["bL2ProdweiQA"])

        print("bL2Prodgocad", ConfigFile.products["bL2Prodgocad"])
        print("bL2Prodag", ConfigFile.products["bL2Prodag"])
        print("bL2ProdSg", ConfigFile.products["bL2ProdSg"])
        print("bL2ProdDOC", ConfigFile.products["bL2ProdDOC"])


        print("bL2Prodgiop", ConfigFile.products["bL2Prodgiop"])
        print("bL2ProdaGiop", ConfigFile.products["bL2ProdaGiop"])
        print("bL2ProdadgGiop", ConfigFile.products["bL2ProdadgGiop"])
        print("bL2ProdadgSGiop", ConfigFile.products["bL2ProdadgSGiop"])
        print("bL2ProdaphGiop", ConfigFile.products["bL2ProdaphGiop"])
        print("bL2ProdaphSGiop", ConfigFile.products["bL2ProdaphSGiop"])
        print("bL2ProdbbGiop", ConfigFile.products["bL2ProdbbGiop"])
        print("bL2ProdbbpGiop", ConfigFile.products["bL2ProdbbpGiop"])
        print("bL2ProdbbpSGiop", ConfigFile.products["bL2ProdbbpSGiop"])
        print("bL2Prodqaa", ConfigFile.products["bL2Prodqaa"])
        print("bL2ProdaQaa", ConfigFile.products["bL2ProdaQaa"])
        print("bL2ProdadgQaa", ConfigFile.products["bL2ProdadgQaa"])
        print("bL2ProdaphQaa", ConfigFile.products["bL2ProdaphQaa"])
        print("bL2ProdbQaa", ConfigFile.products["bL2ProdbQaa"])
        print("bL2ProdbbQaa", ConfigFile.products["bL2ProdbbQaa"])
        print("bL2ProdbbpQaa", ConfigFile.products["bL2ProdbbpQaa"])
        print("bL2ProdcQaa", ConfigFile.products["bL2ProdcQaa"])

        print("bL2SaveSeaBASS", ConfigFile.settings["bL2SaveSeaBASS"])
        print("seaBASSHeaderFileName", ConfigFile.settings["seaBASSHeaderFileName"])
        print("bL2WriteReport", ConfigFile.settings["bL2WriteReport"])


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
        ConfigFile.settings["CalibrationFiles"] = {}
        ConfigFile.settings["AncFile"] = ''
        ConfigFile.settings["SensorType"] = "SeaBird" # SeaBird TriOS
        ConfigFile.settings["fL1aUTCOffset"] = 0
        ConfigFile.settings["bL1aCleanSZA"] = 0
        ConfigFile.settings["fL1aCleanSZAMax"] = 70.0 # e.g. 60:Brewin 2016,

        ConfigFile.settings["bL1aqcSolarTracker"] = 1
        ConfigFile.settings["bL1aqcCleanPitchRoll"] = 0
        ConfigFile.settings["fL1aqcPitchRollPitch"] = 5 # 2-5 deg. IOCCG Draft Protocols
        ConfigFile.settings["fL1aqcPitchRollRoll"] = 5 # 2-5 deg. IOCCG Draft Protocols
        ConfigFile.settings["fL1aqcRotatorHomeAngle"] = 0.0 # Require knowledge of deployment set-up
        ConfigFile.settings["bL1aqcRotatorDelay"] = 0
        ConfigFile.settings["fL1aqcRotatorDelay"] = 5.0 # 60.0s Vandenberg 2016, but for SolarTracker, not pySAS
        ConfigFile.settings["bL1aqcRotatorAngle"] = 0
        ConfigFile.settings["fL1aqcRotatorAngleMin"] = -40.0 # Require knowledge of deployment set-up
        ConfigFile.settings["fL1aqcRotatorAngleMax"] = 40.0 # Require knowledge of deployment set-up
        ConfigFile.settings["bL1aqcCleanSunAngle"] = 0
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
        ConfigFile.settings["bL1bObpgCreds"] = 0
        ConfigFile.settings["fL1bDefaultWindSpeed"] = 5.0
        ConfigFile.settings["fL1bDefaultAOD"] = 0.5
        ConfigFile.settings["fL1bDefaultSalt"] = 35.0
        ConfigFile.settings["fL1bDefaultSST"] = 26.0
        ConfigFile.settings["bL1bCal"] = 1  # 1 for Factory, 2 for Class, 3 for Instrument Full
        ConfigFile.settings["FullCalDir"] = os.getcwd()
        ConfigFile.settings['RadCalDir'] = os.getcwd()
        ConfigFile.settings['FidRadDB'] = False

        ConfigFile.settings["fL1bInterpInterval"] = 3.3 #3.3 is nominal HyperOCR; Brewin 2016 uses 3.5 nm
        ConfigFile.settings["bL1bPlotTimeInterp"] = 0
        ConfigFile.settings["fL1bPlotInterval"] = 20 # nm

        ConfigFile.settings["bL1bqcLtUVNIR"] = 1
        ConfigFile.settings["fL1bMaxWind"] = 10.0 # 6-7 m/s: IOCCG Draft Protocols, D'Alimonte pers. comm. 2019; 10 m/s: NASA SeaWiFS Protocols; 15 m/s: Zibordi 2009,
        ConfigFile.settings["fL1bSZAMin"] = 20 # e.g. 20: Zhang 2017, depends on wind
        ConfigFile.settings["fL1bSZAMax"] = 60 # e.g. 60:Brewin 2016,

        ConfigFile.settings["bL1bqcEnableSpecQualityCheck"] = 1
        ConfigFile.settings["bL1bqcEnableSpecQualityCheckPlot"] = 1
        ConfigFile.settings["fL1bqcSpecFilterEs"] = 5
        ConfigFile.settings["fL1bqcSpecFilterLi"] = 8
        ConfigFile.settings["fL1bqcSpecFilterLt"] = 3

        ConfigFile.settings["bL1bqcEnableQualityFlags"] = 1
        ConfigFile.settings["fL1bqcCloudFlag"] = 1.0 # 1.0 basically disregards this, though cloud cover can still be used in glint correction; 0.05 Ruddick 2006, IOCCG Protocols
        ConfigFile.settings["fL1bqcSignificantEsFlag"] = 2.0 # Wernand 2002
        ConfigFile.settings["fL1bqcDawnDuskFlag"] = 1.0 # Wernand 2002
        ConfigFile.settings["fL1bqcRainfallHumidityFlag"] = 1.095  # ?? Wang? # Wernand 2002 uses Es(940/370), with >0.25 dry, 0.2-0.25 humid, <=0.25 rain



        ConfigFile.settings["bL2Stations"] = 0
        ConfigFile.settings["fL2TimeInterval"] = 300
        ConfigFile.settings["bL2EnablePercentLt"] = 0
        ConfigFile.settings["fL2PercentLt"] = 5 # 5% Hooker et al. 2002, Hooker and Morel 2003; <10% IOCCG Protocols

        ConfigFile.settings["fL2RhoSky"] = 0.0256 # Mobley 1999
        ConfigFile.settings["bL23CRho"] = 1
        ConfigFile.settings["bL2ZhangRho"] = 0
        ConfigFile.settings["bL2DefaultRho"] = 0

        ConfigFile.settings["bL2PerformNIRCorrection"] = 1
        ConfigFile.settings["bL2SimpleNIRCorrection"] = 0 # Mobley 1999 adapted to minimum 700-800, not 750 nm
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = 1 # Ruddick 2005, Ruddick 2006 similarity spectrum

        ConfigFile.settings["bL2NegativeSpec"] = 1

        ConfigFile.settings["bL2BRDF"] = 1
        ConfigFile.settings["bL2BRDF_fQ"] = 1
        ConfigFile.settings["bL2BRDF_IOP"] = 0

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
        ConfigFile.settings["bL2SaveSeaBASS"] = 0
        ConfigFile.settings["bL2WriteReport"] = 1

        # If this is a new config file, save it
        if new==1:
            ConfigFile.saveConfig(fileName)


    # Saves the cfg file
    @staticmethod
    def saveConfig(filename):
        print("ConfigFile - Save Config")
        ConfigFile.filename = filename
        params = dict(ConfigFile.settings, **ConfigFile.products)
        jsn = json.dumps(params)
        fp = os.path.join("Config", filename)

        #print(os.path.abspath(os.curdir))
        with open(fp, 'w') as f:
            f.write(jsn)
        ConfigFile.createCalibrationFolder()

    # Loads the cfg file
    @staticmethod
    def loadConfig(filename):
        # print("ConfigFile - Load Config")

        # Load the default values first to insure all settings are present, then populate with saved values where possible
        ConfigFile.createDefaultConfig(filename, 0)

        configPath = os.path.join("Config", filename)
        if os.path.isfile(configPath):
            # print(f'Populating ConfigFile with saved parameters: {filename}')
            ConfigFile.filename = filename
            text = ""
            with open(configPath, 'r') as f:
                text = f.read()
                # ConfigFile.settings = json.loads(text, object_pairs_hook=collections.OrderedDict)
                fullCollection = json.loads(text, object_pairs_hook=collections.OrderedDict)

                for key, value in fullCollection.items():
                    if key.startswith("bL2Prod"):
                        ConfigFile.products[key] = value
                    else:
                        ConfigFile.settings[key] = value

                ConfigFile.createCalibrationFolder()
        #     return 1
        # else:
        #     print(f'Bad ConfigFile path: {configPath}')
        #     return 0


    # Deletes a config
    @staticmethod
    def deleteConfig(filename):
        print("ConfigFile - Delete Config")
        configPath = os.path.join("Config", filename)
        seabassPath = os.path.join("Config", filename.split('.')[0], "hdr")
        if "seaBASSHeaderFileName" in ConfigFile.settings:
            seabassPath = os.path.join("Config", ConfigFile.settings["seaBASSHeaderFileName"])
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

