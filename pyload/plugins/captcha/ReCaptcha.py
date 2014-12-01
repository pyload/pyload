# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.Captcha import Captcha


class ReCaptcha(Captcha):
    __name__    = "ReCaptcha"
    __type__    = "captcha"
    __version__ = "0.08"

    __description__ = """ReCaptcha captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = r'recaptcha(/api|\.net)/(challenge|noscript)\?k=(?P<KEY>[\w-]+)'
    KEY_AJAX_PATTERN = r'Recaptcha\.create\s*\(\s*["\'](?P<KEY>[\w-]+)'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("ReCaptcha html not found")
                self.plugin.error(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.KEY_PATTERN, html) or re.search(self.KEY_AJAX_PATTERN, html)
        if m:
            self.key = m.group("KEY")
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
                self.plugin.error(errmsg)
                raise TypeError(errmsg)

        js = self.plugin.req.load("http://www.google.com/recaptcha/api/challenge", get={'k': key})
        try:
            challenge = re.search("challenge : '(.+?)',", js).group(1)
            server = re.search("server : '(.+?)',", js).group(1)
        except Exception:
            self.plugin.error(_("ReCaptcha challenge pattern not found"))

        result = self.result(server, challenge)

        self.plugin.logDebug("ReCaptcha result: %s" % result, "challenge: %s" % challenge)

        return challenge, result


    def result(self, server, challenge):
        return self.plugin.decryptCaptcha("%simage" % server, get={'c': challenge},
                                          cookies=True, forceUser=True, imgtype="jpg")
