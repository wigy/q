# -*- coding: UTF-8 -*-
from ..error import QError
from ..settings import QSettings
from ..command import AutoGoCommand
from ..helper import Git

class CommandUpdate(AutoGoCommand):
    """
    Fetch the latest base and merge them to the ticket.
    If --all given, then update all base branches until common configured base branch is met.
    If --local given, then no pulls are made and the latest pull is used instead.
    """
    def run(self):
        """
        usage: q update [<code>] [--all] [--local]
        """
        base = self.ticket.base_branch()
        from ..q import Q
        Q('my','revert')
        if Git().has_changes():
            raise QError("Need to commit changes first.")
        old = Git().current_branch_name()
        base = self.ticket.base_branch()
        if not self.opts.get('local'):
            if base == QSettings.BASE_BRANCH:
                Git()('pull')
            else:
                Git()('fetch -a')
        if base != QSettings.BASE_BRANCH and self.opts.get('all'):
            Q('update', self.ticket.branch_number_of(base),'--all','--local')
        if old != base:
            Git()('checkout '+old)
            if base == QSettings.BASE_BRANCH:
                to_merge = QSettings.GIT_REMOTE +'/' + QSettings.BASE_BRANCH
            else:
                to_merge = base
            Git()('merge --no-edit '+to_merge)
        Q('my','apply')
