# -*- coding: utf-8 -*-


class Abort(Exception):
    """
    Raised when aborted.
    """


class Fail(Exception):
    """
    Raised when failed.
    """


class Reconnect(Exception):
    """
    Raised when reconnected.
    """


class Retry(Exception):
    """
    Raised when start again from beginning.
    """


class Skip(Exception):
    """
    Raised when download should be skipped.
    """
