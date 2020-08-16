# -*- coding: utf-8 -*-


from ..base.addon import BaseAddon


class RestartFailed(BaseAddon):
    __name__ = "RestartFailed"
    __type__ = "addon"
    __version__ = "1.65"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("interval", "int", "Check interval in minutes", 90),
    ]

    __description__ = """Restart all the failed downloads in queue"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def periodical_task(self):
        self.log_info(self._("Restarting all failed downloads..."))
        self.pyload.api.restart_failed()

    def activate(self):
        self.periodical.start(self.config.get("interval") * 60)
