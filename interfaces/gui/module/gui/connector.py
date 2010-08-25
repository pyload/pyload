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
"""

SERVER_VERSION = "0.4.1-dev"

from time import sleep
from uuid import uuid4 as uuid

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from xmlrpclib import ServerProxy
import socket

class Connector(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.mutex = QMutex()
        self.addr = None
        self.errorQueue = []
        self.connectionID = None
        self.running = True
        self.proxy = self.Dummy()
    
    def setAddr(self, addr):
        """
            set new address
        """
        self.mutex.lock()
        self.addr = addr
        self.mutex.unlock()
    
    def connectProxy(self):
        self.proxy = DispatchRPC(self.mutex, ServerProxy(self.addr, allow_none=True, verbose=False))
        self.connect(self.proxy, SIGNAL("proxy_error"), self._proxyError)
        self.connect(self.proxy, SIGNAL("connectionLost"), self, SIGNAL("connectionLost"))
        try:
            server_version = self.proxy.get_server_version()
            self.connectionID = uuid().hex
        except:
            return False
        if not server_version:
            return False
        elif not server_version == SERVER_VERSION:
            self.emit(SIGNAL("error_box"), "server is version %s client accepts version %s" % (server_version, SERVER_VERSION))
            return False
        return True
    
    def canConnect(self):
        return self.connectProxy()
    
    def _proxyError(self, func, e):
        """
            formats proxy error msg
        """
        msg = "proxy error in '%s':\n%s" % (func, e)
        self.errorQueue.append(msg)
    
    def getError(self):
        self.mutex.lock()
        if len(self.errorQueue) > 0:
            err = self.errorQueue.pop()
            print err
            self.emit(SIGNAL("error_box"), err)
        self.mutex.unlock()
    
    def stop(self):
        """
            stop thread
        """
        self.running = False
    
    def run(self):
        """
            start thread
            (called from thread.start())
        """
        self.canConnect()
        while self.running:
            sleep(1)
            self.getError()
    
    class Dummy(object):
        def __getattr__(self, attr):
            def dummy(*args, **kwargs):
                return None
            return dummy
    
    def getPackageCollector(self):
        """
            grab packages from collector and return the data
        """
        return self.proxy.get_collector()
    
    def getLinkInfo(self, id):
        """
            grab file info for the given id and return it
        """
        w = self.proxy.get_file_info
        w.error = False
        info = w(id)
        if not info: return None
        info["downloading"] = None
        return info
    
    def getPackageInfo(self, id):
        """
            grab package info for the given id and return it
        """
        w = self.proxy.get_package_data
        w.error = False
        return w(id)
    
    def getPackageQueue(self):
        """
            grab queue return the data
        """
        return self.proxy.get_queue()
    
    def getPackageFiles(self, id):
        """
            grab package files and return ids
        """
        return self.proxy.get_package_files(id)
    
    def getDownloadQueue(self):
        """
            grab files that are currently downloading and return info
        """
        return self.proxy.status_downloads()
    
    def getServerStatus(self):
        """
            return server status
        """
        return self.proxy.status_server()
    
    def addURLs(self, links):
        """
            add links to collector
        """
        self.proxy.add_urls(links)
    
    def togglePause(self):
        """
            toogle pause
        """
        return self.proxy.toggle_pause()
    
    def setPause(self, pause):
        """
            set pause
        """
        if pause:
            self.proxy.pause_server()
        else:
            self.proxy.unpause_server()
    
    def newPackage(self, name):
        """
            create a new package and return id
        """
        return self.proxy.new_package(name)
    
    def addFileToPackage(self, fileid, packid):
        """
            add a file from collector to package
        """
        self.proxy.move_file_2_package(fileid, packid)
    
    def pushPackageToQueue(self, packid):
        """
            push a package to queue
        """
        self.proxy.push_package_2_queue(packid)
    
    def restartPackage(self, packid):
        """
            restart a package
        """
        self.proxy.restart_package(packid)
    
    def restartFile(self, fileid):
        """
            restart a file
        """
        self.proxy.restart_file(fileid)
    
    def removePackage(self, packid):
        """
            remove a package
        """
        self.proxy.del_packages([packid,])
    
    def removeFile(self, fileid):
        """
            remove a file
        """
        self.proxy.del_links([fileid,])
    
    def uploadContainer(self, filename, type, content):
        """
            upload a container
        """
        self.proxy.upload_container(filename, type, content)
    
    def getLog(self, offset):
        """
            get log
        """
        return self.proxy.get_log(offset)
    
    def stopAllDownloads(self):
        """
            get log
        """
        self.proxy.pause_server()
        self.proxy.stop_downloads()
    
    def updateAvailable(self):
        """
            update available
        """
        return self.proxy.update_available()
    
    def setPackageName(self, pid, name):
        """
            set new package name
        """
        return self.proxy.set_package_name(pid, name)
    
    def pullOutPackage(self, pid):
        """
            pull out package
        """
        return self.proxy.pull_out_package(pid)
    
    def captchaWaiting(self):
        """
            is the a captcha waiting?
        """
        return self.proxy.is_captcha_waiting()
    
    def getCaptcha(self):
        """
            get captcha
        """
        return self.proxy.get_captcha_task()
    
    def setCaptchaResult(self, cid, result):
        """
            get captcha
        """
        return self.proxy.set_captcha_result(cid, result)
    
    def getCaptchaStatus(self, cid):
        """
            get captcha status
        """
        return self.proxy.get_task_status(cid)
    
    def getEvents(self):
        """
            get events
        """
        return self.proxy.get_events(self.connectionID)

class DispatchRPC(QObject):
    def __init__(self, mutex, server):
        QObject.__init__(self)
        self.mutex = mutex
        self.server = server
    
    def __getattr__(self, attr):
        self.mutex.lock()
        self.fname = attr
        f = self.Wrapper(getattr(self.server, attr), self.mutex, self)
        return f
    
    class Wrapper(object):
        def __init__(self, f, mutex, dispatcher):
            self.f = f
            self.mutex = mutex
            self.dispatcher = dispatcher
            self.error = True
        
        def __call__(self, *args, **kwargs):
            try:
                return self.f(*args, **kwargs)
            except socket.error:
                self.dispatcher.emit(SIGNAL("connectionLost"))
            except Exception, e:
                if self.error:
                    self.dispatcher.emit(SIGNAL("proxy_error"), self.dispatcher.fname, e)
            finally:
                self.mutex.unlock()
