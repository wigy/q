# -*- coding: UTF-8 -*-

from ..error import QError
from ..command import AutoLoadCommand

class CommandReopen(AutoLoadCommand):
    """
    Mark finished ticket back to the actively working.
    """
    def run(self):
        """
        usage: q reopen [<code>]
        """
        from ..q import Q
        self.app.reopen_work_on_ticket(self.ticket)
        self.ticket.delete('Finished')
        self.ticket.delete('Build Result')
        self.ticket.delete('Build ID')
        self.ticket.delete('Review Result')
        self.ticket.delete('Review ID')
        self.ticket.set_status("Working")
        self.ticket.save()
        self.Q('go', self.ticket.code)
