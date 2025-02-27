# -*- coding: utf-8 -*-

# TODO let user manually solve captchas
# currently this requires premium account for
# src/pyload/plugins/addons/TwoCaptcha.py

import io
import os
import re
import urllib.parse

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    pass

from ..base.captcha_service import CaptchaService


# based on jdownloader
# src/org/jdownloader/captcha/v2/challenge/cutcaptcha/CutCaptchaChallenge.java

class CutCaptcha(CaptchaService):
    __name__ = "CutCaptcha"
    __type__ = "anticaptcha"
    __version__ = '0.1'
    __status__ = "testing"

    __description__ = "CutCaptcha captcha service plugin"
    __license__ = "MIT"
    __authors__ = [
        ("milahu", "milahu@gmail.com"),
    ]

    CUTCAPTCHA_CAPTCHA_KEY_PATTERN = r'''\sCUTCAPTCHA_MISERY_KEY\s*=\s*["']([0-9a-f]{40})["']'''
    CUTCAPTCHA_API_KEY_PATTERN = r'''cutcaptcha\.net/captcha/([0-9a-zA-Z]+)\.js'''

    def detect_key(self, data=None):
        html = data or self.retrieve_data()
        m = re.search(self.CUTCAPTCHA_CAPTCHA_KEY_PATTERN, self.data)
        if not m:
            self.log_error("Not found CUTCAPTCHA_CAPTCHA_KEY_PATTERN")
            return None
        self.key = m.group(1)
        self.log_debug(f"Key: {self.key}")
        return self.key

    def detect_api_key(self, data=None):
        m = re.search(self.CUTCAPTCHA_API_KEY_PATTERN, self.data)
        if not m:
            self.log_error("Not found CUTCAPTCHA_API_KEY_PATTERN")
            return None
        self.api_key = m.group(1)
        self.log_debug(f"API Key: {self.api_key}")
        return self.api_key

    def challenge(self, key=None, api_key=None, data=None, version=None, secure_token=None):
        key = key or self.retrieve_key(data)
        api_key = api_key or self.detect_api_key(data)
        params = {
            "url": self.pyfile.url,
            "miseryKey": key,
            "apiKey": api_key,
        }
        result = self.decrypt_interactive(params, timeout=300)
        return result
