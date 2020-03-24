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

from module.gui import USE_QT5
if USE_QT5:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
else:
    from PyQt4.QtCore import Qt
    from PyQt4.QtGui import QCheckBox, QComboBox, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

import logging

from module.gui.Tools import whatsThisFormat

class AdvancedSelect(QWidget):
    """
        Advanced Select/Deselect of links and packages
    """

    # enum for QRegExp pattern syntax
    class MODE_IDX(object):
        STRING   = -1
        WILDCARD = -1
        REGEXP   = -1

    def __init__(self, parent=None, flags=Qt.Widget):
        QWidget.__init__(self, parent, flags)
        self.log = logging.getLogger("guilog")

        self.modeIdx = self.MODE_IDX()

        self.patternEditLbl = QLabel()
        self.patternEditLbl.setText(_("Name:"))
        self.patternEdit = QComboBox()
        self.patternEdit.setEditable(True)
        self.patternEdit.completer().setCaseSensitivity(Qt.CaseSensitive)
        self.patternEdit.setInsertPolicy(QComboBox.NoInsert)
        self.patternEdit.lineEdit().setPlaceholderText(_("Enter a search pattern"))
        lsp = self.patternEdit.sizePolicy()
        lsp.setHorizontalPolicy(QSizePolicy.Expanding)
        self.patternEdit.setSizePolicy(lsp)
        self.clearBtn = QPushButton(_("Clear Pattern"))
        self.selectBtn = QPushButton(_("Select"))
        self.deselectBtn = QPushButton(_("Deselect"))
        self.linksCb = QCheckBox(_("Links"))
        wt = _("Search for links instead of packages.<br>Links are searched in preselected packages or in all packages when there are no packages selected.")
        self.linksCb.setWhatsThis(whatsThisFormat(self.linksCb.text(), wt))
        self.caseCb = QCheckBox(_("Match case"))
        self.modeCmb = QComboBox()
        self.modeCmb.addItem(_("String"))       ;self.modeIdx.STRING   = 0  # combobox indexes in the order the items are added
        self.modeCmb.addItem(_("Wildcard"))     ;self.modeIdx.WILDCARD = 1
        self.modeCmb.addItem(_("RegExp"))       ;self.modeIdx.REGEXP   = 2
        self.hideBtn = QPushButton(_("Hide"))

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.patternEditLbl)
        hbox1.addWidget(self.patternEdit)
        hbox1.addWidget(self.clearBtn)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.modeCmb)
        hbox2.addWidget(self.caseCb)
        hbox2.addStretch(1)
        hbox2.addWidget(self.selectBtn)
        hbox2.addWidget(self.deselectBtn)
        hbox2.addWidget(self.linksCb)
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

