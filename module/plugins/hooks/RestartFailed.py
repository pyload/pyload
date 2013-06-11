# -*- coding: utf-8 -*-

from module.plugins.Hook import Hook

class RestartFailed(Hook):
    __name__ = "RestartFailed"
    __version__ = "1.52"
    __description__ = "restartedFailed Packages after defined time"
    __config__ = [("activated", "bool", "Activated" , "False"),
                  ("interval", "int", "Interval in Minutes", "15") ]
 
    __author_name__ = ("bambie")
    __author_mail__ = ("bambie@gulli.com")

    interval = 300

    def setup(self):
        self.info = {"running": False}

    def coreReady(self):
        self.info["running"] = True
        self.logInfo("loaded")
        self.interval = self.getConfig("interval") * 60
        self.logDebug("interval is set to %s" % self.interval)

    def periodical(self):
        self.logDebug("periodical called")
        if self.getConfig("interval") * 60 != self.interval:
            self.interval = self.getConfig("interval") * 60
            self.logDebug("interval is set to %s" % self.interval)
        self.core.api.restartFailed()
