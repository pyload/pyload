# -*- coding: utf-8 -*-


import pycurl
from pyload.core.network.request_factory import get_request

from ..base.notifier import Notifier


class PushBullet(Notifier):
    __name__ = "PushBullet"
    __type__ = "addon"
    __version__ = "0.05"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("tokenkey", "str", "Access Token", ""),
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

    __description__ = """Send push notifications to your phone using pushbullet.com"""
    __license__ = "GPLv3"
    __authors__ = [("Malkavi", "")]

    def get_key(self):
        return self.config.get("tokenkey")

    def send(self, event, msg, key):
        req = get_request()
        req.c.setopt(pycurl.HTTPHEADER, ["Access-Token: {}".format(str(key))])

        self.load(
            "https://api.pushbullet.com/v2/pushes",
            post={"type": "note", "title": event, "message": msg},
            req=req,
        )
