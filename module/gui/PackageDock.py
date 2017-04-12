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

import logging
from os.path import join

class NewPackageDock(QDockWidget):
    def __init__(self):
        self.paintEventSignal = False
        QDockWidget.__init__(self, _("New Package"))
        self.log = logging.getLogger("guilog")
        
        self.setObjectName("New Package Dock")
        self.widget = NewPackageWindow(self)
        self.setWidget(self.widget)
        self.setAllowedAreas(Qt.RightDockWidgetArea|Qt.LeftDockWidgetArea)
        self.hide()
    
    def slotDone(self):
        text = unicode(self.widget.box.toPlainText())
        pw   = unicode(self.widget.passwordInput.text())
        if not pw:
            pw = None
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            lines.append(line)
        if not lines:
            self.widget.slotMsgShow("<b>" + _("Error, no URLs given.") + "</b>")
            return
        queue = self.widget.destQueue.isChecked()
        self.emit(SIGNAL("done"), unicode(self.widget.nameInput.text()), lines, queue, pw)
        self.widget.nameInput.setText("")
        self.widget.passwordInput.setText("")
        self.widget.box.clear()
    
    def parseUri(self):
        text = unicode(self.widget.box.toPlainText())
        self.emit(SIGNAL("parseUri"), "packagedock", text)
    
    def parseUriResult(self, result):
        self.widget.box.setPlainText(result)
    
    def closeEvent(self, event):
        self.hide()
        event.ignore()
    
    def paintEvent(self, event):
        QDockWidget.paintEvent(self, event)
        if self.paintEventSignal:
            self.paintEventSignal = False
            self.emit(SIGNAL("newPackDockPaintEvent"))

class NewPackageWindow(QWidget):
    def __init__(self, dock):
        QWidget.__init__(self)
        self.log = logging.getLogger("guilog")
        self.dock = dock
        
        self.setLayout(QVBoxLayout())
        layout = self.layout()
        
        nameLabel = QLabel(_("Name"))
        nameInput = QLineEdit()
        passwordLabel = QLabel(_("Password"))
        passwordInput = QLineEdit()
        
        linksLabel = QLabel(_("Drop or Paste URLs here") + ":")
        
        self.box = PlainTextEdit()
        self.nameInput = nameInput
        self.passwordLabel = passwordLabel
        self.passwordInput = passwordInput
        
        self.destQueue     = QRadioButton(_("Queue"))
        self.destCollector = QRadioButton(_("Collector"))
        self.destCollector.setChecked(True)
        destBtnLayout = QHBoxLayout()
        destBtnLayout.addWidget(self.destQueue)
        destBtnLayout.addWidget(self.destCollector)
        destBtnLayout.addStretch(1)
        
        self.clear = QPushButton(_("Clear"))
        self.filter = QPushButton(_("Filter URLs"))
        
        self.save = QPushButton(_("Create"))
        self.save.setIcon(QIcon(join(pypath, "icons", "add_small.png")))
        self.msg = QLabel("ERROR")
        lsp = self.msg.sizePolicy()
        lsp.setHorizontalPolicy(QSizePolicy.Ignored)
        self.msg.setSizePolicy(lsp)
        hbox = QHBoxLayout()
        hbox.addWidget(self.msg)
        hbox.addWidget(self.save)
        
        grid = QGridLayout()
        grid.addWidget(nameLabel, 0, 0)
        grid.addWidget(nameInput, 0, 1)
        grid.addWidget(passwordLabel, 1, 0)
        grid.addWidget(passwordInput, 1, 1)
        layout.addLayout(grid)
        layout.addWidget(linksLabel)
        layout.addWidget(self.box)
        layout.addWidget(self.clear)
        layout.addWidget(self.filter)
        layout.addLayout(destBtnLayout)
        layout.addLayout(hbox)
        
        self.adjustSize()
        self.msg.setFixedHeight(self.save.height())
        self.slotMsgHide()
        
        self.connect(self.save, SIGNAL("clicked()"), self.dock.slotDone)
        self.connect(self.clear, SIGNAL("clicked()"), self.box.clear)
        self.connect(self.filter, SIGNAL("clicked()"), self.dock.parseUri)
    
    def slotMsgShow(self, msg):
        self.msg.setText(msg)
        self.msg.setFixedHeight(self.save.height())
        self.msg.show()
        self.save.hide()
        QTimer.singleShot(2000, self.slotMsgHide)
    
    def slotMsgHide(self):
        self.msg.hide()
        self.save.show()

class PlainTextEdit(QPlainTextEdit):
    def __init__(self):
        QPlainTextEdit.__init__(self)
        self.setMinimumHeight(30)
    
    def dropEvent(self, event):
        if not self.toPlainText().isEmpty():
            self.appendPlainText("")    # appends a line feed
        QPlainTextEdit.dropEvent(self, event)
