#!/usr/bin/env python
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
import traceback
from time import sleep
from time import time


class Status(object):
    """ Saves all status information
    """
    def __init__(self, pyfile):
        self.pyfile = pyfile
        self.type = None
        self.status_queue = None
        self.filename = None
        self.url = None
        self.exists = False
        self.waituntil = 0
        self.want_reconnect = False

    def get_ETA(self):
        return self.pyfile.plugin.req.get_ETA()
    def get_speed(self):
        return self.pyfile.plugin.req.get_speed()
    def kB_left(self):
        return self.pyfile.plugin.req.kB_left()
    def size(self):
        return self.pyfile.plugin.req.dl_size / 1024
    def percent(self):
        if not self.kB_left() == 0 and not self.size() == 0:
            return ((self.size()-self.kB_left()) * 100) / self.size()
        return 0

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
            self.loadedPyFile = self.parent.get_job()
            if self.loadedPyFile:
                try:
                    self.download(self.loadedPyFile)
                except Exception, e:
                    traceback.print_exc()
                    self.loadedPyFile.status.type = "failed"
                finally:
                    self.parent.job_finished(self.loadedPyFile)
            sleep(0.5)
        if self.shutdown:
            sleep(1)
            self.parent.remove_thread(self)

    def download(self, pyfile):
        status = pyfile.status
        pyfile.prepareDownload()

        if not status.exists:
            raise "FileDontExists", "The file was not found on the server." #i know its deprecated, who cares^^

        status.type = "waiting"

        while (time() < status.waituntil):
            if self.parent.init_reconnect() or self.parent.reconnecting:
                status.type = "reconnected"
                status.want_reconnect = False
                return False
            sleep(1)
        if status.filename == "":
            pyfile.get_filename()

        status.want_reconnect = False

        status.type = "downloading"

        pyfile.plugin.proceed(status.url, pyfile.download_folder + "/" + status.filename)

        status.type = "finished"

        #startet downloader
        #urllib.urlretrieve(status.url, pyfile.download_folder + "/" + status.filename, status)
        #self.shutdown = True
