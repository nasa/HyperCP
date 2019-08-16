# HyperInSPACE 

HyperInSPACE is designed to provide Hyperspectral In situ Support for the PACE mission by processing automated, above-water, hyperspectral ocean color radiometry collected on automated platforms with Satlantic HyperSAS SolarTracker instruments.

Author: Dirk Aurin, USRA @ NASA Goddard Space Flight Center (dirk.a.aurin@nasa.gov)  
Acknowledgements: Nathan Vandenberg (PySciDON; https://ieeexplore.ieee.org/abstract/document/8121926)

## Version
1.0.a 
---
```
                 NASA Goddard Space Flight Center (GSFC) 
         Software distribution policy for Public Domain Software

 The HyperInSPACE code is in the public domain, available without fee for 
 educational, research, non-commercial and commercial purposes. Users may 
 distribute this code to third parties provided that this statement appears
 on all copies and that no charge is made for such copies.

 NASA GSFC MAKES NO REPRESENTATION ABOUT THE SUITABILITY OF THE SOFTWARE
 FOR ANY PURPOSE. IT IS PROVIDED "AS IS" WITHOUT EXPRESS OR IMPLIED
 WARRANTY. NEITHER NASA GSFC NOR THE U.S. GOVERNMENT SHALL BE LIABLE FOR
 ANY DAMAGE SUFFERED BY THE USER OF THIS SOFTWARE.
```
---

## Requirements and Installation

Requires that the Anaconda distribution of Python 3.X is installed on a Linux, MacOS, or Windows computer.

*{If upgraded to include model retrievals of ancillary data (i.e. getanc.py), the OCCSW package will become an additional requirement}*

Save this entire HyperInSPACE file repository to a convenient directory on your computer.

HyperInSPACE is a Main-View-Controller package that can be launched in several ways to compile the Main.py module,
such as by navigating to the program folder on the command line and typing the following command:
```
**prompt$** python Main.py
```

The following folders will be created automatically when you first run the program:    
- Config - Configuration and instrument files (by subdirectory - auto-created), SeaBASS header configuration files
- Data - Optional location for input and/or output data, and some ancillary data required for the program
- Logs - Most command line output messages are captured for later reference in .log text files here
- Plots - A variety of optional plotting routines are included, some of which create name-appropriate sub-
directories (e.g. 'L1B_Anoms', 'L3', 'L4_Rrs', etc.)

## Guide

### Main Window

The Main window appears once HyperInSPACE is launched. It has options to specify a configuration file, input/output 
directories, ancillary input files (e.g. wind file), single-level processing, and multi-level processing.

The 'New' button allows creation of a new configuration file. 'Edit' allows editing the currently selected config file. 'Delete' is used to delete the currently selected configuration file and corresponding auto-created calibration directories (see Configuration). When creating a new configuration file, select the new configuration file from the drop-down menu after naming it, and select 'Edit' to launch the Configuration module and GUI. Configuration files are saved in the './Config' subdirectory of HyperInSPACE.

The 'Input-' 'Output Data Directory' buttons allow optional selection of data directories from any mounted/mapped drive. Note that output data sub-directories are also auto-created as described below. If no input or output data directories are selected, './Data' under HyperInSPACE will be used by default.

*{To Do: Save last-used values for Config File, Input, Output, and Met file from the Main window in a .config for convenience when re-launching on the same machine.}*

Ancillary files for meteorologic conditions should be text files in SeaBASS format with columns for date, time, lat, and lon.
See https://seabass.gsfc.nasa.gov/ for a description of SeaBASS format. It is recommended that ancillary files are checked 
with the 'FCHECK' utility as described on the SeaBASS website. They will be interpreted using the included SB_support.py module.

The most important ancillary parameter is wind speed (in m/s) for use in sea-surface skylight reflectance calculations (see Level 4). 

*{To Do: allow for getanc.py option to obtain model wind data and AOD.}*

### Configuration

Launch the configuration module and GUI (ConfigWindow.py) from the Main window by selecting a configuration file or creating a new one. This file will be instrument-suite-specific, and is usually also deployment-specific according to which factory calibration files are needed, as well as how the instrument was configured on the platform or ship. 

*{Possible To Do: Interpolate values between cals?}*

##### Calibration Files:
In the 'Configuration' window, click 'Add Calibration Files' to add the calibration files that were from the relevant extracted 
Satlantic '.sip' file (i.e. '.cal' and '.tdf' files). The calibration file can be selected using the drop-down menu. Select the calibration files that correspond to the data you want to process with this configuration. You will need to know which .cal files correspond to each sensor, and which represent light and dark shutter measurements. For example,
- HEDXXXX.cal > Es Dark
- HSEXXXX.cal > Es Light
- HLDYYYY.cal > Li Dark
- HSLYYYY.cal > Li Light
- HLDZZZZ.cal > Lt Dark
- HSLZZZZ.cal > Lt Light

Selections:  
-Add Calibration Files - Allows loading calibration files (.cal/.tdf) into HyperInSPACE. Once loaded the drop-down 
box can be used to select the calibration file. 
-Enabled checkbox - Used to enable/disable loading the calibration file in HyperInSPACE.
-Frame Type - ShutterLight/ShutterDark/Not Required/LightAncCombined can be selected. This is mainly used to specify 
frame type (ShutterLight/ShutterDark) for dark correction, the other options are unused.

For each calibration file:  
Click 'Enable' to enable the calibration file. Select the frame type used for dark data correction, light data, or 
'Not Required' for navigational and ancillary data. Each radiometer will require two calibration files (light and dark).
Data from the GPS and SATNAV instruments is interpreted using the corresponding, required '.tdf' files.

Calibration files are copied from their selected locations into the ./Config directory within an automatically created sub-directory named after the configuration (i.e. KORUS.cfg results in ./Config/KORUS_Calibration/calfiles... once calibration files have been added).

Level 1A through Level 4 processing configurations are adjusted in the Configuration window, and it is a good reference to accompany the discussion below regarding processing levels. *The values set in the configuration file should be considered carefully, as they will depend on your viewing geometry and desired quality control thresholds.* Level 2 includes a module which can be launched from the Configuration window to assist with data deglitching parameter selection ('Anomaly Analysis'). More details with citations and default setting descriptions are given below. A seperate module to assist in the creation of SeaBASS output files is launched in Level 3 processing, and applied to L3 and L4 SeaBASS output as described below.

Click 'Save' or 'Save As' to save the configuration file. The configuration files are saved to the ./Config directory under the HyperInSPACE main directory with a .cfg extension. 

### Processing Overview

Again, it is helpful (though not required) to set your 'Input Data' and 'Output Data' directories from the Main window. If not selected, these will default to the ./Data directory within HyperInSPACE. Note that output subdirectories for particular processing levels (i.e. 'L1A', ... 'L4') will be created automatically within your output directory as appropriate. 

Process the data by clicking on one of the buttons for single-level or multi-level processing. A file selection dialogue will appear. Multiple data files can be processed at once (in succession) by selecting them together in the GUI. Multi-level processing works the same as single-level, by processing each input raw file through all levels before moving on to the next file. However, it will only continue with a file if the preceding level was created immediately prior. In other words, if -- due to changes in QA/QC parameterization -- a file is entirely discarded at a given level, but an old file of the same name still exists in that directory, it will be ignored, and processing for that file will be terminated for higher levels. 

#### Level 1A - Preprocessing

Process data from raw binary ('.RAW' collections) to L1A (Hierarchical Data Format 5 '.hdf'). Calibration files and RawFileReader.py allow for interpretation of raw data fields, which are read into HDF objects.

**Solar Zenith Angle Filter**: prescreens data for high SZA (low solar elevation) to exclude files which may have been
collected post-dusk or pre-dawn from further processing. Triggering the SZA threshold will skip the entire file.  
**Default: 60 degrees (e.g. Brewin et al., 2016)**

#### Level 1B

Process data from L1A to L1B. Data are filtered for vessel attitude (pitch and roll), viewing and solar geometry, 
and then processed from raw counts to calibrated radiances/irradiances using the factory calibration files. *It should be noted that viewing geometry should conform to total radiance (Lt) measured at 40 degrees from nadir, and sky radiance (Li) from 40 degrees from zenith* **(Mobley 1999)**.

**Rotator Home Angle**: The offset between the neutral position of the SolarTracker unit and the bow of the ship. This
/should/ be zero if the SAS Home Direction was set at the time of data collection as per Satlantic SAT-DN-635.** 

*{\*\*Still waiting to hear from Satlantic about how this value gets tweaked and recorded in the raw data during instrument set-up. Also, from page D-19 of SolarTracker manual, which heading sensor was used during data collection.}*

**Rotator Delay**: Seconds of data discarded after a SAS rotation is detected.  
**Default: 60 seconds (Vandenberg 2016)**

**Pitch & Roll Filter** (optional): Data outside these thresholds are discarded if this is enabled in the checkbox.  
**Default 5 degrees (IOCCG Draft Protocols; Zibordi et al. 2019; 2 deg "ideal" to 5 deg "upper limit")**


**Relative Solar Azimuth Filter** (optional): Relative angle in degrees between the viewing Li/Lt and the sun.  
**Default: 90-135 deg (Mobley 1999, Zhang et al. 2017); 90 deg unless certain of platform shadow (Zibordi et al. 2009, IOCCG Draft Protocols)**

#### Level 2

Process data from L1B to L2. Light and dark data are screened for electronic noise ("deglitched" - see Anomaly 
Analysis), which are then removed from the data (optional). Shutter dark samples are then subtracted from shutter lights after dark data have been interpolated in time to match light data.  
**(e.g. Brewin et al. 2016, Sea-Bird/Satlantic 2017)**

*{To Do: discard dark data outside thresholds as hinted at in Zibordi 2009 (no actual threshold or methods given)}*

##### Anomaly Analysis (optional)

Deglitching the data is highly sensitive to the deglitching parameters described below, as well as environmental 
conditions and the variability of the radiometric data itself. Therefore, a seperate module was developed to 
tune these parameters for individual files, instruments, and/or field campaigns. The tool is launched by setting 
the parameters (windows and sigma factors described below) in the Configuration window, *SAVING THE CHANGES*, and then running the tool on an example of L1B data using the Anomaly Analysis button and file dialog. Plots produced automatically in the ./Plots/L1B_Anoms directory can be used to evaluate the choice of parameters.

For each waveband of each sensor, and for both light and dark shutter measurements, the time series of radiometric
data are low-pass filtered with a moving average using discrete linear convolution of two one dimensional 
sequences with adjustable window sizes. For darks, a stationary standard deviation anomaly (from 
the moving average) is used to assess whether data are within an adjustable "sigma factor" multiplier within the window. For lights, a MOVING standard deviation anomaly (from the moving average of seperately adjustable window size) is used 
to assess whether data are within a seperately adjustable sigma. The low-band filter is passed over the
data twice. First and last data points for light and dark data cannot be accurately filtered with this method, 
and are discarded.  
**Defaults: Dark Window 11, Light Window 9, Dark Sigma 2.7, Light Sigma 3.7 determined empirically from KORUS cruise**
**(Abe et al. 2006, Chandola et al. 2009)**  
**(API Reference: https://docs.scipy.org/doc/numpy/reference/generated/numpy.convolve.html)**

Time-series plots of Es, Li, and Lt showing the results of the anomaly detection are saved to ./Plots/L3_Anoms. Data flagged for removal given the parameterizations chosen in the Configuration window are shown for the filter first pass (red box) and second pass (blue star). Review of these plots and adjustment of the parameters allow the user to optimize the low-pass filter for a given instrument and collection environment. 

#### Level 3

Process data from L2 to L3. Interpolates radiometric data to common timestamps and wavebands, optionally generates spectral
plots of Li, Lt, and Es, and optionally outputs text files containing the data and metadata for submission
to the SeaWiFS Bio-optical Archive and Storage System (SeaBASS; https://seabass.gsfc.nasa.gov/)

Each HyperOCR collects data at unique time intervals and requires interpolation for inter-instrument comparison. Satlantic ProSoft 7.7 software interpolates radiometric data between radiometers using the OCR with the fastest sampling rate (Sea-Bird 2017), but here we use the timestamp of the slowest-sampling radiometer (typically Lt) to minimize perterbations in interpolated data (i.e. interpolated data in HyperInSPACE are always closer in time to actual sampled data) **(Brewin et al. 2016, Vandenberg 2017)**. Each HyperOCR radiometer collects data in a unique set of wavebands nominally at 3.3 nm resolution. For merging, they must be interpolated to common wavebands. Interpolating to a different (i.e. lower) spectral resolution is also an option. No extrapolation is calculated (i.e. interpolation is between the global minimum and maximum spectral range for all HyperOCRs). Spectral interpolation is by univariate spline with a smoothing factor of 3.
**(API: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.UnivariateSpline.html)**

Optional spectral plots of Es, Li, and Lt of L3 data can be generated. They are saved in ./Plots/L3.

*{TO DO: Include selections for various ocean color sensor bands, and use spectral response functions from those instruments to weight HyperSAS data spectrally to those wavebands.}*

##### SeaBASS File and Header

To output SeaBASS formatted text files, check the box. A subfolder within the L3 directory will be created, and seperated files made for Li, Lt, and Es hyperspectral data.

A linked module allows the user to collect all of the information from the data being processed and from the processing configuration (as defined in the Configuration window) for use in automatically creating SeaBASS headers and data files. The module is launched by selecting the New, Open, or Edit buttons in the Configuration window to create, select, or edit a SeaBASS header configuration file, which is automatically stored in the ./Config directory with a .hdr extension. Instructions are given at the top of the new SeaBASS Header window that launches when the Edit button is pressed. Within the SeaBASS Header window, the left column allows the user to input the fields required by SeaBASS. Calibration files (if they have been added at the time of creation) are auto-populated. In the right hand column, additional header fields can be auto-populated or updated from the Configuration window additional comments can be added, and the lower fields are autopopulated from each data file as it is processed. To override auto-population of fields, enter the desired value here in the SeaBASS Header window, and save it.


**When updating values in the Configuration window, be sure to apply those updates in the SeaBASS Header by editing the header through the module, selecting the 'Update from Config Window' button, and saving the header file.**

#### Level 4 - Rrs Calculation

Process L3 to L4. Further quality control filters are applied to data, and data are average into optional time interval bins prior to calculating the remote sensing reflectance within each bin (or at each sample).  

Prior to binning, data may be filtered for **Maximum Wind Speed**.  
**Default 15 m/s (Zibordi et al. 2009); 7 m/s (IOCCG Draft Protocols 2019; D'Alimonte pers.comm 2019)**

**Solar Zenith Angle** may be filtered for minimum and maximum values.  
**Default Min: 20 deg (Zhang et al 2017); Default Max: 60 deg (Brewin et al. 2016)**

**Spectral Outlier Filter** may be applied to remove noisy data prior to binning. This simple filter examines only the spectrum of Es, Li, and Lt from 400 - 700 nm, above which the data are extremely noisy. Using the standard deviation of the normalized spectra for the entire sample ensemble, together with a multiplier to establish an envelope, spectra with data outside the envelop in any band are rejected. Currently, the arbitrary filter factors are 5.0 for Es, 8.0 for Li, and 3.0 for Lt. Results of spectral filtering are saved as spectral plots in ./Plots/L4_Spectral_Filter.

*{To Do: Improve this filter and/or include the sigmas as adjustables in the GUI as per Anom. Anal.}*

**Time Average Interval** can be set to the user's requirements. Setting this to avoids temporal binning, using the common timestamps established in L3.

Data are optionally limited to the lowest (e.g. 5% default) of Lt data at 780 nm within the sampling interval (if binning is performed) to minimize the effects of glint reflection from surface waves **(Hooker et al. 2002, Hooker and Morel 2003)**.

The default value for sea-surface reflectance (**Rho_sky**) is set to 0.0256 based on **(Morel 1999, Mueller et al. 2003)**, which can be optionally adjusted for wind speed and cloud cover using the relationship found in **(Ruddick et al. 2006)**. The default wind speed should be set by the user depending on in situ conditions for instances when the ancillary data and models are not available. This correction does not account for the spectral dependence or polarization sensitivity in Rho_sky.

*{TO DO: encode the Zhang et al. 2017 approach in Python to calculate a spectrally dependent, polarization-sensitive rho_sky. Matlab code was provided by Zhang, along with permission to distribute. This will also require an estimate of aerosol optical thickness, so adding getanc.py with AOD would be required.}*

**Meteorological flags** based on **(Wernand et al. 2002, Garaba et al. 2012, Vandenberg 2017)** can be optionally applied to screen for undesirable data. Specifically, data are filtered for unusually low downwelling irradiance at 480 nm (default 2.0 uW cm^-2 nm^-1, for data likely to have been collected near dawn or dusk (Es(470)/Es(680) < 1.0), and for data likely to have high relative humidity or rain (Es(720)/Es(370) < 1.095).

*{TO DO: Include a bidirectional correction to Lw based on, e.g. Lee 2011, Zibordi 2009}*

Remote sensing reflectance is calculated as Rrs = (Lt - rho_sky* Li) / Es (e.g. **(Mobley 1999, Mueller et al. 2003, Ruddick et al. 2006)**). 

Additional sun glint can be optionally removed from the Rrs by subtracting the value in the NIR from the entire spectrum **(Mueller et al. 2003)**. This approach, however, assumes neglible water-leaving radiance in the 750-800 nm range (not true of turbid waters), and ignores the spectral dependence in sky glint, and should therefore only be used in the clearest waters with caution. Here, a minimum in Rrs(750-800) is found and subtracted from the entire spectrum.

*{TO Do: The NIR dark-pixel subtraction is bogus, and should be eliminated in favor of a more robust glint correction above (e.g. Zhang et al 2017)}*

To output SeaBASS formatted text files, check the box. A subfolder within the L4 directory will be created, and seperated files made for Li, Lt, Es, and Rrs hyperspectral data.

Optional 


## References
- Abe, N., B. Zadrozny, et al. (2006). Outlier detection by active learning. Proceedings of the 12th ACM SIGKDD international conference on Knowledge discovery and data mining. Philadelphia, PA, USA, ACM: 504-509.
- Brewin, R. J. W., G. Dall'Olmo, et al. (2016). "Underway spectrophotometry along the Atlantic Meridional Transect reveals high performance in satellite chlorophyll retrievals." Remote Sensing of Environment 183: 82-97.
- Chandola, V., A. Banerjee, et al. (2009). "Anomaly detection: A survey." ACM Comput. Surv. 41(3): 1-58.
- Garaba, S. P., J. Schulz, et al. (2012). "Sunglint Detection for Unmanned and Automated Platforms." Sensors 12(9): 12545.
- Hooker, S. B., G. Lazin, et al. (2002). "An Evaluation of Above- and In-Water Methods for Determining Water-Leaving Radiances." Journal of Atmospheric and Oceanic Technology 19(4): 486-515.
- Hooker, S. B. and A. Morel (2003). "Platform and Environmental Effects on Above-Water Determinations of Water-Leaving Radiances." Journal of Atmospheric and Oceanic Technology 20(1): 187-205.
- Mobley, C. D. (1999). "Estimation of the remote-sensing reflectance from above-surface measurements." Applied Optics 38(36): 7442-7455.
- Mueller, J. L., A. Morel, et al. (2003). Ocean Optics Protocols for Satellite Ocean Color Sensor Validation, Revision 4, Volume III. Ocean Optics Protocols for Satellite Ocean Color Sensor Validation. J. L. Mueller. Greenbelt, MD, NASA Goddard Space Flight Center.
- Ruddick, K. G., V. De Cauwer, et al. (2006). "Seaborne measurements of near infrared water-leaving reflectance: The similarity spectrum for turbid waters." Limnology and Oceanography 51(2): 1167-1179.
- Sea-Bird Scientific (2017). Prosoft 7.7 Product Manual SAT-DN-00228 Rev. K.
- Vandenberg, N., M. Costa, et al. (2017). PySciDON: A python scientific framework for development of ocean network applications. 2017 IEEE Pacific Rim Conference on Communications, Computers and Signal Processing (PACRIM).
- Wernand, M. R. (2002). Guidelines for (ship-borne) auto-monitoring of coastal ocean colour. Ocean Optics XVI, Sante Fe, NM, The Oceanography Society.
- Zhang, X., S. He, et al. (2017). "Spectral sea surface reflectance of skylight." Optics Express 25(4): A1-A13.
- Zibordi, G., F. Mélin, et al. (2009). "AERONET-OC: A Network for the Validation of Ocean Color Primary Products." Journal of Atmospheric and Oceanic Technology 26(8): 1634-1651.
- Zibordi, G. and K. J. Voss (2019). Protocols for Satellite Ocean Color Data Validation (DRAFT). I. O. C. C. Group.
