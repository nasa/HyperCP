
import csv
import os
import numpy as np
import datetime
import time

from SeaBASSWriter import SeaBASSWriter
from CalibrationFileReader import CalibrationFileReader
from HDFRoot import HDFRoot
from MainConfig import MainConfig
from ConfigFile import ConfigFile
from Utilities import Utilities
from AncillaryReader import AncillaryReader

from ProcessL1a import ProcessL1a
from ProcessL1b import ProcessL1b
from ProcessL1c import ProcessL1c
from ProcessL1d import ProcessL1d
from ProcessL1e import ProcessL1e
from ProcessL2 import ProcessL2



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
            elif cf.id.startswith("SATPYR"):
                cf.instrumentType = "SATPYR"
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
    def processAncData(fp):
        if fp is None:
            return None
        elif not os.path.isfile(fp):
            print("Specified ancillary file not found: " + fp)
            return None
        ancillaryData = AncillaryReader.readAncillary(fp)
        return ancillaryData

    @staticmethod
    def processL1a(inFilePath, outFilePath, calibrationMap):      
        if not os.path.isfile(inFilePath):
            msg = 'No such file...'
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Process the data
        msg = "ProcessL1a"
        print(msg)
        Utilities.writeLogFile(msg)
        root = ProcessL1a.processL1a(inFilePath, outFilePath, calibrationMap)

        # Apply SZA filter 
        if root is not None:
            for gp in root.groups:                              
                # try:
                if 'FrameTag' in gp.attributes:
                    if gp.attributes["FrameTag"].startswith("SATNAV"):
                        elevData = gp.getDataset("ELEVATION")
                        elevation = elevData.data.tolist()
                        szaLimit = float(ConfigFile.settings["fL1aCleanSZAMax"])

                        ''' It would be good to add local time as a printed output with SZA'''
                        if (90-np.nanmax(elevation)) > szaLimit:
                            msg = f'SZA too low. Discarding file. {round(90-np.nanmax(elevation))}'
                            print(msg)
                            Utilities.writeLogFile(msg)
                            return None
                        else:
                            msg = f'SZA passed filter: {round(90-np.nanmax(elevation))}'
                            print(msg)
                            Utilities.writeLogFile(msg)
                else:
                    print(f'No FrameTag in {gp.id} group')
                # except:
                #     msg = f'FrameTag does not exist in the group {gp.id}.'
                #     print(msg)
                #     Utilities.writeLogFile(msg)
                #     return None
        
        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:                
                msg = 'Unable to write L1A file. It may be open in another program.'
                Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return None
        else:
            msg = "L1a processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

    @staticmethod
    def processL1b(inFilePath, outFilePath, calibrationMap):      
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        print("ProcessL1b")
        try:
            root = HDFRoot.readHDF5(inFilePath)
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        root = ProcessL1b.processL1b(root, calibrationMap)

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                msg = "Unable to write the file. May be open in another application."
                Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return None
        else:
            msg = "L1b processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

    @staticmethod
    def processL1c(inFilePath, outFilePath, ancillaryData=None):

        _,fileName = os.path.split(outFilePath)
        
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        msg = ("ProcessL1c: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg,'w')
        try:
            root = HDFRoot.readHDF5(inFilePath)
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        root = ProcessL1c.processL1c(root, fileName, ancillaryData)     

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                msg = "Unable to write file. May be open in another application."
                Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return None
        else:
            msg = "L1c processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

    @staticmethod
    def processL1d(inFilePath, outFilePath):        
        
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        msg = ("ProcessL1d: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg,'w')
        try:
            root = HDFRoot.readHDF5(inFilePath)
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        root = ProcessL1d.processL1d(root)     

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                msg = "Unable to write file. May be open in another application."
                Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return None
        else:
            msg = "L1d processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None            

    @staticmethod
    def processL1e(inFilePath, outFilePath):
        _,fileName = os.path.split(outFilePath)

        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        print("ProcessL1e")
        try:
            root = HDFRoot.readHDF5(inFilePath)
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        root = ProcessL1e.processL1e(root, fileName)

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                msg = "Unable to write file. May be open in another application."
                Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return None
        else:
            msg = "L1e processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None  


    @staticmethod
    def processL2(inFilePath, outFilePath, ancillaryData):
        
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        msg = ("ProcessL2: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg,'w')
        try:
            root = HDFRoot.readHDF5(inFilePath)
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        
        root.attributes['In_Filepath'] = inFilePath
        root = ProcessL2.processL2(root, ancillaryData)

        # Create Plots
        dirpath = os.getcwd()
        if root is not None and ConfigFile.settings['bL2PlotRrs']==1:            
            _, filename = os.path.split(outFilePath)
            Utilities.plotRadiometry(root, dirpath, filename, rType='Rrs', plotDelta = True)
        if root is not None and ConfigFile.settings['bL2PlotnLw']==1:            
            _, filename = os.path.split(outFilePath)
            Utilities.plotRadiometry(root, dirpath, filename, rType='nLw', plotDelta = True)            
        if root is not None and ConfigFile.settings['bL2PlotEs']==1:
            _, filename = os.path.split(outFilePath)
            Utilities.plotRadiometry(root, dirpath, filename, rType='ES', plotDelta = True)
        if root is not None and ConfigFile.settings['bL2PlotLi']==1:
            _, filename = os.path.split(outFilePath)
            Utilities.plotRadiometry(root, dirpath, filename, rType='LI', plotDelta = True)
        if root is not None and ConfigFile.settings['bL2PlotLt']==1:
            _, filename = os.path.split(outFilePath)
            Utilities.plotRadiometry(root, dirpath, filename, rType='LT', plotDelta = True)

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
            except:
                msg = "Unable to write file. May be open in another application."
                Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return None
        else:
            msg = "L2 processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

    # Process every file in a list of files 1 level
    @staticmethod
    def processSingleLevel(pathOut, inFilePath, calibrationMap, level, ancFile=None):
        # Find the absolute path to the output directory
        pathOut = os.path.abspath(pathOut)
        # inFilePath is a singleton file complete with path
        inFilePath = os.path.abspath(inFilePath)        
        # (inpath, inFileName) = os.path.split(inFilePath)        
        inFileName = os.path.split(inFilePath)[1]        
        # Split off the . suffix (retains the LXx for L1a and above)
        fileName = os.path.splitext(inFileName)[0]   

        # Initialize the Utility logger, overwriting it if necessary
        os.environ["LOGFILE"] = (fileName + '_' + level + '.log')
        msg = "Process Single Level"
        Utilities.writeLogFile(msg,mode='w')

        if level == "L1A" or \
            level == "L1B" or \
            level == "L1C" or \
            level == "L1D":       

            if os.path.isdir(pathOut):
                pathOut = os.path.join(pathOut,level)
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                msg = "Bad output destination. Select new Output Data Directory."
                print(msg)
                Utilities.writeLogFile(msg)
                return False
            
            if level == "L1A":               
                outFilePath = os.path.join(pathOut,fileName + "_" + level + ".hdf")
            else:
                # split the level suffix off the infile to make the outfilename
                fileName = fileName.split('_')
                outFilePath = os.path.join(pathOut,fileName[0] + "_" + level + ".hdf")                
            
            if level == "L1A":
                Controller.processL1a(inFilePath, outFilePath, calibrationMap) 
            elif level == "L1B":
                Controller.processL1b(inFilePath, outFilePath, calibrationMap) 
            elif level == "L1C":
                if ConfigFile.settings["bL1cSolarTracker"] == 0:
                    ancillaryData = Controller.processAncData(ancFile)
                else:
                    ancillaryData = None
                Controller.processL1c(inFilePath, outFilePath, ancillaryData)
            elif level == "L1D":
                Controller.processL1d(inFilePath, outFilePath) 

            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60: # If the file exists and was created in the last minute...
                    msg = f'{level} file produced: {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)  
                    return True                                        

        elif level == "L1E":
            if os.path.isdir(pathOut):
                pathOut = os.path.join(pathOut,level)
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                msg = "Bad output destination. Select new Output Data Directory."
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_" + level + ".hdf")
            Controller.processL1e(inFilePath, outFilePath)   
            
            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60:
                    msg = f'{level} file produced: {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    
                    if int(ConfigFile.settings["bL1eSaveSeaBASS"]) == 1:
                        msg = f'Output SeaBASS for HDF: {outFilePath}'
                        print(msg)
                        Utilities.writeLogFile(msg)
                        SeaBASSWriter.outputTXT_Type1e(outFilePath)                      
                    return True

        elif level == "L2":          
            if os.path.isdir(pathOut):
                pathOut = os.path.join(pathOut,level)
                if os.path.isdir(pathOut) is False:
                    os.mkdir(pathOut)
            else:
                msg = "Bad output destination. Select new Output Data Directory."
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            ancillaryData = Controller.processAncData(ancFile)
            fileName = fileName.split('_')
            outFilePath = os.path.join(pathOut,fileName[0] + "_" + level + ".hdf")
            Controller.processL2(inFilePath, outFilePath, ancillaryData)  
            
            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60: 
                    msg = f'{level} file produced: {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)

                    if int(ConfigFile.settings["bL2SaveSeaBASS"]) == 1:
                        msg = f'Output SeaBASS for HDF: {outFilePath}'
                        print(msg)
                        Utilities.writeLogFile(msg)
                        SeaBASSWriter.outputTXT_Type2(outFilePath)
                    return True

        msg = f'Process Single Level: {outFilePath} - DONE'
        print(msg)
        Utilities.writeLogFile(msg)


    # Process every file in a list of files from L0 to L2
    @staticmethod
    def processFilesMultiLevel(pathOut,inFiles, calibrationMap, ancFile=None):
        print("processFilesMultiLevel")
        t0 = time.time()
        for fp in inFiles:
            print("Processing: " + fp)
            # Controller.processMultiLevel(pathout, fp, calibrationMap, ancFile)
            if Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L1A', ancFile):
                # Going from L0 to L1A, need to account for the underscore
                inFileName = os.path.split(fp)[1]
                fileName = f'L1A/{os.path.splitext(inFileName)[0]}_L1A.hdf'
                fp = os.path.join(os.path.abspath(pathOut),fileName)
                if Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L1B', ancFile):
                    inFileName = os.path.split(fp)[1]
                    fileName = f'L1B/{os.path.splitext(inFileName)[0].split("_")[0]}_L1B.hdf'
                    fp = os.path.join(os.path.abspath(pathOut),fileName)
                    if Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L1C', ancFile):
                        inFileName = os.path.split(fp)[1]
                        fileName = f'L1C/{os.path.splitext(inFileName)[0].split("_")[0]}_L1C.hdf'
                        fp = os.path.join(os.path.abspath(pathOut),fileName)
                        if Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L1D', ancFile):
                            inFileName = os.path.split(fp)[1]
                            fileName = f'L1D/{os.path.splitext(inFileName)[0].split("_")[0]}_L1D.hdf'
                            fp = os.path.join(os.path.abspath(pathOut),fileName)
                            if Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L1E', ancFile):
                                inFileName = os.path.split(fp)[1]
                                fileName = f'L1E/{os.path.splitext(inFileName)[0].split("_")[0]}_L1E.hdf'
                                fp = os.path.join(os.path.abspath(pathOut),fileName)
                                Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L2', ancFile) 
        print("processFilesMultiLevel - DONE")
        t1 = time.time()
        print(f'Elapsed time: {(t1-t0)/60} minutes')


    # Process every file in a list of files 1 level
    @staticmethod
    def processFilesSingleLevel(pathOut, inFiles, calibrationMap, level, ancFile=None):
        # print("processFilesSingleLevel")
        for fp in inFiles:            
            # Check that the input file matches what is expected for this processing level
            # Not case sensitive
            fileName = str.lower(os.path.split(fp)[1])
            if level == "L1A":
                srchStr = 'RAW'
            elif level == 'L1B':
                srchStr = 'L1A'
            elif level == 'L1C':
                srchStr = 'L1B'
            elif level == 'L1D':
                srchStr = 'L1C'
            elif level == 'L1E':
                srchStr = 'L1D'
            elif level == 'L2':
                srchStr = 'L1E'
            if fileName.find(str.lower(srchStr)) == -1:
                msg = f'{fileName} does not match expected input level for outputing {level}'
                print(msg)
                Utilities.writeLogFile(msg)
                return -1

            print("Processing: " + fp)
            # try:
            Controller.processSingleLevel(pathOut, fp, calibrationMap, level, ancFile)
            # except OSError:
            #     print("Unable to process that file due to an operating system error. Try again.")
        print("processFilesSingleLevel - DONE")
    