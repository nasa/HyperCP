
import numpy as np
from Utilities import Utilities


def L2qwip(wavelength, Rrs, avw):
    ''' Use hyperspectral Rrs to calculate average visible wavelength. Vectorwise.'''
    #   Function adapted from 2D image-based approach of RV by DAA: 2022-03-29
    #
    #       Rrs is an mxn array where n is the number of spectra to be
    #       evaluated as a group and m is the length of wavelength. AVW has n values.
    #
    #   Updated for DESIS 2022-03-28: DAA
    #   Converted to python DA 2022-05-10: DAA

    n = Rrs.shape[1]
    AVW = np.array(avw)
    # Interpolation to QWIP/QCI bands, which are representative of several missions
    test_lambda = np.array([490, 665])
    test_Rrs = np.empty([len(test_lambda), n]) * np.nan
    for i in np.arange(0,n):
        test_Rrs[:,i] = Utilities.interp(wavelength.tolist(), Rrs[:,i].tolist(), test_lambda.tolist())

    QCI = (test_Rrs[1,:] - test_Rrs[0,:])/(test_Rrs[1,:] + test_Rrs[0,:])
    p = [-8.399885e-09,1.715532e-05,-1.301670e-02,4.357838,-5.449532e02]

    # Just generating an array here of the "predicted" QCI based on the AVW
    # image values. We then subtract this from the actual QCI that we
    # calculate above, and get an pixel by pixel QWIP score.
    QCI_pred = p[0]*AVW**4 + p[1]*AVW**3 + p[2]*AVW**2 + p[3]*AVW**1 + p[4]
    QWIP_score = QCI_pred-QCI
    abs_QWIP_score = abs(QWIP_score)

    return abs_QWIP_score




