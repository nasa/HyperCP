''' Process L1AQC to L1B for SeaBird in Factory or Class regime '''
import re
import datetime as dt
import numpy as np
import pandas as pd

from Source.ProcessL1b_FRMCal import ProcessL1b_FRMCal
from Source.ProcessL1aDALEC import ProcessL1aDALEC
from Source.Utilities import Utilities

class ProcessL1b_FactoryCal:
    '''Process L1AQC to L1B for SeaBird in Factory or Class regime '''
    # Used to calibrate raw data (convert from L1a to L1b)
    # Reference: "SAT-DN-00134_Instrument File Format.pdf"
    @staticmethod
    def processDataset(ds, cd, inttime=None, immersed=False):
        #print("FitType:", cd.fitType)
        if cd.fitType == "OPTIC2":
            ProcessL1b_FactoryCal.processOPTIC2(ds, cd, immersed)
        # elif cd.fitType == "OPTIC1":
        #     ProcessL1b_FactoryCal.processOPTIC1(ds, cd, immersed)
        elif cd.fitType == "OPTIC3":
            ProcessL1b_FactoryCal.processOPTIC3(ds, cd, immersed, inttime)
        elif cd.fitType == "OPTIC4":
            ProcessL1b_FactoryCal.processOPTIC4(ds, cd, immersed)
        # elif cd.fitType == "THERM1":
        #     ProcessL1b_FactoryCal.processTHERM1(ds, cd)
        elif cd.fitType == "POW10":
            ProcessL1b_FactoryCal.processPOW10(ds, cd, immersed)
        elif cd.fitType == "POLYU":
            ProcessL1b_FactoryCal.processPOLYU(ds, cd)
        elif cd.fitType == "POLYF":
            ProcessL1b_FactoryCal.processPOLYF(ds, cd)
        # elif cd.fitType == "DDMM":
        #     ProcessL1b_FactoryCal.processDDMM(ds, cd)
        # elif cd.fitType == "HHMMSS":
        #     ProcessL1b_FactoryCal.processHHMMSS(ds, cd)
        # elif cd.fitType == "DDMMYY":
        #     ProcessL1b_FactoryCal.processDDMMYY(ds, cd)
        # elif cd.fitType == "TIME2":
        #     ProcessL1b_FactoryCal.processTIME2(ds, cd)
        elif cd.fitType == "COUNT":
            pass
        elif cd.fitType == "NONE":
            pass
        elif cd.fitType == "THERMAL_RESP":
            pass
        else:
            msg = f'ProcessL1b_FactoryCal.processDataset: Unknown Fit Type: {cd.fitType}'
            print(msg)
            Utilities.writeLogFile(msg)

    # # Process OPTIC1 - not implemented
    # @staticmethod
    # def processOPTIC1(ds, cd, immersed):
    #     return

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

    # # Process THERM1 - not implemented
    # #   This is for optical thermal sensors like pyrometers, I believe.
    # #   This is not for thermal responsivity of OPTICS3 sensors
    # @staticmethod
    # def processTHERM1(ds, cd):
    #     return

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
            for i, coeff in enumerate(cd.coefficients):
                a = float(coeff)
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

    # @staticmethod
    # def processDDMM(ds, cd):
    #     ''' Process DDMM - not implemented '''
    #     return
    #     #s = "{:.2f}".format(x)
    #     #x = s[:1] + " " + s[1:3] + "\' " + s[3:5] + "\""

    # @staticmethod
    # def processHHMMSS(ds, cd):
    #     ''' Process HHMMSS - not implemented '''
    #     return
    #     #s = "{:.2f}".format(x)
    #     #x = s[:2] + ":" + s[2:4] + ":" + s[4:6] + "." + s[6:8]

    # @staticmethod
    # def processDDMMYY(ds, cd):
    #     ''' Process DDMMYY - not implemented '''
    #     return
    #     #s = str(x)
    #     #x = s[:2] + "/" + s[2:4] + "/" + s[4:]

    # @staticmethod
    # def processTIME2(ds, cd):
    #     ''' Process TIME2 - not implemented '''
    #     return
    #     #x = datetime.fromtimestamp(x).strftime("%y-%m-%d %H:%M:%S")

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
    def get_cal_file_lines(calibrationMap):
        """
        function to recover effective calibration start and stop pixel from cal files.
        """
        cal_name_pattern = re.compile("HS.", re.IGNORECASE)  # patter for selecting shutterlight data
        coefs = {}
        indx = {}
        for k, var in calibrationMap.items():
            # filter for cal names to take out cals such as shutter dark and GPS/Tilt.
            if re.search(cal_name_pattern, k) and k.endswith('.cal'):  # any(['HSE' in k, 'HSL' in k]):
            # var.frameType == "shutterlight":  # ideal solution for this section, but frameType not populated in cal data
                coefs[k] = []
                for d in var.data:
                    if d.type == 'ES' or d.type == 'LI' or d.type == 'LT':
                        coefs[k].append(d.fitType)

                indx[k] = []
                for i, c in enumerate(coefs[k]):
                    if c == 'OPTIC3':
                        indx[k].append(i)

        # TODO: assess if this is stricly necessary, all indexes the same in examples used for testing
        start = max(ind[0] for ind in indx.values())  # -1 to cover the first pixel which has no coef but is valid
        end = min(ind[-1] for ind in indx.values())
        if start < 0: #  cannot be less than 0
            start = 0
        return start, end

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
        # get effective calibration and save to node attributes
        start, end = ProcessL1b_FactoryCal.get_cal_file_lines(calibrationMap)
        node.attributes['CAL_START'] = str(start)
        node.attributes['CAL_STOP'] = str(end)
        # node.attributes['CAL_LINES'] = lines
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
            if 'L1AQC' not in gp.id:
                msg = f'  Group: {gp.id}'
                print(msg)
                Utilities.writeLogFile(msg)
                if "CalFileName" in gp.attributes:
                    if gp.attributes["CalFileName"] != 'ANCILLARY':  # GPS constructed from Ancillary data will cause bug here
                        cf = calibrationMap[gp.attributes["CalFileName"]]
                        #print(gp.id, gp.attributes)
                        msg = f'    File: {cf.id}'
                        print(msg)
                        Utilities.writeLogFile(msg)

                        ProcessL1b_FactoryCal.processGroup(gp, cf)

                        if esUnits is None:
                            esUnits = cf.getUnits("ES")
                        if liUnits is None:
                            liUnits = cf.getUnits("LI")
                        if ltUnits is None:
                            ltUnits = cf.getUnits("LT")
                        if pyrUnits is None:
                            pyrUnits = cf.getUnits("T") #Pyrometer

        node.attributes["LI_UNITS"] = liUnits
        node.attributes["LT_UNITS"] = ltUnits
        node.attributes["ES_UNITS"] = esUnits
        node.attributes["L1AQC_UNITS"] = 'count'
        node.attributes["SATPYR_UNITS"] = pyrUnits

        # Calculate 6S model
        print('Running sixS')

        sensortype = "ES"
        # Irradiance direct and diffuse ratio
        res_sixS = ProcessL1b_FRMCal.get_direct_irradiance_ratio(node, sensortype)

        # Store sixS results in new group
        grp = node.getGroup(sensortype)
        solar_zenith = res_sixS['solar_zenith']
        # ProcessL1b_FRMCal.get_direct_irradiance_ratio uses Es bands to run 6S and then works around bands that
        #  don't have values from Tartu for full FRM. Here, use all the Es bands.
        direct_ratio = res_sixS['direct_ratio']
        diffuse_ratio = res_sixS['diffuse_ratio']
        # sixS model irradiance is in W/m^2/um, scale by 10 to match HCP units
        # model_irr = (res_sixS['direct_irr']+res_sixS['diffuse_irr']+res_sixS['env_irr'])[:,ind_raw_data]/10
        model_irr = (res_sixS['direct_irr']+res_sixS['diffuse_irr']+res_sixS['env_irr'])/10

        sixS_grp = node.addGroup("SIXS_MODEL")
        for dsname in ["DATETAG", "TIMETAG2", "DATETIME"]:
            # copy datetime dataset for interp process
            ds = sixS_grp.addDataset(dsname)
            ds.data = grp.getDataset(dsname).data

        ds = sixS_grp.addDataset("sixS_irradiance")

        irr_grp = node.getGroup('ES_LIGHT_L1AQC')
        str_wvl = np.asarray(pd.DataFrame(irr_grp.getDataset(sensortype).data).columns)
        ds_dt = np.dtype({'names': str_wvl,'formats': [np.float64]*len(str_wvl)})
        rec_arr = np.rec.fromarrays(np.array(model_irr).transpose(), dtype=ds_dt)
        ds.data = rec_arr

        ds = sixS_grp.addDataset("direct_ratio")
        ds_dt = np.dtype({'names': str_wvl,'formats': [np.float64]*len(str_wvl)})
        rec_arr = np.rec.fromarrays(np.array(direct_ratio).transpose(), dtype=ds_dt)
        ds.data = rec_arr

        ds = sixS_grp.addDataset("diffuse_ratio")
        ds_dt = np.dtype({'names': str_wvl,'formats': [np.float64]*len(str_wvl)})
        rec_arr = np.rec.fromarrays(np.array(diffuse_ratio).transpose(), dtype=ds_dt)
        ds.data = rec_arr

        ds = sixS_grp.addDataset("solar_zenith")
        ds.columns["solar_zenith"] = solar_zenith
        ds.columnsToDataset()

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
                except Exception:
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

    @staticmethod
    def extract_calibration_coeff_dalec(calibrationMap, sensor):
        '''
        extract spectral calibration coeff as array
        '''
        sensorCoeff={'ES':'a0','LT':'b0','LI':'c0'}
        sensorType={'ES':'Lambda_Ed','LT':'Lambda_Lu','LI':'Lambda_Lsky'}
        calMap=list(calibrationMap.values())
        calfile=calMap[0].name
        #print(calfile)
        #read cal data
        meta_instrument,coefficients,cal_data=ProcessL1aDALEC.read_cal(calfile)
        #print(cal_data)
        coeff = cal_data[sensorCoeff[sensor]]
        wvl = cal_data[sensorType[sensor]]
         
        return np.array(wvl), np.array(coeff)











