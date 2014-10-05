# -*- coding: utf-8 -*-

import re

from random import random

from pyload.plugins.base.Captcha import Captcha


class AdsCaptcha(Captcha):
    __name__ = "AdsCaptcha"
    __version__ = "0.02"

    __description__ = """AdsCaptcha captcha service plugin"""
    __author_name__ = "pyLoad Team"
    __author_mail__ = "admin@pyload.org"


    ID_PATTERN = r'http://api\.adscaptcha\.com/Get\.aspx\?[^"\']*CaptchaId=(?P<ID>\d+)'
    KEY_PATTERN = r'http://api\.adscaptcha\.com/Get\.aspx\?[^"\']*PublicKey=(?P<KEY>[\w-]+)'


    def detect_key(self, html=None):
        if not html:
            if hasattr(self.plugin, "html") and self.plugin.html:
                html = self.plugin.html
            else:
                errmsg = "AdsCaptcha html missing"
                self.plugin.fail(errmsg)
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


    def challenge(self, key=None):  #: key is tuple(CaptchaId, PublicKey)
        if not key:
            if self.key:
                key = self.key
            else:
                errmsg = "AdsCaptcha key missing"
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        CaptchaId, PublicKey = key

        js = self.plugin.req.load("http://api.adscaptcha.com/Get.aspx", get={'CaptchaId': CaptchaId, 'PublicKey': PublicKey}, cookies=True)

        try:
            challenge = re.search("challenge: '(.+?)',", js).group(1)
            server = re.search("server: '(.+?)',", js).group(1)
        except:
            self.plugin.parseError("AdsCaptcha challenge pattern not found")

        result = self.result(server, challenge)

        return challenge, result


    def result(self, server, challenge):
        return self.plugin.decryptCaptcha("%sChallenge.aspx" % server, get={'cid': challenge, 'dummy': random()},
                                          cookies=True, imgtype="jpg")
