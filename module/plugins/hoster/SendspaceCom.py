# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SendspaceCom(SimpleHoster):
    __name__ = "SendspaceCom"
    __type__ = "hoster"
    __version__ = "0.13"

    __pattern__ = r'http://(?:www\.)?sendspace.com/file/.*'

    __description__ = """Sendspace.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<h2 class="bgray">\s*<(?:b|strong)>(?P<N>[^<]+)</'
    FILE_SIZE_PATTERN = r'<div class="file_description reverse margin_center">\s*<b>File Size:</b>\s*(?P<S>[0-9.]+)(?P<U>[kKMG])i?B\s*</div>'
    OFFLINE_PATTERN = r'<div class="msg error" style="cursor: default">Sorry, the file you requested is not available.</div>'

    LINK_PATTERN = r'<a id="download_button" href="([^"]+)"'
    CAPTCHA_PATTERN = r'<td><img src="(/captchas/captcha.php?captcha=([^"]+))"></td>'
    USER_CAPTCHA_PATTERN = r'<td><img src="/captchas/captcha.php?user=([^"]+))"></td>'


    def handleFree(self):
        params = {}
        for _ in xrange(3):
            m = re.search(self.LINK_PATTERN, self.html)
            if m:
                if 'captcha_hash' in params:
                    self.correctCaptcha()
                download_url = m.group(1)
                break

            m = re.search(self.CAPTCHA_PATTERN, self.html)
            if m:
                if 'captcha_hash' in params:
                    self.invalidCaptcha()
                captcha_url1 = "http://www.sendspace.com/" + m.group(1)
                m = re.search(self.USER_CAPTCHA_PATTERN, self.html)
                captcha_url2 = "http://www.sendspace.com/" + m.group(1)
                params = {'captcha_hash': m.group(2),
                          'captcha_submit': 'Verify',
                          'captcha_answer': self.decryptCaptcha(captcha_url1) + " " + self.decryptCaptcha(captcha_url2)}
            else:
                params = {'download': "Regular Download"}

            self.logDebug(params)
            self.html = self.load(self.pyfile.url, post=params)
        else:
            self.fail("Download link not found")

        self.logDebug("Download URL: %s" % download_url)
        self.download(download_url)


create_getInfo(SendspaceCom)
