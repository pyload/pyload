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
    from PyQt5.QtCore import QObject
else:
    from PyQt4.QtCore import QObject

import logging, os
from os.path import join

class Notification(QObject):
    def __init__(self, desktopNotifications, tray):
        QObject.__init__(self)
        self.log = logging.getLogger("guilog")
        self.desktopNotifications = desktopNotifications
        self.tray = tray
        if os.name != "nt":
            if self.desktopNotifications == "notify2":
                import notify2
                self.notify = notify2
                try:
                    self.notify.init(_("pyLoad Client"))
                    self.log.info("Using notify2 for desktop notifications")
                except Exception:
                    self.desktopNotifications = "qt_tray"
                    self.log.warning("Desktop notifications: notify2 init failed, falling back to Qt tray notifications")
            elif self.desktopNotifications == "pynotify":
                import pynotify
                self.notify = pynotify
                try:
                    self.notify.init(_("pyLoad Client"))
                    self.log.info("Using pynotify for desktop notifications")
                except Exception:
                    self.desktopNotifications = "qt_tray"
                    self.log.warning("Desktop notifications: pynotify init failed, falling back to Qt tray notifications")
            elif self.desktopNotifications == "qt_tray":
                self.log.info("Using Qt tray for desktop notifications")
            else:
                raise ValueError("Invalid desktop notification system: %s" % str(self.desktopNotifications))
        else:
            self.log.info("Using Qt tray for desktop notifications on Windows OS")

    def slotShowMessage(self, body):
        if self.desktopNotifications != "qt_tray":
            if self.desktopNotifications == "notify2":
                self.notify.init(_("pyLoad Client"))    # workaround for DBusException in n.show()
            n = self.notify.Notification(_("pyLoad Client"), body, join(pypath, "icons", "logo.png"))
            try:
                n.set_hint_string("x-canonical-append", "")
            except Exception:
                self.log.debug9("Desktop notifications: set_hint_string failed")
            try:
                n.show()
            except Exception:
                self.log.error("Desktop notifications: n.show() failed")
        else:
            self.tray.showMessage(_("pyLoad Client"), body)


