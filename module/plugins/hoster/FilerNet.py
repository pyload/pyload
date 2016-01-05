# -*- coding: utf-8 -*-
#
# Test links:
# http://filer.net/get/ivgf5ztw53et3ogd
# http://filer.net/get/hgo14gzcng3scbvv

import re

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster


class FilerNet(SimpleHoster):
    __name__    = "FilerNet"
    __type__    = "hoster"
    __version__ = "0.24"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?filer\.net/get/\w+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Filer.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN    = r'<h1 class="page-header">Free Download (?P<N>\S+) <small>(?P<S>[\w.]+) (?P<U>[\w^_]+)</small></h1>'
    OFFLINE_PATTERN = r'Nicht gefunden'

    WAIT_PATTERN = r'musst du <span id="time">(\d+)'

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'href="([^"]+)">Get download</a>'


    def handle_free(self, pyfile):
        inputs = self.parse_html_form(input_names={'token': re.compile(r'.+')})[1]
        if 'token' not in inputs:
            self.error(_("Unable to detect token"))

        self.data = self.load(pyfile.url, post={'token': inputs['token']})

        inputs = self.parse_html_form(input_names={'hash': re.compile(r'.+')})[1]
        if 'hash' not in inputs:
            self.error(_("Unable to detect hash"))

        self.captcha = ReCaptcha(pyfile)
        response, challenge = self.captcha.challenge()

        header = self.load(pyfile.url,
                           post={'recaptcha_challenge_field': challenge,
                                 'recaptcha_response_field' : response,
                                 'hash'                     : inputs['hash']},
                           just_header=True)

        self.link = header.get('location')
