# -*- coding: utf-8 -*-
# AUTHOR: vuolter

class Abort(Exception):
    """
    raised when aborted.
    """


class Fail(Exception):
    """
    raised when failed.
    """


class Reconnect(Exception):
    """
    raised when reconnected.
    """


class Retry(Exception):
    """
    raised when start again from beginning.
    """


class Skip(Exception):
    """
    raised when download should be skipped.
    """
