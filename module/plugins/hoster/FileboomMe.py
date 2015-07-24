# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileboomMe(SimpleHoster):
    __name__    = "FileboomMe"
    __type__    = "hoster"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'https?://f(?:ile)?boom\.me/file/(?P<ID>\w+)'

    __description__ = """Fileboom.me hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", None)]


    NAME_PATTERN    = r'<i class="icon-download"></i>\s*(?P<N>.+?)\s*<'
    SIZE_PATTERN    = r'File size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>This file is no longer available'

    WAIT_PATTERN = r'<div class="tik-tak">([\d:]+)'
    LINK_PATTERN = r'/file/url\.html\?file=\w+'

    CAPTCHA_PATTERN = r'<img .* src="(/file/captcha.html\?v=\w+)"'


    def setup(self):
        self.resume_download = True
        self.multiDL        = False
        self.chunk_limit     = 1


    def handle_free(self, pyfile):
        post_url = urljoin(pyfile.url, "/file/" + self.info['pattern']['ID'])

        m = re.search(r'data-slow-id="(\w+)"', self.html)
        if m:
            self.html = self.load(post_url,
                                  post={'slow_id': m.group(1)})

            m = re.search(self.LINK_PATTERN, self.html)
            if m:
                self.link = urljoin(pyfile.url, m.group(0))

            else:
                for _i in xrange(5):
                    m = re.search(r'<input type="hidden" name="uniqueId" value="(\w+)">', self.html)
                    if m:
                        uniqueId = m.group(1)

                        m = re.search(self.CAPTCHA_PATTERN, self.html)
                        if m:
                            captcha = self.captcha.decrypt(urljoin(pyfile.url, m.group(1)))

                            self.html = self.load(post_url,
                                                  post={'CaptchaForm[code]'  : captcha,
                                                        'free'               : 1,
                                                        'freeDownloadRequest': 1,
                                                        'uniqueId'           : uniqueId})

                            if 'The verification code is incorrect' in self.html:
                                self.captcha.invalid()

                            else:
                                self.check_errors()

                                self.html = self.load(post_url,
                                                      post={'free'    : 1,
                                                            'uniqueId': uniqueId})

                                m = re.search(self.LINK_PATTERN, self.html)
                                if m:
                                    self.link = urljoin(pyfile.url, m.group(0))

                                else:
                                    self.captcha.invalid()

                                break

                        else:
                            self.fail(_("Captcha not found"))

                    else:
                        m = re.search(r'>\s*Please wait ([\d:]+)', self.html)
                        if m:
                            wait_time = 0
                            for v in re.findall(r'(\d+)', m.group(1), re.I):
                                wait_time = 60 * wait_time + int(v)
                            self.wait(wait_time)
                            self.retry()
                        break

                else:
                    self.fail(_("Invalid captcha"))


getInfo = create_getInfo(FileboomMe)
