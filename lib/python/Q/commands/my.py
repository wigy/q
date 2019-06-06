# -*- coding: UTF-8 -*-
import os

from ..error import QError
from ..command import Command
from ..helper import Git
from ..file import QFile


class CommandMy(Command):
    """
    Handler for my private changes that are not to be commited publicly.
    """
    param_aliases = {
                     'a' : 'apply',
                     's' : 'save',
                     'r' : 'revert',
                     'd' : 'drop',
                     }

    def run(self):
        """
        usage: q my [<code>] save|apply|revert|drop
        """
        from ..q import Q
        # This command should work quietly even when no ticket.
        current = self.current_branch_number(ignore_error=True)
        if not current:
            return
        self.load(current)
        path = self.ticket.path('private.diff')
        flag = self.ticket.path('.private.diff')
        is_applied = os.path.isfile(flag)
        if not self.args:
            if path and os.path.isfile(path):
                self.wr(QFile(path).read())
                if is_applied:
                    self.wr("Currently applied.")
                    self.wr("Use "+Q.COMMAND+"q my r"+Q.END+" to revert.")
                    self.wr("Use "+Q.COMMAND+"q my d"+Q.END+" to drop.")
                else:
                    self.wr("Currently NOT applied.")
                    self.wr("Use "+Q.COMMAND+"q my a"+Q.END+" to apply.")
                    self.wr("Use "+Q.COMMAND+"q my d"+Q.END+" to drop.")
            else:
                self.wr("No private changes found. Use "+Q.COMMAND+"q my save"+Q.END+" to create from the current state.")
        elif self.args[0] == "save":
            Git(self.settings)('--no-pager diff --color')
            self.wr("Record these changes as private. Are you sure (y/n)?")
            resp = raw_input()
            if resp!='y':
                self.wr("Canceled")
            else:
                Git(self.settings)('diff > '+path)
            QFile(flag).write('Private saved!')
        elif self.args[0] == "revert":
            if not path or not os.path.isfile(path) or not is_applied:
                return
            Git(self.settings).patch(path, reverse = True)
            os.remove(flag)
        elif self.args[0] == "apply":
            if not path or not os.path.isfile(path) or is_applied:
                return
            Git(self.settings).patch(path)
            QFile(flag).write('Private diff applied!')
        elif self.args[0] == "drop":
            QFile(path).drop()
            QFile(flag).drop()
            self.wr('Private diff dropped!')
        else:
            raise QError("Invalid argument for 'q my': %s.", self.args[0])
