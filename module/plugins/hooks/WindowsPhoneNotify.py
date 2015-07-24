# -*- coding: utf-8 -*-

import httplib
import time

from module.plugins.internal.Addon import Addon, Expose


class WindowsPhoneNotify(Addon):
    __name__    = "WindowsPhoneNotify"
    __type__    = "hook"
    __version__ = "0.12"
    __status__  = "testing"

    __config__ = [("push-id"        , "str" , "Push ID"                                  , ""   ),
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


    def init(self):
        self.event_list = ["plugin_updated"]
        self.event_map  = {'allDownloadsProcessed': "all_downloads_processed"}

        self.last_notify   = 0
        self.notifications = 0


    def plugin_updated(self, type_plugins):
        if not self.get_config('notifyupdate'):
            return

        self.notify(_("Plugins updated"), str(type_plugins))


    def activate(self):
        self.key = (self.get_config('push-id'), self.get_config('push-url'))


    def exit(self):
        if not self.get_config('notifyexit'):
            return

        if self.pyload.do_restart:
            self.notify(_("Restarting pyLoad"))
        else:
            self.notify(_("Exiting pyLoad"))


    def captcha_task(self, task):
        if not self.get_config('notifycaptcha'):
            return

        self.notify(_("Captcha"), _("New request waiting user input"))


    def package_finished(self, pypack):
        if self.get_config('notifypackage'):
            self.notify(_("Package finished"), pypack.name)


    def all_downloads_processed(self):
        if not self.get_config('notifyprocessed'):
            return

        if any(True for pdata in self.pyload.api.getQueue() if pdata.linksdone < pdata.linkstotal):
            self.notify(_("Package failed"), _("One or more packages was not completed successfully"))
        else:
            self.notify(_("All packages finished"))


    def get_xml_data(self, msg):
        return ("<?xml version='1.0' encoding='utf-8'?> <wp:Notification xmlns:wp='WPNotification'> "
                "<wp:Toast> <wp:Text1>pyLoad</wp:Text1> <wp:Text2>%s</wp:Text2> "
                "</wp:Toast> </wp:Notification>" % msg)


    @Expose
    def notify(self,
               event,
               msg="",
               key=(None, None)):

        id, url = key or self.key
        if not id or not url:
            return

        if self.pyload.isClientConnected() and not self.get_config('ignoreclient'):
            return

        elapsed_time = time.time() - self.last_notify

        if elapsed_time < self.get_config("sendtimewait"):
            return

        if elapsed_time > 60:
            self.notifications = 0

        elif self.notifications >= self.get_config("sendpermin"):
            return

        request    = self.get_xml_data("%s: %s" % (event, msg) if msg else event)
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

        return True
