# -*- coding: utf-8 -*-

from module.plugins.internal.Addon import Addon


class RestartFailed(Addon):
    __name__    = "RestartFailed"
    __type__    = "hook"
    __version__ = "1.60"
    __status__  = "testing"

    __config__ = [("interval", "int", "Check interval in minutes", 90)]

    __description__ = """Restart all the failed downloads in queue"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    MIN_CHECK_INTERVAL = 15 * 60  #: 15 minutes


    # def plugin_config_changed(self, plugin, name, value):
        # if name == "interval":
            # interval = value * 60
            # if self.MIN_CHECK_INTERVAL <= interval is not self.interval:
                # self.pyload.scheduler.removeJob(self.cb)
                # self.interval = interval
                # self.init_periodical()
            # else:
                # self.log_debug("Invalid interval value, kept current")


    def periodical(self):
        self.log_debug("Restart failed downloads")
        self.pyload.api.restartFailed()


    def init(self):
        # self.event_map = {'pluginConfigChanged': "plugin_config_changed"}
        self.interval = self.MIN_CHECK_INTERVAL


    def activate(self):
        # self.plugin_config_changed(self.__name__, "interval", self.get_config('interval'))
        self.interval = max(self.MIN_CHECK_INTERVAL, self.get_config('interval') * 60)
