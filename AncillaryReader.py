
import csv

from datetime import datetime
import pytz

from HDFDataset import HDFDataset
from SB_support import readSB
from Utilities import Utilities


class AncillaryReader:

    # Reads a wind speed SeaBASS file and returns an HDFDataset
    @staticmethod
    def readAncillary(fp):
        print("AncillaryReader.readAncillary: " + fp)
        
        try:                    
            print('This may take a moment on large SeaBASS files...')
            ancData=readSB(fp, no_warn=True)
        except IOError:
            msg = "Unable to read ancillary data file. Make sure it is in SeaBASS format."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None

        # ancData = readSB(fp, no_warn=False)
        if not ancData.fd_datetime():
            msg = "SeaBASS ancillary file has no datetimes and cannot be used."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None
        else:
            ancDatetime = ancData.fd_datetime()
            # Convert to timezone aware
            ancDatetimeTZ = []
            for dt in ancDatetime:
                timezone = pytz.utc
                ancDatetimeTZ.append(timezone.localize(dt))
            ancDatetime = ancDatetimeTZ


        '''TO DO: could add cloud cover, wave height, etc. here'''
        lat = False
        lon = False
        wind = False
        aot = False   
        wt = False
        sal = False
        heading = False
        homeangle = False # sensor azimuth relative to heading
        for ds in ancData.data:            
            # Remember, all lower case...
            if ds == "lat":
                lat = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                lat = ancData.data[ds]
                latUnits = ancData.variables[ds][1]
            if ds == "lon":
                lon = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                lon = ancData.data[ds]
                lonUnits = ancData.variables[ds][1]
            if ds == "wind":
                wind = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                wspd = ancData.data[ds]
                windUnits = ancData.variables[ds][1]
            if ds.startswith("aot"):
                aot = True
                # Same as AOD or Tot. Aerosol Extinction
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                aot = ancData.data[ds]
                aotUnits = ancData.variables[ds][1] 
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
                wT = ancData.data[ds]
                wTUnits = ancData.variables[ds][1] 
            if ds == "sal":
                sal = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                S = ancData.data[ds]
                SUnits = ancData.variables[ds][1] 
            if ds == "heading":
                heading = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                heading = ancData.data[ds]
                headingUnits = ancData.variables[ds][1]
            if ds == "relaz": # Note: this misnomer is to trick readSB into accepting a non-conventional data field (home angle)
                homeangle = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                homeAngle = ancData.data[ds]
                homeAngleUnits = ancData.variables[ds][1] 


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

        
    @staticmethod
    def ancillaryFromNoTracker(ancGroup):
        ''' Reads ancillary data from ANCILLARY_NOTRACKER group and returns an HDFDataset '''

        print("AncillaryReader.ancillaryFromNoTracker: " + ancGroup.id)
        
        # try:                    
        #     print('This may take a moment on large SeaBASS files...')
        #     ancData=readSB(fp, no_warn=True)
        # except IOError:
        #     msg = "Unable to read ancillary data file. Make sure it is in SeaBASS format."
        #     print(msg)
        #     Utilities.writeLogFile(msg)  
        #     return None

        # # ancData = readSB(fp, no_warn=False)
        # if not ancData.fd_datetime():
        #     msg = "SeaBASS ancillary file has no datetimes and cannot be used."
        #     print(msg)
        #     Utilities.writeLogFile(msg)  
        #     return None
        # else:
        #     ancDatetime = ancData.fd_datetime()
        #     # Convert to timezone aware
        #     ancDatetimeTZ = []
        #     for dt in ancDatetime:
        #         timezone = pytz.utc
        #         ancDatetimeTZ.append(timezone.localize(dt))
        #     ancDatetime = ancDatetimeTZ        

        # ancGroup here has already been interpolated to radiometry in L1E, so all 
        # datasets have data columns (in data, not in columns) for Datetag and Timetag2
        # Choose any (required) dataset to find datetime
        relAz = ancGroup.getDataset("REL_AZ")
        relAz.datasetToColumns()
        dateTag = relAz.columns["Datetag"]
        tt2 = relAz.columns["Timetag2"]
        ancDatetime = []
        for i, dt in enumerate(dateTag):
            ancDatetime.append(Utilities.timeTag2ToDateTime( Utilities.dateTagToDateTime(dt),tt2[i] ))


        '''TO DO: could add cloud cover, wave height, etc. here'''
        # lat = False
        # lon = False
        wind = False
        # aot = False   
        wt = False
        sal = False
        heading = False
        relAz = False # sensor azimuth relative to heading
        for ds in ancGroup.datasets:            
            # # Remember, all lower case...
            # if ds == "lat":
            #     lat = True
            #     msg = f'Found data: {ds}'                
            #     print(msg)
            #     Utilities.writeLogFile(msg)  
            #     lat = ancGroup.datasets[ds]
            #     # latUnits = ancData.variables[ds][1]
            # if ds == "lon":
            #     lon = True
            #     msg = f'Found data: {ds}'                
            #     print(msg)
            #     Utilities.writeLogFile(msg)  
            #     lon = ancGroup.datasets[ds]
            #     # lonUnits = ancData.variables[ds][1]
            if ds == "WINDSPEED":
                wind = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                wspd = ancGroup.datasets[ds].data["NONE"].tolist()
                # windUnits = ancData.variables[ds][1]
            # if ds.startswith("aot"):
            #     aot = True
            #     # Same as AOD or Tot. Aerosol Extinction
            #     msg = f'Found data: {ds}'                
            #     print(msg)
            #     Utilities.writeLogFile(msg)  
            #     aot = ancGroup.datasets[ds]
            #     # aotUnits = ancData.variables[ds][1] 
            #     if len(ds) == 3:
            #         # with no waveband present, assume 550 nm
            #         wv = '550'
            #     else:
            #         wv = ds[3:]   
            if ds == "SST":
                wt = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                wT = ancGroup.datasets[ds].data["NONE"].tolist()
                # wTUnits = ancData.variables[ds][1] 
            if ds == "SALINITY":
                sal = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                S = ancGroup.datasets[ds].data["NONE"].tolist()
                # SUnits = ancData.variables[ds][1] 
            if ds == "HEADING":
                heading = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                heading = ancGroup.datasets[ds].data["NONE"].tolist()
                # headingUnits = ancData.variables[ds][1]
            if ds == "REL_AZ":
                relAz = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                relAz = ancGroup.datasets[ds].data["NONE"].tolist()
                # homeAngleUnits = ancData.variables[ds][1] 


        # Generate HDFDataset
        ancillaryData = HDFDataset()
        ancillaryData.id = "AncillaryData"
        ancillaryData.appendColumn("DATETIME", ancDatetime)
        # if lat:
        #     ancillaryData.appendColumn("LATITUDE", lat)
        #     ancillaryData.attributes["Lat_Units"]='degrees'
        # if lon:
        #     ancillaryData.appendColumn("LONGITUDE", lon)
        #     ancillaryData.attributes["Wind_Units"]='degrees'
        if wind:
            ancillaryData.appendColumn("WINDSPEED", wspd)
            ancillaryData.attributes["Wind_Units"]='m/s'
        # if aot:
        #     ancillaryData.appendColumn("AOD", aot)
        #     # ancillaryData.attributes["AOD_Units"]=aotUnits
        #     ancillaryData.attributes["AOD_wavelength"] = wv
        if wt:
            ancillaryData.appendColumn("SST", wT)
            ancillaryData.attributes["SST_Units"]='degrees_C'
        if sal:
            ancillaryData.appendColumn("SALINITY", S)
            ancillaryData.attributes["SALINITY_Units"]='psu'
        if heading:
            ancillaryData.appendColumn("HEADING", heading)
            ancillaryData.attributes["HEADING_Units"]='degrees'
        # if homeangle:
        #     ancillaryData.appendColumn("HOMEANGLE", homeAngle)
            # ancillaryData.attributes["HOMEANGLE_Units"]=homeAngleUnits
        if relAz:
            ancillaryData.appendColumn("REL_AZ", relAz)
            ancillaryData.attributes["REL_AZ_Units"]='degrees'
        
        ancillaryData.columnsToDataset()        

        return ancillaryData

