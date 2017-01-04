# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import object
from threading import  RLock
from time import time

from pyload.datatype.check import OnlineCheck
from pyload.utils import lock, to_list
from pyload.thread.info import InfoThread


class ThreadManager(object):
    """manages all non download related threads and jobs """

    def __init__(self, core):
        """Constructor"""
        self.pyload = core

        self.thread = []  # thread list

        self.lock = RLock()

        # some operations require to fetch url info from hoster, so we caching them so it wont be done twice
        # contains a timestamp and will be purged after timeout
        self.info_cache = {}

        # pool of ids for online check
        self.result_ids = 0

        # saved online checks
        self.info_results = {}

        # timeout for cache purge
        self.timestamp = 0

    @lock
    def add_thread(self, thread):
        self.thread.append(thread)

    @lock
    def remove_thread(self, thread):
        """ Remove a thread from the local list """
        if thread in self.thread:
            self.thread.remove(thread)

    @lock
    def create_info_thread(self, data, pid):
        """ start a thread which fetches online status and other info's """
        self.timestamp = time() + 5 * 60
        if data:
            InfoThread(self, None, data, pid)

    @lock
    def create_result_thread(self, user, data):
        """ creates a thread to fetch online status, returns result id """
        self.timestamp = time() + 5 * 60

        rid = self.result_ids
        self.result_ids += 1

        oc = OnlineCheck(rid, user)
        self.info_results[rid] = oc

        InfoThread(self, user, data, oc=oc)

        return rid

    @lock
    def get_info_result(self, rid):
        return self.info_results.get(rid)

    def set_info_results(self, oc, result):
        self.pyload.evm.dispatch_event("linkcheck:updated", oc.rid, result, owner=oc.owner)
        oc.update(result)

    def get_progress_list(self, user=None):
        info = []

        for thread in self.thread:
            # skip if not belong to current user
            if user is not None and thread.owner != user:
                continue

            progress = thread.get_progress()
            if progress:
                info.extend(to_list(progress))

        return info

    def work(self):
        """run all task which have to be done (this is for repetitive call by core)"""

        if self.info_cache and self.timestamp < time():
            self.info_cache.clear()
            self.pyload.log.debug("Cleared Result cache")

        for rid in self.info_results.keys():
            if self.info_results[rid].is_stale():
                del self.info_results[rid]
