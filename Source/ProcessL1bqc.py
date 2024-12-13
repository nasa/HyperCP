''' Process L1B to L1BQC '''
import numpy as np
import scipy as sp

from Source.MainConfig import MainConfig
from Source.Utilities import Utilities
from Source.ConfigFile import ConfigFile


class ProcessL1bqc:
    '''Process L1BQC'''

    @staticmethod
    def interpolateColumn(columns, wl):
        ''' Interpolate wavebands to estimate a single, unsampled waveband. This allows for QC filters
            designed for nominal bands. '''
        #print("interpolateColumn")
        # Values to return
        return_y = []

        # Column to interpolate to
        new_x = [wl]

        # Get wavelength values
        wavelength = []
        for k in columns:
            #print(k)
            wavelength.append(float(k))
        x = np.asarray(wavelength)

        # get the length of a column
        num = len(list(columns.values())[0])

        # Perform interpolation for each row
        for i in range(num):
            values = []
            for k in columns:
                #print("b")
                values.append(columns[k][i])
            y = np.asarray(values)

            new_y = sp.interpolate.interp1d(x, y)(new_x)
            return_y.append(new_y[0])

        return return_y


    @staticmethod
    def specQualityCheck(group, inFilePath, station=None):
        ''' Perform spectral filtering
        Calculate the STD of the normalized (at some max value) spectra in the file.
        Then test each normalized spectrum against the file average and STD and negatives (within the spectral range).
        Plot results'''

        # This is the range upon which the spectral filter is applied (and plotted)
        # It goes up to 900 to include bands used in NIR correction
        fRange = [350, 900]

        badTimes = []
        if group.id == 'IRRADIANCE':
            Data = group.getDataset("ES")
            timeStamp = group.getDataset("ES").data["Datetime"]
            badTimes = Utilities.specFilter(inFilePath, Data, timeStamp, station, filterRange=fRange,\
                filterFactor=ConfigFile.settings["fL1bqcSpecFilterEs"], rType='Es')
            msg = f'{len(np.unique(badTimes))/len(timeStamp)*100:.1f}% of Es data flagged'
            print(msg)
            Utilities.writeLogFile(msg)
        else:
            Data = group.getDataset("LI")
            timeStamp = group.getDataset("LI").data["Datetime"]
            badTimes1 = Utilities.specFilter(inFilePath, Data, timeStamp, station, filterRange=fRange,\
                filterFactor=ConfigFile.settings["fL1bqcSpecFilterLi"], rType='Li')
            msg = f'{len(np.unique(badTimes1))/len(timeStamp)*100:.1f}% of Li data flagged'
            print(msg)
            Utilities.writeLogFile(msg)

            Data = group.getDataset("LT")
            timeStamp = group.getDataset("LT").data["Datetime"]
            badTimes2 = Utilities.specFilter(inFilePath, Data, timeStamp, station, filterRange=fRange,\
                filterFactor=ConfigFile.settings["fL1bqcSpecFilterLt"], rType='Lt')
            msg = f'{len(np.unique(badTimes2))/len(timeStamp)*100:.1f}% of Lt data flagged'
            print(msg)
            Utilities.writeLogFile(msg)

            badTimes = np.append(badTimes1,badTimes2, axis=0)

        if len(badTimes) == 0:
            badTimes = None
        return badTimes


    @staticmethod
    def ltQuality(sasGroup):
        ''' Perform Lt Quality checking '''

        ltData = sasGroup.getDataset("LT")
        ltData.datasetToColumns()
        ltColumns = ltData.columns
        # These get popped off the columns, but restored when filterData runs datasetToColumns
        ltColumns.pop('Datetag')
        ltColumns.pop('Timetag2')
        ltDatetime = ltColumns.pop('Datetime')

        badTimes = []
        for indx, dateTime in enumerate(ltDatetime):
            # If the Lt spectrum in the NIR is brighter than in the UVA, something is very wrong
            UVA = [350,400]
            NIR = [780,850]
            ltUVA = []
            ltNIR = []
            for wave in ltColumns:
                if float(wave) > UVA[0] and float(wave) < UVA[1]:
                    ltUVA.append(ltColumns[wave][indx])
                elif float(wave) > NIR[0] and float(wave) < NIR[1]:
                    ltNIR.append(ltColumns[wave][indx])

            if np.nanmean(ltUVA) < np.nanmean(ltNIR):
                badTimes.append(dateTime)

        badTimes = np.unique(badTimes)
        # Duplicate each element to a list of two elements in a list
        # BUG: This is not optimal as it creates one badTimes record for each bad
        #    timestamp, rather than span of timestamps from badtimes[i][0] to badtimes[i][1]
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3)
        msg = f'{len(np.unique(badTimes))/len(ltDatetime)*100:.1f}% of spectra flagged'
        print(msg)
        Utilities.writeLogFile(msg)

        if len(badTimes) == 0:
            badTimes = None
            # In case filterData does not need to be run:
            ltData.datasetToColumns()
        return badTimes

    @staticmethod
    def metQualityCheck(refGroup, sasGroup, py6sGroup, ancGroup):
        ''' Perform meteorological quality control '''

        esFlag = float(ConfigFile.settings["fL1bqcSignificantEsFlag"])
        dawnDuskFlag = float(ConfigFile.settings["fL1bqcDawnDuskFlag"])
        humidityFlag = float(ConfigFile.settings["fL1bqcRainfallHumidityFlag"])
        cloudFLAG = float(ConfigFile.settings["fL1bqcCloudFlag"]) # Not to be confused with cloudFlag...

        esData = refGroup.getDataset("ES")
        esData.datasetToColumns()
        esColumns = esData.columns

        esColumns.pop('Datetag')
        esColumns.pop('Timetag2')
        esTime = esColumns.pop('Datetime')

        liData = sasGroup.getDataset("LI")
        liData.datasetToColumns()
        liColumns = liData.columns
        liColumns.pop('Datetag')
        liColumns.pop('Timetag2')
        liColumns.pop('Datetime')

        ltData = sasGroup.getDataset("LT")
        ltData.datasetToColumns()
        ltColumns = ltData.columns
        ltColumns.pop('Datetag')
        ltColumns.pop('Timetag2')
        ltColumns.pop('Datetime')

        li750 = ProcessL1bqc.interpolateColumn(liColumns, 750.0)
        es370 = ProcessL1bqc.interpolateColumn(esColumns, 370.0)
        es470 = ProcessL1bqc.interpolateColumn(esColumns, 470.0)
        es480 = ProcessL1bqc.interpolateColumn(esColumns, 480.0)
        es680 = ProcessL1bqc.interpolateColumn(esColumns, 680.0)
        es720 = ProcessL1bqc.interpolateColumn(esColumns, 720.0)
        es750 = ProcessL1bqc.interpolateColumn(esColumns, 750.0)
        badTimes = []

        flags1 = ancGroup.datasets['MET_FLAGS'].columns['Flag1']
        flags2 = ancGroup.datasets['MET_FLAGS'].columns['Flag2']
        flags3 = ancGroup.datasets['MET_FLAGS'].columns['Flag3']
        flags4 = ancGroup.datasets['MET_FLAGS'].columns['Flag4']
        flags5 = ancGroup.datasets['MET_FLAGS'].columns['Flag5']

        for indx, dateTime in enumerate(esTime):
            # Flag spectra affected by clouds (Compare with 6S Es). Placeholder while under development
            # Need to propagate 6S even in Default and Class for this to work
            if py6sGroup is not None:
                if li750[indx]/es750[indx] >= cloudFLAG:
                    badTimes.append(dateTime)
                    flags1[indx] = True

            # Flag spectra affected by clouds (Ruddick 2006, IOCCG Protocols).
            if li750[indx]/es750[indx] >= cloudFLAG:
                badTimes.append(dateTime)
                flags2[indx] = True

            # Flag for significant es
            # Wernand 2002
            if es480[indx] < esFlag:
                badTimes.append(dateTime)
                flags3[indx] = True

            # Flag spectra affected by dawn/dusk radiation
            # Wernand 2002
            #v = esXSlice["470.0"][0] / esXSlice["610.0"][0] # Fix 610 -> 680
            if es470[indx]/es680[indx] < dawnDuskFlag:
                badTimes.append(dateTime)
                flags4[indx] = True

            # Flag spectra affected by rainfall and high humidity
            # Wernand 2002 (940/370), Garaba et al. 2012 also uses Es(940/370), presumably 720 was developed by Wang...???
            # NOTE: Follow up on the source of this flag
            if es720[indx]/es370[indx] < humidityFlag:
                badTimes.append(dateTime)
                flags5[indx] = True

        badTimes = np.unique(badTimes)
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) # Duplicates each element to a list of two elements in a list
        msg = f'{len(np.unique(badTimes))/len(esTime)*100:.1f}% of spectra flagged (not filtered)'
        print(msg)
        Utilities.writeLogFile(msg)

        # Restore timestamps to columns (since it's not going to filterData, where it otherwise happens)
        esData.datasetToColumns()
        liData.datasetToColumns()
        ltData.datasetToColumns()
        if len(badTimes) == 0:
            badTimes = None
        return badTimes

    @staticmethod
    def QC(node):
        ''' Add model data. QC for wind, Lt, SZA, spectral outliers, and met filters'''
        print("Add model data. QC for wind, Lt, SZA, spectral outliers, and met filters")

        referenceGroup = node.getGroup("IRRADIANCE")
        sasGroup = node.getGroup("RADIANCE")
        gpsGroup = node.getGroup('GPS')
        if ConfigFile.settings['SensorType'].lower() == 'seabird':
            esDarkGroup = node.getGroup('ES_DARK_L1AQC')
            esLightGroup = node.getGroup('ES_LIGHT_L1AQC')
            ltDarkGroup = node.getGroup('LT_DARK_L1AQC')
            ltLightGroup = node.getGroup('LT_LIGHT_L1AQC')
            liDarkGroup = node.getGroup('LI_DARK_L1AQC')
            liLightGroup = node.getGroup('LI_LIGHT_L1AQC')
        elif ConfigFile.settings['SensorType'].lower() == 'trios':
            esGroup = node.getGroup('ES_L1AQC')
            liGroup = node.getGroup('LI_L1AQC')
            ltGroup = node.getGroup('LT_L1AQC')        

        satnavGroup = None
        ancGroup = None
        pyrGroup = None
        py6sGroup = None
        for gp in node.groups:
            if gp.id.startswith("SOLARTRACKER"):
                if gp.id != "SOLARTRACKER_STATUS":
                    satnavGroup = gp
            if gp.id.startswith("ANCILLARY"):
                ancGroup = gp
                ancGroup.id = "ANCILLARY" # shift back from ANCILLARY_METADATA
            if gp.id.startswith("PYROMETER"):
                pyrGroup = gp
            if gp.id.startswith("PY6S"):
                py6sGroup = gp


        # # Regardless of whether SolarTracker/pySAS is used, Ancillary data will have been already been
        # # interpolated in L1B as long as the ancillary file was read in at L1AQC. Regardless, these need
        # # to have model data and/or default values incorporated.

        # # If GMAO modeled data is selected in ConfigWindow, and an ancillary field data file
        # # is provided in Main Window, then use the model data to fill in gaps in the field
        # # record. Otherwise, use the selected default values from ConfigWindow

        # # This step is only necessary for the ancillary datasets that REQUIRE
        # # either field or GMAO or GUI default values. The remaining ancillary data
        # # are culled from datasets in groups in L1B
        # ProcessL1bqc.includeModelDefaults(ancGroup, modRoot)

        # Shift metadata into the ANCILLARY group as needed (i.e. from GPS and tracker)
        #
        # GPS Group
        # These have TT2/Datetag incorporated in arrays
        # Change their column names from NONE to something appropriate to be consistent in
        # ancillary group going forward.
        # Replace metadata lat/long with GPS lat/long, in case the former is from the ancillary file
        ancGroup.datasets['LATITUDE'] = gpsGroup.getDataset('LATITUDE')
        ancGroup.datasets['LATITUDE'].changeColName('NONE','LATITUDE')
        ancGroup.datasets['LONGITUDE'] = gpsGroup.getDataset('LONGITUDE')
        ancGroup.datasets['LONGITUDE'].changeColName('NONE','LONGITUDE')

        # Take Course (presumably COG) and SOG preferentially from GPS
        if 'COURSE' in gpsGroup.datasets:
            # These have TT2/Datetag incorporated in arrays
            ancGroup.addDataset('COURSE')
            ancGroup.datasets['COURSE'] = gpsGroup.getDataset('COURSE')
            ancGroup.datasets['COURSE'].changeColName('TRUE','COURSE')
        if 'SOG' in gpsGroup.datasets:
            ancGroup.addDataset('SOG')
            ancGroup.datasets['SOG'] = gpsGroup.getDataset('SOG')
            ancGroup.datasets['SOG'].changeColName('NONE','SOG')

        # Finished with GPS group. Delete
        for gp in node.groups:
            if gp.id == gpsGroup.id:
                node.removeGroup(gp)

        if 'SPEED_F_W' in ancGroup.datasets:
            ancGroup.datasets['SPEED_F_W'].changeColName('NONE','SPEED_F_W')

        if satnavGroup is not None:
            # Take REL_AZ, SZA, SOLAR_AZ, HEADING, POINTING, HUMIDITY, PITCH and ROLL
            #  preferentially from tracker data. Some of these might change as
            #  new instruments are added that don't fit the SolarTracker/pySAS
            #  robot model.
            #
            # Keep in mind these may overwrite ancillary data from outside sources.
            ancGroup.addDataset('SZA')
            ancGroup.datasets['SZA'] = satnavGroup.getDataset('SZA')
            ancGroup.datasets['SZA'].changeColName('NONE','SZA')
            ancGroup.addDataset('SOLAR_AZ')
            ancGroup.datasets['SOLAR_AZ'] = satnavGroup.getDataset('SOLAR_AZ')
            ancGroup.datasets['SOLAR_AZ'].changeColName('NONE','SOLAR_AZ')
            ancGroup.addDataset('REL_AZ')
            ancGroup.datasets['REL_AZ'] = satnavGroup.getDataset('REL_AZ')
            ancGroup.datasets['REL_AZ'].changeColName('NONE','REL_AZ')
            # ancGroup.datasets['REL_AZ'].datasetToColumns()
            if 'HEADING' in satnavGroup.datasets:
                ancGroup.addDataset('HEADING')
                ancGroup.datasets['HEADING'] = satnavGroup.getDataset('HEADING')
            if 'POINTING' in satnavGroup.datasets:
                ancGroup.addDataset('POINTING')
                ancGroup.datasets['POINTING'] = satnavGroup.getDataset('POINTING')
                ancGroup.datasets['POINTING'].changeColName('ROTATOR','POINTING')
            if 'HUMIDITY' in satnavGroup.datasets:
                ancGroup.addDataset('HUMIDITY')
                ancGroup.datasets['HUMIDITY'] = satnavGroup.getDataset('HUMIDITY')
            if 'PITCH' in satnavGroup.datasets:
                ancGroup.addDataset('PITCH')
                ancGroup.datasets['PITCH'] = satnavGroup.getDataset('PITCH')
                ancGroup.datasets['PITCH'].changeColName('SAS','PITCH')
            if 'ROLL' in satnavGroup.datasets:
                ancGroup.addDataset('ROLL')
                ancGroup.datasets['ROLL'] = satnavGroup.getDataset('ROLL')
                ancGroup.datasets['ROLL'].changeColName('SAS','ROLL')

            # Finished with SOLARTRACKER/pySAS group. Delete
            for gp in node.groups:
                if gp.id == satnavGroup.id:
                    node.removeGroup(gp)

        # ancGroup.datasets['SZA'].changeColName('NONE','SZA') # In case SZA was ancillary
        if 'SZA'in ancGroup.datasets:
            ancGroup.datasets['SZA'].changeColName('NONE','SZA')
        if 'SOLAR_AZ'in ancGroup.datasets:
            ancGroup.datasets['SOLAR_AZ'].changeColName('NONE','SOLAR_AZ')
        if 'REL_AZ'in ancGroup.datasets:
            ancGroup.datasets['REL_AZ'].changeColName('NONE','REL_AZ')
        if 'HUMIDITY' in ancGroup.datasets:
            ancGroup.datasets['HUMIDITY'].changeColName('NONE','HUMIDITY')
        if 'CLOUD' in ancGroup.datasets:
            ancGroup.datasets['CLOUD'].changeColName('NONE','CLOUD')
        if 'PITCH' in ancGroup.datasets:
            ancGroup.datasets['PITCH'].changeColName('NONE','PITCH')
        if 'ROLL' in ancGroup.datasets:
            ancGroup.datasets['ROLL'].changeColName('NONE','ROLL')
        if 'STATION' in ancGroup.datasets:
            ancGroup.datasets['STATION'].changeColName('NONE','STATION')
        if 'WAVE_HT' in ancGroup.datasets:
            ancGroup.datasets['WAVE_HT'].changeColName('NONE','WAVE_HT')
        if 'SALINITY'in ancGroup.datasets:
            ancGroup.datasets['SALINITY'].changeColName('NONE','SALINITY')
        if 'WINDSPEED'in ancGroup.datasets:
            ancGroup.datasets['WINDSPEED'].changeColName('NONE','WINDSPEED')
        if 'SST'in ancGroup.datasets:
            ancGroup.datasets['SST'].changeColName('NONE','SST')

        if pyrGroup is not None:
            #PYROMETER
            ancGroup.datasets['SST_IR'] = pyrGroup.getDataset("T")
            ancGroup.datasets['SST_IR'].datasetToColumns()
            ancGroup.datasets['SST_IR'].changeColName('IR','SST_IR')

            # Finished with PYROMETER group. Delete
            for gp in node.groups:
                if gp.id == pyrGroup.id:
                    node.removeGroup(gp)

        enableMetQualityCheck = ConfigFile.settings["bL1bqcEnableQualityFlags"]
        if enableMetQualityCheck:
            ancGroup.addDataset('MET_FLAGS')
            ancGroup.datasets['MET_FLAGS'].columns['Datetag'] = ancGroup.datasets['LATITUDE'].columns['Datetag']
            ancGroup.datasets['MET_FLAGS'].columns['Timetag2'] = ancGroup.datasets['LATITUDE'].columns['Timetag2']
            lenAnc = len(ancGroup.datasets['MET_FLAGS'].columns['Timetag2'])
            ancGroup.datasets['MET_FLAGS'].columns['Flag1'] = [False for i in range(lenAnc)]
            ancGroup.datasets['MET_FLAGS'].columns['Flag2'] = [False for i in range(lenAnc)]
            ancGroup.datasets['MET_FLAGS'].columns['Flag3'] = [False for i in range(lenAnc)]
            ancGroup.datasets['MET_FLAGS'].columns['Flag4'] = [False for i in range(lenAnc)]
            ancGroup.datasets['MET_FLAGS'].columns['Flag5'] = [False for i in range(lenAnc)]


        # At this stage, all datasets in all groups of node have Timetag2
        #     and Datetag incorporated into data arrays. Calculate and add
        #     Datetime to each data array.
        Utilities.rootAddDateTimeCol(node)


        #################################################################################

        #   Filter the spectra from the entire collection before slicing the intervals at L2

        ##################################################################################

        # Lt Quality Filtering; anomalous elevation in the NIR
        if ConfigFile.settings["bL1bqcLtUVNIR"]:
            msg = "Applying Lt(NIR)>Lt(UV) quality filtering to eliminate spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            # This is not well optimized for large files...
            badTimes = ProcessL1bqc.ltQuality(sasGroup)

            # NOTE: There is a problem for individual timestamps in badTimes that will not match Darks from L1AQC data
            #   Need to convert singleton start-stop records in badTimes to ranges of time to capture Darks in L1AQC data

            if badTimes is not None:
                print('Removing records... Can be slow for large files')
                check = Utilities.filterData(referenceGroup, badTimes)
                # check is now fraction removed
                #   I.e., if >99% of the Es spectra from this entire file were remove, abort this file
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
                Utilities.filterData(sasGroup, badTimes)
                Utilities.filterData(ancGroup, badTimes)

                # Filter L1AQC data for L1BQC criteria. badTimes start/stop
                # are used to bracket the same spectral collections, though it
                # will involve a difference number/percentage of the datasets.
                if ConfigFile.settings['SensorType'].lower() == 'seabird':
                    check = []
                    check.append(Utilities.filterData(esDarkGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(esLightGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(liDarkGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(liLightGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(ltDarkGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(ltLightGroup,badTimes,'L1AQC'))
                    if any(np.array(check) > 0.99):
                        msg = "Too few spectra remaining. Abort."
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return False
                elif ConfigFile.settings['SensorType'].lower() == 'trios':
                    Utilities.filterData(esGroup,badTimes,'L1AQC')
                    Utilities.filterData(liGroup,badTimes,'L1AQC')
                    Utilities.filterData(ltGroup,badTimes,'L1AQC')

                if py6sGroup is not None:
                    Utilities.filterData(py6sGroup,badTimes)


        # Filter low SZAs and high winds after interpolating model/ancillary data
        maxWind = float(ConfigFile.settings["fL1bqcMaxWind"])

        wind = ancGroup.getDataset("WINDSPEED").data["WINDSPEED"]
        timeStamp = ancGroup.datasets["WINDSPEED"].columns["Datetime"]

        badTimes = None
        i=0
        start = -1
        stop = []
        for index, _ in enumerate(wind):
            if wind[index] > maxWind:
                i += 1
                if start == -1:
                    msg =f'High Wind: {round(wind[index])}'
                    Utilities.writeLogFile(msg)
                    start = index
                stop = index
                if badTimes is None:
                    badTimes = []
            else:
                if start != -1:
                    msg = f'Passed. Wind: {round(wind[index])}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    startstop = [timeStamp[start],timeStamp[stop]]
                    msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
                    # print(msg)
                    Utilities.writeLogFile(msg)
                    badTimes.append(startstop)
                    start = -1
            end_index = index
        msg = f'Percentage of data out of Wind limits: {round(100*i/len(timeStamp))} %'
        print(msg)
        Utilities.writeLogFile(msg)

        if start != -1 and stop == end_index: # Records from a mid-point to the end are bad
            startstop = [timeStamp[start],timeStamp[stop]]
            msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
            # print(msg)
            Utilities.writeLogFile(msg)
            if badTimes is None: # only one set of records
                badTimes = [startstop]
            else:
                badTimes.append(startstop)

        if start==0 and stop==end_index: # All records are bad
            return False

        if badTimes is not None and len(badTimes) != 0:
            print('Removing records...')
            check = Utilities.filterData(referenceGroup, badTimes)
            if check > 0.99:
                msg = "Too few spectra remaining. Abort."
                print(msg)
                Utilities.writeLogFile(msg)
                return False
            Utilities.filterData(sasGroup, badTimes)
            Utilities.filterData(ancGroup, badTimes)
            # Filter L1AQC data for L1BQC criteria
            if ConfigFile.settings['SensorType'].lower() == 'seabird':
                check = []
                check.append(Utilities.filterData(esDarkGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(esLightGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(liDarkGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(liLightGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(ltDarkGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(ltLightGroup,badTimes,'L1AQC'))
                if any(np.array(check) > 0.99):
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
            elif ConfigFile.settings['SensorType'].lower() == 'trios':
                Utilities.filterData(esGroup,badTimes,'L1AQC')
                Utilities.filterData(liGroup,badTimes,'L1AQC')
                Utilities.filterData(ltGroup,badTimes,'L1AQC')
            if py6sGroup is not None:
                Utilities.filterData(py6sGroup,badTimes)


        # Filter SZAs
        SZAMin = float(ConfigFile.settings["fL1bqcSZAMin"])
        SZAMax = float(ConfigFile.settings["fL1bqcSZAMax"])

        # SZA will be in ancGroup at this point regardless of whether it is from Ancillary or Tracker
        SZA = ancGroup.datasets["SZA"].columns["SZA"]
        # SZA = ancGroup.datasets["SZA"].columns["NONE"]
        timeStamp = ancGroup.datasets["SZA"].columns["Datetime"]

        badTimes = None
        i=0
        start = -1
        stop = []
        for index, _ in enumerate(SZA):
            if SZA[index] < SZAMin or SZA[index] > SZAMax:
                i += 1
                if start == -1:
                    msg =f'Low SZA. SZA: {round(SZA[index])}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    start = index
                stop = index
                if badTimes is None:
                    badTimes = []
            else:
                if start != -1:
                    msg = f'Passed. SZA: {round(SZA[index])}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    startstop = [timeStamp[start],timeStamp[stop]]
                    msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
                    # print(msg)
                    Utilities.writeLogFile(msg)
                    badTimes.append(startstop)
                    start = -1
            end_index = index
        msg = f'Percentage of data out of SZA limits: {round(100*i/len(timeStamp))} %'
        print(msg)
        Utilities.writeLogFile(msg)

        if start != -1 and stop == end_index: # Records from a mid-point to the end are bad
            startstop = [timeStamp[start],timeStamp[stop]]
            msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
            # print(msg)
            Utilities.writeLogFile(msg)
            if badTimes is None: # only one set of records
                badTimes = [startstop]
            else:
                badTimes.append(startstop)

        if start==0 and stop==end_index: # All records are bad
            return False

        if badTimes is not None and len(badTimes) != 0:
            print('Removing records...')
            check = Utilities.filterData(referenceGroup, badTimes)
            if check > 0.99:
                msg = "Too few spectra remaining. Abort."
                print(msg)
                Utilities.writeLogFile(msg)
                return False
            Utilities.filterData(sasGroup, badTimes)
            Utilities.filterData(ancGroup, badTimes)
            # Filter L1AQC data for L1BQC criteria
            if ConfigFile.settings['SensorType'].lower() == 'seabird':
                check = []
                check.append(Utilities.filterData(esDarkGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(esLightGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(liDarkGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(liLightGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(ltDarkGroup,badTimes,'L1AQC'))
                check.append(Utilities.filterData(ltLightGroup,badTimes,'L1AQC'))
                if any(np.array(check) > 0.99):
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
            elif ConfigFile.settings['SensorType'].lower() == 'trios':
                Utilities.filterData(esGroup,badTimes,'L1AQC')
                Utilities.filterData(liGroup,badTimes,'L1AQC')
                Utilities.filterData(ltGroup,badTimes,'L1AQC')
            if py6sGroup is not None:
                    Utilities.filterData(py6sGroup,badTimes)

       # Spectral Outlier Filter
        enableSpecQualityCheck = ConfigFile.settings['bL1bqcEnableSpecQualityCheck']
        if enableSpecQualityCheck:
            badTimes = None
            msg = "Applying spectral filtering to eliminate noisy spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            inFilePath = node.attributes['In_Filepath']
            badTimes1 = ProcessL1bqc.specQualityCheck(referenceGroup, inFilePath)
            badTimes2 = ProcessL1bqc.specQualityCheck(sasGroup, inFilePath)
            if badTimes1 is not None and badTimes2 is not None:
                badTimes = np.append(badTimes1,badTimes2, axis=0)
            elif badTimes1 is not None:
                badTimes = badTimes1
            elif badTimes2 is not None:
                badTimes = badTimes2

            if badTimes is not None:
                msg = "Removing spectra from combined flags."
                print(msg)
                Utilities.writeLogFile(msg)
                check = Utilities.filterData(referenceGroup, badTimes)
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
                check = Utilities.filterData(sasGroup, badTimes)
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
                check = Utilities.filterData(ancGroup, badTimes)
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False

                if py6sGroup is not None:
                    Utilities.filterData(py6sGroup,badTimes)

                # Filter L1AQC data for L1BQC criteria
                if ConfigFile.settings['SensorType'].lower() == 'seabird':
                    check = []
                    check.append(Utilities.filterData(esDarkGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(esLightGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(liDarkGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(liLightGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(ltDarkGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(ltLightGroup,badTimes,'L1AQC'))
                    if any(np.array(check) > 0.99):
                        msg = "Too few spectra remaining. Abort."
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return False
                elif ConfigFile.settings['SensorType'].lower() == 'trios':
                    Utilities.filterData(esGroup,badTimes,'L1AQC')
                    Utilities.filterData(liGroup,badTimes,'L1AQC')
                    Utilities.filterData(ltGroup,badTimes,'L1AQC')

        # Next apply the Meteorological FLAGGING prior to slicing
        # esData = referenceGroup.getDataset("ES")
        if enableMetQualityCheck:
            # msg = "Applying meteorological filtering to eliminate spectra."
            msg = "Applying meteorological flags. Met flags are NOT used to eliminate spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            badTimes = ProcessL1bqc.metQualityCheck(referenceGroup, sasGroup, py6sGroup, ancGroup)

        # NOTE: This is not finalized and needs a ConfigFile.setting #########################################
        ConfigFile.settings['bL2filterMetFlags'] = 0
        if ConfigFile.settings['bL2filterMetFlags'] == 1:
            # Placeholder to filter out based on Met Flags
            metFlags = ancGroup.datasets['MET_FLAGS']
            AncDatetime = metFlags.columns['Datetime']
            Flag3 = metFlags.columns['Flag3']

            badTimes = []
            for indx, dateTime in enumerate(AncDatetime):
                if Flag3[indx]:
                    badTimes.append(dateTime)

            badTimes = np.unique(badTimes)
            # Duplicate each element to a list of two elements in a list
            badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3)
            # msg = f'{len(np.unique(badTimes))/len(AncDatetime)*100:.1f}% of spectra flagged'

            if badTimes is not None:
                msg = "Removing spectra from Met flags. ######################### Hard-coded override for Flag3"
                print(msg)
                Utilities.writeLogFile(msg)
                check = Utilities.filterData(referenceGroup, badTimes)
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
                check = Utilities.filterData(sasGroup, badTimes)
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
                check = Utilities.filterData(ancGroup, badTimes)
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False

                if py6sGroup is not None:
                    Utilities.filterData(py6sGroup,badTimes)

                # Filter L1AQC data for L1BQC criteria
                if ConfigFile.settings['SensorType'].lower() == 'seabird':
                    check = []
                    check.append(Utilities.filterData(esDarkGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(esLightGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(liDarkGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(liLightGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(ltDarkGroup,badTimes,'L1AQC'))
                    check.append(Utilities.filterData(ltLightGroup,badTimes,'L1AQC'))
                    if any(np.array(check) > 0.99):
                        msg = "Too few spectra remaining. Abort."
                        print(msg)
                        Utilities.writeLogFile(msg)
                        return False
                elif ConfigFile.settings['SensorType'].lower() == 'trios':
                    Utilities.filterData(esGroup,badTimes,'L1AQC')
                    Utilities.filterData(liGroup,badTimes,'L1AQC')
                    Utilities.filterData(ltGroup,badTimes,'L1AQC')

        return True

    @staticmethod
    def processL1bqc(node):
        ''' Fill in ancillary data with models as needed. Run QC on L1B for wind, SZA,
            spectral outliers, and meteorological filters (experimental).'''

        # For completeness, flip datasets into colums in all groups
        for grp in node.groups:
            for ds in grp.datasets:
                # print (grp.id, ds)
                grp.datasets[ds].datasetToColumns()

        # Need to either create a new ancData object, or populate the nans in the current one with the model data
        if not ProcessL1bqc.QC(node):
            return None

        node.attributes["PROCESSING_LEVEL"] = "1BQC"
        # Clean up units and push into relevant groups attributes
        # Ancillary
        gp = node.getGroup("ANCILLARY")
        gp.attributes["AOD_UNITS"] = "unitless"
        gp.attributes["HEADING_UNITS"] = "degrees"
        gp.attributes["HUMIDITY_UNITS"] = "percent"
        gp.attributes["LATITUDE_UNITS"] = "dec. deg. N"
        gp.attributes["LONGITUDE_UNITS"] = "dec. deg. E"
        gp.attributes["MET_FLAGS"] = "1: 6S Cloud, 2: Ruddick Cloud, 3: Es, 4: Dark,s 5: Rain"
        gp.attributes["PITCH_UNITS"] = "degrees"
        gp.attributes["POINTING_UNITS"] = "degrees"
        gp.attributes["REL_AZ_UNITS"] = "degrees"
        gp.attributes["ROLL_UNITS"] = "degrees"
        gp.attributes["SALINITY_UNITS"] = "psu"
        gp.attributes["SOLAR_AZ_UNITS"] = "degrees"
        gp.attributes["SPEED_UNITS"] = "m/s"
        gp.attributes["SST_UNITS"] = "degrees C"
        # gp.attributes["SST_IR_UNITS"] = node.attributes["SATPYR_UNITS"]
        # del node.attributes["SATPYR_UNITS"]
        gp.attributes["STATION_UNITS"] = "unitless"
        gp.attributes["SZA_UNITS"] = "degrees"
        gp.attributes["WINDSPEED_UNITS"] = "m/s"

        # Irradiance
        gp = node.getGroup("IRRADIANCE")
        gp.attributes["ES_UNITS"] = node.attributes["ES_UNITS"]
        del node.attributes["ES_UNITS"]
        if ConfigFile.settings['bL1bqcEnableSpecQualityCheck']:
            gp.attributes['ES_SPEC_FILTER'] = str(ConfigFile.settings['fL1bqcSpecFilterEs'])
        if node.attributes['L1AQC_DEGLITCH'] == 'ON':
            gp.attributes['L1AQC_DEGLITCH'] = 'ON'
            gp.attributes['ES_WINDOW_DARK'] = node.attributes['ES_WINDOW_DARK']
            gp.attributes['ES_WINDOW_LIGHT'] = node.attributes['ES_WINDOW_LIGHT']
            gp.attributes['ES_SIGMA_DARK'] = node.attributes['ES_SIGMA_DARK']
            gp.attributes['ES_SIGMA_LIGHT'] = node.attributes['ES_SIGMA_LIGHT']

            gp.attributes['ES_MINMAX_BAND_DARK'] = node.attributes['ES_MINMAX_BAND_DARK']
            gp.attributes['ES_MINMAX_BAND_LIGHT'] = node.attributes['ES_MINMAX_BAND_LIGHT']
            gp.attributes['ES_MIN_DARK'] = node.attributes['ES_MIN_DARK']
            gp.attributes['ES_MAX_DARK'] = node.attributes['ES_MAX_DARK']
            gp.attributes['ES_MIN_LIGHT'] = node.attributes['ES_MIN_LIGHT']
            gp.attributes['ES_MAX_LIGHT'] = node.attributes['ES_MAX_LIGHT']

        if ConfigFile.settings['bL1bqcEnableQualityFlags']:
            gp.attributes['ES_FILTER'] = str(ConfigFile.settings['fL1bqcSignificantEsFlag'])

        # Radiance
        gp = node.getGroup("RADIANCE")
        gp.attributes["LI_UNITS"] = node.attributes["LI_UNITS"]
        del(node.attributes["LI_UNITS"])
        gp.attributes["LT_UNITS"] = node.attributes["LT_UNITS"]
        del(node.attributes["LT_UNITS"])
        if ConfigFile.settings['bL1bqcEnableSpecQualityCheck']:
            gp.attributes['LI_SPEC_FILTER'] = str(ConfigFile.settings['fL1bqcSpecFilterLi'])
            gp.attributes['LT_SPEC_FILTER'] = str(ConfigFile.settings['fL1bqcSpecFilterLt'])
        if node.attributes['L1AQC_DEGLITCH'] == 'ON':
            gp.attributes['L1AQC_DEGLITCH'] = 'ON'
            gp.attributes['LT_WINDOW_DARK'] = node.attributes['LT_WINDOW_DARK']
            gp.attributes['LT_WINDOW_LIGHT'] = node.attributes['LT_WINDOW_LIGHT']
            gp.attributes['LT_SIGMA_DARK'] = node.attributes['LT_SIGMA_DARK']
            gp.attributes['LT_SIGMA_LIGHT'] = node.attributes['LT_SIGMA_LIGHT']

            gp.attributes['LT_MINMAX_BAND_DARK'] = node.attributes['LT_MINMAX_BAND_DARK']
            gp.attributes['LT_MINMAX_BAND_LIGHT'] = node.attributes['LT_MINMAX_BAND_LIGHT']
            gp.attributes['LT_MAX_DARK'] = node.attributes['LT_MAX_DARK']
            gp.attributes['LT_MAX_LIGHT'] = node.attributes['LT_MAX_LIGHT']
            gp.attributes['LT_MIN_DARK'] = node.attributes['LT_MIN_DARK']
            gp.attributes['LT_MIN_LIGHT'] = node.attributes['LT_MIN_LIGHT']

            gp.attributes['LI_WINDOW_DARK'] = node.attributes['LI_WINDOW_DARK']
            gp.attributes['LI_WINDOW_LIGHT'] = node.attributes['LI_WINDOW_LIGHT']
            gp.attributes['LI_SIGMA_DARK'] = node.attributes['LI_SIGMA_DARK']
            gp.attributes['LI_SIGMA_LIGHT'] = node.attributes['LI_SIGMA_LIGHT']

            gp.attributes['LI_MINMAX_BAND_DARK'] = node.attributes['LI_MINMAX_BAND_DARK']
            gp.attributes['LI_MINMAX_BAND_LIGHT'] = node.attributes['LI_MINMAX_BAND_LIGHT']
            gp.attributes['LI_MAX_DARK'] = node.attributes['LI_MAX_DARK']
            gp.attributes['LI_MAX_LIGHT'] = node.attributes['LI_MAX_LIGHT']
            gp.attributes['LI_MIN_DARK'] = node.attributes['LI_MIN_DARK']
            gp.attributes['LI_MIN_LIGHT'] = node.attributes['LI_MIN_LIGHT']

        # Py6S model
        py6sGroup = None
        for gp in node.groups:
            if gp.id.startswith("PY6S"):
                py6sGroup = gp
        if py6sGroup is not None:
            gp = node.getGroup('PY6S_MODEL')
            gp.attributes['Irradiance Units'] = 'W/m^2/um' # See ProcessL1b
            gp.attributes['direct_ratio'] = 'percent_direct_solar_irradiance'
            gp.attributes['diffuse_ratio'] = 'percent_diffuse_solar_irradiance'


        # Root
        node.attributes["HYPERINSPACE"] = MainConfig.settings["version"]
        node.attributes["DATETAG_UNITS"] = "YYYYDOY"
        node.attributes["TIMETAG2_UNITS"] = "HHMMSSmmm"

        if "DATETAG" in node.attributes.keys():
            del(node.attributes["DATETAG"])
        if "TIMETAG2" in node.attributes.keys():
            del(node.attributes["TIMETAG2"])
        if "COMMENT" in node.attributes.keys():
            del(node.attributes["COMMENT"])
        if "CLOUD_PERCENT" in node.attributes.keys():
            del(node.attributes["CLOUD_PERCENT"])
        if "DEPTH_RESOLUTION" in node.attributes.keys():
            del(node.attributes["DEPTH_RESOLUTION"])
        if ConfigFile.settings["bL1aqcSolarTracker"]:
            if "SAS SERIAL NUMBER" in node.attributes.keys():
                node.attributes["SOLARTRACKER_SERIAL_NUMBER"] = node.attributes["SAS SERIAL NUMBER"]
                del(node.attributes["SAS SERIAL NUMBER"])
        if ConfigFile.settings['bL1bqcLtUVNIR']:
            node.attributes['LT_UV_NIR_FILTER'] = 'ON'
        node.attributes['WIND_MAX'] = str(ConfigFile.settings['fL1bqcMaxWind'])
        node.attributes['SZA_MAX'] = str(ConfigFile.settings['fL1bqcSZAMax'])
        node.attributes['SZA_MIN'] = str(ConfigFile.settings['fL1bqcSZAMin'])
        if ConfigFile.settings['bL1bqcEnableQualityFlags']:
            node.attributes['CLOUD_FILTER'] = str(ConfigFile.settings['fL1bqcCloudFlag'])
            node.attributes['ES_FILTER'] = str(ConfigFile.settings['fL1bqcSignificantEsFlag'])
            node.attributes['DAWN_DUSK_FILTER'] = str(ConfigFile.settings['fL1bqcDawnDuskFlag'])
            node.attributes['RAIN_RH_FILTER'] = str(ConfigFile.settings['fL1bqcRainfallHumidityFlag'])

        # Clean up
        if node.attributes['L1AQC_DEGLITCH'] == 'ON':
            # Moved into group attributes above
            del(node.attributes['ES_WINDOW_DARK'])
            del(node.attributes['ES_WINDOW_LIGHT'])
            del(node.attributes['ES_SIGMA_DARK'])
            del(node.attributes['ES_SIGMA_LIGHT'])
            del(node.attributes['LT_WINDOW_DARK'])
            del(node.attributes['LT_WINDOW_LIGHT'])
            del(node.attributes['LT_SIGMA_DARK'])
            del(node.attributes['LT_SIGMA_LIGHT'])
            del(node.attributes['LI_WINDOW_DARK'])
            del(node.attributes['LI_WINDOW_LIGHT'])
            del(node.attributes['LI_SIGMA_DARK'])
            del(node.attributes['LI_SIGMA_LIGHT'])

            del(node.attributes['ES_MAX_DARK'])
            del(node.attributes['ES_MAX_LIGHT'])
            del(node.attributes['ES_MINMAX_BAND_DARK'])
            del(node.attributes['ES_MINMAX_BAND_LIGHT'])
            del(node.attributes['ES_MIN_DARK'])
            del(node.attributes['ES_MIN_LIGHT'])

            del(node.attributes['LT_MAX_DARK'])
            del(node.attributes['LT_MAX_LIGHT'])
            del(node.attributes['LT_MINMAX_BAND_DARK'])
            del(node.attributes['LT_MINMAX_BAND_LIGHT'])
            del(node.attributes['LT_MIN_DARK'])
            del(node.attributes['LT_MIN_LIGHT'])

            del(node.attributes['LI_MAX_DARK'])
            del(node.attributes['LI_MAX_LIGHT'])
            del(node.attributes['LI_MINMAX_BAND_DARK'])
            del(node.attributes['LI_MINMAX_BAND_LIGHT'])
            del(node.attributes['LI_MIN_DARK'])
            del(node.attributes['LI_MIN_LIGHT'])

        # Check to insure at least some data survived quality checks
        if node.getGroup("RADIANCE").getDataset("LT").data is None:
            msg = "All data appear to have been eliminated from the file. Aborting."
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Now strip datetimes from all datasets
        for gp in node.groups:
            for dsName in gp.datasets:
                ds = gp.datasets[dsName]
                if "Datetime" in ds.columns:
                    ds.columns.pop("Datetime")
                ds.columnsToDataset()

            # Finished with SolarTracker Status strings
            if gp.id == 'SOLARTRACKER_STATUS':
                node.removeGroup(gp)

        return node
