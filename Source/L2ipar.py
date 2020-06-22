
import numpy as np
from Utilities import Utilities

class L2ipar():
    
    @staticmethod
    def L2ipar(root):
        ''' Use hyperspectral irradiance to calculate instantaneous photosynthetically 
            available radiation in Einstein m^-2'''

        Es_ds = root.getGroup("IRRADIANCE").datasets["ES_HYPER"]
        keys = list(Es_ds.columns.keys())
        values = list(Es_ds.columns.values())
        waveStr = keys[3:]
        Es = np.array(values[3:])
        wavelength = np.array([float(i) for i in waveStr])
        fullSpec = np.array(list(range(400, 701)))

        # ipar
        unitc = 119.625e8
        
        dateTime = Es_ds.columns['Datetime']
        dateTag = Es_ds.columns['Datetag']
        timeTag2 = Es_ds.columns['Timetag2']

        prodGroup = root.getGroup('DERIVED_PRODUCTS')
        iparDS = prodGroup.addDataset('ipar')
        prodGroup.attributes['ipar_UNITS'] = 'Einstein m^-2 d^-1'
        iparDS.columns['Datetime'] = dateTime
        iparDS.columns['Datetag'] = dateTag
        iparDS.columns['Timetag2'] = timeTag2

        ipar = []
        for n in range(0, len(dateTime)):
            ipar.append(0.0)
            Es_n = Utilities.interp(wavelength, Es[:,n], fullSpec)
            for i, wl in enumerate(fullSpec):
                ipar[n] += (wl * Es_n[i] / unitc )

        iparDS.columns['ipar'] = ipar
        iparDS.columnsToDataset()

       