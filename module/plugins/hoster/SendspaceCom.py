# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SendspaceCom(SimpleHoster):
    __name__    = "SendspaceCom"
    __type__    = "hoster"
    __version__ = "0.18"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?sendspace\.com/file/\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Sendspace.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'<h2 class="bgray">\s*<(?:b|strong)>(?P<N>[^<]+)</'
    SIZE_PATTERN    = r'<div class="file_description reverse margin_center">\s*<b>File Size:</b>\s*(?P<S>[\d.,]+)(?P<U>[\w^_]+)\s*</div>'
    OFFLINE_PATTERN = r'<div class="msg error" style="cursor: default">Sorry, the file you requested is not available.</div>'

    LINK_FREE_PATTERN = r'<a id="download_button" href="(.+?)"'

    CAPTCHA_PATTERN      = r'<td><img src="(/captchas/captcha\.php?captcha=(.+?))"></td>'
    USER_CAPTCHA_PATTERN = r'<td><img src="/captchas/captcha\.php?user=(.+?))"></td>'


    def handle_free(self, pyfile):
        params = {}
        for _i in xrange(3):
            m = re.search(self.LINK_FREE_PATTERN, self.html)
            if m:
                if 'captcha_hash' in params:
                    self.captcha.correct()
                self.link = m.group(1)
                break

            m = re.search(self.CAPTCHA_PATTERN, self.html)
            if m:
                if 'captcha_hash' in params:
                    self.captcha.invalid()
                captcha_url1 = "http://www.sendspace.com/" + m.group(1)
                m = re.search(self.USER_CAPTCHA_PATTERN, self.html)
                captcha_url2 = "http://www.sendspace.com/" + m.group(1)
                params = {'captcha_hash': m.group(2),
                          'captcha_submit': 'Verify',
                          'captcha_answer': self.captcha.decrypt(captcha_url1) + " " + self.captcha.decrypt(captcha_url2)}
            else:
                params = {'download': "Regular Download"}

            self.log_debug(params)
            self.html = self.load(pyfile.url, post=params)
        else:
            self.fail(_("Download link not found"))


getInfo = create_getInfo(SendspaceCom)
