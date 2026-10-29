'''Establish class to hold Main window configurations'''
import os
import collections
import json
from tempfile import NamedTemporaryFile

from Source import PATH_TO_CONFIG
from Source import PATH_TO_DATA


class MainConfig:
    '''Class to hold Main window configurations'''
    fileName = "main.config"
    settings = collections.OrderedDict()

    # Saves the cfg file
    @staticmethod
    def saveConfig(fileName):
        # print("MainConfig - Save MainConfig")
        # jsn = json.dumps(MainConfig.settings)
        fp = os.path.join(PATH_TO_CONFIG, fileName)

        config_dir = os.path.dirname(fp)
        os.makedirs(config_dir, exist_ok=True)
        temp_file_path = None
        try:
            with NamedTemporaryFile("w", dir=config_dir, suffix='.tmp', delete=False, encoding="utf-8") as temp_file:
                json.dump(MainConfig.settings, temp_file, indent=4)
                temp_file_path = temp_file.name
            os.replace(temp_file_path, fp)
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        # ConfigFile.saveConfig(ConfigFile.filename)

    # Loads the cfg file
    @staticmethod
    def loadConfig(fileName, version):
        # print("MainConfig - Load MainConfig")

        # Load the default values first to insure all settings are present, then populate with saved values where possible
        MainConfig.createDefaultConfig(fileName,version)

        configPath = os.path.join(PATH_TO_CONFIG, fileName)
        if os.path.isfile(configPath):
            with open(configPath, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                raise ValueError(f"Config file {configPath} is empty.")
            fullCollection = json.loads(content, object_pairs_hook=collections.OrderedDict)
            for key, value in fullCollection.items():
                if isinstance(value,str) and PATH_TO_DATA in value:
                    value = value.replace(PATH_TO_DATA,'./Data')
                if isinstance(value,str) and PATH_TO_CONFIG in value:
                    value = value.replace(PATH_TO_CONFIG,'./Config')
                MainConfig.settings[key] = value

    # Generates the default configuration
    @staticmethod
    def createDefaultConfig(fileName, version):
        # print("MainConfig - Set MainConfig settings defaults prior to populating with saved settings.")

        # Make all paths relative to HyperCP
        MainConfig.settings["cfgFile"] = fileName
        MainConfig.settings["cfgPath"] = os.path.join('./Config',fileName)
        MainConfig.settings["version"] = version
        MainConfig.settings["inDir"] = './Data/Sample_Data'
        MainConfig.settings["outDir"] = './Data/Sample_Data'
        MainConfig.settings["ancFileDir"] = './Data/Sample_Data'
        MainConfig.settings["ancFile"] = ""
        MainConfig.settings["popQuery"] = 0
        MainConfig.settings["deleteConfig"] = False # Avoids saving a deleted configuration (ConfigFile) into the MainConfig settings
