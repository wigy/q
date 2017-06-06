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
                     's' : 'save',
                     'o' : 'offline',
                     }

    def run(self):
        """
        usage: q settings [save|offline]
        """
        from ..q import Q
        if not self.args:
            path = QSettings.find()
            if path:
                self.wr("Settings used from "+Q.COMMAND+"%s"+Q.END+".", path)
            settings = QSettings.dict()
            names = settings.keys()
            names.sort()
            for k in names:
                self.wr(Q.TITLE+k+':'+Q.END)
                self.wr(str(settings[k]))
        elif self.args[0]=='save':
            path = os.getcwd()+'/.q'
            QSettings.save(path)
            self.wr("Settings saved to '%s'.", path)
        elif self.args[0]=='offline':
            if QSettings.OFFLINE_MODE:
                QSettings.OFFLINE_MODE = ''
                self.wr("Turning offline mode OFF.")
            else:
                QSettings.OFFLINE_MODE = 'yes'
                self.wr("Turning offline mode ON.")
            Q('settings', 'save')
        else:
            raise QError("Invalid arguments '%s'.", self.args[0])
