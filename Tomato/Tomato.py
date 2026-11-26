#!/Users/ryanshen/Documents/A-workingfilewithp3.11/.venv/bin/python
# -*- coding: utf-8 -*-
# -*- encoding:UTF-8 -*-
# coding=utf-8
# coding:utf-8

import sys
# Started by another AI app as its MCP server (shared/APP_MCP_SPEC.md): no window, only the bridge that
# forwards to the tools of the family's apps on this Mac. Before anything else, so stdout stays clean.
if '--mcp-stdio' in sys.argv[1:]:
	import app_mcp_host
	sys.exit(app_mcp_host.main())

import codecs
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
							 QLabel, QHBoxLayout, QVBoxLayout, QLineEdit, QDateEdit, QTimeEdit,
							 QSystemTrayIcon, QMenu, QComboBox, QDialog, QMenuBar, QFrame, QFileDialog,
							 QPlainTextEdit, QTabWidget, QTextEdit, QGraphicsOpacityEffect,
							 QTableWidget, QTableWidgetItem, QAbstractItemView, QInputDialog,
							 QMessageBox, QSplitter, QDialogButtonBox, QListWidget, QListWidgetItem, QCheckBox,
							 QStackedWidget, QTextBrowser, QStyledItemDelegate, QGraphicsDropShadowEffect, QSizePolicy)
from PyQt6.QtCore import Qt, QRect, QSize, QPropertyAnimation, QDate, QTime, QTimer, QObject, QEvent, QPoint, QRectF, pyqtSignal, QThread, pyqtSlot, QEventLoop, QMimeData
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QColor, QCursor, QGuiApplication, QPainterPath, QPainter, QPalette, QSurfaceFormat, QPen, QPixmap, QFont, QTextCursor, QDrag
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
import atexit
import hashlib
import plistlib
import tempfile
import markdown2
from dataclasses import dataclass
from functools import partial
import Foundation
try:
	from AppKit import NSWorkspace, NSWorkspaceWillSleepNotification, NSWorkspaceDidWakeNotification, NSColor
except ImportError:
	NSWorkspace = None
	NSWorkspaceWillSleepNotification = None
	NSWorkspaceDidWakeNotification = None
	NSColor = None
try:
	from Foundation import NSDate, NSRunLoop, NSCalendar, NSObject, NSUserDefaults, NSSelectorFromString, NSDistributedNotificationCenter
	import objc
except Exception:
	NSDate = None
	NSRunLoop = None
	NSCalendar = None
	NSObject = None
	objc = None
import requests
import html2text
from bs4 import BeautifulSoup

# UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md
# The system's NEW design (Liquid Glass) for everything macOS draws in this program — the window traffic
# lights, menus, alerts (style book 5.7.2). macOS picks new vs old design from the SDK the main executable
# was built with; Python 3.11 and the packaged launcher both say 12.1, so this registration-domain default
# (this process only, nothing written to the user's settings) has to be set before the QApplication exists.
if sys.platform == 'darwin' and NSUserDefaults is not None:
	try:
		NSUserDefaults.standardUserDefaults().registerDefaults_(
			{'com.apple.SwiftUI.IgnoreSolariumLinkedOnCheck': True})
	except Exception:
		pass

# The Collection page's preview is a web page (2026-11-20, tomato_preview.py): the web engine has to be
# imported before the QApplication exists. The two flags are the workaround Broccoli / Watermelon use on
# macOS + Qt 6 (Chromium calls QAccessible::uniqueId with a null pointer while a page loads, and crashes).
_existing_flags = os.environ.get('QTWEBENGINE_CHROMIUM_FLAGS', '')
for _flag in ('--disable-blink-features=AccessibilityObjectModel', '--disable-renderer-accessibility'):
	if _flag not in _existing_flags:
		_existing_flags = (_existing_flags + ' ' + _flag).strip()
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = _existing_flags
from PyQt6.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

BasePath = '/Applications/Tomato.app/Contents/Resources/'
# BasePath = ''  # test

VERSION = "1.2.12"
NAME = 'Tomato'

os.environ["QT_QUICK_BACKEND"] = "metal"

fmt = QSurfaceFormat()
fmt.setSamples(8)  # 打开 MSAA 多重采样抗锯齿
QSurfaceFormat.setDefaultFormat(fmt)

# The app's identifier and its folders (2026-11-17, Ryan: "当然要改" — the same scheme as Broccoli's and
# Strawberry's): the bundle id is com.ryanthehito.tomato (was "Tomato"), and what Tomato writes lives under
#   ~/Library/Application Support/com.ryanthehito.tomato/   TomatoAppPath (the data) + tomato_errors.log
# Pictures, Record.csv and the translations are still read from the app (BasePath).
TOMATO_BUNDLE_ID = 'com.ryanthehito.tomato'
LEGACY_TOMATO_BUNDLE_ID = 'Tomato'
LEGACY_TOMATO_DATA_DIR = os.path.join(str(Path.home()), 'TomatoAppPath')
TOMATO_APPLICATION_SUPPORT_DIR = os.path.join(str(Path.home()), 'Library', 'Application Support', TOMATO_BUNDLE_ID)
TOMATO_DATA_DIR = os.path.join(TOMATO_APPLICATION_SUPPORT_DIR, 'TomatoAppPath')
os.makedirs(TOMATO_APPLICATION_SUPPORT_DIR, exist_ok=True)

# Configure logging with file handler for error tracking (beside the data folder, not inside the app:
# the app's own folder is replaced by every update and must not be written to)
ERROR_LOG_PATH = os.path.join(TOMATO_APPLICATION_SUPPORT_DIR, 'tomato_errors.log')
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
	handlers=[
		logging.FileHandler(ERROR_LOG_PATH, encoding='utf-8'),
		logging.StreamHandler()
	]
)

# ══ Liquid Glass UI (2026-11-15, style book UI_STYLEBOOK_macOS27.md section 5.12) ══════════════════════
# The glass kit (glass_kit.py, copied from Broccoli via Strawberry) and Tomato's own parts built on it
# (tomato_ui.py) live next to this file; both need the QApplication to exist.
# - main window body: the solid smooth panel Broccoli's main window has (white / #2D2D2D, 36 smooth);
# - every page: its table fills the page (content, never glass) and the edit part floats on its lower
#   part as ONE Liquid Glass panel that can be pushed in like a drawer (Ryan 2026-11-15: "表格整个在底下，
#   然后编辑的部分使用液态玻璃的浮窗浮在上面"; "底部一整块"; "浮窗可以收起");
# - tab bar: the glass PillNavBar (5.6), never QTabWidget;
# - buttons: the main action of a block = glass white capsule, the other clustered buttons = grey normal
#   button; drop-downs = compact grey drop-down with the system menu; inputs = normal single-line input;
# - date / time boxes = normal inputs, their calendar / clock = small glass pop-ups (5.4.1);
# - light and dark follow the system live (5.8); every visible text goes through _tr (1.6).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glass_kit
import tomato_ui
import markdown_preview
import tomato_preview
# formulas are typeset by Tomato's own MathJax (MathJax-2.7.9/, the trimmed copy; no network. 2026-11-25: up from 2.7.1, which let \unicode put script into the page)
TOMATO_MATHJAX_DIR = markdown_preview.set_mathjax_folders(
	os.path.join(BasePath, 'MathJax-2.7.9'), os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MathJax-2.7.9'))
import tomato_sync
import tomato_eventkit
import tomato_broccoli
import tomato_broccoli_ui
from glass_kit import (_tr, is_dark_theme, on_theme_changed, install_theme_observer, MacNormalButton,
					   WhiteButton, StrawberryDropdown, keep_scroll_bar_knob, install_window_liquid_glass,
					   add_search_glyph, NATIVE_TITLEBAR_HEIGHT)
from tomato_ui import (GlassTabWidget, FloatPanelStage, edit_panel, panel_line, style_table,
					   style_date_time_field, glass_calendar_popup, make_native_glass_window,
					   make_glass_dialog, install_glass_dialog_class, install_native_glass_window_class,
					   tomato_alert, tomato_confirm, tomato_choice, ask_text, GlassFormDialog, CheckRowDelegate,
					   apply_tomato_theme, MAIN_ROW_HEIGHT, GREY_ROW_HEIGHT, EndTimeLink, end_time_boxes,
					   QuickEditCard, ShortcutDialog)
import tomato_hotkey
import tomato_diary
import tomato_tools
import tomato_feed
import tomato_report
import tomato_report_ui
import share_picture

COLLECTION_ROW_MIME = 'application/x-tomato-collection-row'
import app_mcp_host

# The interface language (English / 简体中文 / 日本語): chosen in the menu-bar menu, kept with the data,
# applied at the next launch (the same scheme as Strawberry's and Broccoli's).
#
# Where the data lives (2026-11-17, Ryan: "把路径迁移到它应该在的那个路径上…学习 broccoli 的写法…主动地去迁移"):
#   ~/Library/Application Support/com.ryanthehito.tomato/TomatoAppPath     (was ~/TomatoAppPath)
# the same layout as Broccoli's and Strawberry's (folder named by the bundle id). The first start with this version moves the old folder
# there as it is (one rename: every file, the sync marker of a syncing tool included, keeps its place inside).
# (the constants are above, with the log)


def _data_folder_entries(folder: str) -> list:
	try:
		return [name for name in os.listdir(folder) if name != '.DS_Store']
	except OSError:
		return []


def _real_folder(path: str) -> bool:
	return os.path.isdir(path) and not os.path.islink(path)


def _other_tomato_running() -> bool:
	"""Another Tomato is open right now (an older one still writes to ~/TomatoAppPath)."""
	try:
		from AppKit import NSRunningApplication
		mine = os.getpid()
		return any(int(running.processIdentifier()) != mine
				   for bundle_id in (LEGACY_TOMATO_BUNDLE_ID, TOMATO_BUNDLE_ID)
				   for running in NSRunningApplication.runningApplicationsWithBundleIdentifier_(bundle_id))
	except Exception:
		return False


def _move_legacy_data_folder() -> str:
	"""'latest' (nothing at the old place) / 'moved' / 'busy' (another Tomato is open and still writes to the
	old folder: it is used this time, moved on a later start) / 'linked' (~/TomatoAppPath is a link the user
	made: used as it is) / 'set_aside' (a folder made at the old place again after the move — by an older
	Tomato: put into the data folder's Backups, never merged back) / 'error' (the old folder is used this
	time, tried again next start)."""
	global TOMATO_DATA_DIR
	old_data, new_data = LEGACY_TOMATO_DATA_DIR, TOMATO_DATA_DIR
	if os.path.islink(old_data):
		if not _data_folder_entries(new_data):
			TOMATO_DATA_DIR = old_data
			return 'linked'
		return 'latest'
	if not _real_folder(old_data):
		return 'latest'
	if _other_tomato_running():
		TOMATO_DATA_DIR = old_data
		return 'busy'
	try:
		if _data_folder_entries(new_data):
			aside = os.path.join(new_data, 'Backups', 'TomatoAppPath-' + time.strftime('%Y%m%d-%H%M%S'))
			os.makedirs(os.path.dirname(aside), exist_ok=True)
			os.rename(old_data, aside)
			logging.warning('A data folder was made at %s again; it was put into %s.', old_data, aside)
			return 'set_aside'
		os.makedirs(os.path.dirname(new_data), exist_ok=True)
		if os.path.isdir(new_data):
			shutil.rmtree(new_data)   # empty (at most Finder's .DS_Store)
		os.rename(old_data, new_data)
		return 'moved'
	except OSError:
		logging.exception('Moving the data folder %s to %s failed.', old_data, new_data)
		if _real_folder(old_data) and not _data_folder_entries(new_data):
			TOMATO_DATA_DIR = old_data
			return 'error'
		return 'latest'


def carry_over_macos_preferences(old_domain: str = LEGACY_TOMATO_BUNDLE_ID, new_domain: str = TOMATO_BUNDLE_ID, *,
								 only_in_app: bool = True, defaults=None) -> int:
	"""macOS keeps an app's own remembered state under its bundle id (~/Library/Preferences/<id>.plist: where
	its menu-bar icon sits, the open-file panel's last folder). The app with the new bundle id takes over what
	the old id had — what it set itself stays — and the old domain is emptied (macOS keeps its empty file: it
	writes it back a few seconds after a delete, so it is left to macOS). Only in the packaged app (run from
	source, the domain is Python's). How many settings were carried over. (Broccoli's / Strawberry's.)"""
	try:
		if only_in_app:
			from Foundation import NSBundle
			if str(NSBundle.mainBundle().bundleIdentifier() or '') != new_domain:
				return 0
		if defaults is None:
			defaults = NSUserDefaults.standardUserDefaults()
		old = defaults.persistentDomainForName_(old_domain)
		if not old:
			return 0
		current = defaults.persistentDomainForName_(new_domain) or {}
		merged = dict(old)
		merged.update(dict(current))
		defaults.setPersistentDomain_forName_(merged, new_domain)
		defaults.removePersistentDomainForName_(old_domain)
		return len(set(dict(old)) - set(dict(current)))
	except Exception:
		logging.exception('Carrying the macOS preferences over to %s failed.', new_domain)
		return 0


DATA_FOLDER_MOVE_REPORT = _move_legacy_data_folder()
MACOS_PREFERENCES_CARRIED_OVER = carry_over_macos_preferences()
os.makedirs(TOMATO_DATA_DIR, exist_ok=True)
UI_LANGUAGE = tomato_ui.read_ui_language_setting(TOMATO_DATA_DIR)
tomato_ui.load_translation(UI_LANGUAGE, [os.path.join(BasePath, 'i18n'),
										 os.path.join(os.path.dirname(os.path.abspath(__file__)), 'i18n')])
_app_font = QFont('Helvetica Neue')
_app_font.setPixelSize(13)
app.setFont(_app_font)


EDIT_PANEL_COLUMNS_HEIGHT = 236  # the three columns of an edit panel (filter + buttons | comments | diary)


def compact_dropdown(parent=None):
	"""A drop-down in the edit panel: the compact grey drop-down (22 high, the system menu pops up; 5.2)."""
	return StrawberryDropdown(parent, compact_light=True)


# Create the icon
# the menu-bar icon has a picture of its own (tomatomen.icns: drawn for that small size); the Dock icon is the
# app's icon, tomato.icns. A copy of the app without the menu-bar picture falls back to the app's icon.
_menu_bar_icon_path = BasePath + "tomatomen.icns"
icon = QIcon(_menu_bar_icon_path if os.path.isfile(_menu_bar_icon_path) else BasePath + "tomato.icns")

# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()

tray_selected_section = menu.addSection(_tr("⏱ Main list (countdown)"))
tray_selected_section.setVisible(False)
tray_selected_separator = menu.addSeparator()
tray_selected_separator.setVisible(False)

time_sensitive_menu = menu.addMenu(_tr("🕒 Countdown"))
menu.addSeparator()

action3 = QAction(_tr("📝 Plan + record!"))
menu.addAction(action3)

action4 = QAction(_tr("👀 Auto-record!"))
action4.setCheckable(True)
menu.addAction(action4)

action_auto_record_startup = QAction(_tr("🔄 Auto-record on startup"))
action_auto_record_startup.setCheckable(True)
menu.addAction(action_auto_record_startup)

# Submenu for repeat pre-generation count
repeat_pregenerate_menu = menu.addMenu(_tr("🔁 Repeat pre-generate count"))
repeat_pregenerate_actions = []
repeat_pregenerate_action_group = QActionGroup(menu)
repeat_pregenerate_action_group.setExclusive(True)
for i in range(1, 16):
	action = QAction(f"{i}", menu)
	action.setCheckable(True)
	action.setActionGroup(repeat_pregenerate_action_group)
	if i == 10:  # Default value
		action.setChecked(True)
	repeat_pregenerate_menu.addAction(action)
	repeat_pregenerate_actions.append(action)

# The main window above every other window, or an ordinary window (Broccoli's switch; kept in the settings file).
action_always_on_top = QAction(_tr("📌 Always on top"))
action_always_on_top.setCheckable(True)
action_always_on_top.setChecked(True)
menu.addAction(action_always_on_top)

# Dock icon shown or hidden, Broccoli's / Strawberry's way: the app starts without one (LSBackgroundOnly in
# Tomato.spec) and shows it at run time unless it was hidden here. Hidden, Tomato lives in the menu bar only:
# no Dock icon, no app menu, not in Command-Tab; its windows still open from this menu and from the edge strip.
def set_dock_icon_visible(visible, activate=False):
	"""(Broccoli's.) Regular app with a Dock icon, or an accessory app without one."""
	try:
		from AppKit import NSApplication
		ns_app = NSApplication.sharedApplication()
		ns_app.setActivationPolicy_(0 if visible else 1)
		if visible and activate:
			ns_app.activateIgnoringOtherApps_(True)
		return True
	except Exception:
		logging.exception('Failed to change the Dock icon visibility.')
		return False


action_dock_icon = QAction(_tr("👀 Show/Hide dock icon"))
action_dock_icon.setCheckable(True)
action_dock_icon.setChecked(True)
menu.addAction(action_dock_icon)

# Tomato's windows on every desktop (Space) and over other apps' full-screen windows, or only on the desktop
# they were opened on (Broccoli's switch; on unless switched off — Tomato always was on every desktop).
action_all_spaces = QAction(_tr("🪟 Show on all Spaces"))
action_all_spaces.setCheckable(True)
action_all_spaces.setChecked(True)
menu.addAction(action_all_spaces)

# The show / hide shortcut (2026-11-22, tomato_hotkey.py): set in a small dialog; ⌃⌥T unless changed.
action_shortcut = QAction(_tr("⌨️ Show/Hide shortcut…"))
menu.addAction(action_shortcut)

# The tasks Tomato sends to Broccoli at their time (tomato_broccoli.py): the manager window.
action_broccoli_tasks = QAction(_tr("🥦 Broccoli tasks…"))
menu.addAction(action_broccoli_tasks)

# What Broccoli's background vision sees goes into the diary, one short line per look (tomato_feed.py, 2026-11-23).
action_vision_diary = QAction(_tr("👁 Broccoli's view in diary"))
action_vision_diary.setCheckable(True)
action_vision_diary.setChecked(True)
menu.addAction(action_vision_diary)

# The day / week / month gathered into one page (tomato_report.py, 2026-11-23/24): the window with the month, the reports, the language.
action_daily_report = QAction(_tr("📊 Reports…"))
menu.addAction(action_daily_report)

# Tomato's tools in any other AI app that speaks MCP (Claude Desktop, Cursor, …; 2026-11-24): copies the setup lines.
action_ai_apps = QAction(_tr("🔌 Use in other AI apps…"))
menu.addAction(action_ai_apps)


def _copy_ai_apps_setup() -> None:
	QGuiApplication.clipboard().setText(app_mcp_host.bridge_setup_json())
	tomato_alert(None, _tr('Use in other AI apps'),
				 _tr('The setup is copied. Paste it into the MCP settings of your AI app (for example Claude Desktop or Cursor). '
					 'The AI app can then use the tools of Tomato and of your other apps on this Mac.'))

# The interface language: applied at the next launch.
lang_menu = QMenu(_tr("🌐 Language"))
menu.addMenu(lang_menu)
_lang_menu_actions = {}


def _on_ui_language_chosen(code: str) -> None:
	tomato_ui.write_ui_language_setting(TOMATO_DATA_DIR, code)
	for _code, _action in _lang_menu_actions.items():
		_action.setChecked(_code == code)
	if code != UI_LANGUAGE:
		tomato_alert(None, _tr('Language'), _tr('The language setting will apply after Tomato restarts.'))


for _lang_code, _lang_label in tomato_ui.UI_LANGUAGES:
	_lang_action = QAction(_lang_label)
	_lang_action.setCheckable(True)
	_lang_action.setChecked(_lang_code == UI_LANGUAGE)
	_lang_action.triggered.connect(lambda _checked, c=_lang_code: _on_ui_language_chosen(c))
	_lang_menu_actions[_lang_code] = _lang_action
	lang_menu.addAction(_lang_action)

menu.addSeparator()

action2 = QAction(_tr("🆕 Check for Updates"))
menu.addAction(action2)

action1 = QAction(_tr("ℹ️ About"))
menu.addAction(action1)

menu.addSeparator()

# Add a Quit option to the menu.
quit = QAction(_tr("Quit"))
menu.addAction(quit)

# Add the menu to the tray
tray.setContextMenu(menu)

# create a system menu
btna4 = QAction(_tr("&Pin!"))
btna4.setCheckable(True)
sysmenu = QMenuBar()
file_menu = sysmenu.addMenu(_tr("&Actions"))
file_menu.addAction(btna4)


def get_accent_color_hex():
	try:
		accent = NSColor.controlAccentColor()
		rgb = accent.colorUsingColorSpaceName_("NSCalibratedRGBColorSpace")
		if rgb:
			r = int(rgb.redComponent() * 255)
			g = int(rgb.greenComponent() * 255)
			b = int(rgb.blueComponent() * 255)
			return f"#{r:02X}{g:02X}{b:02X}"
	except Exception:
		pass
	return "#0A84FF"




class SleepWakeState:
	def __init__(self):
		self._sleeping = False
		self._lock = threading.Lock()

	def set_sleeping(self, val):
		with self._lock:
			self._sleeping = bool(val)

	def is_sleeping(self):
		with self._lock:
			return self._sleeping


if NSObject is not None and objc is not None:
	class SleepWakeObserver(NSObject):
		def initWithState_(self, state):
			self = objc.super(SleepWakeObserver, self).init()
			if self is None:
				return None
			self.state = state
			return self

		def handleSleep_(self, notification):
			self.state.set_sleeping(True)

		def handleWake_(self, notification):
			self.state.set_sleeping(False)
else:
	class SleepWakeObserver:
		pass


sleep_wake_state = SleepWakeState()
_sleep_wake_observer = None


def _register_sleep_wake_observer():
	global _sleep_wake_observer
	if not (NSWorkspace and NSWorkspaceWillSleepNotification and NSWorkspaceDidWakeNotification and NSObject and objc):
		return
	try:
		_sleep_wake_observer = SleepWakeObserver.alloc().initWithState_(sleep_wake_state)
		nc = NSWorkspace.sharedWorkspace().notificationCenter()
		nc.addObserver_selector_name_object_(_sleep_wake_observer, "handleSleep:", NSWorkspaceWillSleepNotification, None)
		nc.addObserver_selector_name_object_(_sleep_wake_observer, "handleWake:", NSWorkspaceDidWakeNotification, None)
	except Exception:
		logging.exception("Failed to register sleep/wake observer; continuing without it.")


def _system_pause_reason():
	"""None, 'away' (asleep, nobody logged in) or 'front' (Reminders / Calendar is the front app)."""
	if sleep_wake_state.is_sleeping():
		return 'away'
	if NSWorkspace is None:
		return None
	try:
		active_app = NSWorkspace.sharedWorkspace().activeApplication()
	except Exception:
		# If we cannot read active application, do not pause the threads
		return None
	if not active_app:
		return 'away'
	app_name = active_app.get('NSApplicationName')
	if not app_name or app_name == 'loginwindow':
		return 'away'
	if app_name == 'Reminders' or app_name == 'Calendar':
		return 'front'
	return None


_register_sleep_wake_observer()


class _MainThreadRunner(QObject):
	"""runner(fn): fn runs on the main thread, the calling thread gets what it returned (or its exception)."""
	_call = pyqtSignal(object)

	def __init__(self):
		super().__init__()
		self._call.connect(self._run)      # emitted from another thread → queued to this object's (the main) thread

	def _run(self, job):
		job()

	def __call__(self, fn):
		if threading.current_thread() is threading.main_thread():
			return fn()
		box, done = {}, threading.Event()

		def job():
			try:
				box['value'] = fn()
			except BaseException as exc:
				box['error'] = exc
			done.set()
		self._call.emit(job)
		done.wait()
		if 'error' in box:
			raise box['error']
		return box.get('value')

	def post(self, fn):
		"""fn runs on the main thread a moment later; the caller does not wait."""
		self._call.emit(fn)


class AutoRecordThread(threading.Thread):
	def __init__(self, diary_dir):
		super().__init__(daemon=True)
		self.diary_dir = Path(diary_dir)
		self.diary_dir.mkdir(parents=True, exist_ok=True)
		self._stop_event = threading.Event()
		self._counter = 5
		self._last_active_name = None
		self._paused_logged = False

	def run(self):
		while not self._stop_event.wait(1):
			if _system_pause_reason() == 'away':    # asleep / nobody logged in; every app is recorded, Reminders and Calendar too
				if not self._paused_logged:
					logging.info("AutoRecordThread paused (system inactive).")
					self._paused_logged = True
				continue
			if self._paused_logged:
				logging.info("AutoRecordThread resumed.")
				self._paused_logged = False
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
		tomato_diary.ensure(self.diary_dir)
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
			tomato_diary.append_raw(self.diary_dir, pretext)
		if app_name and app_name != self._last_active_name:
			self._last_active_name = app_name
			parta = '- %s \n\n- %s -(%s)' % (
				datetime.datetime.now().strftime('%H:%M:%S'),
				datetime.datetime.now().strftime('%H:%M:%S'),
				app_name
			)
			tomato_diary.append_raw(self.diary_dir, parta)


class SystemSyncSignals(QObject):
	ready = pyqtSignal()      # a reading is in the queue (sent from the reading thread)


class SystemSyncThread(threading.Thread):
	"""Reads the Calendar and the Reminders list back to back and hands the pair over, so the main thread
	decides about both at once (tomato_sync.reconcile). A pass runs: every `interval` seconds; when the Mac
	wakes; when the main thread asks (request()); and — with the system interface — SETTLE seconds after the
	system said that something changed (note_change(): a change made in Reminders, in Calendar or on another
	device is on the table a moment later, also while one of the two apps stays in front; several changes in
	a row are one pass).

	Both are read through the system interface (tomato_eventkit: hundredths of a second, the two apps are
	not woken). Without full access to Calendars the calendar is read by asking Calendar.app (17–28 s for
	130 events): then, as before, nothing is read while Reminders / Calendar are in front (looked at again
	every TICK seconds, read at once when they leave), change notices are not followed, and the passes keep
	the long interval."""
	TICK = 2.0
	MIN_GAP = 10.0            # between two passes on the old way, however often the front app changes
	FAST_INTERVAL = 30        # seconds between passes when a pass costs next to nothing
	FAST_MIN_GAP = 1.5
	SETTLE = 1.5              # after the last change notice: the hand has left the item
	CALENDAR_TIMEOUT = 150    # seconds; Calendar.app answers a column of 130 events in about 7

	def __init__(self, output_queue, interval_seconds=120, on_reading=None):
		super().__init__(daemon=True)
		self.output_queue = output_queue
		self.interval = max(30, int(interval_seconds))
		self.on_reading = on_reading
		self._stop_event = threading.Event()
		self._requested = threading.Event()
		self._wake = threading.Event()
		self._changed_at = 0.0
		self._store = tomato_eventkit.STORE
		self._paused_logged = False
		self._no_access_logged = False

	def stop(self, timeout=2.0):
		self._stop_event.set()
		self._wake.set()
		if self.is_alive():
			self.join(timeout)

	def request(self):
		self._requested.set()
		self._wake.set()

	def note_change(self):
		"""The system said that reminders / events changed (any thread)."""
		if not self._store.events_ok:
			return      # old way: a pass asks Calendar.app for half a minute; the timed passes do
		self._changed_at = time.time()
		self._wake.set()

	def _must_wait(self):
		reason = _system_pause_reason()
		if reason == 'front':
			return not self._store.events_ok    # the system interface does not disturb the two apps
		return reason is not None

	def run(self):
		next_due = 0.0
		last_pass = 0.0
		held = False
		while not self._stop_event.is_set():
			self._wake.clear()
			now = time.time()
			if self._store.events_ok is None and _system_pause_reason() != 'away':
				with contextlib.suppress(Exception):
					self._store.ensure_access()   # which way it goes decides whether the front app matters
			direct = bool(self._store.events_ok)
			gap = self.FAST_MIN_GAP if direct else self.MIN_GAP
			changed = self._changed_at
			settled = bool(changed) and now - changed >= self.SETTLE
			pause = self.TICK
			if self._must_wait():
				held = True
				if not self._paused_logged:
					logging.info("SystemSyncThread paused (system inactive).")
					self._paused_logged = True
			elif held or self._requested.is_set() or settled or now >= next_due:
				if now - last_pass >= gap:
					if self._paused_logged:
						logging.info("SystemSyncThread resumed.")
						self._paused_logged = False
					held = False
					self._requested.clear()
					if self._changed_at == changed:
						self._changed_at = 0.0
					try:
						self._pass()
					except Exception:
						logging.exception("Failed to read Reminders / Calendar.")
					last_pass = time.time()
					next_due = last_pass + (min(self.interval, self.FAST_INTERVAL) if self._store.events_ok else self.interval)
				else:
					pause = min(pause, gap - (now - last_pass) + 0.02)
			elif changed:
				pause = min(pause, self.SETTLE - (now - changed) + 0.02)
			if self._stop_event.is_set():
				break
			self._wake.wait(max(0.05, pause))

	def _pass(self):
		self._store.ensure_access()   # the first time the system asks; the answer is waited for here
		if not self._store.reminders_ok:
			if not self._no_access_logged:
				logging.warning("No access to Reminders; nothing is synchronised.")
				self._no_access_logged = True
			return
		started = time.time()
		event_window = None
		if self._store.events_ok:
			calendar, event_window = self._store.read_events(started)
		else:
			calendar = self._fetch_calendar()
		if self._must_wait():
			self._requested.set()   # Reminders / Calendar came to the front meanwhile: read again afterwards
			return
		# the same stretch as always: 30 days back, a year ahead
		reminders = self._store.read_reminders(started - 30 * 86400, started + 365 * 86400)
		if reminders is None:
			return
		self.output_queue.put({'timestamp': started, 'reminders': reminders, 'calendar': calendar, 'event_window': event_window})
		if self.on_reading:
			with contextlib.suppress(Exception):
				self.on_reading()       # the main thread looks at it now (it also looks every few seconds)

	def _fetch_calendar(self):
		"""The events of the "Tomato" calendar, or None when it could not be read as a whole (then nothing
		is decided about events in this pass)."""
		try:
			output = subprocess.run(
				['osascript', '-l', 'JavaScript', '-e', tomato_sync.CALENDAR_SNAPSHOT_JXA],
				capture_output=True, text=True, timeout=self.CALENDAR_TIMEOUT
			).stdout.strip()
		except (subprocess.SubprocessError, OSError):
			return None
		return tomato_sync.parse_calendar_snapshot(output)


class AppleScriptWorkerSignals(QObject):
	"""Signals for AppleScriptWorker to communicate with main thread"""
	started = PyQt6.QtCore.pyqtSignal()
	finished = PyQt6.QtCore.pyqtSignal()
	error = PyQt6.QtCore.pyqtSignal(str)


class AppleScriptWorker(threading.Thread):
	"""
	Background thread for executing AppleScript commands.
	Communicates with main thread via Qt signals.
	"""
	def __init__(self, script_chunks, signals):
		super().__init__(daemon=True)
		self.script_chunks = script_chunks
		self.signals = signals
		self._result = None
		self._error = None

	def run(self):
		if not self.script_chunks:
			self.signals.finished.emit()
			return
		# what Tomato asks for in these texts goes straight to the system interface where the access is there
		# (hundredths of a second); the rest runs as AppleScript, as before
		store = tomato_eventkit.STORE
		direct, remaining = [], []
		for chunk in self.script_chunks:
			ops = tomato_sync.parse_script(chunk) if store.reminders_ok else None
			if ops is not None and store.can(ops):
				direct.extend(ops)
			else:
				remaining.append(chunk)
		if direct:
			try:
				store.apply(direct)
			except Exception:
				logging.exception("System interface: the changes could not be sent.")
		# each command on its own: one that fails (nothing matched, a calendar that is gone) used to stop
		# every command after it in the same batch
		parts = []
		for chunk in remaining:
			text = (chunk or '').strip()
			if text.startswith('tell application') and text.endswith('end tell'):
				parts.append('try\n%s\nend try' % text)
			elif text:
				parts.append(text)
		script = '\n'.join(parts)
		try:
			if script:
				subprocess.call(['osascript', '-e', script])
		except Exception as e:
			self._error = str(e)
			self.signals.error.emit(str(e))
		finally:
			self.signals.finished.emit()


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
			no_item_action = QAction(_tr("No Countdown for now"), self.submenu)
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
		prefix = _tr("Still: ") if delta_seconds >= 0 else _tr("Overdue: ")
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
			parts.append(_tr('%n Days').replace('%n', str(days)))
		if hours:
			parts.append(' ' + _tr('%n Hours').replace('%n', str(hours)))
		if minutes:
			parts.append(' ' + _tr('%n Minutes').replace('%n', str(minutes)))
		if not parts:
			parts.append(' ' + _tr('%n Seconds').replace('%n', str(rem)))
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


class TableEditDelegate(QStyledItemDelegate):
	"""
	Custom delegate to detect when table cell editing starts and ends.
	This allows keyboard-based editing to trigger the same save logic as mouse clicks.
	"""
	editing_started = PyQt6.QtCore.pyqtSignal(int, int)  # row, column
	editing_finished = PyQt6.QtCore.pyqtSignal(int, int)  # row, column

	def __init__(self, parent=None):
		super().__init__(parent)
		self._current_edit_index = None

	def createEditor(self, parent, option, index):
		"""Called when editing begins - emit editing_started signal"""
		self._current_edit_index = (index.row(), index.column())
		self.editing_started.emit(index.row(), index.column())
		return super().createEditor(parent, option, index)

	def destroyEditor(self, editor, index):
		"""Called when editing ends - emit editing_finished signal"""
		if self._current_edit_index is not None:
			row, col = self._current_edit_index
			self._current_edit_index = None
			self.editing_finished.emit(row, col)
		super().destroyEditor(editor, index)


class ClockPickerPopup(QWidget):
	"""A hover-triggered clock picker popup for selecting time: a small Liquid Glass pop-up (style book
	5.4.1 — window glass, corner 9, the system window shadow); without glass the same shape, solid."""
	time_changed = PyQt6.QtCore.pyqtSignal(QTime)

	def __init__(self, parent=None):
		super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
		self.selected_hour = 12
		self.selected_minute = 0
		self.selecting_hour = True
		self._target_widget = None
		self._hide_timer = QTimer(self)
		self._hide_timer.setSingleShot(True)
		self._hide_timer.timeout.connect(self._check_and_hide)
		self.initUI()

	def initUI(self):
		self.setFixedSize(220, 286)

		layout = QVBoxLayout()
		layout.setContentsMargins(8, 8, 8, 8)
		layout.setSpacing(6)

		# Time display at top
		self.time_display = QLabel()
		self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.update_time_display()
		layout.addWidget(self.time_display)

		# Mode toggle buttons (grey normal buttons; the chosen one is filled with the system accent)
		mode_layout = QHBoxLayout()
		mode_layout.setSpacing(6)
		self.hour_btn = MacNormalButton(_tr('Hour'), self)
		self.minute_btn = MacNormalButton(_tr('Minute'), self)
		self.hour_btn.clicked.connect(lambda: self.set_mode(True))
		self.minute_btn.clicked.connect(lambda: self.set_mode(False))
		mode_layout.addWidget(self.hour_btn)
		mode_layout.addWidget(self.minute_btn)
		layout.addLayout(mode_layout)

		# Clock face widget
		self.clock_widget = ClockFaceWidget(self)
		self.clock_widget.setFixedSize(200, 200)
		self.clock_widget.time_selected.connect(self.on_clock_selection)
		clock_layout = QHBoxLayout()
		clock_layout.setContentsMargins(0, 0, 0, 0)
		clock_layout.addStretch()
		clock_layout.addWidget(self.clock_widget)
		clock_layout.addStretch()
		layout.addLayout(clock_layout)

		self.setLayout(layout)
		self._restyle()

	def _restyle(self):
		accent = tomato_ui.accent_color()
		self.time_display.setStyleSheet(
			'QLabel { font-size: 22px; font-weight: bold; padding: 5px; background-color: %s;'
			' color: white; border-radius: 6px; }' % accent.name())
		tomato_ui.set_button_highlight(self.hour_btn, self.selecting_hour)
		tomato_ui.set_button_highlight(self.minute_btn, not self.selecting_hour)

	def paintEvent(self, event):
		if getattr(self, '_liquid_glass_active', False):
			return  # the window's Liquid Glass is the card
		pal = tomato_ui.ui_palette()
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setPen(QPen(QColor('#4A4B4F') if pal['dark'] else QColor('#ECECEC'), 1))
		painter.setBrush(pal['panel'])
		radius = tomato_ui.POPUP_GLASS_RADIUS
		painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
		painter.end()

	def set_target_widget(self, widget):
		self._target_widget = widget

	def set_time(self, time):
		self.selected_hour = time.hour()
		self.selected_minute = time.minute()
		self.update_time_display()
		self.update_clock()

	def set_mode(self, selecting_hour):
		self.selecting_hour = selecting_hour
		self._restyle()
		self.update_clock()

	def update_time_display(self):
		self.time_display.setText(f'{self.selected_hour:02d}:{self.selected_minute:02d}')

	def update_clock(self):
		self.clock_widget.set_mode(self.selecting_hour, self.selected_hour, self.selected_minute)

	def on_clock_selection(self, value):
		if self.selecting_hour:
			self.selected_hour = value
			self.set_mode(False)
		else:
			self.selected_minute = value
		self.update_time_display()
		self.update_clock()
		self.time_changed.emit(QTime(self.selected_hour, self.selected_minute))

	def get_time(self):
		return QTime(self.selected_hour, self.selected_minute)

	def showAt(self, global_pos):
		self._restyle()  # light / dark, the accent colour
		self.move(global_pos)
		self.show()
		self.update_clock()

	def enterEvent(self, event):
		self._hide_timer.stop()
		super().enterEvent(event)

	def leaveEvent(self, event):
		self._hide_timer.start(600)
		super().leaveEvent(event)

	def _check_and_hide(self):
		if self._target_widget and self._target_widget.underMouse():
			return
		if self.underMouse():
			return
		self.hide()


class ClockFaceWidget(QWidget):
	"""Custom widget that draws a clock face for time selection"""
	time_selected = PyQt6.QtCore.pyqtSignal(int)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.selecting_hour = True
		self.current_hour = 12
		self.current_minute = 0
		self.hovered_value = None
		self.setMouseTracking(True)
		# Store positions for accurate hit detection
		self._outer_positions = []  # [(x, y, hour), ...]
		self._inner_positions = []  # [(x, y, hour), ...]
		self._minute_positions = []  # [(x, y, minute), ...]

	def set_mode(self, selecting_hour, hour, minute):
		self.selecting_hour = selecting_hour
		self.current_hour = hour
		self.current_minute = minute
		self.hovered_value = None
		self.update()

	def _colors(self):
		"""System accent for the chosen value and the hand (style book 5.8), light / dark for the rest."""
		dark = is_dark_theme(app)
		accent = tomato_ui.accent_color()
		hover = QColor(accent)
		hover.setAlpha(70)
		return {'accent': accent, 'hover': hover,
				'face': QColor(255, 255, 255, 26) if dark else QColor(0, 0, 0, 13),
				'rim': QColor(255, 255, 255, 40) if dark else QColor(0, 0, 0, 26),
				'text': QColor('#F2F2F7') if dark else QColor('#20242B'),
				'text2': QColor('#B8BAC0') if dark else QColor(80, 80, 80)}

	def paintEvent(self, event):
		import math
		c = self._colors()
		painter = PyQt6.QtGui.QPainter(self)
		painter.setRenderHint(PyQt6.QtGui.QPainter.RenderHint.Antialiasing)

		center_x = self.width() // 2
		center_y = self.height() // 2
		radius = min(center_x, center_y) - 3

		# Background circle
		painter.setBrush(c['face'])
		painter.setPen(c['rim'])
		painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

		# Clear position caches
		self._outer_positions = []
		self._inner_positions = []
		self._minute_positions = []

		if self.selecting_hour:
			outer_radius = radius - 18
			inner_radius = radius - 42

			# Outer ring: 12, 1-11 (12 at top)
			font = PyQt6.QtGui.QFont()
			font.setPointSize(11)
			font.setBold(False)
			painter.setFont(font)

			for i in range(12):
				hour = 12 if i == 0 else i
				angle = math.radians(i * 30 - 90)
				x = center_x + int(outer_radius * math.cos(angle))
				y = center_y + int(outer_radius * math.sin(angle))
				self._outer_positions.append((x, y, hour))

				is_selected = (self.current_hour == hour)
				is_hovered = (self.hovered_value == hour)

				if is_selected:
					painter.setBrush(c['accent'])
					painter.setPen(Qt.PenStyle.NoPen)
					painter.drawEllipse(x - 13, y - 13, 26, 26)
					painter.setPen(QColor(255, 255, 255))
				elif is_hovered:
					painter.setBrush(c['hover'])
					painter.setPen(Qt.PenStyle.NoPen)
					painter.drawEllipse(x - 13, y - 13, 26, 26)
					painter.setPen(c['text'])
				else:
					painter.setPen(c['text'])

				rect = PyQt6.QtCore.QRect(x - 13, y - 8, 26, 16)
				painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(hour))

			# Inner ring: 0, 13-23 (0 at top)
			font.setPointSize(9)
			painter.setFont(font)

			for i in range(12):
				hour = 0 if i == 0 else i + 12
				angle = math.radians(i * 30 - 90)
				x = center_x + int(inner_radius * math.cos(angle))
				y = center_y + int(inner_radius * math.sin(angle))
				self._inner_positions.append((x, y, hour))

				is_selected = (self.current_hour == hour)
				is_hovered = (self.hovered_value == hour)

				if is_selected:
					painter.setBrush(c['accent'])
					painter.setPen(Qt.PenStyle.NoPen)
					painter.drawEllipse(x - 11, y - 11, 22, 22)
					painter.setPen(QColor(255, 255, 255))
				elif is_hovered:
					painter.setBrush(c['hover'])
					painter.setPen(Qt.PenStyle.NoPen)
					painter.drawEllipse(x - 11, y - 11, 22, 22)
					painter.setPen(c['text2'])
				else:
					painter.setPen(c['text2'])

				rect = PyQt6.QtCore.QRect(x - 11, y - 7, 22, 14)
				painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(hour))

			# Draw hand
			if self.current_hour == 0 or self.current_hour > 12:
				hand_radius = inner_radius
				hour_for_angle = 0 if self.current_hour == 0 else self.current_hour - 12
			else:
				hand_radius = outer_radius
				hour_for_angle = self.current_hour
			angle = math.radians(hour_for_angle * 30 - 90)
			hand_x = center_x + int(hand_radius * math.cos(angle))
			hand_y = center_y + int(hand_radius * math.sin(angle))

		else:
			# Minutes
			num_radius = radius - 18
			font = PyQt6.QtGui.QFont()
			font.setPointSize(11)
			painter.setFont(font)

			for i in range(12):
				minute = i * 5
				angle = math.radians(i * 30 - 90)
				x = center_x + int(num_radius * math.cos(angle))
				y = center_y + int(num_radius * math.sin(angle))
				self._minute_positions.append((x, y, minute))

				is_selected = (self.current_minute == minute)
				is_hovered = (self.hovered_value == minute)

				if is_selected:
					painter.setBrush(c['accent'])
					painter.setPen(Qt.PenStyle.NoPen)
					painter.drawEllipse(x - 13, y - 13, 26, 26)
					painter.setPen(QColor(255, 255, 255))
				elif is_hovered:
					painter.setBrush(c['hover'])
					painter.setPen(Qt.PenStyle.NoPen)
					painter.drawEllipse(x - 13, y - 13, 26, 26)
					painter.setPen(c['text'])
				else:
					painter.setPen(c['text'])

				rect = PyQt6.QtCore.QRect(x - 13, y - 8, 26, 16)
				painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(minute).zfill(2))

			# Draw hand for minutes
			angle = math.radians(self.current_minute * 6 - 90)
			hand_radius = num_radius
			hand_x = center_x + int(hand_radius * math.cos(angle))
			hand_y = center_y + int(hand_radius * math.sin(angle))

		# Draw center dot
		painter.setBrush(c['accent'])
		painter.setPen(Qt.PenStyle.NoPen)
		painter.drawEllipse(center_x - 4, center_y - 4, 8, 8)

		# Draw hand line
		painter.setPen(PyQt6.QtGui.QPen(c['accent'], 2))
		painter.drawLine(center_x, center_y, hand_x, hand_y)

	def mouseMoveEvent(self, event):
		value = self._get_value_at_pos(event.position())
		if value != self.hovered_value:
			self.hovered_value = value
			self.update()

	def mousePressEvent(self, event):
		value = self._get_value_at_pos(event.position())
		if value is not None:
			self.time_selected.emit(value)

	def leaveEvent(self, event):
		self.hovered_value = None
		self.update()
		super().leaveEvent(event)

	def _get_value_at_pos(self, pos):
		"""Find which number was clicked/hovered using stored positions"""
		import math
		px, py = pos.x(), pos.y()

		if self.selecting_hour:
			# Check inner ring first (smaller hit area, higher priority)
			for x, y, hour in self._inner_positions:
				dist = math.sqrt((px - x) ** 2 + (py - y) ** 2)
				if dist <= 14:
					return hour

			# Check outer ring
			for x, y, hour in self._outer_positions:
				dist = math.sqrt((px - x) ** 2 + (py - y) ** 2)
				if dist <= 16:
					return hour
		else:
			# Check minute positions
			for x, y, minute in self._minute_positions:
				dist = math.sqrt((px - x) ** 2 + (py - y) ** 2)
				if dist <= 16:
					return minute

		return None


class AutoCloseNotification(QDialog):
	"""Auto-closing notification for safety check warnings: a glass dialog (style book 5.7: the window is
	the card, corner 16, grey normal button), non-modal so it never blocks the main thread."""
	def __init__(self, title, message, auto_close_seconds=5, action=None):
		super().__init__()
		self.auto_close_seconds = auto_close_seconds
		self.remaining_seconds = auto_close_seconds
		self._action = action      # (label, callback): one more grey button left of Close (e.g. Download Broccoli…)
		self.initUI(title, message)

	def _countdown_text(self):
		return _tr('This window will auto-close in %n seconds').replace('%n', str(self.remaining_seconds))

	def initUI(self, title, message):
		self.setWindowTitle(title)
		make_glass_dialog(self)
		self.setModal(False)  # Non-modal so it doesn't block the main thread

		layout = QVBoxLayout()
		layout.setContentsMargins(20, 18, 20, 16)
		layout.setSpacing(10)

		heading = QLabel(title)
		heading_font = QFont(heading.font())
		heading_font.setPixelSize(15)
		heading_font.setBold(True)
		heading.setFont(heading_font)
		layout.addWidget(heading)

		# Message label
		message_label = QLabel(message)
		message_label.setWordWrap(True)
		layout.addWidget(message_label)

		# Countdown label
		self.countdown_label = QLabel(self._countdown_text())
		self.countdown_label.setStyleSheet("color: #8E8E93; font-size: 11px;")
		layout.addWidget(self.countdown_label)

		# Close button
		close_button = MacNormalButton(_tr('Close'), self)
		close_button.setMinimumWidth(96)
		close_button.clicked.connect(self.accept)
		button_row = QHBoxLayout()
		button_row.setContentsMargins(0, 0, 0, 0)
		button_row.setSpacing(8)
		button_row.addStretch()
		if self._action is not None:
			action_button = MacNormalButton(self._action[0], self)
			action_button.setMinimumWidth(96)
			action_button.clicked.connect(lambda: (self._action[1](), self.accept()))
			button_row.addWidget(action_button)
		button_row.addWidget(close_button)
		layout.addLayout(button_row)

		self.setLayout(layout)
		self.resize(420, 190)

		# Setup auto-close timer
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_countdown)
		self.timer.start(1000)  # Update every second

	def update_countdown(self):
		self.remaining_seconds -= 1
		if self.remaining_seconds <= 0:
			self.timer.stop()
			self.accept()
		else:
			self.countdown_label.setText(self._countdown_text())


install_glass_dialog_class(AutoCloseNotification)


# WhiteButton (glass white capsule), MacNormalButton (grey normal button): the kit's (glass_kit.py).
# The old hand-drawn traffic light (MacWindowButton) and CustomMessageBox are gone: windows carry the
# system's own traffic lights, notices and questions are system alerts (style book 5.7 / 5.7.2).


class WindowAbout(QWidget):  # 增加说明页面(About)
	def __init__(self):
		super().__init__()
		self.init_ui()

	def init_ui(self):
		self.setUpMainWindow()
		make_native_glass_window(self)
		self.setFixedSize(400, 600)  # Broccoli's About
		self.center()
		self.setWindowTitle(_tr('About'))
		self.setFocus()

	def setUpMainWindow(self):
		widg1 = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'tomato.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
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
		lbl0 = QLabel(NAME, self)
		font = QFont()
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
		lbl1 = QLabel(_tr('Version %n').replace('%n', VERSION), self)
		blay3 = QHBoxLayout()
		blay3.setContentsMargins(0, 0, 0, 0)
		blay3.addStretch()
		blay3.addWidget(lbl1)
		blay3.addStretch()
		widg3.setLayout(blay3)

		widg4 = QWidget()
		lbl2 = QLabel(_tr('Thanks for your love🤟.'), self)
		blay4 = QHBoxLayout()
		blay4.setContentsMargins(0, 0, 0, 0)
		blay4.addStretch()
		blay4.addWidget(lbl2)
		blay4.addStretch()
		widg4.setLayout(blay4)

		widg5 = QWidget()
		lbl3 = QLabel(_tr('For more of my works, please visit the homepage🥰.'), self)
		blay5 = QHBoxLayout()
		blay5.setContentsMargins(0, 0, 0, 0)
		blay5.addStretch()
		blay5.addWidget(lbl3)
		blay5.addStretch()
		widg5.setLayout(blay5)

		widg6 = QWidget()
		lbl4 = QLabel(_tr('Special thanks to ut.code(); of the University of Tokyo❤️.'), self)
		blay6 = QHBoxLayout()
		blay6.setContentsMargins(0, 0, 0, 0)
		blay6.addStretch()
		blay6.addWidget(lbl4)
		blay6.addStretch()
		widg6.setLayout(blay6)

		widg7 = QWidget()
		lbl5 = QLabel(_tr('This app is under the protection of GPL-3.0 license.'), self)
		blay7 = QHBoxLayout()
		blay7.setContentsMargins(0, 0, 0, 0)
		blay7.addStretch()
		blay7.addWidget(lbl5)
		blay7.addStretch()
		widg7.setLayout(blay7)

		widg8 = QWidget()
		widg8.setFixedHeight(50)
		bt1 = WhiteButton(_tr('The Author'))
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.intro)
		bt2 = WhiteButton(_tr('Github Page'))
		bt2.setMinimumWidth(100)
		bt2.clicked.connect(self.homepage)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg8.setLayout(blay8)

		bt7 = WhiteButton(_tr('Buy me a cup of coffee☕'))
		bt7.setMinimumWidth(215)
		bt7.clicked.connect(self.coffee)
		widg8_5 = QWidget()
		widg8_5.setFixedHeight(50)
		blay8_5 = QHBoxLayout()
		blay8_5.setContentsMargins(0, 0, 0, 0)
		blay8_5.addStretch()
		blay8_5.addWidget(bt7)
		blay8_5.addStretch()
		widg8_5.setLayout(blay8_5)

		widg9 = QWidget()
		widg9.setFixedHeight(70)
		bt3 = WhiteButton('🍪\n¥5')
		bt3.setMaximumHeight(50)
		bt3.setMinimumHeight(50)
		bt3.setMinimumWidth(50)
		bt3.clicked.connect(self.donate)
		bt4 = WhiteButton('🥪\n¥10')
		bt4.setMaximumHeight(50)
		bt4.setMinimumHeight(50)
		bt4.setMinimumWidth(50)
		bt4.clicked.connect(self.donate2)
		bt5 = WhiteButton('🍜\n¥20')
		bt5.setMaximumHeight(50)
		bt5.setMinimumHeight(50)
		bt5.setMinimumWidth(50)
		bt5.clicked.connect(self.donate3)
		bt6 = WhiteButton('🍕\n¥50')
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
		lbl6 = QLabel('© 2023 Yixiang SHEN. All rights reserved.', self)
		blay10 = QHBoxLayout()
		blay10.setContentsMargins(0, 0, 0, 0)
		blay10.addStretch()
		blay10.addWidget(lbl6)
		blay10.addStretch()
		widg10.setLayout(blay10)

		main_h_box = QVBoxLayout()
		main_h_box.setContentsMargins(20, 40, 20, 20)  # 重要，用来保证关闭按钮的位置。
		main_h_box.addSpacing(10)
		main_h_box.addWidget(widg1)
		main_h_box.addWidget(widg2)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg3)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg4)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg5)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg6)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg7)
		main_h_box.addStretch()
		main_h_box.addWidget(widg8)
		main_h_box.addWidget(widg8_5)
		main_h_box.addWidget(widg9)
		main_h_box.addWidget(widg10)
		main_h_box.addStretch()
		main_h_box.addSpacing(10)
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
		make_native_glass_window(self, kind=Qt.WindowType.Dialog)
		self.setWindowTitle(_tr("Thank you for your support!"))
		self.setFixedSize(400, 420)
		self.center()
		self.setFocus()

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'wechat5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = QPixmap(BasePath + 'alipay5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel(_tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(_tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(_tr('Thank you!'))
		bt1.setMinimumWidth(120)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(_tr('Neither one above? Buy me a coffee~'))
		#bt2.setMaximumHeight(20)
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
		make_native_glass_window(self, kind=Qt.WindowType.Dialog)
		self.setWindowTitle(_tr("Thank you for your support!"))
		self.setFixedSize(400, 420)
		self.center()
		self.setFocus()

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'wechat10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = QPixmap(BasePath + 'alipay10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel(_tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(_tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(_tr('Thank you!'))
		bt1.setMinimumWidth(120)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(_tr('Neither one above? Buy me a coffee~'))
		#bt2.setMaximumHeight(20)
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
		make_native_glass_window(self, kind=Qt.WindowType.Dialog)
		self.setWindowTitle(_tr("Thank you for your support!"))
		self.setFixedSize(400, 420)
		self.center()
		self.setFocus()

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'wechat20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = QPixmap(BasePath + 'alipay20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel(_tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(_tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(_tr('Thank you!'))
		bt1.setMinimumWidth(120)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(_tr('Neither one above? Buy me a coffee~'))
		#bt2.setMaximumHeight(20)
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
		make_native_glass_window(self, kind=Qt.WindowType.Dialog)
		self.setWindowTitle(_tr("Thank you for your support!"))
		self.setFixedSize(400, 420)
		self.center()
		self.setFocus()

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'wechat50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = QPixmap(BasePath + 'alipay50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel(_tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(_tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(_tr('Thank you!'))
		bt1.setMinimumWidth(120)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(_tr('Neither one above? Buy me a coffee~'))
		#bt2.setMaximumHeight(20)
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


# ---- One-click update: check → download → verify → install → relaunch (Broccoli's, ported 2026-11-25;
# Ryan: "所有的软件……都是要学习 Broccoli 的这个更新写法的，下载更新的写法") ----
# Every release ships one notarized DMG on GitHub (the API gives the asset's `digest` = its sha256).
#  1. WindowUpdate downloads it into ~/Library/Caches/com.ryanthehito.tomato/Updates with a progress bar
#     (a .part file, resumed with an HTTP Range request), then checks size + sha256.
#  2. It mounts the DMG read-only ("Y" answers its licence agreement), copies Tomato.app into a hidden
#     folder NEXT TO the running bundle (same volume → the swap is a rename) and requires the copy to
#     satisfy TOMATO_UPDATE_CODE_REQUIREMENT (Developer ID + this team + this bundle id); a changed or
#     foreign-signed installer, or an older version, is never installed.
#  3. Tomato quits the normal way (totalquit: the diary line, the threads stopped). AFTER app.exec() returns,
#     this process swaps the bundles (macOS App Management lets an app modify apps signed by its own team).
#     Tomato's data and settings live outside the app (Application Support/com.ryanthehito.tomato), so the
#     swap keeps them; nothing is carried over. Tomato does not replace NSApp's delegate (Qt's own stays),
#     so app.exec() does return on Quit / ⌘Q / the Dock's Quit — unlike Raspberry, no applicationWillTerminate_ hook.
#  4. A detached waiter reopens the app once this PID is gone; the new build deletes the previous bundle on
#     its first start and says how the install went (the update window's startup note).
# The old daily re-check (UpdateCheckWorker) and its "open the release page?" question are gone: one check
# 3 s after the start; when a newer release is out (or the last install left a note) the window comes out.
TOMATO_CACHE_DIR = os.path.join(str(Path.home()), 'Library', 'Caches', TOMATO_BUNDLE_ID)
TOMATO_UPDATE_LATEST_API = 'https://api.github.com/repos/Ryan-the-hito/Tomato/releases/latest'
TOMATO_UPDATE_RELEASES_URL = 'https://github.com/Ryan-the-hito/Tomato/releases'
TOMATO_UPDATE_BUNDLE_ID = TOMATO_BUNDLE_ID
TOMATO_UPDATE_TEAM_ID = '49C7YMHM5Q'
TOMATO_UPDATE_CODE_REQUIREMENT = (
	'anchor apple generic and identifier "%s"'
	' and certificate 1[field.1.2.840.113635.100.6.2.6] exists'      # Developer ID CA
	' and certificate leaf[field.1.2.840.113635.100.6.1.13] exists'  # Developer ID Application
	' and certificate leaf[subject.OU] = "%s"' % (TOMATO_UPDATE_BUNDLE_ID, TOMATO_UPDATE_TEAM_ID))
TOMATO_UPDATE_CACHE_DIR = os.path.join(TOMATO_CACHE_DIR, 'Updates')
TOMATO_UPDATE_RESULT_PATH = os.path.join(TOMATO_UPDATE_CACHE_DIR, 'last_install.json')
TOMATO_UPDATE_STAGING_DIRNAME = '.Tomato-update'
_TOMATO_UPDATE_FS_LOCK = threading.Lock()   # staging vs. the startup cleanup of the same folder
_TOMATO_PENDING_UPDATE_INSTALL = None        # set right before quitting for an install


class TomatoUpdateError(Exception):
	"""A user-presentable reason the update stopped (already translated)."""


class TomatoUpdateCanceled(TomatoUpdateError):
	pass


def tomato_parse_version(text):
	match = re.search(r'(\d+)\.(\d+)\.(\d+)', str(text or ''))
	return tuple(int(part) for part in match.groups()) if match else None


def tomato_is_newer_version(candidate, current) -> bool:
	"""'v1.2.13' / 'Tomato_v1.2.13.dmg' / '1.2.13' against VERSION: strictly newer only (numbers, not text)."""
	newer, older = tomato_parse_version(candidate), tomato_parse_version(current)
	return bool(newer and older and newer > older)


def tomato_running_app_bundle():
	"""The .app bundle this process runs from (packaged builds only)."""
	if not getattr(sys, 'frozen', False):
		return None
	try:
		bundle = Path(sys.executable).resolve().parents[2]
	except Exception:
		return None
	if bundle.suffix != '.app' or not (bundle / 'Contents' / 'Info.plist').is_file():
		return None
	return bundle


def tomato_update_install_blocker(bundle) -> str:
	"""Why this copy cannot replace itself ('' when it can)."""
	if sys.platform != 'darwin':
		return _tr('automatic install needs macOS')
	if bundle is None:
		return _tr('Tomato is not running from an installed app')
	if '/AppTranslocation/' in str(bundle):
		return _tr('macOS is running Tomato from a temporary copy; move it into Applications first')
	# renaming the bundle into another folder needs write access to it and its parent
	if not os.access(str(bundle.parent), os.W_OK) or not os.access(str(bundle), os.W_OK):
		return _tr('no permission to replace %1').replace('%1', str(bundle))
	return ''


def tomato_fetch_latest_release():
	"""Latest release from the GitHub API: tag, version and its DMG asset
	(dmg_* fields stay empty when the release carries no DMG)."""
	response = requests.get(TOMATO_UPDATE_LATEST_API, timeout=(4, 6),
							headers={'Accept': 'application/vnd.github+json'})
	if not response.ok:
		return None
	data = response.json() or {}
	tag = str(data.get('tag_name', '') or '').strip()
	if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
		return None
	info = {'tag': tag, 'version': tag[1:], 'dmg_name': '', 'dmg_url': '', 'dmg_size': 0, 'dmg_sha256': ''}
	dmgs = [asset for asset in (data.get('assets') or []) if isinstance(asset, dict)
			and str(asset.get('name', '')).lower().endswith('.dmg')
			and str(asset.get('state', 'uploaded')) == 'uploaded'
			and str(asset.get('browser_download_url', '')).startswith('https://')]
	dmgs.sort(key=lambda asset: not str(asset.get('name', '')).lower().startswith('tomato'))
	if dmgs:
		asset = dmgs[0]
		digest = str(asset.get('digest') or '')
		info.update(dmg_name=str(asset.get('name')),
					dmg_url=str(asset.get('browser_download_url')),
					dmg_size=int(asset.get('size') or 0),
					dmg_sha256=digest[7:].lower() if digest.lower().startswith('sha256:') else '')
	return info


def _tomato_sha256_file(path) -> str:
	digest = hashlib.sha256()
	with open(path, 'rb') as handle:
		for block in iter(lambda: handle.read(4 << 20), b''):
			digest.update(block)
	return digest.hexdigest()


def _tomato_update_file_matches(path, size, sha256) -> bool:
	try:
		if size and os.path.getsize(path) != size:
			return False
		return not sha256 or _tomato_sha256_file(path) == sha256
	except OSError:
		return False


def tomato_download_update_dmg(info, progress, cancel_event, status=None) -> str:
	"""Download the release DMG into the cache (resuming an earlier .part), verify size + sha256 and
	return its path. progress(done, total) and status(text) run on the calling worker thread;
	cancel_event aborts between chunks and keeps the .part for the next attempt."""
	status = status or (lambda _text: None)
	url = str(info.get('dmg_url') or '')
	if not url:
		raise TomatoUpdateError(_tr('This release has no installer package.'))
	size = int(info.get('dmg_size') or 0)
	sha256 = str(info.get('dmg_sha256') or '').lower()
	os.makedirs(TOMATO_UPDATE_CACHE_DIR, exist_ok=True)
	name = re.sub(r'[^A-Za-z0-9._-]+', '_', str(info.get('dmg_name') or '')).strip('.') or 'Tomato-update.dmg'
	final_path = os.path.join(TOMATO_UPDATE_CACHE_DIR, name)
	part_path = final_path + '.part'
	if os.path.isfile(final_path):
		status(_tr('Verifying the download…'))
		if _tomato_update_file_matches(final_path, size, sha256):
			return final_path
		os.remove(final_path)
	have = os.path.getsize(part_path) if os.path.isfile(part_path) else 0
	if size and have > size:
		os.remove(part_path)
		have = 0
	if not size or have < size:
		headers = {'Range': 'bytes=%d-' % have} if have else {}
		try:
			with requests.get(url, stream=True, timeout=(10, 60), headers=headers) as response:
				if have and response.status_code == 206:
					mode = 'ab'
				elif response.status_code == 200:
					mode, have = 'wb', 0
				else:
					raise TomatoUpdateError(_tr('Download failed (HTTP %1).').replace('%1', str(response.status_code)))
				total = size or (have + int(response.headers.get('Content-Length') or 0))
				progress(have, total)
				with open(part_path, mode) as handle:
					for chunk in response.iter_content(chunk_size=1 << 20):
						if cancel_event.is_set():
							raise TomatoUpdateCanceled(_tr('Download canceled.'))
						if chunk:
							handle.write(chunk)
							have += len(chunk)
							progress(have, total)
		except TomatoUpdateError:
			raise
		except Exception as exc:
			if cancel_event.is_set():   # cancelled while the connection hung: counts as cancelled
				raise TomatoUpdateCanceled(_tr('Download canceled.')) from exc
			raise TomatoUpdateError(_tr('Download interrupted: %1').replace('%1', str(exc))) from exc
	status(_tr('Verifying the download…'))
	if not _tomato_update_file_matches(part_path, size, sha256):
		try:
			os.remove(part_path)
		except OSError:
			pass
		raise TomatoUpdateError(_tr('The download is damaged (checksum mismatch). Please try again.'))
	os.replace(part_path, final_path)
	return final_path


def _tomato_attach_dmg(dmg_path, mountpoint) -> None:
	env = dict(os.environ, PAGER='/bin/cat')
	commands = (
		['/usr/bin/hdiutil', 'attach', '-nobrowse', '-readonly', '-noautoopen', '-noverify',
		 '-mountpoint', mountpoint, dmg_path],
		# hdiutil is deprecated from macOS 27 on; diskutil image is its successor
		['/usr/sbin/diskutil', 'image', 'attach', '--mountOptions', 'nobrowse', '--readOnly',
		 '--mountPoint', mountpoint, dmg_path],
	)
	for command in commands:
		if not os.path.exists(command[0]):
			continue
		try:
			# a release DMG shows a licence agreement before mounting; "Y" accepts it
			subprocess.run(command, input=b'Y\n', capture_output=True, timeout=300, env=env)
		except Exception:
			continue
		if os.path.ismount(mountpoint):
			return
	raise TomatoUpdateError(_tr('Could not open the downloaded installer.'))


def _tomato_detach_dmg(mountpoint) -> None:
	for command in (['/usr/bin/hdiutil', 'detach', mountpoint, '-quiet'],
					['/usr/bin/hdiutil', 'detach', mountpoint, '-force', '-quiet'],
					['/usr/sbin/diskutil', 'eject', mountpoint]):
		if not os.path.ismount(mountpoint):
			break
		if not os.path.exists(command[0]):
			continue
		try:
			subprocess.run(command, capture_output=True, timeout=60)
		except Exception:
			pass
	if not os.path.ismount(mountpoint):
		try:
			os.rmdir(mountpoint)
		except OSError:
			pass


def _tomato_bundle_info(bundle) -> dict:
	try:
		with open(Path(bundle) / 'Contents' / 'Info.plist', 'rb') as handle:
			data = plistlib.load(handle)
		return data if isinstance(data, dict) else {}
	except Exception:
		return {}


def tomato_verify_update_bundle(bundle) -> str:
	"""Return the bundle's version once its whole signature satisfies TOMATO_UPDATE_CODE_REQUIREMENT
	(Developer ID, team 49C7YMHM5Q, bundle id com.ryanthehito.tomato); raise TomatoUpdateError otherwise."""
	info = _tomato_bundle_info(bundle)
	if info.get('CFBundleIdentifier') != TOMATO_UPDATE_BUNDLE_ID:
		raise TomatoUpdateError(_tr('The installer does not contain Tomato.'))
	try:
		result = subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict',
								 '-R=' + TOMATO_UPDATE_CODE_REQUIREMENT, str(bundle)],
								capture_output=True, timeout=900)
	except Exception as exc:
		raise TomatoUpdateError(_tr('Could not check the signature: %1').replace('%1', str(exc))) from exc
	if result.returncode != 0:
		logging.warning('Update bundle rejected by codesign: %s', result.stderr.decode('utf-8', 'replace')[-800:])
		raise TomatoUpdateError(_tr('The update is not signed by the Tomato developer, so it was not installed.'))
	return str(info.get('CFBundleShortVersionString') or '')


def tomato_stage_update(dmg_path, target, status=None) -> dict:
	"""Copy the DMG's Tomato.app into <target's folder>/.Tomato-update and verify the copy.
	Returns the pending-install record applied after the event loop ends (tomato_apply_pending_update_install)."""
	status = status or (lambda _text: None)
	target = Path(target)
	staging_root = target.parent / TOMATO_UPDATE_STAGING_DIRNAME
	staged = staging_root / target.name
	with _TOMATO_UPDATE_FS_LOCK:
		try:
			if staging_root.exists():
				shutil.rmtree(staging_root, ignore_errors=True)
			staging_root.mkdir(parents=True, exist_ok=True)
			os.makedirs(TOMATO_UPDATE_CACHE_DIR, exist_ok=True)
			mountpoint = tempfile.mkdtemp(prefix='mnt-', dir=TOMATO_UPDATE_CACHE_DIR)
			try:
				status(_tr('Opening the installer…'))
				_tomato_attach_dmg(dmg_path, mountpoint)
				source = next((entry for entry in sorted(Path(mountpoint).iterdir())
							   if entry.suffix == '.app' and entry.is_dir() and not entry.is_symlink()
							   and _tomato_bundle_info(entry).get('CFBundleIdentifier') == TOMATO_UPDATE_BUNDLE_ID),
							  None)
				if source is None:
					raise TomatoUpdateError(_tr('The installer does not contain Tomato.'))
				status(_tr('Copying the new version…'))
				copied = subprocess.run(['/usr/bin/ditto', str(source), str(staged)],
										capture_output=True, timeout=1800)
				if copied.returncode != 0 or not staged.is_dir():
					raise TomatoUpdateError(_tr('Could not copy the new version: %1').replace(
						'%1', copied.stderr.decode('utf-8', 'replace').strip()[-300:]))
			finally:
				_tomato_detach_dmg(mountpoint)
			subprocess.run(['/usr/bin/xattr', '-dr', 'com.apple.quarantine', str(staged)],
						   capture_output=True, timeout=300)
			status(_tr('Checking the developer signature…'))
			version = tomato_verify_update_bundle(staged)
			if tomato_is_newer_version(VERSION, version):
				raise TomatoUpdateError(
					_tr('The installer holds an older version (v%1); nothing was changed.').replace('%1', str(version)))
		except Exception as exc:
			shutil.rmtree(staging_root, ignore_errors=True)
			if isinstance(exc, TomatoUpdateError):
				raise
			raise TomatoUpdateError(_tr('Could not prepare the update: %1').replace('%1', str(exc))) from exc
	return {'target': str(target), 'staged': str(staged),
			'backup': str(staging_root / ('previous-' + target.name)),
			'version': version, 'dmg': str(dmg_path)}


def _tomato_write_update_result(record) -> None:
	try:
		os.makedirs(TOMATO_UPDATE_CACHE_DIR, exist_ok=True)
		with open(TOMATO_UPDATE_RESULT_PATH, 'w', encoding='utf-8') as handle:
			json.dump(record, handle, ensure_ascii=False)
	except Exception:
		pass


def tomato_take_last_update_result() -> dict:
	"""The record the previous run left after an install attempt (read once)."""
	try:
		with open(TOMATO_UPDATE_RESULT_PATH, 'r', encoding='utf-8') as handle:
			record = json.load(handle)
	except Exception:
		return {}
	try:
		os.remove(TOMATO_UPDATE_RESULT_PATH)
	except OSError:
		pass
	return record if isinstance(record, dict) else {}


def _tomato_spawn_relauncher(app_path) -> None:
	"""Reopen app_path once this process has exited (force-kill after ~60 s if it hangs).
	Double-forked: the waiter is reparented to launchd, so reaping this process's children at exit
	cannot take it along."""
	waiter = ('pid=$1; app=$2; n=0; '
			  'while kill -0 "$pid" 2>/dev/null; do '
			  'n=$((n+1)); if [ "$n" -ge 300 ]; then kill -9 "$pid" 2>/dev/null; sleep 1; break; fi; '
			  'sleep 0.2; done; sleep 0.5; /usr/bin/open "$app"')
	try:
		subprocess.Popen(['/bin/sh', '-c', '(' + waiter + ') </dev/null >/dev/null 2>&1 &',
						  'tomato-relaunch', str(os.getpid()), str(app_path)],
						 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
						 start_new_session=True, close_fds=True).wait(timeout=10)
	except Exception:
		pass


def tomato_apply_pending_update_install() -> None:
	"""Runs after app.exec() returns: swap the staged bundle in, record the outcome, schedule the relaunch.
	A failed rename rolls back and reopens the old build, which then shows the reason (WindowUpdate's
	startup note). Once only; nothing happens unless the update window prepared an install."""
	global _TOMATO_PENDING_UPDATE_INSTALL
	pending = _TOMATO_PENDING_UPDATE_INSTALL
	_TOMATO_PENDING_UPDATE_INSTALL = None
	if not pending:
		return
	target, staged, backup = Path(pending['target']), Path(pending['staged']), Path(pending['backup'])
	record = {'status': 'failed', 'version': str(pending.get('version') or ''), 'previous': VERSION,
			  'dmg': str(pending.get('dmg') or ''), 'reason': '', 'time': time.time()}
	try:
		# exit hooks (pending writes) run now, while every file of the running build is still in place
		atexit._run_exitfuncs()
	except Exception:
		pass
	launch = target
	try:
		if not staged.is_dir():
			raise FileNotFoundError(str(staged))
		if backup.exists():
			shutil.rmtree(backup, ignore_errors=True)
		os.rename(target, backup)
		try:
			os.rename(staged, target)
		except OSError:
			try:
				os.rename(backup, target)
			except OSError:
				launch = backup
			raise
		record['status'] = 'installed'
	except Exception as exc:
		record['reason'] = '%s: %s' % (type(exc).__name__, exc)
	_tomato_write_update_result(record)
	_tomato_spawn_relauncher(str(launch))


def tomato_cleanup_update_leftovers() -> None:
	"""Startup (background thread): drop the previous bundle kept by the last swap or a stale staged copy,
	stale mounts, and cached installers this build has already reached. A failed install keeps its DMG
	for the retry."""
	with _TOMATO_UPDATE_FS_LOCK:
		bundle = tomato_running_app_bundle()
		if bundle is not None:
			staging_root = bundle.parent / TOMATO_UPDATE_STAGING_DIRNAME
			if staging_root.is_dir():
				shutil.rmtree(staging_root, ignore_errors=True)
		if not os.path.isdir(TOMATO_UPDATE_CACHE_DIR):
			return
		for name in os.listdir(TOMATO_UPDATE_CACHE_DIR):
			path = os.path.join(TOMATO_UPDATE_CACHE_DIR, name)
			try:
				if name.startswith('mnt-') and os.path.isdir(path):
					_tomato_detach_dmg(path)
				elif name.endswith(('.dmg', '.dmg.part')) and not tomato_is_newer_version(name, VERSION):
					os.remove(path)
			except Exception:
				pass


class _UpdateProgressBar(QWidget):
	"""Slim rounded track for the update window (style book 5.7.2: the system's progress bar is not drawn
	under the new design, so it is drawn here). busy=True sweeps an indeterminate segment (mount / copy /
	signature check have no percentage). Broccoli's, unchanged."""

	def __init__(self, parent=None):
		super().__init__(parent)
		self._fraction = 0.0
		self._busy = False
		self._phase = 0.0
		self._timer = QTimer(self)
		self._timer.setInterval(30)
		self._timer.timeout.connect(self._advance)
		self.setFixedHeight(6)

	def fraction(self) -> float:
		return self._fraction

	def is_busy(self) -> bool:
		return self._busy

	def set_fraction(self, fraction):
		self._busy = False
		self._timer.stop()
		self._fraction = max(0.0, min(1.0, float(fraction)))
		self.update()

	def set_busy(self, busy=True):
		self._busy = bool(busy)
		if self._busy and self.isVisible():
			self._timer.start()
		else:
			self._timer.stop()
		self.update()

	def showEvent(self, event):
		super().showEvent(event)
		if self._busy:
			self._timer.start()

	def hideEvent(self, event):
		self._timer.stop()
		super().hideEvent(event)

	def _advance(self):
		self._phase = (self._phase + 0.015) % 1.0
		self.update()

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		rect = QRectF(self.rect())
		radius = rect.height() / 2.0
		dark = is_dark_theme(app)
		track = QPainterPath()
		track.addRoundedRect(rect, radius, radius)
		painter.fillPath(track, QColor('#3A3A3C') if dark else QColor('#E5E5EA'))
		if self._busy:
			segment = rect.width() * 0.3
			fill_rect = QRectF(rect.left() - segment + (rect.width() + segment) * self._phase,
							   rect.top(), segment, rect.height())
		else:
			fill_rect = QRectF(rect.left(), rect.top(), rect.width() * self._fraction, rect.height())
		if fill_rect.width() > 0:
			fill = QPainterPath()
			fill.addRoundedRect(fill_rect, radius, radius)
			painter.setClipPath(track)
			painter.fillPath(fill, QColor('#0A84FF') if dark else QColor('#007AFF'))


class _UpdateStatusLabel(QLabel):
	"""The update window's status line; tells the window when its text changes (the window shows the line
	only while it says something, and fits its height to it). Broccoli's."""
	text_changed = None

	def setText(self, text):
		super().setText(text)
		if callable(self.text_changed):
			self.text_changed()


class WindowUpdate(QWidget):  # 增加更新页面（Check for Updates）
	"""Broccoli's update window (layout and size the same: 320 wide, as tall as its content). The release check
	runs in a background thread; "Update Now" downloads, verifies and installs the new version, then
	relaunches Tomato."""
	# (result_text, update_ready, popup_when_ready, release_info) from the check thread
	update_check_finished = pyqtSignal(str, bool, bool, object)
	# one-click install worker → GUI thread
	install_progress = pyqtSignal(object, object)   # (done_bytes, total_bytes)
	install_status = pyqtSignal(str)                # a phase without percentage
	install_failed = pyqtSignal(str)
	install_ready = pyqtSignal(object)              # pending-install record

	def __init__(self):
		super().__init__()
		self._check_inflight = False
		self._release_info = None
		self._update_available = False
		self._install_busy = False
		self._install_can_cancel = False
		self._install_cancel = None
		self._download_started_at = 0.0
		self._download_started_bytes = 0
		self._startup_note = self._read_startup_note()
		self.update_check_finished.connect(self._on_update_check_finished)
		self.install_progress.connect(self._on_install_progress)
		self.install_status.connect(self._on_install_status)
		self.install_failed.connect(self._on_install_failed)
		self.install_ready.connect(self._on_install_ready)
		self.init_ui()

	def init_ui(self):
		# style book 5.7.2 / 5.12: the system's traffic lights + window glass (make_native_glass_window, as
		# About and the donation windows); 320 wide, as tall as its content (Broccoli's update window)
		self.setUpMainWindow()
		make_native_glass_window(self)
		QWidget.layout(self).setContentsMargins(20, NATIVE_TITLEBAR_HEIGHT, 20, 20)
		self.setFixedWidth(320)
		self._fit_height()
		self.center()
		self.setWindowTitle(_tr('Tomato Updates'))
		self.setFocus()

	def _fit_height(self):
		"""As tall as the content: no empty band at the bottom. While a download runs the progress bar and the
		status line appear under the buttons and the window grows by that much (its top edge stays)."""
		layout = QWidget.layout(self)
		if layout is None:
			return
		busy = not self.install_progress_bar.isHidden() or bool(self.install_status_lbl.text().strip())
		self._progress_block.setVisible(busy)
		layout.activate()
		width = self.width() or 320
		height = layout.totalHeightForWidth(width) if layout.hasHeightForWidth() else layout.totalSizeHint().height()
		self.setFixedHeight(max(1, int(height)))

	def setUpMainWindow(self):
		# Broccoli's layout: centred lines (current, then latest version), then one row per action sharing
		# one label column and one button column
		title = QLabel(_tr("<h2>Tomato Update</h2>"), self)
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.lbl = QLabel(_tr('Current version: v%n').replace('%n', VERSION), self)
		self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

		widg5 = QWidget()
		lbl1 = QLabel(_tr('Latest version:'), self)
		self.lbl2 = QLabel('', self)
		blay5 = QHBoxLayout()
		blay5.setContentsMargins(0, 0, 0, 0)
		blay5.setSpacing(4)
		blay5.addStretch(1)
		blay5.addWidget(lbl1)
		blay5.addWidget(self.lbl2)
		blay5.addStretch(1)
		widg5.setLayout(blay5)

		lbl0 = QLabel(_tr('Check release:'), self)
		bt1 = WhiteButton(_tr('Github'))
		bt1.setFixedWidth(120)
		bt1.clicked.connect(self.upd)
		# one-click update: download with progress → verify → install → relaunch
		lbl_install = QLabel(_tr('Install update:'), self)
		self.install_btn = WhiteButton(_tr('Update Now'))
		self.install_btn.setFixedWidth(120)
		self.install_btn.setEnabled(False)
		self.install_btn.clicked.connect(self.start_install)
		label_width = max(lbl0.sizeHint().width(), lbl_install.sizeHint().width())
		action_rows = []
		for label, button in ((lbl0, bt1), (lbl_install, self.install_btn)):
			label.setFixedWidth(label_width)
			label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
			row = QWidget()
			row.setFixedHeight(50)   # About's button rows
			row_layout = QHBoxLayout(row)
			row_layout.setContentsMargins(0, 0, 0, 0)
			row_layout.setSpacing(12)
			row_layout.addStretch(1)
			row_layout.addWidget(label)
			row_layout.addWidget(button)
			row_layout.addStretch(1)
			action_rows.append(row)

		# progress bar + status line: only while there is something to show
		self._progress_block = QWidget()
		progress_layout = QVBoxLayout(self._progress_block)
		progress_layout.setContentsMargins(0, 6, 0, 0)
		progress_layout.setSpacing(10)
		self.install_progress_bar = _UpdateProgressBar(self._progress_block)
		self.install_progress_bar.hide()
		self.install_status_lbl = _UpdateStatusLabel(self._progress_block)
		self.install_status_lbl.setWordWrap(True)
		self.install_status_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		self.install_status_lbl.text_changed = lambda: QTimer.singleShot(0, self._fit_height)
		progress_layout.addWidget(self.install_progress_bar)
		progress_layout.addWidget(self.install_status_lbl)
		self.install_progress_bar.installEventFilter(self)
		self._progress_block.hide()

		main_h_box = QVBoxLayout()
		main_h_box.setContentsMargins(20, 40, 20, 20)
		main_h_box.addSpacing(10)
		main_h_box.addWidget(title)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(self.lbl)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg5)
		main_h_box.addSpacing(16)
		for row in action_rows:
			main_h_box.addWidget(row)
		main_h_box.addWidget(self._progress_block)
		main_h_box.addSpacing(10)
		self.setLayout(main_h_box)

	def eventFilter(self, obj, event):
		if obj is getattr(self, 'install_progress_bar', None) and event.type() in (QEvent.Type.Show, QEvent.Type.Hide):
			QTimer.singleShot(0, self._fit_height)
		return super().eventFilter(obj, event)

	def upd(self):
		webbrowser.open(TOMATO_UPDATE_RELEASES_URL)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def activate(self):  # 设置窗口显示
		self.show()
		self.checkupdate()

	@staticmethod
	def _read_startup_note() -> str:
		"""What the previous run's install attempt left behind, shown once with the startup check."""
		record = tomato_take_last_update_result()
		if record.get('status') == 'installed' and not tomato_is_newer_version(record.get('version'), VERSION):
			return _tr('Tomato was updated to v%1.').replace('%1', VERSION)
		if record.get('status') == 'failed':
			return _tr('The last update could not be installed (%1). Click Update Now to try again.').replace(
				'%1', str(record.get('reason') or '?'))
		return ''

	def checkupdate(self, *, popup_when_ready=False):
		"""Start the release check WITHOUT touching the network on the GUI thread (the old check fetched
		github.com right here and froze the window while GitHub was slow or unreachable)."""
		if self._check_inflight:
			return
		self._check_inflight = True
		self.lbl2.setText(_tr('Checking…'))
		self.lbl2.adjustSize()

		def worker():
			alertupdate = _tr('No Internet')
			ready = False
			info = None
			try:
				info = self.fetch_latest_release_info()
				result = (info or {}).get('tag')
				if result:
					# only a strictly NEWER release is an update (the old window offered any release that
					# differed — a build ahead of the latest release was offered a "downgrade")
					if tomato_is_newer_version(result, VERSION):
						alertupdate = result + _tr(' is ready!')
						ready = True
					else:
						alertupdate = result + _tr(' (up-to-date)')
			except Exception:
				pass
			try:
				self.update_check_finished.emit(alertupdate, ready, popup_when_ready, info)
			except RuntimeError:
				pass   # window destroyed during shutdown

		threading.Thread(target=worker, daemon=True, name='tomato-update-check').start()

	def _on_update_check_finished(self, alertupdate, ready, popup_when_ready, info):
		self._check_inflight = False
		self.lbl2.setText(str(alertupdate or ''))
		self.lbl2.adjustSize()
		if not self._install_busy:
			self._update_available = bool(ready)
			self._release_info = dict(info) if (ready and isinstance(info, dict)) else None
			has_package = bool((self._release_info or {}).get('dmg_url'))
			self.install_btn.setEnabled(has_package)
			if ready and not has_package:
				self.install_status_lbl.setText(_tr('This release has no installer package; use the Github button.'))
		note = self._startup_note if popup_when_ready else ''
		if note and not self._install_busy:
			self._startup_note = ''
			self.install_status_lbl.setText(note)
		if popup_when_ready and (ready or note) and not self.isVisible():
			self.show()

	# ---- one-click install ----------------------------------------------------
	def start_install(self):
		if self._install_busy:
			# the same button reads "Cancel" while the download runs
			if self._install_can_cancel and self._install_cancel is not None:
				self._install_cancel.set()
				self.install_btn.setEnabled(False)
				self.install_status_lbl.setText(_tr('Canceling…'))
			return
		info = dict(self._release_info or {})
		if not info.get('dmg_url'):
			return
		self._install_busy = True
		self._install_can_cancel = True
		self._install_cancel = threading.Event()
		self._download_started_at = 0.0
		self._download_started_bytes = 0
		self.install_btn.setText(_tr('Cancel'))
		self.install_progress_bar.set_fraction(0.0)
		self.install_progress_bar.show()
		self.install_status_lbl.setText(_tr('Connecting…'))
		threading.Thread(target=self._install_worker, args=(info, self._install_cancel),
						 daemon=True, name='tomato-update-install').start()

	def _install_worker(self, info, cancel_event):
		last_emit = [0.0]

		def progress(done, total):
			now = time.monotonic()
			if now - last_emit[0] >= 0.1 or (total and done >= total):
				last_emit[0] = now
				self.install_progress.emit(int(done), int(total))

		try:
			dmg_path = tomato_download_update_dmg(info, progress, cancel_event, status=self.install_status.emit)
			bundle = tomato_running_app_bundle()
			blocker = tomato_update_install_blocker(bundle)
			if blocker:
				# this copy cannot replace itself: hand the verified DMG to Finder instead
				subprocess.Popen(['/usr/bin/open', dmg_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				self.install_ready.emit({'manual': True, 'reason': blocker, 'dmg': dmg_path})
				return
			self.install_ready.emit(tomato_stage_update(dmg_path, bundle, status=self.install_status.emit))
		except TomatoUpdateError as exc:
			self.install_failed.emit(str(exc))
		except Exception as exc:
			logging.exception('One-click update failed.')
			self.install_failed.emit(_tr('Update failed: %1').replace('%1', str(exc)))

	def _on_install_progress(self, done, total):
		done, total = int(done or 0), int(total or 0)
		now = time.monotonic()
		if not self._download_started_at:
			self._download_started_at, self._download_started_bytes = now, done
		mb = 1024 * 1024
		text = _tr('Downloading… %1 / %2 MB').replace('%1', '%.1f' % (done / mb)).replace(
			'%2', ('%.1f' % (total / mb)) if total else '?')
		elapsed = now - self._download_started_at
		if elapsed >= 1.0 and done > self._download_started_bytes:
			text += ' · %.1f MB/s' % ((done - self._download_started_bytes) / mb / elapsed)
		self.install_progress_bar.set_fraction(done / total if total else 0.0)
		self.install_status_lbl.setText(text)

	def _on_install_status(self, text):
		# verify / mount / copy / signature: no percentage and no way back
		self._install_can_cancel = False
		self.install_btn.setEnabled(False)
		self.install_btn.setText(_tr('Installing…'))
		self.install_progress_bar.set_busy(True)
		self.install_status_lbl.setText(str(text or ''))

	def _reset_install_controls(self):
		self._install_busy = False
		self._install_can_cancel = False
		self._install_cancel = None
		self.install_progress_bar.set_busy(False)
		self.install_progress_bar.hide()
		self.install_btn.setText(_tr('Update Now'))
		self.install_btn.setEnabled(self._update_available and bool((self._release_info or {}).get('dmg_url')))

	def _on_install_failed(self, message):
		self._reset_install_controls()
		self.install_status_lbl.setText(str(message or ''))
		if not self.isVisible():
			self.show()

	def _on_install_ready(self, pending):
		pending = dict(pending or {})
		if pending.get('manual'):
			self._reset_install_controls()
			self.install_status_lbl.setText(
				_tr("Can't install automatically (%1). The installer is open: drag Tomato into Applications.").replace(
					'%1', str(pending.get('reason', ''))))
			return
		global _TOMATO_PENDING_UPDATE_INSTALL
		_TOMATO_PENDING_UPDATE_INSTALL = pending
		self.install_progress_bar.set_fraction(1.0)
		self.install_status_lbl.setText(_tr('Restarting Tomato to finish the update…'))
		if not self.isVisible():
			self.show()
		QTimer.singleShot(800, self._quit_for_install)

	def _quit_for_install(self):
		# Tomato's normal Quit (totalquit: today's diary line, the sync / auto-record threads and the tools
		# service stopped, then app.quit()); the swap itself runs after app.exec() returns
		main = globals().get('w3')
		if main is not None and hasattr(main, 'totalquit'):
			main.totalquit()
		else:
			app.quit()

	@classmethod
	def fetch_latest_release_info(cls):
		"""Release info (tag + DMG asset) from the API; when the API is unavailable, the tag alone from the
		releases page (no one-click install then — the Github button still works)."""
		try:
			info = tomato_fetch_latest_release()
			if info:
				return info
		except Exception:
			pass
		tag = cls.extract_latest_tag(cls.fetch_latest_version_text())
		return {'tag': tag} if tag else None

	@staticmethod
	def fetch_latest_version_text():
		# the releases page as plain text (the fallback when the API is unavailable)
		try:
			s = requests.session()
			s.keep_alive = False
			response = s.get(TOMATO_UPDATE_RELEASES_URL, timeout=(4, 8))
			response.encoding = 'utf-8'
			soup = BeautifulSoup(response.text, "html.parser")
			for img in soup.find_all("img"):
				img.decompose()
			text_maker = html2text.HTML2Text()
			text_maker.ignore_links = True
			text_maker.ignore_images = True
			plain_text = text_maker.handle(str(soup))
			plain_text_utf8 = plain_text.encode(response.encoding).decode("utf-8")
			for _ in range(10):
				plain_text_utf8 = (plain_text_utf8
								   .replace('\n\n\n\n', '\n\n')
								   .replace('\n\n\n', '\n\n')
								   .replace('   ', ' ')
								   .replace('  ', ' '))
			return plain_text_utf8
		except Exception:
			return None

	@staticmethod
	def extract_latest_tag(plain_text_utf8):
		# e.g. 'v1.2.13'
		if not plain_text_utf8:
			return None
		result = re.compile(r'(v\d+\.\d+\.\d+)\sLatest').findall(plain_text_utf8)
		return result[0] if result else None


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


class SyncIndicatorDialog(QDialog):
	"""The small "syncing" card over the main window: a floating glass card (window glass, corner 16), never
	modal; the main window puts it where it belongs."""
	_no_auto_place = True

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
		self.radius = glass_kit.MAIN_WINDOW_SMOOTH_RADIUS


install_glass_dialog_class(SyncIndicatorDialog)


class window3(QWidget):  # 主程序的代码块（Find a dirty word!）
	def __init__(self):
		super().__init__()
		self.radius = 16
		self.dragPosition = self.pos()
		self._diary_text_edits = []
		self._diary_box_base = {}        # diary box → (day, the file as the box loaded it), see _save_diary_box
		self._diary_viewport_owner = {}
		self._suppress_diary_write = False
		self._last_local_reminder_change = 0.0
		self._last_safety_notification_time = {}  # Track last notification time per function
		self._safety_notification_cooldown = 60  # Cooldown in seconds to prevent spam
		self.initUI()
		# the screen changes its resolution / Dock / menu bar, or a screen is plugged in or out: the window
		# takes its place again at once (as Broccoli's main window: the screens' own signals restart one
		# 300 ms timer; nothing polls)
		self._screen_fit_timer = QTimer(self)
		self._screen_fit_timer.setSingleShot(True)
		self._screen_fit_timer.setInterval(300)
		self._screen_fit_timer.timeout.connect(self._fit_to_current_screen)
		self._connect_screen_fit_signals()

	def _connect_screen_fit_signals(self):
		gui_app = QGuiApplication.instance()
		if gui_app is None:
			return
		try:
			gui_app.screenAdded.connect(self._on_screen_fit_screen_added)
			gui_app.screenRemoved.connect(self._schedule_screen_fit)
			gui_app.primaryScreenChanged.connect(self._schedule_screen_fit)
		except Exception:
			pass
		for screen in QGuiApplication.screens() or []:
			self._connect_screen_fit_screen(screen)

	def _connect_screen_fit_screen(self, screen):
		# the marker lives on the screen object: a replacement one (unplug / replug) is connected afresh
		if screen is None or screen.property('_tomato_fit_connected'):
			return
		screen.setProperty('_tomato_fit_connected', True)
		try:
			screen.geometryChanged.connect(self._schedule_screen_fit)
			screen.availableGeometryChanged.connect(self._schedule_screen_fit)
		except Exception:
			pass

	def _on_screen_fit_screen_added(self, screen):
		self._connect_screen_fit_screen(screen)
		self._schedule_screen_fit()

	def _connect_screen_fit_handle(self):
		# setWindowFlags() makes a new native window: connect its "moved to another screen" again
		handle = self.windowHandle()
		if handle is None or handle is getattr(self, '_screen_fit_handle', None):
			return
		self._screen_fit_handle = handle
		try:
			handle.screenChanged.connect(self._schedule_screen_fit)
		except Exception:
			pass

	def showEvent(self, event):
		super().showEvent(event)
		self._connect_screen_fit_handle()
		keep_out_of_stage_manager(self)

	def _apply_window_flags(self):
		flags = Qt.WindowType.FramelessWindowHint
		if getattr(self, '_always_on_top', True):
			flags |= Qt.WindowType.WindowStaysOnTopHint
		self.setWindowFlags(flags)

	def set_always_on_top(self, enabled):
		"""(Broccoli's.) The main window — the strip at the screen edge too — above every other window, or
		an ordinary window that other windows can cover. Changing the flags makes a new native window: it is
		shown again where it was, without taking the keyboard."""
		enabled = bool(enabled)
		if enabled == getattr(self, '_always_on_top', True):
			return
		was_visible = self.isVisible()
		geom = self.geometry()
		self._always_on_top = enabled
		self._apply_window_flags()
		if was_visible:
			self.show()
			self.setGeometry(geom)
			if enabled:
				self.raise_()

	def is_always_on_top(self):
		return bool(getattr(self, '_always_on_top', True))

	def _toggle_all_spaces(self, checked):
		self._app_settings['show_on_all_spaces'] = bool(checked)
		self._save_app_settings()
		set_show_on_all_spaces(checked)

	def _toggle_dock_icon(self, checked):
		self._app_settings['dock_icon'] = bool(checked)
		self._save_app_settings()
		set_dock_icon_visible(bool(checked), activate=bool(checked))

	def _toggle_always_on_top(self, checked):
		self._app_settings['always_on_top'] = bool(checked)
		self._save_app_settings()
		self.set_always_on_top(checked)

	def _strip_top(self, area):
		"""Where the 120-high strip window goes so that the strip's middle is the middle between the top of
		the screen and the top of the Dock (Ryan 2026-11-16: "始终处于屏幕上下的正中间 … 去掉 dock 高度的
		正中间"). `area` = the screen's available geometry (it ends where the Dock begins)."""
		screen = QGuiApplication.screenAt(area.center())
		top = screen.geometry().y() if screen is not None else area.y()
		bottom = area.y() + area.height()
		return int(round((top + bottom) / 2 - 60))

	def _schedule_screen_fit(self, *_args):
		timer = getattr(self, '_screen_fit_timer', None)
		if timer is not None:
			timer.start()

	def _fit_to_current_screen(self):
		"""Size and place as pin_a_tab does, from the screen as it is now: out = half the screen wide and
		as tall as it, at the left; in = the thin strip at the left edge, at the screen's middle height."""
		if not self.isVisible():
			return 'hidden'   # the next show / pin_a_tab sizes from the screen of that moment
		animation = getattr(self, '_geometry_animation', None)
		try:
			running = animation is not None and animation.state() == QPropertyAnimation.State.Running
		except RuntimeError:
			running = False
		if running:
			self._schedule_screen_fit()   # once the slide has settled
			return 'deferred'
		handle = self.windowHandle()
		screen = (handle.screen() if handle is not None else None) or self.screen() or QGuiApplication.primaryScreen()
		if screen is None:
			return 'no screen'
		area = screen.availableGeometry()
		height = int(area.height())
		if self.tab_bar.isVisible():
			state = 'out'
			target = QRect(3, 0, int(area.width() / 2), height)
			self.setMinimumSize(0, 0)
			self.setMaximumSize(16777215, 16777215)
		else:
			state = 'in'
			target = QRect(0, self._strip_top(area), self.new_width, 120)
			self.setFixedSize(self.new_width, 120)
		if self.geometry() != target:
			self.setGeometry(target)
		logging.info('Main window screen fit (%s): available %dx%d at (%d,%d) -> window %dx%d at (%d,%d)',
					 state, area.width(), area.height(), area.x(), area.y(),
					 target.width(), target.height(), target.x(), target.y())
		return state

	def initUI(self):  # 设置窗口内布局
		self._init_sync_indicator()
		self.newlist()
		fulldir1 = TOMATO_DATA_DIR
		os.makedirs(fulldir1, exist_ok=True)
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
		# Settings file for app preferences
		self.settings_file = os.path.join(fulldir1, 'app_settings.json')
		self._load_app_settings()
		self.setUpMainWindow()
		MOST_WEIGHT = int(self.screen().availableGeometry().width() * 0.75)
		HALF_WEIGHT = int(self.screen().availableGeometry().width() / 2)
		MINI_WEIGHT = int(self.screen().availableGeometry().width() / 4)
		SCREEN_WEIGHT = int(self.screen().availableGeometry().width())

		DE_HEIGHT = int(self.screen().availableGeometry().height())
		HALF_HEIGHT = int(self.screen().availableGeometry().height() * 0.5)
		BIGGIST_HEIGHT = int(self.screen().availableGeometry().height())

		self.resize(HALF_WEIGHT, DE_HEIGHT)
		self.move(self.width() + 3, self._strip_top(self.screen().availableGeometry()))
		self.move_window2(0, self._strip_top(self.screen().availableGeometry()))
		self._always_on_top = True
		self._apply_window_flags()
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.show()
		self.tab_bar.setVisible(False)
		self.new_width = 10
		self.setFixedSize(self.new_width, 120)
		self._style_edge_strip()
		self.auto_record_thread = None
		self.system_sync_thread = None
		self.system_sync_queue = queue.Queue()
		self._sync_processing = False
		self.reminder_sync_timer = QTimer(self)
		self.reminder_sync_timer.setInterval(3000)
		self.reminder_sync_timer.timeout.connect(self._process_sync_messages)
		self.reminder_sync_timer.start()
		self._start_system_sync_worker()
		# an item named "@Broccoli …" is sent to Broccoli when its time comes (tomato_broccoli.py): one single-shot
		# timer for the nearest one, set again when the table file changes, on wake and on a clock change
		self.broccoli_scheduler = tomato_broccoli.Scheduler(self, self._broccoli_entries, self._broccoli_complete_row,
															self.fulldirall, self._broccoli_notice)
		QTimer.singleShot(3000, self.broccoli_scheduler.rearm)
		# long instructions: task folders (task.md + schedule.json) in Broccoli's data folder; "@" in the item box
		# lists them; a folder that holds both files is put on the table (also when Broccoli wrote it)
		self.broccoli_store = tomato_broccoli.TaskStore()
		self.broccoli_scheduler.store = self.broccoli_store
		self.broccoli_tasks = tomato_broccoli.TaskSync(self, self.broccoli_store, os.path.join(os.path.dirname(self.fulldirall), 'broccoli_tasks.json'),
													 self._broccoli_add_rows, self._broccoli_remove_rows)
		self.broccoli_tasks.changed.connect(self._broccoli_tasks_changed)
		self.broccoli_suggest = tomato_broccoli_ui.TaskSuggest(self.le1, self.broccoli_store, self.open_broccoli_tasks)
		self._broccoli_manager = None
		self._broccoli_editors = []
		self.broccoli_store.write_manifest()
		tomato_broccoli.install_skill()
		self.broccoli_discussion = tomato_broccoli.Discussion(self)
		tomato_broccoli.PLAIN_GROUP = _tr('Scheduled tasks')
		self.broccoli_discussion.finished.connect(self._broccoli_discussion_finished)
		QTimer.singleShot(3500, self.broccoli_tasks.sync)
		self._tools_host = None
		self._main_runner = _MainThreadRunner()      # made here, on the main thread: what it is handed runs here
		QTimer.singleShot(2500, self._start_tools_service)
		self._feed_watcher = None
		QTimer.singleShot(3000, self._start_feed_watcher)
		self._report_dialog = None
		self._report_waiting = {}        # (kind, key) → (when Broccoli was asked for the written part, meta)
		self._report_slot_cache = {}     # the calendar's days, by file (tomato_report.day_slots)
		try:
			tomato_report.move_old_layout(TOMATO_DATA_DIR)      # the first version's Reports/<day>.md → Reports/day/
		except Exception:
			logging.exception('The old reports could not be moved.')
		self._report_sender = tomato_broccoli.send
		self._report_timer = QTimer(self)
		self._report_timer.setSingleShot(True)
		self._report_timer.timeout.connect(self._report_time_came)
		QTimer.singleShot(6000, self._report_time_came)

	def setUpMainWindow(self):
		# The window body with the glass tab bar on top (style book 5.6 / 5.12); each page is a stage: its
		# table fills it and the edit panel floats on the table's lower part.
		self.tab_bar = GlassTabWidget(kind='body')
		self.word_tab = QWidget()
		self.art_tab = QWidget()
		self.insp_tab = QWidget()
		self.collect_tab = QWidget()
		self._edit_stages = []

		self.tab_bar.addTab(self.word_tab, _tr("Time"))
		self.tab_bar.addTab(self.art_tab, _tr("Frequency"))
		self.tab_bar.addTab(self.insp_tab, _tr("Memory"))
		self.tab_bar.addTab(self.collect_tab, _tr("Collection"))
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

		# date / time boxes: normal inputs; the calendar a date box opens = a small glass pop-up (5.4.1)
		for field in self.findChildren(QDateEdit):
			style_date_time_field(field, 'calendar')
			glass_calendar_popup(field)
		for field in self.findChildren(QTimeEdit):
			style_date_time_field(field, 'clock')
		self._install_quick_edit()

		self.set_edit_panel_open(self._app_settings.get('edit_panel_open', True), animate=False, save=False)

	def _page_stage(self, page, content, panel):
		"""One page: `content` (its table) fills it, `panel` (the edit part) floats on the table's lower
		part as a Liquid Glass drawer (style book 5.12)."""
		stage = FloatPanelStage(content, panel, on_toggle=self.set_edit_panel_open)
		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(stage)
		page.setLayout(layout)
		self._edit_stages.append(stage)
		return stage

	def set_edit_panel_open(self, open_, animate=True, save=True):
		"""The edit panels of all four pages are pushed in / pulled out together; only the page on screen
		slides. The choice is remembered (app_settings.json)."""
		open_ = bool(open_)
		current = self.tab_bar.currentWidget()
		for stage in self._edit_stages:
			on_screen = current is not None and current.isAncestorOf(stage) and stage.isVisible()
			stage.set_open(open_, animate=bool(animate and on_screen))
		if save and self._app_settings.get('edit_panel_open', True) != open_:
			self._app_settings['edit_panel_open'] = open_
			self._save_app_settings()

	def _style_edge_strip(self):
		"""The thin strip that shows / hides the window (not glass, style book 5.10): filled with the system
		accent while the window is out, white (dark: #3A3A3A) with a hairline while it is in."""
		shown = self.i % 2 == 0
		dark = is_dark_theme(app)
		if shown:
			fill, edge = get_accent_color_hex(), 'transparent'
		else:
			fill, edge = ('#3A3A3A', '#4A4B4F') if dark else ('#FFFFFF', '#D9D9DE')
		self.btn_00.setStyleSheet(
			'QPushButton { border: 1px solid %s; background-color: %s; border-radius: 4px; padding: 1px; }' % (edge, fill))

	def move_window(self, width, height):
		animation = QPropertyAnimation(self, b"geometry", self)
		self._geometry_animation = animation
		animation.setDuration(250)
		new_pos = QRect(width, height, self.width(), self.height())
		animation.setEndValue(new_pos)
		# Stage Manager (measured 2026-11-25 on the real screen): while the window slides out the system
		# sometimes fits it into the room right of its strip — it ended at x 188, 924 × 1198 instead of
		# x 3, 1028 × 1218 — and Tomato never heard of it. Once the slide has settled: is it where it was sent?
		self._slide_serial = getattr(self, '_slide_serial', 0) + 1
		serial = self._slide_serial
		animation.finished.connect(lambda: QTimer.singleShot(self.SLIDE_LANDING_CHECK_MS, lambda: self._check_slide_landing(serial, QRect(new_pos))))
		animation.start()
		self.i += 1
		self._style_edge_strip()

	SLIDE_LANDING_CHECK_MS = 450
	SLIDE_LANDING_TOLERANCE = 8

	def _slide_landing_off(self, got, wanted):
		"""Away from where it was sent: the left edge elsewhere, or made SMALLER. (Wider / taller than asked is
		the window's own smallest size on a small screen, not somebody moving it.)"""
		tolerance = self.SLIDE_LANDING_TOLERANCE
		return (abs(got.x() - wanted.x()) > tolerance or got.width() < wanted.width() - tolerance
				or got.height() < wanted.height() - tolerance)

	def _check_slide_landing(self, serial, wanted):
		"""After a slide: put the window back where it was sent when something else moved or resized it — once
		per slide, so nothing is fought over. (The height from the top is the system's: a window cannot go
		under the menu bar, so only left edge, width and height are compared.)"""
		if serial != getattr(self, '_slide_serial', 0) or not self.isVisible():
			return 'stale'
		got = self.geometry()
		if not self._slide_landing_off(got, wanted):
			return 'in place'
		logging.info('Main window was moved after its slide: wanted %dx%d at (%d,%d), found %dx%d at (%d,%d) -> put back once',
					 wanted.width(), wanted.height(), wanted.x(), wanted.y(), got.width(), got.height(), got.x(), got.y())
		self.setGeometry(QRect(wanted))
		self._slide_put_back = getattr(self, '_slide_put_back', 0) + 1
		QTimer.singleShot(700, lambda: self._log_slide_landing(serial, QRect(wanted)))
		return 'put back'

	def _log_slide_landing(self, serial, wanted):
		if serial != getattr(self, '_slide_serial', 0) or not self.isVisible():
			return
		got = self.geometry()
		stayed = not self._slide_landing_off(got, wanted)
		logging.info('Main window after being put back: %dx%d at (%d,%d) — %s', got.width(), got.height(), got.x(), got.y(),
					 'stayed' if stayed else 'moved again (left as it is)')

	def move_window2(self, width, height):
		animation = QPropertyAnimation(self, b"geometry", self)
		self._geometry_animation = animation
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

	# ── a Collection row dragged into the diary (2026-11-23) ─────────────────────────────────────────────
	# Ryan 2026-11-23: "把选中的这个食物直接拖到这个日志里面，然后就直接就记上了"; no meal label, only the time ("你就加
	# 个时间，自动加个时间就行。然后后面再自己归总"). The line is "- HH:MM:SS [collection] name"; the collection itself
	# is not changed, and the report looks the row's numbers up by that name.
	def _collection_drag_filter(self, event):
		"""Press on a row and move further than the system's drag distance: the row is dragged (as a copy)."""
		kind = event.type()
		if kind == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
			index = self.collection_table.indexAt(event.position().toPoint())
			self._collection_drag_from = (event.position().toPoint(), index.row()) if index.isValid() else None
		elif kind == QEvent.Type.MouseButtonRelease:
			self._collection_drag_from = None
		elif kind == QEvent.Type.MouseMove and self._collection_drag_from is not None and event.buttons() & Qt.MouseButton.LeftButton:
			start, row = self._collection_drag_from
			if (event.position().toPoint() - start).manhattanLength() >= QApplication.startDragDistance() \
					and self.collection_table.state() != QAbstractItemView.State.EditingState:
				self._collection_drag_from = None
				mime = self._collection_row_mime(row)
				if mime is not None:
					drag = QDrag(self.collection_table)
					drag.setMimeData(mime)
					rect = self.collection_table.visualRect(self.collection_table.model().index(row, 0))
					rect.setLeft(0)
					rect.setWidth(min(self.collection_table.viewport().width(), 360))
					picture = self.collection_table.viewport().grab(rect)
					if not picture.isNull():
						faded = QPixmap(picture.size())
						faded.setDevicePixelRatio(picture.devicePixelRatio())
						faded.fill(Qt.GlobalColor.transparent)
						painter = QPainter(faded)
						painter.setOpacity(0.7)
						painter.drawPixmap(0, 0, picture)
						painter.end()
						drag.setPixmap(faded)
						drag.setHotSpot(QPoint(min(start.x(), rect.width() - 1), rect.height() // 2))
					drag.exec(Qt.DropAction.CopyAction)
					return True
		return False

	def _collection_row_mime(self, row):
		if not self.collection_current_file or not (0 <= row < self.collection_table.rowCount()):
			return None
		values = [self._collection_item_text(row, column) for column in range(self.collection_table.columnCount())]
		title = tomato_tools.row_title(self._collection_headers(), values)
		if not title:
			return None
		name = os.path.splitext(os.path.basename(self.collection_current_file))[0]
		mime = QMimeData()
		mime.setData(COLLECTION_ROW_MIME, json.dumps({'collection': name, 'name': title}, ensure_ascii=False).encode('utf-8'))
		mime.setText(title)                    # dropped into another app: the row's name
		return mime

	def _collection_row_dropped(self, mime, box=None):
		try:
			data = json.loads(bytes(mime.data(COLLECTION_ROW_MIME)).decode('utf-8'))
			text = tomato_diary.collection_line(data['collection'], data['name'])
		except Exception:
			logging.exception('The dropped Collection row could not be read.')
			return None
		line = self.add_diary_line(text)
		if box is not None:                    # the box it was dropped on shows it at once, at its end
			self._refresh_diary_text_widget(box)
		return line

	def _save_diary_box(self, widget):
		"""A diary box changed. Loaded by the program (it shows the file) → only remembered as what the box knows.
		Typed in by the person → saved without losing what was written into the file behind the box
		(tomato_diary.merge_box): the front-app record, a line from Broccoli, another box. The lines the box did
		not have yet are added at its end; the caret stays where the person is typing."""
		box = widget.toPlainText()
		today = tomato_diary.day_name()
		if self._suppress_diary_write:
			self._diary_box_base[widget] = (today, box)
			return
		if box == '':
			return
		if box == tomato_diary.read(self.fulldir_dia, today):
			self._diary_box_base[widget] = (today, box)
			return
		day, base = self._diary_box_base.get(widget, (today, None))
		try:
			text, extra = tomato_diary.save_box(self.fulldir_dia, day, base, box)
		except Exception:
			logging.exception('The diary could not be saved.')
			return
		if extra:
			self._suppress_diary_write = True
			try:
				own = widget.textCursor()
				anchor, position = own.anchor(), own.position()
				cursor = QTextCursor(widget.document())
				cursor.movePosition(QTextCursor.MoveOperation.End)
				cursor.insertText(extra)
				if widget.textCursor().position() != position:     # typing at the very end: stay before the added lines
					own.setPosition(anchor)
					own.setPosition(position, QTextCursor.MoveMode.KeepAnchor)
					widget.setTextCursor(own)
			finally:
				self._suppress_diary_write = False
			text = widget.toPlainText()
		self._diary_box_base[widget] = (day, text)

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
		if target in self._diary_text_edits and event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop) \
				and event.mimeData().hasFormat(COLLECTION_ROW_MIME):
			# a Collection row dropped on a diary box is a diary line of its own, not text put in at the caret
			if event.type() == QEvent.Type.Drop:
				self._collection_row_dropped(event.mimeData(), target)
			event.setDropAction(Qt.DropAction.CopyAction)
			event.accept()
			return True
		if obj is getattr(self, '_collection_viewport', None) and self._collection_drag_filter(event):
			return True
		if obj == getattr(self, 'collection_view_stack', None) and event.type() == QEvent.Type.Resize:
			self._position_collection_toggle_button()
		# Handle time_edit hover for clock picker (all time edits)
		time_edit_popup_map = self._get_time_edit_popup_map()
		if obj in time_edit_popup_map:
			popup = time_edit_popup_map[obj]
			if event.type() == QEvent.Type.Enter:
				# Use a timer to delay showing the popup
				if not hasattr(self, '_clock_hover_timers'):
					self._clock_hover_timers = {}
				if obj not in self._clock_hover_timers:
					timer = QTimer(self)
					timer.setSingleShot(True)
					timer.timeout.connect(lambda te=obj, p=popup: self._show_clock_picker_for(te, p))
					self._clock_hover_timers[obj] = timer
				self._clock_hover_timers[obj].start(200)
			elif event.type() == QEvent.Type.Leave:
				if hasattr(self, '_clock_hover_timers') and obj in self._clock_hover_timers:
					self._clock_hover_timers[obj].stop()
				if popup.isVisible():
					popup._hide_timer.start(600)
		return super().eventFilter(obj, event)

	def _get_time_edit_popup_map(self):
		"""Return a mapping of time_edit widgets to their clock picker popups"""
		mapping = {}
		if hasattr(self, 'time_edit') and hasattr(self, 'clock_picker_popup'):
			mapping[self.time_edit] = self.clock_picker_popup
		if hasattr(self, 'freq_time_edit') and hasattr(self, 'freq_clock_picker_popup'):
			mapping[self.freq_time_edit] = self.freq_clock_picker_popup
		if hasattr(self, 'memo_time_edit') and hasattr(self, 'memo_clock_picker_popup'):
			mapping[self.memo_time_edit] = self.memo_clock_picker_popup
		if hasattr(self, 'collect_time_edit') and hasattr(self, 'collect_clock_picker_popup'):
			mapping[self.collect_time_edit] = self.collect_clock_picker_popup
		mapping.update(getattr(self, '_extra_clock_popups', {}))
		return mapping

	def _attach_clock(self, time_edit):
		"""A time box made after the four pages (the end boxes, the quick-edit card's): the same hover clock
		pop-up as the start boxes have (style book 5.4.1)."""
		if not hasattr(self, '_extra_clock_popups'):
			self._extra_clock_popups = {}
		popup = ClockPickerPopup()
		popup.set_target_widget(time_edit)
		popup.time_changed.connect(lambda t, edit=time_edit: edit.setTime(t))
		time_edit.installEventFilter(self)
		self._extra_clock_popups[time_edit] = popup
		return popup

	def _detach_clock(self, time_edit):
		popup = getattr(self, '_extra_clock_popups', {}).pop(time_edit, None)
		timers = getattr(self, '_clock_hover_timers', {})
		timer = timers.pop(time_edit, None)
		if timer is not None:
			timer.stop()
		if popup is not None:
			popup.hide()
			popup.deleteLater()

	def _end_time_row(self, prefix, start_date, start_time, length_edit, length_unit):
		"""The row under a page's start date / time: '→' + end date + end time, kept in step with start +
		length (style book 5.12 "结束时间", 2026-11-22)."""
		arrow, end_date, end_time = end_time_boxes(self, start_date, start_time)
		self._attach_clock(end_time)
		link = EndTimeLink(start_date, start_time, length_edit, length_unit, end_date, end_time, self._time_unit_hours_index)
		setattr(self, prefix + '_end_date_edit', end_date)
		setattr(self, prefix + '_end_time_edit', end_time)
		setattr(self, prefix + '_end_time_link', link)
		row = QHBoxLayout()
		row.setContentsMargins(0, 0, 0, 0)
		row.addWidget(arrow)
		row.addWidget(end_date)
		row.addWidget(end_time)
		return row

	def _show_clock_picker_for(self, time_edit, popup):
		"""Show the clock picker popup above the time_edit widget"""
		popup.set_time(time_edit.time())
		popup.set_mode(True)  # Start with hour selection
		# Position above the time_edit (subtract popup height from top-left position)
		top_left = time_edit.mapToGlobal(time_edit.rect().topLeft())
		global_pos = PyQt6.QtCore.QPoint(top_left.x(), top_left.y() - popup.height())
		popup.showAt(global_pos)

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
		fulldir1 = TOMATO_DATA_DIR
		os.makedirs(fulldir1, exist_ok=True)
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
				self._clear_table_selection(self.tableWidget)
				self._clear_table_selection(self.tableWidget_record)
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
				self._clear_table_selection(self.tableWidget_freq)
				self._clear_table_selection(self.tableWidget_record2)
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
				self._clear_table_selection(self.tableWidget_memo)
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

		# Setup delegate for keyboard-based editing detection
		self._table_delegate = TableEditDelegate(self.tableWidget)
		self.tableWidget.setItemDelegate(self._table_delegate)
		self._table_delegate.editing_started.connect(self._on_table_edit_started)
		self._table_delegate.editing_finished.connect(self._on_table_edit_finished)
		#self.tableWidget.setFixedHeight(int(self.height() * 2 / 3))

		t1 = QWidget()
		self.le1 = QLineEdit(self)
		self.le1.setPlaceholderText(_tr('Item (with notes in {})'))
		self.le1.setFixedHeight(MAIN_ROW_HEIGHT)

		self.date_edit = QDateEdit(self)
		self.date_edit.setCalendarPopup(True)
		self.date_edit.setDisplayFormat('yyyy-MM-dd')
		self.date_edit.setDate(QDate.currentDate())
		self.date_edit.setFixedHeight(GREY_ROW_HEIGHT)
		self.date_edit.setToolTip(_tr('Choose Date'))

		self.time_edit = QTimeEdit(self)
		self.time_edit.setDisplayFormat('HH:mm')
		self.time_edit.setTime(QTime.currentTime())
		self.time_edit.setFixedHeight(GREY_ROW_HEIGHT)
		self.time_edit.setToolTip(_tr('Hover to open clock picker'))
		self.time_edit.installEventFilter(self)

		# Clock picker popup (hover triggered)
		self.clock_picker_popup = ClockPickerPopup()
		self.clock_picker_popup.set_target_widget(self.time_edit)
		self.clock_picker_popup.time_changed.connect(lambda t: self.time_edit.setTime(t))

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
		self.le3.setPlaceholderText(_tr('Length'))
		self.le3.setFixedHeight(GREY_ROW_HEIGHT)

		self.length_unit = compact_dropdown(self)
		for label, factor in self._time_unit_items:
			self.length_unit.addItem(_tr(label), factor)
		self.length_unit.setCurrentIndex(self._time_unit_hours_index)

		self.le4 = QLineEdit(self)
		self.le4.setPlaceholderText(_tr('Repeat'))
		self.le4.setFixedHeight(GREY_ROW_HEIGHT)
		self._refresh_on_program_change(self.le4, self.refresh)

		self.repeat_unit = compact_dropdown(self)
		for label, factor in self._time_unit_items:
			self.repeat_unit.addItem(_tr(label), factor)
		self.repeat_unit.setCurrentIndex(self._time_unit_hours_index + 1)

		self.repeat_until_check = QCheckBox(_tr('Repeat until'), self)
		self.repeat_until_check.setChecked(False)
		self.repeat_until_date = QDateEdit(self)
		self.repeat_until_date.setCalendarPopup(True)
		self.repeat_until_date.setDisplayFormat('yyyy-MM-dd')
		self.repeat_until_date.setDate(QDate.currentDate())
		self.repeat_until_date.setFixedHeight(GREY_ROW_HEIGHT)
		self.repeat_until_date.setEnabled(False)
		self.repeat_until_check.toggled.connect(lambda _: self._apply_repeat_until_enable(self.repeat_until_check, self.repeat_until_date))

		b1_row1 = QHBoxLayout()
		b1_row1.setContentsMargins(0, 0, 0, 0)
		b1_row1.addWidget(self.le1)
		
		b1_row2 = QHBoxLayout()
		b1_row2.setContentsMargins(0, 0, 0, 0)
		# two rows, so every box keeps a readable width in a window half the screen wide:
		# when + how long, then how often + until when
		self.date_edit.setFixedWidth(118)
		self.time_edit.setFixedWidth(76)
		self.repeat_until_date.setFixedWidth(118)
		self.length_unit.setFixedWidth(132)
		self.repeat_unit.setFixedWidth(132)
		# start → end (2026-11-22, style book 5.12 "结束时间"): the end follows start + length, and a new end
		# gives a new length; so the length and the repeat share the next row, repeat-until the one after
		self.end_arrow, self.end_date_edit, self.end_time_edit = end_time_boxes(self, self.date_edit, self.time_edit)
		self._attach_clock(self.end_time_edit)
		self.end_time_link = EndTimeLink(self.date_edit, self.time_edit, self.le3, self.length_unit,
										  self.end_date_edit, self.end_time_edit, self._time_unit_hours_index)
		b1_row2.addWidget(self.date_edit)
		b1_row2.addWidget(self.time_edit)
		b1_row2.addWidget(self.end_arrow)
		b1_row2.addWidget(self.end_date_edit)
		b1_row2.addWidget(self.end_time_edit)
		b1_row2.addStretch(1)

		b1_row3 = QHBoxLayout()
		b1_row3.setContentsMargins(0, 0, 0, 0)
		b1_row3.addWidget(self.le3, 1)
		b1_row3.addWidget(self.length_unit)
		b1_row3.addWidget(self.le4, 1)
		b1_row3.addWidget(self.repeat_unit)

		b1_row4 = QHBoxLayout()
		b1_row4.setContentsMargins(0, 0, 0, 0)
		b1_row4.addWidget(self.repeat_until_check)
		b1_row4.addWidget(self.repeat_until_date)
		b1_row4.addStretch(1)

		b1 = QVBoxLayout()
		b1.setContentsMargins(0, 0, 0, 0)
		b1.addLayout(b1_row1)
		b1.addLayout(b1_row2)
		b1.addLayout(b1_row3)
		b1.addLayout(b1_row4)
		t1.setLayout(b1)

		# the block's main action: a glass white capsule in the row of the item box (style book 5.1 / 5.12)
		t1_5 = QWidget()
		btn_t1 = WhiteButton(_tr('Add!'), self)
		btn_t1.clicked.connect(self.add_to_list)
		btn_t1.setShortcut("Ctrl+Return")
		btn_t1.setMinimumWidth(96)
		b1_5 = QHBoxLayout()
		b1_5.setContentsMargins(0, 0, 0, 0)
		b1_5.addWidget(btn_t1)
		t1_5.setLayout(b1_5)
		t1_5.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

		b1_row1.addWidget(t1_5)
		b1.setSpacing(8)
		t1_6 = QWidget()
		b1_6 = QVBoxLayout()
		b1_6.setContentsMargins(0, 0, 0, 0)
		b1_6.addWidget(t1)
		t1_6.setLayout(b1_6)

		t2 = QWidget()
		self.widget0 = compact_dropdown(self)
		self.widget0.setCurrentIndex(0)
		self.widget0.currentIndexChanged.connect(self.index_changed)
		self.widget0.addItems([_tr('All'), _tr('Today'), _tr('To-do'), _tr('Overdue'), _tr('Done')])

		btn_t2 = MacNormalButton(_tr('Delete selected item'), self)
		btn_t2.clicked.connect(self.delete_item)
		btn_t2.setFixedHeight(GREY_ROW_HEIGHT)
		# self.widget0.setFixedWidth(btn_t2.width() * 2)

		btn_t3 = MacNormalButton(_tr('Export plan'), self)
		btn_t3.clicked.connect(self.export_plan)
		btn_t3.setFixedHeight(GREY_ROW_HEIGHT)

		btn_t5 = MacNormalButton(_tr('Export diary'), self)
		btn_t5.clicked.connect(self.export_diary)
		btn_t5.setFixedHeight(GREY_ROW_HEIGHT)

		btn_t6 = MacNormalButton(_tr('Export records'), self)
		btn_t6.clicked.connect(self.export_record)
		btn_t6.setFixedHeight(GREY_ROW_HEIGHT)

		btn_t7 = MacNormalButton(_tr('Delete all DONEs'), self)
		btn_t7.clicked.connect(self.delete_all_dones)
		btn_t7.setFixedHeight(GREY_ROW_HEIGHT)

		self.frame2 = panel_line(self)
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
		self.textw1.setPlaceholderText(_tr('Comments'))

		btn_t4 = WhiteButton(_tr('Save + Done'), self)
		btn_t4.clicked.connect(self.save_and_done)
		btn_t4.setShortcut("Ctrl+Shift+Return")
		b3 = QVBoxLayout()
		b3.setContentsMargins(0, 0, 0, 0)
		b3.setSpacing(6)
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

		# # Setup delegate for keyboard-based editing detection
		# self._table_record_delegate = TableEditDelegate(self.tableWidget_record)
		# self.tableWidget_record.setItemDelegate(self._table_record_delegate)
		# self._table_record_delegate.editing_finished.connect(self._on_record_edit_finished)

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
		t5.setFixedHeight(EDIT_PANEL_COLUMNS_HEIGHT)

		style_table(self.tableWidget)
		style_table(self.tableWidget_record, kind='card')
		self.time_panel = edit_panel(t1_6, t5)
		self.time_stage = self._page_stage(self.word_tab, self.tableWidget, self.time_panel)

	def to_stamp(self, date):
		return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M").timestamp()

	def _time_text_ok(self, text):
		try:
			self.to_stamp(text)
			return True
		except Exception:
			return False

	def write_table_time(self):
		# a time cell that was given something that is not a time ("tomorrow 9"): the old time stays. (Before
		# 2026-11-17 this emptied All.csv down to its header line and stopped the program.)
		if self.changing_bool == 1 and getattr(self, 'changing_column', None) == 1 and 0 <= self.changing_row < self.tableWidget.rowCount():
			edited = self.tableWidget.item(self.changing_row, 1)
			if edited is not None and not self._time_text_ok(edited.text()) and self._time_text_ok(self.changing_date):
				edited.setText(self.changing_date)
		self._repeat_time_scope = self._repeat_time_scope_for_edit() if self.changing_bool == 1 else 'one'
		ori = [['Item', 'Time', 'Length', 'Repeat', 'Status', 'Target times', 'Progress', 'Type', 'Stamp']]
		rownum = int(self.tableWidget.rowCount())
		col = int(self.tableWidget.columnCount())
		for n in range(rownum):
			if self.tableWidget.item(n, 1) != None and self.tableWidget.item(n, 1).text() != '':
				oricon = self.tableWidget.item(n, 1).text()
				if not self._time_text_ok(oricon):      # an unreadable time keeps the stamp it has; the file is still written whole
					continue
				self.tableWidget.setItem(n, 8, QTableWidgetItem(str(self.to_stamp(oricon))))
		if self.widget0.currentIndex() == 2:
			text = 'DONE'  # 筛选 含有 “test” 的所有行
			items = self.tableWidget.findItems(text, Qt.MatchFlag.MatchExactly)
			if items != []:
				for m in range(len(items)):
					item = items[m].row()
					self.tableWidget.setRowHidden(item, True)  # 隐藏对应的行
		with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerows(ori)
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
			# Has repeat - show history records and enable editing
			self.tableWidget_record.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed | QAbstractItemView.EditTrigger.AnyKeyPressed)
			record_file = self._record_file_path(self.tableWidget.item(self.tableWidget.currentRow(), 0).text())
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
		else:
			# No repeat - show placeholder message and disable editing
			self.tableWidget_record.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
			self.tableWidget_record.setColumnCount(1)
			self.tableWidget_record.setRowCount(1)
			self.tableWidget_record.setHorizontalHeaderLabels(['History'])
			self.tableWidget_record.verticalHeader().setVisible(False)
			placeholder_item = QTableWidgetItem('No history records available\n(This item has no repeat)')
			placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
			placeholder_item.setFlags(placeholder_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
			self.tableWidget_record.setItem(0, 0, placeholder_item)
			self.tableWidget_record.setColumnWidth(0, self.tableWidget_record.width())
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
				# Sync changes to all related repeat tasks (if this is a repeat task)
				self._repeat_sync_in_progress = True
				_repeat_sync_done = False
				if hasattr(self, 'changing_repeat') and self.changing_repeat not in ('', '-'):
					self._mark_local_reminder_change()
					# Sync name change (column 0)
					if self.changing_column == 0 and old_text != new_text:
						sync_cmds = self._sync_repeat_task_changes(
							old_text, self.changing_repeat, self.changing_progress,
							new_text, self.changing_repeat)
						for del_rem, del_cal, add_rem, add_cal in sync_cmds:
							self._run_osascript_batch([del_rem, del_cal, add_rem, add_cal])
						_repeat_sync_done = True
					# Sync time change (column 1)
					if self.changing_column == 1:
						new_time = self.tableWidget.item(self.changing_row, 1).text()
						old_stamp_val = self.to_stamp(self.changing_date)
						new_stamp_val = self.to_stamp(new_time)
						if abs(float(new_stamp_val) - float(old_stamp_val)) >= 1 and self._repeat_time_scope == 'later':
							sync_cmds = self._sync_repeat_task_time_changes(
								self.changing_text, self.changing_repeat, self.changing_progress,
								old_stamp_val, new_stamp_val, self.changing_row, after_stamp=float(old_stamp_val))
							for del_rem, del_cal, add_rem, add_cal in sync_cmds:
								self._run_osascript_batch([del_rem, del_cal, add_rem, add_cal])
							_repeat_sync_done = True
					# Sync length change (column 2)
					if self.changing_column == 2:
						new_length = self.tableWidget.item(self.changing_row, 2).text()
						if self.changing_length != new_length:
							sync_cmds = self._sync_repeat_task_length_changes(
								self.changing_text, self.changing_repeat, self.changing_progress,
								new_length, self.changing_row)
							for del_cal, add_cal in sync_cmds:
								self._run_osascript_batch([del_cal, add_cal])
							_repeat_sync_done = True
				if _repeat_sync_done:
					self._write_time_csv_from_table()
				self._repeat_sync_in_progress = False
			if self.changing_column == 3 and hasattr(self, 'changing_repeat'):
				# Sync repeat interval change: delete future UNDONE tasks and regenerate with new interval
				new_repeat = self.tableWidget.item(self.changing_row, 3).text() if self.tableWidget.item(self.changing_row, 3) else '-'
				if self.changing_repeat not in ('', '-') and new_repeat not in ('', '-') and self.changing_repeat != new_repeat:
					self._repeat_sync_in_progress = True
					self._mark_local_reminder_change()
					sync_cmds = self._resync_repeat_interval_change(
						self.changing_text, self.changing_repeat, self.changing_progress,
						new_repeat, self.changing_row)
					if sync_cmds:
						self._run_osascript_batch(sync_cmds)
					self._write_time_csv_from_table()
					self._repeat_sync_in_progress = False
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
				if self.tableWidget.item(self.changing_row, 3).text() != '-' and not self._next_repeat_is_past_until(self.changing_row):
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
					record_file = self._record_file_path(self.tableWidget.item(self.changing_row, 0).text())
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
		repeat_item = self.tableWidget.item(self.changing_row, 3)
		self.changing_repeat = repeat_item.text() if repeat_item else '-'
		progress_item = self.tableWidget.item(self.changing_row, 6)
		self.changing_progress = progress_item.text() if progress_item else '-'
		self.changing_done = self.tableWidget.item(self.changing_row, 4).text()
		if self.changing_done == 'UNDONE':
			self.to_done = 1
		if self.changing_done == 'DONE':
			self.to_done = 2

	def _on_table_edit_started(self, row, column):
		"""Called when a cell in tableWidget starts being edited (keyboard or mouse)"""
		# Same logic as change_write - record original values
		if row < 0 or row >= self.tableWidget.rowCount():
			return
		self.changing_bool = 1
		self.changing_row = row
		self.changing_column = column
		item0 = self.tableWidget.item(row, 0)
		item1 = self.tableWidget.item(row, 1)
		item2 = self.tableWidget.item(row, 2)
		item3 = self.tableWidget.item(row, 3)
		item4 = self.tableWidget.item(row, 4)
		item6 = self.tableWidget.item(row, 6)
		self.changing_text = item0.text() if item0 else ''
		self.changing_date = item1.text() if item1 else ''
		self.changing_length = item2.text() if item2 else ''
		self.changing_repeat = item3.text() if item3 else '-'
		self.changing_progress = item6.text() if item6 else '-'
		self.changing_done = item4.text() if item4 else ''
		if self.changing_done == 'UNDONE':
			self.to_done = 1
		if self.changing_done == 'DONE':
			self.to_done = 2

	def _on_table_edit_finished(self, row, column):
		"""Called when a cell in tableWidget finishes being edited (keyboard or mouse)"""
		# Same logic as write_table_time - save changes
		if self.changing_bool == 1:
			if self._repeat_time_question_rows():
				QTimer.singleShot(0, self._finish_table_edit_later)
				return
			self.write_table_time()

	def _finish_table_edit_later(self, tries=0):
		"""The save of an edit that has a question to ask, one turn after its editor closed. While the table is
		being read in again (its header line is a row for a moment) it waits."""
		if self.changing_bool != 1:
			return
		first = self.tableWidget.item(0, 1) if self.tableWidget.rowCount() else None
		if first is not None and first.text() == 'Time' and tries < 20:
			QTimer.singleShot(150, lambda: self._finish_table_edit_later(tries + 1))
			return
		self.write_table_time()

	def _repeat_later_rows(self, name, repeat, until, stamp, skip_row=None):
		"""The rows of the same repeating item (same name, repeat and repeat-until) that are still to do
		and later than `stamp`."""
		rows = []
		if repeat in ('', '-'):
			return rows
		for row in range(self.tableWidget.rowCount()):
			if row == skip_row:
				continue
			name_item, repeat_item, status_item = self.tableWidget.item(row, 0), self.tableWidget.item(row, 3), self.tableWidget.item(row, 4)
			if name_item is None or repeat_item is None or status_item is None or status_item.text() != 'UNDONE':
				continue
			until_item = self.tableWidget.item(row, 6)
			if name_item.text() != name or repeat_item.text() != repeat or (until_item.text() if until_item else '-') != until:
				continue
			row_stamp = self._stamp_from_items(self.tableWidget.item(row, 8), self.tableWidget.item(row, 1))
			if row_stamp and float(row_stamp) > float(stamp):
				rows.append(row)
		return rows

	def _ask_repeat_scope(self, title, text, name, count):
		"""'one' / 'later' / 'cancel' — the system question for a change to one of a repeating item's rows
		(style book 5.12; Cancel is the default button and Esc)."""
		if getattr(self, '_tool_repeat_scope', None):      # a tool call said which (no question on the screen)
			return self._tool_repeat_scope
		one, later, cancel = _tr('Only this one'), _tr('This and later ones'), _tr('Cancel')
		chosen = tomato_choice(self, title, text.replace('%1', name).replace('%n', str(count)), [one, later, cancel], cancel)
		return 'one' if chosen == one else 'later' if chosen == later else 'cancel'

	def _repeat_time_question_rows(self):
		"""The later rows a time change of the row being edited could take along ([] = nothing to ask)."""
		if self.changing_bool != 1 or getattr(self, 'changing_column', None) != 1:
			return []
		row = self.changing_row
		if not (0 <= row < self.tableWidget.rowCount()):
			return []
		time_item, status_item = self.tableWidget.item(row, 1), self.tableWidget.item(row, 4)
		if time_item is None or status_item is None or status_item.text() != 'UNDONE':
			return []
		try:
			old, new = float(self.to_stamp(self.changing_date)), float(self.to_stamp(time_item.text()))
		except Exception:
			return []
		if abs(new - old) < 1:
			return []
		return self._repeat_later_rows(self.changing_text, getattr(self, 'changing_repeat', '-'), getattr(self, 'changing_progress', '-'), old, row)

	def _repeat_time_scope_for_edit(self):
		"""Asked once, before the edit is written: does a new time move only this row, or the later ones of the
		same repeating item too? Cancel puts the old time back."""
		later = self._repeat_time_question_rows()
		if not later:
			return 'one'
		scope = self._ask_repeat_scope(
			_tr('Change the time'),
			_tr('"%1" repeats, and %n later ones are still to do. Move the later ones by the same amount too?'),
			self.changing_text, len(later))
		if scope == 'cancel':
			item = self.tableWidget.item(self.changing_row, 1)
			if item is not None:
				item.setText(self.changing_date)
			return 'one'
		return scope

	def _next_repeat_is_past_until(self, row):
		"""True when the occurrence after this row would fall after the row's repeat-until."""
		until = self._read_repeat_until_from_row(row)
		if until is None:
			return False
		try:
			return self.to_stamp(self.tableWidget.item(row, 1).text()) + 3600 * float(self.tableWidget.item(row, 3).text()) > until
		except Exception:
			return False

	def _delete_repeat_from(self, row, later_rows):
		"""Deletes this row and the later rows of its repeating item, and ends the repetition there: what is
		left of it gets a repeat-until just before this row, so ticking an earlier one makes no new ones."""
		name = self.tableWidget.item(row, 0).text()
		repeat = self.tableWidget.item(row, 3).text()
		until_item = self.tableWidget.item(row, 6)
		until = until_item.text() if until_item else '-'
		stamp = self._stamp_from_items(self.tableWidget.item(row, 8), self.tableWidget.item(row, 1))
		commands = []
		for gone in sorted([row] + list(later_rows), reverse=True):
			key = (self.tableWidget.item(gone, 0).text(), self._stamp_from_items(self.tableWidget.item(gone, 8), self.tableWidget.item(gone, 1)))
			if key[1]:
				commands += [self._sync_delete_reminder_script(key), self._sync_delete_event_script(key)]
			self.tableWidget.removeRow(gone)
		if stamp:
			for left in range(self.tableWidget.rowCount()):
				name_item, repeat_item, status_item = self.tableWidget.item(left, 0), self.tableWidget.item(left, 3), self.tableWidget.item(left, 4)
				left_until = self.tableWidget.item(left, 6)
				if (name_item is not None and repeat_item is not None and status_item is not None and status_item.text() == 'UNDONE'
						and name_item.text() == name and repeat_item.text() == repeat and (left_until.text() if left_until else '-') == until):
					self._set_time_cell(left, 6, str(int(float(stamp)) - 1))
		self._refresh_stamp_column()
		self._write_time_csv_from_table()
		self._mark_local_reminder_change()
		self._run_osascript_batch(commands)

	def _get_selected_rows(self, table_widget):
		selection = table_widget.selectionModel()
		if selection is None:
			return []
		return sorted({index.row() for index in selection.selectedRows() if index.row() >= 0})

	def _warn_selection_required(self, message):
		tomato_alert(self, _tr('Error'), message)
	
	def _clear_table_selection(self, table_widget):
		if table_widget is None:
			return
		table_widget.clearSelection()
		table_widget.setCurrentItem(None)
		table_widget.clearFocus()

	def _init_sync_indicator(self):
		self._sync_counter = 0
		self._active_workers = []  # Track active AppleScript workers
		self._applescript_signals = AppleScriptWorkerSignals()
		self._applescript_signals.finished.connect(self._on_applescript_finished)
		self.sync_dialog = SyncIndicatorDialog(self)
		self.sync_dialog.setWindowTitle(_tr('Syncing...'))
		self.sync_dialog.setModal(False)
		layout = QVBoxLayout()
		layout.setContentsMargins(20, 15, 20, 15)
		label = QLabel(_tr('Synchronizing with Reminders / Calendar…\nPlease wait for a second.'), self.sync_dialog)
		label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(label)
		self.sync_dialog.setLayout(layout)
		self.sync_dialog.adjustSize()
		self.sync_dialog.hide()
		# changes sent through the system interface are over in hundredths of a second: the notice comes up
		# only when the sending is still going on after a moment (it used to flash up for every change)
		self._sync_dialog_timer = QTimer(self)
		self._sync_dialog_timer.setSingleShot(True)
		self._sync_dialog_timer.setInterval(400)
		self._sync_dialog_timer.timeout.connect(self._show_sync_dialog_now)

	def _show_sync_indicator(self):
		self._sync_counter += 1
		if self._sync_counter == 1:
			# Lock all tables to prevent editing during sync
			self._lock_all_tables()
			self._sync_dialog_timer.start()

	def _show_sync_dialog_now(self):
		if self._sync_counter <= 0:
			return
		parent_geom = self.frameGeometry()
		dialog_size = self.sync_dialog.size()
		target_x = parent_geom.center().x() - dialog_size.width() // 2
		target_y = parent_geom.center().y() - dialog_size.height() // 2
		self.sync_dialog.move(int(target_x), int(target_y))
		self.sync_dialog.show()

	def _hide_sync_indicator(self):
		if self._sync_counter > 0:
			self._sync_counter -= 1
		if self._sync_counter <= 0:
			self._sync_counter = 0
			self._sync_dialog_timer.stop()
			self.sync_dialog.hide()
			# Unlock all tables when sync is complete
			self._unlock_all_tables()

	def _lock_all_tables(self):
		"""Disable editing on all tables during sync operations"""
		tables = [
			('tableWidget', getattr(self, 'tableWidget', None)),
			('tableWidget_freq', getattr(self, 'tableWidget_freq', None)),
			('tableWidget_memo', getattr(self, 'tableWidget_memo', None)),
			('tableWidget_record', getattr(self, 'tableWidget_record', None)),
			('tableWidget_record2', getattr(self, 'tableWidget_record2', None)),
			('tableWidget_collect', getattr(self, 'tableWidget_collect', None)),
		]
		# Store original edit triggers to restore later
		if not hasattr(self, '_original_edit_triggers'):
			self._original_edit_triggers = {}
		for name, table in tables:
			if table is not None:
				self._original_edit_triggers[name] = table.editTriggers()
				table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

	def _unlock_all_tables(self):
		"""Re-enable editing on all tables after sync operations"""
		tables = [
			('tableWidget', getattr(self, 'tableWidget', None)),
			('tableWidget_freq', getattr(self, 'tableWidget_freq', None)),
			('tableWidget_memo', getattr(self, 'tableWidget_memo', None)),
			('tableWidget_record', getattr(self, 'tableWidget_record', None)),
			('tableWidget_record2', getattr(self, 'tableWidget_record2', None)),
			('tableWidget_collect', getattr(self, 'tableWidget_collect', None)),
		]
		if hasattr(self, '_original_edit_triggers'):
			for name, table in tables:
				if table is not None and name in self._original_edit_triggers:
					table.setEditTriggers(self._original_edit_triggers[name])

	def _on_applescript_finished(self):
		"""Called when an AppleScript worker finishes"""
		self._mark_local_reminder_change()
		self._hide_sync_indicator()
		# Clean up finished workers
		self._active_workers = [w for w in self._active_workers if w.is_alive()]

	def _run_osascript_batch(self, script_chunks):
		"""Execute AppleScript commands in a background thread"""
		if not script_chunks:
			return
		self._show_sync_indicator()
		worker = AppleScriptWorker(script_chunks, self._applescript_signals)
		self._active_workers.append(worker)
		worker.start()

	def _mark_local_reminder_change(self):
		self._last_local_reminder_change = time.time()

	def _escape_applescript_string(self, value):
		if value is None:
			return ''
		escaped = value.replace('\\', '\\\\')
		escaped = escaped.replace('"', '\\"')
		return escaped

	def _sanitize_filename(self, name):
		safe = re.sub(r'[\\/]+', '_', name or '')
		safe = re.sub(r'[\\:*?"<>|]', '_', safe)
		safe = safe.strip('.')
		return safe or "record"

	def _record_file_path(self, base_name):
		return os.path.join(self.fulldir_rec, f"{self._sanitize_filename(base_name)}.csv")

	def _write_time_csv_from_table(self):
		if not hasattr(self, 'tableWidget') or self.tableWidget is None:
			logging.warning("_write_time_csv_from_table: tableWidget not available, skipping")
			self._show_safety_notification("_write_time_csv_from_table")
			return
		try:
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
		except Exception as e:
			logging.exception("Error in _write_time_csv_from_table: %s", e)

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

	def _find_related_repeat_tasks(self, task_name, repeat_interval, repeat_until_stamp):
		"""
		Find all rows in the table that are related repeat tasks.
		Related tasks share the same name, repeat interval, and repeat_until_stamp.
		Returns a list of (row_index, stamp) tuples sorted by stamp.
		"""
		related = []
		for row in range(self.tableWidget.rowCount()):
			name_item = self.tableWidget.item(row, 0)
			repeat_item = self.tableWidget.item(row, 3)
			progress_item = self.tableWidget.item(row, 6)
			stamp_item = self.tableWidget.item(row, 8)
			if name_item is None or repeat_item is None:
				continue
			row_name = name_item.text()
			row_repeat = repeat_item.text()
			row_progress = progress_item.text() if progress_item else '-'
			row_stamp = float(stamp_item.text()) if stamp_item and stamp_item.text() else 0
			# Check if this row matches the criteria
			if row_name == task_name and row_repeat == repeat_interval and row_progress == repeat_until_stamp:
				related.append((row, row_stamp))
		# Sort by stamp (chronological order)
		related.sort(key=lambda x: x[1])
		return related

	def _count_future_undone_occurrences(self, task_name, repeat_interval, repeat_until_stamp, current_stamp):
		"""
		Count how many UNDONE occurrences exist in the future (stamp > current_stamp).
		"""
		count = 0
		for row in range(self.tableWidget.rowCount()):
			name_item = self.tableWidget.item(row, 0)
			repeat_item = self.tableWidget.item(row, 3)
			progress_item = self.tableWidget.item(row, 6)
			status_item = self.tableWidget.item(row, 4)
			stamp_item = self.tableWidget.item(row, 8)
			if name_item is None or repeat_item is None or status_item is None:
				continue
			row_name = name_item.text()
			row_repeat = repeat_item.text()
			row_progress = progress_item.text() if progress_item else '-'
			row_status = status_item.text()
			row_stamp = float(stamp_item.text()) if stamp_item and stamp_item.text() else 0
			if (row_name == task_name and row_repeat == repeat_interval and
				row_progress == repeat_until_stamp and row_status == 'UNDONE' and
				row_stamp > current_stamp):
				count += 1
		return count

	def _get_latest_stamp_for_repeat(self, task_name, repeat_interval, repeat_until_stamp):
		"""
		Get the latest (highest) stamp among all related repeat tasks.
		"""
		latest_stamp = 0
		for row in range(self.tableWidget.rowCount()):
			name_item = self.tableWidget.item(row, 0)
			repeat_item = self.tableWidget.item(row, 3)
			progress_item = self.tableWidget.item(row, 6)
			stamp_item = self.tableWidget.item(row, 8)
			if name_item is None or repeat_item is None:
				continue
			row_name = name_item.text()
			row_repeat = repeat_item.text()
			row_progress = progress_item.text() if progress_item else '-'
			row_stamp = float(stamp_item.text()) if stamp_item and stamp_item.text() else 0
			if row_name == task_name and row_repeat == repeat_interval and row_progress == repeat_until_stamp:
				if row_stamp > latest_stamp:
					latest_stamp = row_stamp
		return latest_stamp

	def _generate_repeat_occurrences(self, base_values, count, start_stamp, repeat_hours, repeat_end_stamp):
		"""
		Generate up to 'count' new repeat occurrences starting from start_stamp.
		Returns list of (row_values, reminder_cmd, calendar_cmd) tuples.
		"""
		occurrences = []
		current_stamp = start_stamp
		for _ in range(count):
			new_stamp = current_stamp + 3600 * repeat_hours
			# Check if we've exceeded the repeat_until limit
			if repeat_end_stamp is not None and new_stamp > repeat_end_stamp:
				break
			# Check if this stamp already exists in the table
			next_time_array = time.localtime(new_stamp)
			new_time = time.strftime("%Y-%m-%d %H:%M", next_time_array)
			otherStyleTime = time.strftime("%m/%d/%Y %H:%M", next_time_array)
			new_row_values = [
				base_values[0],  # Item name
				new_time,        # Time
				base_values[2],  # Length
				base_values[3],  # Repeat
				'UNDONE',        # Status
				'-',             # Target times
				base_values[6],  # Progress (repeat_until_stamp)
				'TIME_SNS',      # Type
				str(new_stamp)   # Stamp
			]
			if not self._table_contains_row(self.tableWidget, new_row_values):
				escaped_text = self._escape_applescript_string(base_values[0])
				reminder_cmd = """tell application "Reminders"
	set eachLine to "%s"
	set mylist to list "Tomato"
	tell mylist
		make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
	end tell
end tell""" % (escaped_text, otherStyleTime)
				calendar_cmd = """tell application "Calendar"
  tell calendar "Tomato"
	make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
  end tell
end tell""" % (escaped_text, otherStyleTime, otherStyleTime, base_values[2])
				occurrences.append((new_row_values, reminder_cmd, calendar_cmd))
			current_stamp = new_stamp
		return occurrences

	def _sync_repeat_task_changes(self, old_name, old_repeat, repeat_until_stamp, new_name, new_repeat):
		"""
		When name or repeat interval changes, update all related UNDONE tasks.
		Returns list of (reminder_cmd, calendar_cmd) tuples for updates.
		"""
		commands = []
		for row in range(self.tableWidget.rowCount()):
			name_item = self.tableWidget.item(row, 0)
			repeat_item = self.tableWidget.item(row, 3)
			progress_item = self.tableWidget.item(row, 6)
			status_item = self.tableWidget.item(row, 4)
			time_item = self.tableWidget.item(row, 1)
			length_item = self.tableWidget.item(row, 2)
			if name_item is None or repeat_item is None or status_item is None:
				continue
			row_name = name_item.text()
			row_repeat = repeat_item.text()
			row_progress = progress_item.text() if progress_item else '-'
			row_status = status_item.text()
			# Only update UNDONE tasks that match the old criteria
			if (row_name == old_name and row_repeat == old_repeat and
				row_progress == repeat_until_stamp and row_status == 'UNDONE'):
				old_time = time_item.text() if time_item else ''
				old_length = length_item.text() if length_item else '1'
				if old_time:
					# Delete old reminder and calendar event
					stamp_item = self.to_stamp(old_time)
					timeArray = time.localtime(float(stamp_item))
					otherStyleTime = time.strftime("%m/%d/%Y %H:%M", timeArray)
					escaped_old = self._escape_applescript_string(old_name)
					escaped_new = self._escape_applescript_string(new_name)
					# Delete old
					del_reminder = """tell application "Reminders"
	set mylist to list "Tomato"
	tell mylist
		delete (reminders whose (name is "%s") and (remind me date is date "%s"))
	end tell
end tell""" % (escaped_old, otherStyleTime)
					del_calendar = """tell application "Calendar"
	tell calendar "Tomato"
		delete (events whose (start date is date "%s") and (summary is "%s"))
	end tell
end tell""" % (otherStyleTime, escaped_old)
					# Create new
					add_reminder = """tell application "Reminders"
	set eachLine to "%s"
	set mylist to list "Tomato"
	tell mylist
		make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
	end tell
end tell""" % (escaped_new, otherStyleTime)
					add_calendar = """tell application "Calendar"
  tell calendar "Tomato"
	make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
  end tell
end tell""" % (escaped_new, otherStyleTime, otherStyleTime, old_length)
					commands.append((del_reminder, del_calendar, add_reminder, add_calendar))
				# Update the table
				name_item.setText(new_name)
				repeat_item.setText(new_repeat)
		return commands

	def _sync_repeat_task_time_changes(self, task_name, repeat_interval, repeat_until_stamp, old_stamp, new_stamp, current_row, after_stamp=None):
		"""
		When time changes on a repeat task, shift the UNDONE related tasks by the same delta
		(after_stamp: only the ones later than that time).
		Returns list of (del_reminder, del_calendar, add_reminder, add_calendar) tuples.
		"""
		delta = float(new_stamp) - float(old_stamp)
		if abs(delta) < 1:
			return []
		commands = []
		for row in range(self.tableWidget.rowCount()):
			if row == current_row:
				continue
			name_item = self.tableWidget.item(row, 0)
			time_item = self.tableWidget.item(row, 1)
			length_item = self.tableWidget.item(row, 2)
			repeat_item = self.tableWidget.item(row, 3)
			status_item = self.tableWidget.item(row, 4)
			progress_item = self.tableWidget.item(row, 6)
			stamp_item = self.tableWidget.item(row, 8)
			if name_item is None or repeat_item is None or status_item is None or time_item is None or stamp_item is None:
				continue
			row_name = name_item.text()
			row_repeat = repeat_item.text()
			row_progress = progress_item.text() if progress_item else '-'
			row_status = status_item.text()
			row_stamp = float(stamp_item.text()) if stamp_item.text() else 0
			row_length = length_item.text() if length_item else '1'
			if after_stamp is not None and row_stamp <= after_stamp:
				continue
			if (row_name == task_name and row_repeat == repeat_interval and
				row_progress == repeat_until_stamp and row_status == 'UNDONE'):
				old_time_array = time.localtime(row_stamp)
				old_other_style = time.strftime("%m/%d/%Y %H:%M", old_time_array)
				escaped_name = self._escape_applescript_string(task_name)
				del_reminder = """tell application "Reminders"
	set mylist to list "Tomato"
	tell mylist
		delete (reminders whose (name is "%s") and (remind me date is date "%s"))
	end tell
end tell""" % (escaped_name, old_other_style)
				del_calendar = """tell application "Calendar"
	tell calendar "Tomato"
		delete (events whose (start date is date "%s") and (summary is "%s"))
	end tell
end tell""" % (old_other_style, escaped_name)
				new_row_stamp = row_stamp + delta
				new_time_array = time.localtime(new_row_stamp)
				new_time_str = time.strftime("%Y-%m-%d %H:%M", new_time_array)
				new_other_style = time.strftime("%m/%d/%Y %H:%M", new_time_array)
				add_reminder = """tell application "Reminders"
	set eachLine to "%s"
	set mylist to list "Tomato"
	tell mylist
		make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
	end tell
end tell""" % (escaped_name, new_other_style)
				add_calendar = """tell application "Calendar"
  tell calendar "Tomato"
	make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
  end tell
end tell""" % (escaped_name, new_other_style, new_other_style, row_length)
				commands.append((del_reminder, del_calendar, add_reminder, add_calendar))
				time_item.setText(new_time_str)
				stamp_item.setText(str(new_row_stamp))
		return commands

	def _sync_repeat_task_length_changes(self, task_name, repeat_interval, repeat_until_stamp, new_length, current_row):
		"""
		When length changes on a repeat task, update length on all future UNDONE related tasks.
		Returns list of (del_calendar, add_calendar) tuples (reminders have no duration).
		"""
		commands = []
		for row in range(self.tableWidget.rowCount()):
			if row == current_row:
				continue
			name_item = self.tableWidget.item(row, 0)
			time_item = self.tableWidget.item(row, 1)
			length_item = self.tableWidget.item(row, 2)
			repeat_item = self.tableWidget.item(row, 3)
			status_item = self.tableWidget.item(row, 4)
			progress_item = self.tableWidget.item(row, 6)
			if name_item is None or repeat_item is None or status_item is None or length_item is None:
				continue
			row_name = name_item.text()
			row_repeat = repeat_item.text()
			row_progress = progress_item.text() if progress_item else '-'
			row_status = status_item.text()
			row_time = time_item.text() if time_item else ''
			if (row_name == task_name and row_repeat == repeat_interval and
				row_progress == repeat_until_stamp and row_status == 'UNDONE'):
				old_length = length_item.text()
				if old_length == new_length:
					continue
				if row_time:
					stamp_val = self.to_stamp(row_time)
					time_array = time.localtime(float(stamp_val))
					other_style_time = time.strftime("%m/%d/%Y %H:%M", time_array)
					escaped_name = self._escape_applescript_string(task_name)
					del_calendar = """tell application "Calendar"
	tell calendar "Tomato"
		delete (events whose (start date is date "%s") and (summary is "%s"))
	end tell
end tell""" % (other_style_time, escaped_name)
					add_calendar = """tell application "Calendar"
  tell calendar "Tomato"
	make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
  end tell
end tell""" % (escaped_name, other_style_time, other_style_time, new_length)
					commands.append((del_calendar, add_calendar))
				length_item.setText(new_length)
		return commands

	def _resync_repeat_interval_change(self, task_name, old_repeat, repeat_until_stamp, new_repeat, current_row):
		"""
		When repeat interval changes, delete all future UNDONE occurrences and regenerate them
		with the new interval from the edited task's time.
		Returns a flat list of AppleScript commands: all deletes first, then all creates.
		This ensures sequential execution in a single osascript call to avoid
		race conditions between delete and create operations for overlapping times.
		"""
		delete_commands = []
		create_commands = []
		# Step 1: Delete all future UNDONE related tasks (matching old criteria)
		rows_to_delete = []
		for row in range(self.tableWidget.rowCount()):
			if row == current_row:
				continue
			name_item = self.tableWidget.item(row, 0)
			repeat_item = self.tableWidget.item(row, 3)
			status_item = self.tableWidget.item(row, 4)
			progress_item = self.tableWidget.item(row, 6)
			time_item = self.tableWidget.item(row, 1)
			if name_item is None or repeat_item is None or status_item is None:
				continue
			row_name = name_item.text()
			row_repeat = repeat_item.text()
			row_progress = progress_item.text() if progress_item else '-'
			row_status = status_item.text()
			if (row_name == task_name and row_repeat == old_repeat and
				row_progress == repeat_until_stamp and row_status == 'UNDONE'):
				row_time = time_item.text() if time_item else ''
				if row_time:
					stamp_val = self.to_stamp(row_time)
					time_array = time.localtime(float(stamp_val))
					other_style = time.strftime("%m/%d/%Y %H:%M", time_array)
					escaped_name = self._escape_applescript_string(task_name)
					del_rem = """tell application "Reminders"
	set mylist to list "Tomato"
	tell mylist
		delete (reminders whose (name is "%s") and (remind me date is date "%s"))
	end tell
end tell""" % (escaped_name, other_style)
					del_cal = """tell application "Calendar"
	tell calendar "Tomato"
		delete (events whose (start date is date "%s") and (summary is "%s"))
	end tell
end tell""" % (other_style, escaped_name)
					delete_commands.append(del_rem)
					delete_commands.append(del_cal)
				rows_to_delete.append(row)
		# Delete rows from table (in reverse order to preserve indices)
		for row in sorted(rows_to_delete, reverse=True):
			self.tableWidget.removeRow(row)
		# Step 2: Regenerate future occurrences with new interval
		# Find the edited row again (its index may have changed after deletions)
		edited_row = -1
		for row in range(self.tableWidget.rowCount()):
			name_item = self.tableWidget.item(row, 0)
			repeat_item = self.tableWidget.item(row, 3)
			progress_item = self.tableWidget.item(row, 6)
			stamp_item = self.tableWidget.item(row, 8)
			if name_item is None or repeat_item is None:
				continue
			if (name_item.text() == task_name and repeat_item.text() == new_repeat and
				(progress_item.text() if progress_item else '-') == repeat_until_stamp):
				edited_row = row
				break
		if edited_row >= 0:
			try:
				new_repeat_hours = float(new_repeat)
			except (ValueError, TypeError):
				return delete_commands + create_commands
			stamp_item = self.tableWidget.item(edited_row, 8)
			length_item = self.tableWidget.item(edited_row, 2)
			base_stamp = float(stamp_item.text()) if stamp_item and stamp_item.text() else 0
			base_length = length_item.text() if length_item else '1'
			repeat_end_stamp = None
			if repeat_until_stamp not in ('-', ''):
				try:
					repeat_end_stamp = float(repeat_until_stamp)
				except (ValueError, TypeError):
					pass
			base_values = [task_name, '', base_length, new_repeat, 'UNDONE', '-', repeat_until_stamp, 'TIME_SNS', '']
			pregenerate_count = self._get_repeat_pregenerate_count()
			# Count existing UNDONE occurrences (including the edited row)
			existing_undone = 0
			for row in range(self.tableWidget.rowCount()):
				ni = self.tableWidget.item(row, 0)
				ri = self.tableWidget.item(row, 3)
				pi = self.tableWidget.item(row, 6)
				si = self.tableWidget.item(row, 4)
				if ni and ri and si:
					if (ni.text() == task_name and ri.text() == new_repeat and
						(pi.text() if pi else '-') == repeat_until_stamp and si.text() == 'UNDONE'):
						existing_undone += 1
			needed = max(0, pregenerate_count - existing_undone)
			if needed > 0:
				occurrences = self._generate_repeat_occurrences(
					base_values, needed, base_stamp, new_repeat_hours, repeat_end_stamp)
				for row_values, reminder_cmd, calendar_cmd in occurrences:
					self._append_time_row_to_table(row_values)
					create_commands.append(reminder_cmd)
					create_commands.append(calendar_cmd)
		return delete_commands + create_commands

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

	def _broccoli_entries(self):
		return [(key[0], key[1], info.get('status')) for key, info in self._collect_time_entries().items()]

	def _broccoli_complete_row(self, name, stamp):
		"""The row of a question that was just sent to Broccoli is ticked off the way Save does it (a repeating
		item gets its next occurrence from that). False = not now, the scheduler asks again in a few seconds."""
		if getattr(self, '_sync_counter', 0) > 0 or getattr(self, '_repeat_sync_in_progress', False):
			return False
		focused = QApplication.focusWidget()
		if focused is not None and focused is not self.tableWidget and self.tableWidget.isAncestorOf(focused):
			return False   # a cell is being edited
		row = self._find_time_row_by_key(name, stamp)
		if row is None:
			return True   # deleted meanwhile
		reminder_cmds, calendar_cmds, done = self._complete_time_row(row, _tr('Sent to Broccoli'))
		if done:
			self._refresh_stamp_column()
			self._write_time_csv_from_table()
			with contextlib.suppress(Exception):
				self.tableWidget.sortByColumn(8, Qt.SortOrder.AscendingOrder)
		self._run_osascript_batch(reminder_cmds + calendar_cmds)
		self.tableWidget.clearSelection()
		self.tableWidget.setCurrentItem(None)
		return True

	def _broccoli_busy(self):
		if getattr(self, '_sync_counter', 0) > 0 or getattr(self, '_repeat_sync_in_progress', False):
			return True
		focused = QApplication.focusWidget()
		return focused is not None and focused is not self.tableWidget and self.tableWidget.isAncestorOf(focused)

	def _broccoli_item_name(self, task):
		return tomato_broccoli.MARKER + ' ' + task

	def _broccoli_task_rows(self, task, undone_only=True):
		"""Table rows of the timed items that name this task."""
		wanted = self._broccoli_item_name(task).casefold()
		rows = []
		for row in range(self.tableWidget.rowCount()):
			type_item, name_item, status_item = self.tableWidget.item(row, 7), self.tableWidget.item(row, 0), self.tableWidget.item(row, 4)
			if type_item is None or type_item.text() != 'TIME_SNS' or name_item is None:
				continue
			if ' '.join(name_item.text().split()).casefold() != wanted:
				continue
			if undone_only and (status_item is None or status_item.text() != 'UNDONE'):
				continue
			rows.append(row)
		return rows

	def _broccoli_after_table_change(self, commands):
		self._refresh_stamp_column()
		self._write_time_csv_from_table()
		with contextlib.suppress(Exception):
			self.tableWidget.sortByColumn(8, Qt.SortOrder.AscendingOrder)
		self._mark_local_reminder_change()
		self._run_osascript_batch(commands)

	def _broccoli_add_rows(self, task, schedule):
		"""A task folder asked for its rows (tomato_broccoli.TaskSync): the first one and, for a repeating task, the
		next ones as Add makes them. False = the table is busy, asked again in a few seconds."""
		if self._broccoli_busy():
			return False
		name = self._broccoli_item_name(task)
		start = int(schedule['start'])
		length = self._format_hours(float(schedule.get('length_hours') or 1.0))
		repeat_hours = schedule.get('repeat_hours')
		repeat = self._format_hours(float(repeat_hours)) if repeat_hours else '-'
		until = schedule.get('repeat_until')
		until_text = str(int(until)) if until else '-'
		commands = []
		first = [name, time.strftime("%Y-%m-%d %H:%M", time.localtime(start)), length, repeat, 'UNDONE', '-', until_text, 'TIME_SNS', str(start)]
		if self._find_time_row_by_key(name, start) is None:
			self._append_time_row_to_table(first)
			commands += [self._sync_make_reminder_script((name, start)), self._sync_make_event_script((name, start))]
		if repeat_hours:
			base_values = [name, '', length, repeat, 'UNDONE', '-', until_text, 'TIME_SNS', '']
			for row_values, reminder_cmd, calendar_cmd in self._generate_repeat_occurrences(
					base_values, self._get_repeat_pregenerate_count() - 1, float(start), float(repeat_hours), float(until) if until else None):
				self._append_time_row_to_table(row_values)
				commands += [reminder_cmd, calendar_cmd]
		self._broccoli_after_table_change(commands)
		return True

	def _broccoli_remove_rows(self, task):
		"""The undone rows of a task leave the table (its folder is gone, or its schedule was rewritten)."""
		if self._broccoli_busy():
			return False
		commands = []
		for row in reversed(self._broccoli_task_rows(task)):
			key = (self.tableWidget.item(row, 0).text(), self._stamp_from_items(self.tableWidget.item(row, 8), self.tableWidget.item(row, 1)))
			if key[1]:
				commands += [self._sync_delete_reminder_script(key), self._sync_delete_event_script(key)]
			self.tableWidget.removeRow(row)
		if commands:
			self._broccoli_after_table_change(commands)
		return True

	def _broccoli_tasks_changed(self):
		self.broccoli_scheduler.tasks_changed()
		if self._broccoli_manager is not None and self._broccoli_manager.isVisible():
			self._broccoli_manager.refresh()

	def _broccoli_begin_task(self, item_name, stamp_text, length_hours, repeat_hours, until_text):
		"""Add was clicked on "@Broccoli <a new task's name>" (chosen as "New task" in the @ list): the time is kept as
		a draft in the task's folder and the instructions are asked for. The rows come when the instructions are saved.
		True = handled here, Add does nothing more."""
		target = tomato_broccoli.prompt_of(item_name)
		if target is None or not self.broccoli_suggest.is_new_task() or self.broccoli_store.find(target) is not None:
			return False
		name = tomato_broccoli.valid_task_name(target)
		if name is None:
			tomato_alert(self, _tr('New task'), _tr('Use a name that is not taken, without / \\ : and at most 80 characters.'))
			return True
		def number(value):
			try:
				return float(value)
			except (TypeError, ValueError):
				return None
		try:
			self.broccoli_store.write_schedule(name, int(float(stamp_text)), number(length_hours) or 1.0, number(repeat_hours), number(until_text))
			self.broccoli_store.write_manifest()
		except Exception:
			logging.exception("Could not write the task's folder")
			tomato_alert(self, _tr('New task'), _tr('The task folder could not be written.'))
			return True
		self.le1.clear()
		self.le3.clear()
		self.le4.clear()
		self.repeat_until_check.setChecked(False)
		self.broccoli_tasks.look()
		if tomato_broccoli.broccoli_installed():
			# the instructions are worked out with Broccoli (its "tomato-schedule" skill); the rows come when it saves task.md
			tomato_broccoli.install_skill()
			self.broccoli_discussion.start(name, self.broccoli_store.read_schedule(name))
		else:
			# no Broccoli: first its download is offered (Ryan 2026-11-21: "先推荐下载"), then the instructions are
			# written by hand as before (the task runs once Broccoli is there)
			download, by_hand = _tr('Download Broccoli…'), _tr('Write by Hand')
			if tomato_choice(self, _tr('Broccoli is not on this Mac'),
							 _tr('Tasks are carried out by Broccoli, an AI assistant app for Mac. Download it and open it once; '
								 'until then, write what this task should do by hand.'),
							 [by_hand, download], download) == download:
				threading.Thread(target=tomato_broccoli.open_download_page, daemon=True).start()
			self.edit_broccoli_task(name)
		return True

	def _broccoli_discussion_finished(self, name, ok, reason):
		if ok:
			tomato_broccoli.activate_broccoli()
			self._broccoli_notice('discuss_started', name)
		else:
			logging.warning('Broccoli: the draft "%s" could not be handed over: %s', name, reason)
			self._broccoli_notice('discuss_failed', name)
			self.edit_broccoli_task(name)

	def edit_broccoli_task(self, name):
		"""The window in which the instructions of one task are written by hand."""
		text, _error = self.broccoli_store.read_spec(name)
		dialog = tomato_broccoli_ui.TaskEditorDialog(name, text or '', None)
		dialog.saved.connect(self._broccoli_save_instructions)
		dialog.finished.connect(lambda _result, d=dialog: self._broccoli_editors.remove(d) if d in self._broccoli_editors else None)
		self._broccoli_editors.append(dialog)
		dialog.show()
		return dialog

	def _broccoli_save_instructions(self, name, text):
		try:
			self.broccoli_store.write_spec(name, text)
		except Exception:
			logging.exception("Could not write the task's instructions")
			tomato_alert(self, _tr('Instructions for Broccoli'), _tr('This file cannot be saved.'))
			return
		self.broccoli_tasks.look()

	def open_broccoli_tasks(self):
		if self._broccoli_manager is None:
			self._broccoli_manager = tomato_broccoli_ui.TaskManagerDialog(self.broccoli_store, self, None)
		self._broccoli_manager.refresh()
		self._broccoli_manager.show()
		self._broccoli_manager.raise_()
		return self._broccoli_manager

	# what the manager window asks of the table
	def task_info(self, task):
		stamps = []
		for row in self._broccoli_task_rows(task):
			stamp = self._stamp_from_items(self.tableWidget.item(row, 8), self.tableWidget.item(row, 1))
			if stamp:
				stamps.append(int(stamp))
		return (min(stamps) if stamps else None), len(stamps)

	def format_time(self, stamp):
		return time.strftime("%Y-%m-%d %H:%M", time.localtime(int(stamp)))

	def rename_task(self, old, new):
		if self._broccoli_busy() or not self.broccoli_store.rename(old, new):
			return False
		commands = []
		new_name = self._broccoli_item_name(new)
		for row in self._broccoli_task_rows(old):
			stamp = self._stamp_from_items(self.tableWidget.item(row, 8), self.tableWidget.item(row, 1))
			old_key = (self.tableWidget.item(row, 0).text(), stamp)
			self._set_time_cell(row, 0, new_name)
			if stamp:
				commands += [self._sync_delete_reminder_script(old_key), self._sync_delete_event_script(old_key),
							 self._sync_make_reminder_script((new_name, stamp)), self._sync_make_event_script((new_name, stamp))]
		self.broccoli_tasks.forget(old, renamed_to=new)
		if commands:
			self._broccoli_after_table_change(commands)
		self.broccoli_tasks.look()
		return True

	def delete_task(self, task):
		if self._broccoli_remove_rows(task) is False:
			return False
		self.broccoli_tasks.forget(task)
		deleted = self.broccoli_store.delete(task)
		self.broccoli_tasks.look()
		return deleted

	def _broccoli_notice(self, kind, name):
		if kind == 'discuss_started':
			message = _tr('Broccoli has opened a conversation for this task. Tell it what the task should do; the task appears here once Broccoli saves it:')
		elif kind == 'discuss_failed':
			message = _tr('Broccoli could not be reached, so write the instructions here:')
		elif kind.startswith('task_file'):
			message = {
				'task_file_too_big': _tr('The instructions of this task are too large to send, so it was not sent to Broccoli:'),
				'task_file_empty': _tr('This task has no instructions yet, so it was not sent to Broccoli:'),
				'task_file_missing': _tr('This task has no instructions yet, so it was not sent to Broccoli:'),
			}.get(kind, _tr('The instructions of this task cannot be read, so it was not sent to Broccoli:'))
		elif kind == 'missed':
			message = _tr('Its time passed more than a day ago, so it was not sent to Broccoli:')
		elif kind == 'not_installed':
			message = _tr('Broccoli was not found on this Mac. Tomato will try again in 5 minutes:')
		else:
			message = _tr('Broccoli did not answer. Tomato will try again in 5 minutes:')
		if kind == 'not_installed':     # first its download is offered (Ryan 2026-11-21: "先推荐下载")
			notification = AutoCloseNotification(_tr('Send to Broccoli'), message + "\n\n" + name, auto_close_seconds=20,
												 action=(_tr('Download Broccoli…'), lambda: threading.Thread(
													 target=tomato_broccoli.open_download_page, daemon=True).start()))
		else:
			notification = AutoCloseNotification(_tr('Send to Broccoli'), message + "\n\n" + name, auto_close_seconds=8)
		self._broccoli_notification = notification   # keep it alive while it is on screen
		notification.show()

	def _start_system_sync_worker(self):
		if self.system_sync_thread and self.system_sync_thread.is_alive():
			return
		try:
			if not hasattr(self, '_system_sync_signals'):
				self._system_sync_signals = SystemSyncSignals()
				self._system_sync_signals.ready.connect(self._process_sync_messages)
			self.system_sync_thread = SystemSyncThread(self.system_sync_queue, on_reading=self._system_sync_signals.ready.emit)
			self.system_sync_thread.start()
			# the system tells when reminders / events changed: read a moment later instead of waiting for the next timed pass
			tomato_eventkit.STORE.watch(self._system_store_changed)
		except Exception:
			logging.exception("Failed to start the Reminders / Calendar sync thread.")
			self.system_sync_thread = None
			if self.reminder_sync_timer.isActive():
				self.reminder_sync_timer.stop()

	def _system_store_changed(self):
		thread = self.system_sync_thread
		if thread is not None:
			thread.note_change()

	def _time_cell_being_edited(self):
		"""A cell of the main table is open for typing: the table must not be moved or sorted under it. The
		quick-edit card counts too (its Save looks the row up again)."""
		if self._quick_edit_open():
			return True
		focused = QApplication.focusWidget()
		if focused is not None and focused is not self.tableWidget and self.tableWidget.isAncestorOf(focused):
			return True
		delegate = getattr(self, '_table_delegate', None)
		if delegate is not None and getattr(delegate, '_current_edit_index', None) is not None:
			viewport = self.tableWidget.viewport()
			return any(child.isVisible() for child in viewport.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly))
		return False

	def _process_sync_messages(self):
		if self._sync_processing:
			return
		self._sync_processing = True
		try:
			self._drain_system_sync_queue()
		except Exception as e:
			# Catch all exceptions to prevent PyQt6 abort() crash
			# Skip this round and try again next time
			logging.exception("Error in _process_sync_messages, skipping this round: %s", e)
		finally:
			self._sync_processing = False

	def _drain_system_sync_queue(self):
		if getattr(self, '_sync_counter', 0) > 0:
			return   # Tomato's own commands are still running: what was read is looked at afterwards
		if getattr(self, '_repeat_sync_in_progress', False):
			return
		if self._time_cell_being_edited():
			return   # looked at again in a few seconds; what the edit then sends out makes this reading an old one
		message = None
		while True:
			try:
				latest = self.system_sync_queue.get_nowait()
			except queue.Empty:
				break
			if isinstance(latest, dict):
				message = latest   # only the newest reading counts
		if message is None:
			return
		if float(message.get('timestamp') or 0.0) < getattr(self, '_last_local_reminder_change', 0.0):
			# read before Tomato's own last change went out: it would look like "changed over there".
			# Read again now (it used to wait for the next two-minute poll).
			if self.system_sync_thread:
				self.system_sync_thread.request()
			return
		self._handle_system_snapshot(message)

	def _sync_base_path(self):
		return os.path.join(os.path.dirname(self.fulldirall), 'sync_base.json')

	def _handle_system_snapshot(self, message):
		"""One joint decision for the table, the Reminders list and the Calendar (tomato_sync.reconcile)."""
		if not hasattr(self, 'tableWidget') or self.tableWidget is None:
			logging.warning("_handle_system_snapshot: tableWidget not available, skipping")
			self._show_safety_notification("_handle_system_snapshot")
			return
		try:
			reminders = tomato_sync.snapshot_map(message.get('reminders'))
			calendar = tomato_sync.snapshot_map(message.get('calendar'))
			if reminders is None:
				return
			local = {(key[0].strip(), key[1]): info.get('status') for key, info in self._collect_time_entries().items()}
			base_path = self._sync_base_path()
			stamp = int(float(message.get('timestamp') or time.time()))
			# what the Reminders read covers (30 days back, a year ahead), a day in from both ends
			window = (stamp - 29 * 86400, stamp + 364 * 86400)
			actions, new_base = tomato_sync.reconcile(local, reminders, calendar, tomato_sync.load_base(base_path), window, message.get('event_window'))
			if actions is None:
				logging.warning("System sync: this pass would delete most of the table (%d rows, %d reminders, %s events); nothing was changed.",
								len(local), len(reminders), 'no' if calendar is None else len(calendar))
				return
			commands = []
			table_changed = False
			for action in actions:
				commands.extend(self._apply_sync_action(action))
				if action[0] in ('move_row', 'add_row', 'delete_row', 'complete_row', 'reopen_row'):
					table_changed = True
			tomato_sync.save_base(base_path, new_base)
			if actions:
				logging.info("System sync: %s", ', '.join('%s %s' % (a[0], a[1][0]) for a in actions[:12]))
			if table_changed:
				self._refresh_stamp_column()
				self._write_time_csv_from_table()
				with contextlib.suppress(Exception):
					self.tableWidget.sortByColumn(8, Qt.SortOrder.AscendingOrder)
			if commands:
				self._run_osascript_batch(commands)
		except Exception as e:
			logging.exception("Error in _handle_system_snapshot: %s", e)

	def _set_time_cell(self, row, column, text):
		item = QTableWidgetItem(str(text))
		item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
		self.tableWidget.setItem(row, column, item)

	def _sync_script_time(self, stamp):
		return time.strftime("%m/%d/%Y %H:%M", time.localtime(int(stamp)))

	def _sync_row_hours(self, key):
		row = self._find_time_row_by_key(*key)
		item = self.tableWidget.item(row, 2) if row is not None else None
		try:
			hours = float(item.text()) if item is not None else 1.0
		except ValueError:
			hours = 1.0
		return self._format_hours(hours) if hours > 0 else '1'

	def _sync_make_reminder_script(self, key):
		return """tell application "Reminders"
	set eachLine to "%s"
	set mylist to list "Tomato"
	tell mylist
		make new reminder at end with properties {name:eachLine, remind me date:date "%s"}
	end tell
end tell""" % (self._escape_applescript_string(key[0]), self._sync_script_time(key[1]))

	def _sync_delete_reminder_script(self, key):
		return """tell application "Reminders"
	set mylist to list "Tomato"
	tell mylist
		delete (reminders whose (name is "%s") and (remind me date is date "%s"))
	end tell
end tell""" % (self._escape_applescript_string(key[0]), self._sync_script_time(key[1]))

	def _sync_make_event_script(self, key):
		when = self._sync_script_time(key[1])
		return """tell application "Calendar"
	tell calendar "Tomato"
		make new event at end with properties {summary:"%s", start date:date "%s", end date:date "%s" + (%s * hours)}
	end tell
end tell""" % (self._escape_applescript_string(key[0]), when, when, self._sync_row_hours(key))

	def _sync_delete_event_script(self, key):
		return """tell application "Calendar"
	tell calendar "Tomato"
		delete (events whose (start date is date "%s") and (summary is "%s"))
	end tell
end tell""" % (self._sync_script_time(key[1]), self._escape_applescript_string(key[0]))

	def _apply_sync_action(self, action):
		"""Carry out one action of tomato_sync.reconcile on the table; returns the AppleScript commands
		for Reminders / Calendar it needs."""
		kind = action[0]
		if kind == 'move_row':
			_, old, new, duration = action
			row = self._find_time_row_by_key(*old)
			if row is None:
				return []
			self._set_time_cell(row, 0, new[0])
			self._set_time_cell(row, 1, datetime.datetime.fromtimestamp(int(new[1])).strftime("%Y-%m-%d %H:%M"))
			self._set_time_cell(row, 8, new[1])
			if duration:
				self._set_time_cell(row, 2, self._format_hours(round(duration / 3600, 6)))
			return []
		if kind == 'add_row':
			_, key, duration = action
			length = self._format_hours(round(duration / 3600, 6)) if duration else '1'
			when = datetime.datetime.fromtimestamp(int(key[1])).strftime("%Y-%m-%d %H:%M")
			self._append_time_row_to_table([key[0], when, length, '-', 'UNDONE', '-', '-', 'TIME_SNS', key[1]])
			return []
		if kind == 'delete_row':
			row = self._find_time_row_by_key(*action[1])
			if row is not None:
				self.tableWidget.removeRow(row)
			return []
		if kind == 'complete_row':
			row = self._find_time_row_by_key(*action[1])
			if row is None:
				return []
			reminder_cmds, calendar_cmds, _done = self._complete_time_row(row, '')
			return reminder_cmds + calendar_cmds
		if kind == 'reopen_row':
			return self._reopen_time_row(action[1], action[2])
		if kind == 'make_reminder':
			return [self._sync_make_reminder_script(action[1])]
		if kind == 'delete_reminder':
			return [self._sync_delete_reminder_script(action[1])]
		if kind == 'move_reminder':
			_, old, new = action
			if old[0] == new[0]:
				return self._build_reminder_update_command(new[0], old[1], new[1])
			return [self._sync_delete_reminder_script(old), self._sync_make_reminder_script(new)]
		if kind == 'make_event':
			return [self._sync_make_event_script(action[1])]
		if kind == 'delete_event':
			return [self._sync_delete_event_script(action[1])]
		if kind == 'move_event':
			_, old, new = action
			return [self._sync_delete_event_script(old), self._sync_make_event_script(new)]
		return []

	def _reopen_time_row(self, key, make_event):
		"""The tick of a completed item was taken off again in Reminders: the row is UNDONE again, its event
		comes back from "Tomato-old", the diary says so, and the line its completion left in the item's
		record goes. (Occurrences of a repeating item made when it was completed stay.)"""
		row = self._find_time_row_by_key(*key)
		status_item = self.tableWidget.item(row, 4) if row is not None else None
		if status_item is None or status_item.text() != 'DONE':
			return []
		self._set_time_cell(row, 4, 'UNDONE')
		view = self.widget0.currentIndex()
		if view == 2:
			self.tableWidget.setRowHidden(row, False)
		elif view == 4:
			self.tableWidget.setRowHidden(row, True)
		elif view == 3:
			with contextlib.suppress(ValueError, TypeError):
				self.tableWidget.setRowHidden(row, int(key[1]) >= time.time())
		when = self._sync_script_time(key[1])
		commands = ["""tell application "Calendar"
	tell calendar "Tomato-old"
		delete (events whose (start date is date "%s") and (summary is "%s"))
	end tell
end tell""" % (when, self._escape_applescript_string(key[0]))]
		if make_event:
			commands.append(self._sync_make_event_script(key))
		time_item = self.tableWidget.item(row, 1)
		date_text = time_item.text() if time_item else ''
		with contextlib.suppress(Exception):
			self._append_diary_line('Reopened ' + key[0] + ' scheduled for ' + date_text)
		repeat_item = self.tableWidget.item(row, 3)
		if repeat_item and repeat_item.text() not in ('', '-'):
			with contextlib.suppress(Exception):
				self._drop_last_record_line(self._record_file_path(key[0]), date_text)
		return commands

	def _append_diary_line(self, text):
		diary_file = os.path.join(self.fulldir_dia, datetime.datetime.now().strftime('%Y-%m-%d diary') + '.md')
		if not os.path.exists(diary_file):
			os.makedirs(self.fulldir_dia, exist_ok=True)
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write('# ' + datetime.datetime.now().strftime('%Y-%m-%d diary'))
		with open(diary_file, 'a', encoding='utf-8') as f0:
			f0.write('\n\n- ' + datetime.datetime.now().strftime('%H:%M:%S ') + text)
		contm = codecs.open(diary_file, 'r', encoding='utf-8').read()
		self.textii1.setText(contm)
		cursor = self.textii1.textCursor()
		cursor.setPosition(len(self.textii1.toPlainText()))
		self.textii1.setTextCursor(cursor)

	def _drop_last_record_line(self, record_file, date_text):
		"""Takes the newest line with this date out of an item's record file."""
		if not date_text or not os.path.exists(record_file):
			return False
		with open(record_file, 'r', encoding='utf8', newline='') as csv_file:
			lines = list(csv.reader(csv_file))
		for index in range(len(lines) - 1, -1, -1):
			if lines[index] and lines[index][0] == date_text:
				del lines[index]
				with open(record_file, 'w', encoding='utf8', newline='') as csv_file:
					csv.writer(csv_file).writerows(lines)
				return True
		return False

	def _show_safety_notification(self, function_name):
		"""Show auto-closing notification when safety check fails"""
		try:
			# Check if we recently showed a notification for this function (cooldown)
			current_time = time.time()
			last_time = self._last_safety_notification_time.get(function_name, 0)

			if current_time - last_time < self._safety_notification_cooldown:
				# Still in cooldown period, don't show notification
				logging.debug(f"Skipping notification for {function_name} (in cooldown period)")
				return

			# Update last notification time
			self._last_safety_notification_time[function_name] = current_time

			# Show the notification
			notification = AutoCloseNotification(
				_tr("Safety Check Warning"),
				_tr("Unable to access table widget in %n.").replace('%n', str(function_name)) + "\n\n"
				+ _tr("The operation will be skipped this round and retried in the next sync cycle.") + "\n\n"
				+ _tr("This is a protective measure to prevent crashes."),
				auto_close_seconds=5
			)
			self._safety_notification = notification  # keep it alive while it is on screen
			notification.show()
		except Exception as e:
			# If we can't even show the notification, just log it
			logging.exception("Failed to show safety notification: %s", e)

	def _collect_time_entries(self):
		# Safety check: ensure tableWidget exists and is valid
		if not hasattr(self, 'tableWidget') or self.tableWidget is None:
			logging.warning("_collect_time_entries: tableWidget not available, skipping")
			self._show_safety_notification("_collect_time_entries")
			return {}

		try:
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
		except Exception as e:
			logging.exception("Error in _collect_time_entries: %s", e)
			return {}

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
		if not hasattr(self, 'tableWidget') or self.tableWidget is None:
			logging.warning("_find_time_row_by_key: tableWidget not available, skipping")
			self._show_safety_notification("_find_time_row_by_key")
			return None
		try:
			target_stamp = self._normalize_stamp(stamp_value)
			for row in range(self.tableWidget.rowCount()):
				type_item = self.tableWidget.item(row, 7)
				if type_item is None or type_item.text() != 'TIME_SNS':
					continue
				name_item = self.tableWidget.item(row, 0)
				if name_item is None:
					continue
				row_stamp = self._stamp_from_items(self.tableWidget.item(row, 8), self.tableWidget.item(row, 1))
				# names are compared without the spaces around them, as the system's own are read
				if name_item.text().strip() == (name or '').strip() and row_stamp == target_stamp:
					return row
			return None
		except Exception as e:
			logging.exception("Error in _find_time_row_by_key: %s", e)
			return None

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
		if not hasattr(self, 'tableWidget') or self.tableWidget is None:
			logging.warning("_refresh_stamp_column: tableWidget not available, skipping")
			self._show_safety_notification("_refresh_stamp_column")
			return
		try:
			for row in range(self.tableWidget.rowCount()):
				time_item = self.tableWidget.item(row, 1)
				if not time_item or time_item.text() == '':
					continue
				with contextlib.suppress(Exception):
					stamp_str = self._normalize_stamp(self.to_stamp(time_item.text()))
					if stamp_str:
						self.tableWidget.setItem(row, 8, QTableWidgetItem(stamp_str))
		except Exception as e:
			logging.exception("Error in _refresh_stamp_column: %s", e)


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
			if sta9_inp != '' and self._broccoli_begin_task(ite1_inp, sta9_inp, length_hours, repeat_hours, pro7_inp):
				return
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

				# If this is a repeat task, pre-generate future occurrences based on setting
				if repeat_hours != '-':
					try:
						repeat_hours_float = float(repeat_hours)
						repeat_end_stamp = None
						if pro7_inp not in ('', '-'):
							try:
								repeat_end_stamp = float(pro7_inp)
							except ValueError:
								pass
						base_stamp = float(sta9_inp)
						# Prepare base values for generation
						base_values = [ite1_inp, '', length_hours, repeat_hours, 'UNDONE', '-', pro7_inp, 'TIME_SNS', '']
						# Generate N-1 more occurrences (we already have the first one)
						pregenerate_count = self._get_repeat_pregenerate_count()
						occurrences = self._generate_repeat_occurrences(
							base_values, pregenerate_count - 1, base_stamp, repeat_hours_float, repeat_end_stamp)
						# Add each occurrence to CSV and create reminders/calendar events
						additional_rows = []
						additional_cmds = []
						for row_values, rem_cmd, cal_cmd in occurrences:
							additional_rows.append(row_values)
							additional_cmds.extend([rem_cmd, cal_cmd])
						if additional_rows:
							with open(self.fulldirall, 'r', encoding='utf8') as csv_file:
								csv_reader = csv.reader(csv_file)
								lines = list(csv_reader)
								lines = lines + additional_rows
							with open(self.fulldirall, 'w', encoding='utf8') as csv_file:
								csv_writer = csv.writer(csv_file)
								csv_writer.writerows(lines)
							if additional_cmds:
								self._run_osascript_batch(additional_cmds)
					except (ValueError, TypeError):
						pass

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
			ask_row = self.tableWidget.currentIndex().row()
			ask_items = [self.tableWidget.item(ask_row, col) for col in (0, 3, 6, 4)]
			if ask_items[0] is not None and ask_items[1] is not None and ask_items[3] is not None and ask_items[3].text() == 'UNDONE':
				ask_stamp = self._stamp_from_items(self.tableWidget.item(ask_row, 8), self.tableWidget.item(ask_row, 1))
				later_rows = self._repeat_later_rows(ask_items[0].text(), ask_items[1].text(), ask_items[2].text() if ask_items[2] else '-', ask_stamp, ask_row) if ask_stamp else []
				if later_rows:
					scope = self._ask_repeat_scope(
						_tr('Delete'),
						_tr('"%1" repeats, and %n later ones are still to do. Delete the later ones too?'),
						ask_items[0].text(), len(later_rows))
					if scope == 'cancel':
						return
					if scope == 'later':
						self._delete_repeat_from(ask_row, later_rows)
						self.le4.setText('-')
						self.le4.setText('')
						return
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
			self._mark_local_reminder_change()
			self.tableWidget.removeRow(find_row)
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
			fulldir1 = TOMATO_DATA_DIR
			os.makedirs(fulldir1, exist_ok=True)
			tarname2 = "All.csv"
			fulldir2 = os.path.join(fulldir1, tarname2)
			shutil.copy(fulldir2, fj)

	def on_text_change(self):
		self._save_diary_box(self.textii1)

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
				new3_leng = self.tableWidget.item(self.changing_row, 2).text()
				new4_rep = repeat_item.text()
				new7_pro = self.tableWidget.item(self.changing_row, 6).text() if self.tableWidget.item(self.changing_row, 6) else '-'
				try:
					current_stamp = float(self.to_stamp(new_time))
				except Exception:
					current_stamp = None
				if current_stamp is not None:
					# Count how many UNDONE future occurrences exist
					future_count = self._count_future_undone_occurrences(
						new1_text, new4_rep, new7_pro, current_stamp)
					# Calculate how many new occurrences we need to create based on setting
					pregenerate_count = self._get_repeat_pregenerate_count()
					needed_count = max(0, pregenerate_count - future_count)
					if needed_count > 0:
						# Get the latest stamp to start generating from
						latest_stamp = self._get_latest_stamp_for_repeat(new1_text, new4_rep, new7_pro)
						if latest_stamp < current_stamp:
							latest_stamp = current_stamp
						# Prepare base values for generation
						base_values = [new1_text, '', new3_leng, new4_rep, 'UNDONE', '-', new7_pro, 'TIME_SNS', '']
						# Generate the needed occurrences
						occurrences = self._generate_repeat_occurrences(
							base_values, needed_count, latest_stamp, repeat_hours, repeat_end_stamp)
						# Add each occurrence to the table and collect commands
						for row_values, rem_cmd, cal_cmd in occurrences:
							new_row_index = self._append_time_row_to_table(row_values)
							self.tableWidget.setRowHidden(new_row_index, False)
							reminder_cmds.append(rem_cmd)
							calendar_cmds.append(cal_cmd)

		ISOTIMEFORMAT = '%Y-%m-%d diary'
		theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
		diary_name = str(theTime) + ".md"
		diary_file = os.path.join(self.fulldir_dia, diary_name)
		if not os.path.exists(diary_file):
			os.makedirs(self.fulldir_dia, exist_ok=True)
			with open(diary_file, 'a', encoding='utf-8') as f0:
				f0.write(f'# {theTime}')
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
			record_file = self._record_file_path(self.tableWidget.item(self.changing_row, 0).text())
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
		if not selected_rows:
			self._warn_selection_required(_tr('Please select the items to be completed first, then click save.'))
			return
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
			record_file = self._record_file_path(self.tableWidget.item(self.tableWidget.currentRow(), 0).text())
			if os.path.exists(record_file):
				shutil.copy(record_file, fj)

	def record_write(self):
		if self.tableWidget.currentItem() != None:
			record_file = self._record_file_path(self.tableWidget.item(self.tableWidget.currentRow(), 0).text())
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

	# def _on_record_edit_finished(self, row, column):
	# 	"""Called when a cell in tableWidget_record finishes being edited (keyboard or mouse)"""
	# 	self.record_write()

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

		# Setup delegate for keyboard-based editing detection
		self._table_freq_delegate = TableEditDelegate(self.tableWidget_freq)
		self.tableWidget_freq.setItemDelegate(self._table_freq_delegate)
		self._table_freq_delegate.editing_started.connect(self._on_freq_edit_started)
		self._table_freq_delegate.editing_finished.connect(self._on_freq_edit_finished)
		#self.tableWidget_freq.setFixedHeight(int(self.tableWidget_freq.width()))

		t1 = QWidget()
		self.lf1 = QLineEdit(self)
		self.lf1.setPlaceholderText(_tr('Item'))
		self.lf1.setFixedHeight(MAIN_ROW_HEIGHT)

		self.lf2 = QLineEdit(self)
		self.lf2.setPlaceholderText(_tr('Target'))
		self.lf2.setFixedHeight(MAIN_ROW_HEIGHT)
		self._refresh_on_program_change(self.lf2, self.freq_refresh)
		b1 = QHBoxLayout()
		b1.setContentsMargins(0, 0, 0, 0)
		b1.addWidget(self.lf1)
		b1.addWidget(self.lf2)
		t1.setLayout(b1)

		# the block's main action: a glass white capsule in the row of the item box (style book 5.1 / 5.12)
		t1_5 = QWidget()
		btn_t1 = WhiteButton(_tr('Add!'), self)
		btn_t1.clicked.connect(self.add_to_freq)
		btn_t1.setShortcut("Ctrl+Return")
		btn_t1.setMinimumWidth(96)
		b1_5 = QHBoxLayout()
		b1_5.setContentsMargins(0, 0, 0, 0)
		b1_5.addWidget(btn_t1)
		t1_5.setLayout(b1_5)
		t1_5.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

		t1_6 = QWidget()
		b1_6 = QHBoxLayout()
		b1_6.setContentsMargins(0, 0, 0, 0)
		b1_6.addWidget(t1, 1)
		b1_6.addWidget(t1_5)
		t1_6.setLayout(b1_6)

		t2 = QWidget()
		self.widget1 = compact_dropdown(self)
		self.widget1.setCurrentIndex(0)
		self.widget1.currentIndexChanged.connect(self.freq_index)
		self.widget1.addItems([_tr('All'), _tr('To-do'), _tr('Done')])

		btn_t2 = MacNormalButton(_tr('Delete selected item'), self)
		btn_t2.clicked.connect(self.freq_delete)
		btn_t2.setFixedHeight(GREY_ROW_HEIGHT)
		# self.widget1.setFixedWidth(btn_t2.width() * 2)

		btn_t7 = MacNormalButton(_tr('Delete all DONEs'), self)
		btn_t7.clicked.connect(self.freq_delete_dones)
		btn_t7.setFixedHeight(GREY_ROW_HEIGHT)

		self.freq1 = panel_line(self)

		btn_t3 = MacNormalButton(_tr('Export plan'), self)
		btn_t3.clicked.connect(self.export_plan)
		btn_t3.setFixedHeight(GREY_ROW_HEIGHT)

		btn_t5 = MacNormalButton(_tr('Export diary'), self)
		btn_t5.clicked.connect(self.export_diary)
		btn_t5.setFixedHeight(GREY_ROW_HEIGHT)

		btn_t6 = MacNormalButton(_tr('Export records'), self)
		btn_t6.clicked.connect(self.export_record)
		btn_t6.setFixedHeight(GREY_ROW_HEIGHT)
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
		self.textw2.setPlaceholderText(_tr('Comments'))
		#self.textw2.setMaximumHeight(44)

		btn_t4 = WhiteButton(_tr('Add 1 time!'), self)
		btn_t4.clicked.connect(self.freq_add_time)
		btn_t4.setShortcut("Ctrl+Shift+Return")

		self.freq2 = panel_line(self)

		self.freq_date_edit = QDateEdit(self)
		self.freq_date_edit.setCalendarPopup(True)
		self.freq_date_edit.setDisplayFormat('yyyy-MM-dd')
		self.freq_date_edit.setDate(QDate.currentDate())
		self.freq_date_edit.setFixedHeight(GREY_ROW_HEIGHT)
		self.freq_date_edit.setToolTip(_tr('Choose Date'))

		self.freq_time_edit = QTimeEdit(self)
		self.freq_time_edit.setDisplayFormat('HH:mm')
		self.freq_time_edit.setTime(QTime.currentTime())
		self.freq_time_edit.setFixedHeight(GREY_ROW_HEIGHT)
		self.freq_time_edit.setToolTip(_tr('Hover to open clock picker'))
		self.freq_time_edit.installEventFilter(self)

		self.freq_clock_picker_popup = ClockPickerPopup()
		self.freq_clock_picker_popup.set_target_widget(self.freq_time_edit)
		self.freq_clock_picker_popup.time_changed.connect(lambda t: self.freq_time_edit.setTime(t))

		self.lf4 = QLineEdit(self)
		self.lf4.setPlaceholderText(_tr('Length'))
		self.lf4.setFixedHeight(GREY_ROW_HEIGHT)

		self.freq_length_unit = compact_dropdown(self)
		for label, factor in self._time_unit_items:
			self.freq_length_unit.addItem(_tr(label), factor)
		self.freq_length_unit.setCurrentIndex(self._time_unit_hours_index)
		self.freq_length_unit.setFixedWidth(100)

		self.lf5 = QLineEdit(self)
		self.lf5.setPlaceholderText(_tr('Repeat'))
		self.lf5.setFixedHeight(GREY_ROW_HEIGHT)

		self.freq_repeat_unit = compact_dropdown(self)
		for label, factor in self._repeat_unit_items:
			self.freq_repeat_unit.addItem(_tr(label), factor)
		self.freq_repeat_unit.setCurrentIndex(0)
		self.freq_repeat_unit.setFixedWidth(100)

		self.freq_repeat_until_check = QCheckBox(_tr('Repeat until'), self)
		self.freq_repeat_until_check.setChecked(False)
		self.freq_repeat_until_check.setFixedWidth(100)
		self.freq_repeat_until_date = QDateEdit(self)
		self.freq_repeat_until_date.setCalendarPopup(True)
		self.freq_repeat_until_date.setDisplayFormat('yyyy-MM-dd')
		self.freq_repeat_until_date.setDate(QDate.currentDate())
		self.freq_repeat_until_date.setFixedHeight(GREY_ROW_HEIGHT)
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

		btn_t5 = MacNormalButton(_tr('Copy to Time-sensitive list'), self)
		btn_t5.clicked.connect(self.freq_move_time)
		btn_t5.setFixedHeight(GREY_ROW_HEIGHT)
		freq_datetime_row = QHBoxLayout()
		freq_datetime_row.setContentsMargins(0, 0, 0, 0)
		freq_datetime_row.addWidget(self.freq_date_edit)
		freq_datetime_row.addWidget(self.freq_time_edit)
		freq_end_row = self._end_time_row('freq', self.freq_date_edit, self.freq_time_edit, self.lf4, self.freq_length_unit)

		b3 = QVBoxLayout()
		b3.setContentsMargins(0, 0, 0, 0)
		b3.setSpacing(6)
		b3.addWidget(self.textw2)
		b3.addWidget(btn_t4)
		b3.addWidget(self.freq2)
		b3.addLayout(freq_datetime_row)
		b3.addLayout(freq_end_row)
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

		# # Setup delegate for keyboard-based editing detection
		# self._table_record2_delegate = TableEditDelegate(self.tableWidget_record2)
		# self.tableWidget_record2.setItemDelegate(self._table_record2_delegate)
		# self._table_record2_delegate.editing_finished.connect(self._on_record2_edit_finished)

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
		t5.setFixedHeight(EDIT_PANEL_COLUMNS_HEIGHT)

		style_table(self.tableWidget_freq)
		style_table(self.tableWidget_record2, kind='card')
		self.freq_panel = edit_panel(t1_6, t5)
		self.freq_stage = self._page_stage(self.art_tab, self.tableWidget_freq, self.freq_panel)

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
			# Has selected item - show history records and enable editing
			self.tableWidget_record2.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed | QAbstractItemView.EditTrigger.AnyKeyPressed)
			record2_file = self._record_file_path(self.tableWidget_freq.item(self.tableWidget_freq.currentRow(), 0).text())
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
		else:
			# No selected item - show placeholder message and disable editing
			self.tableWidget_record2.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
			self.tableWidget_record2.setColumnCount(1)
			self.tableWidget_record2.setRowCount(1)
			self.tableWidget_record2.setHorizontalHeaderLabels(['History'])
			self.tableWidget_record2.verticalHeader().setVisible(False)
			placeholder_item = QTableWidgetItem('No history records available\n(Please select a frequency item)')
			placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
			placeholder_item.setFlags(placeholder_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
			self.tableWidget_record2.setItem(0, 0, placeholder_item)
			self.tableWidget_record2.setColumnWidth(0, self.tableWidget_record2.width())
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

				record_file = self._record_file_path(self.tableWidget_freq.item(self.freq_changing_row, 0).text())
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

				record_file = self._record_file_path(self.tableWidget_freq.item(self.freq_changing_row, 0).text())
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

	def _on_freq_edit_started(self, row, column):
		"""Called when a cell in tableWidget_freq starts being edited (keyboard or mouse)"""
		if row < 0 or row >= self.tableWidget_freq.rowCount():
			return
		self.freq_double = 1
		self.freq_changing_row = row
		self.freq_changing_column = column
		item5 = self.tableWidget_freq.item(row, 5)
		try:
			self.freq_target = int(item5.text()) if item5 else 0
		except ValueError:
			self.freq_target = 0

	def _on_freq_edit_finished(self, row, column):
		"""Called when a cell in tableWidget_freq finishes being edited (keyboard or mouse)"""
		if self.freq_double == 1:
			self.freq_write_time()

	def freq_index(self, i):
		self.freq_readlater()
		self._clear_table_selection(self.tableWidget_freq)

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
		self._clear_table_selection(self.tableWidget_freq)

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
		self._save_diary_box(self.textii2)

	def freq_record_write(self):
		if self.tableWidget_freq.currentItem() != None:
			record2_file = self._record_file_path(self.tableWidget_freq.item(self.tableWidget_freq.currentRow(), 0).text())
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

	# def _on_record2_edit_finished(self, row, column):
	# 	"""Called when a cell in tableWidget_record2 finishes being edited (keyboard or mouse)"""
	# 	self.freq_record_write()

	def _freq_add_time_single(self):
		if self.tableWidget_freq.currentItem() != None:
			current_row = self.tableWidget_freq.currentIndex().row()
			if current_row < 0:
				self._warn_selection_required(_tr('Please select the frequency items to be summed first.'))
				return

			target_item = self.tableWidget_freq.item(current_row, 5)
			target_text = target_item.text().strip() if target_item else ''
			if target_text in ('', '-'):
				self._warn_selection_required(_tr('Please fill in the number first.'))
				return
			try:
				self.freq_target = int(target_text)
			except ValueError:
				self._warn_selection_required(_tr('"The target must be a number."'))
				return

			process_item = self.tableWidget_freq.item(current_row, 6)
			process_text = process_item.text().strip() if process_item else ''
			try:
				process_time = int(process_text) + 1
			except Exception:
				process_time = 1
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

			record_file = self._record_file_path(self.tableWidget_freq.item(self.freq_changing_row, 0).text())
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
			self._warn_selection_required(_tr('Please select the frequency items to be summed first.'))
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

		# Setup delegate for keyboard-based editing detection
		self._table_memo_delegate = TableEditDelegate(self.tableWidget_memo)
		self.tableWidget_memo.setItemDelegate(self._table_memo_delegate)
		self._table_memo_delegate.editing_started.connect(self._on_memo_edit_started)
		self._table_memo_delegate.editing_finished.connect(self._on_memo_edit_finished)
		#self.tableWidget_memo.setFixedHeight(int(self.tableWidget_memo.width()))

		t1 = QWidget()
		self.lm1 = QLineEdit(self)
		self.lm1.setPlaceholderText(_tr('Item'))
		self.lm1.setFixedHeight(MAIN_ROW_HEIGHT)
		self._refresh_on_program_change(self.lm1, self.memo_refresh)

		b1 = QVBoxLayout()
		b1.setContentsMargins(0, 0, 0, 0)
		b1.addWidget(self.lm1)
		t1.setLayout(b1)

		# the block's main action: a glass white capsule in the row of the item box (style book 5.1 / 5.12)
		t1_5 = QWidget()
		btn_t1 = WhiteButton(_tr('Add!'), self)
		btn_t1.clicked.connect(self.memo_add)
		btn_t1.setShortcut("Ctrl+Return")
		btn_t1.setMinimumWidth(96)
		b1_5 = QHBoxLayout()
		b1_5.setContentsMargins(0, 0, 0, 0)
		b1_5.addWidget(btn_t1)
		t1_5.setLayout(b1_5)
		t1_5.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

		t1_6 = QWidget()
		b1_6 = QHBoxLayout()
		b1_6.setContentsMargins(0, 0, 0, 0)
		b1_6.addWidget(t1, 1)
		b1_6.addWidget(t1_5)
		t1_6.setLayout(b1_6)

		t2 = QWidget()
		self.widget2 = compact_dropdown(self)
		self.widget2.setCurrentIndex(0)
		self.widget2.currentIndexChanged.connect(self.memo_index_change)
		self.widget2.addItems([_tr('All'), _tr('To-do'), _tr('Done')])

		btn_t2 = MacNormalButton(_tr('Delete selected item'), self)
		btn_t2.clicked.connect(self.memo_delete)
		btn_t2.setFixedHeight(GREY_ROW_HEIGHT)
		# self.widget2.setFixedWidth(btn_t2.width() * 2)

		btn_t7 = MacNormalButton(_tr('Delete all DONEs'), self)
		btn_t7.clicked.connect(self.memo_delete_dones)
		btn_t7.setFixedHeight(GREY_ROW_HEIGHT)

		self.memo1 = panel_line(self)

		btn_t3 = MacNormalButton(_tr('Export plan'), self)
		btn_t3.clicked.connect(self.export_plan)
		btn_t3.setFixedHeight(GREY_ROW_HEIGHT)

		btn_t5 = MacNormalButton(_tr('Export diary'), self)
		btn_t5.clicked.connect(self.export_diary)
		btn_t5.setFixedHeight(GREY_ROW_HEIGHT)

		btn_t6 = MacNormalButton(_tr('Export records'), self)
		btn_t6.clicked.connect(self.export_record)
		btn_t6.setFixedHeight(GREY_ROW_HEIGHT)
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
		self.textw3.setPlaceholderText(_tr('Comments'))
		#self.textw3.setMaximumHeight(44)

		btn_t4 = WhiteButton(_tr('Done this memo!'), self)
		btn_t4.clicked.connect(self.memo_done_memo)
		btn_t4.setShortcut("Ctrl+Shift+Return")

		self.memo2 = panel_line(self)

		self.memo_date_edit = QDateEdit(self)
		self.memo_date_edit.setCalendarPopup(True)
		self.memo_date_edit.setDisplayFormat('yyyy-MM-dd')
		self.memo_date_edit.setDate(QDate.currentDate())
		self.memo_date_edit.setFixedHeight(GREY_ROW_HEIGHT)
		self.memo_date_edit.setToolTip(_tr('Choose Date'))

		self.memo_time_edit = QTimeEdit(self)
		self.memo_time_edit.setDisplayFormat('HH:mm')
		self.memo_time_edit.setTime(QTime.currentTime())
		self.memo_time_edit.setFixedHeight(GREY_ROW_HEIGHT)
		self.memo_time_edit.setToolTip(_tr('Hover to open clock picker'))
		self.memo_time_edit.installEventFilter(self)

		self.memo_clock_picker_popup = ClockPickerPopup()
		self.memo_clock_picker_popup.set_target_widget(self.memo_time_edit)
		self.memo_clock_picker_popup.time_changed.connect(lambda t: self.memo_time_edit.setTime(t))

		self.lm4 = QLineEdit(self)
		self.lm4.setPlaceholderText(_tr('Length'))
		self.lm4.setFixedHeight(GREY_ROW_HEIGHT)

		self.memo_length_unit = compact_dropdown(self)
		for label, factor in self._time_unit_items:
			self.memo_length_unit.addItem(_tr(label), factor)
		self.memo_length_unit.setCurrentIndex(self._time_unit_hours_index)
		self.memo_length_unit.setFixedWidth(100)

		self.lm5 = QLineEdit(self)
		self.lm5.setPlaceholderText(_tr('Repeat'))
		self.lm5.setFixedHeight(GREY_ROW_HEIGHT)

		self.memo_repeat_unit = compact_dropdown(self)
		for label, factor in self._repeat_unit_items:
			self.memo_repeat_unit.addItem(_tr(label), factor)
		self.memo_repeat_unit.setCurrentIndex(0)
		self.memo_repeat_unit.setFixedWidth(100)

		self.memo_repeat_until_check = QCheckBox(_tr('Repeat until'), self)
		self.memo_repeat_until_check.setChecked(False)
		self.memo_repeat_until_check.setFixedWidth(100)
		self.memo_repeat_until_date = QDateEdit(self)
		self.memo_repeat_until_date.setCalendarPopup(True)
		self.memo_repeat_until_date.setDisplayFormat('yyyy-MM-dd')
		self.memo_repeat_until_date.setDate(QDate.currentDate())
		self.memo_repeat_until_date.setFixedHeight(GREY_ROW_HEIGHT)
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

		btn_t5 = MacNormalButton(_tr('Copy to Time-sensitive list'), self)
		btn_t5.clicked.connect(self.memo_copy_to_time)
		btn_t5.setFixedHeight(GREY_ROW_HEIGHT)
		memo_datetime_row = QHBoxLayout()
		memo_datetime_row.setContentsMargins(0, 0, 0, 0)
		memo_datetime_row.addWidget(self.memo_date_edit)
		memo_datetime_row.addWidget(self.memo_time_edit)
		memo_end_row = self._end_time_row('memo', self.memo_date_edit, self.memo_time_edit, self.lm4, self.memo_length_unit)

		b3 = QVBoxLayout()
		b3.setContentsMargins(0, 0, 0, 0)
		b3.setSpacing(6)
		b3.addWidget(self.textw3)
		b3.addWidget(btn_t4)
		b3.addWidget(self.memo2)
		b3.addLayout(memo_datetime_row)
		b3.addLayout(memo_end_row)
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
		t5.setFixedHeight(EDIT_PANEL_COLUMNS_HEIGHT)

		style_table(self.tableWidget_memo)
		self.memo_panel = edit_panel(t1_6, t5)
		self.memo_stage = self._page_stage(self.insp_tab, self.tableWidget_memo, self.memo_panel)

	def collectTab(self):
		self.collection_current_file = None
		self._collection_loading = False
		self._collection_table_block = False
		self._collection_preview_updating = False
		self._collection_preview_mode = False
		self._collection_scroll_ratio = 0.0
		self._collection_last_markdown = ''

		self.collection_table = QTableWidget()
		self.collection_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
		self.collection_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
		self.collection_table.setAutoScroll(False)
		self.collection_table.verticalHeader().setVisible(True)
		self.collection_table.itemSelectionChanged.connect(self._update_collection_markdown_preview)
		self.collection_table.itemChanged.connect(self._handle_collection_item_changed)
		self._collection_viewport = self.collection_table.viewport()
		self._collection_viewport.installEventFilter(self)             # a row can be dragged into a diary box
		self._collection_drag_from = None

		self.collection_md_editor = QPlainTextEdit(self)
		self.collection_md_editor.setPlaceholderText(_tr('Select a row to view it as Markdown.'))
		self.collection_md_editor.setReadOnly(True)
		self.collection_md_editor.textChanged.connect(self._handle_collection_markdown_change)

		# a web page (formulas are typeset; see tomato_preview.py) — it answers the calls the QTextBrowser got
		self.collection_md_preview = tomato_preview.MarkdownWebPreview(self, base_folder=TOMATO_MATHJAX_DIR)
		self.collection_md_preview.set_background('#F3F2EE')

		self.collection_view_stack = QStackedWidget(self)
		self.collection_view_stack.addWidget(self.collection_md_editor)
		self.collection_view_stack.addWidget(self.collection_md_preview)
		self.collection_view_stack.setCurrentWidget(self.collection_md_editor)

		# Preview / Edit: a glass white capsule floating at the top right of the Markdown box (style book 5.1;
		# its old place, the bottom right, now lies under the edit panel)
		self.collection_view_toggle_btn = WhiteButton(_tr('Preview'), self.collection_view_stack)
		self.collection_view_toggle_btn.setCheckable(True)
		self.collection_view_toggle_btn.setFixedWidth(96)
		self.collection_view_toggle_btn.toggled.connect(self._toggle_collection_view_mode)
		self.collection_view_stack.installEventFilter(self)
		self._position_collection_toggle_button()

		right_view_container = QWidget()
		right_view_layout = QVBoxLayout()
		right_view_layout.setContentsMargins(0, 0, 0, 0)
		right_view_layout.setSpacing(4)
		right_view_layout.addWidget(self.collection_view_stack, 1)
		right_view_container.setLayout(right_view_layout)

		splitter = QSplitter(Qt.Orientation.Horizontal)
		splitter.setHandleWidth(8)
		splitter.addWidget(self.collection_table)
		splitter.addWidget(right_view_container)
		splitter.setStretchFactor(0, 2)
		splitter.setStretchFactor(1, 1)

		self.collection_file_combo = compact_dropdown(self)
		self.collection_file_combo.currentIndexChanged.connect(self._collection_file_changed)

		btn_new_csv = MacNormalButton(_tr('New'), self)
		btn_new_csv.clicked.connect(self._collection_new_file)
		btn_delete_csv = MacNormalButton(_tr('Delete'), self)
		btn_delete_csv.clicked.connect(self._collection_delete_file)
		btn_open_dir = MacNormalButton(_tr('Open Folder'), self)
		btn_open_dir.clicked.connect(self._open_collection_dir)

		btn_t3 = MacNormalButton(_tr('Export plan'), self)
		btn_t3.clicked.connect(self.export_plan)
		btn_t3.setFixedHeight(GREY_ROW_HEIGHT)

		btn_t5 = MacNormalButton(_tr('Export diary'), self)
		btn_t5.clicked.connect(self.export_diary)
		btn_t5.setFixedHeight(GREY_ROW_HEIGHT)

		btn_t6 = MacNormalButton(_tr('Export records'), self)
		btn_t6.clicked.connect(self.export_record)
		btn_t6.setFixedHeight(GREY_ROW_HEIGHT)

		t4 = QWidget()
		t4.setFixedHeight(GREY_ROW_HEIGHT)
		b4 = QHBoxLayout()
		b4.setContentsMargins(0, 0, 0, 0)
		b4.addWidget(btn_new_csv)
		b4.addWidget(btn_delete_csv)
		t4.setLayout(b4)

		self.frame21 = panel_line(self)

		t2 = QWidget()
		file_bar = QVBoxLayout()
		file_bar.setContentsMargins(0, 0, 0, 0)
		#file_bar.addStretch()
		# file_bar.addWidget(QLabel(_tr('CSV File:'), self))
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
		self.collection_search_input.setPlaceholderText(_tr('Search…'))
		self.collection_search_input.setClearButtonEnabled(True)  # replaces the old separate "Clear" button
		self.collection_search_input.setStyleSheet(glass_kit._search_input_stylesheet(is_dark_theme(app)))
		glass_kit.glass_search_field(self.collection_search_input)
		self.collection_search_input.textChanged.connect(self._collection_apply_search)
		search_bar = QHBoxLayout()
		search_bar.setContentsMargins(0, 0, 0, 0)
		search_bar.addWidget(self.collection_search_input, 1)

		self.collection_sort_column_combo = compact_dropdown(self)
		self.collection_sort_column_combo.setFixedHeight(GREY_ROW_HEIGHT)
		self.collection_sort_mode_combo = compact_dropdown(self)
		self.collection_sort_mode_combo.setFixedHeight(GREY_ROW_HEIGHT)
		self.collection_sort_mode_combo.setMinimumWidth(104)
		self.collection_sort_mode_combo.addItem(_tr('Text'), 'text')
		self.collection_sort_mode_combo.addItem(_tr('Number'), 'number')
		self.collection_sort_mode_combo.addItem(_tr('Date/Time'), 'datetime')
		self.collection_sort_mode_combo.addItem(_tr('Boolean'), 'bool')
		btn_sort_asc = MacNormalButton(_tr('Sort ↑'), self)
		btn_sort_asc.setFixedSize(100, 20)
		btn_sort_asc.clicked.connect(lambda: self._collection_sort(False))
		btn_sort_desc = MacNormalButton(_tr('Sort ↓'), self)
		btn_sort_desc.setFixedSize(100, 20)
		btn_sort_desc.clicked.connect(lambda: self._collection_sort(True))
		# btn_sort_reset = MacNormalButton(_tr('Reset Order'), self)
		# btn_sort_reset.clicked.connect(self._collection_reset_order)
		btn_manage_columns = MacNormalButton(_tr('Hide Columns'), self)
		btn_manage_columns.setFixedHeight(GREY_ROW_HEIGHT)
		btn_manage_columns.clicked.connect(self._collection_manage_columns)

		t10 = QWidget()
		b10 = QHBoxLayout()
		b10.setContentsMargins(0, 0, 0, 0)
		b10.addWidget(QLabel(_tr('Sort column:'), self))
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
		# sort_bar.addWidget(QLabel(_tr('Sort column:'), self))
		# sort_bar.addWidget(self.collection_sort_column_combo, 1)
		# sort_bar.addWidget(self.collection_sort_mode_combo)
		# sort_bar.addWidget(btn_sort_asc)
		# sort_bar.addWidget(btn_sort_desc)
		# sort_bar.addWidget(btn_manage_columns)
		sort_bar.addWidget(t10)
		sort_bar.addWidget(t11)
		# sort_bar.addWidget(btn_sort_reset)

		btn_add_row = MacNormalButton(_tr('Add Row'), self)
		btn_add_row.setFixedHeight(GREY_ROW_HEIGHT)
		btn_add_row.clicked.connect(self._collection_add_row)
		btn_delete_row = MacNormalButton(_tr('Delete Row'), self)
		btn_delete_row.setFixedHeight(GREY_ROW_HEIGHT)
		btn_delete_row.clicked.connect(self._collection_delete_row)
		btn_row_up = MacNormalButton(_tr('Row ↑'), self)
		btn_row_up.setFixedHeight(GREY_ROW_HEIGHT)
		btn_row_up.clicked.connect(lambda: self._collection_move_row(-1))
		btn_row_down = MacNormalButton(_tr('Row ↓'), self)
		btn_row_down.setFixedHeight(GREY_ROW_HEIGHT)
		btn_row_down.clicked.connect(lambda: self._collection_move_row(1))
		
		row_bar = QHBoxLayout()
		row_bar.setContentsMargins(0, 0, 0, 0)
		row_bar.addWidget(btn_add_row)
		row_bar.addWidget(btn_delete_row)
		row_bar.addWidget(btn_row_up)
		row_bar.addWidget(btn_row_down)
		#row_bar.addStretch()

		btn_add_col = MacNormalButton(_tr('Add Col'), self)
		btn_add_col.setFixedHeight(GREY_ROW_HEIGHT)
		btn_add_col.clicked.connect(self._collection_add_column)
		btn_delete_col = MacNormalButton(_tr('Delete Col'), self)
		btn_delete_col.setFixedHeight(GREY_ROW_HEIGHT)
		btn_delete_col.clicked.connect(self._collection_delete_column)
		btn_col_left = MacNormalButton(_tr('Col ←'), self)
		btn_col_left.setFixedHeight(GREY_ROW_HEIGHT)
		btn_col_left.clicked.connect(lambda: self._collection_move_column(-1))
		btn_col_right = MacNormalButton(_tr('Col →'), self)
		btn_col_right.setFixedHeight(GREY_ROW_HEIGHT)
		btn_col_right.clicked.connect(lambda: self._collection_move_column(1))
		btn_rename_col = MacNormalButton(_tr('Rename Column'), self)
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
		self.collect_date_edit.setFixedHeight(GREY_ROW_HEIGHT)
		self.collect_date_edit.setToolTip(_tr('Choose Date'))

		self.collect_time_edit = QTimeEdit(self)
		self.collect_time_edit.setDisplayFormat('HH:mm')
		self.collect_time_edit.setTime(QTime.currentTime())
		self.collect_time_edit.setFixedHeight(GREY_ROW_HEIGHT)
		self.collect_time_edit.setToolTip(_tr('Hover to open clock picker'))
		self.collect_time_edit.installEventFilter(self)

		self.collect_clock_picker_popup = ClockPickerPopup()
		self.collect_clock_picker_popup.set_target_widget(self.collect_time_edit)
		self.collect_clock_picker_popup.time_changed.connect(lambda t: self.collect_time_edit.setTime(t))

		self.collect_length_input = QLineEdit(self)
		self.collect_length_input.setPlaceholderText(_tr('Length'))
		self.collect_length_input.setFixedHeight(GREY_ROW_HEIGHT)

		self.collect_length_unit = compact_dropdown(self)
		for label, factor in self._time_unit_items:
			self.collect_length_unit.addItem(_tr(label), factor)
		self.collect_length_unit.setCurrentIndex(self._time_unit_hours_index)
		self.collect_length_unit.setFixedWidth(100)
		self.collect_length_unit.setFixedHeight(GREY_ROW_HEIGHT)

		self.collect_repeat_input = QLineEdit(self)
		self.collect_repeat_input.setPlaceholderText(_tr('Repeat'))
		self.collect_repeat_input.setFixedHeight(GREY_ROW_HEIGHT)

		self.collect_repeat_unit = compact_dropdown(self)
		for label, factor in self._repeat_unit_items:
			self.collect_repeat_unit.addItem(_tr(label), factor)
		self.collect_repeat_unit.setCurrentIndex(0)
		self.collect_repeat_unit.setFixedWidth(100)
		self.collect_repeat_unit.setFixedHeight(GREY_ROW_HEIGHT)

		self.collect_repeat_until_check = QCheckBox(_tr('Repeat until'), self)
		self.collect_repeat_until_check.setChecked(False)
		self.collect_repeat_until_check.setFixedWidth(100)
		self.collect_repeat_until_date = QDateEdit(self)
		self.collect_repeat_until_date.setCalendarPopup(True)
		self.collect_repeat_until_date.setDisplayFormat('yyyy-MM-dd')
		self.collect_repeat_until_date.setDate(QDate.currentDate())
		self.collect_repeat_until_date.setFixedHeight(GREY_ROW_HEIGHT)
		self.collect_repeat_until_date.setEnabled(False)
		self.collect_repeat_until_check.toggled.connect(lambda _: self._apply_repeat_until_enable(self.collect_repeat_until_check, self.collect_repeat_until_date))

		btn_collect_copy = MacNormalButton(_tr('Copy to Time-sensitive list'), self)
		btn_collect_copy.clicked.connect(self._collect_copy_to_time)
		btn_collect_copy.setFixedHeight(GREY_ROW_HEIGHT)

		collect_time_row = QHBoxLayout()
		collect_time_row.setContentsMargins(0, 0, 0, 0)
		collect_time_row.addWidget(self.collect_date_edit)
		collect_time_row.addWidget(self.collect_time_edit)
		collect_end_row = self._end_time_row('collect', self.collect_date_edit, self.collect_time_edit,
											 self.collect_length_input, self.collect_length_unit)
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

		self.frame23 = panel_line(self)

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
		mid_bar.addLayout(collect_end_row)
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
		self.textiii1.textChanged.connect(lambda: self._save_diary_box(self.textiii1))   # was on_text_change: that saved the Time page's box
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
		t5.setFixedHeight(EDIT_PANEL_COLUMNS_HEIGHT)

		style_table(self.collection_table)
		self.collect_panel = edit_panel(search_bar, t5)
		self.collect_stage = self._page_stage(self.collect_tab, splitter, self.collect_panel)


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
			self.collection_md_editor.setPlainText(_tr('No CSV found. Create one to get started.'))
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
		name, ok = ask_text(self, _tr('New CSV'), _tr('File name (without extension):'))
		if not ok or name.strip() == '':
			return
		name = name.strip()
		if not name.lower().endswith('.csv'):
			name += '.csv'
		target = os.path.join(self.fulldir_collection, name)
		if os.path.exists(target):
			tomato_alert(self, _tr('File exists'), _tr('A file with this name already exists.'))
			return
		with open(target, 'w', encoding='utf-8', newline='') as csv_file:
			csv_writer = csv.writer(csv_file)
			csv_writer.writerow(['Column 1'])
		self._refresh_collection_files(select_path=target)

	def _collection_add_row(self):
		if self.collection_table.columnCount() == 0:
			tomato_alert(self, _tr('No columns'), _tr('Add a column before inserting rows.'))
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
		name, ok = ask_text(self, _tr('Add Column'), _tr('Column name:'))
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
		name, ok = ask_text(self, _tr('Rename Column'), _tr('Column name:'), text=current_name)
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
		if not tomato_confirm(self, _tr('Delete CSV'),
							  _tr('Delete "%n"?').replace('%n', os.path.basename(self.collection_current_file))):
			return
		try:
			os.remove(self.collection_current_file)
		except OSError as exc:
			tomato_alert(self, _tr('Delete failed'), _tr('Cannot delete file:') + '\n' + str(exc))
			return
		self.collection_current_file = None
		self._ensure_default_collection_file()
		self._refresh_collection_files()

	def _collection_manage_columns(self):
		col_count = self.collection_table.columnCount()
		if col_count == 0:
			return
		dialog = GlassFormDialog(_tr('Column Visibility'), self)
		list_widget = QListWidget(dialog)
		list_widget.setItemDelegate(CheckRowDelegate(list_widget))
		list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
		list_widget.setMouseTracking(True)
		list_widget.setMinimumHeight(220)
		for idx, header in enumerate(self._collection_headers()):
			item = QListWidgetItem(header if header else _tr('Column %n').replace('%n', str(idx + 1)))
			item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
			item.setCheckState(Qt.CheckState.Unchecked if self.collection_table.isColumnHidden(idx)
							   else Qt.CheckState.Checked)
			item.setData(Qt.ItemDataRole.UserRole, idx)
			list_widget.addItem(item)
		dialog.body.addWidget(list_widget)
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
			label = header if header else _tr('Column %n').replace('%n', str(idx + 1))
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
			self.collection_md_editor.setPlainText(_tr('Select a row to view its Markdown.'))
			self._collection_preview_updating = False
			self._collection_last_markdown = self.collection_md_editor.toPlainText()
			self._update_collection_html_preview()
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
		self._update_collection_html_preview()

	def _update_collection_html_preview(self):
		markdown_text = self.collection_md_editor.toPlainText()
		try:
			html_text = self.md2html(markdown_text)
			self.collection_md_preview.setHtml(html_text)
		except Exception:
			logging.exception("Failed to render collection markdown preview.")
			self.collection_md_preview.setPlainText(markdown_text)
		if self._collection_preview_mode:
			QTimer.singleShot(0, lambda: self._collection_apply_scroll_ratio(self.collection_md_preview, self._collection_scroll_ratio))

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
			tomato_alert(self, _tr('Invalid Markdown'), _tr('Please keep the "# Header" lines unchanged.'))
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
		if self._collection_preview_mode:
			self._update_collection_html_preview()

	def _toggle_collection_view_mode(self, checked):
		current_widget = self.collection_view_stack.currentWidget()
		self._collection_scroll_ratio = self._collection_get_scroll_ratio(current_widget)
		self._collection_preview_mode = checked
		if self._collection_preview_mode:
			self._update_collection_html_preview()
			self.collection_view_stack.setCurrentWidget(self.collection_md_preview)
			self.collection_view_toggle_btn.setText(_tr('Edit'))
			self._collection_apply_scroll_ratio(self.collection_md_preview, self._collection_scroll_ratio)
		else:
			self.collection_view_stack.setCurrentWidget(self.collection_md_editor)
			self.collection_view_toggle_btn.setText(_tr('Preview'))
			self._collection_apply_scroll_ratio(self.collection_md_editor, self._collection_scroll_ratio)
		self._position_collection_toggle_button()
		self.collection_view_toggle_btn.raise_()

	def _collection_get_scroll_ratio(self, widget):
		bar = widget.verticalScrollBar()
		maximum = bar.maximum()
		if maximum <= 0:
			return 0.0
		return bar.value() / maximum

	def _collection_apply_scroll_ratio(self, widget, ratio):
		bar = widget.verticalScrollBar()
		maximum = bar.maximum()
		if maximum <= 0:
			return
		bar.setValue(int(maximum * ratio))

	def _position_collection_toggle_button(self):
		if not hasattr(self, 'collection_view_toggle_btn') or not hasattr(self, 'collection_view_stack'):
			return
		margin = 12
		btn = self.collection_view_toggle_btn
		stack = self.collection_view_stack
		btn.move(stack.width() - btn.width() - margin, margin)
		btn.raise_()

	def md2html(self, mdstr, pre_rendered_html=None):
		"""The Collection page's preview page. Formulas vs. the dollar sign, the newer Markdown forms
		(==highlight==, task lists, "+ " lists), the style sheet and the MathJax part come from
		markdown_preview.py (the copy shared with Watermelon and Strawberry; the formula part is Broccoli's code).
		2026-11-20, Ryan: "渲染…该更新的就更新"; "Tomato 的也跟着一起改" (formulas typeset: the preview is a web page)."""
		body = markdown_preview.render_markdown_body(mdstr) if pre_rendered_html is None else pre_rendered_html
		return markdown_preview.preview_page(
			body, font_family='Helvetica Neue', font_size=14, background='#F3F2EE', text_color='#000000', dark=False,
			extra_css='    body { margin: 8px 20px 8px 8px; line-height: 1.5; }')

	def _open_collection_dir(self):
		if os.path.isdir(self.fulldir_collection):
			try:
				subprocess.call(['open', self.fulldir_collection])
			except Exception:
				pass

	def _collect_copy_to_time(self):
		row = self.collection_table.currentRow()
		if row < 0:
			tomato_alert(self, _tr('Select a row'), _tr('Please select a row in the table first.'))
			return
		name_item = self.collection_table.item(row, 0)
		if name_item is None or name_item.text().strip() == '':
			tomato_alert(self, _tr('Missing name'), _tr('The first column is empty. Please provide a task name.'))
			return
		item_name = name_item.text().strip()
		selected_date = self.collect_date_edit.date()
		selected_time = self.collect_time_edit.time()
		if not (selected_date.isValid() and selected_time.isValid()):
			tomato_alert(self, _tr('Missing time'), _tr('Please choose a valid date and time.'))
			return
		time_text = f"{selected_date.toString('yyyy-MM-dd')} {selected_time.toString('HH:mm')}"
		try:
			stamp_value = str(self.to_stamp(time_text))
		except Exception:
			tomato_alert(self, _tr('Invalid time'), _tr('Please choose a valid date and time.'))
			return
		length_hours = self._convert_value_to_hours(self.collect_length_input.text(), self.collect_length_unit)
		if length_hours is None:
			tomato_alert(self, _tr('Invalid length'), _tr('Please enter a valid length.'))
			return
		repeat_hours = '-'
		repeat_text = self.collect_repeat_input.text().strip()
		if repeat_text != '':
			repeat_hours = self._convert_value_to_hours(repeat_text, self.collect_repeat_unit)
			if repeat_hours is None:
				tomato_alert(self, _tr('Invalid repeat'), _tr('Please enter a valid repeat interval.'))
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

	def _on_memo_edit_started(self, row, column):
		"""Called when a cell in tableWidget_memo starts being edited (keyboard or mouse)"""
		if row < 0 or row >= self.tableWidget_memo.rowCount():
			return
		self.memo_dou = 1
		self.memo_changing_row = row
		self.memo_changing_column = column
		item4 = self.tableWidget_memo.item(row, 4)
		self.memo_changing_done = item4.text() if item4 else ''
		if self.memo_changing_done == 'UNDONE':
			self.memo_to_done = 1

	def _on_memo_edit_finished(self, row, column):
		"""Called when a cell in tableWidget_memo finishes being edited (keyboard or mouse)"""
		if self.memo_dou == 1:
			self.memo_click_write()

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
		self._clear_table_selection(self.tableWidget_memo)

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

	def _refresh_on_program_change(self, edit, refresh):
		"""`refresh` (the page's table read in again) when the program sets the box — the "setText('-');
		clear()" after Add / Done — but not on every key typed into it. Before 2026-11-22 each key read the
		whole table in twice and flipped its filter through "nothing chosen", which hid every row for a
		moment and pulled the table's scroll bar up (Ryan: "输入一些文字它就会不停地把这个滚动条往上跑").
		Typing sends textEdited before textChanged; setText sends textChanged only."""
		typed = [False]

		def edited(_text):
			typed[0] = True

		def changed(_text):
			if typed[0]:
				typed[0] = False
				return
			refresh()

		edit.textEdited.connect(edited)
		edit.textChanged.connect(changed)

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
		self._clear_table_selection(self.tableWidget_memo)

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
		self._save_diary_box(self.textii3)

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
			# Update all date and time edits to current date/time
			current_date = QDate.currentDate()
			current_time = QTime.currentTime()
			if hasattr(self, 'date_edit'):
				self.date_edit.setDate(current_date)
			if hasattr(self, 'time_edit'):
				self.time_edit.setTime(current_time)
			if hasattr(self, 'freq_date_edit'):
				self.freq_date_edit.setDate(current_date)
			if hasattr(self, 'freq_time_edit'):
				self.freq_time_edit.setTime(current_time)
			if hasattr(self, 'memo_date_edit'):
				self.memo_date_edit.setDate(current_date)
			if hasattr(self, 'memo_time_edit'):
				self.memo_time_edit.setTime(current_time)
			if hasattr(self, 'collect_date_edit'):
				self.collect_date_edit.setDate(current_date)
			if hasattr(self, 'collect_time_edit'):
				self.collect_time_edit.setTime(current_time)

			target_width = int(screen_geom.width() / 2)
			btna4.setChecked(True)
			self.tab_bar.setVisible(True)
			self.setMinimumSize(0, 0)
			self.setMaximumSize(16777215, 16777215)
			self.resize(int(target_width), DE_HEIGHT)
			self.move(0 - int(target_width) + 10, 0)
			target_x = 3
			target_y = 0
		if self.i % 2 == 0: # hide
			btna4.setChecked(False)
			self.tab_bar.setVisible(False)
			self.move(self.width() + 3, self._strip_top(screen_geom))
			self.setFixedSize(self.new_width, 120)
			target_x = 0
			target_y = self._strip_top(screen_geom)

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
			# Update all date and time edits to current date/time
			current_date = QDate.currentDate()
			current_time = QTime.currentTime()
			if hasattr(self, 'date_edit'):
				self.date_edit.setDate(current_date)
			if hasattr(self, 'time_edit'):
				self.time_edit.setTime(current_time)
			if hasattr(self, 'freq_date_edit'):
				self.freq_date_edit.setDate(current_date)
			if hasattr(self, 'freq_time_edit'):
				self.freq_time_edit.setTime(current_time)
			if hasattr(self, 'memo_date_edit'):
				self.memo_date_edit.setDate(current_date)
			if hasattr(self, 'memo_time_edit'):
				self.memo_time_edit.setTime(current_time)
			if hasattr(self, 'collect_date_edit'):
				self.collect_date_edit.setDate(current_date)
			if hasattr(self, 'collect_time_edit'):
				self.collect_time_edit.setTime(current_time)

			target_width = int(screen_geom.width() / 2)
			btna4.setChecked(True)
			self.tab_bar.setVisible(True)
			self.setMinimumSize(0, 0)
			self.setMaximumSize(16777215, 16777215)
			self.resize(int(target_width), DE_HEIGHT)
			self.move(0 - int(target_width) + 10, 0)
			target_x = 3
			target_y = 0
		if self.i % 2 == 0:
			btna4.setChecked(False)
			self.tab_bar.setVisible(False)
			self.resize(self.new_width, 120)
			self.move(self.width() + 3, self._strip_top(screen_geom))
			target_x = 0
			target_y = self._strip_top(screen_geom)

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

	# ── right-click a table row = the quick-edit card (style book 5.12, 2026-11-22) ──────────────────────
	# Ryan 2026-11-22: "选中了这一项之后呢……右键……弹出一个小小的框……在这个被点击的边上……包含这个事情的名称……
	# 时间……时长，所有那些我们一开始设置的那些框框……以比较快的速度去修改". The card holds the boxes the page
	# adds an item with; Save goes the way an edit of the table's cells goes (Reminders / Calendar follow,
	# a repeating item's time still asks "only this one / this and later ones").
	def _install_quick_edit(self):
		self._quick_edit_card = None
		for table, kind in ((self.tableWidget, 'time'), (self.tableWidget_freq, 'freq'),
							(self.tableWidget_memo, 'memo'), (self.collection_table, 'collect')):
			table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
			table.customContextMenuRequested.connect(lambda pos, t=table, k=kind: self._open_quick_edit(t, k, pos))

	def _quick_edit_open(self):
		card = getattr(self, '_quick_edit_card', None)
		return card is not None and card.isVisible()

	def _unit_for_hours(self, hours, items, fallback_index):
		"""(unit index, value text) that shows `hours` as a whole number when one unit can (2 days, 30
		minutes), else in hours."""
		for index in sorted(range(len(items)), key=lambda i: -(items[i][1] or 0)):
			factor = items[index][1]
			if not factor:
				continue
			value = hours / float(factor)
			if value >= 1 and abs(value - round(value)) < 1e-6:
				return index, str(int(round(value)))
		factor = items[fallback_index][1] or 1
		return fallback_index, tomato_ui._format_length(hours / float(factor))

	def _quick_number_row(self, card, text, unit_items, unit_index, placeholder, hours_text):
		"""A number box + its unit drop-down, filled from an hours value ('-' = empty)."""
		edit = QLineEdit(card)
		edit.setFixedHeight(GREY_ROW_HEIGHT)
		edit.setPlaceholderText(placeholder)
		unit = compact_dropdown(card)
		for label, factor in unit_items:
			unit.addItem(_tr(label), factor)
		unit.setFixedWidth(100)
		unit.setCurrentIndex(unit_index)
		try:
			hours = float(hours_text)
		except (TypeError, ValueError):
			hours = None
		if hours is not None and hours > 0:
			index, value = self._unit_for_hours(hours, unit_items, self._time_unit_hours_index)
			unit.setCurrentIndex(index)
			edit.setText(value)
		return edit, unit

	def _style_card_boxes(self, card):
		for field in card.findChildren(QDateEdit):
			style_date_time_field(field, 'calendar')
			glass_calendar_popup(field)
		for field in card.findChildren(QTimeEdit):
			style_date_time_field(field, 'clock')

	def _open_quick_edit(self, table, kind, pos):
		row = table.rowAt(pos.y())
		if row < 0 or table.isRowHidden(row) or getattr(self, '_sync_counter', 0) > 0:
			return None
		if kind == 'collect' and table.columnCount() == 0:
			return None
		if self._quick_edit_open():
			self._quick_edit_card.reject()
		table.selectRow(row)
		card = QuickEditCard(_tr('Edit item'), self)
		builder = {'time': self._quick_time_fields, 'freq': self._quick_freq_fields,
				   'memo': self._quick_memo_fields, 'collect': self._quick_collect_fields}[kind]
		if not builder(card, table, row):
			card.deleteLater()
			return None
		self._style_card_boxes(card)
		card.allowed_windows = [tomato_ui.calendar_popup()] + list(getattr(card, '_clocks', []))
		card.finished.connect(lambda _result, c=card: self._quick_edit_closed(c))
		cell = table.visualRect(table.model().index(row, 0))
		viewport = table.viewport()
		row_rect = QRect(viewport.mapToGlobal(QPoint(0, cell.top())), QSize(viewport.width(), cell.height()))
		card.place_at(row_rect, viewport.mapToGlobal(pos).x())
		self._quick_edit_card = card
		card.show()
		card.raise_()
		card.activateWindow()
		first = getattr(card, '_first_box', None)
		if first is not None:
			first.setFocus()
			first.selectAll()
		return card

	def _quick_edit_closed(self, card):
		for time_edit in card.findChildren(QTimeEdit):
			self._detach_clock(time_edit)
		if getattr(self, '_quick_edit_card', None) is card:
			self._quick_edit_card = None
		card.deleteLater()

	def _quick_name_box(self, card, text):
		name = QLineEdit(card)
		name.setFixedHeight(GREY_ROW_HEIGHT)
		name.setPlaceholderText(_tr('Item'))
		name.setText(text)
		card._first_box = name
		card.body.addWidget(name)
		return name

	@staticmethod
	def _hbox(*widgets, stretch_last=False):
		row = QHBoxLayout()
		row.setContentsMargins(0, 0, 0, 0)
		for widget in widgets:
			if isinstance(widget, int):
				row.addStretch(widget)
			else:
				row.addWidget(widget)
		return row

	def _cell_text(self, table, row, column, default='-'):
		item = table.item(row, column)
		return item.text() if item is not None and item.text() != '' else default

	def _quick_time_fields(self, card, table, row):
		name_text = self._cell_text(table, row, 0, '')
		time_text = self._cell_text(table, row, 1, '')
		if not self._time_text_ok(time_text):
			return False
		stamp = self._stamp_from_items(table.item(row, 8), table.item(row, 1))
		card._key = (name_text, stamp)
		card._old = {0: name_text, 1: time_text, 2: self._cell_text(table, row, 2), 3: self._cell_text(table, row, 3),
					 6: self._cell_text(table, row, 6)}
		name = self._quick_name_box(card, name_text)
		start = datetime.datetime.strptime(time_text, '%Y-%m-%d %H:%M')
		start_date = QDateEdit(card)
		start_date.setDisplayFormat('yyyy-MM-dd')
		start_date.setDate(QDate(start.year, start.month, start.day))
		start_date.setFixedSize(118, GREY_ROW_HEIGHT)
		start_date.setToolTip(_tr('Choose Date'))
		start_time = QTimeEdit(card)
		start_time.setDisplayFormat('HH:mm')
		start_time.setTime(QTime(start.hour, start.minute))
		start_time.setFixedSize(76, GREY_ROW_HEIGHT)
		start_time.setToolTip(_tr('Hover to open clock picker'))
		length, length_unit = self._quick_number_row(card, card._old[2], self._time_unit_items, self._time_unit_hours_index,
													 _tr('Length'), card._old[2])
		repeat, repeat_unit = self._quick_number_row(card, card._old[3], self._repeat_unit_items,
													 self._time_unit_hours_index + 1, _tr('Repeat'), card._old[3])
		arrow, end_date, end_time = end_time_boxes(card, start_date, start_time)
		card._clocks = [self._attach_clock(start_time), self._attach_clock(end_time)]
		card._link = EndTimeLink(start_date, start_time, length, length_unit, end_date, end_time, self._time_unit_hours_index)
		until_check = QCheckBox(_tr('Repeat until'), card)
		until_date = QDateEdit(card)
		until_date.setDisplayFormat('yyyy-MM-dd')
		until_date.setFixedSize(118, GREY_ROW_HEIGHT)
		until_stamp = card._old[6]
		try:
			until = datetime.datetime.fromtimestamp(float(until_stamp))
			until_date.setDate(QDate(until.year, until.month, until.day))
			until_check.setChecked(True)
		except (TypeError, ValueError, OverflowError, OSError):
			until_date.setDate(QDate.currentDate())
			until_check.setChecked(False)
		until_date.setEnabled(until_check.isChecked())
		until_check.toggled.connect(lambda _on: self._apply_repeat_until_enable(until_check, until_date))
		card.body.addLayout(self._hbox(start_date, start_time, arrow, end_date, end_time, 1))
		row3 = self._hbox(length, length_unit, repeat, repeat_unit)
		row3.setStretch(0, 1)
		row3.setStretch(2, 1)
		card.body.addLayout(row3)
		card.body.addLayout(self._hbox(until_check, until_date, 1))
		card._boxes = dict(name=name, start_date=start_date, start_time=start_time, length=length, length_unit=length_unit,
						   repeat=repeat, repeat_unit=repeat_unit, until_check=until_check, until_date=until_date)
		card.validate = lambda c=card: self._quick_time_values(c)[1]
		card.accepted.connect(lambda c=card: self._save_quick_time(c))
		return True

	def _quick_time_values(self, card):
		"""({column: new text}, problem text)."""
		box = card._boxes
		name = box['name'].text().replace('\n', ' ').strip()
		if not name:
			return {}, _tr('Please enter the item name.')
		when = '%s %s' % (box['start_date'].date().toString('yyyy-MM-dd'), box['start_time'].time().toString('HH:mm'))
		old_length = card._old[2]
		if box['length'].text().strip() == '' and old_length in ('', '-'):
			length = old_length
		else:
			length = self._convert_value_to_hours(box['length'].text(), box['length_unit'])
			if length is None:
				return {}, _tr('Please enter a valid length.')
		repeat = '-'
		if box['repeat'].text().strip() not in ('', '-'):
			repeat = self._convert_value_to_hours(box['repeat'].text(), box['repeat_unit'])
			if repeat is None:
				return {}, _tr('Please enter a valid repeat.')
		until = self._get_repeat_until_stamp(box['until_check'], box['until_date'])
		return {0: name, 1: when, 2: str(length), 3: str(repeat), 6: until}, ''

	def _save_quick_time(self, card):
		values, problem = self._quick_time_values(card)
		if problem:
			return
		self._apply_time_changes(card._key, values)

	def _apply_time_changes(self, key, values):
		"""{column: new text} for the row (name, stamp), one cell at a time through the same path as an edit by hand."""
		name, stamp = key
		keep_repeat, keep_comment = self.le4.text(), self.textw1.toPlainText()     # an edit's save empties these
		stamps = [stamp]
		for column in (0, 1, 2, 3, 6):
			if column not in values:
				continue
			new = values[column]
			row = None
			for candidate in stamps:
				row = self._find_time_row_by_key(name, candidate)
				if row is not None:
					break
			if row is None:
				logging.warning('Quick edit: the row of %r is gone; the rest is not saved.', name)
				break
			item = self.tableWidget.item(row, column)
			if item is None:
				item = QTableWidgetItem('')
				item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
				self.tableWidget.setItem(row, column, item)
			if item.text() == new:
				continue
			self._on_table_edit_started(row, column)
			item.setText(new)
			self.write_table_time()
			if column == 0:
				name = new
			elif column == 1:
				stamps = [self._normalize_stamp(self.to_stamp(new)), stamp]
		self.le4.setText(keep_repeat)
		if keep_comment:
			self.textw1.setPlainText(keep_comment)

	def _find_row_of(self, table, kind, name, stamp):
		for row in range(table.rowCount()):
			type_item, name_item = table.item(row, 7), table.item(row, 0)
			if type_item is None or name_item is None or type_item.text() != kind:
				continue
			if name_item.text() == name and self._stamp_from_items(table.item(row, 8), table.item(row, 1)) == stamp:
				return row
		return None

	def _quick_freq_fields(self, card, table, row):
		name_text = self._cell_text(table, row, 0, '')
		card._key = (name_text, self._stamp_from_items(table.item(row, 8), table.item(row, 1)))
		name = self._quick_name_box(card, name_text)
		target, progress = QLineEdit(card), QLineEdit(card)
		for box, value, hint in ((target, self._cell_text(table, row, 5), _tr('Target times')),
								 (progress, self._cell_text(table, row, 6), _tr('Done times'))):
			box.setFixedHeight(GREY_ROW_HEIGHT)
			box.setPlaceholderText(hint)
			box.setToolTip(hint)
			box.setText('' if value == '-' else value)
		card.body.addLayout(self._hbox(target, progress))
		card._boxes = dict(name=name, target=target, progress=progress)
		card.validate = lambda c=card: self._quick_freq_values(c)[1]
		card.accepted.connect(lambda c=card: self._save_quick_freq(c))
		return True

	def _quick_freq_values(self, card):
		box = card._boxes
		name = box['name'].text().replace('\n', ' ').strip()
		if not name:
			return {}, _tr('Please enter the item name.')
		numbers = []
		for key in ('target', 'progress'):
			text = box[key].text().strip() or '0'
			if not text.isdigit():
				return {}, _tr('Target and done times must be whole numbers.')
			numbers.append(str(int(text)))
		return {0: name, 5: numbers[0], 6: numbers[1]}, ''

	def _save_quick_freq(self, card):
		values, problem = self._quick_freq_values(card)
		if problem:
			return
		self._apply_freq_changes(card._key, values)

	def _apply_freq_changes(self, key, values):
		name, stamp = key
		for column in (0, 5, 6):
			if column not in values:
				continue
			row = self._find_row_of(self.tableWidget_freq, 'FREQ_SNS', name, stamp)
			if row is None:
				break
			item = self.tableWidget_freq.item(row, column)
			if item is None or item.text() == values[column]:
				continue
			self._on_freq_edit_started(row, column)
			item.setText(values[column])
			self.freq_write_time()
			if column == 0:
				name = values[0]

	def _quick_memo_fields(self, card, table, row):
		name_text = self._cell_text(table, row, 0, '')
		card._key = (name_text, self._stamp_from_items(table.item(row, 8), table.item(row, 1)))
		name = self._quick_name_box(card, name_text)
		card._boxes = dict(name=name)
		card.validate = lambda c=card: '' if c._boxes['name'].text().strip() else _tr('Please enter the item name.')
		card.accepted.connect(lambda c=card: self._save_quick_memo(c))
		return True

	def _save_quick_memo(self, card):
		self._apply_memo_name(card._key, card._boxes['name'].text())

	def _apply_memo_name(self, key, new):
		new = new.replace('\n', ' ').strip()
		name, stamp = key
		row = self._find_row_of(self.tableWidget_memo, 'MEMO_SNS', name, stamp)
		if not new or row is None:
			return
		item = self.tableWidget_memo.item(row, 0)
		if item is None or item.text() == new:
			return
		self._on_memo_edit_started(row, 0)
		item.setText(new)
		self.memo_click_write()

	def _quick_collect_fields(self, card, table, row):
		from PyQt6.QtWidgets import QGridLayout
		grid = QGridLayout()
		grid.setContentsMargins(0, 0, 0, 0)
		grid.setHorizontalSpacing(8)
		grid.setVerticalSpacing(6)
		boxes = []
		for column, header in enumerate(self._collection_headers()):
			label = QLabel(header, card)
			label.setStyleSheet('color: #8E8E93; font-size: 12px; background: transparent;')
			label.setMaximumWidth(120)
			box = QLineEdit(card)
			box.setFixedHeight(GREY_ROW_HEIGHT)
			box.setText(self._collection_item_text(row, column))
			grid.addWidget(label, column, 0)
			grid.addWidget(box, column, 1)
			boxes.append(box)
		card.body.addLayout(grid)
		card._first_box = boxes[0] if boxes else None
		card._row = row
		card._boxes = boxes
		card.validate = lambda c=card: ''
		card.accepted.connect(lambda c=card: self._save_quick_collect(c))
		return bool(boxes)

	def _save_quick_collect(self, card):
		row = card._row
		if not (0 <= row < self.collection_table.rowCount()):
			return
		changed = False
		self._collection_table_block = True
		try:
			for column, box in enumerate(card._boxes):
				if column >= self.collection_table.columnCount():
					break
				item = self.collection_table.item(row, column)
				if item is None:
					item = QTableWidgetItem('')
					self.collection_table.setItem(row, column, item)
				if item.text() != box.text():
					item.setText(box.text())
					changed = True
		finally:
			self._collection_table_block = False
		if changed:
			self._save_collection_file()
			self._update_collection_markdown_preview()

	# ── what Broccoli's background vision saw, into the diary (tomato_feed.py, 2026-11-23) ───────────────
	VISION_LINE_MAX_CHARS = 80      # Ryan: "不要写太长吧，就简短一点就好"

	def _start_feed_watcher(self, data_dir=None):
		if self._feed_watcher is not None:
			return
		data_dir = data_dir if data_dir is not None else tomato_broccoli.broccoli_data_dir()
		if not os.path.isdir(data_dir):
			return                          # no Broccoli on this Mac: nothing to wait for (looked at again at the next start)
		self._feed_watcher = tomato_feed.make_watcher(
			data_dir, lambda: self._app_settings.get('feed_state'), self._save_feed_state, self._feed_arrived, self)

	def _save_feed_state(self, state):
		if self._app_settings.get('feed_state') != state:
			self._app_settings['feed_state'] = state
			self._save_app_settings()

	def _feed_arrived(self, entries):
		"""One line per look, at the time of the look (Ryan: "多久有一次视觉，那就是多久记一次"). Switched off in the
		menu: the entries are passed over, not kept for later. Only today's and yesterday's are written."""
		if not self._app_settings.get('vision_to_diary', True):
			return
		oldest = datetime.datetime.now() - datetime.timedelta(days=1)
		wrote = False
		for entry in entries:
			when = tomato_feed.entry_time(entry)
			if entry.get('kind') != 'vision' or when < oldest:
				continue
			tomato_diary.append_line(self.fulldir_dia, tomato_diary.VISION_MARK + ' ' + entry['text'], when, self.VISION_LINE_MAX_CHARS + 2)
			wrote = True
		if wrote:
			self._refresh_unfocused_diary_boxes()

	def set_vision_to_diary(self, checked):
		self._app_settings['vision_to_diary'] = bool(checked)
		self._save_app_settings()

	# ── the reports (tomato_report.py, 2026-11-23; weekly / monthly and the report language 2026-11-24) ──────────
	# The numbers are Tomato's own and always there; the written part comes from Broccoli when it is on this Mac.
	# Reports are due at 23:30 (one single-shot timer set for that moment, as the Broccoli link does — nothing
	# looks at the clock in between) and, for one that was missed, at the next start.
	REPORT_WAIT_SECONDS = 15 * 60

	def _report_labels(self):
		return {'title': _tr('Daily report'), 'title_week': _tr('Weekly report'), 'title_month': _tr('Monthly report'),
				'apps': _tr('Time per app'), 'timeline': _tr('Timeline'), 'also': _tr('also'),
				'taken': _tr('From the Collections'), 'total': _tr('Total'), 'items': _tr('Items'), 'notes': _tr('Own notes'),
				'numbers': _tr('The numbers'), 'nothing': _tr('Nothing was recorded on this day.'),
				'nothing_period': _tr('Nothing was recorded in this period.'), 'app': _tr('App'), 'length': _tr('Length'),
				'per_day': _tr('Day by day'), 'day': _tr('Day'), 'mostly': _tr('Mostly')}

	def _report_facts(self, day):
		now = datetime.datetime.now()
		end = now.hour * 3600 + now.minute * 60 + now.second if day == tomato_diary.day_name() else None
		return tomato_report.build_facts(tomato_diary.read(self.fulldir_dia, day), self.fulldir_collection, end)

	def _report_period_facts(self, kind, key):
		return tomato_report.period_facts(kind, key, self._report_facts)

	def report_auto(self):
		return bool(self._app_settings.get('daily_report', True))

	def set_report_auto(self, on):
		self._app_settings['daily_report'] = bool(on)
		self._save_app_settings()
		self._report_time_came()

	def report_languages(self):
		"""(the languages the person keeps, the one in use). Until one is picked: the one of the interface."""
		languages = tomato_report.normalize_languages(self._app_settings.get('report_languages'))
		current = ' '.join(str(self._app_settings.get('report_language') or '').split())
		if current not in languages:
			current = tomato_report.default_language(UI_LANGUAGE, languages)
		return languages, current

	def set_report_language(self, language):
		languages, _current = self.report_languages()
		if language in languages and self._app_settings.get('report_language') != language:
			self._app_settings['report_language'] = language
			self._save_app_settings()

	def set_report_languages(self, languages, current):
		languages = tomato_report.normalize_languages(languages)
		self._app_settings['report_languages'] = languages
		self._app_settings['report_language'] = current if current in languages else languages[0]
		self._save_app_settings()

	def _report_time_came(self):
		"""23:30 came, Tomato started, or the switch was turned: make the reports that are due, set the timer for
		the next 23:30 (a far time is approached in steps; waking up late still lands here)."""
		self._report_timer.stop()
		if not self.report_auto():
			return
		try:
			for kind, key in tomato_report.due_reports(TOMATO_DATA_DIR, self.fulldir_dia):
				self.make_report(kind, key)
		except Exception:
			logging.exception('The reports could not be made.')
		self._report_timer.start(int(min(tomato_report.seconds_to_next() + 2, 6 * 3600) * 1000))

	def make_report(self, kind, key=None):
		"""The numbers at once; then, with Broccoli on this Mac, the written part is asked for in the background.
		(make_report(day) alone = that day's daily report.)"""
		if key is None:
			kind, key = 'day', kind
		kind = tomato_report.kind_of(kind)
		key = tomato_report.valid_key(kind, key)
		if not key:
			return False
		facts = self._report_period_facts(kind, key)
		if facts['empty']:
			return False
		_languages, language = self.report_languages()
		template, own = tomato_report.read_template(TOMATO_DATA_DIR, kind, language)
		meta = {'language': language, 'template': 'own' if own else 'default'}
		tomato_report.save_report(TOMATO_DATA_DIR, key, tomato_report.numbers_report(kind, key, facts, self._report_labels(), meta), kind)
		if tomato_broccoli.broccoli_installed():
			prompt = tomato_report.prompt(kind, key, template, facts, language)
			self._report_waiting[(kind, key)] = (time.time(), meta)
			title = _tr('Daily report')                 # the Broccoli group all reports go into
			name = {'day': _tr('Daily report'), 'week': _tr('Weekly report'), 'month': _tr('Monthly report')}[kind] + ' ' + key
			sender = self._report_sender

			def work():
				try:
					ok, reason = sender(name, int(time.time()), prompt, title=title)
				except Exception as exc:
					ok, reason = False, str(exc)
				if not ok:
					logging.warning('Report %s %s: Broccoli could not be asked (%s); the numbers stay.', kind, key, reason)
					self._main_runner.post(lambda: self._report_asked_failed(kind, key))
			threading.Thread(target=work, name='tomato-report', daemon=True).start()
			QTimer.singleShot(int(self.REPORT_WAIT_SECONDS * 1000) + 500, lambda: self._report_refresh(kind, key))
		self._report_refresh(kind, key)
		return True

	def _report_asked_failed(self, kind, key):
		self._report_waiting.pop((kind, key), None)
		self._report_refresh(kind, key)

	def _report_refresh(self, kind, key):
		if self._report_dialog is not None and self._report_dialog.isVisible():
			self._report_dialog.refresh(kind, key)

	def report_status(self, kind, key=None):
		if key is None:
			kind, key = 'day', kind
		asked = self._report_waiting.get((kind, key))
		if asked is None:
			return ''
		if time.time() - asked[0] > self.REPORT_WAIT_SECONDS:
			self._report_waiting.pop((kind, key), None)
			return ''
		return _tr('Broccoli is writing…')

	def report_text(self, kind, key=None):
		if key is None:
			kind, key = 'day', kind
		return tomato_report.read_report(TOMATO_DATA_DIR, key, kind)

	def report_has_record(self, kind, key):
		if kind == 'day':
			return tomato_report.has_record(self.fulldir_dia, key) and not self._report_facts(key)['empty']
		return any(tomato_report.has_record(self.fulldir_dia, day) for day in tomato_report.period_days(kind, key))

	def report_slots(self, days):
		"""Worker thread: the calendar's days (files only)."""
		return tomato_report.day_slots(self.fulldir_dia, days, self._report_slot_cache)

	def report_streak(self, today):
		return tomato_report.streak(self.fulldir_dia, today)

	def report_html(self, markdown_text):
		return self.md2html(markdown_text or '')

	def report_template(self, kind='day'):
		_languages, language = self.report_languages()
		return tomato_report.read_template(TOMATO_DATA_DIR, kind, language)[0], tomato_report.default_template(kind, language)

	def save_report_template(self, kind, text):
		tomato_report.write_template(TOMATO_DATA_DIR, kind, text)
		self._report_refresh(None, None)

	def open_daily_report(self, day=None, kind=None):
		if self._report_dialog is None:
			self._report_dialog = tomato_report_ui.ReportDialog(self, None)
		if day is not None or kind is not None:
			self._report_dialog.show_day(day or tomato_diary.day_name(), kind)
		else:
			self._report_dialog.refresh()
		self._report_dialog.show()
		self._report_dialog.raise_()
		return self._report_dialog

	def _tool_report_key(self, a):
		kind = str(a.get('kind') or 'day')
		if kind not in tomato_report.KINDS:
			raise tomato_tools.ToolError('"kind" is day, week or month.')
		if kind == 'day':
			return kind, self._tool_day(a)
		key = tomato_report.valid_key(kind, a.get('day') or tomato_diary.day_name())
		if not key:
			raise tomato_tools.ToolError('"day" is written "YYYY-MM-DD" (a week: any day of it) or "YYYY-MM" (a month).')
		return kind, key

	def _tool_read_report(self, a):
		kind, key = self._tool_report_key(a)
		text, _mark, _meta = tomato_report.read_report(TOMATO_DATA_DIR, key, kind)
		return text or 'There is no %s report for %s yet.' % (tomato_report.KIND_WORDS[kind], key)

	def _tool_save_report(self, a):
		kind, key = self._tool_report_key(a)
		text = str(a.get('text') or '').strip()
		if len(text) < 20 or len(text) > tomato_report.MAX_REPORT_CHARS:
			raise tomato_tools.ToolError('"text" is the whole report, as Markdown.')
		facts = self._report_period_facts(kind, key)
		if facts['empty']:
			raise tomato_tools.ToolError('Nothing was recorded in %s, so there is no report to save.' % key)
		asked = self._report_waiting.pop((kind, key), None)
		meta = asked[1] if asked else tomato_report.read_report(TOMATO_DATA_DIR, key, kind)[2]
		tomato_report.save_report(TOMATO_DATA_DIR, key, tomato_report.written_report(kind, key, text, facts, self._report_labels(), meta), kind)
		self._report_refresh(kind, key)
		return 'Saved the %s report of %s.' % (tomato_report.KIND_WORDS[kind], key)

	def _tool_create_report_picture(self, a):
		"""The report as one long picture (what the report window's Share makes), saved as a PNG."""
		kind, key = self._tool_report_key(a)
		text, _mark, _meta = tomato_report.read_report(TOMATO_DATA_DIR, key, kind)
		if not (text or '').strip():
			raise tomato_tools.ToolError('There is no %s report for %s yet.' % (tomato_report.KIND_WORDS[kind], key))
		target = str(a.get('path') or '').strip()
		if target:
			target = os.path.expanduser(target)
			if not os.path.isabs(target) or not target.lower().endswith('.png') or not os.path.isdir(os.path.dirname(target)):
				raise tomato_tools.ToolError('"path" is an absolute path ending in .png, in a folder that exists.')
			if os.path.exists(target):
				raise tomato_tools.ToolError('There is already a file at %s.' % target)
		else:
			folder = os.path.join(os.path.expanduser('~'), 'Downloads')
			os.makedirs(folder, exist_ok=True)
			stem, number = 'Tomato-report-%s' % key, 1
			target = os.path.join(folder, stem + '.png')
			while os.path.exists(target):
				number += 1
				target = os.path.join(folder, '%s %d.png' % (stem, number))
		maker = share_picture.SharePictureMaker(self)
		got, loop = [], QEventLoop()
		maker.finished.connect(lambda pixmap: (got.append(pixmap), loop.quit()))
		markdown = '## %s\n\n%s' % (tomato_report.period_label(kind, key), text)
		if not maker.make(self.report_html(markdown), None, 720, False):
			raise tomato_tools.ToolError('The picture could not be started.')
		QTimer.singleShot(90000, loop.quit)
		loop.exec()                    # the window keeps answering while the page is photographed
		maker.deleteLater()
		if not got or got[0] is None or got[0].isNull() or not got[0].save(target, 'PNG'):
			raise tomato_tools.ToolError('The picture could not be made.')
		return 'Saved a picture of the %s report of %s (%d × %d pixels): %s' % (
			tomato_report.KIND_WORDS[kind], key, got[0].width(), got[0].height(), target)

	# ── Tomato's functions as tools for an assistant app (2026-11-23) ────────────────────────────────────
	# Ryan 2026-11-23: "把 Tomato 的所有的这些功能全部都暴露给 Broccoli，作为一个 MCP，他自动就挂上去了". Tomato runs
	# a small MCP service on this Mac only (app_mcp_host.py, the file every app of the family carries) and leaves
	# its card in the family's AppConnectors folder; Broccoli reads the folder — neither names the other in a list
	# of apps. Every call runs here on the main thread, through the same paths as the same change made by hand
	# (the table, All.csv, Reminders and Calendar stay in step); the service's thread only waits.
	# 2026-11-24 (Ryan: "接口通用，别的也能接"): the service always starts, Broccoli or not; any other AI app reaches
	# it through the bridge (Tomato started with --mcp-stdio; the menu's "Use in other AI apps…" copies the setup).
	def _start_tools_service(self, card_dir=None):
		if getattr(self, '_tools_host', None) is not None:
			return True
		host = app_mcp_host.AppMcpHost(
			TOMATO_BUNDLE_ID, 'Tomato', VERSION,
			description='The person\'s to-do items (timed, counted, memos), their diary of the day, their Collections (tables: recipes, books, …) and their daily / weekly / monthly reports.',
			instructions='Tomato keeps the person\'s items (page "time": things with a start time; "frequency": things to do N times; '
						 '"memory": memos), a diary file per day, and Collections (tables with free columns). Look before you '
						 'change: list / search first, and say what you are going to change. Times are local, "YYYY-MM-DD HH:MM".')
		obj = lambda **properties: {'type': 'object', 'properties': properties}
		text = lambda description: {'type': 'string', 'description': description}
		number = lambda description: {'type': 'number', 'description': description}
		page = {'type': 'string', 'enum': ['time', 'frequency', 'memory'], 'description': 'Which page the item is on.'}
		which = dict(page=page, name=text('The item\'s name, exactly as listed.'),
					 start=text('For a timed item: its start "YYYY-MM-DD HH:MM", when several items share the name.'))
		scope = {'type': 'string', 'enum': ['one', 'later'], 'description': 'For a repeating timed item, when its start is moved or it is deleted: only this one (default) or this and the later ones. (A new name or length always goes to its later ones too, as in the app.)'}
		collection = text('The collection\'s name (list_collections).')
		values = {'type': 'object', 'description': 'Column name → text.', 'additionalProperties': {'type': 'string'}}
		add_columns = {'type': 'boolean', 'description': 'Add columns that are not there yet. Ask the person first.'}
		host.tool('list_items', 'Lists the person\'s items. status: undone (default) / done / all. text: part of the name. '
				  'start_from / start_to: "YYYY-MM-DD" bounds for timed items.',
				  obj(page={'type': 'string', 'enum': ['all', 'time', 'frequency', 'memory']}, status={'type': 'string', 'enum': ['undone', 'done', 'all']},
					  text=text('Part of the name.'), start_from=text('YYYY-MM-DD'), start_to=text('YYYY-MM-DD'), limit=number('At most this many (50).')),
				  self._tool_list_items)
		host.tool('create_item', 'Adds an item. time: name + start (+ length_hours, default 1; repeat_hours; repeat_until "YYYY-MM-DD"). '
				  'frequency: name + target_times. memory: name only.',
				  dict(obj(page=page, name=text('The item\'s name.'), start=text('"YYYY-MM-DD HH:MM" (time page).'),
						   length_hours=number('How long, in hours.'), repeat_hours=number('Repeat every this many hours.'),
						   repeat_until=text('Last day of the repeat, "YYYY-MM-DD".'), target_times=number('How many times (frequency page).')),
					   required=['page', 'name']), self._tool_create_item, mutating=True)
		host.tool('update_item', 'Changes an item: new_name; for a timed item also new_start, length_hours, repeat_hours; for a counted '
				  'item target_times, done_times.',
				  dict(obj(new_name=text('The new name.'), new_start=text('"YYYY-MM-DD HH:MM"'), length_hours=number('Hours.'),
						   repeat_hours=number('Hours; 0 = no repeat.'), target_times=number('Target count.'), done_times=number('Count done.'),
						   scope=scope, **which), required=['page', 'name']), self._tool_update_item, mutating=True)
		host.tool('update_item_done', 'Marks an item as done (time, memory), or counts one more time for a counted item (frequency). '
				  'comment: an optional note kept with it.',
				  dict(obj(comment=text('A note.'), **which), required=['page', 'name']), self._tool_complete_item, mutating=True)
		host.tool('delete_item', 'Deletes an item. Ask the person first.',
				  dict(obj(scope=scope, **which), required=['page', 'name']), self._tool_delete_item, destructive=True)
		host.tool('read_diary', 'The diary of a day (default today). form "summary" (default): time per app, the stretches of the day, what '
				  'was seen on screen, what was taken from the Collections (meals …), finished items, the person\'s own notes. '
				  'form "full": the file as it is (long).',
				  obj(day=text('YYYY-MM-DD'), form={'type': 'string', 'enum': ['summary', 'full']}), self._tool_read_diary)
		host.tool('write_diary_line', 'Adds one line to today\'s diary, stamped with the time. Either free text, or a row of a Collection '
				  '(collection + row, e.g. a dish the person ate — search_collection first) with an optional note ("half a portion"). '
				  'time "HH:MM": when it happened, if not now.',
				  obj(text=text('Free text for the line.'), collection=collection, row=number('The row number from search_collection.'),
					  note=text('A short note after the row\'s name.'), time=text('HH:MM today.')), self._tool_write_diary_line, mutating=True)
		host.tool('list_collections', 'The person\'s Collections: name, columns, number of rows.', obj(), self._tool_list_collections)
		host.tool('search_collection', 'Rows of a collection that hold every word of "text" (no text: the first rows). Gives row numbers.',
				  dict(obj(collection=collection, text=text('Words to look for.'), limit=number('At most this many (20).')), required=['collection']),
				  self._tool_search_collection)
		host.tool('read_collection_row', 'One row in full.', dict(obj(collection=collection, row=number('Row number.')), required=['collection', 'row']),
				  self._tool_read_collection_row)
		host.tool('create_collection_row', 'Adds a row to a collection.',
				  dict(obj(collection=collection, values=values, add_missing_columns=add_columns), required=['collection', 'values']),
				  self._tool_create_collection_row, mutating=True)
		host.tool('update_collection_row', 'Writes cells of one row (e.g. the nutrition of a dish); other cells stay.',
				  dict(obj(collection=collection, row=number('Row number.'), values=values, add_missing_columns=add_columns),
					   required=['collection', 'row', 'values']), self._tool_update_collection_row, mutating=True)
		host.tool('delete_collection_row', 'Deletes one row. Ask the person first.',
				  dict(obj(collection=collection, row=number('Row number.')), required=['collection', 'row']),
				  self._tool_delete_collection_row, destructive=True)
		host.tool('create_collection', 'Makes a new, empty collection with these columns.',
				  dict(obj(collection=collection, columns={'type': 'array', 'items': {'type': 'string'}}), required=['collection', 'columns']),
				  self._tool_create_collection, mutating=True)
		report_kind = {'type': 'string', 'enum': ['day', 'week', 'month'], 'description': 'day (default), week (Monday–Sunday) or month.'}
		report_day = text('YYYY-MM-DD; for a week any day of it (its Monday is used), for a month YYYY-MM.')
		host.tool('read_daily_report', 'The daily, weekly or monthly report (default: today\'s daily report), if there is one.',
				  obj(kind=report_kind, day=report_day), self._tool_read_report)
		# Not marked as a change that needs the person's approval: it only puts the written half of a report into
		# Tomato's own Reports folder (the report before it is kept), and it is asked for every night at 23:30 —
		# an approval window then would stop the report nobody is there to approve.
		host.tool('save_daily_report', 'Saves the written part of a daily, weekly or monthly report (Markdown). Tomato adds its own numbers under it. '
				  'Use it only when asked for such a report.',
				  dict(obj(kind=report_kind, day=report_day, text=text('The whole report, Markdown.')), required=['day', 'text']), self._tool_save_report)
		host.tool('create_daily_report', 'Makes the daily, weekly or monthly report now (default: today\'s daily report): Tomato\'s numbers at once; '
				  'the written part is asked from the person\'s assistant app when there is one (that uses their model). Replaces the report of that period.',
				  obj(kind=report_kind, day=report_day), self._tool_create_report, mutating=True)
		host.tool('create_report_picture', 'Saves a daily, weekly or monthly report (default: today\'s daily report) as one long picture (PNG) for '
				  'sharing — what "Share" in the Reports window makes. Without "path" it goes into the Downloads folder; an existing file is never replaced.',
				  obj(kind=report_kind, day=report_day, path=text('Where to save it: an absolute path ending in .png. Optional.')),
				  self._tool_create_report_picture, mutating=True)
		host.tool('read_report_template', 'The template the written part of a report follows (kind: day / week / month), and whether it is the default one.',
				  obj(kind=report_kind), self._tool_read_template)
		host.tool('update_report_template', 'Replaces the template of the daily, weekly or monthly report with "text" (Markdown: the headings and what goes under each). '
				  '"" = the default template again. Show the person the new template first.',
				  dict(obj(kind=report_kind, text=text('The whole template, or "".')), required=['text']), self._tool_update_template, mutating=True)
		host.tool('search_diary', 'Diary lines of the last days that hold every word of "text" (when did I …, how often …): day + line, newest first.',
				  dict(obj(text=text('Words to look for.'), days=number('How many days back (30).'), limit=number('At most this many lines (50).')), required=['text']),
				  self._tool_search_diary)
		diary_line = text('The line as the diary has it (read_diary with form "full", or search_diary), with its time.')
		diary_day = text('YYYY-MM-DD (default today).')
		host.tool('update_diary_line', 'Corrects one line of a diary: "line" is replaced by "new_text" (keep the time at its front). For a mistake the person points out.',
				  dict(obj(day=diary_day, line=diary_line, new_text=text('The line as it should read.')), required=['line', 'new_text']),
				  self._tool_update_diary_line, mutating=True)
		host.tool('delete_diary_line', 'Takes one line out of a diary. Ask the person first.',
				  dict(obj(day=diary_day, line=diary_line), required=['line']), self._tool_delete_diary_line, destructive=True)
		column = text('The column\'s name (list_collections).')
		host.tool('create_collection_column', 'Adds an empty column to a collection (e.g. "Zinc (mg)": put the unit in the name).',
				  dict(obj(collection=collection, column=text('The new column\'s name.')), required=['collection', 'column']),
				  self._tool_create_collection_column, mutating=True)
		host.tool('update_collection_column', 'Renames a column of a collection; its cells stay.',
				  dict(obj(collection=collection, column=column, new_name=text('The new name.')), required=['collection', 'column', 'new_name']),
				  self._tool_update_collection_column, mutating=True)
		host.tool('delete_collection_column', 'Deletes a column of a collection with everything in it. Ask the person first.',
				  dict(obj(collection=collection, column=column), required=['collection', 'column']), self._tool_delete_collection_column, destructive=True)
		switch = lambda description: {'type': 'boolean', 'description': description}
		host.tool('read_settings', 'Tomato\'s switches: auto_record (the apps in use are written into the diary), auto_record_on_startup, always_on_top, '
				  'show_on_all_spaces, vision_to_diary (lines from the assistant app\'s look at the screen), report_auto (a report every evening), '
				  'repeat_pregenerate_count (how many rows a repeating item gets ahead).', obj(), self._tool_read_settings)
		host.tool('update_settings', 'Sets any of Tomato\'s switches (read_settings names them); the rest stay.',
				  obj(auto_record=switch('Record the apps in use into the diary, now.'), auto_record_on_startup=switch('Start recording when Tomato starts.'),
					  always_on_top=switch('The main window above other windows.'), show_on_all_spaces=switch('On every desktop.'),
					  vision_to_diary=switch('Write the assistant app\'s screen notes into the diary.'), report_auto=switch('Make a report every evening.'),
					  repeat_pregenerate_count=number('1–15.')), self._tool_update_settings, mutating=True)
		launch = None
		marker = '.app/Contents/MacOS/'
		if getattr(sys, 'frozen', False) and marker in sys.executable:      # the packaged app can be opened again by its card
			launch = {'bundle_id': TOMATO_BUNDLE_ID, 'path': sys.executable.split(marker)[0] + '.app'}
		try:
			started = host.start(run_on_main=self._main_runner, launch=launch, card_dir=card_dir)
		except Exception:
			logging.exception('The tools service could not be started.')
			started = False
		self._tools_host = host if started else None
		return started

	def _tools_busy(self):
		if self._broccoli_busy() or self._quick_edit_open() or self._time_cell_being_edited() \
				or self.collection_table.state() == QAbstractItemView.State.EditingState:
			raise tomato_tools.ToolError('Tomato is in the middle of an edit by the person. Try again in a moment.')

	def _tool_list_items(self, a):
		return tomato_tools.filter_items(tomato_tools.read_items(self.fulldirall), a.get('page') or 'all', a.get('status') or 'undone',
										 a.get('text') or '', a.get('start_from') or '', a.get('start_to') or '', a.get('limit') or 50)

	def _tool_stamp(self, value, what='start'):
		try:
			return int(self.to_stamp(' '.join(str(value or '').replace('T', ' ').split())[:16]))
		except Exception:
			raise tomato_tools.ToolError('"%s" is a local time written "YYYY-MM-DD HH:MM".' % what)

	def _tool_hours(self, value, what, allow_zero=False):
		try:
			hours = float(value)
		except (TypeError, ValueError):
			raise tomato_tools.ToolError('"%s" is a number of hours.' % what)
		if hours < 0 or (hours == 0 and not allow_zero) or hours > 24 * 366:
			raise tomato_tools.ToolError('"%s" is out of range.' % what)
		return hours

	def _tool_count(self, value, what):
		try:
			count = int(float(value))
		except (TypeError, ValueError):
			raise tomato_tools.ToolError('"%s" is a whole number.' % what)
		if not 0 <= count <= 100000:
			raise tomato_tools.ToolError('"%s" is out of range.' % what)
		return count

	def _tool_table(self, page):
		tables = {'time': (self.tableWidget, 'TIME_SNS'), 'frequency': (self.tableWidget_freq, 'FREQ_SNS'), 'memory': (self.tableWidget_memo, 'MEMO_SNS')}
		if page not in tables:
			raise tomato_tools.ToolError('"page" is time, frequency or memory.')
		return tables[page]

	def _tool_find_row(self, a, undone_only=False):
		"""(table, kind, row) of the item a call names; words for the model when there is none or more than one."""
		table, kind = self._tool_table(a.get('page'))
		wanted, start = ' '.join(str(a.get('name') or '').split()).casefold(), ' '.join(str(a.get('start') or '').split())
		if not wanted:
			raise tomato_tools.ToolError('"name" is the item\'s name.')
		rows = []
		for row in range(table.rowCount()):
			type_item, name_item = table.item(row, 7), table.item(row, 0)
			if type_item is None or name_item is None or type_item.text() != kind:
				continue
			if ' '.join(name_item.text().split()).casefold() != wanted:
				continue
			if start and kind == 'TIME_SNS' and not self._cell_text(table, row, 1, '').startswith(start):
				continue
			rows.append(row)
		undone = [row for row in rows if self._cell_text(table, row, 4, '') == 'UNDONE']
		if undone_only or len(undone) >= 1:
			rows = undone
		if not rows:
			raise tomato_tools.ToolError('No such item%s on the %s page. Use list_items to see the names.' % (' still to do' if undone_only else '', a.get('page')))
		if len(rows) > 1:
			if kind == 'TIME_SNS':
				rows.sort(key=lambda row: self._cell_text(table, row, 1, ''))
				if not start:
					raise tomato_tools.ToolError('Several items have this name; pass "start". Their starts: '
												 + ', '.join(self._cell_text(table, row, 1, '') for row in rows[:12]))
			rows = rows[:1]
		return table, kind, rows[0]

	def _tool_create_item(self, a):
		self._tools_busy()
		page, name = a.get('page'), ' '.join(str(a.get('name') or '').split())
		self._tool_table(page)
		if not name:
			raise tomato_tools.ToolError('"name" is the item\'s name.')
		if page == 'time':
			start = self._tool_stamp(a.get('start'))
			length = self._tool_hours(a.get('length_hours', 1) or 1, 'length_hours')
			repeat = self._tool_hours(a['repeat_hours'], 'repeat_hours') if a.get('repeat_hours') else None
			until = None
			if repeat and a.get('repeat_until'):
				try:
					day = datetime.datetime.strptime(str(a['repeat_until'])[:10], '%Y-%m-%d').date()
				except ValueError:
					raise tomato_tools.ToolError('"repeat_until" is a day written "YYYY-MM-DD".')
				until = int(datetime.datetime.combine(day, datetime.time(23, 59, 59)).timestamp())
				if until < start:
					raise tomato_tools.ToolError('"repeat_until" is before the start.')
			if self._find_time_row_by_key(name, start) is not None:
				raise tomato_tools.ToolError('There is already an item with this name at this time.')
			added = self._add_time_item(name, start, length, repeat, until)
			return {'created': {'page': 'time', 'name': name, 'start': time.strftime('%Y-%m-%d %H:%M', time.localtime(start)),
								'length_hours': length, 'repeat_hours': repeat}, 'rows_added': added}
		box, extra = (self.lf1, self.lf2) if page == 'frequency' else (self.lm1, None)
		keep = (box.text(), extra.text() if extra is not None else '')
		box.setText(name)
		if extra is not None:
			extra.setText(str(max(1, self._tool_count(a.get('target_times', 1) or 1, 'target_times'))))
		(self.add_to_freq if page == 'frequency' else self.memo_add)()
		box.setText(keep[0])
		if extra is not None:
			extra.setText(keep[1])
		return {'created': {'page': page, 'name': name}}

	def _add_time_item(self, name, start, length_hours, repeat_hours=None, until=None):
		"""A timed item and, when it repeats, its next ones as Add makes them. Returns how many rows were added."""
		length = self._format_hours(float(length_hours))
		repeat = self._format_hours(float(repeat_hours)) if repeat_hours else '-'
		until_text = str(int(until)) if until else '-'
		self._append_time_row_to_table([name, time.strftime('%Y-%m-%d %H:%M', time.localtime(start)), length, repeat,
										'UNDONE', '-', until_text, 'TIME_SNS', str(start)])
		commands = [self._sync_make_reminder_script((name, start)), self._sync_make_event_script((name, start))]
		added = 1
		if repeat_hours:
			base_values = [name, '', length, repeat, 'UNDONE', '-', until_text, 'TIME_SNS', '']
			for row_values, reminder_cmd, calendar_cmd in self._generate_repeat_occurrences(
					base_values, self._get_repeat_pregenerate_count() - 1, float(start), float(repeat_hours), float(until) if until else None):
				self._append_time_row_to_table(row_values)
				commands += [reminder_cmd, calendar_cmd]
				added += 1
		self._broccoli_after_table_change(commands)
		return added

	def _tool_with_scope(self, a, work):
		self._tool_repeat_scope = 'later' if a.get('scope') == 'later' else 'one'
		try:
			return work()
		finally:
			self._tool_repeat_scope = None

	def _tool_update_item(self, a):
		self._tools_busy()
		table, kind, row = self._tool_find_row(a)
		key = (self._cell_text(table, row, 0, ''), self._stamp_from_items(table.item(row, 8), table.item(row, 1)))
		new_name = ' '.join(str(a.get('new_name') or '').split())
		values = {0: new_name} if new_name else {}
		if kind == 'TIME_SNS':
			if a.get('new_start'):
				values[1] = time.strftime('%Y-%m-%d %H:%M', time.localtime(self._tool_stamp(a['new_start'], 'new_start')))
			if a.get('length_hours') is not None:
				values[2] = self._format_hours(self._tool_hours(a['length_hours'], 'length_hours'))
			if a.get('repeat_hours') is not None:
				hours = self._tool_hours(a['repeat_hours'], 'repeat_hours', allow_zero=True)
				values[3] = self._format_hours(hours) if hours else '-'
		elif kind == 'FREQ_SNS':
			if a.get('target_times') is not None:
				values[5] = str(self._tool_count(a['target_times'], 'target_times'))
			if a.get('done_times') is not None:
				values[6] = str(self._tool_count(a['done_times'], 'done_times'))
		if not values:
			raise tomato_tools.ToolError('Nothing to change was given for an item of this page.')
		if kind == 'TIME_SNS':
			self._tool_with_scope(a, lambda: self._apply_time_changes(key, values))
		elif kind == 'FREQ_SNS':
			self._apply_freq_changes(key, values)
		else:
			self._apply_memo_name(key, values[0])
		return {'updated': a.get('page'), 'name': values.get(0, key[0]), 'changed': sorted(
			{0: 'name', 1: 'start', 2: 'length_hours', 3: 'repeat_hours', 5: 'target_times', 6: 'done_times'}[c] for c in values)}

	def _tool_select(self, table, row):
		table.clearSelection()
		table.setCurrentCell(row, 0)

	def _tool_complete_item(self, a):
		self._tools_busy()
		table, kind, row = self._tool_find_row(a, undone_only=True)
		name = self._cell_text(table, row, 0, '')
		box, done = {'TIME_SNS': (self.textw1, self.save_and_done), 'FREQ_SNS': (self.textw2, self.freq_add_time),
					 'MEMO_SNS': (self.textw3, self.memo_done_memo)}[kind]
		if kind == 'FREQ_SNS' and self._cell_text(table, row, 5, '-') in ('', '-'):
			raise tomato_tools.ToolError('This counted item has no target number yet; set target_times with update_item first.')
		keep = box.toPlainText()
		box.setPlainText(tomato_diary.one_line(a.get('comment') or '', 2000))
		self._tool_select(table, row)
		try:
			done()
		finally:
			box.setPlainText(keep)
		return {'done': name, 'page': a.get('page')}

	def _tool_delete_item(self, a):
		self._tools_busy()
		table, kind, row = self._tool_find_row(a)
		name = self._cell_text(table, row, 0, '')
		self._tool_select(table, row)
		delete = {'TIME_SNS': self.delete_item, 'FREQ_SNS': self.freq_delete, 'MEMO_SNS': self.memo_delete}[kind]
		self._tool_with_scope(a, delete)
		return {'deleted': name, 'page': a.get('page')}

	def _tool_day(self, a):
		day = str(a.get('day') or '').strip()[:10] or tomato_diary.day_name()
		try:
			datetime.datetime.strptime(day, '%Y-%m-%d')
		except ValueError:
			raise tomato_tools.ToolError('"day" is written "YYYY-MM-DD".')
		return day

	def _tool_read_diary(self, a):
		day = self._tool_day(a)
		text = tomato_diary.read(self.fulldir_dia, day)
		if not text.strip():
			return 'There is no diary for %s.' % day
		if a.get('form') == 'full':
			return text if len(text) <= 60000 else text[:60000] + '\n… (cut; ask for the summary)'
		now = datetime.datetime.now()
		end = now.hour * 3600 + now.minute * 60 + now.second if day == tomato_diary.day_name() else None
		return '# %s\n\n%s' % (day, tomato_diary.digest(text, end, max_chars=12000) or '(nothing recorded)')

	def _refresh_unfocused_diary_boxes(self):
		"""A line was added to the diary by a program: the boxes show it, except one the person is typing in
		(that one takes the line in at its next save, see _save_diary_box)."""
		for box in self._diary_text_edits:
			if not box.hasFocus():
				bar = box.verticalScrollBar()
				at_end = bar.value() >= bar.maximum() - 4
				value = bar.value()
				self._refresh_diary_text_widget(box)
				if not at_end:
					bar.setValue(value)

	def add_diary_line(self, text, when=None, limit=0):
		line = tomato_diary.append_line(self.fulldir_dia, text, when, limit)
		self._refresh_unfocused_diary_boxes()
		return line

	def _tool_write_diary_line(self, a):
		when = None
		if a.get('time'):
			try:
				clock = datetime.datetime.strptime(str(a['time']).strip()[:5], '%H:%M')
			except ValueError:
				raise tomato_tools.ToolError('"time" is written "HH:MM".')
			when = datetime.datetime.now().replace(hour=clock.hour, minute=clock.minute, second=0, microsecond=0)
		note = tomato_diary.one_line(a.get('note') or '', 200)
		if a.get('collection'):
			path = tomato_tools.collection_path(self.fulldir_collection, a['collection'])
			columns, rows = tomato_tools.read_collection(path)
			number = tomato_tools._row_number(a.get('row'), rows)
			title = tomato_tools.row_title(columns, rows[number - 1])
			if not title:
				raise tomato_tools.ToolError('That row is empty.')
			text = tomato_diary.collection_line(os.path.basename(path)[:-4], title) + (' — ' + note if note else '')
		else:
			text = tomato_diary.one_line(a.get('text') or '', 1000)
			if not text:
				raise tomato_tools.ToolError('Give "text", or "collection" and "row".')
		return {'added': self.add_diary_line(text, when)}

	def _tool_list_collections(self, a):
		return tomato_tools.list_collections(self.fulldir_collection)

	def _tool_search_collection(self, a):
		return tomato_tools.search_collection(self.fulldir_collection, a.get('collection'), a.get('text') or '', a.get('limit') or 20)

	def _tool_read_collection_row(self, a):
		return tomato_tools.read_row(self.fulldir_collection, a.get('collection'), a.get('row'))

	def _tools_collection_changed(self, path, row=None):
		"""A tool wrote a collection file: the window shows it (the file that is open is read again, the same row
		selected; a new file appears in the list)."""
		current = self.collection_current_file
		if current and os.path.exists(current) and os.path.samefile(current, path):
			keep = self.collection_table.currentRow() if row is None else row
			self._load_collection_file(current)
			if 0 <= keep < self.collection_table.rowCount():
				self.collection_table.setCurrentCell(keep, 0)
		elif self.collection_file_combo.findData(path) == -1:
			self._refresh_collection_files(current)

	def _tool_create_collection_row(self, a):
		self._tools_busy()
		path, row = tomato_tools.add_row(self.fulldir_collection, a.get('collection'), a.get('values'), bool(a.get('add_missing_columns')))
		self._tools_collection_changed(path, row['row'] - 1)
		return {'created': row}

	def _tool_update_collection_row(self, a):
		self._tools_busy()
		path, row = tomato_tools.update_row(self.fulldir_collection, a.get('collection'), a.get('row'), a.get('values'), bool(a.get('add_missing_columns')))
		self._tools_collection_changed(path, row['row'] - 1)
		return {'updated': row}

	def _tool_delete_collection_row(self, a):
		self._tools_busy()
		path, row = tomato_tools.delete_row(self.fulldir_collection, a.get('collection'), a.get('row'))
		self._tools_collection_changed(path)
		return {'deleted': row}

	def _tool_create_collection(self, a):
		self._tools_busy()
		path = tomato_tools.create_collection(self.fulldir_collection, a.get('collection'), a.get('columns'))
		self._tools_collection_changed(path)
		return {'created': os.path.basename(path)[:-4]}

	# ── more tools (2026-11-25, Ryan: "所有的主要的功能都需要"): the menu's switches, a report made now, the report
	# templates, the diary searched and one of its lines corrected, a collection's columns ─────────────────────
	def _tool_read_settings(self, a):
		settings = self._app_settings
		return {'auto_record': bool(action4.isChecked()),
				'auto_record_on_startup': bool(settings.get('auto_record_on_startup', False)),
				'always_on_top': self.is_always_on_top(),
				'show_on_all_spaces': bool(settings.get('show_on_all_spaces', True)),
				'vision_to_diary': bool(settings.get('vision_to_diary', True)),
				'report_auto': self.report_auto(),
				'repeat_pregenerate_count': int(self._get_repeat_pregenerate_count())}

	def _tool_update_settings(self, a):
		before = self._tool_read_settings(a)
		wanted = {}
		for key in before:
			if a.get(key) is None:
				continue
			if key == 'repeat_pregenerate_count':
				try:
					count = int(a[key])
				except (TypeError, ValueError):
					count = 0
				if not 1 <= count <= len(repeat_pregenerate_actions) or count != a[key]:
					raise tomato_tools.ToolError('"repeat_pregenerate_count" is a whole number from 1 to %d.' % len(repeat_pregenerate_actions))
				wanted[key] = count
			elif not isinstance(a[key], bool):
				raise tomato_tools.ToolError('"%s" is true or false.' % key)
			else:
				wanted[key] = a[key]
		wanted = {key: value for key, value in wanted.items() if value != before[key]}
		if not wanted and not any(a.get(key) is not None for key in before):
			raise tomato_tools.ToolError('Nothing to change. The settings are: %s.' % ', '.join(before))
		# each goes the way its menu item goes; the menu's tick follows
		if 'auto_record' in wanted:
			action4.setChecked(wanted['auto_record'])
			self.auto_record(wanted['auto_record'])
			if action4.isChecked() != wanted['auto_record']:
				raise tomato_tools.ToolError('Auto-record could not be switched on on this Mac.')
		if 'auto_record_on_startup' in wanted:
			action_auto_record_startup.setChecked(wanted['auto_record_on_startup'])
			self._toggle_auto_record_startup(wanted['auto_record_on_startup'])
		if 'always_on_top' in wanted:
			action_always_on_top.setChecked(wanted['always_on_top'])
			self._toggle_always_on_top(wanted['always_on_top'])
		if 'show_on_all_spaces' in wanted:
			action_all_spaces.setChecked(wanted['show_on_all_spaces'])
			self._toggle_all_spaces(wanted['show_on_all_spaces'])
		if 'vision_to_diary' in wanted:
			action_vision_diary.setChecked(wanted['vision_to_diary'])
			self.set_vision_to_diary(wanted['vision_to_diary'])
		if 'report_auto' in wanted:
			self.set_report_auto(wanted['report_auto'])
			self._report_refresh(None, None)
		if 'repeat_pregenerate_count' in wanted:
			repeat_pregenerate_actions[wanted['repeat_pregenerate_count'] - 1].setChecked(True)
			self._set_repeat_pregenerate_count(wanted['repeat_pregenerate_count'])
		return {'changed': sorted(wanted), 'settings': self._tool_read_settings(a)}

	def _tool_create_report(self, a):
		kind, key = self._tool_report_key(a)
		if not self.make_report(kind, key):
			raise tomato_tools.ToolError('Nothing was recorded in %s, so there is no report to make.' % key)
		words = 'Made the %s report of %s from Tomato\'s own numbers.' % (tomato_report.KIND_WORDS[kind], key)
		if (kind, key) in self._report_waiting:
			words += ' Its written part has been asked for and joins it when it arrives (read_daily_report shows what is there).'
		return words

	def _tool_template_kind(self, a):
		kind = str(a.get('kind') or 'day')
		if kind not in tomato_report.KINDS:
			raise tomato_tools.ToolError('"kind" is day, week or month.')
		return kind

	def _tool_read_template(self, a):
		kind = self._tool_template_kind(a)
		template, default = self.report_template(kind)
		return {'kind': kind, 'template': template, 'is_the_default': template == default}

	def _tool_update_template(self, a):
		kind = self._tool_template_kind(a)
		template = str(a.get('text') or '')
		if template.strip() and len(template.strip()) < 20 or len(template) > 20000:
			raise tomato_tools.ToolError('"text" is the whole template (Markdown), or "" to go back to the default one.')
		self.save_report_template(kind, template)
		return 'Saved the template of the %s report.' % tomato_report.KIND_WORDS[kind] if template.strip() \
			else 'The %s report uses the default template again.' % tomato_report.KIND_WORDS[kind]

	def _tool_search_diary(self, a):
		return tomato_tools.search_diary(self.fulldir_dia, a.get('text'), a.get('days'), a.get('limit'))

	def _tool_change_diary_line(self, a, new):
		self._tools_busy()
		day = self._tool_day(a)
		state, line = tomato_diary.replace_line(self.fulldir_dia, day, a.get('line'), new)
		if state == 'several':
			raise tomato_tools.ToolError('More than one line of %s reads like that; give the whole line with its time.' % day)
		if state != 'done':
			raise tomato_tools.ToolError('No line of %s reads like that. read_diary with form "full" shows the lines as they are.' % day)
		if day == tomato_diary.day_name():
			self._refresh_unfocused_diary_boxes()
		return line

	def _tool_update_diary_line(self, a):
		new = tomato_diary.one_line(a.get('new_text') or '', 1000)
		if not new:
			raise tomato_tools.ToolError('"new_text" is the line as it should read (keep its time at the front).')
		return {'now': self._tool_change_diary_line(a, new)}

	def _tool_delete_diary_line(self, a):
		return {'deleted': self._tool_change_diary_line(a, None)}

	def _tool_create_collection_column(self, a):
		self._tools_busy()
		path, columns = tomato_tools.add_column(self.fulldir_collection, a.get('collection'), a.get('column'))
		self._tools_collection_changed(path)
		return {'columns': columns}

	def _tool_update_collection_column(self, a):
		self._tools_busy()
		path, columns = tomato_tools.rename_column(self.fulldir_collection, a.get('collection'), a.get('column'), a.get('new_name'))
		self._tools_collection_changed(path)
		return {'columns': columns}

	def _tool_delete_collection_column(self, a):
		self._tools_busy()
		path, columns, filled = tomato_tools.delete_column(self.fulldir_collection, a.get('collection'), a.get('column'))
		self._tools_collection_changed(path)
		return {'columns': columns, 'cells_that_held_something': filled}

	# ── the show / hide shortcut (style book 5.12, 2026-11-22) ───────────────────────────────────────────
	# Ryan 2026-11-22: "像 Broccoli 它能换出……然后再隐藏……给 Tomato 也加一个快捷键"; he chose a menu-bar item,
	# ⌃⌥T to start with, and the system's hot-key registration (no permission to give).
	def _register_show_hide_shortcut(self, text):
		if getattr(self, '_show_hide_hotkey', None) is None:
			self._show_hide_hotkey = tomato_hotkey.GlobalHotKey(lambda: QTimer.singleShot(0, self._show_hide_from_shortcut))
		return self._show_hide_hotkey.set_shortcut(text)

	def _show_hide_shortcut_text(self):
		value = self._app_settings.get('show_hide_shortcut', tomato_hotkey.DEFAULT_SHORTCUT)
		return tomato_hotkey.normalize(value) if isinstance(value, str) else ''

	def _tomato_is_front(self):
		return QGuiApplication.applicationState() == Qt.ApplicationState.ApplicationActive

	def _bring_tomato_to_front(self):
		try:
			from AppKit import NSApplication
			NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
		except Exception:
			pass
		self.raise_()
		self.activateWindow()

	def _show_hide_from_shortcut(self):
		"""Slid in → slide out and come to the front; out but behind other apps → to the front; out and in
		front → slide in."""
		shown = self.i % 2 == 0
		if not shown:
			self.pin_a_tab2()
			self._bring_tomato_to_front()
		elif not self._tomato_is_front():
			self._bring_tomato_to_front()
		else:
			self.pin_a_tab2()

	def open_shortcut_dialog(self):
		hotkey = getattr(self, '_show_hide_hotkey', None)
		if hotkey is not None:
			hotkey.unregister()        # while recording, pressing the current shortcut must reach the dialog
		dialog = ShortcutDialog(self._show_hide_shortcut_text(), self)
		self._shortcut_dialog = dialog
		self._bring_tomato_to_front()
		accepted = dialog.exec() == QDialog.DialogCode.Accepted
		self._shortcut_dialog = None
		value = dialog.value if accepted else self._show_hide_shortcut_text()
		if accepted:
			self._app_settings['show_hide_shortcut'] = value
			self._save_app_settings()
		if not self._register_show_hide_shortcut(value) and value:
			tomato_alert(self, _tr('Show/Hide shortcut'),
						 _tr('%1 could not be set as the shortcut. Try another one.').replace('%1', tomato_hotkey.display(value)))
		return accepted

	def _load_app_settings(self):
		"""Load application settings from JSON file"""
		self._app_settings = {'auto_record_on_startup': False, 'repeat_pregenerate_count': 10, 'always_on_top': True, 'dock_icon': True, 'show_on_all_spaces': True,
							  'show_hide_shortcut': tomato_hotkey.DEFAULT_SHORTCUT}
		if os.path.exists(self.settings_file):
			try:
				with open(self.settings_file, 'r', encoding='utf-8') as f:
					self._app_settings.update(json.load(f))
			except Exception:
				logging.exception("Failed to load app settings.")
		# Apply the auto-record on startup setting to the menu item
		action_auto_record_startup.setChecked(self._app_settings.get('auto_record_on_startup', False))
		all_spaces = bool(self._app_settings.get('show_on_all_spaces', True))
		action_all_spaces.setChecked(all_spaces)
		set_show_on_all_spaces(all_spaces)
		dock_icon = bool(self._app_settings.get('dock_icon', True))
		action_dock_icon.setChecked(dock_icon)
		set_dock_icon_visible(dock_icon)
		on_top = bool(self._app_settings.get('always_on_top', True))
		action_always_on_top.setChecked(on_top)
		self.set_always_on_top(on_top)
		self._register_show_hide_shortcut(self._show_hide_shortcut_text())
		action_vision_diary.setChecked(bool(self._app_settings.get('vision_to_diary', True)))
		# Apply the repeat pregenerate count setting to the menu
		pregenerate_count = self._app_settings.get('repeat_pregenerate_count', 10)
		if 1 <= pregenerate_count <= 15:
			repeat_pregenerate_actions[pregenerate_count - 1].setChecked(True)

	def _save_app_settings(self):
		"""Save application settings to JSON file"""
		try:
			with open(self.settings_file, 'w', encoding='utf-8') as f:
				json.dump(self._app_settings, f, ensure_ascii=False, indent=2)
		except Exception:
			logging.exception("Failed to save app settings.")

	def _toggle_auto_record_startup(self, checked):
		"""Toggle the auto-record on startup setting"""
		self._app_settings['auto_record_on_startup'] = checked
		self._save_app_settings()

	def _set_repeat_pregenerate_count(self, count):
		"""Set the repeat pregenerate count setting"""
		self._app_settings['repeat_pregenerate_count'] = count
		self._save_app_settings()

	def _get_repeat_pregenerate_count(self):
		"""Get the current repeat pregenerate count setting"""
		return self._app_settings.get('repeat_pregenerate_count', 10)

	def _start_auto_record_if_enabled(self):
		"""Start auto-record if the setting is enabled (called on startup)"""
		if self._app_settings.get('auto_record_on_startup', False):
			action4.setChecked(True)
			self.auto_record(True)

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
		if getattr(self, '_tools_host', None) is not None:
			self._tools_host.stop()
		if self.auto_record_thread:
			self.auto_record_thread.stop()
			self.auto_record_thread = None
		if hasattr(self, 'reminder_sync_timer') and self.reminder_sync_timer.isActive():
			self.reminder_sync_timer.stop()
		if self.system_sync_thread:
			self.system_sync_thread.stop()
			self.system_sync_thread = None
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


install_window_liquid_glass(ClockPickerPopup, tomato_ui.POPUP_GLASS_RADIUS, 0, keep_shadow=True, menu_look=True)
glass_kit.install_glass_button_class(WhiteButton)  # white capsules become glass (before any window is built)
for _glass_window_cls in (WindowAbout, WindowUpdate, CustomDialog, CustomDialog2, CustomDialog3, CustomDialog4):
	install_native_glass_window_class(_glass_window_cls)


# Every Tomato window shows on all desktops (Spaces). This used to be the Dock icon's Options ▸ All Desktops,
# clicked through System Events at every start — impossible once the Dock icon is hidden, it needed the
# Accessibility permission, and the start waited for it. Now each window is told itself, natively, as Broccoli
# and Strawberry do, set every time the window is shown (Qt may make a new native window, e.g. after its flags
# change). Since 2026-11-20 it is a switch in the menu-bar menu (🪟 Show on all Spaces), with Broccoli's meaning:
# on = every desktop and over other apps' full-screen windows; off = only the desktop the window is on.
_NS_WINDOW_CAN_JOIN_ALL_SPACES = 1 << 0
_NS_WINDOW_MOVE_TO_ACTIVE_SPACE = 1 << 1
_NS_WINDOW_FULL_SCREEN_AUXILIARY = 1 << 8
SHOW_ON_ALL_SPACES = True
_ALL_SPACES_CLASSES = []


# Stage Manager (2026-11-25, Ryan: "它有的时候左边显示就会突然空出来这么一块…这个问题早就有了"; measured on his
# screen: the system fitted the sliding main window into the room right of its strip). The main window is a
# panel at the screen's edge, not a document window: it is marked as one that belongs to no stage and shows with
# every app's (auxiliary + can join all applications, never primary), so the system has no stage to fit it into.
_NS_WINDOW_PRIMARY = 1 << 16
_NS_WINDOW_AUXILIARY = 1 << 17
_NS_WINDOW_CAN_JOIN_ALL_APPLICATIONS = 1 << 18


def keep_out_of_stage_manager(widget):
	if sys.platform != 'darwin' or QGuiApplication.platformName() != 'cocoa':
		return False   # no system window behind the widget (e.g. Qt drawing off screen)
	window = glass_kit._broccoli_own_ns_window(widget)
	if window is None:
		return False
	try:
		behavior = int(window.collectionBehavior())
		wanted = (behavior & ~_NS_WINDOW_PRIMARY) | _NS_WINDOW_AUXILIARY | _NS_WINDOW_CAN_JOIN_ALL_APPLICATIONS
		if wanted != behavior:
			window.setCollectionBehavior_(wanted)
			logging.info('Main window marked as outside Stage Manager: behaviour %#x -> %#x', behavior, int(window.collectionBehavior()))
		return True
	except Exception:
		logging.exception('Main window: the Stage Manager mark could not be set')
		return False


def show_window_on_all_spaces(widget, enabled=None):
	if sys.platform != 'darwin' or QGuiApplication.platformName() != 'cocoa':
		return False   # no system window behind the widget (e.g. Qt drawing off screen)
	window = glass_kit._broccoli_own_ns_window(widget)
	if window is None:
		return False
	enabled = SHOW_ON_ALL_SPACES if enabled is None else bool(enabled)
	bits = _NS_WINDOW_CAN_JOIN_ALL_SPACES | _NS_WINDOW_FULL_SCREEN_AUXILIARY
	try:
		behavior = int(window.collectionBehavior())
		wanted = behavior & ~_NS_WINDOW_MOVE_TO_ACTIVE_SPACE
		wanted = (wanted | bits) if enabled else (wanted & ~bits)
		if wanted != behavior:
			window.setCollectionBehavior_(wanted)
		return True
	except Exception:
		return False


def set_show_on_all_spaces(enabled):
	"""The switch: for the windows that are open now and every one shown later."""
	global SHOW_ON_ALL_SPACES
	SHOW_ON_ALL_SPACES = bool(enabled)
	for widget in QApplication.topLevelWidgets():
		if isinstance(widget, tuple(_ALL_SPACES_CLASSES)) and widget.testAttribute(Qt.WidgetAttribute.WA_WState_Created):
			show_window_on_all_spaces(widget)


def install_all_spaces_class(cls):
	original = cls.showEvent

	def showEvent(self, event, _original=original):
		_original(self, event)
		show_window_on_all_spaces(self)

	cls.showEvent = showEvent
	_ALL_SPACES_CLASSES.append(cls)


for _all_spaces_cls in (window3, WindowAbout, WindowUpdate, CustomDialog, CustomDialog2, CustomDialog3, CustomDialog4,
						CustomDialog_warn, SyncIndicatorDialog, AutoCloseNotification,
						tomato_broccoli_ui.TaskEditorDialog, tomato_broccoli_ui.TaskManagerDialog):
	install_all_spaces_class(_all_spaces_cls)

w1 = WindowAbout()  # about
w2 = WindowUpdate()  # update
w3 = window3()  # main1


def _tell_data_folder_moved():
	"""Once, after the start that moved the data: where it is now (a syncing or backup tool that watched the
	old folder has to be pointed at the new one)."""
	tomato_alert(None, NAME, _tr(
		'Tomato\'s data has moved from the home folder to:\n\n%1\n\nNothing else changed. If a syncing or backup tool watched the old folder "TomatoAppPath", point it at the new one.'
	).replace('%1', TOMATO_DATA_DIR.replace(str(Path.home()), '~', 1)))


if DATA_FOLDER_MOVE_REPORT == 'moved':
	QTimer.singleShot(1500, lambda: _tell_data_folder_moved())
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
action_broccoli_tasks.triggered.connect(w3.open_broccoli_tasks)
action4.triggered.connect(w3.auto_record)
action_auto_record_startup.triggered.connect(w3._toggle_auto_record_startup)
action_always_on_top.triggered.connect(w3._toggle_always_on_top)
action_dock_icon.triggered.connect(w3._toggle_dock_icon)
action_all_spaces.triggered.connect(w3._toggle_all_spaces)
action_shortcut.triggered.connect(w3.open_shortcut_dialog)
action_vision_diary.toggled.connect(w3.set_vision_to_diary)
action_daily_report.triggered.connect(lambda: w3.open_daily_report())
action_ai_apps.triggered.connect(_copy_ai_apps_setup)
# Connect repeat pregenerate count menu actions
for i, action in enumerate(repeat_pregenerate_actions):
	action.triggered.connect(lambda checked, count=i+1: w3._set_repeat_pregenerate_count(count))
# tray.activated.connect(w3.activate)
btna4.triggered.connect(w3.pin_a_tab2)
quit.triggered.connect(w3.totalquit)
tomato_ui.set_dialog_host(lambda: w3)
tomato_ui._THEME_HOOKS.append(lambda dark: w3._style_edge_strip())
on_theme_changed(apply_tomato_theme)
install_theme_observer()
apply_tomato_theme()
# Start auto-record if the setting is enabled
w3._start_auto_record_if_enabled()
# Updates, Broccoli's way (2026-11-25, Ryan: "所有的软件……都是要学习 Broccoli 的这个更新写法的"): the previous
# bundle / installers the last update left are removed in the background; 3 s after the start one release check
# runs in the background, and when a newer release is out (or the last install left a note) the update window
# comes out by itself, with its one-click "Update Now". No daily re-check, no switches, no "open the page?".
threading.Thread(target=tomato_cleanup_update_leftovers, daemon=True, name='tomato-update-cleanup').start()
QTimer.singleShot(3000, lambda: w2.checkupdate(popup_when_ready=True))
app.exec()
# One-click update: the bundles are swapped only once Qt has wound down (only when the update window prepared an
# install before quitting). Tomato keeps Qt's own app delegate (it never calls setDelegate_), so app.exec()
# returns on every Quit path (the menu's Quit → totalquit, ⌘Q, the Dock's Quit) and this line is reached.
tomato_apply_pending_update_install()
