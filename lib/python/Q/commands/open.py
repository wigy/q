# -*- coding: UTF-8 -*-
from ..command import AutoGoCommand
from ..settings import QSettings
from ..helper import Edit


class CommandOpen(AutoGoCommand):
    """
    Open changed files in editor.
    """
    def run(self):
        """
        usage: q open [<code>]
        """
        if not self.ticket['Files']:
            self.wr("No Files defined yet. Must commit something first.")
        else:
            files = []
            for file in self.ticket.list('Files'):
                files.append(QSettings.APPDIR + "/" + file)
            Edit()(*files)
            # TODO: Add browser opening an URL.
