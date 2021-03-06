# -*- coding: UTF-8 -*-
from ..error import QError
from ..command import AutoGoCommand
from ..helper import Git


class CommandDiff(AutoGoCommand):
    """
    Check out the changes done since commit or all changes for the ticket.
    """

    param_aliases = {
                     'a' : 'all',
                     }

    def run(self):
        """
        usage: q diff [<code>] [all]
        """
        self.Q('my','revert')
        if self.args and (self.args[0] == 'all'):
            merge_base = self.ticket.merge_base()
            Git(self.settings)('diff --color '+merge_base)
        else:
            Git(self.settings)('diff --color')
        self.Q('my','apply')
