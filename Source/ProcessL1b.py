
import math
import datetime as dt
import numpy as np

import HDFRoot

from Utilities import Utilities
from ConfigFile import ConfigFile

class ProcessL1b:
   
    # Used to calibrate raw data (convert from L1a to L1b)
    # Reference: "SAT-DN-00134_Instrument File Format.pdf"
    @staticmethod
    def processDataset(ds, cd, inttime=None, immersed=False):
        #print("FitType:", cd.fitType)
        if cd.fitType == "OPTIC1":
            ProcessL1b.processOPTIC1(ds, cd, immersed)
        elif cd.fitType == "OPTIC2":
            ProcessL1b.processOPTIC2(ds, cd, immersed)
        elif cd.fitType == "OPTIC3":
            ProcessL1b.processOPTIC3(ds, cd, immersed, inttime)
        elif cd.fitType == "OPTIC4":
            ProcessL1b.processOPTIC4(ds, cd, immersed)
        elif cd.fitType == "THERM1":
            ProcessL1b.processTHERM1(ds, cd)
        elif cd.fitType == "POW10":
            ProcessL1b.processPOW10(ds, cd, immersed)
        elif cd.fitType == "POLYU":
            ProcessL1b.processPOLYU(ds, cd)
        elif cd.fitType == "POLYF":
            ProcessL1b.processPOLYF(ds, cd)
        elif cd.fitType == "DDMM":
            ProcessL1b.processDDMM(ds, cd)
        elif cd.fitType == "HHMMSS":
            ProcessL1b.processHHMMSS(ds, cd)
        elif cd.fitType == "DDMMYY":
            ProcessL1b.processDDMMYY(ds, cd)
        elif cd.fitType == "TIME2":
            ProcessL1b.processTIME2(ds, cd)
        elif cd.fitType == "COUNT":
            pass
        elif cd.fitType == "NONE":
            pass
        else:
            msg = f'ProcessL1b.processDataset: Unknown Fit Type: {cd.fitType}'
            print(msg)
            Utilities.writeLogFile(msg)

    # Process OPTIC1 - not implemented
    @staticmethod
    def processOPTIC1(ds, cd, immersed):
        return

    @staticmethod
    def processOPTIC2(ds, cd, immersed):
        a0 = float(cd.coefficients[0])
        a1 = float(cd.coefficients[1])
        im = float(cd.coefficients[2]) if immersed else 1.0
        k = cd.id
        for x in range(ds.data.shape[0]):
            ds.data[k][x] = im * a1 * (ds.data[k][x] - a0)

    @staticmethod
    def processOPTIC3(ds, cd, immersed, inttime):
        a0 = float(cd.coefficients[0])
        a1 = float(cd.coefficients[1])
        im = float(cd.coefficients[2]) if immersed else 1.0
        cint = float(cd.coefficients[3])
        #print(inttime.data.shape[0], self.data.shape[0])
        k = cd.id
        #print(cint, aint)
        #print(cd.id)
        for x in range(ds.data.shape[0]):
            aint = inttime.data[cd.type][x]
            #v = self.data[k][x]
            ds.data[k][x] = im * a1 * (ds.data[k][x] - a0) * (cint/aint)

    @staticmethod
    def processOPTIC4(ds, cd, immersed):
        a0 = float(cd.coefficients[0])
        a1 = float(cd.coefficients[1])
        im = float(cd.coefficients[2]) if immersed else 1.0
        cint = float(cd.coefficients[3])
        k = cd.id
        aint = 1
        for x in range(ds.data.shape[0]):
            ds.data[k][x] = im * a1 * (ds.data[k][x] - a0) * (cint/aint)

    # Process THERM1 - not implemented
    @staticmethod
    def processTHERM1(ds, cd):
        return

    @staticmethod
    def processPOW10(ds, cd, immersed):
        a0 = float(cd.coefficients[0])
        a1 = float(cd.coefficients[1])
        im = float(cd.coefficients[2]) if immersed else 1.0
        k = cd.id
        for x in range(ds.data.shape[0]):
            ds.data[k][x] = im * pow(10, ((ds.data[k][x]-a0)/a1))

    @staticmethod
    def processPOLYU(ds, cd):
        k = cd.id
        for x in range(ds.data.shape[0]):
            num = 0
            for i in range(0, len(cd.coefficients)):
                a = float(cd.coefficients[i])
                num += a * pow(ds.data[k][x],i)
            ds.data[k][x] = num

    @staticmethod
    def processPOLYF(ds, cd):
        a0 = float(cd.coefficients[0])
        k = cd.id
        for x in range(ds.data.shape[0]):
            num = a0
            for a in cd.coefficients[1:]:
                num *= (ds.data[k][x] - float(a))
            ds.data[k][x] = num

    # Process DDMM - not implemented
    @staticmethod
    def processDDMM(ds, cd):
        return
        #s = "{:.2f}".format(x)
        #x = s[:1] + " " + s[1:3] + "\' " + s[3:5] + "\""

    # Process HHMMSS - not implemented
    @staticmethod
    def processHHMMSS(ds, cd):
        return
        #s = "{:.2f}".format(x)
        #x = s[:2] + ":" + s[2:4] + ":" + s[4:6] + "." + s[6:8]

    # Process DDMMYY - not implemented
    @staticmethod
    def processDDMMYY(ds, cd):
        return
        #s = str(x)
        #x = s[:2] + "/" + s[2:4] + "/" + s[4:]

    # Process TIME2 - not implemented
    @staticmethod
    def processTIME2(ds, cd):
        return
        #x = datetime.fromtimestamp(x).strftime("%y-%m-%d %H:%M:%S")

    # Used to calibrate raw data (from L1a to L1b)
    @staticmethod
    def processGroup(gp, cf): # group, calibration file

        # Rename the groups to more generic ids rather than the names of the cal files
        if gp.id.startswith("GPRMC") or gp.id.startswith("GPGAA"):
            gp.id = "GPS"
        if gp.id.startswith("UMTWR"):
            gp.id = "SOLARTRACKER_UM"
        if gp.id.startswith("SATNAV"):
            gp.id = "SOLARTRACKER"
        if gp.id.startswith("SATMSG"):
            gp.id = "SOLARTRACKER_STATUS"
        if gp.id.startswith("SATPYR"):
            gp.id = "PYROMETER"
        if gp.id.startswith("HED"):
            gp.id = "ES_DARK"
        if gp.id.startswith("HSE"):
            gp.id = "ES_LIGHT"
        if gp.id.startswith("HLD"):
            if cf.sensorType == "LI":
                gp.id = "LI_DARK"
            if cf.sensorType == "LT":
                gp.id = "LT_DARK"
        if gp.id.startswith("HSL"):
            if cf.sensorType == "LI":
                gp.id = "LI_LIGHT"
            if cf.sensorType == "LT":
                gp.id = "LT_LIGHT"

        inttime = None
        for cd in cf.data: # cd is the name of the cal file data
            # Process slightly differently for INTTIME
            if cd.type == "INTTIME":
                #print("Process INTTIME")
                ds = gp.getDataset("INTTIME")
                ProcessL1b.processDataset(ds, cd)
                inttime = ds

        for cd in cf.data:
            # process each dataset in the cal file list of data, except INTTIME
            if gp.getDataset(cd.type) and cd.type != "INTTIME":
                #print("Dataset:", cd.type)
                ds = gp.getDataset(cd.type)
                ProcessL1b.processDataset(ds, cd, inttime)
    
    @staticmethod
    def processL1b(node, calibrationMap):                 
        '''
        Filters data for pitch, roll, yaw, and rotator.
        Calibrates raw data from L1a using information from calibration file
        '''

        esUnits = None
        liUnits = None
        ltUnits = None
        pyrUnits = None

        node.attributes["PROCESSING_LEVEL"] = "1b"
        
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr
        msg = f"ProcessL1b.processL1b: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        msg = "Applying factory calibrations."
        print(msg)
        Utilities.writeLogFile(msg)

        for gp in node.groups:
            # Apply calibration factors to each dataset in HDF 
            msg = f'  Group: {gp.id}'
            print(msg)
            Utilities.writeLogFile(msg)
            if "CalFileName" in gp.attributes:
                #cf = calibrationMap[gp.attributes["FrameTag"]]
                cf = calibrationMap[gp.attributes["CalFileName"]]
                #print(gp.id, gp.attributes)
                msg = f'    File: {cf.id}'
                print(msg)
                Utilities.writeLogFile(msg)

                ProcessL1b.processGroup(gp, cf)
    
                if esUnits == None:
                    esUnits = cf.getUnits("ES")
                if liUnits == None:
                    liUnits = cf.getUnits("LI")
                if ltUnits == None:
                    ltUnits = cf.getUnits("LT")
                if pyrUnits == None:
                    pyrUnits = cf.getUnits("T") #Pyrometer
        
        node.attributes["LI_UNITS"] = liUnits
        node.attributes["LT_UNITS"] = ltUnits
        node.attributes["ES_UNITS"] = esUnits
        node.attributes["SATPYR_UNITS"] = pyrUnits

        return node
