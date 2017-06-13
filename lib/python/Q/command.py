# -*- coding: UTF-8 -*-

from error import QError
from settings import QSettings
from ticket import Ticket
from helper import *


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
               '?' : 'help',
               }

    param_aliases = {}

    def __init__(self, app):
        self.app = app
        self.ticket = Ticket(self)

    def parse(self, *argv):
        """
        Parse options and run the command.
        """
        self.args = []
        self.opts = {}
        code = None
        for arg in argv:
            if arg in self.param_aliases:
                arg = self.param_aliases[arg]
            if (re.match(QSettings.TICKET_NUMBER_REGEX, arg)
                    and not self.args
                    and not self.opts):
                code = arg
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
        from commands.build import CommandBuild
        from commands.cancel import CommandCancel
        from commands.create import CommandCreate
        from commands.commit import CommandCommit
        from commands.destroy import CommandDestroy
        from commands.diff import CommandDiff
        from commands.done import CommandDone
        from commands.edit import CommandEdit
        from commands.go import CommandGo
        from commands.help import CommandHelp
        from commands.ls import CommandLs
        from commands.my import CommandMy
        from commands.publish import CommandPublish
        from commands.release import CommandRelease
        from commands.reopen import CommandReopen
        from commands.review import CommandReview
        from commands.show import CommandShow
        from commands.settings import CommandSettings
        from commands.start import CommandStart
        from commands.update import CommandUpdate
        from commands.test import CommandTest
        from commands.find import CommandFind
        from commands.base import CommandBase
        from commands.open import CommandOpen

        for name in ['Destroy', 'Help', 'Ls', 'Show', 'Start', 'Go', 'My', 'Diff', 'Commit', 'Settings', 'Publish',
                     'Update', 'Edit', 'Backport', 'Done', 'Build', 'Review', 'Release', 'Create', 'Reopen',
                     'Cancel', 'Test', 'Find', 'Base', 'Open']:
            ret[name.lower()] = eval("Command" + name)

        return ret


class AutoLoadCommand(Command):
    """
    A command that automatically loads the current ticket and ticket is required.
    """
    def init(self, code):
        if code:
            if not self.ticket.exists(code):
                raise QError("No such ticket as #%s." % code)
        else:
            code = Git().current_branch_number()
        if not code:
            raise QError("Cannot find the current ticket number from git branch.")
        self.load(code)


class AutoGoCommand(AutoLoadCommand):
    """
    A command that automatically switches to the another ticket.
    """
    def init(self, code):
        if not code:
            AutoLoadCommand.init(self, code)
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


class CommandUrl(AutoGoCommand):
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
        from q import Q
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
