# -*- coding: utf-8 -*-

import re

from random import random

from pyload.plugins.internal.Captcha import Captcha


class AdsCaptcha(Captcha):
    __name__    = "AdsCaptcha"
    __type__    = "captcha"
    __version__ = "0.05"

    __description__ = """AdsCaptcha captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    ID_PATTERN = r'api\.adscaptcha\.com/Get\.aspx\?[^"\']*CaptchaId=(?P<ID>\d+)'
    KEY_PATTERN = r'api\.adscaptcha\.com/Get\.aspx\?[^"\']*PublicKey=(?P<KEY>[\w-]+)'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = _("AdsCaptcha html not found")
                self.plugin.error(errmsg)
                raise TypeError(errmsg)

        m = re.search(self.ID_PATTERN, html)
        n = re.search(self.KEY_PATTERN, html)
        if m and n:
            self.key = (m.group("ID"), m.group("KEY"))
            self.plugin.logDebug("AdsCaptcha id|key: %s | %s" % self.key)
            return self.key
        else:
            self.plugin.logDebug("AdsCaptcha id or key not found")
            return None


    def challenge(self, key=None):  #: key is a tuple(CaptchaId, PublicKey)
        if not key:
            if self.detect_key():
                key = self.key
            else:
                errmsg = _("AdsCaptcha key not found")
                self.plugin.error(errmsg)
                raise TypeError(errmsg)

        CaptchaId, PublicKey = key

        js = self.plugin.req.load("http://api.adscaptcha.com/Get.aspx", get={'CaptchaId': CaptchaId, 'PublicKey': PublicKey})
        try:
            challenge = re.search("challenge: '(.+?)',", js).group(1)
            server = re.search("server: '(.+?)',", js).group(1)
        except:
            self.plugin.error(_("AdsCaptcha challenge pattern not found"))

        result = self.result(server, challenge)

        self.plugin.logDebug("AdsCaptcha result: %s" % result, "challenge: %s" % challenge)

        return challenge, result


    def result(self, server, challenge):
        return self.plugin.decryptCaptcha("%sChallenge.aspx" % server, get={'cid': challenge, 'dummy': random()},
                                          cookies=True, imgtype="jpg")
