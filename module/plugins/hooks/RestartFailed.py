# -*- coding: utf-8 -*-

from module.plugins.Hook import Hook


class RestartFailed(Hook):
    __name__    = "RestartFailed"
    __type__    = "hook"
    __version__ = "1.58"

    __config__ = [("interval", "int", "Check interval in minutes", 90)]

    __description__ = """Restart all the failed downloads in queue"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    # event_list = ["pluginConfigChanged"]

    MIN_CHECK_INTERVAL = 15 * 60  #: 15 minutes


    # def pluginConfigChanged(self, plugin, name, value):
        # if name == "interval":
            # interval = value * 60
            # if self.MIN_CHECK_INTERVAL <= interval != self.interval:
                # self.core.scheduler.removeJob(self.cb)
                # self.interval = interval
                # self.initPeriodical()
            # else:
                # self.logDebug("Invalid interval value, kept current")


    def periodical(self):
        self.logDebug(_("Restart failed downloads"))
        self.core.api.restartFailed()


    def setup(self):
        self.info     = {}  #@TODO: Remove in 0.4.10
        self.interval = self.MIN_CHECK_INTERVAL


    def coreReady(self):
        # self.pluginConfigChanged(self.__name__, "interval", self.getConfig('interval'))
        self.interval = max(self.MIN_CHECK_INTERVAL, self.getConfig('interval') * 60)
