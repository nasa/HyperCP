
class L2ipar():
    
    @staticmethod
    def L2ipar(root):
        ''' Use hyperspectral irradiance to calculate instantaneous photosynthetically 
            available radiation in Einstein m^-2'''

        Es = root.getGroup("IRRADIANCE").datasets["ES_HYPER"]
        keys = list(Es.columns.keys())
        waveStr = keys[3:]
        wavelength = [float(i) for i in waveStr]

        # ipar
        unitc = 119.625e8
        
        dateTime = Es.columns['Datetime']
        dateTag = Es.columns['Datetag']
        timeTag2 = Es.columns['Timetag2']

        prodGroup = root.getGroup('DERIVED_PRODUCTS')
        iparDS = prodGroup.addDataset('ipar')
        prodGroup.attributes['ipar_UNITS'] = 'Einstein m^-2 d^-1'
        iparDS.columns['Datetime'] = dateTime
        iparDS.columns['Datetag'] = dateTag
        iparDS.columns['Timetag2'] = timeTag2

        ipar = []
        for n in range(0, len(dateTime)):
            ipar.append(0.0)
            for i, wl in enumerate(wavelength):
                Es
                ipar[n] += (wl * Es.columns[waveStr[i]][n] / unitc )

        iparDS.columns['ipar'] = ipar
        iparDS.columnsToDataset()

       