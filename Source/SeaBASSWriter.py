'''Write L2 files (Es and Rrs) to SeaBASS files. Rename to SeaBASS format.'''
import os
import time
import numpy as np

from Source import PATH_TO_CONFIG
from Source.HDFRoot import HDFRoot
from Source.SeaBASSHeader import SeaBASSHeader
from Source.ConfigFile import ConfigFile
from Source.Utilities import Utilities


class SeaBASSWriter:
    '''L2 SeaBASS file writer'''

    @staticmethod
    def sbFileName(fp,headerBlock,formattedData,dtype):
        version = SeaBASSHeader.settings["version"]
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
        headerBlock['data_file_name'] = outFileName.split('/')[-1]
        return outFileName

    @staticmethod
    def formatHeader(fp,node, level):

        seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
        seaBASSFP = os.path.join(PATH_TO_CONFIG, seaBASSHeaderFileName)
        SeaBASSHeader.loadSeaBASSHeader(seaBASSFP)
        headerBlock = SeaBASSHeader.settings

        # Dataset leading columns can be taken from any sensor
        referenceGroup = node.getGroup("IRRADIANCE")

        if level == '2':
            esData = referenceGroup.getDataset("ES_HYPER")
            ancillaryGroup = node.getGroup("ANCILLARY")
            wind = ancillaryGroup.getDataset("WINDSPEED")
            wind.datasetToColumns()
            winCol = wind.columns["WINDSPEED"]
            aveWind = np.nanmean(winCol)
        else:
            # Cannot get here. level force to 2
            esData = None

        if ConfigFile.settings['SensorType'].lower() =='trios':
            fileNameString = node.attributes['RAW_FILE_NAME']
            fileNameList = fileNameString.split(',')
            headerRawNames = ''
            for i, fp in enumerate(fileNameList):
                fp = fp.replace("[",'').replace("'",'').replace("]",'')
                if i==len(fileNameList)-1:
                    headerRawNames = headerRawNames + os.path.basename(fp)
                else:
                    headerRawNames = headerRawNames + os.path.basename(fp) +','
            headerBlock['original_file_name'] = headerRawNames
        else:
            headerBlock['original_file_name'] = node.attributes['RAW_FILE_NAME']
        # headerBlock['data_file_name'] = os.path.split(fp)[1].replace('.hdf','.sb')
        # headerBlock['data_file_name'] = SeaBASSWriter.sbFileName()
        headerBlock['comments'] = headerBlock['comments'] + f'\n! DateTime Processed = {time.asctime()}'

        # Convert Dates and Times
        # timeDT = esData.data['Datetime'].tolist() # Datetime has already been stripped off for saving the HDF
        dateDay = esData.data['Datetag'].tolist()
        dateDT = [Utilities.dateTagToDateTime(x) for x in dateDay]
        timeTag2 = esData.data['Timetag2'].tolist()
        timeDT = []
        for i, dtDT in enumerate(dateDT):
            timeDT.append(Utilities.timeTag2ToDateTime(dtDT,timeTag2[i]))

        # Python 2 format operator
        # startTime = "%02d:%02d:%02d[GMT]" % (min(timeDT).hour, min(timeDT).minute, min(timeDT).second)
        startTime = f"{min(timeDT).hour:02d}:{min(timeDT).minute:02d}:{min(timeDT).second:02d}[GMT]"
        # endTime = "%02d:%02d:%02d[GMT]" % (max(timeDT).hour, max(timeDT).minute, max(timeDT).second)
        endTime = f"{max(timeDT).hour:02d}:{max(timeDT).minute:02d}:{max(timeDT).second:02d}[GMT]"
        # startDate = "%04d%02d%02d" % (min(timeDT).year, min(timeDT).month, min(timeDT).day)
        startDate = f"{min(timeDT).year:04d}{min(timeDT).month:02d}{min(timeDT).day:02d}"
        # endDate = "%04d%02d%02d" % (max(timeDT).year, max(timeDT).month, max(timeDT).day)
        endDate = f"{max(timeDT).year:04d}{max(timeDT).month:02d}{max(timeDT).day:02d}"

        # Convert Position
        # Python 3 format syntax
        southLat = "{:.4f}[DEG]".format(min(esData.data['LATITUDE'].tolist()))
        northLat = "{:.4f}[DEG]".format(max(esData.data['LATITUDE'].tolist()))
        eastLon = "{:.4f}[DEG]".format(max(esData.data['LONGITUDE'].tolist()))
        westLon = "{:.4f}[DEG]".format(min(esData.data['LONGITUDE'].tolist()))

        if headerBlock['station'] == '' and ConfigFile.settings['bL2Stations'] == 1:
            station = node.getGroup('ANCILLARY').getDataset('STATION').data[0][2]
            headerBlock['station'] = station
        else:
            # if ConfigFile.settings['SensorType'].lower() =='trios':
                # headerBlock['station'] = headerRawNames
            headerBlock['station'] = node.attributes['L1BQC_FILE_NAME'].split('.')[0]
            # else:
                # headerBlock['station'] = node.attributes['RAW_FILE_NAME'].split('.')[0]
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
        if headerBlock['documents'] == '':
            headerBlock['documents'] = 'README.md'
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
        if dsDelta is not None:
            if 'Datetag' in dsDelta.columns:
                del dsDelta.columns['Datetag']
        dateDT = [Utilities.dateTagToDateTime(x) for x in dateDay]
        timeTag2 = dsCopy['Timetag2'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'Timetag2')
        if dsDelta is not None:
            if 'Timetag2' in dsDelta.columns:
                del dsDelta.columns['Timetag2']

        if dsDelta is not None:
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
        bincount = dsCopy['BINCOUNT'].tolist()
        newData = SeaBASSWriter.removeColumns(newData,'BINCOUNT')

        dsCopy = newData

        # Change field names for SeaBASS compliance
        bands = list(dsCopy.dtype.names)
        ls = ['date','time','lat','lon','RelAz','SZA','AOT','cloud','wind','bincount']

        fieldSpecs = {}
        fieldSpecs['rrs'] = {'fieldName': 'Rrs', 'unc_or_sd':'unc'}
        # fieldSpecs['nLw'] = {'fieldName': 'nLw', 'unc_or_sd':'unc'}
        fieldSpecs['Lwn'] = {'fieldName': 'Lwn', 'unc_or_sd':'unc'}
        fieldSpecs['Lwnex'] = {'fieldName': 'Lwnex', 'unc_or_sd':'unc'}
        fieldSpecs['es']  = {'fieldName': 'Es' , 'unc_or_sd':'unc'}

        fieldsLine = ls + [f'{fieldSpecs[dtype]["fieldName"]}{band}' for band in bands]

        if dsDelta is not None:
            fieldsLine = fieldsLine + [f'{fieldSpecs[dtype]["fieldName"]}{band}_{fieldSpecs[dtype]["unc_or_sd"]}' for band in bands]

        fieldsLineStr = ','.join(fieldsLine)

        lenRad = (len(dsCopy.dtype.names))
        unitsLine = ['yyyymmdd']
        unitsLine.append('hh:mm:ss')
        unitsLine.extend(['degrees']*4) # lat, lon, relAz, sza
        unitsLine.append('unitless') # AOD
        unitsLine.append('%') # cloud
        unitsLine.append('m/s') # wind
        unitsLine.append('none') # bincount
        unitsLine.extend([units]*lenRad) # data
        if dsDelta is not None:
            unitsLine.extend([units]*lenRad)    # data uncertainty
        unitsLineStr = ','.join(unitsLine)

        # Add data for each row
        dataOut = []
        formatStr = str('{:04d}{:02d}{:02d},{:02d}:{:02d}:{:02d},{:.4f},{:.4f},{:.1f},{:.1f}'\
            + ',{:.4f},{:.0f},{:.1f},{:.0f}' + ',{:.6f}'*lenRad)
        if dsDelta is not None:
            formatStr = formatStr + ',{:.6f}' * lenRad
        for i in range(dsCopy.shape[0]):
            subList = [lat[i],lon[i],relAz[i],sza[i],aod[i],cloud[i],wind[i],bincount[i]]
            lineList = [timeDT[i].year,timeDT[i].month,timeDT[i].day,timeDT[i].hour,timeDT[i].minute,timeDT[i].second] +\
                subList + list(dsCopy[i].tolist())

            if dsDelta is not None:
                lineList = lineList + list(dsDelta.data[i].tolist())

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

        outFileName = SeaBASSWriter.sbFileName(fp,headerBlock,formattedData,dtype)

        outFile = open(outFileName,'w',newline='\n')
        outFile.write('/begin_header\n')
        for key,value in headerBlock.items():
            if key != 'comments' and key != 'other_comments' and key != 'version':# and key != 'platform':
                line = f'/{key}={value}\n'
                outFile.write(line)
            # if key == 'platform':
            #     # NOTE: While header is pending at SeaBASS
            #     line = f'!/{key}={value}\n'
            #     outFile.write(line)
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
        except Exception:
            print('SeaBassWriter: cannot open HDF. May be open in another app.')
            return

        if root is None:
            print("SeaBASSWriter: root is None")
            return

        # Get datasets to output
        irradianceGroup = root.getGroup("IRRADIANCE")
        # radianceGroup = root.getGroup("RADIANCE")
        reflectanceGroup = root.getGroup("REFLECTANCE")

        rrsData = reflectanceGroup.getDataset("Rrs_HYPER")
        rrsUnc = reflectanceGroup.getDataset("Rrs_HYPER_unc")
        # Fallback uncertainty for non-SeaBird, Factory regime
        if rrsUnc is None:
            rrsUnc = reflectanceGroup.getDataset("Rrs_HYPER_sd")

        nLwData = reflectanceGroup.getDataset("nLw_HYPER")
        nLwUnc = reflectanceGroup.getDataset("nLw_HYPER_unc")
        # Fallback uncertainty for non-SeaBird, Factory regime
        if nLwUnc is None:
            nLwUnc = reflectanceGroup.getDataset("nLw_HYPER_sd")

        if ConfigFile.settings['bL2BRDF']:
            if ConfigFile.settings['bL2BRDF_fQ']:
                nLwData_BRDF = reflectanceGroup.getDataset("nLw_HYPER_M02")
                rrsData_BRDF = reflectanceGroup.getDataset("Rrs_HYPER_M02")
            if ConfigFile.settings['bL2BRDF_IOP']:
                nLwData_BRDF = reflectanceGroup.getDataset("nLw_HYPER_L11")
                rrsData_BRDF = reflectanceGroup.getDataset("Rrs_HYPER_L11")
            if ConfigFile.settings['bL2BRDF_O23']:
                nLwData_BRDF = reflectanceGroup.getDataset("nLw_HYPER_O23")
                rrsData_BRDF = reflectanceGroup.getDataset("Rrs_HYPER_O23")
            # There are currently no additional uncertainties added for BRDF
            # nLwUnc_BRDF = reflectanceGroup.getDataset("nLw_HYPER_unc")

        esData = irradianceGroup.getDataset("ES_HYPER")
        esUnc = irradianceGroup.getDataset("ES_HYPER_unc")
        # Fallback uncertainty for non-SeaBird, Factory regime
        if esUnc is None:
            esUnc = irradianceGroup.getDataset("ES_HYPER_sd")

        # Keep for now, but these won't be output for SeaBASS
        # They are of little use to others...
        # liData = radianceGroup.getDataset("LI_HYPER")
        # ltData = radianceGroup.getDataset("LT_HYPER")

        # if esData is None or liData is None or ltData is None or rrsData is None or nLwData is None:
        if esData is None or rrsData is None or nLwData is None:
            print("SeaBASSWriter: Radiometric data is missing")
            return

        # Append bincount to datasets
        bincountData = reflectanceGroup.getDataset("Ensemble_N")
        bincountData.datasetToColumns()
        bincount = bincountData.columns["N"]


        # Append latpos/lonpos to datasets
        ancGroup = root.getGroup("ANCILLARY")
        latposData = ancGroup.getDataset("LATITUDE")
        lonposData = ancGroup.getDataset("LONGITUDE")
        latposData.datasetToColumns()
        lonposData.datasetToColumns()
        latpos = latposData.columns["LATITUDE"]
        lonpos = lonposData.columns["LONGITUDE"]

        rrsData.datasetToColumns()
        nLwData.datasetToColumns()

        if ConfigFile.settings['bL2BRDF']:
            nLwData_BRDF.datasetToColumns()
            rrsData_BRDF.datasetToColumns()

        # In the case of TriOS factory, rrsUnc is None so datasetToColumns() is not applicable
        if rrsUnc is not None:
            rrsUnc.datasetToColumns()
            nLwUnc.datasetToColumns()

        esData.datasetToColumns()
        esUnc.datasetToColumns()
        # liData.datasetToColumns()
        # ltData.datasetToColumns()

        # Truncate wavebands to desired output
        esCols = esData.columns
        esColsUnc = esUnc.columns
        rrsCols = rrsData.columns
        nLwCols = nLwData.columns
        if ConfigFile.settings['bL2BRDF']:
            nLwCols_BRDF = nLwData_BRDF.columns
            rrsCols_BRDF = rrsData_BRDF.columns

        # In the case of TriOS factory, rrsUnc is None
        if rrsUnc is not None:
            rrsColsUnc = rrsUnc.columns
            nLwColsUnc = nLwUnc.columns
        else:
            rrsColsUnc = None
            nLwColsUnc = None

        for k in list(esCols.keys()):
            if (k != 'Datetag') and (k != 'Timetag2'):
                if float(k) < minWave or float(k) > maxWave:
                    del esCols[k]
                    del esColsUnc[k]
        for k in list(rrsCols.keys()):
            if (k != 'Datetag') and (k != 'Timetag2'):
                if float(k) < minWave or float(k) > maxWave:
                    del rrsCols[k]
                    if rrsUnc is not None:
                        del rrsColsUnc[k]
        for k in list(nLwCols.keys()):
            if (k != 'Datetag') and (k != 'Timetag2'):
                if float(k) < minWave or float(k) > maxWave:
                    del nLwCols[k]
                    if nLwUnc is not None:
                        del nLwColsUnc[k]
        if ConfigFile.settings['bL2BRDF']:
            for k in list(nLwCols_BRDF.keys()):
                if (k != 'Datetag') and (k != 'Timetag2'):
                    if float(k) < minWave or float(k) > maxWave:
                        del nLwCols_BRDF[k]
            for k in list(rrsCols_BRDF.keys()):
                if (k != 'Datetag') and (k != 'Timetag2'):
                    if float(k) < minWave or float(k) > maxWave:
                        del rrsCols_BRDF[k]

        esData.columns = esCols
        esUnc.columns = esColsUnc
        rrsData.columns = rrsCols
        nLwData.columns = nLwCols
        if ConfigFile.settings['bL2BRDF']:
            nLwData_BRDF.columns = nLwCols_BRDF
            rrsData_BRDF.columns = rrsCols_BRDF

        if rrsUnc is not None:
            rrsUnc.columns = rrsColsUnc
            nLwUnc.columns = nLwColsUnc

        esData.columns["BINCOUNT"] = bincount
        rrsData.columns["BINCOUNT"] = bincount
        nLwData.columns["BINCOUNT"] = bincount
        esData.columns["LATITUDE"] = latpos
        rrsData.columns["LATITUDE"] = latpos
        nLwData.columns["LATITUDE"] = latpos
        esData.columns["LONGITUDE"] = lonpos
        rrsData.columns["LONGITUDE"] = lonpos
        nLwData.columns["LONGITUDE"] = lonpos
        rrsData.columnsToDataset()
        nLwData.columnsToDataset()
        if ConfigFile.settings['bL2BRDF']:
            nLwData_BRDF.columns["BINCOUNT"] = bincount
            nLwData_BRDF.columns["LATITUDE"] = latpos
            nLwData_BRDF.columns["LONGITUDE"] = lonpos
            nLwData_BRDF.columnsToDataset()
            rrsData_BRDF.columns["BINCOUNT"] = bincount
            rrsData_BRDF.columns["LATITUDE"] = latpos
            rrsData_BRDF.columns["LONGITUDE"] = lonpos
            rrsData_BRDF.columnsToDataset()
        # liData.columns["LATITUDE"] = latpos
        # ltData.columns["LATITUDE"] = latpos
        # liData.columns["LONGITUDE"] = lonpos
        # ltData.columns["LONGITUDE"] = lonpos

        if rrsUnc is not None:
            rrsUnc.columnsToDataset()
            nLwUnc.columnsToDataset()

        esData.columnsToDataset()
        esUnc.columnsToDataset()
        # liData.columnsToDataset()
        # ltData.columnsToDataset()

        # # Append ancillary datasets
        # Required
        azimuthData = ancGroup.getDataset("SOLAR_AZ")
        relAzData = ancGroup.getDataset("REL_AZ")
        szaData = ancGroup.getDataset("SZA")
        windData = ancGroup.getDataset("WINDSPEED")
        azimuthData.datasetToColumns()
        relAzData.datasetToColumns()
        szaData.datasetToColumns()
        windData.datasetToColumns()

        azimuth = azimuthData.columns["SOLAR_AZ"]
        relAz = relAzData.columns["REL_AZ"]
        sza = szaData.columns["SZA"]
        wind = windData.columns["WINDSPEED"]

        # Optional
        aodData = ancGroup.getDataset("AOD")
        headingData = ancGroup.getDataset("HEADING")
        cloudData = ancGroup.getDataset("CLOUD")

        if aodData is not None:
            aodData.datasetToColumns()
            aod = aodData.columns["AOD"]
        else:
            aod = np.empty((1,len(wind)))
            aod = aod[0]*np.nan
            aod = aod.tolist()
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
        nLwData.columns["AOD"] = aod
        esData.columns["AOD"] = aod
        # liData.columns["AOD"] = aod
        # ltData.columns["AOD"] = aod

        rrsData.columns["CLOUD"] = cloud
        nLwData.columns["CLOUD"] = cloud
        esData.columns["CLOUD"] = cloud
        # liData.columns["CLOUD"] = cloud
        # ltData.columns["CLOUD"] = cloud

        rrsData.columns["SOLAR_AZ"] = azimuth
        nLwData.columns["SOLAR_AZ"] = azimuth
        esData.columns["SOLAR_AZ"] = azimuth
        # liData.columns["SOLAR_AZ"] = azimuth
        # ltData.columns["SOLAR_AZ"] = azimuth

        rrsData.columns["HEADING"] = heading
        nLwData.columns["HEADING"] = heading
        esData.columns["HEADING"] = heading
        # liData.columns["HEADING"] = heading
        # ltData.columns["HEADING"] = heading

        rrsData.columns["REL_AZ"] = relAz
        nLwData.columns["REL_AZ"] = relAz
        esData.columns["REL_AZ"] = relAz
        # liData.columns["REL_AZ"] = relAz
        # ltData.columns["REL_AZ"] = relAz

        rrsData.columns["SZA"] = sza
        nLwData.columns["SZA"] = sza
        esData.columns["SZA"] = sza
        # liData.columns["SZA"] = sza
        # ltData.columns["SZA"] = sza

        rrsData.columns["WIND"] = wind
        nLwData.columns["WIND"] = wind
        esData.columns["WIND"] = wind
        # liData.columns["WIND"] = wind
        # ltData.columns["WIND"] = wind

        rrsData.columnsToDataset()
        nLwData.columnsToDataset()
        esData.columnsToDataset()
        # liData.columnsToDataset()
        # ltData.columnsToDataset()

        if ConfigFile.settings['bL2BRDF']:
            nLwData_BRDF.columns["AOD"] = aod
            nLwData_BRDF.columns["CLOUD"] = cloud
            nLwData_BRDF.columns["SOLAR_AZ"] = azimuth
            nLwData_BRDF.columns["HEADING"] = heading
            nLwData_BRDF.columns["REL_AZ"] = relAz
            nLwData_BRDF.columns["SZA"] = sza
            nLwData_BRDF.columns["WIND"] = wind
            nLwData_BRDF.columnsToDataset()
            rrsData_BRDF.columns["AOD"] = aod
            rrsData_BRDF.columns["CLOUD"] = cloud
            rrsData_BRDF.columns["SOLAR_AZ"] = azimuth
            rrsData_BRDF.columns["HEADING"] = heading
            rrsData_BRDF.columns["REL_AZ"] = relAz
            rrsData_BRDF.columns["SZA"] = sza
            rrsData_BRDF.columns["WIND"] = wind
            rrsData_BRDF.columnsToDataset()

        # Format the non-specific header block
        headerBlock = SeaBASSWriter.formatHeader(fp,root, level='2')

        # Format each data block for individual output
        formattedRrs, fieldsRrs, unitsRrs  = SeaBASSWriter.formatData2(rrsData,rrsUnc,'rrs',reflectanceGroup.attributes["Rrs_UNITS"])
        formattednLw, fieldsnLw, unitsnLw  = SeaBASSWriter.formatData2(nLwData,nLwUnc,'Lwn',reflectanceGroup.attributes["nLw_UNITS"])
        formattedEs, fieldsEs, unitsEs = SeaBASSWriter.formatData2(esData,esUnc,'es',irradianceGroup.attributes["ES_UNITS"])
        if ConfigFile.settings['bL2BRDF']:
            formattednLw_BRDF, fieldsnLw_BRDF, unitsnLw_BRDF  = SeaBASSWriter.formatData2(nLwData_BRDF,nLwUnc,'Lwnex',reflectanceGroup.attributes["nLw_UNITS"])
            formattedRrs_BRDF, fieldsRrs_BRDF, unitsRrs_BRDF  = SeaBASSWriter.formatData2(rrsData_BRDF,rrsUnc,'rrs',reflectanceGroup.attributes["Rrs_UNITS"])

        # formattedLi, fieldsLi, unitsLi  = SeaBASSWriter.formatData2(liData,'li',radianceGroup.attributes["LI_UNITS"])
        # formattedLt, fieldsLt, unitsLt  = SeaBASSWriter.formatData2(ltData,'lt',radianceGroup.attributes["LT_UNITS"])

        # # Write SeaBASS files
        # Need to update headerBlock for BRDF
        # headerBlock['BRDF_correction'] = SeaBASSHeader.settings['BRDF_correction']
        BRDF_correction = SeaBASSHeader.settings['BRDF_correction']
        headerBlock['BRDF_correction'] = 'noBRDF'
        SeaBASSWriter.writeSeaBASS('Rrs',fp,headerBlock,formattedRrs,fieldsRrs,unitsRrs)
        SeaBASSWriter.writeSeaBASS('Lwn',fp,headerBlock,formattednLw,fieldsnLw,unitsnLw)
        SeaBASSWriter.writeSeaBASS('Es',fp,headerBlock,formattedEs,fieldsEs,unitsEs)
        SeaBASSHeader.settings['BRDF_correction'] = BRDF_correction # Changes headerBlock as well.


        if ConfigFile.settings['bL2BRDF']:
            # Use M02 and L11 in filenames to avoid conflict with datatype "_IOP_"
            if ConfigFile.settings['bL2BRDF_fQ']:
                SeaBASSWriter.writeSeaBASS('Lwn_M02',fp,headerBlock,formattednLw_BRDF,fieldsnLw_BRDF,unitsnLw_BRDF)
                SeaBASSWriter.writeSeaBASS('Rrs_M02',fp,headerBlock,formattedRrs_BRDF,fieldsRrs_BRDF,unitsRrs_BRDF)

            if ConfigFile.settings['bL2BRDF_IOP']:
                SeaBASSWriter.writeSeaBASS('Lwn_L11',fp,headerBlock,formattednLw_BRDF,fieldsnLw_BRDF,unitsnLw_BRDF)
                SeaBASSWriter.writeSeaBASS('Rrs_L11',fp,headerBlock,formattedRrs_BRDF,fieldsRrs_BRDF,unitsRrs_BRDF)

            if ConfigFile.settings['bL2BRDF_O23']:
                SeaBASSWriter.writeSeaBASS('Lwn_O23',fp,headerBlock,formattednLw_BRDF,fieldsnLw_BRDF,unitsnLw_BRDF)
                SeaBASSWriter.writeSeaBASS('Rrs_O23',fp,headerBlock,formattedRrs_BRDF,fieldsRrs_BRDF,unitsRrs_BRDF)

        # SeaBASSWriter.writeSeaBASS('LI',fp,headerBlock,formattedLi,fieldsLi,unitsLi)
        # SeaBASSWriter.writeSeaBASS('LT',fp,headerBlock,formattedLt,fieldsLt,unitsLt)

        return headerBlock['data_file_name']
