# -*- coding: UTF-8 -*-
from ..command import AutoGoCommand


class CommandGo(AutoGoCommand):
    """
    Switch to another ticket for working.
    """
    def run(self):
        """
        usage: q [go] <code>|0
        """
        # Nothing to do, switching is done automatically.
        self.Q('ls', '--short')
