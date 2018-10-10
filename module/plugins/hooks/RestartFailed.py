# -*- coding: utf-8 -*-

from ..internal.Addon import Addon


class RestartFailed(Addon):
    __name__ = "RestartFailed"
    __type__ = "hook"
    __version__ = "1.65"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("interval", "int", "Check interval in minutes", 90)]

    __description__ = """Restart all the failed downloads in queue"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def periodical_task(self):
        self.log_info(_("Restarting all failed downloads..."))
        self.pyload.api.restartFailed()

    def activate(self):
        self.periodical.start(self.config.get('interval') * 60)
