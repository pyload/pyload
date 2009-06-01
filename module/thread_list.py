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
#python
import re
import subprocess
import time
import urllib2
from threading import RLock

from download_thread import Download_Thread

class Thread_List(object):
    def __init__(self, parent):
        self.parent = parent
        self.threads = []
        self.max_threads = 3
        self.py_load_files = [] # files in queque
        self.f_relation = [0, 0]
        self.lock = RLock()
        self.py_downloading = [] # files downloading
        self.occ_plugins = [] #occupied plugins
        self.pause = False
        self.reconnecting = False

    def create_thread(self):
        """ creates thread for Py_Load_File and append thread to self.threads
        """
        if self.py_load_files:
            thread = Download_Thread(self)
            self.threads.append(thread)
            return True
        
    def get_loaded_urls(self):
        loaded_urls = []
        for file in self.py_load_files:
            loaded_urls.append(file.url)
        return loaded_urls
    
    def remove_thread(self, thread):
        self.threads.remove(thread)
    
#    def status(self):
#        if not self.status_queue.empty():
#            while not self.status_queue.empty():
#                status = self.status_queue.get()
#                self.py_load_files[status.id].status = status

    def get_job(self):
        # return job if suitable, otherwise send thread idle
        self.lock.acquire()

        if not self.py_load_files:
            return False

        self.init_reconnect()

        if self.reconnecting:
            return None

        if self.pause:
            return None

        pyfile = None
        for i in range(len(self.py_load_files)):
            if not self.py_load_files[i].modul.__name__ in self.occ_plugins:
                pyfile = self.py_load_files.pop(i)
                break
        
        if pyfile:
            self.py_downloading.append(pyfile)	
            if not pyfile.plugin.multi_dl:
                self.occ_plugins.append(pyfile.modul.__name__)
            self.parent.logger.info('start downloading ' + pyfile.url)
        
        self.lock.release()
        return pyfile
    
    
    def job_finished(self, pyfile):
        self.lock.acquire()
        
        if not pyfile.plugin.multi_dl:
            self.occ_plugins.remove(pyfile.modul.__name__)
    
        self.py_downloading.remove(pyfile)	

        if pyfile.status.type == "finished":
            self.parent.logger.info('finished downloading ' + pyfile.url + ' @' + str(pyfile.status.get_speed()) + 'kb/s')

            #remove from txt

            if pyfile.plugin.props['type'] == "container":
                self.parent.extend_links(pyfile.plugin.links)

        if pyfile.status.type == "reconnected":
            print "put it back"
            self.py_load_files.insert(0, pyfile)

        self.lock.release()
        return True

    def extend_py_load_files(self):
        pass
    
    def select_thread(self):
        """ select a thread
        """
        if len(self.threads) < self.max_threads:
            self.create_thread()
    
    def append_py_load_file(self, py_load_file):
        py_load_file.id = len(self.py_load_files)
        self.py_load_files.append(py_load_file)
        self.f_relation[1] += 1
        self.select_thread()

    def init_reconnect(self, pyfile=None):

        self.lock.acquire()

        reconnecting = filter(lambda pyfile: pyfile.status.want_reconnect is True, self.py_downloading) #returns all which  want to reconenct


        if reconnecting and reconnecting == self.py_downloading:
            #if empty -> all want reconnect
            self.reconnecting = True
            self.parent.logger.info("Reconnecting")
            self.reconnect()
    
            self.py_downloading.remove(pyfile)

            while self.py_downloading:
                print "waiting"
                time.sleep(1)

            self.py_downloading.append(pyfile)

            self.reconnecting = False

            self.lock.release()

            return True

        else:
            self.lock.release()
            return False


    def reconnect(self):

        print "reconnected"
        return True

        reconn = subprocess.Popen(self.parent.config['reconnectMethod'])
        reconn.wait()
        ip = re.match(".*Current IP Address: (.*)</body>.*", urllib2.urlopen("http://checkip.dyndns.org/").read()).group(1) #versuchen neue ip aus zu lesen
        while ip == "": #solange versuch bis neue ip ausgelesen
            ip = re.match(".*Current IP Address: (.*)</body>.*", urllib2.urlopen("http://checkip.dyndns.org/").read()).group(1)
            time.sleep(1)
        self.parent.logger.info("Reconnected, new IP: " + ip)
        