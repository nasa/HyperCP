import os
import collections
import json

from Source import PATH_TO_CONFIG


class MainConfig:
    fileName = "main.config"
    settings = collections.OrderedDict()

    # Saves the cfg file
    @staticmethod
    def saveConfig(fileName):
        print("ConfigFile - Save Config")
        jsn = json.dumps(MainConfig.settings)
        fp = os.path.join(PATH_TO_CONFIG, fileName)

        with open(fp, 'w') as f:
            f.write(jsn)

    # Loads the cfg file
    @staticmethod
    def loadConfig(fileName, version):
        print("MainConfig - Load Config")

        # Load the default values first to insure all settings are present, then populate with saved values where possible
        MainConfig.createDefaultConfig(fileName,version)

        configPath = os.path.join(PATH_TO_CONFIG, fileName)
        if os.path.isfile(configPath):
            text = ""
            with open(configPath, 'r') as f:
                text = f.read()
                fullCollection = json.loads(text, object_pairs_hook=collections.OrderedDict)

                for key, value in fullCollection.items():
                    MainConfig.settings[key] = value
        else:
            MainConfig.createDefaultConfig(fileName, version)

    # Generates the default configuration
    @staticmethod
    def createDefaultConfig(fileName, version):
        print("MainConfig - Refresh or create from default Config")

        MainConfig.settings["cfgFile"] = fileName
        MainConfig.settings["version"] = version
        MainConfig.settings["inDir"] = './Data'
        MainConfig.settings["outDir"] = './Data'
        MainConfig.settings["ancFileDir"] = './Data/Sample_Data'
        MainConfig.settings["metFile"] = ""
        MainConfig.settings["popQuery"] = 0