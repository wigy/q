# -*- coding: UTF-8 -*-
import time

from ..error import QError
from ..settings import QSettings
from ..command import Command
from ..helper import Git


class CommandStart(Command):
    """
    Initialize a new ticket for working.
    """

    def init(self, code):
        self.code = code

    def run(self):
        """
        usage: q start <code> [--branch=<existing_branch_name>] [--base=<initial_checkout_tag>] [<title>]
               <code> - A ticket number.
               <title> - A descriptive title of the ticket.

               If title is not given, then data is fetched from the remote ticketing.
        """
        if not self.code:
            raise QError("No code given for the ticket.")

        # Leave current ticket.
        current = Git().current_branch_number(ignore_error=True)
        if(current):
            self.load(current)
            self.ticket.leave()

        # Construct ticket from arguments or from remote.
        if self.args:
            str = " ".join(self.args)
            if str[-1] != '.':
                str += '.'
            self.ticket['Title'] = str
        else:
            self.ticket = self.app.fetch_ticket(self, self.code)
            if not self.ticket:
                raise QError("Ticketing system failed to get the ticket.")
        self.ticket['Branch'] = None

        # Set the branch
        branch = self.opts.get('branch', None)
        if branch:
            self.ticket['Branch'] = branch
        else:
            self.ticket['Branch'] = self.ticket.branch_name()
            Git()('branch '+self.ticket['Branch'] + ' ' + QSettings.BASE_BRANCH)
            Git()('push -u ' + QSettings.GIT_REMOTE + ' '+self.ticket['Branch'])

        # Set the base branch.
        base = self.opts.get('base', None)
        if base:
            self.ticket['Base'] = base

        # Mark it started and save.
        self.ticket['Owner'] = QSettings.TICKETING_USER
        self.ticket['Started'] = time.strftime('%Y-%m-%d %H:%M')
        self.ticket.set_status('Started')
        self.ticket.save()

        # Claim the remote ticket.
        self.app.start_work_on_ticket(self.ticket)

        # Go to the branch.
        Git()('checkout '+self.ticket.branch_name())
