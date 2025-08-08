'''Process Raw (L0) data to L1A HDF5'''

from Source.HDFRoot import HDFRoot
class ProcessL1aSoRad:
    '''Process L1A SoRad. 
    
    For now, ProcessL1a So-rad, is a function that reads pre-formatted L1A hdf file
    
    In the future, I think/hope we can re-design this function so that it is parsed data
    directly from the So-Rad database
        
    '''
    @staticmethod
    def processL1a(input_path, output_path, calibrationMap):
        root = HDFRoot.readHDF5(input_path)
        print('Reading hdf file' + str(input_path))

        return root, output_path
