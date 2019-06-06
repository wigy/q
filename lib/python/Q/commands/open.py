# -*- coding: UTF-8 -*-
import os
from ..command import AutoGoCommand
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
                path = self.settings.APPDIR + "/" + file
                if os.path.exists(path):
                    files.append(path)
            if not len(files):
                self.wr("No editabe files found.")
            Edit(self.settings)(*files)
            # TODO: Add browser opening an URL.
