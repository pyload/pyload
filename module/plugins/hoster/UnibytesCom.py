# -*- coding: utf-8 -*-

import pycurl
import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UnibytesCom(SimpleHoster):
    __name__    = "UnibytesCom"
    __type__    = "hoster"
    __version__ = "0.16"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?unibytes\.com/[\w\- .]{11}B'
    __config__  = [("activated", "bool", "Activated", True),
                   ("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """UniBytes.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    PLUGIN_DOMAIN = "unibytes.com"

    INFO_PATTERN = r'<span[^>]*?id="fileName".*?>(?P<N>[^>]+)</span>\s*\((?P<S>\d.*?)\)'

    WAIT_PATTERN = r'Wait for <span id="slowRest">(\d+)</span> sec'
    LINK_FREE_PATTERN = r'<a href="(.+?)">Download</a>'


    def handle_free(self, pyfile):
        domain = "http://www.%s/" % self.PLUGIN_DOMAIN
        action, post_data = self.parse_html_form('id="startForm"')

        for _i in xrange(3):
            self.log_debug(action, post_data)
            self.html = self.load(urlparse.urljoin(domain, action),
                                  post=post_data,
                                  redirect=False)

            m = re.search(r'location:\s*(\S+)', self.req.http.header, re.I)
            if m is not None:
                self.link = m.group(1)
                break

            if '>Somebody else is already downloading using your IP-address<' in self.html:
                self.wait(10 * 60, True)
                self.restart()

            if post_data['step'] == "last":
                m = re.search(self.LINK_FREE_PATTERN, self.html)
                if m is not None:
                    self.captcha.correct()
                    self.link = m.group(1)
                    break
                else:
                    self.retry_captcha()

            last_step = post_data['step']
            action, post_data = self.parse_html_form('id="stepForm"')

            if last_step == "timer":
                m = re.search(self.WAIT_PATTERN, self.html)
                self.wait(m.group(1) if m else 60, False)

            elif last_step in ("captcha", "last"):
                post_data['captcha'] = self.captcha.decrypt(urlparse.urljoin(domain, "captcha.jpg"))


getInfo = create_getInfo(UnibytesCom)
