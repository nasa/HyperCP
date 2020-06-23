
import numpy as np

from ConfigFile import ConfigFile
from Utilities import Utilities

class L2qaa():
    
    @staticmethod
    def L2qaa(root):
        ''' Use weighted MODIS Aqua bands to calculate IOPs using
            QAA_v6 '''

        # Adjustable empirical coefficient set-up. Many coefficients remain hard
        #   coded as in SeaDAS qaa.c

        # Step 1
        g0 = 0.08945
        g1 = 0.1247
        # Step 2
        h0 = -1.146
        h1 = -1.366
        h2 = -0.469
        # Step 8
        S = 0.015

        # Pure water. Historically used Pope & Fry adjusted for S&T using Sullivan et al. 2006.
        # Now considering using inverted values from Lee et al. 2015
        aw = []
                

        Reflectance = root.getGroup("REFLECTANCE")
        
        dateTime = Reflectance.datasets['Rrs_HYPER'].columns['Datetime']
        dateTag = Reflectance.datasets['Rrs_HYPER'].columns['Datetag']
        timeTag2 = Reflectance.datasets['Rrs_HYPER'].columns['Timetag2']

        prodGroup = root.getGroup('DERIVED_PRODUCTS')
        if ConfigFile.products["bL2ProdaQaa"]:
            prodGroup.attributes['a_UNITS'] = '1/m'
            aDS = prodGroup.addDataset('a')
            aDS.columns['Datetime'] = dateTime
            aDS.columns['Datetag'] = dateTag
            aDS.columns['Timetag2'] = timeTag2
        if ConfigFile.products["bL2ProdadgQaa"]:
            prodGroup.attributes['adg_UNITS'] = '1/m'
            adgDS = prodGroup.addDataset('adg')
            adgDS.columns['Datetime'] = dateTime
            adgDS.columns['Datetag'] = dateTag
            adgDS.columns['Timetag2'] = timeTag2
        if ConfigFile.products["bL2ProdaphQaa"]:
            prodGroup.attributes['aph_UNITS'] = '1/m'
            aphDS = prodGroup.addDataset('aph')
            aphDS.columns['Datetime'] = dateTime
            aphDS.columns['Datetag'] = dateTag
            aphDS.columns['Timetag2'] = timeTag2
        if ConfigFile.products["bL2ProdbQaa"]:
            prodGroup.attributes['b_UNITS'] = '1/m'
            abDS = prodGroup.addDataset('b')
            abDS.columns['Datetime'] = dateTime
            abDS.columns['Datetag'] = dateTag
            abDS.columns['Timetag2'] = timeTag2            
        if ConfigFile.products["bL2ProdbbQaa"]:
            prodGroup.attributes['bb_UNITS'] = '1/m'
            abbDS = prodGroup.addDataset('bb')
            abbDS.columns['Datetime'] = dateTime
            abbDS.columns['Datetag'] = dateTag
            abbDS.columns['Timetag2'] = timeTag2            
        if ConfigFile.products["bL2ProdbbpQaa"]:
            prodGroup.attributes['bbp_UNITS'] = '1/m'
            abbpDS = prodGroup.addDataset('bbp')
            abbpDS.columns['Datetime'] = dateTime
            abbpDS.columns['Datetag'] = dateTag
            abbpDS.columns['Timetag2'] = timeTag2            
        if ConfigFile.products["bL2ProdcQaa"]:
            prodGroup.attributes['c_UNITS'] = '1/m'
            acDS = prodGroup.addDataset('c')
            acDS.columns['Datetime'] = dateTime
            acDS.columns['Datetag'] = dateTag
            acDS.columns['Timetag2'] = timeTag2            

        Rrs443 = Reflectance.datasets["Rrs_MODISA"].columns['443']
        Rrs488 = Reflectance.datasets["Rrs_MODISA"].columns['488'] # assumed equivalent to 490
        # Rrs547 = Reflectance.datasets["Rrs_MODISA"].columns['551'] # 551 in name only
        Rrs555 = Reflectance.datasets["Rrs_MODISA"].columns['555']
        Rrs667 = Reflectance.datasets["Rrs_MODISA"].columns['667'].copy() # assumed equivalent to 670

        # For fun, let's apply it to the full hyperspectral dataset
        Rrs_ds = Reflectance.datasets["Rrs_HYPER"]
        keys = list(Rrs_ds.columns.keys())
        values = list(Rrs_ds.columns.values())
        waveStr = keys[3:]
        Rrs = np.array(values[3:])
 

        # Pretest on Rrs(670)
        for n in range(0, len(dateTime)):
            
            # Pretest on Rrs(670) from QAAv5
            if Rrs667[n] > 20 * np.power(Rrs555[n], 1.5) or \
                Rrs667[n] < 0.9 * np.power(Rrs555[n], 1.7):

                msg = "L2qaa: Rrs(667) out of bounds, adjusting."
                print(msg)
                Utilities.writeLogFile(msg)  

                Rrs667[n] = 1.27 * np.power(Rrs555[n], 1.47) + 0.00018 * np.power(Rrs488[n]/Rrs555[n], -3.19)


            # Step 0        
            rrs = Rrs[n] / (0.52 + 1.7 * Rrs[n])
            rrs443 = Rrs443[n] / (0.52 + 1.7 * Rrs443[n])
            rrs488 = Rrs488[n] / (0.52 + 1.7 * Rrs488[n])
            rrs555 = Rrs555[n] / (0.52 + 1.7 * Rrs555[n])
            rrs667 = Rrs667[n] / (0.52 + 1.7 * Rrs667[n])

            # Step 1
            u = (np.sqrt(g0*g0 + 4.0 * g1 * rrs) - g0) / (2.0 * g1)

            # Switch, Step 2
            if Rrs667 < 0.0015:
                chi = np.log10( (rrs443 + rrs488) / (rrs555 + 5 * rrs667/rrs488 * rrs667) )
                a0 = aw0 + np.power(10.0, (h0 + h1*chi + h2*chi*chi))

            else:


                a = []
        
        
        aDS.columns['qaa'] = a
        aDS.columnsToDataset()

    