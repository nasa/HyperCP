import numpy as np
import matplotlib.pyplot as plt
from Source.PIU.PIUDataStore import PIUDataStore as pds

from Source.PIU.HyperOCR import HyperOCR
from Source.PIU.TriOS import TriOS
from Source.PIU.DALEC import Dalec


class Plotting:
    def __init__(self):
        pass

    @staticmethod
    def plot(sensor, name, x, mag1, mag2, lab1, lab2, ylab, xlab='Wavelength (nm)', xlim=[320, 800], ylim=[None, None], diff=False):
        plt.figure(f"{sensor}_{name}")
        if not diff:
            plt.title(f"{sensor} {name}")
            sp = f"{sensor}_{name}.png"
            plt.plot(x, mag1, label=f"{sensor} {lab1}")
            plt.plot(x, mag2, label=f"{sensor} {lab2}")
        else:
            plt.title(f"divided difference {sensor} {name}")
            sp = f"{sensor}_{name}_diff.png"
            plt.plot(x, 100*((mag1/mag2)-1), label=f"{sensor} diff {lab1} {lab2}")

        plt.grid(axis='both')
        plt.ylim(*ylim)
        plt.xlim(*xlim)
        plt.xlabel(xlab)
        plt.ylabel(ylab)

        plt.legend()

        plt.savefig(sp)
        plt.close(f"{sensor}_{name}")
    
    def get_BD_FRM(self, PDS: pds, stats: dict, nWB: np.array) -> dict:
        """
        """

        if ConfigFile.settings['SensorType'].lower() == "seabird":
            inst = HyperOCR()
        elif ConfigFile.settings['SensorType'].lower() == "trios":
            inst = TriOS()
        else:
            inst = DALEC()

        # coefs = PDS.coeff.copy()
        uncs  = PDS.uncs.copy()
        self.reset(PDS)

        loop = {
            "NOISE":        {'ES': [], 'LI': [], 'LT': []},
            "NLINEARITY":   [],
            "STRAYLIGHT":   [],
            "CALIBRATION":  [],
            "STABILITY":    [],
            "TEMPERATURE":  [],
            "COSINE":       [],
            "POLARISATION": [],
        }
        UNCS = {}
        for label, indx in loop:
            for s in ['ES', 'LI', 'LT']:
                PDS.unc[s][indx[s]] = uncs[s][indx[s]]

            UNCS[label] = inst.FRM(PDS, stats, nWB)
            self.reset(PDS)

        
    @staticmethod
    def reset(PDS):
        PDS.uncs = {
            key: {k: np.zeros_like(v) for k, v in uncs[key].items()} for key in ['ES', 'LI', 'LT']
            }


