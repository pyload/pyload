# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster


class DebridItaliaCom(Hoster):
    __name__ = "DebridItaliaCom"
    __version__ = "0.01"
    __type__ = "hoster"
    __pattern__ = r"https?://.*debriditalia\.com"
    __description__ = """Debriditalia.com hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def init(self):
        self.chunkLimit = -1
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.logError("Please enter your DebridItalia account or deactivate this plugin")
            self.fail("No DebridItalia account provided")

        self.logDebug("Old URL: %s" % pyfile.url)
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        else:
            url = "http://debriditalia.com/linkgen2.php?xjxfun=convertiLink&xjxargs[]=S<![CDATA[%s]]>" % pyfile.url
            page = self.load(url)
            self.logDebug("XML data: %s" % page)

            new_url = re.search(r'<a href="(?:[^"]+)">(?P<direct>[^<]+)</a>', page).group('direct')

        self.logDebug("New URL: %s" % new_url)

        self.download(new_url, disposition=True)