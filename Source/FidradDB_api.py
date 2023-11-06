# from fidraddb_api.ocdb.api.OCDBApi import new_api, OCDBApi
from ocdb.api.OCDBApi import new_api, OCDBApi

def FidradDB_api(elem, date, cal_path):
    
    #api server_url configuration
    api = new_api(server_url='https://ocdb.eumetsat.int')

    #FidradDB connection and listening of all files for input instrument (serial number + type)
    list = OCDBApi.fidrad_list_files(api,elem)
    
    #Listening of the date versioning of filtered calibration files
    date_list = [eval(i.split('_')[-1].split('.')[0]) for i in list] 

    #Selection of the closest calibration data file to the measuring date
    closest_date = min(date_list, key=lambda x:abs(x-int(date)))
    
    #Selection of the corresponding calibration file
    matching = [s for s in list if str(closest_date) in s]

    # Download from FidRadDB of the selected file
    OCDBApi.fidrad_download_file(api, matching[0], cal_path)
 

    return None
