# -*- coding: utf-8 -*-

from module.plugins.internal.Captcha import Captcha


class CaptchaService(Captcha):
    __name__    = "CaptchaService"
    __type__    = "captcha"
    __version__ = "0.32"
    __status__  = "testing"

    __description__ = """Base anti-captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def init(self):
        self.key = None  #: Last key detected


    #@TODO: Recheck in 0.4.10
    def retrieve_key(self, data):
        if self.detect_key(data):
            return self.key
        else:
            self.fail(_("%s key not found") % self.__name__)


    #@TODO: Recheck in 0.4.10, html is now pyfile.data
    def retrieve_data(self):
        if hasattr(self.plugin, "html") and self.plugin.html:
            return self.plugin.html
        else:
            self.fail(_("%s data not found") % self.__name__)


    def detect_key(self, data=None):
        raise NotImplementedError


    def challenge(self, key=None, data=None):
        raise NotImplementedError


    def result(self, server, challenge):
        raise NotImplementedError
