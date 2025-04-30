'''Establish class to hold Main window configurations'''
import os
import collections
import json
# import time

from Source import PATH_TO_CONFIG
from Source.ConfigFile import ConfigFile

class MainConfig:
    '''Class to hold Main window configurations'''
    fileName = "main.config"
    settings = collections.OrderedDict()

    # Saves the cfg file
    @staticmethod
    def saveConfig(fileName):
        print("MainConfig - Save Config")
        # jsn = json.dumps(MainConfig.settings)
        fp = os.path.join(PATH_TO_CONFIG, fileName)

        with open(fp, 'w', encoding="utf-8") as f:
            json.dump(MainConfig.settings,f,indent=4)
            # f.write(jsn)
        ConfigFile.saveConfig(ConfigFile.filename)

    # Loads the cfg file
    @staticmethod
    def loadConfig(fileName, version):
        print("MainConfig - Load Config")

        # Load the default values first to insure all settings are present, then populate with saved values where possible
        MainConfig.createDefaultConfig(fileName,version)

        configPath = os.path.join(PATH_TO_CONFIG, fileName)
        if os.path.isfile(configPath):
            text = ""
            with open(configPath, 'r', encoding="utf-8") as f:
                text = f.read()
                fullCollection = json.loads(text, object_pairs_hook=collections.OrderedDict)

                for key, value in fullCollection.items():
                    MainConfig.settings[key] = value
        # else:
        #     MainConfig.createDefaultConfig(fileName, version)

    # Generates the default configuration
    @staticmethod
    def createDefaultConfig(fileName, version):
        print("MainConfig - Refresh or create from default Config")

        MainConfig.settings["cfgFile"] = fileName
        MainConfig.settings["cfgPath"] = os.path.join('./Config',fileName)
        MainConfig.settings["version"] = version
        MainConfig.settings["inDir"] = './Data'
        MainConfig.settings["outDir"] = './Data'
        MainConfig.settings["ancFileDir"] = './Data/Sample_Data'
        MainConfig.settings["ancFile"] = ""
        MainConfig.settings["popQuery"] = 0
