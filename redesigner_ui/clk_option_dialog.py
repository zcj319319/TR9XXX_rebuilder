# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dialog(object):
    def setupUi(self, dialog):
        dialog.setObjectName("dialog")
        dialog.resize(199, 212)
        self.lineEdit = QtWidgets.QLineEdit(dialog)
        self.lineEdit.setGeometry(QtCore.QRect(30, 40, 113, 20))
        self.lineEdit.setObjectName("lineEdit")
        self.label = QtWidgets.QLabel(dialog)
        self.label.setGeometry(QtCore.QRect(40, 20, 140, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(dialog)
        self.label_2.setGeometry(QtCore.QRect(150, 40, 30, 16))
        self.label_2.setObjectName("label_2")
        self.lineEdit_2 = QtWidgets.QLineEdit(dialog)
        self.lineEdit_2.setGeometry(QtCore.QRect(30, 85, 113, 20))
        self.lineEdit_2.setText("")
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.label_3 = QtWidgets.QLabel(dialog)
        self.label_3.setGeometry(QtCore.QRect(40, 65, 121, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(dialog)
        self.label_4.setGeometry(QtCore.QRect(150, 85, 30, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(dialog)
        self.label_5.setGeometry(QtCore.QRect(40, 110, 111, 16))
        self.label_5.setObjectName("label_5")
        self.lineEdit_3 = QtWidgets.QLineEdit(dialog)
        self.lineEdit_3.setGeometry(QtCore.QRect(30, 130, 113, 20))
        self.lineEdit_3.setText("")
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.label_6 = QtWidgets.QLabel(dialog)
        self.label_6.setGeometry(QtCore.QRect(150, 130, 20, 16))
        self.label_6.setObjectName("label_6")
        self.pushButton = QtWidgets.QPushButton(dialog)
        self.pushButton.setGeometry(QtCore.QRect(65, 170, 75, 23))
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(dialog)
        QtCore.QMetaObject.connectSlotsByName(dialog)

    def retranslateUi(self, dialog):
        _translate = QtCore.QCoreApplication.translate
        dialog.setWindowTitle(_translate("dialog", "CLK OPTION"))
        self.label.setText(_translate("dialog", "ADC Sampling Rate"))
        self.label_2.setText(_translate("dialog", "MHz"))
        self.label_3.setText(_translate("dialog", "ADC input Freq"))
        self.label_4.setText(_translate("dialog", "MHz"))
        self.label_5.setText(_translate("dialog", "Lane rate"))
        self.label_6.setText(_translate("dialog", "GHz"))
        self.pushButton.setText(_translate("dialog", "OK"))

class Ui_Dialog1(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(334, 145)
        self.comboBox = QtWidgets.QComboBox(Dialog)
        self.comboBox.setGeometry(QtCore.QRect(30, 30, 280, 25))
        self.comboBox.setObjectName("comboBox")
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(110, 90, 120, 25))
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "select sheet"))
        self.pushButton.setText(_translate("Dialog", "OK"))
