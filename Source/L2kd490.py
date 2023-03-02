
import numpy as np

def L2kd490(Rrs488, Rrs547):
    ''' Use weighted MODIS Aqua bands to calculate diffuse attenuation
    coefficient of downwelling irradiance at 490 '''

    Rrs488 = np.array(Rrs488)
    Rrs547 = np.array(Rrs547)

    a0 = -0.8813
    a1 = -2.0584
    a2 = 2.5878
    a3 = -3.4885
    a4 = -1.5061

    log10kd = a0 + a1 * (np.log10(Rrs488 / Rrs547)) \
            + a2 * (np.log10(Rrs488 / Rrs547))**2 \
                + a3 * (np.log10(Rrs488 / Rrs547))**3 \
                    + a4 * (np.log10(Rrs488 / Rrs547))**4
    kd490 = np.power(10, log10kd) + 0.0166        

    return kd490

    