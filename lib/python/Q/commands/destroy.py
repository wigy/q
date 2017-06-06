from ..command import AutoGoCommand
from ..error import QError
from ..settings import QSettings
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
        Git()('push ' + QSettings.GIT_REMOTE + ' :'+self.ticket.branch_name())
        Git()('checkout '+QSettings.LOBBY_BRANCH)
        Git()('branch -D '+self.ticket.branch_name())
        self.ticket.destroy()
