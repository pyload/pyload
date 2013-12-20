#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2013 pyLoad Team
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

from os.path import exists, join
import re
from subprocess import Popen
from threading import Event, Lock
from time import sleep, time
from traceback import print_exc
from random import choice

from pyload.datatypes.PyFile import PyFile
from pyload.datatypes.OnlineCheck import OnlineCheck
from pyload.network.RequestFactory import getURL
from pyload.utils import lock, uniqify, to_list
from pyload.utils.fs import free_space

from DecrypterThread import DecrypterThread
from DownloadThread import DownloadThread
from InfoThread import InfoThread


class ThreadManager:
    """manages the download threads, assign jobs, reconnect etc"""


    def __init__(self, core):
        """Constructor"""
        self.core = core
        self.log = core.log

        self.threads = []  # thread list
        self.localThreads = []  #addon+decrypter threads

        self.pause = True

        self.reconnecting = Event()
        self.reconnecting.clear()
        self.downloaded = 0 #number of files downloaded since last cleanup

        self.lock = Lock()

        # some operations require to fetch url info from hoster, so we caching them so it wont be done twice
        # contains a timestamp and will be purged after timeout
        self.infoCache = {}

        # pool of ids for online check
        self.resultIDs = 0

        # saved online checks
        self.infoResults = {}

        # timeout for cache purge
        self.timestamp = 0

        for i in range(self.core.config.get("download", "max_downloads")):
            self.createThread()


    def createThread(self):
        """create a download thread"""

        thread = DownloadThread(self)
        self.threads.append(thread)

    def createInfoThread(self, data, pid):
        """ start a thread which fetches online status and other info's """
        self.timestamp = time() + 5 * 60
        if data: InfoThread(self, None, data, pid)

    @lock
    def createResultThread(self, user, data):
        """ creates a thread to fetch online status, returns result id """
        self.timestamp = time() + 5 * 60

        rid = self.resultIDs
        self.resultIDs += 1

        oc = OnlineCheck(rid, user)
        self.infoResults[rid] = oc

        InfoThread(self, user, data, oc=oc)

        return rid

    @lock
    def createDecryptThread(self, data, pid):
        """ Start decrypting of entered data, all links in one package are accumulated to one thread."""
        if data: DecrypterThread(self, data, pid)

    @lock
    def getInfoResult(self, rid):
        return self.infoResults.get(rid)

    def setInfoResults(self, oc, result):
        self.core.evm.dispatchEvent("linkcheck:updated", oc.rid, result, owner=oc.owner)
        oc.update(result)

    def getActiveDownloads(self, user=None):
        # TODO: user context
        return [x.active for x in self.threads if x.active and isinstance(x.active, PyFile)]

    def getProgressList(self, user=None):
        info = []

        for thread in self.threads + self.localThreads:
            # skip if not belong to current user
            if user is not None and thread.owner != user: continue

            progress = thread.getProgress()
            if progress: info.extend(to_list(progress))

        return info

    def getActiveFiles(self):
        active = self.getActiveDownloads()

        for t in self.localThreads:
            active.extend(t.getActiveFiles())

        return active

    def processingIds(self):
        """get a id list of all pyfiles processed"""
        return [x.id for x in self.getActiveFiles()]

    def work(self):
        """run all task which have to be done (this is for repetetive call by core)"""
        try:
            self.tryReconnect()
        except Exception, e:
            self.log.error(_("Reconnect Failed: %s") % str(e))
            self.reconnecting.clear()
            self.core.print_exc()

        self.checkThreadCount()

        try:
            self.assignJob()
        except Exception, e:
            self.log.warning("Assign job error", e)
            self.core.print_exc()

            sleep(0.5)
            self.assignJob()
            #it may be failed non critical so we try it again

        if self.infoCache and self.timestamp < time():
            self.infoCache.clear()
            self.log.debug("Cleared Result cache")

        for rid in self.infoResults.keys():
            if self.infoResults[rid].isStale():
                del self.infoResults[rid]
  
    def tryReconnect(self, force=False):
        """checks if reconnect needed"""

        if not (self.core.config["reconnect"]["activated"] and self.core.api.isTimeReconnect()):
            return False

        if not force:
            reconnable = [1 if x.active.plugin.wantReconnect and x.active.plugin.waiting and self.pyfile.waitUntil - time() > 60
                          else 0 if not x.active.plugin.waiting and not x.active.plugin.resumeDownload else 2
                          for x in self.threads if x.active]
            if not reconnable.count(1) or reconnable.count(0):
                return

        if not exists(self.core.config['reconnect']['method']):
            reconn_path = join(pypath, self.core.config['reconnect']['method'])
            if exists():
                self.core.config['reconnect']['method'] = reconn_path
            else:
                self.core.config["reconnect"]["activated"] = False
                self.log.warning(_("Reconnect script not found!"))
                return

        self.reconnecting.set()

        #Do reconnect
        self.log.info(_("Starting reconnect"))

        reconnected = False

        while [x.active.plugin.waiting for x in self.threads if x.active].count(True) != 0:
            sleep(0.25)

        oldip = self.getIP()
        self.log.debug("Old IP: %s" % oldip)
        self.core.evm.dispatchEvent("reconnect:before", oldip)

        if not self.reconnecting.isSet():
            self.log.info(_("Reconnect aborted"))
            return

        try:
            retries = self.config["reconnect"]["retries"]
            for i in xrange((retries if retries > 0 else 0) + 1):
                reconn = Popen(self.core.config['reconnect']['method'], bufsize=-1, shell=True)#, stdout=subprocess.PIPE)
                newip = self.getIP()
                if newip != oldip:
                    reconnected = True
                    break
            reconn.wait()
            sleep(1)
        except:
            self.log.warning(_("Failed executing reconnect script!"))
            self.core.config["reconnect"]["activated"] = False
            self.core.print_exc()

        self.reconnecting.clear()

        self.log.debug("Current IP: %s" % newip)
        if reconnected:
            self.log.info(_("Reconnect succeed"))
            self.core.evm.dispatchEvent("reconnect:after", newip, oldip)
        else:
            self.log.info(_("Reconnect failed"))
            self.core.evm.dispatchEvent("reconnect:failed", newip)

    def getIP(self):
        """retrieve current ip"""
        services = [("http://automation.whatismyip.com/n09230945.asp", "(\S+)"),
                    ("http://checkip.dyndns.org/", ".*Current IP Address: (\S+)</body>.*")]

        ip = ""
        for i in range(10):
            try:
                sv = choice(services)
                ip = getURL(sv[0])
                ip = re.match(sv[1], ip).group(1)
                break
            except:
                ip = ""
                sleep(1)

        return ip

    def checkThreadCount(self):
        """checks if there is a need for increasing or reducing thread count"""

        if len(self.threads) == self.core.config.get("download", "max_downloads"):
            return True
        elif len(self.threads) < self.core.config.get("download", "max_downloads"):
            self.createThread()
        else:
            free = [x for x in self.threads if not x.active]
            if free:
                free[0].put("quit")


    def cleanPycurl(self):
        """ make a global curl cleanup (currently unused) """
        if self.processingIds():
            return False
        import pycurl

        pycurl.global_cleanup()
        pycurl.global_init(pycurl.GLOBAL_DEFAULT)
        self.downloaded = 0
        self.log.debug("Cleaned up pycurl")
        return True


    def assignJob(self):
        """assign a job to a thread if possible"""

        if self.pause or not self.core.api.isTimeDownload(): return

        #if self.downloaded > 20:
        #    if not self.cleanPyCurl(): return

        free = [x for x in self.threads if not x.active]

        inuse = [(x.active.pluginname, x.active.plugin.getDownloadLimit()) for x in self.threads if
                 x.active and x.active.hasPlugin()]
        inuse = [(x[0], x[1], len([y for y in self.threads if y.active and y.active.pluginname == x[0]])) for x in
                 inuse]
        occ = tuple(sorted(uniqify([x[0] for x in inuse if 0 < x[1] <= x[2]])))

        job = self.core.files.getJob(occ)
        if job:
            try:
                job.initPlugin()
            except Exception, e:
                self.log.critical(str(e))
                print_exc()
                job.setStatus("failed")
                job.error = str(e)
                job.release()
                return

            spaceLeft = free_space(self.core.config["general"]["download_folder"]) / 1024 / 1024
            if spaceLeft < self.core.config["general"]["min_free_space"]:
                self.log.warning(_("Not enough space left on device"))
                self.pause = True

            if free and not self.pause:
                thread = free[0]
                #self.downloaded += 1
                thread.put(job)
            else:
                #put job back
                if occ not in self.core.files.jobCache:
                    self.core.files.jobCache[occ] = []
                self.core.files.jobCache[occ].append(job.id)
