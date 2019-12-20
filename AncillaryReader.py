
import csv

from datetime import datetime

from HDFDataset import HDFDataset
from SB_support import readSB
from Utilities import Utilities


class AncillaryReader:

    # Reads a wind speed SeaBASS file and returns an HDFDataset
    @staticmethod
    def readAncillary(fp):
        print("AncillaryReader.readAncillary: " + fp)

        # metData = readSB(fp,mask_missing=False, no_warn=True)
        if not readSB(fp, no_warn=True):
            msg = "Unable to read ancillary data file. Make sure it is in SeaBASS format."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None
        else:
            metData=readSB(fp, no_warn=True)

        # metData = readSB(fp, no_warn=False)
        if not metData.fd_datetime():
            msg = "SeaBASS ancillary file has no datetimes and cannot be used."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None
        else:
            ancDatetime = metData.fd_datetime()

        for ds in metData.data:
            if ds == ("wind"):
                wind = True
                print(ds)
                wspd = metData.data['wind']
                windUnits = metData.variables['wind'][1]
            else:
                wind = False

            if ds.startswith("AOT"):
                aot = True
                # Same as AOD or Tot. Aerosol Extinction
                print(ds)
                aot = metData.data[ds]
                windUnits = metData.variables[ds][1] 
                if len(ds) == 3:
                    # with no waveband present, assume 550 nm
                    wv = '550'
                else:
                    wv = ds[3:]   
            else:
                aot = False   

            if ds == ("Wt"):
                wt = True
                print(ds)
                wT = metData.data['Wt']
                wTUnits = metData.variables['Wt'][1] 
            else:
                wt = False

            if ds == ("sal"):
                sal = True
                print(ds)
                S = metData.data['sal']
                SUnits = metData.variables['sal'][1] 
            else:
                sal = False


        # Generate HDFDataset
        ancillaryData = HDFDataset()
        ancillaryData.id = "AncillaryData"
        ancillaryData.appendColumn("DATETIME", ancDatetime)
        if wind:
            ancillaryData.appendColumn("WINDSPEED", wspd)
            ancillaryData.attributes["Wind_Units"]=windUnits
        if aot:
            ancillaryData.appendColumn("AOD", aot)
            ancillaryData.attributes["AOD_Units"]=windUnits
            ancillaryData.attributes["AOD_wavelength"] = wv
        if wt:
            ancillaryData.appendColumn("SST", wT)
            ancillaryData.attributes["SST_Units"]=wTUnits
        if sal:
            ancillaryData.appendColumn("SALINITY", S)
            ancillaryData.attributes["SALINITY_Units"]=SUnits
        #ancillaryData.appendColumn("LATPOS", lat)
        #ancillaryData.appendColumn("LONPOS", lon)
        
        ancillaryData.columnsToDataset()        

        return ancillaryData

