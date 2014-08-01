# -*- coding: utf-8 -*-
#
# Test links:
# http://uploadhero.co/dl/wQBRAVSM

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UploadheroCom(SimpleHoster):
    __name__ = "UploadheroCom"
    __type__ = "hoster"
    __version__ = "0.15"

    __pattern__ = r'http://(?:www\.)?uploadhero\.com?/dl/\w+'

    __description__ = """UploadHero.co plugin"""
    __author_name__ = ("mcmyst", "zoidberg")
    __author_mail__ = ("mcmyst@hotmail.fr", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<div class="nom_de_fichier">(?P<N>.*?)</div>'
    FILE_SIZE_PATTERN = r'Taille du fichier : </span><strong>(?P<S>.*?)</strong>'
    OFFLINE_PATTERN = r'<p class="titre_dl_2">|<div class="raison"><strong>Le lien du fichier ci-dessus n\'existe plus.'

    SH_COOKIES = [(".uploadhero.co", "lang", "en")]

    IP_BLOCKED_PATTERN = r'href="(/lightbox_block_download.php\?min=.*?)"'
    IP_WAIT_PATTERN = r'<span id="minutes">(\d+)</span>.*\s*<span id="seconds">(\d+)</span>'

    CAPTCHA_PATTERN = r'"(/captchadl\.php\?[a-z0-9]+)"'
    FREE_URL_PATTERN = r'var magicomfg = \'<a href="(http://[^<>"]*?)"|"(http://storage\d+\.uploadhero\.co/\?d=[A-Za-z0-9]+/[^<>"/]+)"'
    PREMIUM_URL_PATTERN = r'<a href="([^"]+)" id="downloadnow"'


    def handleFree(self):
        self.checkErrors()

        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m is None:
            self.parseError("Captcha URL")
        captcha_url = "http://uploadhero.co" + m.group(1)

        for _ in xrange(5):
            captcha = self.decryptCaptcha(captcha_url)
            self.html = self.load(self.pyfile.url, get={"code": captcha})
            m = re.search(self.FREE_URL_PATTERN, self.html)
            if m:
                self.correctCaptcha()
                download_url = m.group(1) or m.group(2)
                break
            else:
                self.invalidCaptcha()
        else:
            self.fail("No valid captcha code entered")

        self.download(download_url)

    def handlePremium(self):
        self.logDebug("%s: Use Premium Account" % self.__name__)
        self.html = self.load(self.pyfile.url)
        link = re.search(self.PREMIUM_URL_PATTERN, self.html).group(1)
        self.logDebug("Downloading link : '%s'" % link)
        self.download(link)

    def checkErrors(self):
        m = re.search(self.IP_BLOCKED_PATTERN, self.html)
        if m:
            self.html = self.load("http://uploadhero.co%s" % m.group(1))

            m = re.search(self.IP_WAIT_PATTERN, self.html)
            wait_time = (int(m.group(1)) * 60 + int(m.group(2))) if m else 5 * 60
            self.wait(wait_time, True)
            self.retry()


getInfo = create_getInfo(UploadheroCom)
