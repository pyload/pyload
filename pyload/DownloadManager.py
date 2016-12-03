#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2009-2017 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

from __future__ import absolute_import
from __future__ import unicode_literals
from collections import defaultdict
from threading import Event
from time import sleep
from random import sample
from subprocess import call

from ReadWriteLock import ReadWriteLock

from .Api import DownloadStatus as DS

from .utils import lock, read_lock
from .utils.fs import exists, join, free_space

from .network import get_ip

from .threads.DownloadThread import DownloadThread
from .threads.DecrypterThread import DecrypterThread


class DownloadManager:
    """ Schedules and manages download and decrypter jobs. """

    def __init__(self, core):
        self.core = core
        self.log = core.log

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
        """ Switch thread from working to free state """
        # only download threads will be re-used
        if isinstance(thread, DownloadThread):
            # clean local var
            thread.active = None
            self.working.remove(thread)
            self.free.append(thread)
            thread.isWorking.clear()
        elif isinstance(thread, DecrypterThread):
            self.decrypter.remove(thread)

    @lock
    def stop(self, thread):
        """  Removes a thread from all lists  """
        if thread in self.free:
            self.free.remove(thread)
        elif thread in self.working:
            self.working.remove(thread)

    @lock
    def startDownloadThread(self, info):
        """ Use a free dl thread or create a new one """
        if self.free:
            thread = self.free[0]
            del self.free[0]
        else:
            thread = DownloadThread(self)

        thread.put(self.core.files.getFile(info.fid))

        # wait until it picked up the task
        thread.isWorking.wait()
        self.working.append(thread)

    @lock
    def startDecrypterThread(self, info):
        """ Start decrypting of entered data, all links in one package are accumulated to one thread."""
        self.core.files.setDownloadStatus(info.fid, DS.Decrypting)
        self.decrypter.append(DecrypterThread(self, [(info.download.url, info.download.plugin)],
                                              info.fid, info.package, info.owner))

    @read_lock
    def activeDownloads(self, uid=None):
        """ retrieve pyfiles of running downloads  """
        return [x.active for x in self.working
                if uid is None or x.active.owner == uid]

    @read_lock
    def waitingDownloads(self):
        """ all waiting downloads """
        return [x.active for x in self.working if x.active.hasStatus("waiting")]

    @read_lock
    def getProgressList(self, uid):
        """ Progress of all running downloads """
        # decrypter progress could be none
        return filter(lambda x: x is not None,
                      [p.getProgress() for p in self.working + self.decrypter
                       if uid is None or p.owner == uid])

    def processingIds(self):
        """get a id list of all pyfiles processed"""
        return [x.fid for x in self.activeDownloads(None)]


    @read_lock
    def shutdown(self):
        """  End all threads """
        self.paused = True
        for thread in self.working + self.free:
            thread.put("quit")

    def work(self):
        """ main routine that does the periodical work """

        self.tryReconnect()

        if free_space(self.core.config["general"]["download_folder"]) / 1024 / 1024 < \
                self.core.config["general"]["min_free_space"]:
            self.log.warning(_("Not enough space left on device"))
            self.paused = True

        if self.paused or not self.core.api.isTimeDownload():
            return False

        # at least one thread want reconnect and we are supposed to wait
        if self.core.config['reconnect']['wait'] and self.wantReconnect() > 1:
            return False

        self.assignJobs()

        # TODO: clean free threads

    def assignJobs(self):
        """ Load jobs from db and try to assign them """

        limit = self.core.config['download']['max_downloads'] - len(self.activeDownloads())

        # check for waiting dl rule
        if limit <= 0:
            # increase limit if there are waiting downloads
            limit += min(len(self.waitingDownloads()), self.core.config['download']['wait_downloads'] +
                                                  self.core.config['download']['max_downloads'] - len(
                self.activeDownloads()))

        slots = self.getRemainingPluginSlots()
        occ = tuple([plugin for plugin, v in slots.items() if v == 0])
        jobs = self.core.files.getJobs(occ)

        # map plugin to list of jobs
        plugins = defaultdict(list)

        for uid, info in jobs.items():
            # check the quota of each user and filter
            quota = self.core.api.calcQuota(uid)
            if -1 < quota < info.size:
                del jobs[uid]

            plugins[info.download.plugin].append(info)

        for plugin, jobs in plugins.items():
            # we know exactly the number of remaining jobs
            # or only can start one job if limit is not known
            to_schedule = slots[plugin] if plugin in slots else 1
            # start all chosen jobs
            for job in self.chooseJobs(jobs, to_schedule):
                # if the job was started the limit will be reduced
                if self.startJob(job, limit):
                    limit -= 1

    def chooseJobs(self, jobs, k):
        """ make a fair choice of which k jobs to start """
        # TODO: prefer admins, make a fairer choice?
        if k <= 0: return []
        if k >= len(jobs): return jobs

        return sample(jobs, k)

    def startJob(self, info, limit):
        """ start a download or decrypter thread with given file info """

        plugin = self.core.pluginManager.findPlugin(info.download.plugin)
        # this plugin does not exits
        if plugin is None:
            self.log.error(_("Plugin '%s' does not exists") % info.download.plugin)
            self.core.files.setDownloadStatus(info.fid, DS.Failed)
            return False

        if plugin == "hoster":
            # this job can't be started
            if limit <= 0:
                return False

            self.startDownloadThread(info)
            return True

        elif plugin == "crypter":
            self.startDecrypterThread(info)
        else:
            self.log.error(_("Plugin type '%s' can't be used for downloading") % plugin)

        return False

    @read_lock
    def tryReconnect(self):
        """checks if reconnect needed"""

        if not self.core.config["reconnect"]["activated"] or not self.core.api.isTimeReconnect():
            return False

        # only reconnect when all threads are ready
        if not (0 < self.wantReconnect() == len(self.working)):
            return False

        if not exists(self.core.config['reconnect']['method']):
            if exists(join(pypath, self.core.config['reconnect']['method'])):
                self.core.config['reconnect']['method'] = join(pypath, self.core.config['reconnect']['method'])
            else:
                self.core.config["reconnect"]["activated"] = False
                self.log.warning(_("Reconnect script not found!"))
                return

        self.reconnecting.set()

        self.log.info(_("Starting reconnect"))

        # wait until all thread got the event
        while [x.active.plugin.waiting for x in self.working].count(True) != 0:
            sleep(0.25)

        old_ip = get_ip()

        self.core.evm.dispatchEvent("reconnect:before", old_ip)
        self.log.debug("Old IP: %s" % old_ip)

        try:
            call(self.core.config['reconnect']['method'], shell=True)
        except:
            self.log.warning(_("Failed executing reconnect script!"))
            self.core.config["reconnect"]["activated"] = False
            self.reconnecting.clear()
            self.core.print_exc()
            return

        sleep(1)
        ip = get_ip()
        self.core.evm.dispatchEvent("reconnect:after", ip)

        if not old_ip or old_ip == ip:
            self.log.warning(_("Reconnect not successful"))
        else:
            self.log.info(_("Reconnected, new IP: %s") % ip)

        self.reconnecting.clear()

    @read_lock
    def wantReconnect(self):
        """ number of downloads that are waiting for reconnect """
        active = [x.active.hasPlugin() and x.active.plugin.wantReconnect and x.active.plugin.waiting for x in self.working]
        return active.count(True)

    @read_lock
    def getRemainingPluginSlots(self):
        """  dict of plugin names mapped to remaining dls  """
        occ = {}
        # decrypter are treated as occupied
        for p in self.decrypter:
            progress = p.getProgress()
            if progress:
                occ[progress.plugin] = 0

        # get all default dl limits
        for t in self.working:
            if not t.active.hasPlugin(): continue
            limit = t.active.plugin.getDownloadLimit()
            # limit <= 0 means no limit
            occ[t.active.pluginname] = limit if limit > 0 else float('inf')

        # subtract with running downloads
        for t in self.working:
            if not t.active.hasPlugin(): continue
            plugin = t.active.pluginname
            if plugin in occ:
                occ[plugin] -= 1

        return occ
