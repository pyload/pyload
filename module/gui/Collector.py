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

from module.gui.Queue import ItemIterator

class PackageCollector(QThread):
    def __init__(self, view, connector):
        QThread.__init__(self)
        self.view = view
        self.connector = connector
        self.collector = []
        self.interval = 2
        self.running = True
        self.rootItem = self.view.invisibleRootItem()
        self.mutex = QMutex()
        item = self.PackageCollectorPack(self)
        item.setPackData({"id":"fixed"})
        item.setData(0, Qt.DisplayRole, QVariant("Single Links"))
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.rootItem.addChild(item)
        self.linkCollector = item
        self.pauseIDs = []
    
    def run(self):
        while self.running:
            self.update()
            sleep(self.interval)
    
    def stop(self):
        self.running = False
    
    def update(self):
        locker = QMutexLocker(self.mutex)
        packs = self.connector.getPackageCollector()
        ids = []
        for data in packs:
            ids.append(data["id"])
        self.clear(ids)
        for data in packs:
            if data["id"] in self.pauseIDs:
                continue
            ids.append(data["id"])
            pack = self.getPack(data["id"])
            if not pack:
                pack = self.PackageCollectorPack(self)
            pack.setPackData(data)
            self.addPack(data["id"], pack)
            files = self.connector.getPackageFiles(data["id"])
            pack.clear(files)
            for fid in files:
                info = self.connector.getLinkInfo(fid)
                child = pack.getChild(fid)
                if not child:
                    child = self.PackageCollectorFile(self, pack)
                child.setFileData(info)
                pack.addPackChild(fid, child)
    
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
    
    def clear(self, ids):
        clear = False
        remove = []
        for k, pack in enumerate(ItemIterator(self.rootItem)):
            if not pack.getPackData()["id"] in ids and not pack.getPackData()["id"] == "fixed":
                clear = True
                remove.append(k)
        if not clear:
            return
        remove.sort()
        remove.reverse()
        for k in remove:
            self.rootItem.takeChild(k)
    
    def pauseItemUpdate(self, pid, pause=True):
        locker = QMutexLocker(self.mutex)
        if pause and not pid in self.pauseIDs:
            self.pauseIDs.append(int(pid))
        else:
            try:
                self.pauseIDs.remove(int(pid))
            except:
                pass
    
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
    
        def clear(self, ids):
            clear = False
            remove = []
            children = []
            for k, file in enumerate(self.getChildren()):
                if not file.getFileData()["id"] in ids:
                    remove.append(file.getFileData()["id"])
                if file.getFileData()["id"] in children and not file.getFileData()["id"] in remove:
                    remove.append(file.getFileData()["id"])
                    continue
                children.append(file.getFileData()["id"])
            if not remove:
                return
            remove.sort()
            remove.reverse()
            parent = self
            for k in remove:
                parent.takeChild(k)

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

class LinkCollector(QThread):
    def __init__(self, view, root, connector):
        QThread.__init__(self)
        self.view = view
        self.connector = connector
        self.interval = 2
        self.running = True
        self.rootItem = root
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
        self.clear(ids)
        for fid in ids:
            data = self.connector.getLinkInfo(fid)
            file = self.getFile(fid)
            if not file:
                file = self.LinkCollectorFile(self)
            file.setFileData(data)
            self.addFile(fid, file)
    
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
    
    def clear(self, ids):
        clear = False
        for file in ItemIterator(self.rootItem):
            if not file.getFileData()["id"] in ids:
                clear = True
                break
        if not clear:
            return
        self.rootItem.takeChildren()

    class LinkCollectorFile(QTreeWidgetItem):
        def __init__(self, collector):
            QTreeWidgetItem.__init__(self)
            self.collector = collector
            self._data = {}
        
        def getFileData(self):
            return self._data
        
        def setFileData(self, data):
            self._data = data
