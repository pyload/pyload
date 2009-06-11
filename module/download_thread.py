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
        self.waituntil = None
        self.want_reconnect = False

    def get_ETA(self):
        return self.pyfile.plugin.req.get_ETA()
    def get_speed(self):
        return self.pyfile.plugin.req.get_speed()
    def kB_left(self):
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
            if self.parent.py_load_files:
                self.loadedPyFile = self.parent.get_job()
                if self.loadedPyFile:
                    try:
                        self.download(self.loadedPyFile)
                    except Exception, e:
                        print "Error:", e #catch up all error here
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
            raise "FileDontExists" #i know its deprecated, who cares^^

        status.type = "waiting"

        while (time() < status.waituntil):
            if self.parent.init_reconnect() or self.parent.reconnecting:
                status.type = "reconnected"
                status.want_reconnect = False
                return False
            sleep(1)

        status.want_reconnect = False

        status.type = "downloading"

        pyfile.plugin.proceed(status.url, pyfile.download_folder + "/" + status.filename)

        status.type = "finished"

        #startet downloader
        #urllib.urlretrieve(status.url, pyfile.download_folder + "/" + status.filename, status)
        #self.shutdown = True