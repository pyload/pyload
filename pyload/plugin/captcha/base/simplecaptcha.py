# -*- coding: utf-8 -*-
#@author: zoidberg

from __future__ import unicode_literals

import re
from builtins import object
from random import random


class CaptchaService(object):
    __version__ = "0.04"

    def __init__(self, plugin):
        self.plugin = plugin


class ReCaptcha(object):
    RECAPTCHA_KEY_PATTERN = r"https?://(?:www\.)?google\.com/recaptcha/api/challenge\?k=(?P<key>\w+)"
    RECAPTCHA_KEY_AJAX_PATTERN = r"Recaptcha\.create\s*\(\s*[\"'](?P<key>\w+)[\"']\s*,"

    recaptcha_key = None

    def __init__(self, plugin):
        self.plugin = plugin

    def detect_key(self, html):
        m = re.search(self.RECAPTCHA_KEY_PATTERN, html)
        if not m:
            m = re.search(self.RECAPTCHA_KEY_AJAX_PATTERN, html)
        if m:
            self.recaptcha_key = m.group('key')
            return self.recaptcha_key
        else:
            return None

    def challenge(self, key=None):
        if not key and self.recaptcha_key:
            key = self.recaptcha_key
        elif not (key or self.recaptcha_key):
            raise TypeError("ReCaptcha key not found")

        js = self.plugin.req.load(
            "http://www.google.com/recaptcha/api/challenge", get={"k": key}, cookies=True)

        try:
            challenge = re.search("challenge : '(.*?)',", js).group(1)
            server = re.search("server : '(.*?)',", js).group(1)
        except Exception:
            self.plugin.fail(_("recaptcha error"))
        result = self.result(server, challenge)

        return challenge, result

    def result(self, server, challenge):
        return self.plugin.decrypt_captcha("{}image".format(server), get={"c": challenge},
                                           cookies=True, forceuser=True, imgtype="jpg")


class AdsCaptcha(CaptchaService):

    def challenge(self, src):
        js = self.plugin.req.load(src, cookies=True)

        try:
            challenge = re.search("challenge: '(.*?)',", js).group(1)
            server = re.search("server: '(.*?)',", js).group(1)
        except Exception:
            self.plugin.fail(_("adscaptcha error"))
        result = self.result(server, challenge)

        return challenge, result

    def result(self, server, challenge):
        return self.plugin.decrypt_captcha("{}Challenge.aspx".format(server), get={"cid": challenge, "dummy": random()},
                                           cookies=True, imgtype="jpg")


class SolveMedia(CaptchaService):

    def challenge(self, src):
        html = self.plugin.req.load(
            "http://api.solvemedia.com/papi/challenge.noscript?k={}".format(src), cookies=True)
        try:
            challenge = re.search(r'<input type=hidden name="adcopy_challenge" id="adcopy_challenge" value="([^"]+)">',
                                  html).group(1)
        except Exception:
            self.plugin.fail(_("solvemedia error"))
        result = self.result(challenge)

        return challenge, result

    def result(self, challenge):
        return self.plugin.decrypt_captcha(
            "http://api.solvemedia.com/papi/media?c={}".format(challenge), imgtype="gif")
