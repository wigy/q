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

    """
    Storage for work log entry.
    """
    def __init__(self, code=None, start=None, stop=None, text=None):
        self.code = code
        self.start = start
        self.stop = stop
        self.text = text

    def __repr__(self):
        return '%s - %s %s %s' % (self.start, self.stop or WorkEntry.PLACEHOLDER, self.code, self.text)

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
        t1 = datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")
        if self.stop:
            t2 = datetime.datetime.strptime(self.stop, "%Y-%m-%d %H:%M:%S")
        else:
            t2 = datetime.datetime.now()
        return (t2 - t1).total_seconds()

    def minutes(self):
        return self.seconds() / 60

    def get_start_stamp(self):
        return self.start.replace(' ', 'T') + '.000+0000'

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
        print TimingMixin.log

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
        self.timing_load()
        return TimingMixin.log

    def _parse_timing_date(self, time):
        if re.match('^\d?\d:\d\d$', time):
            h, m = time.split(':')
            day = strftime('%Y-%m-%d', localtime())
            date = '%s %02d:%02d:00' % (day, int(h), int(m))
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
