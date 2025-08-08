'''################################# LOG AND ERROR ORIENTED #################################'''
import os
import logging

from PyQt5.QtWidgets import QMessageBox

# This gets reset later in Controller.processSingleLevel to reflect the file being processed.
if "LOGFILE" not in os.environ:
    os.environ["LOGFILE"] = "temp.log"

def errorWindow(winText,errorText):
    if os.environ["HYPERINSPACE_CMD"].lower() == 'true':
        return
    msgBox = QMessageBox()
    # msgBox.setIcon(QMessageBox.Information)
    msgBox.setIcon(QMessageBox.Critical)
    msgBox.setText(errorText)
    msgBox.setWindowTitle(winText)
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.exec_()

def writeLogFileAndPrint(logText, andPrint=True, mode='a'):
    writeLogFile(logText, mode)
    if andPrint:
        print(logText)

def writeLogFile(logText, mode='a'):
    ''' These logs will be written in the HyperCP directory structure '''
    if not os.path.exists('Logs'):
        logging.getLogger().warning('Made directory: Logs/')
        os.mkdir('Logs')
    with open('Logs/' + os.environ["LOGFILE"], mode, encoding="utf-8") as logFile:
        logFile.write(logText + "\n")
