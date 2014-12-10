# -*- coding: utf-8 -*-

import re

from pyload.utils import json_loads
from pyload.plugins.internal.captcha import ReCaptcha
from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class IfileIt(SimpleHoster):
    __name__    = "IfileIt"
    __type__    = "hoster"
    __version__ = "0.28"

    __pattern__ = r'^unmatchable$'

    __description__ = """Ifile.it"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'</span> If it doesn\'t, <a target="_blank" href="([^"]+)">'
    RECAPTCHA_PATTERN = r'var __recaptcha_public\s*=\s*\'(.+?)\''
    INFO_PATTERN = r'<span style="cursor: default;[^>]*>\s*(?P<N>.*?)\s*&nbsp;\s*<strong>\s*(?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)\s*</strong>\s*</span>'
    OFFLINE_PATTERN = r'<span style="cursor: default;[^>]*>\s*&nbsp;\s*<strong>\s*</strong>\s*</span>'
    TEMP_OFFLINE_PATTERN = r'<span class="msg_red">Downloading of this file is temporarily disabled</span>'


    def handleFree(self):
        ukey      = re.match(self.__pattern__, self.pyfile.url).group(1)
        json_url  = 'http://ifile.it/new_download-request.json'
        post_data = {"ukey": ukey, "ab": "0"}
        res       = json_loads(self.load(json_url, post=post_data))

        self.logDebug(res)

        if res['status'] == 3:
            self.offline()

        if res['captcha']:
            captcha_key = re.search(self.RECAPTCHA_PATTERN, self.html).group(1)

            recaptcha = ReCaptcha(self)
            post_data['ctype'] = "recaptcha"

            for _i in xrange(5):
                challenge, response = recaptcha.challenge(captcha_key)
                post_data.update({'recaptcha_challenge': challenge,
                                  'recaptcha_response' : response})
                res = json_loads(self.load(json_url, post=post_data))
                self.logDebug(res)

                if res['retry']:
                    self.invalidCaptcha()
                else:
                    self.correctCaptcha()
                    break
            else:
                self.fail(_("Incorrect captcha"))

        if not "ticket_url" in res:
            self.error(_("No download URL"))

        self.download(res['ticket_url'])


getInfo = create_getInfo(IfileIt)
