# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import object
from logging import getLogger

from pyload.network.HeaderDict import HeaderDict


class ResponseException(Exception):
    def __init__(self, code, content=""):
        Exception.__init__(self, "Server response error: %s %s" % (code, content))
        self.code = code


class Request(object):
    """ Abstract class to support different types of request, most methods should be overwritten """

    __version__ = "0.1"

    #: Class that will be instantiated and associated with the request, and if needed copied and reused
    CONTEXT_CLASS = None

    def __init__(self, config, context=None, options=None):
        self.log = getLogger("log")

        # Global config, holds some configurable parameter
        self.config = config

        # Create a new context if not given
        if context is None and self.CONTEXT_CLASS is not None:
            self.context = self.CONTEXT_CLASS()
        else:
            self.context = context

        # Store options in dict
        self.options = {} if options is None else options

        self.headers = HeaderDict()

        # Last response code
        self.code = 0
        self.flags = 0
        self.doAbort = False
        self.initContext()

        # TODO: content encoding? Could be handled globally

    def initContext(self):
        """ Should be used to initialize everything from given context and options """
        pass

    def getContext(self):
        """ Retrieves complete state that is needed to copy the request context """
        return self.config, self.context, self.options

    def setContext(self, *args):
        """  Sets request context """
        self.config, self.context, self.options = args

    def setOption(self, name, value):
        """ Sets an option """
        self.options[name] = value

    def unsetOption(self, name):
        """ Removes a specific option or reset everything on empty string  """
        if name == "":
            self.options.clear()
        else:
            if name in self.options:
                del self.options[name]

    def addAuth(self, user, pwd):
        """  Adds authentication information to the request """
        self.options["auth"] = user + ":" + pwd

    def removeAuth(self):
        """ Removes authentication from the request """
        self.unsetOption("auth")

    def load(self, uri, *args, **kwargs):
        """  Loads given resource from given uri. Args and kwargs depends on implementation"""
        raise NotImplementedError

    def abort(self):
        self.doAbort = True

    def reset(self):
        """  Resets the context to initial state """
        self.unsetOption("")

    def close(self):
        """ Close and clean everything """
        pass
