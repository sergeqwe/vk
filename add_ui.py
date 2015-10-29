# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'add.ui'
#
# Created: Thu Oct 22 11:44:54 2015
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_FormUrl(object):
    def setupUi(self, FormUrl):
        FormUrl.setObjectName("FormUrl")
        FormUrl.resize(600, 83)
        FormUrl.setMaximumSize(QtCore.QSize(16777215, 83))
        self.gridLayoutUrl2 = QtWidgets.QGridLayout(FormUrl)
        self.gridLayoutUrl2.setObjectName("gridLayoutUrl2")
        self.gridLayoutUrl = QtWidgets.QGridLayout()
        self.gridLayoutUrl.setObjectName("gridLayoutUrl")
        self.lineEditUrl = QtWidgets.QLineEdit(FormUrl)
        self.lineEditUrl.setObjectName("lineEditUrl")
        self.gridLayoutUrl.addWidget(self.lineEditUrl, 0, 0, 1, 1)
        self.gridLayoutUrl2.addLayout(self.gridLayoutUrl, 0, 0, 1, 1)
        self.pushButtonUrl = QtWidgets.QPushButton(FormUrl)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("pic/apply_8900.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButtonUrl.setIcon(icon)
        self.pushButtonUrl.setIconSize(QtCore.QSize(16, 16))
        self.pushButtonUrl.setDefault(True)
        self.pushButtonUrl.setObjectName("pushButtonUrl")
        self.gridLayoutUrl2.addWidget(self.pushButtonUrl, 1, 0, 1, 1, QtCore.Qt.AlignRight|QtCore.Qt.AlignBottom)

        self.retranslateUi(FormUrl)
        QtCore.QMetaObject.connectSlotsByName(FormUrl)

    def retranslateUi(self, FormUrl):
        _translate = QtCore.QCoreApplication.translate
        FormUrl.setWindowTitle(_translate("FormUrl", "Url"))
        self.pushButtonUrl.setText(_translate("FormUrl", "Ok"))

