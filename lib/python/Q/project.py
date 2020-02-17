import sys
import os
import re
import glob
from distutils.dir_util import mkpath

from .error import QError
from .building import NoBuild, BuildByBamboo, BuildByCommandLine
from .reviewing import ReviewByReviewBoard, ReviewByGerrit, ReviewByVSTS, ReviewByBitbucket, NoReview, ReviewByLocalDiff
from .testing import TestingByNose, TestingByShellCommands
from .database import DatabaseByDjango
from .ticketing import TicketingByTrac, ManualTicketing, TicketingByVSTS, TicketingByAtlassian
from .releasing import NoReleasing, ReleasingByGerrit, ReleasingByBamboo, ReleasingByMerge
from .timing import NoTiming, TimingByAtlassian
from .command import Command
from .ticket import Ticket


class QProject:
    """
    Base functionality for querying and executing tasks for the application project.
    """
    def __init__(self, settings, q):
        self.settings = settings
        self.q = q

    def __repr__(self):
        if self.settings.APPSETTINGS:
            return '<Q.Project ' + self.settings.APPSETTINGS + '.project.py>'
        return '<Q.Project>'

    def parse(self, *_argv):
        argv = list(_argv)
        # Handle short-cuts for no arguments and single ticket number argument.
        if len(argv)==0:
            argv = ['ls', '--short']
        elif len(argv)==1 and (re.match('^[0-9]+$', argv[0]) or re.match(self.settings.TICKET_NUMBER_REGEX, argv[0])):
            argv = ['go', argv[0]]
        # Find the command and execute it.
        constructor = Command.find(argv[0])
        if constructor is None:
            raise QError("Command '%s' not found.", argv[0])
        self.cmd = constructor(self)
        argv = argv[1:]
        self.cmd.parse(*argv)

    def set_path(self):
        """
        Hook for setting up additional Python paths.
        """
        pass

    def find_file(self, basename):
        """
        Perform a lookup for PYTHON_PATH and find a file.
        """
        self.set_path()
        for p in sys.path:
            if os.path.exists(p+"/"+basename):
                return p+"/"+basename
        raise QError("Cannot find a file '%s'.", basename)

    def all_codes(self):
        """
        Collect a list of all ticket codes of this project.
        """
        from q import Q
        if not self.settings.WORKDIR:
            raise QError("Ticket storage directory WORKDIR is not set.")
        if not os.path.isdir(self.settings.WORKDIR):
            Q.wr("Initialize", "Creating ticket directory '%s'.", self.settings.WORKDIR)
            mkpath(self.settings.WORKDIR)
        ret = []
        for p in os.listdir(self.settings.WORKDIR):
            if os.path.isfile(self.settings.WORKDIR+"/"+p+"/README"):
                ret.append(p)
        return ret

    def num2code(self, num):
        """
        Convert ticket number to ticket code.
        """
        for path in glob.glob(self.settings.WORKDIR + '/*' + num + '*'):
            code = path.split('/')[-1]
            match = re.match(self.settings.TICKET_NUMBER_REGEX, code)
            if match and int(match.groups()[1]) == int(num):
                return code
        return None

    def load_ticket(self, code):
        """
        Load a ticket from this project.
        """
        ticket = Ticket(self, code)
        ticket.load()
        return ticket

    def all_tickets(self):
        """
        Collect a list of all tickets of this project.
        """
        ret = []
        for code in self.all_codes():
            ret.append(self.load_ticket(code))
        return ret

    def Q(self, *args):
        """
        Call Q again.
        """
        self.q.parse(*args)

    @classmethod
    def create(cls, settings, q):
        project_path = os.path.dirname(settings.APPSETTINGS) + '/.q.project.py'
        if not os.path.exists(project_path) or os.path.getmtime(project_path) < os.path.getmtime(settings.APPSETTINGS):
            if not settings.APP_TICKETING:
                raise QError("Ticketing mixing APP_TICKETING must be set in configuration.")
            definition = """#
# Automatically generated from `.q`.
# Just delete this if you want to regenerate it.
#
class Project(QProject, APP_TICKETING, APP_RELEASING, APP_REVIEWING, APP_BUILDING, APP_TESTING, APP_TIMING):
    pass
"""
            definition = definition.replace('APP_TICKETING', settings.APP_TICKETING)
            definition = definition.replace('APP_RELEASING', settings.APP_RELEASING)
            definition = definition.replace('APP_REVIEWING', settings.APP_REVIEWING)
            definition = definition.replace('APP_BUILDING', settings.APP_BUILDING)
            definition = definition.replace('APP_TESTING', settings.APP_TESTING)
            definition = definition.replace('APP_TIMING', settings.APP_TIMING)
            f = open(project_path,'w')
            f.write(definition)
            f.close()
        content = {}
        try:
            exec(open(project_path).read(), globals())
        except NameError as err:
            raise QError("Invalid configuration: %r.", err)

        return Project(settings, q)
