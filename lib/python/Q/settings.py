import sys
import inspect
import re
import os
import random
import readline
import glob
import time
import shutil

from .file import QFile

class QSettings:
    """
    Initialize configuration for the project.
    """
    def __init__(self):
        # Name of the project.
        self.APP = None
        # Mixin classes to use in the project.
        self.APP_TICKETING = 'ManualTicketing'
        self.APP_RELEASING = 'NoReleasing'
        self.APP_REVIEWING = 'NoReview'
        self.APP_BUILDING = 'NoBuild'
        self.APP_TESTING = 'TestingByShellCommands'
        self.APP_TIMING = 'NoTiming'
        # Root directory of the application git tree.
        self.APPDIR = None
        # Path to the settings (filled automatically).
        self.APPSETTINGS = None
        # Base url for the JIRA tickets.
        self.ATLASSIAN_URL = None
        # Name of the status for tickes in progress.
        self.ATLASSIAN_STATUS_WORKING = 'In Progress'
        # Name of the status for tickes in review.
        self.ATLASSIAN_STATUS_REVIEWING = 'In Review'
        # Name of the status for done tickes.
        self.ATLASSIAN_STATUS_DONE = 'Done'
        # Name of the status for available tickes.
        self.ATLASSIAN_STATUS_AVAILABLE = 'Backlog'
        # Password for the Bamboo.
        self.BAMBOO_PASSWORD = None
        # One or more Bamboo plan codes to launch build.
        self.BAMBOO_PLANS = None
        # Base url of the Bamboo server.
        self.BAMBOO_URL = None
        # Username for the Bamboo.
        self.BAMBOO_USER = None
        # Which branch is used by default as a base for new features.
        self.BASE_BRANCH = 'master'
        # Name of the project in the Bitbucket (https://bitbucket.org/PROJECT/REPO/).
        self.BITBUCKET_PROJECT = None
        # Name of the repository in the Bitbucket (https://bitbucket.org/PROJECT/REPO/).
        self.BITBUCKET_REPO = None
        # User name in the Bitbucket.
        self.BITBUCKET_USER = None
        # Password in the Bitbucket.
        self.BITBUCKET_PASSWORD = None
        # Branch to create pull requests against.
        self.BITBUCKET_PR_TARGET = 'master'
        # New branch name patterb. %c ticket code, %u user, %t title in lower case underscored
        self.BRANCH_NAMING = '%c_%u_%t'
        # Command for local command line building.
        self.BUILD_COMMAND = None
        # How long ticket build and review statuses are cached until refetched.
        self.CACHING_TIME_MIN = 5
        # Format of the commit message: %c ticket code, %m message
        self.COMMIT_MESSAGE = 'Ticket #%c: %m'
        # Name of the database.
        self.DB_NAME = None
        # Which editor to use for editing text files.
        self.EDITOR = 'code'
        # User account in git.
        self.GIT_USER = None
        # Name of the remote used for storing feature branches.
        self.GIT_REMOTE = 'origin'
        # Relative directory inside the project where Grunt jobs are run.
        self.GRUNT_DIR = None
        # URL for grunt builder: %c is build id.
        self.GRUNT_BUILD_URL = None
        # Name of the IDE for code editing.
        self.IDE = 'code'
        # Command to verify syntax for the source code.
        self.LINT = None
        # Colon separated path list of other projects belonging to this work timing group.
        self.LINKED_PROJECTS = None
        # Name of the branch we hang around, when there is no ticket selected.
        self.LOBBY_BRANCH = 'master'
        # If set, do not do any network queries.
        self.OFFLINE_MODE = False
        # Name of the branch we merge tickets with merge releasing.
        self.RELEASE_BRANCH = None
        # URL of the server to be used for reviewing.
        self.REVIEW_SERVER = None
        # Name of the repository to post review requests.
        self.REVIEW_REPOSITORY = None
        # Name of the user to log in to the review server.
        self.REVIEW_USER = None
        # Format of the review URL if used by the review system.
        self.REVIEW_URL = None
        # Password of the user to log in to the review server.
        self.REVIEW_PASS = None
        # If set, we need to have 'Build ID' set before review and it is added to review.
        self.REVIEW_NEEDS_BUILD = False
        # Title format of the review: %c ticket code, %t ticket title
        self.REVIEW_TITLE = 'Ticket #%c: %t'
        # Description format of the review: %u url of ticket
        self.REVIEW_DESCRIPTION = '\nTicket %u\n'
        # Description format of the additional review info: %b url of the build.
        self.REVIEW_ADDITIONAL_DESCRIPTION = ''
        # Review groups to receive review request.
        self.REVIEW_GROUPS = None
        # How many "Ship It!" is required to pass.
        self.REVIEW_SHIPITS = 1
        self.TEST_DATABASE = None
        # Regex extracting the ticket code from the git branch.
        self.TICKET_BRANCH_REGEX = r'([0-9]+)'
        # Regex matching ticket code when given as an argument to Q.
        self.TICKET_NUMBER_REGEX = r'^([0-9]+)$'
        # User ID in the ticketing system.
        self.TICKETING_ID = None
        # User name or ID in the ticketing system.
        self.TICKETING_USER = None
        # Password in the ticketing system.
        self.TICKETING_PASSWORD = None
        # What milestone to use in Trac when new ticket has been created.
        self.TRAC_INITIAL_MILESTONE = None
        # What milestone to use in Trac when starting work on ticket.
        self.TRAC_WORKING_MILESTONE = None
        # Trac API address.
        self.TICKETING_TRAC_API = None
        # Generic ticket URL.
        self.TICKET_URL = None
        # If set, we have submodules in our project.
        self.USE_SUBMODULES = False
        # Directory to store local ticket data.
        self.WORKDIR = None
        # Timestamp of work starting time for work log purposes.
        self.WORK_START = '09:00:00'
        # Timestamp of work finishing time for work log purposes.
        self.WORK_END = '17:00:00'
        # How many working hours during the day.
        self.WORK_HOURS = 7.5
        # Name of the VSTS instance, i.e. hostname of visualstudio.com.
        self.VSTS_INSTANCE = None
        # Name (full name and email) to be used when assigning ownership for things.
        self.VSTS_FULL_NAME = None

    def __repr__(self):
        if self.APPSETTINGS:
            return '<Q.Settings ' + self.APPSETTINGS + '>'
        return '<Q.Settings>'

    def dict(self):
        """
        Collect settings and return them as a dictionary.
        """
        ret = {}
        for member in dir(self):
            if re.match(r'^[A-Z_]+$', member):
                ret[member] = self.__dict__[member]
        return ret

    def save(self, path):
        """
        Save the current settings to the given file.
        """
        QFile(path).save(self.dict())

    @staticmethod
    def load(path):
        """
        Load the settings from the given file.
        """
        data = QFile(path).load()
        ret = QSettings()
        for k in data:
            if data[k] == 'True':
                data[k] = True
            if data[k] == 'None':
                data[k] = None
            if data[k] == 'False':
                data[k] = False
            ret.__dict__[k] = data[k]
        ret.APPSETTINGS = path
        return ret

    @staticmethod
    def find(path):
        """
        Find the nearest '.q' file from the directory or from its nearest possible parents.
        """
        file = path + '/.q'
        if os.path.isfile(file):
            return file
        parts = os.path.split(path)
        if parts[0]=='/' or parts[0]=='':
            return None
        return QSettings.find(parts[0])

    @classmethod
    def find_by_code(cls, code):
        """
        Find the project and load its settings by looking into ticket code.
        """
        # TODO: Move elsewhere.
        for p in cls.visit_all():
            QSettings.load(p)
            if re.match(QSettings.TICKET_NUMBER_REGEX, code):
                settings_stack.pop()
                return True
        cls.visit_done()
        return False
