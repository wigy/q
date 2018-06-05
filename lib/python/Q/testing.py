from .error import QError
from .helper import Nose, SystemCall


class TestingMixin:
    """
    Base class for testing system implementation.
    """

    def run_test(self, test_spec):
        """
        Run the given test in application specific manner.
        """
        raise QError("Not implemented in %s: run_test().", self.__class__.__name__)


class TestingByShellCommands(TestingMixin):
    """
    General purpose testing by executing any shell command.
    """

    def run_test(self, spec):
        class ShellTest(SystemCall):
            command=None

        ShellTest()(command=spec)


class TestingByNose(TestingMixin):
    """
    Implementation of testing by Nose.
    """

    def run_test(self, spec):
        """
        Run nose test.
        """
        Nose()("-s --with-django --logging-level=INFO "+spec, app=self)
