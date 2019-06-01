# -*- coding: UTF-8 -*-
import os

from ..error import QError
from ..settings import QSettings
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
            if QSettings.LINKED_PROJECTS is None:
                self.wr('  None')
            else:
                for path in QSettings.LINKED_PROJECTS.split(':'):
                    self.wr('  ' + path)
        else:
            this_path=QSettings.dict()['APPDIR']
            QSettings.push()
            QSettings.load(self.args[0] + '.q')
            other_path=QSettings.dict()['APPDIR']
            if QSettings.LINKED_PROJECTS is None:
                QSettings.LINKED_PROJECTS=this_path
            else:
                QSettings.LINKED_PROJECTS+=':' + this_path
            QSettings.save(other_path + '.q')
            self.wr('Linked ' + Q.FILE + this_path + Q.END + ' to ' + Q.FILE + other_path + Q.END)
            QSettings.pop()
            if QSettings.LINKED_PROJECTS is None:
                QSettings.LINKED_PROJECTS=other_path
            else:
                QSettings.LINKED_PROJECTS+=':' + other_path
            QSettings.save(this_path + '.q')
            self.wr('Linked ' + Q.FILE + other_path + Q.END + ' to ' + Q.FILE + this_path + Q.END)
