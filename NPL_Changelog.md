NPL Uncertainty Analysis Changes - In progress
--- 
Branch maintained by ashley.ramsay@npl.co.uk

__Changes__
* Added uncertainties to the 'Default' branch of the community processor
* Handle reading and storing instrument and calibration uncertainties in hdf objects
* Provide uncertainty for Es/Ed, Li and Lt
* Calculate Rho uncertainty using unoptimised Monte Carlo Propagation 
* Provide uncertainty for Products Lw and Rrs
* Output raw uncertainties into an Uncertainty budget group in hdf files from L2AQC onwards

__Todo__
* optimise Rho uncertainty
* Attain Uncertainty for BRDF corrections within the defaut branch
* implement Lee et al. BRDF correction
* Begin implementation of an 'FRM' branch which ingests instrument characterisation and gives a full uncertainty budget for fully corrected products

___

22/06/2022
-

__Controller.py__
* _processL1aqc_: Initialise Uncertainty Budget hdf group in main hdf object, read instrument characterisation files and store uncertainty
* _processL1aqc_: Interpolate polarisation uncertainty into hyperspectral wavebands to match other uncertainties/no. of instrument pixels
* _processL1aqc_: Smooth straylight uncertainty using a moving average, window size set to 5 but may be changed in code

__Utilities.py__
* Implemented 3 new methods: getline, parseline & read
* _getline_: implements C++ getline functionallity, reads line in file until specified delimiter is reached and returns the result
* _parseline_: Takes a line of data and parses it into a dataset
* _read_: uses getline to read through an entire file line by line; separating header, data and different instrument datasets before calling parseline to store the data in an appropriate format
* Implemented methods to retrieve temperature coefficients from ingested uncertainty data. getTempCorrection and generateTempCoeffs.
* _getTempCorrection_: Takes the filepath to temperature uncertainties and coeffs as well as reference to the HDFroot. Creates a dataset in the uncertainty budget for temperature coeffs & uncertainties then calles generateTempCoeffs.
* _generateTempCoeffs_ : Uses the reference temperature for the instrument calibration to calculate difference in Temperature for each pixel using instrument data. Calculates temperature coeff as 1 + delta T * coeff. 

__ProcessL1b.py__
* _processDarkCorrection_: Added uncertainty group reference to store uncertainties
* _darkCorrection_: Added arguments including a sensor designation and mutable types for storing uncertainties. Calculate standard deviation (k = 1) in each sensor as a relative uncertainty.
* Now _darkCorrection_ calls punpy to calculate uncertainty in ES, LI, & LT using ingested input uncertainties and sensor standard deviation for light and dark readings in DN.

__ProcessL1b_interp.py__
* added new methods to interpolate and handle the newly added uncertainty budget group and contained datasets
* _interpUncertaintyWavelength_: goes through all datasets within the uncertainty budget group interpolating the dictionary keys to align with the interpolated wavelengths for the instrument datasets
* _copyUncertaintyBudget_: copies the uncertainty budget datasets into the new main hdf file for L1BQC
* _processL1b_Interp_: intialised new uncertainty budget and retrieved uncertainties from L1B hdf file for use further in the L1B->L1BQC processing step

__ProcessL2.py__
* _spectralReflectance_: retrieved uncertainties from hdf object
* _spectralReflectance_: intialise datasets for storing instrument, Lw and Rrs uncertainties
* _spectralReflectance_: Initialise propagate objects for Rrs, instrument and Rho uncertainties
* _spectralReflectance_: calculate uncertainties for instruments, Rrs and Lw for a given Rho calculation method
* _ensemblesReflectance_: now takes uncertainty group as an argument, also changed all calls to method to reflect this change
* _ensemblesReflectance_: calculate Rho uncertainty for selected Rho calculation method

__Uncertainty_Analysis.py__
* _init_: Created Propagate object which intialises MCP object from punpy when created
* _Propagate_RRS_cal_: method which calculated RRS uncertainty with full calibration uncertainty applied. For default branch coefficients are set to 1 but uncertainties still applied. Uses full correlation matrix calculated by NPL
* _instrument_Uncertainty_: Calculated the instrument uncertainty for a given sensor (string ES/ED, LI or LT) using punpy
* _Propagate_Lw_: Propagates uncertainty for Lw applying a correlation matrix for inputs that are involved
* added various static functions representing the measurement function for the instrument outputs, Lw and Rrs
* ___appendResults_ & _printResults_: appends results to a dictionary which is a member of the Propagate object, then printResults will output all stored results into a text file with an absolute path specified on initialisation of Propagate
* _getResults_: returns the results dictionary
* _addResult_: adds a value to the results dictionary for a given key and value

__RhoCorrections.py__
* changed the behaviour of the rho calculation functions to take a Propagate argument
* _M99Corr_, _threeCCorr_, _ZhangCorr_: Will use punpy to calculate Rho uncertainty if Propagate is not None