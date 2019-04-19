
import HDFRoot
#import HDFGroup
#import HDFDataset

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
            print("Unknown Fit Type:", cd.fitType)

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

    # Used to calibrate raw data (from L0 to L1b)
    @staticmethod
    def processGroup(gp, cf): # group, calibration file
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

    # Calibrates raw data from L1a using information from calibration file
    @staticmethod
    def processL1b(node, calibrationMap): # ToDo: Switch to contextMap ??
        root = HDFRoot.HDFRoot()
        root.copy(node)

        root.attributes["PROCESSING_LEVEL"] = "1a"

        esUnits = None
        liUnits = None
        ltUnits = None

        for gp in root.groups:
            # Apply calibration factors to each dataset in HDF 
            print("Group: ", gp.id)
            if "CalFileName" in gp.attributes:
                #cf = calibrationMap[gp.attributes["FrameTag"]]
                cf = calibrationMap[gp.attributes["CalFileName"]]
                #print(gp.id, gp.attributes)
                print("File:", cf.id)
                ProcessL1b.processGroup(gp, cf)
    
                if esUnits == None:
                    esUnits = cf.getUnits("ES")
                if liUnits == None:
                    liUnits = cf.getUnits("LI")
                if ltUnits == None:
                    ltUnits = cf.getUnits("LT")

        #print(esUnits, luUnits)
        root.attributes["LI_UNITS"] = liUnits
        root.attributes["LT_UNITS"] = ltUnits
        root.attributes["ES_UNITS"] = esUnits

        return root
