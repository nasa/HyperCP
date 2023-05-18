
import collections
import datetime as dt
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
            Required fields relAz, sza, solarAz must be in Ancillary already, or be obtained from SolarTrackers
        '''
        print('Interpolating Ancillary data to radiometry timestamps')
        gpsGroup = None
        STGroup = None
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
            if gp.id.startswith("SOLARTRACKER"):
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
        courseData = None
        sogData = None

        # Required for non-Tracker:
        #   May be acquired from Ancillary or SolarTracker (preferred)
        relAzData = None
        szaData = None
        solAzData = None

        if gpsGroup is not None:
            newGPSGroup.attributes = gpsGroup.attributes.copy()
            # These are from the raw data, not to be confused with those in the ancillary file
            ProcessL1b_Interp.convertDataset(gpsGroup, "LATPOS", newGPSGroup, "LATITUDE")
            ProcessL1b_Interp.convertDataset(gpsGroup, "LONPOS", newGPSGroup, "LONGITUDE")
            latData = newGPSGroup.getDataset("LATITUDE")
            lonData = newGPSGroup.getDataset("LONGITUDE")
            # Only if the right NMEA data are provided (e.g. with SolarTracker)
            if gpsGroup.attributes["CalFileName"].startswith("GPRMC"):
                ProcessL1b_Interp.convertDataset(gpsGroup, "COURSE", newGPSGroup, "COURSE")
                ProcessL1b_Interp.convertDataset(gpsGroup, "SPEED", newGPSGroup, "SPEED")
                courseData = newGPSGroup.getDataset("COURSE")
                courseData.datasetToColumns()
                sogData = newGPSGroup.getDataset("SPEED")
                sogData.datasetToColumns()
                newGPSGroup.datasets['SPEED'].id="SOG"
            newGPSGroup.attributes["SOURCE"] = 'GPS'
        else:
            # These are from the ancillary file; place in GPS
            #   Ignore COURSE and SOG
            ProcessL1b_Interp.convertDataset(ancGroup, "LATITUDE", newGPSGroup, "LATITUDE")
            ProcessL1b_Interp.convertDataset(ancGroup, "LONGITUDE", newGPSGroup, "LONGITUDE")
            latData = newGPSGroup.getDataset("LATITUDE")
            lonData = newGPSGroup.getDataset("LONGITUDE")
            newGPSGroup.attributes["SOURCE"] = 'ANCILLARY'
            newGPSGroup.attributes["CalFileName"] = 'ANCILLARY'


        if STGroup is not None:
            newSTGroup = node.addGroup('ST_TEMP')
            for ds in STGroup.datasets:
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
        # Preferentially from SolarTracker over Ancillary file
        if not relAzData:
            # Here from Ancillary file, not SolarTracker
            if "REL_AZ" in newAncGroup.datasets:
                relAzData = newAncGroup.getDataset("REL_AZ")
        else:
            # Here from SolarTracker; different timestamp from other Ancillary; interpolated below
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
        stationData = None
        headingDataAnc = None
        latDataAnc = None
        lonDataAnc = None
        cloudData = None
        waveData = None
        speedData = None
        # Optional and may reside in SolarTracker or SATTHS group
        pitchAncData = None
        rollAncData = None
        # Optional, assured with MERRA2 models when selected
        saltData = None
        sstData = None
        windData = None
        aodData = None

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
        if "AOD" in newAncGroup.datasets:
            aodData = newAncGroup.getDataset("AOD")
        if "CLOUD" in newAncGroup.datasets:
            cloudData = newAncGroup.getDataset("CLOUD")
        if "WAVE_HT" in newAncGroup.datasets:
            waveData = newAncGroup.getDataset("WAVE_HT")
        if "SPEED_F_W" in newAncGroup.datasets:
            speedData = newAncGroup.getDataset("SPEED_F_W")
        # Allow for the unlikely option that pitch/roll data are included in both the SolarTracker/pySAS and Ancillary datasets
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
            msg = f"ES has fewest records - interpolating to ES. This should raise a red flag; {esLength} records"
            print(msg)
            Utilities.writeLogFile(msg)
            interpData = esData
        elif liLength < ltLength:
            msg = f"LI has fewest records - interpolating to LI. This should raise a red flag; {liLength} records"
            print(msg)
            Utilities.writeLogFile(msg)
            interpData = liData
        else:
            msg = f"LT has fewest records (as expected) - interpolating to LT; {ltLength} records"
            print(msg)
            Utilities.writeLogFile(msg)
            interpData = ltData

        # latData, lonData need to correspond to interData
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
            msg = "Error: REL_AZ missing from Ancillary data, and no Tracker group"
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1b_Interp.interpolateData(newAncGroup.datasets['SOLAR_AZ'], interpData, "SOLAR_AZ", fileName, latData, lonData):
            msg = "Error: SOLAR_AZ missing from Ancillary data, and no Tracker group"
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        if not ProcessL1b_Interp.interpolateData(newAncGroup.datasets['SZA'], interpData, "SZA", fileName, latData, lonData):
            msg = "Error: SZA missing from Ancillary data, and no Tracker group"
            print(msg)
            Utilities.writeLogFile(msg)
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
            ConfigFile.settings["bL1b_InterpPlotTimeInterp"] = 0 # Reserve lat/lon plots for actual GPS, not ancillary file
            ProcessL1b_Interp.interpolateData(latDataAnc, interpData, "LATITUDE", fileName)
            ConfigFile.settings["bL1b_InterpPlotTimeInterp"] = 1
        if lonDataAnc:
            ConfigFile.settings["bL1b_InterpPlotTimeInterp"] = 0
            ProcessL1b_Interp.interpolateData(lonDataAnc, interpData, "LONGITUDE", fileName)
            ConfigFile.settings["bL1b_InterpPlotTimeInterp"] = 1
        if saltData:
            ProcessL1b_Interp.interpolateData(saltData, interpData, "SALINITY", fileName)
        if sstData:
            ProcessL1b_Interp.interpolateData(sstData, interpData, "SST", fileName)
        if windData:
            ProcessL1b_Interp.interpolateData(windData, interpData, "WINDSPEED", fileName)
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
        angList = ['AZIMUTH', 'POINTING', 'REL_AZ', 'HEADING', 'SOLAR_AZ', 'SZA']

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
            xTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in x]
            newXTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in new_x]

            if dataName in angList:
                ''' SOLAR_AZ and SZA are now recalculated for new timestamps rather than interpolated'''
                # if dataName == 'SOLAR_AZ' or dataName == 'SZA':
                #     # newXData.columns[k] = Utilities.interpAngular(xTS, y, newXTS, fill_value="extrapolate")

                # else:
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
            ''' TO DO: This is still broken on Mac. See the hack to fix it here: https://github.com/pandas-dev/pandas/issues/22859'''
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
    def interpolateData(xData, yData, dataName, fileName, latData=None, lonData=None):
        ''' Preforms time interpolation to match xData to yData. xData is the dataset to be
        interpolated, yData is the reference dataset with the times to be interpolated to.'''

        msg = f'Interpolate Data {dataName}'
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

        if Utilities.hasNan(xData):
            frameinfo = getframeinfo(currentframe())
            # print(frameinfo.filename, frameinfo.lineno)
            msg = f'found NaN {frameinfo.lineno}'
            print(msg)
            Utilities.writeLogFile(msg)

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
            msg = f'found NaN {frameinfo.lineno}'
            print(msg)
            Utilities.writeLogFile(msg)
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

        interval = float(ConfigFile.settings["fL1bInterpInterval"])

        newReferenceGroup = root.addGroup("IRRADIANCE")
        newSASGroup = root.addGroup("RADIANCE")
        root.groups.append(node.getGroup("GPS"))
        if node.getGroup("ANCILLARY_METADATA"):
            root.groups.append(node.getGroup("ANCILLARY_METADATA"))
        if node.getGroup("SOLARTRACKER"):
            root.groups.append(node.getGroup("SOLARTRACKER"))
        if node.getGroup("SOLARTRACKER_STATUS"):
            root.groups.append(node.getGroup("SOLARTRACKER_STATUS"))
        if node.getGroup("PYROMETER"):
            root.groups.append(node.getGroup("PYROMETER"))

        referenceGroup = node.getGroup("IRRADIANCE")
        sasGroup = node.getGroup("RADIANCE")

        # Propagate L1AQC data
        for gp in node.groups:
            if gp.id.endswith("_L1AQC"):
                newGroup = root.addGroup(gp.id)
                newGroup.copy(gp)
                for ds in newGroup.datasets:
                    if ds == 'DATETIME':
                        del(gp.datasets[ds])
                    elif ds.startswith('BACK_') or ds.startswith('CAL_'):
                        continue
                    else:
                        newGroup.datasets[ds].datasetToColumns()


        esData = referenceGroup.getDataset("ES")
        liData = sasGroup.getDataset("LI")
        ltData = sasGroup.getDataset("LT")

        newESData = newReferenceGroup.addDataset("ES")
        newLIData = newSASGroup.addDataset("LI")
        newLTData = newSASGroup.addDataset("LT")

        # Es dataset to dictionary
        esData.datasetToColumns()
        # esRaw.datasetToColumns()
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

        # Li dataset to dictionary
        liData.datasetToColumns()
        # liRaw.datasetToColumns()
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
        # ltRaw.datasetToColumns()
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

        msg = f"ProcessL1b_Interp.processL1b_Interp: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        gpsGroup = None
        pyrGroup = None
        esGroup = None
        liGroup = None
        ltGroup = None
        satnavGroup = None
        ancGroup = None # For non-SolarTracker deployments
        satmsgGroup = None
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
            if gp.id == "SOLARTRACKER" or gp.id =="SOLARTRACKER_pySAS":
                satnavGroup = gp # Now labelled SOLARTRACKER at L1B to L1D
            if gp.id == ("ANCILLARY_METADATA"):
                ancGroup = root.addGroup('ANCILLARY_METADATA')
                ancGroup.copy(gp)
                for ds in ancGroup.datasets:
                    if ds != 'DATETIME':
                        ancGroup.datasets[ds].datasetToColumns()


            if gp.id == "SOLARTRACKER_STATUS":
                satmsgGroup = gp

        # New group scheme combines both radiance sensors in one group
        refGroup = root.addGroup("IRRADIANCE")
        sasGroup = root.addGroup("RADIANCE")

        # Conversion of datasets within groups to move date/timestamps into
        # the data arrays and add datetime column. Also can change dataset name.
        # Places the dataset into the new group.
        ProcessL1b_Interp.convertDataset(esGroup, "ES", refGroup, "ES")
        ProcessL1b_Interp.convertDataset(liGroup, "LI", sasGroup, "LI")
        ProcessL1b_Interp.convertDataset(ltGroup, "LT", sasGroup, "LT")
        if ConfigFile.settings['SensorType'].lower() == 'trios':
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
                # Only if the right NMEA data are provided (e.g. with SolarTracker)
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
                # Only if the right NMEA data are provided (e.g. with SolarTracker)
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


        if satnavGroup is not None:
            newSTGroup = root.addGroup("SOLARTRACKER")
            # Required
            ProcessL1b_Interp.convertDataset(satnavGroup, "SOLAR_AZ", newSTGroup, "SOLAR_AZ")
            solAzData = newSTGroup.getDataset("SOLAR_AZ")
            ProcessL1b_Interp.convertDataset(satnavGroup, "SZA", newSTGroup, "SZA")
            szaData = newSTGroup.getDataset("SZA")
            ProcessL1b_Interp.convertDataset(satnavGroup, "REL_AZ", newSTGroup, "REL_AZ")
            relAzData = newSTGroup.getDataset("REL_AZ")
            ProcessL1b_Interp.convertDataset(satnavGroup, "POINTING", newSTGroup, "POINTING")
            pointingData = newSTGroup.getDataset("POINTING")

            # Optional
            # ProcessL1b_Interp.convertDataset(satnavGroup, "HEADING", newSTGroup, "HEADING") # Use SATNAV Heading if available (not GPS COURSE)
            if "HUMIDITY" in satnavGroup.datasets:
                ProcessL1b_Interp.convertDataset(satnavGroup, "HUMIDITY", newSTGroup, "HUMIDITY")
                humidityData = newSTGroup.getDataset("HUMIDITY")
            if "PITCH" in satnavGroup.datasets:
                ProcessL1b_Interp.convertDataset(satnavGroup, "PITCH", newSTGroup, "PITCH")
                pitchData = newSTGroup.getDataset("PITCH")
            if "ROLL" in satnavGroup.datasets:
                ProcessL1b_Interp.convertDataset(satnavGroup, "ROLL", newSTGroup, "ROLL")
                rollData = newSTGroup.getDataset("ROLL")
            headingData = None
            if "HEADING" in satnavGroup.datasets:
                ProcessL1b_Interp.convertDataset(satnavGroup, "HEADING", newSTGroup, "HEADING")
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
            msg = f"ES has fewest records - interpolating to ES. This should raise a red flag; {esLength} records"
            print(msg)
            Utilities.writeLogFile(msg)
            interpData = esData
        elif liLength < ltLength:
            msg = f"LI has fewest records - interpolating to LI. This should raise a red flag; {liLength} records"
            print(msg)
            Utilities.writeLogFile(msg)
            interpData = liData
        else:
            msg = f"LT has fewest records (as expected) - interpolating to LT; {ltLength} records"
            print(msg)
            Utilities.writeLogFile(msg)
            interpData = ltData

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

        # # Optional:
        # '''
        # The only way to enter is if we had a GPS course and speed, in which case it's already inter'd.'''
        # if courseData:
                # ProcessL1b_Interp.interpolateData(courseData, interpData, "COURSE", fileName) # COG (not heading), presumably?
        # if sogData:
        #         ProcessL1b_Interp.interpolateData(sogData, interpData, "SOG", fileName)

        if satnavGroup is not None:
            # Required:
            if not ProcessL1b_Interp.interpolateData(relAzData, interpData, "REL_AZ", fileName):
                return None
            if not ProcessL1b_Interp.interpolateData(szaData, interpData, "SZA", fileName, latData, lonData):
                return None
            # Optional, but should all be there with the SOLAR TRACKER or pySAS
            ProcessL1b_Interp.interpolateData(solAzData, interpData, "SOLAR_AZ", fileName, latData, lonData)
            ProcessL1b_Interp.interpolateData(pointingData, interpData, "POINTING", fileName)

            # Optional
            if "HUMIDITY" in satnavGroup.datasets:
                ProcessL1b_Interp.interpolateData(humidityData, interpData, "HUMIDITY", fileName)
            if "PITCH" in satnavGroup.datasets:
                ProcessL1b_Interp.interpolateData(pitchData, interpData, "PITCH", fileName)
            if "ROLL" in satnavGroup.datasets:
                ProcessL1b_Interp.interpolateData(rollData, interpData, "ROLL", fileName)
            if "HEADING" in satnavGroup.datasets:
                ProcessL1b_Interp.interpolateData(headingData, interpData, "HEADING", fileName)

        if pyrGroup is not None:
            # Optional:
            ProcessL1b_Interp.interpolateData(pyrData, interpData, "T", fileName)

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
                    del(gp.datasets[dsName])
                elif dsName.startswith('BACK_') or dsName.startswith('CAL_'):
                    continue
                else:
                    ds = gp.datasets[dsName]
                    if "Datetime" in ds.columns:
                        ds.columns.pop("Datetime")
                    ds.columnsToDataset() # redundant for radiometry, but harmless

        return root
