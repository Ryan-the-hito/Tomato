"""Tomato ⇄ Reminders ⇄ Calendar: one joint decision per sync pass.

Before (two separate polls, each comparing only itself with the table and remembering nothing):
a reminder moved in Reminders and its event moved in Calendar inside the same two minutes left two
events of one name, and the table then followed one of them on every poll, back and forth, for ever;
a row whose reminder / event had simply not been made yet was taken for "deleted over there"; DONE rows
(whose event lives in "Tomato-old") were deleted by the Calendar poll.

Now: the Reminders list and the Calendar are read back to back by one thread, and `reconcile` looks at
all three sides at once, with what was seen last time (the base, kept in sync_base.json):

- the same reminder / event (by its system identifier) under another name or time = moved: the row keeps
  its other columns and the other side follows; moved on both sides to different places = the Calendar wins
  and the reminder follows (one answer, so nothing flips back);
- on one side only and never seen there before = new: the row and the missing counterpart are made;
- seen there last time and gone now = deleted over there: the row and the counterpart go;
- in the table but never seen over there = not made yet (or the making failed): it is made again (three
  tries), the row is not deleted;
- ticked off in Reminders = the row is completed; the tick taken off again there = the row is open again;
- a pass that would delete most of the table (a list that cannot be read, a renamed calendar) does nothing.

Pure functions: no Qt, no system calls (tests_dev/tm_sync_test.py)."""
import json
import re
import time

MAKE_TRIES = 3            # a counterpart that never shows up is made this many times, then left alone
MASS_DELETE_MIN = 5       # a pass deleting at least this many rows and more than half of them is refused

CALENDAR_SNAPSHOT_JXA = r'''
function run() {
	var result = {status: "ok", data: []};
	try {
		var app = Application("Calendar");
		var cals = app.calendars.whose({name: "Tomato"});
		if (cals.length === 0) {
			result.status = "missing";
			return JSON.stringify(result);
		}
		var ev = cals[0].events;
		// one question per column for the whole calendar (asking event by event took 4 questions per event)
		var starts = ev.startDate(), ends = ev.endDate(), names = ev.summary(), ids = ev.uid();
		if (ends.length !== starts.length || names.length !== starts.length || ids.length !== starts.length) {
			result.status = "changed";
			return JSON.stringify(result);
		}
		for (var i = 0; i < starts.length; i++) {
			if (!starts[i]) { continue; }
			var duration = ends[i] ? Math.floor((ends[i].getTime() - starts[i].getTime()) / 1000) : 0;
			result.data.push({id: ids[i] || "", name: names[i] || "", stamp: Math.floor(starts[i].getTime() / 1000), duration: duration});
		}
	} catch (err) {
		result.status = "error";
		result.message = err.toString();
	}
	return JSON.stringify(result);
}
'''


def parse_calendar_snapshot(output):
    """The JXA answer -> list of entries, or None when the calendar could not be read as a whole."""
    try:
        payload = json.loads(output or '')
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict) or payload.get('status') != 'ok':
        return None
    data = payload.get('data')
    return data if isinstance(data, list) else None


def normalize_stamp(value):
    if value in (None, ''):
        return ''
    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return ''


def snapshot_map(entries):
    """[{name, stamp, id, …}] -> {(name, stamp): entry}; None stays None (that side could not be read)."""
    if entries is None:
        return None
    result = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = (entry.get('name') or '').strip()
        stamp = normalize_stamp(entry.get('stamp'))
        if name and stamp:
            result.setdefault((name, stamp), entry)
    return result


def load_base(path):
    try:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_base(path, base):
    try:
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(base, handle, ensure_ascii=False)
    except OSError:
        pass


def _key(value):
    return (value[0], value[1]) if isinstance(value, (list, tuple)) and len(value) == 2 else None


def _moves(snapshot, base_ids, rows):
    """{old key: new key} for the items of one side that changed name / time since last time, where the
    table still has the row under the old key."""
    moves = {}
    if not snapshot:
        return moves
    for key, entry in snapshot.items():
        old = _key(base_ids.get(entry.get('id') or ''))
        if old is None or old == key:
            continue
        if old in rows and key not in rows and old not in snapshot and old not in moves:
            moves[old] = key
    return moves


def reconcile(local, reminders, calendar, base, window=None, event_window=None):
    """local: {(name, stamp): 'UNDONE' | 'DONE'} (the TIME_SNS rows); reminders: {(name, stamp): {'id',
    'completed'}}; calendar: {(name, stamp): {'id', 'duration'}} or None (not readable this time: nothing
    is decided about events); base: what load_base gave; window: (lowest, highest) stamp the Reminders
    read covers, or None; event_window: the same for the Calendar read (None: all of the calendar was read).

    Returns (actions, new_base). Actions, to apply in order:
      ('move_row', old, new, duration | None)   ('add_row', key, duration | None)   ('delete_row', key)
      ('complete_row', key)
      ('reopen_row', key, make_event)           the tick was taken off again in Reminders: the row is UNDONE
                                                again; make_event: its event is to be put back in "Tomato"
      ('make_reminder', key)  ('delete_reminder', key)  ('move_reminder', old, new)
      ('make_event', key)     ('delete_event', key)     ('move_event', old, new)
    actions is None when the pass was refused (mass deletion)."""
    base = base if isinstance(base, dict) else {}
    rows = dict(local)
    rem = dict(reminders or {})
    cal = dict(calendar) if calendar is not None else None
    base_r = base.get('r') if isinstance(base.get('r'), dict) else {}
    base_c = base.get('c') if isinstance(base.get('c'), dict) else {}
    seen_r = {k for k in map(_key, base.get('rk') or []) if k}
    seen_c = {k for k in map(_key, base.get('ck') or []) if k}
    tries = dict(base.get('tries') or {}) if isinstance(base.get('tries'), dict) else {}
    ticked = set(base.get('rd') or []) if isinstance(base.get('rd'), list) else set()
    actions = []
    touched = set()
    in_r = set(rem)                                   # where the reminders will be once the actions ran
    in_c = set(cal) if cal is not None else None      # … and the events
    new_base_r = {entry.get('id'): list(key) for key, entry in rem.items() if entry.get('id')}

    def in_window(key):
        if window is None:
            return True
        try:
            return window[0] <= int(key[1]) <= window[1]
        except (ValueError, TypeError):
            return False

    def in_event_window(key):
        if event_window is None:
            return True
        try:
            return event_window[0] <= int(key[1]) <= event_window[1]
        except (ValueError, TypeError):
            return False

    # 1 moved: the same reminder / event under another name or time
    r_moves = _moves(rem, base_r, rows)
    c_moves = _moves(cal, base_c, rows)
    if cal is not None:
        # an event the base does not know by identifier (first pass, or made by hand): the old rule —
        # a name only one row carries, whose own event is gone
        by_name = {}
        for key in rows:
            by_name.setdefault(key[0], []).append(key)
        for key in cal:
            if key in rows or key in rem or key in c_moves.values():
                continue
            same = by_name.get(key[0], [])
            if len(same) == 1 and same[0] not in cal and same[0] not in c_moves and rows[same[0]] == 'UNDONE':
                c_moves[same[0]] = key
    for old in list(dict.fromkeys(list(c_moves) + list(r_moves))):
        if old not in rows:
            continue
        to_c, to_r = c_moves.get(old), r_moves.get(old)
        done = rows[old] == 'DONE'
        if to_c is not None and to_c not in rows:
            new = to_c
            actions.append(('move_row', old, new, (cal[new].get('duration') or None)))
            where = to_r if to_r is not None else (old if old in in_r else None)
            if where is not None and where != new:
                if new in in_r:
                    actions.append(('delete_reminder', where))
                else:
                    actions.append(('move_reminder', where, new))
                    moved_id = (rem.get(where) or {}).get('id')
                    if moved_id:
                        new_base_r[moved_id] = list(new)
                    in_r.add(new)
                in_r.discard(where)
            elif where is None and new not in in_r and in_window(new) and not done:
                actions.append(('make_reminder', new))
                in_r.add(new)
        elif to_r is not None and to_r not in rows:
            new = to_r
            actions.append(('move_row', old, new, None))
            if in_c is not None and not done:
                if old in in_c:
                    if new in in_c:
                        actions.append(('delete_event', old))
                    else:
                        actions.append(('move_event', old, new))
                        in_c.add(new)
                    in_c.discard(old)
                elif new not in in_c and in_event_window(new):
                    actions.append(('make_event', new))
                    in_c.add(new)
        else:
            continue
        rows[new] = rows.pop(old)
        touched.add(new)

    # 2 ticked off in Reminders
    for key, entry in rem.items():
        if entry.get('completed') and rows.get(key) == 'UNDONE':
            actions.append(('complete_row', key))     # moves its event to "Tomato-old" itself
            rows[key] = 'DONE'
            touched.add(key)
            if in_c is not None:
                in_c.discard(key)

    # 2b the tick taken off again in Reminders (a reminder seen ticked last time): the row is open again.
    # A row Tomato ticked whose reminder never got its tick is not this — that one was never seen ticked.
    for key, entry in rem.items():
        if not entry.get('completed') and rows.get(key) == 'DONE' and entry.get('id') and entry.get('id') in ticked:
            make_event = in_c is not None and key not in in_c and in_event_window(key)
            actions.append(('reopen_row', key, make_event))
            rows[key] = 'UNDONE'
            touched.add(key)
            if make_event:
                in_c.add(key)

    # 3 new over there
    for key, entry in rem.items():
        if key in rows or key not in in_r:
            continue
        actions.append(('add_row', key, None))
        rows[key] = 'UNDONE'
        touched.add(key)
        if in_c is not None and key not in in_c and not entry.get('completed') and in_event_window(key):
            actions.append(('make_event', key))
            in_c.add(key)
    if cal is not None:
        for key, entry in cal.items():
            if key in rows or key not in in_c:
                continue
            actions.append(('add_row', key, (entry.get('duration') or None)))
            rows[key] = 'UNDONE'
            touched.add(key)
            if key not in in_r and in_window(key):
                actions.append(('make_reminder', key))
                in_r.add(key)

    # 4 gone over there, or never made
    deletions = []
    for key, status in list(rows.items()):
        if key in touched or status != 'UNDONE':
            continue        # DONE: the reminder is ticked, the event lives in "Tomato-old"
        r_missing = key not in in_r and in_window(key)
        c_missing = in_c is not None and key not in in_c and in_event_window(key)
        if (r_missing and key in seen_r) or (c_missing and key in seen_c):
            deletions.append(key)
            continue
        for side, missing, make in (('r', r_missing, 'make_reminder'), ('c', c_missing, 'make_event')):
            mark = '%s|%s|%s' % (side, key[0], key[1])
            if not missing:
                tries.pop(mark, None)
                continue
            if int(tries.get(mark, 0)) >= MAKE_TRIES:
                continue
            tries[mark] = int(tries.get(mark, 0)) + 1
            actions.append((make, key))
            (in_r if side == 'r' else in_c).add(key)
    undone = sum(1 for status in local.values() if status == 'UNDONE')
    if len(deletions) >= MASS_DELETE_MIN and len(deletions) * 2 > undone:
        return None, base
    for key in deletions:
        actions.append(('delete_row', key))
        if key in in_r:
            actions.append(('delete_reminder', key))
            in_r.discard(key)
        if in_c is not None and key in in_c:
            actions.append(('delete_event', key))
            in_c.discard(key)
        rows.pop(key, None)

    # what was really seen this time (not what the actions are expected to produce: a making that failed
    # must look "never made" next time, not "deleted over there")
    alive = {'%s|%s|%s' % (side, key[0], key[1]) for side in ('r', 'c') for key in rows}
    new_base = {
        'r': new_base_r,
        'rk': [list(key) for key in rem if key in in_r],
        'rd': [entry.get('id') for entry in rem.values() if entry.get('completed') and entry.get('id')],
        'c': ({entry.get('id'): list(key) for key, entry in cal.items() if entry.get('id') and key in in_c}
              if cal is not None else base_c),
        'ck': ([list(key) for key in cal if key in in_c] if cal is not None else [list(k) for k in seen_c]),
        'tries': {mark: count for mark, count in tries.items() if mark in alive},
    }
    return actions, new_base


# ---------------------------------------------------------------------------------------------------------
# Tomato's own commands for Reminders / Calendar, read back as plain operations
#
# Every change Tomato makes over there is written as an AppleScript text (about forty places in the main
# file). Sending those texts through `osascript` is the slow part of every "Syncing…". `parse_script` reads
# such a text back into what it asks for, so the same request can go straight to the system interface
# (tomato_eventkit). A text it does not recognise completely gives None and is sent as AppleScript, as before.
#
#   ('make_reminder', name, stamp, notes | None)     ('delete_reminder', name, stamp)
#   ('complete_reminder', name, stamp)               ('move_reminder', name, old stamp, new stamp)
#   ('purge_completed_reminders',)
#   ('make_event', calendar, name, stamp, seconds)   ('delete_event', calendar, name, stamp)

REMINDER_LIST = 'Tomato'
_ESCAPES = {'n': '\n', 't': '\t', 'r': '\r'}
_S = r'(«\d+»|[A-Za-z_]\w*)'       # a text: written out, or the name of a variable holding one
_NUM = r'(-?\d+(?:\.\d+)?)'
_PATTERNS = [(kind, re.compile(pattern + r'\Z')) for kind, pattern in (
    ('app', r'tell application «(\d+)»'),
    ('list', r'set ([A-Za-z_]\w*) to list «(\d+)»'),
    ('var', r'set ([A-Za-z_]\w*) to «(\d+)»'),
    ('calendar', r'tell calendar «(\d+)»'),
    ('end', r'end tell'),
    ('make_reminder', r'make new reminder at end with properties \{name:%s, remind me date:date %s(?:, body:%s)?\}' % (_S, _S, _S)),
    ('delete_reminder', r'delete \(reminders whose \(name is %s\) and \(remind me date is date %s\)\)' % (_S, _S)),
    ('complete_reminder', r'set completed of \(reminders whose \(name is %s\) and \(remind me date is date %s\)\) to true' % (_S, _S)),
    ('move_reminder', r'set remind me date of \(reminders whose \(name is %s\) and \(remind me date is date %s\)\) to date %s' % (_S, _S, _S)),
    ('purge', r'delete \(reminders in ([A-Za-z_]\w*)\) whose completed is true'),
    ('make_event', r'make new event at end with properties \{summary:%s, start date:date %s, end date:date %s \+ \(%s \* hours\)\}' % (_S, _S, _S, _NUM)),
    ('delete_event', r'delete \(events whose \(start date is date %s\) and \(summary is %s\)\)' % (_S, _S)),
    ('tell', r'tell ([A-Za-z_]\w*)'),
)]


def _split_literals(text):
    """The script with every "…" replaced by «n», and the texts themselves; None when a quote never closes."""
    out, literals, i = [], [], 0
    while i < len(text):
        char = text[i]
        if char == '«' or char == '»':
            return None, None
        if char != '"':
            out.append(char)
            i += 1
            continue
        i += 1
        piece = []
        while True:
            if i >= len(text):
                return None, None
            char = text[i]
            if char == '\\' and i + 1 < len(text):
                piece.append(_ESCAPES.get(text[i + 1], text[i + 1]))
                i += 2
            elif char == '"':
                i += 1
                break
            else:
                piece.append(char)
                i += 1
        out.append('«%d»' % len(literals))
        literals.append(''.join(piece))
    return ''.join(out), literals


def _script_stamp(text):
    try:
        return int(time.mktime(time.strptime(text.strip(), '%m/%d/%Y %H:%M')))
    except (ValueError, OverflowError, AttributeError):
        return None


def parse_script(script):
    """One AppleScript text of Tomato's -> list of operations, or None when any line of it is not one of
    the known forms (then nothing of it is taken over: it runs as AppleScript)."""
    skeleton, literals = _split_literals(script or '')
    if skeleton is None:
        return None
    app = None
    variables, lists = {}, {}
    scope = []          # what each open "tell" is: 'app', ('list', name), ('calendar', name)
    ops = []

    def text_of(token):
        if token is None:
            return None
        if token.startswith('«'):
            return literals[int(token[1:-1])]
        return variables.get(token)

    for raw in skeleton.splitlines():
        line = ' '.join(raw.split())
        if not line:
            continue
        for kind, pattern in _PATTERNS:
            match = pattern.match(line)
            if match:
                break
        else:
            return None
        groups = match.groups()
        target = scope[-1] if scope else None
        if kind == 'app':
            if scope or literals[int(groups[0])] not in ('Reminders', 'Calendar'):
                return None
            app = literals[int(groups[0])]
            scope.append('app')
        elif kind == 'list':
            lists[groups[0]] = literals[int(groups[1])]
        elif kind == 'var':
            variables[groups[0]] = literals[int(groups[1])]
        elif kind == 'calendar':
            if app != 'Calendar':
                return None
            scope.append(('calendar', literals[int(groups[0])]))
        elif kind == 'tell':
            if app != 'Reminders' or groups[0] not in lists:
                return None
            scope.append(('list', lists[groups[0]]))
        elif kind == 'end':
            if not scope:
                return None
            scope.pop()
        elif kind == 'purge':
            if app != 'Reminders' or lists.get(groups[0]) != REMINDER_LIST:
                return None
            ops.append(('purge_completed_reminders',))
        elif kind in ('make_reminder', 'delete_reminder', 'complete_reminder', 'move_reminder'):
            if app != 'Reminders' or target != ('list', REMINDER_LIST):
                return None
            name, stamp = text_of(groups[0]), _script_stamp(text_of(groups[1]) or '')
            if not name or stamp is None:
                return None
            if kind == 'make_reminder':
                ops.append((kind, name, stamp, text_of(groups[2]) or None))
            elif kind == 'move_reminder':
                new_stamp = _script_stamp(text_of(groups[2]) or '')
                if new_stamp is None:
                    return None
                ops.append((kind, name, stamp, new_stamp))
            else:
                ops.append((kind, name, stamp))
        elif kind == 'make_event':
            if app != 'Calendar' or not isinstance(target, tuple) or target[0] != 'calendar':
                return None
            name, stamp = text_of(groups[0]), _script_stamp(text_of(groups[1]) or '')
            if not name or stamp is None or _script_stamp(text_of(groups[2]) or '') != stamp:
                return None
            seconds = int(round(float(groups[3]) * 3600))
            if seconds < 0:
                return None
            ops.append((kind, target[1], name, stamp, seconds))
        elif kind == 'delete_event':
            if app != 'Calendar' or not isinstance(target, tuple) or target[0] != 'calendar':
                return None
            stamp, name = _script_stamp(text_of(groups[0]) or ''), text_of(groups[1])
            if not name or stamp is None:
                return None
            ops.append((kind, target[1], name, stamp))
    if scope or app is None:
        return None
    return ops
