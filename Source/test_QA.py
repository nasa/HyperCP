import numpy as np
import scipy.interpolate

from L2wei_QA import QAscores_5Bands

# Rrs = np.array([0.005, 0.007, 0.009, 0.010, 0.004])
Rrs = np.array([ [0.005, 0.007, 0.009, 0.010, 0.004], \
    [0.005, 0.007, 0.009, 0.010, 0.004] ])
# wave = np.array([412, 443, 488, 551, 670])
# wave = np.array([412, 443, 488, 551, 670])
wave = np.array([ [412, 443, 488, 551, 670], \
    [412, 443, 488, 551, 670] ])

test_lambda = np.array([412,443,488,551,670])
if Rrs.ndim > 1:
    test_Rrs = np.empty((Rrs.shape[0],len(test_lambda)))
else:
    # Always cast into a multidimensional array, even if only passing one vector
    test_Rrs = np.empty(( 1, len(test_lambda)))
test_Rrs[:] = np.nan
for i, Rrsi in enumerate(Rrs):
    test_Rrs[i,:] = scipy.interpolate.interp1d(wave[i,:], Rrsi)(test_lambda)

test = QAscores_5Bands(test_Rrs, test_lambda)
print(test)
# maxCos, cos, clusterID, totScore = QAscores_5Bands(test_Rrs, test_lambda)