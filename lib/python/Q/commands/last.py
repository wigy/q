# -*- coding: UTF-8 -*-
import datetime

from ..error import QError
from ..settings import QSettings
from ..command import Command
from ..ticket import Ticket


class CommandLast(Command):
    """
    Show the latest started and completed tickets.
    """
    def run(self):
        """
        usage: q last [--all]
        """
        from ..q import Q

        if self.opts.get('all'):
            LIMIT = '1900-01-01'
        else:
            LIMIT = str(datetime.date.today() + datetime.timedelta(days=-7))

        results = {}
        for code in Ticket.all_codes():
            self.load(code)
            if self.ticket['Status'] == 'Done':
                date = self.ticket['Finished'][0:10]
                if date >= LIMIT:
                    if date not in results:
                        results[date] = []
                    started = self.ticket['Started'][0:10]
                    if date == started:
                        results[date].append(code + ' ' + self.ticket['Title'] + Q.GREEN + ' [Done]' + Q.END)
                    else:
                        results[date].append(code + ' ' + self.ticket['Title'] + Q.YELLOW + ' [Finished]' + Q.END)
            else:
                date = self.ticket['Started'][0:10]
                if date >= LIMIT:
                    if date not in results:
                        results[date] = []
                    results[date].append(code + ' ' + self.ticket['Title'] + Q.MAGENTA + ' [Started]' + Q.END)
        for title in sorted(results.keys()):
            self.wr(Q.TITLE + "\n" + title + Q.END + "\n")
            for subtitle in sorted(results[title]):
                self.wr('  ' + subtitle)
        self.wr('')
