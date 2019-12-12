
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


class ProcessL2:

    # Delete records within the out-of-bounds SZA
    @staticmethod
    def filterData(group, badTimes):                    
        
        # Now delete the record from each dataset in the group
        ticker = 0
        finalCount = 0
        for timeTag in badTimes:

            msg = f'Eliminate data between: {timeTag} (HHMMSSMSS)'
            # print(msg)
            Utilities.writeLogFile(msg)
            # print(timeTag)
            # print(" ")         
            start = Utilities.timeTag2ToSec(timeTag[0])
            stop = Utilities.timeTag2ToSec(timeTag[1])                
            # badIndex = ([i for i in range(lenDataSec) if start <= dataSec[i] and stop >= dataSec[i]])      
                    
            msg = f'   Remove {group.id}  Data'
            # print(msg)
            Utilities.writeLogFile(msg)
            #  timeStamp = satnavGroup.getDataset("ELEVATION").data["Timetag2"]
            if group.id == "IRRADIANCE":
                timeData = group.getDataset("ES").data["Timetag2"]
            if group.id == "RADIANCE":
                timeData = group.getDataset("LI").data["Timetag2"]
            if group.id == "SOLARTRACKER":
                timeData = group.getDataset("AZIMUTH").data["Timetag2"]
            if group.id == "SOLARTRACKER_STATUS":
                return # Nothing we can do without a timetag
            if group.id == "GPS":
                timeData = group.getDataset("COURSE").data["Timetag2"]
            if group.id == "PYROMETER":
                timeData = group.getDataset("T").data["Timetag2"]

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
    def metQualityCheck(es5Columns):   
        esFlag = float(ConfigFile.settings["fL2SignificantEsFlag"])
        dawnDuskFlag = float(ConfigFile.settings["fL2DawnDuskFlag"])
        humidityFlag = float(ConfigFile.settings["fL2RainfallHumidityFlag"])     
        # print("quality check")     

        # Threshold for significant es
        # Wernand 2002
        #v = es5Columns["480.0"][0]
        v = ProcessL2.interpolateColumn(es5Columns, 480.0)[0]
        if v < esFlag:
            print("Quality Check: Sign. ES(480.0) =", v)
            return False

        # Masking spectra affected by dawn/dusk radiation
        # Wernand 2002
        #v = es5Columns["470.0"][0] / es5Columns["610.0"][0] # Fix 610 -> 680
        v1 = ProcessL2.interpolateColumn(es5Columns, 470.0)[0]
        v2 = ProcessL2.interpolateColumn(es5Columns, 680.0)[0]
        v = v1/v2
        if v < dawnDuskFlag:
            print("Quality Check: ES(470.0)/ES(680.0) =", v)
            return False

        # Masking spectra affected by rainfall and high humidity
        # Wernand 2002 (940/370), Garaba et al. 2012 also uses Es(940/370), presumably 720 was developed by Wang...???
        ''' Follow up on the source of this flag'''
        #v = es5Columns["720.0"][0] / es5Columns["370.0"][0]    
        v1 = ProcessL2.interpolateColumn(es5Columns, 720.0)[0]
        v2 = ProcessL2.interpolateColumn(es5Columns, 370.0)[0]
        v = v1/v2
        if v < humidityFlag:
            print("Quality Check: ES(720.0)/ES(370.0) =", v)
            return False

        return True


    # Take a slice of a dataset stored in columns
    @staticmethod
    def columnToSlice(columns, start, end):
        # Each column is a time series at a waveband
        # Start and end are defined by the interval established in the Config
        newSlice = collections.OrderedDict()
        for k in columns:
            newSlice[k] = columns[k][start:end]
        return newSlice

    # Interpolate wind to radiometry
    @staticmethod
    def interpWind(windSpeedData, radData):
        
        windSpeedColumns=None

        # interpolate wind speed to match sensor time values
        if windSpeedData is not None:
            x = windSpeedData.getColumn("DATETIME")[0]
            y = windSpeedData.getColumn("WINDSPEED")[0]

            # Convert windSpeed datetime to seconds for interpolation
            epoch = dt.datetime(1970, 1, 1)
            windSeconds = [(i-epoch).total_seconds() for i in x]

            # Convert radData date and time to datetime and then to seconds for interpolation
            radTime = radData.data["Timetag2"].tolist()
            radSeconds = []
            radDatetime = []
            for i, radDate in enumerate(radData.data["Datetag"].tolist()):                
                radDatetime.append(Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(radDate),radTime[i]))
                radSeconds.append((radDatetime[i]-epoch).total_seconds())
                            
            # windInradSeconds = [i for i in windSeconds if i>=min(radSeconds) and i<=max(radSeconds)]
            windInRadSeconds = []
            windDateTimeInRad = []
            windInRad = []
            for i, value in enumerate(windSeconds):
                if value>=min(radSeconds) and value <=max(radSeconds):
                    windInRadSeconds.append(value)
                    windInRad.append(y[i])        
                    windDateTimeInRad.append(x[i])    
            # Eliminate Nans
            nanIndex = []
            for i,value in enumerate(windInRad):
                if np.isnan(value):                    
                    nanIndex.append(i)
            if len(nanIndex)>0:
                msg = f'Wind records deleted as Nans: {len(nanIndex)}'
                print(msg)
                Utilities.writeLogFile(msg)                    
            for index in sorted(nanIndex, reverse=True):
                del windInRadSeconds[index]
                del windInRad[index]    
            
            # Interpolate winds
            if windInRadSeconds:
                durationRad = max(radSeconds)-min(radSeconds)
                durationWind = max(windInRadSeconds)-min(windInRadSeconds)

                # If at least half of the period has wind data
                if durationWind/durationRad > 0.5:
                    print("Warning: ProcessL2 Wind values may be extrapolated to match radiometric data.")
                    new_y = Utilities.interp(windInRadSeconds, windInRad, radSeconds,fill_value="extrapolate")                    
                    windSpeedColumns = new_y.tolist()
                else:
                    msg = "Insufficient intersection of wind and radiometric data; reverting to default wind speed."
                    print(msg)
                    Utilities.writeLogFile(msg)  
                    windSpeedColumns=None
            else:
                msg = "Wind data do not intersect radiometric data; reverting to default wind speed************************"
                print(msg)
                Utilities.writeLogFile(msg)  
                windSpeedColumns=None

        return windSpeedColumns

    # Take the slice median averages of ancillary data
    @staticmethod
    def sliceAverageAncillary(start, end, newESData, gpsCourseColumns=None, newGPSCourseData=None, gpsLatPosColumns=None, newGPSLatPosData=None, \
            gpsLonPosColumns=None, newGPSLonPosData=None, gpsMagVarColumns=None, newGPSMagVarData=None, gpsSpeedColumns=None, newGPSSpeedData=None, \
            satnavAzimuthColumns=None, newSATNAVAzimuthData=None, satnavElevationColumns=None, newSATNAVElevationData=None, satnavHeadingColumns=None, \
            newSATNAVHeadingData=None, satnavPointingColumns=None, newSATNAVPointingData=None, satnavRelAzColumns=None, newSATNAVRelAzData=None, \
            pyrColumns=None, newPyrData=None):

        # Take the slice median of ancillary data and add it to appropriate groups 
        # You can't take medians of Datetag and Timetag2, so use those from es
        sliceDate = newESData.columns["Datetag"][-1]
        sliceTime = newESData.columns["Timetag2"][-1]

        if gpsLatPosColumns is not None:
            gpsCourseSlice = ProcessL2.columnToSlice(gpsCourseColumns, start, end)
            sliceCourse = np.nanmedian(gpsCourseSlice["TRUE"])
            gpsLatSlice = ProcessL2.columnToSlice(gpsLatPosColumns, start, end)
            sliceLat = np.nanmedian(gpsLatSlice["NONE"])
            gpsLonSlice = ProcessL2.columnToSlice(gpsLonPosColumns, start, end)
            sliceLon = np.nanmedian(gpsLonSlice["NONE"])
            # gpsMagVarSlice = ProcessL2.columnToSlice(gpsMagVarColumns, start, end)
            # sliceMagVar = np.nanmedian(gpsMagVarSlice["NONE"])
            gpsSpeedSlice = ProcessL2.columnToSlice(gpsSpeedColumns, start, end)
            sliceSpeed = np.nanmedian(gpsSpeedSlice["NONE"])
            if not ("Datetag" in newGPSCourseData.columns):
                newGPSCourseData.columns["Datetag"] = [sliceDate]
                newGPSCourseData.columns["Timetag2"] = [sliceTime]
                newGPSCourseData.columns["TRUE"] = [sliceCourse]                        
                newGPSLatPosData.columns["Datetag"] = [sliceDate]
                newGPSLatPosData.columns["Timetag2"] = [sliceTime]
                newGPSLatPosData.columns["NONE"] = [sliceLat]
                newGPSLonPosData.columns["Datetag"] = [sliceDate]
                newGPSLonPosData.columns["Timetag2"] = [sliceTime]
                newGPSLonPosData.columns["NONE"] = [sliceLon]
                # newGPSMagVarData.columns["Datetag"] = [sliceDate]
                # newGPSMagVarData.columns["Timetag2"] = [sliceTime]
                # newGPSMagVarData.columns["NONE"] = [sliceMagVar]
                newGPSSpeedData.columns["Datetag"] = [sliceDate]
                newGPSSpeedData.columns["Timetag2"] = [sliceTime]
                newGPSSpeedData.columns["NONE"] = [sliceSpeed]
            else:
                newGPSCourseData.columns["Datetag"].append(sliceDate)
                newGPSCourseData.columns["Timetag2"].append(sliceTime)
                newGPSCourseData.columns["TRUE"].append(sliceCourse)
                newGPSLatPosData.columns["Datetag"].append(sliceDate)
                newGPSLatPosData.columns["Timetag2"].append(sliceTime)
                newGPSLatPosData.columns["NONE"].append(sliceLat)
                newGPSLonPosData.columns["Datetag"].append(sliceDate)
                newGPSLonPosData.columns["Timetag2"].append(sliceTime)
                newGPSLonPosData.columns["NONE"].append(sliceLon)
                # newGPSMagVarData.columns["Datetag"].append(sliceDate)
                # newGPSMagVarData.columns["Timetag2"].append(sliceTime)
                # newGPSMagVarData.columns["NONE"].append(sliceMagVar)
                newGPSSpeedData.columns["Datetag"].append(sliceDate)
                newGPSSpeedData.columns["Timetag2"].append(sliceTime)
                newGPSSpeedData.columns["NONE"].append(sliceSpeed)

        if satnavRelAzColumns is not None:
            satnavAzimuthSlice = ProcessL2.columnToSlice(satnavAzimuthColumns, start, end)
            sliceAzimuth = np.nanmedian(satnavAzimuthSlice["SUN"])
            satnavElevationSlice = ProcessL2.columnToSlice(satnavElevationColumns, start, end)
            sliceElevation = np.nanmedian(satnavElevationSlice["SUN"])
            satnavHeadingSlice = ProcessL2.columnToSlice(satnavHeadingColumns, start, end)
            sliceHeadingSAS = np.nanmedian(satnavHeadingSlice["SAS_TRUE"])
            sliceHeadingShip = np.nanmedian(satnavHeadingSlice["SHIP_TRUE"])
            satnavPointingSlice = ProcessL2.columnToSlice(satnavPointingColumns, start, end)
            slicePointing = np.nanmedian(satnavPointingSlice["ROTATOR"])
            satnavRelAzSlice = ProcessL2.columnToSlice(satnavRelAzColumns, start, end)
            sliceRelAz = np.nanmedian(satnavRelAzSlice["REL_AZ"])
            if not ("Datetag" in newSATNAVAzimuthData.columns):
                newSATNAVAzimuthData.columns["Datetag"] = [sliceDate]
                newSATNAVAzimuthData.columns["Timetag2"] = [sliceTime]
                newSATNAVAzimuthData.columns["SUN"] = [sliceAzimuth]
                newSATNAVElevationData.columns["Datetag"] = [sliceDate]
                newSATNAVElevationData.columns["Timetag2"] = [sliceTime]
                newSATNAVElevationData.columns["SUN"] = [sliceElevation]
                newSATNAVHeadingData.columns["Datetag"] = [sliceDate]
                newSATNAVHeadingData.columns["Timetag2"] = [sliceTime]
                newSATNAVHeadingData.columns["SAS_True"] = [sliceHeadingSAS]
                newSATNAVHeadingData.columns["SHIP_True"] = [sliceHeadingShip]
                newSATNAVPointingData.columns["Datetag"] = [sliceDate]
                newSATNAVPointingData.columns["Timetag2"] = [sliceTime]
                newSATNAVPointingData.columns["ROTATOR"] = [slicePointing]
                newSATNAVRelAzData.columns["Datetag"] = [sliceDate]
                newSATNAVRelAzData.columns["Timetag2"] = [sliceTime]
                newSATNAVRelAzData.columns["REL_AZ"] = [sliceRelAz]    
            else:
                newSATNAVAzimuthData.columns["Datetag"].append(sliceDate)
                newSATNAVAzimuthData.columns["Timetag2"].append(sliceTime)
                newSATNAVAzimuthData.columns["SUN"].append(sliceAzimuth)
                newSATNAVElevationData.columns["Datetag"].append(sliceDate)
                newSATNAVElevationData.columns["Timetag2"].append(sliceTime)
                newSATNAVElevationData.columns["SUN"].append(sliceElevation)
                newSATNAVHeadingData.columns["Datetag"].append(sliceDate)
                newSATNAVHeadingData.columns["Timetag2"].append(sliceTime)
                newSATNAVHeadingData.columns["SAS_True"].append(sliceHeadingSAS)
                newSATNAVHeadingData.columns["SHIP_True"].append(sliceHeadingShip)
                newSATNAVPointingData.columns["Datetag"].append(sliceDate)
                newSATNAVPointingData.columns["Timetag2"].append(sliceTime)
                newSATNAVPointingData.columns["ROTATOR"].append(slicePointing)
                newSATNAVRelAzData.columns["Datetag"].append(sliceDate)
                newSATNAVRelAzData.columns["Timetag2"].append(sliceTime)
                newSATNAVRelAzData.columns["REL_AZ"].append(sliceRelAz)

        if pyrColumns is not None:
            pyrSlice = ProcessL2.columnToSlice(pyrColumns, start, end)
            slicePyr = np.nanmedian(pyrSlice["IR"])
            if not ("Datetag" in newPyrData.columns):
                newPyrData.columns["Datetag"] = [sliceDate]  
                newPyrData.columns["Timetag2"] = [sliceTime]
                newPyrData.columns["WATER_TEMP"] = [slicePyr]              
            else:
                newPyrData.columns["Datetag"].append(sliceDate)
                newPyrData.columns["Timetag2"].append(sliceTime)
                newPyrData.columns["WATER_TEMP"].append(slicePyr)
       
    @staticmethod
    def calculateREFLECTANCE2(root, esColumns, liColumns, ltColumns, newRrsData, newESData, newLIData, newLTData, \
                            windSpeedColumns=None):
        '''Calculate the lowest X% Lt(780). Check for Nans in Li, Lt, Es, or wind. Send out for meteorological quality flags, 
        Perform rho correction with wind. Calculate the Rrs. Correct for NIR.'''
    
        rhoSky = float(ConfigFile.settings["fL2RhoSky"])
        RuddickRho = int(ConfigFile.settings["bL2RuddickRho"])
        ZhangRho = int(ConfigFile.settings["bL2ZhangRho"])
        defaultWindSpeed = float(ConfigFile.settings["fL2DefaultWindSpeed"])
        windSpeedMean = defaultWindSpeed # replaced later with met file, if present   
        enableMetQualityCheck = int(ConfigFile.settings["bL2EnableQualityFlags"])                        
        performNIRCorrection = int(ConfigFile.settings["bL2PerformNIRCorrection"])                        
        enablePercentLt = float(ConfigFile.settings["bL2EnablePercentLt"])
        percentLt = float(ConfigFile.settings["fL2PercentLt"])

        ''' Going to need output from getanc.py for Zhang Rho corrections '''
        # I think getanc produces a file I can read in here to get the values I need
        # Then need to replace default wind with model wind - this will be replaced with field
        # data if it's available

        AOD = 0 # from getanc
        Cloud = 0 # from getanc
        solZen = 0 # Need to grad this from the HDF
        wTemp = 0 # Need to pull this off the pyrometer, if available. Need an input value otherwise
        Sal = 0 # This is going to have to be input

        



        datetag = esColumns["Datetag"]
        timetag = esColumns["Timetag2"]

        esColumns.pop("Datetag")
        esColumns.pop("Timetag2")

        liColumns.pop("Datetag")
        liColumns.pop("Timetag2")

        ltColumns.pop("Datetag")
        ltColumns.pop("Timetag2")

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

        '''# Calculates the lowest 5% (based on Hooker & Morel 2003; Hooker et al. 2002)'''
        n = len(list(ltColumns.values())[0])
        x = round(n*percentLt/100) # number of retained values
        if n <= 5 or x == 0:
            x = n # if only 5 or fewer records retained, use them all...
        # Find the indexes for the lowest 5%
        lt780 = ProcessL2.interpolateColumn(ltColumns, 780.0)
        index = np.argsort(lt780) # gives indexes if values were to be sorted
                
        if enablePercentLt:
            # returns indexes of the first x values (if values were sorted); i.e. the indexes of the lowest 5% of lt780
            y = index[0:x] 
        else:
            y = index # If Percent Lt is turned off, this will average the whole slice

        # Takes the mean of the lowest 5%
        es5Columns = collections.OrderedDict()
        li5Columns = collections.OrderedDict()
        lt5Columns = collections.OrderedDict()
             
        hasNan = False
        # Ignore runtime warnings when array is all NaNs
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            for k in esColumns: # each k is a time series at a waveband.
                v = [esColumns[k][i] for i in y] # selects the lowest 5% within the interval window...
                mean = np.nanmean(v) # ... and averages them
                es5Columns[k] = [mean]
                if np.isnan(mean):
                    hasNan = True
            for k in liColumns:
                v = [liColumns[k][i] for i in y]
                mean = np.nanmean(v)
                li5Columns[k] = [mean]
                if np.isnan(mean):
                    hasNan = True
            for k in ltColumns:
                v = [ltColumns[k][i] for i in y]
                mean = np.nanmean(v)
                lt5Columns[k] = [mean]
                if np.isnan(mean):
                    hasNan = True
        # Mean of wind speed for data
        # If present, use this instead of the default value
        if windSpeedColumns is not None:
            v = [windSpeedColumns[i] for i in y]
            mean = np.nanmean(v)
            windSpeedMean = mean
            if np.isnan(mean):
                hasNan = True

        # Exit if detect NaN
        if hasNan:
            print("Error NaN Found")
            return False

        # Filter on meteorological flags
        if enableMetQualityCheck:
            if not ProcessL2.metQualityCheck(es5Columns):
                msg = 'Slice failed quality check.'
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
            
            li750 = ProcessL2.interpolateColumn(li5Columns, 750.0)
            es750 = ProcessL2.interpolateColumn(es5Columns, 750.0)
            sky750 = li750[0]/es750[0]

            p_sky = RhoCorrections.RuddickCorr(sky750, rhoSky, windSpeedMean)

        elif ZhangRho:
            p_sky = RhoCorrections.ZhangCorr(windSpeedMean,AOD,Cloud,solZen,wTemp,Sal)

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

        rrsColumns = {}
                
        # Calculate Rrs
        '''# No bidirectional correction is made here.....'''
        for k in es5Columns:
            if (k in li5Columns) and (k in lt5Columns):
                if k not in newESData.columns:
                    newESData.columns[k] = []
                    newLIData.columns[k] = []
                    newLTData.columns[k] = []
                    newRrsData.columns[k] = []

                es = es5Columns[k][0]
                li = li5Columns[k][0]
                lt = lt5Columns[k][0]

                # Calculate the Rrs
                rrs = (lt - (p_sky * li)) / es

                newESData.columns[k].append(es)
                newLIData.columns[k].append(li)
                newLTData.columns[k].append(lt)
                #newRrsData.columns[k].append(rrs)
                rrsColumns[k] = rrs

        # Perfrom near-infrared correction to remove additional atmospheric and glint contamination
        if performNIRCorrection:

            # Data show a minimum near 725; using an average from above 750 leads to negative reflectances
            NIRRRs = []
            for k in rrsColumns:
                # if float(k) >= 750 and float(k) <= 800:
                if float(k) >= 700 and float(k) <= 800:
                    # avg += rrsColumns[k]
                    # num += 1
                    NIRRRs.append(rrsColumns[k])
            # avg /= num
            # avg = np.median(NIRRRs)
            minNIR = min(NIRRRs)
    
            # Subtract average from each waveband
            for k in rrsColumns:
                # rrsColumns[k] -= avg
                rrsColumns[k] -= minNIR

        for k in rrsColumns:
            newRrsData.columns[k].append(rrsColumns[k])

        return True


    @staticmethod
    def calculateREFLECTANCE(root, node, windSpeedData):
        '''Filter out high wind and high/low SZA.
        Interpolate windspeeds, average intervals.
        Run meteorology quality checks.
        Pass to calculateREFLECTANCE2 for rho calcs, Rrs, NIR correction.'''

        print("calculateREFLECTANCE")
        
        interval = float(ConfigFile.settings["fL2TimeInterval"])       

        # Node (input) groups:
        gpsGroup = None
        satnavGroup = None
        pyrGroup = None
        referenceGroup = node.getGroup("IRRADIANCE")
        sasGroup = node.getGroup("RADIANCE")
        if  node.getGroup("GPS"):
            gpsGroup = node.getGroup("GPS")
        if node.getGroup("SOLARTRACKER")        :
            satnavGroup = node.getGroup("SOLARTRACKER")        
        if node.getGroup("PYROMETER"):
            pyrGroup = node.getGroup("PYROMETER")

        ''' # Filter low SZAs and high winds '''
        defaultWindSpeed = float(ConfigFile.settings["fL2DefaultWindSpeed"])
        maxWind = float(ConfigFile.settings["fL2MaxWind"]) 
        SZAMin = float(ConfigFile.settings["fL2SZAMin"])
        SZAMax = float(ConfigFile.settings["fL2SZAMax"])
        SZA = 90 -satnavGroup.getDataset("ELEVATION").data["SUN"]
        timeStamp = satnavGroup.getDataset("ELEVATION").data["Timetag2"]
        
        esData = referenceGroup.getDataset("ES")
        windSpeedColumns = ProcessL2.interpWind(windSpeedData, esData)
        
        badTimes = None
        i=0
        start = -1
        stop = []
        if windSpeedColumns is not None:
            wind = windSpeedColumns
        else:
            wind = mb.repmat(defaultWindSpeed, len(SZA), 1)

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
            ProcessL2.filterData(referenceGroup, badTimes)            
            ProcessL2.filterData(sasGroup, badTimes)
            if gpsGroup is not None:
                ProcessL2.filterData(gpsGroup, badTimes)
            if satnavGroup is not None:
                ProcessL2.filterData(satnavGroup, badTimes)   
            if pyrGroup is not None:
                ProcessL2.filterData(pyrGroup, badTimes)   


        ''' # Now filter the spectra from the entire collection before slicing the intervals'''
       # Spectral Outlier Filter
        enableSpecQualityCheck = ConfigFile.settings['bL2EnableSpecQualityCheck']
        if enableSpecQualityCheck:
            msg = "Applying spectral filtering to eliminate noisy spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            inFilePath = root.attributes['In_Filepath']
            badTimes1 = ProcessL2.specQualityCheck(referenceGroup, inFilePath)
            badTimes2 = ProcessL2.specQualityCheck(sasGroup, inFilePath)
            badTimes = np.append(badTimes1,badTimes2, axis=0)

            if badTimes is not None:
                ProcessL2.filterData(referenceGroup, badTimes)            
                ProcessL2.filterData(sasGroup, badTimes)
                if gpsGroup is not None:
                    ProcessL2.filterData(gpsGroup, badTimes)
                if satnavGroup is not None:
                    ProcessL2.filterData(satnavGroup, badTimes)   
                if pyrGroup is not None:
                    ProcessL2.filterData(pyrGroup, badTimes)   
        esData = referenceGroup.getDataset("ES")
        liData = sasGroup.getDataset("LI")
        ltData = sasGroup.getDataset("LT")

        # Root (new/output) groups:
        newReflectanceGroup = root.getGroup("REFLECTANCE")
        newRadianceGroup = root.getGroup("RADIANCE")
        newIrradianceGroup = root.getGroup("IRRADIANCE")
        if gpsGroup is not None:
            # newGPSGroup = root.getGroup("GPS")
            newGPSGroup = root.getGroup("ANCILLARY")
        if satnavGroup is not None:
            # newSATNAVGroup = root.getGroup("SOLARTRACKER")
            newSATNAVGroup = root.getGroup("ANCILLARY")
        if pyrGroup is not None:
            # newPyrGroup = root.getGroup("PYROMETER")
            newPyrGroup = root.getGroup("ANCILLARY")

        newRrsData = newReflectanceGroup.addDataset("Rrs")
        newESData = newIrradianceGroup.addDataset("ES")
        newLIData = newRadianceGroup.addDataset("LI")
        newLTData = newRadianceGroup.addDataset("LT") 

        if gpsGroup is not None:
            # GPS
            # Creates new gps group with Datetag/Timetag2 columns appended to all datasets
            gpsCourseData = gpsGroup.getDataset("COURSE")
            gpsLatPosData = gpsGroup.getDataset("LATITUDE")
            gpsLonPosData = gpsGroup.getDataset("LONGITUDE")
            # gpsMagVarData = gpsGroup.getDataset("MAGVAR")
            gpsSpeedData = gpsGroup.getDataset("SPEED")        

            # newGPSGroup = root.getGroup("GPS")
            newGPSGroup = root.getGroup("ANCILLARY")
            newGPSCourseData = newGPSGroup.addDataset("COURSE")
            newGPSLatPosData = newGPSGroup.addDataset("LATITUDE")
            newGPSLonPosData = newGPSGroup.addDataset("LONGITUDE")
            # newGPSMagVarData = newGPSGroup.addDataset("MAGVAR")
            newGPSSpeedData = newGPSGroup.addDataset("SPEED")    

        if satnavGroup is not None:
            #SATNAV
            satnavAzimuthData = satnavGroup.getDataset("AZIMUTH")
            satnavHeadingData = satnavGroup.getDataset("HEADING")
            satnavPointingData = satnavGroup.getDataset("POINTING")
            satnavRelAzData = satnavGroup.getDataset("REL_AZ")
            satnavElevationData = satnavGroup.getDataset("ELEVATION")

            # newSATNAVGroup = root.getGroup("SATNAV")
            newSATNAVGroup = root.getGroup("ANCILLARY")
            newSATNAVAzimuthData = newSATNAVGroup.addDataset("SOLAR_AZIMUTH")
            newSATNAVHeadingData = newSATNAVGroup.addDataset("HEADING")
            newSATNAVPointingData = newSATNAVGroup.addDataset("POINTING")
            newSATNAVRelAzData = newSATNAVGroup.addDataset("REL_AZ")
            newSATNAVElevationData = newSATNAVGroup.addDataset("SOLAR_ELEVATION")   
        
        if pyrGroup is not None:
            #PYROMETER
            pyrData = pyrGroup.getDataset("T")            

            # newPyrGroup = root.getGroup("PYROMETER")
            newPyrGroup = root.getGroup("ANCILLARY")
            newPyrData = newPyrGroup.addDataset("WATER_TEMP")            

        # Copy datasets to dictionary
        esData.datasetToColumns()
        esColumns = esData.columns
        tt2 = esColumns["Timetag2"]

        liData.datasetToColumns()
        liColumns = liData.columns        

        ltData.datasetToColumns()
        ltColumns = ltData.columns

        if gpsGroup is not None:
            gpsCourseData.datasetToColumns()
            gpsCourseColumns = gpsCourseData.columns
            gpsLatPosData.datasetToColumns()
            gpsLatPosColumns = gpsLatPosData.columns
            gpsLonPosData.datasetToColumns()
            gpsLonPosColumns = gpsLonPosData.columns
            # gpsMagVarData.datasetToColumns()
            # gpsMagVarColumns = gpsMagVarData.columns
            gpsSpeedData.datasetToColumns()
            gpsSpeedColumns = gpsSpeedData.columns

        if satnavGroup is not None:
            satnavAzimuthData.datasetToColumns()
            satnavAzimuthColumns = satnavAzimuthData.columns
            satnavHeadingData.datasetToColumns()
            satnavHeadingColumns = satnavHeadingData.columns
            satnavPointingData.datasetToColumns()
            satnavPointingColumns = satnavPointingData.columns
            satnavRelAzData.datasetToColumns()
            satnavRelAzColumns = satnavRelAzData.columns
            satnavElevationData.datasetToColumns()
            satnavElevationColumns =satnavElevationData.columns

        if pyrGroup is not None:
            pyrData.datasetToColumns()
            pyrColumns = pyrData.columns

        #if Utilities.hasNan(esData):
        #    print("Found NAN 1") 
        #    sys.exit(1)

        #if Utilities.hasNan(liData):
        #    print("Found NAN 2") 
        #    sys.exit(1)

        #if Utilities.hasNan(ltData):
        #    print("Found NAN 3") 
        #    sys.exit(1)

        esLength = len(list(esColumns.values())[0])
        ltLength = len(list(ltColumns.values())[0])

        if ltLength > esLength:
            print('Warning. Why would ltLength be > esLength??************************************')
            for col in ltColumns:
                col = col[0:esLength] # strips off final columns
            for col in liColumns:
                col = col[0:esLength]

        
        windSpeedColumns = ProcessL2.interpWind(windSpeedData, esData)


        # Break up data into time intervals, and calculate reflectance
        if interval == 0:
            # Here, take the complete time series
            print("No time binning. This can take a moment.")
            # Utilities.printProgressBar(0, esLength-1, prefix = 'Progress:', suffix = 'Complete', length = 50)
            for i in range(0, esLength-1):
                Utilities.printProgressBar(i+1, esLength-1, prefix = 'Progress:', suffix = 'Complete', length = 50)
                start = i
                end = i+1

                esSlice = ProcessL2.columnToSlice(esColumns,start, end)
                liSlice = ProcessL2.columnToSlice(liColumns,start, end)
                ltSlice = ProcessL2.columnToSlice(ltColumns,start, end)
                if windSpeedColumns is not None:
                    windSlice = windSpeedColumns[i: i+1]
                else:
                    windSlice = None
                if not ProcessL2.calculateREFLECTANCE2(root, esSlice, liSlice, ltSlice, newRrsData, newESData, newLIData, newLTData, \
                                                windSlice):
                    # msg = 'Slice failed. Skipping.'
                    # print(msg)
                    # Utilities.writeLogFile(msg)                      
                    continue
                
                # Take the slice median of ancillary data and add it to appropriate groups
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')

                    ProcessL2.sliceAverageAncillary(start, end, newESData, gpsCourseColumns, newGPSCourseData, gpsLatPosColumns, newGPSLatPosData, \
                        gpsLonPosColumns, newGPSLonPosData, None, None, gpsSpeedColumns, newGPSSpeedData, \
                        satnavAzimuthColumns, newSATNAVAzimuthData, satnavElevationColumns, newSATNAVElevationData, satnavHeadingColumns, \
                        newSATNAVHeadingData, satnavPointingColumns, newSATNAVPointingData, satnavRelAzColumns, newSATNAVRelAzData, \
                        pyrColumns, newPyrData)                
                            

        else:
            start = 0
            endTime = Utilities.timeTag2ToSec(tt2[0]) + interval
            for i in range(0, esLength):
                time = Utilities.timeTag2ToSec(tt2[i])
                if time > endTime: # end of increment reached
                    endTime = time + interval # increment for the next bin loop
                    # end = i-1
                    end = i # end of the slice is up to and not including...so -1 is not needed
                    # Here take one interval as defined in Config
                    esSlice = ProcessL2.columnToSlice(esColumns, start, end)
                    liSlice = ProcessL2.columnToSlice(liColumns, start, end)
                    ltSlice = ProcessL2.columnToSlice(ltColumns, start, end)
                    if windSpeedColumns is not None:
                        windSlice = windSpeedColumns[start: end]
                    else:
                        windSlice = None
                    if not ProcessL2.calculateREFLECTANCE2(root, esSlice, liSlice, ltSlice, newRrsData, newESData, newLIData, newLTData, \
                                                    windSlice):
                        # msg = 'Slice failed. Skipping.'
                        # print(msg)
                        # Utilities.writeLogFile(msg)  
                        start = i                        
                        continue

                    # Take the slice median of ancillary data and add it to appropriate groups
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')

                        ProcessL2.sliceAverageAncillary(start, end, newESData, gpsCourseColumns, newGPSCourseData, gpsLatPosColumns, newGPSLatPosData, \
                            gpsLonPosColumns, newGPSLonPosData, None, None, gpsSpeedColumns, newGPSSpeedData, \
                            satnavAzimuthColumns, newSATNAVAzimuthData, satnavElevationColumns, newSATNAVElevationData, satnavHeadingColumns, \
                            newSATNAVHeadingData, satnavPointingColumns, newSATNAVPointingData, satnavRelAzColumns, newSATNAVRelAzData, \
                            pyrColumns, newPyrData)           
                    start = i

            # Try converting any remaining
            end = esLength-1
            time = Utilities.timeTag2ToSec(tt2[end])
            if time < endTime:
                esSlice = ProcessL2.columnToSlice(esColumns, start, end)
                liSlice = ProcessL2.columnToSlice(liColumns, start, end)
                ltSlice = ProcessL2.columnToSlice(ltColumns, start, end)

                if windSpeedColumns is not None:
                    windSlice = windSpeedColumns[start: end]
                else:
                    windSlice = None

                if ProcessL2.calculateREFLECTANCE2(root, esSlice, liSlice, ltSlice, newRrsData, newESData, newLIData, newLTData, windSlice):
                    # Take the slice median of ancillary data and add it to appropriate groups
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')

                        ProcessL2.sliceAverageAncillary(start, end, newESData, gpsCourseColumns, newGPSCourseData, gpsLatPosColumns, newGPSLatPosData, \
                            gpsLonPosColumns, newGPSLonPosData, None, None, gpsSpeedColumns, newGPSSpeedData, \
                            satnavAzimuthColumns, newSATNAVAzimuthData, satnavElevationColumns, newSATNAVElevationData, satnavHeadingColumns, \
                            newSATNAVHeadingData, satnavPointingColumns, newSATNAVPointingData, satnavRelAzColumns, newSATNAVRelAzData, \
                            pyrColumns, newPyrData)           


        newESData.columnsToDataset()
        newLIData.columnsToDataset()
        newLTData.columnsToDataset()
        newRrsData.columnsToDataset()
        if gpsGroup is not None:
            newGPSCourseData.columnsToDataset()
            newGPSLatPosData.columnsToDataset()
            newGPSLonPosData.columnsToDataset()
            # newGPSMagVarData.columnsToDataset()
            newGPSSpeedData.columnsToDataset()
        if satnavGroup is not None:
            newSATNAVAzimuthData.columnsToDataset()
            newSATNAVElevationData.columnsToDataset()
            newSATNAVHeadingData.columnsToDataset()
            newSATNAVPointingData.columnsToDataset()
            newSATNAVRelAzData.columnsToDataset()
        if pyrGroup is not None:
            newPyrData.columnsToDataset()

        return True


    # Calculates Rrs
    @staticmethod
    def processL2(node, windSpeedData=None):

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
            root.addGroup("ANCILLARY")
        # if pyrGroup is not None:
        #     root.addGroup("PYROMETER")    

        if ConfigFile.settings["l2pGetAnc"] ==1:
            AOD, modWind = getAnc() # lat, long, YYYYDDDHH

        if not ProcessL2.calculateREFLECTANCE(root, node, windSpeedData):
            return None

        root.attributes["Rrs_UNITS"] = "sr^-1"
        
        # Check to insure at least some data survived quality checks
        if root.getGroup("REFLECTANCE").getDataset("Rrs").data is None:
            msg = "All data appear to have been eliminated from the file. Aborting."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None

        return root
