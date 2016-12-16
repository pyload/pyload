# -*- coding: utf-8 -*-
#@author: RaNaN, Godofdream, zoidberg

from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
import time
import http.client
from pyload.plugins.hook import Hook


class WindowsPhoneToastNotify(Hook):
    __name__ = "WindowsPhoneToastNotify"
    __version__ = "0.02"
    __description__ = """Send push notifications to Windows Phone"""
    __author_name__ = "Andy Voigt"
    __author_mail__ = "phone-support@hotmail.de"
    __config__ = [("activated", "bool", "Activated", False),
                  ("force", "bool", "Force even if client is connected", False),
                  ("pushId", "str", "pushId", ""),
                  ("pushUrl", "str", "pushUrl", ""),
                  ("pushTimeout", "int", "Timeout between notifications in seconds", 0)]

    def setup(self):
        self.info = {}

    def get_xml_data(self):
        myxml = ("<?xml version='1.0' encoding='utf-8'?> <wp:Notification xmlns:wp='WPNotification'> "
                 "<wp:Toast> <wp:Text1>Pyload Mobile</wp:Text1> <wp:Text2>Captcha waiting!</wp:Text2> "
                 "</wp:Toast> </wp:Notification>")
        return myxml

    def do_request(self):
        URL = self.getConfig("pushUrl")
        request = self.getXmlData()
        webservice = http.client.HTTP(URL)
        webservice.putrequest("POST", self.getConfig("pushId"))
        webservice.putheader("Host", URL)
        webservice.putheader("Content-type", "text/xml")
        webservice.putheader("X-NotificationClass", "2")
        webservice.putheader("X-WindowsPhone-Target", "toast")
        webservice.putheader("Content-length", "%d" % len(request))
        webservice.endheaders()
        webservice.send(request)
        webservice.close()
        self.setStorage("LAST_NOTIFY", time.time())

    def new_captcha_task(self, task):
        if not self.getConfig("pushId") or not self.getConfig("pushUrl"):
            return False

        if self.pyload.isClientConnected() and not self.getConfig("force"):
            return False

        if (time.time() - float(self.getStorage("LAST_NOTIFY", 0))) < self.getConf("pushTimeout"):
            return False

        self.doRequest()
