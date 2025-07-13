import collections
import json
import os

from Source import PATH_TO_CONFIG
from Source.ConfigFile import ConfigFile
from Source.MainConfig import MainConfig

class SeaBASSHeader:
    filename = ""
    settings = collections.OrderedDict()

    @staticmethod
    def printd():
        print("SeaBASSHeader - Printd")
        print("version", SeaBASSHeader.settings["version"])
        print("investigators", SeaBASSHeader.settings["investigators"])
        print("affiliations", SeaBASSHeader.settings["affiliations"])
        print("contact", SeaBASSHeader.settings["contact"])
        print("experiment", SeaBASSHeader.settings["experiment"])
        print("cruise", SeaBASSHeader.settings["cruise"])
        print("platform", SeaBASSHeader.settings["platform"])
        print("station", SeaBASSHeader.settings["station"])
        print("data_file_name", SeaBASSHeader.settings["data_file_name"])
        print("original_file_name", SeaBASSHeader.settings["original_file_name"])
        print("documents", SeaBASSHeader.settings["documents"])
        print("calibration_files", SeaBASSHeader.settings["calibration_files"])

        print("instrument_manufacturer", SeaBASSHeader.settings["instrument_manufacturer"])
        print("instrument_model", SeaBASSHeader.settings["instrument_model"])
        print("calibration_date", SeaBASSHeader.settings["calibration_date"])

        print("data_type", SeaBASSHeader.settings["data_type"])
        print("data_status", SeaBASSHeader.settings["data_status"])

        print("start_date", SeaBASSHeader.settings["start_date"])
        print("end_date", SeaBASSHeader.settings["end_date"])
        print("start_time", SeaBASSHeader.settings["start_time"])
        print("end_time", SeaBASSHeader.settings["end_time"])
        print("north_latitude", SeaBASSHeader.settings["north_latitude"])
        print("south_latitude", SeaBASSHeader.settings["south_latitude"])
        print("east_longitude", SeaBASSHeader.settings["east_longitude"])
        print("west_longitude", SeaBASSHeader.settings["west_longitude"])

        print("water_depth", SeaBASSHeader.settings["water_depth"])
        print("measurement_depth", SeaBASSHeader.settings["measurement_depth"])
        print("cloud_percent", SeaBASSHeader.settings["cloud_percent"])
        print("wave_height", SeaBASSHeader.settings["wave_height"])
        print("secchi_depth", SeaBASSHeader.settings["secchi_depth"])
        print("wind_speed", SeaBASSHeader.settings["wind_speed"])
        print("nadir", SeaBASSHeader.settings["nadir"])

        print("rho_correction", SeaBASSHeader.settings["rho_correction"])
        print("NIR_residual_correction", SeaBASSHeader.settings["NIR_residual_correction"])
        print("BRDF_correction", SeaBASSHeader.settings["BRDF_correction"])

        print("comments", SeaBASSHeader.settings["comments"])
        print("other_comments", SeaBASSHeader.settings["other_comments"])
        print("missing", SeaBASSHeader.settings["missing"])
        print("delimiter", SeaBASSHeader.settings["delimiter"])

    # Generates the default configuration
    @staticmethod
    def createDefaultSeaBASSHeader(name):
        # print("SeaBASSHeader - Create Default SeaBASSHeader")

        SeaBASSHeader.settings["version"] = 'R1'
        SeaBASSHeader.settings["investigators"] = ''
        SeaBASSHeader.settings["affiliations"] = ''
        SeaBASSHeader.settings["contact"] = ''
        SeaBASSHeader.settings["experiment"] = ''
        SeaBASSHeader.settings["cruise"] = name.split('.')[0] # I generally name configuration files after cruise.
        SeaBASSHeader.settings["platform"] = ''

        SeaBASSHeader.settings["documents"] = 'README.md'

        SeaBASSHeader.settings["instrument_manufacturer"] = ''
        SeaBASSHeader.settings["instrument_model"] = ''
        SeaBASSHeader.settings["calibration_date"] = ''
        SeaBASSHeader.refreshCalibrationFiles()

        SeaBASSHeader.settings["data_type"] = 'above_water'
        SeaBASSHeader.settings["data_status"] = ''

        SeaBASSHeader.settings["water_depth"] = 'NA'
        SeaBASSHeader.settings["measurement_depth"] = '0'
        SeaBASSHeader.settings["cloud_percent"] = 'NA'
        SeaBASSHeader.settings["wave_height"] = 'NA'
        SeaBASSHeader.settings["secchi_depth"] = 'NA'
        SeaBASSHeader.settings["wind_speed"] = 'NA'

        SeaBASSHeader.settings["station"] = ''
        SeaBASSHeader.settings["data_file_name"] = ''
        SeaBASSHeader.settings["original_file_name"] = ''
        SeaBASSHeader.settings["start_date"] = ''
        SeaBASSHeader.settings["end_date"] = ''
        SeaBASSHeader.settings["start_time"] = ''
        SeaBASSHeader.settings["end_time"] = ''

        SeaBASSHeader.settings["north_latitude"] = ''
        SeaBASSHeader.settings["south_latitude"] = ''
        SeaBASSHeader.settings["east_longitude"] = ''
        SeaBASSHeader.settings["west_longitude"] = ''

        SeaBASSHeader.settings["nadir"] = '40'

        SeaBASSHeader.settings["rho_correction"] = ''
        SeaBASSHeader.settings["NIR_residual_correction"] = ''
        SeaBASSHeader.settings["BRDF_correction"] = ''


        # This will update subsequently from the ConfigFile on demand
        # if ConfigFile.settings["bL1aCleanSZA"]:
        #     szaFilt = "On"
        # else:
        #     szaFilt = "Off"
        if ConfigFile.settings["bL1aqcCleanPitchRoll"]:
            pitchRollFilt = "On"
        else:
            pitchRollFilt = "Off"
        if ConfigFile.settings["bL1aqcRotatorAngle"]:
            cleanRotFilt = "On"
        else:
            cleanRotFilt = "Off"
        if ConfigFile.settings["bL1aqcCleanSunAngle"]:
            cleanRelAzFilt = "On"
        else:
            cleanRelAzFilt = "Off"

        if ConfigFile.settings["bL1aqcDeglitch"]:
            deglitchFilt = "On"
        else:
            deglitchFilt = "Off"

        if ConfigFile.settings['fL1bCal'] == 1:
            if ConfigFile.settings['SensorType'].lower() == 'seabird':
                FRMRegime = 'Non-FRM_Class-based'
            else:
                FRMRegime = 'Factory_Calibration'
        elif ConfigFile.settings['fL1bCal'] == 2:
            FRMRegime = 'FRM_Class-based'
        elif ConfigFile.settings['fL1bCal'] == 3:
            FRMRegime = 'FRM-Full-Characterization'
        else:
            FRMRegime = None

        if ConfigFile.settings['fL1bThermal'] == 1:
            ThermalSource = 'Internal_Thermistor'
        elif ConfigFile.settings['fL1bThermal'] == 2:
            ThermalSource = 'Air_Termperature'
        elif ConfigFile.settings['fL1bThermal'] == 3:
            ThermalSource = 'Caps_On_Dark_File'
        else:
            ThermalSource = None

        if ConfigFile.settings["bL1bqcEnableSpecQualityCheck"]:
            specFilt = "On"
        else:
            specFilt = "Off"
        if ConfigFile.settings["bL1bqcEnableQualityFlags"]:
            metFilt = "On"
        else:
            metFilt = "Off"

        if ConfigFile.settings["bL2EnablePercentLt"]:
            ltFilt = "On"
        else:
            ltFilt = "Off"

        if ConfigFile.settings["bL2ZhangRho"]:
            # rhoCorr = 'Zhang et al. 2017'
            SeaBASSHeader.settings["rho_correction"] = 'Z17'
        else:
            # rhoCorr = 'Mobley 1999'
            SeaBASSHeader.settings["rho_correction"] = 'M99'

        if ConfigFile.settings["bL2PerformNIRCorrection"]:
            if ConfigFile.settings["bL2SimpleNIRCorrection"]:
                # NIRFilt = 'Mueller and Austin 1995'
                SeaBASSHeader.settings["NIR_residual_correction"] = 'MA95'
            else:
                # NIRFilt = 'Ruddick et al. 2005/2006'
                SeaBASSHeader.settings["NIR_residual_correction"] = 'R06'
        else:
            # NIRFilt = "Off"
            SeaBASSHeader.settings["NIR_residual_correction"] = 'NA'

        if ConfigFile.settings["bL2BRDF"]:
            if ConfigFile.settings["bL2BRDF_fQ"]:
                # Morel 2002
                SeaBASSHeader.settings["BRDF_correction"] = 'M02'
            elif ConfigFile.settings["bL2BRDF_IOP"]:
                # Lee 2011
                SeaBASSHeader.settings["BRDF_correction"] = 'L11'
            elif ConfigFile.settings["bL2BRDF_O23"]:
                # Pitarch et al. 2025
                SeaBASSHeader.settings["BRDF_correction"] = 'O23'
        else:
            SeaBASSHeader.settings["BRDF_correction"] = 'noBRDF'

        if ConfigFile.settings["bL2NegativeSpec"]:
            NegativeFilt = "On"
        else:
            NegativeFilt = "Off"

        SeaBASSHeader.settings["comments"] =\
            f'! HyperInSPACE vers = {MainConfig.settings["version"]}\n'+\
            f'! HyperInSPACE Config = {ConfigFile.filename}\n'+\
            f'! Rotator Home Angle = {ConfigFile.settings["fL1aqcRotatorHomeAngle"]}\n'+\
            f'! Rotator Delay = {ConfigFile.settings["fL1aqcRotatorDelay"]}\n'+\
            f'! Pitch/Roll Filter = {pitchRollFilt}\n'+\
            f'! Max Pitch/Roll = {ConfigFile.settings["fL1aqcPitchRollPitch"]}\n'+\
            f'! Rotator Min/Max Filter = {cleanRotFilt}\n'+\
            f'! Rotator Min = {ConfigFile.settings["fL1aqcRotatorAngleMin"]}\n'+\
            f'! Rotator Max = {ConfigFile.settings["fL1aqcRotatorAngleMax"]}\n'+\
            f'! Rel Azimuth Filter = {cleanRelAzFilt}\n'+\
            f'! Rel Azimuth Min = {ConfigFile.settings["fL1aqcSunAngleMin"]}\n'+\
            f'! Rel Azimuth Max = {ConfigFile.settings["fL1aqcSunAngleMax"]}\n'+\
            f'! Deglitch Filter = {deglitchFilt}\n'+\
            f'! ES Dark Window = {ConfigFile.settings["fL1aqcESWindowDark"]}\n'+\
            f'! ES Light Window = {ConfigFile.settings["fL1aqcESWindowLight"]}\n'+\
            f'! ES Dark Sigma = {ConfigFile.settings["fL1aqcESSigmaDark"]}\n'+\
            f'! ES Light Sigma = {ConfigFile.settings["fL1aqcESSigmaLight"]}\n'+\
            f'! LI Dark Window = {ConfigFile.settings["fL1aqcLIWindowDark"]}\n'+\
            f'! LI Light Window = {ConfigFile.settings["fL1aqcLIWindowLight"]}\n'+\
            f'! LI Dark Sigma = {ConfigFile.settings["fL1aqcLISigmaDark"]}\n'+\
            f'! LI Light Sigma = {ConfigFile.settings["fL1aqcLISigmaLight"]}\n'+\
            f'! LT Dark Window = {ConfigFile.settings["fL1aqcLTWindowDark"]}\n'+\
            f'! LT Light Window = {ConfigFile.settings["fL1aqcLTWindowLight"]}\n'+\
            f'! LT Dark Sigma = {ConfigFile.settings["fL1aqcLTSigmaDark"]}\n'+\
            f'! LT Light Sigma = {ConfigFile.settings["fL1aqcLTSigmaLight"]}\n'+\
            f'! FRM Regime = {FRMRegime}\n'+\
            f'! Thermal Source = {ThermalSource}\n'+\
            f'! Default Salt = {ConfigFile.settings["fL1bDefaultSalt"]}\n'+\
            f'! Default SST = {ConfigFile.settings["fL1bDefaultSST"]}\n'+\
            f'! Default AOD = {ConfigFile.settings["fL1bDefaultAOD"]}\n'+\
            f'! Default Wind = {ConfigFile.settings["fL1bDefaultWindSpeed"]}\n'+\
            f'! Default AirTemp = {ConfigFile.settings["fL1bDefaultAirT"]}\n'+\
            f'! Wavelength Interp Int = {ConfigFile.settings["fL1bInterpInterval"]}\n'+\
            f'! Max Wind = {ConfigFile.settings["fL1bqcMaxWind"]}\n'+\
            f'! Min SZA = {ConfigFile.settings["fL1bqcSZAMin"]}\n'+\
            f'! Max SZA = {ConfigFile.settings["fL1bqcSZAMax"]}\n'+\
            f'! Spectral Filter = {specFilt}\n'+\
            f'! Filter Sigma Es = {ConfigFile.settings["fL1bqcSpecFilterEs"]}\n'+\
            f'! Filter Sigma Li = {ConfigFile.settings["fL1bqcSpecFilterLi"]}\n'+\
            f'! Filter Sigma Lt = {ConfigFile.settings["fL1bqcSpecFilterLt"]}\n'+\
            f'! Meteorological Filter = {metFilt}\n'+\
            f'! Cloud Flag = {ConfigFile.settings["fL1bqcCloudFlag"]}\n'+\
            f'! Es Flag = {ConfigFile.settings["fL1bqcSignificantEsFlag"]}\n'+\
            f'! Dawn/Dusk Flag = {ConfigFile.settings["fL1bqcDawnDuskFlag"]}\n'+\
            f'! Rain/Humidity Flag = {ConfigFile.settings["fL1bqcRainfallHumidityFlag"]}\n'+\
            f'! Ensemble Interval = {ConfigFile.settings["fL2TimeInterval"]}\n'+\
            f'! Percent Lt Filter = {ltFilt}\n'+\
            f'! Percent Light = {ConfigFile.settings["fL2PercentLt"]}\n'+\
            f'! Remove Negatives = {NegativeFilt}'
            # f'! Processing DateTime = {time.asctime()}'

        SeaBASSHeader.settings["other_comments"] = '!\n'\
            '! Other comments...\n'\
            '!'

        SeaBASSHeader.settings["missing"] = -9999
        SeaBASSHeader.settings["delimiter"] = 'comma'

        if name != "temp":
            if not name.endswith(".hdr"):
                name = name + ".hdr"
            SeaBASSHeader.filename = name
            SeaBASSHeader.saveSeaBASSHeader(name)


    # Saves the hdr file
    @staticmethod
    def saveSeaBASSHeader(filename):
        print("SeaBASSHeader - Save SeaBASSHeader")

        fp = os.path.join(PATH_TO_CONFIG, filename)

        with open(fp, 'w', encoding="utf-8") as f:
            json.dump(SeaBASSHeader.settings,f,indent=4)

    # Loads the hdr file
    @staticmethod
    def loadSeaBASSHeader(filename):
        # To accomodate new header fields with old headers, start with default.
        #   Eliminate obsolete headers
        SeaBASSHeader.createDefaultSeaBASSHeader("temp")
        goodSettingsKeys = SeaBASSHeader.settings.keys()

        # print("SeaBASSHeader - Load seaBASSHeader")
        seaBASSHeaderPath = os.path.join(PATH_TO_CONFIG, filename)
        if os.path.isfile(seaBASSHeaderPath):
            SeaBASSHeader.filename = filename
            text = ""
            with open(seaBASSHeaderPath, 'r', encoding="utf-8") as f:
                text = f.read()
                # SeaBASSHeader.settings = json.loads(text, object_pairs_hook=collections.OrderedDict)
                fullCollection = json.loads(text, object_pairs_hook=collections.OrderedDict)
                for key, value in fullCollection.items():
                    if key in goodSettingsKeys:
                        SeaBASSHeader.settings[key] = value
                # SeaBASSHeader.createCalibrationFolder()

    # Deletes a seaBASSHeader
    @staticmethod
    def deleteSeaBASSHeader(filename):
        print("SeaBASSHeader - Delete SeaBASSHeader")
        seaBASSHeaderPath = os.path.join(PATH_TO_CONFIG, filename)
        if os.path.isfile(seaBASSHeaderPath):
            SeaBASSHeader.filename = filename
            os.remove(seaBASSHeaderPath)
            # shutil.rmtree(calibrationPath)

    @staticmethod
    def refreshCalibrationFiles():
        # print("SeaBASSHeader - refreshCalibrationFiles")
        calibrationPath = ConfigFile.getCalibrationDirectory()
        files = os.listdir(calibrationPath)
        if ConfigFile.settings['fL1bCal'] != 3:
            # Only keep the full characterization files if running Full FRM
            files = [item for item in files if not item.startswith('CP')]

        SeaBASSHeader.settings["calibration_files"] = (','.join(files))


