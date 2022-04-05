# -*- coding: utf-8 -*-

from ..base.notifier import Notifier


class PushOver(Notifier):
    __name__ = "PushOver"
    __type__ = "addon"
    __version__ = "0.08"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("tokenkey", "str", "Token key", ""),
        ("userkey", "str", "User key", ""),
        ("captcha", "bool", "Notify captcha request", True),
        ("reconnection", "bool", "Notify reconnection request", False),
        ("downloadfinished", "bool", "Notify download finished", True),
        ("downloadfailed", "bool", "Notify download failed", True),
        ("alldownloadsfinished", "bool", "Notify all downloads finished", True),
        ("alldownloadsprocessed", "bool", "Notify all downloads processed", True),
        ("packagefinished", "bool", "Notify package finished", True),
        ("packagefailed", "bool", "Notify package failed", True),
        ("update", "bool", "Notify pyLoad update", False),
        ("exit", "bool", "Notify pyLoad shutdown/restart", False),
        ("sendinterval", "int", "Interval in seconds between notifications", 1),
        ("sendpermin", "int", "Max notifications per minute", 60),
        ("ignoreclient", "bool", "Send notifications if client is connected", True),
    ]

    __description__ = """Send push notifications to your phone using pushover.net"""
    __license__ = "GPLv3"
    __authors__ = [("Malkavi", "")]

    def get_key(self):
        return self.config.get("tokenkey"), self.config.get("userkey")

    def send(self, event, msg, key):
        token, user = key
        self.load(
            "https://api.pushover.net/1/messages.json",
            post={
                "token": token,
                "user": user,
                "title": event,
                "message": msg or event,
            },
        )  # NOTE: msg can not be None or empty
