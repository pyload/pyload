# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import object
from builtins import pypath
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

from .thread.downloadthread import DownloadThread
from .thread.decrypterthread import DecrypterThread


class DownloadManager(object):
    """ Schedules and manages download and decrypter jobs. """

    def __init__(self, core):
        self.pyload = core
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
    def start_download_thread(self, info):
        """ Use a free dl thread or create a new one """
        if self.free:
            thread = self.free[0]
            del self.free[0]
        else:
            thread = DownloadThread(self)

        thread.put(self.pyload.files.get_file(info.fid))

        # wait until it picked up the task
        thread.isWorking.wait()
        self.working.append(thread)

    @lock
    def start_decrypter_thread(self, info):
        """ Start decrypting of entered data, all links in one package are accumulated to one thread."""
        self.pyload.files.set_download_status(info.fid, DS.Decrypting)
        self.decrypter.append(DecrypterThread(self, [(info.download.url, info.download.plugin)],
                                              info.fid, info.package, info.owner))

    @read_lock
    def active_downloads(self, uid=None):
        """ retrieve pyfiles of running downloads  """
        return [x.active for x in self.working
                if uid is None or x.active.owner == uid]

    @read_lock
    def waiting_downloads(self):
        """ all waiting downloads """
        return [x.active for x in self.working if x.active.has_status("waiting")]

    @read_lock
    def get_progress_list(self, uid):
        """ Progress of all running downloads """
        # decrypter progress could be none
        return [x for x in [p.getProgress() for p in self.working + self.decrypter
                       if uid is None or p.owner == uid] if x is not None]

    def processing_ids(self):
        """get a id list of all pyfiles processed"""
        return [x.fid for x in self.active_downloads(None)]


    @read_lock
    def shutdown(self):
        """  End all threads """
        self.paused = True
        for thread in self.working + self.free:
            thread.put("quit")

    def work(self):
        """ main routine that does the periodical work """

        self.try_reconnect()

        if free_space(self.pyload.config["general"]["download_folder"]) / 1024 / 1024 < \
                self.pyload.config["general"]["min_free_space"]:
            self.log.warning(_("Not enough space left on device"))
            self.paused = True

        if self.paused or not self.pyload.api.is_time_download():
            return False

        # at least one thread want reconnect and we are supposed to wait
        if self.pyload.config['reconnect']['wait'] and self.want_reconnect() > 1:
            return False

        self.assign_jobs()

        # TODO: clean free threads

    def assign_jobs(self):
        """ Load jobs from db and try to assign them """

        limit = self.pyload.config['download']['max_downloads'] - len(self.active_downloads())

        # check for waiting dl rule
        if limit <= 0:
            # increase limit if there are waiting downloads
            limit += min(len(self.waiting_downloads()), self.pyload.config['download']['wait_downloads'] +
                                                  self.pyload.config['download']['max_downloads'] - len(
                self.active_downloads()))

        slots = self.get_remaining_plugin_slots()
        occ = tuple([plugin for plugin, v in slots.items() if v == 0])
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
        """ make a fair choice of which k jobs to start """
        # TODO: prefer admins, make a fairer choice?
        if k <= 0: return []
        if k >= len(jobs): return jobs

        return sample(jobs, k)

    def start_job(self, info, limit):
        """ start a download or decrypter thread with given file info """

        plugin = self.pyload.pluginmanager.find_plugin(info.download.plugin)
        # this plugin does not exits
        if plugin is None:
            self.log.error(_("Plugin '%s' does not exists") % info.download.plugin)
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
            self.log.error(_("Plugin type '%s' can't be used for downloading") % plugin)

        return False

    @read_lock
    def try_reconnect(self):
        """checks if reconnect needed"""

        if not self.pyload.config["reconnect"]["activated"] or not self.pyload.api.is_time_reconnect():
            return False

        # only reconnect when all threads are ready
        if not (0 < self.want_reconnect() == len(self.working)):
            return False

        if not exists(self.pyload.config['reconnect']['method']):
            if exists(join(pypath, self.pyload.config['reconnect']['method'])):
                self.pyload.config['reconnect']['method'] = join(pypath, self.pyload.config['reconnect']['method'])
            else:
                self.pyload.config["reconnect"]["activated"] = False
                self.log.warning(_("Reconnect script not found!"))
                return

        self.reconnecting.set()

        self.log.info(_("Starting reconnect"))

        # wait until all thread got the event
        while [x.active.plugin.waiting for x in self.working].count(True) != 0:
            sleep(0.25)

        old_ip = get_ip()

        self.pyload.evm.dispatch_event("reconnect:before", old_ip)
        self.log.debug("Old IP: %s" % old_ip)

        try:
            call(self.pyload.config['reconnect']['method'], shell=True)
        except Exception:
            self.log.warning(_("Failed executing reconnect script!"))
            self.pyload.config["reconnect"]["activated"] = False
            self.reconnecting.clear()
            self.pyload.print_exc()
            return

        sleep(1)
        ip = get_ip()
        self.pyload.evm.dispatch_event("reconnect:after", ip)

        if not old_ip or old_ip == ip:
            self.log.warning(_("Reconnect not successful"))
        else:
            self.log.info(_("Reconnected, new IP: %s") % ip)

        self.reconnecting.clear()

    @read_lock
    def want_reconnect(self):
        """ number of downloads that are waiting for reconnect """
        active = [x.active.has_plugin() and x.active.plugin.wantReconnect and x.active.plugin.waiting for x in self.working]
        return active.count(True)

    @read_lock
    def get_remaining_plugin_slots(self):
        """  dict of plugin names mapped to remaining dls  """
        occ = {}
        # decrypter are treated as occupied
        for p in self.decrypter:
            progress = p.getProgress()
            if progress:
                occ[progress.plugin] = 0

        # get all default dl limits
        for t in self.working:
            if not t.active.has_plugin(): continue
            limit = t.active.plugin.get_download_limit()
            # limit <= 0 means no limit
            occ[t.active.pluginname] = limit if limit > 0 else float('inf')

        # subtract with running downloads
        for t in self.working:
            if not t.active.has_plugin(): continue
            plugin = t.active.pluginname
            if plugin in occ:
                occ[plugin] -= 1

        return occ
