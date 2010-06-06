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
    
    @author: mkaay
    @author: spoob
    @author: sebnapi
    @author: RaNaN
    @version: v0.3.2
"""

from __future__ import with_statement
from os.path import exists
import re
import subprocess
from threading import RLock, Thread
from time import sleep
from module.network.Request import getURL
from module.DownloadThread import DownloadThread
from module.SpeedManager import SpeedManager

class ThreadManager(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent
        self.list = parent.file_list #file list
        self.threads = []
        self.lock = RLock()
        self.py_downloading = [] # files downloading
        self.occ_plugins = [] #occupied plugins
        self.pause = True
        self.reconnecting = False

        self.speedManager = SpeedManager(self)
    
    def run(self):
        while True:
            if (len(self.threads) < int(self.parent.config['general']['max_downloads']) or self.isDecryptWaiting()) and not self.pause:
                job = self.getJob()
                if job:
                    thread = self.createThread(job)
                    thread.start()
            sleep(1)

    def createThread(self, job):
        """ creates thread for Py_Load_File and append thread to self.threads
        """
        thread = DownloadThread(self, job)
        self.threads.append(thread)
        return thread

    def removeThread(self, thread):
        self.threads.remove(thread)

    def getJob(self):
        """return job if suitable, otherwise send thread idle"""

        if not self.parent.server_methods.is_time_download() or self.pause or self.reconnecting or self.list.queueEmpty(): #conditions when threads dont download
            return None
        
        if self.parent.freeSpace() < self.parent.config["general"]["min_free_space"]:
            self.parent.logger.debug(_("minimal free space exceeded"))
            return None

        self.initReconnect()

        self.lock.acquire()

        pyfile = None
        pyfiles = self.list.getDownloadList(self.occ_plugins)

        if pyfiles:
            pyfile = pyfiles[0]
            self.py_downloading.append(pyfile)
            self.parent.hookManager.downloadStarts(pyfile)
            if not pyfile.plugin.multi_dl:
                self.occ_plugins.append(pyfile.plugin.__name__)
            pyfile.active = True
            if pyfile.plugin.__type__ == "container":
                self.parent.logger.info(_("Get links from: %s") % pyfile.url)
            else:
                self.parent.logger.info(_("Download starts: %s") % pyfile.url)

        self.lock.release()
        return pyfile
    
    def isDecryptWaiting(self):
        pyfiles = self.list.getDownloadList(self.occ_plugins)
        for pyfile in pyfiles:
            if pyfile.plugin.__type__ == "container":
                return True
        return False
    
    def handleNewInterface(self, pyfile):
        plugin = pyfile.plugin
        if plugin.__type__ == "container":
            if plugin.createNewPackage():
                packages = plugin.getPackages()
                if len(packages) == 1:
                    self.parent.logger.info(_("1 new package from %s") % (pyfile.status.filename,))
                else:
                    self.parent.logger.info(_("%i new packages from %s") % (len(packages), pyfile.status.filename))
                for name, links in packages:
                    pid = self.list.packager.addNewPackage(name)
                    for link in links:
                        newFile = self.list.collector.addLink(link)
                        self.list.packager.addFileToPackage(pid, self.list.collector.popFile(newFile))
                    if len(links) == 1:
                        self.parent.logger.info(_("1 link in %s") % (name,))
                    else:
                        self.parent.logger.info(_("%i links in %s") % (len(links), name))
            else:
                pass
    
    def jobFinished(self, pyfile):
        """manage completing download"""
        self.lock.acquire()

        if not pyfile.plugin.multi_dl:
            self.occ_plugins.remove(pyfile.plugin.__name__)
            
        pyfile.active = False

        if not pyfile.status == "reconnected":
            try:
                pyfile.plugin.req.pycurl.close()
            except:
                pass

        self.py_downloading.remove(pyfile)

        if pyfile.status.type == "finished":
            if hasattr(pyfile.plugin, "__interface__") and pyfile.plugin.__interface__ >= 2:
                self.handleNewInterface(pyfile)
            elif pyfile.plugin.__type__ == "container":
                newLinks = 0
                if pyfile.plugin.links:
                    if isinstance(pyfile.plugin.links, dict):
                        packmap = {}
                        for packname in pyfile.plugin.links.keys():
                            packmap[packname] = self.list.packager.addNewPackage(packname)
                        for packname, links in pyfile.plugin.links.items():
                            pid = packmap[packname]
                            for link in links:
                                newFile = self.list.collector.addLink(link)
                                self.list.packager.addFileToPackage(pid, self.list.collector.popFile(newFile))
                                newLinks += 1
                    else:
                        for link in pyfile.plugin.links:
                            newFile = self.list.collector.addLink(link)
                            self.list.packager.addFileToPackage(pyfile.package.data["id"], self.list.collector.popFile(newFile))
                            newLinks += 1
                        #self.list.packager.pushPackage2Queue(pyfile.package.data["id"])
                self.list.packager.removeFileFromPackage(pyfile.id, pyfile.package.data["id"])
    
                if newLinks:
                    self.parent.logger.info(_("Parsed links from %s: %i") % (pyfile.status.filename, newLinks))
                else:
                    self.parent.logger.info(_("No links in %s") % pyfile.status.filename)
                #~ self.list.packager.removeFileFromPackage(pyfile.id, pyfile.package.id)
                #~ for link in pyfile.plugin.links:
                #~ id = self.list.collector.addLink(link)
                #~ pyfile.packager.pullOutPackage(pyfile.package.id)
                #~ pyfile.packager.addFileToPackage(pyfile.package.id, pyfile.collector.popFile(id))
            else:
                self.parent.logger.info(_("Download finished: %s") % pyfile.url)

        elif pyfile.status.type == "reconnected":
            pyfile.plugin.req.init_curl()

        elif pyfile.status.type == "failed":
            self.parent.logger.warning(_("Download failed: %s | %s") % (pyfile.url, pyfile.status.error))
            with open(self.parent.config['general']['failed_file'], 'a') as f:
                f.write(pyfile.url + "\n")

        elif pyfile.status.type == "aborted":
            self.parent.logger.info(_("Download aborted: %s") % pyfile.url)

        self.list.save()

        self.parent.hookManager.downloadFinished(pyfile)

        self.lock.release()
        return True

    def initReconnect(self):
        """initialise a reonnect"""
        if not self.parent.config['reconnect']['activated'] or self.reconnecting or not self.parent.server_methods.is_time_reconnect():
            return False

        if not exists(self.parent.config['reconnect']['method']):
            self.parent.logger.info(self.parent.config['reconnect']['method'] + " not found")
            self.parent.config['reconnect']['activated'] = False
            return False

        self.lock.acquire()

        if self.checkReconnect():
            self.reconnecting = True
            self.reconnect()
            sleep(1.1)

            self.reconnecting = False
            self.lock.release()
            return True

        self.lock.release()
        return False

    def checkReconnect(self):
        """checks if all files want reconnect"""

        if not self.py_downloading:
            return False

        i = 0
        for obj in self.py_downloading:
            if obj.status.want_reconnect:
                i += 1

        if len(self.py_downloading) == i:
            return True
        else:
            return False

    def reconnect(self):
        self.parent.logger.info(_("Starting reconnect"))
        ip = re.match(".*Current IP Address: (.*)</body>.*", getURL("http://checkip.dyndns.org/")).group(1)
        self.parent.hookManager.beforeReconnecting(ip)
        reconn = subprocess.Popen(self.parent.config['reconnect']['method'])#, stdout=subprocess.PIPE)
        reconn.wait()
        sleep(1)
        ip = ""
        while ip == "":
            try:
                ip = re.match(".*Current IP Address: (.*)</body>.*", getURL("http://checkip.dyndns.org/")).group(1) #versuchen neue ip aus zu lesen
            except:
                ip = ""
            sleep(1)
        self.parent.hookManager.afterReconnecting(ip)
        self.parent.logger.info(_("Reconnected, new IP: %s") % ip)
    
    def stopAllDownloads(self):
        self.pause = True
        for pyfile in self.py_downloading:
            pyfile.plugin.req.abort = True
