# -*- coding: utf-8 -*-

import re

from pyload.plugin.Plugin import Base


#@TODO: Extend Plugin class; remove all `html` args
class Captcha(Base):
    __name__    = "Captcha"
    __type__    = "captcha"
    __version__ = "0.25"

    __description__ = """Base captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, plugin):
        self.plugin = plugin
        self.key = None  #: last key detected
        super(CaptchaService, self).__init__(plugin.core)


    def detect_key(self, html=None):
        raise NotImplementedError


    def challenge(self, key=None, html=None):
        raise NotImplementedError


    def result(self, server, challenge):
        raise NotImplementedError
