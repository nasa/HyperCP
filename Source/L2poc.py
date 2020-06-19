
import numpy as np

class L2poc():
    
    @staticmethod
    def L2poc(root):
        ''' Use weighted MODIS Aqua bands to calculate particulate organic carbon  in mg m^-3 '''

        Reflectance = root.getGroup("REFLECTANCE")
        
        dateTime = Reflectance.datasets['Rrs_HYPER'].columns['Datetime']
        dateTag = Reflectance.datasets['Rrs_HYPER'].columns['Datetag']
        timeTag2 = Reflectance.datasets['Rrs_HYPER'].columns['Timetag2']

        prodGroup = root.getGroup('DERIVED_PRODUCTS')
        pocDS = prodGroup.addDataset('poc')
        prodGroup.attributes['poc_UNITS'] = 'mg m^-3'
        pocDS.columns['Datetime'] = dateTime
        pocDS.columns['Datetag'] = dateTag
        pocDS.columns['Timetag2'] = timeTag2

        Rrs443 = np.array(Reflectance.datasets["Rrs_MODISA"].columns['443'])
        # Rrs547 = Reflectance.datasets["Rrs_MODISA"].columns['551'] # 551 in name only       
        Rrs555 = np.array(Reflectance.datasets["Rrs_MODISA"].columns['555'])

        a = 203.2
        b = -1.034

        poc = a * (Rrs443/Rrs555)**b     

        pocDS.columns['poc'] = poc.tolist()
        pocDS.columnsToDataset()