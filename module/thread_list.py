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
    @version: v0.3.1
"""

from __future__ import with_statement
from os.path import exists
import re
import subprocess
from threading import RLock, Thread
import time
import urllib2
from download_thread import Download_Thread

class Thread_List(object):
    def __init__(self, parent):
        self.parent = parent
        self.list = parent.file_list #file list
        self.threads = []
        self.max_threads = int(self.parent.config['general']['max_downloads'])
        self.lock = RLock()
        self.py_downloading = [] # files downloading
        self.occ_plugins = [] #occupied plugins
        self.pause = True
        self.reconnecting = False

        self.select_thread()
        if self.parent.config['general']['download_speed_limit'] != 0:
            self.speedManager = self.SpeedManager(self)

    def create_thread(self):
        """ creates thread for Py_Load_File and append thread to self.threads
        """
        thread = Download_Thread(self)
        self.threads.append(thread)
        return True

    def remove_thread(self, thread):
        self.threads.remove(thread)

    def select_thread(self):
        """ create all threads
        """
        while len(self.threads) < self.max_threads:
            self.create_thread()

    def get_job(self):
        """return job if suitable, otherwise send thread idle"""

        if not self.parent.server_methods.is_time_download() or self.pause or self.reconnecting or self.list.queueEmpty(): #conditions when threads dont download
            return None
        
        if self.parent.freeSpace() < self.parent.config["general"]["min_free_space"]:
            self.parent.logger.debug("min free space exceeded")
            return None

        self.init_reconnect()

        self.lock.acquire()

        pyfile = None
        pyfiles = self.list.getDownloadList(self.occ_plugins)

        if pyfiles:
            pyfile = pyfiles[0]
            self.py_downloading.append(pyfile)
            self.parent.hookManager.downloadStarts(pyfile)
            if not pyfile.plugin.multi_dl:
                self.occ_plugins.append(pyfile.modul.__name__)
            pyfile.active = True
            if pyfile.plugin.props['type'] == "container":
                self.parent.logger.info(_("Get links from: %s") % pyfile.url)
            else:
                self.parent.logger.info(_("Download starts: %s") % pyfile.url)

        self.lock.release()
        return pyfile

    def job_finished(self, pyfile):
        """manage completing download"""
        self.lock.acquire()

        if not pyfile.plugin.multi_dl:
            self.occ_plugins.remove(pyfile.modul.__name__)
            
        pyfile.active = False

        if not pyfile.status == "reconnected":
            try:
                pyfile.plugin.req.pycurl.close()
            except:
                pass

        self.py_downloading.remove(pyfile)

        if pyfile.status.type == "finished":
            if pyfile.plugin.props['type'] == "container":
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

    def init_reconnect(self):
        """initialise a reonnect"""
        if not self.parent.config['reconnect']['activated'] or self.reconnecting or not self.parent.server_methods.is_time_reconnect():
            return False

        if not exists(self.parent.config['reconnect']['method']):
            self.parent.logger.info(self.parent.config['reconnect']['method'] + " not found")
            self.parent.config['reconnect']['activated'] = False
            return False

        self.lock.acquire()

        if self.check_reconnect():
            self.reconnecting = True
            self.reconnect()
            time.sleep(1.1)

            self.reconnecting = False
            self.lock.release()
            return True

        self.lock.release()
        return False

    def check_reconnect(self):
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
        ip = re.match(".*Current IP Address: (.*)</body>.*", urllib2.urlopen("http://checkip.dyndns.org/").read()).group(1)
        self.parent.hookManager.beforeReconnecting(ip)
        reconn = subprocess.Popen(self.parent.config['reconnect']['method'])#, stdout=subprocess.PIPE)
        reconn.wait()
        time.sleep(1)
        ip = ""
        while ip == "":
            try:
                ip = re.match(".*Current IP Address: (.*)</body>.*", urllib2.urlopen("http://checkip.dyndns.org/").read()).group(1) #versuchen neue ip aus zu lesen
            except:
                ip = ""
            time.sleep(1)
        self.parent.hookManager.afterReconnecting(ip)
        self.parent.logger.info(_("Reconnected, new IP: %s") % ip)
    
    def stopAllDownloads(self):
        self.pause = True
        for pyfile in self.py_downloading:
            pyfile.plugin.req.abort = True
    
    class SpeedManager(Thread):
        def __init__(self, parent):
            Thread.__init__(self)
            self.parent = parent
            self.running = True
            self.lastSlowCheck = 0.0
            
            stat = {}
            stat["slow_downloads"] = None
            stat["each_speed"] = None
            stat["each_speed_optimized"] = None
            self.stat = stat
            
            self.slowCheckInterval = 60
            self.slowCheckTestTime = 25
            
            self.logger = self.parent.parent.logger
            self.start()
        
        def run(self):
            while self.running:
                time.sleep(1)
                self.manageSpeed()
        
        def getMaxSpeed(self):
            return self.parent.parent.getMaxSpeed()
        
        def manageSpeed(self):
            maxSpeed = self.getMaxSpeed()
            if maxSpeed <= 0:
                for thread in self.parent.py_downloading:
                    thread.plugin.req.speedLimitActive = False
                return
            threads = self.parent.py_downloading
            threadCount = len(threads)
            if threadCount <= 0:
                return
            eachSpeed = maxSpeed/threadCount
            
            currentOverallSpeed = 0
            restSpeed = maxSpeed - currentOverallSpeed
            speeds = []
            for thread in threads:
                currentOverallSpeed += thread.plugin.req.dl_speed
                speeds.append((thread.plugin.req.dl_speed, thread.plugin.req.averageSpeed, thread))
                thread.plugin.req.speedLimitActive = True
            
            if currentOverallSpeed+50 < maxSpeed:
                for thread in self.parent.py_downloading:
                    thread.plugin.req.speedLimitActive = False
                return
            
            slowCount = 0
            slowSpeed = 0
            if self.lastSlowCheck + self.slowCheckInterval + self.slowCheckTestTime < time.time():
                self.lastSlowCheck = time.time()
            if self.lastSlowCheck + self.slowCheckInterval < time.time() < self.lastSlowCheck + self.slowCheckInterval + self.slowCheckTestTime:
                for speed in speeds:
                    speed[2].plugin.req.isSlow = False
            else:
                for speed in speeds:
                    if speed[0] <= eachSpeed-7:
                        if speed[1] < eachSpeed-15:
                            if speed[2].plugin.req.dl_time > 0 and speed[2].plugin.req.dl_time+30 < time.time():
                                speed[2].plugin.req.isSlow = True
                                if not speed[1]-5 < speed[2].plugin.req.maxSpeed/1024 < speed[1]+5:
                                    speed[2].plugin.req.maxSpeed = (speed[1]+10)*1024
                    if speed[2].plugin.req.isSlow:
                        slowCount += 1
                        slowSpeed += speed[2].plugin.req.maxSpeed/1024
            stat = {}
            stat["slow_downloads"] = slowCount
            stat["each_speed"] = eachSpeed
            eachSpeed = (maxSpeed - slowSpeed) / (threadCount - slowCount)
            stat["each_speed_optimized"] = eachSpeed
            self.stat = stat
            
            for speed in speeds:
                if speed[2].plugin.req.isSlow:
                    continue
                speed[2].plugin.req.maxSpeed = eachSpeed*1024
                print "max", speed[2].plugin.req.maxSpeed, "current", speed[2].plugin.req.dl_speed
