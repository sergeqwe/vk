#! /usr/bin/env python
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QAction
import socket

UDP_IP = "192.168.1.1"
UDP_PORT = 20118

class RightClickMenu(QMenu):
    def __init__(self, parent=None):
        QMenu.__init__(self, "File", parent)

        # icon = QtGui.QIcon("system-shutdown")
        icon = QtGui.QIcon.fromTheme("load")
        offAction = QAction(icon, "&Off", self)
        offAction.triggered.connect(lambda : sendudp("s53905\n"))
        self.addAction(offAction)

        icon = QtGui.QIcon.fromTheme("view-statistics")
        fmAction = QAction(icon, "&FM", self)
        fmAction.triggered.connect(lambda : sendudp("s32113\n"))
        self.addAction(fmAction)

        icon = QtGui.QIcon.fromTheme("view-split-left-right")
        pcAction = QAction(icon, "&PC", self)
        pcAction.triggered.connect(lambda : sendudp("s32401\n"))
        self.addAction(pcAction)

        icon = QtGui.QIcon.fromTheme("text-speak")
        muteAction = QAction(icon, "&Mute", self)
        muteAction.triggered.connect(lambda : sendudp("s3641\n"))
        self.addAction(muteAction)

        icon = QtGui.QIcon("go-up")
        volupAction = QAction(icon, "Vol &Up", self)
        volupAction.triggered.connect(lambda : sendudp("s51153\n"))
        self.addAction(volupAction)

        icon = QtGui.QIcon("go-down")
        voldownAction = QAction(icon, "Vol &Down", self)
        voldownAction.triggered.connect(lambda : sendudp("s53201\n"))
        self.addAction(voldownAction)

        icon = QtGui.QIcon("media-skip-forward")
        chupAction = QAction(icon, "Ch U&p", self)
        chupAction.triggered.connect(lambda : sendudp("s3150\n"))
        self.addAction(chupAction)

        icon = QtGui.QIcon("media-skip-backward")
        chdownAction = QAction(icon, "Ch D&own", self)
        chdownAction.triggered.connect(lambda : sendudp("s32198\n"))
        self.addAction(chdownAction)

        icon = QtGui.QIcon("application-exit")
        exitAction = QAction(icon, "&Exit", self)
        exitAction.triggered.connect(lambda : QApplication.exit(0))
        self.addAction(exitAction)

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        QSystemTrayIcon.__init__(self, parent)
        self.setIcon(QtGui.QIcon.fromTheme("gnomeradio.xpm"))
        QSystemTrayIcon.setToolTip (self, 'qweqwedshf jsdgfjsd fgjhsd fjhsdgfjhsdgfjsdgfjhsgfjh\nwehrwe ruwe iweiurweiu riuweruw\nf kjhfkjhsdfkjsdhf')

        self.right_menu = RightClickMenu()
        self.setContextMenu(self.right_menu)

        self.activated.connect(self.onTrayIconActivated)

        class SystrayWheelEventObject(QtCore.QObject):
            def eventFilter(self, object, event):
                if type(event)==QtGui.QWheelEvent:
                    if event.delta() > 0:
                        sendudp("s51153\n")
                    else:
                        sendudp("s53201\n")
                    event.accept()
                    return True
                return False

        self.eventObj=SystrayWheelEventObject()
        self.installEventFilter(self.eventObj)

    def onTrayIconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            sendudp("s3641\n")

    def welcome(self):
        self.showMessage("Hello", "I should be aware of both buttons")

    def show(self):
        QSystemTrayIcon.show(self)
        #QtCore.QTimer.singleShot(100, self.welcome)

def sendudp(value):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto(bytes(value, 'UTF-8'), (UDP_IP, UDP_PORT))

if __name__ == "__main__":
    app = QApplication([])

    tray = SystemTrayIcon()
    tray.show()

    app.exec_()