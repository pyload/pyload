# -*- coding: utf-8 -*-
#
# Test links:
# http://k2s.cc/file/55fb73e1c00c5/random.bin

import re

from urlparse import urlparse, urljoin

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class Keep2shareCC(SimpleHoster):
    __name__ = "Keep2shareCC"
    __type__ = "hoster"
    __version__ = "0.10"

    __pattern__ = r'https?://(?:www\.)?(keep2share|k2s|keep2s)\.cc/file/(?P<ID>\w+)'

    __description__ = """Keep2share.cc hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    FILE_NAME_PATTERN = r'File: <span>(?P<N>.+)</span>'
    FILE_SIZE_PATTERN = r'Size: (?P<S>[^<]+)</div>'
    OFFLINE_PATTERN = r'File not found or deleted|Sorry, this file is blocked or deleted|Error 404'

    LINK_PATTERN = r'To download this file with slow speed, use <a href="([^"]+)">this link</a>'
    WAIT_PATTERN = r'Please wait ([\d:]+) to download this file'
    ALREADY_DOWNLOADING_PATTERN = r'Free account does not allow to download more than one file at the same time'

    RECAPTCHA_KEY = "6LcYcN0SAAAAABtMlxKj7X0hRxOY8_2U86kI1vbb"


    def handleFree(self):
        self.sanitize_url()
        self.html = self.load(self.pyfile.url)

        self.fid = re.search(r'<input type="hidden" name="slow_id" value="([^"]+)">', self.html).group(1)
        self.html = self.load(self.pyfile.url, post={'yt0': '', 'slow_id': self.fid})

        m = re.search(r"function download\(\){.*window\.location\.href = '([^']+)';", self.html, re.DOTALL)
        if m:  # Direct mode
            self.startDownload(m.group(1))
        else:
            self.handleCaptcha()

            self.wait(30)

            self.html = self.load(self.pyfile.url, post={'uniqueId': self.fid, 'free': 1})

            m = re.search(self.WAIT_PATTERN, self.html)
            if m:
                self.logDebug('Hoster told us to wait for %s' % m.group(1))
                # string to time convert courtesy of https://stackoverflow.com/questions/10663720
                ftr = [3600, 60, 1]
                wait_time = sum([a * b for a, b in zip(ftr, map(int, m.group(1).split(':')))])
                self.wait(wait_time, reconnect=True)
                self.retry()

            m = re.search(self.ALREADY_DOWNLOADING_PATTERN, self.html)
            if m:
                # if someone is already downloading on our line, wait 30min and retry
                self.logDebug('Already downloading, waiting for 30 minutes')
                self.wait(30 * 60, reconnect=True)
                self.retry()

            m = re.search(self.LINK_PATTERN, self.html)
            if m is None:
                self.parseError("Unable to detect direct link")
            self.startDownload(m.group(1))

    def handleCaptcha(self):
        recaptcha = ReCaptcha(self)
        for _ in xrange(5):
            challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
            post_data = {'recaptcha_challenge_field': challenge,
                         'recaptcha_response_field': response,
                         'CaptchaForm%5Bcode%5D': '',
                         'free': 1,
                         'freeDownloadRequest': 1,
                         'uniqueId': self.fid,
                         'yt0': ''}

            self.html = self.load(self.pyfile.url, post=post_data)

            if 'recaptcha' not in self.html:
                self.correctCaptcha()
                break
            else:
                self.logInfo('Wrong captcha')
                self.invalidCaptcha()
        else:
            self.fail("All captcha attempts failed")

    def startDownload(self, url):
        d = urljoin(self.base_url, url)
        self.logDebug('Direct Link: ' + d)
        self.download(d, disposition=True)

    def sanitize_url(self):
        header = self.load(self.pyfile.url, just_header=True)
        if 'location' in header:
            self.pyfile.url = header['location']
        p = urlparse(self.pyfile.url)
        self.base_url = "%s://%s" % (p.scheme, p.hostname)


getInfo = create_getInfo(Keep2shareCC)
