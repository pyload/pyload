# -*- coding: utf-8 -*-

import datetime

from module.plugins.internal.Addon import Addon, Expose
from module.plugins.internal.Plugin import seconds_to_nexthour


class LogMarker(Addon):
    __name__    = "LogMarker"
    __type__    = "hook"
    __version__ = "0.03"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated" , False),
                  ("mark_hour", "bool", "Mark hours", True ),
                  ("mark_day" , "bool", "Mark days" , True )]

    __description__ = """Print a mark in the log"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def activated(self):
        self.start_periodical(1 * 60 * 60 - 1, delay=seconds_to_nexthour(strict=True) - 1)


    def periodical(self):
        if self.get_config('mark_day') and datetime.datetime.today().hour is 0:
            self.log_info("------------------------------------------------")
            self.log_info(_("------------------- DAY MARK -------------------"))
            self.log_info("------------------------------------------------")

        elif self.get_config('mark_hour'):
            self.log_info("------------------------------------------------")
            self.log_info(_("------------------- HOUR MARK ------------------"))
            self.log_info("------------------------------------------------")
