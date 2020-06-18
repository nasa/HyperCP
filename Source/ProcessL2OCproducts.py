
import numpy as np
from ConfigFile import ConfigFile

from L2chlor_a import L2chlor_a


class ProcessL2OCproducts():
    
    @staticmethod
    def procProds(root):

        # chlor_a
        if ConfigFile.products["bL2Prodoc3m"]:
            L2chlor_a(root)
