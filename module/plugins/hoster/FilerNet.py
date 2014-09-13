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
    __version__ = "0.03"

    __pattern__ = r'https?://(?:www\.)?filer\.net/get/(\w+)'

    __description__ = """Filer.net hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    FILE_INFO_PATTERN = r'<h1 class="page-header">Free Download (?P<N>\S+) <small>(?P<S>[\w.]+) (?P<U>\w+)</small></h1>'
    OFFLINE_PATTERN = r'Nicht gefunden'
    RECAPTCHA_KEY = "6LcFctISAAAAAAgaeHgyqhNecGJJRnxV1m_vAz3V"
    LINK_PATTERN = r'href="([^"]+)">Get download</a>'


    def process(self, pyfile):
        if self.premium and (not self.SH_CHECK_TRAFFIC or self.checkTrafficLeft()):
            self.handlePremium()
        else:
            self.handleFree()

    def handleFree(self):
        self.req.setOption("timeout", 120)
        self.html = self.load(self.pyfile.url, decode=not self.SH_BROKEN_ENCODING, cookies=self.SH_COOKIES)

        # Wait between downloads
        m = re.search(r'musst du <span id="time">(\d+)</span> Sekunden warten', self.html)
        if m:
            waittime = int(m.group(1))
            self.retry(3, waittime, "Wait between free downloads")

        self.getFileInfo()

        self.html = self.load(self.pyfile.url, decode=True)

        inputs = self.parseHtmlForm(input_names='token')[1]
        if 'token' not in inputs:
            self.parseError('Unable to detect token')
        token = inputs['token']
        self.logDebug('Token: ' + token)

        self.html = self.load(self.pyfile.url, post={'token': token}, decode=True)

        inputs = self.parseHtmlForm(input_names='hash')[1]
        if 'hash' not in inputs:
            self.parseError('Unable to detect hash')
        hash_data = inputs['hash']
        self.logDebug('Hash: ' + hash_data)

        downloadURL = r''
        recaptcha = ReCaptcha(self)
        for _ in xrange(5):
            challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
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
                self.logInfo('Wrong captcha')
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
                self.parseError("Unable to detect direct link, try to enable 'Direct download' in your user settings")
            dl = 'http://filer.net' + m.group(1)

        self.logDebug('Direct link: ' + dl)
        self.download(dl, disposition=True)


getInfo = create_getInfo(FilerNet)
