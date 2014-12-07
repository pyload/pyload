# -*- coding: utf-8 -*-
#
# Test links:
# http://filer.net/get/ivgf5ztw53et3ogd
# http://filer.net/get/hgo14gzcng3scbvv

import re

from urlparse import urljoin

from pyload.plugins.internal.CaptchaService import ReCaptcha
from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FilerNet(SimpleHoster):
    __name__    = "FilerNet"
    __type__    = "hoster"
    __version__ = "0.09"

    __pattern__ = r'https?://(?:www\.)?filer\.net/get/\w+'

    __description__ = """Filer.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")
                       ("Walter Purcaro", "vuolter@gmail.com")]


    CONTENT_DISPOSITION = True

    INFO_PATTERN    = r'<h1 class="page-header">Free Download (?P<N>\S+) <small>(?P<S>[\w.]+) (?P<U>[\w^_]+)</small></h1>'
    OFFLINE_PATTERN = r'Nicht gefunden'

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'href="([^"]+)">Get download</a>'


    def checkErrors(self):
        # Wait between downloads
        m = re.search(r'musst du <span id="time">(\d+)</span> Sekunden warten', self.html)
        if m:
            errmsg = self.info['error'] = _("Wait between free downloads")
            self.retry(wait_time=int(m.group(1)), reason=errmsg)

        self.info.pop('error', None)


    def handleFree(self):
        inputs = self.parseHtmlForm(input_names={'token': re.compile(r'.+')})[1]
        if 'token' not in inputs:
            self.error(_("Unable to detect token"))

        self.html = self.load(self.pyfile.url, post={'token': inputs['token']}, decode=True)

        inputs = self.parseHtmlForm(input_names={'hash': re.compile(r'.+')})[1]
        if 'hash' not in inputs:
            self.error(_("Unable to detect hash"))

        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            challenge, response = recaptcha.challenge()

            header = self.load(self.pyfile.url,
                               post={'recaptcha_challenge_field': challenge,
                                     'recaptcha_response_field' : response,
                                     'hash'                     : inputs['hash']})

            if 'location' in header and header['location']:
                self.correctCaptcha()
                self.link = urljoin('http://filer.net', header['location'])
                return
            else:
                self.invalidCaptcha()


    def handlePremium(self):
        super(FilerNet, self).handlePremium()
        if self.link:
            self.link = urljoin("http://filer.net/", self.link)


getInfo = create_getInfo(FilerNet)
