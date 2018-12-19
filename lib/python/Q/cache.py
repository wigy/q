import os
import time
import pickle
from .settings import QSettings

class QCache:
    """
    A cache for storing network intensive result queries.
    """

    cache = None

    @classmethod
    def get(cls, id, fn):
        if QSettings.OFFLINE_MODE:
            return None
        if QCache.cache is None:
            QCache.load()
        if id not in QCache.cache or (time.time() - QCache.cache[id]['time']) / 60 > int(QSettings.CACHING_TIME_MIN):
            QCache.cache[id] = {
                "time": time.time(),
                "value": fn()
            }
            QCache.save()
        return QCache.cache[id]['value']

    @classmethod
    def path(cls):
        return os.path.join(QSettings.APPDIR, '.q.cache')

    @classmethod
    def save(cls):
        with open(QCache.path(), 'wb') as output:
            pickle.dump(QCache.cache, output, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls):
        try:
            with open(QCache.path(), 'rb') as input:
                QCache.cache = pickle.load(input)
        except IOError:
            QCache.cache = {}
