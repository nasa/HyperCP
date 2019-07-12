# HyperInSPACE 

HyperInSPACE is designed to provide Hyperspectral In situ Support for the PACE mission by processing
above-water, hyperspectral radiometry collected with Satlantic HyperSAS instruments.

Author: Dirk Aurin, USRA @ NASA Goddard Space Flight Center
Acknowledgements: Nathan Vanderberg (PySciDON; https://ieeexplore.ieee.org/abstract/document/8121926)

## Installation

Requires the Anaconda distribution of Python 3.X

Download the entire HyperInSPACE repository, and save it anywhere on your machine.

HyperInSPACE can be started in several of ways, such as by navigating to the program folder on the command line and using the following command:
$ python Main.py


## Guide

### Config

Under "Config File", click "New" to create a new HyperInSPACE config file. This file will be instrument-specific, and is usually
also deployment-specific. Select the new config file from the drop-down menu. Click "Edit" to edit the config file.

In the "Edit Config" window, click "Add Calibration Files" to add the calibration files that were from the extracted Satlantic .sip file. The currently selected calibration file can be selected using the drop-down menu.

For each calibration file:
Click "Enable" to enable the calibration file.
Select the frame type used for dark data correction, light data, or "Not Required" for navigational and ancillary data.

Level 1A through Level 4 processing configurations can be set here. These values will depend on your viewing geometry, and quality control thresholds. Level 2 includes a tool to assist with data deglitching parameters ("Anomaly Analysis").

Click "Save" to save the settings. A file will be created in the Config subdirectory, together with copies of the instrument files for later use.

### Processing

Process the data by clicking on one of the buttons for single-level or multi-level processing.

You will need to set up your data input and output directories from the Main window. Note that output subdirectories for particular processing levels (i.e. "L1a", "L3") will be created automatically within your output directory.
The following folders will be created automatically when you first run the program:
    Ascii - Data from L3 and L4 can optionally be output to text files here
    Config - Configuration and instrument files
    Data - Optional location for input and/or output data
    Logs - Most command line output messages are captured for later reference in .log text files here
    Plots - and Plots/Anomalies for optional plotted output (e.g. from Anomaly Analysis)



## Overview

### Main Window

The Main window is the window that appears once HyperInSPACE is started.
It has options to specify a config file, single-level processing, and multi-level processing.

#### Config File

Before doing any processing, a config file needs to be selected to specify the configuration 
HyperInSPACE should use when processing the data.
Available config files can be chosen using the drop-down box.
The New button allows creation of a new config file.
Edit allows editing the currently selected config file.
Delete can be used to delete the currently selected config file.

Single-level processing - Performs one level of processing.
Multi-level processing - Performs multiple levels of processing from the raw file up to the specified level.

### Edit Config Window

This window allows editing all the HyperInSPACE configuration file options:

#### Calibration Files:

Add Calibration Files - Allows loading calibration files (.cal/.tdf) to HyperInSPACE.
Once loaded the drop-down box can be used to select the calibration file.
Enabled checkbox - Used to enable/disable loading the calibration file in HyperInSPACE.
Frame Type - ShutterLight/ShutterDark/Not Required/LightAncCombined can be selected.
This is mainly used to specify frame type (ShutterLight/ShutterDark) for dark correction, the other options are unused.

#### Level 0 - Preprocessing

Enable Longitude/Direction Checking - Enables/disables longitude and direction checking.
Longitude Min/Max - Minimum and maximum settings for longitude
Ferry Direction - specifies the ferry direction between East (E) and West (W).

SAS Solar Tracker Angle Detection/Cleaning - Enables/disables detecting and cleaning of non-optimal angles.
Angle Min/Max - Used to specify the minimum and maximum angles to accept.

#### Level 3 - Wavelength Interpolation

Interpolation Interval (nm) - Sets the interval between points for interpolated wavelengths.

#### Level 4 - Rrs Calculation

Enable Meteorogical Flags - Enables/disables meteorogical flag checking.
Es, Dawn/Dusk, Rainfall/Humidity flags - Specifies values for the meteorological flags.

Rrs Time Interval (seconds) - Specifies the interval where data is split into groups before 
calculating the Rrs value on each separate group.

Default Wind Speed - The default wind speed used for the Rrs calculation.

Save Button - Used to save the config file
Cancel Button - Closes the Config File window.
