
import csv
import os
import datetime

from HDFRoot import HDFRoot
from SeaBASSHeader import SeaBASSHeader
from ConfigFile import ConfigFile
from Utilities import Utilities


class SeaBASSWriter:

    @staticmethod
    def formatHeader(fp,node):
        
        # seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
        headerBlock = SeaBASSHeader.settings        

        # Leading columns can be taken from any sensor 
        referenceGroup = node.getGroup("Reference")
        esData = referenceGroup.getDataset("ES_hyperspectral")

        headerBlock['original_file_name'] = node.attributes['RAW_FILE_NAME']
        headerBlock['data_file_name'] = os.path.split(fp)[1]

        # Convert Dates and Times
        dateDay = esData.data['Datetag'].tolist()
        dateDT = [Utilities.dateTagToDateTime(x) for x in dateDay]
        timeTag2 = esData.data['Timetag2'].tolist()
        timeDT = []
        for i in range(len(dateDT)):
            timeDT.append(Utilities.timeTag2ToDateTime(dateDT[i],timeTag2[i]))
        # time = [Utilities.timeTagToDateTime(y,x) for x,y in date,timeTag]  
        # Python 2 format operator       
        startTime = "%02d:%02d:%02d [UTC]" % (min(timeDT).hour, min(timeDT).minute, min(timeDT).second)
        endTime = "%02d:%02d:%02d [UTC]" % (max(timeDT).hour, max(timeDT).minute, max(timeDT).second)
        startDate = "%04d%02d%02d" % (min(timeDT).year, min(timeDT).month, min(timeDT).day)      
        endDate = "%04d%02d%02d" % (max(timeDT).year, max(timeDT).month, max(timeDT).day)

        # Convert Position
        # Python 3 format syntax
        southLat = "{:.4f}".format(min(esData.data['LATPOS'].tolist()))
        northLat = "{:.4f}".format(max(esData.data['LATPOS'].tolist()))
        eastLon = "{:.4f}".format(max(esData.data['LONPOS'].tolist()))
        westLon = "{:.4f}".format(min(esData.data['LONPOS'].tolist()))

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
        
        return headerBlock

        # headerBlock = print(json.dumps(SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)))
    
   
    @staticmethod
    def formatData3(dataset,dtype, units):        
        ls = list(dataset.data.dtype.names)
        fieldsLineStr = ','.join(list(dataset.data.dtype.names)[:5] + [f'{dtype}{band}' for band in ls[5:]])
        
        lenRad = (len(dataset.data.dtype.names)-5)
        unitsLine = ['yymmdd']
        unitsLine.append('hh:mm:ss')
        unitsLine.extend(['degrees']*3)
        unitsLine.extend([units]*lenRad)
        unitsLineStr = ','.join(unitsLine)
        
        # Convert Dates and Times
        dateDay = dataset.data['Datetag'].tolist()
        dateDT = [Utilities.dateTagToDateTime(x) for x in dateDay]
        timeTag2 = dataset.data['Timetag2'].tolist()
        timeDT = []
        for i in range(len(dateDT)):
            timeDT.append(Utilities.timeTag2ToDateTime(dateDT[i],timeTag2[i]))
                     
        # Add data for each row
        dataOut = []
        formatStr = str('{:04d}{:02d}{:02d},{:02d}:{:02d}:{:02d},{:.4f},{:.4f},{:.1f}' + ',{:.6f}'*lenRad)
        for i in range(dataset.data.shape[0]):                        
            lineList = [timeDT[i].year,timeDT[i].month,timeDT[i].day,timeDT[i].hour,timeDT[i].minute,timeDT[i].second]+list(dataset.data[i].tolist()[2:])
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
        
        outFileName = f'{os.path.split(fp)[0]}/SeaBASS/{dtype}{os.path.split(fp)[1].replace(".hdf",".out")}'

        outFile = open(outFileName,'w')
        outFile.write('/begin_header\n')
        for key,value in headerBlock.items():
            if key != 'comments':
                # Python 3 f-string
                line = f'/{key}={value}\n'
                outFile.write(line)
        outFile.write(headerBlock['comments']+'\n')
        outFile.write('/missing_data=-999\n')
        outFile.write('/delimiter=comma\n')
        outFile.write('/fields='+fields+'\n')
        outFile.write('/units='+units+'\n')
        outFile.write('/end_header\n')
        
        for line in formattedData:
            outFile.write(f'{line}\n')
        
        outFile.close()

        # # Create output directory
        # csvdir = os.path.join(dirpath, 'csv')
        # os.makedirs(csvdir, exist_ok=True)

        # # Write csv file
        # filename = name + "_" + sensorName + "_" + level
        # csvPath = os.path.join(csvdir, filename + ".csv")
        # #np.savetxt(csvPath, data, delimiter=',')
        # with open(csvPath, 'w') as f:
        #     writer = csv.writer(f)
        #     writer.writerows(data)

    @staticmethod
    def outputTXT_L3(fp):
        print('Writing type 3 SeaBASS file')
        SeaBASSWriter.outputTXT_Type3(fp, "L3")

    # @staticmethod
    # def outputTXT_L4(fp):
    #     SeaBASSWriter.outputTXT_Type4(fp, "L4")
    #     SeaBASSWriter.outputTXT_Type4(fp, "L4-flags")


    # Convert Level 3 data to SeaBASS file
    @staticmethod
    def outputTXT_Type3(fp, level):

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
        referenceGroup = root.getGroup("Reference")
        sasGroup = root.getGroup("SAS")

        esData = referenceGroup.getDataset("ES_hyperspectral")
        liData = sasGroup.getDataset("LI_hyperspectral")
        ltData = sasGroup.getDataset("LT_hyperspectral")

        if esData is None or liData is None or ltData is None:
            print("SeaBASSWriter: Radiometric data is missing")
            return

        # Format the non-specific header block
        headerBlock = SeaBASSWriter.formatHeader(fp,root)

        # Format each data block for individual output
        formattedEs, fieldsEs, unitsEs = SeaBASSWriter.formatData3(esData,'es',root.attributes["ES_UNITS"])        
        formattedLi, fieldsLi, unitsLi  = SeaBASSWriter.formatData3(liData,'li',root.attributes["LI_UNITS"])
        formattedLt, fieldsLt, unitsLt  = SeaBASSWriter.formatData3(ltData,'lt',root.attributes["LT_UNITS"])                        

        # # Write SeaBASS files
        SeaBASSWriter.writeSeaBASS('ES',fp,headerBlock,formattedEs,fieldsEs,unitsEs)
        SeaBASSWriter.writeSeaBASS('LI',fp,headerBlock,formattedLi,fieldsLi,unitsLi)
        SeaBASSWriter.writeSeaBASS('LT',fp,headerBlock,formattedLt,fieldsLt,unitsLt)

    # # Convert Level 4 data to SeaBASS file
    # @staticmethod
    # def outputTXT_Type4(fp, level):
    
    #     if not os.path.isfile(fp):
    #         return

    #     # Make sure hdf can be read
    #     root = HDFRoot.readHDF5(fp)
    #     if root is None:
    #         print("outputSeaBASS: root is None")
    #         return

    #     #name = filename[28:43]
    #     name = filename[0:15]

    #     # Get datasets to output
    #     gp = root.getGroup("Reflectance")

    #     esData = gp.getDataset("ES")
    #     liData = gp.getDataset("LI")
    #     ltData = gp.getDataset("LT")
    #     rrsData = gp.getDataset("Rrs")

    #     if esData is None or liData is None or ltData is None or rrsData is None:
    #         return

    #     # Format for output
    #     es = SeaBASSWriter.formatData3(esData)
    #     li = SeaBASSWriter.formatData3(liData)
    #     lt = SeaBASSWriter.formatData3(ltData)
    #     rrs = SeaBASSWriter.formatData3(rrsData)

    #     # Write SeaBASS files
    #     SeaBASSWriter.writeSeaBASS(name, dirpath, es, "ES", level)
    #     SeaBASSWriter.writeSeaBASS(name, dirpath, li, "LI", level)
    #     SeaBASSWriter.writeSeaBASS(name, dirpath, lt, "LT", level)
    #     SeaBASSWriter.writeSeaBASS(name, dirpath, rrs, "RRS", level)

