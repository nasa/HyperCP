
import numpy as np

from Source.ConfigFile import ConfigFile
from Source.Utilities import Utilities
from Source.L2chlor_a import L2chlor_a
from Source.L2pic import L2pic
from Source.L2poc import L2poc
from Source.L2gocad import L2gocad

from Source.L2kd490 import L2kd490
from Source.L2ipar import L2ipar
# from L2giop import L2giop
from Source.L2qaa import L2qaa
from Source.L2avw import L2avw
from Source.L2wei_QA import QAscores_5Bands
from Source.L2qwip import L2qwip


class ProcessL2OCproducts():
    ''' Most product algorithms can be found at https://oceancolor.gsfc.nasa.gov/atbd/
    TODO: Uncertainty propagation'''

    @staticmethod
    def procProds(root):

        Reflectance = root.getGroup("REFLECTANCE")

        dateTime = Reflectance.datasets['Rrs_HYPER'].columns['Datetime']
        dateTag = Reflectance.datasets['Rrs_HYPER'].columns['Datetag']
        timeTag2 = Reflectance.datasets['Rrs_HYPER'].columns['Timetag2']

        # Multispectral bands required for some algorithms
        # Confirm necessary satellite bands are processed
        if ConfigFile.products["bL2Prodoc3m"] or ConfigFile.products["bL2Prodkd490"] or \
            ConfigFile.products["bL2Prodpic"] or ConfigFile.products["bL2Prodpoc"] or \
            ConfigFile.products["bL2Prodgocad"] or ConfigFile.products["bL2Prodgiop"] or \
            ConfigFile.products["bL2Prodqaa"] or ConfigFile.products["bL2ProdweiQA"]:
            Rrs412 = Reflectance.datasets["Rrs_MODISA"].columns['412']
            Rrs443 = Reflectance.datasets["Rrs_MODISA"].columns['443']
            Rrs488 = Reflectance.datasets["Rrs_MODISA"].columns['488']
            Rrs531 = Reflectance.datasets["Rrs_MODISA"].columns['531']
            Rrs547 = Reflectance.datasets["Rrs_MODISA"].columns['551'] # 551 in name only
            Rrs555 = Reflectance.datasets["Rrs_MODISA"].columns['555']
            Rrs667 = Reflectance.datasets["Rrs_MODISA"].columns['667'].copy()

        # waveSat = [412, 443, 488, 532, 547, 555, 667]

        RrsHYPER = Reflectance.datasets["Rrs_HYPER"]

        Ancillary = root.getGroup("ANCILLARY")
        DerProd = None

        if not root.getGroup("DERIVED_PRODUCTS"):
            DerProd = root.addGroup("DERIVED_PRODUCTS")

        # chlor_a
        if ConfigFile.products["bL2Prodoc3m"]:
            msg = "Processing chlor_a"
            print(msg)
            Utilities.writeLogFile(msg)

            DerProd.attributes['chlor_a_UNITS'] = 'mg m^-3'
            chlDS = DerProd.addDataset('chlor_a')
            chlDS.columns['Datetime'] = dateTime
            chlDS.columns['Datetag'] = dateTag
            chlDS.columns['Timetag2'] = timeTag2

            chlor_a = []
            for i in range(0, len(dateTime)):
                chlor_a.append(L2chlor_a(Rrs443[i], Rrs488[i], Rrs547[i], Rrs555[i], Rrs667[i]))

            chlDS.columns['chlor_a'] = chlor_a
            chlDS.columnsToDataset()


        # pic
        # Not yet implemented
        if ConfigFile.products["bL2Prodpic"]:
            msg = "Processing pic"
            print(msg)
            Utilities.writeLogFile(msg)

            picDS = DerProd.addDataset('pic')
            DerProd.attributes['pic_UNITS'] = 'mol m^-3'
            picDS.columns['Datetime'] = dateTime
            picDS.columns['Datetag'] = dateTag
            picDS.columns['Timetag2'] = timeTag2

            pic = L2pic(root)
            picDS.columns['pic'] = pic
            picDS.columnsToDataset()

        # poc
        if ConfigFile.products["bL2Prodpoc"]:
            msg = "Processing poc"
            print(msg)
            Utilities.writeLogFile(msg)

            pocDS = DerProd.addDataset('poc')
            DerProd.attributes['poc_UNITS'] = 'mg m^-3'
            pocDS.columns['Datetime'] = dateTime
            pocDS.columns['Datetag'] = dateTag
            pocDS.columns['Timetag2'] = timeTag2

            # Vectorwise
            poc = L2poc(Rrs443, Rrs555)

            pocDS.columns['poc'] = poc.tolist()
            pocDS.columnsToDataset()

        # kd490
        if ConfigFile.products["bL2Prodkd490"]:
            msg = "Processing kd490"
            print(msg)
            Utilities.writeLogFile(msg)

            kdDS = DerProd.addDataset('kd490')
            DerProd.attributes['kd490_UNITS'] = 'm^-1'
            kdDS.columns['Datetime'] = dateTime
            kdDS.columns['Datetag'] = dateTag
            kdDS.columns['Timetag2'] = timeTag2

            # Vectorwise
            kd490 = L2kd490(Rrs488, Rrs547)

            kdDS.columns['kd490'] = kd490.tolist()
            kdDS.columnsToDataset()

        # ipar
        if ConfigFile.products["bL2Prodipar"]:
            msg = "Processing ipar"
            print(msg)
            Utilities.writeLogFile(msg)

            Es_ds = root.getGroup("IRRADIANCE").datasets["ES_HYPER"]
            keys = list(Es_ds.columns.keys())
            values = list(Es_ds.columns.values())
            waveStr = keys[3:]
            Es = np.array(values[3:])
            wavelength = np.array([float(i) for i in waveStr])
            fullSpec = np.array(list(range(400, 701)))

            iparDS = DerProd.addDataset('ipar')
            DerProd.attributes['ipar_UNITS'] = 'Einstein m^-2 d^-1'
            iparDS.columns['Datetime'] = dateTime
            iparDS.columns['Datetag'] = dateTag
            iparDS.columns['Timetag2'] = timeTag2

            ipar = []
            for n in range(0, len(dateTime)):
                ipar.append(L2ipar(wavelength, Es[:,n], fullSpec))

            iparDS.columns['ipar'] = ipar
            iparDS.columnsToDataset()

        # Spectral QA
        # ''' Wei, Lee, and Shang (2016).
        #      A system to measure the data quality of spectral remote sensing
        #      reflectance of aquatic environments. Journal of Geophysical Research,
        #      121, doi:10.1002/2016JC012126'''

        if ConfigFile.products["bL2ProdweiQA"]:
            msg = "Processing Wei QA"
            print(msg)
            Utilities.writeLogFile(msg)

            DerProd.attributes['wei_QA_UNITS'] = 'score'
            weiQADS = DerProd.addDataset('wei_QA')
            weiQADS.columns['Datetime'] = dateTime
            weiQADS.columns['Datetag'] = dateTag
            weiQADS.columns['Timetag2'] = timeTag2

            # Reorganize datasets into multidimensional numpy arrays
            Rrs_mArray = np.transpose(np.array([ Rrs412, Rrs443, Rrs488, Rrs547, Rrs667 ]))
            Rrs_wave =    np.array([412, 443, 488, 547, 667])

            # Interpolation to QA bands, which are representative of several missions (see L2wei_QA.py)
            test_lambda = np.array([412, 443, 488, 551, 670])
            test_Rrs = np.empty((Rrs_mArray.shape[0],len(test_lambda))) * np.nan
            for i, Rrsi in enumerate(Rrs_mArray):
                test_Rrs[i,:] = Utilities.interp(Rrs_wave.tolist(), Rrsi.tolist(), test_lambda.tolist(), \
                    kind='linear', fill_value=0.0)


            # maxCos, cos, clusterID, totScore = QAscores_5Bands(test_Rrs, test_lambda)
            _, _, _, totScore = QAscores_5Bands(test_Rrs, test_lambda)

            weiQADS.columns['QA_score'] = totScore.tolist()
            weiQADS.columnsToDataset()

        # avw
        # ''' Average Visible Wavelength
        #     Vandermuelen et al. 2020'''

        if ConfigFile.products["bL2Prodavw"]:
            msg = "Processing avw"
            print(msg)
            Utilities.writeLogFile(msg)

            keys = list(RrsHYPER.columns.keys())
            values = list(RrsHYPER.columns.values())
            waveStr = keys[3:]
            wavelength = np.array([float(i) for i in waveStr])
            Rrs = np.array(values[3:])

            avwDS = DerProd.addDataset('avw')
            DerProd.attributes['avw_UNITS'] = 'nm'
            DerProd.attributes['lambda_max_UNITS'] = 'nm'
            DerProd.attributes['brightness_UNITS'] = 'nm/sr'
            avwDS.columns['Datetime'] = dateTime
            avwDS.columns['Datetag'] = dateTag
            avwDS.columns['Timetag2'] = timeTag2

            # Vectorwise
            avw, lambda_max, brightness = L2avw(wavelength, Rrs)

            avwDS.columns['avw'] = avw
            avwDS.columns['lambda_max'] = lambda_max
            avwDS.columns['brightness'] = brightness
            avwDS.columnsToDataset()

        # qwip
        # ''' Quantitative Water Index Polynomial
        #     Dierssen et al. 2022'''

        if ConfigFile.products["bL2Prodqwip"]:
            msg = "Processing QWIP"
            print(msg)
            Utilities.writeLogFile(msg)

            qwipDS = DerProd.addDataset('qwip')
            DerProd.attributes['qwip_UNITS'] = 'sr^-1'

            qwipDS.columns['Datetime'] = dateTime
            qwipDS.columns['Datetag'] = dateTag
            qwipDS.columns['Timetag2'] = timeTag2

            qwip = L2qwip(wavelength, Rrs, avw)

            qwipDS.columns['qwip'] = qwip
            qwipDS.columnsToDataset()

        # CDOM (GOCAD)
        # ''' Global Ocean Carbon Algorithm Database
        #     Aurin et al. 2018 MLRs for global dataset (GOCAD) '''

        if ConfigFile.products["bL2Prodgocad"]:
            msg = "Processing CDOM, Sg, DOC"
            print(msg)
            Utilities.writeLogFile(msg)

            SAL = Ancillary.datasets["SALINITY"].columns["SALINITY"]

            waveStr = ['275', '355', '380', '412', '443', '488']
            waveStrS = ['275', '300', '350', '380', '412']

            # Vectorwise
            ag, Sg, doc = \
                L2gocad(Rrs443, Rrs488, Rrs531, Rrs547, SAL, fill=-9999)

            if ConfigFile.products["bL2Prodag"]:
                DerProd.attributes['ag_UNITS'] = '1/m'
                agDS = DerProd.addDataset('gocad_ag')
                agDS.columns['Datetime'] = dateTime
                agDS.columns['Datetag'] = dateTag
                agDS.columns['Timetag2'] = timeTag2
                ag = dict(zip(waveStr,np.transpose(ag).tolist()))
                for key, value in ag.items(): agDS.columns[key] = value
                agDS.columnsToDataset()
            if ConfigFile.products["bL2ProdSg"]:
                DerProd.attributes['Sg_UNITS'] = '1/nm'
                SgDS = DerProd.addDataset('gocad_Sg')
                SgDS.columns['Datetime'] = dateTime
                SgDS.columns['Datetag'] = dateTag
                SgDS.columns['Timetag2'] = timeTag2
                Sg = dict(zip(waveStrS,np.transpose(Sg).tolist()))
                for key, value in Sg.items(): SgDS.columns[key] = value
                SgDS.columnsToDataset()
            if ConfigFile.products["bL2ProdDOC"]:
                DerProd.attributes['doc_UNITS'] = 'umol/L'
                docDS = DerProd.addDataset('gocad_doc')
                docDS.columns['Datetime'] = dateTime
                docDS.columns['Datetag'] = dateTag
                docDS.columns['Timetag2'] = timeTag2
                docDS.columns['doc'] = doc.tolist()
                docDS.columnsToDataset()



        # GIOP
        # ''' Generalized ocean color inversion model for Inherent Optical Properties
        #     Werdell et al. 2013
        #     Not yet implemented'''


        # QAA
        # ''' Quasi-Analytcal Algorithm
        #     Lee et al. 2002, updated to QAAv6 for MODIS bands'''

        if ConfigFile.products["bL2Prodqaa"]:
            msg = "Processing qaa"
            print(msg)
            Utilities.writeLogFile(msg)

            # For fun, let's apply it to the full hyperspectral dataset
            keys = list(RrsHYPER.columns.keys())
            values = list(RrsHYPER.columns.values())
            waveStr = keys[3:]
            wavelength = np.array([float(i) for i in waveStr])
            Rrs = np.array(values[3:])

            T = Ancillary.datasets["SST"].columns["SST"]
            S = Ancillary.datasets["SALINITY"].columns["SALINITY"]

            # Maximum range based on P&F/S&B
            minMax = [380, 800]
            waveTemp = []
            RrsHyperTemp = []
            for i, wl in enumerate(wavelength):
                if wl >= minMax[0] and wl <= minMax[1]:
                    waveTemp.append(wl)
                    RrsHyperTemp.append(Rrs[i])
            wavelength = np.array(waveTemp)
            Rrs = np.array(RrsHyperTemp)
            waveStr = [f'{x}' for x in wavelength]

            a = np.empty(np.shape(Rrs))
            adg = np.empty(np.shape(Rrs))
            aph = np.empty(np.shape(Rrs))
            b = np.empty(np.shape(Rrs))
            bb = np.empty(np.shape(Rrs))
            bbp = np.empty(np.shape(Rrs))
            c = np.empty(np.shape(Rrs))
            for i in range(0, len(dateTime)):

                a[:,i], adg[:,i], aph[:,i], b[:,i], bb[:,i], bbp[:,i], c[:,i], msg = \
                    L2qaa(Rrs412[i], Rrs443[i], Rrs488[i], Rrs555[i], Rrs667[i], \
                        Rrs[:,i], wavelength, \
                            T[i], S[i])
                for msgs in msg:
                    Utilities.writeLogFile(msgs)

            if ConfigFile.products["bL2ProdaQaa"]:
                DerProd.attributes['a_UNITS'] = '1/m'
                aDS = DerProd.addDataset('qaa_a')
                aDS.columns['Datetime'] = dateTime
                aDS.columns['Datetag'] = dateTag
                aDS.columns['Timetag2'] = timeTag2
                a = dict(zip(waveStr,a.tolist()))
                for key, value in a.items(): aDS.columns[key] = value
                aDS.columnsToDataset()
            if ConfigFile.products["bL2ProdadgQaa"]:
                DerProd.attributes['adg_UNITS'] = '1/m'
                adgDS = DerProd.addDataset('qaa_adg')
                adgDS.columns['Datetime'] = dateTime
                adgDS.columns['Datetag'] = dateTag
                adgDS.columns['Timetag2'] = timeTag2
                adg = dict(zip(waveStr,adg.tolist()))
                for key, value in adg.items(): adgDS.columns[key] = value
                adgDS.columnsToDataset()
            if ConfigFile.products["bL2ProdaphQaa"]:
                DerProd.attributes['aph_UNITS'] = '1/m'
                aphDS = DerProd.addDataset('qaa_aph')
                aphDS.columns['Datetime'] = dateTime
                aphDS.columns['Datetag'] = dateTag
                aphDS.columns['Timetag2'] = timeTag2
                aph = dict(zip(waveStr,aph.tolist()))
                for key, value in aph.items(): aphDS.columns[key] = value
                aphDS.columnsToDataset()
            if ConfigFile.products["bL2ProdbQaa"]:
                DerProd.attributes['b_UNITS'] = '1/m'
                bDS = DerProd.addDataset('qaa_b')
                bDS.columns['Datetime'] = dateTime
                bDS.columns['Datetag'] = dateTag
                bDS.columns['Timetag2'] = timeTag2
                b = dict(zip(waveStr,b.tolist()))
                for key, value in b.items(): bDS.columns[key] = value
                bDS.columnsToDataset()
            if ConfigFile.products["bL2ProdbbQaa"]:
                DerProd.attributes['bb_UNITS'] = '1/m'
                bbDS = DerProd.addDataset('qaa_bb')
                bbDS.columns['Datetime'] = dateTime
                bbDS.columns['Datetag'] = dateTag
                bbDS.columns['Timetag2'] = timeTag2
                bb = dict(zip(waveStr,bb.tolist()))
                for key, value in bb.items(): bbDS.columns[key] = value
                bbDS.columnsToDataset()
            if ConfigFile.products["bL2ProdbbpQaa"]:
                DerProd.attributes['bbp_UNITS'] = '1/m'
                bbpDS = DerProd.addDataset('qaa_bbp')
                bbpDS.columns['Datetime'] = dateTime
                bbpDS.columns['Datetag'] = dateTag
                bbpDS.columns['Timetag2'] = timeTag2
                bbp = dict(zip(waveStr,bbp.tolist()))
                for key, value in bbp.items(): bbpDS.columns[key] = value
                bbpDS.columnsToDataset()
            if ConfigFile.products["bL2ProdcQaa"]:
                DerProd.attributes['c_UNITS'] = '1/m'
                cDS = DerProd.addDataset('qaa_c')
                cDS.columns['Datetime'] = dateTime
                cDS.columns['Datetag'] = dateTag
                cDS.columns['Timetag2'] = timeTag2
                c = dict(zip(waveStr,c.tolist()))
                for key, value in c.items(): cDS.columns[key] = value
                cDS.columnsToDataset()

