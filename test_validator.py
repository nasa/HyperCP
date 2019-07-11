from PyQt5.QtWidgets import *
from PyQt5 import QtGui, QtCore

app = QApplication([])
window = QWidget()
layout = QVBoxLayout()
button = QPushButton('Test')
inputTextBox = QLabel('Input odd number')
inputLineEdit = QLineEdit()
intValidator = QtGui.QIntValidator()

layout.addWidget(inputTextBox)
layout.addWidget(inputLineEdit)
inputLineEdit.setValidator(intValidator)
layout.addWidget(button)
window.setLayout(layout)

def on_button_clicked():
    inputValue = int(inputLineEdit.text())
    print('You input: '+str(inputValue))    
    re = QtCore.QRegExp("inputValue%2 == 1")
    valResult = re.isValid()
    alert = QMessageBox()
    alert.setText(str(valResult))
    alert.exec_()

button.clicked.connect(on_button_clicked)
window.show()
app.exec_()




