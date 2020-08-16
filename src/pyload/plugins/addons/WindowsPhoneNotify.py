# -*- coding: utf-8 -*-

import http.client
from contextlib import closing

from ..base.notifier import Notifier


class WindowsPhoneNotify(Notifier):
    __name__ = "WindowsPhoneNotify"
    __type__ = "addon"
    __version__ = "0.18"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("pushid", "str", "Push ID", ""),
        ("pushurl", "str", "Push url", ""),
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

    __description__ = """Send push notifications to Windows Phone"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Andy Voigt", "phone-support@hotmail.de"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    def get_key(self):
        return self.config.get("pushid"), self.config.get("pushurl")

    def format_request(self, msg):
        return (
            "<?xml version='1.0' encoding='utf-8'?> <wp:Notification xmlns:wp='WPNotification'> "
            "<wp:Toast> <wp:Text1>pyLoad</wp:Text1> <wp:Text2>{}</wp:Text2> "
            "</wp:Toast> </wp:Notification>".format(msg)
        )

    def send(self, event, msg, key):
        id, url = key
        request = self.format_request("{}: {}".format(event, msg) if msg else event)
        with closing(http.client.HTTPConnection(url)) as webservice:
            webservice.putrequest("POST", id)
            webservice.putheader("Host", url)
            webservice.putheader("Content-type", "text/xml")
            webservice.putheader("X-NotificationClass", "2")
            webservice.putheader("X-WindowsPhone-Target", "toast")
            webservice.putheader("Content-length", "{}".format(len(request)))
            webservice.endheaders()
            webservice.send(request)
