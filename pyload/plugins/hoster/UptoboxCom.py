# -*- coding: utf-8 -*-

import re

from urllib import unquote

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
from pyload.plugins.internal.CaptchaService import ReCaptcha, SolveMedia
from pyload.utils import html_unescape


class UptoboxCom(XFileSharingPro):
    __name__ = "UptoboxCom"
    __type__ = "hoster"
    __version__ = "0.09"

    __pattern__ = r'https?://(?:www\.)?uptobox\.com/\w+'

    __description__ = """Uptobox.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    HOSTER_NAME = "uptobox.com"

    FILE_INFO_PATTERN = r'"para_title">(?P<N>.+) \((?P<S>[\d\.]+) (?P<U>\w+)\)'
    OFFLINE_PATTERN = r'>(File not found|Access Denied|404 Not Found)'
    TEMP_OFFLINE_PATTERN = r'>This server is in maintenance mode'

    WAIT_PATTERN = r'>(\d+)</span> seconds<'

    LINK_PATTERN = r'"(https?://\w+\.uptobox\.com/d/.*?)"'


    def handleCaptcha(self, inputs):
        m = re.search(self.SOLVEMEDIA_PATTERN, self.html)
        if m:
            captcha_key = m.group(1)
            captcha = SolveMedia(self)
            inputs['adcopy_challenge'], inputs['adcopy_response'] = captcha.challenge(captcha_key)
            return 4
        else:
            m = re.search(self.CAPTCHA_URL_PATTERN, self.html)
            if m:
                captcha_url = m.group(1)
                inputs['code'] = self.decryptCaptcha(captcha_url)
                return 2
            else:
                m = re.search(self.CAPTCHA_DIV_PATTERN, self.html, re.DOTALL)
                if m:
                    captcha_div = m.group(1)
                    self.logDebug(captcha_div)
                    numerals = re.findall(r'<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>',
                                          html_unescape(captcha_div))
                    inputs['code'] = "".join([a[1] for a in sorted(numerals, key=lambda num: int(num[0]))])
                    self.logDebug("CAPTCHA", inputs['code'], numerals)
                    return 3
                else:
                    m = re.search(self.RECAPTCHA_URL_PATTERN, self.html)
                    if m:
                        recaptcha_key = unquote(m.group(1))
                        self.logDebug("RECAPTCHA KEY: %s" % recaptcha_key)
                        recaptcha = ReCaptcha(self)
                        inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(
                            recaptcha_key)
                        return 1
        return 0


getInfo = create_getInfo(UptoboxCom)
