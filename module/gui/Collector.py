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

from module.gui.Queue import ItemIterator

class PackageCollector(QObject):
    def __init__(self, view, connector):
        QObject.__init__(self)
        self.view = view
        self.connector = connector
        self.collector = []
        self.rootItem = self.view.invisibleRootItem()
        self.mutex = QMutex()
        item = self.PackageCollectorPack(self)
        item.setPackData({"id":"fixed"})
        item.setData(0, Qt.DisplayRole, QVariant("Single Links"))
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.rootItem.addChild(item)
        self.linkCollector = item
    
    def fullReload(self):
        locker = QMutexLocker(self.mutex)
        self.clearAll()
        packs = self.connector.getPackageCollector()
        for data in packs:
            pack = self.PackageCollectorPack(self)
            pack.setPackData(data)
            files = self.connector.getPackageFiles(data["id"])
            for fid in files:
                info = self.connector.getLinkInfo(fid)
                child = self.PackageCollectorFile(self, pack)
                child.setFileData(info)
                pack.addPackChild(fid, child)
            self.addPack(data["id"], pack)
    
    def addEvent(self, event):
        if event[0] == "reload":
            self.fullReload()
        elif event[0] == "remove":
            self.removeEvent(event)
        elif event[0] == "insert":
            self.insertEvent(event)
        elif event[0] == "update":
            self.updateEvent(event)
    
    def removeEvent(self, event):
        if event[2] == "file":
            for pack in ItemIterator(self.rootItem):
                for k, child in enumerate(pack.getChildren()):
                    if child.getFileData()["id"] == event[3]:
                        pack.removeChild(child)
                        break
        else:
            for k, pack in enumerate(ItemIterator(self.rootItem)):
                if pack.getPackData()["id"] == event[3]:
                    pack.clearAll()
                    self.rootItem.removeChild(pack)
                    break
    
    def insertEvent(self, event):
        if event[2] == "file":
            info = self.connector.getLinkInfo(event[3])
            for pack in ItemIterator(self.rootItem):
                if pack.getPackData()["id"] == info["package"]:
                    child = self.PackageCollectorFile(self, pack)
                    child.setFileData(info)
                    pack.addPackChild(info["id"], child)
                    break
        else:
            data = self.connector.getPackageInfo(event[3])
            pack = self.PackageCollectorPack(self)
            pack.setPackData(data)
            self.addPack(data["id"], pack)
            files = self.connector.getPackageFiles(data["id"])
            for fid in files:
                info = self.connector.getLinkInfo(fid)
                child = self.PackageCollectorFile(self, pack)
                child.setFileData(info)
                pack.addPackChild(fid, child)
            self.addPack(data["id"], pack)
    
    def updateEvent(self, event):
        if event[2] == "file":
            info = self.connector.getLinkInfo(event[3])
            if not info:
                return
            for pack in ItemIterator(self.rootItem):
                if pack.getPackData()["id"] == info["package"]:
                    child = pack.getChild(event[3])
                    child.setFileData(info)
                    pack.addPackChild(info["id"], child)
        else:
            data = self.connector.getPackageInfo(event[3])
            pack = self.getPack(event[3])
            pack.setPackData(data)
            files = self.connector.getPackageFiles(data["id"])
            for fid in files:
                info = self.connector.getLinkInfo(fid)
                child = pack.getChild(fid)
                if not child:
                    child = self.PackageCollectorFile(self, pack)
                child.setFileData(info)
                pack.addPackChild(fid, child)
            self.addPack(data["id"], pack)
    
    def addPack(self, pid, newPack):
        pos = None
        try:
            for pack in ItemIterator(self.rootItem):
                if pack.getPackData()["id"] == pid:
                    pos = self.rootItem.indexOfChild(pack)
                    break
            if pos == None:
                raise Exception()
            item = self.rootItem.child(pos)
            item.setPackData(newPack.getPackData())
        except:
            self.rootItem.insertChild(self.rootItem.childCount()-1, newPack)
            item = newPack
        item.setData(0, Qt.DisplayRole, QVariant(item.getPackData()["package_name"]))
        item.setData(0, Qt.UserRole, QVariant(pid))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsEditable)
    
    def getPack(self, pid):
        for k, pack in enumerate(ItemIterator(self.rootItem)):
            if pack.getPackData()["id"] == pid:
                return pack
        return None
    
    def clearAll(self):
        for k, pack in enumerate(ItemIterator(self.rootItem)):
            if not pack.getPackData()["id"] == "fixed":
                pack.clearAll()
                self.rootItem.removeChild(pack)
    
    class PackageCollectorPack(QTreeWidgetItem):
        def __init__(self, collector):
            QTreeWidgetItem.__init__(self)
            self.collector = collector
            self._data = {}
        
        def addPackChild(self, cid, newChild):
            pos = None
            try:
                for child in ItemIterator(self):
                    if child.getData()["id"] == cid:
                        pos = self.indexOfChild(child)
                        break
                if pos == None:
                    raise Exception()
                item = self.child(pos)
                item.setFileData(newChild.getFileData())
            except:
                self.addChild(newChild)
                item = newChild
            item.setData(0, Qt.DisplayRole, QVariant(item.getFileData()["filename"]))
            item.setData(0, Qt.UserRole, QVariant(cid))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        def setPackData(self, data):
            self._data = data
        
        def getPackData(self):
            return self._data
        
        def getChildren(self):
            ret = []
            for item in ItemIterator(self):
                ret.append(item)
            return ret
        
        def getChild(self, cid):
            for item in ItemIterator(self):
                if item.getFileData()["id"] == cid:
                    return item
            return None
    
        def clearAll(self):
            for c in ItemIterator(self):
                self.removeChild(c)

    class PackageCollectorFile(QTreeWidgetItem):
        def __init__(self, collector, pack):
            QTreeWidgetItem.__init__(self)
            self.collector = collector
            self.pack = pack
            self._data = {}
            self.wait_since = None
        
        def getFileData(self):
            return self._data
        
        def setFileData(self, data):
            self._data = data
        
        def getPack(self):
            return self.pack

class LinkCollector(QObject):
    def __init__(self, view, root, connector):
        QObject.__init__(self)
        self.view = view
        self.connector = connector
        self.rootItem = root
        self.mutex = QMutex()
    
    def fullReload(self):
        locker = QMutexLocker(self.mutex)
        self.clearAll()
        ids = self.connector.getLinkCollector()
        for fid in ids:
            data = self.connector.getLinkInfo(fid)
            file = self.LinkCollectorFile(self)
            file.setFileData(data)
            self.addFile(fid, file)
    
    def addEvent(self, event):
        if event[0] == "reload":
            self.fullReload()
        elif event[0] == "remove":
            self.removeEvent(event)
        elif event[0] == "insert":
            self.insertEvent(event)
        elif event[0] == "update":
            self.updateEvent(event)
    
    def removeEvent(self, event):
        if event[2] == "file":
            for k, file in enumerate(ItemIterator(self.rootItem)):
                if file.getFileData()["id"] == event[3]:
                    self.rootItem.removeChild(file)
                    break
    
    def insertEvent(self, event):
        if event[2] == "file":
            data = self.connector.getLinkInfo(event[3])
            file = self.LinkCollectorFile(self)
            file.setFileData(data)
            self.addFile(event[3], file)
    
    def updateEvent(self, event):
        if event[2] == "file":
            data = self.connector.getLinkInfo(event[3])
            if not data:
                return
            file = getFile(event[3])
            file.setFileData(data)
            self.addFile(event[3], file)
    
    def addFile(self, pid, newFile):
        pos = None
        try:
            for pack in ItemIterator(self.rootItem):
                if file.getFileData()["id"] == pid:
                    pos = self.rootItem.indexOfChild(file)
                    break
            if pos == None:
                raise Exception()
            item = self.rootItem.child(pos)
            item.setFileData(newFile.getPackData())
        except:
            self.rootItem.addChild(newFile)
            item = newFile
        item.setData(0, Qt.DisplayRole, QVariant(newFile.getFileData()["filename"]))
        item.setData(0, Qt.UserRole, QVariant(pid))
        flags = Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled
        item.setFlags(flags)
    
    def getFile(self, pid):
        for file in ItemIterator(self.rootItem):
            if file.getFileData()["id"] == pid:
                return file
        return None
    
    def clearAll(self):
        for k, file in enumerate(ItemIterator(self.rootItem)):
            self.rootItem.removeChild(file)
    
    class LinkCollectorFile(QTreeWidgetItem):
        def __init__(self, collector):
            QTreeWidgetItem.__init__(self)
            self.collector = collector
            self._data = {}
        
        def getFileData(self):
            return self._data
        
        def setFileData(self, data):
            self._data = data
