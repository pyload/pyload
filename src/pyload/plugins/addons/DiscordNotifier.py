# -*- coding: utf-8 -*-

from pyload.core.network.request_factory import get_request

from ..base.notifier import Notifier


class DiscordNotifier(Notifier):
    __name__ = "DiscordNotifier"
    __type__ = "addon"
    __version__ = "0.1"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("webhookurl", "string", "The URL of the webhook", ""),
        ("captcha", "bool", "Notify captcha request", True),
        ("reconnection", "bool", "Notify reconnection request", True),
        ("downloadfinished", "bool", "Notify download finished", True),
        ("downloadfailed", "bool", "Notify download failed", True),
        ("packagefinished", "bool", "Notify package finished", True),
        ("packagefailed", "bool", "Notify package failed", True),
        ("update", "bool", "Notify pyload update", False),
        ("exit", "bool", "Notify pyload shutdown/restart", False),
        ("sendinterval", "int", "Interval in seconds between notifications", 1),
        ("sendpermin", "int", "Max notifications per minute", 60),
        ("ignoreclient", "bool", "Send notifications if client is connected", True),
    ]

    __description__ = "Send push notifications to a Discord channel via a webhook."
    __license__ = "GPLv3"
    __authors__ = [("Jan-Olaf Becker", "job87@web.de")]

    def get_key(self):
        return self.config.get("webhookurl")

    def send(self, event, msg, key):
        req = get_request()
        self.log_info("Sending message to discord")
        self.load(self.get_key(), post={"content": event + "\n" + msg}, req=req)
