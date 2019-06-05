# -*- coding: UTF-8 -*-
from ..error import QError
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
        if self.settings.LOBBY_BRANCH == Git(self.settings).current_branch_name():
            raise QError('You are in ' + self.settings.LOBBY_BRANCH + ' branch.')
        self.Q('my','revert')
        diff = Git(self.settings)('--no-pager diff', get_output=True).strip()
        missing = Git(self.settings).missing_files()
        if diff == "" and len(missing) == 0 and not self.opts.get('force'):
            self.wr("No changes to commit.")
            self.Q('my','apply')
            return

        merge_base = self.ticket.merge_base()
        Git(self.settings)('diff '+merge_base+" > "+self.ticket.path("latest.diff"))
        Git(self.settings)('diff --color')

        for file in missing:
            self.wr('New file: ' + Q.FILE + file + Q.END)
        self.wr('Empty line to abort:')
        comments = raw_input()
        if not comments:
            self.wr('Aborted.')
        else:
            for file in missing:
                Git(self.settings)('add', file)
            msg = self.settings.COMMIT_MESSAGE
            msg = msg.replace('%c', self.ticket.code)
            msg = msg.replace('%m', comments)
            msg = msg.replace('"', '\\"')
            Git(self.settings)('commit -a -m "'+ msg + '"')
            files = self.ticket.changed_files()
            if self.ticket['Status'] != 'Working':
                self.ticket.set_status('Working')
            if self.ticket['Build Status']:
                self.ticket['Build Status'] = 'Need Rebuild'
            if self.ticket['Review Status']:
                self.ticket['Review Status'] = 'Need Update'
            self.ticket['Files'] = files
            self.ticket.save()
            if self.app.timing_is_in_use():
                self.app.timing_comment_for_ticket(self.ticket, comments)
                self.ticket.save()
                self.Q('work', 'switch')
        self.Q('my','apply')
