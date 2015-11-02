#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import os
from re import sub
import time
import subprocess
import platform
import requests
from requests.auth import HTTPProxyAuth

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, qApp, QFileDialog, QMessageBox, QSplashScreen
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QFont

from vk_ui import Ui_MainWindow
from vk_settings_ui import Ui_Form
from add_ui import Ui_FormUrl


class Example(QMainWindow, Ui_MainWindow):

    DEBUG = True # Если TRUE, то выводим вспомогательную информацию в консоль
    result = {}  # Variable for JSON
    photo_avg = []  # Сюда помещаются картинки приблизительно равные размеру, заданному в переменной photo_size
    photo_date = []  # Сюда помещаются даты, когда были выложены картинки
    photo_max = []  # Сюда помещаются самые большие картинки
    current_page = 1  # Текущая страница просмоторщика
    label = {}  # Массив элементов label
    loading_image = []  # Сюда помещаем список загруженных фото
    button = {}  # Массив кнопок
    icon = {}  # Массив иконок для button
    pic_date = {}  # Массив времени публикации для картинок
    prev_mode = 0  # Флаг где находимся. 0 - если в превиюхах. 1 - если в режима просмотра большой картинки
    group_id = 0  # ID группы, которую будем загружать
    dict_count = {}  # Переменная через которую сопоставляется выделенный элемент в listWidget и ID для загрузки
    first_run = 0  # Если приложение запустилось первый раз, то при нажатии Load загрузить аватарки групп
    loading_error = False # Флаг удачной загрузки

    def __init__(self, MainWindow):
        super().__init__()

        # Сконфигурировать интерфейс методом из базового класса MainWindow
        self.setupUi(MainWindow)

        # Показываем заставку при загрузке
        self.downloading('Interface is initialized...')
        self.wait()

        # Подключить созданные нами слоты к виджетам
        self.connect_slots()

        try:
            fp = open("settings.json", "r")
            try:
                self.settings = json.load(fp)
            finally:
                fp.close()
                # Количество загружаемых страниц
                self.num_pages = self.settings['settings']['pages_load'][0]['num_pages']
                # Количество строк
                self.num_line = self.settings['settings']['preview'][0]['num_line']
                # Количество столбцов
                self.num_column = self.settings['settings']['preview'][0]['num_column']
                # Размер preview
                self.photo_size = self.settings['settings']['preview'][0]['prev_size']
                #  Путь (каталог на диске) для сохранения изображений
                self.pic_save_path = self.settings['settings']['pic_save'][0]['path']
                #  Прокси
                self.proxy_host = self.settings['settings']['proxies'][0]['host']
                self.proxy_port = self.settings['settings']['proxies'][0]['port']
                self.proxy_username = self.settings['settings']['proxies'][0]['username']
                self.proxy_password = self.settings['settings']['proxies'][0]['password']

                if not self.proxy_host:
                    self.proxies = {}
                    self.auth = HTTPProxyAuth('', '')

                if self.proxy_host and self.proxy_port:
                    self.proxies = {"http": "http://" + self.proxy_host + ":" + self.proxy_port,
                                    "https": "https://" + self.proxy_host + ":" + self.proxy_port}
                    self.auth = HTTPProxyAuth('', '')

                if self.proxy_host and self.proxy_port and self.proxy_username and self.proxy_password:
                    self.proxies = {"http": "http://" + self.proxy_username + ':' + self.proxy_password + '@' + self.proxy_host + ':' + self.proxy_port,
                                    "https": "https://" + self.proxy_username + ':' + self.proxy_password + '@' + self.proxy_host + ':' + self.proxy_port,}
                self.auth = HTTPProxyAuth(self.proxy_username, self.proxy_password)

                if self.DEBUG:
                    print('Proxy: ' + str(self.proxies))

                # Заполняем listVidget группами без аватарки
                self.group_fill()

        except IOError:
            self.statusbar.showMessage('settings.json not found!')
            self.num_pages = 2
            self.num_line = 2
            self.num_column = 2
            self.photo_size = 50

        # self.modalWindowDownloading.close()
        self.splash.close()

    # Подключаем слоты к виджетам
    def connect_slots(self):
        self.actionLoad.triggered.connect(self.load_pic)
        self.actionNext.triggered.connect(self.next_pic)
        self.actionPreview.triggered.connect(self.preview_pic)
        self.actionRefresh.triggered.connect(self.refresh)
        self.actionSettings.triggered.connect(self.settings_window)
        self.actionQuit.triggered.connect(qApp.quit)
        self.actionAbout.triggered.connect(self.about_vk)
        self.actionAbout_Qt.triggered.connect(self.about_qt)
        self.actionHelp.triggered.connect(self.help)
        self.actionOpen_saving_folder.triggered.connect(self.open_saving_folder)
        QMainWindow.resizeEvent = self.scale_pic

    # Заполняем listWidget списком групп
    def group_fill(self):
        self.listWidgetMain.clear()  # Очищаем listWidgetMain
        try:
            fp = open("settings.json", "r")
            try:
                self.settings = json.load(fp)
            finally:
                fp.close()
        except IOError:
            self.statusbar.showMessage('settings.json not found!')

        #  Заполняем listWidget списком групп
        self.dict = self.settings['vk_groups']
        # print('DICT: ' + str(self.dict))
        n = 0
        self.dict_count = {}  # Обнуляем
        for i in self.dict:
            self.listWidgetMain.addItem(self.dict[i])
            self.dict_count[n] = str(i)
            n += 1

    # Заполняем listWidget аватарками
    def group_fill_ava(self):
        self.listWidgetMain.clear()  # Очищаем listWidgetMain
        # Формируем список групп для которых нужно загрузить аватарку и выполняем запрос
        text = ''
        for i in range(len(self.dict_count)):
            text = text + str(self.dict_count[i])
            if i < len(self.dict_count) - 1:
                text = text + ','

        # Загружаем, парсим JSON и вытаскиваем аватарки групп
        url_ava = 'https://api.vk.com/method/groups.getById?v=5.32&group_ids=' + text
        if self.DEBUG:
            print('Get JSON Avatars URL: ' + url_ava)

        self.splash.showMessage('Downloading Avatars', QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter, QtCore.Qt.black)


        try:
            response = requests.get(url_ava, proxies=self.proxies, auth=self.auth)

        except IOError:
            if self.DEBUG:
                print('ERROR Loading avatars!')
            self.group_fill()
            self.loading_error = True
            self.splash.close()

        if self.loading_error == False:

            result = json.loads(response.text)

            # Заполняем listWidget аватарками групп
            loading_ava = []
            for i in range(len(self.dict_count)):

                if self.DEBUG:
                    print(str(i) + ')' + result['response'][i]['photo_50'])

                self.splash.showMessage(os.path.basename(result['response'][i]['photo_50']), QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter, QtCore.Qt.black)
                response = requests.get(result['response'][i]['photo_50'], proxies=self.proxies, auth=self.auth)
                image = QImage()
                image.loadFromData(response.content)
                loading_ava.append(image)
                item = QtWidgets.QListWidgetItem()
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(image), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                item.setIcon(icon)
                self.listWidgetMain.addItem(item)

        # Заполняем listWidget названиями групп
        n = 0
        for i in self.dict:
            item = self.listWidgetMain.item(n)
            item.setText(self.dict[i])
            # item.setText(str(i) + ':' + self.dict[i])
            # self.listWidgetMain.addItem(str(i) + ':' + self.dict[i])
            n += 1

    # Открываем каталок загрузок в текущем проводнике
    def open_saving_folder(self):
        if platform.system() == 'Linux':
            try:
                subprocess.check_call(['xdg-open', self.pic_save_path])
            except subprocess.CalledProcessError:
                QMessageBox.critical(window, 'Error','Unable to open dir\n"File->Settings->Path"')

    # Помощь
    def help(self):

        print(self.dict_count)
        #
        # self.group_id = self.dict_count[self.listWidgetMain.currentRow()]
        # print(self.group_id)
        #
        # self.downloading()

    # Увеличение картинки при растяжении окна
    def scale_pic(self, e):

        if self.prev_mode == 1:
            self.big_check()
            self.label.setPixmap(QtGui.QPixmap(self.image).scaled(
                self.width_my, self.height_my, QtCore.Qt.KeepAspectRatio))

    # Указываем путь для сохранения картинок
    def tool_button(self, e):
        print('tool button')
        fname = QFileDialog.getExistingDirectory(self, 'Dir', self.pic_save_path)
        if fname:
            self.lineEdit.setText(fname)

    # Обновить картинку
    def refresh(self):
        print('refresh')

        # self.load_big()
        self.big_check()

        self.label.setPixmap(QtGui.QPixmap(self.image).scaled(self.width_my, self.height_my, QtCore.Qt.KeepAspectRatio))

        # self.label.mousePressEvent = self.close_full_pic_view
        self.actionRefresh.setEnabled(True)

    def about_vk(self):
        QMessageBox.about(window, 'About VK Girls', 'VK Girls v.1.0')

    def about_qt(self):
        QMessageBox.aboutQt(window)

    # Загружаем картинки при нажатии кнопки Load
    def load_pic(self):

        # Проверяем есть ли и-нет соединение
        try:
            requests.get('http://vk.com', proxies=self.proxies, auth=self.auth)
        except IOError:
            if self.DEBUG:
                print('Check internet connection')
            msgBox = QMessageBox(
                QMessageBox.Critical,
                'Error',
                'Check internet connection',
                QMessageBox.NoButton)
            msgBox.exec_()
        else:

            print('Поехали')
            self.current_page = 1
            self.load_pic_list()
            self.load_pic_prev()
            self.draw_pic()
            self.check_buttons()
            self.statusbar.showMessage('Page: ' + str(self.current_page))
            self.loading_error = False

    # Загружаем следующую картинку при нажатии кнопки Next
    def next_pic(self):

        # Если находимся в режиме preview, то загружаем следующие
        if self.prev_mode == 0:
            # Показываем заставку при загрузке
            self.downloading('Loading next pics...')
            self.wait()
            self.current_page += 1
            self.load_pic_prev()
            self.draw_pic()
            self.check_buttons()
            self.statusbar.showMessage('Page: ' + str(self.current_page))
            self.splash.close()

        # Если находимся в режима просмотра большой картинки, то показываем следующую
        else:
            print('--->')

            if self.photo_max_id < len(self.photo_max) - 1:
                self.photo_max_id += 1
                self.load_big()
                self.big_check()

                self.label.setPixmap(QtGui.QPixmap(self.image).scaled(
                    self.width_my, self.height_my, QtCore.Qt.KeepAspectRatio))

            # Если фото последнее и режим просмотра большого фото,то делаем кнопку next в меню и на панели неактивной
            if self.photo_max_id >= len(self.photo_max) - 1 and self.prev_mode == 1:
                self.actionNext.setEnabled(False)
            else:
                self.actionNext.setEnabled(True)

            # Если фото первое и режим просмотра большого фото,то делаем кнопку preview неактивной
            if self.photo_max_id <= 0 and self.prev_mode == 1:
                self.actionPreview.setEnabled(False)
            else:
                self.actionPreview.setEnabled(True)

    # Загружаем предыдущую картинку при нажатии кнопки Preview
    def preview_pic(self):
        if self.prev_mode == 0:
            # Показываем заставку при загрузке
            self.downloading('Loading prev pics...')
            self.wait()
            self.current_page -= 1
            self.load_pic_prev()
            self.draw_pic()
            self.check_buttons()
            self.statusbar.showMessage('Page: ' + str(self.current_page))
            self.splash.close()
        else:
            print('<---')

            if self.photo_max_id > 0:

                self.photo_max_id -= 1
                self.load_big()
                self.big_check()  # Сравниваем его размер с размером окна
                self.label.setPixmap(QtGui.QPixmap(self.image).scaled(
                    self.width_my, self.height_my, QtCore.Qt.KeepAspectRatio))

            # Если фото последнее и режим просмотра большого фото,то делаем кнопку next в меню и на панели неактивной
            if self.photo_max_id >= len(self.photo_max) - 1 and self.prev_mode == 1:
                self.actionNext.setEnabled(False)
            else:
                self.actionNext.setEnabled(True)

            # Если фото первое и режим просмотра большого фото,то делаем кнопку preview неактивной
            if self.photo_max_id <= 0 and self.prev_mode == 1:
                self.actionPreview.setEnabled(False)
            else:
                self.actionPreview.setEnabled(True)

    # Просмотр большого фото
    def full_pic_view(self, event):

        # Показываем заставку при загрузке
        self.downloading('Loading full image...')
        self.wait()

        """Загрузка и просмотр большого изображения"""
        self.prev_mode = 1  # Выставляем флаг, что мы перешли в режим просмотра большого фото
        self.wat_is_button()  # Какая кнопка с preview была нажата, чтобы загрузить большое фото
        self.clear_screen()  # Удаляем все кнопки с изображениями (очищаем окно)
        self.check_buttons()  # Проверяем флаги кнопок в меню и тулбаре
        # self.win_size()  # Определяем текущий размер окна

        # Ищем большое фото
        mult_num = self.num_line * self.num_column
        self.photo_max_id = self.current_page *\
                            mult_num - mult_num + self.sender1

        # Создаем Label в котором будем выводить фото
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")

        self.load_big()  # Загружаем большое фото
        self.big_check()  # Сравниваем его размер с размером окна


        self.label.setPixmap(QtGui.QPixmap(self.image).scaled(
            self.width_my, self.height_my, QtCore.Qt.KeepAspectRatio))
        self.gridLayout_2.addWidget(self.label, 0, 0, 0, 0)
        self.label.mousePressEvent = self.close_full_pic_view

        # Если фото последнее, то делаем кнопку next в меню и на панели неактивной
        if self.photo_max_id >= len(self.photo_max) - 1:
            self.actionNext.setEnabled(False)

        # Если фото первое, то делаем кнопку preview неактивной
        if self.photo_max_id == 0:
            self.actionPreview.setEnabled(False)

        # Закрываем заставку
        self.splash.close()

    # Загрузка большого фото
    def load_big(self):
        """Загружаем большое фото"""
        # req = Request(self.photo_max[self.photo_max_id])
        # response = urlopen(req).read()

        # # Показываем заставку при загрузке
        # self.downloading()
        # self.wait()

        response = requests.get(self.photo_max[self.photo_max_id], proxies=self.proxies, auth=self.auth)

        self.image = QImage()
        self.image.loadFromData(response.content)

        # self.modalWindowDownloading.close()

    # Подгоняем размер картинки под размер окна
    def big_check(self):
        # Определяем размер окна, чтобы оно не растягивалось, если размер изображения больше, чем размер окна
        self.win_size()

        # Сверяем размер большого фото с размером окна
        if self.image.width() < self.width:
            self.width_my = self.image.width()
            self.height_my = self.image.height()

        else:
            if self.DEBUG:
                print('BIG_width')
            self.width_my = self.width - self.width * 0.1
            self.height_my = self.height - self.height * 0.1

        if self.height_my < self.height:
            if self.DEBUG:
                print('do nothing')
        else:
            if self.DEBUG:
                print('BIG_height')
            self.width_my = self.width - self.width * 0.1
            self.height_my = self.height - self.height * 0.1
        if self.DEBUG:
            print('Ширина:{0}; Высота:{1}'.format(self.width_my, self.height_my))

    # ##############Окно настроек ######################################################
    def settings_window(self):
        """Окно настройки"""

        combo = {
            50: 0,
            100: 1,
            130: 2,
            160: 3,
            200: 4,
            250: 5
        }

        self.modalWindow = QWidget(window, Qt.Window)
        self.modalWindow.setWindowModality(Qt.WindowModal)
        # SettingsWindow(modalWindow)

        Ui_Form.setupUi(self, self.modalWindow)
        Ui_Form.retranslateUi(self, self.modalWindow)

        self.pushButtonOK.mousePressEvent = self.button_ok
        self.pushButtonCancel.mousePressEvent = self.button_cancel
        self.toolButton.mousePressEvent = self.tool_button
        self.pushButtonAdd.mousePressEvent = self.button_add
        self.pushButtonDel.mousePressEvent = self.button_del
        self.checkBox.stateChanged.connect(self.check_box)
        self.radioButtonYes.toggled.connect(self.radio_button)



        self.modalWindow.setAttribute(Qt.WA_DeleteOnClose, True)
        # modalWindow.move(window.geometry().center() - modalWindow.rect().center() - QtCore.QPoint(4, 30))

        try:
            fp = open("settings.json", "r")
            try:
                self.settings = json.load(fp)
            finally:
                fp.close()
                # Размер preview
                self.photo_size = self.settings['settings']['preview'][0]['prev_size']
                self.comboBox.setCurrentIndex(combo[self.photo_size])

                # Количество загружаемых страниц
                self.num_pages = self.settings['settings']['pages_load'][0]['num_pages']
                self.spinPages.setProperty("value", self.num_pages)

                # Количество строк
                self.num_line = self.settings['settings']['preview'][0]['num_line']
                self.spinRow.setProperty("value", self.num_line)

                # Количество столбцов
                self.num_column = self.settings['settings']['preview'][0]['num_column']
                self.spinColumns.setProperty("value", self.num_column)

                #  Путь (каталог на диске) для сохранения изображений
                self.pic_save_path = self.settings['settings']['pic_save'][0]['path']
                self.lineEdit.setText(self.pic_save_path)

                #  Заполняем listWidget списком групп
                dict = self.settings['vk_groups']
                for i in dict:
                    self.listWidget.addItem(str(i) + ':' + dict[i])

                #  Заполняем прокси, если есть
                self.proxy_host = self.settings['settings']['proxies'][0]['host']
                self.proxy_port = self.settings['settings']['proxies'][0]['port']
                self.proxy_username = self.settings['settings']['proxies'][0]['username']
                self.proxy_password = self.settings['settings']['proxies'][0]['password']

                if self.proxy_host and self.proxy_port:
                    self.radioButtonYes.setChecked(True)
                    self.lineEditProxy.setText(self.proxy_host)
                    self.spinBoxPort.setProperty("value", self.proxy_port)
                    if self.proxy_username and self.proxy_password:
                        self.checkBox.setChecked(True)
                        self.lineEditLogin.setText(self.proxy_username)
                        self.lineEditPwd.setText(self.proxy_password)
                    else:
                        self.lineEditLogin.setDisabled(True)
                        self.lineEditPwd.setDisabled(True)
                else:
                    self.radioButtonNo.setChecked(True)

                    self.lineEditProxy.setDisabled(True)
                    self.spinBoxPort.setDisabled(True)

                    self.lineEditLogin.setDisabled(True)
                    self.lineEditPwd.setDisabled(True)

                    self.checkBox.setDisabled(True)

        except IOError:
            self.num_pages = 2
            self.num_line = 2
            self.num_column = 2
            self.photo_size = 50

        self.modalWindow.show()

    def radio_button(self):
        if self.radioButtonYes.isChecked():
            self.lineEditProxy.setDisabled(False)
            self.spinBoxPort.setDisabled(False)
            self.checkBox.setDisabled(False)
        else:
            self.lineEditProxy.setDisabled(True)
            self.spinBoxPort.setDisabled(True)
            self.checkBox.setDisabled(True)
            self.lineEditLogin.setDisabled(True)
            self.lineEditPwd.setDisabled(True)
            self.checkBox.setChecked(False)

    def check_box(self):
        if self.checkBox.isChecked():
            self.lineEditLogin.setDisabled(False)
            self.lineEditPwd.setDisabled(False)
        else:
            self.lineEditLogin.setDisabled(True)
            self.lineEditPwd.setDisabled(True)

    # Кнопка добавления группы в список listWidget
    def button_add(self, e):
        print('button add')
        self.modalWindowAdd = QWidget(window, Qt.Window)
        self.modalWindowAdd.setWindowModality(Qt.WindowModal)

        Ui_FormUrl.setupUi(self, self.modalWindowAdd)
        Ui_FormUrl.retranslateUi(self, self.modalWindowAdd)

        self.pushButtonUrl.mousePressEvent = self.buttonUrl

        self.modalWindowAdd.show()

    # Кнопка удаления группы из списка listWidget
    def button_del(self, e):
        print(self.settings['vk_groups'])
        # Берем из listWidget текущее значение (id группы)
        self.group_id = self.dict_count[self.listWidget.currentRow()]
        # print(self.group_id)
        # print(self.dict_count)
        # self.dict_count.pop(self.dict_count[self.group_id])
        # print(self.dict_count)

        # Удаляем текущее значение из JSON
        self.settings['vk_groups'].pop(self.group_id)
        print(self.settings['vk_groups'])

        # Удаляем текущее значение из списка listWidget
        for item in self.listWidget.selectedItems():
            self.listWidget.takeItem(self.listWidget.row(item))

    def buttonUrl(self, e):
        url = self.lineEditUrl.text()
        try:
            response = requests.post(url, proxies=self.proxies, auth=self.auth)
        except IOError:
            print('Unable to fetch URL!')
            QMessageBox.critical(self.modalWindowAdd, 'Error','Unable to fetch URL!\nURL must be like: http://vk.com/sergeqwe')

            return None


        if response.status_code == 200:
            # Ищем ID группы
            result = response.text
            start = result.find('[group]')
            id = result[start:start+20]
            if id:
                id = int(sub("\D", "", id))
                print(id)

                # Ищем название группы
                start = result.find('<title>')
                end = result.find('</title>')
                groupe_name = result[start+7:end]
                print(groupe_name)

                self.listWidget.addItem(str(id) + ':' + groupe_name)
                self.settings['vk_groups'][str(id)] = groupe_name

                print(self.settings['vk_groups'])

            else:
                QMessageBox.critical(self.modalWindowAdd, 'Error', 'Not a group!')
                return None
        else:
            print('Unable to fetch URL...')

        self.modalWindowAdd.close()

    def button_ok(self, e):

        # Размер preview
        self.settings['settings']['preview'][0]['prev_size'] = int(self.comboBox.currentText())
        self.photo_size = int(self.comboBox.currentText())

        # Количество загружаемых страниц
        self.settings['settings']['pages_load'][0]['num_pages'] = int(self.spinPages.text())
        self.num_pages = int(self.spinPages.text())

        # Количество строк
        self.settings['settings']['preview'][0]['num_line'] = int(self.spinRow.text())
        self.num_line = int(self.spinRow.text())

        # Количество столбцов
        self.settings['settings']['preview'][0]['num_column'] = int(self.spinColumns.text())
        self.num_column = int(self.spinColumns.text())

        #  Путь (каталог на диске) для сохранения изображений
        self.settings['settings']['pic_save'][0]['path'] = self.lineEdit.text()
        self.pic_save_path = self.lineEdit.text()

        # Проверяем включен ли в настройках прокси
        # Если прокси выключен, то обнуляем переменную proxies
        if self.radioButtonNo.isChecked():
            print('proxy_disable')
            self.proxies = {}
            self.auth = HTTPProxyAuth('', '')

        if self.radioButtonYes.isChecked():

            if self.checkBox.isChecked():

                username = self.lineEditLogin.text()
                password = self.lineEditPwd.text()

                self.proxies = {
                "http": 'http://' + username + ':' + password + '@' + self.lineEditProxy.text() + ':' + self.spinBoxPort.text(),
                "https": 'http://' + username + ':' + password + '@' + self.lineEditProxy.text() + ':' + self.spinBoxPort.text(),
                }

                self.auth = self.auth = HTTPProxyAuth(username, password)

                self.settings['settings']['proxies'][0]['username'] = self.lineEditLogin.text()
                self.settings['settings']['proxies'][0]['password'] = self.lineEditPwd.text()

            else:
                self.proxies = {
                "http": 'http://' + self.lineEditProxy.text() + ':' + self.spinBoxPort.text(),
                "https": 'http://' + self.lineEditProxy.text() + ':' + self.spinBoxPort.text(),
                }

                self.settings['settings']['proxies'][0]['username'] = ''
                self.settings['settings']['proxies'][0]['password'] = ''

            self.settings['settings']['proxies'][0]['host'] = self.lineEditProxy.text()
            self.settings['settings']['proxies'][0]['port'] = self.spinBoxPort.text()

        else:
            self.settings['settings']['proxies'][0]['host'] = ''
            self.settings['settings']['proxies'][0]['port'] = ''
            self.settings['settings']['proxies'][0]['username'] = ''
            self.settings['settings']['proxies'][0]['password'] = ''

        try:
            fp = open("settings.json", "w")
            try:
                json.dump(self.settings, fp, indent=4)
            finally:
                fp.close()

        except IOError:
            print('error')

        self.group_fill()
        self.modalWindow.close()
        self.first_run = 0

    def button_cancel(self, e):
        print('cancel')
        self.modalWindow.close()

    ######################################################################################

    # Флаги активности кнопок
    def check_buttons(self):
        """Флаги для выставления активности(затемненности) пунктов меню и кнопок"""

        # Если находимся в режиме росмотра большого фото, то делаем кнопку refresh активной
        # А кнопку Load недоступной
        if self.prev_mode == 1:
            self.actionRefresh.setEnabled(True)
            self.actionLoad.setEnabled(False)
        else:
            self.actionRefresh.setEnabled(False)
            self.actionLoad.setEnabled(True)

        if self.loading_error == False:
            # Если в режиме preview и на последней странице, то затемняем кнопку next
            if self.current_page == (len(self.result["response"]["items"])) / (self.num_line * self.num_column)\
                    and self.prev_mode == 0:
                self.actionPreview.setEnabled(True)
                self.actionNext.setEnabled(False)

            else:
                self.actionPreview.setEnabled(True)
                self.actionNext.setEnabled(True)

        # Если в режиме preview и на первой странице, то затемняем кнопку preview
        if self.current_page == 1 and self.prev_mode == 0:
            self.actionPreview.setEnabled(False)
            self.actionNext.setEnabled(True)

    #  Загружаем список фото
    def load_pic_list(self):


        self.downloading('Loading...')
        self.wait()

        if self.first_run == 0:
            self.group_fill_ava()
            self.first_run = 1

        current_row = self.listWidgetMain.currentRow()

        #  Берем из listWidget текущее значение (id группы)
        if self.DEBUG:
            print('Current row (group): ' + str(current_row))

        if current_row == -1:
            current_row = 0
            if self.DEBUG:
                print('Current row (group): ' + str(current_row))


        self.group_id = self.dict_count[current_row]

        if self.DEBUG:
            print('Groupe ID: ' + self.group_id)

        """Загружаем и парсим JSON"""

        # self.label.setPixmap(QtGui.QPixmap("pic/avto.jpg").scaled(200, 200, QtCore.Qt.KeepAspectRatio))

        req = 'https://api.vk.com/method/photos.get?v=5.32' \
              '&owner_id=-{0}' \
              '&album_id=wall&count={1}' \
              '&rev=1&photo_sizes=1'.format(self.group_id,(self.num_line * self.num_column) * self.num_pages)

        if self.DEBUG:
            print('Loading JSON list of pics: ' + req)

        try:
            response = requests.get(req, proxies=self.proxies, auth=self.auth, timeout=3)

        except requests.exceptions.Timeout:
            print('Time out')
            self.loading_error = True


        except requests.exceptions.ProxyError:
            print('04 Gateway Time-out')
            self.loading_error = True

        except IOError:
            print('Error loading JSON')
            self.loading_error = True


        # if response.status_code != 200:
        #     print('Косяк. Статус код')
        #     self.loading_error = True

        if self.loading_error == False:
            self.result = json.loads(response.text)

            # req = Request(req)
            #
            # try:
            #     response = urlopen(req)
            #
            # except HTTPError as e:
            #     print('The server couldn\'t fulfill the request.')
            #     print('Error code: ', e.code)
            #     exit(0)
            #
            # except URLError as e:
            #     print('We failed to reach a server.')
            #     print('Reason: ', e.reason)
            #     exit(0)
            #
            # self.result = json.loads(response.read().decode('utf8'))
            # print('JSON LOADING OK')
            # print(self.result)

            # Ищем приблизительно равные размеры фото заданные в переменной photo_size
            # Так же помещаем в переменную photo_date дату публикации фото

            if self.DEBUG:
                print('Всего фото загружено: ' + str(len(self.result["response"]["items"])))
            if len(self.result["response"]["items"]) < (self.num_line * self.num_column) * self.num_pages:
                print('НЕТ СТОЛЬКО ФОТО!')
                exit(0)
                return None

            self.photo_avg = []
            self.photo_date = []
            e = 0
            while e < len(self.result["response"]["items"]):
                i = 0
                v = []
                while i < len(self.result["response"]["items"][e]["sizes"]):
                    v.append(abs(self.photo_size - self.result["response"]["items"][e]["sizes"][i]["height"]))
                    i += 1

                out = 0
                generator = enumerate(v)
                out = [i for i,x in generator if x == min(v)]
                self.photo_avg.append(self.result["response"]["items"][e]["sizes"][out[0]]["src"])
                self.photo_date.append(self.result["response"]["items"][e]["date"])

                e += 1

            # Ищем картинку с самым большим разрешением
            self.photo_max = []
            e = 0
            while e < len(self.result["response"]["items"]):

                i = 0
                v = 0
                count = 0

                while i < len(self.result["response"]["items"][e]["sizes"]):

                    if v < self.result["response"]["items"][e]["sizes"][i]["height"]:
                        v = self.result["response"]["items"][e]["sizes"][i]["height"]
                        count = i

                    i += 1

                self.photo_max.append(self.result["response"]["items"][e]["sizes"][count]["src"])
                e += 1

            if self.DEBUG:
                print(self.photo_max)
            # self.modalWindowDownloading.close()
        self.splash.close()


    # Загружаем preview
    def load_pic_prev(self):
        """Загружаем фото с сайта в зависимости от страницы и момещаем их в список loading_image"""

        # Показываем заставку при загрузке
        self.downloading('Img...')
        self.wait()

        if self.loading_error == False:
            if self.result and len(self.result["response"]["items"]) == (self.num_line * self.num_column) * self.num_pages:

                self.loading_image = []  # Обнуляем список
                mult_num = self.num_line * self.num_column
                for i in range(self.current_page * mult_num - mult_num, self.current_page * mult_num):

                    # req = Request(self.photo_avg[i])
                    # response = urlopen(req).read()
                    try:
                        response = requests.get(self.photo_avg[i], proxies=self.proxies, auth=self.auth)
                    except IOError:
                        print('Не смог загрузить preview на страницу')
                        exit(0)
                    image = QImage()
                    image.loadFromData(response.content)
                    self.loading_image.append(image)
                    if self.DEBUG:
                        print(str(i) + ')' + self.photo_avg[i])
                    self.splash.showMessage(os.path.basename(self.photo_avg[i]), QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter, QtCore.Qt.black)
            else:
                print('NO_RESULT')

            # self.modalWindowDownloading.close()
            # print('На странице: ' + str(self.loading_image))
            if self.loading_image[0].size().width() <=0:
                if self.DEBUG:
                    print('Error internet connection')
                # QMessageBox.critical(window, 'Error','Error internet connection')
                self.splash.close()
                msgBox = QMessageBox(
                    QMessageBox.Critical,
                'Error',
                'Check internet connection',
                QMessageBox.NoButton)
                msgBox.exec_()
                self.first_run = 0
                return None

        self.splash.close()


    # Выводим preview
    def draw_pic(self):
        if self.loading_error == False:
            """Выводим preview"""
            self.clear_screen()  # Очищаем окно

            if len(self.result["response"]["items"]) == (self.num_line * self.num_column) * self.num_pages:


                t = 0
                for i in range(self.num_line):
                    for n in range(self.num_column):
                        self.icon[t] = QtGui.QIcon()
                        self.icon[t].addPixmap(QtGui.QPixmap(self.loading_image[t]), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                        self.button[t] = QtWidgets.QPushButton(self.centralwidget)
                        self.button[t].setIcon(self.icon[t])
                        self.button[t].setIconSize(QtCore.QSize(self.photo_size, self.photo_size))
                        self.button[t].setFlat(True)
                        # self.button[t].setStyleSheet('background-color:#FFFFFF;color:#000000;')
                        # self.button[t].setStyleSheet("font-size:40px;background-color:#333333;border: 2px solid #222222")
                        # self.button[t].setStyleSheet("border: 1px solid #222222")
                        self.gridLayout_2.addWidget(self.button[t], i, n, 1, 1, QtCore.Qt.AlignTop)
                        self.button[t].setObjectName("Button: " + str(t))
                        self.pic_date[t] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(self.photo_date[t]))
                        self.button[t].setToolTip(str(self.pic_date[t]))
                        self.button[t].clicked.connect(self.full_pic_view)
                        t += 1
            else:
                print('Не совпало')
                exit(0)

    # Выход из просмотра большой картинки при нажатии левой кнопки и сохранение картинки при нажатии правой кнопки
    def close_full_pic_view(self, e):
        """Закрываем просмотр большой картинки левым кликом мыши"""
        if e.buttons() == QtCore.Qt.LeftButton:
            if self.DEBUG:
                print('left button pressed')
            self.prev_mode = 0  # Флаг, что выходим из просмотра в preview
            self.clear_screen()  # Удаляем изображение
            self.check_buttons()
            self.draw_pic()
            self.statusbar.showMessage('Page: ' + str(self.current_page))

        #  Созраняем изображение при нажатии правой кнопки мыши
        if e.buttons() == QtCore.Qt.RightButton:

            path = self.pic_save_path + '/' + os.path.basename(self.photo_max[self.photo_max_id])
            print(path)
            self.image.save(path)

            if os.path.exists(path):
                self.statusbar.showMessage('File saved to: ' + path )
            else:
                self.statusbar.showMessage('File is not saved. Сheck the path settings!' )
                msgBox = QMessageBox(
                    QMessageBox.Critical,
                    'Error', 'File is not saved. Сheck the path settings!\n<File-Settings-Path>',
                    QMessageBox.NoButton)
                msgBox.exec_()

    # Очищаем окно
    def clear_screen(self):
        """Удаляем все кнопки с изображениями (очищаем окно)"""
        while self.gridLayout_2.count():
            item = self.gridLayout_2.takeAt(0)
            item.widget().deleteLater()

    #  Определяем какая кнопка (превиюшка) была нажата
    def wat_is_button(self):
        """Определяем какая кнопка была нажата"""
        sender1 = self.sender().objectName()
        self.sender1 = int(sub("\D", "", sender1))
        print(self.sender1)

    # Определяем размер окна
    def win_size(self):
        """Определяем размер окна (scrollArea), чтобы оно не растягивалось, если размер изображения больше, чем размер окна"""
        # self.height = window.size().height() - 70
        # self.width = window.size().width() - 10

        self.height = self.scrollArea.size().height()
        self.width = self.scrollArea.size().width()

    # Окно загрузки
    def downloading(self, msg):
        # print('downloading...')
        # self.modalWindowDownloading = QWidget(window, Qt.Window)
        # self.modalWindowDownloading.setWindowModality(Qt.WindowModal)
        # Ui_FormDownload.setupUi(self, self.modalWindowDownloading)
        # Ui_FormDownload.retranslateUi(self, self.modalWindowDownloading)
        # self.modalWindowDownloading.show()

        image = QPixmap('./pic/loading1.jpg')
        self.splash = QSplashScreen(image)
        self.splash.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.splash = QSplashScreen(image, Qt.WindowStaysOnTopHint)
        self.splash.setMask(image.mask())
        font = QFont(self.splash.font())
        font.setPointSize(font.pointSize() + 3)
        self.splash.setFont(font)
        self.splash.showMessage(msg, QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter, QtCore.Qt.black)
        self.splash.show()

    def wait(self):
        start = time.time()
        while time.time() - start < 1:
            time.sleep(0.001)
            app.processEvents()

if __name__ == '__main__':

    # Создаём экземпляр приложения
    app = QApplication(sys.argv)
    # Создаём базовое окно, в котором будет отображаться наш UI
    window = QMainWindow()
    # Создаём экземпляр нашего UI
    ui = Example(window)
    # Отображаем окно
    window.show()
    # Обрабатываем нажатие на кнопку окна "Закрыть"
    sys.exit(app.exec_())