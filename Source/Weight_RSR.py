
import collections
import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.integrate import simpson
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

    @staticmethod
    def gaussian_L1B(ds, newDS, commonWaveBands):
        ''' Build relative spectral response for gaussians at commonWaveBands with
            10 nm FWHM with 50 RSR bands per commonWaveBand. Then convolve raw L1B 
            bands to the RSR at commonWaveBands.
            NOTE: This will truncate the initial set of commonWaveBands due to lack of 
            overlap in the RSR at the extremities.'''

        # Build the Gaussian RSR table
        fwhm = 10
        bins = 50
        step = fwhm/bins
        minWave = min(commonWaveBands) - bins/2
        maxWave = max(commonWaveBands) + bins/2
        RSRwave = np.arange(minWave,maxWave,step)
        RSR = np.zeros((len(RSRwave),len(commonWaveBands)))

        order = 1
        for i in np.arange(0,RSR.shape[1]):
            mu = commonWaveBands[i]
            x = np.arange(mu - 4*fwhm,mu + 4*fwhm,step)
            sig = fwhm/(2*np.sqrt(2*np.log(2)))
            amp = 1/(sig*np.sqrt(2*np.pi)) *step
            vo = 0
            y = amp*np.exp(-(((x-mu)**2)/(2*sig**2)))+vo 
            # Pad out with zeros
            fn = InterpolatedUnivariateSpline(x,y.tolist(),k=order)
            RSR[:,i] = fn(RSRwave)

        # Convolve raw L1B bands to RSR at commonWaveBands
        # Flip ds datetimes into columns and pop them for use in newDS
        ds.datasetToColumns()
        columns = ds.columns
        saveDatetag = columns.pop("Datetag")
        saveTimetag2 = columns.pop("Timetag2")
        columns.pop("Datetime")

        overlap = (RSRwave >= min(commonWaveBands)) & (RSRwave <= max(commonWaveBands))
        rawData = ds.columns
        rawBands = np.empty([1,len(rawData.keys())])*0
        for i, key in enumerate(rawData.keys()):
            rawBands[0,i] = float(key)
        rawBands = rawBands[0].tolist()
        rawData = np.array(list(rawData.values()))

        # Interpolate each raw spectrum to RSRwave and integrate over the RSR
        start = 1
        spectrum_out = dict()
        for i in np.arange(0,rawData.shape[1]):
            fn = InterpolatedUnivariateSpline(rawBands,rawData[:,i], ext=1) # Return 0s on extrapolation
            interpData = fn(RSRwave)

            # spectrum_out = np.zeros((len(commonWaveBands),1))
            # common_wave_out = np.zeros((len(commonWaveBands),1))            
            for j,commonBand in enumerate(commonWaveBands):
                # Test for band overlap
                RSR_total = simpson(RSR[:,j], x=RSRwave) # same as trapz to several decimal places...
                RSR_overlap = simpson(RSR[overlap,j], x=RSRwave[overlap])

                # 5% maximum difference
                if (RSR_total - RSR_overlap)/RSR_total < 0.05:

                    # Insure that the integral over lambda for this band == 1
                    RSR_band = RSR[:,j]/RSR_total
                    if start == 1:
                        spectrum_out[f'{commonBand:.3f}'] = [simpson(interpData*RSR_band,x=RSRwave)]
                    else:
                        spectrum_out[f'{commonBand:.3f}'].append(simpson(interpData*RSR_band,x=RSRwave))
            if spectrum_out:
                start = 0


        newDS.columns = {k: [float(x) for x in v] for k, v in spectrum_out.items()}
        newDS.columns = {'Timetag2': saveTimetag2, **newDS.columns}
        newDS.columns = {'Datetag': saveDatetag, **newDS.columns}
        newDS.columnsToDataset()
