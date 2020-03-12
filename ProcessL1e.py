
import collections
import numpy as np
import scipy as sp
import calendar

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
    # xTimer, yTimer are already converted from TimeTag2 to datetimes
    @staticmethod
    def interpolateL1e(xData, xTimer, yTimer, newXData, instr, kind='linear', fileName='default'):    
        for k in xData.data.dtype.names:
            if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                continue
            # print(k)
            x = list(xTimer)
            new_x = list(yTimer)
            y = np.copy(xData.data[k]).tolist()

            # Because x is now a list of datetime tuples, they'll need to be
            # converted to Unix timestamp values
            ''' WILL THIS WORK IN WINDOWS ??'''
            xTS = [calendar.timegm(xDT.timetuple()) for xDT in x]
            newXTS = [calendar.timegm(xDT.timetuple()) for xDT in new_x]
            
            if kind == 'cubic':  
                # test = Utilities.interpSpline(x, y, new_x)   
                # print('len(test) = ' + str(len(test)))           
                # newXData.columns[k] = Utilities.interpSpline(x, y, new_x)       
                newXData.columns[k] = Utilities.interpSpline(xTS, y, newXTS)       
                # print('len(newXData.columns[k]) = ' + str(len(newXData.columns[k])))  
                # print('')      
            else:
                # newXData.columns[k] = Utilities.interp(x, y, new_x, kind)
                newXData.columns[k] = Utilities.interp(xTS,y,newXTS, fill_value=np.nan)

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


    
    @staticmethod
    def convertGroup(group, datasetName, newGroup, newDatasetName):        
        ''' Converts a sensor group into the L1E format; option to change group name.
        The separate DATETAG, TIMETAG2, and DATETIM datasets are combined into the sensor dataset
        This also adds a temporary column in the sensor data array for datetime to be
        used in interpolation. This is later removed, as HDF5 does not support datetime'''

        dataset = group.getDataset(datasetName)
        dateData = group.getDataset("DATETAG")
        timeData = group.getDataset("TIMETAG2")
        dateTimeData = group.getDataset("DATETIME")

        # Convert degrees minutes to decimal degrees format
        if newDatasetName == "LATITUDE":
            latPosData = group.getDataset("LATPOS")
            latHemiData = group.getDataset("LATHEMI")
            for i in range(dataset.data.shape[0]):
                latDM = latPosData.data["NONE"][i]
                latDirection = latHemiData.data["NONE"][i]
                latDD = Utilities.dmToDd(latDM, latDirection)
                latPosData.data["NONE"][i] = latDD          
        if newDatasetName == "LONGITUDE":
            lonPosData = group.getDataset("LONPOS")
            lonHemiData = group.getDataset("LONHEMI")
            for i in range(dataset.data.shape[0]):
                lonDM = lonPosData.data["NONE"][i]
                lonDirection = lonHemiData.data["NONE"][i]
                lonDD = Utilities.dmToDd(lonDM, lonDirection)
                lonPosData.data["NONE"][i] = lonDD          
        newSensorData = newGroup.addDataset(newDatasetName)

        # Datetag, Timetag2, and Datetime columns added to sensor data array
        newSensorData.columns["Datetag"] = dateData.data["NONE"].tolist()
        newSensorData.columns["Timetag2"] = timeData.data["NONE"].tolist()
        newSensorData.columns["Datetime"] = dateTimeData.data

        # Copies over the sensor dataset from original group to newGroup
        for k in dataset.data.dtype.names: # For each waveband (or vector data for other groups)
            #print("type",type(esData.data[k]))
            newSensorData.columns[k] = dataset.data[k].tolist()
        newSensorData.columnsToDataset()

    @staticmethod
    def interpolateData(xData, yData, instr, fileName):
        ''' Preforms time interpolation to match xData to yData. xData is the dataset to be 
        interpolated, yData is the reference dataset with the times to be interpolated to.'''

        msg = f'Interpolate Data {instr}'
        print(msg)
        Utilities.writeLogFile(msg)

        # Interpolating to itself
        if xData is yData:
            msg = 'Skip. Other instruments are being interpolated to this one.'
            print(msg)
            Utilities.writeLogFile(msg)
            return True

        xDatetime = xData.data["Datetime"].tolist()
        yDatetime = yData.data["Datetime"].tolist()
        print('Interpolating '+str(len(xDatetime))+' timestamps from '+\
            str(min(xDatetime))+' to '+str(max(xDatetime)))
        print('           To '+str(len(yDatetime))+' timestamps from '+\
            str(min(yDatetime))+' to '+str(max(yDatetime)))

        # xData will be interpolated to yDatetimes
        xData.columns["Datetag"] = yData.data["Datetag"].tolist()
        xData.columns["Timetag2"] = yData.data["Timetag2"].tolist()
        xData.columns["Datetime"] = yData.data["Datetime"].tolist()

        #if Utilities.hasNan(xData):
        #    print("Found NAN 1")

        # Perform interpolation on full hyperspectral time series
        # ProcessL1e.interpolateL1e(xData, xTimer, yTimer, xData, instr, 'cubic', fileName)
        # ProcessL1e.interpolateL1e(xData, xTimer, yTimer, xData, instr, 'linear', fileName)
        ProcessL1e.interpolateL1e(xData, xDatetime, yDatetime, xData, instr, 'linear', fileName)
        xData.columnsToDataset()
        
        #if Utilities.hasNan(xData):
        #    print("Found NAN 2")
        #    exit
        return True
    
    # @staticmethod
    # def interpolateGPSData(node, gpsGroup, fileName):
    #     ''' Interpolate GPS to match ES using linear interpolation '''

    #     # This is handled seperately in order to correct the Lat Long and UTC fields
    #     msg = "Interpolate GPS Data"
    #     print(msg)
    #     Utilities.writeLogFile(msg)

    #     if gpsGroup is None:            
    #         msg = "WARNING, gpsGroup is None"
    #         print(msg)
    #         Utilities.writeLogFile(msg)
    #         return False

    #     # All other sensors are already interpolated to common times at this point,
    #     # so any sensor group will do here
    #     refGroup = node.getGroup("IRRADIANCE")
    #     esData = refGroup.getDataset("ES")

    #     # GPS
    #     # Creates new gps group from old with Datetag/Timetag2/Datetime columns appended to all datasets
    #     gpsTimeData = gpsGroup.getDataset("UTCPOS")
    #     gpsDatetime = gpsGroup.getDataset("DATETIME")
    #     gpsLatPosData = gpsGroup.getDataset("LATPOS")
    #     gpsLonPosData = gpsGroup.getDataset("LONPOS")
    #     gpsLatHemiData = gpsGroup.getDataset("LATHEMI")
    #     gpsLonHemiData = gpsGroup.getDataset("LONHEMI")        
    #     if ConfigFile.settings["bL1cSolarTracker"]:
    #         # gpsMagVarData = gpsGroup.getDataset("MAGVAR")
    #         gpsCourseData = gpsGroup.getDataset("COURSE")
    #         gpsSpeedData = gpsGroup.getDataset("SPEED")

    #     for gp in node.groups:
    #         if gp.id.startswith("GP"):
    #             newGPSGroup = gp
    #     # newGPSGroup = node.getGroup("Ancillary")        
    #     newGPSLatPosData = newGPSGroup.addDataset("LATITUDE")
    #     newGPSLonPosData = newGPSGroup.addDataset("LONGITUDE")
    #     if ConfigFile.settings["bL1cSolarTracker"]:
    #         # newGPSMagVarData = newGPSGroup.addDataset("MAGVAR")
    #         newGPSCourseData = newGPSGroup.addDataset("COURSE")
    #         newGPSSpeedData = newGPSGroup.addDataset("SPEED")

    #     # Add Datetag, Timetag2 and Datetime data to gps groups
    #     # This matches ES data records (timestamps) after interpolation        
    #     newGPSLatPosData.columns["Datetag"] = esData.data["Datetag"].tolist()
    #     newGPSLatPosData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
    #     newGPSLatPosData.columns["Datetime"] = esData.data["Datetime"].tolist()
    #     newGPSLonPosData.columns["Datetag"] = esData.data["Datetag"].tolist()
    #     newGPSLonPosData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
    #     newGPSLonPosData.columns["Datetime"] = esData.data["Datetime"].tolist()
    #     if ConfigFile.settings["bL1cSolarTracker"]:
    #         newGPSCourseData.columns["Datetag"] = esData.data["Datetag"].tolist()
    #         newGPSCourseData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
    #         newGPSCourseData.columns["Datetime"] = esData.data["Datetime"].tolist()
    #         # newGPSMagVarData.columns["Datetag"] = esData.data["Datetag"].tolist()
    #         # newGPSMagVarData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
    #         newGPSSpeedData.columns["Datetag"] = esData.data["Datetag"].tolist()
    #         newGPSSpeedData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
    #         newGPSSpeedData.columns["Datetime"] = esData.data["Datetime"].tolist()
        

    #     # Convert degrees minutes to decimal degrees format
    #     for i in range(gpsTimeData.data.shape[0]):
    #         latDM = gpsLatPosData.data["NONE"][i]
    #         latDirection = gpsLatHemiData.data["NONE"][i]
    #         latDD = Utilities.dmToDd(latDM, latDirection)
    #         gpsLatPosData.data["NONE"][i] = latDD

    #         lonDM = gpsLonPosData.data["NONE"][i]
    #         lonDirection = gpsLonHemiData.data["NONE"][i]
    #         lonDD = Utilities.dmToDd(lonDM, lonDirection)            
    #         gpsLonPosData.data["NONE"][i] = lonDD

    #     ''' This is a good idea to persue at some point. No implementation yet.
    #     #print("PlotGPS")
    #     #Utilities.plotGPS(x, y, 'test1')
    #     #print("PlotGPS - DONE")'''        

        
        # Convert GPS UTC time to datetime. This requires a datetag for each record.
        

        # xTimer = []
        # for i in range(gpsTimeData.data.shape[0]):
        #     xTimer.append(Utilities.utcToSec(gpsTimeData.data["NONE"][i]))

        # # yTimer = []
        yDatetime = esData.data["Datetime"]
        # # for i in range(esData.data.shape[0]):
        # #     yTimer.append(Utilities.timeTag2ToSec(esData.data["Timetag2"][i]))
        # print('Intperpolating '+str(len(xTimer))+' timestamps from '+\
        #     str(min(xTimer))+'s to '+str(max(xTimer)))
        # print(' To '+str(len(yTimer))+' timestamps from '+str(min(yTimer))+\
        #     's to '+str(max(yTimer)))

        xDatetime = gpsDatetime

        # Interpolate by time values
        # Convert GPS UTC time values to seconds to be used for interpolation        
        # ProcessL1e.interpolateL1e(gpsLatPosData, xTimer, yTimer, newGPSLatPosData, gpsLatPosData.id, 'linear', fileName)
        # ProcessL1e.interpolateL1e(gpsLonPosData, xTimer, yTimer, newGPSLonPosData, gpsLonPosData.id, 'linear', fileName)
        ProcessL1e.interpolateL1e(gpsLatPosData, xDatetime, yDatetime, newGPSLatPosData, gpsLatPosData.id, 'linear', fileName)
        ProcessL1e.interpolateL1e(gpsLonPosData, xDatetime, yDatetime, newGPSLonPosData, gpsLonPosData.id, 'linear', fileName)
        # ProcessL1e.interpolateL1e(xData, xDatetime, yDatetime, xData, instr, 'linear', fileName)
        if ConfigFile.settings["bL1cSolarTracker"]:
            # ProcessL1e.interpolateL1e(gpsMagVarData, xTimer, yTimer, newGPSMagVarData, gpsMagVarData.id, 'linear', fileName)
            # Angular interpolation is for compass angles 0-360 degrees (i.e. crossing 0, North)       
            ProcessL1e.interpolateL1eAngular(gpsCourseData, xDatetime, yDatetime, newGPSCourseData, gpsCourseData.id, fileName)        
            ProcessL1e.interpolateL1e(gpsSpeedData, xDatetime, yDatetime, newGPSSpeedData, gpsSpeedData.id, 'linear', fileName)
            newGPSCourseData.columnsToDataset()
            # newGPSMagVarData.columnsToDataset()
            newGPSSpeedData.columnsToDataset()

        newGPSLatPosData.columnsToDataset()
        newGPSLonPosData.columnsToDataset()
        return True
        

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
            return False

        refGroup = node.getGroup("IRRADIANCE")
        esData = refGroup.getDataset("ES")

        satnavTimeData = satnavGroup.getDataset("TIMETAG2")
        satnavAzimuthData = satnavGroup.getDataset("AZIMUTH")
        satnavHeadingData = satnavGroup.getDataset("HEADING")
        satnavPitchData = satnavGroup.getDataset("PITCH")
        satnavPointingData = satnavGroup.getDataset("POINTING")
        satnavRollData = satnavGroup.getDataset("ROLL")
        satnavRelAzData = satnavGroup.getDataset("REL_AZ")
        satnavElevationData = satnavGroup.getDataset("ELEVATION")
        satnavHumidityData = satnavGroup.getDataset("HUMIDITY")

        # newSATNAVGroup = node.getGroup("Ancillary")
        newSATNAVGroup = node.getGroup("SOLARTRACKER")
        newSATNAVAzimuthData = newSATNAVGroup.addDataset("AZIMUTH")
        newSATNAVHeadingData = newSATNAVGroup.addDataset("HEADING")
        newSATNAVPitchData = newSATNAVGroup.addDataset("PITCH")
        newSATNAVPointingData = newSATNAVGroup.addDataset("POINTING")
        newSATNAVRollData = newSATNAVGroup.addDataset("ROLL")
        newSATNAVRelAzData = newSATNAVGroup.addDataset("REL_AZ")
        newSATNAVElevationData = newSATNAVGroup.addDataset("ELEVATION")
        newSATNAVHumidityData = newSATNAVGroup.addDataset("HUMIDITY")

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
        newSATNAVHumidityData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newSATNAVHumidityData.columns["Timetag2"] = esData.data["Timetag2"].tolist()

        # Convert SATNAV time values to seconds to be used for interpolation
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
        ProcessL1e.interpolateL1e(satnavHumidityData, xTimer, yTimer, newSATNAVHumidityData, 'Humidity', 'linear', fileName)

        newSATNAVAzimuthData.columnsToDataset()
        newSATNAVHeadingData.columnsToDataset()
        newSATNAVPitchData.columnsToDataset()
        newSATNAVPointingData.columnsToDataset()
        newSATNAVRollData.columnsToDataset()
        newSATNAVRelAzData.columnsToDataset()
        newSATNAVElevationData.columnsToDataset()
        newSATNAVHumidityData.columnsToDataset()
        return True

    # interpolate SATNAV to match ES
    @staticmethod
    def interpolateAncData(node, ancGroup, fileName):
        msg = "Interpolate ANCILLARY_NOTRACKER Data"
        print(msg)
        Utilities.writeLogFile(msg)

        if ancGroup is None:
            msg = "WARNING, satnavGroup is None"
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        refGroup = node.getGroup("IRRADIANCE")
        esData = refGroup.getDataset("ES")

        ancTimeData = ancGroup.getDataset("TIMETAG2")
        ancAzimuthData = ancGroup.getDataset("SOLAR_AZ")
        ancHeadingData = ancGroup.getDataset("HEADING")        
        ancRelAzData = ancGroup.getDataset("REL_AZ")
        ancSZAData = ancGroup.getDataset("SZA")

        newANCGroup = node.getGroup("SOLARTRACKER")
        newANCAzimuthData = newANCGroup.addDataset("SOLAR_AZ")
        newANCHeadingData = newANCGroup.addDataset("HEADING")
        newANCRelAzData = newANCGroup.addDataset("REL_AZ")
        newANCSZAData = newANCGroup.addDataset("SZA")        

        # Add Datetag, Timetag2 data to anc groups
        # This matches ES data after interpolation
        newANCAzimuthData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newANCAzimuthData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newANCHeadingData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newANCHeadingData.columns["Timetag2"] = esData.data["Timetag2"].tolist()        
        newANCRelAzData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newANCRelAzData.columns["Timetag2"] = esData.data["Timetag2"].tolist()
        newANCSZAData.columns["Datetag"] = esData.data["Datetag"].tolist()
        newANCSZAData.columns["Timetag2"] = esData.data["Timetag2"].tolist()

        # Convert ANC time values to seconds to be used for interpolation
        xTimer = []
        for i in range(ancTimeData.data.shape[0]):
            xTimer.append(Utilities.timeTag2ToSec(ancTimeData.data["NONE"][i]))

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
        ProcessL1e.interpolateL1eAngular(ancAzimuthData, xTimer, yTimer, newANCAzimuthData, 'SunAz', fileName)
        ProcessL1e.interpolateL1eAngular(ancHeadingData, xTimer, yTimer, newANCHeadingData, 'Heading', fileName)
        ProcessL1e.interpolateL1e(ancRelAzData, xTimer, yTimer, newANCRelAzData, 'RelAz', 'linear', fileName)
        ProcessL1e.interpolateL1e(ancSZAData, xTimer, yTimer, newANCSZAData, 'SZA', 'linear', fileName)

        newANCAzimuthData.columnsToDataset()
        newANCHeadingData.columnsToDataset()
        newANCRelAzData.columnsToDataset()
        newANCSZAData.columnsToDataset()
        return True

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

        newReferenceGroup = root.addGroup("IRRADIANCE")
        newSASGroup = root.addGroup("RADIANCE")
        if node.getGroup("GPS"):
            root.groups.append(node.getGroup("GPS"))
        if node.getGroup("PYROMETER"):
            root.groups.append(node.getGroup("PYROMETER"))
        if node.getGroup("SOLARTRACKER"):
            root.groups.append(node.getGroup("SOLARTRACKER"))
        if node.getGroup("SOLARTRACKER_STATUS"):
            root.groups.append(node.getGroup("SOLARTRACKER_STATUS"))

        referenceGroup = node.getGroup("IRRADIANCE")
        sasGroup = node.getGroup("RADIANCE")

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
    
    @staticmethod
    def processL1e(node, fileName):
        '''
        Process time and wavelength interpolation across instruments and ancillary data
        '''
        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG        
        node  = Utilities.addDateTime(node)

        root = HDFRoot.HDFRoot() # creates a new instance of HDFRoot Class 
        root.copyAttributes(node) # Now copy the attributes in from the L1d object
        root.attributes["PROCESSING_LEVEL"] = "1e"
        root.attributes["DEPTH_RESOLUTION"] = "N/A"
        
        gpsGroup = None
        pyrGroup = None
        esGroup = None 
        liGroup = None
        ltGroup = None
        satnavGroup = None
        ancGroup = None # For non-SolarTracker deployments
        satmsgGroup = None
        for gp in node.groups:
            #if gp.id.startswith("GPS"):
            if gp.getDataset("UTCPOS"):
                # print("GPS")
                gpsGroup = gp
            if gp.getDataset("T"):
                # print("PYROMETER")
                pyrGroup = gp
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
            elif gp.getDataset("SOLAR_AZ"):
                # print("ANCILLARY_NOTRACKER")
                ancGroup = gp 
            elif gp.getDataset("MESSAGE"):
                # print("SATNAV")
                satmsgGroup = gp # Now labelled SOLARTRACKER at L1B to L1D

        # New group scheme combines both radiance sensors in one group
        refGroup = root.addGroup("IRRADIANCE")
        sasGroup = root.addGroup("RADIANCE")
        
        ProcessL1e.convertGroup(esGroup, "ES", refGroup, "ES")        
        ProcessL1e.convertGroup(liGroup, "LI", sasGroup, "LI")
        ProcessL1e.convertGroup(ltGroup, "LT", sasGroup, "LT")

        

        if gpsGroup is not None:
            newGPSGroup = root.addGroup("GPS")
            ProcessL1e.convertGroup(gpsGroup, "LATPOS", newGPSGroup, "LATITUDE")
            ProcessL1e.convertGroup(gpsGroup, "LONPOS", newGPSGroup, "LONGITUDE")
            latData = newGPSGroup.getDataset("LATITUDE")
            lonData = newGPSGroup.getDataset("LONGITUDE")
            if gpsGroup.id.startswith("GPRMC"):
                ProcessL1e.convertGroup(gpsGroup, "COURSE", newGPSGroup, "COURSE")
                ProcessL1e.convertGroup(gpsGroup, "SPEED", newGPSGroup, "SPEED")            
                courseData = newGPSGroup.getDataset("COURSE")
                speedData = newGPSGroup.getDataset("SPEED")
        if pyrGroup is not None:
            newPyrGroup = root.addGroup("PYROMETER")
            ProcessL1e.convertGroup(pyrGroup, "T", newPyrGroup, "T")
            pyrData = newPyrGroup.getDataset("T")
        if satnavGroup is not None:
            newSTGroup = root.addGroup("SOLARTRACKER")

            ''' Need to populate '''

        if ancGroup is not None:
            newAncGroup = root.addGroup("ANCILLARY_NOTRACKER")
            ProcessL1e.convertGroup(ancGroup, "HEADING", newAncGroup, "HEADING")
            ProcessL1e.convertGroup(ancGroup, "REL_AZ", newAncGroup, "REL_AZ")
            ProcessL1e.convertGroup(ancGroup, "SOLAR_AZ", newAncGroup, "SOLAR_AZ")
            ProcessL1e.convertGroup(ancGroup, "SZA", newAncGroup, "SZA")
            headingData = newAncGroup.getDataset("HEADING")
            relAzData = newAncGroup.getDataset("REL_AZ")
            solAzData = newAncGroup.getDataset("SOLAR_AZ")
            szaData = newAncGroup.getDataset("SZA")
        if satmsgGroup is not None:
            newSatMSGGroup = root.addGroup("SOLARTRACKER_STATUS")
            # SATMSG (SOLARTRACKER_STATUS) has no date or time, just propogate it as is
            satMSG = satmsgGroup.getDataset("MESSAGE")
            newSatMSG = newSatMSGGroup.addDataset("MESSAGE")
            # newSatMSGGroup["MESSAGE"] = satMSG
            # Copies over the dataset
            for k in satMSG.data.dtype.names:
                #print("type",type(esData.data[k]))
                newSatMSG.columns[k] = satMSG.data[k].tolist()
            newSatMSG.columnsToDataset()

        
        # PysciDON interpolated to the SLOWEST sampling rate and ProSoft
        # interpolates to the FASTEST. Not much in the literature on this, although
        # Brewin et al. RSE 2016 used the slowest instrument on the AMT cruises,
        # which makes the most sense for minimizing error.
        esData = refGroup.getDataset("ES") # array with columns date, time, esdata*wavebands...
        liData = sasGroup.getDataset("LI")
        ltData = sasGroup.getDataset("LT")

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
            msg = "LT has fewest records (as expected) - interpolating to LT"
            print(msg)
            Utilities.writeLogFile(msg)                                       
            interpData = ltData

        # Perform time interpolation
        # Note that only the specified datasets in each group will be interpolated and 
        # carried forward. For radiometers, this means that ancillary metadata such as 
        # SPECC_TEMP and THERMAL_RESP will be dropped at L1E and beyond.
        if not ProcessL1e.interpolateData(esData, interpData, "ES", fileName):
            return None
        if not ProcessL1e.interpolateData(liData, interpData, "LI", fileName):
            return None
        if not ProcessL1e.interpolateData(ltData, interpData, "LT", fileName):
            return None
        if pyrGroup is not None:
            if not ProcessL1e.interpolateData(pyrData, interpData, "T", fileName):
                return None
        
        if gpsGroup is not None:
            if not ProcessL1e.interpolateData(latData, interpData, "LATITUDE", fileName):
                return None
            if not ProcessL1e.interpolateData(lonData, interpData, "LONGITUDE", fileName):
                return None
            if gpsGroup.id.startswith("GPRMC"):
                if not ProcessL1e.interpolateData(courseData, interpData, "COURSE", fileName):
                    return None
                if not ProcessL1e.interpolateData(speedData, interpData, "SPEED", fileName):
                    return None

        if satnavGroup is not None:
            if not ProcessL1e.interpolateData(speedData, interpData, "SPEED", fileName): 
                return None

                ''' need to populate '''

        if ancGroup is not None:
            if not ProcessL1e.interpolateData(headingData, interpData, "HEADING", fileName):
                return None
            if not ProcessL1e.interpolateData(relAzData, interpData, "REL_AZ", fileName):
                return None
            if not ProcessL1e.interpolateData(solAzData, interpData, "SOLAR_AZ", fileName):
                return None
            if not ProcessL1e.interpolateData(szaData, interpData, "SZA", fileName):
                return None

        # if not ProcessL1e.interpolateGPSData(root, gpsGroup, fileName):
        # #     return None        
        # if satnavGroup is not None:
        #     if not ProcessL1e.interpolateSATNAVData(root, satnavGroup, fileName):
        #         return None
        # if ancGroup is not None:
        #     if not ProcessL1e.interpolateAncData(root, ancGroup, fileName):
        #         return None


        # Match wavelengths across instruments
        # Calls interpolateWavelengths and matchColumns
        root = ProcessL1e.matchWavelengths(root)

        #ProcessL1e.dataAveraging(newESData)
        #ProcessL1e.dataAveraging(newLIData)
        #ProcessL1e.dataAveraging(newLTData)
        return root
