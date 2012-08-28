# -*- coding: utf-8 -*-

import re
from module.lib.BeautifulSoup import BeautifulSoup
from module.plugins.Crypter import Crypter

class DuckCryptInfo(Crypter):
    __name__ = "DuckCryptInfo"
    __type__ = "container"
    __pattern__ = r"http://(?:www\.)?duckcrypt.info/(folder|wait|link)/(\w+)/?(\w*)"
    __version__ = "0.01"
    __description__ = """DuckCrypt.Info Container Plugin"""
    __author_name__ = ("godofdream")
    __author_mail__ = ("soilfiction@gmail.com")

    TIMER_PATTERN = r'<span id="timer">(.*)</span>'
    
    def decrypt(self, pyfile):
        url = pyfile.url
        # seems we don't need to wait
        #src = self.req.load(str(url))
        #found = re.search(self.TIMER_PATTERN, src)
        #if found:
        #    self.logDebug("Sleeping for" % found.group(1))
        #    self.setWait(int(found.group(1)) ,False)
        found = re.search(self.__pattern__, url)
        if not found:
            self.fail('Weird error in link')
        if str(found.group(1)) == "link":
            self.handleLink(url)
        else:
            self.handleFolder(found)

        
		
    def handleFolder(self, found):
        src = self.load("http://duckcrypt.info/ajax/auth.php?hash="  + str(found.group(2)))
        found = re.search(self.__pattern__, src)
        self.logDebug("Redirectet to " + str(found.group(0)))
        src = self.load(str(found.group(0)))
        soup = BeautifulSoup(src)
        cryptlinks = soup.find("div", attrs={"class": "folderbox"}).findAll("a")
        self.logDebug("Redirectet to " + str(cryptlinks))
        if not cryptlinks:
            self.fail('no links found - (Plugin out of date?)')
        for clink in cryptlinks:
            self.handleLink(clink['href'])

    def handleLink(self, url):
        src = self.load(url)
        soup = BeautifulSoup(src)
        link = soup.find("iframe")["src"]
        if not link:
            self.logDebug('no links found - (Plugin out of date?)')
        else:
            self.core.files.addLinks([link], self.pyfile.package().id)
        
