# -*- coding: utf-8 -*-

import re
import urlparse

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.SimpleHoster import SimpleHoster


class Keep2ShareCc(SimpleHoster):
    __name__ = "Keep2ShareCc"
    __type__ = "hoster"
    __version__ = "0.35"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(keep2share|k2s|keep2s)\.cc/file/(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Keep2Share.cc hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    DISPOSITION = False  # @TODO: Recheck in v0.4.10

    URL_REPLACEMENTS = [(__pattern__ + ".*", "https://keep2share.cc/file/\g<ID>?force_old=1")]

    NAME_PATTERN = r'File: <span>(?P<N>.+?)</span>'
    SIZE_PATTERN = r'Size: (?P<S>.+?)</div>'

    OFFLINE_PATTERN = r'File not found or deleted|Sorry, this file is blocked or deleted|Error 404'
    TEMP_OFFLINE_PATTERN = r'Downloading blocked due to'

    LINK_FREE_PATTERN = r'"([^"]+?url.html\?file=.+?)"|window\.location\.href = \'(.+?)\';'
    LINK_PREMIUM_PATTERN = r'window\.location\.href = \'(.+?)\';'
    UNIQUE_ID_PATTERN = r"data: {uniqueId: '(?P<uID>\w+)', free: 1}"

    CAPTCHA_PATTERN = r'src="(/file/captcha\.html.+?)"'

    WAIT_PATTERN = r'Please wait ([\d:]+) to download this file'
    TEMP_ERROR_PATTERN = r'>\s*(Download count files exceed|Traffic limit exceed|Free account does not allow to download more than one file at the same time)'
    ERROR_PATTERN = r'>\s*(Free user can\'t download large files|You no can access to this file|This download available only for premium users|This is private file)'

    def check_errors(self):
        m = re.search(self.TEMP_ERROR_PATTERN, self.data)
        if m is not None:
            self.info['error'] = m.group(1)
            self.wantReconnect = True
            self.retry(wait=30 * 60, msg=m.group(0))

        m = re.search(self.ERROR_PATTERN, self.data)
        if m is not None:
            errmsg = self.info['error'] = m.group(1)
            self.error(errmsg)

        m = re.search(self.WAIT_PATTERN, self.data)
        if m is not None:
            self.log_debug("Hoster told us to wait for %s" % m.group(1))

            #: String to time convert courtesy of https://stackoverflow.com/questions/10663720
            ftr = [3600, 60, 1]
            wait_time = sum(a * b for a, b in zip(ftr,
                                                  map(int, m.group(1).split(':'))))

            self.wantReconnect = True
            self.retry(wait=wait_time, msg="Please wait to download this file")

        self.info.pop('error', None)
        # SimpleHoster.check_errors(self)

    def handle_free(self, pyfile):
        m = re.search(r'<input type="hidden" name="slow_id" value="(.+?)">', self.data)

        if m is None:
            self.error(_("Slow-ID pattern not found"))

        self.data = self.load(pyfile.url,
                              post={'yt0': '',
                                    'slow_id': m.group(1)})

        self.check_errors()

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.handle_captcha()

            m = re.search(r'<div id="download-wait-timer".*>\s*(\d+).+?</div>', self.data)
            if m is not None:
                self.wait(m.group(1))

            # get the uniqueId from the html code
            m = re.search(self.UNIQUE_ID_PATTERN, self.data)
            if m is None:
                self.error(_("Unique-ID pattern not found"))

            self.data = self.load(pyfile.url,
                                  post={'uniqueId': m.group('uID'),
                                        'free': '1'})

            m = re.search(self.LINK_FREE_PATTERN, self.data)
            if m is None:
                self.error(_("Free download link not found"))

        # if group 1 did not match, check group 2
        self.link = m.group(1) or m.group(2)

    def handle_captcha(self):
        url, inputs = self.parse_html_form('id="captcha-form"')
        if inputs is not None:
            m = re.search(self.CAPTCHA_PATTERN, self.data)
            if m is not None:
                captcha_url = urlparse.urljoin(self.pyfile.url, m.group(1))
                inputs['CaptchaForm[code]'] = self.captcha.decrypt(captcha_url)
            else:
                self.captcha = ReCaptcha(self.pyfile)
                response, challenge = self.captcha.challenge()
                inputs.update({'recaptcha_challenge_field': challenge,
                               'recaptcha_response_field': response})

            self.data = self.load(self.fixurl(url),
                                  post=inputs)

            if 'verification code is incorrect' in self.data:
                self.retry_captcha()

            else:
                self.captcha.correct()
