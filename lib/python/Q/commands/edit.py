# -*- coding: UTF-8 -*-

from ..error import QError
from ..settings import QSettings
from ..command import AutoLoadCommand
from ..file import QFile
from ..helper import Edit


class CommandEdit(AutoLoadCommand):
    """
    Launch editor for free form notes.
    """
    def run(self):
        """
        usage: q edit [<code>]
        """
        notes = self.ticket['Notes']
        if not notes:
            notes = ""
        path = self.ticket.path('notes.txt')
        QFile(path).write(notes + "\n")
        Edit()(path, light=True)
        new_notes = QFile(path).read().strip()
        if new_notes != notes:
            self.ticket['Notes'] = new_notes
            self.ticket.save()
            self.app.change_text_of_ticket(self.ticket)
