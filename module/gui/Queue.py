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

from time import sleep, time

from module.gui.Collector import CollectorModel, Package, Link, CollectorView, statusMap, statusMapReverse

class QueueModel(CollectorModel):
    def __init__(self, view, connector):
        CollectorModel.__init__(self, view, connector)
        self.cols = 6
        self.wait_dict = {}
        
        self.updater = self.QueueUpdater(self.interval)
        self.connect(self.updater, SIGNAL("update()"), self.update)
    
    class QueueUpdater(QObject):
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
    
    def fullReload(self):
        self._data = []
        packs = self.connector.getPackageQueue()
        self.beginInsertRows(QModelIndex(), 0, len(packs))
        for pid, data in packs.items():
            package = Package(pid, data)
            self._data.append(package)
        self._data = sorted(self._data, key=lambda p: p.data["order"])
        self.endInsertRows()
    
    def update(self):
        locker = QMutexLocker(self.mutex)
        downloading = self.connector.getDownloadQueue()
        if downloading is None:
            return
        for p, pack in enumerate(self._data):
            for d in downloading:
                child = pack.getChild(d["id"])
                if child:
                    child.data["downloading"] = d
                    k = pack.getChildKey(d["id"])
                    self.emit(SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"), self.index(k, 0, self.index(p, 0)), self.index(k, self.cols, self.index(p, self.cols)))
                    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return QVariant(_("Name"))
            elif section == 2:
                return QVariant(_("Status"))
            elif section == 1:
                return QVariant(_("Plugin"))
            elif section == 3:
                return QVariant(_("Priority"))
            elif section == 4:
                return QVariant(_("ETA"))
            elif section == 5:
                return QVariant(_("Progress"))
        return QVariant()
    
    def getWaitingProgress(self, item):
        locker = QMutexLocker(self.mutex)
        if isinstance(item, Link):
            if item.data["status"] == 5 and item.data["downloading"]:
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
                res = 100/max_wait
                perc = rest*res
                return perc, rest
        return None
    
    def getProgress(self, item):
        locker = QMutexLocker(self.mutex)
        if isinstance(item, Link):
            if item.data["downloading"]:
                return int(item.data["downloading"]["percent"])
            if item.data["statusmsg"] == "finished" or \
                  item.data["statusmsg"] == "failed" or \
                  item.data["statusmsg"] == "aborted":
                return 100
        elif isinstance(item, Package):
            count = len(item.children)
            perc_sum = 0
            for child in item.children:
                val = 0
                if child.data["downloading"]:
                    val = int(child.data["downloading"]["percent"])
                elif child.data["statusmsg"] == "finished" or \
                        child.data["statusmsg"] == "failed" or \
                        child.data["statusmsg"] == "aborted":
                    val = 100
                perc_sum += val
            if count == 0:
                return 0
            return perc_sum/count
        return 0
    
    def getSpeed(self, item):
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
                speed = self.getSpeed(item)
                if isinstance(item, Package):
                    for child in item.children:
                        if child.data["status"] > status:
                            status = child.data["status"]
                else:
                    status = item.data["status"]
                
                if speed is None or status == 7 or status == 10 or status == 5:
                    return QVariant(self.translateStatus(statusMapReverse[status]))
                else:
                    return QVariant("%s (%s KB/s)" % (self.translateStatus(statusMapReverse[status]), speed))
            elif index.column() == 3:
                item = index.internalPointer()
                if isinstance(item, Package):
                    return QVariant(item.data["priority"])
            elif index.column() == 4:
                item = index.internalPointer()
                if isinstance(item, Link):
                    if item.data["downloading"]:
                        return QVariant(item.data["downloading"]["format_eta"])
        elif role == Qt.EditRole:
            if index.column() == 0:
                return QVariant(index.internalPointer().data["name"])
        return QVariant()
    
    def flags(self, index):
        if index.column() == 0 and self.parent(index) == QModelIndex():
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
    
class QueueView(CollectorView):
    def __init__(self, connector):
        CollectorView.__init__(self, connector)
        self.setModel(QueueModel(self, connector))

        self.setColumnWidth(0, 300)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 50)
        self.setColumnWidth(4, 70)
        self.setColumnWidth(5, 80)
        
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.delegate = QueueProgressBarDelegate(self, self.model())
        self.setItemDelegateForColumn(5, self.delegate)

class QueueProgressBarDelegate(QItemDelegate):
    def __init__(self, parent, queue):
        QItemDelegate.__init__(self, parent)
        self.queue = queue
    
    def paint(self, painter, option, index):
        if not index.isValid():
            return
        if index.column() == 5:
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
                opts.text = QString(_("waiting %d seconds") % (wait,))
            else:
                opts.text = QString.number(opts.progress) + "%"
            QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)
            return
        QItemDelegate.paint(self, painter, option, index)

