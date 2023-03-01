
import numpy as np
import h5py
from HDFRoot import HDFRoot
from HDFGroup import HDFGroup
import sys, os
import pandas as pd
import glob
from datetime import datetime, timedelta, date
from Utilities import Utilities


class SeabirdasciiL1a:

    def get_attr(calfile, radiometer, group):
        HEAD = 'HEAD_0'
        cfile= open(calfile, 'r')
        # use header to reach info of interest
        if radiometer!="ES":
            unit = 'uW/cm^2/nm/sr'
        else:
            unit = 'uW/cm^2/nm'
        for x in cfile:
            if radiometer in x and unit in x:
                #extract the wavelength
                wl   = x.split("'"+unit+"'")[0].split(radiometer+' ')[1]
                HEAD, idx = HEAD.split('_')
                idx = str(int(idx)+1)
                HEAD = HEAD+'_' + idx
                group.attributes[HEAD] = radiometer+" 1 1 "+wl


    def reshape_string(datalist):
        asciiList = [n.encode("ascii") for n in datalist]
        return asciiList


    def AsciiFileReader(inputfile):
        print("Open input files:", os.path.basename(inputfile))
        csv=pd.read_csv(inputfile, header=None)
        # Adapt the format of the input file
        newframe = csv[0].str.split()

        # Get metadata

        HEADER = newframe[2]
        # Type of Measurement (Es, Li or Lt)
        TypeMes= HEADER[2].split('(')[1].split(')')[0]
        # List of Header for radiometric measurement (e.g. ES(308.4) )
        H_rdm  = HEADER[4:-8]
        namesList = []
        # retrieve only the wavelength
        separ  = TypeMes + '('
        for x in H_rdm:
            namesList.append(x.replace(separ,"").replace(")",""))

        csv=pd.read_csv(inputfile, skiprows=3, sep=' ')
        cks  = csv['CHECK(SUM)'][1:]
        dka  = csv['DARK_AVE('+TypeMes+')'][1:]
        dks  = csv['DARK_SAMP('+TypeMes+')'][1:]
        dtag = csv['DATETAG'][1:].str.replace("-","")
        frame= csv['FRAME(COUNTER)'][1:]
        itime= csv['INTTIME('+TypeMes+')'][1:]
        smpl = csv['SAMPLE(DELAY)'][1:]
        temp = csv['TEMP(PCB)'][1:]
        timr = csv['TIMER'][1:]
        ttag2= csv['TIMETAG2'][1:].str.replace(":","").str.replace(".","")
        rad  = csv.iloc[1:,4:259]

        N = len(csv)
        tresp = np.zeros(N)

        posf  = np.linspace(1,N*2,N).astype(int)

        frame =[N, rad, cks, dka, dks, dtag, frame, itime,
                 smpl, temp, timr,tresp, posf, ttag2, namesList]

        return frame , TypeMes


    def reformat_coord(x, hemi):
        d, m, pos = SeabirdasciiL1a.ddToDm(float(x))
        X = ("{} {}' ").format(d, m)+hemi
        return X, pos

    def ddToDm(dd):
        d = int(dd)
        m = abs(dd - d)*60
        dm = (d*100) + m
        return d, m, dm

    def seabirdasciiL1a(inFilePath, outFilePath, configPath, ancillaryData):
        ascii_type = h5py.string_dtype('ascii',30)
        configPath = os.path.splitext(configPath)[0]+'_Calibration'

        # creation of the telemetry file
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
            lonpos = SeabirdasciiL1a.reformat_coord(df['lon'][j], 'E')[1]
            latpos = SeabirdasciiL1a.reformat_coord(df['lat'][j], 'N')[1]

            day_of_year = str(date(year, month, day).timetuple().tm_yday)
            YYYDOY = np.append(YYYDOY, int(str(year)+day_of_year))
            LONPOS = np.append(LONPOS, float(lonpos))
            LATPOS = np.append(LATPOS, float(latpos))

#            LATPOS = np.append(LATPOS, [latpos.encode('ascii')])

        now = datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")

        # Construct the hdf File
        root = HDFRoot()
        root.id = "/"

        gpsGroup = HDFGroup()
        gpsGroup.id = 'GPS'
        root.groups.append(gpsGroup)

        N_GPS = len(HHMMSS)

        gpsGroup.addDataset("ALT")
        gpsGroup.addDataset("ALTUNITS")
        gpsGroup.addDataset("DATETAG")
        gpsGroup.addDataset("FIXQUAL")
        gpsGroup.addDataset("GEOID")
        gpsGroup.addDataset("GEOIDUNITS")
        gpsGroup.addDataset("HORIZ")
        gpsGroup.addDataset("LATHEMI")
        gpsGroup.addDataset("LATPOS")
        gpsGroup.addDataset("LONHEMI")
        gpsGroup.addDataset("LONPOS")
        gpsGroup.addDataset("NMEA_CHECKSUM")
        gpsGroup.addDataset("NUMSAT")
        gpsGroup.addDataset("POSFRAME")
        gpsGroup.addDataset("REFSTAT")
        gpsGroup.addDataset("TIMELAG")
        gpsGroup.addDataset("TIMETAG2")
        gpsGroup.addDataset("UTCPOS")
        ascii_type = h5py.string_dtype('ascii',30)

        gpsGroup.datasets["GEOID"].columns["NONE"] = ['NaN'.encode('ascii')]*N_GPS
        gpsGroup.datasets["GEOIDUNITS"].columns["NONE"] = ['M'.encode('ascii')]*N_GPS
        gpsGroup.datasets["ALT"].columns["NONE"] = alt * np.ones(N_GPS)
        gpsGroup.datasets["ALTUNITS"].columns["NONE"] = ['M'.encode('ascii')]*N_GPS
        gpsGroup.datasets["UTCPOS"].columns["NONE"] = HHMMSS
        gpsGroup.datasets["DATETAG"].columns["NONE"] = YYYDOY
        gpsGroup.datasets["FIXQUAL"].columns["NONE"] = np.ones(N_GPS)
        gpsGroup.datasets["HORIZ"].columns["NONE"] = np.ones(N_GPS)
        gpsGroup.datasets["LATHEMI"].columns["NONE"] = ['N'.encode('ascii')]*N_GPS
        gpsGroup.datasets["LATPOS"].columns["NONE"] = LATPOS
        gpsGroup.datasets["LONHEMI"].columns["NONE"] = ['E'.encode('ascii')]*N_GPS
        gpsGroup.datasets["LONPOS"].columns["NONE"] = LONPOS
        gpsGroup.datasets["NMEA_CHECKSUM"].columns["NONE"] = np.ones(N_GPS)
        gpsGroup.datasets["NUMSAT"].columns["NONE"] = np.ones(N_GPS)*10.
        gpsGroup.datasets["POSFRAME"].columns["COUNT"] = np.ones(N_GPS)
        gpsGroup.datasets["REFSTAT"].columns["NONE"] = ['NaN'.encode('ascii')]*N_GPS
        gpsGroup.datasets["TIMELAG"].columns["NONE"] = ['NaN'.encode('ascii')]*N_GPS
        gpsGroup.datasets["TIMETAG2"].columns["NONE"] = TTAG2

        gpsGroup.attributes['DISTANCE_1'] = "Pressure None 1 1 0"
        gpsGroup.attributes['DISTANCE_2'] = "Surface None 1 1 0"
        gpsGroup.attributes['FrameTag'] = "$GPS"
        gpsGroup.attributes['FrameType'] = "Not Required"
        gpsGroup.attributes['InstrumentType'] = "GPS"
        gpsGroup.attributes['MeasMode'] = "Not Required"
        gpsGroup.attributes['Media'] = "Not Required"
        gpsGroup.attributes['SensorDataList'] = "INTTIME, SAMPLE, THERMAL_RESP, ES, DARK_SAMP, DARK_AVE, SPECTEMP, FRAME, TIMER, CHECK, DATETAG, TIMETAG2, POSFRAME"

        # Formatting of radiometric dataset
        # Loop on the files with the same prefix than the input file

        '''
        inpath = os.path.dirname(inFilePath)
        fdat = os.path.basename(inFilePath)
        fdat = fdat.split('-')[:-1]
        fdat = '-'.join(fdat)+'*.dat'
        ListInput = glob.glob(os.path.join(inpath, fdat))

        ListInput = inFilePath
        print('TEST TEST TEST TEST SEABASS')
        print(ListInput)
        exit()

        # Check the number of input files
        if len(inFilePath)!=6:
            print('Err: {} files found while 6 are expected'.format(len(inFilePath)))
            print('Aborting')
            sys.exit()
        else:
            print('{} in situ files found '.format(len(inFilePath)))
            print('Write the HDF file')
        '''

        print('{} in situ files found '.format(len(inFilePath)))
        print('Writing the HDF file')

        ListCal = [os.path.basename(ancillaryData)]

        #print(ListCal)

        acq_time = []
        for file in inFilePath:
            a_time = file.split('/')[-1].rsplit('-',1)[0]
            acq_time.append(a_time)
        acq_time = list(dict.fromkeys(acq_time))
        for a_time in acq_time:
            inFilePath_ascii = [s for s in inFilePath if a_time in s]


            for h in inFilePath_ascii:
                H, instr= SeabirdasciiL1a.AsciiFileReader(h)
                h = os.path.basename(h).split('-')[-1]
                print('Read:', h)

                pre= h[:3]
                SN = os.path.splitext(h)[0]
                sn = '{:0>4}'.format(int(SN[3:-1]))
    #            cal = os.path.join(args.cal, SN+'.cal')
                cal = os.path.join(configPath, SN+'.cal')
                ListCal = np.append(ListCal, pre+sn+'.cal')

                if SN[:3]=='HED' or SN[:3]=='HLD':
                    shutter = 'Dark'
                else:
                    shutter = 'Light'

                #create a group within the HDF file for the instrument in question
                gpRad = HDFGroup()
                gpRad.id = os.path.basename(h)
                root.groups.append(gpRad)

                gpRad.addDataset('CHECK')
                gpRad.addDataset('DARK_AVE')
                gpRad.addDataset('DARK_SAMP')
                gpRad.addDataset('DATETAG')
                gpRad.addDataset(instr)
                #print('instr',instr)
                gpRad.addDataset('FRAME')
                gpRad.addDataset('INTTIME')
                gpRad.addDataset('POSFRAME')
                gpRad.addDataset('SAMPLE')
                gpRad.addDataset('SPECTEMP')
                gpRad.addDataset('TIMER')
                gpRad.addDataset('THERMAL_RESP')
                gpRad.addDataset('TIMETAG2')

                wl = np.array(H[-1]).astype(float)
                gpRad.datasets['CHECK'].columns["SUM"] = np.array(H[2])
                gpRad.datasets['DARK_AVE'].columns[instr] = np.array(H[3])
                gpRad.datasets['DARK_SAMP'].columns[instr] = np.array(H[4])
                gpRad.datasets['DATETAG'].columns["NONE"] = np.array(H[5], dtype=float)
                es = np.array(H[1])

                for i in range(len(wl)):
                    gpRad.datasets[instr].columns['{0:.2f}'.format(wl[i])] = np.array(es[:,i], dtype=float)

                gpRad.datasets['FRAME'].columns["COUNTER"] = np.array(H[6])
                gpRad.datasets['INTTIME'].columns[instr] = np.array(H[7], dtype=float )
                gpRad.datasets['POSFRAME'].columns["COUNT"] = np.array(H[12])
                gpRad.datasets['SAMPLE'].columns["DELAY"] = np.array(H[8], dtype=float )
                gpRad.datasets['SPECTEMP'].columns["NONE"] = np.array(H[9], dtype=float)
                gpRad.datasets['TIMER'].columns["NONE"] = np.array(H[10], dtype=float )
                gpRad.datasets['THERMAL_RESP'].columns["NONE"] = np.array(H[11])
                gpRad.datasets['TIMETAG2'].columns["NONE"] = np.array(H[13], dtype=float)

                # Add metadata
                CalId = '{:04d}'.format(int(SN[3:-1]))

                gpRad.attributes['CalFileName'] = SN+'.cal'
                gpRad.attributes['DISTANCE_1'] = "Pressure "+instr+" 1 1 0"
                gpRad.attributes['DISTANCE_2'] = "Surface "+instr+" 1 1 0"
                gpRad.attributes['FrameTag'] = "SAT"+h[:3]+CalId
                gpRad.attributes['FrameType'] = "Shutter"+shutter
                SeabirdasciiL1a.get_attr(cal, instr, gpRad)
                gpRad.attributes['InstrumentType'] = "SAS"
                gpRad.attributes['MeasMode'] = "Surface"
                gpRad.attributes['Media'] = "Air"
                gpRad.attributes['SN'] = CalId
                gpRad.attributes['SensorDataList'] = "INTTIME, SAMPLE, THERMAL_RESP, ES, DARK_SAMP, DARK_AVE, SPECTEMP, FRAME, TIMER, CHECK, DATETAG, TIMETAG2, POSFRAME"



            root.attributes['AFFILIATION']=str('Missing').encode("ascii")
            root.attributes['CAL_FILE_NAMES']=ListCal
            root.attributes['CAST']='AA'
            root.attributes['CLOUD_PERCENT']=str('Missing').encode("ascii")
            root.attributes['COMMENT']=str('Missing').encode("ascii")
            root.attributes['CONTACT']=contact
            root.attributes['CRUISE-ID']=cruise
            root.attributes['DATETAG']='ON'
            root.attributes['DOCUMENT']='readme.txt'
            root.attributes['ES_UNITS']='count'
            root.attributes['EXPERIMENT']='Missing'
            root.attributes['FILE_CREATION_TIME']=timestr
            root.attributes['HYPERINSPACE']='1.0.9'
            root.attributes['INVESTIGATOR']=investigator
            root.attributes['LATITUDE']=SeabirdasciiL1a.reformat_coord(df['lat'][0],'N')[0]
            root.attributes['LI_UNITS']='count'
            root.attributes['LONGITUDE']=SeabirdasciiL1a.reformat_coord(df['lon'][0],'E')[0]
            root.attributes['LT_UNITS']='count'
            root.attributes['MODE']='NONE'
            root.attributes['NMEA']='$GPS'
            root.attributes['OPERATOR']='Missing'
            root.attributes['PRO-DARK']='OFF'
            root.attributes['PROCESSING_LEVEL']='1a'
            root.attributes['PROFILER']='OFF'
            root.attributes['RAW_FILE_NAME']=str(inFilePath).encode('ascii')
            root.attributes['REF-DARK']='OFF'
            root.attributes['REFERENCE']='OFF'
            root.attributes['SATPYR_UNITS']='count'
            root.attributes['STATION-ID']='Missing'
            root.attributes['SZA_FILTER_1A']=70.0
            #root.attributes['SZA_FILTER_1A']=ConfigFile.settings["fL1aCleanSZAMax"]
            root.attributes['TIME-STAMP']=timestamp
            root.attributes['TIMETAG']='OFF'
            root.attributes['TIMETAG2']='ON'
            root.attributes['WAVELENGTH_UNITS']='Missing'
            root.attributes['WAVE_HEIGHT']='Missing'
            root.attributes['WIND_SPEED']='Missing'
            root.attributes['ZONE']='Missing'



            # Converts gp.columns to numpy array
            for gp in root.groups:
                if gp.id.startswith("SATMSG"): # Don't convert these strings to datasets.
                    for key in gp.datasets.keys():
                        ds = gp.datasets[key]
                else:
                    for key in gp.datasets.keys():
                        ds = gp.datasets[key]
                        if not ds.columnsToDataset():
                            msg = "ProcessL1a.processL1a: Essential column cannot be converted to Dataset. Aborting."
                            print(msg)
                            Utilities.writeLogFile(msg)


            root.writeHDF5(outFilePath+'/SeaBird_'+a_time+'_L1A.hdf')

        root = None

        return None
#    root.writeHDF5(args.output)
#    print(args.output, ' - SUCCESSFUL')


