# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import time

from future import standard_library

from pyload.utils.convert import to_list
from pyload.utils.layer.safethreading import RLock
from pyload.utils.struct.lock import lock

from pyload.core.datatype.check import OnlineCheck
from pyload.core.manager.base import BaseManager
from pyload.core.thread import InfoThread

standard_library.install_aliases()


class InfoManager(BaseManager):
    """
    Manages all non download related threads and jobs.
    """
    def __init__(self, core):
        """
        Constructor.
        """
        BaseManager.__init__(self, core)

        self.thread = []  # thread list

        self.lock = RLock()

        # some operations require to fetch url info from hoster,
        # so we caching them so it wont be done twice
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
        """
        Remove a thread from the local list.
        """
        if thread in self.thread:
            self.thread.remove(thread)

    @lock
    def create_info_thread(self, data, pid):
        """
        Start a thread which fetches online status and other info's.
        """
        self.timestamp = time.time() + 5 * 60
        thread = InfoThread(self, None, data, pid)
        thread.start()

    @lock
    def create_result_thread(self, user, data):
        """
        Creates a thread to fetch online status, returns result id.
        """
        self.timestamp = time.time() + 5 * 60

        rid = self.result_ids
        self.result_ids += 1

        oc = OnlineCheck(rid, user)
        self.info_results[rid] = oc

        thread = InfoThread(self, user, data, oc=oc)
        thread.start()

        return rid

    @lock
    def get_info_result(self, rid):
        return self.info_results.get(rid)

    def set_info_results(self, oc, result):
        self.pyload_core.evm.fire("linkcheck:updated", oc.rid,
                               result, owner=oc.owner)
        oc.update(result)

    def get_progress_list(self, user=None):
        info = []

        for thread in self.thread:
            # skip if not belong to current user
            if user is not None and thread.owner != user:
                continue
            if thread.progress:
                info.extend(to_list(thread.progress, []))

        return info

    def work(self):
        """
        Run all task which have to be done
        (this is for repetitive call by core).
        """
        if self.info_cache and self.timestamp < time.time():
            self.info_cache.clear()
            self.pyload_core.log.debug("Cleared Result cache")

        for rid in self.info_results:
            if self.info_results[rid].is_stale():
                del self.info_results[rid]
