# -*- coding: UTF-8 -*-
import os

from ..error import QError
from ..command import AutoLoadCommand
from ..helper import Git


class CommandEpic(AutoLoadCommand):
    """
    Set the current ticket as an epic.
    """

    def run(self):
        """
        usage: q epic [on|off]
        """
        from ..q import Q
        changed = False
        if self.args:
          if self.args[0]=='on':
            if not self.ticket.is_epic():
              changed = True
              old_branch = self.ticket.branch_name()
              self.ticket['Epic'] = True
              self.ticket.delete('Branch')
              new_branch = self.ticket.branch_name()
          elif self.args[0]=='off':
            if self.ticket.is_epic():
              changed = True
              old_branch = self.ticket.branch_name()
              self.ticket['Epic'] = False
              new_branch = self.ticket.branch_name()
          else:
              raise QError("Invalid arguments '%s'.", self.args[0])

        self.wr(Q.TITLE + "\nEpic ticket: " + Q.VAR + str(self.ticket['Epic']) + Q.END + "\n")
        if changed:
          if old_branch != new_branch:
            # TODO: This could be generic function somewhere automatically updating all branch references in all tickets
            Git(self.settings)('branch', '-M', old_branch, new_branch)
            Git(self.settings)('push', '-u', self.settings.GIT_REMOTE, new_branch)
            Git(self.settings)('push', self.settings.GIT_REMOTE, ':' + old_branch)
          self.ticket['Branch'] = new_branch
          self.ticket.save()
