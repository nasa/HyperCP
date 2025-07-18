''' Process L1AQC to L1B '''
import os
import datetime as dt
import calendar
from inspect import currentframe, getframeinfo
import glob
from datetime import datetime
import numpy as np

from Source import PATH_TO_CONFIG, PATH_TO_DATA
from Source.ConfigFile import ConfigFile
from Source.CalibrationFileReader import CalibrationFileReader
from Source.ProcessL1b_Interp import ProcessL1b_Interp
from Source.ProcessL1b_FactoryCal import ProcessL1b_FactoryCal
from Source.ProcessL1b_FRMCal import ProcessL1b_FRMCal
from Source.Utilities import Utilities
from Source.GetAnc import GetAnc
from Source.GetAnc_ecmwf import GetAnc_ecmwf
from Source import PACKAGE_DIR as CODE_HOME

class ProcessL1b:
    '''L1B mainly for SeaBird with some shared methods'''


    @staticmethod
    def read_unc_coefficient_factory(root, inpath):
        ''' SeaBird only.'''
        # Read Uncertainties_new_char from provided files
        gp = root.addGroup("RAW_UNCERTAINTIES")
        gp.attributes['FrameType'] = 'NONE'  # add FrameType = None so grp passes a quality check later

        # Read uncertainty parameters from class-based calibration
        for f in glob.glob(os.path.join(inpath, r'*class_POLAR*')):
            Utilities.read_char(f, gp)
        for f in glob.glob(os.path.join(inpath, r'*class_STRAY*')):
            Utilities.read_char(f, gp)
        for f in glob.glob(os.path.join(inpath, r'*class_ANGULAR*')):
            Utilities.read_char(f, gp)
        for f in glob.glob(os.path.join(inpath, r'*class_THERMAL*')):
            Utilities.read_char(f, gp)
        for f in glob.glob(os.path.join(inpath, r'*class_LINEAR*')):
            Utilities.read_char(f, gp)
        for f in glob.glob(os.path.join(inpath, r'*class_STAB*')):
            Utilities.read_char(f, gp)

        # Unc dataset renaming
        Utilities.RenameUncertainties_Class(root)

        # Creation of RADCAL class unc for Seabird, values are extracted from:
        # The Seventh SeaWiFS Intercalibration Round-Robin Experiment (SIRREX-7), March 1999.
        # NASA Technical Reports Server (NTRS)
        # https://ntrs.nasa.gov/citations/20020045342
        # For Trios uncertainties are set 0
        if ConfigFile.settings['SensorType'].lower() == "seabird":
            for sensor in ['LI','LT']:
                dsname = sensor+'_RADCAL_UNC'
                gp.addDataset(dsname)
                ds = gp.getDataset(dsname)
                ds.columns["wvl"] = [400]
                ds.columns["unc"] = [2.7]
                ds.columnsToDataset()
            for sensor in ['ES']:
                dsname = sensor+'_RADCAL_UNC'
                gp.addDataset(dsname)
                ds = gp.getDataset(dsname)
                ds.columns["wvl"] = [400]
                ds.columns["unc"] = [2.3]
                ds.columnsToDataset()

        if ConfigFile.settings['SensorType'].lower() == "trios" or ConfigFile.settings['SensorType'].lower() == "dalec":
            for sensor in ['LI','LT','ES']:
                dsname = sensor+'_RADCAL_UNC'
                gp.addDataset(dsname)
                ds = gp.getDataset(dsname)
                ds.columns["wvl"] = [400]
                ds.columns["unc"] = [0.0]
                ds.columnsToDataset()

        # interpolate unc to full wavelength range, depending on class based or full char
        Utilities.interpUncertainties_Factory(root)

        # # generate temperature coefficient
        Utilities.UncTempCorrection(root)

        return root

    @staticmethod
    def choose_cal_char_per_time(acq_time_seconds, available_files_calTime_seconds, available_files, rule='most_recent_prior_acquisition'):
        '''
        Choose FidRadDB cal/char file according to it's timestamp, provided in filename.
            e.g. 'CP_SAT0385_POLAR_20220603115256.TXT',
            where:
            - 'SAT0385' is the sensor ID
            - 'POLAR' is the characterisation type
            - '20220603115256' is the time stamp, i.e. the time when the given characterisation was masured at cal/char laboratory.

        Two possible options are:
            'most_recent_prior_acquisition' --> applicable to RADCAL files (default "multi cal option", i.e. ConfigFile.settings['MultiCal'] = 0
            'most_recent' --> applicable to sensor-specific characterisations

        return: a string, /full/path/to/selected_cal_char_file.TXT
        '''

        # TEST
        # acq_time_seconds = 3
        # available_files_calTime_seconds = np.array([0, 1, 2, 3.01, 30])
        # available_files = np.array(['a', 'b', 'c', 'd', 'e'])

        # Check goodness of some inputs...
        if (len(available_files_calTime_seconds) == 0) or (len(available_files) == 0) or (len(available_files_calTime_seconds) != len(available_files)):
            raise ValueError('Something wrong here! At least X candidate files (X>0) should be inputted to this function, with X corrsponding cal. timestamps!')

        # Two possible rules (see above)
        chosen_file = None
        if rule == 'most_recent_prior_acquisition':

            # Filter by only those cal./chars. whose timestamps is previous to measurement acquisition
            prior2acq = available_files_calTime_seconds <= acq_time_seconds

            # If found, chose the most recent prior to acquisition, otherwise simply choose the closest to acquisition
            if np.any(prior2acq):
                # Selection of the closest char data file PRE-EXISTING to the measuring date
                chosen_file_idx = np.argmax(available_files_calTime_seconds[prior2acq])
                chosen_file = available_files[prior2acq][chosen_file_idx]
            else:
                # Selection of the closest char data file to the measuring date
                chosen_file_idx = np.argmin(np.abs(available_files_calTime_seconds - acq_time_seconds))
                chosen_file = available_files[chosen_file_idx]
        elif rule == 'most_recent':

            # Choose the most recent (applicable to sensor-specific characterisations)
            chosen_file_idx = np.argmax(available_files_calTime_seconds)
            chosen_file = available_files[chosen_file_idx]

        return chosen_file

    @staticmethod
    def read_FidRadDB_cal_char_files(root):
        '''Read FidRadDB cal/char files into root according:
        - Acquisition time stamp
        - Cal/char files available under fidRadPath, according to their sensorID, cal/char type (e.g. STRAY) and time stamp.
        - Selected cal/char regime
        - Selected multi-cal option

        return root (with the group "RAW_UNCERTAINTIES" updated to contain the read cal/chars)
        '''
        fidRadPath =os.path.join(CODE_HOME, 'Data', 'FidRadDB',ConfigFile.settings['SensorType'])

        # Initialise "RAW_UNCERTAINTIES"
        gp = root.addGroup("RAW_UNCERTAINTIES")

        # add FrameType = None so grp passes a quality check later
        gp.attributes['FrameType'] = 'NONE'

        # Get measurement acquisition time stamp and convert to seconds to compare to cal/char files' timestamps
        # BUG: Some are unable to read this root attribute due to OS language settings
        # print(f"Root attribute TIME-STAMP: {root.attributes['TIME-STAMP']}")
        # acq_time_seconds = datetime.strptime(root.attributes['TIME-STAMP'], '%a %b %d %H:%M:%S %Y').timestamp()
        # Alternative: Grab start time of Es
        if ConfigFile.settings['SensorType'] .lower() == 'seabird':
            esDatetime = root.getGroup('ES_LIGHT').datasets['DATETIME'].data[0]
        else:
            esDatetime = root.getGroup('ES').datasets['DATETIME'].data[0]
        acq_time_seconds = esDatetime.timestamp()

        # Check which cal/char files are needed for each of the 3 sensor types (ES, LT, LI) in cal/char regime = Full, i.e. ConfigFile.settings["fL1bCal"] == 3
        # ... then filter to RADCAL if cal'char regime = class, i.e. ConfigFile.settings["fL1bCal"] == 2
        for sensorType, needed_cal_chars_fullFRM in ConfigFile.settings['neededCalCharsFRM'].items():
            # Loop over each serialNumber_calCharType tag available in ConfigFile.settings['neededCalCharsFRM']
            for serialNumber_calCharType in needed_cal_chars_fullFRM:

                # Get cal/char type from tag (e.g. 'POLAR')
                calCharType = serialNumber_calCharType.split('_')[-1]

                # Find available files in fidRadPath for the given serialNumber_calCharType tag
                available_files = np.array(glob.glob(os.path.join(CODE_HOME,fidRadPath,'CP_%s_*' % serialNumber_calCharType)))

                # get their timestamps anc convert to seconds since UNIX epoch (Jan 1 1970 00:00 UTC)
                available_files_calTime0 = [os.path.basename(f).split('_')[-1].split('.')[0] for f in available_files]
                available_files_calTime_seconds  = np.array([datetime.strptime(t, '%Y%m%d%H%M%S').timestamp() for t in available_files_calTime0])

                # Unless this is a characterisation tag and not calibration tag (i.e. not RADCAL) + class-based regime, raise an error if files are missing...
                if len(available_files) == 0 and not (calCharType != 'RADCAL' and ConfigFile.settings["fL1bCal"] == 2):
                    raise ValueError(
                        'Missing FidRadDB file of type CP_%s_yyyymmdd.txt for %s sensor. At least one file with this name format should be stored at %s (see GUI-->Edit-->Cal/Char options).' % (serialNumber_calCharType, sensorType, fidRadPath))

                if calCharType != 'RADCAL': # Char case
                    if ConfigFile.settings["fL1bCal"] == 2:# class-based
                        continue # class-based, skipping sensor-specific char

                    elif ConfigFile.settings["fL1bCal"] == 3:# sensor-specific
                        # Choose most recent sensor-specific characterisation (this is regardless of measurement acquisition time)
                        chosen_file = ProcessL1b.choose_cal_char_per_time(
                            acq_time_seconds, available_files_calTime_seconds, available_files, rule='most_recent')
                        Utilities.read_char(chosen_file, gp)

                elif calCharType == 'RADCAL':
                    # RADCAL files to be ingested depend on the multical options
                    if ConfigFile.settings["MultiCal"] == 0:# Most recent prior to acquisition

                        # This will choose the most recent prior to acquisition unless nothing prior to acquisition exists, then it will choose simply the closest
                        chosen_file = ProcessL1b.choose_cal_char_per_time(
                            acq_time_seconds, available_files_calTime_seconds, available_files, rule='most_recent_prior_acquisition')
                        Utilities.read_char(chosen_file, gp)

                    elif ConfigFile.settings["MultiCal"] == 1:  # Pre-post average

                        # TODO Not implemented! But pre- and post- cals are at least read into the HDF file
                        raise NotImplementedError("pre/post cal average is not implemented yet.")

                        # Read preCal into gp
                        preCal = os.path.join(CODE_HOME,fidRadPath,ConfigFile.settings.get("preCal_%s" % sensorType))
                        if preCal is None:
                            raise ValueError('Pre-calibration file should have been chosen if pre-post average was chosen (see GUI-->Edit-->Cal/Char options).')
                        Utilities.read_char(preCal, gp)

                        # Read postCal into gp
                        postCal = os.path.join(CODE_HOME,fidRadPath,ConfigFile.settings.get("postCal_%s" % sensorType))
                        if postCal is None:
                            raise ValueError('Post-calibration file should have been chosen if pre-post average was chosen (see GUI-->Edit-->Cal/Char options).')
                        Utilities.read_char(postCal, gp)

                        ###### TO BE CONTINUED #######

                    elif ConfigFile.settings["MultiCal"] == 2: # Choose-cal

                        # Read specific chosen cal into gp
                        chooseCal = os.path.join(CODE_HOME,fidRadPath,ConfigFile.settings.get("chooseCal_%s" % sensorType))
                        if chooseCal is None:
                            raise ValueError('Calibration file should have been chosen if "Chose cal." option was chosen (see GUI-->Edit-->Cal/Char options).')
                        Utilities.read_char(chooseCal, gp)

        return root


    @staticmethod
    def read_unc_coefficient_class(root, classbased_dir):
        ''' SeaBird or TriOS. ProcessL1bTriOS also redirects here.'''

        # Read Uncertainties_new_char from provided files
        gp = root.addGroup("RAW_UNCERTAINTIES")
        gp.attributes['FrameType'] = 'NONE'  # add FrameType = None so grp passes a quality check later

        # Read uncertainty parameters from class-based calibration
        for f in glob.glob(os.path.join(classbased_dir, r'*class_POLAR*')):
            Utilities.read_char(f, gp)
        for f in glob.glob(os.path.join(classbased_dir, r'*class_STRAY*')):
            Utilities.read_char(f, gp)
        for f in glob.glob(os.path.join(classbased_dir, r'*class_ANGULAR*')):
            Utilities.read_char(f, gp)
        for f in glob.glob(os.path.join(classbased_dir, r'*class_THERMAL*')):
            Utilities.read_char(f, gp)

        for f in glob.glob(os.path.join(classbased_dir, r'*class_LINEAR*')):
            Utilities.read_char(f, gp)
        for f in glob.glob(os.path.join(classbased_dir, r'*class_STAB*')):
            Utilities.read_char(f, gp)

        # Read sensor-specific radiometric calibration
        root = ProcessL1b.read_FidRadDB_cal_char_files(root)

        # Unc dataset renaming
        Utilities.RenameUncertainties_Class(root)

        # interpolate unc to full wavelength range, depending on class based or full char
        Utilities.interpUncertainties_Class(root)

        # # generate temperature coefficient
        Utilities.UncTempCorrection(root)

        return root


    @staticmethod
    def read_unc_coefficient_frm(root, classbased_dir):
        ''' SeaBird or TriOS.  ProcessL1bTriOS also redirects here. '''
        # Read Uncertainties_new_char from provided files
        gp = root.addGroup("RAW_UNCERTAINTIES")
        gp.attributes['FrameType'] = 'NONE'  # add FrameType = None so grp passes a quality check later        

        # Read sensor-specific radiometric calibration
        root = ProcessL1b.read_FidRadDB_cal_char_files(root)

        # temporarily use class-based polar unc for FRM
        for f in glob.glob(os.path.join(classbased_dir, r'*class_POLAR*')):
            if any([s in os.path.basename(f) for s in ["LI", "LT"]]):  # don't read ES Pol which is the manufacturer cosine error
                Utilities.read_char(f, gp)
        # Polar correction to be developed and added to FRM branch.

        # unc dataset renaming
        Utilities.RenameUncertainties_FullChar(root)

        # interpolate LAMP and PANEL to full wavelength range
        success = Utilities.interpUncertainties_FullChar(root)
        if not success:
            print('interpUncertainties_FullChar failed.')
            return None

        # generate temperature coefficient
        Utilities.UncTempCorrection(root)

        return root


    @staticmethod
    def includeModelDefaults(ancGroup, modRoot):
        ''' Include model data or defaults for blank ancillary fields.  ProcessL1bTriOS and ProcessL1bDALEC also redirect here. '''
        print('Filling blank ancillary data with models or defaults from Configuration')

        epoch = dt.datetime(1970, 1, 1,tzinfo=dt.timezone.utc)
        # radData = referenceGroup.getDataset("ES") # From node, the input file

        # Convert ancillary date time
        if ancGroup is not None:
            ancGroup.datasets['LATITUDE'].datasetToColumns()
            ancTime = ancGroup.datasets['LATITUDE'].columns['Timetag2']
            ancSeconds = []
            ancDatetime = []
            for i, ancDate in enumerate(ancGroup.datasets['LATITUDE'].columns['Datetag']):
                ancDatetime.append(Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(ancDate),ancTime[i]))
                ancSeconds.append((ancDatetime[i]-epoch).total_seconds())
        # Convert model data date and time to datetime and then to seconds for interpolation
        if modRoot is not None:
            modTime = modRoot.groups[0].datasets["Timetag2"].tolist()
            modSeconds = []
            modDatetime = []
            for i, modDate in enumerate(modRoot.groups[0].datasets["Datetag"].tolist()):
                modDatetime.append(Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(modDate),modTime[i]))
                modSeconds.append((modDatetime[i]-epoch).total_seconds())

        # Model or default fills
        if 'WINDSPEED' in ancGroup.datasets:
            ancGroup.datasets['WINDSPEED'].datasetToColumns()
            windDataset = ancGroup.datasets['WINDSPEED']
            wind = windDataset.columns['NONE']
        else:
            windDataset = ancGroup.addDataset('WINDSPEED')
            wind = np.empty((1,len(ancSeconds)))
            wind[:] = np.nan
            wind = wind[0].tolist()
        if 'AOD' in ancGroup.datasets:
            ancGroup.datasets['AOD'].datasetToColumns()
            aodDataset = ancGroup.datasets['AOD']
            aod = aodDataset.columns['NONE']
        else:
            aodDataset = ancGroup.addDataset('AOD')
            aod = np.empty((1,len(ancSeconds)))
            aod[:] = np.nan
            aod = aod[0].tolist()
        # Default fills
        if 'SALINITY' in ancGroup.datasets:
            ancGroup.datasets['SALINITY'].datasetToColumns()
            saltDataset = ancGroup.datasets['SALINITY']
            salt = saltDataset.columns['NONE']
        else:
            saltDataset = ancGroup.addDataset('SALINITY')
            salt = np.empty((1,len(ancSeconds)))
            salt[:] = np.nan
            salt = salt[0].tolist()
        if 'SST' in ancGroup.datasets:
            ancGroup.datasets['SST'].datasetToColumns()
            sstDataset = ancGroup.datasets['SST']
            sst = sstDataset.columns['NONE']
        else:
            sstDataset = ancGroup.addDataset('SST')
            sst = np.empty((1,len(ancSeconds)))
            sst[:] = np.nan
            sst = sst[0].tolist()
        if 'AIRTEMP' in ancGroup.datasets:
            ancGroup.datasets['AIRTEMP'].datasetToColumns()
            airDataset = ancGroup.datasets['AIRTEMP']
            air = airDataset.columns['NONE']
        else:
            airDataset = ancGroup.addDataset('AIRTEMP')
            air = np.empty((1,len(ancSeconds)))
            air[:] = np.nan
            air = air[0].tolist()

        # Initialize flags
        windFlag = []
        aodFlag = []
        airFlag = []
        for i,ancSec in enumerate(ancSeconds):
            if np.isnan(wind[i]):
                windFlag.append('undetermined')
            else:
                windFlag.append('field')
            if np.isnan(aod[i]):
                aodFlag.append('undetermined')
            else:
                aodFlag.append('field')
            if np.isnan(air[i]):
                airFlag.append('undetermined')
            else:
                airFlag.append('field')

        # Replace Wind, AOD, and AirTemp NaNs with modeled data where possible.
        # These will be within one hour of the field data.
        if modRoot is not None:
            Utilities.writeLogFileAndPrint('Filling in field data with model data where needed.')

            for i,ancSec in enumerate(ancSeconds):

                if np.isnan(wind[i]):
                    idx = Utilities.find_nearest(modSeconds,ancSec)
                    wind[i] = modRoot.groups[0].datasets['Wind'][idx]
                    windFlag[i] = 'model'
                    if i==0:
                        ancGroup.attributes['Model Wind units'] = modRoot.groups[0].attributes['Wind units']
                if np.isnan(aod[i]):
                    idx = Utilities.find_nearest(modSeconds,ancSec)
                    aod[i] = modRoot.groups[0].datasets['AOD'][idx]
                    aodFlag[i] = 'model'
                    if i==0:
                        ancGroup.attributes['Model AOD wavelength'] = modRoot.groups[0].attributes['AOD wavelength']
                if np.isnan(air[i]):
                    idx = Utilities.find_nearest(modSeconds,ancSec)
                    air[i] = modRoot.groups[0].datasets['AirTemp'][idx]
                    airFlag[i] = 'model'
                    if i==0:
                        ancGroup.attributes['Model AIRTEMP units'] = modRoot.groups[0].attributes['Air Temp. units']

        # Replace Wind, AOD, SST, Sal, and AirTemp with defaults where still nan
        Utilities.writeLogFileAndPrint('Filling in ancillary data with default values where still needed.')
        # Salt and SST do not have model fallbacks.
        saltFlag = []
        sstFlag = []
        for i, value in enumerate(wind):
            if np.isnan(value):
                wind[i] = ConfigFile.settings["fL1bDefaultWindSpeed"]
                windFlag[i] = 'default'
        for i, value in enumerate(aod):
            if np.isnan(value):
                aod[i] = ConfigFile.settings["fL1bDefaultAOD"]
                aodFlag[i] = 'default'
        for i, value in enumerate(salt):
            if np.isnan(value):
                salt[i] = ConfigFile.settings["fL1bDefaultSalt"]
                saltFlag.append('default')
            else:
                saltFlag.append('field')
        for i, value in enumerate(sst):
            if np.isnan(value):
                sst[i] = ConfigFile.settings["fL1bDefaultSST"]
                sstFlag.append('default')
            else:
                sstFlag.append('field')
        for i, value in enumerate(air):
            if np.isnan(value):
                air[i] = ConfigFile.settings["fL1bDefaultSST"]
                airFlag.append('default')
            else:
                airFlag.append('field')

        # Populate the datasets and flags with the InRad variables
        windDataset.columns["NONE"] = wind
        windDataset.columns["WINDFLAG"] = windFlag
        windDataset.columnsToDataset()
        aodDataset.columns["AOD"] = aod
        aodDataset.columns["AODFLAG"] = aodFlag
        aodDataset.columnsToDataset()
        airDataset.columns["AIRTEMP"] = air
        airDataset.columns["AIRFLAG"] = airFlag
        airDataset.columnsToDataset()
        saltDataset.columns["NONE"] = salt
        saltDataset.columns["SALTFLAG"] = saltFlag
        saltDataset.columnsToDataset()
        sstDataset.columns["NONE"] = sst
        sstDataset.columns["SSTFLAG"] = sstFlag
        sstDataset.columnsToDataset()

        # Convert ancillary seconds back to date/timetags ...
        ancDateTag = []
        ancTimeTag2 = []
        ancDT = []
        for i, sec in enumerate(ancSeconds):
            ancDT.append(dt.datetime.utcfromtimestamp(sec).replace(tzinfo=dt.timezone.utc))
            ancDateTag.append(float(f'{int(ancDT[i].timetuple()[0]):04}{int(ancDT[i].timetuple()[7]):03}'))
            ancTimeTag2.append(float( \
                f'{int(ancDT[i].timetuple()[3]):02}{int(ancDT[i].timetuple()[4]):02}{int(ancDT[i].timetuple()[5]):02}{int(ancDT[i].microsecond/1000):03}'))

        # Move the Timetag2 and Datetag into the arrays and remove the datasets
        for ds in ancGroup.datasets:
            ancGroup.datasets[ds].columns["Datetag"] = ancDateTag
            ancGroup.datasets[ds].columns["Timetag2"] = ancTimeTag2
            ancGroup.datasets[ds].columns["Datetime"] = ancDT
            ancGroup.datasets[ds].columns.move_to_end('Timetag2', last=False)
            ancGroup.datasets[ds].columns.move_to_end('Datetag', last=False)
            ancGroup.datasets[ds].columns.move_to_end('Datetime', last=False)

            ancGroup.datasets[ds].columnsToDataset()

    @staticmethod
    def convertDataset(group, datasetName, newGroup, newDatasetName):
        ''' Converts a sensor group into the L1B format; option to change dataset name.
            Moves dataset to new group.
            The separate DATETAG, TIMETAG2, and DATETIME datasets are combined into
            the sensor dataset. This also adds a temporary column in the sensor data
            array for datetime to be used in interpolation. This is later removed, as
            HDF5 does not support datetime. '''

        dataset = group.getDataset(datasetName)
        dateData = group.getDataset("DATETAG")
        timeData = group.getDataset("TIMETAG2")
        dateTimeData = group.getDataset("DATETIME")

        # Convert degrees minutes to decimal degrees format; only for GPS, not ANCILLARY_METADATA
        if group.id.startswith("GP"):
            if newDatasetName == "LATITUDE":
                latPosData = group.getDataset("LATPOS")
                latHemiData = group.getDataset("LATHEMI")
                for i in range(dataset.data.shape[0]):
                    latDM = latPosData.data["NONE"][i]
                    latDirection = latHemiData.data["NONE"][i]
                    latDD = Utilities.dmToDd(latDM, latDirection)
                    latPosData.data["NONE"][i] = latDD
            if newDatasetName == "LONGITUDE":
                lonPosData = group.getDataset("LONPOS")
                lonHemiData = group.getDataset("LONHEMI")
                for i in range(dataset.data.shape[0]):
                    lonDM = lonPosData.data["NONE"][i]
                    lonDirection = lonHemiData.data["NONE"][i]
                    lonDD = Utilities.dmToDd(lonDM, lonDirection)
                    lonPosData.data["NONE"][i] = lonDD

        newSensorData = newGroup.addDataset(newDatasetName)

        # Datetag, Timetag2, and Datetime columns added to sensor data array
        newSensorData.columns["Datetag"] = dateData.data["NONE"].tolist()
        newSensorData.columns["Timetag2"] = timeData.data["NONE"].tolist()
        newSensorData.columns["Datetime"] = dateTimeData.data

        # Copies over the sensor dataset from original group to newGroup
        for k in dataset.data.dtype.names: # For each waveband (or vector data for other groups)
            #print("type",type(esData.data[k]))
            newSensorData.columns[k] = dataset.data[k].tolist()
        newSensorData.columnsToDataset()

    @staticmethod
    def darkCorrection(darkData, darkTimer, lightData, lightTimer):
        '''
        HyperInSPACE - Interpolate Dark values to match light measurements (e.g. Brewin 2016, Prosoft
        7.7 User Manual SAT-DN-00228-K)
        '''
        if (darkData is None) or (lightData is None):
            msg  = f'Dark Correction, dataset not found: {darkData} , {lightData}'
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        if Utilities.hasNan(lightData):
            frameinfo = getframeinfo(currentframe())
            # msg = f'found NaN {frameinfo.lineno}'

        if Utilities.hasNan(darkData):
            frameinfo = getframeinfo(currentframe())
            # msg = f'found NaN {frameinfo.lineno}'

        # Interpolate Dark Dataset to match number of elements as Light Dataset
        newDarkData = np.copy(lightData.data)
        for k in darkData.data.dtype.fields.keys(): # For each wavelength
            x = np.copy(darkTimer.data).tolist() # darktimer
            y = np.copy(darkData.data[k]).tolist()  # data at that band over time
            new_x = lightTimer.data  # lighttimer

            if len(x) < 3 or len(y) < 3 or len(new_x) < 3:
                Utilities.writeLogFileAndPrint("**************Cannot do cubic spline interpolation, length of datasets < 3")
                return False

            if not Utilities.isIncreasing(x):
                Utilities.writeLogFileAndPrint("**************darkTimer does not contain strictly increasing values")
                return False
            if not Utilities.isIncreasing(new_x):
                Utilities.writeLogFileAndPrint("**************lightTimer does not contain strictly increasing values")
                return False

            if len(x) >= 3:
                # Because x is now a list of datetime tuples, they'll need to be
                # converted to Unix timestamp values
                xTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in x]
                newXTS = [calendar.timegm(xDT.utctimetuple()) + xDT.microsecond / 1E6 for xDT in new_x]

                newDarkData[k] = Utilities.interp(xTS,y,newXTS, fill_value=np.nan)

                for val in newDarkData[k]:
                    if np.isnan(val):
                        frameinfo = getframeinfo(currentframe())
                        # msg = f'found NaN {frameinfo.lineno}'
            else:
                Utilities.writeLogFileAndPrint('**************Record too small for splining. Exiting.')
                return False

        darkData.data = newDarkData

        if Utilities.hasNan(darkData):
            frameinfo = getframeinfo(currentframe())
            Utilities.writeLogFileAndPrint(f'found NaN {frameinfo.lineno}')
            return False

        # Correct light data by subtracting interpolated dark data from light data
        for k in lightData.data.dtype.fields.keys():
            for x in range(lightData.data.shape[0]):
                lightData.data[k][x] -= newDarkData[k][x]

        if Utilities.hasNan(lightData):
            frameinfo = getframeinfo(currentframe())
            Utilities.writeLogFileAndPrint(f'found NaN {frameinfo.lineno}')
            return False

        return True


    @staticmethod
    def processDarkCorrection(node, sensorType):
        Utilities.writeLogFileAndPrint(f'Dark Correction: {sensorType}')
        darkGroup,darkData,darkDateTime,lightGroup,lightData,lightDateTime = \
            None,None,None,None,None,None

        for gp in node.groups:
            if not gp.id.endswith('_L1AQC') and not gp.id.startswith('SATTHS') \
                and not gp.id.startswith('SunTracker') \
                and not gp.id.startswith('GPS') \
                and not gp.id.startswith('ANCILLARY') \
                    and 'FrameType' in gp.attributes:
                if gp.attributes["FrameType"] == "Not Required":
                    Utilities.writeLogFileAndPrint(f'ERROR: Check the FrameType for {sensorType}')
                    break

                if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensorType):
                    darkGroup = gp
                    darkData = gp.getDataset(sensorType)
                    darkDateTime = gp.getDataset("DATETIME")

                if gp.attributes["FrameType"] == "ShutterLight" and gp.getDataset(sensorType):
                    lightGroup = gp
                    lightData = gp.getDataset(sensorType)
                    lightDateTime = gp.getDataset("DATETIME")

        if darkGroup is None or lightGroup is None:
            Utilities.writeLogFileAndPrint(f'No radiometry found for {sensorType}')
            return False

        # Instead of using TT2 or seconds, use python datetimes to avoid problems crossing
        # UTC midnight.
        if not ProcessL1b.darkCorrection(darkData, darkDateTime, lightData, lightDateTime):
            Utilities.writeLogFileAndPrint(f'ProcessL1b.darkCorrection failed  for {sensorType}')
            return False

        # Now that the dark correction is done, we can strip the dark shutter data from the
        # HDF object.
        for gp in node.groups:
            if not gp.id.endswith('_L1AQC') and 'FrameType' in gp.attributes:
                if gp.attributes["FrameType"] == "ShutterDark" and gp.getDataset(sensorType):
                    node.removeGroup(gp)
        # And rename the corrected light frame
        for gp in node.groups:
            if not gp.id.endswith('_L1AQC') and 'FrameType' in gp.attributes:
                if gp.attributes["FrameType"] == "ShutterLight" and gp.getDataset(sensorType):
                    gp.id = gp.id[0:2] # Strip off "_LIGHT" from the name
        return True

    @staticmethod
    def processL1b(node, outFilePath):
        '''
        Non-TriOS path. ProcessL1b_Interp.processL1b_Interp will be common to both platforms
        Apply dark shutter correction to light data. Then apply either default factory cals
        or full instrument characterization. Introduce uncertainty group.
        Match timestamps and interpolate wavebands.
        '''
        node.attributes["PROCESSING_LEVEL"] = "1B"
        now = dt.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr
        if ConfigFile.settings["fL1bCal"] == 1:
            node.attributes['CAL_TYPE'] = 'Factory'
        elif ConfigFile.settings["fL1bCal"] == 2:
            node.attributes['CAL_TYPE'] = 'FRM-Class'
        elif ConfigFile.settings["fL1bCal"] == 3:
            node.attributes['CAL_TYPE'] = 'FRM-Full'
        node.attributes['WAVE_INTERP'] = str(ConfigFile.settings['fL1bInterpInterval']) + ' nm'

        Utilities.writeLogFileAndPrint(f"ProcessL1b.processL1b: {timestr}")

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        node  = Utilities.rootAddDateTime(node)

        # Introduce a new group for carrying L1AQC data forward. Groups keep consistent timestamps across all datasets,
        #    so it has to be a new group to avoid conflict with interpolated timestamps.
        #       Due to the way light/dark sampling works with OCRs, each will need its own group
        esDarkGroup = node.addGroup('ES_DARK_L1AQC')
        esLightGroup = node.addGroup('ES_LIGHT_L1AQC')
        liDarkGroup = node.addGroup('LI_DARK_L1AQC')
        liLightGroup = node.addGroup('LI_LIGHT_L1AQC')
        ltDarkGroup = node.addGroup('LT_DARK_L1AQC')
        ltLightGroup = node.addGroup('LT_LIGHT_L1AQC')
        for gp in node.groups:
            if gp.id == 'ES_DARK':
                esDarkGroup.copy(gp)
            elif gp.id == 'ES_LIGHT':
                esLightGroup.copy(gp)
            elif gp.id == 'LI_DARK':
                liDarkGroup.copy(gp)
            elif gp.id == 'LI_LIGHT':
                liLightGroup.copy(gp)
            elif gp.id == 'LT_DARK':
                ltDarkGroup.copy(gp)
            elif gp.id == 'LT_LIGHT':
                ltLightGroup.copy(gp)

        # Interpolate only the Ancillary group, and then fold in model data
        # This is run ahead of the other groups for all processing pathways. Anc group
        # exists regardless of Ancillary file being provided
        if not ProcessL1b_Interp.interp_Anc(node, outFilePath):
            Utilities.writeLogFileAndPrint('Error interpolating ancillary data')
            return None

        # Need to fill in with model and fallback values before running ProcessL1b.read_unc_coefficient_class in order to get proper thermal data
        ancGroup = node.getGroup("ANCILLARY_METADATA")

        # Retrieve MERRA2 model ancillary data
        if ConfigFile.settings["bL1bGetAnc"] ==1:
            Utilities.writeLogFileAndPrint('MERRA2 data for Wind and AOD may be used to replace blank values. Reading in model data...')
            modRoot = GetAnc.getAnc(ancGroup)
        # Retrieve ECMWF model ancillary data
        elif ConfigFile.settings["bL1bGetAnc"] == 2:
            Utilities.writeLogFileAndPrint('ECMWF data for Wind and AOD may be used to replace blank values. Reading in model data...')
            modRoot = GetAnc_ecmwf.getAnc_ecmwf(ancGroup)
        else:
            modRoot = None

        # Regardless of whether SunTracker is used, Ancillary data will have already been
        # interpolated in L1B as long as the ancillary file was read in at L1AQC. Regardless, these need
        # to have model data and/or default values incorporated.

        # If GMAO modeled data is selected in ConfigWindow, and an ancillary field data file
        # is provided in Main Window, then use the model data to fill in gaps in the field
        # record. Otherwise, use the selected default values from ConfigWindow

        # This step is only necessary for the ancillary datasets that REQUIRE
        # either field or GMAO or GUI default values. The remaining ancillary data
        # are culled from datasets in groups in L1B
        ProcessL1b.includeModelDefaults(ancGroup, modRoot)

        # Add class-based files (RAW_UNCERTAINTIES)
        # classbased_dir = os.path.join(PATH_TO_DATA, 'Class_Based_Characterizations', # Needs to be revised for sorad
        #                             ConfigFile.settings['SensorType']+"_initial")  # classbased_dir required for FRM-cPol
        if ConfigFile.settings["SensorType"].lower() == "seabird" or  ConfigFile.settings["SensorType"].lower() == "trios":
            classbased_dir = os.path.join(PATH_TO_DATA, 'Class_Based_Characterizations', #
                                     ConfigFile.settings['SensorType']+"_initial")
        elif ConfigFile.settings["SensorType"].lower() == "sorad":
            classbased_dir = os.path.join(PATH_TO_DATA, 'Class_Based_Characterizations', # Hard-coded solution for sorad
                                     'TriOS' +"_initial")


        # The radCalDir is now the same for all cal/char regimes and regardless of whether files were downloaded from FidRadDB or not
        radcal_dir = os.path.join(CODE_HOME, 'Data', 'FidRadDB',ConfigFile.settings['SensorType'])

        if ConfigFile.settings['fL1bCal'] == 1:
            # classbased_dir = os.path.join(PATH_TO_DATA, 'Class_Based_Characterizations', ConfigFile.settings['SensorType']+"_initial")
            print("Factory SeaBird HyperOCR - uncertainty computed from class-based and Sirrex-7")
            node = ProcessL1b.read_unc_coefficient_factory(node, classbased_dir)
            if node is None:
                Utilities.writeLogFileAndPrint('Error running factory uncertainties.')
                return None

        # Add class-based files + RADCAL file
        elif ConfigFile.settings['fL1bCal'] == 2:
            print("Class-Based - uncertainty computed from class-based and RADCAL")
            print('Class-Based:', classbased_dir)
            print('RADCAL:', radcal_dir)

            node = ProcessL1b.read_unc_coefficient_class(node, classbased_dir)
            if node is None:
                Utilities.writeLogFileAndPrint('Error running class based uncertainties.')
                return None

        # Add full characterization files
        elif ConfigFile.settings['fL1bCal'] == 3:

            # NOTE: Does this method lead to to corrections being applied in addition to uncertainty estimates?s
            node = ProcessL1b.read_unc_coefficient_frm(node, classbased_dir)

            if node is None:
                Utilities.writeLogFileAndPrint('Error loading FRM characterization files. Check directory.')
                return None

        # Dark Correction
        if not ProcessL1b.processDarkCorrection(node, "ES"):
            Utilities.writeLogFileAndPrint('Error dark correcting ES')
            return None
        if not ProcessL1b.processDarkCorrection(node, "LI"):
            Utilities.writeLogFileAndPrint('Error dark correcting LI')
            return None
        if not ProcessL1b.processDarkCorrection(node, "LT"):
            Utilities.writeLogFileAndPrint('Error dark correcting LT')
            return None

        # For SeaBird (shutter darks), now that dark correction is complete, change the dark timestamps to their
        #   _ADJUSTED values (matching nearest lights) for the sake of filtering the data later
        for gp in node.groups:
            if '_DARK_L1AQC' in gp.id:
                gp.datasets['DATETAG'] = gp.datasets['DATETAG_ADJUSTED']
                gp.datasets['DATETAG'].id = 'DATETAG'
                gp.removeDataset('DATETAG_ADJUSTED')
                gp.datasets['TIMETAG2'] = gp.datasets['TIMETAG2_ADJUSTED']
                gp.datasets['TIMETAG2'].id = 'TIMETAG2'
                gp.removeDataset('TIMETAG2_ADJUSTED')
                gp.removeDataset('DATETIME')
                gp = Utilities.groupAddDateTime(gp)

        # # Interpolate only the Ancillary group, and then fold in model data
        # # This is run ahead of the other groups for all processing pathways. Anc group
        # # exists regardless of Ancillary file being provided
        # if not ProcessL1b_Interp.interp_Anc(node, outFilePath):
        #     Utilities.writeLogFileAndPrint('Error interpolating ancillary data')
        #     return None

        # # Need to fill in with model data here. This had previously been run on the GPS group, but now shifted to Ancillary group
        # ancGroup = node.getGroup("ANCILLARY_METADATA")
        # # Retrieve MERRA2 model ancillary data
        # if ConfigFile.settings["bL1bGetAnc"] ==1:
        #     Utilities.writeLogFileAndPrint('MERRA2 data for Wind and AOD may be used to replace blank values. Reading in model data...')
        #     modRoot = GetAnc.getAnc(ancGroup)
        # # Retrieve ECMWF model ancillary data
        # elif ConfigFile.settings["bL1bGetAnc"] == 2:
        #     Utilities.writeLogFileAndPrint('ECMWF data for Wind and AOD may be used to replace blank values. Reading in model data...')
        #     modRoot = GetAnc_ecmwf.getAnc_ecmwf(ancGroup)
        # else:
        #     modRoot = None

        # # Regardless of whether SunTracker is used, Ancillary data will have already been
        # # interpolated in L1B as long as the ancillary file was read in at L1AQC. Regardless, these need
        # # to have model data and/or default values incorporated.

        # # If GMAO modeled data is selected in ConfigWindow, and an ancillary field data file
        # # is provided in Main Window, then use the model data to fill in gaps in the field
        # # record. Otherwise, use the selected default values from ConfigWindow

        # # This step is only necessary for the ancillary datasets that REQUIRE
        # # either field or GMAO or GUI default values. The remaining ancillary data
        # # are culled from datasets in groups in L1B
        # ProcessL1b.includeModelDefaults(ancGroup, modRoot)

        # Calibration
        # Depending on the Configuration, process either the factory
        # calibration, class-based characterization, or the complete
        # instrument characterizations
        if ConfigFile.settings['fL1bCal'] == 1 or ConfigFile.settings['fL1bCal'] == 2:
            # Class-based radiometric processing is identical to factory processing
            # Results may differs due to updated calibration files but the two
            # process are the same. The class-based characterisation will be used
            # in the uncertainty computation.
            calFolder = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
            calPath = os.path.join(PATH_TO_CONFIG, calFolder)
            print("Read CalibrationFile ", calPath)
            calibrationMap = CalibrationFileReader.read(calPath)
            ProcessL1b_FactoryCal.processL1b_SeaBird(node, calibrationMap)

        elif ConfigFile.settings['fL1bCal'] == 3:
            calFolder = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
            calPath = os.path.join(PATH_TO_CONFIG, calFolder)
            print("Read CalibrationFile ", calPath)
            calibrationMap = CalibrationFileReader.read(calPath)
            if not ProcessL1b_FRMCal.processL1b_SeaBird(node, calibrationMap):
                Utilities.writeLogFileAndPrint('Error in ProcessL1b.process_FRM_calibration')
                return None

        # Interpolation
        # Used with both TriOS and SeaBird
        # Match instruments to a common timestamp (slowest shutter, should be Lt) and
        # interpolate to the chosen spectral resolution. HyperSAS instruments operate on
        # different timestamps and wavebands, so interpolation is required.
        node = ProcessL1b_Interp.processL1b_Interp(node, outFilePath)

        # Datetime format is not supported in HDF5; already removed in ProcessL1b_Interp.py

        return node
