
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
            
            metaData = ' \n'
            metaData += 'Processing Parameters and metadata: \n'
            # metaData += f'HyperInSPACE version: {commentsDict[" HyperInSPACE vers"]}'
            metaData += f'HyperInSPACE version: {root.attributes["HYPERINSPACE"]}'
            # metaData += f'SZA Filter (L1A): {commentsDict[" SZA Filter"]}'
            if 'SZA_FILTER_L1A' in root.attributes:
                metaData += f'SZA Filter (L1A): {root.attributes["SZA_FILTER_L1A"]}'
            # metaData += f'SZA Limit (L1A): {commentsDict[" SZA Max"]}'
            comments2 = headerBlock['other_comments'].split('!')
            for comment in comments2:
                if comment != '':
                    metaData += comment
            for key,value in headerBlock.items():
                if key != 'comments' and key != 'other_comments' and \
                    key != 'data_file_name' and key != 'missing' and \
                        key != 'delimiter':
                    # Python 3 f-string
                    metaData += f'/{key}={value}\n'
                            
        if level == "L1B":
            intro = 'Apply factory calibrations.'  
            metaData = ' \n'
            metaData += 'Processing Parameters: None\n'          
        if level == "L1C":
            intro = 'Filter data on pitch, roll, yaw, and azimuth angles.'
            
            metaData = ' \n'
            metaData += 'Processing Parameters: \n'
            if 'HOME_ANGLE' in root.attributes:
              metaData += f'Rotator Home Angle: {root.attributes["HOME_ANGLE"]}'  
            if 'ROTATOR_DELAY_FILTER' in root.attributes:
              metaData += f'Rotator Delay: {root.attributes["ROTATOR_DELAY_FILTER"]}'  
            # metaData += f'Rotator Home Angle: {commentsDict[" Rotator Home Angle"]}'
            # metaData += f'Rotator Delay: {commentsDict[" Rotator Delay"]}'
            if 'PITCH_ROLL_FILTER' in root.attributes:
                metaData += f'Pitch/Roll Filter: {root.attributes["PITCH_ROLL_FILTER"]}'
            # metaData += f'Pitch/Roll Filter: {commentsDict[" Pitch/Roll Filter"]}'
            # metaData += f'Max Pitch/Roll: {commentsDict[" Max Pitch/Roll"]}'
            # metaData += f'Max Roll: {commentsDict[" Max Roll"]}'
            # metaData += f'Max Pitch: {commentsDict[" Max Pitch"]}'
            if 'ROTATOR_ANGLE_MIN' in root.attributes:
                metaData += f'Rotator Min Filter: {root.attributes["ROTATOR_ANGLE_MIN"]}'
                metaData += f'Rotator Max Filter: {root.attributes["ROTATOR_ANGLE_MAX"]}'
            # metaData += f'Rotator Min/Max Filter: {commentsDict[" Rotator Min/Max Filter"]}'
            # metaData += f'Rotator Min: {commentsDict[" Rotator Min"]}'
            # metaData += f'Rotator Max: {commentsDict[" Rotator Max"]}'
            # metaData += f'Rel Azimuth Filter: {commentsDict[" Rel Azimuth Filter"]}'
            if 'RELATIVE_AZIMUTH_MIN' in root.attributes:
                metaData += f'Rel Azimuth Min: {root.attributes["RELATIVE_AZIMUTH_MIN"]}'    
                metaData += f'Rel Azimuth Max: {root.attributes["RELATIVE_AZIMUTH_MAX"]}'    
            # metaData += f'Rel Azimuth Min: {commentsDict[" Rel Azimuth Min"]}'
            # metaData += f'Rel Azimuth Max: {commentsDict[" Rel Azimuth Max"]}'
        
        gpDict = {}
        for gp in root.groups: 
            gpDict[gp.id] = gp
            
        if level == "L1D":
            intro = 'Deglitch data and apply shutter dark corrections.'

            metaData = ' \n'
            metaData += 'Processing Parameters: \n'
            if root.attributes['L1D_DEGLITCH'] == 'ON':
                # These deglitching parameters might be in root.attributes if from files L1D or L1E, 
                # or within their respective groups at L2
                if 'ES_WINDOW_DARK' in root.attributes:
                    metaData += f'ES Dark Window: {root.attributes["ES_WINDOW_DARK"]}'
                    metaData += f'ES Light Window: {root.attributes["ES_WINDOW_LIGHT"]}'
                    metaData += f'ES Dark Sigma: {root.attributes["ES_SIGMA_DARK"]}'
                    metaData += f'ES Light Sigma: {root.attributes["ES_SIGMA_LIGHT"]}'
                    metaData += f'LT Dark Window: {root.attributes["LT_WINDOW_DARK"]}'
                    metaData += f'LT Light Window: {root.attributes["LT_WINDOW_LIGHT"]}'
                    metaData += f'LT Dark Sigma: {root.attributes["LT_SIGMA_DARK"]}'
                    metaData += f'LT Light Sigma: {root.attributes["LT_SIGMA_LIGHT"]}'
                    metaData += f'LI Dark Window: {root.attributes["LI_WINDOW_DARK"]}'
                    metaData += f'LI Light Window: {root.attributes["LI_WINDOW_LIGHT"]}'
                    metaData += f'LI Dark Sigma: {root.attributes["LI_SIGMA_DARK"]}'
                    metaData += f'LI Light Sigma: {root.attributes["LI_SIGMA_LIGHT"]}'
                else:
                    metaData += f'ES Dark Window: {gpDict["IRRADIANCE"].attributes["ES_WINDOW_DARK"]}'
                    metaData += f'ES Light Window: {gpDict["IRRADIANCE"].attributes["ES_WINDOW_LIGHT"]}'
                    metaData += f'ES Dark Sigma: {gpDict["IRRADIANCE"].attributes["ES_SIGMA_DARK"]}'
                    metaData += f'ES Light Sigma: {gpDict["IRRADIANCE"].attributes["ES_SIGMA_LIGHT"]}'
                    metaData += f'LT Dark Window: {gpDict["RADIANCE"].attributes["LT_WINDOW_DARK"]}'
                    metaData += f'LT Light Window: {gpDict["RADIANCE"].attributes["LT_WINDOW_LIGHT"]}'
                    metaData += f'LT Dark Sigma: {gpDict["RADIANCE"].attributes["LT_SIGMA_DARK"]}'
                    metaData += f'LT Light Sigma: {gpDict["RADIANCE"].attributes["LT_SIGMA_LIGHT"]}'
                    metaData += f'LI Dark Window: {gpDict["RADIANCE"].attributes["LI_WINDOW_DARK"]}'
                    metaData += f'LI Light Window: {gpDict["RADIANCE"].attributes["LI_WINDOW_LIGHT"]}'
                    metaData += f'LI Dark Sigma: {gpDict["RADIANCE"].attributes["LI_SIGMA_DARK"]}'
                    metaData += f'LI Light Sigma: {gpDict["RADIANCE"].attributes["LI_SIGMA_LIGHT"]}'

        if level == "L1E":
            intro = 'Interpolate data to common timestamps and wavebands.'

            metaData = 'Processing Parameters: \n'
            metaData += f'Wavelength Interp Int: {root.attributes["WAVE_INTERP"]}'
        if level == "L2":
            intro = 'Apply more quality control filters, temporal binning, '\
                'station selection, glint correction, NIR corrections, reflectance '\
                    'calculation and OC product calculation.'            

            metaData = ' \n'
            metaData += 'Processing Parameters: \n'
            # if 'WIND_MAX' in root.attributes:
            metaData += f'Max Wind: {root.attributes["WIND_MAX"]}'
            metaData += f'Min SZA: {root.attributes["SZA_MIN"]}'
            metaData += f'Max SZA: {root.attributes["SZA_MAX"]}'
            # metaData += f'Spectral Filter: {root.attributes[" Spectral Filter"]}'
            if 'ES_SPEC_FILTER' in gpDict['IRRADIANCE'].attributes:
                metaData += f'Filter Sigma Es: {gpDict["IRRADIANCE"].attributes["ES_SPEC_FILTER"]}'
                metaData += f'Filter Sigma Li: {gpDict["RADIANCE"].attributes["LI_SPEC_FILTER"]}'
                metaData += f'Filter Sigma Lt: {gpDict["RADIANCE"].attributes["LT_SPEC_FILTER"]}'
            # metaData += f'Meteorological Filter: {root.attributes[" Meteorological Filter"]}'
            if 'CLOUD_FILTER' in root.attributes:
                metaData += f'Cloud Filter: {root.attributes["CLOUD_FILTER"]}'
                metaData += f'Es Filter: {root.attributes["ES_FILTER"]}'
                metaData += f'Dawn/Dusk Filter: {root.attributes["DAWN_DUSK_FILTER"]}'
                metaData += f'Rain/Humidity Filter: {root.attributes["RAIN_RH_FILTER"]}'
            metaData += f'Ensemble Duration: {root.attributes["ENSEMBLE_DURATION"]}'            
            if '%LT_FILTER' in gpDict['RADIANCE'].attributes:                
                metaData += f'Percent Lt Filter: {gpDict["RADIANCE"].attributes["%LT_FILTER"]}'
            # metaData += f'Percent Light: {root.attributes[" Percent Light"]}'
            metaData += f'Glint_Correction: {gpDict["REFLECTANCE"].attributes["GLINT_CORR"]}'
            if 'NIR_RESID_CORR' in gpDict['REFLECTANCE'].attributes:
                metaData += f'NIR Correction: {gpDict["REFLECTANCE"].attributes["NIR_RESID_CORR"]}'
            if 'NEGATIVE_VALUE_FILTER' in gpDict['REFLECTANCE'].attributes:
                metaData += f'Remove Negatives: {gpDict["REFLECTANCE"].attributes["NEGATIVE_VALUE_FILTER"]}'

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
        
        # Times 12
        self.set_font('Times', '', 12)

        ''' This is the old method of pulling parameters from the SeaBASS Header. 
            Shift to using root attributes from the file.'''
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

            print('Adding deglitching plots...')
            # ES
            fileList = glob.glob(os.path.join(inPath, \
                f'{filebasename}_L1C_W{ESWindowDark}S{ESSigmaDark}_*ESDark_*.png' ))  

            if len(fileList) > 0:
                
                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)

                fileList = glob.glob(os.path.join(inPath, \
                    f'{filebasename}_L1C_W{ESWindowLight}S{ESSigmaLight}_*ESLight_*.png' )) 

                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)

                # LI
                fileList = glob.glob(os.path.join(inPath, \
                    f'{filebasename}_L1C_W{LIWindowDark}S{LISigmaDark}_*LIDark_*.png' ))

                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)

                fileList = glob.glob(os.path.join(inPath, \
                    f'{filebasename}_L1C_W{LIWindowLight}S{LISigmaLight}_*LILight_*.png' ))

                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)

                # LT
                fileList = glob.glob(os.path.join(inPath, \
                    f'{filebasename}_L1C_W{LTWindowDark}S{LTSigmaDark}_*LTDark_*.png' ))

                for i in range (0, 1): #range(0, len(fileList)):
                    randIndx = random.randint(0, len(fileList)-1)
                    # self.image(fileList[i], w = 175)
                    self.image(fileList[randIndx], w = 175)

                fileList = glob.glob(os.path.join(inPath, \
                    f'{filebasename}_L1C_W{LTWindowLight}S{LTSigmaLight}_*LTLight_*.png' ))

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

        headerBlock = SeaBASSHeader.settings

        self.chapter_body(inLog, headerBlock, level, inPlotPath, filebasename, root)

    # # @staticmethod
    # def write_report(self, title):
    #     self.title = title
        




