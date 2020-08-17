# -*- coding: utf-8 -*-

from ..base.notifier import Notifier


class AndroidPhoneNotify(Notifier):
    __name__ = "AndroidPhoneNotify"
    __type__ = "addon"
    __version__ = "0.16"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("apikey", "str", "API key", ""),
        ("captcha", "bool", "Notify captcha request", True),
        ("reconnection", "bool", "Notify reconnection request", False),
        ("downloadfinished", "bool", "Notify download finished", True),
        ("downloadfailed", "bool", "Notify download failed", True),
        ("packagefinished", "bool", "Notify package finished", True),
        ("packagefailed", "bool", "Notify package failed", True),
        ("update", "bool", "Notify pyLoad update", False),
        ("exit", "bool", "Notify pyLoad shutdown/restart", False),
        ("sendinterval", "int", "Interval in seconds between notifications", 1),
        ("sendpermin", "int", "Max notifications per minute", 60),
        ("ignoreclient", "bool", "Send notifications if client is connected", True),
    ]

    __description__ = (
        """Send push notifications to your Android Phone using notifymyandroid.com"""
    )
    __license__ = "GPLv3"
    __authors__ = [
        ("Steven Kosyra", "steven.kosyra@gmail.com"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    def get_key(self):
        return self.config.get("apikey")

    def send(self, event, msg, key):
        self.load(
            "http://www.notifymyandroid.com/publicapi/notify",
            get={
                "apikey": key,
                "application": "pyLoad",
                "event": event,
                "description": msg,
            },
        )
