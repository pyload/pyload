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

from PyQt4.QtCore import Qt, SIGNAL, SLOT
from PyQt4.QtGui import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QGridLayout, QIcon, QLabel, QLineEdit

import logging
from os.path import join

from module.gui.Tools import WtDialogButtonBox

class AccountEdit(QDialog):
    """
        account editor widget
    """

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.setLayout(QGridLayout())
        l = self.layout()

        typeLabel = QLabel(_("Type"))
        loginLabel = QLabel(_("Login"))
        self.passwordLabel = QLabel()
        self.changePw = QCheckBox()
        self.changePw.setChecked(False)
        self.password = QLineEdit()
        self.password.setEnabled(False)
        self.password.setEchoMode(QLineEdit.Password)
        self.login = QLineEdit()
        self.acctype = QComboBox()

        self.buttons = WtDialogButtonBox(Qt.Horizontal)
        self.buttons.hideWhatsThisButton()
        self.save = self.buttons.addButton(QDialogButtonBox.Save)
        self.save.setDefault(False)
        self.save.setAutoDefault(False)
        self.cancel = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.cancel.setDefault(True)
        self.cancel.setAutoDefault(True)
        self.buttons.button(QDialogButtonBox.Save).setText(_("Save"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        self.connect(self.changePw, SIGNAL("toggled(bool)"), self.password, SLOT("setEnabled(bool)"))

        l.setRowMinimumHeight(3, 7)
        l.addLayout(self.buttons.layout(), 4, 0, 1, 3)
        l.addWidget(self.acctype, 0, 1, 1, 2)
        l.addWidget(self.login, 1, 1, 1, 2)
        l.addWidget(self.password, 2, 2)
        l.addWidget(self.changePw, 2, 1)
        l.addWidget(self.passwordLabel, 2, 0)
        l.addWidget(loginLabel, 1, 0)
        l.addWidget(typeLabel, 0, 0)

        self.setMinimumWidth(280)
        self.adjustSize()
        self.setFixedHeight(self.height())

        self.connect(self.save, SIGNAL("clicked()"), self.slotSave)
        self.connect(self.cancel, SIGNAL("clicked()"), self.reject)

    def slotSave(self):
        """
            save entered data
        """
        data = {"login": unicode(self.login.text()), "acctype": unicode(self.acctype.currentText()), "password": None}
        if self.changePw.isChecked():
            data["password"] = unicode(self.password.text())
        self.emit(SIGNAL("accountEditSave"), data)

    @staticmethod
    def newAccount(parent, types):
        """
            create empty editor instance
        """
        w = AccountEdit(parent)
        w.setWindowTitle(_("Create Account"))
        w.passwordLabel.setText(_("Password"))

        w.changePw.setChecked(True)
        w.password.setEnabled(True)
        w.acctype.addItems(types)
        w.acctype.setFocus(Qt.OtherFocusReason)
        w.adjustSize()
        return w

    @staticmethod
    def editAccount(parent, types, base):
        """
            create editor instance with given data
        """
        w = AccountEdit(parent)
        w.setWindowTitle(_("Edit Account"))
        w.passwordLabel.setText(_("New Password"))

        w.changePw.setChecked(True)
        w.acctype.addItems(types)
        i = w.acctype.findText(base.type)
        w.acctype.setCurrentIndex(i)
        w.acctype.setEnabled(False)

        w.login.setText(base.login)
        w.login.setEnabled(False)
        w.password.setFocus(Qt.OtherFocusReason)
        w.adjustSize()
        return w
