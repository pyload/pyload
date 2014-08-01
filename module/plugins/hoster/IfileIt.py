# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class IfileIt(SimpleHoster):
    __name__ = "IfileIt"
    __type__ = "hoster"
    __version__ = "0.27"

    __pattern__ = r'^unmatchable$'

    __description__ = """Ifile.it"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    LINK_PATTERN = r'</span> If it doesn\'t, <a target="_blank" href="([^"]+)">'
    RECAPTCHA_KEY_PATTERN = r"var __recaptcha_public\s*=\s*'([^']+)';"
    FILE_INFO_PATTERN = r'<span style="cursor: default;[^>]*>\s*(?P<N>.*?)\s*&nbsp;\s*<strong>\s*(?P<S>[0-9.]+)\s*(?P<U>[kKMG])i?B\s*</strong>\s*</span>'
    OFFLINE_PATTERN = r'<span style="cursor: default;[^>]*>\s*&nbsp;\s*<strong>\s*</strong>\s*</span>'
    TEMP_OFFLINE_PATTERN = r'<span class="msg_red">Downloading of this file is temporarily disabled</span>'


    def handleFree(self):
        ukey = re.match(self.__pattern__, self.pyfile.url).group(1)
        json_url = 'http://ifile.it/new_download-request.json'
        post_data = {"ukey": ukey, "ab": "0"}

        json_response = json_loads(self.load(json_url, post=post_data))
        self.logDebug(json_response)
        if json_response['status'] == 3:
            self.offline()

        if json_response['captcha']:
            captcha_key = re.search(self.RECAPTCHA_KEY_PATTERN, self.html).group(1)
            recaptcha = ReCaptcha(self)
            post_data['ctype'] = "recaptcha"

            for _ in xrange(5):
                post_data['recaptcha_challenge'], post_data['recaptcha_response'] = recaptcha.challenge(captcha_key)
                json_response = json_loads(self.load(json_url, post=post_data))
                self.logDebug(json_response)

                if json_response['retry']:
                    self.invalidCaptcha()
                else:
                    self.correctCaptcha()
                    break
            else:
                self.fail("Incorrect captcha")

        if not "ticket_url" in json_response:
            self.parseError("Download URL")

        self.download(json_response['ticket_url'])


getInfo = create_getInfo(IfileIt)
