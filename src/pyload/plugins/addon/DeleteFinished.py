# -*- coding: utf-8 -*-
from builtins import _

from pyload.database.database_backend import style
from pyload.plugins.internal.addon import Addon


class DeleteFinished(Addon):
    __name__ = "DeleteFinished"
    __type__ = "addon"
    __version__ = "1.19"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __config__ = [
        ("activated", "bool", "Activated", False),
        ("interval", "int", "Check interval in hours", 72),
        ("deloffline", "bool", "Delete package with offline links", False),
    ]

    __description__ = """Automatically delete all finished packages from queue"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def periodical_task(self):
        if not self.info["sleep"]:
            deloffline = self.config.get("deloffline")
            mode = "0,1,4" if deloffline else "0,4"
            msg = _(
                "delete all finished packages in queue list ({} packages with offline links)"
            )
            self.log_info(msg % (_("including") if deloffline else _("excluding")))
            self.delete_finished(mode)
            self.info["sleep"] = True
            self.add_event("package_finished", self.wakeup)

    def deactivate(self):
        self.m.removeEvent("package_finished", self.wakeup)

    def activate(self):
        self.info["sleep"] = True
        self.add_event("package_finished", self.wakeup)
        self.periodical.start(self.config.get("interval") * 60 * 60)

    ## own methods ##
    @style.queue
    def delete_finished(self, mode):
        self.c.execute(
            "DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE package=packages.id AND status NOT IN ({}))"
            % mode
        )
        self.c.execute(
            "DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id=links.package)"
        )

    def wakeup(self, pypack):
        self.m.removeEvent("package_finished", self.wakeup)
        self.info["sleep"] = False

    ## event managing ##
    def add_event(self, event, func):
        """
        Adds an event listener for event name.
        """
        if event in self.m.events:
            if func in self.m.events[event]:
                self.log_debug("Function already registered", func)
            else:
                self.m.events[event].append(func)
        else:
            self.m.events[event] = [func]
