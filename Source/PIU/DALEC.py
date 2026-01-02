# Maths
import numpy as np

# Packages
import warnings
from copy import deepcopy

# PIU
from Source.PIU.BaseInstrument import BaseInstrument

# Utilities
from Source.utils.loggingHCP import writeLogFileAndPrint


class Dalec(BaseInstrument):

    def __init__(self):
        super().__init__()  # call to instrument __init__
        self.instrument = "Dalec"

    def lightDarkStats(self, grp, slice, sensortype):
        # Dalec
        lightSlice = deepcopy(slice)  # copy to prevent changing of Raw data

        lightData = lightSlice['data']  # lightGrp.getDataset(sensortype)
        darkData = lightSlice['dc']
        if  grp is None:
            writeLogFileAndPrint(f'No radiometry found for {sensortype}')
            return False

        # Correct light data by subtracting interpolated dark data from light data
        std_Light = []
        std_Dark = []
        ave_Light = []
        ave_Dark = []
        stdevSignal = {}

        # number of replicates for light and dark readings
        N = np.asarray(list(lightData.values())).shape[1]

        if N > 25:  # normal case
            std_Dark0=np.std(darkData[sensortype])/np.sqrt(N)
        elif N > 3:
            std_Dark0=np.sqrt(((N-1)/(N-3))*(np.std(darkData[sensortype]) / np.sqrt(N))**2)

        ave_Dark0=np.average(darkData[sensortype])
        #print("std_Dark0")
        #print(std_Dark0)
        for i, k in enumerate(lightData.keys()):
            wvl = str(float(k))

            # apply normalisation to the standard deviations used in uncertainty calculations
            if N > 25:  # normal case
                std_Light.append(np.std(lightData[k])/np.sqrt(N))
                std_Dark.append(std_Dark0)  # sigma here is essentially sigma**2 so N must sqrt
            elif N > 3:  # few scans, use different statistics
                std_Light.append(np.sqrt(((N-1)/(N-3))*(np.std(lightData[k]) / np.sqrt(N))**2))
                std_Dark.append(std_Dark0)
            else:
                writeLogFileAndPrint("too few scans to make meaningful statistics")
                return False

            ave_Light.append(np.average(lightData[k]))
            ave_Dark.append(ave_Dark0)

            for x in range(N):
                lightData[k][x] -= darkData[sensortype][x]

            signalAve = np.average(lightData[k])

            # Normalised signal standard deviation =
            if signalAve:
                stdevSignal[wvl] = pow((pow(std_Light[i], 2) + pow(std_Dark[i], 2))/pow(signalAve, 2), 0.5)
            else:
                stdevSignal[wvl] = 0.0

        #print("std_Light/Dark")
        #print(std_Light)
        #print(stdevSignal)
        return dict(
            ave_Light=np.array(ave_Light),
            ave_Dark=np.array(ave_Dark),
            std_Light=np.array(std_Light),
            std_Dark=np.array(std_Dark),
            std_Signal=stdevSignal,
            )

    def FRM(self, node, uncGrp, raw_grps, raw_slices, stats, newWaveBands):
        # calibration of HyperOCR following the FRM processing of FRM4SOC2
        output = {}
        return output
