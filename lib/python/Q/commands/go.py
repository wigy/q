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
        from ..q import Q
        # Nothing to do, switching is done automatically.
        Q('ls', '--short')
