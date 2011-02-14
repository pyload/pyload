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

from time import strftime, gmtime

class AccountModel(QAbstractItemModel):
    """
        model for account view
    """
    
    def __init__(self, view, connector):
        QAbstractItemModel.__init__(self)
        self.connector = connector
        self.view = view
        self._data = []
        self.cols = 4
        self.mutex = QMutex()
    
    def reloadData(self, force=False):
        """
            reload account list
        """
        accounts = self.connector.proxy.getAccounts(False)

        if self._data == accounts:
            return
        
        if len(self._data) > 0:        
            self.beginRemoveRows(QModelIndex(), 0, len(self._data)-1)
            self._data = []
            self.endRemoveRows()
            
        if len(accounts) > 0:
            self.beginInsertRows(QModelIndex(), 0, len(accounts)-1)
            self._data = accounts
            self.endInsertRows()
    
    def toData(self, index):
        """
            return index pointer
        """
        return index.internalPointer()
    
    def data(self, index, role=Qt.DisplayRole):
        """
            return cell data
        """
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return QVariant(self.toData(index).type)
            elif index.column() == 1:
                return QVariant(self.toData(index).login)
            elif index.column() == 2:
                if not self.toData(index).valid:
                    return QVariant(_("not valid"))
                if not self.toData(index).validuntil:
                    return QVariant(_("n/a"))
                until = int(self.toData(index).validuntil)
                if until > 0:
                    fmtime = strftime(_("%a, %d %b %Y %H:%M"), gmtime(until))
                    return QVariant(fmtime)
                else:
                    return QVariant(_("unlimited"))
        #elif role == Qt.EditRole:
        #    if index.column() == 0:
        #        return QVariant(index.internalPointer().data["name"])
        return QVariant()
        
    def index(self, row, column, parent=QModelIndex()):
        """
            create index with data pointer
        """
        if parent == QModelIndex() and len(self._data) > row:
            pointer = self._data[row]
            index = self.createIndex(row, column, pointer)
        elif parent.isValid():
            pointer = parent.internalPointer().children[row]
            index = self.createIndex(row, column, pointer)
        else:
            index = QModelIndex()
        return index
    
    def parent(self, index):
        """
            no parents, everything on top level
        """
        return QModelIndex()
    
    def rowCount(self, parent=QModelIndex()):
        """
            account count
        """
        if parent == QModelIndex():
            return len(self._data)
        return 0
    
    def columnCount(self, parent=QModelIndex()):
        return self.cols
    
    def hasChildren(self, parent=QModelIndex()):
        """
            everything on top level
        """
        if parent == QModelIndex():
            return True
        else:
            return False
    
    def canFetchMore(self, parent):
        return False
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
            returns column heading
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return QVariant(_("Type"))
            elif section == 1:
                return QVariant(_("Login"))
            elif section == 2:
                return QVariant(_("Valid until"))
            elif section == 3:
                return QVariant(_("Traffic left"))
        return QVariant()
    
    def flags(self, index):
        """
            cell flags
        """
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
    
class AccountView(QTreeView):
    """
        view component for accounts
    """
    
    def __init__(self, connector):
        QTreeView.__init__(self)
        self.setModel(AccountModel(self, connector))
        
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 150)
        
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.delegate = AccountDelegate(self, self.model())
        self.setItemDelegateForColumn(3, self.delegate)

class AccountDelegate(QItemDelegate):
    """
        used to display a progressbar for the traffic in the traffic cell
    """
    
    def __init__(self, parent, model):
        QItemDelegate.__init__(self, parent)
        self.model = model

    def paint(self, painter, option, index):
        """
            paint the progressbar
        """
        if not index.isValid():
            return
        if index.column() == 3:
            data = self.model.toData(index)
            opts = QStyleOptionProgressBarV2()
            opts.minimum = 0
            if data.trafficleft:
                if data.trafficleft == -1 or data.trafficleft is None:
                    opts.maximum = opts.progress = 1
                else:
                    opts.maximum = opts.progress = data.trafficleft
            if data.maxtraffic:
                opts.maximum = data.maxtraffic
            
            opts.rect = option.rect
            opts.rect.setRight(option.rect.right()-1)
            opts.rect.setHeight(option.rect.height()-1)
            opts.textVisible = True
            opts.textAlignment = Qt.AlignCenter
            if data.trafficleft and data.trafficleft == -1:
                opts.text = QString(_("unlimited"))
            elif data.trafficleft is None:
                opts.text = QString(_("n/a"))
            else:
                opts.text = QString.number(round(float(opts.progress)/1024/1024, 2)) + " GB"
            QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)
            return
        QItemDelegate.paint(self, painter, option, index)

