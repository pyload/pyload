#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: mkaay




from PyQt4.QtCore import *
from PyQt4.QtGui import *

from time import time

from module.remote.thriftbackend.ThriftClient import Destination
from module.gui.Collector import CollectorModel, Package, Link, CollectorView, statusMapReverse
from module.utils import formatSize, formatSpeed

class QueueModel(CollectorModel):
    """
        model for the queue view, inherits from CollectorModel
    """

    def __init__(self, view, connector):
        CollectorModel.__init__(self, view, connector)
        self.cols = 6
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

    def fullReload(self):
        """
            reimplements CollectorModel.fullReload, because we want the Queue data
        """
        self._data = []
        order = self.connector.getPackageOrder(Destination.Queue)
        self.beginInsertRows(QModelIndex(), 0, len(list(order.values())))
        for position, pid in order.items():
            pack = self.connector.getPackageData(pid)
            package = Package(pack)
            self._data.append(package)
        self._data = sorted(self._data, key=lambda p: p.data["order"])
        self.endInsertRows()
        self.updateCount()

    def insertEvent(self, event):
        """
            wrap CollectorModel.insertEvent to update the element count
        """
        CollectorModel.insertEvent(self, event)
        self.updateCount()

    def removeEvent(self, event):
        """
            wrap CollectorModel.removeEvent to update the element count
        """
        CollectorModel.removeEvent(self, event)
        self.updateCount()

    def updateEvent(self, event):
        """
            wrap CollectorModel.updateEvent to update the element count
        """
        CollectorModel.updateEvent(self, event)
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
        self.mutex.unlock()
        self.emit(SIGNAL("updateCount"), packageCount, fileCount)
        self.mutex.lock()

    def update(self):
        """
            update slot for download status updating
        """
        locker = QMutexLocker(self.mutex)
        downloading = self.connector.statusDownloads()
        if not downloading:
            return
        for p, pack in enumerate(self._data):
            for d in downloading:
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
        self.updateCount()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
            returns column heading
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return QVariant(_("Name"))
            elif section == 2:
                return QVariant(_("Status"))
            elif section == 1:
                return QVariant(_("Plugin"))
            elif section == 3:
                return QVariant(_("Size"))
            elif section == 4:
                return QVariant(_("ETA"))
            elif section == 5:
                return QVariant(_("Progress"))
        return QVariant()

    def getWaitingProgress(self, item):
        """
            returns time to wait, caches startingtime to provide progress
        """
        locker = QMutexLocker(self.mutex)
        if isinstance(item, Link):
            if item.data["status"] == 5 and item.data["downloading"]:
                until = float(item.data["downloading"]["wait_until"])
                try:
                    since, until_old = self.wait_dict[item.id]
                    if not until == until_old:
                        raise Exception
                except Exception:
                    since = time()
                    self.wait_dict[item.id] = since, until
                since = float(since)
                max_wait = float(until-since)
                rest = int(until-time())
                if rest < 0:
                    return 0, None
                res = 100//max_wait
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
                if item.data["status"] == 0:
                    return 100
                return int(item.data["downloading"]["percent"])
            except Exception:
                return 0
        elif isinstance(item, Package):
            count = len(item.children)
            perc_sum = 0
            for child in item.children:
                try:
                    if child.data["status"] == 0: #completed
                        perc_sum += 100
                    perc_sum += int(child.data["downloading"]["percent"])
                except Exception:
                    pass
            if count == 0:
                return 0
            return perc_sum // count
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
                    return QVariant("{} ({})".format(self.translateStatus(statusMapReverse[status]), formatSpeed(speed)))
            elif index.column() == 3:
                item = index.internalPointer()
                if isinstance(item, Link):
                    if item.data["status"] == 0: #TODO needs change??
                    #self.getProgress(item, False) == 100:
                        return QVariant(formatSize(item.data["size"]))
                    elif self.getProgress(item, False) == 0:
                        try:
                            return QVariant("{} / {}".format(formatSize(item.data["size"]-item.data["downloading"]["bleft"]), formatSize(item.data["size"])))
                        except Exception:
                            return QVariant("0 B / {}".format(formatSize(item.data["size"])))
                    else:
                        try:
                            return QVariant("{} / {}".format(formatSize(item.data["size"]-item.data["downloading"]["bleft"]), formatSize(item.data["size"])))
                        except Exception:
                            return QVariant("? / {}".format(formatSize(item.data["size"])))
                else:
                    ms = 0
                    cs = 0
                    for c in item.children:
                        try:
                            s = c.data["downloading"]["size"]
                        except Exception:
                            s = c.data["size"]
                        if c.data["downloading"]:
                            cs += s - c.data["downloading"]["bleft"]
                        elif self.getProgress(c, False) == 100:
                            cs += s
                        ms += s
                    if cs == 0 or cs == ms:
                        return QVariant(formatSize(ms))
                    else:
                        return QVariant("{} / {}".format(formatSize(cs), formatSize(ms)))
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
        """
            cell flags
        """
        if index.column() == 0 and self.parent(index) == QModelIndex():
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

class QueueView(CollectorView):
    """
        view component for queue
    """

    def __init__(self, connector):
        CollectorView.__init__(self, connector)
        self.setModel(QueueModel(self, connector))

        self.setColumnWidth(0, 300)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 140)
        self.setColumnWidth(3, 180)
        self.setColumnWidth(4, 70)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.delegate = QueueProgressBarDelegate(self, self.model())
        self.setItemDelegateForColumn(5, self.delegate)

class QueueProgressBarDelegate(QItemDelegate):
    """
        used to display a progressbar in the progress cell
    """

    def __init__(self, parent, queue):
        QItemDelegate.__init__(self, parent)
        self.queue = queue

    def paint(self, painter, option, index):
        """
            paint the progressbar
        """
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
                opts.text = QString(_("waiting {:d} seconds").format(wait))
            else:
                opts.text = QString.number(opts.progress) + "%"
            QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)
            return
        QItemDelegate.paint(self, painter, option, index)

