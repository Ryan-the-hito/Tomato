#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- encoding:UTF-8 -*-
# coding=utf-8
# coding:utf-8

import codecs
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
							 QLabel, QHBoxLayout, QVBoxLayout, QLineEdit, QDateEdit, QTimeEdit,
							 QSystemTrayIcon, QMenu, QComboBox, QDialog, QMenuBar, QFrame, QFileDialog,
							 QPlainTextEdit, QTabWidget, QTextEdit, QGraphicsOpacityEffect,
							 QTableWidget, QTableWidgetItem, QAbstractItemView, QInputDialog,
							 QMessageBox, QSplitter, QDialogButtonBox, QListWidget, QListWidgetItem, QCheckBox)
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QDate, QTime, QTimer, QObject, QEvent
from PyQt6.QtGui import QAction, QIcon, QColor, QCursor, QGuiApplication
import PyQt6.QtGui
import sys
import webbrowser
import os
from pathlib import Path
import re
import datetime
import time
import threading
import pandas as pd
import csv
import subprocess
import shutil
import urllib3
import logging
import json
import queue
import contextlib
from dataclasses import dataclass
from functools import partial
try:
	from AppKit import NSWorkspace
except ImportError:
	NSWorkspace = None
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

tray_selected_section = menu.addSection("⏱ 主清单（倒计时）")
tray_selected_section.setVisible(False)
tray_selected_separator = menu.addSeparator()
tray_selected_separator.setVisible(False)

time_sensitive_menu = menu.addMenu("🕒 Countdown")
menu.addSeparator()

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
menu.addAction(quit)

# Add the menu to the tray
tray.setContextMenu(menu)

# create a system menu
btna4 = QAction("&Pin!")
btna4.setCheckable(True)
sysmenu = QMenuBar()
file_menu = sysmenu.addMenu("&Actions")
file_menu.addAction(btna4)


class AutoRecordThread(threading.Thread):
	def __init__(self, diary_dir):
		super().__init__(daemon=True)
		self.diary_dir = Path(diary_dir)
		self.diary_dir.mkdir(parents=True, exist_ok=True)
		self._stop_event = threading.Event()
		self._counter = 5
		self._last_active_name = None

	def run(self):
		while not self._stop_event.wait(1):
			self._counter -= 1
			if self._counter <= 0:
				try:
					self.auto_scan()
				except Exception:
					logging.exception("Auto-record scan failed.")
				self._counter = 5

	def stop(self, timeout=2.0):
		self._stop_event.set()
		if self.is_alive():
			self.join(timeout)

	def auto_scan(self):
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_file = self.diary_dir / f"{theTime}.md"
		if not diary_file.exists():
			with diary_file.open('a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		if NSWorkspace is None:
			return
		try:
			active_app = NSWorkspace.sharedWorkspace().activeApplication()
		except Exception:
			logging.exception("Failed to fetch active application.")
			return
		if not active_app:
			return
		app_name = active_app.get('NSApplicationName')
		if self._last_active_name is None:
			pretext = '\n\n- %s -(Tomato)' % datetime.datetime.now().strftime('%H:%M:%S ')
			with diary_file.open('a', encoding='utf-8') as f0:
				f0.write(pretext)
		if app_name and app_name != self._last_active_name:
			self._last_active_name = app_name
			parta = '- %s \n\n- %s -(%s)' % (
				datetime.datetime.now().strftime('%H:%M:%S'),
				datetime.datetime.now().strftime('%H:%M:%S'),
				app_name
			)
			with diary_file.open('a', encoding='utf-8') as f0:
				f0.write(parta)


class ReminderSyncThread(threading.Thread):
	def __init__(self, output_queue, interval_seconds=120):
		super().__init__(daemon=True)
		self.output_queue = output_queue
		self.interval = max(30, int(interval_seconds))
		self._stop_event = threading.Event()

	def stop(self, timeout=2.0):
		self._stop_event.set()
		if self.is_alive():
			self.join(timeout)

	def run(self):
		while not self._stop_event.is_set():
			try:
				start_time = time.time()
				snapshot = self._fetch_snapshot()
				if snapshot is not None:
					self.output_queue.put({
						'timestamp': start_time,
						'snapshot': snapshot
					})
			except Exception:
				logging.exception("Failed to fetch reminders snapshot.")
			if self._stop_event.wait(self.interval):
				break

	def _fetch_snapshot(self):
		script = r'''
function run() {
	var result = {status: "ok", data: []};
	try {
		var app = Application("Reminders");
		var lists = app.lists.whose({name: "Tomato"});
		if (lists.length === 0) {
			result.status = "missing";
			return JSON.stringify(result);
		}
		var reminderList = lists[0];
		var reminders = reminderList.reminders();
		for (var i = 0; i < reminders.length; i++) {
			var reminder = reminders[i];
			var due = reminder.remindMeDate();
			if (!due) {
				continue;
			}
			result.data.push({
				id: reminder.id(),
				name: reminder.name() || "",
				stamp: Math.floor(due.getTime() / 1000),
				completed: reminder.completed()
			});
		}
	} catch (err) {
		result.status = "error";
		result.message = err.toString();
	}
	return JSON.stringify(result);
}
'''
		try:
			output = subprocess.check_output(
				['osascript', '-l', 'JavaScript', '-e', script],
				text=True
			).strip()
		except subprocess.CalledProcessError:
			return None
		if not output:
			return None
		try:
			payload = json.loads(output)
		except json.JSONDecodeError:
			logging.warning("Unable to parse reminder snapshot: %s", output)
			return None
		if payload.get('status') != 'ok':
			if payload.get('status') not in ('missing', 'error'):
				logging.warning("Unexpected reminder snapshot status: %s", payload.get('status'))
			return None
		return payload.get('data', [])


class CalendarSyncThread(threading.Thread):
	def __init__(self, output_queue, interval_seconds=120):
		super().__init__(daemon=True)
		self.output_queue = output_queue
		self.interval = max(30, int(interval_seconds))
		self._stop_event = threading.Event()

	def stop(self, timeout=2.0):
		self._stop_event.set()
		if self.is_alive():
			self.join(timeout)

	def run(self):
		while not self._stop_event.is_set():
			try:
				start_time = time.time()
				snapshot = self._fetch_snapshot()
				if snapshot is not None:
					self.output_queue.put({
						'timestamp': start_time,
						'snapshot': snapshot
					})
			except Exception:
				logging.exception("Failed to fetch calendar snapshot.")
			if self._stop_event.wait(self.interval):
				break

	def _fetch_snapshot(self):
		script = r'''
function run() {
	var result = {status: "ok", data: []};
	try {
		var app = Application("Calendar");
		var cals = app.calendars.whose({name: "Tomato"});
		if (cals.length === 0) {
			result.status = "missing";
			return JSON.stringify(result);
		}
		var cal = cals[0];
		var events = cal.events();
		for (var i = 0; i < events.length; i++) {
			var ev = events[i];
			var start = ev.startDate();
			if (!start) {
				continue;
			}
			var end = ev.endDate();
			var duration = 0;
			if (end) {
				duration = Math.floor((end.getTime() - start.getTime()) / 1000);
			}
			result.data.push({
				id: ev.id(),
				name: ev.summary() || "",
				stamp: Math.floor(start.getTime() / 1000),
				duration: duration
			});
		}
	} catch (err) {
		result.status = "error";
		result.message = err.toString();
	}
	return JSON.stringify(result);
}
'''
		try:
			output = subprocess.check_output(
				['osascript', '-l', 'JavaScript', '-e', script],
				text=True
			).strip()
		except subprocess.CalledProcessError:
			return None
		if not output:
			return None
		try:
			payload = json.loads(output)
		except json.JSONDecodeError:
			logging.warning("Unable to parse calendar snapshot: %s", output)
			return None
		if payload.get('status') != 'ok':
			if payload.get('status') not in ('missing', 'error'):
				logging.warning("Unexpected calendar snapshot status: %s", payload.get('status'))
			return None
		return payload.get('data', [])


@dataclass
class TimeSensitiveTask:
	task_id: str
	name: str
	due: datetime.datetime
	due_label: str
	stamp: int


class TimeSensitiveTrayController(QObject):
	def __init__(self, menu, submenu, section_header, section_separator, path_provider):
		super().__init__(menu)
		self.menu = menu
		self.submenu = submenu
		self.section_header = section_header
		self.section_separator = section_separator
		self.path_provider = path_provider
		self.selected_tasks = {}
		self.available_lookup = {}
		self.main_actions = {}
		self._state_file = None
		self._pending_restore_ids = None
		self.submenu.aboutToShow.connect(self.refresh_available_items)
		self.menu.aboutToShow.connect(self._update_selected_task_actions)
		self.refresh_available_items()

	def refresh_available_items(self):
		tasks = self._load_time_sensitive_tasks()
		self.available_lookup = {task.task_id: task for task in tasks}
		removed_any = False
		relinked_any = False
		for task_id in list(self.selected_tasks.keys()):
			preferred = self._preferred_task_for_identifier(task_id)
			if preferred is None:
				self._remove_from_main_menu(task_id)
				self.selected_tasks.pop(task_id, None)
				removed_any = True
				continue
			if preferred.task_id != task_id:
				old_action = self.main_actions.pop(task_id, None)
				self.selected_tasks.pop(task_id, None)
				self.selected_tasks[preferred.task_id] = preferred
				if old_action is not None:
					self.main_actions[preferred.task_id] = old_action
				else:
					self._add_to_main_menu(preferred.task_id, preferred)
				self._update_single_action(preferred.task_id)
				relinked_any = True
			else:
				self.selected_tasks[task_id] = preferred
		if removed_any or relinked_any:
			self._persist_current_selection()
		else:
			for task_id, task in list(self.selected_tasks.items()):
				latest = self.available_lookup.get(task_id)
				if latest:
					self.selected_tasks[task_id] = latest
		self._build_submenu_actions(tasks)

	def _build_submenu_actions(self, tasks):
		self.submenu.clear()
		if not tasks:
			no_item_action = QAction("No Countdown for now", self.submenu)
			no_item_action.setEnabled(False)
			self.submenu.addAction(no_item_action)
			return
		for task in tasks:
			action = QAction(f"{task.due_label} · {task.name}", self.submenu)
			action.setCheckable(True)
			action.blockSignals(True)
			action.setChecked(task.task_id in self.selected_tasks)
			action.blockSignals(False)
			action.toggled.connect(partial(self._toggle_task_selection, task.task_id))
			self.submenu.addAction(action)
		self._restore_pending_selections()

	def _toggle_task_selection(self, task_id, checked):
		task = self.available_lookup.get(task_id)
		if not task:
			return
		if checked:
			self.selected_tasks[task_id] = task
			self._add_to_main_menu(task_id, task)
		else:
			self.selected_tasks.pop(task_id, None)
			self._remove_from_main_menu(task_id)
		self._persist_current_selection()

	def _add_to_main_menu(self, task_id, task):
		if task_id in self.main_actions:
			self._update_single_action(task_id)
			return
		action = QAction("", self.menu)
		action.setEnabled(False)
		self.menu.insertAction(self.section_separator, action)
		self.main_actions[task_id] = action
		self._update_section_visibility()
		self._update_single_action(task_id)

	def _remove_from_main_menu(self, task_id):
		action = self.main_actions.pop(task_id, None)
		if action:
			self.menu.removeAction(action)
			action.deleteLater()
		self._update_section_visibility()

	def _update_selected_task_actions(self):
		now = datetime.datetime.now()
		for task_id in list(self.main_actions.keys()):
			self._update_single_action(task_id, now)
		self._reorder_main_actions(now)

	def _update_single_action(self, task_id, now=None):
		task = self.selected_tasks.get(task_id)
		action = self.main_actions.get(task_id)
		if not task or not action:
			return
		now = now or datetime.datetime.now()
		delta_seconds = (task.due - now).total_seconds()
		countdown_text = self._format_countdown(delta_seconds)
		prefix = "Still: " if delta_seconds >= 0 else "Overdue: "
		action.setText(f"{task.name} · {task.due_label} · {prefix}{countdown_text}")

	def _reorder_main_actions(self, now=None):
		if not self.main_actions:
			return
		now = now or datetime.datetime.now()
		ordered_ids = []
		for task_id, task in self.selected_tasks.items():
			action = self.main_actions.get(task_id)
			if not action or not task:
				continue
			delta = abs((task.due - now).total_seconds())
			ordered_ids.append((delta, task.due, task_id))
		if not ordered_ids:
			return
		ordered_ids.sort(key=lambda item: (item[0], item[1]))
		actions = []
		for _, _, task_id in ordered_ids:
			action = self.main_actions.get(task_id)
			if not action:
				continue
			self.menu.removeAction(action)
			actions.append((task_id, action))
		for task_id, action in actions:
			self.menu.insertAction(self.section_separator, action)

	def _format_countdown(self, seconds):
		total = int(abs(seconds))
		days, rem = divmod(total, 86400)
		hours, rem = divmod(rem, 3600)
		minutes, rem = divmod(rem, 60)
		parts = []
		if days:
			parts.append(f"{days} Days")
		if hours:
			parts.append(f" {hours} Hours")
		if minutes:
			parts.append(f" {minutes} Minutes")
		if not parts:
			parts.append(f" {rem} Seconds")
		return "".join(parts[:3])

	def _update_section_visibility(self):
		visible = bool(self.main_actions)
		self.section_header.setVisible(visible)
		self.section_separator.setVisible(visible)

	def _load_time_sensitive_tasks(self):
		path = self._safe_path()
		if not path:
			return []
		self._ensure_state_file(path)
		tasks = []
		try:
			with open(path, 'r', encoding='utf-8') as csv_file:
				reader = csv.DictReader(csv_file)
				for row in reader:
					if (row.get('Type') or '').strip() != 'TIME_SNS':
						continue
					name = (row.get('Item') or '').strip()
					if not name:
						continue
					due = self._parse_due(row)
					if due is None:
						continue
					due_dt, label, stamp = due
					task_id = f"{name}|{stamp}"
					tasks.append(TimeSensitiveTask(task_id, name, due_dt, label, stamp))
		except Exception:
			logging.exception("Failed to load countdowns")
			return []
		tasks.sort(key=lambda item: item.due)
		return tasks

	def _parse_due(self, row):
		time_text = (row.get('Time') or '').strip()
		stamp_text = (row.get('Stamp') or '').strip()
		due_dt = None
		stamp_value = None
		if stamp_text:
			try:
				stamp_value = int(round(float(stamp_text)))
				due_dt = datetime.datetime.fromtimestamp(stamp_value)
			except ValueError:
				due_dt = None
		if due_dt is None and time_text:
			try:
				due_dt = datetime.datetime.strptime(time_text, "%Y-%m-%d %H:%M")
				stamp_value = int(round(due_dt.timestamp()))
			except ValueError:
				due_dt = None
		if due_dt is None:
			return None
		label = time_text or due_dt.strftime("%Y-%m-%d %H:%M")
		if stamp_value is None:
			stamp_value = int(round(due_dt.timestamp()))
		return due_dt, label, stamp_value

	def _safe_path(self):
		try:
			return self.path_provider()
		except Exception:
			logging.exception("无法获取 All.csv 路径")
			return None

	def _ensure_state_file(self, csv_path):
		if self._state_file:
			return
		try:
			directory = os.path.dirname(csv_path)
			self._state_file = os.path.join(directory, 'time_sensitive_selection.json')
		except Exception:
			logging.exception("无法生成持久化文件路径")
			self._state_file = None
			return
		self._pending_restore_ids = self._load_persisted_ids()

	def _load_persisted_ids(self):
		if not self._state_file or not os.path.exists(self._state_file):
			return set()
		try:
			with open(self._state_file, 'r', encoding='utf-8') as fh:
				data = json.load(fh)
			if isinstance(data, list):
				return {str(item) for item in data if isinstance(item, str)}
		except Exception:
			logging.exception("读取倒计时选择记录失败")
		return set()

	def _persist_current_selection(self):
		if not self._state_file:
			return
		try:
			os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
			with open(self._state_file, 'w', encoding='utf-8') as fh:
				json.dump(sorted(self.selected_tasks.keys()), fh, ensure_ascii=False, indent=2)
		except Exception:
			logging.exception("保存倒计时选择记录失败")

	def _restore_pending_selections(self):
		if not self._pending_restore_ids:
			return
		remaining = set()
		restored = False
		for task_id in list(self._pending_restore_ids):
			task = self._preferred_task_for_identifier(task_id)
			if task:
				new_id = task.task_id
				if new_id not in self.selected_tasks:
					self.selected_tasks[new_id] = task
					self._add_to_main_menu(new_id, task)
					restored = True
				else:
					self.selected_tasks[new_id] = task
			else:
				remaining.add(task_id)
		self._pending_restore_ids = remaining if remaining else None
		if restored:
			self._persist_current_selection()

	def _preferred_task_for_identifier(self, identifier):
		task = self.available_lookup.get(identifier)
		if task:
			return task
		try:
			name = identifier.split('|', 1)[0]
		except Exception:
			return None
		if not name:
			return None
		candidates = [item for item in self.available_lookup.values() if item.name == name]
		if len(candidates) == 1:
			return candidates[0]
		return None

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
		lbl1 = QLabel('Version 1.2.1', self)
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
		lbl6 = QLabel('© 2023-2024 Ryan-the-hito. All rights reserved.', self)
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

		self.lbl = QLabel('Current Version: v1.2.1', self)
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
		webbrowser.open('https://drive.google.com/drive/folders/1OFbVRi5nCUwG12VCUYpTzxA12W5uRoec?usp=sharing')

	def upd2(self):
		webbrowser.open('https://pan.baidu.com/s/1wqtKv2G8fP4uHeh6P0kuNw?pwd=rkuu')

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
		self._diary_text_edits = []
		self._diary_viewport_owner = {}
		self._suppress_diary_write = False
		self._last_local_reminder_change = 0.0
		self.initUI()

	def initUI(self):  # 设置窗口内布局
		self._init_sync_indicator()
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
		tarname_collection = "Collection"
		self.fulldir_collection = os.path.join(fulldir1, tarname_collection)
		if not os.path.exists(self.fulldir_collection):
			os.mkdir(self.fulldir_collection)
		self.setUpMainWindow()
		MOST_WEIGHT = int(self.screen().availableGeometry().width() * 0.75)
		HALF_WEIGHT = int(self.screen().availableGeometry().width() / 2)
		MINI_WEIGHT = int(self.screen().availableGeometry().width() / 4)
		SCREEN_WEIGHT = int(self.screen().availableGeometry().width())

		DE_HEIGHT = int(self.screen().availableGeometry().height())
		HALF_HEIGHT = int(self.screen().availableGeometry().height() * 0.5)
		BIGGIST_HEIGHT = int(self.screen().availableGeometry().height())

		self.resize(HALF_WEIGHT, DE_HEIGHT)
		self.move(self.width() + 3, int((DE_HEIGHT - 70) / 2))
		self.move_window2(0, int((DE_HEIGHT - 70) / 2))
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.show()
		self.tab_bar.setVisible(False)
		self.new_width = 10
		self.setFixedSize(self.new_width, 120)
		app.setStyleSheet(style_sheet_ori)
		self.assigntoall()
		self.auto_record_thread = None
		self.reminder_sync_thread = None
		self.calendar_sync_thread = None
		self.reminder_sync_queue = queue.Queue()
		self.calendar_sync_queue = queue.Queue()
		self._sync_processing = False
		self._last_calendar_snapshot_ts = 0.0
		self._last_reminder_snapshot_ts = 0.0
		self.reminder_sync_timer = QTimer(self)
		self.reminder_sync_timer.setInterval(3000)
		self.reminder_sync_timer.timeout.connect(self._process_sync_messages)
		self.reminder_sync_timer.start()
		self._start_reminder_sync_worker()
		self._start_calendar_sync_worker()

	def setUpMainWindow(self):
		self.tab_bar = QTabWidget()
		self.word_tab = QWidget()
		self.art_tab = QWidget()
		self.insp_tab = QWidget()
		self.collect_tab = QWidget()

		self.tab_bar.addTab(self.word_tab, "Time")
		self.tab_bar.addTab(self.art_tab, "Frequency")
		self.tab_bar.addTab(self.insp_tab, "Memory")
		self.tab_bar.addTab(self.collect_tab, "Collection")
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
		self.collectTab()

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

	def _current_screen_geometry(self):
		screen = QGuiApplication.screenAt(QCursor.pos())
		if screen:
			return screen.availableGeometry()
		window_handle = self.windowHandle()
		if window_handle and window_handle.screen():
			return window_handle.screen().availableGeometry()
		if self.screen():
			return self.screen().availableGeometry()
		primary = QGuiApplication.primaryScreen()
		return primary.availableGeometry() if primary else QRect(0, 0, 1440, 900)

	def _register_diary_refresh(self, widget):
		widget.installEventFilter(self)
		self._diary_text_edits.append(widget)
		viewport = getattr(widget, "viewport", None)
		if callable(viewport):
			vp = widget.viewport()
			if vp:
				vp.installEventFilter(self)
				self._diary_viewport_owner[vp] = widget

	def _load_today_diary_content(self):
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_file = os.path.join(self.fulldir_dia, f"{theTime}.md")
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		with open(diary_file, 'r', encoding='utf-8') as fh:
			return fh.read()

	def _refresh_diary_text_widget(self, widget):
		try:
			self._suppress_diary_write = True
			contm = self._load_today_diary_content()
		except Exception:
			self._suppress_diary_write = False
			return
		widget.setText(contm)
		widget.ensureCursorVisible()
		cursor = widget.textCursor()
		cursor.setPosition(len(widget.toPlainText()))
		widget.setTextCursor(cursor)
		self._suppress_diary_write = False

	def eventFilter(self, obj, event):
		target = obj
		if obj in self._diary_viewport_owner:
			target = self._diary_viewport_owner.get(obj)
		if target in self._diary_text_edits and event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.FocusIn):
			self._refresh_diary_text_widget(target)
		return super().eventFilter(obj, event)

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
		CMD = """tell application "System Events"
	set appPath to POSIX path of (path to application "Reminders")
	do shell script "open -g -a " & quoted form of appPath & " --hide"
end tell
tell application "Reminders"
	launch
end tell
delay 0.5
tell application "System Events"
	repeat 3 times
		if exists process "Reminders" then
			set visible of process "Reminders" to false
			exit repeat
		end if
		delay 0.2
	end repeat
end tell"""
		CMD2 = """tell application "System Events"
	set appPath to POSIX path of (path to application "Calendar")
	do shell script "open -g -a " & quoted form of appPath & " --hide"
end tell
tell application "Calendar"
	launch
end tell
delay 0.5
tell application "System Events"
	repeat 3 times
		if exists process "Calendar" then
			set visible of process "Calendar" to false
			exit repeat
		end if
		delay 0.2
	end repeat
end tell"""
		self._run_osascript_batch([CMD, CMD2])
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
end tell"""
			cmd2 = """tell application "Calendar"
	set theCalendarName to "Tomato"
	set theCalendarDescription to "Calendar for Tomato app."
	set theNewCalendar to make new calendar with properties {name:theCalendarName, description:theCalendarDescription}
end tell
"""
			cmd3 = """tell application "Calendar"
	set theCalendarName to "Tomato-old"
	set theCalendarDescription to "Calendar for the completed items."
	set theNewCalendar to make new calendar with properties {name:theCalendarName, description:theCalendarDescription}
end tell
"""
			try:
				self._run_osascript_batch([cmd, cmd2, cmd3])
				shutil.copy('All.csv', fulldir1)
				with open(fulldir2, 'w', encoding='utf-8') as f0:
					f0.write('1')
			except Exception as e:
				pass

	def clickbarss(self, index):
		self._suppress_diary_write = True
		try:
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
			if index == 3:
				self.textiii1.setText(contm)
				self.textiii1.ensureCursorVisible()  # 游标可用
				cursor = self.textiii1.textCursor()  # 设置游标
				pos = len(self.textiii1.toPlainText())  # 获取文本尾部的位置
				cursor.setPosition(pos)  # 游标位置设置为尾部
				self.textiii1.setTextCursor(cursor)  # 滚动到游标位置
		finally:
			self._suppress_diary_write = False

	def wordTab(self):
		conLayout = QVBoxLayout()

		self.tableWidget = QTableWidget()
		self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
		self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
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

		self.date_edit = QDateEdit(self)
		self.date_edit.setCalendarPopup(True)
		self.date_edit.setDisplayFormat('yyyy-MM-dd')
		self.date_edit.setDate(QDate.currentDate())
		self.date_edit.setFixedHeight(20)
		self.date_edit.setToolTip('Choose Date')

		self.time_edit = QTimeEdit(self)
		self.time_edit.setDisplayFormat('HH:mm')
		self.time_edit.setTime(QTime.currentTime())
		self.time_edit.setFixedHeight(20)
		self.time_edit.setToolTip('Choose Time')

		self._time_unit_items = [
			('None', None),
			('Minutes', 1 / 60),
			('Hours', 1),
			('Days', 24),
			('Weeks (7 days)', 24 * 7),
			('Months (30 days)', 24 * 30),
			('Years (365 days)', 24 * 365),
		]
		self._repeat_unit_items = list(self._time_unit_items)
		self._time_unit_hours_index = 0
		for idx, (_, factor) in enumerate(self._time_unit_items):
			if factor == 1:
				self._time_unit_hours_index = idx

		self.le3 = QLineEdit(self)
		self.le3.setPlaceholderText('Length')
		self.le3.setFixedHeight(20)

		self.length_unit = QComboBox(self)
		for label, factor in self._time_unit_items:
			self.length_unit.addItem(label, factor)
		self.length_unit.setCurrentIndex(self._time_unit_hours_index)

		self.le4 = QLineEdit(self)
		self.le4.setPlaceholderText('Repeat')
		self.le4.setFixedHeight(20)
		self.le4.textChanged.connect(self.refresh)

		self.repeat_unit = QComboBox(self)
		for label, factor in self._time_unit_items:
			self.repeat_unit.addItem(label, factor)
		self.repeat_unit.setCurrentIndex(self._time_unit_hours_index + 1)

		self.repeat_until_check = QCheckBox('Repeat until', self)
		self.repeat_until_check.setChecked(False)
		self.repeat_until_date = QDateEdit(self)
		self.repeat_until_date.setCalendarPopup(True)
		self.repeat_until_date.setDisplayFormat('yyyy-MM-dd')
		self.repeat_until_date.setDate(QDate.currentDate())
		self.repeat_until_date.setFixedHeight(20)
		self.repeat_until_date.setEnabled(False)
		self.repeat_until_check.toggled.connect(lambda _: self._apply_repeat_until_enable(self.repeat_until_check, self.repeat_until_date))

		b1_row1 = QHBoxLayout()
		b1_row1.setContentsMargins(0, 0, 0, 0)
		b1_row1.addWidget(self.le1)
		
		b1_row2 = QHBoxLayout()
		b1_row2.setContentsMargins(0, 0, 0, 0)
		b1_row2.addWidget(self.date_edit)
		b1_row2.addWidget(self.time_edit)
		b1_row2.addWidget(self.le3)
		b1_row2.addWidget(self.length_unit)
		b1_row2.addWidget(self.le4)
		b1_row2.addWidget(self.repeat_unit)

		b1_row3 = QHBoxLayout()
		b1_row3.setContentsMargins(0, 0, 0, 0)
		b1_row3.addWidget(self.repeat_until_check)
		b1_row3.addWidget(self.repeat_until_date)

		b1 = QVBoxLayout()
		b1.setContentsMargins(0, 0, 0, 0)
		b1.addLayout(b1_row1)
		b1.addLayout(b1_row2)
		b1.addLayout(b1_row3)
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
		# self.widget0.setFixedWidth(btn_t2.width() * 2)

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
		b2.addStretch()
		b2.addWidget(btn_t2)
		b2.addStretch()
		b2.addWidget(btn_t7)
		b2.addStretch()
		b2.addWidget(self.frame2)
		b2.addStretch()
		b2.addWidget(btn_t3)
		b2.addStretch()
		b2.addWidget(btn_t5)
		b2.addStretch()
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
		self._register_diary_refresh(self.textii1)
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
				escaped_old_text = self._escape_applescript_string(old_text)
				cmd = """tell application "Reminders"
					set mylist to list "Tomato"
					set reminderName to "%s" 
					tell mylist
						delete (reminders whose (name is reminderName) and (remind me date is date "%s"))
					end tell
				end tell""" % (escaped_old_text, otherStyleTime)
				cmd2 = """tell application "Calendar"
					tell calendar "Tomato"
						delete (events whose (start date is date "%s") and (summary is "%s"))
					end tell
				end tell""" % (otherStyleTime, escaped_old_text)
				self._run_osascript_batch([cmd, cmd2])

				new_text = self.tableWidget.item(self.changing_row, 0).text()
				escaped_new_text = self._escape_applescript_string(new_text)
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
				end tell""" % (escaped_new_text, otherStyleTime)
				cmd2 = """tell application "Calendar"
				  tell calendar "Tomato"
					make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
				  end tell
				end tell""" % (escaped_new_text, otherStyleTime, otherStyleTime, new_leng)
				self._run_osascript_batch([cmd, cmd2])
			if self.changing_column == 3:
				pass
			if self.changing_column == 4 and self.tableWidget.item(self.changing_row, 4).text() == 'UNDONE' and self.to_done == 2:
				new1_text = self.changing_text
				escaped_new1_text = self._escape_applescript_string(new1_text)
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
					end tell""" % (escaped_new1_text, otherStyleTime)
				cmd2 = '''tell application "Calendar"
					tell calendar "Tomato"
						make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)} 
					end tell
				end tell
				''' % (escaped_new1_text, otherStyleTime, otherStyleTime, old_length)
				self._run_osascript_batch([cmd, cmd2])
			if self.changing_column == 4 and self.tableWidget.item(self.changing_row, 4).text() == 'DONE' and self.to_done == 1:
				old_text = self.changing_text
				escaped_old_text = self._escape_applescript_string(old_text)
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
				end tell""" % (escaped_old_text, otherStyleTime)
				cmd2 = '''tell application "Calendar"
					tell calendar "Tomato"
						delete (events whose (start date is date "%s") and (summary is "%s"))
					end tell
					tell calendar "Tomato-old"
						make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)} 
					end tell
				end tell
				''' % (otherStyleTime, escaped_old_text, escaped_old_text, otherStyleTime, otherStyleTime, old_length)
				self._run_osascript_batch([cmd, cmd2])
				if self.tableWidget.item(self.changing_row, 3).text() != '-':
					outlist = []
					new_time_sns = []
					new_things_list = []
					new1_text = self.tableWidget.item(self.changing_row, 0).text()
					escaped_new1_text = self._escape_applescript_string(new1_text)
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
						end tell""" % (escaped_new1_text, otherStyleTime)
						cmd2 = """tell application "Calendar"
						  tell calendar "Tomato"
							make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
						  end tell
						end tell""" % (escaped_new1_text, otherStyleTime, otherStyleTime, new3_leng)
						self._run_osascript_batch([cmd, cmd2])
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
	
	def _get_selected_rows(self, table_widget):
		selection = table_widget.selectionModel()
		if selection is None:
			return []
		return sorted({index.row() for index in selection.selectedRows() if index.row() >= 0})

	def _init_sync_indicator(self):
		self._sync_counter = 0
		self.sync_dialog = QDialog(self)
		self.sync_dialog.setWindowTitle('Syncing...')
		self.sync_dialog.setModal(False)
		self.sync_dialog.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
		self.sync_dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
		layout = QVBoxLayout()
		layout.setContentsMargins(20, 15, 20, 15)
		label = QLabel('Synchronizing with Reminders / Calendar…\nPlease wait for a second.', self.sync_dialog)
		label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(label)
		self.sync_dialog.setLayout(layout)
		self.sync_dialog.adjustSize()
		self.sync_dialog.hide()

	def _show_sync_indicator(self):
		self._sync_counter += 1
		if self._sync_counter == 1:
			parent_geom = self.frameGeometry()
			dialog_size = self.sync_dialog.size()
			target_x = parent_geom.center().x() - dialog_size.width() // 2
			target_y = parent_geom.center().y() - dialog_size.height() // 2
			self.sync_dialog.move(int(target_x), int(target_y))
			self.sync_dialog.show()
			QApplication.processEvents()

	def _hide_sync_indicator(self):
		if self._sync_counter > 0:
			self._sync_counter -= 1
		if self._sync_counter <= 0:
			self._sync_counter = 0
			self.sync_dialog.hide()

	def _run_osascript_batch(self, script_chunks):
		if not script_chunks:
			return
		script = '\n'.join(script_chunks)
		self._show_sync_indicator()
		try:
			subprocess.call(['osascript', '-e', script])
			self._mark_local_reminder_change()
		except Exception:
			pass
		finally:
			self._hide_sync_indicator()

	def _mark_local_reminder_change(self):
		self._last_local_reminder_change = time.time()

	def _escape_applescript_string(self, value):
		if value is None:
			return ''
		escaped = value.replace('\\', '\\\\')
		escaped = escaped.replace('"', '\\"')
		return escaped

	def _write_time_csv_from_table(self):
		headers = []
		for col in range(self.tableWidget.columnCount()):
			header_item = self.tableWidget.horizontalHeaderItem(col)
			headers.append(header_item.text() if header_item else '')
		with open(self.fulldirall, 'w', encoding='utf8', newline='') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerow(headers)
			for row in range(self.tableWidget.rowCount()):
				row_values = []
				for col in range(self.tableWidget.columnCount()):
					item = self.tableWidget.item(row, col)
					if item and item.text() != '':
						row_values.append(item.text())
					elif item is None:
						row_values.append('')
					else:
						row_values.append('-')
				csv_writer.writerow(row_values)

	def _table_contains_row(self, table, values):
		col_count = len(values)
		for row in range(table.rowCount()):
			match = True
			for col in range(col_count):
				item = table.item(row, col)
				item_text = '' if item is None else item.text()
				if item_text != str(values[col]):
					match = False
					break
			if match:
				return True
		return False

	def _append_time_row_to_table(self, values):
		new_row = self.tableWidget.rowCount()
		self.tableWidget.insertRow(new_row)
		for col, value in enumerate(values):
			item = QTableWidgetItem(str(value))
			item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
			self.tableWidget.setItem(new_row, col, item)
		return new_row

	def _format_hours(self, hours):
		if isinstance(hours, float):
			hours = round(hours, 6)
			if abs(hours - round(hours)) < 1e-6:
				return str(int(round(hours)))
			return f"{hours:.6f}".rstrip('0').rstrip('.')
		elif isinstance(hours, int):
			return str(hours)
		return str(float(hours))

	def _convert_value_to_hours(self, value_text, unit_combo):
		value_text = value_text.strip()
		if value_text == '':
			return None
		try:
			value = float(value_text)
		except ValueError:
			return None
		factor = unit_combo.currentData()
		if factor is None:
			factor = 1
		hours = value * float(factor)
		return self._format_hours(hours)

	def _apply_repeat_until_enable(self, checkbox, date_edit):
		enabled = checkbox.isChecked()
		date_edit.setEnabled(enabled)

	def _get_repeat_until_stamp(self, checkbox, date_edit):
		if checkbox is None or date_edit is None or not checkbox.isChecked():
			return '-'
		try:
			end_date = date_edit.date().toPyDate()
			end_dt = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))
			return str(int(end_dt.timestamp()))
		except Exception:
			return '-'

	def _read_repeat_until_from_row(self, row):
		item = self.tableWidget.item(row, 6)
		if item is None:
			return None
		text = (item.text() or '').strip()
		if text in ('', '-'):
			return None
		try:
			return float(text)
		except ValueError:
			return None

	def _start_reminder_sync_worker(self):
		if self.reminder_sync_thread and self.reminder_sync_thread.is_alive():
			return
		try:
			self.reminder_sync_thread = ReminderSyncThread(self.reminder_sync_queue)
			self.reminder_sync_thread.start()
		except Exception:
			logging.exception("Failed to start reminder sync thread.")
			self.reminder_sync_thread = None
			if self.reminder_sync_timer.isActive():
				self.reminder_sync_timer.stop()

	def _start_calendar_sync_worker(self):
		if self.calendar_sync_thread and self.calendar_sync_thread.is_alive():
			return
		try:
			self.calendar_sync_thread = CalendarSyncThread(self.calendar_sync_queue)
			self.calendar_sync_thread.start()
		except Exception:
			logging.exception("Failed to start calendar sync thread.")
			self.calendar_sync_thread = None
			if self.reminder_sync_timer.isActive():
				self.reminder_sync_timer.stop()

	def _process_sync_messages(self):
		if self._sync_processing:
			return
		self._sync_processing = True
		try:
			self._drain_reminder_queue()
			self._drain_calendar_queue()
		finally:
			self._sync_processing = False

	def _drain_reminder_queue(self):
		if not self.reminder_sync_queue:
			return
		while True:
			try:
				message = self.reminder_sync_queue.get_nowait()
			except queue.Empty:
				break
			if message is None:
				continue
			snapshot, snapshot_timestamp = self._parse_reminder_sync_message(message)
			if snapshot is None:
				continue
			last_change = getattr(self, '_last_local_reminder_change', 0.0)
			if snapshot_timestamp is not None:
				if snapshot_timestamp < last_change:
					continue
				self._last_reminder_snapshot_ts = snapshot_timestamp
			self._handle_reminder_snapshot(snapshot)

	def _drain_calendar_queue(self):
		if not self.calendar_sync_queue:
			return
		while True:
			try:
				message = self.calendar_sync_queue.get_nowait()
			except queue.Empty:
				break
			if message is None:
				continue
			snapshot, snapshot_timestamp = self._parse_calendar_sync_message(message)
			if snapshot is None:
				continue
			last_change = getattr(self, '_last_local_reminder_change', 0.0)
			if snapshot_timestamp is not None:
				if snapshot_timestamp < last_change:
					continue
				self._last_calendar_snapshot_ts = snapshot_timestamp
			self._handle_calendar_snapshot(snapshot, snapshot_timestamp)

	def _parse_reminder_sync_message(self, message):
		if isinstance(message, dict):
			return message.get('snapshot'), message.get('timestamp')
		if isinstance(message, (tuple, list)) and len(message) == 2:
			first, second = message
			if isinstance(first, (int, float)):
				return second, first
			if isinstance(second, (int, float)):
				return first, second
		return message, None

	def _parse_calendar_sync_message(self, message):
		if isinstance(message, dict):
			return message.get('snapshot'), message.get('timestamp')
		if isinstance(message, (tuple, list)) and len(message) == 2:
			first, second = message
			if isinstance(first, (int, float)):
				return second, first
			if isinstance(second, (int, float)):
				return first, second
		return message, None

	def _handle_reminder_snapshot(self, snapshot):
		if not isinstance(snapshot, list):
			return
		remote_map = {}
		for entry in snapshot:
			name = entry.get('name', '').strip()
			stamp_value = self._normalize_stamp(entry.get('stamp'))
			if not name or not stamp_value:
				continue
			remote_map[(name, stamp_value)] = entry
		local_entries = self._collect_time_entries()
		commands = []
		table_changed = False

		for key, entry in remote_map.items():
			local_entry = local_entries.get(key)
			if not local_entry:
				continue
			if entry.get('completed') and local_entry.get('status') == 'UNDONE':
				row = self._find_time_row_by_key(*key)
				if row is None:
					continue
				rcmds, ccmds, row_done = self._complete_time_row(row, '')
				commands.extend(rcmds + ccmds)
				if row_done:
					table_changed = True

		for key, entry in remote_map.items():
			if key in local_entries:
				continue
			add_cmds = self._add_time_row_from_reminder(entry)
			if add_cmds is not None:
				if add_cmds:
					commands.extend(add_cmds)
				table_changed = True

		for key in list(local_entries.keys()):
			if key in remote_map:
				continue
			delete_cmds = self._delete_time_row_by_key(*key)
			if delete_cmds is not None:
				if delete_cmds:
					commands.extend(delete_cmds)
				table_changed = True

		if table_changed:
			self._refresh_stamp_column()
			self._write_time_csv_from_table()
			with contextlib.suppress(Exception):
				self.tableWidget.sortByColumn(8, Qt.SortOrder.AscendingOrder)
		if commands:
			self._run_osascript_batch(commands)

	def _handle_calendar_snapshot(self, snapshot, snapshot_ts=None):
		if not isinstance(snapshot, list):
			return
		if snapshot_ts and self._last_reminder_snapshot_ts:
			if snapshot_ts + 300 < self._last_reminder_snapshot_ts:
				return
		calendar_map = {}
		for entry in snapshot:
			name = (entry.get('name') or '').strip()
			stamp_value = self._normalize_stamp(entry.get('stamp'))
			if not name or not stamp_value:
				continue
			calendar_map[(name, stamp_value)] = entry
		local_entries = self._collect_time_entries()
		if not local_entries and not calendar_map:
			return

		commands = []
		table_changed = False

		# Handle time change (same name, different stamp) when unique
		name_to_local = {}
		for (lname, lstamp), info in local_entries.items():
			name_to_local.setdefault(lname, []).append((lstamp, info))

		for (cname, cstamp), entry in calendar_map.items():
			locals_for_name = name_to_local.get(cname, [])
			if (cname, cstamp) in local_entries:
				continue
			if len(locals_for_name) == 1:
				old_stamp, info = locals_for_name[0]
				row = info.get('row')
				if row is not None and self._update_time_row_from_calendar(row, entry):
					commands.extend(self._build_reminder_update_command(cname, old_stamp, cstamp))
					table_changed = True
					local_entries.pop((cname, old_stamp), None)
					local_entries[(cname, cstamp)] = info

		# Additions
		for key, entry in calendar_map.items():
			if key in local_entries:
				continue
			add_cmds = self._add_time_row_from_calendar(entry)
			if add_cmds is not None:
				if add_cmds:
					commands.extend(add_cmds)
				table_changed = True

		# Deletions
		for key, info in list(local_entries.items()):
			if key in calendar_map:
				continue
			row = info.get('row')
			if row is None:
				continue
			del_cmds = self._delete_time_row_by_key(key[0], key[1])
			if del_cmds is not None:
				if del_cmds:
					commands.extend(del_cmds)
				table_changed = True

		if table_changed:
			self._refresh_stamp_column()
			self._write_time_csv_from_table()
			with contextlib.suppress(Exception):
				self.tableWidget.sortByColumn(8, Qt.SortOrder.AscendingOrder)
		if commands:
			self._run_osascript_batch(commands)

	def _collect_time_entries(self):
		entries = {}
		for row in range(self.tableWidget.rowCount()):
			type_item = self.tableWidget.item(row, 7)
			if type_item is None or type_item.text() != 'TIME_SNS':
				continue
			name_item = self.tableWidget.item(row, 0)
			if name_item is None or name_item.text() == '':
				continue
			stamp_value = self._stamp_from_items(self.tableWidget.item(row, 8), self.tableWidget.item(row, 1))
			if not stamp_value:
				continue
			status_item = self.tableWidget.item(row, 4)
			entries[(name_item.text(), stamp_value)] = {
				'status': status_item.text() if status_item else '',
				'row': row
			}
		return entries

	def _normalize_stamp(self, value):
		if value in (None, ''):
			return ''
		try:
			return str(int(float(value)))
		except (ValueError, TypeError):
			return ''

	def _stamp_from_items(self, stamp_item, time_item):
		if stamp_item and stamp_item.text():
			normalized = self._normalize_stamp(stamp_item.text())
			if normalized:
				return normalized
		if time_item and time_item.text():
			try:
				return self._normalize_stamp(self.to_stamp(time_item.text()))
			except Exception:
				return ''
		return ''

	def _find_time_row_by_key(self, name, stamp_value):
		target_stamp = self._normalize_stamp(stamp_value)
		for row in range(self.tableWidget.rowCount()):
			type_item = self.tableWidget.item(row, 7)
			if type_item is None or type_item.text() != 'TIME_SNS':
				continue
			name_item = self.tableWidget.item(row, 0)
			if name_item is None:
				continue
			row_stamp = self._stamp_from_items(self.tableWidget.item(row, 8), self.tableWidget.item(row, 1))
			if name_item.text() == name and row_stamp == target_stamp:
				return row
		return None

	def _add_time_row_from_reminder(self, entry):
		name = entry.get('name', '').strip()
		stamp_value = self._normalize_stamp(entry.get('stamp'))
		if not name or not stamp_value:
			return None
		try:
			stamp_int = int(stamp_value)
		except ValueError:
			return None
		dt = datetime.datetime.fromtimestamp(stamp_int)
		time_text = dt.strftime("%Y-%m-%d %H:%M")
		otherStyleTime = dt.strftime("%m/%d/%Y %H:%M")
		row_values = [name, time_text, '1', '-', 'UNDONE', '-', '-', 'TIME_SNS', stamp_value]
		self._append_time_row_to_table(row_values)
		escaped_name = self._escape_applescript_string(name)
		cmd = """tell application "Calendar"
	tell calendar "Tomato"
		make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (1 * hours)}
	end tell
end tell""" % (escaped_name, otherStyleTime, otherStyleTime)
		return [cmd]

	def _delete_time_row_by_key(self, name, stamp_value):
		row = self._find_time_row_by_key(name, stamp_value)
		if row is None:
			return []
		time_item = self.tableWidget.item(row, 1)
		otherStyleTime = None
		stamp_to_use = stamp_value or self._stamp_from_items(self.tableWidget.item(row, 8), time_item)
		if stamp_to_use:
			with contextlib.suppress(Exception):
				time_struct = time.localtime(int(stamp_to_use))
				otherStyleTime = time.strftime("%m/%d/%Y %H:%M", time_struct)
		if otherStyleTime is None and time_item and time_item.text():
			with contextlib.suppress(Exception):
				time_struct = time.localtime(int(self.to_stamp(time_item.text())))
				otherStyleTime = time.strftime("%m/%d/%Y %H:%M", time_struct)
		self.tableWidget.removeRow(row)
		if otherStyleTime is None:
			return []
		escaped_name = self._escape_applescript_string(name)
		cmd1 = """tell application "Reminders"
	set mylist to list "Tomato"
	tell mylist
		delete (reminders whose (name is "%s") and (remind me date is date "%s"))
	end tell
end tell""" % (escaped_name, otherStyleTime)
		cmd2 = """tell application "Calendar"
	tell calendar "Tomato"
		delete (events whose (start date is date "%s") and (summary is "%s"))
	end tell
end tell""" % (otherStyleTime, escaped_name)
		return [cmd1, cmd2]

	def _add_time_row_from_calendar(self, entry):
		name = (entry.get('name') or '').strip()
		stamp_value = self._normalize_stamp(entry.get('stamp'))
		if not name or not stamp_value:
			return None
		try:
			stamp_int = int(stamp_value)
		except ValueError:
			return None
		dt = datetime.datetime.fromtimestamp(stamp_int)
		time_text = dt.strftime("%Y-%m-%d %H:%M")
		duration = entry.get('duration') or 0
		length_hours = self._format_hours(round(duration / 3600, 6)) if duration else '1'
		row_values = [name, time_text, length_hours, '-', 'UNDONE', '-', '-', 'TIME_SNS', stamp_value]
		self._append_time_row_to_table(row_values)
		escaped_name = self._escape_applescript_string(name)
		otherStyleTime = dt.strftime("%m/%d/%Y %H:%M")
		cmd = """tell application "Reminders"
	set eachLine to "%s"
	set mylist to list "Tomato"
	tell mylist
		make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
	end tell
end tell""" % (escaped_name, otherStyleTime)
		return [cmd]

	def _update_time_row_from_calendar(self, row, entry):
		name = (entry.get('name') or '').strip()
		stamp_value = self._normalize_stamp(entry.get('stamp'))
		if not name or not stamp_value:
			return False
		try:
			stamp_int = int(stamp_value)
		except ValueError:
			return False
		dt = datetime.datetime.fromtimestamp(stamp_int)
		time_text = dt.strftime("%Y-%m-%d %H:%M")
		duration = entry.get('duration') or 0
		length_hours = self.tableWidget.item(row, 2).text() if self.tableWidget.item(row, 2) else '1'
		if duration:
			length_hours = self._format_hours(round(duration / 3600, 6))
		self.tableWidget.setItem(row, 1, QTableWidgetItem(time_text))
		self.tableWidget.setItem(row, 8, QTableWidgetItem(stamp_value))
		self.tableWidget.setItem(row, 2, QTableWidgetItem(str(length_hours)))
		return True

	def _build_reminder_update_command(self, name, old_stamp, new_stamp):
		escaped_name = self._escape_applescript_string(name)
		try:
			old_time = time.strftime("%m/%d/%Y %H:%M", time.localtime(int(old_stamp)))
			new_time = time.strftime("%m/%d/%Y %H:%M", time.localtime(int(new_stamp)))
		except Exception:
			return []
		cmd = """tell application "Reminders"
	set mylist to list "Tomato"
	tell mylist
		set remind me date of (reminders whose (name is "%s") and (remind me date is date "%s")) to date "%s"
	end tell
end tell""" % (escaped_name, old_time, new_time)
		return [cmd]

	def _refresh_stamp_column(self):
		for row in range(self.tableWidget.rowCount()):
			time_item = self.tableWidget.item(row, 1)
			if not time_item or time_item.text() == '':
				continue
			with contextlib.suppress(Exception):
				stamp_str = self._normalize_stamp(self.to_stamp(time_item.text()))
				if stamp_str:
					self.tableWidget.setItem(row, 8, QTableWidgetItem(stamp_str))


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
		selected_date = self.date_edit.date()
		selected_time = self.time_edit.time()
		tim2_inp = f"{selected_date.toString('yyyy-MM-dd')} {selected_time.toString('HH:mm')}"
		length_hours = self._convert_value_to_hours(self.le3.text(), self.length_unit)
		if length_hours is None:
			return
		repeat_input = self.le4.text()
		repeat_hours = '-'
		if repeat_input.strip() != '':
			repeat_converted = self._convert_value_to_hours(repeat_input, self.repeat_unit)
			if repeat_converted is None:
				repeat_converted = '-'
			repeat_hours = repeat_converted
		sta5_inp = 'UNDONE'
		tar6_inp = '-'
		pro7_inp = self._get_repeat_until_stamp(self.repeat_until_check, self.repeat_until_date)
		typ8_inp = 'TIME_SNS'
		pattern = re.compile(r'{(.*?)}')
		result = pattern.findall(self.le1.text().replace('\n', ''))
		notes = ''.join(result)
		sta9_inp = ''
		if ite1_inp != '' and length_hours is not None and selected_date.isValid() and selected_time.isValid():
			try:
				sta9_inp = str(self.to_stamp(tim2_inp))
			except Exception as e:
				pass
			if sta9_inp != '':
				new_time_sns.append(ite1_inp)
				new_time_sns.append(tim2_inp)
				new_time_sns.append(length_hours)
				new_time_sns.append(repeat_hours)
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
				escaped_item = self._escape_applescript_string(ite1_inp)
				escaped_notes = self._escape_applescript_string(notes)
				cmd = """tell application "Reminders"
	set eachLine to "%s"
	set mylist to list "Tomato"
	tell mylist
		make new reminder at end with properties {name:eachLine, remind me date:date "%s", body:"%s"}
	end tell
end tell""" % (escaped_item, otherStyleTime, escaped_notes)
				cmd2 = """tell application "Calendar"
  tell calendar "Tomato"
	make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
  end tell
end tell""" % (escaped_item, otherStyleTime, otherStyleTime, length_hours)
				self._run_osascript_batch([cmd, cmd2])
				self.le1.clear()
				self.le3.clear()
				self.le4.setText("-")
				self.le4.clear()
				self.length_unit.setCurrentIndex(self._time_unit_hours_index)
				self.repeat_unit.setCurrentIndex(self._time_unit_hours_index + 1)
				self.repeat_until_check.setChecked(False)
				self.repeat_until_date.setDate(QDate.currentDate())
				self.date_edit.setDate(QDate.currentDate())
				self.time_edit.setTime(QTime.currentTime())

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
			escaped_find_item = self._escape_applescript_string(find_item)
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
	end tell""" % (escaped_find_item, otherStyleTime)
			cmd2 = """tell application "Calendar"
		tell calendar "Tomato"
			delete (events whose (start date is date "%s") and (summary is "%s"))
		end tell
	end tell""" % (otherStyleTime, escaped_find_item)
			self._run_osascript_batch([cmd, cmd2])
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
		end tell"""
		self._run_osascript_batch([cmd])

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
		if self._suppress_diary_write:
			return
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

	def _complete_time_row(self, row, comment_text):
		reminder_cmds = []
		calendar_cmds = []
		self.tableWidget.setCurrentCell(row, 0)
		self.change_write()
		status_item = self.tableWidget.item(row, 4)
		if status_item is None or status_item.text() != 'UNDONE':
			return reminder_cmds, calendar_cmds, False
		self.tableWidget.setItem(row, 4, QTableWidgetItem('DONE'))
		self.tableWidget.item(row, 4).setTextAlignment(
			Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
		if self.widget0.currentIndex() == 2:
			self.tableWidget.setRowHidden(row, True)

		old_text = self.changing_text
		escaped_old_text = self._escape_applescript_string(old_text)
		old_date = self.changing_date
		old_length = self.changing_length
		old_time_stamp = self.to_stamp(old_date)
		timeArray = time.localtime(float(old_time_stamp))
		otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
		reminder_cmds.append("""tell application "Reminders"
	set mylist to list "Tomato"
	tell mylist
		set completed of (reminders whose (name is "%s") and (remind me date is date "%s")) to true
	end tell
end tell""" % (escaped_old_text, otherStyleTime))
		calendar_cmds.append('''tell application "Calendar"
	tell calendar "Tomato"
		delete (events whose (start date is date "%s") and (summary is "%s"))
	end tell
	tell calendar "Tomato-old"
		make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)} 
	end tell
end tell
''' % (otherStyleTime, escaped_old_text, escaped_old_text, otherStyleTime, otherStyleTime, old_length))

		repeat_item = self.tableWidget.item(self.changing_row, 3)
		if repeat_item and repeat_item.text() not in ('', '-'):
			try:
				repeat_hours = float(repeat_item.text())
			except ValueError:
				repeat_hours = None
			if repeat_hours is not None:
				new1_text = self.tableWidget.item(self.changing_row, 0).text()
				new_time = self.tableWidget.item(self.changing_row, 1).text()
				repeat_end_stamp = self._read_repeat_until_from_row(self.changing_row)
				new_stamp = None
				try:
					base_stamp = float(self.to_stamp(new_time))
				except Exception:
					base_stamp = None
				if base_stamp is not None:
					new_stamp = base_stamp + 3600 * repeat_hours
					if repeat_end_stamp is not None and new_stamp > repeat_end_stamp:
						new_stamp = None
				if new_stamp is not None:
					next_time_array = time.localtime(new_stamp)
					otherStyleTime_new = time.strftime("%m/%d/%Y %H:%M", next_time_array)
					new2_time = time.strftime("%Y-%m-%d %H:%M", next_time_array)
					new3_leng = self.tableWidget.item(self.changing_row, 2).text()
					new4_rep = repeat_item.text()
					new5_sta = 'UNDONE'
					new6_tar = '-'
					new7_pro = self.tableWidget.item(self.changing_row, 6).text() if self.tableWidget.item(self.changing_row, 6) else '-'
					new8_typ = 'TIME_SNS'
					new9_sta = str(new_stamp)
					new_row_values = [new1_text, new2_time, new3_leng, new4_rep,
									  new5_sta, new6_tar, new7_pro, new8_typ, new9_sta]
					if not self._table_contains_row(self.tableWidget, new_row_values):
						new_row_index = self._append_time_row_to_table(new_row_values)
						self.tableWidget.setRowHidden(new_row_index, False)
					escaped_new1_text = self._escape_applescript_string(new1_text)
					reminder_cmds.append("""tell application "Reminders"
	set eachLine to "%s"
	set mylist to list "Tomato"
	tell mylist
		make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
	end tell
end tell""" % (escaped_new1_text, otherStyleTime_new))
					calendar_cmds.append("""tell application "Calendar"
  tell calendar "Tomato"
	make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
  end tell
end tell""" % (escaped_new1_text, otherStyleTime_new, otherStyleTime_new, new3_leng))

		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
		self.textii1.setText(contm)
		self.textii1.ensureCursorVisible()
		cursor = self.textii1.textCursor()
		pos = len(self.textii1.toPlainText())
		cursor.setPosition(pos)
		self.textii1.setTextCursor(cursor)

		ISOTIMEFORMAT = '%H:%M:%S '
		now_display_time = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		parta = '\n\n- ' + str(now_display_time)
		partb = 'Completed ' + self.changing_text + ' scheduled for ' + self.changing_date
		partc = ''
		if comment_text != '':
			partc = '\n\t- ' + comment_text
		with open(diary_file, 'a', encoding='utf-8') as f0:
			f0.write(parta + partb + partc)
		contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
		self.textii1.setText(contm)
		self.textii1.ensureCursorVisible()
		cursor = self.textii1.textCursor()
		pos = len(self.textii1.toPlainText())
		cursor.setPosition(pos)
		self.textii1.setTextCursor(cursor)

		repeat_item = self.tableWidget.item(self.changing_row, 3)
		if repeat_item and repeat_item.text() != '-':
			record_name = self.tableWidget.item(self.changing_row, 0).text() + '.csv'
			record_file = os.path.join(self.fulldir_rec, record_name)
			out_list = []
			item_list = []
			comments = 'No comment'
			if comment_text != '':
				comments = comment_text
			item_list.append(self.changing_date)
			item_list.append(comments)
			out_list.append(item_list)
			with open(record_file, 'a', encoding='utf8') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerows(out_list)
			input_table = pd.read_csv(record_file)
			input_table_rows = input_table.shape[0]
			self.input_table_colunms = input_table.shape[1]
			input_table_header = input_table.columns.values.tolist()
			self.tableWidget_record.setColumnCount(self.input_table_colunms)
			self.tableWidget_record.setRowCount(input_table_rows + 1)
			self.tableWidget_record.setHorizontalHeaderLabels(input_table_header)
			self.tableWidget_record.verticalHeader().setVisible(False)
			t = 0
			while t >= 0 and t <= input_table_rows:
				csv_reader = csv.reader(open(record_file, encoding='utf-8'))
				for each_row in csv_reader:
					if t <= input_table_rows:
						i = 0
						while i >= 0 and i <= self.input_table_colunms - 1:
							self.tableWidget_record.setItem(t, i, QTableWidgetItem(str(each_row[i])))
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

		self.tableWidget_record.setCurrentCell(self.tableWidget_record.rowCount() - 1, 0)
		self.orderType = Qt.SortOrder.AscendingOrder
		self.tableWidget.sortByColumn(8, self.orderType)
		self.tableWidget.setCurrentCell(self.changing_row, 0)
		self.changing_bool = 0
		return reminder_cmds, calendar_cmds, True

	def save_and_done(self):
		selected_rows = self._get_selected_rows(self.tableWidget)
		if not selected_rows and self.tableWidget.currentItem() is not None:
			selected_rows = [self.tableWidget.currentRow()]
		comment_text = self.textw1.toPlainText()
		processed = False
		reminder_cmds = []
		calendar_cmds = []
		for row in selected_rows:
			rcmds, ccmds, row_done = self._complete_time_row(row, comment_text)
			reminder_cmds.extend(rcmds)
			calendar_cmds.extend(ccmds)
			if row_done:
				processed = True
		if processed:
			for n in range(self.tableWidget.rowCount()):
				time_item = self.tableWidget.item(n, 1)
				if time_item and time_item.text() != '':
					self.tableWidget.setItem(n, 8, QTableWidgetItem(str(self.to_stamp(time_item.text()))))
			self._write_time_csv_from_table()
		self._run_osascript_batch(reminder_cmds + calendar_cmds)
		if processed:
			self.le4.setText('-')
			self.le4.setText('')
			self.textw1.clear()
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
		self.tableWidget_freq.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
		self.tableWidget_freq.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
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
		# self.widget1.setFixedWidth(btn_t2.width() * 2)

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
		b2.addStretch()
		b2.addWidget(btn_t2)
		b2.addStretch()
		b2.addWidget(btn_t7)
		b2.addStretch()
		b2.addWidget(self.freq1)
		b2.addStretch()
		b2.addWidget(btn_t3)
		b2.addStretch()
		b2.addWidget(btn_t5)
		b2.addStretch()
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

		self.freq_date_edit = QDateEdit(self)
		self.freq_date_edit.setCalendarPopup(True)
		self.freq_date_edit.setDisplayFormat('yyyy-MM-dd')
		self.freq_date_edit.setDate(QDate.currentDate())
		self.freq_date_edit.setFixedHeight(20)
		self.freq_date_edit.setToolTip('Choose Date')

		self.freq_time_edit = QTimeEdit(self)
		self.freq_time_edit.setDisplayFormat('HH:mm')
		self.freq_time_edit.setTime(QTime.currentTime())
		self.freq_time_edit.setFixedHeight(20)
		self.freq_time_edit.setToolTip('Choose Time')

		self.lf4 = QLineEdit(self)
		self.lf4.setPlaceholderText('Length')
		self.lf4.setFixedHeight(20)

		self.freq_length_unit = QComboBox(self)
		for label, factor in self._time_unit_items:
			self.freq_length_unit.addItem(label, factor)
		self.freq_length_unit.setCurrentIndex(self._time_unit_hours_index)
		self.freq_length_unit.setFixedWidth(100)

		self.lf5 = QLineEdit(self)
		self.lf5.setPlaceholderText('Repeat')
		self.lf5.setFixedHeight(20)

		self.freq_repeat_unit = QComboBox(self)
		for label, factor in self._repeat_unit_items:
			self.freq_repeat_unit.addItem(label, factor)
		self.freq_repeat_unit.setCurrentIndex(0)
		self.freq_repeat_unit.setFixedWidth(100)

		self.freq_repeat_until_check = QCheckBox('Repeat until', self)
		self.freq_repeat_until_check.setChecked(False)
		self.freq_repeat_until_date = QDateEdit(self)
		self.freq_repeat_until_date.setCalendarPopup(True)
		self.freq_repeat_until_date.setDisplayFormat('yyyy-MM-dd')
		self.freq_repeat_until_date.setDate(QDate.currentDate())
		self.freq_repeat_until_date.setFixedHeight(20)
		self.freq_repeat_until_date.setEnabled(False)
		self.freq_repeat_until_check.toggled.connect(lambda _: self._apply_repeat_until_enable(self.freq_repeat_until_check, self.freq_repeat_until_date))

		length_repeat_row = QHBoxLayout()
		length_repeat_row.setContentsMargins(0, 0, 0, 0)
		length_repeat_row.addWidget(self.lf4)
		length_repeat_row.addWidget(self.freq_length_unit)
		length_repeat_row.addWidget(self.lf5)
		length_repeat_row.addWidget(self.freq_repeat_unit)

		freq_until_row = QHBoxLayout()
		freq_until_row.setContentsMargins(0, 0, 0, 0)
		freq_until_row.addWidget(self.freq_repeat_until_check)
		freq_until_row.addWidget(self.freq_repeat_until_date)

		btn_t5 = QPushButton('Copy to Time-sensitive list', self)
		btn_t5.clicked.connect(self.freq_move_time)
		btn_t5.setFixedHeight(20)
		freq_datetime_row = QHBoxLayout()
		freq_datetime_row.setContentsMargins(0, 0, 0, 0)
		freq_datetime_row.addWidget(self.freq_date_edit)
		freq_datetime_row.addWidget(self.freq_time_edit)

		b3 = QVBoxLayout()
		b3.setContentsMargins(0, 0, 0, 0)
		b3.addWidget(self.textw2)
		b3.addWidget(btn_t4)
		b3.addWidget(self.freq2)
		b3.addLayout(freq_datetime_row)
		b3.addLayout(length_repeat_row)
		b3.addLayout(freq_until_row)
		b3.addWidget(btn_t5)
		t3.setLayout(b3)

		t4 = QWidget()
		self.textii2 = QTextEdit(self)
		self.textii2.setReadOnly(False)
		self.textii2.textChanged.connect(self.freq_text_change)
		self._register_diary_refresh(self.textii2)
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
		if self._suppress_diary_write:
			return
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

	def _freq_add_time_single(self):
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

	def freq_add_time(self):
		selected_rows = self._get_selected_rows(self.tableWidget_freq)
		if not selected_rows and self.tableWidget_freq.currentItem() != None:
			selected_rows = [self.tableWidget_freq.currentRow()]
		if not selected_rows:
			return
		comment_text = self.textw2.toPlainText()
		for index, row in enumerate(selected_rows):
			self.tableWidget_freq.setCurrentCell(row, 0)
			if index > 0 and comment_text != '':
				self.textw2.setPlainText(comment_text)
			self._freq_add_time_single()
		self.textw2.clear()
		self.lf2.setText('-')
		self.lf2.clear()
		self.tableWidget_freq.clearSelection()
		self.tableWidget_freq.clearFocus()
		self.tableWidget_freq.setCurrentItem(None)

	def freq_move_time(self):  # copy to time
		if self.tableWidget_freq.currentItem() != None:
			new_time_sns = []
			outerlist = []
			ite1_inp = self.tableWidget_freq.item(self.tableWidget_freq.currentIndex().row(), 0).text()
			selected_date = self.freq_date_edit.date()
			selected_time = self.freq_time_edit.time()
			if not (selected_date.isValid() and selected_time.isValid()):
				return
			tim2_inp = f"{selected_date.toString('yyyy-MM-dd')} {selected_time.toString('HH:mm')}"
			length_hours = self._convert_value_to_hours(self.lf4.text(), self.freq_length_unit)
			if length_hours is None:
				return
			repeat_input = self.lf5.text()
			repeat_hours = '-'
			if repeat_input.strip() != '':
				repeat_converted = self._convert_value_to_hours(repeat_input, self.freq_repeat_unit)
				if repeat_converted is None:
					return
				repeat_hours = repeat_converted
			sta5_inp = 'UNDONE'
			tar6_inp = '-'
			pro7_inp = self._get_repeat_until_stamp(self.freq_repeat_until_check, self.freq_repeat_until_date)
			typ8_inp = 'TIME_SNS'
			sta9_inp = ''
			if ite1_inp != '' and tim2_inp != '' and self.tableWidget_freq.item(self.tableWidget_freq.currentIndex().row(), 0) != None:
				try:
					sta9_inp = str(self.to_stamp(tim2_inp))
				except Exception as e:
					pass
				if sta9_inp != '':
					new_time_sns.append(ite1_inp)
					new_time_sns.append(tim2_inp)
					new_time_sns.append(length_hours)
					new_time_sns.append(repeat_hours)
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
					escaped_ite1_inp = self._escape_applescript_string(ite1_inp)
					cmd = """tell application "Reminders"
						set eachLine to "%s"
						set mylist to list "Tomato"
						tell mylist
							make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
						end tell
					end tell""" % (escaped_ite1_inp, otherStyleTime)
					cmd2 = """tell application "Calendar"
					  tell calendar "Tomato"
						make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
					  end tell
					end tell""" % (escaped_ite1_inp, otherStyleTime, otherStyleTime, length_hours)
					self._run_osascript_batch([cmd, cmd2])
					self.freq_date_edit.setDate(QDate.currentDate())
					self.freq_time_edit.setTime(QTime.currentTime())
					self.lf4.clear()
					self.lf5.clear()
					self.freq_length_unit.setCurrentIndex(self._time_unit_hours_index)
					self.freq_repeat_unit.setCurrentIndex(0)
					self.freq_repeat_until_check.setChecked(False)
					self.freq_repeat_until_date.setDate(QDate.currentDate())
					self.le4.setText('-')
					self.le4.clear()

	def inspiTab(self):
		self.tableWidget_memo = QTableWidget()
		self.tableWidget_memo.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
		self.tableWidget_memo.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
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
		# self.widget2.setFixedWidth(btn_t2.width() * 2)

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
		b2.addStretch()
		b2.addWidget(btn_t2)
		b2.addStretch()
		b2.addWidget(btn_t7)
		b2.addStretch()
		b2.addWidget(self.memo1)
		b2.addStretch()
		b2.addWidget(btn_t3)
		b2.addStretch()
		b2.addWidget(btn_t5)
		b2.addStretch()
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

		self.memo_date_edit = QDateEdit(self)
		self.memo_date_edit.setCalendarPopup(True)
		self.memo_date_edit.setDisplayFormat('yyyy-MM-dd')
		self.memo_date_edit.setDate(QDate.currentDate())
		self.memo_date_edit.setFixedHeight(20)
		self.memo_date_edit.setToolTip('Choose Date')

		self.memo_time_edit = QTimeEdit(self)
		self.memo_time_edit.setDisplayFormat('HH:mm')
		self.memo_time_edit.setTime(QTime.currentTime())
		self.memo_time_edit.setFixedHeight(20)
		self.memo_time_edit.setToolTip('Choose Time')

		self.lm4 = QLineEdit(self)
		self.lm4.setPlaceholderText('Length')
		self.lm4.setFixedHeight(20)

		self.memo_length_unit = QComboBox(self)
		for label, factor in self._time_unit_items:
			self.memo_length_unit.addItem(label, factor)
		self.memo_length_unit.setCurrentIndex(self._time_unit_hours_index)
		self.memo_length_unit.setFixedWidth(100)

		self.lm5 = QLineEdit(self)
		self.lm5.setPlaceholderText('Repeat')
		self.lm5.setFixedHeight(20)

		self.memo_repeat_unit = QComboBox(self)
		for label, factor in self._repeat_unit_items:
			self.memo_repeat_unit.addItem(label, factor)
		self.memo_repeat_unit.setCurrentIndex(0)
		self.memo_repeat_unit.setFixedWidth(100)

		self.memo_repeat_until_check = QCheckBox('Repeat until', self)
		self.memo_repeat_until_check.setChecked(False)
		self.memo_repeat_until_date = QDateEdit(self)
		self.memo_repeat_until_date.setCalendarPopup(True)
		self.memo_repeat_until_date.setDisplayFormat('yyyy-MM-dd')
		self.memo_repeat_until_date.setDate(QDate.currentDate())
		self.memo_repeat_until_date.setFixedHeight(20)
		self.memo_repeat_until_date.setEnabled(False)
		self.memo_repeat_until_check.toggled.connect(lambda _: self._apply_repeat_until_enable(self.memo_repeat_until_check, self.memo_repeat_until_date))

		memo_length_repeat_row = QHBoxLayout()
		memo_length_repeat_row.setContentsMargins(0, 0, 0, 0)
		memo_length_repeat_row.addWidget(self.lm4)
		memo_length_repeat_row.addWidget(self.memo_length_unit)
		memo_length_repeat_row.addWidget(self.lm5)
		memo_length_repeat_row.addWidget(self.memo_repeat_unit)

		memo_until_row = QHBoxLayout()
		memo_until_row.setContentsMargins(0, 0, 0, 0)
		memo_until_row.addWidget(self.memo_repeat_until_check)
		memo_until_row.addWidget(self.memo_repeat_until_date)

		btn_t5 = QPushButton('Copy to Time-sensitive list', self)
		btn_t5.clicked.connect(self.memo_copy_to_time)
		btn_t5.setFixedHeight(20)
		memo_datetime_row = QHBoxLayout()
		memo_datetime_row.setContentsMargins(0, 0, 0, 0)
		memo_datetime_row.addWidget(self.memo_date_edit)
		memo_datetime_row.addWidget(self.memo_time_edit)

		b3 = QVBoxLayout()
		b3.setContentsMargins(0, 0, 0, 0)
		b3.addWidget(self.textw3)
		b3.addWidget(btn_t4)
		b3.addWidget(self.memo2)
		b3.addLayout(memo_datetime_row)
		b3.addLayout(memo_length_repeat_row)
		b3.addLayout(memo_until_row)
		b3.addWidget(btn_t5)
		t3.setLayout(b3)

		t4 = QWidget()
		self.textii3 = QTextEdit(self)
		self.textii3.setReadOnly(False)
		self.textii3.textChanged.connect(self.memo_text_change)
		self._register_diary_refresh(self.textii3)
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

	def collectTab(self):
		self.collection_current_file = None
		self._collection_loading = False
		self._collection_table_block = False
		self._collection_preview_updating = False
		self._collection_last_markdown = ''

		self.collection_table = QTableWidget()
		self.collection_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
		self.collection_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
		self.collection_table.setAutoScroll(False)
		self.collection_table.verticalHeader().setVisible(True)
		self.collection_table.itemSelectionChanged.connect(self._update_collection_markdown_preview)
		self.collection_table.itemChanged.connect(self._handle_collection_item_changed)

		self.collection_md_editor = QPlainTextEdit(self)
		self.collection_md_editor.setPlaceholderText('Select a row to view it as Markdown.')
		self.collection_md_editor.setReadOnly(True)
		self.collection_md_editor.textChanged.connect(self._handle_collection_markdown_change)

		splitter = QSplitter(Qt.Orientation.Horizontal)
		splitter.addWidget(self.collection_table)
		splitter.addWidget(self.collection_md_editor)
		splitter.setStretchFactor(0, 2)
		splitter.setStretchFactor(1, 1)

		self.collection_file_combo = QComboBox(self)
		self.collection_file_combo.currentIndexChanged.connect(self._collection_file_changed)

		btn_new_csv = QPushButton('New', self)
		btn_new_csv.clicked.connect(self._collection_new_file)
		btn_delete_csv = QPushButton('Delete', self)
		btn_delete_csv.clicked.connect(self._collection_delete_file)
		btn_open_dir = QPushButton('Open Folder', self)
		btn_open_dir.clicked.connect(self._open_collection_dir)

		btn_t3 = QPushButton('Export plan', self)
		btn_t3.clicked.connect(self.export_plan)
		btn_t3.setFixedHeight(20)

		btn_t5 = QPushButton('Export diary', self)
		btn_t5.clicked.connect(self.export_diary)
		btn_t5.setFixedHeight(20)

		btn_t6 = QPushButton('Export records', self)
		btn_t6.clicked.connect(self.export_record)
		btn_t6.setFixedHeight(20)

		t4 = QWidget()
		t4.setFixedHeight(20)
		b4 = QHBoxLayout()
		b4.setContentsMargins(0, 0, 0, 0)
		b4.addWidget(btn_new_csv)
		b4.addWidget(btn_delete_csv)
		t4.setLayout(b4)

		self.frame21 = QFrame(self)
		self.frame21.setFrameShape(QFrame.Shape.HLine)
		self.frame21.setFrameShadow(QFrame.Shadow.Sunken)

		t2 = QWidget()
		file_bar = QVBoxLayout()
		file_bar.setContentsMargins(0, 0, 0, 0)
		#file_bar.addStretch()
		# file_bar.addWidget(QLabel('CSV File:', self))
		file_bar.addWidget(self.collection_file_combo, 1)
		# file_bar.addWidget(btn_new_csv)
		# file_bar.addWidget(btn_delete_csv)
		file_bar.addStretch()
		file_bar.addWidget(t4)
		file_bar.addStretch()
		file_bar.addWidget(btn_open_dir)
		file_bar.addStretch()
		file_bar.addWidget(self.frame21)
		file_bar.addStretch()
		file_bar.addWidget(btn_t3)
		file_bar.addStretch()
		file_bar.addWidget(btn_t5)
		file_bar.addStretch()
		file_bar.addWidget(btn_t6)
		#file_bar.addStretch()
		# file_bar.addWidget(btn_manage_columns)
		t2.setLayout(file_bar)

		self.collection_search_input = QLineEdit(self)
		self.collection_search_input.setPlaceholderText('Search…')
		self.collection_search_input.textChanged.connect(self._collection_apply_search)
		btn_clear_search = QPushButton('Clear', self)
		btn_clear_search.setFixedWidth(120)
		btn_clear_search.clicked.connect(self._collection_clear_search)
		search_bar = QHBoxLayout()
		search_bar.setContentsMargins(0, 0, 0, 0)
		# search_bar.addWidget(QLabel('Search:', self))
		search_bar.addWidget(self.collection_search_input, 1)
		search_bar.addWidget(btn_clear_search)

		self.collection_sort_column_combo = QComboBox(self)
		self.collection_sort_column_combo.setFixedHeight(20)
		self.collection_sort_mode_combo = QComboBox(self)
		self.collection_sort_mode_combo.setFixedHeight(20)
		self.collection_sort_mode_combo.addItem('Text', 'text')
		self.collection_sort_mode_combo.addItem('Number', 'number')
		self.collection_sort_mode_combo.addItem('Date/Time', 'datetime')
		self.collection_sort_mode_combo.addItem('Boolean', 'bool')
		btn_sort_asc = QPushButton('Sort ↑', self)
		btn_sort_asc.setFixedSize(100, 20)
		btn_sort_asc.clicked.connect(lambda: self._collection_sort(False))
		btn_sort_desc = QPushButton('Sort ↓', self)
		btn_sort_desc.setFixedSize(100, 20)
		btn_sort_desc.clicked.connect(lambda: self._collection_sort(True))
		# btn_sort_reset = QPushButton('Reset Order', self)
		# btn_sort_reset.clicked.connect(self._collection_reset_order)
		btn_manage_columns = QPushButton('Hide Columns', self)
		btn_manage_columns.setFixedHeight(20)
		btn_manage_columns.clicked.connect(self._collection_manage_columns)

		t10 = QWidget()
		b10 = QHBoxLayout()
		b10.setContentsMargins(0, 0, 0, 0)
		b10.addWidget(QLabel('Sort column:', self))
		b10.addWidget(self.collection_sort_column_combo, 1)
		b10.addWidget(self.collection_sort_mode_combo)
		t10.setLayout(b10)

		t11 = QWidget()
		b11 = QHBoxLayout()
		b11.setContentsMargins(0, 0, 0, 0)
		b11.addWidget(btn_sort_asc)
		b11.addWidget(btn_sort_desc)
		b11.addWidget(btn_manage_columns)
		t11.setLayout(b11)

		sort_bar = QVBoxLayout()
		sort_bar.setContentsMargins(0, 0, 0, 0)
		# sort_bar.addWidget(QLabel('Sort column:', self))
		# sort_bar.addWidget(self.collection_sort_column_combo, 1)
		# sort_bar.addWidget(self.collection_sort_mode_combo)
		# sort_bar.addWidget(btn_sort_asc)
		# sort_bar.addWidget(btn_sort_desc)
		# sort_bar.addWidget(btn_manage_columns)
		sort_bar.addWidget(t10)
		sort_bar.addWidget(t11)
		# sort_bar.addWidget(btn_sort_reset)

		btn_add_row = QPushButton('Add Row', self)
		btn_add_row.setFixedHeight(20)
		btn_add_row.clicked.connect(self._collection_add_row)
		btn_delete_row = QPushButton('Delete Row', self)
		btn_delete_row.setFixedHeight(20)
		btn_delete_row.clicked.connect(self._collection_delete_row)
		btn_row_up = QPushButton('Row ↑', self)
		btn_row_up.setFixedHeight(20)
		btn_row_up.clicked.connect(lambda: self._collection_move_row(-1))
		btn_row_down = QPushButton('Row ↓', self)
		btn_row_down.setFixedHeight(20)
		btn_row_down.clicked.connect(lambda: self._collection_move_row(1))
		
		row_bar = QHBoxLayout()
		row_bar.setContentsMargins(0, 0, 0, 0)
		row_bar.addWidget(btn_add_row)
		row_bar.addWidget(btn_delete_row)
		row_bar.addWidget(btn_row_up)
		row_bar.addWidget(btn_row_down)
		#row_bar.addStretch()

		btn_add_col = QPushButton('Add Col', self)
		btn_add_col.setFixedHeight(20)
		btn_add_col.clicked.connect(self._collection_add_column)
		btn_delete_col = QPushButton('Delete Col', self)
		btn_delete_col.setFixedHeight(20)
		btn_delete_col.clicked.connect(self._collection_delete_column)
		btn_col_left = QPushButton('Col ←', self)
		btn_col_left.setFixedHeight(20)
		btn_col_left.clicked.connect(lambda: self._collection_move_column(-1))
		btn_col_right = QPushButton('Col →', self)
		btn_col_right.setFixedHeight(20)
		btn_col_right.clicked.connect(lambda: self._collection_move_column(1))
		btn_rename_col = QPushButton('Rename Column', self)
		btn_rename_col.clicked.connect(self._collection_rename_column)

		col_bar = QHBoxLayout()
		col_bar.setContentsMargins(0, 0, 0, 0)
		col_bar.addWidget(btn_add_col)
		col_bar.addWidget(btn_delete_col)
		col_bar.addWidget(btn_col_left)
		col_bar.addWidget(btn_col_right)
		# col_bar.addWidget(btn_rename_col)
		#col_bar.addStretch()

		self.collect_date_edit = QDateEdit(self)
		self.collect_date_edit.setCalendarPopup(True)
		self.collect_date_edit.setDisplayFormat('yyyy-MM-dd')
		self.collect_date_edit.setDate(QDate.currentDate())
		self.collect_date_edit.setFixedHeight(20)
		self.collect_date_edit.setToolTip('Choose Date')

		self.collect_time_edit = QTimeEdit(self)
		self.collect_time_edit.setDisplayFormat('HH:mm')
		self.collect_time_edit.setTime(QTime.currentTime())
		self.collect_time_edit.setFixedHeight(20)
		self.collect_time_edit.setToolTip('Choose Time')

		self.collect_length_input = QLineEdit(self)
		self.collect_length_input.setPlaceholderText('Length')
		self.collect_length_input.setFixedHeight(20)

		self.collect_length_unit = QComboBox(self)
		for label, factor in self._time_unit_items:
			self.collect_length_unit.addItem(label, factor)
		self.collect_length_unit.setCurrentIndex(self._time_unit_hours_index)
		self.collect_length_unit.setFixedWidth(100)
		self.collect_length_unit.setFixedHeight(20)

		self.collect_repeat_input = QLineEdit(self)
		self.collect_repeat_input.setPlaceholderText('Repeat')
		self.collect_repeat_input.setFixedHeight(20)

		self.collect_repeat_unit = QComboBox(self)
		for label, factor in self._repeat_unit_items:
			self.collect_repeat_unit.addItem(label, factor)
		self.collect_repeat_unit.setCurrentIndex(0)
		self.collect_repeat_unit.setFixedWidth(100)
		self.collect_repeat_unit.setFixedHeight(20)

		self.collect_repeat_until_check = QCheckBox('Repeat until', self)
		self.collect_repeat_until_check.setChecked(False)
		self.collect_repeat_until_date = QDateEdit(self)
		self.collect_repeat_until_date.setCalendarPopup(True)
		self.collect_repeat_until_date.setDisplayFormat('yyyy-MM-dd')
		self.collect_repeat_until_date.setDate(QDate.currentDate())
		self.collect_repeat_until_date.setFixedHeight(20)
		self.collect_repeat_until_date.setEnabled(False)
		self.collect_repeat_until_check.toggled.connect(lambda _: self._apply_repeat_until_enable(self.collect_repeat_until_check, self.collect_repeat_until_date))

		btn_collect_copy = QPushButton('Copy to Time list', self)
		btn_collect_copy.clicked.connect(self._collect_copy_to_time)
		btn_collect_copy.setFixedHeight(20)

		collect_time_row = QHBoxLayout()
		collect_time_row.setContentsMargins(0, 0, 0, 0)
		collect_time_row.addWidget(self.collect_date_edit)
		collect_time_row.addWidget(self.collect_time_edit)
		#collect_time_row.addWidget(btn_collect_copy)
		#collect_time_row.addStretch()

		collect_length_row = QHBoxLayout()
		collect_length_row.setContentsMargins(0, 0, 0, 0)
		collect_length_row.addWidget(self.collect_length_input)
		collect_length_row.addWidget(self.collect_length_unit)
		collect_length_row.addWidget(self.collect_repeat_input)
		collect_length_row.addWidget(self.collect_repeat_unit)
		#collect_length_row.addStretch()

		collect_until_row = QHBoxLayout()
		collect_until_row.setContentsMargins(0, 0, 0, 0)
		collect_until_row.addWidget(self.collect_repeat_until_check)
		collect_until_row.addWidget(self.collect_repeat_until_date)

		# self.frame22 = QFrame(self)
		# self.frame22.setFrameShape(QFrame.Shape.HLine)
		# self.frame22.setFrameShadow(QFrame.Shadow.Sunken)

		self.frame23 = QFrame(self)
		self.frame23.setFrameShape(QFrame.Shape.HLine)
		self.frame23.setFrameShadow(QFrame.Shadow.Sunken)

		mid_widget = QWidget()
		mid_bar = QVBoxLayout()
		#mid_bar.setSpacing(5)
		mid_bar.setContentsMargins(0, 0, 0, 0)
		#mid_bar.addStretch()
		#mid_bar.addLayout(sort_bar)
		#mid_bar.addWidget(self.frame22)
		mid_bar.addLayout(row_bar)
		mid_bar.addStretch()
		mid_bar.addLayout(col_bar)
		mid_bar.addStretch()
		mid_bar.addWidget(btn_rename_col)
		mid_bar.addStretch()
		mid_bar.addWidget(self.frame23)
		mid_bar.addStretch()
		mid_bar.addLayout(collect_time_row)
		mid_bar.addStretch()
		mid_bar.addLayout(collect_length_row)
		mid_bar.addLayout(collect_until_row)
		mid_bar.addStretch()
		mid_bar.addWidget(btn_collect_copy)
		#mid_bar.addStretch()
		mid_widget.setLayout(mid_bar)

		right_widget = QWidget()
		self.textiii1 = QTextEdit(self)
		self.textiii1.setReadOnly(False)
		self.textiii1.textChanged.connect(self.on_text_change)
		self._register_diary_refresh(self.textiii1)
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		if os.path.exists(diary_file):
			contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
			self.textiii1.setText(contm)
		b21 = QVBoxLayout()
		b21.setContentsMargins(0, 0, 0, 0)
		b21.addWidget(self.textiii1)
		b21.addLayout(sort_bar)
		right_widget.setLayout(b21)

		t5 = QWidget()
		b5 = QHBoxLayout()
		b5.setContentsMargins(0, 0, 0, 0)
		b5.addWidget(t2, 1)
		b5.addWidget(mid_widget, 2)
		b5.addWidget(right_widget, 2)
		#b5.addWidget(t3, 2)
		#b5.addWidget(t4, 2)
		t5.setLayout(b5)
		t5.setFixedHeight(int(self.height() / 2))

		main_layout = QVBoxLayout()
		#main_layout.setContentsMargins(20, 12, 20, 20)
		main_layout.addWidget(splitter, 1)
		main_layout.addLayout(search_bar)
		main_layout.addWidget(t5)

		# main_layout.addLayout(file_bar)
		# main_layout.addLayout(sort_bar)
		# main_layout.addLayout(row_bar)
		# main_layout.addLayout(col_bar)
		# main_layout.addLayout(collect_time_row)
		# main_layout.addLayout(collect_length_row)
		self.collect_tab.setLayout(main_layout)

		self._ensure_default_collection_file()
		self._refresh_collection_files()

	def _ensure_default_collection_file(self):
		if not os.path.isdir(self.fulldir_collection):
			os.makedirs(self.fulldir_collection, exist_ok=True)
		files = [f for f in os.listdir(self.fulldir_collection) if f.lower().endswith('.csv')]
		if files:
			return
		default_path = os.path.join(self.fulldir_collection, 'Collection1.csv')
		with open(default_path, 'w', encoding='utf-8', newline='') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerow(['Title', 'Notes'])
		self.collection_current_file = default_path

	def _refresh_collection_files(self, select_path=None):
		files = sorted([f for f in os.listdir(self.fulldir_collection) if f.lower().endswith('.csv')])
		current_path = select_path or self.collection_current_file
		self.collection_file_combo.blockSignals(True)
		self.collection_file_combo.clear()
		for fname in files:
			self.collection_file_combo.addItem(fname, os.path.join(self.fulldir_collection, fname))
		if not files:
			self.collection_current_file = None
			self.collection_table.setRowCount(0)
			self.collection_table.setColumnCount(0)
			self.collection_md_editor.setReadOnly(True)
			self.collection_md_editor.setPlainText('No CSV found. Create one to get started.')
			self.collection_file_combo.blockSignals(False)
			return
		if current_path and os.path.exists(current_path):
			index = self.collection_file_combo.findData(current_path)
			if index != -1:
				self.collection_file_combo.setCurrentIndex(index)
				self.collection_file_combo.blockSignals(False)
				self._collection_file_changed(index)
				return
		self.collection_file_combo.setCurrentIndex(0)
		self.collection_file_combo.blockSignals(False)
		self._collection_file_changed(0)

	def _collection_file_changed(self, index):
		if index < 0:
			return
		path = self.collection_file_combo.itemData(index)
		if not path:
			return
		self._load_collection_file(path)

	def _load_collection_file(self, path):
		if not os.path.exists(path):
			return
		self.collection_current_file = path
		self._collection_loading = True
		self.collection_table.clear()
		headers = []
		rows = []
		with open(path, 'r', encoding='utf-8', newline='') as csv_file:
			csv_reader = csv.reader(csv_file)
			for idx, row in enumerate(csv_reader):
				if idx == 0:
					headers = row
				else:
					rows.append(row)
		if not headers:
			headers = [f'Column {i + 1}' for i in range(len(rows[0]))] if rows else ['Column 1']
		self.collection_table.setColumnCount(len(headers))
		self.collection_table.setRowCount(len(rows))
		self.collection_table.setHorizontalHeaderLabels(headers)
		for r, row_values in enumerate(rows):
			for c in range(len(headers)):
				value = row_values[c] if c < len(row_values) else ''
				self.collection_table.setItem(r, c, QTableWidgetItem(value))
		self._collection_loading = False
		if rows:
			self.collection_table.setCurrentCell(0, 0)
		else:
			self._update_collection_markdown_preview()
		self._collection_refresh_sort_columns()
		self._collection_apply_search()

	def _save_collection_file(self):
		if self._collection_loading or not self.collection_current_file:
			return
		headers = self._collection_headers()
		with open(self.collection_current_file, 'w', encoding='utf-8', newline='') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerow(headers)
			for row in range(self.collection_table.rowCount()):
				row_values = []
				for col in range(self.collection_table.columnCount()):
					item = self.collection_table.item(row, col)
					row_values.append(item.text() if item else '')
				csv_writer.writerow(row_values)

	def _collection_headers(self):
		headers = []
		for col in range(self.collection_table.columnCount()):
			header_item = self.collection_table.horizontalHeaderItem(col)
			if header_item and header_item.text().strip():
				headers.append(header_item.text())
			else:
				headers.append(f'Column {col + 1}')
		return headers

	def _collection_new_file(self):
		name, ok = QInputDialog.getText(self, 'New CSV', 'File name (without extension):')
		if not ok or name.strip() == '':
			return
		name = name.strip()
		if not name.lower().endswith('.csv'):
			name += '.csv'
		target = os.path.join(self.fulldir_collection, name)
		if os.path.exists(target):
			QMessageBox.warning(self, 'File exists', 'A file with this name already exists.')
			return
		with open(target, 'w', encoding='utf-8', newline='') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerow(['Column 1'])
		self._refresh_collection_files(select_path=target)

	def _collection_add_row(self):
		if self.collection_table.columnCount() == 0:
			QMessageBox.information(self, 'No columns', 'Add a column before inserting rows.')
			return
		row = self.collection_table.rowCount()
		self.collection_table.insertRow(row)
		for col in range(self.collection_table.columnCount()):
			self.collection_table.setItem(row, col, QTableWidgetItem(''))
		self.collection_table.setCurrentCell(row, 0)
		self._save_collection_file()
		self._collection_apply_search()

	def _collection_delete_row(self):
		row = self.collection_table.currentRow()
		if row < 0:
			return
		self.collection_table.removeRow(row)
		self._save_collection_file()
		self._update_collection_markdown_preview()
		self._collection_apply_search()

	def _collection_move_row(self, offset):
		row = self.collection_table.currentRow()
		if row < 0:
			return
		target = row + offset
		if target < 0 or target >= self.collection_table.rowCount():
			return
		self.collection_table.blockSignals(True)
		for col in range(self.collection_table.columnCount()):
			item_row = self.collection_table.item(row, col)
			item_target = self.collection_table.item(target, col)
			text_row = item_row.text() if item_row else ''
			text_target = item_target.text() if item_target else ''
			if not item_row:
				item_row = QTableWidgetItem(text_row)
				self.collection_table.setItem(row, col, item_row)
			if not item_target:
				item_target = QTableWidgetItem(text_target)
				self.collection_table.setItem(target, col, item_target)
			item_row.setText(text_target)
			item_target.setText(text_row)
		self.collection_table.blockSignals(False)
		self.collection_table.setCurrentCell(target, 0)
		self._save_collection_file()
		self._collection_apply_search()

	def _collection_add_column(self):
		name, ok = QInputDialog.getText(self, 'Add Column', 'Column name:')
		if not ok:
			return
		name = name.strip() or f'Column {self.collection_table.columnCount() + 1}'
		col = self.collection_table.columnCount()
		self.collection_table.insertColumn(col)
		self.collection_table.setHorizontalHeaderItem(col, QTableWidgetItem(name))
		for row in range(self.collection_table.rowCount()):
			self.collection_table.setItem(row, col, QTableWidgetItem(''))
		self._save_collection_file()
		self._collection_refresh_sort_columns()
		self._collection_apply_search()

	def _collection_delete_column(self):
		col = self.collection_table.currentColumn()
		if col < 0:
			return
		self.collection_table.removeColumn(col)
		self._save_collection_file()
		self._update_collection_markdown_preview()
		self._collection_refresh_sort_columns()
		self._collection_apply_search()

	def _collection_move_column(self, offset):
		col = self.collection_table.currentColumn()
		if col < 0:
			return
		target = col + offset
		if target < 0 or target >= self.collection_table.columnCount():
			return
		headers = self._collection_headers()
		headers[col], headers[target] = headers[target], headers[col]
		self.collection_table.blockSignals(True)
		for row in range(self.collection_table.rowCount()):
			item_col = self.collection_table.item(row, col)
			item_target = self.collection_table.item(row, target)
			text_col = item_col.text() if item_col else ''
			text_target = item_target.text() if item_target else ''
			if not item_col:
				item_col = QTableWidgetItem(text_col)
				self.collection_table.setItem(row, col, item_col)
			if not item_target:
				item_target = QTableWidgetItem(text_target)
				self.collection_table.setItem(row, target, item_target)
			item_col.setText(text_target)
			item_target.setText(text_col)
		for idx, header in enumerate(headers):
			self.collection_table.setHorizontalHeaderItem(idx, QTableWidgetItem(header))
		self.collection_table.blockSignals(False)
		self.collection_table.setCurrentCell(self.collection_table.currentRow(), target)
		self._save_collection_file()
		self._update_collection_markdown_preview()
		self._collection_refresh_sort_columns()
		self._collection_apply_search()

	def _collection_rename_column(self):
		col = self.collection_table.currentColumn()
		if col < 0:
			return
		current_name = self._collection_headers()[col]
		name, ok = QInputDialog.getText(self, 'Rename Column', 'Column name:', text=current_name)
		if not ok or name.strip() == '':
			return
		self.collection_table.setHorizontalHeaderItem(col, QTableWidgetItem(name.strip()))
		self._save_collection_file()
		self._update_collection_markdown_preview()
		self._collection_refresh_sort_columns()
		self._collection_apply_search()

	def _collection_delete_file(self):
		if not self.collection_current_file:
			return
		if not os.path.exists(self.collection_current_file):
			return
		reply = QMessageBox.question(self, 'Delete CSV',
									 f'Delete "{os.path.basename(self.collection_current_file)}"?',
									 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
									 QMessageBox.StandardButton.No)
		if reply != QMessageBox.StandardButton.Yes:
			return
		try:
			os.remove(self.collection_current_file)
		except OSError as exc:
			QMessageBox.warning(self, 'Delete failed', f'Cannot delete file:\n{exc}')
			return
		self.collection_current_file = None
		self._ensure_default_collection_file()
		self._refresh_collection_files()

	def _collection_manage_columns(self):
		col_count = self.collection_table.columnCount()
		if col_count == 0:
			return
		dialog = QDialog(self)
		dialog.setWindowTitle('Column Visibility')
		layout = QVBoxLayout(dialog)
		list_widget = QListWidget(dialog)
		for idx, header in enumerate(self._collection_headers()):
			item = QListWidgetItem(header if header else f'Column {idx + 1}')
			item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
			item.setCheckState(Qt.CheckState.Unchecked if self.collection_table.isColumnHidden(idx)
							   else Qt.CheckState.Checked)
			item.setData(Qt.ItemDataRole.UserRole, idx)
			list_widget.addItem(item)
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=dialog)
		buttons.accepted.connect(dialog.accept)
		buttons.rejected.connect(dialog.reject)
		layout.addWidget(list_widget)
		layout.addWidget(buttons)
		if dialog.exec() == QDialog.DialogCode.Accepted:
			for i in range(list_widget.count()):
				item = list_widget.item(i)
				col = item.data(Qt.ItemDataRole.UserRole)
				self.collection_table.setColumnHidden(col, item.checkState() != Qt.CheckState.Checked)

	def _collection_clear_search(self):
		if hasattr(self, 'collection_search_input'):
			self.collection_search_input.clear()

	def _collection_apply_search(self):
		if not hasattr(self, 'collection_search_input'):
			return
		query = self.collection_search_input.text().strip().lower()
		row_count = self.collection_table.rowCount()
		if row_count == 0:
			return
		if query == '':
			for row in range(row_count):
				self.collection_table.setRowHidden(row, False)
			return
		matches = []
		for row in range(row_count):
			best_col = None
			for col in range(self.collection_table.columnCount()):
				if query in self._collection_item_text(row, col).lower():
					best_col = col
					break
			if best_col is not None:
				matches.append((best_col, row))
				self.collection_table.setRowHidden(row, False)
			else:
				self.collection_table.setRowHidden(row, True)
		matches.sort(key=lambda x: (x[0], x[1]))
		if matches:
			self.collection_table.setCurrentCell(matches[0][1], 0)
		else:
			self.collection_table.clearSelection()

	def _collection_refresh_sort_columns(self):
		if not hasattr(self, 'collection_sort_column_combo'):
			return
		self.collection_sort_column_combo.blockSignals(True)
		self.collection_sort_column_combo.clear()
		headers = self._collection_headers()
		for idx, header in enumerate(headers):
			label = header if header else f'Column {idx + 1}'
			self.collection_sort_column_combo.addItem(label, idx)
		self.collection_sort_column_combo.blockSignals(False)

	def _collection_sort(self, descending):
		if self.collection_table.columnCount() == 0:
			return
		column_index = self.collection_sort_column_combo.currentData()
		if column_index is None:
			return
		mode = self.collection_sort_mode_combo.currentData() or 'text'
		rows = self._collection_get_all_rows()
		headers = self._collection_headers()
		valid_rows = []
		invalid_rows = []
		for row in rows:
			value = row[column_index] if column_index < len(row) else ''
			ok, parsed = self._collection_parse_sort_value(value, mode)
			if ok:
				valid_rows.append((parsed, row))
			else:
				invalid_rows.append(row)
		valid_rows.sort(key=lambda item: item[0], reverse=descending)
		ordered = [row for _, row in valid_rows]
		ordered.extend(invalid_rows)
		self._collection_loading = True
		row_count = len(ordered)
		col_count = len(headers)
		self.collection_table.setRowCount(row_count)
		self.collection_table.setColumnCount(col_count)
		self.collection_table.setHorizontalHeaderLabels(headers)
		for r, row_values in enumerate(ordered):
			for c in range(col_count):
				value = row_values[c] if c < len(row_values) else ''
				item = self.collection_table.item(r, c)
				if item is None:
					item = QTableWidgetItem()
					self.collection_table.setItem(r, c, item)
				item.setText(value)
		self._collection_loading = False
		if row_count > 0:
			self.collection_table.setCurrentCell(0, 0)
		self._save_collection_file()
		self._collection_apply_search()
		self._update_collection_markdown_preview()

	def _collection_get_all_rows(self):
		rows = []
		col_count = self.collection_table.columnCount()
		for row in range(self.collection_table.rowCount()):
			row_values = []
			for col in range(col_count):
				row_values.append(self._collection_item_text(row, col))
			rows.append(row_values)
		return rows

	def _collection_parse_sort_value(self, value, mode):
		text = value.strip()
		if mode == 'number':
			try:
				return True, float(text)
			except ValueError:
				return False, None
		if mode == 'datetime':
			formats = ['%Y-%m-%d %H:%M', '%Y-%m-%d', '%m/%d/%Y %H:%M', '%m/%d/%Y']
			for fmt in formats:
				try:
					dt = datetime.datetime.strptime(text, fmt)
					return True, dt.timestamp()
				except ValueError:
					continue
			return False, None
		if mode == 'bool':
			lower = text.lower()
			if lower in ('true', 'yes', 'y', '1', 'on'):
				return True, 1
			if lower in ('false', 'no', 'n', '0', 'off'):
				return True, 0
			return False, None
		# text mode
		return True, text.lower()

	def _collection_item_text(self, row, col):
		item = self.collection_table.item(row, col)
		return item.text() if item else ''

	# def _collection_reset_order(self):
	# 	if not self.collection_current_file:
	# 		return
	# 	self._load_collection_file(self.collection_current_file)

	def _handle_collection_item_changed(self, item):
		if self._collection_loading or self._collection_table_block:
			return
		self._save_collection_file()
		if item.row() == self.collection_table.currentRow():
			self._update_collection_markdown_preview()

	def _build_collection_markdown(self, headers, values):
		parts = []
		for header, value in zip(headers, values):
			parts.append(f"# {header}\n{value}".rstrip())
		return '\n\n'.join(parts)

	def _parse_collection_markdown(self, text):
		sections = []
		current_header = None
		buffer = []
		for line in text.splitlines():
			if line.startswith('# '):
				if current_header is not None:
					sections.append((current_header, '\n'.join(buffer).strip()))
				current_header = line[2:].strip()
				buffer = []
			else:
				buffer.append(line)
		if current_header is not None:
			sections.append((current_header, '\n'.join(buffer).strip()))
		return sections

	def _update_collection_markdown_preview(self):
		row = self.collection_table.currentRow()
		if self.collection_table.rowCount() == 0 or row < 0:
			self._collection_preview_updating = True
			self.collection_md_editor.setReadOnly(True)
			self.collection_md_editor.setPlainText('Select a row to view its Markdown.')
			self._collection_preview_updating = False
			self._collection_last_markdown = self.collection_md_editor.toPlainText()
			return
		headers = self._collection_headers()
		values = []
		for col in range(self.collection_table.columnCount()):
			item = self.collection_table.item(row, col)
			values.append(item.text() if item else '')
		text = self._build_collection_markdown(headers, values)
		self._collection_preview_updating = True
		self.collection_md_editor.setReadOnly(False)
		self.collection_md_editor.setPlainText(text)
		self._collection_preview_updating = False
		self._collection_last_markdown = text

	def _handle_collection_markdown_change(self):
		if self._collection_preview_updating:
			return
		row = self.collection_table.currentRow()
		if row < 0:
			return
		headers = self._collection_headers()
		sections = self._parse_collection_markdown(self.collection_md_editor.toPlainText())
		if [header for header, _ in sections] != headers:
			self._collection_preview_updating = True
			self.collection_md_editor.blockSignals(True)
			self.collection_md_editor.setPlainText(self._collection_last_markdown)
			self.collection_md_editor.blockSignals(False)
			self._collection_preview_updating = False
			QMessageBox.warning(self, 'Invalid Markdown', 'Please keep the \"# Header\" lines unchanged.')
			return
		self._collection_table_block = True
		for col, (_, value) in enumerate(sections):
			if not self.collection_table.item(row, col):
				self.collection_table.setItem(row, col, QTableWidgetItem(value))
			else:
				self.collection_table.item(row, col).setText(value)
		self._collection_table_block = False
		self._collection_last_markdown = self.collection_md_editor.toPlainText()
		self._save_collection_file()

	def _open_collection_dir(self):
		if os.path.isdir(self.fulldir_collection):
			try:
				subprocess.call(['open', self.fulldir_collection])
			except Exception:
				pass

	def _collect_copy_to_time(self):
		row = self.collection_table.currentRow()
		if row < 0:
			QMessageBox.information(self, 'Select a row', 'Please select a row in the table first.')
			return
		name_item = self.collection_table.item(row, 0)
		if name_item is None or name_item.text().strip() == '':
			QMessageBox.warning(self, 'Missing name', 'The first column is empty. Please provide a task name.')
			return
		item_name = name_item.text().strip()
		selected_date = self.collect_date_edit.date()
		selected_time = self.collect_time_edit.time()
		if not (selected_date.isValid() and selected_time.isValid()):
			QMessageBox.warning(self, 'Missing time', 'Please choose a valid date and time.')
			return
		time_text = f"{selected_date.toString('yyyy-MM-dd')} {selected_time.toString('HH:mm')}"
		try:
			stamp_value = str(self.to_stamp(time_text))
		except Exception:
			QMessageBox.warning(self, 'Invalid time', 'Please choose a valid date and time.')
			return
		length_hours = self._convert_value_to_hours(self.collect_length_input.text(), self.collect_length_unit)
		if length_hours is None:
			QMessageBox.warning(self, 'Invalid length', 'Please enter a valid length.')
			return
		repeat_hours = '-'
		repeat_text = self.collect_repeat_input.text().strip()
		if repeat_text != '':
			repeat_hours = self._convert_value_to_hours(repeat_text, self.collect_repeat_unit)
			if repeat_hours is None:
				QMessageBox.warning(self, 'Invalid repeat', 'Please enter a valid repeat interval.')
				return
		repeat_until = self._get_repeat_until_stamp(self.collect_repeat_until_check, self.collect_repeat_until_date)
		new_row = [
			item_name,
			time_text,
			length_hours,
			repeat_hours,
			'UNDONE',
			'-',
			repeat_until,
			'TIME_SNS',
			stamp_value
		]
		with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
			csv_reader = csv.reader(csv_file)
			lines = list(csv_reader)
			lines.append(new_row)
		with open(self.fulldirall, 'w', encoding='utf8', newline='') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerows(lines)
		timeArray = time.localtime(float(stamp_value))
		otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
		escaped_name = self._escape_applescript_string(item_name)
		cmd = """tell application "Reminders"
	set eachLine to "%s"
	set mylist to list "Tomato"
	tell mylist
		make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
	end tell
end tell""" % (escaped_name, otherStyleTime)
		cmd2 = """tell application "Calendar"
  tell calendar "Tomato"
	make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
  end tell
end tell""" % (escaped_name, otherStyleTime, otherStyleTime, length_hours)
		self._run_osascript_batch([cmd, cmd2])
		self.collect_date_edit.setDate(QDate.currentDate())
		self.collect_time_edit.setTime(QTime.currentTime())
		self.collect_length_input.clear()
		self.collect_repeat_input.clear()
		self.collect_length_unit.setCurrentIndex(self._time_unit_hours_index)
		self.collect_repeat_unit.setCurrentIndex(0)
		self.collect_repeat_until_check.setChecked(False)
		self.collect_repeat_until_date.setDate(QDate.currentDate())

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
		if self._suppress_diary_write:
			return
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

	def _memo_done_single(self):
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

	def memo_done_memo(self):
		selected_rows = self._get_selected_rows(self.tableWidget_memo)
		if not selected_rows and self.tableWidget_memo.currentItem() != None:
			selected_rows = [self.tableWidget_memo.currentRow()]
		if not selected_rows:
			return
		comment_text = self.textw3.toPlainText()
		for index, row in enumerate(selected_rows):
			self.tableWidget_memo.setCurrentCell(row, 0)
			if index > 0 and comment_text != '':
				self.textw3.setPlainText(comment_text)
			self._memo_done_single()
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
			selected_date = self.memo_date_edit.date()
			selected_time = self.memo_time_edit.time()
			if not (selected_date.isValid() and selected_time.isValid()):
				return
			tim2_inp = f"{selected_date.toString('yyyy-MM-dd')} {selected_time.toString('HH:mm')}"
			length_hours = self._convert_value_to_hours(self.lm4.text(), self.memo_length_unit)
			if length_hours is None:
				return
			repeat_input = self.lm5.text()
			repeat_hours = '-'
			if repeat_input.strip() != '':
				repeat_converted = self._convert_value_to_hours(repeat_input, self.memo_repeat_unit)
				if repeat_converted is None:
					return
				repeat_hours = repeat_converted
			sta5_inp = 'UNDONE'
			tar6_inp = '-'
			pro7_inp = self._get_repeat_until_stamp(self.memo_repeat_until_check, self.memo_repeat_until_date)
			typ8_inp = 'TIME_SNS'
			sta9_inp = ''
			if ite1_inp != '' and tim2_inp != '' and self.tableWidget_memo.item(
					self.tableWidget_memo.currentIndex().row(), 0) != None:
				try:
					sta9_inp = str(self.to_stamp(tim2_inp))
				except Exception as e:
					pass
				if sta9_inp != '':
					new_time_sns.append(ite1_inp)
					new_time_sns.append(tim2_inp)
					new_time_sns.append(length_hours)
					new_time_sns.append(repeat_hours)
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
					escaped_ite1_inp = self._escape_applescript_string(ite1_inp)
					cmd = """tell application "Reminders"
						set eachLine to "%s"
						set mylist to list "Tomato"
						tell mylist
							make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
						end tell
					end tell""" % (escaped_ite1_inp, otherStyleTime)
					cmd2 = """tell application "Calendar"
					  tell calendar "Tomato"
						make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
					  end tell
					end tell""" % (escaped_ite1_inp, otherStyleTime, otherStyleTime, length_hours)
					self._run_osascript_batch([cmd, cmd2])
					self.memo_date_edit.setDate(QDate.currentDate())
					self.memo_time_edit.setTime(QTime.currentTime())
					self.lm4.clear()
					self.lm5.clear()
					self.memo_length_unit.setCurrentIndex(self._time_unit_hours_index)
					self.memo_repeat_unit.setCurrentIndex(0)
					self.memo_repeat_until_check.setChecked(False)
					self.memo_repeat_until_date.setDate(QDate.currentDate())
					self.lm1.setText('-')
					self.lm1.clear()

	def pin_a_tab(self):
		screen_geom = self._current_screen_geometry()
		SCREEN_WEIGHT = int(screen_geom.width())
		WINDOW_WEIGHT = int(self.width())
		DE_HEIGHT = int(screen_geom.height())
		target_x = 0
		target_y = self.pos().y()
		if self.i % 2 == 1: # show
			target_width = int(screen_geom.width() / 2)
			btna4.setChecked(True)
			self.btn_00.setStyleSheet('''
						border: 1px outset grey;
						background-color: #0085FF;
						border-radius: 4px;
						padding: 1px;
						color: #FFFFFF''')
			self.tab_bar.setVisible(True)
			self.setMinimumSize(0, 0)
			self.setMaximumSize(16777215, 16777215)
			self.resize(int(target_width), DE_HEIGHT)
			self.move(0 - int(target_width) + 10, 0)
			target_x = 3
			target_y = 0
		if self.i % 2 == 0: # hide
			btna4.setChecked(False)
			self.btn_00.setStyleSheet('''
						border: 1px outset grey;
						background-color: #FFFFFF;
						border-radius: 4px;
						padding: 1px;
						color: #000000''')
			self.tab_bar.setVisible(False)
			self.move(self.width() + 3, int((DE_HEIGHT - 70) / 2))
			self.setFixedSize(self.new_width, 120)
			target_x = 0
			target_y = int((DE_HEIGHT - 70) / 2)

		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		contm = codecs.open(diary_file, 'r', encoding='utf-8').read()

		# update desktop widget
		home_dir = str(Path.home())
		tarname1 = "Library"
		fulldir1 = os.path.join(home_dir, tarname1)
		tarname2 = "Application Support"
		fulldir2 = os.path.join(fulldir1, tarname2)
		tarname3 = "Übersicht"
		fulldir3 = os.path.join(fulldir2, tarname3)
		tarname4 = "widgets"
		fulldir4 = os.path.join(fulldir3, tarname4)
		tarname5 = ".totomato.txt"
		fulldir5 = os.path.join(fulldir4, tarname5)
		if os.path.isfile(fulldir5):
			totomato = codecs.open(fulldir5, 'r', encoding='utf-8').read()
			if totomato != '':
				tomato_list = totomato.split('\n')
				while '' in tomato_list:
					tomato_list.remove('')
				for i in range(len(tomato_list)):
					new_time_sns = []
					outerlist = []
					part1 = tomato_list[i].replace('\n', '')
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
				with open(fulldir5, 'w', encoding='utf-8') as f0:
					f0.write('')

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
		if tabnum == 3:
			self.textiii1.setText(contm)
			self.textiii1.ensureCursorVisible()  # 游标可用
			cursor = self.textiii1.textCursor()  # 设置游标
			pos = len(self.textiii1.toPlainText())  # 获取文本尾部的位置
			cursor.setPosition(pos)  # 游标位置设置为尾部
			self.textiii1.setTextCursor(cursor)  # 滚动到游标位置

		self.move_window(target_x, target_y)
		self._suppress_diary_write = False

	def pin_a_tab2(self):
		screen_geom = self._current_screen_geometry()
		SCREEN_WEIGHT = int(screen_geom.width())
		WINDOW_WEIGHT = int(self.width())
		DE_HEIGHT = int(screen_geom.height())
		target_x = 0
		target_y = self.pos().y()
		if self.i % 2 == 1:
			target_width = int(screen_geom.width() / 2)
			btna4.setChecked(True)
			self.btn_00.setStyleSheet('''
						border: 1px outset grey;
						background-color: #0085FF;
						border-radius: 4px;
						padding: 1px;
						color: #FFFFFF''')
			self.tab_bar.setVisible(True)
			self.setMinimumSize(0, 0)
			self.setMaximumSize(16777215, 16777215)
			self.resize(int(target_width), DE_HEIGHT)
			self.move(0 - int(target_width) + 10, 0)
			target_x = 3
			target_y = 0
		if self.i % 2 == 0:
			btna4.setChecked(False)
			self.btn_00.setStyleSheet('''
						border: 1px outset grey;
						background-color: #FFFFFF;
						border-radius: 4px;
						padding: 1px;
						color: #000000''')
			self.tab_bar.setVisible(False)
			self.resize(self.new_width, 120)
			self.move(self.width() + 3, int((DE_HEIGHT - 70) / 2))
			target_x = 0
			target_y = int((DE_HEIGHT - 70) / 2)

		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		contm = codecs.open(diary_file, 'r', encoding='utf-8').read()

		# update desktop widget
		home_dir = str(Path.home())
		tarname1 = "Library"
		fulldir1 = os.path.join(home_dir, tarname1)
		tarname2 = "Application Support"
		fulldir2 = os.path.join(fulldir1, tarname2)
		tarname3 = "Übersicht"
		fulldir3 = os.path.join(fulldir2, tarname3)
		tarname4 = "widgets"
		fulldir4 = os.path.join(fulldir3, tarname4)
		tarname5 = ".totomato.txt"
		fulldir5 = os.path.join(fulldir4, tarname5)
		if os.path.isfile(fulldir5):
			totomato = codecs.open(fulldir5, 'r', encoding='utf-8').read()
			if totomato != '':
				tomato_list = totomato.split('\n')
				while '' in tomato_list:
					tomato_list.remove('')
				for i in range(len(tomato_list)):
					new_time_sns = []
					outerlist = []
					part1 = tomato_list[i].replace('\n', '')
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
				with open(fulldir5, 'w', encoding='utf-8') as f0:
					f0.write('')

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
		if tabnum == 3:
			self.textiii1.setText(contm)
			self.textiii1.ensureCursorVisible()  # 游标可用
			cursor = self.textiii1.textCursor()  # 设置游标
			pos = len(self.textiii1.toPlainText())  # 获取文本尾部的位置
			cursor.setPosition(pos)  # 游标位置设置为尾部
			self.textiii1.setTextCursor(cursor)  # 滚动到游标位置

		self.move_window(target_x, target_y)

	def auto_record(self, checked):
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
		if checked:
			if NSWorkspace is None:
				print("can't import AppKit -- maybe you're running python from homebrew?")
				print("try running with /usr/bin/python instead")
				action4.setChecked(False)
				return
			if self.auto_record_thread and self.auto_record_thread.is_alive():
				return
			try:
				self.auto_record_thread = AutoRecordThread(self.fulldir_dia)
				self.auto_record_thread.start()
			except Exception:
				logging.exception("Failed to start auto-record thread.")
				self.auto_record_thread = None
				action4.setChecked(False)
		else:
			if self.auto_record_thread:
				self.auto_record_thread.stop()
				self.auto_record_thread = None

	def totalquit(self):
		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')

		ISOTIMEFORMAT = '%H:%M:%S '
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		pretext = '- ' + theTime
		with open(diary_file, 'a', encoding='utf-8') as f0:
			f0.write(pretext)
		if self.auto_record_thread:
			self.auto_record_thread.stop()
			self.auto_record_thread = None
		if hasattr(self, 'reminder_sync_timer') and self.reminder_sync_timer.isActive():
			self.reminder_sync_timer.stop()
		if self.reminder_sync_thread:
			self.reminder_sync_thread.stop()
			self.reminder_sync_thread = None
		action4.setChecked(False)

		app.quit()

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
tray_time_controller = TimeSensitiveTrayController(
	menu,
	time_sensitive_menu,
	tray_selected_section,
	tray_selected_separator,
	lambda: w3.fulldirall
)
action1.triggered.connect(w1.activate)
action2.triggered.connect(w2.activate)
action3.triggered.connect(w3.pin_a_tab)
action4.triggered.connect(w3.auto_record)
# tray.activated.connect(w3.activate)
btna4.triggered.connect(w3.pin_a_tab2)
quit.triggered.connect(w3.totalquit)
app.setStyleSheet(style_sheet_ori)
app.exec()
