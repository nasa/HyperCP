""" Build PDF report for each file """
import os
import glob
import random
from fpdf import FPDF

from Source import PATH_TO_CONFIG
from Source.SeaBASSHeader import SeaBASSHeader
from Source.ConfigFile import ConfigFile


class PDF(FPDF):

    def header(self):
        # Times bold 15
        self.set_font('Times', 'B', 15)
        # Calculate width of title and position
        w = self.get_string_width(self.title)
        # self.set_x((50 - w) / 2)
        # Colors of frame, background and text
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(0, 0, 0)
        # Thickness of frame (1 mm)
        self.set_line_width(1)
        # Title
        self.cell(w, 9, self.title, 1, 1, 'C', 1)
        # Line break
        self.ln(10)

    def format_intro(self, level, headerBlock, commentsDict, root):
        # Intros
        intro = None
        if level == "L1A":
            intro = 'Raw binary to HDF5 and filter data on SZA.\n'

            # If level completed (i.e. L2), use the attributes of the file, otherwise, use the ConfigFile settings
            metaData = ' \n'
            metaData += 'Processing Parameters and metadata: \n'
            if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
                metaData += f'HyperInSPACE version: {root.attributes["HYPERINSPACE"]}\n'
                if 'SZA_FILTER_L1A' in root.attributes:
                    metaData += f'SZA Filter (L1A): {root.attributes["SZA_FILTER_L1A"]}\n'
            else:
                metaData += f'HyperInSPACE version: {commentsDict[" HyperInSPACE vers"]}\n'
                if ConfigFile.settings['bL1aCleanSZA']:
                    metaData += f'SZA Limit (L1A): {ConfigFile.settings["fL1aCleanSZAMax"]}\n'
            comments2 = headerBlock['other_comments'].split('!')
            for comment in comments2:
                if comment != '':
                    metaData += comment
            for key,value in headerBlock.items():
                if key != 'comments' and key != 'other_comments' and \
                    key != 'data_file_name' and key != 'missing' and \
                        key != 'delimiter':
                    # L1A data has not populated file-specific metadata into the SeaBASS header yet
                    if key != 'station' and key != 'original_file_name' and \
                        'start' not in key and 'end' not in key and 'latitude' not in key and \
                            'longitude' not in key and 'wind' not in key and \
                                'cloud' not in key and 'wave' not in key and 'secchi' not in key and \
                                    'water_depth' not in key:
                        metaData += f'/{key}={value}\n'

        if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
            gpDict = {}
            for gp in root.groups:
                gpDict[gp.id] = gp

        if level == "L1AQC":
            intro = 'Low level QC (pitch, roll, yaw, and azimuth) and deglitching.\n'
            metaData = ' \n'
            metaData += 'Processing Parameters: \n'


            if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
                if 'HOME_ANGLE' in root.attributes:
                    metaData += f'Rotator Home Angle: {root.attributes["HOME_ANGLE"]}\n'
                if 'ROTATOR_DELAY_FILTER' in root.attributes:
                    metaData += f'Rotator Delay: {root.attributes["ROTATOR_DELAY_FILTER"]}\n'
                if 'PITCH_ROLL_FILTER' in root.attributes:
                    metaData += f'Pitch/Roll Filter: {root.attributes["PITCH_ROLL_FILTER"]}\n'
                if 'ROTATOR_ANGLE_MIN' in root.attributes:
                    metaData += f'Rotator Min Filter: {root.attributes["ROTATOR_ANGLE_MIN"]}\n'
                    metaData += f'Rotator Max Filter: {root.attributes["ROTATOR_ANGLE_MAX"]}\n'
                if 'RELATIVE_AZIMUTH_MIN' in root.attributes:
                    metaData += f'Rel Azimuth Min: {root.attributes["RELATIVE_AZIMUTH_MIN"]}\n'
                    metaData += f'Rel Azimuth Max: {root.attributes["RELATIVE_AZIMUTH_MAX"]}\n'

                # These deglitching parameters might be in root.attributes if from files L1AQC or L1B (or L1BQC?),
                # or within their respective groups at L2
                if root.attributes['L1AQC_DEGLITCH'] == 'ON':
                    if 'ES_WINDOW_DARK' in root.attributes:
                        # Low level has these in root, but L2 has them in groups
                        metaData += f'ES Dark Window: {root.attributes["ES_WINDOW_DARK"]}\n'
                        metaData += f'ES Light Window: {root.attributes["ES_WINDOW_LIGHT"]}\n'
                        metaData += f'ES Dark Sigma: {root.attributes["ES_SIGMA_DARK"]}\n'
                        metaData += f'ES Light Sigma: {root.attributes["ES_SIGMA_LIGHT"]}\n'
                        metaData += f'LT Dark Window: {root.attributes["LT_WINDOW_DARK"]}\n'
                        metaData += f'LT Light Window: {root.attributes["LT_WINDOW_LIGHT"]}\n'
                        metaData += f'LT Dark Sigma: {root.attributes["LT_SIGMA_DARK"]}\n'
                        metaData += f'LT Light Sigma: {root.attributes["LT_SIGMA_LIGHT"]}\n'
                        metaData += f'LI Dark Window: {root.attributes["LI_WINDOW_DARK"]}\n'
                        metaData += f'LI Light Window: {root.attributes["LI_WINDOW_LIGHT"]}\n'
                        metaData += f'LI Dark Sigma: {root.attributes["LI_SIGMA_DARK"]}\n'
                        metaData += f'LI Light Sigma: {root.attributes["LI_SIGMA_LIGHT"]}\n'
                        if ConfigFile.settings['bL1aqcThreshold']:
                            metaData += f'ES Light Thresh. Band: {root.attributes["ES_MINMAX_BAND_LIGHT"]}\n'
                            metaData += f'ES Light Min.: {root.attributes["ES_MIN_LIGHT"]}\n'
                            metaData += f'ES Light Max.: {root.attributes["ES_MAX_LIGHT"]}\n'
                            metaData += f'ES Dark Thresh. Band: {root.attributes["ES_MINMAX_BAND_DARK"]}\n'
                            metaData += f'ES Dark Min.: {root.attributes["ES_MIN_DARK"]}\n'
                            metaData += f'ES LDark Max.: {root.attributes["ES_MAX_DARK"]}\n'

                            metaData += f'LI Light Thresh. Band: {root.attributes["LI_MINMAX_BAND_LIGHT"]}\n'
                            metaData += f'LI Light Min.: {root.attributes["LI_MIN_LIGHT"]}\n'
                            metaData += f'LI Light Max.: {root.attributes["LI_MAX_LIGHT"]}\n'
                            metaData += f'LI Dark Thresh. Band: {root.attributes["LI_MINMAX_BAND_DARK"]}\n'
                            metaData += f'LI Dark Min.: {root.attributes["LI_MIN_DARK"]}\n'
                            metaData += f'LI LDark Max.: {root.attributes["LI_MAX_DARK"]}\n'

                            metaData += f'LT Light Thresh. Band: {root.attributes["LT_MINMAX_BAND_LIGHT"]}\n'
                            metaData += f'LT Light Min.: {root.attributes["LT_MIN_LIGHT"]}\n'
                            metaData += f'LT Light Max.: {root.attributes["LT_MAX_LIGHT"]}\n'
                            metaData += f'LT Dark Thresh. Band: {root.attributes["LT_MINMAX_BAND_DARK"]}\n'
                            metaData += f'LT Dark Min.: {root.attributes["LT_MIN_DARK"]}\n'
                            metaData += f'LT LDark Max.: {root.attributes["LT_MAX_DARK"]}\n'
                    else: # Level 2 files have these in Group attributes
                        metaData += f'ES Dark Window: {gpDict["IRRADIANCE"].attributes["ES_WINDOW_DARK"]}\n'
                        metaData += f'ES Light Window: {gpDict["IRRADIANCE"].attributes["ES_WINDOW_LIGHT"]}\n'
                        metaData += f'ES Dark Sigma: {gpDict["IRRADIANCE"].attributes["ES_SIGMA_DARK"]}\n'
                        metaData += f'ES Light Sigma: {gpDict["IRRADIANCE"].attributes["ES_SIGMA_LIGHT"]}\n'
                        metaData += f'LT Dark Window: {gpDict["RADIANCE"].attributes["LT_WINDOW_DARK"]}\n'
                        metaData += f'LT Light Window: {gpDict["RADIANCE"].attributes["LT_WINDOW_LIGHT"]}\n'
                        metaData += f'LT Dark Sigma: {gpDict["RADIANCE"].attributes["LT_SIGMA_DARK"]}\n'
                        metaData += f'LT Light Sigma: {gpDict["RADIANCE"].attributes["LT_SIGMA_LIGHT"]}\n'
                        metaData += f'LI Dark Window: {gpDict["RADIANCE"].attributes["LI_WINDOW_DARK"]}\n'
                        metaData += f'LI Light Window: {gpDict["RADIANCE"].attributes["LI_WINDOW_LIGHT"]}\n'
                        metaData += f'LI Dark Sigma: {gpDict["RADIANCE"].attributes["LI_SIGMA_DARK"]}\n'
                        metaData += f'LI Light Sigma: {gpDict["RADIANCE"].attributes["LI_SIGMA_LIGHT"]}\n'

                        if ConfigFile.settings['bL1aqcThreshold']:
                            metaData += f'ES Light Thresh. Band: {gpDict["IRRADIANCE"].attributes["ES_MINMAX_BAND_LIGHT"]}\n'
                            metaData += f'ES Light Min.: {gpDict["IRRADIANCE"].attributes["ES_MIN_LIGHT"]}\n'
                            metaData += f'ES Light Max.: {gpDict["IRRADIANCE"].attributes["ES_MAX_LIGHT"]}\n'
                            metaData += f'ES Dark Thresh. Band: {gpDict["IRRADIANCE"].attributes["ES_MINMAX_BAND_DARK"]}\n'
                            metaData += f'ES Dark Min.: {gpDict["IRRADIANCE"].attributes["ES_MIN_DARK"]}\n'
                            metaData += f'ES LDark Max.: {gpDict["IRRADIANCE"].attributes["ES_MAX_DARK"]}\n'

                            metaData += f'LI Light Thresh. Band: {gpDict["RADIANCE"].attributes["LI_MINMAX_BAND_LIGHT"]}\n'
                            metaData += f'LI Light Min.: {gpDict["RADIANCE"].attributes["LI_MIN_LIGHT"]}\n'
                            metaData += f'LI Light Max.: {gpDict["RADIANCE"].attributes["LI_MAX_LIGHT"]}\n'
                            metaData += f'LI Dark Thresh. Band: {gpDict["RADIANCE"].attributes["LI_MINMAX_BAND_DARK"]}\n'
                            metaData += f'LI Dark Min.: {gpDict["RADIANCE"].attributes["LI_MIN_DARK"]}\n'
                            metaData += f'LI LDark Max.: {gpDict["RADIANCE"].attributes["LI_MAX_DARK"]}\n'

                            metaData += f'LT Light Thresh. Band: {gpDict["RADIANCE"].attributes["LT_MINMAX_BAND_LIGHT"]}\n'
                            metaData += f'LT Light Min.: {gpDict["RADIANCE"].attributes["LT_MIN_LIGHT"]}\n'
                            metaData += f'LT Light Max.: {gpDict["RADIANCE"].attributes["LT_MAX_LIGHT"]}\n'
                            metaData += f'LT Dark Thresh. Band: {gpDict["RADIANCE"].attributes["LT_MINMAX_BAND_DARK"]}\n'
                            metaData += f'LT Dark Min.: {gpDict["RADIANCE"].attributes["LT_MIN_DARK"]}\n'
                            metaData += f'LT Dark Max.: {gpDict["RADIANCE"].attributes["LT_MAX_DARK"]}\n'
            else:
                # Failed run, use values from Config
                metaData += f'Rotator Home Angle: {ConfigFile.settings["fL1aqcRotatorHomeAngle"]}\n'
                if ConfigFile.settings['bL1aqcSunTracker']:
                    if ConfigFile.settings['bL1aqcRotatorDelay']:
                        metaData += f'Rotator Delay: {ConfigFile.settings["fL1aqcRotatorDelay"]}\n'
                    if ConfigFile.settings['bL1aqcCleanPitchRoll']:
                        metaData += f'Pitch/Roll Filter: {ConfigFile.settings["fL1aqcPitchRollPitch"]}\n'
                    if ConfigFile.settings['bL1aqcRotatorAngle']:
                        metaData += f'Rotator Min: {ConfigFile.settings["fL1aqcRotatorAngleMin"]}\n'
                        metaData += f'Rotator Max: {ConfigFile.settings["fL1aqcRotatorAngleMax"]}\n'
                if ConfigFile.settings['bL1aqcCleanSunAngle']:
                    metaData += f'Rel Azimuth Min: {ConfigFile.settings["fL1aqcSunAngleMin"]}\n'
                    metaData += f'Rel Azimuth Max: {ConfigFile.settings["fL1aqcSunAngleMax"]}\n'

                if ConfigFile.settings['bL1aqcDeglitch']:
                    metaData += f'ES Dark Window: {ConfigFile.settings["fL1aqcESWindowDark"]}\n'
                    metaData += f'ES Light Window: {ConfigFile.settings["fL1aqcESWindowLight"]}\n'
                    metaData += f'ES Dark Sigma: {ConfigFile.settings["fL1aqcESSigmaDark"]}\n'
                    metaData += f'ES Light Sigma: {ConfigFile.settings["fL1aqcESSigmaLight"]}\n'
                    metaData += f'LT Dark Window: {ConfigFile.settings["fL1aqcLTWindowDark"]}\n'
                    metaData += f'LT Light Window: {ConfigFile.settings["fL1aqcLTWindowLight"]}\n'
                    metaData += f'LT Dark Sigma: {ConfigFile.settings["fL1aqcLTSigmaDark"]}\n'
                    metaData += f'LT Light Sigma: {ConfigFile.settings["fL1aqcLTSigmaLight"]}\n'
                    metaData += f'LI Dark Window: {ConfigFile.settings["fL1aqcLIWindowDark"]}\n'
                    metaData += f'LI Light Window: {ConfigFile.settings["fL1aqcLIWindowLight"]}\n'
                    metaData += f'LI Dark Sigma: {ConfigFile.settings["fL1aqcLISigmaDark"]}\n'
                    metaData += f'LI Light Sigma: {ConfigFile.settings["fL1aqcLISigmaLight"]}\n'

                    if ConfigFile.settings['bL1aqcThreshold']:
                        metaData += f'ES Light Thresh. Band: {ConfigFile.settings["fL1aqcESMinMaxBandLight"]}\n'
                        metaData += f'ES Dark Thresh. Band: {ConfigFile.settings["fL1aqcESMinMaxBandDark"]}\n'
                        metaData += f'ES Min.: {ConfigFile.settings["fL1aqcESMinLight"]}\n'
                        metaData += f'ES Max.: {ConfigFile.settings["fL1aqcESMaxLight"]}\n'
                        metaData += f'LI Dark Thresh. Band: {ConfigFile.settings["fL1aqcLIMinMaxBandDark"]}\n'
                        metaData += f'LI Min.: {ConfigFile.settings["fL1aqcLIMinLight"]}\n'
                        metaData += f'LI Max.: {ConfigFile.settings["fL1aqcLIMaxLight"]}\n'
                        metaData += f'LT Dark Thresh. Band: {ConfigFile.settings["fL1aqcLTMinMaxBandDark"]}\n'
                        metaData += f'LT Min.: {ConfigFile.settings["fL1aqcLTMinLight"]}\n'
                        metaData += f'LT Max.: {ConfigFile.settings["fL1aqcLTMaxLight"]}\n'

        if level == "L1B":
            intro = 'Dark correction. Calibration and/or full characterization. Match timestamps & wavebands.\n'
            metaData = ' \n'
            metaData += 'Processing Parameters: None\n'
            if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
                metaData += f'Cal. Type: {root.attributes["CAL_TYPE"]}\n'
                metaData += f'Wavelength Interp Int: {root.attributes["WAVE_INTERP"]}\n'
            else:
                if  ConfigFile.settings["fL1bCal"] == 1:
                    metaData += 'Cal. Type: Default/Factory'
                elif ConfigFile.settings["fL1bCal"] == 2:
                    metaData += 'Cal. Type: Class-based'
                elif ConfigFile.settings["fL1bCal"] == 3:
                    metaData += 'Cal. Type: Full-FRM'
                # metaData += f'Wavelength Interp Int: {ConfigFile.settings["fL1bInterpInterval"]}\n'
                if  ConfigFile.settings["fL1bThermal"] == 1:
                    metaData += 'Internal working temp source: Internal thermistor\n'
                if  ConfigFile.settings["fL1bThermal"] == 2:
                    metaData += 'Internal working temp source: Air temperature + margin\n'
                if  ConfigFile.settings["fL1bThermal"] == 3:
                    metaData += 'Internal working temp source: Caps-on dark file unless < 30C.\n'                    

        if level == "L1BQC":
            intro = 'Apply more quality control filters.\n'

            metaData = ' \n'
            metaData += 'Processing Parameters: \n'
            if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
                metaData += f'Max Wind: {root.attributes["WIND_MAX"]}\n'
                metaData += f'Min SZA: {root.attributes["SZA_MIN"]}\n'
                metaData += f'Max SZA: {root.attributes["SZA_MAX"]}\n'
                if 'ES_SPEC_FILTER' in gpDict['IRRADIANCE'].attributes:
                    metaData += f'Filter Sigma Es: {gpDict["IRRADIANCE"].attributes["ES_SPEC_FILTER"]}\n'
                    metaData += f'Filter Sigma Li: {gpDict["RADIANCE"].attributes["LI_SPEC_FILTER"]}\n'
                    metaData += f'Filter Sigma Lt: {gpDict["RADIANCE"].attributes["LT_SPEC_FILTER"]}\n'
                if 'CLOUD_FILTER' in root.attributes:
                    metaData += f'Cloud Filter: {root.attributes["CLOUD_FILTER"]}\n'
                    metaData += f'Es Filter: {gpDict["IRRADIANCE"].attributes["ES_FILTER"]}\n'
                    metaData += f'Dawn/Dusk Filter: {root.attributes["DAWN_DUSK_FILTER"]}\n'
                    metaData += f'Rain/Humidity Filter: {root.attributes["RAIN_RH_FILTER"]}\n'
            else:
                metaData += f'Max Wind: {ConfigFile.settings["fL1bqcMaxWind"]}\n'
                metaData += f'Min SZA: {ConfigFile.settings["fL1bqcSZAMin"]}\n'
                metaData += f'Max SZA: {ConfigFile.settings["fL1bqcSZAMax"]}\n'
                if ConfigFile.settings['bL1bqcEnableSpecQualityCheck']:
                    metaData += f'Filter Sigma Es: {ConfigFile.settings["fL1bqcSpecFilterEs"]}\n'
                    metaData += f'Filter Sigma Li: {ConfigFile.settings["fL1bqcSpecFilterLi"]}\n'
                    metaData += f'Filter Sigma Lt: {ConfigFile.settings["fL1bqcSpecFilterLt"]}\n'
                if ConfigFile.settings['bL1bqcEnableQualityFlags']:
                    metaData += f'Cloud Filter: {ConfigFile.settings["fL1bqcCloudFlag"]}\n'
                    metaData += f'Es Filter: {ConfigFile.settings["fL1bqcSignificantEsFlag"]}\n'
                    metaData += f'Dawn/Dusk Filter: {ConfigFile.settings["fL1bqcDawnDuskFlag"]}\n'
                    metaData += f'Rain/Humidity Filter: {ConfigFile.settings["fL1bqcRainfallHumidityFlag"]}\n'

        if level == "L2":
            intro = 'Apply temporal binning,station selection, glint correction,\n'\
                'NIR corrections, reflectance calculation, and OC product calculation.\n'

            metaData = ' \n'
            metaData += 'Processing Parameters: \n'
            if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
                metaData += f'Ensemble Duration: {root.attributes["ENSEMBLE_DURATION"]}\n'
                if '%LT_FILTER' in gpDict['RADIANCE'].attributes:
                    metaData += f'Percent Lt Filter: {gpDict["RADIANCE"].attributes["%LT_FILTER"]}\n'
                metaData += f'Glint_Correction: {gpDict["REFLECTANCE"].attributes["GLINT_CORR"]}\n'
                if 'NIR_RESID_CORR' in gpDict['REFLECTANCE'].attributes:
                    metaData += f'NIR Correction: {gpDict["REFLECTANCE"].attributes["NIR_RESID_CORR"]}\n'
                if 'NEGATIVE_VALUE_FILTER' in gpDict['REFLECTANCE'].attributes:
                    metaData += f'Remove Negatives: {gpDict["REFLECTANCE"].attributes["NEGATIVE_VALUE_FILTER"]}\n'
            else:
                metaData += f'Ensemble Duration: {ConfigFile.settings["fL2TimeInterval"]}\n'
                if ConfigFile.settings['bL2EnablePercentLt']:
                    metaData += f'Percent Lt Filter: {ConfigFile.settings["fL2PercentLt"]}\n'
                if ConfigFile.settings['bL2ZhangRho']:
                    metaData += 'Glint_Correction: Zhang et al. 2017'
                if ConfigFile.settings['bL2DefaultRho']:
                    metaData += 'Glint_Correction: Mobley 1999'
                if ConfigFile.settings['bL2PerformNIRCorrection']:
                    if ConfigFile.settings['bL2SimpleNIRCorrection']:
                        metaData += 'NIR Correction: Mueller and Austin 1995'
                    if ConfigFile.settings['bL2SimSpecNIRCorrection']:
                        metaData += 'NIR Correction: Ruddick et al. 2005/2006'
                else:
                    metaData += 'NIR Correction: None'
                if ConfigFile.settings['bL2NegativeSpec']:
                    metaData += 'Remove Negatives: ON'

        metaData += ' \n'
        return intro, metaData


    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Times italic 8
        self.set_font('Times', 'I', 8)
        # Text color in gray
        self.set_text_color(128)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def chapter_title(self, num, label):
        # Times 12
        self.set_font('Times', '', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, f'{num} : {label}', 0, 1, 'L', 1)
        # Line break
        self.ln(4)

    def chapter_body(self, inLog, headerBlock, level, inPlotPath, filebasename, root):

        self.set_font('Times', '', 12)

        #  This is the old method of pulling parameters from the SeaBASS Header.
        #     Shift to using root attributes from the file. Preserved here only to retain features not in
        #     ConfigFile settings
        comments1 = headerBlock['comments'].split('!')
        commentsDict = {}
        for comment in comments1:
            key, value = comment.split(' = ') if ' = ' in comment \
                else ('','')
            commentsDict[key] = value

        intro, metaData = self.format_intro(level, headerBlock, commentsDict, root)

        # Output justified text
        self.multi_cell(0, 5, intro)
        self.multi_cell(0, 5, metaData)
        self.multi_cell(0, 5, "Process log:\n")

        # Read text log file
        with open(inLog, 'rb') as fh:
            txt = fh.read().decode('latin-1')

        # Output justified text
        self.multi_cell(0, 5, txt)
        # Line break
        self.ln()

        # Figures
        if level == "L1AQC":
            inPath = os.path.join(inPlotPath, 'L1AQC_Anoms')

            self.cell(0, 6, 'Example Deglitching', 0, 1, 'L', 1)
            self.multi_cell(0, 5, 'Randomized. Complete plots of hyperspectral \n'\
                'deglitching from anomaly analysis can be found in [output_directory]/Plots/L1AQC_Anoms.\n')

            print('Adding deglitching plots...')
            # ES
            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1A_ESDark_*.png' ))
            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.\n")

            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1A_ESLight_*.png' ))

            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.\n")

            # LI
            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1A_LIDark_*.png' ))
            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.\n")

            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1A_LILight_*.png' ))
            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.\n")

            # LT
            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1A_LTDark_*.png' ))
            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.\n")

            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1A_LTLight_*.png' ))
            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.\n")

        if level == "L1B":
            inPath = os.path.join(inPlotPath, f'{level}_Interp')
            self.cell(0, 6, 'Example Temporal Interpolations', 0, 1, 'L', 1)
            self.multi_cell(0, 5, 'Randomized. Complete plots of hyperspectral \n'\
                'interpolations can be found in [output_directory]/Plots/L1B_Interp.\n')

            fileList = glob.glob(os.path.join(inPath, f'{filebasename}_*.png'))
            # NOTE: Should screen out the sixS plots here at some point

            print('Adding interpolation plots...')
            if len(fileList) > 0:

                # for i in range(0, len(fileList)):
                res = [i for i in fileList if 'L1B_LI' not in i and 'L1B_ES' not in i and 'L1B_LT' not in i]
                for i, resi in enumerate(res):
                    self.image(resi, w = 175)
                res = [i for i in fileList if 'L1B_ES' in i]
                if len(res) >= 3:
                    for i in range (0, 3): #range(0, len(fileList)):
                        randIndx = random.randint(0, len(res))
                        self.image(res[i], w = 175)
                res = [i for i in fileList if 'L1B_LI' in i]
                if len(res) >= 3:
                    for i in range (0, 3): #range(0, len(fileList)):
                        randIndx = random.randint(0, len(res))
                        self.image(res[i], w = 175)
                res = [i for i in fileList if 'L1B_LT' in i]
                if len(res) >= 3:
                    for i in range (0, 3): #range(0, len(fileList)):
                        randIndx = random.randint(0, len(res))
                        self.image(res[i], w = 175)
            else:
                self.multi_cell(0, 5, "None found.\n")

            # Not sure what happened to the spectral interpolation plotting...
            # inPath = os.path.join(inPlotPath, 'L1B_Interp')
            # self.cell(0, 6, 'Complete spectral plots', 0, 1, 'L', 1)

            # fileList = glob.glob(os.path.join(inPath, f'{filebasename}_*.png'))

            # if len(fileList) > 0:
            #     for i in range(0, len(fileList)):
            #         self.image(fileList[i], w = 175)
            # else:
            #     self.multi_cell(0, 5, "None found.")
        if level == "L1BQC":
            print('Adding spectral filter plots')
            inSpecFilterPath = os.path.join(inPlotPath, f'{level}_Spectral_Filter')
            fileList = glob.glob(os.path.join(inSpecFilterPath, f'*{filebasename}_*.png'))
            if len(fileList) > 0:
                self.cell(0, 6, 'Spectral Filters', 0, 1, 'L', 1)
                for i, file in enumerate(fileList):
                    self.image(file, w = 175)

        if level == "L2":            
            print('Adding radiometry plots')
            fileList = glob.glob(os.path.join(inPlotPath, level, f'*{filebasename}_*.png'))
            if len(fileList) > 0:
                self.cell(0, 6, 'Radiometry', 0, 1, 'L', 1)
                for i, file in enumerate(fileList):
                    if ConfigFile.settings["bL2Stations"]:
                        if "STATION" in file:
                            self.image(file, w = 175)
                    else:
                        if "STATION" not in file:
                            self.image(file, w = 175)

            print('Adding ocean color product plots')
            inProdPath = os.path.join(inPlotPath, f'{level}_Products')
            fileList = glob.glob(os.path.join(inProdPath, f'*{filebasename}_*.png'))
            if len(fileList) > 0:
                self.cell(0, 6, 'Derived Spectral Products', 0, 1, 'L', 1)
                for i,file in enumerate(fileList):
                    if ConfigFile.settings["bL2Stations"]:
                        if "STATION" in file:
                            self.image(file, w = 175)
                    else:
                        if "STATION" not in file:
                            self.image(file, w = 175)


    def print_chapter(self, level, title, inLog, inPlotPath, filebasename, root):
        self.add_page()
        self.chapter_title(level, title)

        seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
        seaBASSHeaderPath = os.path.join(PATH_TO_CONFIG, seaBASSHeaderFileName)
        if os.path.isfile(seaBASSHeaderPath):
            SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)

        headerBlock = SeaBASSHeader.settings

        self.chapter_body(inLog, headerBlock, level, inPlotPath, filebasename, root)






