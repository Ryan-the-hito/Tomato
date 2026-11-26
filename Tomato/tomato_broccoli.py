"""Tomato → Broccoli: a timed item whose name starts with "@Broccoli " is a question for Broccoli, sent when the
item's time comes.

    @Broccoli summarise today's tech news        (Time page, any time; a repeating item works the same)

How it runs (nothing here looks at the clock on a schedule):
  1. Scheduler.rearm() reads the table once, finds the nearest unsent "@Broccoli" item and sets ONE single-shot
     timer for that moment. rearm() is called only when something tells Tomato the answer may have changed:
     All.csv was written (file watcher), the Mac woke up, the system clock / time zone was changed, Tomato started.
  2. When the timer fires, the due items are sent on a background thread: POST /agent/tasks of Broccoli's
     "Agent automation" door (127.0.0.1, token from Broccoli's own agent_automation_server.json). Broccoli not
     running → it is opened in the background and waited for.
  3. A sent item is written into broccoli_sent.json (name|stamp), so it is never sent twice, then the row is ticked
     off the usual way. For a repeating item that is what adds the next occurrence at the end of the series: a
     repeating task is a chain of one-time tasks.
  4. An item whose time passed more than GRACE_SECONDS ago (Mac asleep, Tomato closed) is marked "missed", not sent.

Long instructions (2026-11-17): a task is a folder  <Broccoli's data folder>/ScheduledTasks/<task name>/  with
  task.md        what to do and what not to do, as long as needed (written by Broccoli, or by hand in Tomato)
  schedule.json  optional: "put this on Tomato's table" — {"scheduler": "Tomato", "start": "2026-11-23 09:00",
                 "length_hours": 1, "repeat_hours": 168 | null, "repeat_until": "2026-12-31" | null}
An item named "@Broccoli <task name>" sends the whole of task.md (read at that moment) instead of its own words.
A folder holding BOTH files is a request: TaskSync puts the rows on the table, once per schedule; a folder with a
schedule and no task.md is a draft and does nothing. The folder is shared ground: any program may write such a
folder (Broccoli will), and other timing programs use the same place with their own name in "scheduler"
(each announces itself in ScheduledTasks/_schedulers/<name>.json). TaskSync is told of changes by the file
watcher, like the timer.

Writing task.md together with Broccoli (2026-11-17): Tomato carries a Broccoli skill, tomato_schedule_skill.md
("tomato-schedule": ask first, show the task, write the two files only after a yes). install_skill() puts it into
<Broccoli's data folder>/AppSkills/ so that Broccoli can offer it while Tomato is on this Mac. A new task made in
Tomato is handed to Broccoli as a conversation that starts with "//tomato-schedule" (Discussion); without Broccoli
the instructions are written by hand in Tomato.

A standby Mac (2026-11-18): a task may name another Mac that runs it when this Mac is asleep or off at its time
(Tomato is not running then either, so the other Mac has to know beforehand). Tomato only writes and reads small
files on the shared ground; Broccoli does the handing over:
  <task>/standby.json           {"device_id": …, "device_name": …}: which Mac stands by for this task (the manager window)
  _due/Tomato.json              the task rows still to come, {"items": [{"task": name, "stamp": seconds}]}; written
                                whenever the table is looked at and the list changed
  _devices.json                 written by Broccoli: this person's other Macs that can stand by (the drop-down)
  _done/<task>/<stamp>.json     written by Broccoli: the standby Mac ran this one → the row is ticked off, not sent

The first half of the file is plain Python (tests: tests_dev/tm_broccoli_test.py); only Scheduler needs Qt."""
import http.client
import json
import logging
import os
import re
import subprocess
import threading
import time

MARKER = '@Broccoli'
GRACE_SECONDS = 24 * 3600        # later than this after the item's time: missed, not sent
RETRY_SECONDS = 300              # after a failed send
MAX_TIMER_SECONDS = 6 * 3600     # a far-away time is approached in steps (a Qt timer cannot hold weeks)
LAUNCH_WAIT_SECONDS = 120        # how long a just-opened Broccoli gets to answer
KEEP_SECONDS = 400 * 86400       # how long the "sent" book remembers an item

BROCCOLI_BUNDLE_ID = 'com.ryanthehito.broccoli'
BROCCOLI_APP_NAME = 'Broccoli'
DEFAULT_PORT = 49153
PING_SERVICE = 'broccoli-agent-automation'
SOURCE = 'Tomato'

PLAIN_GROUP = 'Scheduled tasks'  # Broccoli group of the one-sentence items (the app sets it in its own language)
TASKS_FOLDER = 'ScheduledTasks'
SCHEDULERS_FOLDER = '_schedulers'
SPEC_FILE = 'task.md'
SCHEDULE_FILE = 'schedule.json'
SCHEDULER_NAME = 'Tomato'
MAX_SPEC_BYTES = 1500000         # Broccoli's door reads 2,000,000 bytes of request at most
MAX_TASK_NAME = 80
SKILL_NAME = 'tomato-schedule'
SKILL_FILE = 'tomato_schedule_skill.md'
# further skills Tomato brings (2026-11-23): (name in Broccoli, file beside this module)
EXTRA_SKILLS = (('tomato-food-log', 'tomato_food_skill.md'),)
APP_SKILLS_FOLDER = 'AppSkills'  # in Broccoli's data folder: skills that other programs bring along
STANDBY_FILE = 'standby.json'     # in a task's folder: the Mac that runs it when this one is off
DUE_FOLDER = '_due'               # ScheduledTasks/_due/<scheduler>.json: the task rows still to come
DEVICES_FILE = '_devices.json'    # written by Broccoli: the other Macs that can stand by
DONE_FOLDER = '_done'             # written by Broccoli: _done/<task>/<stamp>.json = a standby Mac ran it

_MARKED = re.compile(r'^\s*@broccoli(?:[\s:：,，]+)(.*\S)\s*$', re.I | re.S)


def info_path():
    return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', BROCCOLI_BUNDLE_ID,
                        'BroccoliAppPath', 'agent_automation_server.json')


def prompt_of(name):
    """The question in an item's name, or None when the item is not for Broccoli."""
    match = _MARKED.match(name or '')
    return match.group(1).strip() if match else None


def job_key(name, stamp):
    return '%s|%d' % ((name or '').strip(), int(float(stamp)))


# ── task folders ───────────────────────────────────────────────────────────────────────────────────────────────
def broccoli_data_dir():
    return os.path.dirname(info_path())


def tasks_root():
    return os.path.join(broccoli_data_dir(), TASKS_FOLDER)


# Where Broccoli is downloaded (its own update check uses this page). Ryan 2026-11-21: when Broccoli is not on
# the Mac, "先推荐下载" — the first thing offered is to download it.
DOWNLOAD_URL = 'https://github.com/Ryan-the-hito/Broccoli/releases/latest'


def open_download_page():
    """The download page in the default browser."""
    try:
        import subprocess
        return subprocess.run(['/usr/bin/open', DOWNLOAD_URL], capture_output=True, timeout=20).returncode == 0
    except Exception:
        logging.exception('opening the Broccoli download page failed')
        return False


def broccoli_installed():
    """Broccoli has run on this Mac (its data folder is there) or the system knows the app."""
    if os.path.isdir(broccoli_data_dir()):
        return True
    try:
        from AppKit import NSWorkspace
        return NSWorkspace.sharedWorkspace().URLForApplicationWithBundleIdentifier_(BROCCOLI_BUNDLE_ID) is not None
    except Exception:
        return False


def valid_task_name(name):
    """The name as a folder name, or None: one line, no / \\ :, not starting with . or _, at most 80 characters."""
    name = ' '.join((name or '').split())
    if not name or len(name) > MAX_TASK_NAME or name[0] in '._' or any(c in name for c in '/\\:') or prompt_of(name) is not None:
        return None
    return name


def _stamp_of(value, end_of_day=False):
    if value in (None, '', '-'):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    for pattern in ('%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
        try:
            return int(time.mktime(time.strptime(text, pattern)))
        except ValueError:
            pass
    try:
        day = time.mktime(time.strptime(text, '%Y-%m-%d'))
        return int(day) + (86399 if end_of_day else 0)
    except ValueError:
        pass
    try:
        return int(float(text))
    except ValueError:
        return None


def normalize_schedule(data):
    """What Tomato needs from a schedule.json, or None when it is not (validly) addressed to Tomato."""
    if not isinstance(data, dict) or str(data.get('scheduler') or '').strip().casefold() != SCHEDULER_NAME.casefold():
        return None
    start = _stamp_of(data.get('start'))
    if start is None:
        return None
    def number(key, default):
        try:
            value = float(data.get(key))
            return value if value > 0 else default
        except (TypeError, ValueError):
            return default
    return {'start': (start // 60) * 60, 'length_hours': number('length_hours', 1.0), 'repeat_hours': number('repeat_hours', None),
            'repeat_until': _stamp_of(data.get('repeat_until'), end_of_day=True)}


class TaskStore:
    """The task folders. Nothing here is created before a task is."""

    use_trash = True                 # tests turn it off: their folders do not belong in the real Trash

    def __init__(self, root=None):
        self.root = root or tasks_root()

    def path(self, name, file=None):
        return os.path.join(self.root, name, file) if file else os.path.join(self.root, name)

    def names(self):
        try:
            return sorted((entry for entry in os.listdir(self.root)
                           if entry[0] not in '._' and os.path.isdir(os.path.join(self.root, entry))), key=str.casefold)
        except OSError:
            return []

    def find(self, text):
        """The task a typed name means: letter case and outer spaces do not matter."""
        wanted = ' '.join((text or '').split()).casefold()
        if not wanted:
            return None
        import unicodedata
        wanted = unicodedata.normalize('NFC', wanted)
        for name in self.names():
            if unicodedata.normalize('NFC', name).casefold() == wanted:
                return name
        return None

    def has_spec(self, name):
        try:
            return os.path.getsize(self.path(name, SPEC_FILE)) > 0
        except OSError:
            return False

    def read_spec(self, name):
        """(text, None) or (None, 'missing' | 'empty' | 'too_big' | 'unreadable')."""
        path = self.path(name, SPEC_FILE)
        try:
            if os.path.getsize(path) > MAX_SPEC_BYTES:
                return None, 'too_big'
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
        except FileNotFoundError:
            return None, 'missing'
        except Exception:
            return None, 'unreadable'
        return (text, None) if text.strip() else (None, 'empty')

    def _write(self, name, file, text):
        os.makedirs(self.path(name), exist_ok=True)
        temp = self.path(name, file) + '.tmp'
        with open(temp, 'w', encoding='utf-8') as handle:
            handle.write(text)
        os.replace(temp, self.path(name, file))

    def create(self, name):
        os.makedirs(self.path(name), exist_ok=True)

    def write_spec(self, name, text):
        self._write(name, SPEC_FILE, text)

    def read_schedule(self, name):
        try:
            with open(self.path(name, SCHEDULE_FILE), encoding='utf-8') as handle:
                return normalize_schedule(json.load(handle))
        except Exception:
            return None

    def write_schedule(self, name, start, length_hours=1.0, repeat_hours=None, repeat_until=None):
        def day(stamp, pattern):
            return time.strftime(pattern, time.localtime(int(stamp)))
        self._write(name, SCHEDULE_FILE, json.dumps({
            'version': 1, 'scheduler': SCHEDULER_NAME, 'start': day(start, '%Y-%m-%d %H:%M'), 'length_hours': length_hours,
            'repeat_hours': repeat_hours, 'repeat_until': day(repeat_until, '%Y-%m-%d') if repeat_until else None,
            'created_by': SCHEDULER_NAME, 'created_at': day(time.time(), '%Y-%m-%d %H:%M')}, ensure_ascii=False, indent=1))

    # ── the standby Mac ──
    def read_standby(self, name):
        """{'device_id', 'device_name'} of the Mac that stands by for this task, or None."""
        try:
            with open(self.path(name, STANDBY_FILE), encoding='utf-8') as handle:
                data = json.load(handle)
            device = str(data.get('device_id') or '').strip()
            return {'device_id': device, 'device_name': str(data.get('device_name') or device)} if device else None
        except Exception:
            return None

    def write_standby(self, name, device_id, device_name=''):
        """Name the standby Mac of a task; an empty device_id = none (the file goes)."""
        path = self.path(name, STANDBY_FILE)
        if not str(device_id or '').strip():
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
            return
        self._write(name, STANDBY_FILE, json.dumps({'version': 1, 'device_id': str(device_id), 'device_name': str(device_name or device_id)},
                                                   ensure_ascii=False, indent=1))

    def standby_devices(self):
        """[{'id', 'name'}]: the other Macs Broccoli says can stand by (empty: none, or Broccoli has not said yet)."""
        try:
            with open(os.path.join(self.root, DEVICES_FILE), encoding='utf-8') as handle:
                data = json.load(handle)
            return [{'id': str(d['id']), 'name': str(d.get('name') or d['id'])} for d in data.get('devices') or []
                    if isinstance(d, dict) and d.get('id') and d.get('standby')]
        except Exception:
            return []

    def done_elsewhere(self, name, stamp):
        """The name of the Mac that ran this task at this time instead of this one, or None."""
        try:
            with open(os.path.join(self.root, DONE_FOLDER, name, '%d.json' % int(stamp)), encoding='utf-8') as handle:
                data = json.load(handle)
            return str(data.get('device_name') or data.get('device_id') or '?')
        except Exception:
            return None

    def rename(self, old, new):
        if self.find(new) not in (None, old):
            return False
        try:
            os.rename(self.path(old), self.path(new))
            return True
        except OSError:
            logging.exception('renaming a task folder failed')
            return False

    def delete(self, name):
        """Into the Trash (it can be taken back out); removed outright only when that is not possible."""
        path = self.path(name)
        try:
            if not self.use_trash:
                raise RuntimeError('no trash')
            from Foundation import NSFileManager, NSURL
            ok, _url, _error = NSFileManager.defaultManager().trashItemAtURL_resultingItemURL_error_(NSURL.fileURLWithPath_(path), None, None)
            if ok:
                return True
        except Exception:
            pass
        try:
            import shutil
            shutil.rmtree(path)
            return True
        except OSError:
            logging.exception('deleting a task folder failed')
            return False

    def write_manifest(self):
        """Tell whoever writes task folders that Tomato is here and what it can time. Only when Broccoli's data
        folder already exists: Tomato does not create another program's folder just by starting."""
        if not os.path.isdir(os.path.dirname(self.root)):
            return False
        try:
            folder = os.path.join(self.root, SCHEDULERS_FOLDER)
            os.makedirs(folder, exist_ok=True)
            text = json.dumps({
                'version': 1, 'name': SCHEDULER_NAME,
                'what': 'Sends task.md to Broccoli at the scheduled time, while Tomato is running. A time missed by more than a day is skipped.',
                'schedule_file': SCHEDULE_FILE, 'task_file': SPEC_FILE,
                'schedule': {'scheduler': SCHEDULER_NAME, 'start': 'YYYY-MM-DD HH:MM (local time)', 'length_hours': 'number, optional',
                             'repeat_hours': 'number or null (24 = daily, 168 = weekly)', 'repeat_until': 'YYYY-MM-DD or null'},
            }, ensure_ascii=False, indent=1)
            path = os.path.join(folder, SCHEDULER_NAME + '.json')
            try:
                if open(path, encoding='utf-8').read() == text:
                    return True
            except OSError:
                pass
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(text)
            return True
        except Exception:
            logging.exception('writing the scheduler note failed')
            return False


def skill_text(file_name=None):
    """The skill Tomato brings for Broccoli, or '' when the file is not beside this module."""
    file_name = file_name or SKILL_FILE
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    # beside the module (from source); in the packaged app the data files are in Contents/Resources
    for folder in (here, getattr(sys, '_MEIPASS', ''), os.path.join(os.path.dirname(here), 'Resources')):
        try:
            with open(os.path.join(folder, file_name), encoding='utf-8') as handle:
                return handle.read()
        except OSError:
            continue
    return ''


def install_skill(data_dir=None):
    """Keep <Broccoli's data folder>/AppSkills/tomato-schedule.md (and Tomato's further skills) equal to Tomato's
    own copies. Nothing is written when Broccoli has never run on this Mac. → whether the schedule skill is there."""
    for name, file_name in EXTRA_SKILLS:
        _install_one_skill(name, skill_text(file_name), data_dir)
    return _install_one_skill(SKILL_NAME, skill_text(), data_dir)


def _install_one_skill(name, text, data_dir=None):
    data_dir = data_dir or broccoli_data_dir()
    if not text or not os.path.isdir(data_dir):
        return False
    try:
        folder = os.path.join(data_dir, APP_SKILLS_FOLDER)
        path = os.path.join(folder, name + '.md')
        try:
            if open(path, encoding='utf-8').read() == text:
                return True
        except OSError:
            pass
        os.makedirs(folder, exist_ok=True)
        with open(path + '.tmp', 'w', encoding='utf-8') as handle:
            handle.write(text)
        os.replace(path + '.tmp', path)
        return True
    except Exception:
        logging.exception('installing the Broccoli skill failed')
        return False


def discussion_prompt(name, schedule):
    """What Tomato says to Broccoli to start writing a draft's task.md together with the user."""
    def day(stamp, pattern='%Y-%m-%d %H:%M'):
        return time.strftime(pattern, time.localtime(int(stamp)))
    repeat = schedule.get('repeat_hours')
    when = 'first run %s (local time)' % day(schedule['start'])
    when += ', then every %g hours' % repeat if repeat else ', once'
    if repeat and schedule.get('repeat_until'):
        when += ' until %s' % day(schedule['repeat_until'], '%Y-%m-%d')
    return ('//%s The user just created a scheduled task in Tomato and wants to work out its instructions with you.\n'
            'Task name (use exactly this as the folder name): %s\n'
            'Time, already set in Tomato: %s. This is a draft: schedule.json already exists in the task folder and '
            'task.md does not. Do not ask about the time and do not rewrite schedule.json.\n'
            'Ask the user what the task should do, show them the full task.md, and after they agree write only task.md.'
            % (SKILL_NAME, name, when))


def activate_broccoli():
    """Bring the installed Broccoli to the front, if it is the one running."""
    try:
        from AppKit import NSRunningApplication
        for running in NSRunningApplication.runningApplicationsWithBundleIdentifier_(BROCCOLI_BUNDLE_ID):
            running.activateWithOptions_(0)
            return True
    except Exception:
        pass
    return False


def resolve(name, store):
    """What an item sends: ('task', task name, the text of task.md) | ('plain', None, its own words) |
    ('error', task name, why task.md cannot be sent)."""
    words = prompt_of(name)
    task = store.find(words) if store is not None else None
    if task is None:
        return 'plain', None, words
    text, error = store.read_spec(task)
    return ('error', task, error) if error else ('task', task, text)


def task_requests(store, state):
    """Which folders ask for rows now. state: {'known': [names seen last time], 'made': {name: schedule signature}}.
    → {'make': [(name, schedule, signature)], 'gone': [names whose folder disappeared]}"""
    names = store.names()
    made = state.get('made') or {}
    out = {'make': [], 'gone': [name for name in (state.get('known') or []) if name not in names], 'names': names}
    for name in names:
        schedule = store.read_schedule(name)
        if schedule is None or not store.has_spec(name):
            continue
        signature = json.dumps(schedule, sort_keys=True)
        if made.get(name) != signature:
            out['make'].append((name, schedule, signature))
    return out


# ── the standby Mac: what is still to come, and what another Mac already did ────────────────────────────────────
def due_items(entries, store, now):
    """The task rows still to come: [{'task': task name, 'stamp': seconds}], nearest first. Only rows that name a
    task folder: a one-sentence item has no folder to say which Mac stands by."""
    out, seen = [], set()
    for name, stamp, status in entries:
        words = prompt_of(name)
        if words is None or (status or '').strip() != 'UNDONE':
            continue
        try:
            stamp = int(float(stamp))
        except (TypeError, ValueError):
            continue
        task = store.find(words) if stamp > now else None
        if task is None or (task, stamp) in seen:
            continue
        seen.add((task, stamp))
        out.append({'task': task, 'stamp': stamp})
    out.sort(key=lambda item: (item['stamp'], item['task']))
    return out


def write_due(store, items):
    """Put the list where Broccoli reads it. → True when the file was (re)written. Nothing is written while
    Broccoli's task folder does not exist, and nothing when the list is the one already there."""
    if not os.path.isdir(store.root):
        return False
    path = os.path.join(store.root, DUE_FOLDER, SCHEDULER_NAME + '.json')
    try:
        with open(path, encoding='utf-8') as handle:
            if json.load(handle).get('items') == items:
                return False
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        temp = path + '.tmp'
        with open(temp, 'w', encoding='utf-8') as handle:
            json.dump({'version': 1, 'scheduler': SCHEDULER_NAME, 'written_at': int(time.time()), 'items': items}, handle,
                      ensure_ascii=False, indent=1)
        os.replace(temp, path)
        return True
    except Exception:
        logging.exception('writing the list of coming tasks failed')
        return False


def done_by_standby(entries, store, ledger, now):
    """Rows whose time has come and that a standby Mac already ran: [(name, stamp, that Mac's name)]."""
    out = []
    for name, stamp, status in entries:
        words = prompt_of(name)
        if words is None or (status or '').strip() != 'UNDONE':
            continue
        try:
            stamp = int(float(stamp))
        except (TypeError, ValueError):
            continue
        if stamp > now or ledger.get(job_key(name, stamp)):
            continue
        task = store.find(words)
        device = store.done_elsewhere(task, stamp) if task is not None else None
        if device:
            out.append((name, stamp, device))
    return out


# ── the "sent" book ────────────────────────────────────────────────────────────────────────────────────────────
class Ledger:
    """{key: {'status': 'sent' | 'missed', 'at': when, 'done': the row was ticked off}} in one small file."""

    def __init__(self, path):
        self.path = path
        self.items = {}
        try:
            with open(path, encoding='utf-8') as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                self.items = {str(k): v for k, v in data.items() if isinstance(v, dict)}
        except FileNotFoundError:
            pass
        except Exception:
            logging.exception('broccoli_sent.json could not be read; starting an empty one')

    def get(self, key):
        return self.items.get(key)

    def mark(self, key, status, now=None, **extra):
        entry = dict(self.items.get(key) or {})
        entry.update(extra)
        entry['status'] = status
        entry.setdefault('at', int(now if now is not None else time.time()))
        self.items[key] = entry
        self.save()

    def prune(self, now):
        def stamp_of(key):
            try:
                return int(key.rsplit('|', 1)[1])
            except Exception:
                return 0
        old = [key for key in self.items if stamp_of(key) < now - KEEP_SECONDS]
        for key in old:
            del self.items[key]
        if old:
            self.save()

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            temp = self.path + '.tmp'
            with open(temp, 'w', encoding='utf-8') as handle:
                json.dump(self.items, handle, ensure_ascii=False, indent=1)
            os.replace(temp, self.path)
        except Exception:
            logging.exception('broccoli_sent.json could not be written')


def plan(entries, ledger, now, grace=GRACE_SECONDS):
    """What to do now with the table's rows. entries: (name, stamp, status) of every timed row.
    → {'send': [(name, stamp, prompt)], 'missed': [(name, stamp)], 'complete': [(name, stamp)], 'next': stamp | None}
    'complete' = sent earlier but the row could not be ticked off then."""
    out = {'send': [], 'missed': [], 'complete': [], 'next': None}
    seen = set()
    for name, stamp, status in entries:
        prompt = prompt_of(name)
        if prompt is None or (status or '').strip() != 'UNDONE':
            continue
        try:
            stamp = int(float(stamp))
        except (TypeError, ValueError):
            continue
        key = job_key(name, stamp)
        if key in seen:
            continue
        seen.add(key)
        entry = ledger.get(key)
        if entry:
            if entry.get('status') == 'sent' and not entry.get('done'):
                out['complete'].append((name, stamp))
            continue
        if stamp > now:
            if out['next'] is None or stamp < out['next']:
                out['next'] = stamp
        elif now - stamp > grace:
            out['missed'].append((name, stamp))
        else:
            out['send'].append((name, stamp, prompt))
    out['send'].sort(key=lambda job: job[1])
    return out


# ── sending ────────────────────────────────────────────────────────────────────────────────────────────────────
def read_info(path=None):
    """(port, token) from the file Broccoli writes for other programs."""
    try:
        with open(path or info_path(), encoding='utf-8') as handle:
            data = json.load(handle)
        return int(data.get('port') or DEFAULT_PORT), str(data.get('token') or '').strip()
    except Exception:
        return DEFAULT_PORT, ''


def _request(port, method, route, body=None, token='', timeout=5):
    # straight to this Mac (http.client never goes through a proxy)
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=timeout)
    try:
        headers = {}
        if body is not None:
            headers['Content-Type'] = 'application/json; charset=utf-8'
        if token:
            headers['X-Broccoli-Agent-Token'] = token
        connection.request(method, route, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        try:
            data = json.loads(raw.decode('utf-8'))
        except Exception:
            data = {}
        return response.status, data if isinstance(data, dict) else {}
    finally:
        connection.close()


def ping(port):
    try:
        status, data = _request(port, 'GET', '/ping', timeout=2)
        return status == 200 and data.get('service') == PING_SERVICE
    except Exception:
        return False


def launch_broccoli():
    """Open Broccoli without bringing it to the front. False = it is not on this Mac."""
    for arguments in (['-b', BROCCOLI_BUNDLE_ID], ['-a', BROCCOLI_APP_NAME]):
        try:
            if subprocess.run(['/usr/bin/open', '-g'] + arguments, capture_output=True, timeout=20).returncode == 0:
                return True
        except Exception:
            logging.exception('opening Broccoli failed')
    return False


def send(name, stamp, prompt, info=None, launch=launch_broccoli, wait=LAUNCH_WAIT_SECONDS, sleep=time.sleep, title=None,
         show=False):
    """Hand one question to Broccoli. → (True, 'sent') or (False, 'not_installed' | 'no_answer' | 'refused …').
    show: ask Broccoli to open the new conversation in front (the user is about to talk in it); a scheduled run
    stays in the background. A Broccoli that does not know "show" or "group" ignores them."""
    port, token = read_info(info)
    if not ping(port):
        if not launch():
            return False, 'not_installed'
        deadline = time.time() + wait
        while True:
            sleep(1.0)
            port, token = read_info(info)      # a first start writes the file
            if ping(port):
                break
            if time.time() >= deadline:
                return False, 'no_answer'
    payload = {
        'prompt': prompt,
        'source': SOURCE,
        'metadata': {'tomato_item': name, 'tomato_stamp': int(stamp),
                     'tomato_time': time.strftime('%Y-%m-%d %H:%M', time.localtime(int(stamp)))},
    }
    if title:                                  # a task: the conversation is named after it, not after its first line
        # each run is a new conversation "<task> · <its time>"; all of one task's conversations go into one
        # Broccoli group named after the task (models / autonomous per task, and a run can look at earlier ones)
        payload['title'] = title if show else '%s · %s' % (title, payload['metadata']['tomato_time'])
        payload['metadata']['tomato_task'] = title
        payload['group'] = title
    elif PLAIN_GROUP:                          # one-sentence items share one group
        payload['group'] = PLAIN_GROUP
    if show:
        payload['show'] = True
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    try:
        status, data = _request(port, 'POST', '/agent/tasks', body, token, timeout=15)
        if status == 401:                      # Broccoli made a new token since the file was read
            port, token = read_info(info)
            status, data = _request(port, 'POST', '/agent/tasks', body, token, timeout=15)
    except Exception as error:
        return False, 'no_answer (%s)' % error
    if status == 202 and data.get('ok'):
        return True, 'sent'
    return False, 'refused %s %s' % (status, data.get('error') or '')


# ── the one timer ──────────────────────────────────────────────────────────────────────────────────────────────
try:
    from PyQt6.QtCore import QObject, QTimer, QFileSystemWatcher, Qt, pyqtSignal
except Exception:                                   # the plain half still works (tests without Qt)
    QObject = None

if QObject is not None:
    _observers = []

    def _watch_system(callback):
        """callback() on wake from sleep and when the system clock or the time zone is changed."""
        try:
            import objc
            from Foundation import NSObject, NSNotificationCenter
            from AppKit import NSWorkspace, NSWorkspaceDidWakeNotification
        except Exception:
            return
        global _TomatoBroccoliObserver
        try:
            _TomatoBroccoliObserver
        except NameError:
            class _TomatoBroccoliObserver(NSObject):
                def tomatoBroccoliNudge_(self, notification):
                    try:
                        self.callback()
                    except Exception:
                        logging.exception('Broccoli scheduler: nudge failed')
        try:
            observer = _TomatoBroccoliObserver.alloc().init()
            observer.callback = callback
            NSWorkspace.sharedWorkspace().notificationCenter().addObserver_selector_name_object_(
                observer, 'tomatoBroccoliNudge:', NSWorkspaceDidWakeNotification, None)
            center = NSNotificationCenter.defaultCenter()
            for name in ('NSSystemClockDidChangeNotification', 'NSSystemTimeZoneDidChangeNotification'):
                center.addObserver_selector_name_object_(observer, 'tomatoBroccoliNudge:', name, None)
            _observers.append(observer)
        except Exception:
            logging.exception('Broccoli scheduler: could not watch for wake / clock changes')

    class Scheduler(QObject):
        """entries() → [(name, stamp, status)] of the timed rows; complete(name, stamp) → True once the row is
        ticked off (False = busy, asked again shortly); notify(kind, name) with kind 'failed' | 'missed'."""
        _finished = pyqtSignal(object)          # from the sending thread
        _nudged = pyqtSignal()                  # from the system's notifications

        def __init__(self, parent, entries, complete, csv_path, notify=None, sender=send, clock=time.time, watch_system=True, store=None):
            super().__init__(parent)
            self._entries, self._complete, self._notify = entries, complete, notify
            self._sender, self._clock = sender, clock
            self._csv_path = csv_path
            self.ledger = Ledger(os.path.join(os.path.dirname(csv_path), 'broccoli_sent.json'))
            self._sending = False
            self._retry_at = 0.0
            self._told = set()                  # items whose failure was already shown
            self.store = store                  # TaskStore: "@Broccoli <task name>" sends that task's task.md
            self._blocked = set()               # items whose task.md cannot be sent; looked at again when a task changes
            self.armed_for = None               # the moment the timer waits for (tests read it)
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.setTimerType(Qt.TimerType.PreciseTimer)
            self._timer.timeout.connect(self._evaluate)
            self._settle = QTimer(self)         # several changes in a row = one look at the table
            self._settle.setSingleShot(True)
            self._settle.setInterval(700)
            self._settle.timeout.connect(self._evaluate)
            self._finished.connect(self._on_finished)
            self._nudged.connect(self.rearm)
            self._watcher = QFileSystemWatcher(self)
            self._watcher.fileChanged.connect(self._on_file_changed)
            self._watcher.directoryChanged.connect(self._watch_file)
            with_dir = os.path.dirname(csv_path)
            if os.path.isdir(with_dir):
                self._watcher.addPath(with_dir)
            self._watch_file()
            if watch_system:
                _watch_system(self._nudged.emit)
            self.ledger.prune(self._clock())

        def _watch_file(self, *_):
            if self._csv_path not in self._watcher.files() and os.path.exists(self._csv_path):
                self._watcher.addPath(self._csv_path)
                self.rearm()                    # the file was replaced: its content may be new

        def _on_file_changed(self, *_):
            self._watch_file()
            self.rearm()

        def rearm(self):
            self._settle.start()

        def tasks_changed(self):
            """A task folder changed: an item that waited for a readable task.md gets another try."""
            self._blocked.clear()
            self.rearm()

        def _evaluate(self):
            if self._sending:
                return                          # looked at again when the sending thread reports
            now = self._clock()
            try:
                entries = list(self._entries())
                if self.store is not None:
                    # a standby Mac ran it while this one was off: written down as sent (ticked off below, never sent)
                    for name, stamp, device in done_by_standby(entries, self.store, self.ledger, now):
                        self.ledger.mark(job_key(name, stamp), 'sent', now, done=False, by=device)
                        logging.info('Broccoli: "%s" (%s) was run by %s', name, stamp, device)
                    write_due(self.store, due_items(entries, self.store, now))
                todo = plan(entries, self.ledger, now)
            except Exception:
                logging.exception('Broccoli scheduler: reading the table failed')
                return
            for name, stamp in todo['missed']:
                self.ledger.mark(job_key(name, stamp), 'missed', now)
                logging.info('Broccoli: missed "%s" (%s)', name, stamp)
                self._tell('missed', name)
            again_soon = False
            for name, stamp in todo['complete']:
                if self._tick_off(name, stamp):
                    self.ledger.mark(job_key(name, stamp), 'sent', done=True)
                else:
                    again_soon = True
            wake_at = todo['next']
            todo['send'] = [job for job in todo['send'] if job_key(job[0], job[1]) not in self._blocked]
            if todo['send']:
                if now >= self._retry_at:
                    self._sending = True
                    threading.Thread(target=self._send_all, args=(todo['send'],), daemon=True, name='tomato-broccoli-send').start()
                    return
                wake_at = self._retry_at if wake_at is None else min(wake_at, self._retry_at)
            if again_soon:
                wake_at = now + 5 if wake_at is None else min(wake_at, now + 5)
            self._arm(wake_at, now)

        def _arm(self, wake_at, now):
            self._timer.stop()
            self.armed_for = wake_at
            if wake_at is None:
                return
            seconds = min(max(0.0, wake_at - now) + 0.25, MAX_TIMER_SECONDS)
            self._timer.start(int(seconds * 1000))

        def _tick_off(self, name, stamp):
            try:
                return bool(self._complete(name, stamp))
            except Exception:
                logging.exception('Broccoli scheduler: ticking the row off failed')
                return False

        def _tell(self, kind, name):
            if self._notify is None:
                return
            try:
                self._notify(kind, name)
            except Exception:
                logging.exception('Broccoli scheduler: notice failed')

        def _send_all(self, jobs):              # background thread: no Qt, no table
            results = []
            for name, stamp, prompt in jobs:
                try:
                    kind, task, text = resolve(name, self.store)     # task.md is read now, not when the item was made
                    if kind == 'error':
                        results.append((name, stamp, False, 'task_file %s' % text))
                        continue
                    ok, reason = self._sender(name, stamp, text, **({'title': task} if task else {}))
                except Exception as error:
                    ok, reason = False, 'error %s' % error
                results.append((name, stamp, ok, reason))
                if not ok:
                    break                       # Broccoli is not there: the rest waits for the retry too
            self._finished.emit(results)

        def _on_finished(self, results):
            self._sending = False
            now = self._clock()
            for name, stamp, ok, reason in results:
                key = job_key(name, stamp)
                if ok:
                    self._retry_at = 0.0
                    self.ledger.mark(key, 'sent', now, done=False)     # written before anything else: never twice
                    logging.info('Broccoli: sent "%s" (%s)', name, stamp)
                    if self._tick_off(name, stamp):
                        self.ledger.mark(key, 'sent', done=True)
                elif reason.startswith('task_file'):
                    self._blocked.add(key)      # not sent, the row stays; tried again when the task's files change
                    logging.warning('Broccoli: "%s" (%s) not sent: %s', name, stamp, reason)
                    if key not in self._told:
                        self._told.add(key)
                        self._tell(reason.replace(' ', '_'), name)       # task_file_empty | _too_big | _unreadable | _missing
                else:
                    self._retry_at = now + RETRY_SECONDS
                    logging.warning('Broccoli: "%s" (%s) not sent: %s', name, stamp, reason)
                    if key not in self._told:
                        self._told.add(key)
                        self._tell('not_installed' if reason == 'not_installed' else 'failed', name)
            self._evaluate()


    class TaskSync(QObject):
        """Watches the task folders. add_rows(name, schedule) → True once the rows are on the table;
        remove_rows(name) → True once the undone rows of that task are off it (False = busy, asked again shortly).
        changed is emitted after every look (the manager window and the timer listen)."""
        changed = pyqtSignal()

        def __init__(self, parent, store, state_path, add_rows, remove_rows):
            super().__init__(parent)
            self.store, self._state_path = store, state_path
            self._add_rows, self._remove_rows = add_rows, remove_rows
            self.state = {'known': [], 'made': {}}
            try:
                with open(state_path, encoding='utf-8') as handle:
                    data = json.load(handle)
                if isinstance(data, dict):
                    self.state = {'known': list(data.get('known') or []), 'made': dict(data.get('made') or {})}
            except FileNotFoundError:
                pass
            except Exception:
                logging.exception('broccoli_tasks.json could not be read; starting an empty one')
            self._watcher = QFileSystemWatcher(self)
            self._watcher.directoryChanged.connect(self.look)
            self._watcher.fileChanged.connect(self.look)
            self._settle = QTimer(self)
            self._settle.setSingleShot(True)
            self._settle.setInterval(500)
            self._settle.timeout.connect(self.sync)
            self._again = QTimer(self)          # only while the table was busy
            self._again.setSingleShot(True)
            self._again.setInterval(5000)
            self._again.timeout.connect(self.sync)

        def look(self, *_):
            self._settle.start()

        def _rewatch(self, names):
            wanted = []
            if os.path.isdir(self.store.root):
                wanted.append(self.store.root)
                for name in names:
                    wanted.append(self.store.path(name))
                    for file in (SCHEDULE_FILE, SPEC_FILE):
                        if os.path.exists(self.store.path(name, file)):
                            wanted.append(self.store.path(name, file))
                # what a standby Mac ran instead of this one (Broccoli writes _done/<task>/<stamp>.json)
                done = os.path.join(self.store.root, DONE_FOLDER)
                if os.path.isdir(done):
                    wanted.append(done)
                    wanted += [os.path.join(done, name) for name in names if os.path.isdir(os.path.join(done, name))]
            elif os.path.isdir(os.path.dirname(self.store.root)):
                wanted.append(os.path.dirname(self.store.root))     # Broccoli's folder: ScheduledTasks may appear in it
            have = set(self._watcher.files()) | set(self._watcher.directories())
            for path in have - set(wanted):
                self._watcher.removePath(path)
            for path in wanted:
                if path not in have:
                    self._watcher.addPath(path)

        def _save(self):
            try:
                temp = self._state_path + '.tmp'
                with open(temp, 'w', encoding='utf-8') as handle:
                    json.dump(self.state, handle, ensure_ascii=False, indent=1)
                os.replace(temp, self._state_path)
            except Exception:
                logging.exception('broccoli_tasks.json could not be written')

        def forget(self, name, renamed_to=None):
            """Tomato itself deleted / renamed this task: its rows are already dealt with."""
            signature = self.state['made'].pop(name, None)
            self.state['known'] = [n for n in self.state['known'] if n != name]
            if renamed_to:
                self.state['known'].append(renamed_to)
                if signature is not None:
                    self.state['made'][renamed_to] = signature
            self._save()

        def sync(self):
            try:
                todo = task_requests(self.store, self.state)
            except Exception:
                logging.exception('Broccoli tasks: reading the task folders failed')
                return
            busy = False
            for name in todo['gone']:
                if self._remove_rows(name) is False:
                    busy = True
                    continue
                self.state['made'].pop(name, None)
                self.state['known'] = [n for n in self.state['known'] if n != name]
            for name, schedule, signature in todo['make']:
                if name in self.state['made'] and self._remove_rows(name) is False:     # the schedule was changed
                    busy = True
                    continue
                self.state['made'].pop(name, None)
                if self._add_rows(name, schedule):
                    self.state['made'][name] = signature
                    logging.info('Broccoli tasks: "%s" is on the table', name)
                else:
                    busy = True
            gone_waiting = [name for name in todo['gone'] if name in self.state['known']]
            self.state['known'] = todo['names'] + gone_waiting
            self._save()
            self._rewatch(todo['names'])
            if busy:
                self._again.start()
            self.changed.emit()


    class Discussion(QObject):
        """Hands a draft to Broccoli on a background thread. finished(task name, ok, reason)."""
        finished = pyqtSignal(str, bool, str)

        def __init__(self, parent, sender=send):
            super().__init__(parent)
            self._sender = sender

        def start(self, name, schedule):
            def work():
                try:
                    ok, reason = self._sender(MARKER + ' ' + name, schedule['start'], discussion_prompt(name, schedule), title=name,
                                              show=True)
                except Exception as error:
                    ok, reason = False, 'error %s' % error
                self.finished.emit(name, bool(ok), str(reason))
            threading.Thread(target=work, daemon=True, name='tomato-broccoli-discuss').start()
