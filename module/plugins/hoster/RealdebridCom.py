#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urllib import quote, unquote
from module.plugins.Hoster import Hoster

class RealdebridCom(Hoster):
    __name__ = "RealdebridCom"
    __version__ = "0.4"
    __type__ = "hoster"

    __pattern__ = r"https?://.*real-debrid\..*"
    __description__ = """Real-Debrid.com hoster plugin"""
    __author_name__ = ("Devirex, Hazzard")
    __author_mail__ = ("naibaf_11@yahoo.de")

    def getFilename(self, url):
        return unquote(url.rsplit("/", 1)[1])

    def setup(self):
        self.chunkLimit = 3
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.log.error(_("Please enter your Real-debrid account or deactivate this plugin"))
            self.fail("No Real-debrid account provided")

        self.log.debug("Real-Debrid: Old URL: %s" % pyfile.url)
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        else:
            password = self.getPassword().splitlines()
            if not password: password = ""
            else: password = password[0]
            
            url = "http://real-debrid.com/ajax/deb.php?lang=en&sl=1&link=%s&passwort=%s" % (quote(pyfile.url, ""), password)
            page = self.load(url)

            error = re.search(r'<span id="generation-error">(.*)</span>', page)

            if error:
                msg = error.group(1).strip()
                self.log.debug(page)
                if msg == "Your file is unavailable on the hoster.":
                    self.offline()
                else:
                    self.fail(msg)
            else:
                new_url = page

        if self.getConfig("https"):
            new_url = new_url.replace("http://", "https://")
        else:
            new_url = new_url.replace("https://", "http://")

        self.log.debug("Real-Debrid: New URL: %s" % new_url)

        try:
            pyfile.name = self.getFilename(new_url)
        except IndexError:
            pyfile.name = "Unknown_Filename.ext"

        self.download(new_url, disposition=True)

        check = self.checkDownload(
                {"error": "<html><head><title>An error occured while processing your request</title>"})

        if check == "error":
            self.fail("Error occured.")

