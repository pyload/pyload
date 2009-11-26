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
    @version: v0.3
    @list-version: v4
"""

LIST_VERSION = 4

from threading import RLock
from download_thread import Status
import cPickle
import re
import module.Plugin

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
        
    def load(self):
        self.lock.acquire()
        try:
            pkl_file = open('links.pkl', 'rb')
            obj = cPickle.load(pkl_file)
        except:
            obj = False
        if obj['version'] == LIST_VERSION and obj:
            self.data = obj
        self.lock.release()
        
        if len(self.data["collector"]) > 0:
            self.core.logger.info("Found %s links in linkcollector" % len(self.data["collector"]))
        if len(self.data["packages"]) > 0:
            self.core.logger.info("Found %s unqueued packages" % len(self.data["packages"]))
        if len(self.data["queue"]) > 0:
            self.core.logger.info("Added %s packages to queue" % len(self.data["queue"]))
    
    def save(self):
        self.lock.acquire()

        output = open('links.pkl', 'wb')
        cPickle.dump(self.data, output, -1)
        
        self.lock.release()
    
    def queueEmpty(self):
        return (self.data["queue"] == [])
    
    def getDownloadList(self):
        """
            for thread_list only
        """
        files = []
        for pypack in self.data["queue"]:
            for pyfile in pypack.files:
                if pyfile.status.type == "reconnected" or pyfile.status.type == None:
                    files.append(pyfile)
        return files
    
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
            for pyfile in collector.file_list.data["collector"]:
                ids.append(pyfile.id)
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
                collector.file_list.lock.release()
            except:
                collector.file_list.lock.release()
            else:
                return pyfile
        
        def addLink(collector, url):
            """
                appends a new PyLoadFile instance to the end of the collector
            """
            pyfile = PyLoadFile(url)
            pyfile.id = collector._getFreeID()
            pyfile.download_folder =  collector.file_list.download_folder
            collector.file_list.lock.acquire()
            collector.file_list.data["collector"].append(pyfile)
            collector.file_list.lock.release()
            return pyfile.id
        
        def removeFile(collector, id):
            """
                removes PyLoadFile instance with the given id from collector
            """
            collector.popFile(id)
        
        def replaceFile(collector, newpyfile):
            """
                replaces PyLoadFile instance with the given PyLoadFile instance at the given id
            """
            collector.file_list.lock.acquire()
            try:
                n, pyfile = collector._getFileFromID(newpyfile.id)
                collector.file_list.data["collector"][n] = newpyfile
            finally:
                collector.file_list.lock.release()
        
    class pyLoadPackager():
        def __init__(packager, file_list):
            packager.file_list = file_list
        
        def _getFreeID(packager):
            """
                returns a free id
            """
            ids = []
            for pypack in (packager.file_list.data["packages"] + packager.file_list.data["queue"]):
                ids.append(pypack.id)
            id = 1
            while id in ids:
                id += 1
            return id
        
        def _getPackageFromID(packager, id):
            """
                returns PyLoadPackage instance and position with given id
            """
            for n, pypack in enumerate(packager.file_list.data["packages"]):
                if pypack.id == id:
                    return ("packages", n, pypack)
            for n, pypack in enumerate(packager.file_list.data["queue"]):
                if pypack.id == id:
                    return ("queue", n, pypack)
            raise NoSuchElementException()
        
        def addNewPackage(packager, package_name=None):
            pypack = PyLoadPackage()
            pypack.id = packager._getFreeID()
            if package_name is not None:
                pypack.data["package_name"] = package_name
            packager.file_list.data["packages"].append(pypack)
            return pypack.id
        
        def removePackage(packager, id):
            packager.file_list.lock.acquire()
            try:
                key, n, pypack = packager._getPackageFromID(id)
                del packager.file_list.data[key][n]
            finally:
                packager.file_list.lock.release()
        
        def pushPackage2Queue(packager, id):
            packager.file_list.lock.acquire()
            try:
                key, n, pypack = packager._getPackageFromID(id)
                if key == "packages":
                    del packager.file_list.data["packages"][n]
                    packager.file_list.data["queue"].append(pypack)
            finally:
                packager.file_list.lock.release()
        
        def pullOutPackage(packager, id):
            packager.file_list.lock.acquire()
            try:
                key, n, pypack = packager._getPackageFromID(id)
                if key == "queue":
                    del packager.file_list.data["queue"][n]
                    packager.file_list.data["packages"].append(pypack)
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
            finally:
                packager.file_list.lock.release()
        
        def addFileToPackage(packager, id, pyfile):
            key, n, pypack = packager._getPackageFromID(id)
            pyfile.package = pypack
            pypack.files.append(pyfile)
            packager.file_list.data[key][n] = pypack
       
        def removeFileFromPackage(packager, id, pid):
            key, n, pypack = packager._getPackageFromID(pid)
            for k, pyfile in enumerate(pypack.files):
                if id == pyfile.id:
                    del pypack.files[k]
                    return True
            raise NoSuchElementException()

class PyLoadPackage():
    def __init__(self):
        self.files = []
        self.data = {
            "id": None,
            "package_name": "",
            "folder": ""
        }

class PyLoadFile():
    def __init__(self, url):
        self.id = None
        self.url = url
        self.folder = None
        self.package = None
        self.filename = "filename"
        self.download_folder = ""
        self.active = False
        pluginName = self._get_my_plugin()
        if pluginName:
            self.modul = __import__(pluginName)
            pluginClass = getattr(self.modul, self.modul.__name__)
        else:
            self.modul = module.Plugin
            pluginClass = module.Plugin.Plugin
        self.plugin = pluginClass(self)
        self.status = Status(self)
    
    def _get_my_plugin(self):
        for plugin, plugin_pattern in self.parent.plugins_avaible.items():
            if re.match(plugin_pattern, self.url) != None:
                return plugin

    def init_download(self):
        if self.parent.config['proxy']['activated']:
            self.plugin.req.add_proxy(self.parent.config['proxy']['protocol'], self.parent.config['proxy']['adress'])
