
import numpy as np
from ConfigFile import ConfigFile



class ProcessL2OCproducts():
    
    @staticmethod
    def procProds(root):

        Reflectance = root.getGroup("REFLECTANCE")

        # chlor_a
        if ConfigFile.products["bL2Prodoc3m"]:
            Rrs443 = Reflectance.datasets["Rrs_MODISA"].columns['443']
            Rrs488 = Reflectance.datasets["Rrs_MODISA"].columns['488']
            Rrs547 = Reflectance.datasets["Rrs_MODISA"].columns['551'] # 551 in name only
            Rrs667 = Reflectance.datasets["Rrs_MODISA"].columns['667']


            thresh = [0.15, 0.20]
            a0 = 0.2424
            a1 = -2.7423
            a2 = 1.8017
            a3 = 0.0015
            a4 = -1.2280

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

                CI = Rrs547[i] - (Rrs443[i] + (547 - 443)/(667 - 443) * \
                    (Rrs667[i] -Rrs443[i]))

                if CI <= thresh[0]:
                    chlor_a.append(CI)
                elif CI > thresh[1]:
                    chlor_a.append(oc3m)
                else:
                    chlor_a.append(oc3m * (CI-thresh[0]) / (thresh[1]-thresh[0]) +\
                        CI * (thresh[1]-CI) / (thresh[1]-thresh[0]))


                


            print('hi')        
       