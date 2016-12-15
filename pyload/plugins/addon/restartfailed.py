# -*- coding: utf-8 -*-
#@author: Walter Purcaro

from __future__ import unicode_literals

from pyload.plugins.hook import Hook


class RestartFailed(Hook):
    __name__ = "RestartFailed"
    __version__ = "1.53"
    __description__ = """Periodically restart all failed downloads in queue"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("interval", "int", "Interval in minutes", 90)]
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    event_list = ["pluginConfigChanged"]

    MIN_INTERVAL = 15 * 60  # seconds

    def periodical(self):
        self.logDebug("Restart all failed downloads now")
        self.pyload.api.restartFailed()

    def restartPeriodical(self, interval):
        self.logDebug("Set periodical interval to %s seconds" % interval)
        if self.cb:
            self.pyload.scheduler.removeJob(self.cb)
        self.interval = interval
        self.cb = self.pyload.scheduler.addJob(interval, self._periodical, threaded=False)

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
