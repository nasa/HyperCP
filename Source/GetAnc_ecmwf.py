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
from Source.GetAnc_credentials import read_user_credentials

class GetAnc_ecmwf:

    def timeStamp2yrMnthDayHrMinSec(timestamp):
        '''
        Definition for timestamp managing
        :param timeStamp: a string, the time in UTC with format yyyy-mm-ddThh:MM:ss
        '''
        date = timestamp.split('T')[0]
        time = timestamp.split('T')[1]

        year = date.split('-')[0]
        month = date.split('-')[1]
        day = date.split('-')[2]

        hour = time.split(':')[0]
        minute = time.split(':')[1]
        second = time.split(':')[2]

        return year,month,day,hour,minute,second

    def ECMWF_latLonTimeTags(lat, lon, timeStamp, latRes, lonRes, timeResHours):
        '''
        :param timeStamp: a string, the time in UTC with format yyyy-mm-ddThh:MM:ss
        :param lat: a float, the query latitude in degrees North
        :param lon: a float, the query longitude in degrees East
        :return:
        latEff: a float, the effective latitude - i.e. to the closest resolution degree
        lonEff: a float, the effective latitude - i.e. to the closest resolution degree
        latLonTag: a string, a tag to indicate the effective lat/lon.
        dateTag: a string, a tag to indicate time stamp, to the hour
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

        # Time; choose 00:00 or 12:00 model
        year, month, day, hour, minute, second = GetAnc_ecmwf.timeStamp2yrMnthDayHrMinSec(timeStamp)
        dTtimeStamp = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second),tzinfo=datetime.timezone.utc)
        dTtimeVec = [datetime.datetime(int(year), int(month), int(day), int(0), int(0), int(0),tzinfo=datetime.timezone.utc),\
                     datetime.datetime(int(year), int(month), int(day), int(12), int(0), int(0),tzinfo=datetime.timezone.utc)]
        timeEff = min(dTtimeVec, key=lambda x: abs(x - dTtimeStamp))

        # timeSec = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second),tzinfo=datetime.timezone.utc).timestamp()
        # timeEffSec = np.round(timeSec / (3600 * timeResHours)) * (3600 * timeResHours) - 7200
        # timeStampEff = str(pd.Timestamp(datetime.datetime.fromtimestamp(timeEffSec))).replace(' ','T')
        timeStampEff = str(pd.Timestamp(timeEff)).replace(' ','T')

        dateTag = timeStampEff.replace(':','').replace('-','').replace('T','')
        # print(timeStamp)
        # print(year, month, day, hour, minute, second)
        # print(timeSec)
        # print(timeEffSec)
        # print(timeStampEff)

        return latEff,lonEff,timeStampEff,latLonTag,dateTag


    def EAC4_download_ensembles(lat, lon, timeStamp, EAC4_variables, pathOut):
        '''
        Performs CDSAPI command to download the required data from EAC4 (dataset "cams-global-atmospheric-composition-forecasts") in netCDF
        format. It will retrieve the variables in a single space-time point corresponding to

        For more information, please check: https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-atmospheric-composition-forecasts?tab=overview

        :param timeStamp: a string, the time in UTC with format yyyy-mm-ddThh:MM:ss,
        :param lat: a float, the query latitude in degrees North
        :param lon: a float, the query longitude in degrees East

        :param EAC4_variables: a list, with the variables of interest
        :param pathOut: full path to output, a netCDF file with the requested variables.
        :return:
        '''

        if os.path.exists(pathOut):
            pass
        else:
            print(f'Nearest model found at {timeStamp}')
            url,key = read_user_credentials('ECMWF_ADS')

            year, month, day, hour, _, _ = GetAnc_ecmwf.timeStamp2yrMnthDayHrMinSec(timeStamp)

            if int(year) < 2003:
                print('EAC4 dataset not available before 2003, skipping')
            else:
                try:
                    c = cdsapi.Client(timeout=5, url=url, key=key)
                    c.retrieve(
                        'cams-global-atmospheric-composition-forecasts',
                        {
                            'format': 'netcdf',
                            'type' : 'forecast',
                            'variable': list(EAC4_variables.keys()),
                            'date': '%s-%s-%s/%s-%s-%s' % (year, month, day, year, month, day),
                            'time': '%s:00' % (hour,),
                            'area': [lat, lon, lat, lon],
                            'leadtime_hour': '0',
                        },
                        pathOut)
                except:
                    print('EAC4 atmospheric data could not be retrieved. Check inputs.')
                    exit()


    def get_ancillary_main(lat, lon, timeStamp, pathAncillary):
        '''
        Retrieves ancillary
        :param lat: a float, the query latitude in degrees North
        :param lon: a float, the query longitude in degrees East
        :param timeStamp: a string, the time in UTC with format yyyy-mm-ddThh:MM:ss
        :param pathAncillary:a string, /full/path/to/where_you_wish_to_store_the_ECMWF_netcdfs
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

        #################### EAC4 ####################
        pathEAC4 = pathAncillary
        if not os.path.exists(pathEAC4):
            os.mkdir(pathEAC4)

        EAC4_variables = {
        '10m_u_component_of_wind' :'u10',
        '10m_v_component_of_wind' :'v10',
        'total_aerosol_optical_depth_550nm' :'aod550'
        }

        EAC4nc = {}


        # Check https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-atmospheric-composition-forecasts?tab=overview
        latRes = 0.4
        lonRes = 0.4
        timeResHours = 12

        latEff, lonEff, timeStampEff, latLonTag, dateTag = GetAnc_ecmwf.ECMWF_latLonTimeTags(lat, lon, timeStamp, latRes, lonRes, timeResHours)

        pathOut = os.path.join(pathEAC4, 'EAC4_%s_%s.nc' % (latLonTag, dateTag))

        GetAnc_ecmwf.EAC4_download_ensembles(latEff, lonEff, timeStampEff, EAC4_variables, pathOut)

        try:
            EAC4nc['reanalysis'] = xr.open_dataset(pathOut,engine='netcdf4')
            EAC4_flag = True
        except:
            EAC4_flag = False
            print('EAC4 data missing. Skipping...')

        if EAC4_flag:
            try:
                for EAC4_variable, shortName in EAC4_variables.items():
                    var = EAC4nc['reanalysis'][shortName]
                    ancillary[EAC4_variable] = {}
                    ancillary[EAC4_variable]['value']      = var.values[0][0][0]
                    ancillary[EAC4_variable]['units']      = var.units
                    ancillary[EAC4_variable]['long_name']  = var.long_name
                    ancillary[EAC4_variable]['source']     = 'EAC4 (ECMWF). https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-atmospheric-composition-forecasts?tab=overview'
            except:
                print('Problem processing EAC4 data. Skipping...')

        return ancillary


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
        modAOD = []

        # Loop through the input group and extract model data for each element
        for index, dateTag in enumerate(latDate):
            dateTagNew = Utilities.dateTagToDateTime(dateTag)
            lat_datetime = str(Utilities.timeTag2ToDateTime(dateTagNew,latTime[index])).split('.')[0]
            lat_timeStamp = lat_datetime.replace(' ','T')
            lat_timeStamp = lat_timeStamp.replace('+',':')

            ancillary = GetAnc_ecmwf.get_ancillary_main(lat[index], lon[index], lat_timeStamp, ancPath)

            # position retrieval index has been confirmed manually in SeaDAS
            uWind = ancillary['10m_u_component_of_wind']['value'][0]
            vWind = ancillary['10m_v_component_of_wind']['value'][0]
            modWind.append(np.sqrt(uWind*uWind + vWind*vWind)) # direction not needed
            #ancAOD = aerGroup.getDataset("TOTEXTTAU")
            modAOD.append(ancillary['total_aerosol_optical_depth_550nm']['value'][0])

        modData = HDFRoot()
        modGroup = modData.addGroup('ECMWF')
        modGroup.addDataset('Datetag')
        modGroup.addDataset('Timetag2')
        modGroup.addDataset('AOD')
        modGroup.addDataset('Wind')
        '''NOTE: This is an unconventional use of Dataset, i.e., overides object with .data and .column.
            Keeping for continuity of application'''
        modGroup.datasets['Datetag'] = latDate
        modGroup.datasets['Timetag2'] = latTime
        modGroup.datasets['AOD'] = modAOD
        modGroup.datasets['Wind'] = modWind
        modGroup.attributes['Wind units'] = 'm s-1'
        modGroup.attributes['AOD wavelength'] = '550 nm'
        print('GetAnc_ecmwf: Model data retrieved')

        return modData

