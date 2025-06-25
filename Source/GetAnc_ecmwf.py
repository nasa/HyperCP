import os
import shutil
# import stat
import numpy as np
import xarray as xr
import pandas as pd
# import math
import datetime
import configparser
import decimal
import cdsapi

from Source import PATH_TO_DATA, PACKAGE_DIR
# from Source.MainConfig import MainConfig
from Source.HDFRoot import HDFRoot
# from HDFGroup import HDFGroup
from Source.Utilities import Utilities
from Source.GetAnc_credentials import GetAnc_credentials

class GetAnc_ecmwf:

    @staticmethod
    def ECMWF_latLonTimeTags(lat: float, lon: float, timeStamp: datetime.datetime, latRes: float, lonRes: float, timeResHours: float) -> tuple[float,float,str,str,str]:
        '''
        :param lat: a float, the query latitude in degrees North
        :param lon: a float, the query longitude in degrees East
        :param timeStamp: a datetime.datetime, the time in UTC
        :param timeResHours: an integer, time resolution of the queried ECMWF dataset
        :return:
        latEff: a float, the effective latitude - i.e. to the closest resolution degree
        lonEff: a float, the effective latitude - i.e. to the closest resolution degree
        latLonTag: a string, a tag to indicate the effective lat/lon.
        dateStrRounded: a string, a tag to indicate effective date (i.e. date in UTC rounded to closest hour)
        timeStrRounded: a string, a tag to indicate effective time (i.e. time in UTC rounded to closest hour)
        '''

        # Lat-Lon
        latEff = np.round(lat / latRes) * latRes
        lonEff = np.round(lon / lonRes) * lonRes

        latSigFigures = np.abs(decimal.Decimal(str(latRes)).as_tuple().exponent)
        lonSigFigures = np.abs(decimal.Decimal(str(lonRes)).as_tuple().exponent)

        latLonTagFormat = '%s%0' + str(3 + lonSigFigures) + 'd%s%0' + str(2 + latSigFigures) + 'd'

        latLonTag = latLonTagFormat % (str(int(np.sign(lonEff))).replace('-1', 'W').replace('1', 'E'),
                                    np.abs(lonEff * (10 ** lonSigFigures)),
                                    str(int(np.sign(latEff))).replace('-1', 'S').replace('1', 'N'),
                                    np.abs(latEff * (10 ** latSigFigures)))

        # Obtain rounded date and time considering the temporal resolution of the dataset)
        epoch_time = timeStamp.timestamp()
  
        # epoch_time = datetime.datetime.strptime(timeStamp, '%Y-%m-%dT%H:%M:%S').timestamp()
        timeResSecs = 3600 * timeResHours
        rounded_epoch_time = np.floor(epoch_time / timeResSecs) * timeResSecs # changed from round to np.floor (I think it was is downloading data with a 1 hr offset?)
        rounded_timestamp = datetime.datetime.fromtimestamp(rounded_epoch_time)
        dateStrRounded, timeStrRounded = rounded_timestamp.strftime('%Y-%m-%dT%H:%M:%S').split('T')

        return latEff,lonEff,latLonTag,dateStrRounded,timeStrRounded


    @staticmethod
    def CAMS_download_ensembles(lat: float, lon: float, dateStrRounded: str, timeStrRounded: str, CAMS_variables: list, pathOut: str) -> None:
        '''
        Performs CDSAPI command to download the required data from CAMS (dataset "cams-global-atmospheric-composition-forecasts") in netCDF
        format. It will retrieve the variables in a single space-time point corresponding to

        For more information, please check: https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-atmospheric-composition-forecasts?tab=overview

        :param dateStrRounded: a string, the date in UTC with format yyyy-mm-dd,
        :param timeStrRounded: a string, the time in UTC with format hh:MM:ss,
        :param lat: a float, the query latitude in degrees North
        :param lon: a float, the query longitude in degrees East

        :param CAMS_variables: a list, with the variables of interest
        :param pathOut: full path to output, a netCDF file with the requested variables.
        :return:
        '''

        if os.path.exists(pathOut):
            pass
        else:
            url,key = GetAnc_credentials.read_user_credentials('ECMWF_ADS')

            year = dateStrRounded.split('-')[0]
            hour = timeStrRounded.split(':')[0]

            hourForecast = '%02d' % ((int(hour) // 12) * 12)
            leadtime     = str(int(hour) % 12)

            if int(year) < 2015:
                print('CAMS dataset not available before 2015, skipping')
            else:
                try:
                 
                    c = cdsapi.Client(timeout=5, url=url, key=key)
                    c.retrieve(
                        'cams-global-atmospheric-composition-forecasts',
                        {
                            'type' : 'forecast',
                            'variable': list(CAMS_variables.keys()),
                            'date': '%s/%s' % (dateStrRounded, dateStrRounded),
                            'area': [lat, lon, lat, lon],
                            'time': '%s:00' % hourForecast,
                            'leadtime_hour': leadtime,
                            'format': 'netcdf',
                        },
                        pathOut)
                except:
                    raise Exception('CAMS atmospheric data could not be retrieved. Check inputs.')
        return

    @staticmethod
    def get_ancillary_main(lat: float, lon: float, timeStamp: datetime.datetime, pathAncillary: str, latRes: float = 0.4, lonRes: float = 0.4, timeResHours: float = 1) -> dict:
        '''
        Retrieves ancillary
        :param lat: a float, the query latitude in degrees North
        :param lon: a float, the query longitude in degrees East
        :param timeStamp: a datetime.datetime object, the time in UTC
        :param pathAncillary:a string, /full/path/to/where_you_wish_to_store_the_ECMWF_netcdfs
        :param latRes: a float, latitude resolution in degrees.
        :param lonRes: a float, longitude resolution in degrees.
        :param timeResHours: a float, longitude resolution in degrees.
            Defaults for latRes, lonRes and timeResHours come from:
             https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-atmospheric-composition-forecasts?tab=overview
        :return:
        ancillary: a dictionary, organised as:
            --> variable
                --> value
                --> units
                --> description
            --> variable absolute uncertainty (k=1), var_unc
                --> value
                --> units
                --> description
        '''

        ancillary = {}

        #################### CAMS ####################
        pathCAMS = pathAncillary
        if not os.path.exists(pathCAMS):
            os.mkdir(pathCAMS)

        CAMS_variables = {
        '10m_u_component_of_wind' :'u10',
        '10m_v_component_of_wind' :'v10',
        'total_aerosol_optical_depth_550nm' :'aod550',
        '2m_temperature': 't2m'
        }

        CAMSnc = {}


        latEff, lonEff, latLonTag, dateStrRounded, timeStrRounded = GetAnc_ecmwf.ECMWF_latLonTimeTags(lat, lon, timeStamp, latRes=latRes, lonRes=lonRes, timeResHours=timeResHours)

        pathOut = os.path.join(pathCAMS, 'CAMS_%s_%s_%s.nc' % (latLonTag, dateStrRounded.replace('-',''), timeStrRounded.replace(':','')))

        GetAnc_ecmwf.CAMS_download_ensembles(latEff, lonEff, dateStrRounded, timeStrRounded, CAMS_variables, pathOut)

        try:
            CAMSnc['reanalysis'] = xr.open_dataset(pathOut,engine='netcdf4')
            CAMS_flag = True
        except:
            CAMS_flag = False
            print('CAMS data missing. Skipping...')

        if CAMS_flag:
            try:
                for CAMS_variable, shortName in CAMS_variables.items():
                    var = CAMSnc['reanalysis'][shortName]
                    ancillary[CAMS_variable] = {}
                    ancillary[CAMS_variable]['value']      = var.values[0][0][0][0]
                    ancillary[CAMS_variable]['units']      = var.units
                    ancillary[CAMS_variable]['long_name']  = var.long_name
                    ancillary[CAMS_variable]['source']     = 'CAMS (ECMWF). https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-atmospheric-composition-forecasts?tab=overview'
            except:
                print('Problem processing CAMS data. Skipping...')

        return ancillary

    @staticmethod
    def getAnc_ecmwf(inputGroup):
        ''' Retrieve model data from ECMWF and save in Data/Anc and in ModData '''
        # cwd = os.getcwd()
        ancPath = os.path.join(PATH_TO_DATA, 'Anc')

        # Get the dates, times, and locations from the input group
        latDate = inputGroup.getDataset('LATITUDE').data["Datetag"]
        latTime = inputGroup.getDataset('LATITUDE').data["Timetag2"]
        lat = inputGroup.getDataset('LATITUDE').data["NONE"]
        lon = inputGroup.getDataset('LONGITUDE').data["NONE"]

        modWind = []
        modAirT = []
        modAOD = []

        # Loop through the input group and extract model data for each element
        for index, dateTag in enumerate(latDate):
            dateTagNew = Utilities.dateTagToDateTime(dateTag)
            timeStamp = Utilities.timeTag2ToDateTime(dateTagNew,latTime[index])

            ancillary = GetAnc_ecmwf.get_ancillary_main(lat[index], lon[index], timeStamp, ancPath)

            # position retrieval index has been confirmed manually in SeaDAS
            uWind = ancillary['10m_u_component_of_wind']['value']
            vWind = ancillary['10m_v_component_of_wind']['value']
            modWind.append(np.sqrt(uWind*uWind + vWind*vWind)) # direction not needed
            #ancAOD = aerGroup.getDataset("TOTEXTTAU")
            modAOD.append(ancillary['total_aerosol_optical_depth_550nm']['value'])
            modAirT.append(ancillary['2m_temperature']['value'] - 273.15) # [C]



        modData = HDFRoot()
        modGroup = modData.addGroup('ECMWF')
        modGroup.addDataset('Datetag')
        modGroup.addDataset('Timetag2')
        modGroup.addDataset('AOD')
        modGroup.addDataset('Wind')
        modGroup.addDataset('AirTemp')
        '''NOTE: This is an unconventional use of Dataset, i.e., overides object with .data and .column.
            Keeping for continuity of application'''
        modGroup.datasets['Datetag'] = latDate
        modGroup.datasets['Timetag2'] = latTime
        modGroup.datasets['AOD'] = modAOD
        modGroup.datasets['Wind'] = modWind
        modGroup.datasets['AirTemp'] = modAirT
        modGroup.attributes['Wind units'] = 'm s-1'
        modGroup.attributes['Air Temp. units'] = 'C'
        modGroup.attributes['AOD wavelength'] = '550 nm'
        print('GetAnc_ecmwf: Model data retrieved')

        return modData
