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
        from ..settings import QSettings

        if not len(self.args):
            self.wr(Q.TITLE+'Linked projects'+Q.END)
            if self.settings.LINKED_PROJECTS is None:
                self.wr('  None')
            else:
                for path in self.settings.LINKED_PROJECTS.split(':'):
                    self.wr('  ' + path)
        else:
            settings=QSettings.load(self.args[0] + '.q')
            this_path=self.settings.__dict__['APPDIR']
            other_path=settings.__dict__['APPDIR']

            if self.settings.LINKED_PROJECTS is None:
                self.settings.LINKED_PROJECTS=other_path
                self.wr('Linked ' + Q.FILE + other_path + Q.END + ' to ' + Q.FILE + this_path + Q.END)
            else:
                if other_path not in self.settings.LINKED_PROJECTS.split(':'):
                    self.settings.LINKED_PROJECTS+=':' + other_path
                    self.wr('Linked ' + Q.FILE + other_path + Q.END + ' to ' + Q.FILE + this_path + Q.END)
            self.settings.save(this_path + '.q')

            if settings.LINKED_PROJECTS is None:
                settings.LINKED_PROJECTS=this_path
                self.wr('Linked ' + Q.FILE + this_path + Q.END + ' to ' + Q.FILE + other_path + Q.END)
            else:
                if this_path not in settings.LINKED_PROJECTS.split(':'):
                    settings.LINKED_PROJECTS+=':' + this_path
                    self.wr('Linked ' + Q.FILE + this_path + Q.END + ' to ' + Q.FILE + other_path + Q.END)

            settings.save(other_path + '.q')
