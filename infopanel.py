# -*- coding: utf-8 -*-
import os
import sys
import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
import requests
import urllib3
import httplib2
from PIL import Image
from os import remove
from json import loads
from random import choice
import sqlite3
import re
from time import time, sleep
import resource_validator
import subprocess

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WriteDB:
    def __init__(self):
        self.connection = sqlite3.connect('Rasp.db')
        self.cursor = self.connection.cursor()
        self.json = ''

    def update_db(self):
        self.get_new_json()
        old_json1 = self.cursor.execute('''SELECT json from schedule WHERE id=0''').fetchone()
        old_json2 = self.cursor.execute('''SELECT json from schedule WHERE id=2''').fetchone()
        self.cursor.execute('''UPDATE schedule SET json = ? WHERE id=0''', (old_json2,))
        self.cursor.execute('''UPDATE schedule SET json = ? WHERE id=2''', (''.join(old_json1, )))
        self.connection.commit()
        self.connection.close()

    def get_new_json(self):
        url = 'https://lyceum.nstu.ru/rasp/schedule.html'
        content = requests.get(url, verify=False)
        content.encoding = 'utf-8'
        # source = BeautifulSoup(content.text, "html.parser")
        js_source = re.findall(
            r'<script type="text/javascript" src="(nika_data_\d{8}_\d{6}.js)"></script>',
            content.text
        )[0]
        print('JS_Source:', js_source)
        schedule_js = requests.get('https://lyceum.nstu.ru/rasp/' + js_source, verify=False)
        schedule_js.encoding = 'utf-8'
        # schedule_js = BeautifulSoup(schedule_js.text, "html.parser")
        self.json = str(schedule_js.text)[133:-3]

    def get_next(self):
        return ''.join(self.cursor.execute('''SELECT json from schedule WHERE id=2''').fetchone())

    def get_prev(self):
        return ''.join(self.cursor.execute('''SELECT json from schedule WHERE id=0''').fetchone())

    def check(self):
        self.get_new_json()
        if int(*loads(self.json)['PERIODS'].keys()) % 2 == 0:
            return True
        return False


class GetRasp:
    @staticmethod
    def getrasp():
        url = 'https://lyceum.nstu.ru/rasp/schedule.html'
        content = requests.get(url, verify=False)
        content.encoding = 'utf-8'
        # source = BeautifulSoup(content.text, "html.parser")
        # schedule_js = requests.get('https://lyceum.nstu.ru/rasp/' + source.select("script")[0]['src'], verify=False)
        # schedule_js.encoding = 'utf-8'
        '''schedule_js = BeautifulSoup(schedule_js.text, "html.parser")'''
        js_source = re.findall(
            r'<script type="text/javascript" src="(nika_data_\d{8}_\d{6}.js)"></script>',
            content.text
        )[0]
        print('JS_Source:', js_source)
        schedule_js = requests.get('https://lyceum.nstu.ru/rasp/' + js_source, verify=False)
        schedule_js.encoding = 'utf-8'
        data_py = loads(str(schedule_js.text)[133:-3])
        rasp_dict = {}
        for i in data_py["CLASSES"].keys():
            rasp_dict[data_py["CLASSES"][i]] = []
        week_schedule = ''
        for group in data_py["CLASSES"].keys():
            class_ = data_py["CLASSES"][group]
            week_schedule += class_
            schedule = data_py['CLASS_SCHEDULE'][str(*data_py['PERIODS'].keys())][group]
            day = ''
            for i in schedule:
                if data_py['DAY_NAMES'][int(i) // 100 - 1] != day:
                    day = data_py['DAY_NAMES'][int(i) // 100 - 1]
                    week_schedule += ', ' + day + '  '
                if i[1] == '0':
                    num = i[-1]
                else:
                    num = i[1:]
                if len(schedule[i]['s']) > 1:
                    try:
                        week_schedule += num + '. ' + data_py['SUBJECTS'][schedule[i]['s'][0]] + '(' + data_py['ROOMS'][
                            schedule[i]['r'][0]] + ')' + '/'
                    except KeyError:
                        week_schedule += num + '. ' + 'Занятий нет/'
                    try:
                        week_schedule += data_py['SUBJECTS'][
                                             schedule[i]['s'][1]] + '(' + data_py['ROOMS'][
                                             schedule[i]['r'][1]] + ')' + '  '
                    except KeyError:
                        week_schedule += 'Занятий нет' + '  '
                else:
                    week_schedule += num + '. ' + data_py['SUBJECTS'][schedule[i]['s'][0]] + '(' + data_py['ROOMS'][
                        schedule[i]['r'][0]] + ')' + '  '
            week_schedule += '\n'
        for i in week_schedule.split('\n'):
            days = i.split(', ')
            for j in days[1:]:
                rasp_dict[days[0]].append(j.split('  '))
        return rasp_dict

    @staticmethod
    def get_previousrasp(json):
        data_py = loads(json)
        rasp_dict = {}
        for i in data_py["CLASSES"].keys():
            rasp_dict[data_py["CLASSES"][i]] = []
        week_schedule = ''
        for group in data_py["CLASSES"].keys():
            class_ = data_py["CLASSES"][group]
            week_schedule += class_
            schedule = data_py['CLASS_SCHEDULE'][str(*data_py['PERIODS'].keys())][group]
            day = ''
            for i in schedule:
                if data_py['DAY_NAMES'][int(i) // 100 - 1] != day:
                    day = data_py['DAY_NAMES'][int(i) // 100 - 1]
                    week_schedule += ', ' + day + '  '
                if i[1] == '0':
                    num = i[-1]
                else:
                    num = i[1:]
                if len(schedule[i]['s']) > 1:
                    try:
                        week_schedule += num + '. ' + data_py['SUBJECTS'][schedule[i]['s'][0]] + '(' + \
                                         data_py['ROOMS'][
                                             schedule[i]['r'][0]] + ')' + '/'
                    except KeyError:
                        week_schedule += num + '. ' + 'Занятий нет/'
                    try:
                        week_schedule += data_py['SUBJECTS'][
                                             schedule[i]['s'][1]] + '(' + data_py['ROOMS'][
                                             schedule[i]['r'][1]] + ')' + '  '
                    except KeyError:
                        week_schedule += 'Занятий нет' + '  '
                else:
                    week_schedule += num + '. ' + data_py['SUBJECTS'][schedule[i]['s'][0]] + '(' + data_py['ROOMS'][
                        schedule[i]['r'][0]] + ')' + '  '
            week_schedule += '\n'
        for i in week_schedule.split('\n'):
            days = i.split(', ')
            for j in days[1:]:
                rasp_dict[days[0]].append(j.split('  '))
        return rasp_dict


class GetArticle:
    def __init__(self, article=None):
        self.main_page = 'http://127.0.0.1:8080/'
        self.page = requests.get('http://127.0.0.1:8080/novosti/itemlist/category/1-news')
        self.page_text = re.sub(r'\n|  +|\n', '', self.page.text)
        self.page_text = re.sub(r'&quot', '"', self.page_text)
        self.num_of_article = article

    def getting_links(self):
        dt = time()
        a_elements = re.findall(r"<h3 class=\"catItemTitle\"><a[^><]*?href=['\"](/novosti/item/.*?)['\"][^><]*?>.*?</a></h3>", self.page_text, re.S)
        print('Glinks:', time() - dt)
        return a_elements[self.num_of_article]

    def getting_images_links(self):
        dt = time()
        img_elements = re.findall(r"<img.*?src=['\"](/media/k2.*?)['\"].*?/?>", self.page.text, re.S)
        print('GIMlinks:', time() - dt)
        return img_elements

    def getting_image_link(self, news_url):
        dt = time()
        # print("<a[^><]*?href=\"" + news_url + "\"[^><]*?><img.*?src=['\"](/media/k2.*?)['\"].*?/?></a>", self.page_text)
        img_elements = re.findall(r"<a[^><]*?href=\"" + news_url + "\"[^><]*?><img.*?src=['\"](/media/k2.*?)['\"].*?/?></a>", self.page_text, re.S)
        print('GIMlink:', time() - dt)
        return img_elements[0] if len(img_elements) > 0 else None

    def save_image(self):
        link = self.getting_links()
        img_link = self.getting_image_link(link)
        image = requests.get(self.main_page + img_link).content
        print(self.main_page + img_link)
        open(f'news{self.num_of_article}.jpg', 'wb').write(image)

    def getting_names(self):
        dt = time()
        a_names = re.findall(r"<h3 class=\"catItemTitle\"><a[^><]*?href=['\"]/novosti/item/.*?['\"][^><]*?>(.*?)</a></h3>", self.page_text, re.S)
        print(a_names)
        print('Gnms:', time() - dt)
        return a_names

    def getting_date(self):
        dt = time()
        span_dates = re.findall(r"<span[^><]*?class=\"\S*?catItemDateCreated\S*?\"[^><]*?>(.*?)</span>", self.page_text, re.S)
        print('Gdate:', time() - dt)
        return span_dates[0]

    def getting_text(self):
        dt = time()
        page_news = requests.get(self.main_page + self.getting_links(), verify=False)
        print('LoadPG:', time() - dt)
        page_news_text = page_news.text
        page_news_text = re.sub(r'\n|  +|\n', '', page_news_text)
        page_news_text = re.sub(r'&quot;', '"', page_news_text)
        page_news_text = re.sub(r'&nbsp;', ' ', page_news_text)
        p_texts = re.findall(r"<p>([^><]*?)</p>", page_news_text, re.S)
        print('ParsePG:', time() - dt)
        print(p_texts)
        return ' '.join(p_texts)

    def get_article(self):
        return [str(self.getting_names()[self.num_of_article]), self.getting_date(), self.getting_text()]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.resize(1600, 900)
        self.setStyleSheet("background-color: #0e2254")


class MainWidget(MainWindow):
    def __init__(self):
        super().__init__()
        self.mainwidget = QtWidgets.QWidget(self)
        self.mainwidget.setObjectName("mainwidget")


class SubMainWidget(MainWidget):
    def __init__(self):
        super().__init__()
        self.sub_mainwidget = QtWidgets.QWidget(self.mainwidget)
        self.sub_mainwidget.setObjectName("sub_mainwidget")
        self.logo_widget = QtWidgets.QWidget(self.sub_mainwidget)
        self.logo_widget.setObjectName("logo_widget")
        self.name_label = QtWidgets.QLabel(self.sub_mainwidget)
        self.name_label.setObjectName("name_label")
        self.anniversary_label = QtWidgets.QLabel(self.sub_mainwidget)

        self.class_name_label = QtWidgets.QLabel(self.sub_mainwidget)

        self.set_submainwidget_geometry()
        self.set_submainwidget_stylesheet()
        self.set_logowidget()
        self.set_namelabel()
        self.set_anniversarylabel()
        self.set_class_name_label()

        self.setCentralWidget(self.mainwidget)

        self.anniversary_label.hide()
        self.class_name_label.hide()

    def set_submainwidget_geometry(self):
        self.sub_mainwidget.setGeometry(QtCore.QRect(int(20 * 0.83), int(20 * 0.83), int(1880 * 0.83), int(1040 * 0.83)))

    def set_submainwidget_stylesheet(self):
        self.sub_mainwidget.setStyleSheet("QWidget#sub_mainwidget{\n"
                                          "    background-color: #ebecf0;\n"
                                          "    border-radius: 15px;\n"
                                          "}")

    def set_logowidget(self):
        self.logo_widget.setGeometry(QtCore.QRect(int(20 * 0.83), int(20 * 0.83), int(200 * 0.83), int(206 * 0.83)))
        self.logo_widget.setStyleSheet("QWidget#logo_widget{\n"
                                       "    background-color: transparent;\n"
                                       "    border-image: url(Logo_L.png);\n"
                                       "}")

    def set_namelabel(self):
        self.name_label.setGeometry(QtCore.QRect(int(450 * 0.83), int(40 * 0.83), int(1100 * 0.83), int(61 * 0.83)))
        self.name_label.setStyleSheet("QLabel#name_label{\n"
                                      "    background-color: transparent;\n"
                                      "    font: 32pt \"Yu Gothic UI\";\n"
                                      "    font-weight: bold;\n"
                                      "    color: #393939;\n"
                                      "}")
        self.name_label.setText(QtCore.QCoreApplication.translate("MainWindow", "МБОУ \'\'Инженерный лицей НГТУ\'\'"))

    def set_anniversarylabel(self):
        self.anniversary_label.setGeometry(int(750 * 0.83), int(100 * 0.83), int(1100 * 0.83), int(61 * 0.83))
        self.anniversary_label.setStyleSheet("background-color: transparent;\n"
                                      "    font: 32pt \"Yu Gothic UI\";\n"
                                      "    font-weight: bold;\n"
                                             "font-style: italic;"
                                      "    color: red;\n")
        self.anniversary_label.setText(QtCore.QCoreApplication.translate("MainWindow", 'Лицею 25 лет!'))

    def set_class_name_label(self):
        self.class_name_label.setGeometry(50, 400, 120, 60)
        self.class_name_label.setStyleSheet("background-color: #ebecf0;\n"
                            "    color: #0e2254;\n"
                            "    font: 30pt \"Yu Gothic UI\";\n"
                            "    font-weight: light;\n"
                            "    border-radius: 7px;\n")
        colors = ['#18233F', '#051337', '#405EAA', '#5C72AA', '#907101', '#1E2F47', '#3A1E47', '#352252']
        self.class_name_label.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(15, 10),
                                                                    color=QtGui.QColor(choice(colors))))


class CalendarWidget(SubMainWidget):
    def __init__(self):
        super().__init__()
        self.calendar_widget = QtWidgets.QWidget(self.sub_mainwidget)
        self.calendar_widget.setObjectName("calendar_widget")
        self.day_label = QtWidgets.QLabel(self.calendar_widget)
        self.day_label.setObjectName("day_label")
        self.calendarLogo_widget = QtWidgets.QWidget(self.calendar_widget)
        self.calendarLogo_widget.setObjectName("calendarLogo_widget")
        self.date_label = QtWidgets.QLabel(self.calendarLogo_widget)
        self.date_label.setObjectName("date_label")
        self.time_label = QtWidgets.QLabel(self.calendar_widget)
        self.time_label.setObjectName("time_label")

        self.set_calendarwidget_geometry()
        self.set_calendarwidget_stylesheet()
        self.set_daylabel()
        self.set_calendarlogo()
        self.set_datelabel()
        self.set_timelabel()

    def set_calendarwidget_geometry(self):
        self.calendar_widget.setGeometry(QtCore.QRect(int(1645 * 0.83), int(10 * 0.83), int(300 * 0.83), int(200 * 0.83)))

    def set_calendarwidget_stylesheet(self):
        self.calendar_widget.setStyleSheet("background-color: transparent;")

    def set_daylabel(self):
        self.day_label.setGeometry(QtCore.QRect(int(90 * 0.83), int(130 * 0.83), int(90 * 0.83), int(60 * 0.83)))
        self.day_label.setStyleSheet("QLabel#day_label{\n"
                                     "    background-color: transparent;\n"
                                     "    font: 26pt \"Manrope\";\n"
                                     "    font-weight: medium;\n"
                                     "    color: #393939;\n"
                                     "}")

    def set_calendarlogo(self):
        self.calendarLogo_widget.setGeometry(QtCore.QRect(int(20 * 0.83), int(7 * 0.83), int(200 * 0.83), int(70 * 0.83)))
        self.calendarLogo_widget.setStyleSheet("QWidget#calendarLogo_widget{\n"
                                               "    background-color: #ebecf0;\n"
                                               "    border-radius: 13px;\n"
                                               "}")
        self.calendarLogo_widget.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=27, offset=QtCore.QPoint(0, 3),
                                                color=QtGui.QColor('#1f1b3a')))

    def set_datelabel(self):
        self.date_label.setGeometry(QtCore.QRect(int(10 * 0.83), int(16 * 0.83), int(200 * 0.83), int(40 * 0.83)))
        self.date_label.setStyleSheet("QLabel#date_label{\n"
                                      "    background-color: transparent;\n"
                                      "    font: 24pt \"Manrope\";\n"
                                      "    font-weight: medium;\n"
                                      "    color: #bd7800;\n"
                                      "}")

    def set_timelabel(self):
        self.time_label.setGeometry(QtCore.QRect(int(60 * 0.83), int(70 * 0.83), int(140 * 0.83), int(81 * 0.83)))
        self.time_label.setStyleSheet("QLabel#time_label{\n"
                                      "    background-color: transparent;\n"
                                      "    font: 26pt \"Manrope\";\n"
                                      "    font-weight: medium;\n"
                                      "    color: #393939;\n"
                                      "}")


class MainButtonsWidget(SubMainWidget):
    def __init__(self):
        super().__init__()
        self.buttons_widget = QtWidgets.QWidget(self.sub_mainwidget)
        self.buttons_widget.setObjectName("buttons_widget")
        self.newsButton = QtWidgets.QPushButton(self.buttons_widget)
        self.newsButton.setObjectName("newsButton")
        self.aboutButton = QtWidgets.QPushButton(self.buttons_widget)
        self.aboutButton.setObjectName("aboutButton")
        self.activityButton = QtWidgets.QPushButton(self.buttons_widget)
        self.activityButton.setObjectName("activityButton")
        self.raspButton = QtWidgets.QPushButton(self.buttons_widget)
        self.raspButton.setObjectName("raspButton")

        self.main_buttons = [self.newsButton, self.activityButton, self.aboutButton, self.raspButton]

        self.set_buttonswidget_geometry()
        self.set_buttonswidget_stylesheet()
        self.set_newsbutton()
        self.set_aboutbutton()
        self.set_activitybutton()
        self.set_raspbutton()
        self.set_buttons_effects()

        self.aboutButton.setStyleSheet("background-color: #bbbfc8;\n"
                                       "    color: #0e2254;\n"
                                       "    font: 20pt \"Yu Gothic UI\";\n"
                                       "    font-weight: light;\n"
                                       "    border-radius: 7px;\n")

    def set_buttonswidget_geometry(self):
        self.buttons_widget.setGeometry(QtCore.QRect(int(47 * 0.83), int(860 * 0.83), int(1810 * 0.83), int(200 * 0.83)))

    def set_buttonswidget_stylesheet(self):
        self.buttons_widget.setStyleSheet("QWidget#buttons_widget{\n"
                                          "    background-color: transparent;\n"
                                          "}")

    def set_newsbutton(self):
        self.newsButton.setGeometry(QtCore.QRect(int(10 * 0.83), int(60 * 0.83), int(320 * 0.83), int(70 * 0.83)))
        self.newsButton.setStyleSheet("QPushButton#newsButton{\n"
                                      "    background-color: #ebecf0;\n"
                                      "    color: #0e2254;\n"
                                      "    font: 20pt \"Yu Gothic UI\";\n"
                                      "    font-weight: light;\n"
                                      "    border-radius: 7px;\n"
                                      "}"
                                      "QPushButton#newsButton:hover{\n"
                                      "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                      "stop:1 #bbbfc8); "
                                      "}"
                                      "QPushButton#newsButton:pressed{\n"
                                      "    background-color: #bbbfc8;"
                                      "}"
                                      )
        self.newsButton.setText(QtCore.QCoreApplication.translate("MainWindow", "Новости"))

    def set_aboutbutton(self):
        self.aboutButton.setGeometry(QtCore.QRect(int(490 * 0.83), int(60 * 0.83), int(320 * 0.83), int(70 * 0.83)))
        self.aboutButton.setStyleSheet("QPushButton#aboutButton{\n"
                                       "    background-color: #ebecf0;\n"
                                       "    color: #0e2254;\n"
                                       "    font: 20pt \"Yu Gothic UI\";\n"
                                       "    font-weight: light;\n"
                                       "    border-radius: 7px;\n"
                                       "}"
                                       "QPushButton#aboutButton:hover{\n"
                                       "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                       "stop:1 #bbbfc8); "
                                       "}"
                                       "QPushButton#aboutButton:pressed{\n"
                                       "    background-color: #bbbfc8;"
                                       "}"
                                       )
        self.aboutButton.setText(QtCore.QCoreApplication.translate("MainWindow", "О лицее"))

    def set_activitybutton(self):
        self.activityButton.setGeometry(QtCore.QRect(int(970 * 0.83), int(60 * 0.83), int(320 * 0.83), int(70 * 0.83)))
        self.activityButton.setStyleSheet("QPushButton#activityButton{\n"
                                          "    background-color: #ebecf0;\n"
                                          "    color: #0e2254;\n"
                                          "    font: 20pt \"Yu Gothic UI\";\n"
                                          "    font-weight: light;\n"
                                          "    border-radius: 7px;\n"
                                          "}"
                                          "QPushButton#activityButton:hover{\n"
                                          "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                          "stop:1 #bbbfc8); "
                                          "}"
                                          "QPushButton#activityButton:pressed{\n"
                                          "    background-color: #bbbfc8;"
                                          "}"
                                          )
        self.activityButton.setText(QtCore.QCoreApplication.translate("MainWindow", "Деятельность"))

    def set_raspbutton(self):
        self.raspButton.setGeometry(QtCore.QRect(int(1450 * 0.83), int(60 * 0.83), int(320 * 0.83), int(70 * 0.83)))
        self.raspButton.setStyleSheet("QPushButton#raspButton{\n"
                                      "    background-color: #ebecf0;\n"
                                      "    color: #0e2254;\n"
                                      "    font: 20pt \"Yu Gothic UI\";\n"
                                      "    font-weight: light;\n"
                                      "    border-radius: 7px;\n"
                                      "}"
                                      "QPushButton#raspButton:hover{\n"
                                      "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                      "stop:1 #bbbfc8); "
                                      "}"
                                      "QPushButton#raspButton:pressed{\n"
                                      "    background-color: #bbbfc8;"
                                      "}"
                                      )
        self.raspButton.setText(QtCore.QCoreApplication.translate("MainWindow", "Расписание"))

    def set_buttons_effects(self):
        for i in self.main_buttons:
            i.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=35, offset=QtCore.QPoint(15, 15),
                                                                    color=QtGui.QColor('#1f1b3a')))


class AboutWidget(SubMainWidget):
    def __init__(self):
        super().__init__()
        self.about_widget = QtWidgets.QWidget(self.sub_mainwidget)
        self.plaintext = QtWidgets.QPlainTextEdit(self.about_widget)
        self.lyceumPhoto_widget = QtWidgets.QWidget(self.about_widget)
        self.schedulePhoto_widget = QtWidgets.QWidget(self.about_widget)
        self.minobrrfPhoto_widget = QtWidgets.QWidget(self.about_widget)
        self.minobrnsoPhoto_widget = QtWidgets.QWidget(self.about_widget)
        self.ITSchoolPhoto_widget = QtWidgets.QWidget(self.about_widget)
        self.RANschoolPhoto_widget = QtWidgets.QWidget(self.about_widget)

        self.set_aboutwidget_geometry()
        self.set_aboutwidget_stylesheet()
        self.set_plaintext()
        self.set_lyceumphotowidget()
        self.set_schedulephotowidget()
        self.set_minobrrfphotowidget()
        self.set_minobrnsophotowidget()
        self.set_itschoolphotowidget()
        self.set_ranschoolphotowidget()

    def set_aboutwidget_geometry(self):
        self.about_widget.setGeometry(QtCore.QRect(int(50 * 0.83), int(200 * 0.83), int(1780 * 0.83), int(660 * 0.83)))

    def set_aboutwidget_stylesheet(self):
        self.about_widget.setStyleSheet("background-color: transparent;")

    def set_plaintext(self):
        self.plaintext.setGeometry(QtCore.QRect(int(770 * 0.83), int(5 * 0.83), int(690 * 0.83), int(270 * 0.83)))
        self.plaintext.setStyleSheet('background-color: transparent;'
                                     "font: 13pt \"Yu Gothic UI\";\n"
                                     "font-weight: light;\n"
                                     "color: #393939;\n"
                                     "border: 0;"
                                     )
        self.plaintext.setPlainText(
            QtCore.QCoreApplication.translate('MainWindow',
                                              'Муниципальное бюджетное общеобразовательное учреждение города '
                                              'Новосибирска '
                                              '"Инженерный лицей НГТУ" был открыт в августе 1996 года по инициативе '
                                              'НГТУ и '
                                              'Управления Образованием мэрии города Новосибирска. Учредитель '
                                              'образовательного '
                                              'учреждения: муниципальное образование, город Новосибирск.'))
        self.plaintext.setDisabled(True)

    def set_lyceumphotowidget(self):
        self.lyceumPhoto_widget.setGeometry(QtCore.QRect(int(250 * 0.83), int(20 * 0.83), int(422 * 0.83), int(413 * 0.83)))
        self.lyceumPhoto_widget.setStyleSheet("border-image: url(lyceum.png);"
                                              "border-radius: 13px;")
        self.lyceumPhoto_widget.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=40,
                                                                                      offset=QtCore.QPoint(15, 10),
                                                                                      color=QtGui.QColor('#1f1b3a')))

    def set_schedulephotowidget(self):
        self.schedulePhoto_widget.setGeometry(QtCore.QRect(int(775 * 0.83), int(290 * 0.83), int(540 * 0.83), int(110 * 0.83)))
        self.schedulePhoto_widget.setStyleSheet("border-image: url(schedule.png);"
                                                "border-radius: 13px;")
        self.schedulePhoto_widget.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=40,
                                                                                        offset=QtCore.QPoint(15, 10),
                                                                                        color=QtGui.QColor('#1f1b3a')))

    def set_minobrrfphotowidget(self):
        self.minobrrfPhoto_widget.setGeometry(QtCore.QRect(int(15 * 0.83), int(490 * 0.83), int(420 * 0.83), int(98 * 0.83)))
        self.minobrrfPhoto_widget.setStyleSheet("border-image: url(minobrrf.png);"
                                                "border-radius: 13px;")
        self.minobrrfPhoto_widget.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=40,
                                                                                        offset=QtCore.QPoint(15, 10),
                                                                                        color=QtGui.QColor('#1f1b3a')))

    def set_minobrnsophotowidget(self):
        self.minobrnsoPhoto_widget.setGeometry(QtCore.QRect(int(470 * 0.83), int(490 * 0.83), int(450 * 0.83), int(98 * 0.83)))
        self.minobrnsoPhoto_widget.setStyleSheet("border-image: url(minobrnso.png);"
                                                 "border-radius: 13px;")
        self.minobrnsoPhoto_widget.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=40,
                                                                                         offset=QtCore.QPoint(15, 10),
                                                                                         color=QtGui.QColor('#1f1b3a')))

    def set_itschoolphotowidget(self):
        self.ITSchoolPhoto_widget.setGeometry(QtCore.QRect(int(955 * 0.83), int(490 * 0.83), int(420 * 0.83), int(135 * 0.83)))
        self.ITSchoolPhoto_widget.setStyleSheet("border-image: url(ITSchool.png);"
                                                "border-radius: 13px;")
        self.ITSchoolPhoto_widget.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=40,
                                                                                        offset=QtCore.QPoint(int(15 * 0.83), int(10 * 0.83)),
                                                                                        color=QtGui.QColor('#1f1b3a')))

    def set_ranschoolphotowidget(self):
        self.RANschoolPhoto_widget.setGeometry(QtCore.QRect(int(1390 * 0.83), int(430 * 0.83), int(380 * 0.83), int(232 * 0.83)))
        self.RANschoolPhoto_widget.setStyleSheet("border-image: url(RANschool.png);"
                                                 "border-radius: 13px;")
        self.RANschoolPhoto_widget.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=40,
                                                                                         offset=QtCore.QPoint(int(15 * 0.83), int(10 * 0.83)),
                                                                                         color=QtGui.QColor('#1f1b3a')))



class NewsMainWidget(SubMainWidget):
    def __init__(self):
        super().__init__()
        self.news_mainwidget = QtWidgets.QWidget(self.sub_mainwidget)

        self.set_newsmainwidget_geometry()
        self.set_newsmainwidget_stylesheet()
        self.news_mainwidget.hide()

    def set_newsmainwidget_geometry(self):
        self.news_mainwidget.setGeometry(QtCore.QRect(int(200 * 0.83), int(210 * 0.83), int(1580 * 0.83), int(660 * 0.83)))

    def set_newsmainwidget_stylesheet(self):
        self.news_mainwidget.setStyleSheet("background-color: transparent;")


class News0Widget(NewsMainWidget):
    def __init__(self):
        super().__init__()
        self.news0_widget = QtWidgets.QWidget(self.news_mainwidget)
        self.news0_textedit = QtWidgets.QTextEdit(self.news0_widget)
        self.news0_photo = QtWidgets.QLabel(self.news0_widget)
        self.news0_Button = QtWidgets.QPushButton(self.news0_widget)
        self.news0_Button.setObjectName('news0_Button')

        self.set_news0widget_geometry()
        self.set_news0widget_stylesheet()
        self.set_news0textedit()
        self.set_news0photo()
        self.set_news0button()

    def set_news0widget_geometry(self):
        self.news0_widget.setGeometry(QtCore.QRect(int(10 * 0.83), int(10 * 0.83), int(380 * 0.83), int(270 * 0.83)))

    def set_news0widget_stylesheet(self):
        self.news0_widget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.news0_widget.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(0, 7),
                                                color=QtGui.QColor('#1f1b3a')))

    def set_news0textedit(self):
        self.news0_textedit.setGeometry(int(10 * 0.83), int(10 * 0.83), int(340 * 0.83), int(70 * 0.83))
        self.news0_textedit.setDisabled(True)

    def set_news0photo(self):
        self.news0_photo.setGeometry(int(80 * 0.83), int(80 * 0.83), int(200 * 0.83), int(110 * 0.83))
        photo = QtGui.QPixmap('./news0.jpg')
        self.news0_photo.setPixmap(photo)

    def set_news0button(self):
        self.news0_Button.setGeometry(int(50 * 0.83), int(210 * 0.83), int(260 * 0.83), int(30 * 0.83))
        self.news0_Button.setStyleSheet("QPushButton#news0_Button{\n"
                                        "    background-color: #ebecf0;\n"
                                        "    color: #0e2254;\n"
                                        "    font: 14pt \"Yu Gothic UI\";\n"
                                        "    font-weight: light;\n"
                                        "    border-radius: 7px;\n"
                                        "}"
                                        "QPushButton#news0_Button:hover{\n"
                                        "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                        "stop:1 #bbbfc8); "
                                        "}")
        self.news0_Button.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(7, 7),
                                                color=QtGui.QColor('#1f1b3a')))
        self.news0_Button.setText(QtCore.QCoreApplication.translate("MainWinow", "Читать"))


class News1Widget(NewsMainWidget):
    def __init__(self):
        super().__init__()
        self.news1_widget = QtWidgets.QWidget(self.news_mainwidget)
        self.news1_textedit = QtWidgets.QTextEdit(self.news1_widget)
        self.news1_photo = QtWidgets.QLabel(self.news1_widget)
        self.news1_Button = QtWidgets.QPushButton(self.news1_widget)
        self.news1_Button.setObjectName('news1_Button')

        self.set_news1widget_geometry()
        self.set_news1widget_stylesheet()
        self.set_news1textedit()
        self.set_news1photo()
        self.set_news1button()

    def set_news1widget_geometry(self):
        self.news1_widget.setGeometry(QtCore.QRect(int(565 * 0.83), int(10 * 0.83), int(380 * 0.83), int(270 * 0.83)))

    def set_news1widget_stylesheet(self):
        self.news1_widget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.news1_widget.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(0, 7),
                                                color=QtGui.QColor('#1f1b3a')))

    def set_news1textedit(self):
        self.news1_textedit.setGeometry(int(10 * 0.83), int(10 * 0.83), int(340 * 0.83), int(70 * 0.83))
        self.news1_textedit.setDisabled(True)

    def set_news1photo(self):
        self.news1_photo.setGeometry(int(80 * 0.83), int(80 * 0.83), int(200 * 0.83), int(110 * 0.83))
        photo = QtGui.QPixmap('./news1.jpg')
        self.news1_photo.setPixmap(photo)

    def set_news1button(self):
        self.news1_Button.setGeometry(int(50 * 0.83), int(210 * 0.83), int(260 * 0.83), int(30 * 0.83))
        self.news1_Button.setObjectName('news1_Button')
        self.news1_Button.setStyleSheet("QPushButton#news1_Button{\n"
                                        "    background-color: #ebecf0;\n"
                                        "    color: #0e2254;\n"
                                        "    font: 14pt \"Yu Gothic UI\";\n"
                                        "    font-weight: light;\n"
                                        "    border-radius: 7px;\n"
                                        "}"
                                        "QPushButton#news1_Button:hover{\n"
                                        "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                        "stop:1 #bbbfc8); "
                                        "}")
        self.news1_Button.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(7, 7),
                                                color=QtGui.QColor('#1f1b3a')))
        self.news1_Button.setText(QtCore.QCoreApplication.translate("MainWinow", "Читать"))


class News2Widget(NewsMainWidget):
    def __init__(self):
        super().__init__()
        self.news2_widget = QtWidgets.QWidget(self.news_mainwidget)
        self.news2_textedit = QtWidgets.QTextEdit(self.news2_widget)
        self.news2_photo = QtWidgets.QLabel(self.news2_widget)
        self.news2_Button = QtWidgets.QPushButton(self.news2_widget)
        self.news2_Button.setObjectName('news2_Button')

        self.set_news2widget_geometry()
        self.set_news2widget_stylesheet()
        self.set_news2textedit()
        self.set_news2photo()
        self.set_news2button()

    def set_news2widget_geometry(self):
        self.news2_widget.setGeometry(QtCore.QRect(int(1120 * 0.83), int(10 * 0.83), int(380 * 0.83), int(270 * 0.83)))

    def set_news2widget_stylesheet(self):
        self.news2_widget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.news2_widget.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(0, 7),
                                                color=QtGui.QColor('#1f1b3a')))

    def set_news2textedit(self):
        self.news2_textedit.setGeometry(int(10 * 0.83), int(10 * 0.83), int(340 * 0.83), int(70 * 0.83))
        self.news2_textedit.setDisabled(True)

    def set_news2photo(self):
        self.news2_photo.setGeometry(int(80 * 0.83), int(80 * 0.83), int(200 * 0.83), int(110 * 0.83))
        photo = QtGui.QPixmap('./news2.jpg')
        self.news2_photo.setPixmap(photo)

    def set_news2button(self):
        self.news2_Button.setGeometry(int(50 * 0.83), int(210 * 0.83), int(260 * 0.83), int(30 * 0.83))
        self.news2_Button.setStyleSheet("QPushButton#news2_Button{\n"
                                        "    background-color: #ebecf0;\n"
                                        "    color: #0e2254;\n"
                                        "    font: 14pt \"Yu Gothic UI\";\n"
                                        "    font-weight: light;\n"
                                        "    border-radius: 7px;\n"
                                        "}"
                                        "QPushButton#news2_Button:hover{\n"
                                        "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                        "stop:1 #bbbfc8); "
                                        "}")
        self.news2_Button.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(7, 7),
                                                color=QtGui.QColor('#1f1b3a')))
        self.news2_Button.setText(QtCore.QCoreApplication.translate("MainWinow", "Читать"))


class News3Widget(NewsMainWidget):
    def __init__(self):
        super().__init__()
        self.news3_widget = QtWidgets.QWidget(self.news_mainwidget)
        self.news3_textedit = QtWidgets.QTextEdit(self.news3_widget)
        self.news3_photo = QtWidgets.QLabel(self.news3_widget)
        self.news3_Button = QtWidgets.QPushButton(self.news3_widget)
        self.news3_Button.setObjectName('news3_Button')

        self.set_news3widget_geometry()
        self.set_news3widget_stylesheet()
        self.set_news3textedit()
        self.set_news3photo()
        self.set_news3button()

    def set_news3widget_geometry(self):
        self.news3_widget.setGeometry(QtCore.QRect(int(10 * 0.83), int(360 * 0.83), int(380 * 0.83), int(270 * 0.83)))

    def set_news3widget_stylesheet(self):
        self.news3_widget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.news3_widget.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(0, 7),
                                                color=QtGui.QColor('#1f1b3a')))

    def set_news3textedit(self):
        self.news3_textedit.setGeometry(int(10 * 0.83), int(10 * 0.83), int(340 * 0.83), int(70 * 0.83))
        self.news3_textedit.setDisabled(True)

    def set_news3photo(self):
        self.news3_photo.setGeometry(int(80 * 0.83), int(80 * 0.83), int(200 * 0.83), int(110 * 0.83))
        photo = QtGui.QPixmap('./news3.jpg')
        self.news3_photo.setPixmap(photo)

    def set_news3button(self):
        self.news3_Button.setGeometry(int(50 * 0.83), int(210 * 0.83), int(260 * 0.83), int(30 * 0.83))
        self.news3_Button.setStyleSheet("QPushButton#news3_Button{\n"
                                        "    background-color: #ebecf0;\n"
                                        "    color: #0e2254;\n"
                                        "    font: 14pt \"Yu Gothic UI\";\n"
                                        "    font-weight: light;\n"
                                        "    border-radius: 7px;\n"
                                        "}"
                                        "QPushButton#news3_Button:hover{\n"
                                        "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                        "stop:1 #bbbfc8); "
                                        "}")
        self.news3_Button.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(7, 7),
                                                color=QtGui.QColor('#1f1b3a')))
        self.news3_Button.setText(QtCore.QCoreApplication.translate("MainWinow", "Читать"))


class News4Widget(NewsMainWidget):
    def __init__(self):
        super().__init__()
        self.news4_widget = QtWidgets.QWidget(self.news_mainwidget)
        self.news4_textedit = QtWidgets.QTextEdit(self.news4_widget)
        self.news4_photo = QtWidgets.QLabel(self.news4_widget)
        self.news4_Button = QtWidgets.QPushButton(self.news4_widget)
        self.news4_Button.setObjectName('news4_Button')

        self.set_news4widget_geometry()
        self.set_news4widget_stylesheet()
        self.set_news4textedit()
        self.set_news4photo()
        self.set_news4button()

    def set_news4widget_geometry(self):
        self.news4_widget.setGeometry(QtCore.QRect(int(565 * 0.83), int(360 * 0.83), int(380 * 0.83), int(270 * 0.83)))

    def set_news4widget_stylesheet(self):
        self.news4_widget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.news4_widget.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(0, 7),
                                                color=QtGui.QColor('#1f1b3a')))

    def set_news4textedit(self):
        self.news4_textedit.setGeometry(int(10 * 0.83), int(10 * 0.83), int(340 * 0.83), int(70 * 0.83))
        self.news4_textedit.setDisabled(True)

    def set_news4photo(self):
        self.news4_photo.setGeometry(int(80 * 0.83), int(80 * 0.83), int(200 * 0.83), int(110 * 0.83))
        photo = QtGui.QPixmap('./news4.jpg')
        self.news4_photo.setPixmap(photo)

    def set_news4button(self):
        self.news4_Button.setGeometry(int(50 * 0.83), int(210 * 0.83), int(260 * 0.83), int(30 * 0.83))
        self.news4_Button.setStyleSheet("QPushButton#news4_Button{\n"
                                        "    background-color: #ebecf0;\n"
                                        "    color: #0e2254;\n"
                                        "    font: 14pt \"Yu Gothic UI\";\n"
                                        "    font-weight: light;\n"
                                        "    border-radius: 7px;\n"
                                        "}"
                                        "QPushButton#news4_Button:hover{\n"
                                        "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                        "stop:1 #bbbfc8); "
                                        "}")
        self.news4_Button.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(7, 7),
                                                color=QtGui.QColor('#1f1b3a')))
        self.news4_Button.setText(QtCore.QCoreApplication.translate("MainWinow", "Читать"))


class News5Widget(NewsMainWidget):
    def __init__(self):
        super().__init__()
        self.news5_widget = QtWidgets.QWidget(self.news_mainwidget)
        self.news5_textedit = QtWidgets.QTextEdit(self.news5_widget)
        self.news5_photo = QtWidgets.QLabel(self.news5_widget)
        self.news5_Button = QtWidgets.QPushButton(self.news5_widget)
        self.news5_Button.setObjectName('news5_Button')

        self.set_news5widget_geometry()
        self.set_news5widget_stylesheet()
        self.set_news5textedit()
        self.set_news5photo()
        self.set_news5button()

    def set_news5widget_geometry(self):
        self.news5_widget.setGeometry(QtCore.QRect(int(1120 * 0.83), int(360 * 0.83), int(380 * 0.83), int(270 * 0.83)))

    def set_news5widget_stylesheet(self):
        self.news5_widget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.news5_widget.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(0, 7),
                                                color=QtGui.QColor('#1f1b3a')))

    def set_news5textedit(self):
        self.news5_textedit.setGeometry(int(10 * 0.83), int(10 * 0.83), int(340 * 0.83), int(70 * 0.83))
        self.news5_textedit.setDisabled(True)

    def set_news5photo(self):

        self.news5_photo.setGeometry(int(80 * 0.83), int(80 * 0.83), int(200 * 0.83), int(110 * 0.83))
        photo = QtGui.QPixmap('./news5.jpg')
        print(photo, photo.width())
        self.news5_photo.setPixmap(photo)

    def set_news5button(self):
        self.news5_Button.setGeometry(int(50 * 0.83), int(210 * 0.83), int(260 * 0.83), int(30 * 0.83))
        self.news5_Button.setStyleSheet("QPushButton#news5_Button{\n"
                                        "    background-color: #ebecf0;\n"
                                        "    color: #0e2254;\n"
                                        "    font: 14pt \"Yu Gothic UI\";\n"
                                        "    font-weight: light;\n"
                                        "    border-radius: 7px;\n"
                                        "}"
                                        "QPushButton#news5_Button:hover{\n"
                                        "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                        "stop:1 #bbbfc8); "
                                        "}")
        self.news5_Button.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(7, 7),
                                                color=QtGui.QColor('#1f1b3a')))
        self.news5_Button.setText(QtCore.QCoreApplication.translate("MainWinow", "Читать"))


class NewsOpenWidget(SubMainWidget):
    def __init__(self):
        super().__init__()
        self.NEWS_Widget = QtWidgets.QWidget(self.sub_mainwidget)
        self.NEWS_heading = QtWidgets.QTextEdit(self.NEWS_Widget)
        self.NEWS_date = QtWidgets.QTextEdit(self.NEWS_Widget)
        self.NEWS_text = QtWidgets.QTextEdit(self.NEWS_Widget)
        self.NEWS_backButton = QtWidgets.QPushButton(self.NEWS_Widget)
        self.NEWS_backButton.setObjectName('NEWS_backButton')
        self.vsb_text = QtWidgets.QScrollBar()
        self.vsb_heading = QtWidgets.QScrollBar()

        self.set_newswidget_geometry()
        self.set_newswidget_stylesheet()
        self.set_newsheading()
        self.set_newsdate()
        self.set_newstext()
        self.set_newsbackbutton()
        self.set_vsbtext()
        self.set_vsbheading()
        self.NEWS_Widget.hide()

    def set_newswidget_geometry(self):
        self.NEWS_Widget.setGeometry(QtCore.QRect(0, int(210 * 0.83), int(1680 * 0.83), int(800 * 0.83)))

    def set_newswidget_stylesheet(self):
        self.NEWS_Widget.setStyleSheet("background-color: transparent;")

    def set_newsheading(self):
        self.NEWS_heading.setGeometry(int(220 * 0.83), int(10 * 0.83), int(1460 * 0.83), int(150 * 0.83))
        self.NEWS_heading.setStyleSheet("background-color: #ebecf0;\n"
                                        "    color: #0e2254;\n"
                                        "    font: 26pt \"Yu Gothic UI\";\n"
                                        "    font-weight: bold;\n"
                                        "    border-radius: 7px;\n")
        self.NEWS_heading.setReadOnly(True)

    def set_newsdate(self):
        self.NEWS_date.setGeometry(int(1170 * 0.83), int(710 * 0.83), int(480 * 0.83), int(50 * 0.83))
        self.NEWS_date.setStyleSheet("background-color: #ebecf0;\n"
                                     "    color: #0e2254;\n"
                                     "    font: 14pt \"Yu Gothic UI\";\n"
                                     "    font-weight: light;\n"
                                     "    border-radius: 7px;\n")
        self.NEWS_date.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(10, 10),
                                                color=QtGui.QColor('#1f1b3a')))
        self.NEWS_date.setDisabled(True)

    def set_newstext(self):
        self.NEWS_text.setGeometry(int(220 * 0.83), int(160 * 0.83), int(1460 * 0.83), int(540 * 0.83))
        self.NEWS_text.setStyleSheet("background-color: rgba(187, 191, 200, 90);\n"
                                     "    color: #393939;\n"
                                     "    font: 16pt \"Yu Gothic UI\";\n"
                                     "    font-weight: light;\n"
                                     "    border-radius: 7px;\n")
        self.NEWS_text.setReadOnly(True)

    def set_newsbackbutton(self):
        self.NEWS_backButton.setGeometry(int(220 * 0.83), int(710 * 0.83), int(140 * 0.83), int(50 * 0.83))
        self.NEWS_backButton.setStyleSheet("QPushButton#NEWS_backButton{\n"
                                           "    background-color: #ebecf0;\n"
                                           "    color: #0e2254;\n"
                                           "    font: 20pt \"Yu Gothic UI\";\n"
                                           "    font-weight: light;\n"
                                           "    border-radius: 7px;\n"
                                           "}"
                                           "QPushButton#NEWS_backButton:hover{\n"
                                           "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                           "stop:1 #bbbfc8); "
                                           "}")
        self.NEWS_backButton.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(7, 7),
                                                color=QtGui.QColor('#1f1b3a')))
        self.NEWS_backButton.setText(QtCore.QCoreApplication.translate("MainWindow", "Назад"))

    def set_vsbtext(self):
        self.vsb_text.setStyleSheet('QScrollBar:vertical {'
                                    'background-color: #ebecf0;'
                                    ' }'
                                    'QScrollBar::handle:vertical {'
                                    'background-color: #0e2254;'
                                    'min-height: 10px;'
                                    '}')
        self.NEWS_text.setVerticalScrollBar(self.vsb_text)
        self.vsb_text.setEnabled(True)

    def set_vsbheading(self):
        self.vsb_heading.setStyleSheet('QScrollBar:vertical {'
                                       'background-color: #ebecf0;'
                                       ' }'
                                       'QScrollBar::handle:vertical {'
                                       'background-color: #0e2254;'
                                       'min-height: 10px;'
                                       '}')
        self.NEWS_heading.setVerticalScrollBar(self.vsb_heading)
        self.vsb_heading.setEnabled(True)


class RaspMainWidget(SubMainWidget):
    def __init__(self):
        super().__init__()
        self.RaspMainWidget = QtWidgets.QWidget(self.sub_mainwidget)
        self.previousWeekButton = QtWidgets.QPushButton(self.RaspMainWidget)
        self.currentWeekButton = QtWidgets.QPushButton(self.RaspMainWidget)
        self.futureWeekButton = QtWidgets.QPushButton(self.RaspMainWidget)
        self.li_buttons = [self.futureWeekButton, self.currentWeekButton, self.previousWeekButton]

        self.set_futureweekbutton()
        self.set_previousweekbutton()
        self.set_currentweekbutton()
        self.set_raspmainwidget_geometry()
        self.set_raspmainwidget_stylesheet()
        self.set_buttonsgraphic_effects()

        self.PREVIOUS_FLAG = False
        self.FUTURE_FLAG = False
        self.CURRENT_FLAG = False

        self.RaspMainWidget.hide()

    def set_raspmainwidget_geometry(self):
        self.RaspMainWidget.setGeometry(QtCore.QRect(int(50 * 0.83), int(200 * 0.83), int(1780 * 0.83), int(660 * 0.83)))

    def set_raspmainwidget_stylesheet(self):
        self.RaspMainWidget.setStyleSheet("background-color: transparent;")

    def set_previousweekbutton(self):
        self.previousWeekButton.setStyleSheet("background-color: #bbbfc8;\n"
                                              "    color: #0e2254;\n"
                                              "    font: 20pt \"Yu Gothic UI\";\n"
                                              "    font-weight: light;\n"
                                              "    border-radius: 7px;\n")
        self.previousWeekButton.setGeometry(int(145 * 0.83), int(130 * 0.83), int(400 * 0.83), int(400 * 0.83))
        self.previousWeekButton.setText(QtCore.QCoreApplication.translate("MainWinow", "Предыдущая неделя"))

    def set_currentweekbutton(self):
        self.currentWeekButton.setStyleSheet("background-color: #bbbfc8;\n"
                                             "    color: #0e2254;\n"
                                             "    font: 20pt \"Yu Gothic UI\";\n"
                                             "    font-weight: light;\n"
                                             "    border-radius: 7px;\n")
        self.currentWeekButton.setGeometry(int(690 * 0.83), int(130 * 0.83), int(400 * 0.83), int(400 * 0.83))
        self.currentWeekButton.setText(QtCore.QCoreApplication.translate("MainWinow", "Текущая неделя"))

    def set_futureweekbutton(self):
        self.futureWeekButton.setStyleSheet("background-color: #bbbfc8;\n"
                                            "    color: #0e2254;\n"
                                            "    font: 20pt \"Yu Gothic UI\";\n"
                                            "    font-weight: light;\n"
                                            "    border-radius: 7px;\n")
        self.futureWeekButton.setGeometry(int(1235 * 0.83), int(130 * 0.83), int(400 * 0.83), int(400 * 0.83))
        self.futureWeekButton.setText(QtCore.QCoreApplication.translate("MainWinow", "Следующая неделя"))

    def set_buttonsgraphic_effects(self):
        for i in self.li_buttons:
            i.setGraphicsEffect(
                QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(10, 10),
                                                    color=QtGui.QColor('#1f1b3a')))


class RaspWidget(SubMainWidget):
    def __init__(self):
        super().__init__()
        self.rasp_widget = QtWidgets.QWidget(self.sub_mainwidget)

        self.a1 = QtWidgets.QPushButton(self.rasp_widget)
        self.a2 = QtWidgets.QPushButton(self.rasp_widget)
        self.a3 = QtWidgets.QPushButton(self.rasp_widget)
        self.a4 = QtWidgets.QPushButton(self.rasp_widget)
        self.a5 = QtWidgets.QPushButton(self.rasp_widget)
        self.a6 = QtWidgets.QPushButton(self.rasp_widget)
        self.a7 = QtWidgets.QPushButton(self.rasp_widget)
        self.a8 = QtWidgets.QPushButton(self.rasp_widget)
        self.a9 = QtWidgets.QPushButton(self.rasp_widget)

        self.b1 = QtWidgets.QPushButton(self.rasp_widget)
        self.b2 = QtWidgets.QPushButton(self.rasp_widget)
        self.b3 = QtWidgets.QPushButton(self.rasp_widget)
        self.b4 = QtWidgets.QPushButton(self.rasp_widget)
        self.b5 = QtWidgets.QPushButton(self.rasp_widget)
        self.b6 = QtWidgets.QPushButton(self.rasp_widget)
        self.b7 = QtWidgets.QPushButton(self.rasp_widget)
        self.b8 = QtWidgets.QPushButton(self.rasp_widget)
        self.b9 = QtWidgets.QPushButton(self.rasp_widget)

        self.v1 = QtWidgets.QPushButton(self.rasp_widget)
        self.v2 = QtWidgets.QPushButton(self.rasp_widget)
        self.v3 = QtWidgets.QPushButton(self.rasp_widget)
        self.v5 = QtWidgets.QPushButton(self.rasp_widget)
        self.v6 = QtWidgets.QPushButton(self.rasp_widget)
        self.v7 = QtWidgets.QPushButton(self.rasp_widget)
        self.v8 = QtWidgets.QPushButton(self.rasp_widget)
        self.v9 = QtWidgets.QPushButton(self.rasp_widget)

        self.g8 = QtWidgets.QPushButton(self.rasp_widget)

        self.L10_1 = QtWidgets.QPushButton(self.rasp_widget)
        self.L10_2 = QtWidgets.QPushButton(self.rasp_widget)
        self.L10_3 = QtWidgets.QPushButton(self.rasp_widget)
        self.L10_4 = QtWidgets.QPushButton(self.rasp_widget)

        self.L11_1 = QtWidgets.QPushButton(self.rasp_widget)
        self.L11_2 = QtWidgets.QPushButton(self.rasp_widget)
        self.L11_3 = QtWidgets.QPushButton(self.rasp_widget)
        self.L11_4 = QtWidgets.QPushButton(self.rasp_widget)

        self.raspBackButton_classes = QtWidgets.QPushButton(self.rasp_widget)
        self.raspBackButton_classes.setObjectName('raspBackButton_classes')

        self.colors = ['#ff00ff', '#00ff00', '#808000', '#00ffff']

        self.rasp = GetRasp.getrasp()

        self.li_ALLbuttons = [self.a1, self.a2, self.a3, self.a4, self.a5, self.a6, self.a7, self.a8, self.a9, self.b1,
                              self.b2, self.b3, self.b4, self.b5, self.b6, self.b7, self.b8, self.b9, self.v1, self.v2,
                              self.v3, self.v5, self.v6, self.v7, self.v8, self.v9, self.g8, self.L10_1, self.L10_2,
                              self.L10_3, self.L10_4, self.L11_1, self.L11_2, self.L11_3, self.L11_4]

        self.li_FIRSTline = [self.a1, self.a2, self.a3, self.a4, self.a5, self.a6, self.a7, self.a8, self.a9,
                             self.L10_1, self.L11_1]
        self.li_SECONDline = [self.b1, self.b2, self.b3, self.b4, self.b5, self.b6, self.b7, self.b8, self.b9,
                              self.L10_2, self.L11_2]
        self.li_THIRDline = [self.v1, self.v2, self.v3, self.v5, self.v6, self.v7, self.v8, self.v9, self.L10_3,
                             self.L11_3]
        self.li_FOURTHline = [self.g8, self.L10_4, self.L11_4]

        self.set_raspwidget_geometry()
        self.set_raspwidget_stylesheet()
        self.set_buttons_stylesheet()
        self.set_buttons_geometry()
        self.set_rasp_buttons_effects()
        self.set_buttons_name()
        self.set_raspbackbutton_classes()

        self.rasp_widget.hide()

    def set_raspwidget_geometry(self):
        self.rasp_widget.setGeometry(QtCore.QRect(int(200 * 0.83), int(210 * 0.83), int(1580 * 0.83), int(660 * 0.83)))

    def set_raspwidget_stylesheet(self):
        self.rasp_widget.setStyleSheet("background-color: transparent;")

    def set_buttons_stylesheet(self):
        for i in self.li_ALLbuttons:
            i.setStyleSheet("background-color: #ebecf0;\n"
                            "    color: #0e2254;\n"
                            "    font: 20pt \"Yu Gothic UI\";\n"
                            "    font-weight: light;\n"
                            "    border-radius: 7px;\n")

    def set_buttons_geometry(self):
        x = int(5 * 0.83)
        y = int(150 * 0.83)
        for i in self.li_FIRSTline:
            i.setGeometry(x, y, int(100 * 0.83), int(60 * 0.83))
            x += int((10 + 90 + 40) * 0.83)
        x = int(5 * 0.83)
        for i in self.li_SECONDline:
            i.setGeometry(x, y + 65, int(100 * 0.83), int(60 * 0.83))
            x += int((10 + 90 + 40) * 0.83)
        x = int(5 * 0.83)
        for i in self.li_THIRDline[:3]:
            i.setGeometry(x, int((y + 180) * 0.83), int(100 * 0.83), int(60 * 0.83))
            x += int((10 + 90 + 40) * 0.83)
        for i in self.li_THIRDline[3:]:
            x += int((10 + 90 + 40) * 0.83)
            i.setGeometry(x, int((y + 180) * 0.83), int(100 * 0.83), int(60 * 0.83))
        x = 140
        self.L11_4.setGeometry(int((10 * x + 5) * 0.83), int((y + 260) * 0.83), int(100 * 0.83), int(60 * 0.83))
        self.L10_4.setGeometry(int((9 * x + 5) * 0.83), int((y + 260) * 0.83), int(100 * 0.83), int(60 * 0.83))
        self.g8.setGeometry(int((x * 7 + 5) * 0.83), int((y + 260) * 0.83), int(100 * 0.83), int(60 * 0.83))

    def set_rasp_buttons_effects(self):
        colors = ['#18233F', '#051337', '#405EAA', '#5C72AA', '#907101', '#1E2F47', '#3A1E47', '#352252']
        for i in self.li_ALLbuttons:
            i.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(15, 10),
                                                                    color=QtGui.QColor(choice(colors))))

    def set_buttons_name(self):
        for i in range(len(self.li_FIRSTline) - 2):
            self.li_FIRSTline[i].setText(QtCore.QCoreApplication.translate("MainWindow", "{}А".format(i + 1)))
        for i in range(len(self.li_SECONDline) - 2):
            self.li_SECONDline[i].setText(QtCore.QCoreApplication.translate("MainWindow", "{}Б".format(i + 1)))
        for i in range(len(self.li_THIRDline[:3])):
            self.li_THIRDline[i].setText(QtCore.QCoreApplication.translate("MainWindow", "{}В".format(i + 1)))
        for i in range(len(self.li_THIRDline[3:]) - 2):
            self.li_THIRDline[i + 3].setText(QtCore.QCoreApplication.translate("MainWindow", "{}В".format(i + 5)))
        for i in range(len(self.li_FIRSTline[9:])):
            self.li_FIRSTline[i + 9].setText(QtCore.QCoreApplication.translate("MainWindow", "{}-1".format(i + 10)))
        for i in range(len(self.li_SECONDline[9:])):
            self.li_SECONDline[i + 9].setText(QtCore.QCoreApplication.translate("MainWindow", "{}-2".format(i + 10)))
        for i in range(len(self.li_THIRDline[8:])):
            self.li_THIRDline[i + 8].setText(QtCore.QCoreApplication.translate("MainWindow", "{}-3".format(i + 10)))
        self.g8.setText(QtCore.QCoreApplication.translate("MainWindow", "8Г"))
        self.L10_4.setText(QtCore.QCoreApplication.translate("MainWindow", "10-4"))
        self.L11_4.setText(QtCore.QCoreApplication.translate("MainWindow", "11-4"))

    def set_raspbackbutton_classes(self):
        self.raspBackButton_classes.setGeometry(int(40 * 0.83), int(500 * 0.83), int(200 * 0.83), int(60 * 0.83))
        self.raspBackButton_classes.setStyleSheet("QPushButton#raspBackButton_classes{\n"
                                                  "    background-color: #ebecf0;\n"
                                                  "    color: #0e2254;\n"
                                                  "    font: 24pt \"Yu Gothic UI\";\n"
                                                  "    font-weight: light;\n"
                                                  "    border-radius: 7px;\n"
                                                  "}"
                                                  "QPushButton#raspBackButton_classes:hover{\n"
                                                  "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 "
                                                  "#f8f8f8, "
                                                  "stop:1 #bbbfc8); "
                                                  "}")
        self.raspBackButton_classes.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(7, 7),
                                                color=QtGui.QColor('#1f1b3a')))
        self.raspBackButton_classes.setText(QtCore.QCoreApplication.translate("MainWindow", "Назад"))


class RaspOpenWidget(SubMainWidget):
    def __init__(self):
        super().__init__()
        self.raspOpenWidget = QtWidgets.QWidget(self.sub_mainwidget)

        self.mondayWidget = QtWidgets.QWidget(self.raspOpenWidget)
        self.tuesdayWidget = QtWidgets.QWidget(self.raspOpenWidget)
        self.wednesdayWidget = QtWidgets.QWidget(self.raspOpenWidget)
        self.thursdayWidget = QtWidgets.QWidget(self.raspOpenWidget)
        self.fridayWidget = QtWidgets.QWidget(self.raspOpenWidget)
        self.saturdayWidget = QtWidgets.QWidget(self.raspOpenWidget)

        self.mondayLabel = QtWidgets.QLabel(self.mondayWidget)
        self.tuesdayLabel = QtWidgets.QLabel(self.tuesdayWidget)
        self.wednesdayLabel = QtWidgets.QLabel(self.wednesdayWidget)
        self.thursdayLabel = QtWidgets.QLabel(self.thursdayWidget)
        self.fridayLabel = QtWidgets.QLabel(self.fridayWidget)
        self.sataurdayLabel = QtWidgets.QLabel(self.saturdayWidget)

        self.mondayTextEdit = QtWidgets.QTextEdit(self.mondayWidget)
        self.tuesdayTextEdit = QtWidgets.QTextEdit(self.tuesdayWidget)
        self.wednesdayTextEdit = QtWidgets.QTextEdit(self.wednesdayWidget)
        self.thursdayTextEdit = QtWidgets.QTextEdit(self.thursdayWidget)
        self.fridayTextEdit = QtWidgets.QTextEdit(self.fridayWidget)
        self.saturdayTextEdit = QtWidgets.QTextEdit(self.saturdayWidget)

        self.raspBackButton = QtWidgets.QPushButton(self.raspOpenWidget)
        self.raspBackButton.setObjectName('raspBackButton')

        self.li_daysLabels = [self.mondayLabel, self.tuesdayLabel, self.wednesdayLabel, self.thursdayLabel,
                              self.fridayLabel, self.sataurdayLabel]
        self.li_daysTexts = [self.mondayTextEdit, self.tuesdayTextEdit, self.wednesdayTextEdit, self.thursdayTextEdit,
                             self.fridayTextEdit, self.saturdayTextEdit]
        self.li_daysWidgets = [self.mondayWidget, self.tuesdayWidget, self.wednesdayWidget, self.thursdayWidget,
                               self.fridayWidget, self.saturdayWidget]
        self.days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

        self.set_raspopenwidget_geometry()
        self.set_dayswidgets_geometry()
        self.set_daystextedit_geometry()
        self.set_dayslabels_geometry()
        self.set_raspopenwidget_stylesheet()
        self.set_dayswidgets_stylesheet()
        self.set_dayslabels_stylesheet()
        self.set_raspbackbutton()
        self.set_daystextedit_stylesheet()
        self.set_dayswidgets_effects()
        self.set_dayslabels_text()

        self.raspOpenWidget.hide()

    def set_raspopenwidget_geometry(self):
        self.raspOpenWidget.setGeometry(QtCore.QRect(int(210 * 0.83), int(100 * 0.83), int(1680 * 0.83), int(900 * 0.83)))

    def set_dayswidgets_geometry(self):
        self.mondayWidget.setGeometry(QtCore.QRect(int(40 * 0.83), int(20 * 0.83), int(450 * 0.83), int(370 * 0.83)))
        self.tuesdayWidget.setGeometry(QtCore.QRect(int(520 * 0.83), int(20 * 0.83), int(450 * 0.83), int(370 * 0.83)))
        self.wednesdayWidget.setGeometry(QtCore.QRect(int(1000 * 0.83), int(20 * 0.83), int(450 * 0.83), int(370 * 0.83)))
        self.thursdayWidget.setGeometry(QtCore.QRect(int(40 * 0.83), int(410 * 0.83), int(450 * 0.83), int(370 * 0.83)))
        self.fridayWidget.setGeometry(QtCore.QRect(int(520 * 0.83), int(410 * 0.83), int(450 * 0.83), int(370 * 0.83)))
        self.saturdayWidget.setGeometry(QtCore.QRect(int(1000 * 0.83), int(410 * 0.83), int(450 * 0.83), int(370 * 0.83)))

    def set_dayslabels_geometry(self):
        self.mondayLabel.setGeometry(QtCore.QRect(int(10 * 0.83), 0, int(250 * 0.83), int(40 * 0.83)))
        self.tuesdayLabel.setGeometry(QtCore.QRect(int(10 * 0.83), 0, int(150 * 0.83), int(40 * 0.83)))
        self.wednesdayLabel.setGeometry(QtCore.QRect(int(10 * 0.83), 0, int(150 * 0.83), int(40 * 0.83)))
        self.thursdayLabel.setGeometry(QtCore.QRect(int(10 * 0.83), 0, int(150 * 0.83), int(40 * 0.83)))
        self.fridayLabel.setGeometry(QtCore.QRect(int(10 * 0.83), 0, int(150 * 0.83), int(40 * 0.83)))
        self.sataurdayLabel.setGeometry(QtCore.QRect(int(10 * 0.83), 0, int(150 * 0.83), int(40 * 0.83)))

    def set_daystextedit_geometry(self):
        self.mondayTextEdit.setGeometry(int(10 * 0.83), int(50 * 0.83), int(430 * 0.83), int(310 * 0.83))
        self.tuesdayTextEdit.setGeometry(int(10 * 0.83), int(50 * 0.83), int(430 * 0.83), int(310 * 0.83))
        self.wednesdayTextEdit.setGeometry(int(10 * 0.83), int(50 * 0.83), int(430 * 0.83), int(310 * 0.83))
        self.thursdayTextEdit.setGeometry(int(10 * 0.83), int(50 * 0.83), int(430 * 0.83), int(310 * 0.83))
        self.fridayTextEdit.setGeometry(int(10 * 0.83), int(50 * 0.83), int(430 * 0.83), int(310 * 0.83))
        self.saturdayTextEdit.setGeometry(int(10 * 0.83), int(50 * 0.83), int(430 * 0.83), int(310 * 0.83))

        self.mondayTextEdit.setDisabled(True)
        self.tuesdayTextEdit.setDisabled(True)
        self.wednesdayTextEdit.setDisabled(True)
        self.thursdayTextEdit.setDisabled(True)
        self.fridayTextEdit.setDisabled(True)
        self.saturdayTextEdit.setDisabled(True)

    def set_daystextedit_stylesheet(self):
        for i in self.li_daysTexts:
            i.setStyleSheet("background-color: rgba(187, 191, 200, 90);\n"
                            "    color: #443e58;\n"
                            "    font: 12pt \"Yu Gothic UI\";\n"
                            "    font-weight: light;\n"
                            "    border-radius: 7px;\n")

    def set_dayslabels_stylesheet(self):
        for i in self.li_daysLabels:
            i.setStyleSheet("background-color: transparent;\n"
                            "    color: #699b7f;\n"
                            "    font: 18pt \"Yu Gothic UI\";\n"
                            "    font-weight: light;\n"
                            "    border-radius: 7px;\n")

    def set_dayslabels_text(self):
        for i in range(len(self.li_daysLabels)):
            self.li_daysLabels[i].setText(self.days[i])
            '''self.li_daysLabels[i].setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(10, 10),
                                                                    color=QtGui.QColor('#699b7f')))'''

    def set_raspopenwidget_stylesheet(self):
        self.raspOpenWidget.setStyleSheet("background-color: transparent;")

    def set_dayswidgets_stylesheet(self):
        '''self.mondayWidget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.tuesdayWidget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.wednesdayWidget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.thursdayWidget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.fridayWidget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")
        self.saturdayWidget.setStyleSheet("background-color: rgba(187, 191, 200, 90);")'''

    def set_raspbackbutton(self):
        self.raspBackButton.setGeometry(int(40 * 0.83), int(800 * 0.83), int(200 * 0.83), int(60 * 0.83))
        self.raspBackButton.setStyleSheet("QPushButton#raspBackButton{\n"
                                          "    background-color: #ebecf0;\n"
                                          "    color: #0e2254;\n"
                                          "    font: 24pt \"Yu Gothic UI\";\n"
                                          "    font-weight: light;\n"
                                          "    border-radius: 7px;\n"
                                          "}"
                                          "QPushButton#raspBackButton:hover{\n"
                                          "background-color: qlineargradient( x1:1 y1:0, x2:1 y2:1, stop:0 #f8f8f8, "
                                          "stop:1 #bbbfc8); "
                                          "}")
        self.raspBackButton.setGraphicsEffect(
            QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(7, 7),
                                                color=QtGui.QColor('#1f1b3a')))
        self.raspBackButton.setText(QtCore.QCoreApplication.translate("MainWindow", "Назад"))

    def set_dayswidgets_effects(self):
        colors = ['#18233F', '#051337', '#405EAA', '#5C72AA', '#907101', '#1E2F47', '#3A1E47', '#352252']
        for i in self.li_daysWidgets:
            i.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=30, offset=QtCore.QPoint(0, 0),
                                                                    color=QtGui.QColor('#fbfac1')))


class Logic(CalendarWidget, News0Widget, News1Widget, News2Widget, News3Widget, News4Widget, News5Widget, AboutWidget,
            NewsOpenWidget, MainButtonsWidget, RaspWidget, RaspOpenWidget, RaspMainWidget):
    def __init__(self):
        self.update_data()
        super().__init__()
        self.digital_clock()
        self.NEWS_backButton.clicked.connect(self.backbutton_clicked)
        self.raspBackButton.clicked.connect(self.raspbackbutton_clicked)
        self.raspBackButton_classes.clicked.connect(self.raspbackbutton_classes_clicked)
        self.news_texts = [self.news0_textedit, self.news1_textedit, self.news2_textedit,
                           self.news3_textedit, self.news4_textedit, self.news5_textedit]
        self.main_buttons = [self.newsButton, self.activityButton, self.aboutButton, self.raspButton]
        self.news_buttons = [self.news0_Button, self.news1_Button, self.news2_Button,
                             self.news3_Button, self.news4_Button, self.news5_Button]
        for i in self.news_buttons:
            i.clicked.connect(self.news_buttonclicked)
        for i in self.main_buttons:
            i.clicked.connect(self.main_buttonclicked)
        for i in self.li_ALLbuttons:
            i.clicked.connect(self.raspbuttonsclicked)
        self.set_start_settings()
        for i in self.li_buttons:
            i.clicked.connect(self.week_buttons_clicked)

    def digital_clock(self):
        days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
        time_live = datetime.datetime.today().strftime("%H:%M")
        date_live = datetime.datetime.today().strftime("%d.%m.%y")
        day_live = datetime.datetime.today().weekday()
        self.time_label.setText(QtCore.QCoreApplication.translate("MainWindow", time_live))
        self.date_label.setText(QtCore.QCoreApplication.translate("MainWindow", date_live))
        self.day_label.setText(QtCore.QCoreApplication.translate("MainWindow", days[day_live]))
        QtCore.QTimer.singleShot(200, self.digital_clock)

    def main_buttonclicked(self):
        sender = self.sender()
        self.set_raspbutton()
        self.set_aboutbutton()
        self.set_activitybutton()
        self.set_newsbutton()
        sender.setStyleSheet("background-color: #bbbfc8;\n"
                             "    color: #0e2254;\n"
                             "    font: 20pt \"Yu Gothic UI\";\n"
                             "    font-weight: light;\n"
                             "    border-radius: 7px;\n")

        if sender == self.aboutButton:
            self.anniversary_label.show()
            self.raspButton.setEnabled(True)
            self.news_mainwidget.hide()
            self.raspOpenWidget.hide()
            self.rasp_widget.hide()
            self.RaspMainWidget.hide()
            self.class_name_label.hide()
            self.about_widget.show()
        elif sender == self.newsButton:
            self.class_name_label.hide()
            self.raspButton.setEnabled(True)
            self.raspOpenWidget.hide()
            self.about_widget.hide()
            self.RaspMainWidget.hide()
            self.setting_news_names()
            self.rasp_widget.hide()
            self.news_mainwidget.show()
        elif sender == self.activityButton:
            self.class_name_label.hide()
            self.raspButton.setEnabled(True)
            self.raspOpenWidget.hide()
            self.about_widget.hide()
            self.RaspMainWidget.hide()
            self.news_mainwidget.hide()
            self.rasp_widget.hide()
        elif sender == self.raspButton:
            self.anniversary_label.hide()
            self.about_widget.hide()
            self.news_mainwidget.hide()
            self.set_rasp_buttons_effects()
            self.RaspMainWidget.show()

    def news_buttonclicked(self):
        sender = self.sender()
        if sender == self.news0_Button:
            self.buttons_widget.hide()
            self.news_mainwidget.hide()
            text = GetArticle(0).get_article()
            self.NEWS_heading.setText(str(text[0]))
            self.NEWS_date.setText(str(text[1]))
            self.NEWS_text.setText(''.join(text[2]))
            self.NEWS_Widget.show()
        elif sender == self.news1_Button:
            self.buttons_widget.hide()
            self.news_mainwidget.hide()
            text = GetArticle(1).get_article()
            self.NEWS_heading.setText(str(text[0]))
            self.NEWS_date.setText(str(text[1]))
            self.NEWS_text.setText(''.join(text[2]))
            self.NEWS_Widget.show()
        elif sender == self.news2_Button:
            self.buttons_widget.hide()
            self.news_mainwidget.hide()
            text = GetArticle(2).get_article()
            self.NEWS_heading.setText(str(text[0]))
            self.NEWS_date.setText(str(text[1]))
            self.NEWS_text.setText(''.join(text[2]))
            self.NEWS_Widget.show()
        elif sender == self.news3_Button:
            self.buttons_widget.hide()
            self.news_mainwidget.hide()
            text = GetArticle(3).get_article()
            self.NEWS_heading.setText(str(text[0]))
            self.NEWS_date.setText(str(text[1]))
            self.NEWS_text.setText(''.join(text[2]))
            self.NEWS_Widget.show()
        elif sender == self.news4_Button:
            self.buttons_widget.hide()
            self.news_mainwidget.hide()
            text = GetArticle(4).get_article()
            self.NEWS_heading.setText(str(text[0]))
            self.NEWS_date.setText(str(text[1]))
            self.NEWS_text.setText(''.join(text[2]))
            self.NEWS_Widget.show()
        elif sender == self.news5_Button:
            self.buttons_widget.hide()
            self.news_mainwidget.hide()
            text = GetArticle(5).get_article()
            self.NEWS_heading.setText(str(text[0]))
            self.NEWS_date.setText(str(text[1]))
            self.NEWS_text.setText(''.join(text[2]))
            self.NEWS_Widget.show()

    def setting_news_names(self):
        li_names = GetArticle(1).getting_names()
        for i in range(len(self.news_texts)):
            text = li_names[i]
            if len(' '.join(text.split())) > 40:
                self.news_texts[i].setText(str(text[:40]) + '...')
            else:
                self.news_texts[i].setText(text)

    def backbutton_clicked(self):
        self.NEWS_Widget.hide()
        self.news_mainwidget.show()
        self.buttons_widget.show()

    def week_buttons_clicked(self):
        self.raspButton.setDisabled(True)
        sender = self.sender()
        if sender == self.previousWeekButton:
            self.PREVIOUS_FLAG = True
        elif sender == self.futureWeekButton:
            self.FUTURE_FLAG = True
        else:
            self.CURRENT_FLAG = True
        self.RaspMainWidget.hide()
        self.buttons_widget.show()
        self.rasp_widget.show()

    def raspbuttonsclicked(self):
        self.class_name_label.show()
        self.rasp_widget.hide()
        self.buttons_widget.hide()
        sender = self.sender()
        group = sender.text()
        if len(group) > 2:
            self.class_name_label.setText(QtCore.QCoreApplication.translate("MainWindow", ' ' + group))
        else:
            self.class_name_label.setText(QtCore.QCoreApplication.translate("MainWindow", '  ' + group))
        if '-' in group:
            pass
        else:
            group = group[0] + group[1].lower()
        if self.FUTURE_FLAG:
            rasp = GetRasp.get_previousrasp(WriteDB().get_next())[group]
        elif self.PREVIOUS_FLAG:
            rasp = GetRasp.get_previousrasp(WriteDB().get_prev())[group]
        else:
            rasp = GetRasp.getrasp()[group]
        for i in range(len(self.li_daysTexts)):
            try:
                self.li_daysTexts[i].setText('\n'.join(rasp[i][1:-1]))
            except IndexError:
                self.li_daysTexts[i].setText('\n'.join(['Нет занятий' for _ in range(6)]))
        self.set_dayswidgets_effects()
        self.raspOpenWidget.show()

    def raspbackbutton_clicked(self):
        self.raspOpenWidget.hide()
        self.buttons_widget.show()
        self.rasp_widget.show()
        self.class_name_label.hide()

    def raspbackbutton_classes_clicked(self):
        self.rasp_widget.hide()
        self.RaspMainWidget.show()
        self.buttons_widget.show()
        self.raspButton.setEnabled(True)
        self.class_name_label.hide()

        self.PREVIOUS_FLAG = False
        self.FUTURE_FLAG = False
        self.CURRENT_FLAG = False

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def set_start_settings(self):
        for i in self.news_texts:
            i.setStyleSheet('background-color: transparent;'
                            "font: 11pt \"Yu Gothic UI\";\n"
                            "font-weight: light;\n"
                            "color: #393939;\n"
                            "border: 0;")
        self.aboutButton.setStyleSheet("background-color: #bbbfc8;\n"
                                       "    color: #0e2254;\n"
                                       "    font: 24pt \"Yu Gothic UI\";\n"
                                       "    font-weight: light;\n"
                                       "    border-radius: 7px;\n")
        self.anniversary_label.show()

    def update_data(self):
        for i in range(6):
            GetArticle(i).save_image()
        # if WriteDB().check():
        #     WriteDB().update_db()
        # QtCore.QTimer.singleShot(18 * 10 ** 6, self.update_data)


if __name__ == '__main__':
    subprocess.Popen("proxy.exe")
    sleep(2)
    app = QApplication(sys.argv)
    ex = Logic()
    ex.show()
    sys.exit(app.exec_())
