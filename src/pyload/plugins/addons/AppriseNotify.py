# -*- coding: utf-8 -*-

from ..base.notifier import Notifier
from ..helpers import check_module


class AppriseNotify(Notifier):
    __name__ = "AppriseNotify"
    __type__ = "addon"
    __version__ = "0.02"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("configs", "string", "Configuration(s) path/URL (comma separated)", ""),
        ("title", "string", "Notification title", "pyLoad Notification"),
        ("captcha", "bool", "Notify captcha request", True),
        ("reconnection", "bool", "Notify reconnection request", True),
        ("downloadfinished", "bool", "Notify download finished", True),
        ("downloadfailed", "bool", "Notify download failed", True),
        ("alldownloadsfinished", "bool", "Notify all downloads finished", True),
        ("alldownloadsprocessed", "bool", "Notify all downloads processed", True),
        ("packagefinished", "bool", "Notify package finished", True),
        ("packagefailed", "bool", "Notify package failed", True),
        ("update", "bool", "Notify pyload update", False),
        ("exit", "bool", "Notify pyload shutdown/restart", False),
        ("sendinterval", "int", "Interval in seconds between notifications", 1),
        ("sendpermin", "int", "Max notifications per minute", 60),
        ("ignoreclient", "bool", "Send notifications if client is connected", True),
    ]

    __description__ = "Send push notifications to apprise."
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def get_key(self):
        return self.config.get("configs").split(",")

    def send(self, event, msg, key):
        if not check_module("apprise"):
            self.log_error(
                self._("Cannot send notification: apprise is not installed."),
                self._("Install apprise by issuing 'pip install apprise' command."),
            )
            return

        import apprise

        apprise_obj = apprise.Apprise()
        apprise_config = apprise.AppriseConfig()

        for c in key:
            apprise_config.add(c)

        apprise_obj.add(apprise_config)

        apprise_obj.notify(
            title=self.config.get("title"),
            body="%s: %s" % (event, msg) if msg else event,
        )
