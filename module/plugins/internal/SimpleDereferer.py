# -*- coding: utf-8 -*-

import re
import urllib

from module.plugins.Crypter import Crypter
from module.plugins.internal.SimpleHoster import create_getInfo, set_cookies
from module.utils import html_unescape


class SimpleDereferer(Crypter):
    __name__    = "SimpleDereferer"
    __type__    = "crypter"
    __version__ = "0.13"

    __pattern__ = r'^unmatchable$'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Simple dereferer plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    """
    Following patterns should be defined by each crypter:

      LINK_PATTERN: Regex to catch the redirect url in group(1)
        example: LINK_PATTERN = r'<div class="link"><a href="(.+?)"'

      OFFLINE_PATTERN: (optional) Checks if the page is unreachable
        example: OFFLINE_PATTERN = r'File (deleted|not found)'

      TEMP_OFFLINE_PATTERN: (optional) Checks if the page is temporarily unreachable
        example: TEMP_OFFLINE_PATTERN = r'Server maintainance'


    You can override the getLinks method if you need a more sophisticated way to extract the redirect url.
    """

    LINK_PATTERN = None

    TEXT_ENCODING = False
    COOKIES       = True


    def handleDirect(self, pyfile):
        header = self.load(pyfile.url, just_header=True, decode=True)
        if 'location' in header and header['location']:
            self.link = header['location']


    def decrypt(self, pyfile):
        self.handleDirect(pyfile)

        if not self.link:
            try:
                self.link = urllib.unquote(re.match(self.__pattern__, pyfile.url).group('LINK'))

            except AttributeError:
                self.prepare()
                self.preload()
                self.checkStatus()

                self.link = self.getLink()

        if self.link:
            self.urls = [self.link]

        elif not self.urls and not self.packages:  #@TODO: Remove in 0.4.10
            self.fail(_("No link grabbed"))


    def prepare(self):
        self.info = {}
        self.html = ""
        self.link = ""  #@TODO: Move to hoster class in 0.4.10

        self.req.setOption("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)


    def preload(self):
        self.html = self.load(self.pyfile.url, cookies=bool(self.COOKIES), decode=not self.TEXT_ENCODING)

        if isinstance(self.TEXT_ENCODING, basestring):
            self.html = unicode(self.html, self.TEXT_ENCODING)


    def checkStatus(self):
        if hasattr(self, "OFFLINE_PATTERN") and re.search(self.OFFLINE_PATTERN, self.html):
            self.offline()

        elif hasattr(self, "TEMP_OFFLINE_PATTERN") and re.search(self.TEMP_OFFLINE_PATTERN, self.html):
            self.tempOffline()


    def getLink(self):
        link = re.search(self.LINK_PATTERN, self.html).group(1)
        return html_unescape(link.strip().decode('unicode-escape'))  #@TODO: Move this check to plugin `load` method in 0.4.10
