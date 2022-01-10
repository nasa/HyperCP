v1.0.10 Unreleased; DAA = (dirk.a.aurin@nasa.gov)
---

Next priorities:
* Implement Groetch et al. 2017 3C glint correction
* Implement Vandermuelen, Dierssen (in prep) QWIP QC
* Implement TriOS platform support
* Implement satellite matchup with fd_mathcup.py
* Integration time issue with HyperOCRs; develop/add correction (in cal file? another level?)
    * Do other users of SeaBird HOCRs see int. time response issues?
    * Contact me for further info regarding integration time uncertainty
* Improve/augment to NIR residual corrections
    * Iterative approaches; process time concern.
* Add BRDF correction options
* Propagate uncertainties from radiometry to OC products
* Improve uncertainty estimates of glint corrections
* Memory issue with FPDF causes major slowdown in PDF report building with figures
* Fix non-unique station/file bug

Ideas and To-Dos:
* Explore ML approaches to automate filter selection and glint/NIR correction selection
* Incorporate additional platforms with collaborators (write to dirk.a.aurin@nasa.gov)
* Use ancillary SeaBASS metadata to populate remaining L1E/L2 SeaBASS header fields
* Add failure flags in HDF object attributes:
    * Capture details when errors thrown (inspect, currentframe, getframeinfo)
    * Split Wind and SZA bombs in L2
* Add PIC and GIOP to L2 OC products
* Produce kml files for GoogleEarth on entire cruise/directory

___________________________________________________________

2021-12-14:
* Fix bug in Rrs_MODISA_Uncorr columns2dataset (PL2 L486)

2021-11-24:
* Change all progress bars to tqdm

2021-11-23: Pseudonymous github contributor
* Retrieve database size from server on initial download
* Use tqdm progress bar

2021-11-17:
* Build netCDF LUT for Mobley 1999 glint correction
* Edit M99 glint corr to utilize complete LUT

2021-11-1:
* Remove Ruddick 2006 rho correction, leave placeholder for Groetsch 3C
* Change GPS "SPEED" to "SOG" throughout, and ANCILLARY "SAL" to "SALINITY"
* Numerous bug fixes - mainly associated with AncGroup dataset column keys and Utilities plotting directories

2021-10-29: DAA adapted from M Bretagnon (ACRI)
* Add command line option for single-level processing

---
v1.0.9 2021-09-01: DAA

2021-09-01:
* Adapt for HyperOCRs that do not extend into NIR beyond ~800 nm

2021-08-19:
* Build in capability for pitch/roll in ancillary file
* Facilitate SATTHS (tilt-heading sensor) as separate data source (SolarTracker had it merged, but not pySAS)
* Vectorize HDFDataset.colDeleteRow for speed
* Eliminate ancillary file processing in L2

2021-05-24:
* Add uncertainties to SeaBASS Es & Rrs output
* Change notation on L2 products (and in SeaBASS) to reflect sd for std and unc for uncertainty

---
v1.0.8 2021-05-11: DAA

2021-05-05:
* Checkout v1.0.8 on pySAS/UMTower system data from EXPORTS_2021. Tests ok, but THS data still missing in raw binary from the UMTower.

2021-05-05:
* Update L1C to add ancGroup even when no ancillary data are provided. Take timestamps, lat, lon from GPS, calculat SZA, SAz.

2021-04-22:
* Update photo window with current photo time and filename

---
v1.0.7 2021-04-19: DAA

2021-04-19:
* Fix bug in Controller that flipped LI/LT anomaly params from the CSV file.
* Fix PDF report root source for RAW?L1A fail and clean up premature SeaBASS header items
* Restore automatic deglitching plots to ProcessL1d (making AnomalyDetection Save Plots redundant)

2021-04-14:
* Add a module to L1D Anomaly Analysis for displaying photos taken in the field

2021-04-12:
* Incorporate complete deglitching params into PDF report. Complete moves to group from root at L2.
* Retool PDF reporting for failed level processing
* Add metadata to the top of the AnomalyDetection window

2021-04-09:
* Reconfigure L1C to ingest the Ancillary Metadata file regardless of whether SolarTracker type system is in use or not. Propagate changes through L2. Tested on TRACKER and NOTRACKER datasets.

2021-04-06:
* Fix Controller to update /all/ ConfigFile settings with the pre-saved Anomaly parameter
* Fix bad path for PDF report in AnomalyDetection
* Clean up AnomalyDetection plots

---
v1.0.6 2021-03-31: DAA
2021-03-31:
* Update README and Changelog in preparation for version release
* Clean up file naming in batch mode to allow more flexibility in name formats
* Fix bug in AnomalyDetection for f3.2 type waveband naming (lights)

2021-03-29:
* Port repository over from GitLab to https://github.com/nasa/HyperInSPACE
* Add Data directory to repo (less Anc and Zhang database)
* Add code to Main to download the Zhang et al. (2017) database for glint correction after initial clone/launch

2021-02-28:
* CalibrationFile.py reads DATETAG/ TIMETAG2 bytes from binary GPRMC and UMTWR (not GPGGA) frames instead of NMEA string
* Add UMaine SolarTracker (SOLARTRACKER_UM) to potential groups in ProcessL1B.py

---
v1.0.5 2021-02-11: DAA

2021-02-10:
* Add a tool to AnomalyDetection to allow for high/low thresholding of lights/darks; propagate parameters locally and in ConfigFile.settings
* Move deglitching functionality into Utilities to be called by either AnomalyDetection or ProcessL1d
* Update meta fields in PDF reports and SeaBASS headers to reflect root/group attributes over ConfigFile.settings

2021-02-05:
* Add all configuration parameters to HDF root and group attributes as appropriate; tidied up at L2.

2021-02-04:
* Allow for independant deglitching/anomaly parameterizations for each sensor, light and dark.
* Set bounding window for deglitching to (hard-coded) 350 - 850 nm to avoid NIR noise
* Add a CSV file to track deglitching parameterizations for each L1C file in case of reprocessing.
* Add direct L1D processing option to the AnomAnal widget.

2021-01-21:
* Change AnomalyAnalysis module to dynamically plot results with a given set of sigmas/windows (requires pyqtgraph install)

2021-01-13:
* Fix .netrc file permissions when created by HyperInSPACE
* Fix spec filter plot filename bug for stations

2021-01-12:
* Add option to not produce PDF reports in L2 in order to speed up batching when necessary.

2021-01-07:
* Tidy up spectral plotting and fix SeaBASSHeader file saving on ConfigWindow Save/Close

2020-12-16:
* Fix PDF Report plots for L2 with stations. Fix No_NIR correction offset object in L2.

2020-12-04:
* Fix default Max Pitch/Roll Config.setting for when SeaBASS header window never opened.
* Change default wavelength sampling interpolation interval to 3.3 nm.

---
v1.0.4 2020-12-02: DAA

2020-12-01:
* Create default SeaBASS header file when new Config file is created.
* Check the L2 OC products were actually generated before plotting.
* Eliminate "Update" button for SeaBASS header. Updates automatically on opening SeaBASS header window or closing Config window.

2020-11-30:
* Change L1E angular extrapolations to use constant values rather than linear extrapolation except for SOLAR_AZ and SZA.

2020-11-27:
* Add Wei et al. 2016 spectral QA score to L2 products. Include on Rrs plots.
* Automatically save SeaBASS header comments when closing ConfigWindow; remove reminder prompts.

2020-11-20:
* Fix NIR dataset for when no NIR residual correction is performed.

2020-11-17:
* Introduce failure tracking including PDF report generation for lower level processing aborts. Failure codes TBD.
* Tighten up Controller code

2020-11-13:
* Fix Utilities.fixDateTime to catch time redundancy in first record

2020-11-09:
* L2 delete column keys outside Zhang model limits for newRhoHyper

2020-11-05:
* L1C bug corrected for newer group names and trashing files with no radiometric data left after QA

2020-10-19:
* L2 product list bug corrected in ConfigWindow
* Add abort for no SolarTracker (in SolarTracker mode...) found L1C

2020-10-14:
* Add Lw to Lt plots

2020-08-31:
* Bug fix to Ruddick SimSpec NIR correction. Pi conversion was missing for rrs to rho.
* Add version label to SeaBASS file names (e.g. "R1", "R2", etc.)

2020-08-26:
* Bug fix to force Aqua convolution whenever certain Derived Products are sought
* Correct SeaBASS file naming errror for station files
* Fix SeaBASS output units for L2 and L1e.
* Restore radiometry units at L1b onward to HDF attributes

2020-08-21:
* Fix bug in ConfigFile defaults for oc3m vs. oc4

2020-08-19:
* Correct PDF report writer for case where Li or Es have fewest records for L1E interpolation.

2020-08-18:
* Combine pitch/roll filter into one lineedit in the ConfigWindow.

2020-07-14:
* Add splashscreen for PDF unwriteable. Add sigma to spectral filter plots. Fix hard-coded filter sigmas. Fix which deglitching plots added to report.

---
v1.0.3 2020-07-07: DAA

2020-07-07: DAA
* v1.0.3 tested and debugged for MacOS, Win10, Linux
* L2 PDF reporting per file extended to include comments, metadata, and OC product plots

2020-07-01: DAA
* Complete modules for GOCAD (CDOM/Sg/DOC)
* Set up plotting routines for OC products
* Set up PDF reporting at L2 processing

2020-06-24: DAA
* Complete modules for chlor_a, kd490, poc, ipar, AVW, QAAv6

2020-06-18: DAA
* Move most source code into ./Source
* Build chlor_a into root HDF file

---
v1.0.2 2020-05-27: DAA

2020-05-26: DAA
* Update configuration instructions and plotting directories in README.md
* Change output plot directory for AnomalyDetection.py to user selected folder in Main window
* Check that Anomaly Analysis file is a L1C HDF file before proceeding

2020-05-12: DAA
* Change banner. Fix L1a SZA filter option.

2020-05-07: DAA
* Fix log file naming for L2 with stations. Track missing sensors in L1A logs.

2020-05-05: DAA
 * Patch SeaBASSWriter.py (new dataset naming hitch for L1e; added to v.1.0.1 release) and Weight_RSR for calculateBand when slice is only 1 spectrum thick.

---
v1.0.1: 2020-05-05: DAA
* Update README.md and citations
* Correct spectral convolution to operate on (ir)radiances rather than reflectances
* Change the output of plots to match the path of output data directory (i.e. rather than within the HyperInSPACE path). Still reverts to HyperInSPACE/Plots if left blank/default.

---
v1.0.0: 2020-04-27: DAA

2020-04-23: DAA
* Implement station extraction in the GUI and fix errors in the ConfigWindow.py Save As method. SeaBASSHeaderWindow.py debugged to properly track its SeaBASS header name. Tried to allow for string-type station names, but ultimately had to revert to floats as HDF5 struggled with string-type data fields. Station information is now input via the SeaBASS ancillary file in the Main window. Interpolation issue for samples within <1 second resolved by adding microseconds to the conversions to serial times from Python datetime objects in L1D and L1E. Minor updates to ConfigWindow.py text and layout. Outstanding issue with station extraction: if more than one station is visited in the same L1E file, output fails with notification. This is rare, and only happens in files collected without the SolarTracker when nobody resets file collection manually for several hours. Need to develop a way to isolate each station from a given file into its own node to be processed sequentially.

2020-04-07: DAA
* Clean up the wavelength interpolation to one decimal place when using as column/file names.

2020-04-06: DAA
* Introduce filter in ConfigWindow.py to prevent SZA outside of Zhang model bounds. Fix bug in L2 that missed badTimes from a midpoint to EOF for SZA and wind filtering.

---

v1.0.b: 2020-04-02: Dirk A. Aurin
* Limited, external release to reviewers.

---

v1.0.a: 2019-09-04: Dirk A. Aurin <dirk.a.aurin@nasa.gov>
* Limited, internal release to NASA/OBPG/OEL/FSG