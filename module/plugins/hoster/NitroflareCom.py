# -*- coding: utf-8 -*-

import re

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster


class NitroflareCom(SimpleHoster):
    __name__    = "NitroflareCom"
    __type__    = "hoster"
    __version__ = "0.15"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?nitroflare\.com/view/(?P<ID>[\w^_]+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Nitroflare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("sahil"         , "sahilshekhawat01@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("Stickell"      , "l.stickell@yahoo.it"       )]

    INFO_PATTERN    = r'title="(?P<N>.+?)".+>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File doesn\'t exist'

    LINK_PREMIUM_PATTERN = LINK_FREE_PATTERN = r'(https?://[\w\-]+\.nitroflare\.com/.+?)"'

    RECAPTCHA_KEY        = "6Lenx_USAAAAAF5L1pmTWvWcH73dipAEzNnmNLgy"
    PREMIUM_ONLY_PATTERN = r'This file is available with Premium only'
    WAIT_PATTERN         = r'You have to wait (\d+ minutes)'
    # ERROR_PATTERN        = r'downloading is not possible'


    def handle_free(self, pyfile):
        #: Used here to load the cookies which will be required later
        self.load(pyfile.url, post={'goToFreePage': ""})

        self.load("http://nitroflare.com/ajax/setCookie.php", post={'fileId': self.info['pattern']['ID']})
        self.html = self.load("http://nitroflare.com/ajax/freeDownload.php",
                              post={'method': "startTimer", 'fileId': self.info['pattern']['ID']})

        self.check_errors()

        try:
            js_file   = self.load("http://nitroflare.com/js/downloadFree.js?v=1.0.1")
            var_time  = re.search("var time = (\\d+);", js_file)
            wait_time = int(var_time.groups()[0])

        except Exception:
            wait_time = 60

        self.wait(wait_time)

        recaptcha = ReCaptcha(self)
        response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)

        self.html = self.load("http://nitroflare.com/ajax/freeDownload.php",
                              post={'method'                   : "fetchDownload",
                                    'recaptcha_challenge_field': challenge,
                                    'recaptcha_response_field' : response})

        return super(NitroflareCom, self).handle_free(pyfile)
