# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class SimplydebridCom(MultiHoster):
    __name__    = "SimplydebridCom"
    __type__    = "hoster"
    __version__ = "0.14"

    __pattern__ = r'http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/sd\.php'

    __description__ = """Simply-debrid.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def handlePremium(self):
        #fix the links for simply-debrid.com!
        self.link = self.pyfile.url
        self.link = self.link.replace("clz.to", "cloudzer.net/file")
        self.link = self.link.replace("http://share-online", "http://www.share-online")
        self.link = self.link.replace("ul.to", "uploaded.net/file")
        self.link = self.link.replace("uploaded.com", "uploaded.net")
        self.link = self.link.replace("filerio.com", "filerio.in")
        self.link = self.link.replace("lumfile.com", "lumfile.se")

        if('fileparadox' in self.link):
            self.link = self.link.replace("http://", "https://")

        if re.match(self.__pattern__, self.link):
            self.link = self.link

        self.logDebug("New URL: %s" % self.link)

        if not re.match(self.__pattern__, self.link):
            page = self.load("http://simply-debrid.com/api.php", get={'dl': self.link})
            if 'tiger Link' in page or 'Invalid Link' in page or ('API' in page and 'ERROR' in page):
                self.fail(_("Unable to unrestrict link"))
            self.link = page

        self.setWait(5)
        self.wait()


    def checkFile(self):
        super(SimplydebridCom, self).checkFile()

        check = self.checkDownload({"bad1": "No address associated with hostname", "bad2": "<html"})

        if check == "bad1" or check == "bad2":
            self.retry(24, 3 * 60, "Bad file downloaded")


getInfo = create_getInfo(SimplydebridCom)
