# TODO: Rename this file 'building.py'
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
from helper import Curl, Grunt


class BuildMixin:
    """
    Base class for build mixins.
    """

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
