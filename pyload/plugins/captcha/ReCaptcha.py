# -*- coding: utf-8 -*-

import re

from pyload.plugins.base.Captcha import Captcha


class ReCaptcha(Captcha):
    __name__ = "ReCaptcha"
    __version__ = "0.02"

    __description__ = """ReCaptcha captcha service plugin"""
    __authors__ = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = r"https?://(?:www\.)?google\.com/recaptcha/api/challenge\?k=(?P<KEY>\w+?)"
    KEY_AJAX_PATTERN = r"Recaptcha\.create\s*\(\s*[\"'](?P<KEY>\w+)[\"']\s*,"


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = "ReCaptcha html missing"
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.KEY_PATTERN, html)
        if m is None:
            m = re.search(self.KEY_AJAX_PATTERN, html)
        if m:
            self.key = m.group("KEY")
            self.plugin.logDebug("ReCaptcha key: %s" % self.key)
            return self.key
        else:
            self.plugin.logDebug("ReCaptcha key not found")
            return None


    def challenge(self, key=None):
        if not key:
            if self.key:
                key = self.key
            else:
                errmsg = "ReCaptcha key missing"
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        js = self.plugin.req.load("http://www.google.com/recaptcha/api/challenge", get={'k': key}, cookies=True)

        try:
            challenge = re.search("challenge : '(.+?)',", js).group(1)
            server = re.search("server : '(.+?)',", js).group(1)
        except:
            self.plugin.parseError("ReCaptcha challenge pattern not found")

        result = self.result(server, challenge)

        return challenge, result


    def result(self, server, challenge):
        return self.plugin.decryptCaptcha("%simage" % server, get={'c': challenge},
                                          cookies=True, forceUser=True, imgtype="jpg")
