# -*- coding: utf-8 -*-

from pyload.plugin.Addon import Addon


class RestartFailed(Addon):
    __name    = "RestartFailed"
    __type    = "addon"
    __version = "1.58"

    __config = [("activated", "bool", "Activated"                , True),
                ("interval" , "int" , "Check interval in minutes", 90  )]

    __description = """Restart all the failed downloads in queue"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


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


    def activate(self):
        # self.pluginConfigChanged(self.__class__.__name__, "interval", self.getConfig('interval'))
        self.interval = max(self.MIN_CHECK_INTERVAL, self.getConfig('interval') * 60)
        self.initPeriodical()
