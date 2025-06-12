
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
            Utilities.writeLogFileAndPrint("Unable to read ancillary data file. Make sure it is in SeaBASS format.")
            return None

        # ancData = readSB(fp, no_warn=False)
        if not ancData.fd_datetime():
            Utilities.writeLogFileAndPrint("SeaBASS ancillary file has no datetimes and cannot be used.")
            return None
        else:
            ancDatetime = ancData.fd_datetime()
            # Convert to timezone aware
            ancDatetimeTZ = []
            for dt in ancDatetime:
                timezone = pytz.utc
                ancDatetimeTZ.append(timezone.localize(dt))
            ancDatetime = ancDatetimeTZ

        # Generate HDFDataset
        ancillaryData = HDFDataset()
        ancillaryData.id = "AncillaryData"
        ancillaryData.appendColumn("DATETIME", ancDatetime)

        dsTranslation = {'station':['STATION','STATION_UNITS'],
                         'lat':['LATITUDE','LATITUDE_UNITS'],
                         'lon':['LONGITUDE','LONGITUDE_UNITS'],
                         'wind':['WINDSPEED','WINDSPEED_UNITS'],
                         'aot':['AOD','AOD_UNITS'],
                         'at':['AIRTEMP','AIRTEMP_UNITS'],
                         'wt':['SST','SST_UNITS'],
                         'sal':['SALINITY','SALINITY_UNITS'],
                         'heading':['HEADING','HEADING_UNITS'],
                         'relaz':['REL_AZ','RELAZ_UNITS'],
                         'speed_f_w':['SPEED_F_W','SPEED_F_W_UNITS'],
                         'sensor_azimuth':['SENSOR_AZ','SENSORAZ_UNITS'],
                         'cloud':['CLOUD','CLOUD_UNITS'],
                         'waveht':['WAVE_HT','WAVE_UNITS'],
                         'pitch':['PITCH','PITCH_UNITS'],
                         'roll':['ROLL','ROLL_UNITS']}

        for ds in ancData.data:
            if ds in dsTranslation:
                Utilities.writeLogFileAndPrint(f'Found data: {ds}')
                ancillaryData.appendColumn(dsTranslation[ds][0], ancData.data[ds])
                ancillaryData.attributes[dsTranslation[ds][1]]=ancData.variables[ds][1]
                if ds == 'aot':
                    if len(ds) == 3:
                        # with no waveband present, assume 550 nm
                        wv = '550'
                    else:
                        wv = ds[4:]
                    ancillaryData.attributes["AOD_wavelength"] = wv

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
            Utilities.writeLogFileAndPrint("Unable to read ancillary data file. Make sure it is in SeaBASS format.")
            return None

        return ancData.headers
