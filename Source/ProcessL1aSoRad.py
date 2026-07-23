'''Process Raw (L0) data to L1A HDF5'''
import numpy as np
import json
import logging 

from Source.HDFRoot import HDFRoot
from Source.ProcessL1aTriOS import ProcessL1aTriOS
from Source.MainConfig import MainConfig

class ProcessL1aSoRad:
    '''Process L1A SoRad. 
    
    For now, ProcessL1a So-rad, is a function that reads pre-formatted L1A hdf file.

    Currently developed for the "L1A" version of raw HDF data from Tom (presumably mimicking geoserver conversion), 
    and not yet "L0" HDF data directly off the So-Rad.
        
    '''
    # TODO: Test on L0 HDF data 
    
    # @staticmethod -  old `L1A'
    # def processL1a(input_path, output_path, calibrationMap):
        
    #   root = HDFRoot.readHDF5(input_path)
    #  print('Reading hdf file' + str(input_path))

        # Test for the erroneous sorad group attribute in Tom's raw HDF
    #   for gp in root.groups:
    #      if gp.id == 'sorad':
    #         if gp.attributes['CalFileName'] == 'sorad.tdf':
    #            gp.attributes['CalFileName'] = 'sorad'

    # return root, output_path
        
    def processL1a(input_path, output_path, calibrationMap):
  
        root = HDFRoot.readHDF5(input_path)
        print('Reading hdf file' + str(input_path))
        
        # Line 24 in ProcessL1aTriOS)
        configPath = MainConfig.settings['cfgPath']
        cal_path = configPath[0:configPath.rfind('.')] + '_Calibration/'
    
        # Test for the erroneous sorad group attribute in Tom's raw HDF 
        # TJ - I think this will be removed later on (it is useful for testing agaisnt `old L1A' for now)
        for gp in root.groups:
            if gp.id == 'sorad':
                try: # old L1A (with `legacy' tdf label)
                    if gp.attributes['CalFileName'] == 'sorad.tdf': 
                        gp.attributes['CalFileName'] = 'sorad'
                except: # NASA system L1 0 (where CalFileName does not exist)
                    gp.attributes['CalFileName'] = 'sorad'
         
        # Add wavelength coeffs and calibrations to each sensor group
        # This uses sections of the `formatting_instrument' function in ProcesssL1aTriOs
        for gp in root.groups:
            if (gp.id != 'sorad'):
                if (gp.id != 'SAM_5129.ini'): # temporary catch
                    
                    # assign `sensor_id', `sensor' and `name' labels used in ProcesssL1aTriOS
                    sensor_id = gp.id  # e.g. 'SAM_8729.ini'
                    
                    with open(configPath, 'r', encoding="utf-8") as fc:
                        text = fc.read()
                        conf_json = json.loads(text)
                    sensor = conf_json['CalibrationFiles'][sensor_id]['frameType']   # e.g. LT
                    
                    name  = (sensor_id.split('_')[1]).split('.')[0]   # e.g. '8729'
                 
                    # Append wavelength coeffs (c0,c1,c2,c3) from ini file
                    ProcessL1aTriOS.attr_ini(cal_path + sensor_id, gp)

                    # Derive wavelengths - see L478 in ProcessL1aTriOS
                    c0 = float(gp.attributes['c0s'])
                    c1 = float(gp.attributes['c1s'])
                    c2 = float(gp.attributes['c2s'])
                    c3 = float(gp.attributes['c3s'])
                    wl = []
                    for i in range(1,256):
                        wl.append(str(round((c0 + c1*(i+1) + c2*(i+1)**2 + c3*(i+1)**3), 2)))
   
                    # Add callibration data - Line 504 in ProcessL1aTriOS
                    metacal,cal = ProcessL1aTriOS.read_cal(cal_path + 'Cal_SAM_'+ name +'.dat') 
                    if metacal is None:
                        logging.writeLogFileAndPrint("Error reading calibration file")
                        return None,None
                    B1 = gp.addDataset('CAL_'+ sensor)
                    B1.columns["0"] = cal.values[:,1].astype(np.float64)
                    B1.columnsToDataset()
                    ProcessL1aTriOS.get_attr(metacal,B1)
                    
                    metaback,back = ProcessL1aTriOS.read_cal(cal_path + 'Back_SAM_'+ name +'.dat')
                    if metacal is None:
                        logging.writeLogFileAndPrint("Error reading calibration file")
                        return None,None
                    # C1 = gp.addDataset('BACK_'+sensor,data=back[[1,2]].astype(np.float64))
                    C1 = gp.addDataset('BACK_'+ sensor)
                    C1.columns["0"] = back.values[:,1]
                    C1.columns["1"] = back.values[:,2]
                    C1.columnsToDataset()
                    ProcessL1aTriOS.get_attr(metaback,C1)
                    
        breakpoint()
        return root, output_path