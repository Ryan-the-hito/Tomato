# -*- coding: utf-8 -*-
"""What an assistant app noticed, read into Tomato's diary (2026-11-23).

Ryan 2026-11-23: Tomato "知道最顶上的 app 是什么，但是他却不知道现在正在发生什么事情……把 background vision 他的这些
东西也写一份记录，写到我们这个 Tomato 的那个日志里面……简短一点"; how often: "多久有一次视觉，那就是多久记一次".

Broccoli keeps an activity feed in its data folder:  ActivityFeed/<YYYY-MM-DD>.jsonl , one json line per entry
{"at": local ISO time, "kind": "vision", "text": one sentence}. Tomato is told by the system when the file grows
(a file watcher — nothing looks at the clock), reads the new lines and hands them over; where it stopped is
remembered ({'day', 'offset'}) so nothing is taken twice, also over a restart. The first time, it starts at the
end of today's file: what was noticed before Tomato cared is not poured into the diary.

read_new() is plain Python (tests: tests_dev/tm_feed_test.py); FeedWatcher needs Qt.
"""
import datetime
import json
import os

FOLDER = 'ActivityFeed'
MAX_LINE_BYTES = 8000


def feed_dir(data_dir):
    return os.path.join(data_dir, FOLDER)


def _day_path(folder, day):
    return os.path.join(folder, day + '.jsonl')


def _read_from(path, offset):
    """(entries, new offset): the complete lines after `offset`. A file that got shorter is read from its start."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return [], offset
    if offset > size:
        offset = 0
    entries = []
    with open(path, 'rb') as handle:
        handle.seek(offset)
        while True:
            line = handle.readline(MAX_LINE_BYTES + 1)
            if not line.endswith(b'\n'):
                break                              # the writer is in the middle of this line (or it is absurdly long)
            offset += len(line)
            try:
                entry = json.loads(line.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(entry, dict) and str(entry.get('text', '') or '').strip():
                entries.append({'at': str(entry.get('at', '') or ''), 'kind': str(entry.get('kind', '') or ''),
                                'text': ' '.join(str(entry['text']).split())})
    return entries, offset


def read_new(folder, state, today=None):
    """(new entries in order, the state to remember). `state` None = first time: nothing is taken, the state
    points at the end of today's file."""
    today = today or datetime.date.today().isoformat()
    if not isinstance(state, dict) or not state.get('day'):
        try:
            size = os.path.getsize(_day_path(folder, today))
        except OSError:
            size = 0
        return [], {'day': today, 'offset': size}
    day, offset = str(state['day']), int(state.get('offset') or 0)
    entries = []
    if day < today:                                # the day turned: the rest of the old file, then the new one
        found, _offset = _read_from(_day_path(folder, day), offset)
        entries += found
        day, offset = today, 0
    found, offset = _read_from(_day_path(folder, day), offset)
    return entries + found, {'day': day, 'offset': offset}


def entry_time(entry):
    try:
        return datetime.datetime.fromisoformat(entry['at'])
    except (ValueError, KeyError, TypeError):
        return datetime.datetime.now()


def make_watcher(data_dir, load_state, save_state, deliver, parent=None):
    from PyQt6.QtCore import QObject, QFileSystemWatcher

    class FeedWatcher(QObject):
        """Calls deliver(entries) on the main thread when the feed grew. The folder (and, before it exists, the
        data folder it will appear in) is watched for the new day's file, the day's file for new lines."""

        def __init__(self):
            super().__init__(parent)
            self.folder = feed_dir(data_dir)
            self._watcher = QFileSystemWatcher(self)
            self._watcher.directoryChanged.connect(self.look)
            self._watcher.fileChanged.connect(self.look)
            self.look()

        def _watch(self):
            wanted = []
            if os.path.isdir(self.folder):
                wanted.append(self.folder)
                today = _day_path(self.folder, datetime.date.today().isoformat())
                if os.path.exists(today):
                    wanted.append(today)
            elif os.path.isdir(data_dir):
                wanted.append(data_dir)
            have = set(self._watcher.directories()) | set(self._watcher.files())
            gone = [path for path in have if path not in wanted]
            if gone:
                self._watcher.removePaths(gone)
            new = [path for path in wanted if path not in have]
            if new:
                self._watcher.addPaths(new)

        def look(self, *_args):
            try:
                entries, state = read_new(self.folder, load_state())
                save_state(state)
                self._watch()
                if entries:
                    deliver(entries)
            except Exception:
                import logging
                logging.exception('The activity feed could not be read.')

    return FeedWatcher()
