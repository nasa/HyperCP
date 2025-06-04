""" A cornucopia of addition methods """
import os
from datetime import datetime, timedelta, timezone
import collections
from collections import Counter
import csv
import re
import hashlib
from tqdm import tqdm
import requests
from PyQt5.QtWidgets import QMessageBox
import pytz
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
import scipy.interpolate
from scipy.interpolate import splev, splrep
import scipy as sp
import pandas as pd
from pandas.plotting import register_matplotlib_converters

from Source import PACKAGE_DIR as dirPath
from Source.SB_support import readSB
from Source.HDFRoot import HDFRoot
from Source.ConfigFile import ConfigFile
from Source.MainConfig import MainConfig
# from Source.Uncertainty_Visualiser import Show_Uncertainties  # class for uncertainty visualisation plots
register_matplotlib_converters()

# This gets reset later in Controller.processSingleLevel to reflect the file being processed.
if "LOGFILE" not in os.environ:
    os.environ["LOGFILE"] = "temp.log"

class Utilities:
    """A catchall class for HyperCP utilities"""

    @staticmethod
    def downloadZhangLUT(fpfZhangLUT, force=False):
        infoText = "  NEW INSTALLATION\nGlint LUT required.\nClick OK to download.\n\nTHIS IS A 258 MB DOWNLOAD.\n\n\
        If canceled, Zhang et al. (2017) glint correction will fail. If download fails, a link and instructions will be provided in the terminal."
        YNReply = True if force else Utilities.YNWindow("Database Download", infoText) == QMessageBox.Ok
        if YNReply:

            # url = "https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Zhang_rho_LUT.nc"
            url = "https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Z17_LUT_v2.nc"
            download_session = requests.Session()
            try:
                file_size = int(
                    download_session.head(url).headers["Content-length"]
                )
                file_size_read = round(int(file_size) / (1024**3), 2)
                print(
                    f"##### Downloading {file_size_read}GB data file. ##### "
                )
                download_file = download_session.get(url, stream=True)
                download_file.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print("Error in download_file:", err)
            if download_file.ok:
                progress_bar = tqdm(
                    total=file_size, unit="iB", unit_scale=True, unit_divisor=1024
                )
                with open(fpfZhangLUT, "wb") as f:
                    for chunk in download_file.iter_content(chunk_size=1024):
                        progress_bar.update(len(chunk))
                        f.write(chunk)
                progress_bar.close()

                # Check the hash of the file
                print('Checking file...')
                thisHash = Utilities.md5(fpfZhangLUT)
                if thisHash == '1a33ed647d9c7359b0800915bd0229c7':
                    print('File checks out.')
                else:
                    print(f'Error in downloaded file {fpfZhangLUT}. Recommend you delete the downloaded file and try again.')
                    print(
                    f"Try download from {url} (e.g. copy paste this URL in your internet browser) and place under"
                    f" {dirPath}/Data directory."
                )

            else:
                print(
                    "Failed to download core databases."
                    f"Try download from {url} (e.g. copy paste this URL in your internet browser) and place under"
                    f" {dirPath}/Data directory."
                )

    @staticmethod
    def downloadZhangDB(fpfZhang, force=False):
        infoText = "  NEW INSTALLATION\nGlint database required.\nClick OK to download.\n\nWARNING: THIS IS A 2.8 GB DOWNLOAD.\n\n\
        If canceled, Zhang et al. (2017) glint correction will fail. If download fails, a link and instructions will be provided in the terminal."
        YNReply = True if force else Utilities.YNWindow("Database Download", infoText) == QMessageBox.Ok
        if YNReply:

            url = "https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Zhang_rho_db_expanded.mat"
            download_session = requests.Session()
            try:
                file_size = int(
                    download_session.head(url).headers["Content-length"]
                )
                file_size_read = round(int(file_size) / (1024**3), 2)
                print(
                    f"##### Downloading {file_size_read}GB data file. This could take several minutes. ##### "
                )
                download_file = download_session.get(url, stream=True)
                download_file.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print("Error in download_file:", err)
            if download_file.ok:
                progress_bar = tqdm(
                    total=file_size, unit="iB", unit_scale=True, unit_divisor=1024
                )
                with open(fpfZhang, "wb") as f:
                    for chunk in download_file.iter_content(chunk_size=1024):
                        progress_bar.update(len(chunk))
                        f.write(chunk)
                progress_bar.close()

                # Check the hash of the file
                print('Checking file...')
                thisHash = Utilities.md5(fpfZhang)
                if thisHash == 'e4c155f8ce92dcfa012a450a56b64e28':
                    print('File checks out.')
                else:
                    print(f'Error in downloaded file {fpfZhang}. Recommend you delete the downloaded file and try again.')
                    print(
                    f"Try download from {url} (e.g. copy paste this URL in your internet browser) and place under"
                    f" {dirPath}/Data directory."
                )

            else:
                print(
                    "Failed to download core databases."
                    f"Try download from {url} (e.g. copy paste this URL in your internet browser) and place under"
                    f" {dirPath}/Data directory."
                )

    @staticmethod
    def md5(fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()                

    @staticmethod
    def checkInputFiles(inFilePath, level="L1A+"):
        if ConfigFile.settings['SensorType'].lower() == 'trios':
            flag_Trios = True
        else:
            flag_Trios = False
        if flag_Trios and level == "L1A":
            for fp in inFilePath:
                if not os.path.isfile(fp):
                    msg = 'No such file...'
                    if not MainConfig.settings['popQuery']:
                        Utilities.errorWindow("File Error", msg)
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
                else:
                    return True
        else:
            if not os.path.isfile(inFilePath):
                msg = 'No such file...'
                if not MainConfig.settings['popQuery']:
                    Utilities.errorWindow("File Error", msg)
                print(msg)
                Utilities.writeLogFile(msg)
                return False
            else:
                return True

    @staticmethod
    def checkOutputFiles(outFilePath):
        if os.path.isfile(outFilePath):
            modTime = os.path.getmtime(outFilePath)
            nowTime = datetime.now()
            if nowTime.timestamp() - modTime < 60: # If the file exists and was created in the last minute...
                # msg = f'{level} file produced: \n {outFilePath}'
                # print(msg)
                # Utilities.writeLogFile(msg)
                msg = f'Process Single Level: {outFilePath} - SUCCESSFUL'
                print(msg)
                Utilities.writeLogFile(msg)
            else:
                msg = f'Process Single Level: {outFilePath} - NOT SUCCESSFUL'
                print(msg)
                Utilities.writeLogFile(msg)
        else:
            msg = f'Process Single Level: {outFilePath} - NOT SUCCESSFUL'
            print(msg)
            Utilities.writeLogFile(msg)


    @staticmethod
    def SASUTCOffset(node):
        for gp in node.groups:
            if not gp.id.startswith("SATMSG"): # Don't convert these strings to datasets.

                timeStamp = gp.datasets["DATETIME"].data
                timeStampNew = [time + datetime.timedelta(hours=ConfigFile.settings["fL1aUTCOffset"]) for time in timeStamp]
                TimeTag2 = [Utilities.datetime2TimeTag2(dt) for dt in timeStampNew]
                DateTag = [Utilities.datetime2DateTag(dt) for dt in timeStampNew]
                gp.datasets["DATETIME"].data = timeStampNew
                gp.datasets["DATETAG"].data["NONE"] = DateTag
                gp.datasets["DATETAG"].datasetToColumns()
                gp.datasets["TIMETAG2"].data["NONE"] = TimeTag2
                gp.datasets["TIMETAG2"].datasetToColumns()

        return node


    @staticmethod
    def TSIS_1(dateTag, wavelength, F0_raw=None, F0_unc_raw=None, wv_raw=None):
        def dop(year):
            # day of perihelion
            years = list(range(2001,2031))
            key = [str(x) for x in years]
            day = [4, 2, 4, 4, 2, 4, 3, 2, 4, 3, 3, 5, 2, 4, 4, 2, 4, 3, 3, 5, 2, 4, 4, 3, 4, 3, 3, 5, 2, 3]
            dop = {key[i]: day[i] for i in range(0, len(key))}
            result = dop[str(year)]
            return result

        if F0_raw is None:
            # Only read this if we haven't already read it in
            fp = 'Data/hybrid_reference_spectrum_p1nm_resolution_c2020-09-21_with_unc.nc'
            # fp = 'Data/Thuillier_F0.sb'
            # print("SB_support.readSB: " + fp)
            # print("Reading : " + fp)
            if not HDFRoot.readHDF5(fp):
                msg = "Unable to read TSIS-1 netcdf file."
                print(msg)
                Utilities.writeLogFile(msg)
                return None
            else:
                F0_hybrid = HDFRoot.readHDF5(fp)
                # F0_raw = np.array(Thuillier.data['esun']) # uW cm^-2 nm^-1
                # wv_raw = np.array(Thuillier.data['wavelength'])
                for ds in F0_hybrid.datasets:
                    if ds.id == 'SSI':
                        F0_raw = ds.data        #  W  m^-2 nm^-1
                        F0_raw = F0_raw * 100 # uW cm^-2 nm^-1
                    if ds.id == 'SSI_UNC':
                        F0_unc_raw = ds.data        #  W  m^-2 nm^-1
                        F0_unc_raw = F0_unc_raw * 100 # uW cm^-2 nm^-1
                    if ds.id == 'Vacuum Wavelength':
                        wv_raw =ds.data

        # Earth-Sun distance
        day = int(str(dateTag)[4:7])
        year = int(str(dateTag)[0:4])
        eccentricity = 0.01672
        dayFactor = 360/365.256363
        dayOfPerihelion = dop(year)
        dES = 1-eccentricity*np.cos(dayFactor*(day-dayOfPerihelion)) # in AU
        F0_fs = F0_raw*dES

        # Smooth F0 to 10 nm windows centered on data wavelengths
        avg_f0 = np.empty(len(wavelength))
        avg_f0[:] = np.nan
        avg_f0_unc = avg_f0.copy()
        for i, wv in enumerate(wavelength):
            idx = np.where((wv_raw >= wv-5.) & ( wv_raw <= wv+5.))
            if idx:
                avg_f0[i] = np.mean(F0_fs[idx])
                avg_f0_unc[i] = np.mean(F0_unc_raw[idx])
        # F0 = sp.interpolate.interp1d(wv_raw, F0_fs)(wavelength)

        # Use the strings for the F0 dict
        wavelengthStr = [str(wave) for wave in wavelength]
        F0 = collections.OrderedDict(zip(wavelengthStr, avg_f0))
        F0_unc = collections.OrderedDict(zip(wavelengthStr, avg_f0_unc))

        return F0, F0_unc, F0_raw, F0_unc_raw, wv_raw


    @staticmethod
    def Thuillier(dateTag, wavelength):
        def dop(year):
            # day of perihelion
            years = list(range(2001,2031))
            key = [str(x) for x in years]
            day = [4, 2, 4, 4, 2, 4, 3, 2, 4, 3, 3, 5, 2, 4, 4, 2, 4, 3, 3, 5, 2, 4, 4, 3, 4, 3, 3, 5, 2, 3]
            dop = {key[i]: day[i] for i in range(0, len(key))}
            result = dop[str(year)]
            return result

        fp = 'Data/Thuillier_F0.sb'
        print("SB_support.readSB: " + fp)
        if not readSB(fp, no_warn=True):
            msg = "Unable to read Thuillier file. Make sure it is in SeaBASS format."
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        else:
            Thuillier = readSB(fp, no_warn=True)
            F0_raw = np.array(Thuillier.data['esun']) # uW cm^-2 nm^-1
            wv_raw = np.array(Thuillier.data['wavelength'])
            # Earth-Sun distance
            day = int(str(dateTag)[4:7])
            year = int(str(dateTag)[0:4])
            eccentricity = 0.01672
            dayFactor = 360/365.256363
            dayOfPerihelion = dop(year)
            dES = 1-eccentricity*np.cos(dayFactor*(day-dayOfPerihelion)) # in AU
            F0_fs = F0_raw*dES

            F0 = sp.interpolate.interp1d(wv_raw, F0_fs)(wavelength)
            # Use the strings for the F0 dict
            wavelengthStr = [str(wave) for wave in wavelength]
            F0 = collections.OrderedDict(zip(wavelengthStr, F0))

        return F0


    @staticmethod
    def mostFrequent(List):
        occurence_count = Counter(List)
        return occurence_count.most_common(1)[0][0]


    @staticmethod
    def find_nearest(array,value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx


    @staticmethod
    def errorWindow(winText,errorText):
        if os.environ["HYPERINSPACE_CMD"].lower() == 'true':
            return
        msgBox = QMessageBox()
        # msgBox.setIcon(QMessageBox.Information)
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText(errorText)
        msgBox.setWindowTitle(winText)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    @staticmethod
    def YNWindow(winText,infoText):
        if os.environ["HYPERINSPACE_CMD"].lower() == 'true':
            return QMessageBox.Ok  # Assume positive answer to keep processing in command line mode (no X)
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(infoText)
        msgBox.setWindowTitle(winText)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = msgBox.exec_()
        return returnValue

    @staticmethod
    def writeLogFile(logText, mode='a'):
        if not os.path.exists('Logs'):
            import logging
            logging.getLogger().warning('Made directory: Logs/')
            os.mkdir('Logs')
        with open('Logs/' + os.environ["LOGFILE"], mode, encoding="utf-8") as logFile:
            logFile.write(logText + "\n")

    # Converts degrees minutes to decimal degrees format
    @staticmethod
    def dmToDd(dm, direction, *, precision=6):
        d = int(dm/100)
        m = dm-d*100
        dd = d + m/60
        if direction == b'W' or direction == b'S':
            dd *= -1
        dd = round(dd, precision)
        return dd

    # Converts decimal degrees to degrees minutes format
    @staticmethod
    def ddToDm(dd):
        d = int(dd)
        m = (dd - d)*60
        dm = (d*100) + m
        return dm


    # Converts GPS UTC time (HHMMSS.ds; i.e. 99 ds after midnight is 000000.99)to seconds
    # Note: Does not support multiple days
    @staticmethod
    def utcToSec(utc):
        # Use zfill to ensure correct width, fixes bug when hour is 0 (12 am)
        t = str(int(utc)).zfill(6)
        # print(t)
        #print(t[:2], t[2:4], t[4:])
        h = int(t[:2])
        m = int(t[2:4])
        s = float(t[4:])
        return ((h*60)+m)*60+s

    # Converts datetime date and UTC (HHMMSS.ds) to datetime (uses microseconds)
    @staticmethod
    def utcToDateTime(dt, utc):
        # Use zfill to ensure correct width, fixes bug when hour is 0 (12 am)
        num, dec = str(float(utc)).split('.')
        t = num.zfill(6)
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:6])
        us = 10000*int(dec) # i.e. 0.55 s = 550,000 us
        return datetime(dt.year,dt.month,dt.day,h,m,s,us,tzinfo=timezone.utc)

    # Converts datetag (YYYYDDD) to date string
    @staticmethod
    def dateTagToDate(dateTag):
        dt = datetime.strptime(str(int(dateTag)), '%Y%j')
        timezone = pytz.utc
        dt = timezone.localize(dt)
        return dt.strftime('%Y%m%d')

    # Converts datetag (YYYYDDD) to datetime
    @staticmethod
    def dateTagToDateTime(dateTag):
        dt = datetime.strptime(str(int(dateTag)), '%Y%j')
        timezone = pytz.utc
        dt = timezone.localize(dt)
        return dt

    # Converts seconds of the day (NOT GPS UTCPOS) to GPS UTC (HHMMSS.SS)
    @staticmethod
    def secToUtc(sec):
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return float("%d%02d%02d" % (h, m, s))

    # Converts seconds of the day to TimeTag2 (HHMMSSmmm; i.e. 0.999 sec after midnight = 000000999)
    @staticmethod
    def secToTimeTag2(sec):
        #return float(time.strftime("%H%M%S", time.gmtime(sec)))
        t = sec * 1000
        s, ms = divmod(t, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return int("%d%02d%02d%03d" % (h, m, s, ms))

    # Converts TimeTag2 (HHMMSSmmm) to seconds
    @staticmethod
    def timeTag2ToSec(tt2):
        t = str(int(tt2)).zfill(9)
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:6])
        ms = int(t[6:])
        # print(h, m, s, ms)
        return ((h*60)+m)*60+s+(float(ms)/1000.0)

    # Converts datetime.date and TimeTag2 (HHMMSSmmm) to datetime
    @staticmethod
    def timeTag2ToDateTime(dt,tt2):
        t = str(int(tt2)).zfill(9)
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:6])
        us = 1000*int(t[6:])
        return datetime(dt.year,dt.month,dt.day,h,m,s,us,tzinfo=timezone.utc)

    # Converts datetime to Timetag2 (HHMMSSmmm)
    @staticmethod
    def datetime2TimeTag2(dt):
        h = dt.hour
        m = dt.minute
        s = dt.second
        ms = dt.microsecond/1000
        return int("%d%02d%02d%03d" % (h, m, s, ms))

    # Converts datetime to Datetag
    @staticmethod
    def datetime2DateTag(dt):
        y = dt.year
        # mon = dt.month
        day = dt.timetuple().tm_yday

        return int("%d%03d" % (y, day))

    # Converts HDFRoot timestamp attribute to seconds
    @staticmethod
    def timestampToSec(timestamp):
        timei = timestamp.split(" ")[3]
        t = timei.split(":")
        h = int(t[0])
        m = int(t[1])
        s = int(t[2])
        return ((h*60)+m)*60+s

    # Convert GPRMC Date to Datetag
    @staticmethod
    def gpsDateToDatetime(year, gpsDate):
        date = str(gpsDate).zfill(6)
        day = int(date[:2])
        mon = int(date[2:4])
        return datetime(year,mon,day,0,0,0,0,tzinfo=timezone.utc)


    @staticmethod
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

                        dt = Utilities.dateTagToDateTime(dateTag[i])
                        timeStamp.append(Utilities.timeTag2ToDateTime(dt, timei))
                    else:
                        msg = f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}"
                        print(msg)
                        Utilities.writeLogFile(msg)
                        gp.datasetDeleteRow(i)

                dateTime = gp.addDataset("DATETIME")
                dateTime.data = timeStamp
        return node


    @staticmethod
    def groupAddDateTime(gp):
        ''' Add a dataset to one group for DATETIME, as defined by TIMETAG2 and DATETAG
         Also screens for nonsense timetags like 0.0 or NaN, and datetags that are not
         in the 20th or 21st centuries '''

        # for gp in node.groups:
        # print(gp.id)
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

                    dt = Utilities.dateTagToDateTime(dateTag[i])
                    timeStamp.append(Utilities.timeTag2ToDateTime(dt, timei))
                else:
                    msg = f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}"
                    print(msg)
                    Utilities.writeLogFile(msg)
                    gp.datasetDeleteRow(i)

            dateTime = gp.addDataset("DATETIME")
            dateTime.data = timeStamp
        return gp


    @staticmethod
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

                                        dt = Utilities.dateTagToDateTime(dateTag[i])
                                        timeStamp.append(Utilities.timeTag2ToDateTime(dt, timei))
                                    else:
                                        gp.datasetDeleteRow(i)
                                        msg = f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}"
                                        print(msg)
                                        Utilities.writeLogFile(msg)
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

                            dt = Utilities.dateTagToDateTime(dateTag[i])
                            timeStamp.append(Utilities.timeTag2ToDateTime(dt, timei))
                        else:
                            gp.datasetDeleteRow(i) # L1AQC datasets all have the same i
                            msg = f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}"
                            print(msg)
                            Utilities.writeLogFile(msg)
                    # This will be the only dataset structure like a higher level with time/date columns
                    gp.datasets['Timestamp'].columns["Datetime"] = timeStamp
                    gp.datasets['Timestamp'].columns.move_to_end('Datetime', last=False)
                    gp.datasets['Timestamp'].columnsToDataset()

        return node

    # Add a data column to each group dataset for DATETIME, as defined by TIMETAG2 and DATETAG
    # Also screens for nonsense timetags like 0.0 or NaN, and datetags that are not
    # in the 20th or 21st centuries, specifically for raw data groups - used in L2 processing.
    @staticmethod
    def rawDataAddDateTime(node):
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

                        dt = Utilities.dateTagToDateTime(dateTag[i])
                        timeStamp.append(Utilities.timeTag2ToDateTime(dt, timei))
                    else:
                        msg = f"Bad Datetag or Timetag2 found. Eliminating record. {i} DT: {dateTag[i]} TT2: {timei}"
                        print(msg)
                        Utilities.writeLogFile(msg)
                        gp.datasetDeleteRow(i)

                dateTime = gp.addDataset("DATETIME")
                dateTime.data = timeStamp
        return node

    # Remove records if values of DATETIME are not strictly increasing
    # (strictly increasing values required for interpolation)
    @staticmethod
    def fixDateTime(gp):
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
                msg = f'Out of order timestamp deleted at {i}'
                print(msg)
                Utilities.writeLogFile(msg)

                #In case we went from 2 to 1 element on the first element,
                if total == 1:
                    msg = f'************Too few records ({total}) to test for ascending timestamps. Exiting.'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False

            i = 1
            while i < total:
                if dateTime[i] <= dateTime[i-1]:
                    if dateTime[i] == dateTime[i-1]:
                        # BUG?:Same values of consecutive TT2s are shockingly common. Confirmed
                        #   that 1) they exist from L1A, and 2) sensor data changes while TT2 stays the same
                        #
                        msg = f'Duplicate row deleted at {i}'
                        print(msg)
                        Utilities.writeLogFile(msg)
                    else:
                        msg = f'WARNING: Out of order row deleted at {i}; this should not happen after sortDateTime'
                        print(msg)
                        Utilities.writeLogFile(msg)

                    gp.datasetDeleteRow(i)
                    # del dateTime[i] # I'm fuzzy on why this is necessary; not a pointer?
                    dateTime = gp.getDataset("DATETIME").data
                    total = total - 1

                    continue # goto while test skipping i incrementation. dateTime[i] is now the next value.
                i += 1
        else:
            msg = f'************Too few records ({total}) to test for ascending timestamps. Exiting.'
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        if (globalTotal - total) > 0:
            msg = f'Data eliminated for non-increasing timestamps: {100*(globalTotal - total)/globalTotal:3.1f}%'
            print(msg)
            Utilities.writeLogFile(msg)

        return True


    # Checks if a string is a floating point number
    @staticmethod
    def isFloat(text):
        try:
            float(text)
            return True
        except ValueError:
            return False

    # Check if dataset contains NANs
    @staticmethod
    def hasNan(ds):
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
                # else:
                #     if np.isnan(ds.data[k][x]):
                #         return True
        return False

    @staticmethod
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


    @staticmethod
    def isIncreasing(l):
        ''' Check if the list contains strictly increasing values '''
        return all(x<y for x, y in zip(l, l[1:]))

    @staticmethod
    def windowAverage(data,window_size):
        min_periods = round(window_size/2)
        df=pd.DataFrame(data)
        out=df.rolling(window_size,min_periods,center=True,win_type='boxcar')
        # out = [item for items in out for item in items] #flattening doesn't work
        return out

    @staticmethod
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


    @staticmethod
    def darkConvolution(data,avg,std,sigma):
        badIndex = []
        for i, dat in enumerate(data):
            if i < 1 or i > len(data)-2:
                # First and last avg values from convolution are not to be trusted
                badIndex.append(True)
            elif np.isnan(dat):
                badIndex.append(False)
            else:
                # Use stationary standard deviation anomaly (from rolling average) detection for dark data
                if (dat > avg[i] + (sigma*std)) or (dat < avg[i] - (sigma*std)):
                    badIndex.append(True)
                else:
                    badIndex.append(False)
        return badIndex

    @staticmethod
    def lightConvolution(data,avg,rolling_std,sigma):
        badIndex = []
        for i, dat in enumerate(data):
            if i < 1 or i > len(data)-2:
                # First and last avg values from convolution are not to be trusted
                badIndex.append(True)
            elif np.isnan(dat):
                badIndex.append(False)
            else:
                # Use rolling standard deviation anomaly (from rolling average) detection for dark data
                if (dat > avg[i] + (sigma*rolling_std[i])) or (dat < avg[i] - (sigma*rolling_std[i])):
                    badIndex.append(True)
                else:
                    badIndex.append(False)
        return badIndex

    @staticmethod
    def deglitchThresholds(band,data,minRad,maxRad,minMaxBand):

        badIndex = []
        for dat in data:
            badIndex.append(False)
            # ConfigFile setting updated directly from the checkbox in AnomDetection.
            # This insures values of badIndex are false if unthresholded or Min or Max are None
            if ConfigFile.settings["bL1aqcThreshold"]:
                # Only run on the pre-selected waveband
                if band == minMaxBand:
                    if minRad or minRad==0: # beware falsy zeros...
                        if dat < minRad:
                            badIndex[-1] = True

                    if maxRad or maxRad==0:
                        if dat > maxRad:
                            badIndex[-1] = True
        return badIndex


    @staticmethod
    def interp(x, y, new_x, kind='linear', fill_value=0.0):
        ''' Wrapper for scipy interp1d that works even if
            values in new_x are outside the range of values in x'''

        # ''' NOTE: This will fill missing values at the beginning and end of data record with
        #     the nearest actual record. This is fine for integrated datasets, but may be dramatic
        #     for some gappy ancillary records of lower temporal resolution.'''
        # If the last value to interp to is larger than the last value interp'ed from,
        # then append that higher value onto the values to interp from
        n0 = len(x)-1
        n1 = len(new_x)-1
        if new_x[n1] > x[n0]:
            #print(new_x[n], x[n])
            # msg = '********** Warning: extrapolating to beyond end of data record ********'
            # print(msg)
            # Utilities.writeLogFile(msg)

            x.append(new_x[n1])
            y.append(y[n0])
        # If the first value to interp to is less than the first value interp'd from,
        # then add that lesser value to the beginning of values to interp from
        if new_x[0] < x[0]:
            #print(new_x[0], x[0])
            # msg = '********** Warning: extrapolating to before beginning of data record ******'
            # print(msg)
            # Utilities.writeLogFile(msg)

            x.insert(0, new_x[0])
            y.insert(0, y[0])

        new_y = scipy.interpolate.interp1d(x, y, kind=kind, bounds_error=False, fill_value=fill_value)(new_x)

        return new_y

    @staticmethod
    def interpAngular(x, y, new_x, fill_value="extrapolate"):
        ''' Wrapper for scipy interp1d that works even if
            values in new_x are outside the range of values in x'''

        # ''' NOTE: Except for SOLAR_AZ and SZA, which are extrapolated, this will fill missing values at the
        #     beginning and end of data record with the nearest actual record. This is fine for integrated
        #     datasets, but may be dramatic for some gappy ancillary records of lower temporal resolution.
        #     NOTE: SOLAR_AZ and SZA should no longer be int/extrapolated at all, but recalculated in L1B

        #     NOTE: REL_AZ (sun to sensor) may be negative and should be 90 - 135, so does not require angular
        #     interpolation.
        #     '''

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
                    # msg = '********** Warning: extrapolating to beyond end of data record ********'
                    # print(msg)
                    # Utilities.writeLogFile(msg)

                    x.append(new_x[n1])
                    y.append(y[n0])

                # If the first value to interp to is less than the first value interp'd from,
                # then add that lesser value to the beginning of values to interp from
                if new_x[0] < x[0]:
                    #print(new_x[0], x[0])
                    # msg = '********** Warning: extrapolating to before beginning of data record ******'
                    # print(msg)
                    # Utilities.writeLogFile(msg)

                    x.insert(0, new_x[0])
                    y.insert(0, y[0])

            y_rad = np.deg2rad(y)
            # f = scipy.interpolate.interp1d(x,y_rad,kind='linear', bounds_error=False, fill_value=None)
            f = scipy.interpolate.interp1d(x,y_rad,kind='linear', bounds_error=False, fill_value=fill_value)
            new_y_rad = f(new_x)%(2*np.pi)
            new_y = np.rad2deg(new_y_rad)

        else:
            # All y values were NaNs. Fill in NaNs in new_y
            new_y = np.empty((len(new_x)))
            new_y.fill(np.nan)
            new_y = new_y.tolist()

        return new_y

    # Cubic spline interpolation intended to get around the all NaN output from InterpolateUnivariateSpline
    # x is original time to be splined, y is the data to be interpolated, new_x is the time to interpolate/spline to
    # interpolate.splrep is intolerant of duplicate or non-ascending inputs, and inputs with fewer than 3 points
    @staticmethod
    def interpSpline(x, y, new_x):
        spl = splrep(x, y)
        new_y = splev(new_x, spl)

        for newy in new_y:
            if np.isnan(newy):
                print("NaN")

        return new_y

    @staticmethod
    def interpFill(x, y, newXList, fillValue=np.nan):
        ''' Used where fill is needed instead of interpolation, e.g., STATIONS in L1B.'''

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

    @staticmethod
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


    @staticmethod
    def filterData(group, badTimes, level = None):
        ''' Delete flagged records. Level is only specified to point to the timestamp.
            All data in the group (including satellite sensors) will be deleted.
            Called by both ProcessL1bqc and ProcessL2. 
            
            filterData for L1AQC is contained within ProcessL1aqc.py'''

        # NOTE: This is still very slow on long files with many badTimes, despite badTimes being filtered for 
        #   unique pairs.


        msg = f'Remove {group.id} Data'
        print(msg)
        Utilities.writeLogFile(msg)
        # internal switch to trigger the reset of CAL & BACK
        # dataset that we have to delete to avoid conflict during filtering
        do_reset = False
        timeStamp = None
        raw_cal, raw_back, raw_back_att, raw_cal_att = None,None,None,None,

        if level != 'L1AQC':
            if group.id == "ANCILLARY":
                timeStamp = group.getDataset("LATITUDE").data["Datetime"]
            if group.id == "IRRADIANCE":
                timeStamp = group.getDataset("ES").data["Datetime"]
            if group.id == "RADIANCE":
                timeStamp = group.getDataset("LI").data["Datetime"]
            if group.id == "SIXS_MODEL":
                timeStamp = group.getDataset("solar_zenith").data["Datetime"]
        else:
            timeStamp = group.getDataset("Timestamp").data["Datetime"]
            # TRIOS: copy CAL & BACK before filetering, and delete them
            # to avoid conflict when filtering more row than 255
            if ConfigFile.settings['SensorType'].lower() == 'trios':
                do_reset = True
                raw_cal  = group.getDataset("CAL_"+group.id[0:2]).data
                raw_back = group.getDataset("BACK_"+group.id[0:2]).data
                raw_cal_att  = group.getDataset("CAL_"+group.id[0:2]).attributes
                raw_back_att = group.getDataset("BACK_"+group.id[0:2]).attributes
                del group.datasets['CAL_'+group.id[0:2]]
                del group.datasets['BACK_'+group.id[0:2]]


        startLength = len(timeStamp)
        msg = f'   Length of dataset prior to removal {startLength} long'
        print(msg)
        Utilities.writeLogFile(msg)

        # Delete the records in badTime ranges from each dataset in the group
        finalCount = 0
        originalLength = len(timeStamp)
        for dateTime in badTimes:
            # Need to reinitialize for each loop
            startLength = len(timeStamp)
            newTimeStamp = []

            # msg = f'Eliminate data between: {dateTime}'
            # print(msg)
            # Utilities.writeLogFile(msg)

            start = dateTime[0]
            stop = dateTime[1]

            if startLength > 0:
                rowsToDelete = []
                for i in range(startLength):
                    if start <= timeStamp[i] and stop >= timeStamp[i]:
                        try:
                            rowsToDelete.append(i)
                            finalCount += 1
                        except Exception:
                            print('error')
                    else:
                        newTimeStamp.append(timeStamp[i])
                group.datasetDeleteRow(rowsToDelete)
            else:
                msg = 'Data group is empty. Continuing.'
                print(msg)
                Utilities.writeLogFile(msg)
                break
            timeStamp = newTimeStamp.copy()

        if ConfigFile.settings['SensorType'].lower() == 'trios':
            # TRIOS: reset CAL and BACK as before filtering
            if do_reset:
                group.addDataset("CAL_"+group.id[0:2])
                group.datasets["CAL_"+group.id[0:2]].data = raw_cal
                group.datasets["CAL_"+group.id[0:2]].attributes = raw_cal_att
                group.addDataset("BACK_"+group.id[0:2])
                group.datasets["BACK_"+group.id[0:2]].data = raw_back
                group.datasets["BACK_"+group.id[0:2]].attributes = raw_back_att

            for ds in group.datasets:
                group.datasets[ds].datasetToColumns()
        else:
            for ds in group.datasets:
                group.datasets[ds].datasetToColumns()

        msg = f'   Length of dataset after removal {originalLength-finalCount} long: {(100*finalCount/originalLength):.1f}% removed'
        print(msg)
        Utilities.writeLogFile(msg)
        return finalCount/originalLength


    @staticmethod
    def plotRadiometry(root, filename, rType, plotDelta = False):
        # refresh figure to ensure debug plots do not affect Rrs plotting
        plt.figure()

        outDir = MainConfig.settings["outDir"]

        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L2')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        # dataDelta in this case can be STD (for TriOS Factory) or UNC (otherwise)
        dataDelta = None
        # Note: If only one spectrum is left in a given ensemble, STD will
        #be zero for Es, Li, and Lt.'''
        #if ConfigFile.settings['SensorType'].lower() == 'trios' and ConfigFile.settings['bL1bCal'] == 1:
        if  (ConfigFile.settings['SensorType'].lower() == 'trios' or \
             ConfigFile.settings['SensorType'].lower() == 'dalec') and ConfigFile.settings['bL1bCal'] == 1:
            suffix = 'sd'
        else:
            suffix = 'unc'

        # In the case of reflectances, only use _unc. There are no _std, because reflectances are calculated
        # from the average Lw and Es values within the ensembles
        Data, lwData, Data_MODISA, Data_MODIST = None, None, None, None
        Data_Sentinel3A, Data_Sentinel3B, Data_VIIRSJ,Data_VIIRSN = None, None, None, None
        dataDelta, dataDelta_MODISA, dataDelta_MODIST, dataDelta_Sentinel3A = None, None, None, None
        dataDelta_Sentinel3B, dataDelta_VIIRSJ, dataDelta_VIIRSN, units = None, None, None, None
        if rType=='Rrs' or rType=='nLw':
            print('Plotting Rrs or nLw')
            group = root.getGroup("REFLECTANCE")
            if rType=='Rrs':
                units = group.attributes['Rrs_UNITS']
            else:
                units = group.attributes['nLw_UNITS']
            Data = group.getDataset(f'{rType}_HYPER')
            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_unc').data.copy()

            plotRange = [340, 800]
            if ConfigFile.settings['bL2WeightMODISA']:
                Data_MODISA = group.getDataset(f'{rType}_MODISA')
                if plotDelta:
                    dataDelta_MODISA = group.getDataset(f'{rType}_MODISA_unc')

            if ConfigFile.settings['bL2WeightMODIST']:
                Data_MODIST = group.getDataset(f'{rType}_MODIST')
                if plotDelta:
                    dataDelta_MODIST = group.getDataset(f'{rType}_MODIST_unc')

            if ConfigFile.settings['bL2WeightVIIRSN']:
                Data_VIIRSN = group.getDataset(f'{rType}_VIIRSN')
                if plotDelta:
                    dataDelta_VIIRSN = group.getDataset(f'{rType}_VIIRSN_unc')
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                Data_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ')
                if plotDelta:
                    dataDelta_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ_unc')
            if ConfigFile.settings['bL2WeightSentinel3A']:
                Data_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A')
                if plotDelta:
                    dataDelta_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A_unc')
            if ConfigFile.settings['bL2WeightSentinel3B']:
                Data_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B')
                if plotDelta:
                    dataDelta_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B_unc')

        else:
            # Could include satellite convolved (ir)radiances in the future '''
            if rType=='ES':
                print('Plotting Es')
                group = root.getGroup("IRRADIANCE")
                units = group.attributes['ES_UNITS']
                Data = group.getDataset(f'{rType}_HYPER')

            if rType=='LI':
                print('Plotting Li')
                group = root.getGroup("RADIANCE")
                units = group.attributes['LI_UNITS']
                Data = group.getDataset(f'{rType}_HYPER')

            if rType=='LT':
                print('Plotting Lt')
                group = root.getGroup("RADIANCE")
                units = group.attributes['LT_UNITS']
                Data = group.getDataset(f'{rType}_HYPER')
                lwData = group.getDataset('LW_HYPER')
                if plotDelta:
                    # lwDataDelta = group.getDataset(f'LW_HYPER_{suffix}')
                    lwDataDelta = group.getDataset('LW_HYPER_unc').data.copy() # Lw does not have STD
                    # For the purpose of plotting, use zeros for NaN uncertainties
                    lwDataDelta = Utilities.datasetNan2Zero(lwDataDelta)

            if plotDelta:
                dataDelta = group.getDataset(f'{rType}_HYPER_{suffix}').data.copy() # Do not change the L2 data
                # For the purpose of plotting, use zeros for NaN uncertainties
                dataDelta = Utilities.datasetNan2Zero(dataDelta)
            # plotRange = [305, 1140]
            plotRange = [305, 1000]



        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }

        # Hyperspectral
        x = []
        xLw = []
        wave = []
        subwave = [] # accomodates Zhang, which deletes out-of-bounds wavebands
        # For each waveband
        for k in Data.data.dtype.names:
            if Utilities.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    x.append(k)
                    wave.append(float(k))
        # Add Lw to Lt plots
        if rType=='LT':
            for k in lwData.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        xLw.append(k)
                        subwave.append(float(k))

        # Satellite Bands
        x_MODISA = []
        wave_MODISA = []
        if ConfigFile.settings['bL2WeightMODISA'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_MODISA.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_MODISA.append(k)
                        wave_MODISA.append(float(k))
        x_MODIST = []
        wave_MODIST = []
        if ConfigFile.settings['bL2WeightMODIST'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_MODIST.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_MODIST.append(k)
                        wave_MODIST.append(float(k))
        x_VIIRSN = []
        wave_VIIRSN = []
        if ConfigFile.settings['bL2WeightVIIRSN'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_VIIRSN.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_VIIRSN.append(k)
                        wave_VIIRSN.append(float(k))
        x_VIIRSJ = []
        wave_VIIRSJ = []
        if ConfigFile.settings['bL2WeightVIIRSJ'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_VIIRSJ.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_VIIRSJ.append(k)
                        wave_VIIRSJ.append(float(k))
        x_Sentinel3A = []
        wave_Sentinel3A = []
        if ConfigFile.settings['bL2WeightSentinel3A'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_Sentinel3A.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_Sentinel3A.append(k)
                        wave_Sentinel3A.append(float(k))
        x_Sentinel3B = []
        wave_Sentinel3B = []
        if ConfigFile.settings['bL2WeightSentinel3B'] and (rType == 'Rrs' or rType == 'nLw'):
            for k in Data_Sentinel3B.data.dtype.names:
                if Utilities.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        x_Sentinel3B.append(k)
                        wave_Sentinel3B.append(float(k))


        total = Data.data.shape[0]
        maxRad = 0
        minRad = 0
        cmap = cm.get_cmap("jet")
        color=iter(cmap(np.linspace(0,1,total)))

        plt.figure(1, figsize=(8,6))
        for i in range(total):
            # Hyperspectral
            y = []
            dy = []
            for k in x:
                y.append(Data.data[k][i])
                if plotDelta:
                    dy.append(dataDelta[k][i])
            # Add Lw to Lt plots
            if rType=='LT':
                yLw = []
                dyLw = []
                for k in xLw:
                    yLw.append(lwData.data[k][i])
                    if plotDelta:
                        dyLw.append(lwDataDelta[k][i])

            # Satellite Bands
            y_MODISA = []
            dy_MODISA = []
            if ConfigFile.settings['bL2WeightMODISA']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_MODISA:
                    y_MODISA.append(Data_MODISA.data[k][i])
                    if plotDelta:
                        dy_MODISA.append(dataDelta_MODISA.data[k][i])
            y_MODIST = []
            dy_MODIST = []
            if ConfigFile.settings['bL2WeightMODIST']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_MODIST:
                    y_MODIST.append(Data_MODIST.data[k][i])
                    if plotDelta:
                        dy_MODIST.append(dataDelta_MODIST.data[k][i])
            y_VIIRSN = []
            dy_VIIRSN = []
            if ConfigFile.settings['bL2WeightVIIRSN']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_VIIRSN:
                    y_VIIRSN.append(Data_VIIRSN.data[k][i])
                    if plotDelta:
                        dy_VIIRSN.append(dataDelta_VIIRSN.data[k][i])
            y_VIIRSJ = []
            dy_VIIRSJ = []
            if ConfigFile.settings['bL2WeightVIIRSJ']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_VIIRSJ:
                    y_VIIRSJ.append(Data_VIIRSJ.data[k][i])
                    if plotDelta:
                        dy_VIIRSJ.append(dataDelta_VIIRSJ.data[k][i])
            y_Sentinel3A = []
            dy_Sentinel3A = []
            if ConfigFile.settings['bL2WeightSentinel3A']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_Sentinel3A:
                    y_Sentinel3A.append(Data_Sentinel3A.data[k][i])
                    if plotDelta:
                        dy_Sentinel3A.append(dataDelta_Sentinel3A.data[k][i])
            y_Sentinel3B = []
            dy_Sentinel3B = []
            if ConfigFile.settings['bL2WeightSentinel3B']  and (rType == 'Rrs' or rType == 'nLw'):
                for k in x_Sentinel3B:
                    y_Sentinel3B.append(Data_Sentinel3B.data[k][i])
                    if plotDelta:
                        dy_Sentinel3B.append(dataDelta_Sentinel3B.data[k][i])

            c=next(color)
            if max(y) > maxRad:
                maxRad = max(y)+0.1*max(y)
            if rType == 'LI' and maxRad > 20:
                maxRad = 20
            if rType == 'LT' and maxRad > 2:
                maxRad = 2
            if min(y) < minRad:
                minRad = min(y)-0.1*min(y)
            if rType == 'LI':
                minRad = 0
            if rType == 'LT':
                minRad = 0
            if rType == 'ES':
                minRad = 0

            # Plot the Hyperspectral spectrum
            plt.plot(wave, y, c=c, zorder=-1)

            # Add the Wei QA score to the Rrs plot, if calculated
            if rType == 'Rrs':
                # Add the Wei score to the Rrs plot, if calculated
                if ConfigFile.products['bL2ProdweiQA']:
                    groupProd = root.getGroup("DERIVED_PRODUCTS")
                    score = groupProd.getDataset('wei_QA')
                    QA_note = f"Wei: {score.columns['QA_score'][i]}"
                    axes = plt.gca()
                    axes.text(0.7,1.1 - (i+1)/len(score.columns['QA_score']), QA_note,
                        verticalalignment='top', horizontalalignment='right',
                        transform=axes.transAxes,
                        color=c, fontdict=font)

                # Add the QWIP score to the Rrs plot, if calculated
                if ConfigFile.products['bL2Prodqwip']:
                    groupProd = root.getGroup("DERIVED_PRODUCTS")
                    score = groupProd.getDataset('qwip')
                    QA_note = f"QWIP: {score.columns['qwip'][i]:5.3f}"
                    axes = plt.gca()
                    axes.text(0.75,1.1 - (i+1)/len(score.columns['qwip']), QA_note,
                        verticalalignment='top', horizontalalignment='left',
                        transform=axes.transAxes,
                        color=c, fontdict=font)

            # Add Lw to Lt plots
            if rType=='LT':
                plt.plot(subwave, yLw, c=c, zorder=-1, linestyle='dashed')

            if plotDelta:
                # Generate the polygon for uncertainty bounds
                deltaPolyx = wave + list(reversed(wave))
                dPolyyPlus = [(y[i]+dy[i]) for i in range(len(y))]
                dPolyyMinus = [(y[i]-dy[i]) for i in range(len(y))]
                deltaPolyyPlus = y + list(reversed(dPolyyPlus))
                deltaPolyyMinus = y + list(reversed(dPolyyMinus))

                plt.fill(deltaPolyx, deltaPolyyPlus, alpha=0.2, c=c, zorder=-1)
                plt.fill(deltaPolyx, deltaPolyyMinus, alpha=0.2, c=c, zorder=-1)

                # deltaPolyy = dPolyyMinus + list(reversed(dPolyyPlus))
                # plt.fill(deltaPolyx, deltaPolyy, alpha=0.2, c=c, zorder=-1)


                if rType=='LT':
                    dPolyyPlus = [(yLw[i]+dyLw[i]) for i in range(len(yLw))]
                    dPolyyMinus = [(yLw[i]-dyLw[i]) for i in range(len(yLw))]
                    deltaPolyyPlus = yLw + list(reversed(dPolyyPlus))
                    deltaPolyyMinus = yLw + list(reversed(dPolyyMinus))
                    plt.fill(deltaPolyx, deltaPolyyPlus, alpha=0.2, c=c, zorder=-1)
                    plt.fill(deltaPolyx, deltaPolyyMinus, alpha=0.2, c=c, zorder=-1)

            # Satellite Bands
            if ConfigFile.settings['bL2WeightMODISA']:
                # Plot the MODISA spectrum
                if plotDelta:
                    plt.errorbar(wave_MODISA, y_MODISA, yerr=dy_MODISA, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black', zorder=3) # ecolor is broken
                else:
                    plt.plot(wave_MODISA, y_MODISA, 'o', c=c)
            if ConfigFile.settings['bL2WeightMODIST']:
                # Plot the MODIST spectrum
                if plotDelta:
                    plt.errorbar(wave_MODIST, y_MODIST, yerr=dy_MODIST, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_MODIST, y_MODIST, 'o', c=c)
            if ConfigFile.settings['bL2WeightVIIRSN']:
                # Plot the VIIRSN spectrum
                if plotDelta:
                    plt.errorbar(wave_VIIRSN, y_VIIRSN, yerr=dy_VIIRSN, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_VIIRSN, y_VIIRSN, 'o', c=c)
            if ConfigFile.settings['bL2WeightVIIRSJ']:
                # Plot the VIIRSJ spectrum
                if plotDelta:
                    plt.errorbar(wave_VIIRSJ, y_VIIRSJ, yerr=dy_VIIRSJ, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_VIIRSJ, y_VIIRSJ, 'o', c=c)
            if ConfigFile.settings['bL2WeightSentinel3A']:
                # Plot the Sentinel3A spectrum
                if plotDelta:
                    plt.errorbar(wave_Sentinel3A, y_Sentinel3A, yerr=dy_Sentinel3A, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_Sentinel3A, y_Sentinel3A, 'o', c=c)
            if ConfigFile.settings['bL2WeightSentinel3B']:
                # Plot the Sentinel3B spectrum
                if plotDelta:
                    plt.errorbar(wave_Sentinel3B, y_Sentinel3B, yerr=dy_Sentinel3B, fmt='.',
                        elinewidth=0.1, color=c, ecolor='black')
                else:
                    plt.plot(wave_Sentinel3B, y_Sentinel3B, 'o', c=c)

        axes = plt.gca()
        axes.set_title(filename, fontdict=font)
        # axes.set_xlim([390, 800])
        axes.set_ylim([minRad, maxRad])

        plt.xlabel('wavelength (nm)', fontdict=font)
        if rType=='LT':
            plt.ylabel(f'LT (LW dash) [{units}]', fontdict=font)
        else:
            plt.ylabel(f'{rType} [{units}]', fontdict=font)

        # Tweak spacing to prevent clipping of labels
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)

        note = f'Interval: {ConfigFile.settings["fL2TimeInterval"]} s'
        axes.text(0.2, -0.1, note,
        verticalalignment='top', horizontalalignment='right',
        transform=axes.transAxes,
        color='black', fontdict=font)
        axes.grid()

        # plt.show() # --> QCoreApplication::exec: The event loop is already running

        # Save the plot
        # filebasename = filename.split('_')
        # fp = os.path.join(plotDir, '_'.join(filebasename[0:-1]) + '_' + rType + '.png')
        filebasename = filename.split('.hdf')
        fp = os.path.join(plotDir, filebasename[0] + '_' + rType + '.png')
        plt.savefig(fp)
        plt.close() # This prevents displaying the plot on screen with certain IDEs


    @staticmethod
    def plotTimeInterp(xData, xTimer, newXData, yTimer, instr, fp):
        ''' Plot results of L1B time interpolation '''

        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L1B_Interp')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        # For the sake of MacOS, need to hack the datetimes into panda dataframes for plotting
        dfx = pd.DataFrame(data=xTimer, index=list(range(0,len(xTimer))), columns=['x'])
        # *** HACK: CONVERT datetime column to string and back again - who knows why this works? ***
        dfx['x'] = pd.to_datetime(dfx['x'].astype(str))
        dfy = pd.DataFrame(data=yTimer, index=list(range(0,len(yTimer))), columns=['x'])
        dfy['x'] = pd.to_datetime(dfy['x'].astype(str))

        [_,fileName] = os.path.split(fp)
        fileBaseName,_ = fileName.rsplit('.',1)
        register_matplotlib_converters()

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }

        progressBar = None
        # Steps in wavebands used for plots
        # This happens prior to waveband interpolation, so each interval is ~3.3 nm
        step = ConfigFile.settings['fL1bPlotInterval']

        intervalList = ['ES','LI','LT','sixS_irradiance','direct_ratio','diffuse_ratio']
        # if instr == 'ES' or instr == 'LI' or instr == 'LT':
        if instr in intervalList:
            l = round((len(xData.data.dtype.names)-3)/step) # skip date and time and datetime
            index = l
        else:
            l = len(xData.data.dtype.names)-3 # skip date and time and datetime
            index = None

        if index:
            progressBar = tqdm(total=l, unit_scale=True, unit_divisor=step)

        ticker = 0
        if index is not None:
            for k in xData.data.dtype.names:
                if index % step == 0:
                    if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                        continue
                    ticker += 1
                    progressBar.update(1)

                    x = np.copy(xData.data[k]).tolist()
                    new_x = np.copy(newXData.columns[k]).tolist()

                    fig = plt.figure(figsize=(12, 4))
                    ax = fig.add_subplot(1, 1, 1)
                    # ax.plot(xTimer, x, 'bo', label='Raw')
                    ax.plot(dfx['x'], x, 'bo', label='Raw')
                    # ax.plot(yTimer, new_x, 'k.', label='Interpolated')
                    ax.plot(dfy['x'], new_x, 'k.', label='Interpolated')
                    ax.legend()

                    plt.xlabel('Date/Time (UTC)', fontdict=font)
                    plt.ylabel(f'{instr}_{k}', fontdict=font)
                    plt.subplots_adjust(left=0.15)
                    plt.subplots_adjust(bottom=0.15)

                    # plt.savefig(os.path.join('Plots','L1E',f'{fileBaseName}_{instr}_{k}.png'))
                    plt.savefig(os.path.join(plotDir,f'{fileBaseName}_{instr}_{k}.png'))
                    plt.close()
                index +=1
        else:
            for k in xData.data.dtype.names:
                if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                    continue

                x = np.copy(xData.data[k]).tolist()
                new_x = np.copy(newXData.columns[k]).tolist()

                fig = plt.figure(figsize=(12, 4))
                ax = fig.add_subplot(1, 1, 1)
                # ax.plot(xTimer, x, 'bo', label='Raw')
                ax.plot(dfx['x'], x, 'bo', label='Raw')
                # ax.plot(yTimer, new_x, 'k.', label='Interpolated')
                ax.plot(dfy['x'], new_x, 'k.', label='Interpolated')
                ax.legend()

                plt.xlabel('Date/Time (UTC)', fontdict=font)
                plt.ylabel(f'{instr}', fontdict=font)
                plt.subplots_adjust(left=0.15)
                plt.subplots_adjust(bottom=0.15)

                if k == 'NONE':
                    plt.savefig(os.path.join(plotDir,f'{fileBaseName}_{instr}.png'))
                else:
                    plt.savefig(os.path.join(plotDir,f'{fileBaseName}_{instr}_{k}.png'))
                plt.close()

        print('\n')

    @staticmethod
    def specFilter(inFilePath, Dataset, timeStamp, station=None, filterRange=[400, 700],\
                filterFactor=3, rType='None'):

        if ConfigFile.settings['bL1bqcEnableSpecQualityCheckPlot']:
            import logging
            logging.getLogger('matplotlib.font_manager').disabled = True

            outDir = MainConfig.settings["outDir"]
            # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
            # and build on that (HyperInSPACE/Plots/etc...)
            if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
                outDir = dirPath

            # Otherwise, put Plots in the chosen output directory from Main
            plotDir = os.path.join(outDir,'Plots','L1BQC_Spectral_Filter')

            if not os.path.exists(plotDir):
                os.makedirs(plotDir)

            font = {'family': 'serif',
                    'color':  'darkred',
                    'weight': 'normal',
                    'size': 16,
                    }

        # Collect each column name ignoring Datetag and Timetag2 (i.e. each wavelength) in the desired range
        x = []
        wave = []
        for k in Dataset.data.dtype.names:
            if Utilities.isFloat(k):
                if float(k)>=filterRange[0] and float(k)<=filterRange[1]:
                    x.append(k)
                    wave.append(float(k))

        # Read in each spectrum
        total = Dataset.data.shape[0]
        specArray = []
        normSpec = []

        if ConfigFile.settings['bL1bqcEnableSpecQualityCheckPlot']:
            # cmap = cm.get_cmap("jet")
            # color=iter(cmap(np.linspace(0,1,total)))
            print('Creating plots...')
            plt.figure(1, figsize=(10,8))

        for timei in range(total):
            y = []
            for waveband in x:
                y.append(Dataset.data[waveband][timei])

            specArray.append(y)
            peakIndx = y.index(max(y))
            normSpec.append(y / y[peakIndx])
            # plt.plot(wave, y / y[peakIndx], color='grey')

        normSpec = np.array(normSpec)

        aveSpec = np.median(normSpec, axis = 0)
        stdSpec = np.std(normSpec, axis = 0)

        badTimes  = []
        badIndx = []
        # For each spectral band...
        for i in range(0, len(normSpec[0])-1):
            # For each timeseries radiometric measurement...
            for j, rad in enumerate(normSpec[:,i]):
                # Identify outliers and negative values for elimination
                if rad > (aveSpec[i] + filterFactor*stdSpec[i]) or \
                    rad < (aveSpec[i] - filterFactor*stdSpec[i]) or \
                    rad < 0:
                    badIndx.append(j)
                    badTimes.append(timeStamp[j])

        badIndx = np.unique(badIndx)
        badTimes = np.unique(badTimes)
        # Duplicates each element to a list of two elements in a list:
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3)

        if ConfigFile.settings['bL1bqcEnableSpecQualityCheckPlot']:
            # t0 = time.time()
            for timei in range(total):
            # for i in badIndx:
                if timei in badIndx:
                    # plt.plot( wave, normSpec[i,:], color='red', linewidth=0.5, linestyle=(0, (1, 10)) ) # long-dot
                    plt.plot( wave, normSpec[timei,:], color='red', linewidth=0.5, linestyle=(0, (5, 5)) ) # dashed
                else:
                    plt.plot(wave, normSpec[timei,:], color='grey')

            # t1 = time.time()
            # print(f'Time elapsed: {str(round((t1-t0)))} Seconds')

            plt.plot(wave, aveSpec, color='black', linewidth=0.5)
            plt.plot(wave, aveSpec + filterFactor*stdSpec, color='black', linewidth=2, linestyle='dashed')
            plt.plot(wave, aveSpec - filterFactor*stdSpec, color='black', linewidth=2, linestyle='dashed')

            plt.title(f'Sigma = {filterFactor}', fontdict=font)
            plt.xlabel('Wavelength [nm]', fontdict=font)
            plt.ylabel(f'{rType} [Normalized to peak value]', fontdict=font)
            plt.subplots_adjust(left=0.15)
            plt.subplots_adjust(bottom=0.15)
            axes = plt.gca()
            axes.grid()

            # Save the plot
            _,filename = os.path.split(inFilePath)
            filebasename,_ = filename.rsplit('_',1)
            if station:
                fp = os.path.join(plotDir, f'STATION_{station}_{filebasename}_{rType}.png')
            else:
                fp = os.path.join(plotDir, f'{filebasename}_{rType}.png')
            plt.savefig(fp)
            plt.close()

        return badTimes

    @staticmethod
    def plotIOPs(root, filename, algorithm, iopType, plotDelta = False):

        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L2_Products')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }

        cmap = cm.get_cmap("jet")

        # dataDelta = None

        group = root.getGroup("DERIVED_PRODUCTS")
        # if iopType=='a':
        #     print('Plotting absorption')

        if algorithm == "qaa" or algorithm == "giop":
            plotRange = [340, 700]
            qaaName = f'bL2Prod{iopType}Qaa'
            giopName = f'bL2Prod{iopType}Giop'
            if ConfigFile.products["bL2Prodqaa"] and ConfigFile.products[qaaName]:
                label = f'qaa_{iopType}'
                DataQAA = group.getDataset(label)
                # if plotDelta:
                #     dataDelta = group.getDataset(f'{iopType}_HYPER_delta')

                xQAA = []
                waveQAA = []
                # For each waveband
                for k in DataQAA.data.dtype.names:
                    if Utilities.isFloat(k):
                        if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                            xQAA.append(k)
                            waveQAA.append(float(k))
                totalQAA = DataQAA.data.shape[0]
                colorQAA = iter(cmap(np.linspace(0,1,totalQAA)))

            if ConfigFile.products["bL2Prodgiop"] and ConfigFile.products[giopName]:
                label = f'giop_{iopType}'
                DataGIOP = group.getDataset(label)
                # if plotDelta:
                #     dataDelta = group.getDataset(f'{iopType}_HYPER_delta')

                xGIOP = []
                waveGIOP = []
                # For each waveband
                for k in DataGIOP.data.dtype.names:
                    if Utilities.isFloat(k):
                        if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                            xGIOP.append(k)
                            waveGIOP.append(float(k))
                totalGIOP = DataQAA.data.shape[0]
                colorGIOP = iter(cmap(np.linspace(0,1,totalGIOP)))


        if algorithm == "gocad":
            plotRange = [270, 700]
            gocadName = f'bL2Prod{iopType}'
            if ConfigFile.products["bL2Prodgocad"] and ConfigFile.products[gocadName]:

                # ag
                label = f'gocad_{iopType}'
                agDataGOCAD = group.getDataset(label)
                # if plotDelta:
                #     dataDelta = group.getDataset(f'{iopType}_HYPER_delta')

                agGOCAD = []
                waveGOCAD = []
                # For each waveband
                for k in agDataGOCAD.data.dtype.names:
                    if Utilities.isFloat(k):
                        if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                            agGOCAD.append(k)
                            waveGOCAD.append(float(k))
                totalGOCAD = agDataGOCAD.data.shape[0]
                colorGOCAD = iter(cmap(np.linspace(0,1,totalGOCAD)))

                # Sg
                sgDataGOCAD = group.getDataset('gocad_Sg')

                sgGOCAD = []
                waveSgGOCAD = []
                # For each waveband
                for k in sgDataGOCAD.data.dtype.names:
                    if Utilities.isFloat(k):
                        if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                            sgGOCAD.append(k)
                            waveSgGOCAD.append(float(k))

                # DOC
                docDataGOCAD = group.getDataset('gocad_doc')

        maxIOP = 0
        minIOP = 0

        # Plot
        plt.figure(1, figsize=(8,6))

        if algorithm == "qaa" or algorithm == "giop":
            if ConfigFile.products["bL2Prodqaa"] and ConfigFile.products[qaaName]:
                for i in range(totalQAA):
                    y = []
                    # dy = []
                    for k in xQAA:
                        y.append(DataQAA.data[k][i])
                        # if plotDelta:
                        #     dy.append(dataDelta[k][i])

                    c=next(colorQAA)
                    if max(y) > maxIOP:
                        maxIOP = max(y)+0.1*max(y)
                    # if iopType == 'LI' and maxIOP > 20:
                    #     maxIOP = 20

                    # Plot the Hyperspectral spectrum
                    plt.plot(waveQAA, y, c=c, zorder=-1)

                    # if plotDelta:
                    #     # Generate the polygon for uncertainty bounds
                    #     deltaPolyx = wave + list(reversed(wave))
                    #     dPolyyPlus = [(y[i]+dy[i]) for i in range(len(y))]
                    #     dPolyyMinus = [(y[i]-dy[i]) for i in range(len(y))]
                    #     deltaPolyyPlus = y + list(reversed(dPolyyPlus))
                    #     deltaPolyyMinus = y + list(reversed(dPolyyMinus))
                    #     plt.fill(deltaPolyx, deltaPolyyPlus, alpha=0.2, c=c, zorder=-1)
                    #     plt.fill(deltaPolyx, deltaPolyyMinus, alpha=0.2, c=c, zorder=-1)
            if ConfigFile.products["bL2Prodgiop"] and ConfigFile.products[giopName]:
                for i in range(totalGIOP):
                    y = []
                    for k in xGIOP:
                        y.append(DataGIOP.data[k][i])

                    c=next(colorGIOP)
                    if max(y) > maxIOP:
                        maxIOP = max(y)+0.1*max(y)

                    # Plot the Hyperspectral spectrum
                    plt.plot(waveGIOP, y,  c=c, ls='--', zorder=-1)

        if algorithm == "gocad":
            if ConfigFile.products["bL2Prodgocad"] and ConfigFile.products[gocadName]:
                for i in range(totalGOCAD):
                    y = []
                    for k in agGOCAD:
                        y.append(agDataGOCAD.data[k][i])

                    c=next(colorGOCAD)
                    if max(y) > maxIOP:
                        maxIOP = max(y)+0.1*max(y)

                    # Plot the point spectrum
                    # plt.scatter(waveGOCAD, y, s=100, c=c, marker='*', zorder=-1)
                    plt.plot(waveGOCAD, y, c=c, marker='*', markersize=13, linestyle = '', zorder=-1)

                    # Now extrapolate using the slopes
                    Sg = []
                    for k in sgGOCAD:
                        Sg.append(sgDataGOCAD.data[k][i])
                        yScaler = maxIOP*i/totalGOCAD
                        if k == '275':
                            wave = np.array(list(range(275, 300)))
                            ag_extrap = agDataGOCAD.data['275'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 275))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(285, 0.9*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S275 = ', sgDataGOCAD.data[k][i]), color=c)

                        if k == '300':
                            wave = np.array(list(range(300, 355)))
                            # uses the trailing end of the last extrapolation.
                            ag_extrap = ag_extrap[-1] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 300))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(300, 0.7*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S300 = ', sgDataGOCAD.data[k][i]), color=c)

                        if k == '350':
                            # Use the 350 slope starting at 355 (where we have ag)
                            wave = np.array(list(range(355, 380)))
                            ag_extrap = agDataGOCAD.data['355'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 355))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(350, 0.5*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S350 = ', sgDataGOCAD.data[k][i]), color=c)

                        if k == '380':
                            wave = np.array(list(range(380, 412)))
                            ag_extrap = agDataGOCAD.data['380'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 380))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(380, 0.3*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S380 = ', sgDataGOCAD.data[k][i]), color=c)

                        if k == '412':
                            wave = np.array(list(range(412, 700)))
                            ag_extrap = agDataGOCAD.data['412'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 412))
                            plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                            plt.text(440, 0.15*maxIOP- 0.12*yScaler, '{} {:.4f}'.format('S412 = ', sgDataGOCAD.data[k][i]), color=c)

                    # Now tack on DOC
                    plt.text(600, 0.5 - 0.12*yScaler, '{} {:3.2f}'.format('DOC = ', docDataGOCAD.data['doc'][i]) , color=c)

        axes = plt.gca()
        axes.set_title(filename, fontdict=font)
        axes.set_ylim([minIOP, maxIOP])

        plt.xlabel('wavelength (nm)', fontdict=font)
        plt.ylabel(f'{label} [1/m]', fontdict=font)

        # Tweak spacing to prevent clipping of labels
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)

        note = f'Interval: {ConfigFile.settings["fL2TimeInterval"]} s'
        axes.text(0.95, 0.95, note,
        verticalalignment='top', horizontalalignment='right',
        transform=axes.transAxes,
        color='black', fontdict=font)
        axes.grid()

        # plt.show() # --> QCoreApplication::exec: The event loop is already running

        # Save the plot
        filebasename = filename.split('_')
        fp = os.path.join(plotDir, '_'.join(filebasename[0:-1]) + '_' + label + '.png')
        plt.savefig(fp)
        plt.close() # This prevents displaying the plot on screen with certain IDEs

    @staticmethod
    def readAnomAnalFile(filePath):
        paramDict = {}
        with open(filePath, newline='', encoding="utf-8") as csvfile:
            paramreader = csv.DictReader(csvfile)
            for row in paramreader:

                paramDict[row['filename']] = [ int(row['ESWindowDark']), int(row['ESWindowLight']),
                                    float(row['ESSigmaDark']), float(row['ESSigmaLight']),
                                    float(row['ESMinDark']), float(row['ESMaxDark']),
                                    float(row['ESMinMaxBandDark']),float(row['ESMinLight']),
                                    float(row['ESMaxLight']),float(row['ESMinMaxBandLight']),
                                    int(row['LIWindowDark']), int(row['LIWindowLight']),
                                    float(row['LISigmaDark']), float(row['LISigmaLight']),
                                    float(row['LIMinDark']), float(row['LIMaxDark']),
                                    float(row['LIMinMaxBandDark']),float(row['LIMinLight']),
                                    float(row['LIMaxLight']),float(row['LIMinMaxBandLight']),
                                    int(row['LTWindowDark']), int(row['LTWindowLight']),
                                    float(row['LTSigmaDark']), float(row['LTSigmaLight']),
                                    float(row['LTMinDark']), float(row['LTMaxDark']),
                                    float(row['LTMinMaxBandDark']),float(row['LTMinLight']),
                                    float(row['LTMaxLight']),float(row['LTMinMaxBandLight']),int(row['Threshold']),
                                    row['Comments'] ]
                paramDict[row['filename']] = [None if v==-999 else v for v in paramDict[row['filename']]]

        return paramDict

    @staticmethod
    def deglitchBand(band, radiometry1D, windowSize, sigma, lightDark, minRad, maxRad, minMaxBand):
        ''' For a given sensor in a given band (1D), calculate the first and second outliers on the
                light and dark based on moving average filters. Then apply thresholds.

                This may benefit in the future from eliminating the thresholded values from the moving
                average filter analysis.
        '''
        if lightDark == 'Dark':
            # For Darks, calculate the moving average and residual vectors
            #   and the OVERALL standard deviation of the residual over the entire file

            # First pass
            avg = Utilities.movingAverage(radiometry1D, windowSize).tolist()
            residual = np.array(radiometry1D) - np.array(avg)
            stdData = np.std(residual)

            badIndex = Utilities.darkConvolution(radiometry1D,avg,stdData,sigma)

            # Second pass
            radiometry1D2 = np.array(radiometry1D[:])
            radiometry1D2[badIndex] = np.nan
            radiometry1D2 = radiometry1D2.tolist()
            avg2 = Utilities.movingAverage(radiometry1D2, windowSize).tolist()
            residual = np.array(radiometry1D2) - np.array(avg2)
            stdData = np.nanstd(residual)

            badIndex2 = Utilities.darkConvolution(radiometry1D2,avg2,stdData,sigma)

            # Threshold pass
            # Tolerates "None" for min or max Rad. ConfigFile.setting updated directly from checkbox
            badIndex3 = Utilities.deglitchThresholds(band,radiometry1D,minRad,maxRad, minMaxBand)

        else:
            # For Lights, calculate the moving average and residual vectors
            #   and the ROLLING standard deviation of the residual

            # First pass
            avg = Utilities.movingAverage(radiometry1D, windowSize).tolist()
            residual = np.array(radiometry1D) - np.array(avg)

            # Calculate the variation in the distribution of the residual
            residualDf = pd.DataFrame(residual)
            testing_std_as_df = residualDf.rolling(windowSize).std()
            rolling_std = testing_std_as_df.replace(np.nan,
                testing_std_as_df.iloc[windowSize - 1]).round(3).iloc[:,0].tolist()

            # This rolling std on the residual has a tendancy to blow up for extreme outliers,
            # replace it with the median residual std when that happens
            y = np.array(rolling_std)
            y[y > np.median(y)+3*np.std(y)] = np.median(y)
            rolling_std = y.tolist()

            badIndex = Utilities.lightConvolution(radiometry1D,avg,rolling_std,sigma)

            # Second pass
            radiometry1D2 = np.array(radiometry1D[:])
            radiometry1D2[badIndex] = np.nan
            radiometry1D2 = radiometry1D2.tolist()
            avg2 = Utilities.movingAverage(radiometry1D2, windowSize).tolist()
            residual2 = np.array(radiometry1D2) - np.array(avg2)
            residualDf2 = pd.DataFrame(residual2)
            testing_std_as_df2 = residualDf2.rolling(windowSize).std()
            rolling_std2 = testing_std_as_df2.replace(np.nan,
                testing_std_as_df2.iloc[windowSize - 1]).round(3).iloc[:,0].tolist()
            y = np.array(rolling_std2)
            y[np.isnan(y)] = np.nanmedian(y)
            y[y > np.nanmedian(y)+3*np.nanstd(y)] = np.nanmedian(y)
            rolling_std2 = y.tolist()

            badIndex2 = Utilities.lightConvolution(radiometry1D2,avg2,rolling_std2,sigma)

            # Threshold pass
            # Tolerates "None" for min or max Rad
            badIndex3 = Utilities.deglitchThresholds(band, radiometry1D,minRad,maxRad, minMaxBand)

        return badIndex, badIndex2, badIndex3


    @staticmethod
    def saveDeglitchPlots(fileName,timeSeries,dateTime,sensorType,lightDark,windowSize,sigma,badIndex,badIndex2,badIndex3):#,\
        import matplotlib.dates as mdates
        #Plot results

        # # Set up datetime axis objects
        # #   https://stackoverflow.com/questions/49046931/how-can-i-use-dateaxisitem-of-pyqtgraph
        # class TimeAxisItem(pg.AxisItem):
        #     def tickStrings(self, values, scale, spacing):
        #         return [datetime.fromtimestamp(value, pytz.timezone("UTC")) for value in values]

        # date_axis_Dark = TimeAxisItem(orientation='bottom')
        # date_axis_Light = TimeAxisItem(orientation='bottom')
        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L1AQC_Anoms')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16}

        waveBand = timeSeries[0]

        radiometry1D = timeSeries[1]
        # x = np.arange(0,len(radiometry1D),1)
        x = np.array(dateTime)
        avg = Utilities.movingAverage(radiometry1D, windowSize).tolist()

        # try:
        text_xlabel="Time Series"
        text_ylabel=f'{sensorType}({waveBand}) {lightDark}'
        # plt.figure(figsize=(15, 8))
        fig, ax = plt.subplots(1)
        fig.autofmt_xdate()

        # First Pass
        y_anomaly = np.array(radiometry1D)[badIndex]
        x_anomaly = x[badIndex]
        # Second Pass
        y_anomaly2 = np.array(radiometry1D)[badIndex2]
        x_anomaly2 = x[badIndex2]
        # Thresholds
        y_anomaly3 = np.array(radiometry1D)[badIndex3]
        x_anomaly3 = x[badIndex3]

        plt.plot(x, radiometry1D, marker='o', color='k', linestyle='', fillstyle='none')
        plt.plot(x_anomaly, y_anomaly, marker='x', color='red', markersize=12, linestyle='')
        plt.plot(x_anomaly2, y_anomaly2, marker='+', color='red', markersize=12, linestyle='')
        plt.plot(x_anomaly3, y_anomaly3, marker='o', color='red', markersize=12, linestyle='', fillstyle='full', markerfacecolor='blue')
        # y_av = moving_average(radiometry1D, window_size)
        plt.plot(x[3:-3], avg[3:-3], color='green')

        xfmt = mdates.DateFormatter('%y-%m-%d %H:%M')
        ax.xaxis.set_major_formatter(xfmt)

        plt.text(0,0.95,'Marked for exclusions in ALL bands', transform=plt.gcf().transFigure)
        # plt.xlabel(text_xlabel, fontdict=font)
        plt.ylabel(text_ylabel, fontdict=font)
        plt.title('WindowSize = ' + str(windowSize) + ' Sigma Factor = ' + str(sigma), fontdict=font)

        fp = os.path.join(plotDir,fileName)
        # plotName = f'{fp}_W{windowSize}S{sigma}_{sensorType}{lightDark}_{waveBand}.png'
        plotName = f'{fp}_{sensorType}{lightDark}_{waveBand}.png'

        print(plotName)
        plt.savefig(plotName)
        plt.close()
        # except:
        #     e = sys.exc_info()[0]
        #     print("Error: %s" % e)

    @staticmethod
    def getDateTime(gp):
        dateTagDS = gp.getDataset('DATETAG')
        dateTags = dateTagDS.data["NONE"].tolist()
        timeTagDS = gp.getDataset('TIMETAG2')
        timeTags = timeTagDS.data["NONE"].tolist()
        # Conversion not set up for vectors, loop it
        dateTime=[]
        for i, dateTag in enumerate(dateTags):
            dt = Utilities.dateTagToDateTime(dateTag)
            dateTime.append(Utilities.timeTag2ToDateTime(dt,timeTags[i]))

        return dateTime
    @staticmethod
    def generateTempCoeffs(InternalTemp, uncDS, ambTemp, sensor):

        # Get the reference temperature
        if 'REFERENCE_TEMP' in uncDS.attributes:
            refTemp = float(uncDS.attributes["REFERENCE_TEMP"])
        else:
            print("reference temperature not found")
            print("aborting ...")
            return None

        # Get thermal coefficient from characterization
        uncDS.datasetToColumns()
        therm_coeff = uncDS.data[list(uncDS.columns.keys())[2]]
        therm_unc = uncDS.data[list(uncDS.columns.keys())[3]]
        ThermCorr = []
        ThermUnc = []

        # Seabird case
        if ConfigFile.settings['SensorType'].lower() == "seabird" or ConfigFile.settings['SensorType'].lower() == "dalec":
            for i in range(len(therm_coeff)):
                try:
                    ThermCorr.append(1 + (therm_coeff[i] * (InternalTemp - refTemp)))
                    if ConfigFile.settings["bL1bCal"] == 3:
                        ThermUnc.append(np.abs(therm_unc[i] * (InternalTemp - refTemp)) / 2)
                        # div by 2 because uncertainty is k=2
                    else:
                        ThermUnc.append(np.abs(therm_coeff[i] * (InternalTemp - refTemp)))
                except IndexError:
                    ThermCorr.append(1.0)
                    ThermUnc.append(0)

        # TRIOS case: no temperature available
        elif ConfigFile.settings['SensorType'].lower() == "trios":
            # For Trios the radiometer InternalTemp is a place holder filled with 0.
            # We use ambiant_temp+2.5° instead to estimate internal temp
            for i in range(len(therm_coeff)):
                try:
                    ThermCorr.append(1 + (therm_coeff[i] * (InternalTemp+ambTemp+5 - refTemp)))
                    if ConfigFile.settings["bL1bCal"] == 3:
                        ThermUnc.append(np.abs(therm_unc[i]*(InternalTemp+ambTemp+5 - refTemp)) / 2)
                        # uncertainty is k=2 from char file
                    else:
                        ThermUnc.append(np.abs(therm_coeff[i] * (InternalTemp+ambTemp+5 - refTemp)))
                except IndexError:
                    ThermCorr.append(1.0)
                    ThermUnc.append(0)

        # Change thermal general coefficients into ones specific for processed data
        uncDS.columns[f"{sensor}_TEMPERATURE_COEFFICIENTS"] = ThermCorr
        uncDS.columns[f"{sensor}_TEMPERATURE_UNCERTAINTIES"] = ThermUnc
        uncDS.columnsToDataset()

        return True

    @staticmethod
    def UncTempCorrection(node):
        unc_grp = node.getGroup("RAW_UNCERTAINTIES")
        sensorID = Utilities.get_sensor_dict(node)
        # inv_ID = {v: k for k, v in sensorID.items()}
        for sensor in ["LI", "LT", "ES"]:
            TempCoeffDS = unc_grp.getDataset(sensor+"_TEMPDATA_CAL")

            ### Seabird
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                if "TEMP" in node.getGroup(f'{sensor}_LIGHT').datasets:
                    TempDS = node.getGroup(f'{sensor}_LIGHT').getDataset("TEMP")
                elif "SPECTEMP" in node.getGroup(f'{sensor}_LIGHT').datasets:
                    TempDS = node.getGroup(f'{sensor}_LIGHT').getDataset("SPECTEMP")
                else:
                    msg = "Thermal dataset not found"
                    print(msg)
                # internal temperature is the mean of all replicate
                internalTemp = np.mean(np.array(TempDS.data.tolist()))
                # ambiant temp is not needed for seabird as internal temp is measured, set to 0
                ambTemp = 0
                if not Utilities.generateTempCoeffs(internalTemp, TempCoeffDS, ambTemp, sensor):
                    msg = "Failed to generate Thermal Coefficients"
                    print(msg)

            ### Dalec
            elif ConfigFile.settings['SensorType'].lower() == "dalec":
                if "SPECTEMP" in node.getGroup(f'{sensor}').datasets:
                    TempDS = node.getGroup(f'{sensor}').getDataset("SPECTEMP")
                else:
                    msg = "Thermal dataset not found"
                    print(msg)
                # internal temperature is the mean of all replicate
                internalTemp = np.mean(np.array(TempDS.data.tolist()))
                # ambiant temp is not needed for seabird as internal temp is measured, set to 0
                ambTemp = 0
                if not Utilities.generateTempCoeffs(internalTemp, TempCoeffDS, ambTemp, sensor):
                    msg = "Failed to generate Thermal Coefficients"
                    print(msg)

            ### Trios
            elif ConfigFile.settings['SensorType'].lower() == "trios":
                # No internal temperature available for Trios, set to 0.
                internalTemp = 0
                # Ambiant temperature is needed to estimate internal temperature instead.
                RadcalDS = unc_grp.getDataset(sensor+"_RADCAL_CAL")
                if 'AMBIENT_TEMP' in RadcalDS.attributes:
                    ambTemp = float(RadcalDS.attributes["AMBIENT_TEMP"])
                else:
                    print("Ambient temperature not found")
                    print("Aborting ...")
                    return None
                if not Utilities.generateTempCoeffs(internalTemp, TempCoeffDS, ambTemp, sensor):
                    msg = "Failed to generate Thermal Coefficients"
                    print(msg)

        return True


    @staticmethod
    def get_sensor_dict(node):
        sensorID = {}
        for grp in node.groups:
            # if "CalFileName" in grp.attributes:
            if ConfigFile.settings['SensorType'].lower() == 'seabird':
                # Provision for sensor calibration names without leading zeros
                if "ES_" in grp.id or "LI_" in grp.id or "LT_" in grp.id:
                    sensorCode = grp.attributes["CalFileName"][3:7]
                    if not sensorCode.isnumeric():
                        sensorCode = re.findall(r'\d+', sensorCode)
                    if len(sensorCode) < 4:
                        sensorCode = '0' + sensorCode[0]

                if "ES_" in grp.id:
                    sensorID[sensorCode] = "ES"
                    # sensorID[grp.attributes["CalFileName"][3:7]] = "ES"
                if "LI_" in grp.id:
                    sensorID[sensorCode] = "LI"
                if "LT_" in grp.id:
                    sensorID[sensorCode] = "LT"

            # elif "IDDevice" in grp.attributes:
            elif ConfigFile.settings['SensorType'].lower() == 'trios':
                if "ES" in grp.datasets:
                    sensorID[grp.attributes["IDDevice"][4:8]] = "ES"
                if "LI" in grp.datasets:
                    sensorID[grp.attributes["IDDevice"][4:8]] = "LI"
                if "LT" in grp.datasets:
                    sensorID[grp.attributes["IDDevice"][4:8]] = "LT"

        return sensorID


    @staticmethod
    def RenameUncertainties_Class(node):
        """
        Rename unc dataset from generic class-based id to sensor type
        TODO: adapted to old version of ckass-based file, will be switch to next version
        when ready. Next version is commented below.
        """
        unc_group = node.getGroup("RAW_UNCERTAINTIES")
        sensorID = Utilities.get_sensor_dict(node) # should result in OD{[Instr#:ES, Instr#:LI, Instr#:LT]}
        print("sensors type", sensorID)
        names = [i for i in unc_group.datasets]  # get names in advance, mutation of iteration object breaks for loop
        for name in names:
            ds = unc_group.getDataset(name)

            if "_RADIANCE_" in name:
                # Class-based radiance coefficient are the same for both Li and Lt
                new_LI_name = ''.join(["LI", name.split("RADIANCE")[-1]])
                new_LI_ds = unc_group.addDataset(new_LI_name)
                new_LI_ds.copy(ds)
                new_LI_ds.datasetToColumns()

                new_LT_name = ''.join(["LT", name.split("RADIANCE")[-1]])
                new_LT_ds = unc_group.addDataset(new_LT_name)
                new_LT_ds.copy(ds)
                new_LT_ds.datasetToColumns()
                unc_group.removeDataset(ds.id) # remove dataset

            if "_IRRADIANCE_" in name:
                # Class-based irradiance coefficient are unique for Es
                new_ES_name = ''.join(["ES", name.split("IRRADIANCE")[-1]])
                new_ES_ds = unc_group.addDataset(new_ES_name)
                new_ES_ds.copy(ds)
                new_ES_ds.datasetToColumns()
                unc_group.removeDataset(ds.id) # remove dataset

            if "_LI_" in name:
                # Class-based irradiance coefficient are unique for Es
                new_name = ''.join(["LI", name.split("LI")[-1]])
                new_ds = unc_group.addDataset(new_name)
                new_ds.copy(ds)
                new_ds.datasetToColumns()
                unc_group.removeDataset(ds.id) # remove dataset

            if "_LT_" in name:
                # Class-based irradiance coefficient are unique for Es
                new_name = ''.join(["LT", name.split("LT")[-1]])
                new_ds = unc_group.addDataset(new_name)
                new_ds.copy(ds)
                new_ds.datasetToColumns()
                unc_group.removeDataset(ds.id) # remove dataset

            if "_RADCAL_" in name:
                # RADCAL are always sensor specific
                for sensor in sensorID:
                    if sensor in ds.id:
                        new_ds_name = ''.join([sensorID[sensor], ds.id.split(sensor)[-1]])
                        new_ds = unc_group.addDataset(new_ds_name)
                        new_ds.copy(ds)
                        new_ds.datasetToColumns()
                        unc_group.removeDataset(ds.id)  # remove dataset

        return True


    # @staticmethod
    # def RenameUncertainties_Class(node):
    #     """
    #     Rename unc dataset from generic class-based id to sensor type
    #     """
    #     unc_group = node.getGroup("RAW_UNCERTAINTIES")
    #     sensorID = Utilities.get_sensor_dict(node) # should result in OD{[Instr#:ES, Instr#:LI, Instr#:LT]}
    #     print("sensors type", sensorID)
    #     names = [i for i in unc_group.datasets]  # get names in advance, mutation of iteration object breaks for loop
    #     for name in names:
    #         ds = unc_group.getDataset(name)

    #         if "_RADIANCE_" in name:
    #             # Class-based radiance coefficient are the same for both Li and Lt
    #             new_LI_name = ''.join(["LI", name.split("RADIANCE")[-1]])
    #             new_LI_ds = unc_group.addDataset(new_LI_name)
    #             new_LI_ds.copy(ds)
    #             new_LI_ds.datasetToColumns()

    #             new_LT_name = ''.join(["LT", name.split("RADIANCE")[-1]])
    #             new_LT_ds = unc_group.addDataset(new_LT_name)
    #             new_LT_ds.copy(ds)
    #             new_LT_ds.datasetToColumns()
    #             unc_group.removeDataset(ds.id) # remove dataset

    #         if "_IRRADIANCE_" in name:
    #             # Class-based irradiance coefficient are unique for Es
    #             new_ES_name = ''.join(["ES", name.split("IRRADIANCE")[-1]])
    #             new_ES_ds = unc_group.addDataset(new_ES_name)
    #             new_ES_ds.copy(ds)
    #             new_ES_ds.datasetToColumns()
    #             unc_group.removeDataset(ds.id) # remove dataset

    #         if "_RADCAL_" in name:
    #             # RADCAL are always sensor specific
    #             for sensor in sensorID:
    #                 if sensor in ds.id:
    #                     new_ds_name = ''.join([sensorID[sensor], ds.id.split(sensor)[-1]])
    #                     new_ds = unc_group.addDataset(new_ds_name)
    #                     new_ds.copy(ds)
    #                     new_ds.datasetToColumns()
    #                     unc_group.removeDataset(ds.id)  # remove dataset

    #     return True


    @staticmethod
    def RenameUncertainties_FullChar(node):
        """
        Rename unc dataset from specific sensor id to sensor type
        """
        unc_group = node.getGroup("RAW_UNCERTAINTIES")
        sensorID = Utilities.get_sensor_dict(node) # should result in OD{[Instr#:ES, Instr#:LI, Instr#:LT]}
        print("sensors type", sensorID)
        names = [i for i in unc_group.datasets]  # get names in advance, mutation of iteration object breaks for loop
        for name in names:
            ds = unc_group.getDataset(name)
            for sensor in sensorID:
                if sensor in ds.id:
                    new_ds_name = ''.join([sensorID[sensor], ds.id.split(sensor)[-1]])
                    new_ds = unc_group.addDataset(new_ds_name)
                    new_ds.copy(ds)
                    new_ds.datasetToColumns()
                    unc_group.removeDataset(ds.id)  # remove  dataset
        return True


    @staticmethod
    def interpUncertainties_Factory(node):

        grp = node.getGroup("RAW_UNCERTAINTIES")
        sensorList = ['ES', 'LI', 'LT']
        for sensor in sensorList:

            ## retrieve dataset from corresponding instrument
            data = None
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                data = node.getGroup(sensor+'_LIGHT').getDataset(sensor)
            elif ConfigFile.settings['SensorType'].lower() == "trios" or ConfigFile.settings['SensorType'].lower() == "dalec":
                data = node.getGroup(sensor).getDataset(sensor)

            # Retrieve hyper-spectral wavelengths from dataset
            x_new = np.array(pd.DataFrame(data.data).columns, dtype=float)

            for data_type in ["_RADCAL_UNC"]:
                ds = grp.getDataset(sensor+data_type)
                ds.datasetToColumns()
                x = ds.columns['wvl']
                y = ds.columns['unc']
                y_new = np.interp(x_new, x, y)
                ds.columns['unc'] = y_new
                ds.columns['wvl'] = x_new
                ds.columnsToDataset()


            ## Interpolate for initial class-based file, in use at the moment
            for data_type in ["_TEMPDATA_CAL"]:
                ds = grp.getDataset(sensor + data_type)
                ds.datasetToColumns()
                x = ds.columns['1']
                for indx in range(2, len(ds.columns)):
                    y = ds.columns[str(indx)]
                    y_new = np.interp(x_new, x, y)
                    ds.columns[str(indx)] = y_new
                # column ['0'] longer than the rest due to interpolation - this is a quick work around
                ds.columns['0'] = np.array(
                    range(len(x_new)))  # np.array(ds.columns['0'])[1:] # drop 1st line from TARTU file
                ds.columns['1'] = x_new
                ds.columnsToDataset()

            ## Interpolate for initial class-based file, in use at the moment
            for data_type in ["_POLDATA_CAL", "_STABDATA_CAL", "_NLDATA_CAL"]:
                ds = grp.getDataset(sensor + data_type)
                ds.datasetToColumns()
                x = ds.columns['0']
                y = ds.columns['1']
                y_new = np.interp(x_new, x, y)
                ds.columns['0'] = x_new
                ds.columns['1'] = y_new
                ds.columnsToDataset()


            ### for updated version of class based file, not used at the moment
            # if sensor != "ES":
            #     for data_type in ["_POLDATA_CAL","_TEMPDATA_CAL"]:
            #         ds = grp.getDataset(sensor+data_type)
            #         ds.datasetToColumns()
            #         x = ds.columns['1']
            #         for indx in range(2,len(ds.columns)):
            #             y = ds.columns[str(indx)]
            #             y_new = np.interp(x_new, x, y)
            #             ds.columns[str(indx)] = y_new
            #         # column ['0'] longer than the rest due to interpolation - this is a quick work around
            #         ds.columns['0'] = np.array(range(len(x_new))) # np.array(ds.columns['0'])[1:] # drop 1st line from TARTU file
            #         ds.columns['1'] = x_new
            #         ds.columnsToDataset()
            # else:
            #     for data_type in ["_TEMPDATA_CAL","_ANGDATA_COSERROR", "_ANGDATA_COSERROR_AZ90", "_ANGDATA_UNCERTAINTY", "_ANGDATA_UNCERTAINTY_AZ90"]:
            #         ds = grp.getDataset(sensor+data_type)
            #         ds.datasetToColumns()
            #         x = ds.columns['1']
            #         for indx in range(2,len(ds.columns)):
            #             y = ds.columns[str(indx)]
            #             y_new = np.interp(x_new, x, y)
            #             ds.columns[str(indx)] = y_new
            #         # quick workaround for bug desovered in parsing uncertainties
            #         # one column of TEMPDATA_CAL is longer than the others!
            #         ds.columns['0'] = np.array(range(len(x_new))) # drop 1st line from TARTU file
            #         ds.columns['1'] = x_new
            #         ds.columnsToDataset()

        return True


    @staticmethod
    def interpUncertainties_Class(node):

        grp = node.getGroup("RAW_UNCERTAINTIES")
        sensorList = ['ES', 'LI', 'LT']
        for sensor in sensorList:

            ## retrieve dataset from corresponding instrument
            data = None
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                data = node.getGroup(sensor+'_LIGHT').getDataset(sensor)
            elif ConfigFile.settings['SensorType'].lower() == "trios":
                data = node.getGroup(sensor).getDataset(sensor)

            # Retrieve hyper-spectral wavelengths from dataset
            x_new = np.array(pd.DataFrame(data.data).columns, dtype=float)


            # RADCAL data do not need interpolation, just removing the first line
            for data_type in ["_RADCAL_CAL"]:
                ds = grp.getDataset(sensor+data_type)
                ds.datasetToColumns()
                for indx in range(len(ds.columns)):
                    indx_name = str(indx)
                    if indx_name != '':
                        y = np.array(ds.columns[indx_name])
                        if len(y)==255:
                            ds.columns[indx_name] = y
                        elif len(y)==256:
                            # drop 1st line from TARTU file
                            ds.columns[indx_name] = y[1:]
                ds.columnsToDataset()

            ## Interpolate for initial class-based file, in use at the moment
            for data_type in ["_TEMPDATA_CAL"]:
                ds = grp.getDataset(sensor + data_type)
                ds.datasetToColumns()
                x = ds.columns['1']
                for indx in range(2, len(ds.columns)):
                    y = ds.columns[str(indx)]
                    y_new = np.interp(x_new, x, y)
                    ds.columns[str(indx)] = y_new
                # column ['0'] longer than the rest due to interpolation - this is a quick work around
                ds.columns['0'] = np.array(
                    range(len(x_new)))  # np.array(ds.columns['0'])[1:] # drop 1st line from TARTU file
                ds.columns['1'] = x_new
                ds.columnsToDataset()

            ## Interpolate for initial class-based file, in use at the moment
            for data_type in ["_POLDATA_CAL", "_STABDATA_CAL", "_NLDATA_CAL"]:
                ds = grp.getDataset(sensor + data_type)
                ds.datasetToColumns()
                x = ds.columns['0']
                y = ds.columns['1']
                y_new = np.interp(x_new, x, y)
                ds.columns['0'] = x_new
                ds.columns['1'] = y_new
                ds.columnsToDataset()

            ### for updated version of class based file, not used at the moment
            # if sensor != "ES":
            #     for data_type in ["_POLDATA_CAL","_TEMPDATA_CAL"]:
            #         ds = grp.getDataset(sensor+data_type)
            #         ds.datasetToColumns()
            #         x = ds.columns['1']
            #         for indx in range(2,len(ds.columns)):
            #             y = ds.columns[str(indx)]
            #             y_new = np.interp(x_new, x, y)
            #             ds.columns[str(indx)] = y_new
            #         # column ['0'] longer than the rest due to interpolation - this is a quick work around
            #         ds.columns['0'] = np.array(range(len(x_new))) # np.array(ds.columns['0'])[1:] # drop 1st line from TARTU file
            #         ds.columns['1'] = x_new
            #         ds.columnsToDataset()
            # else:
            #     for data_type in ["_TEMPDATA_CAL","_ANGDATA_COSERROR", "_ANGDATA_COSERROR_AZ90", "_ANGDATA_UNCERTAINTY", "_ANGDATA_UNCERTAINTY_AZ90"]:
            #         print(data_type)
            #         ds = grp.getDataset(sensor+data_type)
            #         ds.datasetToColumns()
            #         x = ds.columns['1']
            #         for indx in range(2,len(ds.columns)):
            #             y = ds.columns[str(indx)]
            #             y_new = np.interp(x_new, x, y)
            #             ds.columns[str(indx)] = y_new
            #         # quick workaround for bug desovered in parsing uncertainties
            #         # one column of TEMPDATA_CAL is longer than the others!
            #         ds.columns['0'] = np.array(range(len(x_new))) # drop 1st line from TARTU file
            #         ds.columns['1'] = x_new
            #         ds.columnsToDataset()

            ## RADCAL_LAMP/: Interpolate data to hyper-spectral pixels
            for data_type in ["_RADCAL_LAMP"]:
                ds = grp.getDataset(sensor+data_type)
                ds.datasetToColumns()
                x = ds.columns['0']
                for indx in range(1,len(ds.columns)):
                    y = ds.columns[str(indx)]
                    y_new = np.interp(x_new, x, y)
                    ds.columns[str(indx)] = y_new
                ds.columns['0'] = x_new
                ds.columnsToDataset()

            ## RADCAL_PANEL: only for Li & Lt
            if sensor != "ES":
                for data_type in ["_RADCAL_PANEL"]:
                    ds = grp.getDataset(sensor+data_type)
                    ds.datasetToColumns()
                    x = ds.columns['0']
                    for indx in range(1,len(ds.columns)):
                        y = ds.columns[str(indx)]
                        y_new = np.interp(x_new, x, y)
                        ds.columns[str(indx)] = y_new
                    ds.columns['0'] = x_new
                    ds.columnsToDataset()

        return True


    @staticmethod
    def interpUncertainties_FullChar(node):
        """
        For full char, all input comes already with a wavelength columns,
        except RADCAL LAMP ad PANEL, that need to be interpolated on wvl.
        """

        grp = node.getGroup("RAW_UNCERTAINTIES")
        # sensorId = Utilities.get_sensor_dict(node)
        sensorList = ['ES', 'LI', 'LT']
        for sensor in sensorList:

            ds = grp.getDataset(sensor+"_RADCAL_CAL")
            ds.datasetToColumns()
            # indx = ds.attributes["INDEX"]
            # pixel = np.array(ds.columns['0'[1:])
            bands = np.array(ds.columns['1'][1:])
            coeff = np.array(ds.columns['2'][1:])
            valid = bands>0
            # x_new2 = bands[valid]

            ## retrieve hyper-spectral wavelengths from corresponding instrument
            data = None
            if ConfigFile.settings['SensorType'].lower() == "seabird":
                data = node.getGroup(sensor+'_LIGHT').getDataset(sensor)
            elif ConfigFile.settings['SensorType'].lower() == "trios":
                # inv_dict = {v: k for k, v in sensorId.items()}
                # data = node.getGroup('SAM_'+inv_dict[sensor]+'.dat').getDataset(sensor)
                data = node.getGroup(sensor).getDataset(sensor)

            x_new = np.array(pd.DataFrame(data.data).columns, dtype=float)

            # intersect, ind1, valid = np.intersect1d(x_new, bands, return_indices=True)
            if len(bands[valid]) != len(x_new):
                print("ERROR: band wavelength not found in calibration file")
                print(len(bands[valid]))
                print(len(x_new))
                # exit()
                return False

            ## RADCAL_LAMP: Interpolate data to hyper-spectral pixels
            for data_type in ["_RADCAL_LAMP"]:
                ds = grp.getDataset(sensor+data_type)
                ds.datasetToColumns()
                x = ds.columns['0']
                for indx in range(1,len(ds.columns)):
                    y = ds.columns[str(indx)]
                    y_new = np.interp(x_new, x, y)
                    ds.columns[str(indx)] = y_new
                ds.columns['0'] = x_new
                ds.columnsToDataset()

            ## RADCAL_PANEL: interplation only for Li & Lt
            if sensor != "ES":
                for data_type in ["_RADCAL_PANEL"]:
                    ds = grp.getDataset(sensor+data_type)
                    ds.datasetToColumns()
                    x = ds.columns['0']
                    for indx in range(1,len(ds.columns)):
                        y = ds.columns[str(indx)]
                        y_new = np.interp(x_new, x, y)
                        ds.columns[str(indx)] = y_new
                    ds.columns['0'] = x_new
                    ds.columnsToDataset()

        return True

    @staticmethod
    def getline(sstream, delimiter: str = '\n') -> str:
        """replicates C++ getline functionality - reads a string until delimiter character is found
        :sstream: string stream, reference to an open file in 'read' mode [with open(file_path, 'r') as sstream:]
        :delimiter: the newline delimiter used in the file being read - default = '\n' Newline
        :return type: string"""
        def _gen():
            while True:
                line = sstream.readline()
                if delimiter in line:
                    yield line[0:line.index(delimiter)]
                    break
                elif line:
                    yield line
                else:
                    break

        return "".join(_gen())


    @staticmethod
    def parseLine(line: str, ds) -> None:
        """parses a line of data to a HDFDataset depending on the index attribute. This attribute must be called 'INDEX'
        and have length equal to the split line of data
        :line: string - line of data to be read
        :ds: HDFDataset
        """
        index = ds.attributes['INDEX']
        # [x for x in ds.attributes['INDEX'] if x != ' ']
        # TODO: fix way of finding the index
        for i, x in enumerate(line.split('\t')):
            if x:
                if index[i] not in ds.columns.keys():
                    ds.columns[index[i]] = []
                try:
                    ds.columns[index[i]].append(float(x))
                except ValueError:
                    ds.columns[index[i]].append(x)


    # @staticmethod
    # def read_unc(filepath: str, gp) -> None:
    #     """
    #     Reads in L1/L2 data using the header to organise the data storage object
    #     :filepath: - the full path to the file to be opened, requires a file to have begin_data and end_data before
    #     and after the main data body
    #     :gp: HDFGroup object - Input data is stored as HDFDatasets and appended to this group.
    #     return type: None - may be changed to bool for better error handling
    #     """
    #     begin_data = False  # set up data flag
    #     attrs = {}
    #     end_flag = 0

    #     with open(filepath, 'r', encoding="utf-8") as f:  # open file
    #         key = None; index = None
    #         while True:  # start loop
    #             line = Utilities.getline(f, '\n')  # reads the file until a '\n' character is reached
    #             if end_flag == 0:  # end condition not met

    #                 if '[END_OF_CALDATA]' in line:  # end conditions met
    #                     begin_data = False  # set to not collect data
    #                     ds.columnsToDataset()  # convert read data to dataset
    #                     end_flag = 1

    #                 elif line.startswith('!'):  # first lines start with '!' so can be used to determine which file is being read
    #                     if 'FRM' in line:
    #                         gp.attributes['INSTRUMENT_CAL_TYPE'] = line[1:]
    #                     else:
    #                         caltype = line[1:]
    #                         if 'CAL_FILE' not in gp.attributes.keys():
    #                             gp.attributes['CAL_FILE'] = []
    #                         gp.attributes['CAL_FILE'].append(line[1:])

    #                 # elif line.startswith('SAT'):
    #                 #     device = line.rstrip()
    #                 #     name = device+'_'+caltype

    #                 # elif line.startswith('SAM_'):
    #                 #     device = line.rstrip()
    #                 #     name = device+'_'+caltype

    #                 elif begin_data:
    #                     Utilities.parseLine(line, ds)  # add the data

    #                 else:  # part of header
    #                     if '[CALDATA]' in line:  # begin reading data
    #                         begin_data = True
    #                         ds = gp.addDataset(name)
    #                         if ds is None:
    #                             ds = gp.getDataset(name)
    #                         ds.attributes['INDEX'] = [x for x in index if x != ' ']  # populate ds attributes with column names
    #                         index = None
    #                         # populate ds attributes with header data
    #                         for k, v in attrs.items():
    #                             ds.attributes[k] = v  # set the attributes
    #                         attrs.clear()

    #                     else:  # part of header, check if attribute or column names
    #                         if line.startswith('['):  # if line has '[ ]' then take the next line as the attribute
    #                             key = line[1:-1]
    #                         elif key is not None:
    #                             attrs[key] = line
    #                             if key == "DEVICE":
    #                                 device = line.rstrip()
    #                                 name = device+'_'+caltype
    #                             key = None
    #                         else:  # only blank lines and comments get here
    #                             if index is None and len(line.split(',')) > 2:  # if comma separated then must be column names!
    #                                 index = list(line[1:].split(','))

    #             else:  # check for end condition
    #                 # this will skip the first real line after 'END_OF_XXXXDATA', however this is always a comment so ignored.
    #                 if end_flag >= 3:
    #                     break  # end if empty lines found after [END_DATA], else more data to be read
    #                 elif not line:
    #                     end_flag += 1
    #                 else:
    #                     end_flag = 0

    @staticmethod
    def parseLine_no_index(line: str, ds) -> None:
        for i, x in enumerate(line.split('\t')):
            if x:
                if str(i) not in ds.columns.keys():
                    ds.columns[str(i)] = []
                try:
                    ds.columns[str(i)].append(float(x))
                except ValueError:
                    ds.columns[str(i)].append(x)

    @staticmethod
    def read_char(filepath: str, gp) -> None:
        begin_data = False  # set up data flag
        attrs = {}
        end_count = 0
        Azimuth_angle = None

        with open(filepath, 'r', encoding="utf-8") as f:  # open file
            key, ds, name = None, None, None
            while True:  # start loop
                line = Utilities.getline(f, '\n')  # reads the file until a '\n' character is reached
                if not line:  # breaks out of loop if three empty lines in a row
                    if end_count < 3:
                        end_count += 1
                    else:
                        return "end condition reached"
                elif not line.startswith('#'):  # not a comment
                    end_count = 0
                    if begin_data:
                        if 'end' in line.lower():  # end conditions met
                            begin_data = False  # set to read header data
                            ds.columnsToDataset()  # convert read data to dataset
                        else:
                            Utilities.parseLine_no_index(line, ds)  # add the data
                    else:  # part of header
                        if line.startswith('!'):  # get filetype from ! comment
                            if line != '!FRM4SOC_CP':
                                gp.attributes['CHARACTERISATION_FILE_TYPE'] = line[1:]
                        elif any([k in line.lower() for k in ['data', 'lsf', 'uncertainty', 'coserror']]) is True:
                        # elif ['data', 'lsf', 'uncertainty'] in line.lower():  # begin reading data
                            begin_data = True
                            attrs['DATA_TYPE'] = line[1:line.lower().find('data')]
                            ds = gp.addDataset(f"{name}_{attrs['DATA_TYPE']}")
                            if ds is None:
                                if 'AZIMUTH_ANGLE' in attrs:  # reading angular file and has identical identifiers for different az angles
                                    ds = gp.addDataset(f"{name}_{attrs['DATA_TYPE']}_AZ{attrs['AZIMUTH_ANGLE']}")
                                    Azimuth_angle = attrs['AZIMUTH_ANGLE']
                                elif Azimuth_angle is not None:  # uncertainty also repeated so save the az angle from earlier to use here
                                    ds = gp.addDataset(f"{name}_{attrs['DATA_TYPE']}_AZ{Azimuth_angle}")
                                    Azimuth_angle = None
                                else:
                                    msg = f"dataset could not be contructed, Utilties.read_char(file-path, HDFGroup) in {gp.attributes['CHARACTERISATION_FILE_TYPE']}"
                                    print(msg)
                                    raise KeyError
                            # populate ds attributes with header data
                            for k, v in attrs.items():
                                ds.attributes[k] = v  # set the attributes
                            attrs.clear()

                        else:  # part of header, check if attribute or column names
                            if line.startswith('['):  # if line has '[ ]' then take the next line as the attribute
                                key = line[1:-1]
                            elif key is not None:
                                attrs[key] = line
                                if key.lower() == "device":
                                    device = line.rstrip()
                                    name = device + '_' + gp.attributes['CHARACTERISATION_FILE_TYPE']
                                key = None

    @staticmethod
    def datasetNan2Zero(inputArray):
        ''' Workaround nans within a Group.Dataset '''
        # There must be a better way...
        for ens, row in enumerate(inputArray):
            for i, value in enumerate(row):
                if np.isnan(value):
                    inputArray[ens][i] = 0.0
        return inputArray

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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
                    msg = f'   Flag data from {startstop[0]} to {startstop[1]}'
                    print(msg)
                    Utilities.writeLogFile(msg)
                    bTs.append(startstop)
                    start = -1

        if start != -1 and stop == index: # Records from a mid-point to the end are bad
            startstop = [DT1[start],DT1[stop]]
            bTs.append(startstop)
            msg = f'   Flag additional data from {startstop[0]} to {startstop[1]}'
            print(msg)
            Utilities.writeLogFile(msg)

        if start==0 and stop==index: # All records are bad
            return False

        return bTs

    @staticmethod
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

            msg = f'Screening {group.id} for clean timestamps.'
            print(msg)
            Utilities.writeLogFile(msg)
            if not Utilities.fixDateTime(group):
                msg = f'***********Too few records in {group.id} to continue after timestamp correction. Exiting.'
                print(msg)
                Utilities.writeLogFile(msg)
                return None

        return group

