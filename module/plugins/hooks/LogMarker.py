# -*- coding: utf-8 -*-

from module.plugins.internal.Addon import Addon, Expose


class LogMarker(Addon):
    __name__    = "LogMarker"
    __type__    = "hook"
    __version__ = "0.01"
    __status__  = "testing"

    __description__ = """Log a mark when the day begins"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def periodical(self):
        self.log_info("------------------------------------------------")
        self.log_info(_("--------------------- MARK ---------------------"))
        self.log_info("------------------------------------------------")