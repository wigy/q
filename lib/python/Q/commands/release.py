# -*- coding: UTF-8 -*-
import time

from ..error import QError
from ..settings import QSettings
from ..command import AutoGoCommand
from ..helper import Git


class CommandRelease(AutoGoCommand):
    """
    Release a ticket that is reedy.
    """

    def run(self):
        """
        usage: q release [<code>]
        """
        self.ticket.refresh()
        if self.ticket['Status'] != 'Ready':
            raise QError("Cannot release when ticket status is %r.", self.ticket['Status'])
        self.run_release()

    def run_release(self):
        if not self.app.release_ticket(self.ticket):
            raise QError("Releasing process returned false.")
