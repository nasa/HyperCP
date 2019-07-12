from PyQt5.QtWidgets import * # Yes, this is lazy...
from PyQt5 import QtGui

app = QApplication([])
window = QWidget()
layout = QVBoxLayout()
inputTextBox = QLabel('Input odd number')
inputLineEdit = QLineEdit()
inputTextBox2 = QLabel('Then enter something here...')
inputLineEdit2 = QLineEdit()
intValidator = QtGui.QIntValidator()
oddValidator = QtGui.QOddNumberTest('inputValue%2 == 1')

if oddValidator is False:
    alert = QMessageBox()
    alert.setText('I said an ODD number, you dope!')
    alert.exec_()

layout.addWidget(inputTextBox)
layout.addWidget(inputLineEdit)
layout.addWidget(inputTextBox2)
layout.addWidget(inputLineEdit2)
inputLineEdit.setValidator(intValidator)
inputLineEdit.setValidator(oddValidator)

window.setLayout(layout)
window.show()
app.exec_()




