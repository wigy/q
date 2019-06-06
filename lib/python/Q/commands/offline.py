# -*- coding: UTF-8 -*-
import datetime

from ..error import QError
from ..command import Command


class CommandOffline(Command):
    """
    Turn offline mode on and off.
    """
    def run(self):
        """
        usage: q offline [<off|on>]
        """
        from ..q import Q

        if len(self.args):
          if self.args[0] == 'on':
            val = True
          elif self.args[0] == 'off':
            val = False
          else:
            raise QError('Invalid argument ' + repr(self.args[0]))
          self.settings.OFFLINE_MODE = val
          self.Q('settings', 'save')

        self.wr(Q.TITLE + "\nOffline mode: " + Q.VAR + str(self.settings.OFFLINE_MODE) + Q.END + "\n")
        if self.settings.OFFLINE_MODE:
          self.wr('Use ' + Q.COMMAND + 'q offline off' + Q.END + ' to turn it off.\n')
        else:
          self.wr('Use ' + Q.COMMAND + 'q offline on' + Q.END + ' to turn it on.\n')
