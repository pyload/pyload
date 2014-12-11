# -*- coding: utf-8 -*-

import re

from random import random

from pyload.plugins.Captcha import Captcha


class AdsCaptcha(Captcha):
    __name    = "AdsCaptcha"
    __type    = "captcha"
    __version = "0.06"

    __description = """AdsCaptcha captcha service plugin"""
    __license     = "GPLv3"
    __authors     = [("pyLoad Team", "admin@pyload.org")]


    CAPTCHAID_PATTERN  = r'api\.adscaptcha\.com/Get\.aspx\?[^"\']*CaptchaId=(\d+)'
    PUBLICKEY_PATTERN = r'api\.adscaptcha\.com/Get\.aspx\?[^"\']*PublicKey=([\w-]+)'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("AdsCaptcha html not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.PUBLICKEY_PATTERN, html)
        n = re.search(self.CAPTCHAID_PATTERN, html)
        if m and n:
            self.key = (m.group(1).strip(), n.group(1).strip())  #: key is the tuple(PublicKey, CaptchaId)
            self.plugin.logDebug("AdsCaptcha key|id: %s | %s" % self.key)
            return self.key
        else:
            self.plugin.logDebug("AdsCaptcha key or id not found")
            return None


    def challenge(self, key=None):
        if not key:
            if self.detect_key():
                key = self.key
            else:
                errmsg = _("AdsCaptcha key not found")
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        PublicKey, CaptchaId = key

        html = self.plugin.req.load("http://api.adscaptcha.com/Get.aspx", get={'CaptchaId': CaptchaId, 'PublicKey': PublicKey})
        try:
            challenge = re.search("challenge: '(.+?)',", html).group(1)
            server    = re.search("server: '(.+?)',", html).group(1)
        except Exception:
            errmsg = _("AdsCaptcha challenge pattern not found")
            self.plugin.error(errmsg)
            raise ValueError(errmsg)

        self.plugin.logDebug("AdsCaptcha challenge: %s" % challenge)

        return challenge, self.result(server, challenge)


    def result(self, server, challenge):
        result = self.plugin.decryptCaptcha("%sChallenge.aspx" % server,
                                            get={'cid': challenge, 'dummy': random()},
                                            cookies=True,
                                            imgtype="jpg")

        self.plugin.logDebug("AdsCaptcha result: %s" % result)

        return result
