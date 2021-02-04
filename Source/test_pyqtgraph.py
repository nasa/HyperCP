import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout


class MyGraph(QWidget):
    def __init__(self):
        super(MyGraph, self).__init__()
        self.resize(600, 600)

        pg.setConfigOption('background', 'w')

        x = np.random.normal(size=1000)
        y = np.random.normal(size=1000)

        self.pw = pg.PlotWidget(self)
        self.plot = self.pw.plot(x, y, pen=None, symbol='o', symbolBrush='r')

        self.plot_btn = QPushButton("Replot", self, clicked=self.plot_slot)

        self.v_layout = QVBoxLayout(self)
        self.v_layout.addWidget(self.pw)
        self.v_layout.addWidget(self.plot_btn)        

    def plot_slot(self):
        x = np.random.normal(size=1000)
        y = np.random.normal(size=1000)

        # The new data is added to the existed one
        self.plot.setData(x, y)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = MyGraph()
    demo.show()
    sys.exit(app.exec_())