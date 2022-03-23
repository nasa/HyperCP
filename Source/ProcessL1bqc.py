
import collections
import warnings

import numpy as np
import scipy as sp
import datetime as datetime

import HDFRoot
from MainConfig import MainConfig
from AncillaryReader import AncillaryReader
from GetAnc import GetAnc
from Utilities import Utilities
from ConfigFile import ConfigFile


class ProcessL1bqc:
    '''Process L1BQC'''

    @staticmethod
    # def Thuillier(dateTag, wavelength):
    def TSIS_1(dateTag, wavelength):
        def dop(year):
            # day of perihelion
            years = list(range(2001,2031))
            key = [str(x) for x in years]
            day = [4, 2, 4, 4, 2, 4, 3, 2, 4, 3, 3, 5, 2, 4, 4, 2, 4, 3, 3, 5, 2, 4, 4, 3, 4, 3, 3, 5, 2, 3]
            dop = {key[i]: day[i] for i in range(0, len(key))}
            result = dop[str(year)]
            return result

        fp = 'Data/hybrid_reference_spectrum_p1nm_resolution_c2020-09-21_with_unc.nc'
        # fp = 'Data/Thuillier_F0.sb'
        # print("SB_support.readSB: " + fp)
        print("Reading : " + fp)
        if not HDFRoot.HDFRoot.readHDF5(fp):
            msg = "Unable to read TSIS-1 netcdf file."
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        else:
            F0_hybrid = HDFRoot.HDFRoot.readHDF5(fp)
            # F0_raw = np.array(Thuillier.data['esun']) # uW cm^-2 nm^-1
            # wv_raw = np.array(Thuillier.data['wavelength'])
            F0_raw = np.array(F0_hybrid['SSI']) # W m^-2 nm^-1
            wv_raw = np.array(F0_hybrid['Vacuum Wavelength'])
            # Earth-Sun distance
            day = int(str(dateTag)[4:7])
            year = int(str(dateTag)[0:4])
            eccentricity = 0.01672
            dayFactor = 360/365.256363
            dayOfPerihelion = dop(year)
            dES = 1-eccentricity*np.cos(dayFactor*(day-dayOfPerihelion)) # in AU
            F0_fs = F0_raw*dES

            F0 = sp.interpolate.interp1d(wv_raw, F0_fs)(wavelength)
            # Use the strings for the F0 dict
            wavelengthStr = [str(wave) for wave in wavelength]
            F0 = collections.OrderedDict(zip(wavelengthStr, F0))

        return F0

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
        ''' BUG: This is not optimal as it creates one badTimes record for each bad
            timestamp, rather than span of timestamps from badtimes[i][0] to badtimes[i][1]'''
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3)
        msg = f'{len(np.unique(badTimes))/len(ltDatetime)*100:.1f}% of spectra flagged'
        print(msg)
        Utilities.writeLogFile(msg)

        if len(badTimes) == 0:
            badTimes = None
        return badTimes

    @staticmethod
    def metQualityCheck(refGroup, sasGroup):
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
        for indx, dateTime in enumerate(esTime):
            # Masking spectra affected by clouds (Ruddick 2006, IOCCG Protocols).
            # The alternative to masking is to process them differently (e.g. See Ruddick_Rho)
            # Therefore, set this very high if you don't want it triggered (e.g. 1.0, see Readme)
            if li750[indx]/es750[indx] >= cloudFLAG:
                msg = f"Quality Check: Li(750)/Es(750) >= cloudFLAG:{cloudFLAG}"
                print(msg)
                Utilities.writeLogFile(msg)
                badTimes.append(dateTime)

            # Threshold for significant es
            # Wernand 2002
            if es480[indx] < esFlag:
                msg = f"Quality Check: es(480) < esFlag:{esFlag}"
                print(msg)
                Utilities.writeLogFile(msg)
                badTimes.append(dateTime)

            # Masking spectra affected by dawn/dusk radiation
            # Wernand 2002
            #v = esXSlice["470.0"][0] / esXSlice["610.0"][0] # Fix 610 -> 680
            if es470[indx]/es680[indx] < dawnDuskFlag:
                msg = f'Quality Check: ES(470.0)/ES(680.0) < dawnDuskFlag:{dawnDuskFlag}'
                print(msg)
                Utilities.writeLogFile(msg)
                badTimes.append(dateTime)

            # Masking spectra affected by rainfall and high humidity
            # Wernand 2002 (940/370), Garaba et al. 2012 also uses Es(940/370), presumably 720 was developed by Wang...???
            ''' Follow up on the source of this flag'''
            if es720[indx]/es370[indx] < humidityFlag:
                msg = f'Quality Check: ES(720.0)/ES(370.0) < humidityFlag:{humidityFlag}'
                print(msg)
                Utilities.writeLogFile(msg)
                badTimes.append(dateTime)

        badTimes = np.unique(badTimes)
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) # Duplicates each element to a list of two elements in a list
        msg = f'{len(np.unique(badTimes))/len(esTime)*100:.1f}% of spectra flagged'
        print(msg)
        Utilities.writeLogFile(msg)

        if len(badTimes) == 0:
            # Restore timestamps to columns (since it's not going to filterData, where it otherwise happens)
            esData.datasetToColumns()
            liData.datasetToColumns()
            ltData.datasetToColumns()
            badTimes = None
        return badTimes


    # @staticmethod
    # def columnToSlice(columns, start, end):
    #     ''' Take a slice of a dataset stored in columns '''

    #     # Each column is a time series either at a waveband for radiometer columns, or various grouped datasets for ancillary
    #     # Start and end are defined by the interval established in the Config (they are indexes)
    #     newSlice = collections.OrderedDict()
    #     for k in columns:
    #         if start == end:
    #             newSlice[k] = columns[k][start:end+1] # otherwise you get nada []
    #         else:
    #             newSlice[k] = columns[k][start:end] # up to not including end...next slice will pick it up
    #     return newSlice


    @staticmethod
    def includeModelDefaults(ancGroup, modRoot):
        ''' Include model data or defaults for blank ancillary fields '''
        print('Filling blank ancillary data with models or defaults from Configuration')

        epoch = datetime.datetime(1970, 1, 1,tzinfo=datetime.timezone.utc)
        # radData = referenceGroup.getDataset("ES") # From node, the input file

        # Convert ancillary date time
        if ancGroup is not None:
            ancGroup.datasets['LATITUDE'].datasetToColumns()
            ancTime = ancGroup.datasets['LATITUDE'].columns['Timetag2']
            ancSeconds = []
            ancDatetime = []
            for i, ancDate in enumerate(ancGroup.datasets['LATITUDE'].columns['Datetag']):
                ancDatetime.append(Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(ancDate),ancTime[i]))
                ancSeconds.append((ancDatetime[i]-epoch).total_seconds())
        # Convert model data date and time to datetime and then to seconds for interpolation
        if modRoot is not None:
            modTime = modRoot.groups[0].datasets["Timetag2"].tolist()
            modSeconds = []
            modDatetime = []
            for i, modDate in enumerate(modRoot.groups[0].datasets["Datetag"].tolist()):
                modDatetime.append(Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(modDate),modTime[i]))
                modSeconds.append((modDatetime[i]-epoch).total_seconds())

        # Model or default fills
        if 'WINDSPEED' in ancGroup.datasets:
            ancGroup.datasets['WINDSPEED'].datasetToColumns()
            windDataset = ancGroup.datasets['WINDSPEED']
            wind = windDataset.columns['NONE']
        else:
            windDataset = ancGroup.addDataset('WINDSPEED')
            wind = np.empty((1,len(ancSeconds)))
            wind[:] = np.nan
            wind = wind[0].tolist()
        if 'AOD' in ancGroup.datasets:
            ancGroup.datasets['AOD'].datasetToColumns()
            aodDataset = ancGroup.datasets['AOD']
            aod = aodDataset.columns['NONE']
        else:
            aodDataset = ancGroup.addDataset('AOD')
            aod = np.empty((1,len(ancSeconds)))
            aod[:] = np.nan
            aod = aod[0].tolist()
        # Default fills
        if 'SALINITY' in ancGroup.datasets:
            ancGroup.datasets['SALINITY'].datasetToColumns()
            saltDataset = ancGroup.datasets['SALINITY']
            salt = saltDataset.columns['NONE']
        else:
            saltDataset = ancGroup.addDataset('SALINITY')
            salt = np.empty((1,len(ancSeconds)))
            salt[:] = np.nan
            salt = salt[0].tolist()
        if 'SST' in ancGroup.datasets:
            ancGroup.datasets['SST'].datasetToColumns()
            sstDataset = ancGroup.datasets['SST']
            sst = sstDataset.columns['NONE']
        else:
            sstDataset = ancGroup.addDataset('SST')
            sst = np.empty((1,len(ancSeconds)))
            sst[:] = np.nan
            sst = sst[0].tolist()

        # Initialize flags
        windFlag = []
        aodFlag = []
        for i,ancSec in enumerate(ancSeconds):
            if np.isnan(wind[i]):
                windFlag.append('undetermined')
            else:
                windFlag.append('field')
            if np.isnan(aod[i]):
                aodFlag.append('undetermined')
            else:
                aodFlag.append('field')

        # Replace Wind, AOD NaNs with modeled data where possible.
        # These will be within one hour of the field data.
        if modRoot is not None:
            msg = 'Filling in field data with model data where needed.'
            print(msg)
            Utilities.writeLogFile(msg)

            for i,ancSec in enumerate(ancSeconds):

                if np.isnan(wind[i]):
                    # msg = 'Replacing wind with model data'
                    # print(msg)
                    # Utilities.writeLogFile(msg)
                    idx = Utilities.find_nearest(modSeconds,ancSec)
                    wind[i] = modRoot.groups[0].datasets['Wind'][idx]
                    windFlag[i] = 'model'
                if np.isnan(aod[i]):
                    # msg = 'Replacing AOD with model data'
                    # print(msg)
                    # Utilities.writeLogFile(msg)
                    idx = Utilities.find_nearest(modSeconds,ancSec)
                    aod[i] = modRoot.groups[0].datasets['AOD'][idx]
                    aodFlag[i] = 'model'

        # Replace Wind, AOD, SST, and Sal with defaults where still nan
        msg = 'Filling in ancillary data with default values where still needed.'
        print(msg)
        Utilities.writeLogFile(msg)

        saltFlag = []
        sstFlag = []
        for i, value in enumerate(wind):
            if np.isnan(value):
                wind[i] = ConfigFile.settings["fL1bqcDefaultWindSpeed"]
                windFlag[i] = 'default'
        for i, value in enumerate(aod):
            if np.isnan(value):
                aod[i] = ConfigFile.settings["fL1bqcDefaultAOD"]
                aodFlag[i] = 'default'
        for i, value in enumerate(salt):
            if np.isnan(value):
                salt[i] = ConfigFile.settings["fL1bqcDefaultSalt"]
                saltFlag.append('default')
            else:
                saltFlag.append('field')
        for i, value in enumerate(sst):
            if np.isnan(value):
                sst[i] = ConfigFile.settings["fL1bqcDefaultSST"]
                sstFlag.append('default')
            else:
                sstFlag.append('field')

        # Populate the datasets and flags with the InRad variables
        windDataset.columns["NONE"] = wind
        windDataset.columns["WINDFLAG"] = windFlag
        windDataset.columnsToDataset()
        aodDataset.columns["AOD"] = aod
        aodDataset.columns["AODFLAG"] = aodFlag
        aodDataset.columnsToDataset()
        saltDataset.columns["NONE"] = salt
        saltDataset.columns["SALTFLAG"] = saltFlag
        saltDataset.columnsToDataset()
        sstDataset.columns["NONE"] = sst
        sstDataset.columns["SSTFLAG"] = sstFlag
        sstDataset.columnsToDataset()

        # Convert ancillary seconds back to date/timetags ...
        ancDateTag = []
        ancTimeTag2 = []
        ancDT = []
        for i, sec in enumerate(ancSeconds):
            ancDT.append(datetime.datetime.utcfromtimestamp(sec).replace(tzinfo=datetime.timezone.utc))
            ancDateTag.append(float(f'{int(ancDT[i].timetuple()[0]):04}{int(ancDT[i].timetuple()[7]):03}'))
            ancTimeTag2.append(float( \
                f'{int(ancDT[i].timetuple()[3]):02}{int(ancDT[i].timetuple()[4]):02}{int(ancDT[i].timetuple()[5]):02}{int(ancDT[i].microsecond/1000):03}'))

        # Move the Timetag2 and Datetag into the arrays and remove the datasets
        for ds in ancGroup.datasets:
            ancGroup.datasets[ds].columns["Datetag"] = ancDateTag
            ancGroup.datasets[ds].columns["Timetag2"] = ancTimeTag2
            ancGroup.datasets[ds].columns["Datetime"] = ancDT
            ancGroup.datasets[ds].columns.move_to_end('Timetag2', last=False)
            ancGroup.datasets[ds].columns.move_to_end('Datetag', last=False)
            ancGroup.datasets[ds].columns.move_to_end('Datetime', last=False)

            ancGroup.datasets[ds].columnsToDataset()

    @staticmethod
    def QC(node, modRoot):
        ''' Add model data. QC for wind, Lt, SZA, spectral outliers, and met filters'''
        print("Add model data. QC for wind, Lt, SZA, spectral outliers, and met filters")

        referenceGroup = node.getGroup("IRRADIANCE")
        sasGroup = node.getGroup("RADIANCE")
        gpsGroup = node.getGroup('GPS')
        satnavGroup = None
        ancGroup = None
        pyrGroup = None
        for gp in node.groups:
            if gp.id.startswith("SOLARTRACKER"):
                if gp.id != "SOLARTRACKER_STATUS":
                    satnavGroup = gp
            if gp.id.startswith("ANCILLARY"):
                ancGroup = gp
                ancGroup.id = "ANCILLARY" # shift back from ANCILLARY_METADATA
            if gp.id.startswith("PYROMETER"):
                pyrGroup = gp

        # Regardless of whether SolarTracker/pySAS is used, Ancillary data will have been already been
        # interpolated in L1B as long as the ancillary file was read in at L1AQC. Regardless, these need
        # to have model data and/or default values incorporated.

        # If GMAO modeled data is selected in ConfigWindow, and an ancillary field data file
        # is provided in Main Window, then use the model data to fill in gaps in the field
        # record. Otherwise, use the selected default values from ConfigWindow

        # This step is only necessary for the ancillary datasets that REQUIRE
        # either field or GMAO or GUI default values. The remaining ancillary data
        # are culled from datasets in groups in L1B
        ProcessL1bqc.includeModelDefaults(ancGroup, modRoot)

        # Shift metadata into the ANCILLARY group as needed.
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

        # Take Heading and Speed preferentially from GPS
        if 'HEADING' in gpsGroup.datasets:
            # These have TT2/Datetag incorporated in arrays
            ancGroup.addDataset('HEADING')
            ancGroup.datasets['HEADING'] = gpsGroup.getDataset('COURSE')
            ancGroup.datasets['HEADING'].changeColName('TRUE','HEADING')
        if 'SOG' in gpsGroup.datasets:
            ancGroup.addDataset('SOG')
            ancGroup.datasets['SOG'] = gpsGroup.getDataset('SOG')
            ancGroup.datasets['SOG'].changeColName('NONE','SOG')
        if 'HEADING' not in gpsGroup.datasets and 'HEADING' in ancGroup.datasets:
            ancGroup.addDataset('HEADING')
            # ancGroup.datasets['HEADING'] = ancTemp.getDataset('HEADING')
            ancGroup.datasets['HEADING'] = ancGroup.getDataset('HEADING')
            ancGroup.datasets['HEADING'].changeColName('NONE','HEADING')
        if 'SOG' not in gpsGroup.datasets and 'SOG' in ancGroup.datasets:
            ancGroup.datasets['SOG'] = ancGroup.getDataset('SOG')
            ancGroup.datasets['SOG'].changeColName('NONE','SOG')
        if 'SPEED_F_W' in ancGroup.datasets:
            ancGroup.addDataset('SPEED_F_W')
            ancGroup.datasets['SPEED_F_W'] = ancGroup.getDataset('SPEED_F_W')
            ancGroup.datasets['SPEED_F_W'].changeColName('NONE','SPEED_F_W')
        # Take SZA and SOLAR_AZ preferentially from ancGroup (calculated with pysolar in L1C)
        ancGroup.datasets['SZA'].changeColName('NONE','SZA')
        ancGroup.datasets['SOLAR_AZ'].changeColName('NONE','SOLAR_AZ')
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

        if satnavGroup:
            ancGroup.datasets['REL_AZ'] = satnavGroup.getDataset('REL_AZ')
            if 'HUMIDITY' in ancGroup.datasets:
                ancGroup.datasets['HUMIDITY'] = satnavGroup.getDataset('HUMIDITY')
                ancGroup.datasets['HUMIDITY'].changeColName('NONE','HUMIDITY')
            # ancGroup.datasets['HEADING'] = satnavGroup.getDataset('HEADING') # Use GPS heading instead
            ancGroup.addDataset('POINTING')
            ancGroup.datasets['POINTING'] = satnavGroup.getDataset('POINTING')
            ancGroup.datasets['POINTING'].changeColName('ROTATOR','POINTING')
            ancGroup.datasets['REL_AZ'] = satnavGroup.getDataset('REL_AZ')
            ancGroup.datasets['REL_AZ'].datasetToColumns()
            # Use PITCH and ROLL preferentially from SolarTracker
            if 'PITCH' in satnavGroup.datasets:
                ancGroup.addDataset('PITCH')
                ancGroup.datasets['PITCH'] = satnavGroup.getDataset('PITCH')
                ancGroup.datasets['PITCH'].changeColName('SAS','PITCH')
            if 'ROLL' in satnavGroup.datasets:
                ancGroup.addDataset('ROLL')
                ancGroup.datasets['ROLL'] = satnavGroup.getDataset('ROLL')
                ancGroup.datasets['ROLL'].changeColName('SAS','ROLL')

        if 'NONE' in ancGroup.datasets['REL_AZ'].columns:
            ancGroup.datasets['REL_AZ'].changeColName('NONE','REL_AZ')

        if pyrGroup is not None:
            #PYROMETER
            ancGroup.datasets['SST_IR'] = pyrGroup.getDataset("T")
            ancGroup.datasets['SST_IR'].datasetToColumns()
            ancGroup.datasets['SST_IR'].changeColName('IR','SST_IR')

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

        # Filter SZAs
        SZAMin = float(ConfigFile.settings["fL1bqcSZAMin"])
        SZAMax = float(ConfigFile.settings["fL1bqcSZAMax"])

        SZA = ancGroup.datasets["SZA"].columns["SZA"]
        timeStamp = ancGroup.datasets["SZA"].columns["Datetime"]

        badTimes = None
        i=0
        start = -1
        stop = []
        for index, _ in enumerate(SZA):
            if SZA[index] < SZAMin or SZA[index] > SZAMax or wind[index] > maxWind:
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
                print('Removing records...')
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

        # Next apply the Meteorological Filter prior to slicing
        esData = referenceGroup.getDataset("ES")
        enableMetQualityCheck = int(ConfigFile.settings["bL1bqcEnableQualityFlags"])
        if enableMetQualityCheck:
            msg = "Applying meteorological filtering to eliminate spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            badTimes = ProcessL1bqc.metQualityCheck(referenceGroup, sasGroup)

            if badTimes is not None:
                if len(badTimes) == esData.data.size:
                    msg = "All data flagged for deletion. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
                print('Removing records...')
                check = Utilities.filterData(referenceGroup, badTimes)
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
                Utilities.filterData(sasGroup, badTimes)
                Utilities.filterData(ancGroup, badTimes)

        return True

    @staticmethod
    def processL1bqc(node):
        ''' Fill in ancillary data with models as needed. Run QC on L1B for wind, SZA,
            spectral outliers, and meteorological filters (experimental).'''

        # For completeness, flip datasets into colums in all groups
        for grp in node.groups:
            for ds in grp.datasets:
                grp.datasets[ds].datasetToColumns()

        gpsGroup = None
        for gp in node.groups:
            if gp.id.startswith("GPS"):
                gpsGroup = gp

        # Retrieve MERRA2 model ancillary data
        if ConfigFile.settings["bL1bqcpGetAnc"] ==1:
            msg = 'Model data for Wind and AOD may be used to replace blank values. Reading in model data...'
            print(msg)
            Utilities.writeLogFile(msg)
            modRoot = GetAnc.getAnc(gpsGroup)
            if modRoot is None:
                return None
        else:
            modRoot = None

        # Need to either create a new ancData object, or populate the nans in the current one with the model data
        if not ProcessL1bqc.QC(node, modRoot):
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
        gp.attributes["PITCH_UNITS"] = "degrees"
        gp.attributes["POINTING_UNITS"] = "degrees"
        gp.attributes["REL_AZ_UNITS"] = "degrees"
        gp.attributes["ROLL_UNITS"] = "degrees"
        gp.attributes["SAL_UNITS"] = "psu"
        gp.attributes["SOLAR_AZ_UNITS"] = "degrees"
        gp.attributes["SPEED_UNITS"] = "m/s"
        gp.attributes["SST_UNITS"] = "degrees C"
        gp.attributes["SST_IR_UNITS"] = node.attributes["SATPYR_UNITS"]
        del node.attributes["SATPYR_UNITS"]
        gp.attributes["STATION_UNITS"] = "unitless"
        gp.attributes["SZA_UNITS"] = "degrees"
        gp.attributes["WIND_UNITS"] = "m/s"

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

        # Root
        node.attributes["HYPERINSPACE"] = MainConfig.settings["version"]
        node.attributes["DATETAG_UNITS"] = "YYYYDOY"
        node.attributes["TIMETAG2_UNITS"] = "HHMMSSmmm"
        del(node.attributes["DATETAG"])
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

        return node
