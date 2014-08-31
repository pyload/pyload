# -*- coding: utf-8 -*-

import re

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class CatShareNet(SimpleHoster):
    __name__ = "CatShareNet"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?catshare.net/\w{16}.*'

    __description__ = """CatShare.net hoster plugin"""
    __author_name__ = "z00nx"
    __author_mail__ = "z00nx0@gmail.com"

    FILE_INFO_PATTERN = r'<h3 class="pull-left"[^>]+>(?P<N>.*)</h3>\s+<h3 class="pull-right"[^>]+>(?P<S>.*)</h3>'
    OFFLINE_PATTERN = r'Podany plik zosta'

    SECONDS_PATTERN = r'var\s+count\s+=\s+(\d+);'

    RECAPTCHA_KEY = "6Lfln9kSAAAAANZ9JtHSOgxUPB9qfDFeLUI_QMEy"


    def handleFree(self):
        m = re.search(self.SECONDS_PATTERN, self.html)
        seconds = int(m.group(1))
        self.logDebug("Seconds found", seconds)
        self.wait(seconds + 1)
        recaptcha = ReCaptcha(self)
        challenge, code = recaptcha.challenge(self.RECAPTCHA_KEY)
        post_data = {"recaptcha_challenge_field": challenge, "recaptcha_response_field": code}
        self.download(self.pyfile.url, post=post_data)
        check = self.checkDownload({"html": re.compile("\A<!DOCTYPE html PUBLIC")})
        if check == "html":
            self.logDebug("Wrong captcha entered")
            self.invalidCaptcha()
            self.retry()


getInfo = create_getInfo(CatShareNet)
