
import numpy as np
from ConfigFile import ConfigFile

class L2qaa():
    
    @staticmethod
    def L2qaa(root):
        ''' Use weighted MODIS Aqua bands to calculate IOPs using
            QAA_v6 '''

        Reflectance = root.getGroup("REFLECTANCE")
        
        dateTime = Reflectance.datasets['Rrs_HYPER'].columns['Datetime']
        dateTag = Reflectance.datasets['Rrs_HYPER'].columns['Datetag']
        timeTag2 = Reflectance.datasets['Rrs_HYPER'].columns['Timetag2']

        prodGroup = root.getGroup('DERIVED_PRODUCTS')
        if ConfigFile.products["bL2aQaa"]:
            prodGroup.attributes['a_UNITS'] = '1/m'
            aDS = prodGroup.addDataset('a')
            aDS.columns['Datetime'] = dateTime
            aDS.columns['Datetag'] = dateTag
            aDS.columns['Timetag2'] = timeTag2
        if ConfigFile.products["bL2adgQaa"]:
            prodGroup.attributes['adg_UNITS'] = '1/m'
            adgDS = prodGroup.addDataset('adg')
            adgDS.columns['Datetime'] = dateTime
            adgDS.columns['Datetag'] = dateTag
            adgDS.columns['Timetag2'] = timeTag2
        if ConfigFile.products["bL2aphQaa"]:
            prodGroup.attributes['aph_UNITS'] = '1/m'
            aphDS = prodGroup.addDataset('aph')
            aphDS.columns['Datetime'] = dateTime
            aphDS.columns['Datetag'] = dateTag
            aphDS.columns['Timetag2'] = timeTag2
        if ConfigFile.products["bL2bQaa"]:
            prodGroup.attributes['b_UNITS'] = '1/m'
            abDS = prodGroup.addDataset('b')
            abDS.columns['Datetime'] = dateTime
            abDS.columns['Datetag'] = dateTag
            abDS.columns['Timetag2'] = timeTag2            
        if ConfigFile.products["bbL2aQaa"]:
            prodGroup.attributes['bb_UNITS'] = '1/m'
            abbDS = prodGroup.addDataset('bb')
            abbDS.columns['Datetime'] = dateTime
            abbDS.columns['Datetag'] = dateTag
            abbDS.columns['Timetag2'] = timeTag2            
        if ConfigFile.products["bL2bbpQaa"]:
            prodGroup.attributes['bbp_UNITS'] = '1/m'
            abbpDS = prodGroup.addDataset('bbp')
            abbpDS.columns['Datetime'] = dateTime
            abbpDS.columns['Datetag'] = dateTag
            abbpDS.columns['Timetag2'] = timeTag2            
        if ConfigFile.products["bL2cQaa"]:
            prodGroup.attributes['c_UNITS'] = '1/m'
            acDS = prodGroup.addDataset('c')
            acDS.columns['Datetime'] = dateTime
            acDS.columns['Datetag'] = dateTag
            acDS.columns['Timetag2'] = timeTag2            

        Rrs443 = Reflectance.datasets["Rrs_MODISA"].columns['443']
        Rrs488 = Reflectance.datasets["Rrs_MODISA"].columns['488']
        Rrs547 = Reflectance.datasets["Rrs_MODISA"].columns['551'] # 551 in name only
        Rrs555 = Reflectance.datasets["Rrs_MODISA"].columns['555']
        Rrs667 = Reflectance.datasets["Rrs_MODISA"].columns['667']


        
        aDS.columns['qaa'] = qaa
        aDS.columnsToDataset()

    