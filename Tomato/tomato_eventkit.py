"""Tomato ⇄ Reminders / Calendar through the system interface (EventKit), without the two apps.

Reading the "Tomato" calendar by asking Calendar.app took 17–28 s for 134 events, and every change went out
as an AppleScript text through `osascript` (seconds each, the "Syncing…" wait). The same reads and changes
through EventKit take hundredths of a second and do not wake Reminders / Calendar.

What it needs: full access to Reminders and to Calendars for the app (Info.plist:
NSRemindersFullAccessUsageDescription, NSCalendarsFullAccessUsageDescription; the system asks once).
Whatever is not granted stays on the old way — `can()` says per operation which way it goes — so nothing
depends on the permission being there.

One store, one lock: the reading thread and the threads that send changes take turns."""
import logging
import threading
import time

try:
    import objc
    from EventKit import EKEventStore, EKReminder, EKEvent, EKAlarm
    from Foundation import NSDate, NSRunLoop, NSCalendar, NSTimeZone, NSBundle
except Exception:      # not macOS, or pyobjc without EventKit: everything stays on the old way
    EKEventStore = None

ENTITY_EVENT, ENTITY_REMINDER = 0, 1
STATUS_NOT_DETERMINED, STATUS_FULL = 0, 3
SPAN_THIS_EVENT = 0
UNITS_TO_MINUTE = 4 | 8 | 16 | 32 | 64 | 128            # year … second
USAGE_KEYS = {ENTITY_EVENT: 'NSCalendarsFullAccessUsageDescription',
              ENTITY_REMINDER: 'NSRemindersFullAccessUsageDescription'}
REMINDER_OPS = ('make_reminder', 'delete_reminder', 'complete_reminder', 'move_reminder', 'purge_completed_reminders')
EVENT_OPS = ('make_event', 'delete_event')
EVENT_SPAN_DAYS = 729          # read this far back and ahead (a search may span four years at most)


def _same(name, other):
    """AppleScript's `name is "…"` does not look at upper / lower case; neither does this."""
    return (name or '').strip().casefold() == (other or '').strip().casefold()


class SystemStore:
    def __init__(self, suffix='', ask=None):
        """suffix: added to the list / calendar names ("Tomato", "Tomato-old"), for tests on a list of
        their own. ask: whether to ask the system for full access; None = only when this app's Info.plist
        carries the sentence the system shows (asking without it is refused, or ends the app)."""
        self.suffix = suffix
        self._ask = ask
        self._lock = threading.RLock()
        self._store = None
        self.reminders_ok = None        # None: not looked at yet (changes go the old way until then)
        self.events_ok = None
        self._logged = set()
        self._observer = None

    # ---- access ----------------------------------------------------------------------------------------
    @staticmethod
    def available():
        return EKEventStore is not None

    def _log_once(self, text):
        if text not in self._logged:
            self._logged.add(text)
            logging.info(text)

    def _may_ask(self, entity):
        if self._ask is not None:
            return bool(self._ask)
        try:
            return bool((NSBundle.mainBundle().infoDictionary() or {}).get(USAGE_KEYS[entity]))
        except Exception:
            return False

    def _wait(self, done, seconds=None):
        """Keep this thread's run loop turning until `done` is set (EventKit answers through it)."""
        deadline = None if seconds is None else time.time() + seconds
        while not done.wait(0.02):
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.02))
            if deadline is not None and time.time() > deadline:
                return False
        return True

    def _request(self, entity):
        status = EKEventStore.authorizationStatusForEntityType_(entity)
        if status not in (STATUS_NOT_DETERMINED, STATUS_FULL):
            return False            # denied, restricted, or write-only
        asking = self._may_ask(entity)
        if not asking:
            # reminders: as it always was (the status alone). events: a status of "allowed" can still mean
            # write-only for an app built some time ago, and only the full-access question tells
            if entity == ENTITY_REMINDER and status == STATUS_FULL:
                return True
            if entity == ENTITY_EVENT:
                return False
        done = threading.Event()
        answer = {'granted': False}

        def handler(granted, error):
            answer['granted'] = bool(granted)
            done.set()

        name = 'requestFullAccessToEventsWithCompletion_' if entity == ENTITY_EVENT else 'requestFullAccessToRemindersWithCompletion_'
        if asking and hasattr(self._store, name):
            getattr(self._store, name)(handler)
        else:
            self._store.requestAccessToEntityType_completion_(entity, handler)
        self._wait(done)            # the system's question stays up until it is answered
        return answer['granted']

    def ensure_access(self):
        """Looks at (and, the first time, asks for) the access. May wait for the system's question: call
        it from the reading thread only."""
        if not self.available():
            self.reminders_ok = self.events_ok = False
            return
        with self._lock:
            try:
                if self._store is None:
                    self._store = EKEventStore.alloc().init()
                reminders_ok = self._request(ENTITY_REMINDER)
                events_ok = self._request(ENTITY_EVENT)
                if events_ok:
                    self._fresh()
                if events_ok and self._calendar(ENTITY_EVENT, 'Tomato') is None:
                    # allowed on paper, but the calendar is not among what the system shows: not full access
                    events_ok = False
                    self._log_once('System interface: no "Tomato" calendar visible; Calendar stays on AppleScript.')
            except Exception:
                logging.exception("EventKit access check failed.")
                self._store = None
                reminders_ok = events_ok = False
            if (reminders_ok, events_ok) != (self.reminders_ok, self.events_ok):
                logging.info("System interface: reminders %s, calendar %s.",
                             'direct' if reminders_ok else 'old way', 'direct' if events_ok else 'old way')
            self.reminders_ok, self.events_ok = reminders_ok, events_ok

    def watch(self, callback):
        """callback() every time the system says that reminders or events changed — in Reminders, in Calendar,
        on another device, or by this app itself. It comes on the main thread, a tenth of a second after the
        change, and only while the main thread's run loop turns (Qt's does). Set up once."""
        if not self.available() or self._observer is not None:
            return self._observer is not None
        try:
            from Foundation import NSNotificationCenter

            def fired(_note):
                try:
                    callback()
                except Exception:
                    logging.exception("System interface: the change notice could not be passed on.")

            self._fired = fired
            self._observer = NSNotificationCenter.defaultCenter().addObserverForName_object_queue_usingBlock_(
                'EKEventStoreChangedNotification', None, None, fired)
        except Exception:
            logging.exception("System interface: change notices are not available.")
            self._observer = None
        return self._observer is not None

    def can(self, ops):
        """Whether every one of these operations can go through the system interface right now."""
        for op in ops:
            if op[0] in REMINDER_OPS:
                if not self.reminders_ok:
                    return False
            elif op[0] in EVENT_OPS:
                if not self.events_ok:
                    return False
            else:
                return False
        return True

    # ---- finding things --------------------------------------------------------------------------------
    def _calendars(self, entity, name):
        title = name + self.suffix
        return [cal for cal in self._store.calendarsForEntityType_(entity) if cal.title() == title]

    def _calendar(self, entity, name):
        found = self._calendars(entity, name)
        writable = [cal for cal in found if cal.allowsContentModifications()]
        return (writable or found or [None])[0]

    def _fetch_reminders(self, calendars):
        done = threading.Event()
        results = []

        def handler(reminders):
            if reminders:
                results.extend(reminders)
            done.set()

        self._store.fetchRemindersMatchingPredicate_completion_(self._store.predicateForRemindersInCalendars_(calendars), handler)
        if not self._wait(done, 60):
            raise RuntimeError('Reminders did not answer.')
        return results

    @staticmethod
    def _due_stamp(reminder):
        components = reminder.dueDateComponents()
        if not components:
            return None
        calendar = components.calendar() or NSCalendar.currentCalendar()
        date = calendar.dateFromComponents_(components)
        return int(date.timeIntervalSince1970()) if date else None

    @staticmethod
    def _date(stamp):
        return NSDate.dateWithTimeIntervalSince1970_(float(stamp))

    def _fresh(self):
        """What other apps (or iCloud) changed since this store last looked."""
        self._store.refreshSourcesIfNecessary()
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.02))

    # ---- reading ---------------------------------------------------------------------------------------
    def read_reminders(self, low, high):
        """[{id, name, stamp, completed}] of the "Tomato" list with a due time between the two stamps, or
        None when the list could not be read (which is not the same as an empty list)."""
        if not self.reminders_ok:
            return None
        with self._lock:
            try:
                self._fresh()
                calendars = self._calendars(ENTITY_REMINDER, 'Tomato')
                if not calendars:
                    return None
                result = []
                for reminder in self._fetch_reminders(calendars):
                    stamp = self._due_stamp(reminder)
                    if stamp is None or stamp < low or stamp > high:
                        continue
                    result.append({'id': reminder.calendarItemIdentifier() or '', 'name': reminder.title() or '',
                                   'stamp': stamp, 'completed': bool(reminder.isCompleted())})
                return result
            except Exception:
                logging.exception("EventKit reminder read failed.")
                self._store = None
                self.reminders_ok = self.events_ok = None
                return None

    def read_events(self, now=None):
        """([{id, name, stamp, duration}], (low, high)) of the "Tomato" calendar — the events that start
        between the two stamps — or (None, None) when it could not be read."""
        if not self.events_ok:
            return None, None
        now = time.time() if now is None else now
        low, high = int(now - EVENT_SPAN_DAYS * 86400), int(now + EVENT_SPAN_DAYS * 86400)
        with self._lock:
            try:
                self._fresh()
                calendars = self._calendars(ENTITY_EVENT, 'Tomato')
                if not calendars:
                    return None, None
                predicate = self._store.predicateForEventsWithStartDate_endDate_calendars_(self._date(low), self._date(high), calendars)
                by_id = {}
                result = []
                for event in self._store.eventsMatchingPredicate_(predicate) or []:
                    start, end = event.startDate(), event.endDate()
                    if not start:
                        continue
                    stamp = int(start.timeIntervalSince1970())
                    if stamp < low or stamp > high:
                        continue        # only overlaps the range
                    # the same identifier Calendar.app gives as uid: what was remembered from the old way of reading still fits
                    entry = {'id': event.calendarItemIdentifier() or '',
                             'name': event.title() or '', 'stamp': stamp,
                             'duration': int(end.timeIntervalSince1970() - stamp) if end else 0}
                    earlier = by_id.get(entry['id']) if entry['id'] else None
                    if earlier is not None:
                        # a repeating event comes once per occurrence; Calendar.app gave it once, at its
                        # first: keep the earliest
                        if stamp < earlier['stamp']:
                            earlier.update(entry)
                        continue
                    if entry['id']:
                        by_id[entry['id']] = entry
                    result.append(entry)
                # a day in from both ends, so that an event at the very edge is never "missing"
                return result, (low + 86400, high - 86400)
            except Exception:
                logging.exception("EventKit calendar read failed.")
                self._store = None
                self.reminders_ok = self.events_ok = None
                return None, None

    # ---- changing --------------------------------------------------------------------------------------
    def _set_due(self, reminder, stamp):
        date = self._date(stamp)
        calendar = NSCalendar.currentCalendar()
        components = calendar.components_fromDate_(UNITS_TO_MINUTE, date)
        components.setSecond_(0)
        components.setTimeZone_(NSTimeZone.localTimeZone())
        reminder.setDueDateComponents_(components)
        # the "remind me" time: one alarm at that moment, as Reminders itself (and AppleScript) set it
        for alarm in list(reminder.alarms() or []):
            reminder.removeAlarm_(alarm)
        reminder.addAlarm_(EKAlarm.alarmWithAbsoluteDate_(date))

    def _matching_events(self, calendar, name, stamp):
        minute = int(stamp) // 60
        predicate = self._store.predicateForEventsWithStartDate_endDate_calendars_(
            self._date(minute * 60 - 1), self._date(minute * 60 + 60), [calendar])
        return [event for event in self._store.eventsMatchingPredicate_(predicate) or []
                if event.startDate() and int(event.startDate().timeIntervalSince1970()) // 60 == minute
                and _same(event.title(), name)]

    def apply(self, ops):
        """Carry the operations out, in order, and save them together. Returns how many were carried out.
        One that fails is logged and left (the next sync pass sees what is really there)."""
        if not ops or not self.available():
            return 0
        with self._lock:
            if self._store is None:
                return 0
            applied = 0
            reminders = None            # the list's reminders, fetched once for all the operations
            dirty = False
            for op in ops:
                try:
                    kind = op[0]
                    if kind in REMINDER_OPS:
                        target = self._calendar(ENTITY_REMINDER, 'Tomato')
                        if target is None:
                            raise RuntimeError('no "Tomato" list')
                        if kind == 'make_reminder':
                            _, name, stamp, notes = op
                            reminder = EKReminder.reminderWithEventStore_(self._store)
                            reminder.setTitle_(name)
                            reminder.setCalendar_(target)
                            if notes:
                                reminder.setNotes_(notes)
                            self._set_due(reminder, stamp)
                            self._check(self._store.saveReminder_commit_error_(reminder, False, None))
                            if reminders is not None:
                                reminders.append(reminder)
                        else:
                            if reminders is None:
                                if dirty:
                                    self._check(self._store.commit_(None))
                                    dirty = False
                                reminders = self._fetch_reminders([target])
                            if kind == 'purge_completed_reminders':
                                hits = [r for r in reminders if r.isCompleted()]
                            else:
                                minute = int(op[2]) // 60
                                hits = [r for r in reminders if _same(r.title(), op[1])
                                        and (self._due_stamp(r) or -60) // 60 == minute]
                            for reminder in hits:
                                if kind == 'complete_reminder':
                                    reminder.setCompleted_(True)
                                    self._check(self._store.saveReminder_commit_error_(reminder, False, None))
                                elif kind == 'move_reminder':
                                    self._set_due(reminder, op[3])
                                    self._check(self._store.saveReminder_commit_error_(reminder, False, None))
                                else:
                                    self._check(self._store.removeReminder_commit_error_(reminder, False, None))
                                    reminders.remove(reminder)
                    elif kind == 'make_event':
                        _, calendar_name, name, stamp, seconds = op
                        target = self._calendar(ENTITY_EVENT, calendar_name)
                        if target is None:
                            raise RuntimeError('no "%s" calendar' % calendar_name)
                        event = EKEvent.eventWithEventStore_(self._store)
                        event.setTitle_(name)
                        event.setCalendar_(target)
                        event.setStartDate_(self._date(stamp))
                        event.setEndDate_(self._date(stamp + seconds))
                        self._check(self._store.saveEvent_span_commit_error_(event, SPAN_THIS_EVENT, False, None))
                    elif kind == 'delete_event':
                        _, calendar_name, name, stamp = op
                        target = self._calendar(ENTITY_EVENT, calendar_name)
                        if target is None:
                            raise RuntimeError('no "%s" calendar' % calendar_name)
                        if dirty:
                            # what this batch made or removed so far has to be in before it is searched
                            self._check(self._store.commit_(None))
                            dirty = False
                        for event in self._matching_events(target, name, stamp):
                            self._check(self._store.removeEvent_span_commit_error_(event, SPAN_THIS_EVENT, False, None))
                    else:
                        continue
                    applied += 1
                    dirty = True
                except Exception:
                    logging.exception("System interface: %s failed.", op[0])
            if dirty:
                try:
                    self._check(self._store.commit_(None))
                except Exception:
                    logging.exception("System interface: saving failed.")
                    with_reset = getattr(self._store, 'reset', None)
                    if with_reset:
                        with_reset()
                    return 0
            return applied

    @staticmethod
    def _check(result):
        ok, error = result if isinstance(result, tuple) else (result, None)
        if not ok:
            raise RuntimeError(str(error) if error is not None else 'refused')


STORE = SystemStore()
