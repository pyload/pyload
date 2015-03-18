# -*- coding: utf-8 -*-

import httplib
import time

from module.plugins.Hook import Hook, Expose


class WindowsPhoneNotify(Hook):
    __name__    = "WindowsPhoneNotify"
    __type__    = "hook"
    __version__ = "0.09"

    __config__ = [("id"             , "str" , "Push ID"                                  , ""   ),
                  ("url"            , "str" , "Push url"                                 , ""   ),
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


    def getXmlData(self, msg):
        return ("<?xml version='1.0' encoding='utf-8'?> <wp:Notification xmlns:wp='WPNotification'> "
                "<wp:Toast> <wp:Text1>pyLoad</wp:Text1> <wp:Text2>%s</wp:Text2> "
                "</wp:Toast> </wp:Notification>" % msg)


    @Expose
    def notify(self,
               event,
               msg="",
               key=(self.getConfig('id'), self.getConfig('url'))):

        id, url = key

        if not id or not url:
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

        self.last_notify    = time.time()
        self.notifications += 1
