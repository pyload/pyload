# -*- coding: utf-8 -*-

import re

from pyload.plugins.Plugin import Plugin


class Captcha(Plugin):
    __name__ = "Captcha"
    __version__ = "0.09"

    __description__ = """Base captcha service plugin"""
    __authors__ = [("pyLoad Team", "admin@pyload.org")]


    key = None

    KEY_PATTERN = None


    def __init__(self, plugin):
        self.plugin = plugin


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = "%s html missing" % self.__name__
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.KEY_PATTERN, html)
        if m:
            self.key = m.group("KEY")
            self.plugin.logDebug("%s key: %s" % (self.__name__, self.key))
            return self.key
        else:
            self.plugin.logDebug("%s key not found" % self.__name__)
            return None


    def challenge(self, key=None):
        raise NotImplementedError


    def result(self, server, challenge):
        raise NotImplementedError
