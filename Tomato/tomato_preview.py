# -*- coding: utf-8 -*-
"""Tomato's Markdown preview as a web page (2026-11-20).

Ryan 2026-11-20: "Tomato 的也跟着一起改" — the Collection page's preview was Qt's own text view, which runs
no scripts, so formulas were never typeset. It is now a web view (as Strawberry's since 2026-11-11) with
Tomato's own MathJax (MathJax-2.7.9/, no network). The page itself comes from markdown_preview.py.

MarkdownWebPreview answers the few calls the old QTextBrowser got: setHtml, setPlainText,
verticalScrollBar() (maximum / value / setValue, by fraction of the page), setOpenExternalLinks, setReadOnly.
The web view is made with the widget — before the window is shown — because the first web view makes Qt
rebuild the window's native view; made later, the glass, the traffic lights and the "all Spaces" mark that
hang on that view would have to be put back.
PyQt6.QtWebEngineWidgets must have been imported before the QApplication was made (the main file does it).
"""
import html
import json
import os

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView

SCROLL_RANGE = 100000   # the stand-in scroll bar's maximum: the page is scrolled by fraction

_FRACTION_JS = ('(function(){var r = document.documentElement.scrollHeight - window.innerHeight;'
                'return r > 0 ? window.scrollY / r : 0;})()')


class _Page(QWebEnginePage):
    """Shows the preview only: a clicked link opens in the default browser."""

    def acceptNavigationRequest(self, url, kind, is_main_frame):
        if kind == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            if url.scheme() in ('http', 'https', 'mailto', 'file'):
                QDesktopServices.openUrl(url)
            return False
        return True

    def createWindow(self, kind):
        return None


class _ScrollBar:
    """What the page's code asks of a scroll bar: a position between 0 and SCROLL_RANGE."""

    def __init__(self, owner):
        self._owner = owner

    def maximum(self):
        return SCROLL_RANGE

    def value(self):
        return int(round(self._owner.fraction() * SCROLL_RANGE))

    def setValue(self, value):
        self._owner.scroll_to_fraction(float(value) / SCROLL_RANGE)


class MarkdownWebPreview(QWidget):
    def __init__(self, parent=None, base_folder=''):
        super().__init__(parent)
        self._base = QUrl.fromLocalFile((base_folder or '/').rstrip('/') + '/')
        self._fraction = 0.0
        self._wanted = None            # a fraction to go to once the page has loaded
        self._scroll_bar = _ScrollBar(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._view = QWebEngineView(self)
        self._page = _Page(self._view)
        self._view.setPage(self._page)
        self._view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self._page.loadFinished.connect(self._on_loaded)
        self._page.scrollPositionChanged.connect(lambda _point: self._page.runJavaScript(_FRACTION_JS, self._remember))
        layout.addWidget(self._view)

    # the QTextBrowser calls
    def setHtml(self, page_html):
        self._wanted = self._fraction
        self._view.setHtml(str(page_html or ''), self._base)

    def setPlainText(self, text):
        self.setHtml('<html><body><pre style="white-space: pre-wrap; font: 14px Menlo, monospace">%s</pre></body></html>'
                     % html.escape(str(text or '')))

    def verticalScrollBar(self):
        return self._scroll_bar

    def setOpenExternalLinks(self, on):
        pass                           # always: see _Page

    def setReadOnly(self, read_only):
        pass

    def set_background(self, color):
        self._page.setBackgroundColor(QColor(color))

    # the position
    def fraction(self) -> float:
        return self._fraction

    def scroll_to_fraction(self, fraction):
        self._fraction = max(0.0, min(1.0, float(fraction)))
        self._wanted = self._fraction
        self._page.runJavaScript(
            '(function(f){var r = document.documentElement.scrollHeight - window.innerHeight;'
            'window.scrollTo(0, Math.max(0, r) * f);})(%s)' % json.dumps(self._fraction))

    def run_javascript(self, script, callback=None):
        """Runs a script in the page; callback(result) when given."""
        if callback is None:
            self._page.runJavaScript(script)
        else:
            self._page.runJavaScript(script, callback)

    def base_url(self):
        return self._base

    def _remember(self, value):
        try:
            self._fraction = max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            pass

    def _on_loaded(self, _ok):
        if self._wanted is not None:
            wanted, self._wanted = self._wanted, None
            self.scroll_to_fraction(wanted)
            self._wanted = None
