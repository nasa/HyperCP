from PyQt5 import QtCore, QtGui, QtWidgets
from Window1 import Values

class Window2(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)        
        self.initUI()

    def initUI(self):

        self.setOneLineEdit = QtWidgets.QLineEdit(self)
        self.setOneLineEdit.setText(str(Values.settings["One"]))

        Values.settings["One"] = 2