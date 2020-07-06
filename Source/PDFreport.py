
import os
import glob
from fpdf import FPDF
import random

from SeaBASSWriter import SeaBASSWriter
from SeaBASSHeader import SeaBASSHeader


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

    def format_intro(self, level, headerBlock, commentsDict):        
        # Intros
        if level == "L1A":
            intro = 'Raw binary to HDF5 and filter data on SZA.'
            
            metaData = ' \n'
            metaData += 'Processing Parameters and metadata: \n'
            metaData += f'HyperInSPACE version: {commentsDict[" HyperInSPACE vers"]}'
            metaData += f'SZA Filter (L1A): {commentsDict[" SZA Filter"]}'
            metaData += f'SZA Limit (L1A): {commentsDict[" SZA Max"]}'
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
            metaData += f'Rotator Home Angle: {commentsDict[" Rotator Home Angle"]}'
            metaData += f'Rotator Delay: {commentsDict[" Rotator Delay"]}'
            metaData += f'Max Pitch: {commentsDict[" Max Pitch"]}'
            metaData += f'Max Roll: {commentsDict[" Max Roll"]}'
            metaData += f'Max Pitch: {commentsDict[" Max Pitch"]}'
            metaData += f'Rotator Min/Max Filter: {commentsDict[" Rotator Min/Max Filter"]}'
            metaData += f'Rotator Min: {commentsDict[" Rotator Min"]}'
            metaData += f'Rotator Max: {commentsDict[" Rotator Max"]}'
            metaData += f'Rel Azimuth Filter: {commentsDict[" Rel Azimuth Filter"]}'
            metaData += f'Rel Azimuth Min: {commentsDict[" Rel Azimuth Min"]}'
            metaData += f'Rel Azimuth Max: {commentsDict[" Rel Azimuth Max"]}'
            metaData += f'Pitch/Roll Filter: {commentsDict[" Pitch/Roll Filter"]}'
        if level == "L1D":
            intro = 'Deglitch data and apply shutter dark corrections.'

            metaData = ' \n'
            metaData += 'Processing Parameters: \n'
            metaData += f'Deglitch Filter: {commentsDict[" Deglitch Filter"]}'
            metaData += f'Dark Window: {commentsDict[" Dark Window"]}'
            metaData += f'Light Window: {commentsDict[" Light Window"]}'
            metaData += f'Dark Sigma: {commentsDict[" Dark Sigma"]}'
            metaData += f'Light Sigma: {commentsDict[" Light Sigma"]}'
        if level == "L1E":
            intro = 'Interpolate data to common timestamps and wavebands.'

            metaData = 'Processing Parameters: \n'
            metaData += f'Wavelength Interp Int: {commentsDict[" Wavelength Interp Int"]}'
        if level == "L2":
            intro = 'Apply more quality control filters, temporal binning, '\
                'station selection, glint correction, NIR corrections, reflectance '\
                    'calculation and OC product calculation.'

            metaData = ' \n'
            metaData += 'Processing Parameters: \n'
            metaData += f'Max Wind: {commentsDict[" Max Wind"]}'
            metaData += f'Min SZA: {commentsDict[" Min SZA"]}'
            metaData += f'Max SZA: {commentsDict[" Max SZA"]}'
            metaData += f'Spectral Filter: {commentsDict[" Spectral Filter"]}'
            metaData += f'Filter Sigma Es: {commentsDict[" Filter Sigma Es"]}'
            metaData += f'Filter Sigma Li: {commentsDict[" Filter Sigma Li"]}'
            metaData += f'Filter Sigma Lt: {commentsDict[" Filter Sigma Lt"]}'
            metaData += f'Meteorological Filter: {commentsDict[" Meteorological Filter"]}'
            metaData += f'Cloud Flag: {commentsDict[" Cloud Flag"]}'
            metaData += f'Es Flag: {commentsDict[" Es Flag"]}'
            metaData += f'Dawn/Dusk Flag: {commentsDict[" Dawn/Dusk Flag"]}'
            metaData += f'Rain/Humidity Flag: {commentsDict[" Rain/Humidity Flag"]}'
            metaData += f'Ensemble Interval: {commentsDict[" Ensemble Interval"]}'
            metaData += f'Percent Lt Filter: {commentsDict[" Percent Lt Filter"]}'
            metaData += f'Percent Light: {commentsDict[" Percent Light"]}'
            metaData += f'Glint_Correction: {commentsDict[" Glint_Correction"]}'
            metaData += f'NIR Correction: {commentsDict[" NIR Correction"]}'
            metaData += f'Remove Negatives: {commentsDict[" Remove Negatives"]}'

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

    def chapter_body(self, inLog, headerBlock, level, inPlotPath, filebasename):
        
        # Times 12
        self.set_font('Times', '', 12)

        comments1 = headerBlock['comments'].split('!')
        commentsDict = {}
        for comment in comments1:
            key, value = comment.split(' = ') if ' = ' in comment \
                else ('','')
            commentsDict[key] = value

        intro, metaData = self.format_intro(level, headerBlock, commentsDict)        

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
            fileList = glob.glob(os.path.join(inPath, f'{filebasename}_*.png'))            
            self.cell(0, 6, 'Example Deglitching', 0, 1, 'L', 1)
            self.multi_cell(0, 5, 'Randomized. Complete plots of hyperspectral '\
                'deglitching from anomaly analysis can be found in [output_directory]/Plots/L1C_Anoms.')
            for i in range (0, 5): #range(0, len(fileList)):
                randIndx = random.randint(0, len(fileList))
                # self.image(fileList[i], w = 175)
                self.image(fileList[randIndx], w = 175)
                
        if level == "L1E":
            inPath = os.path.join(inPlotPath, f'{level}')
            fileList = glob.glob(os.path.join(inPath, f'{filebasename}_*.png'))            
            self.cell(0, 6, 'Example Temporal Interpolations', 0, 1, 'L', 1)
            self.multi_cell(0, 5, 'Randomized. Complete plots of hyperspectral '\
                'interpolations can be found in [output_directory]/Plots/L1E.')
            # for i in range(0, len(fileList)):
            res = [i for i in fileList if 'L1E_LI' not in i and 'L1E_ES' not in i]            
            for i in range (0, len(res)): #range(0, len(fileList)):
                self.image(res[i], w = 175)
            res = [i for i in fileList if 'L1E_ES' in i]            
            for i in range (0, 3): #range(0, len(fileList)):
                randIndx = random.randint(0, len(res))
                self.image(res[i], w = 175)
            res = [i for i in fileList if 'L1E_LI' in i]            
            for i in range (0, 3): #range(0, len(fileList)):
                randIndx = random.randint(0, len(res))
                self.image(res[i], w = 175)

        if level == "L2":
            inSpecFilterPath = os.path.join(inPlotPath, f'{level}_Spectral_Filter')
            fileList = glob.glob(os.path.join(inSpecFilterPath, f'{filebasename}_*.png'))
            self.cell(0, 6, 'Spectral Filters', 0, 1, 'L', 1)
            for i in range(0, len(fileList)):
                self.image(fileList[i], w = 175)

            fileList = glob.glob(os.path.join(inPlotPath, level, f'{filebasename}_*.png'))
            self.cell(0, 6, 'Radiometry', 0, 1, 'L', 1)
            for i in range(0, len(fileList)):
                self.image(fileList[i], w = 175)

            inProdPath = os.path.join(inPlotPath, f'{level}_Products')
            fileList = glob.glob(os.path.join(inProdPath, f'{filebasename}_*.png'))
            self.cell(0, 6, 'Derived Spectral Products', 0, 1, 'L', 1)
            for i in range(0, len(fileList)):
                self.image(fileList[i], w = 175)

        # # Mention in italics
        # self.set_font('', 'I')
        # self.cell(0, 5, '(end of excerpt)')

    
    def print_chapter(self, root, level, title, inLog, inPlotPath, filebasename, fp):
        self.add_page()
        self.chapter_title(level, title)        

        headerBlock = SeaBASSHeader.settings

        self.chapter_body(inLog, headerBlock, level, inPlotPath, filebasename)

    # # @staticmethod
    # def write_report(self, title):
    #     self.title = title
        




