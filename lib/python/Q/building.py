import sys
import inspect
import re
import os
import random
import readline
import glob
import time
import shutil
import requests
import json

from .settings import QSettings
from .error import QError
from .helper import Curl, Grunt


class BuildMixin:
    """
    Base class for build mixins.
    """

    def build_is_auto(self):
        """
        Check of the build success is automatic.
        """
        return False

    def build_start(self, ticket, gitid):
        """
        Build the code based on git-commit id and return build_id.
        """
        raise QError("Not implemented in %s: build().", self.__class__.__name__)

    def build_url(self, ticket):
        """
        Get the URL for the given build.
        """
        raise QError("Not implemented in %s: build_url().", self.__class__.__name__)

    def build_status(self, ticket):
        """
        Fetch the build status 'Pending', 'Success', 'Fail' or percentage.
        """
        raise QError("Not implemented in %s: build_status().", self.__class__.__name__)


class NoBuild(BuildMixin):
    """
    No building. Automatically success.
    """

    def build_is_auto(self):
        return True

    def build_start(self, ticket, gitid):
        return 'AutoSuccess'

    def build_url(self, ticket):
        """
        Get the URL for the given build.
        """
        return None

    def build_status(self, ticket):
        """
        Fetch the build status 'Pending', 'Success' or 'Fail'.
        """
        return 'Success'

class BuildByBamboo(BuildMixin):

    def build_start(self, ticket, gitid):
        if not QSettings.BAMBOO_URL:
            raise QError("Must define BAMBOO_URL to build.")
        if not QSettings.BAMBOO_PLANS:
            raise QError("Must define BAMBOO_PLANS to build.")
        ret = {}
        for plan in QSettings.BAMBOO_PLANS.split("\n"):
            url = QSettings.BAMBOO_URL + "rest/api/latest/queue/%s.json?customRevision=%s" % (plan, gitid)
            resp = requests.post(url, auth=self._build_auth(), verify=False)
            data = resp.json()
            ret[data['planKey']] = data['buildNumber']
        return json.dumps(ret)

    def build_status(self, ticket):
        builds = json.loads(ticket['Build ID'])
        success = 0
        fail = 0
        total = 0
        for plan in builds.keys():
            total += 1
            url = QSettings.BAMBOO_URL + "rest/api/latest/result/%s/%s.json" % (plan, builds[plan])
            try:
                resp = requests.get(url, auth=self._build_auth(), verify=False)
                data = resp.json()
            except Exception, e:
                print resp
                print e
                raise QError('Getting status failed.')
            state = data['state']
            if state == 'Successful':
                success += 1
            elif state == 'Unknown':
                pass
            elif state == 'Failed':
                fail += 1
            else:
                raise QError('Unknown status of build: %r.' % state)
        if fail:
            return 'Fail'
        if success < total:
            return str(success) + '/' + str(total)
        return 'Success'

    def build_url(self, ticket):
        if ticket['Build ID']:
            builds = json.loads(ticket['Build ID'])
            ret = []
            for plan in builds.keys():
                ret.append(QSettings.BAMBOO_URL + 'browse/%s-%d' % (plan, builds[plan]))
            return "\n".join(ret)

    def _build_auth(self):
        """
        Authentication parameter.
        """
        if not QSettings.BAMBOO_USER:
            raise QError("User for Bamboo BAMBOO_USER is not set.")
        if not QSettings.BAMBOO_PASSWORD:
            raise QError("Password for Bamboo BAMBOO_PASSWORD is not set.")
        return (QSettings.BAMBOO_USER, QSettings.BAMBOO_PASSWORD)
