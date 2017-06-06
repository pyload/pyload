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

class NewLinkDock(QDockWidget):
    def __init__(self):
        self.paintEventSignal = False
        QDockWidget.__init__(self, _("Add Links"))
        self.log = logging.getLogger("guilog")
        
        self.geo = None
        self.paintEventCounter = int(0)
        
        self.setObjectName("New Links Dock")
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))
        self.widget = NewLinkWindow(self)
        self.setWidget(self.widget)
        self.setAllowedAreas(Qt.RightDockWidgetArea|Qt.LeftDockWidgetArea)
        self.hide()
    
    def slotDone(self):
        text = unicode(self.widget.box.toPlainText())
        lines = text.splitlines()
        if not lines:
            self.widget.slotMsgShow("<b>" + _("Error, no URLs given.") + "</b>")
            return
        queue = self.widget.destQueue.isChecked()
        self.emit(SIGNAL("done"), lines, queue)
    
    def parseUri(self):
        text = unicode(self.widget.box.toPlainText())
        self.emit(SIGNAL("parseUri"), "linkdock", text)
    
    def parseUriResult(self, result):
        self.widget.box.setPlainText(result)
    
    def closeEvent(self, event):
        if self.isFloating():
            self.emit(SIGNAL("newLinkDockClosed"))
        self.hide()
        event.ignore()
    
    def paintEvent(self, event):
        QDockWidget.paintEvent(self, event)
        if self.isFloating():
            self.geo = self.geometry()
        self.paintEventCounter += 1
        if self.paintEventSignal:
            self.paintEventSignal = False
            self.emit(SIGNAL("newLinkDockPaintEvent"))
    
    def moveEvent(self, event):
        if self.isFloating():
            self.geo = self.geometry()

class NewLinkWindow(QWidget):
    def __init__(self, dock):
        QWidget.__init__(self)
        self.log = logging.getLogger("guilog")
        self.dock = dock
        
        self.setLayout(QVBoxLayout())
        layout = self.layout()
        
        boxLabel = QLabel(_("Drop or Paste URLs here") + ":")
        self.box = PlainTextEdit()
        
        self.destQueue     = QRadioButton(_("Queue"))
        self.destCollector = QRadioButton(_("Collector"))
        self.destCollector.setChecked(True)
        destBtnLayout = QHBoxLayout()
        destBtnLayout.addWidget(self.destQueue)
        destBtnLayout.addWidget(self.destCollector)
        destBtnLayout.addStretch(1)
        
        self.clear = QPushButton(_("Clear"))
        self.filter = QPushButton(_("Filter URLs"))
        
        self.save = QPushButton(_("Add"))
        self.save.setIcon(QIcon(join(pypath, "icons", "add_small.png")))
        self.msg = QLabel("ERROR")
        lsp = self.msg.sizePolicy()
        lsp.setHorizontalPolicy(QSizePolicy.Ignored)
        self.msg.setSizePolicy(lsp)
        hbox = QHBoxLayout()
        hbox.addWidget(self.msg)
        hbox.addWidget(self.save)
        
        layout.addWidget(boxLabel)
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
