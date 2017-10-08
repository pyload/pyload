# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging
from abc import ABCMeta, abstractmethod

from future import standard_library
from future.utils import with_metaclass

from pyload.requests.base.request import Request
from pyload.utils.layer.safethreading import Event

standard_library.install_aliases()


class DownloadRequest(with_metaclass(ABCMeta, Request)):
    """Abstract class for download request."""

    def __init__(self, bucket, request=None, logger=None):
        if logger is None:
            self.log = logging.getLogger('null')
            self.log.addHandler(logging.NullHandler())
        else:
            self.log = logger

        # Copies the context
        context = request.get_context() if request else [{}]
        super(DownloadRequest, self).__init__(*context)

        self.__running = Event()
        self._name = None
        self._size = 0

        # bucket used for rate limiting
        self.bucket = bucket

    @abstractmethod
    def download(self, uri, filename, *args, **kwargs):
        """Downloads the resource with additional options depending on
        implementation."""

    @property
    def running(self):
        return self.__running.is_set()

    @property
    def size(self):
        """Size in bytes."""
        return self._size

    @property
    def name(self):
        """Name of the resource if known."""
        return self._name

    @property
    def speed(self):
        """Download rate in bytes per second."""
        return 0

    @property
    def arrived(self):
        """Number of bytes already loaded."""
        return 0
