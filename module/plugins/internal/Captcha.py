# -*- coding: utf-8 -*-

from module.plugins.internal.Plugin import Plugin


class Captcha(Plugin):
    __name__    = "Captcha"
    __type__    = "captcha"
    __version__ = "0.31"

    __description__ = """Base captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, plugin):
        super(Captcha, self).__init__(plugin.core)

        self.plugin = plugin
        self.key    = None  #: last key detected


    #@TODO: Recheck in 0.4.10
    def retrieve_key(self, html):
        if self.detect_key(html):
            return self.key
        else:
            self.fail(_("%s key not found") % self.__name__)


    #@TODO: Recheck in 0.4.10
    def retrieve_html(self):
        if hasattr(self.plugin, "html") and self.plugin.html:
            return self.plugin.html
        else:
            self.fail(_("%s html not found") % self.__name__)


    def detect_key(self, html=None):
        raise NotImplementedError


    def challenge(self, key=None, html=None):
        raise NotImplementedError


    def result(self, server, challenge):
        raise NotImplementedError
