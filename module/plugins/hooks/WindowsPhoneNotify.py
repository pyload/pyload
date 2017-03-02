# -*- coding: utf-8 -*-


import httplib

from ..internal.Notifier import Notifier


class WindowsPhoneNotify(Notifier):
    __name__ = "WindowsPhoneNotify"
    __type__ = "hook"
    __version__ = "0.18"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
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
                  ("sendinterval", "int",
                   "Interval in seconds between notifications", 1),
                  ("sendpermin", "int", "Max notifications per minute", 60),
                  ("ignoreclient", "bool", "Send notifications if client is connected", True)]

    __description__ = """Send push notifications to Windows Phone"""
    __license__ = "GPLv3"
    __authors__ = [("Andy Voigt", "phone-support@hotmail.de"),
                   ("Walter Purcaro", "vuolter@gmail.com")]

    def get_key(self):
        return self.config.get('pushid'), self.config.get('pushurl')

    def format_request(self, msg):
        return ("<?xml version='1.0' encoding='utf-8'?> <wp:Notification xmlns:wp='WPNotification'> "
                "<wp:Toast> <wp:Text1>pyLoad</wp:Text1> <wp:Text2>%s</wp:Text2> "
                "</wp:Toast> </wp:Notification>" % msg)

    def send(self, event, msg, key):
        id, url = key
        request = self.format_request(
            "%s: %s" %
            (event, msg) if msg else event)
        webservice = httplib.HTTP(url)

        webservice.putrequest("POST", id)
        webservice.putheader("Host", url)
        webservice.putheader("Content-type", "text/xml")
        webservice.putheader("X-NotificationClass", "2")
        webservice.putheader("X-WindowsPhone-Target", "toast")
        webservice.putheader("Content-length", "%d" % len(request))
        webservice.endheaders()
        webservice.send(request)
        webservice.close()
