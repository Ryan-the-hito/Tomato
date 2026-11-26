# -*- coding: utf-8 -*-
"""Tomato's show / hide shortcut as a system-wide hot key (2026-11-22).

Ryan 2026-11-22: "像 Broccoli 它能换出……然后再隐藏……给 Tomato 也加一个快捷键"; asked, he chose the
system's own hot-key registration (Carbon RegisterEventHotKey): no "Input Monitoring" permission is
needed, so a packaged Tomato never asks for one. The price: only "modifiers + one key" shortcuts — no
Broccoli-style double tap of a modifier, no left / right modifier.

Shortcuts are written the Broccoli way, '<ctrl>+<alt>+t', and shown the Mac way, ⌃⌥T (style book 5.3.3).
The key is found by its place on the keyboard (macOS virtual key code, the US layout's names), the same
place whatever the layout — which is also what the recording dialog reads from the key press.
"""
import ctypes
import ctypes.util
import logging

# modifiers: text name → (Carbon flag, Mac symbol); in the system's order ⌃ ⌥ ⇧ ⌘
MODIFIERS = (
    ('ctrl', 1 << 12, '⌃'),
    ('alt', 1 << 11, '⌥'),
    ('shift', 1 << 9, '⇧'),
    ('cmd', 1 << 8, '⌘'),
)
_MODIFIER_ALIASES = {'ctrl': 'ctrl', 'control': 'ctrl', 'alt': 'alt', 'option': 'alt', 'opt': 'alt',
                     'shift': 'shift', 'cmd': 'cmd', 'command': 'cmd', 'meta': 'cmd', 'super': 'cmd'}

# macOS virtual key codes (Events.h, kVK_*): name in the shortcut text → (code, shown as)
KEYS = {
    'a': (0x00, 'A'), 's': (0x01, 'S'), 'd': (0x02, 'D'), 'f': (0x03, 'F'), 'h': (0x04, 'H'), 'g': (0x05, 'G'),
    'z': (0x06, 'Z'), 'x': (0x07, 'X'), 'c': (0x08, 'C'), 'v': (0x09, 'V'), 'b': (0x0B, 'B'), 'q': (0x0C, 'Q'),
    'w': (0x0D, 'W'), 'e': (0x0E, 'E'), 'r': (0x0F, 'R'), 'y': (0x10, 'Y'), 't': (0x11, 'T'), '1': (0x12, '1'),
    '2': (0x13, '2'), '3': (0x14, '3'), '4': (0x15, '4'), '6': (0x16, '6'), '5': (0x17, '5'), '=': (0x18, '='),
    '9': (0x19, '9'), '7': (0x1A, '7'), '-': (0x1B, '-'), '8': (0x1C, '8'), '0': (0x1D, '0'), ']': (0x1E, ']'),
    'o': (0x1F, 'O'), 'u': (0x20, 'U'), '[': (0x21, '['), 'i': (0x22, 'I'), 'p': (0x23, 'P'), 'l': (0x25, 'L'),
    'j': (0x26, 'J'), "'": (0x27, "'"), 'k': (0x28, 'K'), ';': (0x29, ';'), '\\': (0x2A, '\\'), ',': (0x2B, ','),
    '/': (0x2C, '/'), 'n': (0x2D, 'N'), 'm': (0x2E, 'M'), '.': (0x2F, '.'), '`': (0x32, '`'),
    'enter': (0x24, '↩'), 'tab': (0x30, '⇥'), 'space': (0x31, 'Space'), 'backspace': (0x33, '⌫'),
    'esc': (0x35, '⎋'), 'left': (0x7B, '←'), 'right': (0x7C, '→'), 'down': (0x7D, '↓'), 'up': (0x7E, '↑'),
    'f1': (0x7A, 'F1'), 'f2': (0x78, 'F2'), 'f3': (0x63, 'F3'), 'f4': (0x76, 'F4'), 'f5': (0x60, 'F5'),
    'f6': (0x61, 'F6'), 'f7': (0x62, 'F7'), 'f8': (0x64, 'F8'), 'f9': (0x65, 'F9'), 'f10': (0x6D, 'F10'),
    'f11': (0x67, 'F11'), 'f12': (0x6F, 'F12'),
}
_KEY_ALIASES = {'return': 'enter', 'escape': 'esc', 'delete': 'backspace'}
_NAME_OF_CODE = {code: name for name, (code, _shown) in KEYS.items()}

DEFAULT_SHORTCUT = '<ctrl>+<alt>+t'


def parse(text):
    """'<ctrl>+<alt>+t' → (set of modifier names, key name) or None. An empty text is None too."""
    text = (text or '').strip().lower()
    if not text:
        return None
    modifiers, key = set(), None
    for part in text.replace(' ', '').split('+'):
        if not part:
            continue
        bare = part.strip('<>')
        if bare in _MODIFIER_ALIASES:
            modifiers.add(_MODIFIER_ALIASES[bare])
            continue
        bare = _KEY_ALIASES.get(bare, bare)
        if bare not in KEYS or key is not None:
            return None
        key = bare
    if key is None:
        return None
    return modifiers, key


def compose(modifiers, key):
    """The shortcut text for a set of modifier names and a key name ('<ctrl>+<alt>+t')."""
    parts = ['<%s>' % name for name, _flag, _symbol in MODIFIERS if name in modifiers]
    return '+'.join(parts + [key])


def normalize(text):
    parsed = parse(text)
    return compose(*parsed) if parsed else ''


def usable(text):
    """A shortcut Tomato can take: a known key with at least one of ⌃ ⌥ ⌘ (⇧ alone would be typing)."""
    parsed = parse(text)
    return bool(parsed) and bool(parsed[0] & {'ctrl', 'alt', 'cmd'})


def display(text):
    """The Mac way of writing it (style book 5.3.3): ⌃⌥T; '' when there is none."""
    parsed = parse(text)
    if not parsed:
        return ''
    modifiers, key = parsed
    return ''.join(symbol for name, _flag, symbol in MODIFIERS if name in modifiers) + KEYS[key][1]


def from_key_press(virtual_key, ctrl, alt, shift, cmd):
    """The shortcut text for a key press (macOS virtual key code + modifiers); '' for a key not in KEYS."""
    name = _NAME_OF_CODE.get(int(virtual_key))
    if name is None:
        return ''
    modifiers = {n for n, on in (('ctrl', ctrl), ('alt', alt), ('shift', shift), ('cmd', cmd)) if on}
    return compose(modifiers, name)


def _fourcc(text):
    return int.from_bytes(text.encode('ascii'), 'big')


class _EventHotKeyID(ctypes.Structure):
    _fields_ = [('signature', ctypes.c_uint32), ('id', ctypes.c_uint32)]


class _EventTypeSpec(ctypes.Structure):
    _fields_ = [('eventClass', ctypes.c_uint32), ('eventKind', ctypes.c_uint32)]


_HANDLER_PROC = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
_SIGNATURE = _fourcc('TMTO')
_K_EVENT_CLASS_KEYBOARD = _fourcc('keyb')
_K_EVENT_HOT_KEY_PRESSED = 5
_K_EVENT_PARAM_DIRECT_OBJECT = _fourcc('----')
_TYPE_EVENT_HOT_KEY_ID = _fourcc('hkid')


class GlobalHotKey:
    """One system-wide hot key; `callback()` runs on the main thread (the system delivers the press
    through the app's own event loop). set_shortcut('') removes it."""

    def __init__(self, callback):
        self._callback = callback
        self._carbon = None
        self._handler_installed = False
        self._ref = ctypes.c_void_p()
        self._registered = False
        self.shortcut = ''
        try:
            path = ctypes.util.find_library('Carbon') or '/System/Library/Frameworks/Carbon.framework/Carbon'
            self._carbon = ctypes.CDLL(path)
            c = self._carbon
            c.GetApplicationEventTarget.restype = ctypes.c_void_p
            c.InstallEventHandler.argtypes = [ctypes.c_void_p, _HANDLER_PROC, ctypes.c_uint32,
                                              ctypes.POINTER(_EventTypeSpec), ctypes.c_void_p, ctypes.c_void_p]
            c.InstallEventHandler.restype = ctypes.c_int32
            c.RegisterEventHotKey.argtypes = [ctypes.c_uint32, ctypes.c_uint32, _EventHotKeyID, ctypes.c_void_p,
                                              ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)]
            c.RegisterEventHotKey.restype = ctypes.c_int32
            c.UnregisterEventHotKey.argtypes = [ctypes.c_void_p]
            c.UnregisterEventHotKey.restype = ctypes.c_int32
            c.GetEventParameter.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                                            ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p]
            c.GetEventParameter.restype = ctypes.c_int32
        except Exception:
            logging.exception('Show/hide shortcut: the system hot-key interface is not available.')
            self._carbon = None
        self._proc = _HANDLER_PROC(self._on_event)     # kept: the system holds only the pointer

    @property
    def available(self):
        return self._carbon is not None

    @property
    def registered(self):
        return self._registered

    def _install_handler(self):
        if self._handler_installed or self._carbon is None:
            return self._handler_installed
        spec = _EventTypeSpec(_K_EVENT_CLASS_KEYBOARD, _K_EVENT_HOT_KEY_PRESSED)
        status = self._carbon.InstallEventHandler(self._carbon.GetApplicationEventTarget(), self._proc, 1,
                                                  ctypes.byref(spec), None, None)
        self._handler_installed = status == 0
        if status != 0:
            logging.warning('Show/hide shortcut: installing the hot-key handler failed (%s).', status)
        return self._handler_installed

    def _on_event(self, _call_ref, event, _user_data):
        try:
            hot_key = _EventHotKeyID()
            status = self._carbon.GetEventParameter(event, _K_EVENT_PARAM_DIRECT_OBJECT, _TYPE_EVENT_HOT_KEY_ID, None,
                                                    ctypes.sizeof(hot_key), None, ctypes.byref(hot_key))
            if status == 0 and hot_key.signature == _SIGNATURE and self._registered:
                self._callback()
        except Exception:
            logging.exception('Show/hide shortcut: the hot key could not be handled.')
        return 0

    def unregister(self):
        if self._registered and self._carbon is not None:
            self._carbon.UnregisterEventHotKey(self._ref)
        self._registered = False
        self._ref = ctypes.c_void_p()

    def set_shortcut(self, text):
        """Registers `text` (replacing the one before). True when it is registered, or when `text` is empty."""
        self.unregister()
        self.shortcut = normalize(text)
        if not self.shortcut:
            return True
        if self._carbon is None or not self._install_handler():
            return False
        modifiers, key = parse(self.shortcut)
        flags = 0
        for name, flag, _symbol in MODIFIERS:
            if name in modifiers:
                flags |= flag
        status = self._carbon.RegisterEventHotKey(KEYS[key][0], flags, _EventHotKeyID(_SIGNATURE, 1),
                                                  self._carbon.GetApplicationEventTarget(), 0, ctypes.byref(self._ref))
        self._registered = status == 0
        if status != 0:
            logging.warning('Show/hide shortcut %s could not be registered (%s).', self.shortcut, status)
        return self._registered
