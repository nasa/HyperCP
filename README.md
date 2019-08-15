# HyperInSPACE 

HyperInSPACE is designed to provide Hyperspectral In situ Support for the PACE mission by processing
automated, above-water, hyperspectral radiometry collected with Satlantic HyperSAS SolarTracker instruments.

Author: Dirk Aurin, USRA @ NASA Goddard Space Flight Center
Acknowledgements: Nathan Vanderberg (PySciDON; https://ieeexplore.ieee.org/abstract/document/8121926)
Release Version: 1.0.a August 2019
/*=====================================================================*/
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
/*=====================================================================*/
---

## Installation

Requires the Anaconda distribution of Python 3.X

Save this entire HyperInSPACE repository to a convenient directory on your computer.

HyperInSPACE is a Main-View-Controller package that can be launched in several ways to compile the Main.py module,
such as by navigating to the program folder on the command line and using the following command:
$ python Main.py

The following folders will be created automatically when you first run the program:    
    Config - Configuration and instrument files (by subdirectory - auto-created), SeaBASS configuration files
    Data - Optional location for input and/or output data
    Logs - Most command line output messages are captured for later reference in .log text files here
    Plots - A variety of optional plotting routines are included, some of which create name-appropriate sub-
            directories (e.g. 'L3', 'L4_Rrs', etc.)


## Guide ###

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

The New button allows creation of a new config file.
Edit allows editing the currently selected config file.
Delete can be used to delete the currently selected config file.

The Input/Output Data Directory buttons allow selection of data directories. Note that output data sub-
directories are also auto-created as described below.

*{To Do: Save last-used values for Config File, Input, Output, and Met file in a .config}*

Ancillary files for meteorologic conditions should be text files in SeaBASS format with columns for date, time, lat, and lon.
See https://seabass.gsfc.nasa.gov/ for a description of SeaBASS format. It is recommended that ancillary files are checked 
with the 'FCHECK' utility as described on the SeaBASS website. 

The most important ancillary parameter is wind for use in sea-surface skylight reflectance calculations (L4). 

*{To Do: allow for getanc.py option to obtain model wind data.}*


### Config File

A configuration file needs to be created or selected prior to processing to specify the configuration HyperInSPACE 
should use when processing the data. 

### Edit Config Window

This window allows editing all the HyperInSPACE configuration file options including:

### Calibration Files:

Add Calibration Files - Allows loading calibration files (.cal/.tdf) into HyperInSPACE. Once loaded the drop-down 
box can be used to select the calibration file. 
Enabled checkbox - Used to enable/disable loading the calibration file in HyperInSPACE.
Frame Type - ShutterLight/ShutterDark/Not Required/LightAncCombined can be selected. This is mainly used to specify 
frame type (ShutterLight/ShutterDark) for dark correction, the other options are unused.

#### Level 1A - Preprocessing

Process data from raw binary ('.RAW' collections) to L1A (HDF5 '.hdf'). Calibration files and RawFileReader.py 
allow for interpretation of raw data fields, which are read into HDF objects.

Solar Zenith Angle Filter: prescreens data for high SZA (low solar elevation) to exclude files which may have been
collected post-dusk or pre-dawn from further processing. Triggering the SZA threshold will skip the entire file.
**Default: 60 degrees (e.g. Brewin et al., 2016)**

#### Level 1B

Process data from L1A to L1B. Data are filtered for vessel attitude, viewing and solar geometry, 
and then processed from raw counts to calibrated radiances/irradiances using the factory calibration files.

Rotator Home Angle: The offset between the neutral position of the SolarTracker unit and the bow of the ship. This
/should/ be zero if the SAS Home Direction was set at the time of data collection as per Satlantic SAT-DN-635.** 

*{\*\*Still waiting to hear from Satlantic about how this value gets tweaked and recorded in the raw data during*
*instrument set-up. Also, from page D-19, which heading sensor was used during data collection.}*

Rotator Delay: Seconds of data discarded after a SAS rotation is detected.
**Default: 60 seconds (Vandenberg 2016)**

Pitch & Roll Filter (optional): Data outside these thresholds are discarded if this is enabled in the checkbox.
**Default 5 degrees (IOCCG Draft Protocols; Zibordi et al. 2019; 2 deg "ideal" to 5 deg "upper limit")**


Relative Solar Azimuth Filter (optional): Relative angle in degrees between the viewing Li/Lt and the sun.
**Default: 90-135 deg (Mobley 1999)**
**IOCCG Draft Protocols: 90 deg unless certain of platform shadow**


#### Level 2

Process data from L1B to L2. Light and dark data are screened for electronic noise ("deglitched" - see Anomaly 
Analysis), which is removed (optional). Shutter dark samples are the subtracted from shutter lights after dark 
data have been interpolated in time to match light data. 
**(e.g. Brewin 2016, Prosoft7.7 User Manual SAT-DN-00228-K)**

##### Anomaly Analysis (optional)

Deglitching the data is very sensitive to the deglitching parameters described below, as well as environmental 
conditions and the variability of the radiometric data itself. Therefore, a seperate module was developed to 
tune these parameters for individual files, instruments, and/or field campaigns. The tool is launched by setting 
the parameters (windows and sigma factors) in the Configuration window, SAVING THE CHANGES, and then running the 
tool on an example of L1B data using the Anomaly Analysis button.

For each waveband of each sensor, and for both light and dark shutter measurements, the time series of radiometric
data are low-pass filtered with a moving average using discrete linear convolution of two one dimensional 
sequences with an adjustable window sizes. For darks, a stationary standard deviation anomaly (from 
the moving average) is used to assess whether data are within an adjustable "sigma factor". For lights, 
a MOVING standard deviation anomaly (from the moving average of seperately adjustable window size) is used 
to assess whether data are within a seperately adjustable "sigma factor". The low-band filter is passed over the
data twice. First and last data points for light and dark data cannot be accurately filtered with this method, 
and are discarded. 
**(e.g. API Reference: https://docs.scipy.org/doc/numpy/reference/generated/numpy.convolve.html**
**Abe et al. 2006, Chandola et al. 2009)** 

#### Level 3

Process data from L2 to L3. Interpolates radiometric data to common wavebands, optionally generates spectral
plots of Li, Lt, and Es, and optionally outputs text files containing the data and metadata for submission
to the SeaWiFS Bio-optical Archive and Storage System (SeaBASS; https://seabass.gsfc.nasa.gov/)

Each HyperOCR radiometer collects data in a unique set of waveband at nominally 3.3 nm resolution. For merging, 
they must be interpolated to common wavebands. Interpolating to a different (presumably lower) spectral resolution
is also an option. No extrapolation is calculate (i.e. interpolation is between the global minimum and maximum 
spectral range). Spectral interpolation is by univariate spline with a smoothing factor of 3.
**https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.UnivariateSpline.html**

*{TO DO: Include selections for various ocean color sensor bands and use spectral response functions from*
*those instruments to interpolate HyperSAS data spectrally to those wavebands.}*

A module allows the user to collect all of the information from the data and the processing configuration
for use in automatically creating SeaBASS headers. 

#### Level 4 - Rrs Calculation

Enable Meteorogical Flags - Enables/disables meteorogical flag checking.
Es, Dawn/Dusk, Rainfall/Humidity flags - Specifies values for the meteorological flags.

Rrs Time Interval (seconds) - Specifies the interval where data is split into groups before 
calculating the Rrs value on each separate group.

Default Wind Speed - The default wind speed used for the Rrs calculation.

Save Button - Used to save the config file
Cancel Button - Closes the Config File window.

##
Abe, N., Zadrozny, B., and Langford, J. 2006. Outlier detection by active learning. 
            In Proceedings of the 12th ACM SIGKDD International Conference on Knowledge Discovery and 
            Data Mining. ACM Press, New York, 504–509
        [4] V Chandola, A Banerjee and V Kumar 2009. Anomaly Detection: A Survey Article No. 15 in ACM 
            Computing Surveys""")**