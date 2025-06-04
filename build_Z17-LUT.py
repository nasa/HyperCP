########################## DEVELOPER USE ONLY ##########################

"""
used to build Z17 look up table for the optimisation of ProcessL2.

"""

# NOTE: I don't know how to do tests for this because anything I write will take weeks to execute - Ashley

########################################################################

# import python packages
import os
# import random as rand
import xarray as xr
import numpy as np
import multiprocessing as mp
from multiprocessing.managers import BaseManager

# import RhoCorrections for running of Z17
from Source.ZhangRho import PATH_TO_DATA
from Source.RhoCorrections import RhoCorrections

# import Propagate module for processing uncertainties
from Source.Uncertainty_Analysis import Propagate


class build_LUT():

    def __init__(self):
        # set fixed variables
        self.cloud = None  # not used
        self.waveBands = np.array(
            [350.,  355.,  360.,  365.,  370.,  375.,  380.,  385.,  390.,
            395.,  400.,  405.,  410.,  415.,  420.,  425.,  430.,  435.,
            440.,  445.,  450.,  455.,  460.,  465.,  470.,  475.,  480.,
            485.,  490.,  495.,  500.,  505.,  510.,  515.,  520.,  525.,
            530.,  535.,  540.,  545.,  550.,  555.,  560.,  565.,  570.,
            575.,  580.,  585.,  590.,  595.,  600.,  605.,  610.,  615.,
            620.,  625.,  630.,  635.,  640.,  645.,  650.,  655.,  660.,
            665.,  670.,  675.,  680.,  685.,  690.,  695.,  700.,  705.,
            710.,  715.,  720.,  725.,  730.,  735.,  740.,  745.,  750.,
            755.,  760.,  765.,  770.,  775.,  780.,  785.,  790.,  795.,
            800.,  805.,  810.,  815.,  820.,  825.,  830.,  835.,  840.,
            845.,  850.,  855.,  860.,  865.,  870.,  875.,  880.,  885.,
            890.,  895.,  900.,  905.,  910.,  915.,  920.,  925.,  930.,
            935.,  940.,  945.,  950.,  955.,  960.,  965.,  970.,  975.,
            980.,  985.,  990.,  995., 1000.], dtype=float)  # waveband values already act as nodes for interpolation

        # self.windspeed = np.array([0, 1, 2, 3, 4, 5, 7.5, 10, 12.5, 15])  # 10
        self.windspeed = np.array([0, 1, 2, 3, 5, 7.5, 10, 15])  # 8
        self.AOT = np.array([0, 0.05, 0.1, 0.2, 0.5])  # 5
        self.SZA = np.arange(10, 65, 5)  # 11  # expanded database would go to 65
        self.RELAZ = np.arange(80, 145, 5)  # 13
        self.VZEN = np.array([30, 40]) # 2
        self.SAL = np.arange(0, 70, 10)  # 7
        self.SST = np.arange(-40, 60, 20)  # 5
        self.data = np.zeros((len(self.windspeed), len(self.AOT), len(self.SZA), len(self.RELAZ), len(self.SAL), len(self.SST), len(self.waveBands)))
        # import ctypes
        # self.data = mp.Array('d', data)

        # uncs = np.zeros((len(windspeed), len(AOT), len(SZA), len(RELAZ), len(VZEN), len(SAL), len(SST), len(waveBands)))
        self.da = {}
        self.ds = {}

    @staticmethod
    def run_for_ws(i_windspeed, windSpeedMean, vzen, db, inst):
        waveBands = np.array(
            [350.,  355.,  360.,  365.,  370.,  375.,  380.,  385.,  390.,
            395.,  400.,  405.,  410.,  415.,  420.,  425.,  430.,  435.,
            440.,  445.,  450.,  455.,  460.,  465.,  470.,  475.,  480.,
            485.,  490.,  495.,  500.,  505.,  510.,  515.,  520.,  525.,
            530.,  535.,  540.,  545.,  550.,  555.,  560.,  565.,  570.,
            575.,  580.,  585.,  590.,  595.,  600.,  605.,  610.,  615.,
            620.,  625.,  630.,  635.,  640.,  645.,  650.,  655.,  660.,
            665.,  670.,  675.,  680.,  685.,  690.,  695.,  700.,  705.,
            710.,  715.,  720.,  725.,  730.,  735.,  740.,  745.,  750.,
            755.,  760.,  765.,  770.,  775.,  780.,  785.,  790.,  795.,
            800.,  805.,  810.,  815.,  820.,  825.,  830.,  835.,  840.,
            845.,  850.,  855.,  860.,  865.,  870.,  875.,  880.,  885.,
            890.,  895.,  900.,  905.,  910.,  915.,  920.,  925.,  930.,
            935.,  940.,  945.,  950.,  955.,  960.,  965.,  970.,  975.,
            980.,  985.,  990.,  995., 1000.], dtype=float)
        AOT = np.array([0, 0.05, 0.1, 0.2, 0.5])  # 5
        SZA = np.arange(10, 65, 5)  # 11  # expanded database would go to 65
        RELAZ = np.arange(80, 145, 5)  # 13
        SAL = np.arange(0, 70, 10)  # 7
        SST = np.arange(-40, 60, 20)  # 5
        for i_aot, aot in enumerate(AOT):
            for i_sza, sza in enumerate(SZA):
                for i_relaz, relAz in enumerate(RELAZ):
                    for i_sal, sal in enumerate(SAL):
                        for i_wtemp, wtemp in enumerate(SST):
                            rho, unc = RhoCorrections.ZhangCorr(
                                windSpeedMean,
                                aot,
                                None,  # cloud
                                sza,
                                wtemp,
                                sal,
                                relAz,
                                vzen,
                                waveBands,
                                db=db
                            )
                            inst.set_data(i_windspeed, i_aot, i_sza, i_relaz, i_sal, i_wtemp, rho)  # waveBands

    def wrap_rho(self, windSpeedMean, aot, sza, wtemp, sal, relAz, vzen, waveBands, db, cls):
        cls.data = np.ones(len(waveBands))

    def create_lut(self):

        # from threading import Thread
        
        # threads = {}
        # pool = mp.Pool(processes=8)  # create pool
        BaseManager.register('self', build_LUT)
        manager = BaseManager()
        manager.start()
        inst = manager.self()
        db = self.load()

        process = []
        for i_vzen, vzen in enumerate(self.VZEN):
            for i_windspeed, windSpeedMean in enumerate(self.windspeed):
                # pool.apply_async(self.run_for_ws, args=(i_windspeed, windSpeedMean, vzen, inst))
                process.append(mp.Process(target=self.run_for_ws, args=[i_windspeed, windSpeedMean, vzen, db, inst]))                
                # self.run_for_ws(i_windspeed, windSpeedMean, vzen)
                print(vzen, windSpeedMean)
            
            for p in process:
                p.start()

            for p in process:
                p.join()

            data = inst.get_data()  # get data from shared obect

            da = {}
            ds = {}

            da[vzen] = xr.DataArray(
                data,
                dims=['wind', 'aot', 'sza', 'relAz', 'sal', 'SST', 'wavelength'],
                coords={
                    'wind': self.windspeed,
                    'aot': self.AOT,
                    'sza': self.SZA,
                    'relAz': self.RELAZ,
                    'sal': self.SAL,
                    'SST': self.SST,
                    'wavelength': self.waveBands,
                },
                attrs={
                    'description': "rho values for given inputs",
                    'units': ['ms-1', 'n/a', 'degrees', 'degrees', 'ppm', 'degrees-C']
                },
            )

            ds[vzen] = da[vzen].to_dataset(name="Glint")
            ds[vzen].to_netcdf(os.path.join(PATH_TO_DATA, f'Z17_LUT_{vzen}_new.nc'))

    def get_data(self):
        return self.data
    
    def set_data(self, i_windspeed, i_aot, i_sza, i_relaz, i_sal, i_wtemp, val):
        self.data[i_windspeed, i_aot, i_sza, i_relaz, i_sal, i_wtemp] = val

    @staticmethod
    def load():
        """
        Load look up tables from Zhang et al. 2017
        """
        # logger.debug('Load constants')
        # global db, quads, skyrad0, sunrad0, sdb, vdb, rad_boa_sca, rad_boa_vec

        db_path = os.path.join(PATH_TO_DATA, 'Zhang_rho_db_expanded.mat')
        with xr.open_dataset(db_path, engine='netcdf4') as ds:
            skyrad0 = ds['skyrad0'].to_numpy().T
            sunrad0 = ds['sunrad0'].to_numpy().T
            rad_boa_sca = ds['Radiance_BOA_sca'].to_numpy().T
            rad_boa_vec = ds['Radiance_BOA_vec'].to_numpy().T

        db = xr.open_dataset(db_path, group='db', engine='netcdf4')
        quads = xr.open_dataset(db_path, group='quads', engine='netcdf4')
        sdb = xr.open_dataset(db_path, group='sdb', engine='netcdf4')
        vdb = xr.open_dataset(db_path, group='vdb', engine='netcdf4')

        quads = {k: quads[k].to_numpy().T for k in ['zen', 'azm', 'du', 'dphi', 'sun05',
                                                    'zen_num', 'azm_num', 'zen0', 'azm0']}
        db = {k: db[k].to_numpy().T.squeeze() for k in ['wind', 'od', 'C', 'zen_sun', 'wv']}
        sdb = {k: sdb[k].to_numpy().T.squeeze()
            for k in ['wind', 'od', 'zen_sun', 'zen_view', 'azm_view', 'wv']}
        vdb = {k: vdb[k].to_numpy().T.squeeze()
            for k in ['wind', 'od', 'zen_sun', 'zen_view', 'azm_view', 'wv']}

        return {
            "db": db,
            "quads": quads,
            "sdb": sdb,
            "vdb": vdb,
            "skyrad0": skyrad0,
            "sunrad0": sunrad0,
            "rad_boa_sca": rad_boa_sca,
            "rad_boa_vec": rad_boa_vec,
        }


if __name__ == '__main__':
    # this is the code used to build the Z17 LUT by repeatedly running the Zhang17 code from HCP. Will run if this file, RhoCorrections.py is __main__
    # i.e. running - python3 HCP/Source/RhoCorrections.py

    # read in current LUT. Figure out it's bounds, then append extra nodes to it!
    # pre = xr.open_dataset(os.path.join(PATH_TO_DATA, "Z17_LUT.nc"), engine='netcdf4')

    lut = build_LUT()
    lut.create_lut()
