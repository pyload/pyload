# -*- coding: utf-8 -*-
#
# Note:
#   Right now premium support is not added
#   Thus, any file that require premium support
#   cannot be downloaded. Only the file that is free to
#   download can be downloaded.

import re

from module.common.json_layer import json_loads
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster


class NitroflareCom(SimpleHoster):
    __name__    = "NitroflareCom"
    __type__    = "hoster"
    __version__ = "0.07"

    __pattern__ = r'https?://(?:www\.)?nitroflare\.com/view/(?P<ID>[\w^_]+)'

    __description__ = """Nitroflare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("sahil", "sahilshekhawat01@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]

    # URL_REPLACEMENTS = [("http://", "https://")]

    INFO_PATTERN    = r'title="(?P<N>.+?)".+>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File doesn\'t exist'

    LINK_FREE_PATTERN = r'(https?://[\w\-]+\.nitroflare\.com/.+?)"'

    RECAPTCHA_KEY = "6Lenx_USAAAAAF5L1pmTWvWcH73dipAEzNnmNLgy"

    PREMIUM_ONLY_PATTERN = r'This file is available with Premium only'
    WAIT_PATTERN         = r'You have to wait .+?<'
    ERROR_PATTERN        = r'downloading is not possible'


    def checkErrors(self):
        if not self.html:
            return

        if not self.premium and re.search(self.PREMIUM_ONLY_PATTERN, self.html):
            self.fail(_("Link require a premium account to be handled"))

        elif hasattr(self, 'WAIT_PATTERN'):
            m = re.search(self.WAIT_PATTERN, self.html)
            if m:
                wait_time = sum([int(v) * {"hr": 3600, "hour": 3600, "min": 60, "sec": 1}[u.lower()] for v, u in
                                 re.findall(r'(\d+)\s*(hr|hour|min|sec)', m.group(0), re.I)])
                self.wait(wait_time, wait_time > 300)
                return

        elif hasattr(self, 'ERROR_PATTERN'):
            m = re.search(self.ERROR_PATTERN, self.html)
            if m:
                errmsg = self.info['error'] = m.group(1)
                self.error(errmsg)

        self.info.pop('error', None)


    def handleFree(self, pyfile):
        # used here to load the cookies which will be required later
        self.load(pyfile.url, post={'goToFreePage': ""})

        self.html = self.load("http://nitroflare.com/ajax/freeDownload.php",
                              post={'method': "startTimer", 'fileId': self.info['pattern']['ID']})[4:]

        self.checkErrors()

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
                                    'recaptcha_response_field' : response})[3:]

        self.logDebug(self.html)

        if "The captcha wasn't entered correctly" in self.html:
            return

        if "You have to fill the captcha" in self.html:
            return

        self.link = re.search(self.LINK_FREE_PATTERN, self.html)
