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

# import pynotify before logging to avoid gtk warning on some systems
try:
    havePynotify = True
    import pynotify
except ImportError:
    havePynotify = False

from module.gui import USE_QT5
if USE_QT5:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
else:
    from PyQt4.QtCore import QObject

import logging, os
from os.path import join

class Notification(QObject):
    def __init__(self, tray):
        QObject.__init__(self)
        self.log = logging.getLogger("guilog")
        self.tray = tray

        self.usePynotify = False
        if os.name != "nt":
            if not havePynotify:
                self.log.info("Notification: Pynotify not installed, falling back to qt tray notification")
                return
            try:
                self.usePynotify = pynotify.init(_("pyLoad Client"))
            except Exception:
                self.usePynotify = False
            if not self.usePynotify:
                self.log.error("Notification: Pynotify initialization failed")

    def slotShowMessage(self, body):
        if self.usePynotify:
            n = pynotify.Notification(_("pyLoad Client"), body, join(pypath, "icons", "logo.png"))
            try:
                n.set_hint_string("x-canonical-append", "")
            except Exception:
                self.log.debug9("Notification: set_hint_string failed")
            n.show()
        else:
            self.tray.showMessage(_("pyLoad Client"), body)

