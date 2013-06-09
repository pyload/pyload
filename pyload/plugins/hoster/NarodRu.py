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
from random import random
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class NarodRu(SimpleHoster):
    __name__ = "NarodRu"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?narod(\.yandex)?\.ru/(disk|start/[0-9]+\.\w+-narod\.yandex\.ru)/(?P<ID>\d+)/.+"
    __version__ = "0.1"
    __description__ = """Narod.ru"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<dt class="name">(?:<[^<]*>)*(?P<N>[^<]+)</dt>'
    FILE_SIZE_PATTERN = r'<dd class="size">(?P<S>\d[^<]*)</dd>'
    FILE_OFFLINE_PATTERN = r'<title>404</title>|Файл удален с сервиса|Закончился срок хранения файла\.'
       
    FILE_SIZE_REPLACEMENTS = [(u'КБ', 'KB'), (u'МБ', 'MB'), (u'ГБ', 'GB')]
    FILE_URL_REPLACEMENTS = [("narod.yandex.ru/", "narod.ru/"), (r"/start/[0-9]+\.\w+-narod\.yandex\.ru/([0-9]{6,15})/\w+/(\w+)", r"/disk/\1/\2")]
    
    CAPTCHA_PATTERN = r'<number url="(.*?)">(\w+)</number>'
    DOWNLOAD_LINK_PATTERN = r'<a class="h-link" rel="yandex_bar" href="(.+?)">'

    def handleFree(self):
        for i in range(5):
            self.html = self.load('http://narod.ru/disk/getcapchaxml/?rnd=%d' % int(random() * 777))
            found = re.search(self.CAPTCHA_PATTERN, self.html)
            if not found: self.parseError('Captcha')
            post_data = {"action": "sendcapcha"}
            captcha_url, post_data['key'] = found.groups()
            post_data['rep'] = self.decryptCaptcha(captcha_url)
            
            self.html = self.load(self.pyfile.url, post = post_data, decode = True)
            found = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
            if found:
                url = 'http://narod.ru' + found.group(1)
                self.correctCaptcha()
                break
            elif u'<b class="error-msg"><strong>Ошиблись?</strong>' in self.html:
                self.invalidCaptcha()
            else:
                self.parseError('Download link')
        else:
            self.fail("No valid captcha code entered")
                       
        self.logDebug('Download link: ' + url)
        self.download(url)        

getInfo = create_getInfo(NarodRu)