
import collections
import sys
import warnings

import numpy as np
from numpy import matlib as mb
import scipy as sp
import datetime as dt

import HDFRoot
from Utilities import Utilities
from ConfigFile import ConfigFile
from RhoCorrections import RhoCorrections
from GetAnc import GetAnc


class ProcessL2:

    # Delete records within the out-of-bounds SZA
    @staticmethod
    def filterData(group, badTimes):                    
        
        # Now delete the record from each dataset in the group
        ticker = 0
        finalCount = 0
        for timeTag in badTimes:

            # msg = f'Eliminate data between: {timeTag} (HHMMSSMSS)'
            # print(msg)
            # Utilities.writeLogFile(msg)
            # print(timeTag)
            # print(" ")         
            start = Utilities.timeTag2ToSec(timeTag[0])
            stop = Utilities.timeTag2ToSec(timeTag[1])                
            # badIndex = ([i for i in range(lenDataSec) if start <= dataSec[i] and stop >= dataSec[i]])      
                    
            msg = f'   Remove {group.id}  Data'
            # print(msg)
            Utilities.writeLogFile(msg)
            #  timeStamp = satnavGroup.getDataset("ELEVATION").data["Timetag2"]
            # Ancillary still has datetag and tt2 broken out...
            if group.id == "ANCILLARY":
                timeData = group.getDataset("Timetag2").data["Timetag2"]                
            if group.id == "IRRADIANCE":
                timeData = group.getDataset("ES").data["Timetag2"]
            if group.id == "RADIANCE":
                timeData = group.getDataset("LI").data["Timetag2"]
            # if group.id == "SOLARTRACKER":
            #     timeData = group.getDataset("AZIMUTH").data["Timetag2"]
            # if group.id == "SOLARTRACKER_STATUS":
            #     return # Nothing we can do without a timetag
            # if group.id == "GPS":
            #     timeData = group.getDataset("COURSE").data["Timetag2"]
            # if group.id == "PYROMETER":
            #     timeData = group.getDataset("T").data["Timetag2"]

            dataSec = []
            for i in range(timeData.shape[0]):
                # Converts from TT2 (hhmmssmss. UTC) to milliseconds UTC
                dataSec.append(Utilities.timeTag2ToSec(timeData[i])) 

            lenDataSec = len(dataSec)
            if ticker == 0:
                # startLength = lenDataSec
                ticker +=1

            if lenDataSec > 0:
                counter = 0
                for i in range(lenDataSec):
                    if start <= dataSec[i] and stop >= dataSec[i]:                        
                        # test = group.getDataset("Timetag2").data["NONE"][i - counter]                                            
                        group.datasetDeleteRow(i - counter)  # Adjusts the index for the shrinking arrays
                        counter += 1

                # test = len(group.getDataset("Timetag2").data["NONE"])
                finalCount += counter
            else:
                msg = 'Data group is empty'
                print(msg)
                Utilities.writeLogFile(msg)

        # return finalCount/startLength
        return

    # Interpolate to a single column
    @staticmethod
    def interpolateColumn(columns, wl):
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

    '''# Perform spectral filtering
     # First try: calculate the STD of the normalized (at some max value) average ensemble.
        # Then test each normalized spectrum against the ensemble average and STD.
        # Plot results to see what to do next.... '''
    @staticmethod
    def specQualityCheck(group, inFilePath):
        
        if group.id == 'IRRADIANCE':
            Data = group.getDataset("ES") 
            timeStamp = group.getDataset("ES").data["Timetag2"]
            badTimes = Utilities.specFilter(inFilePath, Data, timeStamp, filterRange=[400, 700],\
                filterFactor=5, rType='Es')
            msg = f'{len(np.unique(badTimes))/len(timeStamp)*100:.1f}% of Es data flagged'
            print(msg)
            Utilities.writeLogFile(msg)  
        else:            
            Data = group.getDataset("LI")
            timeStamp = group.getDataset("LI").data["Timetag2"]
            badTimes1 = Utilities.specFilter(inFilePath, Data, timeStamp, filterRange=[400, 700],\
                filterFactor=8, rType='Li')
            msg = f'{len(np.unique(badTimes1))/len(timeStamp)*100:.1f}% of Li data flagged'
            print(msg)
            Utilities.writeLogFile(msg)  

            Data = group.getDataset("LT")
            timeStamp = group.getDataset("LT").data["Timetag2"]
            badTimes2 = Utilities.specFilter(inFilePath, Data, timeStamp, filterRange=[400, 700],\
                filterFactor=3, rType='Lt')
            msg = f'{len(np.unique(badTimes2))/len(timeStamp)*100:.1f}% of Lt data flagged'
            print(msg)
            Utilities.writeLogFile(msg)  

            badTimes = np.append(badTimes1,badTimes2, axis=0)
        

        return badTimes
        

    # Perform meteorological flag checking
    @staticmethod
    def metQualityCheck(refGroup, sasGroup):   
        esFlag = float(ConfigFile.settings["fL2SignificantEsFlag"])
        dawnDuskFlag = float(ConfigFile.settings["fL2DawnDuskFlag"])
        humidityFlag = float(ConfigFile.settings["fL2RainfallHumidityFlag"])     
        cloudFlag = float(ConfigFile.settings["fL2CloudFlag"])


        esData = refGroup.getDataset("ES")
        esData.datasetToColumns()
        esColumns = esData.columns
        esColumns.pop('Datetag')
        esTime =esColumns.pop('Timetag2')
        #  refGroup.getDataset("ES").data["Timetag2"]

        liData = sasGroup.getDataset("LI")
        liData.datasetToColumns()
        liColumns = liData.columns
        liColumns.pop('Datetag')
        liColumns.pop('Timetag2')
        ltData = sasGroup.getDataset("LT")
        ltData.datasetToColumns()
        ltColumns = ltData.columns
        ltColumns.pop('Datetag')
        ltColumns.pop('Timetag2')
        
        
        li750 = ProcessL2.interpolateColumn(liColumns, 750.0)
        es370 = ProcessL2.interpolateColumn(esColumns, 370.0)
        es470 = ProcessL2.interpolateColumn(esColumns, 470.0)
        es480 = ProcessL2.interpolateColumn(esColumns, 480.0)
        es680 = ProcessL2.interpolateColumn(esColumns, 680.0)
        es720 = ProcessL2.interpolateColumn(esColumns, 720.0)
        es750 = ProcessL2.interpolateColumn(esColumns, 750.0)
        badTimes = []
        for indx, timeTag in enumerate(esTime):                
            # Masking spectra affected by clouds (Ruddick 2006, IOCCG Protocols). 
            # The alternative to masking is to process them differently (e.g. See Ruddick_Rho)
            
            if li750[indx]/es750[indx] >= cloudFlag:
                # msg = f"Quality Check: Li(750)/Es(750) >= cloudFlag:{cloudFlag}"
                # print(msg)
                # Utilities.writeLogFile(msg)  
                badTimes.append(timeTag)


            # Threshold for significant es
            # Wernand 2002
            if es480[indx] < esFlag:
                # msg = f"Quality Check: es(480) < esFlag:{esFlag}"
                # print(msg)
                # Utilities.writeLogFile(msg)  
                badTimes.append(timeTag)

            # Masking spectra affected by dawn/dusk radiation
            # Wernand 2002
            #v = esXSlice["470.0"][0] / esXSlice["610.0"][0] # Fix 610 -> 680
            if es470[indx]/es680[indx] < dawnDuskFlag:
                # msg = f'Quality Check: ES(470.0)/ES(680.0) < dawnDuskFlag:{dawnDuskFlag}'
                # print(msg)
                # Utilities.writeLogFile(msg)  
                badTimes.append(timeTag)

            # Masking spectra affected by rainfall and high humidity
            # Wernand 2002 (940/370), Garaba et al. 2012 also uses Es(940/370), presumably 720 was developed by Wang...???
            ''' Follow up on the source of this flag'''            
            if es720[indx]/es370[indx] < humidityFlag:
                # msg = f'Quality Check: ES(720.0)/ES(370.0) < humidityFlag:{humidityFlag}'
                # print(msg)
                # Utilities.writeLogFile(msg)  
                badTimes.append(timeTag)
        
        badTimes = np.unique(badTimes)
        return badTimes


    # Take a slice of a dataset stored in columns
    @staticmethod
    def columnToSlice(columns, start, end):
        # Each column is a time series either at a waveband for radiometer columns, or various grouped datasets for ancillary
        # Start and end are defined by the interval established in the Config (they are indexes)
        newSlice = collections.OrderedDict()
        for k in columns:
            newSlice[k] = columns[k][start:end]
        return newSlice

    # Interpolate wind to radiometry
    @staticmethod
    def interpAncillary(node, ancData, modData, radData):
        print('Interpolating field ancillary and/or modeled ancillary data to radiometry times...')
        epoch = dt.datetime(1970, 1, 1)

        ancGroup = node.getGroup("ANCILLARY")
        dateTagDataset = ancGroup.addDataset("Datetag")
        timeTag2Dataset = ancGroup.addDataset("Timetag2")
        windDataset = ancGroup.addDataset("WINDSPEED")
        aodDataset = ancGroup.addDataset("AOD")
        saltDataset = ancGroup.addDataset("SAL")
        sstDataset = ancGroup.addDataset("SST")
        ancGroup.copyAttributes(ancData)        

        # Convert radData date and time to datetime and then to seconds for interpolation
        radTime = radData.data["Timetag2"].tolist()
        radSeconds = []
        radDatetime = []
        for i, radDate in enumerate(radData.data["Datetag"].tolist()):                
            radDatetime.append(Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(radDate),radTime[i]))
            radSeconds.append((radDatetime[i]-epoch).total_seconds())
        
        if ancData:
            # These are the entire ancillary record for the cruise
            dateTime = ancData.getColumn("DATETIME")[0]
            wind = ancData.getColumn("WINDSPEED")[0]
            salt = ancData.getColumn("SALINITY")[0]
            sst = ancData.getColumn("SST")[0]
            # Convert ancillary datetime to seconds for interpolation            
            ancSeconds = [(i-epoch).total_seconds() for i in dateTime] 
        else:
            ancData = None
            msg = "Ancillary field data missing; reverting to ancillary model or defaults"
            print(msg)
            Utilities.writeLogFile(msg)

        # Test for any field ancillary data in timeframe of rad time   
        if ancData and (max(ancSeconds) <= min(radSeconds) or min(ancSeconds) >= max(radSeconds)):
            ancData = None
            msg = "Ancillary field data do not intersect radiometric data; reverting to ancillary model or defaults"
            print(msg)
            Utilities.writeLogFile(msg)  

        # Create a framework to hold combined ancillary data
        ancInRadSeconds = []
        windFlag = []
        saltFlag = []
        sstFlag = []
        aodFlag = []
        windInRad = []
        saltInRad = []
        sstInRad = []
        aodInRad = []
        for i, value in enumerate(radSeconds):
            ancInRadSeconds.append(value)
            windFlag.append('undetermined')                   
            saltFlag.append('undetermined')                   
            sstFlag.append('undetermined')                   
            aodFlag.append('undetermined')                   
            windInRad.append(np.nan)
            saltInRad.append(np.nan)
            sstInRad.append(np.nan)
            aodInRad.append(np.nan)

        # Populate with field data if possible
        if ancData:
            for i, value in enumerate(ancInRadSeconds):
                idx = Utilities.find_nearest(ancSeconds,value)
                # Make sure the time difference between field anc and rad is <= 1hr
                if abs(ancSeconds[i] - value)/60/60 < 1:                    
                    windInRad[i] = wind[idx]                    
                    saltInRad[i] = salt[idx]
                    sstInRad[i] = sst[idx]
                    windFlag[i] = 'field'
                    saltFlag[i] = 'field'
                    sstFlag[i] = 'field'
        
        # Tallies
        msg = f'Field wind data has {np.isnan(windInRad).sum()} NaNs out of {len(windInRad)} prior to using model data'                
        print(msg)
        Utilities.writeLogFile(msg)
        msg = f'Field salt data has {np.isnan(saltInRad).sum()} NaNs out of {len(saltInRad)} prior to using model data'                
        print(msg)
        Utilities.writeLogFile(msg)
        msg = f'Field sst data has {np.isnan(sstInRad).sum()} NaNs out of {len(sstInRad)} prior to using model data'                
        print(msg)
        Utilities.writeLogFile(msg)
        msg = f'Field aod data has {np.isnan(aodInRad).sum()} NaNs out of {len(aodInRad)} prior to using model data'                
        print(msg)
        Utilities.writeLogFile(msg)

        # Convert model data date and time to datetime and then to seconds for interpolation
        if modData is not None:                
            modTime = modData.groups[0].datasets["Timetag2"].tolist()
            modSeconds = []
            modDatetime = []
            for i, modDate in enumerate(modData.groups[0].datasets["Datetag"].tolist()):                
                modDatetime.append(Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(modDate),modTime[i]))
                modSeconds.append((modDatetime[i]-epoch).total_seconds())  
        # Replace Wind, AOD Nans with modeled data where possible. These will be within one hour of the field data
        if modData is not None:
            msg = 'Filling in field data with model data where needed.'
            print(msg)
            Utilities.writeLogFile(msg)
            for i,value in enumerate(windInRad):
                if np.isnan(value):   
                    msg = 'Replacing wind with model data'
                    # print(msg)
                    Utilities.writeLogFile(msg)
                    idx = Utilities.find_nearest(modSeconds,ancInRadSeconds[i])
                    windInRad[i] = modData.groups[0].datasets['Wind'][idx]   
                    windFlag[i] = 'model'                     
            for i, value in enumerate(aodInRad):
                if np.isnan(value):
                    msg = 'Replacing AOD with model data'
                    # print(msg)
                    Utilities.writeLogFile(msg)
                    idx = Utilities.find_nearest(modSeconds,ancInRadSeconds[i])
                    aodInRad[i] = modData.groups[0].datasets['AOD'][idx]
                    aodFlag[i] = 'model'

        # Replace Wind, AOD, SST, and Sal with defaults where still nan
        msg = 'Filling in ancillary data with default values where still needed.'
        print(msg)
        Utilities.writeLogFile(msg)
        for i, value in enumerate(windInRad):
            if np.isnan(value):
                windInRad[i] = ConfigFile.settings["fL2DefaultWindSpeed"]
                windFlag[i] = 'default'
        for i, value in enumerate(aodInRad):
            if np.isnan(value):
                aodInRad[i] = ConfigFile.settings["fL2DefaultAOD"]
                aodFlag[i] = 'default'
        for i, value in enumerate(saltInRad):
            if np.isnan(value):
                saltInRad[i] = ConfigFile.settings["fL2DefaultSalt"]
                saltFlag[i] = 'default'
        for i, value in enumerate(sstInRad):
            if np.isnan(value):
                sstInRad[i] = ConfigFile.settings["fL2DefaultSST"]
                sstFlag[i] = 'default'

        windDataset.columns["WINDSPEED"] = windInRad
        windDataset.columns["WINDFLAG"] = windFlag
        aodDataset.columns["AOD"] = aodInRad
        aodDataset.columns["AODFLAG"] = aodFlag
        saltDataset.columns["SAL"] = saltInRad
        saltDataset.columns["SALTFLAG"] = saltFlag
        sstDataset.columns["SST"] = sstInRad
        sstDataset.columns["SSTFLAG"] = sstFlag
    
        # Convert ancillary seconds back to date/timetags
        ancDateTag = []
        ancTimeTag2 = []            
        for sec in radSeconds:
            radDT = dt.datetime.utcfromtimestamp(sec)
            ancDateTag.append(float(f'{int(radDT.timetuple()[0]):04}{int(radDT.timetuple()[7]):03}'))
            ancTimeTag2.append(float( \
                f'{int(radDT.timetuple()[3]):02}{int(radDT.timetuple()[4]):02}{int(radDT.timetuple()[5]):02}{int(radDT.microsecond/1000):03}'))
            # ancTimeTag2.append(Utilities.epochSecToDateTagTimeTag2(sec))
        
        dateTagDataset.columns["Datetag"] = ancDateTag
        timeTag2Dataset.columns["Timetag2"] = ancTimeTag2
        
        windDataset.columnsToDataset()
        aodDataset.columnsToDataset()
        saltDataset.columnsToDataset()
        sstDataset.columnsToDataset()
        dateTagDataset.columnsToDataset()
        timeTag2Dataset.columnsToDataset()
                                            
        return

    # Take the slice median of the lowest X% of hyperspectral slices
    @staticmethod
    def sliceAveHyper(y, hyperSlice, xSlice):
        hasNan = False
        # Ignore runtime warnings when array is all NaNs
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            for k in hyperSlice: # each k is a time series at a waveband.
                v = [hyperSlice[k][i] for i in y] # selects the lowest 5% within the interval window...
                mean = np.nanmean(v) # ... and averages them
                xSlice[k] = [mean]
                if np.isnan(mean):
                    hasNan = True
        return hasNan

    # Take the slice AND the median averages of ancillary data with X%
    @staticmethod
    def sliceAveAnc(root, start, end, y, ancGroup):
        newAncGroup = root.getGroup("ANCILLARY")

        # Combine these steps in a loop for ancillary date
        ancDict = collections.OrderedDict()
        for ds in ancGroup.datasets:
            key = ds            
            value = ancGroup.datasets[ds]            
            ancDict[key] = value

        datetag = ancDict['Datetag'].data
        timetag = ancDict['Timetag2'].data
        # Stores the middle element
        if len(datetag) > 0:
            date = datetag[int(len(datetag)/2)]
            time = timetag[int(len(timetag)/2)]

        for ds in ancDict: 
            if ds != 'Datetag' and ds != 'Timetag2':
                dsSlice = ProcessL2.columnToSlice(ancDict[ds].columns,start, end)

                dsXSlice = collections.OrderedDict

                for subset in dsSlice: # several ancillary datasets are groups
                    if subset != 'Datetag' and subset != 'Timetag2':
                        v = [dsSlice[subset][i] for i in y]
                        dsXSlice = collections.OrderedDict()                    
                        dsXSlice['Datetag'] = date
                        dsXSlice['Timetag2'] = time
                        if subset.endswith('FLAG'):
                            # Find the most frequest element
                            dsXSlice[subset] = Utilities.mostFrequent(v)
                        else:
                            dsXSlice[subset] = [np.mean(v)]
                    
                        # Check if the dataset is already there, and if so add to it, 
                        # otherwise build it
                        if not newAncGroup.getDataset(ds):
                            newDS = newAncGroup.addDataset(ds)                            
                            newDS.columns[subset] = dsXSlice
                        else:
                            newDS = newAncGroup.getDataset(ds)
                            newDS.columns[subset].append(dsXSlice)

                        newDS.columns[subset].columnsToDataset()

            







        # AODSlice = ProcessL2.columnToSlice(ancDict["AOD"].columns,start, end)
        # AZIMUTHSlice = ProcessL2.columnToSlice(ancDict["AZIMUTH"].columns,start, end)
        # COURSESlice = ProcessL2.columnToSlice(ancDict["COURSE"].columns,start, end)
        # ELEVATIONSlice = ProcessL2.columnToSlice(ancDict["ELEVATION"].columns,start, end)
        # HEADINGSlice = ProcessL2.columnToSlice(ancDict["HEADING"].columns,start, end)
        # LATITUDESlice = ProcessL2.columnToSlice(ancDict["LATITUDE"].columns,start, end)
        # LONGITUDESlice = ProcessL2.columnToSlice(ancDict["LONGITUDE"].columns,start, end)
        # PITCHSlice = ProcessL2.columnToSlice(ancDict["PITCH"].columns,start, end)
        # POINTINGSlice = ProcessL2.columnToSlice(ancDict["POINTING"].columns,start, end)
        # REL_AZSlice = ProcessL2.columnToSlice(ancDict["REL_AZ"].columns,start, end)
        # ROLLSlice = ProcessL2.columnToSlice(ancDict["ROLL"].columns,start, end)
        # SPEEDSlice = ProcessL2.columnToSlice(ancDict["SPEED"].columns,start, end)
        # SSTSlice = ProcessL2.columnToSlice(ancDict["SST"].columns,start, end)
        # SST_IRSlice = ProcessL2.columnToSlice(ancDict["SST_IR"].columns,start, end)
        # SALSlice = ProcessL2.columnToSlice(ancDict["SAL"].columns,start, end)
        # WINDSPEEDSlice = ProcessL2.columnToSlice(ancDict["WINDSPEED"].columns,start, end)

        # WINDSPEEDXSlice = collections.OrderedDict()
        # AODXSlice = collections.OrderedDict()
        # SalXSlice = collections.OrderedDict()
        # SSTXSlice = collections.OrderedDict()
        # SOL_ELXSlice = collections.OrderedDict()

        # with warnings.catch_warnings():
        #     warnings.simplefilter("ignore", category=RuntimeWarning)
        #     v = [WINDSPEEDSlice['WINDSPEED'][i] for i in y]
        #     mean = np.nanmean(v)
        #     WINDSPEEDXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True   
        #     # for k in AODSlice:
        #     v = [AODSlice['AOD'][i] for i in y]
        #     mean = np.nanmean(v)
        #     AODXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True  
        #     # for k in SalSlice:
        #     v = [SALSlice['SALT'][i] for i in y]
        #     mean = np.nanmean(v)
        #     SalXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True   
        #     # for k in SSTSlice:
        #     v = [SSTSlice['SST'][i] for i in y]
        #     mean = np.nanmean(v)
        #     SSTXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True   
        #     # for k in SOLAR_ELEVATIONSlice:
        #     v = [ELEVATIONSlice['SUN'][i] for i in y]
        #     mean = np.nanmean(v)
        #     SOL_ELXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True

    # # Take the slice median averages of ancillary data
    # @staticmethod
    # def sliceAverageAncillary(start, end, newESData, gpsCourseColumns=None, newGPSCourseData=None, gpsLatPosColumns=None, newGPSLatPosData=None, \
    #         gpsLonPosColumns=None, newGPSLonPosData=None, gpsMagVarColumns=None, newGPSMagVarData=None, gpsSpeedColumns=None, newGPSSpeedData=None, \
    #         satnavAzimuthColumns=None, newSATNAVAzimuthData=None, satnavElevationColumns=None, newSATNAVElevationData=None, satnavHeadingColumns=None, \
    #         newSATNAVHeadingData=None, satnavPointingColumns=None, newSATNAVPointingData=None, satnavRelAzColumns=None, newSATNAVRelAzData=None, \
    #         pyrColumns=None, newPyrData=None):

    #     # Take the slice median of ancillary data and add it to appropriate groups 
    #     # You can't take medians of Datetag and Timetag2, so use those from es
    #     sliceDate = newESData.columns["Datetag"][-1]
    #     sliceTime = newESData.columns["Timetag2"][-1]

    #     if gpsLatPosColumns is not None:
    #         gpsCourseSlice = ProcessL2.columnToSlice(gpsCourseColumns, start, end)
    #         sliceCourse = np.nanmedian(gpsCourseSlice["TRUE"])
    #         gpsLatSlice = ProcessL2.columnToSlice(gpsLatPosColumns, start, end)
    #         sliceLat = np.nanmedian(gpsLatSlice["NONE"])
    #         gpsLonSlice = ProcessL2.columnToSlice(gpsLonPosColumns, start, end)
    #         sliceLon = np.nanmedian(gpsLonSlice["NONE"])
    #         # gpsMagVarSlice = ProcessL2.columnToSlice(gpsMagVarColumns, start, end)
    #         # sliceMagVar = np.nanmedian(gpsMagVarSlice["NONE"])
    #         gpsSpeedSlice = ProcessL2.columnToSlice(gpsSpeedColumns, start, end)
    #         sliceSpeed = np.nanmedian(gpsSpeedSlice["NONE"])
    #         if not ("Datetag" in newGPSCourseData.columns):
    #             newGPSCourseData.columns["Datetag"] = [sliceDate]
    #             newGPSCourseData.columns["Timetag2"] = [sliceTime]
    #             newGPSCourseData.columns["TRUE"] = [sliceCourse]                        
    #             newGPSLatPosData.columns["Datetag"] = [sliceDate]
    #             newGPSLatPosData.columns["Timetag2"] = [sliceTime]
    #             newGPSLatPosData.columns["NONE"] = [sliceLat]
    #             newGPSLonPosData.columns["Datetag"] = [sliceDate]
    #             newGPSLonPosData.columns["Timetag2"] = [sliceTime]
    #             newGPSLonPosData.columns["NONE"] = [sliceLon]
    #             # newGPSMagVarData.columns["Datetag"] = [sliceDate]
    #             # newGPSMagVarData.columns["Timetag2"] = [sliceTime]
    #             # newGPSMagVarData.columns["NONE"] = [sliceMagVar]
    #             newGPSSpeedData.columns["Datetag"] = [sliceDate]
    #             newGPSSpeedData.columns["Timetag2"] = [sliceTime]
    #             newGPSSpeedData.columns["NONE"] = [sliceSpeed]
    #         else:
    #             newGPSCourseData.columns["Datetag"].append(sliceDate)
    #             newGPSCourseData.columns["Timetag2"].append(sliceTime)
    #             newGPSCourseData.columns["TRUE"].append(sliceCourse)
    #             newGPSLatPosData.columns["Datetag"].append(sliceDate)
    #             newGPSLatPosData.columns["Timetag2"].append(sliceTime)
    #             newGPSLatPosData.columns["NONE"].append(sliceLat)
    #             newGPSLonPosData.columns["Datetag"].append(sliceDate)
    #             newGPSLonPosData.columns["Timetag2"].append(sliceTime)
    #             newGPSLonPosData.columns["NONE"].append(sliceLon)
    #             # newGPSMagVarData.columns["Datetag"].append(sliceDate)
    #             # newGPSMagVarData.columns["Timetag2"].append(sliceTime)
    #             # newGPSMagVarData.columns["NONE"].append(sliceMagVar)
    #             newGPSSpeedData.columns["Datetag"].append(sliceDate)
    #             newGPSSpeedData.columns["Timetag2"].append(sliceTime)
    #             newGPSSpeedData.columns["NONE"].append(sliceSpeed)

    #     if satnavRelAzColumns is not None:
    #         satnavAzimuthSlice = ProcessL2.columnToSlice(satnavAzimuthColumns, start, end)
    #         sliceAzimuth = np.nanmedian(satnavAzimuthSlice["SUN"])
    #         satnavElevationSlice = ProcessL2.columnToSlice(satnavElevationColumns, start, end)
    #         sliceElevation = np.nanmedian(satnavElevationSlice["SUN"])
    #         satnavHeadingSlice = ProcessL2.columnToSlice(satnavHeadingColumns, start, end)
    #         sliceHeadingSAS = np.nanmedian(satnavHeadingSlice["SAS_TRUE"])
    #         sliceHeadingShip = np.nanmedian(satnavHeadingSlice["SHIP_TRUE"])
    #         satnavPointingSlice = ProcessL2.columnToSlice(satnavPointingColumns, start, end)
    #         slicePointing = np.nanmedian(satnavPointingSlice["ROTATOR"])
    #         satnavRelAzSlice = ProcessL2.columnToSlice(satnavRelAzColumns, start, end)
    #         sliceRelAz = np.nanmedian(satnavRelAzSlice["REL_AZ"])
    #         if not ("Datetag" in newSATNAVAzimuthData.columns):
    #             newSATNAVAzimuthData.columns["Datetag"] = [sliceDate]
    #             newSATNAVAzimuthData.columns["Timetag2"] = [sliceTime]
    #             newSATNAVAzimuthData.columns["SUN"] = [sliceAzimuth]
    #             newSATNAVElevationData.columns["Datetag"] = [sliceDate]
    #             newSATNAVElevationData.columns["Timetag2"] = [sliceTime]
    #             newSATNAVElevationData.columns["SUN"] = [sliceElevation]
    #             newSATNAVHeadingData.columns["Datetag"] = [sliceDate]
    #             newSATNAVHeadingData.columns["Timetag2"] = [sliceTime]
    #             newSATNAVHeadingData.columns["SAS_True"] = [sliceHeadingSAS]
    #             newSATNAVHeadingData.columns["SHIP_True"] = [sliceHeadingShip]
    #             newSATNAVPointingData.columns["Datetag"] = [sliceDate]
    #             newSATNAVPointingData.columns["Timetag2"] = [sliceTime]
    #             newSATNAVPointingData.columns["ROTATOR"] = [slicePointing]
    #             newSATNAVRelAzData.columns["Datetag"] = [sliceDate]
    #             newSATNAVRelAzData.columns["Timetag2"] = [sliceTime]
    #             newSATNAVRelAzData.columns["REL_AZ"] = [sliceRelAz]    
    #         else:
    #             newSATNAVAzimuthData.columns["Datetag"].append(sliceDate)
    #             newSATNAVAzimuthData.columns["Timetag2"].append(sliceTime)
    #             newSATNAVAzimuthData.columns["SUN"].append(sliceAzimuth)
    #             newSATNAVElevationData.columns["Datetag"].append(sliceDate)
    #             newSATNAVElevationData.columns["Timetag2"].append(sliceTime)
    #             newSATNAVElevationData.columns["SUN"].append(sliceElevation)
    #             newSATNAVHeadingData.columns["Datetag"].append(sliceDate)
    #             newSATNAVHeadingData.columns["Timetag2"].append(sliceTime)
    #             newSATNAVHeadingData.columns["SAS_True"].append(sliceHeadingSAS)
    #             newSATNAVHeadingData.columns["SHIP_True"].append(sliceHeadingShip)
    #             newSATNAVPointingData.columns["Datetag"].append(sliceDate)
    #             newSATNAVPointingData.columns["Timetag2"].append(sliceTime)
    #             newSATNAVPointingData.columns["ROTATOR"].append(slicePointing)
    #             newSATNAVRelAzData.columns["Datetag"].append(sliceDate)
    #             newSATNAVRelAzData.columns["Timetag2"].append(sliceTime)
    #             newSATNAVRelAzData.columns["REL_AZ"].append(sliceRelAz)

    #     if pyrColumns is not None:
    #         pyrSlice = ProcessL2.columnToSlice(pyrColumns, start, end)
    #         slicePyr = np.nanmedian(pyrSlice["IR"])
    #         if not ("Datetag" in newPyrData.columns):
    #             newPyrData.columns["Datetag"] = [sliceDate]  
    #             newPyrData.columns["Timetag2"] = [sliceTime]
    #             newPyrData.columns["WATER_TEMP"] = [slicePyr]              
    #         else:
    #             newPyrData.columns["Datetag"].append(sliceDate)
    #             newPyrData.columns["Timetag2"].append(sliceTime)
    #             newPyrData.columns["WATER_TEMP"].append(slicePyr)
       
    @staticmethod
    def calculateREFLECTANCE2(root, sasGroup, refGroup, ancGroup, start, end):
        '''Calculate the lowest X% Lt(780). Check for Nans in Li, Lt, Es, or wind. Send out for meteorological quality flags, 
        Perform rho correction with wind. Calculate the Rrs. Correct for NIR.'''

        esData = refGroup.getDataset("ES")
        liData = sasGroup.getDataset("LI")
        ltData = sasGroup.getDataset("LT") 
        
        # Copy datasets to dictionary
        esData.datasetToColumns()
        esColumns = esData.columns
        # tt2 = esColumns["Timetag2"]
        liData.datasetToColumns()
        liColumns = liData.columns        
        ltData.datasetToColumns()
        ltColumns = ltData.columns   

        # Root (new/output) groups:
        newReflectanceGroup = root.getGroup("REFLECTANCE")
        newRadianceGroup = root.getGroup("RADIANCE")
        newIrradianceGroup = root.getGroup("IRRADIANCE")

        newRrsData = newReflectanceGroup.addDataset("Rrs")
        newESData = newIrradianceGroup.addDataset("ES")        
        newLIData = newRadianceGroup.addDataset("LI")
        newLTData = newRadianceGroup.addDataset("LT") 

        esSlice = ProcessL2.columnToSlice(esColumns,start, end)
        liSlice = ProcessL2.columnToSlice(liColumns,start, end)
        ltSlice = ProcessL2.columnToSlice(ltColumns,start, end)

    
        rhoSkyDefault = float(ConfigFile.settings["fL2RhoSky"])
        RuddickRho = int(ConfigFile.settings["bL2RuddickRho"])
        ZhangRho = int(ConfigFile.settings["bL2ZhangRho"])
        # defaultWindSpeed = float(ConfigFile.settings["fL2DefaultWindSpeed"])
        # windSpeedMean = defaultWindSpeed # replaced later with met file, if present                         
        performNIRCorrection = int(ConfigFile.settings["bL2PerformNIRCorrection"])                        
        enablePercentLt = float(ConfigFile.settings["bL2EnablePercentLt"])
        percentLt = float(ConfigFile.settings["fL2PercentLt"])

        datetag = esSlice["Datetag"]
        timetag = esSlice["Timetag2"]

        esSlice.pop("Datetag")
        esSlice.pop("Timetag2")

        liSlice.pop("Datetag")
        liSlice.pop("Timetag2")

        ltSlice.pop("Datetag")
        ltSlice.pop("Timetag2")

        # Stores the middle element
        if len(datetag) > 0:
            date = datetag[int(len(datetag)/2)]
            time = timetag[int(len(timetag)/2)]
        # if latpos:
        #     lat = latpos[int(len(latpos)/2)]
        # if lonpos:
        #     lon = lonpos[int(len(lonpos)/2)]
        # if relAzimuth:
        #     relAzi = relAzimuth[int(len(relAzimuth)/2)]

        '''# Calculates the lowest X% (based on Hooker & Morel 2003; Hooker et al. 2002; Zibordi et al. 2002, IOCCG Protocols)
        X will depend on FOV and integration time of instrument. Hooker cites a rate of 2 Hz.
        It remains unclear to me from Hooker 2002 whether the recommendation is to take the average of the ir/radiances
        within the threshold and calculate Rrs, or to calculate the Rrs within the threshold, and then average, however IOCCG
        Protocols pretty clearly state to average the ir/radiances first, then calculate the Rrs...as done here.'''
        n = len(list(ltSlice.values())[0])
        x = round(n*percentLt/100) # number of retained values
        msg = f'{n} data points in slice (ensemble).'
        print(msg)
        Utilities.writeLogFile(msg)
        
        # IS THIS NECESSARY?...There are often few data points, and given 10% of 10 points is just one data point...(?)
        if n <= 5 or x == 0:
            x = n # if only 5 or fewer records retained, use them all...
        
        # Find the indexes for the lowest X%
        lt780 = ProcessL2.interpolateColumn(ltSlice, 780.0)
        index = np.argsort(lt780) # gives indexes if values were to be sorted
                
        if enablePercentLt:
            # returns indexes of the first x values (if values were sorted); i.e. the indexes of the lowest X% of lt780
            y = index[0:x] 
        else:
            y = index # If Percent Lt is turned off, this will average the whole slice
        msg = f'{len(y)} data points remaining in slice to average after low light filter.'
        print(msg)
        Utilities.writeLogFile(msg)

        # Take the mean of the lowest X%
        esXSlice = collections.OrderedDict()
        liXSlice = collections.OrderedDict()
        ltXSlice = collections.OrderedDict()        

        hasNan = ProcessL2.sliceAveHyper(y, esSlice, esXSlice)
        hasNan = ProcessL2.sliceAveHyper(y, liSlice, liXSlice)
        hasNan = ProcessL2.sliceAveHyper(y, ltSlice, ltXSlice)

        ProcessL2.sliceAveAnc(root, start, end, y, ancGroup)
        newAncGroup = root.getGroup("ANCILLARY") # Just populated above

        WINDSPEEDXSlice = newAncGroup
        AODXSlice = newAncGroup
        CloudXSlice = newAncGroup
        SOL_ELXSlice = newAncGroup
        SSTXSlice = newAncGroup
        SalXSlice = newAncGroup

        # # Combine these steps in a loop for ancillary date
        # ancDict = {}
        # for ds in ancGroup.datasets:
        #     key = ds            
        #     value = ancGroup.datasets[ds]            
        #     ancDict[key] = value

        # WINDSPEEDSlice = ProcessL2.columnToSlice(ancDict["WINDSPEED"].columns,start, end)
        # AODSlice = ProcessL2.columnToSlice(ancDict["AOD"].columns,start, end)
        # SALSlice = ProcessL2.columnToSlice(ancDict["SAL"].columns,start, end)
        # SSTSlice = ProcessL2.columnToSlice(ancDict["SST"].columns,start, end)
        # ELEVATIONSlice = ProcessL2.columnToSlice(ancDict["ELEVATION"].columns,start, end)


        # WINDSPEEDXSlice = collections.OrderedDict()
        # AODXSlice = collections.OrderedDict()
        # SalXSlice = collections.OrderedDict()
        # SSTXSlice = collections.OrderedDict()
        # SOL_ELXSlice = collections.OrderedDict()

        # with warnings.catch_warnings():
        #     warnings.simplefilter("ignore", category=RuntimeWarning)
        #     v = [WINDSPEEDSlice['WINDSPEED'][i] for i in y]
        #     mean = np.nanmean(v)
        #     WINDSPEEDXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True   
        #     # for k in AODSlice:
        #     v = [AODSlice['AOD'][i] for i in y]
        #     mean = np.nanmean(v)
        #     AODXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True  
        #     # for k in SalSlice:
        #     v = [SALSlice['SALT'][i] for i in y]
        #     mean = np.nanmean(v)
        #     SalXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True   
        #     # for k in SSTSlice:
        #     v = [SSTSlice['SST'][i] for i in y]
        #     mean = np.nanmean(v)
        #     SSTXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True   
        #     # for k in SOLAR_ELEVATIONSlice:
        #     v = [ELEVATIONSlice['SUN'][i] for i in y]
        #     mean = np.nanmean(v)
        #     SOL_ELXSlice = [mean]
        #     if np.isnan(mean):
        #         hasNan = True   

        # Exit if detect NaN
        if hasNan:            
            msg = 'ProcessL2.calculateREFLECTANCE2: Slice X"%" average error: Dataset all NaNs.'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        # Calculate Rho_sky
        if RuddickRho:
            '''This is the Ruddick, et al. 2006 approach, which has one method for 
            clear sky, and another for cloudy. Methods of this type (i.e. not accounting
            for spectral dependence (Lee et al. 2010, Gilerson et al. 2018) or polarization
            effects (Harmel et al. 2012, Mobley 2015, Hieronumi 2016, D'Alimonte and Kajiyama 2016, 
            Foster and Gilerson 2016, Gilerson et al. 2018)) are explicitly recommended in the 
            IOCCG Protocols for Above Water Radiometry Measurements and Data Analysis (Chapter 5, Draft 2019).'''
            
            li750 = ProcessL2.interpolateColumn(liXSlice, 750.0)
            es750 = ProcessL2.interpolateColumn(esXSlice, 750.0)
            sky750 = li750[0]/es750[0]

            p_sky = RhoCorrections.RuddickCorr(sky750, rhoSkyDefault, WINDSPEEDXSlice)

        elif ZhangRho:

            ''' Fix '''
            CloudXSlice = 50 # %

            p_sky = RhoCorrections.ZhangCorr(WINDSPEEDXSlice,AODXSlice,CloudXSlice,SOL_ELXSlice,SSTXSlice,SalXSlice)

        # Add date/time data to Rrs dataset
        if not ("Datetag" in newRrsData.columns):
            newESData.columns["Datetag"] = [date]
            newLIData.columns["Datetag"] = [date]
            newLTData.columns["Datetag"] = [date]
            newRrsData.columns["Datetag"] = [date]
            newESData.columns["Timetag2"] = [time]
            newLIData.columns["Timetag2"] = [time]
            newLTData.columns["Timetag2"] = [time]
            newRrsData.columns["Timetag2"] = [time]            
        else:
            newESData.columns["Datetag"].append(date)
            newLIData.columns["Datetag"].append(date)
            newLTData.columns["Datetag"].append(date)
            newRrsData.columns["Datetag"].append(date)
            newESData.columns["Timetag2"].append(time)
            newLIData.columns["Timetag2"].append(time)
            newLTData.columns["Timetag2"].append(time)
            newRrsData.columns["Timetag2"].append(time)           

        rrsSlice = {}
                
        # Calculate Rrs
        '''# No bidirectional correction is made here.....'''
        for k in esXSlice:
            if (k in liXSlice) and (k in ltXSlice):
                if k not in newESData.columns:
                    newESData.columns[k] = []
                    newLIData.columns[k] = []
                    newLTData.columns[k] = []
                    newRrsData.columns[k] = []

                es = esXSlice[k][0]
                li = liXSlice[k][0]
                lt = ltXSlice[k][0]

                # Calculate the Rrs
                rrs = (lt - (p_sky * li)) / es

                newESData.columns[k].append(es)
                newLIData.columns[k].append(li)
                newLTData.columns[k].append(lt)
                #newRrsData.columns[k].append(rrs)
                rrsSlice[k] = rrs

        # Perfrom near-infrared correction to remove additional atmospheric and glint contamination
        if performNIRCorrection:

            # Data show a minimum near 725; using an average from above 750 leads to negative reflectances
            NIRRRs = []
            for k in rrsSlice:
                # if float(k) >= 750 and float(k) <= 800:
                if float(k) >= 700 and float(k) <= 800:
                    # avg += rrsSlice[k]
                    # num += 1
                    NIRRRs.append(rrsSlice[k])
            # avg /= num
            # avg = np.median(NIRRRs)
            minNIR = min(NIRRRs)
    
            # Subtract average from each waveband
            for k in rrsSlice:
                # rrsSlice[k] -= avg
                rrsSlice[k] -= minNIR

        for k in rrsSlice:
            newRrsData.columns[k].append(rrsSlice[k])

        newESData.columnsToDataset()   
        newLIData.columnsToDataset()
        newLTData.columnsToDataset()
        newRrsData.columnsToDataset()
        return True


    @staticmethod
    def calculateREFLECTANCE(root, node, gpsGroup, satnavGroup, pyrGroup, ancData, modData):
        '''Filter out high wind and high/low SZA.
        Interpolate windspeeds, average intervals.
        Run meteorology quality checks.
        Pass to calculateREFLECTANCE2 for rho calcs, Rrs, NIR correction.'''

        print("calculateREFLECTANCE")                   

        referenceGroup = node.getGroup("IRRADIANCE")
        sasGroup = node.getGroup("RADIANCE")

        ''' # Filter low SZAs and high winds '''
        # defaultWindSpeed = float(ConfigFile.settings["fL2DefaultWindSpeed"])
        maxWind = float(ConfigFile.settings["fL2MaxWind"]) 
        SZAMin = float(ConfigFile.settings["fL2SZAMin"])
        SZAMax = float(ConfigFile.settings["fL2SZAMax"])
        SZA = 90 -satnavGroup.getDataset("ELEVATION").data["SUN"]
        timeStamp = satnavGroup.getDataset("ELEVATION").data["Timetag2"]
        
        # If ancillary modeled data is selected, and an ancillary file exists for wind, 
        # use the model data to fill in gaps in the field record prior to interpolating to 
        # L2 timestamps.
        # Otherwise, interpolate the field ancillary data if it exists
        # Otherwise, use the selected default values        
        esData = referenceGroup.getDataset("ES")

        # This will populate the root group ANCILLARY with ancillary and/or modelled datasets
        # and/or default values, all interpolated to the radiometric data timestamps
        ProcessL2.interpAncillary(node, ancData, modData, esData)
        
        # Now that ancillary data has been interpolated, it is matched up with
        #  additional ancillary data (gps, solartracker, etc.) 1:1
        ancGroup = node.getGroup("ANCILLARY")
        ancGroup.addDataset('COURSE')
        ancGroup.addDataset('LATITUDE')
        ancGroup.addDataset('LONGITUDE')
        ancGroup.addDataset('SPEED')
        ancGroup.addDataset('AZIMUTH')
        ancGroup.addDataset('ELEVATION')
        ancGroup.addDataset('HEADING')
        ancGroup.addDataset('PITCH')
        ancGroup.addDataset('POINTING')
        ancGroup.addDataset('REL_AZ')
        ancGroup.addDataset('ROLL')

        if gpsGroup:
            ancGroup.datasets['COURSE'] = gpsGroup.getDataset('COURSE')
            ancGroup.datasets['COURSE'].datasetToColumns()
            ancGroup.datasets['LATITUDE'] = gpsGroup.getDataset('LATITUDE')
            ancGroup.datasets['LATITUDE'].datasetToColumns()
            ancGroup.datasets['LONGITUDE'] = gpsGroup.getDataset('LONGITUDE')
            ancGroup.datasets['LONGITUDE'].datasetToColumns()
            ancGroup.datasets['SPEED'] = gpsGroup.getDataset('SPEED')
            ancGroup.datasets['SPEED'].datasetToColumns()
        if satnavGroup:
            ancGroup.datasets['AZIMUTH'] = satnavGroup.getDataset('AZIMUTH')
            ancGroup.datasets['ELEVATION'] = satnavGroup.getDataset('ELEVATION')
            ancGroup.datasets['HEADING'] = satnavGroup.getDataset('HEADING')
            ancGroup.datasets['PITCH'] = satnavGroup.getDataset('PITCH')
            ancGroup.datasets['POINTING'] = satnavGroup.getDataset('POINTING')
            ancGroup.datasets['REL_AZ'] = satnavGroup.getDataset('REL_AZ')
            ancGroup.datasets['ROLL'] = satnavGroup.getDataset('ROLL')        
            ancGroup.datasets['AZIMUTH'].datasetToColumns()
            ancGroup.datasets['ELEVATION'].datasetToColumns()
            ancGroup.datasets['HEADING'].datasetToColumns()
            ancGroup.datasets['PITCH'].datasetToColumns()
            ancGroup.datasets['POINTING'].datasetToColumns()
            ancGroup.datasets['REL_AZ'].datasetToColumns()
            ancGroup.datasets['ROLL'].datasetToColumns()
        if pyrGroup is not None:
            #PYROMETER
            ancGroup.datasets['SST_IR'] = pyrGroup.getDataset("T")  
            ancGroup.datasets['SST_IR'].datasetToColumns()

        wind = ancGroup.getDataset("WINDSPEED").data["WINDSPEED"]
        

        # Data filtering
        badTimes = None
        i=0
        start = -1
        stop = []        

        # Filter on SZA and Wind limit
        for index in range(len(SZA)):
            # Check for angles spanning north
            if SZA[index] < SZAMin or SZA[index] > SZAMax or wind[index] > maxWind:
                i += 1                              
                if start == -1:
                    print('Low SZA. SZA: ' + str(round(SZA[index])))
                    start = index
                stop = index 
                if badTimes is None:
                    badTimes = []                               
            else:                                
                if start != -1:
                    print('SZA passed. SZA: ' + str(round(SZA[index])))
                    startstop = [timeStamp[start],timeStamp[stop]]
                    msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]} (HHMMSSMSS)'
                    print(msg)
                    Utilities.writeLogFile(msg)                                               
                    badTimes.append(startstop)
                    start = -1
        msg = f'Percentage of data out of SZA and Wind limits: {round(100*i/len(timeStamp))} %'
        print(msg)
        Utilities.writeLogFile(msg)

        if start != -1 and badTimes is None: # Records from a mid-point to the end are bad
            startstop = [timeStamp[start],timeStamp[stop]]
            badTimes = [startstop]

        if start==0 and stop==index: # All records are bad                           
            return False
        
        if badTimes is not None:
            print('Removing records...')
            ProcessL2.filterData(referenceGroup, badTimes)            
            ProcessL2.filterData(sasGroup, badTimes)
            ProcessL2.filterData(ancGroup, badTimes)            


        ''' # Now filter the spectra from the entire collection before slicing the intervals'''
       # Spectral Outlier Filter
        enableSpecQualityCheck = ConfigFile.settings['bL2EnableSpecQualityCheck']
        if enableSpecQualityCheck:
            badTimes = None
            msg = "Applying spectral filtering to eliminate noisy spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            inFilePath = root.attributes['In_Filepath']
            badTimes1 = ProcessL2.specQualityCheck(referenceGroup, inFilePath)
            badTimes2 = ProcessL2.specQualityCheck(sasGroup, inFilePath)
            badTimes = np.append(badTimes1,badTimes2, axis=0)

            if badTimes is not None:
                print('Removing records...')
                ProcessL2.filterData(referenceGroup, badTimes)            
                ProcessL2.filterData(sasGroup, badTimes)
                ProcessL2.filterData(ancGroup, badTimes)                

        ''' Next apply the meteorological filter prior to slicing'''     
        # Meteorological Filtering   
        enableMetQualityCheck = int(ConfigFile.settings["bL2EnableQualityFlags"])          
        if enableMetQualityCheck:
            badTimes = ProcessL2.metQualityCheck(referenceGroup, sasGroup)
                
            if badTimes is not None:
                print('Removing records...')
                ProcessL2.filterData(referenceGroup, badTimes)            
                ProcessL2.filterData(sasGroup, badTimes)
                ProcessL2.filterData(ancGroup, badTimes)


        # # esData = referenceGroup.getDataset("ES")
        # liData = sasGroup.getDataset("LI")
        # ltData = sasGroup.getDataset("LT")        

        # # Root (new/output) groups:
        # newReflectanceGroup = root.getGroup("REFLECTANCE")
        # newRadianceGroup = root.getGroup("RADIANCE")
        # newIrradianceGroup = root.getGroup("IRRADIANCE")
        # # newAncillaryGroup = root.getGroup("ANCILLARY")

        # newRrsData = newReflectanceGroup.addDataset("Rrs")
        # newESData = newIrradianceGroup.addDataset("ES")        
        # newLIData = newRadianceGroup.addDataset("LI")
        # newLTData = newRadianceGroup.addDataset("LT") 

        # # Copy datasets to dictionary
        esData.datasetToColumns()
        esColumns = esData.columns
        tt2 = esColumns["Timetag2"]

        # liData.datasetToColumns()
        # liColumns = liData.columns        

        # ltData.datasetToColumns()
        # ltColumns = ltData.columns                    

        # # Combine these steps in a loop for ancillary date
        # ancDict = {}
        # for ds in ancGroup.datasets:
        #     key = ds            
        #     value = ancGroup.datasets[ds]            
        #     ancDict[key] = value

        # # Test
        esLength = len(list(esColumns.values())[0])
        # ltLength = len(list(ltColumns.values())[0])

        # if ltLength > esLength:
        #     print('Warning. Why would ltLength be > esLength??************************************')
        #     for col in ltColumns:
        #         col = col[0:esLength] # strips off final columns
        #     for col in liColumns:
        #         col = col[0:esLength]


        interval = float(ConfigFile.settings["fL2TimeInterval"])    
        # Break up data into time intervals, and calculate reflectance
        if interval == 0:
            # Here, take the complete time series
            print("No time binning. This can take a moment.")
            # Utilities.printProgressBar(0, esLength-1, prefix = 'Progress:', suffix = 'Complete', length = 50)
            for i in range(0, esLength-1):
                Utilities.printProgressBar(i+1, esLength-1, prefix = 'Progress:', suffix = 'Complete', length = 50)
                start = i
                end = i+1

                # esSlice = ProcessL2.columnToSlice(esColumns,start, end)
                # liSlice = ProcessL2.columnToSlice(liColumns,start, end)
                # ltSlice = ProcessL2.columnToSlice(ltColumns,start, end)

                # WINDSPEEDSlice = ProcessL2.columnToSlice(ancDict["WINDSPEED"].columns,start, end)
                # AODSlice = ProcessL2.columnToSlice(ancDict["AOD"].columns,start, end)
                # SALSlice = ProcessL2.columnToSlice(ancDict["SAL"].columns,start, end)
                # SSTSlice = ProcessL2.columnToSlice(ancDict["SST"].columns,start, end)
                # ELEVATIONSlice = ProcessL2.columnToSlice(ancDict["ELEVATION"].columns,start, end)


                # The reflectance needs to be calculated with the individual unaveraged radiometric and ancillary data
                # Use model (SST) over Pyrometer (WATER_TEMP) until I can figure out the pyrometer issue
                if not ProcessL2.calculateREFLECTANCE2(root, sasGroup, referenceGroup, ancGroup, start, end):
                    # msg = 'Slice failed. Skipping.'
                    # print(msg)
                    # Utilities.writeLogFile(msg)                      
                    continue
                
                # Take the slice median of ancillary data and add it to appropriate groups
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')

                    # ProcessL2.sliceAverageAncillary(start, end, newESData, gpsCourseColumns, newGPSCourseData, gpsLatPosColumns, newGPSLatPosData, \
                    #     gpsLonPosColumns, newGPSLonPosData, None, None, gpsSpeedColumns, newGPSSpeedData, \
                    #     satnavAzimuthColumns, newSATNAVAzimuthData, satnavElevationColumns, newSATNAVElevationData, satnavHeadingColumns, \
                    #     newSATNAVHeadingData, satnavPointingColumns, newSATNAVPointingData, satnavRelAzColumns, newSATNAVRelAzData, \
                    #     pyrColumns, newPyrData)                
                            

        else:
            start = 0
            endTime = Utilities.timeTag2ToSec(tt2[0]) + interval
            for i in range(0, esLength):
                time = Utilities.timeTag2ToSec(tt2[i])
                if time > endTime: # end of increment reached
                    endTime = time + interval # increment for the next bin loop
                    # end = i-1
                    end = i # end of the slice is up to and not including...so -1 is not needed
                    # # Here take one interval as defined in Config
                    # esSlice = ProcessL2.columnToSlice(esColumns, start, end)
                    # liSlice = ProcessL2.columnToSlice(liColumns, start, end)
                    # ltSlice = ProcessL2.columnToSlice(ltColumns, start, end)

                    # WINDSPEEDSlice = ProcessL2.columnToSlice(ancDict["WINDSPEED"].columns,start, end)
                    # AODSlice = ProcessL2.columnToSlice(ancDict["AOD"].columns,start, end)
                    # SALSlice = ProcessL2.columnToSlice(ancDict["SAL"].columns,start, end)
                    # SSTSlice = ProcessL2.columnToSlice(ancDict["SST"].columns,start, end)
                    # ELEVATIONSlice = ProcessL2.columnToSlice(ancDict["ELEVATION"].columns,start, end)

                    # The reflectance needs to be calculated with the individual unaveraged radiometric and ancillary data
                    # Use model (SST) over Pyrometer (WATER_TEMP) until I can figure out the pyrometer issue
                    if not ProcessL2.calculateREFLECTANCE2(root, sasGroup, referenceGroup, ancGroup, start, end):
                        # msg = 'Slice failed. Skipping.'
                        # print(msg)
                        # Utilities.writeLogFile(msg)  
                        start = i                        
                        continue

                    # Take the slice median of ancillary data and add it to appropriate groups
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')

                        # ProcessL2.sliceAverageAncillary(start, end, newESData, gpsCourseColumns, newGPSCourseData, gpsLatPosColumns, newGPSLatPosData, \
                        #     gpsLonPosColumns, newGPSLonPosData, None, None, gpsSpeedColumns, newGPSSpeedData, \
                        #     satnavAzimuthColumns, newSATNAVAzimuthData, satnavElevationColumns, newSATNAVElevationData, satnavHeadingColumns, \
                        #     newSATNAVHeadingData, satnavPointingColumns, newSATNAVPointingData, satnavRelAzColumns, newSATNAVRelAzData, \
                        #     pyrColumns, newPyrData)           
                    start = i

            # Try converting any remaining
            end = esLength-1
            time = Utilities.timeTag2ToSec(tt2[end])
            if time < endTime:
                # esSlice = ProcessL2.columnToSlice(esColumns, start, end)
                # liSlice = ProcessL2.columnToSlice(liColumns, start, end)
                # ltSlice = ProcessL2.columnToSlice(ltColumns, start, end)

                # WINDSPEEDSlice = ProcessL2.columnToSlice(ancDict["WINDSPEED"].columns,start, end)
                # AODSlice = ProcessL2.columnToSlice(ancDict["AOD"].columns,start, end)
                # SALSlice = ProcessL2.columnToSlice(ancDict["SAL"].columns,start, end)
                # SSTSlice = ProcessL2.columnToSlice(ancDict["SST"].columns,start, end)
                # ELEVATIONSlice = ProcessL2.columnToSlice(ancDict["ELEVATION"].columns,start, end)

                # The reflectance needs to be calculated with the individual unaveraged radiometric and ancillary data
                # Use model (SST) over Pyrometer (WATER_TEMP) until I can figure out the pyrometer issue
                if not ProcessL2.calculateREFLECTANCE2(root,sasGroup, referenceGroup, ancGroup, start, end):
                    # Take the slice median of ancillary data and add it to appropriate groups
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')

                        # ProcessL2.sliceAverageAncillary(start, end, newESData, gpsCourseColumns, newGPSCourseData, gpsLatPosColumns, newGPSLatPosData, \
                        #     gpsLonPosColumns, newGPSLonPosData, None, None, gpsSpeedColumns, newGPSSpeedData, \
                        #     satnavAzimuthColumns, newSATNAVAzimuthData, satnavElevationColumns, newSATNAVElevationData, satnavHeadingColumns, \
                        #     newSATNAVHeadingData, satnavPointingColumns, newSATNAVPointingData, satnavRelAzColumns, newSATNAVRelAzData, \
                        #     pyrColumns, newPyrData)           


        
 
        return True


    # Calculates Rrs
    @staticmethod
    def processL2(node, ancillaryData=None):

        root = HDFRoot.HDFRoot()
        root.copyAttributes(node)
        root.attributes["PROCESSING_LEVEL"] = "2"

        root.addGroup("REFLECTANCE")
        root.addGroup("IRRADIANCE")
        root.addGroup("RADIANCE")    

        pyrGroup = None
        gpsGroup = None
        satnavGroup = None
        for gp in node.groups:
            if gp.id.startswith("GPS"):
                gpsGroup = gp
            if gp.id == ("SOLARTRACKER"):
                satnavGroup = gp
            # if gp.id == ("SOLARTRACKER_STATUS"):
            #     satnavGroup = gp            
            if gp.id.startswith("PYROMETER"):
                pyrGroup = gp

        if satnavGroup is not None or gpsGroup is not None or pyrGroup is not None:
            node.addGroup("ANCILLARY")
            root.addGroup("ANCILLARY")
        # if pyrGroup is not None:
        #     root.addGroup("PYROMETER")    

        # Retrieve MERRA2 model ancillary data        
        if ConfigFile.settings["bL2pGetAnc"] ==1:            
            msg = 'Model data for Wind and AOD may be used to replace blank values. Reading in model data...'
            print(msg)
            Utilities.writeLogFile(msg)  
            modData = GetAnc.getAnc(gpsGroup)
        else:
            modData = None


        # Need to either create a new ancData object, or populate the nans in the current one with the model data
        if not ProcessL2.calculateREFLECTANCE(root, node, gpsGroup, satnavGroup, pyrGroup, ancillaryData, modData):
            return None

        root.attributes["Rrs_UNITS"] = "sr^-1"
        
        # Check to insure at least some data survived quality checks
        if root.getGroup("REFLECTANCE").getDataset("Rrs").data is None:
            msg = "All data appear to have been eliminated from the file. Aborting."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None

        return root
