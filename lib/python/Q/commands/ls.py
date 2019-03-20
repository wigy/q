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

    def show_ticket(self, ticket, channel=None, current=False, modified={}, tabs=0):
        """
        Display a ticket info.
        """
        from ..q import Q
        spaces = tabs * ' '
        color = Q.USER
        if ticket['Owner'] == QSettings.GIT_USER:
            color = Q.USER_ME
        branch_color = Q.BRANCH
        if ticket.is_epic():
            branch_color = Q.YELLOW
        title = ticket['Title']
        ownership = '[' + color + ticket['Owner'] + ' ' + branch_color + ticket.branch_name() + Q.END + ']'
        if current==ticket.code:
            title += ' '+Q.MARK
            color = Q.MARKER
        if ticket.code in modified:
            title += Q.CYAN + ' *MODIFIED*'
        status = ticket.flags()
        s = '%s%s - %s\n%s       %s\n%s       [%s]' % (spaces, color + ticket.code, title + Q.END, spaces, ownership, spaces, status)
        self.wr(s, channel=channel)

    def show_ticket_tree(self, tickets, channel=None, current=None, modified={}):
        """
        Display a tree of tickets.
        """
        # TODO: This could be generic function somewhere.
        class TicketNode:
            """
            A class for constructing tree of tickets.
            """
            def __init__(self, ticket):
                self.ticket = ticket
                self.children = []
            def __repr__(self):
                return '<TicketNode #%s %r>' % (self.ticket and self.ticket.code, [child.__repr__() for child in self.children])
            def add(self, ticket):
                self.children.append(ticket)
            def show(self, cmd, **kwargs):
                if self.ticket:
                    cmd.show_ticket(self.ticket, **kwargs)
                    kwargs['tabs'] += 4
                for child in self.children:
                    child.show(cmd, **kwargs)

        root = TicketNode(None)
        branch2code = {}
        code2node = {}
        for ticket in tickets:
            branch2code[ticket['Branch']] = ticket.code
            code2node[ticket.code] = TicketNode(ticket)
        for ticket in tickets:
            base = ticket['Base']
            if base and base in branch2code:
                code2node[branch2code[base]].add(code2node[ticket.code])
            else:
                root.add(code2node[ticket.code])
        root.show(self, channel=channel, current=current, tabs=0, modified=modified)

    def run(self):
        """
        usage: q [ls] [--all]
        """
        from ..q import Q
        current = Git().current_branch_number(ignore_error=True)
        if current:
            Q('my','revert')
        modified = {}
        if current and Git().has_changes():
            modified[current]=True
        for code in Ticket.stash_names():
            modified[code]=True
        done = []
        working = []
        done_but_current = []
        show_all = self.opts.get('all')
        codes = Ticket.all_codes()
        codes.sort(reverse = True)
        # Run separate refresh round to get prints out of the listing.
        for code in codes:
            self.load(code)
            self.ticket.refresh()
        # Separate them to old and current tickets.
        for code in codes:
            self.load(code)
            if self.ticket.finished():
                done.append(self.ticket)
                if (self.ticket.code == current):
                    done_but_current.append(self.ticket)
            else:
                working.append(self.ticket)

        if len(done) + len(working) == 0:
            self.wr("No tickets created.", channel='Help')
            self.wr("You can use "+Q.COMMAND+"q start <ticket_number> [<description>]"+Q.END+" to create one.", channel='Help')
        elif len(working) == 0 and not show_all:
            self.wr("No open tickets. Use " + Q.COMMAND + "q ls --all" + Q.END + " to view old tickets.")
        else:
            self.show_ticket_tree(working, current=current, channel='Tickets', modified=modified)
            if show_all:
                self.show_ticket_tree(done, current=current, channel='Old Tickets', modified=modified)
            elif len(done_but_current):
                self.show_ticket_tree(done_but_current, current=current, channel='Old Tickets', modified=modified)

        Q('work', '--today')
        if current:
            Q('my','apply')
