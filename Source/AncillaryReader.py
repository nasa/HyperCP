
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

        station = False
        lat = False
        lon = False
        wspd = False
        aot = False   
        wT = False
        S = False
        heading = False
        speed_f_w = False
        homeAngle = False # sensor azimuth relative to heading
        cloud = False
        waveht = False
        pitch = False
        roll = False

        for ds in ancData.data:            
            # Remember, all lower case...
            if ds == "station":
                # lat = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                station = ancData.data[ds]
                staUnits = ancData.variables[ds][1]
            if ds == "lat":
                # lat = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                lat = ancData.data[ds]
                latUnits = ancData.variables[ds][1]
            if ds == "lon":
                # lon = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                lon = ancData.data[ds]
                lonUnits = ancData.variables[ds][1]
            if ds == "wind":
                # wind = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                wspd = ancData.data[ds]
                windUnits = ancData.variables[ds][1]
            if ds.startswith("aot"):
                # aot = True
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
                # wt = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                wT = ancData.data[ds]
                wTUnits = ancData.variables[ds][1] 
            if ds == "sal":
                # sal = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                S = ancData.data[ds]
                SUnits = ancData.variables[ds][1] 
            if ds == "heading":
                # heading = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                heading = ancData.data[ds]
                headingUnits = ancData.variables[ds][1]
            if ds == "relaz": # Note: this misnomer is to trick readSB into accepting a non-conventional data field (home angle)
                # SeaBASS thinks RelAz is between sensor and sun, but this is sensor to ship heading. We will call this dataset
                # HOMEANGLE.
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                homeAngle = ancData.data[ds]
                homeAngleUnits = ancData.variables[ds][1] 
            if ds == "cloud":
                # cloud = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                cloud = ancData.data[ds]
                cloudUnits = ancData.variables[ds][1]
            if ds == "waveht":
                # heading = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                waveht = ancData.data[ds]
                waveUnits = ancData.variables[ds][1]
            if ds == "speed_f_w":
                # heading = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                speed_f_w = ancData.data[ds]
                speedUnits = ancData.variables[ds][1]
            if ds == "pitch":
                # heading = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                pitch = ancData.data[ds]
                pitchUnits = ancData.variables[ds][1]
            if ds == "roll":
                # heading = True
                msg = f'Found data: {ds}'                
                print(msg)
                Utilities.writeLogFile(msg)  
                roll = ancData.data[ds]
                rollUnits = ancData.variables[ds][1]


        # Generate HDFDataset
        ancillaryData = HDFDataset()
        ancillaryData.id = "AncillaryData"
        ancillaryData.appendColumn("DATETIME", ancDatetime)
        if station:
            ancillaryData.appendColumn("STATION", station)
            ancillaryData.attributes["STATION_Units"]=staUnits
        if lat:
            ancillaryData.appendColumn("LATITUDE", lat)
            ancillaryData.attributes["LATITUDE_Units"]=latUnits
        if lon:
            ancillaryData.appendColumn("LONGITUDE", lon)
            ancillaryData.attributes["LONGITUDE_Units"]=lonUnits            
        if wspd:
            ancillaryData.appendColumn("WINDSPEED", wspd)
            ancillaryData.attributes["WINDSPEED_Units"]=windUnits
        if aot:
            ancillaryData.appendColumn("AOD", aot)
            ancillaryData.attributes["AOD_Units"]=aotUnits
            ancillaryData.attributes["AOD_wavelength"] = wv
        if wT:
            ancillaryData.appendColumn("SST", wT)
            ancillaryData.attributes["SST_Units"]=wTUnits
        if S:
            ancillaryData.appendColumn("SALINITY", S)
            ancillaryData.attributes["SALINITY_Units"]=SUnits        
        if heading:
            ancillaryData.appendColumn("HEADING", heading)
            ancillaryData.attributes["HEADING_Units"]=headingUnits
        if homeAngle:
            ancillaryData.appendColumn("HOMEANGLE", homeAngle)
            ancillaryData.attributes["HOMEANGLE_Units"]=homeAngleUnits
        if cloud:
            ancillaryData.appendColumn("CLOUD", cloud)
            ancillaryData.attributes["CLOUD_Units"]=cloudUnits        
        if waveht:
            ancillaryData.appendColumn("WAVE_HT", waveht)
            ancillaryData.attributes["WAVE_Units"]=waveUnits
        if speed_f_w:
            ancillaryData.appendColumn("SPEED_F_W", speed_f_w)
            ancillaryData.attributes["SPEED_F_W_Units"]=speedUnits
        if pitch:
            ancillaryData.appendColumn("PITCH", pitch)
            ancillaryData.attributes["PITCH_Units"]=pitchUnits
        if roll:
            ancillaryData.appendColumn("ROLL", roll)
            ancillaryData.attributes["ROLL_Units"]=rollUnits

        ancillaryData.columnsToDataset()        

        return ancillaryData

        
    # @staticmethod
    # def ancillaryFromMetadata(ancGroup):
    #     ''' Reads ancillary data from ANCILLARY_METADATA group and returns an HDFDataset 
    #         This is called from ProcessL2 prior to merging all ancillary datasets. '''

    #     print("AncillaryReader.ancillaryFromMetadata: " + ancGroup.id)        

    #     # ancGroup here has already been interpolated to radiometry in L1E, so all 
    #     # datasets have data columns (in data, not in columns) for Datetag and Timetag2
    #     # Choose any (required) dataset to find datetime
    #     lat = ancGroup.getDataset("LATITUDE")
    #     lat.datasetToColumns()
    #     dateTag = lat.columns["Datetag"]
    #     tt2 = lat.columns["Timetag2"]
    #     ancDatetime = []
    #     for i, dt in enumerate(dateTag):
    #         ancDatetime.append(Utilities.timeTag2ToDateTime( Utilities.dateTagToDateTime(dt),tt2[i] ))

    #     aot = False   
    #     heading = False
    #     station = False
    #     lat = False
    #     lon = False
    #     # Misnomer for ancillary metadata: sensor azimuth relative to HEADING for ancillary seabass file
    #     # Not sensor relative to solar azimuth..
    #     relAz = False 
    #     S = False
    #     solAZ = False
    #     wT = False
    #     SZA = False
    #     wspd = False
    #     cloud = False
    #     waveht = False
    #     speed_f_w = False
        
    #     for ds in ancGroup.datasets:  
    #         if ds.startswith("AOD"):
    #             # aot = True
    #             # Same as AOD or Tot. Aerosol Extinction
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             aot = ancGroup.datasets[ds]
    #             if len(ds) == 3:
    #                 # with no waveband present, assume 550 nm
    #                 wv = '550'
    #             else:
    #                 wv = ds[3:]  
    #         if ds == "HEADING":
    #             # heading = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             heading = ancGroup.datasets[ds].data["NONE"].tolist()

    #         if ds == "STATION":
    #             # lat = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             station = ancGroup.datasets[ds].data["NONE"].tolist()

    #         if ds == "LATITUDE":
    #             # lat = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             lat = ancGroup.datasets[ds].data["NONE"].tolist()
    #         if ds == "LONGITUDE":
    #             # lon = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             lon = ancGroup.datasets[ds].data["NONE"].tolist()
    #         if ds == "REL_AZ":
    #             # relAz = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             relAz = ancGroup.datasets[ds].data["NONE"].tolist()
    #         if ds == "SOLAR_AZ":
    #             # solAz = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             solAZ = ancGroup.datasets[ds].data["NONE"].tolist()
    #         if ds == "SST":
    #             # wt = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             wT = ancGroup.datasets[ds].data["NONE"].tolist()
    #         if ds == "SALINITY":
    #             # sal = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             S = ancGroup.datasets[ds].data["NONE"].tolist()
    #         if ds == "SZA":
    #             # sza = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             SZA = ancGroup.datasets[ds].data["NONE"].tolist()            
    #         if ds == "WINDSPEED":
    #             # wind = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             wspd = ancGroup.datasets[ds].data["NONE"].tolist()
    #         # HOMEANGLE not retained
    #         if ds == "CLOUD":
    #             # cloud = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             cloud = ancGroup.datasets[ds].data["NONE"].tolist()
    #         if ds == "WAVE_HT":
    #             # waveht = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             waveht = ancGroup.datasets[ds].data["NONE"].tolist()
    #         if ds == "SPEED_F_W":
    #             # waveht = True
    #             msg = f'Found data: {ds}'                
    #             print(msg)
    #             Utilities.writeLogFile(msg)  
    #             speed_f_w = ancGroup.datasets[ds].data["NONE"].tolist()

    #     # Generate HDFDataset
    #     ancillaryData = HDFDataset()
    #     ancillaryData.id = "AncillaryData"
    #     ancillaryData.attributes = ancGroup.attributes.copy()
    #     ancillaryData.appendColumn("DATETIME", ancDatetime)
    #     if aot:
    #         ancillaryData.appendColumn("AOD", aot)
    #         ancillaryData.attributes["AOD_wavelength"] = wv
    #     if heading:
    #         ancillaryData.appendColumn("HEADING", heading)
    #     if station:
    #         ancillaryData.appendColumn("STATION", station)
    #     if lat:
    #         ancillaryData.appendColumn("LATITUDE", lat)
    #     if lon:
    #         ancillaryData.appendColumn("LONGITUDE", lon)
    #     if relAz:
    #         ancillaryData.appendColumn("REL_AZ", relAz)
    #     if S:
    #         ancillaryData.appendColumn("SALINITY", S)
    #     if solAZ:
    #         ancillaryData.appendColumn("SOLAR_AZ", solAZ)
    #     if wT:
    #         ancillaryData.appendColumn("SST", wT)
    #     if SZA:
    #         ancillaryData.appendColumn("SZA", SZA)
    #     if wspd:
    #         ancillaryData.appendColumn("WINDSPEED", wspd)
    #     if cloud:
    #         ancillaryData.appendColumn("CLOUD", cloud)
    #     if waveht:
    #         ancillaryData.appendColumn("WAVE_HT", waveht)
    #     if speed_f_w:
    #         ancillaryData.appendColumn("SPEED_F_W", waveht)
        
    #     ancillaryData.columnsToDataset()        

    #     return ancillaryData

