# -*- coding: utf-8 -*-

import re

from random import random

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class NarodRu(SimpleHoster):
    __name__ = "NarodRu"
    __type__ = "hoster"
    __version__ = "0.1"

    __pattern__ = r'http://(?:www\.)?narod(\.yandex)?\.ru/(disk|start/[0-9]+\.\w+-narod\.yandex\.ru)/(?P<ID>\d+)/.+'

    __description__ = """Narod.ru hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<dt class="name">(?:<[^<]*>)*(?P<N>[^<]+)</dt>'
    FILE_SIZE_PATTERN = r'<dd class="size">(?P<S>\d[^<]*)</dd>'
    OFFLINE_PATTERN = r'<title>404</title>|Файл удален с сервиса|Закончился срок хранения файла\.'

    FILE_SIZE_REPLACEMENTS = [(u'КБ', 'KB'), (u'МБ', 'MB'), (u'ГБ', 'GB')]
    FILE_URL_REPLACEMENTS = [("narod.yandex.ru/", "narod.ru/"),
                             (r"/start/[0-9]+\.\w+-narod\.yandex\.ru/([0-9]{6,15})/\w+/(\w+)", r"/disk/\1/\2")]

    CAPTCHA_PATTERN = r'<number url="(.*?)">(\w+)</number>'
    LINK_PATTERN = r'<a class="h-link" rel="yandex_bar" href="(.+?)">'


    def handleFree(self):
        for _ in xrange(5):
            self.html = self.load('http://narod.ru/disk/getcapchaxml/?rnd=%d' % int(random() * 777))
            m = re.search(self.CAPTCHA_PATTERN, self.html)
            if m is None:
                self.parseError('Captcha')
            post_data = {"action": "sendcapcha"}
            captcha_url, post_data['key'] = m.groups()
            post_data['rep'] = self.decryptCaptcha(captcha_url)

            self.html = self.load(self.pyfile.url, post=post_data, decode=True)
            m = re.search(self.LINK_PATTERN, self.html)
            if m:
                url = 'http://narod.ru' + m.group(1)
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
