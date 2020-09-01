
import csv
import os
import datetime
import numpy as np
import time

from HDFRoot import HDFRoot
from SeaBASSHeader import SeaBASSHeader
from ConfigFile import ConfigFile
from Utilities import Utilities


class SeaBASSWriter:

    @staticmethod
    def formatHeader(fp,node, level):
        
        seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
        seaBASSFP = os.path.join(os.getcwd(), 'Config',seaBASSHeaderFileName)
        SeaBASSHeader.loadSeaBASSHeader(seaBASSFP)
        headerBlock = SeaBASSHeader.settings        

        # Dataset leading columns can be taken from any sensor         
        referenceGroup = node.getGroup("IRRADIANCE")
        if level == '1e':
            esData = referenceGroup.getDataset("ES")
        if level == '2':
            # referenceGroup = node.getGroup("IRRADIANCE")
            esData = referenceGroup.getDataset("ES_HYPER")
            # if ConfigFile.settings["bL1cSolarTracker"]:
            ancillaryGroup = node.getGroup("ANCILLARY")
            # else:
            #     ancillaryGroup = node.getGroup("ANCILLARY_NOTRACKER")
            wind = ancillaryGroup.getDataset("WINDSPEED")
            wind.datasetToColumns()
            winCol = wind.columns["WINDSPEED"]
            aveWind = np.nanmean(winCol)

        headerBlock['original_file_name'] = node.attributes['RAW_FILE_NAME']
        headerBlock['data_file_name'] = os.path.split(fp)[1]
        headerBlock['comments'] = headerBlock['comments'] + f'\n! DateTime Processed = {time.asctime()}'

        # Convert Dates and Times
        # timeDT = esData.data['Datetime'].tolist() # Datetime has already been stripped off for saving the HDF
        dateDay = esData.data['Datetag'].tolist()
        dateDT = [Utilities.dateTagToDateTime(x) for x in dateDay]
        timeTag2 = esData.data['Timetag2'].tolist()
        timeDT = []
        for i in range(len(dateDT)):
            timeDT.append(Utilities.timeTag2ToDateTime(dateDT[i],timeTag2[i]))
        
        # Python 2 format operator       
        startTime = "%02d:%02d:%02d[GMT]" % (min(timeDT).hour, min(timeDT).minute, min(timeDT).second)
        endTime = "%02d:%02d:%02d[GMT]" % (max(timeDT).hour, max(timeDT).minute, max(timeDT).second)
        startDate = "%04d%02d%02d" % (min(timeDT).year, min(timeDT).month, min(timeDT).day)      
        endDate = "%04d%02d%02d" % (max(timeDT).year, max(timeDT).month, max(timeDT).day)

        # Convert Position
        # Python 3 format syntax
        southLat = "{:.4f}[DEG]".format(min(esData.data['LATITUDE'].tolist()))
        northLat = "{:.4f}[DEG]".format(max(esData.data['LATITUDE'].tolist()))
        eastLon = "{:.4f}[DEG]".format(max(esData.data['LONGITUDE'].tolist()))
        westLon = "{:.4f}[DEG]".format(min(esData.data['LONGITUDE'].tolist()))

        if headerBlock['station'] is '':
            headerBlock['station'] = node.attributes['RAW_FILE_NAME'].split('.')[0]
        if headerBlock['start_time'] is '':
            headerBlock['start_time'] = startTime
        if headerBlock['end_time'] is '':
            headerBlock['end_time'] = endTime
        if headerBlock['start_date'] is '':
            headerBlock['start_date'] = startDate
        if headerBlock['end_date'] is '':
            headerBlock['end_date'] = endDate
        if headerBlock['north_latitude'] is '':
            headerBlock['north_latitude'] = northLat
        if headerBlock['south_latitude'] is '':
            headerBlock['south_latitude'] = southLat
        if headerBlock['east_longitude'] is '':
            headerBlock['east_longitude'] = eastLon
        if headerBlock['west_longitude'] is '':
            headerBlock['west_longitude'] = westLon
        if level == '2':
            headerBlock['wind_speed'] = aveWind # wind_speed will not be written to l1e
        
        return headerBlock

        # headerBlock = print(json.dumps(SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)))
    
   
    @staticmethod
    def formatData1e(dataset,dtype, units):            
                
        # Convert Dates and Times and remove from dataset
        newData = dataset.data
        dateDay = dataset.data['Datetag'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'Datetag')
        dateDT = [Utilities.dateTagToDateTime(x) for x in dateDay]
        timeTag2 = dataset.data['Timetag2'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'Timetag2')
        timeDT = []
        for i in range(len(dateDT)):
            timeDT.append(Utilities.timeTag2ToDateTime(dateDT[i],timeTag2[i]))

        # Retrieve ancillaries and remove from dataset        
        lat = dataset.data['LATITUDE'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'LATITUDE')
        lon = dataset.data['LONGITUDE'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'LONGITUDE')
        sza = dataset.data['SZA'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'SZA')
        relAz = dataset.data['REL_AZ'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'REL_AZ')
        # The rest remain unused
        newData = SeaBASSWriter.removeColumns(newData,'SHIP_TRUE')
        if ConfigFile.settings["bL1cSolarTracker"]:
            newData = SeaBASSWriter.removeColumns(newData,'ROTATOR')
            newData = SeaBASSWriter.removeColumns(newData,'AZIMUTH')

        dataset.data = newData

        # Change field names for SeaBASS compliance
        bands = list(dataset.data.dtype.names)    
        ls = ['date','time','lat','lon','RelAz','SZA']

        if dtype == 'es':
            fieldName = 'Es'
        elif dtype == 'li':
            fieldName = 'Lsky'
        elif dtype == 'lt':
            fieldName = 'Lt'

        fieldsLineStr = ','.join(ls + [f'{fieldName}{band}' for band in bands])

        lenRad = (len(dataset.data.dtype.names))
        unitsLine = ['yyyymmdd']
        unitsLine.append('hh:mm:ss')
        unitsLine.extend(['degrees']*4) # lat, lon, RelAz, SZA
        unitsLine.extend([units]*lenRad)
        unitsLineStr = ','.join(unitsLine)

        # Add data for each row
        dataOut = []
        formatStr = str('{:04d}{:02d}{:02d},{:02d}:{:02d}:{:02d},{:.4f},{:.4f},{:.1f},{:.1f}' + ',{:.6f}'*lenRad)
        for i in range(dataset.data.shape[0]):                        
            subList = [lat[i],lon[i],relAz[i],sza[i]]
            lineList = [timeDT[i].year,timeDT[i].month,timeDT[i].day,timeDT[i].hour,timeDT[i].minute,timeDT[i].second] +\
                subList + list(dataset.data[i].tolist())

            # Replace NaNs with -9999.0
            lineList = [-9999.0 if np.isnan(element) else element for element in lineList]

            lineStr = formatStr.format(*lineList)
            dataOut.append(lineStr)
        return dataOut, fieldsLineStr, unitsLineStr

    @staticmethod
    def formatData2(dataset,dtype, units):      

        dsCopy = dataset.data.copy() # By copying here, we leave the ancillary data tacked on to radiometry for later      
                
        # Convert Dates and Times and remove from dataset
        newData = dsCopy
        dateDay = dsCopy['Datetag'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'Datetag')
        dateDT = [Utilities.dateTagToDateTime(x) for x in dateDay]
        timeTag2 = dsCopy['Timetag2'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'Timetag2')
        timeDT = []
        for i in range(len(dateDT)):
            timeDT.append(Utilities.timeTag2ToDateTime(dateDT[i],timeTag2[i]))

        # Retrieve ancillaries and remove from dataset        
        lat = dsCopy['LATITUDE'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'LATITUDE')
        lon = dsCopy['LONGITUDE'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'LONGITUDE')
        sza = dsCopy['SZA'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'SZA')
        relAz = dsCopy['REL_AZ'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'REL_AZ')
        # rotator = dsCopy['ROTATOR'].tolist()
        # newData = SeaBASSWriter.removeColumns(newData,'ROTATOR')
        # heading = dsCopy['SHIP_TRUE'].tolist() # from SAS
        newData = SeaBASSWriter.removeColumns(newData,'HEADING')
        # azimuth = dsCopy['AZIMUTH'].tolist()        
        newData = SeaBASSWriter.removeColumns(newData,'SOLAR_AZ')

        dsCopy = newData

        # Change field names for SeaBASS compliance
        bands = list(dsCopy.dtype.names)    
        ls = ['date','time','lat','lon','RelAz','SZA']
        # ls[4]='SAZ'
        # ls[5]='heading'    # This is SAS -> SHIP_TRUE, not GPS    
        # pointing         # no SeaBASS field for sensor azimuth

        if dtype == 'es':
            fieldName = 'Es'
        elif dtype == 'li':
            fieldName = 'Lsky'
        elif dtype == 'lt':
            fieldName = 'Lt'
        elif dtype == 'rrs':
            fieldName = 'Rrs'
        # fieldsLineStr = ','.join(ls[:lenNonRad] + [f'{fieldName}{band}' for band in ls[lenNonRad:]])
        fieldsLineStr = ','.join(ls + [f'{fieldName}{band}' for band in bands])

        lenRad = (len(dsCopy.dtype.names))
        unitsLine = ['yyyymmdd']
        unitsLine.append('hh:mm:ss')
        unitsLine.extend(['degrees']*4) # lat, lon, relAz, sza
        unitsLine.extend([units]*lenRad)
        unitsLineStr = ','.join(unitsLine)

        # Add data for each row
        dataOut = []
        formatStr = str('{:04d}{:02d}{:02d},{:02d}:{:02d}:{:02d},{:.4f},{:.4f},{:.1f},{:.1f}' + ',{:.6f}'*lenRad)
        for i in range(dsCopy.shape[0]):                        
            subList = [lat[i],lon[i],relAz[i],sza[i]]
            lineList = [timeDT[i].year,timeDT[i].month,timeDT[i].day,timeDT[i].hour,timeDT[i].minute,timeDT[i].second] +\
                subList + list(dsCopy[i].tolist())

            # Replace NaNs with -9999.0
            lineList = [-9999.0 if np.isnan(element) else element for element in lineList]

            lineStr = formatStr.format(*lineList)
            dataOut.append(lineStr)
        return dataOut, fieldsLineStr, unitsLineStr

    @staticmethod
    def removeColumns(a, removeNameList):
        return a[[name for name in a.dtype.names if name not in removeNameList]]

    @staticmethod
    def writeSeaBASS(dtype,fp,headerBlock,formattedData,fields,units):

        # Set up the SeaBASS directory within the Level data, if necessary
        if not os.path.exists(os.path.split(fp)[0] + '/SeaBASS'):
            print('Creating a SeaBASS directory')
            os.makedirs(os.path.split(fp)[0] + '/SeaBASS')
            
        version = SeaBASSHeader.settings["version"]
        
        outFileName = f'{os.path.split(fp)[0]}/SeaBASS/{dtype}{os.path.split(fp)[1].replace(".hdf",f"_{version}.sb")}'

        outFile = open(outFileName,'w',newline='\n')
        outFile.write('/begin_header\n')
        for key,value in headerBlock.items():
            if key != 'comments' and key != 'other_comments' and key != 'wind_speed':
                # Python 3 f-string
                line = f'/{key}={value}\n'
                outFile.write(line)
        outFile.write(headerBlock['comments']+'\n')        
        outFile.write(headerBlock['other_comments']+'\n')
        outFile.write('/fields='+fields+'\n')
        outFile.write('/units='+units+'\n')
        outFile.write('/end_header\n')
        
        for line in formattedData:
            outFile.write(f'{line}\n')
        
        outFile.close()

    # Convert Level 3 data to SeaBASS file
    @staticmethod
    def outputTXT_Type1e(fp):

        if not os.path.isfile(fp):
            print("SeaBASSWriter: no file to convert")
            return

        # Make sure hdf can be read
        try:
            root = HDFRoot.readHDF5(fp)
        except:
            print('SeaBassWriter: cannot open HDF. May be open in another app.')
            return

        if root is None:
            print("SeaBASSWriter: root is None")
            return

        # Get datasets to output
        referenceGroup = root.getGroup("IRRADIANCE")
        sasGroup = root.getGroup("RADIANCE")

        esData = referenceGroup.getDataset("ES")
        liData = sasGroup.getDataset("LI")
        ltData = sasGroup.getDataset("LT")

        if esData is None or liData is None or ltData is None:
            print("SeaBASSWriter: Radiometric data is missing")
            return

        # Append latpos/lonpos to datasets
        gpsGroup = root.getGroup("GPS")
        latposData = gpsGroup.getDataset("LATITUDE")
        lonposData = gpsGroup.getDataset("LONGITUDE")

        latposData.datasetToColumns()
        lonposData.datasetToColumns()

        latpos = latposData.columns["NONE"]
        lonpos = lonposData.columns["NONE"]

        esData.datasetToColumns()
        liData.datasetToColumns()
        ltData.datasetToColumns()

        #print(esData.columns)

        esData.columns["LATITUDE"] = latpos
        liData.columns["LATITUDE"] = latpos
        ltData.columns["LATITUDE"] = latpos

        esData.columns["LONGITUDE"] = lonpos
        liData.columns["LONGITUDE"] = lonpos
        ltData.columns["LONGITUDE"] = lonpos

        esData.columnsToDataset()
        liData.columnsToDataset()
        ltData.columnsToDataset()
        
        # Append azimuth, heading, rotator, relAz, and SZA to the dataset
        # in order to pass it to formatData1e (bloody awkward...)
        if ConfigFile.settings["bL1cSolarTracker"]:
            satnavGroup = root.getGroup("SOLARTRACKER")

            azimuthData = satnavGroup.getDataset("AZIMUTH")
            headingData = satnavGroup.getDataset("HEADING") # SAS_TRUE & SHIP_TRUE
            # pitchData = satnavGroup.getDataset("PITCH")
            pointingData = satnavGroup.getDataset("POINTING")
            # rollData = satnavGroup.getDataset("ROLL")
            relAzData = satnavGroup.getDataset("REL_AZ")
            elevationData = satnavGroup.getDataset("ELEVATION")

            azimuthData.datasetToColumns()
            headingData.datasetToColumns()
            # pitchData.datasetToColumns()
            pointingData.datasetToColumns()
            # rollData.datasetToColumns()            
            relAzData.datasetToColumns() 
            elevationData.datasetToColumns() 

            azimuth = azimuthData.columns["SUN"]
            shipTrue = headingData.columns["SHIP_TRUE"]
            # sasTrue = headingData.columns["SAS_TRUE"]
            # pitch = pitchData.columns["SAS"]
            rotator = pointingData.columns["ROTATOR"]
            # roll = rollData.columns["SAS"]
            relAz = relAzData.columns["REL_AZ"]
            elevation = elevationData.columns["SUN"]
            sza = []
            for elev in elevation:
                sza.append(90-elev)

            esData.datasetToColumns()
            liData.datasetToColumns()
            ltData.datasetToColumns()
            
            esData.columns["AZIMUTH"] = azimuth
            liData.columns["AZIMUTH"] = azimuth
            ltData.columns["AZIMUTH"] = azimuth

            esData.columns["SHIP_TRUE"] = shipTrue # From SAS, not GPS...
            liData.columns["SHIP_TRUE"] = shipTrue
            ltData.columns["SHIP_TRUE"] = shipTrue

            # esData.columns["PITCH"] = pitch
            # liData.columns["PITCH"] = pitch
            # ltData.columns["PITCH"] = pitch
            
            esData.columns["ROTATOR"] = rotator
            liData.columns["ROTATOR"] = rotator
            ltData.columns["ROTATOR"] = rotator
            
            # esData.columns["ROLL"] = roll
            # liData.columns["ROLL"] = roll
            # ltData.columns["ROLL"] = roll

            esData.columns["REL_AZ"] = relAz
            liData.columns["REL_AZ"] = relAz
            ltData.columns["REL_AZ"] = relAz

            esData.columns["SZA"] = sza
            liData.columns["SZA"] = sza
            ltData.columns["SZA"] = sza

            esData.columnsToDataset()
            liData.columnsToDataset()
            ltData.columnsToDataset()

        else:
            ancGroup = root.getGroup("ANCILLARY_NOTRACKER")

            headingData = ancGroup.getDataset("HEADING")
            relAzData = ancGroup.getDataset("REL_AZ")
            szaData = ancGroup.getDataset("SZA")

            headingData.datasetToColumns()
            relAzData.datasetToColumns() 
            szaData.datasetToColumns() 

            shipTrue = headingData.columns["NONE"]            
            relAz = relAzData.columns["NONE"]
            sza = szaData.columns["NONE"]

            esData.datasetToColumns()
            liData.datasetToColumns()
            ltData.datasetToColumns()
            
            esData.columns["SHIP_TRUE"] = shipTrue 
            liData.columns["SHIP_TRUE"] = shipTrue
            ltData.columns["SHIP_TRUE"] = shipTrue

            esData.columns["REL_AZ"] = relAz
            liData.columns["REL_AZ"] = relAz
            ltData.columns["REL_AZ"] = relAz

            esData.columns["SZA"] = sza
            liData.columns["SZA"] = sza
            ltData.columns["SZA"] = sza

            esData.columnsToDataset()
            liData.columnsToDataset()
            ltData.columnsToDataset()

        # Format the non-specific header block
        headerBlock = SeaBASSWriter.formatHeader(fp,root, level='1e')

        # Format each data block for individual output
        formattedEs, fieldsEs, unitsEs = SeaBASSWriter.formatData1e(esData,'es',root.attributes["ES_UNITS"])        
        formattedLi, fieldsLi, unitsLi  = SeaBASSWriter.formatData1e(liData,'li',root.attributes["LI_UNITS"])
        formattedLt, fieldsLt, unitsLt  = SeaBASSWriter.formatData1e(ltData,'lt',root.attributes["LT_UNITS"])                        

        # # Write SeaBASS files
        SeaBASSWriter.writeSeaBASS('ES',fp,headerBlock,formattedEs,fieldsEs,unitsEs)
        SeaBASSWriter.writeSeaBASS('LI',fp,headerBlock,formattedLi,fieldsLi,unitsLi)
        SeaBASSWriter.writeSeaBASS('LT',fp,headerBlock,formattedLt,fieldsLt,unitsLt)

    # Convert Level 2 data to SeaBASS file
    @staticmethod
    def outputTXT_Type2(fp):

        if not os.path.isfile(fp):
            print("SeaBASSWriter: no file to convert")
            return

        # Make sure hdf can be read
        try:
            root = HDFRoot.readHDF5(fp)
        except:
            print('SeaBassWriter: cannot open HDF. May be open in another app.')
            return

        if root is None:
            print("SeaBASSWriter: root is None")
            return

        # Get datasets to output
        irradianceGroup = root.getGroup("IRRADIANCE")
        radianceGroup = root.getGroup("RADIANCE")
        reflectanceGroup = root.getGroup("REFLECTANCE")

        esData = irradianceGroup.getDataset("ES_HYPER")
        liData = radianceGroup.getDataset("LI_HYPER")
        ltData = radianceGroup.getDataset("LT_HYPER")
        rrsData = reflectanceGroup.getDataset("Rrs_HYPER")

        if esData is None or liData is None or ltData is None or rrsData is None:
            print("SeaBASSWriter: Radiometric data is missing")
            return

        # Append latpos/lonpos to datasets
        ancGroup = root.getGroup("ANCILLARY")
        latposData = ancGroup.getDataset("LATITUDE")
        lonposData = ancGroup.getDataset("LONGITUDE")
        latposData.datasetToColumns()
        lonposData.datasetToColumns()
        latpos = latposData.columns["LATITUDE"]
        lonpos = lonposData.columns["LONGITUDE"]

        esData.datasetToColumns()
        liData.datasetToColumns()
        ltData.datasetToColumns()
        rrsData.datasetToColumns()

        esData.columns["LATITUDE"] = latpos
        liData.columns["LATITUDE"] = latpos
        ltData.columns["LATITUDE"] = latpos
        rrsData.columns["LATITUDE"] = latpos
        esData.columns["LONGITUDE"] = lonpos
        liData.columns["LONGITUDE"] = lonpos
        ltData.columns["LONGITUDE"] = lonpos
        rrsData.columns["LONGITUDE"] = lonpos

        esData.columnsToDataset()
        liData.columnsToDataset()
        ltData.columnsToDataset()
        rrsData.columnsToDataset()
    
        # # Append azimuth, heading, rotator, relAz, and solar elevation
        # azimuthData = ancGroup.getDataset("AZIMUTH")
        azimuthData = ancGroup.getDataset("SOLAR_AZ")
        headingData = ancGroup.getDataset("HEADING") # GPS
        # pitchData = ancGroup.getDataset("PITCH")
        # pointingData = ancGroup.getDataset("POINTING")
        # rollData = ancGroup.getDataset("ROLL")
        relAzData = ancGroup.getDataset("REL_AZ")
        # elevationData = ancGroup.getDataset("ELEVATION")
        szaData = ancGroup.getDataset("SZA")
        azimuthData.datasetToColumns()
        headingData.datasetToColumns()
        # pitchData.datasetToColumns()
        # pointingData.datasetToColumns()
        # rollData.datasetToColumns()            
        relAzData.datasetToColumns() 
        # elevationData.datasetToColumns() 
        szaData.datasetToColumns() 

        # Ancillary group, unlike most groups, will have named data columns in datasets (i.e. not NONE)
        # This allows for multiple data arrays in one dataset (e.g. FLAGS)
        azimuth = azimuthData.columns["SOLAR_AZ"]
        heading = headingData.columns["HEADING"] # Where is this from in no_tracker?
        # sasTrue = headingData.columns["SAS_True"]
        # pitch = pitchData.columns["SAS"]
        # rotator = pointingData.columns["ROTATOR"]
        # roll = rollData.columns["SAS"]
        relAz = relAzData.columns["REL_AZ"]
        # relAz = relAzData.columns["NONE"]
        # elevation = elevationData.columns["SUN"]
        sza = szaData.columns["SZA"]

        esData.datasetToColumns()
        liData.datasetToColumns()
        ltData.datasetToColumns()
        rrsData.datasetToColumns()
        
        esData.columns["SOLAR_AZ"] = azimuth
        liData.columns["SOLAR_AZ"] = azimuth
        ltData.columns["SOLAR_AZ"] = azimuth
        rrsData.columns["SOLAR_AZ"] = azimuth

        esData.columns["HEADING"] = heading
        liData.columns["HEADING"] = heading
        ltData.columns["HEADING"] = heading
        rrsData.columns["HEADING"] = heading

        # esData.columns["PITCH"] = pitch
        # liData.columns["PITCH"] = pitch
        # ltData.columns["PITCH"] = pitch
        
        # esData.columns["ROTATOR"] = rotator
        # liData.columns["ROTATOR"] = rotator
        # ltData.columns["ROTATOR"] = rotator
        # rrsData.columns["ROTATOR"] = rotator
        
        # esData.columns["ROLL"] = roll
        # liData.columns["ROLL"] = roll
        # ltData.columns["ROLL"] = roll

        esData.columns["REL_AZ"] = relAz
        liData.columns["REL_AZ"] = relAz
        ltData.columns["REL_AZ"] = relAz
        rrsData.columns["REL_AZ"] = relAz

        esData.columns["SZA"] = sza
        liData.columns["SZA"] = sza
        ltData.columns["SZA"] = sza
        rrsData.columns["SZA"] = sza

        esData.columnsToDataset()
        liData.columnsToDataset()
        ltData.columnsToDataset()
        rrsData.columnsToDataset()

        # Format the non-specific header block
        headerBlock = SeaBASSWriter.formatHeader(fp,root, level='2')

        # Format each data block for individual output
        formattedEs, fieldsEs, unitsEs = SeaBASSWriter.formatData2(esData,'es',irradianceGroup.attributes["ES_UNITS"])        
        formattedLi, fieldsLi, unitsLi  = SeaBASSWriter.formatData2(liData,'li',radianceGroup.attributes["LI_UNITS"])
        formattedLt, fieldsLt, unitsLt  = SeaBASSWriter.formatData2(ltData,'lt',radianceGroup.attributes["LT_UNITS"])
        formattedRrs, fieldsRrs, unitsRrs  = SeaBASSWriter.formatData2(rrsData,'rrs',reflectanceGroup.attributes["Rrs_UNITS"])

        # # Write SeaBASS files
        SeaBASSWriter.writeSeaBASS('ES',fp,headerBlock,formattedEs,fieldsEs,unitsEs)
        SeaBASSWriter.writeSeaBASS('LI',fp,headerBlock,formattedLi,fieldsLi,unitsLi)
        SeaBASSWriter.writeSeaBASS('LT',fp,headerBlock,formattedLt,fieldsLt,unitsLt)
        SeaBASSWriter.writeSeaBASS('Rrs',fp,headerBlock,formattedRrs,fieldsRrs,unitsRrs)