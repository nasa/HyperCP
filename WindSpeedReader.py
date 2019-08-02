
import csv

from datetime import datetime

from HDFDataset import HDFDataset
from SB_support import readSB


class WindSpeedReader:

    # @staticmethod
    # def readCSV(fp):
    #     lst = []
    #     with open(fp, 'r') as f:
    #         reader = csv.reader(f)
    #         #for row in reader:
    #         #    print(row)
    #         lst = list(reader)
    #     return lst



    # Reads a wind speed SeaBASS file and returns a HDFDataset
    @staticmethod
    def readWindSpeed(fp):
        print("WindSpeedReader.readWindSpeed: " + fp)

        # metData = readSB(fp,mask_missing=False, no_warn=True)
        metData = readSB(fp, no_warn=True)
        wspd = metData.data['wind']
        windDatetime = metData.fd_datetime()

        # dateTag = []
        # tt2 = []
        # # Convert timestamp to TimeTag2
        # for dt in windDatetime:
        #     # dt = datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%S.%fZ")
        #     dateTag.append(float(dt.strftime("%Y%m%d")))

        #     # float("%d%02d%02d%03d" % (h, m, s, ms)) Tagtag2 format
        #     # HMMSSmmm.0, where mmm is miliseconds
        #     # %f below returns microseconds
        #     # so minute 1 is MM SS mmm is 01 00 000
        #     tt2.append(float(dt.strftime("%-H%M%S%f")[:-3]))
        # #print(tt2)
        

        # Generate HDFDataset
        windSpeedData = HDFDataset()
        windSpeedData.id = "WindSpeedData"
        # windSpeedData.appendColumn("DATETAG", dateTag)
        # windSpeedData.appendColumn("TIMETAG2", tt2)
        windSpeedData.appendColumn("DATETIME", windDatetime)
        windSpeedData.appendColumn("WINDSPEED", wspd)
        #windSpeedData.appendColumn("LATPOS", lat)
        #windSpeedData.appendColumn("LONPOS", lon)
        
        windSpeedData.columnsToDataset()
        #windSpeedData.printd()

        return windSpeedData

