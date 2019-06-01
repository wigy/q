import re
import os
import pickle
import datetime
from time import localtime, strftime
from .error import QError
from .settings import QSettings
from .ticket import Ticket
from .helper import Curl, Requests

class WorkEntry:

    PLACEHOLDER = '????-??-?? ??:??:??'
    JOIN_LIMIT_MIN = 15

    """
    Storage for work log entry.
    """
    def __init__(self, code=None, start=None, stop=None, text=None):
        self.code = code
        self.start = start
        self.stop = stop
        self.text = text

    def __repr__(self):
        return '<Q.WorkEntry %s - %s %s %s>' % (self.start, self.stop or WorkEntry.PLACEHOLDER, self.code, self.text)

    def human(self):
        """
        Human readable period length.
        """
        ret = ''
        m = self.minutes()
        if m >= 60:
            h = int(m / 60)
            ret += str(h) + 'h '
            m -= 60 * h
        m = int(m)
        ret += str(m) + 'min'
        return ret

    def seconds(self):
        """
        How many seconds of work.
        """
        t1 = datetime.datetime.strptime(self.start, '%Y-%m-%d %H:%M:%S')
        if self.stop:
            t2 = datetime.datetime.strptime(self.stop, '%Y-%m-%d %H:%M:%S')
        else:
            t2 = datetime.datetime.now()
        return (t2 - t1).total_seconds()

    def minutes(self):
        """
        How many minutes of work.
        """
        return self.seconds() / 60

    def get_start_stamp(self):
        """
        Format starting time to ISO-format.
        """
        import time
        tz = -(time.timezone / 3600.0)
        if time.localtime( ).tm_isdst > 0:
            tz += 1
        return self.start.replace(' ', 'T') + ('.000+%02d00' % tz)

    def is_running(self):
        """
        Check if there is stopping time stamp.
        """
        return self.stop is None

    def now(self):
        """
        Current time.
        """
        t =datetime.datetime.now()
        return datetime.datetime.strftime(t, '%H:%M:%S')

    def today(self):
        """
        Current date.
        """
        t =datetime.datetime.now()
        return datetime.datetime.strftime(t, '%Y-%m-%d')

    def is_today(self):
        """
        Check if the starting time is today.
        """
        return self.today() == self.start[0:10]

    def add_comment(self, comment):
        """
        Append a comment.
        """
        if self.text:
            self.text += ' '
            self.text += comment
        else:
            self.text = comment

    def to_ticket(self):
        """
        Convert to string to be used in ticket data.
        """

        return '%s - %s %s' % (self.start, self.stop or WorkEntry.PLACEHOLDER, self.text)

    def can_merge(self, entry):
        """
        Check if it makes sense to combine other work entry.
        """
        if self.code != entry.code:
            return False
        if self.start[0:10] != entry.start[0:10]:
            return False
        if self.minutes() < WorkEntry.JOIN_LIMIT_MIN:
            return True
        if entry.minutes() < WorkEntry.JOIN_LIMIT_MIN:
            return True
        return False

    def merge(self, entry):
        """
        Merge another enrty to this.
        """
        self.start = min(self.start, entry.start)
        if self.stop is None or entry.stop is None:
            self.stop = None
        else:
            self.stop = max(self.stop, entry.stop)
        texts = []
        if self.text is not None:
            texts.append(self.text)
        if entry.text is not None:
            texts.append(entry.text)
        self.text = ' '.join(texts)

    @classmethod
    def from_str(cls, s):
        ret = WorkEntry()
        ret.start = s[0: 19]
        ret.stop = s[22: 22 + 19]
        if ret.stop == WorkEntry.PLACEHOLDER:
            ret.stop = None
        ret.text = s[22 + 19 + 1:]
        return ret


class TimingMixin:
    """
    Base class for work log implementations.
    """

    log = []

    @classmethod
    def path(cls):
        """
        Storage path for work log.
        """
        return os.path.join(QSettings.APPDIR, '.q.work.log')

    def read_from_tickets(self):
        """
        Read work log data from tickets.
        """
        TimingMixin.log = []
        for code in Ticket.all_codes():
            self.cmd.load(code)
            TimingMixin.log += self.cmd.ticket.work_timing()
        TimingMixin.log.sort(key = lambda w: w.start)

    def timing_load(self):
        try:
            with open(TimingMixin.path(), 'rb') as input:
                TimingMixin.log = pickle.load(input)
        except IOError, e:
            self.read_from_tickets()
            self.timing_save()

    def timing_save(self):
        with open(TimingMixin.path(), 'wb') as output:
            pickle.dump(TimingMixin.log, output, pickle.HIGHEST_PROTOCOL)

    def timing_is_in_use(self):
        """
        Determine if we are using the timing system.
        """
        return True

    def timing_get_full_list(self):
        """
        Get the full list of timing records.
        """
        ret = []
        for p in QSettings.visit_all():
            QSettings.load(p)
            self.timing_load()
            ret += TimingMixin.log
        QSettings.visit_done()
        ret.sort(key = lambda w: w.start)
        return ret

    def timing_get_the_latest(self):
        """
        Get the last recorded timing entry or empty record if none.
        """
        self.timing_load()
        if len(TimingMixin.log):
            return TimingMixin.log[-1]
        return None

    def _parse_timing_date(self, time):
        if re.match('^\d?\d:\d\d$', time):
            h, m = time.split(':')
            day = strftime('%Y-%m-%d', localtime())
            date = '%s %02d:%02d:00' % (day, int(h), int(m))
        elif re.match('^\d?\d:\d\d:\d\d$', time):
            h, m, s = time.split(':')
            day = strftime('%Y-%m-%d', localtime())
            date = '%s %02d:%02d:00' % (day, int(h), int(m))
        elif re.match('^\d\d\d\d-\d\d-\d\d \d?\d:\d\d:\d\d$', time):
            date = time
        else:
            raise QError('Invalid time %r' % time)
        return date

    def timing_on_for_ticket(self, ticket, time):
        """
        Put the work log timer on for the ticket.
        """
        date = self._parse_timing_date(time)
        ticket.work_timing_on(date)
        ticket.save()
        self.timing_load()
        TimingMixin.log.append(WorkEntry(code=ticket.code, start=date))
        self.timing_save()

    def timing_off_for_ticket(self, ticket, time):
        """
        Put the work log timer on for the ticket.
        """
        date = self._parse_timing_date(time)
        ticket.work_timing_off(date)
        ticket.save()
        self.timing_load()
        TimingMixin.log[-1].stop = date
        self.timing_save()

    def timing_comment_for_ticket(self, ticket, comment):
        """
        Append the comment for the latest work entry.
        """
        work = self.timing_get_the_latest()
        if ticket.code != work.code:
            raise QError('Cannot comment ticket work log that is not the latest work.')
        ticket.work_timing_comment(comment)
        ticket.save()
        work.add_comment(comment)
        self.timing_save()

    def timing_rebuild_cache(self):
        """
        Drop cache and rebuild from tickets.
        """
        self.read_from_tickets()
        self.timing_save()

    def timing_push_ticket(self, ticket):
        """
        Push the timing data to the remote.
        """
        raise QError("Not implemented in %s: timing_push_ticket().", self.__class__.__name__)


class NoTiming(TimingMixin):
    def timing_is_in_use(self):
        return False


class TimingByAtlassian(TimingMixin):
    """
    Implementation using Atlassian worklog (requires also TicketingByAtlassian).
    """

    def __remove_atlassian_worklog(self, ticket):
        resp = Requests()(QSettings.ATLASSIAN_URL + '/rest/api/3/issue/' + ticket.code + '/worklog', auth=self._ticketing_auth())
        for work in resp.json()['worklogs']:
            Requests()(QSettings.ATLASSIAN_URL + '/rest/api/3/issue/' + ticket.code + '/worklog/' + work['id'], delete=True, auth=self._ticketing_auth())

    def timing_push_ticket(self, ticket):
        self.__remove_atlassian_worklog(ticket)
        for work in ticket.work_timing():
            data = {"timeSpentSeconds": work.seconds(), "started": work.get_start_stamp()}
            ticket.wr('Recording worklog for %d minutes' % work.minutes())
            if work.text is not None:
                data["comment"] = {
                    "type": "doc",
                    "version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [
                            {
                                "text": work.text,
                                "type": "text"
                            }
                        ]
                    }]
                }

            resp = Requests()(QSettings.ATLASSIAN_URL + '/rest/api/3/issue/' + work.code + '/worklog', post=data, auth=self._ticketing_auth())
