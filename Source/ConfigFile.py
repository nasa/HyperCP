
import collections
import json
import os
import shutil

class ConfigFile:
    filename = ""
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
        print("bL1aCleanSZA", ConfigFile.settings["bL1aCleanSZA"])
        print("fL1aCleanSZAMax", ConfigFile.settings["fL1aCleanSZAMax"])

        print("bL1cSolarTracker", ConfigFile.settings["bL1cSolarTracker"])
        print("fL1aqcRotatorHomeAngle", ConfigFile.settings["fL1aqcRotatorHomeAngle"])
        print("bL1cRotatorDelay", ConfigFile.settings["bL1cRotatorDelay"])
        print("fL1aqcRotatorDelay", ConfigFile.settings["fL1aqcRotatorDelay"])
        print("bL1cCleanPitchRoll", ConfigFile.settings["bL1cCleanPitchRoll"])
        print("fL1aqcPitchRollPitch", ConfigFile.settings["fL1aqcPitchRollPitch"])
        print("fL1aqcPitchRollRoll", ConfigFile.settings["fL1aqcPitchRollRoll"])
        print("bL1cRotatorAngle", ConfigFile.settings["bL1cRotatorAngle"])
        print("fL1aqcRotatorAngleMin", ConfigFile.settings["fL1aqcRotatorAngleMin"])
        print("fL1aqcRotatorAngleMax", ConfigFile.settings["fL1aqcRotatorAngleMax"])
        print("bL1cCleanSunAngle", ConfigFile.settings["bL1cCleanSunAngle"])
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

        print("fL1bInterpInterval", ConfigFile.settings["fL1bInterpInterval"])
        print("bL1bPlotTimeInterp", ConfigFile.settings["bL1bPlotTimeInterp"])
        print("bL1bSaveSeaBASS", ConfigFile.settings["bL1bSaveSeaBASS"])
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
        print("bL23CRho", ConfigFile.settings["bL23CRho"])
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

        print("bL2Prodoc3m", ConfigFile.products["bL2Prodoc3m"])
        # print("bL2Prodaot", ConfigFile.products["bL2Prodaot"])
        print("bL2Prodkd490", ConfigFile.products["bL2Prodkd490"])
        print("bL2Prodpic", ConfigFile.products["bL2Prodpic"])
        print("bL2Prodpoc", ConfigFile.products["bL2Prodpoc"])
        print("bL2Prodipar", ConfigFile.products["bL2Prodipar"])
        print("bL2Prodavw", ConfigFile.products["bL2Prodavw"])
        print("bL2ProdweiQA", ConfigFile.products["bL2ProdweiQA"])

        print("bL2Prodgocad", ConfigFile.products["bL2Prodgocad"])
        print("bL2Prodag", ConfigFile.products["bL2Prodag"])
        # print("bL2Prodag275", ConfigFile.products["bL2Prodag275"])
        # print("bL2Prodag355", ConfigFile.products["bL2Prodag355"])
        # print("bL2Prodag380", ConfigFile.products["bL2Prodag380"])
        # print("bL2Prodag412", ConfigFile.products["bL2Prodag412"])
        # print("bL2Prodag443", ConfigFile.products["bL2Prodag443"])
        # print("bL2Prodag488", ConfigFile.products["bL2Prodag488"])
        print("bL2ProdSg", ConfigFile.products["bL2ProdSg"])
        # print("bL2ProdSg275", ConfigFile.products["bL2ProdSg275"])
        # print("bL2ProdSg300", ConfigFile.products["bL2ProdSg300"])
        # print("bL2ProdSg412", ConfigFile.products["bL2ProdSg412"])
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
        print("bL2WriteReport", ConfigFile.settings["bL2WriteReport"])


    # Creates the calibration file folder if not exist
    @staticmethod
    def createCalibrationFolder():
        #print("ConfigFile - createCalibrationFolder")
        fp = ConfigFile.getCalibrationDirectory()
        os.makedirs(fp, exist_ok=True)


    # Generates the default configuration
    @staticmethod
    def createDefaultConfig(name, new=1):
        # name: the filename of the configuration file without path
        # new: 1=yes, 0=no
        print("ConfigFile - Create Default Config")

        if not name.endswith(".cfg"):
            name = name + ".cfg"
        ConfigFile.filename = name

        ConfigFile.settings["CalibrationFiles"] = {}

        ConfigFile.settings["bL1aCleanSZA"] = 0
        ConfigFile.settings["fL1aCleanSZAMax"] = 70.0 # e.g. 60:Brewin 2016,

        ConfigFile.settings["bL1aqcSolarTracker"] = 1
        ConfigFile.settings["bL1aqcCleanPitchRoll"] = 0
        ConfigFile.settings["fL1aqcPitchRollPitch"] = 5 # 2-5 deg. IOCCG Draft Protocols
        ConfigFile.settings["fL1aqcPitchRollRoll"] = 5 # 2-5 deg. IOCCG Draft Protocols
        ConfigFile.settings["fL1aqcRotatorHomeAngle"] = 0.0 # Require knowledge of deployment set-up
        ConfigFile.settings["bL1aqcRotatorDelay"] = 0
        ConfigFile.settings["fL1aqcRotatorDelay"] = 60.0 # Vandenberg 2016
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
        ConfigFile.settings["fL1aqcESSigmaLight"] = 3.5
        ConfigFile.settings["fL1aqcLIWindowDark"] = 11
        ConfigFile.settings["fL1aqcLIWindowLight"] = 5
        ConfigFile.settings["fL1aqcLISigmaDark"] = 3.4
        ConfigFile.settings["fL1aqcLISigmaLight"] = 3.4
        ConfigFile.settings["fL1aqcLTWindowDark"] = 11
        ConfigFile.settings["fL1aqcLTWindowLight"] = 5
        ConfigFile.settings["fL1aqcLTSigmaDark"] = 3.5
        ConfigFile.settings["fL1aqcLTSigmaLight"] = 3.2

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


        ConfigFile.settings["bL1bDefaultCal"] = 1
        ConfigFile.settings["bL1bFullCal"] = 0
        ConfigFile.settings["bL1bFullFiles"] = 0
        ConfigFile.settings["fL1bInterpInterval"] = 3.3 #3.3 is nominal HyperOCR; Brewin 2016 uses 3.5 nm
        ConfigFile.settings["bL1bPlotTimeInterp"] = 0
        ConfigFile.settings["bL1bSaveSeaBASS"] = 0
        ConfigFile.settings["seaBASSHeaderFileName"] = os.path.splitext(name)[0] + ".hdr" #

        ConfigFile.settings["bL2pGetAnc"] = 0
        ConfigFile.settings["bL2pObpgCreds"] = 0

        ConfigFile.settings["bL2LtUVNIR"] = 1
        ConfigFile.settings["fL2MaxWind"] = 10.0 # 6-7 m/s: IOCCG Draft Protocols, D'Alimonte pers. comm. 2019; 10 m/s: NASA SeaWiFS Protocols; 15 m/s: Zibordi 2009,
        ConfigFile.settings["fL2SZAMin"] = 20 # e.g. 20: Zhang 2017, depends on wind
        ConfigFile.settings["fL2SZAMax"] = 60 # e.g. 60:Brewin 2016,

        ConfigFile.settings["bL2EnableSpecQualityCheck"] = 1
        ConfigFile.settings["fL2SpecFilterEs"] = 5
        ConfigFile.settings["fL2SpecFilterLi"] = 8
        ConfigFile.settings["fL2SpecFilterLt"] = 3

        ConfigFile.settings["bL2EnableQualityFlags"] = 1
        ConfigFile.settings["fL2CloudFlag"] = 1.0 # 1.0 basically disregards this, though cloud cover can still be used in glint correction; 0.05 Ruddick 2006, IOCCG Protocols
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
        ConfigFile.settings["bL23CRho"] = 1
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

        ConfigFile.products["bL2Prodoc3m"] = 0
        # ConfigFile.products["bL2Prodaot"] = 0
        ConfigFile.products["bL2Prodkd490"] = 0
        ConfigFile.products["bL2Prodpic"] = 0
        ConfigFile.products["bL2Prodpoc"] = 0
        ConfigFile.products["bL2Prodipar"] = 0
        ConfigFile.products["bL2Prodavw"] = 0
        ConfigFile.products["bL2ProdweiQA"] = 0

        ConfigFile.products["bL2Prodgocad"] = 0
        ConfigFile.products["bL2Prodag"] = 0
        # ConfigFile.products["bL2Prodag275"] = 0
        # ConfigFile.products["bL2Prodag355"] = 0
        # ConfigFile.products["bL2Prodag380"] = 0
        # ConfigFile.products["bL2Prodag412"] = 0
        # ConfigFile.products["bL2Prodag443"] = 0
        # ConfigFile.products["bL2Prodag488"] = 0
        ConfigFile.products["bL2ProdSg"] = 0
        # ConfigFile.products["bL2ProdSg275"] = 0
        # ConfigFile.products["bL2ProdSg300"] = 0
        # ConfigFile.products["bL2ProdSg412"] = 0
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

        ConfigFile.settings["bL2SaveSeaBASS"] = 0
        ConfigFile.settings["bL2WriteReport"] = 1

        # If this is a new config file, save it
        if new==1:
            ConfigFile.saveConfig(name)


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

