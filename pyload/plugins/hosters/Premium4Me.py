#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import quote
from os.path import exists
from os import remove

from pyload.plugins.Hoster import Hoster
from pyload.utils.fs import fs_encode

class Premium4Me(Hoster):
    __name__ = "Premium4Me"
    __version__ = "0.08"
    __type__ = "hoster"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for downloads from supported hosters:", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]
    __pattern__ = r"http://premium.to/.*"
    __description__ = """Premium.to hoster plugin"""
    __author_name__ = ("RaNaN", "zoidberg", "stickell")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    def setup(self):
        self.resumeDownload = True
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "premium.to")
            self.fail("No premium.to account provided")

        self.logDebug("premium.to: Old URL: %s" % pyfile.url)

        tra = self.getTraffic()

        #raise timeout to 2min
        self.req.setOption("timeout", 120)

        self.download(
            "http://premium.to/api/getfile.php?authcode=%s&link=%s" % (self.account.authcode, quote(pyfile.url, "")),
            disposition=True)

        check = self.checkDownload({"nopremium": "No premium account available"})

        if check == "nopremium":
            self.retry(60, 300, 'No premium account available')

        err = ''
        if self.req.http.code == '420':
            # Custom error code send - fail
            lastDownload = fs_encode(self.lastDownload)

            if exists(lastDownload):
                f = open(lastDownload, "rb")
                err = f.read(256).strip()
                f.close()
                remove(lastDownload)
            else:
                err = 'File does not exist'

        trb = self.getTraffic()
        self.logInfo("Filesize: %d, Traffic used %d, traffic left %d" % (pyfile.size, tra - trb, trb))

        if err:
            self.fail(err)

    def getTraffic(self):
        try:
            traffic = int(self.load("http://premium.to/api/traffic.php?authcode=%s" % self.account.authcode))
        except:
            traffic = 0
        return traffic       
