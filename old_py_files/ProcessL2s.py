
import os
import numpy as np
import matplotlib.pyplot as plt

import HDFRoot
from Utilities import Utilities
from ConfigFile import ConfigFile


class ProcessL2s:

    # recalculate TimeTag2 to follow GPS UTC time
    @staticmethod
    def processGPSTime(node):
        sec = 0

        for gp in node.groups:
            #if gp.id.startswith("GPS"):
            if gp.hasDataset("UTCPOS"):
                ds = gp.getDataset("UTCPOS")
                sec = Utilities.utcToSec(ds.data["NONE"][0])
                #print("GPS UTCPOS:", ds.data["NONE"][0], "-> sec:", sec)
                #print(secToUtc(sec))

        for gp in node.groups:
            #if not gp.id.startswith("GPS"):
            if not gp.hasDataset("UTCPOS"):
                dsTimer = gp.getDataset("TIMER")
                if dsTimer is not None:
                    dsTimeTag2 = gp.getDataset("TIMETAG2")
                    for x in range(dsTimeTag2.data.shape[0]):
                        v = dsTimer.data["NONE"][x] + sec
                        dsTimeTag2.data["NONE"][x] = Utilities.secToTimeTag2(v)

        
  
       

    @staticmethod
    def interpolateL2s(xData, xTimer, yTimer, newXData, instr, kind='linear'):        
        for k in xData.data.dtype.names:
            if k == "Datetag" or k == "Timetag2":
                continue
            # print(k)
            x = list(xTimer)
            new_x = list(yTimer)
            y = np.copy(xData.data[k]).tolist()
            if kind == 'cubic':  
                # test = Utilities.interpSpline(x, y, new_x)   
                # print('len(test) = ' + str(len(test)))           
                newXData.columns[k] = Utilities.interpSpline(x, y, new_x)       
                # print('len(newXData.columns[k]) = ' + str(len(newXData.columns[k])))  
                # print('')      
            else:
                newXData.columns[k] = Utilities.interp(x, y, new_x, kind)

        Utilities.plotTimeInterp(xData, xTimer, newXData, yTimer, instr)


    # Converts a sensor group into the format used by Level 2s
    # The sensor dataset is renamed (e.g. ES -> ES_hyperspectral)
    # The separate DATETAG, TIMETAG2 datasets are combined into the sensor dataset
    @staticmethod
    def convertGroup(group, datasetName, newGroup, newDatasetName):
        sensorData = group.getDataset(datasetName)
        dateData = group.getDataset("DATETAG")
        timeData = group.getDataset("TIMETAG2")

        newSensorData = newGroup.addDataset(newDatasetName)

        # Datetag and Timetag2 columns added to sensor dataset
        newSensorData.columns["Datetag"] = dateData.data["NONE"].tolist()
        newSensorData.columns["Timetag2"] = timeData.data["NONE"].tolist()

        # Copies over the dataset
        for k in sensorData.data.dtype.names:
            #print("type",type(esData.data[k]))
            newSensorData.columns[k] = sensorData.data[k].tolist()
        newSensorData.columnsToDataset()


    # Preforms time interpolation to match xData to yData
    @staticmethod
    def interpolateData(xData, yData, instr):
        msg = ("Interpolate Data " + instr)
        print(msg)
        Utilities.writeLogFile(msg)

        # Interpolating to itself
        if xData is yData:
            return True

        #xDatetag= xData.data["Datetag"].tolist()
        xTimetag2 = xData.data["Timetag2"].tolist()

        #yDatetag= yData.data["Datetag"].tolist()
        yTimetag2 = yData.data["Timetag2"].tolist()


        # Convert TimeTag2 values to seconds to be used for interpolation
        xTimer = []
        for i in range(len(xTimetag2)):
            xTimer.append(Utilities.timeTag2ToSec(xTimetag2[i]))
        yTimer = []
        for i in range(len(yTimetag2)):
            yTimer.append(Utilities.timeTag2ToSec(yTimetag2[i]))

        if not Utilities.isIncreasing(xTimer):
            msg = ("xTimer does not contain strictly increasing values")
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        if not Utilities.isIncreasing(yTimer):
            msg = ("yTimer does not contain strictly increasing values")
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        xData.columns["Datetag"] = yData.data["Datetag"].tolist()
        xData.columns["Timetag2"] = yData.data["Timetag2"].tolist()


        #if Utilities.hasNan(xData):
        #    print("Found NAN 1")

        # Perform interpolation on full hyperspectral time series
        ProcessL2s.interpolateL2s(xData, xTimer, yTimer, xData, instr, 'cubic')
        xData.columnsToDataset()
        

        #if Utilities.hasNan(xData):
        #    print("Found NAN 2")
        #    exit

        return True


    # interpolate GPS to match ES using linear interpolation
    @staticmethod
    def interpolateGPSData(node, gpsGroup):
        # This is handled seperately in order to correct the Lat Long and UTC fields
        msg = "Interpolate GPS Data"
        print(msg)
        Utilities.writeLogFile(msg)

        if gpsGroup is None:            
            msg = "WARNING, gpsGroup is None"
            print(msg)
            Utilities.writeLogFile(msg)
            return

        refGroup = node.getGroup("Reference")
        esData = refGroup.getDataset("ES_hyperspectral")

        # GPS
        # Creates new gps group with Datetag/Timetag2 columns appended to all datasets
        gpsTimeData = gpsGroup.getDataset("UTCPOS")
        gpsCourseData = gpsGroup.getDataset("COURSE")
        gpsLatPosData = gpsGroup.getDataset("LATPOS")
        gpsLonPosData = gpsGroup.getDataset("LONPOS")
        gpsMagVarData = gpsGroup.getDataset("MAGVAR")
        gpsSpeedData = gpsGroup.getDataset("SPEED")
        gpsLatHemiData = gpsGroup.getDataset("LATHEMI")
        gpsLonHemiData = gpsGroup.getDataset("LONHEMI")

        newGPSGroup = node.getGroup("GPS")
        newGPSCourseData = newGPSGroup.addDataset("COURSE")
        newGPSLatPosData = newGPSGroup.addDataset("LATPOS")
        newGPSLonPosData = newGPSGroup.addDataset("LONPOS")
        newGPSMagVarData = newGPSGroup.addDataset("MAGVAR")
        newGPSSpeedData = newGPSGroup.addDataset("SPEED")

        # Add Datetag, Timetag2 data to gps groups
        # This matches ES data after interpolation
        newGPSCourseData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newGPSCourseData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newGPSLatPosData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newGPSLatPosData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newGPSLonPosData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newGPSLonPosData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newGPSMagVarData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newGPSMagVarData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newGPSSpeedData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newGPSSpeedData.columns["Timetag2"] = esData.data["Timetag2"].tolist()


        x = []
        y = []
        # Convert degrees minutes to decimal degrees format
        for i in range(gpsTimeData.data.shape[0]):
            latDM = gpsLatPosData.data["NONE"][i]
            latDirection = gpsLatHemiData.data["NONE"][i]
            latDD = Utilities.dmToDd(latDM, latDirection)
            gpsLatPosData.data["NONE"][i] = latDD

            lonDM = gpsLonPosData.data["NONE"][i]
            lonDirection = gpsLonHemiData.data["NONE"][i]
            lonDD = Utilities.dmToDd(lonDM, lonDirection)
            gpsLonPosData.data["NONE"][i] = lonDD
            x.append(lonDD)
            y.append(latDD)

        ''' This is a good idea to persue. No implementation yet.'''
        #print("PlotGPS")
        #Utilities.plotGPS(x, y, 'test1')
        #print("PlotGPS - DONE")


        # Convert GPS UTC time values to seconds to be used for interpolation
        xTimer = []
        for i in range(gpsTimeData.data.shape[0]):
            xTimer.append(Utilities.utcToSec(gpsTimeData.data["NONE"][i]))

        # Convert ES TimeTag2 values to seconds to be used for interpolation
        yTimer = []
        for i in range(esData.data.shape[0]):
            yTimer.append(Utilities.timeTag2ToSec(esData.data["Timetag2"][i]))


        # Interpolate by time values
        ProcessL2s.interpolateL2s(gpsCourseData, xTimer, yTimer, newGPSCourseData, 'linear')
        ProcessL2s.interpolateL2s(gpsLatPosData, xTimer, yTimer, newGPSLatPosData, 'linear')
        ProcessL2s.interpolateL2s(gpsLonPosData, xTimer, yTimer, newGPSLonPosData, 'linear')
        ProcessL2s.interpolateL2s(gpsMagVarData, xTimer, yTimer, newGPSMagVarData, 'linear')
        ProcessL2s.interpolateL2s(gpsSpeedData, xTimer, yTimer, newGPSSpeedData, 'linear')


        newGPSCourseData.columnsToDataset()
        newGPSLatPosData.columnsToDataset()
        newGPSLonPosData.columnsToDataset()
        newGPSMagVarData.columnsToDataset()
        newGPSSpeedData.columnsToDataset()


    # interpolate SATNAV to match ES
    @staticmethod
    def interpolateSATNAVData(node, satnavGroup):
        msg = "Interpolate SATNAV Data"
        print(msg)
        Utilities.writeLogFile(msg)

        if satnavGroup is None:
            msg = "WARNING, satnavGroup is None"
            print(msg)
            Utilities.writeLogFile(msg)
            return

        refGroup = node.getGroup("Reference")
        esData = refGroup.getDataset("ES_hyperspectral")

        satnavTimeData = satnavGroup.getDataset("TIMETAG2")
        satnavAzimuthData = satnavGroup.getDataset("AZIMUTH")
        satnavHeadingData = satnavGroup.getDataset("HEADING")
        satnavPitchData = satnavGroup.getDataset("PITCH")
        satnavPointingData = satnavGroup.getDataset("POINTING")
        satnavRollData = satnavGroup.getDataset("ROLL")

        newSATNAVGroup = node.getGroup("SATNAV")
        newSATNAVAzimuthData = newSATNAVGroup.addDataset("AZIMUTH")
        newSATNAVHeadingData = newSATNAVGroup.addDataset("HEADING")
        newSATNAVPitchData = newSATNAVGroup.addDataset("PITCH")
        newSATNAVPointingData = newSATNAVGroup.addDataset("POINTING")
        newSATNAVRollData = newSATNAVGroup.addDataset("ROLL")


        # Add Datetag, Timetag2 data to satnav groups
        # This matches ES data after interpolation
        newSATNAVAzimuthData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newSATNAVAzimuthData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newSATNAVHeadingData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newSATNAVHeadingData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newSATNAVPitchData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newSATNAVPitchData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newSATNAVPointingData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newSATNAVPointingData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newSATNAVRollData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newSATNAVRollData.columns["Timetag2"] = esData.data["Timetag2"].tolist()


        # Convert GPS UTC time values to seconds to be used for interpolation
        xTimer = []
        for i in range(satnavTimeData.data.shape[0]):
            xTimer.append(Utilities.timeTag2ToSec(satnavTimeData.data["NONE"][i]))

        # Convert ES TimeTag2 values to seconds to be used for interpolation
        yTimer = []
        for i in range(esData.data.shape[0]):
            yTimer.append(Utilities.timeTag2ToSec(esData.data["Timetag2"][i]))


        # Interpolate by time values
        ProcessL2s.interpolateL2s(satnavAzimuthData, xTimer, yTimer, newSATNAVAzimuthData, 'SunAz', 'linear')
        ProcessL2s.interpolateL2s(satnavHeadingData, xTimer, yTimer, newSATNAVHeadingData, 'Heading', 'linear')
        ProcessL2s.interpolateL2s(satnavPitchData, xTimer, yTimer, newSATNAVPitchData, 'Pitch', 'linear')
        ProcessL2s.interpolateL2s(satnavPointingData, xTimer, yTimer, newSATNAVPointingData, 'Pointing', 'linear')
        ProcessL2s.interpolateL2s(satnavRollData, xTimer, yTimer, newSATNAVRollData, 'Roll', 'linear')


        newSATNAVAzimuthData.columnsToDataset()
        newSATNAVHeadingData.columnsToDataset()
        newSATNAVPitchData.columnsToDataset()
        newSATNAVPointingData.columnsToDataset()
        newSATNAVRollData.columnsToDataset()


    # Interpolates datasets so they have common time coordinates.
    # According to ProSoft Manual rev. K 2017, "Almost all reference instruments have an Es sensor which ProSoft 
    # uses to calculate the time co-ordinate system. In the case of SAS instruments, an Lt sensor is always 
    # present which is used to calculate the time co-ordinate system...If Timetag2 values were appended to the 
    # logged data then those values are used as the absolute time for each frame....For SAS data the time interval 
    # is determined from the optical sensor operating at the fastest rate."
    # PysciDON used the sensor with the slowest rate.

    @staticmethod
    def processL2s(node):

        
        if fractionRemoved < 0.95: # Abort if 95% or more of data was culled

            #ProcessL2s.processGPSTime(node)
            root = HDFRoot.HDFRoot() # creates a new instance of HDFRoot Class  (not sure about the .HDFRoot...its not a module in HDFRoot.py)
            root.copyAttributes(node) # Now copy the attributes in from the L2 object
            root.attributes["PROCESSING_LEVEL"] = "2s"
            root.attributes["DEPTH_RESOLUTION"] = "N/A"

            esGroup = None # Why are these initialized like this?
            gpsGroup = None
            liGroup = None
            ltGroup = None
            satnavGroup = None
            for gp in node.groups:
                #if gp.id.startswith("GPS"):
                if gp.getDataset("UTCPOS"):
                    # print("GPS")
                    gpsGroup = gp
                elif gp.getDataset("ES") and gp.attributes["FrameType"] == "ShutterLight":
                    # print("ES")
                    esGroup = gp
                elif gp.getDataset("LI") and gp.attributes["FrameType"] == "ShutterLight":
                    # print("LI")
                    liGroup = gp
                elif gp.getDataset("LT") and gp.attributes["FrameType"] == "ShutterLight":
                    # print("LT")
                    ltGroup = gp
                elif gp.getDataset("AZIMUTH"):
                    # print("SATNAV")
                    satnavGroup = gp

            refGroup = root.addGroup("Reference")
            sasGroup = root.addGroup("SAS")
            if gpsGroup is not None:
                gpsGroup2 = root.addGroup("GPS")
            if satnavGroup is not None:
                satnavGroup2 = root.addGroup("SATNAV")

            ProcessL2s.convertGroup(esGroup, "ES", refGroup, "ES_hyperspectral")        
            ProcessL2s.convertGroup(liGroup, "LI", sasGroup, "LI_hyperspectral")
            ProcessL2s.convertGroup(ltGroup, "LT", sasGroup, "LT_hyperspectral")

            esData = refGroup.getDataset("ES_hyperspectral") # array with columns date, time, esdata*wavebands...
            liData = sasGroup.getDataset("LI_hyperspectral")
            ltData = sasGroup.getDataset("LT_hyperspectral")

            ''' PysciDON interpolates to the SLOWEST sampling rate, but ProSoft
            interpolates to the FASTEST. Not much in the literature on this, although
            Brewin et al. RSE 2016 used the slowest instrument on the AMT cruises.'''
            # Interpolate all datasets to the slowest radiometric sampling rate
            esLength = len(esData.data["Timetag2"].tolist())
            liLength = len(liData.data["Timetag2"].tolist())
            ltLength = len(ltData.data["Timetag2"].tolist())
            
            interpData = None
            if esLength < liLength and esLength < ltLength:
                msg = "ES has fewest records - interpolating to ES; This should raise a red flag."
                print(msg)
                Utilities.writeLogFile(msg)                                       
                interpData = esData
            elif liLength < ltLength:
                msg = "LI has fewest records - interpolating to LI; This should raise a red flag."
                print(msg)
                Utilities.writeLogFile(msg)                                       
                interpData = liData
            else:
                msg = "LT has fewest records - interpolating to LT"
                print(msg)
                Utilities.writeLogFile(msg)                                       
                interpData = ltData

            #interpData = liData # Testing against Prosoft ##??

            # Perform time interpolation
            if not ProcessL2s.interpolateData(esData, interpData, "ES"):
                return None
            if not ProcessL2s.interpolateData(liData, interpData, "LI"):
                return None
            if not ProcessL2s.interpolateData(ltData, interpData, "LT"):
                return None

            ProcessL2s.interpolateGPSData(root, gpsGroup)
            ProcessL2s.interpolateSATNAVData(root, satnavGroup)

            return root
        else:
            print('Nothing left to process. Quit.')
