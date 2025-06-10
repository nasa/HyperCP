'''Process Raw (L0) data to L1A HDF5'''
import os
import json
from datetime import timedelta, date
import re
import datetime as dt
import numpy as np
import pandas as pd
import tables

from Source.MainConfig import MainConfig
from Source.HDFRoot import HDFRoot
from Source.HDFGroup import HDFGroup
from Source.Utilities import Utilities


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
                def parse_filename(data):
                    dates = []
                    for pattern in [
                        r'\d{8}.\d{6}', 
                        r'\d{4}.\d{2}.\d{2}.\d{2}.\d{2}.\d{2}',
                        r'\d{8}.\d{2}.\d{2}.\d{2}',
                        r'\d{4}.\d{2}.\d{2}.\d{6}',
                        r'\d{4}S', 
                        r'\d{4}D',
                    ]:
                        match = re.search(pattern, data)
                        if match is not None:
                            dates.append(match.group(0))

                    if len(dates) == 0:
                        raise IndexError

                    return dates[0]

                try:
                    a_name = parse_filename(file.split('/')[-1])
                except IndexError:
                    print("  ERROR: no identifier recognized in TRIOS L0 file name" )
                    print("  L0 filename should have a cast to identify triplet instrument")
                    print("  ending in 4 digits before S.mlb (light) or D.mlb for caps-on dark. ")
                    return None,None

                # match1 = re.search(r'\d{8}_\d{6}', file.split('/')[-1])
                # match2 = re.search(r'\d{4}S', file.split('/')[-1])
                # match3 = re.search(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', file.split('/')[-1])
                acq_name.append(a_name)

            # acq_time = list(dict.fromkeys(acq_time)) # Returns unique timestamps
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
                    print(f'Caps-on dark file recognized {a_name}.')
                    cod = True
                    root.attributes["FRAME_TYPE"] = 'caps-on dark'
                    if os.path.isdir(outFilePathDark) is False:
                        os.mkdir(outFilePathDark)
                else:
                    cod = False
                    root.attributes["FRAME_TYPE"] = 'light'
                for file in ffp:
                    if "SAM_" in file:
                        name = file[file.index('SAM_')+4:file.index('SAM_')+8]
                    else:
                        print("ERROR : naming convention os not respected")
                        name = None

                    start,stop = ProcessL1aTriOS.formatting_instrument(name,cal_path,file,root,configPath)

                    if start is None:
                        return None, None
                    acq_datetime = dt.datetime.strptime(start,"%Y%m%dT%H%M%SZ")
                    root.attributes["TIME-STAMP"] = dt.datetime.strftime(acq_datetime,'%a %b %d %H:%M:%S %Y')
                    # Update to something like "YYYY-MM-DDTHH:MM:SS UTC"
                    root.attributes["TIME_COVERAGE_START"] = dt.datetime.strftime(acq_datetime,'%a %b %d %H:%M:%S %Y')
                    acq_datetime = dt.datetime.strptime(stop,"%Y%m%dT%H%M%SZ")
                    root.attributes["TIME_COVERAGE_END"] = dt.datetime.strftime(acq_datetime,'%a %b %d %H:%M:%S %Y')


                # File naming convention on TriOS TBD depending on convention used in MSDA_XE
                #The D-6 requirements to add the timestamp manually on every acquisition is impractical.
                #Convert to using any unique name and append timestamp from data (start)
                try:
                    new_name = a_name #acq_name[0]
                    # new_name = file.split('/')[-1].split('.mlb')[0].split(f'SAM_{name}_RAW_SPECTRUM_')[1]
                    # NOTE: For caps-on darks, we require a 4-digit station number plus 'S' or 'D' for light or dark, respectively
                    if re.search(r'\d{4}[DS]', file.split('/')[-1]) is not None:
                        new_name = str(start)+'_'+new_name
                except IndexError as err:
                    print(err)
                    msg = "possibly an error in naming of Raw files"
                    Utilities.writeLogFile(msg)
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
                    for gpDark in root.groups:
                        if gpDark.id.startswith('SAM'):
                            # NOTE: Placeholder to calculate T and dT from DN.
                            # T = -Tc + S * ln(DN-DNc)
                            # RAMSES class coefficients
                            # Tc = -16.4
                            # S = 6.147
                            # DNc = 1438
                            print(f'Running caps-on dark algorithm to estimate internal temp:{gpDark.id}')
                            # Add dataset INTERNALTEMP for T and sigmaT columns. SPECTEMP reserved for internal thermistor temp (G2 and others)
                            T = gpDark.addDataset('INTERNALTEMP')
                            # Dummy values
                            T.appendColumn('T',float(31))                      # Placeholder for average internal T from DN
                            T.appendColumn('sigmaT',float(3))                      # Placeholder for standard devation of DN
                            # NOTE: Not clear how long of a record to average, or how to (whether to) average the DNs across all bands.
                            T.columnsToDataset()
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
                                        T = gp.addDataset('INTERNALTEMP')
                                        T.copy(gpDark.datasets['INTERNALTEMP'])
                                        T.datasetToColumns()

                try:
                    # root.writeHDF5(new_name)
                    root.writeHDF5(outFFP[-1])

                except Exception:
                    msg = 'Unable to write L1A file. It may be open in another program.'
                    Utilities.errorWindow("File Error", msg)
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return None, None

                Utilities.checkOutputFiles(outFFP[-1])

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
        file_dat = open(inputfile,'r')
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
        date1 = dt.datetime.strptime(meta[1], " %Y-%m-%d %H:%M:%S")
        time = meta[1].split(' ')[2]
        meta[0] = date1
        meta[1] = time
        return meta,data

    # Function for reading and formatting .mlb data file
    @staticmethod
    def read_mlb(inputfile):
        file_dat = open(inputfile,'r', encoding="utf-8")
        flag = 0
        index = 0
        for line in file_dat:
            index = index + 1
            # checking end of attributes
            if 'DateTime' in line:
                flag = 1
                break
        if flag == 0:
            print('PROBLEM WITH FILE .mlb: Metadata not found')
            return None, None, None
        else:
            end_meta = index
        file_dat.close()

        # NOTE: This may differ from G1 to G2. G2 should have some column for internal thermistor
        # Datetime PositionLatitude PositionLongitude IntegrationTime c001-c255 Comment(filename-like) IDData(unknown)
        #   Sample dataset has an extra line after the headers with NaNs for metadata, 1-255, and no Comment or IDData
        skip = 1 # 1 skips the headers plus the dummy line with NaN Datetime before data begins
        data_temp = pd.read_csv(inputfile, skiprows=end_meta+skip, header=None, sep=r'\s+')
        # Datetime PositionLatitude PositionLongitude IntegrationTime
        meta = pd.concat([data_temp[0],data_temp[1],data_temp[2],data_temp[3]], axis=1, ignore_index=True)
        data_temp = data_temp.drop(columns=[0,1,2,3])
        time = data_temp.iloc[:,-1] # <---- This is from IDData?? Why not from Datetime?
        # c001 - c255        
        data = data_temp.iloc[:,:-2]
        return meta,data,time

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
        print('Formatting ' +name+ ' Data')
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
        data = pd.DataFrame()
        meta = pd.DataFrame()
        meta,data,time = ProcessL1aTriOS.read_mlb(input_file)

        # meta contains Datetime, PositionLat, PositionLon, and IntegrationTime
        if meta is None:
            msg = "Error reading mlb file"
            print(msg)
            Utilities.writeLogFile(msg)
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

        # NOTE: Placeholder for extracting thermistor temp from G2 RAMSES:
        # if G2: ... should have a group attribute for generation RAMSES

        # Reshape data
        rec_datetag  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=meta[0]) # <- From Datetime
        rec_datetag2  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=datetag) # <- From Comments
        rec_timetag2  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=timetag) # <- From Comments
        rec_latitude  = ProcessL1aTriOS.reshape_data(sensor,len(meta[1]),data=meta[1])
        rec_longitude  = ProcessL1aTriOS.reshape_data(sensor,len(meta[2]),data=meta[2])
        rec_inttime  = ProcessL1aTriOS.reshape_data(sensor,len(meta[3]),data=meta[3])

        # Placeholders, zero-buffered
        rec_check  = ProcessL1aTriOS.reshape_data('SUM',len(meta[0]),data=np.zeros(len(meta)))
        rec_darkave  = ProcessL1aTriOS.reshape_data(sensor,len(meta[0]),data=np.zeros(len(meta)))
        rec_darksamp  = ProcessL1aTriOS.reshape_data(sensor,len(meta[0]),data=np.zeros(len(meta)))
        rec_frame  = ProcessL1aTriOS.reshape_data('COUNTER',len(meta[0]),data=np.zeros(len(meta)))
        rec_posframe  = ProcessL1aTriOS.reshape_data('COUNT',len(meta[0]),data=np.zeros(len(meta)))
        rec_sample  = ProcessL1aTriOS.reshape_data('DELAY',len(meta[0]),data=np.zeros(len(meta)))
        # NOTE: Placeholder for translating thermistor temp from G2 RAMSES:
        # if G2: ... else
        rec_spectemp  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=np.zeros(len(meta)))        
        rec_thermalresp  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=np.zeros(len(meta)))
        rec_time  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=np.zeros(len(meta)))

        # HDF5 Dataset creation
        gp.attributes['CalFileName'] = 'SAM_'+name+'.ini'
        gp.addDataset('DATETAG')
        gp.datasets['DATETAG'].data=np.array(rec_datetag2, dtype=[('NONE', '<f8')])# <- From Comments
        gp.addDataset('INTTIME')
        gp.datasets['INTTIME'].data=np.array(rec_inttime, dtype=[('NONE', '<f8')])
        gp.addDataset('CHECK')
        gp.datasets['CHECK'].data=np.array(rec_check, dtype=[('NONE', '<f8')])
        gp.addDataset('DARK_AVE')
        gp.datasets['DARK_AVE'].data=np.array(rec_darkave, dtype=[('NONE', '<f8')])
        gp.addDataset('DARK_SAMP')
        gp.datasets['DARK_SAMP'].data=np.array(rec_darksamp, dtype=[('NONE', '<f8')])
        gp.addDataset('FRAME')
        gp.datasets['FRAME'].data=np.array(rec_frame, dtype=[('NONE', '<f8')])
        gp.addDataset('POSFRAME')
        gp.datasets['POSFRAME'].data=np.array(rec_posframe, dtype=[('NONE', '<f8')])
        gp.addDataset('SAMPLE')
        gp.datasets['SAMPLE'].data=np.array(rec_sample, dtype=[('NONE', '<f8')])
        gp.addDataset('SPECTEMP')
        gp.datasets['SPECTEMP'].data=np.array(rec_spectemp, dtype=[('NONE', '<f8')])
        gp.addDataset('THERMAL_RESP')
        gp.datasets['THERMAL_RESP'].data=np.array(rec_thermalresp, dtype=[('NONE', '<f8')])
        gp.addDataset('TIMER')
        gp.datasets['TIMER'].data=np.array(rec_time, dtype=[('NONE', '<f8')])
        gp.addDataset('TIMETAG2')
        gp.datasets['TIMETAG2'].data=np.array(rec_timetag2, dtype=[('NONE', '<f8')])# <- From Comments
        gp.addDataset('LATITUDE')
        gp.datasets['LATITUDE'].data=np.array(rec_latitude, dtype=[('NONE', '<f8')])
        gp.addDataset('LONGITUDE')
        gp.datasets['LONGITUDE'].data=np.array(rec_longitude, dtype=[('NONE', '<f8')])

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
            msg = "Error reading calibration file"
            print(msg)
            Utilities.writeLogFile(msg)
            return None,None
        B1 = gp.addDataset('CAL_'+sensor)
        B1.columns["0"] = cal.values[:,1].astype(np.float64)
        B1.columnsToDataset()

        ProcessL1aTriOS.get_attr(metacal,B1)
        metaback,back = ProcessL1aTriOS.read_cal(cal_path + 'Back_SAM_'+name+'.dat')
        if metacal is None:
            msg = "Error reading calibration file"
            print(msg)
            Utilities.writeLogFile(msg)
            return None,None
        # C1 = gp.addDataset('BACK_'+sensor,data=back[[1,2]].astype(np.float64))
        C1 = gp.addDataset('BACK_'+sensor)
        C1.columns["0"] = back.values[:,1]
        C1.columns["1"] = back.values[:,2]
        C1.columnsToDataset()

        ProcessL1aTriOS.get_attr(metaback,C1)

        # NOTE: Caution! These are not chronological.
        # start_time = dt.datetime.strftime(dt.datetime(1900,1,1) + timedelta(days=rec_datetag[0][0]-2), "%Y%m%dT%H%M%SZ")# <- From Datetime
        # stop_time = dt.datetime.strftime(dt.datetime(1900,1,1) + timedelta(days=rec_datetag[-1][0]-2), "%Y%m%dT%H%M%SZ")# <- From Datetime
        arr_datetag = rec_datetag.tolist()
        start_time = dt.datetime.strftime(dt.datetime(1900,1,1) + timedelta(days=min(arr_datetag)[0]-2), "%Y%m%dT%H%M%SZ")# <- From Datetime
        stop_time = dt.datetime.strftime(dt.datetime(1900,1,1) + timedelta(days=max(arr_datetag)[0]-2), "%Y%m%dT%H%M%SZ")# <- From Datetime

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
                dt1 = Utilities.dateTagToDateTime(dateTag[0])
                dateTime.append(Utilities.timeTag2ToDateTime(dt1,timeTagArray[i][0]))

            for ds in gp.datasets:

                # BACK_ and CAL_ are nLambda x 2 and nLambda x 1, respectively, not timestamped to DATETAG, TIMETAG2
                if (not ds.startswith('BACK_')) and (not ds.startswith('CAL_')):
                    gp.datasets[ds].datasetToColumns()
                    gp.datasets[ds].data = np.array([x for _, x in sorted(zip(dateTime,gp.datasets[ds].data))])

        return node

    
