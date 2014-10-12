# -*- coding: utf-8 -*-

import re

from random import random


class CaptchaService:
    __name__ = "CaptchaService"
    __version__ = "0.11"

    __description__ = """Base captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = None

    key = None


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


class ReCaptcha(CaptchaService):
    __name__ = "ReCaptcha"
    __version__ = "0.04"

    __description__ = """ReCaptcha captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = r'https?://(?:www\.)?google\.com/recaptcha/api/challenge\?k=(?P<KEY>[\w-]+)'
    KEY_AJAX_PATTERN = r'Recaptcha\.create\s*\(\s*["\'](?P<KEY>[\w-]+)'


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


class AdsCaptcha(CaptchaService):
    __name__ = "AdsCaptcha"
    __version__ = "0.02"

    __description__ = """AdsCaptcha captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad Team", "admin@pyload.org")]


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


class SolveMedia(CaptchaService):
    __name__ = "SolveMedia"
    __version__ = "0.03"

    __description__ = """SolveMedia captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad Team", "admin@pyload.org")]


    KEY_PATTERN = r'http://api\.solvemedia\.com/papi/challenge\.(no)?script\?k=(?P<KEY>.+?)["\']'


    def challenge(self, key=None):
        if not key:
            if self.key:
                key = self.key
            else:
                errmsg = "SolveMedia key missing"
                self.plugin.fail(errmsg)
                raise TypeError(errmsg)

        html = self.plugin.req.load("http://api.solvemedia.com/papi/challenge.noscript", get={'k': key}, cookies=True)
        try:
            challenge = re.search(r'<input type=hidden name="adcopy_challenge" id="adcopy_challenge" value="([^"]+)">',
                                  html).group(1)
            server = "http://api.solvemedia.com/papi/media"
        except:
            self.plugin.parseError("SolveMedia challenge pattern not found")

        result = self.result(server, challenge)

        return challenge, result


    def result(self, server, challenge):
        return self.plugin.decryptCaptcha(server, get={'c': challenge}, imgtype="gif")
