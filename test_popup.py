import sys 
from PyQt5 import QtWidgets, QtCore

class MyWidget(QtWidgets.QWidget): 
    def __init__(self): 
        # QtWidgets.QWidget.__init__(self) 
        # self.setGeometry(400,50,200,200)

        # self.pushButton = QtWidgets.QPushButton('show messagebox', self)
        # self.pushButton.setGeometry(25, 90, 150, 25)
        # self.pushButton.clicked.connect(self.onClick)

    # def onClick(self):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setText('to select click "show details"')
        msgbox.setTextInteractionFlags(QtCore.Qt.TextEditable) # (QtCore.Qt.NoTextInteraction)
        msgbox.setDetailedText('line 1\nline 2')
        msgbox.exec()

app = QtWidgets.QApplication(sys.argv)
w = MyWidget()
# w.show()
# sys.exit(app.exec_())