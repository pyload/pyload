# -*- coding: utf-8 -*-
#
# Test links:
# http://filer.net/get/ivgf5ztw53et3ogd
# http://filer.net/get/hgo14gzcng3scbvv

import pycurl
import re

from urlparse import urljoin

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FilerNet(SimpleHoster):
    __name__    = "FilerNet"
    __type__    = "hoster"
    __version__ = "0.12"

    __pattern__ = r'https?://(?:www\.)?filer\.net/get/\w+'

    __description__ = """Filer.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


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

            #@NOTE: Work-around for v0.4.9 just_header issue
            #@TODO: Check for v0.4.10
            self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 0)
            self.load(self.pyfile.url, post={'recaptcha_challenge_field': challenge,
                                             'recaptcha_response_field' : response,
                                             'hash'                     : inputs['hash']})
            self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 1)

            if 'location' in self.req.http.header.lower():
                self.link = re.search(r'location: (\S+)', self.req.http.header, re.I).group(1)
                self.correctCaptcha()
                break
            else:
                self.invalidCaptcha()


    def downloadLink(self, link):
        if link and isinstance(link, basestring):
            self.download(urljoin("http://filer.net/", link), disposition=True)


getInfo = create_getInfo(FilerNet)
