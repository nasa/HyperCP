
import collections
import h5py
import numpy as np

from Source.HDFGroup import HDFGroup
from Source.HDFDataset import HDFDataset

class HDFRoot:
    def __init__(self):
        self.id = ""
        self.groups = []
        self.datasets = []
        self.attributes = collections.OrderedDict()

    def copy(self, node):
        self.copyAttributes(node)
        for gp in node.groups:
            newGP = self.addGroup(gp.id)
            newGP.copy(gp)

    def copyAttributes(self, node):
        for k,v in node.attributes.items():
            self.attributes[k] = v

    def addGroup(self, name):
        gp = self.getGroup(name)
        if not gp:
            gp = HDFGroup()
            gp.id = name
            self.groups.append(gp)
        return gp

    def getGroup(self, name):
        for gp in self.groups:
            if gp.id == name:
                return gp
        return None

    def removeGroup(self, name):
        gp = name
        if gp:
            self.groups.remove(gp)

    def getDataset(self, name):
        if name in self.datasets:
            return self.datasets[name]
        return None

    def printd(self):
        print("Root:", self.id)
        #print("Processing Level:", self.processingLevel)
        #for k in self.attributes:
        #    print("Attribute:", k, self.attributes[k])
        for gp in self.groups:
            gp.printd()

    @staticmethod
    def readHDF5(fp):
        root = HDFRoot()
        with h5py.File(fp, "r") as f:

            # set name to text after last '/'
            name = f.name[f.name.rfind("/")+1:]
            if len(name) == 0:
                name = "/"
            root.id = name

            # Read attributes
            #print("Attributes:", [k for k in f.attrs.keys()])
            for k in f.attrs.keys():
                # Need to check values for non-character encoding
                value = f.attrs[k]
                if value.__class__ is np.ndarray:
                    root.attributes[k] = value
                else:
                    root.attributes[k] = f.attrs[k].decode("utf-8")
                # Use the following when using h5toh4 converter:
                #root.attributes[k.replace("__GLOSDS", "")] = f.attrs[k].decode("utf-8")
            # Read groups
            for k in f.keys():
                item = f.get(k)
                #print(item)
                if isinstance(item, h5py.Group):
                    gp = HDFGroup()
                    root.groups.append(gp)
                    gp.read(item)
                elif isinstance(item, h5py.Dataset):
                    # print("HDFRoot should not contain datasets")
                    ds = HDFDataset()
                    root.datasets.append(ds)
                    ds.read(item)

        return root

    # Writing to HDF5 file
    def writeHDF5(self, fp):
        with h5py.File(fp, "w") as f:
            #print("Root:", self.id)
            # Write attributes
            for k in self.attributes:
                f.attrs[k] = np.string_(self.attributes[k])
                # h5toh4 converter requires "__GLOSDS" to be appended
                # to attribute name for it to be recognized correctly:
                #f.attrs[k+"__GLOSDS"] = np.string_(self.attributes[k])
            # Write groups
            for gp in self.groups:
                gp.write(f)
