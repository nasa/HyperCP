'''################################# DATETIME ORIENTED #################################'''

from datetime import datetime, timedelta, timezone
import pytz
import numpy as np

import Source.utils.loggingHCP as logging
from Source.ConfigFile import ConfigFile

def fixDarkTimes(darkGroup,lightGroup):
    ''' Find the nearest timestamp in the light data to each dark measurements (Sea-Bird) '''

    darkDatetime = darkGroup.datasets["DATETIME"].data
    lightDatetime = lightGroup.datasets["DATETIME"].data

    dateTagNew = darkGroup.addDataset('DATETAG_ADJUSTED')
    timeTagNew = darkGroup.addDataset('TIMETAG2_ADJUSTED')
    dateTimeNew = darkGroup.addDataset('DATETIME_ADJUSTED')

    is_sorted = lambda x: np.all(x[:-1] <= x[1:])
    if is_sorted(lightDatetime) and is_sorted(darkDatetime):
        iLight = np.searchsorted(lightDatetime, darkDatetime, side="left")
        iLight[iLight == len(lightDatetime)] = len(lightDatetime) - 1  # Edge case
    else:
        iLight = np.empty(len(darkDatetime), dtype=int)
        lightDatetimeArray = np.asarray(lightDatetime)
        for i, darkTime in enumerate(darkDatetime):
            iLight[i] = (np.abs(lightDatetimeArray - darkTime)).argmin()

    dateTagNew.data = lightGroup.datasets['DATETAG'].data[iLight]
    timeTagNew.data = lightGroup.datasets['TIMETAG2'].data[iLight]
    dateTimeNew.data = np.array(lightGroup.datasets['DATETIME'].data)[iLight]

    return darkGroup


def dmToDd(dm, direction, *, precision=6):
    '''# Converts degrees minutes to decimal degrees format'''
    d = int(dm/100)
    m = dm-d*100
    dd = d + m/60
    if direction == b'W' or direction == b'S':
        dd *= -1
    dd = round(dd, precision)
    return dd


def ddToDm(dd):
    '''Converts decimal degrees to degrees minutes format'''
    d = int(dd)
    m = (dd - d)*60
    dm = (d*100) + m
    return dm


def utcToSec(utc):
    '''Converts GPS UTC time (HHMMSS.ds; i.e. 99 ds after midnight is 000000.99)to seconds
    # Note: Does not support multiple days'''
    # Use zfill to ensure correct width, fixes bug when hour is 0 (12 am)
    t = str(int(utc)).zfill(6)
    # print(t)
    #print(t[:2], t[2:4], t[4:])
    h = int(t[:2])
    m = int(t[2:4])
    s = float(t[4:])
    return ((h*60)+m)*60+s


def utcToDateTime(dt, utc):
    '''Converts datetime date and UTC (HHMMSS.ds) to datetime (uses microseconds)'''
    # Use zfill to ensure correct width, fixes bug when hour is 0 (12 am)
    num, dec = str(float(utc)).split('.')
    t = num.zfill(6)
    h = int(t[:2])
    m = int(t[2:4])
    s = int(t[4:6])
    us = 10000*int(dec) # i.e. 0.55 s = 550,000 us
    return datetime(dt.year,dt.month,dt.day,h,m,s,us,tzinfo=timezone.utc)


def dateTagToDate(dateTag):
    '''# Converts datetag (YYYYDDD) to date string'''
    dt = datetime.strptime(str(int(dateTag)), '%Y%j')
    # timezone = pytz.utc
    dt = pytz.utc.localize(dt)
    return dt.strftime('%Y%m%d')


def dateTagToDateTime(dateTag):
    '''# Converts datetag (YYYYDDD) to datetime'''
    dt = datetime.strptime(str(int(dateTag)), '%Y%j')
    # timezone = pytz.utc
    dt = pytz.utc.localize(dt)
    return dt


def secToUtc(sec):
    '''# Converts seconds of the day (NOT GPS UTCPOS) to GPS UTC (HHMMSS.SS)'''
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return float("%d%02d%02d" % (h, m, s))


def secToTimeTag2(sec):
    '''# Converts seconds of the day to TimeTag2 (HHMMSSmmm; i.e. 0.999 sec after midnight = 000000999)'''
    t = sec * 1000
    s, ms = divmod(t, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return int("%d%02d%02d%03d" % (h, m, s, ms))


def timeTag2ToSec(tt2):
    '''# Converts TimeTag2 (HHMMSSmmm) to seconds'''
    t = str(int(tt2)).zfill(9)
    h = int(t[:2])
    m = int(t[2:4])
    s = int(t[4:6])
    ms = int(t[6:])
    # print(h, m, s, ms)
    return ((h*60)+m)*60+s+(float(ms)/1000.0)


def timeTag2ToDateTime(dt,tt2):
    '''# Converts datetime.date and TimeTag2 (HHMMSSmmm) to datetime'''
    t = str(int(tt2)).zfill(9)
    h = int(t[:2])
    m = int(t[2:4])
    s = int(t[4:6])
    us = 1000*int(t[6:])
    return datetime(dt.year,dt.month,dt.day,h,m,s,us,tzinfo=timezone.utc)


def datetime2TimeTag2(dt):
    '''# Converts datetime to Timetag2 (HHMMSSmmm)'''
    h = dt.hour
    m = dt.minute
    s = dt.second
    ms = dt.microsecond/1000
    return int("%d%02d%02d%03d" % (h, m, s, ms))


def datetime2DateTag(dt):
    '''# Converts datetime to Datetag'''
    y = dt.year
    day = dt.timetuple().tm_yday

    return int("%d%03d" % (y, day))


def timestampToSec(timestamp):
    '''# Converts HDFRoot timestamp attribute to seconds'''
    timei = timestamp.split(" ")[3]
    t = timei.split(":")
    h = int(t[0])
    m = int(t[1])
    s = int(t[2])
    return ((h*60)+m)*60+s


def gpsDateToDatetime(year, gpsDate):
    '''# Convert GPRMC Date to Datetag'''
    date = str(gpsDate).zfill(6)
    day = int(date[:2])
    mon = int(date[2:4])
    return datetime(year,mon,day,0,0,0,0,tzinfo=timezone.utc)


def rootAddDateTime(node):
    ''' Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        Also screens for nonsense timetags like 0.0 or NaN, and datetags that are not
        in the 20th or 21st centuries '''

    for gp in node.groups:
        # print(gp.id)
        # Don't add to the following:
        noAddList = ("SOLARTRACKER_STATUS","SATMSG.tdf","CAL_COEF")
        if gp.id not in noAddList and "UNCERT" not in gp.id and ".cal.CE" not in gp.id:
            timeData = gp.getDataset("TIMETAG2").data["NONE"].tolist()
            dateTag = gp.getDataset("DATETAG").data["NONE"].tolist()
            timeStamp = []
            for i, timei in enumerate(timeData):
                # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
                # Filter for aberrant Datetags
                t = str(int(timei)).zfill(9)
                h = int(t[:2])
                m = int(t[2:4])
                s = int(t[4:6])

                if (str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20")) \
                    and timei != 0.0 and not np.isnan(timei) \
                        and h < 60 and m < 60 and s < 60:
                    dt = dateTagToDateTime(dateTag[i])
                    timeStamp.append(timeTag2ToDateTime(dt, timei))
                else:
                    logging.writeLogFileAndPrint(f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}")
                    gp.datasetDeleteRow(i)

            dateTime = gp.addDataset("DATETIME")
            dateTime.data = timeStamp
    return node


def groupAddDateTime(gp):
    ''' Add a dataset to one group for DATETIME, as defined by TIMETAG2 and DATETAG
        Also screens for nonsense timetags like 0.0 or NaN, and datetags that are not
        in the 20th or 21st centuries '''
    if gp.id != "SOLARTRACKER_STATUS" and "UNCERT" not in gp.id and gp.id != "SATMSG.tdf": # No valid timestamps in STATUS
        timeData = gp.getDataset("TIMETAG2").data["NONE"].tolist()
        dateTag = gp.getDataset("DATETAG").data["NONE"].tolist()
        timeStamp = []
        for i, timei in enumerate(timeData):
            # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
            # Filter for aberrant Datetags
            t = str(int(timei)).zfill(9)
            h = int(t[:2])
            m = int(t[2:4])
            s = int(t[4:6])

            if (str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20")) \
                and timei != 0.0 and not np.isnan(timei) \
                    and h < 60 and m < 60 and s < 60:

                dt = dateTagToDateTime(dateTag[i])
                timeStamp.append(timeTag2ToDateTime(dt, timei))
            else:
                logging.writeLogFileAndPrint(f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}")
                gp.datasetDeleteRow(i)

        dateTime = gp.addDataset("DATETIME")
        dateTime.data = timeStamp
    return gp


def rootAddDateTimeCol(node):
    ''' Add a data column to each group dataset for DATETIME, as defined by TIMETAG2 and DATETAG
        Also screens for nonsense timetags like 0.0 or NaN, and datetags that are not
        in the 20th or 21st centuries'''

    for gp in node.groups:
        if gp.id != "SOLARTRACKER_STATUS" and "UNCERT" not in gp.id and gp.id != "SATMSG.tdf": # No valid timestamps in STATUS

            # Provision for L1AQC carry-over groups. These do not have Datetag or Timetag2
            #   dataset, but still have DATETAG and TIMETAG2 datasets
            if '_L1AQC' not in gp.id:
                for ds in gp.datasets:
                    # Make sure all datasets have been transcribed to columns
                    gp.datasets[ds].datasetToColumns()

                    if 'Datetime' not in gp.datasets[ds].columns:
                        if 'Timetag2' in gp.datasets[ds].columns:  # changed to ensure the new (irr)radiance groups don't throw errors
                            timeData = gp.datasets[ds].columns["Timetag2"]
                            dateTag = gp.datasets[ds].columns["Datetag"]

                            timeStamp = []
                            for i, timei in enumerate(timeData):
                                # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
                                # Filter for aberrant Datetags
                                if (str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20")) \
                                    and timei != 0.0 and not np.isnan(timei):

                                    dt = dateTagToDateTime(dateTag[i])
                                    timeStamp.append(timeTag2ToDateTime(dt, timei))
                                else:
                                    gp.datasetDeleteRow(i)
                                    logging.writeLogFileAndPrint(f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}")
                            gp.datasets[ds].columns["Datetime"] = timeStamp
                            gp.datasets[ds].columns.move_to_end('Datetime', last=False)
                            gp.datasets[ds].columnsToDataset()
            else:
                # L1AQC
                # Add a special dataset
                for ds in gp.datasets:
                    # Make sure all datasets have been transcribed to columns
                    if ds != "DATETIME":
                        gp.datasets[ds].datasetToColumns()

                gp.addDataset('Timestamp')
                dateTag = gp.datasets['DATETAG'].columns["NONE"]
                timeData = gp.datasets['TIMETAG2'].columns["NONE"]
                gp.datasets['Timestamp'].columns['Datetag'] = dateTag
                gp.datasets['Timestamp'].columns['Timetag2'] = timeData
                gp.datasets['Timestamp'].columnsToDataset()

                timeStamp = []
                for i, timei in enumerate(timeData):
                    # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
                    # Filter for aberrant Datetags
                    if (str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20")) \
                        and timei != 0.0 and not np.isnan(timei):

                        dt = dateTagToDateTime(dateTag[i])
                        timeStamp.append(timeTag2ToDateTime(dt, timei))
                    else:
                        gp.datasetDeleteRow(i) # L1AQC datasets all have the same i
                        logging.writeLogFileAndPrint(f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}")
                # This will be the only dataset structure like a higher level with time/date columns
                gp.datasets['Timestamp'].columns["Datetime"] = timeStamp
                gp.datasets['Timestamp'].columns.move_to_end('Datetime', last=False)
                gp.datasets['Timestamp'].columnsToDataset()

    return node


def rawDataAddDateTime(node):
    '''# Add a data column to each group dataset for DATETIME, as defined by TIMETAG2 and DATETAG
    # Also screens for nonsense timetags like 0.0 or NaN, and datetags that are not
    # in the 20th or 21st centuries, specifically for raw data groups - used in L2 processing.'''
    for gp in node.groups:
        if "L1AQC" in gp.id:
            timeData = gp.getDataset("TIMETAG2").data["NONE"].tolist()
            dateTag = gp.getDataset("DATETAG").data["NONE"].tolist()
            timeStamp = []
            for i, timei in enumerate(timeData):
                # Converts from TT2 (hhmmssmss. UTC) and Datetag (YYYYDOY UTC) to datetime
                # Filter for aberrant Datetags
                t = str(int(timei)).zfill(9)
                h = int(t[:2])
                m = int(t[2:4])
                s = int(t[4:6])

                if (str(dateTag[i]).startswith("19") or str(dateTag[i]).startswith("20")) \
                    and timei != 0.0 and not np.isnan(timei) \
                        and h < 60 and m < 60 and s < 60:

                    dt = dateTagToDateTime(dateTag[i])
                    timeStamp.append(timeTag2ToDateTime(dt, timei))
                else:
                    logging.writeLogFileAndPrint(f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}")
                    gp.datasetDeleteRow(i)

            dateTime = gp.addDataset("DATETIME")
            dateTime.data = timeStamp
    return node


def fixDateTime(gp):
    '''Remove records if values of DATETIME are not strictly increasing
    (strictly increasing values required for interpolation)'''
    dateTime = gp.getDataset("DATETIME").data
    # Test for strictly ascending values
    # Not sensitive to UTC midnight (i.e. in datetime format)
    total = len(dateTime)
    globalTotal = total
    if total >= 2:
        # Check the first element prior to looping over rest
        i = 0
        if dateTime[i+1] <= dateTime[i]:
            gp.datasetDeleteRow(i)
            # del dateTime[i] # I'm fuzzy on why this is necessary; not a pointer?
            dateTime = gp.getDataset("DATETIME").data
            total = total - 1
            logging.writeLogFileAndPrint(f'Out of order timestamp deleted at {i}')

            #In case we went from 2 to 1 element on the first element,
            if total == 1:
                logging.writeLogFileAndPrint(f'************Too few records ({total}) to test for ascending timestamps. Exiting.')
                return False

        i = 1
        while i < total:
            if dateTime[i] <= dateTime[i-1]:
                if dateTime[i] == dateTime[i-1]:
                    # BUG?:Same values of consecutive TT2s are shockingly common. Confirmed
                    #   that 1) they exist from L1A, and 2) sensor data changes while TT2 stays the same
                    #
                    logging.writeLogFileAndPrint(f'Duplicate row deleted at {i}')
                else:
                    logging.writeLogFileAndPrint(f'WARNING: Out of order row deleted at {i}; this should not happen after sortDateTime')

                gp.datasetDeleteRow(i)
                # del dateTime[i] # I'm fuzzy on why this is necessary; not a pointer?
                dateTime = gp.getDataset("DATETIME").data
                total = total - 1

                continue # goto while test skipping i incrementation. dateTime[i] is now the next value.
            i += 1
    else:
        logging.writeLogFileAndPrint(f'************Too few records ({total}) to test for ascending timestamps. Exiting.')
        return False
    if (globalTotal - total) > 0:
        logging.writeLogFileAndPrint(f'Data eliminated for non-increasing timestamps: {100*(globalTotal - total)/globalTotal:3.1f}%')

    return True


def SASUTCOffset(node):
    for gp in node.groups:
        if not gp.id.startswith("SATMSG"): # Don't convert these strings to datasets.

            timeStamp = gp.datasets["DATETIME"].data
            timeStampNew = [time + datetime.timedelta(hours=ConfigFile.settings["fL1aUTCOffset"]) for time in timeStamp]
            TimeTag2 = [datetime2TimeTag2(dt) for dt in timeStampNew]
            DateTag = [datetime2DateTag(dt) for dt in timeStampNew]
            gp.datasets["DATETIME"].data = timeStampNew
            gp.datasets["DATETAG"].data["NONE"] = DateTag
            gp.datasets["DATETAG"].datasetToColumns()
            gp.datasets["TIMETAG2"].data["NONE"] = TimeTag2
            gp.datasets["TIMETAG2"].datasetToColumns()
    return node


def getDateTime(gp):
    ''' Used in deglitching routines '''
    dateTagDS = gp.getDataset('DATETAG')
    dateTags = dateTagDS.data["NONE"].tolist()
    timeTagDS = gp.getDataset('TIMETAG2')
    timeTags = timeTagDS.data["NONE"].tolist()
    # Conversion not set up for vectors, loop it
    dateTime=[]
    for i, dateTag in enumerate(dateTags):
        dt = dateTagToDateTime(dateTag)
        dateTime.append(timeTag2ToDateTime(dt,timeTags[i]))

    return dateTime


def catConsecutiveBadTimes(badTimes, dateTime):
    '''Test for the existence of consecutive, singleton records that could be 
        concatonated into a time span. This can only work after L1B cross-sensor time interpolation.'''
    newBadTimes = []
    for iBT, badTime in enumerate(badTimes):
        if iBT == 0:
            newBadTimes.append(badTime)
        else:
            iDT = dateTime.index(newBadTimes[-1][1])# end time of last window
            iDT2 = dateTime.index(badTime[0])
            if iDT2 == iDT +1:
                # Consecutive
                newBadTimes[-1][1] = badTime[1]
            else:
                newBadTimes.append(badTime)
    return newBadTimes


def findGaps_dateTime(DT1,DT2,threshold):
    ''' Test whether one DT2 datetime has a gap > threshold [seconds] 
        relative to DT1. '''
    bTs = []
    start = -1
    i, index, stop = 0,0,0
    tThreshold = timedelta(seconds=threshold)

    # See below for faster conversions
    np_dTT = np.array(DT2, dtype=np.datetime64)
    np_dTT.sort()

    np_dTM = np.array(DT1, dtype=np.datetime64)
    pos = np.searchsorted(np_dTT, np_dTM, side='right')

    # Consider the 3 items close the the position found.
    # We can probably only consider 2 of them but this is simpler and less bug-prone.
    pos1 = np.maximum(pos-1, 0)
    pos2 = np.minimum(pos, np_dTT.size-1)
    pos3 = np.minimum(pos+1, np_dTT.size-1)
    tDiff1 = np.abs(np_dTT[pos1] - np_dTM)
    tDiff2 = np.abs(np_dTT[pos2] - np_dTM)
    tDiff3 = np.abs(np_dTT[pos3] - np_dTM)
    tMin = np.minimum(tDiff1, tDiff2, tDiff3)

    for index in range(len(np_dTM)):
        if tMin[index] > tThreshold:
            i += 1
            if start == -1:
                start = index
            stop = index
        else:
            if start != -1:
                startstop = [DT1[start],DT1[stop]]
                logging.writeLogFileAndPrint(f'   Flag data from {startstop[0]} to {startstop[1]}')
                bTs.append(startstop)
                start = -1

    if start != -1 and stop == index: # Records from a mid-point to the end are bad
        startstop = [DT1[start],DT1[stop]]
        bTs.append(startstop)
        logging.writeLogFileAndPrint(f'   Flag additional data from {startstop[0]} to {startstop[1]}')

    if start==0 and stop==index: # All records are bad
        return False

    return bTs


def sortDateTime(group):
    ''' Sort all data in group chronologically based on datetime '''

    if group.id != "SOLARTRACKER_STATUS" and group.id != "CAL_COEF":
        timeStamp = group.getDataset("DATETIME").data
        tz = pytz.timezone('UTC')
        np_dT = np.array(timeStamp, dtype=np.datetime64)
        sortIndex = np.argsort(np_dT)
        np_dT_sorted = np_dT[sortIndex]
        datetime_list = np_dT_sorted.astype('datetime64[us]').tolist()
        datetime_list = [tz.localize(x) for x in datetime_list]
        for ds in group.datasets:
            if len(group.datasets[ds].data) == len(np_dT):
                if ds == 'DATETIME':
                    group.datasets[ds].data = datetime_list
                else:
                    group.datasets[ds].data = group.datasets[ds].data[sortIndex]

        logging.writeLogFileAndPrint(f'Screening {group.id} for clean timestamps.')
        if not fixDateTime(group):
            logging.writeLogFileAndPrint(f'***********Too few records in {group.id} to continue after timestamp correction. Exiting.')
            return None
    return group