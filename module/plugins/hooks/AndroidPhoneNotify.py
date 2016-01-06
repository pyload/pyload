# -*- coding: utf-8 -*-

from module.plugins.internal.Notifier import Notifier


class AndroidPhoneNotify(Notifier):
    __name__    = "AndroidPhoneNotify"
    __type__    = "hook"
    __version__ = "0.13"
    __status__  = "testing"

    __config__ = [("activated"      , "bool", "Activated"                                , False),
                  ("apikey"         , "str" , "API key"                                  , ""   ),
                  ("notifycaptcha"  , "bool", "Notify captcha request"                   , True ),
                  ("notifypackage"  , "bool", "Notify package finished"                  , True ),
                  ("notifyprocessed", "bool", "Notify packages processed"                , True ),
                  ("notifyupdate"   , "bool", "Notify plugin updates"                    , True ),
                  ("notifyexit"     , "bool", "Notify pyLoad shutdown"                   , True ),
                  ("sendtimewait"   , "int" , "Timewait in seconds between notifications", 5    ),
                  ("sendpermin"     , "int" , "Max notifications per minute"             , 12   ),
                  ("ignoreclient"   , "bool", "Send notifications if client is connected", False)]

    __description__ = """Send push notifications to your Android Phone using notifymyandroid.com"""
    __license__     = "GPLv3"
    __authors__     = [("Steven Kosyra" , "steven.kosyra@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com"      )]


    def get_key(self):
        return self.get_config('apikey')


    def send(self, event, msg, key):
        self.load("http://www.notifymyandroid.com/publicapi/notify",
                  get={'apikey'     : key,
                       'application': "pyLoad",
                       'event'      : event,
                       'description': msg})
