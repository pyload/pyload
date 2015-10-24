# -*- coding: utf-8 -*-

import httplib
import time

from module.plugins.internal.Notifier import Notifier


class WindowsPhoneNotify(Notifier):
    __name__    = "WindowsPhoneNotify"
    __type__    = "hook"
    __version__ = "0.15"
    __status__  = "testing"

    __config__ = [("activated"      , "bool", "Activated"                                , False),
                  ("push-id"        , "str" , "Push ID"                                  , ""   ),
                  ("push-url"       , "str" , "Push url"                                 , ""   ),
                  ("notifycaptcha"  , "bool", "Notify captcha request"                   , True ),
                  ("notifypackage"  , "bool", "Notify package finished"                  , True ),
                  ("notifyprocessed", "bool", "Notify packages processed"                , True ),
                  ("notifyupdate"   , "bool", "Notify plugin updates"                    , True ),
                  ("notifyexit"     , "bool", "Notify pyLoad shutdown"                   , True ),
                  ("sendtimewait"   , "int" , "Timewait in seconds between notifications", 5    ),
                  ("sendpermin"     , "int" , "Max notifications per minute"             , 12   ),
                  ("ignoreclient"   , "bool", "Send notifications if client is connected", False)]

    __description__ = """Send push notifications to Windows Phone"""
    __license__     = "GPLv3"
    __authors__     = [("Andy Voigt"    , "phone-support@hotmail.de"),
                       ("Walter Purcaro", "vuolter@gmail.com"       )]


    def get_key(self):
        return self.get_config('push-id'), self.get_config('push-url')


    def format_request(self, msg):
        return ("<?xml version='1.0' encoding='utf-8'?> <wp:Notification xmlns:wp='WPNotification'> "
                "<wp:Toast> <wp:Text1>pyLoad</wp:Text1> <wp:Text2>%s</wp:Text2> "
                "</wp:Toast> </wp:Notification>" % msg)


    def send(self, event, msg, key):
        id, url    = key
        request    = self.format_request("%s: %s" % (event, msg) if msg else event)
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
