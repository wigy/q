import sys
import os
import re

from error import QError
from settings import QSettings
from building import NoBuild
from reviewing import ReviewByReviewBoard, ReviewByGerrit, ReviewByVSTS, NoReview
from testing import TestingByNose, TestingByShellCommands
from database import DatabaseByDjango
from ticketing import TicketingByTrac, ManualTicketing, VSTSTicketing
from releasing import NoReleasing, ReleasingByGerrit
from command import Command


class QProject:
    """
    Base functionality for querying and executing tasks for the application project.
    """

    def parse(self, *argv):
        if len(argv):
            if len(argv) == 1 and re.match(QSettings.TICKET_NUMBER_REGEX, argv[0]):
                cmd = 'go'
            else:
                cmd = argv[0]
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
