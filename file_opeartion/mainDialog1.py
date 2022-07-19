#!/usr/bin/env python 
# -*- coding: utf-8 -*-
'''
Time    : 2022/06/15 13:15
Author  : zhuchunjin
Email   : chunjin.zhu@taurentech.net
File    : mainDialog1.py
Software: PyCharm
'''
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog

from redesigner_ui.clk_option_dialog import Ui_Dialog1


class MainDialog1(QDialog):
    Signal_parp = pyqtSignal(str)

    def __init__(self, sheet_lst):
        super(MainDialog1, self).__init__()
        self.ui = Ui_Dialog1()
        self.ui.setupUi(self)
        self.sheet_lst = sheet_lst
        self.ui.comboBox.addItem('select one sheet')
        for x in sheet_lst:
            self.ui.comboBox.addItem(x)
        # self.ui.comboBox.currentIndexChanged.connect(self.select_sheet_lnk)
        self.ui.pushButton.clicked.connect(self.ok_and_quit)

    def select_sheet_lnk(self):
        self.select_sheet = self.ui.comboBox.currentText()
        if self.select_sheet != 'select one sheet':
            self.Signal_parp.emit(self.select_sheet)
        else:
            self.Signal_parp.emit("")

    def ok_and_quit(self):
        self.select_sheet_lnk()
        self.close()
