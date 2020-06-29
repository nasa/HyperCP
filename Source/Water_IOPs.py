
import os
import numpy as np
import scipy.interpolate

from SB_support import readSB

def water_iops(fp, wave,T,S):

    ''' Function to obtain pure seawater absorption and backscattering spectra '''
    
    #Pure water absorption from
    #   Pope R.M., Fry E.S. Absorption spectrum (380-700 nm) of pure water. 
    #   II. Integrating cavity measurements. Appl. Opt. 1997;36:8710–8723. 
    #   doi: 10.1364/AO.36.008710.
    #   Smith R.C., Baker K.S. Optical properties of the clearest natural waters (
    #   200–800 nm) Appl. Opt. 1981;20:177–184. doi: 10.1364/AO.20.000177.

    #Pure water backscattering from Morel 1974 (powerlaw fit unknown, but looks good...)
    #   Morel A. Optical properties of pure water and pure sea water. 
    #   In: Jerlov N.G., Nielsen E.S., editors. Optical Aspects of Oceanography. 
    #   Academic Press; New York, NY, USA: 1974. pp. 1–24. 

    #Corrected for in situ temperature and salinity conditions
    #   Sullivan, J M , M Twardowski, I R V Zanefcld, C M Moore, A H
    #   Barnard, P L Donaghay, and B Rhoades (2006), Hyperspectral temperature
    #   and salt dependencies of absorption by water and heavy water in the
    #   400-750 nm spectral range, Appl Opt, 45(21), 5294-5309, doi 10 1364/
    #   AO 45 005294

    # Inputs
    #   fp (string): full file path to water absorption table in SeaBASS format
    #   wave (list): wavelengths of intended output
    #   T (float): temperature
    #   S (float): salinity

    # Outputs
    #   a_sw (list): absorption of seawater
    #   bb_sw (list): backscattering of seawater

    wave = np.array(wave)
    
    #Pope and Frye pure water absorption 380-730 nm, then Smith and Baker 730-800 nm
    aw_sb = readSB(fp, no_warn=True)
    a_pw = scipy.interpolate.interp1d(aw_sb.data['wavelength'], aw_sb.data['aw'], \
        kind='linear')(wave)

    # #Morel water backscattering
    #     #wl_b=[380	390	400	410	420	430	440	450	460	470	480	490	500	510	520	530	540	550	560	570	580	590	600	610	620	630	640	650	660	670	680	690	700 750];
    #     #b_water=[0.0073	0.0066	0.0058	0.0052	0.0047	0.0043	0.0039	0.0035	0.0032	0.0029	0.0027	0.0024	0.0022	0.002	0.0018	0.0017	0.0016	0.0015	0.0013	0.0013	0.0012	0.0011	0.00101	0.00094	0.00088	0.00082	0.00076	0.00071	0.00067	0.00063	0.00059	0.00055	0.00052 0.0005];
    #     ##choose pure water scattering function (divide by two for back-scattering):
    #     #bb_pw=0.5*interp1(wl_b,b_water,wl,'linear');

    #log fit water backscattering
    bb_logfit = 0.0037000 * (380**4.3) / (wave**4.3)

    # Salinity correct:
    if S>0:
        bb_sw = ( (1 + 0.01*S) * bb_logfit)
    else:
        bb_sw = bb_logfit

    # Temp and salinity correction for water absorption (need to know at what T it was measured): 
    if S==0:
         S = 35.0
    if T==0:
         T = 22.0
    T_pope = 22.0

    # Parameters for temp and salinity callibration (From Pegau et al Applied optics 1997):
    M = np.array([0.18, 0.17, 0.52, 1.4, 4.6, 2.1, 4.3, 9.6, 1.6, 34.0, 18.0, 42.0])
    sig = np.array([18.0, 15.0, 14.0, 20.0, 17.5, 15.0, 17.0, 22.0, 6.0, 18.0, 20.0, 25.0])
    lamda_c = np.array([453, 485, 517, 558, 610, 638, 661, 697, 740, 744, 775, 795])
    M_T = np.array([0.0045, 0.002, 0.0045, 0.002, 0.0045, -0.004, 0.002, -0.001, 0.0045, 0.0062, -0.001, -0.001])

    # Computing the correction per degree C
    phi_T = []
    for wl in wave:
        phi_T.append(np.sum( M_T * M / sig * np.exp( -(wl-lamda_c)**2/2.0/sig**2) ))
    phi_T = np.array(phi_T)

    # Salinity correction based on Pegau and Zaneveld 1997:
    wls = np.array([400, 412, 440, 488, 510, 532, 555, 650, 676, 715, 750])
    phi_S_PZ = np.array([0.000243, 0.00012, -0.00002, -0.00002, -0.00002, -0.00003, -0.00003, 0, -0.00002, -0.00027, 0.00064])

    # Interpolate to compute salinity correction per psu
    phi_S = scipy.interpolate.interp1d(wls,phi_S_PZ, \
        kind='linear', bounds_error=False, fill_value=0.0)(wave)

    # Temperature and salinity corrections:
    a_sw = ( a_pw + phi_T*(T - T_pope) + phi_S*S)

    return a_sw, bb_sw

# wave = list(range(400, 701))
# T = 20.0
# S = 33.0
# fp = os.path.join(os.path.abspath('.'), 'Data')
# fp = os.path.join(fp,'Water_Absorption.sb')

# a_sw, bb_sw = water_iops(fp, wave, T, S)
# print(a_sw)

