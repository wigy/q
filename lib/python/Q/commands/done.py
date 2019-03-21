# -*- coding: UTF-8 -*-
import time

from ..error import QError
from ..settings import QSettings
from ..command import AutoGoCommand
from ..ticket import Ticket


class CommandDone(AutoGoCommand):
    """
    Mark ticket as completed and update finishing time.
    """
    def run(self):
        """
        usage: q done [<code>] [--force]
        """
        from ..q import Q
        self.ticket.refresh()
        if self.opts.get('force', False):
            if self.ticket['Status'] == 'Started':
                self.ticket.set_status('Working')
            if self.ticket['Status'] in ['Working', 'Reviewing', 'Building', 'Building + Reviewing']:
                self.ticket.set_status('Waiting')
            if self.ticket['Status'] == 'Waiting':
                self.ticket.set_status('Ready')

        # Relink old children in progress.
        for code in Ticket.all_codes():
            ticket = self.get_ticket(code)
            if ticket['Base'] == self.ticket['Branch'] and ticket['Status'] != 'Done':
                new_base = self.ticket['Base']
                if not new_base:
                    new_base = QSettings.BASE_BRANCH
                ticket['Base'] = new_base
                ticket.save()

        self.app.done_work_on_ticket(self.ticket)
        if self.app.timing_is_in_use():
            if self.ticket.work_timing_is_on():
                Q('work','off')
                self.load(self.ticket.code)
                work = self.ticket.work_timing()
                if work[-1].minutes() < 15:
                    self.wr('Merging small work timing entry to the previous.')
                    Q('work', 'merge')
                    self.load(self.ticket.code)
            Q('work','push')
            self.load(self.ticket.code)
        self.ticket.set_status('Done')
        self.ticket.save()
