
import collections
import datetime as dt
import time
import calendar
from inspect import currentframe, getframeinfo
from pysolar.solar import get_azimuth, get_altitude
import numpy as np
import scipy as sp
import warnings

from Source.HDFRoot import HDFRoot
from Source.Utilities import Utilities
from Source.ConfigFile import ConfigFile


class ProcessL1b_Interp:

    @staticmethod
    def interp_Anc(node, fileName):
        '''
        Time interpolation of Ancillary group only to be run prior to model fill and FRM cal/corrections
            Required fields relAz, sza, solarAz must be in Ancillary already, or be obtained from SunTrackers
        '''
        print('Interpolating Ancillary data to radiometry timestamps')
        gpsGroup,STGroup,esGroup,liGroup,ltGroup,ancGroup = None,None,None,None,None,None
        for gp in node.groups:
            if gp.id.startswith("GP"): 
                gpsGroup = gp
                for ds in gpsGroup.datasets:
                    if ds != 'DATETIME':
                        gpsGroup.datasets[ds].datasetToColumns()
            if gp.id == ("ANCILLARY_METADATA"):
                ancGroup = gp
            if gp.id.startswith("ES"):
                esGroup = gp
            if gp.id.startswith("LI"):
                liGroup = gp
            if gp.id.startswith("LT"):
                ltGroup = gp
            if gp.id.startswith("SunTracker"):
                STGroup = gp

        # Conversion of datasets within groups to move date/timestamps into
        # the data arrays and add datetime column. Also can change dataset name.
        # Places the dataset into the new group.
        # New group scheme combines both radiance sensors in one group

        # Several new groups need to be added, but will be deleted below. Only new ANCILLARY_METADATA and GPS will be retained.
        #
        refGroup = node.addGroup("IRRADIANCE_TEMP")
        sasGroup = node.addGroup("RADIANCE_TEMP")
        ProcessL1b_Interp.convertDataset(esGroup, "ES", refGroup, "ES")
        ProcessL1b_Interp.convertDataset(liGroup, "LI", sasGroup, "LI")
        ProcessL1b_Interp.convertDataset(ltGroup, "LT", sasGroup, "LT")

        newGPSGroup = node.addGroup("GPS_TEMP")
        courseData,sogData = None,None
        # Required for non-Tracker:
        #   May be acquired from Ancillary or SunTracker (preferred)
        relAzData,szaData,solAzData = None,None,None
        if gpsGroup is not None:
            newGPSGroup.attributes = gpsGroup.attributes.copy()
            # These are from the raw data, not to be confused with those in the ancillary file

            # Only if the right NMEA data are provided (e.g. with SunTracker)
            if 'CalFileName' in gpsGroup.attributes:
                if gpsGroup.attributes["CalFileName"].startswith("GPRMC"): #pySAS, SolarTracker with GPS TDF input
                    ProcessL1b_Interp.convertDataset(gpsGroup, "LATPOS", newGPSGroup, "LATITUDE")
                    ProcessL1b_Interp.convertDataset(gpsGroup, "LONPOS", newGPSGroup, "LONGITUDE")
                    ProcessL1b_Interp.convertDataset(gpsGroup, "COURSE", newGPSGroup, "COURSE")
                    ProcessL1b_Interp.convertDataset(gpsGroup, "SPEED", newGPSGroup, "SPEED")
                    courseData = newGPSGroup.getDataset("COURSE")
                    courseData.datasetToColumns()
                    sogData = newGPSGroup.getDataset("SPEED")
                    sogData.datasetToColumns()
                    newGPSGroup.datasets['SPEED'].id="SOG"
                elif gpsGroup.attributes["CalFileName"] == 'GPS_MSDA': # MSDA_XE merged GPS
                    ProcessL1b_Interp.convertDataset(gpsGroup, "LATITUDE", newGPSGroup, "LATITUDE")
                    ProcessL1b_Interp.convertDataset(gpsGroup, "LONGITUDE", newGPSGroup, "LONGITUDE")

            newGPSGroup.attributes["SOURCE"] = 'GPS'
        else:
            # These are from the ancillary file; place in GPS
            #   Ignore COURSE and SOG
            # TODO: If GPS is part of the SunTracker group, and gpsGroup was not yet established, pull Lat/Lon from Suntracker Group
            ProcessL1b_Interp.convertDataset(ancGroup, "LATITUDE", newGPSGroup, "LATITUDE")
            ProcessL1b_Interp.convertDataset(ancGroup, "LONGITUDE", newGPSGroup, "LONGITUDE")
            newGPSGroup.attributes["SOURCE"] = 'ANCILLARY'
            newGPSGroup.attributes["CalFileName"] = 'ANCILLARY'

        latData = newGPSGroup.getDataset("LATITUDE")
        lonData = newGPSGroup.getDataset("LONGITUDE")

        if STGroup is not None:
            newSTGroup = node.addGroup('ST_TEMP') # temporary
            for ds in STGroup.datasets:
                # NOTE: New platforms should confirm their SunTracker robots have the proper datasets added here.
                if ds == 'REL_AZ':
                    ProcessL1b_Interp.convertDataset(STGroup, "REL_AZ", newSTGroup, "REL_AZ")
                    relAzData = newSTGroup.datasets['REL_AZ']
                if ds == 'SOLAR_AZ':
                    ProcessL1b_Interp.convertDataset(STGroup, "SOLAR_AZ", newSTGroup, "SOLAR_AZ")
                    solAzData = newSTGroup.datasets['SOLAR_AZ']
                if ds == 'SZA':
                    ProcessL1b_Interp.convertDataset(STGroup, "SZA", newSTGroup, "SZA")
                    szaData = newSTGroup.datasets['SZA']

        newAncGroup = node.addGroup("ANCILLARY_TEMP")
        newAncGroup.attributes = ancGroup.attributes.copy()

        ####################################################################################
        # Convert new Ancillary Group to flip date/timetags into columns and out of datasets
        for ds in ancGroup.datasets:
            if ds != "DATETAG" and ds != "TIMETAG2" and ds != "DATETIME":
                ProcessL1b_Interp.convertDataset(ancGroup, ds, newAncGroup, ds)
        ####################################################################################

        # Required
        # Preferentially from SunTracker over Ancillary file
        if not relAzData:
            # Here from Ancillary file, not SunTracker
            if "REL_AZ" in newAncGroup.datasets:
                # ProcessL1b_Interp.convertDataset(newAncGroup, "REL_AZ", newSTGroup, "REL_AZ")
                relAzData = newAncGroup.getDataset("REL_AZ")
        else:
            # Here from SunTracker; different timestamp from other Ancillary; interpolated below
            ProcessL1b_Interp.convertDataset(STGroup,"REL_AZ", newAncGroup,"REL_AZ")
        if not solAzData:
            if "SOLAR_AZ" in newAncGroup.datasets:
                solAzData = newAncGroup.getDataset("SOLAR_AZ")
        else:
            ProcessL1b_Interp.convertDataset(STGroup,"SOLAR_AZ", newAncGroup,"SOLAR_AZ")
        if not szaData:
            if "SZA" in newAncGroup.datasets:
                szaData = newAncGroup.getDataset("SZA")
        else:
            ProcessL1b_Interp.convertDataset(STGroup,"SZA", newAncGroup,"SZA")

        # Optional Data:
        stationData,headingDataAnc,latDataAnc,lonDataAnc,cloudData,waveData,speedData = \
            None,None,None,None,None,None,None,
        # Optional and may reside in SunTracker or SATTHS group
        pitchAncData,rollAncData = None,None
        # Optional, assured with MERRA2 models when selected
        saltData,sstData,windData,aodData,airData = None,None,None,None,None

        # Optional (already converted):
        if "STATION" in newAncGroup.datasets:
            stationData = newAncGroup.getDataset("STATION")
        if "HEADING" in newAncGroup.datasets:
            headingDataAnc = newAncGroup.getDataset("HEADING") # This HEADING derives from ancillary data file (NOT GPS or pySAS)
        if "LATITUDE" in newAncGroup.datasets:
            latDataAnc = newAncGroup.getDataset("LATITUDE")
        if "LONGITUDE" in newAncGroup.datasets:
            lonDataAnc = newAncGroup.getDataset("LONGITUDE")
        if "SALINITY" in newAncGroup.datasets:
            saltData = newAncGroup.getDataset("SALINITY")
        if "SST" in newAncGroup.datasets:
            sstData = newAncGroup.getDataset("SST")
        if "WINDSPEED" in newAncGroup.datasets:
            windData = newAncGroup.getDataset("WINDSPEED")
        if "AIRTEMP" in newAncGroup.datasets:
            airData = newAncGroup.getDataset("AIRTEMP") 
        if "AOD" in newAncGroup.datasets:
            aodData = newAncGroup.getDataset("AOD")
        if "CLOUD" in newAncGroup.datasets:
            cloudData = newAncGroup.getDataset("CLOUD")
        if "WAVE_HT" in newAncGroup.datasets:
            waveData = newAncGroup.getDataset("WAVE_HT")
        if "SPEED_F_W" in newAncGroup.datasets:
            speedData = newAncGroup.getDataset("SPEED_F_W")
        # Allow for the unlikely option that pitch/roll data are included in both the SunTracker/pySAS and Ancillary datasets
        if "PITCH" in newAncGroup.datasets:
            pitchAncData = newAncGroup.getDataset("PITCH")
        if "ROLL" in newAncGroup.datasets:
            rollAncData = newAncGroup.getDataset("ROLL")

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
            Utilities.writeLogFileAndPrint(f"ES has fewest records - interpolating to ES. This should raise a red flag; {esLength} records")
            interpData = esData
        elif liLength < ltLength:
            Utilities.writeLogFileAndPrint(f"LI has fewest records - interpolating to LI. This should raise a red flag; {liLength} records")
            interpData = liData
        else:
            Utilities.writeLogFileAndPrint(f"LT has fewest records (as expected) - interpolating to LT; {ltLength} records")
            interpData = ltData

        # latData, lonData need to correspond to interpData.
        # Preferentially from GPS, else from Anc file (above)
        if not ProcessL1b_Interp.interpolateData(latData, interpData, "LATITUDE", fileName):
            return None
        if not ProcessL1b_Interp.interpolateData(lonData, interpData, "LONGITUDE", fileName):
            return None
        if courseData:
            if not ProcessL1b_Interp.interpolateData(courseData, interpData, "TRUE", fileName):
                return None
        if sogData:
            if not ProcessL1b_Interp.interpolateData(sogData, interpData, "NONE", fileName):
                return None

        # Required:
        if not ProcessL1b_Interp.interpolateData(newAncGroup.datasets['REL_AZ'], interpData, "REL_AZ", fileName):
            Utilities.writeLogFileAndPrint("Error: REL_AZ missing from Ancillary data, and no Tracker group")
            return None
        # Solar geometries are not interpolated, but re-calculated, so need latData, lonData
        if not ProcessL1b_Interp.interpolateData(newAncGroup.datasets['SOLAR_AZ'], interpData, "SOLAR_AZ", fileName, latData, lonData):
            Utilities.writeLogFileAndPrint("Error: SOLAR_AZ missing from Ancillary data, and no Tracker group")
            return None
        if not ProcessL1b_Interp.interpolateData(newAncGroup.datasets['SZA'], interpData, "SZA", fileName, latData, lonData):
            Utilities.writeLogFileAndPrint("Error: SZA missing from Ancillary data, and no Tracker group")
            return None

        # Optional:
        #   Already in newAncGroup
        if stationData:
            ProcessL1b_Interp.interpolateData(stationData, interpData, "STATION", fileName)
        if aodData:
            ProcessL1b_Interp.interpolateData(aodData, interpData, "AOD", fileName)
        if headingDataAnc:
            ProcessL1b_Interp.interpolateData(headingDataAnc, interpData, "HEADING", fileName)
        if latDataAnc:
            ProcessL1b_Interp.interpolateData(latDataAnc, interpData, "LATITUDE", fileName)
        if lonDataAnc:
            ProcessL1b_Interp.interpolateData(lonDataAnc, interpData, "LONGITUDE", fileName)
        if saltData:
            ProcessL1b_Interp.interpolateData(saltData, interpData, "SALINITY", fileName)
        if sstData:
            ProcessL1b_Interp.interpolateData(sstData, interpData, "SST", fileName)
        if windData:
            ProcessL1b_Interp.interpolateData(windData, interpData, "WINDSPEED", fileName)
        if airData:
            ProcessL1b_Interp.interpolateData(airData, interpData, "AIRTEMP", fileName)
        if cloudData:
            ProcessL1b_Interp.interpolateData(cloudData, interpData, "CLOUD", fileName)
        if waveData:
            ProcessL1b_Interp.interpolateData(waveData, interpData, "WAVE_HT", fileName)
        if speedData:
            ProcessL1b_Interp.interpolateData(speedData, interpData, "SPEED_F_W", fileName)
        if "PITCH" in ancGroup.datasets:
            ProcessL1b_Interp.interpolateData(pitchAncData, interpData, "PITCH", fileName)
        if "ROLL" in ancGroup.datasets:
            ProcessL1b_Interp.interpolateData(rollAncData, interpData, "ROLL", fileName)

        if STGroup is not None:
            node.removeGroup(newSTGroup)
        node.removeGroup(sasGroup)
        node.removeGroup(refGroup)
        node.removeGroup(gpsGroup)
        newGPSGroup.id = 'GPS'
        node.removeGroup(ancGroup)
        newAncGroup.id = 'ANCILLARY_METADATA'

        return True

    @staticmethod
    def interpolateL1b_Interp(xData, xTimer, yTimer, newXData, dataName, kind='linear', fileName='default'):
        ''' Time interpolation
            xTimer, yTimer are already converted from TimeTag2 to Datetimes
            newXData is used instead of a return; often flipped back into xData on call
        '''

        # List of datasets requiring angular interpolation (i.e. through 0 degrees)
        angList = ['AZIMUTH', 'POINTING', 'HEADING']
        # NOTE: SOLAR_AZ and SZA are now recalculated for new timestamps rather than interpolated
        #        REL_AZ is +/- 90-135 and should not be interpolated using interAngular
        #

        # List of datasets requiring fill instead of interpolation
        fillList = ['STATION']

        for k in xData.data.dtype.names:
            if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                continue
            # print(k)
            x = list(xTimer)
            new_x = list(yTimer)
            y = np.copy(xData.data[k]).tolist()

            # Because x is now a list of datetime tuples, they'll need to be
            # converted to Unix timestamp values
            # # BUG: This conversion got the wrong result pre v1.2.13:
            # xTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in x]
            # newXTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in new_x]
            xTS = [time.mktime(xDT.timetuple()) for xDT in x]
            newXTS = [time.mktime(xDT.timetuple()) for xDT in new_x]
            # # Test conversion reversal
            # from datetime import datetime
            # datetime_object = [datetime.fromtimestamp(x) for x in xTS]

            if dataName in angList:

                newXData.columns[k] = Utilities.interpAngular(xTS, y, newXTS, fill_value=0)

                # Some angular measurements (like SAS pointing) are + and -, and get converted
                # to all +. Convert them back to - for 180-359
                if dataName == "POINTING":
                    pointingData = newXData.columns[k]
                    for i, angle in enumerate(pointingData):
                        if angle > 180:
                            pointingData[i] = angle - 360

            elif dataName in fillList:
                newXData.columns[k] = Utilities.interpFill(xTS,y,newXTS, fillValue=np.nan)

            else:
                if kind == 'cubic':
                    newXData.columns[k] = Utilities.interpSpline(xTS, y, newXTS)
                else:
                    newXData.columns[k] = Utilities.interp(xTS,y,newXTS, fill_value=np.nan)

        if ConfigFile.settings["bL1bPlotTimeInterp"] == 1 and dataName != 'T':
            print('Plotting time interpolations ' +dataName)
            # Plots the interpolated data in /Plots/
            Utilities.plotTimeInterp(xData, xTimer, newXData, yTimer, dataName, fileName)

    @staticmethod
    def convertDataset(group, datasetName, newGroup, newDatasetName):
        ''' Converts a sensor group into the L1B format; option to change dataset name.
            Moves dataset to new group.
            The separate DATETAG, TIMETAG2, and DATETIME datasets are combined into
            the sensor dataset. This also adds a temporary column in the sensor data
            array for datetime to be used in interpolation. This is later removed, as
            HDF5 does not support datetime. '''

        dataset = group.getDataset(datasetName)
        dateData = group.getDataset("DATETAG")
        timeData = group.getDataset("TIMETAG2")
        dateTimeData = group.getDataset("DATETIME")

        # Convert degrees minutes to decimal degrees format; only for GPS, not ANCILLARY_METADATA
        if group.id.startswith("GP"):
            if group.id == "GPS_MSDA":
                if newDatasetName == "LATITUDE":
                    # for i in range(dataset.data.shape[0]):
                    latPosData = group.getDataset("LATITUDE")
                if newDatasetName == "LONGITUDE":
                    # for i in range(dataset.data.shape[0]):
                    latPosData = group.getDataset("LONGITUDE")
            else:
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

        newSensorData.attributes = group.attributes.copy()

    @staticmethod
    def interpolateData(xData, yData, dataName, fileName, latData=None, lonData=None):
        ''' Preforms time interpolation to match xData to yData. xData is the dataset to be
        interpolated, yData is the reference dataset with the times to be interpolated to.'''

        Utilities.writeLogFileAndPrint(f'Interpolate Data {dataName}')

        # Interpolating to itself
        if xData is yData:
            Utilities.writeLogFileAndPrint('Skip. Other instruments are being interpolated to this one.')
            return True

        xDatetime = xData.data["Datetime"].tolist()
        yDatetime = yData.data["Datetime"].tolist()
        print('Interpolating '+str(len(xDatetime))+' timestamps from '+\
            str(min(xDatetime))+' to '+str(max(xDatetime)))
        print('           To '+str(len(yDatetime))+' timestamps from '+\
            str(min(yDatetime))+' to '+str(max(yDatetime)))

        if Utilities.hasNan(xData):
            frameinfo = getframeinfo(currentframe())
            # print(frameinfo.filename, frameinfo.lineno)
            Utilities.writeLogFileAndPrint(f'found NaN {frameinfo.lineno}')

            if dataName == 'REL_AZ':
                # Replace nans by interpolating over them if necessary
                if 'REL_AZ' in xData.columns:
                    y = np.array(xData.columns['REL_AZ'])   # <- Robot file
                else:
                    y = np.array(xData.columns['NONE'])     # <- Ancillary file
                nans, x= Utilities.nan_helper(y) # x is a lambda function
                y[nans]= np.interp(x(nans), x(~nans), y[~nans])
                if 'REL_AZ' in xData.columns:
                    xData.columns['REL_AZ'] = y.tolist()
                else:
                    xData.columns['NONE'] = y.tolist()
                xData.columnsToDataset()

                Utilities.writeLogFileAndPrint(f'Replaced NaNs in {dataName}')

        # xData will be interpolated to yDatetimes
        xData.columns["Datetag"] = yData.data["Datetag"].tolist()
        xData.columns["Timetag2"] = yData.data["Timetag2"].tolist()
        xData.columns["Datetime"] = yData.data["Datetime"].tolist()

        # Perform interpolation on full hyperspectral time series
        #   In the case of solar geometries, calculate to new times, don't interpolate
        if dataName == 'SOLAR_AZ':
            sunAzimuthAnc = []

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                for i, dt_utc in enumerate(yDatetime):
                    sunAzimuthAnc.append(get_azimuth(latData.columns['NONE'][i],lonData.columns['NONE'][i],dt_utc,0))
            xData.columns['NONE'] = sunAzimuthAnc
        elif dataName == 'SZA':
            sunZenithAnc = []

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                for i, dt_utc in enumerate(yDatetime):
                    sunZenithAnc.append(90 - get_altitude(latData.columns['NONE'][i],lonData.columns['NONE'][i],dt_utc,0))
            xData.columns['NONE'] = sunZenithAnc
        else:
            ProcessL1b_Interp.interpolateL1b_Interp(xData, xDatetime, yDatetime, xData, dataName, 'linear', fileName)

        xData.columnsToDataset()

        if Utilities.hasNan(xData):
            frameinfo = getframeinfo(currentframe())
            Utilities.writeLogFileAndPrint(f'found NaN {frameinfo.lineno}')
        return True

    @staticmethod
    def interpolateWavelength(ds, newDS, newWavebands):
        ''' Wavelength Interpolation
            Use a common waveband set determined by the maximum lowest wavelength
            of all sensors, the minimum highest wavelength, and the interval
            set in the Configuration Window. '''

        # Copy dataset to dictionary
        ds.datasetToColumns()
        columns = ds.columns
        saveDatetag = columns.pop("Datetag")
        saveTimetag2 = columns.pop("Timetag2")
        columns.pop("Datetime")

        # Get wavelength values
        wavelength = []
        for k in columns:
            wavelength.append(float(k))

        x = np.asarray(wavelength)

        newColumns = collections.OrderedDict()
        newColumns["Datetag"] = saveDatetag
        newColumns["Timetag2"] = saveTimetag2
        # Can leave Datetime off at this point

        for i in range(newWavebands.shape[0]):
            # limit to one decimal place
            newColumns[str(round(10*newWavebands[i])/10)] = []

        # Perform interpolation for each timestamp
        for timeIndex in range(len(saveDatetag)):
            values = []

            for k in columns:
                values.append(columns[k][timeIndex])

            y = np.asarray(values)
            #new_y = sp.interpolate.interp1d(x, y)(newWavebands)
            new_y = sp.interpolate.InterpolatedUnivariateSpline(x, y, k=3)(newWavebands)

            for waveIndex in range(newWavebands.shape[0]):
                newColumns[str(round(10*newWavebands[waveIndex])/10)].append(new_y[waveIndex])

        newDS.columns = newColumns
        newDS.columnsToDataset()

    @staticmethod
    def matchWavelengths(node):
        ''' Wavelength matching through interpolation.
            PySciDON interpolated each instrument to a different set of bands.
            Here we use a common set determined by the maximum lowest wavelength
            of all sensors, the minimum highest wavelength, and the interval
            set in the Configuration Window. '''

        print('Interpolating to common wavelengths')
        root = HDFRoot()
        root.copyAttributes(node)

        # Halt user-imposed interval for now as FRM uncertainties do not support this
        #   Instead, use the interval from Es
        # interval = float(ConfigFile.settings["fL1bInterpInterval"])

        sunTrackers = ['SunTracker_SOLARTRACKER','SunTracker_pySAS','SunTracker_DALEC','SunTracker_SoRad']

        newReferenceGroup = root.addGroup("IRRADIANCE")
        newSASGroup = root.addGroup("RADIANCE")
        root.groups.append(node.getGroup("GPS"))
        if node.getGroup("ANCILLARY_METADATA"):
            root.groups.append(node.getGroup("ANCILLARY_METADATA"))

        for robot in sunTrackers:
            if node.getGroup(robot):
                root.groups.append(node.getGroup(robot))
        if node.getGroup("PYROMETER"):
            root.groups.append(node.getGroup("PYROMETER"))
        if node.getGroup("SIXS_MODEL"):
            root.groups.append(node.getGroup("SIXS_MODEL"))

        referenceGroup = node.getGroup("IRRADIANCE")
        sasGroup = node.getGroup("RADIANCE")

        # Propagate L1AQC data
        for gp in node.groups:
            if gp.id.endswith("_L1AQC"):
                newGroup = root.addGroup(gp.id)
                newGroup.copy(gp)
                for ds in newGroup.datasets:
                    if ds == 'DATETIME':
                        del gp.datasets[ds]
                    elif ds.startswith('BACK_') or ds.startswith('CAL_'):
                        continue
                    else:
                        newGroup.datasets[ds].datasetToColumns()

        esData = referenceGroup.getDataset("ES")
        liData = sasGroup.getDataset("LI")
        ltData = sasGroup.getDataset("LT")

        newESData = newReferenceGroup.addDataset("ES")
        newESData.attributes = esData.attributes.copy()
        newLIData = newSASGroup.addDataset("LI")
        newLIData.attributes = esData.attributes.copy()
        newLTData = newSASGroup.addDataset("LT")
        newLTData.attributes = esData.attributes.copy()

        # Es dataset to dictionary
        esData.datasetToColumns()
        columns = esData.columns
        columns.pop("Datetag")
        columns.pop("Timetag2")
        columns.pop("Datetime")
        # Get wavelength values
        esWavelength = []
        for k in columns:
            esWavelength.append(float(k))
        # Determine interpolated wavelength values
        esStart = np.ceil(esWavelength[0])
        esEnd = np.floor(esWavelength[len(esWavelength)-1])

        # No longer using user-input interval
        interval = (esEnd - esStart)/len(esWavelength)

        # Li dataset to dictionary
        liData.datasetToColumns()
        columns = liData.columns
        columns.pop("Datetag")
        columns.pop("Timetag2")
        columns.pop("Datetime")
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
        columns.pop("Datetime")
        # Get wavelength values
        ltWavelength = []
        for k in columns:
            ltWavelength.append(float(k))

        # Determine interpolated wavelength values
        ltStart = np.ceil(ltWavelength[0])
        ltEnd = np.floor(ltWavelength[len(ltWavelength)-1])

        # No extrapolation
        start = max(esStart,liStart,ltStart)
        end = min(esEnd,liEnd,ltEnd)
        newWavebands = np.arange(start, end, interval)

        print('Interpolating Es')
        ProcessL1b_Interp.interpolateWavelength(esData, newESData, newWavebands)
        print('Interpolating Li')
        ProcessL1b_Interp.interpolateWavelength(liData, newLIData, newWavebands)
        print('Interpolating Lt')
        ProcessL1b_Interp.interpolateWavelength(ltData, newLTData, newWavebands)

        return root

    @staticmethod
    def processL1b_Interp(node, fileName):
        '''
        Process time and wavelength interpolation across instruments and ancillary data
        Used for both SeaBird and TriOS L1b
        '''
        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        # node  = Utilities.rootAddDateTime(node)

        root = HDFRoot() # creates a new instance of HDFRoot Class
        root.copyAttributes(node) # Now copy the attributes in from the L1a object
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        root.attributes['WAVE_INTERP'] = str(ConfigFile.settings['fL1bInterpInterval']) + ' nm'

        Utilities.writeLogFileAndPrint(f"ProcessL1b_Interp.processL1b_Interp: {timestr}")

        gpsGroup,pyrGroup,esGroup,liGroup,ltGroup,robotGroup,ancGroup,satmsgGroup,esL1AQCDark=\
            None,None,None,None,None,None,None,None,None
        esL1AQCLight,esL1AQC,liL1AQCDark,liL1AQCLight,liL1AQC,ltL1AQCDark,ltL1AQCLight,ltL1AQC = \
            None,None,None,None,None,None,None,None
        for gp in node.groups:
            if gp.id.startswith("GP"):
                gpsGroup = gp
            if gp.id.startswith("PYROMETER"):
                pyrGroup = gp
            if gp.id.startswith("ES"):
                if gp.id.endswith("_DARK_L1AQC"):
                    esL1AQCDark = gp
                elif gp.id.endswith("_LIGHT_L1AQC"):
                    esL1AQCLight = gp
                elif gp.id.endswith("_L1AQC"):
                    esL1AQC = gp
                else:
                    esGroup = gp
            if gp.id.startswith("LI"):
                if gp.id.endswith("_DARK_L1AQC"):
                    liL1AQCDark = gp
                elif gp.id.endswith("_LIGHT_L1AQC"):
                    liL1AQCLight = gp
                elif gp.id.endswith("_L1AQC"):
                    liL1AQC = gp
                else:
                    liGroup = gp
            if gp.id.startswith("LT"):
                if gp.id.endswith("_DARK_L1AQC"):
                    ltL1AQCDark = gp
                elif gp.id.endswith("_LIGHT_L1AQC"):
                    ltL1AQCLight = gp
                elif gp.id.endswith("_L1AQC"):
                    ltL1AQC = gp
                else:
                    ltGroup = gp           
            if gp.id.startswith("SunTracker"):
                robotGroup = gp
            if gp.id == ("ANCILLARY_METADATA"):
                ancGroup = root.addGroup('ANCILLARY_METADATA')
                ancGroup.copy(gp)
                for ds in ancGroup.datasets:
                    if ds != 'DATETIME':
                        ancGroup.datasets[ds].datasetToColumns()
            if gp.id == "SOLARTRACKER_STATUS":
                satmsgGroup = gp
            if gp.id == "SIXS_MODEL":
                sixS_grp = gp

        # New group scheme combines both radiance sensors in one group
        refGroup = root.addGroup("IRRADIANCE")
        sasGroup = root.addGroup("RADIANCE")

        # Conversion of datasets within groups to move date/timestamps into
        # the data arrays and add datetime column. Also can change dataset name.
        # Places the dataset into the new group.
        ProcessL1b_Interp.convertDataset(esGroup, "ES", refGroup, "ES")
        ProcessL1b_Interp.convertDataset(liGroup, "LI", sasGroup, "LI")
        ProcessL1b_Interp.convertDataset(ltGroup, "LT", sasGroup, "LT")

        if ConfigFile.settings['SensorType'].lower() == 'trios' or\
              ConfigFile.settings['SensorType'].lower() == 'dalec' or\
                  ConfigFile.settings['SensorType'].lower() == 'sorad':
            esL1AQCGroup = root.addGroup('ES_L1AQC')
            esL1AQCGroup.copy(esL1AQC)
            liL1AQCGroup = root.addGroup('LI_L1AQC')
            liL1AQCGroup.copy(liL1AQC)
            ltL1AQCGroup = root.addGroup('LT_L1AQC')
            ltL1AQCGroup.copy(ltL1AQC)
        else:
            esDarkGroup = root.addGroup('ES_DARK_L1AQC')
            esDarkGroup.copy(esL1AQCDark)
            esLightGroup = root.addGroup('ES_LIGHT_L1AQC')
            esLightGroup.copy(esL1AQCLight)
            liDarkGroup = root.addGroup('LI_DARK_L1AQC')
            liDarkGroup.copy(liL1AQCDark)
            liLightGroup = root.addGroup('LI_LIGHT_L1AQC')
            liLightGroup.copy(liL1AQCLight)
            ltDarkGroup = root.addGroup('LT_DARK_L1AQC')
            ltDarkGroup.copy(ltL1AQCDark)
            ltLightGroup = root.addGroup('LT_LIGHT_L1AQC')
            ltLightGroup.copy(ltL1AQCLight)

        newGPSGroup = root.addGroup("GPS")
        if gpsGroup is not None:
            # If Ancillary data have already been interpolated, this group must exist,
            #   but it might be the data derived from Ancillary, and so require special treatment

            # Test whether this group was derived from Ancillary or GPS
            if 'SOURCE' not in gpsGroup.attributes:
                # then interpolation of ancillary has not happened...

                # These are from the raw data, not to be confused with those in the ancillary file
                ProcessL1b_Interp.convertDataset(gpsGroup, "LATPOS", newGPSGroup, "LATITUDE")
                ProcessL1b_Interp.convertDataset(gpsGroup, "LONPOS", newGPSGroup, "LONGITUDE")
                latData = newGPSGroup.getDataset("LATITUDE")
                lonData = newGPSGroup.getDataset("LONGITUDE")
                # Only if the right NMEA data are provided (e.g. with SunTracker)
                if gpsGroup.attributes["CalFileName"].startswith("GPRMC"):
                    ProcessL1b_Interp.convertDataset(gpsGroup, "COURSE", newGPSGroup, "COURSE")
                    ProcessL1b_Interp.convertDataset(gpsGroup, "SPEED", newGPSGroup, "SPEED")
                    courseData = newGPSGroup.getDataset("COURSE")
                    courseData.datasetToColumns()
                    sogData = newGPSGroup.getDataset("SPEED")
                    newGPSGroup.datasets['SPEED'].id="SOG"
                    sogData.datasetToColumns()
            else:
                newGPSGroup.copy(gpsGroup)
                latData = newGPSGroup.getDataset('LATITUDE')
                lonData = newGPSGroup.getDataset("LONGITUDE")
                latData.datasetToColumns()
                lonData.datasetToColumns()
                # Only if the right NMEA data are provided (e.g. with SunTracker)
                if gpsGroup.attributes["CalFileName"].startswith("GPRMC"):
                    courseData = newGPSGroup.getDataset("COURSE")
                    courseData.datasetToColumns()
                    sogData = newGPSGroup.getDataset("SOG")
                    sogData.datasetToColumns()
        else:
            courseData = None
            sogData = None
            latData = ancGroup.getDataset("LATITUDE")
            lonData = ancGroup.getDataset("LONGITUDE")


        if robotGroup is not None:
            newSTGroup = root.addGroup("SunTracker")
            # Required
            ProcessL1b_Interp.convertDataset(robotGroup, "SOLAR_AZ", newSTGroup, "SOLAR_AZ")
            solAzData = newSTGroup.getDataset("SOLAR_AZ")
            ProcessL1b_Interp.convertDataset(robotGroup, "SZA", newSTGroup, "SZA")
            szaData = newSTGroup.getDataset("SZA")
            ProcessL1b_Interp.convertDataset(robotGroup, "REL_AZ", newSTGroup, "REL_AZ")
            relAzData = newSTGroup.getDataset("REL_AZ")
            if robotGroup.id != "SunTracker_sorad":
                ProcessL1b_Interp.convertDataset(robotGroup, "POINTING", newSTGroup, "POINTING")
                pointingData = newSTGroup.getDataset("POINTING")

            # Optional
            # ProcessL1b_Interp.convertDataset(robotGroup, "HEADING", newSTGroup, "HEADING") # Use SATNAV Heading if available (not GPS COURSE)
            if "HUMIDITY" in robotGroup.datasets:
                ProcessL1b_Interp.convertDataset(robotGroup, "HUMIDITY", newSTGroup, "HUMIDITY")
                humidityData = newSTGroup.getDataset("HUMIDITY")
            if "PITCH" in robotGroup.datasets:
                ProcessL1b_Interp.convertDataset(robotGroup, "PITCH", newSTGroup, "PITCH")
                pitchData = newSTGroup.getDataset("PITCH")
            if "ROLL" in robotGroup.datasets:
                ProcessL1b_Interp.convertDataset(robotGroup, "ROLL", newSTGroup, "ROLL")
                rollData = newSTGroup.getDataset("ROLL")
            headingData = None
            if "HEADING" in robotGroup.datasets:
                ProcessL1b_Interp.convertDataset(robotGroup, "HEADING", newSTGroup, "HEADING")
                headingData = newSTGroup.getDataset("HEADING")

        if satmsgGroup is not None:
            # First make sure it's not empty
            satMSG = satmsgGroup.getDataset("MESSAGE")
            if satMSG is not None:
                newSatMSGGroup = root.addGroup("SOLARTRACKER_STATUS")
                # SATMSG (SOLARTRACKER_STATUS) has no date or time, just propogate it as is
                newSatMSG = newSatMSGGroup.addDataset("MESSAGE")
                # newSatMSGGroup["MESSAGE"] = satMSG
                # Copies over the dataset
                for k in satMSG.data.dtype.names:
                    #print("type",type(esData.data[k]))
                    newSatMSG.columns[k] = satMSG.data[k].tolist()
                newSatMSG.columnsToDataset()

        if pyrGroup is not None:
            newPyrGroup = root.addGroup("PYROMETER")
            ProcessL1b_Interp.convertDataset(pyrGroup, "T", newPyrGroup, "T")
            pyrData = newPyrGroup.getDataset("T")

        # convert datetime into sixS group
        sixS_grp = node.getGroup("SIXS_MODEL")
        if sixS_grp is not None:
            sixS_grp_new = root.addGroup("SIXS_MODEL")
            ProcessL1b_Interp.convertDataset(sixS_grp, "sixS_irradiance", sixS_grp_new, "sixS_irradiance")
            ProcessL1b_Interp.convertDataset(sixS_grp, "direct_ratio", sixS_grp_new, "direct_ratio")
            ProcessL1b_Interp.convertDataset(sixS_grp, "diffuse_ratio", sixS_grp_new, "diffuse_ratio")
            ProcessL1b_Interp.convertDataset(sixS_grp, "solar_zenith", sixS_grp_new, "solar_zenith")
        else:
            sixS_grp_new = None

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
            Utilities.writeLogFileAndPrint(f"ES has fewest records - interpolating to ES. This should raise a red flag; {esLength} records")
            interpData = esData
        elif liLength < ltLength:
            Utilities.writeLogFileAndPrint(f"LI has fewest records - interpolating to LI. This should raise a red flag; {liLength} records")
            interpData = liData
        else:
            Utilities.writeLogFileAndPrint(f"LT has fewest records (as expected) - interpolating to LT; {ltLength} records")
            interpData = ltData

        # Confirm that datasets are overlapping in time
        minInterpDT = min(interpData.columns['Datetime'])
        maxInterpDT = max(interpData.columns['Datetime'])
        if min(esData.columns['Datetime']) > maxInterpDT or max(esData.columns['Datetime']) < minInterpDT:
            Utilities.writeLogFileAndPrint("ES data does not overlap interpolation dataset")
            return None
        if min(liData.columns['Datetime']) > maxInterpDT or max(liData.columns['Datetime']) < minInterpDT:
            Utilities.writeLogFileAndPrint("LI data does not overlap interpolation dataset")
            return None
        if min(ltData.columns['Datetime']) > maxInterpDT or max(ltData.columns['Datetime']) < minInterpDT:
            Utilities.writeLogFileAndPrint("LT data does not overlap interpolation dataset")
            return None

        # Perform time interpolation

        # Note that only the specified datasets in each group will be interpolated and
        # carried forward. For radiometers, this means that ancillary metadata such as
        # SPEC_TEMP and THERMAL_RESP will be dropped at L1B and beyond.
        # Required:
        if not ProcessL1b_Interp.interpolateData(esData, interpData, "ES", fileName):
            return None
        if not ProcessL1b_Interp.interpolateData(liData, interpData, "LI", fileName):
            return None
        if not ProcessL1b_Interp.interpolateData(ltData, interpData, "LT", fileName):
            return None

        if robotGroup is not None:
            # Because of the fact that geometries have already been flipped into Ancillary and
            # interpolated prior to applying cal/corrections, some of this is redundant
            # Required:
            if not ProcessL1b_Interp.interpolateData(relAzData, interpData, "REL_AZ", fileName):
                return None
            if not ProcessL1b_Interp.interpolateData(szaData, interpData, "SZA", fileName, latData, lonData):
                return None
            # Optional, but should all be there with the SOLAR TRACKER or pySAS
            ProcessL1b_Interp.interpolateData(solAzData, interpData, "SOLAR_AZ", fileName, latData, lonData)
            if robotGroup.id != "SunTracker_sorad":
                ProcessL1b_Interp.interpolateData(pointingData, interpData, "POINTING", fileName)

            # Optional
            if "HUMIDITY" in robotGroup.datasets:
                ProcessL1b_Interp.interpolateData(humidityData, interpData, "HUMIDITY", fileName)
            if "PITCH" in robotGroup.datasets:
                ProcessL1b_Interp.interpolateData(pitchData, interpData, "PITCH", fileName)
            if "ROLL" in robotGroup.datasets:
                ProcessL1b_Interp.interpolateData(rollData, interpData, "ROLL", fileName)
            if "HEADING" in robotGroup.datasets:
                ProcessL1b_Interp.interpolateData(headingData, interpData, "HEADING", fileName)

        if pyrGroup is not None:
            # Optional:
            ProcessL1b_Interp.interpolateData(pyrData, interpData, "T", fileName)

        # Py6S group interpolation
        if sixS_grp_new is not None:
            sixS_irradiance = sixS_grp_new.getDataset("sixS_irradiance")
            direct_ratio = sixS_grp_new.getDataset("direct_ratio")
            diffuse_ratio = sixS_grp_new.getDataset("diffuse_ratio")
            solar_zenith = sixS_grp_new.getDataset("solar_zenith")
            ProcessL1b_Interp.interpolateData(sixS_irradiance, interpData, "sixS_irradiance", fileName)
            ProcessL1b_Interp.interpolateData(direct_ratio, interpData, "direct_ratio", fileName)
            ProcessL1b_Interp.interpolateData(diffuse_ratio, interpData, "diffuse_ratio", fileName)
            ProcessL1b_Interp.interpolateData(solar_zenith, interpData, "solar_zenith", fileName)

        # Match wavelengths across instruments
        # Calls interpolateWavelengths and matchColumns
        # Includes columnsToDataset for only the radiometry, for remaining groups, see below
        root = ProcessL1b_Interp.matchWavelengths(root)

        # FRM uncertainties
        _unc = node.getGroup('RAW_UNCERTAINTIES')
        if _unc is not None:
            # Copy RAW_UNCERTAINTIES group over without interpolation
            new_unc = root.addGroup('RAW_UNCERTAINTIES')
            new_unc.copy(_unc)
            for ds in new_unc.datasets:
                new_unc.datasets[ds].datasetToColumns()
        else:
            print('No RAW_UNCERTAINTIES found. Moving on...')

        # DATETIME is not supported in HDF5; remove from groups that still have it
        for gp in root.groups:
            for dsName in gp.datasets:
                if dsName == 'DATETIME':
                    del gp.datasets[dsName]
                elif dsName.startswith('BACK_') or dsName.startswith('CAL_'):
                    continue
                else:
                    ds = gp.datasets[dsName]
                    if "Datetime" in ds.columns:
                        ds.columns.pop("Datetime")
                    ds.columnsToDataset() # redundant for radiometry, but harmless

        return root
