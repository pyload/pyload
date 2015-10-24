# -*- coding: utf-8 -*-

import pycurl

from module.network.RequestFactory import getRequest as get_request
from module.plugins.internal.Notifier import Notifier


class PushBullet(Notifier):
    __name__    = "PushBullet"
    __type__    = "hook"
    __version__ = "0.02"
    __status__  = "testing"

    __config__ = [("activated"      , "bool", "Activated"                                , False),
                  ("tokenkey"       , "str" , "Access Token"                             , ""   ),
                  ("notifycaptcha"  , "bool", "Notify captcha request"                   , True ),
                  ("notifypackage"  , "bool", "Notify package finished"                  , True ),
                  ("notifyprocessed", "bool", "Notify packages processed"                , True ),
                  ("notifyupdate"   , "bool", "Notify plugin updates"                    , True ),
                  ("notifyexit"     , "bool", "Notify pyLoad shutdown"                   , True ),
                  ("sendtimewait"   , "int" , "Timewait in seconds between notifications", 5    ),
                  ("sendpermin"     , "int" , "Max notifications per minute"             , 12   ),
                  ("ignoreclient"   , "bool", "Send notifications if client is connected", False)]

    __description__ = """Send push notifications to your phone using pushbullet.com"""
    __license__     = "GPLv3"
    __authors__     = [("Malkavi" , "")]


    def get_key(self):
        return self.get_config('tokenkey')


    def send(self, event, msg, key):
        req = get_request()
        req.c.setopt(pycurl.HTTPHEADER, ["Access-Token: %s" % str(key)])

        self.load("https://api.pushbullet.com/v2/pushes",
                  post={'type'   : 'note',
                        'title'  : event,
                        'message': msg},
                  req=req)
