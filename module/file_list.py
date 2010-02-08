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
    @author: RaNaN
    @version: v0.3.1
    @list-version: v4
"""

LIST_VERSION = 4

from threading import RLock
from download_thread import Status
import cPickle
import re
import module.Plugin
from operator import concat
from operator import attrgetter
from os import sep
from time import sleep

from module.PullEvents import UpdateEvent, RemoveEvent, InsertEvent

class NoSuchElementException(Exception):
    pass

class File_List(object):
    def __init__(self, core):
        self.core = core
        self.lock = RLock()
        self.download_folder = self.core.config['general']['download_folder']
        self.collector = self.pyLoadCollector(self)
        self.packager = self.pyLoadPackager(self)
        
        self.data = {
            "version": LIST_VERSION,
            "queue": [],
            "packages": [],
            "collector": []
        }
        self.load()
        
    def load(self):
        self.lock.acquire()
        try:
            pkl_file = open('module' + sep + 'links.pkl', 'rb')
            obj = cPickle.load(pkl_file)
        except:
            obj = False
        if obj != False and obj['version'] == LIST_VERSION:
            packages = []
            queue = []
            collector = []
            for n, pd in enumerate(obj["packages"]):
                p = PyLoadPackage()
                pd.get(p, self)
                packages.append(p)
            for pd in obj["queue"]:
                p = PyLoadPackage()
                pd.get(p, self)
                queue.append(p)
            for fd in obj["collector"]:
                f = PyLoadFile("", self)
                fd.get(f)
                collector.append(f)
            obj["packages"] = packages
            obj["queue"] = queue
            obj["collector"] = collector
            self.data = obj
        self.lock.release()
        
        if len(self.data["collector"]) > 0:
            self.core.logger.info(_("Found %s links in linkcollector") % len(self.data["collector"]))
        if len(self.data["packages"]) > 0:
            self.core.logger.info(_("Found %s unqueued packages") % len(self.data["packages"]))
        if len(self.data["queue"]) > 0:
            self.core.logger.info(_("Added %s packages to queue") % len(self.data["queue"]))
    
    def save(self):
        self.lock.acquire()
        
        pdata = {
            "version": LIST_VERSION,
            "queue": [],
            "packages": [],
            "collector": []
        }

        pdata["packages"] = [PyLoadPackageData().set(x) for x in self.data["packages"]]
        pdata["queue"] = [PyLoadPackageData().set(x) for x in self.data["queue"]]
        pdata["collector"] = [PyLoadFileData().set(x) for x in self.data["collector"]]
        
        output = open('module' + sep + 'links.pkl', 'wb')
        cPickle.dump(pdata, output, -1)
        
        self.lock.release()
    
    def queueEmpty(self):
        return (self.data["queue"] == [])
    
    def getDownloadList(self, occ):
        """
            for thread_list only, returns all elements that are suitable for downloadthread
        """
        files = []
        files += [[x for x in p.files if x.status.type == None and x.plugin.props['type'] == "container" and not x.active] for p in self.data["queue"] + self.data["packages"]]
        files += [[x for x in p.files if (x.status.type == None or x.status.type == "reconnected") and not x.active and not x.modul.__name__ in occ] for p in self.data["queue"]]

        return reduce(concat, files, [])
    
    def getAllFiles(self):
        
        files = []
        for pypack in self.data["queue"] + self.data["packages"]:
            files += pypack.files
        return files
    
    def countDownloads(self):
        """ simply return len of all files in all packages(which have no type) in queue and collector"""
        return len(reduce(concat, [[x for x in p.files if x.status.type == None] for p in self.data["queue"] + self.data["packages"]], []))
    
    def getFileInfo(self, id):
        try:
            n, pyfile = self.collector._getFileFromID(id)
        except NoSuchElementException:
            key, n, pyfile, pypack, pid = self.packager._getFileFromID(id)
        info = {}
        info["id"] = pyfile.id
        info["url"] = pyfile.url
        info["folder"] = pyfile.folder
        info["filename"] = pyfile.status.filename
        info["status_type"] = pyfile.status.type
        info["status_url"] = pyfile.status.url
        info["status_filename"] = pyfile.status.filename
        info["status_error"] = pyfile.status.error
        info["size"] = pyfile.status.size()
        info["active"] = pyfile.active
        info["plugin"] = pyfile.plugin.props['name']
        try:
            info["package"] = pypack.data["id"]
        except:
            pass
        return info

    def continueAborted(self):
        [[self.packager.resetFileStatus(x.id) for x in p.files if x.status.type == "aborted"] for p in self.data["queue"]]
    
    class pyLoadCollector():
        def __init__(collector, file_list):
            collector.file_list = file_list
        
        def _getFileFromID(collector, id):
            """
                returns PyLoadFile instance and position in collector with given id
            """
            for n, pyfile in enumerate(collector.file_list.data["collector"]):
                if pyfile.id == id:
                    return (n, pyfile)
            raise NoSuchElementException()
        
        def _getFreeID(collector):
            """
                returns a free id
            """
            ids = []
            for pypack in (collector.file_list.data["packages"] + collector.file_list.data["queue"]):
                for pyf in pypack.files:
                    ids.append(pyf.id)
            ids += map(attrgetter("id"), collector.file_list.data["collector"])
            id = 1
            while id in ids:
                id += 1
            return id
        
        def getFile(collector, id):
            """
                returns PyLoadFile instance from given id
            """
            return collector._getFileFromID(id)[1]
            
        def popFile(collector, id):
            """
                returns PyLoadFile instance given id and remove it from the collector
            """
            collector.file_list.lock.acquire()
            try:
                n, pyfile = collector._getFileFromID(id)
                del collector.file_list.data["collector"][n]
                collector.file_list.core.pullManager.addEvent(RemoveEvent("file", id, "collector"))
            except Exception, e:
                raise Exception, e
            else:
                return pyfile
            finally:
                collector.file_list.lock.release()
        
        def addLink(collector, url):
            """
                appends a new PyLoadFile instance to the end of the collector
            """
            pyfile = PyLoadFile(url, collector.file_list)
            pyfile.id = collector._getFreeID()
            pyfile.folder =  collector.file_list.download_folder
            collector.file_list.lock.acquire()
            collector.file_list.data["collector"].append(pyfile)
            collector.file_list.lock.release()
            collector.file_list.core.pullManager.addEvent(InsertEvent("file", pyfile.id, -2, "collector"))
            return pyfile.id
        
        def removeFile(collector, id):
            """
                removes PyLoadFile instance with the given id from collector
            """
            collector.popFile(id)
            collector.file_list.core.pullManager.addEvent(RemoveEvent("file", id, "collector"))
        
        def replaceFile(collector, newpyfile):
            """
                replaces PyLoadFile instance with the given PyLoadFile instance at the given id
            """
            collector.file_list.lock.acquire()
            try:
                n, pyfile = collector._getFileFromID(newpyfile.id)
                collector.file_list.data["collector"][n] = newpyfile
                collector.file_list.core.pullManager.addEvent(UpdateEvent("file", newpyfile.id, "collector"))
            finally:
                collector.file_list.lock.release()
        
    class pyLoadPackager():
        def __init__(packager, file_list):
            packager.file_list = file_list
        
        def _getFreeID(packager):
            """
                returns a free id
            """
            ids = [ pypack.data["id"] for pypack in packager.file_list.data["packages"] + packager.file_list.data["queue"]]
            
            id = 1
            while id in ids:
                id += 1
            return id
        
        def _getPackageFromID(packager, id):
            """
                returns PyLoadPackage instance and position with given id
            """
            for n, pypack in enumerate(packager.file_list.data["packages"]):
                if pypack.data["id"] == id:
                    return ("packages", n, pypack)
            for n, pypack in enumerate(packager.file_list.data["queue"]):
                if pypack.data["id"] == id:
                    return ("queue", n, pypack)
            raise NoSuchElementException()
        
        def _getFileFromID(packager, id):
            """
                returns PyLoadFile instance and position with given id
            """
            for n, pypack in enumerate(packager.file_list.data["packages"]):
                for pyfile in pypack.files:
                    if pyfile.id == id:
                        return ("packages", n, pyfile, pypack, pypack.data["id"])
            for n, pypack in enumerate(packager.file_list.data["queue"]):
                for pyfile in pypack.files:
                    if pyfile.id == id:
                        return ("queue", n, pyfile, pypack, pypack.data["id"])
            raise NoSuchElementException()
        
        def addNewPackage(packager, package_name=None):
            pypack = PyLoadPackage()
            pypack.data["id"] = packager._getFreeID()
            if package_name is not None:
                pypack.data["package_name"] = package_name
            packager.file_list.data["packages"].append(pypack)
            packager.file_list.core.pullManager.addEvent(InsertEvent("pack", pypack.data["id"], -2, "packages"))
            return pypack.data["id"]
        
        def removePackage(packager, id):
            packager.file_list.lock.acquire()
            try:
                key, n, pypack = packager._getPackageFromID(id)
                for pyfile in pypack.files:
                    pyfile.plugin.req.abort = True
                sleep(0.1)
                del packager.file_list.data[key][n]
                packager.file_list.core.pullManager.addEvent(RemoveEvent("pack", id, key))
            finally:
                packager.file_list.lock.release()
        
        def removeFile(packager, id):
            """
                removes PyLoadFile instance with the given id from package
            """
            packager.file_list.lock.acquire()
            try:
                key, n, pyfile, pypack, pid = packager._getFileFromID(id)
                pyfile.plugin.req.abort = True
                sleep(0.1)
                packager.removeFileFromPackage(id, pid)
                if not pypack.files:
                    packager.removePackage(pid)
            finally:
                packager.file_list.lock.release()
        
        def pushPackage2Queue(packager, id):
            packager.file_list.lock.acquire()
            try:
                key, n, pypack = packager._getPackageFromID(id)
                if key == "packages":
                    del packager.file_list.data["packages"][n]
                    packager.file_list.data["queue"].append(pypack)
                    packager.file_list.core.pullManager.addEvent(RemoveEvent("pack", id, "packages"))
                    packager.file_list.core.pullManager.addEvent(InsertEvent("pack", id, -2, "queue"))
            finally:
                packager.file_list.lock.release()
        
        def pullOutPackage(packager, id):
            packager.file_list.lock.acquire()
            try:
                key, n, pypack = packager._getPackageFromID(id)
                if key == "queue":
                    del packager.file_list.data["queue"][n]
                    packager.file_list.data["packages"].append(pypack)
                    packager.file_list.core.pullManager.addEvent(RemoveEvent("pack", id, "queue"))
                    packager.file_list.core.pullManager.addEvent(InsertEvent("pack", id, -2, "packages"))
            finally:
                packager.file_list.lock.release()
        
        def setPackageData(packager, id, package_name=None, folder=None):
            packager.file_list.lock.acquire()
            try:
                key, n, pypack = packager._getPackageFromID(id)
                if package_name is not None:
                    pypack.data["package_name"] = package_name
                if folder is not None:
                    pypack.data["folder"] = folder
                packager.file_list.data[key][n] = pypack
                packager.file_list.core.pullManager.addEvent(UpdateEvent("pack", id, key))
            finally:
                packager.file_list.lock.release()
        
        def getPackageData(packager, id):
            key, n, pypack = packager._getPackageFromID(id)
            return pypack.data
        
        def getPackageFiles(packager, id):
            key, n, pypack = packager._getPackageFromID(id)
            ids = map(attrgetter("id"), pypack.files)
            
            return ids
        
        def addFileToPackage(packager, id, pyfile):
            key, n, pypack = packager._getPackageFromID(id)
            pyfile.package = pypack
            pypack.files.append(pyfile)
            packager.file_list.data[key][n] = pypack
            packager.file_list.core.pullManager.addEvent(InsertEvent("file", pyfile.id, -2, key))
        
        def resetFileStatus(packager, fileid):
            packager.file_list.lock.acquire()
            try:
                key, n, pyfile, pypack, pid = packager._getFileFromID(fileid)
                pyfile.init()
                pyfile.status.type = None
                packager.file_list.core.pullManager.addEvent(UpdateEvent("file", fileid, key))
            finally:
                packager.file_list.lock.release()
        
        def abortFile(packager, fileid):
            packager.file_list.lock.acquire()
            try:
                key, n, pyfile, pypack, pid = packager._getFileFromID(fileid)
                pyfile.plugin.req.abort = True
                packager.file_list.core.pullManager.addEvent(UpdateEvent("file", fileid, key))
            finally:
                packager.file_list.lock.release()
       
        def removeFileFromPackage(packager, id, pid):
            key, n, pypack = packager._getPackageFromID(pid)
            for k, pyfile in enumerate(pypack.files):
                if id == pyfile.id:
                    del pypack.files[k]
                    packager.file_list.core.pullManager.addEvent(RemoveEvent("file", pyfile.id, key))
                    if not pypack.files:
                        packager.removePackage(pid)
                    return True
            raise NoSuchElementException()

class PyLoadPackage():
    def __init__(self):
        self.files = []
        self.data = {
            "id": None,
            "package_name": "new_package",
            "folder": ""
        }

class PyLoadFile():
    def __init__(self, url, file_list):
        self.id = None
        self.url = url
        self.folder = ""
        self.file_list = file_list
        self.core = file_list.core
        self.package = None
        self.filename = "n/a"
        self.init()
    
    def init(self):
        self.active = False
        pluginName = self._get_my_plugin()
        if pluginName:
            for dir in ["hoster", "decrypter", "container"]:
                try:
                    self.modul = __import__("%s.%s" % (dir, pluginName), globals(), locals(), [pluginName], -1)
                except ImportError:
                    pass
            pluginClass = getattr(self.modul, pluginName)
        else:
            self.modul = module.Plugin
            pluginClass = module.Plugin.Plugin
        self.plugin = pluginClass(self)
        self.status = Status(self)
        self.status.filename = self.url
    
    def _get_my_plugin(self):
        for plugin, plugin_pattern in self.core.plugins_avaible.items():
            if re.match(plugin_pattern, self.url) != None:
                return plugin

    def init_download(self):
        if self.core.config['proxy']['activated']:
            self.plugin.req.add_proxy(self.core.config['proxy']['protocol'], self.core.config['proxy']['adress'])

class PyLoadFileData():
    def __init__(self):
        self.id = None
        self.url = None
        self.folder = None
        self.pack_id = None
        self.filename = None
        self.status_type = None
        self.status_url = None

    def set(self, pyfile):
        self.id = pyfile.id
        self.url = pyfile.url
        self.folder = pyfile.folder
        self.parsePackage(pyfile.package)
        self.filename = pyfile.filename
        self.status_type = pyfile.status.type
        self.status_url = pyfile.status.url
        self.status_filename = pyfile.status.filename
        self.status_error = pyfile.status.error

        return self

    def get(self, pyfile):
        pyfile.id = self.id
        pyfile.url = self.url
        pyfile.folder = self.folder
        pyfile.filename = self.filename
        pyfile.status.type = self.status_type
        pyfile.status.url = self.status_url
        pyfile.status.filename = self.status_filename
        pyfile.status.error = self.status_error
    
    def parsePackage(self, pack):
        if pack:
            self.pack_id = pack.data["id"]

class PyLoadPackageData():
    def __init__(self):
        self.data = None
        self.files = []

    def set(self, pypack):
        self.data = pypack.data
        self.files = [PyLoadFileData().set(x) for x in pypack.files]
        return self
        
    def get(self, pypack, fl):
        pypack.data = self.data
        for fdata in self.files:
            pyfile = PyLoadFile(fdata.url, fl)
            fdata.get(pyfile)
            pyfile.package = pypack
            pypack.files.append(pyfile)
