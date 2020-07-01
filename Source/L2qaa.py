
import os
import numpy as np

from Water_IOPs import water_iops

def L2qaa(Rrs412, Rrs443, Rrs488, Rrs555, Rrs667, RrsHyper, wavelength, SST, SAL):
    ''' Use weighted MODIS Aqua bands to calculate IOPs using
        QAA_v6

    Inputs: 
      RrsXXX: (float) above water remote sensing reflectance at XXX nm
      RrsHyper: (1D numpy array) hyperspectral above water remote sensing reflectance
      wavelength: (1D array) length of RrsHyper; will be truncated to Pope&Fry/Smith&Baker pure water
      T: (float) sea surface temperature
      S: (float) sea surface salinity
        
    Outputs:
    a, adg, aph, b, bb, bbp, c: (1D lists) hyperspectral inherent optical properties
    '''

    # Adjustable empirical coefficient set-up. Many coefficients remain hard
    #   coded as in SeaDAS qaa.c

    # Maximum range based on P&F/S&B
    minMax = [380, 800]
    if min(wavelength) < minMax[0] or max(wavelength) > minMax[1]:
        waveTemp = []
        RrsHyperTemp = []
        for i, wl in enumerate(wavelength):
            if wl >= minMax[0] and wl <= minMax[1]:
                waveTemp.append(wl)
                RrsHyperTemp.append(RrsHyper[i])
        wavelength = np.array(waveTemp)
        RrsHyper = np.array(RrsHyperTemp)

    # Screen hyperspectral Rrs for zeros
    RrsHyper[RrsHyper < 1e-5] = 1e-5

    # Step 1
    g0 = 0.08945
    g1 = 0.1247
    # Step 2
    h0 = -1.146
    h1 = -1.366
    h2 = -0.469
    # Step 8
    S = 0.015  # baseline slope 
    
    # Pure seawater. Pope & Fry adjusted for S&T using Sullivan et al. 2006.
    #   (Now considering using inverted values from Lee et al. 2015...)
    fp = os.path.join(os.path.abspath('.'), 'Data', 'Water_Absorption.sb') # <--- Set path to P&F water
    a_sw412, bb_sw412 = water_iops(fp, [412], SST, SAL)
    a_sw443, bb_sw443 = water_iops(fp, [443], SST, SAL)
    a_sw555, bb_sw555 = water_iops(fp, [555], SST, SAL)
    a_sw667, bb_sw667 = water_iops(fp, [667], SST, SAL)
    a_sw, bb_sw = water_iops(fp, wavelength, SST, SAL)
    

    msg = []
    # Pretest on Rrs(670) from QAAv5
    if Rrs667 > 20 * np.power(Rrs555, 1.5) or \
        Rrs667 < 0.9 * np.power(Rrs555, 1.7):

        msg1 = "L2qaa: Rrs(667) out of bounds, adjusting."
        print(msg1)
        msg.append(msg1)

        Rrs667 = 1.27 * np.power(Rrs555, 1.47) + 0.00018 * np.power(Rrs488/Rrs555, -3.19)


    # Step 0        
    rrs =   RrsHyper / (0.52 + 1.7 * RrsHyper)
    rrs412 = Rrs412 / (0.52 + 1.7 * Rrs412)
    rrs443 = Rrs443 / (0.52 + 1.7 * Rrs443)
    rrs488 = Rrs488 / (0.52 + 1.7 * Rrs488)
    rrs555 = Rrs555 / (0.52 + 1.7 * Rrs555)
    rrs667 = Rrs667 / (0.52 + 1.7 * Rrs667)

    # Step 1
    u = (np.sqrt(g0*g0 + 4.0 * g1 * rrs) - g0) / (2.0 * g1)
    u412 = (np.sqrt(g0*g0 + 4.0 * g1 * rrs412) - g0) / (2.0 * g1)
    u443 = (np.sqrt(g0*g0 + 4.0 * g1 * rrs443) - g0) / (2.0 * g1)
    u555 = (np.sqrt(g0*g0 + 4.0 * g1 * rrs555) - g0) / (2.0 * g1)
    u667 = (np.sqrt(g0*g0 + 4.0 * g1 * rrs667) - g0) / (2.0 * g1)

    # Switch, Step 2
    if Rrs667 < 0.0015:
        chi = np.log10( (rrs443 + rrs488) / (rrs555 + 5 * rrs667/rrs488 * rrs667) )
        lamb0 = 555
        a555 = a_sw555 + np.power(10.0, (h0 + h1*chi + h2*chi*chi))

        # Step 3
        bbp0 = u555*a555 / (1 - u555) - bb_sw555

    else:
        lamb0 = 667
        a667 = np.power(a_sw667 + 0.39*( Rrs667 / (Rrs443 + Rrs488) ), 1.14)

        # Step 3
        bbp0 = u667*a667 / (1 - u667) - bb_sw667

    # Step 4
    eta =  2*( 1 - 1.2 * np.exp( -0.9*rrs443/rrs555 ))

    # Step 5
    bbp = bbp0 * np.power(( lamb0 / wavelength ), eta)
    bb = bbp + bb_sw
    bbp412 = bbp0 * np.power(( lamb0 / 412 ), eta)
    bbp443 = bbp0 * np.power(( lamb0 / 443 ), eta)

    # Step 6
    a = (1 - u) *  bb / u
    a412 = (1 - u412) * ( bb_sw412 + bbp412 ) / u412
    a443 = (1 - u443) * ( bb_sw443 + bbp443 ) / u443

    # Step 7
    zeta = 0.74 + ( 0.2 / ( 0.8 + rrs443/rrs555 ) )

    # Step 8
    S1 = S + ( 0.002 / (0.6 + rrs443/rrs555) )
    xi = np.exp( S1 * (443 - 412))

    #Step 9
    ag443 = ( a412 - zeta * a443 ) / (xi - zeta) - ( a_sw412 - zeta * a_sw443 ) / ( xi - zeta)

    # Step 10
    adg = ag443 * np.exp( -S1 * (wavelength - 443))
    aph = a - adg - a_sw
    
    b = 2.0 * bb
    c = a + b
        
    return a, adg, aph, b, bb, bbp, c, msg




