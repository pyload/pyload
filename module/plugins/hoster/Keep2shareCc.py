# -*- coding: utf-8 -*-

import re

from urlparse import urlparse, urljoin

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class Keep2shareCc(SimpleHoster):
    __name__    = "Keep2shareCc"
    __type__    = "hoster"
    __version__ = "0.14"

    __pattern__ = r'https?://(?:www\.)?(keep2share|k2s|keep2s)\.cc/file/(?P<ID>\w+)'

    __description__ = """Keep2share.cc hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'File: <span>(?P<N>.+)</span>'
    SIZE_PATTERN = r'Size: (?P<S>[^<]+)</div>'
    OFFLINE_PATTERN = r'File not found or deleted|Sorry, this file is blocked or deleted|Error 404'

    LINK_PATTERN = r'To download this file with slow speed, use <a href="([^"]+)">this link</a>'
    CAPTCHA_PATTERN = r'src="(/file/captcha\.html.+?)"'
    WAIT_PATTERN = r'Please wait ([\d:]+) to download this file'
    MULTIDL_ERROR = r'Free account does not allow to download more than one file at the same time'


    def handleFree(self):
        self.sanitize_url()
        self.html = self.load(self.pyfile.url)

        self.fid = re.search(r'<input type="hidden" name="slow_id" value="([^"]+)">', self.html).group(1)
        self.html = self.load(self.pyfile.url, post={'yt0': '', 'slow_id': self.fid})

        m = re.search(r"function download\(\){.*window\.location\.href = '([^']+)';", self.html, re.S)
        if m:  # Direct mode
            self.startDownload(m.group(1))
        else:
            self.handleCaptcha()

            self.wait(30)

            self.html = self.load(self.pyfile.url, post={'uniqueId': self.fid, 'free': 1})

            m = re.search(self.WAIT_PATTERN, self.html)
            if m:
                self.logDebug("Hoster told us to wait for %s" % m.group(1))
                # string to time convert courtesy of https://stackoverflow.com/questions/10663720
                ftr = [3600, 60, 1]
                wait_time = sum([a * b for a, b in zip(ftr, map(int, m.group(1).split(':')))])
                self.wait(wait_time, True)
                self.retry()

            m = re.search(self.MULTIDL_ERROR, self.html)
            if m:
                # if someone is already downloading on our line, wait 30min and retry
                self.logDebug("Already downloading, waiting for 30 minutes")
                self.wait(30 * 60, True)
                self.retry()

            m = re.search(self.LINK_PATTERN, self.html)
            if m is None:
                self.error(_("LINK_PATTERN not found"))
            self.startDownload(m.group(1))


    def handleCaptcha(self):
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            post_data = {'free': 1,
                         'freeDownloadRequest': 1,
                         'uniqueId': self.fid,
                         'yt0': ''}

            m = re.search(self.CAPTCHA_PATTERN, self.html)
            if m:
                captcha_url = urljoin(self.base_url, m.group(1))
                post_data['CaptchaForm[code]'] = self.decryptCaptcha(captcha_url)
            else:
                challenge, response = recaptcha.challenge()
                post_data.update({'recaptcha_challenge_field': challenge,
                                  'recaptcha_response_field': response})

            self.html = self.load(self.pyfile.url, post=post_data)

            if 'recaptcha' not in self.html:
                self.correctCaptcha()
                break
            else:
                self.invalidCaptcha()
        else:
            self.fail(_("All captcha attempts failed"))


    def startDownload(self, url):
        d = urljoin(self.base_url, url)
        self.logDebug("Direct Link: " + d)
        self.download(d, disposition=True)


    def sanitize_url(self):
        header = self.load(self.pyfile.url, just_header=True)
        if 'location' in header:
            self.pyfile.url = header['location']
        p = urlparse(self.pyfile.url)
        self.base_url = "%s://%s" % (p.scheme, p.hostname)


getInfo = create_getInfo(Keep2shareCc)
