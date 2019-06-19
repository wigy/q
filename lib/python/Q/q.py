import sys
import inspect
import re
import os
import random
import readline
import glob
import time
import shutil

from .settings import QSettings
from .error import QError
from .project import QProject


class Q:
    """
    Quick Tools - One man ERP.
    """
    GRAY = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'
    CHANNEL = BLUE
    TITLE = YELLOW
    BRANCH = MAGENTA
    COMMAND = GREEN
    URL = CYAN
    VAR = CYAN
    FILE = CYAN
    MARKER = RED
    MARK = MARKER+"<=="+END
    ERROR = RED
    NOTE = RED
    USER = GRAY
    USER_ME = WHITE
    TIME = YELLOW
    DATE = CYAN

    # What channel was the last print aiming.
    prev_channel = None
    # All loaded projects, the default is the first.
    projects = []

    def __init__(self, *argv):
        """
        Set up the projects.
        """
        if len(Q.projects):
            raise Exception('Re-running Q' + repr(argv) + ' directly is not permitted anymore.\nPlease use self.Q() instead.')
        if len(argv) > 0 and argv[0] in ['help', 'settings']:
            Q.projects.append(QProject(QSettings(), self))
        else:
            path = QSettings.find(os.getcwd())
            if not path:
                raise QError("Project is not defined. Do you have settings file '.q' created?\nUse " + Q.COMMAND + "q settings save" + Q.ERROR + " to create new settings file template.")
            settings = QSettings.load(path)
            project = QProject.create(settings, self)
            Q.projects.append(project)
            if settings.LINKED_PROJECTS:
                for path in settings.LINKED_PROJECTS.split(':'):
                    path = re.sub('\/$', '', path)
                    settings = QSettings.load(QSettings.find(path))
                    project = QProject.create(settings, self)
                    Q.projects.append(project)

    def find_project(self, code):
        """
        Find the project handling the given ticket code.
        """
        for project in self.projects:
            if re.match(project.settings.TICKET_NUMBER_REGEX, code):
                return project

    @staticmethod
    def wr(channel, *msg):
        """
        Print out run time message.
        """
        if Q.prev_channel != channel:
            sys.stderr.write(Q.CHANNEL + "[ " + channel + " ]" + Q.END + "\n")
            Q.prev_channel = channel
        if len(msg) > 1:
            args = msg[1:]
            sys.stderr.write(unicode(msg[0]) % args)
        else:
            sys.stderr.write(unicode(msg[0]))
        sys.stderr.write("\n")

    def parse(self, *argv):
        """
        Parse and run command.
        """
        Q.projects[0].parse(*argv)
