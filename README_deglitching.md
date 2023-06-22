# Anomaly Analysis & Thresholding (optional)

Running the Anomaly Analysis to parameterize the deglitching algorithm requires L1AQC files, so they must first be 
processed to L1AQC with no deglitching and then loaded into the Anomaly Analysis tool to be reprocessed to L1AQC with 
deglitching.

The Anomaly Analysis (deglitching) window looks like this:

<center><img src="Data/Img/Deglitching_window.png" alt="banner"></center>

Deglitching is highly sensitive to the parameters described below, as well as some environmental conditions not 
otherwise controlled for in L1AQC processing and the overall variability of the radiometric data itself. Therefore, a 
separate module was developed to tune these parameters for individual files, instruments, and/or field campaigns and 
conditions. A sharp temperature change of the instrument, shutter malfunction, or heavy vibration, for example, could
 impact "glitchy-ness" and change the optimal parameterization.

Due to high HyperOCR noise in the NIR, deglitching is currently hard-coded to only perform deglichting between 
350 - 850 nm. Deglitching is conservative: i.e. if a value in any waveband within a timeseries is flagged, all data for 
that timestamp are removed.

The tool is launched pressing the Anomaly Analysis button in the Configuration Window. A dialog will appear to select an 
L1AQC file for deglitching, after which a GUI will display timeseries plots of the light (shutter open) and dark 
(shutter closed) data for a given waveband. Metadata including date, time, wind, cloud, waves, solar and sensor geometry
 are shown in the top of the window. In addition, the software allows the user to define the file naming scheme of 
 photographs collected in the field, presuming they are named with date and time. The software will look in a directory 
 called /Photos in the designated input directory structure and match all photos within 90 minutes of the mean 
 collection time for the file. Matched photos can by scanned using the button on the right to launch the viewer. The
 slider below the metadata allows for adjustment of the wavelength to be screened (the Update button will update the 
 figures for any changes in sensor or parameterization), and radio buttons allow selection between Es, Li, or Lt sensors.
 Sensors are parameterized independently of each other, and seperately for the light and dark signals. Plots are 
 interactive and can be explored in higher detail by panning with the left mouse button or zooming with the right mouse
 button (a small "A" box in the bottom left of the plot restores it to all data, or right-click for more options).

For each waveband of each sensor, and for both light and dark shutter measurements, the time series of radiometric data 
are low-pass filtered with a moving average over time using discrete linear convolution of two one-dimensional sequences
with adjustable window sizes (number of samples in the window). For darks, a *STATIONARY* standard deviation anomaly
(from the moving average in time) is used to assess whether data are within an adjustable "sigma factor" multiplier
within the window. For lights, a *MOVING* standard deviation anomaly (from the moving average of separately adjustable 
window size) is used to assess whether data are within a separately adjustable sigma. The low-band filter is passed over
 the data twice (forward and backward). First and last data points for light and dark data cannot be accurately 
 filtered with this method, and are always discarded.

Adjust the window size and sigma parameters for each instrument and hit Update (or keyboard Enter) to see which data 
(black circles) are retained or discarded (red 'x' or '+' for first and second pass, respectively). Default values 
optimized for NASA's HyperSAS are shown adjacent to each box, but these may not be appropriate for other packages. Move
the slider and hit update to see how these factors impact data in various portions of the spectrum. The field '% Loss 
(all bands)' shows how application of the current parameterization decimates the *entire spectral/temporal dataset for 
the given sensor, not just the band shown*.

In addition to the low-pass filters, light and dark data from each sensor can be filtered with a high and low value 
threshold. This is off by default, but can be very powerful for custom processing (e.g., patchy cloud elimination), and 
tends to be more useful in the light data rather than the dark (shutter closed). However, error associated with 
nonlinearity of response in HyperOCRs with dynamic integration time adjustment can also be minimized using dark 
thresholds. Thresholds are chosen by selecting the desired band (and hit Set Band) independently for light and dark data,
and choosing a minimum and/or maximum threshold value in the appropriate boxes. Change value to "None" if a 
particularly threshold should be ignored. For example, to filter Li data on thresholds only for a high threshold for 
dark data based on 555 nm, select the Threshold checkbox, select the Li Radio button, move the slider to 555 nm, and 
hit Update. Now, you can enter a value (e.g. 1.0) into the lefthand "Max" textbox and hit "Update" (or keyboard Enter).
The filtered data should show in blue. *Keep in mind, they will only show in the waveband for which they were set,* 
but like the low-pass filter, if they fall outside the thresholds in that band, that timestamp will be deleted for all
bands.

Currently, to threshold data from any of the three instruments, ```Threshold``` must be checked, but leaving the min/max 
values as None in the other sensors will still work to ignore thresholding those sensors.

*To see the results when reviewing the threshold parameters on a file, make sure the waveband slider is on the 
appropriate waveband (and hit Update).*

Once the parameters have been adjusted for each sensor, they can be saved (```Save Sensor Params```) to the current 
software configuration and to a backup configuration file for later use. This means that once you have 'tuned' these 
parameters for a given file, the software will be able to load the file (from the Config directory) to reference those 
parameters. This is useful for reprocessing; *you should only need to tune these once for each file.* If you find that a
given set of deglitching parameterizations is working sufficiently well for all your L1AQC files for a given cruise, 
simply save them once, save the Configuration from the Configuration Window, and the software configuration will reuse 
them for all files (i.e. it only applies alternative values for files that were specifically saved). Saved file-specific
 parameterization can be viewed/editted in the CSV file named after the Configuration in the Config directory 
 (e.g. "KORUS_anoms.csv" for the "KORUS.cfg").

For record keeping and the PDF processing report, plots of the delitching (similar to those shown in realtime) can be 
saved to disk. Select the waveband interval at which to save plots (e.g. at 3.3 nm resolution and 20 interval, plots are
 produced every 66 nm, or 48 PNG files for a typical HyperSAS system), and click Save Anomaly Plots. Results of the 
 anomaly detection are saved to [output_directory]/Plots/L1AQC_Anoms. Data flagged for removal given the 
 parameterizations chosen in the Configuration window are shown for the filter first pass (red box) and second pass 
 (blue star) and thresholds (red circles only shown in the band for which they were chosen).

For convenience a shortcut to processing the currently active L1AQC file to L1B is provided (Process to L1B).

To save the current values from the Anomaly Analysis tool as the defaults for the given cruise, 
```Save Sensor Params``` > ```Close``` > ```Save/Close``` the Configuration Window.


**Defaults: Currently based on EXPORTSNA DY131; shown in GUI; experimental**
**(Abe et al. 2006, Chandola et al. 2009)**
**(API Reference: https://docs.scipy.org/doc/numpy/reference/generated/numpy.convolve.html)**

<!--- * A problem with instrument linear response sensitivity to integration time was recently discoveres and is under investigation.
# * ATTENTION: Do your SeaBird HyperOCR dark-shutter data often look like a stepped response, like this?
# <center><img src="Data/DarkStepResponse.png" alt="LT Dark"></center>
# If so, please contact me to learn more about this issue if you are willing/able to share your data.
-->