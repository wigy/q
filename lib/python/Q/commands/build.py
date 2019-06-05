# -*- coding: UTF-8 -*-
import time

from ..error import QError
from ..settings import QSettings
from ..command import AutoGoCommand
from ..helper import Git


class CommandBuild(AutoGoCommand):
    """
    Send the ticket for building test.
    """
    param_aliases = {
                     'm' : 'make',
                     'd' : 'drop',
                     'u' : 'update',
                     }

    def run(self):
        """
        usage: q build [<code>] [make|update|drop|success]
        """
        if not self.args:
            self.run_status()
        elif self.args[0] == 'make':
            self.run_make()
        elif self.args[0] == 'update':
            self.run_update()
        elif self.args[0] == 'drop':
            self.run_drop()
        elif self.args[0] == 'success':
            self.run_success()
        elif self.args[0] == 'fail':
            self.run_fail()
        else:
            raise QError("Invalid argument '%s'.",self.args[0])

    def run_status(self):
        from ..q import Q
        self.ticket.refresh()
        if self.ticket['Build Result']:
            self.wr(Q.TITLE+'Build Result:'+Q.END)
            self.wr(self.ticket['Build Result'])
            self.wr(Q.TITLE+'Build ID:'+Q.END)
            self.wr(self.ticket['Build ID'])
            url = self.app.build_url(self.ticket)
            if not url is None:
                self.wr(Q.TITLE+'Build URL:'+Q.END)
                self.wr(url)
        else:
            self.wr("No build attempted. You can try "+Q.COMMAND+"q build make"+Q.END+" to start one.")

    def run_drop(self):
        self.ticket.delete('Build ID')
        self.ticket.delete('Build Result')
        self.ticket.delete('Build Info')
        self.ticket.set_status('Working')
        self.ticket.save()

    def run_make(self):
        if self.ticket['Status'] == 'Started':
            self.ticket.set_status('Working')
        self.readyness_check()
        from ..q import Q
        if not self.ticket['Build ID'] is None:
            raise QError("Ticket has already build %r. Use " + Q.COMMAND + "q build update" + Q.ERROR + " to rebuild.", self.ticket['Build ID'])
        self.Q('my','revert')
        self._do_build()
        self.Q('my','apply')

    def run_update(self):
        self.readyness_check()
        from ..q import Q
        if self.ticket['Build ID'] is None:
            raise QError("Cannot update without any earlier builds.")
        self.Q('my','revert')
        self._do_build()
        if not self.ticket['Review ID'] is None:
            self.app.review_update_build(self.ticket)
        self.Q('my','apply')

    def _do_build(self):
        from ..q import Q
        if self.app.build_needs_publish():
            self.Q('publish')
        cid = Git().latest_commit()
        bid = self.app.build_start(self.ticket, cid)
        if bid is None:
            raise QError("Launching the build failed.")
        self.ticket.set_status('Building')
        self.ticket['Build Result'] = 'Pending'
        self.ticket['Build ID'] = bid
        self.ticket.save()

    def run_success(self):
        self.wr("Marking the ticket as successfully built.")
        self.ticket['Build Result'] = 'Success'
        self.ticket.set_status('End Building')
        self.ticket.save()

    def run_fail(self):
        self.wr("Marking the ticket as build failed.")
        self.ticket['Build Result'] = 'Fail'
        self.ticket.set_status('End Building')
        self.ticket.set_status('Working')
        self.ticket.save()
