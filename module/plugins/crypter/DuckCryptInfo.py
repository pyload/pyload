# -*- coding: utf-8 -*-

import re

from BeautifulSoup import BeautifulSoup

from module.plugins.Crypter import Crypter


class DuckCryptInfo(Crypter):
    __name__ = "DuckCryptInfo"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?duckcrypt\.info/(folder|wait|link)/(\w+)/?(\w*)'

    __description__ = """DuckCrypt.info decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]


    TIMER_PATTERN = r'<span id="timer">(.*)</span>'


    def decrypt(self, pyfile):
        url = pyfile.url

        m = re.match(self.__pattern__, url)
        if m is None:
            self.fail('Weird error in link')
        if str(m.group(1)) == "link":
            self.handleLink(url)
        else:
            self.handleFolder(m)

    def handleFolder(self, m):
        src = self.load("http://duckcrypt.info/ajax/auth.php?hash=" + str(m.group(2)))
        m = re.match(self.__pattern__, src)
        self.logDebug("Redirectet to " + str(m.group(0)))
        src = self.load(str(m.group(0)))
        soup = BeautifulSoup(src)
        cryptlinks = soup.findAll("div", attrs={"class": "folderbox"})
        self.logDebug("Redirectet to " + str(cryptlinks))
        if not cryptlinks:
            self.error("no links m")
        for clink in cryptlinks:
            if clink.find("a"):
                self.handleLink(clink.find("a")['href'])

    def handleLink(self, url):
        src = self.load(url)
        soup = BeautifulSoup(src)
        self.urls = [soup.find("iframe")['src']]
        if not self.urls:
            self.logInfo("No link found")
