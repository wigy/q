# -*- coding: UTF-8 -*-
from ..command import Command


class CommandHelp(Command):
    """
    Display help texts.
    """
    def run(self):
        """
        usage: q help
        """
        self.help()

    def help(self):
        from ..q import Q
        aliases = {}
        for k,v in Command.aliases.iteritems():
            aliases[v] = k
        all = Command.all_commands()
        names = all.keys()
        names.sort()
        for c in names:
            command = all[c]
            alias = ""
            cmd = command.__name__[7:].lower()
            if str(cmd) in aliases:
                alias = " Alias: "+Q.COMMAND+"q "+aliases[str(cmd)]+Q.END
            self.wr(Q.COMMAND+"q "+str(cmd)+Q.END+" - "+command.__doc__.strip()+alias)
            self.wr(command.run.__doc__)
