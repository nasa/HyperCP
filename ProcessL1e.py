
import collections
import numpy as np
import scipy as sp

import HDFRoot
from Utilities import Utilities
from ConfigFile import ConfigFile


class ProcessL1e:

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

    # Time interpolation
    # xTimer, yTimer are already converted from TimeTag2 to seconds
    @staticmethod
    def interpolateL1e(xData, xTimer, yTimer, newXData, instr, kind='linear', fileName='default'):        
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

        if ConfigFile.settings["bL1ePlotTimeInterp"] == 1:
            print('Plotting time interpolations ' +instr)
            # This plots the interpolated data in Plots
            Utilities.plotTimeInterp(xData, xTimer, newXData, yTimer, instr, fileName)

    # Time interpolation
    # xTimer, yTimer are already converted from TimeTag2 to seconds
    @staticmethod
    def interpolateL1eAngular(xData, xTimer, yTimer, newXData, instr, fileName='default'):        
        for k in xData.data.dtype.names:
            if k == "Datetag" or k == "Timetag2":
                continue
            # print(k)
            x = list(xTimer)
            new_x = list(yTimer)
            y = np.copy(xData.data[k]).tolist()
            
            newXData.columns[k] = Utilities.interpAngular(x, y, new_x)

        if ConfigFile.settings["bL1ePlotTimeInterp"] == 1:
            print('Plotting time interpolations ' +instr)
            # This plots the interpolated data in Plots
            Utilities.plotTimeInterp(xData, xTimer, newXData, yTimer, instr, fileName)


    # Converts a sensor group into the format used by Level 1E
    # The sensor dataset is renamed (e.g. ES -> ES)
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
    # xData is the dataset to be interpolate, yData is the reference dataset with the times to be interpolated to.
    @staticmethod
    def interpolateData(xData, yData, instr, fileName):
        msg = f'Interpolate Data {instr}'
        print(msg)
        Utilities.writeLogFile(msg)

        # Interpolating to itself
        if xData is yData:
            msg = 'Skip. Other instruments are being interpolated to this one.'
            print(msg)
            Utilities.writeLogFile(msg)
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
            msg = "xTimer does not contain strictly increasing values"
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        if not Utilities.isIncreasing(yTimer):
            msg = "yTimer does not contain strictly increasing values"
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        print('Intperpolating '+str(len(xTimer))+' timestamps from '+\
            str(min(xTimer))+'s to '+str(max(xTimer)))
        print(' To '+str(len(yTimer))+' timestamps from '+str(min(yTimer))+\
            's to '+str(max(yTimer)))

        xData.columns["Datetag"] = yData.data["Datetag"].tolist()
        xData.columns["Timetag2"] = yData.data["Timetag2"].tolist()

        #if Utilities.hasNan(xData):
        #    print("Found NAN 1")

        # Perform interpolation on full hyperspectral time series
        # ProcessL1e.interpolateL1e(xData, xTimer, yTimer, xData, instr, 'cubic', fileName)
        ProcessL1e.interpolateL1e(xData, xTimer, yTimer, xData, instr, 'linear', fileName)
        xData.columnsToDataset()
        
        #if Utilities.hasNan(xData):
        #    print("Found NAN 2")
        #    exit
        return True

    # interpolate GPS to match ES using linear interpolation
    @staticmethod
    def interpolateGPSData(node, gpsGroup, fileName):
        # This is handled seperately in order to correct the Lat Long and UTC fields
        msg = "Interpolate GPS Data"
        print(msg)
        Utilities.writeLogFile(msg)

        if gpsGroup is None:            
            msg = "WARNING, gpsGroup is None"
            print(msg)
            Utilities.writeLogFile(msg)
            return

        refGroup = node.getGroup("Irradiance")
        esData = refGroup.getDataset("ES")

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
        # newGPSGroup = node.getGroup("Ancillary")
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

            # ''' Catch the bad KORUS GPRMC record with no Lon'''
            # if not np.isnan(lonDM):
            lonDD = Utilities.dmToDd(lonDM, lonDirection)
            
            gpsLonPosData.data["NONE"][i] = lonDD
            x.append(lonDD)
            y.append(latDD)
            # else:
            #     gpsLonPosData.data["NONE"][i] = np.nan

        ''' This is a good idea to persue. No implementation yet.
        #print("PlotGPS")
        #Utilities.plotGPS(x, y, 'test1')
        #print("PlotGPS - DONE")'''        

        # Convert ES TimeTag2 values to seconds to be used for interpolation
        xTimer = []
        for i in range(gpsTimeData.data.shape[0]):
            xTimer.append(Utilities.utcToSec(gpsTimeData.data["NONE"][i]))

        yTimer = []
        for i in range(esData.data.shape[0]):
            yTimer.append(Utilities.timeTag2ToSec(esData.data["Timetag2"][i]))
        print('Intperpolating '+str(len(xTimer))+' timestamps from '+\
            str(min(xTimer))+'s to '+str(max(xTimer)))
        print(' To '+str(len(yTimer))+' timestamps from '+str(min(yTimer))+\
            's to '+str(max(yTimer)))

        # Interpolate by time values
        # Convert GPS UTC time values to seconds to be used for interpolation        
        # Angular interpolation is for compass angles 0-360 degrees (i.e. crossing 0, North)       
        ProcessL1e.interpolateL1eAngular(gpsCourseData, xTimer, yTimer, newGPSCourseData, gpsCourseData.id, fileName)        
        ProcessL1e.interpolateL1e(gpsLatPosData, xTimer, yTimer, newGPSLatPosData, gpsLatPosData.id, 'linear', fileName)
        ProcessL1e.interpolateL1e(gpsLonPosData, xTimer, yTimer, newGPSLonPosData, gpsLonPosData.id, 'linear', fileName)
        ProcessL1e.interpolateL1e(gpsMagVarData, xTimer, yTimer, newGPSMagVarData, gpsMagVarData.id, 'linear', fileName)
        ProcessL1e.interpolateL1e(gpsSpeedData, xTimer, yTimer, newGPSSpeedData, gpsSpeedData.id, 'linear', fileName)

        newGPSCourseData.columnsToDataset()
        newGPSLatPosData.columnsToDataset()
        newGPSLonPosData.columnsToDataset()
        newGPSMagVarData.columnsToDataset()
        newGPSSpeedData.columnsToDataset()

    # interpolate SATNAV to match ES
    @staticmethod
    def interpolateSATNAVData(node, satnavGroup, fileName):
        msg = "Interpolate SATNAV Data"
        print(msg)
        Utilities.writeLogFile(msg)

        if satnavGroup is None:
            msg = "WARNING, satnavGroup is None"
            print(msg)
            Utilities.writeLogFile(msg)
            return

        refGroup = node.getGroup("Irradiance")
        esData = refGroup.getDataset("ES")

        satnavTimeData = satnavGroup.getDataset("TIMETAG2")
        satnavAzimuthData = satnavGroup.getDataset("AZIMUTH")
        satnavHeadingData = satnavGroup.getDataset("HEADING")
        satnavPitchData = satnavGroup.getDataset("PITCH")
        satnavPointingData = satnavGroup.getDataset("POINTING")
        satnavRollData = satnavGroup.getDataset("ROLL")
        satnavRelAzData = satnavGroup.getDataset("REL_AZ")
        satnavElevationData = satnavGroup.getDataset("ELEVATION")

        # newSATNAVGroup = node.getGroup("Ancillary")
        newSATNAVGroup = node.getGroup("SOLARTRACKER")
        newSATNAVAzimuthData = newSATNAVGroup.addDataset("AZIMUTH")
        newSATNAVHeadingData = newSATNAVGroup.addDataset("HEADING")
        newSATNAVPitchData = newSATNAVGroup.addDataset("PITCH")
        newSATNAVPointingData = newSATNAVGroup.addDataset("POINTING")
        newSATNAVRollData = newSATNAVGroup.addDataset("ROLL")
        newSATNAVRelAzData = newSATNAVGroup.addDataset("REL_AZ")
        newSATNAVElevationData = newSATNAVGroup.addDataset("ELEVATION")

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
        newSATNAVRelAzData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newSATNAVRelAzData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newSATNAVElevationData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newSATNAVElevationData.columns["Timetag2"] = esData.data["Timetag2"].tolist()

        # Convert GPS UTC time values to seconds to be used for interpolation
        xTimer = []
        for i in range(satnavTimeData.data.shape[0]):
            xTimer.append(Utilities.timeTag2ToSec(satnavTimeData.data["NONE"][i]))

        # Convert ES TimeTag2 values to seconds to be used for interpolation
        yTimer = []
        for i in range(esData.data.shape[0]):
            yTimer.append(Utilities.timeTag2ToSec(esData.data["Timetag2"][i]))
        print('Intperpolating '+str(len(xTimer))+' timestamps from '+\
            str(min(xTimer))+'s to '+str(max(xTimer)))
        print(' To '+str(len(yTimer))+' timestamps from '+str(min(yTimer))+\
            's to '+str(max(yTimer)))

        # Interpolate by time values
        # Angular interpolation is for compass angles 0-360 degrees (i.e. crossing 0, North)
        ProcessL1e.interpolateL1eAngular(satnavAzimuthData, xTimer, yTimer, newSATNAVAzimuthData, 'SunAz', fileName)
        ProcessL1e.interpolateL1eAngular(satnavHeadingData, xTimer, yTimer, newSATNAVHeadingData, 'Heading', fileName)
        ProcessL1e.interpolateL1e(satnavPitchData, xTimer, yTimer, newSATNAVPitchData, 'Pitch', 'linear', fileName)
        ProcessL1e.interpolateL1eAngular(satnavPointingData, xTimer, yTimer, newSATNAVPointingData, 'Pointing', fileName)
        ProcessL1e.interpolateL1e(satnavRollData, xTimer, yTimer, newSATNAVRollData, 'Roll', 'linear', fileName)
        ProcessL1e.interpolateL1e(satnavRelAzData, xTimer, yTimer, newSATNAVRelAzData, 'RelAz', 'linear', fileName)
        ProcessL1e.interpolateL1e(satnavElevationData, xTimer, yTimer, newSATNAVElevationData, 'Elevation', 'linear', fileName)

        newSATNAVAzimuthData.columnsToDataset()
        newSATNAVHeadingData.columnsToDataset()
        newSATNAVPitchData.columnsToDataset()
        newSATNAVPointingData.columnsToDataset()
        newSATNAVRollData.columnsToDataset()
        newSATNAVRelAzData.columnsToDataset()
        newSATNAVElevationData.columnsToDataset()

    # Interpolates by wavelength
    @staticmethod
    def interpolateWavelength(ds, newDS, newWavebands):

        # Copy dataset to dictionary
        ds.datasetToColumns()
        columns = ds.columns
        saveDatetag = columns.pop("Datetag")
        saveTimetag2 = columns.pop("Timetag2")
        
        # Get wavelength values
        wavelength = []
        for k in columns:
            #print(k)
            wavelength.append(float(k))

        x = np.asarray(wavelength)

        ''' PySciDON interpolated each instrument to a different set of bands.
            Here we use a common set.'''
        newColumns = collections.OrderedDict()
        newColumns["Datetag"] = saveDatetag
        newColumns["Timetag2"] = saveTimetag2

        for i in range(newWavebands.shape[0]):
            newColumns[str(newWavebands[i])] = []

        # Perform interpolation for each row
        for timeIndex in range(len(saveDatetag)):
            values = []

            for k in columns:
                values.append(columns[k][timeIndex])

            y = np.asarray(values)
            #new_y = sp.interpolate.interp1d(x, y)(newWavebands)
            new_y = sp.interpolate.InterpolatedUnivariateSpline(x, y, k=3)(newWavebands)

            for waveIndex in range(newWavebands.shape[0]):
                newColumns[str(newWavebands[waveIndex])].append(new_y[waveIndex])

        newDS.columns = newColumns
        newDS.columnsToDataset()

    # Determines points to average data
    # Note: Prosoft always includes 1 point left/right of n
    #       even if it is outside of specified width
    @staticmethod
    def getDataAverage(n, data, time, width):
        lst = [data[n]]
        i = n-1
        while i >= 0:
            lst.append(data[i])
            if (time[n] - time[i]) > width:
                break
            i -= 1
        i = n+1
        while i < len(time):
            lst.append(data[i])
            if (time[i] - time[n]) > width:
                break
            i += 1
        avg = 0
        for v in lst:
            avg += v
        avg /= len(lst)
        return avg


    # Makes each dataset have matching wavelength values
    # (this is not required, only for testing)
    @staticmethod
    def matchColumns(esData, liData, ltData):

        msg = "Match Columns"
        print(msg)
        Utilities.writeLogFile(msg)

        esData.datasetToColumns()
        liData.datasetToColumns()
        ltData.datasetToColumns()

        matchMin = -1
        matchMax = -1

        # Determine the minimum and maximum values for k
        for ds in [esData, liData, ltData]:
            nMin = -1
            nMax = -1
            for k in ds.columns.keys():
                if Utilities.isFloat(k):
                    num = float(k)
                    if nMin == -1:
                        nMin = num
                        nMax = num
                    elif num < nMin:
                        nMin = num
                    elif num > nMax:
                        nMax = num
            if matchMin == -1:
                matchMin = nMin
                matchMax = nMax
            if matchMin < nMin:
                matchMin = nMin
            if matchMax > nMax:
                matchMax = nMax

        # Remove values to match minimum and maximum
        for ds in [esData, liData, ltData]:
            l = []
            for k in ds.columns.keys():
                if Utilities.isFloat(k):
                    num = float(k)
                    if num < matchMin:
                        l.append(k)
                    elif num > matchMax:
                        l.append(k)
            for k in l:
                del ds.columns[k]

        esData.columnsToDataset()
        liData.columnsToDataset()
        ltData.columnsToDataset()

    @staticmethod
    def matchWavelengths(node):
        print('Interpolating to common wavelengths')
        # Wavelength Interpolation
        root = HDFRoot.HDFRoot()
        root.copyAttributes(node)
        
        interval = float(ConfigFile.settings["fL1eInterpInterval"])
        
        root.attributes["WAVEL_INTERP"] = (str(interval) + " nm") 

        newReferenceGroup = root.addGroup("Irradiance")
        newSASGroup = root.addGroup("Radiance")
        if node.getGroup("GPS"):
            root.groups.append(node.getGroup("GPS"))
        if node.getGroup("SOLARTRACKER"):
            root.groups.append(node.getGroup("SOLARTRACKER"))
        if node.getGroup("SOLARTRACKER_STATUS"):
            root.groups.append(node.getGroup("SOLARTRACKER_STATUS"))

        referenceGroup = node.getGroup("Irradiance")
        sasGroup = node.getGroup("Radiance")

        esData = referenceGroup.getDataset("ES")
        liData = sasGroup.getDataset("LI")
        ltData = sasGroup.getDataset("LT")

        newESData = newReferenceGroup.addDataset("ES")
        newLIData = newSASGroup.addDataset("LI")
        newLTData = newSASGroup.addDataset("LT")

        ''' PySciDON interpolated each instrument to a different set of bands.
        Here we use a common set.'''
        # Es dataset to dictionary
        esData.datasetToColumns()
        columns = esData.columns
        columns.pop("Datetag")
        columns.pop("Timetag2")
        # Get wavelength values
        esWavelength = []
        for k in columns:
            esWavelength.append(float(k))
        # Determine interpolated wavelength values
        esStart = np.ceil(esWavelength[0])
        esEnd = np.floor(esWavelength[len(esWavelength)-1])
        
        # Li dataset to dictionary
        liData.datasetToColumns()
        columns = liData.columns
        columns.pop("Datetag")
        columns.pop("Timetag2")
        # Get wavelength values
        liWavelength = []
        for k in columns:
            liWavelength.append(float(k))
        # Determine interpolated wavelength values
        liStart = np.ceil(liWavelength[0])
        liEnd = np.floor(liWavelength[len(liWavelength)-1])
        
        # Lt dataset to dictionary
        ltData.datasetToColumns()
        columns = ltData.columns
        columns.pop("Datetag")
        columns.pop("Timetag2")
        # Get wavelength values
        ltWavelength = []
        for k in columns:
            ltWavelength.append(float(k))

        # Determine interpolated wavelength values
        ltStart = np.ceil(ltWavelength[0])
        ltEnd = np.floor(ltWavelength[len(liWavelength)-1])

        # No extrapolation
        start = max(esStart,liStart,ltStart)
        end = min(esEnd,liEnd,ltEnd)
        newWavebands = np.arange(start, end, interval)
        # print(newWavebands)

        print('Interpolating Es')
        ProcessL1e.interpolateWavelength(esData, newESData, newWavebands)
        print('Interpolating Li')
        ProcessL1e.interpolateWavelength(liData, newLIData, newWavebands)
        print('Interpolating Lt')
        ProcessL1e.interpolateWavelength(ltData, newLTData, newWavebands)

        return root


    # Does time and wavelength interpolation and data averaging (latter not implemented here)
    @staticmethod
    def processL1e(node, fileName):
        
        root = HDFRoot.HDFRoot() # creates a new instance of HDFRoot Class 
        root.copyAttributes(node) # Now copy the attributes in from the L1d object
        root.attributes["PROCESSING_LEVEL"] = "1e"
        root.attributes["DEPTH_RESOLUTION"] = "N/A"

        esGroup = None 
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
                satnavGroup = gp # Now labelled SOLARTRACKER at L1B to L1D
            elif gp.getDataset("MESSAGE"):
                # print("SATNAV")
                satmsgGroup = gp # Now labelled SOLARTRACKER at L1B to L1D

        refGroup = root.addGroup("Irradiance")
        sasGroup = root.addGroup("Radiance")
        if gpsGroup is not None:
            root.addGroup("GPS")
        if satnavGroup is not None:
            root.addGroup("SOLARTRACKER")
        if satmsgGroup is not None:
            root.addGroup("SOLARTRACKER_STATUS")

        ProcessL1e.convertGroup(esGroup, "ES", refGroup, "ES")        
        ProcessL1e.convertGroup(liGroup, "LI", sasGroup, "LI")
        ProcessL1e.convertGroup(ltGroup, "LT", sasGroup, "LT")

        esData = refGroup.getDataset("ES") # array with columns date, time, esdata*wavebands...
        liData = sasGroup.getDataset("LI")
        ltData = sasGroup.getDataset("LT")

        ''' PysciDON interpolates to the SLOWEST sampling rate, but ProSoft
        interpolates to the FASTEST. Not much in the literature on this, although
        Brewin et al. RSE 2016 used the slowest instrument on the AMT cruises.'''
        # Interpolate all datasets to the SLOWEST radiometric sampling rate
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

        # Perform time interpolation
        if not ProcessL1e.interpolateData(esData, interpData, "ES", fileName):
            return None
        if not ProcessL1e.interpolateData(liData, interpData, "LI", fileName):
            return None
        if not ProcessL1e.interpolateData(ltData, interpData, "LT", fileName):
            return None
        ProcessL1e.interpolateGPSData(root, gpsGroup, fileName)
        ProcessL1e.interpolateSATNAVData(root, satnavGroup, fileName)

        # Match wavelengths across instruments
        # Calls interpolateWavelengths and matchColumns
        root = ProcessL1e.matchWavelengths(root)

        #ProcessL1e.dataAveraging(newESData)
        #ProcessL1e.dataAveraging(newLIData)
        #ProcessL1e.dataAveraging(newLTData)
        return root
