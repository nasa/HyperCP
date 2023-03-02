
import numpy as np
import scipy

def L2avw(wavelength, Rrs):
    ''' Use hyperspectral Rrs to calculate average visible wavelength. Vectorwise.'''
    # Inputs:
    #   wavelength: vector of length Rrs or array of shape Rrs
    #   Rrs: array of shape wavelength X n

    # Truncate to the VIS
    lims = [400, 701]
    # outIndex = []
    # for i, wl in enumerate(wavelength):
    #     if wl < lims[0] or wl > lims[-1]:
    #         outIndex.append(i)

    # wavelength = np.delete(wavelength, outIndex)
    # Rrs = np.delete(Rrs, outIndex, axis = 0)

    if np.shape(wavelength) != np.shape(Rrs):
        wavelength = np.transpose(np.matlib.repmat(wavelength,np.shape(Rrs)[1],1))

    wave_1nm = np.arange(lims[0], lims[1])
    Rrs_1nm = np.empty([wave_1nm.shape[0],Rrs.shape[1]])

    for i in np.arange(0,Rrs.shape[1]):
        Rrs_1nm[:,i] = scipy.interpolate.interp1d(wavelength[:,i], Rrs[:,i], kind='linear', bounds_error=True)(wave_1nm)

    wave_1nm = np.tile(wave_1nm,(Rrs.shape[1],1))
    wave_1nm = np.rot90(wave_1nm,3)
    avw =  np.sum( Rrs_1nm / np.sum( Rrs_1nm/wave_1nm, axis = 0) , axis = 0).tolist()
    lambda_max = wave_1nm[np.argmax(Rrs_1nm, axis=0), 0].tolist()
    brightness =  np.trapz(Rrs_1nm, wave_1nm, axis=0).tolist()

    return avw, lambda_max, brightness




