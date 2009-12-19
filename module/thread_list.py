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
from os.path import exists
import re
import subprocess
from threading import RLock
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

        if not self.parent.server_methods.is_time_download() or self.pause or self.reconnecting or self.list.queueEmpty(): #conditions when threads dont download
            return None

        self.init_reconnect()

        self.lock.acquire()

        pyfile = None
        for f in self.list.getDownloadList():
            if not f.modul.__name__ in self.occ_plugins:
                pyfile = f
                break

        if pyfile:
            self.py_downloading.append(pyfile)
            self.scripts_download_preparing(pyfile.modul.__name__, pyfile.url)
            if not pyfile.plugin.multi_dl:
                self.occ_plugins.append(pyfile.modul.__name__)
            pyfile.active = True
            if pyfile.plugin.props['type'] == "container":
                self.parent.logger.info('Get links from: ' + pyfile.url)
            else:
                self.parent.logger.info('Download starts: ' + pyfile.url)

        self.lock.release()
        return pyfile


    def job_finished(self, pyfile):
        """manage completing download"""
        self.lock.acquire()

        if not pyfile.plugin.multi_dl:
            self.occ_plugins.remove(pyfile.modul.__name__)
            
        pyfile.active = False

        if pyfile.plugin.req.curl and not pyfile.status == "reconnected":
            try:
                pyfile.plugin.req.pycurl.close()
            except:
                pass

        self.py_downloading.remove(pyfile)

        if pyfile.status.type == "finished":
            if pyfile.plugin.props['type'] == "container":
                newLinks = 0
                if pyfile.plugin.links:
                    for link in pyfile.plugin.links:
			print link
                        newFile = self.list.collector.addLink(link)
                        self.list.packager.addFileToPackage(pyfile.package.data["id"], self.list.collector.popFile(newFile))
                        newLinks += 1
                    self.list.packager.pushPackage2Queue(pyfile.package.data["id"])
                self.list.packager.removeFileFromPackage(pyfile.id, pyfile.package.data["id"])
    
                if newLinks:
                    self.parent.logger.info("Parsed link from %s: %i" % (pyfile.status.filename, newLinks))
                else:
                    self.parent.logger.info("No links in %s" % pyfile.status.filename)
                #~ self.list.packager.removeFileFromPackage(pyfile.id, pyfile.package.id)
                #~ for link in pyfile.plugin.links:
                #~ id = self.list.collector.addLink(link)
                #~ pyfile.packager.pullOutPackage(pyfile.package.id)
                #~ pyfile.packager.addFileToPackage(pyfile.package.id, pyfile.collector.popFile(id))
            else:
                self.parent.logger.info("Download finished: %s" % pyfile.url)

        elif pyfile.status.type == "reconnected":
            pyfile.plugin.req.init_curl()

        elif pyfile.status.type == "failed":
            self.parent.logger.warning("Download failed: " + pyfile.url + " | " + pyfile.status.error)
            with open(self.parent.config['general']['failed_file'], 'a') as f:
                f.write(pyfile.url + "\n")

        elif pyfile.status.type == "aborted":
            self.parent.logger.info("Download aborted: " + pyfile.url)

        self.list.save()

        self.scripts_download_finished(pyfile.modul.__name__, pyfile.url, pyfile.status.filename, pyfile.folder)

        self.lock.release()
        return True

    def init_reconnect(self):
        """initialise a reonnect"""
        if not self.parent.config['general']['use_reconnect'] or self.reconnecting or not self.parent.server_methods.is_time_reconnect():
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
        reconn = subprocess.Popen(self.parent.config['general']['reconnect_method'], stdout=subprocess.PIPE)
        reconn.wait()
        time.sleep(1)
        ip = ""
        while ip == "": #solange versuch bis neue ip ausgelesen
            try:
                ip = re.match(".*Current IP Address: (.*)</body>.*", urllib2.urlopen("http://checkip.dyndns.org/").read()).group(1) #versuchen neue ip aus zu lesen
            except:
                ip = ""
            time.sleep(1)
        scripts_reconnected(ip)
        self.parent.logger.info("Reconnected, new IP: " + ip)


    def scripts_download_preparing(self, pluginname, url):
        for script in self.parent.scripts['download_preparing']:
            out = subprocess.Popen([script, pluginname, url], stdout=subprocess.PIPE)
            out.wait()

    def scripts_download_finished(self, pluginname, url, filename, location):
    	map(lambda script: subprocess.Popen([script, pluginname, url, filename, location], stdout=subprocess.PIPE), self.parent.scripts['download_finished'])

    def scripts_package_finished(self, name, location): #@TODO Implement!
    	map(lambda script: subprocess.Popen([script, name, location], stdout=subprocess.PIPE), self.parent.scripts['download_finished'])

    def scripts_reconnected(self, ip):
    	map(lambda script: subprocess.Popen([script, ip], stdout=subprocess.PIPE), self.parent.scripts['download_finished'])
