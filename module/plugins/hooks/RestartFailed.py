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
    __version__ = "0.5"
    __description__ = "Restart failed packages according to defined rules"
    __config__ = [
        ("activated", "bool", "Activated", "True"),
        ("dlFailed", "bool", "Restart if downloads fails", "True"),
        ("dlFailed_n", "int", "Only when failed downloads are more than", "5"),
        ("dlFailed_i", "int", "Only when elapsed time since last restart is (min)", "10"),
        ("packFinished", "bool", "Restart when package finished", "True")
        ("recnt", "bool", "Restart after reconnected", "True")
    ]
    __author_name__ = ("vuolter")
    __author_mail__ = ("vuolter@gmail.com")

    failed = 0
    lastime = 0

    def checkInterval(self, interval):
        now = time()
        interval *= 60
        if now >= self.lastime + interval:
            self.lastime = now
            return True
        else:
            return False

    def downloadFailed(self, pyfile):
        if not self.getConfig("dlFailed"):
            self.failed = 0
            return
        number = self.getConfig("dlFailed_n")
        interval = self.getConfig("dlFailed_i")
        if self.failed > number and checkInterval(interval):
            self.core.api.restartFailed()
            self.logDebug("executed after " + self.failed + " failed downloads")
            self.failed = 0
        else:
            self.failed += 1

    def packageFinished(self, pypack):
        if not self.getConfig("packFinished"):
            return
        self.core.api.restartFailed()
        self.logDebug("executed after one package finished")

    def afterReconnecting(self, ip):
        if not self.getConfig("recnt"):
            return
        self.core.api.restartFailed()
        self.logDebug("executed after reconnecting")
