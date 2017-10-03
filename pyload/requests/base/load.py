# -*- coding: utf-8 -*-

from __future__ import absolute_import

from abc import ABCMeta, abstractmethod

from future.utils import with_metaclass

from pyload.requests.base.request import Request


class LoadRequest(with_metaclass(ABCMeta, Request)):
    """Abstract class for load request."""

    @abstractmethod
    def load(self, uri, *args, **kwargs):
        """Loads given resource from given uri.

        Args and kwargs depends on implementation.

        """
