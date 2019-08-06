
import collections
import numpy as np
import scipy as sp

import HDFRoot
from Utilities import Utilities
from ConfigFile import ConfigFile


class ProcessL3a:


    # Interpolates by wavelength
    @staticmethod
    def interpolateWavelength(ds, newDS, new_x):

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
        # # Determine interpolated wavelength values
        # start = np.ceil(wavelength[0])
        # end = np.floor(wavelength[len(wavelength)-1])
        # new_x = np.arange(start, end, interval)
        # #print(new_x)

        newColumns = collections.OrderedDict()
        newColumns["Datetag"] = saveDatetag
        newColumns["Timetag2"] = saveTimetag2

        # Append latpos/lonpos
        # ToDo: Do this better
        newColumns["LATPOS"] = saveDatetag
        newColumns["LONPOS"] = saveDatetag
        newColumns["AZIMUTH"] = saveDatetag
        newColumns["SHIP_TRUE"] = saveDatetag
        newColumns["PITCH"] = saveDatetag
        newColumns["ROTATOR"] = saveDatetag
        newColumns["ROLL"] = saveDatetag


        for i in range(new_x.shape[0]):
            #print(i, new_x[i])
            newColumns[str(new_x[i])] = []

        # Perform interpolation for each row
        for i in range(len(saveDatetag)):
            #print(i)

            values = []
            for k in columns:
                values.append(columns[k][i])
            y = np.asarray(values)
            #new_y = sp.interpolate.interp1d(x, y)(new_x)
            new_y = sp.interpolate.InterpolatedUnivariateSpline(x, y, k=3)(new_x)

            for i in range(new_x.shape[0]):
                newColumns[str(new_x[i])].append(new_y[i])


        #newDS = HDFDataset()
        newDS.columns = newColumns
        newDS.columnsToDataset()
        #print(ds.columns)
        #return newDS


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

    # # Performs averaging on the data
    # @staticmethod
    # def dataAveraging(ds):
        
    #     msg = "Process Data Average"
    #     print(msg)
    #     Utilities.writeLogFile(msg)
        
    #     interval = 2
    #     width = 1

    #     # Copy dataset to dictionary
    #     ds.datasetToColumns()
    #     columns = ds.columns
    #     saveDatetag = columns.pop("Datetag")
    #     saveTimetag2 = columns.pop("Timetag2")

    #     # convert timetag2 to seconds
    #     timer = []
    #     for i in range(len(saveTimetag2)):
    #         timer.append(Utilities.timeTag2ToSec(saveTimetag2[i]))

    #     # new data to return
    #     newColumns = collections.OrderedDict()
    #     newColumns["Datetag"] = []
    #     newColumns["Timetag2"] = []

    #     i = 0
    #     v = timer[0]
    #     while i < len(timer)-1:
    #         if (timer[i] - v) > interval:
    #             #print(saveTimetag2[i], timer[i])
    #             newColumns["Datetag"].append(saveDatetag[i])
    #             newColumns["Timetag2"].append(saveTimetag2[i])
    #             v = timer[i]
    #             i += 2
    #         else:
    #             i += 1

    #     for k in columns:
    #         data = columns[k]
    #         newColumns[k] = []

    #         # Do a natural log transform
    #         data = np.log(data)

    #         # generate points to average based on interval
    #         i = 0            
    #         v = timer[0]
    #         while i < len(timer)-1:
    #             if (timer[i] - v) > interval:
    #                 avg = ProcessL3a.getDataAverage(i, data, timer, width)
    #                 newColumns[k].append(avg)
    #                 v = timer[i]
    #                 i += 2
    #             else:
    #                 i += 1

    #         newColumns = np.exp(newColumns)

    #     ds.columns = newColumns
    #     ds.columnsToDataset()


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
                #if k != "Datetag" and k != "Timetag2" and k != "LATPOS" and k != "LONPOS":
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

        #print(matchMin, matchMax)

        # Remove values to match minimum and maximum
        for ds in [esData, liData, ltData]:
            l = []
            for k in ds.columns.keys():
                #if k != "Datetag" and k != "Timetag2" and k != "LATPOS" and k != "LONPOS":
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



    # Does wavelength interpolation and data averaging
    @staticmethod
    def processL3a(node):

        interval = float(ConfigFile.settings["fL3aInterpInterval"])
        root = HDFRoot.HDFRoot()
        root.copyAttributes(node)
        root.attributes["PROCESSING_LEVEL"] = "3a"
        ''' This was all very odd in PySciDon'''
        # root.attributes["BIN_INTERVAL"] = "1 m"
        # root.attributes["BIN_WIDTH"] = "0.5 m"
        # root.attributes["TIME_INTERVAL"] = "2 sec"
        # root.attributes["TIME_WIDTH"] = "1 sec"
        root.attributes["WAVEL_INTERP"] = (str(interval) + " nm") 

        newReferenceGroup = root.addGroup("Reference")
        newSASGroup = root.addGroup("SAS")
        if node.getGroup("GPS"):
            root.groups.append(node.getGroup("GPS"))
        if node.getGroup("SATNAV"):
            root.groups.append(node.getGroup("SATNAV"))

        referenceGroup = node.getGroup("Reference")
        sasGroup = node.getGroup("SAS")

        esData = referenceGroup.getDataset("ES_hyperspectral")
        liData = sasGroup.getDataset("LI_hyperspectral")
        ltData = sasGroup.getDataset("LT_hyperspectral")

        newESData = newReferenceGroup.addDataset("ES_hyperspectral")
        newLIData = newSASGroup.addDataset("LI_hyperspectral")
        newLTData = newSASGroup.addDataset("LT_hyperspectral")

        ''' PySciDON interpolated each instrument to a different set of bands.
        Here we use a common set.'''
        # Es dataset to dictionary
        esData.datasetToColumns()
        columns = esData.columns
        saveDatetag = columns.pop("Datetag")
        saveTimetag2 = columns.pop("Timetag2")
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
        saveDatetag = columns.pop("Datetag")
        saveTimetag2 = columns.pop("Timetag2")
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
        saveDatetag = columns.pop("Datetag")
        saveTimetag2 = columns.pop("Timetag2")
        # Get wavelength values
        ltWavelength = []
        for k in columns:
            ltWavelength.append(float(k))
        # esWave = np.asarray(wavelength)
        # Determine interpolated wavelength values
        ltStart = np.ceil(ltWavelength[0])
        ltEnd = np.floor(ltWavelength[len(liWavelength)-1])

        # No extrapolation
        start = max(esStart,liStart,ltStart)
        end = min(esEnd,liEnd,ltEnd)
        new_x = np.arange(start, end, interval)
        # print(new_x)

        ProcessL3a.interpolateWavelength(esData, newESData, new_x)
        ProcessL3a.interpolateWavelength(liData, newLIData, new_x)
        ProcessL3a.interpolateWavelength(ltData, newLTData, new_x)


        # Append latpos/lonpos to datasets
        if root.getGroup("GPS"):
            gpsGroup = node.getGroup("GPS")
            latposData = gpsGroup.getDataset("LATPOS")
            lonposData = gpsGroup.getDataset("LONPOS")

            latposData.datasetToColumns()
            lonposData.datasetToColumns()

            latpos = latposData.columns["NONE"]
            lonpos = lonposData.columns["NONE"]

            newESData.datasetToColumns()
            newLIData.datasetToColumns()
            newLTData.datasetToColumns()

            #print(newESData.columns)

            newESData.columns["LATPOS"] = latpos
            newLIData.columns["LATPOS"] = latpos
            newLTData.columns["LATPOS"] = latpos

            newESData.columns["LONPOS"] = lonpos
            newLIData.columns["LONPOS"] = lonpos
            newLTData.columns["LONPOS"] = lonpos

            newESData.columnsToDataset()
            newLIData.columnsToDataset()
            newLTData.columnsToDataset()
        

        if root.getGroup("SATNAV"):
            satnavGroup = node.getGroup("SATNAV")

            azimuthData = satnavGroup.getDataset("AZIMUTH")
            headingData = satnavGroup.getDataset("HEADING")
            pitchData = satnavGroup.getDataset("PITCH")
            pointingData = satnavGroup.getDataset("POINTING")
            rollData = satnavGroup.getDataset("ROLL")

            azimuthData.datasetToColumns()
            headingData.datasetToColumns()
            pitchData.datasetToColumns()
            pointingData.datasetToColumns()
            rollData.datasetToColumns()
            

            azimuth = azimuthData.columns["SUN"]
            shipTrue = headingData.columns["SHIP_TRUE"]
            pitch = pitchData.columns["SAS"]
            rotator = pointingData.columns["ROTATOR"]
            roll = rollData.columns["SAS"]


            newESData.datasetToColumns()
            newLIData.datasetToColumns()
            newLTData.datasetToColumns()
            
            newESData.columns["AZIMUTH"] = azimuth
            newLIData.columns["AZIMUTH"] = azimuth
            newLTData.columns["AZIMUTH"] = azimuth

            newESData.columns["SHIP_TRUE"] = shipTrue
            newLIData.columns["SHIP_TRUE"] = shipTrue
            newLTData.columns["SHIP_TRUE"] = shipTrue

            newESData.columns["PITCH"] = pitch
            newLIData.columns["PITCH"] = pitch
            newLTData.columns["PITCH"] = pitch
            
            newESData.columns["ROTATOR"] = rotator
            newLIData.columns["ROTATOR"] = rotator
            newLTData.columns["ROTATOR"] = rotator
            
            newESData.columns["ROLL"] = roll
            newLIData.columns["ROLL"] = roll
            newLTData.columns["ROLL"] = roll

            newESData.columnsToDataset()
            newLIData.columnsToDataset()
            newLTData.columnsToDataset()


        # Make each dataset have matching wavelength values (for testing)
        ProcessL3a.matchColumns(newESData, newLIData, newLTData)

        #ProcessL3a.dataAveraging(newESData)
        #ProcessL3a.dataAveraging(newLIData)
        #ProcessL3a.dataAveraging(newLTData)

        return root
