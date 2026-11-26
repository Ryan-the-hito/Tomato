# -*- coding: utf-8 -*-
"""Tomato's Liquid Glass UI (2026-11-15) — the parts built on glass_kit.py.

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (section 5.12)
Ryan 2026-11-15: "按我们在 broccoli 里面的样式书，去把 tomato 也修成液态玻璃的。我希望的样子是表格整个在
底下，然后编辑的部分使用液态玻璃的浮窗浮在上面。" He chose: one panel at the bottom of each page, the panel can
be pushed in (a drawer), date / time boxes = normal inputs with glass pop-ups, Chinese / Japanese this time.

Most of this is Strawberry's code (its main file, 2026-11-11: SectionCard, GlassTabWidget, GlassIconButton,
FloatCardGlass, the card drawer) turned from a drawer on the left into a drawer at the bottom. What
Strawberry learned and this keeps:
 - a panel inside the window is REAL system Liquid Glass, and right under the glass lies a picture of
   Tomato's own content under it (the table) — never the desktop through the window;
 - the content under the panel (the table) has no panel of its own and never moves or shrinks;
 - the glass is told light / dark explicitly; in-window glass of buttons is clipped while the panel slides;
 - the handle also comes up while Tomato is not the front app (a native tracking area).
Import this module AFTER the QApplication exists.
"""
import os
import sys
import math
import logging
import weakref
from ctypes import c_void_p
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget,
                             QSizePolicy, QSpacerItem, QDialog, QLineEdit, QAbstractItemView, QStyledItemDelegate,
                             QStyle, QAbstractScrollArea, QTableWidget, QDateEdit, QTimeEdit, QGraphicsScene,
                             QGraphicsPathItem, QGraphicsDropShadowEffect)
from PyQt6.QtCore import (Qt, QRect, QRectF, QPoint, QPointF, QSize, QTimer, QEvent, QObject, pyqtSignal,
                          QVariantAnimation, QEasingCurve, QCoreApplication, QTranslator, QLocale, QBuffer, QByteArray)
from PyQt6.QtGui import (QColor, QPainter, QPainterPath, QPen, QBrush, QLinearGradient, QFont, QFontMetrics, QIcon,
                         QImage, QPixmap, QPalette, QCursor)

app = QApplication.instance()
if app is None:
    raise RuntimeError('tomato_ui: create the QApplication before importing this module')

import glass_kit
from glass_kit import (_tr, is_dark_theme, on_theme_changed, install_theme_observer, SmoothPanelWidget, PillNavBar,
                       MacNormalButton, WhiteButton, StrawberryDropdown, glass_button, glass_corner_radius,
                       edge_hint_symbol_pixmap, keep_scroll_bar_knob, install_window_liquid_glass,
                       install_native_traffic_lights, approval_window_width, show_broccoli_message,
                       ask_broccoli_message, liquid_glass_available, smooth_round_rect_path,
                       _settings_table_stylesheet, MAIN_WINDOW_SMOOTH_RADIUS, NATIVE_TITLEBAR_HEIGHT)

SECTION_CARD_RADIUS = 36        # smooth radius; = glass 16 (tier 3, like every floating panel)
SECTION_CARD_MARGIN = 14        # content inset inside the panel (clears the corner)
GLASS_ICON_BUTTON_SIZE = 30     # a round button = as tall as a glass capsule (Strawberry, Ryan 2026-11-11)
MAIN_ROW_HEIGHT = 30            # glass white capsule (5.1); an input in its row takes this height
GREY_ROW_HEIGHT = 22            # grey normal button / compact drop-down / normal input (5.1, 5.2, 5.4)
POPUP_GLASS_RADIUS = 9          # small pop-up (tier 4): the calendar and the clock of a date / time box

_UI_SURFACES = weakref.WeakSet()   # everything that repaints itself for light / dark
_THEME_HOOKS = []                  # callback(dark) after the application stylesheet changed


def ui_palette(dark=None) -> dict:
    if dark is None:
        dark = is_dark_theme(app)
    if dark:
        return {'dark': True, 'body': QColor('#2D2D2D'), 'body_border': QColor('#2D2D2D'),
                'panel': QColor('#2D2D2D'), 'text': '#F2F2F7', 'secondary': '#8E8E93',
                'icon': QColor('#E6E6EA'), 'disc': '#3A3A3A', 'disc_border': '#4A4B4F', 'disc_down': '#323234'}
    return {'dark': False, 'body': QColor('#FFFFFF'), 'body_border': QColor('#ECECEC'),
            'panel': QColor('#FFFFFF'), 'text': '#20242B', 'secondary': '#8E8E93',
            'icon': QColor('#3A3D44'), 'disc': '#FFFFFF', 'disc_border': '#E3E3E6', 'disc_down': '#ECECEC'}


def accent_color() -> QColor:
    """The system accent colour (style book 5.8: never a fixed blue)."""
    return QColor(app.palette().color(QPalette.ColorRole.Accent))


FLOAT_CARD_GLASS_RADIUS = 16     # = smooth 36 (style book 2.1 tier 3)


class SectionCard(SmoothPanelWidget):
    """kind='card': the floating panel of a page (style book 5.12 / 5.10): real system Liquid Glass under
    it while it floats on the page's content (see FloatPanelStage); without glass it is drawn by Qt like
    Broccoli's sliding panels — a blurred picture of what lies under it in Tomato itself under a tint of
    the panel colour, a light rim and a hairline.
    kind='body': the main window body (solid, 36 smooth, like Broccoli's).
    kind='open': an area straight on the body with no panel and no edge.
    kind='plain': nothing."""

    def __init__(self, parent=None, kind='card'):
        super().__init__(parent)
        self._kind = kind
        self._dark = False
        self._frosted_source = None
        self._float_host = None     # the stage this panel floats in
        self._stage_glass = None    # its system Liquid Glass while it floats on the content
        _UI_SURFACES.add(self)
        self.apply_theme()

    def set_float_host(self, host):
        self._float_host = host
        self.update()

    def floats(self) -> bool:
        host = self._float_host
        try:
            return host is not None and host.cards_float()
        except RuntimeError:
            return False

    def glass_active(self) -> bool:
        helper = self._stage_glass
        return helper is not None and helper.wanted()

    def card_pad(self) -> int:
        return 0

    def set_frosted_source(self, source):
        """source() → (blurred picture, QRectF where it lies in this panel's coordinates) or None."""
        self._frosted_source = source
        self.update()

    def panel_rect(self) -> QRect:
        return self.rect()

    def apply_theme(self, dark=None):
        pal = ui_palette(dark)
        self._dark = pal['dark']
        if self._kind == 'body':
            self.set_smooth_panel_background(pal['body'], pal['body_border'], MAIN_WINDOW_SMOOTH_RADIUS)
        else:
            self.set_smooth_panel_background(pal['panel'], pal['panel'], SECTION_CARD_RADIUS, border_width=0.0)
        helper = getattr(self, '_stage_glass', None)
        if helper is not None and helper.glass is not None:
            try:
                helper.glass.setAppearance_(glass_kit._ns_appearance(self._dark))
            except Exception:
                pass
        self.update()

    def paintEvent(self, event):
        if self._kind in ('plain', 'open'):
            return
        if self._kind == 'body':
            super().paintEvent(event)
            return
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            dark = self._dark
            if self.floats() and self.glass_active():
                # system Liquid Glass lies under the Qt content here, over a picture of the table: cut what
                # the table (and the body) painted under this panel, so the glass shows
                cut = QPainterPath()
                cut.addRoundedRect(QRectF(self.rect()), FLOAT_CARD_GLASS_RADIUS, FLOAT_CARD_GLASS_RADIUS)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.fillPath(cut, QColor(0, 0, 0))
                return
            rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
            path = smooth_round_rect_path(rect, self._smooth_panel_radius)
            source = self._frosted_source
            backdrop = None
            if source is not None:
                try:
                    backdrop = source()
                except RuntimeError:
                    backdrop = None
            if backdrop is not None:
                pixmap, target = backdrop
                painter.save()
                painter.setClipPath(path)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
                painter.restore()
                tint = QColor(self._smooth_panel_bg)
                tint.setAlpha(198 if dark else 182)   # Broccoli's frosted panel
                painter.fillPath(path, tint)
            else:
                painter.fillPath(path, self._smooth_panel_bg)
            rim = QLinearGradient(0, 0, 0, max(1, self.height()))
            rim.setColorAt(0.0, QColor(255, 255, 255, 70 if dark else 235))
            rim.setColorAt(0.45, QColor(255, 255, 255, 22 if dark else 110))
            rim.setColorAt(1.0, QColor(255, 255, 255, 40 if dark else 170))
            pen = QPen(QBrush(rim), 1.3)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.strokePath(path, pen)
            painter.strokePath(path, QPen(QColor(0, 0, 0, 60 if dark else 22), 0.6))
        finally:
            painter.end()


class GlassTabWidget(SectionCard):
    """The QTabWidget calls Tomato makes (addTab, currentIndex, setCurrentIndex, currentChanged …) on the
    style book's top tab bar: a glass PillNavBar (36 high, sliding grey pill, 5.6), centred over a stack.
    QTabWidget itself is not used: its selected tab is not drawn under the system's new design (5.7.2)."""
    currentChanged = pyqtSignal(int)
    tabBarClicked = pyqtSignal(int)
    TAB_PAD = 28

    def __init__(self, parent=None, kind='body'):
        super().__init__(parent, kind=kind)
        self._labels = []
        self._nav = None
        self._stack = QStackedWidget(self)
        self._header = QHBoxLayout()
        self._header.setContentsMargins(0, 0, 0, 0)
        self._header.addStretch(1)
        self._header.addStretch(1)
        lay = QVBoxLayout(self)
        if kind == 'body':
            lay.setContentsMargins(6, 20, 6, 6)   # = Strawberry's main window body
            lay.setSpacing(6)
        else:
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(8)
        lay.addLayout(self._header)
        lay.addWidget(self._stack, 1)
        self._stack.currentChanged.connect(self._on_stack_changed)

    def _nav_width(self, nav) -> int:
        font = QFont(nav.font())
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        metrics = QFontMetrics(font)
        total = 4
        for label, button in zip(self._labels, nav._buttons):
            need = max(metrics.horizontalAdvance(label) + self.TAB_PAD, button.minimumSizeHint().width())
            button.setMinimumWidth(need)
            total += need
        return total

    def _rebuild_nav(self):
        current = max(0, self._stack.currentIndex())
        if self._nav is not None:
            self._header.removeWidget(self._nav)
            self._nav.hide()
            self._nav.deleteLater()
            self._nav = None
        if not self._labels:
            return
        nav = PillNavBar(list(self._labels), current, self)
        nav.set_theme('dark' if self._dark else 'light')
        nav.setFixedWidth(self._nav_width(nav))
        nav.tab_changed.connect(self._on_nav_clicked)
        self._header.insertWidget(1, nav)   # [stretch, bar, stretch]
        self._nav = nav

    def _on_nav_clicked(self, index):
        self._stack.setCurrentIndex(index)
        self.tabBarClicked.emit(index)

    def apply_theme(self, dark=None):
        super().apply_theme(dark)
        if getattr(self, '_nav', None) is not None:
            self._nav.set_theme('dark' if self._dark else 'light')

    def _on_stack_changed(self, index):
        if self._nav is not None and self._nav._current != index and index >= 0:
            self._nav.select(index)
        self.currentChanged.emit(index)

    # ── QTabWidget's API ──
    def addTab(self, widget, label):
        self._stack.addWidget(widget)
        self._labels.append(str(label))
        self._rebuild_nav()
        return self._stack.indexOf(widget)

    def count(self):
        return self._stack.count()

    def widget(self, index):
        return self._stack.widget(index)

    def indexOf(self, widget):
        return self._stack.indexOf(widget)

    def currentIndex(self):
        return self._stack.currentIndex()

    def currentWidget(self):
        return self._stack.currentWidget()

    def setCurrentIndex(self, index):
        self._stack.setCurrentIndex(index)

    def tabText(self, index):
        return self._labels[index] if 0 <= index < len(self._labels) else ''


class GlassIconButton(QPushButton):
    """The style book's round button (5.1): a glass disc with a system line icon 16 (SF Symbol, one
    colour, following light / dark). Without glass: the same disc, solid."""

    def __init__(self, symbol, parent=None, tooltip=''):
        super().__init__('', parent)
        self._symbol = str(symbol)
        self.setAutoDefault(False)
        self.setFixedSize(GLASS_ICON_BUTTON_SIZE, GLASS_ICON_BUTTON_SIZE)
        self.setIconSize(QSize(16, 16))
        if tooltip:
            self.setToolTip(tooltip)
        _UI_SURFACES.add(self)
        self.apply_theme()
        glass_button(self, radius_for=lambda b: b.height() / 2.0, dark_for=lambda b: is_dark_theme(app))

    def set_symbol(self, symbol):
        self._symbol = str(symbol)
        self.apply_theme()

    def apply_theme(self, dark=None):
        pal = ui_palette(dark)
        pixmap = edge_hint_symbol_pixmap(self._symbol, pal['icon'], 16)
        self.setIcon(QIcon(pixmap) if pixmap is not None else QIcon())
        self.setStyleSheet(
            'QPushButton { background-color: %s; border: 1px solid %s; border-radius: %dpx; padding: 0; }'
            ' QPushButton:pressed { background-color: %s; }'
            % (pal['disc'], pal['disc_border'], GLASS_ICON_BUTTON_SIZE // 2, pal['disc_down']))


def _button_highlight_qss() -> str:
    accent = accent_color()
    return ('QPushButton { border: 1px solid transparent; border-radius: 6px; background-color: %s; color: #FFFFFF;'
            ' padding: 1px 8px; font-size: 13px; } QPushButton:hover { background-color: %s; }'
            ' QPushButton:pressed { background-color: %s; }'
            % (accent.name(), accent.lighter(110).name(), accent.darker(112).name()))


def set_button_highlight(button, on: bool):
    """A grey normal button that is "on" (the chosen one of a pair) fills with the system accent and white
    text, like the pinned toggle (style book 5.1 / 5.8). The button's own restyling keeps it."""
    button._highlight = bool(on)
    button.update_theme()


_KIT_MAC_UPDATE_THEME = MacNormalButton.update_theme


def _mac_update_theme_keeping_highlight(self):
    if getattr(self, '_highlight', False):
        if not self._updating_style:
            self._updating_style = True
            try:
                self.setStyleSheet(_button_highlight_qss())
            finally:
                self._updating_style = False
        return
    _KIT_MAC_UPDATE_THEME(self)


MacNormalButton.update_theme = _mac_update_theme_keeping_highlight


# ── The floating edit panel of a page: a drawer at the bottom (style book 5.12) ───────────────────────────
PANEL_FLOAT_INSET = 14         # the panel floats this far inside the page's edges (= where the edge of a
                               # Strawberry card lies: 8 + its 6 of shadow margin; Ryan 2026-11-16)
PAGE_CONTENT_INSET = 18        # the table keeps this from the page's left, right and bottom edges (=
                               # Strawberry's editing area; Ryan 2026-11-16: "左右上下的 padding 不够")
PAGE_CONTENT_TOP = 10          # … and this below the tab bar's row
PANEL_SLIDE_MS = 250
PANEL_HOVER_DELAY_MS = 150     # the mouse only crossing the edge shows nothing (as 5.1.5)
PANEL_FADE_MS = 150
PANEL_HIDE_DELAY_MS = 250
PANEL_HOVER_POLL_MS = 60
PANEL_BAND_INSIDE = 28         # where the handle comes up: this far into the panel from its top edge …
PANEL_BAND_OUTSIDE = 44        # … to this far above it, all along it (pushed in: the page's bottom 44)
PANEL_HANDLE_GAP = 6           # the handle this far above the panel (pushed in: above the page's bottom edge)
PANEL_FROST_DELAY_MS = 120     # the picture under the panel is retaken this long after the table changed
PANEL_MIN_TABLE_SHOWN = 96     # at least this much of the page stays free above the panel
FLOAT_SHADOW_BLUR = 34.0       # Broccoli's floating panel shadow
FLOAT_SHADOW_DY = 10.0
FLOAT_SHADOW_MARGIN = 44
PANEL_UNDERLAY_MARGIN = 40     # the picture under the glass reaches this far past the panel
_FLOAT_SHADOW_CACHE = {}


def clip_inwindow_glass_to_visible(container):
    """The in-window glass of the buttons in `container` (it sits ON the Qt content, Qt does not clip it)
    shows only the part of its widget that the stage lets show (style book 4.3 rule 3)."""
    try:
        top = container.window()
        helpers = list(glass_kit._INWINDOW_GLASS_BY_WINDOW.get(id(top), []))
    except RuntimeError:
        return
    for helper in helpers:
        widget = getattr(helper, '_widget', None)
        try:
            if widget is None or getattr(helper, '_tomato_clipped', False) or not container.isAncestorOf(widget):
                continue
        except RuntimeError:
            continue
        helper._tomato_clipped = True
        base_wanted = helper._wanted_for
        helper._rect_for = lambda w=widget: glass_kit.glass_visible_part(w)
        helper._wanted_for = lambda w=widget, b=base_wanted: ((b is None or b())
                                                             and not glass_kit.glass_visible_part(w).isEmpty())


_PANEL_HOVER_OWNER_CLASS = []


def _panel_hover_owner(stage):
    """The owner of the stage's native hover area: macOS tells it when the mouse comes into / leaves the
    band even while Tomato is not the front app (Qt only hears the mouse in the front app, and Tomato sits
    beside other apps all day). None when AppKit is not there."""
    appkit, objc_ = glass_kit.AppKit, glass_kit.objc
    if appkit is None or objc_ is None:
        return None
    if not _PANEL_HOVER_OWNER_CLASS:
        class TomatoPanelHoverOwner(appkit.NSObject):
            def mouseEntered_(self, event):
                self._tell(True)

            def mouseExited_(self, event):
                self._tell(False)

            @objc_.python_method
            def _tell(self, entered):
                ref = getattr(self, 'py_stage', None)
                stage = ref() if ref is not None else None
                if stage is not None:
                    try:
                        stage.native_hover_changed(entered)
                    except RuntimeError:
                        pass
        _PANEL_HOVER_OWNER_CLASS.append(TomatoPanelHoverOwner)
    owner = _PANEL_HOVER_OWNER_CLASS[0].alloc().init()
    owner.py_stage = weakref.ref(stage)
    return owner


def _floating_shadow_image(width: int, height: int, dark: bool, ratio: float) -> QImage:
    """The soft shadow of a floating panel of the given size, with FLOAT_SHADOW_MARGIN around it; the
    panel's own area is cleared. Drawn once per size."""
    key = (width, height, dark, ratio)
    image = _FLOAT_SHADOW_CACHE.get(key)
    if image is not None:
        return image
    if len(_FLOAT_SHADOW_CACHE) > 32:
        _FLOAT_SHADOW_CACHE.clear()
    m = FLOAT_SHADOW_MARGIN
    shape = QPainterPath()
    shape.addRoundedRect(QRectF(m, m, max(1, width), max(1, height)), FLOAT_CARD_GLASS_RADIUS, FLOAT_CARD_GLASS_RADIUS)
    scene = QGraphicsScene()
    item = QGraphicsPathItem(shape)
    item.setBrush(QColor(0, 0, 0))
    item.setPen(QPen(Qt.PenStyle.NoPen))
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(FLOAT_SHADOW_BLUR)
    effect.setOffset(0, FLOAT_SHADOW_DY)
    effect.setColor(QColor(0, 0, 0, 120 if dark else 45))
    item.setGraphicsEffect(effect)
    scene.addItem(item)
    full_w, full_h = width + 2 * m, height + 2 * m
    image = QImage(int(math.ceil(full_w * ratio)), int(math.ceil(full_h * ratio)), QImage.Format.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(ratio)
    image.fill(0)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    scene.render(painter, QRectF(0, 0, full_w, full_h), QRectF(0, 0, full_w, full_h))
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    painter.fillPath(shape, QColor(0, 0, 0))
    painter.end()
    _FLOAT_SHADOW_CACHE[key] = image
    return image


class _FloatShadows(QWidget):
    """The floating panel's soft shadow on the table: one see-through sheet between the table and the
    panel (it takes no mouse)."""

    def __init__(self, stage):
        super().__init__(stage)
        self._stage = stage
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def paintEvent(self, event):
        stage = self._stage
        card = stage._cards
        if card is None or not stage.cards_float():
            return
        painter = QPainter(self)
        ratio = max(1.0, float(self.devicePixelRatioF()))
        m = FLOAT_SHADOW_MARGIN
        try:
            if card.isVisibleTo(stage):
                origin = card.mapTo(stage, QPoint(0, 0))
                painter.drawImage(QPointF(origin.x() - m, origin.y() - m),
                                  _floating_shadow_image(card.width(), card.height(), stage._dark, ratio))
        except RuntimeError:
            pass
        painter.end()


class FloatCardGlass(glass_kit.ChildLiquidGlass):
    """System Liquid Glass under the panel floating on the table (the kit's child glass: in the window's
    glass layer, under the Qt content — the panel's inputs and buttons stay ordinary widgets). What it
    shows is the stage's picture of the table lying right under it in the same layer — never the desktop
    (Ryan 2026-11-11 on Strawberry: "液态玻璃不代表去取桌面的色，他应该隐约透着编辑区的下面的文字").
    Stays inside the stage while the panel slides out."""

    def __init__(self, card, stage, dark):
        self._stage = stage
        super().__init__(card, FLOAT_CARD_GLASS_RADIUS, inset=card.card_pad(), dark=dark)
        self.sync(reorder=True)

    def wanted(self) -> bool:
        try:
            return self.glass is not None and self._stage.cards_float() and self._stage.underlay_ready()
        except RuntimeError:
            return False

    def _frame(self):
        frame = super()._frame()
        host = self._stage
        origin = host.mapTo(self._top, QPoint(0, 0))
        rect = QRectF(frame.origin.x, frame.origin.y, frame.size.width, frame.size.height).intersected(
            QRectF(origin.x(), origin.y(), host.width(), host.height()))
        if rect.isEmpty():
            return glass_kit.AppKit.NSMakeRect(origin.x(), origin.y(), 0, 0)
        return glass_kit.AppKit.NSMakeRect(rect.x(), rect.y(), rect.width(), rect.height())

    def sync(self, reorder=False):
        super().sync(reorder=reorder)
        try:
            if self.glass is not None and not self.wanted():
                self.glass.setHidden_(True)
        except Exception:
            pass

    def remove(self):
        try:
            for watched in self._watched:
                try:
                    watched.removeEventFilter(self)
                except RuntimeError:
                    pass
            if self.glass is not None:
                self.glass.removeFromSuperview()
        except Exception:
            pass
        self.deleteLater()


class FloatPanelStage(QWidget):
    """One page: its content (`content`: the table, the full size of the page, never moved or shrunk) with
    the edit panel (`panel`, a SectionCard 'card') floating on its lower part as a drawer. on_toggle(open)
    is called when the handle is clicked (the window keeps every page in step); set_open() moves the drawer.
    Pushed in, the panel slides out through the page's bottom edge and the whole table shows."""

    def __init__(self, content, panel, on_toggle=None, parent=None):
        super().__init__(parent)
        self._cards = None
        self._content = None
        self._painters = []         # widgets of the content whose repaint retakes the picture
        self._underlay = None       # blurred picture of the table where the panel lies (no glass)
        self._underlay_view = None  # glass: the picture itself, a view right under the panel's glass
        self._base_view = None      # glass: the body's own colour under all of it, as large as the body
        self._underlay_set = False
        self._underlay_rect = QRect()
        self._grabbing = False
        self._dark = is_dark_theme(app)
        self._open = True
        self._slide = 0.0   # 0 = the panel in place, 1 = out of sight below
        self._on_toggle = on_toggle
        self._hover_inside = False
        self._outside_polls = 0
        self._native_owner = None
        self._native_area = None
        self._native_view_ref = None
        self._native_key = None
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(PANEL_SLIDE_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_slide_step)
        self._anim.finished.connect(self._on_slide_finished)
        self._fade = QVariantAnimation(self)
        self._fade.setDuration(PANEL_FADE_MS)
        self._fade.valueChanged.connect(self._set_handle_alpha)
        self._fade.finished.connect(self._on_fade_finished)
        self._shadows = _FloatShadows(self)
        self._handle = GlassIconButton('chevron.down', self)
        self._handle.clicked.connect(self._handle_clicked)
        self._handle.installEventFilter(self)
        self._handle.hide()
        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.setInterval(PANEL_HOVER_DELAY_MS)
        self._show_timer.timeout.connect(self._show_handle)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(PANEL_HIDE_DELAY_MS)
        self._hide_timer.timeout.connect(self._maybe_hide_handle)
        self._hover_poll = QTimer(self)
        self._hover_poll.setInterval(PANEL_HOVER_POLL_MS)
        self._hover_poll.timeout.connect(self._poll_hover)
        self._frost_timer = QTimer(self)
        self._frost_timer.setSingleShot(True)
        self._frost_timer.setInterval(PANEL_FROST_DELAY_MS)
        self._frost_timer.timeout.connect(self._refresh_underlay)
        _UI_SURFACES.add(self)
        self._adopt(content, panel)

    # ── what it holds ──
    def _adopt(self, content, panel):
        for widget in (content, panel):
            widget.setParent(self)
            widget.show()
        self._content, self._cards = content, panel
        panel.installEventFilter(self)
        content.lower()
        self._shadows.stackUnder(panel)
        panel.raise_()
        self._handle.raise_()
        panel.set_float_host(self)
        panel.set_frosted_source(lambda c=panel: self._frost_for(c))
        # in-window glass of the content under the panel gives way to Qt's paint (as under Broccoli's
        # sliding panels): that glass sits ON the Qt content and would show through the panel
        panel._glass_occluding_rect = lambda c=panel: self._card_cover_rect(c)
        glass_kit.register_glass_occluder(panel)
        self.watch_content()
        self._relayout()
        self.updateGeometry()
        self.schedule_frost()

    def watch_content(self):
        """Retake the picture whenever something of the content repaints where the panel lies (scrolling,
        a changed cell, a hidden row, a selection …). Call again after the content got new children."""
        content = self._content
        if content is None:
            return
        for widget in [content] + content.findChildren(QWidget):
            targets = [widget]
            if isinstance(widget, QAbstractScrollArea):
                targets.append(widget.viewport())
            for target in targets:
                if target is not None and not any(target is known for known in self._painters):
                    target.installEventFilter(self)
                    self._painters.append(target)

    def is_open(self) -> bool:
        return self._open

    def content_widget(self):
        return self._content

    def panel_widget(self):
        return self._cards

    def cards_float(self) -> bool:
        return self._cards is not None and self._content is not None

    def underlay_ready(self) -> bool:
        return self._underlay_set and self._underlay_view is not None

    # ── system Liquid Glass under the panel, over a picture of the table ──
    def _ensure_card_glass(self):
        card = self._cards
        if card is None or not self.isVisible() or not liquid_glass_available():
            return
        made = False
        try:
            if card._stage_glass is None and card.isVisible() and card.window() is not card:
                card._stage_glass = FloatCardGlass(card, self, self._dark)
                made = True
        except Exception:
            logging.exception('Glass for the floating panel failed.')
        if made:
            try:
                window = glass_kit._broccoli_own_ns_window(self.window())
                if window is not None:
                    glass_kit._want_active_glass(window, self.window())   # stays bright in the background
            except Exception:
                pass

    def _sync_card_glass(self):
        card = self._cards
        if card is not None:
            try:
                if card._stage_glass is not None:
                    card._stage_glass.sync()
                card.update()
            except RuntimeError:
                pass
        self._shadows.update()

    def _uses_glass(self) -> bool:
        return self._cards is not None and self._cards._stage_glass is not None

    def _set_underlay_hidden(self, hidden):
        for view in (self._underlay_view, self._base_view):
            if view is not None:
                view.setHidden_(bool(hidden))
        if hidden:
            self._underlay_set = False

    def _body_widget(self):
        widget = self.parentWidget()
        while widget is not None and not (isinstance(widget, SectionCard) and widget._kind == 'body'):
            widget = widget.parentWidget()
        return widget

    def _sync_base_view(self, container):
        """The body's own colour, as large as the body, at the very bottom of the glass layer: glass also
        bends in what lies well beyond its edge, and without this its rim took a tinge of the desktop."""
        appkit = glass_kit.AppKit
        body = self._body_widget()
        if body is None:
            return
        base = self._base_view
        if base is None:
            base = appkit.NSView.alloc().initWithFrame_(appkit.NSMakeRect(0, 0, 1, 1))
            base.setWantsLayer_(True)
            base.layer().setCornerRadius_(float(FLOAT_CARD_GLASS_RADIUS))
            try:
                base.layer().setCornerCurve_('continuous')
            except Exception:
                pass
            self._base_view = base
        if base.superview() is not container:
            if base.superview() is not None:
                base.removeFromSuperview()
            container.addSubview_positioned_relativeTo_(base, int(getattr(appkit, 'NSWindowBelow', -1)), None)
        color = ui_palette(self._dark)['body']
        base.layer().setBackgroundColor_(appkit.NSColor.colorWithSRGBRed_green_blue_alpha_(
            color.redF(), color.greenF(), color.blueF(), 1.0).CGColor())
        origin = body.mapTo(self.window(), QPoint(0, 0))
        inset = 2.0
        base.setFrame_(appkit.NSMakeRect(origin.x() + inset, origin.y() + inset,
                                         max(1.0, body.width() - 2 * inset), max(1.0, body.height() - 2 * inset)))
        base.setHidden_(False)

    def _show_underlay_view(self, pixmap, area):
        """The picture of the table as a view at the bottom of the window's glass layer, where the table
        is: the panel's glass above it shows (bends, softens) this, not the desktop."""
        try:
            layer = glass_kit._window_glass_layer(self.window())
            if layer is None or not layer.ensure():
                return
            appkit = glass_kit.AppKit
            container = layer.view
            view = self._underlay_view
            if view is None:
                view = appkit.NSImageView.alloc().initWithFrame_(appkit.NSMakeRect(0, 0, 1, 1))
                view.setImageScaling_(int(getattr(appkit, 'NSImageScaleAxesIndependently', 1)))
                view.setImageFrameStyle_(0)
                self._underlay_view = view
            self._sync_base_view(container)
            if view.superview() is not container:
                if view.superview() is not None:
                    view.removeFromSuperview()
                if self._base_view is not None:
                    container.addSubview_positioned_relativeTo_(view, int(getattr(appkit, 'NSWindowAbove', 1)), self._base_view)
                else:
                    container.addSubview_positioned_relativeTo_(view, int(getattr(appkit, 'NSWindowBelow', -1)), None)
            data = QByteArray()
            buffer = QBuffer(data)
            buffer.open(QBuffer.OpenModeFlag.WriteOnly)
            pixmap.toImage().save(buffer, 'BMP')
            buffer.close()
            raw = bytes(data)
            image = appkit.NSImage.alloc().initWithData_(appkit.NSData.dataWithBytes_length_(raw, len(raw)))
            if image is None:
                return
            image.setSize_(appkit.NSMakeSize(area.width(), area.height()))
            view.setImage_(image)
            origin = self.mapTo(self.window(), area.topLeft())
            view.setFrame_(appkit.NSMakeRect(origin.x(), origin.y(), area.width(), area.height()))
            view.setHidden_(False)
            self._underlay_set = True
        except Exception:
            logging.exception('The picture under the floating panel failed.')

    # ── geometry ──
    def _panel_height(self) -> int:
        want = self._cards.sizeHint().height()
        room = self.height() - 2 * PANEL_FLOAT_INSET
        least = min(room, self._cards.minimumSizeHint().height())
        return max(1, least, min(want, room - PANEL_MIN_TABLE_SHOWN))

    def _open_cards_rect(self) -> QRect:
        height = self._panel_height()
        return QRect(PANEL_FLOAT_INSET, self.height() - PANEL_FLOAT_INSET - height,
                     max(1, self.width() - 2 * PANEL_FLOAT_INSET), height)

    def _content_rect(self) -> QRect:
        return QRect(PAGE_CONTENT_INSET, PAGE_CONTENT_TOP, max(1, self.width() - 2 * PAGE_CONTENT_INSET),
                     max(1, self.height() - PAGE_CONTENT_TOP - PAGE_CONTENT_INSET))

    def _relayout(self):
        if self._cards is None:
            return
        width, height = self.width(), self.height()
        self._shadows.setGeometry(0, 0, width, height)
        self._content.setGeometry(self._content_rect())   # the table never moves or shrinks
        rect = self._open_cards_rect()
        shift = int(round(self._slide * (height - rect.top() + FLOAT_SHADOW_MARGIN)))
        self._cards.setGeometry(rect.translated(0, shift))
        self._cards.setVisible(self._slide < 1.0)
        self._place_handle()
        self._handle.raise_()
        self._sync_card_glass()
        self._resync_glass()
        self._sync_native_hover()

    def _place_handle(self):
        size = GLASS_ICON_BUTTON_SIZE
        if self._open and self._cards.isVisibleTo(self):
            geometry = self._cards.geometry()
            x = geometry.center().x() - size // 2
            y = geometry.top() - PANEL_HANDLE_GAP - size
        else:
            x = self.width() // 2 - size // 2
            y = self.height() - PANEL_HANDLE_GAP - size
        self._handle.setGeometry(x, max(0, y), size, size)

    def _resync_glass(self):
        """The in-window glass under / in the moved panel (Qt sends it no move event of its own)."""
        try:
            glass_kit.resync_inwindow_glass(self.window())
        except Exception:
            pass

    def _card_cover_rect(self, card) -> QRect:
        """What the panel covers, in its window's coordinates."""
        try:
            if self._cards is None or card is not self._cards or not card.isVisible():
                return QRect()
            top = card.window()
            cover = QRect(card.mapTo(top, QPoint(0, 0)), card.size())
            return cover.intersected(QRect(self.mapTo(top, QPoint(0, 0)), self.size()))
        except RuntimeError:
            return QRect()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()
        self.schedule_frost()

    def minimumSizeHint(self):
        if self._cards is None:
            return QSize(0, 0)
        cards = self._cards.minimumSizeHint()
        return QSize(cards.width() + 2 * PANEL_FLOAT_INSET, cards.height() + 2 * PANEL_FLOAT_INSET)

    def sizeHint(self):
        if self._cards is None:
            return QSize(0, 0)
        cards = self._cards.sizeHint()
        return QSize(cards.width() + 2 * PANEL_FLOAT_INSET,
                     cards.height() + 2 * PANEL_FLOAT_INSET + PANEL_MIN_TABLE_SHOWN)

    def eventFilter(self, obj, event):
        kind = event.type()
        if obj is self._handle:
            if kind in (QEvent.Type.Enter, QEvent.Type.Leave):
                self.hover_changed()
        elif obj is self._cards:
            if kind == QEvent.Type.LayoutRequest:
                self.updateGeometry()
                self._relayout()
        elif kind == QEvent.Type.Paint and not self._grabbing and self._cards is not None:
            try:
                origin = obj.mapTo(self, QPoint(0, 0))
                if event.rect().translated(origin).intersects(self._underlay_area()):
                    self.schedule_frost()
            except (RuntimeError, AttributeError):
                pass
        return False

    # ── the table under the panel ──
    def schedule_frost(self, *args):
        if not self._grabbing and self._cards is not None and not self._frost_timer.isActive():
            self._frost_timer.start()

    def _underlay_area(self) -> QRect:
        """Everywhere the panel can lie, in place or sliding out (it only moves down), and a margin."""
        rect = self._open_cards_rect()
        top = max(0, rect.top() - PANEL_UNDERLAY_MARGIN)
        return QRect(0, top, self.width(), self.height() - top).intersected(self.rect())

    def _refresh_underlay(self):
        if self._cards is None or not self.isVisible():
            self._underlay = None
            self._set_underlay_hidden(True)
            return
        self._ensure_card_glass()
        area = self._underlay_area()
        if area.isEmpty():
            return
        self._grabbing = True
        try:
            inside = area.intersected(self._content.geometry())   # the table lies inset in the page
            shot = self._content.grab(inside.translated(-self._content.pos())) if not inside.isEmpty() else None
        except RuntimeError:
            return
        finally:
            self._grabbing = False
        ratio = shot.devicePixelRatio() if shot is not None else self.devicePixelRatioF()
        base = QPixmap(int(round(area.width() * ratio)), int(round(area.height() * ratio)))
        base.setDevicePixelRatio(ratio)
        base.fill(ui_palette(self._dark)['body'])   # the body's colour around the table
        if shot is not None:
            painter = QPainter(base)
            painter.drawPixmap(inside.topLeft() - area.topLeft(), shot)
            painter.end()
        self._underlay_rect = QRect(area)
        if self._uses_glass():
            self._underlay = None
            was_ready = self.underlay_ready()
            self._show_underlay_view(base, area)
            if not was_ready:
                self._sync_card_glass()
            return
        self._underlay = glass_kit.broccoli_blurred_backdrop(base)
        try:
            self._cards.update()
        except RuntimeError:
            pass

    def _frost_for(self, card):
        if self._underlay is None or self._cards is None:
            return None
        try:
            offset = card.mapTo(self, QPoint(0, 0))
        except RuntimeError:
            return None
        return self._underlay, QRectF(self._underlay_rect.translated(-offset.x(), -offset.y()))

    def apply_theme(self, dark=None):
        self._dark = ui_palette(dark)['dark']
        self._shadows.update()
        QTimer.singleShot(0, self._refresh_underlay)   # after the table has taken its new colours

    # ── open / close ──
    def set_open(self, open_, animate=True):
        open_ = bool(open_)
        if open_ == self._open and self._anim.state() != self._anim.State.Running:
            self._relayout()
            return
        self._open = open_
        self._hide_handle_now()
        target = 0.0 if open_ else 1.0
        if not animate or not self.isVisible():
            self._anim.stop()
            self._slide = target
            self._relayout()
            return
        clip_inwindow_glass_to_visible(self._cards)
        self._anim.stop()
        self._anim.setStartValue(float(self._slide))
        self._anim.setEndValue(target)
        self._anim.start()
        self._relayout()

    def _on_slide_step(self, value):
        self._slide = float(value)
        self._relayout()

    def _on_slide_finished(self):
        self._relayout()
        self._hover_inside = self._pointer_in_hover_area()
        if self._hover_inside:
            self._show_timer.start()

    def _handle_clicked(self):
        self._hide_handle_now()
        if self._on_toggle is not None:
            self._on_toggle(not self._open)
        else:
            self.set_open(not self._open)

    # ── the handle that shows only near the panel's top edge ──
    def _cursor_pos(self) -> QPoint:
        return self.mapFromGlobal(QCursor.pos())

    def hover_band(self) -> QRect:
        """Where the mouse brings the handle up: along the panel's top edge (pushed in: the page's bottom)."""
        if self._cards is None or self._anim.state() == self._anim.State.Running:
            return QRect()
        if self._open and self._cards.isVisibleTo(self):
            cards = self._cards.geometry()
            return QRect(cards.left(), cards.top() - PANEL_BAND_OUTSIDE,
                         cards.width(), PANEL_BAND_OUTSIDE + PANEL_BAND_INSIDE).intersected(self.rect())
        return QRect(0, self.height() - PANEL_BAND_OUTSIDE, self.width(), PANEL_BAND_OUTSIDE)

    def _pointer_in_hover_area(self) -> bool:
        band = self.hover_band()
        if band.isEmpty():
            return False
        pos = self._cursor_pos()
        return band.contains(pos) or (self._handle.isVisible() and self._handle.geometry().contains(pos))

    def enterEvent(self, event):
        super().enterEvent(event)
        self._outside_polls = 0
        self._hover_poll.start()
        self._poll_hover()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hover_poll.stop()
        self._hover_inside = False
        self._show_timer.stop()
        if self._handle.isVisible():
            self._hide_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._hover_poll.stop()
        self._hover_inside = False
        self._hide_handle_now()
        self._drop_native_hover()
        self._set_underlay_hidden(True)

    def moveEvent(self, event):
        super().moveEvent(event)
        self.schedule_frost()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._refresh_underlay)
        QTimer.singleShot(0, self._sync_native_hover)

    def _native_view(self):
        try:
            top = self.window()
            if (top is None or not top.isVisible() or glass_kit.objc is None
                    or QApplication.platformName() != 'cocoa'):   # elsewhere winId() is no NSView
                return None
            return glass_kit.objc.objc_object(c_void_p=int(top.winId()))   # the top-level's own view only
        except Exception:
            return None

    def _sync_native_hover(self):
        band = self.hover_band() if self.isVisible() else QRect()
        view = self._native_view() if not band.isEmpty() else None
        if view is None:
            self._drop_native_hover()
            return
        origin = self.mapTo(self.window(), band.topLeft())   # Qt's view is flipped: window coordinates as they are
        key = (id(view), origin.x(), origin.y(), band.width(), band.height())
        if key == self._native_key and self._native_area is not None:
            return
        self._drop_native_hover()
        try:
            appkit = glass_kit.AppKit
            if self._native_owner is None:
                self._native_owner = _panel_hover_owner(self)
            if self._native_owner is None:
                return
            options = (int(getattr(appkit, 'NSTrackingMouseEnteredAndExited', 0x01))
                       | int(getattr(appkit, 'NSTrackingActiveAlways', 0x80)))
            area = appkit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                appkit.NSMakeRect(origin.x(), origin.y(), band.width(), band.height()), options, self._native_owner, None)
            view.addTrackingArea_(area)
            self._native_area, self._native_view_ref, self._native_key = area, view, key
        except Exception:
            logging.exception('The panel hover area failed.')
            self._native_area = None

    def _drop_native_hover(self):
        area = getattr(self, '_native_area', None)
        if area is not None:
            try:
                self._native_view_ref.removeTrackingArea_(area)
            except Exception:
                pass
        self._native_area = None
        self._native_view_ref = None
        self._native_key = None

    def native_hover_changed(self, entered):
        """macOS: the mouse came into / left the band (also while another app is in front)."""
        self._hover_inside = bool(entered) and self._pointer_in_hover_area()
        self.hover_changed()

    def _poll_hover(self):
        if not self.isVisible():
            self._hover_poll.stop()
            return
        if self.rect().contains(self._cursor_pos()):
            self._outside_polls = 0
        else:
            self._outside_polls += 1
            if self._outside_polls > 30:   # a Leave that never came: stop after ~2 s
                self._hover_poll.stop()
        inside = self._pointer_in_hover_area()
        if inside != self._hover_inside:
            self._hover_inside = inside
            self.hover_changed()

    def hover_changed(self):
        if self._pointer_in_hover_area():
            self._hide_timer.stop()
            if not self._handle.isVisible() or self._fade.endValue() == 0.0:
                self._show_timer.start()
        else:
            self._show_timer.stop()
            if self._handle.isVisible():
                self._hide_timer.start()

    def _show_handle(self):
        if (self._anim.state() == self._anim.State.Running
                or QApplication.mouseButtons() != Qt.MouseButton.NoButton or not self._pointer_in_hover_area()):
            return
        self._handle.set_symbol('chevron.down' if self._open else 'chevron.up')
        self._handle.setToolTip(_tr('Hide the edit panel') if self._open else _tr('Show the edit panel'))
        self._place_handle()
        start = 0.0 if not self._handle.isVisible() else self._handle_alpha()
        self._handle.show()
        self._handle.raise_()
        self._fade.stop()
        self._fade.setStartValue(start)
        self._fade.setEndValue(1.0)
        self._fade.start()

    def _maybe_hide_handle(self):
        if self._pointer_in_hover_area() or not self._handle.isVisible():
            return
        self._fade.stop()
        self._fade.setStartValue(self._handle_alpha())
        self._fade.setEndValue(0.0)
        self._fade.start()

    def _hide_handle_now(self):
        self._show_timer.stop()
        self._hide_timer.stop()
        self._fade.stop()
        self._handle.hide()

    def _handle_glass(self):
        helper = getattr(self._handle, '_broccoli_inwindow_glass', None)
        return getattr(helper, 'glass', None)

    def _handle_alpha(self) -> float:
        glass = self._handle_glass()
        try:
            return float(glass.alphaValue()) if glass is not None else 1.0
        except Exception:
            return 1.0

    def _set_handle_alpha(self, value):
        glass = self._handle_glass()
        if glass is not None:
            try:
                glass.setAlphaValue_(max(0.0, min(1.0, float(value))))
            except Exception:
                pass

    def _on_fade_finished(self):
        if self._fade.endValue() == 0.0:
            self._handle.hide()
            self._set_handle_alpha(1.0)


def edit_panel(*items, spacing=8, parent=None):
    """A page's floating edit panel holding `items` (widgets or layouts) top to bottom."""
    card = SectionCard(parent)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(SECTION_CARD_MARGIN, SECTION_CARD_MARGIN, SECTION_CARD_MARGIN, SECTION_CARD_MARGIN)
    lay.setSpacing(spacing)
    for item in items:
        if isinstance(item, QWidget):
            lay.addWidget(item)
        elif item is not None:
            lay.addLayout(item)
    return card


# ── tables ─────────────────────────────────────────────────────────────────────────────────────────────
def page_table_stylesheet(dark: bool) -> str:
    """A page's table: content straight on the body — no frame, no panel of its own (style book 5.12);
    rows, header and selection as the settings table (the kit's _settings_table_stylesheet). The
    background is the body's own colour (a solid one: the system scroll bar then picks the right knob, 5.9)."""
    if dark:
        body, line, text, sel, sel_text = '#2D2D2D', '#3A3A3A', '#F2F2F7', '#2E5C91', '#FFFFFF'
        head_bg, head_text, edit_bg, edit_text = '#3A3A3A', '#A7AEB8', '#1C1C1E', '#F2F2F7'
    else:
        body, line, text, sel, sel_text = '#FFFFFF', '#ECECEC', '#20242B', '#E8EEF8', '#1A4B7A'
        head_bg, head_text, edit_bg, edit_text = '#F7F7F8', '#7A8391', '#FFFFFF', '#20242B'
    return '''
        QTableWidget {
            border: none;
            background: %(body)s;
            gridline-color: %(line)s;
            outline: none;
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 13px;
            color: %(text)s;
            selection-background-color: %(sel)s;
            selection-color: %(sel_text)s;
        }
        QTableWidget::item { padding: 4px 8px; border-bottom: 1px solid %(line)s; }
        QTableWidget::item:selected { background: %(sel)s; color: %(sel_text)s; }
        QHeaderView { background: transparent; border: none; }
        QHeaderView::section {
            background: %(head_bg)s;
            color: %(head_text)s;
            border: none;
            border-bottom: 1px solid %(line)s;
            padding: 6px 8px;
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 12px;
        }
        QHeaderView::section:horizontal:first { border-top-left-radius: 8px; border-bottom-left-radius: 8px; }
        QHeaderView::section:horizontal:last { border-top-right-radius: 8px; border-bottom-right-radius: 8px; }
        QTableCornerButton::section { background: %(head_bg)s; border: none; }
        QTableWidget QLineEdit {
            background: %(edit_bg)s;
            color: %(edit_text)s;
            border: 1px solid #2E5C91;
            border-radius: 6px;
            padding: 2px 6px;
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 13px;
        }
    ''' % locals()


_STYLED_TABLES = weakref.WeakKeyDictionary()   # table → 'page' | 'card'


def style_table(table, kind='page'):
    """kind='page': a page's own table (on the body); kind='card': a small table inside the edit panel
    (the settings table: a rounded card). Restyled on light / dark."""
    _STYLED_TABLES[table] = kind
    table.setShowGrid(False)
    table.setFrameShape(table.Shape.NoFrame)
    table.verticalHeader().setDefaultSectionSize(28)
    table.horizontalHeader().setHighlightSections(False)
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    if kind == 'card':   # a small table in the panel: its columns share its width
        from PyQt6.QtWidgets import QHeaderView
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    _apply_table_style(table, kind, is_dark_theme(app))


def _apply_table_style(table, kind, dark):
    table.setStyleSheet(page_table_stylesheet(dark) if kind == 'page' else _settings_table_stylesheet(dark))


# ── date / time boxes (style book 5.4.1, Ryan 2026-11-15: "普通输入框 + 玻璃弹窗") ─────────────────────
_FIELD_GLYPHS = weakref.WeakKeyDictionary()   # date / time box → (glyph label, symbol name)


class _FieldGlyphPlacer(QObject):
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            entry = _FIELD_GLYPHS.get(obj)
            if entry is not None:
                label = entry[0]
                label.move(obj.width() - label.width() - 5, (obj.height() - label.height()) // 2)
        return False


_FIELD_GLYPH_PLACER = _FieldGlyphPlacer(app)


def _field_glyph_pixmap(symbol, dark):
    return edge_hint_symbol_pixmap(symbol, QColor('#8E8E93'), 12)


def style_date_time_field(edit, symbol):
    """A date / time box looks like the normal single-line input (5.4): the stylesheet gives the frame; the
    stepper arrows are not drawn; a small grey system icon on the right says what it is ('calendar' / 'clock').
    For a date box the icon lies on the part that opens the calendar; clicks go through it."""
    edit.setButtonSymbols(edit.ButtonSymbols.NoButtons)
    edit.setFixedHeight(GREY_ROW_HEIGHT)
    label = QLabel(edit)
    label.setFixedSize(12, 12)
    label.setScaledContents(True)
    label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    label.setStyleSheet('background: transparent; border: none;')
    pixmap = _field_glyph_pixmap(symbol, is_dark_theme(app))
    if pixmap is not None:
        label.setPixmap(pixmap)
    _FIELD_GLYPHS[edit] = (label, symbol)
    edit.installEventFilter(_FIELD_GLYPH_PLACER)
    label.move(edit.width() - 17, (edit.height() - 12) // 2)
    label.show()


def calendar_stylesheet(dark: bool) -> str:
    """The calendar inside the date pop-up: see-through (the pop-up's glass, or its own solid card without
    glass, is the background), system accent for the chosen day."""
    pal = ui_palette(dark)
    accent = accent_color().name()
    text = pal['text']
    hover = 'rgba(255,255,255,0.14)' if dark else 'rgba(0,0,0,0.07)'
    return '''
        QCalendarWidget QWidget { background: transparent; color: %(text)s; alternate-background-color: transparent; }
        QCalendarWidget QToolButton {
            background: transparent; color: %(text)s; border: none; border-radius: 6px;
            padding: 3px 6px; font-size: 13px; font-weight: 600;
        }
        QCalendarWidget QToolButton:hover { background: %(hover)s; }
        QCalendarWidget QToolButton::menu-indicator { image: none; width: 0px; }
        QCalendarWidget QSpinBox {
            background: transparent; color: %(text)s; border: none; font-size: 13px;
            selection-background-color: %(accent)s; selection-color: #FFFFFF;
        }
        QCalendarWidget QAbstractItemView {
            background: transparent; color: %(text)s; outline: none; font-size: 13px;
            selection-background-color: %(accent)s; selection-color: #FFFFFF;
        }
    ''' % locals()


class CalendarGlassPopup(QWidget):
    """The calendar a date box opens: a small Liquid Glass pop-up (style book 5.4.1 — window glass, corner
    9, the system window shadow) holding Qt's own calendar; without glass the same shape, solid. One
    pop-up serves every date box. (Qt's built-in calendar pop-up is a private window that cannot be made
    see-through, so the date boxes do not use it.)"""

    def __init__(self):
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        from PyQt6.QtWidgets import QCalendarWidget
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self._edit = None
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.calendar.clicked.connect(self._chosen)
        self.calendar.activated.connect(self._chosen)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.addWidget(self.calendar)
        self.setFixedSize(280, 240)
        self._restyle()

    def _restyle(self):
        from PyQt6.QtGui import QTextCharFormat
        dark = is_dark_theme(app)
        pal = ui_palette(dark)
        clear = QColor(0, 0, 0, 0)
        palette = QPalette(self.calendar.palette())
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            for role in (QPalette.ColorRole.Base, QPalette.ColorRole.Window, QPalette.ColorRole.AlternateBase):
                palette.setColor(group, role, clear)
            for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
                palette.setColor(group, role, QColor(pal['text']))
            palette.setColor(group, QPalette.ColorRole.Highlight, accent_color())
            palette.setColor(group, QPalette.ColorRole.HighlightedText, QColor('#FFFFFF'))
        for role in (QPalette.ColorRole.Base, QPalette.ColorRole.Window, QPalette.ColorRole.AlternateBase):
            palette.setColor(QPalette.ColorGroup.Disabled, role, clear)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor('#8E8E93'))
        self.calendar.setPalette(palette)
        day = QTextCharFormat()
        day.setForeground(QColor(pal['text']))
        for weekday in Qt.DayOfWeek:
            self.calendar.setWeekdayTextFormat(weekday, day)   # no red weekends: one text colour (5.8)
        head = QTextCharFormat()
        head.setForeground(QColor('#8E8E93'))
        head.setBackground(clear)
        self.calendar.setHeaderTextFormat(head)
        self.calendar.setStyleSheet(calendar_stylesheet(dark))
        from PyQt6.QtWidgets import QToolButton
        for name, symbol in (('qt_calendar_prevmonth', 'chevron.left'), ('qt_calendar_nextmonth', 'chevron.right')):
            button = self.calendar.findChild(QToolButton, name)
            pixmap = edge_hint_symbol_pixmap(symbol, pal['icon'], 14)
            if button is not None and pixmap is not None:
                button.setIcon(QIcon(pixmap))   # system line icons in the text colour (Qt's arrows are black)
        self._clear_view_base()

    def _clear_view_base(self):
        """The day grid fills its cells with its palette's Base, and a style sheet's "transparent" turns
        that into opaque black: give the grid a really see-through Base (after every re-styling)."""
        from PyQt6.QtWidgets import QTableView
        view = self.calendar.findChild(QTableView)
        if view is None:
            return
        text = QColor(ui_palette()['text'])
        palette = QPalette(view.palette())
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled):
            palette.setColor(group, QPalette.ColorRole.Base, QColor(255, 255, 255, 0))
            palette.setColor(group, QPalette.ColorRole.AlternateBase, QColor(255, 255, 255, 0))
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            palette.setColor(group, QPalette.ColorRole.Text, text)
            palette.setColor(group, QPalette.ColorRole.Highlight, accent_color())
            palette.setColor(group, QPalette.ColorRole.HighlightedText, QColor('#FFFFFF'))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor('#8E8E93'))
        view.setPalette(palette)

    def showEvent(self, event):
        super().showEvent(event)
        self._clear_view_base()
        QTimer.singleShot(0, self._clear_view_base)

    def open_for(self, edit):
        self._edit = edit
        self._restyle()
        self.calendar.setSelectedDate(edit.date())
        below = edit.mapToGlobal(QPoint(0, edit.height() + 4))
        screen = edit.screen().availableGeometry() if edit.screen() is not None else None
        x, y = below.x(), below.y()
        if screen is not None:
            if y + self.height() > screen.bottom() - 8:   # no room below: above the box
                y = edit.mapToGlobal(QPoint(0, 0)).y() - 4 - self.height()
            x = max(screen.left() + 8, min(x, screen.right() - self.width() - 8))
        self.move(x, y)
        self.show()

    def _chosen(self, date):
        edit = self._edit
        if edit is not None:
            try:
                edit.setDate(date)
            except RuntimeError:
                pass
        self.hide()

    def paintEvent(self, event):
        if getattr(self, '_liquid_glass_active', False):
            return   # the window's Liquid Glass is the card
        pal = ui_palette()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor('#4A4B4F') if pal['dark'] else QColor('#ECECEC'), 1))
        painter.setBrush(pal['panel'])
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), POPUP_GLASS_RADIUS, POPUP_GLASS_RADIUS)
        painter.end()


install_window_liquid_glass(CalendarGlassPopup, POPUP_GLASS_RADIUS, 0, keep_shadow=True, menu_look=True)
_CALENDAR_POPUP = []
DATE_FIELD_BUTTON_WIDTH = 24   # the right end of a date box (where the calendar icon is) opens the calendar


def calendar_popup() -> CalendarGlassPopup:
    if not _CALENDAR_POPUP:
        _CALENDAR_POPUP.append(CalendarGlassPopup())
    return _CALENDAR_POPUP[0]


class _DateFieldOpener(QObject):
    def eventFilter(self, obj, event):
        kind = event.type()
        if kind == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            if obj.isEnabled() and event.position().x() >= obj.width() - DATE_FIELD_BUTTON_WIDTH:
                calendar_popup().open_for(obj)
                return True
        elif kind == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_F4:
            calendar_popup().open_for(obj)
            return True
        return False


_DATE_FIELD_OPENER = _DateFieldOpener(app)


def glass_calendar_popup(date_edit):
    """A click on the right end of the date box (its calendar icon) opens the glass calendar pop-up."""
    date_edit.setCalendarPopup(False)
    date_edit.installEventFilter(_DATE_FIELD_OPENER)


# ── the application-wide look ──────────────────────────────────────────────────────────────────────────
def tomato_stylesheet(dark: bool) -> str:
    """The application-wide look (style book 5.4 / 5.8). No rule here may select a QScrollBar or set a
    background on QWidget (5.9: that turns the system scroll bars into the old style)."""
    if dark:
        text, border_in, bg_in, sel = '#F2F2F7', '#4A4B4F', '#3A3A3A', '#2E5C91'
        big_border = '#4A4B4F'
        paper, paper_text, paper_border = '#2A2928', '#ECEAE4', '#4A4B4F'
        disabled_bg, disabled_text, disabled_border = '#313133', '#8E8E93', '#3E3E42'
        line = '#4A4B4F'
    else:
        text, border_in, bg_in, sel = '#20242B', '#D9D9DE', '#FFFFFF', '#DCEAFB'
        big_border = '#ECECEC'
        paper, paper_text, paper_border = '#F3F2EE', '#000000', '#ECECEC'
        disabled_bg, disabled_text, disabled_border = '#F7F7F8', '#A0A3AA', '#E6E6EA'
        line = '#D9D9DE'
    sel_text = '#FFFFFF' if dark else '#20242B'
    return '''
    QLabel { color: %(text)s; }
    QCheckBox { color: %(text)s; font-size: 13px; }
    QLineEdit, QDateEdit, QTimeEdit {
        border: 1px solid %(border_in)s;
        border-radius: 6px;
        background: %(bg_in)s;
        color: %(text)s;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 13px;
        padding: 0px 4px;
        selection-background-color: %(sel)s;
        selection-color: %(sel_text)s;
    }
    QDateEdit, QTimeEdit { padding-right: 20px; }
    QDateEdit::up-button, QDateEdit::down-button, QTimeEdit::up-button, QTimeEdit::down-button {
        subcontrol-origin: border; width: 0px; height: 0px; border: none;
    }
    QLineEdit:disabled, QDateEdit:disabled, QTimeEdit:disabled {
        background: %(disabled_bg)s; color: %(disabled_text)s; border: 1px solid %(disabled_border)s;
    }
    QPlainTextEdit, QTextEdit, QTextBrowser {
        border: 1px solid %(paper_border)s;
        border-radius: 14px;
        padding: 6px 8px;
        background-color: %(paper)s;
        color: %(paper_text)s;
        font: 14pt "Times New Roman";
        selection-background-color: %(sel)s;
        selection-color: %(sel_text)s;
    }
    QPlainTextEdit#edit, QTextEdit#edit {
        border: 1px solid %(big_border)s;
        border-radius: 14px;
        padding: 10px 12px;
        background-color: %(bg_in)s;
        color: %(text)s;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 13px;
    }
    QListWidget {
        border: 1px solid %(big_border)s;
        border-radius: 14px;
        padding: 6px;
        background-color: %(bg_in)s;
        color: %(text)s;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 13px;
        outline: none;
    }
    QFrame#PanelLine { border: none; background: %(line)s; max-height: 1px; min-height: 1px; }
    QSplitter::handle { background: transparent; image: none; }
    ''' % locals()


def panel_line(parent=None):
    """A hairline between groups of buttons inside the panel."""
    from PyQt6.QtWidgets import QFrame
    line = QFrame(parent)
    line.setObjectName('PanelLine')
    line.setFixedHeight(1)
    return line


def apply_tomato_theme(dark=None):
    """Light / dark, live (style book 5.8): the application stylesheet, every panel / tab bar / icon
    button / table / date box, the kit's buttons and drop-downs, and the glass's appearance."""
    if dark is None:
        dark = is_dark_theme(app)
    app.setStyleSheet(tomato_stylesheet(dark))
    for surface in list(_UI_SURFACES):
        try:
            surface.apply_theme(dark)
        except RuntimeError:
            pass
    for table, kind in list(_STYLED_TABLES.items()):
        try:
            _apply_table_style(table, kind, dark)
        except RuntimeError:
            pass
    for edit, (label, symbol) in list(_FIELD_GLYPHS.items()):
        try:
            pixmap = _field_glyph_pixmap(symbol, dark)
            if pixmap is not None:
                label.setPixmap(pixmap)
        except RuntimeError:
            pass
    for widget in app.allWidgets():
        try:
            if isinstance(widget, MacNormalButton):
                widget.update_theme()
            elif isinstance(widget, WhiteButton):
                widget.apply_default_style()
            elif isinstance(widget, glass_kit.DropdownButton):
                widget._update_style()
        except RuntimeError:
            pass
    for callback in list(_THEME_HOOKS):
        try:
            callback(dark)
        except Exception:
            logging.exception('theme hook failed')
    for top in app.topLevelWidgets():
        try:
            glass_kit.resync_inwindow_glass(top)
            top.update()
        except Exception:
            pass


# ── standalone windows and dialogs ─────────────────────────────────────────────────────────────────────
def make_native_glass_window(widget, kind=Qt.WindowType.Window, resizable=False, stays_on_top=True):
    """A standalone window per the style book: the system's own traffic lights (new design, 5.7.2) in the
    compact transparent title bar (content starts 40 down), and the window's Liquid Glass behind
    everything (4.1 ①: frosted, untinted, corner 16, system shadow). Without glass the window paints the
    same rounded card itself (see glass_window_paint)."""
    widget.setWindowFlags(glass_kit.native_titlebar_window_flags(kind, zoom=resizable, stays_on_top=stays_on_top))
    widget.setAttribute(Qt.WidgetAttribute.WA_ContentsMarginsRespectsSafeArea, False)
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
    widget.radius = MAIN_WINDOW_SMOOTH_RADIUS
    layout = QWidget.layout(widget)   # some windows keep a `layout` attribute that hides the method
    if layout is not None:
        left, top, right, bottom = layout.getContentsMargins()
        layout.setContentsMargins(max(left, 20), NATIVE_TITLEBAR_HEIGHT, max(right, 20), max(bottom, 16))


def glass_window_paint(widget, event):
    """Paint for a glass window: nothing while its glass is up, the rounded body colour (light / dark)
    when there is no glass."""
    if getattr(widget, '_liquid_glass_active', False):
        return
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = smooth_round_rect_path(QRectF(widget.rect()), getattr(widget, 'radius', MAIN_WINDOW_SMOOTH_RADIUS))
    painter.fillPath(path, ui_palette()['body'])
    painter.end()


_MAIN_WINDOW = []   # [getter] → the main window, for placing dialogs over it


def set_dialog_host(getter):
    _MAIN_WINDOW[:] = [getter]


def _dialog_host():
    try:
        main = _MAIN_WINDOW[0]() if _MAIN_WINDOW else None
        if main is not None and main.isVisible() and main.width() > 200:
            return main
    except Exception:
        pass
    return None


def place_glass_dialog(dialog):
    """Style book 3: an edit / confirm dialog is the approval width (main window − 32, 420…640) and
    opens over the main window while that is open, else in the middle of the screen."""
    host = _dialog_host()
    width = approval_window_width(host) if host is not None else 640
    if getattr(dialog, '_keep_width', False):
        width = dialog.width()
    dialog.resize(max(width, dialog.minimumSizeHint().width()), dialog.height())
    area = host.frameGeometry() if host is not None else dialog.screen().availableGeometry()
    frame = dialog.frameGeometry()
    frame.moveCenter(area.center())
    bounds = (host.screen() if host is not None else dialog.screen()).availableGeometry()
    left = max(bounds.left() + 16, min(frame.left(), bounds.right() - frame.width() - 16))
    top = max(bounds.top() + 16, min(frame.top(), bounds.bottom() - frame.height() - 16))
    dialog.move(left, top)


def install_glass_dialog_class(cls, radius=None):
    """A frameless dialog whose whole window is the card: window glass at corner 16 with the system shadow
    (4.1 ①, 2.3), the fallback paint, placed by place_glass_dialog on first show."""
    cls.paintEvent = lambda self, event: glass_window_paint(self, event)
    install_window_liquid_glass(
        cls, (lambda w: glass_corner_radius(MAIN_WINDOW_SMOOTH_RADIUS, smooth=True)) if radius is None else radius, 0,
        keep_shadow=True, menu_look=True)
    original = cls.showEvent

    def showEvent(self, event, _original=original):
        if not getattr(self, '_glass_dialog_placed', False) and not getattr(self, '_no_auto_place', False):
            self._glass_dialog_placed = True
            place_glass_dialog(self)
        _original(self, event)

    cls.showEvent = showEvent


def install_native_glass_window_class(cls, fixed=True):
    """Every window of `cls`: traffic lights set just before each show, window glass on first show
    (radius = glass 16), the fallback paint."""
    cls.paintEvent = lambda self, event: glass_window_paint(self, event)
    install_native_traffic_lights(cls, fixed_buttons=fixed)
    install_window_liquid_glass(cls, lambda w: glass_corner_radius(getattr(w, 'radius', MAIN_WINDOW_SMOOTH_RADIUS),
                                                                   smooth=True), 0,
                                keep_shadow=True, menu_look=True)


def make_glass_dialog(dialog, stays_on_top=True):
    """Window flags / attributes of a frameless glass dialog (see install_glass_dialog_class)."""
    flags = Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
    if stays_on_top:
        flags |= Qt.WindowType.WindowStaysOnTopHint
    dialog.setWindowFlags(flags)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    dialog.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
    dialog.radius = MAIN_WINDOW_SMOOTH_RADIUS


def tomato_alert(parent, title: str, text: str):
    """A notice / warning: the system alert over the window that asked (style book 5.7, 26 corners)."""
    show_broccoli_message(parent, title, text)


def tomato_confirm(parent, title: str, text: str) -> bool:
    """A yes / no question as the system alert; No is the default (Return) and Esc means No."""
    yes, no = _tr('Yes'), _tr('No')
    return ask_broccoli_message(parent, title, text, [yes, no], no) == yes


def tomato_choice(parent, title: str, text: str, buttons, default=None) -> str:
    """A question with the given buttons as the system alert; returns the chosen label."""
    return ask_broccoli_message(parent, title, text, list(buttons), default or buttons[-1])


class GlassFormDialog(QDialog):
    """An edit / confirm dialog (style book 5.7 approval frame): the window is the card — window glass,
    corner 16, system shadow; grey normal buttons (min 96 wide), Return = the default button, Esc = cancel.
    Put the content into `self.body` (a QVBoxLayout)."""

    def __init__(self, title, parent=None, ok_text=None, cancel_text=None):
        super().__init__(parent)
        make_glass_dialog(self)
        self.setWindowTitle(title)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 16)
        outer.setSpacing(12)
        heading = QLabel(title, self)
        font = QFont(heading.font())
        font.setPixelSize(15)
        font.setBold(True)
        heading.setFont(font)
        outer.addWidget(heading)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(8)
        outer.addLayout(self.body, 1)
        row = QHBoxLayout()
        row.setContentsMargins(0, 4, 0, 0)
        row.setSpacing(8)
        row.addStretch(1)
        self.cancel_button = MacNormalButton(cancel_text or _tr('Cancel'), self)
        self.cancel_button.setMinimumWidth(96)
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button = MacNormalButton(ok_text or _tr('OK'), self)
        self.ok_button.setMinimumWidth(96)
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)
        row.addWidget(self.cancel_button)
        row.addWidget(self.ok_button)
        outer.addLayout(row)
        self.resize(420, 10)


install_glass_dialog_class(GlassFormDialog)


def ask_text(parent, title: str, label: str, text: str = ''):
    """One line of text asked in a glass dialog (replaces QInputDialog.getText): → (text, accepted)."""
    dialog = GlassFormDialog(title, parent)
    prompt = QLabel(label, dialog)
    prompt.setWordWrap(True)
    edit = QLineEdit(dialog)
    edit.setFixedHeight(GREY_ROW_HEIGHT)
    edit.setText(text)
    edit.selectAll()
    edit.returnPressed.connect(dialog.accept)
    dialog.body.addWidget(prompt)
    dialog.body.addWidget(edit)
    dialog.adjustSize()
    edit.setFocus()
    accepted = dialog.exec() == QDialog.DialogCode.Accepted
    return edit.text(), accepted


# ── check boxes in a list: drawn by the program (style book 5.3.2) ────────────────────────────────────
def item_check_pixmap(state, dark: bool, accent: QColor, on_selected=False, ratio=2.0) -> QPixmap:
    """A 16 × 16 slot with a 13 × 13 box, corner 3.5: checked = accent with a white check (1.8, round caps),
    unchecked = white (dark #3A3A3C) with a 1-point grey edge #AEB5BF (dark #7A7D84)."""
    pixmap = QPixmap(int(16 * ratio), int(16 * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    box = QRectF(1.5, 1.5, 13, 13)
    if state == Qt.CheckState.Checked:
        painter.setPen(QPen(QColor('#FFFFFF'), 1.0) if on_selected else Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawRoundedRect(box, 3.5, 3.5)
        pen = QPen(QColor('#FFFFFF'), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(4.6, 8.3)
        path.lineTo(7.0, 10.6)
        path.lineTo(11.4, 5.4)
        painter.drawPath(path)
    else:
        painter.setPen(QPen(QColor('#7A7D84' if dark else '#AEB5BF'), 1.0))
        painter.setBrush(QColor('#3A3A3C' if dark else '#FFFFFF'))
        painter.drawRoundedRect(box, 3.5, 3.5)
    painter.end()
    return pixmap


class CheckRowDelegate(QStyledItemDelegate):
    """A list whose rows can be ticked and where selecting a row means nothing: the tick is drawn by the
    program at the row's start, the whole row toggles it, no selection highlight (style book 5.3.2 — the
    system's own tick in lists is broken under the new design)."""

    def paint(self, painter, option, index):
        dark = is_dark_theme(app)
        state = index.data(Qt.ItemDataRole.CheckStateRole)
        try:
            state = Qt.CheckState(state)
        except Exception:
            state = Qt.CheckState.Unchecked
        rect = option.rect
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if option.state & QStyle.StateFlag.State_MouseOver:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 16) if dark else QColor(0, 0, 0, 9))
            painter.drawRoundedRect(QRectF(rect).adjusted(0, 1, 0, -1), 7, 7)
        painter.drawPixmap(QPointF(rect.left() + 6, rect.center().y() - 7.5),
                           item_check_pixmap(state, dark, accent_color()))
        painter.setPen(QColor(ui_palette(dark)['text']))
        text_rect = rect.adjusted(6 + 16 + 6, 0, -8, 0)
        text = option.fontMetrics.elidedText(str(index.data(Qt.ItemDataRole.DisplayRole) or ''),
                                             Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(120, 26)

    def editorEvent(self, event, model, option, index):
        kind = event.type()
        toggle = False
        if kind == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            toggle = True
        elif kind == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Select):
            toggle = True
        elif kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick):
            return True
        if toggle:
            try:
                state = Qt.CheckState(index.data(Qt.ItemDataRole.CheckStateRole))
            except Exception:
                state = Qt.CheckState.Unchecked
            model.setData(index, Qt.CheckState.Unchecked if state == Qt.CheckState.Checked else Qt.CheckState.Checked,
                          Qt.ItemDataRole.CheckStateRole)
            return True
        return False


# ── translation (style book 1.6; the same scheme as Strawberry's / Broccoli's) ─────────────────────────
UI_LANGUAGES = (('en', 'English'), ('zh_CN', '简体中文'), ('ja_JP', '日本語'))
_TRANSLATORS = []


def _language_file(data_dir: str) -> str:
    return os.path.join(data_dir, 'ui_language.txt')


def read_ui_language_setting(data_dir: str) -> str:
    """English until another language is chosen in the menu (as Strawberry / Broccoli)."""
    try:
        with open(_language_file(data_dir), 'r', encoding='utf-8') as handle:
            code = handle.read().strip()
        return code if code in dict(UI_LANGUAGES) else 'en'
    except OSError:
        return 'en'


def write_ui_language_setting(data_dir: str, code: str) -> None:
    try:
        os.makedirs(data_dir, exist_ok=True)
        with open(_language_file(data_dir), 'w', encoding='utf-8') as handle:
            handle.write(code or '')
    except OSError:
        logging.exception('Saving the language failed.')


def load_translation(lang: str, dirs) -> bool:
    """Install tomato_<lang>.qm from the first of `dirs` that has it. English needs no file."""
    for translator in _TRANSLATORS:
        QCoreApplication.removeTranslator(translator)
    _TRANSLATORS.clear()
    if lang in ('', 'en'):
        return True
    for folder in dirs:
        path = os.path.join(folder, 'tomato_%s.qm' % lang)
        if os.path.isfile(path):
            translator = QTranslator(app)
            if translator.load(path):
                QCoreApplication.installTranslator(translator)
                _TRANSLATORS.append(translator)
                return True
    return False


# ── end time next to the start (style book 5.12 "结束时间", 2026-11-22) ────────────────────────────────
# Ryan 2026-11-22: "在开始时间边上再加一个……结束时间……让用户手动输入时间，然后它自动地去跳转这个结束时间，或者
# 是你让这个用户他手动地去写这个结束时间，然后它自动生成时长"; he chose a date box + a time box for the end.
def _format_length(value: float) -> str:
    value = round(float(value), 4)
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return ('%.4f' % value).rstrip('0').rstrip('.')


class EndTimeLink(QObject):
    """Keeps start + length and the end in step. Start date / time, length or its unit changed → end = start +
    length; end changed by the user → length = end − start, written in the length's unit (None → Hours).
    An end before the start changes nothing; when the end box is left like that, the end goes back to
    start + length. The end itself is never saved: the file keeps start + length."""

    def __init__(self, start_date, start_time, length_edit, length_unit, end_date, end_time, hours_index):
        super().__init__(end_date)
        self.start_date, self.start_time = start_date, start_time
        self.length_edit, self.length_unit = length_edit, length_unit
        self.end_date, self.end_time = end_date, end_time
        self._hours_index = hours_index
        self._busy = False
        start_date.dateChanged.connect(self.follow_start)
        start_time.timeChanged.connect(self.follow_start)
        length_edit.textChanged.connect(self.follow_start)
        length_unit.currentIndexChanged.connect(self.follow_start)
        end_date.dateChanged.connect(self._end_changed)
        end_time.timeChanged.connect(self._end_changed)
        end_date.installEventFilter(self)
        end_time.installEventFilter(self)
        self.follow_start()

    def _start(self):
        from PyQt6.QtCore import QDateTime
        return QDateTime(self.start_date.date(), self.start_time.time())

    def _end(self):
        from PyQt6.QtCore import QDateTime
        return QDateTime(self.end_date.date(), self.end_time.time())

    def length_hours(self):
        """The length box in hours (None when it is not a number); empty = 0."""
        text = self.length_edit.text().strip()
        if text in ('', '-'):
            return 0.0
        try:
            value = float(text)
        except ValueError:
            return None
        factor = self.length_unit.currentData()
        return value * float(1 if factor is None else factor)

    def _set_end(self, when):
        self._busy = True
        try:
            self.end_date.setDate(when.date())
            self.end_time.setTime(when.time())
        finally:
            self._busy = False

    def follow_start(self, *_args):
        if self._busy:
            return
        hours = self.length_hours()
        if hours is None or hours < 0:
            return
        seconds = int(math.floor(hours * 60 + 0.5)) * 60      # the boxes show minutes (half a minute rounds up)
        self._set_end(self._start().addSecs(seconds))

    def _end_changed(self, *_args):
        if self._busy:
            return
        seconds = self._start().secsTo(self._end())
        if seconds < 0:
            return
        self._busy = True
        try:
            factor = self.length_unit.currentData()
            if factor is None:
                self.length_unit.setCurrentIndex(self._hours_index)
                factor = self.length_unit.currentData() or 1
            self.length_edit.setText(_format_length(seconds / 3600.0 / float(factor)))
        finally:
            self._busy = False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusOut and self._start().secsTo(self._end()) < 0:
            QTimer.singleShot(0, self.follow_start)
        return False


def end_time_boxes(parent, start_date, start_time):
    """The '→' and the end's date box and time box, sized like the start's (style book 5.12)."""
    arrow = QLabel('→', parent)
    arrow.setFixedWidth(14)
    arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
    arrow.setStyleSheet('color: #8E8E93; background: transparent;')
    end_date = QDateEdit(parent)
    end_date.setDisplayFormat('yyyy-MM-dd')
    end_date.setDate(start_date.date())
    end_date.setFixedHeight(GREY_ROW_HEIGHT)
    end_date.setToolTip(_tr('End date'))
    end_time = QTimeEdit(parent)
    end_time.setDisplayFormat('HH:mm')
    end_time.setTime(start_time.time())
    end_time.setFixedHeight(GREY_ROW_HEIGHT)
    end_time.setToolTip(_tr('End time'))
    for start, end in ((start_date, end_date), (start_time, end_time)):
        if start.minimumWidth() == start.maximumWidth():
            end.setFixedWidth(start.minimumWidth())
        else:
            end.setSizePolicy(start.sizePolicy())
    return arrow, end_date, end_time


# ── the quick-edit card next to a table row (style book 5.12, 2026-11-22) ─────────────────────────────
# Ryan 2026-11-22: "我在选中了这一项之后呢……我可以右键，然后它可以弹出一个小小的框。最好是它在这个被点击的边上
# 弹出来……包含这个事情的名称……时间……时长，所有那些我们一开始设置的那些框框"; he chose the small edit card
# right at the row.
QUICK_EDIT_WIDTH = 480     # the start → end row (118 + 76 + 14 + 118 + 76 + gaps) fits


class QuickEditCard(GlassFormDialog):
    """An edit dialog (window glass, corner 16, grey Cancel / Save) that opens right at a table row instead
    of over the middle of the main window. Not modal: a click anywhere else in Tomato = Cancel (the click
    still does what it does); Return = Save, Esc = Cancel. Windows in `allowed_windows` (the boxes' own
    pop-ups) do not count as "else"."""

    def __init__(self, title, parent=None):
        super().__init__(title, parent, ok_text=_tr('Save'))
        self._no_auto_place = True
        self._keep_width = True
        self.setFixedWidth(QUICK_EDIT_WIDTH)
        self.allowed_windows = []
        self._watching = False
        self.validate = None          # → '' or what is wrong (said with the system alert; the card stays)

    def accept(self):
        problem = self.validate() if callable(self.validate) else ''
        if problem:
            tomato_alert(self, self.windowTitle(), problem)
            return
        super().accept()

    def place_at(self, row_rect: QRect, mouse_x: int):
        """Top 4 under the row (`row_rect` in global coordinates), left edge 24 left of the mouse; above the
        row when there is no room below; at least 8 from the screen's edges."""
        self.adjustSize()
        size = self.sizeHint().expandedTo(self.size())
        width, height = QUICK_EDIT_WIDTH, size.height()
        screen = QApplication.screenAt(row_rect.center()) or self.screen()
        area = screen.availableGeometry()
        x = mouse_x - 24
        y = row_rect.bottom() + 4
        if y + height > area.bottom() - 8:
            y = row_rect.top() - 4 - height
        x = max(area.left() + 8, min(x, area.right() - width - 8))
        y = max(area.top() + 8, min(y, area.bottom() - height - 8))
        self.resize(width, height)
        self.move(int(x), int(y))

    def showEvent(self, event):
        super().showEvent(event)
        if not self._watching:
            app.installEventFilter(self)
            self._watching = True

    def done(self, result):
        if self._watching:
            app.removeEventFilter(self)
            self._watching = False
        super().done(result)

    def _counts_as_inside(self, widget):
        top = widget.window()
        if top is self or self.isAncestorOf(widget):
            return True
        if top.windowType() in (Qt.WindowType.Popup, Qt.WindowType.ToolTip):
            return True
        return any(top is window for window in self.allowed_windows if window is not None)

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Type.MouseButtonPress and isinstance(obj, QWidget) and self.isVisible()
                and not self._counts_as_inside(obj)):
            QTimer.singleShot(0, self.reject)
        return False


# ── the show / hide shortcut (style book 5.12, 2026-11-22) ────────────────────────────────────────────
class ShortcutDialog(GlassFormDialog):
    """Record the show / hide shortcut: a read-only box showing it the Mac way (⌃⌥T), Record (the next key
    press with at least one of ⌃ ⌥ ⌘ fills it; Esc stops), Clear (= no shortcut), Cancel / Save. `value` is
    the shortcut text ('<ctrl>+<alt>+t', '' = none)."""

    def __init__(self, value, parent=None):
        import tomato_hotkey
        self._hotkey = tomato_hotkey
        super().__init__(_tr('Show/Hide shortcut'), parent, ok_text=_tr('Save'))
        self.value = tomato_hotkey.normalize(value)
        self._recording = False
        hint = QLabel(_tr('Press it anywhere to slide Tomato out, bring it to the front, or slide it back in.'), self)
        hint.setWordWrap(True)
        hint.setStyleSheet('color: #8E8E93; font-size: 12px; background: transparent;')
        self.box = QLineEdit(self)
        self.box.setReadOnly(True)
        self.box.setFixedHeight(GREY_ROW_HEIGHT)
        self.box.setPlaceholderText(_tr('No shortcut'))
        self.record_button = MacNormalButton(_tr('Record'), self)
        self.record_button.setMinimumWidth(96)
        self.record_button.setAutoDefault(False)
        self.record_button.clicked.connect(self._toggle_recording)
        self.clear_button = MacNormalButton(_tr('Clear'), self)
        self.clear_button.setMinimumWidth(96)
        self.clear_button.setAutoDefault(False)
        self.clear_button.clicked.connect(self._clear)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self.box, 1)
        row.addWidget(self.record_button)
        row.addWidget(self.clear_button)
        self.problem = QLabel('', self)
        self.problem.setWordWrap(True)
        self.problem.setStyleSheet('color: #FF6B6B; font-size: 12px; background: transparent;')
        self.problem.hide()
        self.body.addWidget(hint)
        self.body.addLayout(row)
        self.body.addWidget(self.problem)
        self._show_value()
        self.adjustSize()

    def _show_value(self):
        self.box.setText(self._hotkey.display(self.value))

    def _say(self, text):
        self.problem.setText(text)
        self.problem.setVisible(bool(text))
        self.adjustSize()

    def _toggle_recording(self):
        self._set_recording(not self._recording)

    def _set_recording(self, on):
        self._recording = bool(on)
        self.record_button.setText(_tr('Press keys…') if on else _tr('Record'))
        self.ok_button.setEnabled(not on)
        if on:
            self._say('')
            self.setFocus()
            app.installEventFilter(self)
        else:
            app.removeEventFilter(self)

    def _clear(self):
        self._set_recording(False)
        self.value = ''
        self._say('')
        self._show_value()

    def eventFilter(self, obj, event):
        if not self._recording or event.type() != QEvent.Type.KeyPress:
            return False
        key = event.key()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Meta, Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_CapsLock):
            return True
        mods = event.modifiers()
        if sys.platform == 'darwin':     # Qt names ⌘ "Control" and ⌃ "Meta" on the Mac
            ctrl, cmd = bool(mods & Qt.KeyboardModifier.MetaModifier), bool(mods & Qt.KeyboardModifier.ControlModifier)
        else:
            ctrl, cmd = bool(mods & Qt.KeyboardModifier.ControlModifier), bool(mods & Qt.KeyboardModifier.MetaModifier)
        alt, shift = bool(mods & Qt.KeyboardModifier.AltModifier), bool(mods & Qt.KeyboardModifier.ShiftModifier)
        if key == Qt.Key.Key_Escape and not (ctrl or alt or cmd or shift):
            self._set_recording(False)
            return True
        text = self._hotkey.from_key_press(event.nativeVirtualKey(), ctrl, alt, shift, cmd)
        if not text:
            self._say(_tr('This key cannot be used for the shortcut.'))
        elif not self._hotkey.usable(text):
            self._say(_tr('Use the key together with at least one of ⌃ ⌥ ⌘.'))
        else:
            self.value = text
            self._show_value()
            self._say('')
            self._set_recording(False)
        return True

    def done(self, result):
        if self._recording:
            self._set_recording(False)
        super().done(result)
