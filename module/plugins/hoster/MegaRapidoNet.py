# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster
from random import randint

def random_with_N_digits(n):
    rand = "0."
    not_zero = 0
    for i in range(1,n+1):
        r = randint(0,9)
        if(r > 0):
            not_zero += 1
        rand += str(r)

    if not_zero > 0:
        return rand
    else:
        return random_with_N_digits(n)

class MegaRapidoNet(Hoster):
    __name__ = "MegaRapidoNet"
    __version__ = "0.01"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)*?(?:[^\.]+)\.megarapido\.net/\?file="
    __description__ = """Megarapido.net hoster plugin"""
    __author_name__ = ("Kagenoshin")
    __author_mail__ = ("kagenoshin@gmx.ch")

    DOWNLOAD_LINK_PATTERN = re.compile(r'<\s*?a[^>]*?title\s*?=\s*?["\'][^"\']*?download["\'][^>]*?href=["\']([^"\']*)', re.I)
    ERROR_MESSAGE_PATTERN = re.compile(r'<\s*?div[^>]*?class\s*?=\s*?["\']?alert-message error[^>]*>([^<]*)',re.I)

    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "vipleech4u.com")
            self.fail("No vipleech4u.com account provided")

        self.logDebug("Old URL: %s" % pyfile.url)

        new_url = pyfile.url

        #load userID
        user_id = self.getStorage("MegarapidoNet_userID")

        #upload the link which has to be loaded
        if not re.match(self.__pattern__, new_url):
            page = self.load("http://megarapido.net/gerar.php", post={"rand":random_with_N_digits(16), "urllist":new_url, "links":new_url, "exibir":"normal", "usar":"premium", "user":user_id, "autoreset":""})
            if "desloga e loga novamente para gerar seus links" in page.lower():
                self.fail("Restart pyload, because you have logged in at another place.")

            error_1 = self.ERROR_MESSAGE_PATTERN.search(page)
            if error_1:
                self.fail("%s" %error_1.group(1))

            download_link = self.DOWNLOAD_LINK_PATTERN.search(page)
            if download_link:
                download_link = download_link.group(1)
            else:
                self.fail("Couldn't find a download link.")
        else:
            download_link = new_url
        
        #tests (todo)
        if re.search(r'You have generated maximum links available to you today', page, re.I):
            self.fail('Daily limit reached.')

        self.setWait(5)
        self.wait()
        self.logDebug("Unrestricted URL: " + download_link)

        self.download(download_link, disposition=True)

        check = self.checkDownload({"bad": "<html"})

        if check == "bad":
            self.retry(24, 150, 'Bad file downloaded')
