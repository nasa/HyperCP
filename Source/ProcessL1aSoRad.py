'''Process Raw (L0) data to L1A HDF5'''

from Source.HDFRoot import HDFRoot
class ProcessL1aSoRad:
    '''Process L1A SoRad. 
    
    For now, ProcessL1a So-rad, is a function that reads pre-formatted L1A hdf file.

    Currently developed for the "L1A" version of raw HDF data from Tom (presumably mimicking geoserver conversion), 
    and not yet "L0" HDF data directly off the So-Rad.
        
    '''
    # TODO: Test on L0 HDF data 
    
    @staticmethod
    def processL1a(input_path, output_path, calibrationMap):
        root = HDFRoot.readHDF5(input_path)
        print('Reading hdf file' + str(input_path))

        # Test for the erroneous sorad group attribute in Tom's raw HDF
        for gp in root.groups:
            if gp.id == 'sorad':
                if gp.attributes['CalFileName'] == 'sorad.tdf':
                    gp.attributes['CalFileName'] = 'sorad'

        return root, output_path
