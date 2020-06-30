
import numpy as np

def L2gocad(Rrs443, Rrs488, Rrs531, Rrs547, SAL, fill=-9999):
    ''' Use weighted MODIS Aqua bands to calculate CDOM absorption, spectral 
        slopes, and DOC base on (Aurin et al. 2018) '''   
    n_spectra = len(Rrs443)     

    # CDOM
    waveOut = ['275','355','380','412','443','488']
    n_bands = len(waveOut)
    # ag_lim = np.array([4.8245,0.9104,0.4341,0.36419,0.1984,0.1114]) #Thresholds based on 99%ile (2nd iteration) see MLR_stats.m
    ag_lim = np.array([0.9,0.9104,0.09054,0.36419,0.1984,0.1114])
    beta = np.array([[0.0885, -0.5396, -1.1416, 3.4442, -1.8752], \
        [-2.2461, -1.1857, -0.5582, 2.9123, -1.3356], \
            [-2.2625, -0.3001, -1.8819, 3.8314, -1.7868], \
                [-2.5350, -0.5625, -1.2943, 1.6055, 0.1697], \
                    [-3.2872, -0.7268, -0.9223, 1.2782, 0.2612], \
                        [-3.7218, -0.3770, -1.4287, 1.4239, 0.2998]])
    ag = np.empty([n_spectra, n_bands])
    for n in range(0, n_bands):
        ag[:,n] = np.exp( beta[n,0] + beta[n,1]*np.exp(Rrs443) + beta[n,2]* np.exp(Rrs488) + \
            beta[n,3]*np.exp(Rrs531) + beta[n,4]*np.exp(Rrs547) )
    
    for n in range(0, n_spectra):
        ag[n, ag[n,:] > ag_lim] = np.nan

    
    # Sg
    # BANDS = [275 290 300 3501 3502 380 4121 4122];
    BANDS = [275, 300, 4121]
    # These will probably never be invoked because the algorithms are not sensitive enough 
    sg_lim = np.array([0.015, 0.032], [0.016, 0.025], [0.015, 0.021], [0.012, 0.02]])  
    
    beta = np.array([[0.0885, -0.5396, -1.1416, 3.4442, -1.8752], \
        [-2.2461, -1.1857, -0.5582, 2.9123, -1.3356], \
            [-2.2625, -0.3001, -1.8819, 3.8314, -1.7868], \
                [-2.5350, -0.5625, -1.2943, 1.6055, 0.1697], \
                    [-3.2872, -0.7268, -0.9223, 1.2782, 0.2612], \
                        [-3.7218, -0.3770, -1.4287, 1.4239, 0.2998]])
    ag = np.empty([n_spectra, n_bands])
    for n in range(0, n_bands):
        ag[:,n] = np.exp( beta[n,0] + beta[n,1]*np.exp(Rrs443) + beta[n,2]* np.exp(Rrs488) + \
            beta[n,3]*np.exp(Rrs531) + beta[n,4]*np.exp(Rrs547) )
    
    for n in range(0, n_spectra):
        ag[n, ag[n,:] > ag_lim] = np.nan


    return ag#, Sg, DOC

