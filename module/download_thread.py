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
    
    @author: mkaay
    @author: spoob
    @author: sebnapi
    @version: v0.3.1
"""

import threading
import traceback
from os.path import join
from time import sleep, time

from module.network.Request import AbortDownload
from module.PullEvents import UpdateEvent

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
        self.plugin = pyfile.modul.__name__
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
            percent = ((self.size()-self.kB_left()) * 100) / self.size()
            return percent if percent < 101 else 0
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

class CaptchaError(Exception):
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
        while not self.shutdown:
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
                except CaptchaError:
                    self.loadedPyFile.status.type = "failed"
                    self.loadedPyFile.status.error = "Can't solve captcha"
                except Exception, e:
                    try:
                        if self.parent.parent.config['general']['debug_mode']:
                            traceback.print_exc()
                        code, msg = e
                        if code == 7:
                            sleep(60)
                        self.parent.parent.logger.info(_("Hoster unvailable, wait 60 seconds"))
                    except Exception, f:
                        self.parent.parent.logger.debug(_("Error getting error code: %s") % f)
                        if self.parent.parent.config['general']['debug_mode']:
                            traceback.print_exc()
                    self.loadedPyFile.status.type = "failed"
                    self.loadedPyFile.status.error = str(e)
                finally:
                    self.parent.job_finished(self.loadedPyFile)
                    self.parent.parent.pullManager.addEvent(UpdateEvent("file", self.loadedPyFile.id, "queue"))
            else:
                sleep(3)
            sleep(0.8)
        if self.shutdown:
            sleep(1)
            self.parent.remove_thread(self)

    def download(self, pyfile):
        status = pyfile.status
        status.type = "starting"
        self.parent.parent.pullManager.addEvent(UpdateEvent("file", pyfile.id, "queue"))
        
        pyfile.init_download()

        pyfile.plugin.prepare(self)
        pyfile.plugin.req.set_timeout(self.parent.parent.config['general']['max_download_time'])
        
        if pyfile.plugin.props["type"] == "container":
            status.type = "decrypting"
        else:
            status.type = "downloading"
        self.parent.parent.pullManager.addEvent(UpdateEvent("file", pyfile.id, "queue"))


        #~ free_file_name = self.get_free_name(status.filename)
        location = join(pyfile.folder, status.filename)
        pyfile.plugin.proceed(status.url, location)
        
        if self.parent.parent.xmlconfig.get("general", "checksum", True):
            status.type = "checking"
            check, code = pyfile.plugin.check_file(location)
            """
            return codes:
            0  - checksum ok
            1  - checksum wrong
            5  - can't get checksum
            10 - not implemented
            20 - unknown error
            """
            if code == 0:
                self.parent.parent.logger.info(_("Checksum ok ('%s')") % status.filename)
            elif code == 1:
                self.parent.parent.logger.info(_("Checksum not matched! ('%s')") % status.filename)
            elif code == 5:
                self.parent.parent.logger.debug(_("Can't get checksum for %s") % status.filename)
            elif code == 10:
                self.parent.parent.logger.debug(_("Checksum not implemented for %s") % status.filename)
            if not check:
                raise Checksum(code, location)

        status.type = "finished"

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
