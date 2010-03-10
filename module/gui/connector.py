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

SERVER_VERSION = "0.3.2"

from time import sleep
from uuid import uuid4 as uuid

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from xmlrpclib import ServerProxy

class connector(QThread):
    def __init__(self):
        """
            init thread
        """
        QThread.__init__(self)
        self.mutex = QMutex()
        self.running = True
        self.proxy = None
        self.addr = None
        self.connectionID = None
        self.errorQueue = []
        self.connect(self, SIGNAL("proxy_error"), self._proxyError)
    
    def setAddr(self, addr):
        """
            set new address
        """
        self.mutex.lock()
        self.addr = addr
        self.mutex.unlock()
    
    def run(self):
        """
            start thread
            (called from thread.start())
        """
        self.canConnect()
        while self.running:
            sleep(1)
            self.getError()
    
    def canConnect(self):
        return self.connectProxy(self.addr)
    
    def stop(self):
        """
            stop thread
        """
        self.running = False
    
    def connectProxy(self, addr):
        """
            connect to remote server
        """
        self.proxy = ServerProxy(addr, allow_none=True)
        try:
            server_version = self.proxy.get_server_version()
            self.connectionID = uuid().hex
        except:
            return False
        if not server_version == SERVER_VERSION:
            self.emit(SIGNAL("error_box"), "server is version %s client accepts version %s" % (server_version, SERVER_VERSION))
            return False
        return True
    
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
    
    def getLinkCollector(self):
        """
            grab links from collector and return the ids
        """
        self.mutex.lock()
        try:
            return self.proxy.get_collector_files()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getLinkCollector", e)
        finally:
            self.mutex.unlock()
    
    def getPackageCollector(self):
        """
            grab packages from collector and return the data
        """
        self.mutex.lock()
        try:
            return self.proxy.get_collector_packages()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getPackageCollector", e)
        finally:
            self.mutex.unlock()
    
    def getLinkInfo(self, id):
        """
            grab file info for the given id and return it
        """
        self.mutex.lock()
        try:
            info = self.proxy.get_file_info(id)
            info["downloading"] = None
            return info
        except Exception, e:
            #self.emit(SIGNAL("proxy_error"), "getLinkInfo", e)
            return None
        finally:
            self.mutex.unlock()
    
    def getPackageInfo(self, id):
        """
            grab package info for the given id and return it
        """
        self.mutex.lock()
        try:
            return self.proxy.get_package_data(id)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getPackageInfo", e)
        finally:
            self.mutex.unlock()
    
    def getPackageQueue(self):
        """
            grab queue return the data
        """
        self.mutex.lock()
        try:
            return self.proxy.get_full_queue()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getPackageQueue", e)
        finally:
            self.mutex.unlock()
    
    def getPackageFiles(self, id):
        """
            grab package files and return ids
        """
        self.mutex.lock()
        try:
            return self.proxy.get_package_files(id)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getPackageFiles", e)
        finally:
            self.mutex.unlock()
    
    def getDownloadQueue(self):
        """
            grab files that are currently downloading and return info
        """
        self.mutex.lock()
        try:
            return self.proxy.status_downloads()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getDownloadQueue", e)
        finally:
            self.mutex.unlock()
    
    def getServerStatus(self):
        """
            return server status
        """
        self.mutex.lock()
        try:
            return self.proxy.status_server()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getServerStatus", e)
        finally:
            self.mutex.unlock()
    
    def addURLs(self, links):
        """
            add links to collector
        """
        self.mutex.lock()
        try:
            self.proxy.add_urls(links)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "addURLs", e)
        finally:
            self.mutex.unlock()
    
    def togglePause(self):
        """
            toogle pause
        """
        self.mutex.lock()
        try:
            return self.proxy.toggle_pause()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "togglePause", e)
        finally:
            self.mutex.unlock()
    
    def setPause(self, pause):
        """
            set pause
        """
        self.mutex.lock()
        try:
            if pause:
                self.proxy.pause_server()
            else:
                self.proxy.unpause_server()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "setPause", e)
        finally:
            self.mutex.unlock()
    
    def newPackage(self, name):
        """
            create a new package and return id
        """
        self.mutex.lock()
        try:
            return self.proxy.new_package(name)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "newPackage", e)
        finally:
            self.mutex.unlock()
    
    def addFileToPackage(self, fileid, packid):
        """
            add a file from collector to package
        """
        self.mutex.lock()
        try:
            self.proxy.move_file_2_package(fileid, packid)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "addFileToPackage", e)
        finally:
            self.mutex.unlock()
    
    def pushPackageToQueue(self, packid):
        """
            push a package to queue
        """
        self.mutex.lock()
        try:
            self.proxy.push_package_2_queue(packid)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "pushPackageToQueue", e)
        finally:
            self.mutex.unlock()
    
    def restartPackage(self, packid):
        """
            restart a package
        """
        self.mutex.lock()
        try:
            self.proxy.restart_package(packid)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "restartPackage", e)
        finally:
            self.mutex.unlock()
    
    def restartFile(self, fileid):
        """
            restart a file
        """
        self.mutex.lock()
        try:
            self.proxy.restart_file(fileid)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "restartFile", e)
        finally:
            self.mutex.unlock()
    
    def removePackage(self, packid):
        """
            remove a package
        """
        self.mutex.lock()
        try:
            self.proxy.del_packages([packid,])
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "removePackage", e)
        finally:
            self.mutex.unlock()
    
    def removeFile(self, fileid):
        """
            remove a file
        """
        self.mutex.lock()
        try:
            self.proxy.del_links([fileid,])
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "removeFile", e)
        finally:
            self.mutex.unlock()
    
    def uploadContainer(self, filename, type, content):
        """
            upload a container
        """
        self.mutex.lock()
        try:
            self.proxy.upload_container(filename, type, content)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "uploadContainer", e)
        finally:
            self.mutex.unlock()
    
    def getLog(self, offset):
        """
            get log
        """
        self.mutex.lock()
        try:
            return self.proxy.get_log(offset)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getLog", e)
        finally:
            self.mutex.unlock()
    
    def stopAllDownloads(self):
        """
            get log
        """
        self.mutex.lock()
        try:
            self.proxy.pause_server()
            self.proxy.stop_downloads()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "stopAllDownloads", e)
        finally:
            self.mutex.unlock()
    
    def updateAvailable(self):
        """
            update available
        """
        self.mutex.lock()
        try:
            return self.proxy.update_available()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "updateAvailable", e)
        finally:
            self.mutex.unlock()
    
    def setPackageName(self, pid, name):
        """
            set new package name
        """
        self.mutex.lock()
        try:
            return self.proxy.set_package_name(pid, name)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "setPackageName", e)
        finally:
            self.mutex.unlock()
    
    def pullOutPackage(self, pid):
        """
            pull out package
        """
        self.mutex.lock()
        try:
            return self.proxy.pull_out_package(pid)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "pullOutPackage", e)
        finally:
            self.mutex.unlock()
    
    def captchaWaiting(self):
        """
            is the a captcha waiting?
        """
        self.mutex.lock()
        try:
            return self.proxy.is_captcha_waiting()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "captchaWaiting", e)
        finally:
            self.mutex.unlock()
    
    def getCaptcha(self):
        """
            get captcha
        """
        self.mutex.lock()
        try:
            return self.proxy.get_captcha_task()
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getCaptcha", e)
        finally:
            self.mutex.unlock()
    
    def setCaptchaResult(self, cid, result):
        """
            get captcha
        """
        self.mutex.lock()
        try:
            return self.proxy.set_captcha_result(cid, result)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "setCaptchaResult", e)
        finally:
            self.mutex.unlock()
    
    def getEvents(self):
        """
            get events
        """
        self.mutex.lock()
        try:
            return self.proxy.get_events(self.connectionID)
        except Exception, e:
            self.emit(SIGNAL("proxy_error"), "getEvents", e)
        finally:
            self.mutex.unlock()
        
