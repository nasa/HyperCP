# HyperInSPACE 

HyperInSPACE is designed to provide Hyperspectral In situ Support for the PACE mission by processing
automated, above-water, hyperspectral radiometry collected with Satlantic HyperSAS SolarTracker instruments.

Author: Dirk Aurin, USRA @ NASA Goddard Space Flight Center (dirk.a.aurin@nasa.gov)

Acknowledgements: Nathan Vandenberg (PySciDON; https://ieeexplore.ieee.org/abstract/document/8121926)

## Version
1.0.a 
---
'''
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
'''
---

## Requirements and Installation

Requires that the Anaconda distribution of Python 3.X is installed on your Linux, MacOS, or Windows computer.

*{If upgraded to include model retrievals of ancillary data (i.e. getanc.py), the OCCSW package will become an additional requirement}*

Save this entire HyperInSPACE repository to a convenient directory on your computer.

HyperInSPACE is a Main-View-Controller package that can be launched in several ways to compile the Main.py module,
such as by navigating to the program folder on the command line and using the following command:
'''
**prompt$** python Main.py
'''

The following folders will be created automatically when you first run the program:    
- Config - Configuration and instrument files (by subdirectory - auto-created), SeaBASS configuration files
- Data - Optional location for input and/or output data
- Logs - Most command line output messages are captured for later reference in .log text files here
- Plots - A variety of optional plotting routines are included, some of which create name-appropriate sub-
directories (e.g. 'L3', 'L4_Rrs', etc.)


## Guide

### Configuration

Under "Select/Create Configuration File", click "New" to create a new HyperInSPACE configuration file. This file will be 
instrument-specific, and is usually also deployment-specific. Select the new configuration file from the drop-down menu. 
Configuration files are saved in the 'Config' subdirectory, and can be edited, saved, and deleted.

In the "Edit Config" window, click "Add Calibration Files" to add the calibration files that were from the extracted 
Satlantic '.sip' file (i.e. '.cal' and '.tdf' files). The currently selected calibration file can be selected using the 
drop-down menu. Select the calibration files that correspond to the data you want to process with this configuration. 
Copies of the calibration files will be made and saved in a subdirectory of 'Config' named after you configuration file.

For each calibration file:
Click "Enable" to enable the calibration file. Select the frame type used for dark data correction, light data, or 
"Not Required" for navigational and ancillary data. Each radiometer will require two calibration files (light and dark).
Data from the GPS and SATNAV instruments will also be required with corresponding '.tdf' files.

Level 1A through Level 4 processing configurations is set in this window. These values will depend on your viewing 
geometry and quality control thresholds. Level 2 includes a tool to assist with data deglitching parameters ("Anomaly 
Analysis"). More details with citations and default setting descriptions are given below.

Click "Save" or "Save As" to save the settings. A file will be created in the Config subdirectory, together with copies 
of the instrument (calibration) files for later use.

### Processing

You will need to set your 'Input Data' and 'Output Data' directories from the Main window. Note that output subdirectories 
for particular processing levels (i.e. "L1A", ... "L4") will be created automatically within your output directory. 

Process the data by clicking on one of the buttons for single-level or multi-level processing. Multiple data files can be
processed at once (in succession) by selecting them together in the dialog box. Processing levels are described below.


## Overview ###

### Main Window

The Main window appears once HyperInSPACE is launched. It has options to specify a configuration file, input/output 
directories, ancillary input files (e.g. wind file), single-level processing, and multi-level processing.

The New button allows creation of a new config file. Edit allows editing the currently selected config file. Delete can be used to delete the currently selected config file.

The Input/Output Data Directory buttons allow selection of data directories. Note that output data sub-
directories are also auto-created as described below.

*{To Do: Save last-used values for Config File, Input, Output, and Met file in a .config for convenience when re-launching.}*

Ancillary files for meteorologic conditions should be text files in SeaBASS format with columns for date, time, lat, and lon.
See https://seabass.gsfc.nasa.gov/ for a description of SeaBASS format. It is recommended that ancillary files are checked 
with the 'FCHECK' utility as described on the SeaBASS website. 

The most important ancillary parameter is wind for use in sea-surface skylight reflectance calculations (L4). 

*{To Do: allow for getanc.py option to obtain model wind data and AOD.}*


### Config File

A configuration file needs to be created or selected prior to processing to specify the configuration HyperInSPACE 
should use when processing the data. The configuration files are saved to ./Config with a .cfg extension. 

### Edit Config Window

This window allows editing all the HyperInSPACE configuration file options including:

### Calibration Files:

-Add Calibration Files - Allows loading calibration files (.cal/.tdf) into HyperInSPACE. Once loaded the drop-down 
box can be used to select the calibration file. 
-Enabled checkbox - Used to enable/disable loading the calibration file in HyperInSPACE.
-Frame Type - ShutterLight/ShutterDark/Not Required/LightAncCombined can be selected. This is mainly used to specify 
frame type (ShutterLight/ShutterDark) for dark correction, the other options are unused.

Calibration files are copied from their selected locations into the ./Config directory within an automatically created sub-directory named after the configuration (i.e. KORUS.cfg results in ./Config/KORUS_Calibration/calfiles... once calibration files have been added).

#### Level 1A - Preprocessing

Process data from raw binary ('.RAW' collections) to L1A (Hierarchical Data Format 5 '.hdf'). Calibration files and RawFileReader.py allow for interpretation of raw data fields, which are read into HDF objects.

Solar Zenith Angle Filter: prescreens data for high SZA (low solar elevation) to exclude files which may have been
collected post-dusk or pre-dawn from further processing. Triggering the SZA threshold will skip the entire file.  
**Default: 60 degrees (e.g. Brewin et al., 2016)**

#### Level 1B

Process data from L1A to L1B. Data are filtered for vessel attitude, viewing and solar geometry, 
and then processed from raw counts to calibrated radiances/irradiances using the factory calibration files. It should be noted that viewing geometry should conform to total irradiance measured at 40 degrees from nadir, and sky radiance from 40 degrees from zenith **(Mobley 1999)**.

Rotator Home Angle: The offset between the neutral position of the SolarTracker unit and the bow of the ship. This
/should/ be zero if the SAS Home Direction was set at the time of data collection as per Satlantic SAT-DN-635.** 

*{\*\*Still waiting to hear from Satlantic about how this value gets tweaked and recorded in the raw data during*
*instrument set-up. Also, from page D-19, which heading sensor was used during data collection.}*

Rotator Delay: Seconds of data discarded after a SAS rotation is detected.  
**Default: 60 seconds (Vandenberg 2016)**

Pitch & Roll Filter (optional): Data outside these thresholds are discarded if this is enabled in the checkbox.  
**Default 5 degrees (IOCCG Draft Protocols; Zibordi et al. 2019; 2 deg "ideal" to 5 deg "upper limit")**


Relative Solar Azimuth Filter (optional): Relative angle in degrees between the viewing Li/Lt and the sun.  
**Default: 90-135 deg (Mobley 1999, Zhang et al. 2017); 90 deg unless certain of platform shadow (Zibordi et al. 2009, IOCCG Draft Protocols)**

#### Level 2

Process data from L1B to L2. Light and dark data are screened for electronic noise ("deglitched" - see Anomaly 
Analysis), which are then removed from the data (optional). Shutter dark samples are the subtracted from shutter lights after dark data have been interpolated in time to match light data.  
**(e.g. Brewin et al. 2016, Sea-Bird/Satlantic 2017)**

##### Anomaly Analysis (optional)

Deglitching the data is highly sensitive to the deglitching parameters described below, as well as environmental 
conditions and the variability of the radiometric data itself. Therefore, a seperate module was developed to 
tune these parameters for individual files, instruments, and/or field campaigns. The tool is launched by setting 
the parameters (windows and sigma factors described below) in the Configuration window, SAVING THE CHANGES, and then running the 
tool on an example of L1B data using the Anomaly Analysis button. Plots produced automatically in the ./Plots/L1B_Anoms directory can be used to evaluate the choice of parameters.

For each waveband of each sensor, and for both light and dark shutter measurements, the time series of radiometric
data are low-pass filtered with a moving average using discrete linear convolution of two one dimensional 
sequences with adjustable window sizes. For darks, a stationary standard deviation anomaly (from 
the moving average) is used to assess whether data are within an adjustable "sigma factor" multiplier within the window. For lights, 
a MOVING standard deviation anomaly (from the moving average of seperately adjustable window size) is used 
to assess whether data are within a seperately adjustable sigma. The low-band filter is passed over the
data twice. First and last data points for light and dark data cannot be accurately filtered with this method, 
and are discarded.  
**(Abe et al. 2006, Chandola et al. 2009)**  
**(e.g. API Reference: https://docs.scipy.org/doc/numpy/reference/generated/numpy.convolve.html**

#### Level 3

Process data from L2 to L3. Interpolates radiometric data to common timestamps and wavebands, optionally generates spectral
plots of Li, Lt, and Es, and optionally outputs text files containing the data and metadata for submission
to the SeaWiFS Bio-optical Archive and Storage System (SeaBASS; https://seabass.gsfc.nasa.gov/)

Each HyperOCR collects data at unique time intervals and requires interpolation for inter-instrument comparison. Satlantic ProSoft 7.7 software interpolates radiometric data between radiometers using the OCR with the fastest sampling rate (Sea-Bird 2017), but here we use the timestamp of the slowest-sampling radiometer (typically Lt) to minimize perterbations in interpolated data (i.e. interpolated data are always closer in time to actual sampled data) **(Brewin et al. 2016, Vandenberg 2017)**. Each HyperOCR radiometer collects data in a unique set of wavebands nominally at 3.3 nm resolution. For merging, they must be interpolated to common wavebands. Interpolating to a different (i.e. lower) spectral resolution is also an option. No extrapolation is calculate (i.e. interpolation is between the global minimum and maximum 
spectral range for all HyperOCRs). Spectral interpolation is by univariate spline with a smoothing factor of 3.
**https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.UnivariateSpline.html**

*{TO DO: Include selections for various ocean color sensor bands and use spectral response functions from those instruments to interpolate HyperSAS data spectrally to those wavebands.}*

A linked module allows the user to collect all of the information from the data being processed and the processing configuration as defined in the Configuration window for use in automatically creating SeaBASS headers. The module is launched by selecting the New, Open, or Edit buttons to create, select, or edit a SeaBASS header configuration file, which is automatically stored in the ./Config directory with a .hdr extension. Instructions are given at the top of the new SeaBASS Header window that pops up. Within the SeaBASS Header module, the left column allows the user to input the fields required by SeaBASS. Calibration files (if they have been added at the time of creation) are auto-populated. On the right hand column, additional header fields can be auto-populated or updated from the Configuration window, or from the data files as they are processed. To override auto-population of fields, enter the desired value here in the SeaBASS Header window.

**When updating values in the Configuration window, be sure to apply those updates in the SeaBASS Header by editing the header through the module, and selecting the "Update from Config Window" button.**

#### Level 4 - Rrs Calculation

Process L3 to L4. Further quality control filters are applied to data, and data are average into optional time interval bins prior to calculating the remote sensing reflectance within each bin (or at each sample).  

Prior to binning, data may be filtered for Maximum Wind Speed.  
**Default 15 m/s (Zibordi et al. 2009); 7 m/s (IOCCG Draft Protocols 2019; D'Alimonte pers.comm 2019)**

Solar Zenith Angle may be filtered for minimum and maximum values.  
**Default Min: 20 deg (Zhang et al 2017); Default Max: 60 deg (Brewin et al. 2016)**

Time Average Interval can be set to the user's requirements. Setting this to avoids temporal binning, using the common timestamps established in L3.

Data are optionally limited to the lowest (e.g.5%) of Lt data at 780 nm within the sampling interval, if binning is performed to minimize the effects of glint reflection off waves **(Hooker et al. 2002, Hooker and Morel 2003)**.

The default value for sea-surface reflectance (rho_sky) is set to 0.0256 based on **(Morel 1999)**, which can be optionally adjusted for wind speed and cloud cover using the relationship found in **(Ruddick et al. 2006)**. The default wind speed should be set by the user depending on field conditions for instances when the ancillary data and models are not available. 

*{TO DO: encode the Zhang et al. 2017 approach in Python to calculate a spectrally dependent, polarization-sensitive rho_sky. Matlab code was provided by Zhang, along with permission to distribute. This will also require an estimate of aerosol optical thickness, so adding getanc.py with AOD would be required.}*

Meteorological flags based on **(Wernand et al. 2002, Garaba et al. 2012, Vandenberg 2017)** can be optionally applied to screen for undesirable data. Specifically, data are filtered for unusually low downwelling irradiance at 480 nm (default 2.0 uW cm^-2 nm^-1, for data likely to have been collected near dawn or dusk (Es(470)/Es(680) < 1.0), and for data likely to have high relative humidity or rain (Es(720)/Es(370) < 1.095).

*{TO DO: Include a bidirectional correction to Lw based on, e.g. }
Remote sensing reflectance is calculated as Rrs = (Lt - rho_sky* Li) / Es (e.g. **(Mobley 1999)**). 

Additional sun glint can be optionally removed from the Rrs by subtracting the value in the NIR from the entire spectrum **(Mueller et al. 2003)**. This approach, however, assumes neglible water-leaving radiance in the 750-800 nm range, and ignores the spectral dependence in sky glint, and should therefore only be used in the clearest waters with caution. Here, a minimum in Rrs(750-800) is found and subtracted from the entire spectrum.

*{TO Do: The NIR dark-pixel subtraction is bogus, and should be eliminated in favor of a more robust glint correction above (e.g. Zhang et al 2017)}*


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
