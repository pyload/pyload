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
    __name__ = "FilerNet"
    __type__ = "hoster"
    __version__ = "0.07"

    __pattern__ = r'https?://(?:www\.)?filer\.net/get/\w+'

    __description__ = """Filer.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    FILE_INFO_PATTERN = r'<h1 class="page-header">Free Download (?P<N>\S+) <small>(?P<S>[\w.]+) (?P<U>[\w^_]+)</small></h1>'
    OFFLINE_PATTERN = r'Nicht gefunden'

    LINK_PATTERN = r'href="([^"]+)">Get download</a>'


    def handleFree(self):
        # Wait between downloads
        m = re.search(r'musst du <span id="time">(\d+)</span> Sekunden warten', self.html)
        if m:
            self.retry(wait_time=int(m.group(1)), reason="Wait between free downloads")

        self.html = self.load(self.pyfile.url, decode=True)

        inputs = self.parseHtmlForm(input_names='token')[1]
        if 'token' not in inputs:
            self.error("Unable to detect token")
        token = inputs['token']
        self.logDebug("Token: " + token)

        self.html = self.load(self.pyfile.url, post={'token': token}, decode=True)

        inputs = self.parseHtmlForm(input_names='hash')[1]
        if 'hash' not in inputs:
            self.error("Unable to detect hash")
        hash_data = inputs['hash']
        self.logDebug("Hash: " + hash_data)

        downloadURL = r''
        recaptcha = ReCaptcha(self)

        for _ in xrange(5):
            challenge, response = recaptcha.challenge()
            post_data = {'recaptcha_challenge_field': challenge,
                         'recaptcha_response_field': response,
                         'hash': hash_data}

            # Workaround for 0.4.9 just_header issue. In 0.5 clean the code using just_header
            self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 0)
            self.load(self.pyfile.url, post=post_data)
            self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 1)

            if 'location' in self.req.http.header.lower():
                location = re.search(r'location: (\S+)', self.req.http.header, re.I).group(1)
                downloadURL = urljoin('http://filer.net', location)
                self.correctCaptcha()
                break
            else:
                self.invalidCaptcha()

        if not downloadURL:
            self.fail("No Download url retrieved/all captcha attempts failed")

        self.download(downloadURL, disposition=True)


    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header=True)
        if 'location' in header:  # Direct Download ON
            dl = self.pyfile.url
        else:  # Direct Download OFF
            html = self.load(self.pyfile.url)
            m = re.search(self.LINK_PATTERN, html)
            if m is None:
                self.error("Unable to detect direct link, try to enable 'Direct download' in your user settings")
            dl = 'http://filer.net' + m.group(1)

        self.logDebug("Direct link: " + dl)
        self.download(dl, disposition=True)


getInfo = create_getInfo(FilerNet)
