''' Interpret raw SeaBird-style data files
    Reads raw files line by line and parses the data 
'''
import binascii
import os
import sys

from Source.CalibrationData import CalibrationData
from Source.Utilities import Utilities


class CalibrationFile:
    '''CalibrationFile class stores information about an instrument
        obtained from reading a calibration file'''

    def __init__(self):
        self.id = ""
        self.name = ""
        self.data = []

        self.instrumentType = ""
        self.media = ""
        self.measMode = ""
        self.frameType = ""
        self.sensorType = ""


    def printd(self):
        if len(self.id) != 0:
            pmsg = f'id: {self.id}'
            print(pmsg)
            Utilities.writeLogFile(pmsg)
#        for cd in self.data:
#            cd.printd()

    # Reads a calibration file and generates calibration data
    def read(self, f):
        #print("CalibrationFile.read()")
        (_, filename) = os.path.split(f.name)
        self.name = filename
        while 1:
            line = f.readline()
            line = line.decode("utf-8")
            #print(line)
            if not line:
                break
            line = line.strip()

            # Ignore comments and empty lines
            if line.startswith("#") or len(line) == 0:
                continue

            cd = CalibrationData()
            cd.read(line)

            cdtype = cd.type.upper()

            # Determines the frame synchronization string by appending
            # ids from INSTRUMENT and SN lines
            if cdtype in ('INSTRUMENT', 'VLF_INSTRUMENT', 'SN', 'VLF_SN'):
                self.id += cd.id

            # Read in coefficients
            for i in range(0, cd.calLines):
                line = f.readline()
                cd.readCoefficients(line)

            #cd.printd()
            self.data.append(cd)

    # Returns units for the calibration data with type t
    def getUnits(self, t):
        for cd in self.data:
            if cd.type == t:
                return cd.units
        return None

    # Returns the sensor type
    def getSensorType(self):
        for cd in self.data:
            if cd.type == "ES" or \
               cd.type == "LI" or \
               cd.type == "LT" or \
               cd.type == "T":
                return cd.type
        return "None"

    # Verify raw data message can be read successfully
    def verifyRaw(self, msg):
        try:
            nRead = 0
            for i, cd in enumerate(self.data):
                v = 0 # for debugging; ignore
                # cd = self.data[i]

                # Read variable length message frames (field length == -1)
                if cd.fieldLength == -1:
                    delimiter = self.data[i+1].units
                    delimiter = delimiter.encode("utf-8").decode("unicode_escape").encode("utf-8")
                    #print("delimiter:", delimiter)

                    end = msg[nRead:].find(delimiter)
                    # print("read:", nRead, end)
                    if end == 0:
                        v = 0.0
                    else:
                        b = msg[nRead:nRead+end]
                        v = cd.convertRaw(b)

                    nRead += end

                # Read fixed length message frames
                else:
                    if cd.fitType.upper() != "DELIMITER":
                        if cd.fieldLength != 0:
                            b = msg[nRead:nRead+cd.fieldLength]
                            # print(nRead, cd.fieldLength, b)
                            v = cd.convertRaw(b)
                    nRead  += cd.fieldLength

                # Passed EndOfFile
                #if nRead > len(msg):
                #    return False

            return True

        except KeyError:
            # pass
            pmsg = "Failed to read message successfully"
            print(pmsg)
            Utilities.writeLogFile(pmsg)

        return False


    # Reads a message frame from the raw file and generates hdf groups/datasets
    # Returns nRead (number of bytes read) or -1 on error
    def convertRaw(self, msg, gp):
        nRead = 0
        instrumentId = ""

        #for i in range(0, len(self.data)):
        #    self.data[i].printd()
        #print("file:", msg)

        if self.verifyRaw(msg) is False:
            print("Message not read successfully:\n" + str(msg))
            self.verifyRaw(msg)
            return -1

        for i, cd in enumerate(self.data):
            v = 0
            # cd = self.data[i]

            # Get value from message frame

            # Read variable length message frames (field length == -1)
            if cd.fieldLength == -1:
                delimiter = self.data[i+1].units
                delimiter = delimiter.encode("utf-8").decode("unicode_escape").encode("utf-8")
                #print("delimiter:", delimiter)

                end = msg[nRead:].find(delimiter)
                #print("read:", nRead, end)
                b = msg[nRead:nRead+end]
                v = cd.convertRaw(b)
                nRead += end

            # Read fixed length message frames
            else:
                if cd.fitType.upper() != "DELIMITER":
                    if cd.fieldLength != 0:
                        b = msg[nRead:nRead+cd.fieldLength]
                        # print(nRead, cd.fieldLength, b)
                        v = cd.convertRaw(b)
                nRead  += cd.fieldLength


            # Stores the instrument id to check for DATETAG/TIMETAG2
            if cd.type.upper() == "INSTRUMENT" or cd.type.upper() == "VLF_INSTRUMENT":
                instrumentId = cd.id

            # Stores value in dataset or attribute depending on type

            # Stores raw data into hdf datasets according to type
            if cd.fitType.upper() != "NONE" and cd.fitType.upper() != "DELIMITER":
                cdtype = cd.type.upper()
                if cdtype not in ('INSTRUMENT', 'VLF_INSTRUMENT', 'SN', 'VLF_SN'):
                    ds = gp.getDataset(cd.type)
                    if ds is None:
                        ds = gp.addDataset(cd.type)
                    #print(cd.id)
                    #ds.temp.append(v)
                    #ds.addColumn(cd.id)
                    ds.appendColumn(cd.id, v)
                else:
                    if sys.version_info[0] < 3: # Python3
                        gp.attributes[cdtype.encode('utf-8')] = cd.id
                    else: # Python2
                        gp.attributes[cdtype] = cd.id

            # None types are stored as attributes
            if cd.fitType.upper() == "NONE":
                cdtype = cd.type.upper()
                if cdtype == "SN" or cdtype == "DATARATE" or cdtype == "RATE":
                    if sys.version_info[0] < 3:
                        gp.attributes[cdtype.encode('utf-8')] = cd.id
                    else:
                        gp.attributes[cdtype] = cd.id


        # Some instruments produce additional bytes for
        # DATETAG (3 bytes), and TIMETAG2 (4 bytes)        
        #       apparently SATMSG does not .... comes out jibberish
        #       $GPGGA also does not work and timetags will be added later from NMEA strings 
        if instrumentId.startswith("SATHED") or \
            instrumentId.startswith("SATHLD") or \
            instrumentId.startswith("SATHSE") or \
            instrumentId.startswith("SATHSL") or \
            instrumentId.startswith("SATPYR") or \
            instrumentId.startswith("SATNAV") or \
            instrumentId.startswith("$GPRMC") or \
            instrumentId.startswith("SATTHS") or \
            instrumentId.startswith("UMTWR"):
            #    instrumentId.startswith("SATMSG") or \
            #print("not gps")
            # Read DATETAG
            b = msg[nRead:nRead+3]
            if sys.version_info[0] < 3:
                v = int(binascii.hexlify(b), 16)
            else:
                v = int.from_bytes(b, byteorder='big', signed=False)
            nRead += 3
            #print("Date:",v)
            ds1 = gp.getDataset("DATETAG")
            if ds1 is None:
                ds1 = gp.addDataset("DATETAG")
            ds1.appendColumn("NONE", v)
            # Read TIMETAG2
            b = msg[nRead:nRead+4]
            if sys.version_info[0] < 3:
                v = int(binascii.hexlify(b), 16)
            else:
                v = int.from_bytes(b, byteorder='big', signed=False)
            nRead += 4
            #print("Time:",v)
            ds1 = gp.getDataset("TIMETAG2")
            if ds1 is None:
                ds1 = gp.addDataset("TIMETAG2")
            ds1.appendColumn("NONE", v)

        return nRead
