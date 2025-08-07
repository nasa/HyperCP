    
'''
################################# FILE AND DOWNLOAD ORIENTED #################################
'''
import os
from datetime import datetime
import hashlib

from tqdm import tqdm
import requests
from PyQt5.QtWidgets import QMessageBox

# from Source.Utilities import Utilities
from Source import PACKAGE_DIR as dirPath
from Source.ConfigFile import ConfigFile
from Source.MainConfig import MainConfig
from Source.Utilities import Utilities

# @staticmethod
def downloadZhangLUT(fpfZhangLUT, force=False):
    infoText = "  NEW INSTALLATION\nGlint LUTs required.\nClick OK to download.\n\nThis comprisese two 200 MB files.\n\n\
    If canceled, Zhang et al. (2017) glint correction will revert to slower analytical solution. If download fails, a link and instructions will be provided in the terminal."
    YNReply = True if force else YNWindow("Database Download", infoText) == QMessageBox.Ok
    if YNReply:

        url = "https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Z17_LUT_40.nc"
        download_session = requests.Session()
        try:
            file_size = int(
                download_session.head(url).headers["Content-length"]
            ) # If this fails, check the file permissions on the server.
            file_size_read = round(int(file_size) / (1024**3), 2)
            print(
                f"##### Downloading {file_size_read}GB data file. ##### "
            )
            download_file = download_session.get(url, stream=True)
            download_file.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print("Error in download_file:", err)
        if download_file.ok:
            progress_bar = tqdm(
                total=file_size, unit="iB", unit_scale=True, unit_divisor=1024
            )
            with open(fpfZhangLUT, "wb") as f:
                for chunk in download_file.iter_content(chunk_size=1024):
                    progress_bar.update(len(chunk))
                    f.write(chunk)
            progress_bar.close()

            # Check the hash of the file
            print('Checking file...')
            thisHash = md5(fpfZhangLUT)
            if thisHash == '1a33ed647d9c7359b0800915bd0229c7':
                print('File checks out.')
            else:
                print(f'Error in downloaded file {fpfZhangLUT}. Recommend you delete the downloaded file and try again.')
                print(
                f"Try download from {url} (e.g. copy paste this URL in your internet browser) and place under"
                f" {dirPath}/Data directory."
            )
        else:
            print(
                "Failed to download core databases."
                f"Try download from {url} (e.g. copy paste this URL in your internet browser) and place under"
                f" {dirPath}/Data directory."
            )

# @staticmethod
def downloadZhangDB(fpfZhang, force=False):
    infoText = "  NEW INSTALLATION\nGlint database required.\nClick OK to download.\n\nWARNING: THIS IS A 2.8 GB DOWNLOAD.\n\n\
    If canceled, Zhang et al. (2017) glint correction will fail. If download fails, a link and instructions will be provided in the terminal."
    YNReply = True if force else YNWindow("Database Download", infoText) == QMessageBox.Ok
    if YNReply:

        url = "https://oceancolor.gsfc.nasa.gov/fileshare/dirk_aurin/Zhang_rho_db_expanded.mat"
        download_session = requests.Session()
        try:
            file_size = int(
                download_session.head(url).headers["Content-length"]
            )# If this fails, check the file permissions on the server.
            file_size_read = round(int(file_size) / (1024**3), 2)
            print(
                f"##### Downloading {file_size_read}GB data file. This could take several minutes. ##### "
            )
            download_file = download_session.get(url, stream=True)
            download_file.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print("Error in download_file:", err)
        if download_file.ok:
            progress_bar = tqdm(
                total=file_size, unit="iB", unit_scale=True, unit_divisor=1024
            )
            with open(fpfZhang, "wb") as f:
                for chunk in download_file.iter_content(chunk_size=1024):
                    progress_bar.update(len(chunk))
                    f.write(chunk)
            progress_bar.close()

            # Check the hash of the file
            print('Checking file...')
            thisHash = md5(fpfZhang)
            if thisHash == 'e4c155f8ce92dcfa012a450a56b64e28':
                print('File checks out.')
            else:
                print(f'Error in downloaded file {fpfZhang}. Recommend you delete the downloaded file and try again.')
                print(
                f"Try download from {url} (e.g. copy paste this URL in your internet browser) and place under"
                f" {dirPath}/Data directory."
            )

        else:
            print(
                "Failed to download core databases."
                f"Try download from {url} (e.g. copy paste this URL in your internet browser) and place under"
                f" {dirPath}/Data directory."
            )

# @staticmethod
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

# @staticmethod
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# @staticmethod
def checkInputFiles(inFilePath, level="L1A+"):
    if ConfigFile.settings['SensorType'].lower() == 'trios':
        flag_Trios = True
    else:
        flag_Trios = False
    if flag_Trios and level == "L1A":
        for fp in inFilePath:
            if not os.path.isfile(fp):
                msg = f'No such L1A TriOS file ... {fp}'
                if not MainConfig.settings['popQuery']:
                    Utilities.errorWindow("File Error", msg)
                Utilities.writeLogFileAndPrint(msg)
                return False
            else:
                return True
    else:
        if not os.path.isfile(inFilePath):
            msg = f'No such L1A non-TriOS file ... {inFilePath}'
            if not MainConfig.settings['popQuery']:
                Utilities.errorWindow("File Error", msg)
            print(msg)
            Utilities.writeLogFile(msg)
            return False
        else:
            return True

# @staticmethod
def checkOutputFiles(outFilePath):
    if os.path.isfile(outFilePath):
        modTime = os.path.getmtime(outFilePath)
        nowTime = datetime.now()
        if nowTime.timestamp() - modTime < 60: # If the file exists and was created in the last minute...
            # Utilities.writeLogFileAndPrint(f'{level} file produced: \n {outFilePath}'
            # print(msg)
            # Utilities.writeLogFile(msg)
            Utilities.writeLogFileAndPrint(f'Process Single Level: {outFilePath} - SUCCESSFUL')
        else:
            Utilities.writeLogFileAndPrint(f'Process Single Level: {outFilePath} - NOT SUCCESSFUL')
    else:
        Utilities.writeLogFileAndPrint(f'Process Single Level: {outFilePath} - NOT SUCCESSFUL')