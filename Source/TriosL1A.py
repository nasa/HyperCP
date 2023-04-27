
import datetime as dt
import os
import numpy as np
import pandas as pd
import h5py
import json
from datetime import datetime, timedelta, date
import re
import tables

from Source.MainConfig import MainConfig
from Source.ConfigFile import ConfigFile


class TriosL1A:

    # use namesList to define dtype for recarray
    def reshape_data(NAME,N,data):
        ds_dt = np.dtype({'names':[NAME],'formats':[(float)] })
        tst = np.array(data).reshape((1,N))
        rec_arr2 = np.rec.fromarrays(tst, dtype=ds_dt)
        return rec_arr2

    def reshape_data_str(NAME,N,data):
        dt = h5py.special_dtype(vlen=str)
        ds_dt = np.dtype({'names':[NAME],'formats':[dt] })
        tst = np.array(data).reshape((1,N))
        rec_arr2 = np.rec.fromarrays(tst, dtype=ds_dt)
        return rec_arr2

    # Function for reading and formatting .dat data file
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
        else:
            end_meta = index
        file_dat.close()
        metadata = pd.read_csv(inputfile, skiprows=1, nrows=end_meta-3, header=None, sep='=')
        meta = metadata[metadata[0].str.contains('Version|Date|PositionLatitude|PositionLongitude|IntegrationTime')][1]
        data = pd.read_csv(inputfile, skiprows=end_meta+2, nrows=255, header=None, sep=r'\s+')[1]
        meta = meta.to_numpy(dtype=str)
        data = data.to_numpy(dtype=str)
        date = dt.datetime.strptime(meta[1], " %Y-%m-%d %H:%M:%S")
        time = meta[1].split(' ')[2]
        meta[0] = date
        meta[1] = time
        return meta,data

    # Function for reading and formatting .mlb data file
    def read_mlb(inputfile):
        file_dat = open(inputfile,'r')
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
            exit()
        else:
            end_meta = index
        file_dat.close()
        data_temp = pd.read_csv(inputfile, skiprows=end_meta+1, header=None, sep=r'\s+')
        meta = pd.concat([data_temp[0],data_temp[1],data_temp[2],data_temp[3]], axis=1, ignore_index=True)
        data_temp = data_temp.drop(columns=[0,1,2,3])
        time = data_temp.iloc[:,-1]
        data = data_temp.iloc[:,:-2]
        return meta,data,time

    # Function for reading cal files
    def read_cal(inputfile):
        file_dat = open(inputfile,'r')
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
            exit()
        if flag_data == 0:
            print('PROBLEM WITH CAL FILE: data not found')
            exit()

        file_dat.close()

        metadata = pd.read_csv(inputfile, skiprows=1, nrows=flag_meta-3, header=None, sep='=')
        metadata = metadata[~metadata[0].str.contains(r'\[')]
        metadata = metadata.reset_index(drop=True)
        data = pd.read_csv(inputfile, skiprows=flag_data+1, nrows=255, header=None, sep=r'\s+')

        return metadata,data

    # Generic function for getting metadata
    def get_attr(metadata, level):
        for irow,_ in enumerate(metadata.iterrows()):
            level.attrs[metadata[0][irow].strip()]=str(metadata[1][irow].strip()).encode('ascii')
        return None

    # Function for reading and getting metadata for config .ini files
    def attr_ini(ini_file, level):
        ini = pd.read_csv(ini_file, skiprows=1, header=None, sep='=')
        ini = ini[~ini[0].str.contains(r'\[')]
        ini = ini.reset_index(drop=True)
        TriosL1A.get_attr(ini,level)
        return None


    # Function for data formatting
    def formatting_instrument(name,cal_path,input_file,f,configPath):
        print('Formatting ' +name+ ' Data')
        # Extract measurement type from config file
        with open(configPath, 'r') as fc:
            text = fc.read()
            conf_json = json.loads(text)
        mesure = conf_json['CalibrationFiles']['SAM_'+name+'.ini']['frameType']
        print(mesure)

        if 'LT' not in mesure and 'LI' not in mesure and 'ES' not in mesure:
            print('Error in config file. Check frame type for calibration files')
            exit()
        else:
            None

        A = f.create_group('SAM_'+name+'.dat')

        # Configuration file
        TriosL1A.attr_ini(cal_path + 'SAM_'+name+'.ini',A)

        # Formatting data
        data = pd.DataFrame()
        meta = pd.DataFrame()
        meta,data,time = TriosL1A.read_mlb(input_file)

        ## if date is the first field "%yyy-mm-dd"
        if len(time[0].rsplit('_')[0]) == 11:
            dates = [i.rsplit('_')[0][1:] for i in time]
            datetag = [float(i.rsplit('-')[0] + str(date(int(i.rsplit('-')[0]), int(i.rsplit('-')[1]), int(i.rsplit('-')[2])).timetuple().tm_yday)) for i in dates]
            timetag = [float(i.rsplit('_')[1].replace('-','') + '000') for i in time]
        ## if not it is in second place
        else:
            dates = [i.rsplit('_')[1] for i in time]
            datetag = [float(i.rsplit('-')[0] + str(date(int(i.rsplit('-')[0]), int(i.rsplit('-')[1]), int(i.rsplit('-')[2])).timetuple().tm_yday)) for i in dates]
            timetag = [float(i.rsplit('_')[2].replace('-','') + '000') for i in time]

        # Reshape data
        rec_datetag  = TriosL1A.reshape_data('NONE',len(meta[0]),data=meta[0])
        rec_datetag2  = TriosL1A.reshape_data('NONE',len(meta[0]),data=datetag)
        rec_inttime  = TriosL1A.reshape_data(mesure,len(meta[3]),data=meta[3])
        rec_check  = TriosL1A.reshape_data('SUM',len(meta[0]),data=np.zeros(len(meta)))
        rec_darkave  = TriosL1A.reshape_data(mesure,len(meta[0]),data=np.zeros(len(meta)))
        rec_darksamp  = TriosL1A.reshape_data(mesure,len(meta[0]),data=np.zeros(len(meta)))
        rec_frame  = TriosL1A.reshape_data('COUNTER',len(meta[0]),data=np.zeros(len(meta)))
        rec_posframe  = TriosL1A.reshape_data('COUNT',len(meta[0]),data=np.zeros(len(meta)))
        rec_sample  = TriosL1A.reshape_data('DELAY',len(meta[0]),data=np.zeros(len(meta)))
        rec_spectemp  = TriosL1A.reshape_data('NONE',len(meta[0]),data=np.zeros(len(meta)))
        rec_thermalresp  = TriosL1A.reshape_data('NONE',len(meta[0]),data=np.zeros(len(meta)))
        rec_time  = TriosL1A.reshape_data('NONE',len(meta[0]),data=np.zeros(len(meta)))
        rec_timetag2  = TriosL1A.reshape_data('NONE',len(meta[0]),data=timetag)

        # HDF5 Dataset creation
        dataset_name = 'SAM_'+name+'.dat'
        f.create_dataset(dataset_name+'/DATETAG',data=rec_datetag2)
        f.create_dataset(dataset_name+'/INTTIME',data=rec_inttime)
        f.create_dataset(dataset_name+'/CHECK',data=rec_check)
        f.create_dataset(dataset_name+'/DARK_AVE',data=rec_darkave)
        f.create_dataset(dataset_name+'/DARK_SAMP',data=rec_darksamp)
        f.create_dataset(dataset_name+'/FRAME',data=rec_frame)
        f.create_dataset(dataset_name+'/POSFRAME',data=rec_posframe)
        f.create_dataset(dataset_name+'/SAMPLE',data=rec_sample)
        f.create_dataset(dataset_name+'/SPECTEMP',data=rec_spectemp)
        f.create_dataset(dataset_name+'/THERMAL_RESP',data=rec_thermalresp)
        f.create_dataset(dataset_name+'/TIMER',data=rec_time)
        f.create_dataset(dataset_name+'/TIMETAG2',data=rec_timetag2)

        # Computing wavelengths
        c0 = float(f[dataset_name].attrs['c0s'])
        c1 = float(f[dataset_name].attrs['c1s'])
        c2 = float(f[dataset_name].attrs['c2s'])
        c3 = float(f[dataset_name].attrs['c3s'])
        wl = []
        for i in range(1,256):
            wl.append(str(round((c0 + c1*(i+1) + c2*(i+1)**2 + c3*(i+1)**3), 2)))

        #Create Data (LI,LT,ES) dataset
        ds_dt = np.dtype({'names': wl,'formats': [np.float64]*len(wl)})
        my_arr = np.array(data).transpose()
        rec_arr = np.rec.fromarrays(my_arr, dtype=ds_dt)
        f.create_dataset(dataset_name+'/'+mesure,data=rec_arr)

        # Calibrations files
        metacal,cal = TriosL1A.read_cal(cal_path + 'Cal_SAM_'+name+'.dat')
        B1 = f.create_dataset(dataset_name+'/CAL_'+mesure,data=cal[1].astype(np.float64))
        TriosL1A.get_attr(metacal,B1)
        metaback,back = TriosL1A.read_cal(cal_path + 'Back_SAM_'+name+'.dat')
        C1 = f.create_dataset(dataset_name+'/BACK_'+mesure,data=back[[1,2]].astype(np.float64))
        TriosL1A.get_attr(metaback,C1)

        start_time = dt.datetime.strftime(dt.datetime(1900,1,1) + timedelta(days=rec_datetag[0][0]-2), "%Y%m%dT%H%M%SZ")
        stop_time = dt.datetime.strftime(dt.datetime(1900,1,1) + timedelta(days=rec_datetag[-1][0]-2), "%Y%m%dT%H%M%SZ")

        return start_time,stop_time


    def triosL1A(fp, outFilePath): #, configPath, ancillaryData):

        configPath = MainConfig.settings['cfgPath']
        cal_path = configPath.split('.')[0] + '_Calibration/'

        if '.mlb' in fp[0]:   # Multi frame
            acq_time = []
            for file in fp:

                ## Test filename for different date formating
                match1 = re.search(r'\d{8}_\d{6}', file.split('/')[-1])
                match2 = re.search(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', file.split('/')[-1])
                if match1 is not None:
                    a_time = match1.group()
                elif match2 is not None:
                    a_time = match2.group()
                else:
                    print("  ERROR: no identifier recognized in TRIOS L0 file name" )
                    print("  L0 filename should have a date to identify triplet instrument")
                    print("  either 'yyymmdd_hhmmss' or 'yyy-mm-dd_hh-mm-ss' ")
                    exit()

                acq_time.append(a_time)

            acq_time = list(dict.fromkeys(acq_time)) # Returns unique timestamps
            for a_time in acq_time:
                print("")
                print("Generate the telemetric file...")
                print('Processing: ' +a_time)

                hdfout = a_time + '_.hdf'

                tables.file._open_files.close_all()
                f = h5py.File(outFilePath+hdfout, 'w')
                f.attrs["WAVELENGTH_UNITS"] = "nm".encode('ascii')
                f.attrs["LI_UNITS"] = "count".encode('ascii')
                f.attrs["LT_UNITS"] = "count".encode('ascii')
                f.attrs["ES_UNITS"] = "count".encode('ascii')
                f.attrs["SATPYR_UNITS"] = "count".encode('ascii')
                f.attrs["PROCESSING_LEVEL"] = "1a".encode('ascii')

                ffp = [s for s in fp if a_time in s]
                f.attrs["RAW_FILE_NAME"] = str(ffp).encode('ascii')
                for file in ffp:
                    # name = file.split('/')[-1].split('.')[-2].split('_')[2]
                    if "SAM_" in file:
                        name = file[file.index('SAM_')+4:file.index('SAM_')+8]
                    else:
                        print("ERROR : naming convention os not respected")

                    start,stop = TriosL1A.formatting_instrument(name,cal_path,file,f,configPath)

                f.close()

                new_name = outFilePath + '/' + 'Trios_' + str(start) + '_' + str(stop) + '_L1A.hdf'
                if os.path.isfile(new_name):
                    os.replace(outFilePath+hdfout, new_name)
                else:
                    os.rename(outFilePath+hdfout, new_name)
        else:
            print('Single Frame deprecated')

        return None
