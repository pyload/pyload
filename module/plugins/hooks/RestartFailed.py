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

    @author: vuolter
"""

from module.plugins.Hook import Hook
import time


class RestartFailed(Hook):
    __name__ = "RestartFailed"
    __version__ = "0.7"
    __description__ = "Restart failed packages according to defined rules"
    __config__ = [
        ("activated", "bool", "Activated", "True"),
        ("dlFail", "bool", "Restart if download fail", "True"),
        ("dlFail_n", "int", "Only when failed downloads are at least", "5"),
        ("dlFail_i", "int", "Only when elapsed time since last restart is (min)", "10"),
        ("pkFinish", "bool", "Restart when a package is finished", "True")
        ("recnt", "bool", "Restart after reconnecting", "True")
    ]
    __author_name__ = ("vuolter")
    __author_mail__ = ("vuolter@gmail.com")

    event_map = {"pluginConfigChanged": "configEvents"}

    def restart(self):
        self.core.api.restartFailed()
        self.info["dlfailed"] = 0
        self.logDebug("called self.core.api.restartFailed()")

    def setTimer(self, timer):
        self.info["timer"] = timer
        if timer:
            self.manager.addEvent("periodical", doRestart)
        else:
            self.manager.removeEvent("periodical", doRestart)

    def doRestart(self):
        now = time()
        lastrstime = self.getInfo("lastrstime")
        interval = self.getConfig("dlFail_i") * 60
        timer = self.getInfo("timer")
        newtimer = 0
        value = False
        if now >= lastrstime + interval:
            self.restart()
            self.info["lastrstime"] = now
            value = True
        else:
            newtimer = 1
        if newtimer != timer:
            setTimer(newtimer)
        return value

    def checkFailed(self, pyfile):
        curr = self.getInfo("dlfailed")
        max = self.getConfig("dlFail_n")
        if curr >= max:
            doRestart()
        else:
            self.info["dlfailed"] = curr + 1

    def arrangeChecks(self):
        self.info["dlfailed"] = 1000
        if self.getInfo("timer"):
            setTimer(0)

    def configEvents(self):
        if self.getConfig("dlFail"):
            self.manager.addEvent("downloadFailed", checkFailed)
        else:
            self.manager.removeEvent("downloadFailed", checkFailed)
            self.arrangeChecks()
        if self.getConfig("pkFinish"):
            self.manager.addEvent("packageFinished", restart)
        else:
            self.manager.removeEvent("packageFinished", restart)
        if self.getConfig("recnt"):
            self.manager.addEvent("afterReconnecting", restart)
        else:
            self.manager.removeEvent("afterReconnecting", restart)

    def setup(self):
        self.info = {"dlfailed": 0, "lastrstime": 0, "timer": 0}
        self.configEvents()
