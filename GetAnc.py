
import os
import urllib.request as ur
# import base64
import numpy as np
from dataclasses import dataclass

from HDFRoot import HDFRoot
from HDFGroup import HDFGroup
from Utilities import Utilities

class GetAnc:    


    @staticmethod 
    def getAnc(inputGroup):
        
        username = "daurin"
        password = "EarthData2019"

        # create a password manager
        password_mgr = ur.HTTPPasswordMgrWithDefaultRealm()

        # Add the username and password.
        # If we knew the realm, we could use it instead of None.
        # top_level_url = "https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/"
        top_level_url = "https://urs.earthdata.nasa.gov"
        password_mgr.add_password(None, top_level_url, username, password)
        handler = ur.HTTPBasicAuthHandler(password_mgr)

        # create "opener" (OpenerDirector instance)
        opener = ur.build_opener(handler)

        # use the opener to fetch a URL
        opener.open("https://oceandata.sci.gsfc.nasa.gov/")

        # Install the opener.
        # Now all calls to urllib.request.urlopen use our opener.
        ur.install_opener(opener)


        # base64string = base64.b64encode(bytes('%s:%s' % (username, password),'ascii'))
        # request.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))
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
            hr = Utilities.timeTag2ToSec(latTime[index])/60/60               

            # file1 = f"{year}/{doy:03.0f}/N{year}{doy:03.0f}{hr:02.0f}_AER_MERRA2_1h.nc"
            file1 = f"N{year}{doy:03.0f}{hr:02.0f}_MERRA2_1h.nc"
            if oldFile != file1:
                # print(file1)
                filePath1 = os.path.join(cwd,"Data","Anc",file1)
                if not os.path.exists(filePath1):
                    # url = f"https://oceandata.sci.gsfc.nasa.gov/Ancillary/Meteorological/{file1}"
                    url = f"https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/{file1}"
                    # ur.urlretrieve(url, filePath1)                    
                    
                    msg = f'Retrieving anchillary file from server: {file1}'
                    print(msg)
                    Utilities.writeLogFile(msg) 
                    
                    filedata = ur.urlopen(url).read()
                    fo = open(filePath1, 'w')
                    print(filedata, file=fo)
                    fo.close()
                    pass
                else:
                    msg = f'Ancillary file found locally: {file1}'
                    print(msg)
                    Utilities.writeLogFile(msg) 


                file2 = f"N{year}{doy:03.0f}{hr:02.0f}_AER_MERRA2_1h.nc"
                # print(file2)
                filePath2 = os.path.join(cwd,"Data","Anc",file2)
                if not os.path.exists(filePath2):
                    # url = f"https://oceandata.sci.gsfc.nasa.gov/Ancillary/Meteorological/{file1}"
                    url = f"https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/{file2}"
                    ur.urlretrieve(url, filePath2)
                    msg = f'Retrieving anchillary file from server: {file2}'
                    print(msg)
                    Utilities.writeLogFile(msg) 
                else:
                    msg = f'Ancillary file found locally: {file2}'
                    print(msg)
                    Utilities.writeLogFile(msg) 

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

