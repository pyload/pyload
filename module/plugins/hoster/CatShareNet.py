# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class CatShareNet(SimpleHoster):
    __name__ = "CatShareNet"
    __type__ = "hoster"
    __version__ = "0.06"

    __pattern__ = r'http://(?:www\.)?catshare\.net/\w{16}'

    __description__ = """CatShare.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("z00nx", "z00nx0@gmail.com"),
                   ("prOq", None),
                   ("Walter Purcaro", "vuolter@gmail.com")]


    TEXT_ENCODING = True

    FILE_INFO_PATTERN = r'<title>(?P<N>.+) \((?P<S>[\d.]+) (?P<U>\w+)\)<'
    OFFLINE_PATTERN = r'Podany plik został usunięty\s*</div>'

    IP_BLOCKED_PATTERN = r'>Nasz serwis wykrył że Twój adres IP nie pochodzi z Polski.<'
    SECONDS_PATTERN = 'var\scount\s=\s(\d+);'
    LINK_PATTERN = r'<form action="(.+?)" method="GET">'


    def setup(self):
        self.multiDL = self.premium
        self.resumeDownload = True


    def getFileInfo(self):
        m = re.search(self.IP_BLOCKED_PATTERN, self.html)
        if m:
            self.fail("Only connections from Polish IP address are allowed")
        return super(CatShareNet, self).getFileInfo()


    def handleFree(self):
        m = re.search(self.SECONDS_PATTERN, self.html)
        if m:
            wait_time = int(m.group(1))
            self.wait(wait_time, True)

        recaptcha = ReCaptcha(self)

        captcha_key = recaptcha.detect_key()
        if captcha_key is None:
            self.parseError("ReCaptcha key not found")

        challenge, code = recaptcha.challenge(captcha_key)
        self.html = self.load(self.pyfile.url,
                              post={'recaptcha_challenge_field': challenge,
                                    'recaptcha_response_field': code})

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.invalidCaptcha()
            self.retry(reason="Wrong captcha entered")

        dl_link = m.group(1)
        self.download(dl_link, disposition=True)


getInfo = create_getInfo(CatShareNet)
