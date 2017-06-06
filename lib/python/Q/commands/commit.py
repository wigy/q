# -*- coding: UTF-8 -*-
from ..error import QError
from ..settings import QSettings
from ..command import AutoGoCommand
from ..helper import Git


class CommandCommit(AutoGoCommand):
    """
    Commit the changes and change status to 'Working', if currently 'Started'.
    """
    def run(self):
        """
        usage: q commit [<code>] [--force]
        """
        from ..q import Q
        Q('my','revert')
        diff = Git()('--no-pager diff', get_output=True).strip()
        if diff == "" and not self.opts.get('force'):
            self.wr("No changes to commit.")
            Q('my','apply')
            return

        merge_base = self.ticket.merge_base()
        Git()('diff '+merge_base+" > "+self.ticket.path("latest.diff"))
        Git()('diff --color')

        self.wr('Empty line to abort:')
        comments = raw_input()
        if not comments:
            self.wr('Aborted.')
        else:
            msg = QSettings.COMMIT_MESSAGE
            msg = msg.replace('%c', self.ticket.code)
            msg = msg.replace('%m', comments)
            msg = msg.replace('"', '\\"')
            Git()('commit -a -m "'+ msg + '"')
            files = self.ticket.changed_files()
            if self.ticket['Status'] != 'Working':
                self.ticket.set_status('Working')
            if self.ticket['Build Status']:
                self.ticket['Build Status'] = 'Need Rebuild'
            if self.ticket['Review Status']:
                self.ticket['Review Status'] = 'Need Update'
            self.ticket['Files'] = files
            self.ticket.save()
        Q('my','apply')
