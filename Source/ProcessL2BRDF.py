
import logging

import numpy as np
import xarray as xr
import Source.ocbrdf.ocbrdf_main as oc_brdf
from Source.ConfigFile import ConfigFile
from Source.utils.loggingHCP import writeLogFileAndPrint


class ProcessL2BRDF():
    '''# purpose: estimate BRDF factors for a given suite of observations.
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
    # 2024.07.10: adapted for HyperCP by Juan Gossn (EUMETSAT) from Constant Mazeran's BRDF Python tool (BRDF4OLCI project)'''

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
        #   NOTE: Juan, can this work with viewz of 30? We should check what is set in the GUI.
        viewz = 40

        solz,relaz,aod,wind = None,None,None,None,
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
                        if not (ds.endswith("_uncorr") or ds.endswith("_O25") or ds.endswith("_L11") or ds.endswith("_M02") or ds.endswith("_unc") or ds.endswith("_sd")):
                            Rrs_list.append(ds)
                
                # ensure hyperspectral dataset is the first in the loop
                Rrs_list.insert(0, Rrs_list.pop(Rrs_list.index("Rrs_HYPER")))
                
                # I have refactored this to loop through Rrs and nLw at the same time as it makes managing variables for the uncertainty easier

                # dicts to store hyperspectral info for convolving BRDF uncs
                brdf_unc = {} 
                hyperspec = {}

                # Extract the spectrla information
                for ds in Rrs_list:  # Rrs_list = [Rrs_HYPER, Rrs_MODISA, Rrs_Sentinel3A, etc.]
                    Rrs_ds = gp.getDataset(ds)
                    Rrs = Rrs_ds.columns
                    
                    # Store BRDF corrected rrs
                    Rrs_BRDF = Rrs.copy()

                    # Apply same factors to corresponding nLw
                    nLw_ds = gp.getDataset(ds.replace('Rrs','nLw'))
                    nLw = nLw_ds.columns

                    nLw_BRDF = nLw.copy()
                    
                    try:
                        # get uncertainty datasets and columns for Rrs and nLw, passig with AttributeError if they do not exits.
                        Rrs_unc_ds = gp.getDataset(f"{ds}_unc")
                        Rrs_unc = Rrs_unc_ds.columns
                        Rrs_BRDF_unc = Rrs_unc.copy()

                        nLw_unc_ds = gp.getDataset(f"{ds.replace('Rrs','nLw')}_unc")
                        nLw_unc = nLw_unc_ds.columns
                        nLw_BRDF_unc = nLw_unc.copy()
                    except AttributeError:  # faster to ask forgiveness than permission
                        if ConfigFile.settings['fL1bCal'] >= 2 or ConfigFile.settings['SensorType'].lower() == 'seabird':
                            writeLogFileAndPrint("Uncertainty group(s) not found")
                        else:
                            pass  # expected for TriOS factory  # no uncertainties, continue without them

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
                            
                    # Calculate BRDF correction for Lee11 or O25
                    if BRDF_option in ['L11','O25','M02','M02_SeaDAS']:
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

                        if ConfigFile.settings['fL1bCal'] >= 2 or ConfigFile.settings['SensorType'].lower() == 'seabird':

                            if "hyper" not in ds.lower():
                                from Source.PIU.Uncertainty_Analysis import Propagate
                                prop = Propagate(100, cores=1)  # TODO: add mDraws to config
                                for meas in ["Rrs","nLw"]:
                                    brdf_unc_vals = prop.conv_hyper_unc(
                                        hyperspec["wvl_hyper"], # hyperspec wavelengths
                                        hyperspec[f"{meas}_hyper"], # reflectance signal
                                        np.sqrt(
                                            np.array(list(brdf_unc[f"{meas}_hyper"].values()))**2 * hyperspec[f"{meas}_hyper"]**2
                                        ), # BRDF unc in refltectance units
                                        platform=ds.split('_')[1]  # which satellite's bands we are integratng to
                                    )
                                    brdf_unc[f"{meas}_{ds.split('_')[1].lower()}"] = {str(k): v for k, v in zip(wavelength, brdf_unc_vals)}  # put in dictionary
                            else:
                                # hyperspectral case must come first
                                hyperspec["wvl_hyper"] = wavelength
                                hyperspec["Rrs_hyper"] = I['Rrs'].flatten()
                                hyperspec["nLw_hyper"] = np.array([v for k,v in nLw.items() if k not in ['Datetime','Datetag','Timetag2']]).T.flatten()

                                for meas in ["Rrs","nLw"]:
                                    meas_uncs = np.sqrt(np.array(OC_BRDF.brdf_unc.values[0])**2 * hyperspec[f"{meas}_hyper"]**2)
                                    brdf_unc[f"{meas}_hyper"] = {
                                        str(k): [v] for k, v in zip(wavelength, meas_uncs)
                                    }  # turn BRDF uncs into dict so we can convolve uncs

                        for k in Rrs:
                            if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                                Rrs_BRDF[k] = np.array(OC_BRDF.nrrs.sel(bands=float(k))).tolist()
                                nLw_BRDF[k] = (np.array(nLw[k])*np.array(OC_BRDF.C_brdf.sel(bands=float(k)))).tolist()

                                if ConfigFile.settings['fL1bCal'] >= 2 or ConfigFile.settings['SensorType'].lower() == 'seabird':
                                    platform = ds.split('_')[1].lower()
                                    
                                    # cs1 = Rrs (applied in lines: 166-169), cs2 = BRDF correction factor
                                    Rrs_BRDF_unc[k] = np.sqrt(
                                        brdf_unc[f"Rrs_{platform}"][k][0]**2 +
                                        (np.array(Rrs_unc[k])**2 * OC_BRDF.C_brdf.sel(bands=float(k)).values**2)
                                    ).tolist()

                                    # cs1 = nLw (applied in lines: 166-169), cs2 = BRDF correction factor
                                    nLw_BRDF_unc[k] = np.sqrt(
                                        brdf_unc[f"nLw_{platform}"][k][0]**2 + 
                                        (np.array(nLw_unc[k])**2 * OC_BRDF.C_brdf.sel(bands=float(k)).values**2)
                                    ).tolist()

                                    # uncs not saved as list, perhaps numpy bug?
                                    Rrs_BRDF_unc[k] = Rrs_BRDF_unc[k] if isinstance(Rrs_BRDF_unc[k], list) else [Rrs_BRDF_unc[k]] 
                                    nLw_BRDF_unc[k] = nLw_BRDF_unc[k] if isinstance(nLw_BRDF_unc[k], list) else [nLw_BRDF_unc[k]]
                        
                        if 'HYPER' in ds:                            
                            try:
                                # save to breakdown groups
                                bd_grp = root.getGroup("BREAKDOWN")
                                if 'BRDF_method' not in bd_grp.attributes or not bd_grp.attributes['BRDF_method']:
                                    bd_grp.attributes['BRDF_method'] = [BRDF_option]
                                elif BRDF_option not in bd_grp.attributes['BRDF_method']:
                                    bd_grp.attributes['BRDF_method'].append(BRDF_option)
                                
                                bd_rrs = bd_grp.addDataset(f"{ds}_BRDF")
                                bd_rrs.columns = {k: v if isinstance(v, list) else [v] for k,v in brdf_unc["Rrs_hyper"].items()}
                                bd_rrs.columnsToDataset()

                                bd_nlw = bd_grp.addDataset(f"{ds.replace('Rrs','nLw')}_BRDF")
                                bd_nlw.columns = {k: v if isinstance(v, list) else [v] for k,v in brdf_unc["nLw_hyper"].items()} 
                                bd_nlw.columnsToDataset()

                            except AttributeError:  # faster to ask forgiveness than permission
                                if ConfigFile.settings['fL1bCal'] >= 2 or ConfigFile.settings['SensorType'].lower() == 'seabird':
                                    writeLogFileAndPrint("BREAKDOWN group not found")
                                else:
                                    pass  # expected for TriOS factory

                        Rrs_BRDF_ds = gp.addDataset(f"{ds}_" + BRDF_option)
                        Rrs_BRDF_ds.columns = Rrs_BRDF
                        Rrs_BRDF_ds.columnsToDataset()

                        Rrs_BRDF_unc_ds = gp.addDataset(f"{ds}_" + BRDF_option + "_unc")
                        Rrs_BRDF_unc_ds.columns = Rrs_BRDF_unc
                        Rrs_BRDF_unc_ds.columnsToDataset()

                        nLw_BRDF_ds = gp.addDataset(f"{ds.replace('Rrs','nLw')}_" + BRDF_option)
                        nLw_BRDF_ds.columns = nLw_BRDF
                        nLw_BRDF_ds.columnsToDataset()

                        nLw_BRDF_unc_ds = gp.addDataset(f"{ds.replace('Rrs','nLw')}_" + BRDF_option + "_unc")
                        nLw_BRDF_unc_ds.columns = nLw_BRDF_unc
                        nLw_BRDF_unc_ds.columnsToDataset()    
                    
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