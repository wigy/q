# -*- coding: UTF-8 -*-
import time

from ..error import QError
from ..settings import QSettings
from ..command import AutoGoCommand

class CommandCancel(AutoGoCommand):
    """
    Mark ticket finished but not done.
    """
    def run(self):
        """
        usage: q cancel [<code>]
        """
        self.app.cancel_work_on_ticket(self.ticket)
        self.ticket.set_status("Canceled")
        self.ticket['Finished'] = time.strftime('%Y-%m-%d %H:%M')
        self.ticket.save()
