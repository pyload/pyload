# -*- coding: utf-8 -*-

from pyload.plugin.Plugin import Base


#@TODO: Extend Plugin class; remove all `html` args
class Captcha(Base):
    __name    = "Captcha"
    __type    = "captcha"
    __version = "0.25"

    __description = """Base captcha service plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, plugin):
        self.plugin = plugin
        self.key = None  #: last key detected
        super(Captcha, self).__init__(plugin.core)


    def detect_key(self, html=None):
        raise NotImplementedError


    def challenge(self, key=None, html=None):
        raise NotImplementedError


    def result(self, server, challenge):
        raise NotImplementedError
