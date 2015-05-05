# -*- coding: utf-8 -*-
#
# Test links:
#   http://filer.net/get/ivgf5ztw53et3ogd
#   http://filer.net/get/hgo14gzcng3scbvv

import re
import urlparse

from pyload.plugin.captcha.ReCaptcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster


class FilerNet(SimpleHoster):
    __name    = "FilerNet"
    __type    = "hoster"
    __version = "0.19"

    __pattern = r'https?://(?:www\.)?filer\.net/get/\w+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Filer.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it"),
                     ("Walter Purcaro", "vuolter@gmail.com")]

    INFO_PATTERN    = r'<h1 class="page-header">Free Download (?P<N>\S+) <small>(?P<S>[\w.]+) (?P<U>[\w^_]+)</small></h1>'
    OFFLINE_PATTERN = r'Nicht gefunden'

    WAIT_PATTERN = r'musst du <span id="time">(\d+)'

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'href="([^"]+)">Get download</a>'


    def handle_free(self, pyfile):
        inputs = self.parseHtmlForm(input_names={'token': re.compile(r'.+')})[1]
        if 'token' not in inputs:
            self.error(_("Unable to detect token"))

        self.html = self.load(pyfile.url, post={'token': inputs['token']}, decode=True)

        inputs = self.parseHtmlForm(input_names={'hash': re.compile(r'.+')})[1]
        if 'hash' not in inputs:
            self.error(_("Unable to detect hash"))

        recaptcha           = ReCaptcha(self)
        response, challenge = recaptcha.challenge()

        self.load(pyfile.url, post={'recaptcha_challenge_field': challenge,
                                    'recaptcha_response_field': response,
                                    'hash': inputs['hash']}, follow_location=False)

        if 'location' in self.req.http.header.lower():
            self.link = re.search(r'location: (\S+)', self.req.http.header, re.I).group(1)
            self.correctCaptcha()
        else:
            self.invalidCaptcha()
