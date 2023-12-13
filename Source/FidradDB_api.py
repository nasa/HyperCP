# from fidraddb_api.ocdb.api.OCDBApi import new_api, OCDBApi
from ocdb.api.OCDBApi import new_api, OCDBApi
import numpy as np
import os

def FidradDB_choose_cal_char_file(elem, acq_time, cal_char_candidates):

    if len(cal_char_candidates) == 0:
        return

    # Listening of the date versioning of filtered calibration files
    fileTimeStamps = np.array([int(os.path.basename(i).split('_')[-1].split('.')[0]) for i in cal_char_candidates])

    cal_char_type = elem.split('_')[-1]

    if cal_char_type == 'RADCAL':
        # Selection of the closest calibration data file to the measuring date
        fileTimeStamp = min(fileTimeStamps, key=lambda x: abs(x - int(acq_time)))
    else:
        # Selection of the closest char data file PRE-EXISTING to the measuring date
        try:
            fileTimeStamp = np.max(fileTimeStamps[np.array(fileTimeStamps) < int(acq_time)])
        except:
            fileTimeStamp = min(fileTimeStamps, key=lambda x: abs(x - int(acq_time)))
    # Selection of the corresponding calibration file
    matching = [s for s in cal_char_candidates if str(fileTimeStamp) in os.path.basename(s)][0]

    return matching

def FidradDB_api(elem, acq_time, cal_path):
    
    #api server_url configuration
    api = new_api(server_url='https://ocdb.eumetsat.int')

    #FidradDB connection and listening of all files for input instrument (serial number + type)
    cal_char_candidates = OCDBApi.fidrad_list_files(api,elem)

    matching = FidradDB_choose_cal_char_file(elem, acq_time, cal_char_candidates)

    # Download from FidRadDB of the selected file
    OCDBApi.fidrad_download_file(api, matching, cal_path)
 

    return None
