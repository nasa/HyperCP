
# from BandData import MODIS, Sentinel3
import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline

from Utilities import Utilities

class Weight_RSR:
    @staticmethod
    def calculateBand(spectralDataset, wavelength, response):
        #print("Calculate Band")
        n = len(list(spectralDataset.columns.values())[0])        
        result = []

        # For each row of rrs data
        for i in range(n):
            srf_sum = 0
            c_sum = 0.0

            # For each lamda in band
            for j in np.arange(0, len(wavelength)):
                ld = str(wavelength[j])
                srf = response[j]
                #print("ld, srf",ld,srf)

                # Check if lamda in rrs
                if ld in spectralDataset.columns:
                    rrs = spectralDataset.columns[ld][i]
                    #print("srf, rrs", srf, rrs)
                    srf_sum += rrs*srf
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
    def processMODISBands(weightedBandData, hyperspecData, sensor='A'):        
        # Read in the RSRs from NASA
        # Aqua
        fields=[412,443,469,488,531,551,555,645,667,678,748,859,869,1240,1640,2130]
        if sensor == 'A':
            modisRSRFile = 'Data/HMODISA_RSRs.txt'
        else:
            modisRSRFile = 'Data/HMODIST_RSRs.txt'

        data = np.loadtxt(modisRSRFile, skiprows=7)
        wavelength = data[:,0].tolist()
        rsr = data[...,1:]

        rsrInterp = np.empty([len(hyperspecData.columns)-2,rsr.shape[1]])
        keys = hyperspecData.columns.keys()
        wvInterp = np.empty([1,len(keys)-2])*0
        for i, key in enumerate(keys):
            if key == 'Datetag' or key == 'Timetag2':
                continue
            wvInterp[0,i-2] = float(key)
        wvInterp = wvInterp[0].tolist()

        # Interpolate the response functions to the wavebands of the OCR
        order = 1
        for i in np.arange(0,rsr.shape[1]):
            # rsrInterp[:,i] = Utilities.interp(wavelength,rsr[:,i].tolist(),wvInterp[0].tolist())
            fn = InterpolatedUnivariateSpline(wavelength,rsr[:,i].tolist(),k=order)
            rsrInterp[:,i] = fn(wvInterp)
        
        for i in np.arange(0, len(fields)):
            weightedBandData.columns[str(fields[i])] = Weight_RSR.calculateBand(hyperspecData, wvInterp, rsrInterp[:,i])
        
        return weightedBandData

    @staticmethod
    def processVIIRSBands(weightedBandData, hyperspecData, sensor='N'):        
        # Read in the RSRs from NASA
        # Aqua
        fields=['RSR_M1','RSR_M2','RSR_M3','RSR_M4','RSR_M5','RSR_M6','RSR_M7','RSR_M8','RSR_M10','RSR_M11']
        if sensor == 'N':
            modisRSRFile = 'Data/VIIRSN_IDPSv3_RSRs.txt'
        else:
            modisRSRFile = 'Data/VIIRS1_RSRs.txt'

        data = np.loadtxt(modisRSRFile, skiprows=5)
        wavelength = data[:,0].tolist()
        rsr = data[...,1:]

        rsrInterp = np.empty([len(hyperspecData.columns)-2,rsr.shape[1]])
        keys = hyperspecData.columns.keys()
        wvInterp = np.empty([1,len(keys)-2])*0
        for i, key in enumerate(keys):
            if key == 'Datetag' or key == 'Timetag2':
                continue
            wvInterp[0,i-2] = float(key)
        wvInterp = wvInterp[0].tolist()

        # Interpolate the response functions to the wavebands of the OCR
        order = 1
        for i in np.arange(0,rsr.shape[1]):
            # rsrInterp[:,i] = Utilities.interp(wavelength,rsr[:,i].tolist(),wvInterp[0].tolist())
            fn = InterpolatedUnivariateSpline(wavelength,rsr[:,i].tolist(),k=order)
            rsrInterp[:,i] = fn(wvInterp)
        
        for i in np.arange(0, len(fields)):
            weightedBandData.columns[str(fields[i])] = Weight_RSR.calculateBand(hyperspecData, wvInterp, rsrInterp[:,i])
        
        return weightedBandData


    @staticmethod
    def processSentinel3Bands(weightedBandData, hyperspecData, sensor='A'):
        # Read in the RSRs from NASA
        # OLCI Sentinel 3A
        fields=['b1','b2','b3','b4','b5','b6','b7','b8','b9','b10','b11','b12','b13','b14','b15','b16','b17','b18','b19','b20','b21']
        if sensor == 'A':
            modisRSRFile = 'Data/OLCIA_RSRs.txt'
        else:
            modisRSRFile = 'Data/OLCIB_RSRs.txt'
        data = np.loadtxt(modisRSRFile, skiprows=10)
        wavelength = data[:,0].tolist()
        rsr = data[...,1:]
        rsr[rsr==-999.0] = 0

        rsrInterp = np.empty([len(hyperspecData.columns)-2,rsr.shape[1]])
        keys = hyperspecData.columns.keys()
        wvInterp = np.empty([1,len(keys)-2])*0
        pass
        for i, key in enumerate(keys):
            if key == 'Datetag' or key == 'Timetag2':
                continue
            wvInterp[0,i-2] = float(key)
        wvInterp = wvInterp[0].tolist()

        # Interpolate the response functions to the wavebands of the OCR
        order = 1
        for i in np.arange(0,rsr.shape[1]):
            # rsrInterp[:,i] = Utilities.interp(wavelength,rsr[:,i].tolist(),wvInterp[0].tolist())
            fn = InterpolatedUnivariateSpline(wavelength,rsr[:,i].tolist(),k=order)
            rsrInterp[:,i] = fn(wvInterp)
        
        for i in np.arange(0, len(fields)):
            weightedBandData.columns[fields[i]] = Weight_RSR.calculateBand(hyperspecData, wvInterp, rsrInterp[:,i])
        
        return weightedBandData