# -*- coding: utf-8 -*-

import random
import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster


class NarodRu(SimpleHoster):
    __name__    = "NarodRu"
    __type__    = "hoster"
    __version__ = "0.16"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?narod(\.yandex)?\.ru/(disk|start/\d+\.\w+\-narod\.yandex\.ru)/(?P<ID>\d+)/.+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Narod.ru hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<dt class="name">(?:<.*?>)*(?P<N>.+?)</dt>'
    SIZE_PATTERN = r'<dd class="size">(?P<S>\d.*?)</dd>'
    OFFLINE_PATTERN = r'<title>404</title>|Файл удален с сервиса|Закончился срок хранения файла\.'

    SIZE_REPLACEMENTS = [(u'КБ', 'KB'), (u'МБ', 'MB'), (u'ГБ', 'GB')]
    URL_REPLACEMENTS = [("narod.yandex.ru/", "narod.ru/"),
                        (r'/start/\d+\.\w+\-narod\.yandex\.ru/(\d{6,15})/\w+/(\w+)', r'/disk/\1/\2')]

    CAPTCHA_PATTERN = r'<number url="(.*?)">(\w+)</number>'
    LINK_FREE_PATTERN = r'<a class="h-link" rel="yandex_bar" href="(.+?)">'


    def handle_free(self, pyfile):
        self.data = self.load('http://narod.ru/disk/getcapchaxml/?rnd=%d' % int(random.random() * 777))

        m = re.search(self.CAPTCHA_PATTERN, self.data)
        if m is None:
            self.error(_("Captcha"))

        post_data = {'action': "sendcapcha"}
        captcha_url, post_data['key'] = m.groups()
        post_data['rep'] = self.captcha.decrypt(captcha_url)

        self.data = self.load(pyfile.url, post=post_data)

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.captcha.correct()
            self.link = urlparse.urljoin("http://narod.ru/", m.group(1))

        elif u'<b class="error-msg"><strong>Ошиблись?</strong>' in self.data:
            self.retry_captcha()
