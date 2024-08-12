
import collections
import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline
from itertools import compress

class Weight_RSR:
    @staticmethod
    def calculateBand(spectralDataset, wavelength, response):
        # In the case of a dictionary of float values rather than lists (e.g. rhoVec), convert to lists
        if isinstance(list(spectralDataset.values())[0], float):
            temp = {}
            for key, value in spectralDataset.items():
                temp[key] = [value]
            spectralDataset = temp

        n = len(list(spectralDataset.values())[0])
        result = []

        # For each row of data within a band
        for i in range(n):
            srf_sum = 0
            c_sum = 0.0

            # For each lamda in band
            for j in np.arange(0, len(wavelength)):
                ld = str(wavelength[j])
                srf = response[j]

                # Check if lamda is in spectralDataset
                if ld in spectralDataset:
                    dataAtLambda = spectralDataset[ld][i]
                    srf_sum += dataAtLambda*srf
                    c_sum += response[j]

            # Calculate srf value for that band
            if c_sum == 0:
                # For satellite bands (like 1240 nm) that have all 0 RSR in bands used for hyperspectral data
                c = 0
            else:
                c = 1/c_sum
            result.append(c * srf_sum)
        return result

    @staticmethod
    def MODISBands():
        wavelength=[412,443,469,488,531,551,555,645,667,
                678,748,859,869,1240,1640,2130]
        return wavelength

    @staticmethod
    def processMODISBands(hyperspecData, sensor='A'):

        keys = hyperspecData.keys()
        wvInterp = np.empty([1,len(keys)])*0
        for i, key in enumerate(keys):
            wvInterp[0,i] = float(key)
        wvInterp = wvInterp[0].tolist()

        weightedBandData = collections.OrderedDict()
        fields = Weight_RSR.MODISBands()

        # Read in the RSRs from NASA
        if sensor == 'A':
            modisRSRFile = 'Data/HMODISA_RSRs.txt'
        else:
            modisRSRFile = 'Data/HMODIST_RSRs.txt'

        data = np.loadtxt(modisRSRFile, skiprows=7)
        wavelength = data[:,0].tolist()

        # Only use bands that intersect hyperspectral data
        gudBands = []
        for field in fields:
            if field >= min(wvInterp) and field <= max(wvInterp):
                gudBands.append(True)
            else:
                gudBands.append(False)
        fields = list(compress(fields,gudBands))

        gudBands.insert(0,False) # First one is false for the wavelength column in data
        rsr = data[:,gudBands]

        rsrInterp = np.empty([len(hyperspecData),rsr.shape[1]])

        # Interpolate the response functions to the wavebands of the OCR
        order = 1
        for i in np.arange(0,rsr.shape[1]):
            # rsrInterp[:,i] = Utilities.interp(wavelength,rsr[:,i].tolist(),wvInterp[0].tolist())
            fn = InterpolatedUnivariateSpline(wavelength,rsr[:,i].tolist(),k=order)
            rsrInterp[:,i] = fn(wvInterp)

        for i in np.arange(0, len(fields)):
            weightedBandData[str(fields[i])] = \
                Weight_RSR.calculateBand(hyperspecData, wvInterp, rsrInterp[:,i])

        return weightedBandData


    @staticmethod
    def VIIRSBands():
        wavelength=[412,445,488,555,672,746,865, 1240,1610,2250]

        return wavelength

    @staticmethod
    def processVIIRSBands(hyperspecData, sensor='N'):
        keys = hyperspecData.keys()
        wvInterp = np.empty([1,len(keys)])*0
        for i, key in enumerate(keys):
            wvInterp[0,i] = float(key)
        wvInterp = wvInterp[0].tolist()

        weightedBandData = collections.OrderedDict()
        fields = Weight_RSR.VIIRSBands()

        # Read in the RSRs from NASA
        if sensor == 'N':
            modisRSRFile = 'Data/VIIRSN_IDPSv3_RSRs.txt'
        else:
            modisRSRFile = 'Data/VIIRS1_RSRs.txt'

        data = np.loadtxt(modisRSRFile, skiprows=5)
        wavelength = data[:,0].tolist()

        # Only use bands that intersect hyperspectral data
        gudBands = []
        for field in fields:
            if field >= min(wvInterp) and field <= max(wvInterp):
                gudBands.append(True)
            else:
                gudBands.append(False)
        fields = list(compress(fields,gudBands))

        gudBands.insert(0,False) # First one is false for the wavelength column in data
        rsr = data[:,gudBands]

        rsrInterp = np.empty([len(hyperspecData),rsr.shape[1]])

        # Interpolate the response functions to the wavebands of the OCR
        order = 1
        for i in np.arange(0,rsr.shape[1]):
            # rsrInterp[:,i] = Utilities.interp(wavelength,rsr[:,i].tolist(),wvInterp[0].tolist())
            fn = InterpolatedUnivariateSpline(wavelength,rsr[:,i].tolist(),k=order)
            rsrInterp[:,i] = fn(wvInterp)

        for i in np.arange(0, len(fields)):
            weightedBandData[str(fields[i])] = \
                Weight_RSR.calculateBand(hyperspecData, wvInterp, rsrInterp[:,i])

        return weightedBandData


    @staticmethod
    def Sentinel3Bands():
        wavelength=[400.0,412.5,442.5,490.0,510.0,560.0,620.0,665.0,673.75,
                681.25,708.75,753.75,761.25,764.38,767.5,778.78,865.0,
                885.0,900.0,940.0,1020.0]  # lack of '.0' causing key error along the pipeline

        return wavelength

    @staticmethod
    def processSentinel3Bands(hyperspecData, sensor='A'):
        keys = hyperspecData.keys()
        wvInterp = np.empty([1,len(keys)])*0
        pass
        for i, key in enumerate(keys):
            wvInterp[0,i] = float(key)
        wvInterp = wvInterp[0].tolist()

        weightedBandData = collections.OrderedDict()
        fields = Weight_RSR.Sentinel3Bands()

        # Read in the RSRs from NASA
        # OLCI Sentinel 3A
        if sensor == 'A':
            modisRSRFile = 'Data/OLCIA_RSRs.txt'
        else:
            modisRSRFile = 'Data/OLCIB_RSRs.txt'
        data = np.loadtxt(modisRSRFile, skiprows=10)
        wavelength = data[:,0].tolist()
        # Only use bands that intersect hyperspectral data
        gudBands = []
        for field in fields:
            if field >= min(wvInterp) and field <= max(wvInterp):
                gudBands.append(True)
            else:
                gudBands.append(False)
        fields = list(compress(fields,gudBands))

        gudBands.insert(0,False) # First one is false for the wavelength column in data
        rsr = data[:,gudBands]
        rsr[rsr==-999.0] = 0

        rsrInterp = np.empty([len(hyperspecData),rsr.shape[1]])


        # Interpolate the response functions to the wavebands of the OCR
        order = 1
        for i in np.arange(0,rsr.shape[1]):
            # rsrInterp[:,i] = Utilities.interp(wavelength,rsr[:,i].tolist(),wvInterp[0].tolist())
            fn = InterpolatedUnivariateSpline(wavelength,rsr[:,i].tolist(),k=order)
            rsrInterp[:,i] = fn(wvInterp)

        for i in np.arange(0, len(fields)):
            weightedBandData[str(fields[i])] = \
                Weight_RSR.calculateBand(hyperspecData, wvInterp, rsrInterp[:,i])

        return weightedBandData