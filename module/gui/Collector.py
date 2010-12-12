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

statusMap = {
    "finished":    0,
    "offline":     1,
    "online":      2,
    "queued":      3,
    "checking":    4,
    "waiting":     5,
    "reconnected": 6,
    "starting":    7,
    "failed":      8,
    "aborted":     9,
    "decrypting":  10,
    "custom":      11,
    "downloading": 12,
    "processing":  13
}
statusMapReverse = dict((v,k) for k, v in statusMap.iteritems())

translatedStatusMap = {} # -> CollectorModel.__init__

class CollectorModel(QAbstractItemModel):
    def __init__(self, view, connector):
        QAbstractItemModel.__init__(self)
        self.connector = connector
        self.view = view
        self._data = []
        self.cols = 3
        self.interval = 1
        self.mutex = QMutex()
        
        global translatedStatusMap # workaround because i18n is not running at import time
        translatedStatusMap = {
            "finished":    _("finished"),
            "offline":     _("offline"),
            "online":      _("online"),
            "queued":      _("queued"),
            "checking":    _("checking"),
            "waiting":     _("waiting"),
            "reconnected": _("reconnected"),
            "starting":    _("starting"),
            "failed":      _("failed"),
            "aborted":     _("aborted"),
            "decrypting":  _("decrypting"),
            "custom":      _("custom"),
            "downloading": _("downloading"),
            "processing":  _("processing")
        }
    
    def translateStatus(self, string):
        return translatedStatusMap[string]
    
    def addEvent(self, event):
        locker = QMutexLocker(self.mutex)
        if event[0] == "reload":
            self.fullReload()
        elif event[0] == "remove":
            self.removeEvent(event)
        elif event[0] == "insert":
            self.insertEvent(event)
        elif event[0] == "update":
            self.updateEvent(event)
    
    def fullReload(self):
        self._data = []
        packs = self.connector.getPackageCollector()
        self.beginInsertRows(QModelIndex(), 0, len(packs))
        for pid, data in packs.items():
            package = Package(pid, data)
            self._data.append(package)
        self._data = sorted(self._data, key=lambda p: p.data["order"])
        self.endInsertRows()
    
    def removeEvent(self, event):
        if event[2] == "file":
            for p, package in enumerate(self._data):
                for k, child in enumerate(package.children):
                    if child.id == int(event[3]):
                        self.beginRemoveRows(self.index(p, 0), k, k)
                        del package.children[k]
                        self.endRemoveRows()
                        break
        else:
            for k, package in enumerate(self._data):
                if package.id == int(event[3]):
                    self.beginRemoveRows(QModelIndex(), k, k)
                    del self._data[k]
                    self.endRemoveRows()
                    break
    
    def insertEvent(self, event):
        if event[2] == "file":
            info = self.connector.proxy.get_file_data(int(event[3]))
            fid = info.keys()[0]
            info = info.values()[0]
            
            for k, package in enumerate(self._data):
                if package.id == int(info["package"]):
                    if package.getChild(fid):
                        del event[4]
                        self.updateEvent(event)
                        break
                    self.beginInsertRows(self.index(k, 0), info["order"], info["order"])
                    package.addChild(fid, info, info["order"])
                    self.endInsertRows()
                    break
        else:
            data = self.connector.proxy.get_package_data(event[3])
            package = Package(event[3], data)
            self.beginInsertRows(QModelIndex(), data["order"], data["order"])
            self._data.insert(data["order"], package)
            self.endInsertRows()
    
    def updateEvent(self, event):
        if event[2] == "file":
            info = self.connector.proxy.get_file_data(int(event[3]))
            if not info:
                return
            fid = info.keys()[0]
            info = info.values()[0]
            for p, package in enumerate(self._data):
                if package.id == int(info["package"]):
                    for k, child in enumerate(package.children):
                        if child.id == int(event[3]):
                            child.data.update(info)
                            if not info["status"] == 12:
                                child.data["downloading"] = None
                            self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(k, 0, self.index(p, 0)), self.index(k, self.cols, self.index(p, self.cols)))
                    break
        else:
            data = self.connector.proxy.get_package_data(int(event[3]))
            if not data:
                return
            pid = event[3]
            del data["links"]
            for p, package in enumerate(self._data):
                if package.id == int(pid):
                    package.data = data
                    self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(p, 0), self.index(p, self.cols))
                    break
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return QVariant(index.internalPointer().data["name"])
            elif index.column() == 2:
                item = index.internalPointer()
                status = 0
                if isinstance(item, Package):
                    for child in item.children:
                        if child.data["status"] > status:
                            status = child.data["status"]
                else:
                    status = item.data["status"]
                return QVariant(self.translateStatus(statusMapReverse[status]))
            elif index.column() == 1:
                item = index.internalPointer()
                plugins = []
                if isinstance(item, Package):
                    for child in item.children:
                        if not child.data["plugin"] in plugins:
                            plugins.append(child.data["plugin"])
                else:
                    plugins.append(item.data["plugin"])
                return QVariant(", ".join(plugins))
        elif role == Qt.EditRole:
            if index.column() == 0:
                return QVariant(index.internalPointer().data["name"])
        return QVariant()
        
    def index(self, row, column, parent=QModelIndex()):
        if parent == QModelIndex() and len(self._data) > row:
            pointer = self._data[row]
            index = self.createIndex(row, column, pointer)
        elif parent.isValid():
            try:
                pointer = parent.internalPointer().children[row]
            except:
                return QModelIndex()
            index = self.createIndex(row, column, pointer)
        else:
            index = QModelIndex()
        return index
    
    def parent(self, index):
        if index == QModelIndex():
            return QModelIndex()
        if index.isValid():
            link = index.internalPointer()
            if isinstance(link, Link):
                for k, pack in enumerate(self._data):
                    if pack == link.package:
                        return self.createIndex(k, 0, link.package)
        return QModelIndex()
    
    def rowCount(self, parent=QModelIndex()):
        if parent == QModelIndex():
            #return package count
            return len(self._data)
        else:
            if parent.isValid():
                #index is valid
                pack = parent.internalPointer()
                if isinstance(pack, Package):
                    #index points to a package
                    #return len of children
                    return len(pack.children)
            else:
                #index is invalid
                return False
        #files have no children
        return 0
    
    def columnCount(self, parent=QModelIndex()):
        return self.cols
    
    def hasChildren(self, parent=QModelIndex()):
        if not parent.isValid():
            return True
        return (self.rowCount(parent) > 0)
    
    def canFetchMore(self, parent):
        return False
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return QVariant(_("Name"))
            elif section == 2:
                return QVariant(_("Status"))
            elif section == 1:
                return QVariant(_("Plugin"))
        return QVariant()
    
    def flags(self, index):
        if index.column() == 0 and self.parent(index) == QModelIndex():
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
   
    def setData(self, index, value, role=Qt.EditRole):
        if index.column() == 0 and self.parent(index) == QModelIndex() and role == Qt.EditRole:
            self.connector.setPackageName(index.internalPointer().id, str(value.toString()))
        return True

class Package(object):
    def __init__(self, pid, data):
        self.id = int(pid)
        self.children = []
        for fid, fdata in data["links"].items():
            self.addChild(int(fid), fdata)
        del data["links"]
        self.data = data
    
    def addChild(self, fid, data, pos=None):
        if pos is None:
            self.children.insert(data["order"], Link(fid, data, self))
        else:
            self.children.insert(pos, Link(fid, data, self))
        self.children = sorted(self.children, key=lambda l: l.data["order"])
    
    def getChild(self, fid):
        for child in self.children:
            if child.id == int(fid):
                return child
        return None
    
    def getChildKey(self, fid):
        for k, child in enumerate(self.children):
            if child.id == int(fid):
                return k
        return None
    
    def removeChild(self, fid):
        for k, child in enumerate(self.children):
            if child.id == int(fid):
                del self.children[k]

class Link(object):
    def __init__(self, fid, data, pack):
        self.data = data
        self.data["downloading"] = None
        self.id = int(fid)
        self.package = pack

class CollectorView(QTreeView):
    def __init__(self, connector):
        QTreeView.__init__(self)
        self.setModel(CollectorModel(self, connector))
        self.setColumnWidth(0, 500)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 200)
        
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

