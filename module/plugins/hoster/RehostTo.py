#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import quote, unquote
from module.plugins.Hoster import Hoster

class RehostTo(Hoster):
    __name__ = "RehostTo"
    __version__ = "0.1"
    __type__ = "hoster"

    __pattern__ = r"https?://.*rehost.to\..*"
    __description__ = """rehost.com hoster plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def getFilename(self, url):
        return unquote(url.rsplit("/", 1)[1])

    def setup(self):
        self.chunkLimit = 3
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.log.error(_("Please enter your rehost.to account or deactivate this plugin"))
            self.fail("No rehost.to account provided")

        data = self.account.getAccountInfo(self.user)
        long_ses = data["long_ses"]

        self.log.debug("Rehost.to: Old URL: %s" % pyfile.url)
        new_url = "http://rehost.to/process_download.php?user=cookie&pass=%s&dl=%s" % (long_ses, quote(pyfile.url, ""))

        #raise timeout to 2min
        self.req.setOption("timeout", 120)

        self.download(new_url, disposition=True)