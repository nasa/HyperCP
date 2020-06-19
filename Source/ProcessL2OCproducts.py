
import numpy as np
from ConfigFile import ConfigFile

from L2chlor_a import L2chlor_a
from L2kd490 import L2kd490
from L2pic import L2pic
from L2poc import L2poc
# from L2par import L2par
from L2ipar import L2ipar


class ProcessL2OCproducts():
    ''' Product algorithms can be found at https://oceancolor.gsfc.nasa.gov/atbd/ '''
    
    @staticmethod
    def procProds(root):

        if not root.getGroup("DERIVED_PRODUCTS"):
            root.addGroup("DERIVED_PRODUCTS")

        # chlor_a
        if ConfigFile.products["bL2Prodoc3m"]:
            L2chlor_a.L2chlor_a(root)

        # kd490
        if ConfigFile.products["bL2Prodkd490"]:
            L2kd490.L2kd490(root)

        # pic
        if ConfigFile.products["bL2Prodpic"]:
            L2pic.L2pic(root)

        # poc
        if ConfigFile.products["bL2Prodpoc"]:
            L2poc.L2poc(root)

        # # par
        # if ConfigFile.products["bL2Prodpar"]:
        #     L2par.L2par(root)

        # ipar
        if ConfigFile.products["bL2Prodipar"]:
            L2ipar.L2ipar(root)
