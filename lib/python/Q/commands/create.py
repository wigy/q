from ..command import Command
from ..error import QError
from ..settings import QSettings
from ..helper import Edit
from ..ticket import Ticket


class CommandCreate(Command):
    """
    Create new ticket.
    """

    def run(self):
        """
        usage: q create <title>
               <title> - A descriptive title of the ticket.
        """

        if not self.app.can_create_ticket():
            raise QError("Configured ticketing system cannot create tickets.")

        # Construct title.
        if len(self.args) == 0:
            raise QError("Please give the title of the ticket.")
        title = " ".join(self.args)
        if title[-1] != '.':
            title += '.'

        # Create new ticket.
        self.ticket=Ticket(self)
        self.ticket['Title'] = title
#        self.ticket['Notes'] = Edit().temp()
        self.ticket['Notes'] = 'Cannot launch virta-main with virta-white due to port conflict.'
        if self.ticket['Notes'].strip() == '':
            raise QError("Canceled")
        self.ticket['Owner'] = None
        self.ticket['Status'] = 'New'
        self.ticket.code = self.app.create_ticket(self.ticket)
        self.ticket.create()
        self.ticket.save()
