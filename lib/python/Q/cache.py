import os
import time
import pickle
from .settings import QSettings

class QCache:
    """
    A cache for storing network intensive result queries.
    """

    def __init__(self, settings):
        self.cache = None
        self.settings = settings

    def get(self, id, fn):
        if self.settings.OFFLINE_MODE:
            return None
        if self.cache is None:
            self.load()
        if id not in self.cache or (time.time() - self.cache[id]['time']) / 60 > int(self.settings.CACHING_TIME_MIN):
            self.cache[id] = {
                "time": time.time(),
                "value": fn()
            }
            self.save()
        return self.cache[id]['value']

    def path(self):
        return os.path.join(self.settings.APPDIR, '.q.cache')

    def save(self):
        with open(self.path(), 'wb') as output:
            pickle.dump(self.cache, output, pickle.HIGHEST_PROTOCOL)

    def load(self):
        try:
            with open(self.path(), 'rb') as input:
                self.cache = pickle.load(input)
        except IOError:
            self.cache = {}
