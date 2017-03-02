# -*- coding: utf-8 -*-

from .Captcha import Captcha


class CaptchaService(Captcha):
    __name__ = "CaptchaService"
    __type__ = "captcha"
    __version__ = "0.36"
    __status__ = "stable"

    __description__ = """Base anti-captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def init(self):
        self.key = None  #: Last key detected

    #@TODO: Recheck in 0.4.10
    def retrieve_key(self, data):
        if self.detect_key(data):
            return self.key
        else:
            self.fail(_("%s key not found") % self.__name__)

    def retrieve_data(self):
        return self.pyfile.plugin.data or self.pyfile.plugin.last_html or ""

    def detect_key(self, data=None):
        raise NotImplementedError

    def challenge(self, key=None, data=None):
        raise NotImplementedError

    def result(self, server, challenge):
        raise NotImplementedError
