
import numpy as np

def L2gocad(Rrs443, Rrs488, Rrs531, Rrs547, SAL, fill=-9999):
    ''' Use weighted MODIS Aqua bands to calculate CDOM absorption, spectral 
        slopes, and DOC based on
            
            D. Aurin, A. Mannino, and D. J. Lary, “Remote sensing of CDOM, CDOM 
            spectral slope, and dissolved organic carbon in the global ocean,” Appl. 
            Sci. 8, 2687 (2018).
        
        Inputs: 
            RrsXXX: (float) above water remote sensing reflectance at XXX nm          
            SAL: (float) sea surface salinity
            fill: value substituted for failed retrieval
        
        Outputs:
            ag: (array) CDOM at 275, 355, 380, 412, 443, 488 nm
            Sg: (array) CDOM slope at 275-295, 300-600, 412-600 nm
            
            
        2020-07-01: by Dirk Aurin, NASA Goddard Space Flight Center, dirk.a.aurin@nasa.gov
        '''   
    
    n_spectra = len(Rrs443)

    # CDOM
    waveOut = ['275','355','380','412','443','488']
    n_bands = len(waveOut)
    #Thresholds based on 99%ile (2nd iteration) see MLR_stats.m
    #  Note: these were run on L3 Aqua using the MLR 3-band algorithm, and could use updating
    ag_lim = np.array([4.8245,0.9104,0.4341,0.36419,0.1984,0.1114]) 
    
    beta = np.array([[0.0885, -0.5396, -1.1416, 3.4442, -1.8752], \
        [-2.2461, -1.1857, -0.5582, 2.9123, -1.3356], \
            [-2.2625, -0.3001, -1.8819, 3.8314, -1.7868], \
                [-2.5350, -0.5625, -1.2943, 1.6055, 0.1697], \
                    [-3.2872, -0.7268, -0.9223, 1.2782, 0.2612], \
                        [-3.7218, -0.3770, -1.4287, 1.4239, 0.2998]])
    ag = np.empty([n_spectra, n_bands])
    for n in range(0, n_bands):
        ag[:,n] = np.exp( beta[n,0] + beta[n,1]*np.log(Rrs443) + beta[n,2]* np.log(Rrs488) + \
            beta[n,3]*np.log(Rrs531) + beta[n,4]*np.log(Rrs547) )
    
    for n in range(0, n_spectra):
        ag[n, ag[n,:] > ag_lim] = fill

    
    # Sg
    BANDS = [275, 300, 350, 380, 412] # 275-295, 300-600, 350-600, 380-600, 412-600
    n_bands = len(BANDS)
    # These are the 2nd and 98th percentiles of GOCAD 
    sg_lim = np.array([[0.0169, 0.0445], [0.0159, 0.0255], [0.0119, 0.0200], [0.0107, 0.0194], [0.0059, 0.0188]])  
    
    beta = np.array([[-3.2892, 0.2697, -0.3346, 1.0507, -0.9211], \
        [-3.6065, 0.0439, -0.1533, 0.8810, -0.7215], \
            [-3.9083, -0.2039, 0.0979, 0.6092, -0.4633], \
                [-3.9116, -0.1519, 0.1272, 0.2360, -0.1731], \
                    [-4.2190, -0.1799, 0.1366, 0.1676, -0.1311]])
    Sg = np.empty([n_spectra, n_bands])
    for n in range(0, n_bands):
        Sg[:,n] = np.exp( beta[n,0] + beta[n,1]*np.log(Rrs443) + beta[n,2]* np.log(Rrs488) + \
            beta[n,3]*np.log(Rrs531) + beta[n,4]*np.log(Rrs547) )
    
    # Set Sg outside limits to thresholds
    for n in range(0, n_spectra):
        Sg[n, Sg[n,:] < sg_lim[:,0]] = sg_lim[Sg[n,:] < sg_lim[:,0],0]
        Sg[n, Sg[n,:] > sg_lim[:,1]] = sg_lim[Sg[n,:] > sg_lim[:,1],1]


    # DOC (MLR2)
    beta = [192.718, 26.790, -3.558]
    # # These are the 2nd and 98th percentiles of GOCAD 
    doc_lim = [47.2383,  223.7900]

    doc = np.empty([n_spectra, ])
    for n in range(0, n_spectra):
        doc[n] = beta[0] + beta[1] * ag[n,2] + beta[2] * SAL[n]

    for n in range(0, n_spectra):
        if doc[n] < doc_lim[0] or doc[n] > doc_lim[1]:
            doc[n] = fill


    return ag, Sg, doc

