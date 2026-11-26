---
name: tomato-schedule
description: Use when the user wants the assistant itself to DO something later or repeatedly on its own ("every Monday at 9 do …", "tomorrow at 8 summarise …", "每周一帮我…", "每天早上自动…", "定时任务", "毎週…して"), or wants to see, change or delete such a scheduled task. Keep using it on every following turn of the same conversation until the task is written or dropped. NOT for "remind me to …" (the user does the thing — that is a reminder), and not for doing something right now.
---

# Scheduled tasks through Tomato

Tomato is the timing app on this Mac. You cannot run anything later by yourself; Tomato can. At the scheduled time
Tomato opens a **new** conversation with you and sends the full text of the task's `task.md` as the request. Your job in
this skill is to agree the task with the user and then write it down as a task folder. You do not perform the task now.

Never use a system reminder, a calendar event, cron, launchd or a shell loop for this. Reminders are only for things
the user will do personally.

## Where tasks live

`~/Library/Application Support/com.ryanthehito.broccoli/BroccoliAppPath/ScheduledTasks/<task name>/`

- `task.md` — the instructions you will receive at each run.
- `schedule.json` — when Tomato should run it.
- `runs/` — where a run puts files it wants to keep (created by the run, not now).

Do not touch `ScheduledTasks/_schedulers/`. If `ScheduledTasks/_schedulers/Tomato.json` does not exist, Tomato is not
installed or has never run: tell the user so and stop — do not write anything.

## Step 1 — understand before writing (no code in this step)

Unless the user has already answered them, ask — briefly, in one message, in the user's language — whatever is still
unclear of:

1. What exactly should be done each time, and what counts as finished?
2. Which files, folders, sites or apps does it read, and which may it change?
3. What must it never do (send messages, delete, pay, post, touch other folders …)?
4. Where should the result go (the answer in the conversation, a file — which path —, a note …)?
5. When: first date and time, and does it repeat (daily, weekly, every N hours), until when?

Ask only what you really need; if the request is already complete, skip straight to step 2. If the request says the
time is already set in Tomato (a draft: `schedule.json` exists and `task.md` does not), do not ask about the time.

## Step 2 — show it, get a yes (no code in this step)

Show the user, in their language:

- the task name (short; a folder name: no `/ \ :`, not starting with `.` or `_`, at most 80 characters),
- the schedule in plain words ("every Monday 09:00 from 2026-11-23, no end date"),
- the full text of `task.md` as you intend to save it.

Then ask whether to save it. Write nothing until the user clearly agrees in a later message. If they ask for changes,
show the changed version and ask again.

Tell the user once, in one or two sentences: the task only runs while Tomato is open; a time missed by more than a day
is skipped; and a step that needs approval will wait for them at the Mac unless auto-approve is on.

## How to write task.md

At run time you will have no memory of this conversation. Each run is a new conversation in a group named after
the task, where the group's models and auto-approve setting apply. `task.md` must stand on its own:

- Start with one line saying what this is: `Scheduled task "<name>" — runs <schedule in words>.`
- **Goal** — the outcome wanted.
- **Steps** — numbered, concrete, with full paths and exact names; no "as discussed", no "the usual file".
- **Do not** — the limits the user gave, plus: do not ask the user questions unless blocked; do not schedule anything.
- **Result** — where the result goes and in what form. Files to keep go in this task's `runs/` folder, named with the
  date (`runs/2026-11-23 report.md`), unless the user named another place.
- **If something is missing or fails** — say what was missing in the answer and stop; do not guess.
- **Notes between runs** — every run is a new conversation that remembers nothing. So `task.md` always contains
  these two steps, with the task's real full path written out: as the first step, "read
  `<task folder>/runs/notes.md` if it exists — it says what earlier runs did and what to watch for"; as the last
  step, "add a dated entry of a few lines to `<task folder>/runs/notes.md` (create it if missing): what was done
  this time, anything the next run should know; keep older entries, and when the file passes about 200 lines
  shorten the oldest ones into a summary". Leave both out only if the user says the runs are unrelated.

Write it in the language the user used. Keep it as long as it needs to be, not longer.

## Step 3 — save (only after the yes): one Python code block

Run one Python code block that does all of this, then report what its output says:

```python
import json, os, time
root = os.path.expanduser('~/Library/Application Support/com.ryanthehito.broccoli/BroccoliAppPath/ScheduledTasks')
name = 'TASK NAME'
if not os.path.isfile(os.path.join(root, '_schedulers', 'Tomato.json')):
    raise SystemExit('Tomato is not set up on this Mac: nothing written')
folder = os.path.join(root, name)
os.makedirs(folder, exist_ok=True)
schedule_path = os.path.join(folder, 'schedule.json')
if not os.path.exists(schedule_path):          # a draft made in Tomato already has its time: leave it
    schedule = {
        'version': 1,
        'scheduler': 'Tomato',
        'start': '2026-11-23 09:00',           # local time, YYYY-MM-DD HH:MM, in the future
        'length_hours': 1,
        'repeat_hours': 168,                   # None = once; 24 = daily; 168 = weekly; any number of hours
        'repeat_until': None,                  # or 'YYYY-MM-DD'
        'created_by': 'Broccoli',
        'created_at': time.strftime('%Y-%m-%d %H:%M'),
    }
    with open(schedule_path + '.tmp', 'w', encoding='utf-8') as handle:
        json.dump(schedule, handle, ensure_ascii=False, indent=1)
    os.replace(schedule_path + '.tmp', schedule_path)
task_text = """FULL TEXT OF task.md"""
with open(os.path.join(folder, 'task.md.tmp'), 'w', encoding='utf-8') as handle:
    handle.write(task_text)
os.replace(os.path.join(folder, 'task.md.tmp'), os.path.join(folder, 'task.md'))   # task.md last: it is the "go"
print('saved', folder, sorted(os.listdir(folder)))
```

Rules for the block: `schedule.json` first, `task.md` last (Tomato puts the task on its table when `task.md` appears);
monthly or "every weekday" cannot be expressed in `repeat_hours` — say so and offer the nearest thing (weekly, or one
task per weekday). After it prints `saved`, tell the user the task is saved and that it shows up in Tomato's Time page
as `@Broccoli <task name>` within a few seconds. If it raised, tell the user what it said; do not claim it was saved.

## Looking at, changing, deleting tasks

- List: read the folder names under `ScheduledTasks/` (skip names starting with `_` or `.`) and each `schedule.json`;
  a folder without `task.md` is a draft.
- Change the instructions: show the new `task.md`, get a yes, rewrite `task.md` only.
- Change the time: show the new schedule, get a yes, rewrite `schedule.json` (Tomato replaces the pending items).
- Delete: get a yes, then remove the task's folder (Tomato removes its pending items). Never delete `runs/` of another
  task or anything outside `ScheduledTasks/`.
