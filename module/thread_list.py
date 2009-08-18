#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Copyright (C) 2009 sp00b, sebnapi, RaNaN
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
from __future__ import with_statement
import re
import subprocess
import time
import urllib2
from os.path import exists
from threading import RLock

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
        self.pause = False
        self.reconnecting = False

        self.select_thread()

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

        if not self.parent.is_dltime() or self.pause or self.reconnecting or not self.list.files: #conditions when threads dont download
            return None

        self.init_reconnect()

        self.lock.acquire()

        pyfile = None
        for i in range(len(self.list.files)):
            if not self.list.files[i].modul.__name__ in self.occ_plugins:
                pyfile = self.list.files.pop(i)
                break

        if pyfile:
            self.py_downloading.append(pyfile)
            if not pyfile.plugin.multi_dl:
                self.occ_plugins.append(pyfile.modul.__name__)
            self.parent.logger.info('Download starts: ' + pyfile.url)

        self.lock.release()
        return pyfile


    def job_finished(self, pyfile):
        """manage completing download"""
        self.lock.acquire()

        if not pyfile.plugin.multi_dl:
            self.occ_plugins.remove(pyfile.modul.__name__)

        if pyfile.plugin.req.curl and not pyfile.status == "reconnected":
            try:
                pyfile.plugin.req.pycurl.close()
            except:
                pass

        self.py_downloading.remove(pyfile)

        if pyfile.status.type == "finished":
            self.parent.logger.info('Download finished: ' + pyfile.url + ' @' + str(pyfile.status.get_speed()) + 'kb/s')

            self.list.remove(pyfile)

            if pyfile.plugin.props['type'] == "container":
                self.list.extend(pyfile.plugin.links)


        elif pyfile.status.type == "reconnected":#put it back in queque
            pyfile.plugin.req.init_curl()
            self.list.files.insert(0, pyfile)

        elif pyfile.status.type == "failed":
            self.parent.logger.warning("Download failed: " + pyfile.url+ " | " + pyfile.status.error)
            with open(self.parent.config['general']['failed_file'], 'a') as f:
                f.write(pyfile.url + "\n")
            self.list.remove(pyfile)

        elif pyfile.status.type == "aborted":
            self.parent.logger.info("Download aborted: " + pyfile.url)
            self.list.remove(pyfile)

        self.list.save()

        self.lock.release()
        return True

    def init_reconnect(self):
        """initialise a reonnect"""
        if not self.parent.config['general']['use_reconnect'] or self.reconnecting or not self.parent.is_reconnect_time():
            return False

        if not exists(self.parent.config['general']['reconnect_method']):
            self.parent.logger.info(self.parent.config['general']['reconnect_method'] + " not found")
            self.parent.config['general']['use_reconnect'] = False
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
        reconn = subprocess.Popen(self.parent.config['general']['reconnect_method'])
        reconn.wait()
        time.sleep(1)
        ip = ""
        while ip == "": #solange versuch bis neue ip ausgelesen
            try:
                ip = re.match(".*Current IP Address: (.*)</body>.*", urllib2.urlopen("http://checkip.dyndns.org/").read()).group(1) #versuchen neue ip aus zu lesen
            except:
                ip = ""
            time.sleep(1)
        self.parent.logger.info("Reconnected, new IP: " + ip)
