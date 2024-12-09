import os


import stat
# import urllib.request as ur
# import requests
import platform
import numpy as np
from PyQt5 import QtWidgets

from Source.HDFRoot import HDFRoot
from Source.Utilities import Utilities
from Source import OBPGSession, PATH_TO_DATA


class GetAnc:

    @staticmethod
    def getAnc(inputGroup):
        ''' Retrieve model data and save in Data/Anc and in ModData '''
        server = 'oceandata.sci.gsfc.nasa.gov'
        # cwd = os.getcwd()

        if not os.path.exists(os.path.join(PATH_TO_DATA, 'Anc')):
            os.makedirs(os.path.join(PATH_TO_DATA, 'Anc'))

        # Get the dates, times, and locations from the input group
        latDate = inputGroup.getDataset('LATITUDE').data["Datetag"]
        latTime = inputGroup.getDataset('LATITUDE').data["Timetag2"]
        lat = inputGroup.getDataset('LATITUDE').data["NONE"]
        lon = inputGroup.getDataset('LONGITUDE').data["NONE"]

        modWind = []
        modAOD = []

        # Loop through the input group and extract model data for each element
        oldFile = None
        for index, dateTag in enumerate(latDate):
            dateTagNew = Utilities.dateTagToDate(dateTag)
            year = int(str(int(dateTagNew))[0:4])
            month = int(str(int(dateTagNew))[4:6])
            day = int(str(int(dateTagNew))[6:8])
            # doy = int(str(int(dateTag))[4:7])
            # Casting below can push hr to 24. Truncate the hr decimal using
            # int() so the script always calls from within the hour in question,
            # and no rounding occurs.
            hr = int(Utilities.timeTag2ToSec(latTime[index])/60/60)

            file1 = f"GMAO_MERRA2.{year}{month:02.0f}{day:02.0f}T{hr:02.0f}0000.MET.nc"
            if oldFile != file1:
                ancPath = os.path.join(PATH_TO_DATA, 'Anc')
                filePath1 = os.path.join(PATH_TO_DATA, 'Anc', file1)
                if not os.path.exists(filePath1):
                    # request = f"/cgi/getfile/{file1}"
                    request = f"/ob/getfile/{file1}"
                    msg = f'Retrieving anchillary file from server: {file1}'
                    print(msg)
                    Utilities.writeLogFile(msg)

                    status = OBPGSession.httpdl(server, request, localpath=ancPath,
                        outputfilename=file1, uncompress=False, verbose=2)
                else:
                    status = 200
                    msg = f'Ancillary file found locally: {file1}'
                    print(msg)
                    Utilities.writeLogFile(msg)

                file2 = f"GMAO_MERRA2.{year}{month:02.0f}{day:02.0f}T{hr:02.0f}0000.AER.nc"
                filePath2 = os.path.join(PATH_TO_DATA, 'Anc', file2)
                if not os.path.exists(filePath2):
                    # request = f"/cgi/getfile/{file2}"
                    request = f"/ob/getfile/{file2}"
                    msg = f'Retrieving anchillary file from server: {file2}'
                    print(msg)
                    Utilities.writeLogFile(msg)

                    status = OBPGSession.httpdl(server, request, localpath=ancPath,
                        outputfilename=file2, uncompress=False, verbose=2)
                else:
                    status = 200
                    msg = f'Ancillary file found locally: {file2}'
                    print(msg)
                    Utilities.writeLogFile(msg)

                if status in (400, 401, 403, 404, 416):
                    msg = f'Request error: {status}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    if os.environ["HYPERINSPACE_CMD"].lower() == 'true':
                        return
                    alert = QtWidgets.QMessageBox()
                    alert.setText(f'Request error: {status}\n \
                                    Check that server credentials have \n \
                                    been entered in Configuration Window L1B. \n  \
                                    MERRA2 model data are not available until \n \
                                    the third week of the following month.')
                    alert.exec_()
                    return

                # GMAO Atmospheric model data
                node = HDFRoot.readHDF5(filePath1)
                root = HDFRoot()
                root.copyAttributes(node)

                # dataset are read into root level
                gmaoGroup = root.addGroup('GMAO')
                for ds in node.datasets:
                    name = ds.id
                    newds = gmaoGroup.addDataset(name)
                    newds.columns["None"] = ds.data[:].tolist()
                    newds.columnsToDataset()
                    newds.attributes['units'] = ds.attributes['units']

                # extract and return ancillary data from netcdf4 files....
                ancLat = np.array(gmaoGroup.getDataset("lat").data.tolist())
                ancLon = np.array(gmaoGroup.getDataset("lon").data.tolist())

                # Humidity
                # not needed

                # Wind
                ancUwind = gmaoGroup.getDataset("U10M") # Eastward at 10m [m/s]
                ancVwind = gmaoGroup.getDataset("V10M") # Northward

                # Aerosols
                node = HDFRoot.readHDF5(filePath2)
                root = HDFRoot()
                root.copyAttributes(node)

                # dataset are read into root level
                aerGroup = root.addGroup('AEROSOLS')
                for ds in node.datasets:
                    name = ds.id
                    newds = aerGroup.addDataset(name)
                    newds.columns["None"] = ds.data[:].tolist()
                    newds.columnsToDataset()
                    newds.attributes['units'] = ds.attributes['units']


                # extract and return ancillary data from netcdf4 files....
                ancLatAer = np.array(aerGroup.getDataset("lat").data.tolist())
                ancLonAer = np.array(aerGroup.getDataset("lon").data.tolist())

                # Total Aerosol Extinction AOT 550 nm, same as AOD(550)
                ancTExt = aerGroup.getDataset("TOTEXTTAU")
                ancTExt.attributes['wavelength'] = '550 nm'

            oldFile = file1

            # Locate the relevant cell
            latInd = Utilities.find_nearest(ancLat,lat[index])
            lonInd = Utilities.find_nearest(ancLon,lon[index])

            # position retrieval index has been confirmed manually in SeaDAS
            uWind = ancUwind.data["None"][latInd][lonInd]
            vWind = ancVwind.data["None"][latInd][lonInd]
            modWind.append(np.sqrt(uWind*uWind + vWind*vWind)) # direction not needed

            # Locate the relevant cell
            latInd = Utilities.find_nearest(ancLatAer,lat[index])
            lonInd = Utilities.find_nearest(ancLonAer,lon[index])

            # position confirmed in SeaDAS
            modAOD.append(ancTExt.data["None"][latInd][lonInd])

        modData = HDFRoot()
        modGroup = modData.addGroup('MERRA2_model')
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
        modGroup.attributes['Wind units'] = ancUwind.attributes['units']
        modGroup.attributes['AOD wavelength'] = ancTExt.attributes['wavelength']
        print('GetAnc: Model data retrieved')

        return modData
