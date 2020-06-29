
import numpy as np
import numpy.matlib

def L2avw(wavelength, Rrs):
    ''' Use hyperspectral Rrs to calculate average visible wavelength. Vectorwise.'''
    # Inputs: 
    #   wavelength: vector of length Rrs or array of shape Rrs
    #   Rrs: array of shape wavelength X n 

    # Truncate to the VIS
    lims = [400, 700]    
    outIndex = []
    for i, wl in enumerate(wavelength):
        if wl < lims[0] or wl > lims[-1]:
            outIndex.append(i)

    wavelength = np.delete(wavelength, outIndex)
    Rrs = np.delete(Rrs, outIndex, axis = 0)

    if np.shape(wavelength) != np.shape(Rrs):
        wavelength = np.transpose(np.matlib.repmat(wavelength,np.shape(Rrs)[1],1))
   
    avw =  np.sum( Rrs / np.sum( Rrs/wavelength, axis = 0) , axis = 0).tolist() 
    lambda_max = wavelength[np.argmax(Rrs, axis=0), 0].tolist()
    brightness =  np.trapz(Rrs, wavelength, axis=0).tolist() 

    return avw, lambda_max, brightness


    

