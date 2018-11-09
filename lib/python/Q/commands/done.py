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
        # Relink old children.
        for code in Ticket.all_codes():
            ticket = self.get_ticket(code)
            if ticket['Base'] == self.ticket['Branch']:
                new_base = self.ticket['Base']
                if not new_base:
                    new_base = QSettings.BASE_BRANCH
                ticket['Base'] = new_base
                ticket.save()

        if self.opts.get('force', False):
            if self.ticket['Status'] == 'Started':
                self.ticket.set_status('Working')
            if self.ticket['Status'] == 'Working':
                self.ticket.set_status('Waiting')
            if self.ticket['Status'] == 'Waiting':
                self.ticket.set_status('Ready')
        self.ticket.set_status('Done')
        self.app.done_work_on_ticket(self.ticket)
        self.ticket.save()
