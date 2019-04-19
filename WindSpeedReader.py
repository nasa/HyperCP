
import csv

from datetime import datetime

from HDFDataset import HDFDataset


class WindSpeedReader:

    @staticmethod
    def readCSV(fp):
        lst = []
        with open(fp, 'r') as f:
            reader = csv.reader(f)
            #for row in reader:
            #    print(row)
            lst = list(reader)
        return lst



    # Reads a wind speed CSV file and returns a HDFDataset
    @staticmethod
    def readWindSpeed(fp):
        print("readWindSpeed: " + fp)
        csv = WindSpeedReader.readCSV(fp)

        timestamp = []

        wspd = []
        #lat = []
        #lon = []
        tt2 = []

        # Read CSV file
        for ls in csv:
            # ignore header/comment lines
            if len(ls) != 7 or ls[0].startswith('#'):
                continue
            #print(ls)

            # ignore lines with QC Flag errors
            wsQC = int(ls[2])
            if wsQC != 1:
                continue

            timestamp.append(ls[0])
            wspd.append(ls[1])
            #lat.append(ls[3])
            #lon.append(ls[5])

        # Convert timestamp to TimeTag2
        for timestr in timestamp:
            dt = datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%S.%fZ")
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

