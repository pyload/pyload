#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""

from os.path import exists, join
import re
from subprocess import Popen
from threading import Event
from time import sleep
from traceback import print_exc
from random import choice

import PluginThread
from module.network.Request import getURL

########################################################################
class ThreadManager:
    """manages the download threads, assign jobs, reconnect etc"""

    #----------------------------------------------------------------------
    def __init__(self, core):
        """Constructor"""
        self.core = core
        self.log = core.log

        self.threads = []  # thread list
        self.localThreads = []  #hook+decrypter threads

        #self.infoThread = PluginThread.InfoThread(self)

        self.pause = True

        self.reconnecting = Event()
        self.reconnecting.clear()
        self.downloaded = 0 #number of files downloaded since last cleanup

        #pycurl.global_init(pycurl.GLOBAL_DEFAULT)

        for i in range(0, self.core.config.get("general", "max_downloads")):
            self.createThread()



    #----------------------------------------------------------------------
    def createThread(self):
        """create a download thread"""

        thread = PluginThread.DownloadThread(self)
        self.threads.append(thread)

    #----------------------------------------------------------------------
    def createInfoThread(self, data, pid):
        """
        start a thread whichs fetches online status and other infos
        data = [ .. () .. ]
        """

        PluginThread.InfoThread(self, data, pid)


    #----------------------------------------------------------------------
    def downloadingIds(self):
        """get a list of the currently downloading pyfile's ids"""
        return [x.active.id for x in self.threads if x.active and x.active != "quit"]

    #----------------------------------------------------------------------
    def processingIds(self):
        """get a id list of all pyfiles processed"""
        return [x.active.id for x in self.threads + self.localThreads if x.active and x.active != "quit"]


    #----------------------------------------------------------------------
    def work(self):
        """run all task which have to be done (this is for repetivive call by core)"""
        try:
            self.tryReconnect()
        except Exception, e:
            self.log.error(_("Reconnect Failed: %s") % str(e) )
            self.reconnecting.clear()
            if self.core.debug:
                print_exc()
        self.checkThreadCount()
        self.assignJob()

    #----------------------------------------------------------------------
    def tryReconnect(self):
        """checks if reconnect needed"""

        if not (self.core.config["reconnect"]["activated"] and self.core.server_methods.is_time_reconnect()):
            return False

        active = [x.active.plugin.wantReconnect and x.active.plugin.waiting for x in self.threads if x.active]

        if not (active.count(True) > 0 and len(active) == active.count(True)):
            return False

        if not exists(self.core.config['reconnect']['method']):
            if exists(join(pypath, self.core.config['reconnect']['method'])):
                self.core.config['reconnect']['method'] = join(pypath, self.core.config['reconnect']['method'])
            else:
                self.core.config["reconnect"]["activated"] = False
                self.log.warning(_("Reconnect script not found!"))
                return

        self.reconnecting.set()

        #Do reconnect
        self.log.info(_("Starting reconnect"))

        while [x.active.plugin.waiting for x in self.threads if x.active].count(True) != 0:
            sleep(0.25)
            sleep(0.25)

        ip = self.getIP()

        self.core.hookManager.beforeReconnecting(ip)

        self.log.debug(_("Old IP: %s") % ip)

        try:
            reconn = Popen(self.core.config['reconnect']['method'], bufsize=-1, shell=True)#, stdout=subprocess.PIPE)
        except:
            self.log.warning(_("Failed executing reconnect script!"))
            self.core.config["reconnect"]["activated"] = False
            self.reconnecting.clear()
            if self.core.debug:
                print_exc()
            return

        reconn.wait()
        sleep(1)
        ip = self.getIP()
        self.core.hookManager.afterReconnecting(ip)
        self.closeAllConnecions()

        self.log.info(_("Reconnected, new IP: %s") % ip)

        self.reconnecting.clear()

    def getIP(self):
        """retrieve current ip"""
        services = [("http://www.whatismyip.com/automation/n09230945.asp", "(\S+)"),
                    ("http://checkip.dyndns.org/",".*Current IP Address: (\S+)</body>.*")]

        ip = ""
        while not ip:
            try:
                sv = choice(services)
                ip = getURL(sv[0])
                ip = re.match(sv[1], ip).group(1)
            except:
                ip = ""
                sleep(1)

        return ip

    #----------------------------------------------------------------------
    def checkThreadCount(self):
        """checks if there are need for increasing or reducing thread count"""

        if len(self.threads) == self.core.config.get("general", "max_downloads"):
            return True
        elif len(self.threads) < self.core.config.get("general", "max_downloads"):
            self.createThread()
        else:
            free = [x for x in self.threads if not x.active]
            if free:
                free[0].put("quit")


    #----------------------------------------------------------------------
    def assignJob(self):
        """assing a job to a thread if possible"""

        if self.pause or not self.core.server_methods.is_time_download(): return

        #if self.downloaded > 20:
        #    if not self.cleanPyCurl(): return

        free = [x for x in self.threads if not x.active]

        occ = [x.active.pluginname for x in self.threads if x.active and not x.active.plugin.multiDL]
        occ.sort()
        occ = tuple(set(occ))
        job = self.core.files.getJob(occ)
        if job:
            try:
                job.initPlugin()
            except Exception, e:
                self.log.critical(str(e))
                if self.core.debug:
                    print_exc()

            if job.plugin.__type__ == "hoster":
                if free:
                    thread = free[0]
                    #self.downloaded += 1

                    thread.put(job)
                else:
                    #put job back
                    if not self.core.files.jobCache.has_key(occ):
                        self.core.files.jobCache[occ] = []
                    self.core.files.jobCache[occ].append(job.id)

                    #check for decrypt jobs
                    job = self.core.files.getDecryptJob()
                    if job:
                        job.initPlugin()
                        thread = PluginThread.DecrypterThread(self, job)


            else:
                thread = PluginThread.DecrypterThread(self, job)

    def closeAllConnecions(self):
        """closes all connections, when a reconnect was made """
        for pyfile in self.core.files.cache.itervalues():
            if pyfile.plugin and pyfile.plugin.req:
                pyfile.plugin.req.http.closeAll()
