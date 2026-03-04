'''################################# INTERPOLATION ORIENTED #################################'''

from scipy.interpolate import splev, splrep, interp1d
import numpy as np

def interp(x, y, new_x, kind='linear', fill_value=0.0):
    ''' Wrapper for scipy interp1d that works even if
        values in new_x are outside the range of values in x
            NOTE: This will fill missing values at the beginning and end of data record with
            the nearest neighbor record. Fine for integrated datasets, but may be dramatic
            for some gappy ancillary records of low temporal resolution.'''
    #    If the last value to interp to is larger than the last value interp'ed from,
    #    then append that higher value onto the values to interp from
    n0 = len(x)-1
    n1 = len(new_x)-1
    if new_x[n1] > x[n0]:
        x.append(new_x[n1])
        y.append(y[n0])
    # If the first value to interp to is less than the first value interp'd from,
    # then add that lesser value to the beginning of values to interp from
    if new_x[0] < x[0]:
        x.insert(0, new_x[0])
        y.insert(0, y[0])

    new_y = interp1d(x, y, kind=kind, bounds_error=False, fill_value=fill_value)(new_x)

    return new_y


def interpAngular(x, y, new_x, fill_value="extrapolate"):
    ''' Wrapper for scipy interp1d that works even if
        values in new_x are outside the range of values in x
            NOTE: Except for SOLAR_AZ and SZA, which are extrapolated, this will fill missing values at the
            beginning and end of data record with the nearest actual record. This is fine for integrated
            datasets, but may be dramatic for some gappy ancillary records of lower temporal resolution.
            NOTE: SOLAR_AZ and SZA should no longer be int/extrapolated at all, but recalculated in L1B
            NOTE: REL_AZ (sun to sensor) may be negative and should be 90 - 135, so does not require angular
            interpolation.'''

    # Eliminate NaNs
    whrNan = np.where(np.isnan(y))[0]
    y = np.delete(y,whrNan).tolist()
    x = np.delete(x,whrNan).tolist()

    # Test for all NaNs
    if y:
        if fill_value != "extrapolate": # Only extrapolate SOLAR_AZ and SZA, otherwise keep fill values constant
            # Some angular measurements (like SAS pointing) are + and -. Convert to all +
            for i, value in enumerate(y):
                if value < 0:
                    y[i] = 360 + value

            # If the last value to interp to is larger than the last value interp'ed from,
            # then append that higher value onto the values to interp from
            n0 = len(x)-1
            n1 = len(new_x)-1
            if new_x[n1] > x[n0]:
                #print(new_x[n], x[n])
                # logging.writeLogFileAndPrint('********** Warning: extrapolating to beyond end of data record ********'
                x.append(new_x[n1])
                y.append(y[n0])

            # If the first value to interp to is less than the first value interp'd from,
            # then add that lesser value to the beginning of values to interp from
            if new_x[0] < x[0]:
                #print(new_x[0], x[0])
                # logging.writeLogFileAndPrint('********** Warning: extrapolating to before beginning of data record ******'
                x.insert(0, new_x[0])
                y.insert(0, y[0])

        y_rad = np.deg2rad(y)
        # f = interp1d(x,y_rad,kind='linear', bounds_error=False, fill_value=None)
        f = interp1d(x,y_rad,kind='linear', bounds_error=False, fill_value=fill_value)
        new_y_rad = f(new_x)%(2*np.pi)
        new_y = np.rad2deg(new_y_rad)
    else:
        # All y values were NaNs. Fill in NaNs in new_y
        new_y = np.empty((len(new_x)))
        new_y.fill(np.nan)
        new_y = new_y.tolist()

    return new_y


def interpSpline(x, y, new_x):
    '''Cubic spline interpolation intended to get around the all NaN output from InterpolateUnivariateSpline
        x is original time to be splined, y is the data to be interpolated, new_x is the time to interpolate/spline to
        interpolate.splrep is intolerant of duplicate or non-ascending inputs, and inputs with fewer than 3 points'''
    spl = splrep(x, y)
    new_y = splev(new_x, spl)

    for newy in new_y:
        if np.isnan(newy):
            print("NaN")
    return new_y


def interpFill(x, y, newXList, fillValue=np.nan):
    ''' Used where nearest-neighbor fill is needed instead of interpolation, e.g., STATIONS in L1B.'''
    y = np.array(y)
    x = np.array(x)
    whrNan = np.where(np.isnan(y))[0]
    y = np.delete(y,whrNan)
    x = np.delete(x,whrNan)
    yUnique = np.unique(y) #.tolist()

    newYList = []
    # Populate with nans first, then replace to guarantee value regardless of any or multiple matches
    for newX in newXList:
        newYList.append(fillValue)

    for value in yUnique:
        # NOTE: If only one timestamp is found, it is highly unlikely to pass the test below.
        minX = min(x[y==value])
        maxX = max(x[y==value])

        # # Test conversion reversal
        # datetime_object = datetime.fromtimestamp(maxX)

        if minX == maxX:
            # NOTE: Workaround: buffer the start and stop times of the station by some amount of time
            # Unix time: Number of seconds that have elapsed since January 1, 1970, at 00:00:00 Coordinated Universal Time (UTC)
            minX -= 120
            maxX += 120

        for i, newX in enumerate(newXList):
            if (newX >= minX) and (newX <= maxX):
                newYList[i] = value
    return newYList
