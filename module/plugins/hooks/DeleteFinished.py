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

    @author: Walter Purcaro
"""

from module.plugins.Hook import Hook
from module.database import style
from time import time


class DeleteFinished(Hook):
    __name__ = "DeleteFinished"
    __version__ = "1.01"
    __description__ = "Automatically delete finished packages from queue"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("interval", "int", "Delete every (hours)", "72")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    ## overwrited methods ##
    def periodical(self):
        # self.logDebug("self.periodical")
        if not self.info["sleep"]:
            self.logInfo("self.deleteFinished")
            self.deleteFinished()
            self.info["sleep"] = True
            self.addEvent("packageFinished", self.wakeup)

    def pluginConfigChanged(self, plugin, name, value):
        # self.logDebug("self.pluginConfigChanged")
        if name == "interval" and value != self.interval:
            self.interval = value
            self.initPeriodical()

    def unload(self):
        # self.logDebug("self.unload")
        self.removeEvent("packageFinished", self.wakeup)

    def coreReady(self):
        # self.logDebug("self.coreReady")
        self.info = {"sleep": True}
        interval = self.getConfig("interval") * 3600
        self.pluginConfigChanged("DeleteFinished", "interval", interval)
        self.addEvent("packageFinished", self.wakeup)

    ## own methods ##
    @style.queue
    def deleteFinished(self):
        self.c.execute("DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE package=packages.id AND status NOT IN (0,4))")
        self.c.execute("DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id=links.package)")

    def wakeup(self, pypack):
        # self.logDebug("self.wakeup")
        self.removeEvent("packageFinished", self.wakeup)
        self.info["sleep"] = False

    ## event managing ##
    def addEvent(self, event, handler):
        if event in self.manager.events:
            if handler not in self.manager.events[event]:
                self.manager.events[event].append(handler)
                # self.logDebug("self.addEvent: " + event + ": added handler")
            else:
                # self.logDebug("self.addEvent: " + event + ": NOT added handler")
                return False
        else:
            self.manager.events[event] = [handler]
            # self.logDebug("self.addEvent: " + event + ": added event and handler")
        return True

    def removeEvent(self, event, handler):
        if event in self.manager.events and handler in self.manager.events[event]:
            self.manager.events[event].remove(handler)
            # self.logDebug("self.removeEvent: " + event + ": removed handler")
            return True
        else:
            # self.logDebug("self.removeEvent: " + event + ": NOT removed handler")
            return False
