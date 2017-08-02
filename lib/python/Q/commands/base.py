# -*- coding: UTF-8 -*-
from ..error import QError
from ..settings import QSettings
from ..command import AutoGoCommand
from ..helper import Git


class CommandBase(AutoGoCommand):
    """
    Display or change the base branch this ticket is based on.
    """

    def run(self):
        """
        usage: q base [<code>] [<branch>]
        """
        from ..q import Q
        if len(self.args):
            self.ticket['Base'] = self.args[0]
            self.ticket.save()
        base = self.ticket['Base']
        if base:
            base = Q.BRANCH + base + Q.END
        else:
            base = 'default ' + Q.BRANCH + QSettings.BASE_BRANCH + Q.END
        self.wr("Base is " + base)
        # TODO: Can run update here.
