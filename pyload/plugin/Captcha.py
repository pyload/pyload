# -*- coding: utf-8 -*-

import re

from pyload.plugin.Plugin import Plugin


class Captcha(Plugin):
    __name    = "Captcha"
    __type    = "captcha"
    __version = "0.14"

    __description = """Base captcha service plugin"""
    __license     = "GPLv3"
    __authors     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = None

    key = None  #: last key detected


    def __init__(self, plugin):
        self.plugin = plugin


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("%s html not found") % self.__name
                self.plugin.error(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.KEY_PATTERN, html)
        if m:
            self.key = m.group("KEY")
            self.plugin.logDebug("%s key: %s" % (self.__name, self.key))
            return self.key
        else:
            self.plugin.logDebug("%s key not found" % self.__name)
            return None


    def challenge(self, key=None):
        raise NotImplementedError


    def result(self, server, challenge):
        raise NotImplementedError
