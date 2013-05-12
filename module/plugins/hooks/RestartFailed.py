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


class RestartFailed(Hook):
    __name__ = "RestartFailed"
    __version__ = "1.5"
    __description__ = "Automatically restart failed/aborted downloads"
    __config__ = [
        ("activated", "bool", "Activated", "True"),
        ("dlFail", "bool", "Restart when download fail", "True"),
        ("dlFail_n", "int", "Only when failed downloads are at least", "5"),
        ("dlFail_i", "int", "Only when elapsed time since last restart is (min)", "10"),
        ("dlPrcs", "bool", "Restart after all downloads are processed", "True"),
        ("recnt", "bool", "Restart after reconnecting", "True"),
        ("rsLoad", "bool", "Restart on plugin activation", "False")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    def restart(self, arg=None):
        # self.logDebug("self.restart")
        self.info["timerflag"] = False
        self.info["dlfailed"] = 0
        self.core.api.restartFailed()
        self.logDebug("self.restart: self.core.api.restartFailed")
        self.info["lastrstime"] = time()

    def periodical(self):
        # self.logDebug("self.periodical")
        if self.info["timerflag"]:
            self.restart()

    def checkInterval(self, arg=None):
        # self.logDebug("self.checkInterval")
        now = time()
        lastrstime = self.info["lastrstime"]
        interval = self.getConfig("dlFail_i") * 60
        if now < lastrstime + interval:
            self.info["timerflag"] = True
        else:
            self.restart()

    def checkFailed(self, pyfile):
        # self.logDebug("self.checkFailed")
        self.info["dlfailed"] += 1
        curr = self.info["dlfailed"]
        max = self.getConfig("dlFail_n")
        if curr >= max:
            self.checkInterval()

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

    def configEvents(self, plugin=None, name=None, value=None):
        # self.logDebug("self.configEvents")
        self.interval = self.getConfig("dlFail_i") * 60
        dlFail = self.getConfig("dlFail")
        dlPrcs = self.getConfig("dlPrcs")
        recnt = self.getConfig("recnt")
        if dlPrcs:
            self.addEvent("allDownloadsProcessed", self.checkInterval)
        else:
            self.removeEvent("allDownloadsProcessed", self.checkInterval)
            if not dlFail:
                self.info["timerflag"] = False
        if recnt:
            self.addEvent("afterReconnecting", self.restart)
        else:
            self.removeEvent("afterReconnecting", self.restart)

    def unload(self):
        # self.logDebug("self.unload")
        self.removeEvent("pluginConfigChanged", self.configEvents)
        self.removeEvent("downloadFailed", self.checkFailed)
        self.removeEvent("allDownloadsProcessed", self.checkInterval)
        self.removeEvent("afterReconnecting", self.restart)

    def coreReady(self):
        # self.logDebug("self.coreReady")
        self.info = {"dlfailed": 0, "lastrstime": 0, "timerflag": False}
        if self.getConfig("rsLoad"):
            self.restart()
        self.addEvent("downloadFailed", self.checkFailed)
        self.addEvent("pluginConfigChanged", self.configEvents)
        self.configEvents()
