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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from time import sleep

class PackageCollector(QThread):
    def __init__(self, view, connector):
        QThread.__init__(self)
        self.view = view
        self.connector = connector
        self.collector = []
        self.interval = 2
        self.running = True
        self.mutex = QMutex()
    
    def run(self):
        while self.running:
            self.update()
            sleep(self.interval)
    
    def stop(self):
        self.running = False
    
    def update(self):
        locker = QMutexLocker(self.mutex)
        packs = self.connector.getPackageCollector()
        for data in packs:
            pack = self.getPack(data["id"])
            if not pack:
                pack = self.PackageCollectorPack(self)
            pack.setData(data)
            self.addPack(data["id"], pack)
            files = self.connector.getPackageFiles(data["id"])
            for fid in files:
                info = self.connector.getLinkInfo(fid)
                child = pack.getChild(fid)
                if not child:
                    child = self.PackageCollectorFile(self, pack)
                child.setData(info)
                pack.addChild(fid, child)
    
    def addPack(self, pid, newPack):
        pos = None
        try:
            for k, pack in enumerate(self.collector):
                if pack.getData()["id"] == pid:
                    pos = k
                    break
            if pos == None:
                raise Exception()
            self.collector[pos] = newPack
        except:
            self.collector.append(newPack)
            pos = self.collector.index(newPack)
        item = self.view.topLevelItem(pos)
        if not item:
            item = QTreeWidgetItem()
            self.view.insertTopLevelItem(pos, item)
        item.setData(0, Qt.DisplayRole, QVariant(newPack.getData()["package_name"]))
        item.setData(0, Qt.UserRole, QVariant(pid))
    
    def getPack(self, pid):
        for k, pack in enumerate(self.collector):
            if pack.getData()["id"] == pid:
                return pack
        return None
    
    class PackageCollectorPack():
        def __init__(self, collector):
            self.collector = collector
            self.data = []
            self.children = []
        
        def addChild(self, cid, newChild):
            pos = None
            try:
                for k, child in enumerate(self.getChildren()):
                    if child.getData()["id"] == cid:
                        pos = k
                        break
                if pos == None:
                    raise Exception()
                self.children[pos] = newChild
            except:
                self.children.append(newChild)
                pos = self.children.index(newChild)
            ppos = self.queue.queue.index(self)
            parent = self.queue.view.topLevelItem(ppos)
            item = parent.child(pos)
            if not item:
                item = QTreeWidgetItem()
                parent.insertChild(pos, item)
            status = "%s (%s)" % (newChild.getData()["status_type"], newChild.getData()["plugin"])
            item.setData(0, Qt.DisplayRole, QVariant(newChild.getData()["filename"]))
            item.setData(0, Qt.UserRole, QVariant(cid))
        
        def getChildren(self):
            return self.children
        
        def getChild(self, cid):
            try:
                return self.children[cid]
            except:
                return None
        
        def hasChildren(self, data):
            return (len(self.children) > 0)
        
        def setData(self, data):
            self.data = data
        
        def getData(self):
            return self.data

    class PackageCollectorFile():
        def __init__(self, collector, pack):
            self.collector = collector
            self.pack = pack
        
        def getData(self):
            return self.data
        
        def setData(self, data):
            self.data = data
        
        def getPack(self):
            return self.pack

class LinkCollector(QThread):
    def __init__(self, view, connector):
        QThread.__init__(self)
        self.view = view
        self.connector = connector
        self.collector = []
        self.interval = 2
        self.running = True
        self.mutex = QMutex()
    
    def run(self):
        while self.running:
            self.update()
            sleep(self.interval)
    
    def stop(self):
        self.running = False
    
    def update(self):
        locker = QMutexLocker(self.mutex)
        ids = self.connector.getLinkCollector()
        for id in ids:
            data = self.connector.getLinkInfo(id)
            file = self.getFile(id)
            if not file:
                file = self.LinkCollectorFile(self)
            file.setData(data)
            self.addFile(id, file)
    
    def addFile(self, pid, newFile):
        pos = None
        try:
            for k, file in enumerate(self.collector):
                if file.getData()["id"] == pid:
                    pos = k
                    break
            if pos == None:
                raise Exception()
            self.collector[pos] = newFile
        except:
            self.collector.append(newFile)
            pos = self.collector.index(newFile)
        item = self.view.topLevelItem(pos)
        if not item:
            item = QTreeWidgetItem()
            self.view.insertTopLevelItem(pos, item)
        item.setData(0, Qt.DisplayRole, QVariant(newFile.getData()["filename"]))
        item.setData(0, Qt.UserRole, QVariant(pid))
    
    def getFile(self, pid):
        for k, file in enumerate(self.collector):
            if file.getData()["id"] == pid:
                return file
        return None

    class LinkCollectorFile():
        def __init__(self, collector):
            self.collector = collector
        
        def getData(self):
            return self.data
        
        def setData(self, data):
            self.data = data
