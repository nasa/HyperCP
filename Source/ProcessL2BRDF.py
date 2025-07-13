#!/usr/bin/env python3
import numpy as np
import xarray as xr
from Source import PATH_TO_DATA
import Source.ocbrdf.ocbrdf_main as oc_brdf


class ProcessL2BRDF():
    # purpose: estimate BRDF factors for a given suite of observations.
    # For the moment, only Morel et al. 2002 BRDF scheme is supported.
    # references:
    # 1) Morel and Gentilli, Applied Optics, 35(24), 1996
    # 2) Morel et al., Applied Optics, 41(3), 2002

    # 2003.08.20 - translated from get_foq.c by PJW, SSAI
    # 2023.08.22: adapted for HyperCP by Juan Gossn (EUMETSAT_
    #   Currently not (yet) iterating more than once
    # 2023.08.22: adapted for HyperCP by Juan Gossn (EUMETSAT) from ThoMaS code:
    #   https://gitlab.eumetsat.int/eumetlab/oceans/ocean-science-studies/ThoMaS
    # ...
    # 2024.07.10: adapted for HyperCP by Juan Gossn (EUMETSAT) from Constant Mazeran's BRDF Python tool (BRDF4OLCI project)

    @staticmethod

    def procBRDF(root,BRDF_option='M02'):
        '''
        Purpose: read all the necessary inputs to perform BRDF correction
        root: an HDF object containing all the necessary ancillary info + already computed radiometric quantities
            These are the directional Rrs and nLw
        BRDF_option: a string, a tag for the selected BRDF scheme
            M02: Morel et al. 2002 scheme
        '''

        # Assuming that measurement protocol is well followed, then sensor should be pointing towards 40 degrees from nadir
        viewz = 40
        # Iterate over root groups to extract ancillary and radiometric quantities to feed the BRDF function.
        for gp in root.groups:
            # if (gp.id == "DERIVED_PRODUCTS"):
            #     # chlorophyll is needed for M02 scheme
            #     chl = gp.datasets["chlor_a"].columns["chlor_a"]
            #     # Could bring in IOPS for IOP BRDF here...
            if (gp.id == "ANCILLARY"):
                solz = gp.datasets["SZA"].columns["SZA"]
                relaz = gp.datasets["REL_AZ"].columns["REL_AZ"]
                aod = gp.datasets["AOD"].columns["AOD"]
                wind = gp.datasets["WINDSPEED"].columns["WINDSPEED"]

        for gp in root.groups:
            if (gp.id == "REFLECTANCE"):
                # NB: BRDF Morel must be applied over Rrs and not nLw because of the iterative process to update chl.
                # Then, the BRDF factors between Rrs and nLw can be assumed to be the same
                # This list will contain Rrs_HYPER and Rrs convoluted to satellite-specific bands, e.g. MODISA
                Rrs_list = []
                for ds in gp.datasets:
                    if ds.startswith("Rrs"):
                        # Can't change datasets in this loop, so make a list
                        # TODO consider uncertainties!
                        if not (ds.endswith("_unc") or ds.endswith("_uncorr") or ds.endswith("_O23") or ds.endswith("_L11") or ds.endswith("_M02")):
                            Rrs_list.append(ds)
                # Extract the spectrla information
                for ds in Rrs_list:
                    Rrs_ds = gp.getDataset(ds)
                    Rrs = Rrs_ds.columns

                    wavelength=[]
                    wv_str=[]
                    for k in Rrs:
                        if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                            if '.' in k:
                                wavelength.append(float(k))
                            else:
                                wavelength.append(int(k))
                            wv_str.append(k)

                    wavelength = np.array(wavelength)

                    # Compile all necessary inputs into an input dictionary "I"
                    I = {}
                    # Transform Rrs to np.array
                    I['Rrs'] = np.array([v for k,v in Rrs.items() if k not in ['Datetime','Datetag','Timetag2']]).T
                    I['wavelengths'] = wavelength
                    # I['chl'] = np.array(chl)
                    I['sza'] = np.array(solz)
                    # give oza the same dimension as the other ancillary inputs!
                    I['oza'] = viewz * np.ones(np.shape(I['sza']))

                    # relaz [-180;180] follows the convention "A", i.e.:
                    # relaz is the azimuth angle between:
                    #     i) vector pointing from the sensor (your location) to target water patch, and
                    #     ii) vector pointing from the sensor (your location) to Sun
                    # BRDF LUT follow convention "B", or "OLCI" convention, see https://www.eumetsat.int/media/50720, Fig. 6.
                    # Additionally, BRDF LUTs are have azimuth ranged [0-180] due to azimuthal symmetry w.r.t. solar plane

                    I['raa'] = np.array(180-np.abs(relaz)) # relaz converted to convention "B" + azimuthal symmetry w.r.t. solar plane
                    I['aot'] = np.array(aod)
                    I['wind'] = np.array(wind)

                    # Reshape to (1,N) in case of single cast
                    for k,v in I.items():
                        if np.shape(v) == ():
                            I[k] = I[k].reshape((1,))
                            
                    # Calculate BRDF correction for Lee11 or O23
                    if BRDF_option in ['L11','O23','M02','M02_SeaDAS']:
                        # fomating input into xarray wanted by OLCI-BRDF code
                        xr_ds = xr.Dataset({
                            'Rw': xr.DataArray(
                                        data   = I['Rrs']*np.pi,
                                        dims   = ['n', 'bands'],
                                        coords = {'n':range(len(I['sza'])), 'bands':wavelength}),
                            'sza': xr.DataArray(
                                        data = I['sza'],
                                        dims   = ['n']),
                            'raa': xr.DataArray(
                                        data = I['raa'],
                                        dims   = ['n']),
                            'vza': xr.DataArray(
                                        data = I['oza'],
                                        dims   = ['n']),
                            'wind': xr.DataArray(
                                        data=I['wind'],
                                        dims=['n']),
                            'aot': xr.DataArray(
                                        data=I['aot'],
                                        dims=['n']),
                            } )
                        
                        # Compute and apply BRDF
                        OC_BRDF = oc_brdf.brdf_prototype(xr_ds, brdf_model=BRDF_option)
                        
                        # Store BRDF corrected rrs
                        Rrs_BRDF = Rrs.copy()
                        for k in Rrs:
                            if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                                Rrs_BRDF[k] = np.array(OC_BRDF.nrrs.sel(bands=float(k))).tolist() 
                        
                        Rrs_BRDF_ds = gp.addDataset(f"{ds}_" + BRDF_option)
                        Rrs_BRDF_ds.columns = Rrs_BRDF
                        Rrs_BRDF_ds.columnsToDataset()
    
                        # Apply same factors to corresponding nLw
                        nLw_ds = gp.getDataset(ds.replace('Rrs','nLw'))
                        nLw = nLw_ds.columns
                        nLw_BRDF = nLw.copy()
                        for k in nLw:
                            if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                                nLw_BRDF[k] = (np.array(nLw[k])*np.array(OC_BRDF.C_brdf.sel(bands=float(k)))).tolist()
    
                        # Store BRDF corrected nLw
                        nLw_BRDF_ds = gp.addDataset(f"{ds.replace('Rrs','nLw')}_" + BRDF_option)
                        nLw_BRDF_ds.columns = nLw_BRDF
                        nLw_BRDF_ds.columnsToDataset()
                        
                        # import matplotlib.pyplot as plt
                        # plt.figure()
                        # ii = 0
                        # plt.plot(wavelength, np.array(Rrs_ds.data[ii]).tolist()[3:], label="raw rrs")
                        # plt.plot(wavelength, np.array(Rrs_BRDF_ds.data[ii]).tolist()[3:], label="BRDF corrected rrs")
                        # plt.legend()
                        # plt.xlabel('wavelength [nm]')
                        # plt.ylabel('Rrs')
                        # plt.title('TRIOS LEE BRDF correction')
                        # plt.figure()
                        # plt.plot(wavelength, np.array(nLw_ds.data[ii]).tolist()[3:], label="raw nLw")
                        # plt.plot(wavelength, np.array(nLw_BRDF_ds.data[ii]).tolist()[3:], label="BRDF corrected nLw")
                        # plt.legend()
                        # plt.xlabel('wavelength [nm]')
                        # plt.ylabel('nLw')
                        # plt.title('TRIOS LEE BRDF correction')
                        # plt.figure()
                        # plt.plot(wavelength, OC_BRDF.C_brdf, 'b', label="BRDF factor")
                        # plt.plot(wavelength, OC_BRDF.C_brdf+OC_BRDF.brdf_unc, 'b--', label="BRDF factor unc")
                        # plt.plot(wavelength, OC_BRDF.C_brdf-OC_BRDF.brdf_unc, 'b--')
                        # plt.legend()
                        # plt.xlabel('wavelength [nm]')
                        # plt.ylabel('BRDF factor')
                        # plt.title('TRIOS LEE BRDF' )
                    else:
                        raise ValueError('BRDF option %s not supported.' % BRDF_option)