#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import quote
from module.plugins.Hoster import Hoster

class Premium4Me(Hoster):
    __name__ = "Premium4Me"
    __version__ = "0.01"
    __type__ = "hoster"

    __pattern__ = r"http://premium4.me/.*"
    __description__ = """premium4.me hoster plugin"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    def setup(self):
        self.chunkLimit = 3
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your premium4.me account or deactivate this plugin"))
            self.fail("No premium4.me account provided")

        self.log.debug("premium4.me: Old URL: %s" % pyfile.url)
        new_url = "http://premium4.me/api/getfile.php?authcode=%s&link=%s" % (self.account.authcode, quote(pyfile.url, ""))

        #raise timeout to 2min
        self.req.setOption("timeout", 120)

        self.download(new_url, disposition=True)