
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
        ''' Note: All field names apparently converted to lower case in readSB.
        Field names in SeaBASS are case insensitive'''
        if not readSB(fp, no_warn=True):
            msg = "Unable to read ancillary data file. Make sure it is in SeaBASS format."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None
        else:
            print('This may take a moment on large SeaBASS files...')
            metData=readSB(fp, no_warn=True)

        # metData = readSB(fp, no_warn=False)
        if not metData.fd_datetime():
            msg = "SeaBASS ancillary file has no datetimes and cannot be used."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None
        else:
            ancDatetime = metData.fd_datetime()

        '''TO DO: could add cloud cover, wave height, etc. here'''
        lat = False
        lon = False
        wind = False
        aot = False   
        wt = False
        sal = False
        heading = False
        homeangle = False # sensor azimuth relative to heading
        for ds in metData.data:            
            # Remember, all lower case...
            if ds == "lat":
                lat = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                lat = metData.data[ds]
                latUnits = metData.variables[ds][1]
            if ds == "lon":
                lon = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                lon = metData.data[ds]
                lonUnits = metData.variables[ds][1]
            if ds == "wind":
                wind = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                wspd = metData.data[ds]
                windUnits = metData.variables[ds][1]
            if ds.startswith("aot"):
                aot = True
                # Same as AOD or Tot. Aerosol Extinction
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                aot = metData.data[ds]
                aotUnits = metData.variables[ds][1] 
                if len(ds) == 3:
                    # with no waveband present, assume 550 nm
                    wv = '550'
                else:
                    wv = ds[3:]   
            if ds == "wt":
                wt = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                wT = metData.data[ds]
                wTUnits = metData.variables[ds][1] 
            if ds == "sal":
                sal = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                S = metData.data[ds]
                SUnits = metData.variables[ds][1] 
            if ds == "heading":
                heading = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                heading = metData.data[ds]
                headingUnits = metData.variables[ds][1]
            if ds == "relaz": # Note: this misnomer is to trick readSB into accepting a non-conventional data field (home angle)
                homeangle = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                homeAngle = metData.data[ds]
                homeAngleUnits = metData.variables[ds][1] 


        # Generate HDFDataset
        ancillaryData = HDFDataset()
        ancillaryData.id = "AncillaryData"
        ancillaryData.appendColumn("DATETIME", ancDatetime)
        if lat:
            ancillaryData.appendColumn("LATITUDE", lat)
            ancillaryData.attributes["Lat_Units"]=latUnits
        if lon:
            ancillaryData.appendColumn("LONGITUDE", lon)
            ancillaryData.attributes["Wind_Units"]=lonUnits            
        if wind:
            ancillaryData.appendColumn("WINDSPEED", wspd)
            ancillaryData.attributes["Wind_Units"]=windUnits
        if aot:
            ancillaryData.appendColumn("AOD", aot)
            ancillaryData.attributes["AOD_Units"]=aotUnits
            ancillaryData.attributes["AOD_wavelength"] = wv
        if wt:
            ancillaryData.appendColumn("SST", wT)
            ancillaryData.attributes["SST_Units"]=wTUnits
        if sal:
            ancillaryData.appendColumn("SALINITY", S)
            ancillaryData.attributes["SALINITY_Units"]=SUnits
        #ancillaryData.appendColumn("LATPOS", lat)
        #ancillaryData.appendColumn("LONPOS", lon)
        if heading:
            ancillaryData.appendColumn("HEADING", heading)
            ancillaryData.attributes["HEADING_Units"]=headingUnits
        if homeangle:
            ancillaryData.appendColumn("HOMEANGLE", homeAngle)
            ancillaryData.attributes["HOMEANGLE_Units"]=homeAngleUnits
        
        ancillaryData.columnsToDataset()        

        return ancillaryData

