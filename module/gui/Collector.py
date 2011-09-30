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

from module.PyFile import statusMap
from module.utils import formatSize

from module.remote.thriftbackend.ThriftClient import Destination, FileDoesNotExists, ElementType

statusMapReverse = dict((v,k) for k, v in statusMap.iteritems())

translatedStatusMap = {} # -> CollectorModel.__init__

class CollectorModel(QAbstractItemModel):
    """
        model for the collector view
    """
    
    def __init__(self, view, connector):
        QAbstractItemModel.__init__(self)
        self.connector = connector
        self.view = view
        self._data = []
        self.cols = 4
        self.interval = 1
        self.mutex = QMutex()
        
        global translatedStatusMap # workaround because i18n is not running at import time
        translatedStatusMap = {
            "finished":    _("finished"),
            "offline":     _("offline"),
            "online":      _("online"),
            "queued":      _("queued"),
            "skipped":    _("skipped"),
            "waiting":     _("waiting"),
            "temp. offline": _("temp. offline"),
            "starting":    _("starting"),
            "failed":      _("failed"),
            "aborted":     _("aborted"),
            "decrypting":  _("decrypting"),
            "custom":      _("custom"),
            "downloading": _("downloading"),
            "processing":  _("processing")
        }
    
    def translateStatus(self, string):
        """
            used to convert to locale specific status
        """
        return translatedStatusMap[string]
    
    def addEvent(self, event):
        """
            called from main loop, pass events to the correct methods
        """
        QMutexLocker(self.mutex)
        if event.eventname == "reload":
            self.fullReload()
        elif event.eventname == "remove":
            self.removeEvent(event)
        elif event.eventname == "insert":
            self.insertEvent(event)
        elif event.eventname == "update":
            self.updateEvent(event)
    
    def fullReload(self):
        """
            reload whole model, used at startup to load initial data
        """
        self._data = []
        order = self.connector.getPackageOrder(Destination.Collector)
        self.beginInsertRows(QModelIndex(), 0, len(order.values()))
        for position, pid in order.iteritems():
            pack = self.connector.getPackageData(pid)
            package = Package(pack)
            self._data.append(package)
        self._data = sorted(self._data, key=lambda p: p.data["order"])
        self.endInsertRows()
    
    def removeEvent(self, event):
        """
            remove an element from model
        """
        if event.type == ElementType.File:
            for p, package in enumerate(self._data):
                for k, child in enumerate(package.children):
                    if child.id == event.id:
                        self.beginRemoveRows(self.index(p, 0), k, k)
                        del package.children[k]
                        self.endRemoveRows()
                        break
        else:
            for k, package in enumerate(self._data):
                if package.id == event.id:
                    self.beginRemoveRows(QModelIndex(), k, k)
                    del self._data[k]
                    self.endRemoveRows()
                    break
    
    def insertEvent(self, event):
        """
            inserts a new element in the model
        """
        if event.type == ElementType.File:
            try:
                info = self.connector.getFileData(event.id)
            except FileDoesNotExists:
                return
            
            for k, package in enumerate(self._data):
                if package.id == info.package:
                    if package.getChild(info.fid):
                        self.updateEvent(event)
                        break
                    self.beginInsertRows(self.index(k, 0), info.order, info.order)
                    package.addChild(info)
                    self.endInsertRows()
                    break
        else:
            data = self.connector.getPackageData(event.id)
            package = Package(data)
            self.beginInsertRows(QModelIndex(), data.order, data.order)
            self._data.insert(data.order, package)
            self.endInsertRows()
    
    def updateEvent(self, event):
        """
            update an element in the model
        """
        if event.type == ElementType.File:
            try:
                info = self.connector.proxy.getFileData(event.id)
            except FileDoesNotExists:
                return
            for p, package in enumerate(self._data):
                if package.id == info.packageID:
                    for k, child in enumerate(package.children):
                        if child.id == event.id:
                            child.update(info)
                            if not info.status == 12:
                                child.data["downloading"] = None
                            self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(k, 0, self.index(p, 0)), self.index(k, self.cols, self.index(p, self.cols)))
                    break
        else:
            data = self.connector.getPackageData(event.id)
            if not data:
                return
            for p, package in enumerate(self._data):
                if package.id == event.id:
                    package.update(data)
                    self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(p, 0), self.index(p, self.cols))
                    break
    
    def data(self, index, role=Qt.DisplayRole):
        """
            return cell data
        """
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return QVariant(index.internalPointer().data["name"])
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
            elif index.column() == 3:
                item = index.internalPointer()
                if isinstance(item, Link):
                    return QVariant(formatSize(item.data["size"]))
                else:
                    ms = 0
                    for c in item.children:
                        ms += c.data["size"]
                    return QVariant(formatSize(ms))
        elif role == Qt.EditRole:
            if index.column() == 0:
                return QVariant(index.internalPointer().data["name"])
        return QVariant()
        
    def index(self, row, column, parent=QModelIndex()):
        """
            creates a cell index with pointer to the data
        """
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
        """
            return index of parent element
            only valid for links
        """
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
        """
            returns row count for the element
        """
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
        return self.rowCount(parent) > 0
    
    def canFetchMore(self, parent):
        return False
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
            returns column heading
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return QVariant(_("Name"))
            elif section == 1:
                return QVariant(_("Plugin"))
            elif section == 2:
                return QVariant(_("Status"))
            elif section == 3:
                return QVariant(_("Size"))
        return QVariant()
    
    def flags(self, index):
        """
            cell flags
        """
        if index.column() == 0 and self.parent(index) == QModelIndex():
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
   
    def setData(self, index, value, role=Qt.EditRole):
        """
            called if package name editing is finished, sets new name
        """
        if index.column() == 0 and self.parent(index) == QModelIndex() and role == Qt.EditRole:
            self.connector.setPackageName(index.internalPointer().id, str(value.toString()))
        return True

class Package(object):
    """
        package object in the model
    """
    
    def __init__(self, pack):
        self.id = pack.pid
        self.children = []
        for f in pack.links:
            self.addChild(f)
        self.data = {}
        self.update(pack)
    
    def update(self, pack):
        """
            update data dict from thift object
        """
        data = {
            "name": pack.name,
            "folder": pack.folder,
            "site": pack.site,
            "password": pack.password,
            "order": pack.order,
        }
        self.data.update(data)
    
    def addChild(self, f):
        """
            add child (Link) to package
        """
        self.children.insert(f.order, Link(f, self))
        self.children = sorted(self.children, key=lambda l: l.data["order"])
    
    def getChild(self, fid):
        """
            get child from package
        """
        for child in self.children:
            if child.id == int(fid):
                return child
        return None
    
    def getChildKey(self, fid):
        """
            get child index
        """
        for k, child in enumerate(self.children):
            if child.id == int(fid):
                return k
        return None
    
    def removeChild(self, fid):
        """
            remove child
        """
        for k, child in enumerate(self.children):
            if child.id == int(fid):
                del self.children[k]

class Link(object):
    def __init__(self, f, pack):
        self.data = {"downloading": None}
        self.update(f)
        self.id = f.fid
        self.package = pack
    
    def update(self, f):
        """
            update data dict from thift object
        """
        data = {
            "url": f.url,
            "name": f.name,
            "plugin": f.plugin,
            "size": f.size,
            "format_size": f.format_size,
            "status": f.status,
            "statusmsg": f.statusmsg,
            "package": f.packageID,
            "error": f.error,
            "order": f.order,
        }
        self.data.update(data)

class CollectorView(QTreeView):
    """
        view component for collector
    """
    
    def __init__(self, connector):
        QTreeView.__init__(self)
        self.setModel(CollectorModel(self, connector))
        self.setColumnWidth(0, 500)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 200)
        self.setColumnWidth(3, 100)
        
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

