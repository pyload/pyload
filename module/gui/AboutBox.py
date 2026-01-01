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
    from PyQt5.QtGui import QFont, QIcon, QPixmap
    from PyQt5.QtWidgets import QApplication, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
else:
    from PyQt4.QtCore import Qt
    from PyQt4.QtGui import QApplication, QDialog, QDialogButtonBox, QFont, QHBoxLayout, QIcon, QLabel, QPixmap, QPushButton, QVBoxLayout

import logging, os
from os.path import join

from module.gui.Tools import WtDialogButtonBox

class AboutBox(QDialog):
    """
        about-box
    """

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("About pyLoad Client"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignTop)
        pix = QPixmap(join(pypath, "icons", "logo-gui.png"))
        self.logo.setPixmap(pix)
        self.text1 = QLabel()
        self.text1.setAlignment(Qt.AlignTop)
        text1font = QFont(self.text1.font())
        text1fontSize = text1font.pointSize()
        if text1fontSize != -1:
            text1font.setPointSize(text1fontSize + 2)
        text1font.setBold(True)
        self.text1.setFont(text1font)
        self.text2 = QLabel()
        self.text2.setAlignment(Qt.AlignTop)
        self.text3 = QLabel()
        self.text3.setAlignment(Qt.AlignTop)
        self.text3.setTextFormat(Qt.PlainText)
        self.text4 = QLabel()
        self.text4.setAlignment(Qt.AlignTop)

        vboxText = QVBoxLayout()
        vboxText.setContentsMargins(0, 0, 0, 0)
        vboxText.setSpacing(0)
        vboxText.addWidget(self.text1)
        vboxText.addWidget(self.text2)
        vboxText.addSpacing(20)
        vboxText.addWidget(self.text3)
        vboxText.addSpacing(20)
        vboxText.addWidget(self.text4)
        vboxText.addStretch(1)

        hbox = QHBoxLayout()
        hbox.addWidget(self.logo)
        hbox.addSpacing(20)
        hbox.addLayout(vboxText)
        hbox.addSpacing(20)
        hbox.addStretch(1)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.buttons.hideWhatsThisButton()
        self.okBtn = self.buttons.addButton(QDialogButtonBox.Ok)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.copyBtn = QPushButton(_("Copy to Clipboard"))
        self.buttons.addButton(self.copyBtn, QDialogButtonBox.ActionRole)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addSpacing(5)
        vbox.addStretch(1)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.okBtn.clicked.connect(self.accept)
        self.copyBtn.clicked.connect(self.slotCopyToClipboard)

    def slotCopyToClipboard(self):
        txt = self.text3.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(txt)

    def exec_(self, version, internalversion):
        import platform
        import struct
        if USE_PYQT5:
            from PyQt5.QtCore import QT_VERSION_STR
        else:
            from PyQt4.QtCore import QT_VERSION_STR
        txt1 = _("pyLoad Client") + " v" + version
        self.text1.setText(txt1)
        txt2 = "2008-2016 the pyLoad Team"
        self.text2.setText(txt2)
        txt3  = "Version: " + version
        txt3 += "\nInternal version: " + internalversion
        txt3 += "\n\nPlatform: " + platform.platform()
        if os.name == "nt":
            if "PROGRAMFILES(X86)" in os.environ:
                txt3 += " (64bit)"
            else:
                txt3 += " (32bit)"
        txt3 += "\nPython version: " + platform.python_version() + " (%dbit)" % (struct.calcsize("P") * 8)
        txt3 += "\nQt version: " + QT_VERSION_STR
        try:
            if USE_PYQT5:
                from PyQt5.pyqtconfig import Configuration
            else:
                from PyQt4.pyqtconfig import Configuration
            cfg = Configuration()
            sipver = cfg.sip_version_str
            pyqtver = cfg.pyqt_version_str
        except Exception:
            if USE_PYQT5:
                from PyQt5.Qt import PYQT_VERSION_STR
            else:
                from PyQt4.Qt import PYQT_VERSION_STR
            from sip import SIP_VERSION_STR
            sipver = SIP_VERSION_STR
            pyqtver = PYQT_VERSION_STR
        txt3 += "\nPyQt version: " + pyqtver
        txt3 += "\nSIP version: " + sipver
        self.text3.setText(txt3)
        txt4 = "Process ID: " + str(os.getpid())
        self.text4.setText(txt4)
        self.okBtn.setFocus(Qt.OtherFocusReason)
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())
        return QDialog.exec_(self)

