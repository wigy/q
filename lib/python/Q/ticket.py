import sys
import inspect
import re
import os
import random
import readline
import glob
import time
import shutil
from distutils.dir_util import mkpath

from error import QError
from settings import QSettings
from file import QFile


class Ticket:
    """
    Ticket data we are working on.

    Status options and their next states:

   => 'New' - Created but not started.
          => 'Started' - With 'q start' command.
   => 'Watching' - Started watching someone else's ticket.
      'Started' - Work has been started, but no sign of progress.
          => 'Working' - With 'q commit' command.
      'Working' - Work is in progress.
          => 'Building' - With 'q build make' command.
          => 'Review' - With 'q review make' command.
          => 'Waiting' - When process completed manually.
      'Building' - A test build in progress.
          => 'Building + Review' - With 'q review make' command.
          => 'Waiting' once build result complete.
      'Reviewing' - Waiting for review.
          => 'Building + Reviewing' - With 'q build make' command.
          => 'Waiting' once review results received.
      'Building + Reviewing' - Waiting for build and review.
          => 'Reviewing' once build result complete.
          => 'Building' once review results received.
          => 'Waiting' once both build and review results received.
      'Waiting' - Waiting for review and/or build to finish.
          => 'Ready' - Once build and review is successfully completed.
      'Ready' - Ready to be released.
          => 'Done' - With 'q release' command.
   <= 'Done' - Ticket has been completed.
          => 'Working' - With 'q reopen' command.
   <= 'Canceled' - Ticket has been canceled and it will not going to be made.
          => 'Working' - With 'q reopen' command.

    TODO: Fill in the complete process. Maybe move status setting to own function to enforce correct flow.
    """
    STATUS_MAP = {None : ['New', 'Watching', 'Started'],
                  'New': ['Started'],
                  'Watching': ['Waiting'],
                  'Started': ['Working', 'Canceled'],
                  'Working': ['Building', 'Reviewing', 'Canceled', 'Waiting'],
                  'Building': ['Building + Reviewing', 'Working', 'Waiting'],
                  'Reviewing': ['Building + Reviewing', 'Working', 'Waiting'],
                  'Building + Reviewing': ['Building', 'Reviewing'],
                  'Waiting': ['Reviewing', 'Building', 'Ready', 'Canceled', 'Working'],
                  'Ready' : ['Done'],
                  'Done': ['Working'],
                  'Canceled': ['Working'],
                  }

    def set_status(self, new):
        """
        Verify and set new status. Special status 'End X' is used to remove partial status of double status.
        """
        old = self['Status']
        if new == 'End Building':
            if old == 'Building + Reviewing':
                new = 'Reviewing'
            elif old == 'Working':
                new = 'Working'
            else:
                new = 'Waiting'
        if new == 'End Reviewing':
            if old == 'Building + Reviewing':
                new = 'Building'
            elif old == 'Working':
                new = 'Working'
            else:
                new = 'Waiting'
        if not new is None and not new in Ticket.STATUS_MAP:
            raise QError("Cannot set status %r, which does not exist.", new)
        if ((old == 'Building' and new == 'Reviewing') or
            (old == 'Reviewing' and new == 'Building')):
            new = 'Building + Reviewing'
        if old == new:
            return
        if new in Ticket.STATUS_MAP[old]:
            self['Status'] = new
            if new == 'Done':
                self['Finished'] = time.strftime('%Y-%m-%d %H:%M')
        else:
            raise QError("Cannot switch from status %r to %r.", old, new)

    def __init__(self, cmd, code=None):
        self.cmd = cmd
        self.root_path = QSettings.WORKDIR
        self.code = code
        self.data = {}

    def __setitem__(self, k, v):
        if type(v)==list:
            label = "Set '%s'=" % k
            for i in v:
                self.wr(label+i)
                label = " " * (7 + len(k))
            self.data[k] = "\n".join(v)
        else:
            self.wr("Set '%s'='%s'", k, v)
            self.data[k] = v

    def __getitem__(self, k):
        if k in self.data:
            return self.data[k]
        return None

    def __repr__(self):
        ret = {}
        for k in self.all_keys():
            v = self[k]
            if not v is None:
                ret[k] = v
        if self.code:
            code = '#' + self.code + ' '
        else:
            code = '#NoCode '
        return '<Q.Ticket ' + code + repr(ret) + '>'

    def list(self, k):
        """
        Get the ticket data in list format splitted from newlines.
        """
        ret = self.__getitem__(k)
        if type(ret) == str:
            ret = ret.strip()
            if ret == "":
                return []
            return ret.split("\n")
        return []

    def delete(self, k):
        """
        Delete ticket attribute.
        """
        if k in self.data:
            self.wr("Delete '%s'", k)
            del self.data[k]

    def wr(self, *msg, **kwargs):
        """
        Print out run time message.
        """
        channel=kwargs.get('channel')
        if not channel:
            if self.code:
                channel = "#"+self.code
            else:
                channel = "#NoTicket"

        self.cmd.wr(*msg, channel=channel)

    def path(self, subdir=None):
        """
        Get the path to the ticket data (optionally add subdir).
        """
        if not self.code:
            return None
        if not QSettings.WORKDIR:
            raise QError("Ticket storage directory WORKDIR is not set.")
        ret = self.root_path + "/" + self.code
        if subdir:
            ret += "/" + subdir
        return ret

    def url(self):
        """
        Get the URL of the ticket in the ticketing system.
        """
        return self.cmd.app.ticket_url(self)

    def exists(self, code):
        """
        Check if this ticket path exists.
        """
        if not QSettings.WORKDIR:
            raise QError("Ticket storage directory WORKDIR is not set.")
        if os.path.isdir(self.root_path + "/" + code):
            return True
        return False

    def mkdir(self, path):
        """
        Check and create a directory if not exist.
        """
        if not os.path.isdir(path):
            os.mkdir(path)

    def create(self):
        """
        Create new ticket.
        """
        self.wr("Created ticket in '%s'.",self.path())
        self.mkdir(self.path())

    def destroy(self):
        """
        Remove all ticket data.
        """
        self.wr("Destroying ticket data in '%s'.",self.path())
        shutil.rmtree(self.path())

    def load(self):
        """
        Load the ticket data.
        """
        self.data = {}
        if not self.exists(self.code):
            self.create()
        else:
            path = self.path('README')
            self.data = QFile(path).load()

    def save(self):
        """
        Save the ticket data.
        """
        if not self.exists(self.code):
            self.create()
        path = self.path('README')
        self.wr("Saving ticket in '%s'.", path)
        QFile(path).save(self.data, self.all_keys())

    def all_keys(self):
        """
        Get the list of all officially supported keys.
        """
        return ['Title', 'Status', 'Started', 'Finished', 'Base', 'Branch',
                'URL', 'User', 'Review', 'Review Result', 'Review ID', 'Review Info',
                'Build Result', 'Build ID', 'Build Info', 'Dump', 'DB',
                'Tests', 'Files', 'Notes', 'Owner', 'Ticket Info']

    def keys(self):
        """
        Get the list of official keys found in ticket data.
        """
        ret = []
        for k in self.all_keys():
            if k in self.data:
                ret.append(k)
        return ret

    def branch_name(self):
        """
        Get the branch name or generate it if not yet set.
        """
        from helper import Git
        if self['Branch']:
            return self['Branch']
        ret = QSettings.BRANCH_NAMING
        ret = ret.replace('%c', self.code)
        ret = ret.replace('%u', Git().username())
        comment = self['Title'].replace(' ','_').lower()
        title = ''
        for c in comment:
            if re.match(r'[0-9a-z]',c):
                title += c
            elif c == ':':
                title += '__'
            elif c == '_' or re.match(r'[^.?!"\']',c):
                if title != '' and title[-1] != '_':
                    title += '_'
        if title[-1] == '_':
            title = title[0:-1]
        ret = ret.replace('%t', title)
        return ret

    def base_branch(self):
        """
        Get the branch name this ticket is originating from.
        """
        base = QSettings.BASE_BRANCH
        if self['Base']:
            base = self['Base']
        return base

    def branch_number_of(self, name):
        """
        Get the ticket number from branch name.
        """
        g = re.match(QSettings.TICKET_BRANCH_REGEX, name)
        if g:
            return g.group(1)

    @classmethod
    def all_codes(cls):
        """
        Get the list of all codes for tickets found.
        """
        from q import Q
        if not QSettings.WORKDIR:
            raise QError("Ticket storage directory WORKDIR is not set.")
        ret = []
        if not os.path.isdir(QSettings.WORKDIR):
            Q.wr("Initialize", "Creating ticket directory '%s'.", QSettings.WORKDIR)
            mkpath(QSettings.WORKDIR)
        for p in os.listdir(QSettings.WORKDIR):
            if os.path.isfile(QSettings.WORKDIR+"/"+p+"/README"):
                ret.append(p)
        return ret

    def print_summary(self):
        """
        Print basic details of the ticket.
        """
        self.wr("Title: "+self['Title'])
        self.wr("Branch: "+Q.BRANCH+self.branch_name()+Q.END)

    def reviews(self):
        """
        Count existing reviews for this ticket.
        """
        return len(glob.glob(self.path() + "/review-*.diff"))

    def leave(self):
        """
        Hook to be called when about to switch to another ticket.
        """
        from q import Q
        from helper import Git
        Q('my','revert')
        if Git().has_changes():
            Git()('stash save --include-untracked QuickAutoStash_'+self.code)

    def enter(self):
        """
        Hook to be called immediately after switched to this ticket.
        """
        from q import Q
        from helper import Git
        db = self['DB']
        if db and db != self.cmd.app.db_info()['db']:
            self.wr("Switching to DB '%s'." % db)
            self.cmd.app.change_db(db)
            # TODO: Restart servers
        Git()('checkout '+self.branch_name())
        for line in Git()('stash list', get_output=True).strip().split("\n"):
            hit = re.match(r'(stash@\{.+\}).*QuickAutoStash_(\d+)',line.strip())
            if hit and hit.group(2) == self.code:
                Git()('stash pop '+hit.group(1))
        if QSettings.USE_SUBMODULES:
            Git()('submodule update', chdir=QSettings.APPDIR)
        Q('my','apply')

    def changed_files(self):
        """
        Get the list of files that has been changed for this ticket.
        """
        from helper import Git
        return Git()('diff --name-only '+self.merge_base(), get_output=True).strip().split("\n")

    def finished(self):
        """
        Check if this ticket count as finished working.
        """
        return self['Status'] in ('Done', 'Canceled')

    def merge_base(self):
        """
        Get merge base from configuration or git.
        """
        from helper import Git
        if self['Base']:
            return self['Base']
        return Git().merge_base()

    def refresh(self):
        """
        Refresh relevant fields carrying information about external processes etc.
        """
        if self.finished():
            return

        save = False

        if self['Build ID'] and self['Build Result'] not in ['Success', 'Fail']:
            state = self.cmd.app.build_status(self)
            if state and self['Build Result'] != state:
                self['Build Result'] = state
                save = True

        if self['Review ID'] and self['Review Result'] not in ['Success', 'Fail']:
            state = self.cmd.app.review_status(self['Review ID'])
            if state and self['Review Result'] != state:
                self['Review Result'] = state
                save = True

        if self['Review ID'] and self['Review Result'] != 'Pending' and 'Reviewing' in self['Status']:
            self.set_status('End Reviewing')
            save = True

        if self['Build ID'] and self['Build Result'] != 'Pending' and 'Building' in self['Status']:
            self.set_status('End Building')
            save = True

        if self['Status'] == 'Working' and self['Review Result'] == 'Success' and self['Build Result'] == 'Success':
            self.set_status('Waiting')
            save = True

        if self['Status'] == 'Waiting':
            if self['Review Result'] == 'Fail' or self['Build Result'] == 'Fail':
                self.set_status('Working')
                save = True
            elif self['Review Result'] == 'Success' and self['Build Result'] == 'Success':
                self.set_status('Ready')
                save = True

        if self['Status'] == 'Ready':
            if self.cmd.app.release_can_be_skipped(self):
                self.set_status('Done')
                save = True

        if save:
            self.save()

    def flags(self):
        """
        Get the collection of flags to identify state as a short string.
        """
        from q import Q
        ret = self['Status']
        if self.finished() or self['Status'] == 'Ready':
            return ret

        if self['Build ID']:
            if self['Build Result']=='Fail':
                ret += Q.NOTE+" Build:"+self['Build Result']+Q.END
            else:
                ret += " Build:"+self['Build Result']
        if self['Review ID']:
            if self['Review Result']=='Fail':
                ret += Q.NOTE+" Review:"+self['Review Result']+Q.END
            else:
                ret += " Review:"+self['Review Result']
        return ret
