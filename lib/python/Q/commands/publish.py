# -*- coding: UTF-8 -*-
from ..error import QError
from ..settings import QSettings
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
        from ..q import Q
        if Git().has_changes():
            Q('commit')
        if self.opts.get('all'):
            Git()('push')
        else:
            Git()('push ' + QSettings.GIT_REMOTE + ' '+self.ticket.branch_name())
