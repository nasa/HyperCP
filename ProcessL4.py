
import collections
import sys
import warnings

import numpy as np
import scipy as sp
import datetime as dt

import HDFRoot
#import HDFGroup
#import HDFDataset

from Utilities import Utilities

from ConfigFile import ConfigFile


class ProcessL4:

    # Interpolate to a single column
    @staticmethod
    def interpolateColumn(columns, wl):
        #print("interpolateColumn")

        # Values to return
        return_y = []

        # Column to interpolate to
        new_x = [wl]

        # Copy dataset to dictionary
        #ds.datasetToColumns()
        #columns = ds.columns
        
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



    # Perform meteorological flag checking
    @staticmethod
    def qualityCheckVar(es5Columns, esFlag, dawnDuskFlag, humidityFlag):
        print("qualtiy check")

        # Threshold for significant es
        #v = es5Columns["480.0"][0]
        v = ProcessL4.interpolateColumn(es5Columns, 480.0)[0]
        if v < esFlag:
            print("Quality Check: ES(480.0) =", v)
            return False

        # Masking spectra affected by dawn/dusk radiation
        #v = es5Columns["470.0"][0] / es5Columns["610.0"][0] # Fix 610 -> 680
        v1 = ProcessL4.interpolateColumn(es5Columns, 470.0)[0]
        v2 = ProcessL4.interpolateColumn(es5Columns, 680.0)[0]
        v = v1/v2
        if v < dawnDuskFlag:
            print("Quality Check: ES(470.0)/ES(680.0) =", v)
            return False

        # Masking spectra affected by rainfall and high humidity
        #v = es5Columns["720.0"][0] / es5Columns["370.0"][0]    
        v1 = ProcessL4.interpolateColumn(es5Columns, 720.0)[0]
        v2 = ProcessL4.interpolateColumn(es5Columns, 370.0)[0]
        v = v1/v2
        if v < humidityFlag:
            print("Quality Check: ES(720.0)/ES(370.0) =", v)
            return False

        return True

    # Perform meteorological flag checking with settings from config
    @staticmethod
    def qualityCheck(es5Columns):
        esFlag = float(ConfigFile.settings["fL4SignificantEsFlag"])
        dawnDuskFlag = float(ConfigFile.settings["fL4DawnDuskFlag"])
        humidityFlag = float(ConfigFile.settings["fL4RainfallHumidityFlag"])

        result = ProcessL4.qualityCheckVar(es5Columns, esFlag, dawnDuskFlag, humidityFlag)

        return result


    # Take a slice of a dataset stored in columns
    @staticmethod
    def columnToSlice(columns, start, end):
        # Each column is a time series at a waveband
        # Start and end are defined by the interval established in the Config
        newSlice = collections.OrderedDict()
        for k in columns:
            newSlice[k] = columns[k][start:end]
        return newSlice


    @staticmethod
    def calculateReflectance2(root, esColumns, liColumns, ltColumns, newRrsData, newESData, newLIData, newLTData, \
                              percentLt, enableQualityCheck, performNIRCorrection, \
                              rhoSky=0.0256, enableWindSpeedCalculation=1, defaultWindSpeed=0.0, windSpeedColumns=None):

        #print("calculateReflectance2")
        
        datetag = esColumns["Datetag"]
        timetag = esColumns["Timetag2"]
        latpos = None
        lonpos = None

        relAzimuth = None

        # azimuth = None
        # shipTrue = None
        # pitch = None
        # rotator = None
        # roll = None


        esColumns.pop("Datetag")
        esColumns.pop("Timetag2")

        liColumns.pop("Datetag")
        liColumns.pop("Timetag2")

        ltColumns.pop("Datetag")
        ltColumns.pop("Timetag2")

        # remove added LATPOS/LONPOS if added
        if "LATPOS" in esColumns:
            latpos = esColumns["LATPOS"]
            esColumns.pop("LATPOS")
            liColumns.pop("LATPOS")
            ltColumns.pop("LATPOS")
        if "LONPOS" in esColumns:
            lonpos = esColumns["LONPOS"]
            esColumns.pop("LONPOS")
            liColumns.pop("LONPOS")
            ltColumns.pop("LONPOS")


        if "REL_AZ" in esColumns:
            relAzimuth = esColumns["REL_AZ"]
            esColumns.pop("REL_AZ")
            liColumns.pop("REL_AZ")
            ltColumns.pop("REL_AZ")
        # if "AZIMUTH" in esColumns:
        #     azimuth = esColumns["AZIMUTH"]
        #     esColumns.pop("AZIMUTH")
        #     liColumns.pop("AZIMUTH")
        #     ltColumns.pop("AZIMUTH")
        # if "SHIP_TRUE" in esColumns:
        #     shipTrue = esColumns["SHIP_TRUE"]
        #     esColumns.pop("SHIP_TRUE")
        #     liColumns.pop("SHIP_TRUE")
        #     ltColumns.pop("SHIP_TRUE")
        # if "PITCH" in esColumns:
        #     pitch = esColumns["PITCH"]
        #     esColumns.pop("PITCH")
        #     liColumns.pop("PITCH")
        #     ltColumns.pop("PITCH")
        # if "ROTATOR" in esColumns:
        #     rotator = esColumns["ROTATOR"]
        #     esColumns.pop("ROTATOR")
        #     liColumns.pop("ROTATOR")
        #     ltColumns.pop("ROTATOR")
        # if "ROLL" in esColumns:
        #     roll = esColumns["ROLL"]
        #     esColumns.pop("ROLL")
        #     liColumns.pop("ROLL")
        #     ltColumns.pop("ROLL")


        # Stores the middle element
        if len(datetag) > 0:
            date = datetag[int(len(datetag)/2)]
            time = timetag[int(len(timetag)/2)]
        if latpos:
            lat = latpos[int(len(latpos)/2)]
        if lonpos:
            lon = lonpos[int(len(lonpos)/2)]

        if relAzimuth:
            relAzi = relAzimuth[int(len(relAzimuth)/2)]
        # if azimuth:
        #     azi = azimuth[int(len(azimuth)/2)]
        # if shipTrue:
        #     ship = shipTrue[int(len(shipTrue)/2)]
        # if pitch:
        #     pit = pitch[int(len(pitch)/2)]
        # if rotator:
        #     rot = rotator[int(len(rotator)/2)]
        # if roll:
        #     rol = roll[int(len(roll)/2)]


        #print("Test:")
        #print(date, time, lat, lon)


        # Calculates the lowest 5% (based on Hooker & Morel 2003)
        n = len(list(ltColumns.values())[0])
        x = round(n*percentLt/100) # number of retained values
        if n <= 5 or x == 0:
            x = n # if only 5 or fewer records retained, use them all...

        #print(ltColumns["780.0"])

        # Find the indexes for the lowest 5%
        #lt780 = ltColumns["780.0"]
        lt780 = ProcessL4.interpolateColumn(ltColumns, 780.0)
        index = np.argsort(lt780) # gives indexes if values were to be sorted
        y = index[0:x] # returns indexes of the first x values (if values were sorted); i.e. the indexes of the lowest 5% of lt780


        # Takes the mean of the lowest 5%
        es5Columns = collections.OrderedDict()
        li5Columns = collections.OrderedDict()
        lt5Columns = collections.OrderedDict()
        windSpeedMean = defaultWindSpeed # replaced later with met file, if present


        # Checks if the data has NaNs
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

        # Test meteorological flags
        if enableQualityCheck:
            if not ProcessL4.qualityCheck(es5Columns):
                return False


        '''# This is the Ruddick, et al. 2006 approach, which has one method for 
        # clear sky, and another for cloudy.'''

        # Calculate Rho_sky
        li750 = ProcessL4.interpolateColumn(li5Columns, 750.0)
        es750 = ProcessL4.interpolateColumn(es5Columns, 750.0)
        #sky750 = li5Columns["750.0"][0]/es5Columns["750.0"][0]
        sky750 = li750[0]/es750[0]


        # ToDo: sunny/wind calculations
        if not enableWindSpeedCalculation or sky750 > 0.05:
            # Cloudy conditions: no further correction
            p_sky = rhoSky
        else:
            # Clear sky conditions: correct for wind
            # Set wind speed here
            w = windSpeedMean
            p_sky = rhoSky + 0.00039 * w + 0.000034 * w * w
            #p_sky = 0.0256


        # Add extra information to Rrs dataset
        if not ("Datetag" in newRrsData.columns):
            newESData.columns["Datetag"] = [date]
            newLIData.columns["Datetag"] = [date]
            newLTData.columns["Datetag"] = [date]
            newRrsData.columns["Datetag"] = [date]
            newESData.columns["Timetag2"] = [time]
            newLIData.columns["Timetag2"] = [time]
            newLTData.columns["Timetag2"] = [time]
            newRrsData.columns["Timetag2"] = [time]
            if latpos:
                newESData.columns["Latpos"] = [lat]
                newLIData.columns["Latpos"] = [lat]
                newLTData.columns["Latpos"] = [lat]
                newRrsData.columns["Latpos"] = [lat]
            if lonpos:
                newESData.columns["Lonpos"] = [lon]
                newLIData.columns["Lonpos"] = [lon]
                newLTData.columns["Lonpos"] = [lon]
                newRrsData.columns["Lonpos"] = [lon]

            if relAzimuth:
                newESData.columns["RelativeAzimuth"] = [relAzi]
                newLIData.columns["RelativeAzimuth"] = [relAzi]
                newLTData.columns["RelativeAzimuth"] = [relAzi]
                newRrsData.columns["RelativeAzimuth"] = [relAzi]
            # if azimuth:
            #     newESData.columns["Azimuth"] = [azi]
            #     newLIData.columns["Azimuth"] = [azi]
            #     newLTData.columns["Azimuth"] = [azi]
            #     newRrsData.columns["Azimuth"] = [azi]
            # if shipTrue:
            #     newESData.columns["ShipTrue"] = [ship]
            #     newLIData.columns["ShipTrue"] = [ship]
            #     newLTData.columns["ShipTrue"] = [ship]
            #     newRrsData.columns["ShipTrue"] = [ship]
            # if pitch:
            #     newESData.columns["Pitch"] = [pit]
            #     newLIData.columns["Pitch"] = [pit]
            #     newLTData.columns["Pitch"] = [pit]
            #     newRrsData.columns["Pitch"] = [pit]
            # if rotator:
            #     newESData.columns["Rotator"] = [rot]
            #     newLIData.columns["Rotator"] = [rot]
            #     newLTData.columns["Rotator"] = [rot]
            #     newRrsData.columns["Rotator"] = [rot]
            # if roll:
            #     newESData.columns["Roll"] = [rol]
            #     newLIData.columns["Roll"] = [rol]
            #     newLTData.columns["Roll"] = [rol]
            #     newRrsData.columns["Roll"] = [rol]
        else:
            newESData.columns["Datetag"].append(date)
            newLIData.columns["Datetag"].append(date)
            newLTData.columns["Datetag"].append(date)
            newRrsData.columns["Datetag"].append(date)
            newESData.columns["Timetag2"].append(time)
            newLIData.columns["Timetag2"].append(time)
            newLTData.columns["Timetag2"].append(time)
            newRrsData.columns["Timetag2"].append(time)
            if latpos:
                newESData.columns["Latpos"].append(lat)
                newLIData.columns["Latpos"].append(lat)
                newLTData.columns["Latpos"].append(lat)
                newRrsData.columns["Latpos"].append(lat)
            if lonpos:
                newESData.columns["Lonpos"].append(lon)
                newLIData.columns["Lonpos"].append(lon)
                newLTData.columns["Lonpos"].append(lon)
                newRrsData.columns["Lonpos"].append(lon)
            if relAzimuth:
                newESData.columns["RelativeAzimuth"].append(relAzi)
                newLIData.columns["RelativeAzimuth"].append(relAzi)
                newLTData.columns["RelativeAzimuth"].append(relAzi)
                newRrsData.columns["RelativeAzimuth"].append(relAzi)
            # if azimuth:
            #     newESData.columns["Azimuth"].append(azi)
            #     newLIData.columns["Azimuth"].append(azi)
            #     newLTData.columns["Azimuth"].append(azi)
            #     newRrsData.columns["Azimuth"].append(azi)
            # if shipTrue:
            #     newESData.columns["ShipTrue"].append(ship)
            #     newLIData.columns["ShipTrue"].append(ship)
            #     newLTData.columns["ShipTrue"].append(ship)
            #     newRrsData.columns["ShipTrue"].append(ship)
            # if pitch:
            #     newESData.columns["Pitch"].append(pit)
            #     newLIData.columns["Pitch"].append(pit)
            #     newLTData.columns["Pitch"].append(pit)
            #     newRrsData.columns["Pitch"].append(pit)
            # if rotator:
            #     newESData.columns["Rotator"].append(rot)
            #     newLIData.columns["Rotator"].append(rot)
            #     newLTData.columns["Rotator"].append(rot)
            #     newRrsData.columns["Rotator"].append(rot)
            # if roll:
            #     newESData.columns["Roll"].append(rol)
            #     newLIData.columns["Roll"].append(rol)
            #     newLTData.columns["Roll"].append(rol)
            #     newRrsData.columns["Roll"].append(rol)

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
                #print(len(newESData.columns[k]))
                es = es5Columns[k][0]
                li = li5Columns[k][0]
                lt = lt5Columns[k][0]

                # Calculate the Rrs
                rrs = (lt - (p_sky * li)) / es


                #esColumns[k] = [es]
                #liColumns[k] = [li]
                #ltColumns[k] = [lt]
                #rrsColumns[k] = [(lt - (p_sky * li)) / es]
                newESData.columns[k].append(es)
                newLIData.columns[k].append(li)
                newLTData.columns[k].append(lt)
                #newRrsData.columns[k].append(rrs)
                rrsColumns[k] = rrs


        # Perfrom near-infrared correction of remove additional contamination from sky/sun glint
        if performNIRCorrection:
            # Get average of Rrs values between 750-800nm
            avg = 0
            num = 0
            for k in rrsColumns:
                if float(k) >= 750 and float(k) <= 800:
                    avg += rrsColumns[k]
                    num += 1
            avg /= num
    
            # Subtract average from each spectra
            for k in rrsColumns:
                rrsColumns[k] -= avg


        for k in rrsColumns:
            newRrsData.columns[k].append(rrsColumns[k])

        return True



    @staticmethod
    def calculateReflectance(root, node, interval, enableQualityCheck, percentLt, performNIRCorrection, \
                             rhoSky=0.0256, enableWindSpeedCalculation=1, defaultWindSpeed=0.0, windSpeedData=None):
    #def calculateReflectance(esData, liData, ltData, newRrsData, newESData, newLIData, newLTData):

        print("calculateReflectance")

        referenceGroup = node.getGroup("Reference")
        sasGroup = node.getGroup("SAS")

        esData = referenceGroup.getDataset("ES_hyperspectral")
        liData = sasGroup.getDataset("LI_hyperspectral")
        ltData = sasGroup.getDataset("LT_hyperspectral")

        newReflectanceGroup = root.getGroup("Reflectance")
        newRrsData = newReflectanceGroup.addDataset("Rrs")
        newESData = newReflectanceGroup.addDataset("ES")
        newLIData = newReflectanceGroup.addDataset("LI")
        newLTData = newReflectanceGroup.addDataset("LT")        

        # Copy datasets to dictionary
        esData.datasetToColumns()
        esColumns = esData.columns
        tt2 = esColumns["Timetag2"]
        # esColumns.pop("Datetag")
        # tt2 = esColumns.pop("Timetag2")

        liData.datasetToColumns()
        liColumns = liData.columns
        # liColumns.pop("Datetag")
        # liColumns.pop("Timetag2")

        ltData.datasetToColumns()
        ltColumns = ltData.columns
        # ltColumns.pop("Datetag")
        # ltColumns.pop("Timetag2")

        # remove added LATPOS/LONPOS if added
        #if "LATPOS" in esColumns:
        #    esColumns.pop("LATPOS")
        #    liColumns.pop("LATPOS")
        #    ltColumns.pop("LATPOS")
        #if "LONPOS" in esColumns:
        #    esColumns.pop("LONPOS")
        #    liColumns.pop("LONPOS")
        #    ltColumns.pop("LONPOS")

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
            print('Warning. Why would ltLength be > esLength??')
            for col in ltColumns:
                col = col[0:esLength] # strips off final columns
            for col in liColumns:
                col = col[0:esLength]

        windSpeedColumns=None

        # interpolate wind speed to match sensor time values
        if windSpeedData is not None:
            # x = windSpeedData.getColumn("TIMETAG2")[0]
            x = windSpeedData.getColumn("DATETIME")[0]
            y = windSpeedData.getColumn("WINDSPEED")[0]
            
            nanIndex = []
            for i,value in enumerate(y):
                if np.isnan(value):                    
                    nanIndex.append(i)
                    
            for index in sorted(nanIndex, reverse=True):
                del x[index]
                del y[index]

            # Convert windSpeed datetime to seconds for interpolation
            epoch = dt.datetime(1970, 1, 1)
            windSeconds = [(i-epoch).total_seconds() for i in x]

            # Convert esData date and time to datetime and then to seconds for interpolation
            esTime = esData.data["Timetag2"].tolist()
            esSeconds = []
            for i, esDate in enumerate(esData.data["Datetag"].tolist()):                
                esDatetime = Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(esDate),esTime[i])
                esSeconds.append((esDatetime-epoch).total_seconds())
                
            '''set up conditional for wind time being within es time, else take default wind'''
            
            new_y = Utilities.interp(windSeconds, y, esSeconds)
            
            windSpeedData.columns["WINDSPEED"] = new_y
            windSpeedData.columns["DATETAG"] = esData.data["Datetag"]
            windSpeedData.columns["TIMETAG2"] = esData.data["Timetag2"]
            windSpeedData.columnsToDataset()
            windSpeedColumns = new_y


        #print("items:", esColumns.values())
        #print(ltLength,resolution)
        if interval == 0:
            # Here, take the complete time series
            for i in range(0, esLength-1):
                esSlice = ProcessL4.columnToSlice(esColumns, i, i+1)
                liSlice = ProcessL4.columnToSlice(liColumns, i, i+1)
                ltSlice = ProcessL4.columnToSlice(ltColumns, i, i+1)
                ProcessL4.calculateReflectance2(root, esSlice, liSlice, ltSlice, newRrsData, newESData, newLIData, newLTData, \
                                                percentLt, enableQualityCheck, performNIRCorrection, \
                                                rhoSky, enableWindSpeedCalculation, defaultWindSpeed, windSpeedColumns)

        else:
            start = 0
            #end = 0
            endTime = Utilities.timeTag2ToSec(tt2[0]) + interval
            for i in range(0, esLength):
                time = Utilities.timeTag2ToSec(tt2[i])
                if time > endTime:
                    end = i-1
                    # Here take one interval as defined in Config
                    esSlice = ProcessL4.columnToSlice(esColumns, start, end)
                    liSlice = ProcessL4.columnToSlice(liColumns, start, end)
                    ltSlice = ProcessL4.columnToSlice(ltColumns, start, end)
                    ProcessL4.calculateReflectance2(root, esSlice, liSlice, ltSlice, newRrsData, newESData, newLIData, newLTData, \
                                                    percentLt, enableQualityCheck, performNIRCorrection, \
                                                    rhoSky, enableWindSpeedCalculation, defaultWindSpeed, windSpeedColumns)
    
                    start = i
                    endTime = time + interval

            # Try converting any remaining
            end = esLength-1
            time = Utilities.timeTag2ToSec(tt2[end])
            if time < endTime:
                esSlice = ProcessL4.columnToSlice(esColumns, start, end)
                liSlice = ProcessL4.columnToSlice(liColumns, start, end)
                ltSlice = ProcessL4.columnToSlice(ltColumns, start, end)
                ProcessL4.calculateReflectance2(root, esSlice, liSlice, ltSlice, newRrsData, newESData, newLIData, newLTData, \
                                                percentLt, enableQualityCheck, performNIRCorrection, \
                                                rhoSky, enableWindSpeedCalculation, defaultWindSpeed, windSpeedColumns)



#        for i in range(0, int(esLength/resolution)):
#            #print(i)
#            start = i*resolution
#            end = start+resolution
#            esSlice = ProcessL4.columnToSlice(esColumns, start, end, i, resolution)
#            liSlice = ProcessL4.columnToSlice(liColumns, start, end, i, resolution)
#            ltSlice = ProcessL4.columnToSlice(ltColumns, start, end, i, resolution)
#
#            ProcessL4.calculateReflectance2(root, node, esSlice, liSlice, ltSlice, newRrsData, newESData, newLIData, newLTData, enableQualityCheck, defaultWindSpeed, windSpeedColumns)


        newESData.columnsToDataset()
        newLIData.columnsToDataset()
        newLTData.columnsToDataset()
        newRrsData.columnsToDataset()


        return True


    # Calculates Rrs
    @staticmethod
    def processL4(node, enableQualityCheck, windSpeedData=None):

        root = HDFRoot.HDFRoot()
        root.copyAttributes(node)
        root.attributes["PROCESSING_LEVEL"] = "4"

        root.addGroup("Reflectance")

        interval = float(ConfigFile.settings["fL4TimeInterval"])
        performNIRCorrection = int(ConfigFile.settings["bL4PerformNIRCorrection"])
        rhoSky = float(ConfigFile.settings["fL4RhoSky"])
        enableWindSpeedCalculation = int(ConfigFile.settings["bL4EnableWindSpeedCalculation"])
        defaultWindSpeed = float(ConfigFile.settings["fL4DefaultWindSpeed"])
        percentLt = float(ConfigFile.settings["fL4PercentLt"])

        # Can change time resolution here
        if not ProcessL4.calculateReflectance(root, node, interval, enableQualityCheck, percentLt, performNIRCorrection, \
                                              rhoSky, enableWindSpeedCalculation, defaultWindSpeed, windSpeedData):
            return None

        return root
