# -*- mode: python ; coding: utf-8 -*-
# Tomato — PyInstaller. Build from the folder that holds Tomato.py (= Tomato_26new.py under its release name),
# glass_kit.py, smooth_widgets.py, tomato_ui.py, tomato_sync.py, tomato_eventkit.py, tomato_broccoli.py, tomato_broccoli_ui.py,
# markdown_preview.py, tomato_preview.py, tomato_hotkey.py, tomato_diary.py, tomato_tools.py, app_mcp_host.py, tomato_feed.py,
# tomato_report.py, tomato_report_ui.py, share_picture.py, tomato_schedule_skill.md, tomato_food_skill.md, i18n/ and MathJax-2.7.9/.
#
#   pyinstaller Tomato.spec
#
# The two sentences in info_plist below are what the system shows the first time Tomato asks for its
# Reminders list and its calendars. Without them Tomato still works, the old slow way (through Reminders.app
# and Calendar.app); with them, and "Allow Full Access" answered once, it reads and writes both directly.
#
# Signing (2026-11-20): the app is signed with the hardened runtime (--options runtime). Under it the system
# refuses the calendars without asking unless the signature carries the calendars entitlement, so sign WITH
# entitlements.plist (next to this spec: calendars + Apple events — Tomato still sends AppleScript for the
# few things the direct way does not cover — and, since 1.2.12, the lines the web engine needs to run the
# preview's scripts under the hardened runtime: allow-jit …, the same ones Watermelon and Broccoli sign with):
#     xattr -cr Tomato.app
#     codesign --deep --force --options runtime --timestamp --entitlements entitlements.plist \
#         --sign "Developer ID Application: <your name> (<team id>)" Tomato.app
#     codesign --verify --deep --strict Tomato.app        (silent = good)
# Nothing else inside needs a signature of its own: --deep signs Qt's web engine helper
# (QtWebEngineProcess.app, there since 1.2.12 for the Collection page's Markdown preview) with the same
# entitlements, and Tomato writes nothing into its own bundle (data and the error log live in Application
# Support). The preview only shows pages Tomato makes itself, so the stray folder that broke Broccoli's
# signature (a web page touching the camera / microphone list) does not come up here.
# How to tell it worked: after "Allow Full Access" the log (…/Application Support/com.ryanthehito.tomato/
# tomato_errors.log) says "System interface: reminders direct, calendar direct".

import glob
import os
import re
from pathlib import Path

block_cipher = None

# the version is the one in the program, so the two cannot drift apart
with open('Tomato.py', encoding='utf-8') as handle:
    __version__ = re.search(r'^VERSION = "([^"]+)"', handle.read(), re.M).group(1)

# icons: tomato.icns = the app's icon (Dock), tomatomen.icns = the menu-bar icon (drawn for that size),
# tomato.png = the picture in the About window
RESOURCES = (
    'tomato.icns', 'tomatomen.icns', 'tomato.png',
    'wechat50.png', 'wechat20.png', 'wechat10.png', 'wechat5.png',
    'alipay50.png', 'alipay20.png', 'alipay10.png', 'alipay5.png',
    'All.csv', 'Record.csv',
    'tomato_schedule_skill.md',      # the Broccoli skill Tomato brings along (tomato_broccoli.install_skill)
    'tomato_food_skill.md',          # … and the one for meals and nutrition (uses Tomato's tools)
)
MODULES = ('glass_kit.py', 'smooth_widgets.py', 'tomato_ui.py', 'tomato_sync.py', 'tomato_eventkit.py', 'tomato_broccoli.py',
           'tomato_broccoli_ui.py',
           'markdown_preview.py',    # the Markdown preview's page (the copy shared with Watermelon and Strawberry)
           'tomato_preview.py',      # the web view the Collection page shows it in (1.2.12)
           'tomato_hotkey.py',       # the show / hide shortcut (system hot key, no permission needed)
           'tomato_diary.py',        # the diary file: one door for every writer, the day read back
           'tomato_tools.py',        # Tomato's functions as tools: the file work
           'app_mcp_host.py',        # the local tools service + its card (the copy shared with the other apps)
           'tomato_feed.py',         # what Broccoli's background vision saw, into the diary
           'tomato_report.py', 'tomato_report_ui.py',     # the daily report and its windows
           'share_picture.py')       # a report as one long picture (Share)
# formulas in the preview: Tomato's own MathJax, no network (markdown_preview.set_mathjax_folders)
MATHJAX = 'MathJax-2.7.9'
MATHJAX_NEEDED = ('MathJax.js', 'config/TeX-MML-AM_CHTML.js')
TRANSLATIONS = sorted(glob.glob('i18n/*.qm'))
missing = [name for name in RESOURCES + MODULES if not os.path.isfile(name)]
missing += [MATHJAX + '/' + name for name in MATHJAX_NEEDED if not os.path.isfile(os.path.join(MATHJAX, name))]
if not TRANSLATIONS:
    missing.append('i18n/*.qm')
if missing:
    raise SystemExit('Tomato.spec: missing next to the spec: ' + ', '.join(missing))

datas = [(name, '.') for name in RESOURCES]
datas += [(name, 'i18n') for name in TRANSLATIONS]
# every file of MathJax-2.7.9/, keeping its layout (without the hidden files of its repository)
for _root, _dirs, _files in os.walk(MATHJAX):
    _dirs[:] = sorted(d for d in _dirs if not d.startswith('.'))
    datas += [(os.path.join(_root, name), _root) for name in sorted(_files) if not name.startswith('.')]

# QtWebEngine's stray "version" in the BUILD environment (as in Broccoli.spec, 2026-11-09). Running a
# program with a web view from source can leave an empty QtWebEngineCore.framework/Versions/Resources
# inside the environment's PyQt6. PyInstaller's Qt hook takes the LAST name in Versions/ as the framework's
# version — "Resources" sorts after "A" — and would put the web engine's helper app under it instead of
# Versions/A, where the framework's links point: the packaged preview would stay empty. An EMPTY extra
# folder holds nothing and is removed before the analysis; anything else stops the build.
import PyQt6 as _pyqt6
_webengine_versions = Path(_pyqt6.__file__).parent / 'Qt6' / 'lib' / 'QtWebEngineCore.framework' / 'Versions'
if _webengine_versions.is_dir():
    for _entry in sorted(_webengine_versions.iterdir()):
        if _entry.name != 'Current' and _entry.is_dir() and not _entry.is_symlink() and not any(_entry.iterdir()):
            _entry.rmdir()
            print('Removed an empty stray QtWebEngine version folder from the build environment:', _entry)
    _versions_left = sorted(e.name for e in _webengine_versions.iterdir() if e.name != 'Current')
    if len(_versions_left) != 1:
        raise SystemExit(f'Tomato.spec: {_webengine_versions} holds {_versions_left}, not one version: PyInstaller '
                         'would package QtWebEngine under the last one. Remove the one that is not part of PyQt6 '
                         '(PyQt6 ships "A") and build again.')

a = Analysis(
    ['Tomato.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['subprocess', 'EventKit', 'glass_kit', 'smooth_widgets', 'tomato_ui', 'tomato_sync', 'tomato_eventkit', 'tomato_broccoli', 'tomato_broccoli_ui',
                   'markdown_preview', 'tomato_preview', 'tomato_hotkey', 'tomato_diary', 'tomato_tools', 'app_mcp_host', 'tomato_feed',
                   'tomato_report', 'tomato_report_ui', 'share_picture', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Tomato',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Tomato',
)
app = BUNDLE(
    coll,
    name='Tomato.app',
    icon='tomato.icns',
    bundle_identifier='com.ryanthehito.tomato',   # 2026-11-17 (was "Tomato"; same scheme as Broccoli / Strawberry)
    version=__version__,
    info_plist={
        # as Broccoli's / Strawberry's: Tomato starts without a Dock icon and shows or hides it at run time
        # (menu-bar menu ▸ 👀 Show/Hide dock icon; shown unless the user hid it)
        'LSBackgroundOnly': True,
        'NSHighResolutionCapable': True,
        'NSRemindersFullAccessUsageDescription': 'Tomato keeps its time-sensitive items in step with your "Tomato" list in Reminders.',
        'NSCalendarsFullAccessUsageDescription': 'Tomato keeps its time-sensitive items in step with your "Tomato" calendar.',
        # shown the first time Tomato sends a command to Reminders / Calendar the old way
        'NSAppleEventsUsageDescription': 'Tomato sets up its "Tomato" list and calendar in Reminders and Calendar, and keeps them in step with its items.',
        # asked for by macOS versions before 14
        'NSRemindersUsageDescription': 'Tomato keeps its time-sensitive items in step with your "Tomato" list in Reminders.',
        'NSCalendarsUsageDescription': 'Tomato keeps its time-sensitive items in step with your "Tomato" calendar.',
    },
)
