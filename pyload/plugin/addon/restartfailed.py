# -*- coding: utf-8 -*-
#@author: Walter Purcaro

from __future__ import unicode_literals

from pyload.plugin.hook import Hook


class RestartFailed(Hook):
    __name__ = "RestartFailed"
    __version__ = "1.53"
    __description__ = """Periodically restart all failed downloads in queue"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("interval", "int", "Interval in minutes", 90)]
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    event_list = ["plugin_config_changed"]

    MIN_INTERVAL = 15 * 60  # seconds

    def periodical(self):
        self.log_debug("Restart all failed downloads now")
        self.pyload.api.restart_failed()

    def restart_periodical(self, interval):
        self.log_debug("Set periodical interval to %s seconds" % interval)
        if self.cb:
            self.pyload.scheduler.remove_job(self.cb)
        self.interval = interval
        self.cb = self.pyload.scheduler.add_job(interval, self._periodical, threaded=False)

    def plugin_config_changed(self, plugin, name, value):
        value *= 60
        if name == "interval":
            if self.interval != value > self.MIN_INTERVAL:
                self.restartPeriodical(value)
            else:
                self.log_warning("Cannot change interval: given value is equal to the current or \
                                 smaller than %s seconds" % self.MIN_INTERVAL)

    def core_ready(self):
        self.plugin_config_changed(plugin="RestartFailed", name="interval", value=self.get_config("interval"))
