#!/usr/bin/env python3
import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import RegularGridInterpolator as rgi
from scipy.interpolate import CubicSpline as spline
import os

class ProcessL2BRDF():
    # fq = get_fq(w,s,chl_in,n,a,foq_data)
    # purpose: estimate f/Q for a given suite of observations
    # references:
    # 1) Morel and Gentilli, Applied Optics, 35(24), 1996
    # 2) Morel et al., Applied Optics, 41(3), 2002
    # input:
    # 1) wavelength float [w]
    # 2) solar zenith angle float [s]
    # 3) chl concentration float [chl_in]
    # 4) nadir zenith angle float [n]
    # 5) azimuth angle float [a]
    # 6) f/Q table array fltarr [foq_data]
    # output: f/Q correction term float [fq]
    # 8.20.2003 - translated from get_foq.c by PJW, SSAI
    #
    # 2022.11.14: adapted for HyperInSPACE by DAA
    #   Currently not (yet) iterating more than once

    @staticmethod
    def procBRDF(root,BRDF_option=None):

        # chl = np.array([0.01,0.01,0.01])
        # solz = np.array([30,35,40])
        viewz = np.array([40])
        # relaz = np.array([95,110,115])
        # wvl = [300.,350.,412.5, 442.5, 490., 510., 560., 620., 660.,700.]
        for gp in root.groups:
            if (gp.id == "DERIVED_PRODUCTS"):
                chl = gp.datasets["chlor_a"].columns["chlor_a"]
                # Could bring in IOPS for IOP BRDF here...
            if (gp.id == "ANCILLARY"):
                solz = gp.datasets["SZA"].columns["SZA"]
                relaz = gp.datasets["REL_AZ"].columns["REL_AZ"]
                if isinstance(relaz, list):
                    relaz = relaz[0]
                relaz = abs(relaz)

        for gp in root.groups:
            if (gp.id == "REFLECTANCE"):

                nLw_list = []
                for ds in gp.datasets:
                    if ds.startswith("nLw"):
                        # Can't change datasets in this loop, so make a list
                        if not ds.endswith("_unc"):
                            nLw_list.append(ds)

                for ds in nLw_list:
                    nLw_ds = gp.getDataset(ds)
                    nLw = nLw_ds.columns

                    wavelength=[]
                    wv_str=[]
                    for k in nLw:
                        if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                            if '.' in k:
                                wavelength.append(float(k))
                            else:
                                wavelength.append(int(k))
                            wv_str.append(k)

                    wavelength = np.array(wavelength)

                    # Calculate BRDF correction (fQ0/fQ)
                    brdf = ProcessL2BRDF.morel_brdf(chl,solz,viewz,relaz,wvl=wavelength,corr=True) # wavelength X brdf

                    # Insure brdf is a list of lists, even if there is only one ensemble
                    if len(chl)==1:
                        brdf = [[x] for x in brdf]
                    brdf_dict = dict(zip(wv_str,brdf))


                    nLw_fQ = nLw.copy()
                    for k in nLw:
                        if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                            nLw_fQ[k] = ( np.array(nLw[k]) * np.array(brdf_dict[k]) ).tolist()

                    nLw_fQ_ds = gp.addDataset(f"{ds}_fQ")
                    nLw_fQ_ds.columns  = nLw_fQ
                    nLw_fQ_ds.columnsToDataset()

    @staticmethod
    def fq_table_interp():
        with Dataset(os.environ['OCDATAROOT']+'/common/morel_fq.nc', 'r') as ncfile:
            data = ncfile['foq'][:,:,:,:,:]
            grdwvl = ncfile['wave'][:]
            grdchl = np.log10(ncfile['chl'][:])
            grdsolz = ncfile['solz'][:]
            grdviewz = ncfile['senz'][:]
            grdrelaz = ncfile['phi'][:]

        interp_func = rgi((grdwvl, grdsolz, grdchl, grdviewz, grdrelaz), data,\
                        fill_value=None,bounds_error=False)

        return interp_func


    @staticmethod
    def get_fq(solz, viewz, relaz, chl, wvl=None):

        interp_func = ProcessL2BRDF.fq_table_interp()
        print("Initializing f/Q interpolation function")

        runspline=True


        interp_arr = np.meshgrid(wvl, solz, np.log10(chl), viewz, relaz,indexing='ij')
        flat = np.array([m.flatten() for m in interp_arr])
        out_array = interp_func(flat.T)
        result = np.squeeze(out_array.reshape(*interp_arr[0].shape))

        while len(result.shape) > 2:
            result = np.diagonal(result,axis1=1,axis2=2)

        if runspline:
            cs = spline(wvl, result)
            result = cs(wvl)

        return result

    @staticmethod
    def morel_brdf(chl, solz, viewz, relaz, wvl=None, corr=False):

        h2o = 1.34
        thetap = np.degrees(np.arcsin(np.sin(np.radians(viewz)) / h2o))

        fqA = ProcessL2BRDF.get_fq(solz, thetap, relaz, chl, wvl=wvl)
        fq0 = ProcessL2BRDF.get_fq(0.0,  0.0,   0.0, chl, wvl=wvl)

        if corr:
            fq = fq0 / fqA
        else:
            fq = fqA

        return fq.tolist()
