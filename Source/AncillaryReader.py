
import pytz

from Source.HDFDataset import HDFDataset
from Source.SB_support import readSB
from Source.Utilities import Utilities


class AncillaryReader:

    # Reads SeaBASS ancillary data file and returns an HDFDataset
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
        wv = None
        wT = False
        S = False
        heading = False
        speed_f_w = False
        # homeAngle = False # no longer in use
        relAzAngle = False
        sensorAzAngle = False
        cloud = False
        waveht = False
        pitch = False
        roll = False

        staUnits = None
        latUnits = None
        lonUnits = None
        windUnits = None
        aotUnits = None
        wTUnits = None
        SUnits = None
        headingUnits = None
        relAzAngleUnits = None
        sensorAzAngleUnits = None
        cloudUnits = None
        waveUnits = None
        speedUnits = None
        pitchUnits = None
        rollUnits = None

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
                    wv = ds[4:]
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
            if ds == "relaz": # Updated v1.2.0: This is sensor-solar relative azimuth
                msg = f'Found data: {ds}'
                print(msg)
                Utilities.writeLogFile(msg)
                relAzAngle = ancData.data[ds]
                relAzAngleUnits = ancData.variables[ds][1]
            if ds == "sensor_azimuth": # This is a new SeaBASS field
                msg = f'Found data: {ds}'
                print(msg)
                Utilities.writeLogFile(msg)
                sensorAzAngle = ancData.data[ds]
                sensorAzAngleUnits = ancData.variables[ds][1]
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
            ancillaryData.attributes["STATION_UNITS"]=staUnits
        if lat:
            ancillaryData.appendColumn("LATITUDE", lat)
            ancillaryData.attributes["LATITUDE_UNITS"]=latUnits
        if lon:
            ancillaryData.appendColumn("LONGITUDE", lon)
            ancillaryData.attributes["LONGITUDE_UNITS"]=lonUnits
        if wspd:
            ancillaryData.appendColumn("WINDSPEED", wspd)
            ancillaryData.attributes["WINDSPEED_UNITS"]=windUnits
        if aot:
            ancillaryData.appendColumn("AOD", aot)
            ancillaryData.attributes["AOD_UNITS"]=aotUnits
            ancillaryData.attributes["AOD_wavelength"] = wv
        if wT:
            ancillaryData.appendColumn("SST", wT)
            ancillaryData.attributes["SST_UNITS"]=wTUnits
        if S:
            ancillaryData.appendColumn("SALINITY", S)
            ancillaryData.attributes["SALINITY_UNITS"]=SUnits
        if heading:
            ancillaryData.appendColumn("HEADING", heading)
            ancillaryData.attributes["HEADING_UNITS"]=headingUnits
        # if homeAngle:
        #     ancillaryData.appendColumn("HOMEANGLE", homeAngle)
        #     ancillaryData.attributes["HOMEANGLE_UNITS"]=homeAngleUnits
        if relAzAngle:
            ancillaryData.appendColumn("REL_AZ", relAzAngle)
            ancillaryData.attributes["RELAZ_UNITS"]=relAzAngleUnits
        if sensorAzAngle:
            ancillaryData.appendColumn("SENSOR_AZ", sensorAzAngle)
            ancillaryData.attributes["SENSORAZ_UNITS"]=sensorAzAngleUnits
        if cloud:
            ancillaryData.appendColumn("CLOUD", cloud)
            ancillaryData.attributes["CLOUD_UNITS"]=cloudUnits
        if waveht:
            ancillaryData.appendColumn("WAVE_HT", waveht)
            ancillaryData.attributes["WAVE_UNITS"]=waveUnits
        if speed_f_w:
            ancillaryData.appendColumn("SPEED_F_W", speed_f_w)
            ancillaryData.attributes["SPEED_F_W_UNITS"]=speedUnits
        if pitch:
            ancillaryData.appendColumn("PITCH", pitch)
            ancillaryData.attributes["PITCH_UNITS"]=pitchUnits
        if roll:
            ancillaryData.appendColumn("ROLL", roll)
            ancillaryData.attributes["ROLL_UNITS"]=rollUnits

        ancillaryData.columnsToDataset()

        return ancillaryData

    # Reads SeaBASS ancillary data file and returns an HDFDataset
    @staticmethod
    def readAncillaryHeader(fp):
        print("AncillaryReader.readAncillaryHeader: " + fp)

        try:
            print('This may take a moment on large SeaBASS files...')
            ancData=readSB(fp, no_warn=True)
        except IOError:
            msg = "Unable to read ancillary data file. Make sure it is in SeaBASS format."
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        return ancData.headers
