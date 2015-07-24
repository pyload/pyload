# -*- coding: utf-8 -*-
#
# Test links:
# http://uploadhero.co/dl/wQBRAVSM

import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UploadheroCom(SimpleHoster):
    __name__    = "UploadheroCom"
    __type__    = "hoster"
    __version__ = "0.19"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?uploadhero\.com?/dl/\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """UploadHero.co plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mcmyst", "mcmyst@hotmail.fr"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'<div class="nom_de_fichier">(?P<N>.+?)<'
    SIZE_PATTERN    = r'>Filesize: </span><strong>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'<p class="titre_dl_2">'

    COOKIES = [("uploadhero.co", "lang", "en")]

    IP_BLOCKED_PATTERN = r'href="(/lightbox_block_download\.php\?min=.+?)"'
    IP_WAIT_PATTERN    = r'<span id="minutes">(\d+)</span>.*\s*<span id="seconds">(\d+)</span>'

    CAPTCHA_PATTERN = r'"(/captchadl\.php\?\w+)"'

    LINK_FREE_PATTERN    = r'var magicomfg = \'<a href="(.+?)"|"(http://storage\d+\.uploadhero\.co.+?)"'
    LINK_PREMIUM_PATTERN = r'<a href="(.+?)" id="downloadnow"'


    def handle_free(self, pyfile):
        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m is None:
            self.error(_("Captcha not found"))

        captcha = self.captcha.decrypt(urlparse.urljoin("http://uploadhero.co", m.group(1)))

        self.html = self.load(pyfile.url,
                              get={'code': captcha})

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m:
            self.link = m.group(1) or m.group(2)
            self.wait(50)


    def check_errors(self):
        m = re.search(self.IP_BLOCKED_PATTERN, self.html)
        if m:
            self.html = self.load(urlparse.urljoin("http://uploadhero.co", m.group(1)))

            m = re.search(self.IP_WAIT_PATTERN, self.html)
            wait_time = (int(m.group(1)) * 60 + int(m.group(2))) if m else 5 * 60
            self.wait(wait_time, True)
            self.retry()

        return super(UploadheroCom, self).check_errors()


getInfo = create_getInfo(UploadheroCom)
