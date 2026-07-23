'''Process Raw (L0) data to L1A HDF5'''
import numpy as np
import json
import logging 
import os

from Source.HDFRoot import HDFRoot
from Source.ProcessL1aTriOS import ProcessL1aTriOS
from Source.MainConfig import MainConfig
import Source.utils.filing as filing

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
    
        # Test for the erroneous sorad group attribute in Tom's raw HDF (and erroneous group name in NASA L0 HDF) 
        # TJ - I think this loop will be removed later on (it is useful for testing/data cleaning for now)
        for gp in root.groups:
            if gp.id == 'SAM_5129.ini': # tempoary fix for nasa group name
               gp.id = 'SAM_8727.ini'
            elif gp.id == 'sorad':
                try: # old L1A (with `legacy' tdf label)
                    if gp.attributes['CalFileName'] == 'sorad.tdf': 
                        gp.attributes['CalFileName'] = 'sorad'
                except: # NASA system L1 0 (where CalFileName does not exist)
                    gp.attributes['CalFileName'] = 'sorad'

        # Add wavelength coeffs and calibrations to each sensor group
        # This uses sections of the `formatting_instrument' function in ProcesssL1aTriOs
        for gp in root.groups:
            
            # re-define TIMETAG2 and DATETAG as integers (they are non-integers in So-Rad L0HDF)      
            gp.datasets["TIMETAG2"].data = np.array((gp.datasets["TIMETAG2"].data)*1000, dtype=[('NONE', '<f8')])
            gp.datasets["DATETAG"].data = np.array((gp.datasets["DATETAG"].data).astype(int), dtype=[('NONE', '<f8')])

            if gp.id.split('_')[0] == 'SAM': # selects sensor group to appemnd cal info
            
                # assign `sensor_id', `sensor' and `name' labels used in ProcesssL1aTriOS
                sensor_id = gp.id  # e.g. 'SAM_8729.ini'   
                
                with open(configPath, 'r', encoding="utf-8") as fc:
                    text = fc.read()
                    conf_json = json.loads(text)
                sensor = conf_json['CalibrationFiles'][sensor_id]['frameType']  # e.g. LT
                
                name  = (sensor_id.split('_')[1]).split('.')[0]   # e.g. '8729'
                
                # add name as attributes
                gp.attributes['CalFileName'] = 'SAM_' + name + '.ini'
             

                #gpsGroup.addDataset("DATETAG")
                #gpsGroup.datasets["DATETAG"].data = np.array(dateTag.data, dtype=[('NONE', '<f8')])
                
                # Append wavelength coeffs (c0,c1,c2,c3) from ini file
                ProcessL1aTriOS.attr_ini(cal_path + sensor_id, gp)

                # Derive wavelengths - see L478 in ProcessL1aTriOS
                c0 = float(gp.attributes['c0s'])
                c1 = float(gp.attributes['c1s'])
                c2 = float(gp.attributes['c2s'])
                c3 = float(gp.attributes['c3s'])
                wl = []
                for i in range(1,256): # 
                    wl.append(str(round((c0 + c1*(i+1) + c2*(i+1)**2 + c3*(i+1)**3), 2)))
   
                # Create new L0 dataset as either ES, LT, LI with 255 pixels as default - see line 490 in Proccess L1A TriOS
                ds_dt = np.dtype({'names': wl,'formats': [np.float64]*len(wl)}) # 255 wl pixels
                my_arr = gp.datasets['L0'].data[:,0:-1].T # reduces to 255 pixels (there are currently 256 pixels in So-Rad L0HDF)
                rec_arr = np.rec.fromarrays(my_arr, dtype=ds_dt)
                gp.addDataset(sensor)
                gp.datasets[sensor].data = np.array(rec_arr.T, dtype=ds_dt)
                del gp.datasets['L0'] # remove old L0 group from So-Rad L0 HDF
                
                # Add callibration/back data. Line 504 onwards in ProcessL1aTriOS
                metacal,cal = ProcessL1aTriOS.read_cal(cal_path + 'Cal_SAM_' + name + '.dat') 
                if metacal is None:
                    logging.writeLogFileAndPrint("Error reading calibration file")
                    return None,None
                B1 = gp.addDataset('CAL_' + sensor)
                B1.columns["0"] = cal.values[:,1].astype(np.float64)
                B1.columnsToDataset()
                ProcessL1aTriOS.get_attr(metacal,B1)
                
                metaback,back = ProcessL1aTriOS.read_cal(cal_path + 'Back_SAM_'+ name + '.dat')
                if metacal is None:
                    logging.writeLogFileAndPrint("Error reading calibration file")
                    return None,None
                # C1 = gp.addDataset('BACK_'+ sensor,data=back[[1,2]].astype(np.float64))
                C1 = gp.addDataset('BACK_' + sensor)
                C1.columns["0"] = back.values[:,1]
                C1.columns["1"] = back.values[:,2]
                C1.columnsToDataset()
                ProcessL1aTriOS.get_attr(metaback,C1)
             
                # breakpoint()
                file_name = input_path.split('/')[-1][:-6]
                outFFP = []
                outFFP.append(os.path.join(output_path, f'{file_name}_L1A.hdf'))
                root.attributes["L1A_FILENAME"] = outFFP[-1]
                filing.checkOutputFiles(outFFP[-1])


        return root, output_path