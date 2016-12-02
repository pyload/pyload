#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time

from pyload.Api import OnlineCheck as OC


class OnlineCheck:
    """  Helper class that holds result of an initiated online check """

    def __init__(self, rid, owner):
        self.rid = rid
        self.owner = owner
        self.result = {}
        self.done = False

        self.timestamp = time()

    def isStale(self, timeout=5):
        """ checks if the data was updated or accessed recently """
        return self.timestamp + timeout * 60 < time()

    def update(self, result):
        self.timestamp = time()
        self.result.update(result)

    def toApiData(self):
        self.timestamp = time()
        oc = OC(self.rid, self.result)
        # getting the results clears the older ones
        self.result = {}
        # indication for no more data
        if self.done:
            oc.rid = -1

        return oc
