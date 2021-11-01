
import csv
import os
import numpy as np
import datetime
import time

from HDFRoot import HDFRoot
from SeaBASSWriter import SeaBASSWriter
from CalibrationFileReader import CalibrationFileReader
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
    def writeReport(fileName, pathOut, outFilePath, level, inFilePath):
        print('Writing PDF Report...')
        numLevelDict = {'L1A':1,'L1B':2,'L1C':3,'L1D':4,'L1E':5,'L2':6}
        numLevel = numLevelDict[level]
        fp = os.path.join(pathOut, level, f'{fileName}_{level}.hdf')

        # Reports are written during failure at any level or success at L2.
        # The highest level succesfully processed will have the correct configurations in the HDF attributes.
        # These are potentially more accurate than values found in the ConfigFile settings.

        #   Try to open current level. If this fails, open the previous level and use all the parameters
        #   from the attributes up to that level, then use the ConfigFile.settings for the current level parameters.
        try:
            # Processing successful at this level
            root = HDFRoot.readHDF5(fp)
            fail = 0
            root.attributes['Fail'] = 0
        except:
            fail =1
            # Processing failed at this level. Open the level below it
            #   This won't work for ProcessL1A looking back for RAW...
            if level != 'L1A':
                try:
                    # Processing successful at the next lower level
                    # Shift from the output to the input directory
                    root = HDFRoot.readHDF5(inFilePath)
                except:
                    msg = "Controller.writeReport: Unable to open HDF file. May be open in another application."
                    Utilities.errorWindow("File Error", msg)
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return

            else:
                # Create a root with nothing but the fail flag in the attributes to pass to PDF reporting
                #   PDF will contain parameters from ConfigFile.settings
                root = HDFRoot()
                root.id = "/"
                root.attributes["HYPERINSPACE"] = MainConfig.settings["version"]
                root.attributes['TIME-STAMP'] = 'Null' # Collection time not preserved in failed RAW>L1A
            root.attributes['Fail'] = 1


        timeStamp = root.attributes['TIME-STAMP']
        title = f'File: {fileName} Collected: {timeStamp}'

        # Reports
        reportPath = os.path.join(pathOut, 'Reports')
        if os.path.isdir(reportPath) is False:
            os.mkdir(reportPath)
        dirPath = os.getcwd()
        inLogPath = os.path.join(dirPath, 'Logs')

        inPlotPath = os.path.join(pathOut,'Plots')
        # The inPlotPath is going to be different for L1A-L1E than L2 for many cruises...
        # In that case, move up one directory
        if os.path.isdir(os.path.join(inPlotPath, 'L1C_Anoms')) is False:
            inPlotPath = os.path.join(pathOut,'..','Plots')
        # outPDF = os.path.join(reportPath,'Reports', f'{fileName}.pdf')
        outHDF = os.path.split(outFilePath)[1]

        if fail:
            outPDF = os.path.join(reportPath, f'{os.path.splitext(outHDF)[0]}_fail.pdf')
        else:
            outPDF = os.path.join(reportPath, f'{os.path.splitext(outHDF)[0]}.pdf')

        pdf = PDF()
        pdf.set_title(title)
        pdf.set_author(f'HyperInSPACE_{MainConfig.settings["version"]}')

        inLog = os.path.join(inLogPath,f'{fileName}_L1A.log')
        if os.path.isfile(inLog):
            print('Level 1A')
            pdf.print_chapter('L1A', 'Process RAW to L1A', inLog, inPlotPath, fileName, outFilePath, root)

        if numLevel > 1:
            print('Level 1B')
            inLog = os.path.join(inLogPath,f'{fileName}_L1A_L1B.log')
            if os.path.isfile(inLog):
                pdf.print_chapter('L1B', 'Process L1A to L1B', inLog, inPlotPath, fileName, outFilePath, root)

        if numLevel > 2:
            print('Level 1C')
            inLog = os.path.join(inLogPath,f'{fileName}_L1B_L1C.log')
            if os.path.isfile(inLog):
                pdf.print_chapter('L1C', 'Process L1B to L1C', inLog, inPlotPath, fileName, outFilePath, root)

        if numLevel > 3:
            print('Level 1D')
            inLog = os.path.join(inLogPath,f'{fileName}_L1C_L1D.log')
            if os.path.isfile(inLog):
                pdf.print_chapter('L1D', 'Process L1C to L1D', inLog, inPlotPath, fileName, outFilePath, root)

        if numLevel > 4:
            print('Level 1E')
            inLog = os.path.join(inLogPath,f'{fileName}_L1D_L1E.log')
            if os.path.isfile(inLog):
                pdf.print_chapter('L1E', 'Process L1D to L1E', inLog, inPlotPath, fileName, outFilePath, root)

        if numLevel > 5:
            print('Level 2')
            # For L2, reset Plot directory
            inPlotPath = os.path.join(pathOut,'Plots')
            inLog = os.path.join(inLogPath,f'{fileName}_L1E_L2.log')
            if os.path.isfile(inLog):
                pdf.print_chapter('L2', 'Process L1E to L2', inLog, inPlotPath, fileName, outFilePath, root)

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
            elif cf.id.startswith("SATTHS"):
                cf.instrumentType = "SATTHS"
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

        return root

    @staticmethod
    def processL1b(inFilePath, outFilePath, calibrationMap):
        root = None
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

        return root

    @staticmethod
    def processL1c(inFilePath, outFilePath, ancillaryData=None):
        root = None
        # _,fileName = os.path.split(outFilePath)

        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None,

        # Process the data
        msg = ("ProcessL1c: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg)
        try:
            root = HDFRoot.readHDF5(inFilePath)
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        root = ProcessL1c.processL1c(root, ancillaryData)

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

        return root

    @staticmethod
    def processL1d(inFilePath, outFilePath):
        root = None
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None

        # Process the data
        msg = ("ProcessL1d: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg)
        try:
            root = HDFRoot.readHDF5(inFilePath)
        except:
            msg = "Controller.processL1d: Unable to open HDF file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        ''' At this stage the Anomanal parameterizations are current in ConfigFile.settings, regardless of who called this method.
            This method will promote them to root.attributes.'''
        root = ProcessL1d.processL1d(root)

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)

                # Create Plots
                # Radiometry
                _, filename = os.path.split(outFilePath)
                if ConfigFile.settings['bL2PlotEs']==1:
                    Utilities.plotRadiometryL1D(root, filename, rType='ES')
                if ConfigFile.settings['bL2PlotLi']==1:
                    Utilities.plotRadiometryL1D(root, filename, rType='LI')
                if ConfigFile.settings['bL2PlotLt']==1:
                    Utilities.plotRadiometryL1D(root, filename, rType='LT')
            except:
                msg = "Controller.ProcessL1d: Unable to write file. May be open in another application."
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

        return root

    @staticmethod
    def processL1e(inFilePath, outFilePath):
        root = None
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
                return None,
        else:
            msg = "L1e processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        return root


    @staticmethod
    def processL2(inFilePath, outFilePath):
        root = None
        if not os.path.isfile(inFilePath):
            print('No such input file: ' + inFilePath)
            return None, outFilePath

        # Process the data
        msg = ("ProcessL2: " + inFilePath)
        print(msg)
        Utilities.writeLogFile(msg)
        try:
            root = HDFRoot.readHDF5(inFilePath)
        except:
            msg = "Unable to open file. May be open in another application."
            Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, outFilePath

        root.attributes['In_Filepath'] = inFilePath
        root = ProcessL2.processL2(root)

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
                Utilities.plotRadiometry(root, filename, rType='Rrs', plotDelta = True)
            if ConfigFile.settings['bL2PlotnLw']==1:
                Utilities.plotRadiometry(root, filename, rType='nLw', plotDelta = True)
            if ConfigFile.settings['bL2PlotEs']==1:
                Utilities.plotRadiometry(root, filename, rType='ES', plotDelta = True)
            if ConfigFile.settings['bL2PlotLi']==1:
                Utilities.plotRadiometry(root, filename, rType='LI', plotDelta = True)
            if ConfigFile.settings['bL2PlotLt']==1:
                Utilities.plotRadiometry(root, filename, rType='LT', plotDelta = True)

            # IOPs
            # These three should plot GIOP and QAA together (eventually, once GIOP is complete)
            if ConfigFile.products["bL2ProdadgQaa"]:
                Utilities.plotIOPs(root, filename, algorithm = 'qaa', iopType='adg', plotDelta = False)
            if ConfigFile.products["bL2ProdaphQaa"]:
                Utilities.plotIOPs(root, filename, algorithm = 'qaa', iopType='aph', plotDelta = False)
            if ConfigFile.products["bL2ProdbbpQaa"]:
                Utilities.plotIOPs(root, filename, algorithm = 'qaa', iopType='bbp', plotDelta = False)

            # This puts ag, Sg, and DOC on the same plot
            if ConfigFile.products["bL2Prodgocad"] and ConfigFile.products["bL2ProdSg"] \
                 and ConfigFile.products["bL2Prodag"] and ConfigFile.products["bL2ProdDOC"]:
                Utilities.plotIOPs(root, filename, algorithm = 'gocad', iopType='ag', plotDelta = False)

        # Write output file
        if root is not None:
            try:
                root.writeHDF5(outFilePath)
                return root, outFilePath
            except:
                msg = "Unable to write file. May be open in another application."
                Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return None, outFilePath
        else:
            msg = "L2 processing failed. Nothing to output."
            if MainConfig.settings["popQuery"] == 0:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return None, outFilePath

    # Process every file in a list of files 1 level
    @staticmethod
    def processSingleLevel(pathOut, inFilePath, calibrationMap, level, ancFile=None):
        # Find the absolute path to the output directory
        pathOut = os.path.abspath(pathOut)
        # inFilePath is a singleton file complete with path
        inFilePath = os.path.abspath(inFilePath)
        # (inpath, inFileName) = os.path.split(inFilePath)
        inFileName = os.path.split(inFilePath)[1]
        # Grab input name and extension
        fileName,extension = os.path.splitext(inFileName)#[0]

        # Initialize the Utility logger, overwriting it if necessary
        if ConfigFile.settings["bL2Stations"] == 1 and level == 'L2':
            os.environ["LOGFILE"] = f'Stations_{fileName}_{level}.log'
        else:
            os.environ["LOGFILE"] = (fileName + '_' + level + '.log')
        msg = "Process Single Level"
        print(msg)
        Utilities.writeLogFile(msg,mode='w') # <<---- Logging initiated here

        # If this is an HDF, assume it is not RAW, drop the level from fileName
        if extension=='.hdf':
            # [basefilename, level] tolerant of multiple "_" in filename; uses last one for Level
            fileName = fileName.rsplit('_',1)[0]


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

        # if inFileName.startswith('pySAS'):
        #     outFilePath = os.path.join(pathOutLevel,fileName[0] + "_" \
        #         + fileName[1] + "_" + fileName[2] + "_" + level + ".hdf")
        # else:
        outFilePath = os.path.join(pathOutLevel,fileName + "_" + level + ".hdf")

        if level == "L1A" or level == "L1B" or \
            level == "L1C" or level == "L1D":

            if level == "L1A":
                root = Controller.processL1a(inFilePath, outFilePath, calibrationMap)
            elif level == "L1B":
                root = Controller.processL1b(inFilePath, outFilePath, calibrationMap)
            elif level == "L1C":
                # if ConfigFile.settings["bL1cSolarTracker"] == 0:
                ancillaryData = Controller.processAncData(ancFile)
                # else:
                #     ancillaryData = None
                root = Controller.processL1c(inFilePath, outFilePath, ancillaryData)
            elif level == "L1D":
                # If called locally from Controller and not AnomalyDetection.py, then
                #   try to load the parameter file for this cruise/configuration and update
                #   ConfigFile.settings to reflect the appropriate parameterizations for this
                #   particular file. If no parameter file exists, or this SAS file is not in it,
                #   then fall back on the current ConfigFile.settings.

                anomAnalFileName = os.path.splitext(ConfigFile.filename)[0]
                anomAnalFileName = anomAnalFileName + '_anoms.csv'
                fp = os.path.join('Config',anomAnalFileName)
                if os.path.exists(fp):
                    msg = 'Deglitching anomaly file found for this L1C. Using these parameters.'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    params = Utilities.readAnomAnalFile(fp)
                    # If a parameterization has been saved in the AnomAnalFile, set the properties in the local object
                    # for all sensors
                    l1CfileName = fileName + '_L1C'
                    if l1CfileName in params.keys():
                        ref = 0
                        for sensor in ['ES','LI','LT']:
                            print(f'{sensor}: Setting ConfigFile.settings to match saved parameterization. ')
                            ConfigFile.settings[f'fL1d{sensor}WindowDark'] = params[l1CfileName][ref+0]
                            ConfigFile.settings[f'fL1d{sensor}WindowLight'] = params[l1CfileName][ref+1]
                            ConfigFile.settings[f'fL1d{sensor}SigmaDark'] = params[l1CfileName][ref+2]
                            ConfigFile.settings[f'fL1d{sensor}SigmaLight'] = params[l1CfileName][ref+3]
                            ConfigFile.settings[f'fL1d{sensor}MinDark'] = params[l1CfileName][ref+4]
                            ConfigFile.settings[f'fL1d{sensor}MaxDark'] = params[l1CfileName][ref+5]
                            ConfigFile.settings[f'fL1d{sensor}MinMaxBandDark'] = params[l1CfileName][ref+6]
                            ConfigFile.settings[f'fL1d{sensor}MinLight'] = params[l1CfileName][ref+7]
                            ConfigFile.settings[f'fL1d{sensor}MaxLight'] = params[l1CfileName][ref+8]
                            ConfigFile.settings[f'fL1d{sensor}MinMaxBandLight'] = params[l1CfileName][ref+9]
                            ref += 10
                    else:
                        msg = 'This file not found in parameter file. Resorting to values in ConfigFile.settings.'
                        print(msg)
                        Utilities.writeLogFile(msg)
                else:
                    msg = 'No deglitching parameter file found. Resorting to values in ConfigFile.settings.'
                    print(msg)
                    Utilities.writeLogFile(msg)

                root = Controller.processL1d(inFilePath, outFilePath)

            # Confirm output file creation
            if os.path.isfile(outFilePath):
                modTime = os.path.getmtime(outFilePath)
                nowTime = datetime.datetime.now()
                if nowTime.timestamp() - modTime < 60: # If the file exists and was created in the last minute...
                    msg = f'{level} file produced: \n {outFilePath}'
                    print(msg)
                    Utilities.writeLogFile(msg)

        elif level == "L1E":
            root = Controller.processL1e(inFilePath, outFilePath)

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
            # if ConfigFile.settings["bL1cSolarTracker"]:
            #     ancillaryData = Controller.processAncData(ancFile)
            # else:

            # Ancillary data from metadata have been read in at L1C,
            # and will be extracted from the ANCILLARY_METADATA group later
            root, outFilePath = Controller.processL2(inFilePath, outFilePath)

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

        # Exempt station writing from reports (So as not to overwrite normal file reports...?)
        if root is None and ConfigFile.settings["bL2Stations"] == 1:
            print('No report written due to Station search, but root is None. Processing failed.')
            return False

        # If the process failed at any level, write a report and return
        if root is None and ConfigFile.settings["bL2Stations"] == 0:
            if ConfigFile.settings["bL2WriteReport"] == 1:
                Controller.writeReport(fileName, pathOut, outFilePath, level, inFilePath)
            return False

        # If L2 successful, write a report
        if level == "L2":
            if ConfigFile.settings["bL2WriteReport"] == 1:
                Controller.writeReport(fileName, pathOut, outFilePath, level, inFilePath)

        msg = f'Process Single Level: {outFilePath} - SUCCESSFUL'
        print(msg)
        Utilities.writeLogFile(msg)


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
                fileName = os.path.join('L1A',f'{os.path.splitext(inFileName)[0]}'+'_L1A.hdf')
                fp = os.path.join(os.path.abspath(pathOut),fileName)
                if Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L1B', ancFile):
                    inFileName = os.path.split(fp)[1]
                    fileName = os.path.join('L1B',f"{os.path.splitext(inFileName)[0].rsplit('_',1)[0]}"+'_L1B.hdf')
                    fp = os.path.join(os.path.abspath(pathOut),fileName)
                    if Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L1C', ancFile):
                        inFileName = os.path.split(fp)[1]
                        fileName = os.path.join('L1C',f"{os.path.splitext(inFileName)[0].rsplit('_',1)[0]}"+'_L1C.hdf')
                        fp = os.path.join(os.path.abspath(pathOut),fileName)
                        if Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L1D', ancFile):
                            inFileName = os.path.split(fp)[1]
                            fileName = os.path.join('L1D',f"{os.path.splitext(inFileName)[0].rsplit('_',1)[0]}"+'_L1D.hdf')
                            fp = os.path.join(os.path.abspath(pathOut),fileName)
                            if Controller.processSingleLevel(pathOut, fp, calibrationMap, 'L1E', ancFile):
                                inFileName = os.path.split(fp)[1]
                                fileName = os.path.join('L1E',f"{os.path.splitext(inFileName)[0].rsplit('_',1)[0]}"+'_L1E.hdf')
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
