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

SERVER_VERSION = "0.3"

from time import sleep

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
        self.connectProxy(self.addr)
        while self.running:
            sleep(1)
            self.getError()
    
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
        server_version = self.proxy.get_server_version()
        if not server_version == SERVER_VERSION:
            self.emit(SIGNAL("error_box"), "server is version %s client accepts version %s" % (server_version, SERVER_VERSION))
    
    def _proxyError(self, func):
        """
            formats proxy error msg
        """
        msg = "proxy error in '%s'" % (func,)
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
        except:
            self.emit(SIGNAL("proxy_error"), "getLinkCollector")
        finally:
            self.mutex.unlock()
    
    def getPackageCollector(self):
        """
            grab packages from collector and return the data
        """
        self.mutex.lock()
        try:
            return self.proxy.get_collector_packages()
        except:
            self.emit(SIGNAL("proxy_error"), "getPackageCollector")
        finally:
            self.mutex.unlock()
    
    def getLinkInfo(self, id):
        """
            grab file info for the given id and return it
        """
        self.mutex.lock()
        try:
            return self.proxy.get_file_info(id)
        except:
            self.emit(SIGNAL("proxy_error"), "getLinkInfo")
        finally:
            self.mutex.unlock()
    
    def getPackageInfo(self, id):
        """
            grab package info for the given id and return it
        """
        self.mutex.lock()
        try:
            return self.proxy.get_package_data(id)
        except:
            self.emit(SIGNAL("proxy_error"), "getPackageInfo")
        finally:
            self.mutex.unlock()
    
    def getPackageQueue(self):
        """
            grab queue return the data
        """
        self.mutex.lock()
        try:
            return self.proxy.get_queue()
        except:
            self.emit(SIGNAL("proxy_error"), "getPackageQueue")
        finally:
            self.mutex.unlock()
    
    def getPackageFiles(self, id):
        """
            grab package files and return ids
        """
        self.mutex.lock()
        try:
            return self.proxy.get_package_files(id)
        except:
            self.emit(SIGNAL("proxy_error"), "getPackageFiles")
        finally:
            self.mutex.unlock()
    
    def getDownloadQueue(self):
        """
            grab files that are currently downloading and return info
        """
        self.mutex.lock()
        try:
            return self.proxy.status_downloads()
        except:
            self.emit(SIGNAL("proxy_error"), "getDownloadQueue")
        finally:
            self.mutex.unlock()
    
    def getServerStatus(self):
        """
            return server status
        """
        self.mutex.lock()
        try:
            return self.proxy.status_server()
        except:
            self.emit(SIGNAL("proxy_error"), "getServerStatus")
        finally:
            self.mutex.unlock()
    
    def addURLs(self, links):
        """
            add links to collector
        """
        self.mutex.lock()
        try:
            self.proxy.add_urls(links)
        except:
            self.emit(SIGNAL("proxy_error"), "addURLs")
        finally:
            self.mutex.unlock()
    
    def togglePause(self):
        """
            toogle pause
        """
        self.mutex.lock()
        try:
            return self.proxy.toggle_pause()
        except:
            self.emit(SIGNAL("proxy_error"), "togglePause")
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
        except:
            self.emit(SIGNAL("proxy_error"), "setPause")
        finally:
            self.mutex.unlock()
    
    def newPackage(self, name):
        """
            create a new package and return id
        """
        self.mutex.lock()
        try:
            return self.proxy.new_package(name)
        except:
            self.emit(SIGNAL("proxy_error"), "newPackage")
        finally:
            self.mutex.unlock()
    
    def addFileToPackage(self, fileid, packid):
        """
            add a file from collector to package
        """
        self.mutex.lock()
        try:
            self.proxy.move_file_2_package(fileid, packid)
        except:
            self.emit(SIGNAL("proxy_error"), "addFileToPackage")
        finally:
            self.mutex.unlock()
    
    def pushPackageToQueue(self, packid):
        """
            push a package to queue
        """
        self.mutex.lock()
        try:
            self.proxy.push_package_2_queue(packid)
        except:
            self.emit(SIGNAL("proxy_error"), "pushPackageToQueue")
        finally:
            self.mutex.unlock()
    
    def restartPackage(self, packid):
        """
            restart a package
        """
        self.mutex.lock()
        try:
            self.proxy.restart_package(packid)
        except:
            self.emit(SIGNAL("proxy_error"), "restartPackage")
        finally:
            self.mutex.unlock()
    
    def restartFile(self, fileid):
        """
            restart a file
        """
        self.mutex.lock()
        try:
            self.proxy.restart_file(fileid)
        except:
            self.emit(SIGNAL("proxy_error"), "restartFile")
        finally:
            self.mutex.unlock()
    
    def removePackage(self, packid):
        """
            remove a package
        """
        self.mutex.lock()
        try:
            self.proxy.del_packages([packid,])
        except:
            self.emit(SIGNAL("proxy_error"), "removePackage")
        finally:
            self.mutex.unlock()
    
    def removeFile(self, fileid):
        """
            remove a file
        """
        self.mutex.lock()
        try:
            self.proxy.del_links([fileid,])
        except:
            self.emit(SIGNAL("proxy_error"), "removeFile")
        finally:
            self.mutex.unlock()
    
    def uploadContainer(self, filename, type, content):
        """
            upload a container
        """
        self.mutex.lock()
        try:
            self.proxy.upload_container(filename, type, content)
        except:
            self.emit(SIGNAL("proxy_error"), "uploadContainer")
        finally:
            self.mutex.unlock()
        
