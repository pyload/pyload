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

class Queue(QThread):
    def __init__(self, view, connector):
        QThread.__init__(self)
        self.view = view
        self.connector = connector
        self.statusMap = {
            "finished":    0,
            "checking":    1,
            "waiting":     2,
            "reconnected": 3,
            "downloading": 4,
            "failed":      5,
            "aborted":     6,
        }
        self.statusMapReverse = dict((v,k) for k, v in self.statusMap.iteritems())
        self.queue = []
        self.interval = 1
        self.running = True
        self.wait_dict = {}
        self.rootItem = self.view.invisibleRootItem()
        self.mutex = QMutex()
    
    def run(self):
        while self.running:
            self.update()
            sleep(self.interval)
    
    def stop(self):
        self.running = False
    
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
            pack.setData(data)
            self.addPack(data["id"], pack)
            files = self.connector.getPackageFiles(data["id"])
            pack.clear(files)
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
                child.setData(info)
                pack.addChild(fid, child)
    
    def addPack(self, pid, newPack):
        pos = None
        try:
            for k, pack in enumerate(self.queue):
                if pack.getData()["id"] == pid:
                    pos = k
                    break
            if pos == None:
                raise Exception()
            self.queue[pos] = newPack
        except:
            self.queue.append(newPack)
            pos = self.queue.index(newPack)
        item = self.rootItem.child(pos)
        if not item:
            item = QTreeWidgetItem()
            self.rootItem.insertChild(pos, item)
        item.setData(0, Qt.DisplayRole, QVariant(newPack.getData()["package_name"]))
        status = -1
        speed = self.getSpeed(newPack)
        plugins = []
        for child in newPack.getChildren():
            if self.statusMap.has_key(child.data["status_type"]) and self.statusMap[child.data["status_type"]] > status:
                status = self.statusMap[child.data["status_type"]]
            if not child.data["plugin"] in plugins:
                plugins.append(child.data["plugin"])
        if status >= 0:
            if speed == None:
                statustxt = self.statusMapReverse[status]
            else:
                statustxt = "%s (%s KB/s)" % (self.statusMapReverse[status], speed)
            item.setData(2, Qt.DisplayRole, QVariant(statustxt))
        item.setData(1, Qt.DisplayRole, QVariant(", ".join(plugins)))
        item.setData(0, Qt.UserRole, QVariant(pid))
        item.setData(3, Qt.UserRole, QVariant(newPack))
    
    def getPack(self, pid):
        for k, pack in enumerate(self.queue):
            if pack.getData()["id"] == pid:
                return pack
        return None
    
    def clear(self, ids):
        clear = False
        for pack in self.queue:
            if not pack.getData()["id"] in ids:
                clear = True
                break
        if not clear:
            return
        self.queue = []
        self.rootItem.takeChildren()
    
    def getWaitingProgress(self, q):
        locker = QMutexLocker(self.mutex)
        if isinstance(q, self.QueueFile):
            data = q.getData()
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
            data = q.getData()
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
                data = child.getData()
                if data["downloading"]:
                    val = int(data["downloading"]["percent"])
                elif child.data["status_type"] == "finished" or \
                        child.data["status_type"] == "failed" or \
                        child.data["status_type"] == "aborted":
                    val = 100
                perc_sum += val
            if count == 0:
                return 0
            return perc_sum/count
        return 0
    
    def getSpeed(self, q):
        if isinstance(q, self.QueueFile):
            data = q.getData()
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
                data = child.getData()
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
    
    class QueuePack():
        def __init__(self, queue):
            self.queue = queue
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
            parent = self.queue.rootItem.child(ppos)
            item = parent.child(pos)
            if not item:
                item = QTreeWidgetItem()
                parent.insertChild(pos, item)
            speed = self.queue.getSpeed(newChild)
            if speed == None or newChild.getData()["status_type"] == "starting":
                status = newChild.getData()["status_type"]
            else:
                status = "%s (%s KB/s)" % (newChild.getData()["status_type"], speed)
            item.setData(0, Qt.DisplayRole, QVariant(newChild.getData()["filename"]))
            item.setData(2, Qt.DisplayRole, QVariant(status))
            item.setData(1, Qt.DisplayRole, QVariant(newChild.getData()["plugin"]))
            item.setData(0, Qt.UserRole, QVariant(cid))
            item.setData(3, Qt.UserRole, QVariant(newChild))
        
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
    
        def clear(self, ids):
            clear = False
            children = {}
            for file in self.getChildren():
                if not file.getData()["id"] in ids:
                    clear = True
                    break
                try:
                    children[file.getData()["id"]]
                    clear = True
                except:
                    children[file.getData()["id"]] = True
                
            if not clear:
                return
            ppos = self.queue.queue.index(self)
            parent = self.queue.rootItem.child(ppos)
            parent.takeChildren()
            self.children = []

    class QueueFile():
        def __init__(self, queue, pack):
            self.queue = queue
            self.pack = pack
            self.wait_since = None
        
        def getData(self):
            return self.data
        
        def setData(self, data):
            self.data = data
        
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
