# -*- coding: utf-8 -*-
"""Tomato's diary file: one door for every writer, and the day read back as facts (2026-11-23).

The diary of a day is  <data folder>/Diary/<YYYY-MM-DD> diary.md . Several things write into it at once:
the front-app record (a background thread, every few seconds), finished items, lines sent by other
programs (Broccoli's background vision, the MCP door), a row dragged in from a Collection — and the person,
typing in one of the diary boxes. Before 2026-11-23 a box wrote its whole text over the file at every key,
so a line added behind its back was lost. Ryan 2026-11-23: "多个编辑同时进行，然后它会发生冲突……人工往里面
打字的话也是会和自动的发生冲突的……这是非常重要的".

Rules now:
  * every writer adds its line with append_line() / append_raw(), under LOCK;
  * a box saves with merge_box(): what the box was showing (its base) is compared with the file; whatever
    was added to the file since stays, the person's own changes go in as typed;
  * a box belongs to the day it was loaded for: typing after midnight still goes into that day's file.

Line shapes (all start with "- HH:MM:SS "):
  - 10:54:58 -(Code)- 10:55:03        the front app from … to … (the closing time is added at the next switch)
  - 10:54:58 Completed X scheduled …  a finished item
  - 11:05:00 👁 reading the Qt docs    what Broccoli's background vision saw (VISION_MARK)
  - 12:30:00 [菜谱收集] 咖喱饭          a row of a Collection (dragged in, or sent by a program)
Anything else is the person's own writing.

Plain Python, no Qt (tests: tests_dev/tm_diary_test.py).
"""
import datetime
import difflib
import os
import re
import threading

LOCK = threading.RLock()
VISION_MARK = '👁'
DAY_FORMAT = '%Y-%m-%d'

_STAMP = r'(\d{1,2}:\d{2}(?::\d{2})?)'
_SEGMENT = re.compile(r'^-\s*' + _STAMP + r'\s*-\((.+?)\)')
_LINE = re.compile(r'^-\s*' + _STAMP + r'\s+(.*)$')
_TRAILING_STAMP = re.compile(r'\s*-\s*' + _STAMP + r'\s*$')
_COLLECTION = re.compile(r'^\[(.+?)\]\s*(.+)$')


def day_name(day=None):
    """'2026-11-23' for a date / datetime / None (today) / a text already in that shape."""
    if day is None:
        day = datetime.datetime.now()
    if isinstance(day, str):
        return day[:10]
    return day.strftime(DAY_FORMAT)


def path(folder, day=None):
    return os.path.join(str(folder), day_name(day) + ' diary.md')


def ensure(folder, day=None):
    """The day's file, made with its title line when it is not there yet."""
    target = path(folder, day)
    with LOCK:
        if not os.path.exists(target):
            os.makedirs(str(folder), exist_ok=True)
            with open(target, 'a', encoding='utf-8') as handle:
                handle.write('# ' + day_name(day) + ' diary')
    return target


def read(folder, day=None, create=False):
    target = ensure(folder, day) if create else path(folder, day)
    with LOCK:
        try:
            with open(target, 'r', encoding='utf-8') as handle:
                return handle.read()
        except OSError:
            return ''


def append_raw(folder, text, day=None):
    with LOCK:
        with open(ensure(folder, day), 'a', encoding='utf-8') as handle:
            handle.write(text)


def one_line(text, limit=0):
    """A text as one diary line: line breaks become spaces, cut at `limit` characters with an ellipsis."""
    text = ' '.join(str(text or '').split())
    if limit and len(text) > limit:
        text = text[:max(1, limit - 1)].rstrip() + '…'
    return text


def append_line(folder, text, when=None, limit=0):
    """Adds '- HH:MM:SS text' as a paragraph of its own (to the day of `when`). Returns the line added."""
    when = when or datetime.datetime.now()
    line = '- %s %s' % (when.strftime('%H:%M:%S'), one_line(text, limit))
    append_raw(folder, '\n\n' + line, when)
    return line


def collection_line(collection, name):
    return '[%s] %s' % (one_line(collection), one_line(name))


def merge_box(base, box, current):
    """A diary box saves: `base` = the file as the box loaded it, `box` = what the box holds now, `current` =
    the file now. Returns (text to write, text to add at the end of the box).

    Nothing was written behind the box → the box as it is. Lines were added after what the box knew → they
    stay, after the person's text. The file changed in another way (another box saved) → the lines the file
    gained since `base` are added at the end; nothing the person typed is dropped."""
    if base is None or current == base or current == box:
        return box, ''
    if current.startswith(base):
        extra = current[len(base):]
        return box + extra, extra
    gained = []
    base_lines, current_lines = base.splitlines(), current.splitlines()
    matcher = difflib.SequenceMatcher(None, base_lines, current_lines, autojunk=False)
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag in ('insert', 'replace'):
            gained.extend(current_lines[j1:j2])
    have = set(box.splitlines())
    gained = [line for line in gained if line.strip() and line not in have]
    if not gained:
        return box, ''
    extra = '\n\n' + '\n\n'.join(gained)
    return box + extra, extra


def write(folder, text, day=None):
    with LOCK:
        target = ensure(folder, day)
        with open(target, 'w', encoding='utf-8') as handle:
            handle.write(text)


def _line_key(line):
    line = str(line or '').strip()
    if line.startswith('- '):
        line = line[2:]
    return ' '.join(line.split())


def replace_line(folder, day, line, new=None):
    """The one line of that day that reads `line` (its leading "- " and the spacing aside) becomes `new` (one
    line), or goes when new is None. → ('done', the line as it is now or was) / ('none', '') / ('several', '')."""
    key = _line_key(line)
    if not key or key.startswith('#'):
        return 'none', ''
    with LOCK:
        text = read(folder, day)
        lines = text.split('\n')
        hits = [index for index, existing in enumerate(lines) if _line_key(existing) == key]
        if len(hits) != 1:
            return ('none' if not hits else 'several'), ''
        index = hits[0]
        old = lines[index]
        if new is None:
            del lines[index]
            if 0 < index < len(lines) and not lines[index - 1].strip() and not lines[index].strip():
                del lines[index]                    # the empty line that kept it apart
            result = old.strip()
        else:
            lead = old[:len(old) - len(old.lstrip())] + ('- ' if old.lstrip().startswith('- ') else '')
            lines[index] = lead + _line_key(one_line(new))
            result = lines[index].strip()
        write(folder, '\n'.join(lines), day)
        return 'done', result


def save_box(folder, day, base, box):
    """merge_box() against the file and write, in one step under LOCK. Returns (written text, extra for the box)."""
    with LOCK:
        current = read(folder, day, create=True)
        text, extra = merge_box(base, box, current)
        if text != current:
            write(folder, text, day)
        return text, extra


# ---- the day read back --------------------------------------------------------------------------------------

def _seconds(stamp):
    parts = [int(p) for p in stamp.split(':')]
    while len(parts) < 3:
        parts.append(0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def clock(seconds):
    seconds = max(0, int(seconds))
    return '%02d:%02d' % (seconds // 3600 % 24, seconds % 3600 // 60)


def duration_text(seconds):
    minutes = int(round(seconds / 60.0))
    if minutes < 60:
        return '%d min' % minutes
    return '%d h %02d min' % (minutes // 60, minutes % 60)


def parse(text, end_seconds=None):
    """The diary text as facts:
      segments  [{'start', 'end', 'app'}] seconds of the day; a segment ends where the next begins, the last at
                its own closing time, else at the last time found in the file, else at `end_seconds`
      vision    [{'at', 'text'}]         background-vision lines
      taken     [{'at', 'collection', 'name', 'note'}]   Collection rows
      events    [{'at', 'text'}]         other timed lines (finished items …)
      notes     [text]                   the person's own writing
    """
    segments, vision, taken, events, notes = [], [], [], [], []
    last_stamp = 0
    for raw in (text or '').splitlines():
        line = raw.strip()
        if not line or line.startswith('# '):
            continue
        for stamp in re.findall(_STAMP, line) if line.startswith('-') else ():
            last_stamp = max(last_stamp, _seconds(stamp))
        found = _SEGMENT.match(line)
        if found:
            closing = _TRAILING_STAMP.search(line[found.end():])
            segments.append({'start': _seconds(found.group(1)), 'app': found.group(2).strip(),
                             'end': _seconds(closing.group(1)) if closing else None})
            rest = line[found.end():]
            rest = _TRAILING_STAMP.sub('', rest).strip() if closing else rest.strip()
            if rest:
                notes.append(rest)                 # typed at the end of an app line
            continue
        found = _LINE.match(line)
        if not found:
            notes.append(line[1:].strip() if line.startswith('- ') else line)
            continue
        at, body = _seconds(found.group(1)), _TRAILING_STAMP.sub('', found.group(2)).strip()
        if not body:
            continue                                # "- 10:55:03 " = only the closing time of an app line
        if body.startswith(VISION_MARK):
            vision.append({'at': at, 'text': body[len(VISION_MARK):].strip()})
            continue
        row = _COLLECTION.match(body)
        if row:
            name, _dash, note = row.group(2).partition(' — ')
            taken.append({'at': at, 'collection': row.group(1).strip(), 'name': name.strip(), 'note': note.strip()})
            continue
        events.append({'at': at, 'text': body})
    segments.sort(key=lambda s: s['start'])
    for index, segment in enumerate(segments):
        following = segments[index + 1]['start'] if index + 1 < len(segments) else None
        if following is not None:
            # the next app began: that is the end, whatever closing time the line carries (a pause in the
            # record — Mac asleep — shows as a closing time earlier than the next start, and is kept)
            end = segment['end'] if segment['end'] is not None and segment['end'] <= following else following
        else:
            end = segment['end']
            if end is None:
                end = max(last_stamp, segment['start']) if end_seconds is None else max(end_seconds, segment['start'])
        segment['end'] = max(end, segment['start'])
    return {'segments': segments, 'vision': vision, 'taken': taken, 'events': events, 'notes': notes}


def app_totals(segments):
    """[(app, seconds)] longest first."""
    totals = {}
    for segment in segments:
        totals[segment['app']] = totals.get(segment['app'], 0) + segment['end'] - segment['start']
    return sorted(totals.items(), key=lambda pair: (-pair[1], pair[0]))


def blocks(segments, anchor_seconds=120, gap_seconds=600):
    """The 5-second flicker between apps as stretches of the day: [{'start', 'end', 'app', 'others': [app]}].
    A stretch is named after the app that held most of it; a stay of `anchor_seconds` or more in another app
    begins a new stretch; shorter visits are counted into the stretch they fall in ('others': those that took
    a tenth of it or more, at most two). A hole of `gap_seconds` in the record (asleep, away) ends a stretch."""
    result, current = [], None

    def close():
        nonlocal current
        if current is None:
            return
        share = sorted(current.pop('share').items(), key=lambda pair: -pair[1])
        total = sum(seconds for _app, seconds in share) or 1
        current['app'] = share[0][0]
        current['others'] = [app for app, seconds in share[1:3] if seconds * 10 >= total]
        result.append(current)
        current = None

    for segment in segments:
        length = segment['end'] - segment['start']
        if current is not None and segment['start'] - current['end'] >= gap_seconds:
            close()
        if current is not None and length >= anchor_seconds and segment['app'] != current['lead']:
            close()
        if current is None:
            current = {'start': segment['start'], 'end': segment['end'], 'lead': segment['app'], 'share': {}}
        if length >= anchor_seconds:
            current['lead'] = segment['app']
        current['share'][segment['app']] = current['share'].get(segment['app'], 0) + length
        current['end'] = max(current['end'], segment['end'])
    close()
    for index in range(len(result) - 1, -1, -1):        # a stretch shorter than a stay joins the one after it
        block = result[index]                           # (or before it): the 5 seconds in Tomato before a morning in Code
        if block['end'] - block['start'] >= anchor_seconds or len(result) == 1:
            continue
        after = result[index + 1] if index + 1 < len(result) else None
        before = result[index - 1] if index > 0 else None
        if after is not None and after['start'] - block['end'] < gap_seconds:
            after['start'] = block['start']
        elif before is not None and block['start'] - before['end'] < gap_seconds:
            before['end'] = block['end']
        else:
            continue
        del result[index]
    merged = []
    for block in result:
        block.pop('lead', None)
        previous = merged[-1] if merged else None
        if previous and previous['app'] == block['app'] and block['start'] - previous['end'] < gap_seconds:
            previous['end'] = block['end']
            previous['others'] = (previous['others'] + [a for a in block['others'] if a not in previous['others']])[:2]
        else:
            merged.append(block)
    return merged


def digest(text, end_seconds=None, max_chars=6000):
    """The day in a few thousand characters, for a reader that should not get the raw 5-second record: time per
    app, the stretches, what was seen, what was taken from the Collections, finished items, own notes."""
    facts = parse(text, end_seconds)
    lines = []
    totals = app_totals(facts['segments'])
    if totals:
        lines.append('## Time per app')
        lines.extend('- %s: %s' % (app, duration_text(seconds)) for app, seconds in totals[:15] if seconds >= 60)
    stretches = blocks(facts['segments'])
    if stretches:
        lines.append('\n## Timeline')
        for block in stretches:
            if block['end'] - block['start'] < 60:
                continue
            also = ' (also %s)' % ', '.join(block['others']) if block['others'] else ''
            lines.append('- %s–%s %s%s' % (clock(block['start']), clock(block['end']), block['app'], also))
    for title, key, shape in (
            ('Seen on screen', 'vision', lambda v: '- %s %s' % (clock(v['at']), v['text'])),
            ('From the Collections', 'taken', lambda t: '- %s [%s] %s%s' % (
                clock(t['at']), t['collection'], t['name'], (' — ' + t['note']) if t['note'] else '')),
            ('Items', 'events', lambda e: '- %s %s' % (clock(e['at']), e['text']))):
        if facts[key]:
            lines.append('\n## ' + title)
            lines.extend(shape(entry) for entry in facts[key])
    if facts['notes']:
        lines.append('\n## Own notes')
        lines.extend('- ' + note for note in facts['notes'])
    result = '\n'.join(lines).strip()
    if max_chars and len(result) > max_chars:
        result = result[:max_chars].rstrip() + '\n…'
    return result
