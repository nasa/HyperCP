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

    def ECMWF_latLonTimeTags(lat, lon, timeStamp, latRes, lonRes, timeResHours):
        '''
        :param timeStamp: a string, the time in UTC with format yyyy-mm-ddThh:MM:ss
        :param lat: a float, the query latitude in degrees North
        :param lon: a float, the query longitude in degrees East
        :param timeResHours: an integer, time resolution of the queried ECMWF dataset
        :return:
        latEff: a float, the effective latitude - i.e. to the closest resolution degree
        lonEff: a float, the effective latitude - i.e. to the closest resolution degree
        latLonTag: a string, a tag to indicate the effective lat/lon.
        dateTagEff: a string, a tag to indicate effective date (i.e. date in UTC rounded to closest hour)
        timeStampEff: a string, a tag to indicate effective time (i.e. time in UTC rounded to closest hour)
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

        # Convert to a datetime object
        epoch_time = datetime.datetime.strptime(':'.join(timeStamp.split(':')[:-2]), '%Y-%m-%dT%H:%M:%S').timestamp()
        timeResHoursSecs = 3600 * timeResHours
        rounded_epoch_time = round(epoch_time / timeResHoursSecs) * timeResHoursSecs
        rounded_timestamp = datetime.datetime.fromtimestamp(rounded_epoch_time).strftime('%Y-%m-%dT%H:%M:%S')
        dateTagEff, timeStampEff = rounded_timestamp.split('T')

        return latEff,lonEff,latLonTag,dateTagEff,timeStampEff


    def CAMS_download_ensembles(lat, lon, dateTag, timeTag, CAMS_variables, pathOut):
        '''
        Performs CDSAPI command to download the required data from CAMS (dataset "cams-global-atmospheric-composition-forecasts") in netCDF
        format. It will retrieve the variables in a single space-time point corresponding to

        For more information, please check: https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-atmospheric-composition-forecasts?tab=overview

        :param timeStamp: a string, the time in UTC with format yyyy-mm-ddThh:MM:ss,
        :param lat: a float, the query latitude in degrees North
        :param lon: a float, the query longitude in degrees East

        :param CAMS_variables: a list, with the variables of interest
        :param pathOut: full path to output, a netCDF file with the requested variables.
        :return:
        '''

        if os.path.exists(pathOut):
            pass
        else:
            url,key = read_user_credentials('ECMWF_ADS')

            year = dateTag.split('-')[0]
            hour = timeTag.split(':')[0]

            hourForecast = '%02d' % (int(hour) // 12)
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
                            'date': '%s/%s' % (dateTag, dateTag),
                            'area': [lat, lon, lat, lon],
                            'time': '%s:00' % hourForecast,
                            'leadtime_hour': leadtime,
                            'format': 'netcdf',
                            'download_format': 'unarchived',
                        },
                        pathOut)
                except:
                    print('CAMS atmospheric data could not be retrieved. Check inputs.')
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

        #################### CAMS ####################
        pathCAMS = pathAncillary
        if not os.path.exists(pathCAMS):
            os.mkdir(pathCAMS)

        CAMS_variables = {
        '10m_u_component_of_wind' :'u10',
        '10m_v_component_of_wind' :'v10',
        'total_aerosol_optical_depth_550nm' :'aod550'
        }

        CAMSnc = {}


        # Check https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-atmospheric-composition-forecasts?tab=overview
        latRes = 0.4
        lonRes = 0.4
        timeResHours = 1

        latEff, lonEff, latLonTag, dateTagEff, timeStampEff = GetAnc_ecmwf.ECMWF_latLonTimeTags(lat, lon, timeStamp, latRes, lonRes, timeResHours)

        pathOut = os.path.join(pathCAMS, 'CAMS_%s_%s_%s.nc' % (latLonTag, dateTagEff.replace('-',''), timeStampEff.replace(':','')))

        GetAnc_ecmwf.CAMS_download_ensembles(latEff, lonEff, dateTagEff, timeStampEff, CAMS_variables, pathOut)

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
            uWind = ancillary['10m_u_component_of_wind']['value']
            vWind = ancillary['10m_v_component_of_wind']['value']
            modWind.append(np.sqrt(uWind*uWind + vWind*vWind)) # direction not needed
            #ancAOD = aerGroup.getDataset("TOTEXTTAU")
            modAOD.append(ancillary['total_aerosol_optical_depth_550nm']['value'])

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

