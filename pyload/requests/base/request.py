# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging
from abc import ABCMeta, abstractmethod
from http.client import responses

from future import standard_library
from future.builtins import object
from future.utils import with_metaclass

from pyload.utils.struct import HeaderDict

standard_library.install_aliases()


BAD_HTTP_RESPONSES = list(range(400, 418)) + list(range(500, 506))

# Mapping status codes to official W3C names (and some unofficial ones)
http_responses = {
    440: "Login Timeout - The client's session has expired and must log in again.",
    449: 'Retry With - The server cannot honour the request because the user has not provided the required information',
    451: 'Redirect - Unsupported Redirect Header',
    509: 'Bandwidth Limit Exceeded',
    520: 'Unknown Error',
    521: 'Web Server Is Down - The origin server has refused the connection from CloudFlare',
    522: 'Connection Timed Out - CloudFlare could not negotiate a TCP handshake with the origin server',
    523: 'Origin Is Unreachable - CloudFlare could not reach the origin server',
    524: 'A Timeout Occurred - CloudFlare did not receive a timely HTTP response',
    525: 'SSL Handshake Failed - CloudFlare could not negotiate a SSL/TLS handshake with the origin server',
    526: 'Invalid SSL Certificate - CloudFlare could not validate the SSL/TLS certificate that the origin server presented',
    527: 'Railgun Error - CloudFlare requests timeout or failed after the WAN connection has been established',
    530: 'Site Is Frozen - Used by the Pantheon web platform to indicate a site that has been frozen due to inactivity'}
http_responses.update(responses)


class Abort(Exception):
    """Raised when aborted."""
    __slots__ = []


class ResponseException(Exception):

    __slots__ = ['code', 'content', 'header']

    def __init__(self, code, content='', header=''):
        super(
            ResponseException,
            self).__init__(
            'Server response error: {0} {1}'.format(
                code,
                http_responses.get(int(code), 'Unknown status code')))
        self.code = code
        self.content = content
        self.header = header


class Request(with_metaclass(ABCMeta, object)):
    """Abstract class to support different types of request, most methods
    should be overwritten."""

    # Class that will be instantiated and associated with the request,
    # and if needed copied and reused
    CONTEXT_CLASS = None

    def __init__(self, config, context=None, options=None, logger=None):
        if logger is None:
            self.log = logging.getLogger('null')
            self.log.addHandler(logging.NullHandler())
        else:
            self.log = logger

        # Global config, holds some configurable parameter
        self.config = config

        # Create a new context if not given
        self.context = self.CONTEXT_CLASS() if context is None else context  #instantiate CONTEXT_CLASS

        # Store options in dict
        self.options = {} if options is None else options

        self.headers = HeaderDict()

        # Last response code
        self.code = 0
        self.flags = 0
        self._abort = False
        self.init_context()

        # TODO: content encoding? Could be handled globally

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractmethod
    def init_context(self):
        """Should be used to initialize everything from given context and
        options."""

    def get_context(self):
        """Retrieves complete state that is needed to copy the request
        context."""
        return self.config, self.context, self.options

    def set_context(self, *args):
        """Sets request context."""
        self.config, self.context, self.options = args

    def set_option(self, name, value):
        """Sets an option."""
        self.options[name] = value

    def unset_option(self, name):
        """Removes a specific option or reset everything on empty string."""
        if name == '':
            self.options.clear()
        else:
            if name in self.options:
                del self.options[name]

    def add_auth(self, user, pwd):
        """Adds authentication information to the request."""
        self.options['auth'] = '{0}:{1}'.format(user, pwd)

    def remove_auth(self):
        """Removes authentication from the request."""
        self.unset_option('auth')

    def abort(self):
        self._abort = True

    def reset(self):
        """Resets the context to initial state."""
        self.unset_option('')

    @abstractmethod
    def close(self):
        """Close and clean everything."""
