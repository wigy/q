# -*- coding: UTF-8 -*-
import time

from ..error import QError
from ..settings import QSettings
from ..command import AutoGoCommand
from ..helper import Git


class CommandReview(AutoGoCommand):
    """
    Set up review board request or view the latest.
    """
    param_aliases = {
                     'm' : 'make',
                     'd' : 'drop',
                     'u' : 'update',
                     }

    def run(self):
        """
        usage: q review [<code>] [[--force] make|drop|success|fail]
        """
        from ..q import Q
        if self.args and (self.args[0] == 'make'):
            self.run_make()
            return
        if self.args and (self.args[0] == 'drop'):
            self.run_drop()
            return
        if self.args and (self.args[0] == 'success'):
            self.run_success()
            return
        if self.args and (self.args[0] == 'fail'):
            self.run_fail()
            return
        if self.args and (self.args[0] == 'pending'):
            self.run_pending()
            return
        if self.args and (self.args[0] == 'update'):
            self.run_update()
            return
        version = self.ticket.reviews()
        if version == 0:
            self.wr("No reviews.")
            self.wr("Create new review with "+Q.COMMAND+"q review make"+Q.END+".")
            return

        self.run_show()

    def run_show(self):
        from ..q import Q
        self.ticket.refresh()
        if self.ticket['Review Result']:
            self.wr(Q.TITLE+'Review Result:'+Q.END)
            self.wr(self.ticket['Review Result'])
            self.wr(Q.TITLE+'Review ID:'+Q.END)
            self.wr(self.ticket['Review ID'])
            if self.ticket['Review Info']:
                self.wr(Q.TITLE+'Review Info:'+Q.END)
                self.wr(self.ticket['Review Info'])
            url = self.app.review_url(self.ticket['Review ID'])
            if not url is None:
                self.wr(Q.TITLE+'Review URL:'+Q.END)
                self.wr(url)
        else:
            self.wr("No review attempted. You can try "+Q.COMMAND+"q review make"+Q.END+" to start one.")

    def run_drop(self):
        self.ticket.delete('Review ID')
        self.ticket.delete('Review Result')
        self.ticket.delete('Review Info')
        self.ticket.set_status('Working')
        self.ticket.save()

    def run_make(self):
        from ..q import Q
        if not self.ticket['Review ID'] is None:
            raise QError("Ticket has already review %r pending.", self.ticket['Review ID'])
        if not self.opts.get('force') and QSettings.REVIEW_NEEDS_BUILD and self.ticket['Build ID'] is None:
            raise QError("Cannot create review before you have build on-going.")
        Q('update')
        Q('publish')
        Q('my','revert')
        file = self._make_diff()
        rid = self.app.review_start(self.ticket, file)
        if rid is None:
            raise QError("Launching the review failed.")
        self.ticket.set_status('Reviewing')
        self.ticket['Review Result'] = 'Pending'
        self.ticket['Review ID'] = rid
        self.ticket.save()
        self.app.start_review_on_ticket(self.ticket, self.app.review_url(rid))
        Q('my','apply')
        self.wr("Review is ready!")
        self.wr("Please check it out and fine tune if needed: " + Q.URL + self.app.review_url(rid) + Q.END)

    def _make_diff(self):
        merge_base = self.ticket.merge_base()
        version = self.ticket.reviews() + 1
        file = self.ticket.path("review-"+str(version)+".diff")
        Git()('diff '+merge_base+" > "+file)
        return file

    def run_update(self):
        from ..q import Q
        rid = self.ticket['Review ID']
        if rid is None:
            raise QError("Ticket has not yet review.")
        Q('publish')
        Q('my','revert')
        file = self._make_diff()
        self.app.review_update(self.ticket, file)
        Q('my','apply')
        self.wr("Review is updated!")
        self.wr("Please check it out and fine tune if needed: " + Q.URL + self.app.review_url(rid) + Q.END)

    def run_success(self):
        self.wr("Marking the ticket as successfully reviewed.")
        self.ticket['Review Result'] = 'Success'
        self.ticket.set_status('End Reviewing')
        self.ticket.save()

    def run_fail(self):
        self.wr("Marking the ticket as failed review.")
        self.ticket['Review Result'] = 'Fail'
        self.ticket.set_status('End Reviewing')
        self.ticket.set_status('Working')
        self.ticket.save()

    def run_pending(self):
        self.wr("Marking the ticket as review pending.")
        self.ticket['Review Result'] = 'Pending'
        self.ticket.set_status('Reviewing')
        self.ticket.save()
