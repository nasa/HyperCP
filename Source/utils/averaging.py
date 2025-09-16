'''################################# AVERAGE ORIENTED #################################'''

import numpy as np

# def windowAverage(data,window_size):
#     min_periods = round(window_size/2)
#     df=pd.DataFrame(data)
#     out=df.rolling(window_size,min_periods,center=True,win_type='boxcar')
#     # out = [item for items in out for item in items] #flattening doesn't work
#     return out


def movingAverage(data, window_size):
    # Window size will be determined experimentally by examining the dark and light data from each instrument.
    """ Noise detection using a low-pass filter.
    https://www.datascience.com/blog/python-anomaly-detection
    Computes moving average using discrete linear convolution of two one dimensional sequences.
    Args:
    -----
            data (pandas.Series): independent variable
            window_size (int): rolling window size
    Returns:
    --------
            ndarray of linear convolution
    References:
    ------------
    [1] Wikipedia, "Convolution", http://en.wikipedia.org/wiki/Convolution.
    [2] API Reference: https://docs.scipy.org/doc/numpy/reference/generated/numpy.convolve.html
    [3] ABE, N., Zadrozny, B., and Langford, J. 2006. Outlier detection by active learning.
        In Proceedings of the 12th ACM SIGKDD International Conference on Knowledge Discovery and
        Data Mining. ACM Press, New York, 504–509
    [4] V Chandola, A Banerjee and V Kumar 2009. Anomaly Detection: A Survey Article No. 15 in ACM
        Computing Surveys"""

    # window = np.ones(int(window_size))/float(window_size)
    # Convolve is not nan-tolerant, so use a mask
    data = np.array(data)
    mask = np.isnan(data)
    K = np.ones(window_size, dtype=int)
    denom = np.convolve(~mask,K)
    denom = np.where(denom != 0, denom, 1) # replace the 0s with 1s to block div0 error; the numerator will be zero anyway

    out = np.convolve(np.where(mask,0,data), K)/denom
    # return np.convolve(data, window, 'same')

    # Slice out one half window on either side; this requires an odd-sized window
    return out[int(np.floor(window_size/2)):-int(np.floor(window_size/2))]