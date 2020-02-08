
import collections
import sys
import warnings

import numpy as np
from numpy import matlib as mb
import scipy as sp
import datetime as dt
from PyQt5 import QtWidgets

import HDFRoot
from Utilities import Utilities
from ConfigFile import ConfigFile
from RhoCorrections import RhoCorrections
from GetAnc import GetAnc
from SB_support import readSB
from Weight_RSR import Weight_RSR


class ProcessL2:

    # Delete records within the out-of-bounds SZA
    @staticmethod
    def filterData(group, badTimes):                    
        
        # Now delete the record from each dataset in the group
        finalCount = 1 # simpler than getting dataset len...
        for timeTag in badTimes:

            # msg = f'Eliminate data between: {timeTag} (HHMMSSMSS)'
            # print(msg)
            # Utilities.writeLogFile(msg)        
            start = Utilities.timeTag2ToSec(timeTag[0])
            stop = Utilities.timeTag2ToSec(timeTag[1])                
                    
            # msg = f'   Remove {group.id}  Data'
            # print(msg)
            # Utilities.writeLogFile(msg)
            if group.id == "ANCILLARY":
                # Early on, Date/Timetags are not appended, but later they are
                if group.getDataset("Timetag2"):
                    timeData = group.getDataset("Timetag2").data["Timetag2"]                
                else:
                    timeData = group.getDataset("AOD").data["Timetag2"]
            if group.id == "IRRADIANCE":
                timeData = group.getDataset("ES").data["Timetag2"]
            if group.id == "RADIANCE":
                timeData = group.getDataset("LI").data["Timetag2"]
            if group.id == "REFLECTANCE":
                timeData = group.getDataset("Rrs").data["Timetag2"]

            dataSec = []
            for i in range(timeData.shape[0]):
                # Converts from TT2 (hhmmssmss. UTC) to milliseconds UTC
                dataSec.append(Utilities.timeTag2ToSec(timeData[i])) 

            lenDataSec = len(dataSec)
            counter = 0
            for i in range(lenDataSec):
                if start <= dataSec[i] and stop >= dataSec[i]:                        
                    # test = group.getDataset("Timetag2").data["NONE"][i - counter]                                            
                    group.datasetDeleteRow(i - counter)  # Adjusts the index for the shrinking arrays
                    counter += 1

            if i-counter == -1:
                finalCount = 0

        for ds in group.datasets: group.datasets[ds].datasetToColumns()
        return finalCount

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

    
    @staticmethod
    def specQualityCheck(group, inFilePath):
        ''' Perform spectral filtering
        Calculate the STD of the normalized (at some max value) average ensemble.
        Then test each normalized spectrum against the ensemble average and STD.
        Plot results'''

        badTimes = []
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
        
        if len(badTimes) == 0:
            badTimes = None
        return badTimes
        

    # Perform Lt Quality checking
    @staticmethod
    def ltQuality(sasGroup):   
        
        ltData = sasGroup.getDataset("LT")
        ltData.datasetToColumns()
        ltColumns = ltData.columns
        ltColumns.pop('Datetag')
        ltTime = ltColumns.pop('Timetag2')
                        
        badTimes = []
        for indx, timeTag in enumerate(ltTime):                        
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
                badTimes.append(timeTag)
        
        badTimes = np.unique(badTimes)
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) # Duplicates each element to a list of two elements in a list
        msg = f'{len(np.unique(badTimes))/len(ltTime)*100:.1f}% of spectra flagged'
        print(msg)
        Utilities.writeLogFile(msg) 

        if len(badTimes) == 0:
            badTimes = None
        return badTimes

    # Perform negative reflectance spectra checking
    @staticmethod
    def negReflectance(reflGroup,field):   
        # Run for entire file, not just this ensemble

        reflData = reflGroup.getDataset(field)
        # reflData.datasetToColumns()
        reflColumns = reflData.columns
        reflDate = reflColumns.pop('Datetag')
        reflTime = reflColumns.pop('Timetag2')
                        
        badTimes = []
        for indx, timeTag in enumerate(reflTime):                        
            # If any spectra in the vis are negative, delete the whole spectrum
            VIS = [400,700]            
            reflVIS = []
            wavelengths = []
            for wave in reflColumns:
                wavelengths.append(float(wave))
                if float(wave) > VIS[0] and float(wave) < VIS[1]:
                    reflVIS.append(reflColumns[wave][indx])
                # elif float(wave) > NIR[0] and float(wave) < NIR[1]:
                #     ltNIR.append(ltColumns[wave][indx])

            # Flag entire record for removal
            if any(item < 0 for item in reflVIS):
                badTimes.append(timeTag)

            # Set negatives to 0
            NIR = [701,max(wavelengths)]
            UV = [min(wavelengths),399]
            for wave in reflColumns:
                if ((float(wave) >= UV[0] and float(wave) < UV[1]) or \
                            (float(wave) >= NIR[0] and float(wave) < NIR[1])) and \
                            reflColumns[wave][indx] < 0:
                    reflColumns[wave][indx] = 0
                            
        badTimes = np.unique(badTimes)
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) # Duplicates each element to a list of two elements (start, stop)
        msg = f'{len(np.unique(badTimes))/len(reflTime)*100:.1f}% of {field} spectra flagged'
        print(msg)
        Utilities.writeLogFile(msg) 

        # Need to add these at the beginning of the ODict
        reflColumns['Datetag'] = reflDate
        reflColumns['Timetag2'] = reflTime
        reflColumns.move_to_end('Timetag2', last=False)
        reflColumns.move_to_end('Datetag', last=False)

        reflData.columnsToDataset()        

        if len(badTimes) == 0:
            badTimes = None
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
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) # Duplicates each element to a list of two elements in a list
        msg = f'{len(np.unique(badTimes))/len(esTime)*100:.1f}% of spectra flagged'
        print(msg)
        Utilities.writeLogFile(msg) 

        if len(badTimes) == 0:
            badTimes = None
        return badTimes


    # Take a slice of a dataset stored in columns
    @staticmethod
    def columnToSlice(columns, start, end):
        # Each column is a time series either at a waveband for radiometer columns, or various grouped datasets for ancillary
        # Start and end are defined by the interval established in the Config (they are indexes)
        newSlice = collections.OrderedDict()
        for k in columns:
            newSlice[k] = columns[k][start:end+1] #up to not including end+1...
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
            # These are the entire ancillary records for the cruise
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
            for i, value in enumerate(ancInRadSeconds): # step through InRad...
                idx = Utilities.find_nearest(ancSeconds,value) # ...identify from entire anc record...
                # Make sure the time difference between field anc and rad is <= 1hr
                if abs(ancSeconds[idx] - value)/60/60 < 1:  # ... and place nearest into InRad
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
                    # msg = 'Replacing wind with model data'
                    # print(msg)
                    # Utilities.writeLogFile(msg)
                    idx = Utilities.find_nearest(modSeconds,ancInRadSeconds[i])
                    windInRad[i] = modData.groups[0].datasets['Wind'][idx]   
                    windFlag[i] = 'model'                     
            for i, value in enumerate(aodInRad):
                if np.isnan(value):
                    # msg = 'Replacing AOD with model data'
                    # print(msg)
                    # Utilities.writeLogFile(msg)
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
    def sliceAveHyper(y, hyperSlice, xSlice, xStd):
        hasNan = False
        # Ignore runtime warnings when array is all NaNs
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            for k in hyperSlice: # each k is a time series at a waveband.
                v = [hyperSlice[k][i] for i in y] # selects the lowest 5% within the interval window...
                mean = np.nanmean(v) # ... and averages them
                std = np.nanstd(v) # ... and the stdev for uncertainty estimates
                xSlice[k] = [mean]
                xStd[k] = [std]
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

        # dateSlice = ProcessL2.columnToSlice(ancDict['Datetag'].columns, start, end)
        # timeSlice = ProcessL2.columnToSlice(ancDict['Timetag2'].columns, start, end)
        # datetag = ancDict['Datetag'].data
        # timetag = ancDict['Timetag2'].data
        # datetag = np.array(dateSlice['Datetag'])
        # timetag = np.array(timeSlice['Timetag2'])
        dateSlice=ancDict['Datetag'].data[start:end+1] #up to not including end+1
        timeSlice=ancDict['Timetag2'].data[start:end+1]
        # Stores the middle element
        # if len(datetag) > 0:
        #     date = datetag[int(len(datetag)/2)]
        #     time = timetag[int(len(timetag)/2)]
        if len(dateSlice) > 0:
            date = dateSlice[int(len(dateSlice)/2)]
            time = timeSlice[int(len(timeSlice)/2)]

        for ds in ancDict: 
            if ds != 'Datetag' and ds != 'Timetag2':
                if not newAncGroup.getDataset(ds):
                    newDS = newAncGroup.addDataset(ds)
                else:
                    newDS = newAncGroup.getDataset(ds)

                dsSlice = ProcessL2.columnToSlice(ancDict[ds].columns,start, end)                
                dsXSlice = None

                for subset in dsSlice: # several ancillary datasets are groups which will become columns (including date, time, and flags)
                    if subset != 'Datetag' and subset != 'Timetag2':
                        v = [dsSlice[subset][i] for i in y] # y is an array of indexes for the lowest X%

                        if dsXSlice is None:
                            dsXSlice = collections.OrderedDict()                        
                            dsXSlice['Datetag'] = date.tolist()
                            dsXSlice['Timetag2'] = time.tolist()
                            # dsXSlice['Datetag'] = date
                            # dsXSlice['Timetag2'] = time

                        if subset.endswith('FLAG'):
                            if not subset in dsXSlice:
                                # Find the most frequest element
                                dsXSlice[subset] = []
                            dsXSlice[subset].append(Utilities.mostFrequent(v))
                        else:
                            if subset not in dsXSlice:
                                dsXSlice[subset] = []                            
                            dsXSlice[subset].append(np.mean(v)) 
                        
                if subset not in newDS.columns:
                    newDS.columns = dsXSlice
                else:
                    for item in newDS.columns:
                        newDS.columns[item] = np.append(newDS.columns[item], dsXSlice[item])

            
                newDS.columnsToDataset()            
       
    @staticmethod
    def calculateREFLECTANCE2(root, sasGroup, refGroup, ancGroup, start, end):
        '''Calculate the lowest X% Lt(780). Check for Nans in Li, Lt, Es, or wind. Send out for meteorological quality flags, 
        Perform rho correction with wind. Calculate the Rrs. Correct for NIR.'''

        def dop(year):
            # day of perihelion            
            years = list(range(2001,2031))
            key = [str(x) for x in years]
            day = [4, 2, 4, 4, 2, 4, 3, 2, 4, 3, 3, 5, 2, 4, 4, 2, 4, 3, 3, 5, 2, 4, 4, 3, 4, 3, 3, 5, 2, 3]            
            dop = {key[i]: day[i] for i in range(0, len(key))}            
            result = dop[str(year)]
            return result

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

        # Test whether this is the first ensemble spectrum
        if not ('Rrs' in newReflectanceGroup.datasets):
            newRrsData = newReflectanceGroup.addDataset("Rrs")            
            newESData = newIrradianceGroup.addDataset("ES")        
            newLIData = newRadianceGroup.addDataset("LI")
            newLTData = newRadianceGroup.addDataset("LT") 
            newnLwData = newReflectanceGroup.addDataset("nLw")            

            newRrsDeltaData = newReflectanceGroup.addDataset("Rrs_delta")            
            newESDeltaData = newIrradianceGroup.addDataset("ES_delta")       
            newLIDeltaData = newRadianceGroup.addDataset("LI_delta")
            newLTDeltaData = newRadianceGroup.addDataset("LT_delta")
            newnLwDeltaData = newReflectanceGroup.addDataset("nLw_delta")

            if ConfigFile.settings['bL2WeightMODISA']:
                newRrsMODISAData = newReflectanceGroup.addDataset("Rrs_MODISA")
                newRrsMODISADeltaData = newReflectanceGroup.addDataset("Rrs_MODISA_delta")
                newnLwMODISAData = newReflectanceGroup.addDataset("nLw_MODISA")
                newnLwMODISADeltaData = newReflectanceGroup.addDataset("nLw_MODISA_delta")
            if ConfigFile.settings['bL2WeightMODIST']:
                newRrsMODISTData = newReflectanceGroup.addDataset("Rrs_MODIST")
                newRrsMODISTDeltaData = newReflectanceGroup.addDataset("Rrs_MODIST_delta")
                newnLwMODISTData = newReflectanceGroup.addDataset("nLw_MODIST")
                newnLwMODISTDeltaData = newReflectanceGroup.addDataset("nLw_MODIST_delta")

            if ConfigFile.settings['bL2WeightVIIRSN']:
                newRrsVIIRSNData = newReflectanceGroup.addDataset("Rrs_VIIRSN")
                newRrsVIIRSNDeltaData = newReflectanceGroup.addDataset("Rrs_VIIRSN_delta")
                newnLwVIIRSNData = newReflectanceGroup.addDataset("nLw_VIIRSN")
                newnLwVIIRSNDeltaData = newReflectanceGroup.addDataset("nLw_VIIRSN_delta")
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                newRrsVIIRSJData = newReflectanceGroup.addDataset("Rrs_VIIRSJ")
                newRrsVIIRSJDeltaData = newReflectanceGroup.addDataset("Rrs_VIIRSJ_delta")
                newnLwVIIRSJData = newReflectanceGroup.addDataset("nLw_VIIRSJ")
                newnLwVIIRSJDeltaData = newReflectanceGroup.addDataset("nLw_VIIRSJ_delta")

            if ConfigFile.settings['bL2WeightSentinel3A']:
                newRrsSentinel3AData = newReflectanceGroup.addDataset("Rrs_Sentinel3A")
                newRrsSentinel3ADeltaData = newReflectanceGroup.addDataset("Rrs_Sentinel3A_delta")
                newnLwSentinel3AData = newReflectanceGroup.addDataset("nLw_Sentinel3A")
                newnLwSentinel3ADeltaData = newReflectanceGroup.addDataset("nLw_Sentinel3A_delta")
            if ConfigFile.settings['bL2WeightSentinel3B']:
                newRrsSentinel3BData = newReflectanceGroup.addDataset("Rrs_Sentinel3B")
                newRrsSentinel3BDeltaData = newReflectanceGroup.addDataset("Rrs_Sentinel3B_delta")
                newnLwSentinel3BData = newReflectanceGroup.addDataset("nLw_Sentinel3B")
                newnLwSentinel3BDeltaData = newReflectanceGroup.addDataset("nLw_Sentinel3B_delta")
        else:
            newRrsData = newReflectanceGroup.getDataset("Rrs")
            newESData = newIrradianceGroup.getDataset("ES")        
            newLIData = newRadianceGroup.getDataset("LI")
            newLTData = newRadianceGroup.getDataset("LT") 
            newnLwData = newReflectanceGroup.getDataset("nLw")

            newRrsDeltaData = newReflectanceGroup.getDataset("Rrs_delta")
            newESDeltaData = newIrradianceGroup.getDataset("ES_delta")    
            newLIDeltaData = newRadianceGroup.getDataset("LI_delta")
            newLTDeltaData = newRadianceGroup.getDataset("LT_delta")
            newnLwDeltaData = newReflectanceGroup.getDataset("nLw_delta")

            if ConfigFile.settings['bL2WeightMODISA']:
                newRrsMODISAData = newReflectanceGroup.getDataset("Rrs_MODISA")
                newRrsMODISADeltaData = newReflectanceGroup.getDataset("Rrs_MODISA_delta")
                newnLwMODISAData = newReflectanceGroup.getDataset("nLw_MODISA")
                newnLwMODISADeltaData = newReflectanceGroup.getDataset("nLw_MODISA_delta")
            if ConfigFile.settings['bL2WeightMODIST']:
                newRrsMODISTData = newReflectanceGroup.getDataset("Rrs_MODIST")
                newRrsMODISTDeltaData = newReflectanceGroup.getDataset("Rrs_MODIST_delta")
                newnLwMODISTData = newReflectanceGroup.getDataset("nLw_MODIST")
                newnLwMODISTDeltaData = newReflectanceGroup.getDataset("nLw_MODIST_delta")

            if ConfigFile.settings['bL2WeightVIIRSN']:
                newRrsVIIRSNData = newReflectanceGroup.getDataset("Rrs_VIIRSN")
                newRrsVIIRSNDeltaData = newReflectanceGroup.getDataset("Rrs_VIIRSN_delta")
                newnLwVIIRSNData = newReflectanceGroup.getDataset("nLw_VIIRSN")
                newnLwVIIRSNDeltaData = newReflectanceGroup.getDataset("nLw_VIIRSN_delta")
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                newRrsVIIRSJData = newReflectanceGroup.getDataset("Rrs_VIIRSJ")
                newRrsVIIRSJDeltaData = newReflectanceGroup.getDataset("Rrs_VIIRSJ_delta")
                newnLwVIIRSJData = newReflectanceGroup.getDataset("nLw_VIIRSJ")
                newnLwVIIRSJDeltaData = newReflectanceGroup.getDataset("nLw_VIIRSJ_delta")

            if ConfigFile.settings['bL2WeightSentinel3A']:
                newRrsSentinel3AData = newReflectanceGroup.getDataset("Rrs_Sentinel3A")
                newRrsSentinel3ADeltaData = newReflectanceGroup.getDataset("Rrs_Sentinel3A_delta")
                newnLwSentinel3AData = newReflectanceGroup.getDataset("nLw_Sentinel3A")
                newnLwSentinel3ADeltaData = newReflectanceGroup.getDataset("nLw_Sentinel3A_delta")
            if ConfigFile.settings['bL2WeightSentinel3B']:
                newRrsSentinel3BData = newReflectanceGroup.getDataset("Rrs_Sentinel3B")
                newRrsSentinel3BDeltaData = newReflectanceGroup.getDataset("Rrs_Sentinel3B_delta")
                newnLwSentinel3BData = newReflectanceGroup.getDataset("nLw_Sentinel3B")
                newnLwSentinel3BDeltaData = newReflectanceGroup.getDataset("nLw_Sentinel3B_delta")

        esSlice = ProcessL2.columnToSlice(esColumns,start, end)
        liSlice = ProcessL2.columnToSlice(liColumns,start, end)
        ltSlice = ProcessL2.columnToSlice(ltColumns,start, end)
        n = len(list(ltSlice.values())[0])
    
        rhoDefault = float(ConfigFile.settings["fL2RhoSky"])
        RuddickRho = int(ConfigFile.settings["bL2RuddickRho"])
        ZhangRho = int(ConfigFile.settings["bL2ZhangRho"])
        # defaultWindSpeed = float(ConfigFile.settings["fL2DefaultWindSpeed"])
        # windSpeedMean = defaultWindSpeed # replaced later with met file, if present                         
        simpleNIRCorrection = int(ConfigFile.settings["bL2SimpleNIRCorrection"])
        simSpecNIRCorrection = int(ConfigFile.settings["bL2SimSpecNIRCorrection"])                        
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
        x = round(n*percentLt/100) # number of retained values
        msg = f'{n} spectra in slice (ensemble).'
        print(msg)
        Utilities.writeLogFile(msg)
        
        # IS THIS NECESSARY?
        # ...There are often few data points, and given 10% of 10 points is just one data point...(?)
        if n <= 5 or x == 0:
            x = n # if only 5 or fewer records retained, use them all...
        
        # Find the indexes for the lowest X%
        lt780 = ProcessL2.interpolateColumn(ltSlice, 780.0)
        index = np.argsort(lt780) # gives indexes if values were to be sorted
                
        if enablePercentLt:
            # returns indexes of the first x values (if values were sorted); i.e. the indexes of the lowest X% of unsorted lt780
            y = index[0:x] 
            msg = f'{len(y)} spectra remaining in slice to average after filtering to lowest {percentLt}%.'
            print(msg)
            Utilities.writeLogFile(msg)
        else:
            y = index # If Percent Lt is turned off, this will average the whole slice

        # Take the mean of the lowest X%
        esXSlice = collections.OrderedDict()
        liXSlice = collections.OrderedDict()
        ltXSlice = collections.OrderedDict()  
        esXstd = collections.OrderedDict()  
        liXstd = collections.OrderedDict()  
        ltXstd = collections.OrderedDict()  

        hasNan = ProcessL2.sliceAveHyper(y, esSlice, esXSlice, esXstd)
        hasNan = ProcessL2.sliceAveHyper(y, liSlice, liXSlice, liXstd)
        hasNan = ProcessL2.sliceAveHyper(y, ltSlice, ltXSlice, ltXstd)

        # Slice average the ancillary group for the slice and the X% criteria
        ProcessL2.sliceAveAnc(root, start, end, y, ancGroup)
        newAncGroup = root.getGroup("ANCILLARY") # Just populated above
        newAncGroup.attributes['Ancillary_Flags (0, 1, 2, 3)'] = ['undetermined','field','model','default']

        WINDSPEEDXSlice = newAncGroup.getDataset('WINDSPEED').data['WINDSPEED'][-1].copy() # Returns the last element (latest slice)
        if isinstance(WINDSPEEDXSlice, list):
            WINDSPEEDXSlice = WINDSPEEDXSlice[0]
        AODXSlice = newAncGroup.getDataset('AOD').data['AOD'][-1].copy()
        if isinstance(AODXSlice, list):
            AODXSlice = AODXSlice[0]
        ''' Fix '''
        # CloudXSlice = newAncGroup.getDataset('CLOUD').data['CLOUD']        
        CloudXSlice = 50 # %
        SOL_ELXSlice = newAncGroup.getDataset('ELEVATION').data['SUN'][-1].copy()
        if isinstance(SOL_ELXSlice, list):
            SOL_ELXSlice = SOL_ELXSlice[0]
        SSTXSlice = newAncGroup.getDataset('SST').data['SST'][-1].copy()
        if isinstance(SSTXSlice, list):
            SSTXSlice = SSTXSlice[0]
        SalXSlice = newAncGroup.getDataset('SAL').data['SAL'][-1].copy()
        if isinstance(SalXSlice, list):
            SalXSlice = SalXSlice[0]
        RelAzXSlice = newAncGroup.getDataset('REL_AZ').data['REL_AZ'][-1].copy()
        if isinstance(RelAzXSlice, list):
            RelAzXSlice = RelAzXSlice[0]
       
        if hasNan:            
            msg = 'ProcessL2.calculateREFLECTANCE2: Slice X"%" average error: Dataset all NaNs.'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        # Add date/time data to Rrs dataset; If this is the first spectrum, add, otherwise append
        if not ("Datetag" in newRrsData.columns):
            newESData.columns["Datetag"] = [date]
            newLIData.columns["Datetag"] = [date]
            newLTData.columns["Datetag"] = [date]
            newRrsData.columns["Datetag"] = [date]
            newnLwData.columns["Datetag"] = [date]
            newESData.columns["Timetag2"] = [time]
            newLIData.columns["Timetag2"] = [time]
            newLTData.columns["Timetag2"] = [time]
            newRrsData.columns["Timetag2"] = [time]
            newnLwData.columns["Timetag2"] = [time]

            newESDeltaData.columns["Datetag"] = [date]
            newLIDeltaData.columns["Datetag"] = [date]
            newLTDeltaData.columns["Datetag"] = [date]
            newRrsDeltaData.columns["Datetag"] = [date]
            newnLwDeltaData.columns["Datetag"] = [date]
            newESDeltaData.columns["Timetag2"] = [time]
            newLIDeltaData.columns["Timetag2"] = [time]
            newLTDeltaData.columns["Timetag2"] = [time]
            newRrsDeltaData.columns["Timetag2"] = [time]
            newnLwDeltaData.columns["Timetag2"] = [time]

            if ConfigFile.settings['bL2WeightMODISA']:
                newRrsMODISAData.columns["Timetag2"] = [time]
                newRrsMODISADeltaData.columns["Timetag2"] = [time]
                newnLwMODISAData.columns["Timetag2"] = [time]
                newnLwMODISADeltaData.columns["Timetag2"] = [time]
                newRrsMODISAData.columns["Datetag"] = [date]
                newRrsMODISADeltaData.columns["Datetag"] = [date]
                newnLwMODISAData.columns["Datetag"] = [date]
                newnLwMODISADeltaData.columns["Datetag"] = [date]
            if ConfigFile.settings['bL2WeightMODIST']:
                newRrsMODISTData.columns["Timetag2"] = [time]
                newRrsMODISTDeltaData.columns["Timetag2"] = [time]
                newnLwMODISTData.columns["Timetag2"] = [time]
                newnLwMODISTDeltaData.columns["Timetag2"] = [time]
                newRrsMODISTData.columns["Datetag"] = [date]
                newRrsMODISTDeltaData.columns["Datetag"] = [date]
                newnLwMODISTData.columns["Datetag"] = [date]
                newnLwMODISTDeltaData.columns["Datetag"] = [date]

            if ConfigFile.settings['bL2WeightVIIRSN']:
                newRrsVIIRSNData.columns["Timetag2"] = [time]
                newRrsVIIRSNDeltaData.columns["Timetag2"] = [time]
                newnLwVIIRSNData.columns["Timetag2"] = [time]
                newnLwVIIRSNDeltaData.columns["Timetag2"] = [time]
                newRrsVIIRSNData.columns["Datetag"] = [date]
                newRrsVIIRSNDeltaData.columns["Datetag"] = [date]
                newnLwVIIRSNData.columns["Datetag"] = [date]
                newnLwVIIRSNDeltaData.columns["Datetag"] = [date]
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                newRrsVIIRSJData.columns["Timetag2"] = [time]
                newRrsVIIRSJDeltaData.columns["Timetag2"] = [time]
                newnLwVIIRSJData.columns["Timetag2"] = [time]
                newnLwVIIRSJDeltaData.columns["Timetag2"] = [time]
                newRrsVIIRSJData.columns["Datetag"] = [date]
                newRrsVIIRSJDeltaData.columns["Datetag"] = [date]
                newnLwVIIRSJData.columns["Datetag"] = [date]
                newnLwVIIRSJDeltaData.columns["Datetag"] = [date]


            if ConfigFile.settings['bL2WeightSentinel3A']:
                newRrsSentinel3AData.columns["Timetag2"] = [time]
                newRrsSentinel3ADeltaData.columns["Timetag2"] = [time]
                newnLwSentinel3AData.columns["Timetag2"] = [time]
                newnLwSentinel3ADeltaData.columns["Timetag2"] = [time]
                newRrsSentinel3AData.columns["Datetag"] = [date]
                newRrsSentinel3ADeltaData.columns["Datetag"] = [date]
                newnLwSentinel3AData.columns["Datetag"] = [date]
                newnLwSentinel3ADeltaData.columns["Datetag"] = [date]
            if ConfigFile.settings['bL2WeightSentinel3B']:
                newRrsSentinel3BData.columns["Timetag2"] = [time]
                newRrsSentinel3BDeltaData.columns["Timetag2"] = [time]
                newnLwSentinel3BData.columns["Timetag2"] = [time]
                newnLwSentinel3BDeltaData.columns["Timetag2"] = [time]
                newRrsSentinel3BData.columns["Datetag"] = [date]
                newRrsSentinel3BDeltaData.columns["Datetag"] = [date]
                newnLwSentinel3BData.columns["Datetag"] = [date]
                newnLwSentinel3BDeltaData.columns["Datetag"] = [date]            
        else:
            newESData.columns["Datetag"].append(date)
            newLIData.columns["Datetag"].append(date)
            newLTData.columns["Datetag"].append(date)
            newRrsData.columns["Datetag"].append(date)
            newnLwData.columns["Datetag"].append(date)
            newESData.columns["Timetag2"].append(time)
            newLIData.columns["Timetag2"].append(time)
            newLTData.columns["Timetag2"].append(time)
            newRrsData.columns["Timetag2"].append(time)           
            newnLwData.columns["Timetag2"].append(time)

            newESDeltaData.columns["Datetag"].append(date)
            newLIDeltaData.columns["Datetag"].append(date)
            newLTDeltaData.columns["Datetag"].append(date)
            newRrsDeltaData.columns["Datetag"].append(date)
            newnLwDeltaData.columns["Datetag"].append(date)
            newESDeltaData.columns["Timetag2"].append(time)
            newLIDeltaData.columns["Timetag2"].append(time)
            newLTDeltaData.columns["Timetag2"].append(time)
            newRrsDeltaData.columns["Timetag2"].append(time)
            newnLwDeltaData.columns["Timetag2"].append(time)

            if ConfigFile.settings['bL2WeightMODISA']:
                newRrsMODISAData.columns["Timetag2"].append(time)
                newRrsMODISADeltaData.columns["Timetag2"].append(time)
                newnLwMODISAData.columns["Timetag2"].append(time)
                newnLwMODISADeltaData.columns["Timetag2"].append(time)
                newRrsMODISAData.columns["Datetag"].append(date)
                newRrsMODISADeltaData.columns["Datetag"].append(date)
                newnLwMODISAData.columns["Datetag"].append(date)
                newnLwMODISADeltaData.columns["Datetag"].append(date)
            if ConfigFile.settings['bL2WeightMODIST']:
                newRrsMODISTData.columns["Timetag2"].append(time)
                newRrsMODISTDeltaData.columns["Timetag2"].append(time)
                newnLwMODISTData.columns["Timetag2"].append(time)
                newnLwMODISTDeltaData.columns["Timetag2"].append(time)
                newRrsMODISTData.columns["Datetag"].append(date)
                newRrsMODISTDeltaData.columns["Datetag"].append(date)
                newnLwMODISTData.columns["Datetag"].append(date)
                newnLwMODISTDeltaData.columns["Datetag"].append(date)

            if ConfigFile.settings['bL2WeightVIIRSN']:
                newRrsVIIRSNData.columns["Timetag2"].append(time)
                newRrsVIIRSNDeltaData.columns["Timetag2"].append(time)
                newnLwVIIRSNData.columns["Timetag2"].append(time)
                newnLwVIIRSNDeltaData.columns["Timetag2"].append(time)
                newRrsVIIRSNData.columns["Datetag"].append(date)
                newRrsVIIRSNDeltaData.columns["Datetag"].append(date)
                newnLwVIIRSNData.columns["Datetag"].append(date)
                newnLwVIIRSNDeltaData.columns["Datetag"].append(date)
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                newRrsVIIRSJData.columns["Timetag2"].append(time)
                newRrsVIIRSJDeltaData.columns["Timetag2"].append(time)
                newnLwVIIRSJData.columns["Timetag2"].append(time)
                newnLwVIIRSJDeltaData.columns["Timetag2"].append(time)
                newRrsVIIRSJData.columns["Datetag"].append(date)
                newRrsVIIRSJDeltaData.columns["Datetag"].append(date)
                newnLwVIIRSJData.columns["Datetag"].append(date)
                newnLwVIIRSJDeltaData.columns["Datetag"].append(date)
            
            if ConfigFile.settings['bL2WeightSentinel3A']:
                newRrsSentinel3AData.columns["Timetag2"].append(time)
                newRrsSentinel3ADeltaData.columns["Timetag2"].append(time)
                newnLwSentinel3AData.columns["Timetag2"].append(time)
                newnLwSentinel3ADeltaData.columns["Timetag2"].append(time)
                newRrsSentinel3AData.columns["Datetag"].append(date)
                newRrsSentinel3ADeltaData.columns["Datetag"].append(date)
                newnLwSentinel3AData.columns["Datetag"].append(date)
                newnLwSentinel3ADeltaData.columns["Datetag"].append(date)
            if ConfigFile.settings['bL2WeightSentinel3B']:
                newRrsSentinel3BData.columns["Timetag2"].append(time)
                newRrsSentinel3BDeltaData.columns["Timetag2"].append(time)
                newnLwSentinel3BData.columns["Timetag2"].append(time)
                newnLwSentinel3BDeltaData.columns["Timetag2"].append(time)
                newRrsSentinel3BData.columns["Datetag"].append(date)
                newRrsSentinel3BDeltaData.columns["Datetag"].append(date)
                newnLwSentinel3BData.columns["Datetag"].append(date)
                newnLwSentinel3BDeltaData.columns["Datetag"].append(date)   

        # Calculate Rho_sky
        wavebands = [*esColumns]
        wavebands.pop(0) # Datetag
        wavebands.pop(0) # Timetag2
        wave = [float(i) for i in wavebands]
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

            rhoScalar, rhoDelta = RhoCorrections.RuddickCorr(sky750, rhoDefault, WINDSPEEDXSlice)

        elif ZhangRho:     
            ''' Zhang rho is based on Zhang et al. 2017 and calculates the wavelength-dependent rho vector
            separated for sun and sky to include polarization factors.
            
            Model limitations: AOD 0 - 0.2, Solar zenith 0-60 deg, Wavelength 350-1000 nm.'''       
            rhoDict = {}
            
            # Need to limit the input for the model limitations. This will also mean cutting out Li, Lt, and Es 
            # from non-valid wavebands.
            if AODXSlice >0.2:
                msg = f'AOD = {AODXSlice}. Maximum Aerosol Optical Depth Reached. Setting to 0.2'
                print(msg)
                Utilities.writeLogFile(msg) 
                AODXSlice = 0.2
            if SOL_ELXSlice < 30:
                msg = f'SZA = {90-SOL_ELXSlice}. Maximum Solar Zenith Reached. Setting to 60'
                print(msg)
                Utilities.writeLogFile(msg) 
                SOL_ELXSlice = 30
            if min(wave) < 350 or max(wave) > 1000:
                msg = f'Wavelengths extend beyond model limits. Truncating to 350 - 1000 nm.'
                print(msg)
                Utilities.writeLogFile(msg) 
                wave_old = wave.copy()
                wave_list = [(i, band) for i, band in enumerate(wave_old) if (band >=350) and (band <= 1000)]
                wave_array = np.array(wave_list)
                wave = wave_array[:,1].tolist()
            #     wave_ind = wave_array[:,0].tolist()
            # else:
            #     wave_ind = np.arange(0,len(wave)).tolist()

            rhoStructure, rhoDelta = RhoCorrections.ZhangCorr(WINDSPEEDXSlice,AODXSlice, \
                CloudXSlice,SOL_ELXSlice,SSTXSlice,SalXSlice,RelAzXSlice,wave)
            rhoVector = rhoStructure['ρ']
            for i, k in enumerate(wave):
                rhoDict[str(k)] = rhoVector[0,i]

        rrsSlice = {}
        nLwSlice = {}
                
        # Calculate Rrs & nLw and uncertainties
        '''# No bidirectional correction is made here.....'''
        # Calculate the normalized water leaving radiance (not exact; no BRDF here)
        fp = 'Data/Thuillier_F0.sb'
        print("SB_support.readSB: " + fp)
        if not readSB(fp, no_warn=True):
            msg = "Unable to read Thuillier file. Make sure it is in SeaBASS format."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None
        else:
            Thuillier = readSB(fp, no_warn=True)
            F0_raw = np.array(Thuillier.data['esun']) # uW cm^-2 nm^-1
            wv_raw = np.array(Thuillier.data['wavelength'])
            # Earth-Sun distance
            day = int(str(datetag[0])[4:7])  
            year = int(str(datetag[0])[0:4])  
            eccentricity = 0.01672
            dayFactor = 360/365.256363
            dayOfPerihelion = dop(year)
            dES = 1-eccentricity*np.cos(dayFactor*(day-dayOfPerihelion)) # in AU
            F0_fs = F0_raw*dES

            # Map to float for interpolation
            wavelength  = list(map(float, list(esColumns.keys())[2:]))
            F0 = sp.interpolate.interp1d(wv_raw, F0_fs)(wavelength)
            # Use the strings for the dict
            wavelength = list(esColumns.keys())[2:]
            F0 = collections.OrderedDict(zip(wavelength, F0))

        deleteKey = []
        for k in esXSlice: # loop through wavebands as key 'k'
            if (k in liXSlice) and (k in ltXSlice):
                if k not in newESData.columns:
                    newESData.columns[k] = []
                    newLIData.columns[k] = []
                    newLTData.columns[k] = []
                    newRrsData.columns[k] = []
                    newnLwData.columns[k] = []

                    newESDeltaData.columns[k] = []
                    newLIDeltaData.columns[k] = []
                    newLTDeltaData.columns[k] = []
                    newRrsDeltaData.columns[k] = []
                    newnLwDeltaData.columns[k] = []

                # At this waveband (k)
                es = esXSlice[k][0]
                li = liXSlice[k][0]
                lt = ltXSlice[k][0]
                f0  = F0[k]

                esDelta = esXstd[k][0]
                liDelta = liXstd[k][0]
                ltDelta = ltXstd[k][0]

                # Calculate the remote sensing reflectance
                if RuddickRho:                    
                    rrs = (lt - (rhoScalar * li)) / es

                    # Rrs uncertainty
                    rrsDelta = rrs * ( 
                            (liDelta/li)**2 + (rhoDelta/rhoScalar)**2 + (liDelta/li)**2 + (esDelta/es)**2 
                            )**0.5
                
                    #Calculate the normalized water leaving radiance
                    nLw = rrs*f0

                    # nLw uncertainty; no provision for F0 uncertainty here
                    nLwDelta = nLw * (
                            (liDelta/li)**2 + (rhoDelta/rhoScalar)**2 + (liDelta/li)**2 + (esDelta/es)**2
                            )**0.5
                elif ZhangRho:
                    if float(k) in wave:
                        rrs = (lt - (rhoDict[k] * li)) / es

                        # Rrs uncertainty
                        rrsDelta = rrs * ( 
                                (liDelta/li)**2 + (rhoDelta/rhoDict[k])**2 + (liDelta/li)**2 + (esDelta/es)**2 
                                )**0.5
                    
                        #Calculate the normalized water leaving radiance
                        nLw = rrs*f0

                        # nLw uncertainty; no provision for F0 uncertainty here
                        nLwDelta = nLw * (
                                (liDelta/li)**2 + (rhoDelta/rhoDict[k])**2 + (liDelta/li)**2 + (esDelta/es)**2
                                )**0.5
                else:
                    # Default rho
                    rhoScalar = rhoDefault
                    rhoDelta = 0.01 # Estimated for range of conditions in Mobley 1999 models; it's actually higher...

                    rrs = (lt - (rhoScalar * li)) / es

                    # Rrs uncertainty
                    rrsDelta = rrs * ( 
                            (liDelta/li)**2 + (rhoDelta/rhoScalar)**2 + (liDelta/li)**2 + (esDelta/es)**2 
                            )**0.5
                
                    #Calculate the normalized water leaving radiance
                    nLw = rrs*f0

                    # nLw uncertainty; no provision for F0 uncertainty here
                    nLwDelta = nLw * (
                            (liDelta/li)**2 + (rhoDelta/rhoScalar)**2 + (liDelta/li)**2 + (esDelta/es)**2
                            )**0.5

                newESData.columns[k].append(es)
                newLIData.columns[k].append(li)
                newLTData.columns[k].append(lt)

                newESDeltaData.columns[k].append(esDelta)
                newLIDeltaData.columns[k].append(liDelta)
                newLTDeltaData.columns[k].append(ltDelta)
                
                # Only populate valid wavelengths. Mark others for deletion
                
                if float(k) in wave:
                    newRrsDeltaData.columns[k].append(rrsDelta)
                    newnLwDeltaData.columns[k].append(nLwDelta)
                    
                    rrsSlice[k] = rrs
                    nLwSlice[k] = nLw
                else:
                    deleteKey.append(k) 
                #     newRrsDeltaData.columns[k].append(np.nan)
                #     newnLwDeltaData.columns[k].append(np.nan)                    
                #     rrsSlice[k] = np.nan
                #     nLwSlice[k] = np.nan
        
        # Eliminate redundant keys using set, and delete unpopulated wavebands
        deleteKey = list(set(deleteKey))
        for key in deleteKey: 
            # Only need to do this for the first ensemble in file
            if key in newRrsData.columns:
                del newRrsData.columns[key]
                del newnLwData.columns[key]
                del newRrsDeltaData.columns[key]
                del newnLwDeltaData.columns[key]

        # Perfrom near-infrared residual correction to remove additional atmospheric and glint contamination
        if ConfigFile.settings["bL2PerformNIRCorrection"]:
            if simpleNIRCorrection:
                # Data show a minimum near 725; using an average from above 750 leads to negative reflectances
                # Find the minimum between 700 and 800, and subtract it from spectrum (spectrally flat)
                msg = "Perform simple residual NIR subtraction."
                print(msg)
                Utilities.writeLogFile(msg)  
                
                # rrs correction
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
                    newRrsData.columns[k].append(rrsSlice[k])

                # nLw correction
                NIRRRs = []
                for k in nLwSlice:
                    if float(k) >= 700 and float(k) <= 800:
                        NIRRRs.append(nLwSlice[k])
                minNIR = min(NIRRRs)
                # Subtract average from each waveband
                for k in nLwSlice:
                    nLwSlice[k] -= minNIR
                    newnLwData.columns[k].append(nLwSlice[k])

            elif simSpecNIRCorrection:
                # From Ruddick 2005, Ruddick 2006 use NIR normalized similarity spectrum
                # (spectrally flat)
                msg = "Perform simulated spectrum residual NIR subtraction."
                print(msg)
                Utilities.writeLogFile(msg)  

                # These ratios are for rho = pi*Rrs
                α1 = 2.35 # 720/780 only good for rho(720)<0.03
                α2 = 1.91 # 780/870 try to avoid, data is noisy here
                threshold = 0.03

                # Retrieve Thuilliers
                wavelength = [float(key) for key in F0.keys()]
                F0 = [value for value in F0.values()]

                # Rrs
                ρ720 = []
                x = []
                for k in rrsSlice:                
                    if float(k) >= 700 and float(k) <= 740:
                        x.append(float(k))
                        ρ720.append(np.pi*rrsSlice[k])
                if not ρ720:
                    QtWidgets.QMessageBox.critical("Error", "NIR wavebands unavailable")
                ρ1 = sp.interpolate.interp1d(x,ρ720)(720)
                F01 = sp.interpolate.interp1d(wavelength,F0)(720)
                ρ780 = []
                x = []
                for k in rrsSlice:                
                    if float(k) >= 760 and float(k) <= 800:
                        x.append(float(k))
                        ρ780.append(rrsSlice[k])
                if not ρ780:
                    QtWidgets.QMessageBox.critical("Error", "NIR wavebands unavailable")
                ρ2 = sp.interpolate.interp1d(x,ρ780)(780)
                F02 = sp.interpolate.interp1d(wavelength,F0)(780)
                ρ870 = []
                x = []
                for k in rrsSlice:                
                    if float(k) >= 850 and float(k) <= 890:
                        x.append(float(k))
                        ρ870.append(rrsSlice[k])
                if not ρ870:
                    QtWidgets.QMessageBox.critical("Error", "NIR wavebands unavailable")
                ρ3 = sp.interpolate.interp1d(x,ρ870)(870)
                F03 = sp.interpolate.interp1d(wavelength,F0)(870)
                
                if ρ1 < threshold:
                    ε = (α1*ρ2 - ρ1)/(α1-1)
                    ε = ε/np.pi # convert to Rrs units
                    εnLw = (α1*ρ2*F02/np.pi - ρ1*F01/np.pi)/(α1-1) # convert to nLw units
                    msg = f'offset(rrs) = {ε}; offset(nLw) = {εnLw}'
                    print(msg)
                    Utilities.writeLogFile(msg)  
                else:
                    msg = "SimSpec threshold tripped. Using 780/870 instead."
                    print(msg)
                    Utilities.writeLogFile(msg)  
                    ε = (α2*ρ3 - ρ2)/(α2-1)
                    ε = ε/np.pi # convert to Rrs units
                    εnLw = (α2*ρ3*F03/np.pi - ρ2*F02/np.pi)/(α2-1) # convert to nLw units              
                    msg = f'offset(rrs) = {ε}; offset(nLw) = {εnLw}'
                    print(msg)
                    Utilities.writeLogFile(msg)  
                for k in rrsSlice:
                    ''' There seems to be some confusion in the Ruddick 2005 SPIE paper.
                    By this method, ε is (and should be) negative, and so must be added 
                    rather than subtracted.''' 
                    # rrsSlice[k] -= ε
                    rrsSlice[k] += ε
                    newRrsData.columns[k].append(rrsSlice[k])
                    # nLwSlice[k] -= εnLw
                    nLwSlice[k] += εnLw
                    newnLwData.columns[k].append(nLwSlice[k])                   
        else:            
            for k in rrsSlice:
                newRrsData.columns[k].append(rrsSlice[k])
            for k in nLwSlice:
                newnLwData.columns[k].append(nLwSlice[k])   
        
        newESData.columnsToDataset()   
        newLIData.columnsToDataset()
        newLTData.columnsToDataset()
        newRrsData.columnsToDataset()
        newnLwData.columnsToDataset()

        newESDeltaData.columnsToDataset()   
        newLIDeltaData.columnsToDataset()
        newLTDeltaData.columnsToDataset()
        newRrsDeltaData.columnsToDataset()
        newnLwDeltaData.columnsToDataset()

        if ConfigFile.settings['bL2WeightMODISA']:
            print("Process MODIS Aqua Bands")
            Weight_RSR.processMODISBands(newRrsMODISAData, newRrsData, sensor='A')
            Weight_RSR.processMODISBands(newRrsMODISADeltaData, newRrsDeltaData, sensor='A')
            newRrsMODISAData.columnsToDataset()
            newRrsMODISADeltaData.columnsToDataset()
            Weight_RSR.processMODISBands(newnLwMODISAData, newnLwData, sensor='A')
            Weight_RSR.processMODISBands(newnLwMODISADeltaData, newnLwDeltaData, sensor='A')
            newnLwMODISAData.columnsToDataset()
            newnLwMODISADeltaData.columnsToDataset()
        if ConfigFile.settings['bL2WeightMODIST']:
            print("Process MODIS Terra Bands")
            Weight_RSR.processMODISBands(newRrsMODISTData, newRrsData, sensor='T')
            Weight_RSR.processMODISBands(newRrsMODISTDeltaData, newRrsDeltaData, sensor='T')
            newRrsMODISTData.columnsToDataset()
            newRrsMODISTDeltaData.columnsToDataset()
            Weight_RSR.processMODISBands(newnLwMODISTData, newnLwData, sensor='T')
            Weight_RSR.processMODISBands(newnLwMODISTDeltaData, newnLwDeltaData, sensor='T')
            newnLwMODISTData.columnsToDataset()
            newnLwMODISTDeltaData.columnsToDataset()

        if ConfigFile.settings['bL2WeightVIIRSN']:
            print("Process VIIRS SNPP Bands")
            Weight_RSR.processVIIRSBands(newRrsVIIRSNData, newRrsData, sensor='N')
            Weight_RSR.processVIIRSBands(newRrsVIIRSNDeltaData, newRrsDeltaData, sensor='N')
            newRrsVIIRSNData.columnsToDataset()
            newRrsVIIRSNDeltaData.columnsToDataset()
            Weight_RSR.processVIIRSBands(newnLwVIIRSNData, newnLwData, sensor='N')
            Weight_RSR.processVIIRSBands(newnLwVIIRSNDeltaData, newnLwDeltaData, sensor='N')
            newnLwVIIRSNData.columnsToDataset()
            newnLwVIIRSNDeltaData.columnsToDataset()
        if ConfigFile.settings['bL2WeightVIIRSJ']:
            print("Process VIIRS JPSS Bands")
            Weight_RSR.processVIIRSBands(newRrsVIIRSJData, newRrsData, sensor='J')
            Weight_RSR.processVIIRSBands(newRrsVIIRSJDeltaData, newRrsDeltaData, sensor='J')
            newRrsVIIRSJData.columnsToDataset()
            newRrsVIIRSJDeltaData.columnsToDataset()
            Weight_RSR.processVIIRSBands(newnLwVIIRSJData, newnLwData, sensor='J')
            Weight_RSR.processVIIRSBands(newnLwVIIRSJDeltaData, newnLwDeltaData, sensor='J')
            newnLwVIIRSJData.columnsToDataset()
            newnLwVIIRSJDeltaData.columnsToDataset()
        
        if ConfigFile.settings['bL2WeightSentinel3A']:
            print("Process Sentinel 3A Bands")
            Weight_RSR.processSentinel3Bands(newRrsSentinel3AData, newRrsData, sensor='A')
            Weight_RSR.processSentinel3Bands(newRrsSentinel3ADeltaData, newRrsDeltaData, sensor='A')
            newRrsSentinel3AData.columnsToDataset()
            newRrsSentinel3ADeltaData.columnsToDataset()
            Weight_RSR.processSentinel3Bands(newnLwSentinel3AData, newnLwData, sensor='A')
            Weight_RSR.processSentinel3Bands(newnLwSentinel3ADeltaData, newnLwDeltaData, sensor='A')
            newnLwSentinel3AData.columnsToDataset()
            newnLwSentinel3ADeltaData.columnsToDataset()
        
        if ConfigFile.settings['bL2WeightSentinel3B']:
            print("Process Sentinel 3B Bands")
            Weight_RSR.processSentinel3Bands(newRrsSentinel3BData, newRrsData, sensor='B')
            Weight_RSR.processSentinel3Bands(newRrsSentinel3BDeltaData, newRrsDeltaData, sensor='B')
            newRrsSentinel3BData.columnsToDataset()
            newRrsSentinel3BDeltaData.columnsToDataset()
            Weight_RSR.processSentinel3Bands(newnLwSentinel3BData, newnLwData, sensor='B')
            Weight_RSR.processSentinel3Bands(newnLwSentinel3BDeltaData, newnLwDeltaData, sensor='B')
            newnLwSentinel3BData.columnsToDataset()
            newnLwSentinel3BDeltaData.columnsToDataset()

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
        

        ''' # Now filter the spectra from the entire collection before slicing the intervals'''               
        # Lt Quality Filtering; anomalous elevation in the NIR
        if ConfigFile.settings["bL2LtUVNIR"]:
            msg = "Applying Lt quality filtering to eliminate spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            badTimes = ProcessL2.ltQuality(sasGroup)
                
            if badTimes is not None:
                print('Removing records...')
                check = ProcessL2.filterData(referenceGroup, badTimes)   
                if check == 0:
                    msg = "No spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False                  
                ProcessL2.filterData(sasGroup, badTimes)
                ProcessL2.filterData(ancGroup, badTimes)
                
        # Filter on SZA and Wind limit
        badTimes = None
        i=0
        start = -1
        stop = []         
        for index in range(len(SZA)):
            # Check for angles spanning north
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
                    msg = f'SZA passed. SZA: {round(SZA[index])}'
                    print(msg)
                    Utilities.writeLogFile(msg)                                               
                    startstop = [timeStamp[start],timeStamp[stop]]
                    msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]} (HHMMSSMSS)'
                    # print(msg)
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
        
        if badTimes is not None and len(badTimes) != 0:
            print('Removing records...')
            check = ProcessL2.filterData(referenceGroup, badTimes)   
            if check == 0:
                msg = "No spectra remaining. Abort."
                print(msg)
                Utilities.writeLogFile(msg)
                return False         
            ProcessL2.filterData(sasGroup, badTimes)
            ProcessL2.filterData(ancGroup, badTimes)            
                    
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
            if badTimes1 is not None and badTimes2 is not None:
                badTimes = np.append(badTimes1,badTimes2, axis=0)
            elif badTimes1 is not None:
                badTimes = badTimes1
            elif badTimes2 is not None:
                badTimes = badTimes2

            if badTimes is not None:
                print('Removing records...')
                check = ProcessL2.filterData(referenceGroup, badTimes)   
                if check == 0:
                    msg = "No spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False                 
                ProcessL2.filterData(sasGroup, badTimes)
                ProcessL2.filterData(ancGroup, badTimes)       

        ''' Next apply the meteorological filter prior to slicing'''     
        # Meteorological Filtering   
        enableMetQualityCheck = int(ConfigFile.settings["bL2EnableQualityFlags"])          
        if enableMetQualityCheck:
            msg = "Applying meteorological filtering to eliminate spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            badTimes = ProcessL2.metQualityCheck(referenceGroup, sasGroup)
                
            if badTimes is not None:
                print('Removing records...')
                check = ProcessL2.filterData(referenceGroup, badTimes)   
                if check == 0:
                    msg = "No spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False              
                ProcessL2.filterData(sasGroup, badTimes)
                ProcessL2.filterData(ancGroup, badTimes)

        # Copy Es dataset to dictionary for length and Timetag2
        esData.datasetToColumns()
        esColumns = esData.columns
        tt2 = esColumns["Timetag2"]
        esLength = len(list(esColumns.values())[0])

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

                if not ProcessL2.calculateREFLECTANCE2(root, sasGroup, referenceGroup, ancGroup, start, end):
                    msg = 'ProcessL2.calculateREFLECTANCE2 unsliced failed. Abort.'
                    print(msg)
                    Utilities.writeLogFile(msg)                      
                    continue                                                      
        else:
            # Iterate over the time ensembles
            start = 0
            endTime = Utilities.timeTag2ToSec(tt2[0]) + interval
            endFileTime = Utilities.timeTag2ToSec(tt2[-1])
            timeFlag = False
            if endTime > endFileTime:
                endTime = endFileTime
                timeFlag = True # In case the whole file is shorter than the selected interval

            for i in range(0, esLength):
                time = Utilities.timeTag2ToSec(tt2[i])
                if (time > endTime) or timeFlag: # end of increment reached
                                        
                    if timeFlag:
                        end = len(tt2)-1 # File shorter than interval; include all spectra
                    else:
                        endTime = time + interval # increment for the next bin loop
                        end = i # end of the slice is up to and not including...so -1 is not needed   
                    if endTime > endFileTime:
                        endTime = endFileTime                 

                    if not ProcessL2.calculateREFLECTANCE2(root, sasGroup, referenceGroup, ancGroup, start, end):
                        msg = 'ProcessL2.calculateREFLECTANCE2 with slices failed. Abort.'
                        print(msg)
                        Utilities.writeLogFile(msg)    

                        start = i                       
                        continue                          
                    start = i

                    if timeFlag:
                        break
            # Try converting any remaining
            end = esLength-1
            time = Utilities.timeTag2ToSec(tt2[start])
            if time < (endTime-interval):                

                if not ProcessL2.calculateREFLECTANCE2(root,sasGroup, referenceGroup, ancGroup, start, end):
                    msg = 'ProcessL2.calculateREFLECTANCE2 ender failed. Abort.'
                    print(msg)
                    Utilities.writeLogFile(msg)    

        # Filter reflectances for negative spectra  
        ''' # 1) Any spectrum that has any negative values between
            #  380 - 700ish, remove the entire spectrum. Otherwise, 
            # set negative bands to 0.
            # This should probably wait until further analysis to see
            # how much overcorrecting is being done by the SimSpec NIR
            # correction. '''
        if ConfigFile.settings["bL2NegativeSpec"]:
            msg = "Filtering reflectance spectra for negative values."
            print(msg)
            Utilities.writeLogFile(msg)
            newReflectanceGroup = root.groups[0]
            badTimes1 = ProcessL2.negReflectance(newReflectanceGroup, 'Rrs')
            badTimes2 = ProcessL2.negReflectance(newReflectanceGroup, 'nLw')

            if badTimes1 is not None and badTimes2 is not None:
                badTimes = np.append(badTimes1,badTimes2, axis=0)
            elif badTimes1 is not None:
                badTimes = badTimes1
            elif badTimes2 is not None:
                badTimes = badTimes2
                
            if badTimes is not None:
                print('Removing records...')               
                
                check = ProcessL2.filterData(newReflectanceGroup, badTimes)
                if check == 0:
                    msg = "No spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False                  
                ProcessL2.filterData(root.groups[1], badTimes)
                ProcessL2.filterData(root.groups[2], badTimes)
                ProcessL2.filterData(root.groups[3], badTimes)        

        return True
    
    @staticmethod
    def processL2(node, ancillaryData=None):
        '''Calculates Rrs and nLw after quality checks and filtering, glint removal, residual 
            subtraction. Weights for satellite bands, and outputs plots and SeaBASS tasetta'''

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

        # Retrieve MERRA2 model ancillary data        
        if ConfigFile.settings["bL2pGetAnc"] ==1:            
            msg = 'Model data for Wind and AOD may be used to replace blank values. Reading in model data...'
            print(msg)
            Utilities.writeLogFile(msg)  
            modData = GetAnc.getAnc(gpsGroup)
            if modData == None:
                return None
        else:
            modData = None


        # Need to either create a new ancData object, or populate the nans in the current one with the model data
        if not ProcessL2.calculateREFLECTANCE(root, node, gpsGroup, satnavGroup, pyrGroup, ancillaryData, modData):
            return None

        root.attributes["Rrs_UNITS"] = "1/sr"
        root.attributes["nLw_UNITS"] = "uW/cm^2/nm/sr"
        
        # Check to insure at least some data survived quality checks
        if root.getGroup("REFLECTANCE").getDataset("Rrs").data is None:
            msg = "All data appear to have been eliminated from the file. Aborting."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None

        return root
