# -*- coding: UTF-8 -*-
import os

from ..error import QError
from ..settings import QSettings
from ..command import Command


class CommandSettings(Command):
    """
    View or save settings.
    """
    param_aliases = {
                     's' : 'save'
                     }

    def run(self):
        """
        usage: q settings [save]
        """
        from ..q import Q
        if not self.args:
            path = QSettings.find(os.getcwd())
            if path:
                self.wr("Settings loaded from "+Q.COMMAND+"%s"+Q.END+".", path)
            settings = QSettings().dict()
            names = settings.keys()
            names.sort()
            for k in names:
                self.wr(Q.TITLE+k+':'+Q.END)
                self.wr(str(settings[k]))
        elif self.args[0]=='save':
            path = os.getcwd()+'/.q'
            QSettings().save(path)
            self.wr("Settings saved to '%s'.", path)
        else:
            raise QError("Invalid arguments '%s'.", self.args[0])
