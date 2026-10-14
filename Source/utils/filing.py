'''################################# FILE AND DOWNLOAD ORIENTED #################################'''
import os
from datetime import datetime
import hashlib
import csv
from tempfile import NamedTemporaryFile

from tqdm import tqdm
import requests
from PyQt5.QtWidgets import QMessageBox

from Source import PACKAGE_DIR as dirPath
from Source.ConfigFile import ConfigFile
from Source.MainConfig import MainConfig
import Source.utils.loggingHCP as logging


def _download_zhang_file(destination, url, expected_hash):
    """Stream and verify a Zhang file without requiring a Content-Length header."""
    temporary_path = None
    try:
        with requests.Session() as session:
            with session.get(url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                try:
                    file_size = int(response.headers.get("Content-Length", ""))
                    if file_size < 0:
                        file_size = None
                except (TypeError, ValueError):
                    file_size = None
                filename = os.path.basename(destination)
                if file_size is None:
                    print(f"##### Downloading {filename} (size unavailable) #####")
                else:
                    print(f"##### Downloading {filename} ({file_size / (1024**3):.2f} GB) #####")

                # Publish only a complete, verified file. Failed transfers must not
                # overwrite an existing database or look like a successful download.
                directory = os.path.dirname(os.path.abspath(destination))
                with NamedTemporaryFile(mode="wb", dir=directory, prefix=".zhang-",
                                        suffix=".part", delete=False) as target:
                    temporary_path = target.name
                    with tqdm(total=file_size, unit="iB", unit_scale=True,
                              unit_divisor=1024) as progress:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                target.write(chunk)
                                progress.update(len(chunk))

        print("Checking file...")
        if md5(temporary_path) != expected_hash:
            raise ValueError(f"Checksum mismatch for {destination}")
        os.replace(temporary_path, destination)
        temporary_path = None
        print("File checks out.")
    except (requests.exceptions.RequestException, OSError, ValueError) as err:
        print("Failed to download core database:", err)
        print(
            f"Try download from {url} (e.g. copy paste this URL in your internet browser) and place under"
            f" {dirPath}/Data directory."
        )
    finally:
        if temporary_path is not None:
            try:
                os.remove(temporary_path)
            except OSError as err:
                print("Unable to remove incomplete download:", err)


def downloadZhangLUT(fpfZhangLUT, force=False):
    infoText = "  NEW INSTALLATION\nGlint LUTs required.\nClick OK to download.\n\nThis comprises two 200 MB files.\n\n\
    If canceled, Zhang et al. (2017) glint correction will revert to slower analytical solution. If download fails, a link and instructions will be provided in the terminal."
    YNReply = True if force else YNWindow("Database Download", infoText) == QMessageBox.Ok
    lut_name = os.path.basename(fpfZhangLUT)
    expected_hash = {
        'Z17_LUT_30.nc': '988cc08446dd00d689280397f2faa672',
        'Z17_LUT_40.nc': 'd9197436125f97c3bd8f00c6ee0185be',
    }
    if YNReply:
        url = f"https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/{lut_name}"
        _download_zhang_file(fpfZhangLUT, url, expected_hash[lut_name])

def downloadZhangDB(fpfZhang, force=False):
    infoText = "  NEW INSTALLATION\nGlint database required.\nClick OK to download.\n\nWARNING: THIS IS A 2.8 GB DOWNLOAD.\n\n\
    If canceled, Zhang et al. (2017) glint correction will fail. If download fails, a link and instructions will be provided in the terminal."
    YNReply = True if force else YNWindow("Database Download", infoText) == QMessageBox.Ok
    if YNReply:

        url = "https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Zhang_rho_db_expanded.mat"
        _download_zhang_file(fpfZhang, url, "e4c155f8ce92dcfa012a450a56b64e28")

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

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def checkInputFiles(inFilePath, level="L1A+"):
    if ConfigFile.settings['SensorType'].lower() in ["trios", "trios es only"]:
        flag_Trios = True
    else:
        flag_Trios = False
    if flag_Trios and level == "L1A":
        for fp in inFilePath:
            if not os.path.isfile(fp):
                msg = f'No such L1A TriOS file ... {fp}'
                if not MainConfig.settings['popQuery']:
                    logging.errorWindow("File Error", msg)
                logging.writeLogFileAndPrint(msg)
                return False
            else:
                return True
    else:
        if not os.path.isfile(inFilePath):
            msg = f'No such L1A non-TriOS file ... {inFilePath}'
            if not MainConfig.settings['popQuery']:
                logging.errorWindow("File Error", msg)
            print(msg)
            logging.writeLogFile(msg)
            return False
        else:
            return True

def checkOutputFiles(outFilePath):
    if os.path.isfile(outFilePath):
        modTime = os.path.getmtime(outFilePath)
        nowTime = datetime.now()
        if nowTime.timestamp() - modTime < 60: # If the file exists and was created in the last minute...
            # logging.writeLogFileAndPrint(f'{level} file produced: \n {outFilePath}'
            # print(msg)
            # logging.writeLogFile(msg)
            logging.writeLogFileAndPrint(f'Process Single Level: {outFilePath} - SUCCESSFUL')
        else:
            logging.writeLogFileAndPrint(f'Process Single Level: {outFilePath} - NOT SUCCESSFUL')
    else:
        logging.writeLogFileAndPrint(f'Process Single Level: {outFilePath} - NOT SUCCESSFUL')

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

def parseLine_no_index(line: str, ds) -> None:
    for i, x in enumerate(line.split('\t')):
        if x:
            if str(i) not in ds.columns.keys():
                ds.columns[str(i)] = []
            try:
                ds.columns[str(i)].append(float(x))
            except ValueError:
                ds.columns[str(i)].append(x)

def read_char(filepath: str, gp) -> None:
    ''' Used by 
            ProcessL1b.read_unc_coefficient_factory
            ProcessL1b.read_FidRadDB_cal_char_files
            ProcessL1b.read_unc_coefficient_class
            ProcessL1b.read_unc_coefficient_frm
        to read in FidRadDB files.
        '''
    begin_data = False  # set up data flag
    attrs = {}
    end_count = 0
    Azimuth_angle = None
    solar_zen_range = None

    with open(filepath, 'r', encoding="utf-8") as f:  # open file
        key, ds, name = None, None, None
        while True:  # start loop
            line = getline(f, '\n')  # reads the file until a '\n' character is reached
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
                        parseLine_no_index(line, ds)  # add the data
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
                            elif 'SOLAR_ZENITH_ANGLE_RANGE' in attrs:
                                ds = gp.addDataset(f"{name}_{attrs['DATA_TYPE']}_RANGE{attrs['SOLAR_ZENITH_ANGLE_RANGE']}")
                                solar_zen_range = attrs['SOLAR_ZENITH_ANGLE_RANGE']
                            elif Azimuth_angle is not None:  # uncertainty also repeated so save the az angle from earlier to use here
                                ds = gp.addDataset(f"{name}_{attrs['DATA_TYPE']}_AZ{Azimuth_angle}")
                                Azimuth_angle = None
                            elif solar_zen_range is not None:
                                ds = gp.addDataset(f"{name}_{attrs['DATA_TYPE']}_RANGE{solar_zen_range}")
                                solar_zen_range = None
                            else:
                                logging.writeLogFileAndPrint(f"Dataset could not be constructed. Utilties.read_char(file-path, HDFGroup) in {gp.attributes['CHARACTERISATION_FILE_TYPE']}")
                                raise KeyError  # TODO: write custom exception for this case, with description of how to fix (SZA_range or AZ ang not in char file)
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
