
import os
import glob
from fpdf import FPDF
import random

from SeaBASSWriter import SeaBASSWriter
from SeaBASSHeader import SeaBASSHeader
from ConfigFile import ConfigFile


class PDF(FPDF):

    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Calculate width of title and position
        w = self.get_string_width(self.title) + 6
        self.set_x((210 - w) / 2)
        # Colors of frame, background and text
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 0)
        self.set_text_color(220, 50, 50)
        # Thickness of frame (1 mm)
        self.set_line_width(1)
        # Title
        self.cell(w, 9, self.title, 1, 1, 'C', 1)
        # Line break
        self.ln(10)

    def format_intro(self, level, headerBlock, commentsDict, root):        
        # Intros
        if level == "L1A":
            intro = 'Raw binary to HDF5 and filter data on SZA.'
            
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
                        not 'start' in key and not 'end' in key and not 'latitude' in key and \
                            not 'longitude' in key and not 'wind' in key and \
                                not 'cloud' in key and not 'wave' in key and not 'secchi' in key and \
                                    not 'water_depth' in key:
                        metaData += f'/{key}={value}\n'                            
        if level == "L1B":
            intro = 'Apply factory calibrations.'  
            metaData = ' \n'
            metaData += 'Processing Parameters: None\n'          
        if level == "L1C":
            intro = 'Filter data on pitch, roll, yaw, and azimuth angles.'
            
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
            else:
                
                metaData += f'Rotator Home Angle: {ConfigFile.settings["fL1cRotatorHomeAngle"]}\n'
                if ConfigFile.settings['bL1cSolarTracker']:
                    if ConfigFile.settings['bL1cRotatorDelay']:
                        metaData += f'Rotator Delay: {ConfigFile.settings["fL1cRotatorDelay"]}\n'
                    if ConfigFile.settings['bL1cCleanPitchRoll']:
                        metaData += f'Pitch/Roll Filter: {ConfigFile.settings["fL1cPitchRollPitch"]}\n'
                    if ConfigFile.settings['bL1cRotatorAngle']:
                        metaData += f'Rotator Min: {ConfigFile.settings["fL1cRotatorAngleMin"]}\n'
                        metaData += f'Rotator Max: {ConfigFile.settings["fL1cRotatorAngleMax"]}\n'
                if ConfigFile.settings['bL1cCleanSunAngle']:
                    metaData += f'Rel Azimuth Min: {ConfigFile.settings["fL1cSunAngleMin"]}\n'
                    metaData += f'Rel Azimuth Max: {ConfigFile.settings["fL1cSunAngleMax"]}\n'
        
        if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
            gpDict = {}
            for gp in root.groups: 
                gpDict[gp.id] = gp
            
        if level == "L1D":
            intro = 'Deglitch data and apply shutter dark corrections.'

            metaData = ' \n'
            metaData += 'Processing Parameters: \n'
            if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
                if root.attributes['L1D_DEGLITCH'] == 'ON':                
                    # These deglitching parameters might be in root.attributes if from files L1D or L1E, 
                    # or within their respective groups at L2
                    if 'ES_WINDOW_DARK' in root.attributes:
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
                        if ConfigFile.settings['bL1dThreshold']:
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

                        if ConfigFile.settings['bL1dThreshold']:
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

            else: # Root is none; this  is a failure report
                if ConfigFile.settings['bL1dDeglitch']:
                    metaData += f'ES Dark Window: {ConfigFile.settings["fL1dESWindowDark"]}\n'
                    metaData += f'ES Light Window: {ConfigFile.settings["fL1dESWindowLight"]}\n'
                    metaData += f'ES Dark Sigma: {ConfigFile.settings["fL1dESSigmaDark"]}\n'
                    metaData += f'ES Light Sigma: {ConfigFile.settings["fL1dESSigmaLight"]}\n'
                    metaData += f'LT Dark Window: {ConfigFile.settings["fL1dLTWindowDark"]}\n'                
                    metaData += f'LT Light Window: {ConfigFile.settings["fL1dLTWindowLight"]}\n'
                    metaData += f'LT Dark Sigma: {ConfigFile.settings["fL1dLTSigmaDark"]}\n'
                    metaData += f'LT Light Sigma: {ConfigFile.settings["fL1dLTSigmaLight"]}\n'
                    metaData += f'LI Dark Window: {ConfigFile.settings["fL1dLIWindowDark"]}\n'
                    metaData += f'LI Light Window: {ConfigFile.settings["fL1dLIWindowLight"]}\n'
                    metaData += f'LI Dark Sigma: {ConfigFile.settings["fL1dLISigmaDark"]}\n'
                    metaData += f'LI Light Sigma: {ConfigFile.settings["fL1dLISigmaLight"]}\n'

                    if ConfigFile.settings['bL1dThreshold']:
                        metaData += f'ES Light Thresh. Band: {ConfigFile.settings["fL1dESMinMaxBandLight"]}\n'
                        metaData += f'ES Dark Thresh. Band: {ConfigFile.settings["fL1dESMinMaxBandDark"]}\n'
                        metaData += f'ES Min.: {ConfigFile.settings["fL1dESMinLight"]}\n'
                        metaData += f'ES Max.: {ConfigFile.settings["fL1dESMaxLight"]}\n'
                        metaData += f'LI Dark Thresh. Band: {ConfigFile.settings["fL1dLIMinMaxBandDark"]}\n'
                        metaData += f'LI Min.: {ConfigFile.settings["fL1dLIMinLight"]}\n'
                        metaData += f'LI Max.: {ConfigFile.settings["fL1dLIMaxLight"]}\n'
                        metaData += f'LT Dark Thresh. Band: {ConfigFile.settings["fL1dLTMinMaxBandDark"]}\n'
                        metaData += f'LT Min.: {ConfigFile.settings["fL1dLTMinLight"]}\n'
                        metaData += f'LT Max.: {ConfigFile.settings["fL1dLTMaxLight"]}\n'

        if level == "L1E":
            intro = 'Interpolate data to common timestamps and wavebands.'

            metaData = 'Processing Parameters: \n'
            if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
                metaData += f'Wavelength Interp Int: {root.attributes["WAVE_INTERP"]}\n'
            else:
                metaData += f'Wavelength Interp Int: {ConfigFile.settings["fL1eInterpInterval"]}\n'
        if level == "L2":
            intro = 'Apply more quality control filters, temporal binning, '\
                'station selection, glint correction, NIR corrections, reflectance '\
                    'calculation and OC product calculation.'            

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
                metaData += f'Ensemble Duration: {root.attributes["ENSEMBLE_DURATION"]}\n'            
                if '%LT_FILTER' in gpDict['RADIANCE'].attributes:                
                    metaData += f'Percent Lt Filter: {gpDict["RADIANCE"].attributes["%LT_FILTER"]}\n'
                metaData += f'Glint_Correction: {gpDict["REFLECTANCE"].attributes["GLINT_CORR"]}\n'
                if 'NIR_RESID_CORR' in gpDict['REFLECTANCE'].attributes:
                    metaData += f'NIR Correction: {gpDict["REFLECTANCE"].attributes["NIR_RESID_CORR"]}\n'
                if 'NEGATIVE_VALUE_FILTER' in gpDict['REFLECTANCE'].attributes:
                    metaData += f'Remove Negatives: {gpDict["REFLECTANCE"].attributes["NEGATIVE_VALUE_FILTER"]}\n'
            else:
                metaData += f'Max Wind: {ConfigFile.settings["fL2MaxWind"]}\n'
                metaData += f'Min SZA: {ConfigFile.settings["fL2SZAMin"]}\n'
                metaData += f'Max SZA: {ConfigFile.settings["fL2SZAMin"]}\n'
                if ConfigFile.settings['bL2EnableSpecQualityCheck']:
                    metaData += f'Filter Sigma Es: {ConfigFile.settings["fL2SpecFilterEs"]}\n'
                    metaData += f'Filter Sigma Li: {ConfigFile.settings["fL2SpecFilterLi"]}\n'
                    metaData += f'Filter Sigma Lt: {ConfigFile.settings["fL2SpecFilterLt"]}\n'            
                if ConfigFile.settings['bL2EnableQualityFlags']:
                    metaData += f'Cloud Filter: {ConfigFile.settings["fL2CloudFlag"]}\n'
                    metaData += f'Es Filter: {ConfigFile.settings["fL2SignificantEsFlag"]}\n'
                    metaData += f'Dawn/Dusk Filter: {ConfigFile.settings["fL2DawnDuskFlag"]}\n'
                    metaData += f'Rain/Humidity Filter: {ConfigFile.settings["fL2RainfallHumidityFlag"]}\n'
                metaData += f'Ensemble Duration: {ConfigFile.settings["fL2TimeInterval"]}\n'            
                if ConfigFile.settings['bL2EnablePercentLt']:                
                    metaData += f'Percent Lt Filter: {ConfigFile.settings["fL2PercentLt"]}\n'
                if ConfigFile.settings['bL2RuddickRho']:
                    metaData += f'Glint_Correction: Ruddick et al. 2006'
                if ConfigFile.settings['bL2ZhangRho']:
                    metaData += f'Glint_Correction: Zhang et al. 2017'
                if ConfigFile.settings['bL2DefaultRho']:
                    metaData += f'Glint_Correction: Mobley 1999'
                if ConfigFile.settings['bL2PerformNIRCorrection']:
                    if ConfigFile.settings['bL2SimpleNIRCorrection']:
                        metaData += f'NIR Correction: Mueller and Austin 1995'
                    if ConfigFile.settings['bL2SimSpecNIRCorrection']:
                        metaData += f'NIR Correction: Ruddick et al. 2005/2006'
                else:
                    metaData += f'NIR Correction: None'
                if ConfigFile.settings['bL2NegativeSpec']:
                    metaData += f'Remove Negatives: ON'

        metaData += ' \n'
        return intro, metaData


    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Text color in gray
        self.set_text_color(128)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def chapter_title(self, num, label):
        # Arial 12
        self.set_font('Arial', '', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, '%s : %s' % (num, label), 0, 1, 'L', 1)
        # Line break
        self.ln(4)

    def chapter_body(self, inLog, headerBlock, level, inPlotPath, filebasename, root):
               
        self.set_font('Times', '', 12)

        ''' This is the old method of pulling parameters from the SeaBASS Header. 
            Shift to using root attributes from the file. Preserved here only to retain features not in
            ConfigFile settings'''
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
        self.multi_cell(0, 5, "Process log:")
        
        # Read text log file
        with open(inLog, 'rb') as fh:
            txt = fh.read().decode('latin-1')
        
        # Output justified text
        self.multi_cell(0, 5, txt)
        # Line break
        self.ln()

        # Figures
        if level == "L1D":            
            inPath = os.path.join(inPlotPath, 'L1C_Anoms')

            self.cell(0, 6, 'Example Deglitching', 0, 1, 'L', 1)
            self.multi_cell(0, 5, 'Randomized. Complete plots of hyperspectral '\
                'deglitching from anomaly analysis can be found in [output_directory]/Plots/L1C_Anoms.')

            if root.attributes['Fail'] == 0: # otherwise this is a report of failed process, so root is None.
                # These deglitching parameters might be in root.attributes if from files L1D or L1E, 
                # or within their respective groups at L2
                gpDict = {}
                for gp in root.groups: 
                    gpDict[gp.id] = gp
                if 'L1D_DEGLITCH' in root.attributes:
                    if 'ES_SIGMA_DARK' in root.attributes:
                        ESWindowDark = root.attributes['ES_WINDOW_DARK']
                        ESWindowLight = root.attributes['ES_WINDOW_LIGHT']
                        ESSigmaDark = root.attributes['ES_SIGMA_DARK']
                        ESSigmaLight = root.attributes['ES_SIGMA_DARK']
                        LIWindowDark = root.attributes['LI_WINDOW_DARK']
                        LIWindowLight = root.attributes['LI_WINDOW_LIGHT']
                        LISigmaDark = root.attributes['LI_SIGMA_DARK']
                        LISigmaLight = root.attributes['LI_SIGMA_DARK']
                        LTWindowDark = root.attributes['LT_WINDOW_DARK']
                        LTWindowLight = root.attributes['LT_WINDOW_LIGHT']
                        LTSigmaDark = root.attributes['LT_SIGMA_DARK']
                        LTSigmaLight = root.attributes['LT_SIGMA_DARK']
                    else:
                        ESWindowDark = gpDict["IRRADIANCE"].attributes['ES_WINDOW_DARK']
                        ESWindowLight = gpDict["IRRADIANCE"].attributes['ES_WINDOW_LIGHT']
                        ESSigmaDark = gpDict["IRRADIANCE"].attributes['ES_SIGMA_DARK']
                        ESSigmaLight = gpDict["IRRADIANCE"].attributes['ES_SIGMA_LIGHT']
                        LIWindowDark = gpDict["RADIANCE"].attributes['LI_WINDOW_DARK']
                        LIWindowLight = gpDict["RADIANCE"].attributes['LI_WINDOW_LIGHT']
                        LISigmaDark = gpDict["RADIANCE"].attributes['LI_SIGMA_DARK']
                        LISigmaLight = gpDict["RADIANCE"].attributes['LI_SIGMA_LIGHT']
                        LTWindowDark = gpDict["RADIANCE"].attributes['LT_WINDOW_DARK']
                        LTWindowLight = gpDict["RADIANCE"].attributes['LT_WINDOW_LIGHT']
                        LTSigmaDark = gpDict["RADIANCE"].attributes['LT_SIGMA_DARK']
                        LTSigmaLight = gpDict["RADIANCE"].attributes['LT_SIGMA_LIGHT']
            else:
                ESWindowDark = ConfigFile.settings['fL1dESWindowDark']
                ESWindowLight = ConfigFile.settings['fL1dESWindowLight']
                ESSigmaDark = ConfigFile.settings['fL1dESSigmaDark']
                ESSigmaLight = ConfigFile.settings['fL1dESSigmaLight']
                LIWindowDark = ConfigFile.settings['fL1dLIWindowDark']
                LIWindowLight = ConfigFile.settings['fL1dLIWindowLight']
                LISigmaDark = ConfigFile.settings['fL1dLISigmaDark']
                LISigmaLight = ConfigFile.settings['fL1dLISigmaLight']
                LTWindowDark = ConfigFile.settings['fL1dLTWindowDark']
                LTWindowLight = ConfigFile.settings['fL1dLTWindowLight']
                LTSigmaDark = ConfigFile.settings['fL1dLTSigmaDark']
                LTSigmaLight = ConfigFile.settings['fL1dLTSigmaLight']

            print('Adding deglitching plots...')
            # ES
            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1C_ESDark_*.png' ))  
                # f'{filebasename}_L1C_W{ESWindowDark}S{ESSigmaDark}_*ESDark_*.png' ))  
            if len(fileList) > 0:            
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.")

            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1C_ESLight_*.png' )) 
                # f'{filebasename}_L1C_W{ESWindowLight}S{ESSigmaLight}_*ESLight_*.png' )) 

            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.")

            # LI
            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1C_LIDark_*.png' ))
                # f'{filebasename}_L1C_W{LIWindowDark}S{LISigmaDark}_*LIDark_*.png' ))
            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.")

            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1C_LILight_*.png' ))
                # f'{filebasename}_L1C_W{LIWindowLight}S{LISigmaLight}_*LILight_*.png' ))
            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.")

            # LT
            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1C_LTDark_*.png' ))
                # f'{filebasename}_L1C_W{LTWindowDark}S{LTSigmaDark}_*LTDark_*.png' ))
            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.")
                
            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1C_LTLight_*.png' ))
                # f'{filebasename}_L1C_W{LTWindowLight}S{LTSigmaLight}_*LTLight_*.png' ))
            if len(fileList) > 0:
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)
            else:
                self.multi_cell(0, 5, "None found.")
                
        if level == "L1E":
            inPath = os.path.join(inPlotPath, f'{level}')
            self.cell(0, 6, 'Example Temporal Interpolations', 0, 1, 'L', 1)
            self.multi_cell(0, 5, 'Randomized. Complete plots of hyperspectral '\
                'interpolations can be found in [output_directory]/Plots/L1E.')

            fileList = glob.glob(os.path.join(inPath, f'{filebasename}_*.png'))            
            
            print('Adding interpolation plots...')
            if len(fileList) > 0:         
                
                # for i in range(0, len(fileList)):
                res = [i for i in fileList if 'L1E_LI' not in i and 'L1E_ES' not in i and 'L1E_LT' not in i]            
                for i in range (0, len(res)): #range(0, len(fileList)):
                    self.image(res[i], w = 175)
                res = [i for i in fileList if 'L1E_ES' in i]  
                if len(res) >= 3:          
                    for i in range (0, 3): #range(0, len(fileList)):
                        randIndx = random.randint(0, len(res))
                        self.image(res[i], w = 175)
                res = [i for i in fileList if 'L1E_LI' in i]            
                if len(res) >= 3:     
                    for i in range (0, 3): #range(0, len(fileList)):
                        randIndx = random.randint(0, len(res))
                        self.image(res[i], w = 175)
                res = [i for i in fileList if 'L1E_LT' in i]            
                if len(res) >= 3:     
                    for i in range (0, 3): #range(0, len(fileList)):
                        randIndx = random.randint(0, len(res))
                        self.image(res[i], w = 175)
            else:
                self.multi_cell(0, 5, "None found.")

            inPath = os.path.join(inPlotPath, 'L1D')
            self.cell(0, 6, 'Complete spectral plots', 0, 1, 'L', 1)            

            fileList = glob.glob(os.path.join(inPath, f'{filebasename}_*.png'))            
            
            if len(fileList) > 0:                                     
                for i in range(0, len(fileList)):
                    self.image(fileList[i], w = 175)
            else:
                self.multi_cell(0, 5, "None found.")

        if level == "L2":
            print('Adding spectral filter plots')
            inSpecFilterPath = os.path.join(inPlotPath, f'{level}_Spectral_Filter')
            fileList = glob.glob(os.path.join(inSpecFilterPath, f'*{filebasename}_*.png'))
            if len(fileList) > 0:         
                self.cell(0, 6, 'Spectral Filters', 0, 1, 'L', 1)
                for i in range(0, len(fileList)):
                    self.image(fileList[i], w = 175)

            print('Adding radiometry plots')
            fileList = glob.glob(os.path.join(inPlotPath, level, f'*{filebasename}_*.png'))
            if len(fileList) > 0:         
                self.cell(0, 6, 'Radiometry', 0, 1, 'L', 1)
                for i in range(0, len(fileList)):
                    self.image(fileList[i], w = 175)

            print('Adding ocean color product plots')
            inProdPath = os.path.join(inPlotPath, f'{level}_Products')
            fileList = glob.glob(os.path.join(inProdPath, f'*{filebasename}_*.png'))
            if len(fileList) > 0:         
                self.cell(0, 6, 'Derived Spectral Products', 0, 1, 'L', 1)
                for i in range(0, len(fileList)):
                    self.image(fileList[i], w = 175)

        # # Mention in italics
        # self.set_font('', 'I')
        # self.cell(0, 5, '(end of excerpt)')

    
    # def print_chapter(self, root, level, title, inLog, inPlotPath, filebasename, fp):
    def print_chapter(self, level, title, inLog, inPlotPath, filebasename, fp, root):
        self.add_page()
        self.chapter_title(level, title)        

        seaBASSHeaderFileName = ConfigFile.settings["seaBASSHeaderFileName"]
        seaBASSHeaderPath = os.path.join("Config", seaBASSHeaderFileName)        
        if os.path.isfile(seaBASSHeaderPath):
            SeaBASSHeader.loadSeaBASSHeader(seaBASSHeaderFileName)

        headerBlock = SeaBASSHeader.settings

        self.chapter_body(inLog, headerBlock, level, inPlotPath, filebasename, root)

    # # @staticmethod
    # def write_report(self, title):
    #     self.title = title
        




