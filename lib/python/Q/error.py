class QError(BaseException):
    """
    Exception class for this utility.
    """
    def __str__(self):
        msg = self.args
        if len(msg) > 1:
            args = msg[1:]
            return msg[0] % args
        else:
            return msg[0]

