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

                # ## Test filename for different date formating
                # match1 = re.search(r'\d{8}_\d{6}', file.split('/')[-1])
                # match2 = re.search(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', file.split('/')[-1])
                # if match1 is not None:
                #     a_time = match1.group()
                # elif match2 is not None:
                #     a_time = match2.group()
                # else:
                #     print("  ERROR: no identifier recognized in TRIOS L0 file name" )
                #     print("  L0 filename should have a date to identify triplet instrument")
                #     print("  either 'yyymmdd_hhmmss' or 'yyy-mm-dd_hh-mm-ss' ")
                #     exit()

                # acq_time.append(a_time)


                ## Test filename for station/cast
                match1 = re.search(r'\d{8}_\d{6}', file.split('/')[-1])
                match2 = re.search(r'\d{4}S', file.split('/')[-1])
                match3 = re.search(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', file.split('/')[-1])
                if match1 is not None:
                    a_name = match1.group()
                elif match2 is not None:
                    a_name = match2.group()
                elif match3 is not None:
                    a_name = match3.group()
                else:
                    print("  ERROR: no identifier recognized in TRIOS L0 file name" )
                    print("  L0 filename should have a cast to identify triplet instrument")
                    print("  ending in 4 digits before S.mlb ")
                    return None,None

                # acq_time.append(a_cast)
                acq_name.append(a_name)

            # acq_time = list(dict.fromkeys(acq_time)) # Returns unique timestamps
            acq_name = list(dict.fromkeys(acq_name)) # Returns unique names
            outFFP = []
            # for a_time in acq_time:
            for a_name in acq_name:
                print("")
                print("Generate the telemetric file...")
                # print('Processing: ' +a_time)
                print('Processing: ' +a_name)

                # hdfout = a_time + '_.hdf'

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

                # ffp = [s for s in fp if a_time in s]
                ffp = [s for s in fp if a_name in s]
                root.attributes["RAW_FILE_NAME"] = str(ffp)
                # root.attributes["TIME-STAMP"] = a_name
                root.attributes["CAST"] = a_name
                for file in ffp:
                    if "SAM_" in file:
                        name = file[file.index('SAM_')+4:file.index('SAM_')+8]
                    else:
                        print("ERROR : naming convention os not respected")
                        name = None

                    start,_ = ProcessL1aTriOS.formatting_instrument(name,cal_path,file,root,configPath)

                    if start is None:
                        return None, None
                    acq_datetime = dt.datetime.strptime(start,"%Y%m%dT%H%M%SZ")
                    root.attributes["TIME-STAMP"] = dt.datetime.strftime(acq_datetime,'%a %b %d %H:%M:%S %Y')


                # File naming convention on TriOS TBD depending on convention used in MSDA_XE
                #The D-6 requirements to add the timestamp manually on every acquisition is impractical.
                #Convert to using any unique name and append timestamp from data (start)

                try:
                    new_name = file.split('/')[-1].split('.mlb')[0].split(f'SAM_{name}_RAW_SPECTRUM_')[1]
                    if match2 is not None:
                        new_name = new_name+'_'+str(start)
                except IndexError as err:
                    print(err)
                    msg = "possibly an error in naming of Raw files"
                    Utilities.writeLogFile(msg)
                    new_name = file.split('/')[-1].split('.mlb')[0].split(f'SAM_{name}_Spectrum_RAW_')[1]

                # new_name = outFilePath + '/' + 'Trios_' + str(start) + '_' + str(stop) + '_L1A.hdf'
                # outFFP.append(os.path.join(outFilePath,f'{new_name}_L1A.hdf'))
                outFFP.append(os.path.join(outFilePath,f'{new_name}_L1A.hdf'))
                root.attributes["L1A_FILENAME"] = outFFP[-1]

                root = ProcessL1aTriOS.fixChronology(root)

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
            exit()
        if flag_data == 0:
            print('PROBLEM WITH CAL FILE: data not found')
            exit()

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
        rec_datetag  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=meta[0])
        rec_datetag2  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=datetag)
        rec_inttime  = ProcessL1aTriOS.reshape_data(sensor,len(meta[3]),data=meta[3])
        rec_check  = ProcessL1aTriOS.reshape_data('SUM',len(meta[0]),data=np.zeros(len(meta)))
        rec_darkave  = ProcessL1aTriOS.reshape_data(sensor,len(meta[0]),data=np.zeros(len(meta)))
        rec_darksamp  = ProcessL1aTriOS.reshape_data(sensor,len(meta[0]),data=np.zeros(len(meta)))
        rec_frame  = ProcessL1aTriOS.reshape_data('COUNTER',len(meta[0]),data=np.zeros(len(meta)))
        rec_posframe  = ProcessL1aTriOS.reshape_data('COUNT',len(meta[0]),data=np.zeros(len(meta)))
        rec_sample  = ProcessL1aTriOS.reshape_data('DELAY',len(meta[0]),data=np.zeros(len(meta)))
        rec_spectemp  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=np.zeros(len(meta)))
        rec_thermalresp  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=np.zeros(len(meta)))
        rec_time  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=np.zeros(len(meta)))
        rec_timetag2  = ProcessL1aTriOS.reshape_data('NONE',len(meta[0]),data=timetag)

        # HDF5 Dataset creation
        gp.attributes['CalFileName'] = 'SAM_'+name+'.ini'
        gp.addDataset('DATETAG')
        gp.datasets['DATETAG'].data=np.array(rec_datetag2, dtype=[('NONE', '<f8')])
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
        gp.datasets['TIMETAG2'].data=np.array(rec_timetag2, dtype=[('NONE', '<f8')])

        # Computing wavelengths
        c0 = float(gp.attributes['c0s'])
        c1 = float(gp.attributes['c1s'])
        c2 = float(gp.attributes['c2s'])
        c3 = float(gp.attributes['c3s'])
        wl = []
        for i in range(1,256):
        # for i in range(1,data.shape[1]+1):
            wl.append(str(round((c0 + c1*(i+1) + c2*(i+1)**2 + c3*(i+1)**3), 2)))

        #Create Data (LI,LT,ES) dataset
        ds_dt = np.dtype({'names': wl,'formats': [np.float64]*len(wl)})
        my_arr = np.array(data).transpose()
        rec_arr = np.rec.fromarrays(my_arr, dtype=ds_dt)

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
        B1 = gp.addDataset('CAL_'+sensor)
        B1.columns["0"] = cal.values[:,1].astype(np.float64)
        B1.columnsToDataset()

        ProcessL1aTriOS.get_attr(metacal,B1)
        metaback,back = ProcessL1aTriOS.read_cal(cal_path + 'Back_SAM_'+name+'.dat')
        # C1 = gp.addDataset('BACK_'+sensor,data=back[[1,2]].astype(np.float64))
        C1 = gp.addDataset('BACK_'+sensor)
        C1.columns["0"] = back.values[:,1]
        C1.columns["1"] = back.values[:,2]
        C1.columnsToDataset()

        ProcessL1aTriOS.get_attr(metaback,C1)
        start_time = dt.datetime.strftime(dt.datetime(1900,1,1) + timedelta(days=rec_datetag[0][0]-2), "%Y%m%dT%H%M%SZ")
        stop_time = dt.datetime.strftime(dt.datetime(1900,1,1) + timedelta(days=rec_datetag[-1][0]-2), "%Y%m%dT%H%M%SZ")

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

    
