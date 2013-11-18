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
    __version__ = "1.50"
    __description__ = "Automatically delete finished packages from queue"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("mode", "instant;periodical", "Delete mode", "periodical"),
                  ("wait_time", "int", "Interval in hours", "72"),
                  ("del_offline", "bool", "Delete package with offline links", "False"),
                  ("del_password", "bool", "Delete package with password", "False"),
                  ("del_error", "bool", "Delete package with error", "True"),
                  ("keep_latest", "int", "Number of latest packages to keep ever", "0")]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    event_list = ["pluginConfigChanged"]

    MIN_INTERVAL = 3600  #: seconds

    ### Overwritten methods ###
    def initPeriodical(self):
        pass

    def setup(self):
        self._packageFinished = self.packageFinished

    def coreReady(self):
        config_name = "mode"
        self.pluginConfigChanged(plugin=self.__name__, name=config_name, value=self.getConfig(config_name))

    def pluginConfigChanged(self, plugin, name, value):
        if name == "mode":
            if value == "instant":
                self.stopTimer()
                self.packageFinished = self.deleteFinished
            else:
                self.wakeup()
        elif name == "wait_time" and self.cb:
            self.restartTimer()

    ### Own methods ###
    ### Schedule ###
    def schedule(self):
        self.logDebug("Do schedule and go to sleep mode")
        self.deleteFinished()
        self.packageFinished = self.wakeup
        self.cb = None

    def startTimer(self):
        wait = max(self.getConfig("wait_time") * 60 * 60, self.MIN_INTERVAL)
        self.logDebug("Start timer countdown: %s seconds" % wait)
        self.cb = self.core.scheduler.addJob(wait, self.deleteFinished, threaded=False)

    def stopTimer(self):
        if not self.cb:
            return
        self.core.scheduler.removeJob(self.cb)
        self.cb = None

    def restartTimer(self):
        self.stopTimer()
        self.startTimer()

    def wakeup(self, arg1=None):
        self.packageFinished = self._packageFinished
        self.startTimer()

    ### Tasks ###
    @style.queue
    def delete(self, password="", packageorder="", status="", error=""):
        self.c.execute("DELETE FROM packages WHERE queue %(password)s %(packageorder)s AND NOT EXISTS(SELECT 1 FROM links WHERE package = packages.id AND status NOT IN (%(status)s)) %(error)s" %
                      {"password": password, "packageorder": packageorder, "status": status, "error": error})
        self.c.execute("DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id = links.package)")

    def deleteFinished(self, arg1=None):
        del_offline = self.getConfig("del_offline")
        del_password = self.getConfig("del_password")
        del_error = self.getConfig("del_error")
        keep_latest = max(self.getConfig("keep_latest"), 0)

        c_password = "AND NOT password" if not del_password else ""
        c_packageorder = "AND packageorder < %s" % len(self.core.api.getQueue()) - keep_latest if keep_latest else ""
        c_statuscode = "0,4" if not del_offline else "0,1,4"
        c_error = "OR error" if not del_error else ""

        self.logInfo("Delete packages from queue now")
        self.delete(password=c_password, packageorder=c_packageorder, status=c_statuscode, error=c_error)
