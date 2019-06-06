# -*- coding: UTF-8 -*-
from ..error import QError
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
        self.Q('my','revert')
        if Git(self.settings).has_changes():
            raise QError("Need to commit changes first.")
        old = Git(self.settings).current_branch_name()
        base = self.ticket.base_branch()
        if not self.opts.get('local'):
            if base == self.settings.BASE_BRANCH:
                Git(self.settings)('pull')
            else:
                Git(self.settings)('fetch -a')
        if base != self.settings.BASE_BRANCH and self.opts.get('all'):
            g = re.match(self.settings.TICKET_BRANCH_REGEX, base)
            self.Q('update', g.group(1),'--all','--local')
        if old != base:
            Git(self.settings)('checkout '+old)
            if base == self.settings.BASE_BRANCH:
                to_merge = self.settings.GIT_REMOTE +'/' + self.settings.BASE_BRANCH
            else:
                to_merge = base
            Git(self.settings)('merge --no-edit '+to_merge)
        self.Q('my','apply')
