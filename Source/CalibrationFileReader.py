'''Read in calibration and telemetry definition files'''
import collections
import os.path
import shutil
import zipfile

from Source.CalibrationFile import CalibrationFile
import Source.utils.loggingHCP as logging


class CalibrationFileReader:
    '''Read in calibration and telemetry definition files. Return the calibrationMap.'''
    # reads calibration files stored in directory
    @staticmethod
    def read(fp):
        calibrationMap = collections.OrderedDict()

        for (dirpath, dirnames, filenames) in os.walk(fp):
            for name in filenames:
                #print("infile:", name)
                if name.lower().startswith("dalec"):
                    cf = CalibrationFile()
                    cf.id=name
                    cf.name=os.path.join(dirpath,name)
                    cf.instrumentType = "Dalec"
                    # NOTE: Highly presumptuous format requirement here
                    try:
                        # This will update with each new calibration date until the last/latest date
                        calYr = int(name[11:15])
                        calMon = int(name[16:18])
                        calDay = int(name[19:21])
                        # calDT = datetime.strptime(f'{calYr:04d}{calMon:02d}{calDay:02d}+0000', '%Y%m%d%z')
                        cf.CalibrationDate = f'{calYr:04d}{calMon:02d}{calDay:02d}000000'
                    except ValueError as err:
                        logging.writeLogFileAndPrint(f"Failed to calibration dates from calibration file {name}: {err}")
                        break
                    calibrationMap[name] = cf
                elif os.path.splitext(name)[1].lower() == ".cal" or \
                   os.path.splitext(name)[1].lower() == ".tdf":
                    with open(os.path.join(dirpath, name), 'rb') as f:
                        cf = CalibrationFile()
                        cf.read(f)
                        #print("id:", cf.id)
                        calibrationMap[name] = cf
            break

        return calibrationMap

    # reads calibration files stored in .sip file (renamed .zip)
    @staticmethod
    def readSip(fp):
        calibrationMap = collections.OrderedDict()

        with zipfile.ZipFile(fp, 'r') as zf:
            for finfo in zf.infolist():
                if not str(finfo.filename).startswith('__MACOSX/'):
                    print("infile:", finfo.filename)
                    if os.path.splitext(finfo.filename)[1].lower() == ".cal" or \
                    os.path.splitext(finfo.filename)[1].lower() == ".tdf":
                        with zf.open(finfo) as f:
                            cf = CalibrationFile()
                            cf.read(f)
                            #print("id:", cf.id)
                            calibrationMap[finfo.filename] = cf
                            [dest,_] = os.path.split(fp)
                            src = zf.extract(f.name,path=dest)
                            [_,fname] = os.path.split(f.name)
                            shutil.move(src, os.path.join(dest,fname))

        return calibrationMap
