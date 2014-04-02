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


class RestartFailed(Hook):
    __name__ = "RestartFailed"
    __version__ = "1.53"
    __description__ = """Periodically restart all failed downloads in queue"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("interval", "int", "Interval in minutes", 90)]
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    event_list = ["pluginConfigChanged"]

    MIN_INTERVAL = 15 * 60 #seconds

    def periodical(self):
        self.logDebug("Restart all failed downloads now")
        self.core.api.restartFailed()

    def restartPeriodical(self, interval):
        self.logDebug("Set periodical interval to %s seconds" % interval)
        if self.cb:
            self.core.scheduler.removeJob(self.cb)
        self.interval = interval
        self.cb = self.core.scheduler.addJob(interval, self._periodical, threaded=False)

    def pluginConfigChanged(self, plugin, name, value):
        value *= 60
        if name == "interval":
            if self.interval != value > self.MIN_INTERVAL:
                self.restartPeriodical(value)
            else:
                self.logWarning("Cannot change interval: given value is equal to the current or \
                                 smaller than %s seconds" % self.MIN_INTERVAL)

    def coreReady(self):
        self.pluginConfigChanged(plugin="RestartFailed", name="interval", value=self.getConfig("interval"))
