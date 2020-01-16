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

from PyQt4.QtGui import QAction, QApplication, QIcon, QMenu, QSystemTrayIcon

import logging
from os.path import join

class TrayIcon(QSystemTrayIcon):
    def __init__(self, appIconSet):
        QSystemTrayIcon.__init__(self)
        self.log = logging.getLogger("guilog")
        self.appIconSet = appIconSet

        self.menu = QMenu()
        self.showAction = QAction("show/hide", self.menu)
        self.showAction.setIcon(QIcon(join(pypath, "icons", "logo.png")))
        self.setShowActionText(False)
        self.menu.addAction(self.showAction)
        self.captchaAction = QAction(_("Captcha"), self.menu)
        self.menu.addAction(self.captchaAction)
        self.menuAdd = self.menu.addMenu(self.appIconSet["add_small"], _("Add"))
        self.addPackageAction = self.menuAdd.addAction(_("Package"))
        self.addLinksAction = self.menuAdd.addAction(_("Links"))
        self.addContainerAction = self.menuAdd.addAction(_("Container"))
        self.menu.addSeparator()
        self.exitAction = QAction(self.appIconSet["abort_small"], _("Exit"), self.menu)
        self.menu.addAction(self.exitAction)
        self.setContextMenu(self.menu)
        if self.log.isEnabledFor(logging.DEBUG9):
            self.menu.addSeparator()
            self.menuDebug = self.menu.addMenu("Debug")
            self.debugTrayAction = self.menuDebug.addAction("Tray")
            self.debugMsgBoxTest1Action = self.menuDebug.addAction("MessageBox Test 1")
            self.debugMsgBoxTest2Action = self.menuDebug.addAction("MessageBox Test 2")
            self.debugKillAction = self.menuDebug.addAction("kill")

        # disable/greyout menu entries
        self.showAction.setEnabled(False)
        self.captchaAction.setEnabled(False)
        self.menuAdd.setEnabled(False)

    def setupIcon(self, size):
        if size == "24x24":
            icon = QIcon(join(pypath, "icons", "logo-gui24x24.png"))
        elif size == "64x64":
            icon = QIcon(join(pypath, "icons", "logo-gui64x64.png"))
        else:
            icon = QIcon()
        self.setIcon(icon)

    def setShowActionText(self, show):
        if show:
            self.showAction.setText(_("Show pyLoad Client"))
        else:
            self.showAction.setText(_("Hide pyLoad Client"))

    def clicked(self, reason):
        # forbid all actions when a modal dialog is visible, this is mainly for ms windows os
        if QApplication.activeModalWidget() is not None:
            if self.contextMenu() is not None:
                self.menu.hide()
                self.setContextMenu(None)
                self.log.debug4("TrayIcon.clicked: context menu deactivated")
            self.log.debug4("TrayIcon.clicked: click ignored")
            return
        elif self.contextMenu() is None:
            self.setContextMenu(self.menu)
            self.log.debug4("TrayIcon.clicked: context menu reactivated")
            if reason == QSystemTrayIcon.Context:
                self.menu.show()
                self.log.debug4("TrayIcon.clicked: show reactivated context menu")
                return

        if self.showAction.isEnabled():
            if reason == QSystemTrayIcon.Trigger:
                self.showAction.trigger()

