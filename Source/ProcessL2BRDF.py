#!/usr/bin/env python3
import argparse
import sys
from typing import OrderedDict
import wave
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
    def procBRDF(root):

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
                    
                    # nLw_ds.columnsToDataset()                        
                    # nLw = nLw_ds.data.copy() # ensembles X wavelength
                    # nLw = nLw.astype(np.float64)

                    # Calculate BRDF correction (fQ0/fQ)
                    brdf = ProcessL2BRDF.morel_brdf(chl,solz,viewz,relaz,wvl=wavelength,corr=True) # wavelength X brdf
                    # outarray = np.column_stack((np.asarray(wavelength),np.asarray(brdf)))
                    brdf_dict = dict(zip(wv_str,brdf))

                    nLw_fQ = nLw.copy()
                    for k in nLw:
                        if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                            nLw_fQ[k] = nLw[k] * brdf_dict[k]

                    nLw_fQ_ds = gp.addDataset(f"{ds}_fQ")
                    nLw_fQ_ds.columns  = nLw_fQ
                    nLw_fQ_ds.columnsToDataset()

    @staticmethod
    def fq_table_interp():
        ncfile = Dataset(os.environ['OCDATAROOT']+'/common/morel_fq.nc', 'r')
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

        fqA = np.array(ProcessL2BRDF.get_fq(solz, thetap, relaz, chl, wvl=wvl))
        fq0 = np.array(ProcessL2BRDF.get_fq(0.0,  0.0,   0.0, chl, wvl=wvl))

        if corr:
            fq = fq0 / fqA
        else:
            fq = fqA

        return fq





    # def main():
    #     """
    #     Primary driver for stand-alone version
    #     """
    #     __version__ = '1.0.0'

    #     parser = argparse.ArgumentParser(description=\
    #         'calculate Morel brdf correction')

    #     parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)

    #     parser.add_argument('chl', nargs='+', type=float, default=None,help='input chlorophyll')
    #     parser.add_argument('--solz', type=float, default=None,help='input solar zenith angle')
    #     parser.add_argument('--viewz', type=float, default=None,help='input view zenith angle')
    #     parser.add_argument('--relaz', type=float, default=None,help='input relative azimuth angle')
    #     parser.add_argument('--output_file',type=str, default=None, help="optional output filename; default: STDOUT")

    #     args = parser.parse_args()

    #     global wl
    #     wvl = [300.,350.,412.5, 442.5, 490., 510., 560., 620., 660.,700.]

    #     chl = np.atleast_1d(args.chl)
    #     solz = np.atleast_1d(args.solz)
    #     viewz = np.atleast_1d(args.viewz)
    #     relaz = np.atleast_1d(args.relaz)

    #     #chl = np.array([0.01])
    #     # solz = np.array([30])
    #     # viewz = np.array([25])
    #     # relaz = np.array([110])
    #     chl = np.array([0.01,0.01,0.01])
    #     solz = np.array([30,35,40])
    #     viewz = np.array([25,27,30])
    #     relaz = np.array([95,110,115])
    #     brdf = morel_brdf(chl,solz,viewz,relaz,wvl=wvl,corr=True)

    #     outarray = np.column_stack((np.asarray(wl),np.asarray(brdf)))

    #     if args.output_file:
    #         ofile = open(args.output_file,'w')
    #         ofile.write("/begin_header\n")
    #         ofile.write("! Output of Model BRDF function\n")
    #         ofile.write("! chlorophyll: %f\n" % args.chl)
    #         ofile.write("! solar zenith angle: %f\n" % args.solz)
    #         ofile.write("! view zenith angle: %f\n" % args.viewz)
    #         ofile.write("! relative azinuth angle: %f\n" % args.relaz)
    #         ofile.write("/missing=-999\n")
    #         ofile.write("/delimiter=space\n")
    #         ofile.write("/fields=wavelength,brdf\n")
    #         ofile.write("/units=nm,dimensionless\n")
    #         ofile.write('\n'.join([' '.join(['{:.6f}'.format(value) for value in row]) for row in outarray]))
    #         # for i in range(len(brdf)):
    #         #     ofile.write('%7.2f %12.9f\n' % (wl[i],brdf[i]))
    #         ofile.close()
    #     else:
    #         # for i in range(len(brdf)):
    #         #     print('%7.2f %12.9f' % (wl[i],brdf[i]))
    #         print('\n'.join([' '.join(['{:.6f}'.format(value) for value in row]) for row in outarray]))

