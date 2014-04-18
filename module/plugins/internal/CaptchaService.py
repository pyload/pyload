# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

import re
from random import random


class CaptchaService():
    __version__ = "0.04"

    def __init__(self, plugin):
        self.plugin = plugin


class ReCaptcha():
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

        js = self.plugin.req.load("http://www.google.com/recaptcha/api/challenge", get={"k": key}, cookies=True)

        try:
            challenge = re.search("challenge : '(.*?)',", js).group(1)
            server = re.search("server : '(.*?)',", js).group(1)
        except:
            self.plugin.fail("recaptcha error")
        result = self.result(server, challenge)

        return challenge, result

    def result(self, server, challenge):
        return self.plugin.decryptCaptcha("%simage" % server, get={"c": challenge},
                                          cookies=True, forceUser=True, imgtype="jpg")


class AdsCaptcha(CaptchaService):
    def challenge(self, src):
        js = self.plugin.req.load(src, cookies=True)

        try:
            challenge = re.search("challenge: '(.*?)',", js).group(1)
            server = re.search("server: '(.*?)',", js).group(1)
        except:
            self.plugin.fail("adscaptcha error")
        result = self.result(server, challenge)

        return challenge, result

    def result(self, server, challenge):
        return self.plugin.decryptCaptcha("%sChallenge.aspx" % server, get={"cid": challenge, "dummy": random()},
                                          cookies=True, imgtype="jpg")


class SolveMedia(CaptchaService):
    def __init__(self, plugin):
        self.plugin = plugin

    def challenge(self, src):
        html = self.plugin.req.load("http://api.solvemedia.com/papi/challenge.noscript?k=%s" % src, cookies=True)
        try:
            challenge = re.search(r'<input type=hidden name="adcopy_challenge" id="adcopy_challenge" value="([^"]+)">',
                                  html).group(1)
        except:
            self.plugin.fail("solvemedia error")
        result = self.result(challenge)

        return challenge, result

    def result(self, challenge):
        return self.plugin.decryptCaptcha("http://api.solvemedia.com/papi/media?c=%s" % challenge, imgtype="gif")
