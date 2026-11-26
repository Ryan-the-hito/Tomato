# -*- coding: utf-8 -*-
"""The windows of the reports (tomato_report.py holds the rules).

2026-11-24 — Ryan: "我希望这个界面就像 broccoli 的初始界面一样，因为现在没有选择生成报告语言的地方". He chose to copy
Broccoli's activity panel whole (style book 5.7.8): the month on the left, four numbers on the right, under them the
Daily / Weekly / Monthly bar with the report language on its right, the report, and at the bottom the template ·
language line with Write now / Regenerate. The window stays Tomato's own (style book 5.12 dialog: the window is the
card, grey buttons); the report is shown in the page preview Tomato already uses.

  ReportDialog      the panel.
  ReportCalendar    the month: days with a record shaded in three steps of the system accent by their time in
                    front of the computer (against the month's longest day), today ringed, the chosen day framed.
  ReportStatTile    one of the four numbers.
  LanguagesDialog   the report languages: one grey button each (✓ = in use), right click Remove, a box and Add
                    (= Broccoli's Settings › Reports language row).
  TemplateDialog    the person's template of one kind of report.

What the calendar needs (the diaries of a month) is read on a worker thread; the answer comes back by a signal.
"""
import datetime
import threading

import os

from PyQt6.QtCore import QObject, QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMenu, QPlainTextEdit,
                             QVBoxLayout, QWidget)

from glass_kit import _tr, DropdownButton, MacNormalButton, PillNavBar, is_dark_theme, style_broccoli_context_menu
from tomato_ui import GlassFormDialog, GREY_ROW_HEIGHT, accent_color
import share_picture
import tomato_preview
import tomato_report

app = QApplication.instance()

CAL_CELL_W = 30          # = Broccoli's ACTIVITY_CAL_* (style book 5.7.8)
CAL_CELL_H = 26
CAL_GAP = 4
CAL_DOW_H = 16
CAL_RADIUS = 8
CAL_PAD = 4              # room left and right of the cells for the chosen day's frame
EDIT_LANGUAGES = '\x00edit'
KIND_LABELS = ('Daily', 'Weekly', 'Monthly')        # _tr'd where shown


def _dark():
    try:
        return bool(is_dark_theme(app))
    except Exception:
        return False


def hours_text(seconds):
    hours = max(0, seconds) / 3600.0
    if hours <= 0:
        return '0'
    return ('%.1f' % hours).rstrip('0').rstrip('.') if hours < 10 else '%d' % round(hours)


class ReportCalendar(QWidget):
    """The month (= Broccoli's ActivityCalendar): Monday first; days without a record grey and not clickable."""
    day_clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.month = datetime.date.today().replace(day=1)
        self.today = datetime.date.today()
        self.selected = self.today
        self.days = {}
        self.dark = False
        self.setFixedSize(7 * CAL_CELL_W + 6 * CAL_GAP + 2 * CAL_PAD, CAL_DOW_H + 6 * (CAL_CELL_H + CAL_GAP))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_state(self, month, today, selected, days, dark):
        self.month, self.today, self.selected, self.days, self.dark = month, today, selected, days or {}, bool(dark)
        self.update()

    def cell_rect(self, day):
        row, column = divmod(self.month.weekday() + day - 1, 7)
        return QRectF(CAL_PAD + column * (CAL_CELL_W + CAL_GAP), CAL_DOW_H + row * (CAL_CELL_H + CAL_GAP), CAL_CELL_W, CAL_CELL_H)

    def _month_days(self):
        return tomato_report.period('month', self.month.strftime('%Y-%m'))[1].day

    def day_at(self, pos):
        for day in range(1, self._month_days() + 1):
            if self.cell_rect(day).contains(QPointF(pos)):
                return self.month.replace(day=day)
        return None

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        day = self.day_at(event.position())
        if day is not None and day.isoformat() in self.days:
            self.day_clicked.emit(day)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        fg = QColor('#F2F2F7') if self.dark else QColor('#20242B')
        muted = QColor('#8E8E93')
        accent = accent_color()
        font = QFont('Helvetica Neue')
        font.setPixelSize(11)
        painter.setFont(font)
        painter.setPen(muted)
        names = [_tr('Mon'), _tr('Tue'), _tr('Wed'), _tr('Thu'), _tr('Fri'), _tr('Sat'), _tr('Sun')]
        for column, name in enumerate(names):
            painter.drawText(QRectF(CAL_PAD + column * (CAL_CELL_W + CAL_GAP), 0, CAL_CELL_W, CAL_DOW_H), int(Qt.AlignmentFlag.AlignCenter), name)
        font.setPixelSize(12)
        painter.setFont(font)
        prefix = self.month.strftime('%Y-%m')
        busiest = max([slot['seconds'] for day, slot in self.days.items() if day.startswith(prefix)] or [0])
        shades = (0.28, 0.52, 0.82) if self.dark else (0.22, 0.45, 0.75)
        for day in range(1, self._month_days() + 1):
            date = self.month.replace(day=day)
            rect = self.cell_rect(day)
            slot = self.days.get(date.isoformat())
            level = tomato_report.heat_level(slot['seconds'], busiest) if slot else 0
            if slot and not level:
                level = 1                      # a day with a record but no app time (only notes, meals): the lightest
            if level:
                fill = QColor(accent)
                fill.setAlphaF(shades[level - 1])
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(fill)
                painter.drawRoundedRect(rect, CAL_RADIUS, CAL_RADIUS)
            if date == self.today:
                painter.setPen(QPen(accent, 2.0))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), CAL_RADIUS - 1, CAL_RADIUS - 1)
            if date == self.selected and slot:
                painter.setPen(QPen(fg, 2.0))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), CAL_RADIUS + 2, CAL_RADIUS + 2)
            painter.setPen(QColor('#FFFFFF') if level == 3 else (fg if slot else muted))
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), str(day))
        painter.end()


class ReportStatTile(QWidget):
    """One of the four numbers (= Broccoli's ActivityStatTile): the number 18 bold, its caption 11 grey after it."""

    def __init__(self, caption, parent=None):
        super().__init__(parent)
        self.caption = caption
        self.value = '–'
        self.dark = False
        self.setFixedHeight(34)
        self.setMinimumWidth(120)

    def set_value(self, value, dark, caption=None):
        self.value, self.dark = str(value), bool(dark)
        if caption is not None:
            self.caption = caption
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 18) if self.dark else QColor(0, 0, 0, 12))
        painter.drawRoundedRect(QRectF(self.rect()), 10, 10)
        font = QFont('Helvetica Neue')
        font.setPixelSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor('#F2F2F7') if self.dark else QColor('#20242B'))
        number_w = 44
        painter.drawText(QRectF(10, 0, number_w, self.height()), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), self.value)
        font.setPixelSize(11)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor('#8E8E93'))
        room = self.width() - 10 - number_w - 8
        caption = QFontMetrics(font).elidedText(self.caption, Qt.TextElideMode.ElideRight, room)
        painter.drawText(QRectF(10 + number_w, 0, room, self.height()), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), caption)
        painter.end()


class LanguageRow(QWidget):
    """One grey button per report language, wrapping onto more lines; ✓ before the one in use. Click = use it;
    right click = Remove (= Broccoli's ReportLanguageRow)."""
    chosen = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    GAP = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.languages, self.current, self.buttons = [], '', []
        sizing = self.sizePolicy()
        sizing.setHeightForWidth(True)
        self.setSizePolicy(sizing)

    def set_languages(self, languages, current):
        for button in self.buttons:
            button.deleteLater()
        self.languages, self.current, self.buttons = list(languages), str(current or ''), []
        for language in self.languages:
            button = MacNormalButton(('✓ ' if language == self.current else '') + language, self)
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.clicked.connect(lambda _checked=False, value=language: self.chosen.emit(value))
            button.customContextMenuRequested.connect(lambda pos, value=language, b=button: self._menu(b, pos, value))
            button.show()
            self.buttons.append(button)
        self._place(self.width())
        self.updateGeometry()

    def _menu(self, button, pos, value):
        menu = style_broccoli_context_menu(QMenu(self))
        remove = menu.addAction(_tr('Remove'))
        remove.setEnabled(len(self.languages) > 1)
        if menu.exec(button.mapToGlobal(pos)) is remove:
            self.remove_requested.emit(value)

    def _place(self, width, move=True):
        x = y = 0
        width = max(1, int(width))
        for button in self.buttons:
            w = button.sizeHint().width()
            if x and x + w > width:
                x, y = 0, y + button.height() + self.GAP
            if move:
                button.setGeometry(x, y, w, button.height())
            x += w + self.GAP
        return (y + 22) if self.buttons else 0

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._place(width, move=False)

    def sizeHint(self):
        return QSize(300, self.heightForWidth(max(300, self.width())))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place(self.width())


class LanguagesDialog(GlassFormDialog):
    """The report languages; every change is kept at once (as Broccoli's settings page)."""

    def __init__(self, host, parent=None):
        super().__init__(_tr('Report languages'), parent, ok_text=_tr('Close'))
        self.host = host
        self.cancel_button.hide()
        hint = QLabel(_tr('Reports are written in the one with ✓. Add a language, or a language with a tone (for example “English (work)”). Right-click one to remove it.'), self)
        hint.setWordWrap(True)
        hint.setStyleSheet('color: #8E8E93; font-size: 11px;')
        self.row = LanguageRow(self)
        self.row.chosen.connect(self._choose)
        self.row.remove_requested.connect(self._remove)
        self.edit = QLineEdit(self)
        self.edit.setFixedHeight(GREY_ROW_HEIGHT)
        self.edit.setPlaceholderText(_tr('New language'))
        self.edit.returnPressed.connect(self._add)
        self.add_button = MacNormalButton(_tr('Add'), self)
        self.add_button.setMinimumWidth(96)
        self.add_button.clicked.connect(self._add)
        add_row = QHBoxLayout()
        add_row.setContentsMargins(0, 0, 0, 0)
        add_row.setSpacing(8)
        add_row.addWidget(self.edit, 1)
        add_row.addWidget(self.add_button)
        self.body.addWidget(hint)
        self.body.addWidget(self.row)
        self.body.addLayout(add_row)
        for button in (self.ok_button, self.add_button):
            button.setDefault(False)
            button.setAutoDefault(False)
        self.resize(440, 10)
        self._show()

    def _show(self):
        languages, current = self.host.report_languages()
        self.row.set_languages(languages, current)
        self.adjustSize()

    def _choose(self, language):
        self.host.set_report_language(language)
        self._show()

    def _remove(self, language):
        languages, current = self.host.report_languages()
        rest = [item for item in languages if item != language]
        if rest:
            self.host.set_report_languages(rest, current if current in rest else rest[0])
        self._show()

    def _add(self):
        text = ' '.join(self.edit.text().split())[:tomato_report.LANGUAGE_MAX_CHARS]
        if not text:
            return
        languages, _current = self.host.report_languages()
        if text not in languages:
            languages = languages + [text]
        self.host.set_report_languages(languages, text)
        self.edit.clear()
        self._show()


class TemplateDialog(GlassFormDialog):
    """saved(text): '' = back to the default of the report language."""
    saved = pyqtSignal(str)

    def __init__(self, title, text, default_text, parent=None):
        super().__init__(title, parent, ok_text=_tr('Save'))
        self._default = default_text
        hint = QLabel(_tr('The written part keeps these headings, in this order. Under each heading, say what belongs there.'), self)
        hint.setWordWrap(True)
        hint.setStyleSheet('color: #8E8E93; font-size: 11px;')
        self.editor = QPlainTextEdit(self)
        self.editor.setObjectName('edit')                 # the big input box (style book 5.4)
        self.editor.setPlainText(text)
        self.editor.setMinimumSize(460, 300)
        self.body.addWidget(hint)
        self.body.addWidget(self.editor, 1)
        self.reset_button = MacNormalButton(_tr('Use Default'), self)
        self.reset_button.setMinimumWidth(96)
        self.reset_button.clicked.connect(lambda: self.editor.setPlainText(self._default))
        row = self.layout().itemAt(self.layout().count() - 1).layout()
        row.insertWidget(0, self.reset_button)
        for button in (self.ok_button, self.cancel_button, self.reset_button):
            button.setDefault(False)                       # Return writes a new line here
            button.setAutoDefault(False)
        self.adjustSize()
        self.editor.setFocus()

    def accept(self):
        text = self.editor.toPlainText()
        self.saved.emit('' if text.strip() == self._default.strip() else text)
        super().accept()


class SharePictureDialog(GlassFormDialog):
    """The finished share picture: a preview, Copy Image, Save As (= Broccoli's share panel, as an edit-type
    dialog; style book 5.12, 2026-11-25)."""
    PREVIEW = (460, 460)

    def __init__(self, pixmap, file_stem='Tomato-report', parent=None):
        super().__init__(_tr('Share'), parent, ok_text=_tr('Close'))
        self._pixmap = QPixmap(pixmap)
        self._file_stem = file_stem
        self.cancel_button.hide()
        self.preview = QLabel(self)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(*self.PREVIEW)
        dark = _dark()
        self.preview.setStyleSheet('QLabel { border: 1px solid %s; border-radius: 12px; background: %s; padding: 10px; }'
                                   % (('#4A4B4F', '#343436') if dark else ('#E2E5EA', '#F7F8FA')))
        try:
            scale = float(self.devicePixelRatioF())
        except Exception:
            scale = 1.0
        self.preview.setPixmap(share_picture.share_preview_pixmap(self._pixmap, self.PREVIEW[0] - 22, self.PREVIEW[1] - 22, scale))
        self.body.addWidget(self.preview, 1)
        self.copy_button = MacNormalButton(_tr('Copy Image'), self)
        self.save_button = MacNormalButton(_tr('Save As'), self)
        row = self.layout().itemAt(self.layout().count() - 1).layout()
        for index, button in enumerate((self.copy_button, self.save_button)):
            button.setMinimumWidth(96)
            button.setAutoDefault(False)
            row.insertWidget(index, button)
        self.ok_button.setDefault(False)
        self.ok_button.setAutoDefault(False)
        self.copy_button.clicked.connect(self.copy_image)
        self.save_button.clicked.connect(self.save_image_as)
        self.adjustSize()

    def pixmap(self):
        return self._pixmap

    def copy_image(self):
        if not self._pixmap.isNull():
            QApplication.clipboard().setPixmap(self._pixmap)

    def save_image_to(self, path) -> bool:
        return bool(path) and not self._pixmap.isNull() and self._pixmap.save(path, 'PNG')

    def save_image_as(self):
        if self._pixmap.isNull():
            return
        default_path = os.path.join(os.path.expanduser('~'), self._file_stem + '.png')
        target, _ = QFileDialog.getSaveFileName(self, _tr('Save share image'), default_path, _tr('PNG Image (*.png)'))
        if target:
            self.save_image_to(target)


class _IndexSignals(QObject):
    ready = pyqtSignal(int, object, int)        # generation, {day: slot}, streak


class ReportDialog(GlassFormDialog):
    """host: report_text(kind, key) → (markdown, '' | 'numbers' | 'written', meta), report_html(markdown),
    make_report(kind, key), report_status(kind, key) → text | '', report_has_record(kind, key) → bool,
    report_template(kind) → (text, default), save_report_template(kind, text), report_languages() → (list, current),
    set_report_language(text), set_report_languages(list, current), report_auto() / set_report_auto(bool),
    report_slots(days) → {day: {'seconds', 'done'}} and report_streak(today) (both called on a worker thread)."""

    def __init__(self, host, parent=None):
        super().__init__(_tr('Reports'), parent, ok_text=_tr('Close'))
        self.host = host
        self.cancel_button.hide()
        self.ok_button.setDefault(False)
        self.ok_button.setAutoDefault(False)
        self.today = datetime.date.today()
        self.selected = self.today
        self.month = self.today.replace(day=1)
        self.kind = 'day'
        self.days = {}
        self.streak = 0
        self._generation = 0
        self._picked = False
        self._shown = None
        self._template_dialog = None
        self._languages_dialog = None
        self._share_dialog = None
        self._share_maker = None
        self._report_text = ''
        self._signals = _IndexSignals(self)
        self._signals.ready.connect(self._on_index)

        # ── top: the month left, the numbers right ──
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(14 - CAL_PAD)
        calendar_box = QVBoxLayout()
        calendar_box.setSpacing(6)
        header = QHBoxLayout()
        header.setContentsMargins(CAL_PAD, 0, CAL_PAD, 0)
        header.setSpacing(6)
        self.month_label = QLabel(self)
        self.prev_button = MacNormalButton('‹', self)
        self.next_button = MacNormalButton('›', self)
        for button in (self.prev_button, self.next_button):
            button.setFixedWidth(26)
            button.setAutoDefault(False)
        self.prev_button.setToolTip(_tr('Previous month'))
        self.next_button.setToolTip(_tr('Next month'))
        self.prev_button.clicked.connect(lambda: self.turn_month(-1))
        self.next_button.clicked.connect(lambda: self.turn_month(1))
        header.addWidget(self.month_label, 1)
        header.addWidget(self.prev_button)
        header.addWidget(self.next_button)
        calendar_box.addLayout(header)
        self.calendar = ReportCalendar(self)
        self.calendar.day_clicked.connect(self.choose_day)
        calendar_box.addWidget(self.calendar)
        top.addLayout(calendar_box, 0)

        stats_box = QVBoxLayout()
        stats_box.setSpacing(8)
        tiles = QVBoxLayout()
        tiles.setSpacing(6)
        self.days_tile = ReportStatTile(_tr('Days with a record this month'), self)
        self.time_tile = ReportStatTile(_tr('Hours that day'), self)
        self.done_tile = ReportStatTile(_tr('Items done'), self)
        self.streak_tile = ReportStatTile(_tr('Days in a row'), self)
        stats_box.addSpacing(28)   # level with the calendar's first row
        for tile in (self.days_tile, self.time_tile, self.done_tile, self.streak_tile):
            tiles.addWidget(tile)
        stats_box.addLayout(tiles)
        stats_box.addStretch(1)
        self.legend_label = QLabel(_tr('Shade = time on the computer that day'), self)
        self.legend_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        stats_box.addWidget(self.legend_label)
        top.addLayout(stats_box, 1)
        self.body.addLayout(top)

        # ── the report ──
        body = QVBoxLayout()
        body.setContentsMargins(CAL_PAD, 4, 0, 0)
        body.setSpacing(10)
        report_header = QHBoxLayout()
        report_header.setSpacing(8)
        self.kind_bar = PillNavBar([_tr(label) for label in KIND_LABELS], 0, self)
        self.kind_bar.setFixedWidth(220)
        self.kind_bar.tab_changed.connect(self._on_kind_changed)
        self.language_combo = DropdownButton(self, compact_light=True)
        # wide enough for a whole language name (= Broccoli, Ryan 11-14: "语言的选择条可以长一点，显示不全")
        self.language_combo.setFitToCurrentText(True)
        self.language_combo.setMinimumWidth(150)
        self.language_combo.setMaximumWidth(280)
        self.language_combo.setToolTip(_tr('The language and tone new reports are written in'))
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        report_header.addWidget(self.kind_bar, 0)
        report_header.addStretch(1)
        report_header.addWidget(self.language_combo, 0)
        body.addLayout(report_header)
        self.report_title = QLabel(self)
        body.addWidget(self.report_title)
        self.page = tomato_preview.MarkdownWebPreview(self)
        self.page.setMinimumSize(560, 260)
        body.addWidget(self.page, 1)
        footer = QHBoxLayout()
        footer.setSpacing(8)
        self.meta_label = QLabel(self)
        self.meta_label.setWordWrap(False)
        self.template_button = MacNormalButton(_tr('Template…'), self)
        self.write_button = MacNormalButton(_tr('Write now'), self)
        for button in (self.template_button, self.write_button):
            button.setMinimumWidth(96)
            button.setAutoDefault(False)
        # Ryan 2026-11-25: "每天的汇报…我是希望他可以截图分享的…什么都没有选中直接点击分享…全部的内容形成一条长图，
        # 选中了一部分内容…只把选中的那一部分去生成图片"
        self.share_button = MacNormalButton(_tr('Share'), self)
        self.share_button.setAutoDefault(False)
        self.share_button.setToolTip(_tr('A picture of this report — of the selected text, when some is selected'))
        self.share_button.clicked.connect(self.share)
        self.template_button.clicked.connect(self._edit_template)
        self.write_button.clicked.connect(self._on_write)
        footer.addWidget(self.meta_label, 1)
        footer.addWidget(self.share_button, 0)
        footer.addWidget(self.template_button, 0)
        footer.addWidget(self.write_button, 0)
        body.addLayout(footer)
        self.body.addLayout(body, 1)

        # ── the window's own row: when reports are written by themselves, Close ──
        self.auto_check = QCheckBox(_tr('Write by themselves: daily at 23:30, weekly on Sunday, monthly at month end'), self)
        self.auto_check.setChecked(bool(host.report_auto()))
        self.auto_check.toggled.connect(host.set_report_auto)
        row = self.layout().itemAt(self.layout().count() - 1).layout()
        row.insertWidget(0, self.auto_check)
        self._apply_theme()
        self.set_languages()
        self.resize(660, 740)
        self.refresh()

    # ── what is shown ──
    def key(self):
        if self.kind == 'month':
            return self.month.strftime('%Y-%m')
        return tomato_report.key_for(self.kind, self.selected)

    def show_day(self, day, kind=None):
        """Opens on a day (a week's / month's key: its first day) and, given, a kind."""
        text = str(day or '')
        try:
            date = datetime.date.fromisoformat(text[:10] if len(text) >= 10 else text[:7] + '-01')
        except ValueError:
            date = datetime.date.today()
        self.today = datetime.date.today()
        self.selected = min(date, self.today)
        self.month = self.selected.replace(day=1)
        self._picked = True
        if kind in tomato_report.KINDS and kind != self.kind:
            self.kind = kind
            self.kind_bar.select(tomato_report.KINDS.index(kind))      # → _on_kind_changed → refresh
        self.refresh()

    def set_languages(self):
        languages, current = self.host.report_languages()
        combo = self.language_combo
        combo.blockSignals(True)
        try:
            combo.clear()
            for language in languages:
                combo.addItem(language, language)
            combo.addItem(_tr('Edit languages…'), EDIT_LANGUAGES)
            index = combo.findData(current)
            combo.setCurrentIndex(index if index >= 0 else 0)
        finally:
            combo.blockSignals(False)

    def turn_month(self, step):
        month = self.month.month - 1 + step
        self.month = datetime.date(self.month.year + month // 12, month % 12 + 1, 1)
        self.refresh()

    def choose_day(self, day):
        self.selected = day
        self.month = day.replace(day=1)
        self._picked = True
        if self.kind == 'month':
            self.kind = 'day'
            self.kind_bar.select(0)
        self.refresh()

    def _on_kind_changed(self, index):
        self.kind = tomato_report.KINDS[max(0, min(2, int(index)))]
        self.refresh()

    def _on_language_changed(self, _index):
        data = self.language_combo.currentData()
        if data == EDIT_LANGUAGES:
            self.set_languages()                 # the box shows the language in use again
            self._edit_languages()
            return
        if data:
            self.host.set_report_language(str(data))
            self.refresh_report()

    def _edit_languages(self):
        if self._languages_dialog is not None and self._languages_dialog.isVisible():
            self._languages_dialog.raise_()
            return
        self._languages_dialog = LanguagesDialog(self.host, None)
        self._languages_dialog.finished.connect(lambda _result: (self.set_languages(), self.refresh_report()))
        self._languages_dialog.show()
        self._languages_dialog.raise_()

    def _on_write(self):
        kind, key = self.kind, self.key()
        if self.host.report_status(kind, key):
            return
        self.host.make_report(kind, key)
        self.refresh()

    def _period_days(self):
        return tomato_report.period_days(self.kind, self.key())

    def refresh(self, kind=None, key=None):
        """Shows the chosen month and report again (kind / key given: only when that one is on show), and asks
        a worker for the month's days."""
        if kind is not None and (kind, key) != (self.kind, self.key()):
            self._load_index()
            return
        self.today = datetime.date.today()
        if self.selected > self.today:
            self.selected = self.today
        self._load_index()
        self._paint_numbers()
        self.refresh_report()

    def _load_index(self):
        days = set(tomato_report.period_days('month', self.month.strftime('%Y-%m'))) | set(self._period_days())
        self._generation += 1
        generation, host, signals, today = self._generation, self.host, self._signals, self.today

        def work():
            try:
                slots = host.report_slots(sorted(days))
                streak = host.report_streak(today)
            except Exception:
                slots, streak = {}, 0
            try:
                signals.ready.emit(generation, slots, streak)
            except RuntimeError:
                pass                         # the window went away meanwhile
        threading.Thread(target=work, name='tomato-report-index', daemon=True).start()

    def _on_index(self, generation, slots, streak):
        self.days.update(slots or {})
        asked = set(tomato_report.period_days('month', self.month.strftime('%Y-%m'))) | set(self._period_days())
        for day in asked - set(slots or {}):
            self.days.pop(day, None)          # a day whose record is gone
        self.streak = int(streak)
        if not self._picked and self.selected.isoformat() not in self.days:
            used = sorted(day for day in self.days if day <= self.today.isoformat() and day.startswith(self.month.strftime('%Y-%m')))
            if used:
                self.selected = datetime.date.fromisoformat(used[-1])
                self._picked = True
                self.refresh()
                return
        self._picked = self._picked or self.selected.isoformat() in self.days
        self._paint_numbers()
        self.refresh_report()

    def _paint_numbers(self):
        dark = _dark()
        prefix = self.month.strftime('%Y-%m')
        self.month_label.setText(prefix)
        self.next_button.setEnabled(self.month < self.today.replace(day=1))
        in_period = [self.days[day] for day in self._period_days() if day in self.days]
        caption = {'day': _tr('Hours that day'), 'week': _tr('Hours that week'), 'month': _tr('Hours that month')}[self.kind]
        self.days_tile.set_value(sum(1 for day in self.days if day.startswith(prefix)), dark)
        self.time_tile.set_value(hours_text(sum(slot['seconds'] for slot in in_period)), dark, caption)
        self.done_tile.set_value(sum(slot['done'] for slot in in_period), dark)
        self.streak_tile.set_value(self.streak, dark)
        self.calendar.set_state(self.month, self.today, self.selected, self.days, dark)

    def refresh_report(self):
        kind, key = self.kind, self.key()
        self.report_title.setText(tomato_report.period_label(kind, key))
        text, mark, meta = self.host.report_text(kind, key)
        waiting = self.host.report_status(kind, key)
        has_record = self.host.report_has_record(kind, key)
        if text:
            markdown = text
        elif has_record:
            markdown = _tr('No report yet. Tomato writes it by itself, or now with “Write now”.')
        else:
            markdown = _tr('Nothing was recorded on this day.') if kind == 'day' else _tr('Nothing was recorded in this period.')
        self._report_text = text or ''
        self._sync_share_button()
        shown = (kind, key, markdown)
        if shown != self._shown:
            self._shown = shown
            self.page.setHtml(self.host.report_html(markdown))
        if waiting:
            status = waiting
        elif mark == 'written':
            status = _tr('Written by Broccoli, numbers by Tomato')
        elif mark == 'numbers':
            status = _tr('Numbers only')
        else:
            status = ''
        # "template · language" (= Broccoli's footer): of the report on show, else of the next one written
        template_text, default = self.host.report_template(kind)
        own = template_text.strip() != default.strip()
        if text and meta.get('template') in ('own', 'default'):
            own = meta.get('template') == 'own'
        template = _tr('Own template') if own else _tr('Default template')
        if text and meta.get('language'):
            language = str(meta.get('language'))
        else:
            language = self.host.report_languages()[1]
        self.meta_label.setText(' · '.join(part for part in (status, template, language) if part))
        self.write_button.setText(_tr('Regenerate') if text else _tr('Write now'))
        self.write_button.setEnabled(bool(has_record) and not waiting)

    # ── Share: a long picture of the report, or of the selected part ──
    def _sync_share_button(self):
        making = self._share_maker is not None and self._share_maker.busy()
        self.share_button.setEnabled(bool(self._report_text.strip()) and not making)

    def share(self):
        if not self._report_text.strip() or (self._share_maker is not None and self._share_maker.busy()):
            return
        self.share_button.setEnabled(False)
        self.page.run_javascript(share_picture.SHARE_SELECTION_JS, self._share_with_selection)

    def _share_with_selection(self, selection):
        only = ''
        if isinstance(selection, dict) and str(selection.get('text') or '').strip():
            only = str(selection.get('html') or '').strip()
        if only:
            markdown = self._report_text                      # the page's styles; only the selected part is shown
        else:
            markdown = '## %s\n\n%s' % (self.report_title.text(), self._report_text)
        if self._share_maker is None:
            self._share_maker = share_picture.SharePictureMaker(self)
            self._share_maker.finished.connect(self._on_share_picture)
        started = self._share_maker.make(self.host.report_html(markdown), self.page.base_url(),
                                         max(360, min(900, self.page.width())), False, only_html=only)   # the page is always the light one
        if not started:
            self._sync_share_button()

    def _on_share_picture(self, pixmap):
        self._sync_share_button()
        if pixmap is None or pixmap.isNull():
            return
        if self._share_dialog is not None:
            self._share_dialog.close()
        stem = 'Tomato-report-%s' % self.key()
        self._share_dialog = SharePictureDialog(pixmap, stem, None)
        self._share_dialog.show()
        # over the report window, not wherever the system puts a new window
        mine, size = self.frameGeometry(), self._share_dialog.frameGeometry()
        self._share_dialog.move(mine.center().x() - size.width() // 2, max(mine.top(), mine.center().y() - size.height() // 2))
        self._share_dialog.raise_()

    def _edit_template(self):
        if self._template_dialog is not None and self._template_dialog.isVisible():
            self._template_dialog.raise_()
            return
        kind = self.kind
        text, default = self.host.report_template(kind)
        title = _tr('Report template') + ' · ' + _tr(KIND_LABELS[tomato_report.KINDS.index(kind)])
        self._template_dialog = TemplateDialog(title, text, default, None)
        self._template_dialog.saved.connect(lambda value, k=kind: self.host.save_report_template(k, value))
        self._template_dialog.show()
        self._template_dialog.raise_()

    # ── looks ──
    def _apply_theme(self):
        dark = _dark()
        fg = '#F2F2F7' if dark else '#20242B'
        self.month_label.setStyleSheet('QLabel { color: %s; font-size: 15px; font-weight: 700; }' % fg)
        self.report_title.setStyleSheet('QLabel { color: %s; font-size: 13px; font-weight: 700; }' % fg)
        self.meta_label.setStyleSheet('QLabel { color: #8E8E93; font-size: 11px; }')
        self.legend_label.setStyleSheet('QLabel { color: #8E8E93; font-size: 11px; }')
        self.kind_bar.set_theme('dark' if dark else 'light')
        if hasattr(self.language_combo, '_update_style'):
            self.language_combo._update_style()
        for button in (self.prev_button, self.next_button, self.share_button, self.template_button, self.write_button):
            button.update_theme()

    def changeEvent(self, event):
        super().changeEvent(event)
        from PyQt6.QtCore import QEvent
        if event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange) and hasattr(self, 'write_button'):
            self._apply_theme()
            self._paint_numbers()
