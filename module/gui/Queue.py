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

from PyQt4.QtCore import QModelIndex, QMutexLocker, QObject, QString, Qt, QTimer, QVariant, SIGNAL
from PyQt4.QtGui import QAbstractItemView, QApplication, QItemDelegate, QStyle, QStyleOptionProgressBarV2, QTreeView

import logging
from time import time

from module.gui.Collector import CollectorModel, Package, Link, CollectorView
from module.remote.thriftbackend.ThriftClient import Destination, DownloadStatus
from module.utils import formatSize
from module.gui.Tools import whatsThisFormat

class QueueModel(CollectorModel):
    """
        model for the queue view, inherits from CollectorModel
    """
    
    def __init__(self, view, connector):
        CollectorModel.__init__(self, view, connector)
        self.log = logging.getLogger("guilog")
        
        self.cols = 10
        self.dnd.allowLinkMove = False
        
        self.wait_dict = {}
        
        self.updater = self.QueueUpdater(self.interval)
        self.connect(self.updater, SIGNAL("update()"), self.update)
    
    class QueueUpdater(QObject):
        """
            timer which emits signal for a download status reload
            @TODO: make intervall configurable
        """
        
        def __init__(self, interval):
            QObject.__init__(self)
            
            self.interval = interval
            self.timer = QTimer()
            self.timer.connect(self.timer, SIGNAL("timeout()"), self, SIGNAL("update()"))
        
        def start(self):
            self.timer.start(1000)
        
        def stop(self):
            self.timer.stop()
    
    def start(self):
        self.updater.start()
    
    def stop(self):
        self.updater.stop()
    
    def fullReload(self, enableView=True):
        """
            reimplements CollectorModel.fullReload, because we want the Queue data
        """
        func_start_time = self.time_msec()
        self.lastFullReload = time()
        self.saveViewItemStates()
        self.beginResetModel()
        self._data = []
        self.endResetModel()
        downloading = self.connector.proxy.statusDownloads()
        order = self.connector.proxy.getPackageOrder(Destination.Queue)
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
            if downloading:
                for idx, d in reversed(list(enumerate(downloading))):
                    child = package.getChild(d.fid)
                    if child:
                        dd = {
                            "name": d.name,
                            "speed": d.speed,
                            "eta": d.eta,
                            "format_eta": d.format_eta,
                            "bleft": d.bleft,
                            "size": d.size,
                            "format_size": d.format_size,
                            "percent": d.percent,
                            "status": d.status,
                            "statusmsg": d.statusmsg,
                            "format_wait": d.format_wait,
                            "wait_until": d.wait_until
                        }
                        child.data["downloading"] = dd
                        del downloading[idx] #might speed up things when there are many files in the queue
            self._data.append(package)
        self.endInsertRows()
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self._data = sorted(self._data, key=lambda p: p.data["order"])
        self.emit(SIGNAL("layoutChanged()"))
        self.dirty = False
        self.fullReloadCheck()
        if enableView:
            self.view.setEnabled(self.view.corePermissions["LIST"])
        self.updateCount()
        self.applyViewItemStates()
        self.log.debug8("%s.fullReload took %dms" % (self.cname, self.time_msec() - func_start_time))
    
    def insertEvent(self, event):
        """
            wrap CollectorModel.insertEvent to update the element count
        """
        CollectorModel.insertEvent(self, event)
        if not self.dirty:
            self.updateCount()
    
    def removeEvent(self, event):
        """
            wrap CollectorModel.removeEvent to update the element count
        """
        CollectorModel.removeEvent(self, event)
        if not self.dirty:
            self.updateCount()
    
    def updateEvent(self, event):
        """
            wrap CollectorModel.updateEvent to update the element count
        """
        CollectorModel.updateEvent(self, event)
        if not self.dirty:
            self.updateCount()
    
    def updateCount(self):
        """
            calculate package- and filecount for statusbar,
            ugly?: Overview connects to this signal for updating
        """
        packageCount = len(self._data)
        fileCount = 0
        for p in self._data:
            fileCount += len(p.children)
        self.emit(SIGNAL("updateCount"), packageCount, fileCount)
    
    def update(self):
        """
            update slot for download status updating
        """
        if not self.view.corePermissions["LIST"]:
            return
        locker = QMutexLocker(self.mutex)
        downloading = self.connector.proxy.statusDownloads()
        if not downloading:
            return
        for p, pack in enumerate(self._data):
            for idx, d in reversed(list(enumerate(downloading))):
                child = pack.getChild(d.fid)
                if child:
                    dd = {
                        "name": d.name,
                        "speed": d.speed,
                        "eta": d.eta,
                        "format_eta": d.format_eta,
                        "bleft": d.bleft,
                        "size": d.size,
                        "format_size": d.format_size,
                        "percent": d.percent,
                        "status": d.status,
                        "statusmsg": d.statusmsg,
                        "format_wait": d.format_wait,
                        "wait_until": d.wait_until
                    }
                    child.data["downloading"] = dd
                    k = pack.getChildKey(d.fid)
                    self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(k, 0, self.index(p, 0)), self.index(k, self.cols, self.index(p, self.cols)))
                    del downloading[idx] #might speed up things when there are many files in the queue
        packageCount = len(self._data)
        fileCount = 0
        for p in self._data:
            fileCount += len(p.children)
        locker.unlock()
        self.emit(SIGNAL("updateCount"), packageCount, fileCount)
                    
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
                return QVariant(_("ETA"))
            elif section == 5:
                return QVariant(_("Progress"))
            elif section == 6:
                return QVariant(_("Folder"))
            elif section == 7:
                return QVariant(_("Password"))
            elif section == 8:
                return QVariant(_("ID"))
            elif section == 9:
                return QVariant(_("Order"))
        return QVariant()
    
    def getWaitingProgress(self, item):
        """
            returns time to wait, caches startingtime to provide progress
        """
        locker = QMutexLocker(self.mutex)
        if isinstance(item, Link):
            if item.data["status"] == DownloadStatus.Waiting and item.data["downloading"]:
                until = float(item.data["downloading"]["wait_until"])
                try:
                    since, until_old = self.wait_dict[item.id]
                    if not until == until_old:
                        raise Exception
                except:
                    since = time()
                    self.wait_dict[item.id] = since, until
                since = float(since)
                max_wait = float(until-since)
                rest = int(until-time())
                if rest < 0:
                    return 0, None
                res = 100/max_wait
                perc = rest*res
                return perc, rest
        return None
    
    def getProgress(self, item, locked=True):
        """
            return download progress, locks by default
            since it's used in already locked calls,
            it provides an option to not lock
        """
        if locked:
            locker = QMutexLocker(self.mutex)
        if isinstance(item, Link):
            try:
                if item.data["status"] == DownloadStatus.Finished:
					return 100
                return int(item.data["downloading"]["percent"])
            except:
                return 0
        elif isinstance(item, Package):
            count = len(item.children)
            perc_sum = 0
            for child in item.children:
                try:
                    if child.data["status"] == DownloadStatus.Finished:
                        perc_sum += 100
                    perc_sum += int(child.data["downloading"]["percent"])
                except:
                    pass
            if count == 0:
                return 0
            return perc_sum/count
        return 0
    
    def getSpeed(self, item):
        """
            calculate download speed
        """
        if isinstance(item, Link):
            if item.data["downloading"]:
                return int(item.data["downloading"]["speed"])
        elif isinstance(item, Package):
            count = len(item.children)
            speed_sum = 0
            all_waiting = True
            running = False
            for child in item.children:
                val = 0
                if child.data["downloading"]:
                    if not child.data["statusmsg"] == "waiting":
                        all_waiting = False
                    val = int(child.data["downloading"]["speed"])
                    running = True
                speed_sum += val
            if count == 0 or not running or all_waiting:
                return None
            return speed_sum
        return None
    
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
                speed = self.getSpeed(item)
                return QVariant(self.getStatus(item, speed))
            elif index.column() == 3: #Size
                item = index.internalPointer()
                if isinstance(item, Link):
                    if item.data["status"] == DownloadStatus.Finished: #TODO needs change??
		            #self.getProgress(item, False) == 100:
                        return QVariant(formatSize(item.data["size"]))
                    elif self.getProgress(item, False) == 0:
                        try:
                            return QVariant("%s / %s" % (formatSize(item.data["size"]-item.data["downloading"]["bleft"]), formatSize(item.data["size"])))
                        except:
                            return QVariant("0 B / %s" % formatSize(item.data["size"]))
                    else:
                        try:
                            return QVariant("%s / %s" % (formatSize(item.data["size"]-item.data["downloading"]["bleft"]), formatSize(item.data["size"])))
                        except:
                            return QVariant("? / %s" % formatSize(item.data["size"]))
                else:
                    ms = 0
                    cs = 0
                    for c in item.children:
                        try:
                            s = c.data["downloading"]["size"]
                        except:
                            s = c.data["size"]
                        if c.data["downloading"]:
                            cs += s - c.data["downloading"]["bleft"]
                        elif self.getProgress(c, False) == 100:
                            cs += s
                        ms += s
                    if cs == 0 or cs == ms:
                        return QVariant(formatSize(ms))
                    else:
                        return QVariant("%s / %s" % (formatSize(cs), formatSize(ms)))
            elif index.column() == 4: #ETA
                item = index.internalPointer()
                if isinstance(item, Link):
                    if item.data["downloading"]:
                        return QVariant(item.data["downloading"]["format_eta"])
            elif index.column() == 6: #Folder
                item = index.internalPointer()
                if isinstance(item, Package):
                    return QVariant(item.data["folder"])
                else:
                    return QVariant()
            elif index.column() == 7: #Password
                item = index.internalPointer()
                if isinstance(item, Package):
                    return QVariant(QString(item.data["password"]).replace('\n', ' ').trimmed())
                else:
                    return QVariant()
            elif index.column() == 8: #ID
                item = index.internalPointer()
                return QVariant(item.id)
            elif index.column() == 9: #Order
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
    
class QueueView(CollectorView):
    """
        view component for queue
    """
    
    def __init__(self, corePermissions, connector):
        QTreeView.__init__(self)
        self.cname = self.__class__.__name__
        self.log = logging.getLogger("guilog")
        self.corePermissions = corePermissions
        self.model = QueueModel(self, connector)
        self.setModel(self.model)
        
        self.buttonMsgHideTimer = QTimer()
        
        wt = _(
        "- Column visibility can be toggled by right-clicking on the header row<br>"
        "- Column order can be changed by Drag'n'Drop<br>"
        "- Context menu by right-clicking on selected items, on the expand/collapse arrows or on the empty bottom area of the view<br>"
        "- Package order can be changed by Drag'n'Drop<br>"
        "- Link order within a package can be changed by Drag'n'Drop"
        )
        self.setWhatsThis(whatsThisFormat(_("Queue View"), wt))
        
        self.setColumnHidden(0, False) # Name
        self.setColumnHidden(1, False) # Status
        self.setColumnHidden(2, False) # Plugin
        self.setColumnHidden(3, False) # Size
        self.setColumnHidden(4, False) # ETA
        self.setColumnHidden(5, False) # Progress
        self.setColumnHidden(6, False) # Folder
        self.setColumnHidden(7, False) # Password
        self.setColumnHidden(8, True)  # ID
        self.setColumnHidden(9, True)  # Order
        
        self.setColumnWidth(0, 180)
        self.setColumnWidth(1, 110)
        self.setColumnWidth(2, 70)
        self.setColumnWidth(3, 70)
        self.setColumnWidth(4, 70)
        self.setColumnWidth(5, 100)
        self.setColumnWidth(6, 150)
        self.setColumnWidth(7, 100)
        self.setColumnWidth(8, 60)
        
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.header().setContextMenuPolicy(Qt.CustomContextMenu)
        self.header().customContextMenuRequested.connect(self.headerContextMenu)
        
        self.connect(self.buttonMsgHideTimer, SIGNAL("timeout()"), self.buttonMsgHideTimerTimeout)
        self.connect(self, SIGNAL("dropEvent"), self.model.slotDropEvent)
        self.connect(self, SIGNAL("collapsed(const QModelIndex &)"), self.packageCollapsed)
        
        self.delegate = QueueProgressBarDelegate(self, self.model)
        self.setItemDelegateForColumn(5, self.delegate)
    
    def buttonMsgShow(self, msg, error):
        self.buttonMsgHideTimer.stop()
        self.emit(SIGNAL("queueMsgShow"), msg, error)
    
    def buttonMsgHideTimerTimeout(self):
        self.emit(SIGNAL("queueMsgHide"))

class QueueProgressBarDelegate(QItemDelegate):
    """
        used to display a progressbar in the progress cell
    """
    
    def __init__(self, parent, queue):
        QItemDelegate.__init__(self, parent)
        self.log = logging.getLogger("guilog")
        self.queue = queue
    
    def paint(self, painter, option, index):
        """
            paint the progressbar
        """
        if not index.isValid():
            return
        if index.column() == 5: #Progress
            item = index.internalPointer()
            w = self.queue.getWaitingProgress(item)
            wait = None
            if w:
                progress = w[0]
                wait = w[1]
            else:
                progress = self.queue.getProgress(item)
            opts = QStyleOptionProgressBarV2()
            opts.maximum = 100
            opts.minimum = 0
            opts.progress = progress
            opts.rect = option.rect
            opts.rect.setRight(option.rect.right()-1)
            opts.rect.setHeight(option.rect.height()-1)
            opts.textVisible = True
            opts.textAlignment = Qt.AlignCenter
            if not wait is None:
                opts.text = QString(_("waiting %d seconds") % wait)
            else:
                opts.text = QString.number(opts.progress) + "%"
            QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)
            return
        QItemDelegate.paint(self, painter, option, index)

