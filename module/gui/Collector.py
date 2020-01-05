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

from PyQt4.QtCore import QAbstractItemModel, QModelIndex, QMutex, QMutexLocker, QObject, QRegExp, QString, Qt, QTimer, QVariant, SIGNAL
from PyQt4.QtGui import QAbstractItemView, QApplication, QItemSelection, QItemSelectionModel, QItemSelectionRange, QMenu, QTreeView

import logging, re
from time import time
from datetime import datetime

from module.remote.thriftbackend.ThriftClient import Destination, FileDoesNotExists, PackageDoesNotExists, ElementType, DownloadStatus
from module.PyFile import statusMap
from module.utils import formatSize, formatSpeed
from module.gui.Tools import whatsThisFormat, longestSubsequence, WidgetDisable

statusMapReverse = dict((v,k) for k, v in statusMap.iteritems())

translatedStatusMap = {} # -> CollectorModel.__init__

class CollectorModel(QAbstractItemModel):
    """
        model for the collector view
    """
    
    @classmethod
    def time_msec(self):
        return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)
    
    def __init__(self, view, connector):
        QAbstractItemModel.__init__(self)
        self.cname = self.__class__.__name__
        self.log = logging.getLogger("guilog")
        self.view = view
        self.connector = connector
        
        self._data = []
        self.expandedState = {}
        self.currentItem = None
        self.selectedItems = []
        self.cols = 8
        self.interval = 1
        self.mutex = QMutex()
        self.dnd = DragAndDrop(self.view, self)
        self.dnd.havePermissions = False
        self.dnd.allowLinkMove = True
        self.lastFullReload = float(0.0)
        
        self.dirty = False
        self.firstSetDirty = None
        self.lastSetDirty  = None
        self.dirtyReloadDelayMin = float(4.5)   # const seconds
        self.dirtyReloadDelayMax = float(9.5)   # const seconds
        
        self.showToolTips = True
        
        global translatedStatusMap # workaround because i18n is not running at import time
        translatedStatusMap = {
            "finished":      _("finished"),
            "offline":       _("offline"),
            "online":        _("online"),
            "queued":        _("queued"),
            "skipped":       _("skipped"),
            "waiting":       _("waiting"),
            "temp. offline": _("temp. offline"),
            "starting":      _("starting"),
            "failed":        _("failed"),
            "aborted":       _("aborted"),
            "decrypting":    _("decrypting"),
            "custom":        _("custom"),
            "downloading":   _("downloading"),
            "processing":    _("processing")
        }
    
    def translateStatus(self, string):
        """
            used to convert to locale specific status
        """
        return translatedStatusMap[string]
    
    def getSelectionInfo(self):
        """
            called from MainWindow
        """
        func_start_time = self.time_msec()
        QMutexLocker(self.mutex)
        packsCnt = linksCnt = 0
        downloading = False
        for si in self.view.selectionModel().selectedIndexes():
            if si.column() != 0:
                continue
            item = si.internalPointer()
            if isinstance(item, Package):
                packsCnt += 1
                if not downloading:
                    for child in item.children:
                        if child.data["downloading"]:
                            downloading = True
                            break
            elif isinstance(item, Link):
                linksCnt += 1
                if not downloading:
                    if item.data["downloading"]:
                        downloading = True
            else:
                raise TypeError("Unknown item instance")
        allPacksCnt = len(self._data)
        self.log.debug8("%s.getSelectionInfo took %dms, packsCnt:%d linksCnt:%d downloading:%s allPacksCnt:%d" % (self.cname, self.time_msec() - func_start_time, packsCnt, linksCnt, downloading, allPacksCnt))
        return (packsCnt, linksCnt, downloading, allPacksCnt)
    
    def getSelection(self, deselect, linksOfPacks):
        """
            called from main
            deselect:     deselect the returned items
            linksOfPacks: if deselect, for the links, only deselect those which belong to a selected package
        """
        func_start_time = self.time_msec()
        QMutexLocker(self.mutex)
        selection = []          # (pid, fid, isPack)
        smodel = self.view.selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            if isinstance(item, Package):
                selection.append((item.id, None, True))
            elif isinstance(item, Link):
                selection.append((item.data["package"], item.id, False))
            else:
                raise TypeError("%s: Unknown item instance" % self.cname)
            if deselect and not linksOfPacks:
                smodel.select(index, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
        if deselect and linksOfPacks:
            for packindex in smodel.selectedRows(0):
                pack = packindex.internalPointer()
                if isinstance(pack, Package):
                    smodel.select(packindex, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
                    for linkindex in smodel.selectedRows(0):
                        link = linkindex.internalPointer()
                        if isinstance(link, Link) and link.data["package"] == pack.id:
                            smodel.select(linkindex, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
        self.log.debug8("%s.getSelection took %dms" % (self.cname, self.time_msec() - func_start_time))
        return selection
    
    def getLastAddedPackage(self):
        """
            called from main
            used for package added desktop notification
            returns info about the package with the highest id
        """
        func_start_time = self.time_msec()
        QMutexLocker(self.mutex)
        if self.lastFullReload == 0:
            return None
        if self.dirty:
            return None
        lpa = (0, "")   # valid package ids are > 0
        for package in self._data:
            if package.id > lpa[0]:
                lpa = (package.id, package.data["name"])
        t = self.time_msec() - func_start_time
        if t > 10:
            self.log.info("%s.getLastAddedPackage took %dms" % (self.cname, t))
        return lpa
    
    def getSelectedPackagesForEdit(self):
        """
            called from main
        """
        func_start_time = self.time_msec()
        QMutexLocker(self.mutex)
        selection = []          # (pid, name, folder, password)
        smodel = self.view.selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            if isinstance(item, Package):
                selection.append((item.id, item.data["name"], item.data["folder"], item.data["password"]))
            elif not isinstance(item, Link):
                raise TypeError("%s: Unknown item instance" % self.cname)
        self.log.debug8("%s.getSelectedPackagesForEdit took %dms" % (self.cname, self.time_msec() - func_start_time))
        return selection
    
    def saveViewItemStates(self):
        func_start_time = self.time_msec()
        # expanded/collapsed
        for p, package in enumerate(self._data):
            pid = package.id
            index = self.index(p, 0)
            if index.isValid():
                e = self.view.isExpanded(index)
                self.expandedState[str(pid)] = e
                self.log.debug0("%s.saveViewItemStates:expanded:   row:%d   name:'%s'   pid:%d   e:%d" % (self.cname, p, package.data["name"], pid, e))
            else:
                raise ValueError("%s: Invalid index" % self.cname)
        # current item
        self.currentItem = None
        smodel = self.view.selectionModel()
        ci = smodel.currentIndex()
        if ci.isValid():
            item = ci.internalPointer()
            if isinstance(item, Package):
                pid = item.id
                fid = None
            elif isinstance(item, Link):
                pid = item.data["package"]
                fid = item.id
            else:
                raise TypeError("%s: Unknown item instance" % self.cname)
            self.currentItem = (pid, fid)
            self.log.debug0("%s.saveViewItemStates:currentItem:   name:'%s'   pid:%d   fid:%s" % (self.cname, item.data["name"], pid, str(fid)))
        else:
            self.log.debug0("%s.saveViewItemStates:currentItem: <none>" % self.cname)
        # selection
        self.selectedItems = []
        for si in smodel.selectedRows(0):
            item = si.internalPointer()
            if isinstance(item, Package):
                pid = item.id
                fid = None
            elif isinstance(item, Link):
                pid = item.data["package"]
                fid = item.id
            else:
                raise TypeError("%s: Unknown item instance" % self.cname)
            self.selectedItems.append([pid, fid])
            self.log.debug0("%s.saveViewItemStates:selectedItem:   name:'%s'   pid:%d   fid:%s" % (self.cname, item.data["name"], pid, str(fid)))
        self.log.debug8("%s.saveViewItemStates took %dms" % (self.cname, self.time_msec() - func_start_time))
    
    def applyViewItemStates(self):
        func_start_time = self.time_msec()
        # expanded/collapsed
        for p, package in enumerate(self._data):
            pid = package.id
            index = self.index(p, 0)
            if index.isValid():
                try:
                    e = self.expandedState[str(pid)]
                except KeyError:
                    continue
                self.view.setExpanded(index, e)
                self.log.debug0("%s.applyViewItemStates:expanded:   row:%d   name:'%s'   pid:%d   e:%d" % (self.cname, p, package.data["name"], pid, e))
            else:
                raise ValueError("%s: Invalid index" % self.cname)
        # current item
        smodel = self.view.selectionModel()
        if self.currentItem:
            (pid, fid) = self.currentItem
            itemIsPackage = (fid == None)
            index = None
            for p, package in enumerate(self._data):
                if package.id == pid:
                    pindex = self.index(p, 0)
                    if not pindex.isValid():
                        raise ValueError("%s: Invalid index" % self.cname)
                    if itemIsPackage:
                        index = pindex
                    else:
                        for l, link in enumerate(package.children):
                            if link.id == fid:
                                index = self.index(l, 0, pindex)
                                if not index.isValid():
                                    raise ValueError("%s: Invalid index" % self.cname)
                                break
                    break
            if index:
                smodel.setCurrentIndex(index, QItemSelectionModel.NoUpdate)
                self.log.debug0("%s.applyViewItemStates:currentItem:   pid:%d   fid:%s" % (self.cname, pid, str(fid)))
            else:
                self.log.debug0("%s.applyViewItemStates:currentItem: *Not found*   pid:%d   fid:%s" % (self.cname, pid, str(fid)))
        else:
            self.log.debug0("%s.applyViewItemStates:currentItem: <none>" % self.cname)
        # selection
        self.view.clearSelection()
        itemSel = QItemSelection()
        for ids in self.selectedItems:
            pid = ids[0]
            fid = ids[1]
            itemIsPackage = (fid == None)
            index = None
            for p, package in enumerate(self._data):
                if package.id == pid:
                    pindex = self.index(p, 0)
                    if not pindex.isValid():
                        raise ValueError("%s: Invalid index" % self.cname)
                    if itemIsPackage:
                        index = pindex
                    else:
                        for l, link in enumerate(package.children):
                            if link.id == fid:
                                index = self.index(l, 0, pindex)
                                if not index.isValid():
                                    raise ValueError("%s: Invalid index" % self.cname)
                                break
                    break
            if index:
                its = QItemSelection()
                its.append(QItemSelectionRange(index, self.index(index.row(), self.cols - 1, index.parent())))
                itemSel.merge(its, QItemSelectionModel.Select)
                self.log.debug0("%s.applyViewItemStates:selectedItem:   pid:%d   fid:%s" % (self.cname, pid, str(fid)))
            elif itemIsPackage:
                self.log.warning("%s.applyViewItemStates:selectedItem: Prevoiusly selected package not found, pid:%d" % (self.cname, pid))
            else:
                self.log.warning("%s.applyViewItemStates:selectedItem: Prevoiusly selected link not found, fid:%s (in package pid:%d)" % (self.cname, str(fid), pid))
        smodel.select(itemSel, QItemSelectionModel.Select)
        self.log.debug8("%s.applyViewItemStates took %dms" % (self.cname, self.time_msec() - func_start_time))
    
    def selectAllPackages(self, deselect):
        func_start_time = self.time_msec()
        QMutexLocker(self.mutex)
        smodel = self.view.selectionModel()
        for p in xrange(len(self._data)):
            index = self.index(p, 0)
            if not deselect:
                if not smodel.isSelected(index): smodel.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
            else:
                if smodel.isSelected(index): smodel.select(index, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
        self.log.debug8("%s.selectAllPackages took %dms" % (self.cname, self.time_msec() - func_start_time))
    
    def selectAll(self, deselect):
        func_start_time = self.time_msec()
        QMutexLocker(self.mutex)
        if not deselect:
            self.view.setCurrentIndex(QModelIndex())
            self.view.selectAll()
        else:
            self.view.clearSelection()
            self.view.setCurrentIndex(QModelIndex())
        self.log.debug8("%s.selectAll took %dms, deselect:%s" % (self.cname, self.time_msec() - func_start_time, deselect))
    
    def fullReloadFromMenu(self):
        if not self.view.corePermissions["LIST"]:
            return
        self.log.debug9("%s.fullReloadFromMenu: function entered" % self.cname)
        QMutexLocker(self.mutex)
        wdgd = WidgetDisable(self.view)
        self.fullReload(False)
        wdgd.Enable()
    
    def fullReloadFromPullEvents(self):
        self.log.debug9("%s.fullReloadFromPullEvents: function entered" % self.cname)
        QMutexLocker(self.mutex)
        self.fullReload()
    
    def automaticReloading(self, interval):
        if not self.view.corePermissions["LIST"]:
            return
        if time() > self.lastFullReload + interval:
            QMutexLocker(self.mutex)
            self.fullReload()
            self.log.debug2("%s.automaticReloading: done" % self.cname)
    
    def fullReloadOnDirty(self, lock=True):
        if not self.view.corePermissions["LIST"]:
            return
        if self.dirty:
            t = time()
            if t > (self.lastSetDirty + self.dirtyReloadDelayMin) or t > (self.firstSetDirty + self.dirtyReloadDelayMax):
                if lock:
                    QMutexLocker(self.mutex)
                self.fullReload()
                self.log.debug2("%s.fullReloadOnDirty: done" % self.cname)
    
    def setDirty(self, lock=True):
        t = time()
        if lock:
            QMutexLocker(self.mutex)
        if not self.dirty:
            self.firstSetDirty = t
            self.lastSetDirty = t
            self.dirty = True
            self.log.debug2("%s.setDirty: first" % self.cname)
        else:
            if t < self.lastSetDirty: # the system clock has been set back
                self.firstSetDirty = t
            self.lastSetDirty = t
            self.log.debug2("%s.setDirty: last" % self.cname)
    
    def addEvent(self, event):
        """
            called from main loop, pass events to the correct methods
        """
        if not self.view.corePermissions["LIST"]:
            return
        QMutexLocker(self.mutex)
        if event.eventname == "reload":
            self.fullReload()
            self.log.debug2("%s.fullReload: done" % self.cname)
            return
#       self.saveViewItemStates()
        if event.eventname == "remove":
            self.removeEvent(event)
        elif event.eventname == "insert":
            self.insertEvent(event)
        elif event.eventname == "update":
            self.updateEvent(event)
#       self.applyViewItemStates()
        self.fullReloadOnDirty(False)
    
    def fullReload(self, enableView=True):
        """
            reload whole model, used at startup to load initial data
        """
        func_start_time = self.time_msec()
        self.lastFullReload = time()
        self.saveViewItemStates()
        self.beginResetModel()
        self._data = []
        self.endResetModel()
        order = self.connector.proxy.getPackageOrder(Destination.Collector)
        self.beginInsertRows(QModelIndex(), 0, len(order.values()))
        for position, pid in order.iteritems():
            try:
                pack = self.connector.proxy.getPackageData(pid)
            except PackageDoesNotExists:
                self.log.error("%s.fullReload: No package data received from the server, pid:%d" % (self.cname, pid))
                self.lastSetDirty = self.firstSetDirty = time()
                self.dirty = True
                self.view.setEnabled(False)
                return
            package = Package(pack)
            self._data.append(package)
        self.endInsertRows()
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self._data = sorted(self._data, key=lambda p: p.data["order"])
        self.emit(SIGNAL("layoutChanged()"))
        self.dirty = False
        self.fullReloadCheck()
        if enableView:
            self.view.setEnabled(self.view.corePermissions["LIST"])
        self.applyViewItemStates()
        self.log.debug8("%s.fullReload took %dms" % (self.cname, self.time_msec() - func_start_time))
    
    def fullReloadCheck(self):
        if len(self._data) == 0:
            return 0
        maxErrors = 10
        numErrors = 0
        indent = " " * len("%s.fullReloadCheck: " % self.cname)
        fpo = self._data[0].data["order"]
        # can we skip testing data[0] here ???
        for p, package in enumerate(self._data):
            if package.data["order"] != p + fpo:
                self.log.error("%s.fullReloadCheck: Non-sequential package order found," % self.cname)
                self.log.error(indent +            "order number %d expected for package '%s' with id:%d." % (p + fpo, package.data["name"], package.id))
                numErrors += 1
                if numErrors == maxErrors: self.log.error("%s.fullReloadCheck: Aborted, too many errors." % self.cname); return numErrors
            if package.children[0].data["order"] != 0:
                self.log.error("%s.fullReloadCheck: Non-zero link order found in package '%s' with id:%d," % (self.cname, package.data["name"], package.id))
                self.log.error(indent +            "order number 0 expected for first link '%s' with id:%d," % (package.children[0].data["name"], package.children[0].id))
                self.log.error(indent +            "skip checking remaining links of this package.")
                numErrors += 1
                if numErrors == maxErrors: self.log.error("%s.fullReloadCheck: Aborted, too many errors." % self.cname); return numErrors
                continue
            # can we skip testing children[0] here ???
            for l, link in enumerate(package.children):
                if link.data["order"] != l:
                    self.log.error("%s.fullReloadCheck: Non-sequential link order found in package '%s' with id:%d," % (self.cname, package.data["name"], package.id))
                    self.log.error(indent +            "order number %d expected for link '%s' with id:%d," % (l, link.data["name"], link.id))
                    self.log.error(indent +            "skip checking remaining links of this package.")
                    numErrors += 1
                    if numErrors == maxErrors: self.log.error("%s.fullReloadCheck: Aborted, too many errors." % self.cname); return numErrors
                    break
        self.log.debug8("%s.fullReloadCheck: Done, %d errors" % (self.cname, numErrors))
        return numErrors
    
    def removeEvent(self, event):
        """
            remove an element from model
        """
        if event.type == ElementType.File:
            linkFound = False
            for p, package in enumerate(self._data):
                for k, child in enumerate(package.children):
                    if child.id == event.id:
                        linkFound = True
                        self.beginRemoveRows(self.index(p, 0), k, k)
                        del package.children[k]
                        self.endRemoveRows()
                        self.log.debug1("%s.removeEvent: Link removed, fid:%d in pid:%d" % (self.cname, event.id, package.id))
                        # manually update all link order attributes, needed for Api.deleteFiles() and Api.orderFile() not sending link update events
                        for k, child in enumerate(package.children):
                            try:
                                info = self.connector.proxy.getFileData(child.id)
                            except FileDoesNotExists:
                                self.log.debug2("%s.removeEvent: Manual link update: No file data received from the server, fid:%d" % (self.cname, child.id))
                                self.setDirty(False)
                                return
                            child.update(info)  # child full update, updating just the order attribute causes crashes?
                            if not info.status == DownloadStatus.Downloading:
                                child.data["downloading"] = None
                            self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(k, 0, self.index(p, 0)), self.index(k, self.cols, self.index(p, self.cols)))
                            self.log.debug0("%s.removeEvent: Link manually updated, fid:%d in pid:%d" % (self.cname, child.id, package.id))
                        self.emit(SIGNAL("layoutAboutToBeChanged()"))
                        package.sortChildren()
                        self.emit(SIGNAL("layoutChanged()"))
                        self.log.debug0("%s.removeEvent: Links re-sorted, pid:%d" % (self.cname, package.id))
                        break
                if linkFound:
                    break
            if not linkFound:
                self.log.debug2("%s.removeEvent: Link not found, fid:%d" % (self.cname, event.id))
                self.setDirty(False)
        
        else: # ElementType.Package
            packageFound = False
            for p, package in enumerate(self._data):
                if package.id == event.id:
                    packageFound = True
                    self.beginRemoveRows(QModelIndex(), p, p)
                    del self._data[p]
                    self.endRemoveRows()
                    self.log.debug1("%s.removeEvent: Package removed, pid:%d" % (self.cname, event.id))
                    break
            if not packageFound:
                self.log.debug2("%s.removeEvent: Package not found, pid:%d" % (self.cname, event.id))
                self.setDirty(False)
    
    def insertEvent(self, event):
        """
            inserts a new element in the model
        """
        if event.type == ElementType.File:
            try:
                info = self.connector.proxy.getFileData(event.id)
            except FileDoesNotExists:
                self.log.debug2("%s.insertEvent: No file data received from the server, fid:%d" % (self.cname, event.id))
                self.setDirty(False)
                return
            for p, package in enumerate(self._data):
                if package.id == info.packageID:
                    for k, child in enumerate(package.children):
                        if child.id == event.id:
                            # link already exists, treat like an update
                            self.log.debug1("%s.insertEvent: Link is already in the tree view, fid:%d in pid:%d" % (self.cname, child.id, package.id))
                            orderChanged = bool(info.order != child.data["order"])
                            child.update(info)
                            if not info.status == DownloadStatus.Downloading:
                                child.data["downloading"] = None
                            self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(k, 0, self.index(p, 0)), self.index(k, self.cols, self.index(p, self.cols)))
                            self.log.debug1("%s.insertEvent: Existing link updated, fid:%d in pid:%d" % (self.cname, child.id, package.id))
                            if orderChanged:
                                self.log.warning("%s.insertEvent: Existing link order attribute value differs, fid:%d in pid:%d" % (self.cname, child.id, package.id))
                                self.emit(SIGNAL("layoutAboutToBeChanged()"))
                                package.sortChildren()
                                self.emit(SIGNAL("layoutChanged()"))
                                self.log.debug0("%s.insertEvent: Existing link updated: Links re-sorted, pid:%d" % (self.cname, package.id))
                            return
                    row = len(package.children)
                    self.beginInsertRows(self.index(p, 0), row, row)
                    package.addChild(info)
                    self.endInsertRows()
                    self.log.debug1("%s.insertEvent: Link inserted, fid:%d in pid:%d" % (self.cname, info.fid, package.id))
                    self.emit(SIGNAL("layoutAboutToBeChanged()"))
                    package.sortChildren()
                    self.emit(SIGNAL("layoutChanged()"))
                    self.log.debug0("%s.insertEvent: Links re-sorted, pid:%d" % (self.cname, package.id))
        
        else: # ElementType.Package
            try:
                data = self.connector.proxy.getPackageData(event.id)
            except PackageDoesNotExists:
                self.log.debug2("%s.insertEvent: No package data received from the server, pid:%d" % (self.cname, event.id))
                self.setDirty(False)
                return
            for p, package in enumerate(self._data):
                if package.id == event.id:
                    # package already exists, treat like an update
                    self.log.debug1("%s.insertEvent: Package is already in the tree view, pid:%d" % (self.cname, package.id))
                    orderChanged = bool(data.order != package.data["order"])
                    package.update(data)
                    self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(p, 0), self.index(p, self.cols))
                    self.log.debug1("%s.insertEvent: Existing package updated, pid:%d" % (self.cname, package.id))
                    if orderChanged:
                        self.log.warning("%s.insertEvent: Existing package order attribute value differs, pid:%d" % (self.cname, package.id))
                        self.emit(SIGNAL("layoutAboutToBeChanged()"))
                        self._data = sorted(self._data, key=lambda d: d.data["order"])
                        self.emit(SIGNAL("layoutChanged()"))
                        self.log.debug0("%s.insertEvent: Existing package updated: Packages re-sorted" % self.cname)
                    return
            pack = Package(data)
            self.beginInsertRows(QModelIndex(), 0, 0)
            self._data.insert(0, pack)
            self.endInsertRows()
            self.log.debug1("%s.insertEvent: Package inserted, pid:%d" % (self.cname, pack.id))
            self.emit(SIGNAL("layoutAboutToBeChanged()"))
            self._data = sorted(self._data, key=lambda d: d.data["order"])
            self.emit(SIGNAL("layoutChanged()"))
            self.log.debug0("%s.insertEvent: Packages re-sorted" % self.cname)
    
    def updateEvent(self, event):
        """
            update an element in the model
        """
        if event.type == ElementType.File:
            try:
                info = self.connector.proxy.getFileData(event.id)
            except FileDoesNotExists:
                self.log.debug2("%s.updateEvent: No file data received from the server, fid:%d" % (self.cname, event.id))
                self.setDirty(False)
                return
            linkFound = False
            for p, package in enumerate(self._data):
                if package.id == info.packageID:
                    packageStatus = DownloadStatus.Finished
                    for k, child in enumerate(package.children):
                        if child.id == event.id:
                            linkFound = True
                            orderChanged = bool(info.order != child.data["order"])
                            child.update(info)
                            if not info.status == DownloadStatus.Downloading:
                                child.data["downloading"] = None
                            self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(k, 0, self.index(p, 0)), self.index(k, self.cols, self.index(p, self.cols)))
                            self.log.debug1("%s.updateEvent: Link updated, fid:%d in pid:%d" % (self.cname, child.id, package.id))
                            if orderChanged:
                                self.log.warning("%s.updateEvent: Link order attribute changed, fid:%d in pid:%d" % (self.cname, child.id, package.id))
                                self.emit(SIGNAL("layoutAboutToBeChanged()"))
                                package.sortChildren()
                                self.emit(SIGNAL("layoutChanged()"))
                                self.log.debug0("%s.updateEvent: Links re-sorted, pid:%d" % (self.cname, package.id))
                            if info.status != DownloadStatus.Downloading:
                                self.emit(SIGNAL("notificationMessage"), info.status, child.data["name"])
                        if child.data["status"] > packageStatus:
                            packageStatus = child.data["status"]
                    if linkFound:
                        if packageStatus == DownloadStatus.Finished:
                            self.emit(SIGNAL("notificationMessage"), 100, package.data["name"])
            if not linkFound:
                self.log.debug2("%s.updateEvent: Link not found, fid:%d" % (self.cname, event.id))
                self.setDirty(False)
        
        else: # ElementType.Package
            try:
                data = self.connector.proxy.getPackageData(event.id)
            except PackageDoesNotExists:
                self.log.debug2("%s.updateEvent: No package data received from the server, pid:%d" % (self.cname, event.id))
                self.setDirty(False)
                return
            packageFound = False
            for p, package in enumerate(self._data):
                if package.id == event.id:
                    packageFound = True
                    # manually update the links at first, needed for Api.restartPackage() not sending link update events
                    orderChanged = False
                    for k, child in enumerate(package.children):
                        linkFound = False
                        for filedata in data.links:
                            if filedata.fid == child.id:
                                linkFound = True
                                if filedata.order != child.data["order"]:
                                    orderChanged = True
                                    self.log.warning("%s.updateEvent: Manual link update: Order attribute value differs, fid:%d in pid:%d" % (self.cname, child.id, package.id))
                                child.update(filedata)
                                if not filedata.status == DownloadStatus.Downloading:
                                    child.data["downloading"] = None
                                self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(k, 0, self.index(p, 0)), self.index(k, self.cols, self.index(p, self.cols)))
                                self.log.debug0("%s.updateEvent: Link manually updated, fid:%d in pid:%d" % (self.cname, child.id, package.id))
                                break
                        if not linkFound:
                            self.log.debug2("%s.updateEvent: Manual link update: Link not found in package data received from the server, fid:%d in pid:%d" % (self.cname, child.id, package.id))
                            self.setDirty(False)
                            return
                    if orderChanged:
                        self.emit(SIGNAL("layoutAboutToBeChanged()"))
                        package.sortChildren()
                        self.emit(SIGNAL("layoutChanged()"))
                        self.log.debug0("%s.updateEvent: Manual link update: Links re-sorted, pid:%d" % (self.cname, package.id))
                    # update the package
                    orderChanged = bool(data.order != package.data["order"])
                    package.update(data)
                    self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(p, 0), self.index(p, self.cols))
                    self.log.debug1("%s.updateEvent: Package updated, pid:%d" % (self.cname, package.id))
                    if orderChanged:
                        self.log.debug0("%s.updateEvent: Package order attribute changed, pid:%d" % (self.cname, package.id))
                        self.emit(SIGNAL("layoutAboutToBeChanged()"))
                        self._data = sorted(self._data, key=lambda d: d.data["order"])
                        self.emit(SIGNAL("layoutChanged()"))
                        self.log.debug0("%s.updateEvent: Packages re-sorted" % self.cname)
                    break
            if not packageFound:
                self.log.debug2("%s.updateEvent: Package not found, pid:%d" % (self.cname, event.id))
                self.setDirty(False)
    
    def getStatus(self, item, speed):
        """
            return status str
        """
        status = DownloadStatus.Finished
        if isinstance(item, Package):
            for child in item.children:
                if child.data["status"] > status:
                    status = child.data["status"]
        else:
            status = item.data["status"]
        if speed is None or status == DownloadStatus.Starting or status == DownloadStatus.Decrypting or status == DownloadStatus.Waiting:
            return self.translateStatus(statusMapReverse[status])
        else:
            return "%s (%s)" % (self.translateStatus(statusMapReverse[status]), formatSpeed(speed))
    
    def data(self, index, role=Qt.DisplayRole):
        """
            return cell data
        """
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            if index.column() == 0:   #Name
                return QVariant(index.internalPointer().data["name"])
            elif index.column() == 1: #Plugin
                item = index.internalPointer()
                plugins = []
                if isinstance(item, Package):
                    for child in item.children:
                        if not child.data["plugin"] in plugins:
                            plugins.append(child.data["plugin"])
                else:
                    plugins.append(item.data["plugin"])
                return QVariant(", ".join(plugins))
            elif index.column() == 2: #Status
                item = index.internalPointer()
                return QVariant(self.getStatus(item, None))
            elif index.column() == 3: #Size
                item = index.internalPointer()
                if isinstance(item, Link):
                    return QVariant(formatSize(item.data["size"]))
                else:
                    ms = 0
                    for c in item.children:
                        ms += c.data["size"]
                    return QVariant(formatSize(ms))
            elif index.column() == 4: #Folder
                item = index.internalPointer()
                if isinstance(item, Package):
                    return QVariant(item.data["folder"])
                else:
                    return QVariant()
            elif index.column() == 5: #Password
                item = index.internalPointer()
                if isinstance(item, Package):
                    return QVariant(QString(item.data["password"]).replace('\n', ' ').trimmed())
                else:
                    return QVariant()
            elif index.column() == 6: #ID
                item = index.internalPointer()
                return QVariant(item.id)
            elif index.column() == 7: #Order
                item = index.internalPointer()
                return QVariant(item.data["order"])
        elif role == Qt.ToolTipRole and self.showToolTips:
            rect = self.view.visualRect(index)
            if rect.isValid():
                txt = self.data(index, Qt.DisplayRole).toString()
                textWidth = self.view.fontMetrics().width(txt)
                textWidth += 6
                if textWidth > rect.width():
                    return QVariant(txt)
        return QVariant()
    
    def index(self, row, column, parent=QModelIndex()):
        """
            creates a cell index with pointer to the data
        """
        if row < 0 or column < 0:
            return QModelIndex()
        if parent == QModelIndex() and len(self._data) > row:
            pointer = self._data[row]
            index = self.createIndex(row, column, pointer)
        elif parent.isValid():
            try:
                pointer = parent.internalPointer().children[row]
            except Exception:
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
            elif section == 4:
                return QVariant(_("Folder"))
            elif section == 5:
                return QVariant(_("Password"))
            elif section == 6:
                return QVariant(_("ID"))
            elif section == 7:
                return QVariant(_("Order"))
        return QVariant()
    
    def flags(self, index):
        """
            cell flags
        """
        defaultFlags = QAbstractItemModel.flags(self, index)
        if self.dnd.havePermissions:
            defaultFlags |= Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        else:
            defaultFlags &= ~(Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        return defaultFlags
    
    @classmethod
    def supportedDropActions(self):
        return Qt.MoveAction | Qt.IgnoreAction
    
    def slotDropEvent(self, sortByOrderAttribute):
        QMutexLocker(self.mutex)
        nothingDone = True
        
        if self.dnd.actionOnDrop == self.dnd.ACT.PACKORDER:
            self.dnd.getSrcPackages()
            if self.dnd.srcPackages:
                if sortByOrderAttribute:
                    self.dnd.srcPackages = sorted(self.dnd.srcPackages, key=lambda p: p[1])
                # get the current package order
                unsortedItems = []
                for package in self._data:
                    unsortedItems.append([None, package.id])
                # remove the selected packages
                sortedItems = list(unsortedItems)
                for sl in self.dnd.srcPackages:
                    sortedItems.remove([None, sl[0]])
                # reinsert the selected packages at the drop position
                i = 0
                while i < len(unsortedItems):
                    if sortedItems[i][1] == self.dnd.destPackId:
                        for j in xrange(len(self.dnd.srcPackages)):
                            sortedItems.insert(i + j, [None, self.dnd.srcPackages[j][0]])
                        i += len(self.dnd.srcPackages)
                    i += 1
                # build a list package move commands and send them to the server
                packageMoves = self.smallestListOfItemMoves(unsortedItems, sortedItems)
                for move in packageMoves:
                    self.connector.proxy.orderPackage(move[0], move[1])
                nothingDone = not packageMoves
            else:
                self.log.debug0("%s.slotDropEvent: PACKORDER: selection lost" % self.cname)
        
        elif self.dnd.actionOnDrop == self.dnd.ACT.LINKORDER:
            self.dnd.getSrcLinks()
            if self.dnd.srcLinks:
                if sortByOrderAttribute:
                    self.dnd.srcLinks = sorted(self.dnd.srcLinks, key=lambda p: p[3])
                # get the current link order
                unsortedItems = []
                for package in self._data:
                    if package.id == self.dnd.srcLinksSamePackId:
                        for child in package.children:
                            unsortedItems.append([None, child.id])
                # remove the selected links
                sortedItems = list(unsortedItems)
                for sl in self.dnd.srcLinks:
                    sortedItems.remove([None, sl[0]])
                # reinsert the selected links at the drop position
                i = 0
                while i < len(unsortedItems):
                    if sortedItems[i][1] == self.dnd.destLinkId:
                        for j in xrange(len(self.dnd.srcLinks)):
                            sortedItems.insert(i + j, [None, self.dnd.srcLinks[j][0]])
                        i += len(self.dnd.srcLinks)
                    i += 1
                # build a list link move commands and send them to the server
                linkMoves = self.smallestListOfItemMoves(unsortedItems, sortedItems)
                for move in linkMoves:
                    self.connector.proxy.orderFile(move[0], move[1])
                nothingDone = not linkMoves
            else:
                self.log.debug0("%s.slotDropEvent: LINKORDER: selection lost" % self.cname)
        
        elif self.dnd.actionOnDrop == self.dnd.ACT.LINKMOVE:
            self.dnd.getSrcLinks()
            if self.dnd.srcLinks:
                if sortByOrderAttribute:
                    self.dnd.srcLinks = sorted(self.dnd.srcLinks, key=lambda p: p[3])
                fids = []
                links = []
                for l in self.dnd.srcLinks:
                    fids.append(l[0])
                    links.append(l[1])
                # delete the links from the source package
                self.connector.proxy.deleteFiles(fids)
                # append (recreated) links to the destination package
                self.connector.proxy.addFiles(self.dnd.destPackId, links)
                nothingDone = not fids
            else:
                self.log.debug0("%s.slotDropEvent: LINKMOVE: selection lost" % self.cname)
        
        else:
            raise ValueError("%s: Unknown drop action" % self.cname)
        
        if nothingDone:
            self.view.setEnabled(self.view.corePermissions["LIST"])
            self.view.setFocus(Qt.OtherFocusReason)
        else:
            self.view.clearSelection()
            self.view.setCurrentIndex(QModelIndex())
    
    def advancedSelect(self, pattern, syntax, cs, deselect, selectLinks):
        """
            called from main
        """
        func_start_time = self.time_msec()
        QMutexLocker(self.mutex)
        smodel = self.view.selectionModel()
        rx = QRegExp(pattern, cs, syntax)
        numOfmatches = 0
        
        # select links
        if selectLinks:
            noPackagesSelected = True
            for pindex in smodel.selectedRows(0):  # search in selected packages
                package = pindex.internalPointer()
                if isinstance(package, Package):
                    for l, link in enumerate(package.children):
                        name = QString(link.data["name"])
                        match = name.contains(rx)
                        if match:
                            index = self.index(l, 0, pindex)
                            if not index.isValid():
                                raise ValueError("%s: Invalid index" % self.cname)
                            if not deselect:
                                if not smodel.isSelected(index): smodel.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                                self.view.expand(pindex)
                            else:
                                if smodel.isSelected(index): smodel.select(index, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
                            numOfmatches += 1
                            self.log.debug9("%s.advancedSelect:selectedLink:   deselect:%s   name:'%s'   pid:%d   fid:%d" % (self.cname, deselect, name, package.id, link.id))
                    noPackagesSelected = False
                elif not isinstance(package, Link):
                    raise TypeError("%s: Unknown item instance" % self.cname)
            
            if noPackagesSelected:  # search in all packages
                for p, package in enumerate(self._data):
                    pindex = self.index(p, 0)
                    if not pindex.isValid():
                        raise ValueError("%s: Invalid index" % self.cname)
                    for l, link in enumerate(package.children):
                        name = QString(link.data["name"])
                        match = name.contains(rx)
                        if match:
                            index = self.index(l, 0, pindex)
                            if not index.isValid():
                                raise ValueError("%s: Invalid index" % self.cname)
                            if not deselect:
                                if not smodel.isSelected(index): smodel.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                                self.view.expand(pindex)
                            else:
                                if smodel.isSelected(index): smodel.select(index, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
                            numOfmatches += 1
                            self.log.debug9("%s.advancedSelect:selectedLink:   deselect:%s   name:'%s'   pid:%d   fid:%d" % (self.cname, deselect, name, package.id, link.id))
        
        # select packages
        else:
            for p, package in enumerate(self._data):
                name = QString(package.data["name"])
                match = name.contains(rx)
                if match:
                    index = self.index(p, 0)
                    if not index.isValid():
                        raise ValueError("%s: Invalid index" % self.cname)
                    if not deselect:
                        if not smodel.isSelected(index): smodel.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                    else:
                        if smodel.isSelected(index): smodel.select(index, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
                    numOfmatches += 1
                    self.log.debug9("%s.advancedSelect:selectedPackage:   deselect:%s   name:'%s'   pid:%d" % (self.cname, deselect,name, package.id))
        
        # info text
        if selectLinks:
            if numOfmatches == 0:
                txt = _("No link matches found")
            elif not noPackagesSelected:
                txt = _("Done (%d link matches found in selected packages)") % numOfmatches
            else:
                txt = _("Done (%d link matches found in all packages)") % numOfmatches
        else:
            if numOfmatches == 0:
                txt = _("No package matches found")
            else:
                txt = _("Done (%d package matches found)") % numOfmatches
        self.view.buttonMsgShow(txt, False)
        self.view.buttonMsgHide(2000)
        self.log.debug8("%s.advancedSelect took %dms" % (self.cname, self.time_msec() - func_start_time))
    
    def removePackageDupes(self):
        """
            called from main
        """
        func_start_time = self.time_msec()
        QMutexLocker(self.mutex)
        dupeIds = []
        if len(self._data) > 1:
            for idx, package in enumerate(self._data):
                if package.id in dupeIds:
                    continue
                for package2 in self._data[(idx + 1):]:
                    if package2.data["name"] == package.data["name"]:
                        dupeIds.append(package2.id)
            if len(dupeIds) == 0:
                self.view.buttonMsgShow(_("No duplicate packages found"), False)
            else:
                self.view.buttonMsgShow(_("Removing duplicate packages ..."), False)
                self.view.setEnabled(False)
                self.view.update()
                QApplication.processEvents()
                self.connector.proxy.deletePackages(dupeIds)
                self.view.buttonMsgShow(_("Duplicate packages removed"), False)
        elif len(self._data) == 1:
            self.view.buttonMsgShow(_("Nothing to do, there is only one package"), True)
        else:
            self.view.buttonMsgShow(_("No packages"), True)
        if len(dupeIds) > 0:
            self.view.clearSelection()
            self.view.setCurrentIndex(QModelIndex())
        self.view.buttonMsgHide(3000)
        self.log.debug8("%s.removePackageDupes took %dms" % (self.cname, self.time_msec() - func_start_time))
    
    def removeLinkDupes(self):
        """
            called from main
        """
        func_start_time = self.time_msec()
        QMutexLocker(self.mutex)
        dupeIds = []
        if len(self._data) > 0:
            packsCnt = 0
            smodel = self.view.selectionModel()
            for si in smodel.selectedRows(0):
                item = si.internalPointer()
                if isinstance(item, Package):
                    pindex = si
                    packsCnt += 1
                elif not isinstance(item, Link):
                    raise TypeError("%s: Unknown item instance" % self.cname)
            if packsCnt == 1:
                package = pindex.internalPointer()
                if len(package.children) > 1:
                    for idx, link in enumerate(package.children):
                        if link.id in dupeIds:
                            continue
                        for link2 in package.children[(idx + 1):]:
                            if link2.data["name"] == link.data["name"]:
                                dupeIds.append(link2.id)
                    if len(dupeIds) == 0:
                        self.view.buttonMsgShow(_("No duplicate links found"), False)
                    else:
                        self.view.buttonMsgShow(_("Removing duplicate links ..."), False)
                        self.view.setEnabled(False)
                        self.view.update()
                        self.view.setExpanded(pindex, True)
                        QApplication.processEvents()
                        self.connector.proxy.deleteFiles(dupeIds)
                        self.view.buttonMsgShow(_("Duplicate links removed"), False)
                else:
                    self.view.buttonMsgShow(_("Nothing to do, package has only one link"), False)
            elif packsCnt == 0:
                self.view.buttonMsgShow(_("Select a package!"), True)
            else:
                self.view.buttonMsgShow(_("Select a single package only!"), True)
        else:
            self.view.buttonMsgShow(_("No packages"), True)
        if len(dupeIds) > 0:
            self.view.clearSelection()
            self.view.setCurrentIndex(QModelIndex())
            smodel.select(pindex, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        self.view.buttonMsgHide(3000)
        self.log.debug8("%s.removeLinkDupes took %dms" % (self.cname, self.time_msec() - func_start_time))
    
    def sortPackages(self):
        """
            called from main
        """
        QMutexLocker(self.mutex)
        func_start_time = self.time_msec()
        sortingPerformed = False
        if len(self._data) > 0:
            if len(self._data) > 1:
                packs = []
                for package in self._data:
                    name = package.data["name"]
                    pid  = package.id
                    packs.append([name, pid])
                (sortedPacks, alreadySorted) = self.sortItems(packs)
                if alreadySorted:
                    self.view.buttonMsgShow(_("Nothing to do, packages are already sorted"), False)
                else:
                    self.view.buttonMsgShow(_("Sorting ..."), False)
                    self.view.setEnabled(False)
                    self.view.update()
                    QApplication.processEvents()
                    packMoves = self.smallestListOfItemMoves(packs, sortedPacks)
                    self.log.debug8("%s.sortPackages: %d packMoves build after %dms" % (self.cname, len(packMoves), self.time_msec() - func_start_time))
                    for move in packMoves:
                        self.connector.proxy.orderPackage(move[0], move[1])
                    self.log.debug8("%s.sortPackages: packages sorted after %dms" % (self.cname, self.time_msec() - func_start_time))
                    sortingPerformed = True
                    self.view.buttonMsgShow(_("Packages sorted"), False)
            else:
                self.view.buttonMsgShow(_("Nothing to do, there is only one package"), False)
        else:
            self.view.buttonMsgShow(_("No packages"), True)
        if sortingPerformed:
            self.view.clearSelection()
            self.view.setCurrentIndex(QModelIndex())
        else:
            self.view.buttonMsgHide(3000)
    
    def sortLinks(self):
        """
            called from main
        """
        QMutexLocker(self.mutex)
        func_start_time = self.time_msec()
        sortingPerformed = False
        if len(self._data) > 0:
            numOfSelectedPacks = 0
            smodel = self.view.selectionModel()
            for si in smodel.selectedRows(0):
                item = si.internalPointer()
                if isinstance(item, Package):
                    pindex = si
                    numOfSelectedPacks += 1
                elif not isinstance(item, Link):
                    raise TypeError("%s: Unknown item instance" % self.cname)
            if numOfSelectedPacks == 1:
                package = pindex.internalPointer()
                if len(package.children) > 1:
                    links = []
                    for link in package.children:
                        name = link.data["name"]
                        fid   = link.id
                        links.append([name, fid])
                    (sortedLinks, alreadySorted) = self.sortItems(links)
                    if alreadySorted:
                        self.view.buttonMsgShow(_("Nothing to do, Links are already sorted"), False)
                    else:
                        self.view.buttonMsgShow(_("Sorting ..."), False)
                        self.view.setEnabled(False)
                        self.view.update()
                        QApplication.processEvents()
                        #self.view.setExpanded(pindex, True)
                        linkMoves = self.smallestListOfItemMoves(links, sortedLinks)
                        self.log.debug8("%s.sortLinks: %d linkMoves build after %dms" % (self.cname, len(linkMoves), self.time_msec() - func_start_time))
                        for move in linkMoves:
                            self.connector.proxy.orderFile(move[0], move[1])
                        self.log.debug8("%s.sortLinks: links sorted after %dms" % (self.cname, self.time_msec() - func_start_time))
                        sortingPerformed = True
                        self.view.buttonMsgShow(_("Links sorted"), False)
                else:
                    self.view.buttonMsgShow(_("Nothing to do, package has only one link"), False)
            elif numOfSelectedPacks == 0:
                self.view.buttonMsgShow(_("Select a package!"), True)
            else:
                self.view.buttonMsgShow(_("Select a single package only!"), True)
        else:
            self.view.buttonMsgShow(_("No packages"), True)
        if sortingPerformed:
            self.view.clearSelection()
            self.view.setCurrentIndex(QModelIndex())
            smodel.select(pindex, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        else:
            self.view.buttonMsgHide(3000)
    
    @classmethod
    def sortItems(self, items):
        """
            Natural sorting of package/link names
                items: [[name, id], ..., ....]
        """
        sortedItems = sorted(items, key = lambda il: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', il[0])])   # http://stackoverflow.com/a/16090640
        alreadySorted = True
        for i in xrange(len(items)):
            if items[i][1] != sortedItems[i][1]:   # id
                alreadySorted = False
                break
        return (sortedItems, alreadySorted)
    
    def smallestListOfItemMoves(self, unsortedItems, sortedItems):
        """
            Calculates the smallest possible amount of item moves
            for sorting a list of links or packages.
                unsortedItems: [[name, id], ...]
                sortedItems:   [[name, id], ...]
                Note: The value of 'name' does not matter here
            Returns a list of (id, position) tuples for feeding to api.orderFile or api.orderPackage.
        """
        items = list(unsortedItems)
        id2SortedItemPos = {id: pos for pos, (dummy, id) in enumerate(sortedItems)}
        seq = []
        for i in xrange(len(items)):
            seq.append(id2SortedItemPos[items[i][1]])
        lis = longestSubsequence(seq)
        itemMoves = []
        for i in xrange(len(items)):
            if i >= len(lis) or lis[i] != i:
                id = sortedItems[i][1]
                # update the 'items' array
                for j in xrange(len(items)):
                    if items[j][1] == id: break
                item = items.pop(j)
                j = id2SortedItemPos[id]
                if j > 0:
                    previousId = sortedItems[j - 1][1]
                    for k in xrange(len(items)):
                        if items[k][1] == previousId: break
                    j = k + 1
                    if j > len(items): raise RuntimeError("%s: j > len(items)" % self.cname)
                items.insert(j, item)
                # update 'lis'
                lis.insert(i, i)
                # add to list
                itemMoves.append((id, j)) # (id, pos)
        # sanity checks
        if len(lis) != len(items): raise RuntimeError("%s: len(lis) != len(items)" % self.cname)
        for i in xrange(len(lis)):
            if lis[i] != i: raise RuntimeError("%s: lis[i] != i" % self.cname)
        if len(items) != len(sortedItems): raise RuntimeError("%s: len(items) != len(sortedItems)" % self.cname)
        for i in xrange(len(items)):
            if items[i][1] != sortedItems[i][1]: raise RuntimeError("%s: items != sortedItems" % self.cname)
        return itemMoves

class Package(object):
    """
        package object in the model
    """
    
    def __init__(self, pack):
        self.log = logging.getLogger("guilog")
        
        self.id = pack.pid
        self.children = []
        for f in pack.links:
            self.addChild(f)
        self.sortChildren()
        self.data = {}
        self.update(pack)
    
    def update(self, pack):
        """
            update data dict from thrift object
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
        self.children.append(Link(f, self))
    
    def sortChildren(self):
        """
            sort children (Links) of package
        """
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
        self.log = logging.getLogger("guilog")
        
        self.data = {"downloading": None}
        self.update(f)
        self.id = f.fid
        self.package = pack
    
    def update(self, f):
        """
            update data dict from thrift object
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
    
    def __init__(self, corePermissions, connector):
        QTreeView.__init__(self)
        self.cname = self.__class__.__name__
        self.log = logging.getLogger("guilog")
        self.corePermissions = corePermissions
        self.model = CollectorModel(self, connector)
        self.setModel(self.model)
        
        self.buttonMsgHideTimer = QTimer()
        
        wt = _(
        "- Column visibility can be toggled by right-clicking on the header row<br>"
        "- Column order can be changed by Drag'n'Drop<br>"
        "- Context menu by right-clicking on selected items, on the expand/collapse arrows or on the empty bottom area of the view<br>"
        "- Package order can be changed by Drag'n'Drop<br>"
        "- Link order within a package can be changed by Drag'n'Drop"
        )
        wt += _("<br>- Links can be moved to another package by Drag'n'Drop")
        self.setWhatsThis(whatsThisFormat(_("Collector View"), wt))
        
        self.setColumnHidden(0, False) # Name
        self.setColumnHidden(1, False) # Plugin
        self.setColumnHidden(2, False) # Status
        self.setColumnHidden(3, False) # Size
        self.setColumnHidden(4, False) # Folder
        self.setColumnHidden(5, False) # Password
        self.setColumnHidden(6, True)  # ID
        self.setColumnHidden(7, True)  # Order
        
        self.setColumnWidth(0, 350)
        self.setColumnWidth(1, 110)
        self.setColumnWidth(2, 70)
        self.setColumnWidth(3, 70)
        self.setColumnWidth(4, 150)
        self.setColumnWidth(5, 100)
        self.setColumnWidth(6, 60)
        
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.header().setContextMenuPolicy(Qt.CustomContextMenu)
        self.header().customContextMenuRequested.connect(self.headerContextMenu)
        
        self.connect(self.buttonMsgHideTimer, SIGNAL("timeout()"), self.buttonMsgHideTimerTimeout)
        self.connect(self, SIGNAL("dropEvent"), self.model.slotDropEvent)
        self.connect(self, SIGNAL("collapsed(const QModelIndex &)"), self.packageCollapsed)
    
    def setCorePermissions(self, corePermissions):
        self.corePermissions = corePermissions
        # PACKORDER + LINKORDER need "MODIFY ; LINKMOVE needs "DELETE" and "ADD"
        if self.corePermissions["MODIFY"] or (self.corePermissions["DELETE"] and self.corePermissions["ADD"]):
            self.model.dnd.havePermissions = True
        else:
            self.model.dnd.havePermissions = False
        self.log.debug9("%s.setCorePermissions: dnd.havePermissions set to: %s" % (self.cname, str(self.model.dnd.havePermissions)))
    
    def headerContextMenu(self, pos):
        """
            header row popup menu for hiding/showing columns
        """
        menu = QMenu()
        for i in range(0, self.model.columnCount()):
            name = self.model.headerData(i, Qt.Horizontal).toString()
            if not name.isEmpty():
                act = menu.addAction(name)
                act.setCheckable(True)
                act.setChecked(not self.isColumnHidden(i))
                if i == 0: # Name
                    act.setDisabled(True)
        act = menu.exec_(self.mapToGlobal(pos))
        if act:
            for columnToToggle in range(0, self.model.columnCount()):
                if self.model.headerData(columnToToggle, Qt.Horizontal).toString() == act.text():
                    break
            if self.isColumnHidden(columnToToggle):
                # get the sorted index of the most right visible column
                mrvi = -1
                for i in range(0, self.model.columnCount()):
                    if not self.isColumnHidden(i):
                        vi = self.header().visualIndex(i)
                        if vi > mrvi:
                            mrvi = vi
                if mrvi < self.header().visualIndex(columnToToggle):
                    # narrow it
                    columnToNarrow = self.header().logicalIndex(mrvi)
                    self.resizeColumnToContents(columnToNarrow)
                self.showColumn(columnToToggle)
            else:
                self.hideColumn(columnToToggle)
    
    def treeExpandAll(self):
        self.expandToDepth(1)
    
    def treeCollapseAll(self):
        for i in range(0, self.model.rowCount()):
            self.collapse(self.model.index(i, 0))
    
    def packageCollapsed(self, index):
        func_start_time = self.model.time_msec()
        package = index.internalPointer()
        if not isinstance(package, Package):
            raise TypeError("%s: Bad item instance" % self.cname)
        smodel = self.selectionModel()
        for l in xrange(len(package.children)):
            lindex = self.model.index(l, 0, index)
            if not lindex.isValid():
                raise ValueError("%s: Invalid index" % self.cname)
            if smodel.isSelected(lindex): smodel.select(lindex, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
            if lindex == smodel.currentIndex():
                smodel.setCurrentIndex(QModelIndex(), QItemSelectionModel.NoUpdate)
        self.log.debug8("%s.packageCollapsed took %dms" % (self.cname, self.model.time_msec() - func_start_time))
    
    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            vr = self.visualRect(index)
            indent = vr.x() - self.visualRect(self.rootIndex()).x()
            if event.pos().x() < indent: # expand/collapse arrow clicked
                if event.buttons() == Qt.RightButton:
                    return
        QTreeView.mousePressEvent(self, event)
    
    def dragEnterEvent(self, event):
        if event.source() != self:
            return
        event.accept()
    
    def dragMoveEvent(self, event):
        if event.source() != self:
            return
        event.ignore()
        self.model.dnd.canDrop(event.pos())
        if self.model.dnd.actionOnDrop == self.model.dnd.ACT.PACKORDER and not self.corePermissions["MODIFY"]:
            self.log.debug3("%s.dragMoveEvent: PACKORDER: insufficient corePermissions" % self.cname)
            self.model.dnd.actionOnDrop = self.model.dnd.ACT.NONE
        elif self.model.dnd.actionOnDrop == self.model.dnd.ACT.LINKORDER and not self.corePermissions["MODIFY"]:
            self.log.debug3("%s.dragMoveEvent: LINKORDER: insufficient corePermissions" % self.cname)
            self.model.dnd.actionOnDrop = self.model.dnd.ACT.NONE
        elif self.model.dnd.actionOnDrop == self.model.dnd.ACT.LINKMOVE and not (self.corePermissions["DELETE"] and self.corePermissions["ADD"]):
            self.log.debug3("%s.dragMoveEvent: LINKMOVE: insufficient corePermissions" % self.cname)
            self.model.dnd.actionOnDrop = self.model.dnd.ACT.NONE
        if self.model.dnd.actionOnDrop == self.model.dnd.ACT.NONE:
            event.setDropAction(Qt.IgnoreAction)
        else:
            event.setDropAction(Qt.MoveAction)
        QTreeView.dragMoveEvent(self, event)
    
    def dragLeaveEvent(self, event):
        event.ignore()
        self.buttonMsgHide(0)
    
    def dropEvent(self, event):
        if event.source() != self:
            return
        event.ignore()
        if self.model.dnd.actionOnDrop == self.model.dnd.ACT.NONE:
            return
        self.buttonMsgHide(0)
        self.setEnabled(False)
        self.emit(SIGNAL("dropEvent"), not bool(event.keyboardModifiers() & Qt.AltModifier))
    
    def buttonMsgShow(self, msg, error):
        self.buttonMsgHideTimer.stop()
        self.emit(SIGNAL("collectorMsgShow"), msg, error)
    
    def buttonMsgHide(self, delay):
        self.buttonMsgHideTimer.setInterval(delay)
        self.buttonMsgHideTimer.setSingleShot(True)
        self.buttonMsgHideTimer.start()
    
    def buttonMsgHideTimerTimeout(self):
        self.emit(SIGNAL("collectorMsgHide"))

class DragAndDrop(QObject):
    """
        Drag and Drop for collector view
    """
    def __init__(self, view, model):
        QObject.__init__(self)
        self.log = logging.getLogger("guilog")
        self.view = view
        self.model = model
        self.cname = model.__class__.__name__ + "." + self.__class__.__name__
        
        self.buttonMsgCanDrop = _("To drop the items in the order they were selected, hold the ALT key when releasing the mouse button!")
        self.viewDesc = _("Collector View") if self.view.__class__.__name__ == "CollectorView" else _("Queue View")
        
        self.allowLinkMove = False
        
        self.destRow            = None
        self.destIsPack         = None
        self.destPackId         = None
        self.destPackOrder      = None
        self.destLinkId         = None
        self.destLinkOrder      = None
        self.srcLinks           = None
        self.srcPacksCnt        = None
        self.srcLinksCnt        = None
        self.srcLinksSamePack   = None
        self.srcLinksSamePackId = None
        self.srcPackages        = None
        self.actionOnDrop       = None

    # enum for actionOnDrop
    class ACT:
        PACKORDER = 1
        LINKORDER = 2
        LINKMOVE  = 3
        NONE      = 4

    def getDestInfo(self, pos):
        """
            Get info about the item we drop the selection on
            Sets: destRow       (package row or link row)
                  destIsPack    (package or link?)
                  destPackId    (package id, or parent package id in case of link)
                  destPackOrder (package order attribute)
                  destLinkId    (link id)
                  destLinkOrder (link order attribute)
            Returns: True on success, False if the index is invalid
        """
        i = self.view.indexAt(pos)     # 'QModelIndex' object
        if i == QModelIndex():
            return False
        dest = i.internalPointer()     # 'Package' object
        if not dest:
            raise RuntimeError("%s: No target item, 'Package' object" % self.cname)
        self.destRow = i.row()
        if isinstance(dest, Package):
            self.destIsPack = True
            self.destPackId = dest.id
            self.destPackOrder = dest.data["order"]
            self.log.debug4("%s.getDestInfo: PACK:   row: %d   pid: %d" % (self.cname, self.destRow, self.destPackId))
        elif isinstance(dest, Link):
            self.destIsPack = False
            self.destPackId = dest.data["package"]
            self.destLinkId = dest.id
            self.destLinkOrder = dest.data["order"]
            self.log.debug4("%s.getDestInfo: LINK:   row: %d   id:%d   pid: %d" % (self.cname, self.destRow, self.destLinkId, self.destPackId))
        else:
            raise TypeError("%s: Unknown item instance" % self.cname)
        return True

    def getSrcInfo(self):
        """
            Count the selected packages and links and check if the links are from the same package
            Sets: srcPacksCnt
                  srcLinksCnt
                  srcLinksSamePack
                  srcLinksSamePackId
        """
        func_start_time = self.model.time_msec()
        
        self.srcPacksCnt = 0
        self.srcLinksCnt = 0
        
        smodel = self.view.selectionModel()
        for si in smodel.selectedRows(0):
            src = si.internalPointer()
            if isinstance(src, Package):
                self.srcPacksCnt += 1
                self.log.debug4("%s.getSrcInfo: PACK:   name:'%s'   order:'%s'   pid:%s" % (self.cname, src.data["name"], src.data["order"], src.id))
            elif isinstance(src, Link):
                self.srcLinksCnt += 1
                self.log.debug4("%s.getSrcInfo: LINK:   name:'%s'   order:'%s'   id:%d   pid:%s" % (self.cname, src.data["name"], src.data["order"], src.id, src.data["package"]))
            else:
                raise TypeError("%s: Unknown item instance" % self.cname)
        self.log.debug4("%s.getSrcInfo: Selection count:   PACKS:%d   LINKS:%d" % (self.cname, self.srcPacksCnt, self.srcLinksCnt))
        
        # check links
        self.srcLinksSamePack = True
        if self.srcLinksCnt > 0:
            pidcnt = 0
            lastpid = -1
            for si in smodel.selectedRows(0):
                src = si.internalPointer()
                if not isinstance(src, Link):
                    continue
                self.srcLinksSamePackId = src.data["package"]   # PackageID (int)
                self.log.debug4("%s.getSrcInfo: check links:   name:'%s'   order:'%s'   id:%d   pid:%s" % (self.cname, src.data["name"], src.data["order"], src.id, self.srcLinksSamePackId))
                if self.srcLinksSamePackId != lastpid:
                    lastpid = self.srcLinksSamePackId
                    pidcnt += 1
                    if pidcnt > 1:
                        self.srcLinksSamePack = False
                        break

        self.log.debug8("%s.getSrcInfo took %dms" % (self.cname, self.model.time_msec() - func_start_time))

    def getSrcPackages(self):
        """
            Get the selected packages
            Sets: srcPackages[[pid, order, row]]
        """
        func_start_time = self.model.time_msec()
        self.srcPackages = []
        
        smodel = self.view.selectionModel()
        for si in smodel.selectedRows(0):
            src = si.internalPointer()
            if isinstance(src, Package):
                pid   = src.id
                order = src.data["order"]
                row = si.row()
                self.log.debug4("%s.getSrcPackages:   pid:%d   order:%d   row:%d" % (self.cname, pid, order, row))
                self.srcPackages.append([pid, order, row])
        self.log.debug8("%s.getSrcPackages took %dms" % (self.cname, self.model.time_msec() - func_start_time))

    def getSrcLinks(self):
        """
            Get the selected links
            Sets: srcLinks[[id, url, pid, order, row]]
        """
        func_start_time = self.model.time_msec()
        self.srcLinks = []
        
        smodel = self.view.selectionModel()
        for si in smodel.selectedRows(0):
            src = si.internalPointer()
            if isinstance(src, Link):
                id    = src.id
                url   = src.data["url"]
                pid   = src.data["package"]
                order = src.data["order"]
                row = si.row()
                self.log.debug4("%s.getSrcLinks:   id:%d   url:'%s'   pid:%d   order:%d   row:%d" % (self.cname, id, url, pid, order, row))
                self.srcLinks.append([id, url, pid, order, row])
        self.log.debug8("%s.getSrcLinks took %dms" % (self.cname, self.model.time_msec() - func_start_time))

    def canDrop(self, pos):
        """
            Check if we can drop the selection at the mouse cursor position
            Sets: actionOnDrop
            On LINKMOVE it calls getSrcLinks() and therefore also
                Sets: srcLinks[[id, url, pid, order]]
            
            Actions on drop:
                selection: packages
                    target: other package
                        action PACKORDER: move packages to the target position
                selection: links from the same package
                      target: other link within the package
                          action LINKORDER: move links to the target position (for link ordering in a package)
                selection: links
                      target: other package
                          action LINKMOVE: move links to the target package
                selection: packages and links
                      action NONE: no action
        """
        ACT = self.ACT
        self.actionOnDrop = ACT.NONE
        if not self.getDestInfo(pos):
            self.view.buttonMsgHide(0)
            self.log.debug4("%s.canDrop: Invalid drop location" % self.cname)
            return
        self.getSrcInfo()
        srcLinkStr = _("link") if self.srcLinksCnt == 1 else _("links")
        if self.srcPacksCnt > 0 and self.srcLinksCnt > 0:
            self.view.buttonMsgShow(_("Operation not supported: mixed selection of packages and links"), True)
            self.log.debug4("%s.canDrop: Invalid selection, packages and links" % self.cname)
            return
        if self.srcPacksCnt > 0:
            # packages selected
            if self.destIsPack:
                self.view.buttonMsgShow(self.buttonMsgCanDrop, False)
                self.actionOnDrop = ACT.PACKORDER
            else:
                self.view.buttonMsgShow(_("Operation not supported: dropping packages on links"), True)
                self.log.debug4("%s.canDrop: Can't drop packages on a link" % self.cname)
            return
        else:
            # links selected
            if self.srcLinksSamePack and not self.destIsPack:
                # drop links from the same package on a link
                if self.destPackId == self.srcLinksSamePackId:
                    self.view.buttonMsgShow(self.buttonMsgCanDrop, False)
                    self.actionOnDrop = ACT.LINKORDER
                else:
                    self.view.buttonMsgShow(_("Operation not supported, drop the %s on the corresponding package instead!") % srcLinkStr, True)
                    self.log.debug4("%s.canDrop: Can't drop links from the same package on a link from a different package" % self.cname)
                return
            if self.destIsPack:
                # drop links on a package
                self.getSrcLinks()
                if not self.srcLinks:
                    self.view.buttonMsgShow(_("Error: selection lost"), True)
                    self.log.warning("%s.canDrop: Selection lost" % self.cname)
                    return
                # check selected links' package ids against target package id
                for l in self.srcLinks:
                    if l[2] == self.destPackId:
                        self.view.buttonMsgShow(_("Operation not supported: dropping links on their own package"), True)
                        self.log.debug4("%s.canDrop: Can't move links from their own package to their own package" % self.cname)
                        return
                if not self.allowLinkMove:
                    self.view.buttonMsgShow(_("Operation not allowed in the %s: moving links between packages") % self.viewDesc, True)
                    self.log.debug4("%s.canDrop: Moving links from package to package is disabled (self.allowLinkMove)" % self.cname)
                    return
                self.view.buttonMsgShow(self.buttonMsgCanDrop, False)
                self.actionOnDrop = ACT.LINKMOVE
                return
            self.view.buttonMsgShow(_("Operation not supported, drop the %s on the corresponding package instead!") % srcLinkStr, True)
            self.log.debug4("%s.canDrop: Can't drop links not from the same package on a link" % self.cname)
            return

