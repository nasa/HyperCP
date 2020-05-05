v1.0.1: 2020-05-05: DAA
* Update README and citations
* Correct spectral convolution to operate on (ir)radiances rather than reflectances
* Change the output of plots to match the path of output data directory (i.e. rather than within the HyperInSPACE path). Still reverts to HyperInSPACE/Plots if left blank/default.

v1.0.0: 2020-04-27: DAA

2020-04-23: DAA
* Implement station extraction in the GUI and fix errors in the ConfigWindow Save As method. SeaBASSHeaderWindow debugged to properly track its SeaBASS header name. Tried to allow for string-type station names, but ultimately had to revert to floats as HDF5 struggled with string-type data fields. Station information is now input via the SeaBASS ancillary file in the Main window. Interpolation issue for samples within <1 second resolved by adding microseconds to the conversions to serial times from Python datetime objects in L1D and L1E. Minor updates to ConfigWindow text and layout. Outstanding issue with station extraction: if more than one station is visited in the same L1E file, output fails with notification. This is rare, and only happens in files collected without the SolarTracker when nobody resets file collection manually for several hours. Need to develop a way to isolate each station from a given file into its own node to be processed sequentially.

2020-04-07: DAA
* Clean up the wavelength interpolation to one decimal place when using as column/file names.

2020-04-06: DAA
* Introduce filter in ConfigWindow to prevent SZA outside of Zhang model bounds. Fix bug in L2 that missed badTimes from a midpoint to EOF for SZA and wind filtering.

---

v1.0.b: 2020-04-02: Dirk A. Aurin <dirk.a.aurin@nasa.gov>
* Limited, external release to reviewers.

---

v1.0.a: 2019-09-04: Dirk A. Aurin <dirk.a.aurin@nasa.gov> 
* Limited, internal release to NASA/OBPG/OEL/FSG