# -*- coding: utf-8 -*-

from module.plugins.internal.Plugin import Plugin


#@TODO: Extend (new) Plugin class; remove all `html` args
class Captcha(Plugin):
    __name__    = "Captcha"
    __type__    = "captcha"
    __version__ = "0.30"

    __description__ = """Base captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    key = None  #: last key detected


    def __init__(self, plugin):
        self.plugin = plugin
        super(Captcha, self).__init__(plugin.core)


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
