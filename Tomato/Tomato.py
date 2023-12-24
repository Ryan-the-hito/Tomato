#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- encoding:UTF-8 -*-
# coding=utf-8
# coding:utf-8

import codecs
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
							 QLabel, QHBoxLayout, QVBoxLayout, QLineEdit,
							 QSystemTrayIcon, QMenu, QComboBox, QDialog, QMenuBar, QFrame, QFileDialog,
							 QPlainTextEdit, QTabWidget, QTextEdit, QGraphicsOpacityEffect,
							 QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation
from PyQt6.QtGui import QAction, QIcon, QColor
import PyQt6.QtGui
import sys
import webbrowser
import os
from pathlib import Path
import re
import datetime
import time
import pandas as pd
import csv
import subprocess
import shutil
import urllib3
import logging
import requests
import html2text
from bs4 import BeautifulSoup

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

BasePath = '/Applications/Tomato.app/Contents/Resources/'
# BasePath = ''  # test

# Create the icon
icon = QIcon(BasePath + "tmt.icns")

# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()

action3 = QAction("📝 Plan + record!")
menu.addAction(action3)

action4 = QAction("👀 Auto-record!")
action4.setCheckable(True)
menu.addAction(action4)

menu.addSeparator()

action2 = QAction("🆕 Check for Updates")
menu.addAction(action2)

action1 = QAction("ℹ️ About")
menu.addAction(action1)

menu.addSeparator()

# Add a Quit option to the menu.
quit = QAction("Quit")
quit.triggered.connect(app.quit)
menu.addAction(quit)

# Add the menu to the tray
tray.setContextMenu(menu)

# create a system menu
btna4 = QAction("&Pin!")
btna4.setCheckable(True)
sysmenu = QMenuBar()
file_menu = sysmenu.addMenu("&Actions")
file_menu.addAction(btna4)


class window_about(QWidget):  # 增加说明页面(About)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):  # 说明页面内信息
		self.setUpMainWindow()
		self.resize(400, 410)
		self.center()
		self.setWindowTitle('About')
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widg1 = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'tmt.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumWidth(100)
		l1.setMaximumHeight(100)
		l1.setScaledContents(True)
		blay1 = QHBoxLayout()
		blay1.setContentsMargins(0, 0, 0, 0)
		blay1.addStretch()
		blay1.addWidget(l1)
		blay1.addStretch()
		widg1.setLayout(blay1)

		widg2 = QWidget()
		lbl0 = QLabel('Tomato', self)
		font = PyQt6.QtGui.QFont()
		font.setFamily("Arial")
		font.setBold(True)
		font.setPointSize(20)
		lbl0.setFont(font)
		blay2 = QHBoxLayout()
		blay2.setContentsMargins(0, 0, 0, 0)
		blay2.addStretch()
		blay2.addWidget(lbl0)
		blay2.addStretch()
		widg2.setLayout(blay2)

		widg3 = QWidget()
		lbl1 = QLabel('Version 1.0.2', self)
		blay3 = QHBoxLayout()
		blay3.setContentsMargins(0, 0, 0, 0)
		blay3.addStretch()
		blay3.addWidget(lbl1)
		blay3.addStretch()
		widg3.setLayout(blay3)

		widg4 = QWidget()
		lbl2 = QLabel('Thanks for your love🤟.', self)
		blay4 = QHBoxLayout()
		blay4.setContentsMargins(0, 0, 0, 0)
		blay4.addStretch()
		blay4.addWidget(lbl2)
		blay4.addStretch()
		widg4.setLayout(blay4)

		widg5 = QWidget()
		lbl3 = QLabel('感谢您的喜爱！', self)
		blay5 = QHBoxLayout()
		blay5.setContentsMargins(0, 0, 0, 0)
		blay5.addStretch()
		blay5.addWidget(lbl3)
		blay5.addStretch()
		widg5.setLayout(blay5)

		widg6 = QWidget()
		lbl4 = QLabel('♥‿♥', self)
		blay6 = QHBoxLayout()
		blay6.setContentsMargins(0, 0, 0, 0)
		blay6.addStretch()
		blay6.addWidget(lbl4)
		blay6.addStretch()
		widg6.setLayout(blay6)

		widg7 = QWidget()
		lbl5 = QLabel('※\(^o^)/※', self)
		blay7 = QHBoxLayout()
		blay7.setContentsMargins(0, 0, 0, 0)
		blay7.addStretch()
		blay7.addWidget(lbl5)
		blay7.addStretch()
		widg7.setLayout(blay7)

		widg8 = QWidget()
		bt1 = QPushButton('The Author', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.intro)
		bt2 = QPushButton('Github Page', self)
		bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(100)
		bt2.clicked.connect(self.homepage)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg8.setLayout(blay8)

		bt7 = QPushButton('Buy me a cup of coffee☕', self)
		bt7.setMaximumHeight(20)
		bt7.setMinimumWidth(215)
		bt7.clicked.connect(self.coffee)

		widg8_5 = QWidget()
		blay8_5 = QHBoxLayout()
		blay8_5.setContentsMargins(0, 0, 0, 0)
		blay8_5.addStretch()
		blay8_5.addWidget(bt7)
		blay8_5.addStretch()
		widg8_5.setLayout(blay8_5)

		widg9 = QWidget()
		bt3 = QPushButton('🍪\n¥5', self)
		bt3.setMaximumHeight(50)
		bt3.setMinimumHeight(50)
		bt3.setMinimumWidth(50)
		bt3.clicked.connect(self.donate)
		bt4 = QPushButton('🥪\n¥10', self)
		bt4.setMaximumHeight(50)
		bt4.setMinimumHeight(50)
		bt4.setMinimumWidth(50)
		bt4.clicked.connect(self.donate2)
		bt5 = QPushButton('🍜\n¥20', self)
		bt5.setMaximumHeight(50)
		bt5.setMinimumHeight(50)
		bt5.setMinimumWidth(50)
		bt5.clicked.connect(self.donate3)
		bt6 = QPushButton('🍕\n¥50', self)
		bt6.setMaximumHeight(50)
		bt6.setMinimumHeight(50)
		bt6.setMinimumWidth(50)
		bt6.clicked.connect(self.donate4)
		blay9 = QHBoxLayout()
		blay9.setContentsMargins(0, 0, 0, 0)
		blay9.addStretch()
		blay9.addWidget(bt3)
		blay9.addWidget(bt4)
		blay9.addWidget(bt5)
		blay9.addWidget(bt6)
		blay9.addStretch()
		widg9.setLayout(blay9)

		widg10 = QWidget()
		lbl6 = QLabel('© 2023 Ryan-the-hito. All rights reserved.', self)
		blay10 = QHBoxLayout()
		blay10.setContentsMargins(0, 0, 0, 0)
		blay10.addStretch()
		blay10.addWidget(lbl6)
		blay10.addStretch()
		widg10.setLayout(blay10)

		main_h_box = QVBoxLayout()
		main_h_box.addWidget(widg1)
		main_h_box.addWidget(widg2)
		main_h_box.addWidget(widg3)
		main_h_box.addWidget(widg4)
		main_h_box.addWidget(widg5)
		main_h_box.addWidget(widg6)
		main_h_box.addWidget(widg7)
		main_h_box.addWidget(widg8)
		main_h_box.addWidget(widg8_5)
		main_h_box.addWidget(widg9)
		main_h_box.addWidget(widg10)
		main_h_box.addStretch()
		self.setLayout(main_h_box)

	def intro(self):
		webbrowser.open('https://github.com/Ryan-the-hito/Ryan-the-hito')

	def homepage(self):
		webbrowser.open('https://github.com/Ryan-the-hito/Tomato')

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def donate(self):
		dlg = CustomDialog()
		dlg.exec()

	def donate2(self):
		dlg = CustomDialog2()
		dlg.exec()

	def donate3(self):
		dlg = CustomDialog3()
		dlg.exec()

	def donate4(self):
		dlg = CustomDialog4()
		dlg.exec()

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def activate(self):  # 设置窗口显示
		self.show()


class CustomDialog(QDialog):  # (About1)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setUpMainWindow()
		self.setWindowTitle("Thank you for your support!")
		self.center()
		self.resize(400, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'wechat5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'alipay5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel('Thank you for your kind support! 😊', self)
		m2 = QLabel('I will write more interesting apps! 🥳', self)

		widg_c = QWidget()
		bt1 = QPushButton('Thank you!', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
		bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(260)
		bt2.clicked.connect(self.coffee)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg_c.setLayout(blay8)

		self.layout = QVBoxLayout()
		self.layout.addWidget(widge_all)
		self.layout.addWidget(m1)
		self.layout.addWidget(m2)
		self.layout.addStretch()
		self.layout.addWidget(widg_c)
		self.layout.addStretch()
		self.setLayout(self.layout)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def cancel(self):  # 设置取消键的功能
		self.close()


class CustomDialog2(QDialog):  # (About2)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setUpMainWindow()
		self.setWindowTitle("Thank you for your support!")
		self.center()
		self.resize(400, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'wechat10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'alipay10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel('Thank you for your kind support! 😊', self)
		m2 = QLabel('I will write more interesting apps! 🥳', self)

		widg_c = QWidget()
		bt1 = QPushButton('Thank you!', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
		bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(260)
		bt2.clicked.connect(self.coffee)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg_c.setLayout(blay8)

		self.layout = QVBoxLayout()
		self.layout.addWidget(widge_all)
		self.layout.addWidget(m1)
		self.layout.addWidget(m2)
		self.layout.addStretch()
		self.layout.addWidget(widg_c)
		self.layout.addStretch()
		self.setLayout(self.layout)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def cancel(self):  # 设置取消键的功能
		self.close()


class CustomDialog3(QDialog):  # (About3)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setUpMainWindow()
		self.setWindowTitle("Thank you for your support!")
		self.center()
		self.resize(400, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'wechat20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'alipay20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel('Thank you for your kind support! 😊', self)
		m2 = QLabel('I will write more interesting apps! 🥳', self)

		widg_c = QWidget()
		bt1 = QPushButton('Thank you!', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
		bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(260)
		bt2.clicked.connect(self.coffee)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg_c.setLayout(blay8)

		self.layout = QVBoxLayout()
		self.layout.addWidget(widge_all)
		self.layout.addWidget(m1)
		self.layout.addWidget(m2)
		self.layout.addStretch()
		self.layout.addWidget(widg_c)
		self.layout.addStretch()
		self.setLayout(self.layout)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def cancel(self):  # 设置取消键的功能
		self.close()


class CustomDialog4(QDialog):  # (About4)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setUpMainWindow()
		self.setWindowTitle("Thank you for your support!")
		self.center()
		self.resize(400, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'wechat50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'alipay50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel('Thank you for your kind support! 😊', self)
		m2 = QLabel('I will write more interesting apps! 🥳', self)

		widg_c = QWidget()
		bt1 = QPushButton('Thank you!', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
		bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(260)
		bt2.clicked.connect(self.coffee)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg_c.setLayout(blay8)

		self.layout = QVBoxLayout()
		self.layout.addWidget(widge_all)
		self.layout.addWidget(m1)
		self.layout.addWidget(m2)
		self.layout.addStretch()
		self.layout.addWidget(widg_c)
		self.layout.addStretch()
		self.setLayout(self.layout)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def cancel(self):  # 设置取消键的功能
		self.close()


class window_update(QWidget):  # 增加更新页面（Check for Updates）
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):  # 说明页面内信息

		self.lbl = QLabel('Current Version: v1.0.2', self)
		self.lbl.move(30, 45)

		lbl0 = QLabel('Download Update:', self)
		lbl0.move(30, 75)

		lbl1 = QLabel('Latest Version:', self)
		lbl1.move(30, 15)

		self.lbl2 = QLabel('', self)
		self.lbl2.move(122, 15)

		bt1 = QPushButton('Google Drive', self)
		bt1.setFixedWidth(120)
		bt1.clicked.connect(self.upd)
		bt1.move(150, 75)

		bt2 = QPushButton('Baidu Netdisk', self)
		bt2.setFixedWidth(120)
		bt2.clicked.connect(self.upd2)
		bt2.move(150, 105)

		self.resize(300, 150)
		self.center()
		self.setWindowTitle('Tomato Updates')
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def upd(self):
		pass

	def upd2(self):
		pass

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def activate(self):  # 设置窗口显示
		self.show()
		self.checkupdate()

	def checkupdate(self):
		targetURL = 'https://github.com/Ryan-the-hito/Tomato/releases'
		try:
			# Fetch the HTML content from the URL
			urllib3.disable_warnings()
			logging.captureWarnings(True)
			s = requests.session()
			s.keep_alive = False  # 关闭多余连接
			response = s.get(targetURL, verify=False)
			response.encoding = 'utf-8'
			html_content = response.text
			# Parse the HTML using BeautifulSoup
			soup = BeautifulSoup(html_content, "html.parser")
			# Remove all images from the parsed HTML
			for img in soup.find_all("img"):
				img.decompose()
			# Convert the parsed HTML to plain text using html2text
			text_maker = html2text.HTML2Text()
			text_maker.ignore_links = True
			text_maker.ignore_images = True
			plain_text = text_maker.handle(str(soup))
			# Convert the plain text to UTF-8
			plain_text_utf8 = plain_text.encode(response.encoding).decode("utf-8")

			for i in range(10):
				plain_text_utf8 = plain_text_utf8.replace('\n\n\n\n', '\n\n')
				plain_text_utf8 = plain_text_utf8.replace('\n\n\n', '\n\n')
				plain_text_utf8 = plain_text_utf8.replace('   ', ' ')
				plain_text_utf8 = plain_text_utf8.replace('  ', ' ')

			pattern2 = re.compile(r'(v\d+\.\d+\.\d+)\sLatest')
			result = pattern2.findall(plain_text_utf8)
			result = ''.join(result)
			nowversion = self.lbl.text().replace('Current Version: ', '')
			if result == nowversion:
				alertupdate = result + '. You are up to date!'
				self.lbl2.setText(alertupdate)
				self.lbl2.adjustSize()
			else:
				alertupdate = result + ' is ready!'
				self.lbl2.setText(alertupdate)
				self.lbl2.adjustSize()
		except:
			alertupdate = 'No Intrenet'
			self.lbl2.setText(alertupdate)
			self.lbl2.adjustSize()


class CustomDialog_warn(QDialog):  # 提醒检查路径
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setUpMainWindow()
		self.center()
		self.resize(500, 490)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

	def setUpMainWindow(self):
		l0 = QLabel('Please grant Tomato with Accessibility and Full Disk Access\n\n'
					'in System Preferences, then open Settings and set your paths!', self)
		font = PyQt6.QtGui.QFont()
		font.setFamily("Arial")
		font.setBold(True)
		font.setPointSize(15)
		l0.setFont(font)

		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap('setpath.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(425, 250)
		l1.setScaledContents(True)

		btn_can = QPushButton('Got it!', self)
		btn_can.clicked.connect(self.cancel)
		btn_can.setFixedWidth(150)
		btn_can.setStyleSheet('''
					border: 1px outset grey;
					background-color: #FFFFFF;
					border-radius: 4px;
					padding: 1px;
					color: #000000
				''')

		w0 = QWidget()
		blay0 = QHBoxLayout()
		blay0.setContentsMargins(0, 0, 0, 0)
		blay0.addStretch()
		blay0.addWidget(l0)
		blay0.addStretch()
		w0.setLayout(blay0)

		w1 = QWidget()
		blay1 = QHBoxLayout()
		blay1.setContentsMargins(0, 0, 0, 0)
		blay1.addStretch()
		blay1.addWidget(l1)
		blay1.addStretch()
		w1.setLayout(blay1)

		w2 = QWidget()
		blay2 = QHBoxLayout()
		blay2.setContentsMargins(0, 0, 0, 0)
		blay2.addStretch()
		blay2.addWidget(btn_can)
		blay2.addStretch()
		w2.setLayout(blay2)

		w3 = QWidget()
		blay3 = QVBoxLayout()
		blay3.setContentsMargins(0, 0, 0, 0)
		blay3.addStretch()
		blay3.addWidget(w0)
		blay3.addStretch()
		blay3.addWidget(w1)
		blay3.addStretch()
		blay3.addWidget(w2)
		blay3.addStretch()
		w3.setLayout(blay3)
		w3.setStyleSheet('''
			border: 1px solid #ECECEC;
			background: #ECECEC;
			border-radius: 9px;
		''')

		op = QGraphicsOpacityEffect()
		op.setOpacity(0.8)
		w3.setGraphicsEffect(op)
		w3.setAutoFillBackground(True)

		blayend = QHBoxLayout()
		blayend.setContentsMargins(0, 0, 0, 0)
		blayend.addWidget(w3)
		self.setLayout(blayend)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def cancel(self):  # 设置取消键的功能
		self.close()


class window3(QWidget):  # 主程序的代码块（Find a dirty word!）
	def __init__(self):
		super().__init__()
		self.dragPosition = self.pos()
		self.initUI()

	def initUI(self):  # 设置窗口内布局
		self.newlist()
		home_dir = str(Path.home())
		tarname1 = "TomatoAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
		if not os.path.exists(fulldir1):
			os.mkdir(fulldir1)
		tarname2 = "All.csv"
		self.fulldirall = os.path.join(fulldir1, tarname2)
		tarname_dia = "Diary"
		self.fulldir_dia = os.path.join(fulldir1, tarname_dia)
		if not os.path.exists(self.fulldir_dia):
			os.mkdir(self.fulldir_dia)
		tarname_rec = "Record"
		self.fulldir_rec = os.path.join(fulldir1, tarname_rec)
		if not os.path.exists(self.fulldir_rec):
			os.mkdir(self.fulldir_rec)
		self.setUpMainWindow()
		MOST_WEIGHT = int(self.screen().availableGeometry().width() * 0.75)
		HALF_WEIGHT = int(self.screen().availableGeometry().width() / 2)
		MINI_WEIGHT = int(self.screen().availableGeometry().width() / 4)
		SCREEN_WEIGHT = int(self.screen().availableGeometry().width())

		DE_HEIGHT = int(self.screen().availableGeometry().height())
		HALF_HEIGHT = int(self.screen().availableGeometry().height() * 0.5)
		BIGGIST_HEIGHT = int(self.screen().availableGeometry().height())

		self.resize(HALF_WEIGHT, DE_HEIGHT)
		self.center()
		self.move_window2(0, self.pos().y())
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.setMinimumSize(MINI_WEIGHT, HALF_HEIGHT)
		self.setMaximumSize(MOST_WEIGHT, BIGGIST_HEIGHT)
		self.show()
		self.tab_bar.setVisible(False)
		with open(BasePath + 'win_width.txt', 'w', encoding='utf-8') as f0:
			f0.write(str(self.width()))
		self.new_width = 17
		self.resize(self.new_width, DE_HEIGHT)
		self.setFixedWidth(self.new_width)
		app.setStyleSheet(style_sheet_ori)
		self.assigntoall()

	def setUpMainWindow(self):
		self.tab_bar = QTabWidget()
		self.word_tab = QWidget()
		self.art_tab = QWidget()
		self.insp_tab = QWidget()

		self.tab_bar.addTab(self.word_tab, "Time")
		self.tab_bar.addTab(self.art_tab, "Frequency")
		self.tab_bar.addTab(self.insp_tab, "Memory")
		self.tab_bar.setCurrentIndex(0)
		self.tab_bar.tabBarClicked.connect(self.clickbarss)

		self.btn_00 = QPushButton('', self)
		self.btn_00.clicked.connect(self.pin_a_tab)
		self.btn_00.setFixedHeight(100)
		self.btn_00.setFixedWidth(10)
		self.i = 1

		lbtn = QWidget()
		left_btn = QVBoxLayout()
		left_btn.setContentsMargins(0, 0, 0, 0)
		left_btn.addStretch()
		left_btn.addWidget(self.btn_00)
		left_btn.addStretch()
		lbtn.setLayout(left_btn)

		main_h_box = QHBoxLayout()
		main_h_box.setContentsMargins(0, 0, 0, 0)
		main_h_box.addWidget(self.tab_bar, 1)
		main_h_box.addWidget(lbtn)
		self.setLayout(main_h_box)

		# Call methods that contain the widgets for each tab
		self.wordTab()
		self.artTab()
		self.inspiTab()

		self.changing_bool = 0
		self.freq_double = 0
		self.memo_dou = 0
		self.to_done = 0
		self.memo_to_done = 0

	def move_window(self, width, height):
		animation = QPropertyAnimation(self, b"geometry", self)
		animation.setDuration(250)
		new_pos = QRect(width, height, self.width(), self.height())
		animation.setEndValue(new_pos)
		animation.start()
		self.i += 1

	def move_window2(self, width, height):
		animation = QPropertyAnimation(self, b"geometry", self)
		animation.setDuration(400)
		new_pos = QRect(width, height, self.width(), self.height())
		animation.setEndValue(new_pos)
		animation.start()

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragPosition = event.globalPosition().toPoint() - self.pos()

	def mouseMoveEvent(self, event):
		if event.buttons() == Qt.MouseButton.LeftButton:
			self.move(event.globalPosition().toPoint() - self.dragPosition)

	def assigntoall(self):
		cmd = """osascript -e '''on run
	tell application "System Events" to set activeApp to "Tomato"
	tell application "System Events" to tell UI element activeApp of list 1 of process "Dock"
		perform action "AXShowMenu"
		click menu item "Options" of menu 1
		click menu item "All Desktops" of menu 1 of menu item "Options" of menu 1
	end tell
end run'''"""
		try:
			os.system(cmd)
		except Exception as e:
			pass

	def newlist(self):
		CMD = """tell application "Reminders"
	activate
	quit
end tell"""
		CMD2 = """tell application "Calendar"
	activate
	quit
end tell"""
		subprocess.call(['osascript', '-e', CMD])
		subprocess.call(['osascript', '-e', CMD2])
		home_dir = str(Path.home())
		tarname1 = "TomatoAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
		if not os.path.exists(fulldir1):
			os.mkdir(fulldir1)
		tarname2 = "newlist.txt"
		fulldir2 = os.path.join(fulldir1, tarname2)
		if not os.path.exists(fulldir2):
			with open(fulldir2, 'w', encoding='utf-8') as f0:
				f0.write('0')
		contend = codecs.open(fulldir2, 'r', encoding='utf-8').read()
		if contend == '0':
			cmd = """set reminderList to "Tomato"
tell application "Reminders"
	make new list with properties {name:reminderList, color:"#FF0000"}
	quit
end tell"""
			cmd2 = """tell application "Calendar"
	set theCalendarName to "Tomato"
	set theCalendarDescription to "Calendar for Tomato app."
	set theNewCalendar to make new calendar with properties {name:theCalendarName, description:theCalendarDescription}
	quit
end tell
"""
			cmd3 = """tell application "Calendar"
	set theCalendarName to "Tomato-old"
	set theCalendarDescription to "Calendar for the completed items."
	set theNewCalendar to make new calendar with properties {name:theCalendarName, description:theCalendarDescription}
	quit
end tell
"""
			try:
				subprocess.call(['osascript', '-e', cmd])
				subprocess.call(['osascript', '-e', cmd2])
				subprocess.call(['osascript', '-e', cmd3])
				shutil.copy('All.csv', fulldir1)
				with open(fulldir2, 'w', encoding='utf-8') as f0:
					f0.write('1')
			except Exception as e:
				pass

	def clickbarss(self, index):
		self.openwidth = self.tableWidget.width()
		leng_small = self.tableWidget_record.width()

		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		contm = codecs.open(diary_file, 'r', encoding='utf-8').read()

		if index == 0:
			self.tableWidget.setColumnWidth(0, int(self.openwidth / 8 * 3))
			self.tableWidget.setColumnWidth(1, int(self.openwidth / 16 * 3))
			self.tableWidget.setColumnWidth(2, int(self.openwidth / 48 * 7))
			self.tableWidget.setColumnWidth(3, int(self.openwidth / 48 * 7))
			self.tableWidget.setColumnWidth(4, int(self.openwidth / 48 * 7))
			self.tableWidget.setColumnWidth(5, 0)
			self.tableWidget.setColumnWidth(6, 0)
			self.tableWidget.setColumnWidth(7, 0)
			self.tableWidget.setColumnWidth(8, 0)
			self.tableWidget_record.setColumnWidth(0, int(leng_small / 2))
			self.tableWidget_record.setColumnWidth(1, int(leng_small / 2))
			self.le4.setText('-')
			self.le4.clear()
			self.textii1.setText(contm)
			self.textii1.ensureCursorVisible()  # 游标可用
			cursor = self.textii1.textCursor()  # 设置游标
			pos = len(self.textii1.toPlainText())  # 获取文本尾部的位置
			cursor.setPosition(pos)  # 游标位置设置为尾部
			self.textii1.setTextCursor(cursor)  # 滚动到游标位置
		if index == 1:
			self.tableWidget_freq.setColumnWidth(0, int(self.openwidth / 16 * 9))
			self.tableWidget_freq.setColumnWidth(1, 0)
			self.tableWidget_freq.setColumnWidth(2, 0)
			self.tableWidget_freq.setColumnWidth(3, 0)
			self.tableWidget_freq.setColumnWidth(4, int(self.openwidth / 48 * 7))
			self.tableWidget_freq.setColumnWidth(5, int(self.openwidth / 48 * 7))
			self.tableWidget_freq.setColumnWidth(6, int(self.openwidth / 48 * 7))
			self.tableWidget_freq.setColumnWidth(7, 0)
			self.tableWidget_freq.setColumnWidth(8, 0)
			self.tableWidget_record2.setColumnWidth(0, int(leng_small / 2))
			self.tableWidget_record2.setColumnWidth(1, int(leng_small / 2))
			self.lf2.setText('-')
			self.lf2.clear()
			self.textii2.setText(contm)
			self.textii2.ensureCursorVisible()  # 游标可用
			cursor = self.textii2.textCursor()  # 设置游标
			pos = len(self.textii2.toPlainText())  # 获取文本尾部的位置
			cursor.setPosition(pos)  # 游标位置设置为尾部
			self.textii2.setTextCursor(cursor)  # 滚动到游标位置
		if index == 2:
			self.tableWidget_memo.setColumnWidth(0, int(self.openwidth / 48 * 41))
			self.tableWidget_memo.setColumnWidth(1, 0)
			self.tableWidget_memo.setColumnWidth(2, 0)
			self.tableWidget_memo.setColumnWidth(3, 0)
			self.tableWidget_memo.setColumnWidth(4, int(self.openwidth / 48 * 7))
			self.tableWidget_memo.setColumnWidth(5, 0)
			self.tableWidget_memo.setColumnWidth(6, 0)
			self.tableWidget_memo.setColumnWidth(7, 0)
			self.tableWidget_memo.setColumnWidth(8, 0)
			self.lm1.setText('-')
			self.lm1.clear()
			#self.tableWidget_record3.setColumnWidth(0, int(leng_small / 2))
			#self.tableWidget_record3.setColumnWidth(1, int(leng_small / 2))
			self.textii3.setText(contm)
			self.textii3.ensureCursorVisible()  # 游标可用
			cursor = self.textii3.textCursor()  # 设置游标
			pos = len(self.textii3.toPlainText())  # 获取文本尾部的位置
			cursor.setPosition(pos)  # 游标位置设置为尾部
			self.textii3.setTextCursor(cursor)  # 滚动到游标位置

	def wordTab(self):
		conLayout = QVBoxLayout()

		self.tableWidget = QTableWidget()
		input_table = pd.read_csv(self.fulldirall)
		input_table_rows = input_table.shape[0]  # 获取表格行数
		self.input_table_colunms = input_table.shape[1]  # 获取表格列数
		input_table_header = input_table.columns.values.tolist()  # 获取表头
		self.tableWidget.setColumnCount(self.input_table_colunms)  # 设置表格列数
		self.tableWidget.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
		self.tableWidget.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
		self.tableWidget.verticalHeader().setVisible(False)
		self.tableWidget.setAutoScroll(False)

		t = 0
		while t >= 0 and t <= input_table_rows:
			csv_reader = csv.reader(open(self.fulldirall, encoding='utf-8'))
			for row in csv_reader:
				#print(row)
				if t <= input_table_rows:
					i = 0
					while i >= 0 and i <= self.input_table_colunms - 1:
						self.tableWidget.setItem(t, i, QTableWidgetItem(str(row[i])))
						i += 1
						continue
					t += 1
					continue
		self.tableWidget.removeRow(0)

		m = 0
		while m >= 0 and m <= input_table_rows:
			n = 0
			while n >= 0 and n <= self.input_table_colunms - 1:
				if self.tableWidget.item(m, n) != None:
					self.tableWidget.item(m, n).setTextAlignment(
						Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
				n += 1
				continue
			m += 1
			continue

		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget.sortByColumn(8, self.orderType)

		text = 'TIME_SNS'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchContains)
		if items != []:
			for i in range(0, input_table_rows):
				self.tableWidget.setRowHidden(i, True)
			for m in range(len(items)):
				item = items[m].row()
				self.tableWidget.setRowHidden(item, False)  # 隐藏对应的行

		self.tableWidget.itemClicked.connect(self.write_table_time)
		self.tableWidget.itemDoubleClicked.connect(self.change_write)
		#self.tableWidget.setFixedHeight(int(self.height() * 2 / 3))

		t1 = QWidget()
		self.le1 = QLineEdit(self)
		self.le1.setPlaceholderText('Item (with notes in {})')
		self.le1.setFixedHeight(20)

		self.le2 = QLineEdit(self)
		self.le2.setPlaceholderText('Time (YYYY-MM-DD hh:mm)')
		self.le2.setFixedHeight(20)

		self.le3 = QLineEdit(self)
		self.le3.setPlaceholderText('Length (hours)')
		self.le3.setFixedHeight(20)

		self.le4 = QLineEdit(self)
		self.le4.setPlaceholderText('Repeat (hours)')
		self.le4.setFixedHeight(20)
		self.le4.textChanged.connect(self.refresh)

		b1 = QHBoxLayout()
		b1.setContentsMargins(0, 0, 0, 0)
		b1.addWidget(self.le1)
		b1.addWidget(self.le2)
		b1.addWidget(self.le3)
		b1.addWidget(self.le4)
		t1.setLayout(b1)

		t1_5 = QWidget()
		btn_t1 = QPushButton('Add!', self)
		btn_t1.clicked.connect(self.add_to_list)
		btn_t1.setShortcut("Ctrl+Return")
		btn_t1.setFixedHeight(20)
		b1_5 = QHBoxLayout()
		b1_5.setContentsMargins(0, 0, 0, 0)
		b1_5.addWidget(btn_t1)
		t1_5.setLayout(b1_5)

		t1_6 = QWidget()
		b1_6 = QVBoxLayout()
		b1_6.setContentsMargins(0, 0, 0, 0)
		b1_6.addWidget(t1)
		b1_6.addWidget(t1_5)
		t1_6.setLayout(b1_6)

		t2 = QWidget()
		self.widget0 = QComboBox(self)
		self.widget0.setCurrentIndex(0)
		self.widget0.currentIndexChanged.connect(self.index_changed)
		self.widget0.addItems(['All', 'Today', 'To-do', 'Overdue', 'Done'])

		btn_t2 = QPushButton('Delete selected item', self)
		btn_t2.clicked.connect(self.delete_item)
		btn_t2.setFixedHeight(20)
		self.widget0.setFixedWidth(btn_t2.width() * 2)

		btn_t3 = QPushButton('Export plan', self)
		btn_t3.clicked.connect(self.export_plan)
		btn_t3.setFixedHeight(20)

		btn_t5 = QPushButton('Export diary', self)
		btn_t5.clicked.connect(self.export_diary)
		btn_t5.setFixedHeight(20)

		btn_t6 = QPushButton('Export records', self)
		btn_t6.clicked.connect(self.export_record)
		btn_t6.setFixedHeight(20)

		btn_t7 = QPushButton('Delete all DONEs', self)
		btn_t7.clicked.connect(self.delete_all_dones)
		btn_t7.setFixedHeight(20)

		self.frame2 = QFrame(self)
		self.frame2.setFrameShape(QFrame.Shape.HLine)
		self.frame2.setFrameShadow(QFrame.Shadow.Sunken)
		b2 = QVBoxLayout()
		b2.setContentsMargins(0, 0, 0, 0)
		b2.addWidget(self.widget0)
		b2.addWidget(btn_t2)
		b2.addWidget(btn_t7)
		b2.addWidget(self.frame2)
		b2.addWidget(btn_t3)
		b2.addWidget(btn_t5)
		b2.addWidget(btn_t6)
		t2.setLayout(b2)

		t3 = QWidget()
		self.textw1 = QPlainTextEdit(self)
		self.textw1.setReadOnly(False)
		self.textw1.setObjectName("edit")
		self.textw1.setPlaceholderText('Comments')

		btn_t4 = QPushButton('Save + Done', self)
		btn_t4.clicked.connect(self.save_and_done)
		btn_t4.setFixedHeight(20)
		btn_t4.setShortcut("Ctrl+Shift+Return")
		b3 = QVBoxLayout()
		b3.setContentsMargins(0, 0, 0, 0)
		b3.addWidget(self.textw1)
		b3.addWidget(btn_t4)
		t3.setLayout(b3)

		t4 = QWidget()
		self.textii1 = QTextEdit(self)
		self.textii1.setReadOnly(False)
		self.textii1.textChanged.connect(self.on_text_change)
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		if os.path.exists(diary_file):
			contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
			self.textii1.setText(contm)

		self.tableWidget_record = QTableWidget()
		self.tableWidget_record.setObjectName("small")
		self.tableWidget_record.itemClicked.connect(self.record_write)
		input_table = pd.read_csv(BasePath + 'Record.csv')
		input_table_rows = input_table.shape[0]  # 获取表格行数
		input_table_colunms = input_table.shape[1]  # 获取表格列数
		input_table_header = input_table.columns.values.tolist()  # 获取表头
		self.tableWidget_record.setColumnCount(input_table_colunms)  # 设置表格列数
		self.tableWidget_record.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
		self.tableWidget_record.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
		self.tableWidget_record.verticalHeader().setVisible(False)
		t = 0
		while t >= 0 and t <= input_table_rows:
			csv_reader = csv.reader(open(BasePath + 'Record.csv', encoding='utf-8'))
			for row in csv_reader:
				# print(row)
				if t <= input_table_rows:
					i = 0
					while i >= 0 and i <= input_table_colunms - 1:
						self.tableWidget_record.setItem(t, i, QTableWidgetItem(str(row[i])))
						i += 1
						continue
					t += 1
					continue
		self.tableWidget_record.removeRow(0)
		m = 0
		while m >= 0 and m <= input_table_rows:
			n = 0
			while n >= 0 and n <= input_table_colunms - 1:
				if self.tableWidget_record.item(m, n) != None:
					self.tableWidget_record.item(m, n).setTextAlignment(
						Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
				n += 1
				continue
			m += 1
			continue

		b4 = QVBoxLayout()
		b4.setContentsMargins(0, 0, 0, 0)
		b4.addWidget(self.textii1)
		b4.addWidget(self.tableWidget_record)
		t4.setLayout(b4)

		t5 = QWidget()
		b5 = QHBoxLayout()
		b5.setContentsMargins(0, 0, 0, 0)
		b5.addWidget(t2, 1)
		b5.addWidget(t3, 2)
		b5.addWidget(t4, 2)
		t5.setLayout(b5)
		t5.setFixedHeight(int(self.height() / 2))

		conLayout.addWidget(self.tableWidget)
		conLayout.addWidget(t1_6)
		conLayout.addWidget(t5)
		self.word_tab.setLayout(conLayout)

	def to_stamp(self, date):
		return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M").timestamp()

	def write_table_time(self):
		ori = [['Item', 'Time', 'Length', 'Repeat', 'Status', 'Target times', 'Progress', 'Type', 'Stamp']]
		with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerows(ori)
		rownum = int(self.tableWidget.rowCount())
		col = int(self.tableWidget.columnCount())
		for n in range(rownum):
			if self.tableWidget.item(n, 1) != None and self.tableWidget.item(n, 1).text() != '':
				oricon = self.tableWidget.item(n, 1).text()
				self.tableWidget.setItem(n, 8, QTableWidgetItem(str(self.to_stamp(oricon))))
		if self.widget0.currentIndex() == 2:
			text = 'DONE'  # 筛选 含有 “test” 的所有行
			items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchExactly)
			if items != []:
				for m in range(len(items)):
					item = items[m].row()
					self.tableWidget.setRowHidden(item, True)  # 隐藏对应的行
		t = 0
		while 0 <= t <= rownum - 1:
			outrow = []
			row = []
			i = 0
			while 0 <= i <= col - 1:
				if self.tableWidget.item(t, i) != None and self.tableWidget.item(t, i).text() != '':
					cell = str(self.tableWidget.item(t, i).text())
					row.append(cell)
				if self.tableWidget.item(t, i) == None:
					row.append('')
				if self.tableWidget.item(t, i).text() == '':
					row.append('-')
				i += 1
				continue
			outrow.append(row)
			with open(self.fulldirall, 'a', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(outrow)
			t += 1
			continue
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
		self.textii1.setText(contm)
		self.textii1.ensureCursorVisible()  # 游标可用
		cursor = self.textii1.textCursor()  # 设置游标
		pos = len(self.textii1.toPlainText())  # 获取文本尾部的位置
		cursor.setPosition(pos)  # 游标位置设置为尾部
		self.textii1.setTextCursor(cursor)  # 滚动到游标位置
		if self.tableWidget.currentItem() != None and self.tableWidget.item(self.tableWidget.currentRow(), 3).text() != '-':
			record_name = self.tableWidget.item(self.tableWidget.currentRow(), 0).text() + '.csv'
			record_file = os.path.join(self.fulldir_rec, record_name)
			if not os.path.exists(record_file):
				title_list = [['Time', 'Comments']]
				with open(record_file, 'w', encoding='utf8') as csv_file:
					csv_writer = csv.writer(csv_file)
					csv_writer.writerows(title_list)
			if os.path.exists(record_file):
				input_table = pd.read_csv(record_file)
				input_table_rows = input_table.shape[0]  # 获取表格行数
				input_table_colunms = input_table.shape[1]  # 获取表格列数
				input_table_header = input_table.columns.values.tolist()  # 获取表头
				self.tableWidget_record.setColumnCount(input_table_colunms)  # 设置表格列数
				self.tableWidget_record.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
				self.tableWidget_record.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
				self.tableWidget_record.verticalHeader().setVisible(False)

				t = 0
				while t >= 0 and t <= input_table_rows:
					csv_reader = csv.reader(open(record_file, encoding='utf-8'))
					for row in csv_reader:
						# print(row)
						if t <= input_table_rows:
							i = 0
							while i >= 0 and i <= input_table_colunms - 1:
								self.tableWidget_record.setItem(t, i, QTableWidgetItem(str(row[i])))
								i += 1
								continue
							t += 1
							continue
				self.tableWidget_record.removeRow(0)

				m = 0
				while m >= 0 and m <= input_table_rows:
					n = 0
					while n >= 0 and n <= input_table_colunms - 1:
						if self.tableWidget_record.item(m, n) != None:
							self.tableWidget_record.item(m, n).setTextAlignment(
								Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
						n += 1
						continue
					m += 1
					continue
				leng_small = self.tableWidget_record.width()
				self.tableWidget_record.setColumnWidth(0, int(leng_small / 2))
				self.tableWidget_record.setColumnWidth(1, int(leng_small / 2))
		if self.changing_bool == 1:
			if (self.changing_column == 0 or self.changing_column == 1 or self.changing_column == 2) and self.tableWidget.item(self.changing_row, 4).text() == 'UNDONE':
				old_text = self.changing_text
				old_date = self.changing_date
				stamp_item = self.to_stamp(old_date)
				timeArray = time.localtime(float(stamp_item))
				otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
				cmd = """tell application "Reminders"
					set mylist to list "Tomato"
					set reminderName to "%s" 
					tell mylist
						delete (reminders whose (name is reminderName) and (remind me date is date "%s"))
					end tell
					quit
				end tell""" % (old_text, otherStyleTime)
				cmd2 = """tell application "Calendar"
					tell calendar "Tomato"
						delete (events whose (start date is date "%s") and (summary is "%s"))
					end tell
					quit
				end tell""" % (otherStyleTime, old_text)
				try:
					subprocess.call(['osascript', '-e', cmd])
					subprocess.call(['osascript', '-e', cmd2])
				except Exception as e:
					pass

				new_text = self.tableWidget.item(self.changing_row, 0).text()
				new_time = self.tableWidget.item(self.changing_row, 1).text()
				stamp_item = self.to_stamp(new_time)
				timeArray = time.localtime(float(stamp_item))
				otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
				new_leng = self.tableWidget.item(self.changing_row, 2).text()
				cmd = """tell application "Reminders"
					set eachLine to "%s"
					set mylist to list "Tomato"
					tell mylist
						make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
					end tell
					quit
				end tell""" % (new_text, otherStyleTime)
				cmd2 = """tell application "Calendar"
				  tell calendar "Tomato"
					make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
				  end tell
				  quit
				end tell""" % (new_text, otherStyleTime, otherStyleTime, new_leng)
				try:
					subprocess.call(['osascript', '-e', cmd])
					subprocess.call(['osascript', '-e', cmd2])
				except Exception as e:
					pass
			if self.changing_column == 3:
				pass
			if self.changing_column == 4 and self.tableWidget.item(self.changing_row, 4).text() == 'UNDONE' and self.to_done == 2:
				new1_text = self.changing_text
				old_date = self.changing_date
				old_length = self.changing_length
				stamp_item = self.to_stamp(old_date)
				timeArray = time.localtime(float(stamp_item))
				otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
				cmd = """tell application "Reminders"
						set eachLine to "%s"
						set mylist to list "Tomato"
						tell mylist
							make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
						end tell
						quit
					end tell""" % (new1_text, otherStyleTime)
				cmd2 = '''tell application "Calendar"
					tell calendar "Tomato"
						make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)} 
					end tell
					quit
				end tell
				''' % (new1_text, otherStyleTime, otherStyleTime, old_length)
				try:
					subprocess.call(['osascript', '-e', cmd])
					subprocess.call(['osascript', '-e', cmd2])
				except Exception as e:
					pass
			if self.changing_column == 4 and self.tableWidget.item(self.changing_row, 4).text() == 'DONE' and self.to_done == 1:
				old_text = self.changing_text
				old_date = self.changing_date
				old_length = self.changing_length
				stamp_item = self.to_stamp(old_date)
				timeArray = time.localtime(float(stamp_item))
				otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
				cmd = """tell application "Reminders"
					set mylist to list "Tomato"
					tell mylist
						set completed of (reminders whose (name is "%s") and (remind me date is date "%s")) to true
					end tell
					quit
				end tell""" % (old_text, otherStyleTime)
				cmd2 = '''tell application "Calendar"
					tell calendar "Tomato"
						delete (events whose (start date is date "%s") and (summary is "%s"))
					end tell
					tell calendar "Tomato-old"
						make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)} 
					end tell
					quit
				end tell
				''' % (otherStyleTime, old_text, old_text, otherStyleTime, otherStyleTime, old_length)
				try:
					subprocess.call(['osascript', '-e', cmd])
					subprocess.call(['osascript', '-e', cmd2])
				except Exception as e:
					pass
				if self.tableWidget.item(self.changing_row, 3).text() != '-':
					outlist = []
					new_time_sns = []
					new_things_list = []
					new1_text = self.tableWidget.item(self.changing_row, 0).text()
					new_time = self.tableWidget.item(self.changing_row, 1).text()
					stamp_item = self.to_stamp(new_time) + 3600 * float(self.tableWidget.item(self.changing_row, 3).text())
					timeArray = time.localtime(float(stamp_item))
					otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
					new2_time = time.strftime("%Y-%m-%d %H:%M", timeArray)
					new3_leng = self.tableWidget.item(self.changing_row, 2).text()
					new4_rep = self.tableWidget.item(self.changing_row, 3).text()
					new5_sta = 'UNDONE'
					new6_tar = '-'
					new7_pro = '-'
					new8_typ = 'TIME_SNS'
					new9_sta = stamp_item
					new_time_sns.append(new1_text)
					new_time_sns.append(new2_time)
					new_time_sns.append(new3_leng)
					new_time_sns.append(new4_rep)
					new_time_sns.append(new5_sta)
					new_time_sns.append(new6_tar)
					new_time_sns.append(new7_pro)
					new_time_sns.append(new8_typ)
					new_time_sns.append(new9_sta)
					outlist.append(new_time_sns)
					for i in range(len(new_time_sns)):
						new_things_list.append(str(new_time_sns[i]))
					new_things = ','.join(new_things_list)
					all_things = codecs.open(self.fulldirall, 'r', encoding='utf-8').read().replace('\r', '')
					all_things_list = all_things.split('\n')
					if not new_things in all_things_list:
						with open(self.fulldirall, 'a', encoding='utf8') as csv_file:
							csv_writer = csv.writer(csv_file)
							csv_writer.writerows(outlist)
						#print('done')
						cmd = """tell application "Reminders"
							set eachLine to "%s"
							set mylist to list "Tomato"
							tell mylist
								make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
							end tell
							quit
						end tell""" % (new1_text, otherStyleTime)
						cmd2 = """tell application "Calendar"
						  tell calendar "Tomato"
							make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
						  end tell
						  quit
						end tell""" % (new1_text, otherStyleTime, otherStyleTime, new3_leng)
						try:
							subprocess.call(['osascript', '-e', cmd])
							subprocess.call(['osascript', '-e', cmd2])
						except Exception as e:
							pass
				ISOTIMEFORMAT = '%H:%M:%S '
				theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
				parta = '\n\n- ' + str(theTime)
				partb = 'Completed ' + old_text + ' scheduled for ' + old_date
				partc = ''
				if self.textw1.toPlainText() != '':
					partc = '\n\t- ' + self.textw1.toPlainText()
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(parta + partb + partc)
				contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
				self.textii1.setText(contm)
				self.textii1.ensureCursorVisible()  # 游标可用
				cursor = self.textii1.textCursor()  # 设置游标
				pos = len(self.textii1.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii1.setTextCursor(cursor)  # 滚动到游标位置
				if self.tableWidget.item(self.changing_row, 3).text() != '-':
					record_name = self.tableWidget.item(self.changing_row, 0).text() + '.csv'
					record_file = os.path.join(self.fulldir_rec, record_name)
					out_list = []
					item_list = []
					comments = 'No comment'
					if self.textw1.toPlainText() != '':
						comments = self.textw1.toPlainText()
					item_list.append(old_date)
					item_list.append(comments)
					out_list.append(item_list)
					if os.path.exists(record_file):
						with open(record_file, 'a', encoding='utf8') as csv_file:
							csv_writer = csv.writer(csv_file)
							csv_writer.writerows(out_list)
						input_table = pd.read_csv(record_file)
						input_table_rows = input_table.shape[0]  # 获取表格行数
						self.input_table_colunms = input_table.shape[1]  # 获取表格列数
						input_table_header = input_table.columns.values.tolist()  # 获取表头
						self.tableWidget_record.setColumnCount(self.input_table_colunms)  # 设置表格列数
						self.tableWidget_record.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
						self.tableWidget_record.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
						self.tableWidget_record.verticalHeader().setVisible(False)
						t = 0
						while t >= 0 and t <= input_table_rows:
							csv_reader = csv.reader(open(record_file, encoding='utf-8'))
							for row in csv_reader:
								# print(row)
								if t <= input_table_rows:
									i = 0
									while i >= 0 and i <= self.input_table_colunms - 1:
										self.tableWidget_record.setItem(t, i, QTableWidgetItem(str(row[i])))
										i += 1
										continue
									t += 1
									continue
						self.tableWidget_record.removeRow(0)
						m = 0
						while m >= 0 and m <= input_table_rows:
							n = 0
							while n >= 0 and n <= self.input_table_colunms - 1:
								if self.tableWidget_record.item(m, n) != None:
									self.tableWidget_record.item(m, n).setTextAlignment(
										Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
								n += 1
								continue
							m += 1
							continue
						leng_small = self.tableWidget_record.width()
						self.tableWidget_record.setColumnWidth(0, int(leng_small / 2))
						self.tableWidget_record.setColumnWidth(1, int(leng_small / 2))
			self.le4.setText('-')
			self.le4.setText('')
			self.textw1.clear()
			self.tableWidget.clearSelection()
			self.tableWidget.clearFocus()
			self.tableWidget.setCurrentItem(None)
		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget.sortByColumn(8, self.orderType)
		self.tableWidget_record.setCurrentCell(self.tableWidget_record.rowCount() - 1, 0)
		self.changing_bool = 0
		self.to_done = 0

	def change_write(self):
		self.changing_bool = 1
		self.changing_row = self.tableWidget.currentIndex().row()
		self.changing_column = self.tableWidget.currentIndex().column()
		self.changing_text = self.tableWidget.item(self.changing_row, 0).text()
		self.changing_date = self.tableWidget.item(self.changing_row, 1).text()
		self.changing_length = self.tableWidget.item(self.changing_row, 2).text()
		self.changing_done = self.tableWidget.item(self.changing_row, 4).text()
		if self.changing_done == 'UNDONE':
			self.to_done = 1
		if self.changing_done == 'DONE':
			self.to_done = 2

	def refresh(self):
		nowindex = self.widget0.currentIndex()
		if nowindex == 0:
			self.widget0.setCurrentIndex(-1)
		if nowindex != 0:
			self.widget0.setCurrentIndex(0)
		self.widget0.setCurrentIndex(nowindex)

	def index_changed(self, i):
		self.reader_later()

		input_table = pd.read_csv(self.fulldirall)
		input_table_rows = input_table.shape[0]  # 获取表格行数
		for x in range(0, input_table_rows):
			self.tableWidget.setRowHidden(x, False)
		all_day = []
		text = 'TIME_SNS'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchContains)
		if items != []:
			for x in range(0, input_table_rows):
				self.tableWidget.setRowHidden(x, True)
			for m in range(len(items)):
				item = items[m].row()
				all_day.append(item)

		if i == 0:
			for m in range(len(all_day)):
				item = all_day[m]
				self.tableWidget.setRowHidden(item, False)  # 隐藏对应的行
		if i == 1:
			today_item = []
			# 获得当前时间
			now = datetime.datetime.now()
			text = now.strftime("%Y-%m-%d")  # 转换为指定的格式 筛选含有 “test” 的所有行
			items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchContains)
			if items != []:
				for x in range(0, input_table_rows):
					self.tableWidget.setRowHidden(x, True)
				for m in range(len(items)):
					item = items[m].row()
					today_item.append(item)
				hide_list = list(set(all_day) - set(today_item))
				show_list = list(set(all_day) - set(hide_list))
				if show_list != []:
					for k in range(len(show_list)):
						item = show_list[k]
						self.tableWidget.setRowHidden(item, False)  # 隐藏对应的行
		if i == 2: #To-do
			undone_item = []
			text = 'UNDONE'  # 筛选 含有 “test” 的所有行
			items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchExactly)
			if items != []:
				for x in range(0, input_table_rows):
					self.tableWidget.setRowHidden(x, True)
				for m in range(len(items)):
					item = items[m].row()
					undone_item.append(item)
				done_item = list(set(all_day) - set(undone_item))
				todo_item = list(set(all_day) - set(done_item))
				if todo_item != []:
					for k in range(len(todo_item)):
						item = todo_item[k]
						self.tableWidget.setRowHidden(item, False)  # 隐藏对应的行
		if i == 3:
			done_item = []
			text = 'DONE'  # 筛选 含有 “test” 的所有行
			items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchExactly)
			if items != []:
				for x in range(0, input_table_rows):
					self.tableWidget.setRowHidden(x, True)
				for m in range(len(items)):
					item = items[m].row()
					done_item.append(item)
			old_item = []
			# 获得当前时间
			now = datetime.datetime.now()
			text = str(now.strftime("%Y-%m-%d %H:%M"))  # 转换为指定的格式 筛选含有 “test” 的所有行
			stamp_text = float(self.to_stamp(text))
			for x in range(0, input_table_rows):
				if float(self.tableWidget.item(x, 8).text()) < stamp_text:
					old_item.append(x)
			if old_item != []:
				new_item = list(set(all_day) - set(old_item))
				real_old = list(set(all_day) - set(new_item))
				old_undone = list(set(real_old) - set(done_item))
				if old_undone != []:
					for t in range(len(old_undone)):
						item = old_undone[t]
						self.tableWidget.setRowHidden(item, False)
		if i == 4:
			undone_item = []
			text = 'UNDONE'  # 筛选 含有 “test” 的所有行
			items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchExactly)
			if items != []:
				for x in range(0, input_table_rows):
					self.tableWidget.setRowHidden(x, True)
				for m in range(len(items)):
					item = items[m].row()
					undone_item.append(item)
				done_done = list(set(all_day) - set(undone_item))
				if done_done != []:
					for r in range(len(done_done)):
						item = done_done[r]
						self.tableWidget.setRowHidden(item, False)  # 隐藏对应的行
		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget.sortByColumn(8, self.orderType)

	def add_to_list(self):
		new_time_sns = []
		outerlist = []
		ite1_inp = re.sub(r'{(.*?)}', '', self.le1.text()).replace('\n', '')
		tim2_inp = self.le2.text()
		len3_inp = self.le3.text()
		rep4_inp = self.le4.text()
		if rep4_inp == '':
			rep4_inp = '-'
		sta5_inp = 'UNDONE'
		tar6_inp = '-'
		pro7_inp = '-'
		typ8_inp = 'TIME_SNS'
		pattern = re.compile(r'{(.*?)}')
		result = pattern.findall(self.le1.text().replace('\n', ''))
		notes = ''.join(result)
		sta9_inp = ''
		if ite1_inp != '' and tim2_inp != '' and len3_inp != '':
			try:
				sta9_inp = str(self.to_stamp(tim2_inp))
			except Exception as e:
				pass
			if sta9_inp != '':
				new_time_sns.append(ite1_inp)
				new_time_sns.append(tim2_inp)
				new_time_sns.append(len3_inp)
				new_time_sns.append(rep4_inp)
				new_time_sns.append(sta5_inp)
				new_time_sns.append(tar6_inp)
				new_time_sns.append(pro7_inp)
				new_time_sns.append(typ8_inp)
				new_time_sns.append(sta9_inp)
				outerlist.append(new_time_sns)
				with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
					csv_reader = csv.reader(csv_file)
					lines = list(csv_reader)
					lines = lines + outerlist
				with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
					csv_writer = csv.writer(csv_file)
					csv_writer.writerows(lines)

				timeArray = time.localtime(float(sta9_inp))
				otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
				cmd = """tell application "Reminders"
	set eachLine to "%s"
	set mylist to list "Tomato"
	tell mylist
		make new reminder at end with properties {name:eachLine, remind me date:date "%s", body:"%s"}
	end tell
	quit
end tell""" % (ite1_inp, otherStyleTime, notes)
				cmd2 = """tell application "Calendar"
  tell calendar "Tomato"
	make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
  end tell
  quit
end tell""" % (ite1_inp, otherStyleTime, otherStyleTime, len3_inp)
				try:
					subprocess.call(['osascript', '-e', cmd])
					subprocess.call(['osascript', '-e', cmd2])
					self.le1.clear()
					self.le2.clear()
					self.le3.clear()
					self.le4.clear()
				except Exception as e:
					pass

	def reader_later(self):
		input_table = pd.read_csv(self.fulldirall)
		input_table_rows = input_table.shape[0]  # 获取表格行数
		self.input_table_colunms = input_table.shape[1]  # 获取表格列数
		input_table_header = input_table.columns.values.tolist()  # 获取表头
		self.tableWidget.setColumnCount(self.input_table_colunms)  # 设置表格列数
		self.tableWidget.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
		self.tableWidget.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头

		t = 0
		while t >= 0 and t <= input_table_rows:
			csv_reader = csv.reader(open(self.fulldirall, encoding='utf-8'))
			for row in csv_reader:
				if t <= input_table_rows:
					i = 0
					while i >= 0 and i <= self.input_table_colunms - 1:
						self.tableWidget.setItem(t, i, QTableWidgetItem(str(row[i])))
						i += 1
						continue
					t += 1
					continue
		self.tableWidget.removeRow(0)

		m = 0
		while m >= 0 and m <= input_table_rows:
			n = 0
			while n >= 0 and n <= self.input_table_colunms - 1:
				if self.tableWidget.item(m, n) != None:
					self.tableWidget.item(m, n).setTextAlignment(
						Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
				n += 1
				continue
			m += 1
			continue

	def delete_item(self):
		if self.tableWidget.currentItem() != None:
			del_row = self.tableWidget.currentIndex().row() + 1
			with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
				csv_reader = csv.reader(csv_file)
				lines = list(csv_reader)
				del lines[del_row]
			with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(lines)
			find_row = self.tableWidget.currentIndex().row()
			find_item = self.tableWidget.item(find_row, 0).text()
			date_item = self.tableWidget.item(find_row, 1).text()
			stamp_item = self.to_stamp(date_item)
			timeArray = time.localtime(float(stamp_item))
			otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
			cmd = """tell application "Reminders"
		set mylist to list "Tomato"
		set reminderName to "%s" 
		tell mylist
			delete (reminders whose (name is reminderName) and (remind me date is date "%s"))
		end tell
		quit
	end tell""" % (find_item, otherStyleTime)
			cmd2 = """tell application "Calendar"
		tell calendar "Tomato"
			delete (events whose (start date is date "%s") and (summary is "%s"))
		end tell
		quit
	end tell""" % (otherStyleTime, find_item)
			try:
				subprocess.call(['osascript', '-e', cmd])
				subprocess.call(['osascript', '-e', cmd2])
			except Exception as e:
				pass
			self.le4.setText('-')
			self.le4.setText('')

	def delete_all_dones(self):
		self.reader_later()

		all_day = []
		text = 'TIME_SNS'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchContains)
		if items != []:
			for m in range(len(items)):
				item = items[m].row()
				all_day.append(item)

		undone_item = []
		text = 'UNDONE'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchExactly)
		if items != []:
			for m in range(len(items)):
				item = items[m].row()
				undone_item.append(item)
			done_item = list(set(all_day) - set(undone_item))
			delete_list = []
			if done_item != []:
				for j in range(len(done_item)):
					delete_list.append(done_item[j] + 1)
				if delete_list != []:
					remove_list = []
					with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
						csv_reader = csv.reader(csv_file)
						lines = list(csv_reader)
						for lo in range(len(delete_list)):
							remove_list.append(lines[delete_list[lo]])
					if remove_list != []:
						new_lines = []
						for x in range(len(lines)):
							if lines[x] not in remove_list:
								new_lines.append(lines[x])
						with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
							csv_writer = csv.writer(csv_file)
							csv_writer.writerows(new_lines)

		cmd = """tell application "Reminders"
			set myList to list "Tomato"
			delete (reminders in myList) whose completed is true
			quit
		end tell"""
		try:
			subprocess.call(['osascript', '-e', cmd])
		except:
			pass

		self.le4.setText('-')
		self.le4.setText('')

	def export_plan(self):
		home_dir = str(Path.home())
		fj = QFileDialog.getExistingDirectory(self, 'Open', home_dir)
		if fj != '':
			tarname1 = "TomatoAppPath"
			fulldir1 = os.path.join(home_dir, tarname1)
			if not os.path.exists(fulldir1):
				os.mkdir(fulldir1)
			tarname2 = "All.csv"
			fulldir2 = os.path.join(fulldir1, tarname2)
			shutil.copy(fulldir2, fj)

	def on_text_change(self):
		if self.textii1.toPlainText() != '':
			ISOTIMEFORMAT = '%Y-%m-%d diary'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			diary_name = str(theTime) + ".md"
			diary_file = os.path.join(self.fulldir_dia, diary_name)
			if not os.path.exists(diary_file):
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(f'# {theTime}')
			new_content = self.textii1.toPlainText()
			with open(diary_file, 'w', encoding='utf-8') as f0:
				f0.write(new_content)

	def export_diary(self):
		home_dir = str(Path.home())
		fj = QFileDialog.getExistingDirectory(self, 'Open', home_dir)
		if fj != '':
			ISOTIMEFORMAT = '%Y-%m-%d diary'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			diary_name = str(theTime) + ".md"
			diary_file = os.path.join(self.fulldir_dia, diary_name)
			if not os.path.exists(diary_file):
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(f'# {theTime}')
			if os.path.exists(diary_file):
				shutil.copy(diary_file, fj)

	def save_and_done(self):
		if self.tableWidget.currentItem() != None and self.tableWidget.item(self.tableWidget.currentRow(), 4).text() == 'UNDONE':
			self.tableWidget.setItem(self.tableWidget.currentRow(), 4, QTableWidgetItem('DONE'))
			self.tableWidget.item(self.tableWidget.currentRow(), 4).setTextAlignment(
				Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
			self.change_write()
			ori = [['Item', 'Time', 'Length', 'Repeat', 'Status', 'Target times', 'Progress', 'Type', 'Stamp']]
			with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(ori)
			rownum = int(self.tableWidget.rowCount())
			col = int(self.tableWidget.columnCount())
			for n in range(rownum):
				if self.tableWidget.item(n, 1) != None and self.tableWidget.item(n, 1).text() != '':
					oricon = self.tableWidget.item(n, 1).text()
					self.tableWidget.setItem(n, 8, QTableWidgetItem(str(self.to_stamp(oricon))))
			if self.widget0.currentIndex() == 2:
				text = 'DONE'  # 筛选 含有 “test” 的所有行
				items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchExactly)
				if items != []:
					for m in range(len(items)):
						item = items[m].row()
						self.tableWidget.setRowHidden(item, True)  # 隐藏对应的行
			t = 0
			while 0 <= t <= rownum - 1:
				outrow = []
				row = []
				i = 0
				while 0 <= i <= col - 1:
					if self.tableWidget.item(t, i) != None and self.tableWidget.item(t, i).text() != '':
						cell = str(self.tableWidget.item(t, i).text())
						row.append(cell)
					if self.tableWidget.item(t, i) == None:
						row.append('')
					if self.tableWidget.item(t, i).text() == '':
						row.append('-')
					i += 1
					continue
				outrow.append(row)
				with open(self.fulldirall, 'a', encoding='utf8') as csv_file:
					csv_writer = csv.writer(csv_file)
					csv_writer.writerows(outrow)
				t += 1
				continue
			ISOTIMEFORMAT = '%Y-%m-%d diary'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			diary_name = str(theTime) + ".md"
			diary_file = os.path.join(self.fulldir_dia, diary_name)
			contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
			self.textii1.setText(contm)
			self.textii1.ensureCursorVisible()  # 游标可用
			cursor = self.textii1.textCursor()  # 设置游标
			pos = len(self.textii1.toPlainText())  # 获取文本尾部的位置
			cursor.setPosition(pos)  # 游标位置设置为尾部
			self.textii1.setTextCursor(cursor)  # 滚动到游标位置
			if self.tableWidget.item(self.changing_row, 4).text() == 'DONE':
				old_text = self.changing_text
				old_date = self.changing_date
				old_length = self.changing_length
				stamp_item = self.to_stamp(old_date)
				timeArray = time.localtime(float(stamp_item))
				otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
				cmd = """tell application "Reminders"
					set mylist to list "Tomato"
					tell mylist
						set completed of (reminders whose (name is "%s") and (remind me date is date "%s")) to true
					end tell
					quit
				end tell""" % (old_text, otherStyleTime)
				cmd2 = '''tell application "Calendar"
					tell calendar "Tomato"
						delete (events whose (start date is date "%s") and (summary is "%s"))
					end tell
					tell calendar "Tomato-old"
						make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)} 
					end tell
					quit
				end tell
				''' % (otherStyleTime, old_text, old_text, otherStyleTime, otherStyleTime, old_length)
				try:
					subprocess.call(['osascript', '-e', cmd])
					subprocess.call(['osascript', '-e', cmd2])
				except Exception as e:
					pass
				if self.tableWidget.item(self.changing_row, 3).text() != '-':
					outlist = []
					new_time_sns = []
					new_things_list = []
					new1_text = self.tableWidget.item(self.changing_row, 0).text()
					new_time = self.tableWidget.item(self.changing_row, 1).text()
					stamp_item = self.to_stamp(new_time) + 3600 * float(
						self.tableWidget.item(self.changing_row, 3).text())
					timeArray = time.localtime(float(stamp_item))
					otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
					new2_time = time.strftime("%Y-%m-%d %H:%M", timeArray)
					new3_leng = self.tableWidget.item(self.changing_row, 2).text()
					new4_rep = self.tableWidget.item(self.changing_row, 3).text()
					new5_sta = 'UNDONE'
					new6_tar = '-'
					new7_pro = '-'
					new8_typ = 'TIME_SNS'
					new9_sta = stamp_item
					new_time_sns.append(new1_text)
					new_time_sns.append(new2_time)
					new_time_sns.append(new3_leng)
					new_time_sns.append(new4_rep)
					new_time_sns.append(new5_sta)
					new_time_sns.append(new6_tar)
					new_time_sns.append(new7_pro)
					new_time_sns.append(new8_typ)
					new_time_sns.append(new9_sta)
					outlist.append(new_time_sns)
					for i in range(len(new_time_sns)):
						new_things_list.append(str(new_time_sns[i]))
					new_things = ','.join(new_things_list)
					all_things = codecs.open(self.fulldirall, 'r', encoding='utf-8').read()
					all_things_list = all_things.split('\n')
					if not new_things in all_things_list:
						with open(self.fulldirall, 'a', encoding='utf8') as csv_file:
							csv_writer = csv.writer(csv_file)
							csv_writer.writerows(outlist)
						cmd = """tell application "Reminders"
							set eachLine to "%s"
							set mylist to list "Tomato"
							tell mylist
								make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
							end tell
							quit
						end tell""" % (new1_text, otherStyleTime)
						cmd2 = """tell application "Calendar"
						  tell calendar "Tomato"
							make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
						  end tell
						  quit
						end tell""" % (new1_text, otherStyleTime, otherStyleTime, new3_leng)
						try:
							subprocess.call(['osascript', '-e', cmd])
							subprocess.call(['osascript', '-e', cmd2])
						except Exception as e:
							pass
				ISOTIMEFORMAT = '%H:%M:%S '
				theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
				parta = '\n\n- ' + str(theTime)
				partb = 'Completed ' + old_text + ' scheduled for ' + old_date
				partc = ''
				if self.textw1.toPlainText() != '':
					partc = '\n\t- ' + self.textw1.toPlainText()
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(parta + partb + partc)
				contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
				self.textii1.setText(contm)
				self.textii1.ensureCursorVisible()  # 游标可用
				cursor = self.textii1.textCursor()  # 设置游标
				pos = len(self.textii1.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii1.setTextCursor(cursor)  # 滚动到游标位置
				if self.tableWidget.item(self.changing_row, 3).text() != '-':
					record_name = self.tableWidget.item(self.tableWidget.currentRow(), 0).text() + '.csv'
					record_file = os.path.join(self.fulldir_rec, record_name)
					out_list = []
					item_list = []
					comments = 'No comment'
					if self.textw1.toPlainText() != '':
						comments = self.textw1.toPlainText()
					item_list.append(old_date)
					item_list.append(comments)
					out_list.append(item_list)
					with open(record_file, 'a', encoding='utf8') as csv_file:
						csv_writer = csv.writer(csv_file)
						csv_writer.writerows(out_list)
					input_table = pd.read_csv(record_file)
					input_table_rows = input_table.shape[0]  # 获取表格行数
					self.input_table_colunms = input_table.shape[1]  # 获取表格列数
					input_table_header = input_table.columns.values.tolist()  # 获取表头
					self.tableWidget_record.setColumnCount(self.input_table_colunms)  # 设置表格列数
					self.tableWidget_record.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
					self.tableWidget_record.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
					self.tableWidget_record.verticalHeader().setVisible(False)
					t = 0
					while t >= 0 and t <= input_table_rows:
						csv_reader = csv.reader(open(record_file, encoding='utf-8'))
						for row in csv_reader:
							# print(row)
							if t <= input_table_rows:
								i = 0
								while i >= 0 and i <= self.input_table_colunms - 1:
									self.tableWidget_record.setItem(t, i, QTableWidgetItem(str(row[i])))
									i += 1
									continue
								t += 1
								continue
					self.tableWidget_record.removeRow(0)
					m = 0
					while m >= 0 and m <= input_table_rows:
						n = 0
						while n >= 0 and n <= self.input_table_colunms - 1:
							if self.tableWidget_record.item(m, n) != None:
								self.tableWidget_record.item(m, n).setTextAlignment(
									Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
							n += 1
							continue
						m += 1
						continue
					leng_small = self.tableWidget_record.width()
					self.tableWidget_record.setColumnWidth(0, int(leng_small / 2))
					self.tableWidget_record.setColumnWidth(1, int(leng_small / 2))
			self.le4.setText('-')
			self.le4.setText('')
			self.textw1.clear()
			self.tableWidget_record.setCurrentCell(self.tableWidget_record.rowCount() - 1, 0)
			self.orderType = Qt.SortOrder.AscendingOrder
			self.tableWidget.sortByColumn(8, self.orderType)
			self.tableWidget.setCurrentCell(self.changing_row, 0)
			self.changing_bool = 0
		self.tableWidget.clearSelection()
		self.tableWidget.clearFocus()
		self.tableWidget.setCurrentItem(None)

	def export_record(self):
		home_dir = str(Path.home())
		fj = QFileDialog.getExistingDirectory(self, 'Open', home_dir)
		if fj != '' and self.tableWidget.currentItem() != None:
			record_name = self.tableWidget.item(self.tableWidget.currentRow(), 0).text() + '.csv'
			record_file = os.path.join(self.fulldir_rec, record_name)
			if os.path.exists(record_file):
				shutil.copy(record_file, fj)

	def record_write(self):
		if self.tableWidget.currentItem() != None:
			record_name = self.tableWidget.item(self.tableWidget.currentRow(), 0).text() + '.csv'
			record_file = os.path.join(self.fulldir_rec, record_name)
			title_list = [['Time', 'Comments']]
			with open(record_file, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(title_list)
			rownum = int(self.tableWidget_record.rowCount())
			col = int(self.tableWidget_record.columnCount())
			t = 0
			while 0 <= t <= rownum - 1:
				outrow = []
				row = []
				i = 0
				while 0 <= i <= col - 1:
					if self.tableWidget_record.item(t, i) != None and self.tableWidget_record.item(t, i).text() != '':
						cell = str(self.tableWidget_record.item(t, i).text())
						row.append(cell)
					if self.tableWidget_record.item(t, i) == None:
						row.append('')
					if self.tableWidget_record.item(t, i).text() == '':
						row.append('-')
					i += 1
					continue
				outrow.append(row)
				with open(record_file, 'a', encoding='utf8') as csv_file:
					csv_writer = csv.writer(csv_file)
					csv_writer.writerows(outrow)
				t += 1
				continue

	def artTab(self):
		self.tableWidget_freq = QTableWidget()
		input_table = pd.read_csv(self.fulldirall)
		input_table_rows = input_table.shape[0]  # 获取表格行数
		self.input_table_colunms = input_table.shape[1]  # 获取表格列数
		input_table_header = input_table.columns.values.tolist()  # 获取表头
		self.tableWidget_freq.setColumnCount(self.input_table_colunms)  # 设置表格列数
		self.tableWidget_freq.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
		self.tableWidget_freq.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
		self.tableWidget_freq.verticalHeader().setVisible(False)
		self.tableWidget_freq.setAutoScroll(False)

		t = 0
		while t >= 0 and t <= input_table_rows:
			csv_reader = csv.reader(open(self.fulldirall, encoding='utf-8'))
			for row in csv_reader:
				if t <= input_table_rows:
					i = 0
					while i >= 0 and i <= self.input_table_colunms - 1:
						self.tableWidget_freq.setItem(t, i, QTableWidgetItem(str(row[i])))
						i += 1
						continue
					t += 1
					continue
		self.tableWidget_freq.removeRow(0)

		m = 0
		while m >= 0 and m <= input_table_rows:
			n = 0
			while n >= 0 and n <= self.input_table_colunms - 1:
				if self.tableWidget_freq.item(m, n) != None:
					self.tableWidget_freq.item(m, n).setTextAlignment(
						Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
				n += 1
				continue
			m += 1
			continue

		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget_freq.sortByColumn(8, self.orderType)

		'''text = 'FREQ_SNS'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget_freq.findItems(text, Qt.MatchFlag.MatchContains)
		if items != []:
			for i in range(0, input_table_rows):
				self.tableWidget_freq.setRowHidden(i, True)
			for m in range(len(items)):
				item = items[m].row()
				self.tableWidget_freq.setRowHidden(item, False)  # 隐藏对应的行'''

		self.tableWidget_freq.itemClicked.connect(self.freq_write_time)
		self.tableWidget_freq.itemDoubleClicked.connect(self.freq_double_write)
		#self.tableWidget_freq.setFixedHeight(int(self.tableWidget_freq.width()))

		t1 = QWidget()
		self.lf1 = QLineEdit(self)
		self.lf1.setPlaceholderText('Item')
		self.lf1.setFixedHeight(20)

		self.lf2 = QLineEdit(self)
		self.lf2.setPlaceholderText('Target')
		self.lf2.setFixedHeight(20)
		self.lf2.textChanged.connect(self.freq_refresh)
		b1 = QHBoxLayout()
		b1.setContentsMargins(0, 0, 0, 0)
		b1.addWidget(self.lf1)
		b1.addWidget(self.lf2)
		t1.setLayout(b1)

		t1_5 = QWidget()
		btn_t1 = QPushButton('Add!', self)
		btn_t1.clicked.connect(self.add_to_freq)
		btn_t1.setShortcut("Ctrl+Return")
		btn_t1.setFixedHeight(20)
		b1_5 = QHBoxLayout()
		b1_5.setContentsMargins(0, 0, 0, 0)
		b1_5.addWidget(btn_t1)
		t1_5.setLayout(b1_5)

		t1_6 = QWidget()
		b1_6 = QVBoxLayout()
		b1_6.setContentsMargins(0, 0, 0, 0)
		b1_6.addWidget(t1)
		b1_6.addWidget(t1_5)
		t1_6.setLayout(b1_6)

		t2 = QWidget()
		self.widget1 = QComboBox(self)
		self.widget1.setCurrentIndex(0)
		self.widget1.currentIndexChanged.connect(self.freq_index)
		self.widget1.addItems(['All', 'To-do', 'Done'])

		btn_t2 = QPushButton('Delete selected item', self)
		btn_t2.clicked.connect(self.freq_delete)
		btn_t2.setFixedHeight(20)
		self.widget1.setFixedWidth(btn_t2.width() * 2)

		btn_t7 = QPushButton('Delete all DONEs', self)
		btn_t7.clicked.connect(self.freq_delete_dones)
		btn_t7.setFixedHeight(20)

		self.freq1 = QFrame(self)
		self.freq1.setFrameShape(QFrame.Shape.HLine)
		self.freq1.setFrameShadow(QFrame.Shadow.Sunken)

		btn_t3 = QPushButton('Export plan', self)
		btn_t3.clicked.connect(self.export_plan)
		btn_t3.setFixedHeight(20)

		btn_t5 = QPushButton('Export diary', self)
		btn_t5.clicked.connect(self.export_diary)
		btn_t5.setFixedHeight(20)

		btn_t6 = QPushButton('Export records', self)
		btn_t6.clicked.connect(self.export_record)
		btn_t6.setFixedHeight(20)
		b2 = QVBoxLayout()
		b2.setContentsMargins(0, 0, 0, 0)
		b2.addWidget(self.widget1)
		b2.addWidget(btn_t2)
		b2.addWidget(btn_t7)
		b2.addWidget(self.freq1)
		b2.addWidget(btn_t3)
		b2.addWidget(btn_t5)
		b2.addWidget(btn_t6)
		t2.setLayout(b2)

		t3 = QWidget()
		self.textw2= QPlainTextEdit(self)
		self.textw2.setReadOnly(False)
		self.textw2.setObjectName("edit")
		self.textw2.setPlaceholderText('Comments')
		#self.textw2.setMaximumHeight(44)

		btn_t4 = QPushButton('Add 1 time!', self)
		btn_t4.clicked.connect(self.freq_add_time)
		btn_t4.setFixedHeight(20)
		btn_t4.setShortcut("Ctrl+Shift+Return")

		self.freq2 = QFrame(self)
		self.freq2.setFrameShape(QFrame.Shape.HLine)
		self.freq2.setFrameShadow(QFrame.Shadow.Sunken)

		self.lf3 = QLineEdit(self)
		self.lf3.setPlaceholderText('Time (YYYY-MM-DD hh:mm)')
		self.lf3.setFixedHeight(20)

		self.lf4 = QLineEdit(self)
		self.lf4.setPlaceholderText('Length (hours)')
		self.lf4.setFixedHeight(20)

		self.lf5 = QLineEdit(self)
		self.lf5.setPlaceholderText('Repeat (hours)')
		self.lf5.setFixedHeight(20)

		btn_t5 = QPushButton('Copy to Time-sensitive list', self)
		btn_t5.clicked.connect(self.freq_move_time)
		btn_t5.setFixedHeight(20)
		b3 = QVBoxLayout()
		b3.setContentsMargins(0, 0, 0, 0)
		b3.addWidget(self.textw2)
		b3.addWidget(btn_t4)
		b3.addWidget(self.freq2)
		b3.addWidget(self.lf3)
		b3.addWidget(self.lf4)
		b3.addWidget(self.lf5)
		b3.addWidget(btn_t5)
		t3.setLayout(b3)

		t4 = QWidget()
		self.textii2 = QTextEdit(self)
		self.textii2.setReadOnly(False)
		self.textii2.textChanged.connect(self.freq_text_change)
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		if os.path.exists(diary_file):
			contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
			self.textii2.setText(contm)

		self.tableWidget_record2 = QTableWidget()
		self.tableWidget_record2.setObjectName("small")
		self.tableWidget_record2.itemClicked.connect(self.freq_record_write)
		input_table = pd.read_csv(BasePath + 'Record.csv')
		input_table_rows = input_table.shape[0]  # 获取表格行数
		input_table_colunms = input_table.shape[1]  # 获取表格列数
		input_table_header = input_table.columns.values.tolist()  # 获取表头
		self.tableWidget_record2.setColumnCount(input_table_colunms)  # 设置表格列数
		self.tableWidget_record2.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
		self.tableWidget_record2.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
		self.tableWidget_record2.verticalHeader().setVisible(False)
		t = 0
		while t >= 0 and t <= input_table_rows:
			csv_reader = csv.reader(open(BasePath + 'Record.csv', encoding='utf-8'))
			for row in csv_reader:
				# print(row)
				if t <= input_table_rows:
					i = 0
					while i >= 0 and i <= input_table_colunms - 1:
						self.tableWidget_record2.setItem(t, i, QTableWidgetItem(str(row[i])))
						i += 1
						continue
					t += 1
					continue
		self.tableWidget_record2.removeRow(0)
		m = 0
		while m >= 0 and m <= input_table_rows:
			n = 0
			while n >= 0 and n <= input_table_colunms - 1:
				if self.tableWidget_record2.item(m, n) != None:
					self.tableWidget_record2.item(m, n).setTextAlignment(
						Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
				n += 1
				continue
			m += 1
			continue

		b4 = QVBoxLayout()
		b4.setContentsMargins(0, 0, 0, 0)
		b4.addWidget(self.textii2)
		b4.addWidget(self.tableWidget_record2)
		t4.setLayout(b4)

		t5 = QWidget()
		b5 = QHBoxLayout()
		b5.setContentsMargins(0, 0, 0, 0)
		b5.addWidget(t2, 1)
		b5.addWidget(t3, 2)
		b5.addWidget(t4, 2)
		t5.setLayout(b5)
		t5.setFixedHeight(int(self.height() / 2))

		self.page2_box_h = QVBoxLayout()
		self.page2_box_h.addWidget(self.tableWidget_freq)
		self.page2_box_h.addWidget(t1_6)
		self.page2_box_h.addWidget(t5)
		self.art_tab.setLayout(self.page2_box_h)

	def add_to_freq(self):
		if self.lf1.text() != '' and self.lf2.text() != '':
			new_time_sns = []
			outerlist = []
			part1 = self.lf1.text().replace('\n', '')
			ISOTIMEFORMAT = '%Y-%m-%d %H:%M'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			part2 = str(theTime)
			part3 = '-'
			part4 = '-'
			part5 = 'UNDONE'
			part6 = self.lf2.text()
			part7 = '0'
			part8 = 'FREQ_SNS'
			part9 = str(self.to_stamp(part2))
			new_time_sns.append(part1)
			new_time_sns.append(part2)
			new_time_sns.append(part3)
			new_time_sns.append(part4)
			new_time_sns.append(part5)
			new_time_sns.append(part6)
			new_time_sns.append(part7)
			new_time_sns.append(part8)
			new_time_sns.append(part9)
			outerlist.append(new_time_sns)
			with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
				csv_reader = csv.reader(csv_file)
				lines = list(csv_reader)
				lines = lines + outerlist
			with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(lines)
			self.lf1.clear()
			self.lf2.clear()

	def freq_write_time(self):
		ori = [['Item', 'Time', 'Length', 'Repeat', 'Status', 'Target times', 'Progress', 'Type', 'Stamp']]
		with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerows(ori)
		rownum = int(self.tableWidget_freq.rowCount())
		col = int(self.tableWidget_freq.columnCount())
		for n in range(rownum):
			if self.tableWidget_freq.item(n, 1) != None and self.tableWidget_freq.item(n, 1).text() != '':
				oricon = self.tableWidget_freq.item(n, 1).text()
				self.tableWidget_freq.setItem(n, 8, QTableWidgetItem(str(self.to_stamp(oricon))))
		if self.freq_double == 1:
			now_target = int(self.tableWidget_freq.item(self.freq_changing_row, 6).text())
			if now_target >= self.freq_target:
				self.tableWidget_freq.setItem(self.freq_changing_row, 4, QTableWidgetItem('DONE'))
		t = 0
		while 0 <= t <= rownum - 1:
			outrow = []
			row = []
			i = 0
			while 0 <= i <= col - 1:
				if self.tableWidget_freq.item(t, i) != None and self.tableWidget_freq.item(t, i).text() != '':
					cell = str(self.tableWidget_freq.item(t, i).text())
					row.append(cell)
				if self.tableWidget_freq.item(t, i) == None:
					row.append('')
				if self.tableWidget_freq.item(t, i).text() == '':
					row.append('-')
				i += 1
				continue
			outrow.append(row)
			with open(self.fulldirall, 'a', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(outrow)
			t += 1
			continue
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
		self.textii2.setText(contm)
		self.textii2.ensureCursorVisible()  # 游标可用
		cursor = self.textii2.textCursor()  # 设置游标
		pos = len(self.textii2.toPlainText())  # 获取文本尾部的位置
		cursor.setPosition(pos)  # 游标位置设置为尾部
		self.textii2.setTextCursor(cursor)  # 滚动到游标位置
		if self.tableWidget_freq.currentItem() != None:
			record2_name = self.tableWidget_freq.item(self.tableWidget_freq.currentRow(), 0).text() + '.csv'
			record2_file = os.path.join(self.fulldir_rec, record2_name)
			if not os.path.exists(record2_file):
				title_list = [['Time', 'Comments']]
				with open(record2_file, 'w', encoding='utf8') as csv_file:
					csv_writer = csv.writer(csv_file)
					csv_writer.writerows(title_list)
			if os.path.exists(record2_file):
				input_table = pd.read_csv(record2_file)
				input_table_rows = input_table.shape[0]  # 获取表格行数
				input_table_colunms = input_table.shape[1]  # 获取表格列数
				input_table_header = input_table.columns.values.tolist()  # 获取表头
				self.tableWidget_record2.setColumnCount(input_table_colunms)  # 设置表格列数
				self.tableWidget_record2.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
				self.tableWidget_record2.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
				self.tableWidget_record2.verticalHeader().setVisible(False)

				t = 0
				while t >= 0 and t <= input_table_rows:
					csv_reader = csv.reader(open(record2_file, encoding='utf-8'))
					for row in csv_reader:
						if t <= input_table_rows:
							i = 0
							while i >= 0 and i <= input_table_colunms - 1:
								self.tableWidget_record2.setItem(t, i, QTableWidgetItem(str(row[i])))
								i += 1
								continue
							t += 1
							continue
				self.tableWidget_record2.removeRow(0)

				m = 0
				while m >= 0 and m <= input_table_rows:
					n = 0
					while n >= 0 and n <= input_table_colunms - 1:
						if self.tableWidget_record2.item(m, n) != None:
							self.tableWidget_record2.item(m, n).setTextAlignment(
								Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
						n += 1
						continue
					m += 1
					continue
				leng_small = self.tableWidget_record2.width()
				self.tableWidget_record2.setColumnWidth(0, int(leng_small / 2))
				self.tableWidget_record2.setColumnWidth(1, int(leng_small / 2))
		if self.freq_double == 1:
			if (self.freq_changing_column == 0 or 5) and self.tableWidget_freq.item(self.freq_changing_row, 4).text() == 'UNDONE':
				pass
			if self.freq_changing_column == 6:
				now_target = int(self.tableWidget_freq.item(self.freq_changing_row, 6).text())
				if now_target < self.freq_target:
					old_text = self.tableWidget_freq.item(self.freq_changing_row, 0).text()
					new_times = self.tableWidget_freq.item(self.freq_changing_row, 6).text()
					ISOTIMEFORMAT = '%H:%M:%S '
					theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
					parta = '\n\n- ' + str(theTime)
					partb = 'Completed ' + old_text + '. It is now ' + new_times + ' times in all.'
					partc = ''
					if self.textw2.toPlainText() != '':
						partc = '\n\t- ' + self.textw2.toPlainText()
					with open(diary_file, 'a', encoding='utf-8') as f0:
						f0.write(parta + partb + partc)
					contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
					self.textii2.setText(contm)
					self.textii2.ensureCursorVisible()  # 游标可用
					cursor = self.textii2.textCursor()  # 设置游标
					pos = len(self.textii2.toPlainText())  # 获取文本尾部的位置
					cursor.setPosition(pos)  # 游标位置设置为尾部
					self.textii2.setTextCursor(cursor)  # 滚动到游标位置
				if now_target >= self.freq_target:
					old_text = self.tableWidget_freq.item(self.freq_changing_row, 0).text()
					new_times = self.tableWidget_freq.item(self.freq_changing_row, 6).text()
					ISOTIMEFORMAT = '%H:%M:%S '
					theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
					parta = '\n\n- ' + str(theTime)
					partb = 'Completed ' + old_text + '. It is now ' + new_times + ' times in all. You have fullfilled this goal.'
					partc = ''
					if self.textw2.toPlainText() != '':
						partc = '\n\t- ' + self.textw2.toPlainText()
					with open(diary_file, 'a', encoding='utf-8') as f0:
						f0.write(parta + partb + partc)
					contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
					self.textii2.setText(contm)
					self.textii2.ensureCursorVisible()  # 游标可用
					cursor = self.textii2.textCursor()  # 设置游标
					pos = len(self.textii2.toPlainText())  # 获取文本尾部的位置
					cursor.setPosition(pos)  # 游标位置设置为尾部
					self.textii2.setTextCursor(cursor)  # 滚动到游标位置

				record_name = self.tableWidget_freq.item(self.freq_changing_row, 0).text() + '.csv'
				record_file = os.path.join(self.fulldir_rec, record_name)
				out_list = []
				item_list = []
				comments = 'No comment'
				if self.textw2.toPlainText() != '':
					comments = self.textw2.toPlainText()
				ISOTIMEFORMAT = '%Y-%m-%d %H:%M'
				nowDate = datetime.datetime.now().strftime(ISOTIMEFORMAT)
				item_list.append(nowDate)
				item_list.append(comments)
				out_list.append(item_list)
				if os.path.exists(record_file):
					with open(record_file, 'a', encoding='utf8') as csv_file:
						csv_writer = csv.writer(csv_file)
						csv_writer.writerows(out_list)
					input_table = pd.read_csv(record_file)
					input_table_rows = input_table.shape[0]  # 获取表格行数
					self.input_table_colunms = input_table.shape[1]  # 获取表格列数
					input_table_header = input_table.columns.values.tolist()  # 获取表头
					self.tableWidget_record2.setColumnCount(self.input_table_colunms)  # 设置表格列数
					self.tableWidget_record2.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
					self.tableWidget_record2.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
					self.tableWidget_record2.verticalHeader().setVisible(False)
					t = 0
					while t >= 0 and t <= input_table_rows:
						csv_reader = csv.reader(open(record_file, encoding='utf-8'))
						for row in csv_reader:
							if t <= input_table_rows:
								i = 0
								while i >= 0 and i <= self.input_table_colunms - 1:
									self.tableWidget_record2.setItem(t, i, QTableWidgetItem(str(row[i])))
									i += 1
									continue
								t += 1
								continue
					self.tableWidget_record2.removeRow(0)
					m = 0
					while m >= 0 and m <= input_table_rows:
						n = 0
						while n >= 0 and n <= self.input_table_colunms - 1:
							if self.tableWidget_record2.item(m, n) != None:
								self.tableWidget_record2.item(m, n).setTextAlignment(
									Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
							n += 1
							continue
						m += 1
						continue
					leng_small = self.tableWidget_record2.width()
					self.tableWidget_record2.setColumnWidth(0, int(leng_small / 2))
					self.tableWidget_record2.setColumnWidth(1, int(leng_small / 2))
			if self.freq_changing_column == 4 and self.tableWidget_freq.item(self.freq_changing_row, 4).text() == 'DONE':
				old_text = self.tableWidget_freq.item(self.freq_changing_row, 0).text()
				new_times = self.tableWidget_freq.item(self.freq_changing_row, 6).text()
				ISOTIMEFORMAT = '%H:%M:%S '
				theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
				parta = '\n\n- ' + str(theTime)
				partb = 'Completed ' + old_text + '. It is now ' + new_times + ' times in all. You have fullfilled this goal.'
				partc = ''
				if self.textw2.toPlainText() != '':
					partc = '\n\t- ' + self.textw2.toPlainText()
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(parta + partb + partc)
				contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
				self.textii2.setText(contm)
				self.textii2.ensureCursorVisible()  # 游标可用
				cursor = self.textii2.textCursor()  # 设置游标
				pos = len(self.textii2.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii2.setTextCursor(cursor)  # 滚动到游标位置

				record_name = self.tableWidget_freq.item(self.freq_changing_row, 0).text() + '.csv'
				record_file = os.path.join(self.fulldir_rec, record_name)
				out_list = []
				item_list = []
				comments = 'No comment'
				if self.textw2.toPlainText() != '':
					comments = self.textw2.toPlainText()
				ISOTIMEFORMAT = '%Y-%m-%d %H:%M'
				nowDate = datetime.datetime.now().strftime(ISOTIMEFORMAT)
				item_list.append(nowDate)
				item_list.append(comments)
				out_list.append(item_list)
				if os.path.exists(record_file):
					with open(record_file, 'a', encoding='utf8') as csv_file:
						csv_writer = csv.writer(csv_file)
						csv_writer.writerows(out_list)
					input_table = pd.read_csv(record_file)
					input_table_rows = input_table.shape[0]  # 获取表格行数
					self.input_table_colunms = input_table.shape[1]  # 获取表格列数
					input_table_header = input_table.columns.values.tolist()  # 获取表头
					self.tableWidget_record2.setColumnCount(self.input_table_colunms)  # 设置表格列数
					self.tableWidget_record2.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
					self.tableWidget_record2.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
					self.tableWidget_record2.verticalHeader().setVisible(False)
					t = 0
					while t >= 0 and t <= input_table_rows:
						csv_reader = csv.reader(open(record_file, encoding='utf-8'))
						for row in csv_reader:
							if t <= input_table_rows:
								i = 0
								while i >= 0 and i <= self.input_table_colunms - 1:
									self.tableWidget_record2.setItem(t, i, QTableWidgetItem(str(row[i])))
									i += 1
									continue
								t += 1
								continue
					self.tableWidget_record2.removeRow(0)
					m = 0
					while m >= 0 and m <= input_table_rows:
						n = 0
						while n >= 0 and n <= self.input_table_colunms - 1:
							if self.tableWidget_record2.item(m, n) != None:
								self.tableWidget_record2.item(m, n).setTextAlignment(
									Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
							n += 1
							continue
						m += 1
						continue
					leng_small = self.tableWidget_record2.width()
					self.tableWidget_record2.setColumnWidth(0, int(leng_small / 2))
					self.tableWidget_record2.setColumnWidth(1, int(leng_small / 2))
			self.lf2.setText('-')
			self.lf2.clear()
			self.textw2.clear()
			self.tableWidget_freq.clearSelection()
			self.tableWidget_freq.clearFocus()
			self.tableWidget_freq.setCurrentItem(None)
		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget_freq.sortByColumn(8, self.orderType)
		self.tableWidget_record2.setCurrentCell(self.tableWidget_record2.rowCount() - 1, 0)
		self.freq_double = 0

	def freq_double_write(self):
		self.freq_double = 1
		self.freq_changing_row = self.tableWidget_freq.currentIndex().row()
		self.freq_changing_column = self.tableWidget_freq.currentIndex().column()
		self.freq_target = int(self.tableWidget_freq.item(self.freq_changing_row, 5).text())

	def freq_index(self, i):
		self.freq_readlater()

		input_table = pd.read_csv(self.fulldirall)
		input_table_rows = input_table.shape[0]  # 获取表格行数
		for x in range(0, input_table_rows):
			self.tableWidget_freq.setRowHidden(x, False)
		all_freq = []
		text = 'FREQ_SNS'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget_freq.findItems(text, Qt.MatchFlag.MatchContains)
		if items != []:
			for x in range(0, input_table_rows):
				self.tableWidget_freq.setRowHidden(x, True)
			for m in range(len(items)):
				item = items[m].row()
				all_freq.append(item)

		if i == 0:
			for m in range(len(all_freq)):
				item = all_freq[m]
				self.tableWidget_freq.setRowHidden(item, False)  # 隐藏对应的行
		if i == 1:
			undone_item = []
			text = 'UNDONE'  # 筛选 含有 “test” 的所有行
			items = self.tableWidget_freq.findItems(text, Qt.MatchFlag.MatchExactly)
			if items != []:
				for x in range(0, input_table_rows):
					self.tableWidget_freq.setRowHidden(x, True)
				for m in range(len(items)):
					item = items[m].row()
					undone_item.append(item)
				done_item = list(set(all_freq) - set(undone_item))
				todo_item = list(set(all_freq) - set(done_item))
				if todo_item != []:
					for k in range(len(todo_item)):
						item = todo_item[k]
						self.tableWidget_freq.setRowHidden(item, False)  # 隐藏对应的行
		if i == 2:
			undone_item = []
			text = 'UNDONE'  # 筛选 含有 “test” 的所有行
			items = self.tableWidget_freq.findItems(text, Qt.MatchFlag.MatchExactly)
			if items != []:
				for x in range(0, input_table_rows):
					self.tableWidget_freq.setRowHidden(x, True)
				for m in range(len(items)):
					item = items[m].row()
					undone_item.append(item)
				done_done = list(set(all_freq) - set(undone_item))
				if done_done != []:
					for r in range(len(done_done)):
						item = done_done[r]
						self.tableWidget_freq.setRowHidden(item, False)  # 隐藏对应的行
		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget_freq.sortByColumn(8, self.orderType)

	def freq_refresh(self):
		nowindex = self.widget1.currentIndex()
		if nowindex == 0:
			self.widget1.setCurrentIndex(-1)
		if nowindex != 0:
			self.widget1.setCurrentIndex(0)
		self.widget1.setCurrentIndex(nowindex)

	def freq_readlater(self):
		input_table = pd.read_csv(self.fulldirall)
		input_table_rows = input_table.shape[0]  # 获取表格行数
		# print(input_table_rows)
		self.input_table_colunms = input_table.shape[1]  # 获取表格列数
		# print(input_table_colunms)
		input_table_header = input_table.columns.values.tolist()  # 获取表头
		self.tableWidget_freq.setColumnCount(self.input_table_colunms)  # 设置表格列数
		self.tableWidget_freq.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
		self.tableWidget_freq.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
		self.tableWidget_freq.verticalHeader().setVisible(False)

		t = 0
		while t >= 0 and t <= input_table_rows:
			csv_reader = csv.reader(open(self.fulldirall, encoding='utf-8'))
			for row in csv_reader:
				# print(row)
				if t <= input_table_rows:
					i = 0
					while i >= 0 and i <= self.input_table_colunms - 1:
						self.tableWidget_freq.setItem(t, i, QTableWidgetItem(str(row[i])))
						i += 1
						continue
					t += 1
					continue
		self.tableWidget_freq.removeRow(0)

		m = 0
		while m >= 0 and m <= input_table_rows:
			n = 0
			while n >= 0 and n <= self.input_table_colunms - 1:
				if self.tableWidget_freq.item(m, n) != None:
					self.tableWidget_freq.item(m, n).setTextAlignment(
						Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
				n += 1
				continue
			m += 1
			continue

	def freq_delete(self):
		if self.tableWidget_freq.currentItem() != None:
			del_row = self.tableWidget_freq.currentIndex().row() + 1
			with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
				csv_reader = csv.reader(csv_file)
				lines = list(csv_reader)
				del lines[del_row]
			with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(lines)
			self.lf2.setText('-')
			self.lf2.clear()

	def freq_delete_dones(self):
		self.freq_readlater()

		all_day = []
		text = 'FREQ_SNS'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget_freq.findItems(text, Qt.MatchFlag.MatchContains)
		if items != []:
			for m in range(len(items)):
				item = items[m].row()
				all_day.append(item)

		undone_item = []
		text = 'UNDONE'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget_freq.findItems(text, Qt.MatchFlag.MatchExactly)
		if items != []:
			for m in range(len(items)):
				item = items[m].row()
				undone_item.append(item)
			done_item = list(set(all_day) - set(undone_item))
			delete_list = []
			if done_item != []:
				for j in range(len(done_item)):
					delete_list.append(done_item[j] + 1)
				if delete_list != []:
					remove_list = []
					with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
						csv_reader = csv.reader(csv_file)
						lines = list(csv_reader)
						for lo in range(len(delete_list)):
							remove_list.append(lines[delete_list[lo]])
					if remove_list != []:
						new_lines = []
						for x in range(len(lines)):
							if lines[x] not in remove_list:
								new_lines.append(lines[x])
						with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
							csv_writer = csv.writer(csv_file)
							csv_writer.writerows(new_lines)
		self.lf2.setText('-')
		self.lf2.clear()

	def freq_text_change(self):
		if self.textii2.toPlainText() != '':
			ISOTIMEFORMAT = '%Y-%m-%d diary'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			diary_name = str(theTime) + ".md"
			diary_file = os.path.join(self.fulldir_dia, diary_name)
			if not os.path.exists(diary_file):
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(f'# {theTime}')
			new_content = self.textii2.toPlainText()
			with open(diary_file, 'w', encoding='utf-8') as f0:
				f0.write(new_content)

	def freq_record_write(self):
		if self.tableWidget_freq.currentItem() != None:
			record2_name = self.tableWidget_freq.item(self.tableWidget_freq.currentRow(), 0).text() + '.csv'
			record2_file = os.path.join(self.fulldir_rec, record2_name)
			title_list = [['Time', 'Comments']]
			with open(record2_file, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(title_list)
			rownum = int(self.tableWidget_record2.rowCount())
			col = int(self.tableWidget_record2.columnCount())
			t = 0
			while 0 <= t <= rownum - 1:
				outrow = []
				row = []
				i = 0
				while 0 <= i <= col - 1:
					if self.tableWidget_record2.item(t, i) != None and self.tableWidget_record2.item(t, i).text() != '':
						cell = str(self.tableWidget_record2.item(t, i).text())
						row.append(cell)
					if self.tableWidget_record2.item(t, i) == None:
						row.append('')
					if self.tableWidget_record2.item(t, i).text() == '':
						row.append('-')
					i += 1
					continue
				outrow.append(row)
				with open(record2_file, 'a', encoding='utf8') as csv_file:
					csv_writer = csv.writer(csv_file)
					csv_writer.writerows(outrow)
				t += 1
				continue

	def freq_add_time(self):
		if self.tableWidget_freq.currentItem() != None:
			current_row = self.tableWidget_freq.currentIndex().row()
			self.freq_target = int(self.tableWidget_freq.item(current_row, 5).text())

			process_time = int(self.tableWidget_freq.item(current_row, 6).text()) + 1
			self.tableWidget_freq.setItem(current_row, 6, QTableWidgetItem(str(process_time)))

			now_target = int(self.tableWidget_freq.item(current_row, 6).text())
			if now_target >= self.freq_target:
				self.tableWidget_freq.setItem(current_row, 4, QTableWidgetItem('DONE'))

			ori = [['Item', 'Time', 'Length', 'Repeat', 'Status', 'Target times', 'Progress', 'Type', 'Stamp']]
			with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(ori)
			rownum = int(self.tableWidget_freq.rowCount())
			col = int(self.tableWidget_freq.columnCount())
			for n in range(rownum):
				if self.tableWidget_freq.item(n, 1) != None and self.tableWidget_freq.item(n, 1).text() != '':
					oricon = self.tableWidget_freq.item(n, 1).text()
					self.tableWidget_freq.setItem(n, 8, QTableWidgetItem(str(self.to_stamp(oricon))))
			t = 0
			while 0 <= t <= rownum - 1:
				outrow = []
				row = []
				i = 0
				while 0 <= i <= col - 1:
					if self.tableWidget_freq.item(t, i) != None and self.tableWidget_freq.item(t, i).text() != '':
						cell = str(self.tableWidget_freq.item(t, i).text())
						row.append(cell)
					if self.tableWidget_freq.item(t, i) == None:
						row.append('')
					if self.tableWidget_freq.item(t, i).text() == '':
						row.append('-')
					i += 1
					continue
				outrow.append(row)
				with open(self.fulldirall, 'a', encoding='utf8') as csv_file:
					csv_writer = csv.writer(csv_file)
					csv_writer.writerows(outrow)
				t += 1
				continue

			self.freq_double = 1
			self.freq_changing_row = self.tableWidget_freq.currentIndex().row()
			self.freq_changing_column = self.tableWidget_freq.currentIndex().column()

			ISOTIMEFORMAT = '%Y-%m-%d diary'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			diary_name = str(theTime) + ".md"
			diary_file = os.path.join(self.fulldir_dia, diary_name)

			if now_target < self.freq_target:
				old_text = self.tableWidget_freq.item(self.freq_changing_row, 0).text()
				new_times = self.tableWidget_freq.item(self.freq_changing_row, 6).text()
				ISOTIMEFORMAT = '%H:%M:%S '
				theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
				parta = '\n\n- ' + str(theTime)
				partb = 'Completed ' + old_text + '. It is now ' + new_times + ' times in all.'
				partc = ''
				if self.textw2.toPlainText() != '':
					partc = '\n\t- ' + self.textw2.toPlainText()
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(parta + partb + partc)
				contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
				self.textii2.setText(contm)
				self.textii2.ensureCursorVisible()  # 游标可用
				cursor = self.textii2.textCursor()  # 设置游标
				pos = len(self.textii2.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii2.setTextCursor(cursor)  # 滚动到游标位置
			if now_target >= self.freq_target:
				old_text = self.tableWidget_freq.item(self.freq_changing_row, 0).text()
				new_times = self.tableWidget_freq.item(self.freq_changing_row, 6).text()
				ISOTIMEFORMAT = '%H:%M:%S '
				theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
				parta = '\n\n- ' + str(theTime)
				partb = 'Completed ' + old_text + '. It is now ' + new_times + ' times in all. You have fullfilled this goal.'
				partc = ''
				if self.textw2.toPlainText() != '':
					partc = '\n\t- ' + self.textw2.toPlainText()
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(parta + partb + partc)
				contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
				self.textii2.setText(contm)
				self.textii2.ensureCursorVisible()  # 游标可用
				cursor = self.textii2.textCursor()  # 设置游标
				pos = len(self.textii2.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii2.setTextCursor(cursor)  # 滚动到游标位置

			record_name = self.tableWidget_freq.item(self.freq_changing_row, 0).text() + '.csv'
			record_file = os.path.join(self.fulldir_rec, record_name)
			out_list = []
			item_list = []
			comments = 'No comment'
			if self.textw2.toPlainText() != '':
				comments = self.textw2.toPlainText()
			ISOTIMEFORMAT = '%Y-%m-%d %H:%M'
			nowDate = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			item_list.append(nowDate)
			item_list.append(comments)
			out_list.append(item_list)
			if os.path.exists(record_file):
				with open(record_file, 'a', encoding='utf8') as csv_file:
					csv_writer = csv.writer(csv_file)
					csv_writer.writerows(out_list)
				input_table = pd.read_csv(record_file)
				input_table_rows = input_table.shape[0]  # 获取表格行数
				self.input_table_colunms = input_table.shape[1]  # 获取表格列数
				input_table_header = input_table.columns.values.tolist()  # 获取表头
				self.tableWidget_record2.setColumnCount(self.input_table_colunms)  # 设置表格列数
				self.tableWidget_record2.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
				self.tableWidget_record2.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
				self.tableWidget_record2.verticalHeader().setVisible(False)
				t = 0
				while t >= 0 and t <= input_table_rows:
					csv_reader = csv.reader(open(record_file, encoding='utf-8'))
					for row in csv_reader:
						if t <= input_table_rows:
							i = 0
							while i >= 0 and i <= self.input_table_colunms - 1:
								self.tableWidget_record2.setItem(t, i, QTableWidgetItem(str(row[i])))
								i += 1
								continue
							t += 1
							continue
				self.tableWidget_record2.removeRow(0)
				m = 0
				while m >= 0 and m <= input_table_rows:
					n = 0
					while n >= 0 and n <= self.input_table_colunms - 1:
						if self.tableWidget_record2.item(m, n) != None:
							self.tableWidget_record2.item(m, n).setTextAlignment(
								Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
						n += 1
						continue
					m += 1
					continue
				leng_small = self.tableWidget_record2.width()
				self.tableWidget_record2.setColumnWidth(0, int(leng_small / 2))
				self.tableWidget_record2.setColumnWidth(1, int(leng_small / 2))
			self.orderType = Qt.SortOrder.AscendingOrder
			self.tableWidget_freq.sortByColumn(8, self.orderType)
			self.textw2.clear()
			self.tableWidget_record2.setCurrentCell(self.tableWidget_record2.rowCount() - 1, 0)
			self.lf2.setText('-')
			self.lf2.clear()
			self.tableWidget_freq.setCurrentCell(self.freq_changing_row, 0)
			self.freq_double = 0
		self.tableWidget_freq.clearSelection()
		self.tableWidget_freq.clearFocus()
		self.tableWidget_freq.setCurrentItem(None)

	def freq_move_time(self):  # copy to time
		if self.tableWidget_freq.currentItem() != None:
			new_time_sns = []
			outerlist = []
			ite1_inp = self.tableWidget_freq.item(self.tableWidget_freq.currentIndex().row(), 0).text()
			tim2_inp = self.lf3.text()
			len3_inp = self.lf4.text()
			rep4_inp = self.lf5.text()
			if rep4_inp == '':
				rep4_inp = '-'
			sta5_inp = 'UNDONE'
			tar6_inp = '-'
			pro7_inp = '-'
			typ8_inp = 'TIME_SNS'
			sta9_inp = ''
			if ite1_inp != '' and tim2_inp != '' and len3_inp != '' and self.tableWidget_freq.item(self.tableWidget_freq.currentIndex().row(), 0) != None:
				try:
					sta9_inp = str(self.to_stamp(tim2_inp))
				except Exception as e:
					pass
				if sta9_inp != '':
					new_time_sns.append(ite1_inp)
					new_time_sns.append(tim2_inp)
					new_time_sns.append(len3_inp)
					new_time_sns.append(rep4_inp)
					new_time_sns.append(sta5_inp)
					new_time_sns.append(tar6_inp)
					new_time_sns.append(pro7_inp)
					new_time_sns.append(typ8_inp)
					new_time_sns.append(sta9_inp)
					outerlist.append(new_time_sns)
					with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
						csv_reader = csv.reader(csv_file)
						lines = list(csv_reader)
						lines = lines + outerlist
					with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
						csv_writer = csv.writer(csv_file)
						csv_writer.writerows(lines)
					timeArray = time.localtime(float(sta9_inp))
					otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
					cmd = """tell application "Reminders"
						set eachLine to "%s"
						set mylist to list "Tomato"
						tell mylist
							make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
						end tell
						quit
					end tell""" % (ite1_inp, otherStyleTime)
					cmd2 = """tell application "Calendar"
					  tell calendar "Tomato"
						make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
					  end tell
					  quit
					end tell""" % (ite1_inp, otherStyleTime, otherStyleTime, len3_inp)
					try:
						subprocess.call(['osascript', '-e', cmd])
						subprocess.call(['osascript', '-e', cmd2])
						self.lf3.clear()
						self.lf4.clear()
						self.lf5.clear()
						self.le4.setText('-')
						self.le4.clear()
					except Exception as e:
						pass

	def inspiTab(self):
		self.tableWidget_memo = QTableWidget()
		input_table = pd.read_csv(self.fulldirall)
		input_table_rows = input_table.shape[0]  # 获取表格行数
		self.input_table_colunms = input_table.shape[1]  # 获取表格列数
		input_table_header = input_table.columns.values.tolist()  # 获取表头
		self.tableWidget_memo.setColumnCount(self.input_table_colunms)  # 设置表格列数
		self.tableWidget_memo.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
		self.tableWidget_memo.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
		self.tableWidget_memo.verticalHeader().setVisible(False)
		self.tableWidget_memo.setAutoScroll(False)

		t = 0
		while t >= 0 and t <= input_table_rows:
			csv_reader = csv.reader(open(self.fulldirall, encoding='utf-8'))
			for row in csv_reader:
				# print(row)
				if t <= input_table_rows:
					i = 0
					while i >= 0 and i <= self.input_table_colunms - 1:
						self.tableWidget_memo.setItem(t, i, QTableWidgetItem(str(row[i])))
						i += 1
						continue
					t += 1
					continue
		self.tableWidget_memo.removeRow(0)

		m = 0
		while m >= 0 and m <= input_table_rows:
			n = 0
			while n >= 0 and n <= self.input_table_colunms - 1:
				if self.tableWidget_memo.item(m, n) != None:
					self.tableWidget_memo.item(m, n).setTextAlignment(
						Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
				n += 1
				continue
			m += 1
			continue

		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget_memo.sortByColumn(8, self.orderType)

		text = 'MEMO_SNS'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget_memo.findItems(text, Qt.MatchFlag.MatchContains)
		if items != []:
			for i in range(0, input_table_rows):
				self.tableWidget_memo.setRowHidden(i, True)
			for m in range(len(items)):
				item = items[m].row()
				self.tableWidget_memo.setRowHidden(item, False)  # 隐藏对应的行

		self.tableWidget_memo.itemClicked.connect(self.memo_click_write)
		self.tableWidget_memo.itemDoubleClicked.connect(self.memo_double)
		#self.tableWidget_memo.setFixedHeight(int(self.tableWidget_memo.width()))

		t1 = QWidget()
		self.lm1 = QLineEdit(self)
		self.lm1.setPlaceholderText('Item')
		self.lm1.setFixedHeight(20)
		self.lm1.textChanged.connect(self.memo_refresh)

		b1 = QVBoxLayout()
		b1.setContentsMargins(0, 0, 0, 0)
		b1.addWidget(self.lm1)
		t1.setLayout(b1)

		t1_5 = QWidget()
		btn_t1 = QPushButton('Add!', self)
		btn_t1.clicked.connect(self.memo_add)
		btn_t1.setShortcut("Ctrl+Return")
		btn_t1.setFixedHeight(20)
		b1_5 = QHBoxLayout()
		b1_5.setContentsMargins(0, 0, 0, 0)
		b1_5.addWidget(btn_t1)
		t1_5.setLayout(b1_5)

		t1_6 = QWidget()
		b1_6 = QVBoxLayout()
		b1_6.setContentsMargins(0, 0, 0, 0)
		b1_6.addWidget(t1)
		b1_6.addWidget(t1_5)
		t1_6.setLayout(b1_6)

		t2 = QWidget()
		self.widget2 = QComboBox(self)
		self.widget2.setCurrentIndex(0)
		self.widget2.currentIndexChanged.connect(self.memo_index_change)
		self.widget2.addItems(['All', 'To-do', 'Done'])

		btn_t2 = QPushButton('Delete selected item', self)
		btn_t2.clicked.connect(self.memo_delete)
		btn_t2.setFixedHeight(20)
		self.widget2.setFixedWidth(btn_t2.width() * 2)

		btn_t7 = QPushButton('Delete all DONEs', self)
		btn_t7.clicked.connect(self.memo_delete_dones)
		btn_t7.setFixedHeight(20)

		self.memo1 = QFrame(self)
		self.memo1.setFrameShape(QFrame.Shape.HLine)
		self.memo1.setFrameShadow(QFrame.Shadow.Sunken)

		btn_t3 = QPushButton('Export plan', self)
		btn_t3.clicked.connect(self.export_plan)
		btn_t3.setFixedHeight(20)

		btn_t5 = QPushButton('Export diary', self)
		btn_t5.clicked.connect(self.export_diary)
		btn_t5.setFixedHeight(20)

		btn_t6 = QPushButton('Export records', self)
		btn_t6.clicked.connect(self.export_record)
		btn_t6.setFixedHeight(20)
		b2 = QVBoxLayout()
		b2.setContentsMargins(0, 0, 0, 0)
		b2.addWidget(self.widget2)
		b2.addWidget(btn_t2)
		b2.addWidget(btn_t7)
		b2.addWidget(self.memo1)
		b2.addWidget(btn_t3)
		b2.addWidget(btn_t5)
		b2.addWidget(btn_t6)
		t2.setLayout(b2)

		t3 = QWidget()
		self.textw3 = QPlainTextEdit(self)
		self.textw3.setReadOnly(False)
		self.textw3.setObjectName("edit")
		self.textw3.setPlaceholderText('Comments')
		#self.textw3.setMaximumHeight(44)

		btn_t4 = QPushButton('Done this memo!', self)
		btn_t4.clicked.connect(self.memo_done_memo)
		btn_t4.setFixedHeight(20)
		btn_t4.setShortcut("Ctrl+Shift+Return")

		self.memo2 = QFrame(self)
		self.memo2.setFrameShape(QFrame.Shape.HLine)
		self.memo2.setFrameShadow(QFrame.Shadow.Sunken)

		self.lm3 = QLineEdit(self)
		self.lm3.setPlaceholderText('Time (YYYY-MM-DD hh:mm)')
		self.lm3.setFixedHeight(20)

		self.lm4 = QLineEdit(self)
		self.lm4.setPlaceholderText('Length (hours)')
		self.lm4.setFixedHeight(20)

		self.lm5 = QLineEdit(self)
		self.lm5.setPlaceholderText('Repeat (hours)')
		self.lm5.setFixedHeight(20)

		btn_t5 = QPushButton('Copy to Time-sensitive list', self)
		btn_t5.clicked.connect(self.memo_copy_to_time)
		btn_t5.setFixedHeight(20)
		b3 = QVBoxLayout()
		b3.setContentsMargins(0, 0, 0, 0)
		b3.addWidget(self.textw3)
		b3.addWidget(btn_t4)
		b3.addWidget(self.memo2)
		b3.addWidget(self.lm3)
		b3.addWidget(self.lm4)
		b3.addWidget(self.lm5)
		b3.addWidget(btn_t5)
		t3.setLayout(b3)

		t4 = QWidget()
		self.textii3 = QTextEdit(self)
		self.textii3.setReadOnly(False)
		self.textii3.textChanged.connect(self.memo_text_change)
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		if os.path.exists(diary_file):
			contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
			self.textii3.setText(contm)

		b4 = QVBoxLayout()
		b4.setContentsMargins(0, 0, 0, 0)
		b4.addWidget(self.textii3)
		t4.setLayout(b4)

		t5 = QWidget()
		b5 = QHBoxLayout()
		b5.setContentsMargins(0, 0, 0, 0)
		b5.addWidget(t2, 1)
		b5.addWidget(t3, 2)
		b5.addWidget(t4, 2)
		t5.setLayout(b5)
		t5.setFixedHeight(int(self.height() / 2))

		self.page3_v_box = QVBoxLayout()
		self.page3_v_box.addWidget(self.tableWidget_memo)
		self.page3_v_box.addWidget(t1_6)
		self.page3_v_box.addWidget(t5)
		self.insp_tab.setLayout(self.page3_v_box)

	def memo_click_write(self):
		ori = [['Item', 'Time', 'Length', 'Repeat', 'Status', 'Target times', 'Progress', 'Type', 'Stamp']]
		with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerows(ori)
		rownum = int(self.tableWidget_memo.rowCount())
		col = int(self.tableWidget_memo.columnCount())
		for n in range(rownum):
			if self.tableWidget_memo.item(n, 1) != None and self.tableWidget_memo.item(n, 1).text() != '':
				oricon = self.tableWidget_memo.item(n, 1).text()
				self.tableWidget_memo.setItem(n, 8, QTableWidgetItem(str(self.to_stamp(oricon))))
		t = 0
		while 0 <= t <= rownum - 1:
			outrow = []
			row = []
			i = 0
			while 0 <= i <= col - 1:
				if self.tableWidget_memo.item(t, i) != None and self.tableWidget_memo.item(t, i).text() != '':
					cell = str(self.tableWidget_memo.item(t, i).text())
					row.append(cell)
				if self.tableWidget_memo.item(t, i) == None:
					row.append('')
				if self.tableWidget_memo.item(t, i).text() == '':
					row.append('-')
				i += 1
				continue
			outrow.append(row)
			with open(self.fulldirall, 'a', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(outrow)
			t += 1
			continue
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
		self.textii3.setText(contm)
		self.textii3.ensureCursorVisible()  # 游标可用
		cursor = self.textii3.textCursor()  # 设置游标
		pos = len(self.textii3.toPlainText())  # 获取文本尾部的位置
		cursor.setPosition(pos)  # 游标位置设置为尾部
		self.textii3.setTextCursor(cursor)  # 滚动到游标位置
		if self.memo_dou == 1:
			if self.memo_changing_column == 4 and self.tableWidget_memo.item(self.memo_changing_row, 4).text() == 'DONE' and self.memo_to_done == 1:
				old_text = self.tableWidget_memo.item(self.tableWidget_memo.currentIndex().row(), 0).text()
				ISOTIMEFORMAT = '%H:%M:%S '
				theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
				parta = '\n\n- ' + str(theTime)
				partb = 'Completed memo: ' + old_text + '. '
				partc = ''
				if self.textw3.toPlainText() != '':
					partc = '\n\t- ' + self.textw3.toPlainText()
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(parta + partb + partc)
				contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
				self.textii3.setText(contm)
				self.textii3.ensureCursorVisible()  # 游标可用
				cursor = self.textii3.textCursor()  # 设置游标
				pos = len(self.textii3.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii3.setTextCursor(cursor)  # 滚动到游标位置
			self.lm1.setText('-')
			self.lm1.clear()
			self.textw3.clear()
			self.tableWidget_memo.clearSelection()
			self.tableWidget_memo.clearFocus()
			self.tableWidget_memo.setCurrentItem(None)
		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget_memo.sortByColumn(8, self.orderType)
		self.memo_dou = 0
		self.memo_to_done = 0

	def memo_double(self):
		self.memo_dou = 1
		self.memo_changing_row = self.tableWidget_memo.currentIndex().row()
		self.memo_changing_column = self.tableWidget_memo.currentIndex().column()
		self.memo_changing_done = self.tableWidget_memo.item(self.memo_changing_row, 4).text()
		if self.memo_changing_done == 'UNDONE':
			self.memo_to_done = 1

	def memo_add(self):
		if self.lm1.text() != '':
			new_time_sns = []
			outerlist = []
			part1 = self.lm1.text().replace('\n', '')
			ISOTIMEFORMAT = '%Y-%m-%d %H:%M'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			part2 = str(theTime)
			part3 = '-'
			part4 = '-'
			part5 = 'UNDONE'
			part6 = '-'
			part7 = '-'
			part8 = 'MEMO_SNS'
			part9 = str(self.to_stamp(part2))
			new_time_sns.append(part1)
			new_time_sns.append(part2)
			new_time_sns.append(part3)
			new_time_sns.append(part4)
			new_time_sns.append(part5)
			new_time_sns.append(part6)
			new_time_sns.append(part7)
			new_time_sns.append(part8)
			new_time_sns.append(part9)
			outerlist.append(new_time_sns)
			with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
				csv_reader = csv.reader(csv_file)
				lines = list(csv_reader)
				lines = lines + outerlist
			with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(lines)
			self.lm1.setText('-')
			self.lm1.clear()

	def memo_index_change(self, i):
		self.memo_readlater()

		input_table = pd.read_csv(self.fulldirall)
		input_table_rows = input_table.shape[0]  # 获取表格行数
		for x in range(0, input_table_rows):
			self.tableWidget_memo.setRowHidden(x, False)
		all_freq = []
		text = 'MEMO_SNS'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget_memo.findItems(text, Qt.MatchFlag.MatchContains)
		if items != []:
			for x in range(0, input_table_rows):
				self.tableWidget_memo.setRowHidden(x, True)
			for m in range(len(items)):
				item = items[m].row()
				all_freq.append(item)

		if i == 0:
			for m in range(len(all_freq)):
				item = all_freq[m]
				self.tableWidget_memo.setRowHidden(item, False)  # 隐藏对应的行
		if i == 1:
			undone_item = []
			text = 'UNDONE'  # 筛选 含有 “test” 的所有行
			items = self.tableWidget_memo.findItems(text, Qt.MatchFlag.MatchExactly)
			if items != []:
				for x in range(0, input_table_rows):
					self.tableWidget_memo.setRowHidden(x, True)
				for m in range(len(items)):
					item = items[m].row()
					undone_item.append(item)
				done_item = list(set(all_freq) - set(undone_item))
				todo_item = list(set(all_freq) - set(done_item))
				if todo_item != []:
					for k in range(len(todo_item)):
						item = todo_item[k]
						self.tableWidget_memo.setRowHidden(item, False)  # 隐藏对应的行
		if i == 2:
			undone_item = []
			text = 'UNDONE'  # 筛选 含有 “test” 的所有行
			items = self.tableWidget_memo.findItems(text, Qt.MatchFlag.MatchExactly)
			if items != []:
				for x in range(0, input_table_rows):
					self.tableWidget_memo.setRowHidden(x, True)
				for m in range(len(items)):
					item = items[m].row()
					undone_item.append(item)
				done_done = list(set(all_freq) - set(undone_item))
				if done_done != []:
					for r in range(len(done_done)):
						item = done_done[r]
						self.tableWidget_memo.setRowHidden(item, False)  # 隐藏对应的行
		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget_memo.sortByColumn(8, self.orderType)

	def memo_refresh(self):
		nowindex = self.widget2.currentIndex()
		if nowindex == 0:
			self.widget2.setCurrentIndex(-1)
		if nowindex != 0:
			self.widget2.setCurrentIndex(0)
		self.widget2.setCurrentIndex(nowindex)

	def memo_readlater(self):
		input_table = pd.read_csv(self.fulldirall)
		input_table_rows = input_table.shape[0]  # 获取表格行数
		# print(input_table_rows)
		self.input_table_colunms = input_table.shape[1]  # 获取表格列数
		# print(input_table_colunms)
		input_table_header = input_table.columns.values.tolist()  # 获取表头
		self.tableWidget_memo.setColumnCount(self.input_table_colunms)  # 设置表格列数
		self.tableWidget_memo.setRowCount(input_table_rows + 1)  # 设置表格行数(不给增加是+1,给增加是+2?)
		self.tableWidget_memo.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
		self.tableWidget_memo.verticalHeader().setVisible(False)

		t = 0
		while t >= 0 and t <= input_table_rows:
			csv_reader = csv.reader(open(self.fulldirall, encoding='utf-8'))
			for row in csv_reader:
				# print(row)
				if t <= input_table_rows:
					i = 0
					while i >= 0 and i <= self.input_table_colunms - 1:
						self.tableWidget_memo.setItem(t, i, QTableWidgetItem(str(row[i])))
						i += 1
						continue
					t += 1
					continue
		self.tableWidget_memo.removeRow(0)

		m = 0
		while m >= 0 and m <= input_table_rows:
			n = 0
			while n >= 0 and n <= self.input_table_colunms - 1:
				if self.tableWidget_memo.item(m, n) != None:
					self.tableWidget_memo.item(m, n).setTextAlignment(
						Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
				n += 1
				continue
			m += 1
			continue

	def memo_delete(self):
		if self.tableWidget_memo.currentItem() != None:
			del_row = self.tableWidget_memo.currentIndex().row() + 1
			with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
				csv_reader = csv.reader(csv_file)
				lines = list(csv_reader)
				del lines[del_row]
			with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(lines)
			self.lm1.setText('-')
			self.lm1.clear()

	def memo_delete_dones(self):
		self.memo_readlater()

		all_day = []
		text = 'MEMO_SNS'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget_memo.findItems(text, Qt.MatchFlag.MatchContains)
		if items != []:
			for m in range(len(items)):
				item = items[m].row()
				all_day.append(item)

		undone_item = []
		text = 'UNDONE'  # 筛选 含有 “test” 的所有行
		items = self.tableWidget_memo.findItems(text, Qt.MatchFlag.MatchExactly)
		if items != []:
			for m in range(len(items)):
				item = items[m].row()
				undone_item.append(item)
			done_item = list(set(all_day) - set(undone_item))
			delete_list = []
			if done_item != []:
				for j in range(len(done_item)):
					delete_list.append(done_item[j] + 1)
				if delete_list != []:
					remove_list = []
					with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
						csv_reader = csv.reader(csv_file)
						lines = list(csv_reader)
						for lo in range(len(delete_list)):
							remove_list.append(lines[delete_list[lo]])
					if remove_list != []:
						new_lines = []
						for x in range(len(lines)):
							if lines[x] not in remove_list:
								new_lines.append(lines[x])
						with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
							csv_writer = csv.writer(csv_file)
							csv_writer.writerows(new_lines)
		self.lm1.setText('-')
		self.lm1.clear()

	def memo_text_change(self):
		if self.textii3.toPlainText() != '':
			ISOTIMEFORMAT = '%Y-%m-%d diary'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			diary_name = str(theTime) + ".md"
			diary_file = os.path.join(self.fulldir_dia, diary_name)
			if not os.path.exists(diary_file):
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(f'# {theTime}')
			new_content = self.textii3.toPlainText()
			with open(diary_file, 'w', encoding='utf-8') as f0:
				f0.write(new_content)

	def memo_done_memo(self):
		if self.tableWidget_memo.currentItem() != None and self.tableWidget_memo.item(self.tableWidget_memo.currentRow(), 4).text() == 'UNDONE':
			current_row = self.tableWidget_memo.currentIndex().row()
			self.tableWidget_memo.setItem(current_row, 4, QTableWidgetItem('DONE'))

			ori = [['Item', 'Time', 'Length', 'Repeat', 'Status', 'Target times', 'Progress', 'Type', 'Stamp']]
			with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(ori)
			rownum = int(self.tableWidget_memo.rowCount())
			col = int(self.tableWidget_memo.columnCount())
			for n in range(rownum):
				if self.tableWidget_memo.item(n, 1) != None and self.tableWidget_memo.item(n, 1).text() != '':
					oricon = self.tableWidget_memo.item(n, 1).text()
					self.tableWidget_memo.setItem(n, 8, QTableWidgetItem(str(self.to_stamp(oricon))))
			t = 0
			while 0 <= t <= rownum - 1:
				outrow = []
				row = []
				i = 0
				while 0 <= i <= col - 1:
					if self.tableWidget_memo.item(t, i) != None and self.tableWidget_memo.item(t, i).text() != '':
						cell = str(self.tableWidget_memo.item(t, i).text())
						row.append(cell)
					if self.tableWidget_memo.item(t, i) == None:
						row.append('')
					if self.tableWidget_memo.item(t, i).text() == '':
						row.append('-')
					i += 1
					continue
				outrow.append(row)
				with open(self.fulldirall, 'a', encoding='utf8') as csv_file:
					csv_writer = csv.writer(csv_file)
					csv_writer.writerows(outrow)
				t += 1
				continue

			ISOTIMEFORMAT = '%Y-%m-%d diary'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			diary_name = str(theTime) + ".md"
			diary_file = os.path.join(self.fulldir_dia, diary_name)

			old_text = self.tableWidget_memo.item(self.tableWidget_memo.currentIndex().row(), 0).text()
			ISOTIMEFORMAT = '%H:%M:%S '
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			parta = '\n\n- ' + str(theTime)
			partb = 'Completed memo: ' + old_text + '. '
			partc = ''
			if self.textw3.toPlainText() != '':
				partc = '\n\t- ' + self.textw3.toPlainText()
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(parta + partb + partc)
			contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
			self.textii3.setText(contm)
			self.textii3.ensureCursorVisible()  # 游标可用
			cursor = self.textii3.textCursor()  # 设置游标
			pos = len(self.textii3.toPlainText())  # 获取文本尾部的位置
			cursor.setPosition(pos)  # 游标位置设置为尾部
			self.textii3.setTextCursor(cursor)  # 滚动到游标位置

			self.orderType = Qt.SortOrder.AscendingOrder
			self.tableWidget_memo.sortByColumn(8, self.orderType)
			self.textw3.clear()
			self.lm1.setText('-')
			self.lm1.clear()
		self.tableWidget_memo.clearSelection()
		self.tableWidget_memo.clearFocus()
		self.tableWidget_memo.setCurrentItem(None)

	def memo_copy_to_time(self):
		if self.tableWidget_memo.currentItem() != None:
			new_time_sns = []
			outerlist = []
			ite1_inp = self.tableWidget_memo.item(self.tableWidget_memo.currentIndex().row(), 0).text()
			tim2_inp = self.lm3.text()
			len3_inp = self.lm4.text()
			rep4_inp = self.lm5.text()
			if rep4_inp == '':
				rep4_inp = '-'
			sta5_inp = 'UNDONE'
			tar6_inp = '-'
			pro7_inp = '-'
			typ8_inp = 'TIME_SNS'
			sta9_inp = ''
			if ite1_inp != '' and tim2_inp != '' and len3_inp != '' and self.tableWidget_memo.item(
					self.tableWidget_memo.currentIndex().row(), 0) != None:
				try:
					sta9_inp = str(self.to_stamp(tim2_inp))
				except Exception as e:
					pass
				if sta9_inp != '':
					new_time_sns.append(ite1_inp)
					new_time_sns.append(tim2_inp)
					new_time_sns.append(len3_inp)
					new_time_sns.append(rep4_inp)
					new_time_sns.append(sta5_inp)
					new_time_sns.append(tar6_inp)
					new_time_sns.append(pro7_inp)
					new_time_sns.append(typ8_inp)
					new_time_sns.append(sta9_inp)
					outerlist.append(new_time_sns)
					with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
						csv_reader = csv.reader(csv_file)
						lines = list(csv_reader)
						lines = lines + outerlist
					with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
						csv_writer = csv.writer(csv_file)
						csv_writer.writerows(lines)
					timeArray = time.localtime(float(sta9_inp))
					otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
					cmd = """tell application "Reminders"
						set eachLine to "%s"
						set mylist to list "Tomato"
						tell mylist
							make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
						end tell
						quit
					end tell""" % (ite1_inp, otherStyleTime)
					cmd2 = """tell application "Calendar"
					  tell calendar "Tomato"
						make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
					  end tell
					  quit
					end tell""" % (ite1_inp, otherStyleTime, otherStyleTime, len3_inp)
					try:
						subprocess.call(['osascript', '-e', cmd])
						subprocess.call(['osascript', '-e', cmd2])
						self.lm3.clear()
						self.lm4.clear()
						self.lm5.clear()
						self.lm1.setText('-')
						self.lm1.clear()
					except Exception as e:
						pass

	def pin_a_tab(self):
		SCREEN_WEIGHT = int(self.screen().availableGeometry().width())
		WINDOW_WEIGHT = int(self.width())
		DE_HEIGHT = int(self.screen().availableGeometry().height())
		if self.pos().x() + WINDOW_WEIGHT + 4 < SCREEN_WEIGHT and self.pos().x() > 4:
			self.btn_00.setStyleSheet('''
									border: 1px outset grey;
									background-color: #FFFFFF;
									border-radius: 4px;
									padding: 1px;
									color: #000000''')
		else:
			target_x = 0
			if self.i % 2 == 1:
				win_old_width = codecs.open(BasePath + 'win_width.txt', 'r', encoding='utf-8').read()
				btna4.setChecked(True)
				self.btn_00.setStyleSheet('''
							border: 1px outset grey;
							background-color: #0085FF;
							border-radius: 4px;
							padding: 1px;
							color: #FFFFFF''')
				self.tab_bar.setVisible(True)
				self.resize(int(win_old_width), DE_HEIGHT)
				self.move(0 - int(win_old_width) + 10, self.pos().y())
				target_x = 3
				self.setFixedWidth(int(win_old_width))
			if self.i % 2 == 0:
				btna4.setChecked(False)
				self.btn_00.setStyleSheet('''
							border: 1px outset grey;
							background-color: #FFFFFF;
							border-radius: 4px;
							padding: 1px;
							color: #000000''')
				self.tab_bar.setVisible(False)
				with open(BasePath + 'win_width.txt', 'w', encoding='utf-8') as f0:
					f0.write(str(self.width()))
				self.resize(self.new_width, DE_HEIGHT)
				self.move(self.width() + 3, self.pos().y())
				target_x = 0
				self.setFixedWidth(self.new_width)

			ISOTIMEFORMAT = '%Y-%m-%d diary'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			diary_name = str(theTime) + ".md"
			diary_file = os.path.join(self.fulldir_dia, diary_name)
			if not os.path.exists(diary_file):
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(f'# {theTime}')
			contm = codecs.open(diary_file, 'r', encoding='utf-8').read()

			tabnum = self.tab_bar.currentIndex()
			self.openwidth = self.tableWidget.width()
			leng_small = self.tableWidget_record.width()
			if tabnum == 0:
				self.tableWidget.setColumnWidth(0, int(self.openwidth / 8 * 3))
				self.tableWidget.setColumnWidth(1, int(self.openwidth / 16 * 3))
				self.tableWidget.setColumnWidth(2, int(self.openwidth / 48 * 7))
				self.tableWidget.setColumnWidth(3, int(self.openwidth / 48 * 7))
				self.tableWidget.setColumnWidth(4, int(self.openwidth / 48 * 7))
				self.tableWidget.setColumnWidth(5, 0)
				self.tableWidget.setColumnWidth(6, 0)
				self.tableWidget.setColumnWidth(7, 0)
				self.tableWidget.setColumnWidth(8, 0)
				self.tableWidget_record.setColumnWidth(0, int(leng_small / 2))
				self.tableWidget_record.setColumnWidth(1, int(leng_small / 2))
				self.le4.setText('-')
				self.le4.clear()
				self.textii1.setText(contm)
				self.textii1.ensureCursorVisible()  # 游标可用
				cursor = self.textii1.textCursor()  # 设置游标
				pos = len(self.textii1.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii1.setTextCursor(cursor)  # 滚动到游标位置
			if tabnum == 1:
				self.tableWidget_freq.setColumnWidth(0, int(self.openwidth / 16 * 9))
				self.tableWidget_freq.setColumnWidth(1, 0)
				self.tableWidget_freq.setColumnWidth(2, 0)
				self.tableWidget_freq.setColumnWidth(3, 0)
				self.tableWidget_freq.setColumnWidth(4, int(self.openwidth / 48 * 7))
				self.tableWidget_freq.setColumnWidth(5, int(self.openwidth / 48 * 7))
				self.tableWidget_freq.setColumnWidth(6, int(self.openwidth / 48 * 7))
				self.tableWidget_freq.setColumnWidth(7, 0)
				self.tableWidget_freq.setColumnWidth(8, 0)
				self.tableWidget_record2.setColumnWidth(0, int(leng_small / 2))
				self.tableWidget_record2.setColumnWidth(1, int(leng_small / 2))
				self.lf2.setText('-')
				self.lf2.clear()
				self.textii2.setText(contm)
				self.textii2.ensureCursorVisible()  # 游标可用
				cursor = self.textii2.textCursor()  # 设置游标
				pos = len(self.textii2.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii2.setTextCursor(cursor)  # 滚动到游标位置
			if tabnum == 2:
				self.tableWidget_memo.setColumnWidth(0, int(self.openwidth / 48 * 41))
				self.tableWidget_memo.setColumnWidth(1, 0)
				self.tableWidget_memo.setColumnWidth(2, 0)
				self.tableWidget_memo.setColumnWidth(3, 0)
				self.tableWidget_memo.setColumnWidth(4, int(self.openwidth / 48 * 7))
				self.tableWidget_memo.setColumnWidth(5, 0)
				self.tableWidget_memo.setColumnWidth(6, 0)
				self.tableWidget_memo.setColumnWidth(7, 0)
				self.tableWidget_memo.setColumnWidth(8, 0)
				self.lm1.setText('-')
				self.lm1.clear()
				#self.tableWidget_record3.setColumnWidth(0, int(leng_small / 2))
				#self.tableWidget_record3.setColumnWidth(1, int(leng_small / 2))
				self.textii3.setText(contm)
				self.textii3.ensureCursorVisible()  # 游标可用
				cursor = self.textii3.textCursor()  # 设置游标
				pos = len(self.textii3.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii3.setTextCursor(cursor)  # 滚动到游标位置

			self.move_window(target_x, self.pos().y())

	def pin_a_tab2(self):
		SCREEN_WEIGHT = int(self.screen().availableGeometry().width())
		WINDOW_WEIGHT = int(self.width())
		DE_HEIGHT = int(self.screen().availableGeometry().height())
		if self.pos().x() + WINDOW_WEIGHT + 4 < SCREEN_WEIGHT and self.pos().x() > 4:
			self.btn_00.setStyleSheet('''
									border: 1px outset grey;
									background-color: #FFFFFF;
									border-radius: 4px;
									padding: 1px;
									color: #000000''')
		else:
			target_x = 0
			if self.i % 2 == 1:
				win_old_width = codecs.open(BasePath + 'win_width.txt', 'r', encoding='utf-8').read()
				btna4.setChecked(True)
				self.btn_00.setStyleSheet('''
							border: 1px outset grey;
							background-color: #0085FF;
							border-radius: 4px;
							padding: 1px;
							color: #FFFFFF''')
				self.tab_bar.setVisible(True)
				self.resize(int(win_old_width), DE_HEIGHT)
				self.move(0 - int(win_old_width) + 10, self.pos().y())
				target_x = 3
				self.setFixedWidth(int(win_old_width))
			if self.i % 2 == 0:
				btna4.setChecked(False)
				self.btn_00.setStyleSheet('''
							border: 1px outset grey;
							background-color: #FFFFFF;
							border-radius: 4px;
							padding: 1px;
							color: #000000''')
				self.tab_bar.setVisible(False)
				with open(BasePath + 'win_width.txt', 'w', encoding='utf-8') as f0:
					f0.write(str(self.width()))
				self.resize(self.new_width, DE_HEIGHT)
				self.move(self.width() + 3, self.pos().y())
				target_x = 0
				self.setFixedWidth(self.new_width)

			ISOTIMEFORMAT = '%Y-%m-%d diary'
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			diary_name = str(theTime) + ".md"
			diary_file = os.path.join(self.fulldir_dia, diary_name)
			if not os.path.exists(diary_file):
				with open(diary_file, 'a', encoding='utf-8') as f0:
					f0.write(f'# {theTime}')
			contm = codecs.open(diary_file, 'r', encoding='utf-8').read()

			tabnum = self.tab_bar.currentIndex()
			self.openwidth = self.tableWidget.width()
			leng_small = self.tableWidget_record.width()
			if tabnum == 0:
				self.tableWidget.setColumnWidth(0, int(self.openwidth / 8 * 3))
				self.tableWidget.setColumnWidth(1, int(self.openwidth / 16 * 3))
				self.tableWidget.setColumnWidth(2, int(self.openwidth / 48 * 7))
				self.tableWidget.setColumnWidth(3, int(self.openwidth / 48 * 7))
				self.tableWidget.setColumnWidth(4, int(self.openwidth / 48 * 7))
				self.tableWidget.setColumnWidth(5, 0)
				self.tableWidget.setColumnWidth(6, 0)
				self.tableWidget.setColumnWidth(7, 0)
				self.tableWidget.setColumnWidth(8, 0)
				self.tableWidget_record.setColumnWidth(0, int(leng_small / 2))
				self.tableWidget_record.setColumnWidth(1, int(leng_small / 2))
				self.le4.setText('-')
				self.le4.clear()
				self.textii1.setText(contm)
				self.textii1.ensureCursorVisible()  # 游标可用
				cursor = self.textii1.textCursor()  # 设置游标
				pos = len(self.textii1.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii1.setTextCursor(cursor)  # 滚动到游标位置
			if tabnum == 1:
				self.tableWidget_freq.setColumnWidth(0, int(self.openwidth / 16 * 9))
				self.tableWidget_freq.setColumnWidth(1, 0)
				self.tableWidget_freq.setColumnWidth(2, 0)
				self.tableWidget_freq.setColumnWidth(3, 0)
				self.tableWidget_freq.setColumnWidth(4, int(self.openwidth / 48 * 7))
				self.tableWidget_freq.setColumnWidth(5, int(self.openwidth / 48 * 7))
				self.tableWidget_freq.setColumnWidth(6, int(self.openwidth / 48 * 7))
				self.tableWidget_freq.setColumnWidth(7, 0)
				self.tableWidget_freq.setColumnWidth(8, 0)
				self.tableWidget_record2.setColumnWidth(0, int(leng_small / 2))
				self.tableWidget_record2.setColumnWidth(1, int(leng_small / 2))
				self.lf2.setText('-')
				self.lf2.clear()
				self.textii2.setText(contm)
				self.textii2.ensureCursorVisible()  # 游标可用
				cursor = self.textii2.textCursor()  # 设置游标
				pos = len(self.textii2.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii2.setTextCursor(cursor)  # 滚动到游标位置
			if tabnum == 2:
				self.tableWidget_memo.setColumnWidth(0, int(self.openwidth / 48 * 41))
				self.tableWidget_memo.setColumnWidth(1, 0)
				self.tableWidget_memo.setColumnWidth(2, 0)
				self.tableWidget_memo.setColumnWidth(3, 0)
				self.tableWidget_memo.setColumnWidth(4, int(self.openwidth / 48 * 7))
				self.tableWidget_memo.setColumnWidth(5, 0)
				self.tableWidget_memo.setColumnWidth(6, 0)
				self.tableWidget_memo.setColumnWidth(7, 0)
				self.tableWidget_memo.setColumnWidth(8, 0)
				self.lm1.setText('-')
				self.lm1.clear()
				#self.tableWidget_record3.setColumnWidth(0, int(leng_small / 2))
				#self.tableWidget_record3.setColumnWidth(1, int(leng_small / 2))
				self.textii3.setText(contm)
				self.textii3.ensureCursorVisible()  # 游标可用
				cursor = self.textii3.textCursor()  # 设置游标
				pos = len(self.textii3.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textii3.setTextCursor(cursor)  # 滚动到游标位置

			self.move_window(target_x, self.pos().y())

	def auto_record(self):
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		if action4.isChecked():
			cmd = """
			tell application "/Applications/Tomato.app/Contents/Auto/TomatoAuto.app"
				activate
			end tell"""
			try:
				subprocess.call(['osascript', '-e', cmd])
			except Exception as e:
				pass
		if not action4.isChecked():
			ISOTIMEFORMAT = '%H:%M:%S '
			theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
			pretext = '- ' + theTime
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(pretext)
			cmd2 = """
			tell application "/Applications/Tomato.app/Contents/Auto/TomatoAuto.app"
				quit
			end tell"""
			try:
				subprocess.call(['osascript', '-e', cmd2])
			except Exception as e:
				pass

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def keyPressEvent(self, e):  # 当页面显示的时候，按下esc键可关闭窗口
		if e.key() == Qt.Key.Key_Escape.value:
			self.close()

	def cancel(self):  # 设置取消键的功能
		self.close()


style_sheet_ori = '''
	QTabWidget::pane {
		border: 1px solid #ECECEC;
		background: #ECECEC;
		border-radius: 9px;
}
	QTableWidget{
		border: 1px solid grey;  
		border-radius:4px;
		background-clip: border;
		background-color: #FFFFFF;
		color: #000000;
		font: 14pt Helvetica;
}
	QPushButton{
		border: 1px outset grey;
		background-color: #FFFFFF;
		border-radius: 4px;
		padding: 1px;
		color: #000000
}
	QPushButton:pressed{
		border: 1px outset grey;
		background-color: #0085FF;
		border-radius: 4px;
		padding: 1px;
		color: #FFFFFF
}
	QPlainTextEdit{
		border: 1px solid grey;  
		border-radius:4px;
		padding: 1px 5px 1px 3px; 
		background-clip: border;
		background-color: #F3F2EE;
		color: #000000;
		font: 14pt Times New Roman;
}
	QPlainTextEdit#edit{
		border: 1px solid grey;  
		border-radius:4px;
		padding: 1px 5px 1px 3px; 
		background-clip: border;
		background-color: #FFFFFF;
		color: rgb(113, 113, 113);
		font: 14pt Helvetica;
}
	QTableWidget#small{
		border: 1px solid grey;  
		border-radius:4px;
		background-clip: border;
		background-color: #F3F2EE;
		color: #000000;
		font: 14pt Times New Roman;
}
	QLineEdit{
		border-radius:4px;
		border: 1px solid gray;
		background-color: #FFFFFF;
}
	QTextEdit{
		border: 1px solid grey;  
		border-radius:4px;
		padding: 1px 5px 1px 3px; 
		background-clip: border;
		background-color: #F3F2EE;
		color: #000000;
		font: 14pt Times New Roman;
}
'''


w1 = window_about()  # about
w2 = window_update()  # update
w3 = window3()  # main1
w3.setAutoFillBackground(True)
p = w3.palette()
p.setColor(w3.backgroundRole(), QColor('#ECECEC'))
w3.setPalette(p)
action1.triggered.connect(w1.activate)
action2.triggered.connect(w2.activate)
action3.triggered.connect(w3.pin_a_tab)
action4.triggered.connect(w3.auto_record)
# tray.activated.connect(w3.activate)
btna4.triggered.connect(w3.pin_a_tab2)
app.setStyleSheet(style_sheet_ori)
app.exec()
