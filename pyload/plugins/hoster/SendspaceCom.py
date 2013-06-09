# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class SendspaceCom(SimpleHoster):
    __name__ = "SendspaceCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?sendspace.com/file/.*"
    __version__ = "0.13"
    __description__ = """sendspace.com plugin - free only"""
    __author_name__ = ("zoidberg")

    DOWNLOAD_URL_PATTERN = r'<a id="download_button" href="([^"]+)"'
    FILE_NAME_PATTERN = r'<h2 class="bgray">\s*<(?:b|strong)>(?P<N>[^<]+)</'
    FILE_SIZE_PATTERN = r'<div class="file_description reverse margin_center">\s*<b>File Size:</b>\s*(?P<S>[0-9.]+)(?P<U>[kKMG])i?B\s*</div>'
    FILE_OFFLINE_PATTERN = r'<div class="msg error" style="cursor: default">Sorry, the file you requested is not available.</div>'
    CAPTCHA_PATTERN = r'<td><img src="(/captchas/captcha.php?captcha=([^"]+))"></td>'
    USER_CAPTCHA_PATTERN = r'<td><img src="/captchas/captcha.php?user=([^"]+))"></td>'
        
    def handleFree(self):
        params = {}
        for i in range(3):
            found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
            if found:
                if params.has_key('captcha_hash'): self.correctCaptcha()
                download_url = found.group(1)
                break

            found = re.search(self.CAPTCHA_PATTERN, self.html)
            if found:
                if params.has_key('captcha_hash'): self.invalidCaptcha()
                captcha_url1 = "http://www.sendspace.com/" + found.group(1)
                found = re.search(self.USER_CAPTCHA_PATTERN, self.html)
                captcha_url2 = "http://www.sendspace.com/" + found.group(1)
                params = {'captcha_hash' : found.group(2),
                          'captcha_submit': 'Verify',
                          'captcha_answer': self.decryptCaptcha(captcha_url1) + " " + self.decryptCaptcha(captcha_url2)
                         }
            else:
                params = {'download': "Regular Download"}

            self.logDebug(params)
            self.html = self.load(self.pyfile.url, post = params)
        else:
            self.fail("Download link not found")

        self.logDebug("Download URL: %s" % download_url)
        self.download(download_url)

create_getInfo(SendspaceCom)