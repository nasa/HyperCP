
import numpy as np

class L2kd490():
    
    @staticmethod
    def L2kd490(root):
        ''' Use weighted MODIS Aqua bands to calculate diffuse attenuation
        coefficient of downwelling irradiance at 490 '''

        Reflectance = root.getGroup("REFLECTANCE")
        
        dateTime = Reflectance.datasets['Rrs_HYPER'].columns['Datetime']
        dateTag = Reflectance.datasets['Rrs_HYPER'].columns['Datetag']
        timeTag2 = Reflectance.datasets['Rrs_HYPER'].columns['Timetag2']

        prodGroup = root.getGroup('DERIVED_PRODUCTS')
        kdDS = prodGroup.addDataset('kd490')
        prodGroup.attributes['kd490_UNITS'] = 'm^-1'
        kdDS.columns['Datetime'] = dateTime
        kdDS.columns['Datetag'] = dateTag
        kdDS.columns['Timetag2'] = timeTag2

        Rrs488 = np.array(Reflectance.datasets["Rrs_MODISA"].columns['488'])
        Rrs547 = np.array(Reflectance.datasets["Rrs_MODISA"].columns['551']) # 551 in name only

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

        kdDS.columns['kd490'] = kd490.tolist()
        kdDS.columnsToDataset()

    