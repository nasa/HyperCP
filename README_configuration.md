# Configuration

Launch the configuration module and GUI (ConfigWindow.py) from the Main window by selecting/editing a configuration file
 or creating a new one. This file will be instrument-suite-specific, and is also deployment-specific according to which
 factory calibration files are needed, as well as how the instrument was configured on the platform or ship.
 Some cruises (e.g. moving between significantly different water types) may also require multiple configurations to
 obtain the highest quality ocean color products at Level 2. Sharp gradients in environmental conditions could also
 warrant multiple configurations for the same cruise (e.g. sharp changes in air temperature may effect how data
 deglitching is parameterized, as described [below]).

The configuration window looks like this:

<center><img src="Data/Img/Configuration_window.png" alt="banner"></center>

## Calibration & Instrument Files

***NOTE: IT IS IMPORTANT THAT THESE INSTRUCTIONS FOR SELECTING AND ACTIVATING CALIBRATION AND INSTRUMENT FILES ARE
FOLLOWED CAREFULLY OR PROCESSING WILL FAIL***

**Note: You do not need to move/copy/paste your calibration and instrument files; HyperCP will take care of that for you.**

In the 'Configuration' window, click 'Add Calibration Files' to add the *relevant* calibration or instrument files
(date-specific HyperOCR or TriOS factory calibrations or ancillary instrument Telemetry Definition Files;
e.g. in the case of HyperOCR the '.cal' and '.tdf' files). *Only add and enable those calibration and instrument files
that are relevant to the cruise/package you wish to process (see below).*

In the case of HyperOCRs, each instrument you add here -- be it a radiometer or an external data instrument such as a
GPS or tilt-heading sensor -- requires at least one .cal or .tdf file for raw binary data to be interpreted.
Two .cal files are required in the case of radiometers calibrated seperately for shutter open (light) and shutter closed
(dark) calibrations, as is typical with Satlantic/Sea-Bird HyperOCRs. Instruments with no calibrations (e.g. GPS,
SolarTracker, etc.) still require a Telemetry Definition File (.tdf) to be properly interpreted. Compressed archives
(.sip) containing all the required cal files can also be imported here, and will be unpacked automatically by the
software to place the calibration and telemetry files into the appropriate Config folder.

In the case of TriOS, 3 files are required per radiometer to provide all the calibration data needed for processing:
for the device number "xxxx", Cal_xxxx.dat and Back_xxxx_dat, respectively contain the raw calibration factors and
the background levels, while SAM_xxxx.ini provides initialisation information to the processor.

Adding new files will automatically copy these files from the directory you identify on your machine when prompted by
 pressing ```Add Cals``` into the HyperCP directory structure. You should not need to edit the contents of the
 ```HyperInSPACE/Config``` directory manually.

The calibration or instrument file is selected using the drop-down menu. Enable (in the neighboring checkbox) only the
files that correspond to the data you want to process with this configuration. You will need to know which .cal/.tdf
files correspond to each sensor/instrument, and which represent light and dark shutter measurements.

For **HyperOCR**:

- **SATMSG.tdf**: SAS Solar Tracker status message string (Frame Type: Not Required)
- **SATTHSUUUUA.tdf**: Tilt-heading sensor (Frame Type: Not Required) ‡
- **SATNAVxxxA.tdf**: SeaBird Solar Tracker (Frame Type: Not Required)
- **UMTWR_v0.tdf**: UMaine Solar Tracker (Frame Type: Not Required)
- **GPRMC_NMEAxxx.tdf**: GPS (Frame Type: Not Required)
- **SATPYR.tdf**: Pyrometer (Frame Type: Not Required)
- **HEDxxxA.cal**: Es (Frame Type: Dark)
- **HSExxxA.cal**: Es (Frame Type: Light)
- **HLDxxxA.cal**: Li (Frame Type: Dark)
- **HSLxxxA.cal**: Li (Frame Type: Light)
- **HLDxxxA.cal**: Lt (Frame Type: Dark)
- **HSLxxxA.cal**: Lt (Frame Type: Light)

where xxx is the serial number of the SeaBird instrument, followed (where appropriate) by factory calibration codes
(usually A, B, C, etc. associated with the date of calibration).
***Be sure to choose the factory calibration files appropriate to the date of data collection.***

‡ **Note**: Use of built-in flux-gate compass is extremely inadvisable on a steel ship or platform. Best practice is to use
externally supplied heading data from the ship's NMEA datastream or from a seperate, external dual antenna GPS
incorporated into the SolarTracker. DO NOT USE COURSE DATA FROM SINGLE GPS SYSTEMS.

For **TriOS RAMSES** device, you will need to associate each radiometers number to its type of acquisition (Li, Lt or Es), for exemple :

- **SAM_8166.ini**: Li
- **SAM_8329.ini**: Es
- **SAM_8595.ini**: Lt


Selections:

- Add Calibration Files - Allows loading calibration/instrument files into HyperCP. Once loaded, the drop-down box can
be used to select the file to enable the instrument and set the frame type.
- Enabled checkbox - Used to enable/disable loading the file in HyperCP.
- Frame Type
     - [Seabird] ShutterLight/ShutterDark/Not Required can be selected. This is used to specify shutter frame type:
            ShutterLight/ShutterDark for light/dark correction or "Not Required" for all other data.
     - [TriOS] Li/Lt/Es can be selected. This is used to specify the target of each radiometers.

For each calibration file:

Click ```Enable``` to enable the calibration file. Select the frame type used for radiometer data or ```Not Required```
for navigational and ancillary data. Data from the GPS and SATNAV instruments, etc. are interpreted using the corresponding
Telemetry Definition Files ('.tdf').

Once you have created your new Configuration, CAL/TDF files are copied from their chosen locations into
the /Config directory HyperCP directory structure within an automatically created sub-directory named for the
Configuration (i.e., a configuration named "KORUS" creates a KORUS.cfg configuration file in ```/Config ``` and creates
the /Config/KORUS_Calibration directory with the chosen calibration & TDF files).

*The values set in the configuration file should be considered carefully. They will depend on your viewing geometry and
desired quality control thresholds. Do not use default values without consideration.*

NB: Level 1AQC processing includes a module that can be launched from the Configuration window to assist with data
deglitching parameter selection ([Anomaly Analysis](README_deglitching.md)). Spectral filters are also plotted in L1BQC
to help with filter parameterization factors. More details with citations and default setting descriptions are given below.
A separate module to assist in the creation of SeaBASS output files is launched in Level 2 processing, and applied to L2
SeaBASS output as described below.

Click 'Save/Close' or 'Save As' to save the configuration file. SeaBASS headers will be updated automatically to reflect
 your selection in the Configuration window.


 ## Level 1A Processing

Process data from raw binary (Satlantic HyperSAS '.RAW' collections) to L1A (Hierarchical Data Format 5 '.hdf').
Calibration files and the RawFileReader.py script allow for interpretation of raw data fields, which are read into HDF
objects.

**Solar Zenith Angle Filter**: prescreens data for high SZA (low solar elevation) to exclude files which may have been
collected post-dusk or pre-dawn from further processing.

*Triggering the SZA threshold will skip the entire file, not
just samples within the file, so do not be overly conservative with this selection, particularly for files collected
over a long period.* Further screening for SZA min/max at a sample level is available in L1BQC processing.
**Default: 60 degrees (e.g. Brewin et al., 2016)**

## Level 1AQC Processing

Process data from L1A to L1AQC. Data are filtered for vessel attitude (pitch, roll, and yaw when available), viewing
and solar geometry. *It should be noted that viewing geometry should conform to total radiance (Lt) measured at about 40
degrees from nadir, and sky radiance (Li) at about 40 degrees from zenith* **(Mobley 1999, Mueller et al. 2003 (NASA Protocols))**.
Unlike other approaches, HyperCP eliminates data flagged for problematic pitch/roll, yaw, and solar/sensor geometries
*prior* to deglitching the time series, thus increasing the relative sensitivity of deglitching for the removal of
non-environmental anomalies.


- **SolarTracker**: Select when using the Satlantic SolarTracker package. In this case sensor and solor geometry data will
 come from the SolarTracker (i.e. SATNAV**.tdf). If deselected, solar geometries will be calculated from GPS time and
 position with Pysolar, while sensor azimuth (i.e. ship heading and sensor offset) must either be provided in the
 ancillary data or (eventually) from other data inputs. Currently, if SolarTracker is unchecked, the Ancillary file
 chosen in the Main Window will be read in, subset for the relevant dates/times, held in the ANCILLARY_NOTRACKER group
 object, and carried forward to subsequent levels (i.e. the file will not need to be read in again at L2). If the
 ancillary data file is very large (e.g. for a whole cruise at high temporal resolution), this process of reading in the
 text file and subsetting it to the radiometry file can be slow.

- **Rotator Home Angle Offset**: Generally 0. This is the offset between the neutral position of the radiometer suite and
the bow of the ship. This *should* be zero if the SAS Home Direction was set at the time of data collection in the
SolarTracker as per Satlantic SAT-DN-635. If no SolarTracker was used, the offset can be set here if stable (e.g.
pointing angle on a fixed tower), or in the ancillary data file if changeable in time. Without SolarTracker, L1C
processing will require at a minimum ship heading data in the ancillary file. Then the offset can be given in the
ancillary file (dynamic) or set here in the GUI (static). *Note: as SeaBASS does not have a field for this angle between
the instrument and the bow of the ship, the field "relaz" (normally reserved for the relative azimuth between the
instrument and the sun) is utilized for the angle between the ship heading (NOT COG) and the sensor.*

- **Rotator Delay**: Seconds of data discarded after a SolarTracker rotation is detected. Set to 0 to ignore.
Not an option without SolarTracker. **Default: 60 seconds (Vandenberg 2017)**

- **Pitch & Roll Filter** (optional): Data outside these thresholds are discarded if this is enabled in the checkbox.
These data may be supplied by a tilt-heading sensor incorporated in the raw data stream accompanied by a telmetry
definition file (.tdf) as per above, or can be ingested from the Ancillary file (see SAMPLE_Ancillary_pySAS.sb provided
in /Data).
    **Default**: 5 degrees (IOCCG Draft Protocols; Zibordi et al. 2019; 2 deg "ideal" to 5 deg "upper limit").

- **Absolute Rotator Angle Filter** (optional): Angles relative to the SolarTracker neutral angle beyond which data will
be excluded due to obstructions blocking the field of view. These are generally set in the SolarTracker or pySAS
software when initialized for a given platform. Not an option without SolarTracker or pySAS.
    **Default**: -40 to +40 (arbitrary)

- **Relative Solar Azimuth Filter** (optional): Relative azimuth angle in degrees between the viewing Li/Lt and the sun.
    **Default**: 90-135 deg (Mobley 1999, Zhang et al. 2017); 135 deg (Mueller 2003 (NASA Protocols)); 90 deg unless certain
    of platform shadow (Zibordi et al. 2009, IOCCG Draft Protocols)

### Deglitching (optional)

Light and dark data are screened (deglitched) for electronic noise, which is then removed from
the data (optional, but strongly advised).**(e.g. Brewin et al. 2016, Sea-Bird/Satlantic 2017)**

*Currently, spectra with anomalies in any band are deleted in their entirety, which is very conservative. It may be
sufficient to set the anomalous values to NaNs, and only delete the entire spectrum if more than, say, 25% of wavebands
 are anomalous.*

See [this](README_deglitching.md) page for more detail.


## Level 1B Processing

Dark current corrections are applied followed by instrument calibrations and then matching of timestamps and wavebands
for all radiometers in the suite.

Unlike legacy processing for Satlantic/Sea-Bird HyperSAS data in ProSoft, data here are dark current corrected prior to
application of the calibration factors. This allows for the option of applying factory calibrations or full
instrument characterization in conjunction with low-level radiometric uncertainty estimation. It should be noted that
when applying calibration to the dark current corrected radiometry, the offsets (a0) cancel
(see ProSoftUserManual7.7 11.1.1.5 Eqns 5-6) presuming light and dark factory cals are equivalent (which they
historically have been from Satlantic/Sea-Bird).

Three calibration/characterization regimes are available:

**Factory:** 
This regime performes the radiometric calibration using the radiometric gains provided within the factory configuration 
files. For both SeaBird and TriOS the calibration process follow their respective manufacturer recommendation. 
Although no uncertainty values associated to the radiometric factors are avaible in the factory configuration files, 
generic uncertainty values can be used for SeaBird, they are taken from "The Seventh SeaWiFS Intercalibration Round-Robin 
Experiment (SIRREX-7), March 1999" (API: https://ntrs.nasa.gov/citations/20020045342). The uncertainties produced at 
level 2 date will not be FRM compliant but remains an interresting first step to characterize the data. Unfortunately, 
there is no equivalent for TriOS and no uncertainties values will be outputted with this regime for TriOS.

**FRM Class-Based:**
This regimes performes the radiometric calibration using the radiometric characterisation completed by external laboratories.
The radiometric characterization includes both the radiometric gains and their uncertainties for each sensor. The results
are saved in the so called "RADCAL" file, with one file per sensor. The calibration process is identical to the factory regime
and follow the manufacturer guidelines. In addition the Class-Based regime also computes FRM uncertainties using the absolute 
radiometric characterization and class-based values for all other contributors. The contributors included in the uncertainty 
propagation are: the straylight impact, the temperature sensitivity, the polarisation sensitivity (for radiance only), the cosine 
response (for irradiance only), the detector non-linearity and the calibration stability (see D10).

**FRM Full-Characterization:**
This regime performes the complete correction of the radiometry using the full characterization of each sensor by external 
laboratories. For both SeaBird and TriOS the radiometric calibration process is performed with additional corrections. The 
corrections are possible only thanks to the full characterization of the sensors provided in the matching files. The process 
performes the non-linearity correction, the straylight correction, the polarisation correction (for radiance only), the cosine 
response correction (for irradiance only) and the temperature correction (see D10). The process also provides FRM compliant 
uncertainties accounting for the residuals effects of each contributors, meaning the correction residuals are used as uncertainty 
contributor instead of global class-based contribution, leading to smaller uncertainty values.

Once instrument calibration has been applied, data are interpolated to common timestamps and wavebands, optionally
generating temporal plots of Li, Lt, and Es, and ancillary data to show how data were interpolated.

Each HyperOCR collects data at unique and adaptive integration intervals and requires interpolation for inter-instrument
 comparison. Satlantic ProSoft 7.7 software interpolates radiometric data between radiometers using the OCR with the
 fastest sampling rate (Sea-Bird 2017), but here we use the timestamp of the slowest-sampling radiometer (typically Lt)
 to minimize perterbations in interpolated data (i.e. interpolated data in HyperCP are always closer in time to actual
 sampled data). (Brewin et al. 2016, Vandenberg 2017).

Each HyperOCR radiometer collects data in a unique set of wavebands nominally at 3.3 nm resolution. For merging, they
must be interpolated to common wavebands. Interpolating to a different (i.e. lower) spectral resolution is also an
option. No extrapolation is calculated (i.e. interpolation is between the global minimum and maximum spectral range for
*all* HyperOCRs). Spectral interpolation is by univariate spline with a smoothing factor of 3, but can be manually
changed to liner (see ProcessL1B_Interp.interpolateWavelength).
**(API: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.UnivariateSpline.html)**

In the case of TriOS, each radiometers have its own waveband definition, specify through a polynomial function available
in the SAM_xxxx.ini file. TriOS resolution is usually really close to 3.3 nm but can slightly vary depending of this
polynomial. The same interpolation scheme describes above for HyperOCR is used on TriOS data.

*Note: only the datasets specified in ```ProcessL1B.py``` in each group will be interpolated and carried forward. For
radiometers, this means that ancillary instrument data such as SPEC_TEMP and THERMAL_RESP will be dropped at L1B and
beyond. See ```ProcessL1b_Interp.py``` at Perform Time Intepolation comment.*

Optional plots of Es, Li, and Lt of L1B data can be generated which show the temporal interpolation for each parameter
and each waveband to the slowest sampling radiometer timestamp. They are saved in [output_directory]/Plots/L1B_Interp.
Plotting is time and memory intensive, and can also add significant time to PDF report production.

*{To Do: Allow provision for above water radiometers that operate simultaneously, sequentially and/or in the same wavebands.}*

## Level 1BQC Processing

Further quality control filters are applied to data prior to L2 ensemble binning and reflectance
calculation.

Use of the Mobley (1999) and Zhang et al. 2017 glint corrections require wind data, and Zhang (2017) also requires
aerosol optical depth, salinity, and sea surface temperature. L1BQC processing also uses wind speed to filter the data
for minimizing glint contamination. Since most field collections of above water radiometry are missing some or all of
these ancillary parameters (though they can be input in the Ancillary file, if available), an embedded function allows
the user to download model data from the NASA EARTHDATA server. These data are generated by the NASA Global Modeling and
 Assimilation Office (GMAO) as hourly, global 'MERRA2' HDF files at 0.5 deg (latitude) by 0.625 deg (longitude)
 resolution (https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/). Two files will be downloaded for each hour of data
 processed (total ~8.3 MB for one hour of field data) and stored in /Data/Anc. Global ancillary data files from GMAO
 will be reused, so it is not recommended to clear this directory unless updated models are being released by GMAO.
 *(Note: MERRA2 files downloaded prior to March 15, 2022 can be deleted as the file name format has changed.)*
 Details for how these data are applied to above water radiometry are given below.

As of January 2020, access to these data requires a user login and password, which can be obtained
[here](https://oceancolor.gsfc.nasa.gov/registration). A link to register is also provided in the Configuration window
at L1BQC. When the user selects ```Download Ancillary Models```, pop-up windows will allow the user to enter a login and
password. Once this has been done once, canceling the login pop-up dialog will force the program to use the current
configuration (i.e. it is only necessary to re-enter the password if it has changed.)

These ancillary data from models will be incorporated if field data are not incorporated in the Ancillary file provided
in the Main window. If field data and model data are both inaccessible for any reason, the system will use the Default
values (i.e., Wind Speed, AOD, Salinity, and SST) provided in the L1BQC Configuration setup here.

Individual spectra may be filtered out for:

- **Lt(NIR)>Lt(UV)**: Spectra with Lt higher in the UV (average from 780-850) than the UV (350-400) are eliminated.
*{Unable to find citation for the Lt(NIR)> Lt(UV) filter...}*

- **Maximum Wind Speed**: Defaults:
    - 7 m/s (IOCCG Draft Protocols 2019; D'Alimonte pers.comm 2019)
    - 10 m/s Mueller et al. 2003 (NASA Protocols)
    - 15 m/s (Zibordi et al. 2009)

- **Solar Zenith Angle**: may be filtered for minimum and maximum values.
    - Default Min: 20 deg (Zhang et al 2017); Default Max: 60 deg (Brewin et al. 2016)

- **Spectral Outlier Filter**: may be applied to remove noisy data prior to binning. This simple filter examines only
    the spectra of Es, Li, and Lt from 400 - 700 nm, above which the data are noisy in both devices. Using the standard
    deviation of the normalized spectra for the entire sample ensemble, together with a multiplier to establish an
    "envelope" of acceptable values, spectra with data outside the envelop in any band are rejected. Currently, the
    arbitrary filter factors are 5.0 for Es, 8.0 for Li, and 3.0 for Lt. Results of spectral filtering are saved as
    spectral plots in [output_directory]/Plots/L1BQC_Spectral_Filter. The filter can be optimized by studying these
    plots for various parameterizations of the filter.

- **Meteorological flags**: based on **(Ruddick et al. 2006, Mobley, 1999, Wernand et al. 2002, Garaba et al. 2012,
    Vandenberg 2017)** can be optionally applied to screen for undesirable data. Specifically, data are filtered for:

    - **Cloud cover**:  Unusually high sky radiance to donwelling irradiance ratio.
        Default: $\frac{L_{i}(750)}{E_{s}(750)} \geq 1.0$

    - **Too hazy atmosphere**: Unusually low Es at 480 nm.
        Default: $E_{s}(480)[uW.cm^{-2}.nm^{-1}] < 2.0$

    - **Proximity to dawn/dusk**: Unusually low ratio of downwelling irradiance at 470 and 680 nm.
        Default: $E_{s}(470)/E_{s}(680) < 1.0$

    - Acquisition with high relative humidity or rain: unusually low ratio of downwelling irradiances at 720 and 370 nm.
        Default: $E_{s}(720)/E_{s}(370) < 1.095$

    - Note: Cloud screening ($L_{i}(750)/E_{s}(750) \geq 0.05$) is optional and not well parameterized. Clear skies are
    approximately 0.02 (Mobley 1999) and fully overcast are of order 0.3 (Ruddick et al. 2006). Further investigation with automated sky
    photography for cloud cover is warranted.

    - Note: Please also refer to
    [this](https://frm4soc2.eumetsat.int/sites/default/files/inline-files/FRM4SOC-2_D-06_MeasurementProcedure_v3.1_24032023_RBINS_EUMETSAT_signed.pdf)
    document to see recommended QC screening in the frame of [FRM4SOC-2](https://frm4soc2.eumetsat.int/).


## L2 Processing

Data are averaged within optional time interval ensembles prior to calculating the remote sensing
reflectance within each ensemble. A typical field collection file for the HyperSAS SolarTracker is one hour, and the
optimal ensemble periods within that hour will depend on how rapidly conditions and water-types are changing, as well as
 the instrument sampling rate. While the use of ensembles is optional (set to 0 to avoid averaging), it is highly
 recommended, as it allows for the statistical analysis required for Percent Lt calculation (radiance acceptance
 fraction; see below) within each ensemble, rather than %Lt across an entire (e.g. one hour) collection, and it also
 improves radiometric uncertainty estimation.

### L2 Ensembles

- **Extract Cruise Stations** can be selected if station information is provided in the ancillary data file identified
    in the Main window. If selected, only data collected on station will be processed, and the output data/plot files
    will have the station number appended to their names. At current writing, stations must be numeric, not string-type.
    If this option is deselected, all automated data (underway and on station) will be included in the ensemble processing.
    Ancillary file should include lines for both the start and stop times of the station for proper interpolation in L1B.

- **Ensemble Interval** can be set to the user's requirements depending on sampling conditions and instrument rate
    (**default 300 sec**). Setting this to zero avoids temporal bin-averaging, preserving the common timestamps
    established in L1B. Processing the data without ensenble averages can be very slow, as the reflectances are
    calculated for each spectrum collected (i.e. nominally every 3.3 seconds of data for HyperSAS). The ensemble period
    is used to process the spectra within the lowest percentile of Lt(780) as defined/set below. The ensemble average
    spectra for Es, Li, and Lt is calculated, as well as variability in spectra within the ensemble, which is used to
    help estimate sample uncertainty.

- **Percent Lt Calculation** Data are optionally limited to the darkest percentile of Lt data at 780 nm within the
    sampling interval (if binning is performed; otherwise across the entire file) to minimize the effects of surface
    glitter from capillary waves. The percentile chosen is sensitive to the sampling rate. The 5% default recommended in
    Hooker et al. 2002 was devised for a multispectral system with rapid sampling rate.
    - **Default**: 5 % (Hooker et al. 2002, Zibordi et al. 2002, Hooker and Morel 2003); <10% (IOCCG Draft Protocols).
    TODO can this be made compatible with Kevin Ruddick's recommendation of chosing the first 5 scans?

### L2 Sky/Sunglint Correction (rho) and NIR correction

The value for (**Rho_sky**, sometimes called the Fresnel factor) can be estimated using various approaches in order
to correct for glint **(Mobley 1999, Mueller et al. 2003 (NASA Protocols))**. It is adjusted for wind speed and
solar-senzor geometries. The default wind speed (U) should be set by the user depending on in situ conditions, for
instances when the ancillary data and models are not available (see L1BQC above, and further explanation below). The
Mobley 1999 correction does not account for the spectral dependence **(Lee et al. 2010, Gilerson et al. 2018)** or
polarization sensitivity **(Harmel et al. 2012, Mobley 2015, Hieronymi 2016, D'Alimonte and Kajiyama 2016,
Foster and Gilerson 2016, Gilerson et al. 2018)** in Rho_sky. The tabulated LUT used for the Mobley 1999 glint correction derived from
**Mobley, 1999, Appl Opt 38, page 7445, Eq. 4** and can be found in the /Data directory as text or HDF5 data.
*{TODO: Uncertainty estimates for rho in M99 are no longer current (vastly overestimated) since the incorporation of the
 full LUT 2021-11-17.)}*

The **Zhang et al. 2017** model explicitly accounts for spectral dependence in rho, separates the glint contribution
from the sky and the sun, and accounts for polarization in the skylight term. This approach requires knowledge of
environmental conditions during sampling including: wind speed, aerosol optical depth, solar and sensor azimuth and
zenith angles, water temperature and salinity. To accomodate these parameters, HyperCP uses either the ancillary data
file provided in the main window, GMAO models, or the default values set in the Configuration window as follows: field
data ancillary files are screened for wind, water temperature, and salinity. These are each associated with the nearest
timestamps of the radiometer suite to within one hour. Radiometer timestamps still lacking wind and aerosol data will
extract it from the GMAO models, if available. Otherwise, the default values set in the Configuration window will be
used as a last resort.

*{TODO: Include additional skylight/skyglint corrections, such as Groetsch et al. 2017/2020}*
*{TODO: Include a bidirectional correction to Lw based on, e.g. Lee 2011, Zibordi 2009 (for starters; ultimately the BRDF will need to be better parameterized for all conditions and water types.)}*

Remote sensing reflectance is then calculated as

```math
Rrs = \frac{L_{t} - \rho_{sky}.L_{i}}{E_{s}}
```

(e.g. Mobley 1999, Mueller et al. 2003, Ruddick et al. 2006)).
Normalized water leaving radiance (nLw) is calculated as $Rrs.F0$, where F0 is the top of atmosphere incident radiation
adjusted for the Earth-Sun distance on the day sampled. This is now estimated using the Coddington et al. (2021) TSIS-1
hybrid model.

Uncertainties in Li, Lt, and Es are estimated using the standard deviation of spectra within each ensemble (e.g. Li_sd)
or full-file average if no ensembles are extracted. For the Mobley 1999 (M99) glint correction, uncertainty in Rho_sky
(Rho_sky_Delta) is estimated as +/- 0.01 based on the range of model estimates for Rho_sky cited in M99 for the range of
likely conditions for which it is held constant. Uncertainty in Rho_sky is otherwise estimated as +/- 0.003 from Ruddick
et al. 2006 Appendix 2; intended for clear skies, though in the future variation in Rho_sky_Delta as a mutable function
of sky and sea surface conditions should be better constrained when possible (i.e. further research is required).
Uncertainty in Rrs (i.e. Rrs_unc) and nLw are estimated using sum of squares propagation of from Li_sd, Lt_sd, Es_sd,
and Rho_sky_Delta assuming random, uncorrelated error. So, e.g.:

```math
Rrs_{unc} = Rrs *  \sqrt{\(\frac{L_{i,sd}}{L_{i}}\)^2 + \(\frac{\rho_{sky}}{\rho_{sky}}\)^2 + \(\frac{L_{t,sd}}{L_{t}}\)^2 + \(\frac{E_{s,sd}}{E_{s}}\)^2}
```

To know more in detail how HyperCP deals with these uncertainties, please read
[this](https://frm4soc2.eumetsat.int/sites/default/files/inline-files/FRM4SOC-2_D-10_v2.4_210042023_NPL_EUMETSAT_signed.pdf)
report.

Additional glint may be removed from the Rrs and nLw by subtracting the value in the NIR from the entire spectrum
(Mueller et al. 2003 (NASA Protocols)). This approach, however, assumes neglible water-leaving radiance in the 750-800 nm
range (not true of turbid waters), and ignores the spectral dependence in sky glint, and **should therefore only be used
in the clearest waters and with caution**. Here, a minimum in Rrs(750-800) or nLw(750-800) is found and subtracted from
the entire spectrum.

An alternate NIR residual correction can be applied based on **Ruddick et al. 2005, Ruddick et al. 2006**. This utilizes
the spectral shape in water leaving reflectances in the NIR to estimate the residual glint correction for turbid waters
with NIR reflectances from about 0.0001 to 0.03

Negative reflectances may be removed as follows: any spectrum with any negative reflectances between 380 nm and 700 nm
is removed from the record entirely. Negative reflectances outside of this range (e.g. noisy data deeper in the NIR) are
set to 0.

TODO: describe BRDF correction

### L2 Products

Spectral wavebands for a few satellite ocean color sensors can be optionally calculated using their spectral weighting
functions. These will be included with the hyperspectral output in the L2 HDF files. Spectral response functions are
applied to convolve the (ir)radiances prior to calculating reflectances. **(Burgghoff et al. 2020)**.

Plots of processed L2 data from each radiometer and calculated reflectances can be created and stored in
[output_directory]/Plots/L2. Uncertainties are shown for each spectrum as shaded regions, and satellite bands (if
selected) are superimposed on the hyperspectral data.

Select the "Derived L2 Ocean Color Products" button to choose, calculate, and plot derived biochemical and inherent
optical properties using a variety of ocean color algorithms. Algorithms largely mirror those available in SeaDAS with
a few additions. They include OC3M, PIC, POC, Kd490, iPAR, GIOP, QAA, and the Average Visible Wavelength (Vandermuellen
et al. 2020) and GOCAD-based CDOM/Sg/DOC algorithms (Aurin et al. 2018), as well as the Rrs spectral QA score (Wei et al
2016).

#### Optional Outputs

In addition to the HDF standard outputs from each of the level processing, the following ouputs can also be set in the
Configuration window:

##### 1. SeaBASS/OCDB File and Header

To output SeaBASS/OCDB formatted text files, check the box. A SeaBASS subfolder within the L2 directory will be created,
 and separate files generated for Li, Lt, and Es hyperspectral data.

An eponymous, linked module allows the user to collect information from the data and the processing configuration (as
defined in the Configuration window) into the SeaBASS files and their headers. The module is launched by selecting the
```Edit SeaBASS Header``` button in the Configuration window. A SeaBASS/OCDB header configuration file is automatically
stored in the /Config directory with the name of the Configuration and a .hdr extension. Instructions are given at the
top of the SeaBASS Header window. Within the SeaBASS/OCDB header window, the left column allows the user to input the
fields required by SeaBASS/OCDB. Calibration files (if they have been added at the time of creation) are auto-populated.
In the right hand column, the HyperCP parameterizations defined in the Configurations window is shown in the
```Config Comments``` box, and can be editted (though this should rarely ever be necessary). Additional comments can be
added in the second comments field, and the lower fields are autopopulated from each data file as it is processed. To
override auto-population of the lower fields in the right column, enter the desired value here in the
```SeaBASS Header``` window.

<!-- *{TODO: Populate the left column using values in the Ancillary file, if present.}* -->

##### 2. PDF Reports

Upon completion of L2 processing for each file (or lower level if that is the terminal processing level), a PDF summary
report will be produced and saved in [output_directory]/Reports. The report is produced either 1) when processing fails
at any level, or 2) at L2. This contains metadata, processing parameters, processing logs, and plots of QA analysis,
radiometry, and derived ocean color products. These reports should be used to evaluate the choices made in the
configuration and adjust them if necessary.

