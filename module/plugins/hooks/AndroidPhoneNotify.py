# -*- coding: utf-8 -*-

from time import time

from module.network.RequestFactory import getURL
from module.plugins.Hook import Hook


class AndroidPhoneNotify(Hook):
    __name__    = "AndroidPhoneNotify"
    __type__    = "hook"
    __version__ = "0.03"

    __config__ = [("apikey"         , "str" , "API key"                                  , ""   ),
                  ("notifycaptcha"  , "bool", "Notify captcha request"                   , True ),
                  ("notifypackage"  , "bool", "Notify package finished"                  , True ),
                  ("notifyprocessed", "bool", "Notify processed packages status"         , True ),
                  ("timeout"        , "int" , "Timeout between captchas in seconds"      , 5    ),
                  ("force"          , "bool", "Send notifications if client is connected", False)]

    __description__ = """Send push notifications to your Android Phone using notifymyandroid.com"""
    __license__     = "GPLv3"
    __authors__     = [("Steven Kosyra", "steven.kosyra@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["allDownloadsProcessed"]


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def newCaptchaTask(self, task):
        if not self.getConfig("notifycaptcha"):
            return False

        if time() - float(self.getStorage("AndroidPhoneNotify", 0)) < self.getConf("timeout"):
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


    def notify(self, event, msg=""):
        apikey = self.getConfig("apikey")

        if not apikey:
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        getURL("http://www.notifymyandroid.com/publicapi/notify",
               get={'apikey'     : apikey,
                    'application': "pyLoad",
                    'event'      : event,
                    'description': msg})

        self.setStorage("AndroidPhoneNotify", time())
