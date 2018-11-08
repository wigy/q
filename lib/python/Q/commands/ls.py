# -*- coding: UTF-8 -*-
from ..error import QError
from ..settings import QSettings
from ..command import Command
from ..helper import Git
from ..ticket import Ticket

class CommandLs(Command):
    """
    List all tickets.
    """
    def run(self):
        """
        usage: q [ls] [--short] [--all]
        """
        from ..q import Q
        current = Git().current_branch_number(ignore_error=True)
        if current:
            Q('my','revert')
        done = []
        current_done = None
        show_all = self.opts.get('all')
        changed = ""
        if current and Git().has_changes():
            changed = " *MODIFIED*"
        codes = Ticket.all_codes()
        codes.sort(reverse = True)
        # Run separate refresh round to get prints out of the listing.
        for code in codes:
            self.load(code)
            self.ticket.refresh()
        # Then list them.
        nothing = True
        for code in codes:
            self.load(code)
            color = Q.USER
            if self.ticket['Owner'] == QSettings.GIT_USER:
                color = Q.USER_ME
            branch_color = Q.BRANCH
            if self.ticket.is_epic():
                branch_color = Q.YELLOW
            title = self.ticket['Title']
            ownership = '[' + color + self.ticket['Owner'] + ' ' + branch_color + self.ticket.branch_name() + Q.END + ']'
            if code==current:
                title += ' '+Q.MARK+changed
                color = Q.MARKER
            status = self.ticket.flags()
            s = '%s - %s\n       %s\n       [%s]' % (color + code, title + Q.END, ownership, status)
            if self.ticket.finished():
                done.append(s)
                if code==current:
                    current_done = s
            else:
                self.wr(s, channel='Tickets')
                nothing = False
        if not self.opts.get('short'):
            n=0
            for s in done:
                self.wr(s, channel='Old Tickets')
                n += 1
                if not show_all and n == 10 and len(done) > n:
                    self.wr("     ... and " + str(len(done) - n) + " other tickets of total " + str(len(codes)), channel='Old Tickets')
                    break
        if current_done:
            self.wr(current_done, channel='Old Tickets')
        if nothing and not show_all:
            self.wr("No open tickets. Use " + Q.COMMAND + "q ls --all" + Q.END + " to view old tickets.")
        if not codes:
            self.wr("No tickets created.", channel='Help')
            self.wr("You can use "+Q.COMMAND+"q start <ticket_number> <description>"+Q.END+" to create one.", channel='Help')
        if current:
            Q('my','apply')
