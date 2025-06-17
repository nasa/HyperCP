'''Process Raw (L0) data to L1A HDF5'''
import os
from datetime import datetime
import datetime as dt
import numpy as np
import pandas as pd


from Source.HDFRoot import HDFRoot
from Source.HDFGroup import HDFGroup
from Source.MainConfig import MainConfig
from Source.Utilities import Utilities
from Source.ConfigFile import ConfigFile


class ProcessL1aDALEC:
    '''Process L1A'''
    @staticmethod
    def processL1a(fp, calibrationMap):
        (_, fileName) = os.path.split(fp)
        #print('This is a placeholder')
        calMap=list(calibrationMap.values())
        calfile=calMap[0].name
        calid=calMap[0].id

        #read cal data
        meta_instrument,coefficients,cal_data=ProcessL1aDALEC.read_cal(calfile)
        #cal dataframes for all 3 channels
        cal_ch=[]
        cal_ch.append(cal_data.iloc[:,2:4])
        cal_ch.append(cal_data.iloc[:,5:7])
        cal_ch.append(cal_data.iloc[:,8:10])
        #print(cal_ch[0].columns.tolist())

        #wavelength all 3 channels
        wl=[]
        wl.append(cal_data['Lambda_Ed'].tolist())
        wl.append(cal_data['Lambda_Lu'].tolist())
        wl.append(cal_data['Lambda_Lsky'].tolist())
        #print(wl[0])

        #read raw data
        metadata,data=ProcessL1aDALEC.read_data(fp)
        #define cal dataframes for all 3 channels
        data_ch=[]
        #filter out each channel (Es-Ed,Li-Lsky,Lt-Lu)
        mask = data['Lat'].notna()
        #mask = data.notna()
        data1=data[mask]
        mask=data1['SolarAzimuth'].notna()
        data2=data1[mask]
        mask=data2['RelAz'].notna()
        data_good=data2[mask]

        mask = data_good['ChannelType'].isin(['Ed'])
        data_ch.append(data_good[mask])
        mask = data_good['ChannelType'].isin(['Lu'])
        data_ch.append(data_good[mask])
        mask = data_good['ChannelType'].isin(['Lsky'])
        data_ch.append(data_good[mask])
        #print(data_ch[0].dtypes)
        #print(data_ch[1].columns.tolist())

        # creates an HDF
        root = HDFRoot()
        root.id = "/"
        #write global attributes
        if os.environ['HYPERINSPACE_CMD'].lower =='true': # os.environ must be string
            MainConfig.loadConfig('cmdline_main.config','version')
        else:
            MainConfig.loadConfig('main.config','version')
        root.attributes["HYPERINSPACE"] = MainConfig.settings["version"]
        root.attributes["CAL_FILE_NAMES"] = ','.join(calibrationMap.keys())
        root.attributes["WAVELENGTH_UNITS"] = "nm"
        root.attributes["LI_UNITS"] = "count"
        root.attributes["LT_UNITS"] = "count"
        root.attributes["ES_UNITS"] = "count"
        root.attributes["RAW_FILE_NAME"] = fileName
        root.attributes["PROCESSING_LEVEL"] = "1a"

        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        root.attributes["FILE_CREATION_TIME"] = timestr

        msg = f"ProcessL1a.processL1a: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        #add global attributes from calfile
        for row in meta_instrument.itertuples():
            root.attributes[row[1].strip().replace(" ","_")]=str(row[2])

        #add global attributes from raw data file
        for row in metadata.itertuples():
            root.attributes[row[1].strip().replace(" ","_")]=str(row[2])

        #get TimeTag2 and DateTag data sets
        dateFormat='%Y-%m-%dT%H:%M:%S.%f'
        dtime=[datetime.strptime(i.replace('Z','000'),dateFormat) for i in data_good['UTCtimestamp']]
        TimeTag2 = [Utilities.datetime2TimeTag2(i) for i in dtime]
        DateTag = [Utilities.datetime2DateTag(i) for i in dtime]
        root.attributes["TIME-STAMP"] = dt.datetime.strftime(dtime[0],'%a %b %d %H:%M:%S %Y')

        #add GPS group
        gp =  HDFGroup()
        gp.id = calid+'.GP'
        root.groups.append(gp)
        gp.attributes['CalFileName']=calid
        gp.attributes['FrameType']="Not Required"
        gp.addDataset("DATETAG")
        gp.addDataset("TIMETAG2")            
        gp.datasets["DATETAG"].data = np.array(DateTag, dtype=[('NONE', '<f8')])
        gp.datasets["TIMETAG2"].data = np.array(TimeTag2, dtype=[('NONE', '<f8')])
        gp.addDataset("LAT")
        gp.datasets["LAT"].data = np.array(data_good['Lat'].tolist(), dtype=[('NONE', '<f8')])
        gp.addDataset("LON")
        gp.datasets["LON"].data = np.array(data_good['Lon'].tolist(), dtype=[('NONE', '<f8')])

        #add SolarTrackor group
        gp =  HDFGroup()
        gp.id = calid+'.ST'
        root.groups.append(gp)
        gp.attributes['CalFileName']=calid
        gp.attributes['FrameType']="Not Required"
        gp.addDataset("DATETAG")
        gp.addDataset("TIMETAG2")            
        gp.datasets["DATETAG"].data = np.array(DateTag, dtype=[('NONE', '<f8')])
        gp.datasets["TIMETAG2"].data = np.array(TimeTag2, dtype=[('NONE', '<f8')])
        gp.addDataset("HUMIDITY")
        gp.datasets["HUMIDITY"].data = np.array(data_good['Humidity'].tolist(), dtype=[('NONE', '<f8')])
        gp.addDataset("VOLTAGE")
        gp.datasets["VOLTAGE"].data = np.array(data_good['Voltage'].tolist(), dtype=[('NONE', '<f8')])
        gp.addDataset("POINTING")
        gp.datasets["POINTING"].data = np.array(data_good['SatelliteCompassHeading'].tolist(), dtype=[('ROTATOR', '<f8')])
        gp.addDataset("PITCH")
        gp.datasets["PITCH"].data = np.array(data_good['Pitch'].tolist(), dtype=[('SAS', '<f8')])
        gp.addDataset("ROLL")
        gp.datasets["ROLL"].data = np.array(data_good['Roll'].tolist(), dtype=[('SAS', '<f8')])
        gp.addDataset("REL_AZ")
        gp.datasets["REL_AZ"].data = np.array(np.abs(data_good['RelAz']).tolist(), dtype=[('REL_AZ', '<f8')])

        # Apply SZA filter; Currently only works with SunTracker data at L1A (again possible in L2 for all types)
        if ConfigFile.settings["bL1aCleanSZA"]:
            root.attributes['SZA_FILTER_L1A'] = ConfigFile.settings["fL1aCleanSZAMax"]
        szaLimit = float(ConfigFile.settings["fL1aCleanSZAMax"])
        szaMin=np.nanmin(data_good['SolarZenith'].tolist())
        if szaMin > szaLimit:
            msg = f'SZA too low. Discarding entire file. {round(szaMin)}'
            print(msg)
            Utilities.writeLogFile(msg)
            return None
        else:
            msg = f'SZA passed filter: {round(szaMin)}'
            print(msg)
            Utilities.writeLogFile(msg)

        gp.addDataset("SZA")
        gp.datasets["SZA"].data = np.array(data_good['SolarZenith'].tolist(), dtype=[('NONE', '<f8')])
        gp.addDataset("SOLAR_AZ")
        gp.datasets["SOLAR_AZ"].data = np.array(data_good['SolarAzimuth'].tolist(), dtype=[('NONE', '<f8')])

        #channel types
        channelType=['ES','LT','LI']

        #add Calibration coefficient group
        gp =  HDFGroup()
        gp.id = calid+'.CE'
        root.groups.append(gp)
        gp.attributes['CalFileName']=calid
        for row in coefficients.itertuples():
            gp.attributes[row[1].strip().replace(" ","_")]=str(row[2])
        for i in [0,1,2]:
            gp.addDataset('Cal_'+channelType[i])
            cal_par=cal_ch[i].columns.tolist()
            ds_dt = np.dtype({'names': cal_par,'formats': [np.float64]*len(cal_par)})
            my_arr=cal_ch[i].to_numpy().transpose()
            #print(my_arr)
            rec_arr = np.rec.fromarrays(my_arr, dtype=ds_dt)
            gp.datasets['Cal_'+channelType[i]].data=np.array(rec_arr, dtype=ds_dt)

        for i in [0,1,2]:
            gp =  HDFGroup()
            gp.id = calid+'.'+channelType[i]
            root.groups.append(gp)
            gp.attributes['CalFileName']=calid
            gp.attributes['FrameType']="Not Required"
            gp.attributes['SensorDataList']='Cal_'+channelType[i]+','+channelType[i]+',DATETAG,TIMETAG2,INTTIME,SPECTEMP'

            #add channel data
            gp.addDataset(channelType[i])
            wl_str=[str(x) for x in wl[i]]
            ds_dt = np.dtype({'names': wl_str,'formats': [np.float64]*len(wl_str)})
            #print(data_ch[i].iloc[:,22:])
            my_arr=data_ch[i].iloc[:,22:].to_numpy().transpose()
            rec_arr = np.rec.fromarrays(my_arr, dtype=ds_dt)
            gp.datasets[channelType[i]].data=np.array(rec_arr, dtype=ds_dt)

            #add ancillary data sets
            dateFormat='%Y-%m-%dT%H:%M:%S.%f'
            dtime=[datetime.strptime(i.replace('Z','000'),dateFormat) for i in data_ch[i]['UTCtimestamp']]
            TimeTag2 = [Utilities.datetime2TimeTag2(i) for i in dtime]
            DateTag = [Utilities.datetime2DateTag(i) for i in dtime]
            #print(TimeTag2)

            gp.addDataset("DATETAG")
            gp.addDataset("TIMETAG2")            
            gp.datasets["DATETAG"].data = np.array(DateTag, dtype=[('NONE', '<f8')])
            gp.datasets["TIMETAG2"].data = np.array(TimeTag2, dtype=[('NONE', '<f8')])
            gp.addDataset("DARK_CNT")
            gp.datasets["DARK_CNT"].data = np.array(data_ch[i]['DarkCounts'].tolist(), dtype=[(channelType[i], '<f8')])
            gp.addDataset("INTTIME")
            gp.datasets["INTTIME"].data = np.array(data_ch[i]['Inttime'].tolist(), dtype=[(channelType[i], '<f8')])
            gp.addDataset("SPECTEMP")
            gp.datasets["SPECTEMP"].data = np.array(data_ch[i]['DetectorTemp'].tolist(), dtype=[('NONE', '<f8')])
            gp.addDataset("QFLAG")
            gp.datasets["QFLAG"].data = np.array(data_ch[i]['Qflag'].tolist(), dtype=[(channelType[i], '<f8')])

            # Correct for UTC offset
        try:
            root  = Utilities.rootAddDateTime(root)
        except AttributeError as err:
            msg = f"ProcessL1a.processL1a: Cannot add datetime to a group dataset: {err}. Aborting."
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Adjust to UTC if necessary
        if ConfigFile.settings["fL1aUTCOffset"] != 0:
            # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
            root = Utilities.SASUTCOffset(root)

        # DATETIME is not supported in HDF5; remove
        for gp in root.groups:
            if ".cal.CE" not in gp.id:
                del gp.datasets["DATETIME"]

        return root
        #return None, None

    # Function for reading cal files
    @staticmethod
    def read_cal(inputfile):
        file_dat = open(inputfile,'r', encoding="utf-8")
        # flag_instrument = 0
        flag_coefficients = 0
        flag_data = 0
        data_hdr=[]
        index = 0
        for line in file_dat:
            index = index + 1
            # checking end of attributes
            # if 'Variable list' in line:
                # flag_instrument = index
            if 'Spectrometer' in line:
                flag_coefficients = index
            if 'Pixel' in line:
                data_hdr=[item.strip() for item in line[1:].split(',')]
                flag_data = index
                break

        if flag_coefficients == 0:
            print('PROBLEM WITH CAL FILE: Coefficents not found')
            exit()
        if flag_data == 0:
            print('PROBLEM WITH CAL FILE: data not found')
            exit()

        file_dat.close()

        meta_instrument = pd.read_csv(inputfile, skiprows=1, nrows=4, on_bad_lines='skip',header=None, comment=';',sep=':')
        coefficients = pd.read_csv(inputfile, skiprows=flag_coefficients+1, nrows=10,header=None, comment=';',sep='=')
        data = pd.read_csv(inputfile, skiprows=flag_data, nrows=200, names=data_hdr,on_bad_lines='warn')

        return meta_instrument,coefficients,data

    @staticmethod
    def validate_line(line):
        """
        Validates a CSV line with the following rules:
        1. The first element must be the string "DALEC".
        2. The second and third elements must be strings.
        3. The fourth element must be a date string in the format "YYYY-MM-DDTHH:MM:SS.sssZ".
        4. The remaining elements must be numbers.
    
        Returns True if valid, otherwise False.
        """
        if len(line) != 212:  # Ensure there are enough elements
            return False

        # 1. First element must be "DALEC"
        if line[0] != "DALEC":
            return False

        # 2. Second and third elements must be strings (implicitly true since they are parsed as strings)
        if not isinstance(line[1], str) or not isinstance(line[2], str):
            return False

        # 3. Fourth element must be a valid date string in the format "YYYY-MM-DDTHH:MM:SS.sssZ"
        try:
            dt.datetime.strptime(line[3], "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            return False

        # 4. The remaining elements must be numbers (float or int)
        try:
            for item in line[4:]:
                float(item)  # Convert to float, raises an exception if not a number
        except ValueError:
            return False

        return True  # If all checks pass

    @staticmethod
    def read_data(inputfile):
        file_dat = open(inputfile,'r', encoding="utf-8")
        flag_config = 0
        flag_end_config = 0
        flag_data = 0
        data_hdr=['DeviceID','SerialNumber','ChannelType','UTCtimestamp','Lat','Lon','SatelliteCompassHeading',
        'SolarAzimuth','SolarZenith','GearPos','DALECazimuth','RelAz','Pitch','Roll','Voltage','Humidity','DetectorTemp',
        'Qflag','Inttime','Signal_percent','DarkCounts','MaxCounts']
        # data_type={'Lat':np.float64,'Lon':np.float64,'SatelliteCompassHeading':np.float64,'SolarAzimuth':np.float64,
        #            'SolarZenith':np.float64,'GearPos':np.float64,'DALECazimuth':np.float64,'RelAz':np.float64,
        #            'Pitch':np.float64,'Roll':np.float64,'Voltage':np.float64,'Humidity':np.float64,
        #            'DetectorTemp':np.float64,'Qflag':np.float64,'Inttime':np.float64,
        #            'Signal_percent':np.float64,'DarkCounts':np.float64,'MaxCounts':np.float64}
        for i in range(190):
            data_hdr.append('spec'+str(i))

        index = 0
        for line in file_dat:
            index = index + 1
            if '-CONFIGURATION' in line:
                flag_config = index
            elif '-END CONFIGURATION' in line:
                flag_end_config = index
            elif '-OUTPUT FORMAT' in line:
                flag_data = index
                break

        if flag_data == 0:
            print('PROBLEM WITH Data FILE: data not found')
            exit()
        skiprows=list(range(flag_data+1))

        index = index + 1
        if not file_dat.readline():  # Stop if there are fewer than 1 lines to skip
            print('PROBLEM WITH Data FILE: data not found')
            exit()

        for line in file_dat:
            if not ProcessL1aDALEC.validate_line(line.split(",")):
                skiprows.append(index)
                print("Bad data line: "+str(index))
                print(line)
            index = index + 1

        file_dat.close()

        # def toDatetime(dt):
        #     #dateFormat='%Y-%m-%dT%H:%M:%S.%f'
        #     return np.datetime64(dt.replace('Z', '000'))

        metadata = pd.read_csv(inputfile, skiprows=flag_config, nrows=flag_end_config-flag_config-1,header=None, comment=';',sep='=')
        data = pd.read_csv(inputfile, skiprows=skiprows, names=data_hdr, on_bad_lines='warn')

        return metadata,data
