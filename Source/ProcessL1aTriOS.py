'''Process Raw (L0) data to L1A HDF5'''
import os
import json
from datetime import datetime, timedelta, date
import re
import numpy as np
import pandas as pd
import tables

from Source.MainConfig import MainConfig
from Source.HDFRoot import HDFRoot
from Source.HDFGroup import HDFGroup
import Source.utils.filing as filing
import Source.utils.loggingHCP as logging
import Source.utils.dating as dating


class ProcessL1aTriOS:
    '''Process L1A for TriOS from MSDA-XE'''
    @staticmethod
    def processL1a(fp, outFilePath):
        # fp is a list of all triplets

        configPath = MainConfig.settings['cfgPath']
        cal_path = configPath[0:configPath.rfind('.')] + '_Calibration/'
        # In case full path includes a '.'

        if '.mlb' in fp[0]:   # Multi frame
            # acq_time = []
            acq_name = []
            for file in fp:

                ## Test filename for station/cast
                # XXXXS for light, XXXXD for caps-on dark
                # XXXXR for blocked sunlight irradiance
                def parse_filename(fileStr):
                    ''' Test filename for datetime or station/cast light/dark '''
                    matches = []
                    matchTypes = []
                    # Possibilities:
                    #   YYYYMMDD_hhmmss, YYYY_MM_DD_hh_mm_ss, YYYYMMDD_hh_mm_ss,YYYY_MM_DD_hhmmss
                    #   SSCCS, SSCCD
                    for i, pattern in enumerate([
                        r'\d{8}.\d{6}', 
                        r'\d{4}.\d{2}.\d{2}.\d{2}.\d{2}.\d{2}',
                        r'\d{8}.\d{2}.\d{2}.\d{2}',
                        r'\d{4}.\d{2}.\d{2}.\d{6}',
                        r'\d{4}S', 
                        r'\d{4}D',
                        r'\d{4}R',]):

                        match = re.search(pattern, fileStr)
                        if match is not None:
                            matches.append(match.group(0))
                            if i < 3:
                                matchTypes.append('datetime')
                            else:
                                matchTypes.append('stationcast')

                    if len(matches) == 0:
                        raise IndexError
                    if 'stationcast' in matchTypes:
                        fileDesignation = matches[matchTypes.index('stationcast')]
                        matchType = 'stationcast'
                    else:
                        fileDesignation = matches[0] # Any of the datetimes
                        matchType = 'datetime'
                    return fileDesignation, matchType

                try:
                    a_name, a_type = parse_filename(file.split('/')[-1])
                except IndexError:
                    print(f'Full path file: {file}')
                    print("  ERROR: no identifier recognized in TRIOS L0 file name" )
                    print("  L0 filename should have a cast to identify triplet instrument")
                    print("  ending in 4 digits before S.mlb (light) or D.mlb for caps-on dark. ")
                    msg = 'PL1aTriOS raw filename not recognized'
                    logging.writeLogFileAndPrint(msg)
                    return None,None

                acq_name.append(a_name)

            acq_name = list(dict.fromkeys(acq_name)) # Returns unique names

            outFFP = []
            for a_name in acq_name:
                print("")
                print("Generate the telemetric file...")
                print('Processing: ' +a_name)

                tables.file._open_files.close_all() # Why is this necessary?

                # For each triplet, this creates an HDF
                root = HDFRoot()
                root.id = "/"
                root.attributes["WAVELENGTH_UNITS"] = "nm"
                root.attributes["LI_UNITS"] = "count"
                root.attributes["LT_UNITS"] = "count"
                root.attributes["ES_UNITS"] = "count"
                root.attributes["SATPYR_UNITS"] = "count"
                root.attributes["PROCESSING_LEVEL"] = "1a"

                ffp = [s for s in fp if a_name in s]
                root.attributes["RAW_FILE_NAME"] = str(ffp)
                root.attributes["CAST"] = a_name
                match = re.search(r"\dD$", a_name)
                outFilePathDark = os.path.join(outFilePath+'/DARK')
                if match is not None:
                    logging.writeLogFileAndPrint(f'Caps-on dark file recognized {a_name}.')
                    cod = True
                    root.attributes["FRAME_TYPE"] = 'caps-on dark'
                    if os.path.isdir(outFilePathDark) is False:
                        os.mkdir(outFilePathDark)
                else:
                    cod = False
                    root.attributes["FRAME_TYPE"] = 'light'
                for file in ffp:
                    if "SAM_" in file:
                        # Regex accomodate both SAM_1234_ and SAM1234 conventions
                        serialNumber = re.findall(r'SAM_?(\d+)_', os.path.basename(file))[0]
                    else:
                        logging.writeLogFileAndPrint("ERROR : naming convention is not respected")
                        serialNumber = None

                    start,stop = ProcessL1aTriOS.formatting_instrument(serialNumber,cal_path,file,root,configPath)

                    if start is None:
                        return None, None
                    acq_datetime = datetime.strptime(start,"%Y%m%dT%H%M%SZ")
                    root.attributes["TIME-STAMP"] = datetime.strftime(acq_datetime,'%a %b %d %H:%M:%S %Y')
                    # Update to something like "YYYY-MM-DDTHH:MM:SS UTC"
                    root.attributes["TIME_COVERAGE_START"] = datetime.strftime(acq_datetime,'%a %b %d %H:%M:%S %Y')
                    acq_datetime = datetime.strptime(stop,"%Y%m%dT%H%M%SZ")
                    root.attributes["TIME_COVERAGE_END"] = datetime.strftime(acq_datetime,'%a %b %d %H:%M:%S %Y')


                # File naming convention on TriOS TBD depending on convention used in MSDA_XE
                #The D-6 requirements to add the timestamp manually on every acquisition is impractical.
                #Convert to using any unique name and append timestamp from data (start)
                try:
                    new_name = a_name #acq_name[0]
                    # new_name = file.split('/')[-1].split('.mlb')[0].split(f'SAM_{name}_RAW_SPECTRUM_')[1]
                    # NOTE: For caps-on darks, we require a 4-digit station number plus 'S' or 'D' for light or dark, respectively
                    # If this is a stationcast type filename, append the start time from the data:
                    if (re.search(r'\d{4}[DSR]', file.split('/')[-1]) is not None) or (a_type == 'stationcast'):
                        new_name = str(start)+'_'+new_name
                except IndexError as err:
                    logging.writeLogFileAndPrint(f"Error in naming of Raw files {err}")
                    return None, None
                    # new_name = file.split('/')[-1].split('.mlb')[0].split(f'SAM_{name}_Spectrum_RAW_')[1]

                if cod:
                    outFFP.append(os.path.join(outFilePathDark,f'{new_name}_L1A.hdf'))
                else:
                    outFFP.append(os.path.join(outFilePath,f'{new_name}_L1A.hdf'))
                root.attributes["L1A_FILENAME"] = outFFP[-1]

                root = ProcessL1aTriOS.fixChronology(root)

                # If Lat/Lon from MSDA file is valid, create a GPS group
                for gp in root.groups:
                    for ds in gp.datasets:
                        if ds == 'ES':
                            lat = gp.datasets['LATITUDE']
                            lon = gp.datasets['LONGITUDE']
                            dateTag = gp.datasets['DATETAG']
                            timeTag2 = gp.datasets['TIMETAG2']

                            if not (all(lat.data) == 0 and all(lon.data) == 0):
                                # Initialize a new group for MSDA GPS data
                                gpsGroup = root.addGroup("GPS_MSDA")
                                gpsGroup.attributes['CalFileName'] = 'GPS_MSDA'
                                gpsGroup.addDataset("LATITUDE")
                                gpsGroup.datasets["LATITUDE"].data = np.array(lat.data, dtype=[('NONE', '<f8')])
                                gpsGroup.addDataset("LONGITUDE")
                                gpsGroup.datasets["LONGITUDE"].data = np.array(lon.data, dtype=[('NONE', '<f8')])
                                gpsGroup.addDataset("TIMETAG2")
                                gpsGroup.datasets["TIMETAG2"].data = np.array(timeTag2.data, dtype=[('NONE', '<f8')])
                                gpsGroup.addDataset("DATETAG")
                                gpsGroup.datasets["DATETAG"].data = np.array(dateTag.data, dtype=[('NONE', '<f8')])

                # For Caps-On Dark measurements
                if cod:
                    minSpectra = 5 # minimum number of spectra to estimate T from DN
                    for gpDark in root.groups:
                        if gpDark.id.startswith('SAM'):
                            sensorIDS = ['ES','LI','LT']
                            for ds in gpDark.datasets:
                                if gpDark.datasets[ds].id in sensorIDS:
                                    DN = gpDark.datasets[ds].data[:].tolist()
                                    if len(DN) < minSpectra:
                                        logging.writeLogFileAndPrint("Too few spectra for caps-on dark algorithm. Abort.")
                                        return None, None

                            # Zibordi & Talone, in prep. (2025)
                            # T = -Tc + S * ln(DN-DNc)
                            # RAMSES class coefficients
                            Tc = -16.4
                            S = 6.147
                            DNc = 1438
                            print(f'Running caps-on dark algorithm to estimate internal temp:{gpDark.id}')

                            T = [Tc + S * np.log(dn-DNc) for dn in np.array(DN[:])]
                            # dn-DNc can result in a negative that leaves NaNs from the log...
                            meanT = np.nanmean(T)
                            # meanT = 31 NOTE: use to force COD threshold for testing
                            stdT = np.nanstd(T)
                            # Add dataset CAPSONTEMP for T and sigmaT columns. SPECTEMP reserved for internal thermistor temp (G2 and others)
                            dsT = gpDark.addDataset('CAPSONTEMP')
                            dsT.appendColumn('T',meanT)
                            dsT.appendColumn('sigmaT',stdT)
                            dsT.columnsToDataset()
                elif re.search(r'\d{4}[S]', a_name):
                    darkFile = None
                    if os.path.isdir(outFilePathDark):
                        darkList = os.listdir(outFilePathDark)
                        pattern = f'{a_name[:2]}'+'\\d{2}'+'D'
                        darkFile = [y for y in darkList if re.search(pattern,y) ]
                    if darkFile:
                        rootDark = HDFRoot.readHDF5(os.path.join(outFilePathDark,darkFile[0]))
                        for gpDark in rootDark.groups:
                            if gpDark.id.startswith('SAM'):
                                for gp in root.groups:
                                    if gp.id == gpDark.id:
                                        T = gp.addDataset('CAPSONTEMP')
                                        T.copy(gpDark.datasets['CAPSONTEMP'])
                                        T.datasetToColumns()

                try:
                    # root.writeHDF5(new_name)
                    root.writeHDF5(outFFP[-1])

                except Exception:
                    msg = 'Unable to write L1A file. It may be open in another program.'
                    logging.errorWindow("File Error", msg)
                    logging.writeLogFileAndPrint(msg)
                    return None, None

                # Utilities.checkOutputFiles(outFFP[-1])
                filing.checkOutputFiles(outFFP[-1])

            return root, outFFP
        else:
            print('Single Frame deprecated')

        return None, None

    # use namesList to define dtype for recarray
    @staticmethod
    def reshape_data(NAME,N,data):
        ds_dt = np.dtype({'names':[NAME],'formats':[(float)] })
        tst = np.array(data).reshape((1,N))
        rec_arr2 = np.rec.fromarrays(tst, dtype=ds_dt)
        return rec_arr2

    # def reshape_data_str(NAME,N,data):
    #     dt = h5py.special_dtype(vlen=str)
    #     ds_dt = np.dtype({'names':[NAME],'formats':[dt] })
    #     tst = np.array(data).reshape((1,N))
    #     rec_arr2 = np.rec.fromarrays(tst, dtype=ds_dt)
    #     return rec_arr2

    # Function for reading and formatting .dat data file
    @staticmethod
    def read_dat(inputfile):
        file_dat = open(inputfile,'r', encoding="utf-8")
        flag = 0
        index = 0
        for line in file_dat:
            index = index + 1
            # checking end of attributes
            if '[END] of [Attributes]' in line:
                flag = 1
                break
        if flag == 0:
            print('PROBLEM WITH FILE .dat: Metadata not found')
            end_meta = None
        else:
            end_meta = index
        file_dat.close()
        metadata = pd.read_csv(inputfile, skiprows=1, nrows=end_meta-3, header=None, sep='=')
        meta = metadata[metadata[0].str.contains('Version|Date|PositionLatitude|PositionLongitude|IntegrationTime')][1]
        data = pd.read_csv(inputfile, skiprows=end_meta+2, nrows=255, header=None, sep=r'\s+')[1]
        meta = meta.to_numpy(dtype=str)
        data = data.to_numpy(dtype=str)
        date1 = datetime.strptime(meta[1], " %Y-%m-%d %H:%M:%S")
        time = meta[1].split(' ')[2]
        meta[0] = date1
        meta[1] = time
        return meta,data

    @staticmethod
    def read_mlb(filename):
        """
        Read TriOS .mlb file and return metadata (e.g. temperature, tilt, integration time),
            spectrum data, and timestamps (from IDData)

        Note: this was tested with G1 files recorded with MSDA_XE and G2 files recorded with [pyTrios](https://github.com/StefanSimis/PyTrios)
        """
        # Skip Header and Get Column Names
        with open(filename, 'r', encoding="utf-8") as f:
            start_index, column_names = 0, ''
            for l in f:
                if l == '\n' or l.startswith('%'):
                    start_index += 1
                    column_names = l
                    continue
                else:
                    break
            else:
                raise ValueError("No header found in .mlb file")
        column_names = re.split('\s+%', column_names[1:].strip())
        # Read Data
        data = pd.read_csv(filename, skiprows=start_index + 1, names=column_names, sep=r'\s+')
        # Format IDData to UTC datetime
        # dt = pd.to_datetime(data.IDData.str[6:], format='%Y-%m-%d_%H-%M-%S_%f', utc=True)
        if 'DateTime' not in data.columns:
            dt = pd.to_datetime(data.IDData.str[6:], format='%Y-%m-%d_%H-%M-%S_%f', utc=True)
            # Convert from seconds since 1970-01-01 to days since 1900-01-01
            dt = ((datetime(1970, 1, 1) - datetime(1900, 1, 1)).total_seconds() + dt.to_numpy(dtype=float)/10**9) / 86400
            # Add two days to match legacy format
            dt += 2
            # Insert Column at position 0
            data.insert(0, 'DateTime', dt)
            column_names = ['DateTime'] + column_names
        # Extract Spectrum Columns (c001 - c255)
        spec_cols = [idx for idx, h in enumerate(column_names) if h.startswith('c')]
        specs = data.iloc[:, spec_cols]
        # For G1 metadata: Datetime PositionLatitude PositionLongitude IntegrationTime
        # For G2 additional information is included such as pre- and post-measurement tilt and internal temperature
        meta = data.iloc[:, 0:spec_cols[0]]
        time = data.IDData
        return meta, specs, time

    # Function for reading cal files
    @staticmethod
    def read_cal(inputfile):
        file_dat = open(inputfile,'r', encoding="utf-8")
        flag_meta = 0
        flag_data = 0
        index = 0
        for line in file_dat:
            index = index + 1
            # checking end of attributes
            if '[END] of [Attributes]' in line:
                flag_meta = index
            if '[DATA]' in line:
                flag_data = index
                break

        if flag_meta == 0:
            print('PROBLEM WITH CAL FILE: Metadata not found')
            # exit()
            return None, None
        if flag_data == 0:
            print('PROBLEM WITH CAL FILE: data not found')
            # exit()
            return None, None

        file_dat.close()

        metadata = pd.read_csv(inputfile, skiprows=1, nrows=flag_meta-3, header=None, sep='=')
        metadata = metadata[~metadata[0].str.contains(r'\[')]
        metadata = metadata.reset_index(drop=True)
        data = pd.read_csv(inputfile, skiprows=flag_data+1, nrows=255, header=None, sep=r'\s+')

        # NAN filtering, set to zero
        for col in data:
            indnan = data[col].astype(str).str.contains('nan', case=False)
            data.loc[indnan, col] = '0.0'

        return metadata,data

    # Generic function for adding metadata from the ini file
    @staticmethod
    def get_attr(metadata, gp):
        for irow,_ in enumerate(metadata.iterrows()):
            gp.attributes[metadata[0][irow].strip()]=str(metadata[1][irow].strip())
        return None

    # Function for reading and getting metadata for config .ini files
    @staticmethod
    def attr_ini(ini_file, gp):
        ini = pd.read_csv(ini_file, skiprows=1, header=None, sep='=')
        ini = ini[~ini[0].str.contains(r'\[')]
        ini = ini.reset_index(drop=True)
        ProcessL1aTriOS.get_attr(ini,gp)
        return None


    # Function for data formatting
    @staticmethod
    def formatting_instrument(name, cal_path, input_file, root, configPath):
        print('Formatting ' + str(name) + ' Data')
        # Extract measurement type from config file
        with open(configPath, 'r', encoding="utf-8") as fc:
            text = fc.read()
            conf_json = json.loads(text)
        sensor = conf_json['CalibrationFiles']['SAM_'+name+'.ini']['frameType']
        print(sensor)

        if 'LT' not in sensor and 'LI' not in sensor and 'ES' not in sensor:
            print('Error in config file. Check frame type for calibration files')
            # exit()
            return None,None

        # A = f.create_group('SAM_'+name+'.dat')
        gp =  HDFGroup()
        gp.id = 'SAM_'+name+'.ini'
        root.groups.append(gp)

        # Configuration file
        ProcessL1aTriOS.attr_ini(cal_path + 'SAM_'+name+'.ini',gp)

        # Formatting data
        meta, data, time = ProcessL1aTriOS.read_mlb(input_file)

        # meta contains Datetime, PositionLat, PositionLon, and IntegrationTime
        if meta is None:
            logging.writeLogFileAndPrint("Error reading mlb file")
            return None,None

        ## if date is the first field "%yyy-mm-dd"
        #   This derives date/time from IDData, not Datetime column of .mlb file
        if len(time[0].rsplit('_')[0]) == 11:
            dates = [i.rsplit('_')[0][1:] for i in time]
            datetag = [float(i.rsplit('-')[0] + str(date(int(i.rsplit('-')[0]), int(i.rsplit('-')[1]), int(i.rsplit('-')[2])).timetuple().tm_yday)) for i in dates]
            timetag = [float(i.rsplit('_')[1].replace('-','') + '000') for i in time]
        ## if not it is in second place
        else:
            dates = [i.rsplit('_')[1] for i in time]
            datetag = [float(i.rsplit('-')[0] + str(date(int(i.rsplit('-')[0]), int(i.rsplit('-')[1]), int(i.rsplit('-')[2])).timetuple().tm_yday)) for i in dates]
            timetag = [float(i.rsplit('_')[2].replace('-','') + '000') for i in time]

        # Reshape data and create HDF5 datasets
        gp.attributes['CalFileName'] = 'SAM_' + name + '.ini'
        n = len(meta)
        cfg = [
            # ('DATETAG', meta['DateTime'], 'NONE'),
            # ('DATETAG2', datetag, 'NONE'),
            ('DATETAG', datetag, 'NONE'),
            ('INTTIME', meta['IntegrationTime'], sensor),
            ('CHECK', np.zeros(n), 'NONE'),
            ('DARK_AVE', meta['DarkAvg'] if 'DarkAvg' in meta.columns else np.zeros(n), sensor),
            ('DARK_SAMP', np.zeros(n), sensor),
            ('FRAME', np.zeros(n), 'COUNTER'),
            ('POSFRAME', np.zeros(n), 'COUNT'),
            ('SAMPLE', np.zeros(n), 'DELAY'),
            ('SPECTEMP', meta['Temperature'] if 'Temperature' in meta.columns else np.zeros(n), 'NONE'),
            ('THERMAL_RESP', np.zeros(n), 'NONE'),
            ('TIMER', np.zeros(n), 'NONE'),
            ('TIMETAG2', timetag, 'NONE'),
            ('LATITUDE', meta['PositionLatitude'] if 'PositionLatitude' in meta.columns else np.zeros(n), 'NONE'),
            ('LONGITUDE', meta['PositionLongitude'] if 'PositionLongitude' in meta.columns else np.zeros(n), 'NONE')
        ]
        if 'PreTilt' in meta.columns:
            cfg.append(('TILT_PRE', meta['PreTilt'], 'NONE'))
        if 'PostTilt' in meta.columns:
            cfg.append(('TILT_POST', meta['PostTilt'], 'NONE'))
        for k, v, t in cfg:
            # Reshape Data
            rec = ProcessL1aTriOS.reshape_data(t, n, data=v)
            # HDF5 Dataset Creation
            gp.addDataset(k)
            gp.datasets[k].data = np.array(rec, dtype=[('NONE', '<f8')])

        # Computing wavelengths
        c0 = float(gp.attributes['c0s'])
        c1 = float(gp.attributes['c1s'])
        c2 = float(gp.attributes['c2s'])
        c3 = float(gp.attributes['c3s'])
        wl = []

        # NOTE: Hardcoded assumption of 256 pixels in .mlb file
        for i in range(1,256):
        # for i in range(1,data.shape[1]+1):
            wl.append(str(round((c0 + c1*(i+1) + c2*(i+1)**2 + c3*(i+1)**3), 2)))

        #Create Data (LI,LT,ES) dataset
        ds_dt = np.dtype({'names': wl,'formats': [np.float64]*len(wl)})
        my_arr = np.array(data).transpose() # 255 x N array of pixel data
        try:
            rec_arr = np.rec.fromarrays(my_arr, dtype=ds_dt)
        except ValueError as err:
            if len(err.args) > 0 and err.args[0].startswith("mismatch between the number of fields "):
                rec_arr = np.rec.fromarrays(my_arr[1:], dtype=ds_dt)
            else:
                raise

        gp.addDataset(sensor)
        gp.datasets[sensor].data=np.array(rec_arr, dtype=ds_dt)

        # Calibrations files
        metacal,cal = ProcessL1aTriOS.read_cal(cal_path + 'Cal_SAM_'+name+'.dat')
        if metacal is None:
            logging.writeLogFileAndPrint("Error reading calibration file")
            return None,None
        B1 = gp.addDataset('CAL_'+sensor)
        B1.columns["0"] = cal.values[:,1].astype(np.float64)
        B1.columnsToDataset()

        ProcessL1aTriOS.get_attr(metacal,B1)
        metaback,back = ProcessL1aTriOS.read_cal(cal_path + 'Back_SAM_'+name+'.dat')
        if metacal is None:
            logging.writeLogFileAndPrint("Error reading calibration file")
            return None,None
        # C1 = gp.addDataset('BACK_'+sensor,data=back[[1,2]].astype(np.float64))
        C1 = gp.addDataset('BACK_'+sensor)
        C1.columns["0"] = back.values[:,1]
        C1.columns["1"] = back.values[:,2]
        C1.columnsToDataset()
        ProcessL1aTriOS.get_attr(metaback,C1)

        start_time = datetime.strftime(datetime(1900,1,1) + timedelta(days=meta['DateTime'].iloc[0]-2), "%Y%m%dT%H%M%SZ")
        stop_time = datetime.strftime(datetime(1900,1,1) + timedelta(days=meta['DateTime'].iloc[-1]-2), "%Y%m%dT%H%M%SZ")

        return start_time,stop_time

    # TriOS L0 exports are in reverse chronological order. Reorder all data fields
    @staticmethod
    def fixChronology(node):
        print('Sorting all datasets chronologically')
        for gp in node.groups:
            dateTime = []
            dateTagArray = gp.datasets['DATETAG'].data
            timeTagArray = gp.datasets['TIMETAG2'].data
            for i, dateTag in enumerate(dateTagArray):
                dt1 = dating.dateTagToDateTime(dateTag[0])
                dateTime.append(dating.timeTag2ToDateTime(dt1,timeTagArray[i][0]))

            for ds in gp.datasets:

                # BACK_ and CAL_ are nLambda x 2 and nLambda x 1, respectively, not timestamped to DATETAG, TIMETAG2
                if (not ds.startswith('BACK_')) and (not ds.startswith('CAL_')):
                    gp.datasets[ds].datasetToColumns()
                    try:
                        gp.datasets[ds].data = np.array([x for _, x in sorted(zip(dateTime,gp.datasets[ds].data))])
                    except:
                        print('fail')

        return node
