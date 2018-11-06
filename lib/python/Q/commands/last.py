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
            started = self.ticket['Started'][0:10]
            finished = None
            if self.ticket['Status'] == 'Done':
                finished = self.ticket['Finished'][0:10]

            if finished == started and started >= LIMIT:
                if started not in results:
                    results[started] = []
                results[started].append(code + ' ' + self.ticket['Title'] + Q.MAGENTA + ' [Started and Finished]' + Q.END)
            else:
                if finished >= LIMIT:
                    if finished not in results:
                        results[finished] = []
                    else:
                        results[finished].append(code + ' ' + self.ticket['Title'] + Q.GREEN + ' [Finished]' + Q.END)

                if started >= LIMIT:
                    if started not in results:
                        results[started] = []
                    results[started].append(code + ' ' + self.ticket['Title'] + Q.YELLOW + ' [Started]' + Q.END)

        for title in sorted(results.keys()):
            self.wr(Q.TITLE + "\n" + title + Q.END + "\n")
            for subtitle in sorted(results[title]):
                self.wr('  ' + subtitle)
        self.wr('')
