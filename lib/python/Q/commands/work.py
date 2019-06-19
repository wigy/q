# -*- coding: UTF-8 -*-
import re

from time import localtime, strftime
from ..error import QError
from ..command import AutoLoadCommand
from datetime import datetime
from datetime import timedelta

class CommandWork(AutoLoadCommand):
    """
    Manage work log.
    """
    param_aliases = {
                     'c' : 'comment',
                     'd' : 'drop',
                     'm' : 'merge',
                     's' : 'switch',
                     'p' : 'push'
                    }

    def run(self):
        """
        usage: q work [--today|on [<time>]|off [<time>]|push|switch|merge|comment|drop]
        """
        if not self.app.timing_is_in_use():
            return
        if len(self.args) == 0:
            today = 'today' in self.opts and self.opts['today']
            self.run_show(today=today)
        elif len(self.args) >= 1:
            if self.args[0] == 'on':
                if self.ticket.code is None:
                    raise QError('No ticket.')
                time = self.args[1] if len(self.args) >= 2 else strftime('%H:%M', localtime())
                self.run_on(time)
            elif self.args[0] == 'off':
                time = self.args[1] if len(self.args) >= 2 else strftime('%H:%M', localtime())
                self.run_off(time)
            elif self.args[0] == 'push':
                self.run_push()
            elif self.args[0] == 'switch':
                self.run_switch()
            elif self.args[0] == 'merge':
                self.run_merge()
            elif self.args[0] == 'comment':
                self.run_comment()
            elif self.args[0] == 'drop':
                self.run_drop()
            else:
                raise QError('Invalid argument.')

    def run_show(self, today=None):
        """
        Display current list.
        """
        from ..q import Q
        log = self.app.timing_get_full_list()
        last_date = None

        sum = 0
        left = 0
        def show_sum():
            self.wr(Q.GREEN + "              Total: %.2fh" % sum + Q.END)
            left = float(self.settings.WORK_HOURS) - sum
            if left:
                self.wr(Q.GREEN + "              Left: %.2fh (%d min)" % (left, left * 60) + Q.END)
        for e in log:
            date, time = e.start.split(' ')
            if today and date != log[0].today():
                continue
            if date != last_date:
                last_date = date
                if sum:
                    show_sum()
                sum = 0
                self.wr(Q.DATE + date + Q.END)
            if e.stop:
                date2, time2 = e.stop.split(' ')
            else:
                time2 = '        '
            text = '' if e.text is None else e.text
            self.wr(Q.TIME + time[0:5] + ' - ' + time2[0:5] + ' ' +  Q.END + e.code + '\t' + e.human() + '  ' + text)
            sum += e.minutes() / 60
        show_sum()
        left = float(self.settings.WORK_HOURS) - sum
        if left:
            self.wr(Q.GREEN + "              Done: %s" % str(datetime.now() + timedelta(hours=left))[11:11 + 5] + Q.END)

    def run_on(self, time):
        """
        Turn work timer on.
        """
        self.app.timing_on_for_ticket(self.ticket, time)
        self.run_show(today=True)

    def run_off(self, time):
        """
        Turn work timer off.
        """
        if not self.ticket.code:
            work = self.app.timing_get_the_latest()
            self.wr('Note: no ticket loaded, using the latest one worked on.')
            self.load(work.code)
        work = self.ticket.work_timing()
        self.app.timing_off_for_ticket(self.ticket, time)
        self.run_show(today=True)

    def run_merge(self):
        """
        Merge last two entries.
        """
        log = self.app.timing_get_full_list()
        if len(log) < 2:
            return
        self.load(log[-1].code)
        if not log[-2].can_merge(log[-1]):
            raise QError('Cannot merge latest two work entries.')
        self.ticket.work_timing_merge()
        self.ticket.save()

    def run_drop(self):
        """
        Drop the last entry.
        """
        log = self.app.timing_get_full_list()
        if len(log) < 1:
            raise QError('No work entries.')
        self.load(log[-1].code)
        self.ticket.work_timing_drop()
        self.ticket.save()

    def run_push(self):
        """
        Push work logs.
        """
        date = strftime('%Y-%m-%d', localtime())
        log = self.app.timing_get_full_list(date = date)
        codes = set()
        if len(self.args) > 1:
            code = self.args[1]
            if not re.match(self.settings.TICKET_NUMBER_REGEX, code):
                code = self.app.num2code(code)
            codes.add(code)
        else:
            for w in log:
                codes.add(w.code)
        for code in codes:
            self.load(code)
            self.app.timing_push_ticket(self.ticket)

    def run_switch(self):
        """
        Switch timing on/off or switch to another branch.
        """
        work = self.app.timing_get_the_latest()
        if not self.ticket.code:
            self.wr('Note: no ticket loaded, using the latest one worked on.')
            self.load(work.code)
        time = work.now()
        if work.is_running():
            if work.is_today():
                if self.ticket.code == work.code:
                    # Same ticket, just start a new entry.
                    self.app.timing_off_for_ticket(self.ticket, time)
                    self.app.timing_on_for_ticket(self.ticket, time)
                else:
                    # Ticket has changed, switch to it.
                    code = self.ticket.code
                    self.load(work.code)
                    self.app.timing_off_for_ticket(self.ticket, time)
                    self.load(code)
                    self.app.timing_on_for_ticket(self.ticket, time)
            else:
                time = work.start[0:10] + ' ' + self.settings.WORK_END
                self.app.timing_off_for_ticket(self.ticket, time)
        else:
            if work.is_today():
                # Switch to new task and pick stop time of previous.
                time = work.stop[11:11 + 8]
                self.app.timing_on_for_ticket(self.ticket, time)
            else:
                # Assume morning and start fresh new day.
                self.app.timing_on_for_ticket(self.ticket, self.settings.WORK_START)

    def run_comment(self):
        """
        Append to the comment of the last entry.
        """
        work = self.app.timing_get_the_latest()
        if work is None:
            raise QError('No work timing entries.')
        if not self.ticket.code:
            self.wr('Note: no ticket loaded, using the latest one worked on.')
            self.load(work.code)
        comment = ' '.join(self.args[1:])
        if not len(comment):
            raise QError('Empty comment.')
        self.app.timing_comment_for_ticket(self.ticket, comment)
