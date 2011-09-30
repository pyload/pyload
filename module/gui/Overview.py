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

from module.utils import formatSpeed, formatSize

class OverviewModel(QAbstractListModel):
    PackageName = 10
    Progress = 11
    PartsFinished = 12
    Parts = 13
    ETA = 14
    Speed = 15
    CurrentSize = 16
    MaxSize = 17
    Status = 18
    
    def __init__(self, view, connector):
        QAbstractListModel.__init__(self)
        
        self.packages = []
    
    def queueChanged(self): #dirty..
        self.beginResetModel()
        
        self.packages = []
        
        def partsFinished(p):
            f = 0
            for c in p.children:
                if c.data["status"] == 0:
                    f += 1
            return f
        
        def maxSize(p):
            ms = 0
            cs = 0
            for c in p.children:
                try:
                    s = c.data["downloading"]["size"]
                except:
                    s = c.data["size"]
                if c.data["downloading"]:
                    cs += s - c.data["downloading"]["bleft"]
                elif self.queue.getProgress(c, False) == 100:
                    cs += s
                ms += s
            return ms, cs
        
        def getProgress(p):
            for c in p.children:
                if c.data["status"] == 13:
                    pass # TODO return _("Unpacking"), int(c.data["progress"])
            return _("Downloading"), self.queue.getProgress(p)
        
        d = self.queue._data
        for p in d:
            status, progress = getProgress(p)
            maxsize, currentsize = maxSize(p)
            speed = self.queue.getSpeed(p)
            if speed:
                eta = (maxsize - (maxsize * (progress/100.0)))/speed
            else:
                eta = 0
            if not speed and not progress:
                status = _("Queued")
            info = {
                OverviewModel.PackageName: p.data["name"],
                OverviewModel.Progress: progress,
                OverviewModel.PartsFinished: partsFinished(p),
                OverviewModel.Parts: len(p.children),
                OverviewModel.ETA: int(eta),
                OverviewModel.Speed: speed,
                OverviewModel.CurrentSize: currentsize,
                OverviewModel.MaxSize: maxsize,
                OverviewModel.Status: status,
            }
            
            self.packages.append(info)
        
        self.endResetModel()
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return QVariant(_("Package"))
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.packages)
    
    def data(self, index, role=Qt.DisplayRole):
        if role in [OverviewModel.PackageName, OverviewModel.Progress, OverviewModel.PartsFinished, OverviewModel.Parts, OverviewModel.ETA, OverviewModel.Speed, OverviewModel.CurrentSize, OverviewModel.MaxSize, OverviewModel.Status]:
            return QVariant(self.packages[index.row()][role])
        return QVariant()
    
class OverviewView(QListView):
    def __init__(self, connector):
        QListView.__init__(self)
        self.setModel(OverviewModel(self, connector))
        
        self.setAlternatingRowColors(True)
        self.delegate = OverviewDelegate(self)
        self.setItemDelegate(self.delegate)

class OverviewDelegate(QItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)
        self.parent = parent
        self.model = parent.model()
    
    def paint(self, painter, option, index):
        option.rect.setHeight(59+16)
        option.rect.setWidth(self.parent.width()-20)
        
        #if option.state & QStyle.State_Selected:
        #    painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))
        
        packagename = index.data(OverviewModel.PackageName).toString()
        partsf = index.data(OverviewModel.PartsFinished).toString()
        parts = index.data(OverviewModel.Parts).toString()
        eta = int(index.data(OverviewModel.ETA).toString())
        speed = index.data(OverviewModel.Speed).toString() or 0
        progress = int(index.data(OverviewModel.Progress).toString())
        currentSize = int(index.data(OverviewModel.CurrentSize).toString())
        maxSize = int(index.data(OverviewModel.MaxSize).toString())
        status = index.data(OverviewModel.Status).toString()
        
        def formatEta(seconds): #TODO add to utils
            if seconds <= 0: return ""
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            return _("ETA: ") + "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
        
        statusline = QString(_("Parts: ") + "%s/%s" % (partsf, parts))
        if partsf == parts:
            speedline = _("Finished")
        elif not status == _("Downloading"):
            speedline = QString(status)
        else:
            speedline = QString(formatEta(eta) + "     " + _("Speed: %s") % formatSpeed(speed))
        
        if progress in (0,100):
            sizeline = QString(_("Size:") + "%s" % formatSize(maxSize))
        else:
            sizeline = QString(_("Size:") + "%s / %s" % (formatSize(currentSize), formatSize(maxSize)))
        
        f = painter.font()
        f.setPointSize(12)
        f.setBold(True)
        painter.setFont(f)
        
        r = option.rect.adjusted(4, 4, -4, -4)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), Qt.AlignTop | Qt.AlignLeft, packagename)
        newr = painter.boundingRect(r.left(), r.top(), r.width(), r.height(), Qt.AlignTop | Qt.AlignLeft, packagename)
        
        f.setPointSize(10)
        f.setBold(False)
        painter.setFont(f)
        
        painter.drawText(r.left(), newr.bottom()+5, r.width(), r.height(), Qt.AlignTop | Qt.AlignLeft, statusline)
        painter.drawText(r.left(), newr.bottom()+5, r.width(), r.height(), Qt.AlignTop | Qt.AlignHCenter, sizeline)
        painter.drawText(r.left(), newr.bottom()+5, r.width(), r.height(), Qt.AlignTop | Qt.AlignRight, speedline)
        newr = painter.boundingRect(r.left(), newr.bottom()+2, r.width(), r.height(), Qt.AlignTop | Qt.AlignLeft, statusline)
        newr.setTop(newr.bottom()+8)
        newr.setBottom(newr.top()+20)
        newr.setRight(self.parent.width()-25)
        
        f.setPointSize(10)
        painter.setFont(f)
        
        opts = QStyleOptionProgressBarV2()
        opts.maximum = 100
        opts.minimum = 0
        opts.progress = progress
        opts.rect = newr
        opts.textVisible = True
        opts.textAlignment = Qt.AlignCenter
        opts.text = QString.number(opts.progress) + "%"
        QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)
    
    def sizeHint(self, option, index):
        return QSize(self.parent.width()-22, 59+16)
