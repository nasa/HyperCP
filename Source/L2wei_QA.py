
import numpy as np
import numpy.matlib as npm

def QAscores_5Bands(test_Rrs, test_lambda):
    '''Quality assurance system for Rrs spectra (Version 2.0)'''

    # function [maxCos, cos, clusterID, totScore] = QAscores_5Bands(test_Rrs, test_lambda)
    # 
    # In this version, five-band Rrs at 412, 443, 488, 551 and 670 nm are used
    # in order to create comparable QA scores for different instruments (e.g., SeawiFS, MODISA, MEIRS, VIIRS, OLCI).
    #
    # ------------------------------------------------------------------------------
    # KNOWN VARIABLES :   ref_nRrs   -- Normalized Rrs spectra per-determined from water clustering (23x5 matrix)  
    #                     ref_lambda -- Wavelengths for ref_nRrs (1x5 matrix)
    #                     upB        -- Upper boundary (23x5 matrix)
    #                     lowB       -- Lower boundary (23x5 matrix)
    #
    # INPUTS:            test_Rrs -- matrix (inRow*inCol), each row represents one Rrs spectrum; numpy array
    #                    test_lambda-- Wavelengths for test_Rrs; numpy array
    #
    # OUTPUTS:  maxCos     -- maximum cosine values
    #           cos        -- cosine values for every ref_nRrs spectra
    #           clusterID  -- idenfification of water types (from 1-23)
    #           totScore   -- total score assigned to test_Rrs
    # ------------------------------------------------------------------------------
    # 
    # NOTE:
    #         1) Five wavelengths (412, 443, 488, 551, 670 nm) are assumed in the model
    #         2) If your Rrs data were measured at other wavelength, e.g. 440nm, you may want to change 440 to 443 before the model run;
    #             or modify the code below to find a cloest wavelength from the nine bands.
    #         3) The latest version may be found online at HTTP://oceanoptics.umb.edu/score_metric
    #
    # Reference:
    #         Wei, Lee, and Shang (2016). 
    #         A system to measure the data quality of spectral remote sensing
    #         reflectance of aquatic environments. Journal of Geophysical Research, 
    #         121, doi:10.1002/2016JC012126
    #         
    # ------------------------------------------------------------------------------
    # Note:
    #     1) nanmean, nansum need statistics toolbox
    #     2) on less memory and multi-core system, it may further speedup using
    #        parfor
    #
    # Author: Jianwei Wei, NOAA/NESDIS Center for Satellite Applications and Research
    # Email: Jianwei.Wei@noaa.gov
    #
    # upated January-14-2020
    # 
    # Translated from the original Matlab to python by Dirk Aurin, 2020-11-25
    # ------------------------------------------------------------------------------

    ''' Check input data '''
    if test_lambda.ndim > 1:
        row_lam, len_lam = test_lambda.shape
        if row_lam != 1:
            test_lambda = np.transpose(test_lambda)
            row_lam, len_lam = test_lambda.shape
    else:
        row_lam = 1
        len_lam = len(test_lambda)

    row, col = test_Rrs.shape
    if len_lam != col and len_lam != row:
        print('Rrs and lambda size mismatch, please check the input data!')
    elif len_lam == row:
        test_Rrs = np.transpose(test_Rrs)

    ''' 23 Normalized spectral water types ''' 
    ref_lambda = np.array([412,443,488,551,670])

    ref_nRrs = np.array([ \
        [0.74996,0.54868,0.35803,0.08539,0.00625], \
        [0.71125,0.55973,0.41201,0.11609,0.01041], \
        [0.65672,0.56203,0.47156,0.16365,0.01648], \
        [0.58645,0.55225,0.53263,0.25561,0.03157], \
        [0.49175,0.54116,0.60256,0.30151,0.03564], \
        [0.54323,0.52581,0.55413,0.33867,0.04925], \
        [0.43659,0.49708,0.61338,0.42321,0.05396], \
        [0.47248,0.48128,0.56584,0.46308,0.07609], \
        [0.38299,0.45771,0.61314,0.51734,0.07333], \
        [0.39674,0.43581,0.56188,0.56855,0.10327], \
        [0.46958,0.44289,0.51258,0.54089,0.14956], \
        [0.30719,0.39258,0.56133,0.64019,0.12493], \
        [0.38158,0.37420,0.47828,0.65599,0.21498], \
        [0.26304,0.34679,0.50187,0.69723,0.25485], \
        [0.27801,0.33191,0.50608,0.72609,0.17123], \
        [0.27331,0.31942,0.45465,0.68178,0.38685], \
        [0.20869,0.28428,0.46490,0.75741,0.27950], \
        [0.21723,0.26406,0.42696,0.80451,0.21960], \
        [0.27088,0.25728,0.35480,0.66337,0.53765], \
        [0.07913,0.19509,0.32714,0.59763,0.70357], \
        [0.23025,0.26588,0.39998,0.77532,0.33684], \
        [0.16532,0.21737,0.38643,0.77736,0.41755], \
        [0.18559,0.18272,0.26051,0.74943,0.53272], \
        ])

    upB = np.array([ \
        [0.78838,0.56847,0.38234,0.10635,0.04743], \
        [0.73772,0.57546,0.44515,0.14046,0.02886], \
        [0.68278,0.58352,0.51810,0.22583,0.07175], \
        [0.63377,0.57471,0.57787,0.29936,0.07270], \
        [0.53567,0.57032,0.66046,0.35981,0.06593], \
        [0.57995,0.54816,0.59574,0.40399,0.12234], \
        [0.48114,0.52110,0.65807,0.46495,0.08516], \
        [0.55356,0.51184,0.59875,0.51171,0.12100], \
        [0.42348,0.48890,0.67525,0.56493,0.11500], \
        [0.45994,0.45828,0.59186,0.63773,0.15269], \
        [0.52342,0.47307,0.57051,0.60074,0.26253], \
        [0.36610,0.42668,0.69114,0.68136,0.21055], \
        [0.43550,0.42450,0.53691,0.74009,0.31536], \
        [0.30584,0.40294,0.54691,0.74744,0.32909], \
        [0.35805,0.36806,0.56152,0.77329,0.21430], \
        [0.34431,0.37320,0.49672,0.73019,0.44881], \
        [0.27500,0.32132,0.50907,0.80017,0.35638], \
        [0.30812,0.29993,0.49224,0.87233,0.28781], \
        [0.33783,0.33282,0.44063,0.73547,0.60083], \
        [0.16938,0.22068,0.35378,0.65586,0.89736], \
        [0.33792,0.30652,0.43326,0.84038,0.40450], \
        [0.23603,0.25683,0.42523,0.84354,0.47431], \
        [0.25485,0.22345,0.34304,0.78502,0.61513], \
        ])

    lowB = np.array([ \
        [0.72630,0.53053,0.27434,0.04958,0.00135], \
        [0.68007,0.53213,0.38784,0.09658,0.00305], \
        [0.60823,0.54421,0.43849,0.13122,0.00773], \
        [0.53531,0.51909,0.49380,0.19941,0.01192], \
        [0.44375,0.49115,0.57837,0.24748,0.01842], \
        [0.49180,0.50349,0.51278,0.29531,0.03114], \
        [0.39096,0.46741,0.58006,0.35830,0.03630], \
        [0.42233,0.45802,0.49776,0.41048,0.04643], \
        [0.28442,0.39007,0.58491,0.46353,0.02408], \
        [0.34428,0.38950,0.52425,0.51943,0.05320], \
        [0.40201,0.40230,0.44712,0.48789,0.08806], \
        [0.19270,0.35270,0.50810,0.55867,0.03655], \
        [0.33731,0.32983,0.38686,0.58958,0.13853], \
        [0.22616,0.31012,0.45382,0.63880,0.21410], \
        [0.14776,0.25932,0.43186,0.66844,0.03853], \
        [0.21041,0.28604,0.38211,0.62868,0.31945], \
        [0.10575,0.23727,0.43373,0.71788,0.23281], \
        [0.09434,0.18851,0.36503,0.76615,0.08160], \
        [0.22957,0.24069,0.28999,0.59611,0.46263], \
        [0.04835,0.04480,0.12898,0.38997,0.63381], \
        [0.17148,0.22387,0.29863,0.73839,0.27090], \
        [0.05797,0.15605,0.30338,0.72705,0.33646], \
        [0.11525,0.14618,0.22647,0.69684,0.47248], \
        ])
        
    refRow, _ = ref_nRrs.shape

    ''' Match the ref_lambda and test_lambda '''
    idx0 = np.empty(len(ref_lambda), dtype='int') # for ref_lambda 
    idx1 = np.empty(len(test_lambda), dtype='int') # for test_lambda

    for i, value in enumerate(test_lambda):
        pos, = np.where(ref_lambda == value) #find(ref_lambda==value);
        # if isempty(pos)
        if pos.size > 0:
            idx0[i] = pos.astype(int)
            idx1[i] = i
        else:
            idx1[i] = np.nan
            
    pos = np.isnan(idx1)
    np.delete(idx1, pos)

    test_lambda = test_lambda[idx1]
    test_Rrs = test_Rrs[:,idx1]
    ref_lambda = ref_lambda[idx0]
    ref_nRrs = ref_nRrs[:,idx0]
    upB = upB[:,idx0]
    lowB = lowB[:,idx0] 

    ''' Match the ref_nRrs and test_Rrs '''
    # keep the original value
    test_Rrs_orig = test_Rrs
    
    ''' Normalization '''
    inRow, inCol = np.shape(test_Rrs)

    # transform spectrum to column, inCol*inRow
    test_Rrs = np.transpose(test_Rrs)
    test_Rrs_orig = np.transpose(test_Rrs_orig)

    # inCol*inRow
    nRrs_denom = np.sqrt(np.nansum(test_Rrs**2, 0))
    # nRrs_denom = repmat(nRrs_denom,[inCol,1]);
    nRrs_denom = npm.repmat(nRrs_denom, inCol, 1)
    nRrs = test_Rrs/nRrs_denom      

    # SAM input, inCol*inRow*refRow 
    test_Rrs2 = np.repeat(test_Rrs_orig[:, :, np.newaxis], refRow, axis=2)

    # #for ref Rrs, inCol*refRow*inRow 
    # test_Rrs2p = np.moveaxis(test_Rrs2, 2, 1)

    # inCol*inRow*refRow  
    nRrs2_denom = np.sqrt(np.nansum(test_Rrs2**2, 0))
    # nRrs2_denom = repeat(nRrs2_denom, inCol, axis=2)
    nRrs2_denom = np.repeat(nRrs2_denom[:,:, np.newaxis], inCol, axis=2)
    nRrs2_denom = np.moveaxis(nRrs2_denom, 2, 0)
    nRrs2 = test_Rrs2/nRrs2_denom
    # inCol*refRow*inRow  
    nRrs2 = np.moveaxis(nRrs2, 2, 1)

    ''' Adjust the ref_nRrs, according to the matched wavebands '''
    #row,_  = ref_nRrs.shape

    #### re-normalize the ref_adjusted
    ref_nRrs = np.transpose(ref_nRrs)

    # inCol*refRow*inRow 
    ref_nRrs2 = np.repeat(ref_nRrs[:,:, np.newaxis], inRow, axis=2)

    # inCol*refRow*inRow 
    ref_nRrs2_denom = np.sqrt(np.nansum(ref_nRrs2**2, 0))
    ref_nRrs2_denom = np.repeat(ref_nRrs2_denom[:,:, np.newaxis], inCol, axis=2)
    ref_nRrs2_denom = np.moveaxis(ref_nRrs2_denom, 2, 0)
    ref_nRrs_corr2 = ref_nRrs2/ref_nRrs2_denom

    ''' Classification '''
    #### calculate the Spectral angle mapper
    # inCol*refRow*inRow 
    cos_denom = np.sqrt(np.nansum(ref_nRrs_corr2**2, 0) * np.nansum(nRrs2**2, 0))
    cos_denom = np.repeat(cos_denom[:, :, np.newaxis], inCol, axis=2)
    cos_denom = np.moveaxis(cos_denom, 2, 0)
    cos = (ref_nRrs_corr2*nRrs2)/cos_denom
    # refRow*inRow 
    cos = np.sum(cos, 0)
    
    # 1*inRow
    maxCos = np.amax(cos, axis=0) 
    clusterID = np.argmax(cos, axis=0) # finds location of max along an axis, returns int64
    posClusterID = np.isnan(maxCos)

    ''' Scoring '''
    upB_corr = np.transpose(upB) 
    lowB_corr = np.transpose(lowB)

    ''' Comparison '''
    # inCol*inRow
    upB_corr2 = upB_corr[:,clusterID] * (1+0.01)
    lowB_corr2 = lowB_corr[:,clusterID] * (1-0.01)
    ref_nRrs2 = ref_nRrs[:,clusterID]

    #normalization
    ref_nRrs2_denom = np.sqrt(np.nansum(ref_nRrs2**2, 0))
    ref_nRrs2_denom = np.transpose(np.repeat(ref_nRrs2_denom[:,np.newaxis], inCol, axis=1))
    upB_corr2 = upB_corr2 / ref_nRrs2_denom
    lowB_corr2 = lowB_corr2 / ref_nRrs2_denom

    upB_diff = upB_corr2 - nRrs
    lowB_diff = nRrs - lowB_corr2

    C = np.empty([inCol,inRow], dtype='float')*0
    pos = np.logical_and(upB_diff>=0, lowB_diff>=0)
    C[pos] = 1

    #process all NaN spectral 
    C[:,posClusterID] = np.nan                                               

    totScore = np.nanmean(C, 0)
    clusterID = clusterID.astype('float')
    clusterID[posClusterID] = np.nan
    # Convert from index to water type 1-23
    clusterID = clusterID +1

    return maxCos, cos, clusterID, totScore