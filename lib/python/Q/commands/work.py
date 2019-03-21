# -*- coding: UTF-8 -*-
from time import localtime, strftime
from ..error import QError
from ..settings import QSettings
from ..command import AutoLoadCommand
from datetime import datetime
from datetime import timedelta

class CommandWork(AutoLoadCommand):
    """
    Manage work log.
    """
    param_aliases = {
                     'm' : 'merge',
                     's' : 'switch',
                     'p' : 'push'
                    }

    def run(self):
        """
        usage: q work [--today|on [<time>]|off [<time>]|push|switch|merge]
        """
        if not self.app.timing_is_in_use():
            return
        if len(self.args) == 0:
            today = 'today' in self.opts and self.opts['today']
            self.run_show(today=today)
        elif len(self.args) >= 1:
            if self.ticket.code is None:
                raise QError('No ticket.')
            if self.args[0] == 'on':
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
            left = float(QSettings.WORK_HOURS) - sum
            if left:
                self.wr(Q.GREEN + "              Left: %.2fh" % left + Q.END)

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
        left = float(QSettings.WORK_HOURS) - sum
        if left:
            self.wr(Q.GREEN + "              Done: %s" % str(datetime.now() + timedelta(hours=left))[11:11 + 5] + Q.END)

    def run_on(self, time):
        """
        Turn work timer on.
        """
        self.app.timing_on_for_ticket(self.ticket, time)
        self.run_show()

    def run_off(self, time):
        """
        Turn work timer off.
        """
        work = self.ticket.work_timing()
        if len(work) >= 2 and work[-2].can_merge(work[-1]):
            self.run_merge()
        self.app.timing_off_for_ticket(self.ticket, time)
        self.run_show()

    def run_merge(self):
        """
        Merge last two entries.
        """
        log = self.app.timing_get_full_list()
        if len(log) < 2:
            raise QError('Not enough work log entries to merge.')
        if log[-1].code != log[-2].code:
            raise QError('Last two work entries must be from the same tickets in order to merge.')
        self.ticket.work_timing_merge()
        self.app.timing_drop_the_latest()
        self.ticket.save()

    def run_push(self):
        """
        Push work logs.
        """
        self.app.timing_push_ticket(self.ticket)

    def run_switch(self):
        """
        Switch timing on/off or switch to another branch.
        """
        work = self.app.timing_get_the_latest()
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
                time = work.start[0:10] + ' ' + QSettings.WORK_END
                self.app.timing_off_for_ticket(self.ticket, time)
        else:
            if work.is_today():
                # Switch to new task and pick stop time of previous.
                time = work.stop[11:11 + 8]
                self.app.timing_on_for_ticket(self.ticket, time)
            else:
                # Assume morning and start fresh new day.
                self.app.timing_on_for_ticket(self.ticket, QSettings.WORK_START)
