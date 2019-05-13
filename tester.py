# Test script

import collections
import HDFRoot

class PDF:
    def __init__(self):
        self.id = ""
        self.groups = []
        self.attributes = collections.OrderedDict()

    
    @staticmethod
    def readHDF5(fp):
        root = HDFRoot()


root2 = HDFRoot()
# root2 = HDFRoot.HDFRoot()
print(root2.attributes)
print(type(root2))

root = PDF()
print(root.attributes)
print(root.groups)
