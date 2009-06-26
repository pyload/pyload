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

from module.network.Request import AbortDownload

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
        self.error = ""

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

class Reconnect(Exception):
    pass

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
                except AbortDownload:
                    self.loadedPyFile.plugin.req.abort = False
                    self.loadedPyFile.status.type = "aborted"
                except Reconnect:
                    pass
                except Exception, e:
                    traceback.print_exc()
                    self.loadedPyFile.status.type = "failed"
                    self.loadedPyFile.status.error = str(e)
                finally:
                    self.parent.job_finished(self.loadedPyFile)
            sleep(0.5)
        if self.shutdown:
            sleep(1)
            self.parent.remove_thread(self)

    def download(self, pyfile):
        status = pyfile.status
        
        pyfile.init_download()
    
        pyfile.plugin.prepare(self)

        if status.url == "":
            status.url = pyfile.plugin.get_file_url()

        status.type = "downloading"

        pyfile.plugin.proceed(status.url, pyfile.download_folder + "/" + status.filename)

        status.type = "finished"

        #startet downloader
        #urllib.urlretrieve(status.url, pyfile.download_folder + "/" + status.filename, status)
        #self.shutdown = True

    def wait(self, pyfile):
        pyfile.status.type = "waiting"
        while (time() < pyfile.status.waituntil):
            if self.parent.init_reconnect() or self.parent.reconnecting:
                pyfile.status.type = "reconnected"
                pyfile.status.want_reconnect = False
                raise Reconnect
            sleep(1)
        pyfile.status.want_reconnect = False
        return True

