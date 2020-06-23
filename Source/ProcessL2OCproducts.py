
import numpy as np

from ConfigFile import ConfigFile
from Utilities import Utilities
from L2chlor_a import L2chlor_a
from L2kd490 import L2kd490
from L2pic import L2pic
from L2poc import L2poc
# from L2par import L2par
from L2ipar import L2ipar
from L2avw import L2avw
from L2qaa import L2qaa


class ProcessL2OCproducts():
    ''' Product algorithms can be found at https://oceancolor.gsfc.nasa.gov/atbd/ '''
    
    @staticmethod
    def procProds(root):

        if not root.getGroup("DERIVED_PRODUCTS"):
            root.addGroup("DERIVED_PRODUCTS")

        # chlor_a
        if ConfigFile.products["bL2Prodoc3m"]:
            msg = "Processing chlor_a"
            print(msg)
            Utilities.writeLogFile(msg)  
            L2chlor_a.L2chlor_a(root)

        # kd490
        if ConfigFile.products["bL2Prodkd490"]:
            msg = "Processing kd490"
            print(msg)
            Utilities.writeLogFile(msg)  
            L2kd490.L2kd490(root)

        # pic
        if ConfigFile.products["bL2Prodpic"]:
            msg = "Processing pic"
            print(msg)
            Utilities.writeLogFile(msg)  
            L2pic.L2pic(root)

        # poc
        if ConfigFile.products["bL2Prodpoc"]:
            msg = "Processing poc"
            print(msg)
            Utilities.writeLogFile(msg)  
            L2poc.L2poc(root)

        # # par
        # if ConfigFile.products["bL2Prodpar"]:
        #     L2par.L2par(root)

        # ipar
        if ConfigFile.products["bL2Prodipar"]:
            msg = "Processing ipar"
            print(msg)
            Utilities.writeLogFile(msg)  
            L2ipar.L2ipar(root)

        # avw
        # Vandermuelen et al. 2020
        if ConfigFile.products["bL2Prodavw"]:
            msg = "Processing avw"
            print(msg)
            Utilities.writeLogFile(msg)  
            L2avw.L2avw(root)

        # GIOP



        # QAA
        ''' Is there a hyperspectral parameterization of the QAA? I see
            Guoqing Wang and Ping worked on a related poster in 2014... '''

        ''' ToDo: In the future, this should have inputs to apply IOP 
            parameters from ancillary file:

            eta: powerlaw slope of bbp
            zeta: ap(411)/aph(443)
            xi: adg(411)/aph(443) 
            
            Also, empirical parameters could be set.
            For now, structure this as QAAv6 for MODIS bands'''

        if ConfigFile.products["bL2Prodqaa"]:
            msg = "Processing qaa"
            print(msg)
            Utilities.writeLogFile(msg)  
            L2qaa.L2qaa(root)






