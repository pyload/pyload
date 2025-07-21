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
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout
else:
    from PyQt4.QtCore import Qt
    from PyQt4.QtGui import QDialog, QDialogButtonBox, QIcon, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout

import logging
from os.path import join

from module.gui.Tools import WtDialogButtonBox

class PackageEdit(QDialog):
    """
        package edit dialog
    """

    def __init__(self, parent):
        self.log = logging.getLogger("guilog")

        self.id = None
        self.old_name = None
        self.old_folder = None
        self.old_password = None

        # custom return codes
        self.SAVE = 100
        self.CANCEL = 101
        self.CANCELALL = 102

        QDialog.__init__(self, parent)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Edit Package"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        vbox = QVBoxLayout()
        spacing = 15

        lbl = QLabel(_("Name"))
        vbox.addWidget(lbl)
        self.name = QLineEdit()
        vbox.addWidget(self.name)
        vbox.addSpacing(spacing)

        lbl = QLabel(_("Folder"))
        vbox.addWidget(lbl)
        self.folder = QLineEdit()
        vbox.addWidget(self.folder)
        vbox.addSpacing(spacing)

        lbl = QLabel(_("Password"))
        vbox.addWidget(lbl)
        self.password = QPlainTextEdit()
        self.password.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.password.setTabChangesFocus(True)
        vbox.addWidget(self.password)
        vbox.addSpacing(spacing)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.buttons.hideWhatsThisButton()
        self.saveBtn = self.buttons.addButton(QDialogButtonBox.Save)
        self.saveBtn.setDefault(True)
        self.saveBtn.setAutoDefault(True)
        self.saveBtn.setText(_("Save"))
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.cancelBtn.setDefault(False)
        self.cancelBtn.setAutoDefault(False)
        self.cancelBtn.setText(_("Cancel"))
        self.cancelAllBtn = self.buttons.addButton(QDialogButtonBox.No)
        self.cancelAllBtn.setDefault(False)
        self.cancelAllBtn.setAutoDefault(False)
        self.cancelAllBtn.setText(_("Cancel Remaining"))
        vbox.addLayout(self.buttons.layout())

        self.setLayout(vbox)
        self.adjustSize()
        self.resize(750, 0)

        self.saveBtn.clicked.connect(self.slotSaveClicked)
        self.cancelBtn.clicked.connect(self.slotCancelClicked)
        self.cancelAllBtn.clicked.connect(self.slotCancelAllClicked)

    def slotSaveClicked(self):
        self.done(self.SAVE)

    def slotCancelClicked(self):
        self.done(self.CANCEL)

    def slotCancelAllClicked(self):
        self.done(self.CANCELALL)

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

