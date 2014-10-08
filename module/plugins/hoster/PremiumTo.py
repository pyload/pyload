# -*- coding: utf-8 -*-

from os import remove
from os.path import exists
from urllib import quote

from module.plugins.Hoster import Hoster
from module.utils import fs_encode


class PremiumTo(Hoster):
    __name__ = "PremiumTo"
    __type__ = "hoster"
    __version__ = "0.10"

    __pattern__ = r'https?://(?:www\.)?premium.to/.*'

    __description__ = """Premium.to hoster plugin"""
    __authors__ = [("RaNaN", "RaNaN@pyload.org"),
                   ("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it")]


    def setup(self):
        self.resumeDownload = True
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "premium.to")
            self.fail("No premium.to account provided")

        self.logDebug("Old URL: %s" % pyfile.url)

        tra = self.getTraffic()

        #raise timeout to 2min
        self.req.setOption("timeout", 120)

        self.download(
            "http://premium.to/api/getfile.php?username=%s&password=%s&link=%s" % (self.account.username, self.account.password, quote(pyfile.url, "")),
            disposition=True)

        check = self.checkDownload({"nopremium": "No premium account available"})

        if check == "nopremium":
            self.retry(60, 5 * 60, "No premium account available")

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
            api_r = self.load("http://premium.to/api/straffic.php",
                              get={'username': self.account.username, 'password': self.account.password})
            traffic = sum(map(int, api_r.split(';')))
        except:
            traffic = 0
        return traffic
