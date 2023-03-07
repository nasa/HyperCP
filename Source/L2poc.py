
import numpy as np

def L2poc(Rrs443, Rrs555):
    ''' Use weighted MODIS Aqua bands to calculate particulate organic carbon  in mg m^-3 '''

    Rrs443 = np.array(Rrs443)
    Rrs555 = np.array(Rrs555)

    a = 203.2
    b = -1.034

    poc = a * (Rrs443/Rrs555)**b     

    return poc