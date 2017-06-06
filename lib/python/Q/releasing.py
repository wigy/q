from settings import QSettings
from error import QError


class ReleasingMixin:
    """
    Base class for releasing implementations.
    """

    def release_ticket(self, ticket):
        """
        Send the ticket to the relasing process.
        """
        raise QError("Not implemented in %s: release_ticket().", self.__class__.__name__)

    def release_can_be_skipped(self, ticket):
        """
        If True, we can go straight to the 'Done' from 'Ready'.
        """
        raise QError("Not implemented in %s: release_ticket().", self.__class__.__name__)


class NoReleasing(ReleasingMixin):
    """
    Releasing can be skipped.
    """

    def release_can_be_skipped(self, ticket):
        return True


class ReleasingByGerrit(ReleasingMixin):
    """
    Gerrit version of relasing.
    """

    def release_can_be_skipped(self, ticket):
        return False
