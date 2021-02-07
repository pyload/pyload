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
"""

from module.gui.PyQtVersion import USE_PYQT5
if USE_PYQT5:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget
else:
    from PyQt4.QtCore import Qt
    from PyQt4.QtGui import QCheckBox, QComboBox, QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget

import logging

from module.gui.Tools import whatsThisFormat

class AdvancedSelect(QWidget):
    """
        Advanced Select/Deselect of links and packages
    """

    def __init__(self, parent=None, flags=Qt.Widget):
        QWidget.__init__(self, parent, flags)
        self.log = logging.getLogger("guilog")

        self.columnCmb = QComboBox()
        self.columnCmb.addItem(_("Name:"),   "name_column")
        self.columnCmb.addItem(_("Plugin:"), "plugin_column")
        self.columnCmb.addItem(_("Status:"), "status_column")
        self.patternEdit = QComboBox()
        self.patternEdit.setEditable(True)
        self.patternEdit.completer().setCaseSensitivity(Qt.CaseSensitive)
        self.patternEdit.setInsertPolicy(QComboBox.NoInsert)
        self.patternEdit.lineEdit().setPlaceholderText(_("Enter a search pattern"))
        lsp = self.patternEdit.sizePolicy()
        lsp.setHorizontalPolicy(QSizePolicy.Expanding)
        self.patternEdit.setSizePolicy(lsp)
        self.modeCmb = QComboBox()
        self.modeCmb.addItem(_("Text"),     "string")
        self.modeCmb.addItem(_("Wildcard"), "wildcard")
        self.modeCmb.addItem(_("RegExp"),   "regexp")
        self.clearBtn = QPushButton(_("Clear Pattern"))

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.columnCmb)
        hbox1.addWidget(self.patternEdit)
        hbox1.addWidget(self.modeCmb)
        hbox1.addWidget(self.clearBtn)

        self.caseCb = QCheckBox(_("Match case"))
        self.itemsCmb = QComboBox()
        self.itemsCmb.addItem(_("Packages"), "packages")
        self.itemsCmb.addItem(_("Links"),    "links")
        self.selectBtn = QPushButton(_("Select"))
        self.deselectBtn = QPushButton(_("Deselect"))
        self.hideBtn = QPushButton(_("Hide"))

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.caseCb)
        hbox2.addWidget(self.itemsCmb)
        hbox2.addStretch(1)
        hbox2.addWidget(self.selectBtn)
        hbox2.addWidget(self.deselectBtn)
        hbox2.addStretch(1)
        hbox2.addWidget(self.hideBtn)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        self.setLayout(vbox)

        self.clearBtn.clicked.connect(self.patternEdit.clearEditText)
        self.selectBtn.clicked.connect(self.slotAddToHistory)
        self.deselectBtn.clicked.connect(self.slotAddToHistory)

    def slotAddToHistory(self):
        text = unicode(self.patternEdit.currentText())
        if text:
            if self.patternEdit.findText(text, Qt.MatchFixedString | Qt.MatchCaseSensitive) == -1:
                self.patternEdit.insertItem(0, text)
                self.patternEdit.setCurrentIndex(0)

