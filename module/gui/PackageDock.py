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

class NewPackageDock(QDockWidget):
    def __init__(self):
        QDockWidget.__init__(self, "New Package")
        self.setObjectName("New Package Dock")
        self.widget = NewPackageWindow(self)
        self.setWidget(self.widget)
        self.setAllowedAreas(Qt.RightDockWidgetArea|Qt.LeftDockWidgetArea)
        self.hide()
    
    def slotDone(self):
        view = self.widget.view
        count = view.topLevelItemCount()
        ids = []
        for i in range(count):
            item = view.topLevelItem(i)
            if item:
                ids.append(item.data(0, Qt.UserRole).toInt()[0])
        self.emit(SIGNAL("done"), self.widget.nameInput.text(), ids)
        view.clear()
        self.hide()

class NewPackageWindow(QWidget):
    def __init__(self, dock):
        QWidget.__init__(self)
        self.dock = dock
        self.setLayout(QGridLayout())
        layout = self.layout()
        
        nameLabel = QLabel("Name")
        nameInput = QLineEdit()
        
        linksLabel = QLabel("Links in this Package")
        linkView = QTreeWidget()
        linkView.setSelectionBehavior(QAbstractItemView.SelectRows)
        linkView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        linkView.setColumnCount(1)
        linkView.setHeaderLabels(["Name"])
        linkView.setDragEnabled(True)
        linkView.setDragDropMode(QAbstractItemView.DragDrop)
        linkView.setDropIndicatorShown(True)
        linkView.setAcceptDrops(True)
        linkView.setDragDropOverwriteMode(True)
        
        self.view = linkView
        self.nameInput = nameInput
        
        save = QPushButton("Create")
        
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(nameInput, 0, 1)
        layout.addWidget(linksLabel, 1, 0, 1, 2)
        layout.addWidget(linkView, 2, 0, 1, 2)
        layout.addWidget(save, 3, 0, 1, 2)
        
        self.connect(save, SIGNAL("clicked()"), self.dock.slotDone)
