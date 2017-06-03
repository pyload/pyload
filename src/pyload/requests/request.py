# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging
from builtins import object

from future import standard_library

from pyload.utils.struct import HeaderDict

standard_library.install_aliases()


class Abort(Exception):
    """
    Raised when aborted.
    """
    pass


class ResponseException(Exception):
    __slots__ = ['code']

    def __init__(self, code, content=""):
        Exception.__init__(
            self, "Server response error: {0} {1}".format(code, content))
        self.code = code


class Request(object):
    """
    Abstract class to support different types of request, most methods should be overwritten.
    """
    # Class that will be instantiated and associated with the request, and if needed copied and reused
    CONTEXT_CLASS = lambda: None

    def __init__(self, config, context=None, options=None, logger=None):
        self.log = self._get_logger(logger)

        # Global config, holds some configurable parameter
        self.config = config

        # Create a new context if not given
        self.context = self.CONTEXT_CLASS() if context is None else context

        # Store options in dict
        self.options = {} if options is None else options

        self.headers = HeaderDict()

        # Last response code
        self.code = 0
        self.flags = 0
        self.__abort = False
        self.init_context()

        # TODO: content encoding? Could be handled globally

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _get_logger(self, value):
        if value is False:
            logger = lambda *args, **kwgs: None
        else:
            logger = logging.getLogger(value)
        return logger

    def init_context(self):
        """
        Should be used to initialize everything from given context and options.
        """
        pass

    def get_context(self):
        """
        Retrieves complete state that is needed to copy the request context.
        """
        return self.config, self.context, self.options

    def set_context(self, *args):
        """
        Sets request context.
        """
        self.config, self.context, self.options = args

    def set_option(self, name, value):
        """
        Sets an option.
        """
        self.options[name] = value

    def unset_option(self, name):
        """
        Removes a specific option or reset everything on empty string.
        """
        if name == "":
            self.options.clear()
        else:
            if name in self.options:
                del self.options[name]

    def add_auth(self, user, pwd):
        """
        Adds authentication information to the request.
        """
        self.options['auth'] = "{0}:{1}".format(user, pwd)

    def remove_auth(self):
        """
        Removes authentication from the request.
        """
        self.unset_option("auth")

    def load(self, uri, *args, **kwargs):
        """
        Loads given resource from given uri. Args and kwargs depends on implementation.
        """
        raise NotImplementedError

    def abort(self):
        self.__abort = True

    def reset(self):
        """
        Resets the context to initial state.
        """
        self.unset_option("")

    def close(self):
        """
        Close and clean everything.
        """
        raise NotImplementedError
