
from Source.Utilities import Utilities

def L2ipar(wavelength, Es, fullSpec):
    ''' Use hyperspectral irradiance to calculate instantaneous photosynthetically 
        available radiation in Einstein m^-2'''    

    # ipar
    unitc = 119.625e8
    
    Es_n = Utilities.interp(wavelength, Es, fullSpec)
    ipar = 0.0
    for i, wl in enumerate(fullSpec):
        ipar += (wl * Es_n[i] / unitc )    

    return ipar

    