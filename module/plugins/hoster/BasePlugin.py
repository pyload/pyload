#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.Hoster import Hoster
from module.utils import html_unescape

from urlparse import urlparse
from re import search
from urllib import unquote

class BasePlugin(Hoster):
    __name__ = "BasePlugin"
    __type__ = "hoster"
    __pattern__ = r"^unmatchable$"
    __version__ = "0.14"
    __description__ = """Base Plugin when any other didnt fit"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True

    def process(self, pyfile):
        """main function"""

        #debug part, for api exerciser
        if pyfile.url.startswith("DEBUG_API"):
            self.multiDL = False
            return

#        self.__name__ = "NetloadIn"
#        pyfile.name = "test"
#        self.html = self.load("http://localhost:9000/short")
#        self.download("http://localhost:9000/short")
#        self.api = self.load("http://localhost:9000/short")
#        self.decryptCaptcha("http://localhost:9000/captcha")
#
#        if pyfile.url == "79":
#            self.core.api.addPackage("test", [str(i) for i in range(80)], 1)
#
#        return
        if pyfile.url.startswith("http"):
            header = self.load(pyfile.url, just_header = True)
            #self.logDebug(header)

            if 'location' in header:
                self.logDebug("Location: " + header['location'])
                url = unquote(header['location'])
            else:
                url = pyfile.url

            name = html_unescape(urlparse(url).path.split("/")[-1])

            if 'content-disposition' in header:
                self.logDebug("Content-Disposition: " + header['content-disposition'])
                m = search("filename(?P<type>=|\*=(?P<enc>.+)'')(?P<name>.*)", header['content-disposition'])
                if m:
                    disp = m.groupdict()
                    self.logDebug(disp)
                    if not disp['enc']: disp['enc'] = 'utf-8'
                    name = disp['name'].replace('"', "").replace("'", "").replace(";", "").strip()
                    name = unicode(unquote(name), disp['enc'])

            if not name: self.offline()
            pyfile.name = name
            self.logDebug("Filename: %s" % pyfile.name)
            self.download(url, disposition=True)

        else:
            self.fail("No Plugin matched and not a downloadable url.")