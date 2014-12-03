# -*- coding: utf-8 -*-

import re

from urlparse import urljoin, urlparse

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import _isDirectLink, SimpleHoster, create_getInfo


class Keep2shareCc(SimpleHoster):
    __name__    = "Keep2shareCc"
    __type__    = "hoster"
    __version__ = "0.16"

    __pattern__ = r'https?://(?:www\.)?(keep2share|k2s|keep2s)\.cc/file/(?P<ID>\w+)'

    __description__ = """Keep2share.cc hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(__pattern__ + ".*", "http://k2s.cc/file/\g<ID>")]

    CONTENT_DISPOSITION = True

    NAME_PATTERN = r'File: <span>(?P<N>.+)</span>'
    SIZE_PATTERN = r'Size: (?P<S>[^<]+)</div>'

    OFFLINE_PATTERN      = r'File not found or deleted|Sorry, this file is blocked or deleted|Error 404'
    TEMP_OFFLINE_PATTERN = r'Downloading blocked due to'

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'"([^"]+url.html?file=.+?)"|window\.location\.href = \'(.+?)\';'

    CAPTCHA_PATTERN = r'src="(/file/captcha\.html.+?)"'

    WAIT_PATTERN         = r'Please wait ([\d:]+) to download this file'
    TEMP_ERROR_PATTERN   = r'>\s*(Download count files exceed|Traffic limit exceed|Free account does not allow to download more than one file at the same time)'
    ERROR_PATTERN        = r'>\s*(Free user can\'t download large files|You no can access to this file|This download available only for premium users|This is private file)'


    def checkErrors(self):
        m = re.search(self.TEMP_ERROR_PATTERN, self.html)
        if m:
            self.info['error'] = m.group(1)
            self.wantReconnect = True
            self.retry(wait_time=30 * 60, reason=m.group(0))

        m = re.search(self.ERROR_PATTERN, self.html)
        if m:
            e = self.info['error'] = m.group(1)
            self.error(e)

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.logDebug("Hoster told us to wait for %s" % m.group(1))

            # string to time convert courtesy of https://stackoverflow.com/questions/10663720
            ftr = [3600, 60, 1]
            wait_time = sum([a * b for a, b in zip(ftr, map(int, m.group(1).split(':')))])

            self.wantReconnect = True
            self.retry(wait_time=wait_time, reason="Please wait to download this file")

        self.info.pop('error', None)


    def handleFree(self):
        self.fid  = re.search(r'<input type="hidden" name="slow_id" value="([^"]+)">', self.html).group(1)
        self.html = self.load(self.pyfile.url, post={'yt0': '', 'slow_id': self.fid})

        self.checkErrors()

        m = re.search(self.LINK_FREE_PATTERN, self.html)

        if m is None:
            self.handleCaptcha()

            self.wait(30)

            self.html = self.load(self.pyfile.url, post={'uniqueId': self.fid, 'free': 1})

            self.checkErrors()

            m = re.search(self.LINK_FREE_PATTERN, self.html)
            if m is None:
                self.error(_("LINK_FREE_PATTERN not found"))

        self.link = self._getDownloadLink(m.group(1))


    def handlePremium(self):
        super(Keep2shareCc, self).handlePremium()
        if self.link:
            self.link = self._getDownloadLink(self.link)


    def handleCaptcha(self):
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            post_data = {'free'               : 1,
                         'freeDownloadRequest': 1,
                         'uniqueId'           : self.fid,
                         'yt0'                : ''}

            m = re.search(self.CAPTCHA_PATTERN, self.html)
            if m:
                captcha_url = urljoin(self.base, m.group(1))
                post_data['CaptchaForm[code]'] = self.decryptCaptcha(captcha_url)
            else:
                challenge, response = recaptcha.challenge()
                post_data.update({'recaptcha_challenge_field': challenge,
                                  'recaptcha_response_field' : response})

            self.html = self.load(self.pyfile.url, post=post_data)

            if 'recaptcha' not in self.html:
                self.correctCaptcha()
                break
            else:
                self.invalidCaptcha()
        else:
            self.fail(_("All captcha attempts failed"))


    def _getDownloadLink(self, url):
        p = urlparse(self.pyfile.url)
        base = "%s://%s" % (p.scheme, p.netloc)
        link = _isDirectLink(self, url, self.premium)
        return urljoin(base, link) if link else ""


getInfo = create_getInfo(Keep2shareCc)
