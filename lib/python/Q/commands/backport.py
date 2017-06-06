# -*- coding: UTF-8 -*-
import os

from ..error import QError
from ..settings import QSettings
from ..command import AutoLoadCommand
from ..helper import Git, Cp, Rm


class CommandBackport(AutoLoadCommand):
    """
    Copy a file(s) to the base branch from the current branch. 
    """
    def run(self):
        """
        usage: q backport [<code>] <file_path>...
        """
        mine = self.ticket.branch_name()
        base = self.ticket.base_branch()
        TMP = "/tmp/"
        for src in self.args:
            if not os.path.exists(src):
                raise QError("Cannot find file '%s'.", src)
            Git()('checkout', mine)
            saved = TMP + os.path.split(src)[1]
            Cp()(src, saved) 
            Git()('checkout', base)
            Cp()(saved, src)
            Rm()(saved)
            Git()('add', src)
            Git()('commit', '-m', '"Back-ported from ' + mine + '"')
