import os
from PDFreport import PDF

fileName = '1614106'
pathOut = os.path.join('D:\\','Dirk','NASA','HyperPACE','Field_Data','HyperSAS','Processed','KORUS')

dirPath = os.getcwd()
inLogPath = os.path.join(dirPath, 'Logs')
inPlotPath = os.path.join(pathOut,'Plots')
outPDF = os.path.join(pathOut,'Reports', f'{fileName}.pdf')
# title = f'File: {fileName} Collected: {root.attributes["TIME-STAMP"]}'
title = f'File: {fileName} Collected: timestamp'

pdf = PDF()
pdf.set_title(title)
# pdf.set_author(f'HyperInSPACE_{MainConfig.settings["version"]}')
pdf.set_author(f'HyperInSPACE_version')

inLog = os.path.join(inLogPath,f'{fileName}_L1A.log')
if os.path.isfile(inLog):
    pdf.print_chapter('L1A', 'Process RAW to L1A', inLog, inPlotPath, fileName)
inLog = os.path.join(inLogPath,f'{fileName}_L1A_L1B.log')
if os.path.isfile(inLog):
    pdf.print_chapter('L1B', 'Process L1A to L1B', inLog, inPlotPath, fileName)
inLog = os.path.join(inLogPath,f'{fileName}_L1B_L1C.log')
if os.path.isfile(inLog):
    pdf.print_chapter('L1C', 'Process L1B to L1C', inLog, inPlotPath, fileName)
inLog = os.path.join(inLogPath,f'{fileName}_L1C_L1D.log')
if os.path.isfile(inLog):
    pdf.print_chapter('L1D', 'Process L1C to L1D', inLog, inPlotPath, fileName)
inLog = os.path.join(inLogPath,f'{fileName}_L1D_L1E.log')
if os.path.isfile(inLog):
    pdf.print_chapter('L1E', 'Process L1D to L1E', inLog, inPlotPath, fileName)
inLog = os.path.join(inLogPath,f'{fileName}_L1E_L2.log')
if os.path.isfile(inLog):
    pdf.print_chapter('L2', 'Process L1E to L2', inLog, inPlotPath, fileName)

pdf.output(outPDF, 'F')

print('done')