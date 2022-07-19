#!/usr/bin/env python 
# -*- coding: utf-8 -*-
'''
Time    : 2022/06/15 13:16
Author  : zhuchunjin
Email   : chunjin.zhu@taurentech.net
File    : ClkOptDialog.py
Software: PyCharm
'''
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QMessageBox

from redesigner_ui.clk_option_dialog import Ui_dialog


class ClkOptDialog(QDialog):
    Signal_parp = pyqtSignal(list)

    def __init__(self):
        super(ClkOptDialog, self).__init__()
        self.ui = Ui_dialog()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.para_updata)
        self.select_sheet = []

    def para_updata(self):
        if self.ui.lineEdit.text() != '' and self.ui.lineEdit_2.text() != '':
            self.select_sheet.append(self.ui.lineEdit.text())
            self.select_sheet.append(self.ui.lineEdit_2.text())
            self.select_sheet.append(self.ui.lineEdit_3.text())
            self.Signal_parp.emit(self.select_sheet)
            self.ok_and_quit()
        else:
            QMessageBox.information(self, 'tip', 'please input number!')

    def ok_and_quit(self):
        self.close()
