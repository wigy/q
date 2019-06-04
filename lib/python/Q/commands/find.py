# -*- coding: UTF-8 -*-
import time
import re

from ..error import QError
from ..settings import QSettings
from ..command import Command
from ..helper import Grep
from ..ticket import Ticket


class CommandFind(Command):
    """
    Find strings from the ticket data.
    """
    def run(self):
        """
        usage: q find [search...]
        """
        from ..q import Q

        args = " ".join(self.args)
        if args == "":
            raise QError("Need arguments to search.")
        args = '"' + args.replace('"', '\\"') + '"'
        out = Grep().run("-r", "-l", "-i", args, QSettings.WORKDIR, get_output=True)
        hits = {}
        codes = self.ticket.all_codes()
        for filename in out.split("\n"):
            if filename == '' or filename[-1] == '~':
                continue
            ticket = filename[len(QSettings.WORKDIR) + 1:]
            ticket = ticket[0:ticket.find('/')]
            if not ticket in codes:
                continue
            if ticket not in hits:
                hits[ticket] = {}
            grep = Grep().run("-A2", "-B2", "-i", args, filename, get_output=True)
            hits[ticket][filename] = grep
        if len(hits) == 0:
            self.wr("Not found")
        else:
            for ticket in hits:
                self.load(ticket)
                self.wr(Q.TITLE + ticket + ' - ' + self.ticket['Title'] + Q.END + "\n")
                for filename in hits[ticket]:
                    self.wr(Q.URL + filename + Q.END + "\n")
                    self.wr(hits[ticket][filename])
