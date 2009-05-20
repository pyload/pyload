#!/usr/bin/python
# -*- coding: utf-8 -*- 
# 
#Copyright (C) 2009 sp00b, sebnapi
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License,
#or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
###

import threading
from time import time, sleep
from copy import copy
import urllib


class Status(object):
    """ Saves all status information
    """
    def __init__(self, pyfile):
        self.pyfile = pyfile
        self.type = None
        self.status_queue = None
        self.total_kb = 0
        self.downloaded_kb = 0
        self.rate = 0
        self.expected_time = 0
        self.filename = None
        self.url = None
        self.exists = None
        self.waituntil = None
        self.want_reconnect = None
    
    def __call__(self, blocks_read, block_size, total_size):
        if self.status_queue == None:
            return False
        self.start = time()
        self.last_status = time()
        self.total_kb = total_size / 1024
        self.downloaded_kb = (blocks_read * block_size) / 1024
        elapsed_time = time() - self.start
        if elapsed_time != 0:
            self.rate = self.downloaded_kb / elapsed_time
            if self.rate != 0:
                self.expected_time = self.downloaded_kb / self.rate
        if self.last_status+0.2 < time():
            self.status_queue.put(copy(self))
            self.last_status = time()
    
    def set_status_queue(self, queue):
        self.status_queue = queue

    def get_ETA(self):
        return self.pyfile.plugin.req.get_ETA()
    def get_speed(self):
        return self.pyfile.plugin.req.get_speed()
    def kB_left():
        return self.pyfile.plugins.req.kB_left()
            
            
class Download_Thread(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.shutdown = False
        self.parent = parent
        self.setDaemon(True)
        self.loadedPyFile = None
        
        self.start()
        
    def run(self):
        while (not self.shutdown):
            if not self.parent.download_queue.empty():
                self.loadedPyFile = self.parent.getJob()
                self.download(self.loadedPyFile)
                
        if self.shutdown:
            sleep(1)
            self.parent.remove_thread(self)

    def download(self, py_load_file):
	pyfile = py_load_file
        status = pyfile.status
        pyfile.prepareDownload()

	if not status.exists:
            return False
            
        if status.want_reconnect:
            print "handle reconnect"
            return False
        
    	while (time() < status.waituntil):
            status.type = "waiting"
	    sleep(1) #eventuell auf genaue zeit warten

	#missing wenn datei nicht auf server vorhanden
        #if type=="check":
            #return params
        #if type in 'missing':
            #self.status = "missing"
            #print "Datei auf Server nicht vorhanden: " + params
            ##im logger eintragen das datei auf server nicht vorhanden ist
            #warning("Datei auf Server nicht voblocks_readrhanden: " + url)

        print "going to download"
        status.type = "downloading"
        print status.url , status.filename

        pyfile.plugin.req.download(status.url, pyfile.download_folder + "/" + status.filename)
        status.type = "finished"
        #startet downloader
        #urllib.urlretrieve(status.url, pyfile.download_folder + "/" + status.filename, status)        
        #self.shutdown = True
