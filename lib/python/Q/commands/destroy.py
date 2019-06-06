from ..command import AutoGoCommand
from ..error import QError
from ..helper import Git


class CommandDestroy(AutoGoCommand):
    """
    Destroy the ticket including data and branches.
    """

    def run(self):
        """
        usage: q destroy [<code>]
               <code> - A ticket number.
        """
        Git(self.settings)('push ' + self.settings.GIT_REMOTE + ' :'+self.ticket.branch_name())
        Git(self.settings)('checkout '+self.settings.LOBBY_BRANCH)
        Git(self.settings)('branch -D '+self.ticket.branch_name())
        self.ticket.destroy()
