
import numpy as np

class L2chlor_a():
    
    @staticmethod
    def L2chlor_a(root):
        ''' Use weighted MODIS Aqua bands to calculate chlorophyll concentration
        using oc3m blended algorithm with CI (Hu et al. 2012) '''

        Reflectance = root.getGroup("REFLECTANCE")
        
        dateTime = Reflectance.datasets['Rrs_HYPER'].columns['Datetime']
        dateTag = Reflectance.datasets['Rrs_HYPER'].columns['Datetag']
        timeTag2 = Reflectance.datasets['Rrs_HYPER'].columns['Timetag2']

        prodGroup = root.getGroup('DERIVED_PRODUCTS')
        prodGroup.attributes['chlor_a_UNITS'] = 'mg m^-3'
        chlDS = prodGroup.addDataset('chlor_a')
        chlDS.columns['Datetime'] = dateTime
        chlDS.columns['Datetag'] = dateTag
        chlDS.columns['Timetag2'] = timeTag2

        Rrs443 = Reflectance.datasets["Rrs_MODISA"].columns['443']
        Rrs488 = Reflectance.datasets["Rrs_MODISA"].columns['488']
        Rrs547 = Reflectance.datasets["Rrs_MODISA"].columns['551'] # 551 in name only
        Rrs555 = Reflectance.datasets["Rrs_MODISA"].columns['555']
        Rrs667 = Reflectance.datasets["Rrs_MODISA"].columns['667']


        thresh = [0.15, 0.20]
        a0 = 0.2424
        a1 = -2.7423
        a2 = 1.8017
        a3 = 0.0015
        a4 = -1.2280

        ci1 = -0.4909
        ci2 = 191.6590

        # Given the blue channel selection, looping is simpler than array-wise
        chlor_a = [] #np.empty((0,len(Rrs443)))
        for i in range(0, len(Rrs443)):
            if Rrs443[i] > Rrs488[i]:
                Rrsblue = Rrs443[i]
            else:
                Rrsblue = Rrs488[i]

            log10chl = a0 + a1 * (np.log10(Rrsblue / Rrs547[i])) \
                + a2 * (np.log10(Rrsblue / Rrs547[i]))**2 \
                    + a3 * (np.log10(Rrsblue / Rrs547[i]))**3 \
                        + a4 * (np.log10(Rrsblue / Rrs547[i]))**4

            oc3m = np.power(10, log10chl)

            CI = Rrs555[i] - ( Rrs443[i] + (555 - 443)/(667 - 443) * \
                (Rrs667[i] -Rrs443[i]) )
            # CI = Rrs555[i] - 0.5 * (Rrs443[i] + Rrs667[i])
            ChlCI = 10** (ci1 + ci2*CI)

            if ChlCI <= thresh[0]:
                chlor_a.append(ChlCI)
            elif ChlCI > thresh[1]:
                chlor_a.append(oc3m)
            else:
                chlor_a.append(oc3m * (ChlCI-thresh[0]) / (thresh[1]-thresh[0]) +\
                    ChlCI * (thresh[1]-ChlCI) / (thresh[1]-thresh[0]))

        
        chlDS.columns['chlor_a'] = chlor_a
        chlDS.columnsToDataset()

    