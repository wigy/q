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
        self.ticket.refresh()
        if self.opts.get('force', False):
            if self.ticket['Status'] == 'Started':
                self.ticket.set_status('Working')
            if self.ticket['Status'] in ['Working', 'Reviewing', 'Building', 'Building + Reviewing']:
                self.ticket.set_status('Waiting')
            if self.ticket['Status'] == 'Waiting':
                self.ticket.set_status('Ready')

        self.ticket.set_status('Done')

        # Relink old children in progress.
        for code in Ticket.all_codes():
            ticket = self.get_ticket(code)
            if ticket['Base'] == self.ticket['Branch'] and ticket['Status'] != 'Done':
                new_base = self.ticket['Base']
                if not new_base:
                    new_base = QSettings.BASE_BRANCH
                ticket['Base'] = new_base
                ticket.save()

        # Finish it.
        self.app.done_work_on_ticket(self.ticket)
        if self.app.timing_is_in_use():
            if self.ticket.work_timing_is_on():
                self.Q('work','off')
            log = self.ticket.work_timing()
            if len(log) > 1 and log[-2].can_merge(log[-1]):
                self.Q('work','merge')
            self.Q('work','push')
        self.ticket.save()
