
import os
import urllib.request as ur

from HDFRoot import HDFRoot
from HDFGroup import HDFGroup

class GetAnc:

    @staticmethod 
    def getAnc(lat,lon,year,doy,hr):

        if not os.path.exists("./Data/Anc/"):  
           os.makedirs("./Data/Anc/") 

        # file1 = f"{year}/{doy:03.0f}/N{year}{doy:03.0f}{hr:02.0f}_AER_MERRA2_1h.nc"
        file1 = f"N{year}{doy:03.0f}{hr:02.0f}_AER_MERRA2_1h.nc"
        print(file1)
        filePath = f"./Data/Anc/{file1}"
        if not os.path.exists(filePath):
            # url = f"https://oceandata.sci.gsfc.nasa.gov/Ancillary/Meteorological/{file1}"
            url = f"https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/{file1}"
            ur.urlretrieve(url, filePath)
        else:
            print("Ancillary file found on disk.")

        node = HDFRoot.readHDF5(filePath)
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
        ancLat = aerGroup.getDataset("lat").data
        AOD = 0.01
        modWind = 5
        return AOD, modWind

