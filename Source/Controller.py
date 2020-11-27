
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
from PDFreport import PDF


class Controller:
    

    @staticmethod
    def writeReport(title, fileName, pathOut, outFilePath, level):
        print('Writing PDF Report...')
        numLevelDict = {'L1A':1,'L1B':2,'L1C':3,'L1D':4,'L1E':5,'L2':6}
        numLevel = numLevelDict[level]
        
        # Reports
        reportPath = os.path.join(pathOut, 'Reports')
        if os.path.isdir(reportPath) is False:
            os.mkdir(reportPath)
        fileName = fileName[0]
        dirPath = os.getcwd()
        inLogPath = os.path.join(dirPath, 'Logs')
        inPlotPath = os.path.join(pathOut,'Plots')
        # outPDF = os.path.join(reportPath,'Reports', f'{fileName}.pdf')
        outPDF = os.path.join(reportPath, f'{fileName}_{level}.pdf')
        # title = f'File: {fileName} Collected: {root.attributes["TIME-STAMP"]}'

        pdf = PDF()
        pdf.set_title(title)
        pdf.set_author(f'HyperInSPACE_{MainConfig.settings["version"]}')

        inLog = os.path.join(inLogPath,f'{fileName}_L1A.log')
        if os.path.isfile(inLog):
            # pdf.print_chapter(root,'L1A', 'Process RAW to L1A', inLog, inPlotPath, fileName, outFilePath)
            pdf.print_chapter('L1A', 'Process RAW to L1A', inLog, inPlotPath, fileName, outFilePath)

        if numLevel > 1:
            inLog = os.path.join(inLogPath,f'{fileName}_L1A_L1B.log')
            if os.path.isfile(inLog):
                # pdf.print_chapter(root,'L1B', 'Process L1A to L1B', inLog, inPlotPath, fileName, outFilePath)
                pdf.print_chapter('L1B', 'Process L1A to L1B', inLog, inPlotPath, fileName, outFilePath)
        
        if numLevel > 2:
            inLog = os.path.join(inLogPath,f'{fileName}_L1B_L1C.log')
            if os.path.isfile(inLog):
                # pdf.print_chapter(root,'L1C', 'Process L1B to L1C', inLog, inPlotPath, fileName, outFilePath)
                pdf.print_chapter('L1C', 'Process L1B to L1C', inLog, inPlotPath, fileName, outFilePath)
        
        if numLevel > 3:
            inLog = os.path.join(inLogPath,f'{fileName}_L1C_L1D.log')
            if os.path.isfile(inLog):
                # pdf.print_chapter(root,'L1D', 'Process L1C to L1D', inLog, inPlotPath, fileName, outFilePath)
                pdf.print_chapter('L1D', 'Process L1C to L1D', inLog, inPlotPath, fileName, outFilePath)
        
        if numLevel > 4:
            inLog = os.path.join(inLogPath,f'{fileName}_L1D_L1E.log')
            if os.path.isfile(inLog):
                # pdf.print_chapter(root,'L1E', 'Process L1D to L1E', inLog, inPlotPath, fileName, outFilePath)
                pdf.print_chapter('L1E', 'Process L1D to L1E', inLog, inPlotPath, fileName, outFilePath)
        
        if numLevel > 5:
            inLog = os.path.join(inLogPath,f'{fileName}_L1E_L2.log')
            if os.path.isfile(inLog):
                # pdf.print_chapter(root,'L2', 'Process L1E to L2', inLog, inPlotPath, fileName, outFilePath)
                pdf.print_chapter('L2', 'Process L1E to L2', inLog, inPlotPath, fileName, outFilePath)

        try:
            pdf.output(outPDF, 'F')
        except:
            msg = 'Unable to write the PDF file. It may be open in another program.'
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)

    @staticmethod
    def generateContext(calibrationMap):
        ''' Generate a calibration context map for the instrument suite '''

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
            elif cf.id.startswith("$GPRMC") or cf.id.startswith("$GPGGA"):
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
        ''' Reaad in calibration files/configuration '''

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
    
    @staticmethod
    def processAncData(fp):
        ''' Read in the ancillary field data file '''

        if fp is None:
            return None
        elif not os.path.isfile(fp):
            print("Specified ancillary file not found: " + fp)
            return None
        ancillaryData = AncillaryReader.readAncillary(fp)
        return ancillaryData

    @staticmethod
    def processL1a(inFilePath, outFilePath, calibrationMap): 
        root = None     
        if not os.path.isfile(inFilePath):
            msg = 'No such file...'
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, 'Never'

        # Process the data
        msg = "ProcessL1a"
        print(msg)
        root = ProcessL1a.processL1a(inFilePath, calibrationMap)

        # Apply SZA filter 
        if ConfigFile.settings["bL1aCleanSZA"]:
            if root is not None:
                timeStamp = root.attributes['TIME-STAMP'] # a string
                for gp in root.groups:                              
                    # try:
                    if 'FrameTag' in gp.attributes:
                        if gp.attributes["FrameTag"].startswith("SATNAV"):
                            elevData = gp.getDataset("ELEVATION")
                            elevation = elevData.data.tolist()
                            szaLimit = float(ConfigFile.settings["fL1aCleanSZAMax"])

                            ''' It would be good to add local time as a printed output with SZA'''
                            if (90-np.nanmax(elevation)) > szaLimit:
                                msg = f'SZA too low. Discarding entire file. {round(90-np.nanmax(elevation))}'
                                print(msg)
                                Utilities.writeLogFile(msg)
                                return None, timeStamp
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
                return None, timeStamp
        else:
            msg = "L1a processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, 'Unknown'
            
        return root, timeStamp

    @staticmethod
    def processL1b(inFilePath, outFilePath, calibrationMap):    
        root = None  
        timeStamp = 'Unknown'
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None, timeStamp

        # Process the data
        print("ProcessL1b")
        try:
            root = HDFRoot.readHDF5(inFilePath)
            timeStamp = root.attributes['TIME-STAMP'] # a string
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, timeStamp

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
                return None, timeStamp
        else:
            msg = "L1b processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, timeStamp

        return root, timeStamp

    @staticmethod
    def processL1c(inFilePath, outFilePath, ancillaryData=None):
        root = None
        timeStamp = 'Unknown'
        _,fileName = os.path.split(outFilePath)
        
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None, timeStamp

        # Process the data
        msg = ("ProcessL1c: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg,'w')
        try:
            root = HDFRoot.readHDF5(inFilePath)
            timeStamp = root.attributes['TIME-STAMP'] # a string
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, timeStamp

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
                return None, timeStamp
        else:
            msg = "L1c processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, timeStamp
        
        return root, timeStamp

    @staticmethod
    def processL1d(inFilePath, outFilePath):        
        root = None
        timeStamp = 'Unknown'
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None, timeStamp

        # Process the data
        msg = ("ProcessL1d: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg,'w')
        try:
            root = HDFRoot.readHDF5(inFilePath)
            timeStamp = root.attributes['TIME-STAMP'] # a string
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, timeStamp

        root = ProcessL1d.processL1d(root)     

        # Write output file
        if root is not None:
            try:                
                root.writeHDF5(outFilePath)

                # Create Plots
                # Radiometry
                dirpath = os.getcwd()
                _, filename = os.path.split(outFilePath)
                if ConfigFile.settings['bL2PlotEs']==1:
                    Utilities.plotRadiometryL1D(root, dirpath, filename, rType='ES')
                if ConfigFile.settings['bL2PlotLi']==1:
                    Utilities.plotRadiometryL1D(root, dirpath, filename, rType='LI')
                if ConfigFile.settings['bL2PlotLt']==1:
                    Utilities.plotRadiometryL1D(root, dirpath, filename, rType='LT')
            except:
                msg = "Unable to write file. May be open in another application."
                Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return None, timeStamp
        else:
            msg = "L1d processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, timeStamp    

        return root, timeStamp

    @staticmethod
    def processL1e(inFilePath, outFilePath):
        root = None
        timeStamp = 'Unknown'
        _,fileName = os.path.split(outFilePath)

        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None, timeStamp

        # Process the data
        print("ProcessL1e")
        try:
            root = HDFRoot.readHDF5(inFilePath)
            timeStamp = root.attributes['TIME-STAMP'] # a string
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, timeStamp

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
                return None, timeStamp
        else:
            msg = "L1e processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, timeStamp  
        
        return root, timeStamp


    @staticmethod
    def processL2(inFilePath, outFilePath, ancillaryData):
        root = None
        timeStamp = 'Unknown'
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None, outFilePath, timeStamp

        # Process the data
        msg = ("ProcessL2: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg,'w')
        try:
            root = HDFRoot.readHDF5(inFilePath)
            timeStamp = root.attributes['TIME-STAMP'] # a string
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, outFilePath, timeStamp
        
        root.attributes['In_Filepath'] = inFilePath
        root = ProcessL2.processL2(root, ancillaryData)
        

        dirpath = os.getcwd()
        outPath, filename = os.path.split(outFilePath)
        if root is not None:
            if ConfigFile.settings["bL2Stations"]:
                station = np.unique(root.getGroup("ANCILLARY").getDataset("STATION").columns["STATION"]).tolist()
                station = str( round(station[0]*100)/100 )
                filename = f'STATION_{station}_{filename}'
                outFilePath = os.path.join(outPath,filename)

            # Create Plots
            # Radiometry
            if ConfigFile.settings['bL2PlotRrs']==1:                        
                Utilities.plotRadiometry(root, dirpath, filename, rType='Rrs', plotDelta = True)
            if ConfigFile.settings['bL2PlotnLw']==1:            
                Utilities.plotRadiometry(root, dirpath, filename, rType='nLw', plotDelta = True)            
            if ConfigFile.settings['bL2PlotEs']==1:
                Utilities.plotRadiometry(root, dirpath, filename, rType='ES', plotDelta = True)
            if ConfigFile.settings['bL2PlotLi']==1:
                Utilities.plotRadiometry(root, dirpath, filename, rType='LI', plotDelta = True)
            if ConfigFile.settings['bL2PlotLt']==1:
                Utilities.plotRadiometry(root, dirpath, filename, rType='LT', plotDelta = True)

            # IOPs
            if 1==1: # For now, always plot these. Utilities checks to make sure they exist first.
                # These three should plot GOIP and QAA together
                Utilities.plotIOPs(root, dirpath, filename, algorithm = 'qaa', iopType='adg', plotDelta = False)
                Utilities.plotIOPs(root, dirpath, filename, algorithm = 'qaa', iopType='aph', plotDelta = False)
                Utilities.plotIOPs(root, dirpath, filename, algorithm = 'qaa', iopType='bbp', plotDelta = False)

                # This puts ag, Sg, and DOC on the same plot
                Utilities.plotIOPs(root, dirpath, filename, algorithm = 'gocad', iopType='ag', plotDelta = False)

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
                return root, outFilePath, timeStamp
            except:
                msg = "Unable to write file. May be open in another application."
                Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return None, outFilePath, timeStamp
        else:
            msg = "L2 processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, outFilePath, timeStamp

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
        if ConfigFile.settings["bL2Stations"] == 1 and level == 'L2': 
            os.environ["LOGFILE"] = f'Stations_{fileName}_{level}.log'
        else:
            os.environ["LOGFILE"] = (fileName + '_' + level + '.log')
        msg = "Process Single Level"
        Utilities.writeLogFile(msg,mode='w')
        
        fileName = fileName.split('_') # [basefilename, level]

        # Check for base output directory
        if os.path.isdir(pathOut):
            pathOutLevel = os.path.join(pathOut,level)
        else:
            msg = "Bad output destination. Select new Output Data Directory."
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        # Add output level directory if necessary
        if os.path.isdir(pathOutLevel) is False:
            os.mkdir(pathOutLevel)
        
        outFilePath = os.path.join(pathOutLevel,fileName[0] + "_" + level + ".hdf")        
    
        if level == "L1A" or level == "L1B" or \
            level == "L1C" or level == "L1D":                           
            
            if level == "L1A":
                root, timeStamp = Controller.processL1a(inFilePath, outFilePath, calibrationMap)                 
            elif level == "L1B":
                root, timeStamp = Controller.processL1b(inFilePath, outFilePath, calibrationMap) 
            elif level == "L1C":
                if ConfigFile.settings["bL1cSolarTracker"] == 0:
                    ancillaryData = Controller.processAncData(ancFile)
                else:
                    ancillaryData = None
                root, timeStamp = Controller.processL1c(inFilePath, outFilePath, ancillaryData)
            elif level == "L1D":
                root, timeStamp = Controller.processL1d(inFilePath, outFilePath) 

            # Confirm output file creation
            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60: # If the file exists and was created in the last minute...
                    msg = f'{level} file produced: \n {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)                              

        elif level == "L1E":
            root, timeStamp = Controller.processL1e(inFilePath, outFilePath)   
            
            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60:
                    msg = f'{level} file produced: \n{outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    
                    if int(ConfigFile.settings["bL1eSaveSeaBASS"]) == 1:
                        msg = f'Output SeaBASS for HDF: Es, Li, Lt files'
                        print(msg)
                        Utilities.writeLogFile(msg)
                        SeaBASSWriter.outputTXT_Type1e(outFilePath)                      
                    return True

        elif level == "L2":          
            if ConfigFile.settings["bL1cSolarTracker"]:
                ancillaryData = Controller.processAncData(ancFile)
            else:
                # Without the SolarTracker, ancillary data would have been read in at L1C,
                # and will be extracted from the ANCILLARY_NOTRACKER group later
                ancillaryData = None

            root, outFilePath, timeStamp = Controller.processL2(inFilePath, outFilePath, ancillaryData)  
            
            if os.path.isfile(outFilePath):
                # Ensure that the L2 on file is recent before continuing with 
                # SeaBASS files or reports
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60: 
                    msg = f'{level} file produced: \n{outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)

                    # Write SeaBASS
                    if int(ConfigFile.settings["bL2SaveSeaBASS"]) == 1:
                        msg = f'Output SeaBASS for HDF: \n{outFilePath}'
                        print(msg)
                        Utilities.writeLogFile(msg)
                        SeaBASSWriter.outputTXT_Type2(outFilePath)
                    # return True        

        # In case of processing failure, write the report at this Process level
        #   Use numeric level for writeReport
        title = f'File: {fileName[0]} Collected: {timeStamp}'
        if root is None:                        
            Controller.writeReport(title,fileName, pathOut, outFilePath, level)
            return False

        msg = f'Process Single Level: {outFilePath} - SUCCESSFUL'
        print(msg)
        Utilities.writeLogFile(msg)
        if level == "L2":
            Controller.writeReport(title,fileName, pathOut, outFilePath, level)
        return True  


    # Process every file in a list of files from L0 to L2
    @staticmethod
    def processFilesMultiLevel(pathOut,inFiles, calibrationMap, ancFile=None):
        print("processFilesMultiLevel")
        # t0 = time.time()
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
        # t1 = time.time()
        # print(f'Elapsed time: {(t1-t0)/60} minutes')


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
    