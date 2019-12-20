
import os
import urllib.request as ur
import numpy as np

from HDFRoot import HDFRoot
from HDFGroup import HDFGroup
from Utilities import Utilities

class GetAnc:

    @staticmethod 
    def getAnc(lat,lon,year,doy,hr):

        if not os.path.exists("./Data/Anc/"):  
           os.makedirs("./Data/Anc/") 

        # file1 = f"{year}/{doy:03.0f}/N{year}{doy:03.0f}{hr:02.0f}_AER_MERRA2_1h.nc"
        file1 = f"N{year}{doy:03.0f}{hr:02.0f}_MERRA2_1h.nc"
        print(file1)
        filePath1 = f"./Data/Anc/{file1}"
        if not os.path.exists(filePath1):
            # url = f"https://oceandata.sci.gsfc.nasa.gov/Ancillary/Meteorological/{file1}"
            url = f"https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/{file1}"
            ur.urlretrieve(url, filePath1)
        else:
            print("Ancillary file found on disk.")

        file2 = f"N{year}{doy:03.0f}{hr:02.0f}_AER_MERRA2_1h.nc"
        print(file2)
        filePath2 = f"./Data/Anc/{file2}"
        if not os.path.exists(filePath2):
            # url = f"https://oceandata.sci.gsfc.nasa.gov/Ancillary/Meteorological/{file1}"
            url = f"https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/{file2}"
            ur.urlretrieve(url, filePath2)
        else:
            print("Ancillary file found on disk.")

        
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

        # Locate the relevant cell
        latInd = Utilities.find_nearest(ancLat,lat)
        lonInd = Utilities.find_nearest(ancLon,lon)
        
        # position confirmed in SeaDAS
        uWind = ancUwind.data["None"][latInd][lonInd]
        vWind = ancVwind.data["None"][latInd][lonInd]
        modWind = np.sqrt(uWind*uWind + vWind*vWind) # direction not needed


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
        ancLat = np.array(aerGroup.getDataset("lat").data.tolist())
        ancLon = np.array(aerGroup.getDataset("lon").data.tolist())

        # Total Aerosol Extinction AOT 550 nm, same as AOD(550)
        ancTExt = aerGroup.getDataset("TOTEXTTAU")

        # Locate the relevant cell
        latInd = Utilities.find_nearest(ancLat,lat)
        lonInd = Utilities.find_nearest(ancLon,lon)
        
        # position confirmed in SeaDAS
        AOD = ancTExt.data["None"][latInd][lonInd]

        return AOD, modWind

