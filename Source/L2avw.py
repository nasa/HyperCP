
import numpy as np

class L2avw():
    
    @staticmethod
    def L2avw(root):
        ''' Use hyperspectral Rrs to calculate average visible wavelength '''
        lims = [400, 700]
        Rrs_ds = root.getGroup("REFLECTANCE").datasets["Rrs_HYPER"]
        keys = list(Rrs_ds.columns.keys())
        values = list(Rrs_ds.columns.values())
        waveStr = keys[3:]
        wavelength = np.array([float(i) for i in waveStr])
        Rrs = np.array(values[3:])
        outIndex = []
        for i, wl in enumerate(wavelength):
            if wl < lims[0] or wl > lims[-1]:
                outIndex.append(i)

        wavelength = np.delete(wavelength, outIndex)
        Rrs = np.delete(Rrs, outIndex, axis = 0)
        
        dateTime = Rrs_ds.columns['Datetime']
        dateTag = Rrs_ds.columns['Datetag']
        timeTag2 = Rrs_ds.columns['Timetag2']

        prodGroup = root.getGroup('DERIVED_PRODUCTS')
        avwDS = prodGroup.addDataset('avw')
        prodGroup.attributes['avw_UNITS'] = 'nm'
        prodGroup.attributes['lambda_max_UNITS'] = 'nm'
        prodGroup.attributes['brightness_UNITS'] = 'nm/sr'
        avwDS.columns['Datetime'] = dateTime
        avwDS.columns['Datetag'] = dateTag
        avwDS.columns['Timetag2'] = timeTag2

        avw = []
        lambda_max = []
        brightness = []
        for n in range(0, len(dateTime)):
            avw.append( np.sum(Rrs[:,n] / np.sum(Rrs[:,n]/wavelength)))
            lambda_max.append( wavelength[np.argmax(Rrs[:,n])] )
            brightness.append( np.trapz(Rrs[:,n], wavelength))


        avwDS.columns['avw'] = avw
        avwDS.columns['lambda_max'] = lambda_max
        avwDS.columns['brightness'] = brightness
        avwDS.columnsToDataset()

    