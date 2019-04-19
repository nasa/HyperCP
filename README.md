# HyperInSPACE 

Hyperspectral In Situ Support for PACE
Principally for processing hyperspectral, in situ, above-water radiometric measurements
made with instruments such as the Satlantic HyperSAS SolarTracker.

## Installation

Requires the Anaconda distribution of Python 3.X

Once Anaconda is installed, HyperInSPACE can be started a number of ways, such as by navigating to the program folder on the command line and using the following command:
python Main.py


## Guide

### Config

Under "Config File", click "New" to create a new HyperInSPACE config file.
Select the new config file from the drop-down menu.
Click "Edit" to edit the config file.

In the "Edit Config" window, click "Add Calibration Files" to add the calibration files that were from the extracted .sip file.
The currently selected calibration file can be selected using the drop-down menu.

For each calibration file:
Click "Enable" to enable the calibration file.
Select the frame type used for dark data correction.

Other config file settings can be changed if required.

Click "Save" to save the settings.

### Processing

Process the data by clicking on one of the buttons for single-level or multi-level processing.

During preprocessing stage, raw files are first copied to the "RawData" folder.
The program sends the output from preprocessing to the "Data" folder.
These folders are created in the HyperInSPACE directory when the program starts up.

If performing multi-level processing, generated HDF files are created in the same folder as the input files.
Plots of the level 4 output are generated in the "Plots" folder. CSV files are created in the "csv" folder.


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
