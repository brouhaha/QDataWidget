#!/usr/bin/env python3
# Copyright 2022 Eric Smith <spacewar@gmail.com>
# SPDX-License-Identifier: MIT

import sys

from PySide2 import QtWidgets as qtw

from QDataWidget import QDataField, QDataWidget


class Resistor(QDataWidget):
    ref = QDataField(str)
    resistance = QDataField(float)
    tolerance = QDataField(float, default_value = 0.05)
    kind = QDataField(str, default_value = 'metal film')


class MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.r1 = Resistor(ref = 'r1', resistance = 220.0)
        self.setCentralWidget(self.r1)

        inc_action = qtw.QAction("increment", self)
        inc_action.triggered.connect(self.increment)

        debug_menu = self.menuBar().addMenu("Debug")
        debug_menu.addAction(inc_action)


    def increment(self):
        r = self.r1.resistance
        r_new = r + 1.0
        print(f'increment resistance from {r} to {r_new}')
        self.r1.resistance = r_new


app = qtw.QApplication(sys.argv)

mw = MainWindow()
mw.show()
sys.exit(app.exec_())
