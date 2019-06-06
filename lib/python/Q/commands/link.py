# -*- coding: UTF-8 -*-
import os

from ..error import QError
from ..command import Command


class CommandLink(Command):
    """
    Link other projects with this project.
    """

    def run(self):
        """
        usage: link <project-path>
        """
        from ..q import Q
        if not len(self.args):
            self.wr(Q.TITLE+'Linked projects'+Q.END)
            if self.settings.LINKED_PROJECTS is None:
                self.wr('  None')
            else:
                for path in self.settings.LINKED_PROJECTS.split(':'):
                    self.wr('  ' + path)
        else:
            # TODO: Could link all currently linked projects to the target as well.
            this_path=self.settings.__dict__['APPDIR']
            self.settings.push()
            self.settings.load(self.args[0] + '.q')
            other_path=self.settings.__dict__['APPDIR']
            if self.settings.LINKED_PROJECTS is None:
                self.settings.LINKED_PROJECTS=this_path
            else:
                self.settings.LINKED_PROJECTS+=':' + this_path
            self.settings.save(other_path + '.q')
            self.wr('Linked ' + Q.FILE + this_path + Q.END + ' to ' + Q.FILE + other_path + Q.END)
            self.settings.pop()
            if self.settings.LINKED_PROJECTS is None:
                self.settings.LINKED_PROJECTS=other_path
            else:
                self.settings.LINKED_PROJECTS+=':' + other_path
            self.settings.save(this_path + '.q')
            self.wr('Linked ' + Q.FILE + other_path + Q.END + ' to ' + Q.FILE + this_path + Q.END)
