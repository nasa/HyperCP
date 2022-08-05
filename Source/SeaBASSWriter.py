
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

        if level == '2':
            # referenceGroup = node.getGroup("IRRADIANCE")
            esData = referenceGroup.getDataset("ES_HYPER")
            # if ConfigFile.settings["bL1cSolarTracker"]:
            ancillaryGroup = node.getGroup("ANCILLARY")
            # else:
            #     ancillaryGroup = node.getGroup("ANCILLARY_METADATA")
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

        if headerBlock['station'] == '' and ConfigFile.settings['bL2Stations'] == 1:
            station = node.getGroup('ANCILLARY').getDataset('STATION').data[0][2]
            # headerBlock['station'] = node.attributes['RAW_FILE_NAME'].split('.')[0]
            headerBlock['station'] = station
        if headerBlock['start_time'] == '':
            headerBlock['start_time'] = startTime
        if headerBlock['end_time'] == '':
            headerBlock['end_time'] = endTime
        if headerBlock['start_date'] == '':
            headerBlock['start_date'] = startDate
        if headerBlock['end_date'] == '':
            headerBlock['end_date'] = endDate
        if headerBlock['north_latitude'] == '':
            headerBlock['north_latitude'] = northLat
        if headerBlock['south_latitude'] == '':
            headerBlock['south_latitude'] = southLat
        if headerBlock['east_longitude'] == '':
            headerBlock['east_longitude'] = eastLon
        if headerBlock['west_longitude'] == '':
            headerBlock['west_longitude'] = westLon
        if level == '2':
            headerBlock['wind_speed'] = aveWind
        return headerBlock


    @staticmethod
    def formatData2(dataset,dsDelta,dtype, units):

        dsCopy = dataset.data.copy() # By copying here, we leave the ancillary data tacked on to radiometry for later
        # dsDelta = dsDelta.data.copy()

        # Convert Dates and Times and remove from dataset
        newData = dsCopy
        dateDay = dsCopy['Datetag'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'Datetag')
        del dsDelta.columns['Datetag']
        dateDT = [Utilities.dateTagToDateTime(x) for x in dateDay]
        timeTag2 = dsCopy['Timetag2'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'Timetag2')
        del dsDelta.columns['Timetag2']

        dsDelta.columnsToDataset()

        timeDT = []
        for i in range(len(dateDT)):
            timeDT.append(Utilities.timeTag2ToDateTime(dateDT[i],timeTag2[i]))

        # Retrieve ancillaries and remove from dataset (they are not on deltas)
        lat = dsCopy['LATITUDE'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'LATITUDE')
        lon = dsCopy['LONGITUDE'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'LONGITUDE')
        aod = dsCopy['AOD'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'AOD')
        cloud = dsCopy['CLOUD'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'CLOUD')
        sza = dsCopy['SZA'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'SZA')
        relAz = dsCopy['REL_AZ'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'REL_AZ')
        newData = SeaBASSWriter.removeColumns(newData,'HEADING')
        newData = SeaBASSWriter.removeColumns(newData,'SOLAR_AZ')
        wind = dsCopy['WIND'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'WIND')

        dsCopy = newData

        # Change field names for SeaBASS compliance
        bands = list(dsCopy.dtype.names)
        ls = ['date','time','lat','lon','RelAz','SZA','AOT','cloud','wind']

        if dtype == 'rrs':
            fieldName = 'Rrs'
        elif dtype == 'es':
            fieldName = 'Es'

        if dtype=='rrs':
            fieldsLineStr = ','.join(ls + [f'{fieldName}{band}' for band in bands] \
                + [f'{fieldName}{band}_unc' for band in bands])
        else:
            fieldsLineStr = ','.join(ls + [f'{fieldName}{band}' for band in bands] \
                + [f'{fieldName}{band}_sd' for band in bands])

        lenRad = (len(dsCopy.dtype.names))
        unitsLine = ['yyyymmdd']
        unitsLine.append('hh:mm:ss')
        unitsLine.extend(['degrees']*4) # lat, lon, relAz, sza
        unitsLine.append('unitless') # AOD
        unitsLine.append('%') # cloud
        unitsLine.append('m/s') # wind
        unitsLine.extend([units]*lenRad) # data
        unitsLine.extend([units]*lenRad)    # data uncertainty
        unitsLineStr = ','.join(unitsLine)

        # Add data for each row
        dataOut = []
        formatStr = str('{:04d}{:02d}{:02d},{:02d}:{:02d}:{:02d},{:.4f},{:.4f},{:.1f},{:.1f}'\
            + ',{:.4f},{:.0f},{:.1f}'\
             + ',{:.6f}'*lenRad  + ',{:.6f}'*lenRad)
        for i in range(dsCopy.shape[0]):
            subList = [lat[i],lon[i],relAz[i],sza[i],aod[i],cloud[i],wind[i]]
            lineList = [timeDT[i].year,timeDT[i].month,timeDT[i].day,timeDT[i].hour,timeDT[i].minute,timeDT[i].second] +\
                subList + list(dsCopy[i].tolist()) + list(dsDelta.data[i].tolist())

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

        # outFileName = f'{os.path.split(fp)[0]}/SeaBASS/{os.path.split(fp)[1].replace(".hdf",f"_{dtype}_{version}.sb")}'
        # Conforms to SeaBASS file names: Experiment_Cruise_Platform_Instrument_YYMMDD_HHmmSS_Level_DataType_Revision
        if ConfigFile.settings['bL2Stations']:
            station = str(headerBlock['station']).replace('.','_')
            outFileName = \
                (   f"{os.path.split(fp)[0]}/SeaBASS/{headerBlock['experiment']}_{headerBlock['cruise']}_"
                    f"{headerBlock['platform']}_{headerBlock['instrument_model']}_{formattedData[0].split(',')[0]}_"
                    f"{formattedData[0].split(',')[1].replace(':','')}_L2_{dtype}_STATION_{station}_{version}.sb")
        else:
            outFileName = \
            (   f"{os.path.split(fp)[0]}/SeaBASS/{headerBlock['experiment']}_{headerBlock['cruise']}_"
                f"{headerBlock['platform']}_{headerBlock['instrument_model']}_{formattedData[0].split(',')[0]}_"
                f"{formattedData[0].split(',')[1].replace(':','')}_L2_{dtype}_{version}.sb")

        outFile = open(outFileName,'w',newline='\n')
        outFile.write('/begin_header\n')
        for key,value in headerBlock.items():
            if key != 'comments' and key != 'other_comments' and key != 'version' and key != 'platform':
                line = f'/{key}={value}\n'
                outFile.write(line)
            if key == 'platform':
                line = f'!/{key}={value}\n'
                outFile.write(line)
        outFile.write(headerBlock['comments']+'\n')
        outFile.write(headerBlock['other_comments']+'\n')
        outFile.write('/fields='+fields+'\n')
        outFile.write('/units='+units+'\n')
        outFile.write('/end_header\n')

        for line in formattedData:
            outFile.write(f'{line}\n')

        outFile.close()

    # Convert Level 2 data to SeaBASS file
    @staticmethod
    def outputTXT_Type2(fp):

        minWave = 350
        maxWave = 750

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

        rrsData = reflectanceGroup.getDataset("Rrs_HYPER")
        rrsDataDelta = reflectanceGroup.getDataset("Rrs_HYPER_unc")
        esData = irradianceGroup.getDataset("ES_HYPER")
        esDataDelta = irradianceGroup.getDataset("ES_HYPER_sd")

        # Keep for now, but these won't be output for SeaBASS
        # They are of little use to others...
        liData = radianceGroup.getDataset("LI_HYPER")
        ltData = radianceGroup.getDataset("LT_HYPER")


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

        rrsData.datasetToColumns()
        rrsDataDelta.datasetToColumns()
        esData.datasetToColumns()
        esDataDelta.datasetToColumns()
        liData.datasetToColumns()
        ltData.datasetToColumns()

        # Truncate wavebands to desired output
        esCols = esData.columns
        esColsD = esDataDelta.columns
        rrsCols = rrsData.columns
        rrsColsD = rrsDataDelta.columns
        for k in list(esCols.keys()):
            if (k != 'Datetag') and (k != 'Timetag2'):
                if float(k) < minWave or float(k) > maxWave:
                     del esCols[k]
                     del esColsD[k]
        for k in list(rrsCols.keys()):
            if (k != 'Datetag') and (k != 'Timetag2'):
                if float(k) < minWave or float(k) > maxWave:
                     del rrsCols[k]
                     del rrsColsD[k]
        esData.columns = esCols
        esDataDelta.columns = esColsD
        rrsData.columns = rrsCols
        rrsDataDelta.columns = rrsColsD

        esData.columns["LATITUDE"] = latpos
        rrsData.columns["LATITUDE"] = latpos
        esData.columns["LONGITUDE"] = lonpos
        rrsData.columns["LONGITUDE"] = lonpos
        liData.columns["LATITUDE"] = latpos
        ltData.columns["LATITUDE"] = latpos
        liData.columns["LONGITUDE"] = lonpos
        ltData.columns["LONGITUDE"] = lonpos

        rrsData.columnsToDataset()
        rrsDataDelta.columnsToDataset()
        esData.columnsToDataset()
        esDataDelta.columnsToDataset()
        liData.columnsToDataset()
        ltData.columnsToDataset()

        # # Append ancillary datasets
        aodData = ancGroup.getDataset("AOD")
        cloudData = ancGroup.getDataset("CLOUD")
        azimuthData = ancGroup.getDataset("SOLAR_AZ")
        headingData = ancGroup.getDataset("HEADING")
        relAzData = ancGroup.getDataset("REL_AZ")
        szaData = ancGroup.getDataset("SZA")
        windData = ancGroup.getDataset("WINDSPEED")

        aodData.datasetToColumns()
        azimuthData.datasetToColumns()
        relAzData.datasetToColumns()
        szaData.datasetToColumns()
        windData.datasetToColumns()

        aod = aodData.columns["AOD"]
        azimuth = azimuthData.columns["SOLAR_AZ"]
        relAz = relAzData.columns["REL_AZ"]
        sza = szaData.columns["SZA"]
        wind = windData.columns["WINDSPEED"]

        if cloudData is not None:
            cloudData.datasetToColumns()
            cloud = cloudData.columns["CLOUD"]
        else:
            cloud = np.empty((1,len(wind)))
            cloud = cloud[0]*np.nan
            cloud = cloud.tolist()
        if headingData is not None:
            headingData.datasetToColumns()
            if 'SHIP_TRUE' in headingData.columns:
                # From Satlantic SolarTracker
                heading = headingData.columns["SHIP_TRUE"]
            elif 'HEADING' in headingData.columns:
                # From pySAS
                heading = headingData.columns["HEADING"]
            elif 'SHIP' in headingData.columns:
                # Also from pySAS??
                heading = headingData.columns["SHIP"]
            elif 'NONE' in headingData.columns:
                # Most likely from Ancillary
                heading = headingData.columns["NONE"]
            else:
                # Fallback for Archimedes Solartracker
                heading = headingData.columns["SAS_TRUE"]
        else:
            heading = np.empty((1,len(wind)))
            heading = heading[0]*np.nan
            heading = heading.tolist()

        # No need to add all ancillary to the uncertainty deltas
        rrsData.columns["AOD"] = aod
        esData.columns["AOD"] = aod
        liData.columns["AOD"] = aod
        ltData.columns["AOD"] = aod

        rrsData.columns["CLOUD"] = cloud
        esData.columns["CLOUD"] = cloud
        liData.columns["CLOUD"] = cloud
        ltData.columns["CLOUD"] = cloud

        rrsData.columns["SOLAR_AZ"] = azimuth
        esData.columns["SOLAR_AZ"] = azimuth
        liData.columns["SOLAR_AZ"] = azimuth
        ltData.columns["SOLAR_AZ"] = azimuth

        esData.columns["HEADING"] = heading
        liData.columns["HEADING"] = heading
        ltData.columns["HEADING"] = heading
        rrsData.columns["HEADING"] = heading

        esData.columns["REL_AZ"] = relAz
        liData.columns["REL_AZ"] = relAz
        ltData.columns["REL_AZ"] = relAz
        rrsData.columns["REL_AZ"] = relAz

        esData.columns["SZA"] = sza
        liData.columns["SZA"] = sza
        ltData.columns["SZA"] = sza
        rrsData.columns["SZA"] = sza

        esData.columns["WIND"] = wind
        liData.columns["WIND"] = wind
        ltData.columns["WIND"] = wind
        rrsData.columns["WIND"] = wind

        esData.columnsToDataset()
        liData.columnsToDataset()
        ltData.columnsToDataset()
        rrsData.columnsToDataset()

        # Format the non-specific header block
        headerBlock = SeaBASSWriter.formatHeader(fp,root, level='2')

        # Format each data block for individual output
        formattedEs, fieldsEs, unitsEs = SeaBASSWriter.formatData2(esData,esDataDelta,'es',irradianceGroup.attributes["ES_UNITS"])
        # formattedLi, fieldsLi, unitsLi  = SeaBASSWriter.formatData2(liData,'li',radianceGroup.attributes["LI_UNITS"])
        # formattedLt, fieldsLt, unitsLt  = SeaBASSWriter.formatData2(ltData,'lt',radianceGroup.attributes["LT_UNITS"])
        formattedRrs, fieldsRrs, unitsRrs  = SeaBASSWriter.formatData2(rrsData,rrsDataDelta,'rrs',reflectanceGroup.attributes["Rrs_UNITS"])

        # # Write SeaBASS files
        SeaBASSWriter.writeSeaBASS('Es',fp,headerBlock,formattedEs,fieldsEs,unitsEs)
        # SeaBASSWriter.writeSeaBASS('LI',fp,headerBlock,formattedLi,fieldsLi,unitsLi)
        # SeaBASSWriter.writeSeaBASS('LT',fp,headerBlock,formattedLt,fieldsLt,unitsLt)
        SeaBASSWriter.writeSeaBASS('Rrs',fp,headerBlock,formattedRrs,fieldsRrs,unitsRrs)