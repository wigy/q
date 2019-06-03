# -*- coding: UTF-8 -*-

import os
from .error import QError
from .settings import QSettings
from .ticket import Ticket
from .helper import *


class Command:
    """
    Encapsulates command execution to different subclasses of this.
    """

    # Shortcuts for commands.
    aliases = {
               'b' : 'build',
               'c' : 'commit',
               'd' : 'diff',
               'e' : 'edit',
               'f' : 'find',
               'o' : 'open',
               'p' : 'publish',
               'q' : 'go',
               'r' : 'review',
               's' : 'show',
               't' : 'test',
               'u' : 'update',
               'w' : 'work',
               '?' : 'help',
               }

    param_aliases = {}

    def __init__(self, app):
        self.app = app
        self.ticket = Ticket(self)

    def readyness_check(self):
        """
        Check configured verifications before launching build or review.
        """
        from .q import Q
        if QSettings.LINT:
            self.wr('Performing readyness checks...')
            self.wr(Q.COMMAND + QSettings.LINT + Q.END)
            if os.system(QSettings.LINT):
                raise QError("Readyness check failed.")

    def _check_for_ticket(self, str):
        """
        Helper to check if the string matches ticket code or is short-cut (number part of code) to the existing ticket.
        """
        if str == '0':
            return str
        if re.match(QSettings.TICKET_NUMBER_REGEX, str):
            return str
        if QSettings.WORKDIR is None:
            return None
        for code in Ticket.all_codes():
            if str == code:
                return code
            match = re.match(QSettings.TICKET_NUMBER_REGEX, code)
            if match:
                matches = match.groups()
                # If there are more than one parenthesis, use the last one.
                if matches[len(matches)-1] == str:
                    return code

    def parse(self, *argv):
        """
        Parse options and run the command.
        """
        self.args = []
        self.opts = {}
        code = None
        argv = list(argv)
        # Parse ticket number as first argument.
        if len(argv):
            code = self._check_for_ticket(argv[0])
            if not code is None:
                argv = argv[1:]
        # Separate options and arguments.
        i = 0
        for arg in argv:
            if arg in self.param_aliases:
                self.args.append(self.param_aliases[arg])
            else:
                opt = re.match('--(\w+)(=(.*))?',arg)
                if opt:
                    opts = opt.groups()
                    if opts[2]:
                        self.opts[opts[0]] = opts[2]
                    else:
                        self.opts[opts[0]] = True
                else:
                    self.args.append(arg)
            i += 1
        # Run intialize hook and execute command.
        self.init(code)
        self.run()

    def init(self, code):
        """
        Hook to initialize command, i.e. load ticket for example.
        """
        pass

    def run(self):
        raise QError("Running not implemented for '%s'.", self.__class__.__name__)

    def wr(self, *msg, **kwargs):
        """
        Print out run time message using command name as channel unless given as channel=<Name>.
        """
        from q import Q
        channel = kwargs.get('channel')
        if not channel:
            channel = '@' + self.__class__.__name__[7:]
        Q.wr(channel, *msg)

    def load(self, code):
        """
        Load the ticket with the given code.
        """
        self.ticket = Ticket(self, code)
        self.ticket.load()

    def get_ticket(self, code):
        """
        Get the ticket without changing current ticket.
        """
        old = self.ticket
        self.load(code)
        ret = self.ticket
        self.ticket = old
        return ret

    def Q(self, *args):
        """
        Call Q and reload the ticket.
        """
        from .q import Q
        code = self.ticket.code
        if code:
            self.ticket.save()
        Q(*args)
        if code:
            self.load(code)

    @staticmethod
    def find(cmd):
        """
        Find the command implementation class.
        """
        if cmd in Command.aliases:
            cmd = Command.aliases[cmd]
        all = Command.all_commands()
        if cmd in all:
            return all[cmd]
        return None

    @staticmethod
    def all_commands():
        """
        Collect a map from all command names to their classes.
        """
        ret = {}
        from commands.backport import CommandBackport
        from commands.base import CommandBase
        from commands.build import CommandBuild
        from commands.cancel import CommandCancel
        from commands.commit import CommandCommit
        from commands.create import CommandCreate
        from commands.destroy import CommandDestroy
        from commands.diff import CommandDiff
        from commands.done import CommandDone
        from commands.edit import CommandEdit
        from commands.epic import CommandEpic
        from commands.find import CommandFind
        from commands.go import CommandGo
        from commands.help import CommandHelp
        from commands.last import CommandLast
        from commands.link import CommandLink
        from commands.ls import CommandLs
        from commands.my import CommandMy
        from commands.offline import CommandOffline
        from commands.open import CommandOpen
        from commands.publish import CommandPublish
        from commands.release import CommandRelease
        from commands.reopen import CommandReopen
        from commands.review import CommandReview
        from commands.settings import CommandSettings
        from commands.show import CommandShow
        from commands.start import CommandStart
        from commands.test import CommandTest
        from commands.update import CommandUpdate
        from commands.url import CommandUrl
        from commands.work import CommandWork

        for name in ['Destroy', 'Help', 'Ls', 'Show', 'Start', 'Go', 'My', 'Diff', 'Commit', 'Settings', 'Publish',
                     'Update', 'Edit', 'Backport', 'Done', 'Build', 'Review', 'Release', 'Create', 'Reopen',
                     'Cancel', 'Test', 'Find', 'Base', 'Open', 'Url', 'Last', 'Offline',
                     'Epic', 'Work', 'Link']:
            ret[name.lower()] = eval("Command" + name)

        return ret


class AutoLoadCommand(Command):
    """
    A command that automatically loads the current ticket and ticket is also always required.
    """
    def init(self, code):
        if code:
            if not self.ticket.exists(code):
                raise QError("No such ticket as #%s." % code)
        else:
            code = Git().current_branch_number()
        if code is None:
            raise QError("Cannot find the current ticket number from git branch.")
        if code:
            self.load(code)


class AutoGoCommand(AutoLoadCommand):
    """
    A command that automatically switches to the another ticket.
    """
    def init(self, code):
        if not code:
            AutoLoadCommand.init(self, None)
            return
        if code != '0' and not self.ticket.exists(code):
            raise QError("No such ticket as #%s." % code)
        old = Git().current_branch_number(ignore_error=True)
        if old:
            self.load(old)
        if code == old:
            return
        if old:
            self.ticket.leave()
        if code == '0':
            Git()('checkout ' + QSettings.LOBBY_BRANCH)
            return
        self.load(code)
        self.ticket.enter()


# TODO: Move these commands to their own files after reviewing their functionality.
class CommandDb(AutoLoadCommand):
    """
    Database related operations.
    """

    param_aliases = {
                     'i' : 'init',
                     'l' : 'load',
                     'r' : 'reset',
                     's' : 'save',
                     'o' : 'open',
                     }

    def run(self):
        """
        usage: q db [<code>] save [<dump_file>[.sql]] | init <ticket_number> | init <db_name> | reset | open
        """
        from q import Q
        if len(self.args)==0:
            if not self.ticket['DB']:
                self.ticket.wr("No database set yet")
                self.ticket.wr("Use "+Q.COMMAND+"q db init <ticket_number>"+Q.END+" or "+Q.COMMAND+"q db init <db_name>"+Q.END+" to create.")
                return
            else:
                conf_db = self.ticket['DB']
                real_db = self.app.db_info()['db']
                self.wr(Q.TITLE+"Current DB:"+Q.END)
                self.wr(real_db)
                if real_db != conf_db:
                    self.wr(Q.TITLE+"Ticket's DB:"+Q.END)
                    self.wr(conf_db)
                self.wr(Q.TITLE+"Dumps:"+Q.END)
                for dump in glob.glob(self.ticket.path('*.sql')):
                    if dump == self.ticket['Dump']:
                        dump += " "+Q.MARK
                    self.wr(dump)
                self.wr(Q.TITLE+"Help:"+Q.END)
                self.wr("Use "+Q.COMMAND+"q db init <ticket_number>"+Q.END+" or "+Q.COMMAND+"q db init <db_name>"+Q.END+" to recreate.")
                self.wr("Use "+Q.COMMAND+"q db save [<dump_file>[.sql]]"+Q.END+" to save a dump.")
                self.wr("Use "+Q.COMMAND+"q db load [<dump_file>[.sql]]"+Q.END+" to load a dump.")
                self.wr("Use "+Q.COMMAND+"q db reset"+Q.END+" start from the scratch.")
                self.wr("Use "+Q.COMMAND+"q db open"+Q.END+" to access it with command-line client.")
                return

        if self.args[0] == 'save':
            if(len(self.args) > 1):
                dump_name = self.args[1]
            else:
                dump_name = 'dump.sql'
            if dump_name[-4:]!='.sql':
                dump_name += '.sql'
            db = self.app.db_info()
            dump_path = self.ticket.path(dump_name)
            Mysql().save(db, dump_path)
            self.ticket['Dump']=dump_path
            self.ticket['DB']=db['db']
            self.ticket.save()
            return

        if self.args[0] == 'load':
            if(len(self.args) > 1):
                dump_path = self.ticket.path(self.args[1])
            else:
                dump_path = self.ticket['Dump']
            if dump_path[-4:]!='.sql':
                dump_path += '.sql'
            if not os.path.isfile(dump_path):
                raise QError("Cannot find dump '%s'.", dump_path)
            info = self.app.db_info()
            Mysql().load(info, dump_path)
            return

        elif self.args[0] == 'init':
            info = self.app.db_info()
            init_path = self.ticket.path("init.sql")
            if len(self.args)==1:
                self.wr("Creating empty database.")
                init_path = None
            elif re.match('^\d+$',self.args[1]):
                ticket = Ticket(self, self.args[1])
                ticket.load()
                if not ticket['Dump']:
                    raise QError("Cannot find dump file for ticket '%s'.",self.args[1])
                dump_path = ticket['Dump']
                self.wr("Copying DB from '%s' to '%s'.", dump_path, init_path)
                shutil.copyfile(dump_path, init_path)
            elif os.path.exists(self.args[1]):
                dump_path=self.args[1]
                self.wr("Copying DB from '%s' to '%s'.", dump_path, init_path)
                if dump_path[-3:] == '.gz':
                    Zcat()(dump_path, '>', init_path)
                else:
                    shutil.copyfile(dump_path, init_path)
            else:
                info['db'] = self.args[1]
                Mysql().save(info, init_path)
            info['db'] = QSettings.DB_NAME % self.ticket.code
            Mysql().create(info)
            if init_path:
                 Mysql().load(info, init_path)
                 self.ticket['Dump']=init_path
            self.ticket['DB']=info['db']
            self.ticket.save()
            self.app.change_db(info['db'])

        elif self.args[0] == 'reset':

            db_name = QSettings.DB_NAME % self.ticket.code
            self.app.db_reset()
            save_path = self.ticket.path("empty.sql")
            self.ticket['Dump']=save_path
            self.ticket['DB']=db_name
            self.ticket.save()

        if self.args[0] == 'open':
            if not self.ticket['DB']:
                raise QError("Cannot open DB since none in use.")
            Mysql().open(self.app.db_info())
            return

        else:
            raise QError("Invalid DB sub-command '%s'.", self.args[0])
