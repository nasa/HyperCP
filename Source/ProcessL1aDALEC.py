'''Process Raw (L0) data to L1A HDF5'''
import collections
import datetime as dt
import os
import numpy as np

from Source.HDFRoot import HDFRoot
from Source.HDFGroup import HDFGroup
from Source.MainConfig import MainConfig
from Source.Utilities import Utilities
from Source.RawFileReader import RawFileReader
from Source.ConfigFile import ConfigFile


class ProcessL1aDALEC:
    '''Process L1A'''
    @staticmethod
    def processL1a(fp, calibrationMap):
        print('This is a placeholder')
        return None, None