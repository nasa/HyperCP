
import csv
import os
import numpy as np
# import logging

from SeaBASSWriter import SeaBASSWriter
from CalibrationFileReader import CalibrationFileReader
from HDFRoot import HDFRoot
from ConfigFile import ConfigFile
from Utilities import Utilities
from WindSpeedReader import WindSpeedReader
from ProcessL0 import ProcessL0
from ProcessL1a import ProcessL1a
from ProcessL1b import ProcessL1b
from ProcessL2 import ProcessL2
# from ProcessL2s import ProcessL2s
from ProcessL3 import ProcessL3
from ProcessL4 import ProcessL4
# from ProcessL4a import ProcessL4a



class Controller:

    @staticmethod
    def generateContext(calibrationMap):
        for key in calibrationMap:
            cf = calibrationMap[key]
            cf.printd()
            if cf.id.startswith("SATHED"):
                cf.instrumentType = "Reference"
                cf.media = "Air"
                cf.measMode = "Surface"
                cf.frameType = "ShutterDark"
                cf.sensorType = cf.getSensorType()
            elif cf.id.startswith("SATHSE"):
                cf.instrumentType = "Reference"
                cf.media = "Air"
                cf.measMode = "Surface"
                cf.frameType = "ShutterLight"
                cf.sensorType = cf.getSensorType()
            elif cf.id.startswith("SATHLD"):
                cf.instrumentType = "SAS"
                cf.media = "Air"
                cf.measMode = "VesselBorne"
                cf.frameType = "ShutterDark"
                cf.sensorType = cf.getSensorType()
            elif cf.id.startswith("SATHSL"):
                cf.instrumentType = "SAS"
                cf.media = "Air"
                cf.measMode = "VesselBorne"
                cf.frameType = "ShutterLight"
                cf.sensorType = cf.getSensorType()
            elif cf.id.startswith("$GPRMC"):
                cf.instrumentType = "GPS"
                cf.media = "Not Required"
                cf.measMode = "Not Required"
                cf.frameType = "Not Required"
                cf.sensorType = cf.getSensorType()
            else:
                cf.instrumentType = "SAS"
                cf.media = "Air"
                cf.measMode = "VesselBorne"
                cf.frameType = "LightAncCombined"
                cf.sensorType = cf.getSensorType()


    # @staticmethod
    # def processCalibration(calPath):
    #     print("processCalibration")
    #     print("ReadCalibrationFile ", calPath)
    #     calibrationMap = CalibrationFileReader.read(calPath)
    #     #calibrationMap = CalibrationFileReader.readSip("cal2013.sip")
    #     print("calibrationMap:", list(calibrationMap.keys()))
    #     Controller.generateContext(calibrationMap)
    #     print("processCalibration - DONE")
    #     return calibrationMap

    @staticmethod
    def processCalibrationConfig(configName, calFiles):
        # print("processCalibrationConfig")
        calFolder = os.path.splitext(configName)[0] + "_Calibration"
        calPath = os.path.join("Config", calFolder)
        print("Read CalibrationFile ", calPath)
        calibrationMap = CalibrationFileReader.read(calPath)       
        Controller.generateContext(calibrationMap)

        # Settings from Config file
        print("Apply ConfigFile settings")
        print("calibrationMap keys:", calibrationMap.keys())
        # print("config keys:", calFiles.keys())
        
        for key in list(calibrationMap.keys()):
            # print(key)
            if key in calFiles.keys():
                if calFiles[key]["enabled"]:
                    calibrationMap[key].frameType = calFiles[key]["frameType"]
                else:
                    del calibrationMap[key]
            else:
                del calibrationMap[key]
        # print("calibrationMap keys 2:", calibrationMap.keys())
        # print("processCalibrationConfig - DONE")
        return calibrationMap

    # Read wind speed file
    @staticmethod
    def processWindData(fp):
        if fp is None:
            return None
        elif not os.path.isfile(fp):
            print("Specified wind file not found.")
            return None
        windSpeedData = WindSpeedReader.readWindSpeed(fp)
        return windSpeedData

    @staticmethod
    def processL1a(inFilePath, outFilePath, calibrationMap):      
        if not os.path.isfile(inFilePath):
            print("No such file...")
            return None

        # Process the data
        print("ProcessL1a")
        root = ProcessL1a.processL1a(inFilePath, outFilePath, calibrationMap)

        # Apply SZA filter 
        if root is not None:

            for gp in root.groups:                              
                try:
                    if gp.attributes["FrameTag"].startswith("SATNAV"):
                        elevData = gp.getDataset("ELEVATION")
                        elevation = elevData.data.tolist()
                        szaLimit = float(ConfigFile.settings["fL1aCleanSZAMax"])

                        # It would be good to add local time as a printed output with SZA, but considering ###
                        # timezones and probable GMT input, it could be overly complex ###
                        if (90-np.nanmax(elevation)) > szaLimit:
                            print('SZA too low. Discarding file. ' + str(round(90-np.nanmax(elevation))))
                            return None
                        else:
                            print('SZA passed filter: ' + str(round(90-np.nanmax(elevation))))
                            # Write output file to HDF
                except:
                    print('FrameTag does not exist in the group ' + gp.id + '. Aborting.')
                    return None
        
        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                print('Unable to write L1A file. It may be open in another program.')
        else:
            msg = "L1a processing failed. Nothing to output."
            print(msg)
            Utilities.writeLogFile(msg)

    @staticmethod
    def processL1b(inFilePath, outFilePath, calibrationMap):      
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        print("ProcessL1b")
        root = HDFRoot.readHDF5(inFilePath)
        root = ProcessL1b.processL1b(root, calibrationMap)

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                print('Unable to write L1b file. It may be open in another program.')
        else:
            msg = "L1b processing failed. Nothing to output."
            print(msg)
            Utilities.writeLogFile(msg)


    @staticmethod
    def processL2(inFilePath, outFilePath):
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        print("ProcessL2")
        root = HDFRoot.readHDF5(inFilePath)
        root = ProcessL2.processL2(root)

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                print('Unable to write L2 file. It may be open in another program.')
        else:
            msg = "L2 processing failed. Nothing to output."
            print(msg)
            Utilities.writeLogFile(msg)

    # @staticmethod
    # def processL2s(inFilePath, outFilePath):        

    #     if not os.path.isfile(inFilePath):
    #         print('No such input file: ' + inFilePath)
    #         return None
        
    #     # Process the data
    #     msg = ("ProcessL2s: " + inFilePath)
    #     print(msg)    
    #     Utilities.writeLogFile(msg,'w')
        
    #     root = HDFRoot.readHDF5(inFilePath)
    #     root = ProcessL2s.processL2s(root) 

    #     # Write output file
    #     if root is not None:
    #         root.writeHDF5(outFilePath)
    #     else:
    #         msg = "L2 processing failed. Nothing to output."
    #         print(msg)
    #         Utilities.writeLogFile(msg)

    @staticmethod
    def processL3(inFilePath, outFilePath):
        
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        msg = ("ProcessL3: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg,'w')
        root = HDFRoot.readHDF5(inFilePath)
        root = ProcessL3.processL3(root)     

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                print('Unable to write L3 file. It may be open in another program.')
        else:
            msg = "L3 processing failed. Nothing to output."
            print(msg)
            Utilities.writeLogFile(msg)

    @staticmethod
    def processL4(inFilePath, outFilePath, windSpeedData):
        
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        msg = ("ProcessL4: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg,'w')
        root = HDFRoot.readHDF5(inFilePath)
        enableQualityFlags = int(ConfigFile.settings["bL4EnableQualityFlags"])
        root = ProcessL4.processL4(root, enableQualityFlags, windSpeedData)


    #     # Write to separate file if quality flags are enabled
    #     enableQualityFlags = int(ConfigFile.settings["bL4EnableQualityFlags"])
    #     if enableQualityFlags:
    #         root = HDFRoot.readHDF5(filepath)
    #         root = ProcessL4.processL4(root, True, windSpeedData)
    #         root = ProcessL4a.processL4a(root)
    #         if root is not None:
    #             Utilities.plotReflectance(root, dirpath, filename + "-flags")
    #             root.writeHDF5(os.path.join(dirpath, filename + "_L4-flags.hdf"))

    # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                print('Unable to write L4 file. It may be open in another program.')
        else:
            msg = "L4 processing failed. Nothing to output."
            print(msg)
            Utilities.writeLogFile(msg)



    # # Saving data to a formatted csv file for testing
    # @staticmethod
    # def outputCSV_L4(fp):
    #     (dirpath, filename) = os.path.split(fp)
    #     filename = os.path.splitext(filename)[0]

    #     filepath = os.path.join(dirpath, filename + "_L4.hdf")
    #     if not os.path.isfile(filepath):
    #         return

    #     root = HDFRoot.readHDF5(filepath)
    #     if root is None:
    #         print("outputCSV: root is None")
    #         return

    #     Controller.outputCSV(fp, root, "Reflectance", "ES")
    #     Controller.outputCSV(fp, root, "Reflectance", "LI")
    #     Controller.outputCSV(fp, root, "Reflectance", "LT")
    #     Controller.outputCSV(fp, root, "Reflectance", "Rrs")


    @staticmethod
    def outputSeaBASS(fp, root, gpName, dsName):
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]

        gp = root.getGroup(gpName)
        ds = gp.getDataset(dsName)
        #np.savetxt('Data/test.out', ds.data)

        if not ds:
            print("Warning - outputCSV: missing dataset")
            return

        #dirpath = "csv"
        #name = filename[28:43]
        dirpath = os.path.join(dirpath, 'csv')
        name = filename[0:15]

        outList = []
        columnName = dsName.lower()
        
        names = list(ds.data.dtype.names)
        names.remove("Datetag")
        names.remove("Timetag2")
        names.remove("Latpos")
        names.remove("Lonpos")
        data = ds.data[names]

        total = ds.data.shape[0]
        #ls = ["wl"] + [k for k,v in sorted(ds.data.dtype.fields.items(), key=lambda k: k[1])]
        ls = ["wl"] + list(data.dtype.names)
        outList.append(ls)
        for i in range(total):
            n = str(i+1)
            ls = [columnName + "_" + name + '_' + n] + ['%f' % num for num in data[i]]
            outList.append(ls)

        outList = zip(*outList)

        filename = dsName.upper() + "_" + name
        #filename = name + "_" + dsName.upper()
        csvPath = os.path.join(dirpath, filename + ".csv")

        with open(csvPath, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(outList)


    @staticmethod
    def processSingleLevel(pathOut, inFilePath, calibrationMap, level, windFile=None):
        pathOut = os.path.abspath(pathOut)
        # inFilePath is a singleton file complete with path
        inFilePath = os.path.abspath(inFilePath)        
        # (inpath, inFileName) = os.path.split(inFilePath)        
        inFileName = os.path.split(inFilePath)[1]        
        # Split off the .RAW suffix
        fileName = os.path.splitext(inFileName)[0]   

        # Initialize the Utility logger
        os.environ["LOGFILE"] = (fileName + '_L' + level + '.log')

        if level == "1a":            
            if os.path.isdir(pathOut):
                pathOut = pathOut + "/L1A"
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                print("Bad output destination. Select new Output Data Directory.")

            outFilePath = os.path.join(pathOut,fileName + "_L1a.hdf")
            Controller.processL1a(inFilePath, outFilePath, calibrationMap) 
            
            if os.path.isfile(outFilePath):
                print("L1a file produced: " + outFilePath)                                   

        elif level == "1b":
            if os.path.isdir(pathOut):
                pathOut = pathOut + "/L1B"
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                print("Bad output destination. Select new Output Data Directory.")

            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_L1b.hdf")
            Controller.processL1b(inFilePath, outFilePath, calibrationMap)   
            
            if os.path.isfile(outFilePath):
                print("L1b file produced: " + outFilePath) 

        elif level == "2":
            if os.path.isdir(pathOut):
                pathOut = pathOut + "/L2"
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                print("Bad output destination. Select new Output Data Directory.")

            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_L2.hdf")
            Controller.processL2(inFilePath, outFilePath) 
            if os.path.isfile(outFilePath):
                print("L2 file produced: " + outFilePath)   

        elif level == "3":
            if os.path.isdir(pathOut):
                pathOut = pathOut + "/L3"
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                print("Bad output destination. Select new Output Data Directory.")

            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_L3.hdf")
            Controller.processL3(inFilePath, outFilePath)   
            if os.path.isfile(outFilePath):
                msg = ("L3 file produced: " + outFilePath)  
                print(msg)
                Utilities.writeLogFile(msg)
                 
            if int(ConfigFile.settings["bL3SaveSeaBASS"]) == 1:
                print("Output SeaBASS for HDF: " + outFilePath)
                SeaBASSWriter.outputTXT_L3(outFilePath)  

        elif level == "4":          
            if os.path.isdir(pathOut):
                pathOut = pathOut + "/L4"
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                print("Bad output destination. Select new Output Data Directory.")  

            windSpeedData = Controller.processWindData(windFile)
            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_L4.hdf")
            Controller.processL4(inFilePath, outFilePath, windSpeedData)  
            if os.path.isfile(outFilePath):
                msg = ("L4 file produced: " + outFilePath)  
                print(msg)
                Utilities.writeLogFile(msg)

            if int(ConfigFile.settings["bL4SaveSeaBASS"]) == 1:
                print("Output SeaBASS: " + inFilePath)
                SeaBASSWriter.outputTXT_L4(inFilePath)                               
        print("Process Single Level: " + inFilePath + " - DONE")


    # @staticmethod
    # def processMultiLevel(outFilePath, inFilePath, calibrationMap, level=4, windFile=None, skyFile=None):
    #     print("Process Multi Level: " + fp)
    #     Controller.processL1a(inFilePath, outFilePath, calibrationMap)
    #     Controller.processL1b(inFilePath, outFilePath, calibrationMap)                                
    #     Controller.processL2(inFilePath, outFilePath)        
    #     Controller.processL2s(inFilePath, outFilePath)
    #     Controller.processL3(inFilePath, outFilePath)
    #     windSpeedData = Controller.processWindData(windFile)
    #     """ sky file proc goes here"""
    #     Controller.processL4(inFilePath, outFilePath, windSpeedData)
    #     if int(ConfigFile.settings["bL4SaveSeaBASS"]) == 1:
    #             print("Output SeaBASS: " + inFilePath)
    #             SeaBASSWriter.outputTXT_L2s(inFilePath)  
    #     Controller.outputCSV_L4(fp)
    #     print("Output CSV: " + fp)
    #     # SeaBASSWriter.outputTXT_L1a(fp)
    #     # SeaBASSWriter.outputTXT_L1b(fp)
    #     # SeaBASSWriter.outputTXT_L2(fp)
    #     # SeaBASSWriter.outputTXT_L2s(fp)
    #     # SeaBASSWriter.outputTXT_L3(fp)
    #     SeaBASSWriter.outputTXT_L4(fp)
    #     print("Process Multi Level: " + fp + " - DONE")

    """ This may never be called
    @staticmethod
    def processDirectoryTest(path, calibrationMap, level=4):
        for (dirpath, dirnames, filenames) in os.walk(path):
            for name in sorted(filenames):
                #print("infile:", name)
                if os.path.splitext(name)[1].lower() == ".raw":
                    Controller.processAll(os.path.join(dirpath, name), calibrationMap)
                    #Controller.processMultiLevel(os.path.join(dirpath, name), calibrationMap, level)
            break
    """

    #       KEEP FOR LATER
    # # Used to process every file in the specified directory
    # @staticmethod
    # def processDirectory(path, calibrationMap, level=4, windFile=None):
    #     for (dirpath, dirnames, filenames) in os.walk(path):
    #         for name in sorted(filenames):
    #             #print("infile:", name)
    #             if os.path.splitext(name)[1].lower() == ".raw":
    #                 #Controller.processAll(os.path.join(dirpath, name), calibrationMap)
    #                 Controller.processMultiLevel(os.path.join(dirpath, name), calibrationMap, level, windFile)
    #         break

    # # Used to process every file in a list of files
    # @staticmethod
    # def processFilesMultiLevel(pathout,files, calibrationMap, level=4, windFile=None, skyFile=None):
    #     print("processFilesMultiLevel")
    #     for fp in files:
    #         print("Processing: " + fp)
    #         Controller.processMultiLevel(pathout, fp, calibrationMap, level, windFile, skyFile)
    #     print("processFilesMultiLevel - DONE")


    # Used to process every file in a list of files
    @staticmethod
    def processFilesSingleLevel(pathOut, inFiles, calibrationMap, level, windFile=None):
        # print("processFilesSingleLevel")
        for fp in inFiles:
            # fp is now singleton files; run this once per file
            print("Processing: " + fp)
            # try:
            Controller.processSingleLevel(pathOut, fp, calibrationMap, level, windFile)
            # except OSError:
            #     print("Unable to process that file due to an operating system error. Try again.")
        print("processFilesSingleLevel - DONE")

