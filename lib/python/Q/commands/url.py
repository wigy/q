from ..command import AutoLoadCommand


class CommandUrl(AutoLoadCommand):
    """
    Update URL and user information for the ticket.
    """
    param_aliases = {
                     'a' : 'add',
                     }

    def run(self):
        """
        usage: q url [<code>] [<user>|add] <debug_url>...
        """
        from ..q import Q
        if len(self.args) == 0:
            self.wr(Q.TITLE+'User:'+Q.END)
            self.wr(self.ticket['User'])
            self.wr(Q.TITLE+'URL:'+Q.END)
            self.wr(self.ticket['URL'])
            return
        if len(self.args) > 1:
            if self.args[0] == 'add':
                self.args = [self.ticket['URL']] + self.args[1:]
            else:
                self.ticket['User'] = self.args[0]
                self.args = self.args[1:]
        self.ticket['URL'] = self.args
        self.ticket.save()
