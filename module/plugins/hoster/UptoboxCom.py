# -*- coding: utf-8 -*-
###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: Walter Purcaro
###############################################################################

import re
from urllib import unquote

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha, SolveMedia
from module.utils import html_unescape


class UptoboxCom(XFileSharingPro):
    __name__ = "UptoboxCom"
    __type__ = "hoster"
    __pattern__ = r'https?://(?:www\.)?uptobox\.com/\w+'
    __version__ = "0.09"
    __description__ = """Uptobox.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    HOSTER_NAME = "uptobox.com"

    FILE_INFO_PATTERN = r'"para_title">(?P<N>.+) \((?P<S>[\d\.]+) (?P<U>\w+)\)'
    FILE_OFFLINE_PATTERN = r'>(File not found|Access Denied|404 Not Found)'
    TEMP_OFFLINE_PATTERN = r'>This server is in maintenance mode'

    WAIT_PATTERN = r'>(\d+)</span> seconds<'

    DIRECT_LINK_PATTERN = r'"(https?://\w+\.uptobox\.com/d/.*?)"'

    def handleCaptcha(self, inputs):
        found = re.search(self.SOLVEMEDIA_PATTERN, self.html)
        if found:
            captcha_key = found.group(1)
            captcha = SolveMedia(self)
            inputs['adcopy_challenge'], inputs['adcopy_response'] = captcha.challenge(captcha_key)
            return 4
        else:
            found = re.search(self.CAPTCHA_URL_PATTERN, self.html)
            if found:
                captcha_url = found.group(1)
                inputs['code'] = self.decryptCaptcha(captcha_url)
                return 2
            else:
                found = re.search(self.CAPTCHA_DIV_PATTERN, self.html, re.DOTALL)
                if found:
                    captcha_div = found.group(1)
                    self.logDebug(captcha_div)
                    numerals = re.findall(r'<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>',
                                          html_unescape(captcha_div))
                    inputs['code'] = "".join([a[1] for a in sorted(numerals, key=lambda num: int(num[0]))])
                    self.logDebug("CAPTCHA", inputs['code'], numerals)
                    return 3
                else:
                    found = re.search(self.RECAPTCHA_URL_PATTERN, self.html)
                    if found:
                        recaptcha_key = unquote(found.group(1))
                        self.logDebug("RECAPTCHA KEY: %s" % recaptcha_key)
                        recaptcha = ReCaptcha(self)
                        inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(
                            recaptcha_key)
                        return 1
        return 0


getInfo = create_getInfo(UptoboxCom)
