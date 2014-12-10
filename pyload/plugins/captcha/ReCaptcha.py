# -*- coding: utf-8 -*-

import re

from pyload.plugins.Captcha import Captcha


class ReCaptcha(Captcha):
    __name    = "ReCaptcha"
    __type    = "captcha"
    __version = "0.08"

    __description = """ReCaptcha captcha service plugin"""
    __license     = "GPLv3"
    __authors     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN      = r'recaptcha(?:/api|\.net)/(?:challenge|noscript)\?k=([\w-]+)'
    KEY_AJAX_PATTERN = r'Recaptcha\.create\s*\(\s*["\']([\w-]+)'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("ReCaptcha html not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.KEY_PATTERN, html) or re.search(self.KEY_AJAX_PATTERN, html)
        if m:
            self.key = m.group(1).strip()
            self.plugin.logDebug("ReCaptcha key: %s" % self.key)
            return self.key
        else:
            self.plugin.logDebug("ReCaptcha key not found")
            return None


    def challenge(self, key=None):
        if not key:
            if self.detect_key():
                key = self.key
            else:
                errmsg = _("ReCaptcha key not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        html = self.plugin.req.load("http://www.google.com/recaptcha/api/challenge", get={'k': key})
        try:
            challenge = re.search("challenge : '(.+?)',", html).group(1)
            server    = re.search("server : '(.+?)',", html).group(1)
        except:
            errmsg = _("ReCaptcha challenge pattern not found")
            self.plugin.error(errmsg)
            raise ValueError(errmsg)

        self.plugin.logDebug("ReCaptcha challenge: %s" % challenge)

        return challenge, self.result(server, challenge)


    def result(self, server, challenge):
        result = self.plugin.decryptCaptcha("%simage" % server,
                                            get={'c': challenge},
                                            cookies=True,
                                            forceUser=True,
                                            imgtype="jpg")

        self.plugin.logDebug("ReCaptcha result: %s" % result)

        return result
