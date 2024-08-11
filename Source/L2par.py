
from Source.ConfigFile import ConfigFile

class L2par():
    
    @staticmethod
    def L2par(root):
        ''' Use weighted MODIS Aqua bands to calculate photosynthetically available radiation in Einstein m^-2 d^-1'''

        Reflectance = root.getGroup("REFLECTANCE")

        # par
        if ConfigFile.products["bL2Prodpar"]:
            
            dateTime = Reflectance.datasets['Rrs_HYPER'].columns['Datetime']
            dateTag = Reflectance.datasets['Rrs_HYPER'].columns['Datetag']
            timeTag2 = Reflectance.datasets['Rrs_HYPER'].columns['Timetag2']

            prodGroup = root.getGroup('DERIVED_PRODUCTS')
            parDS = prodGroup.addDataset('par')
            prodGroup.attributes['par_UNITS'] = 'Einstein m^-2 d^-1'
            parDS.columns['Datetime'] = dateTime
            parDS.columns['Datetag'] = dateTag
            parDS.columns['Timetag2'] = timeTag2

            Rrs443 = Reflectance.datasets["Rrs_MODISA"].columns['443']     
            Rrs469 = Reflectance.datasets["Rrs_MODISA"].columns['469']
            Rrs555 = Reflectance.datasets["Rrs_MODISA"].columns['555']    

            # probably not practical
            par = []


            parDS.columns['par'] = par.tolist()
            parDS.columnsToDataset()

       