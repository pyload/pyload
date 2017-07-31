# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import os
import random
import time
from collections import defaultdict

from future import standard_library

from pyload.utils.fs import availspace
from pyload.utils.layer.legacy import subprocess_ as subprocess
from pyload.utils.layer.safethreading import Event
from pyload.utils.struct.lock import RWLock, lock
from pyload.utils.web.misc import get_ip

from pyload.core.datatype.init import DownloadStatus
from pyload.core.manager.base import BaseManager
from pyload.core.thread import DecrypterThread, DownloadThread

standard_library.install_aliases()


class TransferManager(BaseManager):
    """
    Schedules and manages download and decrypter jobs.
    """
    def __init__(self, core):
        BaseManager.__init__(self, core)

        # won't start download when true
        self.pause = True

        # each thread is in exactly one category
        self.free = []
        # a thread that in working must have a file as active attribute
        self.downloading = []
        # holds the decrypter threads
        self.decrypting = []

        # indicates when reconnect has occurred
        self.reconnecting = Event()

        self.lock = RWLock()

    @lock
    def done(self, thread):
        """
        Switch thread from working to free state.
        """
        # only download threads will be re-used
        if isinstance(thread, DownloadThread):
            # clean local var
            thread.active = None
            self.downloading.remove(thread)
            self.free.append(thread)
            thread.running.clear()
        elif isinstance(thread, DecrypterThread):
            self.decrypting.remove(thread)

    @lock
    def discard(self, thread):
        """
        Removes a thread from all lists.
        """
        if thread in self.free:
            self.free.remove(thread)
        elif thread in self.downloading:
            self.downloading.remove(thread)

    @lock
    def start_download_thread(self, info):
        """
        Use a free dl thread or create a new one.
        """
        if self.free:
            thread = self.free[0]
            del self.free[0]
        else:
            thread = DownloadThread(self)

        thread.put(self.pyload_core.files.get_file(info.fid))
        thread.start()
        # wait until it picked up the task
        thread.running.wait()
        self.downloading.append(thread)
        return thread

    @lock
    def start_decrypter_thread(self, info):
        """
        Start decrypting of entered data,
        all links in one package are accumulated to one thread.
        """
        self.pyload_core.files.set_download_status(
            info.fid, DownloadStatus.Decrypting)
        thread = DecrypterThread(
            self,
            [(info.download.url, info.download.plugin)],
            info.fid, info.package, info.owner
        )
        thread.start()
        self.decrypting.append(thread)
        return thread

    @lock(shared=True)
    def active_downloads(self, uid=None):
        """
        Retrieve pyfiles of running downloads.
        """
        return [x.active for x in self.downloading
                if uid is None or x.active.owner == uid]

    @lock(shared=True)
    def waiting_downloads(self):
        """
        All waiting downloads.
        """
        return [x.active for x in self.downloading
                if x.active.has_status("waiting")]

    @lock(shared=True)
    def get_progress_list(self, uid):
        """
        Progress of all running downloads.
        """
        # decrypter progress could be none
        return [
            x for x in [
                thd.progress for thd in self.downloading + self.decrypting
                if uid is None or thd.owner == uid]
            if x is not None]

    def processing_ids(self):
        """
        Get a id list of all pyfiles processed.
        """
        return [x.fid for x in self.active_downloads(None)]

    @lock(shared=True)
    def shutdown(self):
        """
        End all threads.
        """
        self.pause = True
        for thread in self.downloading + self.free:
            thread.put("quit")

    def work(self):
        """
        Main routine that does the periodical work.
        """
        self.try_reconnect()

        if (availspace(self.pyload_core.config.get('general', 'storage_folder')) <
                self.pyload_core.config.get('general', 'min_storage_size') << 20):
            self.pyload_core.log.warning(
                self._("Not enough space left on device"))
            self.pause = True

        # if self.pause or not self.pyload_core.api.is_time_download():
            # return False
        if self.pause:
            return False

        # at least one thread want reconnect and we are supposed to wait
        if self.pyload_core.config.get(
                'reconnect', 'wait') and self.want_reconnect() > 1:
            return False

        self.assign_jobs()

        # TODO: clean free threads

    def assign_jobs(self):
        """
        Load jobs from db and try to assign them.
        """
        limit = self.pyload_core.config.get(
            'connection', 'max_transfers') - len(self.active_downloads())

        # check for waiting dl rule
        if limit <= 0:
            # increase limit if there are waiting downloads
            limit += min(
                len(self.waiting_downloads()),
                self.pyload_core.config.get('connection', 'wait') +
                self.pyload_core.config.get('connection', 'max_transfers') -
                len(self.active_downloads()))

        slots = self.get_remaining_plugin_slots()
        occ = tuple(plugin for plugin, v in slots.items() if v == 0)
        jobs = self.pyload_core.files.get_jobs(occ)

        # map plugin to list of jobs
        plugins = defaultdict(list)

        for uid, info in jobs.items():
            # check the quota of each user and filter
            quota = self.pyload_core.api.calc_quota(uid)
            if -1 < quota < info.size:
                del jobs[uid]

            plugins[info.download.plugin].append(info)

        for plugin, jobs in plugins.items():
            # we know exactly the number of remaining jobs
            # or only can start one job if limit is not known
            to_schedule = slots[plugin] if plugin in slots else 1
            # start all chosen jobs
            for job in self.choose_jobs(jobs, to_schedule):
                # if the job was started the limit will be reduced
                if self.start_job(job, limit):
                    limit -= 1

    def choose_jobs(self, jobs, k):
        """
        Make a fair choice of which k jobs to start.
        """
        # TODO: prefer admins, make a fairer choice?
        if k <= 0:
            return []
        if k >= len(jobs):
            return jobs

        return random.sample(jobs, k)

    def start_job(self, info, limit):
        """
        Start a download or decrypter thread with given file info.
        """
        plugin = self.pyload_core.pgm.find_type(info.download.plugin)
        # this plugin does not exits
        if plugin is None:
            self.pyload_core.log.error(
                self._("Plugin '{0}' does not exists").format(
                    info.download.plugin))
            self.pyload_core.files.set_download_status(
                info.fid, DownloadStatus.Failed)
            return False

        if plugin == "hoster":
            # this job can't be started
            if limit <= 0:
                return False

            self.start_download_thread(info)
            return True

        elif plugin == "crypter":
            self.start_decrypter_thread(info)
        else:
            self.pyload_core.log.error(
                self._("Plugin type '{0}' "
                       "can't be used for downloading").format(plugin))

        return False

    @lock(shared=True)
    def try_reconnect(self):
        """
        Checks if reconnect needed.
        """
        if not self.pyload_core.config.get('reconnect', 'activated'):
            return False

        # only reconnect when all threads are ready
        if not (0 < self.want_reconnect() == len(self.downloading)):
            return False

        script = self.pyload_core.config.get('reconnect', 'script')
        if not os.path.isfile(script):
            self.pyload_core.config.set('reconnect', 'activated', False)
            self.pyload_core.log.warning(self._("Reconnect script not found!"))
            return None

        self.reconnecting.set()

        self.pyload_core.log.info(self._("Starting reconnect"))

        # wait until all thread got the event
        while [x.active.plugin.waiting
               for x in self.downloading].count(True):
            time.sleep(0.25)

        old_ip = get_ip()

        self.pyload_core.evm.fire("reconnect:before", old_ip)
        self.pyload_core.log.debug("Old IP: {0}".format(old_ip))

        try:
            subprocess.call(
                self.pyload_core.config.get(
                    'reconnect',
                    'script'),
                shell=True)
        except Exception:
            self.pyload_core.log.warning(
                self._("Failed executing reconnect script!"))
            self.pyload_core.config.set('reconnect', 'activated', False)
            self.reconnecting.clear()
            # self.pyload_core.print_exc()
            return None

        time.sleep(1)
        ip = get_ip()
        self.pyload_core.evm.fire("reconnect:after", ip)

        if not old_ip or old_ip == ip:
            self.pyload_core.log.warning(self._("Reconnect not successful"))
        else:
            self.pyload_core.log.info(
                self._("Reconnected, new IP: {0}").format(ip))

        self.reconnecting.clear()

    @lock(shared=True)
    def want_reconnect(self):
        """
        Number of downloads that are waiting for reconnect.
        """
        active = [
            x.active.has_plugin() and
            x.active.plugin.want_reconnect and x.active.plugin.waiting
            for x in self.downloading]
        return active.count(True)

    @lock(shared=True)
    def get_remaining_plugin_slots(self):
        """
        Dict of plugin names mapped to remaining dls.
        """
        occ = {}
        # decrypter are treated as occupied
        for thd in self.decrypting:
            if not thd.progress:
                continue
            occ[thd.progress.plugin] = 0

        # get all default dl limits
        for thd in self.downloading:
            if not thd.active.has_plugin():
                continue
            limit = thd.active.plugin.get_download_limit()
            # limit <= 0 means no limit
            occ[thd.active.pluginname] = limit if limit > 0 else float('inf')

        # subtract with running downloads
        for thd in self.downloading:
            if not thd.active.has_plugin():
                continue
            plugin = thd.active.pluginname
            if plugin in occ:
                occ[plugin] -= 1

        return occ
