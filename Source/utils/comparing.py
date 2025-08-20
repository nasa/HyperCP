'''################################# COMPARISON ORIENTED #################################'''
from collections import Counter
import numpy as np


def mostFrequent(List):
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]


def find_nearest(array,value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def isFloat(text):
    ''' Checks if a string is a floating point number'''
    try:
        float(text)
        return True
    except ValueError:
        return False

def hasNan(ds):
    ''' Check if datasets or column contain NANs'''
    try:
        keys = ds.data.dtype.fields.keys()
        data = ds.data
        length = ds.data.shape[0]
    except AttributeError:
        keys = ds.keys()  # for if columns passed directly
        data = ds
        length = np.asarray(list(ds.values())).shape[1]
    for k in keys:
        for x in range(length):
            if k != 'Datetime':
                if np.isnan(data[k][x]):
                    return True
    return False


def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.
    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
        to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """
    return np.isnan(y), lambda z: z.nonzero()[0]

def isIncreasing(l):
    ''' Check if the list contains strictly increasing values '''
    return all(x<y for x, y in zip(l, l[1:]))

def datasetNan2Zero(inputArray):
    ''' Workaround nans within a Group.Dataset '''
    # There must be a better way...
    for ens, row in enumerate(inputArray):
        for i, value in enumerate(row):
            if np.isnan(value):
                inputArray[ens][i] = 0.0
    return inputArray

def uniquePairs(pairList):
    '''Eliminate redundant pairs of badTimes 
        Must be list, not np array'''
    if not isinstance(pairList, list):
        pairList = pairList.tolist()
    if len(pairList) > 1:
        newPairs = []
        for pair in pairList:
            if pair not in newPairs:
                newPairs.append(pair)
    else:
        newPairs = pairList
    return newPairs
