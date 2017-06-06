import sys
import inspect
import re
import os
import random
import readline
import glob
import time
import shutil

from file import QFile


class QSettings:
    """
    Configuration for the current project.
    """
    # Name of the project.
    APP = None
    # Mixin classes to use in the project.
    APP_TICKETING = 'ManualTicketing'
    APP_RELEASING = 'NoReleasing'
    APP_REVIEWING = 'NoReview'
    APP_BUILDING = 'NoBuild'
    APP_TESTING = 'TestingByShellCommands'
    # Root directory of the application git tree.
    APPDIR = None
    # Path to the settings (filled automatically).
    APPSETTINGS = None
    # Which branch is used by default as a base for new features.
    BASE_BRANCH = 'master'
    # New branch name patterb. %c ticket code, %u user, %t title in lower case underscored
    BRANCH_NAMING = '%c_%u_%t'
    # Format of the commit message: %c ticket code, %m message
    COMMIT_MESSAGE = 'Ticket #%c: %m'
    # Name of the database.
    DB_NAME = None
    # Which editor to use for editing text files.
    EDITOR = 'gedit'
    # User account in git.
    GIT_USER = None
    # Name of the remote used for storing feature branches.
    GIT_REMOTE = 'origin'
    # Relative directory inside the project where Grunt jobs are run.
    GRUNT_DIR = None
    # URL for grunt builder: %c is build id.
    GRUNT_BUILD_URL = None
    # Name of the IDE for code editing.
    IDE = 'eclipse'
    # Name of the branch we hang around, when there is no ticket selected.
    LOBBY_BRANCH = 'master'
    # If set, do not do any network queries.
    OFFLINE_MODE = False
    # URL of the server to be used for reviewing.
    REVIEW_SERVER = None
    # Name of the repository to post review requests.
    REVIEW_REPOSITORY = None
    # Name of the user to log in to the review server.
    REVIEW_USER = None
    # Format of the review URL if used by the review system.
    REVIEW_URL = None
    # Password of the user to log in to the review server.
    REVIEW_PASS = None
    # If set, we need to have 'Build ID' set before review and it is added to review.
    REVIEW_NEEDS_BUILD = False
    # Title format of the review: %c ticket code, %t ticket title
    REVIEW_TITLE = 'Ticket #%c: %t'
    # Description format of the review: %u url of ticket
    REVIEW_DESCRIPTION = '\nTicket %u\n'
    # Description format of the additional review info: %b url of the build.
    REVIEW_ADDITIONAL_DESCRIPTION = ''
    # Review groups to receive review request.
    REVIEW_GROUPS = None
    # How many "Ship It!" is required to pass.
    REVIEW_SHIPITS = 1
    TEST_DATABASE = None
    # Regex extracting the ticket code from the git branch.
    TICKET_BRANCH_REGEX = r'([0-9]+)'
    # Regex matching ticket code when given as an argument to Q.
    TICKET_NUMBER_REGEX = r'^([0-9]+)$'
    # User name in the ticketing system.
    TICKETING_USER = None
    # Password in the ticketing system.
    TICKETING_PASS = None
    # What milestone to use in Trac when new ticket has been created.
    TRAC_INITIAL_MILESTONE = None
    # What milestone to use in Trac when starting work on ticket.
    TRAC_WORKING_MILESTONE = None
    # Trac API address.
    TICKETING_TRAC_API = None
    # Generic ticket URL.
    TICKET_URL = None
    # If set, we have submodules in our project.
    USE_SUBMODULES = False
    # Directory to store local ticket data.
    WORKDIR = None
    # Name of the VSTS instance, i.e. hostname of visualstudio.com.
    VSTS_INSTANCE = None
    # Name (full name and email) to be used when assigning ownership for things.
    VSTS_FULL_NAME = None

    @staticmethod
    def dict():
        """
        Collect settings and return them as a dictionary.
        """
        ret = {}
        for member in dir(QSettings):
            if re.match(r'^[A-Z_]+$', member):
                ret[member] = QSettings.__dict__[member]
        return ret

    @staticmethod
    def save(path):
        """
        Save the current settings to the given file.
        """
        QFile(path).save(QSettings.dict())

    @staticmethod
    def load(path):
        """
        Load the settings from the given file.
        """
        data = QFile(path).load()
        for k in data:
            if data[k] == 'True':
                data[k] = True
            if data[k] == 'None':
                data[k] = None
            if data[k] == 'False':
                data[k] = False
            QSettings.__dict__[k] = data[k]
        QSettings.APPSETTINGS = path

    @staticmethod
    def find(path = None):
        """
        Find the nearest '.q' file from the current directory or from its nearest possible parents.
        """
        if not path:
            path = os.getcwd()
        file = path + '/.q'
        if os.path.isfile(file):
            return file
        parts = os.path.split(path)
        if parts[0]=='/' or parts[0]=='':
            return None
        return QSettings.find(parts[0])
