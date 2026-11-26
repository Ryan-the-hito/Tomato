# -*- coding: utf-8 -*-
"""A long picture of a page the app wrote itself, for sharing (2026-11-25).

Ryan 2026-11-25: "每天的汇报…我是希望他可以截图分享的…什么都没有选中直接点击分享的话，那就是全部的内容形成一条
长图，那如果说是选中了一部分内容的话，那就是只把选中的那一部分去生成图片".

The page is loaded into a web view nobody sees and photographed in pieces of one size; a piece is taken after
the page says it has painted, overlaps the one before and is taken again while the overlap differs; the seam
lies in the middle of the overlap. Then the picture is cut to its content and gets the same margin on all four
sides (on a worker thread — the pixel work never holds the window up).

  maker = SharePictureMaker(some_widget)          # the hidden web view becomes a child of it
  maker.finished.connect(lambda pixmap: …)        # a null pixmap = it did not work
  maker.make(page_html, base_url, width, dark, only_html='')   # only_html: show just this fragment in the page

PyQt6.QtWebEngineWidgets must have been imported before the QApplication was made.
Tests: tests_dev/tm_share_test.py.
"""
import json
import logging
import math

from PyQt6.QtCore import QObject, QRect, QThread, QTimer, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView

# ── the share picture: laying the page out, the pieces, the margins (2026-11-18) ──
SHARE_CAPTURE_MAX_WIDTH = 1200    # css px: the widest the page is laid out for a wide table
SHARE_TILE_HEIGHT = 1200          # css px of one piece
SHARE_TILE_OVERLAP = 64           # css px two pieces share (compared, and the seam lies in its middle)
SHARE_TILE_RETRIES = 6
SHARE_PICTURE_SCALE = 2.0         # pixels per css px in the finished picture
SHARE_MARGIN_CSS = 24             # the white margin of the finished picture, the same on all four sides
SHARE_MARGIN_PIXELS = 64          # the same for pictures that do not say how many pixels a point is

# Opens the boxes that scroll sideways in the window, hides the copy buttons, and measures where
# the content really is (text by its own lines, so text that sticks out of its box counts).
SHARE_CAPTURE_MEASURE_JS = r"""
(() => {
  const doc = document.documentElement;
  const body = document.body || doc;
  const styleId = 'share-picture-open-boxes';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      html, body { overflow-x: visible !important; }
      table, pre, .codehilite {
        overflow: visible !important; max-width: none !important;
      }
      pre, .codehilite pre {
        white-space: pre-wrap !important; overflow-wrap: anywhere !important;
      }
    `;
    document.head.appendChild(style);
  }
  window.scrollTo(0, 0);
  const rects = [];
  const addRect = (rect) => {
    if (!rect || rect.width < 1 || rect.height < 1) return;
    rects.push({left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom});
  };
  const root = document.querySelector('.share-capture') || body;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) => (node.nodeValue && node.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT)
  });
  const range = document.createRange();
  let node;
  while ((node = walker.nextNode())) {
    const parent = node.parentElement;
    if (parent && parent.closest('script, style, noscript')) continue;
    range.selectNodeContents(node);
    for (const rect of range.getClientRects()) addRect(rect);
  }
  if (range.detach) range.detach();
  const mediaSelector = [
    'img', 'video', 'canvas', 'svg', 'table', 'pre', 'blockquote'
  ].join(',');
  root.querySelectorAll(mediaSelector).forEach((el) => {
    const st = window.getComputedStyle(el);
    if (!st || st.display === 'none' || st.visibility === 'hidden' || Number(st.opacity || 1) === 0) return;
    addRect(el.getBoundingClientRect());
  });
  if (!rects.length) addRect((root || body).getBoundingClientRect());
  return {
    left: Math.min(...rects.map(r => r.left)),
    top: Math.min(...rects.map(r => r.top)),
    right: Math.max(...rects.map(r => r.right)),
    bottom: Math.max(...rects.map(r => r.bottom)),
    layoutWidth: Math.ceil((doc && doc.clientWidth) || window.innerWidth || 0)
  };
})();
"""


def share_capture_plan(metrics: dict, view_width: int, slack: int = 8) -> dict:
    """Where the content is (css px) → what to photograph. 'widen_to' (0 = no): the page should be
    laid out this wide first, because something sticks out on the right."""
    def number(key, default=0.0):
        try:
            return float(metrics.get(key, default) or 0)
        except (TypeError, ValueError):
            return float(default)
    left, top = max(0.0, number('left')), max(0.0, number('top'))
    right, bottom = max(left + 1, number('right')), max(top + 1, number('bottom'))
    layout_w = max(1, int(view_width))
    needed = int(math.ceil(right + left))            # as much room on the right as there is on the left
    widen_to = min(SHARE_CAPTURE_MAX_WIDTH, needed) if needed > layout_w + 1 and layout_w < SHARE_CAPTURE_MAX_WIDTH else 0
    content_left, content_top = max(0, int(left) - slack), max(0, int(top) - slack)
    content_w = int(math.ceil(right)) + slack - content_left
    content_h = int(math.ceil(bottom)) + slack - content_top
    return {'widen_to': widen_to if widen_to > layout_w else 0, 'layout_w': layout_w,
            'content_left': content_left, 'content_top': content_top, 'content_w': max(1, content_w),
            'content_h': max(1, content_h), 'capture_w': max(layout_w, content_left + content_w)}


def share_tile_offsets(content_h: int, tile_h: int, overlap: int) -> list:
    """Where each piece starts (css px): every piece is tile_h high, shares `overlap` with the one
    before, and the last one ends exactly at the end (it shares more instead of being shorter)."""
    content_h, tile_h = max(1, int(content_h)), max(1, int(tile_h))
    if content_h <= tile_h:
        return [0]
    step = max(1, tile_h - max(0, int(overlap)))
    offsets, offset = [], 0
    while offset + tile_h < content_h:
        offsets.append(offset)
        offset += step
    offsets.append(content_h - tile_h)
    return offsets


def share_tiles_agree(upper: QImage, lower: QImage, lower_starts_at: int, shared: int, tolerance: int = 60) -> bool:
    """Do two pieces show the same thing where they overlap? (pixels; the lower piece starts
    `lower_starts_at` rows down the upper one, they share `shared` rows.) Looked at on a grid.
    Counted against the points that are not plain background in either piece — most of a page is
    white, so "nearly all points agree" says nothing — and a few may differ (text is not drawn
    identically at two positions)."""
    shared = min(int(shared), upper.height() - int(lower_starts_at), lower.height())
    width = min(upper.width(), lower.width())
    if shared <= 4 or width <= 0:
        return True
    background = upper.pixel(0, int(lower_starts_at)) & 0xFFFFFF

    def far(a, b):
        return (abs(((a >> 16) & 0xFF) - ((b >> 16) & 0xFF)) > tolerance or abs(((a >> 8) & 0xFF) - ((b >> 8) & 0xFF)) > tolerance
                or abs((a & 0xFF) - (b & 0xFF)) > tolerance)

    drawn = differ = 0
    for y in range(2, shared - 2, max(1, shared // 64)):
        for x in range(0, width, max(1, width // 400)):
            a, b = upper.pixel(x, int(lower_starts_at) + y), lower.pixel(x, y)
            if far(a, background) or far(b, background):
                drawn += 1
                if far(a, b):
                    differ += 1
    return differ <= max(3, drawn * 0.12)


def stitch_share_tiles(tiles: list, content_w: int, content_h: int, tile_h: int, bg: QColor) -> QImage:
    """tiles: [(offset css px, image, pixels per css px)] top to bottom → one picture. Where two
    pieces overlap, the upper half of the overlap comes from the upper piece, the lower half from
    the lower one: no piece's edge rows are used inside the picture."""
    dpr = max(1.0, float(tiles[0][2]))
    canvas_w, canvas_h = max(1, int(int(content_w) * dpr)), max(1, int(int(content_h) * dpr))
    scale = 1.0
    max_canvas_h = 120000
    if canvas_h > max_canvas_h:
        scale = max_canvas_h / canvas_h
        canvas_w, canvas_h = max(1, int(canvas_w * scale)), max_canvas_h
    canvas = QImage(canvas_w, canvas_h, QImage.Format.Format_ARGB32)
    canvas.fill(bg)
    painter = QPainter(canvas)
    previous_end = None
    for offset, image, _dpr in tiles:
        skip = 0
        if previous_end is not None:
            skip = max(0, int(round((previous_end - offset) * dpr / 2)))     # half of what is shared
        skip = min(skip, max(0, image.height() - 1))
        part = image.copy(0, skip, image.width(), image.height() - skip)
        part.setDevicePixelRatio(1.0)      # plain pixels: never drawn at half size (see the grab)
        y = int(round(offset * dpr)) + skip
        if scale != 1.0:
            painter.drawImage(QRect(0, int(y * scale), max(1, int(part.width() * scale)), max(1, int(math.ceil(part.height() * scale)))), part)
        else:
            painter.drawImage(0, y, part)
        previous_end = offset + int(tile_h)
    painter.end()
    return canvas


def share_pixel_is_background(image: QImage, x: int, y: int, bg: QColor, tolerance: int = 18) -> bool:
    pixel = image.pixel(x, y)
    alpha = (pixel >> 24) & 0xFF
    if alpha < 8:
        return True
    red = (pixel >> 16) & 0xFF
    green = (pixel >> 8) & 0xFF
    blue = pixel & 0xFF
    return (
        abs(red - bg.red()) <= tolerance
        and abs(green - bg.green()) <= tolerance
        and abs(blue - bg.blue()) <= tolerance
    )


def share_row_has_content(image: QImage, y: int, bg: QColor, x1: int = 0, x2: int | None = None) -> bool:
    width = image.width()
    if x2 is None:
        x2 = width - 1
    x1 = max(0, min(width - 1, int(x1)))
    x2 = max(0, min(width - 1, int(x2)))
    if x2 < x1:
        return False
    step = 1 if (x2 - x1) <= 900 else 2
    for x in range(x1, x2 + 1, step):
        if not share_pixel_is_background(image, x, y, bg):
            return True
    if step > 1 and not share_pixel_is_background(image, x2, y, bg):
        return True
    return False


def share_column_has_content(image: QImage, x: int, bg: QColor, y1: int, y2: int) -> bool:
    height = image.height()
    y1 = max(0, min(height - 1, int(y1)))
    y2 = max(0, min(height - 1, int(y2)))
    if y2 < y1:
        return False
    step = 1 if (y2 - y1) <= 1600 else 2
    for y in range(y1, y2 + 1, step):
        if not share_pixel_is_background(image, x, y, bg):
            return True
    if step > 1 and not share_pixel_is_background(image, x, y2, bg):
        return True
    return False


def share_image_content_bounds(image: QImage, bg: QColor) -> QRect:
    if image.isNull():
        return QRect()
    width = image.width()
    height = image.height()
    top = None
    bottom = None
    for y in range(height):
        if share_row_has_content(image, y, bg):
            top = y
            break
    if top is None:
        return QRect()
    for y in range(height - 1, top - 1, -1):
        if share_row_has_content(image, y, bg):
            bottom = y
            break
    left = None
    right = None
    for x in range(width):
        if share_column_has_content(image, x, bg, top, bottom):
            left = x
            break
    if left is None:
        return QRect()
    for x in range(width - 1, left - 1, -1):
        if share_column_has_content(image, x, bg, top, bottom):
            right = x
            break
    # exactly the content: the margins are put on afterwards, the same on every side
    return QRect(left, top, right - left + 1, bottom - top + 1)


def crop_share_image_to_content(image: QImage, bg: QColor) -> QImage:
    if image.isNull():
        return image
    bounds = share_image_content_bounds(image, bg)
    if not bounds.isValid() or bounds.isNull():
        return image
    return image.copy(bounds)


def compress_share_vertical_whitespace(image: QImage, bg: QColor) -> QImage:
    if image.isNull():
        return image
    width = image.width()
    height = image.height()
    row_has_content = [share_row_has_content(image, y, bg) for y in range(height)]
    bands = []
    y = 0
    max_blank = 48
    while y < height:
        start = y
        has_content = row_has_content[y]
        while y < height and row_has_content[y] == has_content:
            y += 1
        length = y - start
        if has_content:
            bands.append((start, length, length))
            continue
        keep = min(length, max_blank)
        if keep > 0 and bands and y < height:
            bands.append((start, length, keep))
    new_h = max(1, sum(keep for _start, _length, keep in bands))
    if new_h >= height:
        return image
    result = QImage(width, new_h, QImage.Format.Format_ARGB32)
    result.fill(bg)
    painter = QPainter(result)
    target_y = 0
    for start, length, keep in bands:
        if keep <= 0:
            continue
        if keep == length:
            painter.drawImage(0, target_y, image.copy(0, start, width, length))
        target_y += keep
    painter.end()
    return result


def add_share_image_outer_padding(image: QImage, bg: QColor, margin: int = SHARE_MARGIN_PIXELS) -> QImage:
    """The white margin of a share picture: the same on all four sides (2026-11-18, Ryan:
    "四周白边一样宽"; it used to be 64 / 164 / 116 / 128 pixels left / right / top / bottom)."""
    if image.isNull():
        return image
    pad_left = pad_top = pad_right = pad_bottom = max(0, int(margin))
    result = QImage(
        image.width() + pad_left + pad_right,
        image.height() + pad_top + pad_bottom,
        QImage.Format.Format_ARGB32,
    )
    result.fill(bg)
    painter = QPainter(result)
    painter.drawImage(pad_left, pad_top, image)
    painter.end()
    return result


def finalize_share_image_worker(image: QImage, bg: QColor, margin: int | None = None) -> QImage:
    if image.isNull():
        return image
    image = crop_share_image_to_content(image, bg)
    image = compress_share_vertical_whitespace(image, bg)
    image = crop_share_image_to_content(image, bg)
    image = add_share_image_outer_padding(image, bg, SHARE_MARGIN_PIXELS if margin is None else margin)
    return image


def share_background(dark: bool) -> QColor:
    return QColor('#2D2D2D' if dark else '#FFFFFF')


def share_preview_pixmap(pixmap: QPixmap, width: int, height: int, screen_scale: float) -> QPixmap:
    """The share picture made to fit width × height points, with screen_scale pixels per point
    (never enlarged beyond the picture's own pixels)."""
    source = QPixmap(pixmap)
    source.setDevicePixelRatio(1.0)
    scale = max(1.0, float(screen_scale))
    fit = min(width * scale / max(1, source.width()), height * scale / max(1, source.height()), 1.0)
    shown = source.scaled(max(1, int(round(source.width() * fit))), max(1, int(round(source.height() * fit))),
                          Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    shown.setDevicePixelRatio(scale)
    return shown


# Shows only one fragment in the loaded page (the selected part): the page keeps its styles.
SHARE_ONLY_FRAGMENT_JS = r"""
(function(fragment){
  var body = document.body;
  if (!body) return false;
  var holder = document.createElement('div');
  holder.className = 'share-capture';
  holder.innerHTML = fragment;
  while (body.firstChild) body.removeChild(body.firstChild);
  body.appendChild(holder);
  return true;
})(%s);
"""

# What is selected in a page, as HTML that keeps its block's look (a selection inside a heading stays a heading).
SHARE_SELECTION_JS = r"""
(() => {
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0 || !sel.toString().trim()) return null;
  const container = document.createElement('div');
  for (let i = 0; i < sel.rangeCount; i++) {
    const range = sel.getRangeAt(i);
    const fragment = range.cloneContents();
    let host = range.commonAncestorContainer;
    if (host && host.nodeType !== Node.ELEMENT_NODE) host = host.parentElement;
    const styledHost = host && host.closest
      ? host.closest('pre, code, blockquote, table, p, li, h1, h2, h3, h4, h5, h6, td, th')
      : null;
    if (styledHost && styledHost !== document.body && styledHost !== document.documentElement) {
      let wrapper = styledHost.cloneNode(false);
      wrapper.appendChild(fragment);
      // a list item or a table cell alone is not laid out as one: give it its list / table back
      const tag = styledHost.tagName;
      if (tag === 'LI' && styledHost.parentElement) {
        const list = styledHost.parentElement.cloneNode(false); list.appendChild(wrapper); wrapper = list;
      } else if (tag === 'TD' || tag === 'TH') {
        const table = document.createElement('table'); const row = document.createElement('tr');
        row.appendChild(wrapper); table.appendChild(row); wrapper = table;
      }
      container.appendChild(wrapper);
    } else {
      container.appendChild(fragment);
    }
  }
  return {html: container.innerHTML, text: sel.toString()};
})();
"""


class _FinishThread(QThread):
    done = pyqtSignal(object)

    def __init__(self, image, bg, margin, parent=None):
        super().__init__(parent)
        self._image, self._bg, self._margin = image, bg, margin

    def run(self):
        try:
            image = finalize_share_image_worker(self._image, self._bg, self._margin)
        except Exception:
            logging.exception('Share picture: finishing failed')
            image = QImage()
        self.done.emit(image)


class SharePictureMaker(QObject):
    finished = pyqtSignal(object)        # QPixmap; null = no picture
    PAINTED_TITLE = 'share-picture-painted:'
    SETTLE_MS = 350                      # after the page has loaded: formulas and fonts settle

    def __init__(self, host_widget):
        super().__init__(host_widget)
        self._host = host_widget
        self._state = None
        self._view = None
        self._thread = None
        self._dark = False

    def busy(self) -> bool:
        return self._view is not None or self._thread is not None

    def make(self, page_html: str, base_url=None, width: int = 720, dark: bool = False, only_html: str = '') -> bool:
        if self.busy() or not str(page_html or '').strip():
            return False
        self._dark = bool(dark)
        view = QWebEngineView(self._host)
        view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        view.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        view.setGeometry(-10000, -10000, min(1600, max(320, int(width))), 200)
        view.page().setBackgroundColor(share_background(self._dark))
        view.show()
        self._view = view

        def loaded(ok):
            try:
                view.loadFinished.disconnect(loaded)
            except Exception:
                pass
            if not ok or self._view is not view:
                self._fail()
                return
            if only_html:
                view.page().runJavaScript(SHARE_ONLY_FRAGMENT_JS % json.dumps(str(only_html)))
            QTimer.singleShot(self.SETTLE_MS, lambda: self._measure(0))

        view.loadFinished.connect(loaded)
        if isinstance(base_url, QUrl):
            view.setHtml(str(page_html), base_url)
        elif base_url:
            view.setHtml(str(page_html), QUrl(str(base_url)))
        else:
            view.setHtml(str(page_html))
        return True

    # ── measuring, the pieces ──
    def _measure(self, passes):
        view = self._view
        if view is None:
            return
        view.page().runJavaScript(SHARE_CAPTURE_MEASURE_JS, lambda metrics: self._start(metrics, passes))

    def _start(self, metrics, passes):
        view = self._view
        if view is None:
            return
        if not isinstance(metrics, dict):
            self._fail()
            return
        plan = share_capture_plan(metrics, view.width())
        if plan['widen_to'] and passes < 2:
            # a table needs more room than the page has: lay the page out wider and measure again
            view.resize(plan['widen_to'], view.height())
            QTimer.singleShot(160, lambda: self._measure(passes + 1))
            return
        try:
            screen_scale = max(1.0, float(view.devicePixelRatioF()))
        except Exception:
            screen_scale = 1.0
        # the picture has SHARE_PICTURE_SCALE pixels per point: on a Retina screen the page is photographed
        # as it is, on an ordinary one it is drawn twice as large first
        render_scale = max(1.0, SHARE_PICTURE_SCALE / screen_scale)
        tile_h = min(SHARE_TILE_HEIGHT, plan['content_h'])
        self._state = dict(plan, render_scale=render_scale, tile_h=tile_h,
                           offsets=share_tile_offsets(plan['content_h'], tile_h, SHARE_TILE_OVERLAP),
                           index=0, tiles=[], tries=0, serial=0, waiting=None)
        view.setGeometry(-10000, -10000, max(1, int(plan['capture_w'] * render_scale)), max(1, int(tile_h * render_scale)))
        view.titleChanged.connect(self._on_title)
        self._next_piece()

    def _next_piece(self):
        state, view = self._state, self._view
        if not state or view is None:
            return
        if int(state['index']) >= len(state['offsets']):
            self._stitch()
            return
        offset = int(state['offsets'][int(state['index'])])
        layout_w = int(state['layout_w'])
        render_scale = float(state['render_scale'])
        bg = share_background(self._dark).name()
        style_css = f"""
          html {{
            overflow: hidden !important; scrollbar-width: none !important; background: {bg} !important;
            width: {layout_w}px !important; min-width: {layout_w}px !important; max-width: {layout_w}px !important;
          }}
          body {{
            overflow: visible !important;
            width: {layout_w}px !important; min-width: {layout_w}px !important; max-width: {layout_w}px !important;
            box-sizing: border-box !important;
            transform: scale({render_scale}) translate(-{int(state['content_left'])}px, -{int(state['content_top']) + offset}px) !important;
            transform-origin: 0 0 !important;
            background: {bg} !important;
          }}
          ::-webkit-scrollbar {{ display: none !important; width: 0 !important; height: 0 !important; }}
        """
        state['serial'] = int(state['serial']) + 1
        serial = int(state['serial'])
        state['waiting'] = serial
        view.page().runJavaScript(
            f"""
            (() => {{
              const styleId = 'share-picture-capture-style';
              let style = document.getElementById(styleId);
              if (!style) {{
                style = document.createElement('style');
                style.id = styleId;
                document.head.appendChild(style);
              }}
              style.textContent = {json.dumps(style_css)};
              window.scrollTo(0, 0);
              // two frames later the new position has been painted: say so
              requestAnimationFrame(() => requestAnimationFrame(() => {{
                document.title = {json.dumps(self.PAINTED_TITLE)} + {serial};
              }}));
            }})();
            """
        )
        # a page that never says so (no frames while hidden) is photographed anyway
        QTimer.singleShot(1500, lambda: self._piece_ready(serial, 0))

    def _on_title(self, title):
        title = str(title or '')
        if not title.startswith(self.PAINTED_TITLE):
            return
        try:
            serial = int(title[len(self.PAINTED_TITLE):])
        except ValueError:
            return
        self._piece_ready(serial, 120)       # the frame also has to reach the widget

    def _piece_ready(self, serial, delay_ms):
        state = self._state
        if not state or state.get('waiting') != serial:
            return                           # already taken, or another capture
        state['waiting'] = None
        QTimer.singleShot(max(0, int(delay_ms)), self._grab)

    def _grab(self):
        state, view = self._state, self._view
        if not state or view is None:
            return
        pixmap = view.grab()
        if pixmap.isNull():
            self._fail()
            return
        effective_dpr = max(1.0, float(pixmap.devicePixelRatio())) * float(state['render_scale'])
        image = pixmap.toImage()
        # plain pixels from here on: a picture that still says "2 pixels per point" is drawn at half its size
        image.setDevicePixelRatio(1.0)
        tile = image.copy(0, 0, min(image.width(), int(round(int(state['content_w']) * effective_dpr))),
                          min(image.height(), int(round(int(state['tile_h']) * effective_dpr))))
        index = int(state['index'])
        offset = int(state['offsets'][index])
        if state['tiles']:
            previous_offset, previous, _dpr = state['tiles'][-1]
            shared = int(round((previous_offset + int(state['tile_h']) - offset) * effective_dpr))
            same = share_tiles_agree(previous, tile, int(round((offset - previous_offset) * effective_dpr)), shared)
            if not same and int(state['tries']) < SHARE_TILE_RETRIES:
                state['tries'] = int(state['tries']) + 1     # the page had not drawn this position yet
                QTimer.singleShot(250, self._grab)
                return
            if not same:
                logging.warning('Share picture: piece %d still differs from the one before; used as it is.', index)
        state['tries'] = 0
        state['tiles'].append((offset, tile, effective_dpr))
        state['index'] = index + 1
        self._next_piece()

    # ── the end ──
    def _drop_view(self):
        view, self._view = self._view, None
        state, self._state = self._state, None
        if view is not None:
            try:
                view.titleChanged.disconnect(self._on_title)
            except Exception:
                pass
            view.hide()
            view.deleteLater()
        return state

    def _fail(self):
        self._drop_view()
        self.finished.emit(QPixmap())

    def _stitch(self):
        state = self._drop_view()
        tiles = (state or {}).get('tiles') or []
        if not tiles:
            self.finished.emit(QPixmap())
            return
        dpr = max(1.0, float(tiles[0][2]))
        bg = share_background(self._dark)
        canvas = stitch_share_tiles(tiles, int(state['content_w']), int(state['content_h']), int(state['tile_h']), bg)
        self._thread = _FinishThread(canvas, bg, int(round(SHARE_MARGIN_CSS * dpr)), self)
        self._thread.done.connect(self._finished, Qt.ConnectionType.QueuedConnection)
        self._thread.start()

    def _finished(self, image):
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.wait(2000)
            thread.deleteLater()
        if not isinstance(image, QImage) or image.isNull():
            self.finished.emit(QPixmap())
            return
        pixmap = QPixmap.fromImage(image)
        pixmap.setDevicePixelRatio(1.0)
        self.finished.emit(pixmap)
