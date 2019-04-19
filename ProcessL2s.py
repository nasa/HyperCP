
import numpy as np

import HDFRoot
#import HDFGroup
#import HDFDataset

from Utilities import Utilities


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
    def interpolateL2s(xData, xTimer, yTimer, newXData, kind='linear'):
        for k in xData.data.dtype.names:
            if k == "Datetag" or k == "Timetag2":
                continue
            #print(k)
            x = list(xTimer)
            new_x = list(yTimer)
            y = np.copy(xData.data[k]).tolist()
            if kind == 'cubic':
                newXData.columns[k] = Utilities.interpSpline(x, y, new_x)
            else:
                newXData.columns[k] = Utilities.interp(x, y, new_x, kind)


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
    def interpolateData(xData, yData):
        print("Interpolate Data")

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
            print("xTimer does not contain strictly increasing values")
            return False
        if not Utilities.isIncreasing(yTimer):
            print("yTimer does not contain strictly increasing values")
            return False

        xData.columns["Datetag"] = yData.data["Datetag"].tolist()
        xData.columns["Timetag2"] = yData.data["Timetag2"].tolist()


        #if Utilities.hasNan(xData):
        #    print("Found NAN 1")

        # Perform interpolation
        ProcessL2s.interpolateL2s(xData, xTimer, yTimer, xData, 'cubic')
        xData.columnsToDataset()
        

        #if Utilities.hasNan(xData):
        #    print("Found NAN 2")
        #    exit

        return True


    # interpolate GPS to match ES using linear interpolation
    @staticmethod
    def interpolateGPSData(node, gpsGroup):
        print("Interpolate GPS Data")

        if gpsGroup is None:
            print("WARNING, gpsGroup is None")
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
        print("Interpolate SATNAV Data")

        if satnavGroup is None:
            print("WARNING, satnavGroup is None")
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
        ProcessL2s.interpolateL2s(satnavAzimuthData, xTimer, yTimer, newSATNAVAzimuthData, 'linear')
        ProcessL2s.interpolateL2s(satnavHeadingData, xTimer, yTimer, newSATNAVHeadingData, 'linear')
        ProcessL2s.interpolateL2s(satnavPitchData, xTimer, yTimer, newSATNAVPitchData, 'linear')
        ProcessL2s.interpolateL2s(satnavPointingData, xTimer, yTimer, newSATNAVPointingData, 'linear')
        ProcessL2s.interpolateL2s(satnavRollData, xTimer, yTimer, newSATNAVRollData, 'linear')


        newSATNAVAzimuthData.columnsToDataset()
        newSATNAVHeadingData.columnsToDataset()
        newSATNAVPitchData.columnsToDataset()
        newSATNAVPointingData.columnsToDataset()
        newSATNAVRollData.columnsToDataset()


    # Interpolates datasets so they have common time coordinates
    @staticmethod
    def processL2s(node):

        #ProcessL2s.processGPSTime(node)

        root = HDFRoot.HDFRoot()
        root.copyAttributes(node)
        root.attributes["PROCESSING_LEVEL"] = "2s"
        root.attributes["DEPTH_RESOLUTION"] = "0.1 m"

        esGroup = None
        gpsGroup = None
        liGroup = None
        ltGroup = None
        satnavGroup = None
        for gp in node.groups:
            #if gp.id.startswith("GPS"):
            if gp.getDataset("UTCPOS"):
                print("GPS")
                gpsGroup = gp
            elif gp.getDataset("ES") and gp.attributes["FrameType"] == "ShutterLight":
                print("ES")
                esGroup = gp
            elif gp.getDataset("LI") and gp.attributes["FrameType"] == "ShutterLight":
                print("LI")
                liGroup = gp
            elif gp.getDataset("LT") and gp.attributes["FrameType"] == "ShutterLight":
                print("LT")
                ltGroup = gp
            elif gp.getDataset("AZIMUTH"):
                print("SATNAV")
                satnavGroup = gp

        refGroup = root.addGroup("Reference")
        sasGroup = root.addGroup("SAS")
        if gpsGroup is not None:
            gpsGroup2 = root.addGroup("GPS")
        if satnavGroup is not None:
            satnavGroup2 = root.addGroup("SATNAV")


        #ProcessL2s.interpolateGPSData(root, esGroup, gpsGroup)
        #ProcessL2s.interpolateSASData(root, liGroup, ltGroup)

        #ProcessL2s.interpolateData(root, liGroup, ltGroup, esGroup)
        #ProcessL2s.interpolateGPSData2(root, esGroup, gpsGroup)

        ProcessL2s.convertGroup(esGroup, "ES", refGroup, "ES_hyperspectral")        
        ProcessL2s.convertGroup(liGroup, "LI", sasGroup, "LI_hyperspectral")
        ProcessL2s.convertGroup(ltGroup, "LT", sasGroup, "LT_hyperspectral")

        esData = refGroup.getDataset("ES_hyperspectral")
        liData = sasGroup.getDataset("LI_hyperspectral")
        ltData = sasGroup.getDataset("LT_hyperspectral")

        # Find dataset with lowest amount of data
        esLength = len(esData.data["Timetag2"].tolist())
        liLength = len(liData.data["Timetag2"].tolist())
        ltLength = len(ltData.data["Timetag2"].tolist())

        interpData = None
        if esLength < liLength and esLength < ltLength:
            print("Interpolating to ES")
            interpData = esData
        elif liLength < ltLength:
            print("Interpolating to LI")
            interpData = liData
        else:
            print("Interpolating to LT")
            interpData = ltData

        #interpData = liData # Testing against Prosoft

        # Perform time interpolation
        if not ProcessL2s.interpolateData(esData, interpData):
            return None
        if not ProcessL2s.interpolateData(liData, interpData):
            return None
        if not ProcessL2s.interpolateData(ltData, interpData):
            return None

        ProcessL2s.interpolateGPSData(root, gpsGroup)
        ProcessL2s.interpolateSATNAVData(root, satnavGroup)

        return root
