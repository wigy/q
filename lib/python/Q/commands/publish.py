# -*- coding: UTF-8 -*-
from ..error import QError
from ..command import AutoGoCommand
from ..helper import Git


class CommandPublish(AutoGoCommand):
    """
    Send the changes to the remote server.
    """
    def run(self):
        """
        usage: q publish [<code>] [--all]
        """
        if Git(self.settings).has_changes():
            self.Q('commit')
        if self.opts.get('all'):
            Git(self.settings)('push')
        else:
            Git(self.settings)('push ' + self.settings.GIT_REMOTE + ' '+self.ticket.branch_name())
