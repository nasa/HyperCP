# Configuration

Launch the configuration window from the Main window by selecting/editting a configuration file
 or creating a new one. This configuration is sensor/platform specific and deployment-specific according to which
 factory calibration files are needed, as well as how the instrument was configured on the platform.

The configuration window should look like this:

<center><img src="Data/Img/Configuration_window.png" alt="banner"></center>

# Contents
### [Calibration/Instrument Setup](#calibration-and-instrument-files)
### [Level 0](#level-0-raw-files)
### [Level 1A](#level-1a)
### [Level 1AQC](#level-1aqc)
### [Level 1B](#level-1b)
### [Level 1BQC](#level-1bqc)
### [Level 2](#level-2)
### [SeaBASS/OCDB Output](#1-seabassocdb-file-and-header)
### [PDF Reports](#2-pdf-reports)



## Calibration and Instrument Files

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

DALECs have one .cal file for all three radiometers.

Adding new files will automatically copy these files from the directory you identify on your machine when prompted by
 pressing ```Add Cals``` into the HyperCP directory structure. You should not need to edit the contents of the
 ```HyperInSPACE/Config``` directory manually.

The calibration or instrument file is selected using the drop-down menu. Enable (in the neighboring checkbox) only the
files that correspond to the data you want to process with this configuration. For TriOS sensors, you will need to know which .ini
files correspond to each sensor/instrument, but HyperCP can now automatically recognize Es/Li/Lt Light/Dark light and dark calibration files, as described below.

For **HyperOCR**:

- **SATMSG.tdf**: SAS Solar Tracker status message string (Frame Type: Not Required)
- **SATTHSUUUUA.tdf**: Tilt-heading sensor (Frame Type: Not Required) ‡
- **SATNAVxxxA.tdf**: Sea-Bird Solar Tracker (Frame Type: Not Required)
- **UMTWR_v0.tdf**: UMaine Solar Tracker (Frame Type: Not Required)
- **GPRMC_NMEAxxx.tdf**: GPS (Frame Type: Not Required)
- **SATPYR.tdf**: Pyrometer (Frame Type: Not Required)
- **HEDxxxA.cal**: Es (Frame Type: Dark)
- **HSExxxA.cal**: Es (Frame Type: Light)
- **HLDxxxA.cal**: Li (Frame Type: Dark)
- **HSLxxxA.cal**: Li (Frame Type: Light)
- **HLDxxxA.cal**: Lt (Frame Type: Dark)
- **HSLxxxA.cal**: Lt (Frame Type: Light)

where xxx is the serial number of the Sea-Bird instrument, followed (where appropriate) by factory calibration codes
(usually A, B, C, etc. associated with the date of calibration). Note that if you have a robotic platform, you only need one .tdf file for the tracker: SATNAV for Sea-Bird Solar Tracker or UMTWR for UMaine Solar tracker (pySAS).
***Be sure to choose the factory calibration files appropriate to the date of data collection.***

‡ **Note**: Use of built-in flux-gate compass is inadvisable on a steel ship or platform. Best practice is to use
externally supplied heading data from the ship's NMEA datastream or from a seperate, external dual antenna GPS
incorporated into the SunTracker. DO NOT USE COURSE DATA FROM SINGLE GPS SYSTEMS FOR SENSOR ORIENTATION.

For **TriOS RAMSES** device, you will need to associate each radiometer number to its type of acquisition (Li, Lt or Es), for example :

- **SAM_8166.ini**: Li
- **SAM_8329.ini**: Es
- **SAM_8595.ini**: Lt

‡ **Note**: For **TriOS RAMSES**, HyperCP currently expects the Matlab output files (.mlb) from MSDA-XE acquisition software as described in [Measurement Procedure Document D-6](https://frm4soc2.eumetsat.int/sites/default/files/inline-files/FRM4SOC-2_D-06_MeasurementProcedure_v3.1_24032023_RBINS_EUMETSAT_signed.pdf). Additional file formats supporting TriOS systems (e.g. SoRad) are under development.

Selections:

- Add Calibration Files - Allows loading calibration/instrument files into HyperCP. Once loaded, the drop-down box can
be used to select the file to enable the instrument and set the frame type.
- Enabled checkbox - Used to enable/disable loading the file in HyperCP.
- Frame Type (these are now resolved for you automatically)
     - [Seabird] ShutterLight/ShutterDark/Not Required can be selected. This is used to specify shutter frame type:
            ShutterLight/ShutterDark for light/dark correction or "Not Required" for all other data.
     - [TriOS] Li/Lt/Es can be selected. This is used to specify the target of each radiometers.


Each file added (.cal, .ini, .tdf) is enabled by default, but you can unclick the ```Enable``` box or remove those added in error or unused. Selecting the frame type used for radiometer data or ```Not Required``` for navigational and ancillary data should be automatic, but is worth checking. Data from the GPS and SATNAV instruments, etc. are interpreted using the corresponding Telemetry Definition Files ('.tdf').

Once you have created your new Configuration, CAL/INI/TDF files are copied from their chosen locations into
the /Config directory HyperCP directory structure within an automatically created sub-directory named for the
Configuration (i.e., a configuration named "KORUS" creates a KORUS.cfg configuration file in ```/Config ``` and creates
the ```/Config/KORUS_Calibration``` directory with the chosen calibration & TDF files).

*The values set in the configuration file should be considered carefully. They will depend on your viewing geometry and
desired quality control thresholds. Do not use default values without consideration.*

NB: Level 1AQC processing includes a module that can be launched from the Configuration window to assist with data
deglitching parameter selection ([Anomaly Analysis](README_deglitching.md)). Spectral filters are also plotted in L1BQC
to help with filter parameterization factors. More details with citations and default setting descriptions are given below.
A separate module to assist in the creation of SeaBASS output files is launched in Level 2 processing, and applied to L2
SeaBASS output as described below.

Click 'Save/Close' or 'Save As' to save the configuration file. SeaBASS headers will be updated automatically to reflect
 your selection in the Configuration window.

 ## Level 0 (RAW) Files

 Raw filenames for autonomously collected data (i.e., SolarTracker, pySAS, DALEC, So-Rad) have no restrictions as these files contain data from all three radiometers in one file.

 Manual-acquisition TriOS raw files, as exported in Matlab compatible format (ASCII, .mlb, see MSDA_XE Advanced Manual and [Measurement Procedure Document D-6](https://frm4soc2.eumetsat.int/sites/default/files/inline-files/FRM4SOC-2_D-06_MeasurementProcedure_v3.1_24032023_RBINS_EUMETSAT_signed.pdf)) comprise one file per sensor (i.e., Li, Lt, Es). These files have certain filename restrictions in HyperCP.
 - Raw filenames should contain the string "SAM_DDDD", where DDDD refers to the serial number of the instrument.
 - They should contain a date/time signature and/or a station/cast signature
 - Datetime signatures should conform to one of the following conventions: YYYYMMDD_hhmmss, YYYY_MM_DD_hh_mm_ss, YYYYMMDD_hh_mm_ss,YYYY_MM_DD_hhmmss
 - Station/cast signatures should be in the format "SSCCX", where SS is the station number and CC is the cast number. X designates the acquisition as normal ("S") or caps-on-darks ("D").
 - The datetime and station/cast signatures should be set apart from the rest of the name with a seperator such as "_" or "-".
 - For example, a triplet of raw files might be named "SAM_0123_20250625_191500_0101S.mlb","SAM_0124_20250625_191500_0101S.mlb", and "SAM_0125_20250625_191500_0101S.mlb".

 If a station/cast designation is provided, this will supercede any datetime stamp provided, and higher level data will contain the station/cast designation as well as the datetime of the start of the raw file (provided in the data).

 Additional conventions for raw filenaming are permitted, though largely ignored in higher level data filenaming.
 One convention might be GEE_SSCCX_SAM_DDDD, where:
- G indicates the region/site (i.e., A for the AAOT);
- EE indicates the campaign number (i.e., 01-99);
- SS indicates the station number (i.e., 01-99);
- CC indicates the cast number (i.e., 01-99);
- X indicates the data type (i.e., D for dark, S for the actual above-water measurements)
- DDDD indicates the device serial number (anything alphanumerical identifying the sensor operated in the field)
- For example, a raw file might be named "A99_0101S_SAM_0123.mlb"

Another that conforms more closely with SeaBASS conventions would be EXPERIMENT_CRUISE_PLATFORM_DATETIME_SAM_DDDD_SSCCX, where:
- EXPERIMENT and CRUISE are self explanatory (and agreed upon with SeaBASS staff prior to submission)
- PLATFORM refers to the ship or tower, etc. the sensor is mounted on
- DATETIME, SAM_DDDD, and SSCCX conform to the norms listed above
- For example "FICE_FICE2025_AAOT_20250625_191500_SAM_0123.mlb" or "FICE_FICE2025_AAOT_20250625_191500_SAM_0123_0101S.mlb"

Regardless of the raw filenames for the individual instruments, the higher level data will either conform to the data start time and SSCCX designiation, or the datetime designation provided. (Keep in mind that from L1A onwards, the three files become one.)

 ## Level 1A Processing

***NOTE:*** HyperCP is optimized for hour-long raw files when using automated data collections (e.g., pySAS, DALEC, So-Rad).

Process data from raw binary to L1A (Hierarchical Data Format 5 '.hdf'). Raw data files expected are .raw (or .RAW), .mlb, or .TXT for Sea-Bird, TriOS, or DALEC, respectively. It is helpful to keep them in the directory that the Main configuration points to, but directory can be named anything (e.g., "RAW").

***NOTE: Caps-on-darks*** For TriOS manual acquisition, it is possible to estimate the internal working temperature of each radiometer by collecting data samples with the light occluded by covering the foreoptics (i.e., with the cap). The basis for this approach is provided in Zibordi and Talone, in prep. (2025). This requires that station/cast can be designated as described above for L0 filenaming. Caps-on dark measurements are made to help estimate the internal noise of the instrument as a function of temperature, and by inversion can be applied to extract the temperature of the instrument during a station collection and apply that temperature in the processing of normal "S" data aquisition. When selected in L1B (see below), filenames containing "XXYYS" (where XX is station and YY is cast) can use the internal temperature derived in the "XXYYD" file for each radiometer (where only XX-station needs to match, not YY-cast). For example, a caps-on dark file at station 01 processed to L1A using the option **Caps-on darks only** with filename containing "20250617-100300_0101D" can be used to find the internal working temperature of each sensor and applied to regular casts with filenames containing "20250617-100800_0101S", "20250617-101300_0102S", and "20250617-101800_0103S" (casts 01, 02, and 03 at station 01).

**Solar Zenith Angle Filter**: prescreens data for high SZA (low solar elevation) to exclude files which may have been
collected post-dusk or pre-dawn from further processing.

*Triggering the SZA threshold will skip the entire file, not just samples within the file, so do not be overly conservative with this selection, particularly for files collected over a long period.* Further screening for SZA min/max at a sample level is available in L1BQC processing. **Default: 60 degrees (e.g. Brewin et al., 2016)**

## Level 1AQC Processing

Process data from L1A to L1AQC. Ancillary data from the file provided in the Main Window (see [Main Window; Ancillary Data](README.md#3-ancillary-input-files)) are read into the data file. Data are filtered for vessel attitude (pitch, roll, and yaw when available), viewing
and solar geometry. *It should be noted that viewing geometry should conform to total radiance (Lt) measured at about 40
degrees from nadir, and sky radiance (Li) at about 40 degrees from zenith* **(Mobley 1999, Mueller et al. 2003 (NASA Protocols))**.
Unlike other approaches, HyperCP eliminates data flagged for problematic pitch/roll, yaw, and solar/sensor geometries
*prior* to deglitching the time series, thus increasing the relative sensitivity of deglitching for the removal of
non-environmental anomalies.


- **SunTracker**: Select when using an autonomous platform such as SolarTracker, pySAS, DALEC, or So-Rad. In this case sensor and solor geometry data will come from the robot. If deselected, solar geometries will be calculated from GPS time and
 position with Pysolar, while sensor azimuth (i.e. ship heading and sensor offset) must either be provided in the
 ancillary data or (eventually) from other data inputs. Currently, if SunTracker is unchecked, the Ancillary file
 chosen in the Main Window will be read in, subset for the relevant dates/times, held in the ANCILLARY_NOTRACKER group
 object, and carried forward to subsequent levels. If the ancillary data file is very large (e.g. for a whole cruise at high temporal resolution), this process of reading in the text file and subsetting it to the radiometry file can be slow.

- **Rotator Home Angle Offset**: Generally 0. This is the offset between the neutral position of the radiometer suite and
the bow of the ship. This *should* be zero if the SAS Home Direction was set at the time of data collection in the
SunTracker as per Satlantic SAT-DN-635. If no SunTracker was used, the offset can be set here if stable (e.g.
pointing angle on a fixed tower), or in the ancillary data file if changeable in time. Without SunTracker, L1C
processing will require at a minimum ship heading data in the ancillary file. Then the offset can be given in the
ancillary file (dynamic) or set here in the GUI (static). *Note: as SeaBASS does not have a field for this angle between
the instrument and the bow of the ship, the field "relaz" (normally reserved for the relative azimuth between the
instrument and the sun) is utilized for the angle between the ship heading (NOT COG) and the sensor.*

- **Rotator Delay**: Seconds of data discarded after a SunTracker rotation is detected. Set to 0 to ignore.
Not an option without SunTracker. **Default: 60 seconds (Vandenberg 2017)**

- **Pitch & Roll Filter** (optional): Data outside these thresholds are discarded if this is enabled in the checkbox.
These data may be supplied by a tilt-heading sensor incorporated in the raw data stream accompanied by a telmetry
definition file (.tdf) as per above, or can be ingested from the Ancillary file (see SAMPLE_Ancillary_pySAS.sb provided
in /Data).
    **Default**: 5 degrees (IOCCG Draft Protocols; Zibordi et al. 2019; 2 deg "ideal" to 5 deg "upper limit").

- **Absolute Rotator Angle Filter** (optional): Angles relative to the SunTracker neutral angle beyond which data will
be excluded due to obstructions blocking the field of view. These are generally set in the SunTracker
software when initialized for a given platform. Not an option without SunTracker.
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

Sea-Bird instruments intermittently collect dark current data in all pixels (wavebands) between light data collection with the use of an automatic shutter. Unlike legacy processing for Satlantic/Sea-Bird HyperSAS data in ProSoft, data here are dark-current-corrected prior to
application of the calibration factors. This allows the option of applying factory calibrations or full
instrument characterization in conjunction with low-level radiometric uncertainty estimation. It should be noted that
when applying calibration to the dark current corrected radiometry, the offsets (a0) cancel
(see ProSoftUserManual7.7 11.1.1.5 Eqns 5-6) presuming light and dark factory cals are equivalent (which they
historically have been from Satlantic/Sea-Bird).

TriOS and DALEC collect dark current data simultaneously with light data acquisition by reading from blackened pixels enumerated 
in their respective calibration files under the assumption that the dark current noise is similar across all pixels in the array.

### L1B: Ingestion of ancillary information for posterior processing

At Level 1B, critical ancillary information (wind speed, AOD, air temperature) that is not already provided in the Ancillary File (see [Main Window; Ancillary Data](README.md#3-ancillary-input-files)) will be queried from either [GMAO's MERRA](https://gmao.gsfc.nasa.gov/reanalysis/merra-2/)
or [ECMWF's CAMS GACF](https://ads.atmosphere.copernicus.eu/) reanalysis/forecast model databases and used in
posterior processing. To know more about these sources, how they are used in HyperCP and how to obtain the required
access credentials, read [here](README_ancillary.md). 

Fallback values for wind speed, AOD, air temperature, SST, and salinity can be provided in case neither ancillary file data nor model data are available.

### L1B: Calibration/Characterization options

The internal working temperature of each sensor is critical for thermal correction of the signal and/or uncertainty associated with thermal response. This temperature can be derived in several ways. For Sea-Bird, DALEC, and TriOS G2 sensors, an internal thermistor provides the working temperature. For TriOS G1, which has no thermistor, there are two options to derive working temperature: 1) Air temperature + 5°C (best for temperatures below 30°C) 2) Caps-on dark measurements (best for temperatures above 30°C) (Zibordi & Talone, 2025 in prep.) See note in Level 1A Processing [above](#configuration).

Three calibration/characterization regimes are available:

**Non-FRM Factory:**
This regime performs the radiometric calibration using the radiometric gains provided within the factory configuration
files. For Sea-Bird, TriOS, and DALEC, the calibration process follow their respective manufacturer recommendation.
Although no uncertainty values associated to the radiometric factors are currently available in the factory configuration files,
for Sea-Bird, uncertainty can be computed following the class-based processing with generic values for the radiometric
factor uncertainty, taken from "The Seventh SeaWiFS Intercalibration Round-Robin Experiment (SIRREX-7), March 1999"
(API: https://ntrs.nasa.gov/citations/20020045342). The uncertainties produced at level 2 date will not be FRM compliant
but remains an interesting first step to characterize the data. Unfortunately, there is no equivalent for TriOS or DALEC and no
uncertainties values will be outputted with this regime for TriOS or DALEC.

**FRM Class-Specific:**
This regimes performs the radiometric calibration using the radiometric characterization completed by external laboratories.
The radiometric characterization includes both the radiometric gains and their uncertainties for each sensor. The results
are saved in the so called "RADCAL" file, with one file per sensor. The calibration process is identical to the factory regime
and follow the manufacturer guidelines. In addition the Class-Specific regime also computes FRM uncertainties using the absolute
radiometric characterization and class-based values for all other contributors. The contributors included in the uncertainty
propagation are: the straylight impact, the temperature sensitivity, the polarisation sensitivity (for radiance only), the cosine
response (for irradiance only), the detector non-linearity and the calibration stability (see [this report](https://frm4soc2.eumetsat.int/sites/default/files/inline-files/FRM4SOC-2_D-10_v2.4_210042023_NPL_EUMETSAT_signed.pdf)).
Currently, the only classes characterized are Sea-Bird and TriOS.

**FRM Sensor-Specific (Full-Characterization; Highest Quality):**
This regime performs the complete correction of the radiometry using the full characterization of each sensor by external
laboratories. For both Sea-Bird and TriOS the radiometric calibration process is performed with additional corrections (DALEC in development). The
corrections are possible only thanks to the full characterization of the sensors provided in the matching files. The process
performs the non-linearity correction, the straylight correction, the polarisation correction (for radiance only), the cosine
response correction (for irradiance only) and the temperature correction (see [this report](https://frm4soc2.eumetsat.int/sites/default/files/inline-files/FRM4SOC-2_D-10_v2.4_210042023_NPL_EUMETSAT_signed.pdf)). 
The process also provides FRM compliant uncertainties accounting for the residuals effects of each contributors, meaning the correction residuals are used as uncertainty
contributor instead of global class-based contribution, leading to smaller uncertainty values.

There are three options for deciding which calibration files are applied when using FidRadDB RADCAL files (see Cal/Char options button under Config. Edit):

**Most recent prior to acquisition (default)**
Given the available RADCALs for each of the 3 individual radiometric sensors ivolved in the measurement (ES, LT, and LI),
HyperCP will select all 3 RADCALS whose calibration time stamp corresponds to the most recent one prior to the field
measurement acquisition. As an example, if you went to the field in March and had two pre-calibrations for ES done in January, 
February and then two post-calibrations done in August, and October, HyperCP will pick the February one. In the absence of
pre-calibrations, it will choose the closest post-calibration (August). The same criterion will be applied for LT (water)
and LI (sky)

**Pre- and Post- deployment average**
NB: This option is yet not implemented. This option will take user-specified pre-calibrations and post-calibrations and 
average them. Details of how this average will be done are pending scientific discussions.

**User specified**
This option simply takes specific calibration files selected by the user. The user must select 3 RADCALs, one for each sensor
ES, LT, and LI

**Multiple characterizations?**
In the very rare case in which Full FRM cal/char regime is selected and a specific radiometer (a specimen with a serial
number) was characterised several times for the same effect, HyperCP will always choose the most recent characterisation 
(regardless of the filed measurement acquisition time). An example would be an ES sensor which was chacarterised for 
internal straylight twice, in 2022 and 2025. Then, HyperCP will always consider the 2025 characterisation as the valid one.

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

    - **Cloud cover**:  Unusually high sky radiance to downelling irradiance ratio. Threshold in Ruddick et al. 2006 based
        on M99 models is <0.05 for clear sky where O(0.3) represents fully overcast.
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


## Level 2 Processing

Data are averaged within optional time interval ensembles prior to calculating the remote sensing
reflectance within each ensemble. A typical field collection file for the SunTracker is one hour, and the
optimal ensemble periods within that hour will depend on how rapidly conditions and water-types are changing, as well as
 the instrument sampling rate. While the use of ensembles is optional (set this to 0 to avoid averaging), it is highly
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

Remote sensing reflectance is then calculated as

$$
\displaystyle
Rrs = \frac{L_{t} - \rho_{sky}.L_{i}}{E_{s}} = \frac{L_{w}}{E_{s}},
$$

where $L_{w}$ is the water leaving radiance.

(e.g. Mobley 1999, Mueller et al. 2003, Ruddick et al. 2006)).
Normalized water leaving radiance (nLw) is calculated as $Rrs.F0$, where F0 is the top of atmosphere incident radiation
adjusted for the Earth-Sun distance on the day sampled. This is now estimated using the Coddington et al. (2021) TSIS-1
hybrid model.


Uncertainties in $L_{i}$, $L_{t}$, $E_{s}$ ($u(L_{i})$, $u(L_{t})$, $u(E_{s})$ ) are derived as the quadrature sum of uncertainties associated with standard error (i.e., variability among samples) and instrument uncertainties based on laboratory characterization of a specific instrument or class of instruments. Uncertainty in the skylight reflectance factor, $u(\rho_{sky})$, was historically estimated as +/- 0.003 from Ruddick et al. 2006 Appendix 2 (intended for clear skies), but in HyperCP v1.2+ is estimated using Monte Carlo iterations perturbing the input solar-sensor geometries and environmental conditions over normal distributions around the current measurement in addition to differences between multiple models for $\rho_{sky}$ (i.e., Mobley 1999 and Zhang et al. 2017).

Combined absolute standard uncertainty ( $u_{c}$) in $L_{w}$ ($u_{c}(L_{w})$ ) is estimated from $u(L_{i})$, $u(L_{t})$, and $u(\rho_{sky})$ with the Law of Propagation of Uncertainties (LPU) assuming random, uncorrelated error. LPU defines combined standard uncertainty, $u_{c}$ as:

$$
u^2_{c} = \Sigma_{i=0}^{N}[\frac{\partial f}{\partial x_{i}}]^2\cdot u(x_{i})^{2},
$$

where $\frac{\partial f}{\partial x_{i}}$ represents the sensitivity coefficients for the derived parameter $f$ as a function of the measurands $x_{i}$ used to calculate it. Water leaving radiance, $L_{w}$, is calculated as:

$$
L_{w} = L_{t} - \rho_{sky}\cdot L_{i}.
$$

The sensitivity coeficients in the equation above for $L_{w}$ are expressed as:

$$
\frac{\partial L_{w}}{\partial L_{t}} = 1
, 
\frac{\partial  L_{w}}{\partial \rho_{sky}} = -L_{i}
, 
\frac{\partial L_{w}}{\partial L_{i}} = -\rho_{sky}.
$$

Therefore, applying the LPU, uncertainty in $L_{w}$ can be stated as:

$$
u_{c}(L_{w}) = \sqrt{u(L_{t})^{2} + L_{i}^2\cdot u(\rho_{sky})^{2} + \rho_{sky}^{2}\cdot u(L_{i})^{2}}.
$$

$R_{rs}$ is defined as:

$$
R_{rs} = \frac{L_{w}}{E_{s}},
$$

so uncertainty in $R_{rs}$ is calculated as:

$$
u_{c}(R_{rs}) = \sqrt{u_{c}(L_{w})^{2} + u(E_{s})^{2}}.
$$

(Note that $L_{w}$ and $R_{rs}$ uncertainties are propagated separately to avoid a more complicated formulation
of the LPU.)

Since v1.2.0, uncertainties in L2 products include systematic and random sensor error in addition to uncertainties associated with the glint correction, environmental variability, BRDF correction (v1.2.2), and satellite band convolution. The full details of how HyperCP propagates these uncertainties can be found in
[this report](https://frm4soc2.eumetsat.int/sites/default/files/inline-files/FRM4SOC-2_D-10_v2.4_210042023_NPL_EUMETSAT_signed.pdf).

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

### BRDF correction

A correction factor for bi-directional effects (often called "BRDF correction") must be applied to "convert" the measured 
remote-sensing reflectance (or equivalently, the nomralised water-leaving radiance) from the given 
illumination-observation geometry to the "normalised" geometry (Sun at zenith, water-leaving radiance acquired at nadir). 

HyperCP supports two BRDF schemes:
- [Morel et al. 2002](https://opg.optica.org/ao/abstract.cfm?uri=ao-41-30-6289) (the so-called "Chlorophyll-based" approach), and
- [Lee et al. 2011](https://opg.optica.org/ao/fulltext.cfm?uri=ao-50-19-3155&id=219080) (the so-called "IOP-based" apprach)

The Python module to calculate the BRDF scheme was developed as part of 
[this](https://www.eumetsat.int/brdf-correction-s3-olci-water-reflectance-products) Copernicus Programme - EUMETSAT study.

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

