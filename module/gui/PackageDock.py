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
from module.gui.Tools import whatsThisFormat

class NewPackageDock(QDockWidget):
    def __init__(self):
        self.paintEventSignal = False
        QDockWidget.__init__(self, _("New Package"))
        self.log = logging.getLogger("guilog")
        
        self.geo = None
        self.paintEventCounter = int(0)
        
        self.setObjectName("New Package Dock")
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))
        self.widget = NewPackageWindow(self)
        self.defaultSettings()
        self.setWidget(self.widget)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
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
    
    def defaultSettings(self):
        self.widget.append.setChecked(True)
        self.widget.destQueue.setChecked(False)
        self.widget.destCollector.setChecked(True)
        self.widget.destAutoSelect.setChecked(True)
    
    def getSettings(self):
        settings = {}
        #settings["append"]     = self.widget.append.isChecked()
        settings["queue"]      = self.widget.destQueue.isChecked()
        settings["autoSelect"] = self.widget.destAutoSelect.isChecked()
        return settings
    
    def setSettings(self, settings):
        #self.widget.append.setChecked         (settings["append"])
        self.widget.destQueue.setChecked      (settings["queue"])
        self.widget.destCollector.setChecked  (not settings["queue"])
        self.widget.destAutoSelect.setChecked (settings["autoSelect"])
    
    def closeEvent(self, event):
        if self.isFloating():
            self.emit(SIGNAL("newPackDockClosed"))
        self.hide()
        event.ignore()
    
    def paintEvent(self, event):
        QDockWidget.paintEvent(self, event)
        if self.isFloating():
            self.geo = self.geometry()
        self.paintEventCounter += 1
        if self.paintEventSignal:
            self.paintEventSignal = False
            self.emit(SIGNAL("newPackDockPaintEvent"))
    
    def moveEvent(self, event):
        if self.isFloating():
            self.geo = self.geometry()

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
        
        self.append = QCheckBox(_("Append URLs"))
        whatsThis = (self.append.text(), _("Append pasted/dropped text instead of inserting it at the cursor postion."))
        self.append.setWhatsThis(whatsThisFormat(*whatsThis))
        self.destQueue     = QRadioButton(_("Queue"))
        self.destCollector = QRadioButton(_("Collector"))
        destBtnLayout = QHBoxLayout()
        destBtnLayout.addWidget(self.destQueue)
        destBtnLayout.addWidget(self.destCollector)
        destBtnLayout.addStretch(1)
        self.destAutoSelect = QCheckBox(_("Select with tab"))
        
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
        layout.addWidget(self.append)
        layout.addWidget(self.filter)
        layout.addWidget(self.clear)
        layout.addLayout(destBtnLayout)
        layout.addWidget(self.destAutoSelect)
        layout.addLayout(hbox)
        
        self.adjustSize()
        self.msg.setFixedHeight(self.save.height())
        self.slotMsgHide()
        
        self.connect(self.save, SIGNAL("clicked()"), self.dock.slotDone)
        self.connect(self.clear, SIGNAL("clicked()"), self.box.clear)
        self.connect(self.filter, SIGNAL("clicked()"), self.dock.parseUri)
        self.connect(self.append, SIGNAL("toggled(bool)"), self.box.slotAppendToggled)
        self.box.slotAppendToggled(self.append.isChecked())
    
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
        self.append = True
    
    def slotAppendToggled(self, status):
        self.append = status
    
    def insertFromMimeData(self, source):
        cursor = self.textCursor()
        if self.append:
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
            self.setTextCursor(cursor)
            lineLength = cursor.block().length() - 1
            if lineLength > 0:
                self.insertPlainText("\n")
        QPlainTextEdit.insertFromMimeData(self, source)
        if self.append:
            self.insertPlainText("\n")
