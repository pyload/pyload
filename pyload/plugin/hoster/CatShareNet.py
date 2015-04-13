# -*- coding: utf-8 -*-

import re

from pyload.plugin.captcha.ReCaptcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster


class CatShareNet(SimpleHoster):
    __name    = "CatShareNet"
    __type    = "hoster"
    __version = "0.13"

    __pattern = r'http://(?:www\.)?catshare\.net/\w{16}'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """CatShare.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("z00nx", "z00nx0@gmail.com"),
                       ("prOq", ""),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    TEXT_ENCODING = True

    INFO_PATTERN = r'<title>(?P<N>.+) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)<'
    OFFLINE_PATTERN = r'<div class="alert alert-error"'

    IP_BLOCKED_PATTERN = ur'>Nasz serwis wykrył że Twój adres IP nie pochodzi z Polski.<'
    WAIT_PATTERN       = r'var\scount\s=\s(\d+);'

    LINK_FREE_PATTERN    = r'<form action="(.+?)" method="GET">'
    LINK_PREMIUM_PATTERN = r'<form action="(.+?)" method="GET">'


    def setup(self):
        self.multiDL        = self.premium
        self.resumeDownload = True


    def checkErrors(self):
        m = re.search(self.IP_BLOCKED_PATTERN, self.html)
        if m:
            self.fail(_("Only connections from Polish IP address are allowed"))

        return super(CatShareNet, self).checkErrors()


    def handleFree(self, pyfile):
        recaptcha = ReCaptcha(self)

        response, challenge = recaptcha.challenge()
        self.html = self.load(pyfile.url,
                              post={'recaptcha_challenge_field': challenge,
                                    'recaptcha_response_field' : response})

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m:
            self.link = m.group(1)

