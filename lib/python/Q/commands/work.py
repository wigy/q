# -*- coding: UTF-8 -*-
from time import localtime, strftime
from ..error import QError
from ..settings import QSettings
from ..command import AutoLoadCommand

class CommandWork(AutoLoadCommand):
    """
    Manage work log.
    """
    param_aliases = {
                     'p' : 'push'
                     }

    def run(self):
        """
        usage: q work [on [<time>]|off [<time>]|push]
        """
        if not self.app.timing_is_in_use():
            return
        if len(self.args) == 0:
            self.run_show()
        elif len(self.args) >= 1:
            if self.args[0] == 'on':
                time = self.args[1] if len(self.args) >= 2 else strftime('%H:%M', localtime())
                self.run_on(time)
            elif self.args[0] == 'off':
                time = self.args[1] if len(self.args) >= 2 else strftime('%H:%M', localtime())
                self.run_off(time)
            elif self.args[0] == 'push':
                self.run_push()
            else:
                raise QError('Invalid argument.')

    def run_show(self):
        """
        Display current list.
        """
        from ..q import Q
        log = self.app.timing_get_full_list()
        last_date = None
        sum = 0
        for e in log:
            date, time = e.start.split(' ')
            if date != last_date:
                last_date = date
                self.wr(Q.DATE + date + Q.END)
            if e.stop:
                date2, time2 = e.stop.split(' ')
            else:
                time2 = '        '
            self.wr(Q.TIME + time[0:5] + ' - ' + time2[0:5] + ' ' +  Q.END + e.code + '\t' + e.human() + '  ' + e.text)
            sum += e.minutes() / 60
        self.wr(Q.GREEN + "              Total: %.2fh" % sum + Q.END)

    def run_on(self, time):
        """
        Turn work timer on.
        """
        if self.ticket.code is None:
            raise QError('No ticket.')
        self.app.timing_on_for_ticket(self.ticket, time)
        self.run_show()

    def run_off(self, time):
        """
        Turn work timer off.
        """
        if self.ticket.code is None:
            raise QError('No ticket.')
        self.app.timing_off_for_ticket(self.ticket, time)
        self.run_show()

    def run_push(self):
        """
        Push work logs.
        """
        if self.ticket.code is None:
            raise QError('No ticket.')
        self.app.timing_push_ticket(self.ticket)
