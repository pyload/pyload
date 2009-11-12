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
from time import sleep, time

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

class Checksum(Exception):
    def __init__(self, code, local_file):
        self.code = code
        self.file = local_file
    
    def getCode(self):
        return self.code
    
    def getFile(self):
        return self.file

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
                except Checksum, e:
                    self.loadedPyFile.status.type = "failed"
                    self.loadedPyFile.status.error = "Checksum error: %d" % e.getCode()
                    f = open("%s.info" % e.getFile(), "w")
                    f.write("Checksum not matched!")
                    f.close()
                except Exception, e:

                    try:
                        if self.parent.parent.config['general']['debug_mode']:
                            traceback.print_exc()
                        code, msg = e
                        if code == 7:
                            sleep(60)
                        self.parent.parent.logger.info("Hoster unvailable, wait 60 seconds")
                    except Exception, f:
                        self.parent.parent.logger.debug("Error getting error code: "+ str(f))
                        if self.parent.parent.config['general']['debug_mode']:
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
        
        local_file = pyfile.download_folder + "/" + status.filename
        pyfile.plugin.proceed(status.url, local_file)

        status.type = "checking"
        
        check, code = pyfile.plugin.check_file(local_file)
        """
        return codes:
        0  - checksum ok
        1  - checksum wrong
        5  - can't get checksum
        10 - not implemented
        20 - unknown error
        """
        if code == 0:
        	self.parent.parent.logger.info("Checksum ok ('%s')" % status.filename)
        elif code == 1:
        	self.parent.parent.logger.info("Checksum not matched! ('%s')" % status.filename)
        elif code == 5:
        	self.parent.parent.logger.debug("Can't get checksum for %s" % status.filename)
        elif code == 10:
        	self.parent.parent.logger.debug("Checksum not implemented for %s" % status.filename)
        if not check:
        	raise Checksum(code, local_file)
        #print "checksum check returned: %s, %s" % (check, code)
        
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
            if pyfile.plugin.req.abort:
                raise AbortDownload
            sleep(1)
        pyfile.status.want_reconnect = False
        return True

