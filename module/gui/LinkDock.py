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

class NewLinkDock(QDockWidget):
    def __init__(self):
        QDockWidget.__init__(self, "New Links")
        self.setObjectName("New Links Dock")
        self.widget = NewLinkWindow(self)
        self.setWidget(self.widget)
        self.setAllowedAreas(Qt.RightDockWidgetArea|Qt.LeftDockWidgetArea)
        self.hide()
    
    def slotDone(self):
        text = str(self.widget.box.toPlainText())
        lines = text.splitlines()
        self.emit(SIGNAL("done"), lines)
        self.widget.box.clear()
        self.hide()

class NewLinkWindow(QWidget):
    def __init__(self, dock):
        QWidget.__init__(self)
        self.dock = dock
        self.setLayout(QVBoxLayout())
        layout = self.layout()
        
        explanationLabel = QLabel("Select a package and then click Add button.")
        boxLabel = QLabel("Paste URLs here:")
        self.box = QTextEdit()
        
        save = QPushButton("Add")
        
        layout.addWidget(explanationLabel)
        layout.addWidget(boxLabel)
        layout.addWidget(self.box)
        layout.addWidget(save)
        
        self.connect(save, SIGNAL("clicked()"), self.dock.slotDone)
