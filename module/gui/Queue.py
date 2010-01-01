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

class Queue(QObject):
    def __init__(self, view, connector):
        QObject.__init__(self)
        self.view = view
        self.connector = connector
        self.statusMap = {
            "finished":    0,
            "queued":      1,
            "checking":    2,
            "waiting":     3,
            "reconnected": 4,
            "starting":    5,
            "failed":      6,
            "aborted":     7,
            "decrypting":  8,
            "downloading": 9
        }
        self.statusMapReverse = dict((v,k) for k, v in self.statusMap.iteritems())
        self.interval = 1
        self.wait_dict = {}
        self.rootItem = self.view.invisibleRootItem()
        self.mutex = QMutex()
        self.updater = self.QueueUpdater(self.interval)
        self.connect(self.updater, SIGNAL("update()"), self.update)
    
    class QueueUpdater(QThread):
        def __init__(self, interval):
            QThread.__init__(self)
            self.interval = interval
            self.running = True
        
        def run(self):
            while self.running:
                self.emit(SIGNAL("update()"))
                self.sleep(self.interval)
    
    def start(self):
        self.updater.start()
    
    def wait(self):
        self.updater.wait()
    
    def stop(self):
        self.updater.running = False
    
    def update(self):
        locker = QMutexLocker(self.mutex)
        packs = self.connector.getPackageQueue()
        downloading_raw = self.connector.getDownloadQueue()
        downloading = {}
        for d in downloading_raw:
            did = d["id"]
            del d["id"]
            del d["name"]
            del d["status"]
            downloading[did] = d
        ids = []
        for data in packs:
            ids.append(data["id"])
        self.clear(ids)
        for data in packs:
            pack = self.getPack(data["id"])
            if not pack:
                pack = self.QueuePack(self)
            pack.setPackData(data)
            files = self.connector.getPackageFiles(data["id"])
            pack.clear(files)
            self.addPack(data["id"], pack)
            for fid in files:
                info = self.connector.getLinkInfo(fid)
                child = pack.getChild(fid)
                if not child:
                    child = self.QueueFile(self, pack)
                info["downloading"] = None
                try:
                    info["downloading"] = downloading[info["id"]]
                except:
                    pass
                if not info["status_type"]:
                    info["status_type"] = "queued"
                child.setFileData(info)
                pack.addPackChild(fid, child)
            self.addPack(data["id"], pack)
    
    def addPack(self, pid, newPack):
        pos = None
        try:
            for pack in QueueIterator(self.rootItem):
                if pack.getPackData()["id"] == pid:
                    pos = self.rootItem.indexOfChild(pack)
                    break
            if pos == None:
                raise Exception()
            item = self.rootItem.child(pos)
            item.setPackData(newPack.getPackData())
        except:
            self.rootItem.addChild(newPack)
            item = newPack
        item.setData(0, Qt.DisplayRole, QVariant(item.getPackData()["package_name"]))
        status = -1
        speed = self.getSpeed(item)
        plugins = []
        for child in item.getChildren():
            data = child.getFileData()
            if self.statusMap.has_key(data["status_type"]) and self.statusMap[data["status_type"]] > status:
                status = self.statusMap[data["status_type"]]
            if not data["plugin"] in plugins:
                plugins.append(data["plugin"])
        if status >= 0:
            if speed == None:
                statustxt = self.statusMapReverse[status]
            else:
                statustxt = "%s (%s KB/s)" % (self.statusMapReverse[status], speed)
            item.setData(2, Qt.DisplayRole, QVariant(statustxt))
        item.setData(1, Qt.DisplayRole, QVariant(", ".join(plugins)))
        item.setData(0, Qt.UserRole, QVariant(pid))
        item.setData(3, Qt.UserRole, QVariant(item))
    
    def getPack(self, pid):
        for k, pack in enumerate(ItemIterator(self.rootItem)):
            if pack.getPackData()["id"] == pid:
                return pack
        return None
    
    def clear(self, ids):
        clear = False
        remove = []
        for k, pack in enumerate(ItemIterator(self.rootItem)):
            if not pack.getPackData()["id"] in ids:
                clear = True
                remove.append(k)
        if not clear:
            return
        remove.sort()
        remove.reverse()
        for k in remove:
            self.rootItem.takeChild(k)
    
    def getWaitingProgress(self, q):
        locker = QMutexLocker(self.mutex)
        if isinstance(q, self.QueueFile):
            data = q.getFileData()
            if data["status_type"] == "waiting" and data["downloading"]:
                until = float(data["downloading"]["wait_until"])
                try:
                    since, until_old = self.wait_dict[data["id"]]
                    if not until == until_old:
                        raise Exception
                except:
                    since = time()
                    self.wait_dict[data["id"]] = since, until
                since = float(since)
                max_wait = float(until-since)
                rest = int(until-time())
                res = 100/max_wait
                perc = rest*res
                return perc, rest
        return None
    
    def getProgress(self, q):
        locker = QMutexLocker(self.mutex)
        if isinstance(q, self.QueueFile):
            data = q.getFileData()
            if data["downloading"]:
                return int(data["downloading"]["percent"])
            if data["status_type"] == "finished" or \
                  data["status_type"] == "failed" or \
                  data["status_type"] == "aborted":
                return 100
        elif isinstance(q, self.QueuePack):
            children = q.getChildren()
            count = len(children)
            perc_sum = 0
            for child in children:
                val = 0
                data = child.getFileData()
                if data["downloading"]:
                    val = int(data["downloading"]["percent"])
                elif data["status_type"] == "finished" or \
                        data["status_type"] == "failed" or \
                        data["status_type"] == "aborted":
                    val = 100
                perc_sum += val
            if count == 0:
                return 0
            return perc_sum/count
        return 0
    
    def getSpeed(self, q):
        if isinstance(q, self.QueueFile):
            data = q.getFileData()
            if data["downloading"]:
                return int(data["downloading"]["speed"])
        elif isinstance(q, self.QueuePack):
            children = q.getChildren()
            count = len(children)
            speed_sum = 0
            all_waiting = True
            running = False
            for child in children:
                val = 0
                data = child.getFileData()
                if data["downloading"]:
                    if not data["status_type"] == "waiting":
                        all_waiting = False
                    val = int(data["downloading"]["speed"])
                    running = True
                speed_sum += val
            if count == 0 or not running or all_waiting:
                return None
            return speed_sum
        return None
    
    class QueuePack(QTreeWidgetItem):
        def __init__(self, queue):
            QTreeWidgetItem.__init__(self)
            self.queue = queue
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
            speed = self.queue.getSpeed(item)
            if speed == None or item.getFileData()["status_type"] == "starting" or item.getFileData()["status_type"] == "decrypting":
                status = item.getFileData()["status_type"]
            else:
                status = "%s (%s KB/s)" % (item.getFileData()["status_type"], speed)
            item.setData(0, Qt.DisplayRole, QVariant(item.getFileData()["filename"]))
            item.setData(2, Qt.DisplayRole, QVariant(status))
            item.setData(1, Qt.DisplayRole, QVariant(item.getFileData()["plugin"]))
            item.setData(0, Qt.UserRole, QVariant(cid))
            item.setData(3, Qt.UserRole, QVariant(item))
        
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

    class QueueFile(QTreeWidgetItem):
        def __init__(self, queue, pack):
            QTreeWidgetItem.__init__(self)
            self.queue = queue
            self.pack = pack
            self._data = {}
            self.wait_since = None
        
        def getFileData(self):
            return self._data
        
        def setFileData(self, data):
            self._data = data
        
        def getPack(self):
            return self.pack

class QueueProgressBarDelegate(QItemDelegate):
    def __init__(self, parent, queue):
        QItemDelegate.__init__(self, parent)
        self.queue = queue
    
    def paint(self, painter, option, index):
        if index.column() == 3:
            qe = index.data(Qt.UserRole).toPyObject()
            w = self.queue.getWaitingProgress(qe)
            wait = None
            if w:
                progress = w[0]
                wait = w[1]
            else:
                progress = self.queue.getProgress(qe)
            opts = QStyleOptionProgressBarV2()
            opts.maximum = 100
            opts.minimum = 0
            opts.progress = progress
            opts.rect = option.rect
            opts.rect.setRight(option.rect.right()-1)
            opts.rect.setHeight(option.rect.height()-1)
            opts.textVisible = True
            opts.textAlignment = Qt.AlignCenter
            if not wait == None:
                opts.text = QString("waiting %d seconds" % (wait,))
            else:
                opts.text = QString.number(opts.progress) + "%"
            QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)
            return
        QItemDelegate.paint(self, painter, option, index)

class ItemIterator():
    def __init__(self, item):
        self.item = item
        self.current = -1
    
    def __iadd__(self, val):
        self.current += val
    
    def value(self):
        return self.item.child(self.current)
    
    def next(self):
        self.__iadd__(1)
        value = self.value()
        if value:
            return self.value()
        else:
            raise StopIteration
    
    def __iter__(self):
        return self
