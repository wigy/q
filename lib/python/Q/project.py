import sys
import os
import re

from error import QError
from settings import QSettings
from building import NoBuild, BuildByBamboo
from reviewing import ReviewByReviewBoard, ReviewByGerrit, ReviewByVSTS, ReviewByBitbucket, NoReview
from testing import TestingByNose, TestingByShellCommands
from database import DatabaseByDjango
from ticketing import TicketingByTrac, ManualTicketing, TicketingByVSTS, TicketingByAtlassian
from releasing import NoReleasing, ReleasingByGerrit, ReleasingByBamboo
from command import Command
from ticket import Ticket


class QProject:
    """
    Base functionality for querying and executing tasks for the application project.
    """

    def parse(self, *argv):
        if len(argv):
            arg0 = argv[0]
            # Match numbers anyway even if they are not ticket codes exactly.
            if re.match('[0-9]+', arg0) and not re.match(QSettings.TICKET_NUMBER_REGEX, arg0):
                for code in Ticket.all_codes():
                    match = re.match('.*?([0-9]+).*', code)
                    if match:
                        if match.group(1) == arg0:
                            arg0 = code
                            break
            if len(argv) == 1 and re.match(QSettings.TICKET_NUMBER_REGEX, arg0):
                cmd = 'go'
            else:
                cmd = arg0
                argv = argv[1:]
        else:
            cmd = 'ls'
            argv = ['--short']
        constructor = Command.find(cmd)
        if constructor is None:
            raise QError("Command '%s' not found.", cmd)
        self.cmd = constructor(self)
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

    @classmethod
    def create(cls, settings):
        project_path = os.path.dirname(settings.APPSETTINGS) + '/.q.project.py'
        if not os.path.exists(project_path) or os.path.getmtime(project_path) < os.path.getmtime(settings.APPSETTINGS):
            # TODO: Add mixing classes based on configuration.
            # TODO: Crash if no APP_TICKET_CLASS is not set.
            definition = """#
# Automatically generated from `.q`.
# Just delete this if you want to regenerate it.
#
class Project(QProject, APP_TICKETING, APP_RELEASING, APP_REVIEWING, APP_BUILDING, APP_TESTING):
    pass
"""
            definition = definition.replace('APP_TICKETING', settings.APP_TICKETING)
            definition = definition.replace('APP_RELEASING', settings.APP_RELEASING)
            definition = definition.replace('APP_REVIEWING', settings.APP_REVIEWING)
            definition = definition.replace('APP_BUILDING', settings.APP_BUILDING)
            definition = definition.replace('APP_TESTING', settings.APP_TESTING)
            f = open(project_path,'w')
            f.write(definition)
            f.close()
        content = {}
        try:
            exec(open(project_path).read(), globals())
        except NameError as err:
            raise QError("Invalid configuration: %r.", err)

        return Project()
