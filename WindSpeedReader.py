
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

        metData = readSB(fp, no_warn=True)
        wspd = metData.data['wind']
        windDatetime = metData.fd_datetime()

        tt2 = []
        # Convert timestamp to TimeTag2
        for dt in windDatetime:
            # dt = datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%S.%fZ")
            tt2.append(float(dt.strftime("%H%M%S%f")[:-3]))
        #print(tt2)
        

        # Generate HDFDataset
        windSpeedData = HDFDataset()
        windSpeedData.id = "WindSpeedData"
        windSpeedData.appendColumn("WINDSPEED", wspd)
        #windSpeedData.appendColumn("LATPOS", lat)
        #windSpeedData.appendColumn("LONPOS", lon)
        windSpeedData.appendColumn("TIMETAG2", tt2)
        windSpeedData.columnsToDataset()
        #windSpeedData.printd()

        return windSpeedData

