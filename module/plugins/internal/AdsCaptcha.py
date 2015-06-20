# -*- coding: utf-8 -*-

import random
import re

from module.plugins.internal.Captcha import Captcha


class AdsCaptcha(Captcha):
    __name__    = "AdsCaptcha"
    __type__    = "captcha"
    __version__ = "0.09"

    __description__ = """AdsCaptcha captcha service plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    CAPTCHAID_PATTERN  = r'api\.adscaptcha\.com/Get\.aspx\?.*?CaptchaId=(\d+)'
    PUBLICKEY_PATTERN = r'api\.adscaptcha\.com/Get\.aspx\?.*?PublicKey=([\w-]+)'


    def detect_key(self, html=None):
        html = html or self.retrieve_html()

        m = re.search(self.PUBLICKEY_PATTERN, html)
        n = re.search(self.CAPTCHAID_PATTERN, html)
        if m and n:
            self.key = (m.group(1).strip(), n.group(1).strip())  #: key is the tuple(PublicKey, CaptchaId)
            self.logDebug("Key: %s | ID: %s" % self.key)
            return self.key
        else:
            self.logWarning("Key or id pattern not found")
            return None


    def challenge(self, key=None, html=None):
        PublicKey, CaptchaId = key or self.retrieve_key(html)

        html = self.plugin.req.load("http://api.adscaptcha.com/Get.aspx",
                                    get={'CaptchaId': CaptchaId,
                                         'PublicKey': PublicKey})
        try:
            challenge = re.search("challenge: '(.+?)',", html).group(1)
            server    = re.search("server: '(.+?)',", html).group(1)

        except AttributeError:
            self.fail(_("AdsCaptcha challenge pattern not found"))

        self.logDebug("Challenge: %s" % challenge)

        return self.result(server, challenge), challenge


    def result(self, server, challenge):
        result = self.plugin.decryptCaptcha("%sChallenge.aspx" % server,
                                            get={'cid': challenge, 'dummy': random.random()},
                                            cookies=True,
                                            imgtype="jpg")

        self.logDebug("Result: %s" % result)

        return result
