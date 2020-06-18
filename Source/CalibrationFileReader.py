
import collections
import os.path
import zipfile

from CalibrationFile import CalibrationFile


class CalibrationFileReader:

    # reads calibration files stored in directory
    @staticmethod
    def read(fp):
        calibrationMap = collections.OrderedDict()

        for (dirpath, dirnames, filenames) in os.walk(fp):
            for name in filenames:
                #print("infile:", name)
                if os.path.splitext(name)[1].lower() == ".cal" or \
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
                print("infile:", finfo.filename)
                if os.path.splitext(finfo.filename)[1].lower() == ".cal" or \
                   os.path.splitext(finfo.filename)[1].lower() == ".tdf":
                    with zf.open(finfo) as f:
                        cf = CalibrationFile()
                        cf.read(f)
                        #print("id:", cf.id)
                        calibrationMap[finfo.filename] = cf

        return calibrationMap
