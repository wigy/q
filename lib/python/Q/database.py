from .error import QError
from .settings import QSettings
from .helper import Mysql, Sed


class DatabaseMixin:
    """
    Base class for database handler mixins.
    """
    def db_info(self):
        """
        Get a dict 'user', 'pass', 'db', 'host' for the application.
        """
        raise QError("Not implemented %s: db_info().", self.__class__.__name__)

    def db_reset(self):
        """
        Create new empty database.
        """
        info = self.db_info()
        Mysql().create(info)


class DatabaseByDjango(DatabaseMixin):
    """
    Implementation of the Django database.
    """

    def db_info(self):
        """
        Get a dict 'user', 'pass', 'db', 'host' for the application.
        """
        self.set_path()
        import settings
        conf = settings.DATABASES['default']
        return {'db' : conf['NAME'],
                'host' : conf['HOST'],
                'user' : conf['USER'],
                'pass' : conf['PASSWORD']}
