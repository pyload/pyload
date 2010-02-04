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

class PWInputWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.Password)
        label = QLabel(_("Password:"))
        ok = QPushButton(_("OK"))
        cancel = QPushButton(_("Cancel"))
        grid = QGridLayout()
        grid.addWidget(label, 0, 0, 1, 2)
        grid.addWidget(self.input, 1, 0, 1, 2)
        grid.addWidget(cancel, 2, 0)
        grid.addWidget(ok, 2, 1)
        self.setLayout(grid)
        
        self.connect(ok, SIGNAL("clicked()"), self.slotOK)
        self.connect(cancel, SIGNAL("clicked()"), self.slotCancel)
        self.connect(self.input, SIGNAL("returnPressed()"), self.slotOK)
    
    def slotOK(self):
        self.hide()
        self.emit(SIGNAL("ok"), self.input.text())
    
    def slotCancel(self):
        self.hide()
        self.emit(SIGNAL("cancel"))
