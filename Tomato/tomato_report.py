# -*- coding: utf-8 -*-
"""Tomato's daily report: the scattered diary of a day gathered into one page (2026-11-23).

Ryan 2026-11-23: "Tomato 可以出现一个就是每天汇报的这样一个功能：我每天大概做了什么，我每天大概想了什么，什么时间干了
什么……吃了什么、做了什么、什么时间干了什么"; the language follows the interface; "需要一个有模板的那个东西".

A report is  <data folder>/Reports/<kind>/<key>.md  and has two halves:
  * the numbers — counted by Tomato itself from the diary (tomato_diary.parse): time per app, the stretches of the
    day, what was taken from the Collections (meals …) with the numbers found in that collection's row and their
    sums, finished items, own notes. Always there, no model needed. Ryan: without Broccoli (or without its
    background vision) "不至于说就是这个功能直接废掉".
  * the written part — by Broccoli's model, after the person's template (Reports/template-<kind>.md, a default
    per report language until the person changes it). Tomato sends the template and the day's material through Broccoli's
    door; Broccoli hands the text back with Tomato's own tool save_daily_report. Until that arrives (or when it
    never does) the report is the numbers alone.
The first line of the file says which it is:  <!-- tomato-report: numbers -->  /  <!-- tomato-report: written -->.

2026-11-24 (Ryan: "我希望这个界面就像 broccoli 的初始界面一样……没有选择生成报告语言的地方"; then he chose: copy the
whole panel, weekly and monthly reports too, Broccoli's four languages, the numbers days · time · items · streak):
  * three kinds, as Broccoli's reports: 'day' (key YYYY-MM-DD), 'week' (key = its Monday, Monday–Sunday), 'month'
    (key YYYY-MM). Files: Reports/<kind>/<key>.md; templates Reports/template-<kind>.md. move_old_layout() moves the
    first version's Reports/<day>.md and template.md in.
  * the language is a free text out of a list the person keeps (default = Broccoli's four); the model is told to
    write in it. The default templates follow it (中文 → Chinese, 日本語 → Japanese, the rest English).
  * a week / month report is due like Broccoli's: the last finished week / month, written once, also at a start.

Plain Python, no Qt (tests: tests_dev/tm_report_test.py). The labels of the numbers half come from the caller
(translated there).
"""
import datetime
import json
import os
import re

import tomato_diary
import tomato_tools

FOLDER = 'Reports'
KINDS = ('day', 'week', 'month')
MARK_NUMBERS = '<!-- tomato-report: numbers -->'
MARK_WRITTEN = '<!-- tomato-report: written -->'
_MARK = re.compile(r'^<!-- tomato-report: (numbers|written)(?: (\{.*?\}))? -->\n*')
REPORT_HOUR, REPORT_MINUTE = 23, 30
MATERIAL_MAX_CHARS = 9000
PERIOD_MATERIAL_MAX_CHARS = 14000
VISION_MAX_LINES = 60
PERIOD_VISION_PER_DAY = 6
MAX_REPORT_CHARS = 60000
DEFAULT_LANGUAGES = ('日本語（仕事）', '日本語（日常）', '中文', 'English')     # = Broccoli's (style book 5.7.8)
LANGUAGE_MAX_CHARS = 60
DIARY_EMPTY_BYTES = 40           # a diary file this small holds only its title line

WEEK_TEMPLATES = {
    'en': '''## What I did this week
The main things of the week, most important first. Say what was worked on, not which app was open.

## What was on my mind
What the notes and the things on screen suggest I was thinking about or stuck on. Leave the section out when there is nothing to go on.

## How I ate
The meals of the week in a few lines: what came often, what was missing. Add the nutrition when the numbers are there.

## Day by day
One short line per day with a record.
''',
    'zh': '''## 这周做了什么
这一周主要做的事，重要的在前。写在做什么事，不是开着哪个软件。

## 想了什么
从我自己写的话和屏幕上看到的内容，推测我在想什么、卡在哪里。没有依据就不写这一段。

## 吃得怎么样
几句话说这一周吃了什么：常吃什么、缺了什么。有营养数字就写上。

## 每天一句
有记录的每一天写一句话。
''',
    'ja': '''## 今週やったこと
この一週間の主なこと。大事なものから。開いていたアプリではなく、何をしていたかを書く。

## 考えていたこと
自分のメモと画面に見えていた内容から、何を考え、どこで詰まっていたかを推測する。手がかりがなければ書かない。

## 食事
一週間の食事を数行で：よく食べたもの、足りなかったもの。栄養の数字があれば書く。

## 一日ずつ
記録のある日ごとに一行。
''',
}
MONTH_TEMPLATES = {
    'en': '''## What I did this month
The main things of the month, most important first. Say what was worked on, not which app was open.

## How the month went
Patterns: which weeks were busy, which were quiet, what changed over the month.

## How I ate
The meals of the month in a few lines. Add the nutrition when the numbers are there.

## Next month
What the record suggests to keep, to change or to finish next month.
''',
    'zh': '''## 这个月做了什么
这个月主要做的事，重要的在前。写在做什么事，不是开着哪个软件。

## 这个月怎么过的
规律：哪几周忙、哪几周闲，这个月里有什么变化。

## 吃得怎么样
几句话说这个月吃了什么。有营养数字就写上。

## 下个月
从记录看，下个月该保持什么、改什么、做完什么。
''',
    'ja': '''## 今月やったこと
今月の主なこと。大事なものから。開いていたアプリではなく、何をしていたかを書く。

## 今月の流れ
パターン：忙しかった週、落ち着いていた週、月の中で変わったこと。

## 食事
今月の食事を数行で。栄養の数字があれば書く。

## 来月
記録から見て、来月続けること・変えること・終わらせること。
''',
}

DAY_TEMPLATES = {
    'en': '''## What I did
The main things of the day, most important first. Say what was worked on, not which app was open.

## What was on my mind
What the notes and the things on screen suggest I was thinking about or stuck on. Leave the section out when there is nothing to go on.

## What I ate
Each meal with its time (breakfast / lunch / dinner / snack, judged by the time). Add the nutrition when the numbers are there.

## The day by the clock
A short timeline: from – to, what was going on.
''',
    'zh': '''## 做了什么
这一天主要做的事，重要的在前。写在做什么事，不是开着哪个软件。

## 想了什么
从我自己写的话和屏幕上看到的内容，推测我在想什么、卡在哪里。没有依据就不写这一段。

## 吃了什么
每一餐和它的时间（按时间判断是早餐、午餐、晚餐还是加餐）。有营养数字就写上。

## 时间线
简短的时间线：几点到几点，在做什么。
''',
    'ja': '''## やったこと
この日の主なこと。大事なものから。開いていたアプリではなく、何をしていたかを書く。

## 考えていたこと
自分のメモと画面に見えていた内容から、何を考え、どこで詰まっていたかを推測する。手がかりがなければ書かない。

## 食べたもの
食事ごとに時刻を添える（時刻から朝食・昼食・夕食・間食を判断）。栄養の数字があれば書く。

## タイムライン
短い時間の流れ：何時から何時まで、何をしていたか。
''',
}
DEFAULT_TEMPLATES = {'day': DAY_TEMPLATES, 'week': WEEK_TEMPLATES, 'month': MONTH_TEMPLATES}
LANGUAGE_NAMES = {'en': 'English', 'zh': 'Simplified Chinese', 'ja': 'Japanese'}
KIND_WORDS = {'day': 'daily', 'week': 'weekly', 'month': 'monthly'}

DEFAULT_LABELS = {
    'title': 'Daily report', 'title_week': 'Weekly report', 'title_month': 'Monthly report',
    'apps': 'Time per app', 'timeline': 'Timeline', 'also': 'also',
    'taken': 'From the Collections', 'total': 'Total', 'items': 'Items', 'seen': 'Seen on screen',
    'notes': 'Own notes', 'numbers': 'The numbers', 'nothing': 'Nothing was recorded on this day.',
    'nothing_period': 'Nothing was recorded in this period.',
    'time': 'Time', 'what': 'What', 'app': 'App', 'length': 'Length', 'per_day': 'Day by day', 'day': 'Day',
    'mostly': 'Mostly',
}


# ---- languages ------------------------------------------------------------------------------------------------

_LOCALE = re.compile(r'^[a-z]{2}([_-][A-Za-z]{2,4})?$')


def language_key(language):
    """'zh' / 'ja' / 'en': which default template a language takes (a locale code or a free text like 中文)."""
    text = str(language or '').strip()
    low = text.lower()
    if low.startswith('zh') or any(word in text for word in ('中文', '汉语', '漢語', '中国語')):
        return 'zh'
    if low.startswith('ja') or '日本' in text:
        return 'ja'
    return 'en'


def language_name(language):
    """What the model is told: a locale code as its language, a free text (日本語（仕事）) as it is."""
    text = ' '.join(str(language or '').split())
    if not text or _LOCALE.match(text):
        return LANGUAGE_NAMES[language_key(text)]
    return text


def normalize_languages(raw):
    out = []
    for item in raw if isinstance(raw, (list, tuple)) else []:
        text = ' '.join(str(item or '').split())[:LANGUAGE_MAX_CHARS]
        if text and text not in out:
            out.append(text)
    return out or list(DEFAULT_LANGUAGES)


def default_language(ui_language, languages=DEFAULT_LANGUAGES):
    """Before the person picks one: the one that matches the interface."""
    want = {'zh': '中文', 'ja': '日本語（日常）'}.get(language_key(ui_language), 'English')
    return want if want in languages else (list(languages) or ['English'])[0]


# ---- the three kinds (= Broccoli's report_key_for / report_period / report_period_label) ---------------------

def kind_of(kind):
    return kind if kind in KINDS else 'day'


def key_for(kind, day):
    """A day → its report's key: the day, the Monday of its week, or its month."""
    day = day if isinstance(day, datetime.date) else datetime.date.fromisoformat(str(day)[:10])
    if kind == 'week':
        return (day - datetime.timedelta(days=day.weekday())).isoformat()
    if kind == 'month':
        return day.strftime('%Y-%m')
    return day.isoformat()


def period(kind, key):
    """(first day, last day) of a report."""
    if kind == 'month':
        first = datetime.date.fromisoformat('%s-01' % str(key)[:7])
        following = (first.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        return first, following - datetime.timedelta(days=1)
    first = datetime.date.fromisoformat(str(key)[:10])
    return (first, first + datetime.timedelta(days=6)) if kind == 'week' else (first, first)


def period_days(kind, key):
    first, last = period(kind, key)
    return [(first + datetime.timedelta(days=n)).isoformat() for n in range((last - first).days + 1)]


def period_label(kind, key):
    first, last = period(kind, key)
    if kind == 'month':
        return first.strftime('%Y-%m')
    if kind == 'week':
        return '%s – %s' % (first.isoformat(), last.isoformat())
    return first.isoformat()


def valid_key(kind, key):
    """The key in its right shape ('' when it is not one): a week's key is turned into its Monday."""
    text = str(key or '').strip()
    try:
        if kind == 'month':
            return datetime.datetime.strptime(text[:7], '%Y-%m').strftime('%Y-%m')
        return key_for(kind, datetime.datetime.strptime(text[:10], '%Y-%m-%d').date())
    except ValueError:
        return ''


# ---- the files ------------------------------------------------------------------------------------------------

def reports_dir(data_dir):
    return os.path.join(data_dir, FOLDER)


def report_path(data_dir, key, kind='day'):
    kind = kind_of(kind)
    name = tomato_diary.day_name(key) if kind != 'month' else str(key)[:7]
    return os.path.join(reports_dir(data_dir), kind, name + '.md')


def template_path(data_dir, kind='day'):
    return os.path.join(reports_dir(data_dir), 'template-%s.md' % kind_of(kind))


_OLD_DAY_FILE = re.compile(r'^\d{4}-\d{2}-\d{2}(\.before)?\.md$')


def move_old_layout(data_dir):
    """The first version (2026-11-23) kept Reports/<day>.md and Reports/template.md: into Reports/day/ and
    template-day.md (nothing is left at the old place)."""
    folder = reports_dir(data_dir)
    try:
        names = os.listdir(folder)
    except OSError:
        return 0
    moved = 0
    for name in names:
        source = os.path.join(folder, name)
        if _OLD_DAY_FILE.match(name):
            target = os.path.join(folder, 'day', name)
        elif name == 'template.md':
            target = template_path(data_dir, 'day')
        else:
            continue
        if os.path.exists(target):
            continue
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            os.replace(source, target)
            moved += 1
        except OSError:
            pass
    return moved


def default_template(kind, language='en'):
    return DEFAULT_TEMPLATES[kind_of(kind)][language_key(language)]


def read_template(data_dir, kind='day', language='en'):
    """(text, is the person's own)."""
    try:
        with open(template_path(data_dir, kind), encoding='utf-8') as handle:
            text = handle.read()
        if text.strip():
            return text, True
    except OSError:
        pass
    return default_template(kind, language), False


def write_template(data_dir, kind, text):
    """An empty text takes the person's template away (the default of the report language is used again)."""
    path = template_path(data_dir, kind)
    if not str(text or '').strip():
        try:
            os.remove(path)
        except OSError:
            pass
        return
    os.makedirs(reports_dir(data_dir), exist_ok=True)
    with open(path + '.tmp', 'w', encoding='utf-8') as handle:
        handle.write(text)
    os.replace(path + '.tmp', path)


# ---- the day's facts ------------------------------------------------------------------------------------------

_NUMBER = re.compile(r'^\s*(-?\d+(?:[.,]\d+)?)\s*([^\d\s].{0,11})?$')


def _number(value):
    """650 / '650 kcal' / '12,5 g' → the number; anything else → None."""
    found = _NUMBER.match(str(value))
    if not found:
        return None
    try:
        return float(found.group(1).replace(',', '.'))
    except ValueError:
        return None


def nutrition(collections_folder, collection, name):
    """{column: number} of the collection row called `name`: its cells that are numbers. {} when not found."""
    try:
        path = tomato_tools.collection_path(collections_folder, collection)
        columns, rows = tomato_tools.read_collection(path)
    except Exception:
        return {}
    wanted = ' '.join(name.split()).casefold()
    for row in rows:
        if tomato_tools.row_title(columns, row).casefold() != wanted:
            continue
        numbers = {}
        for column, value in zip(columns, row):
            number = _number(value)
            if number is not None and column.strip():
                numbers[column] = number
        return numbers
    return {}


def _thin_vision(entries, limit=VISION_MAX_LINES):
    """The looks without the ones that say the same as the look before; when still more than `limit`, evenly
    thinned (a look every 30 seconds is 2,880 lines a day)."""
    kept = []
    for entry in sorted(entries, key=lambda e: e['at']):
        if kept and kept[-1]['text'].casefold() == entry['text'].casefold():
            continue
        kept.append(entry)
    if len(kept) > limit:
        step = len(kept) / float(limit)
        kept = [kept[int(index * step)] for index in range(limit)]
    return kept


def build_facts(diary_text, collections_folder='', end_seconds=None):
    facts = tomato_diary.parse(diary_text, end_seconds)
    facts['totals'] = [(app, seconds) for app, seconds in tomato_diary.app_totals(facts['segments']) if seconds >= 60]
    facts['blocks'] = [b for b in tomato_diary.blocks(facts['segments']) if b['end'] - b['start'] >= 60]
    facts['taken'].sort(key=lambda entry: entry['at'])
    facts['events'].sort(key=lambda entry: entry['at'])
    sums = {}
    for entry in facts['taken']:
        entry['numbers'] = nutrition(collections_folder, entry['collection'], entry['name']) if collections_folder else {}
        for column, number in entry['numbers'].items():
            sums.setdefault(entry['collection'], {}).setdefault(column, 0.0)
            sums[entry['collection']][column] += number
    facts['sums'] = sums
    facts['vision_thin'] = _thin_vision(facts['vision'])
    facts['empty'] = not (facts['totals'] or facts['taken'] or facts['events'] or facts['notes'] or facts['vision'])
    return facts




# ---- a week / a month: the days' facts together -------------------------------------------------------------

def day_slot(facts):
    """What the calendar and the numbers need of a day: seconds with an app in front, items finished."""
    return {'seconds': int(sum(seconds for _app, seconds in tomato_diary.app_totals(facts['segments']))),
            'done': sum(1 for event in facts['events'] if str(event['text']).startswith('Completed '))}


def period_facts(kind, key, facts_for_day):
    """facts_for_day(day) → build_facts of that day. For a day: its facts. For a week / month: the days with
    something in them, each with its facts, and the time per app summed."""
    kind = kind_of(kind)
    if kind == 'day':
        facts = facts_for_day(key)
        facts['kind'] = 'day'
        return facts
    days, totals, sums = [], {}, {}
    for day in period_days(kind, key):
        facts = facts_for_day(day)
        if facts['empty']:
            continue
        days.append(dict(day_slot(facts), day=day, facts=facts))
        for app, seconds in facts['totals']:
            totals[app] = totals.get(app, 0) + seconds
        for collection, columns in facts['sums'].items():
            for column, number in columns.items():
                sums.setdefault(collection, {}).setdefault(column, 0.0)
                sums[collection][column] += number
    return {'kind': kind, 'key': key, 'days': days, 'totals': sorted(totals.items(), key=lambda pair: (-pair[1], pair[0])),
            'sums': sums, 'empty': not days}


def summary(facts):
    """{'seconds', 'done'} of a day's or a period's facts."""
    if facts.get('kind', 'day') == 'day':
        return day_slot(facts)
    return {'seconds': sum(d['seconds'] for d in facts['days']), 'done': sum(d['done'] for d in facts['days'])}


# ---- the calendar's numbers (read on a worker thread; a cache keeps unchanged days) --------------------------

def has_record(diary_dir, day):
    try:
        return os.path.getsize(tomato_diary.path(diary_dir, day)) > DIARY_EMPTY_BYTES
    except OSError:
        return False


def day_slots(diary_dir, days, cache=None):
    """{day: {'seconds', 'done'}} for the days whose diary holds something. `cache` (a dict) keeps each file's
    slot by its size and time."""
    cache = cache if cache is not None else {}
    out = {}
    for day in days:
        target = tomato_diary.path(diary_dir, day)
        try:
            stat = os.stat(target)
        except OSError:
            continue
        if stat.st_size <= DIARY_EMPTY_BYTES:
            continue
        stamp = (stat.st_mtime, stat.st_size)
        known = cache.get(target)
        if known is not None and known[0] == stamp:
            slot = known[1]
        else:
            facts = build_facts(tomato_diary.read(diary_dir, day))
            slot = None if facts['empty'] else day_slot(facts)
            cache[target] = (stamp, slot)
        if slot is not None:
            out[day] = slot
    return out


def streak(diary_dir, today=None):
    """Days in a row with a record, up to today (or yesterday, before today has any)."""
    cursor = today or datetime.date.today()
    if not has_record(diary_dir, cursor.isoformat()):
        cursor -= datetime.timedelta(days=1)
    count = 0
    while count < 3700 and has_record(diary_dir, cursor.isoformat()):
        count += 1
        cursor -= datetime.timedelta(days=1)
    return count


def heat_level(seconds, busiest):
    """0–3: the shade of a day in the calendar (= Broccoli's activity_heat_level), by its time against the
    month's longest day."""
    if seconds <= 0:
        return 0
    if busiest <= 0:
        return 1
    share = seconds / float(busiest)
    return 1 if share < 0.34 else (2 if share < 0.67 else 3)


# ---- the numbers half -----------------------------------------------------------------------------------------

def _fmt(number):
    return ('%.1f' % number).rstrip('0').rstrip('.')


def _taken_lines(facts, total_label, day=''):
    lines = []
    prefix = (day[5:] + ' ') if day else ''
    for entry in facts['taken']:
        extra = (' — ' + entry['note']) if entry['note'] else ''
        numbers = ('  (' + ', '.join('%s %s' % (column, _fmt(n)) for column, n in entry['numbers'].items()) + ')') if entry['numbers'] else ''
        lines.append('- %s%s [%s] %s%s%s' % (prefix, tomato_diary.clock(entry['at']), entry['collection'], entry['name'], extra, numbers))
    if not day:
        lines += _sum_lines(facts, total_label)
    return lines


def _sum_lines(facts, total_label):
    lines = []
    for collection, columns in facts['sums'].items():
        if facts.get('kind', 'day') == 'day':
            count = sum(1 for entry in facts['taken'] if entry['collection'] == collection and entry['numbers'])
        else:
            count = sum(1 for d in facts['days'] for entry in d['facts']['taken'] if entry['collection'] == collection and entry['numbers'])
        if count > 1:
            lines.append('- **%s [%s]**: %s' % (total_label, collection, ', '.join('%s %s' % (c, _fmt(n)) for c, n in columns.items())))
    return lines


def _apps_table(totals, L):
    rows = ['| %s | %s |' % (L['app'], L['length']), '|---|---|']
    rows += ['| %s | %s |' % (app.replace('|', '/'), tomato_diary.duration_text(seconds)) for app, seconds in totals[:12]]
    return '### %s\n\n%s' % (L['apps'], '\n'.join(rows))


def numbers_markdown(facts, labels=None):
    """The half Tomato counts itself (a day, or a week / month: time per app, the days, items, meals, notes)."""
    L = dict(DEFAULT_LABELS, **(labels or {}))
    if facts.get('kind', 'day') != 'day':
        return _period_numbers_markdown(facts, L)
    if facts['empty']:
        return L['nothing']
    parts = []
    if facts['totals']:
        parts.append(_apps_table(facts['totals'], L))
    if facts['blocks']:
        lines = []
        for block in facts['blocks']:
            also = ' (%s %s)' % (L['also'], ', '.join(block['others'])) if block['others'] else ''
            lines.append('- %s–%s %s%s' % (tomato_diary.clock(block['start']), tomato_diary.clock(block['end']), block['app'], also))
        parts.append('### %s\n\n%s' % (L['timeline'], '\n'.join(lines)))
    if facts['taken']:
        parts.append('### %s\n\n%s' % (L['taken'], '\n'.join(_taken_lines(facts, L['total']))))
    if facts['events']:
        parts.append('### %s\n\n%s' % (L['items'], '\n'.join('- %s %s' % (tomato_diary.clock(e['at']), e['text']) for e in facts['events'])))
    if facts['notes']:
        parts.append('### %s\n\n%s' % (L['notes'], '\n'.join('- ' + note for note in facts['notes'])))
    return '\n\n'.join(parts)


def _period_numbers_markdown(facts, L):
    if facts['empty']:
        return L['nothing_period']
    parts = []
    if facts['totals']:
        parts.append(_apps_table(facts['totals'], L))
    rows = ['| %s | %s | %s |' % (L['day'], L['length'], L['mostly']), '|---|---|---|']
    for d in facts['days']:
        top = d['facts']['totals'][0][0].replace('|', '/') if d['facts']['totals'] else ''
        rows.append('| %s | %s | %s |' % (d['day'], tomato_diary.duration_text(d['seconds']), top))
    parts.append('### %s\n\n%s' % (L['per_day'], '\n'.join(rows)))
    taken = [line for d in facts['days'] for line in _taken_lines(d['facts'], L['total'], d['day'])]
    if taken:
        parts.append('### %s\n\n%s' % (L['taken'], '\n'.join(taken + _sum_lines(facts, L['total']))))
    events = ['- %s %s %s' % (d['day'][5:], tomato_diary.clock(e['at']), e['text']) for d in facts['days'] for e in d['facts']['events']]
    if events:
        parts.append('### %s\n\n%s' % (L['items'], '\n'.join(events)))
    notes = ['- %s %s' % (d['day'][5:], note) for d in facts['days'] for note in d['facts']['notes']]
    if notes:
        parts.append('### %s\n\n%s' % (L['notes'], '\n'.join(notes)))
    return '\n\n'.join(parts)


def _title(kind, key, L):
    return '%s · %s' % (L.get({'week': 'title_week', 'month': 'title_month'}.get(kind, 'title')), period_label(kind, key))


def _mark(base, meta):
    meta = {k: v for k, v in (meta or {}).items() if v}
    return base if not meta else base[:-4] + ' ' + json.dumps(meta, ensure_ascii=False) + ' -->'


def numbers_report(kind, key, facts, labels=None, meta=None):
    L = dict(DEFAULT_LABELS, **(labels or {}))
    return '%s\n# %s\n\n%s\n' % (_mark(MARK_NUMBERS, meta), _title(kind, key, L), numbers_markdown(facts, labels))


def written_report(kind, key, written, facts, labels=None, meta=None):
    """The model's text on top, Tomato's own numbers under it (so the numbers are never the model's)."""
    L = dict(DEFAULT_LABELS, **(labels or {}))
    written = str(written or '').strip()
    if not re.match(r'^#\s', written):
        written = '# %s\n\n%s' % (_title(kind, key, L), written)
    return '%s\n%s\n\n---\n\n## %s\n\n%s\n' % (_mark(MARK_WRITTEN, meta), written, L['numbers'], numbers_markdown(facts, labels))


# ---- what the model reads -------------------------------------------------------------------------------------

def material(facts):
    """The day (or the week / month) for the model, in a few thousand characters."""
    if facts.get('kind', 'day') != 'day':
        return _period_material(facts)
    parts = []
    if facts['totals']:
        parts.append('TIME PER APP\n' + '\n'.join('- %s: %s' % (app, tomato_diary.duration_text(s)) for app, s in facts['totals'][:15]))
    if facts['blocks']:
        parts.append('STRETCHES OF THE DAY (front app)\n' + '\n'.join(
            '- %s–%s %s%s' % (tomato_diary.clock(b['start']), tomato_diary.clock(b['end']), b['app'],
                              (' (also %s)' % ', '.join(b['others'])) if b['others'] else '') for b in facts['blocks']))
    if facts['vision_thin']:
        parts.append('SEEN ON SCREEN (short looks by a vision model)\n' + '\n'.join(
            '- %s %s' % (tomato_diary.clock(v['at']), v['text']) for v in facts['vision_thin']))
    if facts['taken']:
        parts.append('TAKEN FROM THE COLLECTIONS (meals and the like; numbers are from the collection\'s row)\n'
                     + '\n'.join(_taken_lines(facts, 'Total')))
    if facts['events']:
        parts.append('ITEMS\n' + '\n'.join('- %s %s' % (tomato_diary.clock(e['at']), e['text']) for e in facts['events']))
    if facts['notes']:
        parts.append('THE PERSON\'S OWN NOTES\n' + '\n'.join('- ' + note for note in facts['notes']))
    text = '\n\n'.join(parts)
    return text if len(text) <= MATERIAL_MAX_CHARS else text[:MATERIAL_MAX_CHARS].rstrip() + '\n…'


def _period_material(facts):
    parts = []
    if facts['totals']:
        parts.append('TIME PER APP (the whole period)\n' + '\n'.join('- %s: %s' % (app, tomato_diary.duration_text(s)) for app, s in facts['totals'][:15]))
    if facts['sums']:
        parts.append('SUMS FROM THE COLLECTIONS\n' + '\n'.join(_sum_lines(facts, 'Total')))
    for d in facts['days']:
        f = d['facts']
        weekday = datetime.date.fromisoformat(d['day']).strftime('%a')
        lines = ['%s (%s) — %s in front of the computer: %s' % (d['day'], weekday, tomato_diary.duration_text(d['seconds']),
                                                                 ', '.join('%s %s' % (app, tomato_diary.duration_text(s)) for app, s in f['totals'][:4]))]
        lines += ['  item: %s %s' % (tomato_diary.clock(e['at']), e['text']) for e in f['events']]
        lines += ['  taken:' + line[1:] for line in _taken_lines(f, 'Total', '') if not line.startswith('- **')]
        lines += ['  note: ' + note for note in f['notes']]
        lines += ['  seen: %s %s' % (tomato_diary.clock(v['at']), v['text']) for v in _thin_vision(f['vision'], PERIOD_VISION_PER_DAY)]
        parts.append('\n'.join(lines))
    text = '\n\n'.join(parts)
    return text if len(text) <= PERIOD_MATERIAL_MAX_CHARS else text[:PERIOD_MATERIAL_MAX_CHARS].rstrip() + '\n…'


def prompt(kind, key, template, facts, language='en'):
    kind = kind_of(kind)
    label = period_label(kind, key)
    what = {'day': 'date', 'week': 'dates of the week', 'month': 'month'}[kind]
    return (
        'Write my %(word)s report for %(label)s from the record below. It comes from Tomato, the app that keeps my day.\n'
        '- Write in this language and register: %(language)s. Markdown, in the first person, plainly. Start with a level-1 heading with the %(what)s.\n'
        '- Follow the template: keep its headings in its order; the text under each heading tells you what belongs there.\n'
        '- Use only what the record says. Do not invent meals, thoughts or events; leave a section out when the record has nothing for it.\n'
        '- Do not repeat tables of numbers: Tomato adds its own numbers under your text.\n'
        '- When the report is written, save it with Tomato\'s tool save_daily_report (kind "%(kind)s", day "%(key)s", text = the whole report). '
        'Do not ask me anything; do not change anything else in Tomato.\n\n'
        'TEMPLATE\n--------\n%(template)s\n\nTHE RECORD OF %(label)s\n--------\n%(material)s\n'
    ) % {'word': KIND_WORDS[kind], 'label': label, 'what': what, 'kind': kind, 'key': key, 'language': language_name(language),
         'template': str(template).strip(), 'material': material(facts)}


# ---- reading and writing a report -----------------------------------------------------------------------------

def read_report(data_dir, key, kind='day'):
    """(text without the first-line mark, 'written' | 'numbers' | '', meta {'language': …})."""
    try:
        with open(report_path(data_dir, key, kind), encoding='utf-8') as handle:
            text = handle.read()
    except OSError:
        return '', '', {}
    found = _MARK.match(text)
    if not found:
        return text, 'numbers', {}
    meta = {}
    if found.group(2):
        try:
            meta = json.loads(found.group(2))
        except ValueError:
            meta = {}
    return text[found.end():], found.group(1), meta if isinstance(meta, dict) else {}


def save_report(data_dir, key, text, kind='day'):
    """Writes the report; the one before it is kept once as <key>.before.md."""
    path = report_path(data_dir, key, kind)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        try:
            os.replace(path, path[:-3] + '.before.md')
        except OSError:
            pass
    with open(path + '.tmp', 'w', encoding='utf-8') as handle:
        handle.write(text)
    os.replace(path + '.tmp', path)
    return path


def valid_day(day):
    day = str(day or '').strip()[:10]
    try:
        datetime.datetime.strptime(day, '%Y-%m-%d')
    except ValueError:
        return ''
    return day


# ---- when a report is due -------------------------------------------------------------------------------------

def due_reports(data_dir, diary_dir, now=None):
    """[(kind, key)] that should have a report and have none (days first):
      day    yesterday (Tomato was closed or the Mac asleep at 23:30), and today once it is 23:30;
      week   the last finished week (Monday–Sunday; a week is finished at 23:30 on its Sunday);
      month  the last finished month.
    Only when the diary holds something then."""
    now = now or datetime.datetime.now()
    after = (now.hour, now.minute) >= (REPORT_HOUR, REPORT_MINUTE)
    today = now.date()
    last = today if after else today - datetime.timedelta(days=1)
    due = []
    for day in [today - datetime.timedelta(days=1)] + ([today] if after else []):
        key = day.isoformat()
        if os.path.exists(report_path(data_dir, key, 'day')) or not has_record(diary_dir, key):
            continue
        if not build_facts(tomato_diary.read(diary_dir, key))['empty']:
            due.append(('day', key))
    sunday = last - datetime.timedelta(days=(last.weekday() + 1) % 7)
    month_end = last if (last + datetime.timedelta(days=1)).day == 1 else last.replace(day=1) - datetime.timedelta(days=1)
    for kind, key in (('week', key_for('week', sunday)), ('month', key_for('month', month_end))):
        if os.path.exists(report_path(data_dir, key, kind)):
            continue
        if any(has_record(diary_dir, day) for day in period_days(kind, key)):
            due.append((kind, key))
    return due


def seconds_to_next(now=None):
    """Until the next 23:30."""
    now = now or datetime.datetime.now()
    at = now.replace(hour=REPORT_HOUR, minute=REPORT_MINUTE, second=0, microsecond=0)
    if at <= now:
        at += datetime.timedelta(days=1)
    return (at - now).total_seconds()
