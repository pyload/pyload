# -*- coding: utf-8 -*-
###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from module.plugins.Hook import Hook


class RestartFailed(Hook):
    __name__ = "RestartFailed"
    __version__ = "1.55"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", False),
                  ("interval", "int", "Check interval in minutes", 90)]

    __description__ = """Periodically restart all failed downloads in queue"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    MIN_INTERVAL = 15 * 60  #: 15m minimum check interval (value is in seconds)

    event_list = ["pluginConfigChanged"]


    def pluginConfigChanged(self, plugin, name, value):
        if name == "interval":
            interval = value * 60
            if self.MIN_INTERVAL <= interval != self.interval:
                self.core.scheduler.removeJob(self.cb)
                self.interval = interval
                self.initPeriodical()
            else:
                self.logDebug("Invalid interval value, kept current")

    def periodical(self):
        self.logInfo("Restart failed downloads")
        self.api.restartFailed()

    def setup(self):
        self.api = self.core.api
        self.interval = self.MIN_INTERVAL

    def coreReady(self):
        self.pluginConfigChanged(self.__name__, "interval", self.getConfig("interval"))
