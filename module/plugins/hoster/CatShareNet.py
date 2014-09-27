# -*- coding: utf-8 -*-

import re

from urllib import unquote

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class CatShareNet(SimpleHoster):
    __name__ = "CatShareNet"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?catshare\.net/\w{16}'

    __description__ = """CatShare.net hoster plugin"""
    __author_name__ = ("z00nx", "prOq")
    __author_mail__ = ("z00nx0@gmail.com", None)


    FILE_INFO_PATTERN = r'<h3 class="pull-left"[^>]+>(?P<N>.+)</h3>\s+<h3 class="pull-right"[^>]+>(?P<S>.+)</h3>'
    FILE_OFFLINE_PATTERN = r'Podany plik zosta'

    SECONDS_PATTERN = 'var\s+count\s+=\s+(\d+);'
    RECAPTCHA_KEY = "6Lfln9kSAAAAANZ9JtHSOgxUPB9qfDFeLUI_QMEy"
    LINK_PATTERN = r'<form action="(.+?)" method="GET">'


    def handleFree(self):
        m = re.search(self.SECONDS_PATTERN, self.html)
        if m is not None:
            seconds = int(m.group(1))
            self.logDebug("Seconds found", seconds)
            self.wait(seconds + 1)

        # solve captcha and send solution
        recaptcha = ReCaptcha(self)
        challenge, code = recaptcha.challenge(self.RECAPTCHA_KEY)
        self.html = self.load(self.pyfile.url,
                              post={'recaptcha_challenge_field': challenge, 'recaptcha_response_field': code},
                              decode=True,
                              cookies=True,
                              ref=True)

        # find download url
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.invalidCaptcha()
            self.retry(reason="Wrong captcha entered")

        download_url = unquote(m.group(1))
        self.logDebug("Download url: " + download_url)
        self.download(download_url)


getInfo = create_getInfo(CatShareNet)
