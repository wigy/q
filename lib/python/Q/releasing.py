from .error import QError
from .helper import Git


class ReleasingMixin:
    """
    Base class for releasing implementations.
    """

    def release_ticket(self, ticket):
        """
        Send the ticket to the releasing process.
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
    Gerrit version of releasing.
    """

    def release_can_be_skipped(self, ticket):
        return False


class ReleasingByBamboo(ReleasingMixin):
    """
    Bamboo version of releasing.
    """

    def release_can_be_skipped(self, ticket):
        return False


class ReleasingByMerge(ReleasingMixin):
    """
    Simply merge the ticket to the master.
    """

    def release_can_be_skipped(self, ticket):
        return False

    def release_ticket(self, ticket):
        """
        Merge the ticket.
        """
        from .q import Q
        if not self.settings.RELEASE_BRANCH:
            raise QError("Must set RELEASE_BRANCH in order to use ReleasingByMerge.")
        self.Q('my','revert')
        Git(self.settings)('checkout "'+ self.settings.RELEASE_BRANCH + '"')
        Git(self.settings)('pull')
        Git(self.settings)('merge "'+ ticket.branch_name() + '"')
        self.Q('my','apply')
        Git(self.settings)('push "' + self.settings.GIT_REMOTE + '" "' + self.settings.RELEASE_BRANCH + '"')
        Git(self.settings)('checkout "'+ ticket.branch_name() + '"')
        self.Q('done')
        Git(self.settings)('checkout "'+ self.settings.RELEASE_BRANCH + '"')
        return True
