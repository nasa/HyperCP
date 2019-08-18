
import csv
import os
import numpy as np
import datetime

from SeaBASSWriter import SeaBASSWriter
from CalibrationFileReader import CalibrationFileReader
from HDFRoot import HDFRoot
from ConfigFile import ConfigFile
from Utilities import Utilities
from WindSpeedReader import WindSpeedReader

from ProcessL1a import ProcessL1a
from ProcessL1b import ProcessL1b
from ProcessL2 import ProcessL2
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
            print("Specified wind file not found: " + fp)
            return None
        windSpeedData = WindSpeedReader.readWindSpeed(fp)
        return windSpeedData

    @staticmethod
    def processL1a(inFilePath, outFilePath, calibrationMap):      
        if not os.path.isfile(inFilePath):
            print("No such file...")
            return None

        # Process the data
        msg = "ProcessL1a"
        print(msg)
        Utilities.writeLogFile(msg)
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
                            msg = f'SZA too low. Discarding file. {round(90-np.nanmax(elevation))}'
                            print(msg)
                            Utilities.writeLogFile(msg)
                            return None
                        else:
                            msg = f'SZA passed filter: {round(90-np.nanmax(elevation))}'
                            print(msg)
                            Utilities.writeLogFile(msg)
                            
                except:
                    msg = f'FrameTag does not exist in the group {gp.id}. Aborting.'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return None
        
        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                msg = 'Unable to write L1A file. It may be open in another program.'
                print(msg)
                Utilities.writeLogFile(msg)
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

    @staticmethod
    def processL3(inFilePath, outFilePath):

        _,fileName = os.path.split(outFilePath)
        
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        msg = ("ProcessL3: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg,'w')
        root = HDFRoot.readHDF5(inFilePath)
        root = ProcessL3.processL3(root, fileName)     

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
        try:
            root = HDFRoot.readHDF5(inFilePath)
        except:
            print('Unable to read L3 file. It may be open in another program.')
            return None
        
        root.attributes['In_Filepath'] = inFilePath
        root = ProcessL4.processL4(root, windSpeedData)

        # Create Plots
        dirpath = './'
        if root is not None and ConfigFile.settings['bL4PlotRrs']==1:            
            _, filename = os.path.split(outFilePath)
            Utilities.plotRadiometry(root, dirpath, filename, rType='Rrs')
        if root is not None and ConfigFile.settings['bL4PlotEs']==1:
            _, filename = os.path.split(outFilePath)
            Utilities.plotRadiometry(root, dirpath, filename, rType='ES')
        if root is not None and ConfigFile.settings['bL4PlotLi']==1:
            _, filename = os.path.split(outFilePath)
            Utilities.plotRadiometry(root, dirpath, filename, rType='LI')
        if root is not None and ConfigFile.settings['bL4PlotLt']==1:
            _, filename = os.path.split(outFilePath)
            Utilities.plotRadiometry(root, dirpath, filename, rType='LT')

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


    @staticmethod
    def processSingleLevel(pathOut, inFilePath, calibrationMap, level, windFile=None):
        # Find the absolute path to the output directory
        pathOut = os.path.abspath(pathOut)
        # inFilePath is a singleton file complete with path
        inFilePath = os.path.abspath(inFilePath)        
        # (inpath, inFileName) = os.path.split(inFilePath)        
        inFileName = os.path.split(inFilePath)[1]        
        # Split off the . suffix (retains the LXx for L1a and above)
        fileName = os.path.splitext(inFileName)[0]   

        # Initialize the Utility logger, overwriting it if necessary
        os.environ["LOGFILE"] = (fileName + '_L' + level + '.log')
        msg = "Process Single Level"
        Utilities.writeLogFile(msg,mode='w')

        if level == "1a":            
            if os.path.isdir(pathOut):
                pathOut = os.path.join(pathOut,'L1A')
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                msg = "Bad output destination. Select new Output Data Directory."
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            outFilePath = os.path.join(pathOut,fileName + "_L1a.hdf")
            Controller.processL1a(inFilePath, outFilePath, calibrationMap) 
            
            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60: # If the file exists and was created in the last minute...
                    msg = f'L1a file produced: {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)  
                    return True                                 

        elif level == "1b":
            if os.path.isdir(pathOut):
                pathOut = os.path.join(pathOut,'L1B')
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                msg = "Bad output destination. Select new Output Data Directory."
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_L1b.hdf")
            Controller.processL1b(inFilePath, outFilePath, calibrationMap)   
            
            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60:
                    msg = f'L1b file produced: {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return True

        elif level == "2":
            if os.path.isdir(pathOut):
                pathOut = os.path.join(pathOut,'L2')
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                msg = "Bad output destination. Select new Output Data Directory."
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_L2.hdf")
            Controller.processL2(inFilePath, outFilePath) 

            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60:
                    msg = f'L2 file produced: {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return True

        elif level == "3":
            if os.path.isdir(pathOut):
                pathOut = os.path.join(pathOut,'L3')
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                msg = "Bad output destination. Select new Output Data Directory."
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_L3.hdf")
            Controller.processL3(inFilePath, outFilePath)   
            
            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60:
                    msg = f'L3 file produced: {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    
                    if int(ConfigFile.settings["bL3SaveSeaBASS"]) == 1:
                        msg = f'Output SeaBASS for HDF: {outFilePath}'
                        print(msg)
                        Utilities.writeLogFile(msg)

                        SeaBASSWriter.outputTXT_L3(outFilePath)  
                    
                    return True

        elif level == "4":          
            if os.path.isdir(pathOut):
                pathOut = os.path.join(pathOut,'L4')
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                msg = "Bad output destination. Select new Output Data Directory."
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            windSpeedData = Controller.processWindData(windFile)
            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_L4.hdf")
            Controller.processL4(inFilePath, outFilePath, windSpeedData)  
            
            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60: 
                    msg = f'L4 file produced: {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)

                    if int(ConfigFile.settings["bL4SaveSeaBASS"]) == 1:
                        msg = f'Output SeaBASS for HDF: {outFilePath}'
                        print(msg)
                        Utilities.writeLogFile(msg)

                        SeaBASSWriter.outputTXT_L4(outFilePath)

                    return True

        msg = f'Process Single Level: {outFilePath} - DONE'
        print(msg)
        Utilities.writeLogFile(msg)


    # @staticmethod
    # def processMultiLevel(outFilePath, inFilePath, calibrationMap, windFile=None):
    #     print("Process Multi Level: ")
               
    #     print("Process Multi Level: " + outFilePath + " - DONE")

    # Used to process every file in a list of files
    @staticmethod
    def processFilesMultiLevel(pathOut,inFiles, calibrationMap, windFile=None):
        print("processFilesMultiLevel")
        for fp in inFiles:
            print("Processing: " + fp)
            # Controller.processMultiLevel(pathout, fp, calibrationMap, windFile)
            if Controller.processSingleLevel(pathOut, fp, calibrationMap, '1a', windFile):
                # Going from L0 to L1A, need to account for the underscore
                inFileName = os.path.split(fp)[1]
                fileName = f'L1A/{os.path.splitext(inFileName)[0]}_L1a.hdf'
                fp = os.path.join(os.path.abspath(pathOut),fileName)
                if Controller.processSingleLevel(pathOut, fp, calibrationMap, '1b', windFile):
                    inFileName = os.path.split(fp)[1]
                    fileName = f'L1B/{os.path.splitext(inFileName)[0].split("_")[0]}_L1b.hdf'
                    fp = os.path.join(os.path.abspath(pathOut),fileName)
                    if Controller.processSingleLevel(pathOut, fp, calibrationMap, '2', windFile):
                        inFileName = os.path.split(fp)[1]
                        fileName = f'L2/{os.path.splitext(inFileName)[0].split("_")[0]}_L2.hdf'
                        fp = os.path.join(os.path.abspath(pathOut),fileName)
                        if Controller.processSingleLevel(pathOut, fp, calibrationMap, '3', windFile):
                            inFileName = os.path.split(fp)[1]
                            fileName = f'L3/{os.path.splitext(inFileName)[0].split("_")[0]}_L3.hdf'
                            fp = os.path.join(os.path.abspath(pathOut),fileName)
                            Controller.processSingleLevel(pathOut, fp, calibrationMap, '4', windFile) 
        print("processFilesMultiLevel - DONE")


    # Used to process every file in a list of files
    @staticmethod
    def processFilesSingleLevel(pathOut, inFiles, calibrationMap, level, windFile=None):
        # print("processFilesSingleLevel")
        for fp in inFiles:            
            print("Processing: " + fp)
            # try:
            Controller.processSingleLevel(pathOut, fp, calibrationMap, level, windFile)
            # except OSError:
            #     print("Unable to process that file due to an operating system error. Try again.")
        print("processFilesSingleLevel - DONE")

    """ 
    @staticmethod
    def processDirectoryTest(path, calibrationMap, level=4):
        for (dirpath, dirnames, filenames) in os.walk(path):
            for name in sorted(filenames):
                #print("infile:", name)
                if os.path.splitext(name)[1].lower() == ".raw":
                    Controller.processAll(os.path.join(dirpath, name), calibrationMap)
                    #Controller.processMultiLevel(os.path.join(dirpath, name), calibrationMap, level)
            break
        
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
    # @staticmethod
    # def outputSeaBASS(fp, root, gpName, dsName):
    #     (dirpath, filename) = os.path.split(fp)
    #     filename = os.path.splitext(filename)[0]

    #     gp = root.getGroup(gpName)
    #     ds = gp.getDataset(dsName)
    #     #np.savetxt('Data/test.out', ds.data)

    #     if not ds:
    #         print("Warning - outputSeaBASS: missing dataset")
    #         return

    #     #dirpath = "csv"
    #     #name = filename[28:43]
    #     dirpath = os.path.join(dirpath, 'csv')
    #     name = filename[0:15]

    #     outList = []
    #     columnName = dsName.lower()
        
    #     names = list(ds.data.dtype.names)
    #     names.remove("Datetag")
    #     names.remove("Timetag2")
    #     names.remove("Latpos")
    #     names.remove("Lonpos")
    #     data = ds.data[names]

    #     total = ds.data.shape[0]
    #     #ls = ["wl"] + [k for k,v in sorted(ds.data.dtype.fields.items(), key=lambda k: k[1])]
    #     ls = ["wl"] + list(data.dtype.names)
    #     outList.append(ls)
    #     for i in range(total):
    #         n = str(i+1)
    #         ls = [columnName + "_" + name + '_' + n] + ['%f' % num for num in data[i]]
    #         outList.append(ls)

    #     outList = zip(*outList)

    #     filename = dsName.upper() + "_" + name
    #     #filename = name + "_" + dsName.upper()
    #     csvPath = os.path.join(dirpath, filename + ".csv")

    #     with open(csvPath, 'w') as f:
    #         writer = csv.writer(f)
    #         writer.writerows(outList)
    """
    