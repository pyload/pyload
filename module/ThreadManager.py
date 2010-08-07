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

from threading import Event
from subprocess import Popen
from os.path import exists
from time import sleep
from traceback import print_exc
import re

from module.network.Request import getURL
import PluginThread

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
        
        for i in range(0, self.core.config.get("general","max_downloads") ):
            self.createThread()
        
        
        
    #----------------------------------------------------------------------
    def createThread(self):
        """create a download thread"""
        
        thread = PluginThread.DownloadThread(self)        
        self.threads.append(thread)
        
    #----------------------------------------------------------------------
    def createInfoThread(self, data):
        """
        start a thread whichs fetches online status and other infos
        data = [ .. () .. ]
        """
        
        PluginThread.InfoThread(self, data)
        
        
    #----------------------------------------------------------------------
    def downloadingIds(self):
        """get a list of the currently downloading pyfile's ids"""
        return [x.active.id for x in self.threads if x.active and x.active != "quit"]
    
    #----------------------------------------------------------------------
    def processingIds(self):
        """get a id list of all pyfiles processed"""
        return [x.active.id for x in self.threads+self.localThreads if x.active and x.active != "quit"]
        
        
    #----------------------------------------------------------------------
    def work(self):
        """run all task which have to be done (this is for repetivive call by core)"""
                
        self.tryReconnect()
        self.checkThreadCount()
        self.assignJob()
    
    #----------------------------------------------------------------------
    def tryReconnect(self):
        """checks if reconnect needed"""
        
        if not (self.core.server_methods.is_time_reconnect() and self.core.config["reconnect"]["activated"] ):
            return False
                        
        active = [x.active.plugin.wantReconnect and x.active.plugin.waiting for x in self.threads if x.active]

        if active.count(True) > 0 and len(active) == active.count(True):
        
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
                
                        
            ip = re.match(".*Current IP Address: (.*)</body>.*", getURL("http://checkip.dyndns.org/")).group(1)
            
            self.core.hookManager.beforeReconnecting(ip)
            reconn = Popen(self.core.config['reconnect']['method'])#, stdout=subprocess.PIPE)
            reconn.wait()
            sleep(1)
            ip = ""
            while ip == "":
                    try:
                            ip = re.match(".*Current IP Address: (.*)</body>.*", getURL("http://checkip.dyndns.org/")).group(1) #get new ip
                    except:
                            ip = ""
                    sleep(1)
            self.core.hookManager.afterReconnecting(ip)
            
            self.log.info(_("Reconnected, new IP: %s") % ip)
    
                    
            self.reconnecting.clear()
    
    #----------------------------------------------------------------------
    def checkThreadCount(self):
        """checks if there are need for increasing or reducing thread count"""
        
        if len(self.threads) == self.core.config.get("general", "max_downloads"):
            return True
        elif len(self.threads) < self.core.config.get("general", "max_downloads"):
            self.createThread()
        else:
            #@TODO: close thread
            pass
        
    
    #----------------------------------------------------------------------
    def assignJob(self):
        """assing a job to a thread if possible"""
        
        if self.pause: return
        
        free = [x for x in self.threads if not x.active]


        
        occ = [x.active.pluginname for x in self.threads if x.active and not x.active.plugin.multiDL ]
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
                    thread.put(job)
                else:
                    #put job back
                    self.core.files.jobCache[occ].append(job.id)
                    
            else:
                thread = PluginThread.DecrypterThread(self, job)
        