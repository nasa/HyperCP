# from Source.PIU.PIUDataStore import PIUDataStore as pds

from Source.PIU.HyperOCR import HyperOCR
from Source.PIU.TriOS import TriOS
from Source.PIU.DALEC import DALEC


class Plotting:
    def __init__(self):
        pass


    def get_BD_FRM(self, PDS: PIUDataStore, stats: dict, nWB: np.array) -> dict:
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


