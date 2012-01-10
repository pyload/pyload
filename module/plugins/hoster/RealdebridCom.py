#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urllib import quote, unquote
from random import randrange

from module.plugins.Hoster import Hoster

class RealdebridCom(Hoster):
    __name__ = "RealdebridCom"
    __version__ = "0.42"
    __type__ = "hoster"

    __pattern__ = r"https?://.*real-debrid\..*"
    __description__ = """Real-Debrid.com hoster plugin"""
    __author_name__ = ("Devirex, Hazzard")
    __author_mail__ = ("naibaf_11@yahoo.de")

    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."): #incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100,999)
        return name

    def init(self):
        self.tries = 0
        self.chunkLimit = 3
        self.resumeDownload = True


    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your Real-debrid account or deactivate this plugin"))
            self.fail("No Real-debrid account provided")

        self.log.debug("Real-Debrid: Old URL: %s" % pyfile.url)
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        else:
            password = self.getPassword().splitlines()
            if not password: password = ""
            else: password = password[0]
            
            url = "http://real-debrid.com/lib/ajax/generator.php?lang=en&sl=1&link=%s&passwort=%s" % (quote(pyfile.url, ""), password)
            page = self.load(url)

            error = re.search(r'<span id="generation-error">(.*)</span>', page)

            if error:
                msg = error.group(1).strip()
                self.logDebug(page)
                if msg == "Your file is unavailable on the hoster.":
                    self.offline()
                else:
                    self.fail(msg)
            elif url == 'error':
                self.fail("Your IP is most likely blocked. Please contact RealDebrid support")
            else:
                new_url = page

        if self.getConfig("https"):
            new_url = new_url.replace("http://", "https://")
        else:
            new_url = new_url.replace("https://", "http://")

        self.log.debug("Real-Debrid: New URL: %s" % new_url)


        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown"):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload(
                {"error": "<title>An error occured while processing your request</title>"})

        if check == "error":
            #usual this download can safely be retried
            self.retry(reason="An error occured while generating link.", wait_time=60)

