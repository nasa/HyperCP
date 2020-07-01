
import os
import glob
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Calculate width of title and position
        w = self.get_string_width(title) + 6
        self.set_x((210 - w) / 2)
        # Colors of frame, background and text
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 0)
        self.set_text_color(220, 50, 50)
        # Thickness of frame (1 mm)
        self.set_line_width(1)
        # Title
        self.cell(w, 9, title, 1, 1, 'C', 1)
        # Line break
        self.ln(10)

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

    def chapter_body(self, inLog, level, inPlotPath, filebasename):
        # Read text file
        with open(inLog, 'rb') as fh:
            txt = fh.read().decode('latin-1')
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        self.multi_cell(0, 5, txt)
        # Line break
        self.ln()

        # Figures
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

        # # Mention in italics
        # self.set_font('', 'I')
        # self.cell(0, 5, '(end of excerpt)')

    def print_chapter(self, level, title, inLog, inPlotPath, filebasename):
        self.add_page()
        self.chapter_title(level, title)        
        self.chapter_body(inLog, level, inPlotPath, filebasename)


filebasename = '1614106'
title = f'{filebasename} lat lon date time'

dirPath = os.getcwd()
inLogPath = os.path.join(dirPath, 'Logs')
inPlotPath = os.path.join('D:/','Dirk','NASA','HyperPACE','Field_Data','HyperSAS','Processed','KORUS','Plots')
outPath = dirPath
outPDF = os.path.join(outPath, 'AAA.pdf')

pdf = PDF()
pdf.set_title(title)
pdf.set_author('Jules Verne')
inLog = os.path.join(inLogPath,f'{filebasename}_L1D_L1E.log')
pdf.print_chapter('L1E', 'Process L1D to L1E', inLog, inPlotPath, filebasename)
inLog = os.path.join(inLogPath,f'{filebasename}_L1E_L2.log')
pdf.print_chapter('L2', 'Process L1E to L2', inLog, inPlotPath, filebasename)
pdf.output(outPDF, 'F')