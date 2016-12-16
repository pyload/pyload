# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import object
from threading import  RLock
from time import time

from pyload.datatypes.onlinecheck import OnlineCheck
from pyload.utils import lock, to_list
from .infothread import InfoThread


class ThreadManager(object):
    """manages all non download related threads and jobs """

    def __init__(self, core):
        """Constructor"""
        self.pyload = core
        self.log = core.log

        self.threads = []  # thread list

        self.lock = RLock()

        # some operations require to fetch url info from hoster, so we caching them so it wont be done twice
        # contains a timestamp and will be purged after timeout
        self.infoCache = {}

        # pool of ids for online check
        self.resultIDs = 0

        # saved online checks
        self.infoResults = {}

        # timeout for cache purge
        self.timestamp = 0

    @lock
    def add_thread(self, thread):
        self.threads.append(thread)

    @lock
    def remove_thread(self, thread):
        """ Remove a thread from the local list """
        if thread in self.threads:
            self.threads.remove(thread)

    @lock
    def create_info_thread(self, data, pid):
        """ start a thread which fetches online status and other info's """
        self.timestamp = time() + 5 * 60
        if data: InfoThread(self, None, data, pid)

    @lock
    def create_result_thread(self, user, data):
        """ creates a thread to fetch online status, returns result id """
        self.timestamp = time() + 5 * 60

        rid = self.resultIDs
        self.resultIDs += 1

        oc = OnlineCheck(rid, user)
        self.infoResults[rid] = oc

        InfoThread(self, user, data, oc=oc)

        return rid

    @lock
    def get_info_result(self, rid):
        return self.infoResults.get(rid)

    def set_info_results(self, oc, result):
        self.pyload.evm.dispatch_event("linkcheck:updated", oc.rid, result, owner=oc.owner)
        oc.update(result)

    def get_progress_list(self, user=None):
        info = []

        for thread in self.threads:
            # skip if not belong to current user
            if user is not None and thread.owner != user: continue

            progress = thread.getProgress()
            if progress: info.extend(to_list(progress))

        return info

    def work(self):
        """run all task which have to be done (this is for repetitive call by core)"""

        if self.infoCache and self.timestamp < time():
            self.infoCache.clear()
            self.log.debug("Cleared Result cache")

        for rid in self.infoResults.keys():
            if self.infoResults[rid].isStale():
                del self.infoResults[rid]
