# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
from builtins import COREDIR, object
from collections import defaultdict
from random import sample
from time import sleep

from future import standard_library

from pyload.api import DownloadStatus as DS
from pyload.network import get_ip
from pyload.thread import DecrypterThread, DownloadThread
from pyload.utils.decorator import lock, readlock
from pyload.utils.lib.rwlock import ReadWriteLock
from pyload.utils.lib.subprocess import call
from pyload.utils.lib.threading import Event
from pyload.utils.path import availspace

standard_library.install_aliases()


class DownloadManager(object):
    """
    Schedules and manages download and decrypter jobs.
    """

    def __init__(self, core):
        self.pyload = core

        #: won't start download when true
        self.paused = True

        #: each thread is in exactly one category
        self.free = []
        #: a thread that in working must have a pyfile as active attribute
        self.working = []
        #: holds the decrypter threads
        self.decrypter = []

        #: indicates when reconnect has occurred
        self.reconnecting = Event()
        self.reconnecting.clear()

        self.lock = ReadWriteLock()

    @lock
    def done(self, thread):
        """
        Switch thread from working to free state.
        """

        # only download threads will be re-used
        if isinstance(thread, DownloadThread):
            # clean local var
            thread.active = None
            self.working.remove(thread)
            self.free.append(thread)
            thread.is_working.clear()
        elif isinstance(thread, DecrypterThread):
            self.decrypter.remove(thread)

    @lock
    def stop(self, thread):
        """
        Removes a thread from all lists.
        """
        if thread in self.free:
            self.free.remove(thread)
        elif thread in self.working:
            self.working.remove(thread)

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

        thread.put(self.pyload.files.get_file(info.fid))

        # wait until it picked up the task
        thread.is_working.wait()
        self.working.append(thread)

    @lock
    def start_decrypter_thread(self, info):
        """
        Start decrypting of entered data, all links in one package are accumulated to one thread.
        """
        self.pyload.files.set_download_status(info.fid, DS.Decrypting)
        self.decrypter.append(DecrypterThread(self, [(info.download.url, info.download.plugin)],
                                              info.fid, info.package, info.owner))

    @readlock
    def active_downloads(self, uid=None):
        """
        Retrieve pyfiles of running downloads.
        """
        return [x.active for x in self.working if uid is None or x.active.owner == uid]

    @readlock
    def waiting_downloads(self):
        """
        All waiting downloads.
        """
        return [
            x.active for x in self.working if x.active.has_status("waiting")]

    @readlock
    def get_progress_list(self, uid):
        """
        Progress of all running downloads.
        """

        # decrypter progress could be none
        return [x for x in [p.get_progress() for p in self.working + self.decrypter
                            if uid is None or p.owner == uid] if x is not None]

    def processing_ids(self):
        """
        Get a id list of all pyfiles processed.
        """
        return [x.fid for x in self.active_downloads(None)]

    @readlock
    def shutdown(self):
        """
        End all threads.
        """
        self.paused = True
        for thread in self.working + self.free:
            thread.put("quit")

    def work(self):
        """
        Main routine that does the periodical work.
        """
        self.try_reconnect()

        if (availspace(self.pyload.config.get('general', 'storage_folder')) / 1024 / 1024 <
                self.pyload.config.get('general', 'min_storage_size')):
            self.pyload.log.warning(_("Not enough space left on device"))
            self.paused = True

        # if self.paused or not self.pyload.api.is_time_download():
            # return False
        if self.paused:
            return False

        # at least one thread want reconnect and we are supposed to wait
        if self.pyload.config.get(
                'reconnect', 'wait') and self.want_reconnect() > 1:
            return False

        self.assign_jobs()

        # TODO: clean free threads

    def assign_jobs(self):
        """
        Load jobs from db and try to assign them.
        """
        limit = self.pyload.config.get(
            'connection', 'max_transfers') - len(self.active_downloads())

        # check for waiting dl rule
        if limit <= 0:
            # increase limit if there are waiting downloads
            limit += min(len(self.waiting_downloads()), self.pyload.config.get('connection', 'wait') +
                         self.pyload.config.get('connection', 'max_transfers') - len(
                self.active_downloads()))

        slots = self.get_remaining_plugin_slots()
        occ = tuple(plugin for plugin, v in slots.items() if v == 0)
        jobs = self.pyload.files.get_jobs(occ)

        # map plugin to list of jobs
        plugins = defaultdict(list)

        for uid, info in jobs.items():
            # check the quota of each user and filter
            quota = self.pyload.api.calc_quota(uid)
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

        return sample(jobs, k)

    def start_job(self, info, limit):
        """
        Start a download or decrypter thread with given file info.
        """
        plugin = self.pyload.pgm.find_type(info.download.plugin)
        # this plugin does not exits
        if plugin is None:
            self.pyload.log.error(
                _("Plugin '{}' does not exists").format(info.download.plugin))
            self.pyload.files.set_download_status(info.fid, DS.Failed)
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
            self.pyload.log.error(
                _("Plugin type '{}' can't be used for downloading").format(plugin))

        return False

    @readlock
    def try_reconnect(self):
        """
        Checks if reconnect needed.
        """
        # if not self.pyload.config.get('reconnect', 'activated') or not self.pyload.api.is_time_reconnect():
        # return False
        if not self.pyload.config.get('reconnect', 'activated'):
            return False

        # only reconnect when all threads are ready
        if not (0 < self.want_reconnect() == len(self.working)):
            return False

        if not os.path.exists(self.pyload.config.get('reconnect', 'script')):
            if os.path.exists(
                    os.path.join(COREDIR, self.pyload.config.get('reconnect', 'script'))):
                self.pyload.config.set('reconnect', 'script', os.path.join(
                    COREDIR, self.pyload.config.get('reconnect', 'script')))
            else:
                self.pyload.config.set('reconnect', 'activated', False)
                self.pyload.log.warning(_("Reconnect script not found!"))
                return

        self.reconnecting.set()

        self.pyload.log.info(_("Starting reconnect"))

        # wait until all thread got the event
        while [x.active.plugin.waiting for x in self.working].count(True) != 0:
            sleep(0.25)

        old_ip = get_ip()

        self.pyload.evm.fire("reconnect:before", old_ip)
        self.pyload.log.debug("Old IP: {}".format(old_ip))

        try:
            call(self.pyload.config.get('reconnect', 'script'), shell=True)
        except Exception:
            self.pyload.log.warning(_("Failed executing reconnect script!"))
            self.pyload.config.set('reconnect', 'activated', False)
            self.reconnecting.clear()
            # self.pyload.print_exc()
            return

        sleep(1)
        ip = get_ip()
        self.pyload.evm.fire("reconnect:after", ip)

        if not old_ip or old_ip == ip:
            self.pyload.log.warning(_("Reconnect not successful"))
        else:
            self.pyload.log.info(_("Reconnected, new IP: {}").format(ip))

        self.reconnecting.clear()

    @readlock
    def want_reconnect(self):
        """
        Number of downloads that are waiting for reconnect.
        """
        active = [x.active.has_plugin(
        ) and x.active.plugin.want_reconnect and x.active.plugin.waiting for x in self.working]
        return active.count(True)

    @readlock
    def get_remaining_plugin_slots(self):
        """
        Dict of plugin names mapped to remaining dls.
        """
        occ = {}
        # decrypter are treated as occupied
        for p in self.decrypter:
            progress = p.get_progress()
            if progress:
                occ[progress.plugin] = 0

        # get all default dl limits
        for t in self.working:
            if not t.active.has_plugin():
                continue
            limit = t.active.plugin.get_download_limit()
            # limit <= 0 means no limit
            occ[t.active.pluginname] = limit if limit > 0 else float('inf')

        # subtract with running downloads
        for t in self.working:
            if not t.active.has_plugin():
                continue
            plugin = t.active.pluginname
            if plugin in occ:
                occ[plugin] -= 1

        return occ
