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
from __future__ import with_statement
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
    

    def get_job(self):
        """return job if suitable, otherwise send thread idle"""

        if not self.parent.is_dltime():
            return None

        if self.pause:
            return None
        
        if self.reconnecting:
            return None

        self.init_reconnect()

        self.lock.acquire()

        pyfile = None
        for i in range(len(self.py_load_files)):
            if not self.py_load_files[i].modul.__name__ in self.occ_plugins:
                pyfile = self.py_load_files.pop(i)
                break
        
        if pyfile:
            self.py_downloading.append(pyfile)	
            if not pyfile.plugin.multi_dl:
                self.occ_plugins.append(pyfile.modul.__name__)
            self.parent.logger.info('Download starts: ' + pyfile.url)
        
        self.lock.release()
        return pyfile
    
    
    def job_finished(self, pyfile):
        self.lock.acquire()
        
        if not pyfile.plugin.multi_dl:
            self.occ_plugins.remove(pyfile.modul.__name__)
    
        self.py_downloading.remove(pyfile)	

        if pyfile.status.type == "finished":
            self.parent.logger.info('Download finished: ' + pyfile.url + ' @' + str(pyfile.status.get_speed()) + 'kb/s')

            with open(self.parent.config['link_file'], 'r') as f:
                data = f.read()

            if pyfile.plugin.props['type'] == "container":
                links = ""

                for link in pyfile.plugin.links:
                    links += link+"\n"

                self.parent.extend_links(pyfile.plugin.links)
                data = links + data # put the links into text file

            data = data.replace(pyfile.url+'\n', "")

            with open(self.parent.config['link_file'], 'w') as f:
                f.write(data)

        if pyfile.status.type == "reconnected":#put it back in queque
            self.py_load_files.insert(0, pyfile)

        if pyfile.status.type == "failed":
            self.parent.logger.warning("Download failed: " + pyfile.url)
            with open(self.parent.config['failed_file'], 'a') as f:
                f.write(pyfile.url+"\n")

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

    def init_reconnect(self):
        """initialise a reonnect"""
        if not self.parent.config['use_reconnect']:
            return False

        if self.reconnecting:
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
        reconn = subprocess.Popen(self.parent.config['reconnectMethod'])
        reconn.wait()
        ip = re.match(".*Current IP Address: (.*)</body>.*", urllib2.urlopen("http://checkip.dyndns.org/").read()).group(1) #versuchen neue ip aus zu lesen
        while ip == "": #solange versuch bis neue ip ausgelesen
            ip = re.match(".*Current IP Address: (.*)</body>.*", urllib2.urlopen("http://checkip.dyndns.org/").read()).group(1)
            time.sleep(1)
        self.parent.logger.info("Reconnected, new IP: " + ip)
        
