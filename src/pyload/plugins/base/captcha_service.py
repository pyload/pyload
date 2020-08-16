# -*- coding: utf-8 -*-


from .captcha import BaseCaptcha


class CaptchaService(BaseCaptcha):
    __name__ = "CaptchaService"
    __type__ = "anticaptcha"
    __version__ = "0.36"
    __status__ = "stable"

    __description__ = """Anti-captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def init(self):
        self.key = None  #: Last key detected

    # TODO: Recheck in 0.6.x
    def retrieve_key(self, data):
        if self.detect_key(data):
            return self.key
        else:
            self.fail(self._("{} key not found").format(self.__name__))

    def retrieve_data(self):
        return self.pyfile.plugin.data or self.pyfile.plugin.last_html or ""

    def detect_key(self, data=None):
        raise NotImplementedError

    def challenge(self, key=None, data=None):
        raise NotImplementedError

    def result(self, server, challenge):
        raise NotImplementedError
