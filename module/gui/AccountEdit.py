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

from os.path import join

class AccountEdit(QWidget):
    """
        account editor widget
    """
    
    def __init__(self):
        QMainWindow.__init__(self)

        self.setWindowTitle(_("Edit account"))
        self.setWindowIcon(QIcon(join(pypath, "icons","logo.png")))
        
        self.setLayout(QGridLayout())
        l = self.layout()
        
        typeLabel = QLabel(_("Type"))
        loginLabel = QLabel(_("Login"))
        passwordLabel = QLabel(_("New password"))
        changePw = QCheckBox()
        changePw.setChecked(False)
        self.changePw = changePw
        password = QLineEdit()
        password.setEnabled(False)
        password.setEchoMode(QLineEdit.Password)
        self.password = password
        login = QLineEdit()
        self.login = login
        acctype = QComboBox()
        self.acctype = acctype
        
        save = QPushButton(_("Save"))
        
        self.connect(changePw, SIGNAL("toggled(bool)"), password, SLOT("setEnabled(bool)"))
        
        l.addWidget(save, 3, 0, 1, 3)
        l.addWidget(acctype, 0, 1, 1, 2)
        l.addWidget(login, 1, 1, 1, 2)
        l.addWidget(password, 2, 2)
        l.addWidget(changePw, 2, 1)
        l.addWidget(passwordLabel, 2, 0)
        l.addWidget(loginLabel, 1, 0)
        l.addWidget(typeLabel, 0, 0)
        
        self.connect(save, SIGNAL("clicked()"), self.slotSave)
    
    def slotSave(self):
        """
            save entered data
        """
        data = {"login": str(self.login.text()), "acctype": str(self.acctype.currentText()), "password": False}
        if self.changePw.isChecked():
            data["password"] = str(self.password.text())
        self.emit(SIGNAL("done"), data)
    
    @staticmethod
    def newAccount(types):
        """
            create empty editor instance
        """
        w = AccountEdit()
        w.setWindowTitle(_("Create account"))
        
        w.changePw.setChecked(True)
        w.password.setEnabled(True)
        
        w.acctype.addItems(types)
        
        return w
    
    @staticmethod
    def editAccount(types, base):
        """
            create editor instance with given data
        """
        w = AccountEdit()
        
        w.acctype.addItems(types)
        w.acctype.setCurrentIndex(types.index(base["type"]))
        
        w.login.setText(base["login"])
        
        return w
