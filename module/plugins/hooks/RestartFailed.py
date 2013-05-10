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
    __version__ = "1.1"
    __description__ = "Automatically restart failed/aborted downloads"
    __config__ = [
        ("activated", "bool", "Activated", "True"),
        ("dlFail", "bool", "Restart when download fail", "True"),
        ("dlFail_n", "int", "Only when failed/aborted downloads are at least", "5"),
        ("dlFail_i", "int", "Only when elapsed time since last restart is (min)", "10"),
        ("dlPrcs", "bool", "Restart after all downloads are processed", "True"),
        ("recnt", "bool", "Restart after reconnecting", "True"),
        ("rsLoad", "bool", "Restart on plugin activation", "False")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    event_map = {"pluginConfigChanged": "configEvents"}

    def resetCounters(self):
        self.info["dlfailed"] = 0
        if self.info["timerflag"]:
            self.setTimer(False, None)

    def restart(self):
        now = time.time()
        self.resetCounters()
        self.core.api.restartFailed()
        self.logDebug("called self.core.api.restartFailed()")
        self.info["lastrstime"] = now

    def setTimer(self, timerflag, interval):
        self.info["timerflag"] = timerflag
        if interval and interval != self.interval:
            self.interval = interval
        if timerflag:
            self.addEvent("periodical", self.restart)
        else:
            self.removeEvent("periodical", self.restart)

    def checkFailed_i(self):
        now = time.time()
        lastrstime = self.info["lastrstime"]
        interval = self.getConfig("dlFail_i") * 60
        timerflag = self.info["timerflag"]
        if now >= lastrstime + interval:
            self.restart()
        elif not timerflag:
            self.setTimer(True, interval)

    def checkFailed_n(self):
        curr = self.info["dlfailed"]
        max = self.getConfig("dlFail_n")
        if curr >= max:
            self.checkFailed_i()
        else:
            self.info["dlfailed"] = curr + 1

    def checkFailed(self, pyfile):
        status = pyfile.getStatusName()
        if status == "failed" or status == "aborted":
            self.checkFailed_n()

    def addEvent(self, event, handler):
        self.manager.addEvent(event, handler)
        return True

    def removeEvent(self, event, handler):
        if event in self.manager.events and handler in self.manager.events[event]:
            self.manager.events[event].remove(handler)
            return True
        else:
            return False

    def on_allDownloadsProcessed(self):
        self.restart()

    def on_downloadStart(self, pyfile):
        self.removeEvent("downloadStarts", self.on_downloadStart)
        self.addEvent("allDownloadsProcessed", self.on_allDownloadsProcessed)

    def on_allDownloadsFinished(self):
        self.removeEvent("allDownloadsProcessed", self.on_allDownloadsProcessed)
        self.addEvent("downloadStarts", self.on_downloadStart)

    def on_afterReconnecting(self, ip):
        self.restart()

    def configEvents(self, plugin, name, value):
        if self.getConfig("dlFail"):
            self.addEvent("downloadFinished", self.checkFailed)
        else:
            self.removeEvent("downloadFinished", self.checkFailed)
            self.resetCounters()
        if self.getConfig("dlPrcs"):
            self.addEvent("allDownloadsProcessed", self.on_allDownloadsProcessed)
            self.addEvent("allDownloadsFinished", self.on_allDownloadsFinished)
        else:
            if not self.removeEvent("allDownloadsProcessed", self.on_allDownloadsProcessed):
                self.removeEvent("downloadStarts", self.on_downloadStart)
            self.removeEvent("allDownloadsFinished", self.on_allDownloadsFinished)
        if self.getConfig("recnt"):
            self.addEvent("afterReconnecting", self.on_afterReconnecting)
        else:
            self.removeEvent("afterReconnecting", self.on_afterReconnecting)

    def setup(self):
        self.info = {"dlfailed": 0, "lastrstime": 0, "timerflag": False}
        if self.getConfig("rsLoad"):
            self.restart()
