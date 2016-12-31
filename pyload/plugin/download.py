# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.plugin.request import Request


class Download(Request):
    """ Abstract class for download request """

    __version__ = "0.1"

    def __init__(self, bucket, request=None):
        # Copies the context
        context = request.get_context() if request else [{}]
        Request.__init__(self, *context)

        self._running = False
        self._name = None
        self._size = 0

        #: bucket used for rate limiting
        self.bucket = bucket

    def download(self, uri, path, *args, **kwargs):
        """ Downloads the resource with additional options depending on implementation """
        raise NotImplementedError

    @property
    def running(self):
        return self._running

    @property
    def size(self):
        """ Size in bytes """
        return self._size

    @property
    def name(self):
        """  Name of the resource if known """
        return self._name

    @property
    def speed(self):
        """ Download rate in bytes per second """
        return 0

    @property
    def arrived(self):
        """ Number of bytes already loaded """
        return 0
