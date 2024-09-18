
import os
import glob
import datetime
import pytz
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QPixmap


class FieldPhotos(QtWidgets.QDialog):

    def __init__(self, photoPath, photoDT, parent=None):
        # Paths and DTs are lists of photos/datetimes within the time limit
        super().__init__(parent)
        self.setModal(True)
        self.photoPath = photoPath
        self.photoDT = photoDT
        self.left = 300
        self.top = 300
        self.width = 800
        self.height = 820
        self.imageSelect = 0

        self.initUI()

    def initUI(self):
        self.setWindowTitle(f'{self.photoDT[0]} {os.path.split(self.photoPath[self.imageSelect])[-1]}')
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Create widgets ############################
        self.fieldPhoto = QtWidgets.QLabel(self)
        # Set initial photo
        self.pixmap = QPixmap(self.photoPath[self.imageSelect])
        self.pixmapScaled = self.pixmap.scaled(800,800,QtCore.Qt.KeepAspectRatio)
        self.fieldPhoto.setPixmap(self.pixmapScaled)
        # self.fieldPhoto.move(0,50)  # Since Layouts won't work in VBox, move down to make space

        labelNote = QtWidgets.QLabel('Close this window to continue.', self)
        listLabel = QtWidgets.QLabel(\
            f'Number of images found within 90 mins of data: {len(self.photoPath)} ', self)

        self.nextButton = QtWidgets.QPushButton('>')
        self.nextButton.setToolTip('Next image in list')

        self.previousButton = QtWidgets.QPushButton('<')
        self.previousButton.setToolTip('Previous image in list')
        self.nextButton.clicked.connect(lambda: self.updateImagePressed('next'))
        self.previousButton.clicked.connect(lambda: self.updateImagePressed('previous'))

        # Setup Layout ##################################
        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(self.fieldPhoto)

        HBox = QtWidgets.QHBoxLayout()
        HBox.addWidget(listLabel)
        HBox.addWidget(self.previousButton)
        HBox.addWidget(self.nextButton)
        HBox.addWidget(labelNote)
        VBox.addLayout(HBox)

        self.updateImagePressed('first')

        self.setLayout(VBox)

    def updateImagePressed(self, direction):
        print(f'Display {direction} image: {self.photoPath[self.imageSelect]}')

        if direction == 'next':
            self.imageSelect += 1
        if direction == 'previous':
            self.imageSelect -= 1

        if self.imageSelect == 0:
            self.previousButton.setDisabled(True)
        else:
            self.previousButton.setDisabled(False)

        if self.imageSelect == len(self.photoPath)-1:
            self.nextButton.setDisabled(True)
        else:
            self.nextButton.setDisabled(False)

        # Set photo
        self.pixmap = QPixmap(self.photoPath[self.imageSelect])
        self.pixmapScaled = self.pixmap.scaled(800,800,QtCore.Qt.KeepAspectRatio)
        self.fieldPhoto.setPixmap(self.pixmapScaled)
        # # self.fieldPhoto.move(0,100)

        self.setWindowTitle(f'{self.photoDT[self.imageSelect]} {os.path.split(self.photoPath[self.imageSelect])[-1]}')

    @staticmethod
    def photoSetup(inPath, start, end, format='IMG_%Y%m%d_%H%M%S.jpg', tz='+0000'):
        ''' Use the start and end datetimes of the L1C file and the
            names of the photo files to find a photo within a certain
            amount of time of the data file. tz is the timezone of the
            photo name.
            '''

        # Time difference limit between photo and data:
        tDiffLim = datetime.timedelta(minutes = 90)

        # Could either find the nearest, or find one in the data interval...
        midDatetime = start + (end-start)/2

        extension = format.split('.')[1]
        fileList = glob.glob(os.path.join(inPath,f'*.{extension}'))
        if len(fileList) > 0:

            # dFormat = 'IMG_%Y%m%d_%H%M%S.jpg'
            dFormat = f"{format.split('.')[0]}%z" # tack on the time zone below
            dFormatAlt = f"{format.split('.')[0]}%f%z" # for case with microseconds
            # picDateTime = []
            picList = []
            picDTList = []
            for fp in fileList:
                fileName = os.path.split(fp)[-1]
                fileName = fileName.split('.')[0]+tz
                try:
                    dT = datetime.datetime.strptime(fileName, dFormat)
                    # picDateTime.append(dT.astimezone(pytz.utc))
                    picDateTime = dT.astimezone(pytz.utc)
                    # tDiff = abs(picDateTime-midDatetime).seconds / 60
                    tDiff = abs(picDateTime-midDatetime)
                    if tDiff < tDiffLim:
                        picList.append(fp)
                        picDTList.append(picDateTime)
                except Exception:
                    try:
                        dT = datetime.datetime.strptime(fileName, dFormatAlt)
                        # picDateTime.append(dT.astimezone(pytz.utc))
                        picDateTime = dT.astimezone(pytz.utc)
                        # tDiff = abs(picDateTime-midDatetime).seconds / 60
                        tDiff = abs(picDateTime-midDatetime)
                        if tDiff < tDiffLim:
                            picList.append(fp)
                            picDTList.append(picDateTime)
                    except Exception:
                        print(f'This file does not match the format. Rename or update format in AnomAnal GUI. {fileName}')


            if len(picList) > 0:
                return picList, picDTList
            else:
                return None, None

        else:
            print("None found")
            return None, None