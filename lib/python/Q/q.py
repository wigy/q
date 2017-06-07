import sys
import inspect
import re
import os
import random
import readline
import glob
import time
import shutil

from settings import QSettings
from error import QError
from project import QProject


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

    prev_channel = None
    settings_loaded = False

    def __init__(self, *argv):
        """
        Parse and run.
        """
        if not Q.settings_loaded:
            Q.settings_loaded = True
            path = QSettings.find()
            if path:
                QSettings.load(path)
        self.parse(*argv)

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
            sys.stderr.write(msg[0] % args)
        else:
            sys.stderr.write(msg[0])
        sys.stderr.write("\n")

    def parse(self, *argv):
        """
        Parse flags and extract command and arguments.
        """
        try:
            if QSettings.APP:
                # TODO: This gives confusing error once .q is created but not edited. Change this logic.
                self.project = QProject.create(QSettings)
            else:
                if len(argv) > 0 and argv[0] in ['help', 'settings']:
                    self.project = QProject()
                else:
                    if QSettings.APPSETTINGS:
                        raise QError("Project name is not defined. Please define " + Q.VAR + "APP" + Q.ERROR + " in " + Q.FILE + QSettings.APPSETTINGS + Q.ERROR + ".")
                    raise QError("Project is not defined. Do you have settings file '.q' created?\nUse " + Q.COMMAND + "q settings save" + Q.ERROR + " to create new settings file template.")
            self.project.parse(*argv)
        except QError as e:
            Q.wr('Fail', Q.ERROR + "ERROR: " + str(e) + Q.END)
            sys.exit(1)
