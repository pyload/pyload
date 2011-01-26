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

class OverviewModel(QAbstractListModel):
    PackageName = 10
    Progress = 11
    PartsFinished = 12
    Parts = 13
    ETA = 14
    Speed = 15
    
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
        
        d = self.queue._data
        for p in d:
            info = {
                OverviewModel.PackageName: p.data["name"],
                OverviewModel.Progress: self.queue.getProgress(p),
                OverviewModel.PartsFinished: partsFinished(p),
                OverviewModel.Parts: len(p.children),
                OverviewModel.ETA: "n/a",
                OverviewModel.Speed: self.queue.getSpeed(p),
            }
            
            self.packages.append(info)
        
        self.endResetModel()
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return QVariant(_("Package"))
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.packages)
    
    def data(self, index, role=Qt.DisplayRole):
        if role in [OverviewModel.PackageName, OverviewModel.Progress, OverviewModel.PartsFinished, OverviewModel.Parts, OverviewModel.ETA, OverviewModel.Speed]:
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
        option.rect.setWidth(self.parent.width())
        
        #if option.state & QStyle.State_Selected:
        #    painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))
        
        packagename = index.data(OverviewModel.PackageName).toString()
        partsf = index.data(OverviewModel.PartsFinished).toString()
        parts = index.data(OverviewModel.Parts).toString()
        eta = index.data(OverviewModel.ETA).toString()
        speed = index.data(OverviewModel.Speed).toString()
        progress = int(index.data(OverviewModel.Progress).toString())
        
        statusline = QString(_("Parts: %s/%s          ETA: %s          Speed: %s kb/s" % (partsf, parts, eta, speed)))
        
        f = painter.font()
        f.setPointSize(12)
        f.setBold(True)
        painter.setFont(f)
        
        r = option.rect.adjusted(4, 4, -4, -4)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), Qt.AlignTop | Qt.AlignLeft, packagename)
        newr = painter.boundingRect(r.left(), r.top(), r.width(), r.height(), Qt.AlignTop | Qt.AlignLeft, packagename)
        
        f.setPointSize(11)
        f.setBold(False)
        painter.setFont(f)
        
        painter.drawText(r.left(), newr.bottom()+4, r.width(), r.height(), Qt.AlignTop | Qt.AlignLeft, statusline)
        newr = painter.boundingRect(r.left(), newr.bottom()+2, r.width(), r.height(), Qt.AlignTop | Qt.AlignLeft, statusline)
        newr.setTop(newr.bottom()+8)
        newr.setBottom(newr.top()+20)
        newr.setRight(self.parent.width()-5)
        
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
        return QSize(self.parent.width(), 59+16)
