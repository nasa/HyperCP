
import os
import sys
import glob
import datetime
import pytz
from PyQt5 import QtCore, QtWidgets
# from PyQt5.QtWidgets import QApplication, QWidget, QLabel
# from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtGui import QPixmap

from Utilities import Utilities


# class FieldPhotos(QWidget):
class FieldPhotos(QtWidgets.QDialog):

    def __init__(self, photoPath, photoDT, parent=None):
    
        super().__init__(parent)
        self.setModal(True)
        # self.title = 'Field Photos Widget'
        self.photoPath = photoPath
        self.photoDT = photoDT
        # self.left = 10
        # self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()

    def initUI(self):
        # self.setWindowTitle(self.title)
        self.setWindowTitle(f'{self.photoDT} {os.path.split(self.photoPath)[-1]}')
        # self.setGeometry(self.left, self.top, self.width, self.height)
        self.setGeometry(300, 300, 0, 0)
    
        # Create widget
        label = QtWidgets.QLabel(self)
        label2 = QtWidgets.QLabel('CLOSE PHOTO TO CONTINUE.',self)
        pixmap = QPixmap(self.photoPath)
        
        self.VBox = QtWidgets.QVBoxLayout()
        self.VBox.addWidget(label)
        self.VBox.addWidget(label2)
        pixmapScaled = pixmap.scaled(800,800,QtCore.Qt.KeepAspectRatio)
        label.setPixmap(pixmapScaled)
        self.resize(pixmapScaled.width(),pixmapScaled.height())      
                          

    @staticmethod
    def photoSetup(inPath, start, end, format='IMG_%Y%m%d_%H%M%S.jpg', tz='+0000'):
        ''' Use the start and end datetimes of the L1C file and the 
            names of the photo files to find a photo within a certain
            amount of time of the data file. tz is the timezone of the 
            photo name.
            '''   

        # Time difference limit between photo and data:
        tDiffLim = 90

        # Could either find the nearest, or find one in the data interval...
        midDatetime = start + (end-start)/2             

        extension = format.split('.')[1]
        fileList = glob.glob(os.path.join(inPath,'Photos',f'*.{extension}')) 
        if len(fileList) > 0:            
            
            # dFormat = 'IMG_%Y%m%d_%H%M%S.jpg'
            dFormat = f"{format.split('.')[0]}%z" # tack on the time zone below
            picDateTime = []
            for fp in fileList:
                fileName = os.path.split(fp)[-1]
                fileName = fileName.split('.')[0]+tz
                dT = datetime.datetime.strptime(fileName, dFormat)
                picDateTime.append(dT.astimezone(pytz.utc))

            indx = Utilities.find_nearest(picDateTime,midDatetime)

            tDiff = abs(picDateTime[indx]-midDatetime).seconds / 60 # in minutes

            if tDiff < tDiffLim:
                return fileList[indx], picDateTime[indx]
            else:
                return None, None
            
        else:
            print("None found")
            return None


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = FieldPhotos(photoPath=None)
#     sys.exit(app.exec_())