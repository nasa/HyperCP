
import numpy as np
from ConfigFile import ConfigFile

class L2pic():
    
    @staticmethod
    def L2pic(root):
        ''' Use weighted MODIS Aqua bands to calculate particulate inorganic carbon  in mol m^-3 '''

        Reflectance = root.getGroup("REFLECTANCE")
        
        dateTime = Reflectance.datasets['Rrs_HYPER'].columns['Datetime']
        dateTag = Reflectance.datasets['Rrs_HYPER'].columns['Datetag']
        timeTag2 = Reflectance.datasets['Rrs_HYPER'].columns['Timetag2']

        prodGroup = root.getGroup('DERIVED_PRODUCTS')
        picDS = prodGroup.addDataset('pic')
        prodGroup.attributes['pic_UNITS'] = 'mol m^-3'
        picDS.columns['Datetime'] = dateTime
        picDS.columns['Datetag'] = dateTag
        picDS.columns['Timetag2'] = timeTag2

        Rrs443 = Reflectance.datasets["Rrs_MODISA"].columns['443']            
        Rrs555 = Reflectance.datasets["Rrs_MODISA"].columns['555']            
        Rrs667 = Reflectance.datasets["Rrs_MODISA"].columns['667']
        Rrs748 = Reflectance.datasets["Rrs_MODISA"].columns['748']
        Rrs869 = Reflectance.datasets["Rrs_MODISA"].columns['869']

        # 2-band approach
        # Requires a LUT

        # 3- band approach
        # Requires iteration
        pic = []

        picDS.columns['pic'] = pic.tolist()
        picDS.columnsToDataset()

       