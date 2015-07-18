# -*- coding: utf-8 -*-

from module.plugins.internal.Hook import Hook


class RestartFailed(Hook):
    __name__    = "RestartFailed"
    __type__    = "hook"
    __version__ = "1.60"

    __config__ = [("interval", "int", "Check interval in minutes", 90)]

    __description__ = """Restart all the failed downloads in queue"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    MIN_CHECK_INTERVAL = 15 * 60  #: 15 minutes


    # def plugin_config_changed(self, plugin, name, value):
        # if name == "interval":
            # interval = value * 60
            # if self.MIN_CHECK_INTERVAL <= interval != self.interval:
                # self.core.scheduler.removeJob(self.cb)
                # self.interval = interval
                # self.init_periodical()
            # else:
                # self.log_debug("Invalid interval value, kept current")


    def periodical(self):
        self.log_debug("Restart failed downloads")
        self.core.api.restartFailed()


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10
        # self.event_map = {'pluginConfigChanged': "plugin_config_changed"}
        self.interval = self.MIN_CHECK_INTERVAL


    def activate(self):
        # self.plugin_config_changed(self.__name__, "interval", self.get_config('interval'))
        self.interval = max(self.MIN_CHECK_INTERVAL, self.get_config('interval') * 60)
