
import collections
import sys
import h5py
import numpy as np

from Source.HDFDataset import HDFDataset

class HDFGroup:
    def __init__(self):
        self.id = ""
        self.datasets = collections.OrderedDict()
        self.attributes = collections.OrderedDict()

    def copy(self, gp):
        self.copyAttributes(gp)
        for k, ds in gp.datasets.items():
            newDS = self.addDataset(ds.id)
            newDS.copy(ds)

    def copyAttributes(self, gp):
        for k,v in gp.attributes.items():
            self.attributes[k] = v

    def datasetDeleteRow(self, i):  
        for k in self.datasets:
            # Avoid non-temporal datasets. Should cover TriOS and DALEC
            skipList = ['back_es','cal_es','back_li','cal_li','back_lt','cal_lt','capsontemp']
            if k.lower() not in skipList:
                ds = self.datasets[k]
                ds.data = np.delete(ds.data, (i), axis=0)

    def removeDataset(self, name):
        if len(name) == 0:
            print("Name is 0")
            return False
        ds = self.getDataset(name)
        if ds is not None:
            del self.datasets[name]
            return True
        else:
            print("dataset does not exist")
            return False

    def addDataset(self, name):
        if len(name) == 0:
            print("Name is 0")
            exit(1)
        ds = None
        if not self.getDataset(name):
            ds = HDFDataset()
            ds.id = name
            self.datasets[name] = ds
        return ds

    def getDataset(self, name):
        if name in self.datasets:
            return self.datasets[name]
        return None

    def getTableHeader(self, name):
        ''' Generates Head attributes'''
        # ToDo: This should get generated from context file instead
        if name != "None":
            cnt = 1
            ds = self.getDataset(name)
            if ds is None:
                ds = self.addDataset(name)
            for item in ds.columns:
                self.attributes["Head_"+str(cnt)] = name + " 1 1 " + item
                cnt += 1

    def printd(self):
        print("Group:", self.id)
        #print("Sensor Type:", self.sensorType)

        if "FrameType" in self.attributes:
            print("Frame Type:", self.attributes["FrameType"])
        else:
            print("Frame Type not found")

        for k in self.attributes:
            print("Attribute:", k, self.attributes[k])
        #    attr.printd()
        #for gp in self.groups:
        #    gp.printd()
        for k in self.datasets:
            ds = self.datasets[k]
            ds.printd()

    def read(self, f):
        name = f.name[f.name.rfind("/")+1:]
        self.id = name

        # Read attributes
        #print("Attributes:", [k for k in f.attrs.keys()])
        for k in f.attrs.keys():
            if type(f.attrs[k]) == np.ndarray:  # noqa: E721
                self.attributes[k] = f.attrs[k]
            else: # string attribute
                self.attributes[k] = f.attrs[k].decode("utf-8")
        # Read datasets
        for k in f.keys():
            item = f.get(k)
            if isinstance(item, h5py.Group):
                print("HDFGroup should not contain groups")
            elif isinstance(item, h5py.Dataset):
                #print("Item:", k)
                ds = HDFDataset()
                self.datasets[k] = ds
                ds.read(item)

    def write(self, f):
        #print("Group:", self.id)
        try:
            f = f.create_group(self.id)
            # Write attributes
            for k in self.attributes:
                f.attrs[k] = np.string_(self.attributes[k])
            # Write datasets
            for key,ds in self.datasets.items():
                #f.create_dataset(ds.id, data=np.asarray(ds.data))
                ds.write(f)
        except:
            e = sys.exc_info()[0]
            print(e)
