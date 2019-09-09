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
        
        self.textChangeCount = 0
        self.undo = False
        self.undoText = None
        
        self.setObjectName("New Package Dock")
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))
        self.widget = NewPackageWindow(self)
        self.setFilterBtnText()
        whatsThis = (self.widget.filter.text(), _("Extracts the URLs from the pasted/dropped text and removes duplicates."))
        self.widget.filter.setWhatsThis(whatsThisFormat(*whatsThis))
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
            self.widget.slotMsgShow("<b>" + "&nbsp;" + "&nbsp;" + _("Error, no URLs given.") + "</b>")
            return
        queue = self.widget.destQueue.isChecked()
        self.emit(SIGNAL("done"), unicode(self.widget.nameInput.text()), lines, queue, pw)
        self.widget.nameInput.setText("")
        self.widget.passwordInput.setText("")
        self.widget.box.clear()
    
    def setFilterBtnText(self):
        if not self.undo:
            self.widget.filter.setText(_("Filter URLs"))
        else:
            self.widget.filter.setText(_("Undo Filter URLs"))
    
    def slotFilterBtnClicked(self):
        if not self.undo:
            text = self.widget.box.toPlainText()
            if text.trimmed().isEmpty():
                return
            self.widget.box.setEnabled(False)
            self.widget.filter.setEnabled(False)
            self.undoText = text
            self.emit(SIGNAL("parseUri"), "packagedock", unicode(text))
        else:
            self.widget.box.setPlainText(self.undoText)
            self.undo = False
            self.setFilterBtnText()
    
    def slotBoxTextChanged(self):
        if self.undo and self.textChangeCount > 0:
            self.undo = False
            self.setFilterBtnText()
        else:
            self.textChangeCount += 1
    
    def parseUriResult(self, result):
        self.textChangeCount = 0
        self.widget.box.setPlainText(result)
        self.undo = True
        self.setFilterBtnText()
        self.widget.box.setEnabled(True)
        self.widget.filter.setEnabled(True)
    
    def appendClipboardLinks(self, links):
        text = unicode("")
        for l in links:
            text += l + "\n"
        self.widget.box.addText(text)
    
    def slotClearBtnClicked(self):
        if self.widget.box.toPlainText().isEmpty():
            self.widget.nameInput.setText("")
            self.widget.passwordInput.setText("")
        self.widget.box.clear()     # also turns filter undo off again
    
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
        whatsThis = (linksLabel.text(), _("One URL (Link) per line.<br>For manual text editing you may want to deactivate") + " '" + self.append.text() + "'.")
        self.box.setWhatsThis(whatsThisFormat(*whatsThis))
        self.destQueue     = QRadioButton(_("Queue"))
        self.destCollector = QRadioButton(_("Collector"))
        destBtnLayout = QHBoxLayout()
        destBtnLayout.addWidget(self.destQueue)
        destBtnLayout.addWidget(self.destCollector)
        destBtnLayout.addStretch(1)
        self.destAutoSelect = QCheckBox(_("Select with tab"))
        
        self.clear = QPushButton(_("Clear"))
        whatsThis = (self.clear.text(), _("Clears the URL box.<br>A subsequent click also clears Name and Password."))
        self.clear.setWhatsThis(whatsThisFormat(*whatsThis))
        self.filter = QPushButton()
        
        self.save = QPushButton(_("Create"))
        self.save.setIcon(QIcon(join(pypath, "icons", "add_small.png")))
        self.msg = QLabel("ERROR")
        s = "QWidget { color: crimson; background-color: %s }" % QColor(Qt.gray).name()     # red text color on gray background
        self.msg.setStyleSheet(s)
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
        self.connect(self.filter, SIGNAL("clicked()"), self.dock.slotFilterBtnClicked)
        self.connect(self.box, SIGNAL("textChanged()"), self.dock.slotBoxTextChanged)
        self.connect(self.append, SIGNAL("toggled(bool)"), self.box.slotAppendToggled)
        self.box.slotAppendToggled(self.append.isChecked())
        self.connect(self.clear, SIGNAL("clicked()"), self.dock.slotClearBtnClicked)
    
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
    
    def addText(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        self.setTextCursor(cursor)
        lineLength = cursor.block().length() - 1
        if lineLength > 0:
            self.insertPlainText("\n")
        self.insertPlainText(text)
    
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
