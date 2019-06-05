import sys
import inspect
import re
import os
import random
import readline
import glob
import time
import shutil
import tempfile
import requests

from .error import QError
from .file import QFile
from .ticket import Ticket


class QHelper(object):
    """
    A helper base class.
    """
    toolkit = {}

    def __init__(self, settings = None):
        self.settings = settings

    def __call__(self, *args, **kwargs):
        """
        Wrapper to execute run().
        """
        return self.run(*args, **kwargs)

    def wr(self, *msg):
        """
        Print out run time message.
        """
        from q import Q
        Q.wr('*' + self.__class__.__name__, *msg)

    def run(self, *args, **kwargs):
        """
        Main action of the helper.
        """
        raise QError("A helper '%s' does not implement run().", self.__class__.__name__)


class Sed(QHelper):

    def run(self, path, regex, replace):
        """
        Replace with regex all lines matching on the given file.
        Regex must have 3 pairs of parenthesis with the middle taken as replacement.
        """
        data = ""
        found = False
        r = re.compile(regex)
        for line in QFile(path).read().rstrip().split("\n"):
            match = r.match(line)
            if match:
                found = True
                groups = match.groups()
                data += groups[0] + replace + groups[2]
            else:
                data += line
            data += "\n"
        if found:
            QFile(path).write(data)


class Curl(QHelper):

    def run(self, url, post=None, put=None, patch=None, upload=None, quiet=False, user=None, password=None, content_type=None):
        """
        Make a HTTP-request and return the results.
        """
        from q import Q
        if self.settings.OFFLINE_MODE == 'yes':
            self.wr("Skipping in offline-mode: "+Q.URL + url + Q.END)
            return ''
        import pycurl
        import cStringIO
        import urllib
        buf = cStringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.WRITEFUNCTION, buf.write)
        method = 'GET'
        if post:
            method = 'POST'
            c.setopt(c.POSTFIELDS, urllib.urlencode(post))
        if put:
            method = 'PUT'
            c.setopt(c.CUSTOMREQUEST, "PUT")
            c.setopt(c.POSTFIELDS, urllib.urlencode(put))
        if patch:
            method = 'PATCH'
            c.setopt(c.CUSTOMREQUEST, "PATCH")
            c.setopt(c.POSTFIELDS, patch)
        if upload:
            method = 'POST'
            values = []
            for path in upload.keys():
                values.append((path, (pycurl.FORM_FILE, upload[path])))
            c.setopt(c.HTTPPOST, values)
        if content_type:
            c.setopt(pycurl.HTTPHEADER, ["Content-Type: %s" % content_type])
        if not quiet:
            self.wr("Calling: "+method +" " +Q.URL + url + Q.END)
        if os.environ.get('http_proxy'):
            c.setopt(c.PROXY, os.environ.get('http_proxy'))
        if user:
            c.setopt(c.USERNAME, user)
        if password:
            c.setopt(c.PASSWORD, password)
        c.setopt(c.FOLLOWLOCATION, True)
#        c.setopt(c.VERBOSE, True)
        try:
            c.perform()
        except pycurl.error, e:
            raise QError('Curl call to %r failed: %r', url, e)
        ret = buf.getvalue()
        buf.close()
        return ret


class Requests(QHelper):
    """
    Newer HTTP helper version using `requests`.
    """
    def run(self, url, post=None, put=None, delete=None, patch=None, upload=None, quiet=False, user=None, password=None, auth=None):
        from q import Q
        if self.settings.OFFLINE_MODE == 'yes':
            self.wr("Skipping in offline-mode: "+Q.URL + url + Q.END)
            return None
        if user:
            auth = (user, password)
        method = requests.get
        json = None
        if post:
            method = requests.post
            json = post
        elif put:
            method = requests.put
            json = put
        elif patch:
            method = requests.patch
            json = patch
        elif delete:
            method = requests.delete
        return method(url, auth=auth, json=json)


class SystemCall(QHelper):
    """
    Interface for running specific system commands.
    """
    command = None

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """
        Run the command.
        Options:
            get_output - return the output of the command
            no_echo - don't print the command to be run
            stderr - if set, redirect stderr to stdout
            command - change the default command
            chdir - change directory to this before running the command
        """
        from q import Q
        command_name = kwargs.get('command', None)
        if not command_name:
            command_name = self.command
        cmd = command_name + " " + " ".join(args)
        outfile = None
        if kwargs.get('get_output',False):
            outfile = "/tmp/output-"+os.environ['USER']+"-"+str(random.random())
            cmd += " > "+outfile
        if kwargs.get('stderr',False):
            cmd += " 2>&1"
        chdir = kwargs.get('chdir',False)
        if chdir:
            cmd = "cd "+chdir+"; "+cmd
        if not kwargs.get('no_echo',False):
            self.wr(Q.COMMAND+cmd+Q.END)
        ret = None
        ret = os.system(cmd)
        if outfile:
            ret = QFile(outfile).read()
            os.remove(outfile)
        return ret


class Mysql(SystemCall):
    """
    Interface to mysql operations.
    """
    command = 'mysql'

    def _cmd(self, dbinfo):
        """
        Construct command line arguments for the given database.
        """
        cmd = '-u"'+dbinfo['user']+'" -h"'+dbinfo['host']+'"'
        if dbinfo['pass']:
            cmd += ' -p"'+dbinfo['pass']+'"'
        return cmd

    def open(self, dbinfo):
        """
        Open command-line prompt for the DB.
        """
        cmd = self._cmd(dbinfo)
        cmd += ' ' + dbinfo['db']
        return self.run(cmd)

    def save(self, dbinfo, path):
        """
        Create dump of the database to the given file.
        """
        cmd = self._cmd(dbinfo)
        cmd += ' ' + dbinfo['db'] + ' > '+ path
        return self.run(cmd, command='mysqldump')

    def load(self, dbinfo, path):
        """
        Load a dump of the database from the given file.
        """
        cmd = self._cmd(dbinfo)
        cmd += ' '+dbinfo['db'] + ' < '+ path
        return self.run(cmd, command='mysql')

    def exists(self, dbinfo):
        """
        Check if the given database exists.
        """
        cmd = self._cmd(dbinfo)
        for line in self.run('show databases | mysql '+cmd, command='echo', get_output=True).split("\n"):
            if line == dbinfo['db']:
                return True
        return False

    def destroy(self, dbinfo):
        """
        Delete the given database.
        """
        cmd = self._cmd(dbinfo)
        return self.run('y | mysqladmin '+cmd+' drop '+dbinfo['db'], command='echo')

    def create(self, dbinfo):
        """
        Create new database.
        """
        if self.exists(dbinfo):
            self.destroy(dbinfo)
        cmd = self._cmd(dbinfo)
        cmd += ' create '+dbinfo['db']
        return self.run(cmd, command='mysqladmin')


class Git(SystemCall):
    """
    Interface to GIT operations.
    """

    command = 'git'
    user = None

    def current_branch_name(self, ignore_error=False):
        """
        Resolve the name of the current branch.
        """
        for line in self.run('status', get_output=True, no_echo=True, stderr=True).split("\n"):
            name = re.search(r'On branch (.+)', line)
            if name:
                return name.group(1)
        if ignore_error:
            return None
        raise QError("Not currently on the git working directory or not on any specific branch.")

    def branch_exists(self, name):
        text = self.run('rev-parse --verify ' + name, get_output=True, stderr=True)
        if re.match('^[0-9a-f]+$', text.strip()):
            return True
        return False

    def latest_commit(self,branch=None):
        """
        Get the commit code of the latest commit of current or given branch.
        """
        args='-1'
        if branch:
            args += ' '+branch
        for line in self.run('log '+args, get_output=True, no_echo=True).split("\n"):
            hit = re.search(r'^commit\s+(.+)', line)
            if hit:
                return hit.group(1)

    def merge_base(self):
        """
        Find the commit code of the latest commit in develop branch.
        """
        develop = self.latest_commit(self.settings.BASE_BRANCH)
        this = self.latest_commit()
        commit = self.run('merge-base '+this+' '+develop, get_output=True)
        return commit.strip()

    def username(self):
        """
        Resolve user name from git remote listing.
        """
        if Git.user:
            return Git.user
        for line in self.run('remote -v',get_output=True, no_echo=True).split("\n"):
            hit = re.search(r'[a-z]:\/\/(.+?)@', line)
            if hit:
                Git.user = hit.group(1)
                return self.user
        if self.settings.GIT_USER:
            return self.settings.GIT_USER
        raise QError("Cannot find git user (are we on working directory?).")

    def has_changes(self):
        """
        Verify if there are any changes to commit.
        """
        ret = True
        for line in self.run('status',get_output=True, no_echo=False).split("\n"):
            if re.search(r'nothing to commit.*working (tree|directory) clean', line):
                ret = False
                break
        return ret

    def patch(self, diff, reverse=False):
        """
        Apply a patch from the diff file.
        """
        if reverse:
            return self.run('-p1 -R  --no-backup-if-mismatch < '+diff,command='patch', chdir=self.settings.APPDIR)
        else:
            return self.run('-p1 --no-backup-if-mismatch < '+diff,command='patch', chdir=self.settings.APPDIR)

    def missing_files(self):
        """
        Find the files not in git.
        """
        print self.settings
        ret = self.run('ls-files -o --exclude-standard', get_output=True, chdir=self.settings.APPDIR).strip().split("\n")
        if len(ret) == 1 and ret[0] == "":
            return []
        for i in range(len(ret)):
            ret[i] = self.settings.APPDIR + ret[i]
        return ret


class Edit(SystemCall):
    """
    Launcher for IDE or light-weight editor.
    """
    def run(self, *files, **kwargs):
        if kwargs.get('light'):
            editor=self.settings.EDITOR
        else:
            editor=self.settings.IDE
        return super(Edit,self).run(*files, command=editor)

    def temp(self):
        """
        Create temporary file and edit its content returning it.
        """
        temp = tempfile.mkstemp()
        self.run(temp[1], light=True)
        ret = file(temp[1], 'r').read()
        Rm()(temp[1])
        return ret


class Zcat(SystemCall):
    """
    Uncompressor.
    """
    command='zcat'


class Cp(SystemCall):
    """
    Copier.
    """
    command='cp'


class Rm(SystemCall):
    """
    File remover.
    """
    command='rm'


class Grep(SystemCall):
    """
    String search.
    """
    command='grep'


class Nose(SystemCall):
    """
    Helper to look up for nose testing tool and running it.
    """

    def run(self, *args, **kwargs):
        app = kwargs.get('app')
        if app:
            cmd = app.find_file('nosetests')
        else:
            cmd = 'nosetests'
        return super(Nose,self).run(*args, command="DJANGO_SETTINGS_MODULE=test_settings " + cmd)


class Grunt(SystemCall):
    """
    Helper to launch grunt jobs.
    """
    command = 'grunt'

    def run(self, *args, **kwargs):
        if self.settings.GRUNT_DIR is None:
            raise QError("Cannot us Grunt unless GRUNT_DIR has been specified.")
        return super(Grunt,self).run(*args, chdir=os.path.join(self.settings.APPDIR, self.settings.GRUNT_DIR))
