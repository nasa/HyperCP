
import re
import numpy as np
import os

from HDFRoot import HDFRoot
from HDFGroup import HDFGroup
from HDFDataset import HDFDataset


def readLUT(node,filename, headerlines):
    """
    Read in the M99 LUT for 550 nm

    Required arguments:
    node        = HDF5 Root object
    filename    = name of SeaBASS input file (string)
    headerlines = # of headerlines in the LUT text file

    LUT is in self.groups[0].datasets['LUT'].data

    phiView is the relative azimuth angle, and phiSun is 180 - phiView

    """

    node.id = 'rhoLUT'
    node.attributes['LUT origin'] = filename.split(os.path.sep)[-1]
    node.attributes['Citation'] = 'Mobley, 1999, Appl Opt 38, page 7445, Eqn. 4'

    try:
        fileobj = open(filename,'r')
    except Exception as e:
        print(f'Unable to open file for reading: {filename}. Error: {e}')
        return

    try:
        lines = fileobj.readlines()
        fileobj.close()
    except Exception as e:
        print(f'Unable to read data from file: {filename}. Error: {e}')
        return

    # Create the dictionary LUT
    lut = {'wind':[],'sza':[],'theta':[],'phiSun':[],'phiView':[],'rho':[]}

    # Later, interpolate or find-nearest the field data to these steps to match...
    wind = []   # 0:2:14
    sza = []    # 0:10:80
    # I =[]       # 1:1:10
    # J = []      # 1:1:13
    theta = []  # 0:10:80, 87.5
    phiSun = [] # 0:15:180 # phi of 45 deg is relaz of 135 deg
    phiView = []# 0:15:180
    rho = []    # result

    for i, line in enumerate(lines):
        if i < headerlines:
            continue
        data_row = re.search("WIND SPEED =", line)
        data_row = re.search("THETA_SUN", line)

        if data_row:
            elems = re.findall('\d+\.\d+',line)
            continue

        linefloat = [float(elem) for elem in line.split()]
        wind.append(float(elems[0]))
        sza.append(float(elems[1]))
        theta.append(linefloat[2])
        phiSun.append(linefloat[3])
        phiView.append(linefloat[4])
        rho.append(linefloat[5])

    lut['wind'] = wind
    lut['sza'] = sza
    lut['theta'] = theta
    lut['phiSun'] = phiSun
    lut['phiView'] = phiView
    lut['rho'] = rho

    gp = HDFGroup()
    gp.id = 'LUT'
    node.groups.append(gp)

    LUTDataset = gp.addDataset("LUT")
    LUTDataset.columns = lut
    LUTDataset.columnsToDataset()

    return node


fpHySP = os.path.dirname(__file__).split(os.path.sep)
fpHySP[0] = os.path.sep
fpHySP[-1] = 'Data'
fpData = os.path.join(*fpHySP)
fp = os.path.join(fpData, 'rhoTable_AO1999.txt')
outfp = os.path.join(fpData, 'rhoTable_AO1999.hdf')
headerlines = 9
# dims = [13, 117, 6]
root = HDFRoot()
root = readLUT(root, fp, headerlines)

root.writeHDF5(outfp)







