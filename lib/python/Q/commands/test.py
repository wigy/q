from ..command import AutoGoCommand
from ..error import QError
from ..settings import QSettings


class CommandTest(AutoGoCommand):
    """
    List or add or run tests for the ticket.
    """
    param_aliases = {
                     'a' : 'add',
                     'd' : 'del',
                     'r' : 'run',
                     }

    def run(self):
        """
        usage: q test [<code>] [add <test_spec>|del <test_spec>|run [<test_spec>]]
        """
        from ..q import Q
        # TODO: Automatic scanner, which searches diff for tests and adds them to the list.
        tests = self.ticket.list('Tests')
        if not self.args:
            if not tests:
                self.wr("No tests defined, please use "+Q.COMMAND+"q test add <test_spec>"+Q.END+" to add one.")
            for t in tests:
                self.wr(t)
        elif self.args[0] == 'add':
            add = " ".join(self.args[1:])
            if not add:
                raise QError("No specification for test given.")
            else:
                if not add in tests:
                    tests.append(add)
                    self.ticket['Tests'] = tests
                    self.ticket.save()
        elif self.args[0] == 'del':
            delete = " ".join(self.args[1:])
            if not delete in tests:
                raise QError("No such test as '%s'",delete)
            else:
                i = tests.index(delete)
                del tests[i]
                self.ticket['Tests'] = tests
                self.ticket.save()
        elif self.args[0] == 'run':

            if QSettings.DB_NAME:
                old_db = ['db']
                new_db = QSettings.TEST_DATABASE
            else:
                old_db = None
                new_db = None
            if new_db and old_db != new_db:
                self.wr("Changing to the test database '%s'.", Q.NOTE+new_db+Q.END)
                self.app.change_db(new_db)
            test = " ".join(self.args[1:])
            if test:
                tests = [test]
            for t in tests:
                self.wr("Running: %s", t)
                self.app.run_test(t)
                if not t in self.ticket.list('Tests'):
                    self.wr("Note: This is not part of the test list.")
                    self.wr("You can add this test to the test list by running")
                    self.wr(Q.COMMAND+"q test add "+t+Q.END)
            if old_db and old_db != new_db:
                self.wr("Restoring old database '%s'.", Q.NOTE+old_db+Q.END)
                self.app.change_db(old_db)
        else:
            raise QError("Invalid arguments.")
