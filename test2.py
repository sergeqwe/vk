#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import os
from re import sub
import time

import requests
from requests.auth import HTTPProxyAuth

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QAction, qApp, QFileDialog, QMessageBox, QSplashScreen
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt, QCoreApplication
# from PyQt5.QtWidgets import QToolTip
from PyQt5.QtGui import QPixmap, QImage, QFont
# from urllib.request import Request, urlopen
# from urllib.error import URLError, HTTPError
from vk_ui import Ui_MainWindow
from vk_settings_ui import Ui_Form
from add_ui import Ui_FormUrl
from downloading_ui import Ui_FormDownload

app = QApplication(sys.argv)
image = QPixmap('./pic/111.jpg')
splash = QSplashScreen(image)
splash.setAttribute(QtCore.Qt.WA_DeleteOnClose)
splash = QSplashScreen(image, Qt.WindowStaysOnTopHint)
splash.setMask(image.mask())
font = QFont(splash.font())
font.setPointSize(font.pointSize() + 5)
splash.setFont(font)
splash.show()
app.processEvents()
# time.sleep(2)

# splash.showMessage(splash.tr('Processing %1...{0}'),QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft, QtCore.Qt.white)
# QtCore.QThread.msleep(1000)
# QApplication.processEvents()
for count in range(1, 6):
    # splash.showMessage(splash, str(count),QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft, QtCore.Qt.blue)
    splash.showMessage('Loading: ' + str(count), QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft, QtCore.Qt.white)
#     print(str(count))
#
    app.processEvents()
    QtCore.QThread.msleep(1000)