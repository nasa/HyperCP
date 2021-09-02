
import os
import stat
import urllib.request as ur
import requests
import platform
import numpy as np
from PyQt5 import QtWidgets
# from dataclasses import dataclass

from HDFRoot import HDFRoot
from HDFGroup import HDFGroup
from Utilities import Utilities
import OBPGSession

class GetAnc:    

    @staticmethod
    def userCreds(usr,pwd):
        home = os.path.expanduser('~')
        if platform.system() == 'Windows':    
            netrcFile = os.path.join(home,'_netrc')
        else: 
            netrcFile = os.path.join(home,'.netrc')
        if os.path.exists(netrcFile):
            os.chmod(netrcFile, stat.S_IRUSR | stat.S_IWUSR)
        if not os.path.exists(netrcFile):
            with open(netrcFile, 'w') as fo:
                fo.write(f'machine urs.earthdata.nasa.gov login {usr} password {pwd}\n')
            os.chmod(netrcFile, stat.S_IRUSR | stat.S_IWUSR)

        else:
            # print('netrc found')
            fo = open(netrcFile)
            lines = fo.readlines()
            fo.close()
            # This will find and replace or add the Earthdata server
            foundED = False
            for i, line in enumerate(lines):
                if 'machine urs.earthdata.nasa.gov login' in line:
                    foundED = True
                    lineIndx = i

            if foundED == True:
                lines[lineIndx] = f'machine urs.earthdata.nasa.gov login {usr} password {pwd}\n'
            else:
                lines = lines + [f'\nmachine urs.earthdata.nasa.gov login {usr} password {pwd}\n']

            # with open(netrcFile, "w") as fo:
            fo = open(netrcFile,"w")
            fo.writelines(lines)
            fo.close()

    @staticmethod 
    def getAnc(inputGroup):                        
        server = 'oceandata.sci.gsfc.nasa.gov'
        cwd = os.getcwd()        

        if not os.path.exists(os.path.join(cwd,"Data","Anc")):  
            os.makedirs(os.path.join(cwd,"Data","Anc")) 

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
         
            year = int(str(int(dateTag))[0:4])
            doy = int(str(int(dateTag))[4:7])
            # Casting below can push hr to 24. Truncate the hr decimal using
            # int() so the script always calls from within the hour in question, 
            # and no rounding occurs.
            hr = int(Utilities.timeTag2ToSec(latTime[index])/60/60)
            
                      

            file1 = f"N{year}{doy:03.0f}{hr:02.0f}_MERRA2_1h.nc"
            if oldFile != file1:
                ancPath = os.path.join(cwd,"Data","Anc")
                filePath1 = os.path.join(cwd,"Data","Anc",file1)
                if not os.path.exists(filePath1):
                    request = f"/cgi/getfile/{file1}"
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

                file2 = f"N{year}{doy:03.0f}{hr:02.0f}_AER_MERRA2_1h.nc"
                filePath2 = os.path.join(cwd,"Data","Anc",file2)
                if not os.path.exists(filePath2):
                    request = f"/cgi/getfile/{file2}"
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
                    alert = QtWidgets.QMessageBox()
                    alert.setText(f'Request error: {status}\n \
                                    Enter server credentials in the\n \
                                    Configuration Window L2 Preliminary')
                    alert.exec_() 
                    return None

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

                # extract and return ancillary data from netcdf4 files....
                ancLatAer = np.array(aerGroup.getDataset("lat").data.tolist())
                ancLonAer = np.array(aerGroup.getDataset("lon").data.tolist())

                # Total Aerosol Extinction AOT 550 nm, same as AOD(550)
                ancTExt = aerGroup.getDataset("TOTEXTTAU")

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
        modGroup.datasets['Datetag'] = latDate
        modGroup.datasets['Timetag2'] = latTime
        modGroup.datasets['AOD'] = modAOD
        modGroup.datasets['Wind'] = modWind
        print('GetAnc: Model data retrieved')
        
        return modData

