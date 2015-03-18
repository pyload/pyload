# -*- coding: utf-8 -*-

import time

from module.network.RequestFactory import getURL
from module.plugins.Hook import Hook, Expose


class AndroidPhoneNotify(Hook):
    __name__    = "AndroidPhoneNotify"
    __type__    = "hook"
    __version__ = "0.07"

    __config__ = [("apikey"         , "str" , "API key"                                  , ""   ),
                  ("notifycaptcha"  , "bool", "Notify captcha request"                   , True ),
                  ("notifypackage"  , "bool", "Notify package finished"                  , True ),
                  ("notifyprocessed", "bool", "Notify packages processed"                , True ),
                  ("notifyupdate"   , "bool", "Notify plugin updates"                    , True ),
                  ("notifyexit"     , "bool", "Notify pyLoad shutdown"                   , True ),
                  ("sendtimewait"   , "int" , "Timewait in seconds between notifications", 5    ),
                  ("sendpermin"     , "int" , "Max notifications per minute"             , 12   ),
                  ("ignoreclient"   , "bool", "Send notifications if client is connected", False)]

    __description__ = """Send push notifications to your Android Phone (using notifymyandroid.com)"""
    __license__     = "GPLv3"
    __authors__     = [("Steven Kosyra" , "steven.kosyra@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com"      )]


    event_list = ["allDownloadsProcessed", "plugin_updated"]


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def setup(self):
        self.info          = {}  #@TODO: Remove in 0.4.10
        self.last_notify   = 0
        self.notifications = 0


    def plugin_updated(self, type_plugins):
        if not self.getConfig('notifyupdate'):
            return

        self.notify(_("Plugins updated"), str(type_plugins))


    def coreExiting(self):
        if not self.getConfig('notifyexit'):
            return

        if self.core.do_restart:
            self.notify(_("Restarting pyLoad"))
        else:
            self.notify(_("Exiting pyLoad"))


    def newCaptchaTask(self, task):
        if not self.getConfig('notifycaptcha'):
            return

        self.notify(_("Captcha"), _("New request waiting user input"))


    def packageFinished(self, pypack):
        if self.getConfig('notifypackage'):
            self.notify(_("Package finished"), pypack.name)


    def allDownloadsProcessed(self):
        if not self.getConfig('notifyprocessed'):
            return

        if any(True for pdata in self.core.api.getQueue() if pdata.linksdone < pdata.linkstotal):
            self.notify(_("Package failed"), _("One or more packages was not completed successfully"))
        else:
            self.notify(_("All packages finished"))


    @Expose
    def notify(self,
               event,
               msg="",
               key=self.getConfig('apikey')):

        if not key:
            return

        if self.core.isClientConnected() and not self.getConfig('ignoreclient'):
            return

        elapsed_time = time.time() - self.last_notify

        if elapsed_time < self.getConf("sendtimewait"):
            return

        if elapsed_time > 60:
            self.notifications = 0

        elif self.notifications >= self.getConf("sendpermin"):
            return


        getURL("http://www.notifymyandroid.com/publicapi/notify",
               get={'apikey'     : key,
                    'application': "pyLoad",
                    'event'      : event,
                    'description': msg})

        self.last_notify    = time.time()
        self.notifications += 1
