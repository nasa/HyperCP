''' Process L1AQC to L1B '''
import os
import datetime as dt
# import calendar
# from inspect import currentframe, getframeinfo
# import glob
# from datetime import datetime
import numpy as np
import pandas as pd

from Source import PATH_TO_DATA
from Source import PATH_TO_CONFIG
from Source.ProcessL1b import ProcessL1b
# from Source.ProcessL1b_FactoryCal import ProcessL1b_FactoryCal
from Source.ProcessL1b_FRMCal import ProcessL1b_FRMCal
from Source.ConfigFile import ConfigFile
from Source.CalibrationFileReader import CalibrationFileReader
from Source.ProcessL1b_Interp import ProcessL1b_Interp
from Source.Utilities import Utilities
from Source.GetAnc import GetAnc
from Source.GetAnc_ecmwf import GetAnc_ecmwf

class ProcessL1bDALEC:
    '''L1B for DALEC'''

    @staticmethod
    def read_unc_coefficient_factory(root):
        ''' SeaBird or TriOS'''
        # Read Uncertainties_new_char from provided files
        gp = root.addGroup("RAW_UNCERTAINTIES")
        gp.attributes['FrameType'] = 'NONE'  # add FrameType = None so grp passes a quality check later

        # Unc dataset renaming
        Utilities.RenameUncertainties_Class(root)

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
       #Utilities.UncTempCorrection(root)

        return root

    @staticmethod
    def processES(node):
        gp=node.getGroup('ES')
        gpc=node.getGroup('CAL_COEF')
        delta_t_ed=float(gpc.attributes['Delta_T_Ed'])
        tref=float(gpc.attributes['Tref'])
        d0=float(gpc.attributes['d0'])
        d1=float(gpc.attributes['d1'])
        ds=gp.datasets['ES']
        dc=gp.datasets['DARK_CNT'].data['ES'].tolist()
        inttime=gp.datasets['INTTIME'].data['ES'].tolist()
        temp=gp.datasets['SPECTEMP'].data['NONE'].tolist()
        cd=gpc.datasets['Cal_ES']
        a0 = cd.data['a0'].tolist()
        tempco_ed=cd.data['Tempco_Ed'].tolist()

        # K1=d0*(V-DC)+d1
        # Ed=a0*((V-DC)/(Inttime+DeltaT_Ed)/K1)/(Tempco_Ed*(Temp-Tref)+1)

        for i in range(ds.data.shape[0]):
            c1=inttime[i]+delta_t_ed
            for j in range(cd.data.shape[0]):
                ds.data[i][j] = 100.0*a0[j]*((ds.data[i][j]-dc[i])/c1
                /(d1*(ds.data[i][j]-dc[i])+d0))/(tempco_ed[j]*(temp[i]-tref)+1)

    @staticmethod
    def processLT(node):
        gp=node.getGroup('LT')
        gpc=node.getGroup('CAL_COEF')
        delta_t_lu=float(gpc.attributes['Delta_T_Lu'])
        tref=float(gpc.attributes['Tref'])
        e0=float(gpc.attributes['e0'])
        e1=float(gpc.attributes['e1'])
        ds=gp.datasets['LT']
        dc=gp.datasets['DARK_CNT'].data['LT'].tolist()
        inttime=gp.datasets['INTTIME'].data['LT'].tolist()
        temp=gp.datasets['SPECTEMP'].data['NONE'].tolist()
        cd=gpc.datasets['Cal_LT']
        b0 = cd.data['b0'].tolist()
        tempco_lu=cd.data['Tempco_Lu'].tolist()

        # K2=e1*(V-DC)+e0
        # Lu=b0*((V-DC)/(Inttime+DeltaT_Lu)/K2)/(Tempco_Lu*(Temp-Tref)+1)

        for i in range(ds.data.shape[0]):
            c1=inttime[i]+delta_t_lu
            for j in range(cd.data.shape[0]):
                ds.data[i][j] = 100.0*b0[j]*((ds.data[i][j]-dc[i])/c1
                /(e1*(ds.data[i][j]-dc[i])+e0))/(tempco_lu[j]*(temp[i]-tref)+1)

    @staticmethod
    def processLI(node):
        gp=node.getGroup('LI')
        gpc=node.getGroup('CAL_COEF')
        delta_t_lsky=float(gpc.attributes['Delta_T_Lsky'])
        tref=float(gpc.attributes['Tref'])
        f0=float(gpc.attributes['f0'])
        f1=float(gpc.attributes['f1'])
        ds=gp.datasets['LI']
        dc=gp.datasets['DARK_CNT'].data['LI'].tolist()
        inttime=gp.datasets['INTTIME'].data['LI'].tolist()
        temp=gp.datasets['SPECTEMP'].data['NONE'].tolist()
        cd=gpc.datasets['Cal_LI']
        c0 = cd.data['c0'].tolist()
        tempco_lsky=cd.data['Tempco_Lsky'].tolist()

        # K3=f0*(V-DC)+f1
        # Lsky=c0*((V-DC)/(Inttime+DeltaT_Lsky)/K3)/(Tempco_Lsky*(Temp-Tref)+1)

        for i in range(ds.data.shape[0]):
            c1=inttime[i]+delta_t_lsky
            for j in range(cd.data.shape[0]):
                ds.data[i][j] = 100.0*c0[j]*((ds.data[i][j]-dc[i])/c1
                /(f1*(ds.data[i][j]-dc[i])+f0))/(tempco_lsky[j]*(temp[i]-tref)+1)

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

        msg = f"ProcessL1bDALEC.processL1b: {timestr}"
        print(msg)
        Utilities.writeLogFile(msg)

        # Add a dataset to each group for DATETIME, as defined by TIMETAG2 and DATETAG
        node  = Utilities.rootAddDateTime(node)

        # Introduce a new group for carrying L1AQC data forward. Groups keep consistent timestamps across all datasets,
        #    so it has to be a new group to avoid conflict with interpolated timestamps.

        esGroup = node.addGroup('ES_L1AQC')
        liGroup = node.addGroup('LI_L1AQC')
        ltGroup = node.addGroup('LT_L1AQC')

        for gp in node.groups:
            if gp.id == 'ES':
                esGroup.copy(gp)
            elif gp.id == 'LI':
                liGroup.copy(gp)
            elif gp.id == 'LT':
                ltGroup.copy(gp)

        ######### PLACEHOOLDER: when DALEC class-based and full-FRM become available #########
        # classbased_dir needed for FRM whilst pol is handled in class-based way
        # classbased_dir = os.path.join(PATH_TO_DATA, 'Class_Based_Characterizations', ConfigFile.settings['SensorType'] + "_initial")
        #
        # # The radCalDir is now the same for all cal/char regimes and regardless of whether files were downloaded from FidRadDB or not
        # radcal_dir = ConfigFile.settings['calibrationPath']
        #
        # # Add Class-based characterization files if needed (RAW_UNCERTAINTIES)
        # if ConfigFile.settings['fL1bCal'] == 1:
        #     print("Factory DALEC - no uncertainty computation")
        #
        # # Add Class-based characterization files + RADCAL files
        # elif ConfigFile.settings['fL1bCal'] == 2:
        #
        #     print("Class-Based - uncertainty computed from class-based and RADCAL")
        #     print('Class-Based:', classbased_dir)
        #     print('RADCAL:', radcal_dir)
        #     node = ProcessL1b.read_unc_coefficient_class(node, classbased_dir)
        #     if node is None:
        #         Utilities.writeLogFileAndPrint('Error running class based uncertainties.')
        #         return None
        #
        # # Or add Full characterization files (RAW_UNCERTAINTIES)
        # elif ConfigFile.settings['fL1bCal'] == 3:
        #
        #     node = ProcessL1b.read_unc_coefficient_frm(node)
        #     if node is None:
        #         Utilities.writeLogFileAndPrint('Error loading FRM characterization files. Check directory.')
        #         return None
        ############################################################################################################

        if not ProcessL1b_Interp.interp_Anc(node, outFilePath):
            msg = 'Error interpolating ancillary data'
            print(msg)
            Utilities.writeLogFile(msg)
            return None

        # Need to fill in with model data here. This had previously been run on the GPS group, but now shifted to Ancillary group
        ancGroup = node.getGroup("ANCILLARY_METADATA")
        # Retrieve MERRA2 model ancillary data
        if ConfigFile.settings["bL1bGetAnc"] ==1:
            msg = 'MERRA2 data for Wind and AOD may be used to replace blank values. Reading in model data...'
            print(msg)
            Utilities.writeLogFile(msg)
            modRoot = GetAnc.getAnc(ancGroup)
        # Retrieve ECMWF model ancillary data
        elif ConfigFile.settings["bL1bGetAnc"] == 2:
            msg = 'ECMWF data for Wind and AOD may be used to replace blank values. Reading in model data...'
            print(msg)
            Utilities.writeLogFile(msg)
            modRoot = GetAnc_ecmwf.getAnc_ecmwf(ancGroup)
        else:
            modRoot = None

        # if modRoot is not None:
        # Regardless of whether SolarTracker/pySAS is used, Ancillary data will have been already been
        # interpolated in L1B as long as the ancillary file was read in at L1AQC. Regardless, these need
        # to have model data and/or default values incorporated.

        # If GMAO modeled data is selected in ConfigWindow, and an ancillary field data file
        # is provided in Main Window, then use the model data to fill in gaps in the field
        # record. Otherwise, use the selected default values from ConfigWindow

        # This step is only necessary for the ancillary datasets that REQUIRE
        # either field or GMAO or GUI default values. The remaining ancillary data
        # are culled from datasets in groups in L1B
        ProcessL1b.includeModelDefaults(ancGroup, modRoot)

        if ConfigFile.settings["fL1bCal"] == 1 or ConfigFile.settings["fL1bCal"] == 2:
            # Calculate 6S model
            # Run elsewhere for FRM-regime
            print('Running sixS')

            sensortype = "ES"
            # Irradiance direct and diffuse ratio
            res_sixS = ProcessL1b_FRMCal.get_direct_irradiance_ratio(node, sensortype)

            # Store sixS results in new group
            grp = node.getGroup(sensortype)
            solar_zenith = res_sixS['solar_zenith']
            # ProcessL1b_FRMCal.get_direct_irradiance_ratio uses Es bands to run 6S and then works around bands that
            #  don't have values from Tartu for full FRM. Here, use all the Es bands.
            direct_ratio = res_sixS['direct_ratio']
            diffuse_ratio = res_sixS['diffuse_ratio']
            # sixS model irradiance is in W/m^2/um, scale by 10 to match HCP units
            # model_irr = (res_sixS['direct_irr']+res_sixS['diffuse_irr']+res_sixS['env_irr'])[:,ind_raw_data]/10
            model_irr = (res_sixS['direct_irr']+res_sixS['diffuse_irr']+res_sixS['env_irr'])/10
            # model_irr = (res_sixS['direct_irr']+res_sixS['diffuse_irr']+res_sixS['env_irr'])[:,ind_nocal==False]/10

            sixS_grp = node.addGroup("SIXS_MODEL")
            for dsname in ["DATETAG", "TIMETAG2", "DATETIME"]:
                # copy datetime dataset for interp process
                ds = sixS_grp.addDataset(dsname)
                ds.data = grp.getDataset(dsname).data

            ds = sixS_grp.addDataset("sixS_irradiance")

            irr_grp = node.getGroup('ES_L1AQC')
            str_wvl = np.asarray(pd.DataFrame(irr_grp.getDataset(sensortype).data).columns)
            ds_dt = np.dtype({'names': str_wvl,'formats': [np.float64]*len(str_wvl)})
            rec_arr = np.rec.fromarrays(np.array(model_irr).transpose(), dtype=ds_dt)
            ds.data = rec_arr

            ds = sixS_grp.addDataset("direct_ratio")
            ds_dt = np.dtype({'names': str_wvl,'formats': [np.float64]*len(str_wvl)})
            rec_arr = np.rec.fromarrays(np.array(direct_ratio).transpose(), dtype=ds_dt)
            ds.data = rec_arr

            ds = sixS_grp.addDataset("diffuse_ratio")
            ds_dt = np.dtype({'names': str_wvl,'formats': [np.float64]*len(str_wvl)})
            rec_arr = np.rec.fromarrays(np.array(diffuse_ratio).transpose(), dtype=ds_dt)
            ds.data = rec_arr

            ds = sixS_grp.addDataset("solar_zenith")
            ds.columns["solar_zenith"] = solar_zenith
            ds.columnsToDataset()

        # Calibration
        # Depending on the Configuration, process either the factory
        # calibration, class-based characterization, or the complete
        # instrument characterizations
        if ConfigFile.settings['fL1bCal'] == 1 or ConfigFile.settings['fL1bCal'] == 2:
            # Class-based radiometric processing is identical to factory processing
            # Results may differs due to updated calibration files but the two
            # process are the same. The class-based characterisation will be used
            # in the uncertainty computation.
            ProcessL1bDALEC.processES(node)
            ProcessL1bDALEC.processLT(node)
            ProcessL1bDALEC.processLI(node)

        elif ConfigFile.settings['fL1bCal'] == 3:
            calFolder = os.path.splitext(ConfigFile.filename)[0] + "_Calibration"
            calPath = os.path.join(PATH_TO_CONFIG, calFolder)
            print("Read CalibrationFile ", calPath)
            calibrationMap = CalibrationFileReader.read(calPath)
            if not ProcessL1b_FRMCal.processL1b_SeaBird(node, calibrationMap):
                msg = 'Error in ProcessL1b.process_FRM_calibration'
                print(msg)
                Utilities.writeLogFile(msg)
                return None

        # Interpolation
        # Used with both TriOS and SeaBird
        # Match instruments to a common timestamp (slowest shutter, should be Lt) and
        # interpolate to the chosen spectral resolution. HyperSAS instruments operate on
        # different timestamps and wavebands, so interpolation is required.
        node = ProcessL1b_Interp.processL1b_Interp(node, outFilePath)

        # Datetime format is not supported in HDF5; already removed in ProcessL1b_Interp.py
        node.attributes["LI_UNITS"] = 'uW/cm^2/nm/sr'
        node.attributes["LT_UNITS"] = 'uW/cm^2/nm/sr'
        node.attributes["ES_UNITS"] = 'uW/cm^2/nm'

        return node
