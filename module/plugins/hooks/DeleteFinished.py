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
from time import time


class DeleteFinished(Hook):
    __name__ = "DeleteFinished"
    __version__ = "0.3"
    __description__ = "Automatically delete finished packages from queue"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("interval", "int", "Delete every (hours)", "72"),
        ("sleep", "bool", "Sleep mode (useful if interval is small)", "False")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    def periodical(self):
        # self.logDebug("self.periodical")
        self.core.api.deleteFinished()
        self.logDebug("called self.core.api.deleteFinished")
        if self.getConfig("sleep"):
            self.interval = 0

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

    def enPeriodical(self):
        # self.logDebug("self.enPeriodical")
        if not self.interval:
            self.interval = self.getConfig("interval") * 3600

    def configEvents(self, plugin, name, value):
        # self.logDebug("self.configEvents")
        self.enPeriodical()
        if self.getConfig("sleep"):
            self.addEvent("packageFinished", self.enPeriodical)
        else:
            self.removeEvent("packageFinished", self.enPeriodical)

    def unload(self):
        # self.logDebug("self.unload")
        self.removeEvent("pluginConfigChanged", self.configEvents)
        self.removeEvent("packageFinished", self.enPeriodical)
        self.interval = 0

    def coreReady(self):
        # self.logDebug("self.coreReady")
        self.interval = 0
        self.addEvent("pluginConfigChanged", self.configEvents)
        self.configEvents(None, None, None)
