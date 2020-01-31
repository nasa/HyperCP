
import collections
import json
import os
import shutil

from ConfigFile import ConfigFile

class SeaBASSHeader:
    filename = ""
    settings = collections.OrderedDict()

    @staticmethod
    def printd():
        print("SeaBASSHeader - Printd")
        print("investigators", SeaBASSHeader.settings["investigators"])
        print("affiliations", SeaBASSHeader.settings["affiliations"])
        print("contact", SeaBASSHeader.settings["contact"])
        print("experiment", SeaBASSHeader.settings["experiment"]) 
        print("cruise", SeaBASSHeader.settings["cruise"])
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
        print("wind_speed", SeaBASSHeader.settings["wind_speed"])
        print("wave_height", SeaBASSHeader.settings["wave_height"])
        print("secchi_depth", SeaBASSHeader.settings["secchi_depth"])

        print("comments", SeaBASSHeader.settings["comments"])
        print("other_comments", SeaBASSHeader.settings["other_comments"])
        print("missing", SeaBASSHeader.settings["missing"])
        print("delimiter", SeaBASSHeader.settings["delimiter"])

    # Generates the default configuration
    @staticmethod
    def createDefaultSeaBASSHeader(name):
        print("SeaBASSHeader - Create Default SeaBASSHeader")

        SeaBASSHeader.settings["investigators"] = ''
        SeaBASSHeader.settings["affiliations"] = ''
        SeaBASSHeader.settings["contact"] = ''
        SeaBASSHeader.settings["experiment"] = name.split('.')[0]
        SeaBASSHeader.settings["cruise"] = ''        
        
        SeaBASSHeader.settings["documents"] = ''        
        
        SeaBASSHeader.settings["instrument_manufacturer"] = 'Satlantic'
        SeaBASSHeader.settings["instrument_model"] = 'HyperSAS'
        SeaBASSHeader.settings["calibration_date"] = ''
        SeaBASSHeader.refreshCalibrationFiles()    
        
        SeaBASSHeader.settings["data_type"] = 'above_water'            
        SeaBASSHeader.settings["data_status"] = ''

        SeaBASSHeader.settings["water_depth"] = 'NA'
        SeaBASSHeader.settings["measurement_depth"] = '0'
        SeaBASSHeader.settings["cloud_percent"] = 'NA'        
        SeaBASSHeader.settings["wave_height"] = 'NA'
        SeaBASSHeader.settings["secchi_depth"] = 'NA'

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
        SeaBASSHeader.settings["wind_speed"] = 'NA'

        # This will update subsequently from the ConfigFile on demand
        if ConfigFile.settings["bL2RuddickRho"]:
            rhoCorr = "Ruddick2006"
        else:
            rhoCorr = "Zhang2017"
        if ConfigFile.settings["bL2EnableSpecQualityCheck"]:
            specFilt = "On"
        else:
            specFilt = "Off"
        if ConfigFile.settings["bL2EnableQualityFlags"]:
            metFilt = "On"
        else:
            metFilt = "Off"
        if ConfigFile.settings["bL2EnablePercentLt"]:
            ltFilt = "On"
        else:
            ltFilt = "Off"
        if ConfigFile.settings["bL2PerformNIRCorrection"]:
            NIRFilt = "On"
        else:
            NIRFilt = "Off"
        SeaBASSHeader.settings["comments"] =\
            f'! SZA Filter = {ConfigFile.settings["fL1aCleanSZAMax"]}\n'+\
            f'! Rotator Home Angle = {ConfigFile.settings["fL1cRotatorHomeAngle"]}\n'+\
            f'! Rotator Delay = {ConfigFile.settings["fL1cRotatorDelay"]}\n'+\
            f'! Max Pitch = {ConfigFile.settings["fL1cPitchRollPitch"]}\n'+\
            f'! Max Roll = {ConfigFile.settings["fL1cPitchRollRoll"]}\n'+\
            f'! Rotator Min = {ConfigFile.settings["fL1cRotatorAngleMin"]}\n'+\
            f'! Rotator Max = {ConfigFile.settings["fL1cRotatorAngleMax"]}\n'+\
            f'! Rel Azimuth Min = {ConfigFile.settings["fL1cSunAngleMin"]}\n'+\
            f'! Rel Azimuth Max = {ConfigFile.settings["fL1cSunAngleMax"]}\n'+\
            f'! Dark Window = {ConfigFile.settings["fL1dDeglitch0"]}\n'+\
            f'! Light Window = {ConfigFile.settings["fL1dDeglitch1"]}\n'+\
            f'! Dark Sigma = {ConfigFile.settings["fL1dDeglitch2"]}\n'+\
            f'! Light Sigma = {ConfigFile.settings["fL1dDeglitch3"]}\n'+\
            f'! Wavelength Interp Int = {ConfigFile.settings["fL1eInterpInterval"]}\n'+\
            f'! Max Wind = {ConfigFile.settings["fL2MaxWind"]}\n'+\
            f'! Min SZA = {ConfigFile.settings["fL2SZAMin"]}\n'+\
            f'! Max SZA = {ConfigFile.settings["fL2SZAMax"]}\n'+\
            f'! Spectral Filter = {specFilt}\n'+\
            f'! Filter Sigma Es = {ConfigFile.settings["fL2SpecFilterEs"]}\n'+\
            f'! Filter Sigma Li = {ConfigFile.settings["fL2SpecFilterLi"]}\n'+\
            f'! Filter Sigma Lt = {ConfigFile.settings["fL2SpecFilterLt"]}\n'+\
            f'! Meteorological Filter = {metFilt}\n'+\
            f'! Cloud Flag = {ConfigFile.settings["fL2CloudFlag"]}\n'+\
            f'! Es Flag = {ConfigFile.settings["fL2SignificantEsFlag"]}\n'+\
            f'! Dawn/Dusk Flag = {ConfigFile.settings["fL2DawnDuskFlag"]}\n'+\
            f'! Rain/Humidity Flag = {ConfigFile.settings["fL2RainfallHumidityFlag"]}\n'+\
            f'! Ensemble Interval = {ConfigFile.settings["fL2TimeInterval"]}\n'+\
            f'! Percent Lt Filter = {ltFilt}\n'+\
            f'! Percent Light = {ConfigFile.settings["fL2PercentLt"]}\n'+\
            f'! Glint_Correction = {rhoCorr}\n'+\
            f'! Default Wind = {ConfigFile.settings["fL2DefaultWindSpeed"]}\n'+\
            f'! Default AOD = {ConfigFile.settings["fL2DefaultAOD"]}\n'+\
            f'! Default Salt = {ConfigFile.settings["fL2DefaultSalt"]}\n'+\
            f'! Default SST = {ConfigFile.settings["fL2DefaultSST"]}\n'+\
            f'! NIR Correction = {NIRFilt}'

        SeaBASSHeader.settings["other_comments"] = f'!\n'\
            '! Other comments...\n'\
            '!'

        SeaBASSHeader.settings["missing"] = -999
        SeaBASSHeader.settings["delimiter"] = 'comma'

        if not name.endswith(".hdr"):
            name = name + ".hdr"
        SeaBASSHeader.filename = name
        SeaBASSHeader.saveSeaBASSHeader(name)


    # Saves the hdr file
    @staticmethod
    def saveSeaBASSHeader(filename):
        print("SeaBASSHeader - Save SeaBASSHeader")

        jsn = json.dumps(SeaBASSHeader.settings)
        fp = os.path.join("Config", filename)

        #print(os.path.abspath(os.curdir))
        with open(fp, 'w') as f:
            f.write(jsn)
        # SeaBASSHeader.createCalibrationFolder()

    # Loads the hdr file
    # ToDo: Apply default values to any settings that are missing (in case settings are updated)
    @staticmethod
    def loadSeaBASSHeader(filename):
        # print("SeaBASSHeader - Load seaBASSHeader")
        seaBASSHeaderPath = os.path.join("Config", filename)
        if os.path.isfile(seaBASSHeaderPath):
            SeaBASSHeader.filename = filename
            text = ""
            with open(seaBASSHeaderPath, 'r') as f:
                text = f.read()
                SeaBASSHeader.settings = json.loads(text, object_pairs_hook=collections.OrderedDict)
                # SeaBASSHeader.createCalibrationFolder()

    # Deletes a seaBASSHeader
    @staticmethod
    def deleteSeaBASSHeader(filename):
        print("SeaBASSHeader - Delete SeaBASSHeader")
        seaBASSHeaderPath = os.path.join("Config", filename)
        if os.path.isfile(seaBASSHeaderPath):
            SeaBASSHeader.filename = filename
            calibrationPath = ConfigFile.getCalibrationDirectory()
            os.remove(seaBASSHeaderPath)
            # shutil.rmtree(calibrationPath)
        

    @staticmethod
    def refreshCalibrationFiles():
        print("SeaBASSHeader - refreshCalibrationFiles")
        calibrationPath = ConfigFile.getCalibrationDirectory()
        files = os.listdir(calibrationPath)

        # newCalibrationFiles = {}
        # calibrationFiles = ConfigFile.settings["CalibrationFiles"]
        
        # for file in files:
        #     if file in calibrationFiles:
        #         newCalibrationFiles[file] = calibrationFiles[file]
        #     else:
        #         newCalibrationFiles[file] = {"enabled": 0, "frameType": "Not Required"}

        SeaBASSHeader.settings["calibration_files"] = (','.join(files))
    
