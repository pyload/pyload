# -*- coding: utf-8 -*-

import time

from module.plugins.internal.Notifier import Notifier


class PushOver(Notifier):
    __name__    = "PushOver"
    __type__    = "hook"
    __version__ = "0.04"
    __status__  = "testing"

    __config__ = [("activated"      , "bool", "Activated"                                , False),
                  ("tokenkey"       , "str" , "Token key"                                , ""   ),
                  ("userkey"        , "str" , "User key"                                 , ""   ),
                  ("notifycaptcha"  , "bool", "Notify captcha request"                   , True ),
                  ("notifypackage"  , "bool", "Notify package finished"                  , True ),
                  ("notifyprocessed", "bool", "Notify packages processed"                , True ),
                  ("notifyupdate"   , "bool", "Notify plugin updates"                    , True ),
                  ("notifyexit"     , "bool", "Notify pyLoad shutdown"                   , True ),
                  ("sendtimewait"   , "int" , "Timewait in seconds between notifications", 5    ),
                  ("sendpermin"     , "int" , "Max notifications per minute"             , 12   ),
                  ("ignoreclient"   , "bool", "Send notifications if client is connected", False)]

    __description__ = """Send push notifications to your phone using pushover.net"""
    __license__     = "GPLv3"
    __authors__     = [("Malkavi" , "")]


    def get_key(self):
        return self.get_config('tokenkey'), self.get_config('userkey')


    def send(self, event, msg, key):
        token, user = key
        self.load("https://api.pushover.net/1/messages.json",
                  post={'token'	 : token,
                        'user'   : user,
                        'title'  : event,
                        'message': msg or event})  #@NOTE: msg can not be None or empty
