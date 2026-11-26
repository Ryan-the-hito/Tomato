"""The windows of the Broccoli link (tomato_broccoli.py holds the rules):

  TaskSuggest        typing "@" in the item box opens a list drawn like a system menu (style book 5.3, "a list that
                     has to stay open while typing"): one sentence for Broccoli / the saved tasks / a new task /
                     the manager. The list never takes the keyboard: the item box keeps it and hands the list
                     ↑ ↓ Return Tab Esc.
  TaskEditorDialog   the instructions of one task (style book 5.12 dialog: the window is the card, grey buttons).
  TaskManagerDialog  every task and draft, its next time, its instructions; new / rename / delete / show in Finder.
"""
import subprocess

from PyQt6.QtCore import Qt, QEvent, QObject, QPoint, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFontMetrics, QGuiApplication, QPainter
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QLabel, QPlainTextEdit, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

import glass_kit
import tomato_broccoli
from glass_kit import (_tr, is_dark_theme, MacNormalButton, install_window_liquid_glass, glass_list_palette,
                       glass_list_font, glass_list_highlight_rect, paint_glass_list_background,
                       paint_glass_list_highlight, paint_glass_list_separator, GLASS_LIST_ROW_H, GLASS_LIST_PAD,
                       GLASS_LIST_RADIUS, GLASS_LIST_TEXT_X_PLAIN, GLASS_LIST_TEXT_RIGHT, GLASS_LIST_SEPARATOR_H)
from tomato_ui import GlassFormDialog, GREY_ROW_HEIGHT, ask_text, style_table, tomato_alert, tomato_confirm

app = QApplication.instance()
MARKER = tomato_broccoli.MARKER


class TaskSuggestPopup(QWidget):
    """rows: [{'kind': 'direct' | 'task' | 'new' | 'manage' | 'sep', 'text': …, 'value': …}]"""
    chosen = pyqtSignal(dict)

    def __init__(self):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.WindowDoesNotAcceptFocus | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True)
        self.rows = []
        self.index = -1

    def set_rows(self, rows, index=0):
        self.rows = list(rows)
        self.index = -1
        self.move_to(index)
        metrics = QFontMetrics(glass_list_font(self.font()))
        width = max([220] + [metrics.horizontalAdvance(row['text']) + GLASS_LIST_TEXT_X_PLAIN + GLASS_LIST_TEXT_RIGHT + 2
                             for row in self.rows if row['kind'] != 'sep'])
        height = sum(self._row_height(row) for row in self.rows) + 2 * GLASS_LIST_PAD
        self.setFixedSize(min(width, 460), height)
        self.update()

    @staticmethod
    def _row_height(row):
        return GLASS_LIST_SEPARATOR_H if row['kind'] == 'sep' else GLASS_LIST_ROW_H

    def _row_tops(self):
        top = GLASS_LIST_PAD
        for row in self.rows:
            yield top, row
            top += self._row_height(row)

    def move_to(self, index):
        """The highlighted row; separators are stepped over."""
        choices = [i for i, row in enumerate(self.rows) if row['kind'] != 'sep']
        if not choices:
            self.index = -1
        elif index in choices:
            self.index = index
        else:
            self.index = min(choices, key=lambda i: abs(i - index))
        self.update()

    def step(self, delta):
        choices = [i for i, row in enumerate(self.rows) if row['kind'] != 'sep']
        if not choices:
            return
        at = choices.index(self.index) if self.index in choices else (-1 if delta > 0 else 0)
        self.index = choices[(at + delta) % len(choices)]
        self.update()

    def current(self):
        return self.rows[self.index] if 0 <= self.index < len(self.rows) else None

    def show_at(self, anchor):
        """Above the box it belongs to (the box sits in the panel at the bottom of the window); below when there
        is no room above."""
        corner = anchor.mapToGlobal(QPoint(0, 0))
        screen = QGuiApplication.screenAt(corner) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        x = max(area.left() + 4, min(corner.x(), area.right() - self.width() - 4))
        y = corner.y() - self.height() - 4
        if y < area.top() + 4:
            y = corner.y() + anchor.height() + 4
        self.move(int(x), int(y))
        if not self.isVisible():
            self.show()

    def _index_at(self, y):
        for i, (top, row) in enumerate(self._row_tops()):
            if top <= y < top + self._row_height(row):
                return i if row['kind'] != 'sep' else -1
        return -1

    def mouseMoveEvent(self, event):
        index = self._index_at(event.position().y())
        if index >= 0 and index != self.index:
            self.index = index
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            index = self._index_at(event.position().y())
            if index >= 0:
                self.index = index
                self.chosen.emit(self.rows[index])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        dark = is_dark_theme(app)
        palette = glass_list_palette(dark)
        if not getattr(self, '_liquid_glass_active', False):       # with Liquid Glass the system's glass is the card
            paint_glass_list_background(painter, self, dark)
        painter.setFont(glass_list_font(self.font()))
        metrics = painter.fontMetrics()
        for i, (top, row) in enumerate(self._row_tops()):
            if row['kind'] == 'sep':
                paint_glass_list_separator(painter, top, self.width(), dark, text_x=GLASS_LIST_TEXT_X_PLAIN)
                continue
            selected = i == self.index
            if selected:
                paint_glass_list_highlight(painter, glass_list_highlight_rect(self.width(), top), dark)
            painter.setPen(palette['on_accent'] if selected else palette['text'])
            box = QRectF(GLASS_LIST_TEXT_X_PLAIN, top, self.width() - GLASS_LIST_TEXT_X_PLAIN - GLASS_LIST_TEXT_RIGHT, GLASS_LIST_ROW_H)
            painter.drawText(box, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             metrics.elidedText(row['text'], Qt.TextElideMode.ElideRight, int(box.width())))
        painter.end()


install_window_liquid_glass(TaskSuggestPopup, GLASS_LIST_RADIUS, 0, keep_shadow=True, menu_look=True)


class TaskSuggest(QObject):
    """Drives the list for one item box. mode: None (the list follows the typing) | 'direct' (one sentence) |
    'new' (the words after the marker name a new task) | 'task' (a saved task was put in)."""

    def __init__(self, edit, store, on_manage):
        super().__init__(edit)
        self.edit, self.store, self._on_manage = edit, store, on_manage
        self.mode = None
        self.popup = TaskSuggestPopup()
        self.popup.chosen.connect(self._choose)
        edit.textEdited.connect(self._typed)
        edit.textChanged.connect(self._changed)
        edit.installEventFilter(self)
        app.applicationStateChanged.connect(lambda _state: self.popup.hide())

    def is_new_task(self):
        return self.mode == 'new'

    def rows_for(self, text):
        """The list for what is in the box, with the row to highlight; None = no list."""
        typed = text.lstrip()
        low = typed.casefold()
        marker = MARKER.casefold()
        if not low.startswith('@'):
            return None
        if low.startswith(marker + ' '):
            query = ' '.join(typed[len(marker) + 1:].split()).casefold()
        elif marker.startswith(low):
            query = ''
        else:
            return None
        tasks = [name for name in self.store.names() if query in name.casefold()]
        if query and not tasks:
            return None                      # a sentence is being written: the list stays out of the way
        rows = []
        if not query:
            rows.append({'kind': 'direct', 'text': _tr('Broccoli: write one sentence'), 'value': ''})
        for name in tasks:
            mark = '' if self.store.has_spec(name) else '  ' + _tr('(draft)')
            rows.append({'kind': 'task', 'text': name + mark, 'value': name})
        rows.append({'kind': 'sep', 'text': '', 'value': ''})
        rows.append({'kind': 'new', 'text': _tr('New task: type its name, then Add'), 'value': ''})
        rows.append({'kind': 'manage', 'text': _tr('Manage tasks…'), 'value': ''})
        return rows, 0

    def _changed(self, text):
        if not text.lstrip().casefold().startswith(MARKER.casefold() + ' '):
            if self.mode in ('direct', 'new', 'task'):
                self.mode = None
            if not text.lstrip().startswith('@'):
                self.popup.hide()

    def _typed(self, text):
        if self.mode == 'task':
            self.mode = None                 # the name is being changed by hand: back to choosing
        if self.mode in ('direct', 'new'):
            self.popup.hide()
            return
        found = self.rows_for(text)
        if found is None:
            self.popup.hide()
            return
        self.popup.set_rows(*found)
        self.popup.show_at(self.edit)

    def _choose(self, row):
        self.popup.hide()
        kind = row['kind']
        if kind == 'manage':
            self.edit.clear()
            self.mode = None
            self._on_manage()
            return
        self.edit.setText(MARKER + ' ' + (row['value'] if kind == 'task' else ''))
        self.mode = kind
        self.edit.setFocus()

    def eventFilter(self, watched, event):
        if watched is self.edit:
            kind = event.type()
            if kind == QEvent.Type.KeyPress and self.popup.isVisible():
                key = event.key()
                if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                    self.popup.step(1 if key == Qt.Key.Key_Down else -1)
                    return True
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                    row = self.popup.current()
                    if row is not None:
                        self._choose(row)
                        return True
                if key == Qt.Key.Key_Escape:
                    self.popup.hide()
                    return True
            elif kind in (QEvent.Type.FocusOut, QEvent.Type.Hide):
                self.popup.hide()
        return False


def _instructions_box(parent):
    box = QPlainTextEdit(parent)
    box.setObjectName('edit')                # the big input box (style book 5.4)
    box.setPlaceholderText(_tr('What should Broccoli do each time? What must it not do? Where do results go?'))
    box.setTabChangesFocus(False)
    return box


class TaskEditorDialog(GlassFormDialog):
    """Write the instructions of one task. saved(name, text) on Save."""
    saved = pyqtSignal(str, str)

    def __init__(self, name, text='', parent=None):
        super().__init__(_tr('Instructions for Broccoli'), parent, ok_text=_tr('Save'))
        self.task_name = name
        title = QLabel(name, self)
        title.setWordWrap(True)
        hint = QLabel(_tr('Broccoli gets this whole text each time the task runs.'), self)
        hint.setWordWrap(True)
        hint.setStyleSheet('color: #8E8E93; font-size: 11px;')
        self.editor = _instructions_box(self)
        self.editor.setPlainText(text)
        self.editor.setMinimumHeight(240)
        self.editor.textChanged.connect(self._check)
        self.body.addWidget(title)
        self.body.addWidget(hint)
        self.body.addWidget(self.editor, 1)
        self.ok_button.setDefault(False)     # Return writes a new line here
        self.ok_button.setAutoDefault(False)
        self.cancel_button.setAutoDefault(False)
        self._check()
        self.adjustSize()
        self.editor.setFocus()

    def _check(self):
        self.ok_button.setEnabled(bool(self.editor.toPlainText().strip()))

    def accept(self):
        text = self.editor.toPlainText()
        if not text.strip():
            return
        self.saved.emit(self.task_name, text)
        super().accept()


class TaskManagerDialog(GlassFormDialog):
    """host: task_info(name) → (next stamp | None, undone rows), rename_task(old, new) → bool,
    delete_task(name) → bool, format_time(stamp) → text."""

    def __init__(self, store, host, parent=None):
        super().__init__(_tr('Broccoli tasks'), parent, ok_text=_tr('Close'))
        self.store, self.host = store, host
        self._keep_width = True
        self._loaded = None                  # the task whose text is in the editor
        self.cancel_button.hide()
        self.ok_button.setDefault(False)
        self.ok_button.setAutoDefault(False)
        columns = QHBoxLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(12)
        left = QVBoxLayout()
        left.setSpacing(8)
        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels([_tr('Task'), _tr('Next'), _tr('Left')])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFixedWidth(350)
        style_table(self.table, 'card')
        from PyQt6.QtWidgets import QHeaderView
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._selected)
        left.addWidget(self.table, 1)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.new_button = MacNormalButton(_tr('New'), self)
        self.rename_button = MacNormalButton(_tr('Rename'), self)
        self.delete_button = MacNormalButton(_tr('Delete'), self)
        for button, slot in ((self.new_button, self._new), (self.rename_button, self._rename), (self.delete_button, self._delete)):
            button.setAutoDefault(False)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        buttons.addStretch(1)
        left.addLayout(buttons)
        right = QVBoxLayout()
        right.setSpacing(8)
        self.editor = _instructions_box(self)
        self.editor.textChanged.connect(self._edited)
        right.addWidget(self.editor, 1)
        # the Mac that runs this task when this one is asleep or off at its time (style book 5.12)
        standby_row = QHBoxLayout()
        standby_row.setSpacing(8)
        self.standby_label = QLabel(_tr('Standby Mac'), self)
        self.standby_box = glass_kit.StrawberryDropdown(self, compact_light=True)
        self.standby_box.setMinimumWidth(60)       # takes the room that is left: the window keeps its width
        tip = _tr('When this Mac is asleep or off at the task\'s time, the chosen Mac runs the task instead. '
                  'Choose one only for a task that does not need this Mac\'s own files, apps or sign-ins.')
        self.standby_label.setToolTip(tip)
        self.standby_box.setToolTip(tip)
        self.standby_box.currentIndexChanged.connect(self._standby_chosen)
        standby_row.addWidget(self.standby_label)
        standby_row.addWidget(self.standby_box, 1)
        right.addLayout(standby_row)
        under = QHBoxLayout()
        under.setSpacing(8)
        self.status = QLabel('', self)
        self.status.setStyleSheet('color: #8E8E93; font-size: 11px;')
        self.finder_button = MacNormalButton(_tr('Show in Finder'), self)
        self.finder_button.setAutoDefault(False)
        self.finder_button.clicked.connect(self._show_in_finder)
        under.addWidget(self.status, 1)
        under.addWidget(self.finder_button)
        right.addLayout(under)
        columns.addLayout(left)
        columns.addLayout(right, 1)
        self.body.addLayout(columns, 1)
        self._save_timer = QTimer(self)      # typing is saved a moment after it stops
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self.save_now)
        self.resize(640, 440)
        self.refresh()

    # ── the list ──
    def current_name(self):
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    def refresh(self, select=None):
        """Fill the list from the folders; the editor is left alone unless the selection changes."""
        keep = select or self.current_name()
        names = self.store.names()
        self.table.blockSignals(True)
        self.table.setRowCount(len(names))
        for row, name in enumerate(names):
            next_stamp, count = self.host.task_info(name)
            if not self.store.has_spec(name):
                when = _tr('Draft')
            elif next_stamp is None:
                when = '–'
            else:
                when = self.host.format_time(next_stamp)
            for column, text in enumerate((name, when, str(count))):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, name)
                if not column:
                    item.setToolTip(name)
                if column:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)
        self.table.blockSignals(False)
        if names:
            self.table.selectRow(names.index(keep) if keep in names else 0)
        self._selected()

    def _selected(self):
        name = self.current_name()
        for widget in (self.rename_button, self.delete_button, self.finder_button, self.editor):
            widget.setEnabled(name is not None)
        self._fill_standby(name)
        if name == self._loaded:
            return
        self.save_now()
        self._loaded = name
        text = ''
        if name is not None:
            text, error = self.store.read_spec(name)
            text = text or ''
            self.status.setText({'too_big': _tr('This file is too large to send.'), 'unreadable': _tr('This file cannot be read.')}.get(error, ''))
        else:
            self.status.setText(_tr('No tasks yet. Click New, or type @ in the item box.'))
        self.editor.blockSignals(True)
        self.editor.setPlainText(text)
        self.editor.blockSignals(False)
        self._dirty = False

    # ── the standby Mac ──
    def _fill_standby(self, name):
        """The drop-down: None, then the Macs Broccoli says can stand by; the task's own choice stays listed
        (and chosen) even while that Mac is not among them."""
        chosen = self.store.read_standby(name) if name is not None else None
        devices = self.store.standby_devices()
        if chosen and chosen['device_id'] not in [d['id'] for d in devices]:
            devices.append({'id': chosen['device_id'], 'name': chosen['device_name']})
        box = self.standby_box
        box.blockSignals(True)
        box.clear()
        box.addItem(_tr('None'), '')
        for device in devices:
            box.addItem(device['name'], device['id'])
        index = box.findData(chosen['device_id']) if chosen else 0
        box.setCurrentIndex(max(0, index))
        box.blockSignals(False)
        usable = name is not None and len(devices) > 0     # nothing to choose: grey, the reason in the tooltip (5.2)
        box.setEnabled(usable)
        self.standby_label.setEnabled(name is not None)

    def _standby_chosen(self, index):
        name = self.current_name()
        if name is None or name not in self.store.names():
            return
        device = self.standby_box.itemData(index) or ''
        try:
            self.store.write_standby(name, device, self.standby_box.currentText() if device else '')
            self.status.setText(_tr('Saved'))
        except Exception:
            self.status.setText(_tr('This file cannot be saved.'))

    # ── the editor ──
    def _edited(self):
        self._dirty = True
        self.status.setText('')
        self._save_timer.start()

    def save_now(self):
        self._save_timer.stop()
        if not getattr(self, '_dirty', False) or self._loaded is None:
            return
        self._dirty = False
        if self._loaded not in self.store.names():
            return
        try:
            self.store.write_spec(self._loaded, self.editor.toPlainText())
            self.status.setText(_tr('Saved'))
        except Exception:
            self.status.setText(_tr('This file cannot be saved.'))

    # ── the buttons ──
    def _new(self):
        text, ok = ask_text(self, _tr('New task'), _tr('Name of the task:'))
        if not ok:
            return
        name = tomato_broccoli.valid_task_name(text)
        if name is None or self.store.find(name) is not None:
            tomato_alert(self, _tr('New task'), _tr('Use a name that is not taken, without / \\ : and at most 80 characters.'))
            return
        self.store.create(name)
        self.refresh(select=name)
        self.editor.setFocus()

    def _rename(self):
        old = self.current_name()
        if old is None:
            return
        text, ok = ask_text(self, _tr('Rename'), _tr('Name of the task:'), old)
        if not ok or ' '.join(text.split()) == old:
            return
        name = tomato_broccoli.valid_task_name(text)
        if name is None or self.store.find(name) not in (None, old):
            tomato_alert(self, _tr('Rename'), _tr('Use a name that is not taken, without / \\ : and at most 80 characters.'))
            return
        self.save_now()
        if self.host.rename_task(old, name):
            self._loaded = name
            self.refresh(select=name)
        else:
            tomato_alert(self, _tr('Rename'), _tr('Tomato is busy syncing. Try again in a moment.'))

    def _delete(self):
        name = self.current_name()
        if name is None:
            return
        _next, count = self.host.task_info(name)
        question = _tr('Delete the task "%1"? %n scheduled items that use it are deleted too. The folder goes to the Trash.')
        if not tomato_confirm(self, _tr('Delete'), question.replace('%1', name).replace('%n', str(count))):
            return
        self._save_timer.stop()
        self._dirty = False
        if self.host.delete_task(name):
            self._loaded = None
            self.refresh()
        else:
            tomato_alert(self, _tr('Delete'), _tr('Tomato is busy syncing. Try again in a moment.'))

    def _show_in_finder(self):
        name = self.current_name()
        if name is not None:
            subprocess.Popen(['/usr/bin/open', self.store.path(name)])

    def done(self, result):
        self.save_now()
        super().done(result)
