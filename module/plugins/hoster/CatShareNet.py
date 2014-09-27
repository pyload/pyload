# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class CatShareNet(SimpleHoster):
    __name__ = "CatShareNet"
    __type__ = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?catshare\.net/\w{16}'

    __description__ = """CatShare.net hoster plugin"""
    __author_name__ = ("z00nx", "prOq", "Walter Purcaro")
    __author_mail__ = ("z00nx0@gmail.com", None, "vuolter@gmail.com")


    FILE_INFO_PATTERN = r'<title>(?P<N>.+) \((?P<S>[\d.]+) (?P<U>\w+)\)<'
    OFFLINE_PATTERN = r'Podany plik został usunięty\s*</div>'

    IP_BLOCKED_PATTERN = r'>Nasz serwis wykrył że Twój adres IP nie pochodzi z Polski.<'
    SECONDS_PATTERN = 'var count = (\d+);'
    RECAPTCHA_KEY = "6Lfln9kSAAAAANZ9JtHSOgxUPB9qfDFeLUI_QMEy"
    LINK_PATTERN = r'<form action="(.+?)" method="GET">'


    def getFileInfo(self):
        m = re.search(self.IP_BLOCKED_PATTERN, self.html)
        if m is None:
            self.fail("Only connections from Polish IP address are allowed")
        return super(CatShareNet, self).getFileInfo()


    def handleFree(self):
        m = re.search(self.SECONDS_PATTERN, self.html)
        if m:
            wait_time = int(m.group(1))
            self.wait(wait_time, True)

        recaptcha = ReCaptcha(self)
        challenge, code = recaptcha.challenge(self.RECAPTCHA_KEY)
        self.html = self.load(self.pyfile.url,
                              post={'recaptcha_challenge_field': challenge,
                                    'recaptcha_response_field': code})

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.invalidCaptcha()
            self.retry(reason="Wrong captcha entered")

        dl_link = m.group(1)
        self.download(dl_link)


getInfo = create_getInfo(CatShareNet)
