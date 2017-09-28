# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time

from future import standard_library

from .init import BaseObject

standard_library.install_aliases()


class OnlineCheck(BaseObject):
    """
    Helper class that holds result of an initiated online check.
    """
    __slots__ = ['done', 'owner', 'result', 'rid', 'timestamp']

    def __init__(self, rid=None, owner=None):
        self.rid = rid
        self.owner = owner
        self.result = {}
        self.done = False
        self.timestamp = time.time()

    def is_stale(self, timeout=5):
        """
        Checks if the data was updated or accessed recently.
        """
        return self.timestamp + timeout * 60 < time.time()

    def update(self, result):
        self.timestamp = time.time()
        self.result.update(result)

    def to_api_data(self):
        self.timestamp = time.time()
        oc = OnlineCheck(self.rid, self.result)
        # getting the results clears the older ones
        self.result = {}
        # indication for no more data
        if self.done:
            oc.rid = -1
        return oc
