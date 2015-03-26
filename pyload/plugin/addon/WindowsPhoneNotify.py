# -*- coding: utf-8 -*-

import httplib

from time import time

from pyload.plugin.Addon import Addon


class WindowsPhoneNotify(Addon):
    __name__    = "WindowsPhoneNotify"
    __type__    = "addon"
    __version__ = "0.07"

    __config__ = [("id"             , "str" , "Push ID"                                  , ""   ),
                  ("url"            , "str" , "Push url"                                 , ""   ),
                  ("notifycaptcha"  , "bool", "Notify captcha request"                   , True ),
                  ("notifypackage"  , "bool", "Notify package finished"                  , True ),
                  ("notifyprocessed", "bool", "Notify processed packages status"         , True ),
                  ("timeout"        , "int" , "Timeout between captchas in seconds"      , 5    ),
                  ("force"          , "bool", "Send notifications if client is connected", False)]

    __description__ = """Send push notifications to Windows Phone"""
    __license__     = "GPLv3"
    __authors__     = [("Andy Voigt", "phone-support@hotmail.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["allDownloadsProcessed"]


    def setup(self):
        self.info        = {}  #@TODO: Remove in 0.4.10
        self.last_notify = 0


    def newCaptchaTask(self, task):
        if not self.getConfig("notifycaptcha"):
            return False

        if time() - self.last_notify < self.getConf("timeout"):
            return False

        self.notify(_("Captcha"), _("New request waiting user input"))


    def packageFinished(self, pypack):
        if self.getConfig("notifypackage"):
            self.notify(_("Package finished"), pypack.name)


    def allDownloadsProcessed(self):
        if not self.getConfig("notifyprocessed"):
            return False

        if any(True for pdata in self.core.api.getQueue() if pdata.linksdone < pdata.linkstotal):
            self.notify(_("Package failed"), _("One or more packages was not completed successfully"))
        else:
            self.notify(_("All packages finished"))


    def getXmlData(self, msg):
        return ("<?xml version='1.0' encoding='utf-8'?> <wp:Notification xmlns:wp='WPNotification'> "
                "<wp:Toast> <wp:Text1>pyLoad</wp:Text1> <wp:Text2>%s</wp:Text2> "
                "</wp:Toast> </wp:Notification>" % msg)


    def notify(self, event, msg=""):
        id  = self.getConfig("id")
        url = self.getConfig("url")

        if not id or not url:
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        request    = self.getXmlData("%s: %s" % (event, msg) if msg else event)
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

        self.last_notify = time()
