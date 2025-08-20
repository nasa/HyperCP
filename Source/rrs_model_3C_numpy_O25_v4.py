#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analytical 3C Remote Sensing Reflectance (Rrs) Model

Author of this script: Jaime Pitarch Portero (CNR/ISMAR)
Embedded into HyperCP by: Juan Gossn (EUMETSAT)

The 3C model computes the remote sensing reflectance of natural waters from above-surface measurements
(Lt,Li,Es). The Lt/Es signal fitted with an analytical model, that is made of Rrs and the glint (Rg).
The rho*Li/Es signal is used as first estimate of Rg (rho~0.028 is Mobley's sea surface reflectance).
The analytical model has the following components:
  1.- Atmospheric partitioning (GC90) to separate direct and diffuse irradiance fractions.

  2.- The aquatic signal Rrs, calculated after Pitarch et al. (2025). It uses the "G" coefficients
      for water and particles, interpolated over sun/view/azimuth geometries. the inherent optical
      properties (IOPs) of seawater are: water absorption (aw), particulate absorption (aph),
      non-algal particulate absorption (aNAP), colored dissolved organic matter absorption (ag),
      and backscattering by water (bbw), phytoplankton (bbph), and non-algal particles (bbNAP).
      IOPs are modelled as a function of the chlorophyll concentration (C), non-algal particles
      concentration (N) and CDOM absorption coefficient at 440 nm (Y).
  
This model implementation updates the release by PMM Groetsch (https://gitlab.com/pgroetsch/rrs_model_3C),
with the following major changes:
    - The Theano library (deprecated) has been replaced with NumPy.
    - The in-water model by Albert and Mobley (2003) has been replaced with O25 (Pitarch et al., 2025).
    - Bio-optical modeling follows a deterministic variation of the approach by Pitarch and Brando (2025).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import lmfit as lm
from scipy.stats import norm, burr12, uniform
from scipy.interpolate import interp1d, RegularGridInterpolator
import os

class rrs_model_3C(object):
    """
    Workflow:
      1. Load spectral IOP databases (aph, aw, bbw).
      2. Build angular interpolators for G-functions using precomputed tables.
      3. Compute IOP components for given chlorophyll (C), non-algal particles (N), CDOM (Y) and geometry.
      4. Combine IOPs to derive total absorption and backscatter, then compute Rrs spectrum.
      5. Fit model to observed radiometric data (Lu/Ed) by adjusting parameters C, N, Y, alpha, beta, and reflection terms.

    Parameters:
    -----------
    data_folder : str, keyword-only
        Path to directory containing IOP and BRDF coefficient files.

    Attributes:
    -----------
    data_folder : str
        Input data directory.
    l_int : ndarray
        Wavelengths of particulate absorption database (aph_db) [nm].
    aph_db : ndarray
        Matrix of particulate absorption spectra (aph) for various samples.
    l_iops : ndarray
        Uniform wavelength grid [350:1000 nm] for IOP computations.
    aw : ndarray
        Water absorption coefficients interpolated onto l_iops [m^-1].
    bbw : ndarray
        Pure seawater backscattering coefficients interpolated onto l_iops [m^-1].
    G_O25_fn : callable
        Returns G0w, G1w, G0p, G1p given sun/view/azimuth angles.

    Methods:
    --------
    _load_absorption_spectra():
        Load aph database from NPZ file.
    _load_water_iops():
        Load and interpolate water aw and bbw from text file.
    _build_G_interpolators():
        Build RegularGridInterpolator objects for BRDF G-functions.
    _GC90(wl, theta_sun, am, rh, pressure, alpha, beta):
        Compute atmospheric partition factors Edd/Ed and Eds/Ed at wavelengths wl.
    get_iop_components(C, N, Y):
        Compute and return dict of all IOP spectra (aw, aph, ag, aNAP, bbw, bbph, bbNAP) for given C, N, Y.
    _Rrs_O25(C, N, Y, geom):
        Assemble IOPs and G-functions to compute Rrs spectrum on l_iops grid.
    fit_LuEd(wl, Ls, Lu, Ed, params, weights, geom, anc, ...):
        Fit model to observed data, returning optimized parameters and modelled spectra.
    get_iop_components(C, N, Y):
        Return diagnostic IOP components for plotting and analysis.
    """
    def __init__(self, data_folder=os.path.join(os.path.dirname(__file__), '..', 'Data')):
        self.data_folder = data_folder
        # Load absorption spectra once
        self._load_aph_spectra()
        # Load water absorption and scattering IOPs
        self._load_water_iops()
        # Build G-function interpolator
        self.G_O25_fn = self._build_G_interpolators()

    def _load_aph_spectra(self):
        """
        Load phytoplankton absorption database (aph) spectra.
        """
        path = os.path.join(self.data_folder, 'aph_20230419_filtered.npz')
        aph_data = np.load(path)
        self.l_int = aph_data['l_int']
        self.aph_db = aph_data['aph_db']

    def _load_water_iops(self):
        """
        Load water absorption and scattering IOPs onto uniform grid.
        """
        data_path = os.path.join(self.data_folder, 'abs_scat_seawater_20d_35PSU_20230922_short.txt')
        raw = np.loadtxt(data_path, skiprows=8)
        # drop last row if extra
        raw = raw[:-1] if raw.shape[1] >= 3 else raw
        wl_raw = raw[:, 0]
        aw_raw = raw[:, 1]
        bbw_raw = raw[:, 2] / 2.0
        # define model grid
        self.l_iops = np.arange(350, 1001)
        self.aw = np.interp(self.l_iops, wl_raw, aw_raw)
        self.bbw = np.interp(self.l_iops, wl_raw, bbw_raw)

    def _build_G_interpolators(self):
        az = np.arange(0, 181, 15)
        tv = np.concatenate([np.arange(0, 81, 10), [87.5]])
        ts = tv.copy()
        def ld3(fname):
            path = os.path.join(self.data_folder, fname)
            m = np.loadtxt(path)
            arr = m.reshape(len(az), len(ts), len(tv)).transpose(1, 2, 0)
            return arr

        G0w = ld3('G0w.txt'); G1w = ld3('G1w.txt')
        G0p = ld3('G0p.txt'); G1p = ld3('G1p.txt')
        i0 = RegularGridInterpolator((ts, tv, az), G0w)
        i1 = RegularGridInterpolator((ts, tv, az), G1w)
        i2 = RegularGridInterpolator((ts, tv, az), G0p)
        i3 = RegularGridInterpolator((ts, tv, az), G1p)
        return lambda s,v,a: (float(i0((s,v,abs(a)))), float(i1((s,v,abs(a)))), float(i2((s,v,abs(a)))), float(i3((s,v,abs(a)))))

    def model_3C(self, wl, beta, alpha, 
              C, N, Y, geom, anc, Ls_Ed, rho_s, rho_dd, rho_ds, delta):
        # Atmospheric partition
        Edd_Ed, Eds_Ed = self._GC90(wl, geom[0], anc[0], anc[1], anc[2], alpha, beta)
        # Bio-optical Rrs
        iops = self.get_iop_components(C, N, Y)
        l_iops, Rrs_ext = self._Rrs_O25(iops, geom)
        Rrs = np.interp(wl, l_iops, Rrs_ext)
        # Surface reflection
        R_g = rho_s * Ls_Ed + rho_dd * Edd_Ed / np.pi + rho_ds * Eds_Ed / np.pi + delta
        Lu_Ed = Rrs + R_g
        return Rrs, R_g, Lu_Ed, iops

    def _GC90(self, wl, theta_sun, am, rh, pressure, alpha, beta):
        th = np.deg2rad(theta_sun)
        z3 = -0.1417 * alpha + 0.82
        z2 = np.where(alpha > 1.2, 0.65, z3)
        z1 = np.where(alpha < 0, 0.82, z2)
        B3 = np.log(1 - z1)
        B2 = B3 * (0.0783 + B3 * (-0.3824 - 0.5874 * B3))
        B1 = B3 * (1.459 + B3 * (0.1595 + 0.4129 * B3))
        Fa = 1 - 0.5 * np.exp((B1 + B2 * np.cos(th)) * np.cos(th))
        wl_a = 550.0
        omega_a = (-0.0032 * am + 0.972) * np.exp(3.06e-4 * rh)
        tau_a = beta * (wl / wl_a)**(-alpha)
        M = 1.0 / (np.cos(th) + 0.50572 * (90.0 + 6.07995 - theta_sun)**(-1.6364))
        M_ = M * pressure / 1013.25
        Tr = np.exp(- M_ / (115.6406 * (wl / 1000.0)**4 - 1.335 * (wl / 1000.0)**2))
        Tas = np.exp(- omega_a * tau_a * M)
        Edd = Tr * Tas
        Edsr = 0.5 * (1 - Tr**0.95)
        Edsa = Tr**1.5 * (1 - Tas) * Fa
        return Edd/(Edd+Edsr+Edsa), (Edsr+Edsa)/(Edd+Edsr+Edsa)

    def _generate_NAP_slope(self, ad440):
        x = np.log10(ad440)
        if ad440 < 0.001:
            return 0.0175
        elif ad440 < 0.05:
            return 0.0175+(0.0104951-0.0175)/(np.log10(0.05)-np.log10(0.001))*(x-np.log10(0.001))
        else:
            return 0.0104951

    def _generate_CDOM_slope(self, ag440):
        ag440 = max(ag440, 1e-3)
        x = np.log10(ag440)
        if ag440 < 0.01:
            return -0.01085 * x + 0.002534
        elif ag440 < 0.04:
            return 0.0122
        elif ag440 < 10:
            return (0.0172-0.0122)/(np.log10(10)-np.log10(0.04))*(x-np.log10(0.04))
        else:
            return 0.0172

    def get_iop_components(self, C, N, Y):
        """
        Compute and return IOP components for given C,N,Y.
        Returns dict with keys: wl, aw, bbw, aph, aNAP, ag, bbph, bbNAP
        """
        wl = self.l_iops
        aw = self.aw
        bbw = self.bbw
        # phytoplankton absorption
        idx = np.where((self.l_int>=667)&(self.l_int<=673))[0]
        ds = np.nanmean(self.aph_db[:,idx], axis=1)
        ng=55; q=np.linspace(1,ng-1,ng-1)/ng*100
        bnds=10**np.percentile(np.log10(np.maximum(ds,1e-12)), q)
        aph670=0.019092732293411*C**0.955677209349669 # After data by Valente 22 + Castagna 22
        if aph670<bnds[0]: iv=np.where(ds<=bnds[0])[0]
        elif aph670>bnds[-1]: iv=np.where(ds>bnds[-1])[0]
        else: t=np.where(bnds-aph670<0)[0]; g=t[-1]+1; iv=np.where((ds>bnds[g-1])&(ds<=bnds[g]))[0]
        my_spec=np.mean(self.aph_db[iv], axis=0) #default option: sample average
        normF=np.nanmean(my_spec[idx])
        aph=my_spec/normF*aph670; aph=np.maximum(aph,0)
        valid=~np.isnan(aph)
        aph=np.interp(wl, self.l_int[valid], aph[valid])
        # phytoplankton backscatter
        gamma_cph=-0.4+(1.6+1.2*0.5)/(1+np.sqrt(C))
        cph=0.25*C**0.795*(660/wl)**gamma_cph
        Bph=max(0.001,0.002+(0.01-0.002)*np.exp(-0.56*np.log10(C)))
        bbph=Bph*(cph-aph)
        # NAP absorption
        laNAPstar440 = -0.1886*np.exp(-1.0551*np.log10(C/N)) - 1.27
        laNAPstar440 = np.clip(laNAPstar440, -3, -0.5)
        aNAP440 = (10**laNAPstar440) * N
        Sdm = self._generate_NAP_slope(aNAP440)
        aNAP = aNAP440 * np.exp(np.clip(-Sdm * (wl - 440), -700, 700))
        # NAP backscatter
        bbpstar555 = 10**(0.6834*laNAPstar440 - 0.9483)
        eta = 0.854123
        bbpstar440 = bbpstar555 * (440/555)**(-eta)
        bbNAP440 = bbpstar440 * (N + 0.07*C) - np.mean(bbph[(wl>=438)&(wl<=442)])
        BNAP=0.015;
        bNAP440=bbNAP440/BNAP;
        cNAP440=aNAP440+bNAP440
        f = (np.log10(0.07*C/N)+4)/6
        f = np.clip(f, 0, 1)
        gamma_cNAP = gamma_cph*f+0.9*(1-f)
        cNAP = cNAP440*(440/wl)**gamma_cNAP
        bbNAP=BNAP*(cNAP-aNAP)
        # CDOM absorption
        Sg=self._generate_CDOM_slope(Y)
        ag=Y*np.exp(np.clip(-Sg*(wl-440),-700,700))
        return {'wl':wl,'aw':aw,'bbw':bbw,'aph':aph,'aNAP':aNAP,'ag':ag,'bbph':bbph,'bbNAP':bbNAP}

    def _Rrs_O25(self, iops, geom):
        """
        Calculate Rrs from IOP components.
        """
        aw=iops['aw']; aph=iops['aph']; aNAP=iops['aNAP']; ag=iops['ag'];
        bbw=iops['bbw']; bbph=iops['bbph']; bbNAP=iops['bbNAP']
        a_tot=aw+aph+aNAP+ag
        bb_tot=bbw+bbph+bbNAP
        omw=bbw/(a_tot+bb_tot)
        omp=(bbph+bbNAP)/(a_tot+bb_tot)
        G0w,G1w,G0p,G1p=self.G_O25_fn(*geom)
        Rrs_O25=(G0w+G1w*omw)*omw + (G0p+G1p*omp)*omp
        return iops['wl'], Rrs_O25

    def fit_LuEd(self, wl, Ls, Lu, Ed, params, weights, geom, anc, method='lbfgsb', verbose=True):
        """
        Fit Lu/Ed spectrum by minimizing residuals. geom=(theta_sun, theta_view, azimuth)
        """
        def resid(p):
            pv = p.valuesdict()
            Rrs_mod, R_g, LuEd_mod, iops = self.model_3C(
                wl, pv['beta'], pv['alpha'],
                pv['C'], pv['N'], pv['Y'], geom, anc,
                Ls / Ed, pv['rho_s'], pv['rho_dd'], pv['rho_ds'], pv['delta']
            )
            return np.sum((Lu/Ed - LuEd_mod)**2 * weights)
        out = lm.minimize(resid, params, method=method, options={'disp': verbose})
        pv = out.params.valuesdict()
        Rrs_mod, R_g, LuEd_mod, iops = self.model_3C(
            wl, pv['beta'], pv['alpha'],
            pv['C'], pv['N'], pv['Y'], geom, anc,
            Ls/Ed, pv['rho_s'], pv['rho_dd'], pv['rho_ds'], pv['delta']
        )

        # Print optimization results
        print("\nOptimized parameters:")
        for name, val in pv.items():
            print(f"  {name} = {val:.4g}")

        return out, Rrs_mod, R_g, LuEd_mod, Lu/Ed

if __name__ == '__main__':
    data_folder = os.path.join(os.path.dirname(__file__), '..', 'Data')
    data = pd.read_csv(os.path.join(data_folder, 'example_data_NIOZ_jetty_2.csv'), index_col=0, skiprows=15)
    wl = data.index.values; Ls = data.iloc[:,0].values; Lu = data.iloc[:,1].values; Ed = data.iloc[:,2].values
#    geom=(40.62, 40, 135) # Baltic Sea
#    geom=(59, 35, 6) # Jetty
    geom=(59, 35, 100) # Jetty 2
    am=4
    rh=60
    pressure=1013.25
    model = rrs_model_3C(data_folder=data_folder)
    params = lm.Parameters()
    params.add_many(
        ('C',10,True,0.1,50,None),('N',10,True,0.1,60,None),('Y',0.5,True,0.05,2,None),
        ('rho_s',0.028,False,0.0,0.04,None),('rho_dd',0.001,True,0.0,0.2,None),('rho_ds',0.00,True,-0.01,0.01,None),
        ('delta',0.0,False,-0.001,0.001,None),('alpha',1.0,True,0.0,3,None),('beta',0.05,True,0.01,0.5,None)
    )
    weights = np.where(wl < 450, 1, np.where(wl < 700, 1, 5))
    reg, R_rs_mod, R_g, Lumod, LuEd_meas = model.fit_LuEd(
        wl, Ls, Lu, Ed, params, weights, geom, anc=(am,rh,pressure)
    )
    
    fig = plt.figure(figsize=(10, 10), dpi=300); plt.grid(True)
    plt.plot(wl, Lu/Ed, label='L_t/E_s measured');
    plt.plot(wl, Lumod, label='L_t/E_s modelled'); plt.plot(wl, R_rs_mod, label='Modelled R_rs');
    plt.plot(wl, R_g, label='R_g'); plt.plot(wl, LuEd_meas-R_g, label='R_rs 3C');
    plt.xlabel(r'$\lambda\ \mathrm{(nm)}$'); plt.ylabel('Various reflectances (sr^(-1))'); plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(data_folder, 'Plot_3C_1.png'), bbox_inches='tight', dpi=fig.dpi)
    
    """
    """
    # Extract optimized parameters
    optimized = reg.params.valuesdict()
    C_opt, N_opt, Y_opt = optimized['C'], optimized['N'], optimized['Y']

    # Compute and plot IOP components with optimized values
    comps = model.get_iop_components(C_opt, N_opt, Y_opt)
    # list of keys you want to plot (except 'wl')
    keys = ['aw','aph','aNAP','ag','bbw','bbph','bbNAP']
    n = len(keys)

    # create a grid; e.g. 2 rows × 4 cols (adjust as needed)
    cols = 4
    rows = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 3*rows), sharex=True, dpi=300)

    for ax, key in zip(axes.flat, keys):
        ax.grid(True)
        ax.plot(comps['wl'], comps[key])
        ax.set_xlabel(r'$\lambda\ (\mathrm{nm})$')
        ax.set_ylabel(key+ ' m^(-1)')

    # if there are any unused subplots, hide them
    for ax in axes.flat[n:]:
        ax.set_visible(False)

    plt.tight_layout()
    plt.savefig(os.path.join(data_folder, 'Plot_3C_2.png'), bbox_inches='tight', dpi=fig.dpi)
    
    # Plot IOP components and omegas
    comps = model.get_iop_components(C_opt, N_opt, Y_opt)
    a_tot = comps['aw'] + comps['aph'] + comps['aNAP'] + comps['ag']
    bb_tot = comps['bbw'] + comps['bbph'] + comps['bbNAP']
    omph = comps['bbph'] / (a_tot + bb_tot)
    omNAP = comps['bbNAP'] / (a_tot + bb_tot)

    fig = plt.figure(figsize=(10, 10), dpi=300);
    plt.plot(comps['wl'], omph, label='omega_ph');
    plt.plot(comps['wl'], omNAP, label='omega_NAP');
    plt.xlabel('Wavelength (nm)'); plt.ylabel('Omegas');
    plt.title('Omegas vs Wavelength'); plt.legend(); plt.grid(True)
    plt.savefig(os.path.join(data_folder, 'Plot_3C_3.png'), bbox_inches='tight', dpi=fig.dpi)
    plt.close('all')