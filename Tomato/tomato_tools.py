# -*- coding: utf-8 -*-
"""What Tomato offers an assistant app as tools — the parts that are plain file work (2026-11-23).

Ryan 2026-11-23: "把 Tomato 的所有的这些功能全部都暴露给 Broccoli，作为一个 MCP，他自动就挂上去了……我就可以告诉
Broccoli 说我今天吃了什么东西，然后他就可以自动的去 Tomato 里面查有没有这个食物……把营养成分对应的写到
Tomato 的那个表单里面去".

The service itself is app_mcp_host.py (shared with the other apps); the tools are registered in the main file,
which runs every call on the main thread. Here: reading the items (All.csv), and the Collections (one CSV per
collection, first line = the column names) read and changed as files. A change to the collection that is open
in the window is followed by a reload there (the main file does that).

Plain Python, no Qt (tests: tests_dev/tm_tools_test.py).
"""
import csv
import os
import re

PAGES = {'time': 'TIME_SNS', 'frequency': 'FREQ_SNS', 'memory': 'MEMO_SNS'}
MAX_ROWS = 200
MAX_CELL = 20000


class ToolError(Exception):
    """Words for the model: what was wrong with the request."""


# ---- items (All.csv) ------------------------------------------------------------------------------------------

def read_items(all_csv):
    """[{'page', 'name', 'start', 'length_hours', 'repeat_hours', 'status', 'target_times', 'done_times'}]"""
    items = []
    try:
        with open(all_csv, 'r', encoding='utf8', newline='') as handle:
            rows = list(csv.reader(handle))
    except OSError:
        return items
    kinds = {value: key for key, value in PAGES.items()}
    for row in rows[1:]:
        if len(row) < 8 or row[7] not in kinds:
            continue
        page = kinds[row[7]]
        item = {'page': page, 'name': row[0], 'status': row[4].lower()}
        if page == 'time':
            item.update({'start': row[1], 'length_hours': row[2], 'repeat_hours': None if row[3] in ('', '-') else row[3]})
        elif page == 'frequency':
            item.update({'added': row[1], 'target_times': row[5], 'done_times': row[6]})
        else:
            item['added'] = row[1]
        items.append(item)
    return items


def filter_items(items, page='all', status='undone', text='', start_from='', start_to='', limit=50):
    text = (text or '').casefold().strip()
    found = []
    for item in items:
        if page not in ('', 'all', None) and item['page'] != page:
            continue
        if status not in ('', 'all', None) and item['status'] != status:
            continue
        if text and text not in item['name'].casefold():
            continue
        if (start_from or start_to) and item['page'] == 'time':
            if start_from and item['start'] < start_from:
                continue
            if start_to and item['start'][:len(start_to)] > start_to:
                continue
        found.append(item)
    found.sort(key=lambda item: (item['page'], item.get('start') or item.get('added') or ''))
    limit = max(1, min(int(limit or 50), MAX_ROWS))
    return {'count': len(found), 'items': found[:limit], 'more': max(0, len(found) - limit)}


# ---- collections ----------------------------------------------------------------------------------------------

def _clean_name(name):
    name = ' '.join(str(name or '').split())
    if name.lower().endswith('.csv'):
        name = name[:-4]
    if not name or name.startswith('.') or re.search(r'[/\\:\x00]', name) or len(name) > 80:
        raise ToolError('A collection name is 1–80 characters without / \\ :')
    return name


def collection_names(folder):
    try:
        return sorted(name[:-4] for name in os.listdir(folder) if name.lower().endswith('.csv') and not name.startswith('.'))
    except OSError:
        return []


def collection_path(folder, name, must_exist=True):
    name = _clean_name(name)
    for existing in collection_names(folder):
        if existing.casefold() == name.casefold():
            return os.path.join(folder, existing + '.csv')
    if must_exist:
        raise ToolError('There is no collection named "%s". The collections are: %s' % (
            name, ', '.join(collection_names(folder)) or '(none)'))
    return os.path.join(folder, name + '.csv')


def read_collection(path):
    """(columns, rows) — every row as long as the columns."""
    with open(path, 'r', encoding='utf-8', newline='') as handle:
        lines = list(csv.reader(handle))
    columns = lines[0] if lines else []
    rows = [(line + [''] * len(columns))[:max(len(columns), 0)] for line in lines[1:]]
    return columns, rows


def write_collection(path, columns, rows):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    os.replace(tmp, path)


def list_collections(folder):
    result = []
    for name in collection_names(folder):
        try:
            columns, rows = read_collection(os.path.join(folder, name + '.csv'))
        except (OSError, csv.Error, UnicodeDecodeError):
            continue
        result.append({'collection': name, 'columns': columns, 'rows': len(rows)})
    return result


def _row_dict(columns, row, number, short=0):
    values = {}
    for column, value in zip(columns, row):
        if value == '':
            continue
        values[column] = value if not short or len(value) <= short else value[:short] + '…'
    return {'row': number, 'values': values}


def search_collection(folder, name, text='', limit=20):
    """Rows whose any cell holds every word of `text` (no text = the first rows). Row numbers start at 1 and are
    what update_row() takes. Long cells are cut; read_row() gives one row in full."""
    path = collection_path(folder, name)
    columns, rows = read_collection(path)
    words = [word for word in (text or '').casefold().split() if word]
    found = []
    for number, row in enumerate(rows, start=1):
        hay = ' \n'.join(row).casefold()
        if all(word in hay for word in words):
            found.append(_row_dict(columns, row, number, short=300))
    limit = max(1, min(int(limit or 20), MAX_ROWS))
    return {'collection': os.path.basename(path)[:-4], 'columns': columns, 'count': len(found),
            'rows': found[:limit], 'more': max(0, len(found) - limit)}


def read_row(folder, name, row):
    path = collection_path(folder, name)
    columns, rows = read_collection(path)
    number = _row_number(row, rows)
    return _row_dict(columns, rows[number - 1], number)


def _row_number(row, rows):
    try:
        number = int(row)
    except (TypeError, ValueError):
        raise ToolError('"row" is the row number search_collection gave.')
    if not 1 <= number <= len(rows):
        raise ToolError('There is no row %s; the collection has %d rows.' % (row, len(rows)))
    return number


def _values(values, columns, add_columns):
    """{column: text} checked against the columns; unknown columns are added only when add_columns is set."""
    if not isinstance(values, dict) or not values:
        raise ToolError('"values" is an object of column name → text, with at least one entry.')
    known = {column.casefold(): index for index, column in enumerate(columns)}
    placed, new = {}, []
    for key, value in values.items():
        key = ' '.join(str(key).split())
        text = '' if value is None else str(value)
        if len(text) > MAX_CELL:
            raise ToolError('The text for "%s" is too long.' % key)
        if key.casefold() in known:
            placed[known[key.casefold()]] = text
        elif add_columns and key:
            new.append((key, text))
        else:
            raise ToolError('There is no column "%s". The columns are: %s. Pass add_missing_columns: true to add it '
                            '(ask the person first).' % (key, ', '.join(columns)))
    return placed, new


def _apply(columns, rows, row, placed, new):
    for key, text in new:
        columns.append(key)
        for other in rows:
            other.append('')
        if row is not None:
            row[-1] = text
    for index, text in placed.items():
        row[index] = text


def add_row(folder, name, values, add_missing_columns=False):
    path = collection_path(folder, name)
    columns, rows = read_collection(path)
    placed, new = _values(values, columns, add_missing_columns)
    row = [''] * len(columns)
    rows.append(row)
    _apply(columns, rows, row, placed, new)
    write_collection(path, columns, rows)
    return path, _row_dict(columns, row, len(rows))


def update_row(folder, name, row, values, add_missing_columns=False):
    path = collection_path(folder, name)
    columns, rows = read_collection(path)
    number = _row_number(row, rows)
    placed, new = _values(values, columns, add_missing_columns)
    _apply(columns, rows, rows[number - 1], placed, new)
    write_collection(path, columns, rows)
    return path, _row_dict(columns, rows[number - 1], number)


def delete_row(folder, name, row):
    path = collection_path(folder, name)
    columns, rows = read_collection(path)
    number = _row_number(row, rows)
    gone = _row_dict(columns, rows.pop(number - 1), number)
    write_collection(path, columns, rows)
    return path, gone


def create_collection(folder, name, columns):
    name = _clean_name(name)
    if any(existing.casefold() == name.casefold() for existing in collection_names(folder)):
        raise ToolError('There is already a collection named "%s".' % name)
    columns = [' '.join(str(column).split()) for column in (columns or []) if str(column).strip()]
    if not columns:
        raise ToolError('"columns" lists the column names, at least one.')
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name + '.csv')
    write_collection(path, columns, [])
    return path


def _column_name(column):
    column = ' '.join(str(column or '').split())
    if not column or len(column) > 80:
        raise ToolError('A column name is 1–80 characters.')
    return column


def _column_index(columns, column):
    wanted = ' '.join(str(column or '').split()).casefold()
    for index, existing in enumerate(columns):
        if existing.casefold() == wanted:
            return index
    raise ToolError('There is no column "%s". The columns are: %s' % (column, ', '.join(columns)))


def add_column(folder, name, column):
    path = collection_path(folder, name)
    columns, rows = read_collection(path)
    column = _column_name(column)
    if any(existing.casefold() == column.casefold() for existing in columns):
        raise ToolError('There is already a column "%s".' % column)
    _apply(columns, rows, None, {}, [(column, '')])
    write_collection(path, columns, rows)
    return path, columns


def rename_column(folder, name, column, new_name):
    path = collection_path(folder, name)
    columns, rows = read_collection(path)
    index = _column_index(columns, column)
    new_name = _column_name(new_name)
    if any(existing.casefold() == new_name.casefold() for i, existing in enumerate(columns) if i != index):
        raise ToolError('There is already a column "%s".' % new_name)
    columns[index] = new_name
    write_collection(path, columns, rows)
    return path, columns


def delete_column(folder, name, column):
    """The column goes with everything in it. → (path, columns, how many cells held something)."""
    path = collection_path(folder, name)
    columns, rows = read_collection(path)
    index = _column_index(columns, column)
    if len(columns) == 1:
        raise ToolError('That is the only column; a collection keeps at least one.')
    filled = sum(1 for row in rows if row[index] != '')
    del columns[index]
    for row in rows:
        del row[index]
    write_collection(path, columns, rows)
    return path, columns, filled


def search_diary(folder, text, days=30, limit=50, today=None):
    """Diary lines of the last `days` days that hold every word of `text`, newest day first."""
    import datetime
    words = [word for word in (text or '').casefold().split() if word]
    if not words:
        raise ToolError('"text" says what to look for.')
    days = max(1, min(int(days or 30), 3660))
    limit = max(1, min(int(limit or 50), MAX_ROWS))
    today = today or datetime.date.today()
    found, more = [], 0
    for back in range(days):
        day = (today - datetime.timedelta(days=back)).strftime('%Y-%m-%d')
        try:
            with open(os.path.join(folder, day + ' diary.md'), encoding='utf-8') as handle:
                lines = handle.read().split('\n')
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            hay = line.casefold()
            if all(word in hay for word in words):
                if len(found) < limit:
                    found.append({'day': day, 'line': line if len(line) <= 400 else line[:400] + '…'})
                else:
                    more += 1
    return {'count': len(found) + more, 'lines': found, 'more': more}


def row_title(columns, row):
    """What a row is called in the diary: its first cell that reads like a name — not empty, one short line, not a
    picture, a link or a file."""
    for value in row:
        value = str(value).strip()
        if not value or '\n' in value or len(value) > 80 or value.startswith(('http://', 'https://', '/', '![', '<', '~/')):
            continue
        return ' '.join(value.split())
    return ''
