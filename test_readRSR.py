
import numpy as np

modisRSRFile = 'Data/HMODISA_RSRs.txt'
data = np.loadtxt(modisRSRFile, skiprows=7)
wavelength = data[:,0]
rsr = data[...,1:]

print(data)