#!/usr/bin/env python3
import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import RegularGridInterpolator as rgi
import os
import xarray as xr
from Source import PATH_TO_DATA
import Source.ocbrdf.main as oc_brdf


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
                        if not (ds.endswith("_unc") or ds.endswith("_uncorr") or ds.endswith("_L11") or ds.endswith("_M02")):
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
                    I['raa'] = np.array(np.abs(relaz))
                    I['aot'] = np.array(aod)
                    I['wind'] = np.array(wind)

                    # Reshape to (1,N) in case of single cast
                    for k,v in I.items():
                        if np.shape(v) == ():
                            I[k] = I[k].reshape((1,))
                            
                    # Calculate BRDF correction for Lee11 or O23
                    if BRDF_option in ['L11','O23','M02']:
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
                        
                        # replace UNC nan value with closest non-nan value
                        BRDF_unc = OC_BRDF.brdf_unc.data
                        try:
                            arr = np.array(BRDF_unc.copy())
                            mask = np.isnan(arr)
                            arr[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), arr[~mask])
                            OC_BRDF.brdf_unc.data = arr
                        except:
                                print("An error occured in BRDF computation.")
                        
                        # Store BRDF corrected rrs & unc
                        Rrs_BRDF = Rrs.copy()
                        Rrs_unc_ds = gp.getDataset(f"{ds}_unc")
                        Rrs_unc = Rrs_unc_ds.columns
                        Rrs_BRDF_unc = Rrs_unc.copy()
                        for k in Rrs:
                            if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                                Rrs_BRDF[k] = np.array(OC_BRDF.nrrs.sel(bands=float(k))).tolist()
                                brdf = np.array(OC_BRDF.C_brdf.sel(bands=float(k))).tolist()
                                brdf_unc = np.array(OC_BRDF.brdf_unc.sel(bands=float(k))).tolist()
                                Rrs_BRDF_unc[k] = [np.sqrt( (brdf[0]*Rrs_unc[k][0])**2 + (Rrs[k][0]*brdf_unc[0])**2 )]
                        
                        Rrs_BRDF_ds = gp.addDataset(f"{ds}_" + BRDF_option)
                        Rrs_BRDF_ds.columns = Rrs_BRDF
                        Rrs_BRDF_ds.columnsToDataset()
                        Rrs_BRDF_unc_ds = gp.addDataset(f"{ds}_" + BRDF_option + '_unc')
                        Rrs_BRDF_unc_ds.columns = Rrs_BRDF_unc
                        Rrs_BRDF_unc_ds.columnsToDataset()
    
                        # Apply same factors to corresponding nLw & unc
                        nLw_ds = gp.getDataset(ds.replace('Rrs','nLw'))
                        nLw = nLw_ds.columns
                        nLw_BRDF = nLw.copy()
                        nLw_unc_ds = gp.getDataset(f"{ds}_unc".replace('Rrs','nLw'))
                        nLw_unc = nLw_unc_ds.columns
                        nLw_BRDF_unc = nLw_unc.copy()
                        
                        for k in nLw:
                            if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                                nLw_BRDF[k] = (np.array(nLw[k])*np.array(OC_BRDF.C_brdf.sel(bands=float(k)))).tolist()
                                brdf = np.array(OC_BRDF.C_brdf.sel(bands=float(k))).tolist()
                                brdf_unc = np.array(OC_BRDF.brdf_unc.sel(bands=float(k))).tolist()
                                nLw_BRDF_unc[k] = [np.sqrt( (brdf[0]*nLw_unc[k][0])**2 + (nLw[k][0]*brdf_unc[0])**2 )]
    
                        # Store BRDF corrected nLw
                        nLw_BRDF_ds = gp.addDataset(f"{ds.replace('Rrs','nLw')}_" + BRDF_option)
                        nLw_BRDF_ds.columns = nLw_BRDF
                        nLw_BRDF_ds.columnsToDataset()
                        nLw_BRDF_unc_ds = gp.addDataset(f"{ds.replace('Rrs','nLw')}_"+BRDF_option+"_unc")
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
                        # plt.plot(wavelength, OC_BRDF.C_brdf[0], 'b', label="BRDF factor")
                        # plt.plot(wavelength, OC_BRDF.C_brdf[0]+OC_BRDF.brdf_unc, 'b--', label="BRDF factor unc")
                        # plt.plot(wavelength, OC_BRDF.C_brdf[0]-OC_BRDF.brdf_unc, 'b--')
                        # plt.legend()
                        # plt.xlabel('wavelength [nm]')
                        # plt.ylabel('BRDF factor')
                        # plt.title('Seabird M02 BRDF' )
                        # plt.figure()
                        # plt.plot(wavelength, np.array(nLw_unc_ds.data[ii]).tolist()[3:], label="nLw unc")
                        # plt.plot(wavelength, np.array(nLw_BRDF_unc_ds.data[ii]).tolist()[3:], label="nLw brdf unc")
                        # plt.legend()
                        # plt.xlabel('wavelength [nm]')
                        # plt.ylabel('nLw uncertainties')
                        # plt.title('SeaBird Morel BRDF' )
                        # plt.figure()
                        # plt.plot(wavelength, np.array(Rrs_unc_ds.data[ii]).tolist()[3:], label="rrs unc")
                        # plt.plot(wavelength, np.array(Rrs_BRDF_unc_ds.data[ii]).tolist()[3:], label="rrs brdf unc")
                        # plt.legend()
                        # plt.xlabel('wavelength [nm]')
                        # plt.ylabel('Rrs uncertainties')
                        # plt.title('SeaBird Morel BRDF' )
                        
                        
                    else:
                        raise ValueError('BRDF option %s not supported.' % BRDF_option)
                    
                    

    @staticmethod
    def removeRedundantDimensions(inputParameterGrid, LUT):
        '''
        Remove redundant dimension from inputParameterGrid and LUT (see explanation after definition of input parameters).
        :param inputParameterGrid: tuple containing np.arrays sizes N1,N2,...,Nn of the dependencies of LUT
        :param LUT: np.array, size (N1xN2x...xNn)

        Suppose input parameter "5" is redundant, i.e. N5=1, then this parameter will be removed from inputParameterGrid
        (new size will be N1,N2,...,N4,N6,...,Nn) and also sliced from LUT (new size will be N1xN2x...xN4xN6...xNn)

        :return:
        inputParameterGrid, same as input inputParameterGrid but without dimensions from redundant inputs
        LUT, same as input LUT, but sliced in redundant dimensions
        nonRedundantDims, a list of non-redundant dimensions (integer-indexed following original order in LUT and inputParameterGrid)
        '''

        # Check that everything is initially aligned in terms of dimensions:
        inputParameterGridDims = tuple([len(inpParam) for inpParam in inputParameterGrid])
        try:
            assert (np.shape(LUT) == inputParameterGridDims)
        except:
            raise ValueError('LUT dimensions %s should correpond with the inputParameterGrid dimensions %s' % (
            np.shape(LUT), inputParameterGridDims))

        nonRedundantDims = [idx for (idx, dim) in enumerate(inputParameterGrid) if len(dim) > 1]
        inputParameterGrid = tuple(
            parameter for p0, parameter in enumerate(inputParameterGrid) if p0 in nonRedundantDims)
        LUT = np.squeeze(LUT)

        return inputParameterGrid, LUT, nonRedundantDims

    @staticmethod
    def Morel2002singleIteration(I, R_gothic, foq, OC4MEcoeff):
        '''
        Purpose:
        1) Compute one iteration to get Morel (M02) BRDF factors by linear interpolation of gothic R and f/Q LUTs.
        2) Update log10-chlorophyll using corrected remote-sensing reflectance and OC4ME.
        The outputted BRDF factors are intermediate since MO2 is an iterative process.

        :param I: a dictionary of input numpy arrays (see function ApplyBRDF).
        :param R_gothic: a dictionary with R gothic LUT.
            Dependencies of R_gothic:
                pza: point zenith angle (oza after application of Snell's law when propagating from air to water)
                wind: wind speed at surface (m/s)
        :param foq:
            Dependencies of foq:
            bands: in wavelengths (in nm)
            sza: solar zenith angle
            pza
            raa: relative azimuth angle
            wind: surface (10-m) wind speed in m/s
            aot: aerosol optical thickness @ 865 nm --> 2023.08.22 redundant parameter.
            log_chl: log_10(chl[mg.m-3])
        :param OC4MEcoeff:
            Coefficients for OC4ME inversion log_10(CHL) = sum_k=1..5 OC4MEcoeff[k]*log_10(R)^k, R = max(Rrs[blue,cyan,green])/Rrs[yellow]
            TODO For the moment OC4ME is applied with a tolerance of 25 nm spectral distance to the nominal blue, cyan, green and yellow wavelengths
            Nonetheless, OC4ME must in the future be replaced by something more generic.
        :return:
        I: Modified inputs (log_chl = OC4ME(Rrs*BRDF))
        BRDFfactors1Iter: M02 BRDF factors (same shape as I['Rrs'] = N1x...xNnxNlambda) for a single iteration
        '''

        shapeInp = np.shape(I['sza'])

        # clip inputs I out-of-range for R_gothic to nearest neighbor in R_gothic dependency ranges
        for key in I.keys():
            if key in R_gothic:
                I[key] = np.clip(I[key], float(R_gothic[key].min()), float(R_gothic[key].max()))

        # arg: input parameters - as originally inputted.
        # arg0: input parameters in "normalised" situation:
            # pza = 0, i.e. sensor pointing at nadir
            # wind = 0, i.e. calm sea
        R_gothic['arg'] = np.stack((I['pza'], I['wind']), axis=-1)
        R_gothic['arg0'] = np.zeros(R_gothic['arg'].shape)

        # Remove redundant dimension (e.g. if R_gothic['wind'] only takes 1 value) to circumvent bug in RegularGridInterpolator
        RgothInput, RgothLUT, nonRedundantDims = ProcessL2BRDF.removeRedundantDimensions((R_gothic['pza'], R_gothic['wind']),R_gothic['LUT'])
        # Define interpolator function from interpolation nodes
        R_gothic['int'] = rgi(RgothInput, RgothLUT, method='linear', bounds_error=False,fill_value=None)
        # Obtain R_gothic at input and 'normalised' conditions:
        R_gothic['coeff0'] = R_gothic['int'](R_gothic['arg0'][..., nonRedundantDims])
        R_gothic['coeff' ] = R_gothic['int'](R_gothic['arg' ][..., nonRedundantDims])

        # Clip inputs I out-of-range for foq to nearest neighbor in foq dependency ranges
            # NB: This means that wavelengths out of the LUT definition will be extrapolated to their "nearest neigbhor",
            # Within the range, a linear dependence of the BRDF factors with wavelength will be obtained.
        for key in I.keys():
            if key in foq:
                I[key] = np.clip(I[key], float(foq[key].min()), float(foq[key].max()))

        # Transform all inputs (keys in "I" dictionary) to the shape N1xN2x...xNmxNlambda
        # N1xN2x...xNm will typically be a 1D array, equivalent to the number of casts,
        # though in satellite data it may be two dimensional spanning the along-track and across-track dimensions:
        N = np.shape(I['sza'])
        Nlambda = np.shape(I['wavelengths'])

        # I_tiled: inputs are meshed to the same dimensions: N1xN2x...xNmxNlambda. This is done to ease the interpolation.
        I_tiled = {}

        I_tiled['wavelengths'] = np.zeros((N + Nlambda))
        I_tiled['wavelengths'][...,:] = I['wavelengths']

        for k,v in I.items():
            if k not in ['Rrs','wavelengths']:
                I_tiled[k] = np.repeat(v[..., np.newaxis], Nlambda[0], axis=-1)

        # Stack all inputs, in the same way as with R_gothic:
        foq['arg'] = np.stack((I_tiled['wavelengths'],
                               I_tiled['sza'],
                               I_tiled['pza'],
                               I_tiled['raa'],
                               I_tiled['wind'],
                               I_tiled['aot'],
                               I_tiled['log_chl']),axis=-1)  # Inputs, actual geometry
        foq['arg0'] = foq['arg'].copy()
        foq['arg0'][..., 1:4] = 0  # Some inputs are null in normalised geometry: SZA=0, PZA=0, RAA=0
        foq['int'] = {}
        foq['coeff0'] = {}
        foq['coeff'] = {}

        # Remove redundant dimension (e.g. if foq['aot'] only takes 1 value) to circumvent bug in RegularGridInterpolatorf
        foqInput, foqLUT, nonRedundantDims = ProcessL2BRDF.removeRedundantDimensions((foq['bands'], foq['sza'],
                                                                                      foq['pza'], foq['raa'],
                                                                                      foq['wind'], foq['aot'],
                                                                                      foq['log_chl']), foq['LUT'])

        # Obtain f/Q at both actual and normalised geometry at all bands
        foq['int'] = rgi(foqInput, foqLUT, method='linear',bounds_error=False, fill_value=None)
        foq['coeff0'] = foq['int'](foq['arg0'][..., nonRedundantDims])
        foq['coeff'] = foq['int'](foq['arg'][..., nonRedundantDims])

        # BRDF normalisation factor (=1 if band not appearing in f/Q LUT)
        BRDFfactors1Iter = np.ma.array(np.ones(np.shape(I['Rrs'])), mask=False)
        BRDFfactors1Iter = (foq['coeff0'] * R_gothic['coeff0'][...,np.newaxis]) / (
                            foq['coeff' ] * R_gothic['coeff' ][...,np.newaxis])

        #  Update Rrs and compute new chlorophyll with OC4ME:
        Rrs_chlor = I['Rrs'] * BRDFfactors1Iter

        #### Compute log10(CHL) using OC4ME ####

        # Nominal bands requested to compute OC4ME:
        OC4MEwaveNominal = {'blue': 442.5, 'cyan': 490, 'green': 510, 'yellow': 560}
        deltaLambdaTolerance = 25  # If not exactly coincidental with nominal wavelengths of sensor, will accept nominal
        # wavelengths within a range of deltaLambdaTolerance (in nm) centred at the values in OC4MEwaveNominal for blue,
        # cyan, green and yellow.

        # Obtain the OC4ME wavelengths shifted to the closest nominal wavelengths of the sensor.
        OC4MEwaveNominalSensor = {}
        for color, wave in OC4MEwaveNominal.items():
            waveSat = I['wavelengths'][np.argmin(np.abs(I['wavelengths'] - wave))]
            if np.abs(waveSat-wave) > deltaLambdaTolerance:
                raise ValueError('No nominal sensor wavelength found within [%s-%s;%s+%s] nm' % (
                                    wave, deltaLambdaTolerance, wave, deltaLambdaTolerance))
            OC4MEwaveNominalSensor[color] = waveSat

        #  Cache necessary bands with generic tags (colours, given that nominal wavelengths may change between sensors)
        OC4ME_Rrs = {color: Rrs_chlor[..., np.where(I['wavelengths'] == OC4MEwaveNominalSensor[color])[0][0]] for color
                     in OC4MEwaveNominalSensor}

        # Compute the OC4ME "R"
        OC4MElog10R = np.log10(
            np.max([OC4ME_Rrs['blue'], OC4ME_Rrs['cyan'], OC4ME_Rrs['green']], axis=0) / OC4ME_Rrs['yellow'])

        # Apply OC4ME 5-degree polynomial
        I['log_chl'] = np.zeros(shapeInp)
        for k, Ak in enumerate(OC4MEcoeff):
            I['log_chl'] += Ak * (OC4MElog10R ** k)

        return I, BRDFfactors1Iter

    @staticmethod
    def ApplyBRDF(I, BRDF_option):
        '''
        Purpose: Apply BRDF over directional (non-BRDF-corrected) Rrs. This function takes look up tables for each BRDF
        scheme (by 22.08.2023 only Morel et al. 2002 "M02" supported) from ADF (Auxilliary Data Files) files (only
        available for S3OLCI A & B by 22.08.2023)
        :param I: a dictionary of numpy arrays. It shall contain at least:
            sza (solar zenith angle, degrees from zenith), any shape N1x...xNm
            oza (observing zenith angle, degrees from zenith), any shape N1x...xNm (same as sza)
            raa (relative azimuth angle, degrees), any shape N1x...xNm (same as sza)
                or alternatively saa (solar) and oaa (observing) azimuth angles --> raa will be computed from oaa and saa
            wind (wind speed at surface, m/s)
                or alternatively windx (zonal) and windy (meridional) wind speeds --> wind will be computed from wind
            aot (aerosol optical thickness @ 865 nm), any shape N1x...xNm (same as sza)
            wavelength, vector of wavelengths (nm), shape Nlambdax1
            Rrs (Remote Sensing Reflectance), any shape N1x...xNmxNlambda (same as sza but with additional wavelength dimension)
        :param BRDF_option: a string, indicating the BRDF scheme to be applied:
            Currently supported (by 22.08.2023):
                'M02', Morel, Antoine and Gentili 2002

        :return:
        I: a dictionary of numpy arrays. Same as before but modified after BRDF correction:
            1) I['Rrs'] --> I['Rrs']*BRDFfactors
            2) Other by-products yielded by the correction, e.g. for M02, I['log_chl'] after the pre-defined number of
            iterations (=3 in current ADF)
        BRDFfactors: a numpy array, size N1x...xNmxNlambda (same as I['Rrs']) with the resulting BRDF factors.
            NB: in the case of iterative processes (e.g. 'MO2'), these are the cumulative factors, such that
            I['Rrs']/BRDFfactors retrieves the non-corrected Rrs.
        '''

        #  BRDF-scheme-specific LUT:
        if BRDF_option == 'M02':
            BRDF_LUT = Dataset(os.path.join(PATH_TO_DATA, 'BRDF_LUT_MorelEtAl2002.nc'), 'r')
        else:
            raise ValueError('BRDF option %s still not implemented' % BRDF_option)

        # Check whether mandatory inputs are contained in I
        requiredFields = ['sza', 'oza', 'aot', 'Rrs', 'wavelengths']
        for requiredField in requiredFields:
            if requiredField not in I:
                raise ValueError('%s should be inputted to calculate BRDF coefficients' % requiredField)

        # Obtain PZA (point zenith angle) from OZA (Apply Snell's Law to OZA after air-to-water transmission)
        # NB: white refractive index used...
        n_w = float(BRDF_LUT.variables['water_refraction_index'][:].data)
        I['pza'] = np.rad2deg(np.arcsin(np.sin(np.deg2rad(I['oza'])) / n_w))

        # If surface wind speed not inputted, obtain it from zonal and meridional components (Pythagoras).
        if 'wind' not in I:
            if ('windx' in I) and ('windy' in I):
                I['wind'] = np.sqrt(I['windx'] ** 2 + I['windy'] ** 2)
            else:
                raise ValueError(
                    'Either wind (surface wind speed) or both windx and windy (zonal and meridional wind speeds) should '
                    'be inputted to calculate BRDF coefficients.')

        # If relative azimuth angle not inputted, obtain it from solar and observing zenith angles.
        if 'raa' not in I:
            if ('saa' in I) and ('oaa' in I):
                # constrain RAA to effective range [0-180] = range of values of arc-cosine function.
                I['raa'] = np.rad2deg(np.arccos(np.cos(np.deg2rad(I['saa'][:] - I['oaa'][:]))))
            else:
                raise ValueError(
                    'Either raa (relative azimuth angle) or both saa and oaa (solar and viewing azimuth angles) should '
                    'be inputted to calculate BRDF coefficients.')

        shapeInp = np.shape(I['sza'])
        Nwavelengths = np.shape(I['wavelengths'])

        # Check adequate shape of inputs
        for varName, varValue in I.items():
            if varName == 'Rrs':
                try:
                    assert (np.shape(varValue) == shapeInp + Nwavelengths)
                except:
                    raise ValueError(
                        'Check shape of I["%s"]. Should be N1xN2x...xNmxNwavelengths, being N1xN2x...xNm the shape of I["sza"]' % varName)
            elif varName == 'wavelengths':
                pass
            else:
                try:
                    assert (np.shape(varValue) == shapeInp)
                except:
                    raise ValueError('Check shape of I["%s"], should be the same shape as I["sza"]' % varName)

        # BRDF Schemes
        #  Initialize log_chl with value proposed in BRDF_LUT (oc4me_chl0)
        I['log_chl'] = np.log10(float(BRDF_LUT['oc4me_chl0'][:].data)) * np.ones(shapeInp)

        # Initialize R_gothic, gothic R [Morel, Antoine and Gentili 2002]
        R_gothic = {}
        R_gothic['pza']  = BRDF_LUT['PZA_r_goth'][:].data  # as Refracted by water!!!!
        R_gothic['wind'] = BRDF_LUT['wind_speeds_r_goth'][:].data
        R_gothic['LUT']  = BRDF_LUT['r_goth_LUT'][:].data

        # Initialize foq, f/Q [Morel Antoine and Gentili 2002]
        foq = {}
        foq['bands']   = BRDF_LUT['wavelengths_FOQ'][:].data
        foq['pza']     = BRDF_LUT['PZA_FOQ'][:].data  # as Refracted by water!!!!
        foq['sza']     = BRDF_LUT['SZA_FOQ'][:].data
        foq['raa']     = BRDF_LUT['RAA_FOQ'][:].data
        foq['wind']    = BRDF_LUT['wind_speeds_FOQ'][:].data
        foq['aot']     = BRDF_LUT['tau_a_FOQ'][:].data
        foq['log_chl'] = BRDF_LUT['log_chl_FOQ'][:].data
        foq['LUT']     = BRDF_LUT['f_over_q_LUT'][:].data

        # OC4ME parameters to re-compute CHL
        OC4MEnIter   =   int(BRDF_LUT['oc4me_niter'][:].data)  # Max number of iterations (22.08.2023: 3)
        OC4MEepsilon = float(BRDF_LUT['oc4me_epsilon'][:].data)
        OC4MEcoeff   =       BRDF_LUT['log10_coeff_LUT'][:].data  # Coefficients to apply to the 5-degree OC4ME polynomial

        # Loop over the iterations, inputs "I" and BRDFfactors will be updated after each iteration.
        BRDFfactors = np.ones(np.shape(I['Rrs']))
        chlConvergeFlag = np.zeros(shapeInp).astype(bool)  # Initially is not converged (obviously)
        for nIter in range(OC4MEnIter):
            chlPrevIter = 10 ** I['log_chl']
            I, BRDFfactors1Iter = ProcessL2BRDF.Morel2002singleIteration(I, R_gothic, foq, OC4MEcoeff)

            #  Check if convergence is reached |chl_old-chl_new| < epsilon * chl_new
            chlNewIter = 10 ** I['log_chl']
            chlConvergeFlag = chlConvergeFlag | (np.abs(chlPrevIter - chlNewIter) < OC4MEepsilon * chlNewIter)

            if nIter == 1:
                BRDFfactors = BRDFfactors1Iter
            else:
                # Update only if convergence was not reached.
                BRDFfactors[~chlConvergeFlag,:] = BRDFfactors1Iter[~chlConvergeFlag,:]

        # Update Rrs with BRDF factors
        I['Rrs'] = I['Rrs']*BRDFfactors


        return I, BRDFfactors
