
import datetime as dt
import numpy as np
from Source.Utilities import Utilities

class ProcessL1b_FactoryCal:

    # Used to calibrate raw data (convert from L1a to L1b)
    # Reference: "SAT-DN-00134_Instrument File Format.pdf"
    @staticmethod
    def processDataset(ds, cd, inttime=None, immersed=False):
        #print("FitType:", cd.fitType)
        if cd.fitType == "OPTIC1":
            ProcessL1b_FactoryCal.processOPTIC1(ds, cd, immersed)
        elif cd.fitType == "OPTIC2":
            ProcessL1b_FactoryCal.processOPTIC2(ds, cd, immersed)
        elif cd.fitType == "OPTIC3":
            ProcessL1b_FactoryCal.processOPTIC3(ds, cd, immersed, inttime)
        elif cd.fitType == "OPTIC4":
            ProcessL1b_FactoryCal.processOPTIC4(ds, cd, immersed)
        elif cd.fitType == "THERM1":
            ProcessL1b_FactoryCal.processTHERM1(ds, cd)
        elif cd.fitType == "POW10":
            ProcessL1b_FactoryCal.processPOW10(ds, cd, immersed)
        elif cd.fitType == "POLYU":
            ProcessL1b_FactoryCal.processPOLYU(ds, cd)
        elif cd.fitType == "POLYF":
            ProcessL1b_FactoryCal.processPOLYF(ds, cd)
        elif cd.fitType == "DDMM":
            ProcessL1b_FactoryCal.processDDMM(ds, cd)
        elif cd.fitType == "HHMMSS":
            ProcessL1b_FactoryCal.processHHMMSS(ds, cd)
        elif cd.fitType == "DDMMYY":
            ProcessL1b_FactoryCal.processDDMMYY(ds, cd)
        elif cd.fitType == "TIME2":
            ProcessL1b_FactoryCal.processTIME2(ds, cd)
        elif cd.fitType == "COUNT":
            pass
        elif cd.fitType == "NONE":
            pass
        else:
            msg = f'ProcessL1b_FactoryCal.processDataset: Unknown Fit Type: {cd.fitType}'
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
        # a0 = float(cd.coefficients[0])
        a1 = float(cd.coefficients[1])
        im = float(cd.coefficients[2]) if immersed else 1.0
        cint = float(cd.coefficients[3])
        #print(inttime.data.shape[0], self.data.shape[0])
        k = cd.id
        #print(cint, aint)
        #print(cd.id)
        for x in range(ds.data.shape[0]):
            aint = inttime.data[cd.type][x]
            # ds.data[k][x] = im * a1 * (ds.data[k][x] - a0) * (cint/aint)
            ##############################################################
            #   When applying calibration to the dark current corrected
            #   radiometry, a0 cancels (see ProSoftUserManual7.7 11.1.1.5 Eqns 5-6)
            #   presuming light and dark factory cals are equivalent (which they are).
            ##############################################################
            ds.data[k][x] = im * a1 * (ds.data[k][x]) * (cint/aint)

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
    #   This is for optical thermal sensors like pyrometers, I believe.
    #   This is not for thermal responsivity of OPTICS3 sensors
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

    @staticmethod
    def processDDMM(ds, cd):
        ''' Process DDMM - not implemented '''
        return
        #s = "{:.2f}".format(x)
        #x = s[:1] + " " + s[1:3] + "\' " + s[3:5] + "\""

    @staticmethod
    def processHHMMSS(ds, cd):
        ''' Process HHMMSS - not implemented '''
        return
        #s = "{:.2f}".format(x)
        #x = s[:2] + ":" + s[2:4] + ":" + s[4:6] + "." + s[6:8]

    @staticmethod
    def processDDMMYY(ds, cd):
        ''' Process DDMMYY - not implemented '''
        return
        #s = str(x)
        #x = s[:2] + "/" + s[2:4] + "/" + s[4:]

    @staticmethod
    def processTIME2(ds, cd):
        ''' Process TIME2 - not implemented '''
        return
        #x = datetime.fromtimestamp(x).strftime("%y-%m-%d %H:%M:%S")

    # Used to calibrate raw data (from L1a to L1b)
    @staticmethod
    def processGroup(gp, cf): # group, calibration file

        inttime = None
        for cd in cf.data: # cd is the name of the cal file data
            # Process slightly differently for INTTIME
            if cd.type == "INTTIME":
                #print("Process INTTIME")
                ds = gp.getDataset("INTTIME")
                ProcessL1b_FactoryCal.processDataset(ds, cd)
                inttime = ds

        for cd in cf.data:
            # process each dataset in the cal file list of data, except INTTIME
            if gp.getDataset(cd.type) and cd.type != "INTTIME":
                #print("Dataset:", cd.type)
                ds = gp.getDataset(cd.type)
                ProcessL1b_FactoryCal.processDataset(ds, cd, inttime)

    @staticmethod
    def processL1b_SeaBird(node, calibrationMap):
        '''
        Calibrates L1a using information from calibration file
        '''

        esUnits = None
        liUnits = None
        ltUnits = None
        pyrUnits = None

        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr
        msg = f"ProcessL1b_FactoryCal.processL1b: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        msg = "Applying factory calibrations."
        print(msg)
        Utilities.writeLogFile(msg)

        for gp in node.groups:
            # Apply calibration factors to each dataset in HDF except the L1AQC datasets carried forward
            # for L2 uncertainty propagation
            if not 'L1AQC' in gp.id:
                msg = f'  Group: {gp.id}'
                print(msg)
                Utilities.writeLogFile(msg)
                if "CalFileName" in gp.attributes:
                    cf = calibrationMap[gp.attributes["CalFileName"]]
                    #print(gp.id, gp.attributes)
                    msg = f'    File: {cf.id}'
                    print(msg)
                    Utilities.writeLogFile(msg)

                    ProcessL1b_FactoryCal.processGroup(gp, cf)

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
        node.attributes["L1AQC_UNITS"] = 'count'
        node.attributes["SATPYR_UNITS"] = pyrUnits

        return node

    @staticmethod
    def extract_calibration_coeff(node, calibrationMap, sensor):
        '''
        extract spectral calibration coeff (OPTIC3) as array
        '''
        coeff = []
        wvl = []
        for gp in node.groups:
            # retrieve the LIGHT L1AQC dataset for a given sensor
            if sensor+"_LIGHT" in gp.id :
                try:
                    cf = calibrationMap[gp.attributes["CalFileName"]]
                except:
                    # This can happen if you try to process L2 with a different calMap from L1B data
                    msg = f'ProcessL1b_FactoryCal.extract_calibration_coeff: Mismatched Cal File: {gp.attributes["CalFileName"]}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return None, None

                for cd in cf.data:
                    # Process only OPTIC3
                    if cd.fitType == "OPTIC3":
                        coeff.append(float(cd.coefficients[1]))
                        wvl.append(float(cd.id))
        return np.array(wvl), np.array(coeff)











