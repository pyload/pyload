# -*- coding: utf-8 -*-


from module.plugins.Hook import Hook
from module.network.RequestFactory import getURL

class AndroidPhoneNotify(Hook):
    __name__    = "AndroidPhoneNotify"
    __type__    = "hook"
    __version__ = "0.01"

    __config__ = [("apikey", "str", "apikey", ""),
                  ("appname", "str", "ApplicationName", "pyLoad"),
                  ("notifycaptcha", "bool", "Send captcha notifications (maybe usefull if premium fails)", False)]

    __description__ = """Send push notifications to your Android Phone using notifymyandroid.com"""
    __license__     = "GPLv3"
    __authors__     = [("Steven Kosyra", "steven.kosyra@gmail.com")]


    def packageFinished(self, pypack):
                self.genUrl("Package finished:",pypack.name)


    def newCaptchaTask(self, task):
        if self.getConfig("notifycaptcha"):
                self.genUrl("Captcha","new Captcha request")



    def genUrl(self,event, msg):
                self.response(event, msg)



    def response(self, event, msg):
        html = getURL("http://www.notifymyandroid.com/publicapi/notify?apikey=" + self.getConfig("apikey") + "&application=" + self.getConfig("appname") + "&event=" + str(event) + "&description= " + str(msg) + "")
