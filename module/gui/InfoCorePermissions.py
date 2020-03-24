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

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDialog, QDialogButtonBox, QGridLayout, QGroupBox, QIcon, QLabel, QVBoxLayout

import logging
from os.path import join

from module.gui.Tools import LineView, WtDialogButtonBox

class InfoCorePermissions(QDialog):
    """
        permissions info box
    """
    def __init__(self, parent, perms, activeperms):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")
        self.perms = perms
        self.activeperms = activeperms

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(self.windowFlags() &~ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Information"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        wt_width = 500  # QWhatsThis box width
        tabP = "&nbsp;&nbsp;"
        def p(s1, s2):
            return ("<table width='%d'><tr><td><b>" % wt_width + s1 + tabP + "-" + tabP + s2 + "</b></td></tr></table>")
        def d(s):
            return ("<table width='%d'><tr><td>" % wt_width + s + "</td></tr></table>")

        grid = QGridLayout()
        (admin, plist) = self.setup()

        admLbl = QLabel(admin[0])
        admVal = LineView(admin[1])
        #admKlbl = QLabel(admin[2])
        admLbl.setWhatsThis(p(admin[0], admin[3]) + d(admin[4]))

        grid.addWidget(admLbl,  1, 0)
        grid.addWidget(admVal,  1, 1)
        #grid.addWidget(admKlbl, 1, 3)
        for i, perm in enumerate(plist):
            lbl = QLabel(perm[0])
            val = LineView(perm[1])
            klbl = QLabel(perm[2])
            lbl.setWhatsThis(p(perm[0], perm[3]) + d(perm[4]))
            lbl. setDisabled(self.perms["admin"])
            val. setDisabled(self.perms["admin"])
            klbl.setDisabled(self.perms["admin"])
            grid.addWidget(lbl,  i + 2, 0)
            grid.addWidget(val,  i + 2, 1)
            grid.addWidget(klbl, i + 2, 3)

        grid.setRowMinimumHeight(0, 2)
        grid.setColumnMinimumWidth(2, 10)
        grid.setColumnStretch(2, 1)

        gp = QGroupBox(_("Server Permissions") + "     ")
        gp.setLayout(grid)

        hintLbl = QLabel("<b>" + _("Permissons were changed.<br>") + _("Takes effect on next login.") + "</b>")
        hintLbl.setWordWrap(True)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.closeBtn = self.buttons.addButton(QDialogButtonBox.Close)
        self.buttons.button(QDialogButtonBox.Close).setText(_("Close"))

        vbox = QVBoxLayout()
        vbox.addWidget(gp)
        if self.perms != self.activeperms:
            vbox.addWidget(hintLbl)
        vbox.addStretch(1)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        self.closeBtn.clicked.connect(self.accept)

    def setup(self):
        plist = []
        for k, perm in self.perms.iteritems():
            if k == "admin":
                name = _("Administrator")
                wt1  = _("Administrator has all permissions")
                wt2  = _("Needed for:<br>"
                         "- Restart pyLoad Server<br>"
                         "- Quit pyLoad Server"
                         )
                p = _("Yes") if perm else _("No")
                admin = (name, p, "(%s)"%k, wt1, wt2)
                continue
            elif k == "ACCOUNTS":
                name = _("Accounts")
                wt1  = _("Access Accounts")
                wt2  = _("Needed for:<br>"
                         "- Managing file hosting service accounts")
            elif k == "ADD":
                name = _("Add")
                wt1  = _("Add packages and links to Collector and Queue")
                wt2  = _("Also needed for:<br>"
                         "- Queue: Add Container<br>"
                         "- Collector: Moving links to another package<br>"
                         "- Toolbar: Clipboard Watcher")
            elif k == "DELETE":
                name = _("Delete")
                wt1  = _("Remove packages and links from Collector and Queue")
                wt2  = _("Also needed for:<br>"
                         "- Collector: Moving links to another package")
            elif k == "DOWNLOAD":
                name = _("Download")
                wt1  = _("Download from webinterface")
                wt2  = _("Needed for:<br>"
                         "- Downloading files from the server to your local machine")
            elif k == "LIST":
                name = _("List")
                wt1  = _("View Queue and Collector")
                wt2  = _("Needed for:<br>"
                         "- Overview tab<br>"
                         "- Queue tab<br>"
                         "- Collector tab<br>"
                         "- Status bar")
            elif k == "LOGS":
                name = _("Logs")
                wt1  = _("View Server Log")
                wt2  = _("Needed for:<br>"
                         "- Server Log tab")
            elif k == "MODIFY":
                name = _("Modify")
                wt1  = _("Modify some attributes of downloads")
                wt2  = _("Needed for:<br>"
                         "- Toolbar: Abort All and Restart Failed<br>"
                         "- Queue and Collector: Push To Queue, Pull Out, Restart, Edit and Abort<br>"
                         "- Add Package: Password<br>"
                         "- Sorting packages and sorting links within packages")
            elif k == "SETTINGS":
                name = _("Settings")
                wt1  = _("Access settings")
                wt2  = _("Needed for:<br>"
                         "- Server Settings tab<br>"
                         "- Toolbar: Download Speed Limit<br>"
                         "- ClickNLoad Forwarding: Get Remote Port from Server Settings")
            elif k == "STATUS":
                name = _("Status")
                wt1  = _("View and change server status")
                wt2  = _("Needed for:<br>"
                         "- Updating Overview, Queue and Collector<br>"
                         "- Toolbar: Run, Pause and Stop feature to set server status 'Paused'<br>"
                         "- Captchas<br>"
                         "- Status bar: Free space in the download folder")
            else:
                name = k
                wt1 = "&#60;unknown&#62;"
                wt2 = ""
            p = _("Yes") if perm else _("No")
            plist.append((name, p, "(%s)"%k, wt1, wt2))
        plist = sorted(plist, key=lambda d: d[0])
        return (admin, plist)

