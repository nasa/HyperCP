import datetime as dt
import os
import numpy as np
import pandas as pd
import h5py
import json
from datetime import datetime, timedelta, date
import re


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


    def ddToDm(dd):
        d = int(dd)
        m = abs(dd - d)*60
        dm = (d*100) + m
        return d, m, dm


    def reformat_coord(x, hemi):
        d, m, pos = TriosL1A.ddToDm(float(x))
        X = ("{} {}' ").format(d, m)+hemi
        return X, pos


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
        rec_latpos = TriosL1A.reshape_data('NONE',len(meta[1]),data=meta[1])
        rec_lonpos  = TriosL1A.reshape_data('NONE',len(meta[2]),data=meta[2])
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


    # Function for data formatting single frame
    def formatting_instrument_single(name,cal_path,input_file,f,configPath):
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
        input_file.sort()
        data = pd.DataFrame()
        meta = pd.DataFrame()
        for file in input_file:
            if name in file:
                row_meta,row_data = TriosL1A.read_dat(file)
                meta = meta.append(pd.DataFrame(row_meta.reshape(1,-1)), ignore_index=True)
                data = data.append(pd.DataFrame(row_data.reshape(1,-1)), ignore_index=True)
            else:
                None

        datetag = meta[0]
        datetag2 = [float(i.split(' ')[0].split('-')[0] + str(date(int(i.split(' ')[0].split('-')[0]), int(i.split(' ')[0].split('-')[1]), int(i.split(' ')[0].split('-')[2])).timetuple().tm_yday)) for i in meta[0]]
        timetag = [float(i.replace(':','') + '000') for i in meta[1]]

        # Reshape data
        rec_datetag2  = TriosL1A.reshape_data('NONE',len(meta[0]),data=datetag2)
        rec_inttime  = TriosL1A.reshape_data(mesure,len(meta[4]),data=meta[4])
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
            wl.append(str(round((c0 + c1*i + c2*(i**2) + c3*(i**3)),2)))
         
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

        start_time = datetime.strftime(dt.datetime.strptime(datetag[0], "%Y-%m-%d %H:%M:%S"), '%Y%m%dT%H%M%SZ')
        stop_time = datetime.strftime(dt.datetime.strptime(datetag[len(datetag)-1], "%Y-%m-%d %H:%M:%S"), '%Y%m%dT%H%M%SZ')

        return start_time,stop_time


    def triosL1A(fp, outFilePath, configPath, ancillaryData):

        cal_path = configPath.split('.')[0]+'_Calibration/'

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
                
            acq_time = list(dict.fromkeys(acq_time))
            for a_time in acq_time:
                print("")
                print("Generate the telemetric file...")
                with open(ancillaryData) as ancData:
                    i=0
                    for line in ancData:
                        i+=1
                        if '/water_depth' in line:
                            geoid = [(line.split('=')[1])][0].strip()
                        elif '/measurement_depth' in line:
                            alt = float(line.split('=')[1])
                        elif '/investigators' in line:
                            investigator = line.split('=')[1].strip()
                        elif '/cruise' in line:
                            cruise = line.split('=')[1].strip()
                        elif '/contact' in line:
                            contact = line.split('=')[1].strip()
                        elif '/end_header' in line:
                            break
                ancData.close()

                df = pd.read_csv(ancillaryData, skiprows=i-3)
                df = df.drop([0,1]).reset_index(drop=True)
                df.columns = df.columns.str.replace('/fields=', '')

                HHMMSS = []
                YYYDOY = []
                LATPOS = []
                LONPOS = []
                TTAG2  = []
                for j in range(len(df)):
                    # Define the time on the right format (HHMMSS.SS)
                    hh = '{:02d}'.format(int(df['hour'][j]))
                    mm = '{:02d}'.format(int(df['minute'][j]))
                    ss = '{:02d}'.format(int(df['second'][j]))
                    hhmmss = hh+mm+ss
                    hhmmss = round(float(hhmmss),2)
                    HHMMSS = np.append(HHMMSS, hhmmss)
                    TTAG2  = np.append(TTAG2, hhmmss*1e3)

                    # Define the date on the right format (YYY + Day of Year)
                    year = int(df['year'][j])
                    month= int(df['month'][j])
                    day  = int(df['day'][j])
                    time = hh+':'+mm+':'+ss
                    if j==0:
                        ts = datetime(year, month, day, int(hh), int(mm), int(ss))
                        timestamp=(ts.strftime('%a')+' '+ts.strftime('%b')+' '+ts.strftime('%d')+
                                    ' '+time+' '+str(year))

                    # Define coordinate on the right format (DDDMM.MM)
                    lonpos = TriosL1A.reformat_coord(df['lon'][j], 'E')[1]
                    latpos = TriosL1A.reformat_coord(df['lat'][j], 'N')[1]

                    day_of_year = str(date(year, month, day).timetuple().tm_yday)
                    YYYDOY = np.append(YYYDOY, int(str(year)+day_of_year))
                    LONPOS = np.append(LONPOS, float(lonpos))
                    LATPOS = np.append(LATPOS, float(latpos))

                print('Processing: ' +a_time)

                hdfout = a_time + '_.hdf'
                f = h5py.File(outFilePath+hdfout, 'w')
                f.attrs["WAVELENGTH_UNITS"] = "nm".encode('ascii')
                f.attrs["LI_UNITS"] = "count".encode('ascii')
                f.attrs["LT_UNITS"] = "count".encode('ascii')
                f.attrs["ES_UNITS"] = "count".encode('ascii')
                f.attrs["SATPYR_UNITS"] = "count".encode('ascii')
                f.attrs["PROCESSING_LEVEL"] = "1a".encode('ascii')
                f.attrs["TIME-STAMP"] = timestamp.encode('ascii')

                gps = f.create_group('GPS')
                gps.attrs['DISTANCE_1'] = "Pressure None 1 1 0".encode('ascii')
                gps.attrs['DISTANCE_2'] = "Surface None 1 1 0".encode('ascii')
                gps.attrs['FrameTag'] = "$GPS".encode('ascii')
                gps.attrs['FrameType'] = "Not Required".encode('ascii')
                gps.attrs['InstrumentType'] = "GPS".encode('ascii')
                gps.attrs['MeasMode'] = "Not Required".encode('ascii')
                gps.attrs['Media'] = "Not Required".encode('ascii')
                gps.attrs['SensorDataList'] = "INTTIME, SAMPLE, THERMAL_RESP, ES, DARK_SAMP, DARK_AVE, SPECTEMP, FRAME, TIMER, CHECK, DATETAG, TIMETAG2, POSFRAME".encode('ascii')

                N_GPS = len(HHMMSS) # GBAI: TO CHECK IF NEED TO BE MODIFY
                rec_geoid  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['NaN'.encode('ascii')]*N_GPS)
                rec_geoidunits  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['M'.encode('ascii')]*N_GPS)
                rec_alt  = TriosL1A.reshape_data('NONE',N_GPS,data=alt * np.ones(N_GPS))
                rec_altunits  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['M'.encode('ascii')]*N_GPS)
                rec_utcpos  = TriosL1A.reshape_data('NONE',N_GPS,data=HHMMSS)
                rec_datetag  = TriosL1A.reshape_data('NONE',N_GPS,data=YYYDOY)
                rec_fixqual  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS))
                rec_horiz  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS))
                rec_lathemi  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['N'.encode('ascii')]*N_GPS)
                rec_lonhemi  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['E'.encode('ascii')]*N_GPS)
                rec_nmea  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS))
                rec_numsat  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS)*10)
                rec_posframe  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS))
                rec_refstat  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['NaN'.encode('ascii')]*N_GPS)
                rec_timelag  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['NaN'.encode('ascii')]*N_GPS)
                rec_timetag  = TriosL1A.reshape_data('NONE',N_GPS,data=TTAG2)
                rec_lon  = TriosL1A.reshape_data('NONE',N_GPS,data=LONPOS)
                rec_lat  = TriosL1A.reshape_data('NONE',N_GPS,data=LATPOS)

                gps.create_dataset('GEOID', data=rec_geoid)
                #gps.create_dataset('GEOID', data=['NaN'.encode('ascii')]*N_GPS)
                #gps.create_dataset('GEOIDUNITS' , data=['M'.encode('ascii')]*N_GPS)
                gps.create_dataset('GEOIDUNITS' , data=rec_geoidunits)
                gps.create_dataset('ALT' , data=rec_alt)
                #gps.create_dataset('ALTUNITS' , data=['M'.encode('ascii')]*N_GPS)
                gps.create_dataset('ALTUNITS' , data=rec_altunits)
                gps.create_dataset('UTCPOS' , data=rec_utcpos)
                gps.create_dataset('DATETAG' , data=rec_datetag)
                gps.create_dataset('FIXQUAL' , data=rec_fixqual)
                gps.create_dataset('HORIZ' , data=rec_horiz)
                #gps.create_dataset('LATHEMI' , data=['N'.encode('ascii')]*N_GPS)
                gps.create_dataset('LATHEMI' , data=rec_lathemi)
                #gps.create_dataset('LONHEMI' , data=['E'.encode('ascii')]*N_GPS)
                gps.create_dataset('LONHEMI' , data=rec_lonhemi)
                gps.create_dataset('NMEA_CHECKSUM' , data=rec_nmea)
                gps.create_dataset('NUMSAT' , data=rec_numsat)
                gps.create_dataset('POSFRAME' , data=rec_posframe)
                #gps.create_dataset('REFSTAT' , data=['NaN'.encode('ascii')]*N_GPS)
                gps.create_dataset('REFSTAT' , data=rec_refstat)
                #gps.create_dataset('TIMELAG' , data=['NaN'.encode('ascii')]*N_GPS)
                gps.create_dataset('TIMELAG' , data=rec_timelag)
                gps.create_dataset('TIMETAG2' , data=rec_timetag)
                gps.create_dataset('LATPOS' , data=rec_lat)
                gps.create_dataset('LONPOS' , data=rec_lon)

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


        else:   # Single frame
            instruments = []
            for file in fp:
                name = file.split('/')[-1].split('.')[-2].split('_')[1]
                instruments.append(name)
            instrument = list(dict.fromkeys(instruments))

            print("Generate the telemetric file...")

            with open(ancillaryData) as ancData:
                i=0
                for line in ancData:
                    i+=1
                    if '/water_depth' in line:
                        geoid = [(line.split('=')[1])][0].strip()
                    elif '/measurement_depth' in line:
                        alt = float(line.split('=')[1])
                    elif '/investigators' in line:
                        investigator = line.split('=')[1].strip()
                    elif '/cruise' in line:
                        cruise = line.split('=')[1].strip()
                    elif '/contact' in line:
                        contact = line.split('=')[1].strip()
                    elif '/end_header' in line:
                        break
            ancData.close()

            df = pd.read_csv(ancillaryData, skiprows=i-3)
            df = df.drop([0,1]).reset_index(drop=True)
            df.columns = df.columns.str.replace('/fields=', '')

            HHMMSS = []
            YYYDOY = []
            LATPOS = []
            LONPOS = []
            TTAG2  = []
            for j in range(len(df)):
                # Define the time on the right format (HHMMSS.SS)
                hh = '{:02d}'.format(int(df['hour'][j]))
                mm = '{:02d}'.format(int(df['minute'][j]))
                ss = '{:02d}'.format(int(df['second'][j]))
                hhmmss = hh+mm+ss
                hhmmss = round(float(hhmmss),2)
                HHMMSS = np.append(HHMMSS, hhmmss)
                TTAG2  = np.append(TTAG2, hhmmss*1e3)

                # Define the date on the right format (YYY + Day of Year)
                year = int(df['year'][j])
                month= int(df['month'][j])
                day  = int(df['day'][j])
                time = hh+':'+mm+':'+ss
                if j==0:
                    ts = datetime(year, month, day, int(hh), int(mm), int(ss))
                    timestamp=(ts.strftime('%a')+' '+ts.strftime('%b')+' '+ts.strftime('%d')+
                                ' '+time+' '+str(year))

                # Define coordinate on the right format (DDDMM.MM)
                lonpos = TriosL1A.reformat_coord(df['lon'][j], 'E')[1]
                latpos = TriosL1A.reformat_coord(df['lat'][j], 'N')[1]

                day_of_year = str(date(year, month, day).timetuple().tm_yday)
                YYYDOY = np.append(YYYDOY, int(str(year)+day_of_year))
                LONPOS = np.append(LONPOS, float(lonpos))
                LATPOS = np.append(LATPOS, float(latpos))

            hdfout = '/TEST_.hdf'
            f = h5py.File(outFilePath+hdfout, 'w')

            f.attrs["WAVELENGTH_UNITS"] = "nm".encode('ascii')
            f.attrs["LI_UNITS"] = "count".encode('ascii')
            f.attrs["LT_UNITS"] = "count".encode('ascii')
            f.attrs["ES_UNITS"] = "count".encode('ascii')
            f.attrs["SATPYR_UNITS"] = "count".encode('ascii')
            f.attrs["PROCESSING_LEVEL"] = "1a".encode('ascii')
            f.attrs["TIME-STAMP"] = timestamp.encode('ascii')
            f.attrs["RAW_FILE_NAME"] = str(fp[0]).encode('ascii')

            gps = f.create_group('GPS')
            gps.attrs['DISTANCE_1'] = "Pressure None 1 1 0".encode('ascii')
            gps.attrs['DISTANCE_2'] = "Surface None 1 1 0".encode('ascii')
            gps.attrs['FrameTag'] = "$GPS".encode('ascii')
            gps.attrs['FrameType'] = "Not Required".encode('ascii')
            gps.attrs['InstrumentType'] = "GPS".encode('ascii')
            gps.attrs['MeasMode'] = "Not Required".encode('ascii')
            gps.attrs['Media'] = "Not Required".encode('ascii')
            gps.attrs['SensorDataList'] = "INTTIME, SAMPLE, THERMAL_RESP, ES, DARK_SAMP, DARK_AVE, SPECTEMP, FRAME, TIMER, CHECK, DATETAG, TIMETAG2, POSFRAME".encode('ascii')

            N_GPS = len(HHMMSS) # GBAI: TO CHECK IF NEED TO BE MODIFY

            rec_geoid  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['NaN'.encode('ascii')]*N_GPS)
            rec_geoidunits  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['M'.encode('ascii')]*N_GPS)
            rec_alt  = TriosL1A.reshape_data('NONE',N_GPS,data=alt * np.ones(N_GPS))
            rec_altunits  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['M'.encode('ascii')]*N_GPS)
            rec_utcpos  = TriosL1A.reshape_data('NONE',N_GPS,data=HHMMSS)
            rec_datetag  = TriosL1A.reshape_data('NONE',N_GPS,data=YYYDOY)
            rec_fixqual  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS))
            rec_horiz  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS))
            rec_lathemi  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['N'.encode('ascii')]*N_GPS)
            rec_lonhemi  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['E'.encode('ascii')]*N_GPS)
            rec_nmea  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS))
            rec_numsat  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS)*10)
            rec_posframe  = TriosL1A.reshape_data('NONE',N_GPS,data=np.ones(N_GPS))
            rec_refstat  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['NaN'.encode('ascii')]*N_GPS)
            rec_timelag  = TriosL1A.reshape_data_str('NONE',N_GPS,data=['NaN'.encode('ascii')]*N_GPS)
            rec_timetag  = TriosL1A.reshape_data('NONE',N_GPS,data=TTAG2)
            rec_lon  = TriosL1A.reshape_data('NONE',N_GPS,data=LONPOS)
            rec_lat  = TriosL1A.reshape_data('NONE',N_GPS,data=LATPOS)

            gps.create_dataset('GEOID', data=rec_geoid)
            gps.create_dataset('GEOIDUNITS' , data=rec_geoidunits)
            gps.create_dataset('ALT' , data=rec_alt)
            gps.create_dataset('ALTUNITS' , data=rec_altunits)
            gps.create_dataset('UTCPOS' , data=rec_utcpos)
            gps.create_dataset('DATETAG' , data=rec_datetag)
            gps.create_dataset('FIXQUAL' , data=rec_fixqual)
            gps.create_dataset('HORIZ' , data=rec_horiz)
            gps.create_dataset('LATHEMI' , data=rec_lathemi)
            gps.create_dataset('LONHEMI' , data=rec_lonhemi)
            gps.create_dataset('NMEA_CHECKSUM' , data=rec_nmea)
            gps.create_dataset('NUMSAT' , data=rec_numsat)
            gps.create_dataset('POSFRAME' , data=rec_posframe)
            gps.create_dataset('REFSTAT' , data=rec_refstat)
            gps.create_dataset('TIMELAG' , data=rec_timelag)
            gps.create_dataset('TIMETAG2' , data=rec_timetag)
            gps.create_dataset('LATPOS' , data=rec_lat)
            gps.create_dataset('LONPOS' , data=rec_lon)

            for name in instrument:
                start,stop = TriosL1A.formatting_instrument_single(name,cal_path,fp,f,configPath)
            new_name = outFilePath + '/' + 'Trios_' + str(start) + '_' + str(stop) + '_L1A.hdf'
            new_name = os.path.join(outFilePath, 'Trios_' + str(start) + '_' + str(stop) + '_L1A.hdf')
            os.rename(outFilePath+hdfout, new_name)

        return None
