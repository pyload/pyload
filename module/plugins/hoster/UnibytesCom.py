# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from pycurl import FOLLOWLOCATION

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UnibytesCom(SimpleHoster):
    __name__    = "UnibytesCom"
    __type__    = "hoster"
    __version__ = "0.12"

    __pattern__ = r'https?://(?:www\.)?unibytes\.com/[\w .-]{11}B'

    __description__ = """UniBytes.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "unibytes.com"

    INFO_PATTERN = r'<span[^>]*?id="fileName"[^>]*>(?P<N>[^>]+)</span>\s*\((?P<S>\d.*?)\)'

    WAIT_PATTERN = r'Wait for <span id="slowRest">(\d+)</span> sec'
    LINK_FREE_PATTERN = r'<a href="([^"]+)">Download</a>'


    def handleFree(self, pyfile):
        domain            = "http://www.%s/" % self.HOSTER_DOMAIN
        action, post_data = self.parseHtmlForm('id="startForm"')

        self.req.http.c.setopt(FOLLOWLOCATION, 0)

        for _i in xrange(8):
            self.logDebug(action, post_data)
            self.html = self.load(urljoin(domain, action), post=post_data)

            m = re.search(r'location:\s*(\S+)', self.req.http.header, re.I)
            if m:
                url = m.group(1)
                break

            if '>Somebody else is already downloading using your IP-address<' in self.html:
                self.wait(10 * 60, True)
                self.retry()

            if post_data['step'] == 'last':
                m = re.search(self.LINK_FREE_PATTERN, self.html)
                if m:
                    url = m.group(1)
                    self.correctCaptcha()
                    break
                else:
                    self.invalidCaptcha()

            last_step = post_data['step']
            action, post_data = self.parseHtmlForm('id="stepForm"')

            if last_step == 'timer':
                m = re.search(self.WAIT_PATTERN, self.html)
                self.wait(int(m.group(1)) if m else 60, False)

            elif last_step in ("captcha", "last"):
                post_data['captcha'] = self.decryptCaptcha(urljoin(domain, "/captcha.jpg"))

        else:
            self.fail(_("No valid captcha code entered"))

        self.req.http.c.setopt(FOLLOWLOCATION, 1)

        self.download(url)


getInfo = create_getInfo(UnibytesCom)
