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

from module.database import style
from module.plugins.Hook import Hook


class DeleteFinished(Hook):
    __name__ = "DeleteFinished"
    __version__ = "1.07"
    __description__ = "Automatically delete all finished packages from queue"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("interval", "int", "Delete every (hours)", "72"),
        ("incoff", "bool", "Delete packages with offline links", "False")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    ## overwritten methods ##
    def periodical(self):
        if not self.info["sleep"]:
            incoff = self.getConfig("incoff")
            mode = "0,1,4" if incoff else "0,4"
            msg = "delete all finished packages now (%s any package with offline links)"
            self.logInfo(msg % "including" if incoff else "excluding")
            self.deleteFinished(mode)
            self.info["sleep"] = True
            self.addEvent("packageFinished", self.wakeup)

    def pluginConfigChanged(self, plugin, name, value):
        if name == "interval" and value != self.interval:
            self.interval = value
            self.initPeriodical()

    def unload(self):
        self.removeEvent("packageFinished", self.wakeup)

    def coreReady(self):
        self.info = {"sleep": True}
        interval = self.getConfig("interval") * 3600
        self.pluginConfigChanged("DeleteFinished", "interval", interval)
        self.addEvent("packageFinished", self.wakeup)

    ## own methods ##
    @style.queue
    def deleteFinished(self, mode):
        self.c.execute("DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE package=packages.id AND status NOT IN (%s))" % mode)
        self.c.execute("DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id=links.package)")

    def wakeup(self, pypack):
        self.removeEvent("packageFinished", self.wakeup)
        self.info["sleep"] = False

    ## event managing ##
    def addEvent(self, event, func):
        """Adds an event listener for event name"""
        if event in self.events:
            if func in self.events[event]:
                self.logDebug("Function already registered %s" % func)
            else:
                self.events[event].append(func)
        else:
            self.events[event] = [func]

    def setup(self):
        self.removeEvent = self.manager.removeEvent
